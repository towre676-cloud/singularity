#!/usr/bin/env python3
"""One-command replay of the complete exact seventh-order contribution.

Each stage fails immediately on an invalid identity. Generated exact
certificates must reproduce their committed bytes. No third-party packages.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
DEPENDENCY='517d6cf1d2fdd2f5369011db55a1e4bb2b51c7fd'

def main():
    certificates=sorted(HERE.glob('vol7*.json'))
    before={p.name:p.read_bytes() for p in certificates}
    stages=[
        ('complete motif census and connected-support inversion',['vol7_kernel_check.py','--check']),
        ('cubic leaf recurrence',['vol7_reduction.py']),
        ('rational agreement quotient',['vol7_law.py']),
        ('independent determination identities',['vol7_law_check.py']),
        ('all40 deterministic cubic completions',['vol7_completion.py','--full-host-check']),
        ('constructed isolation and delayed-house witnesses',['vol7_observation.py']),
        ('two direct connected14-vertex witnesses',['vol7_witnesses.py','--replay']),
        ('connected24-vertex weld-ring transfer',['vol7_weld_aggregate.py']),
        ('independent kernels, direct heights and354-vertex house witness',['vol7_independent_check.py']),
    ]
    for label,args in stages:
        print('\nChecking '+label,flush=True)
        subprocess.run([sys.executable,str(HERE/args[0]),*args[1:]],check=True,cwd=HERE)
    # The scientific catalogue is discrete; SVG layout is presentation only.
    from vol7_motifs import catalogue
    assert json.loads((HERE/'vol7_motifs.json').read_text())==json.loads(json.dumps(catalogue()))
    for p in certificates:
        assert before[p.name]==p.read_bytes(), 'Certificate drift: '+p.name
    manifest=HERE/'vol7_manifest.json'
    if manifest.exists():
        m=json.loads(manifest.read_text())
        assert m['dependency_commit']==DEPENDENCY
        for name,digest in m['sha256'].items():
            assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==digest,name
    print('\nALL VOLUME-SEVEN CHECKS PASSED; exact certificates reproduced.',flush=True)

if __name__=='__main__':main()
