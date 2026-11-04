"""Deterministic scale orchestration only; frozen scientific functions unchanged."""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import json,hashlib,shutil,time
from experiments.product_recovery_v1.foundation import build,reporting_truth,project
from experiments.product_recovery_v1.publication import publish
from experiments.product_recovery_v1.generate import write
from experiments.product_recovery_v1.inference.contracts import validate_inputs
from experiments.product_recovery_v1_validation.run_validation import verify_development
HERE=Path(__file__).resolve().parent
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def worker(cell):
 cfg=read('experiments/product_recovery_v1/config.json');ledger,c=build(cell['archetype'],cell['generator_index'],cell['seed'],cell['target_employees']);public,_=project(ledger);clean,messy,contacts=publish(public,cfg,cell['seed'],cell['disclosure']);validate_inputs(clean,contacts);validate_inputs(messy,contacts)
 # Sources exist before selected reporting truth, as in frozen development/validation.
 truth=reporting_truth(ledger,c);return cell,ledger.read(),clean,messy,contacts,truth,len(public.contacts),ledger.sha256

def verify_validation():
 verify_development();data=Path('data/product_recovery_v1_validation');report=Path('reports/product_recovery_v1_validation');f=read(data/'PRE_GENERATION_FREEZE.json');assert all(sha(p)==h for p,h in f['sha256'].items());s=read(data/'source_inputs/SOURCE_ONLY_MANIFEST.json');assert all(sha(data/'source_inputs'/p)==h for p,h in s['files_sha256'].items());p=read(report/'predictions_1/PREDICTION_FREEZE.json');assert all(sha(report/'predictions_1'/r)==h for r,h in p['files_sha256'].items());assert sha(report/'evaluation_1/METRICS.json')==read(report/'evaluation_1/EVALUATION_FREEZE.json')['metrics_sha256'];return f

def main():
 old=verify_validation();protocol=read(HERE/'PROTOCOL.json');target=Path('data/product_recovery_v1_scale500');out=Path('reports/product_recovery_v1_scale500');assert not target.exists();assert not (out/'PRE_PREDICTION_FREEZE.json').exists();assert shutil.disk_usage(Path.cwd()).free>=5*1024**3
 frozen={**old['sha256'],**{p.as_posix():sha(p) for p in HERE.iterdir() if p.suffix in {'.py','.json','.md'}}};write(target/'PRE_GENERATION_FREEZE.json',dict(version=protocol['version'],companies=protocol['companies'],sha256=frozen,seed_range=protocol['seed_range'],process_workers=3,source_schema_sha256=sha(Path('experiments/product_recovery_v1/inference/contracts.py')),interpretation='scale-up, not independent validation'))
 old_ids=set();old_people=set()
 for base in ['data/product_recovery_v1/development/source_inputs','data/product_recovery_v1_validation/source_inputs']:
  for p in Path(base).glob('company_*/clean.json'):old_ids.add(read(p)['company_id'])
  for p in Path(base).glob('company_*/contacts.json'):old_people|={r['employee_id'] for r in read(p)}
 stage=target/'source_inputs';summaries=[];seen=set();companies=set();start=time.monotonic();progress=out/'GENERATION_PROGRESS.json'
 try:
  with ProcessPoolExecutor(max_workers=3) as pool:
   for cell,facts,clean,messy,contacts,truth,master,facts_hash in pool.map(worker,protocol['companies'],chunksize=1):
    case=f"company_{cell['index']:02}";ids={r['employee_id'] for r in contacts};assert not ids&seen and not ids&old_people;assert clean['company_id'] not in companies|old_ids;seen|=ids;companies.add(clean['company_id'])
    write(target/case/'technical_audit/facts.json',facts)
    for v,view in [('clean',clean),('messy',messy)]:write(stage/case/f'{v}.json',view)
    write(stage/case/'contacts.json',contacts);write(target/case/'technical_audit/truth.json',truth);summaries.append(dict(cell,company_id=clean['company_id'],master_employees=master,visible_employees=len(contacts),clean_documents=len(clean['documents']),messy_documents=len(messy['documents']),facts_sha256=facts_hash))
    progress.write_text(json.dumps({'completed_companies':len(summaries),'visible_contacts':sum(c['visible_employees'] for c in summaries),'elapsed_seconds':round(time.monotonic()-start,2),'minimum_visible_so_far':min(c['visible_employees'] for c in summaries),'status':'generating'},indent=2)+'\n')
    if len(summaries)%25==0:print('Generated',len(summaries),'/500 companies;',len(seen),'contacts;',round(time.monotonic()-start,1),'seconds',flush=True)
    if shutil.disk_usage(Path.cwd()).free<5*1024**3:raise RuntimeError('Resource floor reached: stop without protocol change')
 except BaseException as e:
  progress.write_text(json.dumps({'completed_companies':len(summaries),'status':'stopped_incomplete','error':repr(e),'companies':summaries},indent=2)+'\n');raise
 files={p.relative_to(stage).as_posix():sha(p) for p in stage.rglob('*.json')};write(stage/'SOURCE_ONLY_MANIFEST.json',dict(files_sha256=files,scope='all500 frozen scale-up companies, source-only'))
 write(target/'COHORT_SUMMARY.json',summaries);write(out/'PRE_PREDICTION_FREEZE.json',dict(code_and_protocol_sha256=frozen,source_sha256=files,generator_freeze_sha256=sha(target/'PRE_GENERATION_FREEZE.json'),truth_used_for_rules=False));visible=dict(companies=len(summaries),master_contacts=sum(c['master_employees'] for c in summaries),visible_contacts=len(seen),minimum_company_contacts=min(c['visible_employees'] for c in summaries),maximum_company_contacts=max(c['visible_employees'] for c in summaries),minimum100_met=all(c['visible_employees']>=100 for c in summaries),company_employee_ids_disjoint=True,elapsed_seconds=round(time.monotonic()-start,2));write(out/'VISIBLE_DENOMINATORS_BEFORE_EVALUATION.json',visible);progress.write_text(json.dumps(visible|{'status':'complete'},indent=2)+'\n');print(json.dumps(visible,indent=2),flush=True)
if __name__=='__main__':main()
