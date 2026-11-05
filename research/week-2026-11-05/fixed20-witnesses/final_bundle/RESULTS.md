# Singularity: exact observation minima by connectivity

November 4, 2026. Repository base:
`towre676-cloud/singularity@17f033ea9a1e6d93224e946a341f7a0e545ee64a`.

## The completed result

For finite simple cubic graphs whose complete height polynomials agree through
volume seven, the uniform minimum number of fixed rational linear observations
of the eighth difference is:

| Graph class | Minimum measurements | Admissible leafless core coordinates | Lower / total observation ranks |
|---|---:|---:|---|
| Possibly disconnected | 7 | 100 | 17 / 24 |
| Connected | 6 | 92 | 15 / 21 |
| Connected and bridgeless | 6 | 86 | 13 / 19 |
| 3-edge-connected | 4 | 58 | 11 / 15 |

The coordinate counts exclude vertex order. The original disconnected theorem
is unchanged. For cubic graphs, bridgelessness is equivalent to
2-vertex-connectivity, and 3-edge-connectivity is equivalent to
3-vertex-connectivity. This therefore also settles the natural vertex-connectivity
restrictions.

The theorem concerns the unbounded graph class and fixed nonadaptive rational
linear measurements. It does not assert the same measurement minima for a
finite bounded-order domain, arbitrary nonlinear encodings or adaptive queries.

## The four-coordinate law and optimized reader

Write kappa=q(1-q^2), f=q^(-2)-1 and a=(1+q^2)^3-1. In the connected and
bridgeless cases the six surviving coordinates are

    Q0, Q1, S8_10, S8_11, Theta223, closed_diamond.

S8_12 has zero difference. Under 3-edge-connectivity, S8_11 and closed_diamond
also have zero difference. The complete eighth difference is then

    Delta H8 = Delta L8
             = kappa^8 (Delta Q0 + f Delta Q1
                        + f^2 Delta S8_10 - a Delta Theta223).

The unique optimal four-coefficient panel, for unscaled observations with equal
independent absolute error bounds, is

    (8,14,18,20), determinant -1014120,
    inverse infinity norm 5977/22536 = 0.2652200922967696...

All 1,001 panels from the fourteen nonzero degrees are checked with exact
rational arithmetic; 825 are invertible. The six-dimensional optimum remains
(6,10,14,18,24,26), determinant 74791080, norm 44191/19786. Its exhaustive
search checks 5,005 panels, with 4,775 invertible. Norms across different output
dimensions should not be presented as like-for-like comparisons.

## A unit-lattice realization theorem

For lambda=1,2,3 let C_lambda be the connected leafless subcubic patterns on
three through eight vertices satisfying

    3 |U| - 2 |E_H(U)| >= lambda

for every nonempty subset U of seed vertices. There are respectively 92,86,58
such patterns. **Every integer vector indexed by C_lambda is an actual
core-count difference of equal-order lambda-edge-connected finite simple cubic
graphs. No multiplicative scale is required.**

This strengthens the earlier sufficient factor 63 to one. Clearing denominators
handles rational vectors. The common vertex order is allowed to depend on the
vector; no minimum-order assertion is implied by this construction.

### Necessity of the cut test

An occurrence of H in a cubic graph G satisfies
boundary_G(U) <= 3|U|-2|E_H(U)|, since additional internal ambient edges only
decrease the boundary. A pattern violating the inequality cannot occur in a
lambda-edge-connected graph larger than itself.

For lambda=1 this excludes saturated cubic components. For lambda=2 it excludes
six additional patterns: five single-port seeds, and one seed with a saturated
lobe behind a bridge. Merely checking bridges of the seed would miss the five
single-port obstructions. For lambda=3 it excludes every two-port region, including
the eleven-edge eight-vertex cores and the six-vertex closed-diamond core.

### Integral isolation

Use the admissible patterns themselves as seeds. Their non-induced connected
leafless subgraph-count matrix is unitriangular, ordered by vertex count and
edge count. Admissibility is hereditary under subgraph occurrence: adding
internal edges can only lower the displayed capacity. Consequently the inverse
matrix is integral and uses only admissible seeds. Direct edge-subset enumeration
checks all 92,86,58 unit isolators.

### Reservoir construction

Use the explicit 126-vertex girth-twelve cubic graph Q already present in the
source machinery. Exact replay checks its 3-edge-connectivity by root-to-all
unit-capacity flows. Delete vertex 0, leaving a 125-vertex block with three
ports at 1,17,125. Site edge (5,6) is at distance at least four from every port.
Distinct ports are at distance at least ten within the block.

Take an arbitrary sufficiently large prism skeleton, with an even number t>=6
of vertices. Replace each skeleton vertex by a block, attaching its three
incident edges to the three ports. This replacement preserves 3-edge-connectivity.
Indeed a cut splitting a block has at least two internal edges; equality forces
the ports to split 1 versus 2. A cut of size at most two would then have no
crossing edge in the connected remainder, contradicting that port split. Cuts
not splitting a block project to skeleton cuts. Iterating proves the claim.

The reservoir has no cycles through eight vertices. Subdivide the site edge in
distinct blocks to make attachment vertices. Such sites are at mutual reservoir
distance at least eleven. Attach every missing seed half-edge to its own site.

No new small leafless core is created. A component of its reservoir part would
be cyclic, requiring at least twelve vertices, or a tree with two leaves at
distinct attachment sites, whose distance already exceeds the cutoff. A single
reservoir vertex cannot have the two seed edges it would need. This argument
excludes short barbell cores as well as short cycles.

The resulting graph is lambda-edge-connected. A small cut separating original
reservoir vertices contradicts reservoir 3-edge-connectivity. Otherwise place
all original reservoir vertices outside the cut. A seed subset has boundary
at least its capacity; moving an attachment site inside replaces at most one
seed crossing edge by two reservoir crossing edges and cannot reduce that cut.

### Equal order without scaling

With K seed vertices and D missing half-edges, the order is K+D+125t. The value
K+D is even. A singleton seed contributes four to K+D and a single-edge seed
contributes six, while neither changes leafless core counts. Both satisfy the
capacity condition for all lambda<=3. Every even discrepancy at least four is
a nonnegative combination of four and six. A discrepancy two is resolved by
adding six to the smaller side and four to the larger. Thus K+D can be made
exactly equal, and both sides use the same sufficiently large reservoir.

This proves the integer realization theorem. In particular, a rational kernel
for fewer than the required measurements can be cleared to an integer seed
relation and realized by actual connected graphs. Necessity is therefore a
realizability statement, not just a formal rank computation.

### Small graphs and vertex-connectivity

At orders 4,6,8 there are 1,2,5 connected cubic types. Direct height enumeration
finds distinct complete through-seven signatures at each order. Volume one fixes
vertex order; odd-order cubic graphs do not exist. Thus compatible small pairs
have zero eighth difference, resolving the exceptions to the forbidden-core
argument.

A bridgeless cubic graph cannot have a cut vertex, because distinct components
after its removal would each need at least two incident edges. A two-vertex cut
in a 3-edge-connected cubic graph would leave exactly two components, each with
three boundary edges. The two cut vertices must be nonadjacent and each component
uses a 2+1 distribution. Adding the cut vertex with two neighbors in one component
produces a two-edge cut, a contradiction. Together with vertex connectivity <=
edge connectivity, these prove the equivalences used above.

## Exact small-witness bounds obtained in this session

The exhaustive connected cubic catalogues through eighteen vertices contain
45,982 graphs. Complete direct weak-composition enumeration and a separate
induced-core/source-law calculation agreed on every lower-order grouping and
all 163 nonzero reference differences at sixteen vertices and all 9,319 at
eighteen. The Python and C++ direct paths also agreed through fourteen vertices.

| Order | Catalogue size | Nonzero reference differences | Connected / bridgeless / 3-edge-connected span ranks |
|---:|---:|---:|---|
| 4 | 1 | 0 | 0 / 0 / 0 |
| 6 | 2 | 0 | 0 / 0 / 0 |
| 8 | 5 | 0 | 0 / 0 / 0 |
| 10 | 19 | 0 | 0 / 0 / 0 |
| 12 | 85 | 2 | 1 / 1 / 1 |
| 14 | 509 | 13 | 1 / 1 / 1 |
| 16 | 4060 | 163 | 4 / 4 / 4 |
| 18 | 41301 | 9319 | 5 / 5 / 4 |

Reference differences exhaust each agreement group's difference span, since
any pair difference is the difference of two reference differences.

The smallest nonzero compatible pair has **twelve** vertices, even under
3-edge-connectivity. The smallest common order admitting a four-direction
3-edge-connected basis is **sixteen**. Four such vectors in six-coordinate order
(Q0,Q1,S8_10,S8_11,Theta223,closed_diamond) are

    ( 2, 4, 2, 0, 0, 0)
    (-2,-2, 0, 0, 0, 0)
    ( 1, 0, 0, 0,-1, 0)
    (-2, 0, 0, 0, 0, 0).

Their determinant on the four surviving coordinates is -8. An eighteen-vertex
bridgeless pair adds (0,0,-1,0,0,1). The retained twenty-vertex weld pair adds
(0,-9,-6,-1,0,0). The combined six vectors have determinant 8.

Thus **twenty is the exact minimum vertex ceiling for a full six-direction
connected or bridgeless basis**, allowing the basis pairs to have different
orders. No pair through eighteen exposes S8_11; the twenty-vertex weld pair does.
This does not establish a common-order six-direction basis at twenty, nor a
bounded-order measurement minimum.

The minimum orders for a nonzero natural coordinate difference, in both the
connected and bridgeless classes, are:

| Coordinate | First possible order |
|---|---:|
| Q0 | 12 |
| Theta223 | 12 |
| Q1 | 16 |
| S8_10 | 16 |
| closed_diamond | 18 |
| S8_11 | 20 |

These concern coordinate exposure, possibly mixed with other coordinates.
Minimum orders for isolated pure unit vectors remain unproved.

## Evidence preservation and repository proposal

Workspace maintenance removed the unsaved files after the completed computations.
The earlier connected bundle was recovered intact. This final package reconstructs
the new report and replay programs from the session, retains the observed
exhaustive-search summary, and freshly checks the packaged small witnesses and
the algebraic connectivity results. It does not pretend the deleted full raw
9,319-pair run files were retained. The supplied complete enumeration program
and source-pinned catalogue generator can regenerate them.

The mathematical results depend on the established exact volume-eight source
law. They have executable integer/rational checks, not a proof-assistant
formalization. The original disconnected theorem is preserved. Proposed repository
additions are supplied as a patch; no upstream branch, commit, PR, proof or reader
has been changed. Remaining narrow questions are minimum pure-unit witness sizes
and a common-order twenty-vertex six-direction basis.
