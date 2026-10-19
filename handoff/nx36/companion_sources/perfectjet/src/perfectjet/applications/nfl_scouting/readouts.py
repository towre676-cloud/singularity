"""Demand support, identifiability, pooled player readouts, repeatability, and next conditions.

Model: eta_ij = phi(s_ij, a_ij)^T (beta + u_i) + e_ij with phi = (1, s', a', s'a') on
training-standardized demand coordinates, u_i ~ N(0, T), e ~ N(0, sigma^2).

The scouting readout is theta_i = h_q^T (beta + u_i), where h_q averages phi over a
demand distribution q learned from training athletes. Whether a player's own
attempts identify it is decided exactly (perfectjet.readout.identify) on the design
rounded to the declared demand resolution; repeats at one demand are one direction.
When they do not, the pooled posterior still returns a number, and the share of
prior variance it retains (pooling reliance) is reported with it.
"""
from fractions import Fraction
from math import sqrt
from ...readout import identify
from .linalg import inverse, matvec, dot, ridge, mean, pearson, transpose, matmul


class DemandFrame:
    """Standardization of (speed, angle) and the demand distribution, fitted on training events."""

    def __init__(self, events, speed_resolution=0.5, angle_resolution=15.0):
        s = [e.entry_speed for e in events]
        a = [e.turn_angle for e in events]
        self.s0, self.a0 = mean(s), mean(a)
        self.ss = max(1e-6, sqrt(sum((x-self.s0)**2 for x in s)/max(1, len(s)-1)))
        self.sa = max(1e-6, sqrt(sum((x-self.a0)**2 for x in a)/max(1, len(a)-1)))
        self.res = (speed_resolution, angle_resolution)
        cells = {}
        for e in events:
            k = self.cell(e.entry_speed, e.turn_angle)
            cells[k] = cells.get(k, 0)+1
        total = sum(cells.values())
        self.q = {k: v/total for k, v in cells.items()}
        # Keep a separate exact design in *raw* cell coordinates.  Rationalizing
        # standardized floats independently breaks the identity phi_3=phi_1*phi_2
        # and can invent a design direction.  Counts also make h exactly a linear
        # combination of the corresponding rows, as the empirical q requires.
        self.q_exact = {k: Fraction(v, total) for k, v in cells.items()}
        self.h_exact = [sum((w*self.exact_cell_row(k)[j] for k, w in self.q_exact.items()), Fraction(0))
                        for j in range(4)]
        self.h = [sum(w*f for w, f in zip(self.q.values(), col))
                  for col in zip(*[self.phi(*self.center(k)) for k in self.q])]

    def cell(self, s, a):
        return (round(s/self.res[0]), round(a/self.res[1]))

    def center(self, cell):
        return cell[0]*self.res[0], cell[1]*self.res[1]

    def phi(self, s, a):
        x, y = (s-self.s0)/self.ss, (a-self.a0)/self.sa
        return [1.0, x, y, x*y]

    def exact_row(self, s, a):
        """Raw bilinear design at the rounded cell; invertible scaling preserves its row-space test."""
        return self.exact_cell_row(self.cell(s, a))

    def exact_cell_row(self, cell):
        s = cell[0]*Fraction(str(self.res[0]))
        a = cell[1]*Fraction(str(self.res[1]))
        return [Fraction(1), s, a, s*a]

    def support(self, events):
        """Exact bilinear h_q identifiability on rounded raw coordinates, plus demand coverage of q."""
        rows = [self.exact_row(e.entry_speed, e.turn_angle) for e in events]
        full = identify(rows, self.h_exact) if rows else {"identified": False, "witness": None}
        cells = {self.cell(e.entry_speed, e.turn_angle) for e in events}
        covered = sum(w for k, w in self.q.items() if k in cells)
        distinct = len({tuple(r) for r in rows})
        return {"identified": full["identified"], "witness": [str(x) for x in full.get("witness") or []] or None,
                "distinct_demands": distinct, "q_mass_observed": covered}


class PooledModel:
    """Linear mixed model fitted by EM on training athletes only."""

    def __init__(self, frame, events_by_athlete, iterations=40, lam=1.0):
        self.frame = frame
        xs, ys = [], []
        for evs in events_by_athlete.values():
            for e in evs:
                xs.append(frame.phi(e.entry_speed, e.turn_angle))
                ys.append(e.eta)
        self.beta = ridge(xs, ys, lam)
        p = len(self.beta)
        resid = [y-dot(x, self.beta) for x, y in zip(xs, ys)]
        self.sigma2 = max(1e-6, sum(r*r for r in resid)/max(1, len(resid)-p))
        self.T = [0.5*self.sigma2 if i == 0 else 0.1*self.sigma2 for i in range(p)]
        for _ in range(iterations):
            acc_t = [0.0]*p
            acc_s = 0.0
            n = 0
            for evs in events_by_athlete.values():
                m, cov, x, r = self._posterior(evs)
                for k in range(p):
                    acc_t[k] += m[k]**2+cov[k][k]
                fitted = matvec(x, m)
                acc_s += sum((ri-fi)**2 for ri, fi in zip(r, fitted))
                acc_s += sum(dot(row, matvec(cov, row)) for row in x)
                n += len(evs)
            k_ath = max(1, len(events_by_athlete))
            self.T = [max(1e-8, v/k_ath) for v in acc_t]
            self.sigma2 = max(1e-8, acc_s/max(1, n))

    def _posterior(self, evs):
        x = [self.frame.phi(e.entry_speed, e.turn_angle) for e in evs]
        r = [e.eta-dot(row, self.beta) for row, e in zip(x, evs)]
        p = len(self.beta)
        prec = [[(1.0/self.T[i] if i == j else 0.0) for j in range(p)] for i in range(p)]
        for row in x:
            for i in range(p):
                for j in range(p):
                    prec[i][j] += row[i]*row[j]/self.sigma2
        cov = inverse(prec)
        m = matvec(cov, [sum(row[i]*ri for row, ri in zip(x, r))/self.sigma2 for i in range(p)])
        return m, cov, x, r

    def readout(self, evs, h=None):
        h = h or self.frame.h
        prior = dot(h, [t*v for t, v in zip(self.T, h)])
        if not evs:
            return {"theta": dot(h, self.beta), "variance": prior, "pooling_reliance": 1.0, "cov": None}
        m, cov, _, _ = self._posterior(evs)
        var = dot(h, matvec(cov, h))
        return {"theta": dot(h, [b+u for b, u in zip(self.beta, m)]), "variance": var,
                "pooling_reliance": var/prior if prior > 0 else 1.0, "cov": cov}

    def intercept_readout(self, evs):
        """Simplest supported readout: shrunken mean of demand-adjusted eta (random intercept only)."""
        h = self.frame.h
        base = dot(h, self.beta)
        if not evs:
            return {"theta": base, "n": 0}
        dev = [e.eta-dot(self.frame.phi(e.entry_speed, e.turn_angle), self.beta) for e in evs]
        k = self.sigma2/self.T[0]
        return {"theta": base+sum(dev)/(len(dev)+k), "n": len(dev)}

    def next_condition(self, evs, candidates):
        """Variance reduction of theta from one more attempt at each candidate demand, repeat vs new."""
        cur = self.readout(evs)
        if cur["cov"] is None:
            return None
        cov, h = cur["cov"], self.frame.h
        prec = inverse(cov)
        seen = {self.frame.cell(e.entry_speed, e.turn_angle) for e in evs}
        rows = [self.frame.exact_row(e.entry_speed, e.turn_angle) for e in evs]
        from ...readout import adds_direction
        out = []
        for s, a in candidates:
            row = self.frame.phi(s, a)
            new = [[prec[i][j]+row[i]*row[j]/self.sigma2 for j in range(len(row))] for i in range(len(row))]
            after = dot(h, matvec(inverse(new), h))
            out.append({"speed": s, "angle": a, "reduction": cur["variance"]-after,
                        "repeat_of_observed_demand": self.frame.cell(s, a) in seen,
                        "new_design_direction": adds_direction(rows, self.frame.exact_row(s, a)) if rows else True})
        out.sort(key=lambda r: -r["reduction"])
        return out


def split_half(events_by_athlete, fn):
    """Spearman-Brown corrected split-half reliability of a per-athlete readout fn(events)."""
    a, b = [], []
    for evs in events_by_athlete.values():
        if len(evs) < 2:
            continue
        evs = sorted(evs, key=lambda e: e.attempt_id)
        first, second = evs[0::2], evs[1::2]
        a.append(fn(first))
        b.append(fn(second))
    if len(a) < 3:
        return {"athletes": len(a), "split_half": None, "spearman_brown": None}
    r = pearson(a, b)
    return {"athletes": len(a), "split_half": r, "spearman_brown": 2*r/(1+r) if r > -1 else None}


def group(events):
    out = {}
    for e in events:
        out.setdefault(e.athlete_id, []).append(e)
    return out
