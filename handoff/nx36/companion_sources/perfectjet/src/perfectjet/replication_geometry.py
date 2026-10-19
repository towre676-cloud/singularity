"""Whole-vector repeat uncertainty, interval ranks and exact replication budgets.

Prediction regions target new measured attempts, not latent athletic ability.
Coverage requires exchangeable original calibration/test groups conditional on
separately fitted models; chronological cohorts do not ensure exchangeability.
"""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction as Q
from math import ceil, floor, inf, isfinite, sqrt
from numbers import Integral
from typing import Mapping, Sequence
import numpy as np


def _fraction(value, name):
    if isinstance(value, bool):
        raise ValueError(f'{name} must be numeric, not boolean')
    try:
        return value if isinstance(value, Q) else Q(str(value))
    except (ValueError, TypeError, ZeroDivisionError) as exc:
        raise ValueError(f'{name} must be finite') from exc


def _family(value):
    if isinstance(value, bool) or not isinstance(value, Integral) or value < 1:
        raise ValueError('family_size must be a positive integer')
    return int(value)


def calibration_requirement(alpha='0.1', family_size=1):
    """Exact finite-radius requirement for this Bonferroni split construction.

    Not a sample-size lower bound on every possible prediction method.
    """
    a = _fraction(alpha, 'alpha'); k = _family(family_size)
    if not 0 < a < 1:
        raise ValueError('alpha must lie strictly between zero and one')
    return ceil(Q(k)/a)-1


@dataclass(frozen=True)
class CalibratedRadius:
    radius: float
    groups: int
    order_statistic: int
    alpha: Q
    family_size: int

    def receipt(self):
        return {'radius': self.radius if isfinite(self.radius) else None,
                'finite': isfinite(self.radius), 'original_groups': self.groups,
                'order_statistic': self.order_statistic,
                'alpha': str(self.alpha), 'family_size': self.family_size,
                'required_groups_for_finite_radius': calibration_requirement(self.alpha, self.family_size),
                'guarantee_scope': 'coverage requires group exchangeability and independent fitting; not conditional-on-selection coverage'}


def calibrate(scores: Sequence[float], *, alpha='0.1', group_ids=None, family_size=1):
    """Take group maxima, then exact-order split quantile, retaining infinity.

    Duplicate IDs, including bootstrap copies, cannot increase sample size.
    """
    a = _fraction(alpha, 'alpha'); family_size = _family(family_size)
    if not 0 < a < 1:
        raise ValueError('alpha must lie strictly between zero and one')
    values = tuple(float(s) for s in scores)
    if any(not isfinite(s) or s < 0 for s in values):
        raise ValueError('scores must be finite and nonnegative')
    ids = tuple(range(len(values))) if group_ids is None else tuple(group_ids)
    if len(ids) != len(values):
        raise ValueError('one original group ID is required per score')
    grouped = {}
    for key, value in zip(ids, values):
        if key is None or isinstance(key, (float, np.floating)) and not isfinite(key):
            raise ValueError('group ID cannot be missing or nonfinite')
        try:
            grouped[key] = max(grouped.get(key, 0.), value)
        except TypeError as exc:
            raise ValueError('group IDs must be hashable') from exc
    v = sorted(grouped.values()); m = len(v)
    order = ceil((m+1)*(1-a/family_size))
    return CalibratedRadius(v[order-1] if order <= m else inf, m, order, a, family_size)


def _covariance(value, width=None, positive=False):
    c = np.asarray(value, dtype=float)
    if c.ndim != 2 or c.shape[0] != c.shape[1] or not c.shape[0] or (width is not None and c.shape[0] != width):
        raise ValueError('nonempty square covariance of compatible dimension required')
    if not np.isfinite(c).all() or not np.allclose(c, c.T, atol=1e-12, rtol=1e-10):
        raise ValueError('covariance must be finite and symmetric')
    c = (c+c.T)/2; e = np.linalg.eigvalsh(c)
    if e[0] < -1e-10*max(1., float(np.max(np.abs(e)))):
        raise ValueError('covariance must be positive semidefinite')
    if positive and e[0] <= 0:
        raise ValueError('scoring covariance must be positive definite')
    return c


def ellipsoid_scores(truth, centers, covariance):
    y, mu = np.asarray(truth, float), np.asarray(centers, float)
    if y.ndim != 2 or y.shape != mu.shape or not np.isfinite(y).all() or not np.isfinite(mu).all():
        raise ValueError('finite equal-shaped sample-by-coordinate matrices required')
    c = _covariance(covariance, y.shape[1], positive=True)
    return np.linalg.norm(np.linalg.solve(np.linalg.cholesky(c), (y-mu).T).T, axis=1)


def linear_interval(center, covariance, radius, loading):
    """Sharp support for every linear loading on one vector ellipsoid.

    Simultaneous across loadings for this vector, NOT across multiple players.
    """
    mu, h = np.asarray(center, float), np.asarray(loading, float)
    if mu.ndim != 1 or h.shape != mu.shape or not np.isfinite(mu).all() or not np.isfinite(h).all():
        raise ValueError('finite compatible center and loading vectors required')
    c = _covariance(covariance, len(mu)); radius = float(radius)
    if np.isnan(radius) or radius < 0:
        raise ValueError('nonnegative radius required; infinity allowed')
    value = float(h@mu); var = max(0., float(h@c@h))
    if not np.any(h) or var == 0:
        return value, value
    width = radius*sqrt(var)
    return value-width, value+width


def interval_ranks(bounds: Mapping[str, tuple[float, float]], *, top_k=1):
    """Attainable best/worst 1-based ranks over a box, larger score is better.

    Ties can be broken either way. Pair counts are not independent sample sizes.
    """
    if not bounds or isinstance(top_k, bool) or not isinstance(top_k, Integral) or not 1 <= top_k <= len(bounds):
        raise ValueError('nonempty bounds and 1 <= top_k <= player count required')
    for lo, hi in bounds.values():
        if np.isnan(lo) or np.isnan(hi) or lo > hi:
            raise ValueError('invalid interval')
    out = {}; settled = 0; keys = tuple(bounds)
    for i, aid in enumerate(keys):
        lo, hi = bounds[aid]
        best = 1+sum(bounds[b][0] > hi for b in keys if b != aid)
        worst = 1+sum(bounds[b][1] >= lo for b in keys if b != aid)
        out[aid] = {'best_rank': best, 'worst_rank': worst,
                    'possible_top_k': best <= top_k, 'guaranteed_top_k': worst <= top_k}
        settled += sum(hi < bounds[b][0] or lo > bounds[b][1] for b in keys[i+1:])
    return {'ranks': out, 'settled_pairs': settled, 'total_pairs': len(keys)*(len(keys)-1)//2,
            'top_k': int(top_k), 'scope': 'deterministic conditional on every interval containing its target'}


def repeat_covariance(signal, noise, repeats, *, target='next_attempt'):
    """Independent-repeat Gaussian working covariance, not certified coverage.

    Latent covariance tends to zero, next-attempt covariance tends to noise.
    """
    if isinstance(repeats, bool) or not isinstance(repeats, Integral) or repeats < 0:
        raise ValueError('repeats must be a nonnegative integer')
    s = _covariance(signal); n = _covariance(noise, len(s), positive=True)
    if target not in ('latent', 'next_attempt'):
        raise ValueError('target must be latent or next_attempt')
    if repeats:
        latent = s-s@np.linalg.solve(s+n/repeats, s)
        latent = (latent+latent.T)/2
    else:
        latent = s.copy()
    return latent+n if target == 'next_attempt' else latent


def scalar_repeat_budget(signal_variance, noise_variance, gap, radius, *, target='next_attempt', minimum=1):
    """Exact scalar budget for two equal-variance, frozen-center players.

    Requires gap > 2*radius*sqrt(v_m). New data change centers; a conformal
    radius calibrated for one known attempt is not validated for other counts.
    """
    s, n, g, q = (_fraction(v, k) for v, k in zip((signal_variance, noise_variance, gap, radius), ('signal', 'noise', 'gap', 'radius')))
    if min(s, n, g, q) < 0 or isinstance(minimum, bool) or not isinstance(minimum, Integral) or minimum < 1:
        raise ValueError('nonnegative inputs and a positive minimum required')
    if target not in ('latent', 'next_attempt'):
        raise ValueError('target must be latent or next_attempt')
    floor_variance = n if target == 'next_attempt' else Q(0)
    if g == 0:
        return {'repeats': None, 'reason': 'zero frozen gap cannot satisfy a strict comparison', 'variance_floor': str(floor_variance)}
    if q == 0:
        return {'repeats': int(minimum), 'reason': 'zero assumed radius', 'variance_floor': str(floor_variance)}
    threshold = g*g/(4*q*q)
    if threshold <= floor_variance:
        return {'repeats': None, 'reason': 'irreducible next-attempt floor', 'variance_floor': str(floor_variance)}
    count = minimum if s == 0 or n == 0 else max(minimum, floor(n/(threshold-floor_variance)-n/s)+1)
    return {'repeats': int(count), 'reason': 'exact strict scalar inequality', 'variance_floor': str(floor_variance),
            'scope': 'conditional scalar working model with frozen gap and radius; not a field-performance guarantee'}
