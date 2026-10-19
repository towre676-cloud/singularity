# Pretrained confirmation: measured advantages and their boundaries

Singularity 0.9.0 runs the observation and prediction tools on three downloaded, publicly released pretrained checkpoints. No neural weights are updated. Model files, tokenizer IDs, document selection, six prediction arms and the audit fault catalogue were frozen before scoring. The strongest result shared by all three models is a cheaper, independently certified behavioral audit. Prediction gains depend on the model.

![Actual retained pretrained audit costs and primary prediction outcomes.](../../docs/assets/pretrained-confirmation.svg)

## Exact audits scale to 1.7 billion parameters

| Model | Parameters | Full pool tokens | Greedy tokens | Exact tokens | Less than greedy | Resident full/panel seconds | Speed ratio |
|---|---:|---:|---:|---:|---:|---:|---:|
| GPT-2 124M | 124,439,808 | 1108 | 196 | **169** | **13.78%** | 3.451 / 0.516 | 6.69× |
| SmolLM2 362M | 361,821,120 | 1089 | 239 | **192** | **19.67%** | 3.818 / 0.589 | 6.49× |
| SmolLM2 1.71B | 1,711,376,384 | 1089 | 239 | **192** | **19.67%** | 12.001 / 1.899 | 6.32× |

Each model has 18 fixed candidate probes. Exact selection and greedy meet the identical requirement of two separating probes for every coverable construction distinction. An independently written scan of all 262,144 subsets confirms each optimum; every single selected-probe erasure is checked. Package verification needs only the standard library. Subsequent model checks need the selected package and the deployed model, with no reference-model forward pass.

All three panels pass both independent clean controls, the actual resident check and a fresh-process CLI check. Every panel detects four of the five held-out variants: CRLF conversion, NFD normalization, temperature 1.1 and weaker truncation. The held-out absolute-position variant is not detected by these panels. Some held-out faults have only one separator, so the one-missing-result guarantee applies only where the retained witness count is at least two.

The padding-mask removal variant has no separating observations on GPT-2 or SmolLM2 1.7B and is explicitly excluded from those construction guarantees; 362M separates it. In Transformers 4.57.1, position IDs can reconstruct a packed-sequence mask in the no-cache path, making explicit-mask removal an executed no-op on GPT-2's real tokens. Changing the framework, cache path or position policy changes the experiment. Four construction distinctions are covered for GPT-2 and 1.7B; five are covered for 362M. A constant RoPE position translation can also preserve relative-position attention. No universal fault-detection, equivalence, quality or safety claim follows from a passing package.

The temperature 1.1 variant preserves every argmax on each full pool and is nevertheless flagged through probability-sensitive observations. Timings are three predeclared interleaved pairs on a shared EPYC CPU with four threads: panel time includes package verification and comparison; full-pool time includes observations only. These are resident audit speed ratios, not faster training or faster ordinary generation. Cold startup remains separate.

## Stronger audit baseline: optimally prune greedy (post hoc)

Deleting redundant probes strengthens the basic greedy baseline. We therefore exhaustively optimize every subset of each original greedy output, checking all 32 subsets per model. This is at least as strong as any deletion-only cleanup. GPT-2 ties exact at 169 tokens. Both SmolLM2 panels cost 214 tokens after optimal greedy pruning, versus the full-pool exact optimum of 192: **10.28% fewer tokens under identical two-witness coverage**. This deterministic post-hoc comparison changes no probe, fault, tolerance or model observation; results are in `results/pretrained_pruned_greedy.json`.

## Prediction: retain the complete comparison

Each model scores the same 24 deterministically selected public documents: eight reference topics, eight license texts and eight Python source modules. Each document contributes its first 512 tokenizer targets, for 12,288 targets per model and 36,864 model-target predictions overall. All six arms score precisely the same targets within a model. Token NLL is meaningful within that tokenizer; these columns do not rank models across tokenizers.

| Model | Neural | Adaptive counts | Fixed 50/50 | Primary online blend | Neural-backed counts | Secondary online neural-backed | Primary loss reduction |
|---|---:|---:|---:|---:|---:|---:|---:|
| GPT-2 124M | 3.100907 | 6.497968 | 3.018716 | 2.786793 | 3.683737 | 2.824878 | **+10.130%** |
| SmolLM2 362M | 1.876680 | 7.062991 | 2.368514 | 1.882145 | 3.017580 | 1.881753 | **-0.291%** |
| SmolLM2 1.71B | 1.278441 | 7.062991 | 1.801192 | 1.284349 | 2.484134 | 1.284042 | **-0.462%** |

Positive reduction favors the blend; negative reduction means the unblended neural model wins. The primary online arm has an equal prior over 21 fixed neural/count mixture weights. The count tables and posteriors reset at document boundaries and observe each target only after predicting it. Neural windows have 256 input tokens and stride 128; overlapping logits already scored are discarded. Counts retain earlier document history across those windows.

The stronger SmolLM2 results do not establish a predictive benefit from the original blend. Use its neural model alone for this measured workload. GPT-2's gain is a real, model-specific result; it does not establish general improvement on modern pretrained language models. Neural-backed counts remain a declared secondary arm, including where they lose.

| Model | Domain | Neural NLL | Primary online NLL | Difference online−neural | Descriptive 95% document interval | Documents improved |
|---|---|---:|---:|---:|---|---:|
| GPT-2 124M | reference_prose | 3.405481 | 3.140889 | -0.264592 | [-0.317585, -0.214898] | 8/8 |
| GPT-2 124M | legal_prose | 2.925972 | 2.586037 | -0.339935 | [-0.722955, -0.118625] | 8/8 |
| GPT-2 124M | source_code | 2.971270 | 2.633454 | -0.337816 | [-0.406884, -0.272470] | 8/8 |
| GPT-2 124M | all_domains | 3.100907 | 2.786793 | -0.314114 | [-0.445026, -0.224852] | 24/24 |
| SmolLM2 362M | reference_prose | 1.982731 | 1.988677 | +0.005946 | [+0.005946, +0.005946] | 0/8 |
| SmolLM2 362M | legal_prose | 2.018674 | 2.023175 | +0.004501 | [+0.001610, +0.005946] | 1/8 |
| SmolLM2 362M | source_code | 1.628636 | 1.634582 | +0.005946 | [+0.005945, +0.005946] | 0/8 |
| SmolLM2 362M | all_domains | 1.876680 | 1.882145 | +0.005464 | [+0.004501, +0.005946] | 1/24 |
| SmolLM2 1.71B | reference_prose | 1.664056 | 1.670003 | +0.005946 | [+0.005946, +0.005946] | 0/8 |
| SmolLM2 1.71B | legal_prose | 0.808961 | 0.814791 | +0.005830 | [+0.005597, +0.005946] | 0/8 |
| SmolLM2 1.71B | source_code | 1.362307 | 1.368253 | +0.005946 | [+0.005946, +0.005946] | 0/8 |
| SmolLM2 1.71B | all_domains | 1.278441 | 1.284349 | +0.005907 | [+0.005830, +0.005946] | 0/24 |

The bootstrap resamples documents, not individual tokens. These licensed documents were used in earlier byte-model work and may overlap the pretrained models' training corpora. This is a fixed transfer benchmark, not a pristine unseen-corpus evaluation. No benchmark arm, document, smoothing value or grid weight was changed after scoring began. All per-target losses, causal weights, per-document regret certificates and execution receipts are retained.

## Full-prefix context sensitivity (post hoc)

The original neural windows retain at most 256 input tokens, while counts remember earlier document targets. A separately declared post-hoc check therefore gives GPT-2 the entire available prefix for all 512 targets of each of the same 24 documents. Neural loss becomes 3.067075 and primary online loss 2.758963 nats/token: a **10.046% reduction**, again improving all 24 documents. Counts are bit-identical to the original study. An independent closed-form joint-likelihood replay checks all 24 blend losses. This is a same-document sensitivity analysis, not new independent confirmation; receipts and readable traces are in `results/pretrained_context512/`.

## A conservative deployment refinement

The small SmolLM2 regression motivates a separate, explicitly post-hoc analysis: `PriorBayesianBlend` assigns 95% prior mass to the pure neural expert and spreads the remaining 5% across the other grid mixtures. This is standard nonuniform-prior Bayesian aggregation. Its data-independent guarantee is

$$L_{\mathrm{online}}\le\min_k\{L_k-\log\pi_k\}\le L_{\mathrm{neural}}-\log(0.95).$$

Thus the whole-document excess over the neural model is at most 0.051294 nats in exact arithmetic, or about 0.000101 nats/token for 512 targets. This limits the adaptation cost; it does not promise an improvement. The 95% choice was motivated by an analytical overhead ceiling, not fitted to document scores. The retrospective replay and theorem tests are separate from the frozen primary/secondary confirmation; its readable metadata and per-document reports are indexed by `results/pretrained_prediction/posthoc_prior_analysis.shards/manifest.json`.

## Identity and reproducibility

| Model | Immutable Hub revision | Execution dtype |
|---|---|---|
| [openai-community/gpt2](https://huggingface.co/openai-community/gpt2/tree/607a30d783dfa663caf39e06633721c8d4cfcd7e) | `607a30d783dfa663caf39e06633721c8d4cfcd7e` | float32 |
| [HuggingFaceTB/SmolLM2-360M](https://huggingface.co/HuggingFaceTB/SmolLM2-360M/tree/f8027fd0eaeea54caa13c31d31b9fdc459c38b49) | `f8027fd0eaeea54caa13c31d31b9fdc459c38b49` | bfloat16 |
| [HuggingFaceTB/SmolLM2-1.7B](https://huggingface.co/HuggingFaceTB/SmolLM2-1.7B/tree/effd688a12921b4cc83e3312b6feb579f70f9c71) | `effd688a12921b4cc83e3312b6feb579f70f9c71` | bfloat16 |

The adapters bind tokenizer vocabulary and processing-pipeline hashes, model configuration, dtype and an explicit checkpoint snapshot digest. The CLI independently hashes actual local files before comparison. Model loading is local-only and disables remote code. Inputs move to the resident embedding device; real execution here is CPU only. GPT-2 uses float32; both SmolLM2 models use bfloat16 to fit the available 8 GiB process memory limit.

New traces are readable JSON under `results/pretrained_prediction/models/*/traces/`. Audit observations are split by execution case under each model's `observations.shards/`; post-hoc prior reports are split by model and document under `posthoc_prior_analysis.shards/`. Their manifests retain metadata, original byte counts and original SHA-256 values. The materialization helper must run before independent replay: it checks every shard and restores the four original JSON receipts byte-for-byte. It also rebuilds the document subset from the existing public cross-domain corpus and reconstructs deterministic gzip receipts against frozen hashes. See [the evidence layout](EVIDENCE_LAYOUT.md). Weights remain outside the repository; scientific protocols and measurements are unchanged.

```sh
python -m pip install -e '.[pretrained]'
python scripts/materialize_pretrained_evidence.py materialize
python scripts/materialize_pretrained_evidence.py materialize --output applications/training_lab/results/pretrained_context512
PYTHONPATH=src python -m unittest tests.test_pretrained_evidence tests.test_pretrained_audit tests.test_pretrained_prediction tests.test_token_experts tests.test_prior_blend -v
python scripts/confirm_pretrained_prediction.py verify --name gpt2
python scripts/confirm_pretrained_prediction.py verify --name smollm2-360m
python scripts/confirm_pretrained_prediction.py verify --name smollm2-1700m
python scripts/verify_pretrained_context.py
python scripts/compare_pruned_pretrained_panels.py
python scripts/replay_pretrained_prior.py --output tmp/prior-replay.json
```

Download matching snapshots with `scripts/fetch_pretrained_models.py --destination /path/to/models --model KEY --receipt applications/training_lab/results/pretrained_audit/KEY/acquisition.json`, using the keys `gpt2`, `smollm2-360m` and `smollm2-1.7b`. The retained acquisition receipt restores identical snapshot bookkeeping after verifying every downloaded file. Recreate the local paths recorded in the prediction protocol or freeze a new output receipt for a new run; retained results refuse to be overwritten. The audit script exposes `freeze`, `run` and `cli`; the prediction script exposes `freeze`, `execute` and `verify`. Freeze a new empty output directory before executing a new measurement.
