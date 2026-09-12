"""Run only the five reviewed representative cases, never evaluation requests."""
from pathlib import Path
from dataclasses import asdict
import csv,json
from evidence import EvidenceBundle
from finance import decimal,resolve,project,capacity,daily_path
from plans import choose,output,verify

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
INPUT_FIELDS=('request_id','user_id','request_date','request_type','requested_amount',
              'desired_completion_date','allows_partial_payment','request_text')
CASES={'user_07':'payroll amendment', 'user_16':'future image-derived rent obligation',
       'user_01':'authorization/settlement and charge/refund lifecycle',
       'user_21':'flexible spending permissions', 'user_25':'regular-payroll control with dated FX'}


def read(name):
    with (ROOT/'dataset'/f'{name}.csv').open(encoding='utf-8-sig') as f:return list(csv.DictReader(f))


def case(user):
    request=next(r for r in read('sample_requests') if r['user_id']==user)
    profile=next(p for p in read('financial_profiles') if p['user_id']==user)
    events=[e for e in read('financial_events') if e['user_id']==user]
    messages=[m for m in read('messages') if m['user_id']==user and m['sent_at'][:10]<=request['request_date']]
    images=[i for i in read('images') if i['user_id']==user]
    for i in images:
        if not (ROOT/'dataset/media/images'/f"{i['image_id']}.png").exists():
            raise ValueError('Missing image '+i['image_id'])
    index={e['event_id']:e for e in events}
    index.update({m['message_id']:m for m in messages})
    index.update({i['image_id']:i for i in images})
    facts=EvidenceBundle.model_validate_json((HERE/'facts'/f'{user}.json').read_text(encoding='utf-8')).facts
    rates={(r['rate_date'],r['from_currency'],r['to_currency']):decimal(r['rate']) for r in read('exchange_rates')}
    state=resolve(events,profile,{k:request[k] for k in INPUT_FIELDS},facts,index)
    project(state,rates)
    options=[o for o in read('request_payment_options') if o['request_id']==request['request_id']]
    return state,options,request


def main():
    out=HERE/'artifacts';out.mkdir(exist_ok=True)
    comparisons=[];outputs=[]
    for user,reason in CASES.items():
        state,options,label=case(user)
        safe,earliest,minimum,path=capacity(state)
        selected,audit=choose(state,options)
        result=output(state,selected,options)
        ok,verified_min=verify(state,selected,options) if selected else (None,None)
        outputs.append(result.model_dump())
        comparisons.append(dict(user=user,case=reason,predicted_safe=str(safe),labeled_safe=label['amount_safe_to_pay'],
                                safe_error=str(safe-decimal(label['amount_safe_to_pay'])),
                                normalized_absolute_error=str(abs(safe-decimal(label['amount_safe_to_pay']))/decimal(label['requested_amount'])),
                                predicted_earliest=earliest.isoformat() if earliest else '',labeled_earliest=label['earliest_date_for_full_payment'],
                                earliest_match=result.earliest_date_for_full_payment==label['earliest_date_for_full_payment'],
                                recommendation=result.recommended_payment_method,selected_plan_verified=ok,schema_valid=True))
        payload=dict(case_reason=reason,facts=[f.model_dump() for f in state.facts],resolved_events=[asdict(e) for e in state.events],
                     state_changes=state.changes,issues=state.issues,blockers=state.blockers,
                     streams=[dict(id=s.id,anchor=s.anchor.id,amount=s.amount,monthly=s.monthly,step=s.step,dom=s.dom,eom=s.eom) for s in state.streams],
                     ledger=[asdict(f) for f in state.flows],daily=path,minimum=minimum,
                     selected=asdict(selected) if selected else None,verified_minimum=verified_min,
                     candidates=[dict(candidate=asdict(c) if not isinstance(c,str) else c,valid=v,result=r) for c,v,r in audit],
                     output=result.model_dump())
        (out/f'{user}.json').write_text(json.dumps(payload,indent=2,default=str),encoding='utf-8')
    for filename,rows in [('comparison.csv',comparisons),('representative_output.csv',outputs)]:
        with (out/filename).open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    metrics=dict(cases=len(comparisons),normalized_MAE=str(sum((decimal(r['normalized_absolute_error']) for r in comparisons),decimal('0'))/decimal(len(comparisons))),
                 exact_dates=sum(r['earliest_match'] for r in comparisons),invalid_selected_plans=sum(r['selected_plan_verified'] is False for r in comparisons),
                 schema_violations=0,semantic_extraction_correctness='Reviewed session-extracted facts; no independent automated extraction evaluation',
                 runtime_model_calls=0,runtime_model_tokens=0,runtime_model_cost=0,interactive_assistant_usage='not available')
    (out/'metrics.json').write_text(json.dumps(metrics,indent=2),encoding='utf-8')
    print(json.dumps(comparisons,indent=2));print(json.dumps(metrics,indent=2))


if __name__=='__main__':main()
