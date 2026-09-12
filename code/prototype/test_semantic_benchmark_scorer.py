"""Behavioral checks for the frozen-reference semantic scorer (development only)."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from prototype.semantic_benchmark_scorer import (REFERENCES, case_context, human_report,
                                                 load_references, score_case, score_set)


class SemanticBenchmarkScorerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference_hash = __import__("hashlib").sha256(REFERENCES["development"].read_bytes()).hexdigest()

    @classmethod
    def tearDownClass(cls):
        actual = __import__("hashlib").sha256(REFERENCES["development"].read_bytes()).hexdigest()
        if cls.reference_hash != actual:
            raise AssertionError("Frozen development reference changed during scorer tests")

    def canonical(self, case_id):
        annotation, _ = case_context("development", case_id)
        return {"facts": deepcopy(annotation["required_contract_facts"])}

    def result(self, case_id, output):
        return score_case("development", case_id, output)

    def test_all_canonical_development_bundles_pass(self):
        annotations = load_references("development")["annotations"]
        self.assertEqual(14, len(annotations))
        outputs = {a["case_id"]: self.canonical(a["case_id"]) for a in annotations}
        result = score_set("development", outputs)
        self.assertEqual(14, result["summary"]["passed_cases"])
        self.assertEqual(0, result["summary"]["failed_cases"])
        self.assertEqual(0, result["summary"]["failure_categories_by_case"].get("missing_required_meaning", 0))
        self.assertIn("14/14 cases passed", human_report(result))

    def test_valid_alternate_history_ids_and_bonus_classification(self):
        ended = self.canonical("dev_user_12")
        ended["facts"][0]["stream_selector"] = None
        annotation, context = case_context("development", "dev_user_12")
        selector = annotation["required_contract_facts"][0]["stream_selector"]
        ended["facts"][0]["affected_event_ids"] = sorted(
            event_id for event_id, event in context["events"].items()
            if all(event[key] == selector[key] for key in ("user_id", "category", "direction", "currency", "description")))
        result = self.result("dev_user_12", ended)
        self.assertTrue(result["semantic_pass"], result)
        self.assertEqual("alternate", result["required_fact_matches"][0]["representation"])

        bonus = self.canonical("dev_user_04")
        bonus["facts"][0]["fact_type"] = "cash_classification"
        bonus["facts"][0]["payload"] = {"classification": "contingent_income"}
        bonus["facts"][0]["effective_from"] = "2024-06-02"
        result = self.result("dev_user_04", bonus)
        self.assertTrue(result["semantic_pass"], result)
        self.assertEqual("alternate", result["required_fact_matches"][0]["representation"])

    def test_empty_and_unavailable_output_fail(self):
        for output, expected in (({"facts": []}, "empty_facts"), (None, "unavailable")):
            with self.subTest(expected=expected):
                result = self.result("dev_user_10", output)
                self.assertFalse(result["semantic_pass"])
                self.assertEqual(expected, result["output_availability"])
                self.assertTrue(result["missing_meanings"])

    def test_missing_required_fact(self):
        output = self.canonical("dev_user_16")
        output["facts"] = output["facts"][1:]
        result = self.result("dev_user_16", output)
        self.assertFalse(result["semantic_pass"])
        self.assertIn("u16_rent_percent", result["missing_facts"])
        self.assertEqual(1, len(result["missing_meanings"]))

    def test_correct_type_wrong_target(self):
        output = self.canonical("dev_user_20")
        output["facts"][0]["affected_event_ids"] = ["event_1784"]
        result = self.result("dev_user_20", output)
        self.assertFalse(result["semantic_pass"])
        self.assertIn("target_correct", result["failure_categories"])
        self.assertIn("wrong_target", result["required_fact_matches"][0]["errors"])

    def test_invented_unknown_amount_date_currency_and_event_id(self):
        amount = self.canonical("dev_user_03")
        amount["facts"][0]["payload"]["money"]["value"] = "999"
        result = self.result("dev_user_03", amount)
        self.assertFalse(result["semantic_pass"])
        self.assertIn("invented_unknown_amount", [e["error"] for e in result["unknown_preservation_errors"]])

        date = self.canonical("dev_user_03")
        date["facts"][0]["payload"]["payment_date"] = "2025-01-01"
        result = self.result("dev_user_03", date)
        self.assertFalse(result["semantic_pass"])
        self.assertIn("invented_unknown_payment_date", [e["error"] for e in result["unknown_preservation_errors"]])

        currency = self.canonical("dev_user_10")
        fact = currency["facts"][0]
        fact["source_target"] = None
        fact["stream_selector"] = {"user_id": "user_10", "category": "salary", "direction": "credit",
                                   "currency": "USD", "description": "QuickCrew payout"}
        result = self.result("dev_user_10", currency)
        self.assertFalse(result["semantic_pass"])
        self.assertIn("invented_stream_currency_or_target", [e["error"] for e in result["unknown_preservation_errors"]])

        event_id = self.canonical("dev_user_26")
        fact = event_id["facts"][0]
        fact["source_target"] = None
        fact["affected_event_ids"] = ["event_123456789"]
        result = self.result("dev_user_26", event_id)
        self.assertFalse(result["semantic_pass"])
        self.assertIn("invented_event_target", [e["error"] for e in result["unknown_preservation_errors"]])

    def test_wrong_lifecycle_relationship(self):
        output = self.canonical("dev_user_229")
        output["facts"][0]["payload"]["relationship"] = "refund_of"
        result = self.result("dev_user_229", output)
        self.assertFalse(result["semantic_pass"])
        self.assertIn("wrong_lifecycle_relationship", result["required_fact_matches"][0]["errors"])
        self.assertIn("false_lifecycle_relationship", [e["error"] for e in result["harmful_errors"]])

    def test_wrong_image_meaning_and_gross_total_as_due(self):
        output = self.canonical("dev_user_16")
        output["facts"][1]["payload"]["value_type"] = "net_pay"
        result = self.result("dev_user_16", output)
        self.assertFalse(result["semantic_pass"])
        self.assertIn("image_value_semantics_correct", result["failure_categories"])

        gross = self.canonical("dev_user_16")
        gross["facts"][1]["payload"]["money"]["value"] = "200000"
        gross["facts"][1]["payload"]["selected_field"] = "Total"
        result = self.result("dev_user_16", gross)
        self.assertFalse(result["semantic_pass"])
        self.assertIn("gross_total_as_current_due", [e["error"] for e in result["harmful_errors"]])

    def test_harmless_supported_extra_and_unsupported_extra(self):
        output = self.canonical("dev_user_20")
        extra = deepcopy(output["facts"][0])
        extra.update(fact_id="optional_refund_link", evidence_ids=["event_1785"],
                     fact_type="lifecycle_relationship", confirmation_state="confirmed",
                     unresolved_fields=[], payload={"relationship": "refund_of", "related_event_id": "event_1784"})
        output["facts"].append(extra)
        result = self.result("dev_user_20", output)
        self.assertTrue(result["semantic_pass"], result)
        self.assertEqual("structured_refund_link", result["extra_facts"][0]["reason"])

        unsupported = deepcopy(output)
        unsupported["facts"][1]["fact_type"] = "stream_status"
        unsupported["facts"][1]["payload"] = {"status": "ongoing"}
        result = self.result("dev_user_20", unsupported)
        self.assertFalse(result["semantic_pass"])
        self.assertIn("unsupported_claim", result["failure_categories"])

    def test_invalid_schema_and_cli(self):
        output = self.canonical("dev_user_10")
        output["facts"][0]["payload"]["extra"] = "forbidden"
        result = self.result("dev_user_10", output)
        self.assertEqual("invalid_schema", result["schema"]["status"])
        self.assertFalse(result["semantic_pass"])
        with tempfile.TemporaryDirectory() as temp:
            input_file = Path(temp) / "input.json"
            json_file = Path(temp) / "result.json"
            report_file = Path(temp) / "report.txt"
            input_file.write_text(json.dumps(self.canonical("dev_user_10")), encoding="utf-8")
            proc = subprocess.run([sys.executable, str(Path(__file__).with_name("score_semantic_benchmark.py")),
                                   "--json-out", str(json_file), "--report-out", str(report_file),
                                   "case", "dev_user_10", str(input_file)], capture_output=True, text=True)
            self.assertEqual(0, proc.returncode, proc.stderr)
            self.assertTrue(json.loads(json_file.read_text(encoding="utf-8"))["semantic_pass"])
            self.assertIn("PASS dev_user_10", report_file.read_text(encoding="utf-8"))

            outputs_dir = Path(temp) / "outputs"
            outputs_dir.mkdir()
            for annotation in load_references("development")["annotations"]:
                case_id = annotation["case_id"]
                (outputs_dir / f"{case_id}.json").write_text(
                    json.dumps(self.canonical(case_id)), encoding="utf-8")
            batch_file = Path(temp) / "batch.json"
            proc = subprocess.run([sys.executable, str(Path(__file__).with_name("score_semantic_benchmark.py")),
                                   "--json-out", str(batch_file), "development", str(outputs_dir)],
                                  capture_output=True, text=True)
            self.assertEqual(0, proc.returncode, proc.stderr)
            self.assertEqual(14, json.loads(batch_file.read_text(encoding="utf-8"))["summary"]["passed_cases"])


if __name__ == "__main__":
    unittest.main()
