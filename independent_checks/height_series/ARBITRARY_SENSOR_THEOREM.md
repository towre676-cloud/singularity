# Exact global sensor-optimality theorem

The previous volume-eight reader theorems optimized only distinct unscaled
single-\(q\)-coefficient observations. We now broaden the sensor class to
**every rational linear functional of the available coefficients**, under a
specified adversarial error-cost normalization.

Let \(r_e\in\mathbf Q^d\) be the response vector for coefficient degree \(e\).
A sensor \(s=\sum_e a_e\,\mathrm{coeff}_e\) has cost
\(\sum_e|a_e|\). Normalize to cost at most one. Its response vector lies in

\[
C=\operatorname{conv}\{\pm r_e\}.
\]

For an invertible \(d\)-sensor matrix \(M\), every row of \(M\) lies in \(C\).
For each coordinate \(i\), write

\[
e_i=\sum_j(M^{-1})_{ij}M_{j,*}.
\]

The gauge of \(e_i\) in \(C\) is therefore bounded above by
\(\sum_j|(M^{-1})_{ij}|\). Hence

\[
\|M^{-1}\|_\infty\ge\gamma_C(e_i).
\]

The polar dual gives

\[
\gamma_C(e_i)=
\max\{y_i:|r_e\cdot y|\le1\text{ for every }e\}.
\]

The script constructs a rational dual feasible vector from the sign pattern of
the critical inverse row of the previously optimal coefficient panel. It
checks **every** degree in the polynomial support exactly and obtains:

| Graph class | Global optimum under the stated sensor model | Attaining panel |
| --- | --- | --- |
| General cubic graphs | \(93093/14165\) | \(4,8,12,14,18,24,26\) |
| Connected cubic graphs | \(44191/19786\) | \(6,10,14,18,24,26\) |

Thus arbitrary rational mixing of coefficients **cannot improve** either
reader's worst-case error gain when the sensor's error radius scales with its
\(\ell_1\) coefficient cost. This is a genuine extension of the previous
optimality theorem to a continuum of rational sensor choices.

The result is **not** an assertion for independent per-sensor fixed errors
regardless of mixing cost, nor for correlated or stochastic noise. Without a
normalization, scaling a sensor by an arbitrarily large rational number makes
the apparent inverse gain arbitrarily small, so no meaningful optimum exists.
