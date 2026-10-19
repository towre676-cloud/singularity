"""Validated finite systems and exact, label-preserving behavior compilation.

The compiler uses inverse transitions and a splitter worklist.  It does not run
an all-pairs search through the space of distinguishing words.
"""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from math import isfinite
from typing import Any, Iterator, Mapping


def scalar_key(value: Any) -> tuple[str, Any]:
    """A JSON-scalar key that does not identify ``True`` with ``1``."""
    if value is None:
        return ("null", None)
    if type(value) in (str, bool, int):
        return (type(value).__name__, value)
    if type(value) is float and isfinite(value):
        return ("float", value)
    raise ValueError("labels must be finite JSON scalars (null, string, boolean or number)")


def labels_equal(left: Any, right: Any) -> bool:
    return scalar_key(left) == scalar_key(right)


def _integer(value: Any, description: str, lower: int = 0) -> int:
    if type(value) is not int or value < lower:
        raise ValueError(f"{description} must be an integer >= {lower}")
    return value


@dataclass(frozen=True)
class FiniteSystem:
    states: tuple[str, ...]
    actions: tuple[str, ...]
    costs: tuple[int, ...]
    transitions: tuple[tuple[int | None, ...], ...]
    observations: tuple[Any, ...]
    targets: tuple[Any, ...]
    accepting: tuple[bool, ...]
    name: str = "Finite system"
    initial: int = 0

    def __post_init__(self) -> None:
        for field in ("states", "actions", "costs", "observations", "targets", "accepting"):
            object.__setattr__(self, field, tuple(getattr(self, field)))
        object.__setattr__(self, "transitions", tuple(tuple(row) for row in self.transitions))
        if not self.states:
            raise ValueError("at least one state is required")
        for field in ("states", "actions"):
            names = getattr(self, field)
            if any(type(value) is not str or not value for value in names):
                raise ValueError(f"{field} must contain nonempty strings")
            if len(set(names)) != len(names):
                raise ValueError(f"{field} names must be distinct")
        if type(self.name) is not str:
            raise ValueError("name must be a string")
        if len(self.costs) != self.alphabet:
            raise ValueError("one positive integer cost is required per action")
        for cost in self.costs:
            _integer(cost, "action cost", 1)
        if len(self.transitions) != self.n or any(len(row) != self.alphabet for row in self.transitions):
            raise ValueError("transitions must be a rectangular state-by-action table")
        for row in self.transitions:
            for target in row:
                if target is not None:
                    _integer(target, "transition target")
                    if target >= self.n:
                        raise ValueError("transition target outside state range")
        for field in ("observations", "targets", "accepting"):
            values = getattr(self, field)
            if len(values) != self.n:
                raise ValueError(f"one {field} value is required per state")
            if field == "accepting":
                if any(type(value) is not bool for value in values):
                    raise ValueError("accepting values must be booleans")
            else:
                for value in values:
                    scalar_key(value)
        _integer(self.initial, "initial state")
        if self.initial >= self.n:
            raise ValueError("initial state outside state range")

    @property
    def n(self) -> int:
        return len(self.states)

    @property
    def alphabet(self) -> int:
        return len(self.actions)

    def action_index(self, action: int | str) -> int:
        if type(action) is str:
            try:
                return self.actions.index(action)
            except ValueError as error:
                raise ValueError(f"unknown action: {action!r}") from error
        _integer(action, "action index")
        if action >= self.alphabet:
            raise ValueError("action index outside alphabet")
        return action

    def step(self, state: int, action: int | str) -> int | None:
        _integer(state, "state")
        if state >= self.n:
            raise ValueError("state outside state range")
        return self.transitions[state][self.action_index(action)]

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "FiniteSystem":
        if not isinstance(data, Mapping):
            raise ValueError("system must be a JSON object")
        transitions = data.get("transitions")
        if not isinstance(transitions, (list, tuple)):
            raise ValueError("transitions must be a state-by-action table")
        if any(not isinstance(row, (list, tuple)) for row in transitions):
            raise ValueError("each transition row must be an array")
        n = len(transitions)
        states = data.get("states", [f"s{i}" for i in range(n)])
        if not isinstance(states, (list, tuple)):
            raise ValueError("states must be an array of names")
        raw_actions = data.get("actions", [f"a{i}" for i in range(len(transitions[0]) if n else 0)])
        if not isinstance(raw_actions, (list, tuple)):
            raise ValueError("actions must be an array")
        if raw_actions and isinstance(raw_actions[0], Mapping):
            if any(not isinstance(item, Mapping) for item in raw_actions):
                raise ValueError("action records and action names cannot be mixed")
            if any("name" not in item or "cost" not in item for item in raw_actions):
                raise ValueError("each action record requires name and cost")
            actions = [item["name"] for item in raw_actions]
            costs = [item["cost"] for item in raw_actions]
            if "costs" in data:
                if not isinstance(data["costs"], (list, tuple)):
                    raise ValueError("costs must be an array")
                for value in data["costs"]:
                    _integer(value, "action cost", 1)
                if list(data["costs"]) != costs:
                    raise ValueError("costs disagree with action records")
        else:
            actions = raw_actions
            costs = data.get("costs", [1] * len(actions))
        if not isinstance(costs, (list, tuple)):
            raise ValueError("costs must be an array")
        if "observations" not in data:
            raise ValueError("observations are required")
        observations = data["observations"]
        targets = data.get("targets", observations)
        accepting = data.get("accepting", [True] * n)
        for field, values in (("observations", observations), ("targets", targets), ("accepting", accepting)):
            if not isinstance(values, (list, tuple)):
                raise ValueError(f"{field} must be an array")
        return cls(tuple(states), tuple(actions), tuple(costs), tuple(tuple(row) for row in transitions),
                   tuple(observations), tuple(targets), tuple(accepting), data.get("name", "Finite system"),
                   data.get("initial", 0))

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "states": list(self.states),
                "actions": [{"name": name, "cost": cost} for name, cost in zip(self.actions, self.costs)],
                "transitions": [list(row) for row in self.transitions],
                "observations": list(self.observations), "targets": list(self.targets),
                "accepting": list(self.accepting), "initial": self.initial}


@dataclass(frozen=True)
class Compilation:
    system: FiniteSystem
    mapping: tuple[int, ...]
    blocks: tuple[tuple[int, ...], ...]
    metrics: dict[str, Any]

    @property
    def model(self) -> FiniteSystem:
        return self.system

    def __iter__(self) -> Iterator[Any]:
        yield self.system
        yield self.mapping
        yield self.blocks


def replay_compilation(original: FiniteSystem, compiled: Compilation) -> bool:
    """Replay every quotient label and transition in original coordinates."""
    reduced, mapping = compiled.system, compiled.mapping
    if len(mapping) != original.n or reduced.actions != original.actions or reduced.costs != original.costs:
        return False
    if reduced.initial != mapping[original.initial]:
        return False
    covered = [state for block in compiled.blocks for state in block]
    if sorted(covered) != list(range(original.n)) or len(compiled.blocks) != reduced.n:
        return False
    for block_index, block in enumerate(compiled.blocks):
        if not block or any(mapping[state] != block_index for state in block):
            return False
    for state, row in enumerate(original.transitions):
        qstate = mapping[state]
        if type(qstate) is not int or not 0 <= qstate < reduced.n:
            return False
        if not labels_equal(original.observations[state], reduced.observations[qstate]):
            return False
        if not labels_equal(original.targets[state], reduced.targets[qstate]):
            return False
        if original.accepting[state] != reduced.accepting[qstate]:
            return False
        if reduced.transitions[qstate] != tuple(None if target is None else mapping[target] for target in row):
            return False
    return True


def compile_system(system: FiniteSystem) -> Compilation:
    """Minimal behavioral quotient preserving sensors, targets and acceptance.

    Splits are driven by inverse transition sets.  When a queued block splits,
    both children remain queued; otherwise only its smaller child is queued.
    Final block order follows original state order, independent of set order.
    """
    initial: dict[Any, set[int]] = {}
    for state in range(system.n):
        key = (scalar_key(system.observations[state]), scalar_key(system.targets[state]),
               system.accepting[state], tuple(target is not None for target in system.transitions[state]))
        initial.setdefault(key, set()).add(state)
    blocks = list(initial.values())
    owner = [0] * system.n
    for index, block in enumerate(blocks):
        for state in block:
            owner[state] = index
    inverse = [[[] for _ in range(system.n)] for _ in range(system.alphabet)]
    for source, row in enumerate(system.transitions):
        for action, target in enumerate(row):
            if target is not None:
                inverse[action][target].append(source)
    queue = deque(range(len(blocks)))
    queued = set(queue)
    splitter_count = split_count = predecessor_visits = 0
    while queue:
        splitter_index = queue.popleft()
        queued.remove(splitter_index)
        splitter = tuple(blocks[splitter_index])
        splitter_count += 1
        for action in range(system.alphabet):
            touched: dict[int, set[int]] = defaultdict(set)
            for target in splitter:
                for source in inverse[action][target]:
                    touched[owner[source]].add(source)
                    predecessor_visits += 1
            for index, inside in touched.items():
                if len(inside) == len(blocks[index]):
                    continue
                # Retain the larger child at the old index.  Updating owner
                # then touches only the smaller child at each unqueued split.
                if len(inside) <= len(blocks[index]) // 2:
                    blocks[index].difference_update(inside)
                else:
                    outside = blocks[index] - inside
                    blocks[index] = inside
                    inside = outside
                new_index = len(blocks)
                blocks.append(inside)
                for state in inside:
                    owner[state] = new_index
                split_count += 1
                # If the old block is queued, its retained larger child is
                # already scheduled; otherwise schedule only the smaller one.
                queue.append(new_index)
                queued.add(new_index)
    final_blocks = tuple(sorted((tuple(sorted(block)) for block in blocks), key=lambda block: block[0]))
    mapping = [0] * system.n
    for index, block in enumerate(final_blocks):
        for state in block:
            mapping[state] = index
    representatives = [block[0] for block in final_blocks]
    reduced = FiniteSystem(
        tuple(f"q{index}: {system.states[state]}" for index, state in enumerate(representatives)),
        system.actions, system.costs,
        tuple(tuple(None if target is None else mapping[target] for target in system.transitions[state])
              for state in representatives),
        tuple(system.observations[state] for state in representatives),
        tuple(system.targets[state] for state in representatives),
        tuple(system.accepting[state] for state in representatives),
        f"{system.name} / behavioral quotient", mapping[system.initial])
    result = Compilation(reduced, tuple(mapping), final_blocks,
                         {"original_states": system.n, "quotient_states": reduced.n,
                          "splits": split_count, "splitters": splitter_count,
                          "predecessor_visits": predecessor_visits, "replayed": True})
    if not replay_compilation(system, result):
        raise AssertionError("behavioral quotient failed transition/label replay")
    return result


behavioral_quotient = compile_system
