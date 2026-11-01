#!/usr/bin/env python3
"""One-command exact replay of the eighth-order observation contribution."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
DEPENDENCY='facb4506d1e9b1667b877815777566296572a4fb'

def main():
    certificates=sorted(HERE.glob('vol8*.json'))
    before={p.name:p.read_bytes() for p in certificates}
    stages=[
      ('full catalogue and all307 exact kernels',['vol8_kernel_check.py','--check']),
      ('terminating cubic leaf recurrence',['vol8_reduction.py']),
      ('eighth correction and natural observation basis',['vol8_law.py']),
      ('rational and3684 direct determination checks',['vol8_law_check.py']),
      ('direct delayed-motif recovery from energy sectors28and30',['vol8_tail_check.py']),
      ('all100 high-girth completions and boundary supports',['vol8_completion.py','--boundary-check']),
      ('60 isolated eighth cores and7 observation coordinates',['vol8_observation.py']),
      ('direct12-vertex delayed-information pair',['vol8_witnesses.py','--replay']),
      ('20-vertex weld transfer and independent global heights',['vol8_weld.py','--replay']),
      ('independent kernels, off-diagonals, quotient and completions',['vol8_independent_check.py']),
    ]
    for label,args in stages:
        print('\nChecking '+label,flush=True)
        subprocess.run([sys.executable,str(HERE/args[0]),*args[1:]],check=True,cwd=HERE)
    from vol8_motifs import catalogue
    assert json.loads((HERE/'vol8_motifs.json').read_text())==json.loads(json.dumps(catalogue()))
    for p in certificates:
        assert before[p.name]==p.read_bytes(),'Certificate drift: '+p.name
    manifest=HERE/'vol8_manifest.json'
    if manifest.exists():
        m=json.loads(manifest.read_text());assert m['dependency_commit']==DEPENDENCY
        for name,digest in m['sha256'].items():
            assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==digest,name
    print('\nALL VOLUME-EIGHT CHECKS PASSED; exact certificates reproduced.',flush=True)

if __name__=='__main__':main()
