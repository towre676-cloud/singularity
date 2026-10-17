# Architecture and reuse map

## Read selectively

Start with CLAUDE.md, START_HERE.md, the status ledger and the selected task packet. Read the matching module, tests and chapter before changing it. The 105-page monograph is reference material; loading it indiscriminately into every session wastes context and obscures the active acceptance contract.

| Layer | Existing files | Contract and extension boundary |
|---|---|---|
| Graph input | src/singularity/graph.py; data/graphs/*.json | Immutable labeled simple graph; validation and exact integer energy; connectedness is a separate hypothesis |
| Height populations | heights.py; tests/test_core.py | Weak compositions, local coefficients, common-shift normalization, marked coefficients, threshold identity |
| Finite invariants | invariants.py; examples.py | Complete binary subset census, minimum cuts, exact integer Laplacian characteristic polynomial |
| Constrained navigation | population.py; tests/test_population.py | Exact completion counts, lexicographic original-label rank/unrank, witnesses under bounded constraints |
| Polynomial arithmetic | polynomials.py | Sparse q-polynomials with Fraction coefficients; exact x-series operations; integer rational JSON triples |
| Euler transforms | euler.py; tests/test_analytics.py | Formal logarithms, two exponent calculations, recomposition, finite first-difference signatures |
| Certificates | certificates.py; results/certificates/*.json | singularity.certificate/1; independent replay-local compositions and energies; source digest is integrity only |
| Forest transfer | transfer.py; tests/test_transfer.py | Bounded-height joint volume/energy histograms; global minimum-zero subtraction; cycles rejected |
| Finite conductors | conductor.py; tests/test_conductor_weighted.py | Exact Z[t]/Phi_m arithmetic, residue numerator, remote coefficient; explicit profile budget |
| Weighted graphs | weighted.py | Integral vertex masses and edge weights, parallel aggregation and hard contraction; not the same input type as Graph |
| Arithmetic tuples | arithmetic.py; tests/test_arithmetic.py | Valuations, finite Dirichlet coefficients and conservative analytic tail constants |
| Primitive profiles | primitive.py; tests/test_primitive.py | Gcd-one marked counts, Mobius inversion and independent direct-gcd oracle |
| User interface | cli.py; __main__.py; pyproject.toml | Thin argparse interface; preserve exact JSON conventions and meaningful error messages |

Paths abbreviated in this table are relative to src/singularity unless tests or results are explicit. Read PROJECT_CONTRACT.md for exact shared API shapes. Query the code for current signatures rather than copying a proposed function name from chat.

## Coefficient shapes

local_coefficients(G,R) returns a list of length R+1; position m is a dictionary mapping energy to integer multiplicity. marked_coefficients(G,R) returns a dictionary mapping (volume,energy,span) to integer multiplicity. Forest transfer returns a dictionary mapping (volume,energy) to multiplicity. Sparse rational q-polynomials elsewhere map exponent to Fraction. Missing monomials represent zero. Do not turn dictionary iteration order into part of a mathematical claim.

Certificate integer count arrays and rational polynomial arrays have different shapes. A rational polynomial serializes as [degree,numerator,denominator] triples. JSON booleans must not be accepted as the integer count one. Certificate replay has a declared work limit; rejecting a request for exceeding it is not a disproof of the input mathematics.

## Reproduction and document pipeline

scripts/reproduce.py deterministically reconstructs three comparisons, six graph JSON inputs, three certificate packets and the conductor example. --check compares retained files without rewriting them. scripts/census.py generates a complete population within its stated order bound; do not casually increase its brute-force bound. scripts/benchmark_transfer.py verifies volume marginals independently and records measured support and runtime.

The authored monograph sources are docs/chapters/01_*.md through 14_*.md, docs/IMPLEMENTATION.md and docs/development/PUSHES.md. scripts/build_documents.py assembles docs/MONOGRAPH.md and generates LaTeX, HTML and PDFs. The two manuscript builders currently require exactly fourteen source chapters. Adding a chapter requires deliberately updating both build_documents.py and check_repository.py, not deleting old checks. The original 36-push roadmap and manuscript are historical sources; update them coherently when accepted work changes stated capability.

The HTML uses embedded MathML, embedded CSS and an embedded illustration. It does not depend on a machine-local JavaScript installation. GitHub displays HTML as a file; the README labels it as a download. The generated Markdown image path is assets/graph_pairs.png relative to docs/MONOGRAPH.md; the LaTeX graphics path includes docs/. Preserve both reading contexts when modifying document generation.

## Interfaces that are proposed, not implemented

There is no general tree-decomposition validator, no cyclic separator transfer engine, no standalone independent nested-chain enumerator and no terminal-kernel gluing module in the handoff baseline. There is no Lean project or proof-assistant build. These are work items rather than hidden capabilities. An ordered vertex-frontier algorithm would be a path-decomposition method; it would not alone satisfy P12's supplied tree-decomposition acceptance contract.

## Testing boundaries

Use the existing independent oracles. Weak compositions can check a new chain or separator method on genuinely small inputs. Cartesian bounded-height enumeration can check transfer and gluing. The independent Euler transform and recomposition check formal arithmetic. Direct gcd filtering checks primitive inversion. A path volume count from (1+x+...+x^H)^n checks transfer marginals without relying on the same energy algorithm.

For proposed separator work, report height-state counts, occupied polynomial terms, convolution work and coefficient bit lengths separately. For terminal gluing, charge terminal volume once and every edge once; duplicate edges between shared terminals require rejection or an explicitly proved correction. A resource limit must stop with an explicit refusal, never a silently incomplete histogram.
