"""One command from source data to machine-readable results, scouting cards, and a report.

    python -m perfectjet.applications.nfl_scouting --synthetic --seed 1 --out results/nfl-synthetic
    python -m perfectjet.applications.nfl_scouting --data DIR [--mapping mapping.json] --out results/nfl

Every run records source hashes, code revision, configuration hash, folds, and the
model-selection rule. Synthetic runs are labelled as such in every output.
"""
import argparse
import csv
import hashlib
import json
import subprocess
from pathlib import Path
from . import EXTRACTION_VERSION
from .events import extract_all, review_sample
from .readouts import DemandFrame, PooledModel, group, split_half
from .validate import (run_validation, fixed_prediction_interval, full_refit_interval, diagnostics, decision_eval,
                       LAMBDAS)
from .outcomes import leakage_check
from .schema import load_directory, audit_joins, DEFAULT_MAPPING, admissible_events
from .validate import decision_date
from .synthetic import generate
from .linalg import mean, quantile

CANDIDATE_CONDITIONS = [(s, a) for s in (4.0, 5.0, 6.0, 7.0) for a in (45.0, 90.0, 135.0, 170.0)]

HISTORICAL = [
    {"claim": "angular-progress alignment reduced measurement sensitivity by about 34.1%", "status": "historical_report",
     "meaning": "measurement improvement only; not a scouting advantage"},
    {"claim": "about 93.2% of player/drill panels cannot identify all four response coefficients",
     "status": "historical_report", "meaning": "motivates supported readouts instead of full response surfaces"},
    {"claim": "get-off split-half stability about 0.77 versus pressure about 0.28", "status": "historical_report",
     "meaning": "get-off is the primary outcome; confirm what the supplied variable measures"},
    {"claim": "duration-model 2025 gain did not persist across earlier partitions", "status": "historical_report",
     "meaning": "2025 is development evidence, not a pristine holdout"},
    {"claim": "pooled turn-response get-off gain was inconsistent across partitions", "status": "historical_report",
     "meaning": "pooling is a controlled candidate here, not the expected breakthrough"},
    {"claim": "future-speed MSE reductions 33.36% / 26.59%", "status": "historical_report",
     "meaning": "short-horizon prediction; does not establish scouting success"},
]


def git_revision():
    """HEAD commit, suffixed with +dirty when the working tree differs from it."""
    here = Path(__file__).resolve().parent
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=here,
                              timeout=10).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True,
                               cwd=here, timeout=10).stdout.strip()
        return (head+("+dirty" if dirty else "")) or None
    except Exception:
        return None


def scouting_cards(ds, events, fold):
    """Cards for the test class of one fold: predictions, coverage, repeatability, sensitivity, reliance, next test."""
    feats = fold["featurizer"]
    eba = group(events)
    cards = []
    for i, a in enumerate(fold["test_ids"]):
        evs, _ = admissible_events(ds.athletes[a], eba.get(a, []), decision_date(ds.athletes[a]))
        sup = feats.frame.support(evs) if evs else {"identified": False, "distinct_demands": 0, "q_mass_observed": 0.0}
        pooled = feats.model.readout(evs) if feats.model else {"pooling_reliance": 1.0}
        nxt = feats.model.next_condition(evs, CANDIDATE_CONDITIONS) if evs and feats.model else None
        best_new = next((c for c in nxt or [] if not c["repeat_of_observed_demand"]), None)
        best_rep = next((c for c in nxt or [] if c["repeat_of_observed_demand"]), None)
        etas = [e.eta for e in evs]
        cards.append({
            "athlete": a, "position": ds.athletes[a].position, "class": ds.athletes[a].draft_year,
            "baseline_prediction": fold["baseline"]["pred"][i], "movement_prediction": fold["movement"]["pred"][i],
            "change": fold["movement"]["pred"][i]-fold["baseline"]["pred"][i],
            "events": len(evs), "distinct_demands": sup["distinct_demands"],
            "readout_identified_by_own_attempts": sup["identified"],
            "demand_mass_observed": sup["q_mass_observed"],
            "attempt_spread": (max(etas)-min(etas)) if len(etas) > 1 else None,
            "measurement_sensitivity": mean(e.sensitivity for e in evs) if evs else None,
            "pooling_reliance": pooled["pooling_reliance"],
            "best_new_condition": best_new, "best_repeat": best_rep})
    return cards


def card_markdown(c):
    def f(x, d=3):
        return "n/a" if x is None else (f"{x:.{d}f}" if isinstance(x, float) else str(x))
    basis = ("own attempts identify the readout" if c["readout_identified_by_own_attempts"]
             else "readout relies on pooled assumptions")
    nxt = c["best_new_condition"]
    lines = [f"### {c['athlete']} ({c['position']}, class {c['class']})",
             f"- Baseline prediction {f(c['baseline_prediction'])}; movement-adjusted {f(c['movement_prediction'])} "
             f"(change {f(c['change'])}).",
             f"- Evidence: {c['events']} turn events at {c['distinct_demands']} distinct demands covering "
             f"{f(100*c['demand_mass_observed'], 0)}% of the reference demand mass; {basis}.",
             f"- Measurement sensitivity across extraction branches {f(c['measurement_sensitivity'])}; "
             f"pooling reliance {f(c['pooling_reliance'], 2)} (share of prior variance retained).",
             f"- Most informative next condition: speed {f(nxt['speed'], 1)} yd/s, angle {f(nxt['angle'], 0)} deg "
             f"(variance reduction {nxt['reduction']:.2e}, {'new direction' if nxt['new_design_direction'] else 'within current design span'})."
             if nxt else "- No candidate condition evaluated."]
    return "\n".join(lines)


def run(ds, out_dir, config):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    events = extract_all(ds.attempts)
    eba = group(events)
    val = run_validation(ds, events, config["readout"])
    folds = val["folds"]
    frame_all = DemandFrame(events)
    model_all = PooledModel(frame_all, eba)
    support = [frame_all.support(v) for v in eba.values()]
    years = sorted({a.draft_year for a in ds.athletes.values()})
    leak = leakage_check(ds.plays, [a for a, v in ds.athletes.items() if v.draft_year < years[-1]],
                         [a for a, v in ds.athletes.items() if v.draft_year == years[-1]]) if len(years) > 1 else None
    refit = (full_refit_interval(ds, extract_all, b=config["bootstrap"], seed=config["seed"], readout=config["readout"])
             if config["bootstrap"] else None)
    results = {
        "synthetic": ds.synthetic,
        "warning": ("SYNTHETIC DATA: tests the pipeline only; not evidence about football." if ds.synthetic else
                    "Real data: development evidence unless the evaluated class was untouched before this run."),
        "question": "Does a demand-adjusted Combine recovery readout predict NFL get-off beyond pre-draft information?",
        "provenance": {"sources": ds.manifest if not ds.synthetic else {k: v for k, v in ds.manifest["synthetic"].items()
                                                                         if k != "latent"},
                       "code_revision": git_revision(), "extraction_version": EXTRACTION_VERSION,
                       "config": config, "config_sha256": hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest(),
                       "target_rules": {"evaluation_horizon": ds.outcome_definition.get("evaluation_horizon", "rookie_season"),
                                        "chronological_training": ds.outcome_definition.get("chronological_training", True)},
                       "outcome_definition_sha256": hashlib.sha256(json.dumps(ds.outcome_definition, sort_keys=True).encode()).hexdigest(),
                       "model_selection": f"ridge penalty from {LAMBDAS} by 5-fold athlete-grouped CV inside each training set; same grid for both models",
                       "folds": [{"test_class": f["year"], "train_athletes": f["train"], "test_athletes": f["test"],
                                  "training_seasons_before": f["training_seasons_before"],
                                  "evaluation_horizon": f["evaluation_horizon"], "test_season": f["test_season"]}
                                 for f in folds]},
        "outcome_definition": ds.outcome_definition,
        "audit": audit_joins(ds),
        "measurement": {"events": len(events), "attempts": len(ds.attempts),
                        "median_branch_sensitivity": quantile([e.sensitivity for e in events], 0.5) if events else None,
                        "repeatability_intercept_readout": split_half(eba, lambda e: model_all.intercept_readout(e)["theta"]),
                        "repeatability_raw_mean_eta": split_half(eba, lambda e: mean(x.eta for x in e))},
        "identifiability": {"athletes": len(support),
                            "readout_identified_share": mean(s["identified"] for s in support) if support else None,
                            "median_distinct_demands": quantile([s["distinct_demands"] for s in support], 0.5) if support else None,
                            "median_demand_mass_observed": quantile([s["q_mass_observed"] for s in support], 0.5) if support else None},
        "validation": {"G_pooled": val["G_pooled"],
                       "by_fold": [{"test_class": f["year"], "G": f["G"], "mse_baseline": f["baseline"]["mse"],
                                    "mse_movement": f["movement"]["mse"], "lambda_baseline": f["baseline"]["lambda"],
                                    "lambda_movement": f["movement"]["lambda"]} for f in folds],
                       "fixed_prediction_interval_90": fixed_prediction_interval(folds) if folds else None,
                       "full_refit_interval_90": refit,
                       "diagnostics": diagnostics(folds) if folds else None},
        "decisions": decision_eval(folds, lower_is_better=ds.outcome_definition.get("lower_is_better", True)) if folds else None,
        "leakage_check": leak,
        "historical_reports": HISTORICAL,
    }
    cards = scouting_cards(ds, events, folds[-1]) if folds else []
    (out/"results.json").write_text(json.dumps(results, indent=2, default=str)+"\n")
    (out/"cards.json").write_text(json.dumps(cards, indent=2, default=str)+"\n")
    sheet = review_sample(events, seed=config["seed"])
    if sheet:
        with open(out/"review_sheet.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(sheet[0]))
            w.writeheader()
            w.writerows(sheet)
    (out/"report.md").write_text(report_markdown(results, cards))
    from .figures import write_figures
    write_figures(out, events, folds, frame_all, ds.attempts)
    return results


def report_markdown(r, cards):
    v = r["validation"]

    def f(x, d=3):
        return "n/a" if x is None else f"{x:.{d}f}"
    lines = ["# Combine recovery readout: validation report", "", f"**{r['warning']}**", "",
             f"Question: {r['question']}", "",
             "## Measurement", "",
             f"{r['measurement']['events']} turn events from {r['measurement']['attempts']} attempts. "
             f"Median extraction-branch spread {f(r['measurement']['median_branch_sensitivity'])} (a sensitivity range, not a calibrated interval). "
             f"Split-half reliability of the demand-adjusted readout: {f(r['measurement']['repeatability_intercept_readout']['spearman_brown'])} (Spearman-Brown).",
             "", "## Identifiability", "",
             f"Own attempts identify the demand-supported readout for {f(100*(r['identifiability']['readout_identified_share'] or 0), 1)}% of athletes "
             f"(exact test on the design rounded to the demand resolution). Median distinct demands {r['identifiability']['median_distinct_demands']}; "
             f"median share of the reference demand mass observed {f(r['identifiability']['median_demand_mass_observed'], 2)}.",
             "", "## Prediction", "",
             f"Pooled G = 1 - MSE_movement/MSE_baseline = **{f(v['G_pooled'])}**.", "",
             "| Test class | G | MSE baseline | MSE movement |", "|---|---|---|---|"]
    for row in v["by_fold"]:
        lines.append(f"| {row['test_class']} | {f(row['G'])} | {f(row['mse_baseline'], 5)} | {f(row['mse_movement'], 5)} |")
    fp, fr = v["fixed_prediction_interval_90"], v["full_refit_interval_90"]
    lines += ["", f"90% interval with predictions fixed: [{f(fp['lo'])}, {f(fp['hi'])}]." if fp else "",
              f"90% interval refitting the full pipeline ({fr['draws']} athlete resamples): [{f(fr['lo'])}, {f(fr['hi'])}]." if fr else
              "Full-refit interval not computed (bootstrap=0).",
              "Temporal folds share training classes, so they are robustness checks, not independent replications.", ""]
    d = v["diagnostics"]
    if d:
        lines += ["## Diagnostics", "",
                  "G by position: "+", ".join(f"{k} {f(x['G'])} (n={x['n']})" for k, x in d["G_by_position"].items())+".",
                  f"G excluding athletes with fewer than {d['low_play_threshold']} plays: {f(d['G_excluding_low_play_athletes'])}.",
                  "Largest single-athlete influence on G: "+", ".join(f"{x['athlete']} {f(x['delta_G'])}" for x in d["largest_single_athlete_influence"][:3])+".", ""]
    dec = r["decisions"]
    if dec:
        lines += ["## Decisions", "", f"Rule: {dec['rule']}.",
                  f"Shortlist hits: baseline {dec['hits_baseline']}, movement {dec['hits_movement']}.", ""]
    lines += ["## Leakage", "", json.dumps(r["leakage_check"]), "", "## Historical reports (not reproduced here)", ""]
    lines += [f"- {h['claim']} — {h['meaning']}." for h in r["historical_reports"]]
    lines += ["", "## Example scouting cards", ""]+[card_markdown(c)+"\n" for c in cards[:6]]
    return "\n".join(lines)+"\n"


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--synthetic", action="store_true")
    src.add_argument("--data", type=Path)
    p.add_argument("--mapping", type=Path)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--athletes", type=int, default=120)
    p.add_argument("--signal", type=float, default=0.5)
    p.add_argument("--bootstrap", type=int, default=20)
    p.add_argument("--readout", choices=["intercept", "pooled"], default="intercept")
    a = p.parse_args(argv)
    config = {"seed": a.seed, "bootstrap": a.bootstrap, "readout": a.readout}
    if a.synthetic:
        config.update({"synthetic_athletes": a.athletes, "synthetic_signal": a.signal})
        ds = generate(n_athletes=a.athletes, signal=a.signal, seed=a.seed)
    else:
        mapping = json.loads(a.mapping.read_text()) if a.mapping else DEFAULT_MAPPING
        ds = load_directory(a.data, mapping)
    res = run(ds, a.out, config)
    print(json.dumps({"G_pooled": res["validation"]["G_pooled"], "out": str(a.out), "synthetic": ds.synthetic}))


if __name__ == "__main__":
    main()
