"""Generate reviewed holdout references under the frozen development conventions.

No model, sample labels, profiles, financial decisions, or source mutation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "code/prototype/extraction_artifacts/semantic_inventory_01"
SPLIT = BASE / "semantic_split_20260912_v5.json"
MANIFEST = BASE / "holdout_runtime_inputs_v1/manifest.json"
DEV = BASE / "semantic_reference_annotations_dev_20260912_v4_frozen.json"
OUT = BASE / "semantic_reference_annotations_holdout_20260912_v1_frozen.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fact(case: str, name: str, kind: str, evidence: list[str], payload: dict,
         *, events: list[str] | None = None, selector: dict | None = None,
         quote: tuple[str, str] | None = None, unresolved: list[str] | None = None,
         effective_from: str | None = None, confirmation: str = "confirmed") -> dict:
    return {
        "schema_version": "1.0", "fact_id": f"{case}.{name}",
        "evidence_ids": evidence, "affected_event_ids": events or [],
        "stream_selector": selector,
        **({"source_target": {"evidence_id": quote[0], "quoted_text": quote[1]}} if quote else {}),
        "effective_from": effective_from, "effective_until": None,
        "confirmation_state": confirmation, "unresolved_fields": unresolved or [],
        "fact_type": kind, "payload": payload,
    }


HISTORY = {
    "holdout_user_02": ["event_104", "event_112", "event_120", "event_128", "event_136"],
    "holdout_user_246": ["event_22585", "event_22591", "event_22597", "event_22603", "event_22609"],
}


def reviewed(case: str) -> dict:
    if case == "holdout_user_02":
        return {
            "required_semantic_meanings": [{"statement": "Monthly salary rises to IDR 42750000 effective 2025-08-15; this is a stream amendment, not a separate bonus or a guaranteed payday.", "source_ids": ["message_01", "event_136"]}],
            "required_contract_facts": [fact(case, "salary_increase", "amount_amendment", ["message_01", "event_136"],
                {"money": {"value": "42750000", "currency": "IDR"}, "percent_increase": None, "scope": "ongoing"},
                selector={"user_id": "user_02", "category": "salary", "direction": "credit", "currency": "IDR", "description": "Payroll credit"},
                effective_from="2025-08-15", unresolved=["next_payment_date"])],
            "contextual_assertions": [{"meaning": "Five settled payroll credits establish the existing IDR monthly stream, not the new amount.", "source_ids": HISTORY[case], "status": "raw_event_context"}],
            "acceptable_alternates": [],
            "unsupported_or_harmful": ["Do not apply the new amount to historical payroll, turn the effective date into a guaranteed settlement date, or calculate an unsupported percentage."],
            "ambiguity_notes": "The employer states the amount and effective date; the next actual credit date is not separately confirmed.",
        }
    if case == "holdout_user_235":
        return fx_refund(case, "message_184")
    if case == "holdout_user_48":
        return {
            "required_semantic_meanings": [
                {"statement": "The property-maintenance bill was paid on 2026-07-24 and the receipt's Total Amount Received is INR 15339.", "source_ids": ["message_35", "image_08", "event_4535"]},
            ],
            "required_contract_facts": [fact(case, "maintenance_paid", "image_financial_value", ["image_08", "message_35", "event_4535"],
                {"value_type": "amount_paid", "money": {"value": "15339.00", "currency": "INR"},
                 "image_id": "image_08", "selected_field": "Total Amount Received"},
                events=["event_4535"])],
            "contextual_assertions": [{"meaning": "The linked event is settled on 2026-07-24 with a blank structured amount; image line items sum to INR 15339 and show original due date 2026-08-30.", "source_ids": ["event_4535", "image_08"], "status": "raw_event_and_image_context"}],
            "acceptable_alternates": ["An additional cash classification on the linked settled event is permitted but does not replace the receipt's total-paid image fact."],
            "unsupported_or_harmful": ["Do not treat INR 15339 as currently due on 2026-08-30, create another debit from the receipt, or confuse an individual line item with the total paid."],
            "ambiguity_notes": "The receipt says Total Amount Received; its later printed due date is historical invoice context after payment.",
        }
    if case == "holdout_user_24":
        return {
            "required_semantic_meanings": [{"statement": "The prize proceeds reached the account after withholding and the claim is closed with no further scheduled payment.", "source_ids": ["message_17", "event_2165"]}],
            "required_contract_facts": [fact(case, "prize_closed", "stream_status", ["message_17", "event_2165"],
                {"status": "one_time"}, events=["event_2165"])],
            "contextual_assertions": [{"meaning": "The INR 33550 prize event is already settled; its amount and settlement date need no model restatement.", "source_ids": ["event_2165"], "status": "raw_event_context"}],
            "acceptable_alternates": ["A precise windfall stream selector grounded in event_2165 may represent the same one-time closed claim."],
            "unsupported_or_harmful": ["Do not forecast recurring prize income, invent another payout, or treat the settled credit as still pending."],
            "ambiguity_notes": "The message confirms closure, while the linked structured event supplies the settled cash amount.",
        }
    if case == "holdout_user_246":
        return {
            "required_semantic_meanings": [{"statement": "Employment and the regular salary stream have ended; no salary after the final settled payroll is scheduled, and any separate final settlement remains unspecified.", "source_ids": ["message_192", "event_22603", "event_22609"]}],
            "required_contract_facts": [fact(case, "salary_ended", "stream_status", ["message_192", "event_22603", "event_22609"],
                {"status": "ended"},
                selector={"user_id": "user_246", "category": "salary", "direction": "credit", "currency": "ZAR", "description": "Payroll credit"},
                unresolved=["employment_end_date", "any_separate_final_settlement_amount", "any_separate_final_settlement_date"])],
            "contextual_assertions": [{"meaning": "Four regular ZAR credits and a distinct final employer payroll are settled history, not a promise of new income.", "source_ids": HISTORY[case], "status": "raw_event_context"}],
            "acceptable_alternates": ["A status fact targeting the supplied regular payroll history IDs is equivalent if it does not erase the distinct settled final payroll."],
            "unsupported_or_harmful": ["Do not forecast normal salary after employment ended or invent a further final-settlement amount or date."],
            "ambiguity_notes": "The exact employment end day and any separate final-settlement details are not supplied.",
        }
    if case == "holdout_user_267":
        return {
            "required_semantic_meanings": [{"statement": "A singular purchase was charged in an unspecified foreign currency; its final home-currency amount is unresolved until the transaction settles at the settlement-date rate.", "source_ids": ["message_208"]}],
            "required_contract_facts": [fact(case, "unfinalized_fx_charge", "amount_amendment", ["message_208"],
                {"money": None, "percent_increase": None, "scope": "one_cycle"},
                quote=("message_208", "final home-currency amount"),
                unresolved=["purchase_event_id", "charge_currency", "foreign_amount", "home_currency_amount", "settlement_date", "settlement_fx_rate"])],
            "contextual_assertions": [],
            "acceptable_alternates": [],
            "unsupported_or_harmful": ["Do not borrow EUR from past shopping debits or USD from payroll, infer a foreign amount/rate, or present a final home-currency debit before settlement."],
            "ambiguity_notes": "No matching purchase event or source currency is supplied. Within the frozen seven types, amount_amendment with null money captures that the final converted amount is still unresolved; it does not assert a numeric change.",
        }
    if case == "holdout_user_268":
        return {
            "required_semantic_meanings": [{"statement": "The verified prize claim is still processing and no proceeds have credited; amount, currency, date, and event ID remain unknown.", "source_ids": ["message_209"]}],
            "required_contract_facts": [fact(case, "prize_pending", "cash_classification", ["message_209"],
                {"classification": "pending_credit"}, quote=("message_209", "prize claim"),
                unresolved=["amount", "currency", "payment_date", "event_id"])],
            "contextual_assertions": [], "acceptable_alternates": [],
            "unsupported_or_harmful": ["Do not count verification as a settled credit or assign the EUR currency of unrelated salary to the prize."],
            "ambiguity_notes": "The message supplies neither a prize cash event nor its currency or amount.",
        }
    if case == "holdout_user_274":
        return fx_refund(case, "message_214")
    raise ValueError(f"unreviewed holdout case: {case}")


def fx_refund(case: str, message_id: str) -> dict:
    return {
        "required_semantic_meanings": [
            {"statement": "The foreign-currency refund remains in processing and is not an available settled credit.", "source_ids": [message_id]},
            {"statement": "The final home-currency credit depends on the rate at actual settlement; currency, amounts, rate, and date remain unknown.", "source_ids": [message_id]},
        ],
        "required_contract_facts": [fact(case, "fx_refund_pending", "cash_classification", [message_id],
            {"classification": "pending_credit"}, quote=(message_id, "foreign-currency refund"),
            unresolved=["refund_event_id", "refund_currency", "foreign_amount", "home_currency_amount", "settlement_date", "settlement_fx_rate"])],
        "contextual_assertions": [],
        "acceptable_alternates": [],
        "unsupported_or_harmful": ["Do not count the refund before settlement, copy an unrelated payroll/purchase currency, or calculate a home-currency credit from an unstated rate."],
        "ambiguity_notes": "No refund event, source currency, foreign amount, settlement date, or applicable settlement rate is supplied in this runtime input.",
    }


def build() -> dict:
    split = json.loads(SPLIT.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    dev = json.loads(DEV.read_text(encoding="utf-8"))
    holdout = split["holdout"]
    bound = {c["case_id"]: c for c in manifest["cases"]}
    if not (len(holdout) == len(bound) == 8):
        raise ValueError("holdout count mismatch")
    annotations = []
    for case in holdout:
        case_id = case["case_id"]
        if case_id not in bound or case["user_id"] != bound[case_id]["user_id"]:
            raise ValueError("holdout runtime binding mismatch")
        annotation = {
            "case_id": case_id, "user_id": case["user_id"],
            "supporting_evidence": {
                "message_ids": case["message_ids"], "image_ids": case["image_ids"],
                "event_ids": case["linked_event_ids"],
                "history_event_ids": HISTORY.get(case_id, []),
            },
            **reviewed(case_id),
            "review_status": "approved_for_holdout_benchmark",
            "runtime_input": {
                "manifest": "holdout_runtime_inputs_v1/manifest.json",
                "request_file": bound[case_id]["request_file"],
                "serialized_payload_sha256": bound[case_id]["serialized_payload_sha256"],
                "serialized_payload_bytes": bound[case_id]["serialized_payload_bytes"],
            },
            "semantic_pass_requires_nonempty_facts": True,
        }
        annotations.append(annotation)
    return {
        "version": "semantic-reference-annotations-holdout-20260912-v1-frozen",
        "scope": "holdout_only", "review_status": "approved_for_holdout_benchmark",
        "ground_truth": False, "model_calls": 0,
        "benchmark_conventions": dev["benchmark_conventions"],
        "contract_fact_types": dev["contract_fact_types"],
        "source_sha256": {
            "split": sha(SPLIT), "frozen_development_reference": sha(DEV),
            "runtime_manifest": sha(MANIFEST),
            "financial_events": sha(ROOT / "dataset/financial_events.csv"),
            "messages": sha(ROOT / "dataset/messages.csv"),
            "images": sha(ROOT / "dataset/images.csv"),
            "schema": sha(ROOT / "code/evidence.py"),
            "exported_schema": sha(ROOT / "code/evidence.schema.json"),
            "extractor": sha(ROOT / "code/prototype/extraction_experiment.py"),
        },
        "annotations": annotations,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    encoded = json.dumps(build(), ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
    if args.check:
        if OUT.read_bytes() != encoded:
            raise ValueError("frozen holdout reference differs from reviewed source")
    else:
        OUT.write_bytes(encoded)
    print(f"{'verified' if args.check else 'wrote'} 8 frozen holdout references")


if __name__ == "__main__":
    main()
