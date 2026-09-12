"""Offline validation of frozen development references and their exact inputs."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code"))
from evidence import EvidenceBundle

BASE = ROOT / "code/prototype/extraction_artifacts/semantic_inventory_01"
SPLIT = BASE / "semantic_split_20260912_v5.json"
ANNOT = BASE / "semantic_reference_annotations_dev_20260912_v4_frozen.json"
MANIFEST = BASE / "development_runtime_inputs_v2/manifest.json"
ALLOWED = {"stream_status", "amount_amendment", "date_or_schedule_amendment",
           "future_event_confirmation", "lifecycle_relationship", "image_financial_value",
           "cash_classification"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def table(name: str, key: str) -> dict[str, dict[str, str]]:
    with (ROOT / "dataset" / name).open(encoding="utf-8-sig", newline="") as handle:
        return {r[key]: r for r in csv.DictReader(handle)}


def validate() -> None:
    split = json.loads(SPLIT.read_text(encoding="utf-8"))
    refs = json.loads(ANNOT.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    # Only development split membership is read; no holdout evidence or labels.
    dev = {c["case_id"]: c for c in split["development"]}
    inputs = {c["case_id"]: c for c in manifest["cases"]}
    anns = {a["case_id"]: a for a in refs["annotations"]}
    assert len(dev) == len(inputs) == len(anns) == 14
    assert set(dev) == set(inputs) == set(anns)
    assert refs["scope"] == manifest["scope"] == "development_only"
    assert refs["review_status"] == "approved_for_development_benchmark"
    assert refs["ground_truth"] is False and refs["model_calls"] == manifest["model_calls"] == 0
    assert set(refs["contract_fact_types"]) == ALLOWED
    assert manifest["split_sha256"] == sha(SPLIT)
    assert refs["source_sha256"] == {
        "split": sha(SPLIT),
        "selection_reference_v3": sha(BASE / "semantic_reference_annotations_dev_20260912_v3.json"),
        "runtime_manifest": sha(MANIFEST),
        "financial_events": sha(ROOT / "dataset/financial_events.csv"),
        "messages": sha(ROOT / "dataset/messages.csv"),
        "images": sha(ROOT / "dataset/images.csv"),
        "schema": sha(ROOT / "code/evidence.py"),
        "exported_schema": sha(ROOT / "code/evidence.schema.json"),
        "extractor": sha(ROOT / "code/prototype/extraction_experiment.py"),
    }
    assert refs["benchmark_conventions"]["empty_facts_never_pass_meaningful_evidence"] is True
    events = table("financial_events.csv", "event_id")
    messages = table("messages.csv", "message_id")
    images = table("images.csv", "image_id")
    for case, ann in anns.items():
        item, inp = dev[case], inputs[case]
        assert ann["user_id"] == item["user_id"] == inp["user_id"]
        selected = ann["supporting_evidence"]
        assert set(selected["message_ids"]) == set(item["message_ids"])
        assert set(selected["image_ids"]) == set(item["image_ids"])
        assert set(selected["event_ids"]) == set(item["linked_event_ids"])
        all_event_ids = set(selected["event_ids"] + selected["history_event_ids"])
        assert set(inp["included_evidence_ids"]["event_ids"]) == all_event_ids
        for key, rows in (("message_ids", messages), ("image_ids", images),
                          ("event_ids", events), ("history_event_ids", events)):
            assert all(rows[x]["user_id"] == ann["user_id"] for x in selected[key])
        assert ann["review_status"] == "approved_for_development_benchmark"
        assert ann["semantic_pass_requires_nonempty_facts"] is True
        assert ann["required_semantic_meanings"] and ann["required_contract_facts"]
        assert ann["unsupported_or_harmful"] and ann["ambiguity_notes"]
        evidence_ids = set(selected["message_ids"] + selected["image_ids"]) | all_event_ids
        for meaning in ann["required_semantic_meanings"]:
            assert meaning["statement"] and meaning["source_ids"]
            assert set(meaning["source_ids"]) <= evidence_ids
        for assertion in ann["contextual_assertions"]:
            assert set(assertion["source_ids"]) <= evidence_ids
            assert assertion["status"] not in {"semantic_context_not_contract_emission", "context_only_not_contract_emission"}
        body_path = MANIFEST.parent / inp["request_file"]
        payload = body_path.read_bytes()
        assert hashlib.sha256(payload).hexdigest() == inp["serialized_payload_sha256"]
        assert len(payload) == inp["serialized_payload_bytes"]
        assert ann["runtime_input"] == {
            "manifest": "development_runtime_inputs_v2/manifest.json",
            "request_file": inp["request_file"],
            "serialized_payload_sha256": inp["serialized_payload_sha256"],
            "serialized_payload_bytes": inp["serialized_payload_bytes"],
        }
        body = json.loads(payload)
        assert len(body["messages"]) == 2 and body["messages"][0]["role"] == "system"
        content = body["messages"][1]["content"]
        text = content[0]["text"] if isinstance(content, list) else content
        raw = json.loads(text.split("CASE AND UNTRUSTED EVIDENCE:\n", 1)[1].split("\nREQUIRED JSON SCHEMA:", 1)[0])
        assert json.loads(text.split("\nREQUIRED JSON SCHEMA:\n", 1)[1]) == EvidenceBundle.model_json_schema()
        assert raw["case_id"] == case and set(raw) == {"case_id", "events", "messages", "images"}
        for field, key in (("events", "event_id"), ("messages", "message_id"), ("images", "image_id")):
            assert {r[key] for r in raw[field]} == set(inp["included_evidence_ids"][{"events":"event_ids", "messages":"message_ids", "images":"image_ids"}[field]])
        assert set(inp["image_sha256"]) == set(selected["image_ids"])
        for image_id, expected in inp["image_sha256"].items():
            assert sha(ROOT / "dataset/media/images" / f"{image_id}.png") == expected
        EvidenceBundle.model_validate({"facts": ann["required_contract_facts"]})
        assert len({f["fact_id"] for f in ann["required_contract_facts"]}) == len(ann["required_contract_facts"])
        for fact in ann["required_contract_facts"]:
            assert fact["fact_type"] in ALLOWED
            assert set(fact["evidence_ids"]) <= evidence_ids
            assert set(fact["affected_event_ids"]) <= all_event_ids
            target, selector = fact.get("source_target"), fact.get("stream_selector")
            if target:
                assert target["evidence_id"] in selected["message_ids"] and target["evidence_id"] in fact["evidence_ids"]
                assert target["quoted_text"] in messages[target["evidence_id"]]["message_text"]
            if selector:
                assert selector["user_id"] == ann["user_id"]
                relevant = [events[x] for x in all_event_ids if events[x]["category"] == selector["category"]
                            and events[x]["direction"] == selector["direction"]]
                msg_text = " ".join(messages[x]["message_text"] for x in selected["message_ids"])
                assert selector["currency"] in {e["currency"] for e in relevant} or selector["currency"] in msg_text
            if fact["fact_type"] == "future_event_confirmation" and target:
                original = messages[target["evidence_id"]]["message_text"]
                assert fact["payload"]["money"]["currency"] in original
                assert fact["payload"]["money"]["value"] in original
                assert fact["payload"]["payment_date"] in original
            if fact["fact_type"] == "lifecycle_relationship" and fact["payload"]["related_event_id"] is not None:
                assert fact["payload"]["related_event_id"] in all_event_ids
            if fact["fact_type"] == "image_financial_value":
                image_id = fact["payload"]["image_id"]
                assert image_id in selected["image_ids"] and image_id in fact["evidence_ids"]
                linked = images[image_id]["related_event_id"]
                assert linked in fact["affected_event_ids"]
                assert fact["payload"]["money"]["currency"] == events[linked]["currency"]
    fact = lambda case, kind: [f for f in anns[case]["required_contract_facts"] if f["fact_type"] == kind]
    assert {f["payload"]["value_type"]: f["payload"]["money"]["value"] for f in fact("dev_user_16", "image_financial_value")} == {
        "balance_due": "100000.00", "amount_paid": "100000.00"}
    assert fact("dev_user_16", "amount_amendment")[0]["payload"] == {"money": None, "percent_increase": "12", "scope": "unknown"}
    assert fact("dev_user_12", "stream_status")[0]["payload"]["status"] == "ended"
    assert fact("dev_user_04", "stream_status")[0]["payload"]["status"] == "contingent"
    assert len(anns["dev_user_20"]["required_contract_facts"]) == 1
    assert len(anns["dev_user_229"]["required_contract_facts"]) == 1
    assert fact("dev_user_18", "lifecycle_relationship")[0]["payload"]["related_event_id"] is None
    for case in ("dev_user_10", "dev_user_23"):
        assert {"amount", "currency", "payment_date", "event_id"} <= set(anns[case]["required_contract_facts"][0]["unresolved_fields"])
    assert {"amount", "currency", "start_date", "event_id"} <= set(fact("dev_user_14", "stream_status")[0]["unresolved_fields"])
    print("validated 14 frozen development references, exact payloads, provenance, unknowns, and nonempty meanings; no holdout/model access")


if __name__ == "__main__":
    validate()
