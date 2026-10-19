#!/usr/bin/env python3
"""Build the pretrained result guide from all retained model outcomes."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "applications/training_lab"
BASE = LAB / "results"
MODELS = [("gpt2", "gpt2", "GPT-2 124M"),
          ("smollm2-360m", "smollm2-360m", "SmolLM2 362M"),
          ("smollm2-1.7b", "smollm2-1700m", "SmolLM2 1.71B")]


def main():
    audits, predictions, summary = {}, {}, {}
    for audit_key, prediction_key, name in MODELS:
        audits[name] = json.loads((BASE / "pretrained_audit" / audit_key / "results.json").read_text())
        predictions[name] = json.loads((BASE / "pretrained_prediction/models" / prediction_key / "results.json").read_text())
        a, p = audits[name], predictions[name]
        arms = p["domains"]["all_domains"]["arms"]
        summary[name] = {"parameters": a["parameters"], "model_id": a["model_id"], "revision": a["revision"],
                         "audit_exact_tokens": a["selection"]["exact"]["cost"],
                         "audit_greedy_tokens": a["selection"]["greedy"]["cost"], "audit_pool_tokens": a["full_pool_cost"],
                         "audit_cost_reduction_vs_greedy_percent": 100*(1-a["selection"]["exact"]["cost"]/a["selection"]["greedy"]["cost"]),
                         "audit_resident_speed_ratio": a["timing"]["speed_ratio_full_over_panel"],
                         "primary_prediction_log_loss_reduction_percent": 100*(1-arms["online_blend"]["nll_nats_per_token"]/arms["neural"]["nll_nats_per_token"])}
    lines = ["# Pretrained confirmation: measured advantages and their boundaries", "",
             "Singularity 0.9.0 runs the observation and prediction tools on three downloaded, publicly released pretrained checkpoints. No neural weights are updated. Model files, tokenizer IDs, document selection, six prediction arms and the audit fault catalogue were frozen before scoring. The strongest result shared by all three models is a cheaper, independently certified behavioral audit. Prediction gains depend on the model.", "",
             "![Actual retained pretrained audit costs and primary prediction outcomes.](../../docs/assets/pretrained-confirmation.svg)", "",
             "## Exact audits scale to 1.7 billion parameters", "",
             "| Model | Parameters | Full pool tokens | Greedy tokens | Exact tokens | Less than greedy | Resident full/panel seconds | Speed ratio |",
             "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for name, a in audits.items():
        s = summary[name]
        t = a["timing"]["median_seconds"]
        lines.append(f"| {name} | {a['parameters']:,} | {s['audit_pool_tokens']} | {s['audit_greedy_tokens']} | **{s['audit_exact_tokens']}** | **{s['audit_cost_reduction_vs_greedy_percent']:.2f}%** | {t['full_pool']:.3f} / {t['panel_check']:.3f} | {s['audit_resident_speed_ratio']:.2f}× |")
    lines.extend(["", "Each model has 18 fixed candidate probes. Exact selection and greedy meet the identical requirement of two separating probes for every coverable construction distinction. An independently written scan of all 262,144 subsets confirms each optimum; every single selected-probe erasure is checked. Package verification needs only the standard library. Subsequent model checks need the selected package and the deployed model, with no reference-model forward pass.", "",
                  "All three panels pass both independent clean controls, the actual resident check and a fresh-process CLI check. Every panel detects four of the five held-out variants: CRLF conversion, NFD normalization, temperature 1.1 and weaker truncation. The held-out absolute-position variant is not detected by these panels. Some held-out faults have only one separator, so the one-missing-result guarantee applies only where the retained witness count is at least two.", "",
                  "The padding-mask removal variant has no separating observations on GPT-2 or SmolLM2 1.7B and is explicitly excluded from those construction guarantees; 362M separates it. In Transformers 4.57.1, position IDs can reconstruct a packed-sequence mask in the no-cache path, making explicit-mask removal an executed no-op on GPT-2's real tokens. Changing the framework, cache path or position policy changes the experiment. Four construction distinctions are covered for GPT-2 and 1.7B; five are covered for 362M. A constant RoPE position translation can also preserve relative-position attention. No universal fault-detection, equivalence, quality or safety claim follows from a passing package.", "",
                  "The temperature 1.1 variant preserves every argmax on each full pool and is nevertheless flagged through probability-sensitive observations. Timings are three predeclared interleaved pairs on a shared EPYC CPU with four threads: panel time includes package verification and comparison; full-pool time includes observations only. These are resident audit speed ratios, not faster training or faster ordinary generation. Cold startup remains separate.", "",
                  "## Stronger audit baseline: optimally prune greedy (post hoc)", "", "Deleting redundant probes strengthens the basic greedy baseline. We therefore exhaustively optimize every subset of each original greedy output, checking all 32 subsets per model. This is at least as strong as any deletion-only cleanup. GPT-2 ties exact at 169 tokens. Both SmolLM2 panels cost 214 tokens after optimal greedy pruning, versus the full-pool exact optimum of 192: **10.28% fewer tokens under identical two-witness coverage**. This deterministic post-hoc comparison changes no probe, fault, tolerance or model observation; results are in `results/pretrained_pruned_greedy.json`.", "", "## Prediction: retain the complete comparison", "",
                  "Each model scores the same 24 deterministically selected public documents: eight reference topics, eight license texts and eight Python source modules. Each document contributes its first 512 tokenizer targets, for 12,288 targets per model and 36,864 model-target predictions overall. All six arms score precisely the same targets within a model. Token NLL is meaningful within that tokenizer; these columns do not rank models across tokenizers.", "",
                  "| Model | Neural | Adaptive counts | Fixed 50/50 | Primary online blend | Neural-backed counts | Secondary online neural-backed | Primary loss reduction |",
                  "|---|---:|---:|---:|---:|---:|---:|---:|"])
    for name, p in predictions.items():
        arms = p["domains"]["all_domains"]["arms"]
        values = [arms[k]["nll_nats_per_token"] for k in ("neural", "adaptive_count", "fixed_half_blend", "online_blend", "neural_backed_adaptive", "online_neural_backed")]
        lines.append("| " + name + " | " + " | ".join(f"{v:.6f}" for v in values) + f" | **{summary[name]['primary_prediction_log_loss_reduction_percent']:+.3f}%** |")
    lines.extend(["", "Positive reduction favors the blend; negative reduction means the unblended neural model wins. The primary online arm has an equal prior over 21 fixed neural/count mixture weights. The count tables and posteriors reset at document boundaries and observe each target only after predicting it. Neural windows have 256 input tokens and stride 128; overlapping logits already scored are discarded. Counts retain earlier document history across those windows.", "",
                  "The stronger SmolLM2 results do not establish a predictive benefit from the original blend. Use its neural model alone for this measured workload. GPT-2's gain is a real, model-specific result; it does not establish general improvement on modern pretrained language models. Neural-backed counts remain a declared secondary arm, including where they lose.", "",
                  "| Model | Domain | Neural NLL | Primary online NLL | Difference online−neural | Descriptive 95% document interval | Documents improved |",
                  "|---|---|---:|---:|---:|---|---:|"])
    for name, p in predictions.items():
        for domain in ("reference_prose", "legal_prose", "source_code", "all_domains"):
            d = p["domains"][domain]
            pair = d["paired"]["online_blend_minus_neural"]
            low, high = pair["percentile_95_interval"]
            lines.append(f"| {name} | {domain} | {d['arms']['neural']['nll_nats_per_token']:.6f} | {d['arms']['online_blend']['nll_nats_per_token']:.6f} | {pair['difference_nats_per_token']:+.6f} | [{low:+.6f}, {high:+.6f}] | {pair['documents_first_better']}/{pair['documents']} |")
    lines.extend(["", "The bootstrap resamples documents, not individual tokens. These licensed documents were used in earlier byte-model work and may overlap the pretrained models' training corpora. This is a fixed transfer benchmark, not a pristine unseen-corpus evaluation. No benchmark arm, document, smoothing value or grid weight was changed after scoring began. All per-target losses, causal weights, per-document regret certificates and execution receipts are retained.", "",
                  "## Full-prefix context sensitivity (post hoc)", "", "The original neural windows retain at most 256 input tokens, while counts remember earlier document targets. A separately declared post-hoc check therefore gives GPT-2 the entire available prefix for all 512 targets of each of the same 24 documents. Neural loss becomes 3.067075 and primary online loss 2.758963 nats/token: a **10.046% reduction**, again improving all 24 documents. Counts are bit-identical to the original study. An independent closed-form joint-likelihood replay checks all 24 blend losses. This is a same-document sensitivity analysis, not new independent confirmation; receipts and readable traces are in `results/pretrained_context512/`.", "", "## A conservative deployment refinement", "",
                  "The small SmolLM2 regression motivates a separate, explicitly post-hoc analysis: `PriorBayesianBlend` assigns 95% prior mass to the pure neural expert and spreads the remaining 5% across the other grid mixtures. This is standard nonuniform-prior Bayesian aggregation. Its data-independent guarantee is", "",
                  "$$L_{\\mathrm{online}}\\le\\min_k\\{L_k-\\log\\pi_k\\}\\le L_{\\mathrm{neural}}-\\log(0.95).$$", "",
                  "Thus the whole-document excess over the neural model is at most 0.051294 nats in exact arithmetic, or about 0.000101 nats/token for 512 targets. This limits the adaptation cost; it does not promise an improvement. The 95% choice was motivated by an analytical overhead ceiling, not fitted to document scores. The retrospective replay and theorem tests are separate from the frozen primary/secondary confirmation; its readable metadata and per-document reports are indexed by `results/pretrained_prediction/posthoc_prior_analysis.shards/manifest.json`.", "",
                  "## Identity and reproducibility", "",
                  "| Model | Immutable Hub revision | Execution dtype |", "|---|---|---|"])
    for name, a in audits.items():
        lines.append(f"| [{a['model_id']}](https://huggingface.co/{a['model_id']}/tree/{a['revision']}) | `{a['revision']}` | {a['environment']['dtype']} |")
    lines.extend(["", "The adapters bind tokenizer vocabulary and processing-pipeline hashes, model configuration, dtype and an explicit checkpoint snapshot digest. The CLI independently hashes actual local files before comparison. Model loading is local-only and disables remote code. Inputs move to the resident embedding device; real execution here is CPU only. GPT-2 uses float32; both SmolLM2 models use bfloat16 to fit the available 8 GiB process memory limit.", "",
                  "New traces are readable JSON under `results/pretrained_prediction/models/*/traces/`. Audit observations are split by execution case under each model's `observations.shards/`; post-hoc prior reports are split by model and document under `posthoc_prior_analysis.shards/`. Their manifests retain metadata, original byte counts and original SHA-256 values. The materialization helper must run before independent replay: it checks every shard and restores the four original JSON receipts byte-for-byte. It also rebuilds the document subset from the existing public cross-domain corpus and reconstructs deterministic gzip receipts against frozen hashes. See [the evidence layout](EVIDENCE_LAYOUT.md). Weights remain outside the repository; scientific protocols and measurements are unchanged.", "",
                  "```sh", "python -m pip install -e '.[pretrained]'", "python scripts/materialize_pretrained_evidence.py materialize", "python scripts/materialize_pretrained_evidence.py materialize --output applications/training_lab/results/pretrained_context512", "PYTHONPATH=src python -m unittest tests.test_pretrained_evidence tests.test_pretrained_audit tests.test_pretrained_prediction tests.test_token_experts tests.test_prior_blend -v", "python scripts/confirm_pretrained_prediction.py verify --name gpt2", "python scripts/confirm_pretrained_prediction.py verify --name smollm2-360m", "python scripts/confirm_pretrained_prediction.py verify --name smollm2-1700m", "python scripts/verify_pretrained_context.py", "python scripts/compare_pruned_pretrained_panels.py", "python scripts/replay_pretrained_prior.py --output tmp/prior-replay.json", "```", "",
                  "Download matching snapshots with `scripts/fetch_pretrained_models.py --destination /path/to/models --model KEY --receipt applications/training_lab/results/pretrained_audit/KEY/acquisition.json`, using the keys `gpt2`, `smollm2-360m` and `smollm2-1.7b`. The retained acquisition receipt restores identical snapshot bookkeeping after verifying every downloaded file. Recreate the local paths recorded in the prediction protocol or freeze a new output receipt for a new run; retained results refuse to be overwritten. The audit script exposes `freeze`, `run` and `cli`; the prediction script exposes `freeze`, `execute` and `verify`. Freeze a new empty output directory before executing a new measurement.", ""])
    (LAB / "PRETRAINED_RESULTS.md").write_text("\n".join(lines))
    (BASE / "pretrained_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(LAB / "PRETRAINED_RESULTS.md")


if __name__ == "__main__":
    main()
