"""Adaptive in-document counts: recount oracle, normalization and causality."""
import unittest

from singularity.training.byte_experts import AdaptiveDocumentCounts, CountByteExpert, adaptive_document_probabilities

try:
    import numpy as np
except ImportError:
    np = None


def recount(prefix, base, max_order):
    """Recompute Witten-Bell from all earlier (context, target) events."""
    distribution = list(base)
    # Targets are prefix[1:]; the event at j has history prefix[:j].
    for order in range(min(max_order, len(prefix)) + 1):
        context = prefix[len(prefix) - order:] if order else b""
        followers = {}
        for j in range(1, len(prefix)):
            if j >= order and prefix[j - order:j] == context:
                followers[prefix[j]] = followers.get(prefix[j], 0) + 1
        if followers:
            distinct, total = len(followers), sum(followers.values())
            distribution = [(followers.get(b, 0) + distinct * distribution[b]) / (total + distinct) for b in range(256)]
    return distribution


@unittest.skipIf(np is None, "optional numpy unavailable")
class AdaptiveCountTests(unittest.TestCase):
    def setUp(self):
        self.expert = CountByteExpert.fit(b"the cat sat on the mat; the hat sat flat.\n" * 3, alpha=.05, sequence_length=8)

    def test_matches_independent_recount(self):
        raw = b"abracadabra abracadabra!"
        output = adaptive_document_probabilities(self.expert, raw, max_order=3)
        for index in range(len(raw) - 1):
            start = max((index // 8) * 8, index - 1)
            base = self.expert.probabilities(raw[start:index + 1])
            np.testing.assert_allclose(output[index], recount(raw[:index + 1], base, 3), rtol=0, atol=1e-12)
            self.assertAlmostEqual(output[index].sum(), 1., places=12)

    def test_future_bytes_do_not_change_earlier_rows(self):
        first = adaptive_document_probabilities(self.expert, b"hello hello hello", 4)
        second = adaptive_document_probabilities(self.expert, b"hello hellX yyyyy", 4)
        np.testing.assert_array_equal(first[:10], second[:10])
        self.assertFalse(np.array_equal(first[11], second[11]))

    def test_order_zero_and_validation(self):
        model = AdaptiveDocumentCounts(0)
        uniform = np.full(256, 1 / 256)
        model.update(65)
        self.assertGreater(model.probabilities(uniform)[65], .5)
        model.reset()
        np.testing.assert_array_equal(model.probabilities(uniform), uniform)
        with self.assertRaises(ValueError):
            model.update(256)
        with self.assertRaises(ValueError):
            model.probabilities(np.ones(256))
        with self.assertRaises(ValueError):
            AdaptiveDocumentCounts(9)


if __name__ == "__main__":
    unittest.main()
