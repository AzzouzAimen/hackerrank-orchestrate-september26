from pathlib import Path

from input_preparation import prepare_case
from scoped_extraction import compose_scoped


def test_preparation_rejects_cross_request_and_future_message(tmp_path: Path):
    request = {"request_id":"r1","user_id":"u1","request_date":"2026-09-01"}
    events = [{"event_id":"e1","user_id":"u1"},{"event_id":"e2","user_id":"u2"}]
    messages = [{"message_id":"m1","user_id":"u1","request_id":"","sent_at":"2026-09-01T01:00:00Z"},
                {"message_id":"m2","user_id":"u1","request_id":"r2","sent_at":"2026-08-01T01:00:00Z"},
                {"message_id":"m3","user_id":"u1","request_id":"","sent_at":"2026-09-02T01:00:00Z"}]
    case = prepare_case(request, events, messages, [], tmp_path)
    assert [x["event_id"] for x in case["evidence"]["events"]] == ["e1"]
    assert [x["event_id"] for x in case["finance_events"]] == ["e1"]
    assert [x["message_id"] for x in case["evidence"]["messages"]] == ["m1"]


def test_preparation_includes_same_user_event_linked_image(tmp_path: Path):
    request = {"request_id":"r1","user_id":"u1","request_date":"2026-09-01"}
    events = [{"event_id":"e1","user_id":"u1"}]
    images = [{"image_id":"i1","user_id":"u1","request_id":"","related_event_id":"e1"},
              {"image_id":"i2","user_id":"u1","request_id":"r2","related_event_id":"e1"}]
    path = tmp_path / "dataset/media/images"
    path.mkdir(parents=True)
    (path / "i1.png").write_bytes(b"fixture")
    case = prepare_case(request, events, [], images, tmp_path)
    assert [x["image_id"] for x in case["evidence"]["images"]] == ["i1"]


def test_image_scope_cannot_emit_non_image_fact():
    case = {"evidence":{"events":[],"messages":[],"images":[]},"image_paths":["x"]}
    good = {"usable":True,"bundle":{"facts":[]},"attempts":[]}
    bad = {"usable":True,"bundle":{"facts":[{"fact_id":"x","fact_type":"cash_classification"}]},"attempts":[]}
    result = compose_scoped(case, good, bad)
    assert not result["usable"]
    assert result["blocked"][0]["reason"] == "non_image_fact_from_image_scope"


def test_unavailable_scope_fails_closed():
    case = {"evidence":{"events":[],"messages":[],"images":[]},"image_paths":[]}
    result = compose_scoped(case, {"usable":False,"bundle":None}, None)
    assert not result["usable"]
