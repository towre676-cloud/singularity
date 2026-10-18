# Proposed extension units P37–P72

**Status:** proposals recorded on 2026-10-18 from the project owner's plan. They extend, and do not replace, the original program in [PUSHES.md](PUSHES.md). P01–P36 keep their identifiers, dependencies and acceptance gates, and `handoff/push_status.json` continues to track exactly those 36. An extension unit is accepted only when its stated result is proved or implemented with an independent check. The column "evidence so far" records work that already bears on a unit; such evidence is not acceptance.

The six waves have three centers: certified arithmetic evaluation, exactly controlled visibility depth, and the information cost of reusable relational interfaces.

## Wave A: exact-depth families (P37–P42)

| ID | Proposed result | Evidence so far |
|---|---|---|
| P37 | Connected decorated-support lemma for the pendant-cycle family | Subsumed by the placement lemma in the proof of SNG-F36 |
| P38 | Disconnected-support reconstruction completing the deck comparison | Proof of SNG-F36 counts all components, including isolated leaves; decks checked computationally for six pairs |
| P39 | Binary transfer factorization | SNG-F36 closed form \(q^2(1-q)^2(1-q^2)^pz^{p+1}(1-z)^2U_{\ell-p}^2\), checked against all subsets for \(\ell\le7\) |
| P40 | Exact-depth family theorem | SNG-F36 (chapter 10); `results/pendant_family.json`. Recorded under original P32 as `implemented_pending_acceptance` |
| P41 | Matched-invariant delay bounds | Depth \((n-2)/2\) with equal degrees, edge degree types and isometric cut lattices; spectra differ |
| P42 | Optimal visibility parameters | \(q_p^*=2/(1+\sqrt{4p+9})\), stationary equation checked exactly in `tests/test_families.py`; the asymptotic \(1/(ep)\) is stated in chapter 10 |

## Wave B: boundary responses (P43–P48)

| ID | Proposed result | Evidence so far |
|---|---|---|
| P43 | Ordered terminal kernels \(K_G^B(\mathbf b;x,q)\) | `terminals.py` (kernels on a checked decomposition, enumeration oracle) |
| P44 | General gluing theorem with correct ownership and contraction | SNG-F41 gluing formula for edge-disjoint blocks with any number of terminals; contraction not yet covered |
| P45 | Whitney-twist discrepancy as an antisymmetric pairing | SNG-F41 identity \(L-L_{\mathrm{tw}}=2\sum x^{\|b\|}A_1A_2\) |
| P46 | Identical-block positivity (sum of squares with equality conditions) | SNG-F42: exact first visible volume \(\min_b(\|b\|+2v_b)\), sum-of-squares leading coefficient, positivity on the unit square; SNG-F36 (even \(p\)) is a twist of identical path blocks |
| P47 | Marked boundary composition with global minimum-zero and span | SNG-F43 via box kernels; `marked_glue`, tested against direct marked enumeration |
| P48 | Response-preserving transformations | SNG-F45: swap-symmetric rooted decks through size m keep twists invisible below volume 2m+3; sharp on all connected blocks with at most six vertices; exhaustive search found no symmetric kernel without a swapping automorphism up to six vertices |

## Wave C: contexts and interfaces (P49–P54)

| ID | Proposed result | Evidence so far |
|---|---|---|
| P49 | Future-context equivalence for a specified attachment grammar | SNG-F44: for all edge-disjoint contexts, equivalence is equality of kernels, and star contexts suffice |
| P50 | Connection-matrix formulation and realizable response spaces | SNG-F41 bilinear gluing; SNG-F44 tensor Vandermonde |
| P51 | Unrestricted linear-interface lower bound under pinned probes | \(\binom{R+k}{k}\) star probes with \(\|r\|\le R\) suffice (lower-set unisolvence) and are optimal for determining the span of realizable kernels; `recover_kernel_from_simplex_probes` |
| P52 | Volume-limited interface rank | SNG-F48: exact probe-map ranks under budget R for swap-symmetric contexts (full with a terminal edge for R ≤ 9; without it, defect equal to the proved top-degree lower bound for R ≤ 9); `results/symmetric_contexts.json` |
| P53 | Constructive restricted-context quotients | SNG-F47 (symmetric contexts factor through K⁺) and SNG-F48(b) (2M leaf-and-edge probes recover K⁺ through volume R ≤ 24); `recover_symmetrized_kernel`; no nontrivial K⁺ class among 12,753 blocks on ≤ 6 vertices at volume 4 |
| P54 | A compression theorem with proved savings, including arithmetic cost | SNG-F49: exact observable quotient \(V_R/N_R\) of simple swap-symmetric contexts with explicit coordinates and a spanning probe family (no terminal edge: R ≤ 25; with it: R ≤ 91), the R = 25 blind direction, and its non-realizability; SNG-F50 weighted restoration at every R; compile-once benchmark (kernel 4.6 s, 7.6 ms per query against 1.33 s direct, break-even 3.5 queries). SNG-F51: edge-free symmetric contexts recover K⁺ through R from volume R + m_R − 1 by finite differences in the leaf/shared-neighbour split (no budget ceiling); SNG-F52: interior slices are q^{Q0} times polynomials of bidegree ≤ j in (q^{-2s}, q^{-2t}), which removes the R = 26 candidate (separation of actual blocks through R = 26 with the edge, R = 8 without; R = 37 and R = 10 for equal terminal degrees). Open: a family with growing proved compression |

## Wave D: engines (P55–P60)

| ID | Proposed result | Evidence so far |
|---|---|---|
| P55 | Compiled decomposition plans | `certified.py` reuses one decomposition per graph across all primes |
| P56 | Multiple arithmetic backends on one checked plan | Exact histograms (`decomposition.py`) and outward-rounded scalars (`certified.py`) share the ownership rule |
| P57 | Incremental height/span evaluation | — |
| P58 | Chamber sensitivity calculus | SNG-F29 gap form |
| P59 | Incremental chamber engine | — |
| P60 | Observation-cost benchmark | — |

## Wave E: analysis (P61–P66)

| ID | Proposed result | Evidence so far |
|---|---|---|
| P61 | Sharp volume–energy coercivity via grounded Green functions | SNG-F39 uses the cruder \(h^2\le DE\) |
| P62 | Entire normalized local factors | SNG-F39 (chapter 7), with an explicit tail valid for complex \(t\) |
| P63 | Larger certified complex domains | SNG-F35 disc; SNG-F39 supplies the tool for improving the small-prime step |
| P64 | Accelerated arithmetic tails | — |
| P65 | Certified local zero analysis | — |
| P66 | Uniform parameter regimes near the endpoints | — |

## Wave F: arithmetic and probes (P67–P72)

| ID | Proposed result | Evidence so far |
|---|---|---|
| P67 | Prime-power conductor theory | SNG-F30 covers odd primes only |
| P68 | Characteristic-two classification | — |
| P69 | Finite-conductor information budgets | SNG-F28 remote formula |
| P70 | Weighted reciprocity in a new category, or a sharper impossibility theorem | SNG-F34 obstruction in the rational-function category |
| P71 | First nonbinary energy layers through nested minimum cuts | — |
| P72 | Optimal probe selection | P42 parameter optimizer |

## Ordering

The owner's suggested order is: P27, which SNG-F38 now addresses; P07–P08 in a prepared proof-assistant environment, with finite preparation for P14; the pendant-cycle theorem, now SNG-F36 and SNG-F37; then terminal kernels and the Whitney-twist identity.
