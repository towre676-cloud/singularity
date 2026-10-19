#!/usr/bin/env python3
"""Generate the 0.10 deployment/transfer report from completed evidence only.

This file is deliberately separate from every frozen experiment dependency.
It never executes a model, chooses a predictor, or changes measured evidence.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "applications/training_lab/results"
MODEL_ORDER = ("gpt2", "smollm2-360m", "smollm2-1_7b", "qwen25-1_5b")
LABELS = {"gpt2": "GPT-2 124M", "smollm2-360m": "SmolLM2 362M", "smollm2-1_7b": "SmolLM2 1.71B", "qwen25-1_5b": "Qwen2.5 1.54B"}


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+"\n")


def snapshot():
    sources = {}
    def read(relative):
        path = RESULTS / relative
        value = json.loads(path.read_text())
        sources[str(path.relative_to(ROOT))] = file_sha(path)
        return value
    qroot = "new_family_audit/qwen2.5-1.5b/"
    q = read(qroot+"results.json")
    qp = read(qroot+"pruned_greedy_posthoc.json")
    audit = [{"id": "qwen_native", "label": "Qwen2.5 1.54B\nnative BF16", "model_id": q["model_id"],
              "parameters": q["parameters"], "representation": "native_bfloat16", "pool_cost": q["full_pool_cost"],
              "exact_cost": q["selection"]["exact"]["cost"], "pruned_greedy_cost": qp["optimally_pruned_greedy"]["cost"],
              "basic_greedy_cost": q["selection"]["greedy"]["cost"], "pruned_comparator_status": qp["analysis_status"],
              "full_seconds": q["timing"]["median_seconds"]["full_pool"], "exact_seconds": q["timing"]["median_seconds"]["panel_check"],
              "speed_ratio": q["timing"]["speed_ratio_full_over_panel"], "construction_covered": len(q["selection"]["eligible_faults"]),
              "construction_unavailable": q["selection"]["unavailable_faults"],
              "heldout": {k: v for k, v in q["panels"]["exact"]["faults"].items() if v["heldout"]},
              "clean_pool_flags": q["pool_clean_false_alarms"], "clean_panel_flags": q["panels"]["exact"]["clean_false_alarms"],
              "timing_scope": "native BF16; full pool observation only, exact includes package verification/comparison",
              "cli": read(qroot+"cli_check.json")}]
    original_int8_protocol = read("deployment_audit/smollm2-360m/dynamic_int8/protocol.json")
    original_int8_failure = read("deployment_audit/smollm2-360m/dynamic_int8/calibration_failure.json")
    original_int8_artifact = read("deployment_audit/smollm2-360m/dynamic_int8/artifact.json")
    failure_diagnostics = []
    margin = original_int8_protocol["protocol"]["tolerance"]["tie_margin"]
    for clean_index, rows in enumerate(original_int8_failure["calibration"]):
        mismatches = []
        for index, (actual, expected) in enumerate(zip(rows, original_int8_failure["reference"])):
            count = sum(got != want and expected["top_gap"][t] > margin for t, (got, want) in enumerate(zip(actual["argmax"], expected["argmax"])))
            if count:
                mismatches.append({"probe": index, "non_tie_discrete_changes": count})
        failure_diagnostics.append({"calibration": clean_index, "unstable_probe_count": len(mismatches),
                                    "non_tie_discrete_changes": sum(row["non_tie_discrete_changes"] for row in mismatches)})
    for target, folder in (("float32", "float32"), ("dynamic_int8", "dynamic_int8_eager")):
        base = f"deployment_audit/smollm2-360m/{folder}/"
        data = read(base+"results.json")
        selected = data["selection"]
        exact = selected["exact"]["cost"]
        random = selected["random_panels"]
        cli = {}
        cli_paths = {*((RESULTS / base).glob("cli_*.json")), *((RESULTS / base).glob("cli_checks/*.json"))}
        for path in sorted(cli_paths):
            receipt = read(str(path.relative_to(RESULTS)))
            payload = receipt.get("report", receipt)
            compact = {key: value for key, value in payload.items() if key != "probes"}
            if "execution" in compact:
                compact["execution"] = {key: value for key, value in compact["execution"].items() if key != "cache_receipts"}
            cli[path.stem] = compact
        compact_artifact = {key: value for key, value in data["artifact"].items() if key != "quantized_linear_modules"}
        frozen_protocol = read(base+"protocol.json")["protocol"]
        compact_protocol = {key: frozen_protocol[key] for key in ("status", "approved_int8_execution", "parent_protocol_file_sha256", "parent_calibration_failure_file_sha256") if key in frozen_protocol}
        audit.append({"id": "smol_"+target, "label": "SmolLM2 362M\n"+{"float32": "FP32", "dynamic_int8": "INT8 eager repair"}[target],
                      "model_id": data["model_id"], "parameters": data["artifact"]["float_parameter_count"],
                      "representation": target, "display_representation": {"float32": "FP32 (prospective)", "dynamic_int8": "INT8 eager (post-calibration repair)"}[target],
                      "pool_cost": data["full_pool_cost"], "exact_cost": exact,
                      "pruned_greedy_cost": selected["pruned_greedy"]["cost"], "basic_greedy_cost": selected["greedy"]["cost"],
                      "random_median_cost": selected["random_median"]["cost"], "random_min_cost": min(r["cost"] for r in random),
                      "random_max_cost": max(r["cost"] for r in random), "random_exact_matches": sum(r["cost"] == exact for r in random),
                      "random_trials": len(random), "construction_covered": len(selected["eligible_faults"]),
                      "construction_unavailable": selected["unavailable_faults"],
                      "heldout": {k: v for k, v in data["panels"]["exact"]["faults"].items() if v["heldout"]},
                      "clean_pool_flags": data["pool_clean_false_alarms"], "clean_panel_flags": data["panels"]["exact"]["clean_false_alarms"],
                      "full_seconds": data["timing"]["median_seconds"]["full_pool"], "exact_seconds": data["timing"]["median_seconds"]["exact"],
                      "speed_ratio": data["timing"]["amortization"]["exact"]["full_pool_over_panel"],
                      "timing": data["timing"], "artifact": compact_artifact, "cli": cli,
                      "protocol": compact_protocol, "folder": folder,
                      "timing_scope": data["timing"]["full_pool_includes"]})
    protocol = read("pretrained_gating/protocol.json")
    predictions = []
    for name in MODEL_ORDER:
        base = f"pretrained_gating/models/{name}/"
        result = read(base+"heldout_analysis.json")
        selection = read(base+"selection.json")
        development = read(base+"development/results.json")
        heldout = read(base+"heldout/results.json")
        primary = result["comparisons"]["all_domains"]["primary_selected_minus_neural"]
        if primary["documents"] != 24 or primary["targets"] != 12288:
            raise ValueError("expected complete 24-document/12,288-target heldout evidence")
        compact_comparisons = {domain: {arm: {key: value[key] for key in ("difference_nats_per_token", "loss_reduction_percent")}
                                        for arm, value in comparisons.items()}
                               for domain, comparisons in result["comparisons"].items()}
        predictions.append({"id": name, "label": LABELS[name], "selected_arm": result["selected_arm"],
                            "primary": primary, "comparisons": compact_comparisons,
                            "development_candidate_count": len(selection["development_candidate_losses"]),
                            "development_documents": len(development["documents"]), "heldout_documents": len(heldout["documents"]),
                            "scope": result["scope"], "ceiling_nats_per_document": result["neural_extra_loss_ceiling_nats_per_document"]})
    for row in audit:
        row["exact_saving_vs_pruned_percent"] = 100*(1-row["exact_cost"]/row["pruned_greedy_cost"])
        row["heldout_detected"] = sum(v["detected"] for v in row["heldout"].values())
        row["heldout_total"] = len(row["heldout"])
        row["heldout_missed"] = [k for k, v in row["heldout"].items() if not v["detected"]]
        row["clean_pool_cases_without_flags"] = sum(not v for v in row["clean_pool_flags"].values())
    counts = Counter((d["split"], d["domain"]) for d in protocol["documents"])
    return {"schema": "singularity.deployment-transfer-summary/1", "release": "0.10.0", "sources_sha256": sources,
            "audits": audit, "predictions": predictions,
            "corpus_counts": [{"split": split, "domain": domain, "documents": count} for (split, domain), count in sorted(counts.items())],
            "evaluated_targets": sum((r["development_documents"]+r["heldout_documents"])*protocol["max_targets"] for r in predictions),
            "original_int8_calibration_failure": {"error": original_int8_failure["error"], "diagnostics": failure_diagnostics,
                                                  "quantized_linear_count": original_int8_artifact["quantized_linear_count"],
                                                  "state_reload_identical": original_int8_artifact["state_reload_identical"],
                                                  "no_package_built": True, "refinement_status": "post-calibration eager-only contract repair"},
            "neural_training_updates": 0, "scope": "CPU study; all exact coverage is catalogue-specific; no universal prediction gain or generation acceleration"}


def signed(value):
    return f"{value:+.9g}"


def report_text(summary):
    q, fp, qi = summary["audits"]
    lines = ["# Singularity 0.10.0: deployment artifacts and fresh transfer", "",
             "**Smaller model checks now survive a new model family and actual deployment transformations.** This release evaluates Qwen2.5-1.5B, real FP32/TorchScript/INT8 SmolLM2 artifacts, and prospective repetition gating on fresh development and held-out documents. Neural weights remain frozen throughout.", "",
             "![Audit costs, resident latency, and fresh held-out prediction outcomes.](../../docs/assets/deployment-transfer.svg)", "",
             "## An independent model family", "",
             f"The untouched Qwen2.5-1.5B family has {q['parameters']:,} parameters. Its exact two-witness panel costs **{q['exact_cost']} native input tokens**, compared with **{q['pruned_greedy_cost']}** after optimally pruning the greedy output: **{q['exact_saving_vs_pruned_percent']:.2f}% fewer tokens**. Scanning all 262,144 subsets independently confirms the optimum. The pruned-greedy comparison is an explicitly post-hoc deterministic calculation on the unchanged construction table.", "",
             f"A resident check takes **{q['exact_seconds']:.3f}s**, compared with **{q['full_seconds']:.3f}s** to observe the full pool (**{q['speed_ratio']:.2f}×**). All {q['construction_covered']} declared construction distinctions have two panel witnesses. The panel flags **{q['heldout_detected']}/{q['heldout_total']} held-out variants**; the misses are `{ '`, `'.join(q['heldout_missed']) }`. Neither of its two independent clean controls flags, and the separate fresh-process package check passes. A constant position translation can be invariant under RoPE; these observations do not create a universal guarantee for missing variants.", "",
             "## Actual serialization, graph and quantized artifacts", "",
             "The deployment study uses the same 18 fixed probe texts and a separate service that executes preprocessing/forward faults outside the audit adapter. FP32 weights are serialized as Safetensors and reloaded. An explicit-mask eager Llama graph is traced, saved, verified and reloaded as TorchScript. The INT8 target quantizes actual Linear modules, saves their packed state, reconstructs a fresh quantized model, and checks state identity after weights-only loading. Receipts retain actual SDPA kernel calls, quantized-module forward calls and cache sequence lengths.", "",
             "| Target | Full pool tokens | Exact | Optimally pruned greedy | Pruned random median | Random trials reaching exact |", "|---|---:|---:|---:|---:|---:|"]
    for row in (fp, qi):
        lines.append(f"| {row['display_representation']} | {row['pool_cost']} | **{row['exact_cost']}** | {row['pruned_greedy_cost']} | {row['random_median_cost']} | {row['random_exact_matches']}/{row['random_trials']} |")
    lines += ["", "All compared panels meet the same two-witness requirement on the same coverable construction distinctions. Each random feasible prefix is optimally pruned, and every trial is retained. A randomized heuristic can find the exact cost; exact selection additionally certifies that no cheaper panel exists.", "",
              "| Target | Full package check | Exact package check | Full/exact ratio | Incremental build break-even | Gross build break-even | Build + artifact preparation |", "|---|---:|---:|---:|---:|---:|---:|"]
    for row in (fp, qi):
        amort = row["timing"]["amortization"]["exact"]
        lines.append(f"| {row['display_representation']} | {row['full_seconds']:.3f}s | **{row['exact_seconds']:.3f}s** | {row['speed_ratio']:.2f}× | {amort['conservative_incremental_build_checks']} checks | {amort['gross_all_comparators_build_checks']} checks | {amort['including_artifact_checks']} checks |")
    lines += ["", "Three predeclared interleaved timing rounds follow warmup, on one shared CPU host with four threads. Both full and reduced deployment checks include package verification, model inference and comparison. Incremental construction excludes common reference/calibration but conservatively charges all comparator selection work to each panel. Gross construction includes all reference/calibration, catalogue observations, selection and package creation. Artifact preparation includes source loading, serialization/conversion and reload; fresh-process import and disk-verification costs are separate. These timings describe audit checks, not generation or training.", "",
              "| Target | Construction distinctions covered | Executed held-out variants flagged | Clean full-pool cases without flags |", "|---|---:|---:|---:|"]
    for row in (fp, qi):
        lines.append(f"| {row['display_representation']} | {row['construction_covered']} | {row['heldout_detected']}/{row['heldout_total']} | {row['clean_pool_cases_without_flags']}/{len(row['clean_pool_flags'])} |")
    lines += ["", "FP32 independent clean controls include SDPA, batching, thread/order changes, a genuine two-chunk KV-cache path, and the saved TorchScript graph. Every selected-result erasure is checked against the retained coverage witness. The graph contract is bounded CPU FP32 eager Llama, batch 1–3, width 1–96, unscaled RoPE and no cache; native cached execution is checked separately.", "",
              f"**The original prospective INT8 calibration did not produce a package.** Its SDPA batch-one control changed non-tie argmax outputs on **{summary['original_int8_calibration_failure']['diagnostics'][0]['unstable_probe_count']}/18 probes**, totaling **{summary['original_int8_calibration_failure']['diagnostics'][0]['non_tie_discrete_changes']} positions**. The eager thread-one control remained stable. All {summary['original_int8_calibration_failure']['quantized_linear_count']} quantized Linear modules and exact packed-state reload identity were verified. The complete failure, original protocol and quantized artifact receipt are retained. The cause of the backend drift is not established by this experiment.", "",
              "The reported INT8 package is an explicitly **post-calibration eager-only contract repair**, frozen in a separate script/output directory before new forwards. It keeps every probe, fault, tolerance and comparator unchanged. It calibrates eager batch-one full prefill at threads one and two; SDPA batch-one is moved to a held-out clean transfer. The package metadata binds its approved backend/batch/cache envelope and the original failure/protocol hashes before all measured checks.", "",
              "Dynamic INT8 has its own baseline and tolerances. Its activation scales depend on batch/chunk extent, so its approved execution uses eager batch-one full prefill. SDPA, batch-three and cache controls are explicitly clean transfers outside that envelope. Their observed flags are numerical drift, not silently relabeled deployment faults. The checker reports `outside_calibration` and exit 3 for these requests, preserving raw measurements. The clean-control details below distinguish these cases:", "",
              "| INT8 clean control | Flagged full-pool probes | Flagged exact-panel probes |", "|---|---:|---:|"]
    for name, flags in qi["clean_pool_flags"].items():
        lines.append(f"| `{name}` | {len(flags)} | {len(qi['clean_panel_flags'][name])} |")
    lines += ["", "INT8 cache-drop variants also leave the approved full-prefill envelope. When healthy chunking itself flags, a dropped-cache flag establishes an observational difference from the reference, not specificity to cache corruption. FP32 supports the stronger cache-correctness comparison: its healthy cached controls pass while the dropped-prefix variants flag. The exact catalogue witness remains valid for the stored observations in both representations.", "",
              f"FP32 held-out misses: `{ '`, `'.join(fp['heldout_missed']) }`. INT8 held-out misses: `{ '`, `'.join(qi['heldout_missed']) }`. Construction distinctions with fewer than two pool witnesses are retained as unavailable: FP32 `{json.dumps(fp['construction_unavailable'], sort_keys=True)}`; INT8 `{json.dumps(qi['construction_unavailable'], sort_keys=True)}`.", "",
              "## Fresh prediction: select on development, then evaluate once", "",
              f"Four pinned models each score 12 development documents and 24 held-out documents, 512 native-token targets per document: **{summary['evaluated_targets']:,} evaluated targets**. Each split contains literary prose, technical reference and Python source. Neural models see the entire available prefix. The count model, repetition features and blending posteriors use only preceding targets and reset for every document. No neural parameter is updated.", "",
              "The primary selection considers pure neural and 18 protected repetition policies, using development aggregate log loss only. A committed selection receipt precedes every held-out forward. Each gate uses prefix context order/support; the protected predictor gives pure neural 95% prior mass. The mathematical whole-document excess-loss ceiling is $-\\log(0.95)=0.0512933$ nats in exact arithmetic. Protection limits overhead; it does not promise improvement. The declared hierarchy and ungated protection are secondary comparisons; all policy diagnostics remain visible.", "",
              "| Model | Development-selected arm | Neural NLL | Selected NLL | Selected − neural | Loss reduction | Documents better / worse / tied |", "|---|---|---:|---:|---:|---:|---:|"]
    for row in summary["predictions"]:
        p = row["primary"]
        lines.append(f"| {row['label']} | `{row['selected_arm']}` | {p['neural_nll_nats_per_token']:.9g} | {p['candidate_nll_nats_per_token']:.9g} | {signed(p['difference_nats_per_token'])} | {p['loss_reduction_percent']:+.6g}% | {p['documents_improved']} / {p['documents_worse']} / {p['documents_numerically_tied']} |")
    lines += ["", "NLL is nats per native tokenizer token and is compared only within each model. A document is numerically tied when its whole-document loss difference is within 1e-10 nats. Pure-neural fallback is an allowed primary outcome with zero change.", "",
              "| Model | Paired difference, 95% descriptive document-bootstrap interval |", "|---|---|"]
    for row in summary["predictions"]:
        lo, hi = row["primary"]["descriptive_paired_document_bootstrap_95_interval"]
        lines.append(f"| {row['label']} | [{signed(lo)}, {signed(hi)}] nats/token |")
    lines += ["", "The predeclared secondary predictors are retained alongside the selected primary:", "",
              "| Model | Selected primary reduction | Protected hierarchy reduction | Ungated protected reduction |", "|---|---:|---:|---:|"]
    for row in summary["predictions"]:
        comparisons = row["comparisons"]["all_domains"]
        values = [comparisons[key]["loss_reduction_percent"] for key in ("primary_selected_minus_neural", "secondary_hierarchy_minus_neural", "secondary_ungated_minus_neural")]
        lines.append(f"| {row['label']} | {values[0]:+.6g}% | {values[1]:+.6g}% | {values[2]:+.6g}% |")
    lines += ["", "Primary differences by held-out domain:", "",
              "| Model | Literary prose | Technical reference | Python source |", "|---|---:|---:|---:|"]
    for row in summary["predictions"]:
        values = [row["comparisons"][domain]["primary_selected_minus_neural"]["difference_nats_per_token"] for domain in ("literary_prose", "technical_reference", "python_source")]
        lines.append(f"| {row['label']} | {signed(values[0])} | {signed(values[1])} | {signed(values[2])} |")
    lines += ["", "These intervals resample documents in 10,000 draws, not individual dependent tokens. The documents/source files are distinct between development and held-out sets, while source projects, some module names and model pretraining may overlap. This is a fresh experimental split, not proof of unseen pretraining data or universal generalization. A tiny improvement must be interpreted at its actual numerical and practical scale.", "",
              "## Saved-artifact command-line checks", "",
              "Fresh-process checks validate artifact/source/tokenizer identities before using only the selected saved reference observations. Their cold validation/load costs remain separate from resident audit timing.", "",
              "| Target / check | Deployment status | Raw verdict | Resident seconds | Validation + load seconds |", "|---|---|---|---:|---:|"]
    for row in (fp, qi):
        for name, receipt in row["cli"].items():
            report = receipt.get("report", receipt)
            if "seconds" not in report:
                continue
            lines.append(f"| {row['representation']} / `{name}` | `{report.get('deployment_status', 'unrecorded')}` | `{report['verdict']}` | {report['seconds']['resident_check']:.3f} | {report['seconds']['artifact_validation_and_load']:.3f} |")
    lines += ["", "## Use and reproduce", "",
              "The [deployment guide](DEPLOYMENT_GUIDE.md) gives download, freeze, construction and existing-artifact check commands. `scripts/check_deployment_package.py` verifies identities, then checks an existing eager, SDPA, TorchScript or quantized artifact using the saved package. It reports cold setup and resident check costs separately. The general [`ProtectedRepetitionBlend`](../../src/singularity/training/repetition_blend.py) exposes predict-before-observe adaptation with a pure-neural fallback.", "",
              "```sh", "python scripts/materialize_pretrained_evidence.py materialize", "PYTHONPATH=src python -m unittest tests.test_new_family_evidence -v", "python scripts/verify_deployment_confirmation.py", "python scripts/verify_gating_confirmation.py", "python scripts/report_deployment_transfer.py --render --update-readme", "```", "",
              "The independent verifiers reconstruct tolerances, raw flags, exact optima, stronger comparators, erasures, causal count distributions, posterior weights, document losses, development selection, receipt chronology and bootstrap intervals. Every observation/target trace is retained as readable, hashed JSON chunks. Executable weights are downloaded/recreated locally and bound by artifact receipts.", "",
              "Evidence: [Qwen native](results/new_family_audit/qwen2.5-1.5b/results.json), [FP32 deployment](results/deployment_audit/smollm2-360m/float32/results.json), [original INT8 calibration failure](results/deployment_audit/smollm2-360m/dynamic_int8/calibration_failure.shards/manifest.json), [repaired INT8 deployment](results/deployment_audit/smollm2-360m/dynamic_int8_eager/results.shards/manifest.json), [fresh gating protocol](results/pretrained_gating/protocol.json), and [machine-readable summary](results/deployment_transfer_summary.json). The [0.9.0 pretrained study](PRETRAINED_RESULTS.md) remains a separate earlier experiment.", ""]
    return "\n".join(lines)


def readme_section(summary):
    q, fp, qi = summary["audits"]
    gpt = next(row for row in summary["predictions"] if row["id"] == "gpt2")["primary"]
    fallbacks = [row["label"] for row in summary["predictions"] if row["selected_arm"] == "neural"]
    return "\n".join(["<!-- BEGIN deployment-transfer -->", "## Make every model check count.", "",
        f"**New in 0.10.0: real deployment artifacts and an untouched model family.** On Qwen2.5-1.5B, a certified panel uses **{q['exact_cost']} input tokens instead of {q['pruned_greedy_cost']}** for optimally pruned greedy selection, while a resident audit takes **{q['exact_seconds']:.2f}s instead of {q['full_seconds']:.2f}s**. The deployment study then checks actual Safetensors reloads, an executable TorchScript graph, dynamic INT8 modules, SDPA attention and KV caches. FP32 clean graph/cache/backend controls pass, and exact selection retains two witnesses for every covered construction distinction.", "",
        "![Exact audit costs, resident check times, and prospectively selected prediction outcomes on fresh held-out documents.](docs/assets/deployment-transfer.svg)", "",
        f"**{gpt['loss_reduction_percent']:.2f}% lower GPT-2 loss on fresh held-out text.** A protected repetition gate, selected on 12 development documents before evaluation, improves {gpt['documents_improved']}/24 held-out documents. The same selection rule retains pure neural for {', '.join(fallbacks)}. All **{summary['evaluated_targets']:,} evaluated targets**, clean-transfer limits and missed fault variants are retained. The original INT8 SDPA calibration fails; a separately frozen post-calibration eager-only contract provides the bounded deployment package. Read the [**complete 0.10.0 evidence**](applications/training_lab/DEPLOYMENT_RESULTS.md) or [**check a saved deployment artifact**](applications/training_lab/DEPLOYMENT_GUIDE.md).", "<!-- END deployment-transfer -->", ""])


def update_readme(summary):
    path = ROOT / "README.md"
    text = path.read_text()
    section = readme_section(summary)
    if "<!-- BEGIN deployment-transfer -->" in text:
        text = re.sub(r"<!-- BEGIN deployment-transfer -->.*?<!-- END deployment-transfer -->\n?", section, text, flags=re.S)
    else:
        text = text.replace("## Real pretrained models. Exact checks. Evidence you can replay.", section+"\n## Real pretrained models. Exact checks. Evidence you can replay.", 1)
    text = text.replace("[**See the pretrained results**]", "[**Deployment evidence**](applications/training_lab/DEPLOYMENT_RESULTS.md) · [**See the pretrained results**]", 1) if "[**Deployment evidence**]" not in text else text
    path.write_text(text)
    for relative in ("pyproject.toml", "src/singularity/__init__.py"):
        path = ROOT / relative
        raw = path.read_text()
        if '"0.10.0"' not in raw:
            if '"0.9.0"' not in raw:
                raise ValueError("unexpected release version: "+relative)
            path.write_text(raw.replace('"0.9.0"', '"0.10.0"', 1))


def render(summary):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.ticker import MaxNLocator
    bg, panel, ink, muted = "#09131f", "#111f30", "#e9f1fa", "#a2b5cc"
    mint, lavender, slate, amber = "#63e6bc", "#b9a2ff", "#69839e", "#ffc779"
    plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": ink, "axes.labelcolor": muted,
                         "xtick.color": muted, "ytick.color": muted, "axes.edgecolor": "#30445a",
                         "svg.fonttype": "none", "font.size": 11})
    fig = plt.figure(figsize=(16, 10), facecolor=bg)
    gs = fig.add_gridspec(2, 2, left=.085, right=.965, top=.80, bottom=.20, hspace=.62, wspace=.25, height_ratios=[1, .85])
    ax_cost, ax_time, ax_pred = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1]), fig.add_subplot(gs[1, :])
    for ax in (ax_cost, ax_time, ax_pred):
        ax.set_facecolor(panel)
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", color="#2a4056", alpha=.55, linewidth=.7, zorder=0)
        ax.tick_params(length=0, pad=8)
    fig.text(.065, .94, "SINGULARITY   /   0.10.0", color=mint, fontsize=13, weight="bold", family="DejaVu Sans Mono")
    fig.text(.065, .885, "Smaller checks. Real deployment artifacts.", fontsize=28, weight="bold")
    fig.text(.065, .846, "Exact audit selection across Qwen and SmolLM2 · prospective prediction choices on fresh documents", fontsize=13, color=muted)
    rows, x = summary["audits"], np.arange(3)
    width = .32
    for offset, key, color, name in ((-width/2, "pruned_greedy_cost", lavender, "Optimally pruned greedy"), (width/2, "exact_cost", mint, "Exact certified optimum")):
        bars = ax_cost.bar(x+offset, [r[key] for r in rows], width=width*.87, color=color, label=name, zorder=3)
        for bar in bars:
            ax_cost.text(bar.get_x()+bar.get_width()/2, bar.get_height()+5, f"{bar.get_height():.0f}", ha="center", color=ink, fontsize=12, weight="bold")
    ax_cost.set_title("A   Fewer tokens, identical declared coverage", loc="left", pad=16, fontsize=13, weight="bold")
    ax_cost.set_xticks(x, [r["label"] for r in rows]); ax_cost.set_ylim(0, max(r["pruned_greedy_cost"] for r in rows)*1.25)
    ax_cost.set_ylabel("Native input tokens per audit panel")
    ax_cost.legend(loc="upper center", bbox_to_anchor=(.5, -.27), ncol=2, frameon=False, fontsize=10, labelcolor=ink)
    for offset, key, color, name in ((-width/2, "full_seconds", slate, "Full probe pool"), (width/2, "exact_seconds", mint, "Exact package check")):
        bars = ax_time.bar(x+offset, [r[key] for r in rows], width=width*.87, color=color, label=name, zorder=3)
        for bar in bars:
            ax_time.text(bar.get_x()+bar.get_width()/2, bar.get_height()+.22, f"{bar.get_height():.2f}", ha="center", color=ink, fontsize=11, weight="bold")
    ax_time.set_title("B   Less resident inference for repeated checks", loc="left", pad=16, fontsize=13, weight="bold")
    ax_time.set_xticks(x, [r["label"] for r in rows]); ax_time.set_ylabel("Median seconds · CPU, four threads")
    ax_time.set_ylim(0, max(r["full_seconds"] for r in rows)*1.25)
    ax_time.yaxis.set_major_locator(MaxNLocator(5))
    ax_time.legend(loc="upper center", bbox_to_anchor=(.5, -.27), ncol=2, frameon=False, fontsize=10, labelcolor=ink)
    prediction = summary["predictions"]
    px = np.arange(len(prediction))
    values = [r["primary"]["difference_nats_per_token"] for r in prediction]
    intervals = [r["primary"]["descriptive_paired_document_bootstrap_95_interval"] for r in prediction]
    centers = [(low+high)/2 for low, high in intervals]
    half_width = [(high-low)/2 for low, high in intervals]
    ax_pred.axhline(0, color=ink, linewidth=.9, alpha=.65)
    ax_pred.errorbar(px, centers, yerr=half_width, fmt="none", capsize=7, capthick=1.8, ecolor=lavender, elinewidth=2, zorder=3)
    ax_pred.scatter(px, values, s=81, color=mint, zorder=4)
    def policy_label(row):
        if row["selected_arm"] == "neural":
            return "Pure neural selected"
        match = re.fullmatch(r"order(\d+)_support(\d+)_alpha(\d+)", row["selected_arm"])
        if not match:
            return row["selected_arm"]
        order, support, alpha = map(int, match.groups())
        return f"Gate: order≥{order}, support≥{support}\nmix {alpha/100:g}"
    labels = [r["label"]+"\n"+policy_label(r) for r in prediction]
    ax_pred.set_xticks(px, labels, fontsize=10); ax_pred.set_xlim(-.5, len(prediction)-.5)
    ax_pred.set_title("C   Prediction choices frozen on development, evaluated on 24 held-out documents per model", loc="left", pad=17, fontsize=13, weight="bold")
    ax_pred.set_ylabel("Selected − neural\nnats / native token\nnegative favors selected", fontsize=10)
    ax_pred.ticklabel_format(axis="y", style="sci", scilimits=(-3, 3))
    low = min([0]+[i[0] for i in intervals]); high = max([0]+[i[1] for i in intervals])
    spread = max(high-low, 1e-6)
    ax_pred.set_ylim(low-.25*spread, high+.35*spread)
    for pos, row, value in zip(px, prediction, values):
        label = ("0 · fallback" if row["selected_arm"] == "neural" else "numerical tie"
                 if row["primary"]["documents_numerically_tied"] == row["primary"]["documents"] else f"{value:+.3g}")
        ax_pred.annotate(label, (pos, value), xytext=(0, 15), textcoords="offset points", ha="center", color=ink, fontsize=11, weight="bold")
    fig.text(.065, .085, "Two-witness coverage is exact for retained construction distinctions. Heuristics can tie the optimum; exact selection certifies it.", fontsize=10, color=muted)
    fig.text(.065, .060, "Qwen full-pool timing is observation only; SmolLM2 full-pool timing includes package verification. Model tokenizers differ.", fontsize=10, color=muted)
    fig.text(.065, .035, "Prediction intervals: descriptive paired document bootstrap. CPU latency concerns audit checks, without measuring generation speed.", fontsize=10, color=muted)
    fig.text(.965, .035, "ALL OUTCOMES RETAINED", fontsize=10, color=mint, ha="right", family="DejaVu Sans Mono")
    fig.text(.065, .010, "INT8 is an explicitly post-calibration eager-only repair; the original SDPA clean calibration failed and remains retained.", fontsize=9.5, color=muted)
    destination = ROOT / "docs/assets/deployment-transfer.svg"
    fig.savefig(destination, facecolor=bg, metadata={"Date": None, "Creator": "Singularity; retained result JSON"})
    raw = destination.read_text()
    destination.write_text("\n".join(line.rstrip() for line in raw.splitlines())+"\n")
    fig.savefig(ROOT.parent / "deployment-transfer-preview.png", dpi=130, facecolor=bg)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--render", action="store_true", help="render scientific SVG after all model timing runs")
    parser.add_argument("--update-readme", action="store_true")
    args = parser.parse_args()
    summary = snapshot()
    write_json(RESULTS / "deployment_transfer_summary.json", summary)
    (ROOT / "applications/training_lab/DEPLOYMENT_RESULTS.md").write_text(report_text(summary))
    if args.render:
        render(summary)
    if args.update_readme:
        update_readme(summary)
    print(json.dumps({"release": summary["release"], "audits": len(summary["audits"]), "prediction_models": len(summary["predictions"]),
                      "evaluated_targets": summary["evaluated_targets"], "figure_rendered": args.render}))


if __name__ == "__main__":
    main()
