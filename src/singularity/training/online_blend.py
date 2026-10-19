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


class VectorizedBlendState:
    """Chunked NumPy form of the same causal posterior.

    With grid log-likelihoods l_{s,k}=log p_{s,k}(y_s), the posterior used at
    row t is proportional to prior_k*exp(S_{t,k}), where S_{t,k} is the
    *exclusive* prefix sum over s<t. Prepending the carried S to each chunk
    and accumulating sequentially gives the same float additions in the same
    order for every chunking, so chunked, resumed and whole-stream scoring
    agree exactly. Row t never reads target t when forming its weights.
    """

    def __init__(self, count_weights=DEFAULT_COUNT_WEIGHTS):
        import numpy as np

        check = BayesianByteBlend(count_weights)
        self.count_weights = np.asarray(check.count_weights, dtype=np.float64)
        self.log_prior = np.full(len(self.count_weights), -math.log(len(self.count_weights)))
        self.cumulative_log_likelihood = np.zeros(len(self.count_weights), dtype=np.float64)
        self.targets_seen = 0
        self.online_cumulative_nll = 0.

    def _grid_log_likelihoods(self, neural_target, count_target):
        import numpy as np

        alpha = self.count_weights[None, :]
        probabilities = (1-alpha)*neural_target[:, None] + alpha*count_target[:, None]
        # Endpoint experts retain their own probability exactly, as in the loop.
        probabilities[:, self.count_weights == 0] = neural_target[:, None]
        probabilities[:, self.count_weights == 1] = count_target[:, None]
        with np.errstate(divide="ignore"):
            return np.log(probabilities)

    def score_chunk(self, neural, counts, targets, validate=True):
        import numpy as np

        neural, counts = np.asarray(neural, dtype=np.float64), np.asarray(counts, dtype=np.float64)
        targets = np.asarray(targets)
        if (neural.ndim != 2 or neural.shape != counts.shape or targets.ndim != 1 or len(targets) != len(neural)
                or not np.issubdtype(targets.dtype, np.integer) or neural.shape[1] < 1
                or np.any(targets < 0) or np.any(targets >= neural.shape[1])):
            raise ValueError("expected aligned two-dimensional expert probabilities and integer targets")
        if validate:
            for values in (neural, counts):
                # min() propagates NaN; an infinite entry makes its row sum fail.
                if not values.min() >= 0 or not np.all(np.abs(values.sum(1) - 1.) <= 1e-6):
                    raise ValueError("expert probabilities must be normalized and nonnegative")
        rows = np.arange(len(targets))
        grid = self._grid_log_likelihoods(neural[rows, targets], counts[rows, targets])
        prefix = np.add.accumulate(np.vstack((self.cumulative_log_likelihood[None, :], grid)), axis=0)
        before = self.log_prior[None, :] + prefix[:-1]
        with np.errstate(invalid="ignore"):
            top = before.max(1, keepdims=True)
            log_weights = before - (top + np.log(np.exp(before-top).sum(1, keepdims=True)))
            joint = log_weights + grid
            joint_top = joint.max(1, keepdims=True)
            log_predictive = joint_top[:, 0] + np.log(np.exp(joint-joint_top).sum(1))
        if not np.isfinite(log_predictive).all():
            raise ValueError("at least one fixed-grid expert must assign positive target probability")
        alpha = (np.exp(log_weights) * self.count_weights).sum(1)
        # (1-a)*n + a*c = n + a*(c-n), formed in one buffer to avoid temporaries.
        mixture = np.subtract(counts, neural)
        np.multiply(mixture, alpha[:, None], out=mixture)
        np.add(mixture, neural, out=mixture)
        predicted = mixture.argmax(1)
        losses = -log_predictive
        self.cumulative_log_likelihood = prefix[-1].copy()
        self.targets_seen += len(targets)
        self.online_cumulative_nll += math.fsum(losses)
        return {"target_nll_nats": losses, "target_correct": predicted == targets,
                "prior_to_target_count_weights": alpha}

    def guarantee(self):
        import numpy as np

        grid_nll = -self.cumulative_log_likelihood
        best = float(grid_nll.min())
        log_k = math.log(len(self.count_weights))
        evidence = -_logsumexp([float(-loss-log_k) for loss in grid_nll])
        return {"targets": self.targets_seen, "grid_size": len(self.count_weights),
                "online_cumulative_nll": self.online_cumulative_nll, "best_fixed_grid_cumulative_nll": best,
                "best_fixed_grid_count_weight": float(self.count_weights[int(np.argmin(grid_nll))]),
                "log_grid_size_nats": log_k, "regret_nats": self.online_cumulative_nll-best,
                "bound_slack_nats": best+log_k-self.online_cumulative_nll,
                "marginal_likelihood_cumulative_nll": evidence,
                "marginal_likelihood_identity_error_nats": self.online_cumulative_nll-evidence}

    def to_dict(self):
        """Exact resumable state: floats are stored as IEEE hexadecimal."""
        return {"schema": "singularity.online-blend-state/1",
                "count_weights": [float(w).hex() for w in self.count_weights],
                "cumulative_log_likelihood": [float(v).hex() for v in self.cumulative_log_likelihood],
                "targets_seen": self.targets_seen, "online_cumulative_nll": self.online_cumulative_nll.hex()}

    @classmethod
    def from_dict(cls, payload):
        import numpy as np

        if payload.get("schema") != "singularity.online-blend-state/1":
            raise ValueError("unsupported online blend state")
        state = cls([float.fromhex(w) for w in payload["count_weights"]])
        values = np.array([float.fromhex(v) for v in payload["cumulative_log_likelihood"]], dtype=np.float64)
        if values.shape != state.count_weights.shape or np.isnan(values).any() or np.any(values > 0):
            raise ValueError("cumulative log-likelihoods must be nonpositive, one per grid weight")
        targets = payload["targets_seen"]
        if not isinstance(targets, int) or isinstance(targets, bool) or targets < 0:
            raise ValueError("targets_seen must be a nonnegative integer")
        state.cumulative_log_likelihood, state.targets_seen = values, targets
        state.online_cumulative_nll = float.fromhex(payload["online_cumulative_nll"])
        return state


def score_online_probabilities_fast(neural, counts, targets, count_weights=DEFAULT_COUNT_WEIGHTS,
                                    chunk_size=4096):
    """Vectorized replacement for ``score_online_probabilities``.

    Returns the same fields. Per-target results do not depend on
    ``chunk_size`` (None scores one chunk); the reference loop agrees to
    floating-point rounding (tests check 1e-9). The default bounds memory
    at chunk_size*(2*vocabulary+3*grid) doubles beyond the inputs.
    """
    import numpy as np

    state = VectorizedBlendState(count_weights)
    length = len(targets)
    if chunk_size is None:
        chunk_size = max(length, 1)
    if isinstance(chunk_size, bool) or not isinstance(chunk_size, int) or chunk_size < 1:
        raise ValueError("chunk_size must be a positive integer")
    if length < 1:
        raise ValueError("expected aligned two-dimensional expert probabilities and integer targets")
    parts = [state.score_chunk(neural[start:start+chunk_size], counts[start:start+chunk_size],
                               targets[start:start+chunk_size]) for start in range(0, length, chunk_size)]
    result = {key: np.concatenate([part[key] for part in parts]) for key in parts[0]}
    result["audit"] = state.guarantee()
    return result
