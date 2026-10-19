"""Incremental connected-support compilation for weighted energies (NX16).

On vertices ``0, ..., n-1`` take symmetric nonnegative integral edge weights
``w_uv`` and nonnegative integral pinnings ``lambda_v``, and put

    E_w(h) = sum_{u<v} w_uv (h_u - h_v)^2 + sum_v lambda_v h_v^2,
    F_w(x, q) = sum_{h >= 0} x^|h| q^(E_w(h)).

A zero weight is the absence of an edge.  ``q`` counts energy in a declared
positive rational unit (``energy_unit``); every exponent is a nonnegative
integer number of units.  The positive-weight support graph replaces the
unweighted ``Graph`` of ``locality``; the ambient decoration of a vertex is
its weighted degree plus its pinning, ``d_v = sum_u w_uv + lambda_v``.

With one variable per vertex, ``Phi_S = sum_{T subset S} (-1)^(|S|-|T|) log Z_T``
is the part of ``log F`` whose monomials use every vertex of ``S``.  It is
``O(x^|S|)``, vanishes unless ``S`` is connected in the positive-weight graph,
and depends only on the decorations and internal weights of ``S``.  Hence

    log F_w mod x^(R+1) = sum_{S connected, |S| <= R} Phi_S(w),

and after a local change with endpoint set ``D`` and union support graph
``U`` (an edge whenever either version has positive weight),

    Delta log F = sum_{S connected in U, |S| <= R, S meets D} (Phi_S(w') - Phi_S(w)).

The proofs are in docs/research/INCREMENTAL_LOCALITY.md.  Memo keys are
complete relabelled descriptions (size, decorations, weighted internal
edges) of the decorated support, so a key can never be shared by two
supports with different contributions, whatever graph either came from;
``Phi`` is computed from the key alone.  The existing ``locality.pinned_log``
API is unchanged and serves as a cross-check for unweighted inputs.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from fractions import Fraction
from itertools import permutations, product
from math import factorial, lcm, prod
from typing import Callable, Iterable, Iterator, Mapping

from .heights import weak_compositions
from .locality import series_from_log
from .polynomials import add, normalize, polynomial_from_json, polynomial_to_json, scale, series_log

SCHEMA = "singularity.locality-update/1"
CONVENTION = "F=sum_h x^|h| q^(E_w(h)/energy_unit); E_w=sum w_uv(h_u-h_v)^2+sum lambda_v h_v^2"
CANONICAL_LIMIT = 5040  # class-respecting orders tried before falling back to a labelled (still complete) key

Series = list


# ---------------------------------------------------------------------------
# validation helpers


def _int(value: object, name: str, minimum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if minimum is not None and value < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    return value


def _rational(value: object, name: str) -> Fraction:
    if isinstance(value, bool) or not isinstance(value, (int, Fraction)):
        raise TypeError(f"{name} must be an integer or Fraction")
    return Fraction(value)


def _zero_series(R: int) -> Series:
    return [{} for _ in range(R + 1)]


def _accumulate(total: Series, series: Series, factor) -> None:
    """total += factor * series, in place, on already-normalized exact coefficients."""
    for row, poly in zip(total, series):
        for e, c in poly.items():
            row[e] = row.get(e, 0) + factor * c


def _clean(total: Series) -> Series:
    return [{e: Fraction(c) for e, c in sorted(row.items()) if c} for row in total]


# ---------------------------------------------------------------------------
# weighted specification and the independent oracle


@dataclass(frozen=True, init=False)
class WeightedSpec:
    """Immutable weighted energy on vertices ``0..n-1``.

    ``weights`` is stored as sorted ``(u, v, w)`` with ``u < v`` and ``w > 0``;
    zero weights given on input are validated and then dropped (absence).
    ``pinning`` is one nonnegative integer per vertex.  ``energy_unit`` is the
    positive rational value of one power of ``q``.
    """

    n: int
    weights: tuple
    pinning: tuple
    energy_unit: Fraction

    def __init__(self, n: int, weights: Iterable | Mapping = (), pinning: Iterable[int] | None = None,
                 energy_unit: int | Fraction = 1) -> None:
        n = _int(n, "n", 1)
        items = list(weights.items()) if isinstance(weights, Mapping) else list(weights)
        seen: dict[tuple[int, int], int] = {}
        for item in items:
            if isinstance(weights, Mapping):
                pair, w = item
                try:
                    u, v = pair
                except (TypeError, ValueError) as exc:
                    raise ValueError("weight keys must be vertex pairs") from exc
            else:
                try:
                    u, v, w = item
                except (TypeError, ValueError) as exc:
                    raise ValueError("weights must be (u, v, w) triples") from exc
            u, v, w = _int(u, "endpoint", 0), _int(v, "endpoint", 0), _int(w, "weight", 0)
            if u >= n or v >= n:
                raise ValueError("endpoint outside 0..n-1")
            if u == v:
                raise ValueError("loops are not allowed")
            key = (min(u, v), max(u, v))
            if key in seen:
                raise ValueError(f"duplicate pair {key}")
            seen[key] = w
        pins = (0,) * n if pinning is None else tuple(pinning)
        if len(pins) != n:
            raise ValueError("pinning needs one value per vertex")
        pins = tuple(_int(p, "pinning", 0) for p in pins)
        unit = _rational(energy_unit, "energy_unit")
        if unit <= 0:
            raise ValueError("energy_unit must be positive")
        object.__setattr__(self, "n", n)
        object.__setattr__(self, "weights", tuple((u, v, w) for (u, v), w in sorted(seen.items()) if w))
        object.__setattr__(self, "pinning", pins)
        object.__setattr__(self, "energy_unit", unit)

    def weight(self, u: int, v: int) -> int:
        u, v = _int(u, "endpoint", 0), _int(v, "endpoint", 0)
        if u >= self.n or v >= self.n or u == v:
            raise ValueError("invalid vertex pair")
        a, b = min(u, v), max(u, v)
        for x, y, w in self.weights:
            if (x, y) == (a, b):
                return w
        return 0

    def energy(self, h) -> int:
        """E_w(h) in energy units, by edge differences (no quadratic-form expansion)."""
        if len(h) != self.n:
            raise ValueError("one height per vertex is required")
        h = [_int(x, "height", 0) for x in h]
        return (sum(w * (h[u] - h[v]) ** 2 for u, v, w in self.weights)
                + sum(p * x * x for p, x in zip(self.pinning, h)))

    def to_json(self) -> dict:
        return {"n": self.n, "weights": [list(e) for e in self.weights], "pinning": list(self.pinning),
                "energy_unit": [self.energy_unit.numerator, self.energy_unit.denominator]}

    @classmethod
    def from_json(cls, data: Mapping) -> "WeightedSpec":
        if not isinstance(data, Mapping) or set(data) != {"n", "weights", "pinning", "energy_unit"}:
            raise ValueError("malformed weighted specification")
        try:
            num, den = data["energy_unit"]
        except (TypeError, ValueError) as exc:
            raise ValueError("energy_unit must be [numerator, denominator]") from exc
        unit = Fraction(_int(num, "unit numerator", 1), _int(den, "unit denominator", 1))
        if (unit.numerator, unit.denominator) != (num, den):
            raise ValueError("unit must be in lowest terms")
        spec = cls(data["n"], [tuple(e) for e in data["weights"]], data["pinning"], unit)
        if any(e[2] == 0 for e in data["weights"]):
            raise ValueError("stored weights must be positive (zero is absence)")
        return spec


def from_graph(graph, lam: int = 0) -> WeightedSpec:
    """Unit weights on the edges of a ``Graph`` and uniform pinning ``lam`` (lam=0: L_G; lam=2: A_H)."""
    lam = _int(lam, "lam", 0)
    return WeightedSpec(graph.n, [(u, v, 1) for u, v in graph.edges], (lam,) * graph.n)


def from_rational_weights(n: int, weights: Iterable, pinning: Iterable | None = None) -> WeightedSpec:
    """Scale nonnegative rational weights/pinnings by the lcm L of their denominators.

    The returned specification has integral weights and ``energy_unit = 1/L``:
    ``q^k`` then means energy ``k/L``.  Floats are rejected.
    """
    n = _int(n, "n", 1)
    triples = []
    for item in weights:
        try:
            u, v, w = item
        except (TypeError, ValueError) as exc:
            raise ValueError("weights must be (u, v, w) triples") from exc
        w = _rational(w, "weight")
        if w < 0:
            raise ValueError("weights must be nonnegative")
        triples.append((u, v, w))
    pins = [Fraction(0)] * n if pinning is None else [_rational(p, "pinning") for p in pinning]
    if any(p < 0 for p in pins):
        raise ValueError("pinning must be nonnegative")
    L = lcm(1, *(w.denominator for _, _, w in triples), *(p.denominator for p in pins))
    return WeightedSpec(n, [(u, v, int(w * L)) for u, v, w in triples], [int(p * L) for p in pins],
                        Fraction(1, L))


def direct_series(spec: WeightedSpec, max_volume: int, max_profiles: int = 400_000) -> Series:
    """Independent oracle: [x^m] F_w for m <= R from every height in the box [0, R]^n.

    Uses ``WeightedSpec.energy`` (edge differences) and ``itertools.product``;
    it calls none of the support machinery.  Raises ValueError when the box
    exceeds ``max_profiles`` (a budget refusal, not a mathematical failure).
    """
    if not isinstance(spec, WeightedSpec):
        raise TypeError("spec must be a WeightedSpec")
    R = _int(max_volume, "max_volume", 0)
    box = (R + 1) ** spec.n
    if box > _int(max_profiles, "max_profiles", 1):
        raise ValueError(f"oracle box has {box} profiles; budget is {max_profiles}")
    rows = [Counter() for _ in range(R + 1)]
    for h in product(range(R + 1), repeat=spec.n):
        s = sum(h)
        if s <= R:
            rows[s][spec.energy(h)] += 1
    return [{e: Fraction(c) for e, c in sorted(r.items())} for r in rows]


def support_contribution_by_definition(spec: WeightedSpec, support: Iterable[int], max_volume: int) -> Series:
    """Phi_S straight from its definition, for checking: no memo, no factorization.

    Each Z_T counts every height supported in T inside [0, R]^T with the
    full edge-difference energy of ``spec``.  Exponential in |S|; use on
    small supports only.
    """
    R = _int(max_volume, "max_volume", 0)
    verts = sorted(set(support))
    if not verts or any(_int(v, "vertex", 0) >= spec.n for v in verts):
        raise ValueError("support must be a nonempty set of vertices")
    total = _zero_series(R)
    for mask in range(1, 1 << len(verts)):
        T = [v for i, v in enumerate(verts) if mask >> i & 1]
        rows = [Counter() for _ in range(R + 1)]
        h = [0] * spec.n
        for values in product(range(R + 1), repeat=len(T)):
            if sum(values) <= R:
                for v, x in zip(T, values):
                    h[v] = x
                rows[sum(values)][spec.energy(h)] += 1
        for v in T:
            h[v] = 0
        log = series_log([dict(r) for r in rows], R)
        sign = -1 if (len(verts) - len(T)) % 2 else 1
        total = [add(a, scale(b, sign)) for a, b in zip(total, log)]
    return [normalize(t) for t in total]


# ---------------------------------------------------------------------------
# local enumeration of connected supports


def connected_sets_through(neighbours: Callable[[int], Iterable[int]], root: int, max_size: int,
                           allowed: Callable[[int], bool] = lambda w: True) -> Iterator[frozenset]:
    """Every connected set of at most ``max_size`` vertices containing ``root``, all other
    members satisfying ``allowed``, once each.

    Adjacency is read only through ``neighbours`` on members of the growing
    set, so the work is local: it never scans the whole graph.  The scheme is
    the exclusion-set extension used by ``locality.connected_supersets``,
    which however copies the full adjacency first.
    """
    k = _int(max_size, "max_size", 0)
    if k == 0:
        return

    def extend(current, frontier, excluded):
        yield current
        if len(current) == k:
            return
        blocked = set(excluded)
        for i, v in enumerate(frontier):
            fresh = sorted(w for w in neighbours(v) if w not in current and w not in blocked
                           and w not in frontier and allowed(w))
            yield from extend(current | {v}, frontier[i + 1:] + fresh, blocked | set(frontier[: i + 1]))
            blocked.add(v)

    start = sorted(w for w in neighbours(root) if w != root and allowed(w))
    yield from extend(frozenset((root,)), start, set())


def connected_sets_meeting(neighbours: Callable[[int], Iterable[int]], marked: Iterable[int],
                           max_size: int) -> Iterator[frozenset]:
    """Every connected set of at most ``max_size`` vertices meeting ``marked``, once each.

    A set is produced from its least marked member d_i, avoiding d_1..d_(i-1).
    """
    order = sorted(set(marked))
    for i, d in enumerate(order):
        earlier = frozenset(order[:i])
        yield from connected_sets_through(neighbours, d, max_size, lambda w, e=earlier: w not in e)


def _is_connected(S: frozenset, adjacency) -> bool:
    start = next(iter(S))
    seen, stack = {start}, [start]
    while stack:
        u = stack.pop()
        for w in adjacency[u]:
            if w in S and w not in seen:
                seen.add(w)
                stack.append(w)
    return len(seen) == len(S)


# ---------------------------------------------------------------------------
# decorated keys and contributions computed from keys


def _canonical(decorations: tuple, edges: tuple) -> tuple:
    """A complete description (k, decorations, weighted edges) under a minimizing relabelling.

    Classes are (decoration, sorted incident internal weights); orders
    respecting them are tried while cheap.  Otherwise the given labelling is
    kept: still a complete description, so equal keys always mean equal
    contributions -- only sharing is lost.
    """
    k = len(decorations)
    incident: list[list[int]] = [[] for _ in range(k)]
    for a, b, w in edges:
        incident[a].append(w)
        incident[b].append(w)
    classes: dict[tuple, list[int]] = {}
    for i in range(k):
        classes.setdefault((decorations[i], tuple(sorted(incident[i]))), []).append(i)
    groups = [classes[c] for c in sorted(classes)]
    if prod(factorial(len(g)) for g in groups) > CANONICAL_LIMIT:
        return (k, tuple(decorations), tuple(sorted(edges)))
    new_decorations = tuple(decorations[i] for g in groups for i in g)
    best = None

    def orders(j):
        if j == len(groups):
            yield ()
            return
        for perm in permutations(groups[j]):
            for rest in orders(j + 1):
                yield perm + rest

    for order in orders(0):
        where = {old: new for new, old in enumerate(order)}
        key = tuple(sorted((min(where[a], where[b]), max(where[a], where[b]), w) for a, b, w in edges))
        if best is None or key < best:
            best = key
    return (k, new_decorations, best)


def _key_components(key: tuple, positions: tuple) -> list[tuple]:
    k, decorations, edges = key
    inside = set(positions)
    adj: dict[int, list[int]] = {p: [] for p in positions}
    for a, b, _ in edges:
        if a in inside and b in inside:
            adj[a].append(b)
            adj[b].append(a)
    seen, out = set(), []
    for p in positions:
        if p in seen:
            continue
        comp, stack = [], [p]
        seen.add(p)
        while stack:
            u = stack.pop()
            comp.append(u)
            for w in adj[u]:
                if w not in seen:
                    seen.add(w)
                    stack.append(w)
        out.append(tuple(sorted(comp)))
    return out


def _sub_key(key: tuple, positions: tuple) -> tuple:
    _, decorations, edges = key
    where = {p: i for i, p in enumerate(positions)}
    sub_edges = tuple((where[a], where[b], w) for a, b, w in edges if a in where and b in where)
    return _canonical(tuple(decorations[p] for p in positions), sub_edges)


def _restricted_log(key: tuple, R: int, counters: Counter) -> Series:
    """log Z for a connected decorated block (heights zero elsewhere) modulo x^(R+1)."""
    k, decorations, edges = key
    rows = [Counter() for _ in range(R + 1)]
    for volume in range(R + 1):
        for h in weak_compositions(volume, k):
            energy = sum(d * x * x for d, x in zip(decorations, h)) - 2 * sum(w * h[a] * h[b] for a, b, w in edges)
            rows[volume][energy] += 1
            counters["profiles"] += 1
    counters["restricted_logs"] += 1
    return series_log([dict(r) for r in rows], R)


def _phi(key: tuple, R: int, cache: dict, counters: Counter) -> Series:
    """Phi for a decorated support described by ``key`` (memoized in ``cache``)."""
    slot = ("phi", R, CONVENTION, key)
    counters["phi_lookups"] += 1
    if slot in cache:
        return cache[slot]
    counters["phi_computed"] += 1
    k = key[0]
    total = _zero_series(R)
    for mask in range(1, 1 << k):
        T = tuple(i for i in range(k) if mask >> i & 1)
        sign = -1 if (k - len(T)) % 2 else 1
        for comp in _key_components(key, T):
            sk = _sub_key(key, comp)
            lslot = ("log", R, CONVENTION, sk)
            if lslot not in cache:
                cache[lslot] = _restricted_log(sk, R, counters)
            _accumulate(total, cache[lslot], sign)
            counters["poly_adds"] += R + 1
    cache[slot] = _clean(total)
    return cache[slot]


# ---------------------------------------------------------------------------
# compilation state


class LocalityCompilation:
    """Compiled ``log F_w mod x^(R+1)`` with its connected-support index.

    ``support_index`` maps every support connected in the positive-weight
    graph with at most R vertices to its decorated key.  ``cache`` holds
    contributions by key and may be shared between compilations of
    unrelated graphs (keys are complete descriptions).
    """

    __slots__ = ("n", "max_volume", "energy_unit", "_adj", "_pin", "_deco", "support_index", "log", "cache")

    def __init__(self, n, max_volume, energy_unit, adj, pin, deco, support_index, log, cache):
        self.n, self.max_volume, self.energy_unit = n, max_volume, energy_unit
        self._adj, self._pin, self._deco = adj, pin, deco
        self.support_index, self.log, self.cache = support_index, log, cache

    def copy(self) -> "LocalityCompilation":
        """Independent state (the contribution cache stays shared, which is safe)."""
        return LocalityCompilation(self.n, self.max_volume, self.energy_unit, [dict(a) for a in self._adj],
                                   list(self._pin), list(self._deco), dict(self.support_index),
                                   [dict(p) for p in self.log], self.cache)

    def weight(self, u: int, v: int) -> int:
        return self._adj[u].get(v, 0)

    def pinning(self, v: int) -> int:
        return self._pin[v]

    @property
    def spec(self) -> WeightedSpec:
        return WeightedSpec(self.n, [(u, v, w) for u in range(self.n) for v, w in self._adj[u].items() if u < v],
                            self._pin, self.energy_unit)

    def series(self, statistics: dict | None = None) -> Series:
        """F_w modulo x^(R+1) by formal exponentiation (R(R+1)/2 polynomial products)."""
        R = self.max_volume
        if statistics is not None:
            statistics["exp_poly_products"] = R * (R + 1) // 2
        return series_from_log(self.log)

    def _key(self, S: frozenset) -> tuple:
        verts = sorted(S)
        where = {v: i for i, v in enumerate(verts)}
        edges = tuple((where[u], where[v], w) for u in verts for v, w in self._adj[u].items() if u < v and v in where)
        return _canonical(tuple(self._deco[v] for v in verts), edges)

    def state_signature(self) -> tuple:
        """Everything that defines the compiled state, for exact comparisons in checks."""
        return (self.n, self.max_volume, self.energy_unit, self.spec.weights, tuple(self._pin),
                tuple(sorted((tuple(sorted(S)), k) for S, k in self.support_index.items())),
                tuple(tuple(sorted(p.items())) for p in self.log))


def compile_locality(spec: WeightedSpec, max_volume: int, cache: dict | None = None,
                     statistics: dict | None = None) -> LocalityCompilation:
    """Full compilation: sum Phi_S over connected supports |S| <= R, memoized by decorated key."""
    if not isinstance(spec, WeightedSpec):
        raise TypeError("spec must be a WeightedSpec")
    R = _int(max_volume, "max_volume", 0)
    cache = {} if cache is None else cache
    if not isinstance(cache, dict):
        raise TypeError("cache must be a dict")
    adj: list[dict[int, int]] = [dict() for _ in range(spec.n)]
    for u, v, w in spec.weights:
        adj[u][v] = w
        adj[v][u] = w
    pin = list(spec.pinning)
    deco = [sum(adj[v].values()) + pin[v] for v in range(spec.n)]
    comp = LocalityCompilation(spec.n, R, spec.energy_unit, adj, pin, deco, {}, _zero_series(R), cache)
    counters: Counter = Counter()
    multiplicity: Counter = Counter()
    neighbours = lambda v: adj[v]
    for root in range(spec.n):
        for S in connected_sets_through(neighbours, root, R, lambda w, r=root: w > r):
            key = comp._key(S)
            comp.support_index[S] = key
            multiplicity[key] += 1
    total = _zero_series(R)
    for key, m in multiplicity.items():
        _accumulate(total, _phi(key, R, cache, counters), m)
        counters["poly_adds"] += R + 1
    comp.log = _clean(total)
    if statistics is not None:
        statistics.update(counters)
        statistics.update({"supports": len(comp.support_index), "distinct_keys": len(multiplicity)})
    return comp


# ---------------------------------------------------------------------------
# local changes


@dataclass(frozen=True)
class LocalChange:
    """An exact patch: ``kind`` 'edge' with ``target=(u, v)``, or 'pin' with ``target=v``.

    ``old`` must equal the current value when applied; otherwise the patch
    is stale and is rejected.
    """

    kind: str
    target: object
    old: int
    new: int

    def __post_init__(self):
        if not isinstance(self.kind, str):
            raise TypeError("kind must be a string")
        if self.kind == "edge":
            try:
                u, v = self.target
            except (TypeError, ValueError) as exc:
                raise ValueError("edge target must be a vertex pair") from exc
            u, v = _int(u, "endpoint", 0), _int(v, "endpoint", 0)
            if u == v:
                raise ValueError("loops are not allowed")
            object.__setattr__(self, "target", (min(u, v), max(u, v)))
        elif self.kind == "pin":
            _int(self.target, "vertex", 0)
        else:
            raise ValueError("kind must be 'edge' or 'pin'")
        _int(self.old, "old value", 0)
        _int(self.new, "new value", 0)

    @property
    def endpoints(self) -> tuple:
        return self.target if self.kind == "edge" else (self.target,)

    def inverse(self) -> "LocalChange":
        return LocalChange(self.kind, self.target, self.new, self.old)

    def to_json(self) -> dict:
        target = list(self.target) if self.kind == "edge" else self.target
        return {"kind": self.kind, "target": target, "old": self.old, "new": self.new}

    @classmethod
    def from_json(cls, data: Mapping) -> "LocalChange":
        if not isinstance(data, Mapping) or set(data) != {"kind", "target", "old", "new"}:
            raise ValueError("malformed change")
        target = tuple(data["target"]) if data["kind"] == "edge" else data["target"]
        return cls(data["kind"], target, data["old"], data["new"])


def edge_change(u: int, v: int, old: int, new: int) -> LocalChange:
    return LocalChange("edge", (u, v), old, new)


def pin_change(v: int, old: int, new: int) -> LocalChange:
    return LocalChange("pin", v, old, new)


def _series_json(series: Series) -> list:
    return [polynomial_to_json(p) for p in series]


def _series_from_json(data) -> Series:
    if not isinstance(data, list):
        raise ValueError("series must be a list")
    return [polynomial_from_json(p) for p in data]


def apply_local_changes(comp: LocalityCompilation, changes: Iterable[LocalChange], *, in_place: bool = False,
                        record: bool = True, statistics: dict | None = None):
    """Apply exact changes and return ``(compilation, update_record_or_None)``.

    All changes are validated against the current state before anything is
    modified (stale or duplicate patches raise ValueError and leave ``comp``
    untouched).  Affected supports are the connected sets of the union graph
    with at most R vertices meeting the endpoint set D; for each, the old and
    new decorated contributions are differenced (an absent side is zero).
    Work and adjacency reads are confined to the radius-(R-1) union
    neighbourhood of D, except that ``record=True`` stores the full baseline
    specification (O(n)).  ``in_place=False`` copies the state first (O(size)).
    """
    if not isinstance(comp, LocalityCompilation):
        raise TypeError("comp must be a LocalityCompilation")
    changes = tuple(changes)
    if not changes:
        raise ValueError("no changes supplied")
    targets = set()
    for ch in changes:
        if not isinstance(ch, LocalChange):
            raise TypeError("changes must be LocalChange values")
        if any(v >= comp.n for v in ch.endpoints):
            raise ValueError("change endpoint outside 0..n-1")
        if (ch.kind, ch.target) in targets:
            raise ValueError("a target may change at most once per batch")
        targets.add((ch.kind, ch.target))
        current = comp.weight(*ch.target) if ch.kind == "edge" else comp.pinning(ch.target)
        if current != ch.old:
            raise ValueError(f"stale patch {ch.to_json()}: current value is {current}")
    R = comp.max_volume
    counters: Counter = Counter()
    baseline = {"spec": comp.spec.to_json(), "log": _series_json(comp.log)} if record else None
    target = comp if in_place else comp.copy()
    adj = target._adj
    D = sorted({v for ch in changes for v in ch.endpoints})
    extra: dict[int, set] = {}
    for ch in changes:
        if ch.kind == "edge" and ch.new and not ch.old:
            u, v = ch.target
            extra.setdefault(u, set()).add(v)
            extra.setdefault(v, set()).add(u)
    union = lambda v: set(adj[v]) | extra.get(v, set())
    supports = list(connected_sets_meeting(union, D, R))
    counters["affected_supports"] = len(supports)
    old_keys = {S: target.support_index.get(S) for S in supports}
    union_edges = None
    if record:  # read before the adjacency is modified (deleted edges stay in the union)
        ball = set().union(*supports) if supports else set(D)
        union_edges = sorted({(min(u, v), max(u, v)) for u in ball for v in union(u) if v in ball})
    for ch in changes:
        if ch.kind == "edge":
            u, v = ch.target
            for a, b in ((u, v), (v, u)):
                if ch.new:
                    adj[a][b] = ch.new
                else:
                    adj[a].pop(b, None)
                target._deco[a] += ch.new - ch.old
        else:
            target._pin[ch.target] = ch.new
            target._deco[ch.target] += ch.new - ch.old
    delta = _zero_series(R)
    rows = []
    for S in supports:
        old_key = old_keys[S]
        new_key = target._key(S) if _is_connected(S, adj) else None
        old_phi = _phi(old_key, R, target.cache, counters) if old_key is not None else None
        new_phi = _phi(new_key, R, target.cache, counters) if new_key is not None else None
        if old_key != new_key:
            counters["supports_changed"] += 1
            if old_phi is not None:
                _accumulate(delta, old_phi, -1)
                counters["poly_adds"] += R + 1
            if new_phi is not None:
                _accumulate(delta, new_phi, 1)
                counters["poly_adds"] += R + 1
        if new_key is None:
            target.support_index.pop(S, None)
            counters["supports_removed"] += old_key is not None
        else:
            target.support_index[S] = new_key
            counters["supports_added"] += old_key is None
        if record:
            rows.append({"support": sorted(S),
                         "old": None if old_phi is None else _series_json(old_phi),
                         "new": None if new_phi is None else _series_json(new_phi)})
    _accumulate(delta, target.log, 1)
    target.log = _clean(delta)
    counters["poly_adds"] += R + 1
    if statistics is not None:
        statistics.update(counters)
    if not record:
        return target, None
    out = {"schema": SCHEMA, "convention": CONVENTION, "max_volume": R,
           "baseline": baseline, "changes": [ch.to_json() for ch in changes], "affected_endpoints": D,
           "declared_union_edges": [list(e) for e in union_edges],
           "supports": rows, "result_log": _series_json(target.log)}
    return target, out


# ---------------------------------------------------------------------------
# independent verification of an update record


def apply_changes_to_spec(spec: WeightedSpec, changes: Iterable[LocalChange]) -> WeightedSpec:
    """The changed specification, checking every old value (stale patches raise ValueError)."""
    weights = {(u, v): w for u, v, w in spec.weights}
    pins = list(spec.pinning)
    seen = set()
    for ch in changes:
        if not isinstance(ch, LocalChange):
            raise TypeError("changes must be LocalChange values")
        if (ch.kind, ch.target) in seen:
            raise ValueError("a target may change at most once per batch")
        seen.add((ch.kind, ch.target))
        if any(v >= spec.n for v in ch.endpoints):
            raise ValueError("change endpoint outside 0..n-1")
        if ch.kind == "edge":
            if weights.get(ch.target, 0) != ch.old:
                raise ValueError("stale patch")
            weights[ch.target] = ch.new
        else:
            if pins[ch.target] != ch.old:
                raise ValueError("stale patch")
            pins[ch.target] = ch.new
    return WeightedSpec(spec.n, [(u, v, w) for (u, v), w in weights.items()], pins, spec.energy_unit)


def verify_local_update(update: Mapping, *, oracle_budget: int = 0, ball_budget: int = 200_000) -> dict:
    """Replay a ``singularity.locality-update/1`` record without the incremental compiler.

    1. Rebuilds old/new specifications from the baseline and the changes
       (stale changes fail).
    2. Completeness: recomputes the union graph from the two specifications,
       takes every vertex within union distance R-1 of D, and checks by
       brute-force subsets plus a connectivity search that the listed
       supports are exactly the union-connected sets |S| <= R meeting D;
       the declared union edges must match.
    3. Recomputes each listed old/new contribution from its definition
       (``support_contribution_by_definition``), requiring ``None`` exactly
       when the support is disconnected in that version.
    4. Checks result_log = baseline log + sum(new - old).
    5. With ``oracle_budget > 0``, compares exp(baseline log) and exp(result
       log) against ``direct_series`` of the two specifications.

    Raises ValueError on any mismatch; returns counts of what was checked.
    The baseline log itself is trusted unless step 5 runs.
    """
    from itertools import combinations
    from math import comb

    if not isinstance(update, Mapping) or update.get("schema") != SCHEMA or update.get("convention") != CONVENTION:
        raise ValueError("not a locality-update/1 record")
    R = _int(update["max_volume"], "max_volume", 0)
    old_spec = WeightedSpec.from_json(update["baseline"]["spec"])
    changes = [LocalChange.from_json(c) for c in update["changes"]]
    new_spec = apply_changes_to_spec(old_spec, changes)
    D = sorted({v for ch in changes for v in ch.endpoints})
    if update["affected_endpoints"] != D:
        raise ValueError("affected endpoint set differs")
    old_adj = {v: set() for v in range(old_spec.n)}
    new_adj = {v: set() for v in range(old_spec.n)}
    for spec, adj in ((old_spec, old_adj), (new_spec, new_adj)):
        for u, v, _ in spec.weights:
            adj[u].add(v)
            adj[v].add(u)
    union = {v: old_adj[v] | new_adj[v] for v in old_adj}
    dist = {d: 0 for d in D}
    frontier = list(D)
    while frontier:
        nxt = []
        for u in frontier:
            if dist[u] >= R - 1:
                continue
            for w in union[u]:
                if w not in dist:
                    dist[w] = dist[u] + 1
                    nxt.append(w)
        frontier = nxt
    ball = sorted(dist)
    cost = sum(comb(len(ball), k) for k in range(1, R + 1))
    if cost > ball_budget:
        raise ValueError(f"completeness check needs {cost} subsets; budget is {ball_budget}")
    expected = set()
    Dset = set(D)
    for k in range(1, R + 1):
        for S in combinations(ball, k):
            S = frozenset(S)
            if S & Dset and _is_connected(S, union):
                expected.add(S)
    listed = [frozenset(row["support"]) for row in update["supports"]]
    if len(set(listed)) != len(listed) or set(listed) != expected:
        raise ValueError("affected support list is not exactly the union-connected sets meeting D")
    support_ball = set().union(*expected) if expected else set(D)
    declared = sorted({(min(u, v), max(u, v)) for u in support_ball for v in union[u] if v in support_ball})
    if [list(e) for e in declared] != update["declared_union_edges"]:
        raise ValueError("declared union edges differ")
    delta = _zero_series(R)
    for row in update["supports"]:
        S = frozenset(row["support"])
        for side, spec, adj in (("old", old_spec, old_adj), ("new", new_spec, new_adj)):
            phi = support_contribution_by_definition(spec, S, R)
            connected = _is_connected(S, adj)
            if not connected and any(phi):
                raise ValueError("a disconnected support has a nonzero contribution")
            if (row[side] is None) == connected:
                raise ValueError(f"{side} side presence disagrees with connectivity of {sorted(S)}")
            if row[side] is not None and _series_from_json(row[side]) != phi:
                raise ValueError(f"{side} contribution of {sorted(S)} differs from its definition")
            delta = [add(a, scale(b, 1 if side == "new" else -1)) for a, b in zip(delta, phi)]
    base_log = _series_from_json(update["baseline"]["log"])
    result = _series_from_json(update["result_log"])
    if len(base_log) != R + 1 or [normalize(add(a, b)) for a, b in zip(base_log, delta)] != result:
        raise ValueError("result log differs from baseline plus listed corrections")
    summary = {"supports": len(listed), "ball_vertices": len(ball), "subsets_examined": cost, "oracle": False}
    if oracle_budget:
        if series_from_log(base_log) != direct_series(old_spec, R, oracle_budget):
            raise ValueError("baseline log disagrees with direct enumeration")
        if series_from_log(result) != direct_series(new_spec, R, oracle_budget):
            raise ValueError("updated log disagrees with direct enumeration")
        summary["oracle"] = True
    return summary


# ---------------------------------------------------------------------------
# measurement helpers


def coefficient_bits(series: Series) -> dict:
    """Largest numerator/denominator bit lengths and total bits of a series."""
    num = den = total = 0
    for poly in series:
        for c in poly.values():
            c = Fraction(c)
            num = max(num, abs(c.numerator).bit_length())
            den = max(den, c.denominator.bit_length())
            total += abs(c.numerator).bit_length() + c.denominator.bit_length()
    return {"max_numerator_bits": num, "max_denominator_bits": den, "total_bits": total}
