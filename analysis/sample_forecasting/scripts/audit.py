"""Evidence and label validation for the investigation, not prediction generation."""
import investigate as a
from collections import Counter, defaultdict
from decimal import Decimal as D
import json
import re

def main():
    users={r['user_id'] for r in a.SAMPLES}
    es=[e for e in a.EVENTS if e['user_id'] in users]
    index={e['event_id']:e for e in a.EVENTS}
    facts={
        'sample_events':len(es),
        'sample_messages':sum(m['user_id'] in users for m in a.MESSAGES),
        'sample_statuses':dict(Counter(e['status'] for e in es)),
        'all_statuses':dict(Counter(e['status'] for e in a.EVENTS)),
        'sample_expense_cadences':dict(Counter(str(s['cadence']) for r in a.SAMPLES for s in a.simulate(r)['streams'] if s['category']!='salary')),
        'sample_link_pairs':dict(Counter(index[e['linked_event_id']]['status']+' -> '+e['status']+' / '+e['event_type'] for e in es if e['linked_event_id'])),
        'all_link_pairs':dict(Counter(index[e['linked_event_id']]['status']+' -> '+e['status']+' / '+e['event_type'] for e in a.EVENTS if e['linked_event_id'])),
        'settled_on_request_day':sum(e['user_id']==r['user_id'] and e['status']=='settled' and e['settlement_date']==r['request_date'] for r in a.SAMPLES for e in es),
        'fx_distinct_rates_by_pair':{str(pair):sorted({rate for (dt,f,t),rate in a.RATES.items() if (f,t)==pair}) for pair in {(f,t) for dt,f,t in a.RATES}},
    }
    (a.OUT/'evidence_counts.json').write_text(json.dumps(facts,indent=2),encoding='utf-8')
    options=a.read('request_payment_options');elig=[];checks=[];change_rows=[]
    for r in a.SAMPLES:
        p=a.PROFILES[r['user_id']];methods=p['payment_methods_user_will_consider'].split('|')
        for o in options:
            if o['request_id']!=r['request_id']:continue
            n=int(o['number_of_payments']);freq=int(o['payment_frequency_days'] or 0)
            last=a.day(o['first_payment_date'])+a.timedelta(days=(n-1)*freq)
            cap=int(p['max_installment_months'] or 0)
            elig.append(dict(request_id=r['request_id'],option_id=o['payment_option_id'],method=o['payment_method'],n=n,interval_days=freq,last_date=last.isoformat(),max_installment_months=cap,method_allowed=o['payment_method'] in methods,count_cap_ok=n<=cap if n>1 else True,deadline_ok=last<=a.day(r['desired_completion_date']),schedule_total_exact=D(o['payment_amount'])*n==D(o['total_payable_amount']),fee_exact=D(o['total_payable_amount'])-D(r['requested_amount'])==D(o['financing_fee'])))
        changes={};valid_changes=True
        if r['spending_changes_needed']!='none':
            for act in r['spending_changes_needed'].split('|'):
                bits=act.split(':');e=index[bits[1]];cat=e['category'];stop=bits[0]=='stop'
                allowed=cat in p['expense_categories_user_is_willing_to_'+('stop' if stop else 'reduce')].split('|') and cat not in p['expense_categories_to_protect'].split('|')
                allowed &= e['flexibility'] in (('stoppable','reducible_or_stoppable') if stop else ('reducible','reducible_or_stoppable'))
                if not stop:allowed &= D(bits[2])>=D(e['minimum_allowed_amount'])
                valid_changes &= allowed
                changes[cat]=0 if stop else float(bits[2])
                change_rows.append(dict(request_id=r['request_id'],action=act,category=cat,anchor_amount=e['amount'],minimum_allowed=e['minimum_allowed_amount'],allowed=allowed,anchor_is_latest=bits[1]==max((x for x in es if x['user_id']==r['user_id'] and x['category']==cat and x['status']=='settled'),key=lambda x:x['event_date'])['event_id']))
        pred=a.simulate(r,changes=changes)
        payments=[] if r['payment_plan']=='none' else [(a.day(x.split(':')[0]),D(x.split(':')[1])) for x in r['payment_plan'].split('|')]
        cumulative=D(0);minimum=D(str(p['current_available_balance']))
        for i,b in enumerate(pred['path']):
            d=a.day(r['request_date'])+a.timedelta(days=i)
            cumulative+=sum((v for dt,v in payments if dt==d),D(0))
            minimum=min(minimum,D(str(b))-cumulative)
        exact_option=True
        if r['recommended_payment_method']=='installments':
            exact_option=any(payments==[(a.day(o['first_payment_date'])+a.timedelta(days=i*int(o['payment_frequency_days'])),D(o['payment_amount'])) for i in range(int(o['number_of_payments']))] for o in options if o['request_id']==r['request_id'] and o['payment_method']=='installments')
        checks.append(dict(request_id=r['request_id'],method=r['recommended_payment_method'],spending_changes_valid=valid_changes,installments_match_option=exact_option,plan_min_balance_under_baseline=round(minimum,2),floor=p['minimum_balance_to_keep'],plan_safe_under_baseline=minimum>=D(p['minimum_balance_to_keep']),has_plan=bool(payments)))
    a.write_csv('option_eligibility.csv',elig);a.write_csv('label_plan_audit.csv',checks);a.write_csv('spending_change_evidence.csv',change_rows)
    def research_csv(name):
        with (a.OUT/name).open(encoding='utf-8') as f:return list(a.csv.DictReader(f))
    amounts=['| Estimator | Exact safe amounts | Exact dates | Normalized MAE |','|---|---:|---:|---:|']
    for x in research_csv('candidate_scores.csv'):
        amounts.append(f"| {x['candidate']} | {x['safe_exact']}/25 | {x['date_exact']}/25 | {float(x['normalized_MAE'])*100:.3f}% |")
    samples=['| Sample | Currency | Baseline minimum | Predicted safe | Labeled safe | Predicted full date | Labeled full date |','|---|---|---:|---:|---:|---|---|']
    for x in research_csv('baseline_90day.csv'):
        samples.append(f"| {x['request_id'].split('_')[-1]} | {x['currency']} | {float(x['min_balance']):,.2f} | {float(x['predicted_safe']):,.2f} | {float(x['true_safe']):,.2f} | {x['predicted_earliest'] or '—'} | {x['true_earliest'] or '—'} |")
    report=a.OUT.parent/'reports'/'REPORT.md'
    if report.exists():
        body=report.read_text(encoding='utf-8')
        for tag,lines in [('AMOUNT_TABLE',amounts),('SAMPLE_TABLE',samples)]:
            block=f'<!-- {tag} -->\n'+'\n'.join(lines)+f'\n<!-- END_{tag} -->'
            body=re.sub(f'<!-- {tag} -->(?:.*?<!-- END_{tag} -->)?',lambda m:block,body,flags=re.S)
        report.write_text(body,encoding='utf-8')
    print(json.dumps(facts,indent=2));print('Unsafe labeled plans under candidate',[(x['request_id'],str(x['plan_min_balance_under_baseline'])) for x in checks if x['has_plan'] and not x['plan_safe_under_baseline']])

if __name__=='__main__':main()
