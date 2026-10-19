# Incremental connected-support compilation (NX16)

Status of this note: units NX16-A, NX16-B and NX16-C, on branch `claude/exciting-brown-95vyq3`. The note keeps four categories separate. **Literature** is background that is cited and not reproved. **Proved** marks project statements proved here. **Exact finite** marks computations over a declared finite population. **Open** marks what remains a research target.

Code: `src/singularity/incremental_locality.py`. Tests: `tests/test_incremental_locality.py`. Receipt: `scripts/incremental_locality.py --check` and `results/incremental_locality.json`.

## 1. Objects

Take vertices `0, ..., n-1`, symmetric nonnegative integral edge weights `w_uv`, and nonnegative integral pinnings `lambda_v`. For a height vector `h` of nonnegative integers put

\[
E_w(h)=\sum_{u<v}w_{uv}(h_u-h_v)^2+\sum_v\lambda_vh_v^2,\qquad
F_w(x,q)=\sum_{h\ge0}x^{|h|}q^{E_w(h)} .
\]

A zero weight is the same thing as a missing edge. Every energy is a nonnegative integer, so each coefficient `[x^m]F_w` is a finite sum, namely a polynomial in `q` with nonnegative integral exponents and nonnegative integral counts. Rational weights are allowed only through a declared energy unit. `from_rational_weights` multiplies every weight and pinning by the least common multiple `L` of their denominators and records `energy_unit = 1/L`. The exponent `k` then means energy `k/L`. Negative weights are outside this contract.

The **positive-weight graph** `G_w` has an edge `uv` exactly when `w_uv > 0`. The **decoration** of a vertex is `d_v = sum_u w_uv + lambda_v`, its weighted degree plus its pinning. Expanding the square gives

\[
E_w(h)=\sum_v d_vh_v^2-2\sum_{u<v}w_{uv}h_uh_v .
\]

With `w = 1` on the edges of a graph `H` and `lambda_v = lam` constant, `F_w` is the `F_lam(H)` of `locality.py`: `lam = 0` gives `L_H` and `lam = 2` gives `A_H`. The implementation checks this equality against `locality.pinned_log`.

Now give each vertex its own variable `x_v`. For a vertex set `T`, `Z_T` is `F_w` with `x_v = 0` for `v` outside `T`. Equivalently, `Z_T` sums over heights that vanish outside `T`, with the full energy. In the expanded form this means vertices in `T` keep their **ambient** decorations `d_v`. Define

\[
\Phi_S(w)=\sum_{T\subseteq S}(-1)^{|S|-|T|}\log Z_T(w),
\]

and then specialise every `x_v` to the common volume variable `x`.

## 2. The support expansion (proved)

**Lemma 1.** `Phi_S` is exactly the part of the multivariate series `log F_w` whose monomials use every vertex of `S` and no other vertex.

*Proof.* `F_w` is a formal power series in `x_0, ..., x_{n-1}`, with coefficients in `Z[q]` and constant term `1`, so `log F_w` is well defined. Write `Psi_A` for the part of `log F_w` whose monomials have support exactly `A`. Setting `x_v = 0` outside `T` is a ring homomorphism. It commutes with `log` and kills exactly the monomials whose support is not contained in `T`. Hence `log Z_T = sum_{A subset T} Psi_A`. Möbius inversion on the Boolean lattice gives `Psi_S = sum_{T subset S} (-1)^{|S|-|T|} log Z_T = Phi_S`. ∎

**Corollary 2.** `Phi_S = O(x^{|S|})`: each monomial of `Psi_S` has every exponent `x_v`, `v in S`, at least one.

**Lemma 3 (disconnected supports vanish).** If `S` is not connected in `G_w`, then `Phi_S = 0`.

*Proof.* Write `S = A ⊔ B` with both parts nonempty and no positive edge between them. Take `T ⊆ S` and a height vector `h` supported in `T`. The cross terms `w_ab h_a h_b`, with `a ∈ A` and `b ∈ B`, vanish because those weights are zero. Every other term involves only `T∩A` or only `T∩B`. So the energy splits, and `Z_T = Z_{T∩A} Z_{T∩B}`. Then `log Z_T = f(T∩A) + g(T∩B)`. An alternating sum over `T ⊆ S` of a function of `T∩A` alone factors through `sum_{T_B ⊆ B} (-1)^{|B|-|T_B|} = 0`, because `B` is nonempty. The same holds for `g`, using that `A` is nonempty. ∎

**Lemma 4 (what Phi depends on).** `Phi_S` depends only on the decorations `d_v` for `v ∈ S` and the internal weights `w_uv` for `u, v ∈ S`. It is unchanged by any bijection of `S` that preserves both.

*Proof.* For `T ⊆ S`, the expanded energy of a height supported in `T` involves only these quantities. A relabelling that preserves them permutes the heights and preserves volume and energy. ∎

**Theorem 5 (support expansion).** For every `R ≥ 0`,

\[
\log F_w\equiv\sum_{S\ \text{connected in }G_w,\ |S|\le R}\Phi_S(w)\pmod{x^{R+1}} .
\]

*Proof.* By Lemma 1, `log F_w` is the sum of `Psi_S` over nonempty `S`. The supports with `|S| > R` contribute nothing modulo `x^{R+1}` by Corollary 2. The disconnected ones contribute nothing by Lemma 3. ∎

The unweighted form of this theorem is the existing SNG-F55 locality result. What is new here is the weighted, per-vertex-pinned statement. Its consequence is that a zero weight behaves exactly as an absent edge.

## 3. The union-graph difference identity (proved)

Compare two weightings `(w, lambda)` and `(w', lambda')`. Let `D` be the set of endpoints of every edge whose weight changes, together with every vertex whose pinning changes. Let `U` be the **union graph**: it has an edge `uv` whenever `w_uv > 0` or `w'_uv > 0`.

**Theorem 6.** Modulo `x^{R+1}`,

\[
\log F_{w'}-\log F_w\equiv\sum_{\substack{S\ \text{connected in }U\\ |S|\le R,\ S\cap D\ne\varnothing}}\bigl(\Phi_S(w')-\Phi_S(w)\bigr).
\]

*Proof.* Each of `G_w` and `G_{w'}` is a subgraph of `U`. So a set connected in either graph is connected in `U`. By Lemma 3 we may therefore sum both expansions of Theorem 5 over all `U`-connected `S` with `|S| ≤ R`; the added terms are zero. Now suppose `S ∩ D = ∅`. Every changed edge has both endpoints in `D`, so no changed edge meets `S`. In particular, no internal weight of `S` changes. No weight incident to a vertex of `S` changes either, so the weighted degrees on `S` are the same. No pinning on `S` changes. By Lemma 4, `Phi_S(w') = Phi_S(w)`. Subtracting the two sums leaves only the supports that meet `D`. ∎

**Why the three naive filters are wrong.** Each failure below is exhibited by an exact test, `test_union_difference_identity_and_naive_filters`, on a path with 4 vertices at `R = 3`.

* *New-graph supports only.* After a deletion, a support that was connected only through the deleted edge has `Phi_S(w') = 0` and `Phi_S(w) ≠ 0`. This filter drops that term.
* *Old-graph supports only.* After an insertion, a newly connected support has `Phi_S(w) = 0`, and this filter drops it.
* *Supports containing both endpoints of a changed edge.* A singleton `{u}` contains only one endpoint, yet its decoration `d_u` changes, so `Phi_{{u}}` changes. This happens in the mandatory two-vertex example below. For a change to the pinning of a single vertex, "contains every endpoint" coincides with "meets `D`".

## 4. Worked example (exact finite; regression)

Compare two isolated vertices with one edge between them, at zero pinning and `R = 2`.

* Isolated: `F_0 = 1 + 2x + 3x^2` and `log F_0 = 2x + x^2`.
* Edge: `F_1 = 1 + 2q x + (1 + 2q^4) x^2` and `log F_1 = 2q x + (1 + 2q^4 - 2q^2) x^2`.
* Each singleton contributes `q x + (q^4 - q^2/2) x^2`. The pair contributes `(1 - q^2) x^2`.
* At `q = 1/2`: `Delta log F = -x - 3x^2/8`, and `F_1 = 1 + x + 9x^2/8`.
* Applying the reverse update recovers the original compiled state exactly, including the support index.

All of these values are retained in `results/incremental_locality.json` under `contract`.

## 5. Cache soundness (proved)

A support's memo key is `(k, decorations, weighted internal edges)` after relabelling `S` to `0..k-1`. The relabelling minimises the edge list over orders that respect the vertex classes `(decoration, sorted incident internal weights)`. When the number of such orders exceeds `CANONICAL_LIMIT`, the sorted vertex labelling is kept instead. Either way, the key is a **complete description** of a decorated, weighted graph that is isomorphic to `S`. Two supports with equal keys are therefore isomorphic in the sense of Lemma 4, and they have equal `Phi`. Moreover, `Phi` is computed from the key alone (`_phi`), so a cache entry is correct by construction. Cache slots also carry `R` and the convention string.

Consequences:

* There are no false collisions across graphs. Sharing one cache between unrelated graphs and truncation depths is safe (`test_cross_graph_cache_isolation`). The packet's warning about a set-only fallback key does not apply, because the fallback key here is the full labelled description, not a vertex-set name.
* The labelled fallback loses only sharing (`test_labelled_fallback_keys_are_exact` forces it everywhere and gets identical logs).

## 6. Update algorithm and its locality (proved)

`apply_local_changes(comp, changes)` runs in five steps.

1. It validates every change against the current state before changing anything. A **stale** patch, whose recorded old value differs from the current one, raises `ValueError`. So does a duplicate target, and so does an out-of-range vertex. In all three cases the state is left untouched.
2. It enumerates the `U`-connected sets with `|S| ≤ R` that meet `D`. It does this by growing from the least marked vertex while avoiding earlier marked vertices (`connected_sets_meeting`). Adjacency is read only at members of the growing set.
3. It reads the old keys from the support index; a support missing from the index is one that was disconnected in the old graph. It then applies the changes and computes the new keys, or none for a support that is now disconnected.
4. It adds `Phi(new) - Phi(old)` to `log F`, with an absent side counted as zero, and updates the support index.
5. It optionally emits a `singularity.locality-update/1` record (section 7).

By Theorem 6 the result is exactly the recompiled logarithm. By Theorem 5 and the correctness of the index, the new support index equals the recompiled index.

**Proposition 7 (local update cost).** Let `Delta_U` be the maximum degree of `U` and `N` the set of vertices within `U`-distance `R-1` of `D`. Assume that dictionary operations take unit time.

* Every affected support lies inside `N`. A connected set of at most `R` vertices that meets `D` has every member within distance `R-1` of `D`.
* The number of affected supports is at most `|D| · sum_{k=1}^{R} (k-1)! Delta_U^{k-1}`. Here is the proof. Grow a connected `k`-set from a vertex of `D` by repeatedly adding a neighbour of the current set. At step `j` there are at most `j·Delta_U` choices, so there are at most `(k-1)! Delta_U^{k-1}` growth sequences, and every such set arises from one of them. Literature gives sharper bounds of the form `(c·Delta)^{k-1}`; they are not needed here.
* The work per affected support depends only on `R`, `Delta_U` and the decorations and weights inside `N`. That work is one key canonicalisation, costing at most `CANONICAL_LIMIT · R^2` comparisons, and two cache lookups. On a cache miss, computing `Phi` enumerates `2^k` subsets and `sum_{j ≤ R} C(j + c - 1, c - 1)` profiles per restricted block. The exponents are at most `R^2 · max d_v`. The coefficients of `Phi` are functions of the key alone.
* Updating `log F` costs `R+1` polynomial additions per changed support and `R+1` for the final merge. Their exponent range is bounded as above. The **bit size** of the coefficients of `log F`, however, does depend on the whole graph, because `log F` sums contributions from every support in the graph.

So, after setup, the number of supports touched, the polynomial operations and the cache traffic depend only on the decorated radius-`(R-1)` union neighbourhood of `D`. They do not depend on `n`. The only `n`-dependent quantities are the bit lengths of the global sums. The scaling receipt below measures both.

The update does not promise constant-time output of the full series. Formal exponentiation costs `R(R+1)/2` polynomial products, and it touches every coefficient. The operation count of that query is independent of `n`, but its operands carry `n`-dependent coefficient sizes.

## 7. Update records and replay

A `singularity.locality-update/1` record stores the following fields:

* the baseline specification (`n`, the positive weights, the pinnings, and the energy unit as `[numerator, denominator]`);
* the baseline logarithm;
* the exact changes, as `{kind, target, old, new}`;
* `affected_endpoints` (the set `D`);
* `declared_union_edges`, the edges of `U` among the vertices of the affected supports;
* the list of affected supports, each with its old and new contribution or `null`;
* `result_log`.

Polynomials use the existing `polynomials.polynomial_to_json` encoding, `[exponent, numerator, denominator]`.

`verify_local_update` replays a record without using the incremental code.

1. It rebuilds the old and new specifications, checking every old value.
2. It checks **completeness**. It recomputes `U` from the two specifications and takes the ball of radius `R-1` around `D`. It then forms every subset of at most `R` ball vertices, keeps those that meet `D` and are `U`-connected by a direct search, and requires the listed supports to be exactly these.
3. It recomputes every listed contribution from its definition, `support_contribution_by_definition`. That function enumerates heights supported in each `T ⊆ S` with the edge-difference energy and uses no memo and no factorisation. A side must be `null` exactly when the support is disconnected in that version. As a by-product, this also confirms that disconnected supports have zero contribution.
4. It checks that `result_log` equals the baseline log plus the listed corrections.
5. Optionally, it compares `exp(baseline log)` and `exp(result log)` with `direct_series`.

A digest would not be enough here, because a hash cannot show that an omitted support was zero; step 2 is what does that. The baseline logarithm is trusted unless step 5 runs. The completeness check is exponential in the ball size, so it is budgeted.

## 8. Evidence

**NX16-A (proved + exact finite).** The tests check the following:

* The two-vertex example (section 4) holds exactly, including the invalidation of both singletons and exact reversal.
* Zero weight is absence: a `1 → 0` update yields exactly the compiled state of the graph without that edge.
* The compiler agrees with `direct_series` on 30 random weighted, pinned graphs with `n ≤ 5` and `R ≤ 3`. Every exponent is an ordinary nonnegative integer.
* With positive weights and no pinning, it agrees with `weighted.weighted_coefficients` on 12 cases. With unit weights, it agrees with `heights.local_coefficients` and with `locality.pinned_log` at `lam = 0` and `lam = 2`.
* Disconnected supports vanish, and `Phi_S = O(x^{|S|})`, both checked by definition.
* The union identity holds, and the naive filters fail as described in section 3.
* Rational weights are handled through a declared unit, and floats are rejected.
* Malformed input is rejected: `TypeError` for `bool`, `float` and `str`, and `ValueError` for bad values or shapes.

**NX16-B (exact finite).** The population is all `3^6 = 729` weightings of `K_4` with edge weights in `{0,1,2}` and zero pinning, at `R = 3`.

* Every single-edge edit was checked: 8748 edits, comprising 2916 insertions, 2916 deletions and 2916 weight changes. Each updated state, both log and support index, equals full recompilation. Each recompiled series equals direct enumeration over the box `[0,3]^4`.
* Pinning changes `0 → 2` and back were checked on all 64 unweighted 4-vertex graphs, with exact reversal.
* A sequential run on 5 vertices applied 14 random batches of edge and pinning changes, mixing in-place and copying updates. After every batch it compared against recompilation and direct enumeration, and it replayed each update record with the direct oracle. Reversing the whole sequence recovered the original state exactly.
* Stale, duplicate and out-of-range patches were rejected, with the state unchanged.
* Sharing a cache across 40 random graphs and different `R` changed no result. Supports with the same vertex set but different weights or ambient degrees receive different keys.
* Tampering with a record was detected: removing a support, swapping a contribution, altering the result log, a stale change, a missing union edge, a wrong `D`, or an altered baseline.

**NX16-C (proved bound + exact finite measurement).** The family is the ladder `P_2 × P_m`, with maximum degree 3 and at most 4 after the diagonal insertion, for `m = 16, 32, 64, 128, 256, 512` (`n` up to 1024), at `R = 4`. Four edits are made in column `m // 2`: a rung reweight `1 → 3`, a rail deletion, a diagonal insertion, and a pinning change `0 → 2`. Retained, separately for each `m`, are:

* **setup**: 319 to 11231 supports, which grows linearly with `n`; 15 distinct keys; 15 contributions computed;
* **storage**: support-index entries, which equal the supports, and 102 cache entries;
* **update**, with a cold cache after setup and with a warm cache. The counts are 55, 53, 69 and 35 affected supports. On a cold cache the edits compute 13, 4, 17 and 2 new contributions; on a warm cache, 0. The edits use 1395, 780, 1790 and 540 polynomial additions. **All of these counts are identical for every `m`**, and the script asserts this.
* **query**: 10 polynomial products in the formal exponential;
* **coefficient bits**: the largest numerator in the log grows from 11 to 16 bits, and the largest numerator in the series from 14 to 36 bits. This growth is consistent with the counts `C(n+R-1, R) ≈ n^4/24`. Denominators stay at 2 to 3 bits.

Every updated log equals full recompilation, whose support count grows with `n`. For the unit-weight edits it also equals `locality.pinned_log`. On the ladder with `m = 3`, every edit also matches `direct_series`. Wall-clock times are printed and not retained. On the development machine, a cold update took about 6 to 45 ms at every size, and a warm update about 2 to 6 ms. Full recompilation took about 40 ms at `n = 32` and about 300 ms at `n = 1024`.

**Receipts.** Two update records, on ladders with `m = 3` (oracle included) and `m = 5`, each make three simultaneous changes. They are retained in full. `--check` regenerates everything, compares the result with the retained JSON, and replays the retained records with `verify_local_update`.

## 9. Proposition for the manuscript (proposed text; chapters are not edited here)

> **Proposition (incremental locality).** Let `F_w` be the height series of a nonnegative integral weighted energy with per-vertex pinning. Let `D` be the set of vertices touched by a change of weights or pinnings, and let `U` be the union of the old and new positive-weight graphs. Then `log F` changes, modulo `x^{R+1}`, by the sum of `Phi_S(w') - Phi_S(w)` over the `U`-connected sets `S` with at most `R` vertices that meet `D`. Every such `S` lies within `U`-distance `R-1` of `D`, and there are at most `|D| sum_{k ≤ R} (k-1)! Delta_U^{k-1}` of them. A zero weight is an absent edge. Singletons in `D` must be recomputed even when they contain only one endpoint of a changed edge.

## 10. Limitations and open items

* The scope is nonnegative integral weights, or rational weights with a declared unit. Negative or signed energies, continuous weights, vertex deletion or insertion, and changes to `n` are not handled.
* The `n`-independence in Proposition 7 concerns support counts, polynomial-operation counts and cache traffic, and it assumes unit-time dictionary operations. Coefficient bit sizes of the global log and series grow with `n`, roughly `R log n` bits for the series. Wall times are measured on one machine and are not a proof.
* The bound in Proposition 7 is fixed-parameter: it is useless for large `R` or dense union graphs.
* Copying updates (`in_place=False`) and records that include the baseline cost `O(size)`. Only in-place updates without a record are local.
* The baseline logarithm in a record is trusted unless the direct oracle runs. Replaying completeness is exponential in the size of the radius-`(R-1)` ball and is budgeted.
* Boundary-charge-aware updates (`charges.py`, `separator_compiler.py`), dynamic canonicalisation, and moment or cycle extensions under updates are left to later pushes.
* `locality.connected_supersets` copies the full adjacency on each call, which costs `O(n)`. This module therefore has its own local enumerator, which is tested against brute force. A lazy version of the shared function would let both modules use one enumerator; that is a suggested change to an existing file.
