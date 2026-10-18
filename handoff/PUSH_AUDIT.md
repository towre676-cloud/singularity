# Original 36-push audit and acceptance ledger

Baseline: `89fb96d25bef0463e41feb74d987b464e5fd534f` (version 0.1.0), audited 2026-10-17; acceptances through 2026-10-18 are recorded below and in the session log. The original sequence is retained in [PUSHES.md](../docs/development/PUSHES.md). The executable ledger is [push_status.json](push_status.json). All P01–P36 identifiers and original dependency edges are preserved.

**The 36 pushes are the development plan, not 36 completed commits.** The initial release implemented substantial parts of several pushes ahead of their acceptance sequence. This audit separates reusable work from closure. No entry is marked complete because the original dependency and acceptance gates have not all been evidenced. The absence of a complete label does not mean the corresponding code or prose proof is absent.

## What Claude Code should do first

Close the finite contract in P01; add the genuinely independent chain generator in P02; then audit and close P03 using the existing certificate engine. Those three steps unlock acceptance of much of the existing work. Do not start by replacing forest transfer, Euler extraction or conductor arithmetic. P04/P05/P06/P09/P10/P18/P23/P26 contain substantive existing deliverables to accept or extend.

Use original dependencies as **completion gates**. Preparatory research may proceed in parallel; an acceptance claim must either satisfy the original gate or record an explicit scope/dependency amendment. In particular, P35 originally requires P33 kernel verification even though a paper draft already exists. Publishing a draft does not silently waive that requirement.

## Status meanings

| Status | Meaning | Push count |
|---|---|---:|
| `planned` | The target is specified, but its substantive deliverable is absent. Preparatory work can proceed while dependencies remain open. | 4 |
| `partial` | Some substantive deliverables exist, but important own acceptance requirements remain unsatisfied. | 4 |
| `implemented_pending_acceptance` | The central target is implemented or proved in exposition, but explicit acceptance checks, dependency closure or publication bookkeeping remain outstanding. | 1 |
| `blocked` | The central deliverable is absent and a named prerequisite must be established before its original acceptance criterion can be evaluated. | 7 |
| `complete` | All original acceptance requirements and declared dependencies have evidence-backed closure. The baseline audit gave it to no push; see the session log for later acceptances. | 20 |

**Effort** estimates remaining work for the push itself, excluding prerequisites: S = contained addition or acceptance work; M = substantial implementation or proof work; L = structural or formal research with uncertain resolution. These are scope judgments, not promised durations. **Priority** 0–3 orders suggested attention; smaller comes first and never overrides dependencies.

## Baseline facts that prevent wasted work

| Existing foundation | Evidence | What is still missing |
|---|---|---|
| Weak-composition coefficients, normalized coefficients, marked sectors | `src/singularity/heights.py`; `tests/test_core.py` | A second generator whose primary objects are level chains |
| Nested energy evaluation and certificate replay | `src/singularity/heights.py`; `src/singularity/certificates.py` | Deriving threshold sets from a composition-generated tuple is not independent chain enumeration |
| Portable certificate packets | `src/singularity/certificates.py`; `results/certificates/` | Full malformed-input acceptance matrix, P02 integration and recorded schema reconciliation |
| Exact forest messages and global minimum-zero subtraction | `src/singularity/transfer.py`; `tests/test_transfer.py` | Exact-span assembly, state/support instrumentation and bounded-separator extension |
| Exact logarithms, inverse series, ordinary Euler exponents and recomposition | `src/singularity/polynomials.py`; `src/singularity/euler.py` | Acceptance closure; ordinary exponents remain distinct from the prose bidegree transform |
| Root-of-unity conductor and remote coefficients | `src/singularity/conductor.py`; `tests/test_conductor_weighted.py` | Volume filters, singular Gauss-sum classification and explicit acceptance receipts |
| Explicit analytic tails | `docs/chapters/07_visibility_singularities.md`; `src/singularity/arithmetic.py` | Certified finite-prime experiments and an explicit complex neighborhood |
| Complete connected graph census through order six | `scripts/census.py`; `results/small_census.json` | Hashed input manifest, independent count reconciliation, all memberships, spectral partitions and witnesses |
| Manuscript proofs and Python replay | `docs/THEOREM_INDEX.md`; `results/validation.json` | No proof-assistant project or kernel-verified theorem is present |

### Certificate schema discrepancy: resolve explicitly

P03 originally proposed `relational-height/1`. The code, fixtures and implementation chapter instead use **`singularity.certificate/1`**. The actual versioned format is authoritative for replay. Do not rename fixture formats or introduce an incompatible second reader merely to match stale planning text. Record an explicit roadmap amendment or a deliberate versioned migration, retain backwards compatibility as needed, and test the decision. This audit records the discrepancy; it does not silently alter P03.

### Mathematical claim boundaries

Manuscript proofs are mathematical exposition. Passing Python tests or replaying a certificate does not create a proof-assistant theorem. The n≤6 census is finite evidence, not complete graph reconstruction. A retained collision has a cutoff; a nonzero coefficient discrepancy is a conclusive separation witness. The latest chat's terminal-interface and unbounded delayed-visibility proposals are new research targets. They do not count as completed P12/P32 or replace the original roadmap without an explicit decision.

## All 36 pushes at a glance

| ID | Original target | Status | Dependencies | Effort | Priority |
|---|---|---|---|---|---:|
| [P01](#p01) | Freeze the coefficient semantics | `complete` | Initial release | S | 0 |
| [P02](#p02) | Add independent level-chain enumeration | `complete` | P01 | M | 0 |
| [P03](#p03) | Publish portable coefficient certificates | `complete` | P01, P02 | M | 0 |
| [P04](#p04) | Give the spectral pair a short coefficient proof | `complete` | P03 | S | 1 |
| [P05](#p05) | Explain the binary-census separation | `complete` | P02, P03 | S | 1 |
| [P06](#p06) | Derive universal low-volume formulas | `complete` | P04, P05 | S | 1 |
| [P07](#p07) | Formalize translation normalization | `planned` | P01 | M | 1 |
| [P08](#p08) | Formalize the nested-level energy identity | `blocked` | P07 | L | 2 |
| [P09](#p09) | Implement bounded-height tree messages | `complete` | P02 | S | 1 |
| [P10](#p10) | Prove safe volume truncation | `complete` | P09 | S | 1 |
| [P11](#p11) | Recover span by bounded-box subtraction | `complete` | P09, P10 | S | 1 |
| [P12](#p12) | Extend messages to bounded separators | `complete` | P10, P11 | L | 1 |
| [P13](#p13) | Classify the first positive-energy layer | `implemented_pending_acceptance` | P06, P08 | S | 2 |
| [P14](#p14) | Compute the nested-pair census | `planned` | P05, P08 | M | 1 |
| [P15](#p15) | Separate lattice information from chamber information | `partial` | P08, P14 | L | 2 |
| [P16](#p16) | Test Whitney switches systematically | `blocked` | P15 | M | 2 |
| [P17](#p17) | Add exact volume congruence filters | `complete` | P03 | S | 2 |
| [P18](#p18) | Prove root-of-unity rationality in energy | `complete` | P03, P17 | S | 2 |
| [P19](#p19) | Analyze finite quadratic Gauss sums | `complete` | P18 | M | 2 |
| [P20](#p20) | Build the disjoint order-chamber formula | `complete` | P02, P06 | M | 2 |
| [P21](#p21) | Relate constrained heights to order polytopes | `complete` | P20 | M | 2 |
| [P22](#p22) | Establish one genuine reciprocity statement | `planned` | P21 | L | 3 |
| [P23](#p23) | Implement formal logarithmic extraction | `complete` | P03 | S | 1 |
| [P24](#p24) | Determine exceptional energy parameters | `complete` | P23 | M | 1 |
| [P25](#p25) | Organize successive visibility levels | `complete` | P23, P24 | M | 1 |
| [P26](#p26) | Make analytic remainder bounds explicit | `complete` | P25 | S | 1 |
| [P27](#p27) | Produce controlled real singularity experiments | `planned` | P26 | M | 1 |
| [P28](#p28) | State the available complex domain exactly | `partial` | P26 | M | 2 |
| [P29](#p29) | Specify a complete finite graph census | `complete` | P03 | S | 1 |
| [P30](#p30) | Measure collision classes across invariants | `partial` | P12, P14, P29 | M | 2 |
| [P31](#p31) | Resolve targeted collisions structurally | `blocked` | P16, P30 | L | 2 |
| [P32](#p32) | Seek a separation bound for one graph family | `blocked` | P06, P12, P31 | L | 2 |
| [P33](#p33) | Verify concrete coefficient certificates in a kernel | `blocked` | P07, P08, P23 | L | 3 |
| [P34](#p34) | Formalize the visibility comparison boundary | `blocked` | P26, P33 | L | 3 |
| [P35](#p35) | Release the first focused manuscript | `partial` | P04, P05, P26, P27, P33 | M | 3 |
| [P36](#p36) | Choose the second paper from actual results | `blocked` | P19, P22, P31, P32, P35 | L | 3 |

## Push-by-push evidence and next actions

### P01

**Freeze the coefficient semantics.** Status: `complete` (accepted 2026-10-17). Dependencies: initial release.

**Accepted evidence:** [docs/specifications/COEFFICIENTS-v1.md](../docs/specifications/COEFFICIENTS-v1.md) (identifier `singularity.coefficients/1`) fixes every public finite interface, truncation convention and serialization, proves the coefficient form of \(B=(1-x^n)L\) by an explicit bijection, and publishes zero-volume and singleton dictionaries. Section 6 works \(K_2\sqcup K_1\) through volume four, global versus componentwise translation, and states that these are different quotients; `componentwise_normalized_coefficients` in [heights.py](../src/singularity/heights.py) makes the second quotient executable. Section 11 is the API-to-test crosswalk. `SemanticsTests` in [tests/test_core.py](../tests/test_core.py) checks the published dictionaries, the product and SNG-F19 relations, and that the two quotients agree exactly for connected graphs on all 75 labeled graphs with at most four vertices.

**Remaining:** none for P01. A change of meaning requires `COEFFICIENTS-v2`.

### P02

**Add independent level-chain enumeration.** Status: `complete` (accepted 2026-10-17). Dependencies: P01.

**Accepted evidence:** [src/singularity/chains.py](../src/singularity/chains.py) generates weakly nested chains with repeated levels as bit masks and charges SNG-F10 incrementally; it calls neither weak compositions nor `Graph.energy`. Proposition SNG-F21 in [chapter 3](../docs/chapters/03_nested_heights.md) proves the volume-pruned search exhaustive and disjoint. [tests/test_chains.py](../tests/test_chains.py) compares complete marked histograms on all 75 labeled graphs on 1–4 vertices through volume 6 (4,713 cells, 13,019 profiles) and shows that forbidding repeats loses exactly the gap profiles. [results/chain_agreement.json](../results/chain_agreement.json) extends the exact comparison to all 1,099 labeled graphs on 1–5 vertices through volume 6: 142,416 cells, 479,963 profiles, no disagreement, 3.8 s.

**Remaining:** none for P02. The comparison is finite evidence on its declared population.

### P03

**Publish portable coefficient certificates.** Status: `complete` (accepted 2026-10-17, with roadmap amendment D007). Dependencies: P01, P02.

**Accepted evidence:** `singularity.certificate/1` remains authoritative; the roadmap name `relational-height/1` is rejected with a superseded-name diagnostic. `parse_certificate` in [certificates.py](../src/singularity/certificates.py) checks structure before arithmetic; replay uses a stars-and-bars route and the P02 chain route, with both counted in the budget. [tests/test_certificates.py](../tests/test_certificates.py) is the adversarial matrix: nine edge defects in both graph fields, malformed degrees and duplicate terms in count, marked and rational rows, field/type/format errors, altered counts with digest and flags unchanged, an injected chain-route disagreement, budget accounting, replay of every retained packet, and agreement of certified first differences with [results/exact_examples.json](../results/exact_examples.json). A fourth packet, [regular_cube_mobius.json](../results/certificates/regular_cube_mobius.json), certifies the volume-four cube–Möbius discrepancy.

**Remaining:** none for P03. Large-integer JavaScript transport remains a possible future schema extension.

### P04

**Give the spectral pair a short coefficient proof.** Status: `complete` (accepted 2026-10-18). Dependencies: P03.

**Accepted evidence:** Chapter 9 now proves SNG-E005 from degree pairs: volumes 0, 1 and the 2e_i sector cancel by the common degree sequence; the e_i+e_j sector gives (q^-2-1)(J_G-J_H) with J_G-J_H=2q^4(1-q)^2 read from an explicit edge-degree-type table. The discrepancy is explained by degree mixing (assortativity), not a higher-order effect.

**Evidence files:** [docs/chapters/09_exact_examples.md](../docs/chapters/09_exact_examples.md); [docs/chapters/04_observation_hierarchy.md](../docs/chapters/04_observation_hierarchy.md); [src/singularity/lowvolume.py](../src/singularity/lowvolume.py); [src/singularity/examples.py](../src/singularity/examples.py); [tests/test_low_volume.py](../tests/test_low_volume.py); [tests/test_core.py](../tests/test_core.py); [results/pair_acceptance.json](../results/pair_acceptance.json); [results/exact_examples.json](../results/exact_examples.json); [results/certificates/spectral.json](../results/certificates/spectral.json).

**Criteria receipt:**

- *classify every profile type at volumes zero, one and two*: chapter 9 proof; lowvolume.pattern_sectors; FixedPairAcceptanceTests.test_spectral_pair_degree_pair_proof.
- *compare exact Laplacian characteristic polynomials*: DiscoveryTests.test_spectral_pair (integer Newton identities, Leibniz determinant oracle).
- *match both enumerators*: results/pair_acceptance.json: closed formulas, weak compositions and level chains agree through volume 2; marked difference lies entirely in span 1.
- *certificate*: results/certificates/spectral.json replays valid with both routes.

**Commands:** `PYTHONPATH=src python -m unittest tests.test_low_volume tests.test_core -v`; `PYTHONPATH=src python scripts/reproduce.py --check`.

**Remaining:** none for P04.

### P05

**Explain the binary-census separation.** Status: `complete` (accepted 2026-10-18). Dependencies: P02, P03.

**Accepted evidence:** The retained receipt holds the complete binary cut-volume table of both graphs (all 128 assignments each), the pattern sectors through volume three, and the full marked difference by both enumerators. Chapter 9 accounts for every coefficient below volume three and every non-2e_i+e_j sector at volume three, identifies the 42 ordered 2e_i+e_j profiles as the nested chain {i,j} >= {i}, and records that the graphs differ in joint degree matrix and spectrum.

**Evidence files:** [docs/chapters/09_exact_examples.md](../docs/chapters/09_exact_examples.md); [src/singularity/lowvolume.py](../src/singularity/lowvolume.py); [src/singularity/invariants.py](../src/singularity/invariants.py); [tests/test_low_volume.py](../tests/test_low_volume.py); [tests/test_core.py](../tests/test_core.py); [results/pair_acceptance.json](../results/pair_acceptance.json); [results/exact_examples.json](../results/exact_examples.json); [results/certificates/binary_census.json](../results/certificates/binary_census.json).

**Criteria receipt:**

- *full binary equality certificate*: results/pair_acceptance.json binary_cut_profile for both graphs; binary_census_equal true; DiscoveryTests.test_binary_pair_all_128_assignments_and_first_nested_difference.
- *identify the span-two profile types responsible*: marked_difference_spans [2]; FixedPairAcceptanceTests.test_binary_pair_lower_coefficients_and_span_two_sector.
- *account for every lower coefficient*: chapter 9 'Accounting for every lower coefficient'; equal sectors e_i, 2e_i, e_i+e_j, 3e_i, e_i+e_j+e_k.
- *exact value at q=1/2*: 11025/262144 from the factorized sector difference.
- *binary sampling insufficient*: all 2^7 subsets enumerated for each graph.

**Commands:** `PYTHONPATH=src python -m unittest tests.test_low_volume -v`; `PYTHONPATH=src python scripts/reproduce.py --check`.

**Remaining:** none for P05.

### P06

**Derive universal low-volume formulas.** Status: `complete` (accepted 2026-10-18). Dependencies: P04, P05.

**Accepted evidence:** lowvolume.py implements SNG-F14 from independently defined statistics: degree histogram, ordered pairs by (d_i,d_j,A_ij), unordered triples by (degree sum, induced edges). Chapter 4 adds the pattern table with index-set (ordered/unordered), support and span conventions and the k<=3 translation boundary. regular_low_volume_local implements the SNG-I008 closed form.

**Evidence files:** [src/singularity/lowvolume.py](../src/singularity/lowvolume.py); [tests/test_low_volume.py](../tests/test_low_volume.py); [docs/chapters/04_observation_hierarchy.md](../docs/chapters/04_observation_hierarchy.md); [docs/chapters/10_inverse_problems.md](../docs/chapters/10_inverse_problems.md); [docs/specifications/COEFFICIENTS-v1.md](../docs/specifications/COEFFICIENTS-v1.md).

**Criteria receipt:**

- *formulas using degree and adjacent-vertex statistics*: lowvolume.degree_histogram, ordered_pair_statistics, triple_statistics; FormulaPopulationTests.test_statistics_are_defined_without_profiles.
- *disjoint profile classification*: FormulaPopulationTests.test_classification_is_disjoint_and_exhaustive.
- *compare against complete small-graph enumeration*: FormulaPopulationTests.test_formulas_equal_both_enumerators_on_all_graphs_through_four_vertices (75 graphs, local/normalized/marked, compositions and chains); session check on all 1099 graphs with n<=5.
- *n=1,2,3 translation boundaries*: test_small_order_translation_boundaries.
- *regular simplification with order assumptions*: SNG-I008; test_regular_graphs_follow_order_degree_and_triangles on seven regular graphs.

**Commands:** `PYTHONPATH=src python -m unittest tests.test_low_volume -v`.

**Remaining:** none for P06.

### P07

**Formalize translation normalization.** Status: `planned`. Dependencies: P01. Remaining effort: M; priority: 1.

**Existing work:** SNG-F02 proves the minimum-zero shift bijection in exposition; exact Python normalization and independent replay exist.

**Evidence:** [docs/chapters/01_orientation.md](../docs/chapters/01_orientation.md); [src/singularity/heights.py](../src/singularity/heights.py); [tests/test_core.py](../tests/test_core.py); [results/certificates/translation.json](../results/certificates/translation.json).

**Acceptance still missing:**

- No proof-assistant project, pinned toolchain, finite profile definitions or compilable theorem exists.
- Kernel proofs of injectivity, surjectivity, volume shift and energy preservation, without admitted lemmas, remain to be written.
- Session 2026-10-17/18 (D009): no Lean, Coq or Isabelle toolchain was installed, and the environment's network policy refused downloads from the Lean release hosts, so no kernel build could be attempted.

**Next concrete action:** In an environment with a proof assistant, create a minimal pinned project for finite tuples; prove the minimum-zero shift bijection and the coefficient identity of COEFFICIENTS-v1 section 3 without admitted lemmas, and record the exact build command.

### P08

**Formalize the nested-level energy identity.** Status: `blocked`. Dependencies: P07. Remaining effort: L; priority: 2.

**Existing work:** Threshold chains, volume, quadratic mixed terms and binary extraction have prose proofs and finite exhaustive tests. Repeated levels are permitted in the mathematical definition.

**Evidence:** [docs/chapters/03_nested_heights.md](../docs/chapters/03_nested_heights.md); [src/singularity/heights.py](../src/singularity/heights.py); [tests/test_core.py](../tests/test_core.py).

**Acceptance still missing:**

- P07's formal finite-profile foundation is absent.
- No kernel-checked threshold-chain bijection, nested mixed-edge count identity or binary extraction theorem exists.

**Next concrete action:** After P07 compiles, formalize one-edge threshold expansion, sum it over edges, then prove volume/span and the span-one extraction using the same tuple definitions.

### P09

**Implement bounded-height tree messages.** Status: `complete` (accepted 2026-10-18). Dependencies: P02.

**Accepted evidence:** Proposition SNG-F23 defines the conditioned message F_v(t) and proves the child-product recursion by subtree induction, charging each vertex volume once (x^t at v) and each edge once (connecting factor), with disconnected components multiplied. Rooting at the least original label is explicit; root_messages exposes conditioned messages; transfer_statistics separates height states, sparse support and bit size. Deleting folded child messages is justified by unique parents.

**Evidence files:** [src/singularity/transfer.py](../src/singularity/transfer.py); [tests/test_transfer.py](../tests/test_transfer.py); [docs/chapters/13_research_program.md](../docs/chapters/13_research_program.md); [scripts/benchmark_transfer.py](../scripts/benchmark_transfer.py); [results/transfer_benchmark.json](../results/transfer_benchmark.json); [docs/specifications/COEFFICIENTS-v1.md](../docs/specifications/COEFFICIENTS-v1.md).

**Criteria receipt:**

- *prove the child-product recursion*: SNG-F23, chapter 13.
- *count every vertex and edge once*: SNG-F23 proof; partition of T_v and E(T_v).
- *match reference coefficients on paths, stars and branched trees*: TreeTransferTests.test_named_trees_against_cartesian_and_chain_oracles (path7, star7, balanced7, branched8, forest7; Cartesian oracle H<=2 and level chains at H=R=4); test_all_small_labeled_forests_randomized; test_root_messages_condition_on_the_least_label.
- *report support sizes separately from height-state counts*: transfer_statistics; test_cost_measures_are_separate; results/transfer_benchmark.json unrestricted_cases.cost.
- *P02 dependency*: complete.

**Commands:** `PYTHONPATH=src python -m unittest tests.test_transfer -v`; `python scripts/benchmark_transfer.py`.

**Remaining:** none for P09.

### P10

**Prove safe volume truncation.** Status: `complete` (accepted 2026-10-18). Dependencies: P09.

**Accepted evidence:** Proposition SNG-F24 proves that degree-above-R deletion is the quotient homomorphism to Z[q][x]/(x^(R+1)), covering messages, component convolution and minimum-zero subtraction with the shifted budget R-n, and that H=R suffices for unrestricted coefficients through R. The benchmark now separates the H=2 bounded-box path runs from H=R unrestricted runs on 40-, 63- and 100-vertex trees, each checked by tree-independent count and energy-moment identities.

**Evidence files:** [src/singularity/transfer.py](../src/singularity/transfer.py); [tests/test_transfer.py](../tests/test_transfer.py); [docs/chapters/13_research_program.md](../docs/chapters/13_research_program.md); [scripts/benchmark_transfer.py](../scripts/benchmark_transfer.py); [results/transfer_benchmark.json](../results/transfer_benchmark.json).

**Criteria receipt:**

- *intermediate reduction modulo x^(R+1) preserves the output*: SNG-F24; test_volume_pruning_matches_unpruned_population; test_sparse_high_energy_pruning_and_disconnected_budget (star with energies to 405, disconnected forest with min_zero).
- *H=R suffices*: SNG-F24; test_low_coefficients_equal_unbounded_composition_engine; test_named_trees_against_cartesian_and_chain_oracles.
- *larger tree computations with identical semantics*: results/transfer_benchmark.json unrestricted_cases; test_unrestricted_large_tree_independent_moments (40 vertices, R=8: counts, energy sums, energy-0 and energy-1 profiles).
- *complete coefficient ranges compared*: every volume 0..R checked; no speed claim made.

**Commands:** `PYTHONPATH=src python -m unittest tests.test_transfer -v`; `python scripts/benchmark_transfer.py`.

**Remaining:** none for P10.

### P11

**Recover span by bounded-box subtraction.** Status: `complete` (accepted 2026-10-18). Dependencies: P09, P10.

**Accepted evidence:** marked_forest_coefficients assembles (volume, energy, span) cells from D_H=C_H-x^n C_(H-1) and exact-span differences D_H-D_(H-1); Proposition SNG-F25 proves both subtractions bijectively, with one global translation, and nonnegativity. A negative difference raises with the input retained.

**Evidence files:** [src/singularity/transfer.py](../src/singularity/transfer.py); [tests/test_transfer.py](../tests/test_transfer.py); [docs/chapters/13_research_program.md](../docs/chapters/13_research_program.md); [docs/specifications/COEFFICIENTS-v1.md](../docs/specifications/COEFFICIENTS-v1.md).

**Criteria receipt:**

- *prove the shift subtraction*: SNG-F25.
- *compare every (v,e,h) count with direct marked enumeration*: test_marked_forest_span_subtraction_all_small_forests: all 339 labeled forests on 1..5 vertices through volume 5 against marked_coefficients; named trees through volume 6 against level chains; span sums recover normalized coefficients.
- *H=0, singleton, disconnected, crossing volume n*: test_marked_forest_boundaries.
- *negative intermediate coefficients investigated, not clipped*: ArithmeticError carrying graph, span and cell.

**Commands:** `PYTHONPATH=src python -m unittest tests.test_transfer -v`.

**Remaining:** none for P11.

### P12

**Extend messages to bounded separators.** Status: `complete` (accepted 2026-10-18). Dependencies: P10, P11.

**Accepted evidence:** decomposition.py adds TreeDecomposition with JSON schema singularity.tree-decomposition/1, an axiom checker (vertex and edge coverage, connected occurrence, tree property, root), owned-charge bag messages, truncation, minimum-zero and exact-span sectors, cost statistics and elimination/forest constructors. Proposition SNG-F26 proves the bag-conditioned recursion by decomposition induction with each charge owned once.

**Evidence files:** [src/singularity/decomposition.py](../src/singularity/decomposition.py); [tests/test_decomposition.py](../tests/test_decomposition.py); [docs/chapters/13_research_program.md](../docs/chapters/13_research_program.md); [docs/specifications/COEFFICIENTS-v1.md](../docs/specifications/COEFFICIENTS-v1.md).

**Criteria receipt:**

- *verify the decomposition axioms*: check_decomposition; CheckerTests.test_malformed_decompositions_are_rejected (missing vertex, missing edge, split occurrence, cycle, disconnected tree, bad root, repeated vertex, out-of-range and Boolean labels, invalid tree edges, empty decomposition).
- *prove local charge bookkeeping*: SNG-F26; CheckerTests.test_every_charge_has_exactly_one_owner.
- *compare cycles and bounded-width examples with reference data*: EngineTests: twelve decompositions of C5, C6, a 4-rung ladder, K4 (with redundant bags), two triangles (with an empty bag) and K5 against Cartesian enumeration (H<=2, both normalizations), weak compositions and level chains (marked, volume <=5).
- *width-one versus forest transfer*: test_width_one_matches_forest_transfer_including_disconnected.
- *state count separate from convolution cost*: decomposition_statistics; test_cost_measures.

**Commands:** `PYTHONPATH=src python -m unittest tests.test_decomposition -v`.

**Remaining:** none for P12.

### P13

**Classify the first positive-energy layer.** Status: `implemented_pending_acceptance`. Dependencies: P06, P08. Remaining effort: S; priority: 2.

**Existing work:** SNG-F12 and SNG-A05 prove E>=lambda*span and characterize minimum-energy normalized profiles as binary minimum-cut sides. Tests enumerate heights 0..2 on connected simple graphs through four vertices, checking nonbinary exclusion and multiplicities.

**Evidence:** [docs/chapters/03_nested_heights.md](../docs/chapters/03_nested_heights.md); [docs/chapters/05_prime_arithmetic.md](../docs/chapters/05_prime_arithmetic.md); [src/singularity/invariants.py](../src/singularity/invariants.py); [tests/test_core.py](../tests/test_core.py).

**Acceptance still missing:**

- P06 is complete; P08's kernel identity remains open (D009).
- Record the existing theorem's acceptance receipt, scope and multiplicity comparison; finite tests supplement the general proof rather than prove it.

**Next concrete action:** Reuse the prose proof and exhaustive checks; when P08 is available, derive the formal min-cut corollary from the same nested identity and close the dependency gate explicitly.

### P14

**Compute the nested-pair census.** Status: `planned`. Dependencies: P05, P08. Remaining effort: M; priority: 1.

**Existing work:** The five coordinates (|S|,|T|,cut(S),cut(T),e(T,V\S)) and their projection to span-two volume/energy are specified. The fixed binary pair has a verified span-two discrepancy.

**Evidence:** [docs/chapters/13_research_program.md](../docs/chapters/13_research_program.md); [docs/chapters/03_nested_heights.md](../docs/chapters/03_nested_heights.md); [tests/test_core.py](../tests/test_core.py); [results/certificates/binary_census.json](../results/certificates/binary_census.json).

**Acceptance still missing:**

- No independent nested-pair tensor enumerator or retained tensor data exists.
- No tested projection equality or tensor-cell explanation of the binary pair is released.
- P05 is complete; P08 acceptance remains open (D009).

**Next concrete action:** Enumerate T subseteq S with precise empty/full and repeated-level conventions, project proper nonempty chains to exact span two, and retain the cells causing the binary-pair discrepancy.

### P15

**Separate lattice information from chamber information.** Status: `partial`. Dependencies: P08, P14. Remaining effort: L; priority: 2.

**Existing work:** The integer cut-lattice realization, quotient by constants, volume/span gauges and the distinction between energy isometry and chamber preservation are described. No new structural preservation theorem is claimed.

**Evidence:** [docs/chapters/02_graphs_lattices.md](../docs/chapters/02_graphs_lattices.md); [docs/chapters/10_inverse_problems.md](../docs/chapters/10_inverse_problems.md); [docs/chapters/11_archival_bridges.md](../docs/chapters/11_archival_bridges.md); [docs/chapters/13_research_program.md](../docs/chapters/13_research_program.md).

**Acceptance still missing:**

- State and prove explicit sufficient conditions on a lattice map preserving the marked series.
- Provide a nontrivial map and worked graph instance or a counterexample to a proposed condition.
- Close P08/P14 and connect the conditions to their concrete marks.

**Next concrete action:** Start with an explicit integral height-quotient map; prove what volume and span preservation would require and test a small nontrivial candidate before generalizing.

### P16

**Test Whitney switches systematically.** Status: `blocked`. Dependencies: P15. Remaining effort: M; priority: 2.

**Existing work:** Whitney switches are identified as a controlled matroid-preserving test family; the text explicitly disallows universal conclusions from failed finite separation.

**Evidence:** [docs/chapters/13_research_program.md](../docs/chapters/13_research_program.md); [docs/chapters/14_literature_and_claims.md](../docs/chapters/14_literature_and_claims.md).

**Acceptance still missing:**

- No admissible two-terminal gluing generator, independent matroid-hypothesis checker or exact switch comparison table exists.
- No separating pair or justified transformation conjecture is retained.
- P15 must fix the preservation question being tested.

**Next concrete action:** Define a small exhaustive switch family with terminal conventions, verify each switch's hypotheses, and retain symbolic comparison bounds and any witness rather than only summary counts.

### P17

**Add exact volume congruence filters.** Status: `complete` (accepted 2026-10-18). Dependencies: P03.

**Accepted evidence:** congruence.py adds direct degree selection, a literal character average of L(w^j x,q) evaluated in Z[t]/Phi_m(t) (divided by m only after the full sum, raising if the result is not an integer multiple of the identity), and direct tuple filtering by each profile's own volume. Proposition SNG-F27 proves the averaging identity, including truncations, residue normalization and m=1.

**Evidence files:** [src/singularity/congruence.py](../src/singularity/congruence.py); [tests/test_congruence.py](../tests/test_congruence.py); [docs/chapters/13_research_program.md](../docs/chapters/13_research_program.md); [docs/specifications/COEFFICIENTS-v1.md](../docs/specifications/COEFFICIENTS-v1.md); [src/singularity/conductor.py](../src/singularity/conductor.py).

**Criteria receipt:**

- *prove the root-of-unity averaging identity*: SNG-F27, chapter 13.5.
- *compare with direct modular filtering of assignments*: CongruenceTests.test_three_routes_agree_on_all_graphs_through_three_vertices (11 graphs, volume <=6, moduli 1..7, 308 comparisons) and test_three_routes_agree_on_all_graphs_with_four_vertices (64 graphs, volume <=4, moduli 1..5, 960 comparisons).
- *nonprimitive powers, composite moduli, short truncation, modulus one, empty classes*: test_nonprimitive_powers_and_cancellation_in_the_ring; test_normalization_modulus_one_empty_classes_and_short_truncation.
- *exact rational representation*: test_rational_coefficients_stay_exact.
- *must not be described as extracting span or binary sector*: SNG-F27 discussion; test_marks_cannot_be_recovered_by_volume_filters.
- *malformed or zero modulus fails*: test_invalid_input.

**Commands:** `PYTHONPATH=src python -m unittest tests.test_congruence -v`.

**Remaining:** none for P17.

### P18

**Prove root-of-unity rationality in energy.** Status: `complete` (accepted 2026-10-18). Dependencies: P03, P17.

**Accepted evidence:** Proposition SNG-F28 proves the residue decomposition a_i=r_i+m b_i, E(a)=E(r) mod m, L(x,w)=N/(1-x^m)^n in Z[t]/Phi_m and the remote binomial formula at every index. Tests add an independent Mobius-product construction of Phi_m (m<=24), composite orders 4, 6, 8, 9, isolated-vertex and edgeless graphs, remote indices near 10^30 and exact budget boundaries. results/conductor_fixtures.json retains 20 numerator fixtures with agreement through volume 12.

**Evidence files:** [src/singularity/conductor.py](../src/singularity/conductor.py); [tests/test_conductor_weighted.py](../tests/test_conductor_weighted.py); [docs/chapters/13_research_program.md](../docs/chapters/13_research_program.md); [results/conductor_fixtures.json](../results/conductor_fixtures.json); [results/conductor_example.json](../results/conductor_example.json); [scripts/reproduce.py](../scripts/reproduce.py).

**Criteria receipt:**

- *prove the coordinate residue decomposition*: SNG-F28; RootOfUnityTests.test_residue_decomposition_preserves_energy_mod_order.
- *reproduce local coefficients through an independent bound*: RootOfUnityTests.test_numerator_expansion_equals_direct_specialization (orders 1,2,4,6,8,9 through volume 10); results/conductor_fixtures.json (4 graphs x orders 1,2,3,4,6 through volume 12); ConductorTests.test_numerator_replays_direct_coefficients.
- *cyclotomic reduction validated independently*: test_cyclotomic_polynomials_by_mobius_product.
- *one root versus the unspecialized series*: test_specialized_equality_is_not_series_equality.
- *remote formula and budget*: test_remote_index_uses_binomial_tail_not_enumeration; ConductorTests.test_remote_and_budget.
- *P17 dependency*: complete.

**Commands:** `PYTHONPATH=src python -m unittest tests.test_conductor_weighted -v`; `PYTHONPATH=src python scripts/reproduce.py --check`.

**Remaining:** none for P18.

### P19

**Analyze finite quadratic Gauss sums.** Status: `complete` (accepted 2026-10-18). Dependencies: P18.

**Accepted evidence:** gauss.py diagonalizes the Laplacian by congruence over F_p (odd p), returns and rechecks the basis witness, and computes rank and the Legendre class of the nonsingular discriminant. Theorem SNG-F30 proves Gamma_G(p)=p^(n-r) chi(D) g_p^r for every graph, with congruence invariance, each singular direction (component constants and modular degeneracy) contributing p, and rank zero giving p^n; it recovers SNG-I022 when p does not divide the spanning-tree count. Comparisons are exact in Z[t]/Phi_p(t).

**Evidence files:** [src/singularity/gauss.py](../src/singularity/gauss.py); [tests/test_gauss.py](../tests/test_gauss.py); [docs/chapters/11_archival_bridges.md](../docs/chapters/11_archival_bridges.md); [results/gauss_fixtures.json](../results/gauss_fixtures.json); [scripts/reproduce.py](../scripts/reproduce.py); [src/singularity/conductor.py](../src/singularity/conductor.py).

**Criteria receipt:**

- *formulas in terms of rank and nonsingular discriminant*: SNG-F30; laplacian_invariants; gauss_sum_formula.
- *singular directions accounted for*: SNG-F30 proof; test_singular_directions_include_components (three components, rank zero).
- *compare direct residue enumeration with diagonalized forms*: test_formula_equals_direct_residue_sum: all 75 graphs with n<=4 at p=3,5,7 and all 1024 five-vertex graphs at p=3; results/gauss_fixtures.json (6 graphs x p=3,5).
- *explicit exceptional-prime examples*: test_exceptional_prime_triangle_mod_three (rank 1, Gamma=-9 g_3); spectral_g at p=3 (tau=3, rank 5) in results/gauss_fixtures.json.
- *transformation witnesses checked exactly*: test_witness_rank_and_invertibility against an independent row-reduction rank.
- *prime powers and characteristic two remain separate*: test_diagonalizer_handles_zero_diagonal_and_rejects_bad_input rejects 2, 4, 9, 1.
- *P18 dependency*: complete.

**Commands:** `PYTHONPATH=src python -m unittest tests.test_gauss -v`; `PYTHONPATH=src python scripts/reproduce.py --check`.

**Remaining:** none for P19.

### P20

**Build the disjoint order-chamber formula.** Status: `complete` (accepted 2026-10-18). Dependencies: P02, P06.

**Accepted evidence:** chambers.py enumerates half-open order chambers (sort by height then label; strict gaps at label descents) and evaluates volume, span and energy from gap coordinates through the nested-boundary gap form Q, without constructing heights. Proposition SNG-F29 proves the chambers are disjoint and cover every profile, derives the volume weights and Q_ij = e(T_max, V minus T_min), and relates Q to SNG-F10.

**Evidence files:** [src/singularity/chambers.py](../src/singularity/chambers.py); [tests/test_chambers.py](../tests/test_chambers.py); [docs/chapters/13_research_program.md](../docs/chapters/13_research_program.md); [docs/specifications/COEFFICIENTS-v1.md](../docs/specifications/COEFFICIENTS-v1.md).

**Criteria receipt:**

- *every profile belongs to exactly one chamber, including ties*: SNG-F29; ChamberTests.test_every_profile_has_exactly_one_chamber (all 256 profiles of {0..3}^4); test_tied_blocks_zero_profile_and_labels.
- *closed chambers overcount*: test_closed_cones_would_overcount_ties.
- *gap expression for volume and quadratic energy*: SNG-F29; test_gap_form_is_the_nested_boundary_matrix.
- *match complete histograms*: test_complete_histograms_match_two_enumerators (75 graphs, local and marked, volume <=6, against weak compositions and level chains); session check of all 1024 five-vertex graphs through volume 5 against chains.
- *factorial cost stated*: chambers.py docstring and chapter 13.6.

**Commands:** `PYTHONPATH=src python -m unittest tests.test_chambers -v`.

**Remaining:** none for P20.

### P21

**Relate constrained heights to order polytopes.** Status: `complete` (accepted 2026-10-18). Dependencies: P20.

**Accepted evidence:** orders.py adds validated finite posets (closure, cycle rejection), weak and strict constrained counts by direct enumeration, a chamber-based weak count valid for arbitrary labels, Stanley's linear-extension formula over a natural labeling, and (volume, energy) histograms on order-polytope points. Proposition SNG-F32 identifies weak assignments with lattice points of H*O(P), counted by Omega(P,H+1) with the argument shift explained, maps chamber tie rules to linear extensions, separates strict assignments, and proves that the quadratic weight can destroy polynomiality in H.

**Evidence files:** [src/singularity/orders.py](../src/singularity/orders.py); [tests/test_orders.py](../tests/test_orders.py); [docs/chapters/13_research_program.md](../docs/chapters/13_research_program.md); [docs/chapters/14_literature_and_claims.md](../docs/chapters/14_literature_and_claims.md); [docs/references.bib](../docs/references.bib); [src/singularity/chambers.py](../src/singularity/chambers.py).

**Criteria receipt:**

- *unweighted bounded-height specialization with correct weak and strict inequalities*: SNG-F32 (1)-(3); OrderPolytopeTests.test_three_counts_agree (seven posets, complete height ranges, three methods); test_closed_forms_and_argument_shift (chain C(H+n,n), strict chain C(H+1,n), antichain (H+1)^n).
- *chamber tie rules mapped to linear extensions*: SNG-F32 (2); count_by_chambers on unnaturally labeled posets; test_linear_extensions_and_natural_labeling.
- *identify what quadratic weighting adds*: SNG-F32 (4); test_quadratic_weight_is_not_an_ehrhart_polynomial.
- *invalid cyclic relations fail*: test_invalid_relations.
- *literature positioning*: chapter 13.6 paragraph citing Stanley1986 and Stanley2012.
- *P20 dependency*: complete.

**Commands:** `PYTHONPATH=src python -m unittest tests.test_orders -v`.

**Remaining:** none for P21.

### P22

**Establish one genuine reciprocity statement.** Status: `planned`. Dependencies: P21. Remaining effort: L; priority: 3.

**Existing work:** The research program states the need for explicit boundary corrections and warns against an unproved weighted Ehrhart analogy. Complement/span reflection elsewhere is not the requested order-population reciprocity.

**Evidence:** [docs/chapters/13_research_program.md](../docs/chapters/13_research_program.md); [docs/chapters/14_literature_and_claims.md](../docs/chapters/14_literature_and_claims.md).

**Acceptance still missing:**

- No scoped reciprocity theorem with full proof, or certified counterexample to a chosen weighted extension, is present.
- P21 now fixes the counting problem (orders.py, SNG-F32): weak assignments are Omega(P,H+1), strict assignments a separate population, and quadratic weighting is shown to leave polynomiality in H.

**Next concrete action:** Using orders.py, state the established order-polynomial reciprocity between weak and strict counts as background, then either prove a scoped weighted identity with boundary terms or certify the smallest counterexample to the naive H -> -H extension of the weighted count.

### P23

**Implement formal logarithmic extraction.** Status: `complete` (accepted 2026-10-18). Dependencies: P03.

**Accepted evidence:** The existing exact transforms are audited and accepted. The specification fixes the coefficient ring Q[q], required constant terms, inclusive truncation and JSON triples, and separates the ordinary exponents from the integral bidegree transform (SNG-A08). Chapter 6 maps each identity to its independent implementation. New tests cover the single-edge worked example (6.10), the triangular identity n c_n = sum_{d|n} d b_d on a graph series, degree-zero truncation, reduced rationals, prefix stability and recomposition of every retained certificate's exponents.

**Evidence files:** [src/singularity/polynomials.py](../src/singularity/polynomials.py); [src/singularity/euler.py](../src/singularity/euler.py); [tests/test_analytics.py](../tests/test_analytics.py); [docs/chapters/06_euler_analysis.md](../docs/chapters/06_euler_analysis.md); [docs/specifications/COEFFICIENTS-v1.md](../docs/specifications/COEFFICIENTS-v1.md); [src/singularity/certificates.py](../src/singularity/certificates.py); [results/certificates/spectral.json](../results/certificates/spectral.json).

**Criteria receipt:**

- *formal logarithm, inverse series and finite Euler exponents in rational arithmetic*: polynomials.series_log/series_inverse/series_exp; euler.euler_exponents; FormalSeriesTests.
- *reconstruct the input truncation by multiplication*: recompose_euler; test_nonconstant_polynomial_exponents_recompose; test_portable_certificate_exponents_recompose; certificate replay.
- *verify the Mobius coefficient identities*: test_triangular_log_identity_and_mobius_inverse; euler_exponents_mobius equality tests.
- *distinguish q-dependent exponents from integer multiplicities*: SNG-A07 versus SNG-A08 discussion; specification section 8; negative and fractional exponents in test_single_edge_worked_example_matches_chapter_six.
- *specialization can annihilate a symbolic discrepancy*: test_symbolic_difference_can_vanish_after_specialization.
- *P03 dependency*: complete.

**Commands:** `PYTHONPATH=src python -m unittest tests.test_analytics -v`.

**Remaining:** none for P23.

### P24

**Determine exceptional energy parameters.** Status: `complete` (accepted 2026-10-18). Dependencies: P23.

**Accepted evidence:** parameters.py implements square-free parts, Sturm sequences, exact rational bisection, rational-root detection, algebraic specialization by gcd and Sturm counts, multiplicities, and parameter_strata, which reports the generic first volume, every exceptional root in (0,1) with the volume first visible there, and the endpoints separately. Proposition SNG-F31 proves finiteness, completeness of isolation and exactness of the specialization test.

**Evidence files:** [src/singularity/parameters.py](../src/singularity/parameters.py); [tests/test_parameters.py](../tests/test_parameters.py); [docs/chapters/13_research_program.md](../docs/chapters/13_research_program.md); [results/parameter_strata.json](../results/parameter_strata.json); [scripts/reproduce.py](../scripts/reproduce.py); [src/singularity/euler.py](../src/singularity/euler.py).

**Criteria receipt:**

- *isolate every real root in (0,1) of the tested leading polynomials*: SNG-F31; RootIsolationTests; parameter_strata status field.
- *recompute at each exceptional value*: StrataTests.test_artificial_interior_algebraic_and_rational_strata (two irrational roots visible at volume 3; rational root 1/2 with agreement through the bound).
- *released examples strictly visible in the interior*: test_released_pairs_have_no_interior_exceptional_parameter; results/parameter_strata.json (spectral 2, binary 3, cube-Mobius 4, no exceptional q).
- *multiplicities, repeated roots, zero polynomials, rational values, endpoints*: test_repeated_roots_and_multiplicity; test_zero_discrepancies_and_endpoint_shift.
- *no plot or grid*: exact Fraction arithmetic only.
- *P23 dependency*: complete.

**Commands:** `PYTHONPATH=src python -m unittest tests.test_parameters -v`; `PYTHONPATH=src python scripts/reproduce.py --check`.

**Remaining:** none for P24.

### P25

**Organize successive visibility levels.** Status: `complete` (accepted 2026-10-18). Dependencies: P23, P24.

**Accepted evidence:** visibility.py partitions named prefixes by agreement through each volume in symbolic, marked, rational-parameter and algebraic-parameter domains, with deterministic class identifiers, memberships at every level, signed split witnesses and classes unresolved at the bound. Proposition SNG-F33 proves refinement, the first-difference meaning of witnesses, the domain implications and their failure of converses, and the finite meaning of unresolved classes. The CENSUS-v1 filtrations through volume 6 are retained.

**Evidence files:** [src/singularity/visibility.py](../src/singularity/visibility.py); [tests/test_visibility.py](../tests/test_visibility.py); [docs/chapters/04_observation_hierarchy.md](../docs/chapters/04_observation_hierarchy.md); [results/visibility_filtration.json](../results/visibility_filtration.json); [results/census_manifest.json](../results/census_manifest.json); [scripts/reproduce.py](../scripts/reproduce.py); [src/singularity/parameters.py](../src/singularity/parameters.py).

**Criteria receipt:**

- *filtration by first discrepancy including parameter-dependent refinements*: visibility_filtration domains polynomial/marked/rational/algebraic; test_specialization_merges_symbolic_classes; test_algebraic_parameter_domain.
- *prove every reported equality below the first differing coefficient*: SNG-F33 (ii); test_witness_lower_coefficients_agree_and_signs.
- *label unresolved collisions with their tested bound*: unresolved_at_bound; test_reference_pairs_split_at_their_depths (cube-Mobius unresolved through 3).
- *recover reference depths 2, 3, 4*: test_reference_pairs_split_at_their_depths.
- *refinement on the complete declared census, duplicates, relabelings*: test_refinement_is_monotone_on_the_census (n<=5, symbolic and marked); test_duplicates_and_relabelings_share_classes; results/visibility_filtration.json class counts equal results/small_census.json.
- *unequal truncations and signs*: test_unequal_lengths_and_bounds; sign test.
- *no unrestricted depth claim*: SNG-F33 (iv) and chapter 4 text.
- *P23 and P24 dependencies*: complete.

**Commands:** `PYTHONPATH=src python -m unittest tests.test_visibility -v`; `PYTHONPATH=src python scripts/reproduce.py --check`.

**Remaining:** none for P25.

### P26

**Make analytic remainder bounds explicit.** Status: `complete` (accepted 2026-10-18). Dependencies: P25.

**Accepted evidence:** The manuscript constant (7.12) is implemented exactly (regularized_tail_constant), with the omitted-prime bound (7.13) for rational s=a/b at cutoffs P=N^b where every power and the radius condition are exact (regularized_prime_tail_bound), recovering C r/N at s=1/r. certified_tail_record recomputes the first discrepancy at q from supplied prefixes and states the remaining hypotheses. Chapter 7 records the relation to the older conservative constant and the finite small-prime treatment. results/tail_records.json holds end-to-end records for the three reference pairs.

**Evidence files:** [src/singularity/arithmetic.py](../src/singularity/arithmetic.py); [tests/test_arithmetic.py](../tests/test_arithmetic.py); [docs/chapters/07_visibility_singularities.md](../docs/chapters/07_visibility_singularities.md); [docs/chapters/06_euler_analysis.md](../docs/chapters/06_euler_analysis.md); [results/tail_records.json](../results/tail_records.json); [scripts/reproduce.py](../scripts/reproduce.py).

**Criteria receipt:**

- *display constants*: (7.12) implemented exactly; test_constant_matches_its_definition.
- *parameter restrictions*: q in [0,1], 0<radius<1, (r+1)s>1, P^(-s)<=radius enforced; test_prime_tail_guards_and_boundary_case.
- *treatment of finitely many small primes*: primes p<=P kept exactly, omitted primes inside the radius by the cutoff guard; chapter 7 paragraph.
- *boundary estimate C r/N at s=1/r, P=N^r*: test_prime_tail_guards_and_boundary_case.
- *rigorously bounded finite comparison on small cases*: test_local_inequality_with_rigorous_rational_enclosures (spectral pair, three rational t, enclosure (7.14), Bernoulli bounds, no floating point).
- *caller must provide exact first-discrepancy evidence*: certified_tail_record recomputes r and delta; test_record_recomputes_depth_and_rejects_bad_hypotheses (truncated prefix, q=1, q outside [0,1]).
- *P25 dependency*: complete.

**Commands:** `PYTHONPATH=src python -m unittest tests.test_arithmetic -v`; `PYTHONPATH=src python scripts/reproduce.py --check`.

**Remaining:** none for P26.

### P27

**Produce controlled real singularity experiments.** Status: `planned`. Dependencies: P26. Remaining effort: M; priority: 1.

**Existing work:** Exact tail constants and local truncation estimates are available as foundations. No retained prime-product numerical experiment is included in results/.

**Evidence:** [src/singularity/arithmetic.py](../src/singularity/arithmetic.py); [docs/chapters/07_visibility_singularities.md](../docs/chapters/07_visibility_singularities.md); [tests/test_arithmetic.py](../tests/test_arithmetic.py).

**Acceptance still missing:**

- No rigorous finite-prime local-factor evaluation with truncation enclosures exists.
- No normalized remainder intervals near s=1/r or demonstrated recovery of the established asymptotic within those intervals is released.
- P26 is complete (2026-10-18): regularized_tail_constant, regularized_prime_tail_bound and certified_tail_record supply exact constants; near s=1/r the tail decays like C r P^(-1/r), so a useful enclosure needs a sharper, coefficient-aware constant or very large cutoffs.

**Next concrete action:** Build interval-enclosed local sums and finite prime products, attach both local truncation and omitted-prime error bounds, and retain a small fully certified table before attempting plots.

### P28

**State the available complex domain exactly.** Status: `partial`. Dependencies: P26. Remaining effort: M; priority: 2.

**Existing work:** SNG-A10 proves normal tail convergence on compact subsets of the finite-extraction half-plane; SNG-A11 supplies a holomorphic nonzero neighborhood of the positive real visibility point. Small-prime denominators and the power-series branch of log(1-p^-rs) are explicitly discussed; global meromorphic continuation is not claimed.

**Evidence:** [docs/chapters/06_euler_analysis.md](../docs/chapters/06_euler_analysis.md); [docs/chapters/07_visibility_singularities.md](../docs/chapters/07_visibility_singularities.md).

**Acceptance still missing:**

- The local complex neighborhood is established existentially, without an explicit computable disk or certified nonvanishing domain for the selected pair.
- Supply domain/branch bookkeeping for all finite denominator factors and the normally convergent tail in a focused statement.
- P26 is complete (2026-10-18); its exact constant (7.12) can quantify the tail on a disc around 1/r.

**Next concrete action:** Choose one fixed rational interior q and derive a conservative explicit disk around s=1/r with certified finite-factor nonvanishing and uniform tail convergence.

### P29

**Specify a complete finite graph census.** Status: `complete` (accepted 2026-10-18). Dependencies: P03.

**Accepted evidence:** CENSUS-v1.md fixes the population (connected simple graphs, orders 1..6), mask-order generation, the degree-sorted minimum-code isomorphism decision with proof, representative selection, digest encoding and the labeled versus class count distinction. census_manifest.py retains every class with code, generation mask, canonical edges, SHA-256 digest, degrees, labeled copies and brute-force automorphism group order, and refuses to write unless the labeled counts match an independent recurrence and every code group satisfies orbit-stabilizer.

**Evidence files:** [docs/specifications/CENSUS-v1.md](../docs/specifications/CENSUS-v1.md); [scripts/census_manifest.py](../scripts/census_manifest.py); [results/census_manifest.json](../results/census_manifest.json); [tests/test_census.py](../tests/test_census.py); [scripts/census.py](../scripts/census.py); [results/small_census.json](../results/small_census.json).

**Criteria receipt:**

- *canonical input manifest with isomorphism handling documented*: docs/specifications/CENSUS-v1.md sections 2-6; results/census_manifest.json.
- *independently reconcile population counts*: recurrence c_n gives 1,1,4,38,728,26704; orbit-stabilizer totals equal them; classes 1,1,2,6,21,112; CensusManifestTests.test_counts_reconcile.
- *uniqueness and coverage, not copied counts*: labeled_copies x |Aut| = n! per class (automorphisms by all n! permutations); pairwise brute-force non-isomorphism through n=5 in test_automorphisms_and_uniqueness_through_five_vertices.
- *generation options and graph hashes*: manifest generation/digest fields; test_reconstruct_every_graph recomputes digests, codes and connectedness.
- *relabeled copies, equal-degree distinct graphs, reserialization*: test_relabeled_copies_and_equal_degree_graphs (prism versus K3,3); test_reserialization_is_deterministic.
- *same population as aggregate summaries*: test_manifest_is_the_census_population.

**Commands:** `PYTHONPATH=src python scripts/census_manifest.py --check`; `PYTHONPATH=src python -m unittest tests.test_census -v`.

**Remaining:** none for P29.

### P30

**Measure collision classes across invariants.** Status: `partial`. Dependencies: P12, P14, P29. Remaining effort: M; priority: 2.

**Existing work:** The census records complete binary class counts, local/marked class counts by depth through volume six and final unresolved local/marked classes. n<=6 height and binary observations all separate by volume three.

**Evidence:** [scripts/census.py](../scripts/census.py); [results/small_census.json](../results/small_census.json); [src/singularity/invariants.py](../src/singularity/invariants.py); [docs/IMPLEMENTATION.md](../docs/IMPLEMENTATION.md).

**Acceptance still missing:**

- No Laplacian spectral partition is retained in the census output.
- Full binary and intermediate prefix class memberships, first-discrepancy witnesses and structured resource limits are absent.
- P12 and P29 are complete; P14 remains open, so the original dependency gate is not met.

**Next concrete action:** Extend the existing fixed-population census output to retain stable class membership IDs, spectral groups, witness polynomials and exact denominators; do not regenerate an undocumented larger population.

### P31

**Resolve targeted collisions structurally.** Status: `blocked`. Dependencies: P16, P30. Remaining effort: L; priority: 2.

**Existing work:** Three fixed comparison pairs have concrete structural explanations, but the retained n<=6 complete census has no unresolved final local or marked classes. Those examples are not outcomes selected from an accepted P30 target ledger.

**Evidence:** [docs/chapters/10_inverse_problems.md](../docs/chapters/10_inverse_problems.md); [docs/chapters/13_research_program.md](../docs/chapters/13_research_program.md); [results/small_census.json](../results/small_census.json).

**Acceptance still missing:**

- P16/P30 must supply a defined target population and collision classes.
- No per-target structural resolution ledger provides bijections, later-volume witnesses or precise remaining conjectures with negative results.

**Next concrete action:** After P30, select the smallest meaningful collisions, including deliberate invariant-matched families if necessary, and seek a mechanism before raising their coefficient cutoff.

### P32

**Seek a separation bound for one graph family.** Status: `blocked`. Dependencies: P06, P12, P31. Remaining effort: L; priority: 2.

**Existing work:** Regular-graph blindness at early volumes and the cube/Mobius-ladder separation provide calibrated finite evidence. The manuscript explicitly keeps general reconstruction and unbounded delayed visibility open.

**Evidence:** [docs/chapters/04_observation_hierarchy.md](../docs/chapters/04_observation_hierarchy.md); [docs/chapters/10_inverse_problems.md](../docs/chapters/10_inverse_problems.md); [docs/chapters/13_research_program.md](../docs/chapters/13_research_program.md); [docs/chapters/09_exact_examples.md](../docs/chapters/09_exact_examples.md).

**Acceptance still missing:**

- No parameterized family with a uniformly proved first-separation bound, or a uniform counterfamily defeating a proposed bound, is established.
- P06 and P12 are complete; P31 remains open.
- The latest chat's large-girth delayed-visibility and terminal-interface ideas are conjectural research directions, not accepted proofs or replacements for P32.

**Next concrete action:** Choose one narrow family from accepted collision evidence, formulate a uniform statement and pursue either a proof or explicit counterfamily with all construction hypotheses checked.

### P33

**Verify concrete coefficient certificates in a kernel.** Status: `blocked`. Dependencies: P07, P08, P23. Remaining effort: L; priority: 3.

**Existing work:** Python replay reconstructs declared coefficients and rejects altered sectors. This is independent finite computational checking, not a kernel-connected enumeration proof.

**Evidence:** [src/singularity/certificates.py](../src/singularity/certificates.py); [results/certificates/spectral.json](../results/certificates/spectral.json); [results/certificates/binary_census.json](../results/certificates/binary_census.json); [docs/chapters/12_computational_methodology.md](../docs/chapters/12_computational_methodology.md); [tests/test_analytics.py](../tests/test_analytics.py).

**Acceptance still missing:**

- P07/P08 formal definitions and identities are absent (D009); P23 is complete.
- No kernel theorem connects parsed records to the mathematical coefficient definition or verifies both decisive pair multiplicities.
- Kernel tests rejecting a changed graph edge and coefficient remain absent.

**Next concrete action:** After formal foundations compile, define a verified finite enumeration/checking path and connect it to both existing packets; prove its soundness rather than only verifying a parser.

### P34

**Formalize the visibility comparison boundary.** Status: `blocked`. Dependencies: P26, P33. Remaining effort: L; priority: 3.

**Existing work:** The first-discrepancy ratio law and real zeta-factor asymptotic are proved in mathematical exposition with explicit branch and convergence scope.

**Evidence:** [docs/chapters/07_visibility_singularities.md](../docs/chapters/07_visibility_singularities.md); [docs/chapters/06_euler_analysis.md](../docs/chapters/06_euler_analysis.md); [docs/papers/visibility.md](../docs/papers/visibility.md).

**Acceptance still missing:**

- P26 is complete; P33 remains open and no formal analysis project exists.
- No exposed list of imported analytic theorems, compiling local-expansion-to-asymptotic chain or precisely recorded unformalized boundary is supplied.

**Next concrete action:** Inventory the chosen proof assistant's actual analytic libraries, formalize the finite local expansion first, and record every remaining analytic assumption without claiming full-chain verification until it compiles.

### P35

**Release the first focused manuscript.** Status: `partial`. Dependencies: P04, P05, P26, P27, P33. Remaining effort: M; priority: 3.

**Existing work:** A six-page focused article with editable sources, literature context, finite examples and the real comparison theorem is already released. Independent computational replay and claim-scope guidance exist. It makes no kernel-verification or priority claim.

**Evidence:** [docs/papers/visibility.md](../docs/papers/visibility.md); [docs/visibility_paper.tex](../docs/visibility_paper.tex); [docs/visibility_paper.html](../docs/visibility_paper.html); [output/pdf/visibility_paper.pdf](../output/pdf/visibility_paper.pdf); [docs/references.bib](../docs/references.bib); [results/validation.json](../results/validation.json); [scripts/reproduce.py](../scripts/reproduce.py).

**Acceptance still missing:**

- The original acceptance gate explicitly depends on P33; a readable article does not satisfy that absent kernel work.
- P04, P05 and P26 are complete; P27's controlled experiments and P33's kernel verification are absent.
- A final claim-by-claim proof/certificate matrix and submission-focused literature comparison must be reconciled with achieved scope.

**Next concrete action:** Treat the current article as a reusable draft. Build its claim matrix and update it as dependencies close; if publication is pursued earlier, record an explicit roadmap dependency amendment rather than silently marking P35 complete.

### P36

**Choose the second paper from actual results.** Status: `blocked`. Dependencies: P19, P22, P31, P32, P35. Remaining effort: L; priority: 3.

**Existing work:** Candidate B (exact tree/separator methods) and Candidate C (structural preservation) are clearly described as future papers. Their theorem centers are not declared achieved.

**Evidence:** [docs/chapters/14_literature_and_claims.md](../docs/chapters/14_literature_and_claims.md); [docs/chapters/13_research_program.md](../docs/chapters/13_research_program.md); [docs/development/PUSHES.md](../docs/development/PUSHES.md).

**Acceptance still missing:**

- P19 is complete; P22/P31/P32/P35 outcomes have not been accepted.
- No second paper is selected around an actual substantial theorem or decisive negative classification, with focused literature comparison and reproduced artifacts.
- The open-problem ledger must distinguish original pushes from any newly approved terminal-interface or delayed-visibility branch.

**Next concrete action:** Wait for substantive accepted results, then select one coherent paper center and package that result; preserve unfinished branches in the ledger instead of combining them into a larger manuscript.

## How to update the ledger

After each push, update this document and `push_status.json` together. Cite the exact new source, theorem, tests and retained output. Record the command actually run and its scope. Preserve unresolved questions and negative results. Promote a push to `complete` only after checking its own acceptance and each dependency's closure or an explicitly approved amendment. A commit title, code file or paper-shaped PDF is not by itself an acceptance receipt.

For a mathematical dependency that remains open, retain `implemented_pending_acceptance` when the central deliverable exists, `partial` when substantive own requirements remain, and `blocked` when the central target cannot yet be evaluated. Do not make the status more optimistic solely because another agent reported success.
