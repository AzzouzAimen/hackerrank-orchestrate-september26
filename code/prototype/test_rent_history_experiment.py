import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from . import rent_history_experiment as experiment


class RentHistoryTests(unittest.TestCase):
    def test_only_six_rows_change_and_arm_is_not_in_payload(self):
        arms = experiment.arms()
        control = arms['control']
        treatment = copy.deepcopy(arms['treatment'])
        self.assertEqual([e['event_id'] for e in treatment['evidence']['events'][-6:]], experiment.RENT_IDS)
        del treatment['evidence']['events'][-6:]
        self.assertEqual(control, treatment)
        self.assertEqual(control['case_id'], 'rep_user16')
        self.assertNotIn('reference', experiment.payload(control))

    def test_preparation_does_not_call_model_or_load_credentials(self):
        with patch.object(experiment.frozen, 'call_model') as call, patch.object(experiment.frozen, 'load_env') as env:
            plan = experiment.prepare()
        call.assert_not_called()
        env.assert_not_called()
        self.assertEqual(plan['sequence'], ['control', 'treatment'] * 3)
        self.assertFalse(plan['executed'])

    def test_empty_output_never_becomes_success_and_run_is_capped(self):
        response = {'choices': [{'message': {'content': ''}, 'finish_reason': 'stop'}], 'usage': {'completion_tokens': 2}}
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(experiment.frozen, 'load_env'), \
             patch.dict('os.environ', {'FEATHERLESS_API_KEY': 'test-secret'}), \
             patch.object(experiment.frozen, 'call_model', return_value=(response, 0.1)) as call:
            output = Path(directory) / 'run'
            report = experiment.execute(output, 'test reviewer')
            self.assertEqual(call.call_count, 12)
            self.assertEqual(report['comparison_status'], 'operationally inconclusive')
            self.assertEqual(report['control']['empty_outputs'], 6)
            first = json.loads((output / '01_control_attempt1_request.json').read_text())
            retry = json.loads((output / '01_control_attempt2_request.json').read_text())
            self.assertNotEqual(first, retry)
            self.assertIn('previous response failed validation', retry['messages'][1]['content'][0]['text'])

    def test_retry_recovery_separate_from_first_attempt_and_secrets_redacted(self):
        valid = {'choices': [{'message': {'content': '{"facts":[]}'}, 'finish_reason': 'stop'}], 'usage': {}}
        outcomes = [RuntimeError('connection test-secret'), (valid, 0.1)] + [(valid, 0.1)] * 5
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(experiment.frozen, 'load_env'), \
             patch.dict('os.environ', {'FEATHERLESS_API_KEY': 'test-secret'}), \
             patch.object(experiment.frozen, 'call_model', side_effect=outcomes) as call:
            output = Path(directory) / 'run'
            report = experiment.execute(output, 'test reviewer')
            self.assertEqual(call.call_count, 7)
            self.assertEqual(report['control']['first_attempt_usable'], 2)
            self.assertEqual(report['control']['final_usable'], 3)
            self.assertEqual(report['control']['retry_recoveries'], 1)
            self.assertEqual(report['comparison_status'], 'awaiting semantic review')
            for file in output.glob('*.json'):
                self.assertNotIn('test-secret', file.read_text())
            rows = json.loads((output / 'claim_review_template.json').read_text())
            self.assertTrue(all(row['target_outcome'] is None for row in rows))

    def test_artifacts_are_exclusive_and_approval_is_required(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'artifact.json'
            experiment.write_new(path, {'original': True})
            with self.assertRaises(FileExistsError):
                experiment.write_new(path, {})
            self.assertEqual(json.loads(path.read_text()), {'original': True})
            with self.assertRaises(ValueError):
                experiment.execute(Path(directory) / 'run', '')


if __name__ == '__main__':
    unittest.main()
