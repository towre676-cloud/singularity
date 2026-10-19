# 15. Context operators, cheapest experiments and periodic sectors

This chapter adds an experimental layer to the boundary machinery of Chapter 10. A two-terminal graph state is changed by attaching declared contexts and is read through its local coefficients. The questions are which states can ever be told apart, by which experiment, at what cost, and how much state an observer must keep. Three ingredients are standard: linear observability, minimal realization of weighted automata, and the invariant-subspace computation behind them. The graph-specific parts are new to this project. They are the context compiler and its correctness conditions, the experiment language with costs, independently replayable certificates that tie the retained rows to actual experiment words, the cost-filtered pruning theorem, the top-volume corank bound and the periodic cutoff. The last section integrates the October 2026 edge-factor supplement.

Throughout, \(\mathbb Q\) is the field of rationals and every computation is exact. "Proved" refers to the proofs written here. "Checked" refers to an exact finite computation with a declared population and budget, retained in `results/operator_experiments.json` and replayed by `scripts/operator_experiments.py --check`. None of the new statements is formalized in Lean unless Section 15.11 says so.

## 15.1 Background and what is new

For a linear system with state \(v\in K^n\), generators \(M_i\) and output rows \(L_j\), the set of states with identical output under every input word is an invariant subspace, and the quotient by it is the minimal linear realization. Kalman (1963) developed this for linear dynamical systems. Schützenberger (1961) introduced the weighted-automaton form of rational series, and Carlyle and Paz (1971) proved the Hankel-rank minimal realization for such automata. Berstel and Reutenauer's monograph gives a modern account of noncommutative rational series and their minimization. These are the established background of Sections 15.2 and 15.3. We do not claim them.

The bibliographic data of these four sources agree across independent library and index records. These include the MIT *Information and Control* author index, the Cambridge copyright record of the Berstel–Reutenauer volume, and reference lists citing Kalman and Carlyle–Paz. In this session the publisher pages, Crossref and author-hosted copies were unreachable through the network policy. Their primary-record check, and the DOIs other than Berstel–Reutenauer's catalogue DOI, remain open.

The project-specific content is as follows:

- a compiler from symmetric two-terminal graph contexts to exact rational operators on truncated boundary kernels, with the conditions under which it is correct for every word length (SNG-O05);
- certificates whose retained rows are actual experiments with their words and costs, replayable without rediscovery, with an exactly typed in-memory verifier and a strict portable format (Section 15.4);
- the cost-filtered pruning theorem, which makes the first retained row nonzero on a difference a globally cheapest distinguishing experiment (SNG-O03), together with the counterexample showing that it does not maximize signal (SNG-O04);
- the top-volume corank bound for graph contexts (SNG-O06) and the exact evidence at budgets four and seven;
- the exact robustness statement for finite candidate families (SNG-O07);
- the periodic residue sector with a palindromic numerator and a sufficient cutoff (SNG-O08, SNG-O09).

## 15.2 Operator systems, experiments and word order

An **operator system** over \(\mathbb Q\) consists of the following data:

- the dimension \(n\ge0\) of the formal state space \(\mathbb Q^n\), whose states are columns;
- generators \(M_1,\ldots,M_g\in\mathbb Q^{n\times n}\), with \(g\ge0\);
- observation rows \(L_1,\ldots,L_o\in\mathbb Q^{1\times n}\), with \(o\ge0\);
- attachment costs \(c_i>0\) and observation costs \(\gamma_j\ge0\).

A **word** is a finite sequence \(w=(i_1,\ldots,i_m)\) of generator indices, read chronologically: \(i_1\) is applied first. It acts on states by
\[
M_w=M_{i_m}\cdots M_{i_1},\qquad v\mapsto M_wv.
\]
The **experiment** \((j,w)\) is the row \(L_jM_w\). Its cost is \(\gamma_j+\sum_{k}c_{i_k}\), and its reading on \(v\) is \(L_jM_wv\). Right multiplication of an experiment row by \(M_i\) gives \(L_jM_wM_i=L_jM_{(i,w)}\), the experiment whose word has \(i\) **prepended**: the new attachment happens first. This convention matters only for noncommuting generators. The test suite checks it on
\[
M_0=\begin{pmatrix}1&1\\0&1\end{pmatrix},\qquad
M_1=\begin{pmatrix}1&0\\1&1\end{pmatrix},\qquad L=(1,0).
\]
Here \(M_1M_0(0,1)^T=(1,2)^T\ne(1,1)^T=M_0M_1(0,1)^T\), and the closure retains the words \(()\) and \((0)\). Parallel graph attachments commute, so graph data alone cannot detect an order error.

The **observation space** \(\mathcal O\) is the span of all experiment rows. Two states are **future-equivalent** if every experiment reads the same value on them.

## 15.3 Closure, quotient and cheapest experiments

**Theorem SNG-O01 (closure certificate).** Let \(B\in\mathbb Q^{r\times n}\) have rows \(b_1,\ldots,b_r\), each equal to an actual experiment \(L_{j_k}M_{w_k}\). Suppose there are matrices \(A\in\mathbb Q^{o\times r}\) and \(T_i\in\mathbb Q^{r\times r}\) with
\[
L=AB,\qquad BM_i=T_iB\quad(1\le i\le g),
\]
where \(L\) stacks the observation rows. Then \(\operatorname{row}B=\mathcal O\). For every word \(w\), the experiment rows satisfy \(LM_w=AT_wB\), where \(T_w=T_{i_1}T_{i_2}\cdots T_{i_m}\).

*Proof.* Induct on \(m=|w|\). The case \(m=0\) is \(L=AB\). If \(LM_w=AT_wB\), then
\[
LM_{(i,w)}=LM_wM_i=AT_wBM_i=AT_wT_iB=AT_{(i,w)}B,
\]
so every experiment row lies in \(\operatorname{row}B\). Conversely, each \(b_k\) is itself an experiment row, so \(\operatorname{row}B\subseteq\mathcal O\). \(\square\)

The identities say that the retained space contains every future observation. The words say that it contains nothing else. Neither half needs a horizon or a bound on word length. Gaussian-elimination residuals are useful internally, but they are generally not experiment rows, so a certificate built from them would not prove reachability. The implementation therefore keeps original experiment rows as \(B\).

**Theorem SNG-O02 (invariant kernel, quotient and linear minimality).** Under SNG-O01, put \(N=\ker B\). Then:

1. \(M_iN\subseteq N\) for every \(i\);
2. every experiment vanishes on \(N\), and two states are future-equivalent if and only if their difference lies in \(N\);
3. the quotient state \(y=Bv\) evolves by \(y\mapsto T_iy\) and is read by \(Lv=Ay\);
4. if \(\phi:\mathbb Q^n\to W\) is linear and every experiment is constant on the fibres of \(\phi\), then \(\ker\phi\subseteq N\). Consequently \(\operatorname{rank}\phi\ge\operatorname{rank}B\).

*Proof.* (1) If \(Bv=0\), then \(BM_iv=T_iBv=0\). (2) By SNG-O01 every experiment row is a combination of rows of \(B\), so it vanishes on \(N\). Conversely, if \(d\notin N\), some row \(b_k\) of \(B\) is nonzero on \(d\), and \(b_k\) is an experiment. (3) \(BM_iv=T_iBv\) and \(Lv=ABv\). (4) If \(\phi(d)=0\), then \(d\) and \(0\) lie in one fibre, so every experiment, and in particular every \(b_k\), vanishes on \(d\); hence \(d\in N\). Then \(\operatorname{rank}\phi=n-\dim\ker\phi\ge n-\dim N=\operatorname{rank}B\). \(\square\)

Part (4) is minimality among **linear** compressions of the **full declared formal state space**. It says nothing about nonlinear encodings. It also says nothing about the smaller set of states that graphs actually realize: a family occupying an affine subspace or a semialgebraic subset can need fewer coordinates. Section 15.12 lists this as open.

**Theorem SNG-O03 (cost-filtered pruning and cheapest witnesses).** Assume the following:

- the rows of \(B\) are actual experiments with costs \(\beta_1\le\cdots\le\beta_r\);
- \(L=AB\) and \(BM_i=T_iB\);
- \(A_{jk}\ne0\) implies \(\beta_k\le\gamma_j\);
- \((T_i)_{ak}\ne0\) implies \(\beta_k\le\beta_a+c_i\).

Then for every real \(C\), every experiment of cost at most \(C\) lies in the span of the rows \(b_k\) with \(\beta_k\le C\). Hence, for any difference \(d\in\mathbb Q^n\):

- if some experiment is nonzero on \(d\), then the first row \(b_k\) with \(b_kd\ne0\) is an experiment of globally minimum cost among all experiments nonzero on \(d\), within the declared generator language;
- if no row of \(B\) is nonzero on \(d\), no experiment distinguishes the two states.

*Proof.* Induct on word length. For the empty word, \(L_j=\sum_kA_{jk}b_k\), and every \(k\) used has \(\beta_k\le\gamma_j\). Suppose \(L_jM_w=\sum_a\lambda_ab_a\) with \(\beta_a\le\gamma_j+c(w)\) whenever \(\lambda_a\ne0\). Then
\[
L_jM_{(i,w)}=\sum_a\lambda_ab_aM_i=\sum_a\sum_k\lambda_a(T_i)_{ak}b_k ,
\]
and every \(k\) with a nonzero contribution has \(\beta_k\le\beta_a+c_i\le\gamma_j+c(w)+c_i\), the cost of \((j,(i,w))\). Now let \(e\) be an experiment of cost \(C\) with \(ed\ne0\). Since \(e\) lies in the span of the rows of cost at most \(C\), one of those rows is nonzero on \(d\). The first row nonzero on \(d\) therefore costs at most \(C\), and it is itself an experiment. \(\square\)

The algorithm produces such a certificate. It processes candidate experiments in nondecreasing cost from a priority queue, keeps a candidate only if it is independent of the rows already kept, and extends each kept row by every generator. A discarded candidate lies in the span of kept rows of cost at most its own. Right multiplication preserves that relation and adds the same positive cost \(c_i\) to every term, so the extensions of discarded rows are never needed. This is where strict positivity of attachment costs is used. Observation costs may be zero. The verifier checks the cost conditions on every nonzero coefficient of \(A\) and \(T_i\).

**Proposition SNG-O04 (cheapest is not strongest).** Take \(n=1\), a single observation \(L=(1)\) and a single generator \(M=(2)\). Then:

- the closure has rank one and the cheapest witness for \(d=1\) is the direct reading, with cost \(0\) and signal \(1\);
- the experiment with word \((0,0,0)\) reads \(8\);
- dependence pruning discards every extension, although the extensions amplify the discrepancy without bound.

Minimum cost, maximum margin under a cost budget, and minimum-cost shared panels for several candidate pairs are therefore three different optimization problems. SNG-O03 solves only the first.

## 15.4 Certificates and their contracts

A closure certificate contains the experiments of \(B\) (observation index, word, row and cost), the matrices \(A\) and \(T_i\), the reduced-row-echelon pivots of \(B\) and the canonical kernel basis of \(N\).

The verifier recomputes every listed experiment from its word, rechecks independence, the pivots and the kernel, both identity families, the invariance of \(N\) and the cost filtration. It never reruns the closure search. It is exact in two senses. Arithmetic is rational, and types are checked: every stored number must be a `Fraction`, every index and pivot an `int` that is not a `bool`, and every container a tuple of the stated size. Python equality identifies `Fraction(0)`, `0`, `0.0` and `False`, so a value check alone would accept a forged cost of `0.0`. The portable JSON format `singularity.operator-closure/1` encodes rationals as reduced pairs `[numerator, denominator]` and replays with resource limits. In memory and on disk the two contracts agree.

A rank-zero closure is legitimate: the zero observation, or no observations at all. Its certificate has no rows, and reconstruction must return the zero vector of the ambient dimension. Earlier checkpoint code lost that dimension when reconstructing from an empty matrix and rejected such certificates. The reconstruction now takes the dimension explicitly. The test suite covers dimension zero, rank zero, and empty observation and generator families.

**Exception contract.** Non-exact public numbers (`bool`, `float`, `str`) raise `TypeError`. Valid types with invalid values or shapes raise `ValueError`. Portable replay converts every defect to `ValueError`.

## 15.5 The graph context compiler

A **context** is a simple graph \(C\) with ordered terminals \((a,b)\), subject to three conditions:

- \(ab\notin E(C)\);
- there is a graph automorphism \(\sigma\) of \(C\) with \(\sigma(a)=b\) and \(\sigma(b)=a\), and the implementation checks the actual permutation;
- on attachment the interior of \(C\) is copied freshly, disjoint from everything else, and the terminals of \(C\) are identified with those of the current graph.

A **base block** is any two-terminal simple graph, symmetric or not, and it may contain its terminal edge. Write \(K_G(s,t)\in\mathbb Z[q][x]\) for the interior kernel of \(G\) at terminal heights \((s,t)\). It sums \(x^{\text{interior volume}}q^{\text{energy}}\) over nonnegative interior heights. Fix a budget \(R\) and \(q\in\mathbb Q\cap(0,1)\). The state coordinates are indexed by orbits \(o=\{s\le t\}\) with \(s+t\le R\) and volumes \(s+t\le v\le R\):
\[
Y_{o}[v]=[x^v]\,x^{s+t}K_G^+(o),\qquad
K_G^+(o)=\begin{cases}K_G(s,t)+K_G(t,s)&s<t,\\ K_G(s,s)&s=t.\end{cases}
\]
These are raw labeled population counts. Nothing is averaged, symmetric coordinates are not identified, and no normalization changes as the graph grows.

**Theorem SNG-O05 (compiler correctness).** Under the conditions above, attaching \(C\) maps the state of \(G\) to the state of the glued graph by
\[
Y'_o[v]=\sum_{j=0}^{v-s-t}[x^j]K_C(o)\,Y_o[v-j],
\]
and the local coefficient at volume \(v\le R\) is \(\sum_oY_o[v]\). The glued graph is again a simple two-terminal graph with the same terminals. Hence the formula holds for every word of attachments of every length, with no truncation error.

*Proof.* Every edge of \(C\) has an interior endpoint, because \(ab\notin E(C)\). The fresh copy makes the interiors of \(G\) and \(C\) disjoint. So for fixed terminal heights the energy splits as \(E_G+E_C\), the volume as \(s+t\) plus the two interior volumes, and the interior height choices are independent. The local series of the glued graph is therefore \(\sum_{(s,t)}x^{s+t}K_G(s,t)K_C(s,t)\) over ordered terminal heights. Since \(\sigma\) swaps the terminals, \(K_C(s,t)=K_C(t,s)\). Grouping \((s,t)\) and \((t,s)\) gives \(\sum_ox^{s+t}K_G^+(o)K_C(o)\). Extracting \([x^v]\) gives the update and the readout. Interior volumes are nonnegative, so \(Y'_o[v]\) uses only \(Y_o[v']\) with \(v'\le v\). The truncated coordinates are therefore closed under the update, and the budget never has to grow with word length. No terminal edge is added and the interior is fresh, so simplicity and the terminal labels persist. \(\square\)

The implementation `BoundaryExperimentSystem` compiles a declared list of contexts at given \(R\) and \(q\). The checked evidence is listed here; all of it is in the retained receipt.

- **Standard contexts.** The pendant-leaf pair attaches one new leaf at each terminal. The shared neighbour attaches one new vertex adjacent to both.
- **Budget four (SNG-E009).** At \(R=4\), \(q=1/2\) the state dimension is \(22\) and the closure has full rank \(22\). The number of retained rows of word length at most \(k\) is
  \[
  5,\ 11,\ 15,\ 17,\ 18,\ 19,\ 20,\ 21,\ 22\qquad(k=0,\ldots,8).
  \]
  By SNG-O03 with unit attachment costs, this is the rank of all experiments of length at most \(k\). The first four values are confirmed by an independent rank computation over all words. The portable certificate is retained, replays without discovery, and equals a fresh discovery byte for byte as JSON.
- **Budget seven (SNG-E010).** At \(R=7\) the dimension is \(70\) and the rank is \(69\). The kernel is spanned by
  \[
  e_{((3,4),7)}-e_{((0,5),7)} .
  \]
  Both generators multiply it by \(q^{25}=2^{-25}\), and every output annihilates it. This is a **formal** interface ambiguity in the declared coordinate space. No pair of graphs realizing this difference is asserted.
- **Path fixture (SNG-E011).** Take the path \(0-1-2\) at \(R=1\), \(q=1/2\), with terminals at the two endpoints or at an endpoint and the middle vertex. Both direct observation vectors are \((1,5/4)\). At volume one, by direct height enumeration on the glued graphs, the pendant-leaf pair gives \(7/4\) and \(15/8\) and the shared neighbour gives \(1\) and \(9/8\). With costs \(2\) and \(1\), the certified cheapest witness is the shared neighbour, with cost \(1\) and discrepancy \(-1/8\). All fifteen words of length at most three were checked against direct enumeration at \(R=3\) for both placements.

**Proposition SNG-O06 (top-volume corank bound).** Let every context in the language satisfy the conditions above, and let \(d_C\) be the number of interior neighbours of a terminal of \(C\), which is the same for both terminals. For each orbit \(o=(s,t)\) with \(s+t\le R\), the coordinate vector \(e_{(o,R)}\) is an eigenvector of every compiled operator, with eigenvalue \(q^{d_C(s^2+t^2)}\), and its readout is the volume-\(R\) unit. Consequently, if orbits \(o\ne o'\) with \(s+t,s'+t'\le R\) have \(s^2+t^2=s'^2+t'^2\), then \(e_{(o,R)}-e_{(o',R)}\) is invisible, and
\[
\operatorname{corank}\ \ge\ \sum_{\text{classes}}\bigl(\#\{o:\ s+t\le R,\ s^2+t^2=c\}-1\bigr).
\]

*Proof.* By SNG-O05, the column \((o,R)\) of the operator has nonzero entries only at \((o,v)\) with \(v\ge R\), so only at \((o,R)\). The entry is the interior-volume-zero kernel coefficient \([x^0]K_C(o)\). With every interior height zero, only the terminal–interior edges carry energy, which totals \(d_Cs^2+d_Ct^2\). The readout of the coordinate \((o,R)\) is the coefficient at volume \(R\). Differences within one class are therefore common eigenvectors with zero readout. Differences from distinct classes have disjoint supports, so they are independent. \(\square\)

The bound is zero for \(R\le6\). It is one for \(R=7,8,9\), from \(0^2+5^2=3^2+4^2\), and two at \(R=10\), adding \(1^2+7^2=5^2+5^2\). It equals the computed corank at \(R=4\) and \(R=7\). Whether it is sharp for larger budgets is open. Fixed-budget closure is a statement about a finite truncation: it does not prove that an untruncated generating function is rational or that the visible rank stabilizes as \(R\) grows.

## 15.6 Exact robustness for finite candidate families

Experiments that return polynomial curves in \(q\) are compared in the integral metric of \(L^2([a,b])\). Its Gram matrix on monomials is \(G_{ij}=(b^{i+j+1}-a^{i+j+1})/(i+j+1)\). The coefficient dot product is a different quantity. For the path discrepancy \(\Delta(q)=-q(1-q)^2\), with coefficients \((0,-1,2,-1)\),
\[
\int_0^1\Delta(q)^2\,dq=\frac1{105},\qquad (0,-1,2,-1)\cdot(0,-1,2,-1)=6 .
\]
In the monic orthogonal basis on \([0,1]\), the coordinates of \(\Delta\) are \((-1/12,1/10,1/2,-1)\) with squared norms \((1,1/12,1/180,1/2800)\), and Parseval returns \(1/105\). All Gram matrices are checked positive definite by exact \(LDL^{\mathsf T}\).

**Proposition SNG-O07 (certified nearest-candidate identification).** Suppose:

- the candidate family is a finite set \(\mathcal F\) of observation vectors with minimum pairwise distance \(\delta\) in a declared positive definite metric;
- the true vector \(m\) lies in \(\mathcal F\);
- the observation is \(y=m+e\) with \(\|e\|\le\varepsilon\).

If \(2\varepsilon<\delta\), then \(m\) is the unique nearest candidate to \(y\).

*Proof.* For \(c\in\mathcal F\setminus\{m\}\),
\[
\|y-c\|\ \ge\ \|m-c\|-\|e\|\ \ge\ \delta-\varepsilon\ >\ \varepsilon\ \ge\ \|y-m\| .\qquad\square
\]

At \(2\varepsilon=\delta\) the observation can be equidistant from two candidates, so equality certifies nothing. The noise model is deterministic and bounded. Nothing outside the declared family is identified. Whole-curve separation is not pointwise separation: \((-1/2)+q\) has positive \(L^2\) norm on \([0,1]\) but vanishes at \(q=1/2\). A single specialized interface value cannot reconstruct a parameter polynomial. The finite-pool ranking scores \(\delta^2/(\text{cost}\cdot\text{noise}^2)\) over an explicit pool. It is not a search over attachment words.

## 15.7 The periodic sector

Fix a graph on \(n\) labeled vertices (isolated vertices and disconnected graphs allowed), a modulus \(M\ge1\), and integer exponents \(a_e\), where zero and negative values are allowed. Put \(t_e=\zeta_M^{a_e}\) in \(\mathbb Z[t]/\Phi_M(t)\) and
\[
F(x)=\sum_{h\in\mathbb N^n}x^{|h|}\prod_{uv\in E}t_{uv}^{(h_u-h_v)^2}.
\]

**Theorem SNG-O08 (residue numerator).** With \(K=n(M-1)\),
\[
F(x)=\frac{P(x)}{(1-x^M)^n},\qquad
P(x)=\sum_{\rho\in\{0,\ldots,M-1\}^n}x^{|\rho|}\prod_{uv}t_{uv}^{(\rho_u-\rho_v)^2},\qquad \deg P\le K .
\]

*Proof.* Write \(h=\rho+Mb\) uniquely with \(0\le\rho_v<M\) and \(b\in\mathbb N^n\). Then \((h_u-h_v)^2\equiv(\rho_u-\rho_v)^2\pmod M\), and \(t_e^M=1\), so each weight depends only on \(\rho\). Summing \(x^{M|b|}\) over \(b\) gives \((1-x^M)^{-n}\). \(\square\)

**Theorem SNG-O09 (palindrome and sufficient cutoff).** Then \(P_k=P_{K-k}\) for every \(k\). Let two models have the same \(n\) and \(M\). If their series agree at every volume up to \(\lfloor K/2\rfloor\), they agree at every volume.

*Proof.* The complement \(\rho\mapsto(M-1)\mathbf 1-\rho\) negates every difference \(\rho_u-\rho_v\), so it preserves every squared difference. It sends \(|\rho|\) to \(K-|\rho|\). It is a bijection of the residue box, so \(P_k=P_{K-k}\). Since \(P=F\cdot(1-x^M)^n\) and the factor is \(1+O(x^M)\), \(P_k\) is determined by \(F_0,\ldots,F_k\). Agreement through \(\lfloor K/2\rfloor\) fixes \(P_0,\ldots,P_{\lfloor K/2\rfloor}\). The palindrome fixes the remaining coefficients, and \(P\) determines \(F\). \(\square\)

This is a sufficient cutoff, not a sharpness claim. The argument uses squared edge differences only. A unary or vertex weight is not preserved by complementation, and no such extension is claimed. The following were checked:

- **A certified equal pair (SNG-E012).** At \(n=3\), \(M=2\), with every exponent one, the path \(0-1-2\) and the edge \(01\) with isolated vertex \(2\) have the same numerator \((1,-1,-1,1)\). The cutoff is \(1\), so their complete series are equal. Direct enumeration confirms agreement through volume \(14\). At \(M=3\) the same pair separates at volume one, with \(F_1=2\zeta+\zeta^2\) versus \(2\zeta+1\).
- **Exhaustive population.** Every graph on \(n\le3\) labeled vertices, every \(M\in\{1,2,3,4\}\) and every exponent assignment from \(\{-1,0,1,2\}\): \(524\) models. The residue identity was checked against direct height enumeration through volume \(K+2M+1\), the palindrome on every numerator, and the cutoff theorem on every pair with equal \((n,M)\).

**Theorem SNG-O17 (period reduction).** For an edge exponent \(a\), let \(p_a\) be the least \(p\ge1\) with \(M\mid 2ap\) and \(M\mid ap^2\), and put \(M^*=\operatorname{lcm}_ep_{a_e}\), which divides \(M\). Then
\[
F=\frac{P^*(x)}{(1-x^{M^*})^n},\qquad \deg P^*\le n(M^*-1),\qquad P^*_k=P^*_{n(M^*-1)-k}.
\]
For two models with the same \(n\) and \(M\), let \(L\) be the lcm of their reduced moduli. Agreement of the two series through \(\lfloor n(L-1)/2\rfloor\) proves that they are equal.

*Proof.* We have \(a\bigl((d+p)^2-d^2\bigr)=a(2pd+p^2)\equiv0\pmod M\) for every \(d\) exactly when \(M\mid 2ap\) and \(M\mid ap^2\). So every edge weight depends only on \(d \bmod M^*\). The proofs of SNG-O08 and SNG-O09 then apply verbatim with \(M^*\) in place of \(M\). Each model's weights are periodic modulo \(L\), so both series have the form \(P/(1-x^L)^n\). \(\square\)

For \(M=4\) with odd exponents, \(M^*=2\). The cutoff drops from \(\lfloor 3n/2\rfloor\) to \(\lfloor n/2\rfloor\), and this reduced cutoff is attained: across all graphs on \(n\le4\) vertices with exponents from a declared set, the worst first discrepancy among distinct series equals \(\lfloor n/2\rfloor\). For \(M=3\) there is no reduction. There the observed worst first discrepancy is \(2\) for \(n=4,5\), well below the cutoffs \(4\) and \(5\). Explaining that gap is open.

**Proposition SNG-O18 (closed form at \(M=2\)).** Let \(d^{\mathrm{odd}}_v\) be the number of odd-exponent edges at \(v\), and let \(o\) be the number of vertices with \(d^{\mathrm{odd}}_v\) odd. Then
\[
F(x)=(1-x)^{-(n-o)}(1+x)^{-o}.
\]
Two models with equal \(n\) have equal series if and only if their volume-one coefficients \(n-2o\) agree.

*Proof.* Modulo \(2\), \(d^2\equiv d\), so \((-1)^{a(h_u-h_v)^2}=(-1)^{a(h_u+h_v)}\). The product over edges is therefore \(\prod_v(-1)^{d^{\mathrm{odd}}_vh_v}\), and the height sum factorizes over vertices into geometric series. \(\square\)

This explains the data at \(M=2\): every graph on \(n\le5\) vertices falls into one of at most three classes, and all of them separate at volume one.

## 15.8 Edge-factor families and compressed interfaces

The October 2026 supplement `docs/research/VAKIL_BRIDGES.md` gives full proofs of three results, recorded here with identifiers. It applies standard tools from Vakil's draft of *Foundations of Algebraic Geometry* to the height series.

**Proposition SNG-O10 (finite determination for edge-factor families).** Place an independent factor \(t_e\) on every edge of a fixed template. For two fixed templates there is an \(R_*\) such that, over every commutative \(\mathbb Q\)-algebra, agreement through volume \(R_*\) is equivalent to equality of the complete series. The proof is the Hilbert basis theorem applied to the chain of coefficient-difference ideals. No effective \(R_*\) is given. An ideal that stops growing once can grow later: the coefficients \(0,\ldots,0,t\) are an example. Noetherian finite determination is not an algorithm.

**Proposition SNG-O11 (triangle tangent ranks).** On the positive octant, the three top-moment probes of the edge-factor triangle have Jacobian rank \(3\), \(2\) or \(1\) according as the edge factors take three, two or one distinct values. No further symmetric coefficient raises the rank.

**Proposition SNG-O12 (parallel composition and terminal forgetting).** Compressed charge interfaces multiply under parallel composition of blocks with disjoint interiors and edge-disjoint terminal graphs. Forgetting a terminal \(t\) at interior height \(h\) sends a cell by
\[
(j,Q,E)\mapsto\bigl(j+h,\ Q_{-t}+h\zeta,\ E+(d_t+|\zeta|)h^2-2hQ_t\bigr),
\]
and a source interface complete through \(R\) suffices for output budget \(R\).

These are applications of standard principles, not new algebraic geometry. They are implemented in `edge_factors.py` and `charges.py` and checked by `scripts/vakil_bridge.py --check`.

## 15.9 Margins, panels and family compression

SNG-O03 optimizes cost alone. This section treats three different objectives: margin under a cost budget, shared panels for several candidate pairs, and the smallest state needed for a restricted family. Each is posed and solved separately.

**Proposition SNG-O15 (bounded maximum margin).** Let observation \(j\) carry a deterministic error bound \(\sigma_j>0\) and fix a budget \(C\). The normalized margin \(|L_jM_wd|/\sigma_j\) attains a maximum over the finitely many experiments of cost at most \(C\). Branch-and-bound with the following bound returns that maximum. For the vector \(\infty\)-norm put \(\kappa(b)=\max\{\prod_{i\in u}\|M_i\|_\infty:\ c(u)\le b\}\). Then every extension \(w\cdot u\) of a word \(w\) satisfies
\[
\frac{|L_jM_uM_wd|}{\sigma_j}\ \le\ \frac{\|L_j\|_1}{\sigma_j}\,\kappa\bigl(C-c(w)-\gamma_j\bigr)\,\|M_wd\|_\infty .
\]

*Proof.* There are finitely many experiments because the attachment costs are bounded below by a positive constant. The bound follows from \(|Lv|\le\|L\|_1\|v\|_\infty\) and \(\|Mv\|_\infty\le\|M\|_\infty\|v\|_\infty\), applied letter by letter. The quantity \(\kappa\) is computed exactly by dynamic programming over the reachable cost sums, since a product of norms does not depend on letter order. A pruned subtree contains no experiment above its bound, and that bound is at most the incumbent, so the optimum survives. \(\square\)

There are three cautions. First, without a budget no optimum need exist: the amplification example has bounded optimum \(2^{\lfloor C\rfloor}\). Second, a finite supremum need not be attained. For \(M=\bigl(\begin{smallmatrix}1&1\\0&1/2\end{smallmatrix}\bigr)\), \(L=(1,0)\) and \(d=(0,1)\), the readings are \(2-2^{1-k}\). Third, dependence pruning can discard the optimal-margin row. In the two-generator example of `docs/research/ROBUST_SEARCH.md`, the cheapest witness has margin \(1\), while a budget-two experiment whose row is a multiple of a retained row reaches margin \(3\). On the path fixture with \(\sigma=1\) and costs \((2,1)\), the bounded optimum at budgets \(1,\ldots,6\) is \(1/8,3/16,\ldots,63/256\). The pattern \(1/4-2^{-(C+2)}\) is checked only for \(C\le6\).

**Proposition SNG-O16 (shared panels under box noise).** Let a panel \(\mathcal P\) of experiments be read with errors \(|\eta_e|\le\varepsilon_e\). Call a candidate \(c\) consistent if \(|y_e-r_e(v_c)|\le\varepsilon_e\) for every \(e\in\mathcal P\). Then the following are equivalent:

- for every possible true candidate, every admissible reading leaves only that candidate consistent;
- every pair of candidates is robustly separated by some \(e\in\mathcal P\), meaning \(|r_e(v_a)-r_e(v_b)|>2\varepsilon_e\).

*Proof.* If \(e\) robustly separates the true \(t\) from \(c\), then \(|y_e-r_e(v_c)|\ge|r_e(v_t)-r_e(v_c)|-\varepsilon_e>\varepsilon_e\), so \(c\) is excluded. Conversely, suppose no member robustly separates \(a\) and \(b\). Then the midpoint readings \(y_e=\tfrac12(r_e(v_a)+r_e(v_b))\) are admissible for both, so both remain consistent. \(\square\)

Finding a cheapest certifying panel is therefore a weighted set-cover problem over pairs. That problem is NP-hard in general, so the exact branch-and-bound in `panels.py` is worst-case exponential. Its lower bound packs pairs that no single experiment covers twice. A Euclidean-ball noise model is treated separately. There, several readings jointly certify a pair that no single reading separates robustly. Take six three-vertex candidates at \(R=3\), \(q=1/2\), costs \((2,1)\) and budget \(4\). Exactly one pair is never separable: the endpoint–middle and middle–endpoint placements on the path, which coincide under the path automorphism. The other classes are separated at cost \(1\). A robust panel exists if and only if \(\varepsilon<278513/2097152\).

**Theorem SNG-O19 (exceptional parameters).** Let the generators and observations have entries in \(\mathbb Q[q]\). Let \(W\) be the matrix of all experiment rows of word length at most \(n-1\), let \(r\) be its rank over \(\mathbb Q(q)\), and let \(D_r\) be the gcd of its \(r\times r\) minors. Then at every \(\alpha\) in a field extending \(\mathbb Q\), the observable rank of the specialized system is at most \(r\). It equals \(r\) if and only if \(D_r(\alpha)\ne0\).

*Proof.* At every specialization, the span of rows of length at most \(k\) is nondecreasing in \(k\) and constant from its first non-increase. So length \(n-1\) suffices at \(\alpha\) as well as over \(\mathbb Q(q)\). Minors commute with evaluation, so \(\operatorname{rank}W(\alpha)<r\) exactly when every \(r\times r\) minor vanishes at \(\alpha\). By Bézout in \(\mathbb Q[q]\), that happens exactly when the minors' gcd vanishes at \(\alpha\). \(\square\)

The minors of the generic closure basis alone are not enough. Their gcd can vanish where other words restore the rank. In the synthetic example \(L_1=(1,0)\), \(L_2=(0,q)\), \(M=\bigl(\begin{smallmatrix}0&1\\0&0\end{smallmatrix}\bigr)\), we have \(D_2(B)=q\) but \(D_2(W)=1\). The implementation `parametric.py` computes \(D_r\) through Hermite forms of the row modules of length at most \(k\), without listing \(W\). It factors \(D_r\) over \(\mathbb Q\) with certificates, isolates real roots by Sturm sequences, and replays rational exceptional values exactly.

For the standard contexts at \(R=1,\ldots,4\), every irreducible factor of \(D_r\) is \(q\), \(q\pm1\) or cyclotomic. For example, at \(R=2\) the divisor is \(q^4(q-1)^7(q+1)^3\Phi_3\Phi_4\). Hence the closure has full rank \(n\) at **every** \(q\in(0,1)\), not only at \(q=1/2\). The rank drops at \(q=0\), at \(q=1\), where it equals the number of observations \(R+1\), and at \(q=-1\) for \(R\ge2\). This is an exact result for \(R\le4\). Whether the factor pattern persists for larger \(R\) is open.

**Theorem SNG-O13 (cyclicity of realizable states).** Let \(A\) be the unital algebra generated by the compiled operators of a context language at budget \(R\) and \(q\in\mathbb Q\cap(0,1)\).

1. For every realizable graph state \(v\), the reachable space \(\operatorname{span}\{M_wv\}\) equals \(Av\) and has dimension \(\dim A\).
2. Suppose some context \(C\) in the language has pairwise distinct orbit constants \(q^{d_C(s^2+t^2)}\) over the orbits with \(s+t\le R\), and \([x^1]\kappa_{C,o}\ne0\) in every block of length at least two. Then \(A=\bigoplus_o\mathbb Q[x]/x^{m_o}\) with \(m_o=R+1-s-t\). In that case every realizable state is cyclic, and no attachment-closed family of graph states admits a linear compression, compatible with the attachments and outputs, of dimension below the formal quotient rank.

*Proof.* (1) By SNG-O05 each operator acts on block \(o\) as multiplication by a truncated series. So \(A\) is a commutative subalgebra of \(\mathcal B=\bigoplus_o\mathbb Q[x]/x^{m_o}\), acting on states by multiplication. The block of a realizable state has constant term \([x^0]x^{-s-t}\cdot x^{s+t}K^+_G(o)>0\), since the counts are positive and \(q>0\). So \(v\) is a unit of \(\mathcal B\), and \(a\mapsto av\) is injective on \(A\). The reachable space is \(\{av:\ a\in A\}\).

(2) Taking constant terms is an algebra homomorphism \(\chi:A\to\mathbb Q^{\text{orbits}}\). Since the values \(\chi(M_C)_o\) are distinct, Lagrange interpolation gives a polynomial \(p\) with \(\chi(p(M_C))=e_{o^*}\). The element \(b=p(M_C)^{N}\), with \(N\ge\max m_o\), is zero in every block \(o\ne o^*\), because there it is a nilpotent power. In block \(o^*\) it is a unit \(u\). Since \(u^{-1}\in\mathbb Q[u]\), some polynomial \(h\) gives \(bh(b)=e_{o^*}\in A\). Then \(z=e_{o^*}\bigl(M_C-\chi(M_C)_{o^*}\bigr)\) is multiplication by \(x\cdot(\text{unit})\) in block \(o^*\). Its powers together with \(e_{o^*}\) span \(\mathbb Q[x]/x^{m_{o^*}}\). Hence \(A=\mathcal B\), and every unit is cyclic. For an attachment-closed family, the space a compatible linear compression must preserve contains the reachable space of each member, which is the whole space here. By SNG-O02, the least dimension is then the formal quotient rank. \(\square\)

For the standard contexts the pendant-leaf pair satisfies the hypotheses exactly when \(R\le6\): the first collision is \(0^2+5^2=3^2+4^2\). Its first-order terms \(q^{(1-s)^2+t^2}+q^{s^2+(1-t)^2}\) are positive. Krylov closure confirms full reachability from several seeds for \(R\le4\). At \(R=7\), reachability from two different seeds has dimension \(69\), equal to the formal quotient rank. That is a finite computation, not a theorem for larger \(R\).

**Theorem SNG-O14 (star family: initial-state compression with growing savings).** Let \(S_\alpha\) be the block with \(\alpha\) leaves attached to terminal \(0\) and an isolated terminal \(1\). There is a matrix \(C\), independent of \(\alpha\), such that
\[
Y(S_\alpha)=C\,\bigl(\alpha^kq^{\alpha r^2}\bigr)_{0\le r\le R,\ 0\le k\le R-r}.
\]
Hence \(\dim\operatorname{span}\{Y(S_\alpha):\alpha\ge0\}\le(R+1)(R+2)/2\), while the formal dimension is \(\sum_{s\le t,\ s+t\le R}(R+1-s-t)\), a cubic polynomial in \(R\).

*Proof.* The interior kernel is \(K(s,t)=f(s)^\alpha\) with \(f(s)=\sum_hx^hq^{(h-s)^2}=q^{s^2}(1+g_s)\) and \(g_s=O(x)\). Then \([x^j]f(s)^\alpha=q^{\alpha s^2}\sum_{k\le j}\binom{\alpha}{k}[x^j]g_s^k\), which is \(q^{\alpha s^2}\) times a polynomial in \(\alpha\) of degree at most \(j\le R-s\) whose coefficients do not depend on \(\alpha\). The swapped term \(K(t,s)\) contributes the same with \(r=t\). \(\square\)

At \(q=1/2\) the span equals the bound for \(R\le7\), which is a finite check. The reconstruction \(C\) is fitted on \(\alpha<d\) and verified exactly on held-out \(\alpha\). The observable part equals the span, and the saving against the formal quotient is \(0,1,3,7,13,22,33\) for \(R=1,\ldots,7\).

The compressed coordinates are the explicit numbers \(\alpha^kq^{\alpha r^2}\). With \(q=a/b\), each has bit length \(O(R\log\alpha+\alpha R^2\log b)\). The \(n\) uncompressed coordinates have the same order each, so the storage ratio is \(n/d\sim R/6\). This family is not attachment-closed, because the pendant pair also adds leaves at terminal \(1\). By SNG-O13, closing it under the standard attachments removes every saving for \(R\le6\). Initial-state compression and attachment-closed compression are thus genuinely different problems.

**Proposition SNG-O20 (noncommuting terminal moves with closed semantics).** Keep the ordered truncated kernels \(Y_{(s,t)}[v]=[x^v]x^{s+t}K_G(s,t)\), with \(s+t\le v\le R\), without symmetrization. Extending terminal \(a\) means joining a new vertex \(\ell\) to \(a\), making \(\ell\) the terminal and \(a\) interior. This move acts by
\[
Y'_{(s',t)}[v]=\sum_sq^{(s-s')^2}\,Y_{(s,t)}[v-s'],
\]
and symmetrically for \(b\). Any context without a terminal edge, symmetric or not, acts blockwise as in SNG-O05. The truncated ordered space is closed under every such word. Extension does not commute with attaching a shared neighbour.

*Proof.* The new kernel is \(K'(s',t)=\sum_sx^sq^{(s-s')^2}K(s,t)\). The only new edge is \(a\ell\), and the old terminal height joins the interior volume. Extracting \([x^v]x^{s'+t}\) gives the formula, which reads \(Y\) only at volumes \(v-s'\le v\). Noncommutation is witnessed by the two orders, which give different graphs with different readings. \(\square\)

All \(85\) words of length at most three over the four moves agree with direct enumeration on six base blocks at \(R=2,3\). The ordered closure has full rank \(10\) and \(20\) there: within those finite budgets the expanded language distinguishes every pair of ordered states. One consequence: path\((0,1)\) and path\((1,2)\) have identical symmetric states, so no symmetric context can separate them, yet a single terminal extension separates them at cost one. Completeness at larger budgets is not claimed.

## 15.10 Interfaces and runnable examples

The public contracts are specified in `docs/specifications/OPERATORS-v1.md`. A minimal session:

```python
from fractions import Fraction
from singularity.graph import Graph
from singularity.graph_experiments import BoundaryExperimentSystem
from singularity.observability import observable_closure, minimum_distinguishing_experiment

system = BoundaryExperimentSystem(1, Fraction(1, 2))
operators = system.operator_system(attachment_costs=(2, 1))
certificate = observable_closure(operators)
path = Graph(3, ((0, 1), (1, 2)))
d = tuple(a - b for a, b in zip(system.compile_graph(path, (0, 2)), system.compile_graph(path, (0, 1))))
witness = minimum_distinguishing_experiment(operators, d, certificate)
assert (witness.word, witness.cost) == ((1,), 1)
```

```python
from singularity.graph import Graph
from singularity.periodic import PeriodicModel, compare_models
result = compare_models(PeriodicModel(Graph(3, ((0, 1), (1, 2))), 2), PeriodicModel(Graph(3, ((0, 1),)), 2))
assert result.equal and result.cutoff == 1
```

## 15.11 Formal status

The Lean packages `formal/` and `formal-analysis/` predate this chapter. Their declarations do not formalize SNG-O01 to SNG-O20. A separate formalization of the closure, quotient, cost-filtration and periodic-complement arguments is reported in `formal-analysis/README.md` only to the extent that it compiles without admitted results. Until then, all statements in this chapter are mathematical exposition with exact finite checks.

## 15.12 Open questions

The following are open:

- **Restricted families.** SNG-O13 settles attachment-closed graph families at \(R\le6\): they admit no savings. For \(R\ge7\) only finite data exist. Initial-state families such as the stars do compress (SNG-O14). Can any attachment-closed family compress at large \(R\), and does the reachable dimension always equal the formal quotient rank?
- **Corank.** Is the corank bound SNG-O06 sharp for every budget? It is attained at \(R=4\) and \(R=7\) in the retained receipts; one unretained run gave corank \(1\) at \(R=8\), also equal to the bound. Does the visible rank have a closed form in \(R\)?
- **Margins.** SNG-O15 handles a fixed budget. The \(\infty\)-norm bound can be loose: nothing is pruned on the path fixture. Better metric-specific bounds remain to be proved.
- **Panels.** Panels are exact only within a declared pool and candidate family. No polynomial-time exact method exists in general, unless P = NP.
- **Parameter dependence.** SNG-O19 settles \(R\le4\): full rank on all of \((0,1)\). Does \(D_r\) factor into \(q\), \(q\pm1\) and cyclotomic polynomials for every \(R\)? Rational-function entries, with pole guards, are not yet implemented.
- **Sharper periodic cutoffs and noncommuting operations.** SNG-O17 and SNG-O18 sharpen the periodic cutoff when weights have smaller periods. At \(M=3\), the observed worst discrepancy of \(2\) is unexplained. Noncommuting terminal moves (SNG-O20) are complete only at the finite budgets checked.
