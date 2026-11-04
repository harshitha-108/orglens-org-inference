"""Read-only recovery adapter. No truth inputs; no inference or publication decisions."""
from pathlib import Path
import json
import sqlite3
import zlib

ROOT = Path(__file__).resolve().parent
DB = ROOT / 'runtime/recovery.sqlite'
SCHEMA_VERSION = 'recovery-experimental-app.1'

def catalogue():
    with sqlite3.connect(DB.as_uri() + '?mode=ro', uri=True) as db:
        return db.execute('SELECT company_id,case_name,contacts FROM companies ORDER BY case_name').fetchall()

def load_company(company_id):
    with sqlite3.connect(DB.as_uri() + '?mode=ro', uri=True) as db:
        row = db.execute('SELECT payload FROM rosters WHERE company_id=?', (company_id,)).fetchone()
    if row is None:
        raise KeyError(company_id)
    raw = json.loads(zlib.decompress(row[0]))
    # Keep the original predictions intact. Approved and proposed IDs are distinct.
    relationships = [{
        'employee_id': p['employee_id'],
        'proposed_manager_id': p['manager_id'],
        'published_manager_id': None,
        'confirmed_manager_id': None,
        'status': 'experimental_proposal' if p['manager_id'] else 'no_proposal',
        'calibrated_probability': None,
        'ranking_score': None,
        'prediction': p,
    } for p in raw['predictions']]
    return raw | {'relationships': relationships, 'schema_version': SCHEMA_VERSION}

def display(value, fallback='Not available'):
    return str(value) if value is not None and str(value).strip().lower() not in ('', 'nan', 'none') else fallback

def search_contacts(company, query='', status='All employees'):
    states = {r['employee_id']: r['status'] for r in company['relationships']}
    return [p for p in company['contacts']
            if query.casefold() in (display(p['display_name'])+' '+display(p.get('title'))).casefold()
            and (status == 'All employees' or
                 states[p['employee_id']] == ('experimental_proposal' if status == 'With proposals' else 'no_proposal'))]

REASONS = {
    'no_matching_people_accountability': 'No matching people-management responsibility was found.',
    'no_substantive_membership_evidence': 'The sources do not establish this employee’s team membership.',
    'accountability_or_pair_evidence_insufficient': 'The available evidence does not establish a direct reporting relationship.',
    'individual_allocation_not_established': 'Responsibility is shared; this employee’s individual manager is not established.',
    'multiple_plausible_named_managers': 'Several named managers remain plausible.',
    'named_manager_not_resolved_to_visible_contact': 'A named manager cannot be matched to a visible contact.',
}

def reason_text(code):
    return REASONS.get(code, 'The sources are insufficient, ambiguous or not current enough to support a proposal.')

def evidence(company, claim_ids):
    claims = {c['claim_id']: c for c in company['claims']}
    docs = {d['source_id']: d for d in company['documents']}
    result = []
    for cid in claim_ids:
        c = claims[cid]; d = docs[c['source_id']]
        assert d['text'][c['span_start']:c['span_end']] == c['quote']
        result.append((c, d))
    return result

def graph_dot(company, employee_id, mode='Selected employee', limit=40):
    """Manager -> employee display; only stored proposed edges, never fabricated links."""
    people = {p['employee_id']: p for p in company['contacts']}
    edges = [(r['proposed_manager_id'], r['employee_id']) for r in company['relationships'] if r['proposed_manager_id']]
    if mode == 'Connected component':
        ids = {employee_id}
        while True:
            expanded = ids | {x for edge in edges if any(y in ids for y in edge) for x in edge}
            if expanded == ids:
                break
            ids = expanded
        edges = [(m,e) for m,e in edges if m in ids and e in ids]
    elif mode == 'Selected employee':
        edges = [(m,e) for m,e in edges if employee_id in (m,e)]
        ids = {employee_id} | {x for edge in edges for x in edge}
    else:
        # Whole-company selection includes disconnected employees; a visible limit avoids clutter.
        ids = set(list(people)[:limit])
        ids.add(employee_id)
        edges = [(m,e) for m,e in edges if m in ids and e in ids]
    q = json.dumps
    lines = ['digraph G { rankdir=TB; graph [bgcolor="transparent"]; node [shape=box,style="rounded,filled",fillcolor="#edf5f6",fontname="Arial"];']
    for eid in people:
        if eid in ids:
            p = people[eid]
            lines.append(f'{q(eid)} [label={q(display(p["display_name"])+chr(10)+display(p.get("title"),"Title unavailable"))},color="'+('#008b8b' if eid==employee_id else '#b5c6ce')+'"];')
    for m,e in edges:
        lines.append(f'{q(m)} -> {q(e)} [style=dashed,color="#008b8b",label="Unverified proposal"];')
    return '\n'.join(lines+['}']), len(ids), len(edges)
