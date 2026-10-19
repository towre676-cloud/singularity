#!/usr/bin/env python3
"""Build pinned core Lean, audit its theorems, and bind the OE12 proof receipt.

Requires ``lake`` (Lean 4.12.0, core only) on PATH. The build and axiom audit
reject omitted declarations and any axiom outside the standard Lean axioms.
Use --operator-receipt to regenerate the source-bound operator proof receipt;
ordinary runs check an existing receipt against the current proof sources.
The separate Mathlib analysis project has its own build and historical receipt.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORMAL = ROOT / "formal"
ALLOWED = {"propext", "Quot.sound", "Classical.choice"}
DEFAULT_RECEIPT = ROOT / "results/formal_operator_audit.json"


def parse_audit(output):
    seen = {}
    for line in output.splitlines():
        match = re.match(r"'Singularity\.(\S+)' (?:depends on axioms: \[(.*)\]|does not depend on any axioms)", line)
        if match:
            seen[match.group(1)] = {
                item.strip() for item in (match.group(2) or "").split(",") if item.strip()
            }
    return seen


def operator_receipt(seen):
    audit_file = FORMAL / "OperatorAxiomAudit.lean"
    names = re.findall(r"^#print axioms Singularity\.(\S+)", audit_file.read_text(), re.M)
    if not names or len(names) != len(set(names)):
        raise SystemExit("operator audit must name a nonempty, duplicate-free theorem list")
    missing = [name for name in names if name not in seen]
    if missing:
        raise SystemExit(f"operator declarations absent from full audit: {missing}")
    version = subprocess.run(["lake", "env", "lean", "--version"], cwd=FORMAL,
                             check=True, capture_output=True, text=True).stdout.strip()
    sources = sorted((FORMAL / "Singularity").glob("*.lean")) + [
        FORMAL / name for name in ("Singularity.lean", "AxiomAudit.lean", "OperatorAxiomAudit.lean",
                                  "lakefile.lean", "lake-manifest.json", "lean-toolchain")
    ] + [Path(__file__).resolve()]
    return {
        "schema": "singularity.formal-operator-audit/1",
        "lean_version": version,
        "operator_theorem_count": len(names),
        "core_theorem_count": len(seen),
        "allowed_axioms": sorted(ALLOWED),
        "theorems": {"Singularity." + name: sorted(seen[name]) for name in names},
        "source_sha256": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(sources)
        },
        "scope": {
            "closure": "Finite retained rows closed under generators contain every future experiment row; actual word witnesses give the reverse inclusion.",
            "quotient": "Encoded-state equality is exactly all-future observational equivalence; generator maps descend to the quotient.",
            "cost": "Natural-cost filtered span completeness, affordable retained-row equivalence, and global cheapest distinguishing witness. Python search termination and rational-cost scaling are not formalized.",
            "periodic": "Actual residue-profile complement bijection, arbitrary signed integer edge-phase histogram palindrome, half-degree uniqueness, and shared-unit-denominator formal-series cutoff.",
            "examples": "Concrete noncommuting integer matrices and a rank-zero observation certificate.",
            "outside_kernel_scope": [
                "Python implementation and portable JSON parser",
                "Row independence, dimension minimality, and discovery termination",
                "Cyclotomic ring implementation and height-to-residue denominator decomposition",
                "Robust optimization, panels, parametric rank, compression, and separator compiler",
            ],
        },
        "analysis_receipt": {
            "path": "results/formal_analysis_audit.json",
            "status": "Separate historical 79-theorem Mathlib receipt; this core audit does not assert a fresh Mathlib build.",
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--operator-receipt", type=Path,
                        help="write a fresh deterministic OE12 audit receipt after building")
    args = parser.parse_args()
    subprocess.run(["lake", "build"], cwd=FORMAL, check=True)
    audit = subprocess.run(["lake", "env", "lean", "AxiomAudit.lean"], cwd=FORMAL, check=True,
                           capture_output=True, text=True).stdout
    names = re.findall(r"^#print axioms (\S+)", (FORMAL / "AxiomAudit.lean").read_text(), re.M)
    if not names or len(names) != len(set(names)):
        sys.exit("core audit must name a nonempty, duplicate-free theorem list")
    seen = parse_audit(audit)
    missing = [name for name in names if name not in seen]
    extra = {name: sorted(axioms - ALLOWED) for name, axioms in seen.items() if axioms - ALLOWED}
    if missing or extra:
        sys.exit(f"formal audit failed: missing {missing}, non-standard axioms {extra}")
    print(f"Formal build and axiom audit passed for {len(seen)} theorems")
    expected = operator_receipt(seen)
    if args.operator_receipt:
        args.operator_receipt.parent.mkdir(parents=True, exist_ok=True)
        args.operator_receipt.write_text(json.dumps(expected, indent=2, sort_keys=True) + "\n")
        print(f"Wrote operator receipt for {expected['operator_theorem_count']} new theorems")
    elif DEFAULT_RECEIPT.exists():
        actual = json.loads(DEFAULT_RECEIPT.read_text())
        if actual != expected:
            sys.exit("operator formal receipt is stale; rebuild with --operator-receipt results/formal_operator_audit.json")
        print("Source-bound operator formal receipt matches the current build")


if __name__ == "__main__":
    main()
