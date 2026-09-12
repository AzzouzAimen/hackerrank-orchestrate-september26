import copy
import unittest
from datetime import date,timedelta
from dataclasses import replace
from pydantic import ValidationError
from ..evidence import EvidenceBundle
from ..finance import (D,ZERO,State,Flow,resolve,project,infer_streams,capacity,decimal,
                      add_months,daily_path)
from ..plans import Candidate,option_schedule,verify,choose,output,validate_output,changed_flows,rank
from prototype.run import case,CASES


def profile():
    return dict(user_id='u',home_currency='USD',current_available_balance='1000',minimum_balance_to_keep='100',
                expense_categories_to_protect='rent',expense_categories_user_is_willing_to_reduce='dining',
                expense_categories_user_is_willing_to_stop='dining',payment_methods_user_will_consider='full_payment|partial_payment|installments',
                max_installment_months='3')


def request():
    return dict(request_id='r',user_id='u',request_date='2026-04-01',requested_amount='400',
                desired_completion_date='2026-06-29',allows_partial_payment='true')


def event(id='e',date='2026-04-05',amount='20',status='scheduled',**kw):
    result=dict(event_id=id,user_id='u',event_type='expense',description='Dinner membership',category='dining',direction='debit',
                amount=amount,currency='USD',event_date=date,settlement_date=date,status=status,linked_event_id='',
                flexibility='reducible_or_stoppable',minimum_allowed_amount='10')
    result.update(kw);return result


def fact(typ='amount_amendment',payload=None,**kw):
    result=dict(schema_version='1.0',fact_id='f',fact_type=typ,evidence_ids=['e'],affected_event_ids=['e'],stream_selector=None,
                effective_from=None,effective_until=None,confirmation_state='confirmed',unresolved_fields=['payload.money.value'],
                payload=payload or dict(money=dict(value=None,currency='USD'),percent_increase=None,scope='unknown'))
    result.update(kw);return result


def parse(f):return EvidenceBundle.model_validate(dict(facts=[f])).facts[0]


def state(events=(),facts=(),p=None,r=None):
    return resolve(list(events),p or profile(),r or request(),list(facts),{e['event_id']:e for e in events})


def history():return [event('h'+str(m),f'2026-{m:02}-05',status='settled') for m in (1,2,3)]


class EvidenceTests(unittest.TestCase):
    def test_missing_amount_stays_null(self):
        self.assertIsNone(parse(fact()).payload.money.value)

    def test_reject_shapes_types_dates_and_extra_fields(self):
        invalid=[]
        for value in (0,2.3,'NaN','-1',{},True):
            f=fact();f['payload']['money']['value']=value;invalid.append(f)
        f=fact();f['payload']['money']['currency']='dollars';invalid.append(f)
        for patch in [dict(fact_type='affordability'),dict(evidence_ids=[]),dict(affected_event_ids=[]),
                      dict(effective_from='2026-02-30'),dict(effective_from='20260401'),dict(safe_amount='2'),dict(should_ignore=True)]:
            invalid.append(fact(**patch))
        f=fact();f['payload']['execute']='delete records';invalid.append(f)
        for f in invalid:
            with self.subTest(f=f),self.assertRaises(ValidationError):parse(f)

    def test_evidence_cross_user_rejected(self):
        e=event();f=parse(fact());e['user_id']='other'
        with self.assertRaises(ValueError):state([e],[f])


class LedgerTests(unittest.TestCase):
    def test_decimal_and_float_rejection(self):
        self.assertEqual(decimal('0.1')+decimal('0.2'),D('.3'))
        with self.assertRaises(ValueError):decimal(.1)

    def test_horizon_inclusive(self):
        s=project(state([event(date='2026-06-29'),event('outside','2026-06-30')]),{})
        self.assertEqual(len(daily_path(s)),90)
        self.assertEqual([f.source for f in s.flows],['e'])

    def test_monthly_end_of_month(self):
        self.assertEqual(add_months(date(2024,1,31),eom=True),date(2024,2,29))
        es=[event(str(m),d,status='settled') for m,d in enumerate(['2026-01-31','2026-02-28','2026-03-31'])]
        s=project(state(es),{})
        self.assertEqual([f.when for f in s.flows],[date(2026,4,30),date(2026,5,31)])

    def test_recurrence_and_explicit_overlap(self):
        s=project(state(history()+[event('explicit','2026-04-05')]),{})
        april=[f for f in s.flows if f.when==date(2026,4,5)]
        self.assertEqual(len(april),1);self.assertEqual(april[0].source,'explicit')
        self.assertEqual(len(s.flows),3)

    def test_category_alone_never_deduplicates(self):
        s=project(state(history()+[event('extra','2026-04-05',description='Outstanding restaurant debt')]),{})
        self.assertEqual(len([f for f in s.flows if f.when==date(2026,4,5)]),2)
        self.assertTrue(s.issues)

    def test_pending_hold_once_and_no_pending_credit(self):
        s=project(state([event(status='pending'),event('credit',status='pending',direction='credit')]),{})
        self.assertEqual(len(s.flows),1);self.assertEqual(s.flows[0].when,s.start)
        self.assertEqual(s.flows[0].amount,D('-20'))

    def test_failed_cancelled_and_valuation_excluded(self):
        s=project(state([event('a',status='failed'),event('b',status='cancelled'),event('c',status='unrealized',direction='non_cash')]),{})
        self.assertFalse(s.flows)

    def test_missing_future_amount_blocks_output(self):
        s=project(state([event(amount='')]),{})
        self.assertIsNone(s.events[0].amount)
        with self.assertRaises(ValueError):capacity(s)

    def test_unknown_amendment_amount_blocks(self):
        es=history();f=parse(fact(affected_event_ids=['h3'],evidence_ids=['h3'],stream_selector=dict(user_id='u',category='dining',direction='debit',currency='USD',description=None)))
        s=project(state(es,[f]),{})
        with self.assertRaises(ValueError):capacity(s)

    def test_lifecycle_settlement_replaces_hold_not_refund(self):
        es=[event('old',status='pending'),event('new',status='settled',linked_event_id='old')]
        f=parse(fact('lifecycle_relationship',dict(relationship='settlement_of',related_event_id='old'),affected_event_ids=['new'],evidence_ids=['old','new']))
        s=project(state(es,[f]),{})
        self.assertEqual([f.source for f in s.flows],['new'])
        es=[event('old',status='settled'),event('new',status='settled',direction='credit',event_type='refund',linked_event_id='old')]
        f=parse(fact('lifecycle_relationship',dict(relationship='refund_of',related_event_id='old'),affected_event_ids=['new'],evidence_ids=['old','new']))
        self.assertEqual(len(project(state(es,[f]),{}).flows),2)

    def test_possible_duplicate_retained(self):
        es=[event('old'),event('new')]
        f=parse(fact('lifecycle_relationship',dict(relationship='possible_duplicate_of',related_event_id='old'),affected_event_ids=['new'],evidence_ids=['old','new']))
        self.assertEqual(len(project(state(es,[f]),{}).flows),2)

    def test_fx_uses_settlement_direction(self):
        e=event(currency='EUR',event_date='2026-04-02')
        s=project(state([e]),{('2026-04-05','EUR','USD'):D('2'),('2026-04-02','EUR','USD'):D('9')})
        self.assertEqual(s.flows[0].amount,D('-40'))

    def test_intraday_trough_and_prefix_invariant(self):
        s=state();s.profile['current_available_balance']='110'
        s.flows=[Flow(s.start,D('-20'),'debit','STRUCTURED_EXPLICIT',[],[]),Flow(s.start,D('1000'),'credit','STRUCTURED_EXPLICIT',[],[])]
        safe,earliest,minimum,_=capacity(s)
        self.assertEqual(minimum,D('90'));self.assertEqual(safe,ZERO);self.assertIsNone(earliest)

    def test_fixed_day_materialization(self):
        es=[event(str(i),(date(2026,3,1)+timedelta(days=i*7)).isoformat(),status='settled') for i in range(5)]
        s=project(state(es),{})
        self.assertEqual(s.flows[0].when,date(2026,4,5))
        self.assertTrue(all((b.when-a.when).days==7 for a,b in zip(s.flows,s.flows[1:])))

    def test_explicit_amendment_and_future_confirmation(self):
        e=event(amount='')
        f=parse(fact(payload=dict(money=dict(value='35',currency='USD'),percent_increase=None,scope='one_cycle')))
        self.assertEqual(project(state([e],[f]),{}).flows[0].amount,D('-35'))
        f=parse(fact('future_event_confirmation',dict(money=dict(value='40',currency='USD'),payment_date='2026-04-08',direction='debit')))
        s=project(state([e],[f]),{})
        self.assertEqual([(x.when,x.amount) for x in s.flows],[(date(2026,4,8),D('-40'))])


class PlanTests(unittest.TestCase):
    def option(self):
        return dict(payment_option_id='o',request_id='r',payment_method='installments',payment_amount='210',number_of_payments='2',
                    first_payment_date='2026-04-03',payment_frequency_days='31',financing_fee='20',total_payable_amount='420')

    def test_exact_option_schedule_and_fees(self):
        o=self.option();s=state();schedule=option_schedule(o)
        self.assertEqual(schedule,((date(2026,4,3),D('210')),(date(2026,5,4),D('210'))))
        c=Candidate('installments',schedule,option_id='o')
        self.assertTrue(verify(s,c,[o])[0])
        self.assertFalse(verify(s,replace(c,payments=((date(2026,4,3),D('200')),schedule[1])),[o])[0])
        s.profile['max_installment_months']='1'
        self.assertFalse(verify(s,c,[o])[0])

    def test_partial_exact_structure(self):
        s=state();s.profile['current_available_balance']='300'
        s.flows=[Flow(date(2026,4,10),D('500'),'pay','STRUCTURED_EXPLICIT',[],[])]
        safe,earliest,_,_=capacity(s)
        c=Candidate('partial_payment',((s.start,safe),(earliest,D('400')-safe)))
        self.assertTrue(verify(s,c,[])[0])
        self.assertFalse(verify(s,replace(c,payments=((s.start,D('100')),(earliest,D('300')))),[])[0])

    def test_reserve_deadline_and_method(self):
        s=state();c=Candidate('full_payment',((s.start,D('400')),))
        self.assertTrue(verify(s,c,[])[0])
        s.profile['current_available_balance']='450';self.assertFalse(verify(s,c,[])[0])
        s.profile['current_available_balance']='1000'
        self.assertFalse(verify(s,replace(c,payments=((date(2026,7,1),D('400')),)),[])[0])
        s.profile['payment_methods_user_will_consider']='installments';self.assertFalse(verify(s,c,[])[0])

    def test_spending_permissions_future_only_and_mutual_exclusion(self):
        s=project(state(history()),{});identifier=s.streams[0].anchor.id
        changed=changed_flows(s,((identifier,'reduce_to',D('10')),))
        self.assertTrue(all(f.amount==D('-10') for f in changed))
        with self.assertRaises(ValueError):changed_flows(s,((identifier,'stop',ZERO),(identifier,'reduce_to',D('10'))))
        with self.assertRaises(ValueError):changed_flows(s,((identifier,'reduce_to',D('9')),))
        s.profile['expense_categories_to_protect']='dining'
        with self.assertRaises(ValueError):changed_flows(s,((identifier,'stop',ZERO),))

    def test_ranking_and_output_validation(self):
        s=state();selected,_=choose(s,[]);r=output(s,selected,[])
        self.assertEqual(selected.method,'full_payment')
        self.assertTrue(validate_output(r,s,selected,[]))
        bad=r.model_copy(update={'amount_safe_to_pay':'999'})
        with self.assertRaises(ValueError):validate_output(bad,s,selected,[])
        for key,value in [('spending_changes_needed','stop:fake'),('affordability_status','not_affordable'),('decision_explanation','')]:
            with self.assertRaises(ValueError):validate_output(r.model_copy(update={key:value}),s,selected,[])
        a=Candidate('installments',((s.start,D('400')),),option_id='a')
        b=replace(a,option_id='b')
        self.assertLess(rank(a),rank(b))

    def test_change_candidate_can_enable_full_payment(self):
        s=project(state(history()),{});s.profile['current_available_balance']='550'
        selected,_=choose(s,[])
        self.assertIsNotNone(selected);self.assertTrue(selected.changes)
        self.assertTrue(verify(s,selected,[])[0])

    def test_max_three_and_request_day_changes(self):
        s=project(state(history()),{});identifier=s.streams[0].anchor.id
        with self.assertRaises(ValueError):changed_flows(s,tuple((str(i),'stop',ZERO) for i in range(4)))
        s.flows[0]=replace(s.flows[0],when=s.start)
        self.assertEqual(changed_flows(s,((identifier,'stop',ZERO),))[0].amount,s.flows[0].amount)


class RepresentativeTests(unittest.TestCase):
    def test_five_cases_finish_and_selected_plans_verify(self):
        for user in CASES:
            with self.subTest(user=user):
                s,options,_=case(user);self.assertFalse(s.blockers)
                selected,_=choose(s,options)
                output(s,selected,options)
                if selected:self.assertTrue(verify(s,selected,options)[0])

    def test_image_resolves_actual_future_debit(self):
        s,_,_=case('user_16')
        f=next(f for f in s.flows if f.source=='event_1442')
        self.assertEqual(f.amount,D('-100000'));self.assertIn('image_02',f.evidence)
        self.assertEqual(f.when,date(2023,8,16))

    def test_payday_fact_versus_persistence_policy(self):
        s,_,_=case('user_07')
        credits=[f for f in s.flows if f.amount>0]
        self.assertEqual(credits[0].provenance,'SEMANTIC_FACT')
        self.assertEqual(credits[1].provenance,'MODELING_POLICY')
        self.assertEqual(credits[1].when,date(2024,10,23))


if __name__=='__main__':unittest.main()
