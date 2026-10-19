# NX34: exact local zero bounds and a larger retained disc

This track proves a fourfold enlargement of the retained spectral-pair disc:
\(|s-1/2|\le1/25000\), compared with the earlier radius \(1/100000\). It uses the
same regularized Euler-product theorem as SNG-F35, with a graph-dependent bound
for local-factor motion. It does not assert global meromorphic continuation.
The exponent \(\delta=3/32\) is nonintegral, so the comparison uses an explicitly
cut fractional branch, not an ordinary pole of that order.

## Polynomial and analytic obligations

For an order-\(k\) graph and fixed \(0\le q\le1\),
\(a_n(q)\le\binom{n+k-1}{k-1}\). Consequently the exact rational tail on
\(|z|\le r<1\) is bounded by

\[
T_N(r)=(1-r)^{-k}-\sum_{n=0}^N\binom{n+k-1}{k-1}r^n.
\]

A polynomial lower bound larger than this tail throughout a domain proves
zero-freeness directly. A boundary Rouche comparison alone supplies a same-zero-
count conclusion and still requires a separate polynomial root count. The
implementation keeps `zero_count` and `zero_free` distinct. Its exact supported
root-count route checks a complete rational-complex factorization and counts
factors in a rational disc, rejecting roots on the boundary. A second route
subdivides a rational rectangle until Taylor lower bounds on enclosing L1 discs
strictly exceed the analytic tail. Budget exhaustion is unresolved, not a zero.

The geometric-series example has tail \(1/8\) at cutoff three and radius one
half; the roots of \(1+z+z^2+z^3\) are independently factored as \(-1,i,-i\).
A polynomial with a genuine interior zero receives count one and no zero-free
claim. The rectangle example for \(1+z^2\) needs subdivision: its initial coarse
lower bound fails, while the subdivided bounds prove nonvanishing.

## Connected graph Gaussian span improvement

Write \(B=(1-z^k)L\). A minimum-zero profile with span \(h\) has volume between
\(h\) and \((k-1)h\). Along a shortest path from its minimum to its maximum,
Cauchy–Schwarz and integrality give energy at least \(\lceil h^2/D\rceil\), where
\(D\) is graph diameter. The number of box profiles with minimum zero and maximum
\(h\) is

\[
N_k(h)=(h+1)^k-2h^k+(h-1)^k.
\]

For \(0<x<1\), positive coefficients therefore give

\[
B(x)\le1+\sum_{h\ge1}N_k(h)x^h q^{\lceil h^2/D\rceil},\qquad
B'(x)\le\sum_{h\ge1}(k-1)hN_k(h)x^{h-1}q^{\lceil h^2/D\rceil}.
\]

The second-difference integral bounds
\(N_k(h)\le k(k-1)(h+1)^{k-2}\). Beyond the retained cutoff, successive terms of
this upper majorant have ratio at most

\[
\left(\frac{h+2}{h+1}\right)^{k-2}
xq^{\lfloor(2h+1)/D\rfloor},
\]

and the derivative majorant has one additional factor \((h+1)/h\). These
ratios decrease. Once the derivative ratio is below one, exact geometric tails
bound both infinite sums. No uncomputed infinite remainder is discarded.
Differentiating \(L=B/(1-x^k)\) then gives

\[
L'(x)\le\frac{B'(x)}{1-x^k}
+\frac{kx^{k-1}B(x)}{(1-x^k)^2}.
\]

For the \(s\)-disc with center \(1/r\), radius \(\eta\), put
\(\sigma=1/r-\eta\), and let \(x\) be a rational upper bound on \(2^{-\sigma}\).
For every prime, \(\log p\,p^{-\sigma}\le1/(e\sigma)\). Integration along the
segment from the center therefore bounds each local-factor change by

\[
\eta L'(x)/(e\sigma).
\]

The center local factor is real and at least one. A strict bound below one
puts the entire local factor in the right half-plane for every prime, hence
fixes its principal logarithm. All inequalities use rational upper bounds,
including \(e>27/10\) and a bisection enclosure of \(2^{-1/r}\). The retained
spectral graphs have diameter three. At \(q=1/2\), \(r=2\), \(\eta=1/25000\),
the uniform lower bound for the local real part exceeds \(0.0873\).

The remaining SNG-F35 hypotheses are checked explicitly:
\((r+1)\sigma>1\), \(r\eta\le1/4\), and the original small-radius regularized
logarithmic tail with its prime cutoff and Schwarz constant. Thus the larger
disc inherits the same proved local branch and uniform Euler-tail conclusion.

Small-prime image records enclose \(p^{-s}\) using rational root bisection,
the positive atanh series for \(\log p\), and
\(e^a-1\le a/(1-a)\) for \(0\le a<1\). These are outward bounds, not sampled
complex plots. The saved limiting inequality is a limitation of this method,
not evidence that the actual analytic function becomes singular outside the
certificate. Replay is in `results/nx36/nx34_acceptance.json`.
