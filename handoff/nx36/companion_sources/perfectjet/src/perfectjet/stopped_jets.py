"""Exact position readouts after an observed speed landmark.

The landmark does not identify an unseen launch time. Conditional on a fixed
window, these contrasts remove unknown position and constant-velocity drift.
Noise formulae condition on that window; they exclude data-dependent gate noise.
"""
from __future__ import annotations
from fractions import Fraction as Q
from math import factorial
from .exact import matmul, transpose, rank
from .readout import dot, identify, inverse


def _times(times):
    t = tuple(Q(v) for v in times)
    if len(t) < 2 or any(b <= a for a, b in zip(t, t[1:])):
        raise ValueError('need at least two strictly increasing rational times')
    return tuple(v-t[0] for v in t)


def signature_area_weights(times):
    """A_tx = (T/2)(x_T-x_0) - integral(x-x_0) for the PL path.

    Equals half the antisymmetric level-two time/position signature. Translation
    and constant-velocity drift vanish exactly. Returned weights act on x itself.
    """
    t = _times(times)
    w = [Q(0)] * len(t)
    w[0] += t[-1]/2
    w[-1] += t[-1]/2
    for i in range(len(t)-1):
        dt = t[i+1]-t[i]
        w[i] -= dt/2
        w[i+1] -= dt/2
    assert sum(w) == 0 and dot(w, t) == 0
    return tuple(w)


def area_acceleration_weights(times):
    """Finite-grid normalization exact on x=x0+v0*t+a*t^2/2.

    On a continuous twice differentiable path, 12*A/T^3 is the acceleration
    average with positive kernel 6*t*(T-t)/T^3. For a sampled quadratic, replace
    T^3 by T^3-sum(dt^3). This corrects trapezoidal interpolation, not all noise.
    """
    t = _times(times)
    denominator = t[-1]**3-sum((b-a)**3 for a,b in zip(t,t[1:]))
    if denominator == 0:
        raise ValueError('two positions cannot identify acceleration')
    w = tuple(12*v/denominator for v in signature_area_weights(t))
    assert dot(w, [v*v/2 for v in t]) == 1
    return w


def minimum_variance_jet(times, derivative=2, degree=3, covariance=None):
    """Exact BLUE for a polynomial derivative at the window midpoint.

    Returns an explicit hidden polynomial when the readout is not identifiable.
    ``covariance`` is a fixed symmetric positive-definite position-noise matrix;
    default identity. It is an assumption, never an inferred tracking precision.
    """
    t = _times(times)
    if not isinstance(degree,int) or degree < 0 or not isinstance(derivative,int) or not 0 <= derivative <= degree:
        raise ValueError('need integer 0 <= derivative <= degree')
    center = (t[0]+t[-1])/2
    design = [[(v-center)**k/Q(factorial(k)) for k in range(degree+1)] for v in t]
    h = [Q(int(k==derivative)) for k in range(degree+1)]
    identification = identify(design,h)
    if not identification['identified']:
        return {**identification, 'design':design, 'readout':h}
    n = len(t)
    cov = [[Q(int(i==j)) for j in range(n)] for i in range(n)] if covariance is None else [[Q(v) for v in row] for row in covariance]
    if len(cov)!=n or any(len(r)!=n for r in cov) or cov!=transpose(cov):
        raise ValueError('covariance must be symmetric with one row per position')
    # Exact LDL positivity via Schur complements, without a floating eigen test.
    schur = [r[:] for r in cov]
    for i in range(n):
        if schur[i][i] <= 0:
            raise ValueError('covariance must be positive definite')
        for j in range(i+1,n):
            for k in range(i+1,n):
                schur[j][k] -= schur[j][i]*schur[i][k]/schur[i][i]
    # Remove dependent polynomial constraints. This also handles an identifiable
    # readout in a rank-deficient model without declaring all coefficients known.
    cols=[]; current=[]
    for k,row in enumerate(transpose(design)):
        if rank(current+[row]) > len(current):
            current.append(row); cols.append(k)
    # If a column is dependent, the right-hand side is consistent by identify.
    x = transpose(current)
    ci = inverse(cov)
    left = matmul(ci,x)
    gram = matmul(transpose(x),left)
    coeff = [dot(row,[h[k] for k in cols]) for row in inverse(gram)]
    weights = [dot(row,coeff) for row in left]
    assert [dot(weights,col) for col in transpose(design)] == h
    variance = dot(weights,[dot(row,weights) for row in cov])
    return {'identified':True,'weights':tuple(weights),'variance':variance,
            'design':design,'readout':h,'center':center,'degree':degree,
            'derivative':derivative,'noise_scope':'fixed window and specified covariance; gate selection excluded'}


def derivative_remainder_bound(times, weights, degree, derivative_bound):
    """Taylor bound with |x^(degree+1)| <= derivative_bound on the window."""
    t = _times(times)
    if len(t)!=len(weights) or degree<0 or Q(derivative_bound)<0:
        raise ValueError('incompatible weights or negative degree/bound')
    center = t[-1]/2
    return Q(derivative_bound)*sum(abs(Q(w))*abs(v-center)**(degree+1) for w,v in zip(weights,t))/factorial(degree+1)


def ordered_area(increments):
    """Streaming exact Chen product for (dt,dx); swaps can change the area."""
    time = displacement = twice_area = Q(0)
    for dt,dx in increments:
        dt,dx = Q(dt),Q(dx)
        if dt <= 0:
            raise ValueError('positive time increments required')
        twice_area += time*dx-displacement*dt
        time += dt; displacement += dx
    return twice_area/2


def readout_receipt():
    times = [Q(i,10) for i in range(6)]
    area = area_acceleration_weights(times)
    blue = minimum_variance_jet(times,2,3)
    jerk = minimum_variance_jet(times,3,3)
    naive = [Q(100),Q(-200),Q(100)]
    noise = dot(area,area)
    return {'schema':'perfectjet/stopped-jet-identities/1',
        'times_seconds':times,'area_acceleration_weights':area,
        'minimum_variance_acceleration':blue,'minimum_variance_jerk':jerk,
        'area_noise_variance_multiplier':noise,
        'naive_second_difference_variance_multiplier':dot(naive,naive),
        'area_vs_naive_variance_ratio':noise/dot(naive,naive),
        'blue_vs_naive_variance_ratio':blue['variance']/dot(naive,naive),
        'ordering_example':{'first':ordered_area([(1,1),(1,3)]),
                            'reversed':ordered_area([(1,3),(1,1)])},
        'unobserved_launch_time':'not identified by in-motion positions without additional assumptions',
        'scope':'exact finite algebra; variance ratios assume independent equal-variance position errors and fixed windows; not empirical NFL precision or scouting gains'}
