"""Pre-edge facts committed immutably; no observation imports or feedback."""
from dataclasses import dataclass
from collections import Counter,defaultdict
import json
import networkx as nx
from .common import config,rng,opaque,canonical,digest
DIRECT='direct_people_management';PROJECT='project_coordination';FUNCTIONAL='functional_leadership';MATRIX='matrix_dotted_line'
TYPES={DIRECT,PROJECT,FUNCTIONAL,MATRIX}
@dataclass(frozen=True)
class FrozenLedger:
    content:str
    sha256:str
    def read(self):
        if digest(json.loads(self.content))!=self.sha256:raise ValueError('Facts changed after commitment')
        return json.loads(self.content)
def commit(facts):
    validate_facts(facts)
    return FrozenLedger(canonical(facts),digest(facts))
ARCH={
 'product':('Software',['Merchant support','Payment reliability','Release operations','Partner services'],'Payments'),
 'regional_services':('Recruitment',['Candidate care','Placement operations','Client onboarding','Contract services'],'Staffing'),
 'multi_site':('Manufacturing',['Plant maintenance','Quality assurance','Production planning','Dispatch operations'],'Industrial equipment'),
 'regulated':('Financial services',['Client servicing','Risk operations','Account services','Settlement operations'],'Accounts'),
 'clinical':('Healthcare',['Outpatient scheduling','Care coordination','Diagnostics operations','Patient services'],'Clinical services')}
def build_facts(archetype='product',index=0,c=None):
    c=c or config()
    if archetype not in ARCH:raise ValueError('Unknown archetype')
    if index<0 or index>=20:raise ValueError('Bounded development examples only')
    industry,names,product=ARCH[archetype];org=rng(c,index,'organisation');staff=rng(c,index,'staffing');cid=opaque(c,index,'company',0)
    units=[];positions=[];memberships=[];mandates=[];policies=[];events=[];occupancy=[]
    def pos(title,unit=None,kind='substantive',vacant=False):
        p=opaque(c,index,'position',len(positions));positions.append({'position_id':p,'company_id':cid,'title':title,'valid_from':c['valid_from'],'valid_to':None})
        if unit:memberships.append({'position_id':p,'unit_id':unit,'kind':kind,'valid_from':c['valid_from'],'valid_to':None})
        if not vacant:
            n=len(occupancy);first=['Ada','Lin','Mira','Bo','Uma','Cia','Owen','Nikhil','Priya','Noah','Sam','Leila'][n%12];last=['Morgan','Singh','Chen','Patel'][n//12%4];occupancy.append({'position_id':p,'employee_id':opaque(c,index,'contact',n),'display_name':first+' '+last,'name_order':staff.random()})
        return p
    root=pos('Managing Director');head=pos('Head of Operations');project=pos('Programme Coordinator');functional=pos('Professional Standards Lead');old=pos('Operations Adviser');vacant=pos('Acting Service Manager',vacant=True)
    exec_unit=opaque(c,index,'unit','leadership');units.append({'unit_id':exec_unit,'name':'Leadership office','function':'Executive','purpose':'Company operations and professional support','product':product,'region':'UK','valid_from':c['valid_from'],'valid_to':None})
    memberships.append({'position_id':head,'unit_id':exec_unit,'kind':'substantive','valid_from':c['valid_from'],'valid_to':None});mandates.append({'position_id':root,'unit_id':exec_unit,'authority':'people','extent':'all','exclude':[],'valid_from':c['valid_from'],'valid_to':None})
    for i,mode in enumerate(['unique','shared','joint','exception']):
        uid=opaque(c,index,'unit',i);region=org.choice(['UK','Australia and New Zealand']) if archetype in ('regional_services','clinical') else 'UK';purpose=org.choice(['case handling and service quality','service continuity and operational planning'])
        units.append({'unit_id':uid,'name':names[i],'function':'Operations','purpose':purpose,'product':product,'region':region,'valid_from':c['valid_from'],'valid_to':None})
        bosses=[pos('Service Manager') for _ in range(2 if mode in ('shared','joint') else 1)]
        for boss in bosses:memberships.append({'position_id':boss,'unit_id':exec_unit,'kind':'leadership_staff','valid_from':c['valid_from'],'valid_to':None})
        workers=[pos('Service Specialist',uid) for _ in range(10 if mode=='shared' else 5)]
        # Pre-existing exception: one seconded position's appraisal remains with the operational head.
        exceptions=[workers[-1]] if mode=='exception' else []
        for boss in bosses:mandates.append({'position_id':boss,'unit_id':uid,'authority':'people','extent':'shared_allocation' if mode=='shared' else 'joint' if mode=='joint' else 'all','exclude':exceptions,'valid_from':c['valid_from'],'valid_to':None})
        for authority,boss in [('project',project),('functional',functional),('matrix',head)]:mandates.append({'position_id':boss,'unit_id':uid,'authority':authority,'extent':'all','exclude':[],'valid_from':c['valid_from'],'valid_to':None})
        for w in exceptions:mandates.append({'position_id':head,'unit_id':uid,'authority':'people','extent':'subset','include':[w],'exclude':[],'valid_from':c['valid_from'],'valid_to':None})
        policies.append({'unit_id':uid,'mode':mode,'workers':workers,'admissible_managers':bosses,'exceptions':exceptions,'exception_manager':head if exceptions else None,'balanced_shared':mode=='shared'})
        # Genuine previous mandate for first unit; its history precedes current facts.
        if i==0:
            mandates.append({'position_id':old,'unit_id':uid,'authority':'people','extent':'all','exclude':[],'valid_from':'2025-01-01T00:00:00Z','valid_to':c['valid_from']})
        events.append({'unit_id':uid,'position_id':bosses[0],'effective_at':c['valid_from'],'kind':'mandate_appointment'})
    for p in [project,functional,old]:memberships.append({'position_id':p,'unit_id':exec_unit,'kind':'leadership_staff','valid_from':c['valid_from'],'valid_to':None})
    # A manager can oversee several units: head owns leadership staff, exceptions and matrix remits.
    mandates.append({'position_id':head,'unit_id':exec_unit,'authority':'people','extent':'leadership_staff','exclude':[],'valid_from':c['valid_from'],'valid_to':None})
    f={'schema_version':c['facts_version'],'company_id':cid,'archetype':archetype,'industry':industry,'index':index,'as_of':c['as_of'],'units':units,'positions':positions,'memberships':memberships,'mandates':mandates,'policies':policies,'events':events,'occupancy':occupancy,'root_position':root,'head_position':head,'vacant_positions':[vacant],'evaluation_unknown_positions':[policies[-1]['workers'][0]],'span_limits':{'manager':c['manager_span_limit'],'head':c['head_span_limit']}}
    return commit(f)
def active(row,asof):return row['valid_from']<=asof and (row['valid_to'] is None or asof<row['valid_to'])
def validate_facts(f):
    positions={p['position_id'] for p in f['positions']};units={u['unit_id'] for u in f['units']}
    if len(positions)!=len(f['positions']) or len(units)!=len(f['units']):raise ValueError('Duplicate keys')
    for m in f['memberships']:
        if m['position_id'] not in positions or m['unit_id'] not in units:raise ValueError('Invalid membership')
    for m in f['mandates']:
        if m['position_id'] not in positions or m['unit_id'] not in units or m['authority'] not in {'people','project','functional','matrix'}:raise ValueError('Invalid mandate')
    occupied=[o['position_id'] for o in f['occupancy']]
    if len(occupied)!=len(set(occupied)) or not set(occupied)<=positions:raise ValueError('Invalid staffing')
    for p in f['policies']:
        if not set(p['workers'])<=positions or not set(p['admissible_managers'])<=positions:raise ValueError('Invalid admissible set')
        if p['mode']=='shared' and (len(p['workers'])%len(p['admissible_managers'])):raise ValueError('Shared allocation not feasible')
    # Validate the union of admissible direct edges before any residual draw.
    possible=nx.DiGraph();planned=Counter()
    for policy in f['policies']:
        for worker in policy['workers']:
            bosses=[policy['exception_manager']] if worker in policy['exceptions'] else policy['admissible_managers']
            for boss in bosses:
                if boss==worker:raise ValueError('Self-accountability in admissible set')
                possible.add_edge(worker,boss)
        if policy['mode']=='shared':
            for boss in policy['admissible_managers']:planned[boss]+=len(policy['workers'])//len(policy['admissible_managers'])
        else:
            for worker in policy['workers']:
                for boss in ([policy['exception_manager']] if worker in policy['exceptions'] else policy['admissible_managers']):planned[boss]+=1
    for m in f['memberships']:
        if m['kind']=='leadership_staff':possible.add_edge(m['position_id'],f['head_position']);planned[f['head_position']]+=1
    possible.add_edge(f['head_position'],f['root_position']);planned[f['root_position']]+=1
    if not nx.is_directed_acyclic_graph(possible):raise ValueError('Admissible choices can form a cycle')
    for boss,n in planned.items():
        maximum=f['span_limits']['head'] if boss in (f['head_position'],f['root_position']) else f['span_limits']['manager']
        if n>maximum:raise ValueError('Infeasible pre-edge span allocation')
    return True

def select_truth(ledger,c=None,residual_salt=0):
    if type(ledger) is not FrozenLedger:raise ValueError('Committed facts required')
    f=ledger.read();c=c or config();occupied={o['position_id']:o['employee_id'] for o in f['occupancy']};edges=[];choices=[]
    def add(child,boss,kind):
        if child==boss or child not in occupied or boss not in occupied:raise ValueError('Invalid occupied endpoint')
        edges.append({'employee_id':occupied[child],'counterpart_employee_id':occupied[boss],'relation_type':kind,'company_id':f['company_id'],'valid_from':c['valid_from'],'valid_to':None})
    for p in f['policies']:
        workers=list(p['workers']);rr=rng(c,f['index'],'residual_relationship_choice',str(residual_salt)+'|'+p['unit_id']);rr.shuffle(workers)
        for j,w in enumerate(workers):
            bosses=[p['exception_manager']] if w in p['exceptions'] else p['admissible_managers'] if p['mode']=='joint' else [p['admissible_managers'][j%len(p['admissible_managers'])]]
            for boss in bosses:add(w,boss,DIRECT)
            if p['mode']=='shared':choices.append({'position_id':w,'admissible_managers':p['admissible_managers'],'selected':bosses,'constraint':'balanced allocation; choices coupled'})
            for m in f['mandates']:
                if m['unit_id']==p['unit_id'] and m['authority']!='people' and active(m,f['as_of']):add(w,m['position_id'],{'project':PROJECT,'functional':FUNCTIONAL,'matrix':MATRIX}[m['authority']])
    leadership=[m for m in f['memberships'] if m['kind']=='leadership_staff']
    for m in leadership:add(m['position_id'],f['head_position'],DIRECT)
    add(f['head_position'],f['root_position'],DIRECT)
    result={'schema_version':'orglens-v4-m22-truth.1','facts_sha256':ledger.sha256,'relationships':edges,'residual_choices':choices,'evaluation_status':{o['employee_id']:('unknown' if o['position_id'] in f['evaluation_unknown_positions'] else 'complete') for o in f['occupancy']}}
    validate_truth(f,result);return result

def validate_truth(f,t):
    g=nx.DiGraph();seen=set();spans=Counter();occ={o['employee_id']:o['position_id'] for o in f['occupancy']};members=defaultdict(list)
    for m in f['memberships']:members[m['position_id']].append(m)
    for e in t['relationships']:
        child,boss=e['employee_id'],e['counterpart_employee_id'];k=(child,boss,e['relation_type'])
        if k in seen or child==boss or child not in occ or boss not in occ or e['company_id']!=f['company_id'] or e['relation_type'] not in TYPES:raise ValueError('Invalid relationship')
        seen.add(k)
        if e['relation_type']==DIRECT:
            g.add_edge(child,boss);spans[boss]+=1
            authority=[m for m in f['mandates'] if m['position_id']==occ[boss] and m['authority']=='people' and active(m,f['as_of']) and any(x['unit_id']==m['unit_id'] and (m['extent']!='leadership_staff' or x['kind']=='leadership_staff') for x in members[occ[child]]) and occ[child] not in m['exclude'] and (m['extent']!='subset' or occ[child] in m['include'])]
            if not authority:raise ValueError('Edge not supported by pre-existing mandate')
        else:
            kind={PROJECT:'project',FUNCTIONAL:'functional',MATRIX:'matrix'}[e['relation_type']]
            if not any(m['position_id']==occ[boss] and m['authority']==kind and active(m,f['as_of']) and any(x['unit_id']==m['unit_id'] for x in members[occ[child]]) for m in f['mandates']):raise ValueError('Secondary edge without matching typed mandate')
        if e['valid_from']>f['as_of'] or (e['valid_to'] is not None and e['valid_to']<=f['as_of']):raise ValueError('Inactive edge at snapshot')
    if not nx.is_directed_acyclic_graph(g):raise ValueError('Direct cycle')
    for boss,n in spans.items():
        limit=f['span_limits']['head'] if occ[boss] in (f['head_position'],f['root_position']) else f['span_limits']['manager']
        if n>limit:raise ValueError('Span exceeded')
    return True
