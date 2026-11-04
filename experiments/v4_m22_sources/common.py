from pathlib import Path
import hashlib,json,random
NAMESPACES={'organisation','responsibility_graph','staffing','residual_relationship_choice','source_rendering','observation_noise','roster_visibility','storage_order'}
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def digest(v):return hashlib.sha256(canonical(v).encode()).hexdigest()
def config():return json.loads(Path(__file__).with_name('config.json').read_text(encoding='utf-8-sig'))
def rng(c,index,namespace,key=''):
    if namespace not in NAMESPACES:raise ValueError('Unknown RNG namespace')
    return random.Random(int(digest([c['version'],c['seed'],index,namespace,key]),16))
def opaque(c,index,domain,key):return digest(['m22-independent-identity',c['seed'],index,domain,key])[:32]
