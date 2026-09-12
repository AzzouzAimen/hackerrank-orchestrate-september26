from pathlib import Path
import pandas as pd, json, re, hashlib
ROOT=Path(__file__).resolve().parents[2]; DATA=ROOT/'dataset'; OUT=Path(__file__).resolve().parent/'extraction_artifacts'/'semantic_inventory_01'; OUT.mkdir(parents=True,exist_ok=True)
FAMS=[('salary_change',r'(increased|naik|changed|berubah|salary.*confirmed|gaji.*dikonfirmasi)'),('temporary_pay',r'temporary monthly pay|reduced amount|salary is reduced|gaji.*sementara'),('ended_income',r'contract has ended|employment has ended|pendapatan.*berakhir|income that has ended'),('arrears',r'arrears|tunggakan'),('pending_income',r'pending approval|belum disetujui|still pending|payment processing'),('invoice',r'approved.*invoice|invoice payment|faktur.*disetujui'),('refund',r'refund.*initiated|pengembalian dana'),('fx',r'foreign-currency|home-currency.*settlement|mata uang asing'),('transfer',r'transfer between your two accounts|transfer antara dua rekening'),('failed_retry',r'debit attempt failed|debit.*gagal'),('investment_noncash',r'investment.*not.*sold|market value.*no cash|investasi.*belum dijual'),('prize',r'prize claim|prize proceeds|hadiah'),('rent',r'renewed lease|perpanjangan sewa'),('receipt',r'receipt|receipt has the final')]
def fam(t):
 return [n for n,p in FAMS if re.search(p,t or '',re.I)] or ['other']
def main():
 ev=pd.read_csv(DATA/'financial_events.csv').fillna(''); msg=pd.read_csv(DATA/'messages.csv').fillna(''); img=pd.read_csv(DATA/'images.csv').fillna('')
 rows=[]
 for _,m in msg.iterrows():
  u=m.user_id; es=ev[ev.user_id.eq(u)]
  rows.append({'case_id':f'case_{u}','user_id':u,'message_ids':[m.message_id],'image_ids':img[img.user_id.eq(u)].image_id.tolist(),'linked_event_ids':([m.related_event_id] if m.related_event_id else [])+img[img.user_id.eq(u)].related_event_id.tolist(),'families':fam(m.message_text),'modalities':['message']+(['image'] if any(img.user_id.eq(u)) else []),'template_family':re.sub(r'\d+','{n}',m.message_text)[:120],'contamination':u=='user_16','difficulty':'high' if len(fam(m.message_text))>1 or u=='user_16' else 'medium','description':m.message_text[:220]})
 manifest={'version':'semantic-inventory-01','source_files':{},'counts':{'events':len(ev),'messages':len(msg),'images':len(img)},'cases':rows,'notes':'Candidates only; no split frozen, no model outputs or sample labels used.'}
 for f in ['financial_events.csv','messages.csv','images.csv']:
  manifest['source_files'][f]=hashlib.sha256((DATA/f).read_bytes()).hexdigest()
 (OUT/'candidate_manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf8')
 print(json.dumps({'families':{k:sum(k in r['families'] for r in rows) for k,_ in FAMS},'cases':len(rows),'out':str(OUT/'candidate_manifest.json')},indent=2))
if __name__=='__main__': main()
