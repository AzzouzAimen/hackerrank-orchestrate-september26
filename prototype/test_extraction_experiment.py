import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from buy_or_wait.evidence import EvidenceBundle
from .extraction_experiment import build_cases, core, fingerprint, load_env, score


class ExtractionExperimentTests(unittest.TestCase):
    def test_all_references_are_schema_valid_and_ids_unique(self):
        cases = build_cases()
        self.assertEqual(len(cases), 10)
        self.assertEqual(len({case["case_id"] for case in cases}), len(cases))
        for case in cases:
            with self.subTest(case=case["case_id"]):
                EvidenceBundle.model_validate(case["reference"])

    def test_scoring_ignores_fact_id_and_order(self):
        case = build_cases()[0]
        bundle = json.loads(json.dumps(case["reference"]))
        bundle["facts"].reverse()
        for index, item in enumerate(bundle["facts"]):
            item["fact_id"] = f"model.{index}"
        result = score(case, {"usable": True, "bundle": bundle, "attempts": [{"schema_valid": True}]})
        self.assertEqual(result["critical_facts_found"], result["reference_fact_count"])
        self.assertFalse(result["failures"])

    def test_unknown_to_value_is_classified(self):
        case = next(c for c in build_cases() if c["case_id"] == "synthetic_unknown_obligation")
        bundle = json.loads(json.dumps(case["reference"]))
        bundle["facts"][0]["payload"]["money"]["value"] = "50"
        result = score(case, {"usable": True, "bundle": bundle, "attempts": [{"schema_valid": True}]})
        self.assertIn("UNCERTAINTY_TO_CERTAINTY", [f["category"] for f in result["failures"]])

    def test_empty_success_is_schema_invalid_not_provider_failure(self):
        case = next(c for c in build_cases() if c["case_id"] == "synthetic_unknown_obligation")
        run = {"usable": False, "bundle": None, "attempts": [{"raw_content": "", "schema_valid": False}]}
        result = score(case, run)
        self.assertIn("SCHEMA_INVALID", [f["category"] for f in result["failures"]])
        self.assertNotIn("PROVIDER_API_FAILURE", [f["category"] for f in result["failures"]])

    def test_target_difference_and_fingerprint_are_semantic(self):
        case = next(c for c in build_cases() if c["case_id"] == "synthetic_possible_duplicate")
        bundle = json.loads(json.dumps(case["reference"]))
        original = fingerprint(bundle)
        bundle["facts"][0]["fact_id"] = "different"
        self.assertEqual(original, fingerprint(bundle))
        bundle["facts"][0]["affected_event_ids"] = ["syn_charge_a"]
        self.assertNotEqual(original, fingerprint(bundle))

    def test_core_excludes_serialization_identity(self):
        case = build_cases()[0]
        item = case["reference"]["facts"][0]
        changed = json.loads(json.dumps(item)); changed["fact_id"] = "another"
        self.assertEqual(core(item), core(changed))

    def test_decimal_serialization_is_semantically_equal(self):
        case = next(c for c in build_cases() if c["case_id"] == "unused_real_image03")
        bundle = json.loads(json.dumps(case["reference"]))
        bundle["facts"][0]["payload"]["money"]["value"] = "41272.00"
        result = score(case, {"usable": True, "bundle": bundle, "attempts": [{"schema_valid": True}]})
        self.assertEqual(result["critical_facts_found"], 1)
        self.assertFalse(result["failures"])


if __name__ == "__main__":
    unittest.main()
