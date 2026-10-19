"""Target-directed numerical delay states for movement continuations.

Consecutive movement samples form *past* and *future* delay-block Hankel rows.
A weighted ridge continuation map is compressed by the singular vectors of its
fitted future outputs.  Its state is therefore directed at a declared finite
movement horizon, rather than at reconstructing arbitrary athlete parameters.
History length, rank and penalty are selected on whole-player inner folds.
Frames/attempts never count as independent validation athletes.

This is a noisy numerical supervised delay model, not exact ERA and not an
application of the exact word-realization theorem to athlete physiology.  It
does not claim a globally valid dynamical state, all-future equivalence, or a
certified forecast error.  Output coordinates must be movement measurements;
football labels have no role in representation selection.  Latent coordinates
can rotate across fits: transfer physical-coordinate forecasts/readouts, not
unaligned latent coordinates from separately fitted folds.
"""

from collections import Counter
from dataclasses import dataclass
from math import sqrt
from typing import Sequence

import numpy as np


PREDICTIVE_STATE_VERSION = "nfl-predictive-state/1"


@dataclass(frozen=True)
class MovementSequence:
    """One uniformly sampled attempt, with causal channels in declared units.

    ``outputs`` defaults to the same channels.  Source extraction must not use
    frames after a forecast origin to calculate its input channels.  This
    module cannot infer whether supplied velocities were smoothed causally.
    ``original_athlete_id`` keeps bootstrap copies in one validation fold.
    """

    athlete_id: str
    attempt_id: str
    times: Sequence[float]
    channels: Sequence[Sequence[float]]
    outputs: Sequence[Sequence[float]] | None = None
    original_athlete_id: str | None = None

    @property
    def group(self):
        return self.original_athlete_id or self.athlete_id


@dataclass(frozen=True)
class _Rows:
    past: np.ndarray
    future: np.ndarray
    athletes: tuple[str, ...]
    groups: tuple[str, ...]
    attempts: tuple[str, ...]
    origins: np.ndarray


@dataclass(frozen=True)
class PredictiveStateModel:
    """Compressed direct forecasts over exactly ``horizon_steps`` steps."""

    history_steps: int
    horizon_steps: int
    state_count: int
    requested_rank: int
    ridge_penalty: float
    sample_interval: float
    input_mean: np.ndarray
    input_scale: np.ndarray
    output_mean: np.ndarray
    output_scale: np.ndarray
    past_center: np.ndarray
    future_center: np.ndarray
    state_map: np.ndarray
    decoder: np.ndarray
    continuation_singular_values: np.ndarray
    training_athlete_ids: tuple[str, ...]
    training_group_ids: tuple[str, ...]
    channel_names: tuple[str, ...]
    output_names: tuple[str, ...]
    comparison_history_steps: int
    support_precision: np.ndarray
    observed_past_basis: np.ndarray
    training_support_p95: float
    version: str = PREDICTIVE_STATE_VERSION

    def transform(self, history):
        """Return a state for one ``(history, channels)`` block or a batch.

        A state contains no future observations.  Input history has to use the
        same alignment, sampling interval and causal channel definition as fit.
        """
        value = np.asarray(history, dtype=float)
        shape = (self.history_steps, len(self.input_mean))
        if value.ndim not in (2, 3) or value.shape[-2:] != shape:
            raise ValueError(f"History must have trailing shape {shape}")
        if not np.isfinite(value).all():
            raise ValueError("History channels must be finite")
        batch = value.ndim == 3
        values = value if batch else value[None, :, :]
        standardized = (values - self.input_mean) / self.input_scale
        past = standardized.reshape(len(values), -1) - self.past_center
        states = past @ self.state_map
        return states if batch else states[0]

    def forecast(self, history, steps=None):
        """Return future movement in physical output coordinates, no rollout.

        ``steps`` can shorten the declared horizon; it cannot extend it.  The
        fit is a direct multi-step prediction and supplies no all-time bound.
        """
        if steps is None:
            steps = self.horizon_steps
        if not isinstance(steps, (int, np.integer)) or not 1 <= steps <= self.horizon_steps:
            raise ValueError("Requested steps must be within the fitted finite horizon")
        states = self.transform(history)
        batch = states.ndim == 2
        state_rows = states if batch else states[None, :]
        standard = state_rows @ self.decoder + self.future_center
        standard = standard.reshape(-1, self.horizon_steps, len(self.output_mean))
        physical = standard * self.output_scale + self.output_mean
        return physical[:, :steps] if batch else physical[0, :steps]

    def forecast_features(self, history, steps=None):
        """Flatten physical continuation coordinates, stable across SVD bases."""
        prediction = self.forecast(history, steps)
        return prediction.reshape(prediction.shape[0], -1) if prediction.ndim == 3 else prediction.reshape(-1)

    def support(self, history):
        """Describe distance from training pasts; not a confidence interval.

        A regularized Mahalanobis distance flags unfamiliar histories, including
        cross-domain motion.  Orthogonal distance separately exposes departure
        from the numerically observed delay-design subspace.  A training 95th
        percentile flag is descriptive, not a calibrated coverage guarantee.
        """
        self.transform(history)  # Reuse the history shape/finite-value checks.
        value = np.asarray(history, dtype=float)
        batch = value.ndim == 3
        values = value if batch else value[None, :, :]
        past = ((values - self.input_mean) / self.input_scale).reshape(len(values), -1) - self.past_center
        dimension = past.shape[1]
        distances = np.sqrt(np.maximum(np.einsum("ni,ij,nj->n", past, self.support_precision, past), 0) / dimension)
        projected = (past @ self.observed_past_basis.T) @ self.observed_past_basis
        orthogonal = np.linalg.norm(past - projected, axis=1) / sqrt(dimension)
        def record(index):
            return {"mahalanobis_distance": float(distances[index]),
                    "orthogonal_design_distance": float(orthogonal[index]),
                    "training_p95_distance": self.training_support_p95,
                    "outside_training_p95": bool(distances[index] > self.training_support_p95),
                    "scope": "Training-history distance, not calibrated forecast uncertainty"}
        return [record(i) for i in range(len(values))] if batch else record(0)


@dataclass(frozen=True)
class PredictiveStateFit:
    model: PredictiveStateModel
    instantaneous_model: PredictiveStateModel
    selection_scores: tuple[dict, ...]
    fold_groups: dict[str, int]
    selected_cv_mse: float
    instantaneous_cv_mse: float
    forecast_tolerance: float | None
    meets_declared_tolerance: bool | None
    training_athlete_ids: tuple[str, ...]
    excluded_athlete_ids: tuple[str, ...]
    scope: str = "Numerical movement continuation; not NFL scouting evidence"

    @property
    def continuation_gain(self):
        """Inner-validation MSE reduction relative to instantaneous histories."""
        if self.instantaneous_cv_mse <= 0:
            return None
        return 1.0 - self.selected_cv_mse / self.instantaneous_cv_mse


def _array(sequence, sample_interval=None, timing_tolerance=1e-5):
    times = np.asarray(sequence.times, dtype=float)
    channels = np.asarray(sequence.channels, dtype=float)
    outputs = channels if sequence.outputs is None else np.asarray(sequence.outputs, dtype=float)
    if not sequence.athlete_id or not sequence.attempt_id:
        raise ValueError("Athlete and attempt identities are required")
    if times.ndim != 1 or len(times) < 2:
        raise ValueError("At least two one-dimensional timestamps are required")
    if channels.ndim != 2 or outputs.ndim != 2 or channels.shape[0] != len(times) or outputs.shape[0] != len(times):
        raise ValueError("Channels and outputs must be frame-by-channel arrays")
    if not channels.shape[1] or not outputs.shape[1]:
        raise ValueError("At least one movement channel and output are required")
    if not np.isfinite(times).all() or not np.isfinite(channels).all() or not np.isfinite(outputs).all():
        raise ValueError("Movement timestamps, channels and outputs must be finite")
    diffs = np.diff(times)
    if np.any(diffs <= 0):
        raise ValueError("Duplicate or non-increasing timestamps are not permitted")
    interval = float(np.median(diffs)) if sample_interval is None else float(sample_interval)
    if not np.isfinite(interval) or interval <= 0:
        raise ValueError("A positive finite sampling interval is required")
    if np.any(np.abs(diffs - interval) > timing_tolerance * max(1.0, interval)):
        raise ValueError("Gaps or irregular sampling require explicit resampling before fitting")
    return times, channels, outputs, interval


def _validated(sequences, sample_interval=None):
    if not sequences:
        raise ValueError("At least one movement sequence is required")
    seen = set()
    dims = None
    interval = sample_interval
    arrays = []
    for sequence in sequences:
        identity = (sequence.athlete_id, sequence.attempt_id)
        if identity in seen:
            raise ValueError("Duplicate athlete/attempt records are not independent attempts")
        seen.add(identity)
        times, channels, outputs, observed_interval = _array(sequence, interval)
        if interval is None:
            interval = observed_interval
        if dims is None:
            dims = (channels.shape[1], outputs.shape[1])
        if dims != (channels.shape[1], outputs.shape[1]):
            raise ValueError("Every sequence must have the same channel and output dimensions")
        arrays.append((sequence, times, channels, outputs))
    return arrays, float(interval), dims


def _weights(groups):
    """Equal total sampled-athlete weight; preserve bootstrap multiplicity.

    Use sampled athlete IDs here, original IDs only for fold isolation.  Giving
    every original group equal total weight would cancel repeated bootstrap
    draws and would not reproduce the empirical bootstrap distribution.
    """
    counts = Counter(groups)
    return np.asarray([1.0 / (len(counts) * counts[g]) for g in groups])


def _frame_scaler(arrays, which):
    values = np.concatenate([record[which] for record in arrays], axis=0)
    athletes = tuple(a for record in arrays for a in [record[0].athlete_id] * len(record[1]))
    weights = _weights(athletes)
    mean = weights @ values
    variance = weights @ ((values - mean) ** 2)
    scale = np.sqrt(np.maximum(variance, 0.0))
    scale[scale < 1e-10] = 1.0
    return mean, scale


def _rows(arrays, history_steps, horizon_steps, minimum_history_steps):
    past, future, athletes, groups, attempts, origins = [], [], [], [], [], []
    for sequence, _, channels, outputs in arrays:
        for origin in range(minimum_history_steps - 1, len(channels) - horizon_steps):
            past.append(channels[origin - history_steps + 1:origin + 1])
            future.append(outputs[origin + 1:origin + horizon_steps + 1])
            athletes.append(sequence.athlete_id)
            groups.append(sequence.group)
            attempts.append(sequence.attempt_id)
            origins.append(origin)
    if not past:
        raise ValueError("No sequence supports the common history and forecast horizon")
    return _Rows(np.asarray(past), np.asarray(future), tuple(athletes), tuple(groups),
                 tuple(attempts), np.asarray(origins))


def _fit(arrays, interval, history, horizon, rank, penalty, common_history, channel_names, output_names):
    rows = _rows(arrays, history, horizon, common_history)
    x_mean, x_scale = _frame_scaler(arrays, 2)
    y_mean, y_scale = _frame_scaler(arrays, 3)
    past = ((rows.past - x_mean) / x_scale).reshape(len(rows.past), -1)
    future = ((rows.future - y_mean) / y_scale).reshape(len(rows.future), -1)
    weights = _weights(rows.athletes)
    past_center, future_center = weights @ past, weights @ future
    past = past - past_center
    future = future - future_center
    weighted_x = past * np.sqrt(weights[:, None])
    weighted_y = future * np.sqrt(weights[:, None])
    # SVD ridge avoids squaring the condition number of a delay design.  The
    # penalty is on equal-player average loss and is independent of frame count.
    u, singular, vt = np.linalg.svd(weighted_x, full_matrices=False)
    cutoff = (singular[0] if len(singular) else 0.0) * 1e-12
    if penalty == 0:
        inverse = np.divide(1.0, singular, out=np.zeros_like(singular), where=singular > cutoff)
    else:
        inverse = singular / (singular ** 2 + penalty)
    coefficient = (vt.T * inverse) @ (u.T @ weighted_y)
    # Compress the fitted continuation map in the weighted training-output
    # metric.  This is a truncated ridge prediction, not a claimed optimum of
    # every rank-constrained ridge formulation.
    fitted = weighted_x @ coefficient
    _, continuation_singular, future_vt = np.linalg.svd(fitted, full_matrices=False)
    continuation_cutoff = (continuation_singular[0] if len(continuation_singular) else 0.0) * 1e-10
    numerical_rank = int(np.sum(continuation_singular > max(continuation_cutoff, 1e-12)))
    state_count = min(rank, numerical_rank)
    decoder = future_vt[:state_count]
    state_map = coefficient @ decoder.T
    covariance = weighted_x.T @ weighted_x
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    floor = max(float(eigenvalues[-1]) * 1e-3, 1e-6)
    support_precision = (eigenvectors * (1 / np.maximum(eigenvalues, floor))) @ eigenvectors.T
    distances = np.sqrt(np.maximum(np.einsum("ni,ij,nj->n", past, support_precision, past), 0) / past.shape[1])
    order = np.argsort(distances)
    index = min(int(np.searchsorted(np.cumsum(weights[order]), 0.95)), len(order) - 1)
    support_p95 = float(distances[order[index]])
    observed_basis = vt[singular > max(cutoff, 1e-12)]
    return PredictiveStateModel(
        history, horizon, state_count, rank, penalty, interval, x_mean, x_scale, y_mean, y_scale,
        past_center, future_center, state_map, decoder, continuation_singular,
        tuple(sorted({record[0].athlete_id for record in arrays})),
        tuple(sorted({record[0].group for record in arrays})), channel_names, output_names, common_history,
        support_precision, observed_basis, support_p95,
    )


def _score(model, arrays):
    rows = _rows(arrays, model.history_steps, model.horizon_steps, model.comparison_history_steps)
    predictions = model.forecast(rows.past)
    standardized_error = (predictions - rows.future) / model.output_scale
    row_errors = np.mean(standardized_error ** 2, axis=(1, 2))
    athlete_errors = {athlete: float(np.mean(row_errors[np.asarray(rows.athletes) == athlete]))
                      for athlete in set(rows.athletes)}
    return athlete_errors


def discover_predictive_state(
    sequences, *, train_athlete_ids=None, history_steps=(1, 3, 5), ranks=(1, 2, 3),
    horizon_steps=3, ridge_penalties=(1e-6, 1e-3, 0.1), inner_folds=3,
    seed=2718, selection_tolerance=0.01, forecast_tolerance=None,
    sample_interval=None, channel_names=None, output_names=None,
):
    """Discover a small finite-horizon state entirely within training players.

    All candidates use common forecast origins, including the instantaneous
    comparator.  The simplest model within ``selection_tolerance`` of the best
    player-held MSE is selected.  ``forecast_tolerance`` optionally declares a
    standardized RMSE ceiling; meeting it is an inner-validation observation,
    not a distribution-free guarantee.  Pass outer-test records only with an
    explicit training-ID subset; their values do not enter fit or selection.
    """
    sequences = list(sequences)
    all_ids = {s.athlete_id for s in sequences}
    train_ids = all_ids if train_athlete_ids is None else set(train_athlete_ids)
    if not train_ids or not train_ids.issubset(all_ids):
        raise ValueError("Training IDs must name observed athletes")
    selected = [s for s in sequences if s.athlete_id in train_ids]
    excluded = [s for s in sequences if s.athlete_id not in train_ids]
    if {s.group for s in selected} & {s.group for s in excluded}:
        raise ValueError("Original-athlete leakage: bootstrap copies cannot straddle train and excluded sets")
    arrays, interval, (n_input, n_output) = _validated(selected, sample_interval)
    histories = sorted(set(history_steps) | {1})
    rank_values = sorted(set(ranks) | {1})
    penalties = sorted(set(ridge_penalties))
    if any(not isinstance(x, (int, np.integer)) or x < 1 for x in histories + rank_values):
        raise ValueError("History lengths and ranks must be positive integers")
    if not isinstance(horizon_steps, (int, np.integer)) or horizon_steps < 1:
        raise ValueError("A positive integer forecast horizon is required")
    if not penalties or any(not np.isfinite(p) or p < 0 for p in penalties):
        raise ValueError("At least one finite nonnegative ridge penalty is required")
    if not rank_values or not np.isfinite(selection_tolerance) or selection_tolerance < 0:
        raise ValueError("Ranks and a finite nonnegative selection tolerance are required")
    if forecast_tolerance is not None and (not np.isfinite(forecast_tolerance) or forecast_tolerance < 0):
        raise ValueError("Forecast tolerance must be finite and nonnegative")
    channel_names = tuple(channel_names or (f"channel_{i}" for i in range(n_input)))
    output_names = tuple(output_names or (f"output_{i}" for i in range(n_output)))
    if len(channel_names) != n_input or len(output_names) != n_output:
        raise ValueError("Channel and output names must match array dimensions")
    common_history = max(histories)
    if any(len(record[1]) < common_history + horizon_steps for record in arrays):
        raise ValueError("Every sequence must support the common history and forecast horizon")
    _rows(arrays, common_history, horizon_steps, common_history)
    groups = sorted({s.group for s in selected})
    if not isinstance(inner_folds, (int, np.integer)) or not 2 <= inner_folds <= len(groups):
        raise ValueError("Inner validation needs at least two distinct original athletes per fold plan")
    shuffled = np.asarray(groups, dtype=object)
    np.random.default_rng(seed).shuffle(shuffled)
    fold_groups = {str(group): i % inner_folds for i, group in enumerate(shuffled)}
    candidates = [(history, rank, penalty) for history in histories for rank in rank_values
                  if rank <= min(history * n_input, horizon_steps * n_output) for penalty in penalties]
    scores = []
    for history, rank, penalty in candidates:
        player_errors, state_counts = {}, []
        for fold in range(inner_folds):
            train = [record for record in arrays if fold_groups[record[0].group] != fold]
            held = [record for record in arrays if fold_groups[record[0].group] == fold]
            model = _fit(train, interval, history, horizon_steps, rank, penalty, common_history,
                         channel_names, output_names)
            player_errors.update(_score(model, held))
            state_counts.append(model.state_count)
        score = float(np.mean(list(player_errors.values())))
        scores.append({"history_steps": history, "rank": rank, "ridge_penalty": penalty,
                       "mse": score, "rmse": sqrt(score), "player_errors": dict(sorted(player_errors.items())),
                       "fold_state_counts": state_counts, "independent_athletes": len(groups),
                       "sampled_athletes": len(player_errors)})
    if not scores:
        raise ValueError("No requested rank is feasible for the declared channels/horizon")

    def choose(options):
        best = min(option["mse"] for option in options)
        admissible = [option for option in options if option["mse"] <= best * (1 + selection_tolerance) + 1e-12]
        return min(admissible, key=lambda option: (option["rank"], option["history_steps"],
                                                   option["mse"], -option["ridge_penalty"]))

    chosen = choose(scores)
    instantaneous = choose([s for s in scores if s["history_steps"] == 1])

    def refit(choice):
        return _fit(arrays, interval, choice["history_steps"], horizon_steps, choice["rank"],
                    choice["ridge_penalty"], common_history, channel_names, output_names)

    return PredictiveStateFit(
        refit(chosen), refit(instantaneous), tuple(scores), fold_groups,
        chosen["mse"], instantaneous["mse"], forecast_tolerance,
        None if forecast_tolerance is None else chosen["rmse"] <= forecast_tolerance,
        tuple(sorted(train_ids)), tuple(sorted(all_ids - train_ids)),
    )


def continuation_diagnostics(model, sequences, *, require_unseen_players=True, max_candidates=8):
    """Evaluate continuation errors and expose residual-linked candidates.

    Candidates are descriptive correlations with causal history functions, not
    selected extra features or physical discoveries.  Any augmentation needs
    a fresh training-only fit and independent player-held evaluation.  Do not
    interpret overlapping frame origins as independent replications.
    """
    arrays, _, dimensions = _validated(list(sequences), model.sample_interval)
    if dimensions != (len(model.input_mean), len(model.output_mean)):
        raise ValueError("Evaluation movement dimensions differ from fit")
    if require_unseen_players and {r[0].group for r in arrays} & set(model.training_group_ids):
        raise ValueError("Held-out continuation diagnostics require unseen original athletes")
    if not isinstance(max_candidates, (int, np.integer)) or max_candidates < 0:
        raise ValueError("max_candidates must be a nonnegative integer")
    rows = _rows(arrays, model.history_steps, model.horizon_steps, model.comparison_history_steps)
    predictions = model.forecast(rows.past)
    errors = (rows.future - predictions) / model.output_scale
    weights = _weights(rows.athletes)
    by_horizon = np.sum(weights[:, None, None] * errors ** 2, axis=(0, 2)) / len(model.output_mean)
    physical_mse = np.sum(weights[:, None, None] * (rows.future - predictions) ** 2, axis=0)
    feature_values = {}
    full_past = _rows(arrays, model.comparison_history_steps, model.horizon_steps,
                      model.comparison_history_steps).past
    for c, name in enumerate(model.channel_names):
        feature_values[f"latest:{name}"] = full_past[:, -1, c]
        if model.comparison_history_steps >= 2:
            feature_values[f"recent_difference:{name}"] = full_past[:, -1, c] - full_past[:, -2, c]
        if model.comparison_history_steps >= 3:
            feature_values[f"curvature:{name}"] = full_past[:, -1, c] - 2 * full_past[:, -2, c] + full_past[:, -3, c]
    candidates = []
    for name, value in feature_values.items():
        centered = value - weights @ value
        variance = weights @ (centered ** 2)
        if variance <= 1e-14:
            continue
        for step in range(model.horizon_steps):
            for c, output in enumerate(model.output_names):
                residual = errors[:, step, c]
                residual = residual - weights @ residual
                residual_variance = weights @ (residual ** 2)
                if residual_variance <= 1e-14:
                    continue
                correlation = float((weights @ (centered * residual)) / sqrt(variance * residual_variance))
                candidates.append({"history_function": name, "future_output": output,
                                   "horizon_step": step + 1, "correlation": correlation,
                                   "status": "Descriptive defect; requires fresh player-held validation"})
    candidates.sort(key=lambda c: (-abs(c["correlation"]), c["history_function"], c["horizon_step"], c["future_output"]))
    player_errors = _score(model, arrays)
    mse = float(np.mean(list(player_errors.values())))
    return {"standardized_mse": mse, "standardized_rmse": sqrt(mse),
            "per_player_mse": dict(sorted(player_errors.items())),
            "per_horizon_standardized_mse": by_horizon.tolist(),
            "physical_mse_by_horizon_and_output": physical_mse.tolist(),
            "forecast_rows": len(rows.past), "independent_athletes": len(set(rows.groups)),
            "sampled_athletes": len(player_errors),
            "defect_candidates": candidates[:max_candidates],
            "scope": "Finite-horizon movement diagnostics; no scouting or all-time guarantee"}


def forecast_features(model, *, sequence=None, origin_index=None, history=None, steps=None):
    """Canonical forecast features from history or a causal sequence prefix.

    This convenience interface deliberately ignores frames after the origin.
    Modifying future movement or output labels cannot alter the features.
    ``sequence.outputs`` is not consulted when constructing source features.
    """
    if (sequence is None) == (history is None):
        raise ValueError("Provide exactly one sequence or history")
    if sequence is not None:
        if not isinstance(origin_index, (int, np.integer)) or not model.history_steps - 1 <= origin_index < len(sequence.times):
            raise ValueError("Forecast origin must have the fitted observed history")
        times = np.asarray(sequence.times[:origin_index + 1], dtype=float)
        channels = np.asarray(sequence.channels[:origin_index + 1], dtype=float)
        if len(times) != len(channels) or channels.ndim != 2 or not np.isfinite(times).all():
            raise ValueError("Observed sequence prefix is malformed")
        if len(times) > 1 and np.any(np.abs(np.diff(times) - model.sample_interval) > 1e-5 * max(1.0, model.sample_interval)):
            raise ValueError("Observed prefix has gaps or duplicate timestamps")
        history = channels[-model.history_steps:]
    elif origin_index is not None:
        raise ValueError("origin_index is only valid with a sequence")
    return model.forecast_features(history, steps)
