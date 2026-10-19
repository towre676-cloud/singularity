"""Independent reference oracles for candidate-specific box panels (NX01).

These functions take raw exact data (costs, readings[e][c], radii[e][c],
target labels) and never call :mod:`singularity.candidate_boxes`.  They test
separation by direct closed-interval endpoint comparisons rather than the
production margin ``|r_a - r_b| > rho_a + rho_b``:

* ``exhaustive_box_panel`` scans every subset of the pool and asks whether
  the two candidates' product boxes over the subset intersect, coordinate by
  coordinate (``max(lower) <= min(upper)``).
* ``cost_bounded_box_panel`` scans every subset whose total cost is at
  most a declared bound, with the same box-intersection test; it is the
  affordable exhaustive check for large pools with positive costs.
* ``cover_state_dijkstra`` runs Dijkstra's algorithm on reached subsets of
  separated pairs; an edge adds one experiment's separated-pair set.

Both are worst-case exponential and budgeted.  An exceeded budget raises
ValueError; it is a refusal, not infeasibility.
"""
from __future__ import annotations

from fractions import Fraction
import heapq

__all__ = ["exhaustive_box_panel", "cost_bounded_box_panel", "cover_state_dijkstra"]


def _raw(costs, readings, radii, targets):
    costs = [Fraction(c) for c in costs]
    readings = [[Fraction(x) for x in row] for row in readings]
    radii = [[Fraction(x) for x in row] for row in radii]
    targets = list(targets)
    if len(readings) != len(costs) or len(radii) != len(costs):
        raise ValueError("one reading row and one radius row per experiment")
    k = len(targets)
    if any(len(row) != k for row in readings) or any(len(row) != k for row in radii):
        raise ValueError("rows need one entry per candidate")
    lower = [[r - h for r, h in zip(rr, hh)] for rr, hh in zip(readings, radii)]
    upper = [[r + h for r, h in zip(rr, hh)] for rr, hh in zip(readings, radii)]
    pairs = [(a, b) for a in range(k) for b in range(a + 1, k) if targets[a] != targets[b]]
    return costs, lower, upper, pairs


def exhaustive_box_panel(costs, readings, radii, targets, max_subsets=2**16):
    """Return (feasible, cost, members, subsets_scanned) by full subset scan.

    A subset is admissible when, for every pair with different targets, the
    two product boxes over the subset are disjoint."""
    costs, lower, upper, pairs = _raw(costs, readings, radii, targets)
    n = len(costs)
    if 2 ** n > max_subsets:
        raise ValueError("exhaustive box search exceeds max_subsets")

    def boxes_meet(members, a, b):
        return all(max(lower[e][a], lower[e][b]) <= min(upper[e][a], upper[e][b]) for e in members)

    best = None
    for subset in range(2 ** n):
        members = [e for e in range(n) if subset >> e & 1]
        if any(boxes_meet(members, a, b) for a, b in pairs):
            continue
        cost = sum((costs[e] for e in members), Fraction(0))
        if best is None or cost < best[0]:
            best = (cost, tuple(members))
    if best is None:
        return False, None, None, 2 ** n
    return True, best[0], best[1], 2 ** n


def cost_bounded_box_panel(costs, readings, radii, targets, bound, max_subsets=10**6):
    """Return (feasible_within_bound, cost, members, subsets_scanned).

    Enumerates every subset with total cost <= ``bound`` (depth-first over
    experiments sorted by cost) and keeps the cheapest separating one.  If
    none exists, no separating panel of cost <= bound exists in the pool.
    Exceeding ``max_subsets`` raises ValueError."""
    costs, lower, upper, pairs = _raw(costs, readings, radii, targets)
    bound = Fraction(bound)
    order = sorted(range(len(costs)), key=lambda e: (costs[e], e))
    state = {"best": None, "scanned": 0}

    def separating(members):
        return all(any(max(lower[e][a], lower[e][b]) > min(upper[e][a], upper[e][b]) for e in members)
                   for a, b in pairs)

    def walk(start, members, cost):
        state["scanned"] += 1
        if state["scanned"] > max_subsets:
            raise ValueError("cost-bounded box search exceeds max_subsets")
        if separating(members):
            best = state["best"]
            if best is None or cost < best[0] or (cost == best[0] and sorted(members) < best[1]):
                state["best"] = (cost, sorted(members))
        for i in range(start, len(order)):
            e = order[i]
            if cost + costs[e] > bound:
                break
            members.append(e)
            walk(i + 1, members, cost + costs[e])
            members.pop()

    walk(0, [], Fraction(0))
    best = state["best"]
    if best is None:
        return False, None, None, state["scanned"]
    return True, best[0], tuple(best[1]), state["scanned"]


def cover_state_dijkstra(costs, readings, radii, targets, max_states=2**20):
    """Return (cost, members, settled) for the cheapest pair cover, or
    (None, None, settled) when the full cover state is unreachable.

    Repeating an experiment never enlarges a covered-pair set, so the
    cheapest path to the full state uses distinct experiments and equals the
    cheapest subset cover (with nonnegative costs)."""
    costs, lower, upper, pairs = _raw(costs, readings, radii, targets)
    masks = []
    for e in range(len(costs)):
        mask = 0
        for bit, (a, b) in enumerate(pairs):
            if upper[e][a] < lower[e][b] or upper[e][b] < lower[e][a]:
                mask |= 1 << bit
        masks.append(mask)
    full = (1 << len(pairs)) - 1
    dist = {0: Fraction(0)}
    back = {0: None}
    queue = [(Fraction(0), 0)]
    settled = 0
    while queue:
        cost, state = heapq.heappop(queue)
        if dist[state] != cost:
            continue
        settled += 1
        if settled > max_states:
            raise ValueError("cover-state search exceeds max_states")
        if state == full:
            members, s = [], state
            while back[s] is not None:
                s, e = back[s]
                members.append(e)
            return cost, tuple(sorted(members)), settled
        for e, (price, mask) in enumerate(zip(costs, masks)):
            nxt = state | mask
            new = cost + price
            if nxt != state and (nxt not in dist or new < dist[nxt]):
                dist[nxt] = new
                back[nxt] = (state, e)
                heapq.heappush(queue, (new, nxt))
    return None, None, settled
