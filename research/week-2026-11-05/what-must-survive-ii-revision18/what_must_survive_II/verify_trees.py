#!/usr/bin/env python3
"""Bounded exact tree audit, distinct from the volume-12 graph replay."""
from pathlib import Path
import subprocess,sys,json
PKG=Path(__file__).resolve().parent
jobs=['check_caterpillars.py','check_ancestor.py','check_exchange.py']
for script in jobs:
    print('Checking',script,flush=True)
    subprocess.run([sys.executable,str(PKG/'review'/script)],check=True,cwd=PKG)
print('Tree audit passed. See review/*.json for exact coverage.',flush=True)
