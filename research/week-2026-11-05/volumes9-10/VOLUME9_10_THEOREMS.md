# Ninth- and tenth-order height-series laws for cubic graphs

4 November 2026. Additive continuation of Singularity main
17f033ea9a1e6d93224e946a341f7a0e545ee64a and the November 4
fixed-excess and connectivity handoffs. No historical-priority claim.

## Theorems and observation model

All graphs are finite, simple and cubic. Heights are nonnegative integers,
and original labelled height assignments retain their full multiplicity:

    L_G(x,q) = sum_h x^(sum_v h_v) q^(sum_uv (h_u-h_v)^2).
    ell_G = log L_G;  kappa=q(1-q^2); f=q^(-2)-1.

N_H is the number of ordinary, possibly non-induced, copies of H.
A core is a connected subcubic pattern of minimum degree at least two.
Let S_(r,e) be the sum of N_H over cores of order r and size e.
Use Delta F=F(A)-F(B) throughout this document.

**Ninth-order theorem.** If L_A and L_B agree coefficientwise as
polynomials in q through volume eight, their ninth difference belongs
to an explicitly specified ten-dimensional rational polynomial space.
It is reconstructed by the ten q-coefficients at degrees

    1,3,5,7,9,11,13,15,17,19.

The reader matrix has determinant -6 in the supplied coordinate basis.
The complete ninth-order rowspace has rank 34, extending rank 24 through
eight. `vol9_law.json` gives every source coefficient and every leaf
reduction; `vol9_reader.json` gives ten coordinate definitions, the exact
inverse, reconstruction functions, and source-row witnesses.

**Tenth-order theorem.** If the series agree through volume nine, their
tenth difference belongs to an explicitly specified fourteen-dimensional
rational polynomial space. Its coefficients at degrees

    0,2,4,6,8,10,12,14,16,18,20,22,24,26

reconstruct it exactly. The reader determinant is 40 in the supplied
basis. The cumulative rank through ten is 48. `vol10_law.json` and
`vol10_reader.json` contain the corresponding full exact certificates.
These panels are proved invertible; neither is claimed noise-optimal.

For known lower agreement, the minimum number of fixed rational linear
observations needed uniformly on each unbounded graph class is:

| Graph class | Eighth increment | Ninth increment | Tenth increment |
|---|---:|---:|---:|
| Possibly disconnected | 7 | 10 | 14 |
| Connected | 6 | 10 | 12 |
| Connected and bridgeless | 6 | 9 | 12 |
| 3-edge-connected | 4 | 8 | 10 |

The eighth column is inherited from the connectivity handoff. The ninth
and tenth columns follow from the calculations and realization proof
below. These are fixed rational linear measurements on the unknown
coefficient polynomial, not nonlinear encodings, arbitrary irrational
queries, or a claim about a bounded vertex-order population. They concern
exact lower agreement and exact arithmetic.

The cumulative ranks at volumes eight, nine and ten respectively are
24,34,48 unrestricted; 21,31,43 connected; 19,28,40 bridgeless; and
15,23,33 under 3-edge-connectivity. Vertex order is included in these
cumulative ranks and is already observed at volume one.

## Complete correction formulas

For R=9 or 10, the source law is

    ell_R(G) = sum_H c_(R,H)(q) N_H(G),

including H=K1 with N_H=n. Coefficients c_(R,H) are the exact sparse
rational q-polynomials in `coefficient_rows[R]`. Rational elimination
modulo every lower coefficient gives the compact, complete formula

    Delta L_R = kappa^R sum_(j=0..floor(R/2))
                              f^j Delta S_(R,R+j)
                + sum_(|H|<R) rho_(R,H)(q) Delta N_H.

The residual contains 25 lower core columns at R=9 and 123 at R=10.
They are stored under `ninth_lower_support_residual` and
`tenth_lower_support_residual`, with explicit lower-row elimination
certificates. Each top core has coefficient kappa^R f^(e-R).
Grouping all top cores of the same size produces the displayed sums.
This formula is exact under literal lower height-series agreement;
matching all individual lower motifs would be a stronger hypothesis.

For a human-readable ninth-order normal form, set t=q^2 and introduce
polynomials

    P_A=t^6+4t^5+4t^4-5t^3-15t^2-14t-6,
    P_B=t^7+3t^6+t^5-6t^4-9t^3-5t^2-t+1,
    P_C=t^6+5t^5+9t^4+5t^3-5t^2-9t-3,
    a=(1+t)^3-1.

The ten coordinates in the reader, named Q0,...,Q4,U,V,W,Y,Z, satisfy

    Delta L9 = kappa^9 [sum_(j=0..4) f^j Delta Qj
                         + f P_A Delta U + (P_B/t) Delta V
                         -2 f^2 P_C Delta W + a Delta Y
                         + f(1+t)^3 Delta Z].

The Qj equal S_(9,9+j) plus the lower corrections listed in the reader.
U,V,W,Y,Z are rational linear combinations of lower core counts, not
claims that five individual lower motifs are separately recovered.
For example U=N_(6,5494)+S_(8,9)/2, V=N_(6,6265)+S_(8,9)+3N_C8,
and W=N_(6,7100)+N_C8. The six-vertex motifs are respectively K3,3
minus an edge, Theta(1,3,3), and the triangular prism. The remaining
coordinate definitions are given exactly as count lists in the reader.
Every ninth coordinate has an explicit rational combination of actual
coefficient rows through nine; every tenth coordinate has the analogous
witness through ten. The quotient identities are checked for every q-degree,
not only at the selected panel.

For orders through eight masks use the source's decreasing-degree
canonical convention. Nine- and ten-vertex masks use actual relabellings
returned by pinned pynauty; consult their stored edge lists/catalogues
rather than mixing the two conventions. Negative powers in the factored
form are formal Laurent expressions; multiply out before endpoint
specialization. The final source coefficients are ordinary q-polynomials.

## Derivation and finite algebra

Cubic energy is 3 sum h_v^2 minus 2 sum_uv h_u h_v. Boolean inversion
of log L by vertex support vanishes on disconnected supports; edge
inversion converts induced counts to ordinary subgraph counts. Every
fixed volume therefore has a finite exact connected-pattern expansion.
Its top-support coefficient is q^(3R)(q^(-2)-1)^e. No coefficient fitting
is used anywhere in this construction.

At volume nine, supports through five use the existing exact cumulant
and edge-inversion calculation; six-vertex supports use the newly
checked third off-diagonal; seven and eight use the established second
and first off-diagonal. At volume ten, supports through six use the
exact cumulant calculation; seven use the third off-diagonal; eight
and nine use the second and first. The new largest supports use the
diagonal identity. Thus all support sizes are covered at each volume.

For a pattern Y formed by adding a leaf to vertex v of H, unused host
neighbours of its embedded v either lie outside H or are images of
non-neighbours of v inside H. Counting these disjoint cases gives

    Emb(Y)=(3-deg_H(v)) Emb(H)-sum_w Emb(H+vw).

Dividing each embedding count by its automorphism order gives the
ordinary-count recurrence. Every resulting graph has fewer vertices,
so iterated leaf removal terminates in K1 and leafless cores. The source
recurrence is used without changing its mathematical semantics.

The new catalogues contain 531 connected subcubic nine-vertex types,
including 148 cores, and 1,733 connected subcubic ten-vertex types,
including 458 cores. Core size distributions are respectively
(1,13,52,63,19) for sizes 9 through 13 and
(1,18,109,198,113,19) for sizes 10 through 15; the exact certificate is
authoritative if reading a differently ordered display.

Each catalogue is checked by two constructions: nauty canonical
augmentation with `geng -c -D3`, and adding a new vertex to every smaller
connected type in all degree-permitted ways. Every connected graph has
a removable non-cut vertex, proving completeness of the second route.
An independent adjacency-preserving backtracker checks automorphism
orders for all 531+1,733 patterns against nauty. This matters because
automorphism divisors enter the leaf recurrence.

Exact rational row reduction yields the ranks and residuals above.
The reader proofs check both directions: its count coordinates are in
the full coefficient rowspace, and every coefficient row is reconstructed
modulo the lower observation space. An invertible panel alone would not
establish these facts; those stronger checks are explicitly included.

## Realization: why the ranks give genuine minima

This extends the supplied unit-lattice reservoir theorem from cutoff
eight to every cutoff R<=11. The explicit cubic graph Q has 126
vertices, girth twelve and edge connectivity three. Removing a vertex
gives a 125-vertex three-port block. Ports have mutual distance at least
ten; site edge (5,6) is distance at least four from each port. Replacing
each vertex of a sufficiently large even prism by such a block produces
a 3-edge-connected reservoir. Subdividing its site edges in distinct
blocks makes attachment sites at pairwise distance at least eleven.

For lambda=1,2,3 retain precisely the cores H such that

    capacity_H(U)=3|U|-2|E_H(U)| >= lambda

for every nonempty seed subset U. In any larger lambda-edge-connected
cubic host, an occurrence violating this inequality would create a cut
smaller than lambda; added ambient internal edges only reduce the cut.
This is stronger than testing the seed's bridges alone.

The admissible seed-count matrix is unitriangular by vertex and edge
count, with diagonal one. Admissibility is hereditary under subgraph
occurrence. Its inverse is integral. Consequently every integer vector
of admissible core counts is a signed integer combination of seeds.
Independent matching enumeration verifies all unit isolators: at cutoff
nine there are 240,213,164 in the three connected classes; at cutoff ten
there are 679,641,446. The full unrestricted core dimensions are 248
and 706. Certificate files retain the actual rows and witness recipes.

Attach every missing seed half-edge to its own reservoir site. A small
leafless core entering the reservoir would contain either a cycle of
length at least twelve or a tree connecting two distinct sites, whose
path already has at least twelve vertices. An isolated site cannot
supply two seed edges. Hence no new core of order at most eleven is
created, including a barbell with bridges. A small cut splitting original
reservoir vertices violates its connectivity; with those vertices all
on one side, moving an attachment site across a cut cannot decrease the
seed cut capacity. The completed graph has the required lambda-connectivity.

If seeds contain K vertices and D missing half-edges, the order is
K+D+125t, with even t sufficiently large. Singleton and edge seeds
add respectively 4 and 6 to K+D without changing core counts. These
adjust every even discrepancy, including two by adding six to one side
and four to the other. Thus the signed seed relation is realized at
equal order with no scaling of its core vector.

For the unrestricted class, form a cap by subdividing edge (0,1) of Q.
Attach its new degree-two vertex to one seed half-edge, using a fresh
cap for every deficit, and allow disjoint unions. Core-free filler components
C(K1), C(K2), and Q have orders 382,510,126. Since
510-382-126=2, signed fillers correct any even order discrepancy without
changing the small-core difference. This also gives unit-scale
unrestricted core realization.

Connected small-order exceptions are handled separately: volume one
fixes order; the 1,2,5,19 connected cubic types at orders 4,6,8,10 have
distinct required lower prefixes. The ninth theorem needs only orders
through eight; the tenth needs through ten. Thus no compatible small
pair invalidates a forbidden-core restriction.

Given fewer than d rational linear measurements on a d-dimensional
ninth/tenth difference space, choose a nonzero rational kernel vector,
clear denominators and realize its admissible core vector by this
construction. The two graphs agree at all lower volumes and on every
chosen measurement, but have different target coefficients. Necessity
therefore concerns actual graph pairs. The stored isolated witnesses
also independently verify this argument in the finite coordinate basis.
`class_readers.json` additionally gives exact coefficient panels and
polynomial reconstruction bases for each connectivity class at both
volumes. Every reconstruction is checked on all source rows modulo its
lower observation space. Their sometimes very large orders are explicit construction upper bounds;
the graphs were not allocated or brute-force enumerated at those orders.

## High-girth consequences

At volume nine, girth at least five eliminates every lower-support
residual modulo the lower observations. The top cores split as one
9-cycle, four theta types, four size-eleven cores, and one size-twelve
core. Thus

    Delta L9=kappa^9[Delta S_(9,9)+f Delta S_(9,10)
                     +f^2 Delta S_(9,11)+f^3 Delta S_(9,12)].

At girth six only C9, Theta(2,4,4), and Theta(3,3,4) survive, giving
two observations. At girth at least seven only C9 remains, so
Delta L9=kappa^9 Delta N_C9. At girth ten no ninth difference remains.
All statements retain agreement through eight.

At volume ten, girth at least six gives a pure top-core law with edge
sizes 10,11,12, requiring three unrestricted directions. Girth seven
leaves C10 and Theta(3,4,4), requiring two; girth at least eight leaves
only C10. At girth five there are seven unrestricted directions and
lower-support residual information remains, so the ninth simplification
must not be extrapolated. The girth restrictions are compatible with
the same reservoir argument up to cutoff eleven.

## Independent checks, scope and remaining work

Direct C++ enumeration of every weak composition through volume ten on
all 112 connected cubic graphs through twelve vertices agrees with the
source laws. A distinct core counter enumerates induced vertex subsets,
then matchings of removable edges: to leave every induced degree at
least two in a subcubic graph, deleted edges must be a matching whose
endpoints both originally have degree three. Conversely every such
matching gives the required spanning leafless subgraph if connected.
Eight tiny hosts additionally agree with raw edge-subset enumeration.
The explicit reservoir parent passes girth and three-edge-connectivity
checks; a 756-vertex triangle-seed example is materialized and checked
for simplicity, cubicity and three-edge-connectivity.
There are 1,232 direct height-coefficient comparisons through ten.

The pending pure-unit Q0/Q1 twenty-vertex witnesses from the earlier
handoff also pass independent direct heights and bridgelessness checks.
Their minimum possible orders are not established by this replay.

These results use mathematical arguments and exact integer/rational
computation, not proof-assistant formalization. The standing support
expansion and previous off-diagonal theorems remain dependencies. No
claim of global graph reconstruction, small optimal witness order,
noise-optimal panels, or a completed volume-eleven coefficient table is
made. The next exact finite target is volume eleven; the realization
lemma already covers it, but its coefficient computation is not included.
