# Complete periodic observations and exact compression

Let a rational block \(c_1,\ldots,c_N\) extend periodically to positive
indices. Its reduced rational kernel is

\[
K_c(x)=\frac{c_1+c_2x+\cdots+c_Nx^{N-1}}{1-x^N},
\qquad
F_c(s)=\sum_{n\ge1}\frac{c_n}{n^s}
=\frac1{\Gamma(s)}\int_0^1(-\log x)^{s-1}K_c(x)\,dx.
\]

The last integral and series converge absolutely on \(\Re(s)>1\).
The reduced kernel, the entire future coefficient sequence, and the whole
Dirichlet function on this half-plane each determine the other two.
Matching one selected period value does not establish any of these equalities.

Kernel and sequence determine one another by uniqueness of power-series
coefficients. To prove uniqueness for the Dirichlet function, suppose the
difference of two bounded sequences first differs at index \(m\), with
coefficient \(d_m\ne0\). Multiply their Dirichlet-series difference by
\(m^s\) and let real \(s\to\infty\). If \(|d_n|\le C\), the tail for
\(s\ge2\) is bounded by

\[
C\left(\frac{m}{m+1}\right)^{s-2}
 \sum_{n>m}\left(\frac mn\right)^2\longrightarrow0.
\]

Consequently the limit equals \(d_m\), so an identically zero difference
would be impossible. For periodic blocks, equality is already decidable on
one least-common-multiple period. `separating_witness` records the first
unequal coefficient, or the full common-period comparison when they agree.
It carries an explicit work budget and does no numerical value recognition.

`PeriodObservation.generating_function()` uses the existing
`generating.RationalGF` implementation to cancel polynomial factors over
\(\mathbb Q\). `machine()` realizes the coefficient block as a cyclic shift
and reads its first coordinate, then invokes the existing
`observable_machine.minimal_machine`. Its exact intertwining identities
preserve every future output. Its finite spanning-word and nonsingular
Hankel-minor witnesses establish minimal linear dimension over \(\mathbb Q\).
At machine time \(k\ge0\) the output is \(c_{k+1}\), whereas the Dirichlet
series starts at index one. The general block budget is 4096 entries; the
existing dense machine is limited to 64 states. Coefficients have an
8192-bit rational budget. These are exact Python certificates, not Lean proofs.

For E8 reflection traces the coefficients are the integer Ramanujan sums
\(c_{30}(n)\), the reduced denominator is \(\Phi_{30}(x)\), and the minimal
observable dimension is eight. For the actual adjoint Coxeter lift, the
separate Lie-algebra calculation gives

\[
a_n=c_{30}(n)+240\,\mathbf1_{30\mid n}.
\]

Its reduced denominator is \(1-x^{30}\), so the minimal trace-output machine
has dimension 30. The underlying adjoint representation still has dimension
248. This compression neither constructs a 30-dimensional replacement Lie
algebra nor identifies the full adjoint representation with a smaller one.
The independently reduced rational kernel and observable quotient agree on
these dimensions. `receipt()` retains both certificates, including their
nonzero Hankel determinants.

The adjoint example also separates a special-value cancellation from loss of
the complete observation: \(F_a(2)=0\), yet \(a_{30}=248\). Its zero period
therefore does not make its sequence, kernel, or full Dirichlet function zero.
Tests compare late outputs through time \(10^{18}\), repeated blocks,
kernel values, coefficients from the Dirichlet engine, the E8 matrix traces,
and the exact weight-two cancellation. No floating-point calculation enters
these checks.
