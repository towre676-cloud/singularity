# Singularity

**Exact graph observations, reconstruction and arithmetic visibility.** Singularity studies how much of a graph becomes visible when each vertex receives an integer height and every edge measures the squared difference between its endpoints. Binary heights see cuts. Taller profiles reveal distinctions that degrees, Laplacian spectra and even the complete binary cut census can miss. The first differing coefficient also determines a fractional singularity in an associated primewise Euler-product ratio.

The project now includes connected-support and loop expansions, exact boundary interfaces, a complete moment-marked graph invariant, and a Lean 4 proof package alongside the monograph, companion article and standard-library Python implementation. The stronger moment-marked series reconstructs finite simple graphs in principle; reconstruction from the ordinary height series or a single fixed pinning remains open. The original 36-push ledger records 33 complete pushes, two partial pushes and one blocked push.

## Read the mathematics

[Research monograph, PDF](output/pdf/monograph.pdf) · [HTML download](docs/monograph.html) · [Editable Markdown](docs/MONOGRAPH.md) · [LaTeX](docs/monograph.tex)

[Companion article, PDF](output/pdf/visibility_paper.pdf) · [Article source](docs/papers/visibility.md) · [Result index](docs/THEOREM_INDEX.md) · [Bibliography](docs/references.bib) · [36-push development program](docs/development/PUSHES.md)

[Packaged v0.1.0 snapshot](releases/Singularity-v0.1.0-complete.zip) · [Current source ZIP](https://github.com/towre676-cloud/singularity/archive/refs/heads/main.zip)

The packaged release and handoff are historical snapshots. Use the current source ZIP or clone `main` for subsequent mathematical and formal developments.

For a connected simple graph G, the local population and its arithmetic lift are

$$L_G(x,q)=\sum_{a\in\mathbb N^k}x^{\sum_i a_i}q^{\sum_{ij\in E}(a_i-a_j)^2},\qquad Z_G(s,q)=\prod_pL_G(p^{-s},q).$$

Minimum-zero representatives remove common translations. A span mark retains the binary census as an explicit sector and records nested-boundary compatibility. If two local series first differ at volume r by delta, their ratio has a factor zeta(rs)^delta with a convergent normalized remainder near the positive real point 1/r. The manuscript proves the hypotheses and scope; the code supplies exact finite inputs and coefficients.

## Exact results retained

| Comparison | Shared observations | First different volume | Difference at q=1/2 |
|---|---|---:|---:|
| Seven-vertex spectral pair | Degree multiset and Laplacian spectrum | 2 | 3/32 |
| Seven-vertex binary-census pair | Entire cut-volume census over all 128 binary assignments | 3 | 11025/262144 |
| Cube and eight-vertex Mobius ladder | Cubic, triangle-free, equal local and marked prefixes through volume 3 | 4 | 81/2048 |
| Pendant cycles: C_2l with leaves at distance p versus opposite, every 2 <= p < l (theorem SNG-F36) | Degrees, edge degree types, cut-lattice theta series, all coefficients through volume p | p+1 | 3^p/4^(p+2) |

The connected-graph census through six vertices contains 112 isomorphism classes at order six, all separated by volume three. The later census includes disconnected graphs: all 1,044 seven-vertex graphs separate through volume five; among all 12,346 eight-vertex graphs, twenty pairs agree through volume five and all separate at volume six. These are exact finite-population results, with retained evidence in [the loop-series report](results/loop_series.json), rather than a general reconstruction theorem for the ordinary series.

**Connected supports and the first visible cycle.** The logarithm of the height series decomposes over connected decorated induced subgraphs; a support of size k cannot contribute below volume k (SNG-F55). For equal-order d-regular graphs of girth at least g, every coefficient below volume g agrees, and for the ordinary local series

$$[x^g](L_G-L_H)=\bigl(N_g(G)-N_g(H)\bigr)q^{(d-2)g}(1-q^2)^g.$$

Here N_g counts g-cycles. This explains the cube–Möbius discrepancy structurally (SNG-F56). The loop expansion extends the calculation up to the first possible cycle overlap, with an explicit correction at that boundary (SNG-F60–F61). The compiler computes small-volume observations on sparse graphs without enumerating every height assignment.

**Reconstruction with declared observations.** For 2-regular interiors, the pinned series reconstructs the cycle decomposition at the sharp budget floor(n/2) (SNG-F57). More generally, retaining both total height and squared height gives

$$\mathcal P_G(x,u,q)=\sum_{a\in\mathbb N^{V(G)}}x^{\sum_v a_v}u^{\sum_v a_v^2}q^{E_G(a)}.$$

For every fixed q in (0,1), this full two-marker formal series is a complete graph invariant (SNG-F58). The proof can require enormous separating volumes; it supplies no efficient general isomorphism algorithm. A finite range of squared-height pinnings recovers each bounded-volume moment prefix by interpolation. The proof and precise distinctions between the ordinary, pinned and moment-marked series are in [the inverse-problems chapter](docs/chapters/10_inverse_problems.md).

**Exact interfaces for graph assembly.** Terminal kernels, symmetric contexts, boundary-charge compression and ordered chart transport reuse a block's information across graph gluings (SNG-F47–F54, F59, F62). On the dominating-terminal family, one closure recovers the compressed interface and predicts every other closure. These are stated families and budgets, rather than an unrestricted graph-compression claim.

A bounded-height transfer experiment on a 96-vertex path counts 2,506,262,962,660,245 retained labeled profiles; every volume marginal is independently checked by a generating-function identity. The [implementation chapter](docs/IMPLEMENTATION.md) describes the algorithms and restrictions.

**Formal proof coverage.** The [Lean package](formal/README.md), pinned to Lean 4.12.0 with core libraries only, proves translation normalization and the nested-level energy identities. It also kernel-checks the two seven-vertex coefficient tables through volume four, their lower-volume agreement, first discrepancies and polynomial factorizations. The recorded axiom audit covers 91 theorems and reports only standard Lean axioms, with no project axioms or admitted proofs. The finite power-series cancellation step of the visibility comparison is formalized. Its analytic conclusion remains conditional on an explicit premise structure: real analysis, faithfulness of those premises to the real numbers and the q = 1/2 exponent evaluations are not formalized. The newer reconstruction and loop theorems have manuscript proofs and computational checks, not Lean proofs.

## Run the machinery

Python 3.10 or newer is sufficient for the entire mathematical core; it has no third-party runtime dependencies.

```sh
python -m pip install -e .
singularity compare binary_g binary_h --max-volume 3 --q 1/2
singularity population --example binary_g --volume 3 --span 2 --sample 5
singularity transfer --path 96 --max-height 2 --max-volume 12 --min-zero
singularity euler --example binary_g --max-volume 4
singularity conductor --path 3 --order 3 --index 100000000000000000000000000000000000000000000000000
```

Without installation, prefix commands with `PYTHONPATH=src` and use `python -m singularity`. Windows PowerShell can set `$env:PYTHONPATH='src'` before that invocation.

The Python API also exposes tree-decomposition transfer, connected-support compilation, moment coefficients, terminal kernels and charge-chart transport, alongside weighted hard contractions, primitive-profile Möbius inversion, finite Dirichlet coefficients and source-bound coefficient certificates. The CLI covers the commands shown above; advanced engines are available through their modules and reproducibility scripts. Counts and rank/unrank preserve original labeled assignments. Forest transfer rejects cycles; conductor calculations have an explicit residue-box budget. See each module's API documentation for its declared domain.

## Reproduce and develop

```sh
make test
make examples
PYTHONPATH=src python scripts/reproduce.py --check
PYTHONPATH=src python scripts/census.py --max-order 6 --max-volume 6
PYTHONPATH=src python scripts/benchmark_transfer.py
python scripts/check_repository.py
python scripts/check_links.py
```

The 14 source chapters are in `docs/chapters`. `make book` uses Pandoc and XeLaTeX to regenerate the PDF, HTML and editable LaTeX. The distributed documents can be read without those tools. `make release` checks the repository and creates the complete source/document/result archive.

Replay the newer results with `PYTHONPATH=src python scripts/locality_family.py --check`, `PYTHONPATH=src python scripts/overlap_hierarchy.py --check`, `PYTHONPATH=src python scripts/loop_series.py --check` and `PYTHONPATH=src python scripts/charge_interfaces.py --check`. The full Python suite and these retained-result checks are configured in GitHub Actions. To rebuild the formal package and print its axiom audit, run `python scripts/check_formal.py` with the pinned Lean toolchain available.

The [live development ledger](handoff/push_status.json) distinguishes accepted results from remaining work. P34 is partial because the analytic visibility theorem is conditional; P35 is partial because manuscript release requirements remain; P36 is blocked on P35. General completeness of the ordinary or fixed-pinning series, realization of the remaining terminal-kernel ambiguity candidates, and publication priority remain open. Established cut-lattice, Ising, Gaussian, Euler-transform and graph-isomorphism literature is discussed in the final monograph chapter, with primary references.

## Continue with Claude Code

The [Claude Code handoff](handoff/START_HERE.md) preserves all 36 original pushes, audits existing work against acceptance criteria and supplies a separate task packet for every push. Start with the [copy-paste prompt](handoff/CLAUDE_START_PROMPT.md). `python scripts/handoff.py doctor` checks the working baseline; `python scripts/handoff.py next` selects dependency-ready work.

The [complete handoff ZIP](https://github.com/towre676-cloud/singularity/raw/refs/heads/main/releases/Singularity-Claude-Code-Handoff.zip) includes the full source, documents, exact results, SHA-256 manifest and an offline Git bundle. Read the pinned source commit in its metadata before merging later remote work. Its original recommendation to start with P01–P03 is superseded by the live ledger: those pushes are complete, and terminal-interface and delayed-visibility work is now implemented. Use the current ledger and session log before choosing further work.
