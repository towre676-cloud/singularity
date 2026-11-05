# Fixed-order bases and pure unit witnesses

November 4, 2026. This extends the preserved connectivity-minima result in
`final_bundle/RESULTS.md`. No repository file, branch, commit or PR was changed.

## A minimal common-order six-direction basis

There exist six pairs of connected bridgeless finite simple cubic graphs,
**all of order twenty**, agreeing in every height polynomial through volume
seven, with volume-eight coordinate difference vectors

| Pair | Q0 | Q1 | S8_10 | S8_11 | Theta223 | closed_diamond |
|---|---:|---:|---:|---:|---:|---:|
| 1 | -1 | 1 | 1 | 0 | 0 | 0 |
| 2 | -2 | -1 | 0 | 0 | 0 | 0 |
| 3 | -1 | 0 | 0 | 0 | 0 | 0 |
| 4 | 0 | -9 | -6 | -1 | 0 | 0 |
| 5 | 2 | 1 | 0 | 0 | 0 | 1 |
| 6 | -1 | 1 | 0 | 0 | -1 | 0 |

Convention: B minus A. The determinant of this integer 6-by-6 matrix is
**one**. The inverse is integral and is retained with all twelve complete edge
lists in `fixed20_certificate.json`.

This closes the earlier common-order question, not merely the vertex-ceiling
question. The previous complete catalogues through eighteen vertices have
span at most five, and no cubic graphs have odd order. Here those catalogues
were freshly re-enumerated by exact core counting and the established source
law, retaining all reference differences again. Consequently **twenty is the
smallest common order supporting six independent differences**, in both the
connected and bridgeless classes. The basis is also unimodular at that order.

Unimodularity means these six realized differences generate the full integer
coordinate lattice. It does not mean arbitrary integer vectors occur between
individual twenty-vertex graphs: that finite realization set is bounded. Nor
does span rank alone establish a measurement-count minimum on a bounded finite
graph class. The unbounded six- and four-measurement minima remain as proved
in the preceding bundle.

## Construction

Two controlled operations generate the new graphs.

* Triangle expansion replaces one cubic vertex by a triangle, attaching its
  three former neighbors to the three triangle vertices. Order increases by two.
* Two-edge expansion subdivides two distinct edges once each and joins the two
  new subdivision vertices. This also increases order by two. Adjacent selected
  edges are permitted, and the resulting edge list is checked for simplicity.

The discovery search tries paired operations on inherited agreeing graphs.
It does **not** assume either operation preserves lower-order equality. Every
candidate is evaluated with exact source-law features, and only matching
complete lower polynomials are retained. All six final pairs are then checked
independently by direct global weak-composition height enumeration, which uses
only their edge lists and integer edge energies. Each pair's simplicity,
cubicity and bridgelessness is checked separately by exact unit-capacity flows.
The twenty-vertex weld pair supplies the fourth row unchanged.

## Exact pure-unit minima already settled

A pure unit witness means the seven original invariant differences are zero
except for a single surviving coordinate, which is exactly +1 or -1. An
integral combination of several graph-pair differences is not such a witness.

| Coordinate | Exact smallest pure-unit order | Connectivity of an attaining pair |
|---|---:|---|
| Q0 | 18 | 3-edge-connected |
| Q1 | 18 | 3-edge-connected |
| Theta223 | 18 | 3-edge-connected |
| S8_10 | 20 | 3-edge-connected |

These minima hold in the connected class and therefore in its bridgeless and
3-edge-connected subclasses, since the attaining witnesses have the strongest
connectivity. All three eighteen-vertex witnesses were checked by the separate
integer direct-height program. The twenty-vertex S8_10 witness was checked the
same way. Complete edge lists are in `pure18_certificate.json` and
`S10_20_certificate.json`.

The complete eighteen-vertex catalogue has pure unit witnesses for Q0, Q1 and
Theta223, but none for S8_10, S8_11 or closed_diamond. There are no pure unit
witnesses for any surviving coordinate at orders four through sixteen. Counts
in `pure_n*.json` count pairs of distinct eighth-polynomial points within lower
agreement fibers, choosing one representative graph for an isospectral point;
they are not multiplicity counts of every graph pair.

## Exact bounded search method

For each retained connected leafless induced pattern through size eight, the
checker precomputes its contribution to the established reduced source law by
summing its connected leafless spanning edge subsets. Every relabeling is
retained in an exact mask table. Denominators are cleared with common scale 840.

For each cubic graph, short cycles seed a growth search over connected vertex
sets of size at most eight. This reaches every leafless connected support,
because every such support contains a cycle and can be grown from that cycle
by adjoining adjacent vertices. Sets are deduplicated, and supports failing
minimum degree two are discarded. Induced-pattern contributions reconstruct
all required logarithmic height coefficients. The vertex-order contribution
is constant within a catalogue and cancels in every difference.

Graphs are grouped by their complete coefficients at volumes three through
seven; volumes one and two are fixed by common cubic vertex order. Within each
fiber, a graph's eighth polynomial is shifted by exactly one of the six pure
factor polynomials and looked up in an exact ordered map. This tests **every
possible pure-unit pair**, not only differences from a chosen reference.

The current lower-order replay also retains the full reference differences in
`reference4.json` through `reference18.json`, regenerating the source-law data
that workspace maintenance had removed in the preceding pass. Their ranks and
counts match the inherited results. Selected witnesses are checked against the
independent global enumeration path. Arithmetic accumulation bounds explicitly
exclude signed-64-bit overflow at order twenty.

## Remaining-coordinate status

The two remaining pure-coordinate questions concern closed_diamond and S8_11,
which vanish entirely under 3-edge-connectivity. The exhaustive twenty-vertex
catalogue test is recorded separately in the final status section below.
The bounded surgical pools at twenty and twenty-two are discovery searches,
not exhaustive absence proofs. A failure to find a witness in such a pool
never establishes a lower bound.

Independently replayed constructive pure-unit upper bounds, from the general
bridgeless reservoir construction, are 13,184 vertices for closed_diamond and
25,932 for S8_11. Exact signed seed recipes are in `unit_upper_bounds.json`.
These are explicit sufficient orders, not optimality claims.

## Replay and scope

Run from the archive root, preserving the `open_work/` and `final_bundle/`
layout. Python scripts use the standard library; the independent height and
catalogue programs require a C++17 compiler. The pinned nauty source is retained
in `final_bundle/nauty_source.tar.gz`.

    python open_work/unit_tables.py
    g++ -O3 -std=c++17 open_work/unit_catalogue.cpp -o open_work/unit_catalogue
    python open_work/verify_fixed20.py
    python open_work/verify_units.py
    python open_work/fresh_bounds.py
    python open_work/unit_upper_bounds.py

The exact bounded catalogue invocation is

    open_work/unit_catalogue CATALOGUE.g6 open_work/weights.txt open_work/orbits.txt OUTPUT.json [REFERENCE_OUTPUT.json]

`verify_fixed20.py` compiles and uses a height enumerator that does not call the
source law. The final pure-unit verifier is packaged alongside it. The source
law remains an inherited mathematical dependency; these results are executable
integer/rational mathematics, not proof-assistant formalizations.

## Final complete twenty-vertex result

All **510,489** connected cubic graphs at order twenty were generated using the
pinned nauty code, by eight disjoint generator residues. The concatenated union
contains exactly that many distinct graph6 records. The manifest retains the
part counts, hashes and complete sorted-catalogue hash.

The exact unit query finds representatives for 58,040 Q0 point pairs, 42,373 Q1,
910 S8_10, and 7,643 Theta223 point pairs, but **zero S8_11 and zero
closed_diamond point pairs**. These are point-pair counts as defined above,
not counts with graph multiplicity. The full result is in `pure_complete20.json`.
Together with the smaller complete catalogues this checks **556,471** connected
cubic graphs through order twenty.

Therefore the remaining rigorous pure-unit bounds, in both connected and
bridgeless classes, are

| Coordinate | Proved lower bound | Explicit constructive upper bound |
|---|---:|---:|
| closed_diamond | 22 | 13,184 |
| S8_11 | 22 | 25,932 |

The surgical family of 5,220 twenty-two-vertex graphs, the additional 1,312 ring
words at order twenty-two, and 3,319 ring words at order twenty-four did not
supply the last two units. These searches do not establish nonexistence at
twenty-two or twenty-four. Exact minima for these two coordinates remain open.

This pass checkpoints the complete catalogue and newly regenerated lower-order
reference tables. No new raw search data are claimed lost. `proposed.patch`
adds a report and compact certificates only; all executable replay programs,
large catalogues and discovery records are delivered in this archive for review.
