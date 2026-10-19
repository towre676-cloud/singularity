# NX33: moving observable quotients

For \(x'=A(t)x\), a constant-rank row matrix \(B(t)\) defines \(z=Bx\). Exact
closure exists precisely when

\[
B'+BA=TB.
\]

Necessity follows by differentiating every possible source solution. Sufficiency
is direct substitution. The kernel criterion is equivalent: a row factors
through a surjective linear map \(B\) if and only if it annihilates its kernel.
On a constant-rank chart, solving a nonvanishing pivot minor constructs regular
coefficients for \(T\). Surjectivity also makes \(T\) unique. The implementation
checks this identity over \(\mathbb Q(t)\), retaining all denominator and pivot
exclusions. A sampled identity is never accepted as a neighbourhood proof.

Target preservation is separate: a requested row \(c\) must factor as \(c=LB\).
A dynamically closed quotient can still discard the requested target. Such an
input is rejected. Zero and full-rank quotients are supported explicitly.

For \(B=(1,t)\), \(A=\left(\begin{smallmatrix}0&-1\\0&0\end{smallmatrix}\right)\),
the derivative term cancels \(BA\), and \(z'=0\). The explicit solution
\(x_1=a-bt,x_2=b\) verifies \(z=a\). With \(A=\operatorname{diag}(0,1)\), closure
fails: \((-t,1)^T\) is hidden but is exposed at rate \(1+t\). A rational sample
with nonzero exposure is a failure witness; vanishing at the isolated point
\(t=-1\) does not restore closure on a chart.

For a reduced gauge \(\widetilde z=Gz\), differentiation gives

\[
\widetilde B=GB,\quad
\widetilde T=G'G^{-1}+GTG^{-1},\quad
\widetilde L=LG^{-1}.
\]

All three identities are checked exactly on overlaps. The gauge \(G=1+t\)
turns the constant scalar example into \(\widetilde T=1/(1+t)\). Conjugation alone
would give the wrong answer. A path crossing the gauge zero is refused even
when the source system itself is regular there. Two subdivided ordinary paths
give compatible target enclosures, checked against explicit solutions.

The integrated period example uses the source-grounded Legendre connection
from NX31 and the full-rank moving frame \(B=\operatorname{diag}(1,t)\). Its
reduced connection and target row are computed exactly; both a direct segment
and a two-segment path contain the independent normalized hypergeometric period
enclosure. The source excludes \(t=0,1\); the gauge also records its zero at
zero. A separate diagonal family \(x'=\operatorname{diag}(0,1)x\), target
\((\lambda,1)x\), has observable rank one at the constant external parameter
\(\lambda=0\) and rank two for \(\lambda\ne0\). The determinant \(\lambda\)
proves these strata; the retained samples are checks, not the proof of the
stratification. This is a one-parameter differential adapter with an explicit
constant external specialization, not a multidimensional flat-connection engine.

All constructions and independent target predictions are retained in
`results/nx36/nx33_acceptance.json`. A local gauge identity makes no assertion
about loop holonomy; actual loop evidence belongs to NX32.
