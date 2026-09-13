"""Independent, read-only audit of a persisted submission run.

This module makes no model calls and does not regenerate decisions.  It verifies
the public output contract, reconciles every output with its persisted decision
audit, and replays the deterministic semantic guard over saved extraction
bundles so the safety-boundary metrics are not inferred from output labels.
"""
from __future__ import annotations

import json
from collections import Counter
from decimal import Decimal
from pathlib import Path

from input_preparation import prepare_case
from plans import Output
from semantic_boundary import guard_bundle
from submission_runner import OUTPUT_FIELDS, read_csv


def _money(value: str) -> Decimal:
    return Decimal(value)


def _plan_entries(value: str) -> list[tuple[str, Decimal]]:
    if value == "none":
        return []
    result = []
    for entry in value.split("|"):
        when, amount = entry.split(":", 1)
        result.append((when, _money(amount)))
    return result


def _known_harm_reasons() -> set[str]:
    return {
        "gross_or_total_not_a_due_or_paid_value",
        "label_value_semantic_conflict",
        "confirmed_credit_has_unsettled_event",
        "unidentified_future_credit_lacks_settlement_evidence",
        "contingent_income_cannot_be_confirmed_cash",
    }


def audit(root: Path, artifact_root: Path, output_path: Path) -> dict:
    data = root / "dataset"
    requests = read_csv(data / "requests.csv")
    outputs = read_csv(output_path)
    events = read_csv(data / "financial_events.csv")
    messages = read_csv(data / "messages.csv")
    images = read_csv(data / "images.csv")
    options = read_csv(data / "request_payment_options.csv")

    errors: list[str] = []
    request_ids = [row["request_id"] for row in requests]
    output_ids = [row["request_id"] for row in outputs]
    if not outputs or tuple(outputs[0]) != OUTPUT_FIELDS:
        errors.append("output columns differ from required contract")
    if output_ids != request_ids:
        errors.append("output request IDs or order differ from requests.csv")

    option_by_request: dict[str, list[dict]] = {}
    for row in options:
        option_by_request.setdefault(row["request_id"], []).append(row)

    decision_counts = Counter()
    block_reasons = Counter()
    trusted_types = Counter()
    guard_reason_counts = Counter()
    total_trusted = total_blocked = 0
    deterministic_harm_blocked = deterministic_harm_trusted = 0
    extraction_calls = retries = prompt_tokens = completion_tokens = cached_tokens = 0

    for request, output_row in zip(requests, outputs):
        rid = request["request_id"]
        try:
            model = Output.model_validate(output_row)
        except Exception as exc:
            errors.append(f"{rid}: output schema invalid: {exc}")
            continue
        if not Decimal("0") <= _money(model.amount_safe_to_pay) <= _money(request["requested_amount"]):
            errors.append(f"{rid}: amount_safe_to_pay outside request bounds")
        try:
            payments = _plan_entries(model.payment_plan)
        except Exception as exc:
            errors.append(f"{rid}: malformed payment_plan: {exc}")
            payments = []
        if payments != sorted(payments) or any(amount <= 0 for _, amount in payments):
            errors.append(f"{rid}: payment plan is non-chronological or non-positive")
        if any(when < request["request_date"] or when > request["desired_completion_date"] for when, _ in payments):
            errors.append(f"{rid}: payment date outside request/deadline bounds")
        method = model.recommended_payment_method
        if method in {"full_payment", "wait", "partial_payment"} and sum((a for _, a in payments), Decimal("0")) != _money(request["requested_amount"]):
            errors.append(f"{rid}: non-installment payment plan does not sum to requested amount")
        if method == "partial_payment" and (len(payments) != 2 or payments[0][1] != _money(model.amount_safe_to_pay)):
            errors.append(f"{rid}: partial payment does not obey exact two-payment contract")
        if method == "installments":
            schedules = []
            for option in option_by_request.get(rid, []):
                if option["payment_method"] != "installments":
                    continue
                count = int(option["number_of_payments"])
                step = int(option["payment_frequency_days"] or 0)
                from datetime import date, timedelta
                start = date.fromisoformat(option["first_payment_date"])
                schedules.append([(str(start + timedelta(days=i * step)), _money(option["payment_amount"])) for i in range(count)])
            if payments not in schedules:
                errors.append(f"{rid}: installment plan does not equal a supplied option")
        if method == "not_recommended" and model.payment_plan != "none":
            errors.append(f"{rid}: not_recommended has a payment plan")
        if not model.decision_explanation.strip():
            errors.append(f"{rid}: empty explanation")

        decision_path = artifact_root / rid / "decision.json"
        if not decision_path.is_file():
            errors.append(f"{rid}: missing persisted decision audit")
            continue
        decision = json.loads(decision_path.read_text(encoding="utf-8"))
        if decision.get("output") != output_row:
            errors.append(f"{rid}: CSV row differs from persisted decision")
        audit_record = decision.get("audit", {})
        usage = audit_record.get("usage", {})
        extraction_calls += int(usage.get("calls", 0))
        retries += int(usage.get("retries", 0))
        prompt_tokens += int(usage.get("prompt_tokens", 0))
        completion_tokens += int(usage.get("completion_tokens", 0))
        if "cached_tokens" in usage:
            cached_tokens += int(usage.get("cached_tokens", 0))
        else:
            for response_path in (artifact_root / rid / "extraction").glob("**/attempt_*_response.json"):
                response = json.loads(response_path.read_text(encoding="utf-8"))
                cached_tokens += int(response.get("usage", {}).get("cached_tokens", 0) or 0)
        selected = audit_record.get("selected")
        if model.decision_explanation.startswith("Blocked unresolved financial evidence:"):
            decision_counts["safety_fail_closed"] += 1
            if selected is not None:
                errors.append(f"{rid}: safety-blocked output retained a selected plan")
        elif selected is None:
            decision_counts["verified_no_eligible_plan"] += 1
        else:
            decision_counts[f"selected_{selected}"] += 1
            if selected != method:
                errors.append(f"{rid}: selected method differs from output")
        for reason in audit_record.get("finance_blockers", []):
            block_reasons[str(reason)] += 1

        extraction_path = artifact_root / rid / "extraction" / "composed.json"
        if extraction_path.is_file():
            extracted = json.loads(extraction_path.read_text(encoding="utf-8"))
            if not extracted.get("usable"):
                decision_counts["extraction_unavailable"] += 1
                continue
            case = prepare_case(request, events, messages, images, root)
            evidence = case["evidence"]
            index = {row["event_id"]: row for row in case["finance_events"]}
            index.update({row[key]: row for field, key in (("messages", "message_id"), ("images", "image_id")) for row in evidence[field]})
            replay = guard_bundle(extracted["bundle"], case["finance_events"], index)
            replay_ids = [fact["fact_id"] for fact in replay["facts"]]
            if replay_ids != audit_record.get("trusted_fact_ids", []):
                errors.append(f"{rid}: persisted trusted facts differ from guard replay")
            if replay["blocked"] != audit_record.get("blocked_facts", []):
                errors.append(f"{rid}: persisted blocked facts differ from guard replay")
            total_trusted += len(replay["facts"])
            total_blocked += len(replay["blocked"])
            for fact in replay["facts"]:
                trusted_types[fact["fact_type"]] += 1
            for record in replay["blocked"]:
                reasons = set(record.get("reasons", []))
                guard_reason_counts.update(reasons)
                if reasons & _known_harm_reasons():
                    deterministic_harm_blocked += 1
            # A known harmful condition surviving replay is an audit defect.
            for fact in replay["facts"]:
                single = guard_bundle({"facts": [fact]}, case["finance_events"], index)
                if single["blocked"] and set(single["blocked"][0].get("reasons", [])) & _known_harm_reasons():
                    deterministic_harm_trusted += 1

    return {
        "valid": not errors,
        "errors": errors,
        "requests": len(requests),
        "outputs": len(outputs),
        "decision_counts": dict(sorted(decision_counts.items())),
        "safety_block_reasons": dict(block_reasons.most_common()),
        "semantic_guard": {
            "trusted_facts": total_trusted,
            "blocked_facts": total_blocked,
            "trusted_fact_types": dict(trusted_types.most_common()),
            "block_reasons": dict(guard_reason_counts.most_common()),
            "known_harmful_facts_blocked": deterministic_harm_blocked,
            "known_harmful_facts_trusted": deterministic_harm_trusted,
        },
        "usage": {
            "calls": extraction_calls,
            "retries": retries,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cached_tokens": cached_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
    }
