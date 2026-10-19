"""Arbitrary-vocabulary counts checked against independent prefix recounts."""
import importlib.util
import unittest

from singularity.training.token_experts import AdaptiveTokenCounts


@unittest.skipUnless(importlib.util.find_spec("numpy"), "optional NumPy unavailable")
class AdaptiveTokenCountTests(unittest.TestCase):
    def test_independent_recount_and_positive_mass(self):
        import numpy as np

        tokens, size, order = [4, 2, 4, 2, 4, 1, 2, 4, 2, 4, 2], 7, 3
        model = AdaptiveTokenCounts(size, order)
        model.reset(tokens[:1])
        for target_index in range(1, len(tokens)):
            prefix = tokens[:target_index]
            expected = [1 / size] * size
            for k in range(min(order, len(prefix)) + 1):
                context = prefix[-k:] if k else []
                followers = {}
                for j in range(1, len(prefix)):
                    if j >= k and prefix[j-k:j] == context:
                        followers[prefix[j]] = followers.get(prefix[j], 0) + 1
                if followers:
                    distinct, total = len(followers), sum(followers.values())
                    expected = [(followers.get(v, 0) + distinct * expected[v]) / (total + distinct)
                                for v in range(size)]
            actual = model.probabilities()
            np.testing.assert_allclose(actual, expected, rtol=0, atol=1e-14)
            self.assertTrue((actual > 0).all())
            self.assertAlmostEqual(float(actual.sum()), 1, places=13)
            model.update(tokens[target_index])

    def test_future_mutation_and_document_reset(self):
        import numpy as np

        def score(tokens):
            model = AdaptiveTokenCounts(1000, 4)
            model.reset(tokens[:1])
            rows = []
            for token in tokens[1:]:
                rows.append(model.probabilities())
                model.update(token)
            model.reset(tokens[:1])
            np.testing.assert_array_equal(model.probabilities(), np.full(1000, .001))
            return np.array(rows)
        original = score([900, 1, 2, 900, 1, 2, 900])
        mutated = score([900, 1, 2, 900, 999, 998, 997])
        np.testing.assert_array_equal(original[:4], mutated[:4])
        self.assertFalse(np.array_equal(original[4], mutated[4]))

    def test_neural_backoff_is_normalized_and_not_mutated(self):
        import numpy as np

        model = AdaptiveTokenCounts(3, 4)
        base = np.array([.2, .3, .5])
        np.testing.assert_array_equal(model.probabilities(base), base)
        model.update(1)
        np.testing.assert_allclose(model.probabilities(base), [.1, .65, .25])
        np.testing.assert_array_equal(base, [.2, .3, .5])
        with self.assertRaises(ValueError):
            model.probabilities([0, .5, .5])
        with self.assertRaises(ValueError):
            model.update(3)
        with self.assertRaises(ValueError):
            model.reset([True])


if __name__ == "__main__":
    unittest.main()
