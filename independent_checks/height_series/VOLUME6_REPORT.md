# Singularity volume 6: report

**Task.** Compute the $x^6$ height-series coefficient structure for
cubic graphs and find/prove the correction formula extending the
proved volume-4 ($N_4,N_{\mathrm{dia}},N_{K_4}$) and volume-5
($N_5,N_{K_{2,3}},N_{\Theta(1,2,3)},N_{K_{2,3}+e}$) theorems, by the
volume-5 method. Work is in
`~/workspace/research/expansions/singularity_vol6/`; the cloned
repository was not modified and nothing was committed to GitHub.

## Result

**Theorem (volume 6; PROVED — see `PROOF.md`).** For cubic $A,B$ on
the same number of vertices agreeing through volume 5 (equivalently
$I_5(A)=I_5(B)$), with $\kappa=q(1-q^2)$, $f=q^{-2}-1$:

$\Delta[x^6]L=\kappa^6[\Delta N_{C_6}
+f(\Delta N_{\Theta(1,2,4)}+\Delta N_{\Theta(2,2,3)}
+\Delta N_{\Theta(1,3,3)}+\Delta N_{\mathrm{barbell}})
+f^2(\Delta N_{\mathrm{prism}-\triangle}
+\Delta N_{\mathrm{prism}-\mathrm{spoke}}
+\Delta N_{\mathrm{closed\ diamond}}
+\Delta N_{K_{3,3}-e})
+f^3(\Delta N_{K_{3,3}}+\Delta N_{\mathrm{prism}})]$.

At girth $\ge5$ this collapses to $\kappa^6\Delta N_{C_6}$ alone; at
girth $\ge4$ to
$\kappa^6[\Delta N_{C_6}+f(\Delta N_{\Theta(2,2,3)}+\Delta N_{\Theta(1,3,3)})
+f^2\Delta N_{K_{3,3}-e}+f^3\Delta N_{K_{3,3}}]$.

## PROVED

The proof (`PROOF.md`) follows the volume-5 route and is complete:
Bell bridge at volume 6; SNG-F55 cumulant split
$\ell_6=S_{\le5}^{(6)}+T_6$; Lemma A ($S_{\le5}^{(6)}$ is a function of
$I_5$) via subgraph-matrix invertibility at sizes $\le5$ (ranks
$2,4,11,34$), the $\beta$-decomposition (supports of sizes
$1,2,6,21$), and determination identities for every $\beta$-support
pattern; the raw size-6 identity
$T_6=a^6\sum_Y N_Yf^{e(Y)}$ via the multilinear identity
$[x^6]\Phi_\tau=a^6P(\tau)$ and the alpha identity, both verified for
all 112 connected 6-types; vacuity of the 83 connected 6-types with a
vertex of degree $\ge4$; hand-proved double-counting determination
identities (rigid-core method) for the 18 non-formula non-vacuous
patterns; assembly. The one genuinely new phenomenon beyond volume 5:
$K_{3,3}-e$ is **not** determined by $I_5$ (weld pairs below move it
by $-6$ and $-7$ on agreeing pairs), so it joins the formula as an
eleventh invariant rather than being absorbed — the exact analogue of
the $K_4$ term at volume 4. A second new subtlety: six determination
identities acquire corrections in $N_{K_4}$ (invisible on connected
graphs, necessary for arbitrary cubic graphs); since $N_{K_4}\in I_5$,
determination is unaffected.

## COMPUTED

All arithmetic exact (rationals). Library and identities
(`vol6_lib.py`, `vol6_libtest.py`, ~36 s): type counts
$(1,2,4,11,34,156)$ for $k=1..6$, connected $(1,1,2,6,21,112)$; only
29 of the 112 connected 6-types are non-vacuous in cubic graphs;
multilinear and alpha identities verified for every connected type on
$\le6$ vertices; $\ell_5,\ell_6$ SNG-F55 identities verified on the
cube, Möbius ladder $M_8$, Petersen, $K_{3,3}$, prism.

Pools (`vol6_main.py`, 5,518 graphs): stored/regenerated $n=8$ (62),
stored $n=10$ (303) and $n=12$ (153), fresh random cubic samples
$n=14$ (3,000, seed 20261027) and $n=16$ (2,000, seed 20261028).
Per graph: height totals $\binom{n+r-1}{r}$; $\ell_6=S_{\le5}^{(6)}+T_6$;
the raw identity for $T_6$; agreement with stored counts at
$n=10,12$ — all pass. Agreeing-through-volume-5 pairs: **58,802**
($n=8$: 519; $n=10$: 3,819; $n=12$: 246; $n=14$: 39,722; $n=16$:
14,496), of which 35,438 have $\Delta L_6\ne0$. The raw all-pattern
formula and the reduced formula over the varying patterns both have
**zero failures on all 58,802 pairs**.

Variation census on agreeing pairs: exactly 8 of the 29 non-vacuous
patterns ever vary ($C_6$; the three $\Theta$'s; barbell; the three
$e=8$ prism-derived patterns); their difference vectors have rank 8
(652 distinct vectors). The $\beta$-identity
$S_{\le5}^{(6)}=\sum_Y\beta_Y N_Y$ holds on all 5,518 graphs, and
$S_{\le5}^{(6)}$ and every size-$\le5$ pattern count have zero
collisions on $(n,I_5)$-classes. All pattern-determination fits were
verified against the full pool; the three apparent fit failures at
sizes $\le5$ are the pure-$n$ polynomials $\binom n4$, $\binom n5$,
$\frac{3n}2\binom{n-2}3$ (verified directly, zero failures).

Targeted searches. (i) The $e=9$ terms never occur in connected
pools. A meet-in-the-middle component-balance search
(`vol6_search4.py`, after two cruder attempts failed and a third was
swamped by isomorphism duplicates in the stored pool) produced 4
pairs $\mathrm{prism}\sqcup H$ vs $H_1\sqcup H_2$ ($n=24$) with
$\Delta N_{\mathrm{prism}}=-1$, $\Delta N_{K_{3,3}}=\Delta N_{K_{3,3}-e}=0$:
the prism $f^3$ term is necessary and correct there. (ii) No random
or component-balance pair moved $N_{K_{3,3}-e}$ (it is $>0$ in only 45
of 5,518 pool graphs, max 1), and no formula for it over $I_5$,
$I_5$-products, or $I_5$ plus the 8 pool invariants fits
(`vol6_m2012.py`) — correctly so, because it is a true invariant:
**weld rings** (`vol6_weld.py`) — rings of $K_{3,3}-e$ units joined
by bridges, whose $I_5$ is exactly additive since every $I_5$ pattern
is 2-connected and inter-unit cycles have length $\ge8$ — give 4
agreeing pairs with $\Delta N_{K_{3,3}}=-1$ and
$\Delta N_{K_{3,3}-e}\in\{-6,-7\}$, on which the 11-term formula
holds exactly and every proper sub-formula fails. Two distinct
$\Delta N_{K_{3,3}-e}$ values plus the linear independence of
$\kappa^6f^2$ and $\kappa^6f^3$ separate the two coefficients. (iii) A
hill-climbing surgery attack on the same target (exact local
$\Delta I_5$ under edge switches; `vol6_surgery*.py`) stalled at
distance $D=2$–$3$ and was abandoned once welds succeeded.

Per-term test status (a term is "tested" where its $\Delta N\ne0$ on
an agreeing pair and the formula is checked there; "isolated" =
pairs where it is the only varying new invariant):

| term | pairs varying | isolated | status |
|---|---|---|---|
| $N_{C_6}$ ($f^0$) | 32,985 | 8,745 | tested |
| $N_{\Theta(1,2,4)}$ ($f$) | 16,903 | 453 | tested |
| $N_{\Theta(2,2,3)}$ ($f$) | 16,654 | 1,013 | tested |
| $N_{\Theta(1,3,3)}$ ($f$) | 10,016 (+4 weld) | 247 | tested |
| $N_{\mathrm{barbell}}$ ($f$) | 4,942 | 142 | tested |
| $N_{\mathrm{prism}-\triangle}$ ($f^2$) | 104 | 0 | tested jointly |
| $N_{\mathrm{prism}-\mathrm{spoke}}$ ($f^2$) | 54 | 0 | tested jointly |
| $N_{\mathrm{closed\ diamond}}$ ($f^2$) | 8 | 0 | tested jointly (thinnest) |
| $N_{K_{3,3}-e}$ ($f^2$) | 4 (weld) | 0 | tested jointly with $N_{K_{3,3}}$ |
| $N_{K_{3,3}}$ ($f^3$) | 4 (weld) | 0 | tested jointly with $N_{K_{3,3}-e}$ |
| $N_{\mathrm{prism}}$ ($f^3$) | 4 (component) | 4 (in the $f^3/f^2$ sense) | tested |

For every term, dropping it breaks the formula on **every** pair
where it varies (drop-one test). The three $e=8$ pool terms never
vary alone; their coefficients are nonetheless pinned jointly by the
rank-8 difference span and the drop-one test. The closed-diamond
term, varying on only 8 pool pairs, is the thinnest-tested term.

## CONJECTURED / OPEN

Nothing in the formula is conjectural. Remaining limitations, stated
plainly: the $e=8$ terms' coefficients are verified jointly rather
than in isolation (no agreeing pair was found where one of them
varies alone); the finite machine-discharged steps of the proof
($\beta$-tables, type identities) are exact but voluminous, in the
same style as the accepted volume-5 package; and the determination
identities' hand derivations rely on the rigid-core degeneracy
enumeration, independently backed by exact verification on 5,525
graphs including $K_4$-, $K_{3,3}$- and prism-component graphs.

## Files

`vol6_lib.py` (exact library), `vol6_libtest.py/.log`,
`vol6_types6.py/.json/.log` (29-pattern catalogue),
`vol6_main.py`, `vol6_results.json`, `vol6_run.log`,
`vol6_relations.py/.json/.log` ($\beta$-decomposition, collisions,
fits), `vol6_final_check.py/.json/.log` (reduced formula, per-term
status), `vol6_m2012.py/.json/.log`, `vol6_k4fix.py/.json/.log`
($N_{K_4}$ corrections), `vol6_search*.py/.json/.log` (component
balance), `vol6_gen2.py`/`vol6_gen3.py` + `vol6_pools2.json`/
`vol6_pools3.json` (fresh $n=18,20,24,26$ pools),
`vol6_weld.py/.json/.log` (weld pairs), `vol6_identify.py/.log`,
`vol6_formula_tables.txt`, `PROOF.md`, `REPORT.md`. The abandoned
surgery scripts and logs (`vol6_surgery*.py`, `vsu*.out`) are kept
for the record.
