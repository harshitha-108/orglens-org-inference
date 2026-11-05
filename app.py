"""Assessment-focused presentation of unchanged frozen recovery proposals."""
import json
import hashlib
import csv
import io
import streamlit as st
import adapter
from confidence import evidence_strength
from streamlit.components.v1 import declare_component
from chart_layout import chart_payload

company_chart = declare_component("recovery_company_chart", path=str(adapter.ROOT / "chart_component"))

st.set_page_config(page_title="OrgLens | Explore Organisations", page_icon="◈", layout="wide")
st.markdown("""<style>
.block-container{padding-top:1.15rem;max-width:1680px;padding-bottom:3rem}[data-testid="stSidebar"]{background:#142942;color:#eef5ff}[data-testid="stSidebar"] p,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] label{color:#eef5ff}
h1,h2,h3{letter-spacing:-.025em}h1{margin-bottom:0}
div[data-testid="stMetric"]{background:#edf5f6;border:1px solid #dae9ed;border-radius:12px;padding:14px}
div[data-testid="stMetricLabel"] p{white-space:normal}
.kicker{font-size:.75rem;letter-spacing:.12em;color:#337b85;font-weight:650;margin-bottom:4px}
.pipeline{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;padding:0;list-style:none}
.pipeline li{background:#edf5f6;border-top:3px solid #008b8b;border-radius:8px;padding:16px}
[data-testid="stGraphVizChart"]{max-width:100%}\n.pipeline b{display:block;margin:6px 0}.pipeline small{line-height:1.5}
@media(max-width:720px){.block-container{padding:1rem}.pipeline{grid-template-columns:1fr}.pipeline li{padding:12px}}
.explore-hero{background:#142942;color:#f2f7ff;border-radius:14px;padding:8px 16px}
.explore-hero>span{font-size:11px;font-weight:700;letter-spacing:.12em;color:#9ce2df}
.explore-hero h1{color:white;font-size:1.8rem;padding:.25rem 0;margin:0}
.explore-hero p{color:#d3e1ef;margin:0;font-size:.91rem}
.st-key-reporting_workspace,.st-key-employee_profile{background:#fff;border-radius:12px}
.st-key-reporting_workspace [data-testid="stVerticalBlock"],.st-key-employee_profile [data-testid="stVerticalBlock"]{gap:.65rem}
.st-key-employee_profile [data-testid="stText"]{white-space:pre-wrap;overflow-wrap:anywhere}
@media(max-width:720px){.explore-hero{padding:12px 15px}.explore-hero h1{font-size:1.4rem}}
.st-key-company_summary [data-testid="stMetric"],.st-key-company_picker{height:100px;min-height:100px;background:#f0f6fa;border:1px solid #dce7ef;border-radius:12px;padding:12px;box-sizing:border-box}
.st-key-company_summary [data-testid="stMetricLabel"],.st-key-company_picker label{min-height:2.4rem;display:flex;align-items:flex-start;margin:0}
.st-key-company_summary [data-testid="stMetricLabel"],.st-key-company_summary [data-testid="stMetricLabel"] *{white-space:normal!important;overflow:visible!important;text-overflow:clip!important;min-width:0}
.st-key-company_summary [data-testid="stMetricValue"]{font-size:1.65rem}
@media(max-width:720px){.st-key-company_summary [data-testid="stHorizontalBlock"]{flex-wrap:wrap}.st-key-company_summary [data-testid="stColumn"]{min-width:100%!important}.st-key-company_summary [data-testid="stMetric"],.st-key-company_picker{height:auto;min-height:78px}.st-key-company_summary [data-testid="stMetricLabel"],.st-key-company_picker label{min-height:0}}
.st-key-company_picker [data-baseweb="select"]>div,.st-key-company_picker .react-aria-ComboBox div:has(>input){background:#d7eaf7!important;border:2px solid #4d718c!important;border-radius:9px}
.st-key-company_picker [data-baseweb="select"]>div:focus-within,.st-key-company_picker .react-aria-ComboBox div:has(>input):focus-within{border-color:#087f86;box-shadow:0 0 0 3px #b5dfdf}
.st-key-company_picker svg{color:#23445f}
.st-key-employee_profile h3{color:#173e59}
@media(max-width:720px){.st-key-reporting_workspace,.st-key-employee_profile{min-width:0}}
</style>""", unsafe_allow_html=True)
st.sidebar.header("OrgLens")
st.sidebar.caption("COMPANY INTELLIGENCE")
nav=st.sidebar.radio("Workspace",["Explore Organisations","Focused Recovery","How It Works"],key="workspace")
st.sidebar.caption("Synthetic companies · experimental research")
if nav=="Explore Organisations":
    st.markdown("""<header class="explore-hero">
    <span>ORGLENS / COMPANY INTELLIGENCE</span>
    <h1>Explore Organisations</h1>
    <p>Explore possible reporting lines and inspect the sources behind them.</p>
    </header>""",unsafe_allow_html=True)
else:
    st.markdown('<div class="kicker">SYNTHETIC DATA · EXPERIMENTAL PRODUCT</div>',unsafe_allow_html=True)
    st.title("OrgLens")
    st.write("From a flat employee list to possible reporting relationships—with the source evidence behind every suggestion.")
    st.divider()

@st.cache_data(max_entries=12)
def company(cid,db_path):
    return adapter.load_company(cid,db_path)

@st.cache_data
def catalogue(db_path):
    return adapter.catalogue(db_path)

@st.cache_data
def metrics(name):
    return json.loads((adapter.ROOT/"evidence"/name).read_text())

@st.cache_data
def checked_focused_release():
    release=metrics("focused_release.json")
    assert release["scale_gate_pass"] and release["heldout_validation_gate_pass"]
    for rel,expected in release["files_sha256"].items():
        assert hashlib.sha256((adapter.ROOT/rel).read_bytes()).hexdigest()==expected
    return release

release=checked_focused_release()
db_path=adapter.ROOT/"runtime/recovery_focused.sqlite"
 
def table_csv(headers, rows):
    """Write an Excel-friendly table and neutralise spreadsheet formulas."""
    output=io.StringIO()
    writer=csv.writer(output)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(["'"+v if isinstance(v,str) and v.lstrip().startswith(("=","+","-","@")) else v for v in row])
    return output.getvalue().encode("utf-8-sig")

if nav=="Focused Recovery":
    st.header("Focused recovery · fresh 500-company scale-up")
    st.write("These frozen synthetic results match the selected runtime. The previous scale-up is a different cohort, not a paired comparison.")
    full=metrics("focused_scale_metrics.json");v=full["views"]["messy"];stats=release["stats"]
    assert (stats["companies"],stats["employees"],stats["proposals"])==(len(full["companies"]),v["employees"],v["selected"])
    a,b,c,d=st.columns(4)
    a.metric("Scored precision",f'{v["precision"]:.2%}')
    b.metric("Employee coverage",f'{v["coverage"]:.2%}')
    c.metric("Candidate recall · manager visible",f'{v["full_pool_recall"]:.2%}')
    d.metric("Correct two-link chains",f'{v["correct_two_hop"]:,}')
    st.write(f'**{stats["companies"]} companies · {v["employees"]:,} visible employees · {v["selected"]:,} proposals**')
    st.write(f'{v["correct"]:,} correct · {v["wrong"]:,} wrong · {v["unknown_selected"]:,} unscorable · {v["unresolved"]:,} unresolved. Structural violations: {v["structural_violations"]}.')
    st.write(f'{v["correct_two_hop"]:,} employees have a correct two-edge reporting chain, out of {v["available_two_hop_employees"]:,} with a scorable visible chain available.')
    st.caption(f'Precision: {v["correct"]:,} of {v["correct"]+v["wrong"]:,} scored proposals. Coverage uses all visible employees. Recall counts employees whose true manager is visible.')
    st.info("These results are synthetic. Observed precision does not guarantee real-world performance. OrgLens leaves managers unresolved when evidence is insufficient. Each proposal shows an evidence rating. Calibrated individual probabilities are unavailable. Sources support suggestions, not independently confirmed reporting lines. Confirmed lines: 0.")
    st.subheader("Independent validation · same 30 fresh companies")
    paired=metrics("focused_validation_metrics.json")
    st.table([{"Arm":label,"Precision":f'{m["precision"]:.2%}',"Coverage":f'{m["coverage"]:.2%}',"Candidate recall":f'{m["full_pool_recall"]:.2%}',"Correct two-edge chains":m["correct_two_hop"]} for label,key in [("Baseline","baseline"),("Focused","focused")] for m in [paired[key]["views"]["messy"]]])
    with st.expander("Previous frozen scale-up · different companies"):
        prev=metrics("scale_metrics.json")["views"]["messy"]
        st.write(f'{prev["employees"]:,} employees · {prev["selected"]:,} proposals · {prev["precision"]:.2%} precision · {prev["coverage"]:.2%} coverage · {prev["full_pool_recall"]:.2%} candidate recall.')
    with st.expander("Methodology and limitations"):
        st.write("Synthetic disclosure and error assumptions limit generalisation. The paired validation measures the combined publication, extraction and guard changes, not the effect of each change. No real-world validation or calibrated individual probabilities are available.")
        st.write("Two-edge chains count only when both selected edges match scorable synthetic truth. Unknown truth is excluded from precision but included in coverage. Original stricter publication requirements are not satisfied.")
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
    with st.expander("What supports a suggestion?"):
        st.write("A source identifies an employee’s team. Another source describes a named person’s people-management responsibility for that team. Dates, identity resolution and competing responsibilities must also be compatible.")
        st.write("A senior title, a shared department or project leadership alone does not establish a direct manager. The pipeline may abstain.")
    with st.expander("Source provenance and evaluation safeguards"):
        st.write("Every selected proposal has exact quotes, document IDs, dates and copy-family provenance. Fixed seeds and frozen code, inputs and predictions make the synthetic evaluation reproducible. The runtime contains no hidden manager labels or per-person correctness verdicts.")
        st.write("Source independence and company realism are modelling assumptions, not external validation. Inferred reporting paths do not prove purchasing authority.")
    st.write("Focused recovery adds dated staff registers derived from pre-reporting facts. Leadership-team duties are matched only to leadership-team membership; provider affiliations cannot independently justify a proposal.")
    st.subheader("Source code & documentation")
    st.markdown("[Current experimental app source](https://github.com/harshitha-108/orglens-recovery-experimental) · [Original assessment repository and write-up](https://github.com/harshitha-108/orglens) · [Historical v1 AI-usage record](https://github.com/harshitha-108/orglens/blob/main/docs/AI_USAGE.md)")
    st.caption("The original repository describes historical v1. Check the experimental repository README for recovery source, documentation and the exact reproduction steps that were tested. These versions are not interchangeable.")
    st.stop()

rows=catalogue(str(db_path))
labels={cid:f'{case.replace("company_","Company ")} · {n} employees' for cid,case,n in rows}
with st.container(key="company_summary"):
    selector,a,b,c=st.columns([1.45,1,1,1],gap="small")
    with selector, st.container(key="company_picker"):
        company_key="focused_company"
        saved_key=f"{company_key}_saved"
        if company_key not in st.session_state:
            st.session_state[company_key]=st.session_state.get(saved_key,next(iter(labels)))
        cid=st.selectbox("Company · 500 available",list(labels),format_func=labels.get,key=company_key)
        st.session_state[saved_key]=cid
    data=company(cid,str(db_path))
    people={p["employee_id"]:p for p in data["contacts"]}
    relations={r["employee_id"]:r for r in data["relationships"]}
    evidence_chart=chart_payload(data)
    count=len(evidence_chart["edges"])
    unresolved=[eid for eid,r in relations.items() if r["proposed_manager_id"] is None]
    a.metric("Visible employees",len(people))
    b.metric("Proposed reporting lines",count)
    c.metric("Employees without a manager proposal",len(unresolved))
key=f"employee_{cid}"
revision=f"focus_{cid}"
if key not in st.session_state:
    st.session_state[key]=evidence_chart["edges"][0][1] if count else next(iter(people))

def employee_label(eid):
    person=people[eid]
    return f'{person["display_name"]} · {adapter.display(person.get("title"),"Job title not listed")} · {eid[:6]}'

def select_employee(widget_key):
    eid=st.session_state[widget_key]
    if eid in people:
        st.session_state[key]=eid
        st.session_state[revision]=st.session_state.get(revision,0)+1

search_key=f"find_{cid}"
chart,detail=st.columns([7,3],gap="small")
with chart, st.container(key="reporting_workspace",border=True):
    st.subheader("Organisation workspace")
    payload=evidence_chart
    st.caption("Dashed lines show evidence-based suggestions, not confirmed reports. Employees without chart links are still searchable.")
    st.selectbox("Find an employee by name or job title",list(people),index=None,format_func=employee_label,key=search_key,on_change=select_employee,args=(search_key,),placeholder="Type a name or title")
    if payload["nodes"]:
        mode="evidence"
        event_key=f"event_{cid}_{mode}"
        event=company_chart(company=cid,payload=payload,selected=st.session_state[key],focus_revision=st.session_state.get(revision,0),key=f"chart_{cid}_{mode}",default=None)
        if isinstance(event,dict) and event.get("event") and event.get("event")!=st.session_state.get(event_key) and event.get("id") in people:
            st.session_state[event_key]=event["event"]
            st.session_state[key]=event["id"]
            st.rerun()
        if st.session_state[key] not in {n["id"] for n in payload["nodes"]}:
            st.info("This employee has no linked node. See their profile for details.")
    else:
        st.info("No suggested reporting links for this company. Browse the employee directory to see employees and why evidence was insufficient.")
    linked={n["id"] for n in payload["nodes"]}
    isolated=[eid for eid in people if eid not in linked]
    with st.expander(f"Employees outside the chart · {len(isolated)}",expanded=not count):
        if isolated:
            tray_key=f"isolated_{cid}"
            st.selectbox("Search employees outside the chart",isolated,index=None,format_func=employee_label,key=tray_key,on_change=select_employee,args=(tray_key,),placeholder="Type a name or title")
        st.caption("This directory excludes tree roots: an employee with proposed direct reports remains on the chart even without a proposed manager.")
    if count:
        st.download_button("Download reporting lines (CSV for Excel)",table_csv(
            ["Employee","Employee title","Suggested manager","Manager title","Status"],
            [(people[e]["display_name"],adapter.display(people[e].get("title")),people[m]["display_name"],
              adapter.display(people[m].get("title")),"Unverified proposal") for m,e in payload["edges"]]
        ),"orglens-reporting-lines.csv","text/csv")
eid=st.session_state[key]
r=relations[eid];pred=r["prediction"]
with detail:
    with st.container(key="employee_profile",border=True):
        person=people[eid]
        manager=r["proposed_manager_id"]
        st.caption("EMPLOYEE PROFILE")
        st.subheader(person["display_name"])
        st.caption(adapter.display(person.get("title"),"Job title not listed"))
        if not person.get("title") or (manager and not people[manager].get("title")):
            st.caption("A missing job title does not rule out a suggestion. Team records can show where someone works and who manages that team.")
        if manager:
            st.markdown("**Suggested direct manager**")
            st.write(people[manager]["display_name"])
            st.caption(adapter.display(people[manager].get("title"),"Job title not listed"))
            st.caption("Suggested from the available records. The reporting line is not confirmed.")
        else:
            st.markdown("**Manager unresolved — insufficient evidence**")
        claims=adapter.evidence(data,pred["evidence_claim_ids"])
        rating=evidence_strength(pred,claims)
        if rating:
            label, explanation=rating
            st.markdown(f"**Evidence strength · {label}**")
            st.caption(explanation)
            st.caption("This describes the source records. It is not a probability that the suggestion is correct.")

        member=next((c for c,_ in claims if c["kind"]=="membership"),None)
        duty=next((c for c,_ in claims if c["kind"]=="people_accountability"),None)
        if manager and member and duty:
            st.write(f'The records list this employee on {member.get("team_raw") or "a team"} and name the suggested manager as responsible for staff on that team.')
        elif manager:
            st.write("The sources below support this suggestion without confirming a reporting line.")
        else:
            st.write("Available records do not provide enough evidence to identify a direct manager.")
        reports=[people[e]["display_name"] for m,e in evidence_chart["edges"] if m==eid]
        if reports:
            st.markdown(f"**Proposed direct reports · {len(reports)}**")
            st.write(", ".join(reports))
        if claims:
            st.markdown("**Why this manager was suggested**")
            for quote in dict.fromkeys(c["quote"] for c,_ in claims):
                st.markdown("> " + quote.replace("\n", "\n> "))
if claims:
    with st.expander(f"Original records for {person['display_name']}"):
        st.caption("Open these records if you want to check where the quotes came from.")
        for claim,doc in claims:
            st.caption(f'Source {doc["source_id"]} · family {doc["document_family_id"]} · exact text span [{claim["span_start"]}, {claim["span_end"]})')
            st.caption(f'Published: {adapter.display(doc.get("published_at"))} · Available: {adapter.display(doc.get("available_at"))} · Retrieved: {adapter.display(doc.get("retrieved_at"))}')
            st.caption(f'Effective: {adapter.display(claim.get("effective_from"))} to {adapter.display(claim.get("effective_to"))} · {adapter.display(doc.get("provenance_status"))}')
            st.text(doc["text"])
