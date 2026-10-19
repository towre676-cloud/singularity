# Shared experiment panels for finite candidate families

**Unit:** OE08. **Status:** proved project results for the statements marked *Lemma*, *Theorem* and *Proposition*, plus exact computations over the declared finite populations below. **Code:** [`panels.py`](../../src/singularity/panels.py), tests in [`test_panels.py`](../../tests/test_panels.py), receipt [`scripts/panels.py`](../../scripts/panels.py) retained as [`results/panels.json`](../../results/panels.json). The operator language and SNG-O03 are those of [Chapter 15](../chapters/15_operators_experiments.md) and [OPERATORS-v1](../specifications/OPERATORS-v1.md).

Chapter 15 separates three optimization problems: the cheapest single witness for one pair (solved by SNG-O03), maximum margin under a budget, and minimum-cost shared panels for many pairs. This note treats the third problem exactly and adds a certified noisy decoder.

## 1. Setting

Fix an operator system \((M_i, L_j, c_i>0, \gamma_j\ge0)\) and candidate states \(v_1,\ldots,v_k\), \(k\ge2\). An experiment \(e=(j,w)\) has cost \(c(e)=\gamma_j+\sum_{i\in w}c_i\) and reading \(r_e(v)=L_jM_wv\), with the chronological word convention of Chapter 15. A **pool** \(\mathcal P\) is either the set of all experiments of cost at most \(C\), or an explicit finite list. The pairs are \(\Pi=\{\{a,b\}:a<b\}\), and \(m=|\Pi|=\binom k2\).

A **panel** is a subset \(S\subseteq\mathcal P\) with cost \(c(S)=\sum_{e\in S}c(e)\). With **margins** \(\mu_e\ge0\), experiment \(e\) covers \(\{a,b\}\) if \(|r_e(v_a)-r_e(v_b)|>2\mu_e\). Exact separation is \(\mu\equiv0\). Box-robust separation is \(\mu_e=\varepsilon_e>0\). A panel is *separating* if it covers every pair.

**Proposition 1 (finite pool).** The set of experiments of cost at most \(C\) is finite.

*Proof.* Let \(c_*=\min_ic_i>0\). A word of cost at most \(C\) has length at most \(C/c_*\), so there are finitely many such words over a finite alphabet, and finitely many observation indices. \(\square\)

The implementation enumerates these words by depth-first extension. It stops with `ValueError` when a declared budget on the number of experiments is exceeded. That is a budget refusal, not a mathematical result.

## 2. Minimum-cost separating panels

The problem is weighted set cover with universe \(\Pi\) and the sets \(\mathrm{cov}(e)\). Weighted set cover is NP-hard in general; this is established background (Karp's set-cover problem). Our instances are special, because the covered pairs of one experiment are the cross pairs of a partition of the candidates, and we do not claim that this special class is hard. The exact method below is worst-case exponential. **No polynomial-time exact method is promised.**

**Infeasibility.** If some pair is covered by no pool member, no panel exists. The functions return `feasible=False` and name every such pair. In exact mode with the complete cost-\(\le C\) pool, Proposition 4 below says whether the pair is future-equivalent or only needs a larger budget.

### 2.1 Lower bounds

At a search node, \(U\subseteq\Pi\) is the set of uncovered pairs and \(A\subseteq\mathcal P\) the set of experiments still allowed. For \(p\in U\) let \(\kappa(p)=\min\{c(e):e\in A,\ p\in\mathrm{cov}(e)\}\), or \(+\infty\) if there is none.

**Lemma 1 (valid bounds).** Let costs be nonnegative and let \(T\subseteq A\) cover \(U\).

1. \(c(T)\ge\max_{p\in U}\kappa(p)\).
2. Let \(P\subseteq U\) be *independent*: no \(e\in A\) covers two pairs of \(P\). Then \(c(T)\ge\sum_{p\in P}\kappa(p)\).
3. If \(P\) is built greedily in nonincreasing order of \(\kappa\), the bound in (2) is at least the bound in (1).

*Proof.* (1) \(T\) contains a coverer of each \(p\in U\), and that coverer costs at least \(\kappa(p)\); costs are nonnegative, so \(c(T)\) is at least the cost of any one member. (2) For each \(p\in P\), choose \(e_p\in T\) covering \(p\). If \(e_p=e_{p'}\) with \(p\ne p'\), that experiment would cover two pairs of \(P\), which is excluded. So the \(e_p\) are distinct, and \(c(T)\ge\sum_pc(e_p)\ge\sum_p\kappa(p)\). (3) The first pair considered has maximal \(\kappa\). It is always admitted, since the packed set is empty, and the other terms are nonnegative. \(\square\)

If some \(\kappa(p)=+\infty\), the node has no completion. The code tests independence as follows: the union of the coverage sets of the allowed coverers of \(p\) must be disjoint from the pairs already packed. This condition is symmetric, so it is exactly independence.

**Cross-check with SNG-O03.** In exact mode with the complete pool and \(A=\mathcal P\), \(\kappa(\{a,b\})\) is the cost of the cheapest experiment separating \(v_a,v_b\) within cost \(C\).

**Proposition 4.** Let \(e^\star\) be `minimum_distinguishing_experiment(system, v_a - v_b)`. In exact mode with the complete cost-\(\le C\) pool:

- if \(e^\star\) is `None`, no pool member covers \(\{a,b\}\), at any budget;
- if \(c(e^\star)\le C\), then \(\kappa(\{a,b\})=c(e^\star)\);
- if \(c(e^\star)>C\), the pair is uncoverable within the pool.

*Proof.* By SNG-O03, \(e^\star\) is a globally cheapest experiment with nonzero reading on the difference, and `None` means no experiment has one. The pool contains every experiment of cost \(\le C\). \(\square\)

`pairwise_cheapest_witnesses` reports these three cases, and the tests check the equality against the pool on seeded random systems.

### 2.2 Dominance reduction

**Lemma 2.** Say \(f\) dominates \(e\) if \(\mathrm{cov}(f)\supseteq\mathrm{cov}(e)\), \(c(f)\le c(e)\), and at least one of the following holds: the coverage containment is strict; \(c(f)<c(e)\); or the coverage and cost are equal and \(f\) has the smaller index. Then:

- dominance is a strict partial order;
- every dominated experiment is dominated by an undominated one;
- the minimum cost over panels drawn from the undominated experiments equals the minimum over the whole pool.

Experiments with empty coverage can also be removed.

*Proof.*

- **Irreflexive.** \(f=e\) satisfies none of the three alternatives.
- **Transitive.** Suppose \(g\) dominates \(f\) and \(f\) dominates \(e\). Then \(\mathrm{cov}(g)\supseteq\mathrm{cov}(e)\) and \(c(g)\le c(e)\). If \(\mathrm{cov}(g)=\mathrm{cov}(e)\), the sandwich forces all three coverages to be equal. Then either some cost inequality is strict, so \(c(g)<c(e)\), or all costs are equal and the indices decrease, so \(g<e\).
- **Existence of an undominated dominator.** In a finite strict order, every element lies below a maximal element. Hence every dominated \(e\) is dominated by an undominated \(f\).
- **Equal optimum.** Replace each dominated member of an optimal panel by such an \(f\). The result is still separating, and its cost does not increase.
- **Empty coverage.** Deleting such members never breaks separation, and costs are nonnegative. \(\square\)

### 2.3 Branch and bound

At a node with chosen set \(Q\), uncovered \(U\) and allowed \(A\), the search does the following:

1. If \(U=\varnothing\), record \(Q\) when it improves the incumbent.
2. Prune when the bound is infinite, or when \(c(Q)+\mathrm{LB}\ge\) the incumbent cost.
3. Otherwise choose \(p\in U\) with the fewest allowed coverers. Order those coverers \(e_1,\ldots,e_r\) by (cost, index). Branch \(i\) adds \(e_i\) and removes \(e_1,\ldots,e_i\) from \(A\).

The incumbent starts as the greedy panel, which is separating when the instance is feasible.

**Theorem 3 (exactness of branch and bound).** On a feasible instance with nonnegative costs, the search terminates and returns a separating panel of minimum cost.

*Proof.*

- **Node invariant.** A node \((Q,U,A)\) represents the panels \(S\) with \(Q\subseteq S\subseteq Q\cup A\). Here \(U\) is the set of pairs that \(Q\) leaves uncovered.
- **Partition.** Every separating \(S\) at the node contains some coverer of \(p\) from \(A\). Let \(e_i\) be the first one in the branching order. Then \(S\) belongs to branch \(i\) and to no other branch, so the branches partition the separating panels of the node.
- **Pruning is safe.** For any such \(S\), the set \(S\setminus Q\subseteq A\) covers \(U\). By Lemma 1, \(c(S)\ge c(Q)+\mathrm{LB}\). A pruned node therefore contains no panel strictly cheaper than the incumbent. An infinite bound means the node contains no separating panel.
- **Optimality.** By induction over the tree, some optimal panel is either the incumbent or is reached at a leaf, where it is recorded.
- **Termination.** Each branch strictly shrinks \(A\).

By Lemma 2, running the search on the undominated experiments gives the same optimum. \(\square\)

The search reports the number of explored nodes and stops with `ValueError` once a declared node budget is exceeded.

**Reference oracle.** `exhaustive_minimum_panel` scans every subset of the pool, which is limited to at most \(2^{16}\) subsets. It recomputes separation from the readings and reuses no coverage masks. The tests compare it with branch and bound on 120 seeded instances: exact and robust modes, pools of at most 10 experiments, zero costs allowed, and 49 infeasible cases (11 exact, 38 robust). All four combinations of packing and reduction are checked. The receipt adds 80 further instances.

### 2.4 Greedy heuristic

`greedy_panel` repeatedly adds the experiment that minimizes cost divided by the number of newly covered pairs. **It is a heuristic.** As established background, greedy weighted set cover is within the factor \(H_m=1+\tfrac12+\cdots+\tfrac1m\) of the optimum, where \(m\) is the universe size. We cite this and do not reprove it here.

Observed gaps are exact computations over the stated populations only:

- **Constructed instance.** The two partitions \(\{01|23\}\) and \(\{02|13\}\) cost 1 each, and an all-distinct reading costs \(19/10\). Greedy pays \(2\); the optimum is \(19/10\).
- **Seeded receipt** (80 instances). Greedy was strictly worse on 3 instances. The maximum absolute gap was \(2\) and the maximum ratio \(3/2\).
- **Graph instance at \(\varepsilon=1/8\).** Greedy pays \(5\); the optimum is \(4\).

## 3. Certified identification under bounded box noise

**Noise model.** The true candidate is \(t\in\{1,\ldots,k\}\). Each panel reading is \(y_e=r_e(v_t)+\eta_e\) with \(|\eta_e|\le\varepsilon_e\), where \(\varepsilon_e\in\mathbb Q_{>0}\) is declared. The noise is deterministic and bounded; no distribution is assumed. **Decoder:** candidate \(c\) is *consistent* if \(|y_e-r_e(v_c)|\le\varepsilon_e\) for all \(e\in S\). Experiment \(e\) *robustly separates* \(\{a,b\}\) if \(|r_e(v_a)-r_e(v_b)|>2\varepsilon_e\).

**Theorem 5 (box certification, sufficiency and necessity).** Fix a panel \(S\).

1. If every pair containing \(t\) is robustly separated by some member of \(S\), then for every admissible noise vector \(t\) is the only consistent candidate.
2. Consequently, if every pair is robustly separated, decoding is unique and correct for every true candidate and every admissible noise vector.
3. Conversely, suppose some pair \(\{a,b\}\) is robustly separated by no member of \(S\). Then the readings \(y_e=\tfrac12(r_e(v_a)+r_e(v_b))\) arise from truth \(a\) with admissible noise, and both \(a\) and \(b\) are consistent with them.

So the minimum-cost box-robust panel is exactly the cheapest panel that certifies identification for all truths under this model and decoder.

*Proof.*

- **(1).** Since \(|\eta_e|\le\varepsilon_e\), \(t\) is consistent. Let \(c\ne t\), and let \(e\in S\) robustly separate \(\{t,c\}\). Then
  \[|y_e-r_e(v_c)|\ \ge\ |r_e(v_t)-r_e(v_c)|-|\eta_e|\ >\ 2\varepsilon_e-\varepsilon_e=\varepsilon_e,\]
  so \(c\) is inconsistent.
- **(2).** Apply (1) to each \(t\).
- **(3).** Set \(\eta_e=\tfrac12(r_e(v_b)-r_e(v_a))\). Then \(|\eta_e|\le\varepsilon_e\) for every \(e\in S\), because no member separates the pair robustly. Also \(|y_e-r_e(v_a)|=|y_e-r_e(v_b)|=|\eta_e|\le\varepsilon_e\). \(\square\)

**Example 6 (equality does not certify).** Take one experiment with readings \(0,1\) and \(\varepsilon=1/2\). Then \(|0-1|=2\varepsilon\). The reading \(y=1/2\) is admissible for both truths, and the decoder returns \(\{0,1\}\). The minimum robust panel is reported infeasible.

The same happens on the graph instance at the exact threshold \(\varepsilon^\star\) of §5. There the whole pool fails to certify the pair of path placements \((0,2)\) and \((0,1)\), and the midpoint reading is ambiguous.

The tests check Theorem 5 exhaustively on 40 seeded integer instances. They try every true candidate and every noise vector on a five-point grid in each coordinate, including both endpoints \(\pm\varepsilon_e\). Part (3) is checked on every non-certified instance.

## 4. A different model: Euclidean noise on the reading vector

This is a separate criterion with a separate decoder; it is not mixed with §3. **Noise model:** \(\|\eta\|_2\le\varepsilon\) on the vector of panel readings. **Decoder:** \(c\) is consistent if \(\|y-r(v_c)\|_2^2\le\varepsilon^2\). The panel *\(\ell_2\)-separates* \(\{a,b\}\) if \(\sum_{e\in S}(r_e(v_a)-r_e(v_b))^2>4\varepsilon^2\). All comparisons are exact, using squares only.

**Theorem 7.** The statement of Theorem 5 holds verbatim with \(\ell_2\)-separation by the whole panel in place of robust separation by a member.

*Proof.* The triangle inequality gives \(\|y-r(v_c)\|\ge\|r(v_t)-r(v_c)\|-\|\eta\|>2\varepsilon-\varepsilon\). Squares of nonnegative numbers preserve order, which gives the exact criterion. The midpoint construction gives necessity: \(\|\eta\|=\tfrac12\|r(v_a)-r(v_b)\|\le\varepsilon\). \(\square\)

**Relation between the models.** The \(\ell_2\) ball of radius \(\varepsilon\) lies inside the box with \(\varepsilon_e=\varepsilon\). If one member satisfies \(|d_e|>2\varepsilon\), then \(\|d\|_2^2\ge d_e^2>4\varepsilon^2\). So a box certificate with uniform \(\varepsilon\) is also an \(\ell_2\) certificate. The converse fails.

**Example 8 (joint beats single).** Take two experiments, each with readings \(0,1\), and \(\varepsilon=3/5\).

- No single experiment robustly separates the pair, since \(1\le6/5\). The box-robust panel problem is infeasible.
- Under the ball model the pair panel gives \(1+1=2>4\cdot9/25=36/25\), so it certifies.
- Either experiment alone does not certify, and it has an ambiguous midpoint reading.
- The tests check the decoder on every point of a \(1/10\)-grid inside the ball, for both truths.

The \(\ell_2\) criterion is not additive over panel members, so it is not set cover. `minimum_cost_l2_panel` is an exhaustive search with a subset budget and makes no scalability claim.

## 5. Graph instance

**Declared population.**

- **System.** `BoundaryExperimentSystem(3, 1/2)`, with dimension \(13\). The contexts are the pendant-leaf pair (attachment cost \(2\)) and the shared neighbour (cost \(1\)). Observation costs are \(0\), and observation \(j\) is the raw volume-\(j\) coefficient.
- **Pool.** All \(48\) experiments of cost \(\le4\): 12 words times 4 volumes.
- **Candidates.** Six 3-vertex graphs:
  - the path \(0-1-2\) with terminals \((0,2)\), \((0,1)\) and \((1,2)\);
  - the triangle with terminals \((0,1)\);
  - the edge \(01\) plus an isolated vertex \(2\), with terminals \((0,1)\) and \((0,2)\).

  The three path placements have equal direct observation vectors, and so do the two edge-plus-isolated placements.
- **Independent check.** All \(48\times6=288\) pool readings equal the direct height enumeration on the actual glued graph, from `direct_observations`. That took 72 enumerations.

**Results** (exact computations over this population):

1. **Future equivalence.** Exactly one pair is future-equivalent: the path with terminals \((0,1)\) and the path with terminals \((1,2)\). The path automorphism \(0\leftrightarrow2\) carries one placement to the other, and the symmetrized states are equal. The full-family exact panel is reported infeasible and names this pair, and SNG-O03 returns `None` for it. Every other pair has a cheapest witness of cost \(0\) (the direct volume-1 reading) or \(1\) (the shared neighbour followed by the volume-1 reading).
2. **Exact panel.** On the remaining five classes, the minimum-cost exact panel has cost \(1\): the volume-1 direct reading, plus the volume-1 reading after one shared neighbour. Greedy also pays \(1\). With observation cost \(1\) per readout, the optimum is the single experiment (volume 1, word \((1)\)), at cost \(2\).
3. **Threshold.** The uniform box threshold over this pool is
   \[\varepsilon^\star=\min_{\text{pairs}}\max_{e}\tfrac12|r_e(v_a)-r_e(v_b)|=278513/2097152\approx0.1328.\]
   It is attained by the path placements \((0,2)\) and \((0,1)\). A box-robust panel exists if and only if \(\varepsilon<\varepsilon^\star\).
4. **Robust panels.**

   | \(\varepsilon\) | optimum | panel | greedy |
   |---|---|---|---|
   | \(1/64\) | 1 | volume 1 direct; volume 1 after \((1)\) | 1 |
   | \(1/16\) | 1 | volume 1 direct; volume 3 after \((1)\) | 1 |
   | \(1/8\) | 4 | volume 2 after \((0,1,1)\) | 5 |
   | \(\varepsilon^\star\) | infeasible | pair \(\{(0,2),(0,1)\}\) ambiguous | — |

   Every reported robust panel was checked through the decoder for each true candidate, at noise \(0\) and at both box corners \(\pm\varepsilon\).

## 6. Limitations

- **Truncated readings.** States are truncated at volume \(R=3\). Readings are exact for the truncated coordinates, but a panel separates the truncated states only. A pair that is future-equivalent at \(R=3\) could separate at a larger \(R\), although for automorphic placements it cannot.
- **Family-relative claims.** Optimal panels are optimal within the declared pool and family only. Nothing is claimed about larger budgets, other contexts, or other graphs.
- **No complexity guarantee.** Branch and bound is exact but worst-case exponential. Instances here explored at most a handful of nodes.
- **Greedy.** No approximation ratio is claimed beyond the cited background bound \(H_m\).
- **Noise models.** Both models are deterministic worst-case models with declared radii. No probabilistic statement is made.
- **Formal verification.** Nothing in this note is formally verified.
