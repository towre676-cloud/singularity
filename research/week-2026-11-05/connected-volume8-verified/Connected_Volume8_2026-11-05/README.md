# The connected volume-eight measurement minimum is six

November 5, 2026. Research reconciliation and fresh exact replay against
`singularity@17f033ea9a1e6d93224e946a341f7a0e545ee64a`.

The requested seven-measurement necessity theorem is false for connected graphs.
The strongest established replacement is an exact **six-measurement minimum**
for finite simple connected cubic graphs, in the unbounded fixed rational linear
observation model, conditional on exact height-polynomial agreement through
volume seven. This was already proved in the recovered November 4 work; this
package rechecks that result and adds exhaustive five-panel collision certificates.
No upstream repository state was changed.

## Why seven cannot remain necessary

A cubic connected subgraph of a cubic graph occupies a whole connected component:
each of its vertices has already used all three ambient edges. Consequently,
when the connected host has more than eight vertices, none of the five cubic
eight-vertex motifs can occur. Their aggregate S8_12 is zero. Volume one fixes
vertex order; the 1,2,5 connected cubic graphs of orders 4,6,8 respectively have
distinct signatures through volume seven, checked by direct height enumeration.
Thus compatible small pairs also have zero S8_12 difference.

The complete inherited volume-eight difference law therefore has just six
coordinates, ordered here as

    Q0, Q1, S8_10, S8_11, Theta223, closed_diamond.

With kappa=q(1-q^2), f=q^(-2)-1, a=(1+q^2)^3-1,

    Delta H8 = kappa^8 (Delta Q0 + f Delta Q1 + f^2 Delta S8_10
                       + f^3 Delta S8_11 - a Delta Theta223
                       + f a Delta closed_diamond).

This statement reuses the completed source law. The new check verifies every
source coefficient modulo the connected lower-observation rowspace; it does
not rederive the volume-eight theorem. Restricted cumulative ranks are 15 and
21, but rank alone is not the necessity argument.

## Connected realization, rather than only linear independence

There are 92 nonsaturated connected leafless subcubic core types through eight
vertices. Their seed-count matrix is integral unitriangular. Independent
edge-subset enumeration verifies all 92 integral isolators. It follows that
any integer core difference vector can first be represented by a signed union
of nonsaturated seeds.

Replace the disjoint union completion by one connected reservoir on each side.
The explicit 126-vertex cubic girth-twelve graph Q supplies necklace blocks:
remove edge (0,1) from every block and cyclically join their exposed endpoints.
Subdivide edge (5,6) in different blocks, once per required seed half-edge;
attach each deficient seed vertex to its own subdivision site. Every seed has
a deficit, so every seed meets the same connected cubic reservoir. The result
is simple, connected and cubic.

Distinct sites are at reservoir distance at least eleven. A connected leafless
pattern on at most eight vertices meeting the reservoir would either contain
a reservoir cycle of length at least twelve or have a reservoir tree part with
two distinct attachment-site leaves. Both alternatives exceed the cutoff.
This excludes new bridge-bearing cores as well as new cycles. Hence every
small core count equals the sum of its original seed counts.

If K is the number of seed vertices and D the number of missing half-edges,
the resulting order is K+D+126t, with t>=max(2,D). Multiplying an arbitrary
integer seed relation by 63 makes the two even base orders congruent modulo
126. Choose t independently on both sides to obtain equal order. The six
retained source isolators already satisfy the congruence, without an extra
factor. Their isolated observation scales are (63,63,21,63,1,63).

For any at most five rational linear measurements on the six coordinates,
choose a nonzero rational kernel vector, clear denominators, and combine these
isolators at their common scale 63. Attach the combined seeds to the reservoir.
This produces one actual connected pair, of equal order and with identical
complete lower polynomials, invisible to every chosen measurement but with
nonzero eighth difference. It is a realization proof for arbitrary rational
measurement rows, not an inference from the span of separately realized pairs.

Full construction details and the small-order exception proof are in
`CONNECTED_PROOF.md`. That retained proof establishes a sufficient universal
scale 63; the stronger unit-scale and higher-connectivity results in the older
bundles are unnecessary for this conclusion and are not re-certified here.

## New exact panel certificate

`replay/panel_collisions.py` independently checks all 24 seed types used by the
six isolators, evaluates the full inherited source law at every volume 1-8,
and constructs a nonzero integer kernel and connected recipe for every
five-coefficient panel. All 3,003 panels from the fifteen nonzero even degrees
2 through 30 pass: 2,937 have rank five and 66 have rank four.

`replay/panel_collisions.json` retains every panel, primitive kernel vector and
resulting equal graph order. The generation recipe is recovered exactly from
the kernel using the packaged script. Each output has coordinate difference
63 times that vector. Lower volumes agree and every selected coefficient is
zero. Degrees outside the fifteen listed degrees vanish identically; any
smaller panel extends to a five-panel. Thus the finite check covers every
panel of at most five single coefficients, even allowing arbitrary degrees.
The general proof above also covers rational linear combinations of coefficients.
Large recipe orders are certified by the reservoir proof and seed arithmetic;
these graphs were not materialized or brute-force enumerated.

For a chosen panel, print its full signed seed relation, polynomial and both
connected graph recipes with

    cd replay
    python panel_collisions.py --panel 6 10 14 18 24

## Concrete graph certificates and independent replay

`fixed20_certificate.json` retains all twelve complete edge lists of six
20-vertex bridgeless pairs from the November 4 work. This session independently
replayed global weak-composition height enumeration directly from their edges,
without calling the motif source law. Simplicity, cubicity and connectedness
after deletion of every edge were separately checked. In B-minus-A convention,
the six coordinate differences are

    (-1, 1, 1, 0, 0, 0)
    (-2,-1, 0, 0, 0, 0)
    (-1, 0, 0, 0, 0, 0)
    ( 0,-9,-6,-1, 0, 0)
    ( 2, 1, 0, 0, 0, 1)
    (-1, 1, 0, 0,-1, 0).

Their determinant is one. This verifies a connected lattice basis, but does not
assert that every lattice vector is a difference between individual 20-vertex
graphs. The unbounded reservoir construction supplies the stronger realization
property used for minimality.

`replay/explicit_five_panel_collision.json` gives a particularly simple concrete
collision: a 20-vertex bridgeless pair whose difference is -kappa^8 and is
invisible to the rank-five panel (2,4,6,28,30). Its graph edges and full eighth
polynomial are retained. This is an individual collision, independent of the
large recipe constructions.

The 1,666-vertex Theta223 pair is also fully materialized and freshly checked:
`replay/connected_theta_0.json` and `connected_theta_1.json`. An independent
connected-support enumeration rooted at every seed vertex confirms precisely
the prescribed core differences. The reservoir exclusion proves that those
roots capture every possible small leafless core. This check depends on that
structural argument; it is not global weak-composition enumeration of 1,666
vertices.

## Sufficiency and optimized extraction

The unique optimum six-coefficient panel for unscaled observations with equal
independent absolute error bounds is

    (6,10,14,18,24,26)
    determinant: 74791080
    inverse infinity norm: 44191/19786.

All 5,005 panels were freshly checked with exact rational arithmetic; 4,775
are invertible. `replay/connected_certificate.json` retains the rational inverse,
the restricted source-law checks, small-graph classification, reservoir edges,
and six connected realization recipes. The norm applies to the six surviving
coordinate differences. It is a different output space from the original
seven-coordinate norm 93093/14165.

## Reproduction

Python 3, standard library only, except the independent direct-height check,
which additionally requires g++ with C++17 support. From this archive's root:

    cd replay
    python connected_check.py --optimize --enumerate-connected
    python panel_collisions.py
    python verify_graphs.py

Fresh successful logs are packaged. The third command compiles its independent
height enumerator in a temporary directory. The first two commands require no
network. No full 20-vertex catalogue replay is needed for the unbounded
six-measurement theorem; no new exhaustive catalogue claim is made here.

The source law, observation certificate and reader were compared byte-for-byte
using Git blob hashes against the pinned GitHub main commit. Their hashes are
recorded in `PROVENANCE.json`. The live reader still explicitly excludes the
connected restriction: https://github.com/towre676-cloud/singularity/blob/17f033ea9a1e6d93224e946a341f7a0e545ee64a/independent_checks/height_series/VOLUME8_READER.md

## Remaining obstruction and limits

There is no remaining realization obstruction to the connected unbounded
six-measurement theorem relative to the inherited law. The obstruction to the
requested seven-measurement extension is structural: S8_12 cannot vary. In
particular it is impossible to exhibit a collision for every six-panel because
the displayed six-panel is injective on all compatible connected differences.

These are conventional proofs with exact executable certificates, not a
proof-assistant formalization. Review and GitHub integration remain outstanding.
The construction makes no claim about minimal collision orders for arbitrary
panels, a measurement minimum on a finite bounded-order graph class, adaptive
queries or arbitrary nonlinear/irrational encodings. Existing narrower open
pure-unit size questions from the older work are separate from this theorem.
