# NX23 — Population geometry with original multiplicities

The original objects are explicit finite labeled assignments, not the compressed feature classes. Their declared rational weights define a probabilistic model. All target probabilities, posterior risks and experiment objectives below depend on those weights; no uniform physical fault prior is inferred from a catalogue.

## Pushforward masses and exact tilts

For original objects \(\omega\), nonnegative rational weights \(w_\omega\), integer feature tuples \(f(\omega)\), and positive rational tilts \(t\), define
\[
 m_z=\sum_{f(\omega)=z}w_\omega,\qquad
 Z(t)=\sum_zm_zt^z,
\qquad
 p_t(\omega)=w_\omega t^{f(\omega)}/Z(t).
\]
Signed bounded features give Laurent monomials. Positivity of every tilt and positive total original weight ensure a nonzero denominator. A zero-weight original object retains its identity but contributes no probability. `WeightedPopulation` preserves stable original IDs and an original-object rank/unrank map; it rejects duplicate IDs, noninteger features, negative weights and zero total mass.

`pushforward_mass` sums original weights. `joint_target_mass` instead keys by both feature tuple and target, retaining ambiguity when one feature class contains multiple targets. For rational tilts, normalization, means and covariance are exact fractions:
\[
 \mu_i=Z^{-1}\sum_\omega w_\omega t^{f(\omega)}f_i(\omega),
\]
\[
 \Sigma_{ij}=Z^{-1}\sum_\omega w_\omega t^{f(\omega)}
 (f_i(\omega)-\mu_i)(f_j(\omega)-\mu_j).
\]
This is the gradient/Hessian of \(\log Z(e^u)\) without evaluating logarithms. Positive semidefiniteness follows because \(a^T\Sigma a\) is an average of squared centered values. It vanishes exactly when \(a\cdot f\) is constant on positive-weight support.

For two bits with feature their sum, the feature masses are \(1,2,1\), not three unit masses. At tilt two,
\[
 Z=9,\quad \mu=4/3,\quad\operatorname{Var}=4/9.
\]
The middle feature class contains both values of the first-bit target. Replacing original objects by one object per feature would change both the prior and the target problem.

## Observation sufficiency and Bayes decisions

A `FiniteObservationChannel` declares a finite observation alphabet and a normalized nonnegative rational likelihood row for every original ID. If two originals share a compressed key but have different likelihoods, that key does not support the proposed observation semantics. `verify_channel_compression` rejects such a compression. A target-enriched key is allowed only when it actually resolves every relevant likelihood difference.

Bayes updating is direct original-object summation. An observation with zero probability raises `UnsupportedObservation`, explicitly rejecting the declared model instead of dividing by zero. At zero-one target loss, the optimal expected error is
\[
 R(e)=1-\sum_y\max_\tau\sum_{\omega:T(\omega)=\tau}
 p_t(\omega)K_e(y\mid\omega).
\]
For each observation, choosing a target with maximal joint mass maximizes correct classification probability; summing these disjoint events proves the formula. The implementation uses exact rational arithmetic and independently checks the original-ID likelihood coverage.

Panels are declared conditionally independent given each original object. Their joint likelihood is the product of constituent likelihoods. This is an explicit assumption, not a consequence of bounded error. The exact design engine exhausts every catalogue panel within the positive rational cost budget and minimizes expected error, with cost and stable panel IDs as deterministic tie breakers. Resource guards bound channel count and joint observation outcomes.

## Bayes and worst-case objectives genuinely differ

Consider three original states with different targets and prior masses \(9/20,9/20,1/10\). One channel perfectly distinguishes the first two states but aliases the third with the first. Its Bayes error is \(1/10\). Another reports the correct target with probability \(17/20\), assigning \(3/40\) to each other label; its Bayes error is \(3/20\). At a one-experiment budget Bayes therefore selects the first channel.

For deterministic decision rules, the first channel has worst-original-state error one: whichever target is assigned to the aliased observation, the other aliased original is always wrong. The second channel has minimax error \(3/20\). Exhausting all finite decision maps proves these values. `deterministic_minimax_risk` explicitly names this decision class; it does not claim optimization over randomized rules. It ignores prior weights, unlike Bayes risk.

This distinction is not an inconsistency. The first decision knowingly accepts failure on a low-prior state. A robust target guarantee requires preventing that failure, and cannot be obtained by silently interpreting expected error as a worst-case bound.

## Integration and replay

The retained `FaultPopulation` has four named original bonds and at most two blocked bonds: eleven original masks. A synthetic weight \(2^{-\#faults}\) is declared, not estimated. Feature compression by total fault count retains original multiplicity and target ambiguity; direct bond-inspection channels retain every original mask ID. The design is synthetic inspection semantics with declared accounting costs, not an empirical thermal-sensor likelihood.

The NX19 lattice example uses output \((2,2)x=4\) inside \(0\le x_i\le2\). The three original vectors \((0,2),(1,1),(2,0)\) have one compressed sum feature and three distinct first-coordinate targets. Their feature mass is three, and their joint target table has three entries. Original-coordinate rank/unrank and mass conservation are checked without treating Smith coordinates as new objects.

`results/population_geometry.json` retains the original masks and fibre members, mass tables, exact binary moments, posterior example, finite design certificates, Bayes/minimax disagreement and scope assumptions. Run `python scripts/population_geometry.py --check`.
