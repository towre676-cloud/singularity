"""Short-horizon motor readouts and an uncertainty-aware scouting correction.

The source readout is ``2 * (displacement - initial_velocity * T) / T**2``.
It equals acceleration for a quadratic straight trajectory, but is generally a
weighted post-onset acceleration functional.  The operational onset is not a
known start cue, so this module does not estimate reaction time.

Smoothing branches are sensitivity scenarios, never independent observations
or calibrated sensor-error draws.  Reliability is estimated from distinct
attempts of training athletes.  The scalar Gaussian observation model assumes
a common athlete deviation after drill centering, independent attempt errors,
and transportable within-drill variance.  Its conditional uncertainty is not a
distribution-free confidence guarantee.
"""

from dataclasses import dataclass, field
from math import atan2, degrees, hypot, isfinite, log, sqrt
from statistics import mean, variance

from .linalg import solve
from .schema import Lineage


BURST_VERSION = "nfl-burst/1"
FORTY = "FORTY_YARD_DASH"
PREDECLARED_SKILL_DRILLS = (
    "PASS_RUSH_DRILL", "RUN_THE_HOOP_DRILL", "FOUR_BAG_AGILITY_DRILL",
    "FRONT_START_WAVE_DRILL_AND_LATERAL_REACTION",
)


@dataclass(frozen=True)
class BurstProtocol:
    allowed_drills: tuple = (FORTY,)
    horizon: float = 0.5
    onset_speed: float = 0.5
    sustained_frames: int = 3
    max_turn_degrees: float = 15.0
    smoothing_windows: tuple = (1, 3, 5)
    max_frame_gap: float = 0.16

    def __post_init__(self):
        if self.horizon <= 0 or self.onset_speed <= 0 or self.sustained_frames < 1:
            raise ValueError("Positive horizon/onset threshold and sustained_frames >= 1 required")
        if not 0 <= self.max_turn_degrees <= 180 or self.max_frame_gap <= 0:
            raise ValueError("Invalid turn or frame-gap threshold")
        if 1 not in self.smoothing_windows or any(k not in (1, 3, 5) for k in self.smoothing_windows):
            raise ValueError("Smoothing branches must include raw (1), with optional 3 and 5")


@dataclass(frozen=True)
class BurstObservation:
    athlete_id: str
    attempt_id: str
    drill: str
    value: float
    branches: dict
    onset_time: float
    end_time: float
    initial_speed: float
    turn_degrees: float
    lineage: Lineage

    @property
    def sensitivity(self):
        return max(self.branches.values()) - min(self.branches.values())

    @property
    def nfl_id(self):
        return self.athlete_id


def _quadratic(times, values, center):
    """Value and derivative at center, using a scaled local quadratic fit."""
    scale = max(abs(t - center) for t in times)
    if len(times) < 3 or scale <= 0:
        raise ValueError("Three distinct frames are required for a local derivative")
    rows = [[1.0, (t - center) / scale, ((t - center) / scale) ** 2] for t in times]
    gram = [[sum(row[i] * row[j] for row in rows) for j in range(3)] for i in range(3)]
    rhs = [sum(row[j] * v for row, v in zip(rows, values)) for j in range(3)]
    a, b, _ = solve(gram, rhs)
    return a, b / scale


def _causal_velocity(path, index):
    before = path[index - 2:index + 1]
    # Exact derivative of the three-point interpolating quadratic at its last
    # frame. Lagrange weights avoid solving thousands of tiny linear systems.
    a, b = before[0][0] - before[2][0], before[1][0] - before[2][0]
    weights = (-b / (a * (a - b)), -a / (b * (b - a)), -(a + b) / (a * b))
    return tuple(sum(w * r[c] for w, r in zip(weights, before)) for c in (1, 2))


def _smooth_quadratic(path, window, start=0, stop=None):
    if window in (1, 3):
        # A quadratic through exactly three distinct points interpolates each
        # point: this declared branch is mathematically identical to raw data.
        return path
    out = list(path)
    for i in range(max(0, start), min(len(path), len(path) if stop is None else stop + 1)):
        row = path[i]
        # Full window whenever possible; local polynomial boundary treatment
        # preserves quadratic motion. Three-point quadratic interpolation does
        # not itself reduce noise, and is retained only as a declared branch.
        lo = max(0, min(i - window // 2, len(path) - window))
        block = path[lo:lo + window]
        t = [r[0] for r in block]
        out[i] = (row[0], *[_quadratic(t, [r[c] for r in block], row[0])[0] for c in (1, 2)])
    return out


def _position_at(path, time):
    if time < path[0][0] - 1e-9 or time > path[-1][0] + 1e-9:
        raise ValueError("No position extrapolation is permitted")
    closest = min(range(len(path)), key=lambda k: abs(path[k][0] - time))
    if abs(path[closest][0] - time) < 1e-9:
        return path[closest][1:]
    lo = max(0, min(closest - 1, len(path) - 3))
    block = path[lo:lo + 3]
    t = [r[0] for r in block]
    return tuple(_quadratic(t, [r[c] for r in block], time)[0] for c in (1, 2))


def burst_functional(path, start, horizon=0.5, direction=None):
    """Evaluate the displacement functional; does not certify a launch event.

    This low-level function is also useful for analytic comparisons. Eligibility
    and an observed below-threshold launch history are checked by extract_burst.
    """
    if start < 2 or horizon <= 0:
        raise ValueError("Two prior frames and a positive horizon are required")
    velocity = _causal_velocity(path, start)
    if direction is None:
        norm = hypot(*velocity)
        if norm <= 1e-12:
            raise ValueError("An initial direction is required at zero velocity")
        direction = tuple(v / norm for v in velocity)
    p0, p1 = path[start][1:], _position_at(path, path[start][0] + horizon)
    travel = sum((b - a) * d for a, b, d in zip(p0, p1, direction))
    projected_v0 = sum(v * d for v, d in zip(velocity, direction))
    return 2 * (travel - projected_v0 * horizon) / horizon ** 2


def extract_burst(attempt, protocol=None):
    """First sustained onset only; return None for unqualified/unsupported starts.

    Primary initial velocity/direction uses only the onset frame and its two
    preceding frames.  Sustained-onset confirmation and straightness use the
    subsequent recorded source frames.  A turning first start is rejected;
    this function never searches for a more favorable later start.
    """
    protocol = protocol or BurstProtocol()
    if attempt.drill not in protocol.allowed_drills:
        return None
    path = [(float(f.t), float(f.x), float(f.y)) for f in attempt.frames]
    if len(path) < max(5, 2 + protocol.sustained_frames):
        return None
    if not all(isfinite(v) for row in path for v in row):
        return None
    if any(b[0] <= a[0] for a, b in zip(path, path[1:])):
        return None
    velocities = {i: _causal_velocity(path, i) for i in range(2, len(path))}
    # Without a recorded low-speed history, the trace may begin midway through
    # acceleration. Never relabel its first available frame as launch onset.
    if hypot(*velocities[2]) >= protocol.onset_speed:
        return None
    start = next((i for i in range(3, len(path) - protocol.sustained_frames + 1)
                  if all(hypot(*velocities[j]) >= protocol.onset_speed
                         for j in range(i, i + protocol.sustained_frames))), None)
    if start is None:
        return None
    t0 = path[start][0]
    end = t0 + protocol.horizon
    if end > path[-1][0] + 1e-9:
        return None
    stop = next(i for i in range(start, len(path)) if path[i][0] >= end - 1e-9)
    # Include derivative history and interpolation support in the gap audit.
    if any(path[i + 1][0] - path[i][0] > protocol.max_frame_gap
           for i in range(start - 3, stop)):
        return None
    initial = velocities[start]
    speed = hypot(*initial)
    direction = (initial[0] / speed, initial[1] / speed)
    turns = []
    for i in range(start, stop + 1):
        v = velocities[i]
        if hypot(*v) < protocol.onset_speed:
            continue
        dot = direction[0] * v[0] + direction[1] * v[1]
        cross = direction[0] * v[1] - direction[1] * v[0]
        turns.append(abs(degrees(atan2(cross, dot))))
    turn = max(turns, default=0.0)
    if turn > protocol.max_turn_degrees:
        return None
    branches = {}
    for window in protocol.smoothing_windows:
        smoothed = _smooth_quadratic(path, window, start - 2, stop + 1)
        branches[f"quadratic-{window}"] = burst_functional(smoothed, start, protocol.horizon, direction)
    h = max(protocol.smoothing_windows) // 2
    lin = Lineage(attempt.athlete_id, attempt.attempt_id, attempt.drill,
                  (0, min(len(path) - 1, stop + h + 1)),
                  (path[0][0], path[min(len(path) - 1, stop + h + 1)][0]),
                  "burst yards/s^2; speed yards/s; angle degrees", BURST_VERSION, attempt.recorded_on,
                  {"primary": "raw", "smoothing": list(protocol.smoothing_windows),
                   "onset_speed": protocol.onset_speed, "sustained_frames": protocol.sustained_frames,
                   "recorded_low_speed_history_required": True,
                   "horizon": protocol.horizon, "initial_direction": "causal trailing three-frame quadratic",
                   "branch_width_is_probability_interval": False,
                   "meaning": "post-onset motor response; no known cue or reaction-time estimate"})
    return BurstObservation(attempt.athlete_id, attempt.attempt_id, attempt.drill,
                            branches["quadratic-1"], branches, t0, end, speed, turn, lin)


def extract_bursts(attempts, protocol=None):
    return [b for a in attempts if (b := extract_burst(a, protocol)) is not None]


@dataclass(frozen=True)
class SourcePosterior:
    mean: float
    variance: float
    information_fraction: float
    attempt_count: int
    repeat_count: int
    available: bool
    excluded_drills: tuple = ()

    @property
    def prior_reliance(self):
        return 1.0 - self.information_fraction


def _unique_observations(observations):
    observations = list(observations)
    seen = set()
    for o in observations:
        key = (o.athlete_id, o.attempt_id, o.drill)
        if key in seen:
            raise ValueError("Duplicate attempt: sensitivity branches are not independent repeats")
        if not isfinite(o.value):
            raise ValueError("Nonfinite burst observation")
        seen.add(key)
    return observations


@dataclass
class ScalarReliabilityModel:
    drill_means: dict
    within_variance: dict
    prior_variance: float
    calibrated: bool
    calibration_reason: str
    repeat_degrees_of_freedom: int
    variance_sources: dict = field(default_factory=dict)
    variance_floor: float = 1e-8
    training_ids: tuple = ()

    @classmethod
    def fit(cls, observations, train_ids=None, min_repeat_df=2, variance_floor=1e-8):
        """Training-only method-of-moments calibration using actual repeat attempts.

        Sparse-drill within variance falls back to the pooled *repeat* variance,
        explicitly recorded in variance_sources. No repeat evidence means an
        uncalibrated model with unavailable readouts, not perfect reliability.
        """
        if min_repeat_df < 1 or variance_floor <= 0:
            raise ValueError("Positive calibration thresholds required")
        allowed = None if train_ids is None else set(train_ids)
        obs = _unique_observations(o for o in observations if allowed is None or o.athlete_id in allowed)
        groups = {}
        for o in obs:
            groups.setdefault((o.athlete_id, o.drill), []).append(o.value)
        by_drill, sse, dfs = {}, {}, {}
        for (_, drill), values in groups.items():
            center = mean(values)
            by_drill.setdefault(drill, []).append(center)
            sse[drill] = sse.get(drill, 0.0) + sum((v - center) ** 2 for v in values)
            dfs[drill] = dfs.get(drill, 0) + len(values) - 1
        centers = {d: mean(v) for d, v in by_drill.items()}
        total_df = sum(dfs.values())
        ids = tuple(sorted({o.athlete_id for o in obs}))
        if total_df < min_repeat_df:
            return cls(centers, {}, 0.0, False, "Insufficient distinct-attempt repeat degrees of freedom",
                       total_df, {}, variance_floor, ids)
        pooled = max(variance_floor, sum(sse.values()) / total_df)
        within, sources = {}, {}
        for d in centers:
            own = dfs[d] >= min_repeat_df
            within[d] = max(variance_floor, sse[d] / dfs[d]) if own else pooled
            sources[d] = "within_drill_repeats" if own else "pooled_distinct_attempt_repeats"
        athlete_sums = {}
        for o in obs:
            precision = 1.0 / within[o.drill]
            old = athlete_sums.setdefault(o.athlete_id, [0.0, 0.0])
            old[0] += precision * (o.value - centers[o.drill])
            old[1] += precision
        means = [a / b for a, b in athlete_sums.values()]
        noise = [1.0 / b for _, b in athlete_sums.values()]
        prior = max(0.0, variance(means) - mean(noise)) if len(means) > 1 else 0.0
        return cls(centers, within, prior, True,
                   "Training repeat variance; Gaussian common-deviation/independent-attempt assumptions",
                   total_df, sources, variance_floor, ids)

    def posterior(self, observations, athlete_id=None):
        obs = _unique_observations(o for o in observations if athlete_id is None or o.athlete_id == athlete_id)
        ids = {o.athlete_id for o in obs}
        if len(ids) > 1:
            raise ValueError("A source posterior is for one athlete")
        excluded = tuple(sorted({o.drill for o in obs if o.drill not in self.within_variance}))
        use = [o for o in obs if o.drill in self.within_variance]
        counts = {}
        for o in use:
            counts[o.drill] = counts.get(o.drill, 0) + 1
        repeats = sum(n - 1 for n in counts.values())
        if not self.calibrated or not use:
            return SourcePosterior(0.0, self.prior_variance, 0.0, len(use), repeats, False, excluded)
        if self.prior_variance <= 0:
            return SourcePosterior(0.0, 0.0, 0.0, len(use), repeats, True, excluded)
        precision = sum(1.0 / self.within_variance[o.drill] for o in use)
        posterior_var = 1.0 / (1.0 / self.prior_variance + precision)
        centered = sum((o.value - self.drill_means[o.drill]) / self.within_variance[o.drill] for o in use)
        information = max(0.0, min(1.0, 1.0 - posterior_var / self.prior_variance))
        return SourcePosterior(posterior_var * centered, posterior_var, information,
                               len(use), repeats, True, excluded)


def integrated_nll(loading, nfl_variance, posteriors, residuals, outcome_variances=None, penalty=0.0):
    """Gaussian integrated negative log likelihood, omitting constant n*log(2pi)/2.

    Outcome variance must describe actual outcome-estimation uncertainty; branch
    widths cannot be substituted. This assumes independence of source and NFL
    estimation errors conditional on the latent athlete deviation.
    """
    posteriors, residuals = list(posteriors), list(residuals)
    noise = [0.0] * len(residuals) if outcome_variances is None else list(outcome_variances)
    if len(posteriors) != len(residuals) or len(noise) != len(residuals):
        raise ValueError("Posterior, outcome and variance arrays must have equal lengths")
    if nfl_variance < 0 or penalty < 0 or not isfinite(loading) or not isfinite(nfl_variance):
        raise ValueError("Finite parameters and nonnegative variances/penalty required")
    total = 0.5 * penalty * loading ** 2
    for p, r, nu in zip(posteriors, residuals, noise):
        if p.variance < 0 or nu < 0 or not all(isfinite(v) for v in (p.mean, p.variance, r, nu)):
            raise ValueError("Finite outcomes and nonnegative source/outcome variances required")
        var = max(1e-12, nfl_variance + nu + loading ** 2 * p.variance)
        total += 0.5 * (log(var) + (r - loading * p.mean) ** 2 / var)
    return total


def _golden_minimize(function, lo, hi, iterations=40):
    ratio = (sqrt(5.0) - 1.0) / 2.0
    a, b = hi - ratio * (hi - lo), lo + ratio * (hi - lo)
    fa, fb = function(a), function(b)
    for _ in range(iterations):
        if fa <= fb:
            hi, b, fb = b, a, fa
            a = hi - ratio * (hi - lo)
            fa = function(a)
        else:
            lo, a, fa = a, b, fb
            b = lo + ratio * (hi - lo)
            fb = function(b)
    candidates = [(lo, function(lo)), (hi, function(hi)), (a, fa), (b, fb)]
    return min(candidates, key=lambda pair: pair[1])


@dataclass
class IntegratedScoutCorrection:
    loading: float
    nfl_variance: float
    penalty: float
    training_nll: float
    baseline_nll: float
    n_training: int
    optimizer: str = "deterministic profiled coarse grid plus bounded golden search"

    @classmethod
    def fit(cls, posteriors, residuals, outcome_variances=None, penalty=1.0):
        """Fit a scalar correction on training residuals; tune penalty outside this function.

        The lambda=0 baseline is evaluated with the identical outcome-noise
        specification and optimized NFL variance. Bounded numerical optimization
        is not a proof of the global optimum or held-out scouting advantage.
        """
        ps, rs = list(posteriors), list(residuals)
        nus = [0.0] * len(rs) if outcome_variances is None else list(outcome_variances)
        if not rs:
            raise ValueError("At least one training outcome is required")
        integrated_nll(0.0, 1.0, ps, rs, nus, penalty)  # input validation
        cache = {}

        def profile(loading):
            if loading in cache:
                return cache[loading]
            errors = [(r - loading * p.mean) ** 2 for p, r in zip(ps, rs)]
            upper = max(1e-10, 4.0 * max(errors))
            grid = [0.0] + [upper * 10 ** (-8 + k / 2) for k in range(17)]
            f = lambda s: integrated_nll(loading, s, ps, rs, nus, penalty)
            vals = [f(s) for s in grid]
            index = min(range(len(grid)), key=lambda k: vals[k])
            best = (grid[index], vals[index])
            if 0 < index < len(grid) - 1:
                refined = _golden_minimize(f, grid[index - 1], grid[index + 1], 32)
                best = min(best, refined, key=lambda pair: pair[1])
            cache[loading] = best
            return best

        base_sigma, base_loss = profile(0.0)
        if not any(abs(p.mean) > 1e-12 for p in ps):
            return cls(0.0, base_sigma, penalty, base_loss, base_loss, len(rs))
        signal_scale = sqrt(mean(p.mean ** 2 for p in ps))
        outcome_scale = sqrt(mean(r ** 2 for r in rs))
        bound = max(1.0, 8.0 * outcome_scale / max(signal_scale, 1e-12))
        grid = [bound * (k - 16) / 16 for k in range(33)]
        vals = [profile(lam)[1] for lam in grid]
        index = min(range(len(grid)), key=lambda k: vals[k])
        candidates = [(0.0, base_loss), (grid[index], vals[index])]
        if 0 < index < len(grid) - 1:
            candidates.append(_golden_minimize(lambda lam: profile(lam)[1], grid[index - 1], grid[index + 1], 40))
        lam, _ = min(candidates, key=lambda pair: pair[1])
        sigma, _ = profile(lam)
        nll = integrated_nll(lam, sigma, ps, rs, nus)
        return cls(lam, sigma, penalty, nll, base_loss, len(rs))

    def predict(self, posterior):
        return self.loading * posterior.mean

    def predict_many(self, posteriors):
        return [self.predict(p) for p in posteriors]

    def predictive_variance(self, posterior, outcome_variance=0.0):
        if outcome_variance < 0:
            raise ValueError("Outcome variance must be nonnegative")
        return self.nfl_variance + outcome_variance + self.loading ** 2 * posterior.variance
