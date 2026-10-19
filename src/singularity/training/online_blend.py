"""Causal Bayesian aggregation over a fixed grid of two-expert mixtures.

This is the standard Bayesian/exponential-weights log-loss construction, not a
new optimizer. Equal prior mass on K fixed mixture weights gives cumulative
log loss at most best-fixed-grid log loss plus log(K), for any target sequence.
The current target updates the posterior only after its prediction is scored.
"""
from __future__ import annotations

import math


DEFAULT_COUNT_WEIGHTS = tuple(i / 20 for i in range(21))


def _logsumexp(values):
    maximum = max(values)
    if maximum == -math.inf:
        return -math.inf
    return maximum + math.log(math.fsum(math.exp(value - maximum) for value in values))


def _log_mixture(left, right, count_weight):
    if count_weight == 0:
        return left
    if count_weight == 1:
        return right
    return _logsumexp((left + math.log1p(-count_weight), right + math.log(count_weight)))


class BayesianByteBlend:
    """Streaming mixture with an explicit predict-then-observe contract.

    ``predict(neural_probs, count_probs)`` freezes the current prediction.
    ``observe(target)`` then receives its realized target. A second prediction
    before observation and observation without prediction are rejected. State
    is carried across windows; individual experts still determine their own
    context conventions. This class needs only the standard library.
    """

    def __init__(self, count_weights=DEFAULT_COUNT_WEIGHTS):
        self.count_weights = tuple(float(weight) for weight in count_weights)
        if (not self.count_weights or len(set(self.count_weights)) != len(self.count_weights)
                or any(not math.isfinite(weight) or not 0 <= weight <= 1 for weight in self.count_weights)):
            raise ValueError("count weights must be distinct finite values in [0,1]")
        self.log_posterior = [-math.log(len(self.count_weights))] * len(self.count_weights)
        self.grid_cumulative_nll = [0.] * len(self.count_weights)
        self._online_losses = []
        self._pending = None

    @property
    def posterior(self):
        return tuple(math.exp(value) for value in self.log_posterior)

    @property
    def posterior_count_weight(self):
        return math.fsum(weight * mass for weight, mass in zip(self.count_weights, self.posterior))

    def predict(self, neural_probabilities, count_probabilities):
        if self._pending is not None:
            raise RuntimeError("observe the previous target before predicting again")
        neural, counts = tuple(neural_probabilities), tuple(count_probabilities)
        if not neural or len(neural) != len(counts):
            raise ValueError("expert distributions must have equal nonzero vocabulary size")
        for probabilities in (neural, counts):
            if (any(not math.isfinite(value) or value < 0 for value in probabilities)
                    or abs(math.fsum(probabilities) - 1) > 1e-6):
                raise ValueError("expert probabilities must be finite, nonnegative and normalized")
        alpha = self.posterior_count_weight
        prediction = tuple((1-alpha)*left + alpha*right for left, right in zip(neural, counts))
        self._pending = (neural, counts)
        return prediction

    def observe(self, target):
        if self._pending is None:
            raise RuntimeError("predict before observing a target")
        neural, counts = self._pending
        if not isinstance(target, int) or isinstance(target, bool) or not 0 <= target < len(neural):
            raise ValueError("target must be a vocabulary index")
        result = self._observe_target_probabilities(neural[target], counts[target])
        self._pending = None
        return result

    def _observe_target_probabilities(self, neural_probability, count_probability):
        """Internal fast path after a caller has emitted/scored the prediction."""
        if neural_probability < 0 or count_probability < 0:
            raise ValueError("target probabilities must be nonnegative")
        neural_log = math.log(neural_probability) if neural_probability else -math.inf
        count_log = math.log(count_probability) if count_probability else -math.inf
        target_logs = [_log_mixture(neural_log, count_log, weight) for weight in self.count_weights]
        updated = [prior + value for prior, value in zip(self.log_posterior, target_logs)]
        log_predictive_probability = _logsumexp(updated)
        if not math.isfinite(log_predictive_probability):
            raise ValueError("at least one fixed-grid expert must assign positive target probability")
        self.log_posterior = [value - log_predictive_probability for value in updated]
        self.grid_cumulative_nll = [old - value for old, value in zip(self.grid_cumulative_nll, target_logs)]
        loss = -log_predictive_probability
        self._online_losses.append(loss)
        return loss

    def guarantee(self):
        """Retrospective audit; its best-grid value never chooses a prediction."""
        if self._pending is not None:
            raise RuntimeError("finish the outstanding observation before auditing")
        online = math.fsum(self._online_losses)
        best = min(self.grid_cumulative_nll)
        log_k = math.log(len(self.count_weights))
        evidence = -_logsumexp([-loss-log_k for loss in self.grid_cumulative_nll])
        return {"targets": len(self._online_losses), "grid_size": len(self.count_weights),
                "online_cumulative_nll": online, "best_fixed_grid_cumulative_nll": best,
                "best_fixed_grid_count_weight": self.count_weights[self.grid_cumulative_nll.index(best)],
                "log_grid_size_nats": log_k, "regret_nats": online-best,
                "bound_slack_nats": best+log_k-online,
                "marginal_likelihood_cumulative_nll": evidence,
                "marginal_likelihood_identity_error_nats": online-evidence,
                "fixed_grid_cumulative_nll": list(self.grid_cumulative_nll),
                "final_posterior": list(self.posterior),
                "final_posterior_count_weight": self.posterior_count_weight}


def score_online_probabilities(neural, counts, targets, count_weights=DEFAULT_COUNT_WEIGHTS):
    """Score already causal expert arrays in temporal order; never fit experts.

    NumPy is imported only for this optional batch scoring helper. Expert
    distributions may be computed in causal masked batches, but the posterior
    used at row t contains only targets 0..t-1. Returned mean weights are the
    *before-current-target* values, useful for independent replay audits.
    """
    import numpy as np

    neural, counts = np.asarray(neural, dtype=np.float64), np.asarray(counts, dtype=np.float64)
    targets = np.asarray(targets)
    if (neural.ndim != 2 or neural.shape != counts.shape or len(targets) != len(neural)
            or targets.ndim != 1 or not np.issubdtype(targets.dtype, np.integer)
            or len(targets) < 1 or neural.shape[1] < 1 or np.any(targets < 0) or np.any(targets >= neural.shape[1])):
        raise ValueError("expected aligned two-dimensional expert probabilities and integer targets")
    for values in (neural, counts):
        if (not np.isfinite(values).all() or np.any(values < 0)
                or not np.allclose(values.sum(1), 1., rtol=0, atol=1e-6)):
            raise ValueError("expert probabilities must be normalized and nonnegative")
    state = BayesianByteBlend(count_weights)
    losses = np.empty(len(targets), dtype=np.float64)
    weights = np.empty(len(targets), dtype=np.float64)
    correct = np.empty(len(targets), dtype=np.bool_)
    for index in range(len(targets)):
        # This prediction is fixed before the current target is indexed.
        alpha = state.posterior_count_weight
        prediction = (1-alpha)*neural[index] + alpha*counts[index]
        predicted_class = int(prediction.argmax())
        weights[index] = alpha
        target = int(targets[index])
        correct[index] = predicted_class == target
        losses[index] = state._observe_target_probabilities(neural[index, target], counts[index, target])
    return {"target_nll_nats": losses, "target_correct": correct,
            "prior_to_target_count_weights": weights, "audit": state.guarantee()}
