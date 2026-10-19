"""NX10-A: constant-input response-tail certificates against independent closed forms."""
import unittest
from fractions import Fraction as F

from singularity.horizon_design import (LinearCandidate, MetricFailure, QuadraticMetric, certify_metric,
                                        certify_response_tail, step_system)


def readings(A, b, c, x0, count):
    """Independent forward iteration y_k = c x_k, x_{k+1} = A x_k + b."""
    n, x, out = len(A), list(x0), []
    for _ in range(count):
        out.append(sum(ci * xi for ci, xi in zip(c, x)))
        x = [sum(A[i][j] * x[j] for j in range(n)) + b[i] for i in range(n)]
    return out


class ScalarExamples(unittest.TestCase):
    def check(self, A, B, u, y_inf, closed_form):
        system = step_system(LinearCandidate("c", A, B, ((1,) + (0,) * (len(A) - 1),)), (u,), 0)
        tail = certify_response_tail(system)
        self.assertNotIsInstance(tail, MetricFailure)
        self.assertEqual(tail.steady_output, y_inf)
        ys = readings(system.A, system.b, system.c, system.x0, 40)
        for k, y in enumerate(ys):
            if closed_form:
                self.assertEqual(y, closed_form(k))
            self.assertLessEqual(abs(y - y_inf), tail.bound(k), k)
        return tail

    def test_half_decay(self):
        # y_k = 2 (1 - 2^-k), y_inf = 2.
        self.check(((F(1, 2),),), ((1,),), 1, F(2), lambda k: 2 * (1 - F(1, 2) ** k))

    def test_alternating_decay(self):
        # x* = 2/(1 + 1/3) = 3/2; y_k = 3/2 (1 - (-1/3)^k).
        self.check(((F(-1, 3),),), ((2,),), 1, F(3, 2), lambda k: F(3, 2) * (1 - F(-1, 3) ** k))

    def test_nonnormal_transient(self):
        # Spectral radius 1/2 but a large transient: |y_k - y_inf| grows before decaying.
        A = ((F(1, 2), F(10)), (F(0), F(1, 2)))
        tail = self.check(A, ((0,), (1,)), 1, F(40), None)
        self.assertGreater(tail.K, abs(0 - 40))
        # Free response from x0 = (0, 1): y_k = 10 k 2^(1-k) rises to 10 before decaying.
        free = step_system(LinearCandidate("f", A, ((0,), (1,)), ((1, 0),), initial=(0, 1)), (0,), 0)
        ftail = certify_response_tail(free)
        ys = readings(free.A, free.b, free.c, free.x0, 40)
        self.assertEqual(ys[:4], [0, 10, 10, F(15, 2)])
        self.assertEqual(max(ys), 10)
        for k, y in enumerate(ys):
            self.assertEqual(y, 10 * k * F(1, 2) ** (k - 1) if k else 0)
            self.assertLessEqual(abs(y), ftail.bound(k))

    def test_anchor_tightens(self):
        system = step_system(LinearCandidate("c", ((F(1, 2),),), ((1,),), ((1,),)), (1,), 0)
        early, late = certify_response_tail(system), certify_response_tail(system, anchor=10)
        self.assertLess(late.K, early.K)
        with self.assertRaises(ValueError):
            late.bound(9)


class MarginalAndTamper(unittest.TestCase):
    def test_marginal_cases_are_refused(self):
        for A in (((F(1),),), ((F(-1),),), ((F(1, 2), F(0)), (F(0), F(1)))):
            result = certify_metric(A)
            self.assertIsInstance(result, MetricFailure)
            self.assertFalse(result.schur_stable)
        system = step_system(LinearCandidate("m", ((F(1, 2), F(0)), (F(0), F(1))), ((0,), (0,)),
                                             ((1, 0),)), (0,), 0)
        self.assertIsInstance(certify_response_tail(system), MetricFailure)

    def test_metric_tamper_rejection(self):
        A = ((F(1, 2),),)
        good = certify_metric(A, P=((F(1),),), rho=F(1, 2))
        self.assertIsInstance(good, QuadraticMetric)
        with self.assertRaises(ValueError):
            QuadraticMetric(A, ((F(1),),), F(1, 4), F(1, 3))      # rho^2 < gamma^2
        with self.assertRaises(ValueError):
            QuadraticMetric(A, ((F(1),),), F(1, 9), F(1, 3))      # contraction fails
        with self.assertRaises(ValueError):
            QuadraticMetric(A, ((F(-1),),), F(1, 4), F(1, 2))     # P not positive definite
        spec = good.spec()
        spec["rho"] = spec["rho"][:1] + [spec["rho"][1] * 3] if isinstance(spec["rho"], list) else spec["rho"]
        with self.assertRaises((ValueError, TypeError)):
            QuadraticMetric.from_spec(spec)
        self.assertIsInstance(certify_metric(A, P=((F(1),),), rho=F(1, 3)), MetricFailure)
        other = step_system(LinearCandidate("o", ((F(1, 3),),), ((1,),), ((1,),)), (1,), 0)
        with self.assertRaises(ValueError):
            certify_response_tail(other, good)                    # metric for a different matrix

    def test_exact_input_contract(self):
        for bad in (0.5, True, "1/2"):
            with self.assertRaises(TypeError):
                LinearCandidate("x", ((bad,),), ((1,),), ((1,),))


if __name__ == "__main__":
    unittest.main()
