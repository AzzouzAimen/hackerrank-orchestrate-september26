"""Deterministic request-scoped evidence preparation."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path


def _semantic_events(all_events: list[dict], messages: list[dict], images: list[dict]) -> list[dict]:
    """Bound model context while preserving deterministic stream/lifecycle evidence."""
    selected: set[str] = set()
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for event in all_events:
        if event.get("status") != "settled" or event.get("linked_event_id"):
            selected.add(event["event_id"])
        key = (event.get("category"), event.get("direction"), event.get("currency"))
        groups[key].append(event)
    # Three observations are the deterministic engine's minimum recurrence
    # support and bound long histories. This is context selection, not recurrence
    # inference; finance still receives every event.
    for history in groups.values():
        history.sort(key=lambda e: (e.get("settlement_date") or e.get("event_date", ""), e["event_id"]))
        selected.update(e["event_id"] for e in history[-3:])
    selected.update(x.get("related_event_id", "") for x in messages + images)
    selected.discard("")
    # Preserve one-hop lifecycle pairs in both directions.
    changed = True
    while changed:
        changed = False
        for event in all_events:
            linked = event.get("linked_event_id")
            if event["event_id"] in selected or (linked and linked in selected):
                before = len(selected); selected.add(event["event_id"])
                if event.get("linked_event_id"): selected.add(event["linked_event_id"])
                changed |= len(selected) != before
    return [event for event in all_events if event["event_id"] in selected]


def prepare_case(request: dict, events: list[dict], messages: list[dict], images: list[dict], root: Path) -> dict:
    """Select only same-user evidence available for a request.

    Messages are included only when unassigned or assigned to this request and
    sent no later than the request day. Images may be request-linked, event-linked,
    or user-level, but must not be assigned to a different request.
    All same-user events are retained so deterministic stream candidates have
    history; future structured rows remain data for the finance engine.
    """
    user, request_id, request_day = request["user_id"], request["request_id"], request["request_date"]
    finance_events = [row for row in events if row["user_id"] == user]
    selected_messages = [row for row in messages if row["user_id"] == user
                         and row.get("request_id", "") in ("", request_id)
                         and row["sent_at"][:10] <= request_day]
    selected_images = [row for row in images if row["user_id"] == user
                       and row.get("request_id", "") in ("", request_id)]
    paths = [root / "dataset/media/images" / f"{row['image_id']}.png" for row in selected_images]
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing request image(s): " + ", ".join(missing))
    evidence = {"events": _semantic_events(finance_events, selected_messages, selected_images),
                "messages": selected_messages, "images": selected_images}
    return {"case_id": request_id, "evidence": evidence, "finance_events": finance_events,
            "image_paths": [str(path) for path in paths]}
