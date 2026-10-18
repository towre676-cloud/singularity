# Claim and reproduction register: exact observation depth

Audit date: 18 October 2026. Article: `docs/papers/locality.md`. Selection packet: `docs/papers/second_paper_choice.md`. This register distinguishes complete ordinary mathematical proofs, implemented finite checks, retained timings and explicitly open questions. The general locality and reconstruction theorems in this article are **not Lean-formalized**.

| Article claim | Evidence and precise scope | Status |
|---|---|---|
| Equation (1), fixed-volume polynomial finiteness | Weak compositions of j into n labeled coordinates; n>0 formula stated | Definition and elementary proof |
| Connected-support expansion, Theorem 1 | Complete multivariate support/inclusion–exclusion proof in §2; SNG-F55 | Proved over Q[q][[x]] |
| Ambient degrees persist on restricted subsets | Equation (2), edge to a zero-height outside vertex contributes d_H(v)h_v² | Proved; crucial normalization |
| Decorated statistics determine truncated series | Theorem 1; only the forward implication is asserted | Proved; converse unclaimed |
| Recursion and integrality, Proposition 2 | Formal identity xF'=F x(log F)'; inverse of an integer series | Proved |
| Linear graph-size cost at fixed R,Δ,λ | Conservative walk count, at most 2^R restrictions and 4^R profiles each, exponent range in Proposition 2 | Proved arithmetic-operation upper bound; coefficient bit cost separate; no claim polynomial in R |
| Exact memoization | `src/singularity/locality.py`: AHU tree encodings, bounded small canonicalization, vertex-set fallback | Implemented; independent oracle and code review |
| First-cycle coefficient, Theorem 3 | Quotient-partition induction for injective tree counts and multilinear connected-spanning-edge formula in §3; SNG-F56 | Proved for equal-order regular simple graphs with girth≥g≥3 |
| Cube–Möbius discrepancy | `results/locality_family.json` `first_cycle`; equality with `results/exact_examples.json` reference polynomial | Exact finite replay for λ=0,2 |
| Prism–K3,3 discrepancy | Same receipt, independent degree/triangle interpretation | Exact finite replay for λ=0,2 |
| Cycle collision family for every g≥3 | Corollary 4 follows from Theorem 3; independent finite-matrix exterior-square proof (11) | Proved; finite receipt g=3…8; independent composition oracle g≤6 |
| Context-independent leading discrepancy | Complete energy decomposition and unit-triangular transformation proof, Proposition 5; SNG-F53–F54 | Proved for fixed two-terminal closing contexts with declared gluing |
| Fifteen-vertex shared-neighbor gluing coefficient | `results/locality_family.json` `dominating_closure`; direct full-graph weak compositions; 729/8388608 at volume6, q=1/2 | Exact finite replay; no extrapolation |
| Background b and cycle corrections | Exact path contributions with ambient degree2 and pinning2; formal local finiteness in (13) | Proved |
| Sharp reconstruction floor(n/2) | Complete Theorem 6: triangular inverse, at most one longer remaining component, even/odd sharpness families | Proved for known n and every q∈(0,1); sharp n≥6 |
| Cycle reconstruction population | `results/locality_family.json` `reconstruction`: 57 partitions into cycle lengths≥3 through total order14 | Exact finite replay; population boundary explicit |
| Ten-graph independent compiler oracle | Same receipt `oracle`: weak compositions against locality, budget4, shifts0,2 | Exact finite replay |
| Timings | Same receipt `benchmark`: graph seed n, exact series comparison for baseline runs n16,32 at R4 | Retained machine-specific observations; not rerun in deterministic checks |
| Large separator-state estimates | Sum (R+1)^bag_size in actual heuristic decomposition | Representation estimate; not timing or universal lower bound |
| Established connected-subgraph framework | Patel–Regts2017 §3, Lemma3.5/Theorem3.7 and Patel–Regts2019 | Verified primary comparisons; no general-method priority claim |
| Loop and Gaussian-model context | Chertkov–Chernyak2006 and Bauerschmidt–Park–Rodriguez2024 | Verified primary context; distinct normalizations and questions stated |
| General fixed-pinning completeness and efficient reconstruction beyond cycle class | §7 | Open, not implied by finite enumeration |

## Independent review

The independent reviewing agent examined the selected theorem center, the implementation and the primary antecedents. It independently reproduced `scripts/locality_family.py --check` successfully. It requested precise handling of finite transfer truncation, known graph order, ambient degree, parameter endpoints, coefficient bit complexity and the absence of a converse to locality; all are made explicit in the article. It also identified two full-graph edge scans in local implementation paths, which were reported to the integrating session to preserve the intended graph-size cost on families with many small cyclic supports. After reading the complete final draft, the independent reviewer recommended acceptance of the P36 mathematical center and found no remaining proof gap. The primary PR2019 bibliographic record and the longer CC2006 paper were independently checked as well. Final rendered-page inspection is recorded by the integrating release.

## Reproduction commands

From a clean checkout with Python3.10 or later, run `PYTHONPATH=src python scripts/locality_family.py --check` for the deterministic article receipt and `PYTHONPATH=src python scripts/reproduce.py --check` for the unchanged regression pairs. The finite reconstruction does not call a graph-isomorphism package. `PYTHONPATH=src python -m unittest discover -s tests -v` exercises the core and malformed-input tests. Running `python scripts/build_documents.py` creates the article's HTML, LaTeX and PDF alongside the first paper and monograph. Rendered-page inspection and the archive integrity check are release steps recorded in `results/publication_release.json` and the session log.

The source and data have no external service dependency. Pandoc, XeLaTeX and a PDF renderer are document-build dependencies, not dependencies of exact counting. Historical-priority review and journal acceptance are not claimed by the roadmap's use of “release”.

## Rendered inspection

The first release render of this article has eight A4 pages. All pages were rasterized at 110 dpi and inspected in full-page contact sheets; the dense triangular-reconstruction equation on page 6 was additionally inspected at full rendered size. No clipped equations, table collisions, missing symbols or overfull boxes were found. The companion visibility paper has ten pages and was likewise inspected, including its certified-interval table on page 7. One overfull inline source path on its page 2 was replaced with a descriptive linked label before the final render. Temporary review images are in `tmp/pdfs/paper-review/` and are excluded from the release archive. The final integration record binds the inspected outputs to file hashes.
