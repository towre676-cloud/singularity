# Singularity 0.10.0: deployment artifacts and fresh transfer

**Smaller model checks now survive a new model family and actual deployment transformations.** This release evaluates Qwen2.5-1.5B, real FP32/TorchScript/INT8 SmolLM2 artifacts, and prospective repetition gating on fresh development and held-out documents. Neural weights remain frozen throughout.

![Audit costs, resident latency, and fresh held-out prediction outcomes.](../../docs/assets/deployment-transfer.svg)

## An independent model family

The untouched Qwen2.5-1.5B family has 1,543,714,304 parameters. Its exact two-witness panel costs **192 native input tokens**, compared with **215** after optimally pruning the greedy output: **10.70% fewer tokens**. Scanning all 262,144 subsets independently confirms the optimum. The pruned-greedy comparison is an explicitly post-hoc deterministic calculation on the unchanged construction table.

A resident check takes **1.974s**, compared with **12.013s** to observe the full pool (**6.09×**). All 5 declared construction distinctions have two panel witnesses. The panel flags **3/5 held-out variants**; the misses are `left_pad_absolute_positions`, `unicode_nfd`. Neither of its two independent clean controls flags, and the separate fresh-process package check passes. A constant position translation can be invariant under RoPE; these observations do not create a universal guarantee for missing variants.

## Actual serialization, graph and quantized artifacts

The deployment study uses the same 18 fixed probe texts and a separate service that executes preprocessing/forward faults outside the audit adapter. FP32 weights are serialized as Safetensors and reloaded. An explicit-mask eager Llama graph is traced, saved, verified and reloaded as TorchScript. The INT8 target quantizes actual Linear modules, saves their packed state, reconstructs a fresh quantized model, and checks state identity after weights-only loading. Receipts retain actual SDPA kernel calls, quantized-module forward calls and cache sequence lengths.

| Target | Full pool tokens | Exact | Optimally pruned greedy | Pruned random median | Random trials reaching exact |
|---|---:|---:|---:|---:|---:|
| FP32 (prospective) | 1089 | **192** | 214 | 256 | 10/64 |
| INT8 eager (post-calibration repair) | 1089 | **192** | 214 | 256 | 10/64 |

All compared panels meet the same two-witness requirement on the same coverable construction distinctions. Each random feasible prefix is optimally pruned, and every trial is retained. A randomized heuristic can find the exact cost; exact selection additionally certifies that no cheaper panel exists.

| Target | Full package check | Exact package check | Full/exact ratio | Incremental build break-even | Gross build break-even | Build + artifact preparation |
|---|---:|---:|---:|---:|---:|---:|
| FP32 (prospective) | 6.804s | **1.165s** | 5.84× | 8 checks | 15 checks | 17 checks |
| INT8 eager (post-calibration repair) | 2.663s | **0.400s** | 6.66× | 8 checks | 13 checks | 19 checks |

Three predeclared interleaved timing rounds follow warmup, on one shared CPU host with four threads. Both full and reduced deployment checks include package verification, model inference and comparison. Incremental construction excludes common reference/calibration but conservatively charges all comparator selection work to each panel. Gross construction includes all reference/calibration, catalogue observations, selection and package creation. Artifact preparation includes source loading, serialization/conversion and reload; fresh-process import and disk-verification costs are separate. These timings describe audit checks, not generation or training.

| Target | Construction distinctions covered | Executed held-out variants flagged | Clean full-pool cases without flags |
|---|---:|---:|---:|
| FP32 (prospective) | 6 | 6/7 | 5/5 |
| INT8 eager (post-calibration repair) | 6 | 6/7 | 1/5 |

FP32 independent clean controls include SDPA, batching, thread/order changes, a genuine two-chunk KV-cache path, and the saved TorchScript graph. Every selected-result erasure is checked against the retained coverage witness. The graph contract is bounded CPU FP32 eager Llama, batch 1–3, width 1–96, unscaled RoPE and no cache; native cached execution is checked separately.

**The original prospective INT8 calibration did not produce a package.** Its SDPA batch-one control changed non-tie argmax outputs on **16/18 probes**, totaling **232 positions**. The eager thread-one control remained stable. All 225 quantized Linear modules and exact packed-state reload identity were verified. The complete failure, original protocol and quantized artifact receipt are retained. The cause of the backend drift is not established by this experiment.

The reported INT8 package is an explicitly **post-calibration eager-only contract repair**, frozen in a separate script/output directory before new forwards. It keeps every probe, fault, tolerance and comparator unchanged. It calibrates eager batch-one full prefill at threads one and two; SDPA batch-one is moved to a held-out clean transfer. The package metadata binds its approved backend/batch/cache envelope and the original failure/protocol hashes before all measured checks.

Dynamic INT8 has its own baseline and tolerances. Its activation scales depend on batch/chunk extent, so its approved execution uses eager batch-one full prefill. SDPA, batch-three and cache controls are explicitly clean transfers outside that envelope. Their observed flags are numerical drift, not silently relabeled deployment faults. The checker reports `outside_calibration` and exit 3 for these requests, preserving raw measurements. The clean-control details below distinguish these cases:

| INT8 clean control | Flagged full-pool probes | Flagged exact-panel probes |
|---|---:|---:|
| `eager_batch1_threads2_reverse` | 0 | 0 |
| `eager_batch3_threads2_reverse` | 12 | 2 |
| `eager_cache_third_threads2` | 18 | 2 |
| `sdpa_batch1_threads2_reverse` | 16 | 2 |
| `sdpa_batch3_threads2_reverse` | 17 | 2 |

INT8 cache-drop variants also leave the approved full-prefill envelope. When healthy chunking itself flags, a dropped-cache flag establishes an observational difference from the reference, not specificity to cache corruption. FP32 supports the stronger cache-correctness comparison: its healthy cached controls pass while the dropped-prefix variants flag. The exact catalogue witness remains valid for the stored observations in both representations.

FP32 held-out misses: `service_dropped_mask`. INT8 held-out misses: `service_dropped_mask`. Construction distinctions with fewer than two pool witnesses are retained as unavailable: FP32 `{}`; INT8 `{}`.

## Fresh prediction: select on development, then evaluate once

Four pinned models each score 12 development documents and 24 held-out documents, 512 native-token targets per document: **73,728 evaluated targets**. Each split contains literary prose, technical reference and Python source. Neural models see the entire available prefix. The count model, repetition features and blending posteriors use only preceding targets and reset for every document. No neural parameter is updated.

The primary selection considers pure neural and 18 protected repetition policies, using development aggregate log loss only. A committed selection receipt precedes every held-out forward. Each gate uses prefix context order/support; the protected predictor gives pure neural 95% prior mass. The mathematical whole-document excess-loss ceiling is $-\log(0.95)=0.0512933$ nats in exact arithmetic. Protection limits overhead; it does not promise improvement. The declared hierarchy and ungated protection are secondary comparisons; all policy diagnostics remain visible.

| Model | Development-selected arm | Neural NLL | Selected NLL | Selected − neural | Loss reduction | Documents better / worse / tied |
|---|---|---:|---:|---:|---:|---:|
| GPT-2 124M | `order1_support1_alpha025` | 3.39750907 | 3.14423112 | -0.253277947 | +7.45481% | 18 / 6 / 0 |
| SmolLM2 362M | `neural` | 2.07922995 | 2.07922995 | +0 | +0% | 0 / 0 / 24 |
| SmolLM2 1.71B | `neural` | 1.63390333 | 1.63390333 | +0 | +0% | 0 / 0 / 24 |
| Qwen2.5 1.54B | `neural` | 1.81073459 | 1.81073459 | +0 | +0% | 0 / 0 / 24 |

NLL is nats per native tokenizer token and is compared only within each model. A document is numerically tied when its whole-document loss difference is within 1e-10 nats. Pure-neural fallback is an allowed primary outcome with zero change.

| Model | Paired difference, 95% descriptive document-bootstrap interval |
|---|---|
| GPT-2 124M | [-0.33007682, -0.176221079] nats/token |
| SmolLM2 362M | [+0, +0] nats/token |
| SmolLM2 1.71B | [+0, +0] nats/token |
| Qwen2.5 1.54B | [+0, +0] nats/token |

The predeclared secondary predictors are retained alongside the selected primary:

| Model | Selected primary reduction | Protected hierarchy reduction | Ungated protected reduction |
|---|---:|---:|---:|
| GPT-2 124M | +7.45481% | +7.36542% | +2.73095% |
| SmolLM2 362M | +0% | -0.00427573% | -0.00481824% |
| SmolLM2 1.71B | +0% | -0.00541079% | -0.00613147% |
| Qwen2.5 1.54B | +0% | -0.00501285% | -0.00553268% |

Primary differences by held-out domain:

| Model | Literary prose | Technical reference | Python source |
|---|---:|---:|---:|
| GPT-2 124M | -0.0331093445 | -0.288524739 | -0.438199756 |
| SmolLM2 362M | +0 | +0 | +0 |
| SmolLM2 1.71B | +0 | +0 | +0 |
| Qwen2.5 1.54B | +0 | +0 | +0 |

These intervals resample documents in 10,000 draws, not individual dependent tokens. The documents/source files are distinct between development and held-out sets, while source projects, some module names and model pretraining may overlap. This is a fresh experimental split, not proof of unseen pretraining data or universal generalization. A tiny improvement must be interpreted at its actual numerical and practical scale.

## Saved-artifact command-line checks

Fresh-process checks validate artifact/source/tokenizer identities before using only the selected saved reference observations. Their cold validation/load costs remain separate from resident audit timing.

| Target / check | Deployment status | Raw verdict | Resident seconds | Validation + load seconds |
|---|---|---|---:|---:|
| float32 / `eager_cache_third` | `unchanged` | `unchanged` | 2.041 | 4.149 |
| float32 / `sdpa_batch3` | `unchanged` | `unchanged` | 1.352 | 4.237 |
| float32 / `torchscript_batch3` | `unchanged` | `unchanged` | 1.743 | 4.520 |
| dynamic_int8 / `approved_eager` | `unchanged` | `unchanged` | 0.500 | 6.428 |
| dynamic_int8 / `missing_all` | `inconclusive_missing_results` | `unchanged` | 0.001 | 6.270 |
| dynamic_int8 / `outside_sdpa` | `outside_calibration` | `changed` | 0.549 | 6.852 |

## Use and reproduce

The [deployment guide](DEPLOYMENT_GUIDE.md) gives download, freeze, construction and existing-artifact check commands. `scripts/check_deployment_package.py` verifies identities, then checks an existing eager, SDPA, TorchScript or quantized artifact using the saved package. It reports cold setup and resident check costs separately. The general [`ProtectedRepetitionBlend`](../../src/singularity/training/repetition_blend.py) exposes predict-before-observe adaptation with a pure-neural fallback.

```sh
python scripts/materialize_pretrained_evidence.py materialize
PYTHONPATH=src python -m unittest tests.test_new_family_evidence -v
python scripts/verify_deployment_confirmation.py
python scripts/verify_gating_confirmation.py
python scripts/report_deployment_transfer.py --render --update-readme
```

The independent verifiers reconstruct tolerances, raw flags, exact optima, stronger comparators, erasures, causal count distributions, posterior weights, document losses, development selection, receipt chronology and bootstrap intervals. Every observation/target trace is retained as readable, hashed JSON chunks. Executable weights are downloaded/recreated locally and bound by artifact receipts.

Evidence: [Qwen native](results/new_family_audit/qwen2.5-1.5b/results.json), [FP32 deployment](results/deployment_audit/smollm2-360m/float32/results.json), [original INT8 calibration failure](results/deployment_audit/smollm2-360m/dynamic_int8/calibration_failure.shards/manifest.json), [repaired INT8 deployment](results/deployment_audit/smollm2-360m/dynamic_int8_eager/results.shards/manifest.json), [fresh gating protocol](results/pretrained_gating/protocol.json), and [machine-readable summary](results/deployment_transfer_summary.json). The [0.9.0 pretrained study](PRETRAINED_RESULTS.md) remains a separate earlier experiment.
