"""Original-world finite histories and exact latent-polytope conditioning."""
from dataclasses import dataclass, replace
from fractions import Fraction
from .joint_uncertainty import _q, _dot, rational_feasibility


@dataclass(frozen=True)
class HistoryWorld:
    original_id: str
    target: object
    state: object


@dataclass(frozen=True)
class HistoryBelief:
    worlds: tuple
    transcript: tuple = ()

    @property
    def targets(self):
        return tuple(sorted({w.target for w in self.worlds}, key=repr))


@dataclass(frozen=True)
class HistoryModel:
    initial_worlds: tuple
    actions: tuple
    transitions: dict
    measurements: dict
    action_costs: tuple
    measurement_costs: tuple
    reset_semantics: tuple = ()

    def __post_init__(self):
        if not self.initial_worlds or any(not isinstance(w, HistoryWorld) for w in self.initial_worlds):
            raise ValueError("explicit original worlds required")
        if len({w.original_id for w in self.initial_worlds}) != len(self.initial_worlds):
            raise ValueError("original IDs must be distinct initially")
        if len(set(self.actions)) != len(self.actions):
            raise ValueError("action identifiers must be distinct")
        ac = tuple(_q(x) for x in self.action_costs)
        mc = tuple(_q(x) for x in self.measurement_costs)
        if len(ac) != len(self.actions) or len(mc) != len(self.measurements) or min(ac+mc, default=1) <= 0:
            raise ValueError("positive declared action and observation costs required")
        object.__setattr__(self, "action_costs", ac)
        object.__setattr__(self, "measurement_costs", mc)


class InfeasibleHistoryAction(ValueError):
    pass


def advance_belief(model, belief, action):
    if action not in model.actions:
        raise InfeasibleHistoryAction("unknown action")
    result = []
    for world in belief.worlds:
        key = (world.original_id, world.state, action)
        if key not in model.transitions or not model.transitions[key]:
            raise InfeasibleHistoryAction("action illegal in a currently possible original world")
        result.extend(HistoryWorld(world.original_id, world.target, state)
                      for state in model.transitions[key])
    unique = tuple(sorted(set(result), key=repr))
    return HistoryBelief(unique, belief.transcript+(("action", action),))


def condition_belief(model, belief, channel, observation):
    if channel not in model.measurements:
        raise ValueError("unknown measurement channel")
    mapping = model.measurements[channel]
    worlds = tuple(world for world in belief.worlds if
                   mapping[(world.original_id, world.state)] == observation)
    return HistoryBelief(worlds, belief.transcript+(("observation", channel, observation),))


def history_policy_search(model, *, horizon=6, max_states=100000):
    """Complete bounded-horizon minimax search on finite original worlds."""
    if type(horizon) is not int or horizon < 0 or type(max_states) is not int or max_states < 1:
        raise ValueError("finite nonnegative horizon and positive work budget required")
    cache = {}
    channels = tuple(model.measurements)
    def solve(worlds, remaining):
        key = (worlds, remaining)
        if key in cache:
            return cache[key]
        if len(cache) >= max_states:
            raise ValueError("history policy state budget exceeded")
        cache[key] = None
        targets = {w.target for w in worlds}
        if len(targets) == 1:
            node = {"worlds": worlds, "kind": "leaf", "target": next(iter(targets)), "cost": Fraction(0)}
            cache[key] = node
            return node
        if remaining == 0:
            return None
        best = None
        for i, action in enumerate(model.actions):
            try:
                child_belief = advance_belief(model, HistoryBelief(worlds), action)
            except InfeasibleHistoryAction:
                continue
            child = solve(child_belief.worlds, remaining-1)
            if child is not None:
                cost = model.action_costs[i]+child["cost"]
                if best is None or cost < best["cost"]:
                    best = {"worlds": worlds, "kind": "action", "action": action,
                            "child": child, "cost": cost}
        for i, channel in enumerate(channels):
            values = sorted({model.measurements[channel][(w.original_id, w.state)] for w in worlds}, key=repr)
            children = []
            for value in values:
                belief = condition_belief(model, HistoryBelief(worlds), channel, value)
                child = solve(belief.worlds, remaining-1)
                if child is None:
                    break
                children.append((value, child))
            else:
                cost = model.measurement_costs[i]+max(c["cost"] for _, c in children)
                if best is None or cost < best["cost"]:
                    best = {"worlds": worlds, "kind": "observe", "channel": channel,
                            "branches": tuple(children), "cost": cost}
        cache[key] = best
        return best
    root = solve(tuple(model.initial_worlds), horizon)
    return {"schema": "singularity.history-policy/1", "semantics": "exact-finite-worlds",
            "status": "optimal-within-horizon" if root else "impossible-within-horizon",
            "horizon": horizon, "root": root, "cost": root["cost"] if root else None,
            "states": len(cache)}


def verify_history_policy(model, certificate):
    if (not isinstance(certificate,dict) or certificate.get("schema") != "singularity.history-policy/1" or
            certificate.get("semantics") != "exact-finite-worlds" or
            certificate.get("status") not in ("optimal-within-horizon","impossible-within-horizon")):
        return False
    active = set()
    def check(node, worlds, remaining):
        if not isinstance(node, dict) or remaining < 0 or id(node) in active or node.get("worlds") != worlds:
            return None
        active.add(id(node))
        try:
            if node["kind"] == "leaf":
                targets = {w.target for w in worlds}
                return Fraction(0) if targets == {node["target"]} and node["cost"] == 0 else None
            if node["kind"] == "action":
                action = node["action"]
                belief = advance_belief(model, HistoryBelief(worlds), action)
                child = check(node["child"], belief.worlds, remaining-1)
                cost = None if child is None else model.action_costs[model.actions.index(action)]+child
            elif node["kind"] == "observe":
                channel = node["channel"]
                values = sorted({model.measurements[channel][(w.original_id, w.state)] for w in worlds}, key=repr)
                if tuple(v for v, _ in node["branches"]) != tuple(values):
                    return None
                costs = []
                for value, child in node["branches"]:
                    belief = condition_belief(model, HistoryBelief(worlds), channel, value)
                    value_cost = check(child, belief.worlds, remaining-1)
                    if value_cost is None:
                        return None
                    costs.append(value_cost)
                cost = model.measurement_costs[tuple(model.measurements).index(channel)]+max(costs)
            else:
                return None
            return cost if cost == node["cost"] else None
        finally:
            active.remove(id(node))
    try:
        if certificate["status"] == "impossible-within-horizon":
            return (certificate.get("root") is None and certificate.get("cost") is None and
                    history_policy_search(model,horizon=certificate["horizon"])["status"] ==
                    "impossible-within-horizon")
        value = check(certificate["root"], tuple(model.initial_worlds), certificate["horizon"])
        return (value is not None and value == certificate["cost"] and
                history_policy_search(model,horizon=certificate["horizon"])["cost"] == value)
    except (KeyError, ValueError, TypeError, IndexError):
        return False


@dataclass(frozen=True)
class AffineHistoryWorld:
    """x=center+generators*z; inequalities retain every previous observation.

    Latent coordinates are shared through time within this original world.
    Different candidate worlds never share the actual latent value.
    """
    original_id: str
    target: object
    center: tuple
    generators: tuple
    inequalities: tuple
    latent_labels: tuple
    transcript: tuple = ()

    def __post_init__(self):
        center = tuple(_q(x) for x in self.center)
        g = tuple(tuple(_q(x) for x in row) for row in self.generators)
        if len(g) != len(center) or any(len(row) != len(self.latent_labels) for row in g):
            raise ValueError("affine state dimensions mismatch")
        rows = tuple((tuple(_q(x) for x in a), _q(b)) for a, b in self.inequalities)
        if len(set(self.latent_labels)) != len(self.latent_labels) or any(len(a) != len(self.latent_labels) for a, _ in rows):
            raise ValueError("latent labels/constraint dimensions invalid")
        object.__setattr__(self, "center", center)
        object.__setattr__(self, "generators", g)
        object.__setattr__(self, "inequalities", rows)


def latent_box_world(identifier, target, center, generators, latent_labels):
    n = len(latent_labels)
    inequalities = []
    for i in range(n):
        unit = tuple(Fraction(int(i == j)) for j in range(n))
        inequalities.extend(((unit, Fraction(1)), (tuple(-x for x in unit), Fraction(1))))
    return AffineHistoryWorld(identifier, target, tuple(center), tuple(generators),
                              tuple(inequalities), tuple(latent_labels))


def affine_advance(world, candidate, amplitude, *, heater_generators=None):
    amplitude = _q(amplitude)
    m = len(world.latent_labels)
    if candidate.dimension != len(world.center):
        raise ValueError("dynamics/state dimension mismatch")
    hg = tuple(tuple(_q(x) for x in row) for row in heater_generators) if heater_generators is not None else (
        (Fraction(0),)*m,)*candidate.dimension
    if len(hg) != candidate.dimension or any(len(row) != m for row in hg):
        raise ValueError("heater latent dimensions mismatch")
    center = candidate.step(world.center, amplitude)
    generators = [[amplitude*x for x in row] for row in hg]
    for i, j, value in candidate.entries:
        for t in range(m):
            generators[i][t] += value*world.generators[j][t]
    return replace(world, center=center, generators=tuple(tuple(row) for row in generators),
                   transcript=world.transcript+(("control", amplitude),))


def affine_condition(world, sensor, observation, *, error=0, max_rows=20000):
    """Intersect with |C x-y|<=error; fresh error is existential per reading.

    Bounded independent sensor errors can be eliminated immediately into two
    inequalities. The persistent state/calibration latents remain shared.
    """
    sensor = tuple(_q(x) for x in sensor)
    observation, error = _q(observation), _q(error)
    if len(sensor) != len(world.center) or error < 0:
        raise ValueError("sensor dimension/error invalid")
    row = tuple(sum((sensor[i]*world.generators[i][j] for i in range(len(sensor))), Fraction(0))
                for j in range(len(world.latent_labels)))
    residual = observation-_dot(sensor, world.center)
    inequalities = world.inequalities+((row, residual+error), (tuple(-x for x in row), -residual+error))
    feasibility = rational_feasibility(inequalities, len(world.latent_labels), max_rows=max_rows)
    if not feasibility["feasible"]:
        return None, feasibility
    return replace(world, inequalities=inequalities,
                   transcript=world.transcript+(("observe", sensor, observation, error),)), feasibility


def affine_reset(world, center, generators, *, fresh_labels=()):
    """Replace current state, retain original ID and prior persistent constraints.

    Existing latent columns persist. Fresh reset-local columns are appended
    with independent [-1,1] constraints and must have unique labels.
    """
    labels = world.latent_labels+tuple(fresh_labels)
    if len(set(labels)) != len(labels):
        raise ValueError("fresh reset labels must be new")
    added = len(fresh_labels)
    inequalities = tuple((a+(Fraction(0),)*added, b) for a, b in world.inequalities)
    for j in range(len(world.latent_labels), len(labels)):
        unit = tuple(Fraction(int(j == i)) for i in range(len(labels)))
        inequalities += ((unit, Fraction(1)), (tuple(-x for x in unit), Fraction(1)))
    return AffineHistoryWorld(world.original_id, world.target, tuple(center), tuple(generators),
        inequalities, labels, world.transcript+(("reset", tuple(fresh_labels)),))
