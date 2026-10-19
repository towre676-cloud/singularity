# A charge-aware separator compiler

Research unit OE11, 19 October 2026. This note extends the compressed charge interfaces of [VAKIL_BRIDGES.md](VAKIL_BRIDGES.md) §3 into a complete compiler for the local coefficients [x^j] L_G(x,q), j ≤ R. It contains one new interface operation (introduce), a vertex-order driver, a tree-decomposition driver with join nodes, and reusable step operators for periodic strips. It also proves a cell bound and a bit bound. Code: `src/singularity/separator_compiler.py`. Tests: `tests/test_separator_compiler.py`. Receipt: `scripts/separator_compiler.py`, which writes `results/separator_compiler.json`.

The note keeps four categories apart. §§1–6 are **proved project results**: exactness of the three operations and both drivers, the cell bound, the bit bound and the operator construction. §7 lists **exact computations** over declared finite populations. §8 gives **measurements**: wall-clock times on the session machine, which are printed and never retained. §9 records limitations and open targets. Two results are **established literature**: the standard tree-decomposition dynamic-programming paradigm, and the equality of vertex separation number and pathwidth (N. G. Kinnersley, *Information Processing Letters* 42 (1992) 345–350). None of the new statements has been formalized in Lean.

## 1. Objects

A *block* is a finite simple graph H with an ordered list T = (t_1, …, t_k) of distinct *boundary* (terminal) vertices. The remaining vertices form the *interior* I. Heights are nonnegative integers. For an interior vertex v, the pattern η_v ∈ {0,1}^k records its adjacencies to the terminals. For interior heights h : I → ℕ, define

- the volume |h| = Σ_v h_v;
- the charge Q(h) = Σ_v h_v η_v ∈ ℕ^k;
- the interior-side energy S(h) = Σ_{uv ∈ E(I)} (h_u − h_v)² + Σ_v |η_v| h_v².

The **interface** of (H, T) through depth R is the integer table

n_{j,Q,E} = #{ h : I → ℕ : |h| = j, Q(h) = Q, S(h) = E }, for 0 ≤ j ≤ R,

together with this metadata: the terminal degrees d_i = #{interior neighbours of t_i}; the terminal-edge set E_T, as index pairs; the set of patterns; and the declared depth R. This is exactly the dictionary produced by `charges.charge_interface`. The cells are keyed by (j, Q) with an energy histogram. Equivalently, A(x, z; q) = Σ n_{j,Q,E} x^j z^Q q^E. For T = ∅ the definition still makes sense. Then Q = (), S(h) = E_H(h), and

n_{j,(),E} = [x^j q^E] L_H(x, q).    (1)

The empty block (no vertices) has the single cell (0, (), 0) with count 1 (`empty_interface`).

**Lemma 0 (energy split).** For terminal heights b and interior heights h,

E_H(h, b) = S(h) + Σ_i d_i b_i² + E_T(b) − 2⟨b, Q(h)⟩.

*Proof.* Split the edges of H into three kinds. Interior–interior edges contribute their terms in S. Terminal–terminal edges give E_T(b). An interior–terminal edge v t_i contributes (h_v − b_i)² = h_v² + b_i² − 2 h_v b_i. Summing over the |η_v| terminal neighbours of v gives |η_v| h_v². Summing over the d_i interior neighbours of t_i gives d_i b_i². The cross terms add to −2 Σ_i b_i Σ_{v∼t_i} h_v = −2⟨b, Q(h)⟩. □

Thus the interface determines the full terminal kernel K_b = x^{|b|} q^{Σ d_i b_i² + E_T(b)} A(x, q^{−2b}; q). `charges.kernel_from_charges` implements this formula, and the tests use it to compare each interface with independent kernel enumeration.

## 2. The three operations

**Proposition 1 (introduce).** Let (H, T) be a block, let u ∉ V(H), and let S ⊆ T. Let H' be H plus the vertex u and the edges u s for s ∈ S. Let T' be T with u inserted at position p. Then the interface of (H', T') is obtained from that of (H, T) as follows:

- each cell (j, Q, E) becomes (j, Q with 0 inserted at p, E), with the same count;
- each pattern gets a 0 inserted at p;
- the degree sequence gets d_u = 0 inserted at p;
- old terminal indices ≥ p shift by one, and E_T gains the index pairs {p, index(s)} for s ∈ S.

The depth is unchanged.

*Proof.* The interior of H' is I, since u is a terminal. The edges inside I are unchanged. No interior vertex is adjacent to u, so η'_v is η_v with a 0 at position p. Hence |η'_v| = |η_v|, and S'(h) = S(h) for every h. The u-coordinate of Q'(h) is Σ_{v ∼ u, v ∈ I} h_v = 0, and its other coordinates are those of Q(h). The map h ↦ h is the identity on interior assignments, so every count is preserved and the cells are relabelled as stated. The interior neighbour count of u is 0, and the other d_i are unchanged. The new terminal–terminal edges are exactly u s, s ∈ S. Since the cells for each j ≤ R come from the old cells for the same j, completeness through R is preserved. □

`introduce_terminal(interface, vertex, neighbours, position=None)` implements this proposition. Its output is compared, field for field, with `charge_interface` of the actual larger graph. The comparison covers all 64 graphs on four vertices, two boundaries, every neighbour set and every insertion position: 2,816 comparisons. It is also compared with `kernel_by_enumeration` on that graph.

**Proposition 2 (forget; existing `charges.forget_terminal`).** Let t = t_s become interior. Let ζ ∈ {0,1}^{k−1} record its adjacencies to the retained terminals. If it is assigned height h ≥ 0, a cell updates by

(j, Q, E) ↦ (j + h, Q_{−s} + hζ, E + (d_s + |ζ|) h² − 2h Q_s).

The retained degrees become d_i + ζ_i, and the edges at t leave E_T. The result is the interface of (H, T ∖ t) through the same R.

*Proof.* An interior assignment of the new block is a pair (h, h_old). Every such pair arises once, so the new counts are sums over h of the old ones. The volume becomes j + h. The new charge adds h ζ_i at each retained terminal adjacent to t. For the new S, the vertex t has |η'_t| = |ζ|, which contributes |ζ| h². Its edges to old interior vertices contribute Σ_{v ∼ t} (h − h_v)² = d_s h² − 2h Q_s + Σ_{v∼t} h_v². The last sum is already contained in the old S, because those edges were interior–terminal edges and each contributed h_v² there. The old interior vertices gain the new terminal-free status of t and nothing else. Their patterns lose coordinate s and gain no new coordinate. Hence the energy shift is as displayed. A retained terminal i gains an interior neighbour exactly when ζ_i = 1. Because volume only grows, an output cell of volume ≤ R uses only source cells with j ≤ R − h. A source complete through R therefore suffices. □

**Proposition 3 (join; existing `charges.parallel_interfaces`).** Let (H_1, T) and (H_2, T) be blocks on the same ordered boundary. Suppose that their interiors are disjoint, that they have no edge between the two interiors, and that their terminal-edge sets are disjoint. Let H be their union, with T identified. Then the interface of (H, T) is the convolution

n_{j,Q,E} = Σ n¹_{j₁,Q₁,E₁} n²_{j₂,Q₂,E₂} over j₁ + j₂ = j, Q₁ + Q₂ = Q, E₁ + E₂ = E.

The degrees add and the terminal edges are united. The depth is the smaller of the two depths.

*Proof.* An interior assignment of H is a pair of independent assignments of I_1 and I_2. No edge joins I_1 to I_2, so S splits as S_1 + S_2. The pattern of an interior vertex is its pattern in its own block, so Q splits as Q_1 + Q_2. Volume is additive. The degree into the interior of H is the sum of the degrees into the two interiors. Terminal edges are counted once because they are disjoint. Every term with j ≤ R needs only j₁, j₂ ≤ R. □

## 3. The vertex-order driver

For an order v_1, …, v_N of V(G), `elimination_schedule` does the following at each step t. It introduces v_t with its edges to the current boundary. It then forgets every boundary vertex whose neighbours have all been introduced, in introduction order. `compile_graph(graph, order, R)` runs the schedule from `empty_interface(R)` and reads the cells (j, ()). Let V_t be the set of introduced vertices, and let B_t be the boundary list after the forgets of step t.

**Theorem 4 (exactness of `compile_graph`).** After every operation the current table is the interface of (G[V_t], B_t) through R. At the end B_N = ∅. The output is [x^j] L_G(x, q) for j ≤ R, as integer polynomials in q.

*Proof.* The proof is by induction over operations. The base case is the empty block. Consider an introduction of v = v_t. A vertex u ∈ V_{t−1} ∖ B_{t−1} was forgotten when all its neighbours had been introduced. At that time v had not been introduced, so v is not a neighbour of u. Hence N(v) ∩ V_{t−1} = N(v) ∩ B_{t−1}, and G[V_{t−1} ∪ {v}] is G[V_{t−1}] plus v and the edges to N(v) ∩ B_{t−1}. These are exactly the declared edges. Proposition 1 then gives the interface of (G[V_t], B_{t−1} + v). Forgetting a vertex leaves the graph unchanged and removes it from the boundary. By Proposition 2 this is exact for any boundary vertex. After v_N every vertex has been introduced, so every boundary vertex satisfies the forgetting rule and B_N = ∅. Identity (1) gives the coefficients. Introduction preserves the depth R, and Proposition 2 shows that forgetting is truncation-safe, so the declared prefix is complete. □

*Corollary (order and forgetting order are immaterial).* The final table is determined by (G, R). The intermediate table after any operation is determined by the pair (V_t, B_t), as an ordered list. The tests compare every one of the 120 orders for two five-vertex graphs.

**Width.** The width w(order) is the maximum boundary size. It is attained just after an introduction, where the boundary is {v_t} together with the vertices of V_{t−1} that still have a neighbour outside V_{t−1}. Thus w(order) = 1 + max_t |{u ∈ V_{t−1} : N(u) ⊄ V_{t−1}}| = 1 + vs(order), where vs is the vertex separation of the linear layout. The tests check this identity on 60 sampled graphs. By Kinnersley's theorem (literature), min over orders of vs equals the pathwidth. Hence a pathwidth-optimal order gives w = pw(G) + 1. The compiler does not search for such an order; the caller supplies one.

## 4. The tree-decomposition driver with joins

`compile_decomposition(graph, decomposition, R)` accepts any `TreeDecomposition` that passes `check_decomposition`. Each edge is charged at its owning (top) bag, using the existing `charge_owners`. The nodes are processed children-first. At a node x with bag X, kept in increasing label order, the driver does three things:

1. For each child c, it forgets the vertices of bag(c) ∖ X. It then introduces the vertices of X ∖ bag(c) without edges, at their sorted positions.
2. It forms the interior-free block on X carrying the edges owned at x (`boundary_block`, built by introductions only).
3. It joins all of these blocks with `parallel_interfaces`.

At the root, it forgets X.

For a node x, let V_x be the union of the bags in its subtree, E_x the edges owned in its subtree, and G_x = (V_x, E_x). The edges of G_x need not include every edge of G[V_x].

**Theorem 5 (exactness with joins).** The table at node x is the interface of (G_x, X) through R. The output at the root is [x^j] L_G for j ≤ R.

*Proof.* The proof is by induction from the leaves. Consider a child c whose table is the interface of (G_c, bag(c)). Forgetting the vertices of bag(c) ∖ X is exact by Proposition 2. Take a vertex y ∈ X ∖ bag(c). If y lay in V_c, the bags containing y would include bags in the subtree of c and the bag X. Their connectivity would then force y ∈ bag(c). So y ∉ V_c, and introducing y without edges is Proposition 1 with S = ∅. Now consider distinct children c, c'. A vertex in V_c ∩ V_{c'} lies in bags in both subtrees, so by connectivity it lies in X. Hence the interiors V_c ∖ X are disjoint. Every edge of G_c lies inside V_c, so no edge joins two interiors. Every edge is owned by exactly one bag, so the terminal-edge sets are disjoint. This includes the boundary block, whose edges are owned at x. Proposition 3 now gives the interface of the union. Its vertex set is X ∪ ⋃_c V_c = V_x, and its edge set is E_x. At the root, V = V_root because every vertex is covered, and E = E_root because every edge is owned. Forgetting X and applying (1) completes the proof. □

At a node, forgetting precedes introduction, so the boundary never exceeds max(|bag(c)|, |X|). The width is the largest bag size, w = tw + 1 for the supplied decomposition. Tests cover explicit join decompositions (a star joined at its centre, and C_6 split along the separator {0, 3}). They also cover elimination decompositions of all 1,024 five-vertex graphs, which contain branching nodes, and a forest decomposition.

## 5. Cost: the cell bound, ranges and the bit bound

Let D be the maximum degree of the represented graph; D is at most the maximum degree of G. Let k₊ = #{i : d_i > 0}.

**Theorem 6 (charge and energy ranges; cell bound).** Every nonzero cell (j, Q, E) satisfies 0 ≤ Q_i ≤ j, with Q_i = 0 when d_i = 0, and 0 ≤ E ≤ D j². Consequently the number of nonzero cells with j ≤ R is at most

C(k₊, R, D) = Σ_{j=0}^{R} (j+1)^{k₊} (D j² + 1) ≤ (R+1)^{k₊+1} (D R² + 1).

*Proof.* Take an assignment h with |h| = j realizing the cell. Then Q_i = Σ_{v ∼ t_i} h_v ≤ |h| = j, and the sum is empty when d_i = 0. For nonnegative a, b, (a − b)² ≤ a² + b². Hence S(h) ≤ Σ_v (deg_I(v) + |η_v|) h_v² ≤ D Σ_v h_v² ≤ D (Σ_v h_v)² = D j². Moreover S ≥ 0, since it is a sum of squares. For fixed j there are at most (j+1)^{k₊} charges and D j² + 1 energies. □

**Corollary (cost).** Suppose an order has width w and N = |V|. Every table along the schedule has at most C(w, R, D) ≤ (R+1)^{w+1}(DR² + 1) cells. This bound does not depend on N. The operation costs are as follows:

- Introduction touches every cell once, which is O(w · C) tuple work.
- Forgetting performs at most R + 1 − j updates per cell, which is O(R · C).
- A join performs at most C₁ C₂ updates.

So `compile_graph` uses O(N · R · w · C(w, R, D)) dictionary updates. This is linear in N at fixed (w, R, D). The integers involved obey the following bound.

**Theorem 7 (bit bound).** If the interior has m ≥ 1 vertices, then n_{j,Q,E} ≤ binom(m + j − 1, j) ≤ m^j. Every count therefore has at most ⌊j log₂ m⌋ + 1 ≤ R log₂ N + 1 bits.

*Proof.* The counted assignments are among the weak compositions of j into m parts, and there are binom(m+j−1, j) of these. A weak composition is a multiset of size j drawn from m vertices, and sending a multiset to its sorted sequence injects these multisets into the m^j sequences. □

The coefficients themselves satisfy the same bound with m = N. The receipt checks Σ_E [x^R q^E] L_G = binom(N+R−1, R) for every benchmark graph. It also checks that the maximal count bit length is at most the bit length of binom(N+R−1, R) (`count_bit_bound`). Measured bit lengths are within three bits of that bound, and within two bits for n ≥ 20. Charges never exceed R, and energies lie in [0, D R²]. For each family the energy maximum equals D R² exactly (§7).

## 6. Reusable step operators

A segment of a schedule is a finite list of introductions and forgettings. Introduction and forgetting act on cells (j, Q) independently of E, apart from adding an E-independent shift. By Propositions 1–2, each is therefore a ℤ-linear map on the free module of cells that commutes with q^s (E ↦ E + s). So is the composite Φ of a segment, and

Φ(Σ n_{j,Q,E} e_{j,Q,E}) = Σ n_{j,Q,E} q^E Φ(e_{j,Q,0}).

`build_step_operator(template, segment, seeds)` computes the rows (j, Q) ↦ Φ(e_{j,Q,0}) as sparse maps {(j', Q') : {shift : count}}. It applies the segment to unit cells that carry the template's metadata. The shifts can be negative; actual energies cannot. Rows are built for the closure under Φ of the seed keys, by breadth-first search. That closure contains the support of every iterate of every interface whose keys are seeds. The builder rejects a segment whose output metadata differs from the template's. The checked metadata are the boundary size, the terminal degrees and the terminal-edge index pairs.

**Proposition 8 (stationary steps).** Introduction and forgetting locate terminals by position; labels play no other role. Suppose a later segment is the label translate τ of the template segment, and its starting boundary is the positional translate of the template boundary with the same metadata. Then the two segments define the same linear map on cells. Applying the rows and renaming the boundary therefore reproduces the direct computation exactly.

*Proof.* Translate both segments into positional operations: insert at a position with neighbour positions, or forget at a position. These sequences coincide. Each positional operation's action on cells depends only on the positions and on the metadata (d, E_T), and these agree at every intermediate stage by induction. Patterns evolve independently of the cells, so `apply_step_operator` replays the segment on metadata alone to update them. □

`periodic_plan(graph, order, period, anchors)` finds the first cut c₀ whose positional metadata equals that of the next cut. It then uses the maximal run of translated segments, verifying each translate explicitly. The translation sends order[i] to order[i + period] and fixes the anchors; for C_n the anchor is vertex 0. `periodic_compile` runs the prefix directly, applies one operator for all stationary steps and runs the suffix directly. The tests and the receipt compare its output with `compile_graph` and, where feasible, with direct enumeration.

## 7. Exact computations (retained in `results/separator_compiler.json`)

**Verification.**

- On all 1,099 labelled graphs with at most five vertices, under three orders each (identity, reverse, seeded shuffle), at R = 3: 3,297 graph–order pairs. Both `compile_graph` and `compile_decomposition` equal `heights.local_coefficients`.
- Paths P_1–P_8, cycles C_3–C_8, ladders P_2×P_1–P_2×P_4 and strips P_3×P_1–P_3×P_3 equal direct enumeration for every R ≤ 4 (105 comparisons).
- Five graphs (P_12, C_10, P_2×P_6, P_3×P_4, and a disconnected graph with isolated vertices) agree with the bag-message engine (`decomposition_histogram`) and with the connected-support compiler (`locality.pinned_series` with λ = 0, which is L_G).

**Benchmarks.** The graphs are `strip_graph(rows, n)` with vertex r + rows·c, in natural order. Every row was also confirmed in three further ways: by the step operator, by direct enumeration (for at most 24 vertices) and by the connected-support compiler (for n ≤ 80). Here "cells" means nonzero (j, Q, E) cells, and "work" means cells summed over all operations. "Direct profiles" is Σ_{j≤R} binom(N+j−1, j), the number of states that direct enumeration visits.

| family | R | n | N | width | peak cells | cell bound | max bits / bound | E range | operator rows / terms | work | direct profiles |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P_n | 4 | 10 | 10 | 2 | 74 | 275 | 7 / 10 | 0–32 | 15 / 35 | 915 | 1,001 |
| P_n | 4 | 40 | 40 | 2 | 74 | 275 | 16 / 17 | 0–32 | 15 / 35 | 5,355 | 135,751 |
| P_n | 4 | 200 | 200 | 2 | 74 | 275 | 26 / 27 | 0–32 | 15 / 35 | 29,035 | 70,058,751 |
| C_n | 4 | 10 | 10 | 3 | 92 | 1,223 | 8 / 10 | 0–32 | 39 / 80 | 937 | 1,001 |
| C_n | 4 | 200 | 200 | 3 | 92 | 1,223 | 26 / 27 | 0–32 | 39 / 80 | 35,897 | 70,058,751 |
| P_2×P_n | 4 | 10 | 20 | 3 | 165 | 1,807 | 11 / 14 | 0–48 | 35 / 126 | 4,611 | 10,626 |
| P_2×P_n | 4 | 200 | 400 | 3 | 165 | 1,807 | 30 / 31 | 0–48 | 35 / 126 | 127,731 | 1,093,567,501 |
| P_3×P_n | 3 | 200 | 600 | 4 | 113 | 2,868 | 24 / 26 | 0–36 | 35 / 120 | 132,315 | 36,361,101 |
| P_3×P_n | 4 | 5 | 15 | 4 | 327 | 10,993 | 9 / 12 | 0–64 | 70 / 330 | 4,424 | 3,876 |
| P_3×P_n | 4 | 40 | 120 | 4 | 339 | 10,993 | 22 / 24 | 0–64 | 70 / 330 | 74,273 | 9,381,251 |
| P_3×P_n | 4 | 200 | 600 | 4 | 339 | 10,993 | 31 / 33 | 0–64 | 70 / 330 | 393,633 | 5,490,526,251 |

The receipt holds all 56 rows: four families, R ∈ {3, 4}, and n ∈ {5, 10, 20, 40, 80, 160, 200}. Each row also carries the peak and widest-step charge keys and the coefficient SHA-256 prefix, which is integrity data only. The peak storage is constant in n once the boundary metadata becomes stationary, as Theorem 6 predicts. The work grows linearly in n, and the maximal count bit length grows like R log₂ n. The bound of Theorem 6 is not tight: across the receipt, the widest-step cells are 1–29% of it. The bound column is evaluated at the widest step; every intermediate table also satisfied the bound at its own step (`bound_violations` = 0).

## 8. Measurements (printed, not retained)

These are single wall-clock runs on the session machine (Python 3.13.16), while another agent was also running. They show orders of magnitude and are not reproducible quantities. All times are in seconds.

| case | (a) compile | (b) operator build / apply ×steps | (c) query | direct enumeration | connected support |
|---|---|---|---|---|---|
| P_n, n=5, R=4 | 0.0005 | 0.0003 / 0.0001 ×2 | <0.0001 | 0.0004 | 0.013 |
| P_n, n=20, R=4 | 0.0030 | 0.0005 / 0.0014 ×17 | <0.0001 | 0.087 | 0.018 |
| P_n, n=200, R=4 | 0.029 | 0.0003 / 0.019 ×197 | <0.0001 | n/a | n/a |
| C_n, n=20, R=4 | 0.0042 | 0.0010 / 0.0022 ×16 | <0.0001 | 0.088 | 0.0085 |
| P_2×P_n, n=10, R=4 | 0.0052 | 0.0019 / 0.0013 ×7 | <0.0001 | 0.100 | 0.053 |
| P_2×P_n, n=200, R=4 | 0.127 | 0.0019 / 0.048 ×197 | <0.0001 | n/a | n/a |
| P_3×P_n, n=5, R=4 | 0.0055 | 0.0063 / 0.0007 ×2 | <0.0001 | 0.027 | 0.152 |
| P_3×P_n, n=40, R=4 | 0.065 | 0.0070 / 0.017 ×37 | <0.0001 | n/a | 0.213 |
| P_3×P_n, n=200, R=4 | 0.327 | 0.0063 / 0.086 ×197 | <0.0001 | n/a | n/a |

**Crossover.** Direct enumeration wins or ties only for graphs of about five vertices at R = 4 (P_5: 0.0004 against 0.0005). At 15–20 vertices the compiler is already 5–30 times faster, and direct enumeration becomes infeasible beyond a few dozen vertices: P_3×P_200 would visit 5.5·10⁹ profiles.

**Step operators.** Construction is a one-time cost, 0.0003–0.007 s, independent of n. For n = 200, applying the operator for all steps took 26–67% of the direct compile time (P_3×P_n 26%, P_2×P_n 38%, C_n 57%, P_n 67%), because a single sparse map replaces several dictionary passes per column. The gain is a constant factor, not an asymptotic one. Querying a closed interface is a list read.

**Connected-support compiler.** Through type memoization, `locality.pinned_series` is nearly constant in n for these bounded-degree families. It is slower than the separator compiler at these sizes for ladders and strips (0.05–0.2 s), and comparable for paths and cycles. It applies only to λ-pinned series such as L_G; it does not produce terminal interfaces.

## 9. Scope and limitations

- **Theorems.** Propositions 1–3 and 8, Theorems 4–7, and the width identity w = 1 + vs(order) for this schedule.
- **Literature.** vs = pathwidth (Kinnersley); the tree-decomposition dynamic-programming paradigm.
- **Exact computations.** The verifications over the declared finite populations above.
- **Measurements.** All times, and the observed ratios of cells to their bound.

Limitations:

1. **No order or decomposition search.** The cost is exponential in the supplied width (Theorem 6). The caller supplies the order or decomposition, and a poor order can be much wider than the treewidth. Joins multiply supports, so a join can cost C₁C₂.
2. **Truncated prefixes only.** The compiler gives the local series L_G modulo x^{R+1}, as exact integer q-polynomials. Normalization by (1 − x^n), span marking and the primewise lift are not built in. They follow from the existing post-processing (`heights.normalize_local_coefficients`) only where that post-processing is valid. Finite prefixes imply nothing about the full series, isomorphism or analytic continuation.
3. **Interior identities are not stored.** The interface does not record interior labels. `introduce_terminal` cannot detect a caller who reintroduces a forgotten vertex; both drivers prevent this by construction, as Theorems 4 and 5 show. Likewise `parallel_interfaces` treats interiors as disjoint copies, by its declared input interpretation.
4. **Stationarity is not automatic.** Step operators require exact stationarity of positional metadata, which is verified. A strip whose first columns are non-stationary is handled by the direct prefix. Families with non-periodic attachments receive no operator.
5. **The bit bound is not tight.** Theorem 7 is a worst-case bound, and the measured bit lengths stay just below it. No sharper asymptotic for the largest count is claimed.
6. **Not proved here.** The cell bound ignores the lattice and semigroup structure of achievable charges ([VAKIL_BRIDGES.md](VAKIL_BRIDGES.md) §4). A Hilbert-function forecast of the exact support remains a research target.

No existing file was edited. `charges.py` was reused unchanged; no defect was found in `charge_interface`, `forget_terminal`, `parallel_interfaces`, `kernel_from_charges` or `_charge_depth` during this work. One feature of the existing code is a limitation rather than a bug: `charge_interface` rejects an empty boundary, so the empty block is supplied by `empty_interface`.

## Reproduction

```sh
PYTHONPATH=src python -m unittest tests.test_separator_compiler -v
PYTHONPATH=src python scripts/separator_compiler.py --check
```

The test module takes about 4 s and the receipt about 9 s on the session machine. Both use only the standard library and exact integers.
