"""Trusted semantic guard and deterministic finance-boundary adapter."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from evidence import EvidenceBundle
from finance import resolve
from target_identity import validate_target_identity


def _unknown(fields: list[str], *needles: str) -> bool:
    names = {str(x).casefold() for x in fields}
    return any(any(needle in name for needle in needles) for name in names)


def guard_bundle(bundle: Any, events: list[dict], evidence_index: dict[str, dict]) -> dict:
    """Block explicit unsafe conditions without rewriting semantic claims."""
    parsed = EvidenceBundle.model_validate(deepcopy(bundle))
    blocked, trusted = [], []
    by_event = {row["event_id"]: row for row in events}
    try:
        validate_target_identity(parsed.facts, events, evidence_index)
    except Exception as exc:
        return {"facts": [], "blocked": [{"fact_id": None, "reasons": ["target_validation", str(exc)]}]}
    for model in parsed.facts:
        fact = model.model_dump(mode="json"); payload = fact["payload"]
        fields = fact.get("unresolved_fields", []); evidence_ids = set(fact["evidence_ids"]); reasons = []
        if fact["fact_type"] == "image_financial_value":
            label = payload["selected_field"].casefold()
            if fact.get("effective_from") or fact.get("effective_until"):
                reasons.append("image_does_not_supply_effective_range")
            if any(word in label for word in ("gross", "total", "subtotal")):
                reasons.append("gross_or_total_not_a_due_or_paid_value")
            if payload["value_type"] in {"balance_due", "current_amount_due"} and any(
                    word in label for word in ("received", "paid", "total", "gross")):
                reasons.append("label_value_semantic_conflict")
        elif fact["fact_type"] == "future_event_confirmation":
            if payload["money"]["value"] is None and not _unknown(fields, "amount", "value", "money"):
                reasons.append("unknown_amount_not_preserved")
            if payload["payment_date"] is None and not _unknown(fields, "date", "payday", "settlement"):
                reasons.append("unknown_payment_date_not_preserved")
            if payload["direction"] == "credit" and fact["confirmation_state"] == "confirmed":
                statuses = {by_event[eid]["status"] for eid in fact["affected_event_ids"] if eid in by_event}
                if statuses & {"pending", "scheduled", "failed", "cancelled", "unrealized"}:
                    reasons.append("confirmed_credit_has_unsettled_event")
                if fact.get("source_target") is not None and not statuses:
                    cited = " ".join(str(evidence_index.get(eid, {}).get("message_text", "")) for eid in evidence_ids).casefold()
                    if not any(word in cited for word in ("settled", "credited", "received", "completed")):
                        reasons.append("unidentified_future_credit_lacks_settlement_evidence")
        elif fact["fact_type"] == "cash_classification":
            if payload["classification"] == "contingent_income" and fact["confirmation_state"] == "confirmed":
                reasons.append("contingent_income_cannot_be_confirmed_cash")
        elif fact["fact_type"] == "amount_amendment":
            if payload["money"] is None and payload["percent_increase"] is None:
                reasons.append("amendment_has_no_supported_value")
            if payload["money"] is None and not _unknown(fields, "amount", "value", "money"):
                reasons.append("unknown_amendment_amount_not_preserved")
            if payload["scope"] == "unknown" and not _unknown(fields, "duration", "scope"):
                reasons.append("unknown_amendment_duration_not_preserved")
            if fact.get("effective_from") is None and not _unknown(fields, "date", "effective"):
                reasons.append("unknown_amendment_date_not_preserved")
        if fact.get("source_target") is not None and not _unknown(fields, "event_id", "target_identity"):
            reasons.append("source_target_identity_not_preserved")
        if evidence_ids and all(str(eid).startswith("image_") for eid in evidence_ids) and (
                fact.get("effective_from") or fact.get("effective_until")):
            reasons.append("image_only_fact_has_inherited_date")
        if reasons:
            blocked.append({"fact_id": fact["fact_id"], "fact": fact, "reasons": sorted(set(reasons))})
        else:
            trusted.append(fact)
    return {"facts": trusted, "blocked": blocked}


def _blocked_may_be_obligation(record: dict, events: list[dict]) -> bool:
    reasons = set(record.get("reasons", []))
    if reasons & {"gross_or_total_not_a_due_or_paid_value", "label_value_semantic_conflict"}:
        return False
    fact = record.get("fact")
    if fact is None:
        return True
    if fact.get("payload", {}).get("direction") == "debit":
        return True
    event_map = {row["event_id"]: row for row in events}
    if any(event_map.get(eid, {}).get("direction") == "debit" for eid in fact["affected_event_ids"]):
        return True
    return (fact.get("stream_selector") or {}).get("direction") == "debit"


@dataclass
class GuardedResolution:
    state: Any
    trusted_bundle: EvidenceBundle
    blocked: list[dict]


def guarded_resolve(raw_events: list[dict], profile: dict, request: dict,
                    extracted_bundle: dict, evidence_index: dict[str, dict]) -> GuardedResolution:
    guarded = guard_bundle(extracted_bundle, raw_events, evidence_index)
    trusted = EvidenceBundle.model_validate({"facts": guarded["facts"]})
    state = resolve(raw_events, profile, request, trusted.facts, evidence_index)
    for record in guarded["blocked"]:
        fact_id = record.get("fact_id") or "whole_bundle"
        state.issues.append(f"semantic_guard:{fact_id}: blocked ({','.join(record.get('reasons', []))})")
        if _blocked_may_be_obligation(record, raw_events):
            state.blockers.append(f"semantic_guard:{fact_id}: unresolved possible obligation")
    return GuardedResolution(state, trusted, guarded["blocked"])
