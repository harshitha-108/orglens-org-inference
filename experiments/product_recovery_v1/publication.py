"""Publisher receives immutable PUBLIC projection only, never reporting truth/policies."""
from copy import deepcopy
from datetime import timedelta
import random,hashlib
from experiments.v4_m25a.projection import PublicationFacts,validate_projection
from experiments.v4_m24_history.foundation import dt,active

def stream(seed,namespace,salt=0):return random.Random(int(hashlib.sha256(repr((seed,namespace,salt)).encode()).hexdigest(),16))
def iso(t):return t.isoformat(timespec='seconds').replace('+00:00','Z')
def publish(public,cfg,seed,regime,noise_salt=0):
 if type(public) is not PublicationFacts:raise ValueError('Strict public projection only')
 validate_projection(public);now=cfg['as_of'];pub=stream(seed,'publication');visibility=stream(seed,'contact_visibility');noise=stream(seed,'observation_noise',noise_salt);docs=[]
 def doc(text,kind,group,family,published=None,start=None,end=None):
  date=published or iso(max(dt(group.valid_from),dt(now)-timedelta(days=pub.randint(1,60))));i=len(docs);docs.append(dict(source_id=hashlib.sha256(repr((public.company_id,i)).encode()).hexdigest()[:24],company_id=public.company_id,text=text,source_type='synthetic_company_profile' if kind=='biography' else 'synthetic_company_website',document_kind=kind,published_at=date,available_at=iso(min(dt(now),dt(date)+timedelta(days=1))),retrieved_at=now,valid_from_claimed=start,valid_to_claimed=end,provenance_status='synthetic_assumption',document_family_id=family,origin_reference='synthetic://'+public.company_id+'/'+kind+'/'+str(i),publisher_description='Synthetic independent editorial origin; source independence is a modelling assumption'))
 current_groups=[g for g in public.groups if active(g.__dict__,now)];unit_names=[g.name for g in current_groups];current_contacts={p.employee_id:p for p in public.contacts}
 # Master documents are published before registry visibility is sampled.
 for gi,g in enumerate(public.groups):
  current=[a for a in g.atoms if active(a.__dict__,now)];name=g.name
  if active(g.__dict__,now):
   for ai,a in enumerate(current):
    if a.meaning=='member' and pub.random()<cfg['biography_probability'][regime]:
     title=a.subject.title;phrase=pub.randrange(3)
     text=[f'{a.subject.name} works in {name}, serving {g.region}.',f'{a.subject.name} works with {name} as {title}, serving {g.region}.',f'Working in {name}, {a.subject.name} focuses on {g.purpose}. Role: {title}.'][phrase]
     if pub.random()<cfg['wording_novel_probability']:text=f'{a.subject.name} is assigned to the {name} team. Their current role is {title}.'
     doc(text,'biography',g,'bio-'+str(gi)+'-'+str(ai))
   people=[a for a in current if a.meaning=='people'];others=[a for a in current if a.meaning in {'project','functional','matrix'}]
   if people and pub.random()<cfg['duties_probability'][regime]:
    public_name=(g.aliases[0]+' ('+name+')') if g.aliases and pub.random()<cfg['alias_probability'] else name
    sentences=[]
    for a in people:
     if a.extent.startswith('joint') or a.extent.startswith('shared'):sentences.append(f'{a.subject.name} shares staff-management duties across {public_name}.')
     elif a.extent.startswith('subset') or 'exceptions' in a.extent:sentences.append(f'{a.subject.name} retains appraisal responsibility for a subset of colleagues in {public_name}.')
     elif a.extent.startswith('leadership_staff'):sentences.append(f'{a.subject.name} holds a leadership role associated with {public_name}.')
     else:
      phr=pub.randrange(3);sentences.append([f'{a.subject.name} handles hiring and staff reviews for {public_name}.',f'Staffing and annual reviews for {public_name} sit with {a.subject.name}.',f'{a.subject.name} manages staff and performance reviews for {public_name}.'][phr])
    doc(public_name+', '+g.region+'\n'+' '.join(sentences),'responsibility_statement',g,'duties-'+str(gi))
   if others and pub.random()<cfg['nonpeople_probability']:
    sentences=[]
    for a in others:
     sentences.append(f'{a.subject.name} coordinates delivery milestones for {name}.' if a.meaning=='project' else f'{a.subject.name} sets professional standards for {name}.' if a.meaning=='functional' else f'{a.subject.name} oversees regional programme commitments involving {name}.')
    doc(name+', '+g.region+'\n'+' '.join(sentences),'unit_page',g,'nonpeople-'+str(gi))
   if pub.random()<cfg['directory_probability']:
    listed=[a.subject.name+' — '+a.subject.title for a in current if a.meaning in {'member','affiliation'} and pub.random()<0.65]
    if listed:doc(name+' | '+g.region+'\nContacts: '+'; '.join(listed)+'. This list includes selected public contacts.','team_directory',g,'directory-'+str(gi))
  for ai,a in enumerate(g.atoms):
   if a.meaning=='people' and a.valid_to is not None and pub.random()<cfg['history_probability']:
    date=iso(dt(a.valid_from)+timedelta(days=7));text=f'From {a.valid_from[:10]}, {a.subject.name} took up staffing and review responsibilities with {name}.';doc(text,'appointment_announcement',g,'history-'+str(gi)+'-'+str(ai),date,a.valid_from,a.valid_to)
 contacts=[]
 for p in public.contacts:
  if visibility.random()<cfg['visible_probability']:
   title=p.title
   if noise.random()<cfg['messy_missing_title']:title=''
   elif noise.random()<0.35:title=title.replace('Manager','Mgr').replace('Operations','Ops').replace('Senior','Sr')
   contacts.append(dict(employee_id=p.employee_id,display_name=p.name,title=title))
 clean=dict(schema_version='orglens-v4-source-observable.1',company_id=public.company_id,snapshot_id=now,as_of=now,documents=docs,mentions=[],claims=[],contradiction_records=[]);messy=deepcopy(clean);messy['documents']=[d for d in messy['documents'] if noise.random()>=cfg['messy_document_omission']]
 for d in messy['documents']:
  if noise.random()<0.08:d['published_at']=None
  if noise.random()<0.12:d['text']=d['text'].replace(', serving UK','').replace(', serving Australia and New Zealand','')
  if noise.random()<0.07:d['text']=d['text'].replace('staff reviews','staffing processes').replace('works in','contributes to')
 # Independent noisy provider affiliation, possibly contradicting an omitted/correct source.
 for p in contacts:
  if noise.random()<cfg['messy_provider_conflict'] and unit_names:
   name=noise.choice(unit_names);i=len(messy['documents']);date=iso(dt(now)-timedelta(days=15));messy['documents'].append(dict(source_id=hashlib.sha256(repr((public.company_id,'provider',i)).encode()).hexdigest()[:24],company_id=public.company_id,text=p['display_name']+'. A provider summary lists '+name+' as the current team.',source_type='synthetic_contact_provider',document_kind='biography',published_at=date,available_at=date,retrieved_at=now,valid_from_claimed=None,valid_to_claimed=None,provenance_status='uncorroborated_provider',document_family_id='provider-'+str(i),origin_reference='synthetic://provider/'+str(i),publisher_description='Possibly outdated affiliation; observation noise independent of reporting truth'))
 return clean,messy,contacts
