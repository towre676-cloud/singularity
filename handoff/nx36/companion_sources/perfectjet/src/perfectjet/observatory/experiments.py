"""Exact active experiments for finite partially observed deterministic systems.

The unknown target belongs to the *initial* state.  A destructive action may
merge current states, but it must never merge their initial target labels.
Adaptive policies are finite AND/OR policies, not a greedy information score.
"""
from __future__ import annotations

from collections import defaultdict, deque
import heapq
from typing import Any, Iterable

from .model import FiniteSystem, scalar_key


# A belief remembers every possible initial state and where it has moved.
Belief = tuple[tuple[int, int | None], ...]


def _state_index(system: FiniteSystem, state: int | str) -> int:
    if isinstance(state, str):
        try:
            return system.states.index(state)
        except ValueError as exc:
            raise ValueError(f"Unknown state: {state!r}") from exc
    if type(state) is not int or not 0 <= state < system.n:
        raise ValueError(f"State must be a state name or index in [0, {system.n}).")
    return state


def _observation_key(system: FiniteSystem, state: int | None) -> tuple:
    return ("undefined",) if state is None else ("live", scalar_key(system.observations[state]))


def _observation(system: FiniteSystem, state: int | None) -> dict[str, Any]:
    return {"kind": "undefined"} if state is None else {
        "kind": "live", "value": system.observations[state]
    }


def _step(system: FiniteSystem, state: int | None, action: int) -> int | None:
    return None if state is None else system.transitions[state][action]


def pair_experiment(system: FiniteSystem, x: int | str, y: int | str) -> dict[str, Any]:
    """Return a minimum-cost word distinguishing two current states.

    The current observation is free.  Undefined actions give a terminal
    observation distinct from every live observation, including a JSON null.
    Positive action costs make Dijkstra's algorithm exact.
    """
    start = (_state_index(system, x), _state_index(system, y))
    distance: dict[tuple[int | None, int | None], int] = {start: 0}
    parent: dict[tuple[int | None, int | None], tuple[tuple[int | None, int | None], int]] = {}
    serial = 0
    queue: list[tuple[int, int, tuple[int | None, int | None]]] = [(0, serial, start)]
    settled = 0
    while queue:
        cost, _, pair = heapq.heappop(queue)
        if distance[pair] != cost:
            continue
        settled += 1
        if _observation_key(system, pair[0]) != _observation_key(system, pair[1]):
            word: list[str] = []
            cursor = pair
            while cursor != start:
                previous, action = parent[cursor]
                word.append(system.actions[action])
                cursor = previous
            word.reverse()
            return {
                "status": "finite", "cost": cost, "word": word,
                "initial_states": [system.states[start[0]], system.states[start[1]]],
                "terminal_observations": [_observation(system, pair[0]), _observation(system, pair[1])],
                "settled_pairs": settled,
            }
        for action, action_cost in enumerate(system.costs):
            nxt = (_step(system, pair[0], action), _step(system, pair[1], action))
            candidate = cost + action_cost
            if candidate < distance.get(nxt, candidate + 1):
                distance[nxt] = candidate
                parent[nxt] = pair, action
                serial += 1
                heapq.heappush(queue, (candidate, serial, nxt))
    return {
        "status": "infinite", "cost": None, "word": None,
        "initial_states": [system.states[start[0]], system.states[start[1]]],
        "settled_pairs": settled,
        "reason": "The two states have identical observations under every finite action word.",
    }


def _target_key(system: FiniteSystem, belief: Belief) -> set[tuple]:
    return {scalar_key(system.targets[initial]) for initial, _ in belief}


def _describe_belief(system: FiniteSystem, belief: Belief) -> list[dict[str, Any]]:
    return [{
        "initial": system.states[initial],
        "current": None if current is None else system.states[current],
        "target": system.targets[initial],
    } for initial, current in belief]


def _branches(system: FiniteSystem, belief: Belief, action: int | None) -> list[tuple[dict[str, Any], Belief]]:
    grouped: dict[tuple, list[tuple[int, int | None]]] = {}
    observations: dict[tuple, dict[str, Any]] = {}
    for initial, current in belief:
        nxt = current if action is None else _step(system, current, action)
        key = _observation_key(system, nxt)
        grouped.setdefault(key, []).append((initial, nxt))
        observations[key] = _observation(system, nxt)
    return [(observations[key], tuple(candidates)) for key, candidates in grouped.items()]


def adaptive_experiment(
    system: FiniteSystem,
    belief: Iterable[int | str] | None = None,
    max_beliefs: int = 4096,
    prefix: Iterable[int | str] = (),
) -> dict[str, Any]:
    """Find an optimal finite adaptive experiment for the initial target.

    The objective is minimum worst-case sum of positive action costs.  Every
    next action may depend on the observation just received.  Reachable belief
    states are enumerated exactly, then an AND/OR Dijkstra retrograde pass
    finalizes the minimax value.  Unfinalized states form a closed losing region.

    ``tree`` is the free initial observation node. ``nodes`` encodes its finite
    decision tree as a shared DAG, with ``next`` integer references.  Costs
    strictly decrease down every chosen action edge.  A resource cap produces
    status ``limit``; it never masquerades as a proof of impossibility.
    An optional fixed ``prefix`` retains the complete sensor history before
    optimizing the remaining experiment.  Its cost is included in worst_cost.
    """
    if type(max_beliefs) is not int or max_beliefs < 1:
        raise ValueError("max_beliefs must be a positive integer.")
    indices = tuple(range(system.n)) if belief is None else tuple(sorted({
        _state_index(system, state) for state in belief
    }))
    if not indices:
        raise ValueError("The initial belief must contain at least one state.")
    if isinstance(prefix, (str, bytes, dict)):
        raise ValueError("prefix must be an iterable of action names or indices.")
    prefix_actions = []
    try:
        for item in prefix:
            if len(prefix_actions) >= 512:
                raise ValueError("prefix must contain at most 512 actions.")
            prefix_actions.append(system.action_index(item))
    except TypeError as error:
        raise ValueError("prefix must be an iterable of action names or indices.") from error
    prefix_names = [system.actions[action] for action in prefix_actions]
    prefix_cost = sum(system.costs[action] for action in prefix_actions)
    initial: Belief = tuple((state, state) for state in indices)
    beliefs: list[Belief] = []
    lookup: dict[Belief, int] = {}
    pending: deque[int] = deque()
    graph: dict[int, list[tuple[int, list[tuple[dict[str, Any], int]]]]] = {}

    class BeliefLimit(Exception):
        pass

    def intern(candidates: Belief) -> int:
        if candidates in lookup:
            return lookup[candidates]
        if len(beliefs) >= max_beliefs:
            raise BeliefLimit
        index = len(beliefs)
        lookup[candidates] = index
        beliefs.append(candidates)
        pending.append(index)
        return index

    try:
        root_groups = [([observation], candidates) for observation, candidates in _branches(system, initial, None)]
        if len(root_groups) > max_beliefs:
            raise BeliefLimit
        for action in prefix_actions:
            next_groups = []
            for history, candidates in root_groups:
                for observation, nxt in _branches(system, candidates, action):
                    if len(next_groups) >= max_beliefs:
                        raise BeliefLimit
                    next_groups.append((history + [observation], nxt))
            root_groups = next_groups
        roots = [(history[-1], intern(candidates)) for history, candidates in root_groups]
        while pending:
            index = pending.popleft()
            candidates = beliefs[index]
            graph[index] = []
            if len(_target_key(system, candidates)) == 1:
                continue
            for action in range(system.alphabet):
                successors = [(observation, intern(nxt)) for observation, nxt in _branches(system, candidates, action)]
                graph[index].append((action, successors))
    except BeliefLimit:
        return {
            "status": "limit", "worst_cost": None, "worst_remaining_cost": None,
            "prefix": prefix_names, "prefix_cost": prefix_cost, "tree": None, "nodes": [],
            "explored_beliefs": len(beliefs), "max_beliefs": max_beliefs,
            "reason": "The reachable belief-state exploration exceeded max_beliefs; solvability is unresolved.",
        }

    # An action becomes a finite candidate only when *all* observation branches
    # have finalized finite values.  The heap ensures the first finalized
    # candidate is the globally smallest minimax value.
    reverse: dict[int, list[int]] = defaultdict(list)
    records: list[dict[str, Any]] = []
    for source, actions in graph.items():
        for action, branches in actions:
            successors = {successor for _, successor in branches}
            record = len(records)
            records.append({"source": source, "action": action,
                            "remaining": len(successors), "maximum": 0})
            for successor in successors:
                reverse[successor].append(record)
    queue: list[tuple[int, int, int]] = []
    for index, candidates in enumerate(beliefs):
        if len(_target_key(system, candidates)) == 1:
            heapq.heappush(queue, (0, index, -1))
    values: dict[int, int] = {}
    choices: dict[int, int] = {}
    while queue:
        value, index, action = heapq.heappop(queue)
        if index in values:
            continue
        values[index] = value
        if action >= 0:
            choices[index] = action
        for record_index in reverse[index]:
            record = records[record_index]
            record["remaining"] -= 1
            record["maximum"] = max(record["maximum"], value)
            if record["remaining"] == 0:
                next_value = record["maximum"] + system.costs[record["action"]]
                heapq.heappush(queue, (next_value, record["source"], record["action"]))

    root_branches = []
    for (observation, index), (history, _) in zip(roots, root_groups):
        branch = {"observation": observation, "next": index}
        if prefix_names:
            branch["observations"] = history
        root_branches.append(branch)
    root_tree = {"kind": "observe", "branches": root_branches}
    losing_roots = [index for _, index in roots if index not in values]
    if losing_roots:
        index = losing_roots[0]
        losing_region = []
        for losing_index, candidates in enumerate(beliefs):
            if losing_index in values:
                continue
            obstruction = []
            for action, branches in graph[losing_index]:
                observation, successor = next((obs, nxt) for obs, nxt in branches if nxt not in values)
                obstruction.append({"action": system.actions[action], "observation": observation,
                                    "next": successor})
            losing_region.append({"id": losing_index,
                                  "candidates": _describe_belief(system, candidates),
                                  "action_obstructions": obstruction})
        root_obstruction = next(item["action_obstructions"] for item in losing_region if item["id"] == index)
        return {
            "status": "infinite", "worst_cost": None, "worst_remaining_cost": None,
            "prefix": prefix_names, "prefix_cost": prefix_cost, "tree": root_tree, "nodes": [],
            "explored_beliefs": len(beliefs), "solved_beliefs": len(values),
            "impossible_witness": {
                "kind": "closed_ambiguity_region", "root": index,
                "candidates": _describe_belief(system, beliefs[index]),
                "losing_beliefs": len(beliefs) - len(values),
                "action_obstructions": root_obstruction,
                "losing_region": losing_region,
                "reason": "Every action has a possible observation branch that remains in the losing region.",
            },
        }

    needed = deque(index for _, index in roots)
    included: set[int] = set()
    nodes: list[dict[str, Any]] = []
    while needed:
        index = needed.popleft()
        if index in included:
            continue
        included.add(index)
        candidates = beliefs[index]
        common = {"id": index, "worst_cost": values[index],
                  "candidates": _describe_belief(system, candidates)}
        if values[index] == 0:
            nodes.append({**common, "kind": "identified", "target": system.targets[candidates[0][0]]})
        else:
            action = choices[index]
            branches = next(branches for a, branches in graph[index] if a == action)
            nodes.append({**common, "kind": "action", "action": system.actions[action],
                          "cost": system.costs[action], "branches": [
                              {"observation": obs, "next": nxt} for obs, nxt in branches
                          ]})
            needed.extend(nxt for _, nxt in branches)
    return {
        "status": "finite", "worst_cost": prefix_cost + max(values[index] for _, index in roots),
        "worst_remaining_cost": max(values[index] for _, index in roots),
        "prefix": prefix_names, "prefix_cost": prefix_cost,
        "tree": root_tree, "nodes": sorted(nodes, key=lambda node: node["id"]),
        "explored_beliefs": len(beliefs), "solved_beliefs": len(values),
        "policy_beliefs": len(included),
        "target_semantics": "The target label of the initial hidden state is retained through every action.",
    }
