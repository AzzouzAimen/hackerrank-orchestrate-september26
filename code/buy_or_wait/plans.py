"""Candidate generation and independent contract/safety verification."""
from dataclasses import dataclass, replace
from itertools import combinations, product
from datetime import timedelta
from typing import Literal
from .finance import D, ZERO, decimal, day, add_months, daily_path, capacity
from .evidence import Strict, Number, Day


@dataclass
class Candidate:
    method: str
    payments: tuple
    changes: tuple = ()  # (anchor ID, stop/reduce_to, native amount)
    option_id: str = ''


def option_schedule(option):
    n=int(option['number_of_payments'])
    if n<1: raise ValueError('Invalid payment count')
    step=int(option['payment_frequency_days'] or 0)
    if n>1 and step<=0: raise ValueError('Invalid interval')
    amount=decimal(option['payment_amount'])
    if amount<=0 or amount*D(n)!=decimal(option['total_payable_amount']):
        raise ValueError('Supplied schedule total mismatch')
    return tuple((day(option['first_payment_date'])+timedelta(days=i*step),amount) for i in range(n))


def changed_flows(state, changes):
    if len(changes)>3 or len({c[0] for c in changes})!=len(changes):
        raise ValueError('At most three distinct changed events')
    streams={s.anchor.id:s for s in state.streams}
    modifications={}
    for identifier,kind,value in changes:
        if identifier not in streams: raise ValueError('Not a recurring expense')
        s=streams[identifier];e=s.anchor;p=state.profile
        if e.direction!='debit' or e.category in p['expense_categories_to_protect'].split('|'):
            raise ValueError('Protected spending')
        if kind=='stop':
            if value!=ZERO or e.flexibility not in ('stoppable','reducible_or_stoppable') or e.category not in p['expense_categories_user_is_willing_to_stop'].split('|'):
                raise ValueError('Stop forbidden')
        elif kind=='reduce_to':
            if e.flexibility not in ('reducible','reducible_or_stoppable') or e.category not in p['expense_categories_user_is_willing_to_reduce'].split('|') or e.minimum is None or not e.minimum<=value<s.amount:
                raise ValueError('Reduction forbidden')
        else: raise ValueError('Unknown spending change')
        modifications[s.id]=value
    flows=[]
    for f in state.flows:
        # Future recurrence only. Explicit arrears and pending holds are unchanged.
        if f.stream_id in modifications and f.when>state.start:
            value=modifications[f.stream_id]
            if f.native_amount is None or f.native_amount<=0: raise ValueError('Missing native amount')
            flows.append(replace(f,amount=-value*(abs(f.amount)/f.native_amount)))
        else: flows.append(f)
    return flows


def verify(state,candidate,options):
    try:
        if state.blockers: raise ValueError('Unresolved financial facts')
        safe,earliest,_,_=capacity(state)
        requested=decimal(state.request['requested_amount'])
        methods=state.profile['payment_methods_user_will_consider'].split('|')
        payments=candidate.payments
        if not payments or list(payments)!=sorted(payments) or any(a<=0 for _,a in payments):
            raise ValueError('Invalid chronological payments')
        if any(d<state.start or d>state.end or d>day(state.request['desired_completion_date']) for d,_ in payments):
            raise ValueError('Deadline/horizon violation')
        if candidate.method=='wait':
            if 'full_payment' not in methods or earliest is None or earliest<=state.start or payments!=((earliest,requested),) or candidate.changes:
                raise ValueError('Invalid wait')
        elif candidate.method not in methods: raise ValueError('Method not accepted')
        if candidate.method=='partial_payment':
            if state.request['allows_partial_payment']!='true' or not ZERO<safe<requested or earliest is None or payments!=((state.start,safe),(earliest,requested-safe)):
                raise ValueError('Partial must be exact two-payment rule')
        elif candidate.method=='installments':
            option=next(o for o in options if o['payment_option_id']==candidate.option_id)
            if option['request_id']!=state.request['request_id'] or option['payment_method']!='installments' or payments!=option_schedule(option):
                raise ValueError('Option schedule differs')
            if decimal(option['total_payable_amount'])!=requested+decimal(option['financing_fee']):
                raise ValueError('Fee mismatch')
            maximum=state.profile['max_installment_months']
            if not maximum or payments[-1][0]>add_months(payments[0][0],int(maximum)):
                raise ValueError('Installment duration exceeds preference')
        elif candidate.method in ('full_payment','wait'):
            if len(payments)!=1 or payments[0][1]!=requested: raise ValueError('Full amount required')
        elif candidate.method!='partial_payment': raise ValueError('Unknown method')
        path=daily_path(state,changed_flows(state,candidate.changes),payments)
        minimum=min(r['minimum'] for r in path)
        if minimum<decimal(state.profile['minimum_balance_to_keep']): raise ValueError('Reserve breach')
        return True,minimum
    except (ValueError,KeyError,StopIteration) as error:
        return False,str(error)


def spending_sets(state):
    choices=[]
    for s in state.streams:
        e=s.anchor;local=[]
        for kind,value in [('stop',ZERO),('reduce_to',e.minimum)]:
            if value is None:continue
            action=(e.id,kind,value)
            try: changed_flows(state,(action,));local.append(action)
            except ValueError: pass
        if local:choices.append(local)
    yield ()
    for n in range(1,min(3,len(choices))+1):
        for subset in combinations(choices,n):
            yield from product(*subset)


def rank(candidate):
    return (bool(candidate.changes),sum((a for _,a in candidate.payments),ZERO),
            candidate.payments[0][0],len(candidate.payments),candidate.option_id,
            str(candidate.changes),candidate.method)


def choose(state,options):
    safe,earliest,_,_=capacity(state)
    amount=decimal(state.request['requested_amount'])
    audited=[];valid=[]
    for changes in spending_sets(state):
        # Earliest verified full payment under each allowed change set.
        for i in range(90):
            c=Candidate('full_payment',((state.start+timedelta(days=i),amount),),changes)
            ok,reason=verify(state,c,options)
            if ok:
                valid.append(c);audited.append((c,ok,reason));break
        candidates=[]
        if earliest and ZERO<safe<amount:
            candidates.append(Candidate('partial_payment',((state.start,safe),(earliest,amount-safe)),changes))
        for o in options:
            if o['payment_method']=='installments':
                try:candidates.append(Candidate('installments',option_schedule(o),changes,o['payment_option_id']))
                except ValueError as error: audited.append((o['payment_option_id'],False,str(error)))
        if not changes and earliest and earliest>state.start:
            candidates.append(Candidate('wait',((earliest,amount),)))
        for c in candidates:
            ok,reason=verify(state,c,options);audited.append((c,ok,reason))
            if ok:valid.append(c)
    if not valid:return None,audited
    selected=min(valid,key=rank)
    if selected.method=='full_payment' and not selected.changes and selected.payments[0][0]>state.start:
        selected=replace(selected,method='wait')
    return selected,audited


class Output(Strict):
    request_id: str
    amount_safe_to_pay: Number
    affordability_status: Literal['affordable_now','affordable_with_plan','affordable_later','not_affordable']
    recommended_payment_method: Literal['full_payment','partial_payment','installments','wait','not_recommended']
    payment_plan: str
    earliest_date_for_full_payment: Day | Literal['']
    spending_changes_needed: str
    decision_explanation: str


def output(state,selected,options):
    safe,earliest,_,_=capacity(state)
    method=selected.method if selected else 'not_recommended'
    status=('affordable_now' if method=='full_payment' and not selected.changes and selected.payments[0][0]==state.start
            else 'affordable_later' if method=='wait' else 'affordable_with_plan' if selected
            else 'affordable_later' if earliest and earliest>state.start else 'not_affordable')
    result=Output(request_id=state.request['request_id'],amount_safe_to_pay=str(safe),affordability_status=status,
                  recommended_payment_method=method,
                  payment_plan='|'.join(f'{d}:{a}' for d,a in selected.payments) if selected else 'none',
                  earliest_date_for_full_payment=earliest.isoformat() if earliest else '',
                  spending_changes_needed='|'.join(f'{kind}:{identifier}'+(f':{value}' if kind=='reduce_to' else '') for identifier,kind,value in selected.changes) if selected and selected.changes else 'none',
                  decision_explanation=('Verified supplied schedule and 90-day reserve.' if method=='installments' else 'Verified payments against the 90-day ledger and reserve.' if selected else 'No eligible plan passes the deadline and reserve checks.'))
    validate_output(result,state,selected,options)
    return result


def validate_output(result,state,selected,options):
    result=Output.model_validate(result.model_dump())
    safe,earliest,_,_=capacity(state)
    if decimal(result.amount_safe_to_pay)!=safe or result.earliest_date_for_full_payment!=(earliest.isoformat() if earliest else ''):
        raise ValueError('Output capacity mismatch')
    if selected:
        ok,reason=verify(state,selected,options)
        if not ok:raise ValueError(reason)
        if result.payment_plan!='|'.join(f'{d}:{a}' for d,a in selected.payments) or result.recommended_payment_method!=selected.method:
            raise ValueError('Output plan mismatch')
    elif result.payment_plan!='none' or result.recommended_payment_method!='not_recommended':
        raise ValueError('Invalid fallback')
    changes='|'.join(f'{kind}:{identifier}'+(f':{value}' if kind=='reduce_to' else '') for identifier,kind,value in selected.changes) if selected and selected.changes else 'none'
    if result.spending_changes_needed!=changes:raise ValueError('Output spending changes mismatch')
    expected=('affordable_now' if selected and selected.method=='full_payment' and not selected.changes and selected.payments[0][0]==state.start
              else 'affordable_later' if selected and selected.method=='wait'
              else 'affordable_with_plan' if selected else 'affordable_later' if earliest and earliest>state.start else 'not_affordable')
    if result.affordability_status!=expected:raise ValueError('Output affordability status mismatch')
    if not result.decision_explanation.strip():raise ValueError('Missing explanation')
    return True
