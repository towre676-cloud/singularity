"""Original-object Boolean fault populations and exact edge-removal physics."""
from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from hashlib import sha256
import json
from .thermal_diagnostics import AffineCandidate, build_plate_candidates


def _integer(x, name="integer"):
    if isinstance(x, bool) or not isinstance(x, int):
        raise TypeError(f"{name} must be an int")
    return x


class FaultPopulation:
    """Lexicographic Boolean masks satisfying integer inequalities R theta<=b.

    A memoized prefix may represent many original masks. Completion counts,
    rank/unrank and conditioning always retain those original multiplicities.
    """
    def __init__(self, bond_ids, constraints=(), *, max_faults=None, max_states=100000,
                 source_model_digest=None):
        self.bond_ids = tuple(bond_ids)
        if len(set(self.bond_ids)) != len(self.bond_ids):
            raise ValueError("bond IDs must be distinct")
        self.max_states = _integer(max_states, "max_states")
        if self.max_states < 1:
            raise ValueError("positive state budget required")
        n = len(self.bond_ids)
        rows = []
        for row, bound in constraints:
            row = tuple(_integer(x, "constraint coefficient") for x in row)
            if len(row) != n:
                raise ValueError("constraint dimension mismatch")
            rows.append((row, _integer(bound, "constraint bound")))
        if max_faults is not None:
            if _integer(max_faults, "max_faults") < 0:
                raise ValueError("max_faults must be nonnegative")
            rows.append(((1,)*n, max_faults))
        self.constraints = tuple(rows)
        if source_model_digest is not None and (not isinstance(source_model_digest,str) or not source_model_digest):
            raise ValueError("source digest must be a nonempty string when supplied")
        self.source_model_digest=source_model_digest
        self._states = 0

        @lru_cache(None)
        def completions(position, residual):
            self._states += 1
            if self._states > self.max_states:
                raise ValueError("fault completion-state budget exceeded")
            if any(sum(min(0, a) for a in row[position:]) > remaining
                   for (row, _), remaining in zip(self.constraints, residual)):
                return 0
            if position == n:
                return 1
            return completions(position+1, residual)+completions(position+1,
                tuple(r-row[position] for (row, _), r in zip(self.constraints, residual)))
        self._completions = completions

    def _prefix(self, prefix):
        prefix = tuple(prefix)
        if len(prefix) > len(self.bond_ids) or any(type(x) is not int or x not in (0, 1) for x in prefix):
            raise ValueError("prefix must contain Boolean integers within the domain")
        return prefix

    def count(self, prefix=()):
        prefix = self._prefix(prefix)
        residual = tuple(b-sum(a*x for a, x in zip(row, prefix)) for row, b in self.constraints)
        return self._completions(len(prefix), residual)

    @property
    def completion_states(self):
        return self._states

    def rank(self, mask):
        mask = self._prefix(mask)
        if len(mask) != len(self.bond_ids) or not self.count(mask):
            raise ValueError("mask is not a feasible original configuration")
        rank, prefix = 0, ()
        for bit in mask:
            if bit:
                rank += self.count(prefix+(0,))
            prefix += (bit,)
        return rank

    def unrank(self, index):
        index = _integer(index, "rank")
        if not 0 <= index < self.count():
            raise ValueError("rank outside original population")
        prefix = ()
        while len(prefix) < len(self.bond_ids):
            left = self.count(prefix+(0,))
            if index < left:
                prefix += (0,)
            else:
                index -= left
                prefix += (1,)
        return prefix

    def iterate_masks(self, *, max_masks=100000):
        if self.count() > max_masks:
            raise ValueError("mask enumeration budget exceeded")
        for i in range(self.count()):
            yield self.unrank(i)

    def condition(self, predicate, *, max_masks=100000):
        return ConditionedFaultPopulation(self, tuple(mask for mask in self.iterate_masks(max_masks=max_masks)
                                                     if predicate(mask)))

    def manifest(self):
        return {"schema": "singularity.fault-population/1", "bond_ids": self.bond_ids,
                "source_model_digest":self.source_model_digest,
                "constraints": self.constraints, "ordering": "lexicographic-original-masks",
                "count": self.count(), "completion_states": self.completion_states}


class ConditionedFaultPopulation:
    def __init__(self, parent, masks):
        self.parent, self.masks = parent, tuple(masks)
        self.bond_ids = parent.bond_ids

    def count(self, prefix=()):
        prefix = self.parent._prefix(prefix)
        return sum(mask[:len(prefix)] == prefix for mask in self.masks)

    def rank(self, mask):
        try:
            return self.masks.index(tuple(mask))
        except ValueError:
            raise ValueError("mask absent from conditioned original population") from None

    def unrank(self, index):
        if type(index) is not int or not 0 <= index < len(self.masks):
            raise ValueError("rank out of range")
        return self.masks[index]

    def iterate_masks(self, **kwargs):
        return iter(self.masks)


def plate_bonds(grid):
    if _integer(grid, "grid") < 2:
        raise ValueError("grid must be at least two")
    return tuple(sorted((r*grid+c, rr*grid+cc)
        for r in range(grid) for c in range(grid)
        for rr, cc in ((r+1, c), (r, c+1)) if rr < grid and cc < grid))


def plate_nominal(grid=12):
    if grid >= 4 and grid % 2 == 0:
        return build_plate_candidates(grid)[0]
    if grid != 2:
        raise ValueError("supported nominal grids are 2 or positive even sizes >=4")
    n, k, loss = 4, Fraction(1, 8), Fraction(1, 100)
    entries = {(i, i): 1-loss for i in range(n)}
    for a, b in plate_bonds(grid):
        entries[a, a] -= k; entries[b, b] -= k
        entries[a, b] = k; entries[b, a] = k
    return AffineCandidate("nominal", n, tuple((i, j, x) for (i, j), x in entries.items()),
                           (Fraction(1, 4),)*4,
                           ((Fraction(1, 4),)*4, (Fraction(1), 0, 0, 0),
                            (0, Fraction(1), 0, 0), (0, 0, Fraction(1), 0)))


def fault_candidate(source, mask, bond_ids, *, conductance=Fraction(1, 8)):
    if not isinstance(source, AffineCandidate):
        raise TypeError("source must be AffineCandidate")
    bond_ids, mask = tuple(bond_ids), tuple(mask)
    if len(bond_ids) != len(mask) or any(type(x) is not int or x not in (0, 1) for x in mask):
        raise ValueError("one Boolean mask bit per bond required")
    if isinstance(conductance, bool) or not isinstance(conductance, (int, Fraction)):
        raise TypeError("exact conductance required")
    conductance = Fraction(conductance)
    if conductance < 0:
        raise ValueError("conductance must be nonnegative")
    canonical = tuple(tuple(sorted(bond)) for bond in bond_ids)
    if len(set(canonical)) != len(canonical) or any(len(b) != 2 or b[0] == b[1] or
            any(type(i) is not int or not 0 <= i < source.dimension for i in b) for b in canonical):
        raise ValueError("distinct valid undirected bonds required")
    entries = {(i, j): v for i, j, v in source.entries}
    for bit, (a, b) in zip(mask, canonical):
        if bit:
            if entries.get((a, b), 0) != conductance or entries.get((b, a), 0) != conductance:
                raise ValueError("fault bond must have the declared nominal conductance")
            entries[a, b] -= conductance; entries[b, a] -= conductance
            entries[a, a] += conductance; entries[b, b] += conductance
    return AffineCandidate(source.identifier+":mask:"+"".join(map(str, mask)), source.dimension,
                           tuple((i, j, x) for (i, j), x in entries.items()), source.heater, source.sensors)


# Frozen explicit row-major twelve-bond catalogue, intentionally not computed
# from another module's iteration order. Its original labels are never quotiented.
PILOT_BONDS_12 = ((0, 1), (0, 12), (1, 2), (1, 13), (2, 3), (2, 14),
                  (3, 4), (3, 15), (4, 5), (4, 16), (5, 6), (5, 17))


def pilot_fault_candidates(grid=12):
    """Return (population, all original compatible models), cardinality 79."""
    bonds = PILOT_BONDS_12 if grid == 12 else plate_bonds(grid)[:12]
    source = plate_nominal(grid)
    payload=json.dumps({'dimension':source.dimension,'entries':source.entries,
                        'heater':source.heater,'sensors':source.sensors},default=str,sort_keys=True)
    population = FaultPopulation(bonds, max_faults=2,
                                 source_model_digest=sha256(payload.encode()).hexdigest())
    return population, tuple(fault_candidate(source, mask, bonds) for mask in population.iterate_masks())
