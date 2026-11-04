"""Post-freeze scale metrics/error audit; no inference features or policy changes."""
from pathlib import Path
from collections import Counter
import json,hashlib
from experiments.product_recovery_v1_validation.audit_validation import intervals
R=Path('reports/product_recovery_v1_scale500');D=Path('data/product_recovery_v1_scale500');read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 if (R/'SCALE_GATE.json').exists():raise ValueError('Scale audit already completed')
 m=read(R/'evaluation_1/METRICS.json');ci=intervals(m['companies']);(R/'CLUSTER_INTERVALS.json').write_text(json.dumps(ci,indent=2)+'\n');v=m['views']['messy'];companies=sum(c['messy']['selected']>0 for c in m['companies']);m0=read('docs/v4/m0/EVALUATION_PROTOCOL.json');g=m0['publication_gates'];pointchecks={'proposal_precision':v['precision']>=g['precision'],'proposal_precision_cluster_lower':m['bootstrap']['messy']['precision_interval95'][0]>=g['minimum_company_bootstrap_lower_precision'],'proposal_coverage':v['coverage']>=g['minimum_employee_coverage_all_observed'],'proposal_edges':v['scorable_selected']>=g['minimum_published_edges'],'companies_with_proposals':companies>=g['minimum_publishing_companies'],'retrieval_at20':v['candidate_recall_at20']>=m0['retrieval']['minimum_any_true_manager_recall'],'structural_validity':v['structural_violations']==0,'calibrated_publication_policy':False,'targeted30percent_manager_removal_stress':'not executed; naturally absent contacts are not that stress test'}
 errors=[];labels=read(R/'evaluation_1/LABELLED_DECISIONS.json');wrong={(x['case'],x['variant'],x['employee_id']):x for x in labels if x['correct'] is False}
 for case in sorted((D/'source_inputs').glob('company_*')):
  truth=None
  for variant in ['clean','messy']:
   selected=[row for (c,v,e),row in wrong.items() if c==case.name and v==variant]
   if not selected:continue
   view=read(case/f'{variant}.json');docs={d['source_id']:d for d in view['documents']};claims={c['claim_id']:c for c in read(R/'predictions_1'/case.name/f'{variant}_claims.json')};preds={p['employee_id']:p for p in read(R/'predictions_1'/case.name/f'{variant}_predictions.json')}
   if truth is None:truth=read(D/case.name/'technical_audit/truth.json')
   for label in selected:
    p=preds[label['employee_id']];cited=[claims[c] for c in p['evidence_claim_ids']];errors.append({'evaluation':label,'employee_name':p['employee_name'],'manager_id':p['manager_id'],'manager_name':p['manager_name'],'true_manager_ids':[e['counterpart_employee_id'] for e in truth['relationships'] if e['employee_id']==p['employee_id'] and e['relation_type']=='direct_people_management'],'cited_claims':cited,'provider_membership_cited':any(c['kind']=='membership' and docs[c['source_id']]['source_type']=='synthetic_contact_provider' for c in cited),'source_types':sorted({docs[c['source_id']]['source_type'] for c in cited}),'own_raw_documents':[d for d in view['documents'] if p['employee_name'] in d['text']]})
 (R/'ALL_WRONG_PREDICTIONS.json').write_text(json.dumps(errors,indent=2)+'\n');audit={'errors':len(errors),'provider_membership_errors':sum(e['provider_membership_cited'] for e in errors),'co_managed_wrong':sum(e['evaluation']['co_managed'] for e in errors),'all_true_managers_absent_wrong':sum(not e['evaluation']['manager_present'] for e in errors),'known_development_and_validation_errors_not_fixed':True};(R/'PROVIDER_ERROR_SUMMARY.json').write_text(json.dumps(audit,indent=2)+'\n')
 result={'interpretation':'scale-up evaluation only; prior30-company validation remains the independent company holdout','companies_with_messy_proposals':companies,'companies_with_clean_proposals':sum(c['clean']['selected']>0 for c in m['companies']),'m0_proposal_level_diagnostics':pointchecks,'actual_production_published_lines':0,'m0_publication_ready':False,'calibration':'not fitted, no per-edge calibrated probabilities','integration_recommendation':'NO-GO for drop-in v1 replacement/published reporting lines; consider a separately approved explicitly experimental UI only after schema/status/metrics changes','generation_or_deployment_approval_implied':False};(R/'SCALE_GATE.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));print(json.dumps(audit,indent=2))
if __name__=='__main__':main()
