"""Graph context compiler: operators against height enumeration on assembled graphs.

The oracle below enumerates nonnegative height vectors on the actual glued
graph with its own loop; it shares no code with terminal kernels, interface
contraction or the closure engine.
"""
import json
import unittest
from fractions import Fraction as F
from itertools import product
from pathlib import Path

from singularity.contexts import orbit_groups
from singularity.graph import Graph
from singularity.graph_experiments import BoundaryExperimentSystem, ContextAttachment, standard_attachments
from singularity.observability import (certificate_bundle, minimum_distinguishing_experiment,
                                       observable_closure, replay_bundle, verify_certificate)

ROOT = Path(__file__).resolve().parents[1]
HALF = F(1, 2)
PATH = Graph(3, ((0, 1), (1, 2)))


def heights(n, total):
    if n == 0:
        if total == 0:
            yield ()
        return
    for first in range(total + 1):
        for rest in heights(n - 1, total - first):
            yield (first,) + rest


def enumerate_series(graph, max_volume, q):
    """[x^v] sum_h x^|h| q^(sum_uv (h_u-h_v)^2), by direct enumeration."""
    return tuple(sum((q ** sum((h[u] - h[v]) ** 2 for u, v in graph.edges) for h in heights(graph.n, v)), F(0))
                 for v in range(max_volume + 1))


def glue(graph, terminals, context):
    """Independent fresh-copy gluing: context terminals onto base terminals."""
    mapping = dict(zip(context.terminals, terminals))
    nxt = graph.n
    for v in range(context.graph.n):
        if v not in mapping:
            mapping[v] = nxt
            nxt += 1
    edges = set(graph.edges) | {tuple(sorted((mapping[u], mapping[v]))) for u, v in context.graph.edges}
    assert len(edges) == len(graph.edges) + len(context.graph.edges)
    return Graph(nxt, sorted(edges))


def oracle_rank(rows, n):
    a = [list(r) for r in rows]
    rank = 0
    for c in range(n):
        k = next((i for i in range(rank, len(a)) if a[i][c]), None)
        if k is None:
            continue
        a[rank], a[k] = a[k], a[rank]
        for i in range(len(a)):
            if i != rank and a[i][c]:
                f = a[i][c] / a[rank][c]
                a[i] = [u - f * w for u, w in zip(a[i], a[rank])]
        rank += 1
    return rank


class AssemblyAgainstEnumerationTests(unittest.TestCase):
    def test_path_fixture_values(self):
        system = BoundaryExperimentSystem(1, HALF)
        pendant, shared = system.attachments
        endpoints, adjacent = (0, 2), (0, 1)
        self.assertEqual(enumerate_series(PATH, 1, HALF), (1, F(5, 4)))
        for terminals in (endpoints, adjacent):
            state = system.compile_graph(PATH, terminals)
            self.assertEqual(system.observe(state), (1, F(5, 4)))
        values = {(t, c.name): enumerate_series(glue(PATH, t, c), 1, HALF)[1]
                  for t in (endpoints, adjacent) for c in (pendant, shared)}
        self.assertEqual(values, {(endpoints, "pendant_leaf_pair"): F(7, 4),
                                  (adjacent, "pendant_leaf_pair"): F(15, 8),
                                  (endpoints, "shared_neighbor"): 1,
                                  (adjacent, "shared_neighbor"): F(9, 8)})

    def test_path_fixture_cheapest_witness(self):
        system = BoundaryExperimentSystem(1, HALF)
        operators = system.operator_system(attachment_costs=(2, 1))
        cert = observable_closure(operators)
        self.assertTrue(verify_certificate(operators, cert))
        first, second = system.compile_graph(PATH, (0, 2)), system.compile_graph(PATH, (0, 1))
        d = tuple(a - b for a, b in zip(first, second))
        witness = minimum_distinguishing_experiment(operators, d, cert)
        self.assertEqual((witness.word, witness.cost, witness.observation), ((1,), 1, 1))
        self.assertEqual(sum(a * b for a, b in zip(witness.row, d)), F(-1, 8))
        # The pendant-leaf attachment also distinguishes, but costs two.
        pendant = system.observe(first, (0,))[1] - system.observe(second, (0,))[1]
        self.assertEqual(pendant, F(7, 4) - F(15, 8))

    def test_fifteen_words_against_enumeration(self):
        R = 3
        system = BoundaryExperimentSystem(R, HALF)
        words = [w for m in range(4) for w in product(range(2), repeat=m)]
        self.assertEqual(len(words), 15)
        for terminals in ((0, 2), (0, 1)):
            state = system.compile_graph(PATH, terminals)
            for word in words:
                graph = PATH
                for i in word:
                    graph = glue(graph, terminals, system.attachments[i])
                self.assertEqual(system.attached_graph(PATH, terminals, word)[0], graph)
                expected = enumerate_series(graph, R, HALF)
                self.assertEqual(system.observe(state, word), expected, (terminals, word))
                self.assertEqual(system.direct_observations(PATH, terminals, word), expected)

    def test_asymmetric_base_blocks_keep_raw_multiplicities(self):
        R = 3
        system = BoundaryExperimentSystem(R, F(1, 3))
        bases = [(Graph(4, ((0, 2), (2, 3))), (0, 1)),          # isolated terminal 1
                 (Graph(4, ((0, 1), (1, 2), (2, 3))), (0, 3)),  # path with endpoint terminals
                 (Graph(5, ((0, 2), (2, 3), (3, 1), (2, 4))), (0, 1)),
                 (Graph(2, ((0, 1),)), (0, 1))]                  # base terminal edge is allowed
        for graph, terminals in bases:
            state = system.compile_graph(graph, terminals)
            for word in ((), (0,), (1,), (0, 1), (1, 0), (1, 1)):
                assembled = graph
                for i in word:
                    assembled = glue(assembled, terminals, system.attachments[i])
                self.assertEqual(system.observe(state, word), enumerate_series(assembled, R, F(1, 3)))


class ClosureEvidenceTests(unittest.TestCase):
    def test_R4_length_filtered_ranks(self):
        system = BoundaryExperimentSystem(4, HALF)
        self.assertEqual(system.dimension, 22)
        operators = system.operator_system()
        cert = observable_closure(operators)
        self.assertTrue(verify_certificate(operators, cert))
        sequence = [sum(e.cost <= k for e in cert.basis) for k in range(9)]
        self.assertEqual(sequence, [5, 11, 15, 17, 18, 19, 20, 21, 22])
        # Independent: rank of all experiment rows of length <= k, k <= 3.
        def rows(length):
            result = []
            for m in range(length + 1):
                for word in product(range(2), repeat=m):
                    for target in range(5):
                        row = system.observations[target]
                        for i in reversed(word):
                            op = system.operators[i]
                            row = tuple(sum(row[k] * op[k][j] for k in range(22)) for j in range(22))
                        result.append(row)
            return result
        self.assertEqual([oracle_rank(rows(k), 22) for k in range(4)], sequence[:4])

    def test_retained_R4_certificate_replays_and_matches_fresh_discovery(self):
        bundle = json.loads((ROOT / "results" / "operator_closure_certificate.json").read_text())
        system, cert = replay_bundle(bundle)
        self.assertEqual((system.dimension, cert.rank), (22, 22))
        fresh = BoundaryExperimentSystem(4, HALF).operator_system()
        self.assertEqual(system, fresh)
        self.assertEqual(certificate_bundle(fresh), bundle)

    def test_R7_formal_invisible_direction(self):
        # Rank 69 itself is rerun by scripts/operator_experiments.py (about 40 s).
        system = BoundaryExperimentSystem(7, HALF)
        self.assertEqual(system.dimension, 70)
        index = {c: i for i, c in enumerate(system.coordinates)}
        d = [F(0)] * 70
        d[index[((0, 5), 7)]], d[index[((3, 4), 7)]] = F(1), F(-1)
        for op in system.operators:
            image = tuple(sum(a * b for a, b in zip(row, d)) for row in op)
            self.assertEqual(image, tuple(HALF ** 25 * x for x in d))
        self.assertEqual(system.observe(tuple(d)), (0,) * 8)

    def test_top_volume_collisions_bound_the_corank(self):
        # Proposition: e_(o,R) is an eigenvector of every context operator with
        # eigenvalue q^(d_C (s^2+t^2)), and L e_(o,R) is the volume-R unit.
        # Orbits sharing s^2+t^2 therefore give invisible directions.
        for R in (4, 7, 8, 10):
            system = BoundaryExperimentSystem(R, HALF)
            index = {c: i for i, c in enumerate(system.coordinates)}
            bound = 0
            for value, group in orbit_groups(R).items():
                bound += len(group) - 1
                for o in group:
                    col = index[(o, R)]
                    # Both standard contexts give each terminal one interior
                    # neighbour, so d_C = 1 and the eigenvalue is q^(s^2+t^2).
                    for op in system.operators:
                        column = [row[col] for row in op]
                        self.assertEqual(column[col], HALF ** value)
                        self.assertEqual(sum(1 for x in column if x), 1)
            # 25 = 0^2+5^2 = 3^2+4^2 (R >= 7); 50 = 1^2+7^2 = 5^2+5^2 (R >= 10).
            self.assertEqual(bound, {4: 0, 7: 1, 8: 1, 10: 2}[R])


class StructuralAssumptionTests(unittest.TestCase):
    def test_context_checks(self):
        with self.assertRaises(ValueError):
            ContextAttachment("edge", Graph(3, ((0, 1), (0, 2), (1, 2))))
        with self.assertRaises(ValueError):
            ContextAttachment("asym", Graph(3, ((0, 2),)))
        with self.assertRaises(ValueError):
            ContextAttachment("badperm", Graph(4, ((0, 2), (1, 3))), swap_automorphism=(1, 0, 2, 3))
        with self.assertRaises(ValueError):
            ContextAttachment("fixes", Graph(4, ((0, 2), (1, 2), (0, 3), (1, 3))), swap_automorphism=(0, 1, 3, 2))
        with self.assertRaises(ValueError):
            ContextAttachment("", Graph(3, ((0, 2), (1, 2))))
        with self.assertRaises(ValueError):
            BoundaryExperimentSystem(2, HALF, standard_attachments() + (standard_attachments()[0],))

    def test_exact_public_inputs(self):
        for bad in (0.5, True, "1/2"):
            with self.assertRaises(TypeError):
                BoundaryExperimentSystem(2, bad)
        for bad in (0, 1, F(3, 2), F(-1, 2)):
            with self.assertRaises(ValueError):
                BoundaryExperimentSystem(2, bad)
        system = BoundaryExperimentSystem(1, HALF)
        state = system.compile_graph(PATH, (0, 1))
        with self.assertRaises(TypeError):
            system.apply_word(tuple(float(x) for x in state))
        with self.assertRaises(TypeError):
            system.apply_word((True,) + state[1:])
        with self.assertRaises(ValueError):
            system.apply_word(state[:-1])
        with self.assertRaises(ValueError):
            system.apply_word(state, (2,))
        with self.assertRaises(TypeError):
            system.apply_word(state, (True,))
        with self.assertRaises(ValueError):
            system.compile_graph(PATH, (0, 0))


if __name__ == "__main__":
    unittest.main()
