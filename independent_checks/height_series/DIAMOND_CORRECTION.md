# Volume-4 factorisation beyond 8 vertices, and a diamond correction

Exact integer arithmetic only; no floating point anywhere in the
height-series work. Scripts and full data are in this directory:
`singularity_extension.py`, `singularity_extension.json`, and
`singularity_extension.log` (the log of the actual run).

## Headline findings

The triangle-free volume-4 formula survives at 10 and 12 vertices with
zero failures in every test run here, against fixed reference graphs
(57 of 57 agreeing graphs at $n = 10$, 18 of 18 at $n = 12$) and
pairwise (1,770 triangle-free agreeing pairs at $n = 10$ and 190 at
$n = 12$, all exact). The naive version of the statement, "any two
cubic graphs agreeing through volume 3 obey the squares-only formula",
is **false**: it fails for 1,144 of 9,201 agreeing pairs with triangles
at $n = 10$ and 410 of 3,044 at $n = 12$, and explicit counterexample
edge lists are stored in the JSON output. Those failures are perfectly
separated by one extra invariant, the **diamond count** (pairs of
triangles sharing an edge): every failing pair had unequal diamond
counts and every holding pair had equal ones, and the residual of a
failing pair was exactly the diamond difference times $q^2(1-q^2)^5$.
Adding that term gives a corrected two-term candidate formula that
held for **all 14,760 pairs agreeing through volume 3 across
$n = 8, 10$ and $12$, with zero failures**. That corrected formula is a
conjecture fitted from computed residuals and then verified on the
sampled pools; it is not proved, and it is stated only for pairs that
agree through volume 3 — outside that domain it fails often, as the
output records.

A necessary honesty note about novelty: the triangle-free case is
**already proved inside this repository** (Theorem SNG-F56,
`docs/chapters/10_inverse_problems.md`, restated in
`docs/papers/locality.md`): for $d$-regular graphs of the same order,
both of girth at least $g$, the series agree below volume $g$ and
$[x^g](L_H - L_{H'}) = (N_g(H) - N_g(H')) \cdot q^{(d-2)g} (1 - q^2)^g$.
So the $n = 10$ and $n = 12$ triangle-free results are independent
exact *checks* of a proved theorem at new orders, valuable as
verification but not new mathematics. The new content in this round
is (a) the refutation of the naive no-girth version with concrete
counterexamples, and (b) the diamond-corrected candidate, which is not
stated in the repository in this $L$-series, volume-4,
agree-through-3 form — its nearest relative there is a
normalised/log-series girth-three term involving squares, diamonds
and $K_4$'s. Both (a) and (b) are computational evidence, not proofs.

## Definitions and method

The script computes $L_G$ exactly as defined in this repository's
README, by recursive enumeration of all labelled height assignments
of total volume 0–4 with incremental squared-edge energy. Cycle counts
$N_3, N_4, N_5$ are computed by a canonicalised simple-cycle counter
($N_3$ cross-checked against an independent triangle counter on every
graph), diamonds are counted as pairs of triangles sharing an edge,
and every graph's volume totals are asserted equal to the number of
weak compositions, $\binom{n+v-1}{v}$ — for example
$[1, 10, 55, 220, 715]$ at $n = 10$ and $[1, 12, 78, 364, 1365]$ at
$n = 12$ for volumes 0–4; an assertion failure would have stopped the
run, and none occurred. Graphs are sampled as distinct labelled
connected cubic graphs by the configuration model (random pairing of
$3n$ stubs, rejecting loops, multi-edges and disconnected results).
Seeds: 20261024 for the $n = 8$ control, 20261025 for $n = 10$,
20261026 for $n = 12$. Sample sizes: 60 at $n = 8$, 300 at $n = 10$,
150 at $n = 12$.

## Control at n = 8

The generalised code reproduces the earlier 8-vertex results exactly:
cube versus Möbius ladder agree through volume 3 and differ at
volume 4 by $2q^4(1-q^2)^4$, and the seeded random reproduction gives
60 distinct sampled graphs, 11 agreeing through volume 3, the formula
holding for all 11, zero failures. This validates the port before any
new order is trusted.

## n = 10 against the Petersen reference

The reference is the Petersen graph ($N_3 = 0$, $N_4 = 0$, $N_5 = 12$,
girth 5). Of 300 sampled graphs (triangle-count frequencies for
$N_3 = 0, 1, 2, 3, 4$ of 57, 89, 92, 44, 18), exactly 57 agreed with
the Petersen graph through volume 3 — precisely the 57 triangle-free
samples — and for all 57 the volume-4 discrepancy equalled
$(0 - N_4) \cdot q^4(1-q^2)^4$, zero failures. The pentagonal prism and
the Möbius ladder $M_{10}$ (both $N_3 = 0$, $N_4 = 5$) agreed through
volume 3 and differed from Petersen at volume 4 by exactly
$-5q^4(1-q^2)^4$. Pairwise over the whole pool of 303 graphs
(45,753 pairs), two further exact patterns held without exception: a
pair agrees through volume 3 **if and only if** the two triangle
counts are equal, and the volume-3 discrepancy always equals
$(N_3 \text{ difference}) \cdot q^3(1-q^2)^3$ — the $g = 3$ case of
SNG-F56, checked here for every sampled pair.

## Where the naive statement breaks

Among the 10,971 $n = 10$ pairs agreeing through volume 3, the 1,770
pairs with both graphs triangle-free obeyed the squares formula in
every case. The 9,201 pairs with equal **nonzero** triangle counts did
not: the squares-only formula held for 8,057 and **failed for 1,144**.
A stored counterexample (full edge lists in the JSON): graphs
`n10_g1` and `n10_g46`, both with $N_3 = 2$ but $N_4 = 2$ versus 6 and
diamond counts 0 versus 1, have actual volume-4 discrepancy
$\{q^2: -1, q^4: 1, q^6: 6, q^8: -14, q^{10}: 11, q^{12}: -3\}$,
whereas squares alone predict
$\{q^4: -4, q^6: 16, q^8: -24, q^{10}: 16, q^{12}: -4\}$.
The actual discrepancy has a $q^2$ term, which no multiple of
$q^4(1-q^2)^4$ can produce — so the failure is structural, not a wrong
coefficient. At $n = 12$ the same picture held: 3,234 agreeing pairs,
of which 190 triangle-free pairs all satisfied the squares formula,
while 410 of 3,044 equal-nonzero-triangle pairs failed it. At $n = 8$,
all 477 agreeing triangle pairs in the smaller pool happened to
satisfy even the squares-only formula, consistent with diamond counts
coinciding throughout that pool — which is presumably why the
limitation was invisible at 8 vertices.

## The diamond-corrected candidate

For cubic graphs of the same order that agree through volume 3
(equivalently, in every sample here, that have equal triangle counts):

$$[x^4](L_A - L_B) = (N_4(A) - N_4(B)) \cdot q^4(1-q^2)^4 + (N_{\mathrm{dia}}(A) - N_{\mathrm{dia}}(B)) \cdot q^2(1-q^2)^5.$$

Re-run with this test built in, it held for every agreeing pair at
every size: 555 of 555 at $n = 8$, 10,971 of 10,971 at $n = 10$, and
3,234 of 3,234 at $n = 12$ — 14,760 pairs, zero failures, including
all the pairs that refute the squares-only version. Delimiting its
domain matters: applied to pairs that do **not** agree through
volume 3, the same formula failed 34,782 of 45,753 times at $n = 10$
(and similarly at the other sizes), because the volume-4 coefficient
also inherits contributions from the volume-3 discrepancy. So the
candidate is specifically a statement about the first possible
correction layer after agreement through volume 3, not a universal
volume-4 formula.

## Limits — evidence versus proof

The triangle-free formula is a theorem (SNG-F56, proved in this
repository); this work adds exact computational confirmation at
orders 10 and 12, nothing more. The refutation of the naive version
is solid as far as it goes: the counterexamples are explicit labelled
graphs whose series were computed exactly, and anyone can re-run the
script and check them. The diamond-corrected formula is **conjecture
supported by exact computation on sampled labelled pools**, not a
proof and not an exhaustive census: isomorphism-class coverage of the
samples was not tracked, the test reaches only volume 4 and cubic
graphs, and no $K_4$ term could be probed because a $K_4$ subgraph of
a connected cubic graph on more than 4 vertices would have to be a
whole component, so that channel is structurally absent here — in
classes where $K_4$'s can occur, an additional term of the kind the
repository's normalised girth-three formula suggests may be needed. A
proof would presumably follow the repository's own connected-support
expansion in chapter 10, tracking diamond supports at volume 4 the way
SNG-F56 tracks cycle supports at volume $g$; that derivation, and a
reconciliation against the repository's normalised-series formula,
are the natural next steps and are **not** done here. "Zero failures"
always refers to the sampled pools described above, with the stated
seeds and sampling method.

## Files in this directory

`singularity_height_series.py` and `singularity_height_series.json`
are the independent cube-versus-Möbius calculator and its table (see
`HEIGHT_SERIES.md`). `singularity_extension.py` is the portable
generalised script (standard library only, paths relative to the
script; run it with `python3 singularity_extension.py`).
`singularity_extension.json` holds the full results: control block,
per-block reference and named-graph records, triangle/square
distributions, all pairwise statistics, counterexample edge lists
with actual versus predicted discrepancies, and every sampled graph's
edge list and counts. The `.log` files are captured output of actual
verified runs.
