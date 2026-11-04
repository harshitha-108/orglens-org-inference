"""Distinct structures and dated facts, committed before current reporting choices."""
from collections import defaultdict,Counter
from datetime import timedelta
from experiments.v4_m24_history import foundation as temporal
from experiments.v4_m24_history.foundation import FrozenLedger,dt,interval,contains,active,snapshot,INF,DIRECT,PROJECT,FUNCTIONAL,MATRIX
from .common import config,compatible,canonical,digest,rng,opaque
STRUCTURES={
 'product':('functional_departments',['Customer delivery','Platform operations'],['Department Head']*2),
 'regional_services':('regional_practices',['UK practice','ANZ practice','Regional accounts'],['Practice Director']*3),
 'multi_site':('plant_and_shifts',['Plant operations','Day shift','Evening shift'],['Plant Manager','Shift Supervisor','Shift Supervisor']),
 'regulated':('service_and_assurance',['Service operations','Assurance office'],['Operations Director','Compliance Officer']),
 'clinical':('service_lines',['Ambulatory services','Diagnostics services','Patient access','Community services'],['Service Line Manager']*4)}
def iso(d):return d.isoformat(timespec='seconds').replace('+00:00','Z')
def build_facts(archetype='product',index=0,c=None):
 c=c or config();base=dict(c,facts_version='orglens-v4-organisation-facts.2');f=temporal.build_facts(archetype,index,base).read();f['schema_version']=c['facts_version'];f['structure'],labels,titles=STRUCTURES[archetype];org=rng(c,index,'organisation','m25-history');lead=f['units'][0];head=f['head_position'];root=f['root_position'];recorded='2026-10-20T00:00:00Z';newunits=[];newheads=[]
 def role(label,title,parent=None):
  k=len(newheads);uid=opaque(c,index,'m25-unit',k);pid=opaque(c,index,'m25-position',k);eid=opaque(c,index,'m25-person',k);start=['2023-04-01T00:00:00Z','2024-02-01T00:00:00Z','2024-08-01T00:00:00Z'][k%3]
  f['units'].append(dict(unit_id=uid,name=label,function='Leadership',purpose=label.lower()+' planning and service delivery',product=lead['product'],region='UK' if k%2==0 else 'Australia and New Zealand',valid_from=start,valid_to=None,recorded_at=recorded))
  f['positions'].append(dict(position_id=pid,company_id=f['company_id'],title=title,valid_from=start,valid_to=None,recorded_at=recorded));f['occupancy'].append(dict(position_id=pid,employee_id=eid,display_name=['Avery Reed','Riley Khan','Robin Brooks','Drew Mason'][k],name_order=0,valid_from=start,valid_to=None,recorded_at=recorded))
  f['memberships'].append(dict(position_id=pid,unit_id=lead['unit_id'] if parent is None else parent,kind='leadership_staff',valid_from='2025-01-01T00:00:00Z',valid_to=None,recorded_at=recorded))
  f['mandates'].append(dict(position_id=pid,unit_id=uid,authority='functional' if archetype=='regulated' and k==1 else 'people',extent='leadership_staff',exclude=[],valid_from='2025-01-01T00:00:00Z',valid_to=None,recorded_at=recorded));newheads.append(pid);newunits.append(uid)
 for j,(label,title) in enumerate(zip(labels,titles)):role(label,title,newunits[0] if archetype=='multi_site' and j else None)
 # Give service managers explicit line-staff affiliation under the relevant hierarchy.
 bosses=list(dict.fromkeys(b for p in f['policies'] for b in p['admissible_managers']))
 for j,boss in enumerate(bosses):
  m=next(m for m in f['memberships'] if m['position_id']==boss and m['kind']=='leadership_staff');m['unit_id']=newunits[(1+j%2) if archetype=='multi_site' else 0 if archetype=='regulated' else j%len(newunits)]
 # Independent assurance: professional control is not a second direct line manager.
 if archetype=='regulated':
  owner=newheads[1]
  for p in f['policies']:f['mandates'].append(dict(position_id=owner,unit_id=p['unit_id'],authority='functional',extent='all',exclude=[],valid_from='2025-01-01T00:00:00Z',valid_to=None,recorded_at=recorded))
 # Varied pre-existing lifetimes, always before the genuine old responsibility begins.
 for j,row in enumerate(f['units']+f['positions']):
  row['valid_from']=['2023-01-01T00:00:00Z','2024-01-01T00:00:00Z','2024-09-01T00:00:00Z'][j%3]
 for o in f['occupancy']:
  p=next(p for p in f['positions'] if p['position_id']==o['position_id']);o['valid_from']=max(p['valid_from'],o['valid_from'])
 # Transfer follows an operational reassignment, never a selected-parent lookup.
 first=f['policies'][0];last=f['policies'][-1];worker=first['workers'][-1];change='2026-09-01T00:00:00Z';m=next(m for m in f['memberships'] if m['position_id']==worker and m['kind']=='substantive');m['valid_to']=change;f['memberships'].append(dict(m,unit_id=last['unit_id'],valid_from=change,valid_to=None));first['workers'].remove(worker);last['workers'].append(worker)
 # Position succession: former holder remains in history, new holder joins after handover.
 boss=first['admissible_managers'][0];old=next(o for o in f['occupancy'] if o['position_id']==boss);old['valid_to']='2026-08-15T00:00:00Z';f['occupancy'].append(dict(old,employee_id=opaque(c,index,'succession-person',0),display_name='Elena Brooks',valid_from=old['valid_to'],valid_to=None))
 # A genuinely vacant spell covered by an acting position; joint mandate is retained.
 joint=next(p for p in f['policies'] if p['mode']=='joint');jb=joint['admissible_managers'][0];o=next(o for o in f['occupancy'] if o['position_id']==jb);o['valid_to']='2026-06-01T00:00:00Z';f['occupancy'].append(dict(o,valid_from='2026-07-15T00:00:00Z',valid_to=None))
 acting=f['vacant_positions'][0];f['occupancy'].append(dict(position_id=acting,employee_id=opaque(c,index,'acting-person',0),display_name='Casey Nolan',name_order=0,valid_from='2026-07-01T00:00:00Z',valid_to='2026-07-15T00:00:00Z',recorded_at=recorded));f['mandates'].append(dict(position_id=acting,unit_id=joint['unit_id'],authority='people',extent='joint',exclude=[],valid_from='2026-07-01T00:00:00Z',valid_to='2026-07-15T00:00:00Z',recorded_at=recorded))
 # Real unit closure, preserved rather than removed from source history.
 uid=opaque(c,index,'closed-unit',0);pid=opaque(c,index,'closed-position',0);end='2026-03-31T00:00:00Z';f['units'].append(dict(unit_id=uid,name='Legacy service desk',function='Operations',purpose='legacy enquiries',product=lead['product'],region='UK',valid_from='2024-01-01T00:00:00Z',valid_to=end,recorded_at=recorded));f['positions'].append(dict(position_id=pid,company_id=f['company_id'],title='Service Associate',valid_from='2024-01-01T00:00:00Z',valid_to=end,recorded_at=recorded));f['occupancy'].append(dict(position_id=pid,employee_id=opaque(c,index,'former-person',0),display_name='Alex Bennett',name_order=0,valid_from='2024-02-01T00:00:00Z',valid_to=end,recorded_at=recorded));f['memberships'].append(dict(position_id=pid,unit_id=uid,kind='substantive',valid_from='2024-02-01T00:00:00Z',valid_to=end,recorded_at=recorded))
 # Scope/name histories and aliases are established before residual edge selection.
 role_titles={
  'product':('Support Specialist','Client Services Manager','Technical Standards Lead'),
  'regional_services':('Recruitment Coordinator','Practice Manager','Professional Practice Lead'),
  'multi_site':('Process Operator','Production Supervisor','Quality Standards Lead'),
  'regulated':('Account Service Associate','Service Operations Manager','Risk Standards Lead'),
  'clinical':('Patient Service Officer','Patient Services Manager','Clinical Practice Lead')}
 worker_title,manager_title,standards_title=role_titles[archetype]
 for position in f['positions']:
  position['title']={'Service Specialist':worker_title,'Service Manager':manager_title,'Professional Standards Lead':standards_title}.get(position['title'],position['title'])
 f['unit_versions']=[];f['position_versions']=[]
 for j,u in enumerate(f['units']):
  aliases=['Service desk','Delivery team'] if j%2==0 else ['Delivery team','Operations team'];v=dict(unit_id=u['unit_id'],name=u['name'],purpose=u['purpose'],product=u['product'],region=u['region'],aliases=aliases,valid_from=u['valid_from'],valid_to=u['valid_to'],recorded_at=recorded)
  if u['unit_id']==last['unit_id']:
   v['valid_to']='2026-09-15T00:00:00Z';f['unit_versions'].append(v);v=dict(v,name={'product':'Partner experience','regional_services':'Contractor support','multi_site':'Distribution services','regulated':'Settlement services','clinical':'Patient access'}[archetype],purpose='regional case resolution',valid_from=v['valid_to'],valid_to=None);u['name']=v['name'];u['purpose']=v['purpose']
  f['unit_versions'].append(v)
 for p in f['positions']:
  v=dict(position_id=p['position_id'],title=p['title'],valid_from=p['valid_from'],valid_to=p['valid_to'],recorded_at=recorded)
  if p['position_id']==worker:
   v['valid_to']=change;f['position_versions'].append(v);title={'product':'Platform Specialist','regional_services':'Recruitment Consultant','multi_site':'Process Technician','regulated':'Account Operations Analyst','clinical':'Service Coordinator'}[archetype];v=dict(v,title=title,valid_from=change,valid_to=None);p['title']=title
  f['position_versions'].append(v)
 # Research capture is independent of effect and publisher clocks.
 for table in ['units','positions','memberships','mandates','occupancy']:
  for row in f[table]:row['recorded_at']=min(f['as_of'],iso(dt(row['valid_from'])+timedelta(days=org.choice([10,40,100]))))
 f['history_events']=[{'kind':'transfer','effective_at':change},{'kind':'succession','effective_at':'2026-08-15T00:00:00Z'},{'kind':'acting_cover','effective_at':'2026-07-01T00:00:00Z'},{'kind':'closure','effective_at':end},{'kind':'unit_revision','effective_at':'2026-09-15T00:00:00Z'}]
 return commit(f)

def validate_facts(f):
 if f.get('schema_version')!='orglens-v4-organisation-facts.3':raise ValueError('M2.5A facts version required')
 temporal.validate_facts(dict(f,schema_version='orglens-v4-organisation-facts.2'))
 for table,key,base in [('unit_versions','unit_id','units'),('position_versions','position_id','positions')]:
  parent={r[key]:r for r in f[base]};groups=defaultdict(list)
  for v in f[table]:
   if v[key] not in parent or not contains(parent[v[key]],v):raise ValueError('History outside entity lifetime')
   if dt(v['recorded_at'])>dt(f['as_of']):raise ValueError('Future history capture')
   groups[v[key]].append(v)
  for k,p in parent.items():
   rows=sorted(groups[k],key=lambda x:x['valid_from'])
   if not rows or rows[0]['valid_from']!=p['valid_from'] or rows[-1]['valid_to']!=p['valid_to'] or any(a['valid_to']!=b['valid_from'] for a,b in zip(rows,rows[1:])):raise ValueError('History must cover entity without gaps/overlap')
 return True

def commit(f):validate_facts(f);return FrozenLedger(canonical(f),digest(f))

def select_truth(ledger,c=None,residual_salt=0):
 f=ledger.read();validate_facts(f);c=c or config();s=snapshot(f);occ={o['position_id']:o for o in s['occupancy']};edges=[];residual={};assignments={}
 for p in f['policies']:
  if p['mode']=='shared':
   workers=list(p['workers']);rng(c,f['index'],'residual_relationship_choice',str(residual_salt)+'|'+p['unit_id']).shuffle(workers)
   for j,w in enumerate(workers):assignments[w]=p['admissible_managers'][j%len(p['admissible_managers'])]
 for pid,o in occ.items():
  membership=[m for m in s['memberships'] if m['position_id']==pid and m['kind'] in ('substantive','leadership_staff')];candidates=[]
  for m in s['mandates']:
   if m['authority']!='people' or m['position_id']==pid or m['position_id'] not in occ or pid in m['exclude'] or m['extent']=='subset' and pid not in m['include']:continue
   matching=[x for x in membership if x['unit_id']==m['unit_id'] and (x['kind']=='leadership_staff' if m['extent']=='leadership_staff' else x['kind']=='substantive')]
   if matching:candidates.append(m)
  if pid in assignments:
   chosen=[m for m in candidates if m['position_id']==assignments[pid]];residual[o['employee_id']]=[occ[m['position_id']]['employee_id'] for m in candidates]
  else:chosen=[m for m in candidates if m['extent']=='joint'] or candidates
  for m in chosen:edges.append(edge(f,o,occ[m['position_id']],DIRECT))
  for m in s['mandates']:
   if m['authority']!='people' and m['position_id'] in occ and m['position_id']!=pid and any(x['unit_id']==m['unit_id'] for x in membership):edges.append(edge(f,o,occ[m['position_id']],{'project':PROJECT,'functional':FUNCTIONAL,'matrix':MATRIX}[m['authority']]))
 unique={ (e['employee_id'],e['counterpart_employee_id'],e['relation_type']):e for e in edges};t={'schema_version':'orglens-v4-m25a-truth.1','facts_sha256':ledger.sha256,'relationships':list(unique.values()),'free_parent_choices':residual,'evaluation_status':{o['employee_id']:('unknown' if p in f['evaluation_unknown_positions'] else 'complete') for p,o in occ.items()}}
 validate_truth(f,t);return t

def edge(f,a,b,kind):return dict(company_id=f['company_id'],employee_id=a['employee_id'],counterpart_employee_id=b['employee_id'],relation_type=kind,valid_from=max(f['as_of'],a['valid_from'],b['valid_from']),valid_to=None)
def validate_truth(f,t):
 # Reuse M2.4 temporal/typed authority validation; the snapshot graph's start is as-of.
 temporal.validate_truth(f,t);return True
