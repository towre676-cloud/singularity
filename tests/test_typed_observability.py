"""Typed observation closure (NX13-A, NX13-C algebra side).

Independent oracles here do not call ``typed_closure``: they enumerate legal
words directly, multiply matrices on the column side, and compute ranks with
a separate elimination routine written in this file.
"""
import copy
import json
import random
import unittest
from dataclasses import replace
from fractions import Fraction as F

from singularity import typed_observability as T
from singularity.typed_observability import (
    StateType, TypedAction, TypedObservation, TypedOperatorSystem, load_typed_bundle,
    minimum_typed_distinction, replay_typed_bundle, typed_apply_word, typed_certificate_bundle,
    typed_closure, typed_experiment, typed_future_equivalent, typed_quotient_state,
    typed_quotient_update, verify_typed_certificate)


# ---------------------------------------------------------------------------
# independent helpers (no shared code with the module under test)

def oracle_rank(rows):
    m = [list(r) for r in rows]
    rank, cols = 0, len(m[0]) if m else 0
    for c in range(cols):
        p = next((i for i in range(rank, len(m)) if m[i][c] != 0), None)
        if p is None:
            continue
        m[rank], m[p] = m[p], m[rank]
        for i in range(len(m)):
            if i != rank and m[i][c] != 0:
                f = m[i][c] / m[rank][c]
                m[i] = [a - f * b for a, b in zip(m[i], m[rank])]
        rank += 1
    return rank


def mat_vec(m, v):
    return [sum(F(a) * b for a, b in zip(row, v)) for row in m]


def legal_words(system, start, length):
    """All chronological legal words from ``start`` of length <= length, with end types."""
    out, frontier = [((), start)], [((), start)]
    for _ in range(length):
        frontier = [(w + (a.identifier,), a.target) for w, t in frontier for a in system.actions if a.source == t]
        out += frontier
    return out


def reading(system, start, word, obs, state):
    """Forward column evaluation, independent of backward row products."""
    acts = {a.identifier: a for a in system.actions}
    v = list(state)
    for a in word:
        v = mat_vec(acts[a].matrix, v)
    o = next(x for x in system.observations if x.identifier == obs)
    return sum(F(a) * b for a, b in zip(o.row, v))


def oracle_rows(system, start, length):
    """Readings as row functionals, by evaluating forward on unit vectors."""
    d = next(t.dimension for t in system.types if t.identifier == start)
    units = [[F(i == j) for j in range(d)] for i in range(d)]
    rows = []
    for word, end in legal_words(system, start, length):
        for o in system.observations:
            if o.type_id == end:
                rows.append((word, o, tuple(reading(system, start, word, o.identifier, u) for u in units)))
    return rows


# ---------------------------------------------------------------------------
# fixtures

def packet_example():
    """Packet fixture: a=Q^2 (no observation), b=Q (observe 1); f costs 2, g costs 3."""
    return TypedOperatorSystem(
        [StateType("a", 2), StateType("b", 1)],
        [TypedAction("f", "a", "b", ((1, 1),), 2), TypedAction("g", "b", "a", ((1,), (0,)), 3)],
        [TypedObservation("Lb", "b", (1,))])


def zoo():
    """Rank-zero type c, zero-dimensional type z, empty outputs, cycles, noncommuting u,v."""
    return TypedOperatorSystem(
        [StateType("a", 3), StateType("b", 1), StateType("c", 2), StateType("z", 0)],
        [TypedAction("u", "a", "a", ((1, 1, 0), (0, 1, 0), (0, 0, 1)), 1),
         TypedAction("v", "a", "a", ((0, 0, 1), (0, 1, 0), (1, 0, 0)), 1),
         TypedAction("f", "a", "b", ((1, 0, 0),), 2),
         TypedAction("g", "b", "a", ((1,), (0,), (0,)), 3),
         TypedAction("k", "a", "c", ((1, 0, 0), (0, 0, 1)), 1),
         TypedAction("h", "c", "c", ((0, 1), (1, 0)), 1),
         TypedAction("e", "z", "b", ((),), 1),
         TypedAction("w", "b", "z", (), 1)],
        [TypedObservation("Lb", "b", (1,)), TypedObservation("Lz", "z", ())])


def random_system(seed):
    rnd = random.Random(seed)
    dims = {"p": rnd.randint(1, 3), "r": rnd.randint(0, 2), "s": rnd.randint(1, 3)}
    acts = []
    for i, (src, tgt) in enumerate([("p", "r"), ("r", "s"), ("s", "p"), ("p", "p"), ("s", "s")]):
        m = tuple(tuple(rnd.choice((0, 0, 1, -1, 2, F(1, 2))) for _ in range(dims[src])) for _ in range(dims[tgt]))
        acts.append(TypedAction(f"a{i}", src, tgt, m, rnd.choice((1, 2, F(3, 2)))))
    obs = [TypedObservation("o1", "s", tuple(rnd.choice((0, 1, -1)) for _ in range(dims["s"])), rnd.choice((0, 1)))]
    if dims["r"]:
        obs.append(TypedObservation("o2", "r", tuple(rnd.choice((0, 1)) for _ in range(dims["r"]))))
    return TypedOperatorSystem([StateType(k, v) for k, v in dims.items()], acts, obs)


FIXTURES = [packet_example, zoo] + [lambda s=s: random_system(s) for s in range(12)]


class HandwrittenExampleTests(unittest.TestCase):
    def test_packet_example_by_hand(self):
        s = packet_example()
        c = typed_closure(s)
        self.assertTrue(verify_typed_certificate(s, c))
        a, b = c.block("a"), c.block("b")
        # First backward step: L_b M_f = (1)(1 1) = (1, 1) at a, cost 0 + 2.
        self.assertEqual(a.rows, ((F(1), F(1)),))
        self.assertEqual(a.basis[0].word, ("f",))
        self.assertEqual(a.basis[0].cost, 2)
        self.assertEqual(b.rows, ((F(1),),))
        # Around the cycle: L_b M_f M_g = (1 1)(1;0) = 1, nothing new.
        self.assertEqual(typed_experiment(s, "Lb", ("g", "f")).row, (F(1),))
        # N_a = span{(1,-1)}, N_b = 0; A_a is 0 x 1, A_b = (1); T_f = T_g = (1).
        self.assertEqual(oracle_rank(a.nullspace + ((F(1), F(-1)),)), 1)
        self.assertEqual(len(a.nullspace), 1)
        self.assertEqual(b.nullspace, ())
        self.assertEqual(a.observation_coordinates, ())
        self.assertEqual(b.observation_coordinates, ((F(1),),))
        self.assertEqual(c.transition_coordinates, (((F(1),),), ((F(1),),)))
        # (2,0) ~ (0,2) forever; (2,0) vs (0,3) separated by f at cost 2.
        self.assertTrue(typed_future_equivalent(s, "a", (2, 0), (0, 2), c))
        self.assertFalse(typed_future_equivalent(s, "a", (2, 0), (0, 3), c))
        self.assertIsNone(minimum_typed_distinction(s, "a", (2, -2), c))
        witness = minimum_typed_distinction(s, "a", (2, -3), c)
        self.assertEqual((witness.word, witness.cost), (("f",), 2))
        # Quotient dynamics: z_b = T_f z_a.
        z = typed_quotient_state(s, c, "a", (2, 5))
        self.assertEqual(typed_quotient_update(c, s, "f", z), typed_apply_word(s, "a", (2, 5), ("f",))[1])

    def test_reading_at_the_wrong_type_is_rejected(self):
        s = packet_example()
        with self.assertRaises(ValueError):
            typed_experiment(s, "Lb", (), start_type="a")
        with self.assertRaises(ValueError):
            typed_experiment(s, "Lb", ("f", "f"))
        with self.assertRaises(ValueError):
            typed_experiment(s, "Lb", ("g",))  # ends at a, Lb lives at b
        with self.assertRaises(ValueError):
            typed_apply_word(s, "b", (1,), ("f",))
        with self.assertRaises(ValueError):
            typed_apply_word(s, "a", (1, 0), ("nope",))
        with self.assertRaises(ValueError):
            s.path(())


class ZooTests(unittest.TestCase):
    def test_rank_zero_zero_dimension_and_empty_outputs(self):
        s = zoo()
        c = typed_closure(s)
        self.assertTrue(verify_typed_certificate(s, c))
        self.assertEqual(c.ranks, {"a": 3, "b": 1, "c": 0, "z": 0})
        cb, zb = c.block("c"), c.block("z")
        self.assertEqual(cb.rows, ())
        self.assertEqual(len(cb.nullspace), 2)          # all of Q^2 is invisible
        self.assertEqual(zb.nullspace, ())               # Q^0 has empty kernel basis
        self.assertEqual(zb.observation_coordinates, ((),))  # one observation, rank 0
        k = s.action_index["k"]
        self.assertEqual(c.transition_coordinates[k], ())  # r_c x r_a = 0 x 3
        self.assertEqual(c.transition_coordinates[s.action_index["e"]], ((),))  # 1 x 0
        self.assertEqual(c.transition_coordinates[s.action_index["w"]], ())     # 0 x 1
        self.assertIsNone(minimum_typed_distinction(s, "c", (1, -7), c))
        self.assertEqual(typed_apply_word(s, "b", (5,), ("w", "e")), ("b", (F(0),)))

    def test_noncommuting_order_matters(self):
        s = zoo()
        x = (1, 2, 3)
        self.assertNotEqual(typed_apply_word(s, "a", x, ("u", "v"))[1], typed_apply_word(s, "a", x, ("v", "u"))[1])
        # chronological: (u, v) means M_v M_u x
        self.assertEqual(typed_apply_word(s, "a", x, ("u", "v"))[1], tuple(mat_vec(
            s.action("v").matrix, mat_vec(s.action("u").matrix, x))))
        self.assertNotEqual(typed_experiment(s, "Lb", ("u", "v", "f")).row,
                            typed_experiment(s, "Lb", ("v", "u", "f")).row)


class IndependentOracleTests(unittest.TestCase):
    def test_closure_spans_equal_exhaustive_legal_words(self):
        """W_b = span of all legal readings; length sum(d_b) suffices (each pass adds rank)."""
        for make in FIXTURES:
            s = make()
            c = typed_closure(s)
            self.assertTrue(verify_typed_certificate(s, c))
            D = sum(t.dimension for t in s.types)
            for t in s.types:
                rows = [r for _, _, r in oracle_rows(s, t.identifier, D)]
                basis = c.block(t.identifier).rows
                r = oracle_rank(rows) if rows else 0
                self.assertEqual(r, len(basis), (make, t))
                if t.dimension:
                    self.assertEqual(oracle_rank(list(rows) + list(basis)), r)
                # minimality: every reading kills N_b, and dim N_b = d_b - rank
                self.assertEqual(len(c.block(t.identifier).nullspace), t.dimension - r)
                for n in c.block(t.identifier).nullspace:
                    for word, end in legal_words(s, t.identifier, D):
                        for o in s.observations_at[end]:
                            self.assertEqual(reading(s, t.identifier, word, o.identifier, n), 0)

    def test_witnesses_are_the_experiments_they_name(self):
        for make in FIXTURES:
            s = make()
            for block in typed_closure(s).blocks:
                for e in block.basis:
                    d = len(e.row)
                    units = [[F(i == j) for j in range(d)] for i in range(d)]
                    self.assertEqual(e.row, tuple(reading(s, e.start_type, e.word, e.observation, u) for u in units))

    def test_quotient_dynamics_descends(self):
        rnd = random.Random(7)
        for make in FIXTURES:
            s = make()
            c = typed_closure(s)
            for a in s.actions:
                x = tuple(F(rnd.randint(-3, 3)) for _ in range(s.dimension[a.source]))
                z = typed_quotient_state(s, c, a.source, x)
                _, y = typed_apply_word(s, a.source, x, (a.identifier,))
                self.assertEqual(typed_quotient_update(c, s, a.identifier, z), typed_quotient_state(s, c, a.target, y))


class ValidationTests(unittest.TestCase):
    def test_scalar_and_identifier_types(self):
        for bad in (True, 0.5, "1"):
            with self.assertRaises(TypeError):
                TypedAction("f", "a", "b", ((bad, 1),))
            with self.assertRaises(TypeError):
                TypedObservation("o", "b", (bad,))
        with self.assertRaises(TypeError):
            StateType("a", True)
        with self.assertRaises(TypeError):
            StateType("a", 1.0)
        with self.assertRaises(ValueError):
            StateType("a", -1)
        with self.assertRaises(TypeError):
            StateType(3, 1)
        with self.assertRaises(ValueError):
            StateType("", 1)
        with self.assertRaises(ValueError):
            TypedAction("f", "a", "b", ((1,),), 0)
        with self.assertRaises(TypeError):
            TypedAction("f", "a", "b", ((1,),), 1.0)
        with self.assertRaises(ValueError):
            TypedObservation("o", "b", (1,), -1)
        with self.assertRaises(TypeError):
            TypedAction("f", "a", "b", "11")

    def test_shapes_and_declarations(self):
        A, B, Z = StateType("a", 2), StateType("b", 1), StateType("z", 0)
        good = TypedAction("f", "a", "b", ((1, 1),))
        obs = TypedObservation("o", "b", (1,))
        TypedOperatorSystem([A, B], [good], [obs])
        bad_shapes = [((1,),), ((1, 1), (1, 1)), ((1, 1, 1),), ()]
        for m in bad_shapes:
            with self.assertRaises(ValueError):
                TypedOperatorSystem([A, B], [TypedAction("f", "a", "b", m)], [obs])
        # a -> z is 0 x 2: (); z -> a is 2 x 0: ((), ()); an empty tuple is not 2 x 0
        TypedOperatorSystem([A, Z], [TypedAction("x", "a", "z", ()), TypedAction("y", "z", "a", ((), ()))], [])
        with self.assertRaises(ValueError):
            TypedOperatorSystem([A, Z], [TypedAction("y", "z", "a", ())], [])
        with self.assertRaises(ValueError):
            TypedOperatorSystem([A, Z], [TypedAction("x", "a", "z", ((),))], [])
        with self.assertRaises(ValueError):
            TypedOperatorSystem([A], [good], [])            # undeclared target
        with self.assertRaises(ValueError):
            TypedOperatorSystem([A, B], [], [TypedObservation("o", "q", (1,))])
        with self.assertRaises(ValueError):
            TypedOperatorSystem([A, B], [], [TypedObservation("o", "b", (1, 1))])
        with self.assertRaises(ValueError):
            TypedOperatorSystem([A, A], [], [])
        with self.assertRaises(ValueError):
            TypedOperatorSystem([A, B], [good, good], [])
        with self.assertRaises(ValueError):
            TypedOperatorSystem([A, B], [], [obs, obs])
        with self.assertRaises(TypeError):
            TypedOperatorSystem(["a"], [], [])
        s = TypedOperatorSystem([A, B], [good], [obs])
        with self.assertRaises(TypeError):
            typed_apply_word(s, "a", (1, 0.5), ())
        with self.assertRaises(ValueError):
            typed_apply_word(s, "a", (1,), ())
        with self.assertRaises(TypeError):
            typed_apply_word(s, "a", (1, 0), "f")


class CertificateTamperTests(unittest.TestCase):
    def test_tampering_is_rejected(self):
        s = zoo()
        c = typed_closure(s)
        a = c.block("a")
        ia = 0
        e = a.basis[-1]
        self.assertGreaterEqual(len(e.word), 2)
        tampered = []

        def with_block(new):
            blocks = list(c.blocks)
            blocks[ia] = new
            return replace(c, blocks=tuple(blocks))

        basis = list(a.basis)
        basis[-1] = replace(e, word=tuple(reversed(e.word)))      # chronology reversal
        tampered.append(with_block(replace(a, basis=tuple(basis))))
        basis = list(a.basis)
        basis[-1] = replace(e, cost=e.cost + 1)
        tampered.append(with_block(replace(a, basis=tuple(basis))))
        basis = list(a.basis)
        basis[-1] = replace(e, row=(e.row[0] + 1,) + e.row[1:])
        tampered.append(with_block(replace(a, basis=tuple(basis))))
        basis = list(a.basis)
        basis[-1] = replace(e, row=tuple(int(x) for x in e.row))   # ints, not Fractions
        tampered.append(with_block(replace(a, basis=tuple(basis))))
        basis = list(a.basis)
        basis[0], basis[-1] = basis[-1], basis[0]                    # cost order broken
        tampered.append(with_block(replace(a, basis=tuple(basis))))
        tampered.append(with_block(replace(a, basis=a.basis[:-1])))  # rank drop
        tr = list(c.transition_coordinates)
        f = s.action_index["f"]
        tr[f] = ((tr[f][0][0] + 1,),) if tr[f] and tr[f][0] else tr[f]
        tampered.append(replace(c, transition_coordinates=tuple(tr)))
        tampered.append(replace(c, blocks=c.blocks[:-1]))
        tampered.append(replace(c, blocks=(c.blocks[1], c.blocks[0]) + c.blocks[2:]))
        for bad in tampered:
            self.assertFalse(verify_typed_certificate(s, bad))
        self.assertTrue(verify_typed_certificate(s, c))
        self.assertFalse(verify_typed_certificate(packet_example(), c))
        with self.assertRaises(ValueError):
            minimum_typed_distinction(s, "a", (1, 0, 0), tampered[0])

    def test_reversed_words(self):
        s = zoo()
        # Reversing a witness across a type change is illegal, hence rejected.
        with self.assertRaises(ValueError):
            typed_experiment(s, "Lb", ("f", "u"))
        # Reversing the same-type prefix is legal but reads a different row.
        self.assertNotEqual(typed_experiment(s, "Lb", ("u", "v", "f")).row,
                            typed_experiment(s, "Lb", ("v", "u", "f")).row)


class PortableBundleTests(unittest.TestCase):
    def test_roundtrip_without_closure(self):
        for make in FIXTURES:
            s = make()
            c = typed_closure(s)
            text = json.dumps(typed_certificate_bundle(s, c))
            original = T.typed_closure
            try:
                T.typed_closure = None  # replay must never call it
                s2, c2 = load_typed_bundle(text)
            finally:
                T.typed_closure = original
            self.assertEqual(c2, c)
            self.assertEqual([(t.identifier, t.dimension) for t in s2.types],
                             [(t.identifier, t.dimension) for t in s.types])

    def test_strict_decoding(self):
        bundle = typed_certificate_bundle(zoo())
        replay_typed_bundle(bundle)

        def broken(mutate):
            b = copy.deepcopy(bundle)
            mutate(b)
            return b

        cases = [
            lambda b: b.update(schema="singularity.operator-closure/1"),
            lambda b: b["system"]["types"][0].update(dimension=True),
            lambda b: b["system"]["types"][0].update(dimension=2.0),
            lambda b: b["system"]["actions"][0].update(cost=[2, 2]),          # noncanonical
            lambda b: b["system"]["actions"][0].update(cost=[1, 0]),
            lambda b: b["system"]["actions"][0].update(cost=[0, 1]),          # nonpositive cost
            lambda b: b["system"]["actions"][0]["matrix"].update(rows=2),
            lambda b: b["system"]["actions"][6]["matrix"].update(entries=[]),  # z->b needs 1 x 0
            lambda b: b["certificate"]["types"][0]["basis"][1].update(word=list(reversed(
                b["certificate"]["types"][0]["basis"][1]["word"])) + ["u"]),
            lambda b: b["certificate"]["types"][0]["basis"][-1].update(
                word=list(reversed(b["certificate"]["types"][0]["basis"][-1]["word"]))),
            lambda b: b["certificate"]["types"][0].update(rank=2),
            lambda b: b["certificate"]["actions"].reverse(),
            lambda b: b["certificate"].update(extra=1),
            lambda b: b["system"]["observations"][0].update(row=[[1.0, 1]]),
        ]
        for mutate in cases:
            with self.assertRaises(ValueError):
                replay_typed_bundle(broken(mutate))
        text = json.dumps(bundle)
        with self.assertRaises(ValueError):
            load_typed_bundle(text.replace('"schema"', '"schema": "x", "schema"', 1))
        with self.assertRaises(ValueError):
            load_typed_bundle(text.replace("[1, 1]", "[NaN, 1]", 1))


class CheapestWitnessTests(unittest.TestCase):
    def test_cheapest_matches_bounded_exhaustive_search(self):
        """Exhaustive legal experiments up to a cost bound, evaluated forward on the difference."""
        rnd = random.Random(11)
        for make in FIXTURES:
            s = make()
            c = typed_closure(s)
            min_cost = min((a.cost for a in s.actions), default=1)
            bound = F(6)
            length = int(bound / min_cost)
            for t in s.types:
                words = [(w, e) for w, e in legal_words(s, t.identifier, length)]
                for _ in range(4):
                    diff = tuple(F(rnd.randint(-2, 2)) for _ in range(t.dimension))
                    best = None
                    for w, end in words:
                        cost = sum((s.action(a).cost for a in w), F(0))
                        for o in s.observations_at[end]:
                            total = cost + o.cost
                            if total <= bound and reading(s, t.identifier, w, o.identifier, diff) != 0:
                                best = total if best is None else min(best, total)
                    witness = minimum_typed_distinction(s, t.identifier, diff, c)
                    if witness is None:
                        self.assertIsNone(best)
                    elif witness.cost <= bound:
                        self.assertEqual(witness.cost, best, (make, t, diff))
                        self.assertNotEqual(reading(s, t.identifier, witness.word, witness.observation, diff), 0)
                    else:
                        self.assertIsNone(best)


if __name__ == "__main__":
    unittest.main()
