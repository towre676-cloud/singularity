# Version 2 deployment audit: Qwen2.5-1.5B on a Tesla T4

Retained unchanged from the Colab archive `deployment_audit_v2_20261019_195015.zip` (SHA-256 `adaa8ab9ac3d3159e1febb4b7444cf826a895b8110418ec1d933a09f19e5f5ef`), produced by `scripts/colab_deployment_audit_v2.py` at commit 22c2527 (script hash recorded in `protocol.json` and checked against that commit before archiving). The empty `scratch/` folder was omitted.

- Model: `Qwen/Qwen2.5-1.5B` at revision `8faed761d45a263340a0528343f099c05c9a4323`, float16, Tesla T4; Python 3.13.15, torch 2.11.0+cu130, transformers 5.20.1.
- Protocol `0ecf6e6d1cc7b8b0`, frozen 2026-10-19T19:50:37Z before any forward pass; results written 19:55:31Z.
- `tests/test_gpu_deployment_evidence.py` recomputes tolerances, every separation, the exact minimum and the false-alarm counts from `observations.json`.

Version 1 (protocol `47b381aacf9182f3`) results are not yet archived here.
