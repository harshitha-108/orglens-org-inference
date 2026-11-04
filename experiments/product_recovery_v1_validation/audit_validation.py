"""Retrospective validation audit, frozen before generation; never imported by predictor."""
from pathlib import Path
from collections import Counter
import json,random,hashlib
from experiments.product_recovery_v1.inference.evaluate import percentile
R=Path('reports/product_recovery_v1_validation');D=Path('data/product_recovery_v1_validation');read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def intervals(companies):
 rng=random.Random(4062502);values={v:{k:[] for k in ['precision','coverage','abstention','candidate_recall','wrong_manager_rate','absent_false_assignments']} for v in ['clean','messy']}
 for _ in range(2000):
  chosen=[rng.randrange(len(companies)) for _ in companies]
  for v in values:
   ct=Counter()
   for i in chosen:ct.update(companies[i]['counts'][v])
   rates={'precision':(ct['correct'],ct['scorable_selected']),'coverage':(ct['selected'],ct['employees']),'abstention':(ct['unresolved'],ct['employees']),'candidate_recall':(ct['candidate_hit'],ct['manager_visible']),'wrong_manager_rate':(ct['wrong'],ct['scorable_selected']),'absent_false_assignments':(ct['wrong_when_all_absent'],ct['all_managers_absent'])}
   for k,(num,den) in rates.items():values[v][k].append(num/den if den else None)
 return {v:{k:{'interval95':[percentile([x for x in vals if x is not None],.025),percentile([x for x in vals if x is not None],.975)],'undefined_replicates':sum(x is None for x in vals),'replicates':2000} for k,vals in ks.items()} for v,ks in values.items()}

def main():
 if (R/'VALIDATION_GATE.json').exists():raise ValueError('Already audited; no re-selection')
 m=read(R/'evaluation_1/METRICS.json');protocol=read('experiments/product_recovery_v1_validation/PROTOCOL.json');p=protocol['feasibility_gates'];v=m['views']['messy'];ncompanies=sum(c['messy']['selected']>0 for c in m['companies']);visible=read(R/'VISIBLE_DENOMINATORS_BEFORE_EVALUATION.json');rate=v['wrong_when_all_absent']/v['all_managers_absent'] if v['all_managers_absent'] else None
 checks={'precision':v['precision'] is not None and v['precision']>=p['messy_precision'],'coverage':v['coverage']>=p['messy_coverage'],'selected_edges':v['scorable_selected']>=p['minimum_selected_edges'],'companies':ncompanies>=p['minimum_companies_with_proposals'],'structural_validity':v['structural_violations']==p['structural_violations'],'absent_manager_false_assignments':rate is not None and rate<=p['maximum_all_managers_absent_false_assignments'],'minimum100_contacts':visible['minimum100_met']}
 ci=intervals(m['companies']);(R/'CLUSTER_INTERVALS.json').write_text(json.dumps(ci,indent=2)+'\n')
 m0=read('docs/v4/m0/EVALUATION_PROTOCOL.json');g=m0['publication_gates'];lower=m['bootstrap']['messy']['precision_interval95'][0];strict={'retrieval_at_least95':v['candidate_recall_at20']>=m0['retrieval']['minimum_any_true_manager_recall'],'precision_at_least90':v['precision'] is not None and v['precision']>=g['precision'],'lower_precision_at_least90':lower is not None and lower>=g['minimum_company_bootstrap_lower_precision'],'coverage_at_least15':v['coverage']>=g['minimum_employee_coverage_all_observed'],'at_least500_edges':v['scorable_selected']>=g['minimum_published_edges'],'at_least30_publishing_companies':ncompanies>=g['minimum_publishing_companies'],'zero_structural_violations':v['structural_violations']==0,'calibration_gate':False,'targeted_30percent_removal_stress_gate':'not executed; natural manager absence is not a substitute'}
 result={'decision':'GO to consider500-company generation only' if all(checks.values()) else 'NO-GO; retain existing submission','feasibility_checks':checks,'messy_companies_with_proposals':ncompanies,'clean_companies_with_proposals':sum(c['clean']['selected']>0 for c in m['companies']),'m0_stricter_requirements':strict,'m0_publication_ready':False,'calibrated_confidence_available':False,'integration_or_generation_authorised':False};(R/'VALIDATION_GATE.json').write_text(json.dumps(result,indent=2)+'\n')
 labels=read(R/'evaluation_1/LABELLED_DECISIONS.json');evidence=read(R/'SOURCE_EVIDENCE.json');lookup={(e['case'],e['variant'],e['employee_id']):e for e in evidence};errors=[]
 for row in labels:
  if row['correct'] is not False:continue
  e=lookup[row['case'],row['variant'],row['employee_id']];view=read(D/'source_inputs'/row['case']/f"{row['variant']}.json");docs={d['source_id']:d for d in view['documents']};truth=read(D/row['case']/'technical_audit/truth.json');true=[t['counterpart_employee_id'] for t in truth['relationships'] if t['employee_id']==row['employee_id'] and t['relation_type']=='direct_people_management'];errors.append({'evaluation':row,'proposal':e,'true_manager_ids':true,'source_types':sorted({docs[c['source_id']]['source_type'] for c in e['claims']}),'own_raw_source_documents':[d for d in view['documents'] if e['employee_name'] in d['text']]})
 (R/'ALL_WRONG_PREDICTIONS.json').write_text(json.dumps(errors,indent=2)+'\n');print(json.dumps(result,indent=2));print('Wrong predictions',len(errors),'provider-linked',sum('synthetic_contact_provider' in e['source_types'] for e in errors))
if __name__=='__main__':main()
