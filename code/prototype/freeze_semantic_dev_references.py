"""Create the frozen, development-only semantic reference from reviewed evidence.

No model calls, sample labels, profiles, requests, or holdout records are read.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "code/prototype/extraction_artifacts/semantic_inventory_01"
SOURCE = BASE / "semantic_reference_annotations_dev_20260912_v3.json"
SPLIT = BASE / "semantic_split_20260912_v5.json"
INPUT = BASE / "development_runtime_inputs_v2/manifest.json"
OUT = BASE / "semantic_reference_annotations_dev_20260912_v4_frozen.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_target(fact: dict, evidence_id: str, quoted_text: str) -> dict:
    fact["affected_event_ids"] = []
    fact["stream_selector"] = None
    fact["source_target"] = {"evidence_id": evidence_id, "quoted_text": quoted_text}
    return fact


def make_fact(case: str, kind: str, message_id: str, quote: str, payload: dict,
              unresolved: list[str]) -> dict:
    return {
        "schema_version": "1.0", "fact_id": f"{case}.{kind}",
        "evidence_ids": [message_id], "affected_event_ids": [],
        "stream_selector": None,
        "source_target": {"evidence_id": message_id, "quoted_text": quote},
        "effective_from": None, "effective_until": None,
        "confirmation_state": "confirmed", "unresolved_fields": unresolved,
        "fact_type": kind, "payload": payload,
    }


MEANINGS = {
    "dev_user_16": [
        ("renewed monthly rent rises by 12%; new amount and exact amendment duration are unknown", ["message_12"]),
        ("the linked document reports INR 100000 Balance Due and INR 100000 Amount Received; gross INR 200000 is not the current due", ["image_02", "event_1442"]),
    ],
    "dev_user_03": [
        ("next regular salary is confirmed with unknown amount and day", ["message_02"]),
        ("a separate one-time payroll adjustment is present with unknown amount and day", ["message_02"]),
        ("the historical payslip reports IDR 4365000 Net Pay", ["image_01", "event_253"]),
    ],
    "dev_user_06": [("temporary monthly pay is EUR 1037.52; duration beyond the next payroll is unknown", ["message_04"])],
    "dev_user_12": [("the seasonal contract income stream ended; renewal and off-season income are unconfirmed", ["message_09", "event_990", "event_996"])],
    "dev_user_28": [
        ("regular salary is EUR 1452 with exact next payment date unknown", ["message_20"]),
        ("EUR 653.40 arrears are a separate one-time adjustment with exact date unknown", ["message_20"]),
    ],
    "dev_user_04": [("the current quarterly bonus is contingent on review; current amount and date are unapproved", ["message_03", "event_270"])],
    "dev_user_10": [("QuickCrew payout remains pending and non-withdrawable; amount, currency, and completion date are unknown", ["message_07"])],
    "dev_user_26": [("one approved IDR 30780000 invoice is expected on 2025-08-15; other invoices remain unapproved", ["message_18"])],
    "dev_user_20": [("the merchant refund has not credited the account", ["message_14", "event_1785"])],
    "dev_user_18": [("the matching debit and credit are a same-owner internal transfer; their event IDs are unavailable", ["message_13"])],
    "dev_user_229": [("the scheduled utility debit retries the failed attempt; the failed debit is not a settled payment", ["message_179", "event_21101", "event_21102"])],
    "dev_user_22": [("the portfolio valuation is unrealized and yields no available cash", ["message_15", "event_1960"])],
    "dev_user_23": [("the verified prize is still processing and has not credited; amount, currency, and date are unknown", ["message_16"])],
    "dev_user_14": [
        ("regular salary of EUR 2717 resumes on 2025-08-15", ["message_10"]),
        ("a recurring childcare payment starts in August; exact day, amount, and currency are unknown", ["message_10"]),
    ],
}


def build() -> dict:
    split = json.loads(SPLIT.read_text(encoding="utf-8"))
    old = json.loads(SOURCE.read_text(encoding="utf-8"))
    manifest = json.loads(INPUT.read_text(encoding="utf-8"))
    by_case = {a["case_id"]: copy.deepcopy(a) for a in old["annotations"]}
    inputs = {a["case_id"]: a for a in manifest["cases"]}
    dev = split["development"]
    assert len(dev) == len(by_case) == len(inputs) == len(MEANINGS) == 14
    annotations = []
    for entry in dev:
        case = entry["case_id"]
        ann = by_case[case]
        facts = ann["required_contract_facts"]
        if case == "dev_user_16":
            facts[:] = [f for f in facts if f["fact_type"] == "amount_amendment" or f["fact_type"] == "image_financial_value"]
            facts[0]["payload"]["scope"] = "unknown"
        elif case == "dev_user_12":
            facts[:] = [{
                "schema_version": "1.0", "fact_id": "u12_season_ended",
                "evidence_ids": ["message_09", "event_990", "event_996"],
                "affected_event_ids": [], "stream_selector": {
                    "user_id": "user_12", "category": "salary", "direction": "credit",
                    "currency": "ZAR", "description": "Seasonal contract payment"},
                "effective_from": None, "effective_until": None,
                "confirmation_state": "confirmed", "unresolved_fields": ["end_date"],
                "fact_type": "stream_status", "payload": {"status": "ended"},
            }]
        elif case == "dev_user_04":
            facts[:] = [{
                "schema_version": "1.0", "fact_id": "u04_bonus_contingent",
                "evidence_ids": ["message_03", "event_270"],
                "affected_event_ids": [], "stream_selector": {
                    "user_id": "user_04", "category": "salary", "direction": "credit",
                    "currency": "IDR", "description": "Quarterly performance bonus"},
                "effective_from": None, "effective_until": None,
                "confirmation_state": "confirmed", "unresolved_fields": ["current_amount", "payment_date"],
                "fact_type": "stream_status", "payload": {"status": "contingent"},
            }]
        elif case == "dev_user_10":
            facts[:] = [make_fact(case, "cash_classification", "message_07", "next QuickCrew payout",
                                  {"classification": "pending_credit"}, ["amount", "currency", "payment_date", "event_id"])]
        elif case == "dev_user_26":
            source_target(facts[0], "message_18", "pembayaran faktur sebesar IDR 30780000")
            facts[0]["confirmation_state"] = "uncertain"
            facts[0]["unresolved_fields"] = ["actual_settlement"]
        elif case == "dev_user_20":
            facts[:] = [f for f in facts if f["fact_type"] == "cash_classification"]
        elif case == "dev_user_18":
            facts[:] = [make_fact(case, "lifecycle_relationship", "message_13", "matching debit and credit",
                                  {"relationship": "internal_transfer", "related_event_id": None},
                                  ["event_ids", "amount", "currency", "settlement_date"])]
        elif case == "dev_user_229":
            facts[:] = [f for f in facts if f["fact_type"] == "lifecycle_relationship"]
            facts[0]["affected_event_ids"] = ["event_21102"]
        elif case == "dev_user_23":
            facts[:] = [make_fact(case, "cash_classification", "message_16", "prize claim",
                                  {"classification": "pending_credit"}, ["amount", "currency", "payment_date", "event_id"])]
        elif case == "dev_user_14":
            source_target(facts[1], "message_10", "new recurring childcare payment")
            facts[1]["unresolved_fields"] = ["amount", "currency", "start_date", "event_id"]
        ann["required_semantic_meanings"] = [
            {"statement": statement, "source_ids": ids} for statement, ids in MEANINGS[case]
        ]
        ann["required_contract_facts"] = facts
        ann["review_status"] = "approved_for_development_benchmark"
        ann["runtime_input"] = {
            "manifest": "development_runtime_inputs_v2/manifest.json",
            "request_file": inputs[case]["request_file"],
            "serialized_payload_sha256": inputs[case]["serialized_payload_sha256"],
            "serialized_payload_bytes": inputs[case]["serialized_payload_bytes"],
        }
        ann["semantic_pass_requires_nonempty_facts"] = True
        ann["contextual_assertions"] = [x for x in ann["contextual_assertions"]
                                        if x["status"] not in ("semantic_context_not_contract_emission", "context_only_not_contract_emission")]
        if case == "dev_user_16":
            ann["acceptable_alternates"] = ["The outstanding event's scheduled date may be restated, but its amount must come from Balance Due, not gross Total or Amount Received."]
        if case == "dev_user_04":
            ann["acceptable_alternates"] = ["cash_classification=contingent_income on the precise bonus stream is equivalent only when effective after the current message, preserving the prior settled bonus."]
        if case == "dev_user_12":
            ann["acceptable_alternates"] = ["A status fact may target the supplied seasonal event IDs instead of the precise historical stream selector."]
        if case == "dev_user_10":
            ann["acceptable_alternates"] = []
        if case == "dev_user_26":
            ann["acceptable_alternates"] = ["An exact source-targeted future confirmation preserves the approved amount and expected date; actual settlement remains uncertain."]
        if case == "dev_user_20":
            ann["acceptable_alternates"] = ["A correct refund_of link may be included; the raw linked_event_id, amount and settlement date need no mandatory restatement."]
        if case == "dev_user_18":
            ann["acceptable_alternates"] = ["An identified internal_transfer pair is acceptable only if both actual event IDs are supplied in later evidence."]
        if case == "dev_user_229":
            ann["acceptable_alternates"] = ["Raw failed status and scheduled retry amount/date need no mandatory restatement."]
        if case == "dev_user_23":
            ann["acceptable_alternates"] = []
        if case == "dev_user_14":
            ann["acceptable_alternates"] = ["A precise childcare event/stream target may replace the message quote only if later evidence supplies its own currency and identity."]
        ann["ambiguity_notes"] = {
            "dev_user_10": "No payout event, amount, currency, or completion date is supplied; the message quote is the only target.",
            "dev_user_26": "Approval and expected settlement are explicit; no invoice event ID or actual settlement confirmation is supplied.",
            "dev_user_18": "The relationship is explicit, but neither transfer leg is supplied; no financial exclusion can be applied to an unrelated event.",
            "dev_user_23": "Claim verification does not establish payment; no prize amount, currency, date, or event ID is supplied.",
            "dev_user_14": "Childcare begins in August, but no amount, exact day, currency, or event ID is supplied.",
            "dev_user_12": "Seasonal history supplies a precise ZAR stream; no renewal or exact end date is supplied.",
            "dev_user_04": "Prior settled bonus identifies the stream but does not establish the current bonus amount or date.",
        }.get(case, ann["ambiguity_notes"])
        annotations.append(ann)
    return {
        "version": "semantic-reference-annotations-dev-20260912-v4-frozen",
        "scope": "development_only", "review_status": "approved_for_development_benchmark",
        "ground_truth": False, "model_calls": 0,
        "benchmark_conventions": {
            "semantic_meanings_are_independent_of_serialization": True,
            "minimum_required_facts_per_case": 1,
            "empty_facts_never_pass_meaningful_evidence": True,
            "equivalent_valid_seven_fact_representations_allowed": True,
            "raw_event_restatements_not_required": True,
            "unresolved_values_must_remain_unknown": True,
            "harmful_interpretations_rejected": True,
        },
        "contract_fact_types": old["contract_fact_types"],
        "source_sha256": {
            "split": digest(SPLIT), "selection_reference_v3": digest(SOURCE),
            "runtime_manifest": digest(INPUT),
            "financial_events": digest(ROOT / "dataset/financial_events.csv"),
            "messages": digest(ROOT / "dataset/messages.csv"),
            "images": digest(ROOT / "dataset/images.csv"),
            "schema": digest(ROOT / "code/evidence.py"),
            "exported_schema": digest(ROOT / "code/evidence.schema.json"),
            "extractor": digest(ROOT / "code/prototype/extraction_experiment.py"),
        },
        "annotations": annotations,
    }


def main() -> None:
    expected = json.dumps(build(), ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
    import sys
    if "--check" in sys.argv:
        assert OUT.read_bytes() == expected, "frozen reference differs from source"
        print("verified frozen development references")
    else:
        OUT.write_bytes(expected)
        print("wrote frozen development references")


if __name__ == "__main__":
    main()
