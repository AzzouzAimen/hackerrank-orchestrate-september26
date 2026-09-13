import unittest

from evidence import EvidenceBundle
from target_identity import target_kind, validate_target_identity


EVENTS = [
    {"event_id": "e1", "user_id": "u", "category": "salary", "direction": "credit",
     "currency": "USD", "description": "Payroll credit"},
    {"event_id": "e2", "user_id": "u", "category": "salary", "direction": "credit",
     "currency": "USD", "description": "Payroll credit"},
]
EVIDENCE = {"m": {"user_id": "u", "message_text": "A new bonus payment"}}


def parse(fact):
    return EvidenceBundle.model_validate({"facts": [fact]}).facts


def base(**changes):
    result = {
        "schema_version": "1.0", "fact_id": "f", "fact_type": "stream_status",
        "evidence_ids": ["m"], "affected_event_ids": [], "stream_selector": None,
        "source_target": None, "effective_from": None, "effective_until": None,
        "confirmation_state": "confirmed", "unresolved_fields": [],
        "payload": {"status": "ongoing"},
    }
    result.update(changes)
    return result


class TargetIdentityTests(unittest.TestCase):
    def test_exact_event_is_strict_and_known(self):
        facts = parse(base(affected_event_ids=["e1"], evidence_ids=["e1"]))
        self.assertEqual(target_kind(facts[0]), "exact_event")
        validate_target_identity(facts, EVENTS, {"e1": {"user_id": "u"}})

    def test_existing_stream_must_bind_history(self):
        selector = {"user_id": "u", "category": "salary", "direction": "credit",
                    "currency": "USD", "description": "Payroll credit"}
        facts = parse(base(stream_selector=selector))
        validate_target_identity(facts, EVENTS, EVIDENCE)
        selector["description"] = "Unknown payroll"
        facts = parse(base(stream_selector=selector))
        with self.assertRaisesRegex(ValueError, "binds no supplied event"):
            validate_target_identity(facts, EVENTS, EVIDENCE)

    def test_new_entity_requires_quote_and_unresolved_identity(self):
        target = {"evidence_id": "m", "quoted_text": "new bonus payment"}
        facts = parse(base(source_target=target, unresolved_fields=["target_identity"]))
        validate_target_identity(facts, EVENTS, EVIDENCE)
        facts = parse(base(source_target=target))
        with self.assertRaisesRegex(ValueError, "preserve unresolved identity"):
            validate_target_identity(facts, EVENTS, EVIDENCE)

    def test_resolver_compatibility_allows_only_consistent_redundancy(self):
        selector = {"user_id": "u", "category": "salary", "direction": "credit",
                    "currency": "USD", "description": "Payroll credit"}
        facts = parse(base(affected_event_ids=["e1"], stream_selector=selector, evidence_ids=["e1"]))
        with self.assertRaises(ValueError):
            validate_target_identity(facts, EVENTS, EVIDENCE)
        validate_target_identity(facts, EVENTS, EVIDENCE, allow_redundant_exact_selector=True)
        selector["description"] = "Other"
        facts = parse(base(affected_event_ids=["e1"], stream_selector=selector, evidence_ids=["e1"]))
        with self.assertRaisesRegex(ValueError, "does not bind exact"):
            validate_target_identity(facts, EVENTS, EVIDENCE, allow_redundant_exact_selector=True)
