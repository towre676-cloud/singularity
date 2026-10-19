# NX18: exact recovery conditioning, physical noise, and coefficient bits

Exact injectivity and usable recovery accuracy are different properties. This module exposes a particular exact left inverse, propagates declared physical reading errors, verifies target-specific primal/dual optimization certificates, and compares real graph experiments at a common target. All statements use exact integer or rational arithmetic. Floating-point conditioning estimates are not substituted for proved bounds.

## Sharp box-noise propagation

Let \(y=Av\), and let \(R\) be a left inverse, \(RA=I\). For raw reading error \(|\eta_i|\le\epsilon_i\),

\[
 \widehat v-v=R\eta,\qquad
 |\widehat v-v|\le |R|\epsilon.
\]

For a scalar target \(g^Tv\), the sharp independent-box error is

\[
 \sup_{|\eta_i|\le\epsilon_i}|g^TR\eta|
 =\sum_i|(g^TR)_i|\epsilon_i.
\]

The upper bound follows from the triangle inequality. Equality is attained by choosing each independent error at its signed endpoint, \(\eta_i=\epsilon_i\operatorname{sgn}(g^TR)_i\). A different sign pattern may be required for a different target; simultaneous attainment of every coordinate bound is not promised.

For

\[
 A=\begin{pmatrix}1&1\\1&17/16\end{pmatrix},\qquad
 R=\begin{pmatrix}17&-16\\-16&16\end{pmatrix},
\]

the coordinate errors under unit box noise are exactly 33 and 32. The tests enumerate all four box vertices independently and attain both bounds. These are exact worst-case errors, not floating-point upper estimates.

If measurements are preprocessed by \(P\), the correct raw reconstruction is \(RP\), and the bound is \(|RP|\epsilon\). Applying \(|R|\) to an unchanged raw noise vector would silently omit amplification by preprocessing. Correlation can reduce the true worst case, but a correlated uncertainty set must be supplied explicitly; it is not inferred from similar-looking rows.

## Physical sensor or mere rescaling?

Consider measurements of one coordinate with rows 1 and 100. If both are distinct physical sensors with error bound one, the second can reconstruct the coordinate with error \(1/100\). If the second reading is only 100 times the first reading, its error bound is 100 and the reconstruction error remains one. Exact row-span pruning preserves distinguishability, but it cannot preserve this physical distinction when noise contracts differ.

The receipt records both examples. Costs and noise bounds are supplied per reading. The real graph comparison below charges each coefficient reading explicitly; no hidden setup-sharing optimization is assumed. A basis change in unknown coordinates similarly changes the forward map and target representation. It cannot improve a physical signal-to-noise guarantee merely by multiplying its coordinates.

## Certified target-specific left inverses

For a scalar target, choose weights \(w\) solving \(A^Tw=g\). The best independent-box error is the linear program

\[
 \min_w\sum_i\epsilon_i|w_i|\quad\text{subject to }A^Tw=g.
\]

Its dual is

\[
 \max_z g^Tz\quad\text{subject to }|(Az)_i|\le\epsilon_i.
\]

A rational certificate consists of a primal feasible \(w\), a dual feasible \(z\), and equality of the two displayed objective values. Weak duality proves optimality without trusting the active-set search. The verifier checks precisely these rational equalities and inequalities. It does not invoke the optimizer. The constructor enumerates small basic supports and dual vertices under a declared active-set limit; a refusal is not an infeasibility theorem.

**Proposition NX18.1.** If the supplied primal and dual witnesses replay, their common value is the least possible box-noise amplification among all linear unbiased estimators of the declared target from those readings.

**Proof.** Every feasible estimator has expected noiseless output \(g^Tv\), since \(A^Tw=g\). For every primal/dual feasible pair,

\[
 g^Tz=w^TAz\le\sum_i|w_i|\epsilon_i.
\]

Equality of a particular pair reaches this universal lower bound. The box-error identity above identifies its operational worst-case error. □

The bounded design selector solves this problem separately for every member of a finite supplied menu. It then chooses the least declared total cost among members meeting the requested error. The retained example has a cost-one reading with error one, a cost-three reading with error \(1/100\), and a cost-seven reading with error \(1/200\). For tolerance \(1/50\), the cost-three design is the exact optimum in that menu. This is not a theorem about unlisted experiments, shared panels, nonlinear estimators, or arbitrary correlated errors.

## A real graph comparison at the same target

The common target is \((A_{H,0},\ldots,A_{H,3})\) for the dominating block over \(H=K_2\), at \(q=1/2\). The edge-free and weighted probe matrices are first compiled on the **entire generic symmetric interface** through volume three. Their inverse wrappers therefore do not assume a dominating-interior prior while constructing the interface recovery map. Target rows are selected afterward at orbit \((0,0)\), whose coefficients are exactly the displayed \(A_H\).

Eighteen actual simple glued graphs are independently counted by weak compositions and direct energy evaluation. Their outputs match the closure operators. The old exact finite-difference and weighted restoration APIs recover the same target on these consistent exact outputs. The new wrappers declare a particular linear extension to inconsistent noisy readings. The old APIs correctly reject inconsistent overdetermined data, so they are not quietly assigned an unstated numerical noise policy.

| Route | Raw coefficient readings | Volume budget | Declared total reading cost | Sharp target-coordinate-3 amplification under unit independent noise |
|---|---:|---:|---:|---:|
| Edge-free finite-difference probe family | 24 | 3 | 144 | \(343326323/6082944\) |
| Weighted terminal-edge restoration, weights 0 and 1 | 48 | 3 | 312 | \(82769649/8012480\) |
| Ordered charge chart | 4 | 3 | 4 | 1 |

This is a finite comparison under the supplied cost and sensor contracts. It does not imply that every charge chart is less noisy, that weighted recovery is always better, or that the displayed left inverses minimize full-state noise. In this particular dominating family the charge chart uses terminal state \((0,0)\), so its forward matrix is the identity. Its advantage follows from the available physical reading, not from arbitrary rescaling.

Volume three precedes the first collision circle. The receipt separately records the two-node \(R=7\) collision moments at \((0,5),(3,4)\): finite-difference nodes \(\tau_o\) and weighted-edge nodes \(q^{(s-t)^2}\). Those inverse metrics concern isolated conditional moments; they are not advertised as raw whole-graph noise bounds. The full delayed wrapper explicitly refuses budgets with delay until nuisance-coordinate elimination is supplied. This prevents the common mistake of assuming all higher-volume unknown coefficients vanish merely because the target is truncated lower.

## Uniform bounds and bit costs

For nodes \(z_i\), \(V_{ri}=z_i^r\). The coefficients of the Lagrange polynomial

\[
 \ell_i(X)=\prod_{j\ne i}\frac{X-z_j}{z_i-z_j}
\]

form row \(i\) of \(V^{-1}\). If a declared compact parameter domain satisfies \(|z_i|\le M\) and \(|z_i-z_j|\ge\gamma>0\), its coefficient one-norm is at most

\[
 \|\ell_i\|_1\le\frac{(1+M)^{m-1}}{\gamma^{m-1}}.
\]

For equal reading error \(\epsilon\), this gives coordinate error at most \(\epsilon((1+M)/\gamma)^{m-1}\). The permanent interval example has nodes 1 and \(1+q\), with \(q\in[1/4,1/2]\). Exact inequalities give \(M=3/2\), \(\gamma=1/4\), hence the uniform bound 10. The proof is the displayed product inequality, not a parameter grid. Endpoints zero and one are not included by extrapolation.

A finite difference of order \(j\) has coefficient one-norm \(2^j\). This quantifies preprocessing amplification before any Vandermonde inverse. Its sufficient observation delay does not bound its necessary precision. The receipt separately records matrix and inverse numerator bits, denominator bits, signs, nonzeros and total encoding bits. Its encoding uses one sign bit, at least one numerator bit, and denominator bit length per cell. These reproducible bit counts are not Python memory usage or an asymptotic speedup theorem.

Implementation and tests are `recovery_metrics.py` and `tests/test_recovery_metrics.py`. Run `python scripts/recovery_metrics.py --check`. The accepted scope includes exact propagation, the bounded real-block comparison, one certified target design, and one genuinely uniform compact-interval bound. Sharp all-budget delayed precision, optimal delay, and general correlated uncertainty remain open.
