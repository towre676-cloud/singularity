# Implementation and retained computational results

The mathematical manuscripts describe a research program, while this chapter records the executable boundary of version 0.1.0. The core package requires Python 3.10 or newer and uses only the standard library. Documentation generation additionally uses Pandoc and a LaTeX installation. The rendered PDF and HTML are distributed so that a reader does not need those authoring tools merely to read the work.

## Installing and running the project

From the repository root, `python -m pip install -e .` installs the command `singularity`. An installation-free alternative is to set `PYTHONPATH=src` and invoke `python -m singularity`. The commands emit structured JSON so a retained calculation can be consumed by another experiment. Human explanations and proofs live in the monograph; JSON field names are not intended to replace the mathematical exposition.

`python -m singularity examples` prints the four original seven-vertex sources. `python -m singularity compare binary_g binary_h --max-volume 3` recovers their binary-census equality and first local difference. The parameter `--q 1/2` uses an exact rational, and the reported value is an exact fraction. A vanishing specialization is reported without pretending that a symbolic discrepancy remained visible at that parameter.

`python -m singularity profile --example binary_g --max-volume 4` returns the degree data, exact Laplacian polynomial, binary census, local coefficients, normalized coefficients and marked height sectors. The input can instead be a JSON object with an integer vertex count and an explicit edge list. Original vertex labels are retained throughout all finite populations. Isomorphism is a separate mathematical quotient, never an implicit division of multiplicities.

## Implemented mathematical modules

The meaning of every public coefficient, population and certificate interface is fixed in the [coefficient specification](specifications/COEFFICIENTS-v1.md).

| Module | Exact object | Current capability |
|---|---|---|
| `graph` | Finite simple graph and integer quadratic energy | Validation, components, relabeling, cuts, Laplacian, signed integer height energy |
| `heights` | Total-height and span-marked populations | Weak compositions, local coefficients, minimum-zero normalization, marked sectors |
| `invariants` | Binary and linear-algebraic comparisons | Complete binary cut census, minimum-cut side sizes, integer characteristic polynomial, first finite difference |
| `population` | Constrained original-labeled height tuples | Exact counts, lexicographic rank/unrank, feasibility witnesses and finite bound certificates |
| `polynomials` | Sparse rational q-polynomials and formal x-series | Exact arithmetic, logarithms, specialization, JSON conversion and factor replay |
| `euler` | Formal zeta exponents | Recursive and Mobius inversion, generalized-binomial recomposition, parameter-specific first discrepancy |
| `transfer` | Bounded-height forest populations | Separator messages on trees/forests, volume pruning, joint volume-energy histograms and minimum-zero subtraction |
| `conductor` | Root-of-unity local series | Integer cyclotomic rings, finite residue numerators, arbitrary-index exact coefficients with explicit residue-box budget |
| `weighted` | Positive integral vertex masses and edge weights | Parallel-weight aggregation and hard equality contraction preserving original energy and mass-weighted height |
| `arithmetic` | Prime-valuation populations | Positive integer factorization, finite Dirichlet coefficients, conservative exact local remainder and tail constants |
| `primitive` | Gcd-one normalized height profiles | Mobius extraction, independent gcd enumeration and exact scaling recomposition |
| `chains` | Weakly nested level chains | Direct chain generation with repeated levels, nested-boundary energy, marked/normalized/local coefficients independent of weak compositions |
| `certificates` | Source-bound finite mathematical claims | Structural parser, two independent replay routes (stars-and-bars and level chains), nested-cut checks, normalization and factorization checks |

The primitive module implements a useful extension of the foundational scaling identity. For every nonzero normalized profile a, its positive coordinate gcd d is unique; dividing by d produces a primitive profile. Total height and span scale by d, while energy scales by d squared. Consequently full marked populations are recovered from primitive populations by a finite divisor sum in every retained volume. The inverse operation uses the ordinary Mobius function on the scaling factor. The released test checks both directions on every simple graph through four vertices at a declared finite depth.

## Population navigation and exact bounds

The command `population --example binary_g --volume 3 --span 2 --sample 5` compiles the 42 ordered profiles of type 2e_i+e_j. Additional exact or upper-bound constraints may restrict energy, total height, coordinate height and span. The compiler records why its search domain is finite. A bound supplied by the total height is different from a bound inferred from connectedness and energy; that distinction remains visible in the report.

The ranking order is lexicographic in the original coordinate tuple. `--rank` checks a proposed tuple and reports its membership and index; `--unrank` reconstructs an original tuple from an index. Prefix completion counts make these operations possible without storing every completed tuple. Their computational cost still depends on the graph's frontier and on the active constraints. The package does not advertise a uniform polynomial-time procedure for arbitrary graphs or arbitrary energy budgets.

## Forest transfer experiment

The forest engine conditions each subtree on the height at its root. Combining a child charges the connecting edge exactly once and convolves the child's volume-energy histogram. A final convolution joins disconnected components. The implementation rejects cycles instead of applying a tree formula to an unsupported graph. A Cartesian enumerator provides an independent oracle on small graphs.

For the path on 96 vertices, heights in 0,1,2, and total height at most 12, the retained population has exactly 2,506,262,962,660,245 original labeled profiles. This is a restricted low-volume population, rather than the entire height cube of size 3^96. Every volume marginal is independently checked against

\[
 [x^v](1+x+x^2)^{96}
 =\sum_{j\ge0}(-1)^j\binom{96}{j}\binom{v-3j+95}{95},
\]

with inadmissible binomial coefficients treated as zero. The report in `results/transfer_benchmark.json` records both counts and measured execution times. Timing is an environmental observation. The arithmetic identities and retained population definition are the reproducible mathematical conclusions.

## Complete small-graph census

The script `scripts/census.py` enumerates every labeled simple graph through six vertices, filters connected graphs, and takes an exact isomorphism quotient using degree-respecting permutations. This is an intentionally modest exhaustive baseline. It avoids a hidden external graph database or an unrecorded canonical-labeling dependency. Its work limit is explicit: graph orders one through six.

| Vertices | Connected labeled graphs | Connected isomorphism classes | Degree-layer classes | Through volume 2 | Through volume 3 |
|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 1 | 1 | 1 | 1 |
| 2 | 1 | 1 | 1 | 1 | 1 |
| 3 | 4 | 2 | 2 | 2 | 2 |
| 4 | 38 | 6 | 6 | 6 | 6 |
| 5 | 728 | 21 | 19 | 21 | 21 |
| 6 | 26704 | 112 | 68 | 100 | 112 |

Here the degree layer is the complete coefficient polynomial at volume one, not a single numeric evaluation. Local and fully marked prefixes produce the same class counts on this retained census. All 112 connected six-vertex classes separate by volume three, and the complete binary census also separates them. The seven-vertex binary collision demonstrates why this finite observation cannot be promoted to a reconstruction theorem. The census gives a reproducible starting point for measuring how visibility changes as the graph population expands.

## Reproduction and document generation

`make test` runs the standard-library suite. `make examples` regenerates the three reference comparisons, graph inputs, finite certificates and a remote conductor coefficient. `python scripts/reproduce.py --check` recomputes these results and compares them with their retained JSON. `python scripts/benchmark_transfer.py` reruns the path experiments. The exhaustive census is separate because its search scope is broader than the routine example replay.

`make book` assembles the chapter sources into a navigable monograph, generates LaTeX and HTML, and compiles the mathematical PDF. The shorter article in `docs/papers/visibility.md` provides a paper-shaped entry to the central construction and visibility theorem. `make release` performs the checks and creates a complete archive with source, documents, tests, inputs and results. Generated archives exclude earlier archives, temporary files and the local git object directory, preventing recursive packaging.

The released finite calculations are computational evidence for their declared inputs. The proofs in the manuscript establish the mathematical identities and analytic transfer statements with their stated hypotheses. Neither the software tests nor a source digest imply a proof-assistant verification of the implementation. This separation lets later pushes strengthen formal coverage without rewriting the meaning of the existing results.
