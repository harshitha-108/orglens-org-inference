"""Fixed development generation; facts/sources committed before selecting reporting edges."""
from pathlib import Path
import json,hashlib
from .foundation import build,reporting_truth,project
from .publication import publish
D=Path(__file__).resolve().parent;ROOT=D.parents[1]
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8') as f:json.dump(x,f,indent=2);f.write('\n')
def main():
 cfg=read(D/'config.json');target=Path('data/product_recovery_v1/development');out=Path('reports/product_recovery_v1/development')
 if target.exists() or out.exists():raise ValueError('Fixed development cohort already exists; refusing regeneration')
 files=[p for p in D.rglob('*') if p.is_file() and p.suffix in {'.py','.json','.md'} and '__pycache__' not in p.parts]
 for base in ['experiments/v4_m25a','experiments/v4_m24_history','experiments/v4_m22_sources']:
  files += [p for p in Path(base).glob('*') if p.suffix in {'.py','.json'}]
 cells=[dict(index=i,archetype=a,disclosure=r,seed=cfg['development_seed']+i,target_employees=cfg['target_employees'][i%3]) for i,(a,r) in enumerate((a,r) for a in cfg['archetypes'] for r in cfg['regimes'])]
 write(target/'PRE_GENERATION_FREEZE.json',dict(version=cfg['version'],companies=cells,sha256={p.as_posix():sha(p) for p in files},assumptions='explicit synthetic scenario, no verified real-world distribution',validation_generated=False))
 stage=target/'source_inputs';summaries=[]
 for cell in cells:
  i=cell['index'];case=f'company_{i:02}';ledger,c=build(cell['archetype'],i,cell['seed'],cell['target_employees']);public,_=project(ledger)
  # Publisher has not been given any selected reporting edges.
  clean,messy,contacts=publish(public,cfg,cell['seed'],cell['disclosure']);write(target/case/'technical_audit/facts.json',ledger.read())
  for label,view in [('clean',clean),('messy',messy)]:write(stage/case/f'{label}.json',view)
  write(stage/case/'contacts.json',contacts);truth=reporting_truth(ledger,c);write(target/case/'technical_audit/truth.json',truth)
  summaries.append(dict(cell,master_employees=len(public.contacts),visible_employees=len(contacts),clean_documents=len(clean['documents']),messy_documents=len(messy['documents']),facts_sha256=ledger.sha256))
 source_files={p.relative_to(stage).as_posix():sha(p) for p in stage.rglob('*.json')};write(stage/'SOURCE_ONLY_MANIFEST.json',dict(files_sha256=source_files,scope='new fixed development companies only; source-only inputs'))
 write(target/'COHORT_SUMMARY.json',summaries);out.mkdir(parents=True);write(out/'PRE_PREDICTION_FREEZE.json',dict(code_and_protocol_sha256={p.as_posix():sha(p) for p in files},source_sha256=source_files,generator_freeze_sha256=sha(target/'PRE_GENERATION_FREEZE.json'),truth_used_for_rules=False));print(json.dumps(summaries,indent=2))
if __name__=='__main__':main()
