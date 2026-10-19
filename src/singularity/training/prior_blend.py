"""Causal Bayesian blending with a declared nonuniform prior.

For fixed-grid mixture k, let L_k be its realized cumulative log loss and
pi_k > 0 its initial prior mass. The Bayesian predictor has joint likelihood
sum_k pi_k exp(-L_k), hence

    L_online <= min_k (L_k - log(pi_k)).

In particular a 0.95 prior mass on the pure-neural endpoint limits total
excess loss over that endpoint to -log(0.95), about 0.051293 nats per reset.
This standard mixture guarantee is algebraic, not a fitted performance claim.
"""
from __future__ import annotations

import math

from .online_blend import BayesianByteBlend, DEFAULT_COUNT_WEIGHTS, _logsumexp


class PriorBayesianBlend(BayesianByteBlend):
    """The same predict-then-observe API with strictly positive prior masses.

    With no supplied prior, put 95% mass on count weight zero (pure neural)
    and spread the remaining 5% equally over the other declared grid weights.
    A one-element pure-neural grid receives mass one. A custom grid without
    a pure-neural endpoint requires an explicit normalized positive prior.
    Priors are declarations; neither this class nor its guarantee fits them.
    """

    def __init__(self, count_weights=DEFAULT_COUNT_WEIGHTS, prior=None):
        super().__init__(count_weights)
        size = len(self.count_weights)
        if prior is None:
            if 0. not in self.count_weights:
                raise ValueError("default neural-protected prior requires count weight zero")
            neural = self.count_weights.index(0.)
            prior = [1.] if size == 1 else [(.95 if k == neural else .05 / (size - 1)) for k in range(size)]
        values = tuple(float(value) for value in prior)
        if (len(values) != size or any(not math.isfinite(value) or value <= 0 for value in values)
                or abs(math.fsum(values) - 1.) > 1e-12):
            raise ValueError("prior must contain one finite positive mass per grid weight and sum to one")
        # Remove only floating-point normalization drift, recording the actual
        # normalized masses to which the certificate applies.
        total = math.fsum(values)
        self.initial_prior = tuple(value / total for value in values)
        self.log_prior = tuple(math.log(value) for value in self.initial_prior)
        self.log_posterior = list(self.log_prior)

    def guarantee(self):
        """Audit the correct nonuniform-prior bound and marginal likelihood."""
        if self._pending is not None:
            raise RuntimeError("finish the outstanding observation before auditing")
        online = math.fsum(self._online_losses)
        losses = self.grid_cumulative_nll
        adjusted = [loss - prior for loss, prior in zip(losses, self.log_prior)]
        best_raw_index = min(range(len(losses)), key=losses.__getitem__)
        best_adjusted_index = min(range(len(adjusted)), key=adjusted.__getitem__)
        evidence = -_logsumexp([prior - loss for prior, loss in zip(self.log_prior, losses)])
        result = {
            "targets": len(self._online_losses), "grid_size": len(losses),
            "initial_prior": list(self.initial_prior),
            "online_cumulative_nll": online,
            "fixed_grid_cumulative_nll": list(losses),
            "prior_adjusted_grid_cumulative_nll": adjusted,
            "best_fixed_grid_cumulative_nll": losses[best_raw_index],
            "best_fixed_grid_count_weight": self.count_weights[best_raw_index],
            "best_prior_adjusted_cumulative_nll": adjusted[best_adjusted_index],
            "best_prior_adjusted_count_weight": self.count_weights[best_adjusted_index],
            "regret_nats": online - losses[best_raw_index],
            "bound_slack_nats": adjusted[best_adjusted_index] - online,
            "marginal_likelihood_cumulative_nll": evidence,
            "marginal_likelihood_identity_error_nats": online - evidence,
            "final_posterior": list(self.posterior),
            "final_posterior_count_weight": self.posterior_count_weight,
            "bound": "L_online <= min_k(L_k - log(initial_prior_k))",
        }
        if 0. in self.count_weights:
            neural = self.count_weights.index(0.)
            ceiling = -self.log_prior[neural]
            result.update({"pure_neural_prior_mass": self.initial_prior[neural],
                           "pure_neural_cumulative_nll": losses[neural],
                           "pure_neural_extra_loss_ceiling_nats": ceiling,
                           "pure_neural_protection_slack_nats": losses[neural] + ceiling - online})
        return result
