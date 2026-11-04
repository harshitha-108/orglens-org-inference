"""Effective-time facts with independent research-recorded time; no source/edge feedback."""
from datetime import datetime,timezone
from collections import defaultdict
from experiments.v4_m22_sources.foundation import FrozenLedger,validate_facts as structural_validate,validate_truth as structural_truth,active,DIRECT,PROJECT,FUNCTIONAL,MATRIX,TYPES
from experiments.v4_m22_sources.foundation import build_facts as scaffold,select_truth as select_current
from .common import config,compatible,canonical,digest

def dt(value):
    try:out=datetime.fromisoformat(value.replace('Z','+00:00'))
    except (AttributeError,ValueError):raise ValueError('Invalid timestamp') from None
    if out.tzinfo is None or out.utcoffset() is None:raise ValueError('Timezone required')
    if value!=out.astimezone(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z'):raise ValueError('Canonical UTC seconds with Z required')
    return out
INF=datetime.max.replace(tzinfo=timezone.utc)
def interval(row):
    a=dt(row['valid_from']);b=dt(row['valid_to']) if row['valid_to'] is not None else INF
    if a>=b:raise ValueError('Empty/inverted effective interval')
    return a,b
def contains(parent,child):
    a,b=interval(parent);x,y=interval(child)
    return a<=x and y<=b

def snapshot(f):
    return dict(f,**{table:[r for r in f[table] if active(r,f['as_of'])] for table in ['occupancy','memberships','mandates']})

def validate_facts(f):
    if f.get('schema_version')!='orglens-v4-organisation-facts.2':raise ValueError('M2.4 effective-time contract required; legacy rows are not reinterpreted')
    units={u['unit_id']:u for u in f['units']};positions={p['position_id']:p for p in f['positions']};now=dt(f['as_of'])
    for table in ['units','positions','memberships','mandates','occupancy']:
        for row in f[table]:
            interval(row)
            if dt(row['recorded_at'])>now:raise ValueError('Ledger capture after snapshot')
    for row in f['memberships']+f['mandates']:
        if row['unit_id'] not in units or row['position_id'] not in positions:raise ValueError('Temporal reference to nonexistent entity')
        if not contains(units[row['unit_id']],row) or not contains(positions[row['position_id']],row):raise ValueError('Responsibility/membership outside entity lifetime')
    byposition=defaultdict(list)
    for row in f['occupancy']:
        if row['position_id'] not in positions or not contains(positions[row['position_id']],row):raise ValueError('Occupancy outside position lifetime')
        byposition[row['position_id']].append(row)
    for rows in byposition.values():
        rows.sort(key=lambda r:interval(r)[0])
        if any(interval(a)[1]>interval(b)[0] for a,b in zip(rows,rows[1:])):raise ValueError('Overlapping occupants of one position')
    for ev in f['events']:
        if ev['unit_id'] not in units or ev['position_id'] not in positions:raise ValueError('Invalid appointment entity')
        t=dt(ev['effective_at'])
        if not all(interval(e)[0]<=t<interval(e)[1] for e in [units[ev['unit_id']],positions[ev['position_id']]]):raise ValueError('Appointment outside entity lifetime')
        if not any(m['position_id']==ev['position_id'] and m['unit_id']==ev['unit_id'] and m['valid_from']==ev['effective_at'] for m in f['mandates']):raise ValueError('Appointment lacks mandate')
        if dt(ev['recorded_at'])>now:raise ValueError('Future recorded event')
    # Older structural validator assumes one current occupant: provide only as-of rows.
    current=snapshot(f);structural_validate(current)
    return True

def commit(facts):
    validate_facts(facts)
    return FrozenLedger(canonical(facts),digest(facts))

def build_facts(archetype='product',index=0,c=None):
    c=c or config()
    # Reuse position/responsibility scaffold only; it never selects reporting edges.
    oldc=dict(compatible(c),facts_version='orglens-v4-organisation-facts.1');f=scaffold(archetype,index,oldc).read()
    f['schema_version']=c['facts_version'];f['history_scope']='effective units/positions/occupancy/mandates; current reporting graph only'
    for table in ['units','positions','memberships','mandates','occupancy']:
        for row in f[table]:
            row['recorded_at']=c['ledger_recorded_at']
            if table in ('units','positions'):row['valid_from']=c['history_existence_from']
            if table=='occupancy':row.update(valid_from=c['occupancy_effective_from'],valid_to=None)
    for ev in f['events']:ev['recorded_at']=c['ledger_recorded_at']
    return commit(f)

def select_truth(ledger,c=None,residual_salt=0):
    if type(ledger) is not FrozenLedger:raise ValueError('Committed facts required')
    f=ledger.read();validate_facts(f);c=c or config()
    current=snapshot(f)
    legacy=FrozenLedger(canonical(current),digest(current));t=select_current(legacy,compatible(c),residual_salt)
    for edge in t['relationships']:
        windows=authority_windows(current,edge)
        if not windows:raise ValueError('No temporal authority for selected edge')
        a,b=max(windows,key=lambda w:(w[1],-w[0].timestamp()))
        start=max(dt(edge['valid_from']),a);end=min(dt(edge['valid_to']) if edge['valid_to'] else INF,b)
        edge['valid_from']=start.isoformat(timespec='seconds').replace('+00:00','Z');edge['valid_to']=None if end==INF else end.isoformat(timespec='seconds').replace('+00:00','Z')
    t.update(schema_version='orglens-v4-m24-truth.1',facts_sha256=ledger.sha256)
    validate_truth(f,t);return t

def authority_windows(f,e):
    occ={o['employee_id']:o for o in f['occupancy']};child=occ[e['employee_id']];boss=occ[e['counterpart_employee_id']];kind={DIRECT:'people',PROJECT:'project',FUNCTIONAL:'functional',MATRIX:'matrix'}[e['relation_type']];out=[]
    for m in f['mandates']:
        if m['position_id']!=boss['position_id'] or m['authority']!=kind:continue
        if kind=='people' and (child['position_id'] in m['exclude'] or m['extent']=='subset' and child['position_id'] not in m['include']):continue
        for member in f['memberships']:
            if member['position_id']!=child['position_id'] or member['unit_id']!=m['unit_id'] or kind=='people' and m['extent']=='leadership_staff' and member['kind']!='leadership_staff':continue
            a=max(interval(x)[0] for x in [m,member,child,boss]);b=min(interval(x)[1] for x in [m,member,child,boss])
            if a<=dt(f['as_of'])<b:out.append((a,b))
    return out

def validate_truth(f,t):
    current=snapshot(f);structural_truth(current,t)
    occ={o['employee_id']:o for o in current['occupancy']}
    for e in t['relationships']:
        if not contains(occ[e['employee_id']],e) or not contains(occ[e['counterpart_employee_id']],e):raise ValueError('Reporting interval outside occupancy')
        if not any(a<=interval(e)[0] and interval(e)[1]<=b for a,b in authority_windows(current,e)):raise ValueError('Reporting interval exceeds mandate/membership support')
    return True
