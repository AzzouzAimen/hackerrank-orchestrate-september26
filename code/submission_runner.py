"""Guarded deterministic submission orchestration."""
from __future__ import annotations

import csv, json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Callable

from finance import decimal, project
from input_preparation import prepare_case
from plans import Output, choose, output
from semantic_boundary import guarded_resolve

OUTPUT_FIELDS = ("request_id","amount_safe_to_pay","affordability_status","recommended_payment_method",
                 "payment_plan","earliest_date_for_full_payment","spending_changes_needed","decision_explanation")


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as h:
        return list(csv.DictReader(h))


def fail_closed(request: dict, reasons: list[str]) -> Output:
    summary = "; ".join(reasons[:3]) or "semantic evidence unavailable"
    return Output(request_id=request["request_id"], amount_safe_to_pay="0",
                  affordability_status="not_affordable", recommended_payment_method="not_recommended",
                  payment_plan="none", earliest_date_for_full_payment="", spending_changes_needed="none",
                  decision_explanation="Blocked unresolved financial evidence: " + summary)


def decide(root: Path, request: dict, tables: dict[str, list[dict]],
           extractor: Callable[[dict, Path], dict], artifact_dir: Path) -> tuple[dict, dict]:
    cached = artifact_dir / "decision.json"
    if cached.is_file():
        saved = json.loads(cached.read_text(encoding="utf-8"))
        return saved["output"], saved["audit"]
    case = prepare_case(request, tables["financial_events"], tables["messages"], tables["images"], root)
    evidence = case["evidence"]; finance_events = case["finance_events"]
    usage = {"calls":0,"retries":0,"prompt_tokens":0,"completion_tokens":0,"cached_tokens":0}
    if evidence["messages"] or evidence["images"]:
        extracted = extractor(case, artifact_dir / "extraction")
        for attempt in extracted.get("attempts", []):
            usage["calls"] += 1
            usage["prompt_tokens"] += attempt.get("usage", {}).get("prompt_tokens", 0) or 0
            usage["completion_tokens"] += attempt.get("usage", {}).get("completion_tokens", 0) or 0
            usage["cached_tokens"] += attempt.get("usage", {}).get("cached_tokens", 0) or 0
        usage["retries"] = max(0, usage["calls"] - (1 + bool(evidence["images"])))
        if not extracted.get("usable"):
            result = fail_closed(request, ["semantic extraction unavailable"])
            audit = {"usage":usage,"blocked":[{"reason":"extraction_unavailable"}],"trusted_fact_ids":[],
                     "blocked_facts":[],"finance_blockers":["semantic extraction unavailable"],
                     "finance_issues":[],"selected":None}
            artifact_dir.mkdir(parents=True, exist_ok=True)
            cached.write_text(json.dumps({"output":result.model_dump(),"audit":audit},indent=2)+"\n",encoding="utf-8")
            return result.model_dump(), audit
        bundle = extracted["bundle"]
    else:
        bundle = {"facts": []}
    index = {row["event_id"]:row for row in finance_events}
    index.update({row[key]:row for field,key in (("messages","message_id"),("images","image_id")) for row in evidence[field]})
    guarded = guarded_resolve(finance_events, next(x for x in tables["financial_profiles"] if x["user_id"] == request["user_id"]),
                              request, bundle, index)
    rates = {(r["rate_date"],r["from_currency"],r["to_currency"]):decimal(r["rate"]) for r in tables["exchange_rates"]}
    project(guarded.state, rates)
    options = [x for x in tables["request_payment_options"] if x["request_id"] == request["request_id"]]
    if guarded.state.blockers:
        result = fail_closed(request, guarded.state.blockers)
        selected = None
    else:
        selected, _ = choose(guarded.state, options)
        result = output(guarded.state, selected, options)
    audit = {"usage":usage,"trusted_fact_ids":[f.fact_id for f in guarded.trusted_bundle.facts],
             "blocked_facts":guarded.blocked,"finance_blockers":guarded.state.blockers,
             "finance_issues":guarded.state.issues,"selected":selected.method if selected else None}
    artifact_dir.mkdir(parents=True, exist_ok=True)
    (artifact_dir / "decision.json").write_text(json.dumps({"output":result.model_dump(),"audit":audit},indent=2,default=str)+"\n",encoding="utf-8")
    return result.model_dump(), audit


def run(root: Path, requests_path: Path, output_path: Path, artifact_root: Path,
        extractor: Callable[[dict, Path], dict], limit: int | None = None, workers: int = 1) -> dict:
    names = ("financial_profiles","financial_events","exchange_rates","request_payment_options","messages","images")
    tables = {name:read_csv(root / "dataset" / f"{name}.csv") for name in names}
    requests = read_csv(requests_path)
    if limit is not None:
        requests = requests[:limit]
    def execute(request):
        directory = artifact_root / request["request_id"]
        try:
            return decide(root, request, tables, extractor, directory)
        except Exception as exc:
            result = fail_closed(request, [type(exc).__name__ + ": " + str(exc)])
            audit = {"usage":{"calls":0,"retries":0,"prompt_tokens":0,"completion_tokens":0,"cached_tokens":0},
                     "blocked":[{"reason":"pipeline_exception","detail":str(exc)}],"trusted_fact_ids":[],
                     "blocked_facts":[],"finance_blockers":[str(exc)],"finance_issues":[],"selected":None}
            directory.mkdir(parents=True, exist_ok=True)
            (directory / "decision.json").write_text(json.dumps({"output":result.model_dump(),"audit":audit},indent=2)+"\n",encoding="utf-8")
            return result.model_dump(), audit
    if workers < 1:
        raise ValueError("workers must be positive")
    with ThreadPoolExecutor(max_workers=workers) as pool:
        records = list(pool.map(execute, requests))
    outputs=[x[0] for x in records]; audits=[x[1] for x in records]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w",encoding="utf-8",newline="") as h:
        writer=csv.DictWriter(h,fieldnames=OUTPUT_FIELDS); writer.writeheader(); writer.writerows(outputs)
    usage = {key:sum(a["usage"].get(key, 0) for a in audits)
             for key in ("calls","retries","prompt_tokens","completion_tokens","cached_tokens")}
    usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]
    summary={"scope":str(requests_path),"requests":len(requests),"workers":workers,"usage":usage,
             "safety_fail_closed":sum(x["decision_explanation"].startswith("Blocked unresolved financial evidence:") for x in outputs),
             "not_recommended":sum(x["recommended_payment_method"]=="not_recommended" for x in outputs),
             "pipeline_exceptions":sum(any(b.get("reason")=="pipeline_exception" for b in a.get("blocked",[])) for a in audits),
             "completed_utc":datetime.now(timezone.utc).isoformat()}
    artifact_root.mkdir(parents=True, exist_ok=True)
    (artifact_root / "run_summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    return summary
