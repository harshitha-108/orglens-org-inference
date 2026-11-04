"""Validation-only orchestration around frozen generator functions. No new world/model rules."""
from pathlib import Path
import json,hashlib
from experiments.product_recovery_v1.foundation import build,reporting_truth,project
from experiments.product_recovery_v1.publication import publish
from experiments.product_recovery_v1.generate import write
HERE=Path(__file__).resolve().parent
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def verify_development():
 dev=Path('data/product_recovery_v1/development');r=Path('reports/product_recovery_v1/development');freeze=read(dev/'PRE_GENERATION_FREEZE.json');assert all(sha(p)==h for p,h in freeze['sha256'].items());sources=read(dev/'source_inputs/SOURCE_ONLY_MANIFEST.json');assert all(sha(dev/'source_inputs'/p)==h for p,h in sources['files_sha256'].items())
 for name in ['predictions_1','reference_predictions']:
  f=read(r/name/'PREDICTION_FREEZE.json');assert all(sha(r/name/p)==h for p,h in f['files_sha256'].items())
 for name in ['evaluation_1','reference_evaluation_1']:
  f=read(r/name/'EVALUATION_FREEZE.json');assert sha(r/name/'METRICS.json')==f['metrics_sha256']
 return freeze

def main():
 baseline=verify_development();protocol=read(HERE/'PROTOCOL.json');cfg=read('experiments/product_recovery_v1/config.json');target=Path('data/product_recovery_v1_validation');out=Path('reports/product_recovery_v1_validation');assert not target.exists();assert not (out/'PRE_PREDICTION_FREEZE.json').exists()
 files={**baseline['sha256'],**{p.as_posix():sha(p) for p in HERE.iterdir() if p.is_file() and p.suffix in {'.py','.json','.md'}},'docs/v4/m0/EVALUATION_PROTOCOL.json':sha('docs/v4/m0/EVALUATION_PROTOCOL.json')}
 write(target/'PRE_GENERATION_FREEZE.json',dict(version=protocol['version'],companies=protocol['companies'],sha256=files,seed_range=[4080400,4080429],generator_rules_unchanged=True))
 stage=target/'source_inputs';summary=[];devsource=Path('data/product_recovery_v1/development/source_inputs');old_ids={read(p)['company_id'] for p in devsource.glob('company_*/clean.json')};old_employees={p['employee_id'] for path in devsource.glob('company_*/contacts.json') for p in read(path)};seen=set();company_ids=set()
 for cell in protocol['companies']:
  case=f"company_{cell['index']:02}";ledger,c=build(cell['archetype'],cell['generator_index'],cell['seed'],cell['target_employees']);public,_=project(ledger);clean,messy,contacts=publish(public,cfg,cell['seed'],cell['disclosure']);ids={p['employee_id'] for p in contacts};assert not ids&old_employees and not ids&seen;assert clean['company_id'] not in old_ids|company_ids;seen|=ids;company_ids.add(clean['company_id'])
  write(target/case/'technical_audit/facts.json',ledger.read())
  for variant,view in [('clean',clean),('messy',messy)]:write(stage/case/f'{variant}.json',view)
  write(stage/case/'contacts.json',contacts)
  # Sources are already written; selection cannot retroactively condition publication.
  truth=reporting_truth(ledger,c);write(target/case/'technical_audit/truth.json',truth)
  summary.append(dict(cell,company_id=clean['company_id'],master_employees=len(public.contacts),visible_employees=len(contacts),clean_documents=len(clean['documents']),messy_documents=len(messy['documents']),facts_sha256=ledger.sha256))
 source_files={p.relative_to(stage).as_posix():sha(p) for p in stage.rglob('*.json')};write(stage/'SOURCE_ONLY_MANIFEST.json',dict(scope='30 fixed fresh company-disjoint validation cases; no hidden labels in staging',files_sha256=source_files));write(target/'COHORT_SUMMARY.json',summary)
 write(out/'PRE_PREDICTION_FREEZE.json',dict(code_and_protocol_sha256=files,source_sha256=source_files,generator_freeze_sha256=sha(target/'PRE_GENERATION_FREEZE.json'),truth_used_for_rules=False))
 write(out/'VISIBLE_DENOMINATORS_BEFORE_EVALUATION.json',dict(companies=len(summary),master_contacts=sum(x['master_employees'] for x in summary),visible_contacts=sum(x['visible_employees'] for x in summary),minimum_company_contacts=min(x['visible_employees'] for x in summary),maximum_company_contacts=max(x['visible_employees'] for x in summary),minimum100_met=all(x['visible_employees']>=100 for x in summary),source_only_company_employee_disjointness=True,truth_derived_denominators='sealed until evaluator after prediction freeze; formulas predeclared in PROTOCOL.json',cells=summary));print(json.dumps(read(out/'VISIBLE_DENOMINATORS_BEFORE_EVALUATION.json')|{'cells':'30 exact cell allocations saved'},indent=2))
if __name__=='__main__':main()
