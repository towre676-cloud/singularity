# Fixed-excess component formula for the height-series pattern kernels

4 November 2026. Mathematical derivation and exact finite verification.
Base source: Singularity main 17f033ea9a1e6d93224e946a341f7a0e545ee64a.
This extends the computation in VOLUME8_OFFDIAGONAL.md; it makes no historical-priority claim.

## Statement and conventions

For a finite simple d-regular host G, write

    L_G(x,q) = sum_h x^(sum h_v) q^(d sum h_v^2 - 2 sum_uv h_u h_v).
    log L_G = sum_(connected H) N_H(G) K_H(x,q).

N_H counts ordinary non-induced unlabelled copies. K_H is the universal
pattern kernel obtained by vertex and edge inversion. It is not the
minimum-zero normalized series sometimes denoted B_G in the project.
Fix a connected simple pattern H with k vertices, e edges and maximum
degree at most d. Fix excess s >= 1. Put z=q^(-2), f=z-1 and

    g_w(z) = 1+z+...+z^(w-1) for w >= 1; g_0=0.

Choose a nonempty set X of exceptional vertices, |X| <= min(k,s).
At each v in X choose an ordered nonempty tuple of positive heights
h_v=(h_(v,1),...,h_(v,m_v)), satisfying

    sum_(v in X) (sum_i h_(v,i) - 1) = s,
    sum_i h_(v,i) >= 2 for every v in X.

Every vertex outside X has one height-one particle. Let P be the set
of labelled exceptional particles (v,i). Partition P into blocks pi,
with at most one particle from each vertex in a block. For a block b,
write h_b(v) for its height at vertex v, or zero if v is absent. Define

    W_uv(pi) = sum_(b in pi) h_b(u) h_b(v),  u,v in X.

Let C range over the connected components of H-X, and let
b_v(C) be the number of edges from v to C. Set

    T_C(pi,z) = sum_(b in pi) product_(v in X: b_v(C)>0)
                                      g_(h_b(v))(z)^b_v(C).

Then the exact formula is

    [x^(k+s)] K_H = f^e sum_(X,(h_v))
          q^[d(k-|X|+sum_(v,i) h_(v,i)^2)] / product_v m_v!
          * sum_(admissible pi) (-1)^(|pi|-1)(|pi|-1)!
          * product_(uv in E(H[X])) g_(W_uv(pi))(z)
          * product_(C in components(H-X)) T_C(pi,z).

Empty products equal one. The case s=0 is separately

    [x^k] K_H = q^(dk) f^e.

This is a finite Laurent-polynomial identity. For host-realizable
patterns the cancellations produce the appropriate ordinary q-polynomial;
intermediate Laurent expressions are legitimate formal arithmetic. At
q=0 or q=1, specialize the expanded polynomial, not the unexpanded
negative-power expression. Rational coefficients are expected in log L.

## Proof

Use the project's particle expansion: a particle of height a at a site
has activity x^a q^(d a^2); interactions at adjacent distinct sites have
factor q^(-2ab)-1, and same-site particle interactions have factor -1.
The logarithm retains connected particle graphs. Summing optional
interactions inside a block of a set partition produces the cumulant
weight (-1)^(b-1)(b-1)!. A block containing repeated occurrences of a
site has a full factor 1-1=0, so only the admissible partitions remain.
The factors m_v! remove temporary labels at each site. Edge inversion
requires every pattern edge to occur and gives, for uv, the factor
z^(W_uv)-1. This recovers the all-particle partition identity already
proved in VOLUME8_OFFDIAGONAL.md.

It remains to compress that identity; this is the new step. Nonexceptional
vertices carry one height-one particle. If two such vertices are joined
by an edge, their particles must lie in the same partition block:
otherwise W_uv=0 and their edge factor is zero. Consequently every
connected component C of H-X lies wholly in one block.

Every component C has an edge to X, since H is connected and X is
nonempty. Its block must therefore contain an exceptional particle at
every boundary vertex v with b_v(C)>0. If one is absent its edge factor
is zero. Conversely, every admissible exceptional block containing
those boundary sites is a possible home for C. All nonzero full
partition blocks contain exceptional particles: a block containing only
nonexceptional vertices would consist of one or more components of
H-X and fail on one of their boundary edges. Thus restricting a full
partition to exceptional particles does not change its number of blocks
or its cumulant weight.

For an internal component edge, W=1 and its factor is f. For a boundary
edge to v in block b, W=h_b(v), giving f g_(h_b(v)). For an edge entirely
inside X, W=sum_b h_b(u)h_b(v), giving f g_W. Extracting one f from
every pattern edge leaves exactly the displayed internal product and
the component weights T_C. Assignments of distinct components are
independent and multiply; they may share a block, and the formula
allows this. This assignment is bijective with the nonzero full
partition contributions, so it loses neither multiplicities nor signs.
The site activities and label factorials supply the remaining factors.
This proves the formula for all finite k,d,s under the stated conditions.

## Why the computation scales with excess

Each exceptional vertex costs at least one excess unit, so |X| <= s.
Also sum_v(m_v-1) <= s, hence the exceptional particle set has size
sum_v m_v <= s+|X| <= 2s. There are at most Bell(2s) set partitions
before inadmissible cases are removed. This bound is independent of k.

For fixed s, enumerate O_s(k^s) exceptional sets and local states.
A deletion-component pass takes O(k+e). On subcubic patterns there
are at most 3s boundary edges and at most 3s components. After the
common factor f^e is extracted, all remaining z-polynomial degrees are
bounded by a function of s. In ambient degree three the q shifts differ
from 3k by a function of s as well. Hence an implementation with adjacency
lists and cached small polynomials uses O_s(k^(s+1)) exact arithmetic
operations, apart from bit complexity and input/output representation.
The supplied implementation is a clear reference version rather than
an optimized realization of that operation bound; for example it checks
component boundaries by scanning vertex pairs. No speedup over the
existing closed first/second formulas is asserted. Dependence on s is
large, so this does not give an efficient unrestricted all-volume solver.

For the newly supplied third off-diagonal, s=3: at most three exceptional
vertices and six exceptional particle labels suffice. Bell(6)=203,
whereas a direct particle partition computation at volume k+3 can
involve partitions on k+3 labels. Setting s=1 and s=2 recovers the
project's existing off-diagonal formulas.

## Direct implications for volume six, eight and nine

At volume six, the method independently computes K_H[6] on three-vertex
patterns at excess three, four-vertex patterns at excess two, five-vertex
patterns at excess one and six-vertex patterns on the diagonal. It does
not change the established four edge-count sums in the volume-six law.

At volume eight, it supplies five-vertex rows at excess three in addition
to the established six-, seven- and eight-vertex formulas. The smaller
patterns can use the same general routine at higher excess. In
particular this strengthens the independent calculation of delayed
motif terms; it does not eliminate the two delayed six-vertex coordinates.

At volume nine, every six-vertex row now has an exact independently
checked third off-diagonal calculation. Together with the existing
second/first/diagonal formulas this covers the rows of support sizes
six, seven, eight and nine. The 29 connected six-vertex subcubic rows
at volume nine are included in defect_certificate.json. Completing the
volume-nine theorem still requires the nine-vertex support catalogue,
leaf reductions, lower-row quotient, rank proof and realizable witnesses.
None of those remaining steps is claimed complete here.

## Verification

Run from this directory:

    python3 check_defect.py

The oracle directly enumerates heights by stars-and-bars, computes
logarithms by an independent coefficient recurrence, and performs raw
edge-subset inversion, without particle partitions or component
compression. For connected H with k>1, edge inversion annihilates every
proper-support term: a missing vertex omits an incident pattern edge.
Thus edge inversion of log Z equals edge inversion of the support
cumulant. The singleton is handled directly.

All 20 connected subcubic types through five vertices are checked at
excess 0,1,2,3 (80 comparisons). Four more checks cover d=0,2,4, a
singleton at higher excess and K4 at ambient degree four. Forty
comparisons recover both previously proved off-diagonals. Every one
of the 29 connected six-vertex subcubic types is checked at volume nine
against the repository's independently structured beta calculation.
Twenty relabelling checks and six invalid-input rejections also pass.
There are zero failures. Timings and source hashes are in the certificate.
This is a mathematical proof with exact arithmetic checks, not a
proof-assistant formalization. The reference dependencies are unmodified
files from the pinned source commit, included for a self-contained replay.
