"""Labels opened only after frozen outputs; never imported by predictor."""
from pathlib import Path
from collections import defaultdict,Counter
import json,hashlib,math,random,statistics
import networkx as nx

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def metrics(ct):
 d=dict(ct);s=ct['scorable_selected'];n=ct['employees'];eligible=ct['manager_visible']
 d.update(precision=ct['correct']/s if s else None,coverage=ct['selected']/n if n else None,wrong_manager_rate=ct['wrong']/s if s else None,false_assignment_rate=ct['wrong']/n if n else None,abstention_rate=ct['unresolved']/n if n else None,candidate_recall_at20=ct['candidate_hit20']/eligible if eligible else None,full_pool_recall=ct['candidate_hit']/eligible if eligible else None,candidate_edge_recall=ct['candidate_edge_hit']/ct['visible_true_edges'] if ct['visible_true_edges'] else None,true_edge_recovery=ct['correct']/ct['full_true_edges'] if ct['full_true_edges'] else None)
 return d

def percentile(values,p):
 if not values:return None
 values=sorted(values);x=(len(values)-1)*p;i=int(x);j=min(i+1,len(values)-1);return values[i]+(values[j]-values[i])*(x-i)
def bootstrap(companies,cfg):
 rng=random.Random(cfg['bootstrap_seed']);data={'clean':[],'messy':[]};paired=[]
 for _ in range(cfg['bootstrap_replicates']):
  chosen=[rng.randrange(len(companies)) for _ in companies];ps=[]
  for label in data:
   total=Counter()
   for i in chosen:total.update(companies[i]['counts'][label])
   value=metrics(total)['precision'];data[label].append(value);ps.append(value)
  paired.append(ps[1]-ps[0] if all(x is not None for x in ps) else None)
 return {**{label:{'precision_interval95':[percentile([v for v in vals if v is not None],.025),percentile([v for v in vals if v is not None],.975)],'undefined_replicates':sum(v is None for v in vals),'replicates':len(vals)} for label,vals in data.items()},'paired_messy_minus_clean_precision':{'interval95':[percentile([v for v in paired if v is not None],.025),percentile([v for v in paired if v is not None],.975)],'undefined_replicates':sum(v is None for v in paired)}}

def evaluate(source_root,prediction_root,truth_root,target):
 source=Path(source_root);pred=Path(prediction_root);truth=Path(truth_root);out=Path(target)
 if out.exists():raise ValueError('Refusing evaluation overwrite; no repeated tuning')
 freeze=read(pred/'PREDICTION_FREEZE.json');assert all(sha(pred/p)==h for p,h in freeze['files_sha256'].items());assert sha(source/'SOURCE_ONLY_MANIFEST.json')==freeze['source_manifest_sha256']
 code=Path(__file__).parent;assert all(sha(code/p)==h for p,h in freeze['code_sha256'].items());cfg=read(code/'config.json');setup=read(pred.parent/'PRE_PREDICTION_FREEZE.json');assert all(sha(p)==h for p,h in setup['code_and_protocol_sha256'].items())
 manifest=read(truth/'PRE_GENERATION_FREEZE.json');meta={f"company_{c['index']:02}":c for c in manifest['companies']};companies=[];labelled=[];cases=[]
 # First truth/metadata reader is here, after all output/code freeze checks.
 for folder in sorted(source.glob('company_*')):
  name=folder.name;info=meta[name];t=read(truth/name/'technical_audit/truth.json');targets=defaultdict(set)
  for e in t['relationships']:
   if e['relation_type']=='direct_people_management':targets[e['employee_id']].add(e['counterpart_employee_id'])
  contacts=read(folder/'contacts.json');visible={c['employee_id'] for c in contacts};company={'case':name,'archetype':info['archetype'],'disclosure':info['disclosure'],'counts':{}}
  for label in ['clean','messy']:
   predictions=read(pred/name/f'{label}_predictions.json');claims=read(pred/name/f'{label}_claims.json');view=read(folder/f'{label}.json');docs={d['source_id']:d for d in view['documents']};byclaim={c['claim_id']:c for c in claims};ct=Counter(employees=len(visible));seen=set();g=nx.DiGraph();reasons=Counter()
   for c in claims:assert docs[c['source_id']]['text'][c['span_start']:c['span_end']]==c['quote']
   for p in predictions:
    eid=p['employee_id'];mid=p['manager_id'];ct['structural_violations']+=int(eid not in visible or eid in seen or p['company_id']!=view['company_id'] or mid is not None and (mid not in visible or mid==eid));seen.add(eid)
    assert set(p['evidence_claim_ids'])<=set(byclaim)
    selected=mid is not None;ct['selected']+=selected;ct['unresolved']+=not selected;reasons.update(p['reasons']);known=t['evaluation_status'].get(eid)=='complete';true=targets[eid] if known else set();present=true&visible
    if selected:g.add_edge(eid,mid)
    correct=None
    if not known:
     ct['unknown_truth']+=1;ct['unknown_selected']+=selected
    else:
     ct['scorable_selected']+=selected;correct=mid in true if selected else None;ct['correct']+=correct is True;ct['wrong']+=correct is False;ct['full_true_edges']+=len(true);ct['roots']+=not true;ct['nonroots']+=bool(true);ct['visible_true_edges']+=len(present)
     cands={c['manager_id'] for c in p['candidates'] if c['manager_id'] is not None};hits=len(cands&present)
     if present:
      ct['manager_visible']+=1;ct['candidate_hit']+=bool(hits);ct['candidate_edge_hit']+=hits;n=len(cands);ct['candidate_hit20']+=float(bool(hits)) if n<=20 else 1-math.comb(n-hits,20)/math.comb(n,20) if n-hits>=20 else 1
     if true and not present:ct['all_managers_absent']+=1;ct['selected_when_all_absent']+=selected;ct['wrong_when_all_absent']+=selected
     if len(true)>1:
      ct['co_managed']+=1;ct['co_correct_partial']+=correct is True;ct['co_full_recovery']+=int(selected and {mid}==true);ct['co_wrong']+=correct is False;ct['co_unresolved']+=not selected
    row={'case':name,'variant':label,'employee_id':eid,'known_truth':known,'selected':selected,'correct':correct,'manager_present':bool(present) if known else None,'co_managed':len(true)>1 if known else None,'reasons':p['reasons']};labelled.append(row)
    if selected or len(cases)<12 or any(r in p['reasons'] for r in ['multiple_plausible_named_managers','named_manager_not_resolved_to_visible_contact']):cases.append({'case':name,'variant':label,'prediction':p,'evaluation':row,'cited_claims':[byclaim[x] for x in set(p['evidence_claim_ids']+[claim for c in p['candidates'] for claim in c['claim_ids']]) if x in byclaim]})
   ct['structural_violations']+=len(visible-seen)+int(not nx.is_directed_acyclic_graph(g));company['counts'][label]=dict(ct);company[label]=metrics(ct);company[label]['abstention_reasons']=dict(reasons)
  companies.append(company)
 result={'scope':'15 frozen already-inspected development companies; exploratory synthetic results, not independent confirmation','pipeline':cfg['version'],'companies':companies,'views':{},'groups':{},'bootstrap':bootstrap(companies,cfg),'calibration':'none; scores/probabilities null; experimental proposals not published','limitations':'No reserved outcomes or generator changes. No heldout source family/domain validation. Unknown labels excluded from correctness. At most one edge; true co-management full recovery usually impossible. Candidate lists unranked, recall@20 uses expected ties above20.'}
 for label in ['clean','messy']:
  total=Counter()
  for c in companies:total.update(c['counts'][label])
  result['views'][label]=metrics(total);precisions=[c[label]['precision'] for c in companies if c[label]['precision'] is not None];result['views'][label]['macro_company_precision']=statistics.mean(precisions) if precisions else None;result['views'][label]['undefined_company_precision']=len(companies)-len(precisions);coverages=[c[label]['coverage'] for c in companies];result['views'][label]['company_coverage']={'min':min(coverages),'median':statistics.median(coverages),'max':max(coverages)}
 for key in ['disclosure','archetype']:
  result['groups'][key]={}
  for group in sorted({c[key] for c in companies}):
   result['groups'][key][group]={}
   for label in ['clean','messy']:
    total=Counter()
    for c in companies:
     if c[key]==group:total.update(c['counts'][label])
    result['groups'][key][group][label]=metrics(total)
 out.mkdir(parents=True);(out/'METRICS.json').write_text(json.dumps(result,indent=2)+'\n');(out/'LABELLED_DECISIONS.json').write_text(json.dumps(labelled,indent=2)+'\n');(out/'INSPECTABLE_CASES.json').write_text(json.dumps(cases,indent=2)+'\n');(out/'EVALUATION_FREEZE.json').write_text(json.dumps({'prediction_freeze_sha256':sha(pred/'PREDICTION_FREEZE.json'),'metrics_sha256':sha(out/'METRICS.json'),'single_pass':True},indent=2)+'\n');print(json.dumps(result['views'],indent=2))
if __name__=='__main__':
 import sys
 evaluate(*sys.argv[1:])
