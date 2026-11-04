"""Versioned config with explicit common-random-number compatibility, not new seeds."""
from pathlib import Path
import json
from experiments.v4_m22_sources.common import digest,canonical,opaque
from experiments.v4_m22_sources.common import rng as base_rng
def config():return json.loads(Path(__file__).with_name('config.json').read_text())
def compatible(c):return dict(c,version=c['rng_compatibility_version'])
def rng(c,index,namespace,key=''):return base_rng(compatible(c),index,namespace,key)
