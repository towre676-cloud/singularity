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
