# Cost-bounded robust experiment search

This note adds a maximum-margin layer beside the cheapest-witness engine of [Chapter 15](../chapters/15_operators_experiments.md). It does not change SNG-O03 or the closure certificate. The code is `src/singularity/robust_search.py`. The tests are in `tests/test_robust_search.py`, and the receipt is [robust_search.json](../../results/robust_search.json), replayed by `scripts/robust_search.py --check`. "Proved" refers to the proofs below. "Checked" refers to exact finite computations recorded in the receipt. Nothing here is formalized in Lean.

## 1. Setting

The setting is an operator system as in Section 15.2. States are columns, and the generators \(M_1,\dots,M_g\) have attachment costs \(c_i>0\). Words are chronological, \(M_w=M_{i_m}\cdots M_{i_1}\). Each observation row \(L_j\) has cost \(\gamma_j\ge0\) and a declared noise bound \(\sigma_j\in\mathbb Q_{>0}\). The experiment \((j,w)\) costs \(\gamma_j+c(w)\). Its reading on \(v\) is \(L_jM_wv+e\) with deterministic error \(|e|\le\sigma_j\).

For a difference \(d\), the **margin** of \((j,w)\) is
\[
\mu_{j,w}(d)=\frac{|L_jM_wd|}{\sigma_j}.
\]
For a candidate family \(v_1,\dots,v_k\) with \(k\ge2\), the **family margin** is \(\min_{a<b}\mu_{j,w}(v_a-v_b)\). It is the margin of the weakest pair under that single experiment.

**Interpretation.** Suppose the family margin of \((j,w)\) exceeds \(2\). Then the reading identifies the true candidate as the unique nearest one. *Proof.* Let \(r_c=L_jM_wv_c\), let \(m\) be the true candidate and let \(y=r_m+e\). For \(c\ne m\),
\[
|y-r_c|\ge|r_m-r_c|-|e|>2\sigma_j-\sigma_j=\sigma_j\ge|y-r_m|.\qquad\square
\]
This is the one-dimensional case of SNG-O07. At margin exactly \(2\), nothing is certified.

## 2. The bounded problem

Fix a budget \(C\ge0\). The bounded problem is to maximize the margin, or the family margin, over all experiments of cost at most \(C\).

**Proposition RS1 (finiteness).** Put \(c_{\min}=\min_ic_i\). Then at most \(\sum_{m\le C/c_{\min}}g^m\) words have cost at most \(C\). If some \(\gamma_j\le C\), the bounded maximum exists and is attained.

*Proof.* A word of length \(m\) costs at least \(mc_{\min}\). So every affordable word has length at most \(C/c_{\min}\), and there are at most \(g^m\) words of each length. A maximum over a finite nonempty set is attained. \(\square\)

If no \(\gamma_j\le C\), no experiment is affordable, and the search returns no experiment.

## 3. The pruning bound

Use \(\|v\|_\infty=\max_k|v_k|\), \(\|L\|_1=\sum_k|L_k|\), and \(\|M\|_\infty=\max_r\sum_k|M_{rk}|\).

**Lemma RS2.** Each of the following holds.

1. \(|Lv|\le\|L\|_1\|v\|_\infty\).
2. \(\|Mv\|_\infty\le\|M\|_\infty\|v\|_\infty\).
3. For every word \(u\), \(\|M_uv\|_\infty\le\prod_{i\in u}\|M_i\|_\infty\,\|v\|_\infty\). The product is over letters with multiplicity.

*Proof.* (1) \(|\sum_kL_kv_k|\le\sum_k|L_k||v_k|\le\|L\|_1\|v\|_\infty\). (2) For each row \(r\), \(|(Mv)_r|\le\sum_k|M_{rk}||v_k|\le\|M\|_\infty\|v\|_\infty\). (3) Apply (2) once per letter, by induction on the length of \(u\). \(\square\)

For \(b\ge0\), define
\[
\kappa(b)=\max\Bigl\{\prod_{i\in u}\|M_i\|_\infty : c(u)\le b\Bigr\}.
\]
This is a maximum over a finite set by RS1. It satisfies \(\kappa(b)\ge1\) because the empty word is allowed.

**Proposition RS3 (exact computation of \(\kappa\)).** Let \(S\) be the finite set of cost sums \(c(u)\le C\). Put \(K(0)=1\) and, for \(t\in S\setminus\{0\}\),
\[
K(t)=\max_{i:\,t-c_i\in S}K(t-c_i)\|M_i\|_\infty.
\]
Then \(K(t)\) is the largest product over words of cost exactly \(t\), and \(\kappa(b)=\max_{t\in S,\,t\le b}K(t)\).

*Proof.* Induct on \(t\) in increasing order. A nonempty word of cost \(t\) is a prefix \(u'\) followed by a last letter \(i\). The prefix has cost \(t-c_i\), which lies in \(S\), and the product is \(\pi(u')\|M_i\|_\infty\). Multiplication by \(\|M_i\|_\infty\ge0\) is monotone, so the largest such product is \(K(t-c_i)\|M_i\|_\infty\). Taking the maximum over \(i\) gives \(K(t)\). Every word of cost at most \(b\) has its cost in \(S\), which gives the last statement. \(\square\)

**Theorem RS4 (subtree bound).** Let \(w\) be a word, and let \(J_w=\{j:\gamma_j+c(w)\le C\}\). Every affordable experiment \((j,w\cdot u)\) satisfies
\[
\mu_{j,w\cdot u}(d)\ \le\ \frac{\|L_j\|_1}{\sigma_j}\,\kappa\bigl(C-c(w)-\gamma_j\bigr)\,\|M_wd\|_\infty .
\]
For a family with pair differences \(d_p\), the family margin of \((j,w\cdot u)\) is at most the same expression with \(\|M_wd\|_\infty\) replaced by \(\min_p\|M_wd_p\|_\infty\). Consequently the node bound
\[
\beta(w)=\min_p\|M_wd_p\|_\infty\cdot\max_{j\in J_w}\frac{\|L_j\|_1}{\sigma_j}\kappa\bigl(C-c(w)-\gamma_j\bigr)
\]
bounds the margin of every affordable experiment whose word extends \(w\), including \(w\) itself.

*Proof.* We have \(M_{w\cdot u}=M_uM_w\). Affordability means \(c(u)\le C-c(w)-\gamma_j\), which forces \(j\in J_w\). By RS2(1), then RS2(3), and then the definition of \(\kappa\),
\[
|L_jM_uM_wd|\le\|L_j\|_1\|M_uM_wd\|_\infty\le\|L_j\|_1\kappa\bigl(C-c(w)-\gamma_j\bigr)\|M_wd\|_\infty .
\]
Divide by \(\sigma_j\) to get the first claim. For a family, the minimum over pairs is at most every per-pair term. It is therefore at most the minimum of the per-pair bounds, and these share the same nonnegative factor. Maximizing over \(j\in J_w\) gives \(\beta(w)\). \(\square\)

## 4. Branch-and-bound and its exactness

The algorithm works as follows.

- **Nodes.** The nodes are words. A child is formed by appending a letter on the state side: the child of \(w\) by \(i\) is \(w\cdot i\), with \(M_{w\cdot i}d=M_iM_wd\).
- **Children.** The child \(w\cdot i\) is generated only when \(c(w)+c_i+\min_{j:\gamma_j\le C}\gamma_j\le C\).
- **Processing.** Nodes are popped in decreasing order of \(\beta\). A node is pruned, and not expanded, when \(\beta(w)\) is at most the incumbent margin. A child is also pruned at generation under the same test. Otherwise every experiment \((j,w)\) with \(j\in J_w\) is evaluated, the incumbent is replaced on a strict improvement, and the children are pushed.

**Theorem RS5 (exactness).** Branch-and-bound terminates. It returns an affordable experiment whose margin equals the maximum over all affordable experiments. The same holds for the family margin.

*Proof.* There are finitely many affordable words by RS1, and no word is generated twice, so the algorithm terminates. The incumbent is always the margin of an evaluated affordable experiment, so the returned value is at most the optimum.

For the converse, let \((j,u)\) be affordable. Every chronological prefix \(w\) of \(u\) satisfies \(c(w)+\gamma_j\le c(u)+\gamma_j\le C\). So the child-generation test never excludes a prefix of \(u\). Follow the prefixes of \(u\) from the empty word. There are two cases.

- If none of them is pruned, then \(u\) is popped and evaluated. Since \(j\in J_u\), its margin is at most the final incumbent.
- If some prefix \(w\) is pruned, then \(\beta(w)\) was at most the incumbent at that moment. The incumbent never decreases, so \(\beta(w)\) is at most the final incumbent. By RS4, \(\mu_{j,u}\le\beta(w)\).

In both cases no affordable experiment exceeds the returned margin. \(\square\)

**Ties.** The exhaustive reference keeps the first maximizer in its enumeration order. Branch-and-bound keeps the first strict improvement in its pop order. The two values are always equal, but the words can differ on ties.

**Independence of the reference.** The exhaustive oracle grows rows by *prepending*, using \(L_jM_{(i,w)}=(L_jM_w)M_i\). Branch-and-bound grows states by appending. The test oracle uses neither: it enumerates words with `itertools.product` and multiplies explicit matrices.

## 5. Counterexamples and separations

**Proposition RS6 (amplification; SNG-O04).** Take \(n=1\), \(L=(1)\), \(M=(2)\), unit cost, \(\sigma=1\) and \(d=1\). Then:

- the bounded optimum at budget \(C\) is \(2^{\lfloor C\rfloor}\), attained by the word \(0^{\lfloor C\rfloor}\);
- there is no unrestricted optimum;
- the closure basis is the empty word alone, and the cheapest witness is the empty word with margin \(1\).

*Proof.* The word \(0^m\) reads \(2^m\) and costs \(m\), and these are all the words. So the bounded optimum is the largest affordable \(m\), namely \(\lfloor C\rfloor\). Margins are unbounded, so no word maximizes over all budgets. The row \(LM=(2)\) is a multiple of \(L\), which has cost \(0\). The closure therefore discards it and keeps only \(L\). \(\square\)

*Checked:* budgets \(0\) to \(10\) and \(C=7/2\) in the tests, and \(0\) to \(8\) in the receipt.

**Proposition RS7 (finite supremum, not attained).** Take
\[
M=\begin{pmatrix}1&1\\0&1/2\end{pmatrix},\qquad L=(1,0),\qquad d=(0,1)^{\mathsf T},
\]
with unit cost and \(\sigma=1\). Then \(LM^kd=2-2^{1-k}\) for every \(k\ge0\). The supremum of the margins is \(2\), and no word attains it. The bounded optimum at an integer budget \(C\) is \(2-2^{1-C}\).

*Proof.* Write \(M^kd=(x_k,y_k)^{\mathsf T}\). We show by induction that \(x_k=2-2^{1-k}\) and \(y_k=2^{-k}\). For \(k=0\), \(x_0=0=2-2\) and \(y_0=1\). For the step,
\[
x_{k+1}=x_k+y_k=2-2^{1-k}+2^{-k}=2-2^{-k},\qquad y_{k+1}=y_k/2=2^{-(k+1)} .
\]
The words are exactly \(0^k\), and their readings \(2-2^{1-k}\) increase strictly with limit \(2\), never reaching it. \(\square\)

*Checked:* \(k\le20\) in the tests. Here \(\|M\|_\infty=2\), so \(\kappa(b)=2^{\lfloor b\rfloor}\) although every margin is below \(2\). This example shows how loose the \(\infty\)-norm bound can be.

**Proposition RS8 (dependence pruning destroys margin optimality).** Take \(n=2\), \(L=(1,0)\),
\[
M_0=\begin{pmatrix}0&1\\1&0\end{pmatrix},\qquad M_1=\begin{pmatrix}1&0\\0&3\end{pmatrix},
\]
unit costs, \(\sigma=1\) and \(d=(0,1)^{\mathsf T}\). Then:

- the closure basis consists of the words \(()\) and \((0)\), with rows \((1,0)\) and \((0,1)\);
- the cheapest witness is \((0,(0))\), with cost \(1\) and margin \(1\);
- the bounded optimum at budget \(2\) is \((0,(1,0))\), with row \((0,3)\) and margin \(3\).

That optimal row equals \(3\,LM_0\), so it depends on a cheaper retained row and the closure discards it.

*Proof.* We have \(LM_0=(0,1)\) and \(LM_1=(1,0)\). The rank is \(2\) after the word \((0)\), and the extension \(LM_1\) is dependent on \(L\). The row \(L\) reads \(0\) on \(d\), so the first basis row nonzero on \(d\) is \(LM_0\), with reading \(1\). The affordable words at budget \(2\) and their rows are:

| Word | Row | Reading |
|---|---|---|
| \(()\) | \((1,0)\) | \(0\) |
| \((0)\) | \((0,1)\) | \(1\) |
| \((1)\) | \((1,0)\) | \(0\) |
| \((0,0)\) | \((1,0)\) | \(0\) |
| \((0,1)\) | \(LM_1M_0=(0,1)\) | \(1\) |
| \((1,0)\) | \(LM_0M_1=(0,3)\) | \(3\) |
| \((1,1)\) | \((1,0)\) | \(0\) |

The largest reading is \(3\), attained only by \((1,0)\). \(\square\)

The amplification example RS6 is the one-dimensional instance of the same phenomenon.

**Corollary RS9 (the two problems separate).** In the two-generator system of RS8, the cheapest witness \((0)\) and the bounded maximum-margin experiment \((1,0)\) at budget \(2\) are different words. The table also shows that word order matters: \((0,1)\) reads only \(1\). \(\square\)

## 6. Graph data (checked)

The data use the path fixture of `tests/test_graph_experiments.py`:

- `BoundaryExperimentSystem(1, 1/2)`, of dimension \(3\), with contexts (pendant leaf pair, shared neighbour);
- attachment costs \((2,1)\) and observation costs \(0\);
- \(d=\) compile\((P_3,(0,2))-\) compile\((P_3,(0,1))=(0,-1/4,1/4)\);
- \(\sigma=1\) on both observations.

The cheapest witness is observation \(1\) with word \((1)\), at cost \(1\).

| Budget | Optimum | Word (B&B) | B&B nodes | Pruned | Exhaustive nodes |
|---:|---:|---|---:|---:|---:|
| 1 | 1/8 | (1) | 2 | 0 | 4 |
| 2 | 3/16 | (1,1) | 4 | 0 | 8 |
| 3 | 7/32 | (1,1,1) | 7 | 0 | 14 |
| 4 | 15/64 | (1,1,1,1) | 12 | 0 | 24 |
| 5 | 31/128 | (1,1,1,1,1) | 20 | 0 | 40 |
| 6 | 63/256 | (1,1,1,1,1,1) | 33 | 0 | 66 |

In every row the optimum is read by observation \(1\), and the exhaustive search returns the same word. Branch-and-bound nodes are words. Exhaustive nodes are (observation, word) pairs.

On this population the values equal \(1/4-2^{-(C+2)}\). That pattern is checked only for \(C\le6\); it is not proved. No subtree is pruned here, because both generators have \(\|M_i\|_\infty>1\) and the bound never falls below the incumbent. The whole receipt runs in well under a second.

## 7. Limitations

- The \(\infty\)-norm bound is valid but can be very loose, as RS7 and the graph data show. Pruning is then ineffective, and the search degenerates to enumeration within the work budget. A sharper bound, such as one from an invariant cone or the closure quotient, is not developed here.
- Each problem solved here uses one experiment at a time. Nothing optimizes a **shared panel** of several experiments for several pairs, or combines readings across experiments.
- The noise model is deterministic, additive and bounded, with one bound per observation row. No statistical model is assumed.
- All results are for a fixed finite budget. RS6 shows that no unrestricted statement is available in general.
- A budget refusal, which raises `ValueError` when `max_nodes` is exceeded, is not a mathematical result.
