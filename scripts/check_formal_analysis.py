#!/usr/bin/env python3
"""Build the Mathlib analysis package and audit every declared release theorem.

Use the Lean version pinned in formal-analysis/lean-toolchain.  Dependency
installation and Mathlib's cache download are separate setup steps.  The
checker itself uses only Python's standard library and Lake.
"""

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "formal-analysis"
ALLOWED = {"propext", "Quot.sound", "Classical.choice"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clean", action="store_true",
                        help="remove this package's generated build directory first")
    parser.add_argument("--receipt", type=Path,
                        help="write a deterministic JSON audit receipt")
    args = parser.parse_args()
    if args.clean:
        shutil.rmtree(PROJECT / ".lake" / "build", ignore_errors=True)
    subprocess.run(["lake", "build"], cwd=PROJECT, check=True)
    audit_file = PROJECT / "AnalysisAxiomAudit.lean"
    names = re.findall(r"^#print axioms (\S+)", audit_file.read_text(), re.M)
    if not names or len(names) != len(set(names)):
        raise SystemExit("analysis audit must name a nonempty, duplicate-free theorem list")
    audit = subprocess.run(
        ["lake", "env", "lean", audit_file.name], cwd=PROJECT,
        capture_output=True, text=True, check=True,
    ).stdout
    seen = {}
    for line in audit.splitlines():
        match = re.match(
            r"'([^']+)' (?:depends on axioms: \[(.*)\]|does not depend on any axioms)", line,
        )
        if match:
            seen[match.group(1)] = {
                item.strip() for item in (match.group(2) or "").split(",") if item.strip()
            }
    missing = [name for name in names if name not in seen]
    extra = {name: sorted(seen[name] - ALLOWED)
             for name in names if name in seen and seen[name] - ALLOWED}
    if missing or extra:
        raise SystemExit(f"analysis audit failed: missing {missing}, non-standard axioms {extra}")
    print(f"Real-analysis build and axiom audit passed for {len(names)} theorems")
    if args.receipt:
        version = subprocess.run(
            ["lake", "env", "lean", "--version"], cwd=PROJECT,
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        sources = sorted(PROJECT.glob("SingularityAnalysis/*.lean")) + [
            PROJECT / "SingularityAnalysis.lean", audit_file,
            PROJECT / "lakefile.lean", PROJECT / "lake-manifest.json",
            PROJECT / "lean-toolchain",
        ]
        sources += sorted((ROOT / "formal").glob("Singularity/*.lean")) + [
            ROOT / "formal" / name for name in
            ("Singularity.lean", "AxiomAudit.lean", "lakefile.lean",
             "lake-manifest.json", "lean-toolchain")
        ]
        sources += [Path(__file__).resolve()]
        receipt = {
            "schema": "singularity.formal-analysis-audit/1",
            "lean_version": version,
            "theorem_count": len(names),
            "allowed_axioms": sorted(ALLOWED),
            "theorems": {name: sorted(seen[name]) for name in names},
            "source_sha256": {
                str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in sorted(sources)
            },
        }
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
