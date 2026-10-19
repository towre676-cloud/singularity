# Readable pretrained evidence and exact reconstruction

The pretrained measurements, frozen scientific programs and original receipt hashes are unchanged. Large JSON receipts are published as smaller, directly readable execution cases and document reports. Every shard contains its destination path within the original JSON object and its complete scientific payload. Each manifest records the metadata retained outside those payloads, the shard files and their byte counts and SHA-256 values, and the original receipt's byte count, SHA-256 and serialization settings.

Each `results/pretrained_audit/MODEL/observations.shards/` directory contains fifteen cases: the reference observations, two clean calibration runs, five construction-fault runs, five held-out variants and two independent clean controls. `reference.json` and the files under `calibration/`, `construction/`, `heldout/` and `clean_audit/` contain one observation per candidate probe, in the order declared by that model's frozen `protocol.json`. The manifest retains the clean calibration maxima and frozen tolerances. All eighteen probes, including faults that have no separating observations, remain available.

`results/pretrained_prediction/posthoc_prior_analysis.shards/manifest.json` retains the post-hoc status, prior choice, theorem, primary receipt hashes, model metadata and domain summaries. The files under `models/MODEL/documents/` retain all seventy-two complete document reports, including hexadecimal per-target losses, prior weights and regret evidence. The original primary token traces remain directly readable under `results/pretrained_prediction/models/MODEL/traces/`; the separate context-sensitivity traces remain under `results/pretrained_context512/models/gpt2/traces/`.

Run the materialization helper before any independent replay or script that opens the original JSON receipt paths:

```sh
python scripts/materialize_pretrained_evidence.py materialize
python scripts/materialize_pretrained_evidence.py materialize --output applications/training_lab/results/pretrained_context512
```

The helper restores the three `observations.json` files and `pretrained_prediction/posthoc_prior_analysis.json`. It verifies every shard hash, assembles each original object at its declared paths, renders the original sorted JSON with its original indentation and trailing newline, and checks the final bytes against the original SHA-256 before writing. Existing conflicting receipts are rejected. Generated monolithic JSON receipts are ignored by Git. The same helper reconstructs the selected public corpus and the original deterministic gzip traces, preserving all frozen result hashes. It uses the standard library and makes no model forward calls.

After materialization, the independent evidence tests, primary verifier, full-prefix context verifier and optimally pruned greedy comparison read precisely the same scientific receipts as before:

```sh
PYTHONPATH=src python -m unittest tests.test_pretrained_evidence -v
python scripts/confirm_pretrained_prediction.py verify --name gpt2
python scripts/confirm_pretrained_prediction.py verify --name smollm2-360m
python scripts/confirm_pretrained_prediction.py verify --name smollm2-1700m
python scripts/verify_pretrained_context.py
python scripts/compare_pruned_pretrained_panels.py
```

The case and document boundaries serve inspection and selective reuse. They do not change the observations, samples, losses, uncertainties, failure reports or claim boundaries. The prior and context sensitivity analyses remain explicitly post hoc.
