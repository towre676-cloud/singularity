"""Exact orbit-count dimension of the Fourier/chirp commutant.

Convention (as in the repository): F[x,y] = zeta_N^(x*y), T = diag(zeta_N^(x*x)).
Conjugation by F and T permutes the Heisenberg basis E[s,t] = Z_t X_s up to
powers of zeta_N:

    F E[s,t] F^-1 = zeta^(s*t)  E[-t, s]
    T E[s,t] T^-1 = zeta^(-s*s) E[s, t+2s]

The commutant is the fixed space of this monomial action.  Its dimension is the
number of orbits on (Z/N)^2 that admit a consistent phase labelling.  All
arithmetic is exact integer arithmetic modulo N; standard library only.
execution_verified is False, as for every Python packet in this repository.
"""
from math import gcd


def _positive(n):
    if type(n) is not int or n < 1:
        raise ValueError("level must be a positive integer")


def tau(n):
    _positive(n)
    r, p = 1, 2
    while n > 1:
        e = 0
        while n % p == 0:
            n //= p
            e += 1
        r *= e + 1
        p += 1
    return r


def closed_form(N):
    """Proved dimension: tau(N) for odd N, (2a-1)*tau(m) for N = 2^a * m, a >= 1."""
    _positive(N)
    a, m = 0, N
    while m % 2 == 0:
        m //= 2
        a += 1
    return tau(m) * (1 if a == 0 else 2 * a - 1)


def labelled_orbits(N, *, cell_limit=2_000_000):
    """Exact spanning-tree phases, including inconsistent (dead) orbits.

    The cell limit bounds the quadratic traversal before allocation. A dead
    orbit's tree labels are not an invariant vector; never use them as a basis.
    """
    _positive(N)
    if type(cell_limit) is not int or cell_limit < 1:
        raise ValueError("cell_limit must be a positive integer")
    if N * N > cell_limit:
        raise ValueError("orbit traversal exceeds cell_limit")
    def act_T(w):
        s, t = w
        return (s, (t + 2 * s) % N), (-s * s) % N

    def act_F(w):
        s, t = w
        return ((-t) % N, s), (t * s) % N

    seen = set()
    out = []
    for s0 in range(N):
        for t0 in range(N):
            if (s0, t0) in seen:
                continue
            label = {(s0, t0): 0}
            stack = [(s0, t0)]
            ok = True
            while stack:
                w = stack.pop()
                for g in (act_T, act_F):
                    w2, ph = g(w)
                    v = (label[w] + ph) % N
                    if w2 in label:
                        if label[w2] != v:
                            ok = False
                    else:
                        label[w2] = v
                        stack.append(w2)
            seen.update(label)
            out.append((label, ok))
    return out


def orbit_census(N, *, cell_limit=2_000_000):
    """Return (representative, orbit_size, survives, content) for every orbit."""
    return [(next(iter(label)), len(label), ok,
             gcd(gcd(*next(iter(label))), N))
            for label, ok in labelled_orbits(N, cell_limit=cell_limit)]


def commutant_dimension(N):
    return sum(1 for _, _, ok, _ in orbit_census(N) if ok)


def orbit_basis(N, *, cell_limit=2_000_000):
    """Sparse orbit sums: (s,t) -> exponent of the coefficient of E[s,t]."""
    return [label for label, ok in labelled_orbits(N, cell_limit=cell_limit) if ok]


def transpose_fixed(N, label):
    """Check the exact E[s,t]^transpose = zeta^(s*t) E[-s,t] identity.

    This verifies support as well as phase, without floating point or assuming
    a closed-form dimension. All coefficients in these sparse vectors are roots.
    """
    return all(((-s) % N, t) in label and
               (e + s * t - label[((-s) % N, t)]) % N == 0
               for (s, t), e in label.items())


def exact_orbit_certificate(level, *, cell_limit=2_000_000):
    """Finite exact evidence; the all-level theorem is a separate paper proof."""
    N = level
    records = []
    for label, ok in labelled_orbits(N, cell_limit=cell_limit):
        s, t = next(iter(label))
        support_expected = N % 2 == 1 or (s % 2 == 0 and t % 2 == 0)
        symmetric = transpose_fixed(N, label) if ok else None
        if ok != support_expected or (ok and not symmetric):
            raise AssertionError("orbit support or transpose theorem failed")
        records.append({"representative": [s, t], "size": len(label),
                        "survives": ok, "transpose_fixed": symmetric})
    dimension = sum(r["survives"] for r in records)
    if dimension != closed_form(N):
        raise AssertionError("dimension formula failed")
    return {"schema": "pp-weil-orbit/1", "level": N, "dimension": dimension,
            "orbits": records, "all_surviving_orbits_transpose_fixed": True,
            "exact_arithmetic": True, "execution_verified": False,
            "scope": "finite phase traversal and transpose check; all-level paper theorem"}


def exact_products_commute(N, *, pair_limit=2_000_000):
    """Independent small-level twisted-convolution check in Q[zeta_N].

    E[s,t] E[u,v] = zeta^(-s*v) E[s+u,t+v]. Products are collected as
    integer polynomials then reduced modulo Phi_N. No matrix SVD is used.
    """
    from .branched_geometry import cyclotomic
    from .weil_commutant import _remainder
    basis = orbit_basis(N)
    work = sum(len(a) * len(b) for i, a in enumerate(basis) for b in basis[i+1:])
    if type(pair_limit) is not int or pair_limit < 1 or work > pair_limit:
        raise ValueError("twisted convolution exceeds pair_limit")
    modulus = cyclotomic(N)
    for i, left in enumerate(basis):
        for right in basis[i+1:]:
            difference = {}
            for (s, t), e in left.items():
                for (u, v), f in right.items():
                    target = ((s + u) % N, (t + v) % N)
                    poly = difference.setdefault(target, [0] * N)
                    poly[(e + f - s * v) % N] += 1
                    poly[(e + f - u * t) % N] -= 1
            if any(any(_remainder(poly, modulus)) for poly in difference.values()):
                return False
    return True
