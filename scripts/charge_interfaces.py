#!/usr/bin/env python3
"""P54: boundary-charge interfaces and context transport (SNG-F53, SNG-F54).

* Verification: for all eight labelled interior graphs H on three vertices,
  the dominating block G_H has charge table {(j, (j, j))} equal to A_{H,j};
  the charge compiler rebuilds the terminal kernel exactly; for three
  contexts (a shared neighbour, a leaf on each terminal, an asymmetric
  context with a terminal edge) and q in {1/2, 2/3}, T_C A equals the
  series of the actual glued graph, counted by weak compositions; one
  shared-neighbour closure recovers A; transport obeys the composition law.
* Compression: interface sizes for the dominating class (R + 1) against the
  ordered kernel table C(R+3, 3) and the symmetrized table of SNG-F49, and
  pattern dimensions for false-twin and general attachments.
* Exact bit accounting for K_{2,3} at q = 1/2: bits of A_0..A_R against the
  ordered kernel entries.
* Future classes: for every isomorphism class of interior graphs H on at
  most six vertices, the sequence A_{H,0..5}; distinct classes never share
  it, so on that population future equivalence of dominating blocks is
  isomorphism of interiors.
* ``--benchmark`` (retained): compile A for H = C_6 once, then answer
  closures by T_C A, against tree decomposition of each glued graph.
"""
import argparse
from fractions import Fraction
from itertools import combinations
import json
from pathlib import Path
import sys
import time

from singularity.charges import (_at, apply, charge_interface, closure_operator, dominating_block, dominating_sequence,
                                 interface_sizes, kernel_from_charges, pattern_dimension, recover_sequence, transport)
from singularity.contexts import interface_status
from singularity.decomposition import decomposition_histogram, elimination_decomposition
from singularity.graph import Graph
from singularity.heights import local_coefficients
from singularity.terminals import glue_graphs, terminal_kernel
from singularity.transfer import histogram_coefficients

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from census import canonical_code  # noqa: E402
TARGET = ROOT / "results/charge_interfaces.json"
CONTEXTS = [("shared neighbour", Graph(3, [(0, 2), (1, 2)])),
            ("leaf on each terminal", Graph(4, [(0, 2), (1, 3)])),
            ("asymmetric with terminal edge", Graph(5, [(0, 2), (2, 3), (1, 3), (0, 4), (0, 1)]))]


def verification(R=5):
    comparisons = recoveries = 0
    pairs = list(combinations(range(3), 2))
    for mask in range(8):
        H = Graph(3, [p for k, p in enumerate(pairs) if mask >> k & 1])
        G, T = dominating_block(H)
        iface = charge_interface(G, T, R)
        assert kernel_from_charges(iface, R) == terminal_kernel(G, T, R)
        assert all(Q == (j, j) for j, Q in iface["charges"]) and pattern_dimension(iface) == 0
        A = dominating_sequence(H, R)
        assert [iface["charges"][j, (j, j)] for j in range(R + 1)] == A
        for q in (Fraction(1, 2), Fraction(2, 3)):
            Aq = [_at(a, q) for a in A]
            for name, C in CONTEXTS:
                Tc = closure_operator(C, (0, 1), 3, R, q)
                glued, _ = glue_graphs(G, T, C, (0, 1))
                Z = [_at(row, q) for row in local_coefficients(glued, R)]
                assert apply(Tc, Aq) == Z, (mask, name, q)
                comparisons += 1
                if name == "shared neighbour":
                    assert recover_sequence(Z, Tc) == Aq
                    recoveries += 1
    q = Fraction(1, 2)
    Ts = [closure_operator(C, (0, 1), 3, R, q) for _, C in CONTEXTS]
    U10, U21, U20 = transport(Ts[1], Ts[0]), transport(Ts[2], Ts[1]), transport(Ts[2], Ts[0])
    composed = [[sum(U21[i][k] * U10[k][j] for k in range(R + 1)) for j in range(R + 1)] for i in range(R + 1)]
    assert composed == U20
    general = []
    for G in (Graph(5, [(0, 2), (2, 3), (3, 1), (2, 4)]), Graph(6, [(0, 2), (0, 3), (1, 3), (1, 4), (2, 5), (4, 5)]),
              Graph(6, [(0, 2), (1, 2), (0, 3), (1, 3), (3, 4), (4, 5), (2, 5)])):
        iface = charge_interface(G, (0, 1), 6)
        assert kernel_from_charges(iface, 6) == terminal_kernel(G, (0, 1), 6)
        general.append({"block": G.to_dict(), "pattern_dimension": pattern_dimension(iface), **interface_sizes(iface, 6)})
    return {"budget": R, "interior_graphs": 8, "q": ["1/2", "2/3"], "contexts": [n for n, _ in CONTEXTS],
            "glued_series_comparisons": comparisons, "single_closure_recoveries": recoveries,
            "transport_composition_law": True, "general_charge_compiler_budget_6": general}


def sizes():
    rows = []
    for R in (4, 8, 12, 16, 24, 32):
        rows.append({"budget": R, "dominating_interface": R + 1, "ordered_kernel_table": (R + 1) * (R + 2) * (R + 3) // 6,
                     "symmetrized_interface": interface_status(R, 1)["unknowns"]})
    # false twins: both terminals see interior vertices 2, 3; vertices 4, 5 see neither
    twins = Graph(6, [(0, 2), (1, 2), (0, 3), (1, 3), (2, 4), (3, 5), (4, 5)])
    iface = charge_interface(twins, (0, 1), 8)
    return {"table": rows, "false_twin_example": {"block": twins.to_dict(), "pattern_dimension": pattern_dimension(iface),
                                                  "charge_cells_budget_8": sum(1 for _ in iface["charges"])}}


def bits(R=10):
    """K_{2,3} at q = 1/2: A_j = sum over |h| = j of 2^(-2 sum h_i^2)."""
    H = Graph(3, [])
    q = Fraction(1, 2)
    A = [_at(a, q) for a in dominating_sequence(H, R)]
    out = []
    for r in range(R + 1):
        interface_bits = sum(a.numerator.bit_length() + a.denominator.bit_length() for a in A[: r + 1])
        raw_bits = 0
        for s in range(r + 1):
            for t in range(r + 1 - s):
                for j in range(r + 1 - s - t):
                    value = q ** (3 * (s * s + t * t) - 2 * j * (s + t)) * A[j]
                    raw_bits += value.numerator.bit_length() + value.denominator.bit_length()
        out.append({"budget": r, "interface_bits": interface_bits, "ordered_kernel_bits": raw_bits})
    for j, a in enumerate(A):
        assert a.denominator == 2 ** (2 * j * j) and (j == 0 or a.numerator % 2 == 1)
    return {"graph": "K_{2,3} (H = three isolated vertices)", "q": "1/2",
            "denominator_of_A_j": "exactly 2^(2 j^2), numerator odd", "rows": out}


def future_classes(max_m=6, R=5):
    rows = []
    for m in range(1, max_m + 1):
        seen, sequences = set(), set()
        pairs = list(combinations(range(m), 2))
        for mask in range(1 << len(pairs)):
            H = Graph(m, [p for k, p in enumerate(pairs) if mask >> k & 1])
            code = canonical_code(H)
            if code in seen:
                continue
            seen.add(code)
            sequences.add(repr(dominating_sequence(H, R)))
        rows.append({"m": m, "isomorphism_classes": len(seen), "distinct_sequences_through_5": len(sequences)})
    return rows


def _min_degree_order(graph):
    remaining = {v: set(graph.neighbors[v]) for v in range(graph.n)}
    order = []
    while remaining:
        v = min(remaining, key=lambda u: (len(remaining[u]), u))
        nbrs = remaining.pop(v)
        for a in nbrs:
            remaining[a] |= nbrs - {a}
            remaining[a].discard(v)
        order.append(v)
    return order


def benchmark(R=8):
    H = Graph(6, [(i, (i + 1) % 6) for i in range(6)])
    G, T = dominating_block(H)
    q = Fraction(1, 2)
    start = time.perf_counter()
    A = [_at(a, q) for a in dominating_sequence(H, R)]
    compile_time = time.perf_counter() - start
    contexts = [C for _, C in CONTEXTS] + [Graph(4, [(0, 2), (2, 3), (3, 1)]), Graph(5, [(0, 2), (1, 2), (2, 3), (3, 4)]),
                                            Graph(4, [(0, 2), (0, 3), (1, 2), (1, 3)])]
    operator = closure = direct = 0.0
    for C in contexts:
        start = time.perf_counter()
        Tc = closure_operator(C, (0, 1), H.n, R, q)
        operator += time.perf_counter() - start
        start = time.perf_counter()
        Z = apply(Tc, A)
        closure += time.perf_counter() - start
        glued, _ = glue_graphs(G, T, C, (0, 1))
        start = time.perf_counter()
        reference = histogram_coefficients(decomposition_histogram(glued, elimination_decomposition(glued, _min_degree_order(glued)), R, R), R)
        direct += time.perf_counter() - start
        assert Z == [_at(row, q) for row in reference]
    n = len(contexts)
    return {"interior": "C_6 (dominating terminals, m = 6)", "budget": R, "q": "1/2", "contexts": n,
            "compile_interface_seconds": round(compile_time, 3),
            "context_operator_seconds_per_context": round(operator / n, 4),
            "apply_seconds_per_closure": round(closure / n, 6),
            "direct_decomposition_seconds_per_closure": round(direct / n, 3),
            "note": "wall-clock on the session machine; operators are reusable across all interiors with m = 6"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--benchmark", action="store_true")
    args = parser.parse_args()
    result = {"schema": "singularity.charge-interfaces/1", "verification": verification(), "sizes": sizes(), "bits": bits(),
              "future_classes": future_classes()}
    retained = json.loads(TARGET.read_text()) if TARGET.exists() else {}
    if args.check:
        if {k: retained.get(k) for k in result} != result:
            raise SystemExit("charge interface receipt differs")
        print("Charge interface receipt matches")
        return
    result["benchmark"] = benchmark() if args.benchmark else retained.get("benchmark")
    TARGET.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    main()
