# Singularity development contract

This repository develops relational height populations and arithmetic visibility. Initial version: 0.1.0. Python core requires Python 3.10+ and the standard library only. Mathematical exposition must distinguish established background, proved propositions, exact finite computations, and conjectures. Do not claim global graph reconstruction, historical priority, or proof-assistant verification without evidence.

## Shared software interfaces

`singularity.graph.Graph(n, edges)` is an immutable graph with vertices `0,...,n-1`, normalized sorted simple undirected edges, and validation rejecting loops, duplicates, invalid endpoints. `degrees` is a tuple property; `energy(a)` returns the integer sum of squared edge differences; `laplacian()` returns integer rows. The graph may be disconnected; analytic results state connectedness separately.

`singularity.heights.weak_compositions(total, length)` yields tuples. `local_coefficients(graph, max_volume)` returns a list indexed by total volume, each entry a dict `{energy: multiplicity}`. `normalized_coefficients(graph, max_volume)` multiplies this formal x-series by `1-x**graph.n`. `marked_coefficients(graph, max_volume)` returns `{(volume, energy, span): multiplicity}` for profiles with minimum zero. Every count retains original labeled assignments.

`singularity.invariants.binary_cut_profile(graph)` returns `{(size, cut): multiplicity}`; `minimum_cut_profile(graph)` returns `(minimum_positive_cut, {side_size: multiplicity})` for connected graphs with at least two vertices; `laplacian_characteristic_polynomial(graph)` returns descending integer coefficients including the leading one.

`singularity.examples.GRAPHS` maps names `spectral_g`, `spectral_h`, `binary_g`, `binary_h` to Graph objects. Spectral edges: G=01,02,03,04,12,35,36; H=01,02,03,04,15,16,56. Binary-census edges: G=03,04,06,12,13,23,24,35; H=01,04,06,15,16,26,36,45.

Exact q-polynomials elsewhere use sparse dicts `{nonnegative_degree: Fraction}`. Analytics modules can coerce integer coefficients. No global graph information is gained by the Euler lift beyond the local series. Full marked B(x,q,z) contains the binary sector; recovering that sector from z=1 alone is not proved.

## Mathematical conventions

Volume means total integer height, not Euclidean volume. B uses min(a)=0; the span mark z is max(a) on those representatives. Nested level sets may repeat: S_h subseteq ... subseteq S_1. Pairwise edge energies remain pairwise even when the observations retain multiple nested boundaries. The first discrepancy at volume r gives a ratio singularity at real s=1/r after cancelling lower local coefficients. State local continuation and positive-real branches, not blanket meromorphic continuation.

## Ownership

Agents write only assigned files. Root integrates package metadata, README, bibliography, documentation build, repository workflow and release. Do not commit independently; root commits the combined result after tests. Manuscripts are substantive prose, definitions, examples, proofs and explanations, not repeated filler for word count.
