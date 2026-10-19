# NX04: certified severity families and independent calibration

`thermal_parameters.py` supplies exact rational sample physics, sparse symbolic
finite-horizon observations, and a bounded complete-domain separation checker.
It completes the small NX04 scope. The parameter boxes are declared modelling
assumptions; the synthetic source does not empirically calibrate them.

## Physical coordinates and admissibility

The parameter ordering is conductance k, loss lambda, heater gain g and
specified-bond severity alpha. The only accepted severity convention is
alpha=0 nominal and alpha=1 fully blocked. For v=e_u-e_v,

\[
A_f=(1-\lambda)I-kL+k\alpha vv^T,\qquad b=g b_0.
\]

The fault bond retains conductance k(1-alpha). `ThermalParameterDomain` requires
k>=0, lambda>0, g>=0, 0<=alpha<=1 and 4k+lambda<=1 over the entire declared box.
A box crossing that last constraint must first be intersected or split; the
current implementation rejects it rather than pretending the full invalid box
is covered. The sufficient stencil condition makes every matrix entry
nonnegative. Since all conductance terms have zero row sum, every row sum is
1-lambda; partial blockage preserves this contract.

`parametric_fault_sample` constructs the exact matrix for any rational point in
the admissible domain. At alpha=0 it reproduces the nominal source matrix; at
alpha=1 it reproduces `fault_candidate` full removal. This endpoint equivalence
is exact, including heater and sensors. Rational intermediate severities are
checked through independent edge-flux evolution, not interpolation between the
two endpoint answers.

## Symbolic maps and interval enclosures

`Polynomial` stores a sparse map from nonnegative multiexponents to rational
coefficients. Addition combines equal monomials and multiplication convolves
them. `panel_parameter_map` propagates the source stencil symbolically, with
separately reset zero initial states for every requested word. Every coordinate
of a finite-horizon response is therefore represented exactly as a polynomial
in the four parameters. The default horizon is four and the coefficient budget
is 100,000 terms across an evolved state. Exceeding either is a refusal to
compile a larger problem, not a physical conclusion.

For a closed rational box, each univariate monomial factor is bounded exactly
at its endpoints, also including zero for an even power across a sign change.
Interval multiplication encloses each multivariate monomial, and summing these
intervals encloses the whole polynomial. The resulting enclosure can be wider
than the actual image because separate monomials can share variables. It is
nevertheless a valid deterministic outer bound. This distinction is retained
throughout the separation proof.

An independent two-step expansion verifies all symbolic coefficients. If the
first input is two, the second zero, the source starts at zero and b is the
unscaled heater, then

\[
x_2=2g\{(1-\lambda)b-kLb+k\alpha vv^Tb\}.
\]

For any sensor c, the response is

\[
2g\{(1-\lambda)c^Tb-k\sum_{ab\in E}(c_a-c_b)(b_a-b_b)
+k\alpha(c_u-c_v)(b_u-b_v)\}.
\]

The test derives this polynomial separately and compares the complete sparse
coefficient table with symbolic propagation, beyond merely checking samples.

## Full-domain contrast certificates

`ParametricFaultFamily` specifies a polynomial observation vector and compact
box. Left and right hypotheses have independent parameter assignments. Within
one hypothesis those same parameters persist across all separately reset
experiments. This is essential: forcing equal calibration between hypotheses
would solve an easier problem, whereas independently redrawing calibration at
each observation would throw away valid information.

For a contrast w and candidate-specific polynomial response Phi, first combine
the coordinates symbolically into w^T Phi. This can cancel nuisance dependence
before enclosure. If its left and right enclosures are [l_a,u_a] and [l_b,u_b],
and each raw reading has independent error bounded by epsilon_i in either world,
the support error in their contrast difference is

\[
2\sum_i|w_i|\epsilon_i.
\]

A positive value of

\[
\max(l_a-u_b,l_b-u_a)-2\sum_i|w_i|\epsilon_i
\]

certifies separation on that entire product cell. Failed cells are bisected at
a rational midpoint of their widest parameter coordinate. The certificate
stores a binary tree of splits; its children share the midpoint boundary and
together cover their parent without gaps. Strict margins cover those boundaries
as well. `verify_family_certificate` reconstructs every split and replays every
leaf enclosure and gap. A full separated result requires every leaf to pass.

**SNG-NX04-01.** If that checker accepts a separated certificate, the two complete
declared observation-error families are disjoint. Proof follows by induction
over the covering tree and the support inequality on each leaf. The proof does
not rely on density of samples or on eventual subdivision convergence.

An overlap certificate instead supplies two complete parameter assignments and
a common possible observation. The checker evaluates both polynomial maps and
all error inequalities directly. Such witnesses may be supplied explicitly;
the solver also tests cell midpoints. It is not a complete algebraic intersection
solver. A cell budget produces `unresolved` with every remaining cell retained.
An actual zero-gap touching case is treated as overlap when its rational witness
is available. Missing a difficult overlap witness never becomes a separation.

## Scalar calibration example

For x'=a(alpha)x+gu with a=1/2-alpha/4 and 1<=g<=2, the two-reading transcript
after pulse then wait is

\[
(y_1,y_2)=(g,(1/2-\alpha/4)g).
\]

The nominal and alpha in [1/2,1] final-reading intervals overlap. In particular,
nominal g=1 and faulty (g,alpha)=(4/3,1/2) both produce final value 1/2. The
retained overlap certificate checks those independent nuisance assignments.
Jointly, contrast y_1/2-y_2 equals alpha*g/4: it is zero nominally and at least
1/8 in the fault family. With error delta per reading, the two-world contrast
error is at most 3delta. Thus delta<1/24 guarantees separation. The receipt
replays a full-domain certificate at delta=1/100. No noisy division is needed.

There cannot be a fixed positive robust margin uniformly across alpha>0 all the
way down to zero for a continuous finite panel: the faulty response converges
to the nominal response. The declared positive-minimum-severity bands are part
of the problem, rather than a technical afterthought.

## Four-location pilot and interpretation

The retained four-by-four pilot uses bonds (4,5), (6,7), (1,5) and (5,6), with
the original symmetric center sensor and pulse-then-wait words of horizons one
through four. It covers the closed bands {0}, [1/2,3/4] and [3/4,1], using known
k=1/8, lambda=1/100 and g=1. These singleton calibration coordinates are reported
explicitly. The symbolic engine supports wider boxes, but no wider physical
calibration guarantee is inferred from this pilot.

The two reflected exterior bonds have overlapping complete-domain families
under that symmetric observation language. Several other pairs also overlap
because the allowed severity can mimic the measured effect. Pairs involving the
interior central bond obtain strict full-domain separation on the two positive
bands. Every reported overlap has explicit rational parameters and every strict
region has a covering certificate; samples independently replay source flux but
do not establish the continuum claim.

Tests include a nonmonotone polynomial whose whole-domain interval touches the
other family but whose two rational subcells prove strict separation. Tampering
with the covering boundary is rejected. Independent scalar overlap, touching
and intentionally unresolved fixtures exercise all three output semantics.
Run `PYTHONPATH=src python scripts/thermal_severity.py --check` for the deterministic
source-pinned replay, retained rational polynomials, covering trees and budgets.
