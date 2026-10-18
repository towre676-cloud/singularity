#!/usr/bin/env python3
"""Build the Lean package in formal/ and audit the axioms of its main theorems.

Requires ``lake`` (Lean 4.12.0, core library only) on PATH.  Fails if the
build fails, if the axiom audit lists anything beyond Lean's standard
``propext``, ``Quot.sound`` and ``Classical.choice`` (``sorryAx`` in
particular), or if a theorem named in AxiomAudit.lean is missing.
"""
import re
import subprocess
import sys
from pathlib import Path

FORMAL = Path(__file__).resolve().parents[1] / "formal"
ALLOWED = {"propext", "Quot.sound", "Classical.choice"}


def main():
    subprocess.run(["lake", "build"], cwd=FORMAL, check=True)
    audit = subprocess.run(["lake", "env", "lean", "AxiomAudit.lean"], cwd=FORMAL, check=True,
                           capture_output=True, text=True).stdout
    names = re.findall(r"^#print axioms (\S+)", (FORMAL / "AxiomAudit.lean").read_text(), re.M)
    seen = {}
    for line in audit.splitlines():
        m = re.match(r"'Singularity\.(\S+)' (?:depends on axioms: \[(.*)\]|does not depend on any axioms)", line)
        if m:
            seen[m.group(1)] = {a.strip() for a in (m.group(2) or "").split(",") if a.strip()}
    missing = [n for n in names if n not in seen]
    extra = {n: a - ALLOWED for n, a in seen.items() if a - ALLOWED}
    if missing or extra:
        sys.exit(f"formal audit failed: missing {missing}, non-standard axioms {extra}")
    print(f"Formal build and axiom audit passed for {len(seen)} theorems")


if __name__ == "__main__":
    main()
