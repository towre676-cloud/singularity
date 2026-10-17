# Original 36-push audit and acceptance ledger

Baseline: `89fb96d25bef0463e41feb74d987b464e5fd534f` (version 0.1.0), audited 2026-10-17. The original sequence is retained in [PUSHES.md](../docs/development/PUSHES.md). The executable ledger is [push_status.json](push_status.json). All P01–P36 identifiers and original dependency edges are preserved.

**The 36 pushes are the development plan, not 36 completed commits.** The initial release implemented substantial parts of several pushes ahead of their acceptance sequence. This audit separates reusable work from closure. No entry is marked complete because the original dependency and acceptance gates have not all been evidenced. The absence of a complete label does not mean the corresponding code or prose proof is absent.

## What Claude Code should do first

Close the finite contract in P01; add the genuinely independent chain generator in P02; then audit and close P03 using the existing certificate engine. Those three steps unlock acceptance of much of the existing work. Do not start by replacing forest transfer, Euler extraction or conductor arithmetic. P04/P05/P06/P09/P10/P18/P23/P26 contain substantive existing deliverables to accept or extend.

Use original dependencies as **completion gates**. Preparatory research may proceed in parallel; an acceptance claim must either satisfy the original gate or record an explicit scope/dependency amendment. In particular, P35 originally requires P33 kernel verification even though a paper draft already exists. Publishing a draft does not silently waive that requirement.

## Status meanings

| Status | Meaning | Push count |
|---|---|---:|
| `planned` | The target is specified, but its substantive deliverable is absent. Preparatory work can proceed while dependencies remain open. | 5 |
| `partial` | Some substantive deliverables exist, but important own acceptance requirements remain unsatisfied. | 13 |
| `implemented_pending_acceptance` | The central target is implemented or proved in exposition, but explicit acceptance checks, dependency closure or publication bookkeeping remain outstanding. | 9 |
| `blocked` | The central deliverable is absent and a named prerequisite must be established before its original acceptance criterion can be evaluated. | 9 |
| `complete` | All original acceptance requirements and declared dependencies have evidence-backed closure. No push receives this label in the baseline audit. | 0 |

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
| [P04](#p04) | Give the spectral pair a short coefficient proof | `implemented_pending_acceptance` | P03 | S | 1 |
| [P05](#p05) | Explain the binary-census separation | `implemented_pending_acceptance` | P02, P03 | S | 1 |
| [P06](#p06) | Derive universal low-volume formulas | `implemented_pending_acceptance` | P04, P05 | S | 1 |
| [P07](#p07) | Formalize translation normalization | `planned` | P01 | M | 1 |
| [P08](#p08) | Formalize the nested-level energy identity | `blocked` | P07 | L | 2 |
| [P09](#p09) | Implement bounded-height tree messages | `implemented_pending_acceptance` | P02 | S | 1 |
| [P10](#p10) | Prove safe volume truncation | `implemented_pending_acceptance` | P09 | S | 1 |
| [P11](#p11) | Recover span by bounded-box subtraction | `partial` | P09, P10 | S | 1 |
| [P12](#p12) | Extend messages to bounded separators | `blocked` | P10, P11 | L | 1 |
| [P13](#p13) | Classify the first positive-energy layer | `implemented_pending_acceptance` | P06, P08 | S | 2 |
| [P14](#p14) | Compute the nested-pair census | `planned` | P05, P08 | M | 1 |
| [P15](#p15) | Separate lattice information from chamber information | `partial` | P08, P14 | L | 2 |
| [P16](#p16) | Test Whitney switches systematically | `blocked` | P15 | M | 2 |
| [P17](#p17) | Add exact volume congruence filters | `planned` | P03 | S | 2 |
| [P18](#p18) | Prove root-of-unity rationality in energy | `implemented_pending_acceptance` | P03, P17 | S | 2 |
| [P19](#p19) | Analyze finite quadratic Gauss sums | `partial` | P18 | M | 2 |
| [P20](#p20) | Build the disjoint order-chamber formula | `partial` | P02, P06 | M | 2 |
| [P21](#p21) | Relate constrained heights to order polytopes | `planned` | P20 | M | 2 |
| [P22](#p22) | Establish one genuine reciprocity statement | `blocked` | P21 | L | 3 |
| [P23](#p23) | Implement formal logarithmic extraction | `implemented_pending_acceptance` | P03 | S | 1 |
| [P24](#p24) | Determine exceptional energy parameters | `partial` | P23 | M | 1 |
| [P25](#p25) | Organize successive visibility levels | `partial` | P23, P24 | M | 1 |
| [P26](#p26) | Make analytic remainder bounds explicit | `implemented_pending_acceptance` | P25 | S | 1 |
| [P27](#p27) | Produce controlled real singularity experiments | `planned` | P26 | M | 1 |
| [P28](#p28) | State the available complex domain exactly | `partial` | P26 | M | 2 |
| [P29](#p29) | Specify a complete finite graph census | `partial` | P03 | S | 1 |
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

**Give the spectral pair a short coefficient proof.** Status: `implemented_pending_acceptance`. Dependencies: P03. Remaining effort: S; priority: 1.

**Existing work:** The volume 0/1/2 classification, exact Laplacian polynomial and degree-adjacency explanation are already present. Tests retain discrepancy 2q^2(1-q)^3(1+q), first depth 2 and value 3/32 at q=1/2.

**Evidence:** [docs/chapters/04_observation_hierarchy.md](../docs/chapters/04_observation_hierarchy.md); [docs/chapters/07_visibility_singularities.md](../docs/chapters/07_visibility_singularities.md); [docs/chapters/09_exact_examples.md](../docs/chapters/09_exact_examples.md); [src/singularity/examples.py](../src/singularity/examples.py); [tests/test_core.py](../tests/test_core.py); [results/exact_examples.json](../results/exact_examples.json); [results/certificates/spectral.json](../results/certificates/spectral.json).

**Acceptance still missing:**

- Match the spectral pair with P02's actual independent chain enumerator.
- P03 portable-certificate acceptance is open; add an explicit closure record tying proof, exact polynomial and both enumerators together.

**Next concrete action:** Reuse the existing proof and fixture; after P02/P03, replay the pair through both enumerators and publish a compact acceptance matrix rather than rewriting the result.

### P05

**Explain the binary-census separation.** Status: `implemented_pending_acceptance`. Dependencies: P02, P03. Remaining effort: S; priority: 1.

**Existing work:** All 128 binary assignments are compared exactly. Volume-three profile classes, the ordered 2e_i+e_j span-two sector, lower equality and q=1/2 value 11025/262144 are retained; the discrepancy factors as q^3(1-q)(1-q^3)^2(1-q^4)^2.

**Evidence:** [docs/chapters/07_visibility_singularities.md](../docs/chapters/07_visibility_singularities.md); [docs/chapters/09_exact_examples.md](../docs/chapters/09_exact_examples.md); [tests/test_core.py](../tests/test_core.py); [results/exact_examples.json](../results/exact_examples.json); [results/certificates/binary_census.json](../results/certificates/binary_census.json); [src/singularity/invariants.py](../src/singularity/invariants.py).

**Acceptance still missing:**

- Run the genuine P02 chain generator and record agreement across all relevant marked cells.
- Close P03 and associate its complete binary equality and height certificate outputs with the prose proof in an acceptance receipt.

**Next concrete action:** Add independent chain replay of the fixed pair and a full binary table digest; keep the graph labels and polynomial orientation unchanged.

### P06

**Derive universal low-volume formulas.** Status: `implemented_pending_acceptance`. Dependencies: P04, P05. Remaining effort: S; priority: 1.

**Existing work:** SNG-F14 gives disjoint profile classifications through volume three; SNG-F15 defines the edge degree-sum polynomial independently and explains the volume-two mixing statistic. Regular-graph early blindness is derived in Chapter 10.

**Evidence:** [docs/chapters/04_observation_hierarchy.md](../docs/chapters/04_observation_hierarchy.md); [docs/chapters/09_exact_examples.md](../docs/chapters/09_exact_examples.md); [docs/chapters/10_inverse_problems.md](../docs/chapters/10_inverse_problems.md); [tests/test_core.py](../tests/test_core.py).

**Acceptance still missing:**

- A dedicated implementation of the closed formulas must be checked against coefficient enumeration across a complete declared small graph population; generic coefficient-oracle tests do not explicitly verify the formulas.
- P04/P05 acceptance remains open.

**Next concrete action:** Implement a small formula oracle separate from weak compositions and retain exhaustive volume-0-to-3 comparisons, including n=1/2/3 normalization boundary cases.

### P07

**Formalize translation normalization.** Status: `planned`. Dependencies: P01. Remaining effort: M; priority: 1.

**Existing work:** SNG-F02 proves the minimum-zero shift bijection in exposition; exact Python normalization and independent replay exist.

**Evidence:** [docs/chapters/01_orientation.md](../docs/chapters/01_orientation.md); [src/singularity/heights.py](../src/singularity/heights.py); [tests/test_core.py](../tests/test_core.py); [results/certificates/translation.json](../results/certificates/translation.json).

**Acceptance still missing:**

- No proof-assistant project, pinned toolchain, finite profile definitions or compilable theorem exists.
- Kernel proofs of injectivity, surjectivity, volume shift and energy preservation, without admitted lemmas, remain to be written.

**Next concrete action:** Create a minimal pinned formal project for finite tuples and coefficient counts; prove only the shift bijection and coefficient identity before importing more advanced infrastructure.

### P08

**Formalize the nested-level energy identity.** Status: `blocked`. Dependencies: P07. Remaining effort: L; priority: 2.

**Existing work:** Threshold chains, volume, quadratic mixed terms and binary extraction have prose proofs and finite exhaustive tests. Repeated levels are permitted in the mathematical definition.

**Evidence:** [docs/chapters/03_nested_heights.md](../docs/chapters/03_nested_heights.md); [src/singularity/heights.py](../src/singularity/heights.py); [tests/test_core.py](../tests/test_core.py).

**Acceptance still missing:**

- P07's formal finite-profile foundation is absent.
- No kernel-checked threshold-chain bijection, nested mixed-edge count identity or binary extraction theorem exists.

**Next concrete action:** After P07 compiles, formalize one-edge threshold expansion, sum it over edges, then prove volume/span and the span-one extraction using the same tuple definitions.

### P09

**Implement bounded-height tree messages.** Status: `implemented_pending_acceptance`. Dependencies: P02. Remaining effort: S; priority: 1.

**Existing work:** Exact forest message passing, single-charge edge combination, disconnected component convolution and a separate Cartesian oracle are implemented. Deterministic generated forests, isolated graphs, a branched tree and paths are checked; cycles are rejected. Joint support cells are reported in benchmarks.

**Evidence:** [src/singularity/transfer.py](../src/singularity/transfer.py); [tests/test_transfer.py](../tests/test_transfer.py); [docs/chapters/13_research_program.md](../docs/chapters/13_research_program.md); [docs/IMPLEMENTATION.md](../docs/IMPLEMENTATION.md); [scripts/benchmark_transfer.py](../scripts/benchmark_transfer.py); [results/transfer_benchmark.json](../results/transfer_benchmark.json).

**Acceptance still missing:**

- Close P02 and compare against its independent population on the accepted finite scope.
- Turn the prose recursion into a complete named correctness proposition with explicit vertex/edge accounting.
- Retain named star and branched-tree cases, and expose height-state counts separately from polynomial support sizes.

**Next concrete action:** Extend the existing transfer engine's instrumentation and acceptance fixtures; avoid creating a replacement tree enumerator.

### P10

**Prove safe volume truncation.** Status: `implemented_pending_acceptance`. Dependencies: P09. Remaining effort: S; priority: 1.

**Existing work:** Convolutions prune by nonnegative total volume. Tests compare pruned with full histograms and verify H=R coefficients against the unrestricted composition engine. The H=2, R=12 path experiments check every retained volume marginal independently, including n=96.

**Evidence:** [src/singularity/transfer.py](../src/singularity/transfer.py); [tests/test_transfer.py](../tests/test_transfer.py); [docs/chapters/13_research_program.md](../docs/chapters/13_research_program.md); [scripts/benchmark_transfer.py](../scripts/benchmark_transfer.py); [results/transfer_benchmark.json](../results/transfer_benchmark.json).

**Acceptance still missing:**

- Close P09's acceptance and publish a full truncation correctness argument, including the H=R sufficiency statement.
- Separate the existing H=2 benchmark's bounded-height semantics from an unrestricted H=R large-tree demonstration; low volume does not make H=2 unrestricted at R=12.

**Next concrete action:** Promote the nonnegative-exponent argument to a named theorem and add one explicit larger H=R experiment with complete volume-energy semantics and a suitable independent check.

### P11

**Recover span by bounded-box subtraction.** Status: `partial`. Dependencies: P09, P10. Remaining effort: S; priority: 1.

**Existing work:** D_H=C_H-x^n C_(H-1) is implemented through min_zero=True, including a disconnected global-shift test and rejection of negative normalized counts. Exact span via D_H-D_(H-1) is described in prose.

**Evidence:** [src/singularity/transfer.py](../src/singularity/transfer.py); [tests/test_transfer.py](../tests/test_transfer.py); [docs/chapters/13_research_program.md](../docs/chapters/13_research_program.md); [src/singularity/heights.py](../src/singularity/heights.py).

**Acceptance still missing:**

- There is no forest-transfer API assembling complete (volume,energy,span) histograms from successive bounded boxes.
- No exhaustive marked-cell comparison of that span algorithm against direct marked enumeration exists.
- P09/P10 acceptance is open.

**Next concrete action:** Add exact-span differencing on top of bounded_height_histogram, investigate rather than clip negative results, and compare every marked cell with marked_coefficients on a declared forest population.

### P12

**Extend messages to bounded separators.** Status: `blocked`. Dependencies: P10, P11. Remaining effort: L; priority: 1.

**Existing work:** The manuscript specifies bag-height state counts and the need to separate state count from convolution cost. The only transfer implementation accepts forests and explicitly rejects cycles.

**Evidence:** [docs/chapters/13_research_program.md](../docs/chapters/13_research_program.md); [docs/chapters/11_archival_bridges.md](../docs/chapters/11_archival_bridges.md); [src/singularity/transfer.py](../src/singularity/transfer.py).

**Acceptance still missing:**

- No supplied-tree-decomposition type or checker exists.
- No bag-conditioned general-graph algorithm, local charge proof or cycle/bounded-width regression output exists.
- P10/P11 must establish the semantics and marked reconstruction used by the extension.

**Next concrete action:** Specify and validate decompositions first, implement a minimal introduce/forget/join or elimination convention with explicit charge ownership, and compare complete cycle histograms to the reference engine.

### P13

**Classify the first positive-energy layer.** Status: `implemented_pending_acceptance`. Dependencies: P06, P08. Remaining effort: S; priority: 2.

**Existing work:** SNG-F12 and SNG-A05 prove E>=lambda*span and characterize minimum-energy normalized profiles as binary minimum-cut sides. Tests enumerate heights 0..2 on connected simple graphs through four vertices, checking nonbinary exclusion and multiplicities.

**Evidence:** [docs/chapters/03_nested_heights.md](../docs/chapters/03_nested_heights.md); [docs/chapters/05_prime_arithmetic.md](../docs/chapters/05_prime_arithmetic.md); [src/singularity/invariants.py](../src/singularity/invariants.py); [tests/test_core.py](../tests/test_core.py).

**Acceptance still missing:**

- P06 and especially P08's kernel identity remain open.
- Record the existing theorem's acceptance receipt, scope and multiplicity comparison; finite tests supplement the general proof rather than prove it.

**Next concrete action:** Reuse the prose proof and exhaustive checks; when P08 is available, derive the formal min-cut corollary from the same nested identity and close the dependency gate explicitly.

### P14

**Compute the nested-pair census.** Status: `planned`. Dependencies: P05, P08. Remaining effort: M; priority: 1.

**Existing work:** The five coordinates (|S|,|T|,cut(S),cut(T),e(T,V\S)) and their projection to span-two volume/energy are specified. The fixed binary pair has a verified span-two discrepancy.

**Evidence:** [docs/chapters/13_research_program.md](../docs/chapters/13_research_program.md); [docs/chapters/03_nested_heights.md](../docs/chapters/03_nested_heights.md); [tests/test_core.py](../tests/test_core.py); [results/certificates/binary_census.json](../results/certificates/binary_census.json).

**Acceptance still missing:**

- No independent nested-pair tensor enumerator or retained tensor data exists.
- No tested projection equality or tensor-cell explanation of the binary pair is released.
- P05/P08 acceptance remains open.

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

**Add exact volume congruence filters.** Status: `planned`. Dependencies: P03. Remaining effort: S; priority: 2.

**Existing work:** The character-filter idea and its distinction from energy specialization and span extraction are explained. Cyclotomic arithmetic is already reusable.

**Evidence:** [docs/chapters/13_research_program.md](../docs/chapters/13_research_program.md); [src/singularity/polynomials.py](../src/singularity/polynomials.py); [src/singularity/conductor.py](../src/singularity/conductor.py).

**Acceptance still missing:**

- No public volume-residue filter or exact character-averaging check is implemented.
- No complete comparison with direct assignment volume residues is retained.
- P03 acceptance is open.

**Next concrete action:** Implement direct finite volume filtering and an independent cyclotomic character average, prove equality and document that neither recovers discarded span marks.

### P18

**Prove root-of-unity rationality in energy.** Status: `implemented_pending_acceptance`. Dependencies: P03, P17. Remaining effort: S; priority: 2.

**Existing work:** Exact cyclotomic rings, residue-cube numerator and arbitrary-index coefficient recovery are implemented with an explicit residue work budget. Tests compare direct local coefficients through volume 12 for two graphs and orders 1..4; a remote index 10^100 is checked. The coordinate-residue rationality argument is in prose.

**Evidence:** [src/singularity/conductor.py](../src/singularity/conductor.py); [tests/test_conductor_weighted.py](../tests/test_conductor_weighted.py); [docs/chapters/11_archival_bridges.md](../docs/chapters/11_archival_bridges.md); [docs/chapters/13_research_program.md](../docs/chapters/13_research_program.md); [results/conductor_example.json](../results/conductor_example.json); [scripts/reproduce.py](../scripts/reproduce.py).

**Acceptance still missing:**

- Close P03/P17 dependencies even though the existing energy-specialization implementation does not technically require a volume-filter API.
- Publish a named theorem-to-code acceptance map and retained independent coefficient comparisons for the selected numerator fixtures.

**Next concrete action:** Accept and document the existing conductor engine after dependency closure; extend its test scope only for a mathematical reason and keep positive-real analytic assertions separate.

### P19

**Analyze finite quadratic Gauss sums.** Status: `partial`. Dependencies: P18. Remaining effort: M; priority: 2.

**Existing work:** Chapter 11 derives the nondegenerate odd-prime formula when p does not divide the spanning-tree count and explains the free constant direction. It identifies singular discriminant primes as requiring a rank-sensitive replacement.

**Evidence:** [docs/chapters/11_archival_bridges.md](../docs/chapters/11_archival_bridges.md); [docs/chapters/13_research_program.md](../docs/chapters/13_research_program.md); [src/singularity/conductor.py](../src/singularity/conductor.py).

**Acceptance still missing:**

- No exact modular symmetric-form diagonalizer or complete singular-rank/discriminant formula is implemented and checked.
- No retained comparison between direct residue sums and diagonalized forms, including exceptional-prime examples, exists.
- P18 acceptance is open; characteristic two and prime powers remain outside this push unless separately proved.

**Next concrete action:** Implement odd-prime modular congruence diagonalization, derive the singular-direction factor explicitly, and test a graph with primes dividing its spanning-tree count against residue enumeration.

### P20

**Build the disjoint order-chamber formula.** Status: `partial`. Dependencies: P02, P06. Remaining effort: M; priority: 2.

**Existing work:** Label-based tie breaking, strict gaps at adjacent descents and volume n*d0+sum((n-j)*dj) are specified. The chamber approach is proposed as another independent finite representation.

**Evidence:** [docs/chapters/13_research_program.md](../docs/chapters/13_research_program.md); [docs/chapters/14_literature_and_claims.md](../docs/chapters/14_literature_and_claims.md); [src/singularity/heights.py](../src/singularity/heights.py).

**Acceptance still missing:**

- No executable chamber generator or explicit graph-dependent gap quadratic-form API exists.
- No complete uniqueness/coverage proof and tied-height histogram replay is released.
- P02/P06 acceptance is open.

**Next concrete action:** Derive the edge-wise gap quadratic form and implement tiny permutation chambers with strict-descent lower bounds; prove disjoint coverage and compare full finite histograms.

### P21

**Relate constrained heights to order polytopes.** Status: `planned`. Dependencies: P20. Remaining effort: M; priority: 2.

**Existing work:** Relevant order-polytope background and the warning that quadratic weighting is not automatically ordinary Ehrhart counting are documented.

**Evidence:** [docs/chapters/13_research_program.md](../docs/chapters/13_research_program.md); [docs/chapters/14_literature_and_claims.md](../docs/chapters/14_literature_and_claims.md); [docs/references.bib](../docs/references.bib).

**Acceptance still missing:**

- No explicit finite-poset constrained-height type, weak/strict inequality convention or derived unweighted bounded-height comparison is supplied.
- No theorem identifies the precise additional role of quadratic weighting.
- P20 chamber acceptance is open.

**Next concrete action:** Choose one finite poset class, derive its integer height counts with an explicit shift convention and test them before adding graph-energy weights.

### P22

**Establish one genuine reciprocity statement.** Status: `blocked`. Dependencies: P21. Remaining effort: L; priority: 3.

**Existing work:** The research program states the need for explicit boundary corrections and warns against an unproved weighted Ehrhart analogy. Complement/span reflection elsewhere is not the requested order-population reciprocity.

**Evidence:** [docs/chapters/13_research_program.md](../docs/chapters/13_research_program.md); [docs/chapters/14_literature_and_claims.md](../docs/chapters/14_literature_and_claims.md).

**Acceptance still missing:**

- P21 has not fixed the underlying order counting problem.
- No scoped reciprocity theorem with full proof, or certified counterexample to a chosen weighted extension, is present.

**Next concrete action:** After P21, formulate a single precise reciprocity candidate, compute all tiny cases including boundary strata, and accept either a proof or a rigorously explained counterexample.

### P23

**Implement formal logarithmic extraction.** Status: `implemented_pending_acceptance`. Dependencies: P03. Remaining effort: S; priority: 1.

**Existing work:** Sparse rational arithmetic, inverse series, logarithms, recursive and independent Mobius ordinary Euler exponents, and generalized-binomial recomposition are implemented. Exact tests reconstruct inputs and check identities. SNG-A07 proves the ordinary polynomial-exponent transform in prose.

**Evidence:** [src/singularity/polynomials.py](../src/singularity/polynomials.py); [src/singularity/euler.py](../src/singularity/euler.py); [tests/test_analytics.py](../tests/test_analytics.py); [docs/chapters/06_euler_analysis.md](../docs/chapters/06_euler_analysis.md); [src/singularity/certificates.py](../src/singularity/certificates.py).

**Acceptance still missing:**

- P03 acceptance is open; record a closure receipt connecting existing transform tests to portable inputs.
- Keep the prose integral bidegree/plethystic transform distinct: it is not the same implemented ordinary Euler exponent API and is not required to close this original push.

**Next concrete action:** Reuse the existing modules and run their acceptance checks on the accepted certificate population; do not implement a duplicate logarithm/Euler engine.

### P24

**Determine exceptional energy parameters.** Status: `partial`. Dependencies: P23. Remaining effort: M; priority: 1.

**Existing work:** Exact rational specialization and parameter-specific first differences exist. Factored reference discrepancies prove no interior real zero for the retained examples; endpoint coincidence and scaling are discussed.

**Evidence:** [src/singularity/euler.py](../src/singularity/euler.py); [src/singularity/polynomials.py](../src/singularity/polynomials.py); [tests/test_analytics.py](../tests/test_analytics.py); [docs/chapters/07_visibility_singularities.md](../docs/chapters/07_visibility_singularities.md); [docs/chapters/09_exact_examples.md](../docs/chapters/09_exact_examples.md).

**Acceptance still missing:**

- No general exact real-root isolation or algebraic-number specialization machinery exists.
- No released parameter-stratum object recomputes first visibility depth at every isolated exceptional value.
- P23 acceptance is open.

**Next concrete action:** First retain complete root certificates for the factored reference polynomials; then add a controlled algebraic root-isolation path and recomputation test for a polynomial with an actual interior exceptional root.

### P25

**Organize successive visibility levels.** Status: `partial`. Dependencies: P23, P24. Remaining effort: M; priority: 1.

**Existing work:** SNG-F16 proves prefix equivalence and the ultrapseudometric in prose. first_difference and finite_signature distinguish a witness from agreement through a cutoff; the census reports prefix class counts.

**Evidence:** [src/singularity/euler.py](../src/singularity/euler.py); [docs/chapters/04_observation_hierarchy.md](../docs/chapters/04_observation_hierarchy.md); [docs/chapters/07_visibility_singularities.md](../docs/chapters/07_visibility_singularities.md); [results/exact_examples.json](../results/exact_examples.json); [scripts/census.py](../scripts/census.py); [results/small_census.json](../results/small_census.json).

**Acceptance still missing:**

- No complete parameter-stratified filtration with retained memberships and bounds is released.
- P24's algebraic exceptional strata are absent and P23 is not accepted.
- No unrestricted depth theorem follows from the existing three small comparison pairs or n<=6 census.

**Next concrete action:** Define a machine-readable bounded filtration record, retain every equality range and unresolved cutoff, and layer P24's exact parameter strata onto it.

### P26

**Make analytic remainder bounds explicit.** Status: `implemented_pending_acceptance`. Dependencies: P25. Remaining effort: S; priority: 1.

**Existing work:** SNG-A14 supplies explicit constants and a normalized logarithmic tail bound for s>1/(r+1), with a finite-prime cutoff condition. arithmetic.py provides a separate conservative exact majorant and a boundary tail C*r/N at P=N^r. Parameter and radius guards are tested.

**Evidence:** [docs/chapters/07_visibility_singularities.md](../docs/chapters/07_visibility_singularities.md); [src/singularity/arithmetic.py](../src/singularity/arithmetic.py); [tests/test_arithmetic.py](../tests/test_arithmetic.py); [docs/chapters/06_euler_analysis.md](../docs/chapters/06_euler_analysis.md).

**Acceptance still missing:**

- Close P25 and bind numerical hypotheses to an accepted exact first-discrepancy record; the tail routine explicitly does not certify those hypotheses.
- Record the relationship between the manuscript's sharper constant and the code's conservative alternative, plus finite-small-prime treatment in an end-to-end acceptance calculation.

**Next concrete action:** Publish a theorem-to-code derivation for the conservative constant and an exact hypothesis receipt from a certified pair, then expose finite small-prime handling for P27.

### P27

**Produce controlled real singularity experiments.** Status: `planned`. Dependencies: P26. Remaining effort: M; priority: 1.

**Existing work:** Exact tail constants and local truncation estimates are available as foundations. No retained prime-product numerical experiment is included in results/.

**Evidence:** [src/singularity/arithmetic.py](../src/singularity/arithmetic.py); [docs/chapters/07_visibility_singularities.md](../docs/chapters/07_visibility_singularities.md); [tests/test_arithmetic.py](../tests/test_arithmetic.py).

**Acceptance still missing:**

- No rigorous finite-prime local-factor evaluation with truncation enclosures exists.
- No normalized remainder intervals near s=1/r or demonstrated recovery of the established asymptotic within those intervals is released.
- P26 acceptance is open.

**Next concrete action:** Build interval-enclosed local sums and finite prime products, attach both local truncation and omitted-prime error bounds, and retain a small fully certified table before attempting plots.

### P28

**State the available complex domain exactly.** Status: `partial`. Dependencies: P26. Remaining effort: M; priority: 2.

**Existing work:** SNG-A10 proves normal tail convergence on compact subsets of the finite-extraction half-plane; SNG-A11 supplies a holomorphic nonzero neighborhood of the positive real visibility point. Small-prime denominators and the power-series branch of log(1-p^-rs) are explicitly discussed; global meromorphic continuation is not claimed.

**Evidence:** [docs/chapters/06_euler_analysis.md](../docs/chapters/06_euler_analysis.md); [docs/chapters/07_visibility_singularities.md](../docs/chapters/07_visibility_singularities.md).

**Acceptance still missing:**

- The local complex neighborhood is established existentially, without an explicit computable disk or certified nonvanishing domain for the selected pair.
- Supply domain/branch bookkeeping for all finite denominator factors and the normally convergent tail in a focused statement.
- P26 acceptance is open.

**Next concrete action:** Choose one fixed rational interior q and derive a conservative explicit disk around s=1/r with certified finite-factor nonvanishing and uniform tail convergence.

### P29

**Specify a complete finite graph census.** Status: `partial`. Dependencies: P03. Remaining effort: S; priority: 1.

**Existing work:** Every labeled simple graph through n=6 is generated, connectedness is checked and degree-respecting permutations give an exact isomorphism quotient. Graph representatives, canonical codes, scope and labeled/unlabeled counts are retained; n=6 yields 26704 connected labeled graphs and 112 classes.

**Evidence:** [scripts/census.py](../scripts/census.py); [results/small_census.json](../results/small_census.json); [docs/IMPLEMENTATION.md](../docs/IMPLEMENTATION.md); [scripts/check_repository.py](../scripts/check_repository.py).

**Acceptance still missing:**

- No canonical per-graph source-hash manifest or independent generation-count reconciliation receipt is released.
- The retained finite graph list must be separated from aggregate invariant summaries so later comparisons reuse exactly the same population.
- P03 acceptance is open.

**Next concrete action:** Freeze the current n<=6 representatives into a hashed input manifest, independently reconcile the known counts and record generation/canonicalization options without expanding the search scope yet.

### P30

**Measure collision classes across invariants.** Status: `partial`. Dependencies: P12, P14, P29. Remaining effort: M; priority: 2.

**Existing work:** The census records complete binary class counts, local/marked class counts by depth through volume six and final unresolved local/marked classes. n<=6 height and binary observations all separate by volume three.

**Evidence:** [scripts/census.py](../scripts/census.py); [results/small_census.json](../results/small_census.json); [src/singularity/invariants.py](../src/singularity/invariants.py); [docs/IMPLEMENTATION.md](../docs/IMPLEMENTATION.md).

**Acceptance still missing:**

- No Laplacian spectral partition is retained in the census output.
- Full binary and intermediate prefix class memberships, first-discrepancy witnesses and structured resource limits are absent.
- P12/P14/P29 dependencies are open; existing small graphs are not a substitute for their acceptance.

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
- P06/P12/P31 are open.
- The latest chat's large-girth delayed-visibility and terminal-interface ideas are conjectural research directions, not accepted proofs or replacements for P32.

**Next concrete action:** Choose one narrow family from accepted collision evidence, formulate a uniform statement and pursue either a proof or explicit counterfamily with all construction hypotheses checked.

### P33

**Verify concrete coefficient certificates in a kernel.** Status: `blocked`. Dependencies: P07, P08, P23. Remaining effort: L; priority: 3.

**Existing work:** Python replay reconstructs declared coefficients and rejects altered sectors. This is independent finite computational checking, not a kernel-connected enumeration proof.

**Evidence:** [src/singularity/certificates.py](../src/singularity/certificates.py); [results/certificates/spectral.json](../results/certificates/spectral.json); [results/certificates/binary_census.json](../results/certificates/binary_census.json); [docs/chapters/12_computational_methodology.md](../docs/chapters/12_computational_methodology.md); [tests/test_analytics.py](../tests/test_analytics.py).

**Acceptance still missing:**

- P07/P08 formal definitions and identities are absent; P23 is not accepted.
- No kernel theorem connects parsed records to the mathematical coefficient definition or verifies both decisive pair multiplicities.
- Kernel tests rejecting a changed graph edge and coefficient remain absent.

**Next concrete action:** After formal foundations compile, define a verified finite enumeration/checking path and connect it to both existing packets; prove its soundness rather than only verifying a parser.

### P34

**Formalize the visibility comparison boundary.** Status: `blocked`. Dependencies: P26, P33. Remaining effort: L; priority: 3.

**Existing work:** The first-discrepancy ratio law and real zeta-factor asymptotic are proved in mathematical exposition with explicit branch and convergence scope.

**Evidence:** [docs/chapters/07_visibility_singularities.md](../docs/chapters/07_visibility_singularities.md); [docs/chapters/06_euler_analysis.md](../docs/chapters/06_euler_analysis.md); [docs/papers/visibility.md](../docs/papers/visibility.md).

**Acceptance still missing:**

- P26/P33 acceptance remains open and no formal analysis project exists.
- No exposed list of imported analytic theorems, compiling local-expansion-to-asymptotic chain or precisely recorded unformalized boundary is supplied.

**Next concrete action:** Inventory the chosen proof assistant's actual analytic libraries, formalize the finite local expansion first, and record every remaining analytic assumption without claiming full-chain verification until it compiles.

### P35

**Release the first focused manuscript.** Status: `partial`. Dependencies: P04, P05, P26, P27, P33. Remaining effort: M; priority: 3.

**Existing work:** A six-page focused article with editable sources, literature context, finite examples and the real comparison theorem is already released. Independent computational replay and claim-scope guidance exist. It makes no kernel-verification or priority claim.

**Evidence:** [docs/papers/visibility.md](../docs/papers/visibility.md); [docs/visibility_paper.tex](../docs/visibility_paper.tex); [docs/visibility_paper.html](../docs/visibility_paper.html); [output/pdf/visibility_paper.pdf](../output/pdf/visibility_paper.pdf); [docs/references.bib](../docs/references.bib); [results/validation.json](../results/validation.json); [scripts/reproduce.py](../scripts/reproduce.py).

**Acceptance still missing:**

- The original acceptance gate explicitly depends on P33; a readable article does not satisfy that absent kernel work.
- P27's controlled experiments and the remaining P04/P05/P26 acceptance records are absent.
- A final claim-by-claim proof/certificate matrix and submission-focused literature comparison must be reconciled with achieved scope.

**Next concrete action:** Treat the current article as a reusable draft. Build its claim matrix and update it as dependencies close; if publication is pursued earlier, record an explicit roadmap dependency amendment rather than silently marking P35 complete.

### P36

**Choose the second paper from actual results.** Status: `blocked`. Dependencies: P19, P22, P31, P32, P35. Remaining effort: L; priority: 3.

**Existing work:** Candidate B (exact tree/separator methods) and Candidate C (structural preservation) are clearly described as future papers. Their theorem centers are not declared achieved.

**Evidence:** [docs/chapters/14_literature_and_claims.md](../docs/chapters/14_literature_and_claims.md); [docs/chapters/13_research_program.md](../docs/chapters/13_research_program.md); [docs/development/PUSHES.md](../docs/development/PUSHES.md).

**Acceptance still missing:**

- P19/P22/P31/P32/P35 outcomes have not been accepted.
- No second paper is selected around an actual substantial theorem or decisive negative classification, with focused literature comparison and reproduced artifacts.
- The open-problem ledger must distinguish original pushes from any newly approved terminal-interface or delayed-visibility branch.

**Next concrete action:** Wait for substantive accepted results, then select one coherent paper center and package that result; preserve unfinished branches in the ledger instead of combining them into a larger manuscript.

## How to update the ledger

After each push, update this document and `push_status.json` together. Cite the exact new source, theorem, tests and retained output. Record the command actually run and its scope. Preserve unresolved questions and negative results. Promote a push to `complete` only after checking its own acceptance and each dependency's closure or an explicitly approved amendment. A commit title, code file or paper-shaped PDF is not by itself an acceptance receipt.

For a mathematical dependency that remains open, retain `implemented_pending_acceptance` when the central deliverable exists, `partial` when substantive own requirements remain, and `blocked` when the central target cannot yet be evaluated. Do not make the status more optimistic solely because another agent reported success.
