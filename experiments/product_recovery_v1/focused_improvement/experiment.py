"""Fixed fresh cohorts. Generation and isolated prediction precede a separate scorer."""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from collections import Counter,defaultdict
import hashlib,json,subprocess,sys
import networkx as nx
from experiments.product_recovery_v1.foundation import build,project,reporting_truth,old
from experiments.product_recovery_v1.publication import publish
from experiments.product_recovery_v1.inference.contracts import validate_inputs
from experiments.product_recovery_v1.inference.evaluate import metrics,bootstrap
from .publication import staff_projection,supplement

HERE=Path(__file__).resolve().parent
BASE=Path('experiments/product_recovery_v1')
CFG=json.loads((HERE/'config.json').read_text(encoding='utf-8-sig'))
BASECFG=json.loads((BASE/'config.json').read_text())
ROOT=Path('reports/recovery_focused_improvement_20261105')
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,value):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8') as f:json.dump(value,f,indent=2);f.write('\n')

def cells(phase):
 seed=CFG[phase+'_seed'];out=[]
 for ai,a in enumerate(BASECFG['archetypes']):
  for j in range(100 if phase=='scale' else 6 if phase=='validation' else 3):
   ri=(j+ai)%3
   out.append(dict(index=len(out),generator_index=3*ai+ri,seed=seed+len(out),archetype=a,disclosure=BASECFG['regimes'][ri],target_employees=BASECFG['target_employees'][ri]))
 return out

def generate(cell):
 seed=cell['seed'];regime=cell['disclosure']
 ledger,c=build(cell['archetype'],cell['generator_index'],seed,cell['target_employees'])
 public,_=project(ledger)
 clean,messy,contacts=publish(public,BASECFG,seed,regime)
 records=staff_projection(ledger)
 enriched=[supplement(clean,records,CFG,seed,regime,messy=False),supplement(messy,records,CFG,seed,regime,messy=True)]
 for view in [clean,messy,*enriched]:validate_inputs(view,contacts)
 truth=reporting_truth(ledger,c)
 assert old.validate_truth(ledger.read(),truth)
 return cell,contacts,[clean,messy],enriched,truth

def run(phase):
 run=ROOT/phase
 if run.exists():raise ValueError('Refusing to overwrite a scientific run')
 if phase=='validation':assert read(ROOT/'development/GATE.json')['pass']
 if phase=='scale':assert read(ROOT/'validation/GATE.json')['pass']
 cohort=cells(phase)
 code={p.as_posix():sha(p) for p in HERE.glob('*') if p.suffix in {'.py','.json'}}
 manifest={'phase':phase,'companies':cohort,'code_sha256':code,'settings':CFG,'baseline_protocol_hash':sha(BASE/'config.json'),'truth_boundary':'Separate child predictor process with enforced source-only read audit'}
 write(run/'FREEZE.json',manifest)
 if phase=='scale':assert manifest['code_sha256']==read(ROOT/'validation/FREEZE.json')['code_sha256']
 if phase=='validation':assert manifest['code_sha256']==read(ROOT/'development/FREEZE.json')['code_sha256']
 arms=['baseline','focused'] if phase!='scale' else ['focused']
 ids=set()
 with ProcessPoolExecutor(max_workers=3) as pool:
  for cell,contacts,original,enriched,truth in pool.map(generate,cohort):
   case=f'company_{cell["index"]:03}'
   cid=original[0]['company_id'];assert cid not in ids;ids.add(cid)
   for arm in arms:
    folder=run/arm/'source_inputs'/case
    write(folder/'contacts.json',contacts)
    for variant,view in zip(('clean','messy'),original if arm=='baseline' else enriched):write(folder/(variant+'.json'),view)
   write(run/'private_truth'/(case+'.json'),truth)
   if (cell['index']+1)%25==0:print('Generated',cell['index']+1,'of',len(cohort),flush=True)
 for arm in arms:
  src=run/arm/'source_inputs'
  write(src/'SOURCE_ONLY_MANIFEST.json',{'files_sha256':{p.relative_to(src).as_posix():sha(p) for p in src.rglob('*.json')},'phase':phase,'arm':arm})
  module='experiments.product_recovery_v1.'+('inference.run_predict' if arm=='baseline' else 'focused_improvement.run_predict')
  subprocess.run([sys.executable,'-B','-m',module,str(src),str(run/arm/'predictions'),str(run/'private_truth/company_000.json')],check=True)
 print('Both prediction phases frozen' if len(arms)==2 else 'Scale predictions frozen',flush=True)

def score(phase):
 run=ROOT/phase;setup=read(run/'FREEZE.json')
 assert all(sha(p)==h for p,h in setup['code_sha256'].items())
 arms=['baseline','focused'] if phase!='scale' else ['focused']
 # Verify every predictor output and input before the evaluator opens labels.
 for arm in arms:
  source=run/arm/'source_inputs';p=run/arm/'predictions';f=read(p/'PREDICTION_FREEZE.json')
  assert f['truth_used'] is False and f['source_manifest_sha256']==sha(source/'SOURCE_ONLY_MANIFEST.json')
  assert all(sha(p/k)==h for k,h in f['files_sha256'].items())
  assert all(sha(source/k)==h for k,h in read(source/'SOURCE_ONLY_MANIFEST.json')['files_sha256'].items())
  access=read(p/'INPUT_ACCESS.json');assert access['denied_probes'] and not any('private_truth' in x for x in access['successful_reads'])
 result={}
 for arm in arms:
  rows=[]
  for cell in setup['companies']:
   case=f'company_{cell["index"]:03}';src=run/arm/'source_inputs'/case;pred=run/arm/'predictions'/case
   visible={c['employee_id'] for c in read(src/'contacts.json')}
   truth=read(run/'private_truth'/(case+'.json'));actual=defaultdict(set)
   for e in truth['relationships']:
    if e['relation_type']=='direct_people_management':actual[e['employee_id']].add(e['counterpart_employee_id'])
   row={'case':case,'archetype':cell['archetype'],'disclosure':cell['disclosure'],'counts':{}}
   for variant in ('clean','messy'):
    ct=Counter(employees=len(visible));p=read(pred/(variant+'_predictions.json'));claims=read(pred/(variant+'_claims.json'));docs={d['source_id']:d for d in read(src/(variant+'.json'))['documents']}
    assert all(docs[c['source_id']]['text'][c['span_start']:c['span_end']]==c['quote'] for c in claims)
    claim_ids={c['claim_id'] for c in claims};selected={x['employee_id']:x['manager_id'] for x in p if x['manager_id']};known_correct={}
    graph=nx.DiGraph(selected.items())
    ct['structural_violations']=int(not nx.is_directed_acyclic_graph(graph))+int(len(p)!=len(visible) or {x['employee_id'] for x in p}!=visible)
    for x in p:
     eid=x['employee_id'];mid=x['manager_id'];ct['selected']+=mid is not None;ct['unresolved']+=mid is None
     ct['structural_violations']+=int(bool(mid) and (mid not in visible or mid==eid))
     assert set(x['evidence_claim_ids'])<=claim_ids
     if mid:assert x['evidence_claim_ids'] and x['calibrated_estimate'] is None
     if truth['evaluation_status'].get(eid)!='complete':
      ct['unknown_truth']+=1;ct['unknown_selected']+=mid is not None;continue
     parents=actual[eid];present=parents&visible
     ct['full_true_edges']+=len(parents);ct['visible_true_edges']+=len(present)
     ct['all_managers_absent']+=bool(parents and not present)
     ct['wrong_when_all_absent']+=bool(mid and parents and not present)
     ct['scorable_selected']+=mid is not None
     if mid:
      ct['correct']+=mid in parents;ct['wrong']+=mid not in parents
      if mid in parents:known_correct[eid]=mid
     if present:
      candidates={c['manager_id'] for c in x['candidates'] if c['manager_id']}
      hits=len(candidates&present);ct['manager_visible']+=1;ct['candidate_hit']+=bool(hits);ct['candidate_edge_hit']+=hits
      import math
      n=len(candidates);ct['candidate_hit20']+=float(bool(hits)) if n<=20 else 1-math.comb(n-hits,20)/math.comb(n,20) if n-hits>=20 else 1
    ct['correct_two_hop']=sum(mid in known_correct for mid in known_correct.values())
    ct['available_two_hop_employees']=sum(any(truth['evaluation_status'].get(mid)=='complete' and bool(actual[mid]&visible) for mid in actual[eid]&visible) for eid in visible if truth['evaluation_status'].get(eid)=='complete')
    row['counts'][variant]=dict(ct)
   rows.append(row)
  totals={v:sum((Counter(c['counts'][v]) for c in rows),Counter()) for v in ('clean','messy')}
  # Counter addition omits zeros, which remain explicit in the metric output.
  required=('selected scorable_selected employees manager_visible correct wrong unresolved wrong_when_all_absent all_managers_absent candidate_hit20 candidate_hit candidate_edge_hit visible_true_edges full_true_edges structural_violations correct_two_hop available_two_hop_employees unknown_selected').split()
  for v in totals:
   for key in required:totals[v].setdefault(key,0)
  result[arm]={'views':{v:metrics(totals[v]) for v in totals},'bootstrap':bootstrap(rows,CFG),'companies':rows,'minimum_company_contacts':min(c['counts']['messy']['employees'] for c in rows)}
 write(run/'METRICS.json',result)
 focused=result['focused']['views']['messy'];ref=result.get('baseline',{}).get('views',{}).get('messy',{'coverage':.1207,'full_pool_recall':.3192,'correct_two_hop':0})
 gate=CFG['gate'];checks={
  'precision':(focused['precision'] or 0)>=gate['minimum_precision'],
  'interval':(result['focused']['bootstrap']['messy']['precision_interval95'][0] or 0)>=gate['minimum_precision_interval_lower'],
  'coverage':focused['coverage']>=max(gate['minimum_coverage'],ref['coverage']+gate['minimum_paired_coverage_gain']),
  'recall':focused['full_pool_recall']>=ref['full_pool_recall']+gate['minimum_paired_recall_gain'],
  'chains':focused['correct_two_hop']>=max(gate['minimum_correct_two_hop'],ref['correct_two_hop']+1),
  'manager_absence':focused['wrong_when_all_absent']/max(1,focused['all_managers_absent'])<=gate['maximum_absent_false_assignment_rate'],
  'structure':focused['structural_violations']==0,
  'roster':result['focused']['minimum_company_contacts']>=100,
 }
 write(run/'GATE.json',{'phase':phase,'checks':checks,'pass':all(checks.values()),'baseline_comparison':'paired same companies' if phase!='scale' else 'frozen earlier scale-up, different companies'})
 print(json.dumps({'views':{k:v['views']['messy'] for k,v in result.items()},'gate':checks},indent=2))

if __name__=='__main__':
 command,phase=sys.argv[1:]
 assert phase in ('development','validation','scale')
 {'run':run,'score':score}[command](phase)
