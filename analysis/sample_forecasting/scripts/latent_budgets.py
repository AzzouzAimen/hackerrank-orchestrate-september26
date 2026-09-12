"""Residual attribution and general latent-center experiments; samples only."""
import math,json,itertools
from collections import Counter,defaultdict
from statistics import mean,median
import investigate as a

def trimmed(v):
    s=sorted(v);k=int(.2*len(s));return mean(s[k:len(s)-k])
def winsor(v):
    s=sorted(v);k=int(.2*len(s));return mean(max(s[k],min(s[-k-1],x)) for x in s)
def sig(x,n):return round(x,n-1-int(math.floor(math.log10(abs(x))))) if x else 0
def estimators():
    result={'mean':mean,'median':median,'trimmed20':trimmed,'winsor20':winsor}
    for name,fn in list(result.items()):
        for n in (1,2,3):result[f'{name}_sig{n}']=lambda v,fn=fn,n=n:sig(fn(v),n)
    return result
EST=estimators()
def uncapped(r):return 0<float(r['amount_safe_to_pay'])<float(r['requested_amount'])
def summarize(rows):
    u=[x for x in rows if x['uncapped']]
    return dict(nmae=mean(abs(x['norm_error']) for x in rows),bias=mean(x['norm_error'] for x in rows),uncapped_nmae=mean(abs(x['norm_error']) for x in u),uncapped_bias=mean(x['norm_error'] for x in u),exact=sum(abs(x['error'])<.011 for x in rows),uncapped_exact=sum(abs(x['error'])<.011 for x in u),dates=sum(x['date_match'] for x in rows),improved=sum(x['amount_improved'] for x in rows),regressed=sum(x['amount_regressed'] for x in rows),date_gained=sum(x['date_gained'] for x in rows),date_lost=sum(x['date_lost'] for x in rows))

def main():
    bases={r['request_id']:a.simulate(r) for r in a.SAMPLES}
    variants=[(name,'all',h,dict(amount_estimator=fn,monthly_horizon=h=='calendar')) for name,fn in EST.items() for h in ('90dates','calendar')]
    variants += [('mean',inc,h,dict(expense_inclusion=inc,monthly_horizon=h=='calendar')) for inc in ('fixed_protected','fixed_only','exclude_flexible') for h in ('90dates','calendar')]
    variants += [('hold_today','all','90dates',dict(hold_today=True))]
    details=[];scores=[]
    for name,inc,h,kw in variants:
        v=f'{name}/{inc}/{h}';rows=[]
        for r in a.SAMPLES:
            b=bases[r['request_id']];x=a.simulate(r,**kw);truth=float(r['amount_safe_to_pay']);err=x['safe']-truth;be=b['safe']-truth;dm=x['earliest']==r['earliest_date_for_full_payment'];bd=b['earliest']==r['earliest_date_for_full_payment']
            rows.append(dict(variant=v,request_id=r['request_id'],uncapped=uncapped(r),min_balance=x['min_balance'],safe=x['safe'],true_safe=truth,error=round(err,2),norm_error=err/float(r['requested_amount']),earliest=x['earliest'],true_earliest=r['earliest_date_for_full_payment'],date_match=dm,amount_improved=abs(err)<abs(be)-.011,amount_regressed=abs(err)>abs(be)+.011,date_gained=dm and not bd,date_lost=bd and not dm))
        scores.append(dict(variant=v,**summarize(rows)));details+=rows
    a.write_csv('latent_variant_scores.csv',scores);a.write_csv('latent_variant_samples.csv',details)
    residuals=[];decomp=[];centers=[];holdout=[];phase=[]
    for r in a.SAMPLES:
        b=bases[r['request_id']];p=a.PROFILES[r['user_id']];target=float(p['minimum_balance_to_keep'])+float(r['amount_safe_to_pay']);delta=b['min_balance']-target
        if uncapped(r):
            residuals.append(dict(request_id=r['request_id'],implied_min=target,baseline_min=b['min_balance'],residual=round(delta,2),normalized_residual=delta/float(r['requested_amount']),min_date=b['min_date']))
            postings=defaultdict(float);counts=Counter()
            for dt,val,source in b['trace']:
                if dt<=b['min_date']:postings[source]+=val;counts[source]+=1
            assert abs(float(p['current_available_balance'])+sum(postings.values())-b['min_balance'])<.011
            for source,total in postings.items():
                if not source.startswith('recurring:') or total>=0:continue
                cat=source.split(':',1)[1];s=next(s for s in b['streams'] if s['category']==cat)
                # One equation at the current binding date; alternative single-category
                # solutions below re-simulate the entire path, allowing the minimum to move.
                req=s['amount']+delta/counts[source]
                lo=0.;hi=max(s['amount']*4,s['amount']+abs(delta)*2,1.)
                at_lo=a.simulate(r,changes={cat:lo})['min_balance'];at_hi=a.simulate(r,changes={cat:hi})['min_balance']
                feasible=at_hi<=target<=at_lo
                root='';new_date=''
                if feasible:
                    for _ in range(40):
                        mid=(lo+hi)/2;y=a.simulate(r,changes={cat:mid})
                        if y['min_balance']>target:lo=mid
                        else:hi=mid
                    root=round((lo+hi)/2,4);new_date=a.simulate(r,changes={cat:root})['min_date']
                decomp.append(dict(request_id=r['request_id'],category=cat,variable=len(set(s['history_amounts']))>1,forecast_amount=s['amount'],count_to_min=counts[source],debits_to_min=round(-total,2),required_amount_at_original_min=round(req,4),required_pct_change=delta/counts[source]/s['amount']*100,global_single_category_solution=root,new_min_date=new_date,identifiable=False))
            variable_debits=sum(-postings['recurring:'+s['category']] for s in b['streams'] if len(set(s.get('history_amounts',[])))>1)
            residuals[-1]['uniform_variable_pct_at_original_min']=100*delta/variable_debits if variable_debits else ''
            # Descriptive counterfactual only: never supplied to the simulator as a rule.
            missing=[s for s in b['streams'] if len(set(s.get('history_amounts',[])))>1 and counts['recurring:'+s['category']]==0]
            for n in (1,2):
                for subset in itertools.combinations(missing,n):
                    total=sum(s['amount'] for s in subset)
                    phase.append(dict(request_id=r['request_id'],categories='+'.join(s['category'] for s in subset),extra_debit=total,residual=delta,remaining_residual=round(delta-total,2),interpretation='Hypothetical extra occurrence before minimum; NOT a fitted prediction policy'))
        for s in b['streams']:
            v=s.get('history_amounts',[])
            if len(set(v))<2:continue
            cut=len(v)//2;center=mean(v);cv=(mean((x-center)**2 for x in v)**.5)/center
            centers.append(dict(request_id=r['request_id'],category=s['category'],n=len(v),mean=center,median=median(v),trimmed=trimmed(v),winsor=winsor(v),sig2=sig(center,2),relative_sig2_move=(sig(center,2)-center)/center,cv=cv,first_half_mean=mean(v[:cut]),second_half_mean=mean(v[cut:]),half_drift=(mean(v[cut:])-mean(v[:cut]))/center))
            for name,fn in EST.items():holdout.append(dict(estimator=name,relative_error=abs(fn(v[:cut])-mean(v[cut:]))/center))
    a.write_csv('latent_implied_minima.csv',residuals);a.write_csv('latent_residual_decomposition.csv',decomp);a.write_csv('latent_stream_centers.csv',centers)
    a.write_csv('latent_missing_occurrence_counterfactuals.csv',phase)
    hs=[dict(estimator=name,mean_relative_half_center_error=mean(x['relative_error'] for x in holdout if x['estimator']==name)) for name in EST]
    a.write_csv('latent_history_holdout.csv',hs)
    (a.OUT/'latent_diagnostics.json').write_text(json.dumps(dict(variable_streams=len(centers),median_cv=median(x['cv'] for x in centers),median_abs_half_drift=median(abs(x['half_drift']) for x in centers),median_sig2_change=median(abs(x['relative_sig2_move']) for x in centers),positive_residuals=sum(x['residual']>0 for x in residuals),negative_residuals=sum(x['residual']<0 for x in residuals)),indent=2),encoding='utf-8')
    print(json.dumps(sorted(scores,key=lambda x:x['uncapped_nmae'])[:12],indent=2));print(json.dumps(hs,indent=2))

if __name__=='__main__':main()
