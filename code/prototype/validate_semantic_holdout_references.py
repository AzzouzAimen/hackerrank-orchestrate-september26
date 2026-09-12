"""Deterministic validation of the eight frozen-split holdout annotations."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code"))
from evidence import EvidenceBundle, validate_source_targets
from prototype import build_semantic_holdout_inputs as input_builder
from prototype import freeze_semantic_holdout_references as reference_builder

BASE = ROOT / "code/prototype/extraction_artifacts/semantic_inventory_01"
SPLIT = BASE / "semantic_split_20260912_v5.json"
DEV = BASE / "semantic_reference_annotations_dev_20260912_v4_frozen.json"
MANIFEST = BASE / "holdout_runtime_inputs_v1/manifest.json"
OUT = BASE / "semantic_reference_annotations_holdout_20260912_v1_frozen.json"
ALLOWED = {"stream_status", "amount_amendment", "date_or_schedule_amendment",
           "future_event_confirmation", "lifecycle_relationship", "image_financial_value",
           "cash_classification"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def table(name: str, key: str) -> dict[str, dict[str, str]]:
    with (ROOT / "dataset" / name).open(encoding="utf-8-sig", newline="") as handle:
        return {r[key]: r for r in csv.DictReader(handle)}


def validate(*, candidate: bool = False) -> None:
    split = json.loads(SPLIT.read_text(encoding="utf-8"))
    dev = json.loads(DEV.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    refs = reference_builder.build() if candidate else json.loads(OUT.read_text(encoding="utf-8"))
    if not candidate:
        assert OUT.read_bytes() == json.dumps(reference_builder.build(), ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
    expected_manifest, request_files = input_builder.build()
    assert manifest == expected_manifest
    assert MANIFEST.read_bytes() == json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
    assert manifest["frozen_development_reference_sha256"] == sha(DEV)
    assert manifest["split_sha256"] == sha(SPLIT)
    assert manifest["schema_sha256"] == sha(ROOT / "code/evidence.py")
    assert manifest["extractor_sha256"] == sha(ROOT / "code/prototype/extraction_experiment.py")
    assert manifest["source_table_sha256"] == {
        name: sha(ROOT / "dataset" / name)
        for name in ("financial_events.csv", "messages.csv", "images.csv")}
    assert manifest["profile_included"] is False and manifest["sample_labels_used"] is False
    assert manifest["model_calls"] == refs["model_calls"] == 0
    assert refs["scope"] == manifest["scope"] == "holdout_only"
    assert refs["review_status"] == "approved_for_holdout_benchmark"
    assert refs["ground_truth"] is False
    assert refs["benchmark_conventions"] == dev["benchmark_conventions"]
    assert set(refs["contract_fact_types"]) == set(dev["contract_fact_types"]) == ALLOWED
    assert refs["source_sha256"] == {
        "split": sha(SPLIT), "frozen_development_reference": sha(DEV),
        "runtime_manifest": sha(MANIFEST),
        "financial_events": sha(ROOT / "dataset/financial_events.csv"),
        "messages": sha(ROOT / "dataset/messages.csv"),
        "images": sha(ROOT / "dataset/images.csv"),
        "schema": sha(ROOT / "code/evidence.py"),
        "exported_schema": sha(ROOT / "code/evidence.schema.json"),
        "extractor": sha(ROOT / "code/prototype/extraction_experiment.py"),
    }
    holdout = {c["case_id"]: c for c in split["holdout"]}
    development_ids = {c["user_id"] for c in split["development"]}
    bound = {c["case_id"]: c for c in manifest["cases"]}
    annotations = {a["case_id"]: a for a in refs["annotations"]}
    assert len(holdout) == len(bound) == len(annotations) == 8
    assert set(holdout) == set(bound) == set(annotations)
    assert not development_ids & {a["user_id"] for a in annotations.values()}
    events = table("financial_events.csv", "event_id")
    messages = table("messages.csv", "message_id")
    images = table("images.csv", "image_id")
    for case, ann in annotations.items():
        selected, entry, source = ann["supporting_evidence"], bound[case], holdout[case]
        user = source["user_id"]
        assert ann["user_id"] == entry["user_id"] == user
        assert ann["review_status"] == "approved_for_holdout_benchmark"
        assert ann["semantic_pass_requires_nonempty_facts"] is True
        assert ann["required_semantic_meanings"] and ann["required_contract_facts"]
        assert ann["unsupported_or_harmful"] and ann["ambiguity_notes"]
        assert selected["message_ids"] == source["message_ids"]
        assert selected["image_ids"] == source["image_ids"]
        assert selected["event_ids"] == source["linked_event_ids"]
        chosen = set(selected["event_ids"] + selected["history_event_ids"])
        all_ids = set(entry["included_evidence_ids"]["event_ids"])
        assert chosen <= all_ids
        evidence_ids = chosen | set(selected["message_ids"] + selected["image_ids"])
        for key, rows in (("event_ids", events), ("history_event_ids", events),
                          ("message_ids", messages), ("image_ids", images)):
            assert all(rows[x]["user_id"] == user for x in selected[key])
        for meaning in ann["required_semantic_meanings"]:
            assert meaning["statement"] and set(meaning["source_ids"]) <= evidence_ids
        for assertion in ann["contextual_assertions"]:
            assert assertion["meaning"] and set(assertion["source_ids"]) <= evidence_ids
        path = MANIFEST.parent / entry["request_file"]
        payload = path.read_bytes()
        assert payload == request_files[entry["request_file"]]
        assert len(payload) == entry["serialized_payload_bytes"]
        assert hashlib.sha256(payload).hexdigest() == entry["serialized_payload_sha256"]
        assert ann["runtime_input"] == {
            "manifest": "holdout_runtime_inputs_v1/manifest.json",
            "request_file": entry["request_file"],
            "serialized_payload_sha256": entry["serialized_payload_sha256"],
            "serialized_payload_bytes": entry["serialized_payload_bytes"],
        }
        body = json.loads(payload)
        assert body["messages"][0]["content"] == input_builder.extractor.SYSTEM_PROMPT
        assert body["model"] == input_builder.extractor.MODEL
        assert all(body[k] == v for k, v in input_builder.extractor.SETTINGS.items())
        content = body["messages"][1]["content"]
        text = content[0]["text"] if isinstance(content, list) else content
        raw = json.loads(text.split("CASE AND UNTRUSTED EVIDENCE:\n", 1)[1].split("\nREQUIRED JSON SCHEMA:", 1)[0])
        assert json.loads(text.split("\nREQUIRED JSON SCHEMA:\n", 1)[1]) == EvidenceBundle.model_json_schema()
        assert raw["case_id"] == case and set(raw) == {"case_id", "events", "messages", "images"}
        for field, key in (("events", "event_id"), ("messages", "message_id"), ("images", "image_id")):
            wanted = {"events": "event_ids", "messages": "message_ids", "images": "image_ids"}[field]
            assert [r[key] for r in raw[field]] == entry["included_evidence_ids"][wanted]
            assert all(r["user_id"] == user for r in raw[field])
        for image_id, expected in entry["image_sha256"].items():
            assert sha(ROOT / "dataset/media/images" / f"{image_id}.png") == expected
        bundle = EvidenceBundle.model_validate({"facts": ann["required_contract_facts"]})
        validate_source_targets(bundle.facts, {**events, **messages, **images})
        for fact in ann["required_contract_facts"]:
            assert fact["fact_type"] in ALLOWED
            assert set(fact["evidence_ids"]) <= evidence_ids
            assert set(fact["affected_event_ids"]) <= chosen
            target, selector = fact.get("source_target"), fact.get("stream_selector")
            if target:
                assert target["evidence_id"] in selected["message_ids"]
                assert target["evidence_id"] in fact["evidence_ids"]
                assert target["quoted_text"] in messages[target["evidence_id"]]["message_text"]
            if selector:
                assert selector["user_id"] == user
                assert any(all(events[x][k] == selector[k] for k in ("category", "direction", "currency", "description"))
                           for x in selected["history_event_ids"])
            if fact["fact_type"] == "image_financial_value":
                image_id = fact["payload"]["image_id"]
                linked = images[image_id]["related_event_id"]
                assert image_id in selected["image_ids"] and image_id in fact["evidence_ids"]
                assert linked in fact["affected_event_ids"]
                assert fact["payload"]["money"]["currency"] == events[linked]["currency"]
            if fact["fact_type"] == "lifecycle_relationship" and fact["payload"]["related_event_id"] is not None:
                assert fact["payload"]["related_event_id"] in chosen
    by = {case: ann["required_contract_facts"] for case, ann in annotations.items()}
    salary = by["holdout_user_02"][0]
    assert salary["payload"] == {"money": {"value": "42750000", "currency": "IDR"}, "percent_increase": None, "scope": "ongoing"}
    assert salary["effective_from"] == "2025-08-15" and "next_payment_date" in salary["unresolved_fields"]
    assert "IDR 42750000" in messages["message_01"]["message_text"]
    assert "2025-08-15" in messages["message_01"]["message_text"]
    assert by["holdout_user_48"][0]["payload"] == {
        "value_type": "amount_paid", "money": {"value": "15339.00", "currency": "INR"},
        "image_id": "image_08", "selected_field": "Total Amount Received"}
    assert by["holdout_user_24"][0]["payload"]["status"] == "one_time"
    assert events["event_2165"]["status"] == "settled"
    assert by["holdout_user_246"][0]["payload"]["status"] == "ended"
    assert by["holdout_user_267"][0]["payload"] == {"money": None, "percent_increase": None, "scope": "one_cycle"}
    assert "foreign currency" in messages["message_208"]["message_text"]
    for case in ("holdout_user_235", "holdout_user_268", "holdout_user_274"):
        assert by[case][0]["payload"]["classification"] == "pending_credit"
        assert not by[case][0]["affected_event_ids"] and by[case][0]["stream_selector"] is None
    for case in ("holdout_user_235", "holdout_user_274"):
        assert {"refund_currency", "home_currency_amount", "settlement_date", "settlement_fx_rate"} <= set(by[case][0]["unresolved_fields"])
    assert {"charge_currency", "home_currency_amount", "settlement_fx_rate"} <= set(by["holdout_user_267"][0]["unresolved_fields"])
    print(f"validated {len(annotations)} holdout references, exact runtime bytes, provenance, unknowns, and frozen conventions")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", action="store_true", help="validate generated references before freezing")
    args = parser.parse_args()
    validate(candidate=args.candidate)


if __name__ == "__main__":
    main()
