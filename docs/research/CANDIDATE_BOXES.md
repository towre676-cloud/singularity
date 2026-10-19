# Candidate-specific uncertainty boxes for finite experiment panels (NX01)

This note covers track NX01 of the NX36 expansion. The existing thermal pilot ([THERMAL_DIAGNOSTICS.md](THERMAL_DIAGNOSTICS.md)) computes an uncertainty radius for every experiment and candidate. It then deliberately replaces those radii by one common envelope per experiment before calling the panel optimizer ([PANELS.md](PANELS.md)). The question here is whether keeping the individual radii changes the cheapest guaranteed diagnosis. It adds no new physical calibration, fault population, correlated-error model or global robustness claim.

Short answer: on the unchanged 112-protocol, six-candidate 12 by 12 plate pool, the cheapest guaranteed panel still costs 20 units, and the per-candidate radii do not change a single coverage decision under the primary contract. On a declared 12-protocol sub-pool of the 4 by 4 plate, the common envelope cannot identify the candidates at any cost, but the per-candidate boxes can, at cost 19. Both statements are exact finite computations, checked by independent oracles.

Implementation: [`candidate_boxes.py`](../../src/singularity/candidate_boxes.py) (production), [`candidate_box_oracles.py`](../../src/singularity/candidate_box_oracles.py) (independent oracles), [`test_candidate_boxes.py`](../../tests/test_candidate_boxes.py), receipt [`candidate_box_thermal.py`](../../scripts/candidate_box_thermal.py) with retained result [`candidate_box_thermal.json`](../../results/candidate_box_thermal.json).

## 1. Objects and contract

A pool has experiments \(e=1,\dots,E\) with exact nonnegative rational costs \(\kappa_e\), and original candidates \(c=1,\dots,K\), \(K\ge2\), with distinct identifiers. Each candidate has a target label \(T(c)\); by default every candidate is its own target. For each experiment and candidate there is an exact central reading \(r_{ec}\) and a nonnegative rational radius \(\rho_{ec}\). The radius matrix is indexed experiment first, candidate second. Its transpose is a different contract, even when \(E=K\) makes the shapes agree.

**Uncertainty contract.** Running experiment \(e\) when the truth is \(c\) yields one reading in the closed interval

\[
I_{ec}=[\,r_{ec}-\rho_{ec},\;r_{ec}+\rho_{ec}\,].
\]

Experiments are independently reset, so the readings of a panel \(P\) range over the product box \(Y_c(P)=\prod_{e\in P}I_{ec}\). The contract asserts that every reading actually produced lies in this box. For the *necessity* half of Theorem 3, every point of the box must also be a possible reading. That holds for the thermal pilot (Section 6) but not for every radius that is merely an upper bound.

**Required pairs.** \(R=\{\{a,b\}: a<b,\ T(a)\ne T(b)\}\). Pairs with a shared target need not be separated. Their candidates are still kept as distinct original hypotheses, with distinct identifiers.

**Plain-language summary.** Every candidate has its own "error bar" in every experiment. A set of experiments is good when, whatever the true candidate and whatever the errors within their bars, the readings rule out every candidate with a different target.

## 2. Geometry

**Lemma 1 (closed intervals).** For \(\rho_a,\rho_b\ge0\), the intervals \([r_a-\rho_a,r_a+\rho_a]\) and \([r_b-\rho_b,r_b+\rho_b]\) are disjoint if and only if \(|r_a-r_b|>\rho_a+\rho_b\).

*Proof.* Without loss of generality \(r_a\le r_b\). Two closed intervals on the line are disjoint exactly when the upper end of the left-hand one is strictly below the lower end of the right-hand one. Their order is fixed by their centers when they are disjoint: if \(r_a\le r_b\) and the intervals are disjoint, then \(I_a\) lies to the left. So disjointness means \(r_a+\rho_a<r_b-\rho_b\), that is \(r_b-r_a>\rho_a+\rho_b\). Conversely, if \(r_b-r_a\le\rho_a+\rho_b\), the point \(\max(r_a-\rho_a,r_b-\rho_b)\) is at most \(\min(r_a+\rho_a,r_b+\rho_b)\), so the intersection is nonempty. \(\square\)

Write the raw margin \(\Delta_{eab}=|r_{ea}-r_{eb}|-\rho_{ea}-\rho_{eb}\). Experiment \(e\) separates \(\{a,b\}\) iff \(\Delta_{eab}>0\). The cases this rules on are exactly the ones tested:

* *Touching endpoints* (\(\Delta=0\)). The shared endpoint is a possible reading under both candidates, so this is not separation.
* *Zero radii.* \(\rho=0\) is a degenerate closed interval. Two exact readings separate iff they differ. A zero radius against a positive one separates iff the exact point lies strictly outside the other interval. The common backend requires strictly positive noisy margins; this module does not.
* *Identical centers* (\(r_{ea}=r_{eb}\)). Then \(\Delta\le0\) whatever the radii, so the pair is never separated by \(e\). The witness reading is the common center.

**Lemma 2 (boxes).** \(Y_a(P)\cap Y_b(P)=\varnothing\) iff some \(e\in P\) has \(\Delta_{eab}>0\).

*Proof.* A product of sets is empty-intersecting with another product exactly when some coordinate pair is disjoint. If every coordinate pair meets, choosing one common point in each coordinate gives a common point of the boxes. Apply Lemma 1 coordinatewise. \(\square\)

For the empty panel the box is the one-point product, so no pair is separated. Hence the empty panel is feasible exactly when \(R=\varnothing\).

## 3. Decoder and identification

The decoder for panel \(P\) and observation vector \(y\in\mathbb Q^P\) returns

\[
D_P(y)=\{c:\ |y_e-r_{ec}|\le\rho_{ec}\ \text{for all }e\in P\}=\{c: y\in Y_c(P)\}.
\]

Its target output is \(T(D_P(y))\).

**Theorem 3 (cover iff guaranteed target identification).** Suppose every point of every box is a possible observation. Then the following are equivalent:

1. every required pair is separated by some member of \(P\);
2. for every candidate \(c\) and every possible observation \(y\in Y_c(P)\), \(T(D_P(y))=\{T(c)\}\).

*Proof.* (1)⇒(2). The truth \(c\) is always in \(D_P(y)\), since \(y\in Y_c(P)\). If \(d\in D_P(y)\) with \(T(d)\ne T(c)\), then \(y\in Y_c(P)\cap Y_d(P)\). By Lemma 2 this contradicts (1).

(2)⇒(1). Suppose \(\{a,b\}\in R\) is unseparated. In each coordinate, the intersection \(I_{ea}\cap I_{eb}=[\max(\text{lower ends}),\min(\text{upper ends})]\) is nonempty by Lemma 1. Let \(y_e\) be its midpoint. Then \(y\in Y_a(P)\), so it is possible under truth \(a\), and \(D_P(y)\supseteq\{a,b\}\) has two targets. \(\square\)

`candidate_box_ambiguity` returns exactly this witness \((a,b,y)\) for the first unseparated required pair. The direction (1)⇒(2) needs only the *enclosure* half of the contract. If radii are only upper bounds, a covering panel still certifies identification, but an ambiguity witness might not be physically attainable. Sharper radii without a proof change the problem; they are not a refinement.

An empty decoder output, which is possible when an observation lies outside every box, signals that the model contract failed. It does not identify an unmodelled fault.

## 4. Comparison with the common envelope

Let \(\varepsilon_e=\max_c\rho_{ec}\) (`common_envelope`).

**Proposition 4 (monotonicity).** If \(|r_{ea}-r_{eb}|>2\varepsilon_e\) then \(\Delta_{eab}>0\). Hence every common-envelope covering panel is a heterogeneous covering panel, and the heterogeneous optimum costs at most the common-envelope optimum. Both comparisons hold for the same readings, costs, population, targets and contract.

*Proof.* \(\rho_{ea}+\rho_{eb}\le2\varepsilon_e\). \(\square\)

**Corollary 5 (where gains can occur).** If \(\rho_{ea}=\rho_{eb}=\varepsilon_e\), then experiment \(e\) has the same decision on \(\{a,b\}\) under both contracts. Gains can occur only on pairs containing a candidate whose radius is below the row maximum.

On equal common radii, the heterogeneous masks coincide with `panels.coverage_masks`, which is tested whenever the envelope is positive. The tests also compare minimum costs with `panels.minimum_cost_panel` on random common-radius pools.

## 5. Exact optimization

With \(M_e=\{p\in R: e\text{ separates }p\}\), a panel covers iff \(\bigcup_{e\in P}M_e=R\) (Lemma 2). Minimum-cost selection is therefore weighted set cover on required pairs. This problem is NP-hard in general.

**Production solver** (`minimum_candidate_box_panel`). This is a private branch-and-bound kernel over validated masks; the masks are always produced from readings and radii inside the module. It follows the design proved in PANELS.md:

* *Dominance reduction.* Experiment \(f\) dominates \(e\) when \(M_f\supseteq M_e\) and \(\kappa_f\le\kappa_e\), with strict improvement or an index tie-break. Removing empty and dominated experiments keeps an optimum, because replacing a dominated member by its dominator never increases cost or loses coverage. The tie-break makes the relation a strict partial order, so a kept dominator exists.
* *Branching.* Pick an uncovered pair \(p\) with fewest admissible coverers \(e_1,\dots,e_m\), ordered by cost. Branch \(i\) includes \(e_i\) and excludes \(e_1,\dots,e_{i-1}\). Every cover contains some coverer of \(p\), and the branch indexed by its first coverer in this order is unique, so the branches partition the covers.
* *Bounds.* Pairs are taken greedily so that no admissible experiment covers two of them. Summing their cheapest admissible coverers gives the packing bound, a valid lower bound because those coverers are distinct experiments. Without packing, the bound is the maximum cheapest coverer.
* *Termination with zero costs.* Every branch removes at least one experiment from the admissible set, so the tree is finite whatever the costs. A pool of many zero-cost experiments separating nothing is pruned by the reduction and never searched as repeated words.
* *Budget.* `max_nodes=10**6` by default. Exceeding it returns `inconclusive` with the greedy-or-better incumbent as an upper bound and the root packing bound as a proved lower bound. An exhausted budget never produces `infeasible`. `infeasible` is returned only when some required pair has no separating experiment in the whole pool, and every such pair is listed.

**Independent oracles** (`candidate_box_oracles`). This module never imports the production module. It recomputes separation from interval endpoints, \(\max(\text{lower})\le\min(\text{upper})\), instead of the production margin formula:

* `exhaustive_box_panel` scans every subset (bounded by `max_subsets`, default \(2^{16}\)) and tests product-box intersection directly.
* `cost_bounded_box_panel` scans every subset of total cost at most a declared bound. If none separates, no panel of cost at most the bound exists. With positive costs this is affordable on large pools when the bound is small.
* `cover_state_dijkstra` is Dijkstra's algorithm on reached sets of separated pairs, with one edge per experiment. Repeating an experiment never enlarges a covered set, so with nonnegative costs a cheapest path uses distinct experiments and equals the cheapest cover. For \(K=6\) there are at most \(2^{15}\) states.

The tests compare all three oracles with the solver, under all four packing and reduction settings, on 300 seeded tiny rational pools. These pools have up to 7 experiments and up to 4 candidates, with mixed zero and positive radii, half-integer readings, zero costs and occasional shared targets. Dedicated tests cover dominated experiments, zero-cost combinations, budget exhaustion and the common-backend comparison. A greedy result is never reported as optimal: optimality is claimed only from completed search, and that search is checked by the oracles.

## 6. Thermal application

**Unchanged pool.** `protocol_pool` compiles the 12 by 12 source-pinned plate with its six candidates: nominal, conductance_half, heater_half, loss_double, and the two blocked bonds. The protocol pool is the original 112-member pool (horizons 1, 2, 3, 4, 6, 8, 12, 20; four sensors). The primary contract is initial radius \(\rho_0=1/100\), sensor noise \(\nu=1/100\), process radius 0 and reduction error 0. `from_diagnostic_pool` reuses `DiagnosticPool.error_bounds` as the radius matrix without recomputing it. The receipt then checks the compilation independently:

* all 672 central readings against the separately written neighbor-flux stencil oracle of `scripts/thermal_diagnostics.py`, which reads no compiled matrix;
* all 672 radii against the closed form \(\rho_{ec}=\nu+\rho_0(1-\lambda_c)^{T_e}\), where \(\lambda_c=1/50\) for loss_double and \(1/100\) otherwise;
* the five retained rows of `results/thermal_diagnostics.json`, covering readings, costs and common radius \(\varepsilon_e\), without regenerating that older receipt;
* the common-envelope optimum from the existing backend: cost 20, protocol index 78 (input 2 for eight steps, left-central sensor), as retained.

**Why the closed form holds, and why it is attained.** For every candidate, \(A_c\) has nonnegative entries and row sums \(1-\lambda_c\); blocked bonds move conductance onto the diagonal. Thus \(|A_c|\mathbf1=(1-\lambda_c)\mathbf1\), and the propagated bound is \(b_T=\rho_0(1-\lambda_c)^T\mathbf1\). Every sensor row is nonnegative with sum one, so \(|C_j|b_T=\rho_0(1-\lambda_c)^T\). The linear image of the initial box \([-\rho_0,\rho_0]^{144}\) under \(C_jA_c^T\) is the whole interval \([-\rho_0(1-\lambda_c)^T,\rho_0(1-\lambda_c)^T]\), with endpoints at the same-sign corners. Adding independent sensor error in \([-\nu,\nu]\) fills \(I_{ec}\) exactly. So the thermal radii are attained, and the necessity half of Theorem 3 applies. For signed sparse models, \(|A|\)-propagation is safe but may be conservative. The test suite keeps the existing signed example, where the radius \(1/20\) is attained.

**Result (exact finite computation).** The heterogeneous optimum is panel \(\{78\}\) with cost 20, the same as the common envelope. The checks agree:

* the solver finishes with status `optimal`, lower bound 20, after 18 nodes;
* the cover-state Dijkstra oracle gives 20 after 23 settled states;
* the cost-bounded exhaustive scan, which enumerates all 3223 subsets of cost at most 20, finds no cheaper separating subset.

Under the primary contract, the heterogeneous and common-envelope masks have exactly the same 809 coverage bits. By Corollary 5, gains could only involve loss_double, the only candidate with a smaller radius, and none occurs here. Every corner of every candidate's box decodes to the true candidate under panel \(\{78\}\). The zero-noise optimum \(\{22\}\) of the old receipt is not robust here. Its witness pair is nominal versus loss_double, with common reading \(57120893/200000000\), and both are retained.

The receipt also repeats the old receipt's grid: initial radius \(0,10^{-4},10^{-3},10^{-2}\) times sensor noise \(0,10^{-3},10^{-2}\). Each grid contract uses the exact additive form \(\rho=|C|b+\nu\) on a pool compiled with zero sensor noise. The grid matches the direct compilation at the primary contract. In all 12 contracts, the heterogeneous optimum equals the common-envelope optimum, and each is confirmed by Dijkstra. Two contracts gain mask bits without changing the optimum: 915 versus 906 bits at \((10^{-2},0)\), and 898 versus 895 at \((10^{-2},10^{-3})\).

**Small-plate contrast (exact finite example).** Take the 4 by 4 plate, the 12 protocols `default_protocols((1,2,3,4,6,8))[1::5][:12]`, \(\rho_0=1/100\) and \(\nu=1/1000\). The common envelope leaves nominal versus loss_double uncoverable: its best margin over the pool is negative, and both the backend and the exhaustive box oracle report infeasibility. With per-candidate radii, protocol 9 (input 2 for four steps, left-central sensor) separates that pair with margin \(926083/10^{10}\), where the envelope margin is \(-1448351/(5\cdot10^9)\). The exact optimum is \(\{4,9\}\) at cost 19, confirmed by the 4096-subset exhaustive oracle and by Dijkstra. Readings and radii are replayed by the stencil oracle and the closed form. This shows the refinement can change feasibility. It is a property of this declared sub-pool, not of the 12 by 12 pool.

**Interpretation.** The gain comes from sharper but still proved uncertainty assumptions on the same model, not from a new measurement. In the source pool, the binding pairs are not ones involving the lower-radius candidate, so the cheapest guaranteed diagnosis is unchanged. An improvement was not required for acceptance, and none is claimed.

## 7. Scope and limits

* **Valid scope.** The results hold for independent resets, scalar closed intervals and a product uncertainty set. A persistent correlated nuisance invalidates the necessity half: box separation remains sufficient for any smaller joint set, but a joint geometry can separate where no coordinate does. That is NX02, not this track.
* **Search space.** Optimality is over the supplied finite pool only, not over all thermal interventions.
* **Unknown faults.** These lie outside the six-candidate population.
* **Cost units.** Costs are declared model accounting units.
* **Wire format.** The receipt uses the NX interchange encoding `[numerator, denominator]` for every exact rational, as specified in `handoff/nx36/architecture/INTERCHANGE_CONTRACT.md`. The packet's earlier suggestion of canonical strings is superseded by that shared contract. The existing `singularity.thermal-diagnostics/1` receipt keeps its string encoding and is not migrated. The schema name is `singularity.candidate-box-panel/1`.
* **No refactor of the existing backend.** `panels.py` is unchanged. The new module has its own private kernel adapted from the PANELS.md design. Factoring a shared kernel out of `panels.minimum_cost_panel` remains an integration option. It would need the existing panel compatibility tests to pass unchanged.
* **Arithmetic growth.** Bit lengths of readings and radii grow roughly linearly with horizon and are recorded per horizon in the receipt. At horizon 20 they stay small enough for exact replay in about ten seconds.

## Reproduction

```sh
PYTHONPATH=src python -m unittest tests.test_candidate_boxes -v
python scripts/candidate_box_thermal.py --check
```

The check recompiles everything and compares it with the retained JSON. It never rewrites the JSON; running without `--check` regenerates it as an explicit maintenance action.
