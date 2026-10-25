# Independent height-series calculator: cube versus Möbius ladder

## What was computed

An independent, exact height-series calculator for this repository's
series $L_G(x, q) = \sum_h x^{\sum_v h_v} q^{\sum_{uv \in E(G)} (h_u - h_v)^2}$,
applied to the cube $Q_3$ and to the Möbius ladder $M_8$, for total
volumes 0 through 8. Counts are exact integers obtained by enumeration
of all labelled height assignments, not by sampling or floating
arithmetic. The script is `singularity_height_series.py`; the full
table is `singularity_height_series.json`.

The cube has 8 vertices, 12 edges, is bipartite, and has 6 squares by
the script's simple-cycle counter. The Möbius ladder $M_8$ (cycle
edges $(i, i+1 \bmod 8)$ plus diameter edges $(i, i+4 \bmod 8)$ for
$i = 0..3$) has 8 vertices, 12 edges, is non-bipartite, and has 4
squares by the same counter.

## Results

The totals agree at every volume, as they must: the number of
assignments of total volume $n$ over 8 vertices is $\binom{n+7}{7}$,
giving 1, 8, 36, 120, 330, 792, 1716, 3432, 6435 for $n = 0..8$.

The series agree through volume 3 and first differ at volume 4,
exactly as the repository states. At volume 4 the discrepancy
polynomial (cube minus Möbius) is
$2q^4 - 8q^6 + 12q^8 - 8q^{10} + 2q^{12} = 2q^4(1-q^2)^4$,
and the leading factor 2 is exactly the difference in square counts,
$6 - 4$.

## Status of this result, stated plainly

This volume-4 instance is a computed, independent check of a result
the repository itself proves in general: Theorem SNG-F56
("the first cycle a budget sees", `docs/chapters/10_inverse_problems.md`)
gives, for $d$-regular graphs of the same order and girth at least $g$,
the first discrepancy at volume $g$ as
$(N_g(H) - N_g(H')) \cdot q^{(d-2)g} (1-q^2)^g$.
So this calculator is verification at a specific instance, not new
mathematics and not a proof of that claim for all graphs. It is also
not a proof of general reconstruction: completeness of the original
scalar height series remains explicitly open in the repository.

## Follow-up in this directory

`DIAMOND_CORRECTION.md` and `singularity_extension.py` test what
happens beyond this triangle-free instance, at 8, 10 and 12 vertices.
The short version: the squares-only formula fails when triangles are
present, and a diamond-count correction term fits every agreeing pair
tested. That corrected formula is a conjecture, not a theorem.

## Branch

These files are committed on the branch
`muse/height-series-diamond-correction` in towre676-cloud/singularity,
as new files under `independent_checks/height_series/`, for review by
pull request rather than by a direct push to main.
