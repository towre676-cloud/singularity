"""Identifiable readouts, observation repair, and value of information, in exact arithmetic.

A linear response eta = phi(d)^T beta is observed at the design rows X (one row
phi(d_j) per observed demand d_j). A readout h^T beta is determined by those
observations exactly when h lies in row(X). Otherwise some n has X n = 0 and
h^T n != 0: beta and beta+n fit every observation identically and disagree on
the readout. That vector is returned as the witness.

Repair asks which additional demand rows make h identifiable; a repeat of an
existing direction can sharpen precision but can never cure non-identifiability.
Value of information is the exact reduction of the Gaussian posterior variance of
h^T beta; for a linear Gaussian model it does not depend on the unseen outcome.
"""
from fractions import Fraction as Q
from itertools import combinations
from .exact import matrix, rref, nullspace, rank, transpose, matmul


def dot(u, v):
    return sum((Q(a)*Q(b) for a, b in zip(u, v)), Q(0))


def identify(design, h):
    """Exact decision h in row(X): estimator weights, or a two-fit witness."""
    x = matrix(design)
    h = [Q(v) for v in h]
    n = len(h)
    if x and len(x[0]) != n:
        raise ValueError("readout length differs from design width")
    for v in nullspace(x, n) if x else [[Q(int(i == j)) for i in range(n)] for j in range(n)]:
        shift = dot(h, v)
        if shift:
            return {"identified": False, "witness": v, "readout_shift": shift,
                    "explanation": "X n = 0 but h.n != 0: beta and beta+n fit every observation"}
    # Solve X^T c = h for the estimator weights c (any solution works).
    xt = transpose(x)
    aug = [row+[hv] for row, hv in zip(xt, h)]
    rr, piv = rref(aug, len(x)+1)
    c = [Q(0)]*len(x)
    for i, p in enumerate(piv):
        c[p] = rr[i][-1]
    assert all(dot([row[k] for row in x], c) == h[k] for k in range(n))
    return {"identified": True, "weights": c}


def demand_readout(features, demands):
    """h_q = sum_k q_k phi(d_k) for a finite demand distribution [(weight, demand), ...]."""
    total = sum((Q(w) for w, _ in demands), Q(0))
    if total <= 0:
        raise ValueError("demand weights must have positive total")
    vecs = [(Q(w)/total, [Q(v) for v in features(d)]) for w, d in demands]
    return [sum((w*v[i] for w, v in vecs), Q(0)) for i in range(len(vecs[0][1]))]


def adds_direction(design, row):
    """True when row is outside row(X): a genuinely new condition, not a repeat."""
    x = matrix(design)
    return rank(x+[list(row)], len(row)) > (rank(x, len(row)) if x else 0)


def repair(design, h, candidates, max_new=3):
    """Smallest set of candidate rows making h identifiable, with the failure count of smaller sets."""
    if identify(design, h)["identified"]:
        return {"needed": 0, "rows": [], "smaller_sets_rejected": 0}
    rejected = 0
    for k in range(1, max_new+1):
        for idx in combinations(range(len(candidates)), k):
            if identify(list(design)+[candidates[i] for i in idx], h)["identified"]:
                return {"needed": k, "rows": list(idx), "smaller_sets_rejected": rejected}
            rejected += 1
    return {"needed": None, "rows": None, "smaller_sets_rejected": rejected}


def inverse(a):
    a = matrix(a)
    n = len(a)
    aug = [row+[Q(int(i == j)) for j in range(n)] for i, row in enumerate(a)]
    rr, piv = rref(aug, 2*n)
    if piv[:n] != list(range(n)):
        raise ZeroDivisionError("singular matrix")
    return [row[n:] for row in rr[:n]]


def posterior_covariance(design, noise_variance, prior_covariance):
    """(Sigma0^{-1} + X^T X / s^2)^{-1} for y = X beta + e, e ~ N(0, s^2 I), beta ~ N(m, Sigma0)."""
    p = inverse(prior_covariance)
    x = matrix(design)
    if x:
        xtx = matmul(transpose(x), x)
        p = [[a+b/Q(noise_variance) for a, b in zip(r1, r2)] for r1, r2 in zip(p, xtx)]
    return inverse(p)


def readout_variance(cov, h):
    return dot(h, [dot(row, h) for row in cov])


def value_of_information(design, h, candidates, noise_variance, prior_covariance):
    """Exact posterior-variance reduction of h^T beta from each candidate condition."""
    before = readout_variance(posterior_covariance(design, noise_variance, prior_covariance), h)
    structural = identify(design, h)["identified"] if design else False
    out = []
    for i, row in enumerate(candidates):
        after = readout_variance(posterior_covariance(list(design)+[row], noise_variance, prior_covariance), h)
        out.append({"candidate": i, "variance_after": after, "reduction": before-after,
                    "new_direction": adds_direction(design, row) if design else True,
                    "resolves_identification": (not structural) and identify(list(design)+[row], h)["identified"]})
    out.sort(key=lambda r: (-r["reduction"], r["candidate"]))
    return {"variance_before": before, "identified_by_data_alone": structural, "candidates": out}


def pooling_reliance(design, h, noise_variance, prior_covariance):
    """Share of the readout's prior variance that the player's own data fail to remove (0..1)."""
    prior = readout_variance(prior_covariance, h)
    post = readout_variance(posterior_covariance(design, noise_variance, prior_covariance), h)
    return post/prior if prior else Q(0)


def readout_receipt():
    phi = lambda d: (1, d[0], d[1], d[0]*d[1])
    # One player's attempts all sit at a single entry speed: the s*a and s directions collapse.
    attempts = [phi((Q(5), Q(a))) for a in (30, 60, 90)]
    demands = [(1, (Q(4), Q(45))), (1, (Q(6), Q(90)))]
    h = demand_readout(phi, demands)
    ident = identify(attempts, h)
    candidates = [phi((Q(5), Q(120))), phi((Q(7), Q(60))), phi((Q(7), Q(120))), phi((Q(5), Q(30)))]
    fix = repair(attempts, h, candidates)
    voi = value_of_information(attempts, h, candidates, Q(1), [[Q(int(i == j))*4 for j in range(4)] for i in range(4)])
    supported = identify(attempts, demand_readout(phi, [(1, (Q(5), Q(45))), (1, (Q(5), Q(75)))]))
    return {"model": "eta = b0 + b1 s + b2 a + b3 s a",
            "unsupported_readout": {"identified": ident["identified"], "witness": ident.get("witness"),
                                    "readout_shift": ident.get("readout_shift")},
            "supported_readout_identified": supported["identified"],
            "repair": fix, "value_of_information": voi}
