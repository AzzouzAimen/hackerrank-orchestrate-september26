"""Exploratory sample-only simulator; not a submission pipeline.

Run: python analysis/sample_forecasting/scripts/investigate.py
Only participant data is read. Labels are used exclusively by score/report code.
"""
from pathlib import Path
from datetime import date, timedelta
from collections import defaultdict, Counter
from statistics import mean, median
import csv, calendar, re, json

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parents[1] / 'artifacts'
def read(name):
    with (ROOT/'dataset'/f'{name}.csv').open(encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))
SAMPLES = read('sample_requests')
PROFILES = {x['user_id']: x for x in read('financial_profiles')}
EVENTS = read('financial_events')
MESSAGES = read('messages')
RATES = {(x['rate_date'], x['from_currency'], x['to_currency']):float(x['rate']) for x in read('exchange_rates')}
IMAGES = {x['related_event_id']:x['image_id'] for x in read('images')}
# Manual transcription of visible financial fields, not sample labels or PII.
IMAGE_FACTS = {
    'image_01': {'amount':4365000, 'field':'Net Pay'},
    'image_02': {'amount':100000, 'field':'Balance Due'},
    'image_03': {'amount':41272, 'field':'Cash Paid'},
    'image_04': {'amount':2854, 'field':'Item Bill; bottom cropped, final total uncertain'},
    'image_05': {'amount':822.05, 'field':'Amount due after 06-Feb-2026', 'before_due':704.05},
}
def day(s): return date.fromisoformat(s)
def month_next(d, dom=None):
    y,m = (d.year+1,1) if d.month==12 else (d.year,d.month+1)
    return date(y,m,min(dom or d.day,calendar.monthrange(y,m)[1]))
def amount(e, home, when=None):
    a=float(e['amount']) if e['amount'] else IMAGE_FACTS[IMAGES[e['event_id']]]['amount']
    if e['currency']!=home:
        a*=RATES[((when or day(e['settlement_date'])).isoformat(),e['currency'],home)]
    return a
def forecast_amount(g, rule, home):
    a=[amount(e,home) for e in g]
    if rule=='mean': return mean(a)
    if rule=='median': return median(a)
    if rule=='last': return a[-1]
    if rule.startswith('recent') and rule!='recent90': return mean(a[-int(rule[6:]):])
    if rule=='max': return max(a)
    if rule=='trimmed_mean':
        s=sorted(a);n=int(len(s)*.2);return mean(s[n:len(s)-n] or s)
    if rule=='p75':
        s=sorted(a);return s[round((len(s)-1)*.75)]
    if rule=='recent90':
        cutoff=day(g[-1]['event_date'])-timedelta(days=89)
        return mean(amount(e,home) for e in g if day(e['event_date'])>=cutoff)
    raise ValueError(rule)
def simulate(r, rule='mean', timing='settlement', include_today=True,
             semantics=True, grouping='category', changes=None,
             salary_mode='last', horizon=89, round_stream=True,
             delay_persists=True, image_history=False, messages=True,
             expense_scale=1.0, variable_cadence=None, monthly_horizon=False,
             expense_inclusion='all', amount_estimator=None, hold_today=False):
    p=PROFILES[r['user_id']]; home=p['home_currency']; start=day(r['request_date']); end=start+timedelta(days=horizon)
    if monthly_horizon:
        end=month_next(month_next(start));end=end.replace(day=calendar.monthrange(end.year,end.month)[1]);horizon=(end-start).days
    es=[e for e in EVENTS if e['user_id']==r['user_id']]
    ms=[m for m in MESSAGES if m['user_id']==r['user_id'] and m['sent_at'][:10]<=r['request_date']]
    if not messages:ms=[]
    flows=defaultdict(float); trace=[]; streams=[]; warnings=[]
    def post(d,a,source):
        if start<=d<=end:
            flows[d]+=a; trace.append((d.isoformat(),round(a,4),source))
    # The current profile balance is the opening snapshot; never replay historical cash.
    for e in es:
        if e['status'] in ('pending','scheduled') and e['direction']=='debit':
            d=day(e['settlement_date'] if timing=='settlement' else e['event_date'])
            if hold_today and e['status']=='pending':d=start
            post(max(start,d),-amount(e,home),e['event_id'])
        elif e['status']=='settled' and e['settlement_date']>=start.isoformat():
            if include_today or e['settlement_date']>start.isoformat():
                post(day(e['settlement_date']),amount(e,home)*(1 if e['direction']=='credit' else -1),e['event_id'])
    groups=defaultdict(list)
    for e in es:
        if e['status']!='settled' or e['event_date']>=start.isoformat() or e['direction']!='debit':continue
        if e['linked_event_id'] or e['event_type'] not in ('expense','subscription','debt_payment'):continue
        if not e['amount'] and not image_history:continue
        key=(e['category'],e['currency'],e['flexibility'])
        if grouping=='description':key+=(e['description'],)
        groups[key].append(e)
    for key,g in groups.items():
        fixed=key[2]=='fixed';protected=key[0] in p['expense_categories_to_protect'].split('|')
        if expense_inclusion=='fixed_protected' and not (fixed or protected):continue
        if expense_inclusion in ('fixed_only','exclude_flexible') and not fixed:continue
        g.sort(key=lambda x:x['event_date'])
        # Reject incidental rows off the regular calendar grid, without ID exceptions.
        dates=[day(e['event_date']) for e in g]
        if len(g)<3:continue
        dom,count=Counter(d.day for d in dates).most_common(1)[0]
        monthly=count>=3 and count/len(g)>=0.7
        if monthly:g=[e for e in g if day(e['event_date']).day==dom]
        dates=[day(e['event_date']) for e in g]
        diffs=[(b-a).days for a,b in zip(dates,dates[1:])]
        step=Counter(diffs).most_common(1)[0][0]
        if not monthly and (step not in (5,7,10,14,21) or sum(x==step for x in diffs)/len(diffs)<0.7):continue
        a=forecast_amount(g,rule,home)
        if amount_estimator and len({e['amount'] for e in g})>1:
            a=amount_estimator([amount(e,home) for e in g])
        if len({e['amount'] for e in g})>1:a*=expense_scale
        if not monthly and variable_cadence:step=variable_cadence
        if round_stream:a=round(a,2)
        if semantics and key[0]=='rent':
            for m in ms:
                mt=m['message_text'].lower()
                match=re.search(r'increases monthly rent by (\d+(?:\.\d+)?)%',mt)
                if match:a*=1+float(match[1])/100
        if changes and key[0] in changes:a=changes[key[0]]
        d=month_next(dates[-1],dom) if monthly else dates[-1]+timedelta(days=step)
        while d<start or (d==start and not include_today):d=month_next(d,dom) if monthly else d+timedelta(days=step)
        streams.append(dict(category=key[0],anchor=g[-1]['event_id'],n=len(g),cadence='monthly' if monthly else step,amount=a,first=d.isoformat(),history_amounts=[amount(e,home) for e in g],flexibility=key[2]))
        while d<=end:
            post(d,-a,'recurring:'+key[0]);d=month_next(d,dom) if monthly else d+timedelta(days=step)
    # Semantic salary candidates: commissions, gig work, arrears and final pay cannot
    # become confirmed future salary merely by belonging to category=salary.
    inc=[e for e in es if e['category']=='salary' and e['direction']=='credit' and e['status'] in ('settled','scheduled')]
    regular=[e for e in inc if re.search(r'payroll|salary',e['description'],re.I) and not re.search(r'final|arrears|net salary',e['description'],re.I)] if semantics else inc
    regular.sort(key=lambda x:x['settlement_date'])
    ended=semantics and (any('final employer payroll' in e['description'].lower() for e in inc) or any('contract has ended' in m['message_text'].lower() for m in ms))
    if regular and not ended:
        latest=regular[-1];a=float(latest['amount']) if latest['amount'] else IMAGE_FACTS[IMAGES[latest['event_id']]]['amount']; currency=latest['currency']
        hist=[e for e in regular if e['status']=='settled']
        dom=day(latest['settlement_date'] if timing=='settlement' else latest['event_date']).day
        d=day(latest['settlement_date']) if latest['status']=='scheduled' else month_next(day(latest['settlement_date']),dom)
        if salary_mode=='mean':a=mean(float(e['amount']) if e['amount'] else IMAGE_FACTS[IMAGES[e['event_id']]]['amount'] for e in regular)
        shift=None
        if semantics:
            for m in ms:
                mt=m['message_text'];low=mt.lower()
                # Explicit amounts in payroll amendments (English and Indonesian).
                if m['source_type']=='employer':
                    match=re.search(r'(?:EUR|IDR|INR|USD|ZAR)\s+(\d+(?:\.\d+)?)',mt)
                    if match:a=float(match[1])
                    date_match=re.search(r'\d{4}-\d{2}-\d{2}',mt)
                    if date_match:
                        d=day(date_match[0])
                        if 'replaces the payroll date' in low:shift=d
                        dom=d.day
        while d<start:d=month_next(d,dom)
        streams.append(dict(category='salary',anchor=latest['event_id'],n=len(regular),cadence='monthly',amount=a,first=d.isoformat()))
        while d<=end:
            cash=a if currency==home else a*RATES[(d.isoformat(),currency,home)]
            post(d,cash,'recurring:salary')
            d=month_next(d,dom if (delay_persists or not shift) else 15)
    bal=float(p['current_available_balance']); floor=float(p['minimum_balance_to_keep']); requested=float(r['requested_amount'])
    path=[]
    for i in range(horizon+1):
        d=start+timedelta(days=i);bal+=flows[d];path.append(bal)
    suffix=list(path)
    for i in range(len(path)-2,-1,-1):suffix[i]=min(suffix[i],suffix[i+1])
    baseline=min(float(p['current_available_balance']),min(path))
    safe=round(max(0,min(requested,baseline-floor)),2)
    earliest=next(((start+timedelta(days=i)).isoformat() for i,b in enumerate(suffix) if b-floor>=requested-0.005),'')
    return dict(min_balance=round(baseline,2),min_date=(start+timedelta(days=path.index(min(path)))).isoformat(),safe=safe,earliest=earliest,streams=streams,trace=sorted(trace),path=path,warnings=warnings)

def compare(**kw):
    rows=[]
    for r in SAMPLES:
        pred=simulate(r,**kw)
        rows.append(dict(request_id=r['request_id'],currency=PROFILES[r['user_id']]['home_currency'],min_balance=pred['min_balance'],min_date=pred['min_date'],predicted_safe=pred['safe'],true_safe=float(r['amount_safe_to_pay']),safe_error=round(pred['safe']-float(r['amount_safe_to_pay']),2),predicted_earliest=pred['earliest'],true_earliest=r['earliest_date_for_full_payment'],date_match=pred['earliest']==r['earliest_date_for_full_payment']))
    return rows
def write_csv(name,rows):
    with (OUT/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
    scores=[];allrows=[]
    for rule in ['mean','median','recent2','recent3','recent4','recent5','recent6','recent8','recent90','trimmed_mean','p75','last','max']:
        rows=compare(rule=rule)
        for x in rows:allrows.append(dict(candidate=rule,**x))
        scores.append(dict(candidate=rule,safe_exact=sum(abs(x['safe_error'])<.011 for x in rows),date_exact=sum(x['date_match'] for x in rows),normalized_MAE=round(mean(abs(x['safe_error'])/float(r['requested_amount']) for x,r in zip(rows,SAMPLES)),6)))
    write_csv('candidate_scores.csv',scores);write_csv('candidate_comparisons.csv',allrows)
    write_csv('baseline_90day.csv',compare())
    write_csv('calendar_month_hypothesis.csv',compare(monthly_horizon=True))
    variants={
        'baseline_mean':{}, 'exclude_request_day':dict(include_today=False),
        'event_date_without_messages':dict(timing='event',messages=False),
        'settlement_without_messages':dict(messages=False),
        'one_cycle_salary_delay':dict(delay_persists=False),
        'all_salary_category_recurs':dict(semantics=False),
        'salary_history_mean':dict(salary_mode='mean'),
        'image_purchases_in_history':dict(image_history=True),
        'description_grouping':dict(grouping='description'),
        'all_variable_weekly':dict(variable_cadence=7),
        'all_variable_fortnightly':dict(variable_cadence=14),
        '90_days_after_request_inclusive':dict(horizon=90),
        'three_calendar_months':dict(monthly_horizon=True),
    }
    ablations=[];details=[]
    for name,kw in variants.items():
        rows=compare(**kw)
        details.extend(dict(candidate=name,**x) for x in rows)
        ablations.append(dict(candidate=name,safe_exact=sum(abs(x['safe_error'])<.011 for x in rows),date_exact=sum(x['date_match'] for x in rows),normalized_MAE=round(mean(abs(x['safe_error'])/float(r['requested_amount']) for x,r in zip(rows,SAMPLES)),6)))
    write_csv('ablation_scores.csv',ablations);write_csv('ablation_comparisons.csv',details)
    traces={r['request_id']:simulate(r) for r in SAMPLES}
    (OUT/'baseline_traces.json').write_text(json.dumps(traces,indent=2),encoding='utf-8')
    print(json.dumps(scores+ablations,indent=2))
if __name__=='__main__':main()
