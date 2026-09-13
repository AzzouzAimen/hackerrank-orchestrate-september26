"""Executable target-identity contract shared by extraction and finance.

The seven semantic fact types keep their existing wire shape.  This module
defines how the three existing target fields are interpreted under
``target-identity-v1``:

* ``affected_event_ids``: exact supplied event occurrence(s);
* ``stream_selector``: an existing stream selector that binds supplied rows;
* ``source_target``: a new or unidentified entity quoted from evidence.

Exactly one representation is permitted.  The model is shown candidates made
from the same supplied events that the deterministic consumer later receives.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable


CONTRACT_VERSION = "target-identity-v1"
IDENTITY_UNKNOWN_NAMES = frozenset({"event_id", "event_ids", "target_identity"})


def _value(item: Any, name: str) -> Any:
    if isinstance(item, dict):
        return item.get(name)
    return getattr(item, name)


def selector_dict(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "user_id": event["user_id"],
        "category": event["category"],
        "direction": event["direction"],
        "currency": event["currency"],
        "description": event["description"],
    }


def target_candidates(events: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Build deterministic, output-ready event and stream candidates."""
    rows = list(events)
    exact_events = []
    stream_groups: dict[tuple[Any, ...], list[str]] = defaultdict(list)
    for event in rows:
        exact_events.append({
            "kind": "exact_event",
            "output": {
                "affected_event_ids": [event["event_id"]],
                "stream_selector": None,
                "source_target": None,
            },
            "identity": {
                key: event.get(key) for key in (
                    "event_id", "event_date", "settlement_date", "status",
                    "category", "direction", "amount", "currency", "description",
                    "linked_event_id",
                )
            },
        })
        if event.get("direction") not in {"debit", "credit"}:
            continue
        selector = selector_dict(event)
        key = tuple(selector[name] for name in
                    ("user_id", "category", "direction", "currency", "description"))
        stream_groups[key].append(event["event_id"])
    existing_streams = []
    for key, event_ids in sorted(stream_groups.items()):
        selector = dict(zip(
            ("user_id", "category", "direction", "currency", "description"), key
        ))
        existing_streams.append({
            "kind": "existing_stream",
            "output": {
                "affected_event_ids": [],
                "stream_selector": selector,
                "source_target": None,
            },
            "matched_event_ids": sorted(event_ids),
        })
    return {
        "contract_version": CONTRACT_VERSION,
        "exact_events": exact_events,
        "existing_streams": existing_streams,
        "new_or_unidentified": {
            "kind": "new_or_unidentified",
            "output_rule": {
                "affected_event_ids": [],
                "stream_selector": None,
                "source_target": {
                    "evidence_id": "a cited message ID",
                    "quoted_text": "an exact identifying quote from that message",
                },
                "unresolved_fields_must_include": "event_id or target_identity",
            },
        },
    }


def matching_event_ids(selector: Any, events: Iterable[dict[str, Any]]) -> set[str]:
    if selector is None:
        return set()
    return {
        event["event_id"] for event in events
        if all(_value(selector, name) == event[name]
               for name in ("user_id", "category", "direction", "currency"))
        and (_value(selector, "description") is None
             or _value(selector, "description") == event["description"])
    }


def target_kind(fact: Any) -> str:
    ids = list(_value(fact, "affected_event_ids") or [])
    selector = _value(fact, "stream_selector")
    source = _value(fact, "source_target")
    populated = sum((bool(ids), selector is not None, source is not None))
    if populated != 1:
        return "invalid_mixed_or_missing"
    if ids:
        return "exact_event"
    if selector is not None:
        return "existing_stream"
    return "new_or_unidentified"


def validate_target_identity(
    facts: Iterable[Any],
    events: Iterable[dict[str, Any]],
    evidence_index: dict[str, dict[str, Any]],
    *,
    allow_redundant_exact_selector: bool = False,
) -> None:
    """Reject target representations that cannot execute under this contract."""
    event_rows = list(events)
    event_ids = {event["event_id"] for event in event_rows}
    for fact in facts:
        fact_id = _value(fact, "fact_id")
        ids = list(_value(fact, "affected_event_ids") or [])
        selector = _value(fact, "stream_selector")
        source = _value(fact, "source_target")
        if allow_redundant_exact_selector and ids and selector is not None and source is None:
            unknown = set(ids) - event_ids
            selected = matching_event_ids(selector, event_rows)
            if unknown:
                raise ValueError(f"{fact_id}: unknown exact event target(s): {sorted(unknown)}")
            if not set(ids) <= selected:
                raise ValueError(f"{fact_id}: redundant selector does not bind exact event target")
            continue
        kind = target_kind(fact)
        if kind == "invalid_mixed_or_missing":
            raise ValueError(
                f"{fact_id}: exactly one of affected_event_ids, stream_selector, "
                "or source_target must identify the target"
            )
        if kind == "exact_event":
            unknown = set(_value(fact, "affected_event_ids")) - event_ids
            if unknown:
                raise ValueError(f"{fact_id}: unknown exact event target(s): {sorted(unknown)}")
            continue
        if kind == "existing_stream":
            selected = matching_event_ids(_value(fact, "stream_selector"), event_rows)
            if not selected:
                raise ValueError(f"{fact_id}: existing stream selector binds no supplied event")
            continue
        source = _value(fact, "source_target")
        evidence_id = _value(source, "evidence_id")
        quoted_text = _value(source, "quoted_text")
        row = evidence_index.get(evidence_id)
        if row is None or evidence_id not in _value(fact, "evidence_ids"):
            raise ValueError(f"{fact_id}: source target must use cited supplied evidence")
        if quoted_text not in row.get("message_text", ""):
            raise ValueError(f"{fact_id}: source target is not an exact evidence quote")
        unresolved = {str(name).casefold() for name in _value(fact, "unresolved_fields")}
        if not unresolved & IDENTITY_UNKNOWN_NAMES:
            raise ValueError(f"{fact_id}: new or unidentified target must preserve unresolved identity")


def binding_record(fact: Any, events: Iterable[dict[str, Any]]) -> dict[str, Any]:
    kind = target_kind(fact)
    if kind == "exact_event":
        bound = sorted(_value(fact, "affected_event_ids"))
    elif kind == "existing_stream":
        bound = sorted(matching_event_ids(_value(fact, "stream_selector"), events))
    else:
        bound = []
    return {"kind": kind, "bound_event_ids": bound, "executable": kind != "invalid_mixed_or_missing"}
