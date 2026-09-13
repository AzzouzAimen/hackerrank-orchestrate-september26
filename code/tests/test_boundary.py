"""Boundary challenge: synthetic evidence and hand-calculated expected cash.

No sample labels. Opening USD 1000, reserve 100, April 1 through June 29.
"""
from dataclasses import asdict
from datetime import date
from itertools import permutations
import unittest
from .test_finance_and_plans import event, fact, parse, profile, request, history
from finance import resolve, project, capacity, daily_path, D


def selector(description=None):
    return dict(user_id='u',category='dining',direction='debit',currency='USD',description=description)


def build(events,facts=(),extra=None,p=None):
    index={e['event_id']:e for e in events}
    index.update(extra or {})
    return project(resolve(events,p or profile(),request(),list(facts),index),{})


def signature(s):
    return ([asdict(e) for e in s.events], [asdict(f) for f in s.flows],
            sorted(s.blockers),sorted(s.issues),sorted(s.changes))


class BoundaryTests(unittest.TestCase):
    def assertBlocked(self,s):
        self.assertTrue(s.blockers)
        with self.assertRaises(ValueError):capacity(s)

    def test_possible_duplicate_preserves_history_and_three_obligations(self):
        es=history()
        f=parse(fact('lifecycle_relationship',dict(relationship='possible_duplicate_of',related_event_id='h2'),
                     affected_event_ids=['h3'],evidence_ids=['h2','h3']))
        s=build(es,[f])
        self.assertFalse(any(e.history_excluded for e in s.events))
        self.assertEqual([(f.when,f.amount) for f in s.flows],
                         [(date(2026,m,5),D('-20')) for m in (4,5,6)])
        self.assertEqual(capacity(s)[2],D('940'))
        balances={r['date']:r['balance'] for r in daily_path(s)}
        self.assertEqual([balances[date(2026,m,5)] for m in (4,5,6)],[D('980'),D('960'),D('940')])

    def test_possible_duplicate_raw_link_does_not_erase_history(self):
        es=history();es[-1]['linked_event_id']='h2'
        f=parse(fact('lifecycle_relationship',dict(relationship='possible_duplicate_of',related_event_id='h2'),
                     affected_event_ids=['h3'],evidence_ids=['h2','h3']))
        self.assertEqual(len(build(es,[f]).flows),3)

    def transfer(self,scope=None):
        es=[event('out',amount='80',status='settled',account_id='checking'),
            event('in',amount='80',status='settled',direction='credit',account_id='savings')]
        f=parse(fact('lifecycle_relationship',dict(relationship='internal_transfer',related_event_id='out'),
                     affected_event_ids=['in'],evidence_ids=['out','in']))
        p=profile()
        if scope is not None:p['modeled_cash_account_ids']=scope
        return es,f,p

    def test_internal_transfer_unknown_scope_retained_and_blocked(self):
        es,f,p=self.transfer();s=build(es,[f],p=p)
        self.assertFalse(any(e.excluded for e in s.events))
        self.assertEqual(len(s.flows),2);self.assertBlocked(s)

    def test_internal_transfer_outside_scope_not_removed(self):
        es,f,p=self.transfer(['checking']);s=build(es,[f],p=p)
        self.assertFalse(any(e.excluded for e in s.events));self.assertBlocked(s)

    def test_internal_transfer_known_scope_balanced_same_day(self):
        es,f,p=self.transfer(['checking','savings']);s=build(es,[f],p=p)
        self.assertFalse(s.blockers);self.assertFalse(s.flows)
        self.assertEqual(capacity(s)[2],D('1000'))

    def image_fact(self,value_type='amount_paid',amount='30'):
        return parse(fact('image_financial_value',dict(value_type=value_type,money=dict(value=amount,currency='USD'),
                         image_id='image',selected_field=value_type),evidence_ids=['image']))

    def test_paid_image_not_outstanding_debit(self):
        s=build([event(amount='')],[self.image_fact()],{'image':dict(user_id='u',related_event_id='e')})
        self.assertIsNone(s.events[0].amount);self.assertFalse(s.flows);self.assertBlocked(s)

    def test_paid_history_and_due_future_are_distinct(self):
        old=build([event(date='2026-03-05',amount='',status='settled')],[self.image_fact()],
                  {'image':dict(user_id='u',related_event_id='e')})
        self.assertEqual(old.events[0].amount,D('30'));self.assertFalse(old.flows)
        due=build([event(amount='')],[self.image_fact('balance_due')],{'image':dict(user_id='u',related_event_id='e')})
        self.assertEqual([(f.when,f.amount) for f in due.flows],[(date(2026,4,5),D('-30'))])
        self.assertEqual(capacity(due)[2],D('970'))

    def test_unknown_new_obligation_confirmed_and_uncertain(self):
        for confirmation in ('confirmed','uncertain'):
            f=parse(fact('future_event_confirmation',dict(money=dict(value=None,currency='USD'),payment_date='2026-04-08',direction='debit'),
                         affected_event_ids=[],stream_selector=None,source_target=dict(evidence_id='message',quoted_text='new bill'),
                         unresolved_fields=['event_id','amount'],evidence_ids=['message'],confirmation_state=confirmation))
            s=build([], [f],{'message':dict(user_id='u',sent_at='2026-03-30',message_text='new bill')})
            with self.subTest(confirmation=confirmation):self.assertBlocked(s)

    def test_unknown_new_obligation_date(self):
        f=parse(fact('future_event_confirmation',dict(money=dict(value='30',currency='USD'),payment_date=None,direction='debit'),
                     affected_event_ids=[],stream_selector=None,source_target=dict(evidence_id='message',quoted_text='new bill'),
                     unresolved_fields=['event_id','payment_date'],evidence_ids=['message']))
        self.assertBlocked(build([], [f],{'message':dict(user_id='u',message_text='new bill')}))

    def test_precise_stream_amendment_does_not_change_neighbor(self):
        es=history()+[event('b'+str(m),f'2026-{m:02}-12',amount='40',status='settled',description='Second dining plan') for m in (1,2,3)]
        f=parse(fact(payload=dict(money=dict(value='25',currency='USD'),percent_increase=None,scope='ongoing'),
                     affected_event_ids=[],stream_selector=selector('Dinner membership'),evidence_ids=['h3']))
        s=build(es,[f]);self.assertFalse(s.blockers)
        self.assertEqual([(f.when,f.amount) for f in s.flows],
                         [(date(2026,m,d),D(a)) for m in (4,5,6) for d,a in [(5,'-25'),(12,'-40')]])
        self.assertEqual(capacity(s)[2],D('805'))
        balances={r['date']:r['balance'] for r in daily_path(s)}
        self.assertEqual([balances[date(2026,m,d)] for m in (4,5,6) for d in (5,12)],
                         [D('975'),D('935'),D('910'),D('870'),D('845'),D('805')])

    def test_broad_selector_cannot_guess_between_streams(self):
        es=history()+[event('b'+str(m),f'2026-{m:02}-12',amount='40',status='settled',description='Second dining plan') for m in (1,2,3)]
        f=parse(fact(payload=dict(money=dict(value='25',currency='USD'),percent_increase=None,scope='ongoing'),
                     affected_event_ids=[],stream_selector=selector(),evidence_ids=['h3']))
        self.assertBlocked(build(es,[f]))

    def test_broad_selector_cannot_merge_same_day_streams(self):
        es=history()+[event('b'+str(m),f'2026-{m:02}-05',amount='40',status='settled',description='Second dining plan') for m in (1,2,3)]
        f=parse(fact(payload=dict(money=dict(value='25',currency='USD'),percent_increase=None,scope='ongoing'),
                     affected_event_ids=[],stream_selector=selector(),evidence_ids=['h3']))
        self.assertBlocked(build(es,[f]))

    def test_transfer_different_dates_retains_transit_exposure(self):
        es,f,p=self.transfer(['checking','savings']);es[1]['settlement_date']='2026-04-06'
        s=build(es,[f],p=p);self.assertBlocked(s);self.assertEqual(len(s.flows),2)

    def test_uncertain_possible_duplicate_does_not_remove_history(self):
        es=history();es[-1]['linked_event_id']='h2'
        f=parse(fact('lifecycle_relationship',dict(relationship='possible_duplicate_of',related_event_id='h2'),
                     affected_event_ids=['h3'],evidence_ids=['h2','h3'],confirmation_state='uncertain'))
        s=build(es,[f]);self.assertEqual(len(s.flows),3)

    def test_image_and_amendment_conflict_order(self):
        image=self.image_fact('balance_due','30')
        amendment=parse(fact(fact_id='amend',payload=dict(money=dict(value='40',currency='USD'),percent_increase=None,scope='one_cycle')))
        states=[build([event(amount='')],fs,{'image':dict(user_id='u',related_event_id='e')}) for fs in permutations([image,amendment])]
        for s in states:self.assertBlocked(s)
        self.assertEqual(signature(states[0]),signature(states[1]))

    def test_three_independent_facts_all_six_orders(self):
        fs=[self.date_fact(),parse(fact(fact_id='amount',payload=dict(money=dict(value='30',currency='USD'),percent_increase=None,scope='one_cycle'))),
            self.date_fact('other','2026-04-11','otherdate')]
        states=[build([event(),event('other',amount='10')],order) for order in permutations(fs)]
        self.assertTrue(all(signature(s)==signature(states[0]) for s in states))
        self.assertEqual([(f.when,f.amount) for f in states[0].flows],[(date(2026,4,9),D('-30')),(date(2026,4,11),D('-10'))])
        self.assertEqual(capacity(states[0])[2],D('960'))
        self.assertEqual(next(r['balance'] for r in daily_path(states[0]) if r['date']==date(2026,4,9)),D('970'))

    def test_event_ids_do_not_union_with_broad_selector(self):
        es=[event('a'),event('b',description='Other bill')]
        f=parse(fact(payload=dict(money=dict(value='35',currency='USD'),percent_increase=None,scope='one_cycle'),
                     affected_event_ids=['a'],stream_selector=selector(),evidence_ids=['a']))
        s=build(es,[f])
        # Ambiguous event/stream scope must block, or explicit event scope must be honored.
        if not s.blockers:
            self.assertEqual(next(e.amount for e in s.events if e.id=='b'),D('20'))
            self.assertEqual(next(e.amount for e in s.events if e.id=='a'),D('35'))

    def date_fact(self,identifier='e',when='2026-04-09',id='f'):
        return parse(fact('date_or_schedule_amendment',dict(payment_date=when,cadence=None,interval_days=None,scope='one_cycle'),
                          affected_event_ids=[identifier],evidence_ids=[identifier],fact_id=id))

    def test_event_date_amendment_without_stream(self):
        s=build([event()], [self.date_fact()])
        self.assertEqual(s.events[0].settlement,date(2026,4,9))
        self.assertEqual([(f.when,f.amount) for f in s.flows],[(date(2026,4,9),D('-20'))])
        self.assertIn('f',s.events[0].facts)
        self.assertEqual(capacity(s)[2],D('980'))

    def test_unknown_event_date_amendment_blocks(self):
        self.assertBlocked(build([event()], [self.date_fact(when=None)]))

    def test_conflicting_amount_facts_fail_closed_in_every_order(self):
        fs=[parse(fact(fact_id='amount'+str(i),payload=dict(money=dict(value=v,currency='USD'),percent_increase=None,scope='one_cycle'))) for i,v in enumerate(['30','40'])]
        states=[build([event()],fs_) for fs_ in permutations(fs)]
        for s in states:self.assertBlocked(s)
        self.assertEqual(signature(states[0]),signature(states[1]))

    def test_independent_facts_order_and_manual_ledger(self):
        fs=[self.date_fact(),parse(fact(fact_id='amount',payload=dict(money=dict(value='30',currency='USD'),percent_increase=None,scope='one_cycle')))]
        states=[build([event()],fs_) for fs_ in permutations(fs)]
        self.assertEqual(signature(states[0]),signature(states[1]))
        self.assertEqual([(f.when,f.amount) for f in states[0].flows],[(date(2026,4,9),D('-30'))])
        self.assertEqual(capacity(states[0])[2],D('970'))


if __name__=='__main__':unittest.main()
