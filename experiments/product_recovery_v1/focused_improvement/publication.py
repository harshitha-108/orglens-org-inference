"""Supplement ordinary published role profiles with independently sampled staff records.

The publisher receives only projected unit names, regions, person names, role scope
and effective dates. Selection outcomes, position IDs and manager IDs are never
passed to it. Organisation generation and all baseline source noise stay intact.
"""
from collections import defaultdict
from copy import deepcopy
from datetime import timedelta
import hashlib
from experiments.product_recovery_v1.publication import publish as baseline_publish, stream, iso
from experiments.v4_m24_history.foundation import snapshot, active, dt

def staff_projection(ledger):
    f=ledger.read();s=snapshot(f);asof=f['as_of']
    units={u['unit_id']:u for u in f['unit_versions'] if active(u,asof)}
    occupancy={o['position_id']:o for o in s['occupancy']}
    records=[]
    for table,kind in [('memberships','membership'),('mandates','duty')]:
        for row in s[table]:
            person=occupancy.get(row['position_id'])
            unit=units.get(row['unit_id'])
            if not person or not unit:continue
            if kind=='duty' and (row['authority']!='people' or row['extent'] not in {'all','leadership_staff'} or row['exclude']):continue
            label=row['kind'] if kind=='membership' else row['extent']
            if label not in {'substantive','leadership_staff','all'}:continue
            records.append((kind,person['display_name'],unit['name'],unit['region'],
                            'leadership' if label=='leadership_staff' else 'substantive',
                            max(person['valid_from'],unit['valid_from'],row['valid_from'])))
    return tuple(sorted(set(records)))

def supplement(view,records,config,seed,regime,*,messy):
    out=deepcopy(view)
    disclosure=stream(seed,'supplement-disclosure')
    noise=stream(seed,'supplement-noise')
    now=dt(view['as_of'])
    for i,(kind,name,unit,region,scope,effective) in enumerate(records):
        rate=config['membership_supplement' if kind=='membership' else 'duty_supplement'][regime]
        if disclosure.random()>=rate:continue
        wording=disclosure.randrange(2)
        if kind=='membership':
            if scope=='leadership':
                text=[f'{name} serves on the leadership team for {unit}.',f'{name} is a member of the leadership team for {unit}.'][wording]
            else:
                text=[f'{name} is assigned to the {unit} team.',f'{name} is a member of the staff team for {unit}.'][wording]
        else:
            audience='the leadership team for ' if scope=='leadership' else 'the staff team for '
            text=[f'{name} oversees staff appraisals and hiring for {audience}{unit}.',f'Staff appraisals and hiring for {audience}{unit} are handled by {name}.'][wording]
        published=iso(max(dt(effective),now-timedelta(days=disclosure.randint(1,45))))
        if messy and noise.random()<.12:continue
        if messy and noise.random()<.07:text=text.replace('staff appraisals','work processes').replace('is assigned to','assists')
        undated=messy and noise.random()<.08
        source=hashlib.sha256(f'{view["company_id"]}|staff-register|{i}'.encode()).hexdigest()[:24]
        out['documents'].append(dict(source_id=source,company_id=view['company_id'],text=f'{unit} | {region}\n{text}',source_type='synthetic_company_website',document_kind='staff_register',published_at=None if undated else published,available_at=published,retrieved_at=view['as_of'],valid_from_claimed=effective,valid_to_claimed=None,provenance_status='synthetic_assumption',document_family_id=f'staff-register-{i}',origin_reference=f'synthetic://staff-register/{i}',publisher_description='Synthetic staff-profile and responsibilities publication assumptions'))
    return out
