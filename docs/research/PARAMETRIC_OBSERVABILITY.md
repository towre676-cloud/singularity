# Parameter-aware observability

This note answers the parameter-dependence question listed among the open questions of [Chapter 15](../chapters/15_operators_experiments.md): where does the rank of the observation space of a context-operator system depend on \(q\)? It separates the **generic rank** over the field \(\mathbb Q(q)\) from the **rank at a given parameter** \(q_0\). It proves that the two differ exactly at the roots of one polynomial, the determinantal divisor \(D_r\). It shows how to compute \(D_r\) without listing exponentially many experiment rows, and it reports exact results for the standard graph contexts at budgets \(R=1,2,3,4\).

Implementation: [`parametric.py`](../../src/singularity/parametric.py). Tests: [`test_parametric.py`](../../tests/test_parametric.py). Receipt: [`parametric_observability.json`](../../results/parametric_observability.json), replayed by `python scripts/parametric_observability.py --check`.

The four categories are kept apart. Smith and Hermite normal forms, Cauchy–Binet, Sturm sequences, Gauss's lemma, the rational-root theorem, Kronecker's factorization method and the irreducibility of cyclotomic polynomials are **established literature**. Theorems 1–5 below are **proved** here. The graph results in Section 7 are **exact computations** over the declared finite population: the standard two-context language and budgets \(R\le4\). Section 8 lists **open questions**.

## 1. Setting

A **polynomial operator system** consists of the following data:

- a dimension \(n\ge0\);
- generators \(M_1,\dots,M_g\in\mathbb Q[q]^{n\times n}\);
- observation rows \(L_1,\dots,L_o\in\mathbb Q[q]^{1\times n}\);
- attachment costs \(c_i>0\) and observation costs \(\gamma_j\ge0\), exactly as in Chapter 15.

Words, experiments and costs follow Section 15.2. A word \(w=(i_1,\dots,i_m)\) applies \(i_1\) first, and its experiment row is \(L_jM_w=L_jM_{i_m}\cdots M_{i_1}\). Right multiplication by \(M_i\) prepends the letter \(i\).

Let \(K\) be a field and \(\phi:\mathbb Q[q]\to K\) a ring homomorphism. Two cases matter:

- evaluation \(q\mapsto q_0\), with \(q_0\) rational or real algebraic;
- the inclusion \(\mathbb Q[q]\subset\mathbb Q(q)\).

Applying \(\phi\) entrywise gives an operator system over \(K\), called the **specialization**. Every entry is a polynomial, so every \(q_0\) is admissible and there are no poles. Rational-function entries are not supported: clearing denominators would add guard polynomials whose roots must be excluded, and that has not been implemented. The graph compiler produces only polynomial entries.

Write \(\mathcal O_k(\phi)\subseteq K^{1\times n}\) for the \(K\)-span of the specialized experiment rows of word length at most \(k\), and \(\mathcal O(\phi)=\bigcup_k\mathcal O_k(\phi)\). Let \(W_k\in\mathbb Q[q]^{N_k\times n}\) stack all experiment rows of length at most \(k\), with \(N_k=o\,(1+g+\cdots+g^k)\). Put \(W=W_{n-1}\).

## 2. The length bound

**Theorem 1 (length bound).** Over any field \(K\) and for any specialization \(\phi\):

1. \(\mathcal O_k(\phi)\subseteq\mathcal O_{k+1}(\phi)\);
2. if \(\mathcal O_k(\phi)=\mathcal O_{k+1}(\phi)\), then \(\mathcal O_k(\phi)=\mathcal O_{k+j}(\phi)\) for every \(j\ge0\);
3. \(\mathcal O(\phi)=\mathcal O_{n-1}(\phi)\) when \(n\ge1\), and \(\mathcal O(\phi)=\mathcal O_0(\phi)=0\) when \(n=0\).

*Proof.* (1) Every row of length at most \(k\) also has length at most \(k+1\).

(2) The rows of length at most \(k+1\) are the observations together with the rows \(xM_i\) for \(x\) of length at most \(k\). By linearity,
\[
\mathcal O_{k+1}=\mathcal O_0+\sum_i\mathcal O_kM_i .
\]
Suppose \(\mathcal O_{k+1}=\mathcal O_k\). Then
\[
\mathcal O_{k+2}=\mathcal O_0+\sum_i\mathcal O_{k+1}M_i=\mathcal O_0+\sum_i\mathcal O_kM_i=\mathcal O_{k+1},
\]
and induction on \(j\) gives the claim.

(3) The dimensions \(\dim\mathcal O_0\le\dim\mathcal O_1\le\cdots\) are bounded by \(n\). By (2) they increase strictly until the first repetition and are constant afterwards. If \(\mathcal O_0=0\), then every \(\mathcal O_k=0\), because \(\mathcal O_1=0+\sum_i0\cdot M_i=0\). Otherwise \(\dim\mathcal O_0\ge1\), so at most \(n-1\) strict increases are possible, and the chain is constant from \(k=n-1\) on. \(\square\)

The argument uses only linearity over \(K\). It therefore holds at every rational or algebraic \(q_0\), and over \(\mathbb Q(q)\). In particular \(\operatorname{row}_KW(\phi)=\mathcal O(\phi)\) for every specialization.

## 3. Generic rank and the determinantal divisor

Let \(r=\operatorname{rank}_{\mathbb Q(q)}W\), the **generic rank**. For \(1\le k\le\min(N,n)\), let \(D_k(A)\) denote the **\(k\)-th determinantal divisor** of a matrix \(A\) over \(\mathbb Q[q]\): the monic gcd of all its \(k\times k\) minors, or \(0\) if all of them vanish. Put \(D_0=1\).

**Theorem 2 (exceptional parameters).** For every field \(K\) with an evaluation \(\phi:q\mapsto\alpha\in K\):

1. \(\dim\mathcal O(\phi)\le r\);
2. \(\dim\mathcal O(\phi)=r\) if and only if \(D_r(W)(\alpha)\ne0\).

*Proof.* By Theorem 1, \(\dim\mathcal O(\phi)=\operatorname{rank}_KW(\alpha)\). The rank of a matrix over a field is the largest size of a nonzero minor. Evaluation is a ring homomorphism, so every minor of \(W(\alpha)\) is the evaluation of the corresponding minor of \(W\).

(1) Every \((r+1)\times(r+1)\) minor of \(W\) is the zero polynomial, since \(r\) is the rank over \(\mathbb Q(q)\). Its evaluation is therefore zero.

(2) The ring \(\mathbb Q[q]\) is a principal ideal domain, so \(D_r(W)=\sum_\mu a_\mu\mu\) for minors \(\mu\) and polynomials \(a_\mu\) (Bézout). If every \(r\times r\) minor vanishes at \(\alpha\), then \(D_r(W)(\alpha)=0\). Conversely, each minor is a multiple of \(D_r(W)\), so \(D_r(W)(\alpha)=0\) forces every minor to vanish at \(\alpha\). Hence some \(r\times r\) minor of \(W(\alpha)\) is nonzero if and only if \(D_r(W)(\alpha)\ne0\). \(\square\)

The **exceptional set** in a domain \(\Omega\subseteq\mathbb R\) is the set of real roots of \(D_r(W)\) in \(\Omega\). It is finite unless \(r=0\); when \(r=0\), \(D_0=1\) and there is nothing to report. Two statements must be kept apart:

- the generic rank holds at all but finitely many \(q_0\);
- the rank holds at every \(q_0\) in \(\Omega\).

The second requires \(D_r(W)\) to have no root in \(\Omega\). One check at one parameter proves neither: it gives only \(\operatorname{rank}W(q_0)\le r\).

## 4. Computing \(D_r(W)\) without listing \(W\)

The matrix \(W\) has \(N_{n-1}\) rows, exponentially many. Let \(\mathcal N_k\subseteq\mathbb Q[q]^{1\times n}\) be the \(\mathbb Q[q]\)-module spanned by the rows of \(W_k\).

**Theorem 3 (module reduction).**

1. \(\mathcal N_k=\mathcal N_0+\sum_i\mathcal N_{k-1}M_i\), and if \(\mathcal N_{k+1}=\mathcal N_k\), the chain is constant from \(k\) on.
2. If two matrices \(A,B\) over \(\mathbb Q[q]\) have the same row module, then \(D_j(A)=D_j(B)\) for every \(j\).
3. Let \(H\) be a matrix with \(r\) rows and rank \(r\), and suppose its \(n\times r\) transpose has row Hermite form \(\begin{pmatrix}T\\0\end{pmatrix}\) with \(T\) upper triangular. Then \(D_r(H)\) is the monic normalization of the product of the diagonal entries of \(T\).
4. For \(k\ge n-1\), \(D_r(W_{k+1})\) divides \(D_r(W_k)\), and all these polynomials have the same set of roots in every field extension.

*Proof.* (1) The proof of Theorem 1(2) works verbatim with \(\mathbb Q[q]\)-spans in place of \(K\)-spans, because right multiplication by \(M_i\) is \(\mathbb Q[q]\)-linear.

(2) Every row of \(A\) is a \(\mathbb Q[q]\)-combination of rows of \(B\), so \(A=PB\) for a polynomial matrix \(P\). By Cauchy–Binet, every \(j\times j\) minor of \(A\) is a \(\mathbb Q[q]\)-combination of \(j\times j\) minors of \(B\). Hence \(D_j(B)\) divides \(D_j(A)\). By symmetry they are equal up to a unit, and monic normalization makes them equal.

(3) Determinantal divisors are unchanged under multiplication by unimodular matrices on either side. This is Cauchy–Binet in both directions, applied to a unimodular matrix and its inverse. They are also unchanged under transposition. The Hermite form \(UH^{\mathsf T}\), with \(U\) unimodular, has exactly one possibly nonzero \(r\times r\) minor, \(\det T\). It is nonzero because the rank is \(r\).

(4) \(\mathcal N_k\subseteq\mathcal N_{k+1}\) gives \(W_k=PW_{k+1}\), so \(D_r(W_{k+1})\mid D_r(W_k)\) by Cauchy–Binet. By Theorem 2 each of them vanishes at \(\alpha\) exactly when \(\dim\mathcal O(\alpha)<r\), and \(\mathcal O(\alpha)\) does not depend on \(k\ge n-1\) (Theorem 1). \(\square\)

*Remarks.*

- **The module chain can grow after the rank stabilizes.** Over the PID \(\mathbb Q[q]\), the chain \(\mathcal N_k\) can keep growing after the rank has stopped growing: the index can shrink. It still stabilizes. Once the rank is \(r\), each strict step \(\mathcal N_k\subsetneq\mathcal N_{k+1}\) between free modules of rank \(r\) writes a basis of \(\mathcal N_k\) as \(P\) times a basis of \(\mathcal N_{k+1}\), with \(P\) square and \(\deg\det P\ge1\). Hence \(\deg D_r\) drops strictly at every step.
- **The recorded quantities.** The implementation iterates the Hermite form of \(\mathcal N_k\) to \(k=\max(n-1,k_*)\), where \(k_*\) is the first repetition. Both are canonical, because the Hermite form with monic pivots and reduced entries above the pivots is unique. It reports \(D_r(W)=D_r(\mathcal N_{n-1})\) and \(D_r(\mathcal N_{k_*})\) for the full experiment set. It checks that the second divides the first and that they have the same square-free part.
- **An oracle for small systems.** For tiny systems the tests also enumerate \(W\) explicitly. They compute the gcd of every \(r\times r\) minor by the Leibniz formula, with independent polynomial code. A Smith normal form routine gives a third computation.

## 5. Why the generic basis is not enough

The closure over \(\mathbb Q(q)\) returns a **generic basis** \(B(q)\): \(r\) experiment rows that are independent over \(\mathbb Q(q)\) and of minimum cost in the sense of SNG-O03. The pruning argument of SNG-O03 is field independent. The rows of \(B\) are rows of \(W\), so \(B=PW\), and Cauchy–Binet gives
\[
D_r(W)\ \big|\ D_r(B).
\]
The converse divisibility fails. At \(q_0\), the matrix \(B(q_0)\) is one particular choice of \(r\) rows. Every other experiment row equals \(\sum_k\lambda_k(q)b_k(q)\) with \(\lambda_k\in\mathbb Q(q)\). If a denominator of \(\lambda_k\) vanishes at \(q_0\), that row need not lie in \(\operatorname{row}B(q_0)\), and it can restore the rank that \(B(q_0)\) lost.

**Example (checked in the tests).** Take \(n=2\), \(L_1=(1,0)\), \(L_2=(0,q)\), both with cost \(0\), and one generator \(M=\begin{pmatrix}0&1\\0&0\end{pmatrix}\) with cost \(1\). The generic closure keeps the two direct readings, so \(B=\begin{pmatrix}1&0\\0&q\end{pmatrix}\) and \(D_2(B)=q\). But \(L_1M=(0,1)=q^{-1}L_2\) is an experiment. Over \(\mathbb Q[q]\) the rows \(L_1,L_2,L_1M\) generate everything, and \(D_2(W)=1\). At \(q_0=0\), the matrix \(B(0)\) has rank one, while the closure at \(q_0=0\) has rank two, with basis words \(()\) and \((0)\). So \(q_0=0\) is a root of \(D_2(B)\) but is not exceptional.

The graph data show the same phenomenon. At \(R=3\), \(D_{13}(B)\) contains the factor \(q^2+q+\tfrac12\), which does not divide \(D_{13}(W)\). Its roots are not real.

There are two sound routes:

- the module route of Theorem 3, which is what the implementation uses;
- the candidate route: the roots of \(D_r(B)\) are a finite superset of the exceptional set, and each candidate is decided by a closure computed at that parameter.

The implementation uses the second route as a cross-check at rational parameters. Both routes are exact. Only the first identifies the exceptional set with the roots of a single computed polynomial.

## 6. Exceptional parameters: isolation and certification

**Factorization over \(\mathbb Q\).** The implementation factors \(D_r(W)\) as follows.

1. **Linear factors.** The rational-root theorem lists every rational root, and each is divided out with full multiplicity.
2. **Cyclotomic factors.** The search is complete: it covers every \(m\ge3\) with \(\varphi(m)\le\deg\). The bound \(\varphi(m)\ge\sqrt{m/2}\) limits it to \(m\le2\deg^2\). A modular filter discards most \(m\). It is sound: if \(\Phi_m\) divides the primitive integer polynomial \(v\), then \(v(\zeta)\equiv0\pmod p\) for a prime \(p\equiv1\pmod m\) and a primitive \(m\)-th root of unity \(\zeta\) modulo \(p\), because \(\Phi_m(\zeta)\equiv0\). Candidates that pass are tested by exact division. \(\Phi_m\) is irreducible over \(\mathbb Q\).
3. **The remainder.** It is split into square-free parts (Yun). Each part is certified irreducible in one of two ways:
   - **by modular degree patterns.** By Gauss's lemma, a factor of degree \(e\) over \(\mathbb Q\) reduces modulo \(p\) to a product of irreducible factors whose degrees sum to \(e\), provided \(p\) does not divide the leading coefficient and the reduction is square-free. If no proper degree is a subset sum of the patterns for every prime used, the part is irreducible.
   - **by Kronecker's exhaustive method**, for small degree. This handles polynomials such as \(q^4-10q^2+1\), which are reducible modulo every prime.

A part that neither method certifies would be reported as "not certified irreducible"; that did not occur. The product of the factors is checked against \(D_r\).

**Real roots.** Linear factors give rational roots. A factor \(\Phi_m\) with \(m\ge3\) has no real root: its roots are the primitive \(m\)-th roots of unity, and the only real roots of unity are \(\pm1\), which are the roots of \(\Phi_2\) and \(\Phi_1\). Every other irreducible factor is isolated by Sturm sequences ([`parameters.py`](../../src/singularity/parameters.py)), inside its Cauchy bound or inside \((0,1)\). The isolating interval is then bisected until two conditions hold: its closure contains no root of any other factor, and its width is at most \(2^{-10}\). The interval endpoints are rational and are never roots, since an irreducible factor of degree at least two has no rational root.

**Theorem 4 (certification).**

1. **Rational roots.** Let \(q_0\) be a rational root of \(D_r(W)\). Then `observable_closure` on the rational specialization has rank below \(r\). The receipt replays this, and it also recomputes the rank of the specialized Hermite basis.
2. **Irrational roots.** Let \(\alpha\) be a real root of an irreducible factor \(f\) of \(D_r(W)\). Then the rank at \(\alpha\) is below \(r\), by Theorem 2. This statement is the certification, and it uses no floating point.
3. **Confirmation over \(\mathbb Q(\alpha)\).** The rank over \(\mathbb Q(\alpha)\cong\mathbb Q[t]/(f)\) equals the rank of the Hermite basis \(H\) of \(\mathcal N_{n-1}\), computed with entries reduced modulo \(f\).

*Proof of (3).* \(H\) and \(W\) have the same row module, so \(W=PH\) and \(H=QW\) over \(\mathbb Q[q]\). Evaluating at \(\alpha\) gives \(\operatorname{row}W(\alpha)=\operatorname{row}H(\alpha)\). Reducing modulo \(f\) is evaluation at \(\alpha\) in \(\mathbb Q[t]/(f)\), which is a field because \(f\) is irreducible. A non-invertible nonzero element would expose a proper factor of \(f\), and the code raises on it. \(\square\)

**Theorem 5 (rank at every parameter).** If \(D_r(W)\) has no root in \(\Omega\), then the observation rank equals \(r\) at every \(q_0\in\Omega\). Otherwise the minimum rank over \(\Omega\) is attained at an exceptional parameter.

*Proof.* Immediate from Theorem 2. \(\square\)

## 7. The graph contexts

**Symbolic compiler.** `symbolic_boundary_system(R)` builds the operators of `BoundaryExperimentSystem` with \(q\) kept symbolic. The entry in row \((o,v)\) and column \((o,j)\) is
\[
\sum_{(k,e):\,k=v-j}\operatorname{count}(k,e)\,q^e,
\]
the sum running over the cells of the terminal kernel \(K_C(o)\). The entries are integer polynomials. Compiler correctness (SNG-O05) is a statement about formal power series in \(x\) with coefficients in \(\mathbb Z[q]\), so it holds with \(q\) symbolic. The compiled matrices at \(q_0\) are the specializations of the symbolic ones. The receipt checks this exactly: the specializations at \(q=\tfrac12\) are identical, as tuples of Fractions, to `BoundaryExperimentSystem(R, 1/2).operator_system()`, and the tests repeat the check at \(q=\tfrac13\). Since `BoundaryExperimentSystem` rejects \(q\notin(0,1)\), replays at \(q_0\in\{-1,0,1\}\) build the specialized `OperatorSystem` directly.

**Exact results.** All contexts are the standard pendant-leaf pair and shared neighbour, with unit attachment costs. "Module chain" lists \(\operatorname{rank}_{\mathbb Q(q)}W_k\) for \(k=0,1,\dots\) up to stabilization.

| \(R\) | \(n\) | generic rank | module chain | \(\deg D_r\) | real exceptional set: rank there | exceptional in \((0,1)\) |
|---|---|---|---|---|---|---|
| 1 | 3 | 3 | 2, 3 | 1 | \(1:2\) | none |
| 2 | 7 | 7 | 3, 5, 6, 7 | 18 | \(-1:5,\ 0:5,\ 1:3\) | none |
| 3 | 13 | 13 | 4, 8, 10, 11, 12, 13 | 93 | \(-1:7,\ 0:9,\ 1:4\) | none |
| 4 | 22 | 22 | 5, 11, 15, 17, 18, 19, 20, 21, 22 | 371 | \(-1:9,\ 0:13,\ 1:5\) | none |

The factorizations over \(\mathbb Q\) are:

- \(R=1\): \(D_3=q-1\);
- \(R=2\): \(D_7=q^4(q-1)^7(q+1)^3\,\Phi_3\,\Phi_4\);
- \(R=3\): \(D_{13}=q^{24}(q-1)^{21}(q+1)^8\,\Phi_3^3\Phi_4^5\Phi_5^2\Phi_7\Phi_8\Phi_9\);
- \(R=4\): \(D_{22}=q^{120}(q-1)^{53}(q+1)^{24}\,\Phi_3^{11}\Phi_4^{14}\Phi_5^5\Phi_6^4\Phi_7^4\Phi_8^5\Phi_9^2\Phi_{10}\Phi_{11}\Phi_{12}\Phi_{14}\Phi_{15}\Phi_{16}\).

Every irreducible factor is \(q\), \(q\pm1\) or cyclotomic. Consequences, exact for this declared population:

1. **On the open interval.** For \(R\le4\) the observation space has full rank \(n\) at **every** \(q_0\in(0,1)\), and at every real \(q_0\notin\{-1,0,1\}\). This follows from Theorem 5. It is not inferred from the earlier full-rank check at \(q=\tfrac12\).
2. **The real exceptional set** is \(\{1\}\) for \(R=1\) and \(\{-1,0,1\}\) for \(R=2,3,4\). Every rank drop was replayed with `observable_closure`.
   - At \(q=1\) the rank is \(R+1\), the number of observations: no experiment adds information beyond the direct volume readings.
   - At \(q=0\) only zero-energy profiles survive.
3. **Non-real exceptional parameters** are the primitive roots of unity whose orders are the cyclotomic indices listed above (3 to 12, 14, 15 and 16). They are recorded, but they are not in any real domain.
4. **The full experiment set.** \(D_r(\mathcal N_{k_*})=D_r(W)\) in all four cases, because the module chain stabilizes at \(k_*=1,3,5,8\le n-1\).
5. **Ranks over \(\mathbb Q(q)\) and at \(q=\tfrac12\).** At \(R=4\) the ranks of \(W_k\) over \(\mathbb Q(q)\) coincide with the length-filtered ranks at \(q=\tfrac12\) recorded in Chapter 15 (SNG-E009). This is consistent with Theorem 1. It is not implied by it: the ranks over \(\mathbb Q(q)\) are upper bounds for the ranks at any parameter.
6. **Sampled parameters.** At the nine sample values \(\{-2,-1,-\tfrac12,0,\tfrac13,\tfrac12,\tfrac23,1,2\}\) and for each \(R\), the closure rank equals the generic rank exactly when \(D_r(q_0)\ne0\), and it agrees with the rank of the specialized Hermite basis.

The multiplicities in \(D_r\) are reported as computed. No interpretation is claimed for them.

**Cost.** With Python 3.13, the full receipt takes about 27 s with a peak resident set of about 24 MB. \(R=4\) dominates, at about 22 s for the analysis and 4 s for the cross-checks. \(D_r\) of the generic basis matrix was computed only for \(R\le3\): at \(R=4\) its Hermite form exceeded the time budget, so the \(R=4\) comparison of \(B\) with \(W\) is not reported. \(R=7\), where the rank at \(q=\tfrac12\) is \(69<70\), was not attempted symbolically.

## 8. Limitations and open questions

- **Scope of the graph results.** They cover the standard two contexts and \(R\le4\). Nothing is claimed for larger budgets, other context languages or the limit \(R\to\infty\). Theorem 2 still applies to every budget.
- **Entry types.** Rational-function entries, with their denominator guards, are not implemented.
- **Factorization certificates.** The certificate is complete for the factors met here: linear, cyclotomic, or certified by degree patterns or by Kronecker's method. A general polynomial can defeat the modular certificate and exceed the Kronecker degree limit. It would then be reported as uncertified, and in that case no number-field rank is computed for its roots.
- **Open: a closed form for \(D_r\).** Does every irreducible factor of \(D_r\) for the standard contexts remain \(q\), \(q\pm1\) or cyclotomic at all budgets? This would imply that the rank at every \(q_0\in(0,1)\) is always the generic rank. The converse need not hold: a noncyclotomic factor can have no roots in that interval. At \(R=7\), parameter-wide generic rank would say that the formal invisible direction of SNG-E010 is the only one at every \(q_0\in(0,1)\). That claim has not been checked.
- **Open: the multiplicities and the exceptional ranks.** Explain the multiplicities of \(q\), \(q-1\) and \(q+1\), and the ranks \(R+1\) at \(q=1\).
