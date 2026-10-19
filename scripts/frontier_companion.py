#!/usr/bin/env python3
"""Replay the five independent frontier-companion receipts, without NX36 work."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = (
    "fr01_pole_divisors.py",
    "fr02_denominator_recovery.py",
    "fr03_tree_positivity.py",
    "fr04_pinned_theta.py",
    "fr05_threshold_reconstruction.py",
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="compare independently regenerated receipts with retained files")
    args = parser.parse_args()
    env = dict(os.environ)
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(ROOT / "src") + (os.pathsep + existing if existing else "")
    reports = []
    for name in SCRIPTS:
        path = ROOT / "scripts" / name
        if not path.is_file():
            raise SystemExit("Missing companion receipt script: " + name)
        command = [sys.executable, str(path)] + (["--check"] if args.check else [])
        result = subprocess.run(command, cwd=ROOT, env=env, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode:
            sys.stderr.write(result.stdout + result.stderr)
            raise SystemExit(result.returncode)
        reports.append({"script": name, "status": "passed"})
    print(json.dumps({"schema": "singularity.frontier-replay/1",
                      "mode": "check" if args.check else "regenerate",
                      "receipts": reports, "nx36_units_modified": 0},
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
