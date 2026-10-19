"""Causal Witten--Bell adaptation for an arbitrary tokenizer vocabulary.

This is a standard interpolated count model, not neural training.  Every
context/follower count comes from targets observed earlier in the document.
The caller must emit the prediction before calling ``update`` on its target.
"""
from __future__ import annotations


class AdaptiveTokenCounts:
    """Document-local order-k counts over a strictly positive base.

    ``probabilities()`` defaults to a uniform distribution.  A caller may
    instead supply a causal neural distribution as its backoff base.  For
    each observed context, p = (counts + distinct_followers * p) /
    (total_followers + distinct_followers), from order zero upward.
    """

    def __init__(self, vocabulary_size, max_order=4):
        if (not isinstance(vocabulary_size, int) or isinstance(vocabulary_size, bool)
                or vocabulary_size < 1):
            raise ValueError("vocabulary_size must be a positive integer")
        if (not isinstance(max_order, int) or isinstance(max_order, bool)
                or not 0 <= max_order <= 8):
            raise ValueError("max_order must be an integer between zero and eight")
        self.vocabulary_size = vocabulary_size
        self.max_order = max_order
        self.reset()

    def _token(self, value):
        if (not isinstance(value, int) or isinstance(value, bool)
                or not 0 <= value < self.vocabulary_size):
            raise ValueError("target must be a vocabulary index")
        return value

    def reset(self, context=()):
        """Clear learned counts; optional initial context is not a target."""
        context = tuple(self._token(value) for value in context)
        self.history = context[-self.max_order:] if self.max_order else ()
        self.tables = [dict() for _ in range(self.max_order + 1)]
        self.totals = [dict() for _ in range(self.max_order + 1)]

    def probabilities(self, base=None):
        import numpy as np

        if base is None:
            distribution = np.full(self.vocabulary_size, 1 / self.vocabulary_size, dtype=np.float64)
        else:
            distribution = np.array(base, dtype=np.float64)
            if (distribution.shape != (self.vocabulary_size,) or not np.all(distribution > 0)
                    or not np.isfinite(distribution).all() or abs(distribution.sum() - 1) > 1e-9):
                raise ValueError("base must be finite, strictly positive, and normalized")
        for order in range(min(self.max_order, len(self.history)) + 1):
            context = self.history[-order:] if order else ()
            row = self.tables[order].get(context)
            if row:
                distinct, total = len(row), self.totals[order][context]
                distribution *= distinct
                for token, count in row.items():
                    distribution[token] += count
                distribution /= total + distinct
        return distribution

    def update(self, target):
        target = self._token(target)
        for order in range(min(self.max_order, len(self.history)) + 1):
            context = self.history[-order:] if order else ()
            row = self.tables[order].setdefault(context, {})
            row[target] = row.get(target, 0) + 1
            self.totals[order][context] = self.totals[order].get(context, 0) + 1
        self.history = (self.history + (target,))[-self.max_order:] if self.max_order else ()
