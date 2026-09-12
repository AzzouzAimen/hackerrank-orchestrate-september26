"""Offline holdout-reference tests; never query the model or sample labels."""
import copy
import hashlib
import json
import unittest
from unittest.mock import patch

from evidence import EvidenceBundle, validate_source_targets
from . import build_semantic_holdout_inputs as inputs
from . import freeze_semantic_holdout_references as frozen
from . import validate_semantic_holdout_references as validator


class FrozenHoldoutReferences(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.refs = frozen.build()
        cls.anns = {a["case_id"]: a for a in cls.refs["annotations"]}

    def test_candidate_and_input_rebuild_are_offline_and_read_only(self):
        paths = [frozen.DEV, frozen.SPLIT] + [frozen.ROOT / "dataset" / name for name in
            ("financial_events.csv", "messages.csv", "images.csv")]
        before = [hashlib.sha256(path.read_bytes()).hexdigest() for path in paths]
        with patch.object(inputs.extractor, "call_model", side_effect=AssertionError("model call forbidden")):
            validator.validate(candidate=True)
            manifest, payloads = inputs.build()
        self.assertEqual(len(payloads), 8)
        self.assertEqual(json.loads((inputs.OUT / "manifest.json").read_text(encoding="utf-8")), manifest)
        for name, payload in payloads.items():
            self.assertEqual((inputs.OUT / name).read_bytes(), payload)
        self.assertEqual(before, [hashlib.sha256(path.read_bytes()).hexdigest() for path in paths])

    def test_every_case_requires_a_grounded_fact(self):
        self.assertEqual(len(self.anns), 8)
        self.assertEqual(self.refs["benchmark_conventions"],
            json.loads(frozen.DEV.read_text(encoding="utf-8"))["benchmark_conventions"])
        for ann in self.anns.values():
            self.assertTrue(ann["required_semantic_meanings"])
            self.assertTrue(ann["required_contract_facts"])
            self.assertTrue(ann["semantic_pass_requires_nonempty_facts"])
            EvidenceBundle.model_validate({"facts": ann["required_contract_facts"]})

    def test_fx_and_prize_unknowns_are_not_filled_from_other_streams(self):
        for case in ("holdout_user_235", "holdout_user_268", "holdout_user_274"):
            fact = self.anns[case]["required_contract_facts"][0]
            self.assertEqual(fact["payload"]["classification"], "pending_credit")
            self.assertIsNone(fact["stream_selector"])
            self.assertEqual(fact["affected_event_ids"], [])
            self.assertIsNotNone(fact["source_target"])
        charge = self.anns["holdout_user_267"]["required_contract_facts"][0]
        self.assertIsNone(charge["payload"]["money"])
        self.assertIn("charge_currency", charge["unresolved_fields"])
        self.assertIn("settlement_fx_rate", charge["unresolved_fields"])

    def test_fabricated_source_quote_is_rejected(self):
        fact = copy.deepcopy(self.anns["holdout_user_235"]["required_contract_facts"][0])
        text = "The foreign-currency refund is still processing."
        source = {"message_184": {"user_id": "user_235", "message_text": text}}
        validate_source_targets(EvidenceBundle.model_validate({"facts": [fact]}).facts, source)
        fact["source_target"]["quoted_text"] = "settled EUR refund"
        with self.assertRaises(ValueError):
            validate_source_targets(EvidenceBundle.model_validate({"facts": [fact]}).facts, source)

    def test_frozen_file_is_exact_candidate(self):
        self.assertEqual(frozen.OUT.read_bytes(),
            (json.dumps(self.refs, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        validator.validate()


if __name__ == "__main__":
    unittest.main()
