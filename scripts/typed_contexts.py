#!/usr/bin/env python3
"""NX13 receipt: typed closure certificates, graph-adapter checks and cheapest witnesses.

Modes:
  (default)   rebuild results/typed_contexts.json
  --check     rebuild and compare with the retained receipt, then replay it
  --replay P  replay every portable certificate in P; decoding and identity
              checks only, with the closure and the graph adapter disabled

Timings are printed, never retained.
"""
from __future__ import annotations

import argparse
from fractions import Fraction as F
import json
from pathlib import Path
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from singularity import typed_observability as TO  # noqa: E402

TARGET = ROOT / "results/typed_contexts.json"
SCHEMA = "singularity.nx13-typed-contexts/1"


def q_str(x):
    return str(F(x))


# ---------------------------------------------------------------------------
# replay: no closure, no adapter


def replay(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    saved = TO.typed_closure

    def refuse(*_args, **_kwargs):
        raise RuntimeError("replay must not invoke the typed closure")

    TO.typed_closure = refuse
    blocked = sys.modules.get("singularity.typed_contexts", None)
    sys.modules["singularity.typed_contexts"] = None  # importing the adapter now fails
    try:
        out = {}
        for name, entry in data["certificates"].items():
            text = json.dumps(entry["bundle"])
            system, cert = TO.load_typed_bundle(text)
            if cert.ranks != entry["ranks"]:
                raise SystemExit(f"{name}: replayed ranks differ")
            out[name] = cert.ranks
        return out
    finally:
        TO.typed_closure = saved
        if blocked is None:
            del sys.modules["singularity.typed_contexts"]
        else:
            sys.modules["singularity.typed_contexts"] = blocked


# ---------------------------------------------------------------------------
# independent helpers for exhaustive search (forward column evaluation)


def mat_vec(m, v):
    return [sum((a * b for a, b in zip(r, v)), F(0)) for r in m]


def legal_experiments(system, start, bound):
    """Every legal (word, end type, cost) from ``start`` with action cost <= bound."""
    out, stack = [], [((), start, F(0))]
    while stack:
        word, end, cost = stack.pop()
        out.append((word, end, cost))
        for a in system.actions:
            if a.source == end and cost + a.cost <= bound:
                stack.append((word + (a.identifier,), a.target, cost + a.cost))
    return out


def exhaustive_cheapest(system, start, difference, bound):
    acts = {a.identifier: a for a in system.actions}
    best, examined = None, 0
    for word, end, cost in legal_experiments(system, start, bound):
        v = list(difference)
        for a in word:
            v = mat_vec(acts[a].matrix, v)
        for o in system.observations_at[end]:
            total = cost + o.cost
            if total > bound:
                continue
            examined += 1
            if sum((a * b for a, b in zip(o.row, v)), F(0)) != 0 and (best is None or total < best):
                best = total
    return best, examined


def bits(bundle):
    num = den = 0

    def walk(x):
        nonlocal num, den
        if isinstance(x, list) and len(x) == 2 and all(type(y) is int for y in x) and x[1] > 0:
            num, den = max(num, x[0].bit_length()), max(den, x[1].bit_length())
        elif isinstance(x, list):
            for y in x:
                walk(y)
        elif isinstance(x, dict):
            for k, y in x.items():
                if k not in ("dimension", "rows", "columns", "rank", "pivots"):
                    walk(y)
    walk(bundle["system"])
    walk(bundle["certificate"])
    return {"max_numerator_bits": num, "max_denominator_bits": den}


def metrics(system, cert, bundle, max_length):
    nonzeros = sum(1 for a in system.actions for r in a.matrix for x in r if x)
    paths = {}
    for t in system.types:
        counts, frontier = [1], [t.identifier]
        for _ in range(max_length):
            frontier = [a.target for s in frontier for a in system.actions if a.source == s]
            counts.append(len(frontier))
        paths[t.identifier] = counts
    return {"dimensions": dict(system.dimension), "ranks": cert.ranks, "action_nonzeros": nonzeros,
            "actions": len(system.actions), "observations": len(system.observations),
            "legal_paths_by_length": paths, **bits(bundle)}


def witness_record(w):
    return None if w is None else {"observation": w.observation, "start_type": w.start_type,
                                   "word": list(w.word), "cost": q_str(w.cost)}


# ---------------------------------------------------------------------------
# build


def build():
    from singularity.graph import Graph
    from singularity.typed_contexts import TWO, BoundaryGrammar
    from singularity.typed_observability import (StateType, TypedAction, TypedObservation,
                                                 TypedOperatorSystem, minimum_typed_distinction,
                                                 typed_certificate_bundle, typed_closure, typed_experiment,
                                                 verify_typed_certificate)

    certificates, results = {}, {}

    # -- rectangular fixtures ------------------------------------------------
    packet = TypedOperatorSystem(
        [StateType("a", 2), StateType("b", 1)],
        [TypedAction("f", "a", "b", ((1, 1),), 2), TypedAction("g", "b", "a", ((1,), (0,)), 3)],
        [TypedObservation("Lb", "b", (1,))])
    zoo = TypedOperatorSystem(
        [StateType("a", 3), StateType("b", 1), StateType("c", 2), StateType("z", 0)],
        [TypedAction("u", "a", "a", ((1, 1, 0), (0, 1, 0), (0, 0, 1)), 1),
         TypedAction("v", "a", "a", ((0, 0, 1), (0, 1, 0), (1, 0, 0)), 1),
         TypedAction("f", "a", "b", ((1, 0, 0),), 2), TypedAction("g", "b", "a", ((1,), (0,), (0,)), 3),
         TypedAction("k", "a", "c", ((1, 0, 0), (0, 0, 1)), 1), TypedAction("h", "c", "c", ((0, 1), (1, 0)), 1),
         TypedAction("e", "z", "b", ((),), 1), TypedAction("w", "b", "z", (), 1)],
        [TypedObservation("Lb", "b", (1,)), TypedObservation("Lz", "z", ())])
    fixture_witnesses = []
    for name, system, cases in (("packet_example", packet, [("a", (2, -3)), ("a", (2, -2)), ("b", (1,))]),
                                ("zoo", zoo, [("a", (0, 0, 1)), ("a", (1, -1, 0)), ("a", (0, 1, 0)),
                                              ("c", (1, 2)), ("z", ()), ("b", (3,))])):
        cert = typed_closure(system)
        assert verify_typed_certificate(system, cert)
        bundle = typed_certificate_bundle(system, cert)
        certificates[name] = {"ranks": cert.ranks, "bundle": bundle}
        results[name] = metrics(system, cert, bundle, 4)
        for ty, diff in cases:
            w = minimum_typed_distinction(system, ty, diff, cert)
            best, examined = exhaustive_cheapest(system, ty, tuple(F(x) for x in diff), F(8))
            if (None if w is None else w.cost) != best:
                raise AssertionError((name, ty, diff, w, best))
            fixture_witnesses.append({"system": name, "type": ty, "difference": [q_str(x) for x in diff],
                                      "witness": witness_record(w), "exhaustive_bound": "8",
                                      "exhaustive_minimum": None if best is None else q_str(best),
                                      "legal_experiments_examined": examined})

    # -- graph grammar ---------------------------------------------------------
    R, q = 2, F(2, 3)
    grammar = BoundaryGrammar(R, q)
    system = grammar.system
    cert = typed_closure(system)
    assert verify_typed_certificate(system, cert)
    bundle = typed_certificate_bundle(system, cert, provenance=grammar.provenance())
    certificates["boundary_grammar_R2_q2_3"] = {"ranks": cert.ranks, "bundle": bundle}
    results["boundary_grammar_R2_q2_3"] = metrics(system, cert, bundle, 4)

    keep = ("shared", "shared@adj", "join", "cut", "forget_a", "forget_a@adj", "close", "open")
    sub = TypedOperatorSystem(system.types, [a for a in system.actions if a.identifier in keep], system.observations)
    sub_cert = typed_closure(sub)
    assert verify_typed_certificate(sub, sub_cert)
    sub_bundle = typed_certificate_bundle(sub, sub_cert, provenance={**grammar.provenance(), "sublanguage": list(keep)})
    certificates["symmetric_sublanguage_R2_q2_3"] = {"ranks": sub_cert.ranks, "bundle": sub_bundle}
    results["symmetric_sublanguage_R2_q2_3"] = metrics(sub, sub_cert, sub_bundle, 4)

    # -- adapter versus enumeration on actual assembled graphs ----------------
    path = Graph(3, ((0, 1), (1, 2)))
    p4 = Graph(4, ((0, 1), (1, 2), (2, 3)))
    triangle = Graph(3, ((0, 1), (1, 2), (0, 2)))
    bases = [(path, ()), (Graph(1), ()), (path, (1,)), (path, (0,)), (Graph(1), (0,)),
             (path, (0, 2)), (path, (2, 0)), (Graph(2), (0, 1)), (p4, (0, 2)),
             (path, (0, 1)), (path, (1, 0)), (Graph(2, ((0, 1),)), (0, 1)), (triangle, (0, 1))]
    adapter_runs = []
    for (RR, qq, length) in ((2, q, 4), (3, F(1, 2), 2)):
        g = grammar if RR == R and qq == q else BoundaryGrammar(RR, qq)
        compared = 0
        per_type = {}
        for graph, terminals in bases:
            ty, state = g.compile_state(graph, terminals)
            frontier = [((), ty, state)]
            words = [((), ty, state)]
            for _ in range(length):
                frontier = [(w + (a.identifier,), a.target, tuple(mat_vec(a.matrix, s)))
                            for w, t, s in frontier for a in g.system.actions if a.source == t]
                words += frontier
            for word, end, image in words:
                assembled, new_terminals = g.assemble(graph, terminals, word)
                if g.direct_state(assembled, new_terminals) != (end, image):
                    raise AssertionError(("adapter mismatch", RR, graph, terminals, word))
                compared += 1
            per_type[ty] = per_type.get(ty, 0) + len(words)
        adapter_runs.append({"max_volume": RR, "q": q_str(qq), "max_word_length": length,
                             "base_placements": len(bases), "words_compared": compared,
                             "words_by_start_type": per_type, "mismatches": 0})

    noncommuting = []
    for graph, terminals, w1, w2 in ((path, (0, 2), ("extend_a", "shared"), ("shared", "extend_a")),
                                     (p4, (0, 2), ("swap", "leaf_a"), ("leaf_a", "swap")),
                                     (path, (0, 2), ("join", "extend_a@adj"), ("extend_a", "join"))):
        ty, state = grammar.compile_state(graph, terminals)
        r1, r2 = grammar.observe(ty, state, w1), grammar.observe(ty, state, w2)
        d1, d2 = grammar.direct_observations(graph, terminals, w1), grammar.direct_observations(graph, terminals, w2)
        if r1 != d1 or r2 != d2 or r1 == r2:
            raise AssertionError(("noncommutation", w1, w2))
        noncommuting.append({"base_edges": [list(e) for e in graph.edges], "terminals": list(terminals),
                             "first": list(w1), "second": list(w2),
                             "first_readings": [q_str(x) for x in r1], "second_readings": [q_str(x) for x in r2]})

    duplicate = {}
    for label, call in (("typed_path", lambda: system.path(("join", "join"), TWO)),
                        ("assembly", lambda: grammar.assemble(path, (0, 2), ("join", "join"))),
                        ("experiment", lambda: typed_experiment(system, "L1@two_adj", ("join", "join"))),
                        ("graph_constructor", lambda: Graph(3, path.edges + ((0, 1),)))):
        try:
            call()
            duplicate[label] = "accepted"
        except ValueError:
            duplicate[label] = "ValueError"
    if set(duplicate.values()) != {"ValueError"}:
        raise AssertionError(duplicate)

    # -- cheapest witnesses on actual graph pairs -----------------------------
    graph_witnesses = []
    bound = F(3)
    for (g1, t1), (g2, t2), label in (((p4, (0, 2)), (p4, (2, 0)), "P4 (0,2) vs (2,0)"),
                                      ((p4, (0, 2)), (p4, (0, 3)), "P4 (0,2) vs (0,3)"),
                                      ((path, (0, 1)), (path, (1, 0)), "P3 (0,1) vs (1,0)"),
                                      ((path, (0,)), (path, (1,)), "P3 end vs middle"),
                                      ((path, ()), (Graph(3, ((0, 1),)), ()), "P3 vs K2+K1"),
                                      ((path, (0, 2)), (path, (2, 0)), "P3 automorphic endpoints")):
        ty, x1 = grammar.compile_state(g1, t1)
        ty2, x2 = grammar.compile_state(g2, t2)
        assert ty == ty2
        diff = tuple(a - b for a, b in zip(x1, x2))
        w = minimum_typed_distinction(system, ty, diff, cert)
        best, examined = exhaustive_cheapest(system, ty, diff, bound)
        if w is not None and w.cost <= bound:
            if w.cost != best:
                raise AssertionError((label, w, best))
            v = int(w.observation[1:w.observation.index("@")])
            a1 = grammar.direct_observations(g1, t1, w.word)[v]
            a2 = grammar.direct_observations(g2, t2, w.word)[v]
            if a1 == a2:
                raise AssertionError((label, "witness does not separate the actual graphs"))
            readings = [q_str(a1), q_str(a2)]
        else:
            if best is not None:
                raise AssertionError((label, w, best))
            readings = None
        graph_witnesses.append({"pair": label, "type": ty, "witness": witness_record(w),
                                "exhaustive_cost_bound": q_str(bound),
                                "exhaustive_minimum": None if best is None else q_str(best),
                                "legal_experiments_examined": examined,
                                "assembled_graph_readings": readings})

    return {
        "schema": SCHEMA,
        "track": "NX13",
        "units": ["NX13-A", "NX13-B", "NX13-C"],
        "word_convention": "chronological; word [a,b] sends v to M_b M_a v; reading L M_b M_a",
        "certificate_schema": TO.SCHEMA,
        "certificates": certificates,
        "metrics": results,
        "adapter_enumeration": adapter_runs,
        "independent_oracle": "kernel_by_enumeration / local_coefficients on the assembled graph",
        "noncommuting_examples": noncommuting,
        "duplicate_edge_rejection": duplicate,
        "fixture_cheapest_witnesses": fixture_witnesses,
        "graph_cheapest_witnesses": graph_witnesses,
        "scope": ("finite declared grammar of four boundary types at fixed volume budget and rational q; "
                  "cheapest exact distinction only, not robust margin; no state-dependent guards, "
                  "no nonlinear joins, no full-series equivalence"),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--replay", type=Path)
    args = parser.parse_args()
    if args.replay is not None:
        start = perf_counter()
        ranks = replay(args.replay)
        print(f"replayed {len(ranks)} typed certificates without closure in {perf_counter() - start:.2f}s")
        for name, r in ranks.items():
            print(f"  {name}: {r}")
        return
    start = perf_counter()
    result = build()
    print(f"built receipt in {perf_counter() - start:.2f}s")
    if args.check:
        retained = json.loads(TARGET.read_text(encoding="utf-8"))
        if result != retained:
            raise SystemExit("NX13 retained receipt differs")
        start = perf_counter()
        replay(TARGET)
        print(f"NX13 receipt matches; replayed {len(result['certificates'])} certificates "
              f"in {perf_counter() - start:.2f}s")
    else:
        TARGET.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print(TARGET)


if __name__ == "__main__":
    main()
