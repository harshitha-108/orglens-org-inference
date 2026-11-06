"""Assessment-focused presentation of unchanged frozen recovery proposals."""
import json
import hashlib
from datetime import datetime
from html import escape
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
.pipeline{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px;padding:0;list-style:none}
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
[data-testid="stDialog"]{background:transparent!important;backdrop-filter:none!important}
[data-testid="stDialog"] > div:has([role="dialog"]){border:1px solid #a9c0d2;box-shadow:0 18px 55px #173e5948}
.st-key-employee_profile [data-testid="stVerticalBlock"]{gap:.5rem}
.profile-identity{display:flex;align-items:center;gap:12px;margin-bottom:8px}
.profile-icon{display:grid;place-items:center;flex:0 0 48px;height:48px;background:#dceef3;color:#17566c;border-radius:14px}
.profile-identity h3{padding:0;margin:0}
.profile-role{color:#52677a;font-size:.9rem}
.profile-manager{padding:4px 0 4px 14px;border-left:3px solid #76a9b5;margin:10px 0 6px;overflow-wrap:anywhere}
.profile-manager small,.profile-manager strong{display:block}
[data-testid="stAppViewContainer"]{background:#f8f8fc}
.st-key-top_navigation{background:#f0effa;border:1px solid #e2e0ef;border-radius:15px;padding:8px 16px}
.brand{font-size:1.45rem;font-weight:750;color:#15133a;white-space:nowrap}
.brand span{color:#5941d1;margin-right:5px}
.st-key-top_navigation [role="radiogroup"]{gap:5px;flex-wrap:wrap}
.st-key-top_navigation label:has(input[type="radio"]){border-radius:8px;padding:6px 10px;margin:0}
.st-key-top_navigation label:has(input:checked){background:#563fc9}
.st-key-top_navigation label:has(input:checked) p{color:white}
.st-key-top_navigation label:has(input[type="radio"]) > div:first-child{position:absolute;opacity:0}
.st-key-top_navigation label:focus-within{outline:2px solid #745ee0;outline-offset:2px}
.explore-hero{background:transparent;padding:8px 0;color:#15133a}
.explore-hero h1{color:#15133a}.explore-hero p{color:#454664}
.st-key-company_picker{height:auto;min-height:0;background:transparent;border:0;padding:0}
.st-key-company_picker [data-baseweb="select"]>div,.st-key-company_picker .react-aria-ComboBox div:has(>input){background:white!important;border:1px solid #c9c8df!important}
.st-key-company_summary{background:#f4f4fa}
.company-facts{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}
.company-facts>div{display:grid;align-content:start;gap:2px;padding:8px 12px;border:1px solid #e1ddef;border-radius:10px;background:#f1effa;color:#454664;font-size:.82rem;line-height:1.25}
.company-facts strong{color:#17133e;font-size:1.4rem}
.st-key-company_summary{background:transparent}
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"]{gap:.75rem}
.explore-hero{padding:3px 0}
@media(max-width:620px){.company-facts{grid-template-columns:repeat(3,minmax(0,1fr));gap:5px}.company-facts>div{padding:7px;font-size:.74rem}}

div[data-testid="stMetric"],.pipeline li{background:#f1f0fa;border:1px solid #dedbef;border-radius:12px}
.pipeline li small:first-child{color:#5941d1;font-weight:700}
.profile-icon{background:#eae4ff;color:#563fc9}
.profile-manager{background:#f4f2fd;border-color:#8b73ed;padding:8px 12px;border-radius:6px}
.rating-chip{justify-self:start;border-radius:6px;padding:3px 8px;font-weight:650;background:#e8e3ff;color:#362586}
.rating-0{background:#d5f3df;color:#155536}.rating-1{background:#dfebff;color:#20488a}.rating-2{background:#fff0c9;color:#65470c}
[data-testid="stDialog"] > div:has([role="dialog"]){
    position:fixed;top:0;right:0;bottom:0;left:auto;margin:0;
    width:min(500px,100vw);max-width:100vw;height:100dvh;max-height:100dvh;
    border-radius:14px 0 0 14px;overflow-y:auto;
    animation:profile-slide-in .22s ease-out both
}
@keyframes profile-slide-in{from{transform:translateX(100%)}to{transform:translateX(0)}}
@media(prefers-reduced-motion:reduce){
    [data-testid="stDialog"] > div:has([role="dialog"]){animation:none}
}
@media(max-width:1000px){.pipeline{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:620px){.pipeline{grid-template-columns:1fr}.st-key-top_navigation{padding:8px}}
.block-container{padding-top:3.6rem;max-width:1600px;padding-bottom:1.5rem}
.st-key-top_navigation label:has(input[type="radio"]) input{position:absolute;opacity:0}
.st-key-top_navigation label:has(input[type="radio"]) > div:has(> input),.st-key-top_navigation label:has(input[type="radio"]) > span:has(> input){display:contents}
.profile-counts{display:flex;flex-wrap:wrap;align-items:center;gap:7px 10px;color:#17143d;font-size:.82rem}
.profile-counts span{background:#f3f3fa;border:1px solid #e4e2ef;border-radius:8px;padding:5px 9px}
.profile-confidence{background:#f0effc;border:1px solid #e9e5fb;border-radius:10px;padding:11px 14px;color:#15133a;font-size:.87rem}
.pipeline{gap:20px;margin:12px 0 18px;padding:0!important}
.pipeline li{position:relative;background:white;text-align:center;padding:18px 12px;list-style:none}
.pipeline-icon{display:grid;place-items:center;width:44px;height:44px;margin:0 auto 10px;border-radius:12px;background:#efebfd;color:#563fc9}
.pipeline-icon svg{width:25px;height:25px}
.pipeline li b{font-size:.87rem}.pipeline li small{display:block;font-size:.8rem;line-height:1.4}
@media(min-width:1001px){.pipeline li:not(:last-child)::after{content:"→";position:absolute;right:-17px;top:42%;color:#6655a9}}
.profile-confidence{display:flex;flex-wrap:wrap;align-items:center;gap:7px 10px;padding:10px 12px}
.profile-confidence small{flex-basis:100%;color:#565370}
.st-key-employee_profile [data-testid="stVerticalBlock"]{gap:.65rem}
.profile-counts{margin:3px 0 12px}
.profile-confidence{margin-bottom:14px}
.st-key-employee_profile [data-testid="stMarkdownContainer"] blockquote{
    margin:8px 0;padding:6px 0 6px 12px;color:#50566f
}
.st-key-employee_profile [data-testid="stMarkdownContainer"] blockquote p{margin:0}
.st-key-company_summary{margin-bottom:8px}
.st-key-company_picker,.company-facts>div{min-height:80px;box-sizing:border-box}
.st-key-company_picker{padding:8px 12px;background:#f1effa;border:1px solid #e1ddef;border-radius:10px}
.st-key-company_picker label{min-height:0}
@media(max-width:720px){.st-key-company_picker,.company-facts>div{min-height:0}}
</style>""", unsafe_allow_html=True)
with st.container(key="top_navigation"):
    brand, navigation = st.columns([1, 4], vertical_alignment="center")
    with brand:
        st.markdown('<div class="brand"><span aria-hidden="true">♧</span> OrgLens</div>', unsafe_allow_html=True)
    with navigation:
        nav = st.radio("Workspace", ["Explore Organisations", "Model Performance", "How It Works"],
                       horizontal=True, label_visibility="collapsed", key="workspace",
                       format_func=lambda page: {"Explore Organisations":"◇  Explore Organisations",
                                                 "Model Performance":"▥  Model Performance",
                                                 "How It Works":"▤  How It Works"}[page])

page_description = {
    "Explore Organisations": "Browse company hierarchies, explore suggested reporting lines, and view the supporting evidence.",
    "Model Performance": "See how well OrgLens recovered reporting relationships in the synthetic evaluation.",
    "How It Works": "Follow the data, method and evidence behind each reporting suggestion.",
}
st.markdown(f'<header class="explore-hero"><h1>{nav}</h1><p>{page_description[nav]}</p></header>',
            unsafe_allow_html=True)

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

if nav=="Model Performance":
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
    st.info("These results are synthetic. Observed precision does not guarantee real-world performance. OrgLens leaves managers unresolved when evidence is insufficient.")
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
    st.write("The app reads frozen source-only predictions. It does not generate new predictions while you browse.")
    steps = [
        ('<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 4 16 4 16 0V5M4 12c0 4 16 4 16 0"/>', "Generate data", "Create synthetic companies with a known reporting structure."),
        ('<path d="M6 3h8l4 4v14H6zM14 3v5h4M9 12h6m-6 4h6"/>', "Build evidence", "Collect team and management signals from observable records."),
        ('<path d="M9 3h6v5H9zM3 16h6v5H3zM15 16h6v5h-6zM12 8v4M6 16v-4h12v4"/>', "Infer reporting lines", "Suggest a manager when the evidence supports a match."),
        ('<path d="M12 22s7-3 7-10V5l-7-3-7 3v7c0 7 7 10 7 10zM9 12l2 2 4-4"/>', "Rate confidence", "Describe the support behind each suggested relationship."),
        ('<path d="M4 21h16M6 17v-5m6 5V8m6 9V4"/>', "Evaluate", "Compare saved suggestions against the synthetic ground truth."),
    ]
    cards = [
        f'<li><span class="pipeline-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">{icon}</svg></span>'
        f'<b>{index}. {title}</b><small>{description}</small></li>'
        for index, (icon, title, description) in enumerate(steps, 1)
    ]
    st.markdown('<ol class="pipeline">' + ''.join(cards) + '</ol>', unsafe_allow_html=True)
    with st.expander("What supports a suggestion?"):
        st.write("A source identifies an employee’s team. Another source describes a named person’s people-management responsibility for that team. Dates, identity resolution and competing responsibilities must also be compatible.")
        st.write("A senior title, a shared department or project leadership alone does not establish a direct manager. The pipeline may abstain.")
    with st.expander("Source provenance and evaluation safeguards"):
        st.write("Every selected proposal has exact quotes, document IDs, dates and copy-family provenance. Fixed seeds and frozen code, inputs and predictions make the synthetic evaluation reproducible. The runtime contains no hidden manager labels or per-person correctness verdicts.")
        st.write("Source independence and company realism are modelling assumptions, not external validation. Inferred reporting paths do not prove purchasing authority.")
    st.write("Focused recovery adds dated staff registers derived from pre-reporting facts. Leadership-team duties are matched only to leadership-team membership; provider affiliations cannot independently justify a proposal.")
    st.subheader("Source code & documentation")
    st.markdown("[Current experimental app source](https://github.com/harshitha-108/orglens-org-inference) · [Original assessment repository and write-up](https://github.com/harshitha-108/orglens) · [Historical v1 AI-usage record](https://github.com/harshitha-108/orglens/blob/main/docs/AI_USAGE.md)")
    st.caption("The original repository describes historical v1. Check the experimental repository README for recovery source, documentation and the exact reproduction steps that were tested. These versions are not interchangeable.")
    st.stop()

rows=catalogue(str(db_path))
labels={cid:f'{case.replace("company_","Company ")} · {n} employees' for cid,case,n in rows}
with st.container(key="company_summary"):
    controls, kpis = st.columns([1, 2.7], gap="small", vertical_alignment="top")
    with controls, st.container(key="company_picker"):
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
    with kpis:
        st.markdown(f"""<div class="company-facts">
            <div><strong>{len(people):,}</strong><span>Visible employees</span></div>
            <div><strong>{count:,}</strong><span>Proposed reporting lines</span></div>
            <div><strong>{len(unresolved):,}</strong><span>Employees without a manager proposal</span></div>
        </div>""", unsafe_allow_html=True)
key=f"employee_{cid}"
revision=f"focus_{cid}"
if key not in st.session_state:
    st.session_state[key]=evidence_chart["edges"][0][1] if count else next(iter(people))

employee_labels = {}
employees_by_label = {}
for eid, person in people.items():
    title = adapter.display(person.get("title"), "Job title not listed")
    label = f'{person["display_name"]} · {title}'
    employees_by_label.setdefault(label, []).append(eid)

for label, employee_ids in employees_by_label.items():
    for index, eid in enumerate(employee_ids, 1):
        employee_labels[eid] = label if len(employee_ids) == 1 else f"{label} ({index})"


def employee_label(eid):
    return employee_labels[eid]


search_key=f"find_{cid}"


def reset_employee_search():
    st.session_state[search_key]=None
    st.session_state[key]=None
    st.session_state[revision]=st.session_state.get(revision,0)+1


def select_employee(widget_key):
    eid=st.session_state[widget_key]
    st.session_state[key]=eid if eid in people else None
    st.session_state[revision]=st.session_state.get(revision,0)+1
    if eid in people:
        st.session_state[f"profile_request_{cid}"]=True


with st.container(key="reporting_workspace",border=True):
    heading, search = st.columns([1,1], gap="small", vertical_alignment="center")
    heading.subheader("Organisation workspace")
    with search:
        unresolved_only=st.checkbox("Search only employees without a manager proposal",
                                    key=f"unresolved_search_{cid}",on_change=reset_employee_search)
        search_options=unresolved if unresolved_only else list(people)
        st.selectbox("Find an employee by name or job title",search_options,index=None,
                     format_func=employee_label,key=search_key,on_change=select_employee,
                     args=(search_key,),placeholder="Type a name or title")
        if st.session_state.get(search_key) is not None:
            st.button("Clear employee search",key=f"clear_search_{cid}",on_click=reset_employee_search)
    payload=evidence_chart
    if payload["nodes"]:
        mode="evidence"
        event_key=f"event_{cid}_{mode}"
        event=company_chart(company=cid,payload=payload,selected=st.session_state[key],focus_revision=st.session_state.get(revision,0),key=f"chart_{cid}_{mode}",default=None)
        if isinstance(event,dict) and event.get("event") and event.get("event")!=st.session_state.get(event_key) and event.get("id") in people:
            st.session_state[event_key]=event["event"]
            st.session_state[key]=event["id"]
            st.session_state[f"profile_request_{cid}"]=True
            st.rerun()
        if st.session_state[key] is not None and st.session_state[key] not in {n["id"] for n in payload["nodes"]}:
            st.info("This employee has no linked node. Open their profile for details.")
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
def publication_date(value):
    if not value or not str(value).strip():
        return "Publication date unavailable"
    try:
        date = datetime.fromisoformat(str(value).strip())
    except ValueError:
        return "Publication date uncertain"
    return f"Published {date.day} {date:%b %Y}"


def supporting_evidence(claims):
    source_labels = {
        "synthetic_company_website": "Synthetic company website",
        "synthetic_company_profile": "Synthetic company profile",
        "synthetic_contact_provider": "Synthetic contact provider",
    }
    explanations = {
        "membership": "This record links the employee to the team.",
        "people_accountability": "This record describes the suggested manager’s responsibility for staff.",
    }
    st.markdown("**Supporting evidence**")
    for claim, doc in claims:
        source_type = adapter.display(doc.get("source_type"), "Source type unavailable")
        label = source_labels.get(source_type, source_type.replace("_", " ").capitalize())
        date = publication_date(doc.get("published_at"))
        explanation = explanations.get(claim["kind"], "This is a source cited for the suggestion.")
        with st.container(border=True):
            st.markdown(
                f'<div><strong>{escape(label)}</strong> · {escape(date)}</div>'
                f'<blockquote style="white-space:pre-wrap;overflow-wrap:anywhere">'
                f'{escape(claim["quote"])}</blockquote>'
                f'<small>{escape(explanation)}</small>',
                unsafe_allow_html=True,
            )

    with st.expander("Technical source details"):
        for number, (claim, doc) in enumerate(claims, 1):
            st.markdown(f"**Record {number}**")
            st.caption(f'Source {doc["source_id"]} · family {doc["document_family_id"]} · exact text span [{claim["span_start"]}, {claim["span_end"]})')
            st.caption(f'Published: {adapter.display(doc.get("published_at"))} · Available: {adapter.display(doc.get("available_at"))} · Retrieved: {adapter.display(doc.get("retrieved_at"))}')
            st.caption(f'Effective: {adapter.display(claim.get("effective_from"))} to {adapter.display(claim.get("effective_to"))} · Provenance: {adapter.display(doc.get("provenance_status"))}')
            flags = ", ".join(claim.get("flags") or [])
            if flags:
                st.caption(f"Evidence flags: {flags}")
            st.text(doc["text"])


@st.dialog("Employee profile", width="medium")
def employee_profile(eid):
    r=relations[eid];pred=r["prediction"]
    with st.container(key="employee_profile"):
        person=people[eid]
        manager=r["proposed_manager_id"]
        name=escape(person["display_name"])
        title=escape(adapter.display(person.get("title"),"Job title not listed"))
        st.markdown(f"""<div class="profile-identity">
            <span class="profile-icon" aria-hidden="true">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                    <circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>
                </svg>
            </span>
            <div><h3>{name}</h3><span class="profile-role">{title}</span></div>
        </div>""",unsafe_allow_html=True)
        manager_name=escape(people[manager]["display_name"]) if manager else "Unresolved"
        manager_title=escape(adapter.display(people[manager].get("title"),"Job title not listed")) if manager else "Insufficient evidence"
        st.markdown(f"""<div class="profile-manager">
            <small>Suggested direct manager</small>
            <strong>{manager_name}</strong>
            <span class="profile-role">{manager_title}</span>
        </div>""",unsafe_allow_html=True)
        claims=adapter.evidence(data,pred["evidence_claim_ids"])
        reports=[people[e]["display_name"] for m,e in evidence_chart["edges"] if m==eid]
        source_count=len({doc["source_id"] for _,doc in claims})
        st.markdown(f"""<div class="profile-counts">
            <span><strong>{len(reports)}</strong> proposed direct reports</span>
            <span><strong>{source_count}</strong> cited documents</span>
        </div>""", unsafe_allow_html=True)
        rating=evidence_strength(pred,claims)
        if rating:
            label, _=rating
            color = {"Corroborated": "rating-0", "Supported": "rating-1",
                     "Supported with caveats": "rating-2"}.get(label, "")
            st.markdown(f"""<div class="profile-confidence">
                <strong>Reporting-line confidence (evidence-based)</strong>
                <span class="rating-chip {color}">{escape(label)}</span>
                <small>Evidence rating only. The reporting line is unconfirmed.</small>
            </div>""", unsafe_allow_html=True)

        if not manager:
            st.caption("Available records do not provide enough evidence to identify a direct manager.")
        if reports:
            st.markdown("**Who may report to this employee**")
            st.write(", ".join(reports))
        if claims:
            supporting_evidence(claims)

if st.session_state.pop(f"profile_request_{cid}", False):
    employee_profile(st.session_state[key])
