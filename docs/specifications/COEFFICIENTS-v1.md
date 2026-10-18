# Coefficient semantics, version 1

**Identifier:** `singularity.coefficients/1`. **Status:** frozen by roadmap push P01 against software version 0.1.0. **Scope:** every public finite interface in `src/singularity/` and the JSON records it writes. A later change to any meaning below requires a new version of this document and a compatibility note; adding a new interface with a new meaning does not.

This document states what each number means. It is the reference for tests, certificates and manuscript statements. Proofs that already appear in the monograph are cited by their result identifiers; the short proofs given here are the ones the specification itself depends on.

## 1. Graphs

A **graph** is a finite simple undirected loopless graph on the labeled vertex set \(V=\{0,\ldots,n-1\}\), \(n\ge1\). Labels are part of the input. No quotient by graph automorphisms is taken anywhere in the core: a permutation of labels is a bijection between populations, never a division of multiplicities.

`Graph(n, edges)` accepts any iterable of two-element sequences. It rejects, with `ValueError`: \(n<1\); an edge without exactly two endpoints; a negative endpoint or one \(\ge n\); a loop; a repeated edge, including the same pair in reverse order. It rejects with `TypeError` a non-integer \(n\) or endpoint, and Booleans (Python `True` is not accepted as `1`). The stored edge tuple is canonical: each pair is written \((\min,\max)\) and pairs are sorted. Disconnected graphs and isolated vertices are allowed.

Serialization is `{"n": n, "edges": [[u, v], ...]}` with canonical edges (`Graph.to_dict`). `Graph.from_dict` accepts any edge order and canonicalizes it; certificate readers additionally require the canonical form (Section 9).

## 2. Heights, volume, energy and span

A **profile** is \(a\in\mathbb Z_{\ge0}^n\), indexed by the original labels. For a profile,
\[
|a|=\sum_i a_i\ \text{(volume)},\qquad
E_G(a)=\sum_{\{u,v\}\in E}(a_u-a_v)^2\ \text{(energy)},\qquad
h(a)=\max_i a_i-\min_i a_i\ \text{(span)}.
\]
Volume is total integer height. Energy is the squared-difference form \(a^\top\Delta_G a\); it is not the absolute-difference cut sum \(\sum|a_u-a_v|\).

`Graph.energy(a)` evaluates the same quadratic form on **signed** integer tuples, because translation and difference arguments use negative heights. It requires exactly \(n\) integers and rejects Booleans. Every population and coefficient interface below uses nonnegative heights only.

## 3. The three series

\[
L_G(x,q)=\sum_{a\ge0}x^{|a|}q^{E_G(a)},\qquad
B_G(x,q)=\sum_{a\ge0,\ \min a=0}x^{|a|}q^{E_G(a)},\qquad
\mathcal B_G(x,q,z)=\sum_{a\ge0,\ \min a=0}x^{|a|}q^{E_G(a)}z^{\max a}.
\]
\([x^mq^e]L_G\) is the number of labeled profiles with volume \(m\) and energy \(e\). \([x^mq^ez^h]\mathcal B_G\) is the number of labeled minimum-zero profiles with volume \(m\), energy \(e\) and span \(h\); on minimum-zero profiles the span equals \(\max a\). All three are elements of \(\mathbb Z_{\ge0}[q][[x]]\) (with \(z\) a further polynomial variable in each \(x\)-coefficient); each coefficient counts a finite set (SNG-F01).

**Proposition (coefficient form of \(B=(1-x^n)L\)).** For every \(m\ge0\) and \(e\ge0\),
\[
[x^mq^e]B_G=[x^mq^e]L_G-[x^{m-n}q^e]L_G,
\]
where the second term is zero for \(m<n\).

*Proof.* Let \(P_m^e\) be the set of profiles of volume \(m\) and energy \(e\), and \(N_m^e\subseteq P_m^e\) those with minimum zero. The map \(a\mapsto a+\mathbf 1\) sends \(P_{m-n}^e\) into \(P_m^e\setminus N_m^e\): it adds \(n\) to the volume, leaves every difference \(a_u-a_v\) and hence the energy unchanged, and produces minimum at least one. It is injective because \(a+\mathbf1=b+\mathbf1\) forces \(a=b\). It is surjective onto \(P_m^e\setminus N_m^e\) because a profile with minimum at least one has the preimage \(a-\mathbf1\ge0\), whose volume is \(m-n\) and whose energy is \(e\). Hence \(|P_m^e|=|N_m^e|+|P_{m-n}^e|\), and \(P_{m-n}^e=\varnothing\) when \(m<n\). \(\square\)

Iterating the bijection gives the inverse \([x^m]L_G=\sum_{t\ge0}[x^{m-nt}]B_G\), a finite sum of nonnegative counts. The same argument with the span mark, which translation also preserves, gives \(\mathcal B_G=(1-x^n)\widetilde L_G\) (SNG-F02). The proposition uses one global translation by \(\mathbf1\), whatever the number of components; Section 6 explains why.

## 4. Truncation

Every coefficient interface takes an inclusive bound `max_volume` \(=M\ge0\) and returns exactly the coefficients of \(x^0,\ldots,x^M\). Those coefficients are exact and complete: they do not depend on \(M\) beyond their own index (enlarging \(M\) appends rows and never changes earlier rows), because every term of \(L_G\) has a nonnegative volume exponent. A truncated result is a **finite prefix** of a formal series. Agreement of two prefixes is not equality of the series, and a prefix certifies nothing about coefficients above \(M\). The multiplication by \(1-x^n\) is valid on prefixes because row \(m\) of \(B\) uses only rows \(m\) and \(m-n\) of \(L\).

Bounded-height interfaces (Section 8) have a second, different truncation: the height box \(\{0,\ldots,H\}^n\). A box count at volume \(m\) equals the unrestricted count exactly when \(H\ge m\), since a profile of volume \(m\) has every height at most \(m\).

## 5. Representations

| Object | Python value | Meaning |
|---|---|---|
| Local or normalized prefix | `list[dict[int,int]]` of length \(M+1\) | Row \(m\) maps energy \(e\) to the count \([x^mq^e]\). Keys ascend; zero counts are omitted; a row may be `{}`. |
| Marked prefix | `dict[tuple[int,int,int],int]` | Key `(volume, energy, span)` maps to a positive count, sorted, minimum-zero profiles only. |
| Bounded histogram | `dict[tuple[int,int],int]` | Key `(volume, energy)` within a height box and optional volume cap. |
| Rational \(q\)-polynomial | `dict[int, Fraction]` | Sparse, nonnegative exponents, zero coefficients removed. |
| JSON count row | `[[energy, count], ...]` | Strictly increasing energies, positive integer counts. |
| JSON marked row | `[volume, energy, span, count]` | Sorted lexicographically, positive counts. |
| JSON rational polynomial | `[[degree, numerator, denominator], ...]` | Unique degrees, nonzero numerator, positive denominator. |

Integers are exact Python integers. Booleans are rejected wherever an integer is required. No floating-point value participates in a count.

## 6. Disconnected graphs: one global translation versus one per component

Common translation \(a\mapsto a+t\mathbf1\) is the only translation that `normalized_coefficients`, `marked_coefficients`, `HeightPopulation(min_zero=True)`, forest `min_zero=True`, chains and certificates remove. On a disconnected graph each component \(C\) admits its own translation \(a\mapsto a+t\mathbf1_C\), which also preserves energy. The quotient by all component translations is a **different population**. It is exposed separately as `componentwise_normalized_coefficients`, which keeps the profiles whose minimum is zero on every component. It is the product of the components' \(B\) series, whereas the global quotient satisfies SNG-F19:
\[
B_{G\sqcup H}=\frac{1-x^{k+\ell}}{(1-x^k)(1-x^\ell)}B_GB_H .
\]

**Worked example.** Let \(G=K_2\sqcup K_1\), edges \(\{0,1\}\), isolated vertex \(2\). Through volume four:

| \(m\) | global \([x^m]B_G\) | componentwise | profiles present only globally |
|---:|---|---|---|
| 0 | `{0: 1}` | `{0: 1}` | — |
| 1 | `{0: 1, 1: 2}` | `{1: 2}` | \((0,0,1)\) |
| 2 | `{0: 2, 1: 2, 4: 2}` | `{4: 2}` | \((1,1,0),(0,0,2),(1,0,1),(0,1,1)\) |
| 3 | `{0: 1, 1: 4, 4: 2, 9: 2}` | `{9: 2}` | seven profiles |
| 4 | `{0: 2, 1: 2, 4: 4, 9: 2, 16: 2}` | `{16: 2}` | ten profiles |

The profile \((1,1,0)\) has global minimum zero, while its component \(\{0,1\}\) is entirely positive. It belongs to \(B_G\) and not to the componentwise population. The two quotients coincide exactly when the graph is connected; for \(n\le4\) and volume at most three the test suite checks this equivalence on all 75 labeled graphs. Nothing in the core silently replaces the global factor \(1-x^n\) by a product of component factors. Independent component translations require the separate bookkeeping above.

## 7. Small exact dictionaries

| Input | Call | Exact output |
|---|---|---|
| `Graph(1)` | `local_coefficients(g, 3)` | `[{0: 1}, {0: 1}, {0: 1}, {0: 1}]` |
| `Graph(1)` | `normalized_coefficients(g, 3)` | `[{0: 1}, {}, {}, {}]` |
| `Graph(1)` | `marked_coefficients(g, 3)` | `{(0, 0, 0): 1}` |
| `Graph(2, [(0, 1)])` | `marked_coefficients(g, 3)` | `{(0,0,0): 1, (1,1,1): 2, (2,4,2): 2, (3,9,3): 2}` |
| any graph | any coefficient call with `max_volume=0` | the single zero profile: `[{0: 1}]` or `{(0, 0, 0): 1}` |

The coefficient 2 for \(K_2\) records the two labeled profiles \((h,0)\) and \((0,h)\); the endpoint swap does not halve it.

## 8. Other finite interfaces

**Populations.** `HeightPopulation(graph, ...)` is the set of labeled nonnegative tuples satisfying every supplied exact value or upper bound (`volume`, `max_volume`, `energy`, `max_energy`, `span`, `max_span`, `max_height`), with `min_zero=True` by default. Span is \(\max-\min\). Construction fails unless an explicit certificate bounds every height: a height or volume bound, a min-zero span bound, a connected min-zero energy bound through \(h^2\le D\,E\) for diameter \(D\), or \(n=1\) with min-zero. `count`, `rank`, `unrank` and iteration use lexicographic order on original tuples. Schema: `singularity-height-population/1`.

**Forest transfer.** `bounded_height_histogram(forest, H, max_volume=None, min_zero=False)` counts labeled profiles in \(\{0,\ldots,H\}^n\) with volume at most `max_volume` (default \(nH\)), keyed by `(volume, energy)`. With `min_zero=True` it subtracts the all-positive profiles, \(x^n\) times the height-\((H-1)\) box (global translation, Section 6). Graphs with cycles are rejected. `brute_bounded_height_histogram` has the same meaning for every graph. `histogram_coefficients` converts to the prefix interface. `root_messages` returns, for each component rooted at its least original label, the list indexed by root height \(t\) of `(volume, energy)` histograms of that component with \(a_{\text{root}}=t\). `transfer_statistics` reports height states, sparse message support and integer bit size separately. `marked_forest_coefficients(forest, M, max_span=None)` has exactly the meaning of `marked_coefficients` (restricted to spans at most `max_span`), computed by bounded-box subtraction (SNG-F25).

**Tree decompositions.** `TreeDecomposition(bags, edges, root)` holds bags of original labels, undirected tree edges between bag indices and a root bag; its JSON form is `{"bags": [[...]], "edges": [[i, j]], "root": r}` with optional `"schema": "singularity.tree-decomposition/1"`. `check_decomposition` lists violations of vertex coverage, edge coverage, connected occurrence of each vertex, and the tree property. `decomposition_histogram` and `marked_decomposition_coefficients` have exactly the meanings of `bounded_height_histogram` and `marked_coefficients` for every graph with a valid decomposition (SNG-F26); `decomposition_statistics` reports width, bag assignments, support and bit size. `elimination_decomposition` and `forest_decomposition` construct valid decompositions.

**Chains.** `chain_marked_coefficients(graph, M)` has exactly the meaning of `marked_coefficients` but is generated from weakly nested level sets (SNG-F09, SNG-F10). `level_chains(n, M)` yields chains as tuples of bit masks over original labels; the empty chain is the zero profile. `chain_normalized_coefficients` and `chain_local_coefficients` are its projections to \(B\) and \(L\).

**Closed low-volume formulas.** `low_volume_local`, `low_volume_normalized` and `low_volume_marked` return the same objects as the enumerators for volumes \(0..3\), computed from degree, ordered-pair and induced-triple statistics (SNG-F14). `regular_low_volume_local(n, d, T)` gives \(C_0..C_3\) of a \(d\)-regular graph with \(T\) triangles.

**Weighted graphs.** `WeightedGraph(masses, edges)` has positive integral vertex masses \(m_i\) and positive integral edge weights \(w_{uv}\), with parallel edges summed. Volume is \(\sum m_ia_i\) and energy \(\sum w_{uv}(a_u-a_v)^2\). `contract` imposes equal heights by merging vertices, summing masses and parallel weights. `weighted_coefficients` returns rows \(0..M\) by weighted volume, enumerating a box of explicitly budgeted size. No normalization is offered there: a common translation changes weighted volume by \(\sum m_i\), not \(n\). The unweighted API is unchanged.

**Primitive profiles.** `primitive_marked_coefficients` counts minimum-zero profiles with \(\gcd(a)=1\) and volume \(\ge1\), by `(volume, energy, span)`, using Möbius inversion of the dilation \(a\mapsto da\) (volume \(\times d\), energy \(\times d^2\), span \(\times d\)). `recompose_primitive_counts` inverts it and restores the zero profile.

**Formal algebra.** Series in `polynomials` are lists of rational \(q\)-polynomials indexed by \(x\)-degree. `euler_exponents(L)` returns the unique \(b_n\in\mathbb Q[q]\) with \(L=\prod_n(1-x^n)^{-b_n}\) through the prefix; these are formal exponents, not integer multiplicities. Coefficients lie in \(\mathbb Q[q]\) as reduced `Fraction`s. `series_log` requires constant term exactly \(1\), `series_exp` constant term \(0\), and `series_inverse` a nonzero rational constant; every transform of a prefix through \(N\) returns a prefix through \(N\) whose rows depend only on input rows up to the same index, and `euler_exponents` sets \(b_0=0\). In JSON an exponent is a rational polynomial (Section 5). `euler_exponents_mobius` computes the same \(b_n\) by divisor inversion and `recompose_euler` multiplies generalized-binomial factors without logarithms; these are independent checks. The integral bidegree (plethystic) transform of SNG-A08 is a different object and is not implemented by these functions. `first_difference(left, right)` returns the first index and signed polynomial difference within the common prefix, or `None`, which means only that the prefix did not distinguish them.

**Arithmetic lift.** `dirichlet_coefficients(graph, N)` returns, for each \(1\le k\le N\), the \(q\)-polynomial \([k^{-s}]\prod_pL_G(p^{-s},q)\), assembled multiplicatively from the same local coefficients. It introduces no graph information beyond \(L_G\).

**Root-of-unity specialization.** For a primitive \(\ell\)-th root \(\zeta\), `residue_numerator(graph, ℓ)` returns \(N\) with \(L_G(x,\zeta)=N(x)/(1-x^\ell)^n\), coefficients in \(\mathbb Z[t]/\Phi_\ell(t)\) written constant-first, by enumerating the residue cube \(\{0,\ldots,\ell-1\}^n\) under a work budget. `remote_coefficient` evaluates one coefficient at an arbitrary index from \(N\). A budget refusal is not a mathematical statement.

**Volume congruence filters.** `volume_residue(series, m, a)` keeps the rows \(v\equiv a\pmod m\) of a prefix and empties the others; the residue is normalized to \(0..m-1\) and the prefix length is kept. `character_average` returns the same prefix computed by the exact character average of SNG-F27 in \(\mathbb Z[t]/\Phi_m(t)\), with rational coefficients kept as `Fraction`. `residue_class_coefficients(graph, R, m, a)` counts labeled profiles of volume \(\le R\) in that class directly. These act on the volume variable \(x\), not on \(q\).

**Invariants.** `binary_cut_profile` counts all \(2^n\) binary profiles by `(size, cut)`; restricted to \(0<\text{size}<n\) it is the span-one sector of \(\mathcal B_G\) (SNG-F11). `laplacian_characteristic_polynomial` is exact \(\det(tI-\Delta_G)\). `invariants.first_difference(G, H, M)` compares local prefixes of two graphs.

## 9. Certificates

The authoritative portable format is `singularity.certificate/1` (`certificates.py`, retained files under `results/certificates/`). The roadmap name `relational-height/1` (P03) is a superseded planning label for the same concept, not a second format: decision D007 records this. Packets carry a canonical graph source and its SHA-256 digest (integrity only, not authentication or proof), `max_volume`, local, normalized and marked prefixes in the JSON forms of Section 5, `profile_count` \(=\binom{M+n}{n}\), rational Euler exponents, fixed identity declarations and an optional comparison graph with its first difference and declared factorization. Replay recomputes every claim independently under an explicit work budget (chapter 12 and `docs/IMPLEMENTATION.md`) and rejects any packet whose fields are malformed, non-canonical or unequal to the recomputation, regardless of digests or flags.

## 10. Invalid input

Integer parameters reject Booleans, non-integers and values below their minimum (`max_volume`, heights, bounds: \(\ge0\); `n`, orders, masses: \(\ge1\)). Coefficient interfaces accept only a `Graph`. A finite population without a bound is refused rather than truncated. Enumeration budgets (`max_profiles`) raise `ValueError` before work starts. None of these refusals is a counterexample.

## 11. Acceptance receipt: public API crosswalk

| Interface | Section | Regression evidence |
|---|---|---|
| `Graph`, `to_dict`, `from_dict`, `relabel`, `components`, `connected`, `degrees`, `laplacian`, `cut_size` | 1 | `tests/test_core.py`: `GraphTests` |
| `Graph.energy` (signed), `validate_heights` | 2 | `GraphTests.test_signed_energy_and_validation` |
| `weak_compositions`, `local_coefficients` | 3, 4 | `HeightTests.test_weak_compositions_against_direct_product`, `test_local_normalized_and_marked_against_direct_products` |
| `normalized_coefficients`, `normalize_local_coefficients`, `normalize_heights` | 3, 4 | same; `SemanticsTests.test_zero_volume_singleton_and_inclusive_truncation` |
| `marked_coefficients`, `threshold_sets`, `nested_energy` | 3, 7 | `HeightTests.test_energy_shift_nested_decomposition_all_small_graphs`, `test_binary_sector_and_complement_all_small_graphs` |
| `componentwise_normalized_coefficients` | 6 | `SemanticsTests.test_disconnected_global_versus_componentwise_translation`, `test_quotients_agree_exactly_for_connected_graphs` |
| Automorphism multiplicity | 1, 7 | `SemanticsTests.test_automorphisms_do_not_divide_multiplicities`, `HeightTests.test_relabel_invariance_all_small_graphs` |
| `chains.*` | 8 | `tests/test_chains.py`; `results/chain_agreement.json` |
| `lowvolume.*` (closed formulas through volume 3) | 3, 8 | `tests/test_low_volume.py`; `results/pair_acceptance.json` |
| `decomposition.*` | 8 | `tests/test_decomposition.py` |
| `congruence.*` | 8 | `tests/test_congruence.py` |
| `HeightPopulation` | 8 | `tests/test_population.py` |
| `bounded_height_histogram`, `brute_bounded_height_histogram`, `histogram_coefficients`, `root_messages`, `transfer_statistics`, `marked_forest_coefficients` | 4, 8 | `tests/test_transfer.py`, including `test_global_shift_subtraction_on_disconnected_forest` |
| `WeightedGraph`, `weighted_coefficients` | 8 | `tests/test_conductor_weighted.py` |
| `primitive_*` | 8 | `tests/test_primitive.py` |
| `polynomials.*`, `euler.*` | 5, 8 | `tests/test_analytics.py` |
| `dirichlet_coefficients`, `prime_valuations`, `valuation_energy` | 8 | `tests/test_arithmetic.py` |
| `CyclotomicRing`, `residue_numerator`, `remote_coefficient` | 8 | `tests/test_conductor_weighted.py`; `results/conductor_example.json` |
| `binary_cut_profile`, `minimum_cut_profile`, `laplacian_characteristic_polynomial`, `invariants.first_difference` | 8 | `HeightTests`, `DiscoveryTests` |
| `build_certificate`, `replay_certificate`, `parse_certificate` | 5, 9 | `tests/test_certificates.py`, `tests/test_analytics.py`; `results/certificates/` |
| CLI `python -m singularity` | all | `CliIntegrationTests` |

## 12. Compatibility note

Version 1 records the behaviour of release 0.1.0; no existing function changed meaning. P01 added `componentwise_normalized_coefficients` (Section 6) to make the second quotient executable, and P02 added the `chains` module with the same output meaning as `marked_coefficients`. Retained fixtures, graph labels and the first discrepancies at volumes 2, 3 and 4 for the spectral, binary-census and cube–Möbius pairs are unchanged.
