"""Independent causal, marginal-likelihood and regret contracts for online mixing."""
import math
import unittest

import json

from singularity.training.online_blend import (
    BayesianByteBlend, VectorizedBlendState, score_online_probabilities, score_online_probabilities_fast,
)

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


@unittest.skipIf(np is None, "optional numpy unavailable")
class VectorizedBlendTests(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(4242)
        self.neural = rng.dirichlet(np.full(16, .2), 900)
        self.counts = rng.dirichlet(np.ones(16), 900)
        self.targets = rng.integers(0, 16, 900)

    def test_matches_reference_loop_and_preserves_grid_bound(self):
        loop = score_online_probabilities(self.neural, self.counts, self.targets)
        fast = score_online_probabilities_fast(self.neural, self.counts, self.targets)
        for key in ("target_nll_nats", "prior_to_target_count_weights"):
            np.testing.assert_allclose(fast[key], loop[key], rtol=0, atol=1e-9)
        np.testing.assert_array_equal(fast["target_correct"], loop["target_correct"])
        audit = fast["audit"]
        self.assertAlmostEqual(audit["online_cumulative_nll"], loop["audit"]["online_cumulative_nll"], places=8)
        self.assertGreaterEqual(audit["bound_slack_nats"], -1e-9)
        self.assertLessEqual(audit["regret_nats"], math.log(21) + 1e-9)
        self.assertAlmostEqual(audit["marginal_likelihood_identity_error_nats"], 0., delta=1e-8)
        self.assertEqual(audit["best_fixed_grid_count_weight"], loop["audit"]["best_fixed_grid_count_weight"])

    def test_every_chunk_size_gives_identical_per_target_results(self):
        whole = score_online_probabilities_fast(self.neural, self.counts, self.targets, chunk_size=None)
        for size in (1, 2, 17, 256, 899, 900, 5000):
            chunked = score_online_probabilities_fast(self.neural, self.counts, self.targets, chunk_size=size)
            for key in ("target_nll_nats", "prior_to_target_count_weights", "target_correct"):
                np.testing.assert_array_equal(chunked[key], whole[key])

    def test_save_and_resume_is_exact(self):
        whole = VectorizedBlendState()
        reference = whole.score_chunk(self.neural, self.counts, self.targets)
        first = VectorizedBlendState()
        head = first.score_chunk(self.neural[:333], self.counts[:333], self.targets[:333])
        resumed = VectorizedBlendState.from_dict(json.loads(json.dumps(first.to_dict())))
        tail = resumed.score_chunk(self.neural[333:], self.counts[333:], self.targets[333:])
        np.testing.assert_array_equal(np.concatenate((head["target_nll_nats"], tail["target_nll_nats"])),
                                      reference["target_nll_nats"])
        np.testing.assert_array_equal(resumed.cumulative_log_likelihood, whole.cumulative_log_likelihood)
        self.assertEqual(resumed.targets_seen, 900)
        bad = first.to_dict()
        bad["cumulative_log_likelihood"][0] = (1.).hex()
        with self.assertRaises(ValueError):
            VectorizedBlendState.from_dict(bad)

    def test_future_target_mutation_cannot_change_earlier_rows(self):
        other = self.targets.copy()
        other[500:] = (other[500:] + 3) % 16
        first = score_online_probabilities_fast(self.neural, self.counts, self.targets, chunk_size=64)
        second = score_online_probabilities_fast(self.neural, self.counts, other, chunk_size=64)
        np.testing.assert_array_equal(first["prior_to_target_count_weights"][:501],
                                      second["prior_to_target_count_weights"][:501])
        np.testing.assert_array_equal(first["target_nll_nats"][:500], second["target_nll_nats"][:500])
        self.assertNotEqual(first["prior_to_target_count_weights"][501], second["prior_to_target_count_weights"][501])

    def test_rejects_invalid_inputs_and_impossible_targets(self):
        bad = self.neural.copy()
        bad[3, 0] = np.nan
        with self.assertRaises(ValueError):
            score_online_probabilities_fast(bad, self.counts, self.targets)
        with self.assertRaises(ValueError):
            score_online_probabilities_fast(self.neural, self.counts, self.targets.astype(float))
        with self.assertRaises(ValueError):
            score_online_probabilities_fast(self.neural, self.counts, self.targets, chunk_size=0)
        zero = np.array([[1., 0.]])
        with self.assertRaises(ValueError):
            score_online_probabilities_fast(zero, zero, np.array([1]))


if __name__ == "__main__":
    unittest.main()
