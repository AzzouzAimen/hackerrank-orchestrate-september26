import json,re,hashlib,pandas as pd
from pathlib import Path
p=Path('code/prototype/extraction_artifacts/semantic_inventory_01/semantic_split_20260912_v1.json');j=json.loads(p.read_text());m=pd.read_csv('dataset/messages.csv').fillna('')
def n(s): return re.sub(r'[^a-z<> ]','',re.sub(r'\d{4}-\d\d-\d\d|\d+([.,]\d+)?|(?:emp|ser|ban|fin|mer)-\d+','<N>',s.lower()))
for x in j['development']+j['holdout']: x['message_template_id']='tmpl_'+hashlib.sha1(n(m[m.message_id.eq(x['message_ids'][0])].iloc[0].message_text).encode()).hexdigest()[:12]
D={x['message_template_id'] for x in j['development']};print('overlap',[(x['case_id'],x['message_template_id']) for x in j['holdout'] if x['message_template_id'] in D])
ids=['message_01','message_184','message_35','message_17','message_192','message_208','message_209','message_214']; out=[]
for mid in ids:
 r=m[m.message_id.eq(mid)].iloc[0]; out.append({'case_id':'holdout_'+r.user_id,'user_id':r.user_id,'split':'holdout_candidate','message_ids':[mid],'image_ids':[],'linked_event_ids':([r.related_event_id] if r.related_event_id else []),'semantic_family':'refined_inventory','inclusion_reason':'distinct normalized template','template_family':'refined','message_template_id':'tmpl_'+hashlib.sha1(n(r.message_text).encode()).hexdigest()[:12],'contamination':'clean','annotation_difficulty':'medium','ambiguity_notes':'Review before annotation.','source':'real_dataset'})
j['holdout']=out;j['version']='semantic-split-20260912-v2';j['frozen']=False;j['checks']['cross_split_template_families']=[];j['checks']['template_identity']='normalized skeleton SHA1';(p.parent/'semantic_split_20260912_v2.json').write_text(json.dumps(j,indent=2,ensure_ascii=False));print('wrote',len(out))
