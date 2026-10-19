"""Independent causal, marginal-likelihood and regret contracts for online mixing."""
import math
import unittest

from singularity.training.online_blend import BayesianByteBlend, score_online_probabilities

try:
    import numpy as np
except ImportError:
    np = None


class BayesianBlendTests(unittest.TestCase):
    def test_predict_then_observe_contract(self):
        blend = BayesianByteBlend((0., .5, 1.))
        with self.assertRaises(RuntimeError):
            blend.observe(0)
        prediction = blend.predict((.9, .1), (.2, .8))
        self.assertAlmostEqual(prediction[0], .55)
        with self.assertRaises(RuntimeError):
            blend.predict((.9, .1), (.2, .8))
        loss = blend.observe(0)
        self.assertAlmostEqual(loss, -math.log(.55))
        self.assertLess(blend.posterior_count_weight, .5)

    def test_exact_marginal_identity_and_regret(self):
        neural, counts, targets = ((.8, .2), (.3, .7), (0, 0, 1, 0, 1))
        grid = (0., .25, .5, .75, 1.)
        blend = BayesianByteBlend(grid)
        products = []
        for weight in grid:
            products.append(math.prod(((1-weight)*neural[target]+weight*counts[target]) for target in targets))
        for target in targets:
            prediction = blend.predict(neural, counts)
            self.assertAlmostEqual(blend.observe(target), -math.log(prediction[target]), places=14)
        audit = blend.guarantee()
        self.assertAlmostEqual(audit["online_cumulative_nll"], -math.log(sum(products)/len(products)), places=13)
        self.assertGreaterEqual(audit["bound_slack_nats"], -1e-12)
        self.assertAlmostEqual(audit["marginal_likelihood_identity_error_nats"], 0., places=13)

    def test_log_domain_does_not_underflow_long_sequence(self):
        blend = BayesianByteBlend()
        for _ in range(1200):
            blend.predict((1e-250, 1.), (1e-220, 1.))
            blend.observe(0)
        audit = blend.guarantee()
        self.assertTrue(math.isfinite(audit["online_cumulative_nll"]))
        self.assertAlmostEqual(sum(audit["final_posterior"]), 1.)
        self.assertGreaterEqual(audit["bound_slack_nats"], -1e-5)
        self.assertAlmostEqual(audit["marginal_likelihood_identity_error_nats"], 0., delta=1e-5)

    def test_invalid_grid_and_distribution(self):
        for grid in ((), (0., 0.), (-.1, .5), (.5, math.nan)):
            with self.assertRaises(ValueError):
                BayesianByteBlend(grid)
        blend = BayesianByteBlend()
        with self.assertRaises(ValueError):
            blend.predict((.2, .2), (.5, .5))
        blend.predict((1., 0.), (1., 0.))
        with self.assertRaises(ValueError):
            blend.observe(1)

    @unittest.skipIf(np is None, "optional numpy unavailable")
    def test_future_targets_cannot_change_earlier_predictions(self):
        rng = np.random.default_rng(90210)
        neural, counts = rng.dirichlet(np.ones(4), 40), rng.dirichlet(np.ones(4), 40)
        targets = rng.integers(0, 4, 40)
        other = targets.copy()
        other[19:] = (other[19:]+1)%4
        first = score_online_probabilities(neural, counts, targets)
        second = score_online_probabilities(neural, counts, other)
        np.testing.assert_array_equal(first["prior_to_target_count_weights"][:20], second["prior_to_target_count_weights"][:20])
        np.testing.assert_array_equal(first["target_nll_nats"][:19], second["target_nll_nats"][:19])
        self.assertNotEqual(first["prior_to_target_count_weights"][20], second["prior_to_target_count_weights"][20])

    @unittest.skipIf(np is None, "optional numpy unavailable")
    def test_fast_scoring_matches_public_streaming_api(self):
        neural = np.array([[.8,.2],[.4,.6],[.3,.7]])
        counts = np.array([[.2,.8],[.9,.1],[.6,.4]])
        targets = np.array([0,1,1])
        batch = score_online_probabilities(neural, counts, targets)
        stream = BayesianByteBlend()
        for index, target in enumerate(targets):
            stream.predict(neural[index], counts[index])
            self.assertAlmostEqual(stream.observe(int(target)), batch["target_nll_nats"][index], places=14)
        self.assertEqual(stream.guarantee(), batch["audit"])


if __name__ == "__main__":
    unittest.main()
