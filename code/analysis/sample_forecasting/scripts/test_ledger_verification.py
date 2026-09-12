"""Focused research regression tests. No expected sample label values."""
from datetime import timedelta
from decimal import Decimal
import unittest
from unittest.mock import patch
import investigate as sim
import verify_ledgers as audit


class VerificationTests(unittest.TestCase):
    def test_decimal_replay_and_literal_horizon(self):
        for user in audit.CASES:
            with self.subTest(user=user):
                request = next(r for r in sim.SAMPLES if r['user_id'] == user)
                result = audit.forecast(request)
                baseline, safe, earliest, path = audit.replay(request, result)
                self.assertEqual(len(path), 90)
                self.assertEqual(path[0][0], request['request_date'])
                self.assertEqual(path[-1][0], (sim.day(request['request_date']) + timedelta(days=89)).isoformat())
                self.assertEqual(baseline.quantize(Decimal('.01')), audit.money(result['min_balance']))
                self.assertEqual(safe.quantize(Decimal('.01')), audit.money(result['safe']))
                self.assertEqual(earliest, result['earliest'])

    def test_provenance_and_row_balances(self):
        for user in audit.CASES:
            request = next(r for r in sim.SAMPLES if r['user_id'] == user)
            rows = audit.ledger(request, audit.forecast(request))
            balance = audit.money(rows[0]['amount'])
            for row in rows:
                self.assertIn(row['provenance'], ('STRUCTURED_EXPLICIT','SEMANTIC_FACT','INFERRED_RECURRENCE','MODELING_POLICY'))
                self.assertTrue(row['evidence_ids'])
                if row['direction'] != 'opening':
                    balance += audit.money(row['amount']) * (1 if row['direction'] == 'credit' else -1)
                self.assertEqual(balance, audit.money(row['running_balance']))

    def test_label_fields_are_not_forecast_inputs(self):
        request = dict(sim.SAMPLES[0])
        expected = audit.forecast(request)
        for field in set(request) - set(audit.INPUT_FIELDS):
            request[field] = 'NOT A LABEL'
        self.assertEqual(expected, audit.forecast(request))

    def salary_scenario(self, historical=True):
        request = dict(user_id='synthetic', request_date='2026-04-01', requested_amount='700')
        profile = dict(home_currency='USD', current_available_balance='1000', minimum_balance_to_keep='100')
        events = [dict(event_id=f'pay_{month}',user_id='synthetic',category='salary',direction='credit',
                       status='settled',description='Payroll credit',amount='500',currency='USD',
                       event_date=f'2026-{month:02}-10',settlement_date=f'2026-{month:02}-10')
                  for month in (1,2,3)] if historical else [
                      dict(event_id='next',user_id='synthetic',category='salary',direction='credit',
                           status='scheduled',description='Next confirmed salary',amount='500',currency='USD',
                           event_date='2026-04-10',settlement_date='2026-04-10')]
        messages = [dict(user_id='synthetic',sent_at='2026-03-25',source_type='employer',
                         message_text='Confirmed salary is now expected on 2026-04-23. This replaces the payroll date.')]
        return request, profile, events, messages

    def test_one_cycle_returns_to_observed_phase_not_fifteenth(self):
        request, profile, events, messages = self.salary_scenario()
        with patch.object(sim,'PROFILES',{'synthetic':profile}), patch.object(sim,'EVENTS',events), patch.object(sim,'MESSAGES',messages):
            result = sim.simulate(request, delay_persists=False)
        self.assertEqual([r[0] for r in result['trace']], ['2026-04-23','2026-05-10','2026-06-10'])

    def test_default_persistence_behavior_preserved(self):
        request, profile, events, messages = self.salary_scenario()
        with patch.object(sim,'PROFILES',{'synthetic':profile}), patch.object(sim,'EVENTS',events), patch.object(sim,'MESSAGES',messages):
            result = sim.simulate(request)
        self.assertEqual([r[0] for r in result['trace']], ['2026-04-23','2026-05-23','2026-06-23'])

    def test_unknown_prior_phase_not_invented(self):
        request, profile, events, messages = self.salary_scenario(historical=False)
        with patch.object(sim,'PROFILES',{'synthetic':profile}), patch.object(sim,'EVENTS',events), patch.object(sim,'MESSAGES',messages):
            result = sim.simulate(request, delay_persists=False)
        self.assertEqual(len(result['trace']), 1)
        self.assertTrue(result['warnings'])


if __name__ == '__main__':
    unittest.main()
