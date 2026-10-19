# NX28 — Conserved totals can conceal a species target

The exact module reactive_transport.py implements a conservative two-cell, two-species toy, finite hypothesis-set design, and a separately sourced daily-ozone proxy pilot. The measured proxy cannot identify atmospheric reaction rates or a uniform physical model-error bound.

## Exact conservative toy

Use
\[
D=\begin{pmatrix}7/8&1/8\\1/8&7/8\end{pmatrix},\quad
M=\begin{pmatrix}(3/4)D&0\\(1/4)D&D\end{pmatrix},\quad
H=\begin{pmatrix}1&0&1&0\\0&1&0&1\end{pmatrix}.
\]
State order is \((A_1,A_2,B_1,B_2)\). The source-derived model is a declared conversion \(A\to B\) followed by mixing; it is not an asserted atmospheric mechanism. The exact identity \(HM=DH\) proves that cellwise total concentrations evolve autonomously. All columns of \(M\) are nonnegative and sum to one, so every nonnegative initial state stays nonnegative and unweighted total mass is preserved.

The states \((1,0,0,0)\) and \((0,0,1,0)\) have the same total observations at every time, yet their total-\(B\) target gap at horizon \(T\) is \((3/4)^T\). Observing totals more often cannot recover the missing species fraction. A species-selective total-\(A\) sensor repairs this target; exact factorization and an invisible original-state direction are retained. Waiting shrinks the target gap here but does not create structural information.

The independent oracle performs reaction and cell fluxes separately, without assembling \(M\). Tests compare every simplex vertex, verify \(HM=DH\), preserve all mass balances, and check horizons zero through eight.

Conservation depends on units and stoichiometry. For the one-cell step
\[
\begin{pmatrix}3/4&0\\1/2&1\end{pmatrix},
\]
one \(A\) produces two \(B\). The unweighted species count is not conserved, but mass row \((2,1)\) is. This prevents molar counts and physical masses from being interchanged.

## Robust finite sensor design

Each experiment declares attainable readings for every finite hypothesis, a fixed deterministic noise radius and cost. The solver enumerates at most twelve experiments and minimizes cost under coordinate interval separation. Its negative status is infeasible_interval_separation: overlapping interval hulls alone do not prove equality of joint correlated reading sets.

The retained uncertain-rate example is stronger than a hull artefact. An \(A\)-initial hypothesis can yield species value \(1/2\), while the \(B\)-initial hypothesis yields one. With radius \(1/4\), both can actually report \(3/4\). Nominal rate \(1/4\) would instead give a larger gap and suggest successful separation. The explicit common reading shows why a nominal row rank is insufficient after reaction uncertainty. A smaller radius repairs the finite hypotheses. An independent subset oracle compares all panels for a three-label catalogue.

## A measured atmospheric proxy, with narrow interpretation

Anonymous EPA AQS bulk downloads timed out. Before fitting any chemical measurements, the fallback was frozen to the R maintainer-distributed airquality benchmark. Source:
https://github.com/r-devel/r-svn/blob/main/src/library/datasets/data/airquality.tab
with immutable Git blob d39db693a2c5dd470ed48aa7c86b6a360527b164.
The primary maintainer description is
https://www.stat.ethz.ch/R-manual/R-devel/RHOME/library/datasets/html/airquality.html.
The separately retained R COPYING file governs the distributed fixture; code and data provenance are not conflated.

The target is mean ozone in ppb at Roosevelt Island, 1300–1500 hours, for the next daily window. The original ozone source is the New York State Department of Conservation. The dataset contains 153 days, 116 observed ozone days and 37 missing values. It does not preserve instrument identity, detection limit or UTC offset. Other meteorological variables have different sites and windows and are not treated as simultaneous species readings.

The declared reduced open-box mechanism is loss to an unobserved sink plus constant external source,
\[
c_{t+1}=\rho c_t+b,\qquad 0\le\rho\le1,\quad b\ge0.
\]
This map preserves nonnegative concentrations; the observed species alone is not conserved. Training-only exact least squares searches \(\rho\in\{0,1/100,\ldots,1\}\) and computes the optimal nonnegative \(b\) for each value. No latent sink concentration is scored as measured truth.

| Frozen comparison | Result |
|---|---|
| Training dates | May–July 1973; both source and target remain in training |
| Evaluation dates | August–September 1973 |
| Consecutive complete train/evaluation pairs | 48 / 49 |
| Fitted empirical retention | \(47/100\) |
| Reduced-model held-out MAE | \(507611/23520\approx21.5821\) ppb |
| Persistence held-out MAE | \(1133/49\approx23.1224\) ppb |

This is an anonymous atmospheric reactive-transport proxy with measured target truth and a deliberately reduced one-box map. The fitted retention is not an identified chemical reaction constant. Unknown forcing, seasonal effects and missing observations can dominate discrepancy. A near-optimal training-rate population is an explicitly heuristic loss-tolerance set, not a confidence interval. Its held-out coverage is reported rather than promised.

The public standard-library checker completely re-fits the exact benchmark and recomputes scores. It separately replays the conservative transport toy. Agreement with measurements and algebraic correctness remain different claims.
