# Singularity

**Relational heights and arithmetic visibility.** Singularity studies what a finite relation structure reveals when observations progress from binary cuts to nested integer heights. Exact graph examples connect the first differing height coefficient to a fractional singularity in a primewise Euler-product ratio.

The repository includes a book-length research monograph, a concise companion article, exact Python machinery, reproducible finite experiments and a roadmap for 36 development pushes. Definitions and proofs distinguish the full span-marked hierarchy from its projections. General graph reconstruction and publication priority remain open questions.

## Read the mathematics

[Navigable HTML](docs/monograph.html) · [Editable Markdown](docs/MONOGRAPH.md) · [LaTeX](docs/monograph.tex)

[Article source](docs/papers/visibility.md) · [Result index](docs/THEOREM_INDEX.md) · [Bibliography](docs/references.bib) · [36-push development program](docs/development/PUSHES.md)

The complete source chapters, software and retained results are committed below. The rendered PDF and ZIP download links will be added when those files are published.

For a connected simple graph G, the local population and its arithmetic lift are

$$L_G(x,q)=\sum_{a\in\mathbb N^k}x^{\sum_i a_i}q^{\sum_{ij\in E}(a_i-a_j)^2},\qquad Z_G(s,q)=\prod_pL_G(p^{-s},q).$$

Minimum-zero representatives remove common translations. A span mark retains the binary census as an explicit sector and records nested-boundary compatibility. If two local series first differ at volume r by delta, their ratio has a factor zeta(rs)^delta with a convergent normalized remainder near the positive real point 1/r. The manuscript proves the hypotheses and scope; the code supplies exact finite inputs and coefficients.

## Exact results retained

| Comparison | Shared observations | First different volume | Difference at q=1/2 |
|---|---|---:|---:|
| Seven-vertex spectral pair | Degree multiset and Laplacian spectrum | 2 | 3/32 |
| Seven-vertex binary-census pair | Entire cut-volume census over all 128 binary assignments | 3 | 11025/262144 |
| Cube and eight-vertex Mobius ladder | Cubic, triangle-free, equal local and marked prefixes through volume 3 | 4 | 81/2048 |

An exhaustive connected-graph census through six vertices contains 112 isomorphism classes at order six; all separate by volume three. This is a finite population result, not a general reconstruction theorem. A bounded-height transfer experiment on a 96-vertex path counts 2,506,262,962,660,245 retained labeled profiles; every volume marginal is independently checked by a generating-function identity. The [implementation chapter](docs/IMPLEMENTATION.md) explains the restrictions and measured scope.

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

The package also exposes weighted hard contractions, primitive-profile Mobius inversion, finite Dirichlet coefficients and source-bound coefficient certificates. Counts and rank/unrank preserve original labeled assignments. Forest transfer rejects cycles; conductor calculations have an explicit residue-box budget. See each module's API documentation for its declared domain.

## Reproduce and develop

```sh
make test
make examples
PYTHONPATH=src python scripts/reproduce.py --check
PYTHONPATH=src python scripts/census.py --max-order 6 --max-volume 6
PYTHONPATH=src python scripts/benchmark_transfer.py
```

The 14 source chapters are in `docs/chapters`. `make book` uses Pandoc and XeLaTeX to regenerate the PDF, HTML and editable LaTeX. The distributed documents can be read without those tools. `make release` checks the repository and creates the complete source/document/result archive.

The initial roadmap develops reconstruction, delayed visibility, graph transformations, separator algorithms, arithmetic boundary layers and formal proof coverage. Every push specifies a concrete mathematical or computational outcome. Established cut-lattice, Ising, Gaussian, Euler-transform and graph-isomorphism literature is discussed in the final monograph chapter, with primary references.
