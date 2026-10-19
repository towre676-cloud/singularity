"""Exact worst-case adaptive policies for independent adversarial reset errors."""
from dataclasses import dataclass
from fractions import Fraction
from .joint_uncertainty import _q


@dataclass(frozen=True)
class ResetExperimentFamily:
    candidate_ids: tuple
    experiment_ids: tuple
    costs: tuple
    intervals: tuple
    targets: tuple = ()

    def __post_init__(self):
        k, e = len(self.candidate_ids), len(self.experiment_ids)
        costs = tuple(_q(x) for x in self.costs)
        intervals = tuple(tuple(tuple(_q(x) for x in pair) for pair in row) for row in self.intervals)
        if k < 1 or len(set(self.candidate_ids)) != k or len(set(self.experiment_ids)) != e:
            raise ValueError("distinct identifiers required")
        if len(costs) != e or any(x <= 0 for x in costs) or len(intervals) != e:
            raise ValueError("one positive cost and interval row per experiment required")
        if any(len(row) != k or any(len(pair) != 2 or pair[0] > pair[1] for pair in row)
               for row in intervals):
            raise ValueError("closed interval dimensions or order invalid")
        targets = tuple(self.targets or self.candidate_ids)
        if len(targets) != k:
            raise ValueError("one target per original candidate required")
        object.__setattr__(self, "costs", costs)
        object.__setattr__(self, "intervals", intervals)
        object.__setattr__(self, "targets", targets)


def observation_cells(family, experiment, belief=None):
    """Singleton endpoints and open cells, including model-rejection rays."""
    if type(experiment) is not int or not 0 <= experiment < len(family.costs):
        raise ValueError("experiment out of range")
    belief = tuple(range(len(family.candidate_ids))) if belief is None else tuple(belief)
    if len(set(belief)) != len(belief) or any(type(i) is not int or not 0 <= i < len(family.candidate_ids)
                                            for i in belief):
        raise ValueError("invalid original-candidate belief")
    endpoints = sorted({value for c in belief for value in family.intervals[experiment][c]})
    if not endpoints:
        return ()
    specs = [(None, endpoints[0], False, False, endpoints[0]-1)]
    for i, endpoint in enumerate(endpoints):
        specs.append((endpoint, endpoint, True, True, endpoint))
        if i+1 < len(endpoints):
            specs.append((endpoint, endpoints[i+1], False, False, (endpoint+endpoints[i+1])/2))
    specs.append((endpoints[-1], None, False, False, endpoints[-1]+1))
    return tuple({"lower": lo, "upper": hi, "lower_closed": lc, "upper_closed": uc,
                  "representative": sample,
                  "candidates": tuple(c for c in belief if family.intervals[experiment][c][0]
                                      <= sample <= family.intervals[experiment][c][1])}
                 for lo, hi, lc, uc, sample in specs)


def _terminal(family, belief):
    return len({family.targets[c] for c in belief}) <= 1


def minimum_reset_policy(family, *, max_beliefs=100000):
    """Complete Bellman solve over proper policies; no branch may retain S.

    Under independent per-reset adversarial errors, a same-belief branch lets
    the adversary repeat forever. Positive costs make that action unnecessary
    in every finite optimum. Strictly shrinking policies have depth <=K-1.
    """
    if type(max_beliefs) is not int or max_beliefs < 1:
        raise ValueError("positive belief budget required")
    table = {}
    transitions = 0

    def solve(belief):
        nonlocal transitions
        if belief in table:
            return table[belief]
        if len(table) >= max_beliefs:
            raise ValueError("adaptive policy belief budget exceeded")
        if _terminal(family, belief):
            node = {"candidates": belief, "target": family.targets[belief[0]] if belief else None,
                    "cost": Fraction(0), "experiment": None, "branches": ()}
            table[belief] = node
            return node
        # Reserve this strictly shrinking state before recursing.
        table[belief] = None
        best = None
        for experiment in range(len(family.costs)):
            cells = observation_cells(family, experiment, belief)
            children = sorted({cell["candidates"] for cell in cells if cell["candidates"]})
            transitions += len(children)
            if belief in children:
                continue
            child_nodes = {child: solve(child) for child in children}
            if any(node is None for node in child_nodes.values()):
                continue
            cost = family.costs[experiment]+max((node["cost"] for node in child_nodes.values()), default=0)
            if best is None or (cost, experiment) < (best["cost"], best["experiment"]):
                best = {"candidates": belief, "cost": cost, "experiment": experiment,
                        "branches": tuple(dict(cell, child=child_nodes[cell["candidates"]])
                                          for cell in cells if cell["candidates"])}
        table[belief] = best
        return best

    root = solve(tuple(range(len(family.candidate_ids))))
    return {"schema": "singularity.reset-policy/1", "uncertainty_semantics":
            "independent-adversarial-per-reset", "status": "optimal" if root else "impossible",
            "root": root, "cost": root["cost"] if root else None,
            "beliefs": len(table), "transitions": transitions,
            "bellman_values": tuple((belief, None if node is None else node["cost"])
                                    for belief, node in sorted(table.items()))}


def verify_reset_policy(family, certificate):
    """Check all continuous branches and every exact path cost independently."""
    if (not isinstance(certificate,dict) or certificate.get("schema") != "singularity.reset-policy/1" or
            certificate.get("status") not in ("optimal","impossible") or
            certificate.get("uncertainty_semantics") != "independent-adversarial-per-reset"):
        return False
    active = set()

    def check(node, belief):
        if not isinstance(node, dict) or id(node) in active or tuple(node.get("candidates", ())) != belief:
            return None
        active.add(id(node))
        try:
            if node.get("experiment") is None:
                return Fraction(0) if _terminal(family, belief) and node.get("cost") == 0 and (
                    not belief or node.get("target") == family.targets[belief[0]]) else None
            experiment = node["experiment"]
            cells = [c for c in observation_cells(family, experiment, belief) if c["candidates"]]
            branches = node["branches"]
            if len(branches) != len(cells):
                return None
            costs = []
            for cell, branch in zip(cells, branches):
                if any(branch.get(k) != value for k, value in cell.items()):
                    return None
                if cell["candidates"] == belief:
                    return None
                value = check(branch["child"], cell["candidates"])
                if value is None:
                    return None
                costs.append(value)
            cost = family.costs[experiment]+max(costs)
            return cost if node.get("cost") == cost else None
        finally:
            active.remove(id(node))
    try:
        if certificate.get("status") == "impossible":
            return (certificate.get("root") is None and certificate.get("cost") is None and
                    minimum_reset_policy(family)["status"] == "impossible")
        value = check(certificate["root"], tuple(range(len(family.candidate_ids))))
        return (value is not None and value == certificate.get("cost") and
                minimum_reset_policy(family)["cost"] == value)
    except (KeyError, ValueError, TypeError, IndexError, RecursionError):
        return False


def replay_policy(family, policy, observations):
    node, cost, transcript = policy["root"], Fraction(0), []
    if node is None:
        return {"status": "impossible"}
    values = iter(observations)
    while node["experiment"] is not None:
        experiment = node["experiment"]
        try:
            y = _q(next(values))
        except StopIteration:
            return {"status": "incomplete", "candidates": node["candidates"], "cost": cost}
        cost += family.costs[experiment]
        belief = tuple(c for c in node["candidates"] if family.intervals[experiment][c][0]
                       <= y <= family.intervals[experiment][c][1])
        transcript.append((experiment, y, belief))
        if not belief:
            return {"status": "model_rejected", "cost": cost, "transcript": tuple(transcript)}
        matching = [branch for branch in node["branches"] if branch["candidates"] == belief]
        if not matching:
            raise ValueError("policy lacks a possible observation branch")
        node = matching[0]["child"]
    return {"status": "identified", "target": node["target"], "candidates": node["candidates"],
            "cost": cost, "transcript": tuple(transcript)}


def reset_family_from_diagnostics(diagnostic, *, targets=(), experiments=None):
    """Keep the exact retained costs/readings and candidate-specific bounds."""
    pool = diagnostic.pool
    indices = tuple(range(pool.size)) if experiments is None else tuple(experiments)
    return ResetExperimentFamily(diagnostic.candidate_ids, tuple(pool.labels[i] for i in indices),
        tuple(pool.costs[i] for i in indices),
        tuple(tuple((pool.readings[i][c]-diagnostic.error_bounds[i][c],
                     pool.readings[i][c]+diagnostic.error_bounds[i][c])
                    for c in range(pool.candidates)) for i in indices), tuple(targets))
