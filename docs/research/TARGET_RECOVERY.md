# NX08: stable target recovery

This note covers the mathematics behind `src/singularity/target_recovery.py`. The tests are in `tests/test_target_recovery.py`, and the retained receipt is `results/target_recovery.json`, which `scripts/target_recovery.py --check` replays. The setting is finite-dimensional, linear, rational and deterministic. Noise lies in a declared ellipsoid. The note makes no statistical, calibrated-physical or nonlinear-global claim.

The question is this. When sensors determine a requested target exactly in the absence of noise, how much can bounded measurement error move the recovered target? Two sensor layouts of equal rank can answer this very differently, so rank alone cannot rank designs.

## 1. Objects and conventions

- **State.** A state is a vector x in Q^d. The admissible states are x = x_c + Qz, where Q is a rational d×k matrix of full column rank and z is unrestricted. A zero-dimensional admissible set (k = 0) is allowed.
- **Observations and target.** The observations are y = Hx + η, with H an m×d matrix. The target is t = Gx, with G a p×d matrix. The known centres Hx_c and Gx_c are subtracted. Write H₀ = HQ and G₀ = GQ.
- **Noise.** η satisfies η^T R^{-1} η ≤ ε². Here R is the positive-definite ellipsoid *shape* matrix, with default I, which is the convention in `INTERCHANGE_CONTRACT.md`. Write W = R^{-1} and ‖η‖²_W = η^T W η.
- **Target error.** Target error is ‖e‖²_P = e^T P e for a positive-definite P, with default I.
- **Forms.** A = H₀^T W H₀ and B = G₀^T P G₀ are positive semidefinite (PSD) k×k matrices. For α ≥ 0, S(α) = αA − B.

**Definition.** The squared target amplification is

  κ*² = min{α ≥ 0 : S(α) ⪰ 0}, and κ*² = +∞ when no such α exists.

The set of admissible α is closed and upward-closed, so the minimum exists when the set is nonempty. When some z has H₀z ≠ 0, κ*² equals sup ‖G₀z‖²_P / ‖H₀z‖²_W over such z. When H₀ = 0 and G₀ = 0, κ*² = 0. This is the convention for "no admissible variation of the target", and it avoids a division by zero.

**Invariance.** κ* depends only on three things: the admissible *subspace* image(Q), the target metric P and the noise metric R. Replacing Q by QT for an invertible T maps z to T^{-1}z and leaves every ratio unchanged. An invertible state coordinate change x' = Tx sends H to HT^{-1}, G to GT^{-1} and Q to TQ, so H₀ and G₀ do not change. No state norm appears anywhere. Changing observation or target *units* does change R or P, and therefore κ*. This is why units and metrics are stored in every receipt. The test `test_basis_invariance_and_whitening` checks basis invariance. It also checks that R = diag(4, 9, 1) is identical to dividing the observation rows by 2 and 3.

## 2. Exact theorems

**Theorem 1 (kernel criterion).** The following are equivalent: (a) κ* < ∞; (b) ker H₀ ⊆ ker G₀; (c) G₀ = LH₀ for some p×m matrix L.

*Proof.*

- (b)⇔(c) is the row-space statement: every row of G₀ is a combination of rows of H₀ exactly when every vector annihilated by H₀ is annihilated by G₀.
- (a)⇒(b): suppose some n has H₀n = 0 and G₀n ≠ 0. Then n^T S(α) n = −‖G₀n‖²_P < 0 for every α, so no α works.
- (b)⇒(a): let Z be a basis of row(H₀), the orthogonal complement of ker H₀ = ker A. Write any z as Zw + n with n ∈ ker H₀ ⊆ ker G₀. Then z^T A z = w^T A_r w and z^T B z = w^T B_r w, where A_r = Z^T A Z is positive definite and B_r = Z^T B Z.
- S(α) ⪰ 0 exactly when α ≥ λ_max(A_r^{-1} B_r), so κ*² is finite. ∎

If the kernel condition fails, the code returns `unobservable` with an exact *hidden-target witness*: a primitive integer z with H₀z = 0 and G₀z ≠ 0. In words, the admissible states x_c and x_c + Qz produce identical noiseless readings but different targets.

**Theorem 2 (no decoder beats εκ\*).** Let D be any map from observations to target estimates, linear or not. Then sup over admissible x and ‖η‖_W ≤ ε of ‖D(Hx + η) − Gx‖_P is at least ε·κ*. If the kernel condition fails, the error is unbounded.

*Proof.*

- Take z with ‖H₀z‖_W ≤ ε.
- The state x_c + Qz with noise −H₀z and the state x_c − Qz with noise +H₀z both produce the reading Hx_c. Both noises are admissible.
- Their targets differ by 2G₀z. Whatever D outputs, it is at distance at least ‖G₀z‖_P from one of the two targets.
- Taking the supremum over z gives εκ*. If z is a hidden-target witness, scaling z makes the gap arbitrarily large while the readings stay identical. ∎

`adversarial_witness` builds exactly these two states and noises, and replays them through a supplied decoder.

**Theorem 3 (the minimum-norm decoder attains εκ\*).** Assume the kernel condition. Let Z be as above, H_Z = H₀Z and

  L* = G₀ Z (H_Z^T W H_Z)^{-1} H_Z^T W.

Then L*H₀ = G₀, and ‖L*η‖_P ≤ κ*‖η‖_W for every η. The estimate t̂ = Gx_c + L*(y − Hx_c) therefore has error at most εκ*.

*Proof.*

- **Decoder identity.** For z = Zw + n we have H₀n = 0, so L*H₀z = G₀Z(H_Z^T W H_Z)^{-1}(H_Z^T W H_Z)w = G₀Zw. This equals G₀z because G₀n = 0.
- **Gain bound.** Decompose η = H_Z w + η_⊥ with η_⊥ W-orthogonal to image(H₀). Then L*η = G₀Zw, and ‖η‖²_W = ‖H_Z w‖²_W + ‖η_⊥‖²_W ≥ ‖H₀Zw‖²_W.
- Hence ‖L*η‖_P = ‖G₀Zw‖_P ≤ κ*‖H₀Zw‖_W ≤ κ*‖η‖_W. ∎

L* is the rational form of G₀H₀^+ in the whitened geometry. It never forms a floating pseudoinverse.

**Arbitrary decoders.** Any decoder L with LH₀ = G₀ has gain at least κ*², by Theorem 2. It can be strictly worse, because it may amplify noise that lies off the observation image. `target_identifiability` also returns a *row-space decoder*, which expresses each target row in the independent rows of H₀. That decoder is valid, but it is not optimal. In the retained two-row example, its exact squared gain is in [13.090169…, 13.090170…], while κ*² is in [3.0962912…, 3.0962919…]. A decoder identity therefore never certifies a noise guarantee by itself. `certify_decoder_norm` certifies β²W − L^T P L ⪰ 0 for the chosen L. `recover_target` refuses a certificate that fails to verify.

**Single target row.** When p = 1, B_r has rank one, so κ*² = g Z A_r^{-1} Z^T g^T · P₁₁ is *rational*. Any nonzero column of A_r^{-1}B_r is an exact maximizer, and the bracketing routine always returns `exact_sharp_constant` in this case. With two or more target rows, κ*² is generally an algebraic number of degree up to min(rank H₀, p).

## 3. Exact PSD certificates with zero pivots

Strict positive-definiteness tests are the wrong tool here. These include DynaComp `stability.positive_definite` and the LDL inside `experiment_design.RationalMetric`. Invisible nuisance directions force S(α) to be singular, and S(κ*²) is always singular. `psd_certificate(S)` performs symmetric elimination in the given order.

- **Positive pivot.** It is eliminated, and the Schur complement of a PSD matrix is PSD.
- **Zero pivot.** It is accepted only if its whole remaining column is zero. Every 2×2 principal minor s_kk s_ii − s_ik² of a PSD matrix is nonnegative, so a zero diagonal entry forces a zero row. The pivot then contributes D_k = 0 and an identity column of L.
- **Negative pivot, or zero pivot with a nonzero entry s_ik.** The routine builds an exact vector v on the remaining coordinates with v^T C v < 0. For a negative pivot, v = e_k. Otherwise, v = te_k + e_i with t = −(|c_ii| + 1)/(2c_ik), which gives −(|c_ii| + 1) + c_ii < 0. The routine then lifts v through the eliminated positive-pivot block by solving S_II z_I = −S_IJ v, so that z^T S z = v^T C v < 0. The lifted vector is re-evaluated exactly before it is returned.

**Soundness.** The certificate is S = L diag(D) L^T, with L unit lower triangular and D ≥ 0. This implies PSD with no further argument. `verify_psd_certificate` and the receipt verifier check only this identity. They never rerun the elimination.

**Completeness.** It follows from the two facts above. Section 8 lists the independent oracles that check it.

## 4. Rational brackets for κ*²

`bracket_target_amplification(problem, tolerance, max_steps)` returns one of four statuses:

- `unobservable`, with a hidden witness;
- `exact_sharp_constant`, where lower = upper, with an attaining witness and a PSD certificate;
- `bracketed_sharp_constant`, where upper − lower ≤ tolerance;
- `resource_limit`, a valid bracket that is still wider than the tolerance after `max_steps` PSD tests.

It never reports infinity as a number. The routine has four parts.

1. **Initial upper bound.** It uses trace(A_r^{-1}B_r). Every eigenvalue is nonnegative, so this is at least λ_max. S(trace) is then certified, which must succeed.
2. **Lower witnesses.** It evaluates exact ratios of candidate directions: coordinate directions of row(H₀), exact columns of A_r^{-1}B_r, and a few power-iteration directions rounded to small denominators. Rounding only affects which direction is tried. The ratio is always computed exactly, and any exact ratio is a valid lower bound.
3. **Bisection.** It tests the simplest rational in the middle third of the bracket. PSD success lowers the upper bound. Failure yields z with z^T S(mid) z < 0, that is, ratio(z) > mid, which raises the lower bound to ratio(z).
4. **Snapping.** Let c be the simplest rational in the bracket. If S(c) is PSD and some null vector v of S(c) has v^T A v > 0, then v^T B v = c·v^T A v, so κ*² = c exactly. Both facts are verified exactly. This is how the τ = 3 forecast target closes at exactly 5/2.

## 5. Sensor layouts (NX08-B)

A `SensorOption` has three parts: one or more rows, a positive installation cost, and a positive-definite noise-shape block. A layout stacks the chosen options in index order and uses a block-diagonal R. The noise contract is the joint ellipsoid η^T R^{-1} η ≤ ε² over all installed rows. It is *not* an independent per-sensor box. A box is a different support-function problem that this module does not compute.

**Monotonicity lemma.** Adding a sensor adds the PSD term H_s^T R_s^{-1} H_s to A. So S(α) for a superset is at least S(α) for the subset, κ*² cannot increase, and the kernel condition is preserved.

*Consequences:*

- The decision "κ*² ≤ κ_max²" is exactly the LDL test of S(κ_max²) for one layout. No bisection is needed.
- In the pruned search, a node is pruned when its cost already exceeds the incumbent.
- A node is also pruned when the node plus *all* remaining options is infeasible. By monotonicity every completion then fails.
- A feasible node is a leaf, because every extension costs strictly more.

Ties are broken by (cost, number of sensors, sorted indices). The rank objective `cheapest_identifying_layout` and the conditioning objective `cheapest_conditioned_layout` are separate functions.

**Retained six-option catalogue.** The target is (0,1,0). Costs are normalized installation units.

| κ_max² | optimum (pruned = exhaustive = brute force) | cost | κ*² of optimum |
|---|---|---|---|
| kernel condition only | cheap_x1 + cheap_x1_weak_x2 | 2 | 5000 |
| 5000 | cheap_x1 + cheap_x1_weak_x2 | 2 | 5000 |
| 5, 12, 100 | pair_x2x3_x3 | 3 | 5 |
| 2 | pair_x2x3_x3 + cheap_x3 | 4 | 9/5 |
| 1, 3/2 | direct_x2 | 5 | 1 |
| 2/3 | direct_x2 + pair_x2x3_x3 + cheap_x3 | 9 | 9/14 |
| 1/2 | infeasible | — | — |

The cheapest *identifying* layout has rank 2, the same rank as {cheap_x1, direct_x2}. Its amplification is 5000 instead of 1. At a demanded noise radius ε, its target error guarantee is √5000·ε ≈ 70.7ε, so it is unusable at any tolerance tighter than that. The full 64-layout table and its brackets are in the receipt. Every one of the 54 identifiable layouts closes at an exact rational, because the target is a single row.

## 6. Forecast and thermal integration (NX08-C)

For a fixed, known linear transition F, the problem has three parts:

- **Observations.** Rows C_j F^t of the initial state.
- **Target.** G_τ = G F^τ.
- **Known inputs.** A known input contributes a subtracted centre.

Uncertainty in F itself is a different problem, and this module does not bound it.

**Synthetic forecast.** The state is (position m, velocity m/step, sensor bias m, decaying mode m), with F = [[1,1,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1/2]] and the sensor reading position + bias + mode.

- *Without a bias constraint.* The target is unobservable. The hidden witness (1,0,−1,0) means that position +1 with bias −1 leaves every reading unchanged.
- *With bias fixed at its calibrated centre and observations at steps 0–3.* The position forecast has exact κ*² = 1069/46, 247/23, 149/46, 17/23, 149/46, 247/23 for τ = 0,…,5. It is smallest inside the observation window and grows when extrapolating.
- *Two-row target.* The (position, velocity) target gives algebraic values bracketed to 10⁻⁶. One exception is τ = 3, where the value is exactly 5/2.
- *Adversarial replay.* At every horizon the minimum-norm decoder's error equals the lower-witness ratio times the noise. The bound is therefore tight up to the bracket width.

**Thermal plate target.** The model is the exact nominal 4×4 plate from `thermal_diagnostics.build_plate_candidates(4)`, with zero heater input. The receipt binds the model's SHA-256 digest and the generating call. All quantities are in K_model excess-temperature units, and time is in model steps.

- *Admissible initial states.* They are spanned by four modes: centre, edge ring, corners and the left–right antisymmetric mode.
- *Target.* The target is the plate-mean temperature after 4 steps.
- *Observability.* With all four sensors at step 0 alone, the target is unobservable.
- *Chosen layout.* corner_mean and center_mean read at steps 0, 1 and 2. The antisymmetric mode is in ker H₀, so it is invisible. It is a harmless nuisance, because the target is symmetric. The exact κ*² ≈ 0.69912 is rational, as for any scalar target.
- *Decoder comparison.* The row-space decoder has squared gain ≈ 5.1447 on the same data, which illustrates the unnecessary off-image amplification.
- *Thermal sensor catalogue.* Each catalogue option is one sensor read at steps 0–2, with costs 1, 1, 2 and 2. The cheapest layouts are:
  - corner_mean alone (cost 1, κ*² ≈ 156.17) for κ_max² = 200;
  - corner_mean + center_mean (cost 2) for κ_max² = 1 or 3;
  - corner_mean + center_mean + left_center_mean (cost 4) for κ_max² = 1/2.

**When the bounds are conservative.** The bound εκ* is the exact worst case over the declared ellipsoid, and the adversarial states attain it. It is conservative in three cases. First, it is conservative for a decoder other than L*. Second, it is conservative for noise that is not adversarial: a typical random draw is far smaller than the worst case. Third, the model or ellipsoid may be a conservative envelope of the physics. A bracket that is not exact adds at most its width.

**Link to NX09.** NX09 (fidelity selection) can call `bracket_target_amplification` or `cheapest_conditioned_layout` on each model fidelity's (H, G, Q) to price measurement design by target error. When it does, any fidelity discrepancy must be added as a separate bounded term in the same target units. This module does not establish calibrated physical performance. It also does not establish nonlinear global identifiability: a bounded or curved admissible set can behave differently from the unrestricted affine theorem used here.

## 7. Public API (for NX09, NX25, NX27, NX29)

| Function | Purpose |
|---|---|
| `TargetRecoveryProblem(observations, target, admissible_basis=None, observation_metric=None, units=None, *, centre, target_metric, state_dimension, admissible_dimension)` | Validated exact problem. Inputs keep their order. |
| `target_identifiability(problem)` | Returns `identifiable` with a row-space decoder L (G₀ = LH₀), or `unobservable` with a hidden witness. Also returns the rank, the pivot rows and a basis of ker H₀ (the nuisance directions). |
| `certify_target_amplification(problem, alpha2)` | `certified_upper_bound` with an LDL certificate, or `refuted` with a witness z whose ratio exceeds alpha2. |
| `bracket_target_amplification(problem, tolerance, max_steps)` | `AmplificationBracket`; see the statuses in Section 4. |
| `minimum_norm_decoder`, `certify_decoder_norm`, `bracket_decoder_norm`, `recover_target` | Optimal decoder, decoder gain certificate and certified estimate. `recover_target` gives the estimate together with the error bound β²ε². |
| `adversarial_witness(problem, z, decoder=None)` | Theorem 2 replay. |
| `target_recovery_receipt`, `verify_target_recovery_receipt` | `singularity.target-recovery/1`. Rationals are stored as `[numerator, denominator]`, and matrices carry explicit shapes. The receipt also stores the units, the R/P semantics, the problem and Q digests, the LDL factors, the witnesses and the decoders. The verifier uses only matrix products and Bareiss determinants. |
| `SensorOption`, `layout_problem`, `cheapest_identifying_layout`, `cheapest_conditioned_layout`, `conditioning_frontier`, `layout_table` | NX08-B. At most 12 options. |
| `linear_forecast_problem`, `thermal_target_problem`, `matrix_power` | NX08-C adapters. |

The admissible dimension is limited to 16 and catalogues to 12 options, as the packet requires. The receipt name `singularity.target-recovery/1` is new. It is not the P03 `relational-height/1` format or the `singularity.certificate/1` format, and the verifier rejects either schema string.

## 8. What is proved, computed and open

- **Proved here (human proofs).** Theorems 1–3, PSD certificate soundness and completeness, the monotonicity lemma and the correctness of pruning, and the rationality of κ*² for a single target row.
- **Exact finite computation.** The oracle population and every retained example are in `results/target_recovery.json`:
  - 600 tiny symmetric matrices, 539 of them PSD and 376 of those with a zero pivot, where the LDL routine and an all-principal-minors oracle agree;
  - optimum agreement among the pruned, exhaustive and brute-force catalogue searches, where the brute force uses raw rows and minors;
  - 14 targeted receipt tamperings, all rejected;
  - 10 receipts replayed.
- **Not covered.** Box or per-sensor noise and other support-function geometries; bounded or curved admissible sets; uncertain transitions F; stochastic or calibrated noise models. None of this has formal (Lean) coverage.
