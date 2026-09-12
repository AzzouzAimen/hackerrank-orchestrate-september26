"""Deterministic, evidence-bound scorer for frozen semantic references.

No model calls, competition labels, financial engine, or reference mutation.
The scorer judges required claims separately from supported extra claims.
"""
from __future__ import annotations

from collections import Counter
from decimal import Decimal, InvalidOperation
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code"))
from evidence import EvidenceBundle

BASE = ROOT / "code/prototype/extraction_artifacts/semantic_inventory_01"
REFERENCES = {
    "development": BASE / "semantic_reference_annotations_dev_20260912_v4_frozen.json",
    "holdout": BASE / "semantic_reference_annotations_holdout_20260912_v1_frozen.json",
}
REFERENCE_SHA256 = {
    "development": "5cb962ed7062a9d1c0e177aea10d95f9581d30c0e445faafc0480ac0e982f396",
    "holdout": "a7086bd128a51076dd06bb911cc422c34b15683fcaaadda60a49dba1724b235a",
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@lru_cache(maxsize=2)
def load_references(split: str) -> dict[str, Any]:
    if split not in REFERENCES:
        raise ValueError(f"Unknown split: {split}")
    raw = REFERENCES[split].read_bytes()
    if digest(raw) != REFERENCE_SHA256[split]:
        raise ValueError(f"Frozen {split} reference hash differs")
    data = json.loads(raw)
    expected_scope = "development_only" if split == "development" else "holdout_only"
    if not data["version"].endswith("-frozen") or data["scope"] != expected_scope:
        raise ValueError("Reference is not the frozen requested split")
    return data


@lru_cache(maxsize=32)
def case_context(split: str, case_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    refs = load_references(split)
    annotation = next((a for a in refs["annotations"] if a["case_id"] == case_id), None)
    if annotation is None:
        raise ValueError(f"Case {case_id} is not in frozen {split} references")
    manifest_path = BASE / annotation["runtime_input"]["manifest"]
    if digest(manifest_path.read_bytes()) != refs["source_sha256"]["runtime_manifest"]:
        raise ValueError("Frozen runtime manifest hash differs")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entry = next((c for c in manifest["cases"] if c["case_id"] == case_id), None)
    if entry is None or entry["user_id"] != annotation["user_id"]:
        raise ValueError("Missing or cross-user runtime binding")
    request_path = manifest_path.parent / entry["request_file"]
    payload = request_path.read_bytes()
    if (digest(payload) != entry["serialized_payload_sha256"] or
            digest(payload) != annotation["runtime_input"]["serialized_payload_sha256"] or
            len(payload) != annotation["runtime_input"]["serialized_payload_bytes"]):
        raise ValueError("Frozen runtime payload hash differs")
    body = json.loads(payload)
    content = body["messages"][1]["content"]
    text = content[0]["text"] if isinstance(content, list) else content
    raw = json.loads(text.split("CASE AND UNTRUSTED EVIDENCE:\n", 1)[1].split("\nREQUIRED JSON SCHEMA:", 1)[0])
    if raw["case_id"] != case_id:
        raise ValueError("Runtime case ID mismatch")
    context = {
        "events": {e["event_id"]: e for e in raw["events"]},
        "messages": {m["message_id"]: m for m in raw["messages"]},
        "images": {i["image_id"]: i for i in raw["images"]},
        "user_id": annotation["user_id"],
        "allowed_alternates": {
            "history_ids": any("event IDs" in rule and "status fact" in rule
                               for rule in annotation["acceptable_alternates"]),
            "contingent_classification": any("cash_classification=contingent_income" in rule
                                             for rule in annotation["acceptable_alternates"]),
        },
    }
    return annotation, context


def canonical_number(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    try:
        return Decimal(value)
    except InvalidOperation:
        return value


def same_money(left: dict | None, right: dict | None) -> bool:
    if left is None or right is None:
        return left is right
    return (left["currency"] == right["currency"] and
            canonical_number(left["value"]) == canonical_number(right["value"]))


def comparable_payload(ref: dict, got: dict) -> bool:
    kind, a, b = ref["fact_type"], ref["payload"], got["payload"]
    if kind == "stream_status":
        if got["fact_type"] == "cash_classification" and a["status"] == "contingent":
            return b["classification"] == "contingent_income"
        return got["fact_type"] == kind and a["status"] == b["status"]
    if kind == "cash_classification":
        return got["fact_type"] == kind and a["classification"] == b["classification"]
    if kind == "amount_amendment":
        return (got["fact_type"] == kind and same_money(a["money"], b["money"]) and
                canonical_number(a["percent_increase"]) == canonical_number(b["percent_increase"]) and
                a["scope"] == b["scope"])
    if kind == "date_or_schedule_amendment":
        return got["fact_type"] == kind and a == b
    if kind == "future_event_confirmation":
        return (got["fact_type"] == kind and same_money(a["money"], b["money"]) and
                a["payment_date"] == b["payment_date"] and a["direction"] == b["direction"])
    if kind == "lifecycle_relationship":
        return got["fact_type"] == kind and a == b
    if kind == "image_financial_value":
        due_types = {"balance_due", "current_amount_due"}
        kind_ok = a["value_type"] == b["value_type"] or {a["value_type"], b["value_type"]} <= due_types
        field_a, field_b = a["selected_field"].casefold(), b["selected_field"].casefold()
        field_ok = field_a == field_b or (min(len(field_a), len(field_b)) >= 8 and
                                         (field_a in field_b or field_b in field_a))
        return (got["fact_type"] == kind and kind_ok and same_money(a["money"], b["money"]) and
                a["image_id"] == b["image_id"] and field_ok)
    raise ValueError(f"Unknown frozen fact type: {kind}")


def selector_events(selector: dict, context: dict) -> set[str]:
    return {e["event_id"] for e in context["events"].values()
            if all(e[k] == selector[k] for k in ("user_id", "category", "direction", "currency"))
            and (selector["description"] is None or e["description"] == selector["description"])}


def source_target_equivalent(left: dict | None, right: dict | None, context: dict) -> bool:
    if left is None or right is None or left["evidence_id"] != right["evidence_id"]:
        return False
    message = context["messages"].get(left["evidence_id"])
    if message is None:
        return False
    a, b = left["quoted_text"].casefold(), right["quoted_text"].casefold()
    return (left["quoted_text"] in message["message_text"] and right["quoted_text"] in message["message_text"]
            and (a == b or (min(len(a), len(b)) >= 8 and (a in b or b in a))))


def target_equivalent(ref: dict, got: dict, context: dict) -> tuple[bool, str]:
    a_ids, b_ids = set(ref["affected_event_ids"]), set(got["affected_event_ids"])
    a_selector, b_selector = ref["stream_selector"], got["stream_selector"]
    a_source, b_source = ref.get("source_target"), got.get("source_target")
    if a_source or b_source:
        if not a_ids and not b_ids and not a_selector and not b_selector and source_target_equivalent(a_source, b_source, context):
            return True, "equivalent_source_quote" if a_source != b_source else "canonical_target"
        return False, "source_target_mismatch"
    if a_ids and b_ids and a_ids == b_ids:
        if a_selector == b_selector:
            return True, "canonical_target"
        if a_selector and b_selector and selector_events(a_selector, context) == selector_events(b_selector, context):
            return True, "equivalent_selector"
        return False, "selector_mismatch"
    if a_selector and b_selector and not a_ids and not b_ids:
        if a_selector == b_selector:
            return True, "canonical_target"
        a_events, b_events = selector_events(a_selector, context), selector_events(b_selector, context)
        if a_events and a_events == b_events:
            return True, "equivalent_selector"
        return False, "stream_selector_mismatch"
    # A terminated, precisely identified historical stream can be named by all
    # of its supplied event IDs. A single prior bonus ID is not equivalent to
    # a contingent future bonus stream.
    if (context["allowed_alternates"]["history_ids"] and
            ref["fact_type"] == "stream_status" and ref["payload"]["status"] == "ended"
            and a_selector and not a_ids and b_ids and not b_selector):
        stream_ids = selector_events(a_selector, context)
        if stream_ids and stream_ids == b_ids:
            return True, "equivalent_history_ids"
    return False, "event_or_stream_target_mismatch"


def alternate_type(ref: dict, got: dict, context: dict) -> bool:
    if (context["allowed_alternates"].get("contingent_classification", False) and
            ref["fact_type"] == "stream_status" and ref["payload"]["status"] == "contingent"
            and got["fact_type"] == "cash_classification"
            and got["payload"]["classification"] == "contingent_income"):
        # Historical settled bonus remains historical. The alternate must
        # begin after the latest cited message and after targeted settled rows.
        dates = [m["sent_at"][:10] for m in context["messages"].values()]
        boundary = max(dates) if dates else None
        selector = ref["stream_selector"]
        history = [context["events"][x]["settlement_date"] for x in selector_events(selector, context)
                   if context["events"][x]["status"] == "settled"] if selector else []
        start = got["effective_from"]
        return bool(start and (boundary is None or start >= boundary) and
                    all(not d or start > d for d in history))
    return False


def normalize_unknown(field: str) -> str:
    name = field.casefold()
    if "currency" in name: return "currency"
    if "event_id" in name or name == "event_ids": return "event_id"
    if "rate" in name: return "rate"
    if "amount" in name or "value" in name: return "amount"
    if "duration" in name or "scope" in name: return "duration"
    if "date" in name or "payday" in name or "effective_from" in name: return "date"
    return name


def unknown_errors(ref: dict, got: dict) -> list[str]:
    errors = []
    a, b = ref["payload"], got["payload"]
    if ref["fact_type"] in ("future_event_confirmation", "image_financial_value") and got["fact_type"] == ref["fact_type"]:
        if a["money"]["value"] is None and b["money"]["value"] is not None:
            errors.append("invented_unknown_amount")
        if ref["fact_type"] == "future_event_confirmation" and a["payment_date"] is None and b["payment_date"] is not None:
            errors.append("invented_unknown_payment_date")
    if ref["fact_type"] == "amount_amendment" and got["fact_type"] == "amount_amendment":
        if a["money"] is None and b["money"] is not None:
            errors.append("invented_unknown_amount")
        if a["percent_increase"] is None and b["percent_increase"] is not None:
            errors.append("invented_unknown_percentage")
        if a["scope"] == "unknown" and b["scope"] != "unknown":
            errors.append("invented_amendment_duration")
    if ref["effective_from"] is None and got["effective_from"] is not None and not (
            ref["fact_type"] == "stream_status" and ref["payload"]["status"] == "contingent" and
            got["fact_type"] == "cash_classification" and
            got["payload"]["classification"] == "contingent_income"):
        errors.append("invented_effective_from")
    if ref["effective_until"] is None and got["effective_until"] is not None:
        errors.append("invented_effective_until")
    if ref["confirmation_state"] == "uncertain" and got["confirmation_state"] == "confirmed":
        errors.append("uncertain_event_asserted_confirmed")
    if ref.get("source_target") and not got.get("source_target"):
        if got["affected_event_ids"]:
            errors.append("invented_event_target")
        if got["stream_selector"] is not None:
            errors.append("invented_stream_currency_or_target")
    expected = {normalize_unknown(x) for x in ref["unresolved_fields"]}
    actual = {normalize_unknown(x) for x in got["unresolved_fields"]}
    for missing in sorted(expected - actual):
        errors.append(f"unmarked_unknown_{missing}")
    return sorted(set(errors))


def evidence_errors(fact: dict, context: dict) -> list[str]:
    errors = []
    events, messages, images = context["events"], context["messages"], context["images"]
    index = {**events, **messages, **images}
    for identifier in fact["evidence_ids"]:
        if identifier not in index or index[identifier]["user_id"] != context["user_id"]:
            errors.append(f"unknown_or_foreign_evidence:{identifier}")
    for identifier in fact["affected_event_ids"]:
        if identifier not in events or events[identifier]["user_id"] != context["user_id"]:
            errors.append(f"unknown_or_foreign_event_target:{identifier}")
    selector = fact["stream_selector"]
    if selector:
        if selector["user_id"] != context["user_id"]:
            errors.append("cross_user_stream_selector")
        relevant = [e for e in events.values() if e["category"] == selector["category"]
                    and e["direction"] == selector["direction"] and e["currency"] == selector["currency"]]
        cited = " ".join(messages[m]["message_text"] for m in fact["evidence_ids"] if m in messages)
        if not relevant and selector["currency"] not in cited:
            errors.append("unproven_stream_currency")
    source = fact.get("source_target")
    if source:
        row = messages.get(source["evidence_id"])
        if row is None or source["evidence_id"] not in fact["evidence_ids"] or source["quoted_text"] not in row["message_text"]:
            errors.append("unquoted_source_target")
    if fact["fact_type"] == "lifecycle_relationship":
        parent = fact["payload"]["related_event_id"]
        if parent is not None and parent not in events:
            errors.append("unknown_lifecycle_parent")
    if fact["fact_type"] == "image_financial_value":
        image_id = fact["payload"]["image_id"]
        image = images.get(image_id)
        if image is None or image_id not in fact["evidence_ids"]:
            errors.append("unknown_image_source")
        elif image["related_event_id"] not in fact["affected_event_ids"]:
            errors.append("image_event_link_mismatch")
    return sorted(set(errors))


def detail_errors(ref: dict, got: dict, context: dict) -> list[str]:
    errors = []
    a, b = ref["payload"], got["payload"]
    kind = ref["fact_type"]
    if kind == "stream_status":
        if got["fact_type"] == "stream_status" and a["status"] != b["status"]:
            errors.append("wrong_stream_status")
        elif got["fact_type"] == "cash_classification" and b["classification"] != "contingent_income":
            errors.append("wrong_cash_classification")
    elif kind == "cash_classification" and got["fact_type"] == kind and a["classification"] != b["classification"]:
        errors.append("wrong_cash_classification")
    elif kind == "lifecycle_relationship" and got["fact_type"] == kind:
        if a["relationship"] != b["relationship"]:
            errors.append("wrong_lifecycle_relationship")
        if a["related_event_id"] != b["related_event_id"]:
            errors.append("wrong_lifecycle_parent")
    elif kind == "image_financial_value" and got["fact_type"] == kind:
        if a["value_type"] != b["value_type"] and {a["value_type"], b["value_type"]} != {"balance_due", "current_amount_due"}:
            errors.append("wrong_image_value_meaning")
        if not same_money(a["money"], b["money"]):
            errors.append("wrong_image_money")
        if a["image_id"] != b["image_id"]:
            errors.append("wrong_image_id")
        left, right = a["selected_field"].casefold(), b["selected_field"].casefold()
        if left != right and not (min(len(left), len(right)) >= 8 and (left in right or right in left)):
            errors.append("wrong_image_field")
    elif kind == "future_event_confirmation" and got["fact_type"] == kind:
        if not same_money(a["money"], b["money"]):
            errors.append("wrong_money_or_currency")
        if a["payment_date"] != b["payment_date"]:
            errors.append("wrong_payment_date")
        if a["direction"] != b["direction"]:
            errors.append("wrong_cash_direction")
    elif kind == "amount_amendment" and got["fact_type"] == kind:
        if not same_money(a["money"], b["money"]):
            errors.append("wrong_money_or_currency")
        if canonical_number(a["percent_increase"]) != canonical_number(b["percent_increase"]):
            errors.append("wrong_percentage")
        if a["scope"] != b["scope"]:
            errors.append("wrong_amendment_scope")
    elif kind == "date_or_schedule_amendment" and got["fact_type"] == kind and a != b:
        errors.append("wrong_schedule")
    return errors


def compare_pair(ref: dict, got: dict, context: dict) -> dict[str, Any]:
    alt = alternate_type(ref, got, context)
    type_ok = ref["fact_type"] == got["fact_type"] or alt
    target_ok, target_rule = target_equivalent(ref, got, context)
    payload_ok = comparable_payload(ref, got) if type_ok else False
    bounds_ok = (ref["effective_until"] == got["effective_until"] and
                 (ref["effective_from"] == got["effective_from"] or alt))
    confirmation_ok = ref["confirmation_state"] == got["confirmation_state"]
    uncertainty = unknown_errors(ref, got)
    provenance = evidence_errors(got, context)
    if not set(ref["evidence_ids"]) & set(got["evidence_ids"]):
        provenance.append("missing_supporting_evidence_citation")
    details = detail_errors(ref, got, context) if type_ok else []
    if not type_ok:
        details.append("wrong_fact_type")
    if not target_ok:
        details.append("wrong_target")
    if not bounds_ok:
        details.append("wrong_effective_range")
    if not confirmation_ok:
        details.append("wrong_confirmation_state")
    if type_ok and not payload_ok and not detail_errors(ref, got, context):
        details.append("wrong_payload")
    passed = bool(type_ok and target_ok and payload_ok and bounds_ok and confirmation_ok
                  and not uncertainty and not provenance)
    representation = "alternate" if alt or target_rule.startswith("equivalent") else "canonical"
    kind = ref["fact_type"]
    value_correct = None
    if kind == "future_event_confirmation" and got["fact_type"] == kind:
        value_correct = same_money(ref["payload"]["money"], got["payload"]["money"])
    elif kind == "amount_amendment" and got["fact_type"] == kind:
        value_correct = (same_money(ref["payload"]["money"], got["payload"]["money"]) and
                         canonical_number(ref["payload"]["percent_increase"]) ==
                         canonical_number(got["payload"]["percent_increase"]))
    elif kind == "image_financial_value" and got["fact_type"] == kind:
        value_correct = same_money(ref["payload"]["money"], got["payload"]["money"])
    elif kind == "date_or_schedule_amendment" and got["fact_type"] == kind:
        value_correct = ref["payload"] == got["payload"]
    image_semantics = None
    if kind == "image_financial_value" and got["fact_type"] == kind:
        a, b = ref["payload"], got["payload"]
        labels_ok = (a["value_type"] == b["value_type"] or
                     {a["value_type"], b["value_type"]} == {"balance_due", "current_amount_due"})
        left, right = a["selected_field"].casefold(), b["selected_field"].casefold()
        field_ok = left == right or (min(len(left), len(right)) >= 8 and
                                     (left in right or right in left))
        image_semantics = labels_ok and field_ok and a["image_id"] == b["image_id"]
    return {
        "reference_fact_id": ref["fact_id"], "actual_fact_id": got["fact_id"],
        "reference_fact_type": ref["fact_type"], "actual_fact_type": got["fact_type"],
        "representation": representation, "target_rule": target_rule,
        "dimensions": {
            "fact_type_correct": type_ok, "target_correct": target_ok,
            "value_correct": value_correct,
            "lifecycle_status_correct": payload_ok if kind in ("lifecycle_relationship", "stream_status", "cash_classification") else None,
            "image_value_semantics_correct": image_semantics,
            "effective_range_correct": bounds_ok,
            "confirmation_correct": confirmation_ok,
            "unknown_preserved": not uncertainty,
        },
        "errors": sorted(set(details)), "unknown_errors": uncertainty,
        "provenance_errors": provenance, "passed": passed,
    }


def pair_weight(ref: dict, got: dict, result: dict) -> int:
    if not result["dimensions"]["fact_type_correct"] and not result["dimensions"]["target_correct"]:
        return 0
    score = (100 if result["dimensions"]["fact_type_correct"] else 0)
    score += 100 if result["dimensions"]["target_correct"] else 0
    score += 100 if result["dimensions"]["fact_type_correct"] and comparable_payload(ref, got) else 0
    score += 20 * len(set(ref["evidence_ids"]) & set(got["evidence_ids"]))
    score += 10 if result["passed"] else 0
    return score


def match_required(reference_facts: list[dict], actual_facts: list[dict], context: dict) -> tuple[list[dict], set[int]]:
    # Maximum-weight one-to-one assignment prevents an extra claim from
    # stealing a match needed by another meaning. The number of required
    # facts per frozen case is small; complexity is O(actual * required * 2^required).
    count = len(reference_facts)
    if count > 16:
        raise ValueError("Frozen case has too many required facts for exact matching")
    comparisons = [[compare_pair(ref, got, context) for ref in reference_facts]
                   for got in actual_facts]
    states: dict[int, tuple[int, tuple[int, ...]]] = {0: (0, (-1,) * count)}
    for ai, got in enumerate(actual_facts):
        next_states = states.copy()
        for mask, (score, assignment) in states.items():
            for ri, ref in enumerate(reference_facts):
                if mask & (1 << ri):
                    continue
                result = comparisons[ai][ri]
                weight = pair_weight(ref, got, result)
                if not weight:
                    continue
                new_mask = mask | (1 << ri)
                new_score = score + weight
                previous = next_states.get(new_mask)
                if previous is None or new_score > previous[0]:
                    new_assignment = list(assignment)
                    new_assignment[ri] = ai
                    next_states[new_mask] = (new_score, tuple(new_assignment))
        states = next_states
    _, assignment = max(states.values(), key=lambda item: (item[0], sum(ai >= 0 for ai in item[1])))
    matches = {ri: comparisons[ai][ri] for ri, ai in enumerate(assignment) if ai >= 0}
    used = {ai for ai in assignment if ai >= 0}
    rows = []
    for ri, ref in enumerate(reference_facts):
        rows.append(matches.get(ri, {
            "reference_fact_id": ref["fact_id"], "actual_fact_id": None,
            "reference_fact_type": ref["fact_type"], "actual_fact_type": None,
            "representation": None, "target_rule": None,
            "dimensions": {"fact_type_correct": None, "target_correct": None,
                           "value_correct": None, "lifecycle_status_correct": None,
                           "image_value_semantics_correct": None,
                           "effective_range_correct": None,
                           "confirmation_correct": None, "unknown_preserved": None},
            "errors": ["missing_required_fact"], "unknown_errors": [],
            "provenance_errors": [], "passed": False,
        }))
    return rows, used


def meaning_fact_groups(annotation: dict) -> list[list[int]]:
    meanings, facts = annotation["required_semantic_meanings"], annotation["required_contract_facts"]
    groups: list[list[int]] = [[] for _ in meanings]
    for fi, fact in enumerate(facts):
        scores = [len(set(fact["evidence_ids"]) & set(meaning["source_ids"])) for meaning in meanings]
        best = max(scores)
        matches = [mi for mi, value in enumerate(scores) if value == best]
        chosen = min(matches, key=lambda mi: (abs(mi - min(fi, len(meanings) - 1)), mi))
        groups[chosen].append(fi)
    # One compact fact can encode several statements, such as pending refund
    # status plus explicitly unresolved settlement FX.
    for mi, group in enumerate(groups):
        if not group:
            best = max(range(len(facts)), key=lambda fi: len(set(facts[fi]["evidence_ids"]) &
                                                           set(meanings[mi]["source_ids"])))
            group.append(best)
    return groups


def parse_bundle(output: Any) -> tuple[list[dict], str, list[str]]:
    """Validate the complete bundle before interpreting any of its claims."""
    if output is None:
        return [], "unavailable", []
    if isinstance(output, EvidenceBundle):
        bundle = output
    else:
        if isinstance(output, (str, bytes)):
            try:
                output = json.loads(output)
            except (ValueError, UnicodeDecodeError) as exc:
                return [], "invalid_json", [str(exc)]
        try:
            bundle = EvidenceBundle.model_validate(output)
        except ValidationError as exc:
            return [], "invalid_schema", [
                f"{'.'.join(str(x) for x in issue['loc'])}: {issue['msg']}"
                for issue in exc.errors()
            ]
    return [fact.model_dump(mode="json") for fact in bundle.facts], "valid", []


def related_reference(fact: dict, refs: list[dict], context: dict) -> tuple[dict | None, dict | None]:
    ranked = []
    for ref in refs:
        result = compare_pair(ref, fact, context)
        weight = pair_weight(ref, fact, result)
        if weight:
            ranked.append((weight, result["passed"], ref, result))
    if not ranked:
        return None, None
    _, _, ref, result = max(ranked, key=lambda row: (row[0], row[1]))
    return ref, result


def supported_extra(fact: dict, refs: list[dict], context: dict) -> tuple[bool, str]:
    """Conservatively accept evidence-backed, optional claims.

    Pixel-derived values need an annotated semantic source; mere access to an
    image ID cannot prove the value or its label. Structured event fields are
    accepted only when their exact status/amount/date/link supports the claim.
    """
    if evidence_errors(fact, context):
        return False, "invalid_evidence_or_target_provenance"
    for ref in refs:
        if compare_pair(ref, fact, context)["passed"]:
            return True, "supported_duplicate_meaning"
    kind, payload = fact["fact_type"], fact["payload"]
    ids = fact["affected_event_ids"]
    events = context["events"]
    if ids and (fact["stream_selector"] is not None or fact.get("source_target") is not None or
                fact["effective_from"] is not None or fact["effective_until"] is not None):
        return False, "extra_structured_claim_has_unproven_target_or_effective_range"
    if kind == "cash_classification" and len(ids) == 1:
        if ids[0] not in fact["evidence_ids"]:
            return False, "uncited_structured_event_restatement"
        event = events[ids[0]]
        status, direction = event["status"], event["direction"]
        expected = {
            "unrealized": "non_cash_valuation",
            "pending": "pending_credit" if direction == "credit" else None,
            "failed": "historical_only", "cancelled": "historical_only",
            "settled": "cash",
        }.get(status)
        if expected == payload["classification"]:
            return True, "structured_event_cash_state"
    if kind == "lifecycle_relationship" and len(ids) == 1:
        if ids[0] not in fact["evidence_ids"]:
            return False, "uncited_structured_event_restatement"
        event = events[ids[0]]
        parent_id = payload["related_event_id"]
        parent = events.get(parent_id) if parent_id else None
        if parent and event["linked_event_id"] == parent_id:
            relation = payload["relationship"]
            if relation == "refund_of" and event["event_type"] == "refund":
                return True, "structured_refund_link"
            if relation == "retry_of" and ("retry" in event["description"].casefold() or parent["status"] == "failed"):
                return True, "structured_retry_link"
            if relation == "settlement_of" and event["status"] == "settled":
                return True, "structured_settlement_link"
    if kind == "future_event_confirmation" and len(ids) == 1:
        if ids[0] not in fact["evidence_ids"]:
            return False, "uncited_structured_event_restatement"
        event = events[ids[0]]
        money = payload["money"]
        if (event["status"] in {"scheduled", "pending"} and
                payload["direction"] == event["direction"] and
                money["currency"] == event["currency"] and
                canonical_number(money["value"]) == canonical_number(event["amount"]) and
                payload["payment_date"] == event["settlement_date"] and
                (event["direction"] == "debit" or fact["confirmation_state"] == "uncertain")):
            return True, "structured_event_restatement"
    return False, "not_supported_by_frozen_reference_or_structured_evidence"


def harmful_errors(ref: dict | None, fact: dict, annotation: dict, context: dict) -> list[str]:
    """Identify financially consequential false claims separately from misses."""
    kind, payload = fact["fact_type"], fact["payload"]
    errors = []
    if ref is not None:
        expected = ref["payload"]
        if (ref["fact_type"] == "image_financial_value" and kind == "image_financial_value"
                and ref["payload"]["value_type"] in {"balance_due", "current_amount_due"}
                and ref["payload"]["image_id"] == payload["image_id"]):
            due = canonical_number(expected["money"]["value"])
            actual = canonical_number(payload["money"]["value"])
            paid_values = [canonical_number(r["payload"]["money"]["value"])
                           for r in annotation["required_contract_facts"]
                           if r["fact_type"] == "image_financial_value" and
                           r["payload"]["value_type"] == "amount_paid" and
                           r["payload"]["image_id"] == payload["image_id"]]
            if actual != due and ("total" in payload["selected_field"].casefold() or
                                  any(actual == due + paid for paid in paid_values)):
                errors.append("gross_total_as_current_due")
            elif payload["value_type"] == "amount_paid":
                errors.append("amount_paid_as_current_due")
        if (ref["fact_type"] == "cash_classification" and kind == "cash_classification" and
                expected["classification"] in {"pending_credit", "non_cash_valuation", "contingent_income"}
                and payload["classification"] == "cash"):
            errors.append("unavailable_value_as_cash")
        if (ref["fact_type"] == "lifecycle_relationship" and kind == "lifecycle_relationship" and
                expected["relationship"] != payload["relationship"]):
            errors.append("false_lifecycle_relationship")
        if (ref["fact_type"] == "stream_status" and kind == "stream_status" and
                expected["status"] in {"ended", "contingent", "one_time"} and
                payload["status"] == "ongoing"):
            errors.append("unsupported_recurring_income")
        if (ref["fact_type"] == "amount_amendment" and kind == "amount_amendment" and
                expected["money"] is None and payload["money"] is not None):
            errors.append("calculated_unsupported_amendment_amount")
        if (ref["fact_type"] == "future_event_confirmation" and kind == "future_event_confirmation" and
                ref["confirmation_state"] == "uncertain" and fact["confirmation_state"] == "confirmed" and
                payload["direction"] == "credit"):
            errors.append("uncertain_income_asserted_confirmed")
    if kind == "cash_classification":
        for event_id in fact["affected_event_ids"]:
            event = context["events"].get(event_id)
            if event and event["status"] in {"pending", "unrealized", "failed", "cancelled"} and payload["classification"] == "cash":
                errors.append("unavailable_event_as_cash")
    if kind == "future_event_confirmation" and payload["direction"] == "credit":
        if fact["confirmation_state"] == "confirmed" and any(
                context["events"].get(event_id, {}).get("status") in {"pending", "failed", "cancelled", "unrealized"}
                for event_id in fact["affected_event_ids"]):
            errors.append("unsettled_credit_asserted_confirmed")
    return sorted(set(errors))


def score_case(split: str, case_id: str, output: Any) -> dict[str, Any]:
    annotation, context = case_context(split, case_id)
    reference_facts = annotation["required_contract_facts"]
    actual_facts, parse_status, parse_errors = parse_bundle(output)
    availability = "unavailable" if parse_status == "unavailable" else (
        "invalid_output" if parse_status != "valid" else
        "empty_facts" if not actual_facts else "available")
    matches, used = match_required(reference_facts, actual_facts, context)
    groups = meaning_fact_groups(annotation)
    meaning_rows = []
    for mi, meaning in enumerate(annotation["required_semantic_meanings"]):
        indices = groups[mi]
        passed = bool(actual_facts) and all(matches[fi]["passed"] for fi in indices)
        meaning_rows.append({
            "index": mi + 1, "meaning": meaning["statement"], "source_ids": meaning["source_ids"],
            "required_fact_ids": [reference_facts[fi]["fact_id"] for fi in indices],
            "passed": passed,
        })
    unsupported = []
    harmful = []
    unknown = []
    for match in matches:
        if match["actual_fact_id"] is None:
            continue
        fact = next(f for f in actual_facts if f["fact_id"] == match["actual_fact_id"])
        ref = next(r for r in reference_facts if r["fact_id"] == match["reference_fact_id"])
        if not match["passed"]:
            unsupported.append({"fact_id": fact["fact_id"], "fact_type": fact["fact_type"],
                                "reasons": sorted(set(match["errors"] + match["provenance_errors"] +
                                                      match["unknown_errors"]))})
        for error in match["unknown_errors"]:
            unknown.append({"fact_id": fact["fact_id"], "error": error})
        for error in harmful_errors(ref, fact, annotation, context):
            harmful.append({"fact_id": fact["fact_id"], "error": error})
    extras = []
    for ai, fact in enumerate(actual_facts):
        if ai in used:
            continue
        supported, reason = supported_extra(fact, reference_facts, context)
        extras.append({"fact_id": fact["fact_id"], "fact_type": fact["fact_type"],
                       "supported": supported, "reason": reason})
        if not supported:
            unsupported.append({"fact_id": fact["fact_id"], "fact_type": fact["fact_type"],
                                "reasons": [reason] + evidence_errors(fact, context)})
        near_ref, near = related_reference(fact, reference_facts, context)
        if near:
            for error in near["unknown_errors"]:
                unknown.append({"fact_id": fact["fact_id"], "error": error})
        for error in harmful_errors(near_ref, fact, annotation, context):
            harmful.append({"fact_id": fact["fact_id"], "error": error})
    categories = set()
    if parse_status != "valid": categories.add("schema_or_parse")
    if availability != "available": categories.add("output_availability")
    if any(not row["passed"] for row in meaning_rows): categories.add("missing_required_meaning")
    for match in matches:
        for dimension, value in match["dimensions"].items():
            if value is False and match["actual_fact_id"] is not None:
                categories.add(dimension)
    if unknown: categories.add("unknown_preservation")
    if unsupported: categories.add("unsupported_claim")
    if harmful: categories.add("harmful_interpretation")
    passed = (parse_status == "valid" and availability == "available" and
              all(row["passed"] for row in meaning_rows) and not unsupported and
              not unknown and not harmful)
    return {
        "split": split, "case_id": case_id, "user_id": annotation["user_id"],
        "runtime_payload_sha256": annotation["runtime_input"]["serialized_payload_sha256"],
        "schema": {"status": parse_status, "valid": parse_status == "valid", "errors": parse_errors},
        "output_availability": availability, "fact_count": len(actual_facts),
        "required_meanings": meaning_rows, "required_fact_matches": matches,
        "missing_meanings": [m["meaning"] for m in meaning_rows if not m["passed"]],
        "missing_facts": [m["reference_fact_id"] for m in matches if m["actual_fact_id"] is None],
        "extra_facts": extras, "unsupported_facts": unsupported,
        "unknown_preservation_errors": unknown, "harmful_errors": harmful,
        "failure_categories": sorted(categories), "semantic_pass": passed,
    }


def summarize(cases: list[dict]) -> dict[str, Any]:
    categories: Counter[str] = Counter()
    required_types: Counter[str] = Counter()
    missing_types: Counter[str] = Counter()
    failed_types: Counter[str] = Counter()
    unsupported_types: Counter[str] = Counter()
    harmful_errors: Counter[str] = Counter()
    unknown_errors_by_kind: Counter[str] = Counter()
    schema_status: Counter[str] = Counter()
    availability: Counter[str] = Counter()
    dimension_counts: dict[str, Counter[str]] = {}
    for case in cases:
        categories.update(case["failure_categories"])
        schema_status[case["schema"]["status"]] += 1
        availability[case["output_availability"]] += 1
        harmful_errors.update(error["error"] for error in case["harmful_errors"])
        unknown_errors_by_kind.update(error["error"] for error in case["unknown_preservation_errors"])
        for match in case["required_fact_matches"]:
            kind = match["reference_fact_type"]
            required_types[kind] += 1
            if match["actual_fact_id"] is None:
                missing_types[kind] += 1
            elif not match["passed"]:
                failed_types[kind] += 1
            for dimension, value in match["dimensions"].items():
                if value is None:
                    continue
                dimension_counts.setdefault(dimension, Counter())["passed" if value else "failed"] += 1
        unsupported_types.update(f["fact_type"] for f in case["unsupported_facts"])
    return {
        "cases": len(cases), "passed_cases": sum(c["semantic_pass"] for c in cases),
        "failed_cases": sum(not c["semantic_pass"] for c in cases),
        "required_meanings": sum(len(c["required_meanings"]) for c in cases),
        "passed_meanings": sum(m["passed"] for c in cases for m in c["required_meanings"]),
        "failure_categories_by_case": dict(sorted(categories.items())),
        "schema_status_by_case": dict(sorted(schema_status.items())),
        "output_availability_by_case": dict(sorted(availability.items())),
        "harmful_error_counts": dict(sorted(harmful_errors.items())),
        "unknown_error_counts": dict(sorted(unknown_errors_by_kind.items())),
        "required_fact_types": dict(sorted(required_types.items())),
        "missing_fact_types": dict(sorted(missing_types.items())),
        "failed_fact_types": dict(sorted(failed_types.items())),
        "unsupported_fact_types": dict(sorted(unsupported_types.items())),
        "dimension_counts": {k: dict(v) for k, v in sorted(dimension_counts.items())},
    }


def score_set(split: str, outputs: dict[str, Any]) -> dict[str, Any]:
    cases = [score_case(split, a["case_id"], outputs.get(a["case_id"]))
             for a in load_references(split)["annotations"]]
    return {"split": split, "summary": summarize(cases), "cases": cases}


def human_report(result: dict) -> str:
    cases = result.get("cases", [result])
    summary = result.get("summary", summarize(cases))
    lines = [f"Semantic benchmark: {result['split']} | {summary['passed_cases']}/{summary['cases']} cases passed; "
             f"{summary['passed_meanings']}/{summary['required_meanings']} required meanings covered"]
    if summary["failure_categories_by_case"]:
        lines.append("Failures by category (cases): " + ", ".join(
            f"{key}={value}" for key, value in summary["failure_categories_by_case"].items()))
    for case in cases:
        status = "PASS" if case["semantic_pass"] else "FAIL"
        lines.append(f"{status} {case['case_id']}: {sum(m['passed'] for m in case['required_meanings'])}/"
                     f"{len(case['required_meanings'])} meanings; schema={case['schema']['status']}; "
                     f"output={case['output_availability']}; "
                     f"categories={','.join(case['failure_categories']) or 'none'}")
    return "\n".join(lines) + "\n"
