# Frontier companion: arithmetic, poles, and positive interfaces

**Release scope.** This is a separate research companion to the published
v0.4.0 baseline, not an implementation of NX36. It adds four narrowly stated
mathematical tools, exact executable checks, and a map of their implications.
The detailed proofs are the four FR documents assembled after this introduction
in the companion manuscript. They have ordinary mathematical proofs and exact
computational checks; no new Lean coverage is claimed.

## The three questions remain distinct

The programme asks how to reconstruct larger graph classes efficiently,
whether the fixed-pinning series is complete or admits a full-series collision,
and which formally invisible symmetric-interface directions actual graphs can
realize. A finite prefix collision answers none of these by itself. The present
work supplies additional necessary invariants and structural constraints rather
than changing that standard of evidence.

For a simple graph G, write

\[
 E_G(h)=\sum_{uv\in E(G)}(h_u-h_v)^2,\qquad
 F_{G,\lambda}(x,q)=\sum_{h\ge0}x^{\sum h_v}
 q^{E_G(h)+\lambda\sum h_v^2}.
\]

The translation-invariant local series is L_G=F_{G,0}. The dominating-terminal
interior sequence uses A_G=F_{G,2}. These are different objects: the pole
arguments for L_G do not transfer to A_G. The rational denominator argument
works for both, and the centered-theta limit specifically requires positive
pinning. The tree results concern a third object, an ordered terminal kernel.

| Companion | Mathematical input | Information extracted | Scope that must travel with the result |
|---|---|---|---|
| FR01: exact connected pole divisors | Complete L_G at one real 0<q<1 | Connected order, number of components; component-size multiset in a proved noncancellation sector | Analytic full-series information, not a finite-prefix oracle; mixed component sizes need a zero-free hypothesis |
| FR02: rational denominator recovery | Known order n and one coefficient at a rational q=A/B | Maximum degree and its multiplicity, for local or integer-pinned series | Exact rational coefficient; a sufficient volume is logarithmic in n, but obtaining that coefficient has its own cost |
| FR03: positive tree interfaces | Full ordered kernel, or a common height box | Strict total positivity and terminal-distance leading minors | Applies to trees and ordered observations; a global volume truncation can destroy positivity |
| FR04: centered pinned theta limits | Complete positively pinned sequence | Graph order and a finite family of limiting affine-lattice theta values | Equality of these invariants is necessary, not sufficient, for equality of the original sequence |

## Why these are useful together

The new tools inspect different parts of the same population. Pole data sees
the common-translation direction that zero pinning leaves free. Denominator
data sees the largest energy present at a fixed volume, even though positive
real evaluation makes that contribution numerically tiny. Centered theta data
sees the low-energy distribution after its universal quadratic decay has been
removed. Tree minors inspect relations among several boundary observations
instead of treating each kernel entry as an arbitrary scalar.

This separation matters. At rational q, a reduced denominator is arithmetic
information, not a numerical condition number. At positive pinning, a large-R
theta limit is a necessary limiting signature, not an exact finite-state model
of every coefficient. A positive full kernel is not a positive coefficientwise
truncation. Keeping these meanings explicit makes the tools useful without
turning any of them into an unsupported completeness claim.

## Arithmetic information from one coefficient

Let a_R=[x^R]F_{G,\lambda}(x,A/B), where A/B is reduced, 0<A<B, and
lambda is a nonnegative integer. Let Delta be the maximum degree and m its
multiplicity. Put c=Delta+lambda. Except for the unpinned edgeless case,
the largest energy is K=cR^2, attained exactly by placing all R units of
height on a maximum-degree vertex. Every other profile lies at least

\[
 g=\min\{R^2,\,2c(R-1)\}
\]

energy units below it. Consequently

\[
 B^K a_R=mA^K+B^g T,\qquad T\in\mathbb Z.
\]

Choose R>=2 with B^{2(R-1)}>n. The unknown multiplicity is then smaller
than the modulus B^g. Denominator depth recovers c, and a modular inverse
recovers m. Composite B needs no prime factorization. This gives a particularly
useful checkpoint for a claimed fixed-pinning full-series collision: it must
preserve the maximum degree and the number of maximum-degree vertices.

The decoder receives n, q and a_R, not the graph. Independent enumeration
supplies test coefficients. The distinction prevents the verification from
silently obtaining the answer from graph metadata.

## What limiting observations preserve and forget

For positive lambda, set C=Laplacian(G)+lambda I and R=kn+r, 0<=r<n.
Centering h at R/n gives

\[
 E_G(h)+\lambda\|h\|^2
 =\lambda R^2/n+y^{\mathsf T}Cy,
 \quad y=h-(R/n)\mathbf1.
\]

Along a fixed residue r, the centered admissible domains increase to an affine
root lattice. Hence the scaled coefficients converge monotonically to a
theta value. The lost orthant boundary has an explicit Gaussian upper bound.
The graph's order itself follows from

\[
 \lim_{R\to\infty}\frac{\log a_R}{R^2}
 =\frac{\lambda\log q}{n}.
\]

Thus an alleged full-series collision cannot hide a change in order by changing
the number of components or by exploiting a short coefficient prefix. It must
also match all the centered residue limits. Conversely, matching those finitely
many limits leaves the exact finite orthant corrections unresolved. Those
corrections remain a possible source of distinguishing information.

At the working rational parameter q=1/2, the same information can be enclosed
without algebraic roots. Retain the graph-independent factor instead:

\[
 \Psi_r(q)=\sum_{\substack{z\in\mathbb Z^n\\\sum z_i=r}}
 q^{E_G(z)+\lambda\|z\|^2},\qquad
 q^{-\lambda(nk^2+2kr)}a_{kn+r}\uparrow\Psi_r(q).
\]

Every exponent in this form is integral. Exact rational Gaussian bounds
therefore certify intervals for Psi at every rational q in (0,1), including
one half. Disjoint intervals for a common residue prove full-series
inequivalence. Overlapping intervals are inconclusive, and equal limiting
values still do not prove equality of the original coefficients.

## A realizability constraint with the correct semantics

A tree's unique terminal path factorizes its ordered kernel into Gaussian edge
matrices and positive diagonal branch messages. Cauchy-Binet then supplies
strict positivity of every finite minor with increasing pin indices. The
leading minor also records the path length. These facts constrain a proposed
ordered tree interface far more than nonnegative individual coefficients do.

There is a useful warning supplied by an actual graph, rather than a hypothetical
pathology: the four-vertex path truncated at interior volume one has a negative
two-by-two determinant at positive x and q. The full kernel is strictly totally
positive. The common height box used in FR03 is a product domain compatible
with the factorization; the volume simplex is not. A realizability test must
therefore certify the relevant complete coefficient order or a valid box before
using a minor as an obstruction.

These constraints apply to ordered kernels. Averaging a kernel with its transpose
is a different operation, and the new theorem does not automatically impose the
same strict positivity on every symmetric interface. The surviving symmetric
ambiguities consequently remain open.

## How Claude should use this beside NX36

| Future task | Safe use of this companion | Work deliberately left to NX36 or later research |
|---|---|---|
| Larger reconstruction classes | Use the degree decoder as a necessary invariant; use the proved restricted pole sectors as analytic examples | A general efficient graph reconstruction algorithm |
| Fixed-pinning collision search | Reject candidates with different recovered extremal degrees, multiplicities, order, or centered theta signatures | Producing a pair with equal complete series, or proving all pairs separate |
| Symmetric-interface realization | Use ordered tree minors only when an ordered lift is available and the complete truncation order is justified | Constructing or excluding the surviving symmetric candidates |
| Certificate design | Preserve rational parameter, coefficient volume, shift, graph order, bound domain and retained witness | Integrating these objects into NX36's proposed generic certificate infrastructure |
| Performance claims | Separate decoding cost from coefficient computation and exact output size | Benchmarks or asymptotic improvements not actually measured here |

The new modules and receipts have FR-specific names. No NX packet is marked
accepted, no NX implementation module is overwritten, and no existing theorem
is relabeled as a new result. The established sixteen-chapter monograph stays
intact; this companion is supplied as a separate manuscript so it can be reviewed
and merged deliberately.

## Literature and proof status

The two classical engines used here are Gaussian Poisson summation and total
positivity of the exponential kernel. A modern primary-source treatment of
theta transformations is Christina Roehrig, *Siegel theta series for indefinite
quadratic forms*, Research in Number Theory 7, 45 (2021),
https://doi.org/10.1007/s40993-021-00272-y. Kenneth W. Johnson and Donald
St. P. Richards, *Hyperdeterminantal Total Positivity*, SIGMA 21, 055 (2025),
https://doi.org/10.3842/SIGMA.2025.055, explicitly identifies exp(xy) as the
classical kernel and discusses composition through Binet-Cauchy.

The graph pole noncancellation, rational denominator decoder, tree-distance
specialization and pinned orthant-limit statements are derived in the FR
documents. These references support the underlying classical machinery, not
a claim that the project-specific results have already appeared there. A full
priority search and proof-assistant formalization remain separate work.



# FR01: exact connected pole divisors and a controlled reconstruction sector

This companion result concerns the complete local series at one fixed real
parameter, not a finite-prefix extrapolation. It is independent of the NX36
implementation programme. It strengthens the existing entire-normalization
theorem SNG-F39: for a connected graph, every possible root-of-unity pole is
actually present. It also gives a rigorous, explicitly restricted sector in
which poles recover the component-size population.

The new results are proved below in ordinary mathematical prose. The Python
module implements rational bounds, finite cyclotomic Gaussian enclosures, and
the combinatorial inversion. No proof-assistant formalization is claimed.

## 1. Objects and the question left by entire normalization

Let G be a finite simple graph on n vertices, let 0<q<1, and write

\[
 E_G(a)=\sum_{uv\in E(G)}(a_u-a_v)^2,
 \qquad
 L_G(x,q)=\sum_{a\in\mathbb Z_{\ge0}^n}x^{\sum_v a_v}q^{E_G(a)}.
\]

For a connected graph, common translation partitions the original labeled
height population into disjoint infinite rays. The representative of a ray
has minimum zero. Consequently

\[
 L_G(x,q)=\frac{B_G(x,q)}{1-x^n},\qquad
 B_G(x,q)=\sum_{\substack{a\ge0\\\min a=0}}
                x^{\sum a_v}q^{E_G(a)}.
\]

SNG-F39 proves that B_G is entire in x. This proves only that the poles of
L_G are *among* the nth roots of unity. A numerator zero could in principle
remove a denominator zero. The present first theorem rules this out exactly
at the roots belonging to the connected component itself.

## 2. The connected noncancellation theorem

**Theorem FR01.1.** For every connected n-vertex graph and every fixed
0<q<1, B_G(zeta,q) is a strictly positive real number whenever zeta^n=1.
Thus L_G has a simple pole at every nth root of unity and no other poles.
More precisely,

\[
 \lim_{r\uparrow1}(1-r)L_G(r\zeta,q)
       =\frac{B_G(\zeta,q)}{n}>0,
 \qquad
 \operatorname{Res}_{x=\zeta}L_G(x,q)
       =-\frac{\zeta}{n}B_G(\zeta,q).
\]

The adjective positive concerns B_G and the displayed radial normalization;
the complex residue itself need not be positive real.

**Proof.** Choose a root vertex 0. Every height class modulo common integer
translation has a unique anchored representative z with z_0=0 and
(z_1,...,z_{n-1}) in Z^(n-1). Its minimum-zero representative is
a=z-(min z)1. Therefore

\[
 E_G(a)=E_G(z),\qquad
 \sum a_v=\sum_{v\ne0}z_v-n\min z.
\]

The last term disappears from the phase at zeta^n=1. If Q is the reduced
Laplacian obtained by deleting row and column 0, then

\[
 B_G(\zeta,q)
    =\sum_{z\in\mathbb Z^{n-1}}
       q^{z^TQz}\zeta^{\mathbf1^Tz}.
\]

Connectedness makes Q positive definite: a vector of zero energy is constant
on every edge, hence constant on the connected graph, and anchoring forces
that constant to be zero. In particular this Gaussian series converges
absolutely. Write s=-log q>0 and zeta=exp(2*pi*i*k/n), and set
alpha=(k/n)1. Gaussian Fourier transform and Poisson summation give

\[
 \boxed{
 B_G(\zeta,q)=
 \frac{\pi^{(n-1)/2}}{s^{(n-1)/2}\sqrt{\det Q}}
 \sum_{m\in\mathbb Z^{n-1}}
 \exp\!\left[-\frac{\pi^2}{s}
 (m-\alpha)^TQ^{-1}(m-\alpha)\right].}
\]

Every summand on the right is a strictly positive real number, and the sum
converges. Hence B_G(zeta,q)>0. Since 1-x^n has a simple zero at zeta,
the quotient has exactly the claimed simple pole. The radial formula follows
from (1-r^n)/(1-r)->n; the residue follows from the derivative -n*zeta^(n-1).
For n=1, Q has dimension zero, B_G=1 and L_G=1/(1-x), so the same result
holds directly. This completes all cases. QED.

**Why the argument is specific.** The phase is a character of the quotient
height lattice only when zeta^n=1. At an unrelated unit-circle point, the
factor zeta^(-n min z) remains. Dropping that factor would turn a proof for
the graph's own denominator roots into a false proof for every root of unity.

**Consequence FR01.2.** The full fixed-q local series determines whether G
is connected. For a connected graph it determines its vertex count from
the complete set of poles. This does not determine the connected graph's
isomorphism type. Full-series equality of two connected graphs forces equal
orders, but the connected fixed-q completeness problem remains open.

## 3. Disconnected products and the cancellation obstruction

Let G have connected components H_1,...,H_c with sizes n_i. Independence of
the original assignments gives

\[
 L_G(x,q)=\prod_{i=1}^c L_{H_i}(x,q)
         =\frac{\prod_i B_{H_i}(x,q)}{\prod_i(1-x^{n_i})}.
\]

At x=1, every numerator is positive by Theorem FR01.1. Therefore the pole
order at 1 is exactly c, with no additional hypothesis. In particular a
disconnected graph has pole order at least two there, proving the first
assertion of Consequence FR01.2.

At a primitive dth root zeta, components with d dividing n_i each have a
simple pole. But a component with d not dividing n_i has no denominator
pole there and its entire numerator has not been proved nonzero there.
Such an analytic factor could cancel a pole of a different component.
Thus the tempting general assertion

\[
 \operatorname{poleord}_{\zeta}L_G
 \stackrel{?}{=}\#\{i:d\mid n_i\}
\]

is **not** an unconditional result of the connected theorem. This package
neither exhibits such a cancellation nor proves that it cannot occur.
Unknown cancellation is kept explicit in the API.

At a given zeta the exact signed order, with zeros counted negatively, is

\[
 \sum_{i:d\mid n_i}1
  -\sum_{i:d\nmid n_i}\operatorname{ord}_{\zeta} B_{H_i}.
\]

The second sum is the precise missing datum. A finite numerical sample
showing it to be zero cannot establish an all-graph noncancellation theorem.

## 4. A uniform zero-free sector from a spanning tree

Define the scalar Gaussian theta value

\[
 \vartheta(q)=\sum_{k\in\mathbb Z}q^{k^2}
            =1+2\sum_{k\ge1}q^{k^2}.
\]

**Lemma FR01.3.** If H is connected on m vertices, then

\[
 B_H(1,q)\le\vartheta(q)^{m-1}.
\]

**Proof.** Choose a spanning tree T and orient it away from a root. The
integer differences on its m-1 edges are independent integer coordinates
on the anchored height lattice. Tree energy is the sum of their squares.
Every extra graph edge adds a nonnegative square. As 0<q<1,
q^(E_H)<=q^(E_T) term by term. Summing over the tree coordinates factors
the upper bound into m-1 copies of vartheta. For m=1 it is the identity
1<=1. QED.

Since the normalized series has constant term 1 and nonnegative real
coefficients, for every |x|<=1,

\[
 |B_H(x,q)-1|\le B_H(1,q)-1
                   \le\vartheta(q)^{m-1}-1.
\]

**Theorem FR01.4.** Fix an integer N>=1. If

\[
 \boxed{\vartheta(q)^{N-1}<2,}
\]

then the numerator of every connected graph of size at most N is zero-free
on the entire closed unit disk. Consequently, for any graph whose component
sizes are at most N, the primitive-d root pole order is exactly

\[
 p_d=\sum_{k\ge1}b_{kd},
\]

where b_m is the number of m-vertex components. This is a sufficient
small-q sector, not an assertion that zeros appear outside that sector.

The strict inequality matters: an enclosure reaching 2 does not give the
strict distance from zero used by the triangle inequality.

For a simple explicit sufficient inequality, k^2>=k gives

\[
 \vartheta(q)\le\frac{1+q}{1-q},\qquad
 \left(\frac{1+q}{1-q}\right)^{N-1}<2.
\]

For implementation we use a much sharper rational enclosure. For K>=0,

\[
 \vartheta(q)\le U_K(q):=
 1+2\sum_{k=1}^Kq^{k^2}
 +\frac{2q^{(K+1)^2}}{1-q^{2K+3}}.
\]

Indeed each successive exponent increment in the omitted tail is at least
2K+3. Exact rational comparison of U_K(q)^(N-1) with 2 certifies the
condition. At q=1/16 the implementation certifies all components of size
at most six. At q=1/2 the bound fails already for size two; this refusal
does not contradict the unconditional connected theorem at q=1/2.

## 5. Inverting the component-size population

Assume the full profile p_1,...,p_N has been justified, for example by
Theorem FR01.4. Descending inversion gives

\[
 \boxed{b_m=p_m-\sum_{k\ge2}b_{km},\qquad m=N,N-1,\ldots,1.}
\]

Equivalently, with the classical integer Mobius function,

\[
 b_m=\sum_{k\ge1}\mu(k)p_{km}.
\]

These sums are finite because no component exceeds N. For the component
population (1,1,2,3,3,6), the profile is
(p_1,...,p_6)=(6,2,3,0,0,1), and inversion returns exactly two isolated
vertices, one size-two component, two size-three components, and one
size-six component. No multiplicity is divided by an automorphism count.

**Corollary FR01.5.** On cluster graphs (disjoint unions of complete graphs)
whose largest component has size at most N, the complete fixed-q local
series is a complete isomorphism invariant whenever the small-q hypothesis
of Theorem FR01.4 holds. The proof recovers b_m from the divisor; these
multiplicities determine the graph because a complete component of each
size has only one isomorphism type.

For general graphs the same result recovers component sizes only, not the
isomorphism types of their connected components. There is no claim that a
finite coefficient prefix reveals the poles or provides a completeness
cutoff. The theorem uses the full analytic function determined by the series.

## 6. An unconditional all-q class

Suppose every nontrivial component has the same size m>=2, with any number
of isolated vertices. At every denominator root of a nontrivial component,
all nontrivial components satisfy zeta^m=1 and hence have positive normalized
numerators. Isolated factors 1/(1-x) never vanish. Thus the divisor formula
p_d=sum_{d|n_i}1 is valid for this class at every 0<q<1.

In particular the complete fixed-q local series distinguishes every graph

\[
 kK_m\;\sqcup\;\ell K_1
 \quad(k\ge1,\ m\ge2,\ \ell\ge0)
\]

from every other graph in that class. The largest primitive pole order is
m; its multiplicity is k; the pole order at 1 is k+ell. Purely isolated
graphs are handled separately by (1-x)^(-ell). This is an infinite class
of disconnected interiors beyond the cycle-union reconstruction family,
but its result concerns the unpinned local series specified here.

## 7. Generic parameters in a fixed finite family

For a fixed connected H and a fixed unit root zeta, B_H(zeta,q) is
holomorphic in |q|<1. Uniform absolute convergence on compact subdisks
follows by domination by B_H(1,|q|) and the Gaussian lattice bound.
Its value at q=0 is 1, since connected zero-energy normalized profiles
contain only the all-zero assignment. Therefore it is not identically
zero and its zeros are locally discrete.

For any fixed finite graph family, there are only finitely many components
and relevant roots. Outside a locally discrete exceptional set of q in
(0,1), every off-denominator cancellation is absent and the divisor
inversion is valid. On every compact subinterval strictly inside (0,1)
the exceptional set is finite. This does not locate it, certify q=1/2,
or exclude rational exceptional values. No such arithmetic strengthening
is claimed.

## 8. Exact finite Gaussian enclosures

`anchored_gaussian_box` uses integer differences r_e on a rooted spanning
tree, rather than bounding the heights themselves. It sums exactly over
|r_e|<=H in the cyclotomic ring Q[zeta]. There are
(2H+1)^(n-1) profiles, checked against a budget before enumeration.

Let theta_H=1+2 sum_{k=1}^H q^(k^2). As E_G>=sum_e r_e^2, the absolute
mass outside this difference box is bounded by

\[
 \vartheta(q)^{n-1}-\vartheta_H(q)^{n-1}
 \le U_K(q)^{n-1}-\vartheta_H(q)^{n-1},\qquad K\ge H.
\]

This gives a rational absolute complex-error radius around the exact
cyclotomic partial sum. Different spanning-tree boxes need not sum the
same finite populations; their certified balls nevertheless contain the
same full theta value. Tests exercise this root-choice failure mode.
For K_2, the character at -1 reduces independently to
sum_{z=-H}^H (-1)^z q^(z^2), and at q=1/2,H=4 the enclosure already
proves strict positivity by rational arithmetic. A triangle at a primitive
third root is checked independently in direct rooted height coordinates.

The finite Gaussian calculation is evidence and an evaluable bound. The
all-graph noncancellation theorem follows from Poisson positivity, not from
checking many boxes or observing positive floating-point approximations.

## 9. Scope relative to the main frontiers

The series A_H(x,q)=sum_a x^(sum a) q^(E_H(a)+2 sum a_v^2), used by
dominating-terminal pinning, has an absolute quadratic pinning term. It
is entire in x and does not have the translation denominator 1-x^n.
Therefore this pole theorem does not prove completeness for the fixed-pinned
A_H series. It provides a separate invariant for unpinned L_H and a
controlled class where full-series reconstruction is proved.

The work does not realize a symmetric-interface null vector, settle
fixed-pinning completeness, extend a finite-prefix cutoff, or duplicate
NX36's proposed parameter-observability and ideal-closure projects.
The surviving questions remain explicit: unit-circle zeros of arbitrary
off-denominator numerators; effective localization of their q exceptions;
full-series collisions in connected graphs; and reconstruction under
quadratic pinning. These are logical next problems, not completed claims.

## 10. Reproduction

From the repository root:

```sh
PYTHONPATH=src python -m unittest tests/test_pole_divisors.py -v
PYTHONPATH=src python scripts/fr01_pole_divisors.py --check
```

The retained JSON records exact rational certificates and bounded Gaussian
examples. Its profile inversion assumes the analytic hypotheses stated
in each record; the inverter alone cannot validate supplied analytic data.


# FR02: arithmetic recovery from a single fixed-pinning coefficient

**Status.** Proved project result, exact decoder, independently enumerated finite checks. This companion does not implement an NX36 work packet. It establishes a new necessary condition for fixed-pinning equality and a reconstruction theorem for one restricted family. It does not prove completeness of the unmarked graph series.

## 1. What information can survive a rational specialization?

The existing exact machinery retains an energy polynomial at each volume. If that polynomial is available, its largest exponent is an obvious source of graph information. A more difficult question is whether the information remains available after replacing the polynomial variable by a single rational number. Different integer energy polynomials can have the same rational value. Indeed, the example below has two different maximum degrees and an equal first coefficient at the project's working value \(q=1/2\).

Nevertheless, sufficiently concentrated height profiles leave a recoverable denominator signature. The signature is not the whole degree distribution. It is the largest degree and the number of vertices having that degree. The decoder needs only one rational coefficient, the graph order, and the declared pinning parameter. It does not receive the graph, the coefficient's energy support, a marked series, or a second value of \(q\).

The same argument applies directly to the dominating-terminal interior sequence already used by the charge interface. Introduce an integer diagonal shift \(\lambda\ge0\) and write

\[
F_{G,\lambda}(x,q)
 =\sum_{h\in\mathbb Z_{\ge0}^{n}}
 x^{\sum_vh_v}\,
 q^{E_G(h)+\lambda\sum_vh_v^2},
\qquad
E_G(h)=\sum_{uv\in E(G)}(h_u-h_v)^2.
\]

The case \(\lambda=0\) is the raw local series \(L_G\). The case \(\lambda=2\) is the existing interior series \(A_G\) for two dominating terminals. This is the diagonal pinning already present in that interface, rather than a new observation variable. Define

\[
a_R(G;q,\lambda)=[x^R]F_{G,\lambda}(x,q),
\qquad
\Delta=\max_v\deg_G(v),
\]

\[
m=\#\{v:\deg_G(v)=\Delta\},
\qquad c=\Delta+\lambda.
\]

Every graph in this note is finite, simple, undirected, and has known order \(n\ge1\). The supplied coefficient is a coefficient of the full nonnegative-height series. Multiplying by \(1-x^n\), imposing minimum zero, restricting span, or changing to componentwise normalization changes the input and is outside the decoder's contract.

## 2. The concentration gap

**SNG-R02.1 — Extremal-energy gap.** Let \(R\ge2\). If \(c\ge1\), the largest exponent in \(a_R(G;q,\lambda)\), considered as a polynomial in \(q\), is

\[
K=cR^2,
\]

and its coefficient is exactly \(m\). Every other exponent is at most \(K-g\), where

\[
\boxed{g=\min\{R^2,\;2c(R-1)\}.}
\]

To see this, expand the quadratic form as

\[
E_G(h)+\lambda\sum_vh_v^2
 =\sum_v(\deg_G(v)+\lambda)h_v^2
   -2\sum_{uv\in E(G)}h_uh_v
 \le c\sum_vh_v^2.
\]

All heights are nonnegative, so the last edge term can only lower the energy. Placing the entire volume at a vertex of maximum degree gives energy \(cR^2\). There are exactly \(m\) such labeled assignments. No division by graph automorphisms is involved.

There are two other kinds of assignment, and both must be considered. A spike placed at a lower-degree vertex has energy at most \((c-1)R^2\), hence gap at least \(R^2\). An assignment with at least two positive coordinates satisfies

\[
\sum_vh_v^2\le(R-1)^2+1
 =R^2-2(R-1),
\]

because concentrating all but one of the units in a single coordinate maximizes that sum. Its energy is at most \(cR^2-2c(R-1)\). Taking the smaller of the two guaranteed gaps proves the result.

The minimum in the displayed formula is essential. A large maximum degree does not make a lower-degree spike disappear. For example, at \(R=2\) a maximum-degree-four vertex and a degree-three vertex produce spike energies separated by only four, even though the nonsingle-spike bound alone would suggest a gap of eight. The implementation has an explicit regression test for that case.

If \(c=0\), then \(\lambda=0\) and \(G\) is edgeless. Every profile has energy zero, and

\[
a_R(G;q,0)=\binom{n+R-1}{R}.
\]

This case is handled separately. An edgeless graph with \(\lambda=2\) belongs to the nondegenerate \(c=2\) case and must not use the unpinned edgeless shortcut.

## 3. A denominator invariant without factoring the denominator

Fix a reduced rational

\[
q=A/B,\qquad 0<A<B,\qquad \gcd(A,B)=1.
\]

The integer \(B\) may be composite. For an integer \(u\ne0\), let

\[
\operatorname{ord}_B(u)=\max\{r\ge0:B^r\mid u\}.
\]

For composite \(B\), this is a divisibility depth and should not be confused with a valuation: in general it is not additive under multiplication. What we use is only that multiplying by a unit modulo \(B\) preserves this depth.

For a positive reduced denominator \(D\), define its clearing depth

\[
\kappa_B(D)=\min\{k\ge0:D\mid B^k\}.
\]

If no such integer exists, \(D\) contains a prime absent from \(B\) and cannot occur in a coefficient of this rational specialization. The following procedure computes the clearing depth without factoring either integer:

\[
D_0=D,
\qquad
D_{r+1}=D_r/\gcd(D_r,B),
\]

stopping when \(D_r=1\). If \(D_r>1\) and its gcd with \(B\) is one, the procedure rejects. For justification, if a prime occurs in \(D\) with exponent \(e\) and in \(B\) with exponent \(b>0\), each step removes up to \(b\) copies of that prime. It disappears after exactly \(\lceil e/b\rceil\) steps. Thus the total number of steps is the least exponent whose power of \(B\) contains the entire denominator. Factoring is useful for this proof but is not performed by the algorithm.

For example,

\[
\kappa_6(72)=3,
\qquad
\kappa_{12}(8)=2,
\qquad
\kappa_{12}(18)=2.
\]

Taking a single prime valuation or treating \(B\) as prime would give the wrong general API.

## 4. The inverse theorem

Choose any \(R\ge2\) satisfying the strict inequality

\[
\boxed{B^{2(R-1)}>n.}
\]

Let \(D\) be the positive reduced denominator of the exact rational coefficient \(a_R(G;A/B,\lambda)\), and put \(k=\kappa_B(D)\).

**SNG-R02.2 — Single-coefficient rational recovery.** With the hypotheses above,

\[
\boxed{
\Delta=\left\lceil\frac{k}{R^2}\right\rceil-\lambda
}
\]

except that the unpinned edgeless case has \(k=0\), \(\Delta=0\), and \(m=n\). Once \(\Delta\) is recovered and \(c=\Delta+\lambda\ge1\), put

\[
K=cR^2,
\qquad
g=\min\{R^2,2c(R-1)\},
\]

\[
M=B^g,
\qquad
N=B^K a_R(G;A/B,\lambda)\in\mathbb Z.
\]

Then

\[
\boxed{
m\equiv N(A^K)^{-1}\pmod M,
\qquad 1\le m\le n<M.
}
\]

Consequently the least nonnegative residue on the right is the actual multiplicity, not merely a congruence class containing several admissible values.

**Proof.** The concentration gap gives

\[
N=mA^K+B^gT
\]

for some integer \(T\): every term below the leading exponent contributes at least \(g\) powers of \(B\) after multiplication by \(B^K\). Because \(R\ge2\) and \(c\ge1\),

\[
g\ge2(R-1),
\qquad
B^g>n\ge m.
\]

Write \(h=\operatorname{ord}_B(m)\). The last inequality gives \(h<g\). The leading summand has exactly divisibility depth \(h\), since \(A\) is coprime to \(B\); the other summand is divisible by \(B^g\). After division by \(B^h\), the first summand is nonzero modulo \(B\), whereas the second is zero modulo \(B\). Hence

\[
\operatorname{ord}_B(N)=h.
\]

No additivity assertion about composite-base divisibility depth has been used.

Now \(a_R=N/B^K\). For every \(0\le r\le K\), the rational number \(B^r a_R\) is an integer exactly when \(B^{K-r}\mid N\). Its first integral value therefore occurs at \(r=K-h\), so

\[
k=K-h=cR^2-h.
\]

Moreover \(B^{2(R-1)}>n\ge m\) implies \(h<2(R-1)<R^2\). Thus

\[
(c-1)R^2<k\le cR^2,
\]

which proves \(c=\lceil k/R^2\rceil\), and subtraction of the declared shift gives \(\Delta\). Finally reduce the congruence for \(N\) modulo \(B^g\) and invert \(A^K\), which is a unit modulo \(B^g\). Since \(m\le n<B^g\), the residue is unique in the admissible range. This proves the multiplicity formula.

The smallest permitted observation volume is

\[
R_*(n,B)=\min\{R\ge2:B^{2(R-1)}>n\}.
\]

It grows logarithmically with known order for fixed \(B\). The code finds it using integer multiplication, avoiding logarithm rounding at the strict boundary. Larger supplied volumes are valid as well.

## 5. What this says about fixed-pinning completeness

For known order and the same declared shift, equality of the entire fixed-rational series forces equality of \(\Delta\) and \(m\), because equality includes the coefficient at \(R_*\). In fact, agreement at that single coefficient is enough for these two invariants. Thus any proposed full-series collision with different maximum degrees, or different numbers of maximum-degree vertices, is impossible.

This statement is useful both for \(L_G\) and for the fixed-pinning interior sequence \(A_G\). It supplies a genuine necessary condition for future collision searches without confusing a finite observation with full equality. The conclusion goes only one way:

\[
F_{G,\lambda}(x,A/B)=F_{H,\lambda}(x,A/B)
\quad\Longrightarrow\quad
(\Delta_G,m_G)=(\Delta_H,m_H)
\]

when the graph orders agree. Equal recovered extrema do not imply equal series, equal graphs, equal degree distributions, or equal component structure. No such converse is asserted.

Known order is part of the input. This theorem does not infer the number of vertices from one coefficient, and it does not compare series with different numbers of vertices by silently inserting isolated vertices. Diagonal shift is also part of the input: \(A_H\) and \(L_H\) must not be decoded using each other's convention.

## 6. A first-coefficient collision that the decoder resolves

Let \(G\) be the complete multipartite graph with twelve singleton parts and two parts of size three. Let \(H\) be the complete multipartite graph with nine parts of size two. Both have order eighteen. Their degree data are

| Graph | Maximum degree | Multiplicity | Other degrees |
|---|---:|---:|---|
| \(G=K_{1,\ldots,1,3,3}\) | 17 | 12 | Six vertices of degree 15 |
| \(H=K_{2,\ldots,2}\) | 16 | 18 | None |

At \(q=1/2\), the first coefficients agree exactly:

\[
[x]L_G
 =12\cdot2^{-17}+6\cdot2^{-15}
 =18\cdot2^{-16}
 =[x]L_H
 =\frac9{32768}.
\]

This is a concrete warning against reading a specialized degree polynomial as if its exponents remained visible. For order eighteen, the recovery cutoff is \(R_*=4\). Exact independent enumeration at that volume gives:

| Quantity | \(G\) | \(H\) |
|---|---:|---:|
| Profiles enumerated | 5,985 | 5,985 |
| \(R^2\) | 16 | 16 |
| Leading energy \(K\) | 272 | 256 |
| Reduced denominator clearing depth \(k\) | 270 | 255 |
| \(\lceil k/16\rceil\) | 17 | 16 |
| Guaranteed gap \(g\) | 16 | 16 |
| Residue modulus \(2^g\) | 65,536 | 65,536 |
| Recovered multiplicity | 12 | 18 |

The denominator-depth losses of two and one are exactly \(\operatorname{ord}_2(12)\) and \(\operatorname{ord}_2(18)\). The numerator congruence recovers the multiplicities despite that cancellation. The retained JSON contains both full rational coefficients; this table omits their long numerators only to keep the mathematical mechanism visible.

## 7. A restricted reconstruction theorem beyond cycle interiors

Consider the complete split graph obtained by joining a clique of size \(c\) to an independent set of size \(n-c\). The word "complete" here describes the full join: every clique vertex is connected to every independent vertex. The family is a strict subclass of the split graphs and is not the family of all graphs admitting a clique/independent partition.

If \(0<c\le n-2\), the clique vertices have degree \(n-1\), whereas the independent vertices have degree \(c\). Thus

\[
\Delta=n-1,
\qquad m=c.
\]

The case \(c=0\) is edgeless. The presentations \(c=n-1\) and \(c=n\) describe the same complete graph, so the canonical answer for a complete graph is \((c,n-c)=(n,0)\). With this convention, the recovered extremum identifies the isomorphism type throughout this known-order family, using one rational coefficient at \(R_*\). The same is true using its pinned \(A_H\) coefficient at shift two.

**SNG-R02.3 — Complete-split reconstruction.** Within the declared known-order complete-split family, either the raw local coefficient or the shift-two pinned coefficient at \(R_*\) uniquely determines the graph up to isomorphism. The reconstruction consists of the arithmetic decoder followed by the elementary degree cases above.

The caller must supply the family-membership hypothesis. An arbitrary graph can share the same extremal degrees with a complete split graph. The software therefore does not claim to recognize complete split graphs from this invariant alone.

This is a reconstruction result beyond cycle interiors, but it is deliberately limited. These graphs are highly structured; their isomorphism types are controlled by a single nontrivial integer parameter. The theorem does not supply a universal graph reconstruction algorithm or an efficient coefficient compiler for arbitrary dense graphs.

## 8. Computation, reproducibility, and cost

The implementation uses only Python's standard library. The public decoder in `denominator_recovery.py` takes `order`, exact rational `q`, exact rational `coefficient`, an optional declared `volume`, and nonnegative integer `diagonal_shift`. It rejects floating point input and booleans, checks the strict observation cutoff, bounds denominator clearing depth by the maximum possible diagonal energy, and validates that the recovered multiplicity lies between one and the supplied order. These are useful consistency checks, not a complete recognizer for graph-realizable rational coefficients.

The companion receipt enumerates every labeled simple graph through order five: 1,099 graphs. For each graph it uses \(q=1/2,2/3,5/6\), with both shifts zero and two. This gives 6,594 exact decoder comparisons and 138,570 height-profile evaluations. The population oracle uses stars-and-bars separator positions and direct edge energy. It does not call the decoder to compute a coefficient, nor does it infer the expected answer from denominator data. The expected maximum degree and multiplicity come directly from graph adjacency.

| Evidence | Declared population or purpose |
|---|---|
| Exhaustive receipt | All labeled simple graphs of orders 1–5; three rational pinnings; shifts 0 and 2 |
| Focused unit population | All labeled graphs of orders 1–4, both series, all three pinnings |
| Composite denominator cases | Uneven prime exponents in clearing depth; multiplicities divisible by the full composite base |
| Degenerate cases | One vertex, edgeless unpinned series, edgeless pinned series |
| Gap regression | Lower-degree spike controls the gap when the nonsingle bound is too large |
| Family reconstruction | All complete-split parameters through order seven, with canonical complete graphs |
| Retained collision | Two order-eighteen multipartite graphs with equal first coefficient |

The exact coefficient can still be expensive to obtain. Direct enumeration uses

\[
\binom{n+R-1}{R}
\]

profiles at a fixed volume. A logarithmic observation index therefore does not imply a polynomial-time coefficient algorithm in the graph order. The rational coefficient also has substantial bit length: its unreduced denominator divides \(B^{(n-1+\lambda)R^2}\). The arithmetic decoder operates on that exact input. It does not turn approximate decimal measurements into exact denominator data, and its guarantee is not a robustness statement under measurement error.

Reproduction commands from the repository root are:

```sh
PYTHONPATH=src python -m unittest discover -s tests -p test_denominator_recovery.py -v
PYTHONPATH=src python scripts/fr02_denominator_recovery.py --check
```

The receipt is `results/fr02_denominator_recovery.json`. Re-running the script without `--check` regenerates it deterministically.

## 9. Follow-on questions without claiming their answers

The theorem naturally suggests asking which other extremal statistics can be recovered after rational specialization. Peeling the leading energy term from one coefficient is insufficient to recover a whole degree distribution: lower-energy nonsingle profiles overlap the contributions from lower-degree spikes, and subtraction must respect that interference. A valid next theorem would need a second isolation argument, rather than a repeated invocation of this one.

The coefficient's numerator is as important as its denominator. Denominator depth identifies the leading diagonal size up to cancellation by its multiplicity; the residue then removes the cancellation. This pattern may be useful for other finite lattice populations with an isolated extremal energy, provided one proves an explicit gap and a uniform bound on its leading multiplicity. That is a general method to investigate, not an already established extension to arbitrary interactions.

For the present fixed-pinning frontier, the immediate contribution is precise: any equal full pinned sequence at rational \(q\) and known order must preserve maximum degree and its multiplicity. Candidate searches can impose these two conditions before expensive coefficient comparisons. The complete-split family is reconstructible from the resulting arithmetic data. The larger questions of general completeness, a genuine full-series collision, and the realization of symmetric-interface ambiguities remain open.


# FR03 — Ordered tree kernels, positivity, and path witnesses

**Status.** Proved project specialization with exact finite checks. The Gaussian total-positivity mechanism and Cauchy–Binet composition are classical linear algebra; the contribution here is their precise application to this project's height kernel, the resulting path-distance coefficient, the all-order leading-minor hierarchy, and the truncation counterexample. This companion neither implements NX36 nor changes its proposed acceptance units.

## 1. Which object is positive?

Let $T=(V,E)$ be a finite connected tree, let $a,b\in V$ be distinct ordered terminals, and let $0<x,q<1$. Pin their heights to $s,t\in\mathbb Z_{\ge0}$. The ordered kernel is

\[
K_T(s,t;x,q)=
\sum_{h\in\mathbb Z_{\ge0}^{V\setminus\{a,b\}}}
 x^{\sum_{v\ne a,b}h_v}
 q^{\sum_{uv\in E}(h_u-h_v)^2},\qquad h_a=s,\ h_b=t.
\]

The terminals receive no factor of $x$. The kernel retains original labeled interior assignments. It is not a quotient by automorphisms. Every summand is nonnegative, and

\[
0<K_T(s,t;x,q)\le (1-x)^{-(|V|-2)}.
\]

The right side follows by dropping every energy factor, which is at most one. This gives absolute convergence without a height cutoff. For $H\ge0$, write $K_T^{[H]}$ when every interior vertex independently has height in $\{0,\ldots,H\}$. This is a Cartesian height box. It is a different object from keeping only profiles whose **sum** of interior heights is at most $R$.

A kernel is strictly totally positive when, for every $k\ge1$ and every pair of strictly increasing nonnegative integer pin lists $s_1<\cdots<s_k$ and $t_1<\cdots<t_k$,

\[
\det\bigl(K_T(s_i,t_j;x,q)\bigr)_{i,j=1}^k>0.
\]

The two pin lists need not be equal. The matrix need not be symmetric: a tree with an asymmetric terminal placement generally has $K_T(s,t)\ne K_T(t,s)$.

## 2. Gaussian edges are strictly totally positive

For one edge put

\[
G(r,c)=q^{(r-c)^2}
      =q^{r^2+c^2}\bigl(q^{-2r}\bigr)^c.
\]

For increasing rows $r_1<\cdots<r_k$, the numbers $z_i=q^{-2r_i}$ are strictly increasing and positive. Removing positive row and column factors reduces a Gaussian minor to

\[
\det(z_i^{c_j})_{i,j=1}^k,
\qquad 0<z_1<\cdots<z_k,\quad 0\le c_1<\cdots<c_k.
\]

Here is a direct proof of positivity, so the result does not depend on a numerical minor test. A nonzero real polynomial with $k$ nonzero monomials has at most $k-1$ distinct positive zeros. To see this, divide by its lowest power of $z$; differentiation removes its constant term and leaves at most $k-1$ monomials. Rolle's theorem and induction give the claim. If the displayed evaluation determinant vanished, a nonzero linear combination of its columns would give a polynomial with at most $k$ monomials and $k$ distinct positive zeros, a contradiction.

The determinant therefore never vanishes in the connected region of increasing positive nodes. Its sign is constant there. To determine that sign, bring the nodes together near $1$, writing $z_i=1+\varepsilon u_i$ with increasing $u_i$. Taylor expansion gives the first nonzero term

\[
\varepsilon^{k(k-1)/2}
\frac{\prod_{i<j}(u_j-u_i)\prod_{i<j}(c_j-c_i)}
     {\prod_{m=0}^{k-1}m!},
\]

which is positive. Thus every ordered Gaussian minor is positive.

This proof needs distinct row and column indices. Repeated pins give a zero determinant, as they should. Reversing one pin order changes the determinant sign and does not contradict positivity.

## 3. The tree factorization and the full positivity theorem

Let $p_0=a,p_1,\ldots,p_d=b$ be the unique terminal path, so $d\ge1$ is terminal distance. Delete its path edges. Every remaining component meets the path at exactly one vertex. Integrate the heights in these off-path components first. At each path vertex $p_i$, this produces a strictly positive branch factor $B_i(h)$. Internal path vertices additionally carry their factor $x^h$; the terminal vertices do not.

For a common finite box the factorization is

\[
K_T^{[H]}(s,t)=B_0^{[H]}(s)
\bigl[G D_1^{[H]}G D_2^{[H]}\cdots
G D_{d-1}^{[H]}G\bigr]_{s,t}
B_d^{[H]}(t),
\]

where each intermediate Gaussian index ranges from $0$ to $H$, and

\[
D_i^{[H]}(h,h)=x^h B_i^{[H]}(h)>0.
\]

When the terminals are adjacent, the bracket is simply $G(s,t)$. Positive endpoint factors preserve signs of all minors. Cauchy–Binet expands every minor of a product as a sum of products of minors, and every term in this expansion is positive whenever the intermediate index sets have the required size.

**Theorem FR03-A (box and full strict positivity).** If $d\ge2$, every ordered minor of $K_T^{[H]}$ of size $k\le H+1$ is strictly positive. If $k>H+1$, its rank is at most $H+1$, so all such larger minors vanish. If $d=1$, the boxed kernel is strictly totally positive at every order because there is no intermediate path-index bottleneck. In all cases the complete analytic kernel $K_T$ is strictly totally positive at every finite order.

For the last statement, the entries of $K_T^{[H]}$ increase to those of $K_T$, and convergence of entries gives convergence of each finite determinant. A limit of positive determinants need only be nonnegative in general, so one additional argument is essential. Fix the intermediate index set $\{0,\ldots,k-1\}$ at every internal path vertex in one Cauchy–Binet term. For every $H\ge k-1$, that term is present. Its branch factors have strictly positive lower bounds obtained by assigning zero to all off-path interior heights. Its Gaussian minors and powers of $x$ are fixed and strictly positive. This single term supplies a uniform positive lower bound for the full determinant. Its limit is therefore strictly positive.

This is a structural necessary condition for ordered tree kernels. It is not a sufficient characterization of trees, and this note does not classify all matrices satisfying it.

## 4. The first determinant coefficient measures terminal geometry

Write

\[
c=\sum_{v\in\{p_0,\ldots,p_d\}}\deg_T(v)-2d.
\]

Each of the $d$ path edges contributes twice to the degree sum. Thus $c\ge0$ counts precisely the edges leaving the terminal path. It counts attachment edges, not all edges deeper inside the pendant branches.

For $k\ge1$, take the principal pin minor

\[
\Delta_k(x,q)=\det\bigl(K_T(i,j;x,q)\bigr)_{i,j=0}^{k-1},
\quad S_k=\frac{k(k-1)}2,
\quad Q_k=\frac{k(k-1)(2k-1)}6.
\]

**Theorem FR03-B (all-order leading-minor hierarchy).** The exact first term is

\[
\boxed{
\Delta_k(x,q)=
x^{(d-1)S_k}q^{cQ_k}
\left[\prod_{r=1}^{k-1}(1-q^{2r})^{k-r}\right]^d
+O\!\left(x^{(d-1)S_k+1}\right).
}
\]

The coefficient in the box is strictly positive for every real $q\in(0,1)$. Consequently the displayed volume is an exact first nonzero degree, not just a lower bound.

To prove this, apply exterior Cauchy–Binet to the path factorization as a formal series in $x$. Every internal index set of size $k$ consists of distinct nonnegative integers and has sum at least $S_k$. Equality holds for the unique set $I=\{0,\ldots,k-1\}$. There are $d-1$ internal path vertices, so the first possible degree is $(d-1)S_k$, and at that degree there is one choice at every vertex. All off-path interior heights must be zero at this first degree. A branch edge incident to a path vertex of pin height $i$ then contributes $q^{i^2}$; multiplying over the selected indices and attachment edges yields $q^{cQ_k}$.

The remaining factor is one Gaussian principal minor per path edge. Its determinant is explicit:

\[
\det(q^{(i-j)^2})_{i,j=0}^{k-1}
=\prod_{r=1}^{k-1}(1-q^{2r})^{k-r}.
\]

Indeed, extract $q^{i^2}$ from each row and $q^{j^2}$ from each column, then use the ordinary Vandermonde determinant on $q^{-2i}$. The negative powers contributed by the Vandermonde cancel the extracted powers exactly. This proves the formula.

The formal Cauchy–Binet argument is legitimate coefficient by coefficient: to compute through a fixed degree $R$, any interior height above $R$ is irrelevant. One can therefore first use a finite box $H\ge R$, prove the finite identity, and extract the desired coefficient.

The order-two case is particularly readable:

\[
\boxed{
K_T(0,0)K_T(1,1)-K_T(0,1)K_T(1,0)
=x^{d-1}q^c(1-q^2)^d+O(x^d).
}
\]

Thus the first nonzero volume recovers $d$. Once $d$ is known, dividing the leading coefficient by $(1-q^2)^d$ gives $q^c$, which uniquely determines the nonnegative integer $c$ at any fixed $q\in(0,1)$. This recovers terminal distance and the number of branches incident to the terminal path. It does not recover the shapes of those branches or the entire tree.

| Minor order | First nonzero volume | Leading coefficient |
|---|---:|---|
| $k=1$ | $0$ | $1$ |
| $k=2$ | $d-1$ | $q^c(1-q^2)^d$ |
| $k=3$ | $3(d-1)$ | $q^{5c}[(1-q^2)^2(1-q^4)]^d$ |
| $k=4$ | $6(d-1)$ | $q^{14c}[(1-q^2)^3(1-q^4)^2(1-q^6)]^d$ |

The higher minors provide redundant structural consistency checks rather than independent reconstruction of additional path statistics at leading order. Their later coefficients can contain branch information; that inverse problem is left open.

## 5. A volume cutoff can manufacture a negative determinant

Consider the four-vertex path $a-u-v-b$. Retain only interior profiles $h_u+h_v\le1$. The resulting polynomial kernel is

\[
K_{\le1}(s,t)=q^{s^2+t^2}
\bigl[1+xq^2(q^{-2s}+q^{-2t})\bigr].
\]

Its determinant on pins $0,1$ is

\[
\boxed{\det(K_{\le1}(s,t))_{s,t=0,1}
=-x^2q^2(1-q^2)^2<0.}
\]

This is an actual tree, so a negative determinant of a volume-truncated kernel cannot reject tree realizability. The cutoff couples $u$ and $v$; it is not a product domain and does not retain the matrix-product factorization used in the positivity proof.

There is no contradiction with the leading-minor theorem. The true tree has $d=3,c=0$, and its full determinant starts with

\[
x^2(1-q^2)^3.
\]

Computing a determinant coefficient at degree two requires each entry through degree two. Entry data only through degree one determine determinant coefficients through degree one; degree-two terms obtained by taking their ordinary determinant can be wrong because omitted degree-two entries multiply nonzero constant entries.

| Available object | Valid conclusion |
|---|---|
| Complete ordered analytic kernel, $0<x,q<1$ | All ordered finite minors are positive |
| Common interior height box $0,\ldots,H$ | Positive minors through order $H+1$; larger minors vanish if there is an internal path vertex |
| Ordered kernel entry coefficients through volume $R$ | Determinant coefficients are valid only through volume $R$ |
| Ordinary determinant of a volume-truncated kernel evaluated at $x>0$ | No general positivity guarantee |
| Symmetrized interface $K(s,t)+K(t,s)$ | This note establishes no total-positivity rule for it |

## 6. Implementation and exact evidence

`src/singularity/tree_positivity.py` provides an exact rational box evaluator. It integrates off-path subtrees by iterative messages and contracts the unique terminal path. Rational $x,q$ must lie strictly between zero and one; floats and booleans are rejected. A conservative preflight scalar-summand budget prevents silently launching a large box contraction. This budget is not a bound on integer bit complexity: very large pin heights or rational denominators can still make individual arithmetic operations expensive.

The structural helpers return the terminal path, distance, off-path attachment count and exact first minor coefficient. The order-$k$ helper has an explicit declared work bound of $k\le256$. It does not compute an infinite sum or pretend that the formula determines later coefficients.

The tests compare the box evaluator with direct enumeration over every interior assignment, including asymmetric terminals, terminal pins above the interior box, and nontrivial pendant branches. Ordered minors of sizes one, two and three are evaluated exactly. Independent weak-composition enumeration checks the distance coefficient on every terminal pair of every labeled tree through four vertices. Additional tests check higher leading minors at orders three and four and the negative volume-cutoff example.

The retained receipt extends the order-two leading-term check to all labeled trees through five vertices and all unordered terminal pairs, with the ordering fixed by the original labels. It records the exact finite population and does not interpret it as a proof for arbitrary trees; the proof above supplies that theorem. No graph census or surviving symmetric-ambiguity search is performed.

## 7. What this contributes to the remaining frontier

These results add a nonlinear necessary condition and a geometry decoder for an important class of realizable **ordered** interfaces. They can accompany a future candidate search by filtering an ordered tree completion, provided that the data include enough volume and the test respects the stated kernel semantics. They cannot directly eliminate a candidate living only in a symmetrized interface: averaging a matrix with its transpose does not follow from the path factorization, and no preservation theorem for that averaging is proved here.

The natural next problems are to decode pendant-branch statistics from subsequent determinant coefficients, understand which analogous sign constraints survive on unicyclic graphs, and determine which ordered positivity constraints descend to symmetrized data under additional terminal symmetries. None of these is counted as an implemented NX36 unit, a full-series collision, or a complete reconstruction theorem for arbitrary pinned graphs.


# FR04 — What the far coefficients remember under fixed positive pinning

**Companion status:** proved necessary invariants and exact small-instance
certificates. This document does not prove completeness of fixed pinning and
does not exhibit a full-series collision. It is independent of the NX36
implementation packets. The graph may be connected or disconnected; positive
pinning makes the quadratic form coercive in either case.

## 1. The question and the change of scale

Let \(G\) be a finite simple graph with \(n\ge1\) labeled vertices, let
\(\lambda\) be a fixed positive integer, and fix \(0<q<1\). Write

\[
 A_{G,R}^{(\lambda)}(q)
 =\sum_{\substack{h\in\mathbb Z_{\ge0}^{n}\\\sum_i h_i=R}}
 q^{E_G(h)+\lambda\sum_i h_i^2},
 \qquad
 E_G(h)=\sum_{\{u,v\}\in E(G)}(h_u-h_v)^2.
\]

For the dominating-terminal interface already used in the project, the
relevant pinning is \(\lambda=2\). These are coefficients of the raw
nonnegative-height series. No minimum-height normalization is applied and no
multiplicity is divided by an automorphism-group order.

A large volume forces a large common mean height. The pinning alone charges
approximately \(\lambda R^2/n\) for that mean, while graph energy is unchanged
by common translation. Consequently the original coefficients become very
small even when their fluctuations retain substantial structure. The right
object is the rescaled coefficient

\[
 S_{G,R}(q)=q^{-\lambda R^2/n}A_{G,R}^{(\lambda)}(q).
\]

The rescaled sequence does not ordinarily have a single limit. There are
\(n\) residue classes, because an integer height vector cannot be translated
by a nonintegral common height. Each residue class has its own affine lattice
of fluctuations, its own limiting theta value, and an explicit boundary error.

| Object | Definition | Information retained |
|---|---|---|
| Pinned coefficient | \(A_{G,R}^{(\lambda)}(q)\) | All nonnegative profiles at one volume |
| Gaussian scale | \(q^{\lambda R^2/n}\) | Graph order when \(\lambda,q\) are known |
| Centered coefficient | \(S_{G,R}=q^{-\lambda R^2/n}A_{G,R}\) | Fluctuations subject to the nonnegative boundary |
| Affine lattice | \(\Lambda_r=\{z-r\mathbf1/n:z\in\mathbb Z^n,\sum z_i=r\}\) | Integer fluctuations for \(R\equiv r\pmod n\) |
| Theta limit | \(\Theta_{G,r}=\sum_{y\in\Lambda_r}q^{y^{\mathsf T}(L_G+\lambda I)y}\) | Necessary full-series invariant after the boundary recedes |
| Boundary deficit | \(\epsilon_{G,R}=\Theta_{G,r}-S_{G,R}\) | Positive information omitted by the limiting invariant |

## 2. Order is already an intrinsic full-series invariant

**Theorem FR04.1 (quadratic coefficient decay).** For every \(R\ge0\),

\[
 q^{\lambda R^2/n+|E(G)|+\lambda n/4}
 \le A_{G,R}^{(\lambda)}(q)
 \le \binom{R+n-1}{n-1}q^{\lambda R^2/n}.
 \tag{1}
\]

In particular,

\[
 \boxed{\displaystyle
 \lim_{R\to\infty}\frac{\log A_{G,R}^{(\lambda)}(q)}{R^2}
 =\frac{\lambda}{n}\log q.}
 \tag{2}
\]

Thus equality of the complete pinned series at the same known
\(\lambda>0\) and \(q\in(0,1)\) forces equal graph order.

**Proof.** Cauchy–Schwarz gives \(\sum_i h_i^2\ge R^2/n\), and graph energy is
nonnegative. Every summand is therefore at most \(q^{\lambda R^2/n}\).
There are exactly \(\binom{R+n-1}{n-1}\) labeled weak compositions of \(R\),
which proves the upper bound.

For the lower bound, put \(R=kn+r\), where \(0\le r<n\), and choose one
profile with \(r\) coordinates equal to \(k+1\) and the rest equal to \(k\).
Every edge contributes either zero or one, so its graph energy is at most
\(|E(G)|\). Its squared norm is

\[
 (n-r)k^2+r(k+1)^2
 =R^2/n+r(n-r)/n
 \le R^2/n+n/4.
\]

Its single positive summand proves the lower bound. Taking logarithms of
(1), dividing by \(R^2\), and using
\(\log\binom{R+n-1}{n-1}=O_n(\log R)\) proves (2). The number
\(\lambda\log q\) is nonzero, so its quotient by the limit determines \(n\).
This last statement is a full-series assertion. It does not supply a universal
finite-volume procedure for reading the limit from an arbitrary prefix. ∎

The theorem has a useful methodological consequence. A completeness question
formulated for the full pinned series need not assume graph order is externally
provided: the complete series contains it. An algorithm using only finitely
many coefficients must still declare how it knows or bounds the order.

## 3. The centered lattice and the exact boundary decomposition

Let \(L_G\) be the graph Laplacian and set

\[
 C_G=L_G+\lambda I.
\]

Since \(L_G\mathbf1=0\) and \(\lambda>0\),

\[
 C_G\mathbf1=\lambda\mathbf1,
 \qquad C_G\succeq\lambda I>0.
\]

For \(R=kn+r\), translate each profile by the integer common height \(k\):

\[
 z=h-k\mathbf1,
 \quad \sum_i z_i=r,
 \quad z_i\ge-k.
\]

Its centered version is

\[
 y=z-\frac r n\mathbf1=h-\frac Rn\mathbf1\in\Lambda_r.
\]

The cross term vanishes because \(\sum_i y_i=0\). Hence the exact identity is

\[
 \boxed{E_G(h)+\lambda\|h\|^2
 =\lambda R^2/n+y^{\mathsf T}C_Gy.}
 \tag{3}
\]

The nonnegative-height condition becomes a moving orthant boundary:

\[
 h_i\ge0\quad\Longleftrightarrow\quad y_i\ge-R/n.
\]

Define the complete affine-root-lattice theta value

\[
 \Theta_{G,r}^{(\lambda)}(q)
 =\sum_{y\in\Lambda_r}q^{y^{\mathsf T}C_Gy}.
 \tag{4}
\]

This is a scalar evaluated at the declared fixed parameter. It is not being
identified with the theta series as a formal function of \(q\). All sums
converge absolutely: positive definiteness bounds them by products of
one-dimensional Gaussian sums.

**Theorem FR04.2 (residue-class limits).** For \(R=kn+r\),

\[
 S_{G,R}(q)
 =\sum_{\substack{y\in\Lambda_r\\y_i\ge-R/n\ \forall i}}
 q^{y^{\mathsf T}C_Gy}
 \nearrow \Theta_{G,r}^{(\lambda)}(q)
 \qquad(k\to\infty).
 \tag{5}
\]

For \(n\ge2\) every increase \(R\mapsto R+n\) is strict. For \(n=1\), the
rescaled coefficients and the unique theta limit are identically one.
Furthermore,

\[
 \boxed{\Theta_{G,r}^{(\lambda)}(q)
 =\Theta_{G,n-r}^{(\lambda)}(q),\qquad 1\le r<n.}
 \tag{6}
\]

Consequently there are at most \(\lfloor n/2\rfloor+1\) distinct limiting
values after reflection.

**Proof.** Formula (3) gives (5) at every finite \(R\). Along one residue
class the affine lattice is fixed and the lower coordinate threshold drops
by one each time. The domains are nested and exhaust the entire lattice.
All summands are positive, so monotone convergence proves the limit. When
\(n\ge2\), there are lattice vectors with one coordinate exactly equal to
the newly admitted lower height, and the remaining coordinates can be chosen
to have the required sum. At least one positive summand is therefore added.
For \(n=1\), \(y=0\) is the only lattice vector.

Reflection \(y\mapsto-y\) preserves the quadratic form. If
\(y=z-r\mathbf1/n\), then

\[
 -y=(\mathbf1-z)-(n-r)\mathbf1/n,
 \quad \sum_i(1-z_i)=n-r.
\]

It maps \(\Lambda_r\) bijectively to \(\Lambda_{n-r}\), proving (6). ∎

## 4. A Gaussian error bound with all constants visible

Put

\[
 T_{n,r}(q)=\sum_{z\in\mathbb Z}q^{\lambda(z-r/n)^2},
 \qquad a_R=R/n+1.
\]

**Theorem FR04.3 (boundary correction).** With \(r=R\bmod n\),

\[
 0\le\epsilon_{G,R}
 :=\Theta_{G,r}^{(\lambda)}(q)-S_{G,R}(q)
 \le nT_{n,r}(q)^{n-1}
 \frac{q^{\lambda a_R^2}}
 {1-q^{\lambda(2a_R+1)}}.
 \tag{7}
\]

The error is identically zero for \(n=1\). For \(n\ge2\), it is positive at
every finite \(R\). The formula deliberately drops graph energy and the sum
constraint when bounding omitted vectors, so it is conservative.

**Proof.** An omitted vector has at least one coordinate
\(y_i<-R/n\). On the shifted integer lattice the first such value is exactly
\(-R/n-1\), followed by \(-R/n-2,\ldots\). Since
\(y^{\mathsf T}C_Gy\ge\lambda\sum_i y_i^2\), a union bound over the chosen
bad coordinate, followed by removal of the zero-sum constraint, gives

\[
 \epsilon_{G,R}
 \le nT_{n,r}(q)^{n-1}
 \sum_{m\ge0}q^{\lambda(a_R+m)^2}.
\]

Successive exponents differ by \(\lambda(2a_R+2m+1)\), which is at least
\(\lambda(2a_R+1)\). The tail is bounded by a geometric series with the
first term and largest successive ratio shown in (7). ∎

Combining the exact decomposition with positivity of the theta limit gives

\[
 A_{G,R}^{(\lambda)}(q)
 =q^{\lambda R^2/n}
 \left(\Theta_{G,r}^{(\lambda)}(q)-\epsilon_{G,R}\right),
 \tag{8}
\]

\[
 \log A_{G,R}^{(\lambda)}(q)
 =\frac{\lambda R^2}{n}\log q
 +\log\Theta_{G,r}^{(\lambda)}(q)+o(1)
 \quad(R\equiv r\pmod n).
 \tag{9}
\]

There is a quadratic scale, a bounded residue-dependent term, and a Gaussian
boundary correction. A further consequence along a residue class is

\[
 \frac{A_{G,R+n}^{(\lambda)}(q)}{A_{G,R}^{(\lambda)}(q)}
 q^{-\lambda(2R+n)}\longrightarrow1.
 \tag{10}
\]

These are asymptotic structural identities, not claims that finitely many
nearby coefficients certify full-series equality.

## 5. Exact arithmetic without pretending fractional powers are rational

Even for rational \(q\), the scaling factor \(q^{-\lambda R^2/n}\) need not
be rational. An implementation must not silently replace such algebraic
numbers by rounded floats and call the result an exact certificate.

The centered-theta APIs first choose a transparent exact sector:

\[
 t\in\mathbb Q\cap(0,1),\qquad q=t^{n^2}.
 \tag{11}
\]

Write \(w_i=nz_i-r\). The centered exponent is now

\[
 q^{y^{\mathsf T}C_Gy}
 =t^{\,n^2E_G(z)+\lambda\sum_i(nz_i-r)^2},
 \tag{12}
\]

an integer power of a rational number. Equivalently,

\[
 S_{G,R}(t^{n^2})
 =t^{-n\lambda R^2}A_{G,R}^{(\lambda)}(t^{n^2}).
\]

The exponent in each centered summand is nonnegative. Thus every finite sum,
interval endpoint, and error bound in the checker is an exact `Fraction`.
This arithmetic restriction belongs to these centered-theta APIs, while
Theorems FR04.1–FR04.3 hold for every real \(0<q<1\). The affine-lift APIs
below remove the restriction and work at every rational parameter.

For any positive integer \(b\), define the rational tail bound

\[
 U(b)=\frac{t^{\lambda b^2}}
 {1-t^{\lambda(2bn+n^2)}}
 \ge\sum_{m\ge0}t^{\lambda(b+nm)^2}.
 \tag{13}
\]

For a declared integer half-width \(H\ge0\), put

\[
 T^{\mathrm{up}}_{n,r,H}
 =\sum_{z=-H}^{H+1}t^{\lambda(nz-r)^2}
 +U(n(H+2)-r)+U(n(H+1)+r).
 \tag{14}
\]

This bounds the complete one-coordinate Gaussian. The asymmetric finite
window \([-H,H+1]\) is intentional: the reflection
\(z\mapsto1-z\) preserves it for the pair \(r,n-r\). In particular the two
finite theta lower sums agree exactly, not merely approximately.

Two independent enclosures are implemented:

| Route | Exact lower endpoint | Certified upper-minus-lower |
|---|---|---|
| One coefficient | \(S_{G,R}(t^{n^2})\) | \(n(T^{\mathrm{up}}_{n,r,H})^{n-1}U(R+n)\) |
| Lattice window | Sum (12) over \(\sum z_i=r\), \(-H\le z_i\le H+1\) | \(n(T^{\mathrm{up}}_{n,r,H})^{n-1}[U(n(H+2)-r)+U(n(H+1)+r)]\) |

The first route sums nonnegative profiles at one volume. The second sums
signed profiles in an affine lattice window. Their certified intervals must
overlap, and their finite sums come from different domains. The checker uses
this relation alongside an independent product-box coefficient oracle.

The window enumeration determines the last coordinate from the first
\(n-1\), so it visits at most \((2H+2)^{n-1}\) candidate prefixes. The
coefficient route visits \(\binom{R+n-1}{n-1}\) profiles. Both APIs reject a
request exceeding the caller's declared state budget before enumerating.
Neither route is advertised as a large-graph compiler.

### 5.1 Exact affine lifts at the working parameter \(q=1/2\)

A graph-independent change of coordinates also makes the complete calculation
rational at every rational \(q\in(0,1)\). Retain the residue-dependent scale
instead of extracting its fractional power. Define

\[
 \Psi_{G,r}^{(\lambda)}(q)
 =\sum_{\substack{z\in\mathbb Z^n\\\sum_i z_i=r}}
 q^{E_G(z)+\lambda\sum_i z_i^2}
 =q^{\lambda r^2/n}\Theta_{G,r}^{(\lambda)}(q).
 \tag{16}
\]

This scale depends on \(n,r,\lambda,q\), but not on the graph edges. It
therefore preserves all comparisons between graphs of the same order. For
\(R=kn+r\), the exact increasing approximation is

\[
 P_{G,R}(q)
 :=q^{-\lambda(nk^2+2kr)}A_{G,R}^{(\lambda)}(q)
 =\sum_{\substack{z\in\mathbb Z^n,\ \sum_i z_i=r\\z_i\ge-k}}
 q^{E_G(z)+\lambda\sum_i z_i^2}
 \nearrow\Psi_{G,r}^{(\lambda)}(q).
 \tag{17}
\]

Every exponent in the sum is a nonnegative integer. Every normalization
exponent is an integer. Exact arithmetic at \(q=1/2\), or any other rational
parameter, needs neither algebraic-number support nor an approximation to an
\(n\)-th root. The original centered-theta APIs remain useful for expressing
the intrinsic Gaussian scale, while the affine-lift APIs are the natural
implementation for exact fixed-rational experiments.

Reflection now includes its scale factor:

\[
 \boxed{\Psi_{G,n-r}^{(\lambda)}(q)
 =q^{\lambda(n-2r)}\Psi_{G,r}^{(\lambda)}(q),\qquad1\le r<n.}
 \tag{18}
\]

This follows directly from \(z\mapsto\mathbf1-z\): graph energy is unchanged,
and \(\|\mathbf1-z\|^2=\|z\|^2+n-2r\).

Let

\[
 T(q)=\sum_{z\in\mathbb Z}q^{\lambda z^2},
 \qquad
 V(b)=\frac{q^{\lambda b^2}}{1-q^{\lambda(2b+1)}}
 \quad(b\ge1).
\]

The same geometric-tail proof gives

\[
 0\le\Psi_{G,r}(q)-P_{G,R}(q)
 \le nT(q)^{n-1}V(k+1).
 \tag{19}
\]

For an exact rational upper bound, use

\[
 T^{\mathrm{up}}_H(q)
 =\sum_{z=-H}^{H+1}q^{\lambda z^2}+V(H+2)+V(H+1).
 \tag{20}
\]

A signed-lattice window with \(-H\le z_i\le H+1\) and \(\sum z_i=r\)
therefore has omitted mass at most

\[
 n\bigl(T^{\mathrm{up}}_H(q)\bigr)^{n-1}
 \bigl(V(H+2)+V(H+1)\bigr).
 \tag{21}
\]

These bounds drop both the graph energy and the sum constraint after selecting
an omitted coordinate. They are intentionally conservative, but every endpoint
is rational. `affine_lift_enclosure` implements the lattice window;
`affine_boundary_enclosure` implements the one-coefficient approximation.
The retained receipt checks their intersection for every residue at
\(q=1/2\), verifies (18) exactly, and obtains disjoint intervals for the
three-vertex path and the disconnected three-vertex single-edge graph. Thus
the method supplies a valid full-series inequivalence certificate at the
project's working parameter, without requiring connectedness of the candidates.

## 6. What this contributes to the fixed-pinning frontier

If two graphs have equal complete pinned series at the same \(\lambda,q\),
Theorem FR04.1 forces equal order, and Theorem FR04.2 forces equality of every
residue-class theta limit. This gives a hierarchy of necessary conditions:

\[
 \begin{aligned}
 \text{full equality}&\Longrightarrow (n_G=n_H,\ \Theta_{G,r}=\Theta_{H,r}\ \forall r),\\
 &\Longrightarrow \text{equal quadratic decay rate}.
 \end{aligned}
 \tag{15}
\]

No converse arrow is asserted. Passing from the full coefficients to the theta
limits removes the moving nonnegative boundary. Equation (8) displays exactly
what was removed: the entire sequence of boundary deficits. Equal limiting
values do not, by themselves, force those deficits to agree. A prefix
collision does not establish equality of the limits, and equality of limits
does not establish a full-series collision.

This distinction gives the next structural question a precise form. A genuine
full-series collision must match both the centered bulk theta data and every
boundary correction. A completeness proof could instead explain why matching
all these corrections forces a graph isomorphism. The present result supplies
the decomposition and certified access to its limiting part; it proves neither
of those further statements.

A practical use is one-sided rejection. Suppose two candidate graphs have the
same order and fixed pinning. If exact theta enclosures for one residue are
disjoint, their theta limits differ, so their complete pinned series differ.
That is a valid full-series inequivalence certificate even when an earlier
finite prefix agreed. The converse remains one-sided: overlapping intervals
merely mean that this computation has not separated the candidates.

## 7. API and acceptance evidence

| API in `singularity.pinned_theta` | Contract |
|---|---|
| `pinned_coefficient(G,R,lambda,q)` | Exact raw coefficient at rational \(q\), with a composition-count budget |
| `scaled_pinned_coefficient(G,R,lambda,t)` | Exact centered coefficient for \(q=t^{n^2}\) |
| `theta_enclosure(G,lambda,t,r,H)` | Rational interval for the complete affine theta limit |
| `boundary_enclosure(G,R,lambda,t)` | Rational interval for that same theta limit from one coefficient |
| `affine_lift_enclosure(G,lambda,q,r,H)` | Exact rational interval for \(\Psi_{G,r}(q)\), for every rational \(q\) |
| `affine_boundary_enclosure(G,R,lambda,q)` | Exact interval for \(\Psi_{G,r}(q)\) from one translated coefficient |
| `coefficient_decay_bounds(G,R,lambda,t)` | Exact lower and upper bounds underlying the order invariant |
| `RationalEnclosure` | Inclusive rational endpoints, exact width, retained-term count |

Tests check raw coefficients against an independent product-box enumeration;
integer centering against explicit multiplication by the scaling factor;
strictly increasing residue subsequences; intersection of the coefficient and
lattice enclosures; reflection; nested lattice windows; the one-vertex edge
case; relabeling; decay inequalities; exact-input validation; and rejection
before over-budget enumeration. No floating-point approximation participates
in the certificates.

The retained receipt is `results/fr04_pinned_theta.json`. Reproduce it with:

```bash
PYTHONPATH=src python scripts/fr04_pinned_theta.py --check
```

The scope remains intentionally narrow: fixed known positive pinning, fixed
positive parameter, raw nonnegative-height populations, and necessary
full-series invariants. Finite-prefix agreement remains separate from the
full-series questions motivating this companion.


# Independent mathematical review of the frontier companion

This review separates mathematical consequences of complete generating series from evidence obtained from a finite coefficient prefix. It does not certify either fixed-pinning completeness or the realization of a surviving symmetric-interface ambiguity.

## FR01: connected pole divisors

**Verdict: sound, subject to the stated connectedness and positive-parameter hypotheses.** Let \(G\) be connected of order \(n\), \(0<q<1\), and \(B_G=(1-x^n)L_G\). The previously established entire continuation of \(B_G\) is used, rather than asserted as a new result. At \(\zeta^n=1\), translation classes of integral heights can be represented either by their minimum-zero representative or by an anchored representative \(u\in\mathbb Z^{n-1}\). The volume phase is independent of the representative because translation changes volume by a multiple of \(n\). Therefore

\[
 B_G(\zeta,q)=\sum_{u\in\mathbb Z^{n-1}}
 \exp(-\beta u^TQ u)\exp(2\pi i\alpha^Tu),\qquad \beta=-\log q>0,
\]

where \(Q\) is the positive-definite reduced graph Laplacian and \(\alpha=(k/n)\mathbf1\) when \(\zeta=e^{2\pi i k/n}\). Poisson summation gives

\[
 B_G(\zeta,q)=\frac{(\pi/\beta)^{(n-1)/2}}{\sqrt{\det Q}}
 \sum_{m\in\mathbb Z^{n-1}}
 \exp\!\left[-\frac{\pi^2}{\beta}(m-\alpha)^TQ^{-1}(m-\alpha)\right]>0.
\]

The absolute convergence and strict positivity are immediate from positive definiteness. Consequently every \(n\)-th root is a genuine simple pole of \(L_G\), with residue \(-\zeta B_G(\zeta,q)/n\). Order one is covered by \(B_G=1\).

**The disconnected caveat is essential.** A different component numerator might vanish at a root that is not one of its own denominator roots. A sum of denominator pole orders is therefore not established at unrestricted positive \(q\). The implementation correctly refuses the general claim. The same-size component case is safe, including arbitrary isolated vertices, because every nontrivial component has the same denominator-root set and every isolated numerator is one.

The uniform zero-free certificate is sound: a spanning-tree difference parametrization gives

\[
 \sup_{|x|\le1}|B_H(x,q)-1|
 \le \vartheta(q)^{|H|-1}-1,
 \quad \vartheta(q)=\sum_{z\in\mathbb Z}q^{z^2}.
\]

Thus any rigorous upper bound \(U\ge\vartheta(q)\) with \(U^{N-1}<2\) excludes all unit-disc numerator zeros for all connected components of order at most \(N\). The scalar theta tail bound used in the code follows from successive exponent increments at least \(2T+3\) beyond index \(T+1\). Gaussian-box errors likewise dominate omitted spanning-tree difference assignments. Cyclotomic coefficient vectors are exact partial sums; their absolute-error bound concerns evaluation on the complex unit circle, not a coordinatewise positivity assertion.

## FR02: denominator reconstruction

**Verdict: sound, including composite denominator bases and uniform pinning.** For \(q=A/B\) in reduced form, \(0<A<B\), diagonal shift \(\lambda\ge0\) an integer, and \(\Lambda=\Delta+\lambda>0\), the maximum energy at volume \(R\ge2\) is

\[
 K=\Lambda R^2,
\]

achieved precisely by spikes on the \(m\) maximum-degree vertices. Every other profile has energy at most \(K-g\), with the valid universal gap

\[
 g=\min\{R^2,\,2\Lambda(R-1)\}.
\]

The minimum is necessary: a spike at a lower-degree vertex has gap only \(R^2\), which need not exceed \(2\Lambda(R-1)\). Non-spikes are bounded using \(E_G(h)+\lambda\sum h_i^2\le\Lambda\sum h_i^2\) and \(\sum h_i^2\le(R-1)^2+1\).

With \(B^{2(R-1)}>n\), we have \(B^g>n\ge m\), so

\[
 B^K a_R=mA^K+B^gT,\qquad T\in\mathbb Z.
\]

If \(\operatorname{ord}_B(m)=\max\{e:B^e\mid m\}\), then the least denominator-clearing depth \(k\) of \(a_R\) is exactly \(K-\operatorname{ord}_B(m)\). This does **not** require \(B\) to be prime. Prime-by-prime, it is the identity

\[
 \max_{p\mid B}\left\lceil\frac{K v_p(B)-v_p(m)}{v_p(B)}\right\rceil
 =K-\min_{p\mid B}\left\lfloor\frac{v_p(m)}{v_p(B)}\right\rfloor.
\]

Because \(\operatorname{ord}_B(m)<R^2\), the decoder recovers

\[
 \Delta=\left\lceil\frac{k}{R^2}\right\rceil-\lambda,
 \qquad
 m\equiv B^K a_R\,A^{-K}\pmod{B^g},\quad 1\le m\le n<B^g.
\]

The residue therefore determines \(m\) uniquely. The unpinned edgeless case \(\Lambda=0\) has integer coefficient equal to the number of compositions and must be treated separately; the implementation does so. Pinned edgeless graphs with \(\lambda=2\) instead have \(\Lambda=2,m=n\), and are handled by the general branch.

An independent implementation, written directly from compositions and graph edge energies rather than the new decoder, checked **450 exact cases**: every labeled graph of orders one through four, \(q=1/2,2/3,5/6\), and shifts zero and two. Every recovered maximum degree and multiplicity agreed. This is finite corroboration of the theorem, not a substitute for the gap proof.

The new module's input validation and the gcd-based composite-base clearing procedure were inspected. The caller supplies graph order, family membership where used, and the actual coefficient; the decoder does not prove coefficient realizability. A logarithmic observation volume does not imply a cheap oracle for computing that coefficient.

## FR03: ordered tree positivity and distance

**Verdict: sound for the full ordered kernel and for product height boxes, with explicit failure under a simplex volume truncation.** For a tree, integrate every off-path branch into positive diagonal messages. The remaining terminal path is a product of Gaussian edge kernels and positive diagonal weights. The Gaussian factor is

\[
 q^{(s-t)^2}=q^{s^2}q^{t^2}\exp(2\beta st),\qquad \beta=-\log q>0.
\]

The exponential kernel is strictly totally positive. Cauchy–Binet preserves positivity under finite products with positive diagonals. A common box \(0\le h_v\le H\) has positive minors of order at most \(H+1\) when an internal path vertex exists. Increasing \(H\) gives the full kernel for \(0<x,q<1\); strict positivity persists because a fixed positive intermediate-index contribution supplies a uniform positive lower bound. Absolute convergence follows from domination by \((1-x)^{-(n-2)}\).

For consecutive terminal pins \(0,\ldots,k-1\), let \(d\) be terminal distance, \(c\) the number of edges leaving their unique path, \(S=k(k-1)/2\), and \(T=k(k-1)(2k-1)/6\). Exterior Cauchy–Binet has the unique minimum-volume intermediate index set \(\{0,\ldots,k-1\}\) at each internal path vertex. The Gaussian principal determinant is a Vandermonde product, giving the full hierarchy

\[
 \det[K(i,j)]_{i,j=0}^{k-1}
 =x^{(d-1)S}q^{cT}
 \left[\prod_{r=1}^{k-1}(1-q^{2r})^{k-r}\right]^d
 +O\!\left(x^{(d-1)S+1}\right).
\]

In particular the two-by-two determinant starts at volume \(d-1\), with coefficient \(q^c(1-q^2)^d\), so its first nonzero degree recovers terminal distance. Off-path contributions enter the leading coefficient only through the number of incident branch edges.

Two qualifications must remain explicit. First, an average of an ordered kernel and its transpose is not automatically totally positive, so this theorem is not directly a constraint on an arbitrary symmetrized interface. Second, global volume truncation can destroy positivity: for the four-vertex path truncated at interior volume one,

\[
 K_{\le1}(s,t)=q^{s^2+t^2}\{1+xq^2(q^{-2s}+q^{-2t})\},
\]

and its zero/one minor is \(-x^2q^2(1-q^2)^2<0\). This is a determinant of a truncated kernel, not the correctly truncated determinant of the full kernel. In particular its degree-two coefficient omits kernel degree-two contributions.

The path-message implementation was inspected. It preserves raw interior-volume weighting, leaves terminals unweighted by \(x\), and boxes every interior coordinate separately. Its preflight budget bounds scalar summands, not arbitrary-precision bit complexity.

## FR04: centered pinned theta limits

**Verdict on the mathematical statement: sound.** For a connected or disconnected finite graph, uniform real pinning \(\lambda>0\) makes \(L_G+\lambda I\) positive definite; connectedness is unnecessary. Write \(R=kn+r\), \(0\le r<n\), and \(z=h-k\mathbf1\). Then \(\sum z_i=r\), \(z_i\ge-k\), and

\[
 q^{-\lambda R^2/n}A_R
 =\sum_{\substack{z\in\mathbb Z^n,\ \sum z_i=r\\z_i\ge-k}}
 q^{E_G(z)+\lambda\sum_i(z_i-r/n)^2}.
\]

The summation domains increase with \(k\), so the normalized sequence converges monotonically to the affine root-lattice theta series on the sum-zero coset. Reflection gives residue symmetry \(r\leftrightarrow n-r\), using \(z\mapsto\mathbf1-z\) for \(r>0\) and \(z\mapsto-z\) for \(r=0\). Positive pinning controls Gaussian tails without a connectivity hypothesis.

Balanced profiles and the composition count give

\[
 q^{\lambda R^2/n+|E(G)|+\lambda n/4}
 \le A_R\le {R+n-1\choose n-1}q^{\lambda R^2/n},
 \qquad
 \lim_{R\to\infty}\frac{\log A_R}{R^2}=\frac{\lambda\log q}{n}.
\]

Thus the complete pinned series at known \(q,\lambda\) determines graph order, independently of a supplied order metadata field. Equality of the complete series implies equality of the affine theta limit packet; equality of the packet alone is not proved sufficient for complete-series equality. Exact rational arithmetic with \(q=t^{n^2}\) gives integral exponents when \(\lambda\) is an integer; arbitrary positive real \(\lambda\) is a theorem-level parameter, not automatically an exact-rational runtime input.

The FR04 implementation was independently inspected after it became available. Its reflection-friendly box \([-H,H+1]\) has the correct positive and negative first omitted Gaussian indices; the boundary enclosure uses the exact first omitted centered magnitude \(R+n\). Twenty-eight additional exact cross-checks on connected and disconnected graphs verified box nesting against a larger direct lattice window and checked subsequent residue-subsequence values against the boundary enclosure. All 32 then-current unit tests across FR01–FR04 passed with the source package on the Python path. These checks concern exact arithmetic and enclosure containment, not an empirical proof of the limiting theorem.

### FR04 rational affine lift at the working parameter

The additional affine-lift APIs remove any need to choose a special rational parameter. For every rational \(0<q<1\) and integer pinning \(\lambda>0\), define

\[
 \Psi_r(q)=\sum_{\substack{z\in\mathbb Z^n\\\sum z_i=r}}
 q^{E_G(z)+\lambda\|z\|^2}
 =q^{\lambda r^2/n}\Theta_r(q).
\]

For \(R=kn+r\), the exact rational normalized coefficient satisfies

\[
 q^{-\lambda(nk^2+2kr)}A_R(q)\uparrow\Psi_r(q).
\]

All exponents in the finite arithmetic are integers, including at the working parameter \(q=1/2\). Reflection gives \(\Psi_{n-r}=q^{\lambda(n-2r)}\Psi_r\) for canonical residues \(1\le r<n\). Residue zero reflects to charge \(n\), outside that canonical packet, so it should not be silently identified with a second residue-zero value.

The implementation uses the reflection-friendly product box \([-H,H+1]\). Its omitted one-coordinate positive and negative Gaussian tails start at magnitudes \(H+2\) and \(H+1\), respectively, exactly as coded. For a coefficient at \(R=kn+r\), the missing negative-coordinate tail starts at magnitude \(k+1\). Dropping the charge constraint and using a union bound with a rigorous one-dimensional Gaussian upper bound therefore gives the stated rational enclosure. A further **90 independent exact cases** across connected and disconnected graphs, \(q=1/2,2/3,5/6\), and pinning one and two checked nested boxes, boundary containment, subsequent normalized coefficients and reflected finite-box sums. No new runtime or proof correction was required.

## Classical source boundaries

The following are primary-source anchors for classical tools. They do not claim the project-specific graph consequences or arithmetic decoder.

* Christina Roehrig, *Siegel theta series for indefinite quadratic forms*, Research in Number Theory **7** (2021), article 45, section 4: https://doi.org/10.1007/s40993-021-00272-y. The proof uses Poisson summation and Fourier transforms of positive-definite Gaussian forms; our connected pole noncancellation argument is the direct positive-definite character specialization written above.
* Kenneth W. Johnson and Donald St. P. Richards, *Hyperdeterminantal Total Positivity*, SIGMA **21** (2025), 055: https://doi.org/10.3842/SIGMA.2025.055. Its discussion identifies the classical exponential kernel and Binet–Cauchy composition framework; the tree path, volume and leading-coefficient consequences above are derived separately.

## Overall conclusion

The companion supplies analytic, arithmetic and ordered-kernel constraints on proposed full-series collisions and graph realizations. It does not infer full-series equality from an arbitrary finite prefix, settle the three general frontiers, or change NX36 implementation and acceptance statuses.
