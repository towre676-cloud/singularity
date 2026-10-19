"""Cross-fitted Combine -> NFL movement -> football bridges.

NFL tracking trains a finite-horizon numerical representation and defines
movement targets. It never enters an evaluated prospect's predictors. The
outcome decoder learns from out-of-player first-stage movement predictions,
matching deployment rather than receiving privileged true movement features.
The supplied context-adjusted get-off target remains the primary outcome.

Cross-domain continuation is a testable representation hypothesis, not a
physical theorem. All forecasts exposed to downstream fits have physical
velocity coordinates; independently fitted SVD state coordinates are not mixed.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, replace
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import burst_transfer as BT
from .burst import FORTY
from .movement_targets import load_movement_targets
from .official import load_official_directory
from .predictive_state import MovementSequence, discover_predictive_state
from .schema import Dataset, Play, available


BRIDGE_CHANNELS = ("forward_displacement_05", "motion_to_los")


@dataclass(frozen=True)
class BridgeConfig:
    source_drills: tuple = (FORTY,)
    state_history_steps: tuple = (1, 3, 5)
    state_ranks: tuple = (1, 2)
    state_penalties: tuple = (0.01, 0.1)
    state_horizon_steps: int = 3
    state_inner_folds: int = 3
    maximum_nfl_sequences_per_athlete: int = 6
    minimum_training_athletes: int = 6
    minimum_movement_plays: int = 5
    minimum_movement_athletes: int = 4
    stack_folds: int = 3
    movement_penalty: float = 100.0
    decoder_penalties: tuple = (10.0, 100.0, 1000.0)
    outer_inner_folds: int = 3

    def __post_init__(self):
        if (self.stack_folds < 2 or self.state_inner_folds < 2 or self.outer_inner_folds < 2
                or self.minimum_training_athletes < 4 or self.minimum_movement_athletes < 2
                or self.maximum_nfl_sequences_per_athlete < 1 or self.minimum_movement_plays < 1):
            raise ValueError("positive counts and at least two original-player folds required")
        if self.movement_penalty <= 0 or any(a <= 0 for a in self.decoder_penalties):
            raise ValueError("positive regularization penalties required")


def _records(value):
    return list(getattr(value, "records", value))


def _original(ds, aid):
    return ds.athletes[aid].bootstrap_group or aid


def _assert_split(ds, train_ids, test_ids, cutoff):
    if set(train_ids) & set(test_ids):
        raise ValueError("athlete leakage")
    if {_original(ds, a) for a in train_ids} & {_original(ds, a) for a in test_ids}:
        raise ValueError("original-athlete leakage")
    if any(ds.athletes[a].draft_year >= cutoff for a in train_ids):
        raise ValueError("training draft year reaches or exceeds temporal cutoff")


def source_prefix(attempt, threshold=0.5, sustained=3):
    """First observed launch; return six causal velocities over a half second.

    Inputs use positions through the declared endpoint only. No symmetric
    smoothing or source outputs after that endpoint are consulted. The start
    needs an observed below-threshold history and sustained intervals; no known
    start cue is assumed. The forward axis is the first qualifying interval.
    Irregular observed-prefix sampling is rejected rather than extrapolated.
    """
    frames = attempt.frames
    if len(frames) < 2:
        return None
    velocities = []
    onset = None
    for i in range(1, len(frames)):
        a, b = frames[i-1], frames[i]
        values = np.asarray([a.t, a.x, a.y, b.t, b.x, b.y], dtype=float)
        if not np.isfinite(values).all() or abs((b.t-a.t)-0.1) > 1e-5:
            return None
        velocities.append(np.asarray([(b.x-a.x)/(b.t-a.t), (b.y-a.y)/(b.t-a.t)]))
        if len(velocities) == 1 and np.linalg.norm(velocities[0]) >= threshold:
            return None
        if len(velocities) >= sustained+1 and all(np.linalg.norm(v) >= threshold for v in velocities[-sustained:]):
            onset = i-sustained
            break
    if onset is None or onset < 1 or onset+5 >= len(frames):
        return None
    direction = velocities[onset]/np.linalg.norm(velocities[onset])
    perpendicular = np.asarray([-direction[1], direction[0]])
    rows = []
    for i in range(onset, onset+6):
        a, b = frames[i-1], frames[i]
        values = np.asarray([a.t, a.x, a.y, b.t, b.x, b.y], dtype=float)
        if not np.isfinite(values).all() or abs((b.t-a.t)-0.1) > 1e-5:
            return None
        velocity = np.asarray([(b.x-a.x)/(b.t-a.t), (b.y-a.y)/(b.t-a.t)])
        rows.append([float(velocity@direction), float(velocity@perpendicular)])
    delta = np.asarray([frames[onset+5].x-frames[onset].x,
                        frames[onset+5].y-frames[onset].y])
    end_speed = float(np.linalg.norm(rows[-1]))
    return {
        "athlete_id": attempt.athlete_id, "attempt_id": attempt.attempt_id,
        "history": np.asarray(rows), "onset_time": float(frames[onset].t),
        "endpoint_time": float(frames[onset+5].t),
        "displacement_05": float(delta@direction),
        "terminal_forward_speed": rows[-1][0],
        "endpoint_retention": rows[-1][0]/end_speed if end_speed > 1e-12 else 0.0,
    }


def _nfl_sequences(ds, records, ids, cutoff, cap):
    buckets = defaultdict(list)
    for record in records:
        if (record.athlete_id not in ids or not record.usable or record.season >= cutoff
                or record.season != ds.athletes[record.athlete_id].draft_year):
            continue
        frames = record.frames
        if len(frames) < 10:
            continue
        positions = np.asarray([[f.x, f.y] for f in frames], dtype=float)
        times = np.asarray([f.t for f in frames], dtype=float)
        dt = np.diff(times)
        if not np.isfinite(positions).all() or not np.isfinite(times).all() or np.any(abs(dt-0.1) > 1e-5):
            continue
        values = np.diff(positions, axis=0)/dt[:, None]
        buckets[record.athlete_id].append(MovementSequence(
            record.athlete_id, record.play_id, times[1:], values,
            original_athlete_id=_original(ds, record.athlete_id)))
    return [sequence for aid in sorted(buckets)
            for sequence in sorted(buckets[aid], key=lambda seq: seq.attempt_id)[:cap]]


def _movement_targets(ds, records, train_ids, test_ids, cutoff, seed, config):
    """Rebuild each physical movement context reference inside the current fit."""
    joint_records = [r for r in records if r.usable and all(
        c in r.channels and np.isfinite(r.channels[c]) for c in BRIDGE_CHANNELS)]
    channels = {}
    precision = {}
    for channel in BRIDGE_CHANNELS:
        plays = [Play(r.athlete_id, r.season, r.play_id, float(r.channels[channel]), dict(r.context))
                 for r in joint_records]
        local = Dataset(ds.athletes, [], plays, ds.manifest,
                        {"minimum_plays": config.minimum_movement_plays}, ds.synthetic)
        y, variance, _ = BT.targets(local, train_ids, test_ids, cutoff, seed)
        channels[channel] = y
        precision[channel] = variance
    ids = set.intersection(*(set(y) for y in channels.values()))
    return {aid: [channels[c][aid] for c in BRIDGE_CHANNELS] for aid in ids}, precision


def _source_features(ds, ids, model, include_ngs, config):
    buckets = defaultdict(list)
    for attempt in ds.attempts:
        if (attempt.athlete_id not in ids or attempt.drill not in config.source_drills
                or not available(attempt.recorded_on, f"{ds.athletes[attempt.athlete_id].draft_year}-04-20")):
            continue
        prefix = source_prefix(attempt)
        if prefix is not None:
            buckets[attempt.athlete_id].append(prefix)
    base = BT.predictor_frame(ds, ids, include_ngs)
    source_names = ["source__displacement_05", "source__terminal_forward_speed", "source__endpoint_retention"]
    source_names += [f"forecast__{channel}__step{step+1}"
                     for step in range(model.horizon_steps) for channel in ("forward_speed", "lateral_speed")]
    source = pd.DataFrame(np.nan, index=ids, columns=source_names)
    for aid in ids:
        prefixes = buckets.get(aid, [])
        feature_rows, distances, outside = [], [], []
        for prefix in prefixes:
            history = prefix["history"][-model.history_steps:]
            if len(history) != model.history_steps:
                continue
            feature_rows.append([prefix["displacement_05"], prefix["terminal_forward_speed"],
                                 prefix["endpoint_retention"], *model.forecast_features(history).tolist()])
            support = model.support(history)
            distances.append(support["mahalanobis_distance"])
            outside.append(support["outside_training_p95"])
        count = len(feature_rows)
        base.loc[aid, "source_prefix_count"] = float(count)
        base.loc[aid, "source_prefix_available"] = float(count > 0)
        base.loc[aid, "source_prefix_repeats"] = float(max(0, count-1))
        base.loc[aid, "source_history_support_distance"] = float(np.median(distances)) if distances else np.nan
        base.loc[aid, "source_history_outside_training_support"] = float(np.mean(outside)) if outside else 1.0
        if feature_rows:
            source.loc[aid] = np.median(np.asarray(feature_rows), axis=0)
    return base, pd.concat([base, source], axis=1), source_names


def _fit_stage(ds, records, train_ids, test_ids, cutoff, include_ngs, seed, config):
    _assert_split(ds, train_ids, test_ids, cutoff)
    sequences = _nfl_sequences(ds, records, set(train_ids), cutoff,
                               config.maximum_nfl_sequences_per_athlete)
    independent = len({s.group for s in sequences})
    if independent < 2:
        raise ValueError("insufficient training NFL movement sequence athletes")
    state = discover_predictive_state(sequences,
        history_steps=config.state_history_steps, ranks=config.state_ranks,
        horizon_steps=config.state_horizon_steps, ridge_penalties=config.state_penalties,
        inner_folds=min(config.state_inner_folds, independent), seed=seed,
        sample_interval=0.1, channel_names=("forward_speed", "lateral_speed"),
        output_names=("forward_speed", "lateral_speed"))
    q, precision = _movement_targets(ds, records, train_ids, test_ids, cutoff, seed+41, config)
    tr = [a for a in train_ids if a in q]
    if len({_original(ds, a) for a in tr}) < config.minimum_movement_athletes:
        raise ValueError("insufficient context-adjusted movement target athletes")
    base_train, source_train, names = _source_features(ds, tr, state.model, include_ngs, config)
    base_test, source_test, _ = _source_features(ds, test_ids, state.model, include_ngs, config)
    target = np.asarray([q[a] for a in tr])
    source_model = BT._regressor(source_train, config.movement_penalty).fit(source_train, target)
    conventional_model = BT._regressor(base_train, config.movement_penalty).fit(base_train, target)
    return {
        "q": q, "precision": precision, "base": base_test, "source": source_test,
        "forecast": source_model.predict(source_test),
        "conventional_forecast": conventional_model.predict(base_test),
        "source_model": source_model, "state": state, "source_names": names,
        "source_training_reference": source_train.iloc[:1].copy(),
        "audit": {"training_ids": sorted(train_ids), "training_group_ids": sorted({_original(ds, a) for a in train_ids}),
                  "evaluated_ids": sorted(test_ids),
                  "state_training_ids": list(state.model.training_athlete_ids),
                  "movement_training_ids": tr, "nfl_sequences": len(sequences),
                  "state_history_steps": state.model.history_steps,
                  "state_count": state.model.state_count, "state_cv_mse": state.selected_cv_mse,
                  "instantaneous_cv_mse": state.instantaneous_cv_mse,
                  "state_sample_interval_seconds": state.model.sample_interval,
                  "state_horizon_seconds": state.model.horizon_steps*state.model.sample_interval,
                  "state_output_units": "forward/lateral velocity in yards/second",
                  "state_training_maximum_season": max(ds.athletes[a].draft_year for a in state.model.training_athlete_ids),
                  "state_training_support_p95": state.model.training_support_p95,
                  "source_prefix_horizon_seconds": 0.5,
                  "maximum_sequences_per_athlete": config.maximum_nfl_sequences_per_athlete,
                  "state_selection_uses_football_outcomes": False},
    }


def _decoder_frame(base, movement):
    frame = base.copy()
    for j, channel in enumerate(BRIDGE_CHANNELS):
        frame["q__"+channel] = np.asarray(movement)[:, j]
    return frame


def _probe(model, frame, columns):
    """Affine fitted slope by a float unit probe, conditional on missingness."""
    origin = frame.iloc[:1].copy()
    value = np.asarray(model.predict(origin)).reshape(-1)
    slopes = []
    for column in columns:
        changed = origin.copy()
        if pd.isna(changed.iloc[0][column]):
            changed.loc[changed.index[0], column] = 0.0
            reference = np.asarray(model.predict(changed)).reshape(-1)
        else:
            reference = value
        changed.loc[changed.index[0], column] += 1.0
        slopes.append((np.asarray(model.predict(changed)).reshape(-1)-reference).tolist())
    return np.asarray(slopes).T


@dataclass(frozen=True)
class _FrozenFrame:
    """Scalar-only frame snapshot; each decoder receives fresh mutable storage."""
    columns: tuple
    index: tuple
    rows: tuple
    dtypes: tuple

    @classmethod
    def capture(cls, frame):
        return cls(tuple(frame.columns), tuple(frame.index),
                   tuple(tuple(row) for row in frame.itertuples(index=False, name=None)),
                   tuple(str(dtype) for dtype in frame.dtypes))

    def frame(self):
        return pd.DataFrame(self.rows, columns=self.columns, index=self.index).astype(
            dict(zip(self.columns, self.dtypes)))


@dataclass(frozen=True)
class _SplitPreparation:
    """Owned immutable result of one alpha-independent original-player split.

    This value has no reference to the input dataset, trajectory records, fitted
    state model or a global cache. JSON snapshots isolate result dictionaries;
    tuples isolate forecasts and training labels. A new preparation is always
    constructed for a new fit, even when the athlete IDs have appeared before.
    """
    base_train: _FrozenFrame
    base_test: _FrozenFrame
    movement_oof: tuple
    conventional_oof: tuple
    forecast: tuple
    conventional_forecast: tuple
    y_train: tuple
    source_jacobian: tuple
    common_json: str
    receipt_json: str
    seed: int
    cutoff: int


def _matrix_snapshot(values):
    return tuple(tuple(float(value) for value in row) for row in values)


def _prepare_split(ds, movement_targets, train_ids, test_ids, cutoff,
                   include_ngs=True, seed=81114, config=None):
    """Rebuild all context, representation and stacking within this split."""
    config = config or BridgeConfig()
    records = _records(movement_targets)
    train_ids, test_ids = sorted(train_ids), sorted(test_ids)
    _assert_split(ds, train_ids, test_ids, cutoff)
    y, nu, counts = BT.targets(ds, train_ids, test_ids, cutoff, seed)
    tr, te = [a for a in train_ids if a in y], [a for a in test_ids if a in y]
    independent = len({_original(ds, a) for a in tr})
    if independent < config.minimum_training_athletes or not te:
        raise ValueError("insufficient primary target athletes in bridge split")
    folds = min(config.stack_folds, independent)
    assignment = BT._groups(ds, tr, folds, seed+101)
    oof, conventional_oof, oof_base, audits = {}, {}, {}, []
    for fold in range(folds):
        a = [aid for aid in tr if assignment[aid] != fold]
        b = [aid for aid in tr if assignment[aid] == fold]
        stage = _fit_stage(ds, records, a, b, cutoff, include_ngs, seed+201+fold, config)
        for i, aid in enumerate(b):
            oof[aid] = stage["forecast"][i]
            conventional_oof[aid] = stage["conventional_forecast"][i]
            oof_base[aid] = stage["base"].loc[aid].to_dict()
        audits.append(stage["audit"])
    full = _fit_stage(ds, records, tr, te, cutoff, include_ngs, seed+401, config)
    base_train = pd.DataFrame([oof_base[a] for a in tr], index=tr)
    q_oof = np.asarray([oof[a] for a in tr])
    conventional_q_oof = np.asarray([conventional_oof[a] for a in tr])
    yy = np.asarray([y[a] for a in tr])
    source_jacobian = _probe(full["source_model"], full["source_training_reference"], full["source_names"])
    q_truth = [full["q"].get(a) for a in te]
    available_q = [a for a in tr if a in full["q"]]
    transfer_residuals = np.asarray([np.asarray(full["q"][a])-oof[a] for a in available_q])
    transfer_covariance = np.cov(transfer_residuals, rowvar=False, ddof=1).tolist() if len(available_q)>1 else None
    receipt = {
        "training_athlete_ids": sorted({_original(ds, a) for a in tr}),
        "held_out_athlete_ids": sorted({_original(ds, a) for a in te}),
        "outcome_cutoff": cutoff-1,
        "latest_training_outcome": max(p.season for p in ds.plays
            if p.athlete_id in set(tr) and p.season < cutoff and p.season == ds.athletes[p.athlete_id].draft_year),
        "loading_source": "conditional fitted source-to-movement-to-getoff affine Jacobian; physical feature coordinates",
    }
    common = {
        "ids": te, "y": [y[a] for a in te],
        "counts": [counts[a] for a in te], "year": cutoff,
        "training_target_quartile": float(np.quantile(yy, 0.25)),
        "movement_channels": list(BRIDGE_CHANNELS), "movement_predictions": full["forecast"].tolist(),
        "movement_truth": q_truth, "movement_transfer_covariance": transfer_covariance,
        "movement_transfer_covariance_scope": "Empirical training-player OOF transfer-residual covariance; not a calibrated source prior or total uncertainty; context-fit and loading uncertainty excluded",
        "frozen_jacobian": {"source_features": full["source_names"],
                             "source_to_movement": source_jacobian.tolist(),
                             "training_cutoff_exclusive": cutoff,
                             "probe_reference": "training rows only; evaluated-player feature values do not set the frozen loading",
                             "scope": "affine fitted sensitivity in declared feature units with fixed preprocessing/missingness; not causal or future uncertainty"},
        "stacking_audit": audits,
        "full_stage_audit": full["audit"], "source_coverage": full["base"][[c for c in full["base"] if c.startswith("source_")]].to_dict("index"),
        "shared_baseline_columns": list(base_train), "synthetic": ds.synthetic,
        "outcome_variance": [nu[a] for a in te],
        "deployment": "Combine-only source and conventional measurements; evaluated-player NFL frames/context/labels excluded from predictors",
    }
    return _SplitPreparation(
        _FrozenFrame.capture(base_train), _FrozenFrame.capture(full["base"]),
        _matrix_snapshot(q_oof), _matrix_snapshot(conventional_q_oof),
        _matrix_snapshot(full["forecast"]), _matrix_snapshot(full["conventional_forecast"]),
        tuple(float(value) for value in yy), _matrix_snapshot(source_jacobian),
        json.dumps(common), json.dumps(receipt), seed, cutoff)


def _fit_decoder(prepared, alpha):
    """Fit an independent decoder from this split's fixed training preparation."""
    result = json.loads(prepared.common_json)
    base_train, base_test = prepared.base_train.frame(), prepared.base_test.frame()
    yy = np.asarray(prepared.y_train)
    baseline = BT._regressor(base_train, alpha).fit(base_train, yy)
    decoder_train = _decoder_frame(base_train, prepared.movement_oof)
    decoder = BT._regressor(decoder_train, alpha).fit(decoder_train, yy)
    conventional_train = _decoder_frame(base_train, prepared.conventional_oof)
    conventional_decoder = BT._regressor(conventional_train, alpha).fit(conventional_train, yy)
    pb = baseline.predict(base_test)
    pm = decoder.predict(_decoder_frame(base_test, prepared.forecast))
    pc = conventional_decoder.predict(_decoder_frame(base_test, prepared.conventional_forecast))
    loading = _probe(decoder, decoder_train, ["q__"+c for c in BRIDGE_CHANNELS])[0]
    end_to_end = loading @ np.asarray(prepared.source_jacobian)
    decompositions = []
    for i, truth in enumerate(result["movement_truth"]):
        if truth is None:
            decompositions.append(None)
            continue
        oracle_frame = _decoder_frame(base_test.iloc[i:i+1], np.asarray([truth]))
        oracle = float(decoder.predict(oracle_frame)[0])
        decoder_residual = oracle-result["y"][i]
        transfer_error = float(pm[i])-oracle
        total = float(pm[i])-result["y"][i]
        decompositions.append({"decoder_residual": decoder_residual,
                               "transferred_movement_error": transfer_error, "total_error": total,
                               "identity_error": abs(total-decoder_residual-transfer_error),
                               "oracle_prediction": oracle,
                               "scope": "held-out diagnostic using true movement; never a deployable forecast"})
    receipt = json.loads(prepared.receipt_json)
    receipt["model_id"] = f"nfl-math-bridge/1:seed{prepared.seed}:alpha{alpha}:before{prepared.cutoff}"
    result.update(baseline=pb.tolist(), movement=pm.tolist(), bridge=pm.tolist(),
                  conventional_bridge=pc.tolist(), alpha=alpha, loading=loading.tolist(),
                  error_decomposition=decompositions)
    result["frozen_jacobian"].update(movement_to_outcome=loading.tolist(),
        source_to_outcome=end_to_end.tolist(), training_receipt=receipt)
    return result


def fit_split(ds, movement_targets, train_ids, test_ids, cutoff, alpha=100.0,
              include_ngs=True, seed=81114, config=None):
    """Fit a complete stacked bridge; permit labeled synthetic fixtures only here.

    Decoder inputs for every training athlete are first-stage predictions from
    other original athletes, including rebuilt NFL state and movement context.
    Test NFL targets affect evaluation/diagnostics only. ``experiment`` refuses
    synthetic evidence, while this lower-level function supports unit fixtures.
    No preparation survives this call or is shared with a different split.
    """
    prepared = _prepare_split(ds, movement_targets, train_ids, test_ids, cutoff,
                               include_ngs, seed, config)
    return _fit_decoder(prepared, alpha)


def _nested_fold(ds, records, train_ids, test_ids, cutoff, include_ngs, seed, config):
    groups = len({_original(ds, a) for a in train_ids})
    assignment = BT._groups(ds, train_ids, min(config.outer_inner_folds, groups), seed+501)
    families = ("baseline", "movement", "conventional_bridge")
    scores = {family: [] for family in families}
    fits_by_alpha = {alpha: [] for alpha in config.decoder_penalties}
    for fold in sorted(set(assignment.values())):
        a = [aid for aid in train_ids if assignment[aid] != fold]
        b = [aid for aid in train_ids if assignment[aid] == fold]
        prepared = _prepare_split(ds, records, a, b, cutoff, include_ngs,
                                   seed+601+fold, config)
        for alpha in config.decoder_penalties:
            fits_by_alpha[alpha].append(_fit_decoder(prepared, alpha))
    for alpha in config.decoder_penalties:
        fits = fits_by_alpha[alpha]
        for family in families:
            scores[family].append(BT._score(fits, family))
    chosen = {family: config.decoder_penalties[int(np.argmin(score))] for family, score in scores.items()}
    prepared = _prepare_split(ds, records, train_ids, test_ids, cutoff, include_ngs,
                               seed+801, config)
    full = {alpha: _fit_decoder(prepared, alpha) for alpha in set(chosen.values())}
    result = full[chosen["movement"]]
    result["baseline"] = full[chosen["baseline"]]["baseline"]
    result["conventional_bridge"] = full[chosen["conventional_bridge"]]["conventional_bridge"]
    benchmark = min(("baseline", "conventional_bridge"), key=lambda family: min(scores[family]))
    result["strong_baseline"] = result[benchmark]
    result["strong_baseline_family"] = benchmark
    result["strong_baseline_selection_scope"] = "selected only by inner training-player validation"
    result["chosen_penalties"] = chosen
    result["inner_scores"] = scores
    return result


def experiment(ds, movement_targets, include_ngs=True, seed=81114, config=None):
    """Temporal nested development experiment; never accept synthetic evidence."""
    if ds.synthetic:
        raise ValueError("bridge experiment requires official real inputs; synthetic fixtures cannot establish scouting advantage")
    config = config or BridgeConfig()
    records = _records(movement_targets)
    years = sorted({a.draft_year for a in ds.athletes.values()})
    folds = []
    for year in years[1:]:
        tr = sorted(a for a, athlete in ds.athletes.items() if athlete.draft_year < year)
        te = sorted(a for a, athlete in ds.athletes.items() if athlete.draft_year == year)
        print(f"Math bridges: rebuilding temporal class {year}", flush=True)
        folds.append(_nested_fold(ds, records, tr, te, year, include_ngs, seed, config))
    if not folds:
        raise ValueError("at least two prospect classes required")
    protocol = {"schema": "perfectjet/nfl-math-bridge/1", "config": asdict(config),
                "primary": "context-adjusted supplied rookie snap-to-LOS get-off",
                "movement": list(BRIDGE_CHANNELS), "2025": "previously inspected development cohort",
                "state": "NFL-trained finite-horizon causal velocity continuation; Combine-domain transfer is an empirical hypothesis",
                "decoder_training": "out-of-original-player first-stage physical movement predictions",
                "baseline": "all fifteen available conventional measurements, raw drill counts, identical source coverage/support flags"}
    conventional_folds = [{**fold, "movement": fold["conventional_bridge"]} for fold in folds]
    strongest_folds = [{**fold, "baseline": fold["strong_baseline"]} for fold in folds]
    against_conventional_bridge = [{**fold, "baseline": fold["conventional_bridge"]} for fold in folds]
    return {"protocol": protocol,
            "protocol_sha256": hashlib.sha256(json.dumps(protocol, sort_keys=True).encode()).hexdigest(),
            "synthetic": False, "status": "real_data_development_experiment", "include_ngs": include_ngs,
            "summary": BT.paired_summary(strongest_folds, seed=seed),
            "movement_vs_direct_baseline_summary": BT.paired_summary(folds, seed=seed),
            "movement_vs_conventional_bridge_summary": BT.paired_summary(against_conventional_bridge, seed=seed),
            "conventional_bridge_summary": BT.paired_summary(conventional_folds, seed=seed),
            "folds": folds, "sources": ds.manifest,
            "movement_audit": getattr(movement_targets, "audit", None),
            "conclusion": "Scouting evidence must come from held-out primary outcomes; movement continuation and algebraic identities alone do not establish advantage."}


def full_refit_sensitivity(ds, movement_targets, draws=64, include_ngs=True,
                           seed=81114, config=None):
    """Class-stratified original-athlete bootstrap of the full nested pipeline.

    Raw source trajectories and target records are copied, not frozen fitted
    features. Repeated draws share their original-athlete fold group. Outcome
    construction, movement context, state discovery, preprocessing, first-stage
    stacking and decoder selection are rebuilt. No independence from the
    project's adaptive research history is claimed by these intervals.
    """
    if ds.synthetic:
        raise ValueError("full refits require official real inputs")
    if not isinstance(draws, int) or draws < 1:
        raise ValueError("positive integer refit draws required")
    config = config or BridgeConfig()
    records = _records(movement_targets)
    by_attempt, by_play, by_record = defaultdict(list), defaultdict(list), defaultdict(list)
    for attempt in ds.attempts:
        by_attempt[attempt.athlete_id].append(attempt)
    for play in ds.plays:
        by_play[play.athlete_id].append(play)
    for record in records:
        by_record[record.athlete_id].append(record)
    rng = np.random.default_rng(seed+1901)
    gains, failures = [], []
    classes = sorted({a.draft_year for a in ds.athletes.values()})
    for draw in range(draws):
        athletes, attempts, plays, sampled_records = {}, [], [], []
        for year in classes:
            ids = sorted(a for a,v in ds.athletes.items() if v.draft_year == year)
            multiplicities = Counter()
            for aid in rng.choice(ids, len(ids), replace=True):
                multiplicities[aid] += 1
                suffix = f"#bridgeboot{multiplicities[aid]}"
                new = aid+suffix
                athletes[new] = replace(ds.athletes[aid], athlete_id=new, bootstrap_group=_original(ds, aid))
                attempts.extend(replace(a, athlete_id=new, attempt_id=a.attempt_id+suffix)
                                for a in by_attempt[aid])
                plays.extend(replace(p, athlete_id=new, play_id=p.play_id+suffix) for p in by_play[aid])
                sampled_records.extend(replace(r, athlete_id=new, play_id=r.play_id+suffix,
                                                context=dict(r.context), channels=dict(r.channels),
                                                lineage={**r.lineage,"bootstrap_original_athlete":_original(ds, aid)})
                                       for r in by_record[aid])
        boot = Dataset(athletes, attempts, plays, ds.manifest, ds.outcome_definition, False)
        try:
            result = experiment(boot, sampled_records, include_ngs, seed, config)
            gain = result["summary"]["gain"]
            if gain is not None and np.isfinite(gain):
                gains.append(float(gain))
            else:
                failures.append({"draw": draw, "reason": "undefined primary relative gain"})
        except ValueError as error:
            failures.append({"draw":draw,"reason":str(error)})
        print(f"Math bridges full refit {draw+1}/{draws}", flush=True)
    return {"requested_draws":draws,"successful_draws":len(gains),"gains":gains,
            "interval_90":np.quantile(gains,[0.05,0.95]).tolist() if gains else None,
            "failures":failures,
            "scope":"empirical full-pipeline original-athlete bootstrap; does not erase prior adaptive inspections"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--minimum-plays", type=int, default=30)
    parser.add_argument("--no-ngs", action="store_true")
    parser.add_argument("--verify-known-hashes", action="store_true")
    parser.add_argument("--refits", type=int, default=0)
    args = parser.parse_args(argv)
    ds = load_official_directory(args.data, minimum_plays=args.minimum_plays,
                                 verify_known_hashes=args.verify_known_hashes)
    movement = load_movement_targets(args.data, ds)
    result = experiment(ds, movement, include_ngs=not args.no_ngs)
    if args.refits:
        result["full_refits"] = full_refit_sensitivity(ds, movement, args.refits,
                                                     include_ngs=not args.no_ngs)
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    main()
