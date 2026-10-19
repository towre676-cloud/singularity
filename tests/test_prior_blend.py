"""Nonuniform-prior mixtures: exact rational identities and causal contracts."""
from fractions import Fraction
import itertools
import importlib.util
import math
from pathlib import Path
import unittest

from singularity.training.prior_blend import PriorBayesianBlend


class PriorBlendTests(unittest.TestCase):
    def test_exact_rational_joint_probability_and_all_binary_sequences(self):
        grid = (Fraction(0), Fraction(1, 2), Fraction(1))
        priors = (Fraction(19, 20), Fraction(1, 40), Fraction(1, 40))
        all_joint_probability = Fraction(0)
        for targets in itertools.product((0, 1), repeat=5):
            state = PriorBayesianBlend(tuple(float(w) for w in grid), tuple(float(p) for p in priors))
            likelihoods = [Fraction(1)] * len(grid)
            online_joint = Fraction(1)
            history = []
            for target in targets:
                neural = (Fraction(2, 3), Fraction(1, 3))
                counts = (Fraction(history.count(0) + 1, len(history) + 2),
                          Fraction(history.count(1) + 1, len(history) + 2))
                evidence = sum(p * likelihood for p, likelihood in zip(priors, likelihoods))
                posterior = [p * likelihood / evidence for p, likelihood in zip(priors, likelihoods)]
                exact_prediction = [sum(p * ((1 - w) * neural[y] + w * counts[y])
                                        for p, w in zip(posterior, grid)) for y in (0, 1)]
                self.assertEqual(sum(exact_prediction), Fraction(1))
                actual = state.predict(tuple(map(float, neural)), tuple(map(float, counts)))
                for left, right in zip(actual, exact_prediction):
                    self.assertAlmostEqual(left, float(right), places=14)
                state.observe(target)
                online_joint *= exact_prediction[target]
                likelihoods = [likelihood * ((1 - w) * neural[target] + w * counts[target])
                               for likelihood, w in zip(likelihoods, grid)]
                self.assertEqual(online_joint, sum(p * likelihood for p, likelihood in zip(priors, likelihoods)))
                history.append(target)
            # An exact finite verification of the mixture identity and its
            # per-comparator inequality; logarithms are checked afterward.
            for p, likelihood in zip(priors, likelihoods):
                self.assertGreaterEqual(online_joint, p * likelihood)
            all_joint_probability += online_joint
            audit = state.guarantee()
            exact_loss = -math.log(float(online_joint))
            self.assertAlmostEqual(audit["online_cumulative_nll"], exact_loss, places=13)
            self.assertAlmostEqual(audit["marginal_likelihood_cumulative_nll"], exact_loss, places=13)
            self.assertGreaterEqual(audit["bound_slack_nats"], -1e-13)
            self.assertGreaterEqual(audit["pure_neural_protection_slack_nats"], -1e-13)
        self.assertEqual(all_joint_probability, Fraction(1))

    def test_default_protects_neural_with_declared_ceiling(self):
        state = PriorBayesianBlend()
        self.assertAlmostEqual(state.initial_prior[0], .95, places=15)
        self.assertAlmostEqual(math.fsum(state.initial_prior), 1, places=15)
        for value in state.initial_prior[1:]:
            self.assertAlmostEqual(value, .0025, places=15)
        for _ in range(100):
            state.predict((.999, .001), (.001, .999))
            state.observe(0)
        audit = state.guarantee()
        self.assertAlmostEqual(audit["pure_neural_extra_loss_ceiling_nats"], -math.log(.95), places=14)
        self.assertLessEqual(audit["online_cumulative_nll"] - audit["pure_neural_cumulative_nll"], -math.log(.95) + 1e-12)
        self.assertNotIn("log_grid_size_nats", audit)

    def test_causality_and_predict_observe_contract(self):
        def run(targets):
            state, predictions, weights = PriorBayesianBlend(), [], []
            for target in targets:
                weights.append(state.posterior_count_weight)
                predictions.append(state.predict((.3, .7), (.8, .2)))
                state.observe(target)
            return predictions, weights
        first = run([0, 1, 0, 0, 1, 0])
        second = run([0, 1, 0, 1, 0, 1])
        self.assertEqual(first[0][:4], second[0][:4])
        self.assertEqual(first[1][:4], second[1][:4])
        self.assertNotEqual(first[0][4], second[0][4])
        state = PriorBayesianBlend()
        with self.assertRaises(RuntimeError):
            state.observe(0)
        state.predict((.3, .7), (.8, .2))
        with self.assertRaises(RuntimeError):
            state.predict((.3, .7), (.8, .2))
        with self.assertRaises(RuntimeError):
            state.guarantee()

    def test_custom_prior_validation_and_comparator_choice(self):
        state = PriorBayesianBlend((.25, .75), (.1, .9))
        state.predict((.2, .8), (.7, .3))
        state.observe(0)
        audit = state.guarantee()
        self.assertAlmostEqual(audit["best_prior_adjusted_cumulative_nll"],
                               min(loss - math.log(prior) for loss, prior in zip(audit["fixed_grid_cumulative_nll"], (.1, .9))))
        self.assertNotIn("pure_neural_extra_loss_ceiling_nats", audit)
        with self.assertRaises(ValueError):
            PriorBayesianBlend((.25, .75))
        for prior in ((0., 1.), (-.1, 1.1), (.2, .2), (.1,), (math.nan, .5)):
            with self.assertRaises(ValueError):
                PriorBayesianBlend((0., 1.), prior)
        singleton = PriorBayesianBlend((0.,))
        singleton.predict((.4, .6), (.8, .2))
        singleton.observe(1)
        self.assertAlmostEqual(singleton.guarantee()["pure_neural_extra_loss_ceiling_nats"], 0.)

    def test_retained_target_loss_replay_matches_full_distribution_predictions(self):
        from singularity.training.online_blend import BayesianByteBlend

        root = Path(__file__).resolve().parents[1]
        spec = importlib.util.spec_from_file_location("prior_replay_for_tests", root / "scripts/replay_pretrained_prior.py")
        replay = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(replay)
        targets = [0, 1, 1, 0, 1, 0, 1, 1]
        neural, counts = (.4, .6), (.8, .2)
        equal, protected = BayesianByteBlend(), PriorBayesianBlend()
        equal_losses, expected_losses = [], []
        for target in targets:
            equal.predict(neural, counts)
            protected.predict(neural, counts)
            equal_losses.append(equal.observe(target))
            expected_losses.append(protected.observe(target))
        record = {"document": 0, "domain": "legal_prose", "name": "synthetic", "targets": len(targets),
                  "token_ids_sha256": "synthetic-test-identity", "losses_hex": {
                      "neural": [(-math.log(neural[t])).hex() for t in targets],
                      "adaptive_count": [(-math.log(counts[t])).hex() for t in targets],
                      "online_blend": [v.hex() for v in equal_losses]}}
        result = replay.replay_document(record)
        actual = [float.fromhex(v) for v in result["protected_target_losses_hex"]]
        for left, right in zip(actual, expected_losses):
            self.assertAlmostEqual(left, right, places=14)
        self.assertGreaterEqual(result["prior_guarantee"]["pure_neural_protection_slack_nats"], -1e-13)
        self.assertEqual(result["arms"]["neural"]["loss_sum_nats_hex"],
                         math.fsum(-math.log(neural[t]) for t in targets).hex())


if __name__ == "__main__":
    unittest.main()
