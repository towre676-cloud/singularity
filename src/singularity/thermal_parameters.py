"""Validated rational polynomial families for partial blockage and calibration.

Interval subdivision certifies the entire declared compact product domain.
Each hypothesis has its own calibration variables. Samples only produce
explicit overlap witnesses; they are never used to prove separation.
"""
from dataclasses import dataclass
from fractions import Fraction
from .joint_uncertainty import _q, _dot
from .fault_population import plate_bonds, plate_nominal
from .thermal_diagnostics import AffineCandidate


@dataclass(frozen=True)
class Polynomial:
    dimension: int
    terms: tuple

    def __post_init__(self):
        if type(self.dimension) is not int or self.dimension < 0:
            raise ValueError("nonnegative polynomial dimension required")
        merged = {}
        for exponent, coefficient in self.terms:
            exponent = tuple(exponent)
            if len(exponent) != self.dimension or any(type(x) is not int or x < 0 for x in exponent):
                raise ValueError("invalid monomial exponent")
            merged[exponent] = merged.get(exponent, Fraction(0))+_q(coefficient)
        object.__setattr__(self, "terms", tuple(sorted((e, c) for e, c in merged.items() if c)))

    @classmethod
    def constant(cls, n, value):
        return cls(n, (((0,)*n, _q(value)),))

    @classmethod
    def variable(cls, n, index):
        if type(index) is not int or not 0 <= index < n:
            raise ValueError("variable index out of range")
        return cls(n, ((tuple(int(i == index) for i in range(n)), Fraction(1)),))

    def __add__(self, other):
        if not isinstance(other, Polynomial):
            other = Polynomial.constant(self.dimension, other)
        if self.dimension != other.dimension:
            raise ValueError("polynomial dimension mismatch")
        return Polynomial(self.dimension, self.terms+other.terms)

    __radd__ = __add__

    def __neg__(self):
        return Polynomial(self.dimension, tuple((e, -c) for e, c in self.terms))

    def __sub__(self, other):
        return self+-other

    def __rsub__(self, other):
        return -self+other

    def __mul__(self, other):
        if not isinstance(other, Polynomial):
            other = Polynomial.constant(self.dimension, other)
        if self.dimension != other.dimension:
            raise ValueError("polynomial dimension mismatch")
        return Polynomial(self.dimension, tuple((tuple(x+y for x, y in zip(a, b)), c*d)
            for a, c in self.terms for b, d in other.terms))

    __rmul__ = __mul__

    def evaluate(self, point):
        point = tuple(_q(x) for x in point)
        if len(point) != self.dimension:
            raise ValueError("point dimension mismatch")
        total = Fraction(0)
        for exponent, coefficient in self.terms:
            term = coefficient
            for x, power in zip(point, exponent):
                term *= x**power
            total += term
        return total

    def enclosure(self, box):
        box = _box(box, self.dimension)
        low = high = Fraction(0)
        for exponent, coefficient in self.terms:
            lo = hi = coefficient
            for (a, b), power in zip(box, exponent):
                endpoints = (a**power, b**power)
                amin = Fraction(0) if power and power % 2 == 0 and a <= 0 <= b else min(endpoints)
                amax = max(endpoints)
                products = (lo*amin, lo*amax, hi*amin, hi*amax)
                lo, hi = min(products), max(products)
            low += lo; high += hi
        return low, high


def _box(box, dimension):
    box = tuple(tuple(_q(x) for x in pair) for pair in box)
    if len(box) != dimension or any(len(pair) != 2 or pair[0] > pair[1] for pair in box):
        raise ValueError("closed parameter box dimension/order invalid")
    return box


@dataclass(frozen=True)
class ThermalParameterDomain:
    bounds: tuple
    names: tuple = ("conductance", "loss", "heater_gain", "severity")
    severity_convention: str = "zero=nominal,one=fully-blocked"
    source_digest: str = "caller-declared-rational-stencil"

    def __post_init__(self):
        box = _box(self.bounds, 4)
        if self.severity_convention != "zero=nominal,one=fully-blocked":
            raise ValueError("ambiguous severity convention")
        if len(self.names) != 4 or len(set(self.names)) != 4:
            raise ValueError("four distinct parameter names required")
        k, loss, gain, severity = box
        if k[0] < 0 or loss[0] <= 0 or gain[0] < 0 or severity[0] < 0 or severity[1] > 1:
            raise ValueError("parameter box violates positivity/severity admissibility")
        if 4*k[1]+loss[1] > 1:
            raise ValueError("entire box must satisfy 4k+loss<=1; split/intersect first")
        object.__setattr__(self, "bounds", box)


def parametric_fault_sample(grid, bond, parameters, *, identifier="parameter-sample"):
    k, loss, gain, alpha = tuple(_q(x) for x in parameters)
    ThermalParameterDomain(tuple((x, x) for x in (k, loss, gain, alpha)))
    source, bonds = plate_nominal(grid), plate_bonds(grid)
    bond = tuple(sorted(bond))
    if bond not in bonds:
        raise ValueError("fault bond absent from source")
    entries = {(i, i): 1-loss for i in range(source.dimension)}
    for a, b in bonds:
        conductance = k*(1-alpha) if (a, b) == bond else k
        entries[a, a] -= conductance; entries[b, b] -= conductance
        entries[a, b] = conductance; entries[b, a] = conductance
    return AffineCandidate(identifier, source.dimension,
        tuple((i, j, value) for (i, j), value in entries.items()),
        tuple(gain*x for x in source.heater), source.sensors)


def panel_parameter_map(grid, bond, protocols, *, max_terms=100000, max_horizon=4):
    """Sparse symbolic evolution in k,loss,g,alpha; every reset starts at zero."""
    source, bonds = plate_nominal(grid), plate_bonds(grid)
    bond = tuple(sorted(bond))
    if bond not in bonds:
        raise ValueError("fault bond absent from source")
    k, loss, gain, alpha = (Polynomial.variable(4, i) for i in range(4))
    zero = Polynomial.constant(4, 0)
    result = []
    for word, sensor in protocols:
        if len(word) > max_horizon or not 0 <= sensor < len(source.sensors):
            raise ValueError("symbolic horizon/sensor outside declared budget")
        state = [zero]*source.dimension
        for amplitude in word:
            amplitude = _q(amplitude)
            new = [(1-loss)*x+gain*(amplitude*b) for x, b in zip(state, source.heater)]
            for a, b in bonds:
                conductance = k*(1-alpha) if (a, b) == bond else k
                flux = conductance*(state[b]-state[a])
                new[a] = new[a]+flux; new[b] = new[b]-flux
            if sum(len(p.terms) for p in new) > max_terms:
                raise ValueError("symbolic coefficient budget exceeded")
            state = new
        result.append(sum((x*c for x, c in zip(state, source.sensors[sensor])), zero))
    return tuple(result)


@dataclass(frozen=True)
class ParametricFaultFamily:
    identifier: str
    domain: tuple
    observations: tuple

    def __post_init__(self):
        observations = tuple(self.observations)
        dimension = observations[0].dimension if observations else len(self.domain)
        if any(not isinstance(p, Polynomial) or p.dimension != dimension for p in observations):
            raise ValueError("consistent polynomial maps required")
        object.__setattr__(self, "observations", observations)
        object.__setattr__(self, "domain", _box(self.domain, dimension))


def certify_family_separation(left, right, *, noise=0, contrasts=None, max_cells=1023,
                              overlap_witnesses=()):
    """Cover independent parameter domains by strict rational contrast gaps.

    A returned overlap contains complete independent parameter assignments and
    a common observation. ``unresolved`` includes every unprocessed cell.
    ``separated`` is a full-domain certificate, replayable from its binary tree.
    """
    if len(left.observations) != len(right.observations):
        raise ValueError("observation dimensions mismatch")
    p = len(left.observations)
    errors = tuple(_q(x) for x in noise) if isinstance(noise, (tuple, list)) else (_q(noise),)*p
    if len(errors) != p or any(x < 0 for x in errors) or type(max_cells) is not int or max_cells < 1:
        raise ValueError("invalid error bounds/cell budget")
    for pa, pb in overlap_witnesses:
        pa, pb = tuple(_q(x) for x in pa), tuple(_q(x) for x in pb)
        if len(pa) != len(left.domain) or len(pb) != len(right.domain) or any(
                not lo <= x <= hi for x, (lo, hi) in zip(pa, left.domain)) or any(
                not lo <= x <= hi for x, (lo, hi) in zip(pb, right.domain)):
            raise ValueError("overlap witness parameters outside declared domains")
        va = tuple(poly.evaluate(pa) for poly in left.observations)
        vb = tuple(poly.evaluate(pb) for poly in right.observations)
        if not all(abs(x-y) <= 2*e for x, y, e in zip(va, vb, errors)):
            raise ValueError("supplied assignments do not give overlap")
        return {"schema": "singularity.parametric-fault-separation/1", "status": "overlap",
                "left_parameters": pa, "right_parameters": pb,
                "observation": tuple((x+y)/2 for x, y in zip(va, vb)), "noise": errors,
                "visited_cells": 0}
    contrasts = tuple(tuple(_q(x) for x in w) for w in (contrasts if contrasts is not None else
                    (tuple(int(i == j) for i in range(p)) for j in range(p))))
    if any(len(w) != p for w in contrasts):
        raise ValueError("contrast dimension mismatch")
    left_maps = tuple(sum((p0*w0 for p0, w0 in zip(left.observations, w)),
                          Polynomial.constant(len(left.domain), 0)) for w in contrasts)
    right_maps = tuple(sum((p0*w0 for p0, w0 in zip(right.observations, w)),
                           Polynomial.constant(len(right.domain), 0)) for w in contrasts)
    margin_errors = tuple(2*sum(abs(x)*e for x, e in zip(w, errors)) for w in contrasts)
    nodes = [{"left_box": left.domain, "right_box": right.domain}]
    queue, visited = [0], 0
    while queue and visited < max_cells:
        index = queue.pop(); node = nodes[index]; visited += 1
        a, b = node["left_box"], node["right_box"]
        pa = tuple((lo+hi)/2 for lo, hi in a)
        pb = tuple((lo+hi)/2 for lo, hi in b)
        va = tuple(p.evaluate(pa) for p in left.observations)
        vb = tuple(p.evaluate(pb) for p in right.observations)
        if all(abs(x-y) <= 2*e for x, y, e in zip(va, vb, errors)):
            return {"schema": "singularity.parametric-fault-separation/1", "status": "overlap",
                    "left_parameters": pa, "right_parameters": pb,
                    "observation": tuple((x+y)/2 for x, y in zip(va, vb)), "noise": errors,
                    "visited_cells": visited}
        for j, (lm, rm, error) in enumerate(zip(left_maps, right_maps, margin_errors)):
            la, ua = lm.enclosure(a); lb, ub = rm.enclosure(b)
            gap = max(la-ub, lb-ua)-error
            if gap > 0:
                node.update(kind="separated", contrast=j, gap=gap)
                break
        else:
            joined = a+b
            width, dimension = max(((hi-lo, j) for j, (lo, hi) in enumerate(joined)), default=(0, 0))
            if width == 0:
                node["kind"] = "unresolved"
                continue
            lo, hi = joined[dimension]; midpoint = (lo+hi)/2
            children = []
            for interval in ((lo, midpoint), (midpoint, hi)):
                box = joined[:dimension]+(interval,)+joined[dimension+1:]
                children.append(len(nodes))
                nodes.append({"left_box": box[:len(a)], "right_box": box[len(a):]})
            node.update(kind="split", dimension=dimension, midpoint=midpoint, children=tuple(children))
            queue.extend(children)
    unresolved = tuple(i for i, node in enumerate(nodes) if node.get("kind") in (None, "unresolved"))
    return {"schema": "singularity.parametric-fault-separation/1",
            "status": "unresolved" if unresolved else "separated", "noise": errors,
            "contrasts": contrasts, "nodes": tuple(nodes), "unresolved_cells": unresolved,
            "visited_cells": visited, "semantics": "independent-parameters-per-hypothesis"}


def verify_family_certificate(left, right, certificate):
    try:
        errors = tuple(_q(x) for x in certificate["noise"])
        if len(errors) != len(left.observations) or len(right.observations) != len(errors) or any(x < 0 for x in errors):
            return False
        if certificate["status"] == "overlap":
            pa, pb, y = (tuple(certificate[k]) for k in
                         ("left_parameters", "right_parameters", "observation"))
            if any(not lo <= x <= hi for x, (lo, hi) in zip(pa, left.domain)) or any(
                    not lo <= x <= hi for x, (lo, hi) in zip(pb, right.domain)):
                return False
            return (len(pa) == len(left.domain) and len(pb) == len(right.domain) and
                    len(y) == len(left.observations) and all(abs(p.evaluate(pa)-z) <= e
                        and abs(r.evaluate(pb)-z) <= e for p, r, z, e in
                        zip(left.observations, right.observations, y, errors)))
        nodes = certificate["nodes"]
        if not nodes or nodes[0]["left_box"] != left.domain or nodes[0]["right_box"] != right.domain:
            return False
        seen = set()
        def check(index):
            if index in seen or not 0 <= index < len(nodes):
                return False
            seen.add(index); node = nodes[index]
            a, b = node["left_box"], node["right_box"]
            if node["kind"] == "separated":
                w = certificate["contrasts"][node["contrast"]]
                lm = sum((p*c for p, c in zip(left.observations, w)), Polynomial.constant(len(a), 0))
                rm = sum((p*c for p, c in zip(right.observations, w)), Polynomial.constant(len(b), 0))
                la, ua = lm.enclosure(a); lb, ub = rm.enclosure(b)
                gap = max(la-ub, lb-ua)-2*sum(abs(c)*e for c, e in zip(w, errors))
                return gap > 0 and gap == node["gap"]
            if node["kind"] != "split" or len(node["children"]) != 2:
                return False
            joined, d, mid = a+b, node["dimension"], node["midpoint"]
            if not joined[d][0] < mid < joined[d][1]:
                return False
            for child, interval in zip(node["children"], ((joined[d][0], mid), (mid, joined[d][1]))):
                expected = joined[:d]+(interval,)+joined[d+1:]
                if nodes[child]["left_box"]+nodes[child]["right_box"] != expected or not check(child):
                    return False
            return True
        return certificate["status"] == "separated" and check(0) and len(seen) == len(nodes)
    except (KeyError, ValueError, TypeError, IndexError):
        return False


def severity_frontier(family_builder, nominal, bands, **kwargs):
    """Certify each caller-declared closed severity band, without interpolation."""
    return tuple({"severity_band": tuple(band), "certificate":
                  certify_family_separation(nominal, family_builder(tuple(band)), **kwargs)} for band in bands)
