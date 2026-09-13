"""Read-only submission dataset contract preflight; no model calls or predictions."""
from __future__ import annotations

from collections import Counter
from pathlib import Path

from input_preparation import prepare_case
from submission_runner import OUTPUT_FIELDS, read_csv


def validate(root: Path) -> dict:
    data = root / "dataset"
    requests = read_csv(data / "requests.csv")
    profiles = read_csv(data / "financial_profiles.csv")
    events = read_csv(data / "financial_events.csv")
    messages = read_csv(data / "messages.csv")
    images = read_csv(data / "images.csv")
    options = read_csv(data / "request_payment_options.csv")
    template = read_csv(data / "output.csv")
    ids = [r["request_id"] for r in requests]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate request IDs")
    profile_ids = {p["user_id"] for p in profiles}
    missing_profiles = sorted({r["user_id"] for r in requests} - profile_ids)
    if missing_profiles:
        raise ValueError("Missing profiles: " + ",".join(missing_profiles))
    template_ids = [r["request_id"] for r in template]
    if template and tuple(template[0]) != OUTPUT_FIELDS:
        raise ValueError("Output template columns differ")
    if template_ids != ids:
        raise ValueError("Output template request IDs/order differ")
    option_counts = Counter(o["request_id"] for o in options)
    invalid_counts = {rid: option_counts[rid] for rid in ids if not 2 <= option_counts[rid] <= 4}
    if invalid_counts:
        raise ValueError(f"Payment option cardinality differs: {invalid_counts}")
    prepared = [prepare_case(r, events, messages, images, root) for r in requests]
    included_messages = {m["message_id"] for c in prepared for m in c["evidence"]["messages"]}
    included_images = {i["image_id"] for c in prepared for i in c["evidence"]["images"]}
    request_users = {r["user_id"] for r in requests}
    eligible_messages = {m["message_id"] for m in messages if m["user_id"] in request_users}
    eligible_images = {i["image_id"] for i in images if any(
        r["user_id"] == i["user_id"] and i.get("request_id", "") in ("", r["request_id"])
        for r in requests
    )}
    if included_messages != eligible_messages:
        raise ValueError("Message selection does not cover each request-user message exactly")
    if included_images != eligible_images:
        raise ValueError("Image selection does not cover eligible request/event/user images")
    return {"requests":len(requests),"users":len({r['user_id'] for r in requests}),
            "events":len(events),"messages":len(included_messages),"images":len(included_images),
            "payment_options":len(options),"requests_with_messages":sum(bool(c['evidence']['messages']) for c in prepared),
            "requests_with_images":sum(bool(c['evidence']['images']) for c in prepared),
            "structured_only_requests":sum(not c['evidence']['messages'] and not c['evidence']['images'] for c in prepared),
            "model_events":sum(len(c['evidence']['events']) for c in prepared),
            "finance_events":sum(len(c['finance_events']) for c in prepared),
            "max_model_events":max(len(c['evidence']['events']) for c in prepared)}
