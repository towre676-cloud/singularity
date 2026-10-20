#!/usr/bin/env python3
"""Run the retained, model-free independent evidence checks."""
import argparse, subprocess, sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--retrain',action='store_true');a=p.parse_args()
root=Path(__file__).resolve().parent
commands=[
    [sys.executable,str(root/'verify_hydraulic.py'),str(root/'hydraulic_v1')],
    [sys.executable,str(root/'audio_v1/verify_audio_study.py')],
    [sys.executable,str(root/'audio_v1/confirmation/verify_confirmation.py')]
]
if a.retrain:commands.append([sys.executable,str(root/'retrain_from_features.py'),str(root/'hydraulic_v1')])
for cmd in commands:subprocess.run(cmd,check=True)
print('All requested sensor evidence checks passed.')
