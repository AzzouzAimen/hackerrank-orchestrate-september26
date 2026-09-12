"""Paired prompt-definition experiment on the frozen rent treatment input."""
from __future__ import annotations
import argparse, copy, hashlib, json, os
from datetime import datetime, timezone
from pathlib import Path
from . import extraction_experiment as frozen
from . import rent_history_experiment as rent

CLARIFICATION = ('When an image separately states a balance due, a gross invoice or receipt total '
                 'is not `current_amount_due`; use the stated balance as the outstanding amount and '
                 'keep amounts received separate as `amount_paid`.')
VERSION = 'semantic-image-definition-v1'

def payload(case, prompt, correction=None):
    return {'model': frozen.MODEL, 'messages':[{'role':'system','content':prompt},
      {'role':'user','content':frozen.request_content(case, correction)}], **frozen.SETTINGS}
def write_new(path, value):
    with path.open('x',encoding='utf-8',newline='\n') as h: json.dump(value,h,indent=2,ensure_ascii=False); h.write('\n')
def execute(output, approved_by):
    if not approved_by or not approved_by.strip(): raise ValueError('approval attribution required')
    case=rent.arms()['treatment']; prompts={'control':frozen.SYSTEM_PROMPT,'treatment':frozen.SYSTEM_PROMPT+'\n\n'+CLARIFICATION}
    plan={'version':VERSION,'executed':True,'approved_by':approved_by,'sequence':['control','treatment']*3,
      'configuration':{'provider':frozen.PROVIDER,'model':frozen.MODEL,'endpoint':frozen.ENDPOINT,'integration_version':frozen.INTEGRATION_VERSION,'timeout_seconds':frozen.REQUEST_TIMEOUT_SECONDS,'settings':frozen.SETTINGS,'schema':frozen.compact_schema(),'retry_policy':'one visible retry after provider or schema failure'},'prompt_variant':CLARIFICATION,'prompts':prompts,'input_case':'rep_user16 treatment from rent_run_02','image_hashes':{Path(x).name:hashlib.sha256(Path(x).read_bytes()).hexdigest() for x in case['image_paths']},'started_at':datetime.now(timezone.utc).isoformat()}
    frozen.load_env(); secret=os.environ.get('FEATHERLESS_API_KEY');
    if not secret: raise RuntimeError('FEATHERLESS_API_KEY is not configured')
    def sanitize(v):
        if isinstance(v,str): return v.replace(secret,'[REDACTED]')
        if isinstance(v,dict): return {k:sanitize(x) for k,x in v.items()}
        if isinstance(v,list): return [sanitize(x) for x in v]
        return v
    output.mkdir(parents=True,exist_ok=False); write_new(output/'manifest.json',sanitize(plan)); original=frozen.call_model; records=[]
    try:
      for index,arm in enumerate(plan['sequence'],1):
        attempts=0; prompt=prompts[arm]
        def captured(c,correction=None):
          nonlocal attempts; attempts+=1; prefix=f'{index:02d}_{arm}_attempt{attempts}'; req=payload(c,prompt,correction); write_new(output/(prefix+'_request.json'),sanitize(req))
          try: response,latency=original(c,correction)
          except Exception as exc: write_new(output/(prefix+'_error.json'),sanitize({'type':type(exc).__name__,'message':str(exc)})); raise
          write_new(output/(prefix+'_response.json'),sanitize({'response':response,'latency_seconds':latency})); return response,latency
        frozen.call_model=captured
        # call_model reads the module prompt; patch only for this logical run.
        old_prompt=frozen.SYSTEM_PROMPT; frozen.SYSTEM_PROMPT=prompt
        try: run=frozen.extract_once(case)
        finally: frozen.SYSTEM_PROMPT=old_prompt
        rec=sanitize({'arm':arm,'logical_run':index,'run':run}); write_new(output/(f'{index:02d}_{arm}_result.json'),rec); records.append(rec)
    finally: frozen.call_model=original
    summary={}
    for arm in ('control','treatment'):
      g=[r for r in records if r['arm']==arm]; aa=[a for r in g for a in r['run']['attempts']]
      summary[arm]={'logical_runs':len(g),'first_attempt_usable':sum(a['schema_valid'] for a in [r['run']['attempts'][0] for r in g]),'retry_recoveries':sum(r['run']['usable'] and not r['run']['attempts'][0]['schema_valid'] for r in g),'final_usable':sum(r['run']['usable'] for r in g),'attempts':len(aa),'empty_outputs':sum(a.get('raw_content')=='' and not a.get('provider_failure') for a in aa),'schema_invalid_nonempty':sum(bool(a.get('raw_content')) and not a['schema_valid'] for a in aa),'provider_exceptions':sum(bool(a.get('provider_failure')) for a in aa),'latencies_seconds':[a['latency_seconds'] for a in aa if a['latency_seconds'] is not None],'usage':{k:sum(a.get('usage',{}).get(k,0) for a in aa) for k in ('prompt_tokens','completion_tokens','total_tokens','cached_tokens')}}
    write_new(output/'summary.json',summary); write_new(output/'claim_review_template.json',[{'arm':r['arm'],'logical_run':r['logical_run'],'attempt':a['attempt'],'usable':a['schema_valid'],'review_status':'pending' if a['schema_valid'] else 'output unavailable'} for r in records for a in r['run']['attempts']]); return summary
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--run',action='store_true'); ap.add_argument('--approved-by'); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args()
    if not a.run: raise SystemExit('Use --run for the approved six-run experiment')
    print(json.dumps(execute(a.output,a.approved_by),indent=2))
