"""Source-only extension for explicit staff membership and scoped authority."""
from collections import defaultdict
from datetime import timedelta
import hashlib,re
from experiments.product_recovery_v1.inference.contracts import validate_inputs
from experiments.product_recovery_v1.inference.extract import extract as baseline_extract,norm,date,NAME

PATTERNS=[
 ('membership','leadership',rf'(?P<name>{NAME}) (?:serves on|is a member of) the leadership team for (?P<unit>.+)\.'),
 ('membership','substantive',rf'(?P<name>{NAME}) is assigned to the (?P<unit>.+) team\.'),
 ('membership','substantive',rf'(?P<name>{NAME}) is a member of the staff team for (?P<unit>.+)\.'),
]
for scope,audience in [('leadership','leadership team'),('substantive','staff team')]:
 PATTERNS.extend([
  ('people_accountability',scope,rf'(?P<name>{NAME}) oversees staff appraisals and hiring for the {audience} for (?P<unit>.+)\.'),
  ('people_accountability',scope,rf'Staff appraisals and hiring for the {audience} for (?P<unit>.+) are handled by (?P<name>{NAME})\.'),
 ])
PATTERNS=[(kind,scope,re.compile(pattern)) for kind,scope,pattern in PATTERNS]

def extract(view,contacts,max_age_days=180):
 validate_inputs(view,contacts)
 original=[d for d in view['documents'] if d['document_kind']!='staff_register']
 # The pre-existing novel wording is a complete affirmative membership assertion.
 # Reuse the original claim's date/entity machinery by parsing it separately below.
 claims=baseline_extract(dict(view,documents=original),contacts,max_age_days)
 registry=defaultdict(list)
 for person in contacts:registry[person['display_name']].append(person['employee_id'])
 now=date(view['as_of'])
 for d in view['documents']:
  if d['source_type']!='synthetic_company_website' and d['source_type']!='synthetic_company_profile':continue
  is_register=d['document_kind']=='staff_register'
  if is_register:
   header,sep,raw=d['text'].partition('\n')
   if not sep or ' | ' not in header:continue
   declared,region=header.split(' | ',1);start=len(header)+1
  elif d['document_kind']=='biography':
   raw=d['text'].split('. Their current role is ',1)[0]
   if raw==d['text']:continue
   raw+='.';start=0;region=None;declared=None
  else:continue
  for kind,scope,pattern in PATTERNS:
   if not is_register and (kind,scope)!=('membership','substantive'):continue
   m=pattern.fullmatch(raw)
   if not m:continue
   name=m['name'];unit=m['unit']
   if declared is not None and norm(declared)!=norm(unit):continue
   end=start+len(raw)
   if d['text'][start:end]!=raw:continue
   flags=[];published=date(d['published_at']);ids=registry[name]
   if published is None:flags.append('date_unknown')
   elif published>now or date(d['available_at'])>now or date(d['retrieved_at'])>now:flags.append('future')
   elif now-published>timedelta(days=max_age_days):flags.append('stale')
   if d['valid_from_claimed'] and date(d['valid_from_claimed'])>now:flags.append('future_effective')
   if d['valid_to_claimed'] and date(d['valid_to_claimed'])<=now:flags.append('ended')
   claim_id=hashlib.sha256(f'{d["source_id"]}|{start}|{end}|{kind}|{scope}'.encode()).hexdigest()[:24]
   claims.append(dict(claim_id=claim_id,company_id=view['company_id'],snapshot_id=view['snapshot_id'],kind=kind,subject_name=name,contact_id=ids[0] if len(ids)==1 else None,entity_status='confirmed' if len(ids)==1 else 'ambiguous' if ids else 'unresolved',team_raw=unit,team=norm(unit),membership_scope=scope,scope=norm(region) or None,source_id=d['source_id'],document_family_id=d['document_family_id'] or d['source_id'],span_start=start,span_end=end,quote=raw,published_at=d['published_at'],available_at=d['available_at'],retrieved_at=d['retrieved_at'],effective_from=d['valid_from_claimed'],effective_to=d['valid_to_claimed'],flags=flags,alias=None,alias_target=None,alias_evidence_ids=[]))
   break
 return claims
