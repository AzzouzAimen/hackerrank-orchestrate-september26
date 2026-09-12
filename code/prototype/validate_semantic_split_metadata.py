"""Offline semantic split metadata validator.

The family classifier is deliberately small and evidence-derived.  It is a
guardrail against stale placeholder/default labels, not semantic ground truth.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "dataset"
DEFAULT_MANIFEST = ROOT / "code/prototype/extraction_artifacts/semantic_inventory_01/semantic_split_20260912_v5.json"


def classify(text: str, events: pd.DataFrame, has_image: bool) -> str:
    t = text.lower()
    if "foreign-currency refund" in t:
        return "fx_refund"
    if "charged in a foreign currency" in t:
        return "fx_payment"
    if "prize" in t and ("reached your account" in t or any(events.status.eq("settled"))):
        return "prize_completed"
    if "prize" in t and ("processing" in t or "not been credited" in t):
        return "prize_pending"
    if "employment has ended" in t or "contract has ended" in t:
        return "ended_income"
    if ("monthly salary" in t or "gaji bulanan" in t) and ("increased" in t or "up" in t or "naik" in t):
        return "salary_change"
    if "one-time arrears" in t:
        return "arrears"
    if ("one-off adjustment" in t or "penyesuaian satu kali" in t) and has_image:
        return "salary_arrears"
    if "temporary monthly pay" in t:
        return "temporary_pay"
    if "bonus" in t and ("pending" in t or "waiting" in t or "belum" in t or "menunggu" in t):
        return "pending_income"
    if "payout" in t and "withdrawable" in t:
        return "pending_payout"
    if "invoice" in t:
        return "invoice"
    if "previous debit attempt failed" in t:
        return "failed_retry"
    if "same-owner" in t or "two accounts" in t and "matching debit" in t:
        return "transfer"
    if "portfolio" in t and "no cash proceeds" in t:
        return "investment_noncash"
    if "refund" in t:
        return "refund"
    if "childcare" in t and "recurring" in t:
        return "recurring_expense"
    if "rent" in t or "lease" in t:
        return "rent"
    if "receipt" in t and "payment was received" in t:
        return "receipt"
    raise AssertionError(f"no deterministic family rule for evidence: {text[:100]}")


def main(path: Path) -> int:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    messages = pd.read_csv(DATA / "messages.csv").set_index("message_id")
    images = pd.read_csv(DATA / "images.csv").set_index("image_id")
    events = pd.read_csv(DATA / "financial_events.csv").set_index("event_id")
    profiles = set(pd.read_csv(DATA / "financial_profiles.csv")["user_id"])
    all_cases = manifest["development"] + manifest["holdout"]
    assert len(manifest["development"]) == 14 and len(manifest["holdout"]) == 8
    assert len({c["case_id"] for c in all_cases}) == len(all_cases)
    assert manifest["development"][0]["split"] == "dev"
    assert all(c["split"] == "holdout" for c in manifest["holdout"])
    assert sum(c["contamination"] == "contaminated" for c in manifest["development"]) == 1
    assert all(c["user_id"] in profiles and re.fullmatch(r"user_\d+", c["user_id"]) for c in all_cases)
    for c in all_cases:
        ms = [messages.loc[m] for m in c["message_ids"]]
        assert ms and all(row["user_id"] == c["user_id"] for row in ms)
        assert all(i in images.index and images.loc[i, "user_id"] == c["user_id"] for i in c["image_ids"])
        assert all(e in events.index and events.loc[e, "user_id"] == c["user_id"] for e in c["linked_event_ids"])
        text = " ".join(str(row["message_text"]) for row in ms)
        ev = events.loc[c["linked_event_ids"]] if c["linked_event_ids"] else events.iloc[0:0]
        expected = classify(text, ev, bool(c["image_ids"]))
        assert c["semantic_family"] == expected, (c["user_id"], c["semantic_family"], expected)
        assert c["inclusion_reason"] not in {"distinct normalized template", "review_required", "refined_inventory"}
        assert "Evidence IDs and ownership verified" not in c["ambiguity_notes"]
        assert re.fullmatch(r"tmpl_[0-9a-f]{12}", c["message_template_id"])
    dev_templates = {c["message_template_id"] for c in manifest["development"]}
    hold_templates = {c["message_template_id"] for c in manifest["holdout"]}
    assert not dev_templates & hold_templates
    for name, expected in manifest["source_hashes"].items():
        assert hashlib.sha256((DATA / name).read_bytes()).hexdigest() == expected, name
    assert manifest["checks"]["model_calls"] == 0
    assert manifest["checks"]["sample_labels_used"] is False
    assert manifest["checks"]["dataset_mutated"] is False
    assert manifest["checks"]["holdout_selected_by_model_performance"] is False
    print(f"validated {len(all_cases)} cases; family, ownership, hashes, and split checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_MANIFEST))
