from pathlib import Path
import hashlib,json,sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

def test_frozen_source_manifest():
    for rel,entry in json.loads((ROOT/'SOURCE_MANIFEST.json').read_text())['files'].items():
        assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==entry['sha256']

def test_metrics_are_separate_and_correctly_denominated():
    scale=json.loads((ROOT/'evidence/scale_metrics.json').read_text())
    validation=json.loads((ROOT/'evidence/validation_metrics.json').read_text())
    assert len(scale['companies'])==500 and len(validation['companies'])==30
    m=scale['views']['messy']
    assert (m['employees'],m['selected'],m['correct'],m['wrong'],m['unknown_selected'])==(74612,9004,8641,360,3)
    assert m['precision']==8641/9001 and m['coverage']==9004/74612

def test_public_example_has_no_evaluation_truth():
    folder=ROOT/'examples/source_only/company_00'
    assert {p.name for p in folder.iterdir()}=={'clean.json','messy.json','contacts.json'}
    forbidden={'true_manager_id','true_manager_ids','position_id','parent_id','is_correct','technical_audit'}
    def check(value):
        if isinstance(value,dict):
            assert not forbidden&value.keys()
            for child in value.values():check(child)
        elif isinstance(value,list):
            for child in value:check(child)
    for path in folder.glob('*.json'):check(json.loads(path.read_text()))
