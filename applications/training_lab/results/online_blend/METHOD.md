# Calibration-free causal blending with a fixed-grid log-loss guarantee

The prospective protocol was frozen at 2026-10-19 12:15:24 UTC, before accessing official WikiText-2 TEST bytes `[98304,131072)`. The three neural experts are the retained fixed AdamW seed 1000, 1001 and 1002 byte transformers, each with 84,544 parameters. Their trainable tensors remain frozen. A smoothed trigram uses the original 262,144 TRAIN bytes; its smoothing value 0.01 is inherited from the earlier separate TUNE selection. Neither smoothing nor the blend grid was selected on this new TEST suffix.

For each neural checkpoint, form the 21 fixed predictive experts

$$p_{t,k}(y)=(1-\alpha_k)p_{t,\mathrm{neural}}(y)+\alpha_k p_{t,\mathrm{count}}(y),\qquad \alpha_k=k/20,\quad k=0,\ldots,20.$$

Start with an equal prior $w_{1,k}=1/21$. At step $t$, emit

$$q_t(y)=\sum_k w_{t,k}p_{t,k}(y).$$

Only after this prediction receives its target $y_t$, update

$$w_{t+1,k}=\frac{w_{t,k}p_{t,k}(y_t)}{q_t(y_t)}.$$

The posterior used for prediction $t$ therefore contains targets strictly before $t$. Model windows reset every 64 inputs; this posterior persists across the full suffix. Neural predictions can be computed in masked causal batches. The posterior calculation still proceeds strictly in temporal order. No expert count or neural tensor is updated. This is online adaptation to past TEST targets, which differs from evaluating a wholly frozen predictor.

Let $L_k=-\sum_t\log p_{t,k}(y_t)$ and $L_{\mathrm{online}}=-\sum_t\log q_t(y_t)$. Multiplication of the Bayesian predictive probabilities telescopes to the mixture likelihood:

$$\prod_t q_t(y_t)=\frac{1}{21}\sum_k\prod_t p_{t,k}(y_t).$$

Consequently

$$L_{\mathrm{online}}=-\log\left(\frac{1}{21}\sum_k e^{-L_k}\right)\leq \min_k L_k+\log21.$$

This is the standard Bayesian expert aggregation identity and regret guarantee, not a new algorithm or a claim that online adaptation beats every fixed predictor. The comparator is the best member of this declared finite grid; there is no corresponding claim about every continuous mixture weight or changing-weight sequence. The reference minimum is computed retrospectively for audit and never drives a prediction. Positive count smoothing makes every target likelihood positive. A stable log-sum-exp update avoids underflow.

On the 32,767 scored bytes, the guarantee costs at most 3.044522438 cumulative nats, or **0.0000929143 nats per target**, relative to the best grid member. Measured regrets are 3.032207876, 3.044516986 and 3.042725414 nats for seeds 1000, 1001 and 1002. The largest absolute residual in the marginal-likelihood identity is $6.55\times10^{-10}$ nats. Six focused tests check prediction-before-observation, exact finite-sequence marginal likelihood, the regret bound, stability over a long sequence with tiny likelihoods, future-target mutation, and equivalence of the streaming and optimized scoring APIs.

Mean NLL falls from **2.088537520** for the neural experts alone to **2.028531539** for online blending, a **2.87311%** reduction. Mean top-1 accuracy rises from **40.3017%** to **40.9904%**. The TRAIN-only count expert scores 2.168074544 nats per byte and 37.7911% accuracy. All 16 contiguous block means favor online blending over neural-only prediction. The paired descriptive 95% interval for online-minus-neural NLL is [-0.06803,-0.05259] nats per target, conditional on these frozen models and this single source interval.

The earlier TUNE-selected fixed mixtures score **2.028732600** nats per byte on these same new bytes. The online mean is only 0.000201062 nats lower; its paired interval [-0.000418457,0.000043142] includes zero. This study establishes the calibration-free blend-weight guarantee and the improvement over the unblended neural experts here. It does **not** establish a predictive advantage over the already calibrated fixed mixtures.

The implementation requires one frozen neural inference pass per checkpoint. Shared CPU measurements show 0.297–0.372 seconds per neural pass, about 0.97 seconds per online posterior/prediction/scoring pass, versus about 0.042 seconds for fixed blending and scoring. Count prediction across the suffix costs 0.063 seconds and TRAIN count fitting 0.189 seconds. The complete study took 6.05 seconds including loading, source reading, comparisons, reporting and audit storage. These are workload measurements, not an inference speedup claim.

`protocol.json` retains all dependency and checkpoint hashes. `results.json` retains each seed, finite-grid losses, final posterior, timings and event ordering. `target_audit.npz` retains aligned targets, neural/count/fixed/online target losses and every prior-to-current-target posterior mean count weight, allowing an independent causal replay without further neural inference. The result is one new suffix from the same official dataset, not validation on a separate corpus.
