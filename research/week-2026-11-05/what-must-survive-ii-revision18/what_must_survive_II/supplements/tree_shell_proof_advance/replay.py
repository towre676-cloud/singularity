"""Replay the exact checks; no original archive path or C++ executable is required."""
from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parent
for name in ['contractions.py','residue_lifts.py','spider_reconstruction.py','symbolic_relation.py','compatible_kernel.py','weighted_kernel.py','check_formal_realizability.py','degree_projections.py']:
    print('Running',name,flush=True)
    subprocess.run([sys.executable,str(ROOT/name)],check=True,cwd=ROOT)
print('All exact checks passed.')
