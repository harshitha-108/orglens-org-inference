"""Immutable public publication facts with no selected edges or hidden structural keys."""
from dataclasses import dataclass
from collections import defaultdict
from .foundation import validate_facts,FrozenLedger,dt,interval,active,INF,iso
@dataclass(frozen=True)
class Contact:
    employee_id:str
    name:str
    title:str
@dataclass(frozen=True)
class Atom:
    subject:Contact|None
    meaning:str
    extent:str
    valid_from:str
    valid_to:str|None
    event_at:str
@dataclass(frozen=True)
class Group:
    name:str
    aliases:tuple[str,...]
    purpose:str
    product:str
    region:str
    valid_from:str
    valid_to:str|None
    atoms:tuple[Atom,...]
@dataclass(frozen=True)
class PublicationFacts:
    company_id:str
    groups:tuple[Group,...]
    contacts:tuple[Contact,...]

def project(ledger):
 if type(ledger) is not FrozenLedger:raise ValueError('Committed facts only')
 f=ledger.read();validate_facts(f);occupancy=defaultdict(list);titles=defaultdict(list)
 for o in f['occupancy']:occupancy[o['position_id']].append(o)
 for v in f['position_versions']:titles[v['position_id']].append(v)
 groups=[];lineage=[]
 def fragments(row,version,meaning,extent=''):
  out=[]
  for o in sorted(occupancy[row['position_id']],key=lambda r:(r['valid_from'],r['employee_id'])):
   for title in titles[row['position_id']]:
    a=max(interval(x)[0] for x in [row,version,o,title]);b=min(interval(x)[1] for x in [row,version,o,title])
    if a<b:out.append(Atom(Contact(o['employee_id'],o['display_name'],title['title']),meaning,extent,iso(a),None if b==INF else iso(b),iso(max(interval(row)[0],interval(o)[0]))))
  return out
 for v in sorted(f['unit_versions'],key=lambda r:(r['unit_id'],r['valid_from'])):
  atoms=[]
  for row in sorted(f['memberships'],key=lambda r:(r['position_id'],r['valid_from'])):
   if row['unit_id']==v['unit_id']:atoms+=fragments(row,v,'member' if row['kind']=='substantive' else 'affiliation')
  for row in sorted(f['mandates'],key=lambda r:(r['position_id'],r['authority'],r['valid_from'])):
   if row['unit_id']==v['unit_id']:
    projected=fragments(row,v,row['authority'],row['extent']+('; exceptions' if row['exclude'] else ''));atoms+=projected
    # Public role eligibility does not require substantive membership (director/acting roles).
    for a in projected:
     if not any(m['position_id']==row['position_id'] and active(m,a.valid_from) for m in f['memberships']):
      atoms.append(Atom(a.subject,'affiliation','',a.valid_from,a.valid_to,a.event_at))
  groups.append(Group(v['name'],tuple(v['aliases']),v['purpose'],v['product'],v['region'],v['valid_from'],v['valid_to'],tuple(atoms)))
  lineage.append({'group_ordinal':len(groups)-1,'unit_id':v['unit_id'],'effective_from':v['valid_from'],'effective_to':v['valid_to'],'input':'committed membership, occupancy, title and mandate versions; no selected edges'})
 contacts=[]
 for o in sorted(f['occupancy'],key=lambda r:r['position_id']):
  if active(o,f['as_of']):
   title=next(v['title'] for v in titles[o['position_id']] if active(v,f['as_of']));contacts.append(Contact(o['employee_id'],o['display_name'],title))
 p=PublicationFacts(f['company_id'],tuple(groups),tuple(contacts));validate_projection(p);return p,lineage

def validate_projection(p):
 if type(p) is not PublicationFacts or type(p.groups) is not tuple or type(p.contacts) is not tuple or type(p.company_id) is not str:raise ValueError('Strict publication projection required')
 for c in p.contacts:
  if type(c) is not Contact or any(type(getattr(c,k)) is not str for k in ['employee_id','name','title']):raise ValueError('Invalid public contact')
 for g in p.groups:
  if type(g) is not Group or type(g.atoms) is not tuple or type(g.aliases) is not tuple or any(type(x) is not str for x in g.aliases):raise ValueError('Invalid public group')
  if any(type(getattr(g,k)) is not str for k in ['name','purpose','product','region']):raise ValueError('Invalid public text')
  interval(g.__dict__)
  for a in g.atoms:
   if type(a) is not Atom or type(a.subject) is not Contact or a.meaning not in ['member','affiliation','people','project','functional','matrix']:raise ValueError('Invalid projected atom')
   if any(type(getattr(a.subject,k)) is not str for k in ['employee_id','name','title']):raise ValueError('Invalid projected person')
   if not (interval(g.__dict__)[0]<=interval(a.__dict__)[0] and interval(a.__dict__)[1]<=interval(g.__dict__)[1]):raise ValueError('Atom outside scope history')
 return True
