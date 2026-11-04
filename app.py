"""Isolated proposal-only Streamlit experience. Not the deployed v1 application."""
import json
from pathlib import Path
import streamlit as st
import adapter

st.set_page_config(page_title='OrgLens · Experimental', page_icon='◈', layout='wide')
st.markdown('''<style>.block-container{padding-top:2rem;max-width:1400px}h1,h2,h3{letter-spacing:-.02em}div[data-testid="stMetric"]{background:#edf5f6;padding:14px;border-radius:10px;color:#123} .stCaption{line-height:1.5}</style>''', unsafe_allow_html=True)
st.title('OrgLens')
st.caption('EXPERIMENTAL PRODUCT · SYNTHETIC COMPANIES · SNAPSHOT 2 NOVEMBER 2026')
st.write('Explore possible reporting relationships backed by published synthetic source documents. Every dashed line is an unverified proposal—not a confirmed manager.')
st.info('No relationships are published or independently confirmed. Individual correctness probabilities are unavailable; the evaluation precision is not confidence for a particular proposal.')

@st.cache_data(max_entries=12)
def company(cid):
    return adapter.load_company(cid)

@st.cache_data
def catalogue():
    return adapter.catalogue()

nav = st.sidebar.radio('Workspace', ['Company Explorer', 'Employee Directory', 'Evaluation & Methodology'])
st.sidebar.caption('Separate recovery prototype. The original v1 app and scientific artifacts are unchanged.')
if nav == 'Evaluation & Methodology':
    st.header('Recovery scale-up evaluation')
    st.write('500-company synthetic scale-up under a frozen authored distribution. This is not another independent holdout or real-world validation. No historical v1 metrics are used here.')
    m = json.loads((adapter.ROOT/'evidence/scale_metrics.json').read_text())['views']['messy']
    a,b,c,d = st.columns(4)
    a.metric('Companies', '500'); b.metric('Visible employees', f'{m["employees"]:,}'); c.metric('Experimental proposals', f'{m["selected"]:,}'); d.metric('Published relationships', '0')
    a,b,c,d = st.columns(4)
    a.metric('Scored precision', f'{m["precision"]:.2%}'); b.metric('All-visible coverage', f'{m["coverage"]:.2%}'); c.metric('Candidate recall', f'{m["full_pool_recall"]:.2%}'); d.metric('Companies with proposals', '466')
    st.write('8,641 correct · 360 wrong · 3 unscorable. Precision uses 9,001 scored proposals; coverage includes all 9,004 proposals. Zero structural violations. Company-cluster 95% precision interval: 95.57–96.39%.')
    st.warning('Calibration is incomplete. Low-disclosure precision is 88.31%. All 360 scored errors cite misleading provider affiliations. Missing evidence limits recall; 30 co-managed cases receive wrong proposals. Citations show what a source says, not that it is correct.')
    st.write('Original M0 gates remain unmet: 95% retrieval, 15% coverage, confidence calibration and targeted manager-removal testing. Proposals have no ranking scores or calibrated probabilities. Candidate lists are unranked.')
    st.subheader('Separate independent validation · 30 companies')
    v = json.loads((adapter.ROOT/'evidence/validation_metrics.json').read_text())['views']['messy']
    st.write(f'Frozen earlier validation: {v["employees"]:,} visible contacts; {v["correct"]} correct and {v["wrong"]} wrong proposals; precision {v["precision"]:.2%}, coverage {v["coverage"]:.2%}. This cohort is separate from the scale-up.')
    st.download_button('Download separate 30-company validation results', (adapter.ROOT/'evidence/validation_metrics.json').read_bytes(), 'validation_30_metrics.json')
    st.download_button('Download authoritative 500-company scale-up results', (adapter.ROOT/'evidence/scale_metrics.json').read_bytes(), 'scale500_metrics.json')
    with st.expander('Method and frozen evaluation metadata'):
        st.write('Source-only extraction links team affiliation to formal people-management accountability with source spans, time compatibility and ambiguity checks. Project, functional and matrix authority alone do not establish direct management. No new inference runs in this app.')
        st.caption('The unchanged evaluator contains a legacy “15-company” scope string. The verified scale-up freeze contains 500 company records; the staging verification records this documented metadata limitation.')
    st.stop()

rows = catalogue()
lookup = {r[0]: f'{r[1].replace("company_", "Company ")} · {r[2]} contacts' for r in rows}
cid = st.selectbox('Select a company · 500 available', list(lookup), format_func=lookup.get, key='company')
data = company(cid)
people = {p['employee_id']: p for p in data['contacts']}
relations = {p['employee_id']: p for p in data['relationships']}
count = sum(r['proposed_manager_id'] is not None for r in relations.values())
a,b,c,d = st.columns(4)
a.metric('Visible employees', len(people)); b.metric('Experimental proposals', count); c.metric('No proposal', len(people)-count); d.metric('Published / confirmed', '0 / 0')
st.caption('All contacts remain accessible below. Company names are synthetic case labels; industry and department are not inferred from hidden generator metadata.')
query = st.text_input('Search employees by name or job title', key='search')
status = st.selectbox('Relationship filter', ['All employees', 'With proposals', 'No proposal'])
filtered = adapter.search_contacts(data, query, status)
if not filtered:
    st.info('No employees match. Clear the search or change the filter.'); st.stop()
if nav == 'Employee Directory':
    st.dataframe([{'Name':p['display_name'], 'Job title':adapter.display(p.get('title'),'Title unavailable'), 'Relationship':'Unverified proposal' if relations[p['employee_id']]['proposed_manager_id'] else 'No proposal'} for p in filtered], hide_index=True, width='stretch')
eid = st.selectbox('Select an employee to explore', [p['employee_id'] for p in filtered], format_func=lambda x:f'{people[x]["display_name"]} · {adapter.display(people[x].get("title"),"Title unavailable")} · {x[:6]}', key=f'employee_{cid}')
r = relations[eid]; pred = r['prediction']
st.subheader(people[eid]['display_name'])
if r['proposed_manager_id']:
    st.info(f'Experimental proposed manager: {people[r["proposed_manager_id"]]["display_name"]}')
    st.caption('Unverified suggestion. Not a published or independently confirmed reporting line. Correctness probability: unavailable.')
else:
    st.warning('Manager unresolved · no proposal')
    for reason in pred['reasons']:
        st.write('• '+adapter.reason_text(reason))

st.subheader('Partial relationship chart')
mode = st.radio('Chart scope', ['Selected employee', 'Connected component', 'Company overview'], horizontal=True)
limit = st.slider('Overview node limit · all employees remain in the directory', 20, 220, 60, step=20) if mode=='Company overview' else 40
dot,n,e = adapter.graph_dot(data,eid,mode,limit)
st.graphviz_chart(dot, width='stretch' if mode == 'Company overview' else 'content')
st.caption(f'{n} visible nodes · {e} dashed experimental edges in this view. Arrows point from possible manager to employee. Disconnected employees have no displayed proposal; the chart is not a complete hierarchy. Select another employee to navigate.')
st.download_button('Download full company proposal graph', json.dumps(data['graph'],indent=2), 'experimental_graph.json')
st.subheader('Evidence and source documents')
claim_ids = pred['evidence_claim_ids']
if not claim_ids:
    st.write('No sufficient evidence bundle supports a selected manager. The following unranked candidates, if any, are retained for inspection.')
for c in pred['candidates']:
    with st.expander('Unranked candidate · '+adapter.display(c.get('manager_name'))):
        st.write('Visible contact' if c.get('manager_id') in people else 'Cannot resolve to a visible contact')
        for reason in c.get('reasons',[]): st.write(adapter.reason_text(reason))
        for claim,doc in adapter.evidence(data,c.get('claim_ids',[])):
            st.write(claim['quote'])
            st.caption(f'Considered candidate evidence, not confirmation · source {doc["source_id"]} · family {doc["document_family_id"]} · span [{claim["span_start"]}, {claim["span_end"]})')
            st.caption(f'Published: {adapter.display(doc.get("published_at"))} · Available: {adapter.display(doc.get("available_at"))} · Retrieved: {adapter.display(doc.get("retrieved_at"))}')
            st.text(doc['text'])
for claim,doc in adapter.evidence(data,claim_ids):
    publication_label = doc["published_at"][:10] if doc.get("published_at") else "Date unavailable"
    with st.expander(f'{doc["document_kind"].replace("_"," ").title()} · {publication_label}', expanded=bool(r['proposed_manager_id'])):
        st.write(claim['quote'])
        st.caption(f'Exact span [{claim["span_start"]}, {claim["span_end"]}) · source {doc["source_id"]} · family {doc["document_family_id"]}')
        st.caption(f'Published: {adapter.display(doc.get("published_at"))} · Available: {adapter.display(doc.get("available_at"))} · Retrieved: {adapter.display(doc.get("retrieved_at"))}')
        st.caption(f'Effective: {adapter.display(claim.get("effective_from"))} to {adapter.display(claim.get("effective_to"))} · provenance: {doc["provenance_status"]}')
        st.text(doc['text'])
with st.expander('Technical details · original stored prediction'):
    st.json(pred)
