"""NX08 target-recovery tests.

Independent oracles here never call the module's elimination: PSD is decided
by all principal minors with a permutation-expansion determinant, lower
witnesses come from enumerating small integer directions, and the catalogue
optimum is recomputed by brute force from the raw sensor rows.
"""
from fractions import Fraction as F
from itertools import combinations, permutations, product
import copy
import random
import unittest

from singularity.target_recovery import (
    AmplificationBracket, DecoderCertificate, NegativeWitness, PSDCertificate, SensorOption,
    TargetRecoveryProblem, adversarial_witness, amplification_form, amplification_ratio,
    bracket_decoder_norm, bracket_target_amplification, certify_decoder_norm,
    certify_target_amplification, cheapest_conditioned_layout, cheapest_identifying_layout,
    conditioning_frontier, decoder_ratio, layout_problem, layout_table, linear_forecast_problem,
    minimum_norm_decoder, psd_certificate, recover_target, target_identifiability,
    target_recovery_receipt, thermal_target_problem, verify_psd_certificate,
    verify_target_recovery_receipt)


# ----------------------------- independent oracles -----------------------------

def perm_det(a):
    n = len(a)
    total = F(0)
    for perm in permutations(range(n)):
        inversions = sum(1 for i in range(n) for j in range(i + 1, n) if perm[i] > perm[j])
        term = F(-1) ** inversions
        for i in range(n):
            term *= a[i][perm[i]]
        total += term
    return total


def psd_oracle(a):
    """Symmetric a is PSD iff every principal minor is nonnegative."""
    n = len(a)
    for size in range(1, n + 1):
        for idx in combinations(range(n), size):
            if perm_det([[a[i][j] for j in idx] for i in idx]) < 0:
                return False
    return True


def raw_forms(h, g, q=None, r_diag=None):
    """A = H0^T W H0, B = G0^T G0 by explicit sums, W diagonal."""
    d = len(h[0]) if h else len(g[0])
    if q is None:
        q = [[F(int(i == j)) for j in range(d)] for i in range(d)]
    k = len(q[0])
    h0 = [[sum(F(row[t]) * q[t][j] for t in range(d)) for j in range(k)] for row in h]
    g0 = [[sum(F(row[t]) * q[t][j] for t in range(d)) for j in range(k)] for row in g]
    w = [F(1) / x for x in (r_diag or [1] * len(h))]
    a = [[sum(w[s] * h0[s][i] * h0[s][j] for s in range(len(h))) for j in range(k)] for i in range(k)]
    b = [[sum(g0[s][i] * g0[s][j] for s in range(len(g))) for j in range(k)] for i in range(k)]
    return a, b


def enumerated_lower(a, b, bound=2):
    k = len(a)
    best = None
    for z in product(range(-bound, bound + 1), repeat=k):
        den = sum(z[i] * a[i][j] * z[j] for i in range(k) for j in range(k))
        if den:
            value = sum(z[i] * b[i][j] * z[j] for i in range(k) for j in range(k)) / den
            best = value if best is None or value > best else best
    return best


def random_problem(rng, d, k, m, p):
    while True:
        h = [[rng.randint(-2, 2) for _ in range(d)] for _ in range(m)]
        g = [[rng.randint(-2, 2) for _ in range(d)] for _ in range(p)]
        q = [[F(rng.randint(-1, 2)) for _ in range(k)] for _ in range(d)]
        try:
            return TargetRecoveryProblem(h, g, q), h, g, q
        except ValueError:
            continue


# ----------------------------------- NX08-A -----------------------------------

class PSDCertificateTests(unittest.TestCase):
    def test_zero_pivot_examples(self):
        cert = psd_certificate([[0, 0], [0, 3]])
        self.assertIsInstance(cert, PSDCertificate)
        self.assertEqual(cert.zero_pivots, (0,))
        self.assertTrue(verify_psd_certificate([[0, 0], [0, 3]], cert))
        # Zero pivot with a nonzero off-diagonal entry is indefinite.
        bad = psd_certificate([[0, 1], [1, 5]])
        self.assertIsInstance(bad, NegativeWitness)
        z = bad.vector
        self.assertLess(5 * z[1] ** 2 + 2 * z[0] * z[1], 0)
        # Zero created by elimination, not present in the input.
        s = [[1, 1, 1], [1, 1, 1], [1, 1, 2]]
        cert = psd_certificate(s)
        self.assertEqual(cert.diagonal, (1, 0, 1))
        self.assertTrue(verify_psd_certificate(s, cert))
        self.assertIsInstance(psd_certificate([]), PSDCertificate)

    def test_random_agreement_with_principal_minor_oracle(self):
        rng = random.Random(8)
        for trial in range(400):
            n = rng.randint(1, 4)
            rank = rng.randint(0, n)
            m = [[rng.randint(-2, 2) for _ in range(n)] for _ in range(rank)]
            s = [[F(sum(m[t][i] * m[t][j] for t in range(rank))) for j in range(n)] for i in range(n)]
            if trial % 3 == 0:  # perturb to obtain indefinite or singular cases
                i, j = rng.randrange(n), rng.randrange(n)
                s[i][j] += F(rng.randint(-1, 1), rng.randint(1, 3))
                s[j][i] = s[i][j]
            cert = psd_certificate(s)
            self.assertEqual(isinstance(cert, PSDCertificate), psd_oracle(s), s)
            if isinstance(cert, PSDCertificate):
                self.assertTrue(verify_psd_certificate(s, cert))
            else:
                z = cert.vector
                self.assertEqual(sum(z[i] * s[i][j] * z[j] for i in range(n) for j in range(n)), cert.value)
                self.assertLess(cert.value, 0)

    def test_tampered_factors_rejected(self):
        s = [[4, 2, 0], [2, 2, 0], [0, 0, 0]]
        cert = psd_certificate(s)
        self.assertTrue(verify_psd_certificate(s, cert))
        lower = [list(r) for r in cert.lower]
        lower[1][0] += 1
        self.assertFalse(verify_psd_certificate(s, PSDCertificate(tuple(map(tuple, lower)), cert.diagonal)))
        self.assertFalse(verify_psd_certificate(s, PSDCertificate(cert.lower, (4, 1, F(-1)))))
        upper = [list(r) for r in cert.lower]
        upper[0][1] = F(1)
        self.assertFalse(verify_psd_certificate(s, PSDCertificate(tuple(map(tuple, upper)), cert.diagonal)))
        self.assertFalse(verify_psd_certificate(s, "certificate"))


class PacketExampleTests(unittest.TestCase):
    def test_equal_rank_different_conditioning(self):
        g = [(0, 1)]
        pa = TargetRecoveryProblem([(1, 0), (0, F(1, 100))], g)
        pb = TargetRecoveryProblem([(1, 0), (0, 1)], g)
        self.assertEqual(target_identifiability(pa).rank, target_identifiability(pb).rank)
        for problem, kappa2 in ((pa, 10000), (pb, 1)):
            br = bracket_target_amplification(problem)
            self.assertEqual((br.status, br.lower, br.upper), ("exact_sharp_constant", kappa2, kappa2))
            self.assertEqual(br.lower_witness, (0, 1))
            self.assertEqual(br.upper_certificate.zero_pivots, (1,))
            # Error guarantee at eps = 1/1000: kappa * eps = 1/10 and 1/1000.
            self.assertEqual(br.upper * F(1, 1000) ** 2, {10000: F(1, 100), 1: F(1, 10 ** 6)}[kappa2])
        self.assertEqual(certify_target_amplification(pa, 9999).status, "refuted")

    def test_hidden_target_then_admissible_constraint(self):
        p = TargetRecoveryProblem([(1, 0)], [(0, 1)])
        br = bracket_target_amplification(p)
        self.assertEqual(br.status, "unobservable")
        self.assertEqual(br.hidden_witness, (0, 1))
        self.assertIsNone(br.upper)
        self.assertRaises(ValueError, minimum_norm_decoder, p)
        constrained = TargetRecoveryProblem([(1, 0)], [(0, 1)], [(1,), (2,)])
        self.assertEqual(constrained.reduced_observations, ((1,),))
        self.assertEqual(constrained.reduced_target, ((2,),))
        br = bracket_target_amplification(constrained)
        self.assertEqual((br.lower, br.upper), (4, 4))

    def test_zero_and_empty_cases(self):
        self.assertEqual(bracket_target_amplification(TargetRecoveryProblem([], [(0, 0)])).upper, 0)
        self.assertEqual(bracket_target_amplification(TargetRecoveryProblem([], [], state_dimension=3)).upper, 0)
        empty = TargetRecoveryProblem([], [(1, 0)])
        self.assertEqual(bracket_target_amplification(empty).status, "unobservable")
        # Zero-dimensional admissible set: a known point; every target is known.
        point = TargetRecoveryProblem([(1, 1)], [(3, 4)], [(), ()], centre=(1, 2))
        br = bracket_target_amplification(point)
        self.assertEqual((br.status, br.upper), ("exact_sharp_constant", 0))
        self.assertEqual(minimum_norm_decoder(point), ((0,),))
        cert = certify_decoder_norm(point, ((0,),), 0)
        self.assertEqual(recover_target(point, (99,), cert).estimate, (11,))
        # Zero target with observations: kappa = 0 and a ratio-zero witness.
        br = bracket_target_amplification(TargetRecoveryProblem([(1, 0)], [(0, 0)]))
        self.assertEqual((br.lower, br.upper), (0, 0))


class SemanticsTests(unittest.TestCase):
    def test_upper_certificate_dominates_enumerated_directions(self):
        rng = random.Random(81)
        checked = 0
        while checked < 40:
            d, k = rng.randint(2, 3), rng.randint(1, 3)
            if k > d:
                continue
            problem, h, g, q = random_problem(rng, d, k, rng.randint(1, 3), rng.randint(1, 2))
            br = bracket_target_amplification(problem, F(1, 10 ** 8))
            a, b = raw_forms(h, g, q)
            if br.status == "unobservable":
                z = br.hidden_witness
                self.assertTrue(all(sum(a[i][j] * z[j] for j in range(k)) == 0 for i in range(k)))
                self.assertGreater(sum(z[i] * b[i][j] * z[j] for i in range(k) for j in range(k)), 0)
                continue
            checked += 1
            self.assertTrue(psd_oracle([[br.upper * a[i][j] - b[i][j] for j in range(k)] for i in range(k)]))
            low = enumerated_lower(a, b)
            if low is not None:
                self.assertLessEqual(low, br.upper)
            if br.lower_witness is not None:
                self.assertEqual(amplification_ratio(problem, br.lower_witness), br.lower)
            self.assertLessEqual(br.upper - br.lower, F(1, 10 ** 8))

    def test_basis_invariance_and_whitening(self):
        h, g = [(1, 1, 0), (0, 1, 2), (1, 0, 1)], [(1, 2, 0), (0, 1, -1)]
        q = [(1, 0), (1, 1), (0, 2)]
        t = [(2, 1), (1, 1)]  # invertible change of admissible coordinates
        qt = [tuple(sum(F(q[i][s]) * t[s][j] for s in range(2)) for j in range(2)) for i in range(3)]
        b1 = bracket_target_amplification(TargetRecoveryProblem(h, g, q), F(1, 10 ** 9))
        b2 = bracket_target_amplification(TargetRecoveryProblem(h, g, qt), F(1, 10 ** 9))
        self.assertTrue(b1.lower <= b2.upper and b2.lower <= b1.upper)
        # R = diag(4, 9, 1) is the same as dividing rows by 2 and 3.
        pr = TargetRecoveryProblem(h, g, q, [(4, 0, 0), (0, 9, 0), (0, 0, 1)])
        scaled = [tuple(F(x, s) for x in row) for row, s in zip(h, (2, 3, 1))]
        ps = TargetRecoveryProblem(scaled, g, q)
        self.assertEqual(pr.information_form(), ps.information_form())

    def test_decoders_and_recovery(self):
        h, g = [(1, 1), (1, 2), (3, 1)], [(1, -1), (2, 1)]
        problem = TargetRecoveryProblem(h, g)
        br = bracket_target_amplification(problem, F(1, 10 ** 9))
        best = minimum_norm_decoder(problem)
        rows = target_identifiability(problem).decoder
        nb = bracket_decoder_norm(problem, best, F(1, 10 ** 9))
        nr = bracket_decoder_norm(problem, rows, F(1, 10 ** 9))
        self.assertTrue(nb.lower <= br.upper and br.lower <= nb.upper)  # same constant
        self.assertGreater(nr.lower, br.upper)  # row-space decoder amplifies off-image noise
        cert = certify_decoder_norm(problem, best, nb.upper)
        self.assertIsInstance(cert, DecoderCertificate)
        self.assertIsInstance(certify_decoder_norm(problem, best, nb.lower / 2), NegativeWitness)
        rng = random.Random(3)
        for _ in range(30):
            x = tuple(F(rng.randint(-9, 9)) for _ in range(2))
            eta = tuple(F(rng.randint(-3, 3), 7) for _ in range(3))
            y = tuple(sum(a * b for a, b in zip(row, x)) + e for row, e in zip(h, eta))
            est = recover_target(problem, y, cert, sum(e * e for e in eta))
            truth = tuple(sum(a * b for a, b in zip(row, x)) for row in g)
            self.assertLessEqual(sum((u - v) ** 2 for u, v in zip(est.estimate, truth)), est.error_squared_bound)
        tampered = DecoderCertificate(cert.decoder, cert.beta_squared / 2, cert.certificate)
        self.assertRaises(ValueError, recover_target, problem, (0, 0, 0), tampered)
        wrong = DecoderCertificate(((1, 0, 0), (0, 0, 0)), cert.beta_squared, cert.certificate)
        self.assertRaises(ValueError, recover_target, problem, (0, 0, 0), wrong)
        self.assertGreater(decoder_ratio(problem, rows, nr.lower_witness), br.upper)

    def test_adversarial_witness_attains_lower_bound(self):
        problem = TargetRecoveryProblem([(1, 1), (0, 1)], [(1, 0)], centre=(5, -2))
        br = bracket_target_amplification(problem)
        self.assertEqual(br.upper, 2)
        best = minimum_norm_decoder(problem)
        w = adversarial_witness(problem, br.lower_witness, best)
        self.assertEqual(w.ratio, 2)
        self.assertEqual(w.decoder_errors_squared, (w.target_gap_squared, w.target_gap_squared))
        for state, noise in ((w.state_plus, w.noise_plus), (w.state_minus, w.noise_minus)):
            y = tuple(sum(a * b for a, b in zip(row, state)) + e
                      for row, e in zip(problem.observations, noise))
            self.assertEqual(y, w.observed)
        self.assertRaises(ValueError, adversarial_witness, problem, (0, 0))


class ValidationAndReceiptTests(unittest.TestCase):
    def test_type_and_shape_errors(self):
        self.assertRaises(TypeError, TargetRecoveryProblem, [(1.0, 0)], [(0, 1)])
        self.assertRaises(TypeError, TargetRecoveryProblem, [(True, 0)], [(0, 1)])
        self.assertRaises(TypeError, TargetRecoveryProblem, ["10"], [(0, 1)])
        self.assertRaises(ValueError, TargetRecoveryProblem, [(1, 0)], [(0, 1, 2)])
        self.assertRaises(ValueError, TargetRecoveryProblem, [(1, 0)], [(0, 1)], [(1, 2), (2, 4)])
        self.assertRaises(ValueError, TargetRecoveryProblem, [(1, 0)], [(0, 1)], [(1,)])
        self.assertRaises(ValueError, TargetRecoveryProblem, [(1, 0)], [(0, 1)], None, [(0,)])
        self.assertRaises(ValueError, TargetRecoveryProblem, [(1, 0), (0, 1)], [(0, 1)], None,
                          [(1, 2), (2, 1)])
        self.assertRaises(ValueError, TargetRecoveryProblem, [], [])
        self.assertRaises(ValueError, TargetRecoveryProblem, [(1, 0)], [(0, 1)], units={"target": ["K", "K"]})
        self.assertRaises(TypeError, TargetRecoveryProblem, [(1, 0)], [(0, 1)], units={"note": 3})
        p = TargetRecoveryProblem([(1, 0)], [(0, 1)])
        self.assertRaises(TypeError, certify_target_amplification, p, 1.5)
        self.assertRaises(ValueError, certify_target_amplification, p, -1)
        self.assertRaises(TypeError, bracket_target_amplification, p, F(1), True)
        self.assertRaises(ValueError, psd_certificate, [[1, 2], [3, 1]])

    def _receipt(self):
        problem = TargetRecoveryProblem([(1, 1, 0), (0, 1, 1), (1, 0, 2), (0, 0, 1)],
                                        [(1, 2, 3), (0, 1, -1)], [(1, 0), (0, 1), (1, 1)],
                                        units={"state": "K", "observations": "K", "target": "K"})
        br = bracket_target_amplification(problem, F(1, 10 ** 6))
        cert = certify_decoder_norm(problem, minimum_norm_decoder(problem), br.upper)
        return target_recovery_receipt(problem, br, cert, {"example": "receipt"})

    def test_receipt_replay_and_tampering(self):
        receipt = self._receipt()
        self.assertTrue(verify_target_recovery_receipt(receipt))
        import json
        self.assertTrue(verify_target_recovery_receipt(json.loads(json.dumps(receipt))))
        cases = []
        r = copy.deepcopy(receipt); r["problem"]["admissible_basis"]["entries"][2][1] = [2, 1]; cases.append(r)
        r = copy.deepcopy(receipt); r["identifiability"]["row_space_decoder"]["entries"][0][0] = [7, 1]; cases.append(r)
        r = copy.deepcopy(receipt); r["decoder"]["matrix"]["entries"][1][0] = [1, 3]; cases.append(r)
        r = copy.deepcopy(receipt); r["amplification_squared"]["upper_ldl"]["diagonal"][0] = [999, 1]; cases.append(r)
        r = copy.deepcopy(receipt); r["decoder"]["ldl"]["lower"]["entries"][1][0] = [5, 1]; cases.append(r)
        r = copy.deepcopy(receipt); up = r["amplification_squared"]["upper"]; r["amplification_squared"]["lower"] = [up[0] + 1, up[1]]; cases.append(r)
        r = copy.deepcopy(receipt); r["amplification_squared"]["upper"] = [0, 1]; cases.append(r)
        r = copy.deepcopy(receipt); r["amplification_squared"]["upper"] = [2, 4]; cases.append(r)
        r = copy.deepcopy(receipt); r["schema"] = "relational-height/1"; cases.append(r)
        for index, tampered in enumerate(cases):
            # Re-hash problem edits so the mathematics, not the digest, rejects them.
            from singularity.target_recovery import _digest
            tampered["problem_sha256"] = _digest(tampered["problem"])
            tampered["admissible_basis_sha256"] = _digest(tampered["problem"]["admissible_basis"])
            self.assertFalse(verify_target_recovery_receipt(tampered), index)

    def test_unobservable_receipt(self):
        problem = TargetRecoveryProblem([(1, 0, 0)], [(0, 1, 0)])
        receipt = target_recovery_receipt(problem)
        self.assertTrue(verify_target_recovery_receipt(receipt))
        receipt["hidden_witness"] = [[1, 1], [0, 1], [0, 1]]
        self.assertFalse(verify_target_recovery_receipt(receipt))


# ----------------------------------- NX08-B -----------------------------------

def brute_catalogue(options, target, kappa2):
    """Brute force from raw rows; kappa2=None tests the kernel condition."""
    best = None
    d = len(target[0])
    for size in range(len(options) + 1):
        for layout in combinations(range(len(options)), size):
            rows = [(row, w) for i in layout for row, w in zip(options[i][0], options[i][2])]
            a = [[sum(F(r[i]) * r[j] / w for r, w in rows) for j in range(d)] for i in range(d)]
            b = [[sum(F(t[i]) * t[j] for t in target) for j in range(d)] for i in range(d)]
            if kappa2 is None:
                # Kernel condition for PSD A, B: ker(A + B) = ker A, i.e. equal ranks.
                ok = _rank_by_minors(a) == _rank_by_minors([[a[i][j] + b[i][j] for j in range(d)] for i in range(d)])
            else:
                ok = psd_oracle([[kappa2 * a[i][j] - b[i][j] for j in range(d)] for i in range(d)])
            if ok:
                key = (sum(F(options[i][1]) for i in layout), len(layout), layout)
                best = key if best is None or key < best else best
    return best


def _rank_by_minors(a):
    n = len(a)
    for size in range(n, 0, -1):
        for rows in combinations(range(n), size):
            for cols in combinations(range(n), size):
                if perm_det([[a[i][j] for j in cols] for i in rows]) != 0:
                    return size
    return 0


class CatalogueTests(unittest.TestCase):
    # Rows, cost, per-row diagonal noise shape.
    RAW = (
        (((1, 0, 0),), 1, (1,)),
        (((1, F(1, 50), 0),), 1, (1,)),
        (((0, 1, 0),), 5, (1,)),
        (((0, 1, 1), (0, 0, 1)), 3, (1, 4)),
        (((0, 0, 1),), 1, (1,)),
        (((1, 1, 1),), 2, (9,)),
    )
    TARGET = ((0, 1, 0),)

    def options(self):
        return tuple(SensorOption(f"s{i}", rows, cost,
                                  [[w if r == c else 0 for c in range(len(rows))] for r, w in
                                   enumerate(shape)], "K")
                     for i, (rows, cost, shape) in enumerate(self.RAW))

    def test_equal_rank_cheap_sensors_unusable(self):
        options = self.options()
        cheap = layout_problem(options, (0, 1), self.TARGET, state_dimension=3)
        good = layout_problem(options, (0, 2), self.TARGET, state_dimension=3)
        self.assertEqual(target_identifiability(cheap).rank, target_identifiability(good).rank)
        self.assertEqual(target_identifiability(cheap).status, "identifiable")
        self.assertGreater(bracket_target_amplification(cheap).lower, 100)
        self.assertEqual(bracket_target_amplification(good).upper, 1)
        ident = cheapest_identifying_layout(options, self.TARGET)
        tight = cheapest_conditioned_layout(options, self.TARGET, 2)
        self.assertEqual(ident.layout, (0, 1))
        self.assertNotEqual(tight.layout, ident.layout)
        self.assertGreater(tight.cost, ident.cost)

    def test_pruned_matches_exhaustive_and_brute_force(self):
        options = self.options()
        raw = [(rows, cost, shape) for rows, cost, shape in self.RAW]
        for kappa2 in (None, 0, F(1, 2), 1, 2, 5, 50, 3000, 10 ** 6):
            if kappa2 is None:
                pruned = cheapest_identifying_layout(options, self.TARGET)
                full = cheapest_identifying_layout(options, self.TARGET, method="exhaustive")
            else:
                pruned = cheapest_conditioned_layout(options, self.TARGET, kappa2)
                full = cheapest_conditioned_layout(options, self.TARGET, kappa2, method="exhaustive")
            brute = brute_catalogue(raw, self.TARGET, kappa2)
            self.assertEqual((pruned.status, pruned.layout), (full.status, full.layout), kappa2)
            if brute is None:
                self.assertEqual(pruned.status, "infeasible")
            else:
                self.assertEqual((pruned.cost, pruned.layout), (brute[0], brute[2]), kappa2)
                self.assertLessEqual(pruned.tests, full.tests)
                if kappa2 is not None:
                    problem = layout_problem(options, pruned.layout, self.TARGET)
                    self.assertTrue(verify_psd_certificate(amplification_form(problem, kappa2),
                                                           pruned.certificate))

    def test_frontier_and_table(self):
        options = self.options()
        frontier = conditioning_frontier(options, self.TARGET, (1, 2, 5, 50, 3000))
        costs = [row["cost"] for row in frontier]
        self.assertEqual(costs, sorted(costs, reverse=True))
        for row in frontier:
            self.assertLessEqual(row["lower"], row["kappa_max_squared"])
        table = layout_table(options[:4], self.TARGET)
        self.assertEqual(len(table), 16)
        self.assertRaises(ValueError, cheapest_conditioned_layout, options * 3, self.TARGET, 1)
        self.assertRaises(ValueError, SensorOption, "x", ((1, 0, 0),), 0)
        self.assertRaises(TypeError, SensorOption, "x", ((1, 0, 0),), 1.0)


# ----------------------------------- NX08-C -----------------------------------

class ForecastAndThermalTests(unittest.TestCase):
    def test_synthetic_forecast(self):
        f = [(1, 1, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, F(1, 2))]
        c = [(1, 0, 1, 1)]
        q = [(1, 0, 0), (0, 1, 0), (0, 0, 0), (0, 0, 1)]
        raw = linear_forecast_problem(f, c, (0, 1, 2), [(1, 0, 0, 0)], 2)
        br = bracket_target_amplification(raw)
        self.assertEqual(br.status, "unobservable")
        self.assertEqual(br.hidden_witness, (1, 0, -1, 0))  # bias versus position
        values = [bracket_target_amplification(linear_forecast_problem(
            f, c, (0, 1, 2), [(1, 0, 0, 0)], tau, q)).upper for tau in range(6)]
        self.assertEqual(values, [89, 33, 5, 5, 33, 89])
        # Independent: square H0, so kappa^2 = ||g H0^-1||^2 with rows (1, t, 2^-t).
        h0 = [[F(1), F(t), F(1, 2 ** t)] for t in range(3)]
        for tau, value in enumerate(values):
            g = [F(1), F(tau), F(0)]
            # Solve c H0 = g by Cramer's rule with the permutation determinant.
            det = perm_det(h0)
            coeff = []
            for i in range(3):
                m = [row[:] for row in h0]
                m[i] = g
                coeff.append(perm_det(m) / det)
            self.assertEqual(sum(x * x for x in coeff), value)

    def test_exact_snap_resource_limit_and_units(self):
        f = [(1, 1, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, F(1, 2))]
        q = [(1, 0, 0), (0, 1, 0), (0, 0, 0), (0, 0, 1)]
        units = {"state": ["m", "m/step", "m", "m"], "observations": "m", "target": ["m", "m/step"]}
        p = linear_forecast_problem(f, [(1, 0, 1, 1)], (0, 1, 2, 3), [(1, 0, 0, 0), (0, 1, 0, 0)], 3, q,
                                    units=units)
        br = bracket_target_amplification(p)
        self.assertEqual((br.status, br.upper), ("exact_sharp_constant", F(5, 2)))
        self.assertEqual(amplification_ratio(p, br.lower_witness), F(5, 2))
        p1 = linear_forecast_problem(f, [(1, 0, 1, 1)], (0, 1, 2, 3), [(1, 0, 0, 0), (0, 1, 0, 0)], 1, q)
        stopped = bracket_target_amplification(p1, F(1, 10 ** 9), 0)
        self.assertEqual(stopped.status, "resource_limit")
        fine = bracket_target_amplification(p1, F(1, 10 ** 9))
        self.assertEqual(fine.status, "bracketed_sharp_constant")
        self.assertTrue(stopped.lower <= fine.lower <= fine.upper <= stopped.upper)
        receipt = target_recovery_receipt(p, br)
        self.assertEqual(receipt["problem"]["units"]["target"], ["m", "m/step"])
        self.assertTrue(verify_target_recovery_receipt(receipt))

    def test_thermal_target_with_nuisance(self):
        from singularity.thermal_diagnostics import build_plate_candidates
        nominal = build_plate_candidates(4)[0]
        n = 16
        cells = ({5, 6, 9, 10}, {1, 2, 4, 7, 8, 11, 13, 14}, {0, 3, 12, 15})
        cols = [tuple(F(int(i in s)) for i in range(n)) for s in cells]
        cols.append(tuple(F(1 if i % 4 < 2 else -1) for i in range(n)))
        q = tuple(tuple(col[i] for col in cols) for i in range(n))
        mean = [tuple(F(1, 16) for _ in range(n))]
        p = thermal_target_problem(nominal, (0, 1), (0, 1, 2), mean, 4, q,
                                   units={"state": "K_model", "observations": "K_model",
                                          "target": "K_model"})
        ident = target_identifiability(p)
        self.assertEqual(ident.status, "identifiable")
        self.assertIn((0, 0, 0, 1), ident.kernel_basis)  # antisymmetric nuisance invisible, harmless
        early = thermal_target_problem(nominal, (0, 1, 2, 3), (0,), mean, 4, q)
        self.assertEqual(bracket_target_amplification(early).status, "unobservable")
        br = bracket_target_amplification(p, F(1, 10 ** 6))
        self.assertIn(br.status, ("exact_sharp_constant", "bracketed_sharp_constant"))
        w = adversarial_witness(p, br.lower_witness, minimum_norm_decoder(p))
        self.assertEqual(w.ratio, br.lower)
        self.assertLessEqual(w.decoder_errors_squared[0], br.upper * w.noise_squared)


if __name__ == "__main__":
    unittest.main()
