from copy import deepcopy
from experiments.product_recovery_v1.focused_improvement.predict import infer
from experiments.product_recovery_v1.focused_improvement.extract import extract

NOW="2026-11-02T00:00:00Z"
CFG={"version":"test","max_source_age_days":180}
CONTACTS=[dict(employee_id=i,display_name=n,title="") for i,n in [('a','Nora Hughes'),('b','Mila Cooper'),('c','Ruby Walsh'),('d','Amir James')]]
def document(i,unit,body,kind='staff_register',source='synthetic_company_website',published=NOW):
    return dict(source_id=i,company_id='fixture',text=f'{unit} | UK\n{body}',source_type=source,document_kind=kind,published_at=published,available_at=NOW,retrieved_at=NOW,valid_from_claimed=None,valid_to_claimed=None,provenance_status='uncorroborated_provider' if source=='synthetic_contact_provider' else 'synthetic_assumption',document_family_id=i,origin_reference='synthetic://fixture',publisher_description='Fixture')
def view(docs):
    return dict(schema_version='orglens-v4-source-observable.1',company_id='fixture',snapshot_id=NOW,as_of=NOW,documents=docs,mentions=[],claims=[],contradiction_records=[])
def run(docs,contacts=CONTACTS):
    return {p['employee_id']:p for p in infer(view(docs),contacts,CFG)['predictions']}
def fixture():
    return [document('1','Service desk','Nora Hughes is assigned to the Service desk team.'),
            document('2','Service desk','Mila Cooper oversees staff appraisals and hiring for the staff team for Service desk.'),
            document('3','Operations','Mila Cooper serves on the leadership team for Operations.'),
            document('4','Operations','Staff appraisals and hiring for the leadership team for Operations are handled by Ruby Walsh.')]
def test_supported_multilevel_chain_and_exact_spans():
    docs=fixture();p=run(docs)
    assert p['a']['manager_id']=='b' and p['b']['manager_id']=='c'
    assert p['a']['calibrated_estimate'] is None
    texts={d['source_id']:d['text'] for d in docs}
    for c in extract(view(docs),CONTACTS):assert texts[c['source_id']][c['span_start']:c['span_end']]==c['quote']
def test_scope_does_not_turn_leadership_into_all_staff():
    docs=fixture()
    docs[2]['text']='Operations | UK\nMila Cooper is assigned to the Operations team.'
    assert run(docs)['b']['manager_id'] is None
def test_competing_or_absent_manager_still_abstains():
    docs=fixture()+[document('5','Service desk','Amir James oversees staff appraisals and hiring for the staff team for Service desk.')]
    assert run(docs)['a']['manager_id'] is None
    assert run(fixture(),[c for c in CONTACTS if c['employee_id']!='b'])['a']['manager_id'] is None
def test_provider_alone_cannot_propose():
    docs=fixture()[1:]
    docs.append(document('provider','Service desk','',kind='biography',source='synthetic_contact_provider'))
    docs[-1]['text']='Nora Hughes. A provider summary lists Service desk as the current team.'
    assert run(docs)['a']['manager_id'] is None
def test_undated_or_unsupported_duties_remain_unresolved():
    docs=fixture();docs[1]['published_at']=None
    assert run(docs)['a']['manager_id'] is None
    docs=fixture();docs[1]['text']='Service desk | UK\nMila Cooper coordinates delivery milestones for Service desk.'
    assert run(docs)['a']['manager_id'] is None
def test_published_unit_mismatch_is_rejected():
    docs=fixture();docs[0]['text']='Different unit | UK\nNora Hughes is assigned to the Service desk team.'
    assert run(docs)['a']['manager_id'] is None
def test_staff_publication_does_not_depend_on_selected_truth():
    from experiments.product_recovery_v1.foundation import build,reporting_truth,project
    from experiments.product_recovery_v1.publication import publish
    from experiments.product_recovery_v1.focused_improvement.publication import staff_projection,supplement
    from experiments.product_recovery_v1.focused_improvement.experiment import BASECFG,CFG,cells
    cell=cells('development')[0];seed=cell['seed']
    ledger,cfg=build(cell['archetype'],cell['generator_index'],seed,cell['target_employees'])
    public,_=project(ledger);_,messy,_=publish(public,BASECFG,seed,cell['disclosure'])
    records=staff_projection(ledger)
    before=supplement(messy,records,CFG,seed,cell['disclosure'],messy=True)
    assert reporting_truth(ledger,cfg,0)['relationships']!=reporting_truth(ledger,cfg,99)['relationships']
    after=supplement(messy,staff_projection(ledger),CFG,seed,cell['disclosure'],messy=True)
    assert before==after and before['documents'][:len(messy['documents'])]==messy['documents']
    new_text='\n'.join(d['text'] for d in after['documents'][len(messy['documents']):])
    assert new_text and all(p['position_id'] not in new_text for p in ledger.read()['positions'])
    assert all(p.employee_id not in new_text for p in public.contacts)
def test_declared_cohort_seeds_are_disjoint_and_fixed():
    from experiments.product_recovery_v1.focused_improvement.experiment import cells
    cohorts=[cells(p) for p in ('development','validation','scale')]
    assert [len(c) for c in cohorts]==[15,30,500]
    seeds=[x['seed'] for c in cohorts for x in c]
    assert len(set(seeds))==545 and min(seeds)>4090899
