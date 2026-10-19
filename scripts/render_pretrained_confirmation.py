#!/usr/bin/env python3
"""Render the README figure directly from retained pretrained results."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "applications/training_lab/results"
MODELS = [("gpt2", "gpt2", "GPT-2\n124M"),
          ("smollm2-360m", "smollm2-360m", "SmolLM2\n362M"),
          ("smollm2-1.7b", "smollm2-1700m", "SmolLM2\n1.71B")]


def main():
    pruned = json.loads((BASE / "pretrained_pruned_greedy.json").read_text())["models"]
    audits, gains, labels = [], [], []
    for key, prediction_key, label in MODELS:
        audit = json.loads((BASE / "pretrained_audit" / key / "results.json").read_text())
        prediction = json.loads((BASE / "pretrained_prediction/models" / prediction_key / "results.json").read_text())
        arms = prediction["domains"]["all_domains"]["arms"]
        gains.append(100 * (1 - arms["online_blend"]["nll_nats_per_token"] / arms["neural"]["nll_nats_per_token"]))
        audits.append(audit)
        labels.append(label)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                         "svg.fonttype": "none", "svg.hashsalt": "singularity-pretrained-v1"})
    fig, axes = plt.subplots(1, 2, figsize=(13.8, 6.9), gridspec_kw={"width_ratios": [1.08, 1]})
    fig.patch.set_facecolor("#081424")
    fig.subplots_adjust(left=.07, right=.97, bottom=.24, top=.74, wspace=.26)
    for ax in axes:
        ax.set_facecolor("#081424")
        ax.tick_params(colors="#c9d6e5")
        ax.yaxis.label.set_color("#c9d6e5")
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.grid(axis="y", alpha=.14, color="#c9d6e5")
        ax.set_axisbelow(True)
    x, width = np.arange(3), .25
    for shift, key, color, text in [(-width, "greedy", "#647a96", "Greedy"),
                                    (0, "pruned", "#f3ad76", "Pruned"),
                                    (width, "exact", "#59e2b5", "Exact")]:
        values = ([pruned[entry[0]]["optimally_pruned_greedy_cost"] for entry in MODELS] if key == "pruned"
                  else [r["selection"][key]["cost"] for r in audits])
        bars = axes[0].bar(x + shift, values, width, color=color, label=text)
        axes[0].bar_label(bars, padding=6, color="#e9f3ff", fontsize=11)
    axes[0].set_xticks(x, labels)
    axes[0].set_ylim(0, max(r["selection"]["greedy"]["cost"] for r in audits)*1.26)
    axes[0].set_ylabel("Forwarded input tokens · lower is better")
    axes[0].set_title("Cheaper checks, same construction coverage", color="white", fontsize=13, pad=19)
    legend = axes[0].legend(frameon=False, loc="upper left", ncol=3, fontsize=10)
    for text in legend.get_texts():
        text.set_color("#e9f3ff")
    bars = axes[1].bar(x, gains, width=.58, color=["#59e2b5" if v > 0 else "#f3ad76" for v in gains])
    for bar, value in zip(bars, gains):
        axes[1].annotate(f"{value:+.2f}%", (bar.get_x()+bar.get_width()/2, value),
                         xytext=(0, 7 if value >= 0 else -18), textcoords="offset points",
                         ha="center", color="#e9f3ff", fontsize=12, weight="bold")
    axes[1].axhline(0, color="#c9d6e5", lw=.8)
    axes[1].set_xticks(x, labels)
    axes[1].set_ylim(min(-2, min(gains)-1.5), max(gains)+3)
    axes[1].set_ylabel("Log-loss reduction vs same model (%)")
    axes[1].set_title("Prediction gains depend on the model", color="white", fontsize=13, pad=19)
    fig.text(.07, .92, "SINGULARITY  /  PRETRAINED CONFIRMATION", color="#75b9ff", fontsize=12, weight="bold")
    fig.text(.07, .845, "From tiny byte models to 1.7 billion parameters.", color="white", fontsize=23, weight="bold")
    fig.text(.07, .115, "Audits: same two-witness requirement; pruned = cheapest feasible subset of the original greedy panel.",
             color="#c9d6e5", fontsize=10)
    fig.text(.07, .079, "Prediction: primary causal blend; 24 fixed documents/model, 512 targets/document. No neural weight updates.",
             color="#c9d6e5", fontsize=10)
    fig.text(.07, .043, "CPU measurements. Model-specific tokenizers. Complete outcomes and limits are retained in the repository.",
             color="#8ea3bd", fontsize=9)
    destination = ROOT / "docs/assets/pretrained-confirmation.svg"
    fig.savefig(destination, facecolor=fig.get_facecolor(), metadata={"Date": None})
    destination.write_text("\n".join(line.rstrip() for line in destination.read_text().splitlines()) + "\n")
    fig.savefig(ROOT / "tmp/pretrained-confirmation.png", dpi=130, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(destination)


if __name__ == "__main__":
    (ROOT / "tmp").mkdir(exist_ok=True)
    main()
