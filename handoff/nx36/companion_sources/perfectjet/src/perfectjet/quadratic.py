"""Solution-carrying compiler for k y^2 = a n^2 + b n + c over the integers.

The equation is transported to a norm equation and every step keeps its way back:

    X = 2 a n + b,  Y = y,  X^2 - D Y^2 = N0,  D = 4 a k,  N0 = b^2 - 4 a c,
    n = (X - b) / (2 a)  (requires X = b mod 2a).

Branches, each with its own completeness status:
- a = 0: k y^2 = b n + c is a congruence on y; the solutions are residue classes.
- D = 0 or D < 0 or D a perfect square: finitely many (X, Y), from divisor pairs
  or a bounded box; complete.
- D > 0 not a square, N0 != 0: a generalized Pell equation. Nagell's bounds give
  every class representative, so seeds times powers of the fundamental unit are all
  solutions; admissibility X = b mod 2a is periodic along each orbit.
- N0 = 0 with D nonsquare: only X = Y = 0.

The compiled population answers counts below a bound, the k-th solution at remote
indices, and its growth rate, and every returned n is replayed in the original
equation.
"""
from fractions import Fraction as Q
from math import isqrt, gcd, log, log1p, sqrt


def is_square(n):
    return n >= 0 and isqrt(n)**2 == n


def fundamental_unit(d):
    """Smallest x1 > 1, y1 > 0 with x1^2 - d y1^2 = 1 (continued fraction of sqrt d)."""
    a0 = isqrt(d)
    if a0*a0 == d:
        raise ValueError("d is a square")
    m, q, a = 0, 1, a0
    p_prev, p = 1, a0
    s_prev, s = 0, 1
    while p*p-d*s*s != 1:
        m = q*a-m
        q = (d-m*m)//q
        a = (a0+m)//q
        p_prev, p = p, a*p+p_prev
        s_prev, s = s, a*s+s_prev
    return p, s


def nagell_seeds(d, n0, cap=10**6):
    """Class representatives of x^2 - d y^2 = n0 (d > 0 nonsquare, n0 != 0), with x >= 0."""
    x1, y1 = fundamental_unit(d)
    if n0 > 0:
        lo, hi2_num, hi2_den = 0, y1*y1*n0, 2*(x1+1)
    else:
        lo, hi2_num, hi2_den = 1, y1*y1*(-n0), 2*(x1-1)
    hi = isqrt(hi2_num//hi2_den)+1
    if hi-lo > cap:
        return None, (x1, y1), hi
    seeds = []
    for y in range(lo, hi+1):
        if y*y*hi2_den > hi2_num:
            break
        t = n0+d*y*y
        if is_square(t):
            x = isqrt(t)
            seeds.append((x, y))
    return seeds, (x1, y1), hi


def _mul(p, q, d):
    return (p[0]*q[0]+d*p[1]*q[1], p[0]*q[1]+p[1]*q[0])


def _embedding_sign(point, d):
    """Exact sign of x+y*sqrt(d), with d positive and nonsquare."""
    x, y = point
    if y == 0:return (x > 0)-(x < 0)
    if x == 0:return (y > 0)-(y < 0)
    if x > 0 and y > 0:return 1
    if x < 0 and y < 0:return -1
    comparison = (x*x > d*y*y)-(x*x < d*y*y)
    return comparison if x > 0 else -comparison


def _positive_unit_representative(point, unit, d):
    """Unique representative with 1 <= x+y sqrt(d) < epsilon.

    Only a positive real embedding is accepted. Equality is decided by integer
    comparisons, so conjugate/end-point representatives are deduplicated exactly.
    """
    if _embedding_sign(point, d) <= 0:
        raise ValueError("a positive real embedding is required")
    cur = point
    while _embedding_sign((cur[0]-1, cur[1]), d) < 0:
        cur = _mul(cur, unit, d)
    inverse = (unit[0], -unit[1])
    while _embedding_sign((cur[0]-unit[0], cur[1]-unit[1]), d) >= 0:
        cur = _mul(cur, inverse, d)
    return cur


def pell_solutions(d, n0, xmax):
    """All (X, Y) with X^2 - d Y^2 = n0 and |X| <= xmax, from Nagell seeds and the unit."""
    seeds, unit, bound = nagell_seeds(d, n0)
    if seeds is None:
        raise OverflowError(f"Nagell search range {bound} exceeds the cap")
    inv = (unit[0], -unit[1])
    out = set()
    for x, y in seeds:
        for sx in (1, -1):
            for sy in (1, -1):
                start = (sx*x, sy*y)
                for step in (unit, inv):
                    cur = start
                    passed_min = False
                    prev = abs(cur[0])
                    for _ in range(10000):
                        if abs(cur[0]) <= xmax:
                            out.add(cur)
                        nxt = _mul(cur, step, d)
                        if abs(nxt[0]) > xmax and (passed_min or abs(nxt[0]) >= prev):
                            break
                        passed_min = passed_min or abs(nxt[0]) > prev
                        prev = abs(nxt[0])
                        cur = nxt
    return sorted(out), seeds, unit


class QuadraticSquare:
    """Compile k y^2 = a n^2 + b n + c (integers, k > 0) into a navigable solution population."""

    def __init__(self, k, a, b, c):
        if any(type(v) is not int for v in (k, a, b, c)):
            raise ValueError("integer coefficients are required")
        if k <= 0:
            raise ValueError("k must be positive")
        self.k, self.a, self.b, self.c = k, a, b, c
        self.d = 4*a*k
        self.n0 = b*b-4*a*c
        if a == 0:
            self.branch = "linear"
        elif self.d < 0 or is_square(self.d) or self.n0 == 0:
            self.branch = "finite" if self.n0 != 0 or self.d < 0 else "degenerate_square"
        else:
            self.branch = "pell"
        if self.branch == "degenerate_square" and not is_square(self.d):
            self.branch = "finite"

    def F(self, n):
        return self.a*n*n+self.b*n+self.c

    def holds(self, n, y):
        return self.k*y*y == self.F(n)

    def y_of(self, n):
        v = self.F(n)
        if v < 0 or v % self.k:
            return None
        q = v//self.k
        return isqrt(q) if is_square(q) else None

    # ------------------------------------------------------------- branches

    def _linear_residues(self):
        """a = 0: k y^2 = b n + c. n is integral iff k y^2 = c mod |b|; periodic in y mod |b|."""
        b = abs(self.b)
        if b == 0:
            return None
        return [r for r in range(b) if (self.k*r*r-self.c) % b == 0]

    def hits(self, nmax, nmin=0):
        """Sorted n in [nmin, nmax] with F(n) = k y^2, each replayed."""
        out = set()
        if self.branch == "linear":
            if self.b == 0:
                if self.c >= 0 and self.c % self.k == 0 and is_square(self.c//self.k):
                    out = set(range(nmin, nmax+1))
            else:
                res = self._linear_residues()
                vals = [self.b*nmin+self.c, self.b*nmax+self.c]
                ymax = isqrt(max(0, max(vals))//self.k)+1
                for y in range(0, ymax+1):
                    if y % abs(self.b) not in res:
                        continue
                    num = self.k*y*y-self.c
                    if num % self.b == 0 and nmin <= num//self.b <= nmax:
                        out.add(num//self.b)
        else:
            xs = [2*self.a*nmin+self.b, 2*self.a*nmax+self.b]
            xmax = max(abs(v) for v in xs)
            for X, _ in self._norm_solutions(xmax):
                if (X-self.b) % (2*self.a) == 0:
                    n = (X-self.b)//(2*self.a)
                    if nmin <= n <= nmax:
                        out.add(n)
        result = sorted(out)
        for n in result:
            assert self.y_of(n) is not None, n
        return result

    def _norm_solutions(self, xmax):
        d, n0 = self.d, self.n0
        if self.branch == "pell":
            return pell_solutions(d, n0, xmax)[0]
        if d < 0:
            # Positive definite: |X| <= sqrt(n0), |Y| <= sqrt(n0/|d|).
            if n0 < 0:
                return []
            out = []
            ymax = isqrt(n0//-d)+1
            for y in range(-ymax, ymax+1):
                t = n0+d*y*y
                if t >= 0 and is_square(t):
                    out += [(isqrt(t), y), (-isqrt(t), y)]
            return out
        if is_square(d):
            s = isqrt(d)
            if n0 == 0:
                # (X - sY)(X + sY) = 0: two lines X = +/- s Y.
                return [(x, y) for x in range(-xmax, xmax+1) for y in {x//s, -(x//s)} if s and x % s == 0 and x*x == d*y*y]
            out = []
            for u in _divisors(abs(n0)):
                for su in (1, -1):
                    p = su*u
                    q = n0//p
                    # X - sY = p, X + sY = q.
                    if (p+q) % 2 == 0 and (q-p) % (2*s) == 0:
                        out.append(((p+q)//2, (q-p)//(2*s)))
            return out
        # d > 0 nonsquare, n0 == 0: only (0, 0).
        return [(0, 0)]

    # --------------------------------------------------------- populations

    def orbit_structure(self):
        """Signed seeds plus distinct positive tails and their logarithmic weight.

        Raw signed seeds remain available for two-sided orbit navigation. They
        are not separate populations of n >= 0. Positive real embeddings are
        reduced modulo the unit to [1, epsilon), then deduplicated. Each class
        has Y > 0 and X > 0 eventually, so it contributes one distinct positive
        n for each admissible exponent. The other sign of Y adds no n values.
        """
        if self.branch != "pell":
            return None
        seeds, unit, bound = nagell_seeds(self.d, self.n0)
        if seeds is None:
            raise OverflowError(f"Nagell search range {bound} exceeds the cap")
        m = 2*abs(self.a)
        orbits, positive = [], set()

        def residue_orbit(start):
            # A norm-one unit is invertible modulo m: every orbit is a cycle.
            cur, residues, seen = (start[0] % m, start[1] % m), [], {}
            while cur not in seen:
                seen[cur] = len(residues)
                residues.append((cur[0]-self.b) % m == 0)
                X, Y = _mul(cur, unit, self.d)
                cur = X % m, Y % m
            pre = seen[cur]
            assert pre == 0
            return {"seed": start, "preperiod": pre, "period": len(residues),
                    "admissible": [i for i, ok in enumerate(residues) if ok]}

        for x, y in seeds:
            for sx, sy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
                start = (sx*x, sy*y)
                orbit = residue_orbit(start)
                orbit["positive_forward_embedding"] = _embedding_sign(start, self.d) > 0
                orbits.append(orbit)
                if orbit["positive_forward_embedding"]:
                    positive.add(_positive_unit_representative(start, unit, self.d))
        positive_orbits = [residue_orbit(p) for p in sorted(positive)]
        weight = sum((Q(len(o["admissible"]), o["period"]) for o in positive_orbits), Q(0))
        # epsilon=u+sqrt(u^2-1). This form avoids converting a huge unit to float.
        unit_log = log(unit[0])+log1p(sqrt(1-1/(unit[0]*unit[0])))
        asymptotic = {
            "domain": "distinct integers n >= 0; the two signs of y are identified",
            "form": "A(N) = c log N + O(1)" if weight else "A(N) = O(1)",
            "logarithmic_weight": str(weight),
            "weight_numerator": weight.numerator, "weight_denominator": weight.denominator,
            "unit_log": unit_log, "coefficient": float(weight)/unit_log,
            "coefficient_expression": f"({weight}) / log({unit[0]} + {unit[1]} sqrt({self.d}))",
            "normalization": "positive real unit classes, reduced to [1, epsilon), with duplicate classes removed",
            "positive_unit_classes": len(positive_orbits),
            "infinite_positive_classes": sum(bool(o["admissible"]) for o in positive_orbits),
        }
        return {"unit": unit, "seeds": seeds, "nagell_bound": bound, "modulus": m, "orbits": orbits,
                "positive_orbits": positive_orbits, "asymptotic": asymptotic,
                "growth": (f"A(N) = ({asymptotic['coefficient_expression']}) log N + O(1); "
                           "counts distinct n >= 0") if weight else "A(N) = O(1): no admissible positive unit class"}

    def nth_on_orbit(self, orbit, j):
        """The j-th admissible n (j >= 0) on an orbit going up from its seed, exact at remote indices."""
        if type(j) is not int or j < 0:
            raise ValueError("orbit index must be a nonnegative integer")
        adm, period, pre = orbit["admissible"], orbit["period"], orbit["preperiod"]
        cyc = [i for i in adm if i >= pre]
        if not cyc:
            return None
        q, r = divmod(j, len(cyc))
        power = cyc[r]+q*period
        unit = self.orbit_structure()["unit"]
        p, base, e = (1, 0), unit, power
        while e:
            if e & 1:
                p = _mul(p, base, self.d)
            base = _mul(base, base, self.d)
            e >>= 1
        X, Y = _mul(orbit["seed"], p, self.d)
        n = (X-self.b)//(2*self.a)
        assert (X-self.b) % (2*self.a) == 0 and self.k*Y*Y == self.F(n)
        return n, abs(Y)

    def report(self, nmax=10**6):
        from .engine import report
        hits = self.hits(nmax)
        rep = {"kind": f"{self.branch} branch", "transport": "X=2an+b, Y=y, X^2-DY^2=N0",
               "D": self.d, "N0": self.n0}
        obligations, answer, nxt = [], {"hits_up_to_bound": len(hits), "first_hits": hits[:10]}, None
        if self.branch == "pell":
            st = self.orbit_structure()
            rep.update({"unit": st["unit"], "seeds": st["seeds"], "modulus": st["modulus"],
                        "orbits": [{k: v for k, v in o.items()} for o in st["orbits"]],
                        "positive_orbits": st["positive_orbits"]})
            answer["growth"] = st["growth"]
            answer["asymptotic"] = st["asymptotic"]
            complete = "complete: Nagell bound covers every class"
        elif self.branch == "linear":
            rep["y_residues_mod_b"] = self._linear_residues()
            complete = "complete: residue classes of y"
        else:
            complete = "complete: finite norm equation"
        return report(f"find all integers n >= 0 with {self.k} y^2 = {self.a} n^2 + {self.b} n + {self.c}",
                      rep, ["every hit and its y", "hit counts below any bound", "hits at remote indices"],
                      [{"equation": "(2an+b)^2 - 4ak y^2 = b^2 - 4ac", "replayed": True},
                       {"equation": "n = (X-b)/(2a) with X = b mod 2a", "replayed": True}],
                      answer=dict(answer, completeness=complete), obligations=obligations, next_step=nxt)


def _divisors(n):
    small = [x for x in range(1, isqrt(n)+1) if n % x == 0]
    return sorted(set(small+[n//x for x in small]))


def quadratic_receipt():
    pell7 = QuadraticSquare(2, 1, 0, 7)  # n^2 + 7 = 2 y^2
    st = pell7.orbit_structure()
    remote = [r for r in (pell7.nth_on_orbit(o, 1000) for o in st["orbits"] if o["admissible"]) if r and r[0] >= 0]
    tri = QuadraticSquare(1, 8, 8, 1)  # (2y)^2... y^2 = 8n^2+8n+1: triangular-square numbers
    return {"pell7": pell7.report(10**12)["answer"], "pell7_orbits": st["orbits"],
            "pell7_remote_index_1000": sorted({(len(str(n)), str(n)[:12], pell7.holds(n, y)) for n, y in remote}),
            "square_triangular": tri.report(10**15)["answer"],
            "finite_branch": QuadraticSquare(1, 1, 0, 5).report(10**6)["answer"],
            "linear_branch": QuadraticSquare(1, 0, 3, 1).report(200)["answer"]}
