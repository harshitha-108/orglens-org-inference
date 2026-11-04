"""Small source-only semantic rules. Raw text/spans retained; no template library."""
import re,hashlib,json
from collections import defaultdict
from datetime import datetime,timedelta
from .contracts import validate_inputs

def norm(v):return re.sub(r'\s+',' ',(v or '').strip(' \t\r\n.,;:')).casefold()
def date(v):return datetime.fromisoformat(v.replace('Z','+00:00')) if v else None
ROLE_WORDS=set('service specialist manager head operations director project programme coordinator officer standards lead leadership office team department regional client services staffing annual reviews joint responsibility staff practice quality assurance chief senior'.split())
WORD=r"[A-ZÀ-ÖØ-Þ][a-zà-öø-ÿ]*(?:[’'\-][A-Za-zÀ-ÖØ-öø-ÿ]+)*"
NAME=WORD+r'(?:\s+'+WORD+r'){1,3}'
def people_names(text,known):
 names={name for name in known if re.search(r'(?<!\w)'+re.escape(name)+r'(?!\w)',text)}
 patterns=[r'(?P<n>'+NAME+r')(?=\s+(?:works?|holds?|handles?|shares?|retains?|manages?|coordinates?|organises?|sets?|oversees?|helps?|took|joined|was|is|focuses?)\b)',r'\b(?:by|with|including|includes?|involves?)\s+(?P<n>'+NAME+r')(?=[.,;]|$)',r'(?:^|[:;])\s*(?P<n>'+NAME+r')\s+[—–]']
 for pattern in patterns:
  for m in re.finditer(pattern,text):
   name=m.group('n')
   if not any(w.casefold() in ROLE_WORDS for w in name.split()):names.add(name)
 return sorted(names)
# Conservative lexical geography vocabulary; no generator or company metadata.
GEOGRAPHY={norm(x) for x in ['UK','United Kingdom','US','USA','United States','ANZ','Australia and New Zealand','Australia','New Zealand','Canada','Singapore','North America','Europe','Asia Pacific','EMEA','APAC']}
def geographic(v):return norm(v) in GEOGRAPHY

def split_geography(text):
 body=text.strip(' .')
 matches=list(re.finditer(r'(?:,\s*|\s+)(?:serving|in|across|within)\s+([^,;.!?]+)$',body,re.I))
 for m in reversed(matches):
  if geographic(m.group(1)):return body[:m.start()].rstrip(' ,'),m.group(1).strip()
 return body,None

def bounded_team(text):
 if not text:return None
 body,_=split_geography(text)
 body=re.split(r'\s*,\s*(?:where|which|while|including)\b|\s*;\s*',body,maxsplit=1,flags=re.I)[0].strip(' .')
 return None if geographic(body) else body

def tail_scope(text):
 body,_=split_geography(text)
 # Inverse accountability clause ends before the named person's predicate.
 joint=re.search(r'\b(?:duties|responsibilities|responsibility)\s+(?:in|for|across|within)\s+(.+?)\s+(?:include|includes|involve|involves)\s+',body,re.I)
 if joint:return bounded_team(joint.group(1))
 markers=list(re.finditer(r'\b(?:for|across|within|involving|with|in)\s+',body,re.I))
 return bounded_team(body[markers[-1].end():]) if markers else None

def alias_heading(text):
 # A biography sentence is not a unit-name heading.
 if re.search(r'\b(?:works?|working|holds?|supporting|serving|handles?|shares?|took|staffing|reviews)\b',text,re.I):return None
 m=re.fullmatch(r'([^,|.!?;()]+?)\s*\(([^()]+)\)(?:\s*[,|]\s*[^.!?;]+)?',text.strip())
 if not m or geographic(m.group(2)) or not bounded_team(m.group(1)):return None
 return m

def extract(view,contacts,max_age_days=180):
 validate_inputs(view,contacts);known=defaultdict(list)
 for c in contacts:known[c['display_name']].append(c['employee_id'])
 now=date(view['as_of']);claims=[]
 def add(kind,name,team,d,start,end,flags=(),scope=None,alias_target=None):
  if not team and kind not in ('vague_authority',):return
  raw=bounded_team(team) if team else None;local_target=None;alias=None
  if not raw and kind!='vague_authority':return
  if raw:
   m=re.fullmatch(r'(.+?)\s*\(([^()]+)\)',raw)
   if m and not geographic(m.group(2)):alias=m.group(1).strip();local_target=m.group(2).strip()
  cid=hashlib.sha256(json.dumps([d['source_id'],start,end,kind,name,raw],ensure_ascii=False).encode()).hexdigest()[:24]
  published=date(d['published_at']);flags=set(flags)
  if published is None:flags.add('date_unknown')
  elif published>now:flags.add('future')
  elif now-published>timedelta(days=max_age_days):flags.add('stale')
  if date(d['available_at'])>now or date(d['retrieved_at'])>now:flags.add('future')
  effective=d['valid_from_claimed'];ended=d['valid_to_claimed'];explicit=re.search(r'\b(?:From|Effective|Since|On)\s+(\d{4}-\d{2}-\d{2})',d['text'][start:end],re.I)
  if explicit:effective=explicit.group(1)+'T00:00:00Z'
  if effective and date(effective)>now:flags.add('future_effective')
  if ended and date(ended)<=now:flags.add('ended')
  ids=known.get(name,[]);row={'claim_id':cid,'company_id':view['company_id'],'snapshot_id':view['snapshot_id'],'kind':kind,'subject_name':name,'contact_id':ids[0] if len(ids)==1 else None,'entity_status':'confirmed' if len(ids)==1 else 'ambiguous' if ids else 'unresolved','team_raw':raw,'team':norm(local_target or raw),'scope':norm(scope) or None,'source_id':d['source_id'],'document_family_id':d['document_family_id'] or d['source_id'],'span_start':start,'span_end':end,'quote':d['text'][start:end],'published_at':d['published_at'],'available_at':d['available_at'],'retrieved_at':d['retrieved_at'],'effective_from':effective,'effective_to':ended,'flags':sorted(flags),'alias':norm(alias) if alias else None,'alias_target':norm(local_target or alias_target) if local_target or alias_target else None}
  assert d['text'][start:end]==row['quote'];claims.append(row)
  if alias and kind!='alias':add('alias',None,alias,d,start,end,flags,scope,local_target)
 for d in view['documents']:
  text=d['text'];first=text.split('\n')[0];header_team=None;header_region=None
  if '\n' in text and ('|' in first or ',' in first):
   header_team,header_region=re.split(r'[|,]',first,maxsplit=1);header_team=header_team.strip();header_region=header_region.strip()
  # A standalone published alias heading can corroborate two differently named scopes.
  heading_alias=alias_heading(first)
  if heading_alias and len(heading_alias.group(2).split())>=2 and norm(heading_alias.group(2)) not in {'north america','united kingdom','australia and new zealand'}:
   add('alias',None,heading_alias.group(1),d,0,len(first),scope=header_region,alias_target=heading_alias.group(2))
  doc_names=people_names(text,known)
  for match in re.finditer(r'[^.!?\n]+[.!?]?',text):
   raw=match.group();left=len(raw)-len(raw.lstrip());sentence=raw.strip();start=match.start()+left;end=start+len(sentence)
   if not sentence:continue
   low=sentence.casefold();names=people_names(sentence,known);scope=header_region;body,body_region=split_geography(sentence)
   if body_region:scope=body_region
   serving=re.search(r'\bserving\s+(.+?)[.]?$',sentence,re.I)
   if serving:scope=serving.group(1).strip(' .')
   # Team equivalence is accepted only when explicitly written, not from hidden dictionaries.
   alias_match=re.search(r'(?P<t>.+?),\s*(?:also called|also known as|known as)\s+(?P<a>[^.]+)',sentence,re.I)
   if alias_match:
    target=alias_match.group('t');target=re.split(r'\b(?:works? (?:in|with)|working in|part of|member of)\s+',target,flags=re.I)[-1];add('alias',None,alias_match.group('a'),d,start,end,scope=scope,alias_target=target)
   if 'provider summary lists' in low and len(doc_names)==1:
    m=re.search(r'lists\s+(.+?)\s+as\s+(?:the\s+)?current team',sentence,re.I)
    if m:add('membership',doc_names[0],m.group(1),d,start,end,scope=scope)
   # Directory entries locate contacts but do not establish substantive membership.
   if d['document_kind']=='team_directory':
    for name in names:add('directory_contact',name,header_team,d,start,end,scope=scope)
    continue
   aff=re.search(r'\bworks?\s+(?:in|with)\s+(.+?)(?=\s+as\s+|,\s*(?:serving|also called|also known as|known as)\s+|\s+in\s+|[.]?$)',sentence,re.I)
   front=re.match(r'Working in\s+(.+?),\s*('+NAME+r')\s+',sentence)
   if front:affteam=front.group(1);affnames=[front.group(2)]
   else:affteam=aff.group(1) if aff else None;affnames=names
   substantive=bool(front or aff and ('works in' in low or re.search(r'\s+as\s+',sentence,re.I)))
   if substantive:
    for name in affnames:add('membership',name,affteam,d,start,end,scope=scope)
    continue
   if 'holds the role' in low or 'leadership role associated' in low:
    support=re.search(r'\b(?:supporting|associated with)\s+(.+)',body,re.I)
    team=bounded_team(support.group(1)) if support else tail_scope(body)
    for name in names:add('general_affiliation',name,team,d,start,end,scope=scope)
    continue
   if not names:continue
   kind=None;team=None;flags=[]
   project_only=bool(re.search(r'\b(?:project|delivery|milestone|schedules?)\b',low) and re.search(r'\b(?:coordinat\w*|organis\w*)\b',low) and not re.search(r'\b(?:appraisal|staff reviews|performance reviews|staff.management|hiring[^.]*reviews)\b',low))
   if project_only:kind='project_coordination'
   elif re.search(r'\b(?:appraisal|staff.management|staffing|staff reviews|performance reviews|hiring[^.]*reviews|manages?\s+(?:the\s+)?staff)\b',low):kind='people_accountability'
   elif re.search(r'\b(?:project|delivery|milestone|schedules?)\b',low) and re.search(r'\b(?:coordinat\w*|organis\w*)\b',low):kind='project_coordination'
   elif re.search(r'\b(?:professional|practice|technical|clinical)\s+(?:standards|guidance)|\bpractice guidance\b',low):kind='functional_oversight'
   elif 'regional' in low and re.search(r'\b(?:programme|program|priorities|commitments)\b',low):kind='matrix_oversight'
   elif re.search(r'\b(?:lead\w*|oversees?|manage\w*)\b',low):kind='vague_authority'
   if kind:
    reverse=re.search(r'\bfor\s+(.+?)\s+(?:sit|sits|lie|lies|rest|are|is)\s+(?:with|handled by|coordinated by|managed by)',sentence,re.I)
    division=re.match(r'(.+?)\s+divides\s+staff',sentence,re.I)
    guidance=re.match(r'(.+?)\s+draws on\s+',sentence,re.I)
    matrix=re.search(r'works with\s+(.+?)\s+on\s+',sentence,re.I)
    team=reverse.group(1) if reverse else division.group(1) if division else guidance.group(1) if guidance else matrix.group(1) if matrix else tail_scope(sentence)
    if kind=='vague_authority' and not team:
     m=re.search(r'\b(?:leads?|oversees?|helps lead)\s+(.+)',sentence,re.I);team=m.group(1) if m else header_team
    if re.search(r'\b(?:no|not|never|without)\b',low):flags.append('negated')
    if any(w in low for w in ['shares','shared','joint','divides']):flags.append('shared_responsibility')
    if 'seconded' in low or 'subset' in low:flags.append('unspecified_subset')
    if re.search(r'\b(?:took up|appointed|joined|assumed)\b',low):flags.append('event_only')
    for name in names:add(kind,name,team or header_team,d,start,end,flags,scope)
 # Explicit alias graph only; no fuzzy matching or private dictionary.
 alias_claims=defaultdict(list)
 for c in claims:
  if c['kind']=='alias' and c['alias_target']:alias_claims[c['team']].append(c)
 blocked={'date_unknown','stale','future','future_effective','ended','event_only','shared_responsibility','unspecified_subset','negated'}
 for c in claims:
  c['alias_evidence_ids']=[]
  if c['kind']=='alias':continue
  current=c['team'];visited=set();refs=[];failure=None
  while current in alias_claims:
   if current in visited:failure='ambiguous_alias';break
   visited.add(current)
   # Canonicalisation is valid only in the claim's published scope and time.
   def compatible(a):
    if set(a['flags'])&blocked:return False
    if c['scope'] and a['scope'] and c['scope']!=a['scope']:return False
    when=date(c['effective_from']) or date(c['published_at'])
    return not when or (not a['effective_from'] or date(a['effective_from'])<=when) and (not a['effective_to'] or when<date(a['effective_to']))
   linked=[a for a in alias_claims[current] if compatible(a)]
   targets={a['alias_target'] for a in linked}
   if not targets:failure='unverified_alias';break
   if len(targets)>1:failure='ambiguous_alias';break
   refs.extend(a['claim_id'] for a in linked);target=next(iter(targets))
   if target==current:break
   current=target
  c['alias_evidence_ids']=sorted(set(refs))
  if failure:c['flags']=sorted(set(c['flags'])|{failure})
  else:c['team']=current
 return claims
