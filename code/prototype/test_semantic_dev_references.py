"""Deterministic development-reference checks; no model or holdout access."""
import copy
import hashlib
import json
import unittest
from unittest.mock import patch

from pydantic import ValidationError

from evidence import EvidenceBundle, validate_source_targets
from finance import resolve
from . import build_semantic_dev_inputs as inputs
from . import freeze_semantic_dev_references as frozen
from . import validate_semantic_reference_annotations as validator


class FrozenDevelopmentReferences(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.refs = frozen.build()
        cls.anns = {a["case_id"]: a for a in cls.refs["annotations"]}

    def test_full_offline_validation_and_rebuild_are_byte_exact(self):
        dataset_files = [frozen.ROOT / "dataset" / name for name in
                         ("financial_events.csv", "messages.csv", "images.csv")]
        before = [hashlib.sha256(path.read_bytes()).hexdigest() for path in dataset_files]
        with patch.object(inputs.extractor, "call_model", side_effect=AssertionError("model call forbidden")):
            validator.validate()
            manifest, payloads = inputs.build()
        self.assertEqual(len(payloads), 14)
        self.assertEqual(json.loads(inputs.OUT.joinpath("manifest.json").read_text(encoding="utf-8")), manifest)
        for name, body in payloads.items():
            self.assertEqual(inputs.OUT.joinpath(name).read_bytes(), body)
        self.assertEqual(frozen.OUT.read_bytes(),
                         (json.dumps(self.refs, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        self.assertEqual(before, [hashlib.sha256(path.read_bytes()).hexdigest() for path in dataset_files])

    def test_no_vacuous_development_case(self):
        self.assertEqual(len(self.anns), 14)
        for ann in self.anns.values():
            self.assertTrue(ann["required_semantic_meanings"])
            self.assertTrue(ann["required_contract_facts"])
            self.assertTrue(ann["semantic_pass_requires_nonempty_facts"])
            EvidenceBundle.model_validate({"facts": ann["required_contract_facts"]})

    def test_unquoted_target_and_fabricated_relationship_are_rejected(self):
        fact = copy.deepcopy(self.anns["dev_user_10"]["required_contract_facts"][0])
        evidence = {"message_07": {"user_id": "user_10", "message_text": "The next QuickCrew payout is pending."}}
        validate_source_targets(EvidenceBundle.model_validate({"facts": [fact]}).facts, evidence)
        fact["source_target"]["quoted_text"] = "settled QuickCrew payout"
        with self.assertRaises(ValueError):
            validate_source_targets(EvidenceBundle.model_validate({"facts": [fact]}).facts, evidence)
        transfer = copy.deepcopy(self.anns["dev_user_18"]["required_contract_facts"][0])
        transfer["source_target"] = None
        with self.assertRaises(ValidationError):
            EvidenceBundle.model_validate({"facts": [transfer]})

    def test_unidentified_transfer_does_not_exclude_unrelated_events(self):
        transfer = self.anns["dev_user_18"]["required_contract_facts"][0]
        fact = EvidenceBundle.model_validate({"facts": [transfer]}).facts[0]
        row = {"event_id": "unrelated", "user_id": "user_18", "category": "salary",
               "description": "Payroll credit", "direction": "credit", "amount": "20",
               "currency": "EUR", "event_date": "2026-06-15", "settlement_date": "2026-06-15",
               "status": "settled", "event_type": "income", "linked_event_id": "",
               "flexibility": "fixed", "minimum_allowed_amount": ""}
        profile = {"user_id": "user_18", "home_currency": "EUR"}
        request = {"user_id": "user_18", "request_date": "2026-07-01"}
        index = {"unrelated": row, "message_13": {"user_id": "user_18",
                 "message_text": "The matching debit and credit came from a transfer."}}
        state = resolve([row], profile, request, [fact], index)
        self.assertIsNone(state.events[0].excluded)
        self.assertTrue(any("relationship event IDs unresolved" in issue for issue in state.issues))


if __name__ == "__main__":
    unittest.main()
