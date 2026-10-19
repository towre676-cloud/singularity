#!/usr/bin/env python3
"""Assemble the separate frontier companion; leave the baseline monograph intact."""

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_documents import assembled_links, render

SOURCES = (
    "docs/research/FRONTIER_COMPANION.md",
    "docs/research/FR01_POLE_DIVISORS.md",
    "docs/research/FR02_DENOMINATOR_RECOVERY.md",
    "docs/research/FR03_TREE_POSITIVITY.md",
    "docs/research/FR04_PINNED_THETA.md",
    "docs/research/FR05_THRESHOLD_RECONSTRUCTION.md",
    "docs/research/FR_INDEPENDENT_REVIEW.md",
)


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-pdf", action="store_true")
    args = parser.parse_args()
    parts = []
    counts = {}
    for name in SOURCES:
        path = ROOT / name
        if not path.is_file():
            raise SystemExit("Missing authored frontier source: " + name)
        text = path.read_text()
        if "\ufffd" in text:
            raise SystemExit("Replacement glyph in " + name)
        parts.append(assembled_links(text, path))
        counts[name] = len(text.split())
    source = ROOT / "docs" / "FRONTIER_MANUSCRIPT.md"
    source.write_text("\n\n".join(parts))
    render(source, "frontier_companion", "Singularity: Frontier Companion",
           "Arithmetic invariants, exact poles, positive tree interfaces and pinned theta limits",
           book=True, pdf=not args.no_pdf)
    report = {"schema": "singularity.frontier-manuscript/1",
              "source_word_counts": counts, "source_words": sum(counts.values()),
              "count_method": "whitespace-delimited source words; mathematics included",
              "baseline_monograph_modified": False}
    (ROOT / "results" / "frontier_manuscript.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
