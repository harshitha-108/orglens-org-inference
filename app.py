"""Assessment-focused presentation of unchanged frozen recovery proposals."""
import json
import streamlit as st
import adapter

st.set_page_config(page_title="OrgLens | Explore Organisations", page_icon="◈", layout="wide")
st.markdown("""<style>
.block-container{padding-top:1.6rem;max-width:1320px;padding-bottom:3rem}
h1,h2,h3{letter-spacing:-.025em}h1{margin-bottom:0}
div[data-testid="stMetric"]{background:#edf5f6;border:1px solid #dae9ed;border-radius:12px;padding:14px}
div[data-testid="stMetricLabel"] p{white-space:normal}
.kicker{font-size:.75rem;letter-spacing:.12em;color:#337b85;font-weight:650;margin-bottom:4px}
.pipeline{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px;padding:0;list-style:none}
.pipeline li{background:#edf5f6;border-top:3px solid #008b8b;border-radius:8px;padding:16px}
[data-testid="stGraphVizChart"]{max-width:100%}\n.pipeline b{display:block;margin:6px 0}.pipeline small{line-height:1.5}
@media(max-width:720px){.block-container{padding:1rem}.pipeline{grid-template-columns:1fr}.pipeline li{padding:12px}}
</style>""", unsafe_allow_html=True)
st.markdown('<div class="kicker">SYNTHETIC DATA · EXPERIMENTAL PRODUCT</div>',unsafe_allow_html=True)
st.title("OrgLens")
st.write("From a flat employee list to possible reporting relationships—with the source evidence behind every suggestion.")
nav=st.radio("Workspace",["Explore Organisations","Model Performance","How It Works"],horizontal=True,key="workspace")
st.divider()

@st.cache_data(max_entries=12)
def company(cid):
    return adapter.load_company(cid)

@st.cache_data
def catalogue():
    return adapter.catalogue()

@st.cache_data
def metrics(name):
    return json.loads((adapter.ROOT/"evidence"/name).read_text())

def source_panel(data,claim_ids,expanded=False):
    for claim,doc in adapter.evidence(data,claim_ids):
        kind=doc["document_kind"].replace("_"," ").title()
        date=doc["published_at"][:10] if doc.get("published_at") else "Date unavailable"
        with st.container(border=True):
            st.caption(kind+" · "+date)
            st.write(claim["quote"])
            with st.expander("View original document & citation",expanded=expanded):
                st.caption(f'Source {doc["source_id"]} · family {doc["document_family_id"]}')
                st.caption(f'Exact text span [{claim["span_start"]}, {claim["span_end"]})')
                st.caption(f'Published: {adapter.display(doc.get("published_at"))} · Available: {adapter.display(doc.get("available_at"))} · Retrieved: {adapter.display(doc.get("retrieved_at"))}')
                st.caption(f'Effective: {adapter.display(claim.get("effective_from"))} to {adapter.display(claim.get("effective_to"))}')
                st.caption('Provenance: synthetic source. Copy-family identifiers are scoped to this company; independence is a modelling assumption.')
                st.text(doc["text"])

if nav=="Model Performance":
    st.header("What the system gets right—and where it stops")
    st.write("Frozen evaluation of the messy-source, 500-company synthetic scale-up. These are dataset-level measurements, not confidence in an individual manager.")
    m=metrics("scale_metrics.json");v=m["views"]["messy"]
    a,b,c=st.columns(3)
    a.metric("Precision · selected, scored proposals",f'{v["precision"]:.2%}')
    b.metric("Coverage · all visible employees",f'{v["coverage"]:.2%}')
    c.metric("Candidate recall · manager visible",f'{v["full_pool_recall"]:.2%}')
    a.caption("Of the proposals we can score, how many match synthetic truth?")
    b.caption("For how many employees did the system make any proposal?")
    c.caption("How often did the candidate pool contain a correct visible manager?")
    st.caption("OrgLens deliberately leaves some employees without a suggested manager when the available evidence is insufficient.")
    st.write("**500 companies · 74,612 employees · 9,004 proposals · 466 companies with proposals**")
    st.write("8,641 correct · 360 wrong · 3 unscorable. Precision uses 9,001 scored proposals. Coverage includes all 9,004. Structural violations: 0.")
    st.info("Individual confidence: unavailable. There are no calibrated probabilities for these proposals. Published or independently confirmed relationships: 0.")
    st.subheader("Separate independent synthetic validation")
    independent=metrics("validation_metrics.json")["views"]["messy"]
    with st.container(border=True):
        st.write("**30 fresh, company-disjoint companies · evaluated before the 500-company scale-up**")
        st.write(f'{independent["employees"]:,} visible employees · {independent["correct"]} correct and {independent["wrong"]} wrong proposals · {independent["precision"]:.2%} precision · {independent["coverage"]:.2%} coverage.')
        st.caption("This is the independent synthetic validation. The 500-company scale-up is not another holdout, and neither establishes real-company accuracy.")
    with st.expander("Limitations that matter"):
        st.write("• Low-disclosure precision is 88.31%; less public information makes inference harder.\n• All 360 scored errors cite misleading provider affiliations. A citation can be wrong.\n• Co-management is not solved: 30 co-managed cases receive wrong proposals.\n• Missing evidence limits recall and coverage. Abstention is deliberate, but does not guarantee that every selected edge is correct.")
        st.write("Original internal publication gates remain unmet: 95% retrieval, 15% coverage, calibration and targeted manager-removal testing. Suggestions must remain experimental.")
    with st.expander("Evaluation details & frozen results"):
        interval=m["bootstrap"]["messy"]["precision_interval95"]
        st.write(f'Company-cluster 95% precision interval: {interval[0]:.2%}–{interval[1]:.2%}. Unknown truth is excluded from correctness, not from coverage. No errors were removed from this app.')
        st.caption("The original evaluator retains an inherited 15-company scope sentence. The verified scale-up file contains 500 company records; its totals and hash match the authoritative scale-up freeze.")
        st.download_button("Download 500-company results",(adapter.ROOT/"evidence/scale_metrics.json").read_bytes(),"scale500_metrics.json")
        st.download_button("Download separate 30-company validation",(adapter.ROOT/"evidence/validation_metrics.json").read_bytes(),"validation30_metrics.json")
    st.stop()

if nav=="How It Works":
    st.header("Evidence first. A reporting line only when supported.")
    st.write("The app reads frozen source-only predictions. It does not generate new predictions while you browse.")
    st.markdown("""<ol class="pipeline">
<li><small>01 · ORGANISATION</small><b>Create organisational facts</b><small>Teams, memberships and people-management responsibilities exist before reporting truth is selected.</small></li>
<li><small>02 · OBSERVATION</small><b>Publish imperfect sources</b><small>Biographies, directories and responsibility pages may be missing, stale or contradictory.</small></li>
<li><small>03 · EXTRACTION</small><b>Keep exact evidence</b><small>Extract named people, team membership and accountability with source dates and text spans.</small></li>
<li><small>04 · INFERENCE</small><b>Propose or abstain</b><small>Combine compatible evidence. Shared, missing or conflicting responsibility can remain unresolved.</small></li>
<li><small>05 · EVALUATION</small><b>Score separately</b><small>Freeze predictions before a separate evaluator opens hidden synthetic truth.</small></li>
</ol>""",unsafe_allow_html=True)
    a,b=st.columns(2)
    with a:
        st.subheader("What supports a suggestion?")
        st.write("A source identifies an employee’s team. Another source describes a named person’s people-management responsibility for that team. Dates, identity resolution and competing responsibilities must also be compatible.")
        st.write("A senior title, a shared department or project leadership alone does not establish a direct manager. The pipeline may abstain.")
    with b:
        st.subheader("What makes the work inspectable?")
        st.write("Every selected proposal has exact quotes, document IDs, dates and copy-family provenance. Fixed seeds and frozen code, inputs and predictions make the synthetic evaluation reproducible. The runtime contains no hidden manager labels or per-person correctness verdicts.")
        st.write("Source independence and company realism are modelling assumptions, not external validation. Inferred reporting paths do not prove purchasing authority.")
    st.subheader("Source code & documentation")
    st.markdown("[Current experimental app source](https://github.com/harshitha-108/orglens-recovery-experimental) · [Original assessment repository and write-up](https://github.com/harshitha-108/orglens) · [Historical v1 AI-usage record](https://github.com/harshitha-108/orglens/blob/main/docs/AI_USAGE.md)")
    st.caption("The original repository describes historical v1. Check the experimental repository README for recovery source, documentation and the exact reproduction steps that were tested. These versions are not interchangeable.")
    st.stop()

st.subheader("Explore an organisation")
st.caption("1. Choose a company   →   2. Find an employee   →   3. Inspect the chart and its sources")
rows=catalogue();labels={cid:f'{case.replace("company_","Company ")} · {n} employees' for cid,case,n in rows}
cid=st.selectbox("Choose a company · 500 available",list(labels),format_func=labels.get,key="company")
data=company(cid);people={p["employee_id"]:p for p in data["contacts"]};relations={r["employee_id"]:r for r in data["relationships"]}
count=sum(r["proposed_manager_id"] is not None for r in relations.values())
a,b,c=st.columns(3);a.metric("Employees",len(people));b.metric("Suggested reporting links",count);c.metric("Employees without a proposal",len(people)-count)
st.caption("OrgLens deliberately leaves some employees without a suggested manager when evidence is insufficient.")
st.caption("All companies and people are synthetic. Every suggested link is unverified; 0 links are published or independently confirmed. Individual confidence probabilities are unavailable.")
left,right=st.columns([3,2]);query=left.text_input("Find an employee by name or job title",key=f"search_{cid}");status=right.selectbox("Show employees",["All employees","With proposals","No proposal"],key="filter")
filtered=adapter.search_contacts(data,query,status)
if not filtered:
    st.info("No employees match. Clear the search or choose All employees.");st.stop()
options=[p["employee_id"] for p in filtered];key=f"employee_{cid}"
if key not in st.session_state or st.session_state[key] not in options:
    st.session_state[key]=next((eid for eid in options if relations[eid]["proposed_manager_id"]),options[0])
eid=st.selectbox("Select an employee",options,format_func=lambda x:f'{people[x]["display_name"]} · {adapter.display(people[x].get("title"),"Title unavailable")} · {x[:6]}',key=key)
r=relations[eid];pred=r["prediction"]
chart,detail=st.columns([3,2],gap="large")
with chart:
    st.subheader("Suggested reporting relationships")
    mode=st.radio("Chart view",["Selected employee","Connected component","Company overview"],index=1,format_func=lambda x:{"Selected employee":"Employee links","Connected component":"Connected team","Company overview":"Company overview"}[x],horizontal=True)
    limit=st.slider("Overview node limit",20,220,60,step=20) if mode=="Company overview" else 40
    dot,n,e=adapter.graph_dot(data,eid,mode,limit)
    st.graphviz_chart(dot,width="stretch" if mode=="Company overview" else 360 if n<=3 else "content")
    st.caption(f'{n} displayed employees · {e} proposed links. Dashed arrows run from possible manager to employee. Teal outline: selected employee. The chart is partial; the directory always contains every employee.')
    st.caption("The initial selection opens the first stored proposal when available—not a ranked or truth-selected example.")
with detail:
    with st.container(border=True):
        st.subheader(people[eid]["display_name"])
        st.caption(adapter.display(people[eid].get("title"),"Title unavailable"))
        if r["proposed_manager_id"]:
            st.write("**Suggested manager**")
            st.subheader(people[r["proposed_manager_id"]]["display_name"])
            st.caption("Unverified suggestion · individual confidence unavailable")
            st.write("**Why this suggestion?**")
            st.write("Sources connect this employee’s team membership with this manager’s people-management responsibilities. The frozen rules found compatible evidence; that is a proposal, not confirmation.")
        else:
            st.write("**Manager unresolved · no proposal**")
            st.write("The evidence is not sufficient to select a direct manager safely. This does not mean the employee has no manager.")
            for explanation in dict.fromkeys(adapter.reason_text(code) for code in pred["reasons"]):st.write("• "+explanation)
        st.caption("Project, functional or matrix leadership alone is not a direct reporting line.")
st.subheader("Evidence behind the decision")
if pred["evidence_claim_ids"]:
    source_panel(data,pred["evidence_claim_ids"])
else:
    st.write("There is no sufficient supporting source bundle for a selected manager. Missing, outdated or shared responsibility should remain unresolved.")
if pred["candidates"]:
    with st.expander(f'Other evidence considered · {len(pred["candidates"])} unranked candidate(s)'):
        st.caption("These candidates are not ranked or confirmed. Evidence here may have been rejected.")
        for candidate in pred["candidates"]:
            st.write("**"+adapter.display(candidate.get("manager_name"))+"**")
            st.caption("Visible contact" if candidate.get("manager_id") in people else "Cannot resolve to a visible contact")
            for explanation in dict.fromkeys(adapter.reason_text(code) for code in candidate.get("reasons",[])):st.write(explanation)
            source_panel(data,candidate.get("claim_ids",[]))
with st.expander(f'Company employee directory · {len(filtered)} matching employees'):
    st.dataframe([{"Employee":p["display_name"],"Job title":adapter.display(p.get("title"),"Title unavailable"),"Relationship":"Unverified suggestion" if relations[p["employee_id"]]["proposed_manager_id"] else "No proposal"} for p in filtered],hide_index=True,width="stretch")
with st.expander("Technical details & full company graph"):
    st.caption("Original frozen prediction. Candidate scores and calibrated estimates remain null.")
    st.json(pred)
    st.download_button("Download full company proposal graph",json.dumps(data["graph"],indent=2),"experimental_graph.json")
