"""Operational read isolation for the source-only predictor process; no evaluator imports."""
from pathlib import Path
import sys,json,hashlib,os
from .predict import infer

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(input_root,output_root,probe):
 source=Path(input_root).resolve();out=Path(output_root).resolve();code=Path(__file__).resolve().parent;cfg=json.loads((code/'config.json').read_text(encoding='utf-8-sig'))
 if out.exists():raise ValueError('Refusing prediction overwrite')
 out.mkdir(parents=True);reads=[];denied=[];read_roots=[source,out,code,Path(sys.prefix).resolve(),Path(sys.base_prefix).resolve()]
 def allowed(p,roots):return any(p==r or p.is_relative_to(r) for r in roots)
 def audit(event,args):
  if event in ('socket.connect','subprocess.Popen','os.system'):raise PermissionError('No external execution/network in predictor')
  if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
   p=Path(os.fsdecode(args[0])).resolve();mode=args[1];flags=args[2];writing=(isinstance(mode,str) and any(k in mode for k in 'wax+')) or isinstance(flags,int) and bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC))
   if not allowed(p,[out] if writing else read_roots):denied.append(str(p));raise PermissionError('Predictor file boundary denied')
   if not writing:reads.append(str(p))
 sys.addaudithook(audit)
 try:Path(probe).read_bytes()
 except PermissionError:pass
 else:raise AssertionError('Private-data probe unexpectedly readable')
 cases=[]
 for case in sorted(source.glob('company_*')):
  contacts=json.loads((case/'contacts.json').read_text())
  for label in ['clean','messy']:
   view=json.loads((case/f'{label}.json').read_text());result=infer(view,contacts,cfg);folder=out/case.name;folder.mkdir(exist_ok=True)
   for key in ['claims','predictions','graph']:(folder/f'{label}_{key}.json').write_text(json.dumps(result[key],indent=2)+'\n',encoding='utf-8')
   cases.append({'case':case.name,'variant':label,'employees':len(contacts),'proposed':sum(p['status']=='proposed' for p in result['predictions'])})
 (out/'INPUT_ACCESS.json').write_text(json.dumps({'boundary':'staged observed inputs + own code/config + Python runtime; no technical_audit reads','successful_reads':sorted(set(reads)),'denied_probes':denied,'process_scope':'extractor/predictor only; evaluator separate','cases':cases},indent=2)+'\n')
 files={p.relative_to(out).as_posix():sha(p) for p in out.rglob('*.json')};(out/'PREDICTION_FREEZE.json').write_text(json.dumps({'version':cfg['version'],'files_sha256':files,'source_manifest_sha256':sha(source/'SOURCE_ONLY_MANIFEST.json'),'code_sha256':{p.name:sha(p) for p in code.glob('*') if p.suffix in {'.py','.json'}},'truth_used':False},indent=2)+'\n');print('Frozen source-only predictions:',len(cases),'paired company views')
if __name__=='__main__':run(*sys.argv[1:])
