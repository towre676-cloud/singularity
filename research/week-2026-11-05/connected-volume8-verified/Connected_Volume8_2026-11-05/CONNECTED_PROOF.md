# Connected cubic graphs need exactly six volume-eight coefficient measurements

Date: November 4, 2026. Base: `towre676-cloud/singularity` main commit
`17f033ea9a1e6d93224e946a341f7a0e545ee64a`.

## Result and scope

The seven-measurement minimum does **not** extend to connected finite simple
cubic graphs. In the same rational linear observation model, the exact connected
minimum is **six**. The original disconnected theorem remains valid.

More precisely, let A and B be connected finite simple cubic graphs whose complete
height polynomials agree in every volume through seven. Their eighth difference
is uniquely determined by six scalar q-coefficients. Fewer than six rational
linear observations cannot recover every such difference. This is an unbounded
graph-class theorem; it does not assert the same necessity at any specified
vertex order, for bridgeless graphs, or for graphs of higher connectivity.
The constructed examples can have bridges. The theorem concerns exact compatible
height calculations and rational linear measurements, including individual
q-coefficients. It makes no claim about nonlinear or irrational encoding queries.

The surviving coordinate order is

`(Q0, Q1, S8_10, S8_11, Theta223, closed_diamond)`.

The omitted coordinate is `S8_12`. With kappa=q(1-q^2),
f=q^(-2)-1 and a=(1+q^2)^3-1, the formula becomes

    Delta H8 = Delta L8
             = kappa^8 (Delta Q0 + f Delta Q1
                        + f^2 Delta S8_10 + f^3 Delta S8_11
                        - a Delta Theta223 + f a Delta closed_diamond).

All retained witness recipes use **Delta = A minus B**. The existing reader uses
B minus A. Reversing the two inputs reconciles the signs.

## Why the seventh coordinate disappears

A connected cubic pattern whose vertices all have degree three cannot occur as
a proper subgraph of a cubic graph: every incident edge of every pattern vertex
has already been used. Its image is an entire connected component. Thus a
connected graph of order greater than eight has zero counts for every connected
cubic core through eight vertices. In particular, every eight-vertex core with
twelve edges is such a component, so S8_12=0.

The forbidden canonical cores in the existing convention are

    (4,63), (6,4060), (6,7100),
    (8,2022000), (8,5192304), (8,5683824),
    (8,5691760), (8,6215777).

Deleting these eight component-count coordinates from the exact source law
changes its cumulative ranks from 17 and 24 to **15 and 21** at volumes seven
and eight. The incremental rank is six. The replay additionally checks the
entire source-row identity modulo the restricted lower-order observation span;
it does not infer sufficiency from the rank difference alone.

The small-order exception must be addressed separately. Equality at volume one
implies equal vertex order, since H1=n q^3. Connected simple cubic graphs at
orders four, six and eight have respectively one, two and five isomorphism
types. Exhaustive catalogue generation and direct weak-composition height
enumeration show that their complete through-seven signatures are distinct at
each order. Consequently every compatible pair of order at most eight has zero
eighth difference. Combining the two cases proves Delta S8_12=0 for every
compatible connected pair, including the small graphs.

## A connected realization theorem

There is a stronger structural statement behind the lower bound.

**Theorem.** Let C be the 92 connected leafless subcubic patterns on three
through eight vertices that are not themselves cubic. For every integer vector
v indexed by C, there exist equal-order connected finite simple cubic graphs
A and B whose non-induced core-count difference is 63 v. All saturated core
counts through eight are zero on both sides. Clearing denominators gives the
corresponding scaled realization statement for every rational vector.

The common order is allowed to depend on v. The scale 63 is a convenient
uniform bound, not a minimal-scale assertion. The six selected coordinate
witnesses below use their existing, sometimes smaller, realization scales.

### 1. Integral isolation inside nonsaturated seeds

For each pattern H in C use H itself as a seed. Its vector of connected
non-induced leafless subgraph counts is unitriangular when patterns are ordered
by vertex count and then edge count: the diagonal count is one, and all other
occurring patterns precede H. A saturated cubic pattern cannot be a proper
connected subgraph of H, by the component argument above.

The inverse matrix is therefore integral and uses only nonsaturated seeds.
Every integer vector v is a signed integer combination of the seed-count rows.
The replay independently enumerates edge subsets to verify this triangular
matrix, its determinant one, and all 92 integer unit isolators. This argument
does not require the source's cubic completions to have free connection ports.

### 2. An explicit connected reservoir with separated attachment sites

Use the existing explicit 126-vertex cubic graph Q of girth twelve. The replay
checks simplicity, cubicity, connectedness and girth from its edge list. Choose
cut edge (0,1) and site edge (5,6). Every site endpoint is at distance at least
four from every cut endpoint. Removing the cut leaves Q connected.

For t>=2, take t copies of Q, remove the cut in every copy, and join the second
cut endpoint of copy i to the first cut endpoint of copy i+1 cyclically. This
is a connected simple cubic necklace. A cycle staying in one block has length
at least twelve. A cycle using cross-block edges traverses every block and uses
an alternative cut-endpoint path of length at least eleven in every block, so
its length is at least 12t. Hence the reservoir has girth at least twelve.

Subdivide the site edge in any chosen D distinct blocks, once per block. The
new subdivision vertices are attachment sites. Two sites in distinct blocks
are at distance at least eleven: one step from a site to its edge endpoint,
at least four steps to a cut endpoint, a cross-block edge, at least four steps
to the other site edge, and one step to its subdivision vertex. Additional
blocks only increase that bound. Subdivision does not create shorter cycles.

### 3. Attach every missing half-edge

For a disjoint collection of seeds with K total vertices and E total edges,
there are D=3K-2E missing cubic half-edges. Assign every missing half-edge its
own reservoir site and join the seed vertex to that site. All degrees become
three. Every seed has a deficit and hence meets the reservoir; the resulting
graph is connected, finite and simple. Its order is

    N = K + D + 126t,    t >= max(2,D).

It has exactly the original seed core counts through eight vertices. To prove
this, suppose a connected leafless subgraph F on at most eight vertices meets
the reservoir. A component of its reservoir part is either cyclic, requiring
at least twelve vertices, or a tree. In the tree case, every leaf must use a
seed attachment edge to have degree at least two in F. There must be at least
two distinct attachment sites, because each site has only one seed edge.
Their reservoir distance is at least eleven, again impossible within eight
vertices. An isolated reservoir vertex would likewise need two seed edges,
which no site has. Thus F lies wholly inside one seed. This also excludes
new barbell cores whose joining edges are bridges; a girth argument alone
would not have excluded those cores.

### 4. Equalize the two orders

Split a signed seed combination into its positive and negative collections.
For each side, K+D=4K-2E is even. Multiplying the seed combination by 63 makes
the two values congruent modulo 126. Choose a sufficiently large common N in
that residue class, then choose t independently on each side using the displayed
order formula. Both reservoir sizes meet t>=max(2,D). A side with no seeds is
simply a reservoir. Both graphs have equal order and the required core difference.

This proves the realization theorem. It is an explicit alternative to trying
to connect saturated cubic components: those components are exactly the
obstruction to the original seventh coordinate.

## Exact necessity and connected witnesses

The existing isolated observation vectors for Q0, Q1, S8_10, S8_11, Theta223,
and closed_diamond involve only nonsaturated seeds. Their girth-twelve padding
components can be discarded and the seed combinations attached to reservoirs.
The old equal-order certificate implies the necessary residue congruence, since
the old completion order K+127D is congruent to K+D modulo 126. No extra factor
63 is needed for these six retained recipes.

The replay checks the signed seed counts by a second edge-subset method and
evaluates every source-law coefficient at volumes one through eight. Each
result has zero lower difference and exactly its claimed isolated coordinate.
The resulting explicit connected recipe orders are:

| Isolated coordinate | Difference scale | Common vertex order |
|---|---:|---:|
| Q0 | 63 | 64,512 |
| Q1 | 63 | 145,152 |
| S8_10 | 21 | 137,172 |
| S8_11 | 63 | 1,598,940 |
| Theta223 | 1 | 1,666 |
| closed_diamond | 63 | 694,260 |

The large witnesses are exact generation recipes, not claims that millions of
vertices were exhaustively enumerated. The 1,666-vertex Theta223 pair is fully
materialized as two edge lists, checked for simplicity/cubicity/connectedness,
and independently re-enumerated for connected supports rooted at every seed
vertex through size eight. The reservoir exclusion just proved ensures those
roots capture every small leafless core. Its only nonzero core differences are
N_(6,956)=1 and N_(6,1881)=-1.

For any fewer than six rational linear observations, their six-column matrix
has a nonzero rational kernel vector. Take integer multiples of the six signed
seed relations so that their isolated coordinate scales realize a common
multiple of that kernel vector. Apply the reservoir construction to the
combined signed seeds. It preserves every core difference and equalizes orders;
the resulting connected pair has zero lower differences and identical measured
coefficients but a nonzero six-dimensional coordinate vector at volume eight.
Thus fewer than six
measurements fail on actual connected graphs, not merely on a formal span.

## Six-coefficient extraction and optimal panel

Form the 6-by-6 matrix whose columns are the six polynomial factors displayed
above and whose rows are selected q-degrees. Exhaustive exact rational search
over the fifteen nonzero even degrees 2 through 30 checks all C(15,6)=5,005
panels; 4,775 are invertible. The unique minimum for the unscaled,
equal-independent-absolute-error objective is

    degrees = (6,10,14,18,24,26)
    determinant = 74791080
    inverse infinity norm = 44191/19786 = 2.2334478924492065...

The certificate stores the exact rational inverse in the surviving coordinate
order. Multiply it by those six measured difference coefficients to recover
all six coordinates, append S8_12=0 in the original position, and reconstruct
the entire eighth difference. The coefficient outside the selected panel must
still be checked when validating a supplied complete polynomial.

This optimum is established for the connected six-dimensional realization
space. The older seven-panel optimum and norm remain correct for the original
seven-dimensional class. The norms concern different coordinate dimensions and
should not be presented as a like-for-like seven-coordinate comparison.

The new norm gives the exact worst-case coordinate error factor when every
selected difference coefficient has absolute error at most epsilon, conditional
on exact lower-order agreement and the connected observation model. No interval
arithmetic or approximate connectedness test is claimed.

## Replay, verification limits, and proposed repository changes

Run with Python 3, standard library only:

    cd replay
    python connected_check.py --optimize --enumerate-connected

This regenerates `connected_certificate.json`, both connected Theta223 edge
lists, all source-row/rank checks, the small-graph classification check,
the 92-isolator check, six symbolic connected recipes, and the exhaustive panel
optimization. `replay.log` records the successful run.

`existing_reader_replay.log` records a separate successful execution of the
unchanged original `vol8_reader_check.py --enumerate --optimize`, including
all 67 original isolated witnesses and the inherited seven-panel optimization.
Its full dependency tree remains in the upstream repository; the compact replay
directory packages only the dependencies needed for the new connected check.

This is an exact mathematical argument with integer/rational executable checks,
conditional on the already established volume-eight source law. It is not a
proof-assistant formalization. Large connected graph recipes are certified by
the reservoir argument and exact seed arithmetic, not by brute-force complete
height enumeration. Neither a small vertex bound nor bridgeless realization is
established here; the displayed orders are upper bounds from a deliberately
simple construction, not minima.

`proposed.patch` adds only the connected report, checker, certificate and two
Theta223 edge lists under `independent_checks/height_series/`. It changes no
existing proof, reader, documentation or workflow. A later integration can link
this result from `VOLUME8_READER.md` and add the replay to CI after review.
No branch, commit, PR or remote repository file was changed in this task.
