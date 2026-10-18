# Architecture and reuse map

## Read selectively

Orient with `CLAUDE.md`, `handoff/START_HERE.md`, the latest session checkpoint and `docs/papers/second_paper_choice.md`. P01–P36 are complete; the original task packets remain acceptance history. Read selected modules, tests and proof sections for a new frontier instead of reopening completed items. The 146-page monograph is reference material.

| Layer | Source files | Current contract |
|---|---|---|
| Graph input | `graph.py`; `data/graphs/*.json` | Immutable labeled simple graphs, validated edges and integer energy; connectedness is a separate hypothesis. |
| Coefficient specification | `docs/specifications/COEFFICIENTS-v1.md`; `heights.py` | Local, global minimum-zero and span-marked populations with exact multiplicities. |
| Independent chain search | `chains.py`; `tests/test_chains.py` | Nested subsets generated directly, repeated levels and mixed quadratic terms included. |
| Finite invariants | `invariants.py`; `examples.py`; `lowvolume.py`; `nested_census.py` | Binary census, cuts, characteristic polynomials, low-volume formulas and nested-boundary statistics. |
| Constrained navigation | `population.py` | Original-label count/rank/unrank and witnesses under finite constraints. |
| Exact algebra | `polynomials.py`; `euler.py` | Sparse Fraction polynomials, logarithms, Euler exponents and independent recomposition. |
| Portable certificates | `certificates.py`; `results/certificates/` | `singularity.certificate/1`, independent finite replay, chain comparison and malformed-input rejection. |
| Forest transfer | `transfer.py` | Bounded-height exact histograms, safe volume truncation and marked recovery; forest-specific entry points reject cycles. |
| General separators | `decomposition.py`; `tests/test_decomposition.py` | Explicit tree-decomposition validation, unique charge ownership, cyclic-graph transfer and marked coefficients. |
| Terminal responses | `terminals.py`; `tests/test_terminals.py` | Ordered kernels, graph gluing, twist differences, marked gluing, star-probe reconstruction and rooted decks. |
| Restricted contexts | `contexts.py`; `tests/test_contexts.py` | Symmetric probes, exact quotient ranks, finite-difference recovery and realization constraints. |
| Charge compilation | `charges.py`; `tests/test_charges.py` | Boundary-charge tables, kernel reconstruction, dominating-block sequence, closure transport and ordered observation charts. |
| Locality and inverse | `locality.py`; `tests/test_locality.py` | Connected-support compiler, cycle reconstruction, moment enrichment, regular-background and overlap corrections. |
| Structural families | `families.py`; `tests/test_families.py` | Explicit delayed-visibility constructions and exact discrepancy checks. |
| Arithmetic specializations | `conductor.py`; `congruence.py`; `gauss.py` | Cyclotomic residue numerators, volume characters and finite quadratic sums with declared domains. |
| Effective analysis | `arithmetic.py`; `certified.py`; `visibility.py`; `parameters.py` | Valuations, explicit tails, outward-rounded experiments, visibility filtration and exceptional parameters. |
| Order geometry | `chambers.py`; `orders.py` | Disjoint tie-broken chambers, constrained heights and precisely scoped reciprocity results. |
| Other exact models | `weighted.py`; `primitive.py` | Integral masses/weights and contractions; gcd-one profiles and independent inversion checks. |
| CLI | `cli.py`; `__main__.py` | Thin argparse interface; inspect current `--help` instead of copying an imagined command. |

Bare module paths are relative to `src/singularity/`. Query current signatures before extending an API. `PROJECT_CONTRACT.md` and the versioned specification describe shared semantics.

## Data shapes and boundaries

`local_coefficients(G,R)` returns R+1 dictionaries `{energy: multiplicity}`. `marked_coefficients(G,R)` returns `{(volume,energy,span): multiplicity}`. Forest and decomposition histograms use `(volume,energy)` keys. Sparse rational q-polynomials use `Fraction`; JSON rational polynomials use `[degree,numerator,denominator]` triples. A missing monomial means zero. JSON booleans are not integer counts.

Terminal kernel entries are conditioned on ordered terminal heights and count internal volume. Assembly charges terminal volume once. The checked decomposition assigns every vertex and edge to one owner. Duplicate shared-terminal edges require the API's explicit validation; they cannot be silently counted twice. Charge tables reorganize those responses rather than introducing a different energy.

Exactness does not imply cheap enumeration. Preserve certificate/residue budgets. Report height-state counts, polynomial support, convolution work and coefficient bit lengths separately. A budget refusal must be explicit rather than returning an incomplete histogram.

## Formal proof packages

`formal/` pins Lean 4.12.0 with no external mathematical library. `scripts/check_formal.py` builds and audits 91 release declarations, including normalization, threshold identities, decisive finite certificates and the core conditional visibility development. Its conditional analytic theorem is retained as a separately buildable component.

`formal-analysis/` pins Mathlib and its transitive manifests and imports `formal/` as a path dependency. `scripts/check_formal_analysis.py` builds and audits 79 declarations proving actual real local-series convergence, logarithmic estimates, prime products, zeta factorization and positive boundary limits. The concrete pair theorems discharge finite hypotheses. `results/formal_analysis_audit.json` binds the audit to sources and manifests. Setup and exact scope are in `formal-analysis/README.md`; neither package claims global complex continuation.

## Reproduction and publication pipeline

`scripts/reproduce.py --check` retains the original comparisons and certificates. `scripts/locality_family.py --check`, `scripts/overlap_hierarchy.py --check` and `scripts/loop_series.py --check` replay structural receipts relevant to the selected second paper. Other scripts retain chain, context, charge, arithmetic and census data. Read a script's declared bounds before rerunning it; a complete small census is not permission to increase the order casually.

The fourteen authored chapters, implementation appendix and original roadmap assemble into `docs/MONOGRAPH.md`. `scripts/build_documents.py` renders that book and the sources `docs/papers/visibility.md` and `docs/papers/locality.md` into PDF, HTML and LaTeX. Current outputs are 146, 10 and 8 pages. `results/manuscript_counts.json` records source counts. Preserve the fourteen-chapter checks unless deliberately changing the document architecture.

HTML includes embedded MathML, CSS and illustrations. Markdown and LaTeX graphics paths have distinct reading contexts. Regenerate affected outputs and inspect mathematical layout after source changes. `scripts/package_release.py` creates `releases/Singularity-v0.2.0-complete.zip`, with all paths under `singularity/` and per-file hashes. It excludes `.git`, Lean caches and earlier archives; it contains no Git bundle.

## Continuing efficiently

The current frontier is described in `docs/papers/second_paper_choice.md`. Reuse the decomposition engine inside connected footprints before inventing a third unrelated coefficient engine. Preserve independent weak-composition oracles for small supports, direct gluing oracles for terminal work, exact polynomial identities and source-bound formal audits. Match each new claim to its proof scope; finite prefix agreement cannot establish a full-series collision.
