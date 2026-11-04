"""Versioned extension of committed temporal facts; no source or outcome feedback."""
from copy import deepcopy
import hashlib
from experiments.v4_m25a import foundation as old
from experiments.v4_m25a.common import config as original_config
from experiments.v4_m25a.projection import project

def identity(*x):return hashlib.sha256(repr(x).encode()).hexdigest()[:32]
def build(archetype,index,seed,target):
 c=original_config();c['seed']=seed
 f=old.build_facts(archetype,index,c).read();departments=[u for u in f['units'] if u['function']=='Leadership' and any(m['unit_id']==u['unit_id'] and m['authority']=='people' and m['extent']=='leadership_staff' for m in f['mandates'])];policies={p['mode']:deepcopy(p) for p in f['policies']};positions={p['position_id']:p for p in f['positions']};units={u['unit_id']:u for u in f['units']};current=old.snapshot(f);occupants={o['position_id']:o for o in current['occupancy']};members={m['position_id']:m for m in current['memberships'] if m['kind']=='substantive'}
 for j,u in enumerate(f['units']):
  if u['function']!='Leadership' and u['name']!='Leadership office':u['parent_unit_id']=departments[j%len(departments)]['unit_id']
 first=['Nora','Ethan','Zoe','Hugo','Iris','Felix','Mila','Oscar','Lena','Theo','Esme','Jasper','Freya','Amir','Clara','Adam','Vera','Isaac','Ruby','Finn'];last=['Bennett','Walsh','Grant','Hughes','Wells','Cooper','Foster','Reed','Murray','Scott','West','Cole','Hayes','Wright','Lewis','Turner','Bell','Clark','Ward','James'];serial=0
 def clone_role(template,unit,kind):
  nonlocal serial
  serial+=1;pid=identity(seed,index,'position',serial);eid=identity(seed,index,'employee',serial);base=deepcopy(positions[template]);base['position_id']=pid;f['positions'].append(base)
  occ=deepcopy(occupants[template]);occ.update(position_id=pid,employee_id=eid,display_name=first[(serial-1)%20]+' '+last[((serial-1)//20)%20]);f['occupancy'].append(occ)
  for v in list(f['position_versions']):
   if v['position_id']==template:f['position_versions'].append(dict(v,position_id=pid))
  template_membership=next(m for m in current['memberships'] if m['position_id']==template);m=deepcopy(template_membership);m.update(position_id=pid,unit_id=unit,kind=kind);f['memberships'].append(m);return pid
 groups={};group_sizes={}
 def department_group(parent):
  if parent['unit_id'] in groups and group_sizes[groups[parent['unit_id']]]<8:return groups[parent['unit_id']]
  gi=len(group_sizes);uid=identity(seed,index,'area-unit',gi);unit=deepcopy(parent);unit.update(unit_id=uid,name=['Northern','Southern','Central','Western','Eastern','International','Commercial','Specialist'][gi%8]+' service leadership',parent_unit_id=parent['unit_id']);f['units'].append(unit)
  f['unit_versions'].append(dict(unit_id=uid,name=unit['name'],purpose=unit['purpose'],product=unit['product'],region=unit['region'],aliases=[],valid_from=unit['valid_from'],valid_to=unit['valid_to'],recorded_at=unit['recorded_at']))
  boss=clone_role(f['head_position'],parent['unit_id'],'leadership_staff')
  next(p for p in f['positions'] if p['position_id']==boss)['title']='Area Operations Manager'
  for v in f['position_versions']:
   if v['position_id']==boss:v['title']='Area Operations Manager'
  f['mandates'].append(dict(position_id=boss,unit_id=uid,authority='people',extent='leadership_staff',exclude=[],valid_from='2025-01-01T00:00:00Z',valid_to=None,recorded_at='2026-10-20T00:00:00Z'));groups[parent['unit_id']]=uid;group_sizes[uid]=0;return uid
 modes=['unique','unique','shared','unique','joint','exception','unique'];qualifiers=['Digital','Enterprise','Regional','Customer','Partner','Specialist','Commercial','Service','Operations','Central','Client','Field','Product','Business','Technical','Local','International','Strategic','Community','Platform'];j=0
 while len([o for o in f['occupancy'] if old.active(o,f['as_of'])])<target:
  mode=modes[j%len(modes)];template=policies[mode];uid=identity(seed,index,'unit',j);u=deepcopy(units[template['unit_id']]);u.update(unit_id=uid,name=qualifiers[j%len(qualifiers)]+' '+units[template['unit_id']]['name'].lower(),parent_unit_id=departments[j%len(departments)]['unit_id']);f['units'].append(u)
  f['unit_versions'].append(dict(unit_id=uid,name=u['name'],purpose=u['purpose'],product=u['product'],region=u['region'],aliases=['Service desk' if j%2 else 'Delivery team'],valid_from=u['valid_from'],valid_to=u['valid_to'],recorded_at=u['recorded_at']))
  bosses=[]
  for b in template['admissible_managers']:
   parent=departments[j%len(departments)];area=department_group(parent);u['parent_unit_id']=area;boss=clone_role(b,area,'leadership_staff');bosses.append(boss);group_sizes[area]+=1
  worker_template=next(w for w in template['workers'] if w in members and w not in template['exceptions']);count={'unique':8,'shared':10,'joint':6,'exception':7}[mode];workers=[clone_role(worker_template,uid,'substantive') for _ in range(count)];exceptions=[workers[-1]] if mode=='exception' else []
  for boss in bosses:
   mandate=next(m for m in current['mandates'] if m['position_id'] in template['admissible_managers'] and m['unit_id']==template['unit_id'] and m['authority']=='people');f['mandates'].append(dict(mandate,position_id=boss,unit_id=uid,exclude=exceptions))
  if exceptions:
   m=next(m for m in current['mandates'] if m['unit_id']==template['unit_id'] and m['authority']=='people' and m['extent']=='subset');f['mandates'].append(dict(m,unit_id=uid,include=exceptions))
  for m in current['mandates']:
   if m['unit_id']==template['unit_id'] and m['authority']!='people':f['mandates'].append(dict(m,unit_id=uid))
  f['policies'].append(dict(unit_id=uid,mode=mode,workers=workers,admissible_managers=bosses,exceptions=exceptions,exception_manager=f['head_position'] if exceptions else None,balanced_shared=mode=='shared'));j+=1
 ledger=old.commit(f);return ledger,c

def reporting_truth(ledger,c,salt=0):return old.select_truth(ledger,c,residual_salt=salt)
