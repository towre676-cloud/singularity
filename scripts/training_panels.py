#!/usr/bin/env python3
"""Choose a construction-only diagnostic panel from frozen checkpoint counts.

Run ``python scripts/training_panels.py predictiontable.json --output report.json``.
The complete input schema and interpretation are documented in
``src/singularity/training_panels.py``. Optional audit data are embedded in the
input's ``audit`` object, and are never used to select the panel.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from singularity.training_panels import training_panel_report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prediction_table", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-nodes", type=int, default=10**6)
    args = parser.parse_args()
    if args.output.resolve() == args.prediction_table.resolve():
        parser.error("--output must differ from the prediction table")
    raw = args.prediction_table.read_bytes()
    report = training_panel_report(json.loads(raw), max_nodes=args.max_nodes)
    report["input_file_sha256"] = hashlib.sha256(raw).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"report": str(args.output),
                      "quotient_class_count": report["quotient_class_count"],
                      "selected_probe_ids": report["selected_probe_ids"],
                      "selected_panel_cost": report["selected_panel_cost"],
                      "full_panel_cost": report["full_panel_cost"],
                      "discovery_cost_examples": report["discovery_cost_examples"]}))


if __name__ == "__main__":
    main()
