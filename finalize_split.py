import json,hashlib,re
from pathlib import Path
import pandas as pd
p=Path('code/prototype/extraction_artifacts/semantic_inventory_01/semantic_split_20260912_v2.json'); j=json.loads(p.read_text()); m=pd.read_csv('dataset/messages.csv').fillna(''); im=pd.read_csv('dataset/images.csv').fillna('')
fam={'user16':'rent_stream_amendment','user03':'salary_arrears_image','user06':'temporary_pay','user12':'ended_seasonal_income','user28':'salary_arrears','user04':'pending_bonus','user10':'pending_payout','user26':'approved_invoice','user20':'pending_refund','user18':'internal_transfer','user229':'failed_debit_retry','user22':'investment_non_cash','user23':'prize_pending','user14':'salary_and_recurring_expense','user02':'salary_change','user36':'salary_change','user235':'fx_refund','user48':'property_receipt_image','user24':'prize_completed','user246':'employment_ended','user267':'fx_charge','user209':'prize_pending'}
def norm(s):
 s=re.sub(r'\d{4}-\d\d-\d\d|\d+([.,]\d+)?|(?:emp|ser|ban|fin|mer)-\d+','<N>',s.lower()); return re.sub(r'[^a-z<> ]','',s)
for x in j['development']+j['holdout']:
 u=x['user_id']; row=m[m.user_id.eq(u)]
 if row.empty: x['ambiguity_notes']='REJECT: user/message not found'; continue
 txt=row.iloc[0].message_text; x['semantic_family']=fam.get(u,'review_required'); x['template_family']='normalized_message_skeleton'; x['message_template_id']='tmpl_'+hashlib.sha1(norm(txt).encode()).hexdigest()[:12]
 x['image_ids']=im[im.user_id.eq(u)].image_id.tolist(); x['linked_event_ids']=list(dict.fromkeys(([row.iloc[0].related_event_id] if row.iloc[0].related_event_id else [])+im[im.user_id.eq(u)].related_event_id.tolist()))
 x['ambiguity_notes']='No obvious ambiguity; inspect linked event lifecycle and image fields before annotation.'
D={x['message_template_id'] for x in j['development']}; H={x['message_template_id'] for x in j['holdout']}; j['checks']['cross_split_template_families']=sorted(D&H); j['checks']['template_identity']='normalized message skeleton (dates, numbers, references replaced) SHA1'; j['frozen']=True; j['version']='semantic-split-20260912-v3'; j['purpose']='final reviewed split before semantic annotation'; (p.parent/'semantic_split_20260912_v3.json').write_text(json.dumps(j,indent=2,ensure_ascii=False),encoding='utf8'); print('counts',len(j['development']),len(j['holdout']),'overlap',D&H)
