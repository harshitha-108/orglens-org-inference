"""Conservative compositional direct-manager baseline. No truth/file access."""
from collections import defaultdict
import networkx as nx
from .extract import extract
BLOCK={'date_unknown','stale','future','future_effective','ended','ambiguous_alias','unverified_alias','event_only','shared_responsibility','unspecified_subset','negated'}
def usable(c):return not set(c['flags'])&BLOCK

def team_scope(c):return c["team"],c.get("membership_scope","substantive")

def infer(view,contacts,config):
 claims=extract(view,contacts,config['max_source_age_days']);byname=defaultdict(list)
 provider={d['source_id'] for d in view['documents'] if d['source_type']=='synthetic_contact_provider' or d['provenance_status']=='uncorroborated_provider'}
 for c in claims:byname[c['subject_name']].append(c)
 people=[c for c in claims if c['kind']=='people_accountability'];predictions=[]
 for employee in contacts:
  own=byname[employee['display_name']];members=[c for c in own if c['kind']=='membership'];current=[c for c in members if usable(c)];teams={c['team'] for c in current};reasons=[]
  if len({c['employee_id'] for c in contacts if c['display_name']==employee['display_name']})>1:reasons.append('employee_entity_ambiguous')
  if not members:reasons.append('no_substantive_membership_evidence')
  elif not current:reasons.append('membership_stale_undated_or_ambiguous')
  if len(teams)>1:reasons.append('multiple_or_conflicting_team_affiliations')
  if any(len({c['scope'] for c in current if c['team']==team and c['scope']})>1 for team in teams):reasons.append('conflicting_geographical_scope')
  candidates={};positive=set();all_refs=[]
  for membership in members:
   for management in people:
    if team_scope(membership)!=team_scope(management) or management['contact_id']==employee['employee_id'] or 'negated' in management['flags']:continue
    key=(management['subject_name'],management['contact_id']);candidate=candidates.setdefault(key,{'manager_name':management['subject_name'],'manager_id':management['contact_id'],'ranking_score':None,'claim_ids':[],'reasons':[]})
    pair_refs=[membership['claim_id'],management['claim_id']]+membership['alias_evidence_ids']+management['alias_evidence_ids']
    candidate['claim_ids']+=pair_refs
    flags=set(management['flags'])|set(membership['flags'])
    if membership['source_id'] in provider or management['source_id'] in provider:flags.add('uncorroborated_provider')
    if membership['scope'] and management['scope'] and membership['scope']!=management['scope']:flags.add('scope_disagreement')
    # Same named unit occurring in several published geographic scopes is not unique.
    geos={c['scope'] for c in claims if team_scope(c)==team_scope(membership) and c['scope'] and c['kind'] in ('membership','people_accountability')}
    if len(geos)>1 and (not membership['scope'] or not management['scope']):flags.add('scope_ambiguous')
    if management['contact_id'] is None:flags.add('manager_contact_unresolved')
    if management['document_family_id']==membership['document_family_id']:flags.add('not_independent_document_families')
    if membership['contact_id']!=employee['employee_id']:flags.add('employee_entity_ambiguous')
    candidate['reasons']+=sorted(flags)
    if not flags:positive.add(key);all_refs.extend(pair_refs)
  if any(n['team'] in teams and 'negated' in n['flags'] and not (set(n['flags'])-{'negated'}) and any(k[0]==n['subject_name'] for k in candidates) for n in people):reasons.append('contradictory_people_accountability')
  options=list(candidates.values())
  for c in options:c['claim_ids']=sorted(set(c['claim_ids']));c['reasons']=sorted(set(c['reasons']))
  # Display order is not a ranking or identity-based tie breaker.
  options.sort(key=lambda c:c['manager_name'] or '')
  if not options:reasons.append('no_matching_people_accountability')
  if len(options)>1:reasons.append('multiple_plausible_named_managers')
  if any(c['manager_id'] is None for c in options):reasons.append('named_manager_not_resolved_to_visible_contact')
  if any(set(c['reasons'])&{'shared_responsibility','unspecified_subset'} for c in options):reasons.append('individual_allocation_not_established')
  if options and not positive:reasons.append('accountability_or_pair_evidence_insufficient')
  selected=None
  if not reasons and len(options)==1 and len(positive)==1:selected=options[0]
  predictions.append({'pipeline_version':config['version'],'company_id':view['company_id'],'snapshot_id':view['snapshot_id'],'employee_id':employee['employee_id'],'employee_name':employee['display_name'],'status':'proposed' if selected else 'unresolved','manager_id':selected['manager_id'] if selected else None,'manager_name':selected['manager_name'] if selected else None,'candidates':options,'reasons':sorted(set(reasons)),'evidence_claim_ids':sorted(set(all_refs)) if selected else [],'ranking_score':None,'calibrated_estimate':None})
 graph=nx.DiGraph((p['employee_id'],p['manager_id']) for p in predictions if p['manager_id'])
 cyclic=set().union(*(s for s in nx.strongly_connected_components(graph) if len(s)>1)) if graph else set()
 for p in predictions:
  if p['employee_id'] in cyclic:p.update(status='unresolved',manager_id=None,manager_name=None,evidence_claim_ids=[],reasons=sorted(set(p['reasons'])|{'cycle_prevented'}))
 return {'claims':claims,'predictions':predictions,'graph':graph_export(contacts,predictions)}

def graph_export(contacts,predictions):
 return {'schema_version':'orglens-relationship-graph.1','direction':'employee_to_manager','verified':False,'nodes':[{'id':c['employee_id'],'label':c['display_name'],'title':c['title']} for c in contacts],'edges':[{'source':p['employee_id'],'target':p['manager_id'],'relation_type':'direct_people_management','label':'Unverified experimental proposal','evidence_claim_ids':p['evidence_claim_ids']} for p in predictions if p['manager_id']],'candidate_edges':[{'source':p['employee_id'],'target':c['manager_id'],'label':'Unverified suggestion','style':'dashed','evidence_claim_ids':c['claim_ids']} for p in predictions for c in p['candidates'] if c['manager_id'] and c['manager_id']!=p['employee_id']]}
