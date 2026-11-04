"""Portable orchestration only. Frozen scientific functions are imported unchanged.

Full generation/evaluation commands are supplied but not executed/certified in this
publication-preparation task. verify, plan and infer-example are tested separately.
"""
from pathlib import Path
import argparse, hashlib, json, os, subprocess, sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def write(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8') as f:
        json.dump(obj,f,indent=2);f.write('\n')

def verify():
    manifest=read(ROOT/'SOURCE_MANIFEST.json')
    for rel,entry in manifest['files'].items():
        p=ROOT/rel
        assert p.stat().st_size==entry['bytes'] and sha(p)==entry['sha256'],rel
    print('Verified',len(manifest['files']),'authoritative frozen source/config files')
    return manifest

def output_path(value):
    p=Path(value).resolve()
    if not p.is_relative_to(ROOT/'_reproduction') or p==ROOT/'_reproduction':
        raise ValueError('Outputs must be a fresh subfolder of this package/_reproduction/')
    return p

def predict(source,target,probe):
    subprocess.run([sys.executable,'-B','-m','experiments.product_recovery_v1.inference.run_predict',str(source),str(target),str(probe)],cwd=ROOT,check=True)

def main():
    os.chdir(ROOT)
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='command',required=True)
    commands.add_parser('verify')
    p=commands.add_parser('plan');p.add_argument('--cohort',choices=['scale500','validation30'],default='scale500')
    p=commands.add_parser('infer-example');p.add_argument('--out',default='_reproduction/example')
    p=commands.add_parser('generate');p.add_argument('--cohort',choices=['scale500','validation30'],required=True);p.add_argument('--out',required=True)
    for name in ['predict','evaluate']:
        p=commands.add_parser(name);p.add_argument('--run',required=True)
    args=parser.parse_args();manifest=verify()
    if args.command=='verify':return
    if args.command in {'plan','generate'}:
        cohort=args.cohort
        protocol=read(ROOT/('experiments/product_recovery_v1_scale500/PROTOCOL.json' if cohort=='scale500' else 'experiments/product_recovery_v1_validation/PROTOCOL.json'))
        cells=protocol['companies']
        if args.command=='plan':
            print(json.dumps({'cohort':cohort,'companies':len(cells),'seed_min':min(c['seed'] for c in cells),'seed_max':max(c['seed'] for c in cells),'generation_executed':False},indent=2));return
    if args.command=='infer-example':
        target=output_path(args.out)
        predict(ROOT/'examples/source_only',target,ROOT/'private_not_distributed/truth.json')
        for p in (ROOT/'examples/frozen_predictions/company_00').glob('*.json'):
            assert read(target/'company_00'/p.name)==read(p),p.name
        print('Six scientific outputs match the frozen example as JSON; no truth was supplied.');return
    if args.command=='generate':
        target=output_path(args.out)
        if target.exists():raise ValueError('Refusing generation overwrite')
        from experiments.product_recovery_v1_scale500.run_scale import worker
        target.mkdir(parents=True)
        code={rel:entry['sha256'] for rel,entry in manifest['files'].items()}
        code['tools/reproduce.py']=sha(ROOT/'tools/reproduce.py')
        dataset=target/'dataset';source=target/'source_inputs';summary=[]
        write(dataset/'PRE_GENERATION_FREEZE.json',{'version':protocol['version'],'companies':cells,'portable_source_sha256':code,'warning':'Local generated truth; never publish _reproduction'})
        for cell in cells:
            cell,facts,clean,messy,contacts,truth,master,facts_hash=worker(cell)
            case=f"company_{cell['index']:02}"
            if len(contacts)<100:raise AssertionError('Retain failed output; do not resample')
            for label,view in [('clean',clean),('messy',messy)]:write(source/case/(label+'.json'),view)
            write(source/case/'contacts.json',contacts)
            write(dataset/case/'technical_audit/facts.json',facts)
            write(dataset/case/'technical_audit/truth.json',truth)
            summary.append({'case':case,'master':master,'visible':len(contacts),'facts_sha256':facts_hash})
        hashes={p.relative_to(source).as_posix():sha(p) for p in source.rglob('*.json')}
        write(source/'SOURCE_ONLY_MANIFEST.json',{'files_sha256':hashes,'scope':'Reproduction with frozen seeds/rules, not a new validation cohort'})
        write(target/'PRE_PREDICTION_FREEZE.json',{'code_and_protocol_sha256':code,'truth_used_for_rules':False})
        write(target/'COHORT_SUMMARY.json',summary)
        print('Generated fixed cohort. Run predict and evaluate as separate processes.');return
    target=output_path(args.run)
    if args.command=='predict':
        predict(target/'source_inputs',target/'predictions',target/'dataset/company_00/technical_audit/truth.json');return
    if args.command=='evaluate':
        subprocess.run([sys.executable,'-B','-m','experiments.product_recovery_v1.inference.evaluate',str(target/'source_inputs'),str(target/'predictions'),str(target/'dataset'),str(target/'evaluation')],cwd=ROOT,check=True)

if __name__=='__main__':main()
