# Singularity

**Exact graph-height populations, finite observation depth, and arithmetic visibility.**

Singularity asks what a graph reveals when its vertices carry nonnegative integer heights. It counts profiles by total height and squared edge differences, computes exactly when two graphs first become distinguishable, and relates that first discrepancy to a controlled real singularity of an Euler-product ratio.

For a finite graph $G$, the basic series is

$$
L_G(x,q)=\sum_{h\ge0}x^{\sum_v h_v}q^{\sum_{uv\in E(G)}(h_u-h_v)^2}.
$$

The Python core uses Python 3.10+ and the standard library. The repository includes exact algorithms, independent enumeration oracles, retained experiments, a research monograph, two focused papers, and a pinned Lean proof project. The [result index](docs/THEOREM_INDEX.md) and [proof-scope documentation](formal/README.md) distinguish mathematical proofs, finite computations and kernel-checked statements.

## Read or download

[Research monograph — PDF](output/pdf/monograph.pdf) · [HTML](docs/monograph.html) · [Editable source](docs/MONOGRAPH.md)

[Paper 1: arithmetic visibility — PDF](output/pdf/visibility_paper.pdf) · [Source](docs/papers/visibility.md) · [Claim register](docs/papers/visibility_claims.md)

[Paper 2: exact observation depth — PDF](output/pdf/locality_paper.pdf) · [Source](docs/papers/locality.md) · [Claim register](docs/papers/locality_claims.md) · [Selection and literature comparison](docs/papers/second_paper_choice.md)

[Complete v0.2.0 download](https://github.com/towre676-cloud/singularity/blob/main/releases/Singularity-v0.2.0-complete.zip) · [Release manifest](results/archive_manifest.json) · [Publication checks](results/publication_release.json)

The archive contains the source, all three PDFs, editable mathematical documents, exact results, tests, proof sources and dependency manifests. Lean and Mathlib build caches are excluded. No document compiler is needed to read the PDFs.

## What is established

**Exact distinctions.** The retained spectral, binary-census and cube–Möbius pairs first differ at volumes 2, 3 and 4. Explicit infinite families agree to arbitrarily late volumes. Their discrepancy coefficients are proved and independently replayed. The connected six-vertex census has 112 classes, all separated by volume three. The later census covers disconnected graphs too: all 1,044 seven-vertex classes separate through volume five; among all 12,346 eight-vertex classes, twenty pairs agree through volume five and all separate at six. These are finite-population results; see the [retained loop-series report](results/loop_series.json).

**A scalable compiler.** Connected-support locality computes a prefix from small connected induced vertex sets with ambient degrees retained. Its graph-size cost is linear at fixed maximum degree and volume budget. Separator and forest engines provide complementary algorithms and independent comparisons. Retained benchmarks state their graph class, cutoff and measured scope. The bounded-height 96-vertex path experiment retains 2,506,262,962,660,245 labeled profiles, with every volume marginal independently checked.

For equal-order $d$-regular graphs of girth at least $g$, all coefficients below $g$ agree, and

$$
[x^g](L_G-L_H)=\bigl(N_g(G)-N_g(H)\bigr)q^{(d-2)g}(1-q^2)^g,
$$

where $N_g$ counts $g$-cycles. This explains the cube–Möbius witness. The loop expansion extends the calculation to the first overlap threshold, with an explicit correction there.

**Sharp reconstruction on a graph class.** Every simple 2-regular graph of known order $n$ is determined by its pinned height series through volume $\lfloor n/2\rfloor$. This worst-case budget is sharp for $n\ge6$.

**A complete enrichment.** Keeping squared height as a separate marker gives $\mathcal P_G(x,u,q)=\sum_hx^{\sum h}u^{\sum h^2}q^{E_G(h)}$, which is complete at every fixed $0<q<1$. Its constructive separating volumes are enormous; this is not an efficient graph-isomorphism algorithm. Completeness of the original fixed-pinning series remains open.

**Interfaces and observation.** Boundary-charge tables compile terminal responses; complete ordered observation charts transport information between experiments. Cycle counts determine the regular-graph series before the first overlap threshold, after which theta, diamond and clique corrections become observable.

**Arithmetic and proof scope.** Explicit remainder bounds and outward-rounded computations control the normalized real Euler-product remainder. Core Lean 4.12.0 checks normalization, nested levels, both decisive coefficient certificates and finite cancellation. The separate [Mathlib analysis project](formal-analysis/README.md) proves the actual real Euler-product factorization and positive normalized boundary limit, including both certified graph pairs at $q=1/2$. Its [source-bound audit](results/formal_analysis_audit.json) checks 79 declarations, alongside 91 in the core project. The newer reconstruction and loop theorems have manuscript proofs and computational checks; their Lean formalization is a separate future task.

## Run and reproduce

```sh
PYTHONPATH=src python -m singularity --help
PYTHONPATH=src python -m singularity compare binary_g binary_h --max-volume 3 --q 1/2
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python scripts/reproduce.py --check
PYTHONPATH=src python scripts/locality_family.py --check
PYTHONPATH=src python scripts/overlap_hierarchy.py --check
PYTHONPATH=src python scripts/loop_series.py --check
python scripts/check_repository.py
python scripts/check_links.py
```

Advanced transfer, locality, moment, terminal and charge-chart engines are available through their Python modules and retained-result scripts. Counts and rank/unrank preserve original labeled assignments. Forest transfer rejects cycles and conductor calculations retain explicit work budgets.

On Windows PowerShell, first set `$env:PYTHONPATH='src'` and omit the `PYTHONPATH=src` prefixes. Optional installation is `python -m pip install -e .`; the command is then `singularity`.

`python scripts/build_documents.py` rebuilds the monograph and both papers with Pandoc and XeLaTeX. `python scripts/package_release.py` creates the complete archive and verifies every manifest hash. [GitHub Actions](https://github.com/towre676-cloud/singularity/actions) runs the exact Python checks, the pinned core Lean build, and the actual Mathlib analysis build.

## Continue the research

The [original 36-push ledger](handoff/PUSH_AUDIT.md), [session log](handoff/SESSION_LOG.md), [current task selector](handoff/START_HERE.md), and [second-paper decision](docs/papers/second_paper_choice.md) record achieved scope and precise open questions. The main research frontiers are efficient reconstruction beyond cycle interiors, completeness or a full-series collision for fixed pinning, and realization of the surviving symmetric-interface ambiguities. Finite prefix agreement alone settles none of those questions.
