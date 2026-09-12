"""Bind the frozen development split to byte-exact offline extractor requests.

Only selected development IDs are read from the split. No network or profile access.
The request bytes use the same serializer as extraction_experiment.call_model.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from prototype import extraction_experiment as extractor

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "code/prototype/extraction_artifacts/semantic_inventory_01"
SPLIT = BASE / "semantic_split_20260912_v5.json"
SELECTIONS = BASE / "semantic_reference_annotations_dev_20260912_v3.json"
OUT = BASE / "development_runtime_inputs_v2"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def table(name: str, key: str) -> dict[str, dict[str, str]]:
    with (ROOT / "dataset" / name).open(encoding="utf-8-sig", newline="") as handle:
        return {row[key]: row for row in csv.DictReader(handle)}


def selected(ids: list[str], rows: dict[str, dict[str, str]], user: str) -> list[dict[str, str]]:
    if len(ids) != len(set(ids)):
        raise ValueError(f"duplicate selected IDs for {user}")
    for item_id in ids:
        row = rows[item_id]
        if row["user_id"] != user:
            raise ValueError(f"{item_id} does not belong to {user}")
    # extraction_experiment.by_ids preserves CSV order, not selection-list order.
    wanted = set(ids)
    return [row for item_id, row in rows.items() if item_id in wanted]


def build() -> tuple[dict, dict[str, bytes]]:
    split = json.loads(SPLIT.read_text(encoding="utf-8"))
    refs = json.loads(SELECTIONS.read_text(encoding="utf-8"))
    dev = split["development"]
    ref_by_case = {a["case_id"]: a for a in refs["annotations"]}
    if len(dev) != 14 or len(ref_by_case) != 14:
        raise ValueError("development case count mismatch")
    events = table("financial_events.csv", "event_id")
    messages = table("messages.csv", "message_id")
    images = table("images.csv", "image_id")
    entries: list[dict] = []
    request_files: dict[str, bytes] = {}
    for case in dev:
        case_id, user = case["case_id"], case["user_id"]
        ann = ref_by_case[case_id]
        evidence_ids = ann["supporting_evidence"]
        if ann["user_id"] != user:
            raise ValueError(f"reference owner mismatch: {case_id}")
        for field, selected_field in (("message_ids", "message_ids"), ("image_ids", "image_ids"), ("linked_event_ids", "event_ids")):
            if case[field] != evidence_ids[selected_field]:
                raise ValueError(f"split/reference selection mismatch: {case_id} {field}")
        event_ids = list(dict.fromkeys(evidence_ids["event_ids"] + evidence_ids["history_event_ids"]))
        e = selected(event_ids, events, user)
        m = selected(case["message_ids"], messages, user)
        i = selected(case["image_ids"], images, user)
        paths = [ROOT / "dataset/media/images" / f"{row['image_id']}.png" for row in i]
        if any(not path.is_file() for path in paths):
            raise FileNotFoundError(f"selected image missing for {case_id}")
        data = {"events": e, "messages": m, "images": i}
        runtime_case = {"case_id": case_id, "evidence": data, "image_paths": [str(p) for p in paths]}
        body = {"model": extractor.MODEL, "messages": [
            {"role": "system", "content": extractor.SYSTEM_PROMPT},
            {"role": "user", "content": extractor.request_content(runtime_case)},
        ], **extractor.SETTINGS}
        body_bytes = json.dumps(body).encode("utf-8")
        request_name = f"{case_id}.request.json"
        request_files[request_name] = body_bytes
        streams = sorted({
            (row["category"], row["direction"], row["currency"], row["description"])
            for row in e if row["category"] and row["direction"] and row["currency"]
        })
        context = [{"category": c, "direction": d, "currency": cur, "description": desc}
                   for c, d, cur, desc in streams]
        message_text = " ".join(row["message_text"] for row in m)
        message_currencies = sorted({currency for currency in ("IDR", "EUR", "INR", "ZAR", "USD")
                                     if currency in message_text})
        available = {"event_ids": [row["event_id"] for row in e],
                     "message_ids": [row["message_id"] for row in m],
                     "image_ids": [row["image_id"] for row in i]}
        for fact in ann["required_contract_facts"]:
            if not set(fact["evidence_ids"]).issubset(set(event_ids + case["message_ids"] + case["image_ids"])):
                raise ValueError(f"unbound required fact evidence: {case_id}/{fact['fact_id']}")
            if not set(fact["affected_event_ids"]).issubset(set(event_ids)):
                raise ValueError(f"unbound target event: {case_id}/{fact['fact_id']}")
        entries.append({
            "case_id": case_id, "user_id": user, "request_file": request_name,
            "included_evidence_ids": available,
            "source_provenance": {
                "event_ids": {x: "dataset/financial_events.csv" for x in event_ids},
                "message_ids": {x: "dataset/messages.csv" for x in case["message_ids"]},
                "image_ids": {x: f"dataset/media/images/{x}.png" for x in case["image_ids"]},
            },
            "available_event_stream_context": context,
            "explicit_message_currency_codes": message_currencies,
            "image_sha256": {row["image_id"]: sha(path.read_bytes()) for row, path in zip(i, paths)},
            "serialized_payload_sha256": sha(body_bytes),
            "serialized_payload_bytes": len(body_bytes),
        })
    manifest = {
        "version": "development-runtime-inputs-v2", "scope": "development_only",
        "split_sha256": sha(SPLIT.read_bytes()), "selection_reference_sha256": sha(SELECTIONS.read_bytes()),
        "serialization": "json.dumps(body).encode('utf-8') as in extraction_experiment.call_model",
        "payload_format": "extraction_experiment.request_content with full PNG data URLs",
        "profile_included": False, "model_calls": 0, "cases": entries,
    }
    return manifest, request_files


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="verify saved bytes without writing")
    args = parser.parse_args()
    manifest, requests = build()
    expected = json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
    if args.check:
        if (OUT / "manifest.json").read_bytes() != expected:
            raise ValueError("development input manifest differs from source")
        for name, content in requests.items():
            if (OUT / name).read_bytes() != content:
                raise ValueError(f"payload differs from source: {name}")
    else:
        OUT.mkdir(parents=True, exist_ok=True)
        for name, content in requests.items():
            (OUT / name).write_bytes(content)
        (OUT / "manifest.json").write_bytes(expected)
    print(f"{'verified' if args.check else 'built'} {len(requests)} offline development requests")


if __name__ == "__main__":
    main()
