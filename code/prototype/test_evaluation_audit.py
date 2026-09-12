"""Evaluation defects, tested without any provider calls."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from . import extraction_experiment as ex


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.case = next(c for c in ex.build_cases()
                         if c['case_id'] == 'synthetic_unknown_obligation')

    def run_score(self, facts):
        return ex.score(self.case, {'usable': True, 'bundle': {'facts': facts}, 'attempts': []})

    def test_one_emission_cannot_satisfy_two_references(self):
        f = copy.deepcopy(self.case['reference']['facts'][0])
        other = copy.deepcopy(f); other['fact_id'] = 'second'
        self.case['reference']['facts'].append(other)
        self.assertEqual(self.run_score([f])['critical_facts_found'], 1)

    def test_unrelated_same_type_is_not_compared(self):
        f = copy.deepcopy(self.case['reference']['facts'][0])
        f['affected_event_ids'] = ['unrelated']; f['evidence_ids'] = ['unrelated']
        f['payload']['money'] = {'value': '999', 'currency': 'EUR'}
        result = self.run_score([f])
        self.assertEqual(result['comparisons'], [])
        self.assertNotIn('WRONG_CURRENCY', [x['category'] for x in result['failures']])

    def test_unmatched_does_not_mean_unsupported(self):
        f = copy.deepcopy(self.case['reference']['facts'][0])
        self.case['reference']['facts'] = []
        self.assertEqual(self.run_score([f])['failures'][0]['category'], 'UNADJUDICATED_EXTRA')

    def test_null_description_is_not_a_wildcard(self):
        c = next(c for c in ex.build_cases() if c['case_id'] == 'rep_user07')
        a = c['reference']['facts'][1]; b = copy.deepcopy(a)
        b['stream_selector']['description'] = 'Unrelated payroll'
        self.assertFalse(ex.targets_equivalent(a, b, c['evidence']['events']))
        b['stream_selector']['description'] = 'Payroll credit'
        self.assertTrue(ex.targets_equivalent(a, b, c['evidence']['events']))
        self.assertFalse(ex.targets_equivalent(a, b))

    def test_nullable_bound_difference_requires_evidence_review(self):
        f = copy.deepcopy(self.case['reference']['facts'][0]); f['effective_from'] = '2026-04-01'
        result = self.run_score([f])
        self.assertEqual(result['failures'][0]['category'], 'EVALUATION_AMBIGUITY')
        self.assertIn('effective_from', result['comparisons'][0]['field_differences'])

    def test_decimal_normalization_never_rounds_long_values(self):
        a = '123456789012345678901234567890.1200'
        self.assertEqual(ex.normalize_payload(a, 'value'), a[:-2])
        self.assertNotEqual(ex.normalize_payload(a, 'value'),
                            ex.normalize_payload('123456789012345678901234567891.12', 'value'))

    def test_unavailable_is_not_semantic_miss_or_consistency(self):
        result = ex.score(self.case, {'usable': False, 'bundle': None, 'attempts': []})
        self.assertFalse(result['semantic_quality_evaluable'])
        self.assertEqual(len(result['failures']), 1)
        self.assertIsNone(ex.structural_consistency([None, None, None])['structurally_equal_among_usable'])

    def test_redundant_claim_does_not_change_structural_fingerprint(self):
        a = self.case['reference']; b = copy.deepcopy(a)
        b['facts'].append(copy.deepcopy(b['facts'][0])); b['facts'][1]['fact_id'] = 'extra'
        self.assertEqual(ex.fingerprint(a), ex.fingerprint(b))
        self.assertEqual(self.run_score(b['facts'])['failures'][0]['category'], 'REDUNDANT_FACT')

    def test_rescore_never_mutates_source_or_calls_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = {'records': [{'case_id': self.case['case_id'], 'run': {
                'usable': True, 'bundle': self.case['reference'], 'attempts': []}}], 'repeats': []}
            raw = json.dumps(source).encode(); (root / 'latest.json').write_bytes(raw)
            (root / 'experiment_old.json').write_bytes(raw)
            with patch.object(ex, 'ARTIFACTS', root), patch.object(ex, 'call_model', side_effect=AssertionError):
                ex.rescore_latest()
            self.assertEqual((root / 'latest.json').read_bytes(), raw)
            self.assertEqual((root / 'experiment_old.json').read_bytes(), raw)
            self.assertEqual(len(list(root.glob('comparison_v2_*.json'))), 1)

    def test_saved_raw_outputs_validate_and_match_recorded_bundles(self):
        for path in ex.ARTIFACTS.glob('experiment_*.json'):
            artifact = json.loads(path.read_text(encoding='utf-8'))
            for record in artifact['records'] + artifact['repeats']:
                run = record['run']
                valid = []
                for attempt in run['attempts']:
                    if attempt['schema_valid']:
                        parsed = ex.EvidenceBundle.model_validate_json(attempt['raw_content'])
                        # Legacy artifacts predate the optional source_target
                        # field; preserve their original serialized shape.
                        valid.append(parsed.model_dump(mode='json', exclude_unset=True))
                self.assertEqual(bool(valid), run['usable'])
                if valid:
                    self.assertEqual(valid[-1], run['bundle'])

    def test_review_covers_every_saved_emission_once(self):
        rows = json.loads((ex.ARTIFACTS / 'audit_v2/claim_review.json').read_text(encoding='utf-8'))['claims']
        identities = [(r['source_artifact'], r['case_id'], r['run_index'], r['fact_id']) for r in rows]
        expected = []
        for path in ex.ARTIFACTS.glob('experiment_*.json'):
            a = json.loads(path.read_text(encoding='utf-8'))
            for r in a['records'] + a['repeats']:
                expected.extend((path.name, r['case_id'], r.get('repeat_index', 1), f['fact_id'])
                                for f in (r['run']['bundle'] or {}).get('facts', []))
        self.assertEqual(len(identities), len(set(identities)))
        self.assertCountEqual(identities, expected)
        self.assertTrue(all(r['rationale'] and 'pending human review' in r['reviewer_provenance'] for r in rows))

    def test_shared_module_identity_and_seven_type_schema(self):
        import evidence, finance, plans
        from . import evidence as old_evidence, finance as old_finance, plans as old_plans, run
        self.assertIs(evidence.EvidenceBundle, old_evidence.EvidenceBundle)
        self.assertIs(finance.resolve, old_finance.resolve)
        self.assertIs(plans.choose, old_plans.choose)
        self.assertIs(run.resolve, finance.resolve)
        self.assertIs(ex.EvidenceBundle, evidence.EvidenceBundle)
        schema = evidence.EvidenceBundle.model_json_schema()
        self.assertEqual(len(schema['properties']['facts']['items']['discriminator']['mapping']), 7)
        self.assertEqual(schema, json.loads((Path(evidence.__file__).parent / 'evidence.schema.json').read_text()))


if __name__ == '__main__':
    unittest.main()
