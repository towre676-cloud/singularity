# Version 1 deployment audit (re-run): Qwen2.5-1.5B on a Tesla T4

Retained unchanged from the Colab archive `deployment_audit_20261019_165822.zip` (SHA-256 `47d875ab0d9b75a5cd494f719f9213e7eb45c45b8be25eb9b058e1a1baff091c`), produced by `scripts/colab_deployment_audit.py` at commit a9bfb31 (script hash checked against that commit). The empty `scratch/` folder was omitted.

**This is not the original version-1 run.** The original run reported in the conversation (protocol `47b381aacf9182f3`, frozen 16:58:23Z) is not retained. This archive carries the original folder name but holds a later run of the same version-1 script: protocol `16b658137ff946d2`, frozen 2026-10-19T20:12:40Z (after the version-2 run) and finished 20:17:17Z, with no cold checks.

- Model: `Qwen/Qwen2.5-1.5B` at revision `8faed761d45a263340a0528343f099c05c9a4323`, float16, Tesla T4; Python 3.13.15, torch 2.11.0+cu130, transformers 5.20.1.
- It reproduces the original run's findings: exact and optimally pruned greedy panels both cost 261 tokens, greedy 272; the panel misses only `heldout/truncate_to_72`; the clean controls `kv_cache_disabled` (4 probes) and `eager_attention_backend` (1348 non-finite values) are flagged.
- `tests/test_gpu_deployment_evidence.py` recomputes these from `observations.json` with the version-1 calibration rule.
