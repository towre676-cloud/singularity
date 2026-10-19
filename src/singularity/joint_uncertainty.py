"""Exact bounded zonotope geometry for persistent and reset-local nuisance.

No floating optimization is used. Fourier--Motzkin elimination is complete
when its explicit row budget is not exhausted. A refusal is never a verdict.
"""
from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations
from math import gcd, lcm
from hashlib import sha256


def _q(x):
    if isinstance(x, bool) or not isinstance(x, (int, Fraction)):
        raise TypeError("exact int or Fraction required")
    return Fraction(x)


def _dot(a, b):
    return sum((x*y for x, y in zip(a, b)), Fraction(0))


class GeometryBudgetExceeded(ValueError):
    """The exact feasibility computation was not completed."""


def rational_feasibility(inequalities, dimension, *, max_rows=20000):
    """Solve ``a*z <= b`` exactly, returning a point or a Farkas vector.

    The latter consists of nonnegative multipliers on the input rows, whose
    weighted left side is zero and weighted right side is negative. Dimension
    zero and unbounded feasible regions are supported. Back substitution picks
    zero whenever possible. All generated rational rows are normalized.
    """
    if isinstance(dimension, bool) or not isinstance(dimension, int) or dimension < 0:
        raise ValueError("nonnegative integer dimension required")
    if isinstance(max_rows, bool) or not isinstance(max_rows, int) or max_rows < 1:
        raise ValueError("positive integer row budget required")
    original = tuple((tuple(_q(x) for x in a), _q(b)) for a, b in inequalities)
    if any(len(a) != dimension for a, _ in original):
        raise ValueError("inequality dimension mismatch")
    count = len(original)
    if count > max_rows:
        raise GeometryBudgetExceeded("initial rows exceed max_rows")
    rows = [(a, b, tuple(Fraction(int(i == j)) for j in range(count)))
            for i, (a, b) in enumerate(original)]
    stages = []
    generated = count

    def clean(source):
        out = {}
        for a, b, cert in source:
            if not any(a):
                if b < 0:
                    return None, cert
                continue
            scale = 1 / abs(next(x for x in a if x))
            a, b, cert = (tuple(x*scale for x in a), b*scale,
                          tuple(x*scale for x in cert))
            if a not in out or b < out[a][0]:
                out[a] = (b, cert)
        return [(a, b, c) for a, (b, c) in out.items()], None

    rows, contradiction = clean(rows)
    if contradiction is not None:
        return {"feasible": False, "multipliers": contradiction, "generated_rows": generated}
    for size in range(dimension, 0, -1):
        stages.append(rows)
        positive = [r for r in rows if r[0][-1] > 0]
        negative = [r for r in rows if r[0][-1] < 0]
        zeros = [(a[:-1], b, c) for a, b, c in rows if not a[-1]]
        generated += len(positive)*len(negative)
        if generated > max_rows:
            raise GeometryBudgetExceeded("Fourier--Motzkin generated rows exceed max_rows")
        new = list(zeros)
        for a, b, c in positive:
            for aa, bb, cc in negative:
                p, n = a[-1], -aa[-1]
                new.append((tuple(n*x+p*y for x, y in zip(a[:-1], aa[:-1])),
                            n*b+p*bb, tuple(n*x+p*y for x, y in zip(c, cc))))
        rows, contradiction = clean(new)
        if contradiction is not None:
            return {"feasible": False, "multipliers": contradiction,
                    "generated_rows": generated}
    point = []
    for rows in reversed(stages):
        lower, upper = None, None
        for a, b, _ in rows:
            residual = b-_dot(a[:-1], point)
            if a[-1] > 0:
                value = residual/a[-1]
                upper = value if upper is None else min(upper, value)
            elif a[-1] < 0:
                value = residual/a[-1]
                lower = value if lower is None else max(lower, value)
        value = Fraction(0)
        if lower is not None:
            value = max(value, lower)
        if upper is not None:
            value = min(value, upper)
        point.append(value)
    if any(_dot(a, point) > b for a, b in original):
        raise ArithmeticError("feasibility replay failed")
    return {"feasible": True, "point": tuple(point), "generated_rows": generated}


@dataclass(frozen=True)
class JointObservationFamily:
    """Candidate-major centers and generator matrices with shared columns.

    ``generators[c][e][j]`` is the contribution of nuisance j to experiment e
    in candidate c's possible world. Different candidates have independent
    latent vectors, even when their source labels agree.
    """
    candidate_ids: tuple
    experiment_ids: tuple
    centers: tuple
    generators: tuple
    costs: tuple
    targets: tuple = ()
    source_labels: tuple = ()
    exact_set: bool = True

    def __post_init__(self):
        k, p = len(self.candidate_ids), len(self.experiment_ids)
        if k < 1 or len(set(self.candidate_ids)) != k or len(set(self.experiment_ids)) != p:
            raise ValueError("distinct candidate and experiment identifiers required")
        centers = tuple(tuple(_q(x) for x in row) for row in self.centers)
        generators = tuple(tuple(tuple(_q(x) for x in row) for row in g)
                           for g in self.generators)
        costs = tuple(_q(x) for x in self.costs)
        if len(centers) != k or len(generators) != k or any(len(c) != p for c in centers):
            raise ValueError("candidate/coordinate dimension mismatch")
        if any(len(g) != p or len({len(row) for row in g}) > 1 for g in generators):
            raise ValueError("generator dimensions mismatch")
        if len(costs) != p or any(c <= 0 for c in costs):
            raise ValueError("positive experiment costs required")
        targets = self.targets or self.candidate_ids
        if len(targets) != k or not isinstance(self.exact_set, bool):
            raise ValueError("target count and exact-set flag invalid")
        if self.source_labels and (len(self.source_labels) != k or
                any(len(labels) != (len(g[0]) if p else 0)
                    for labels, g in zip(self.source_labels, generators))):
            raise ValueError("one source label per generator required")
        object.__setattr__(self, "centers", centers)
        object.__setattr__(self, "generators", generators)
        object.__setattr__(self, "costs", costs)
        object.__setattr__(self, "targets", tuple(targets))


def project_panel(family, panel):
    panel = tuple(panel)
    if len(set(panel)) != len(panel) or any(isinstance(i, bool) or not isinstance(i, int)
                                           or not 0 <= i < len(family.costs) for i in panel):
        raise ValueError("invalid panel indices")
    return JointObservationFamily(family.candidate_ids,
        tuple(family.experiment_ids[i] for i in panel),
        tuple(tuple(c[i] for i in panel) for c in family.centers),
        tuple(tuple(g[i] for i in panel) for g in family.generators),
        tuple(family.costs[i] for i in panel), family.targets,
        family.source_labels if panel else (), family.exact_set)


def support_radius(generator, contrast):
    generator = tuple(tuple(_q(x) for x in row) for row in generator)
    contrast = tuple(_q(x) for x in contrast)
    if len(generator) != len(contrast):
        raise ValueError("contrast dimension mismatch")
    width = len(generator[0]) if generator else 0
    if any(len(row) != width for row in generator):
        raise ValueError("generator row dimensions mismatch")
    return sum((abs(sum((contrast[i]*generator[i][j] for i in range(len(contrast))),
                        Fraction(0))) for j in range(width)), Fraction(0))


def joint_family_digest(family):
    """Bind certificates to ordered exact inputs and nuisance provenance."""
    data=(family.candidate_ids,family.experiment_ids,family.centers,family.generators,
          family.costs,family.targets,family.source_labels,family.exact_set)
    return sha256(repr(data).encode('utf-8')).hexdigest()


def joint_pair_certificate(family, a, b, *, max_rows=20000):
    if not isinstance(family, JointObservationFamily):
        raise TypeError("JointObservationFamily required")
    if type(a) is not int or type(b) is not int or not (0 <= a < b < len(family.candidate_ids)):
        raise ValueError("ordered distinct candidate indices required")
    p = len(family.costs)
    ga, gb = family.generators[a], family.generators[b]
    na, nb = (len(ga[0]) if p else 0), (len(gb[0]) if p else 0)
    full_matrix = tuple(tuple(ga[i])+tuple(-x for x in gb[i]) for i in range(p))
    active = tuple(j for j in range(na+nb) if any(row[j] for row in full_matrix))
    matrix = tuple(tuple(row[j] for j in active) for row in full_matrix)
    rhs = tuple(y-x for x, y in zip(family.centers[a], family.centers[b]))
    inequalities = []
    for row, value in zip(matrix, rhs):
        inequalities.extend(((row, value), (tuple(-x for x in row), -value)))
    for j in range(len(active)):
        unit = tuple(Fraction(int(j == t)) for t in range(len(active)))
        inequalities.extend(((unit, 1), (tuple(-x for x in unit), 1)))
    result = rational_feasibility(inequalities, len(active), max_rows=max_rows)
    record = {"schema": "singularity.joint-observations/1", "pair": (a, b),
              "candidate_ids":(family.candidate_ids[a],family.candidate_ids[b]),
              "panel_coordinates":family.experiment_ids,"family_digest":joint_family_digest(family),
              "exact_set": family.exact_set, "generated_rows": result["generated_rows"]}
    if result["feasible"]:
        values = dict(zip(active, result["point"]))
        point = tuple(values.get(j, Fraction(0)) for j in range(na+nb))
        record.update(kind="overlap", left=point[:na], right=point[na:])
    else:
        lam = result["multipliers"]
        contrast = tuple(lam[2*i]-lam[2*i+1] for i in range(p))
        gap = abs(_dot(contrast, rhs))-support_radius(ga, contrast)-support_radius(gb, contrast)
        if gap <= 0:
            raise ArithmeticError("strict contrast extraction failed")
        record.update(kind="separating_contrast", contrast=contrast, gap=gap)
    return record


def verify_joint_certificate(family, certificate):
    try:
        if not isinstance(family, JointObservationFamily):
            return False
        if (certificate.get("schema") != "singularity.joint-observations/1" or
                certificate.get("family_digest") != joint_family_digest(family) or
                certificate.get("panel_coordinates") != family.experiment_ids or
                type(certificate.get("exact_set")) is not bool or
                certificate["exact_set"] != family.exact_set):
            return False
        a, b = certificate["pair"]
        if type(a) is not int or type(b) is not int or not (0 <= a < b < len(family.candidate_ids)):
            return False
        if certificate.get("candidate_ids") != (family.candidate_ids[a],family.candidate_ids[b]):
            return False
        if certificate["kind"] == "overlap":
            left, right = (tuple(_q(x) for x in certificate[k]) for k in ("left", "right"))
            ga, gb = family.generators[a], family.generators[b]
            p = len(family.costs)
            if len(left) != (len(ga[0]) if p else 0) or len(right) != (len(gb[0]) if p else 0):
                return False
            return (all(abs(x) <= 1 for x in left+right) and all(
                x+_dot(ra, left) == y+_dot(rb, right)
                for x, y, ra, rb in zip(family.centers[a], family.centers[b], ga, gb)))
        if certificate["kind"] == "separating_contrast":
            w = tuple(_q(x) for x in certificate["contrast"])
            if len(w) != len(family.costs):
                return False
            gap = abs(_dot(w, tuple(x-y for x, y in zip(family.centers[a], family.centers[b]))))
            gap -= support_radius(family.generators[a], w)+support_radius(family.generators[b], w)
            return gap > 0 and gap == _q(certificate["gap"])
    except (KeyError, ValueError, TypeError, IndexError):
        return False
    return False


def joint_consistent_candidates(family, observation, *, max_rows=20000):
    observation = tuple(_q(x) for x in observation)
    if len(observation) != len(family.costs):
        raise ValueError("observation dimension mismatch")
    result = []
    for c, center in enumerate(family.centers):
        point = JointObservationFamily(("candidate", "observation"), family.experiment_ids,
            (center, observation), (family.generators[c], tuple(() for _ in observation)),
            family.costs)
        if joint_pair_certificate(point, 0, 1, max_rows=max_rows)["kind"] == "overlap":
            result.append(family.candidate_ids[c])
    return tuple(result)


def minimum_joint_panel(family, *, max_subsets=4096, max_rows=20000):
    """Exhaust all subsets in nondecreasing cost; joint geometry, not set cover."""
    if type(max_subsets) is not int or max_subsets < 1 or type(max_rows) is not int or max_rows < 1:
        raise ValueError("positive integer subset and elimination budgets required")
    p = len(family.costs)
    if 2**p > max_subsets:
        raise GeometryBudgetExceeded("complete subset pool exceeds max_subsets")
    panels = sorted((tuple(i for i in range(p) if mask >> i & 1) for mask in range(2**p)),
                    key=lambda panel: (sum(family.costs[i] for i in panel), len(panel), panel))
    checked = []
    for panel in panels:
        projected = project_panel(family, panel)
        certificates = tuple(joint_pair_certificate(projected, a, b, max_rows=max_rows)
            for a in range(len(family.candidate_ids)) for b in range(a+1, len(family.candidate_ids))
            if family.targets[a] != family.targets[b])
        checked.append((panel, certificates))
        if all(c["kind"] == "separating_contrast" for c in certificates):
            return {"status": "optimal" if family.exact_set else "optimal_for_outer_enclosure", "panel": panel,
                    "scope": "exact-observation-sets" if family.exact_set else "declared-outer-enclosures",
                    "cost": sum((family.costs[i] for i in panel), Fraction(0)),
                    "certificates": certificates, "checked_panels": tuple(checked)}
    return {"status": "impossible" if family.exact_set else "not_certified",
            "scope": "exact-observation-sets" if family.exact_set else "declared-outer-enclosures",
            "panel": None, "checked_panels": tuple(checked)}


def affine_protocol_family(candidates, protocols, *, persistent_offset=0, sensor_noise=0,
                           initial_radius=0, costs=None):
    """Exact affine map for independent reset boxes plus persistent output offset."""
    from .thermal_diagnostics import simulate_protocol
    candidates, protocols = tuple(candidates), tuple(protocols)
    offset, noise, radius = (_q(x) for x in (persistent_offset, sensor_noise, initial_radius))
    if min(offset, noise, radius) < 0:
        raise ValueError("uncertainty bounds must be nonnegative")
    p = len(protocols)
    centers, generators, labels = [], [], []
    for candidate in candidates:
        n = candidate.dimension
        rows, centers_c = [], []
        for e, (word, sensor) in enumerate(protocols):
            centers_c.append(simulate_protocol(candidate, word, sensor))
            sensitivities = []
            for j in range(n):
                state = tuple(Fraction(int(i == j)) for i in range(n))
                for amplitude in word:
                    state = candidate.step(state, 0)
                sensitivities.append(radius*candidate.observe(state, sensor))
            rows.append((offset,)+tuple(noise if e == i else Fraction(0) for i in range(p))+
                        tuple(sensitivities[j] if block == e else Fraction(0)
                              for block in range(p) for j in range(n)))
        centers.append(tuple(centers_c)); generators.append(tuple(rows))
        labels.append(("persistent:output_offset",)+tuple(f"measurement:{i}:noise" for i in range(p))+
                      tuple(f"reset:{i}:initial_cell_{j}" for i in range(p) for j in range(n)))
    return JointObservationFamily(tuple(c.identifier for c in candidates), tuple(protocols),
        tuple(centers), tuple(generators), tuple(costs or (Fraction(1),)*p),
        source_labels=tuple(labels))
