"""Protected causal adaptation from observed repetition, without neural updates.

A policy gates a fixed neural/count mixture using only an observed context's
past follower count. Bayesian aggregation gives at most -log(.95) additional
whole-document log loss over pure neural, in exact arithmetic. This standard
mixture bound does not promise improvement or identify a best policy online.
"""
from __future__ import annotations

import math

from .online_blend import _log_mixture, _logsumexp


REPETITION_POLICIES = tuple({"id": f"order{order}_support{support}_alpha{int(alpha * 100):03d}",
                             "min_order": order, "min_support": support, "alpha": alpha}
                            for order in (1, 2, 3) for support in (1, 2) for alpha in (.25, .5, 1.))


def repetition_feature(counts):
    """Describe the longest context row present before the next prediction."""
    feature = {"context": list(counts.history), "longest_order": -1, "support": 0, "distinct": 0}
    for order in range(min(counts.max_order, len(counts.history)) + 1):
        context = counts.history[-order:] if order else ()
        row = counts.tables[order].get(context)
        if row:
            feature.update(longest_order=order, support=counts.totals[order][context], distinct=len(row))
    return feature


def gate_enabled(policy, feature):
    return feature["longest_order"] >= policy["min_order"] and feature["support"] >= policy["min_support"]


def count_target_probability(counts, target):
    """Index a causal uniform-backed Witten--Bell distribution without arrays."""
    target = counts._token(target)
    probability = 1. / counts.vocabulary_size
    for order in range(min(counts.max_order, len(counts.history)) + 1):
        context = counts.history[-order:] if order else ()
        row = counts.tables[order].get(context)
        if row:
            total, distinct = counts.totals[order][context], len(row)
            probability = (row.get(target, 0) + distinct * probability) / (total + distinct)
    return probability


class ProtectedRepetitionBlend:
    """Streaming protected mixture with a predict-before-observe contract.

    ``predict_weight(feature)`` returns the count weight to apply to the full
    current neural/count distributions. The feature must come from the
    prefix. Only afterward may ``observe(neural_target, count_target)`` see
    the realized target probabilities. Counts remain the caller's state and
    should be updated after observation. Construct one object per document.

    With one supplied policy the prior is .95 pure neural/.05 that gate.
    With multiple policies, the remaining .05 is spread equally. An empty
    policy set is a pure-neural predictor with zero excess-loss ceiling.
    """

    def __init__(self, policies=REPETITION_POLICIES, neural_prior=.95):
        self.policies = tuple(dict(policy) for policy in policies)
        if (not math.isfinite(neural_prior) or not 0 < neural_prior < 1):
            raise ValueError("neural_prior must lie strictly between zero and one")
        identifiers = []
        for policy in self.policies:
            if (not isinstance(policy.get("min_order"), int) or isinstance(policy["min_order"], bool)
                    or not 0 <= policy["min_order"] <= 8
                    or not isinstance(policy.get("min_support"), int) or isinstance(policy["min_support"], bool)
                    or policy["min_support"] < 0 or not isinstance(policy.get("id"), str)
                    or not policy["id"] or not math.isfinite(policy.get("alpha", math.nan))
                    or not 0 <= policy["alpha"] <= 1):
                raise ValueError("each policy requires id, valid min_order/support and alpha in [0,1]")
            identifiers.append(policy["id"])
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("policy IDs must be distinct")
        prior = ([neural_prior] + [(1 - neural_prior) / len(self.policies)] * len(self.policies)
                 if self.policies else [1.])
        self.initial_prior = tuple(prior)
        self.log_prior = tuple(math.log(value) for value in prior)
        self.cumulative_log_likelihood = [0.] * len(prior)
        self.targets_seen = 0
        self.cumulative_nll = 0.
        self._pending = None

    @property
    def posterior(self):
        joint = [prior + value for prior, value in zip(self.log_prior, self.cumulative_log_likelihood)]
        evidence = _logsumexp(joint)
        return tuple(math.exp(value - evidence) for value in joint)

    def predict_weight(self, feature):
        if self._pending is not None:
            raise RuntimeError("observe the previous target before predicting again")
        for name in ("longest_order", "support", "distinct"):
            if not isinstance(feature.get(name), int) or isinstance(feature[name], bool):
                raise ValueError("repetition features must be integer prefix statistics")
        if (not -1 <= feature["longest_order"] <= 8 or feature["support"] < 0
                or not 0 <= feature["distinct"] <= feature["support"]):
            raise ValueError("invalid repetition feature")
        alphas = (0., *(policy["alpha"] if gate_enabled(policy, feature) else 0. for policy in self.policies))
        weight = math.fsum(alpha * mass for alpha, mass in zip(alphas, self.posterior))
        self._pending = alphas
        return weight

    def observe(self, neural_target_probability, count_target_probability):
        if self._pending is None:
            raise RuntimeError("predict before observing a target")
        values = (neural_target_probability, count_target_probability)
        if any(not math.isfinite(value) or not 0 <= value <= 1 for value in values):
            raise ValueError("target probabilities must be finite and in [0,1]")
        neural, counts = (math.log(value) if value else -math.inf for value in values)
        likelihoods = [_log_mixture(neural, counts, alpha) for alpha in self._pending]
        updated = [old + new for old, new in zip(self.cumulative_log_likelihood, likelihoods)]
        evidence = _logsumexp([prior + value for prior, value in zip(self.log_prior, updated)])
        if not math.isfinite(evidence):
            raise ValueError("at least one live expert must assign positive target probability")
        cumulative = -evidence
        loss = cumulative - self.cumulative_nll
        self.cumulative_nll = cumulative
        self.cumulative_log_likelihood = updated
        self.targets_seen += 1
        self._pending = None
        return loss

    def guarantee(self):
        if self._pending is not None:
            raise RuntimeError("finish the outstanding prediction before auditing")
        adjusted = [-value - prior for value, prior in zip(self.cumulative_log_likelihood, self.log_prior)]
        neural_loss = -self.cumulative_log_likelihood[0]
        ceiling = -self.log_prior[0]
        return {"targets": self.targets_seen, "online_cumulative_nll": self.cumulative_nll,
                "component_cumulative_nll": [-value for value in self.cumulative_log_likelihood],
                "initial_prior": list(self.initial_prior), "final_posterior": list(self.posterior),
                "best_prior_adjusted_cumulative_nll": min(adjusted),
                "bound_slack_nats": min(adjusted) - self.cumulative_nll,
                "neural_cumulative_nll": neural_loss, "neural_extra_loss_ceiling_nats": ceiling,
                "neural_protection_slack_nats": neural_loss + ceiling - self.cumulative_nll,
                "bound": "L <= min_k(L_k - log(prior_k)) <= L_neural - log(prior_neural)"}
