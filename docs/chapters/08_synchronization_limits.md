# Synchronization limits, uniform scaling, and exact contractions

Setting the energy weight to zero and letting the arithmetic size parameter approach its divergence point are different operations. At zero weight a connected graph forces every coordinate integer to agree, producing \(\zeta(ks)\). At any fixed positive weight the system has rare unequal valuations at every prime, and their combined contribution diverges at \(s=1\). There are infinitely many opportunities for a rare local event. A small penalty need not remain negligible when those opportunities accumulate. This chapter turns that intuition into a uniform theorem and then develops optional extensions that retain the same exact arithmetic meaning.

Assume first that \(G\) is connected with \(k\ge2\), minimum degree \(d\ge1\), and edge connectivity \(\lambda\ge1\). Write \(m_d\) for the number of vertices of degree \(d\), and \(\alpha(q)=\sum_vq^{d_v}\). All limits below use real positive parameters. No complex continuation is needed for the double-scaling statements.

## An explicit estimate uniform in the energy weight

We begin with constants that are intentionally simple rather than optimized. Define

\[
 D_k=2(2^k-1),\qquad
 C_k=4(2^k-1-k/2),\qquad
 A_k=C_k+D_k^2/2+k.
 \tag{8.1}
\]

Let

\[
 J_k=\sum_{n\ge2}\frac{\log n}{n^k}<\infty.
\]

This last constant is computable with an elementary integral remainder. For a cutoff \(N\ge2\), the omitted tail is at most

\[
 \int_N^\infty\frac{\log t}{t^k}\,dt
 =N^{1-k}\left(\frac{\log N}{k-1}+\frac1{(k-1)^2}\right).
 \tag{8.2}
\]

The summand is decreasing on \([2,\infty)\) for \(k\ge2\), so the integral bound applies directly.

**Theorem SNG-A15 — uniform synchronization estimate.** For \(0\le q\le1\) and \(\varepsilon>0\),

\[
 \begin{aligned}
 &\left|\log Z_G(1+\varepsilon,q)
 -\log\zeta(k)-\alpha(q)\log(1/\varepsilon)\right|\\
 &\hspace{12mm}\le
 A_kq^\lambda\bigl(\zeta(2)-1\bigr)
 +(kJ_k+k)\varepsilon.
 \end{aligned}
 \tag{8.3}
\]

**Proof.** Write \(B_G(x,q)=1+u(x,q)\). Every nonzero minimum-zero profile has energy at least \(\lambda\). Therefore, for real \(0\le x\le1/2\),

\[
 0\le u(x,q)\le q^\lambda D_kx,
\]

and, since the volume-one coefficient is \(\alpha(q)\),

\[
 0\le u(x,q)-\alpha(q)x\le q^\lambda C_kx^2.
\]

To verify the constants, bound each minimum-zero coefficient by the number of all weak compositions. At \(x\le1/2\), dividing the first bound by \(x\) and the second by \(x^2\) leaves geometric-composition sums bounded respectively by \(D_k\) and \(C_k\). These bounds discard graph information but retain the crucial factor \(q^\lambda\).

For \(u\ge0\), integration of \(1-1/(1+u)\) gives

\[
 0\le u-\log(1+u)\le u^2/2.
\]

Also \(|\log(1-x)+x|\le x^2/[2(1-x)]\), and \(\alpha(q)\le kq^\lambda\). Combining the estimates gives

\[
 |\log B_G(x,q)+\alpha(q)\log(1-x)|
 \le A_kq^\lambda x^2.
 \tag{8.4}
\]

Here \(q^{2\lambda}\le q^\lambda\) was used in the quadratic term. Substitute \(x=p^{-s}\), with real \(s\ge1\), and sum over primes. By common-shift factorization,

\[
 \log H_G(s,q)-\log\zeta(ks)
 =\sum_p\{\log B_G(p^{-s},q)+\alpha(q)\log(1-p^{-s})\}.
\]

Thus its absolute value is at most \(A_kq^\lambda(\zeta(2)-1)\). The derivative bound \(|(\log\zeta)'(t)|\le\sum_{n\ge2}(\log n)n^{-k}=J_k\) for \(t\ge k\) gives

\[
 |\log\zeta(k(1+\varepsilon))-\log\zeta(k)|\le kJ_k\varepsilon.
\]

Finally the integral test yields \(1/\varepsilon\le\zeta(1+\varepsilon)\le1+1/\varepsilon\). Hence

\[
 0\le\log\zeta(1+\varepsilon)-\log(1/\varepsilon)
 \le\varepsilon.
\]

Multiply by \(\alpha(q)\le k\), use the leading factorization, and add the three error bounds. \(\square\)

This proof provides more than continuity of a regular factor. It shows exactly which uniform estimate permits the two parameters to move together. The graph-dependent minimum-cut exponent controls the error in replacing the regular factor by its synchronized value. The minimum-degree exponent will control the rare unequal valuations that are amplified by the singular factor. Those exponents need not be equal, and they play different mathematical roles.

## The double-scaling law

**Theorem SNG-A16 — synchronization boundary layer.** Let \(q_j\to0\), \(\varepsilon_j\downarrow0\). If

\[
 \alpha(q_j)\log(1/\varepsilon_j)\longrightarrow\tau
 \quad\text{in }[0,\infty],
\]

then

\[
 Z_G(1+\varepsilon_j,q_j)
 \longrightarrow\zeta(k)e^\tau,
 \tag{8.5}
\]

where \(e^{+\infty}=+\infty\). In particular, if

\[
 q_j^d\log(1/\varepsilon_j)\longrightarrow t<\infty,
\]

then the limit is \(\zeta(k)e^{m_dt}\). If that product tends to infinity, the partition function tends to infinity.

**Proof.** The error in (8.3) tends to zero. Exponentiating gives the first statement, including the infinite case. For the second, use

\[
 \alpha(q)=m_dq^d+R(q),\qquad
 0\le R(q)\le(k-m_d)q^{d+1}.
\]

When \(q^d\log(1/\varepsilon)\) has a finite limit, the extra contribution \(R(q)\log(1/\varepsilon)\) tends to zero. In the infinite case, \(\alpha(q)\ge m_dq^d\) is enough. \(\square\)

The scaling variable is logarithmic in the distance to the arithmetic singularity. For a graph with minimum degree one, maintaining a nontrivial finite limit requires \(q\) of order \(1/\log(1/\varepsilon)\). With minimum degree two it requires order \(1/\sqrt{\log(1/\varepsilon)}\). This is a conclusion of the exact estimate, not a power-law ansatz chosen from numerical plots. The coefficient \(m_d\) counts the cheapest single-vertex disagreements.

The theorem also explains the noncommuting iterated limits. At fixed \(\varepsilon>0\), sending \(q\to0\) gives \(\zeta(k(1+\varepsilon))\), and then sending \(\varepsilon\to0\) gives \(\zeta(k)\). At fixed \(q>0\), sending \(\varepsilon\to0\) gives infinity, so subsequently shrinking \(q\) does not recover that finite iterated limit. A family can therefore look synchronized throughout a large finite range and still have a different limiting divergence. The double-scaling variable states how close to one the size parameter must be before that discrepancy matters.

## Optional extension: vertex masses

Positive integer vertex masses allow exact contraction without pretending that a merged vertex represents only one original coordinate. Assign a mass \(m_v\ge1\) to each vertex and let \(M=\sum_vm_v\). Define

\[
 L_{G,m}(x,q)=\sum_{a\ge0}q^{E_G(a)}x^{\sum_vm_va_v}.
\]

Its arithmetic counterpart weights an integer tuple by \(\prod_vn_v^{-m_vs}\). All coefficients remain finite, and a common shift increases weighted volume by \(M\).

**Theorem SNG-A17 — weighted endpoints and first divergence.** For connected \(G\),

\[
 L_{G,m}=\frac{B_{G,m}}{1-x^M},\quad
 Z_{G,m}(s,0)=\zeta(Ms),\quad
 Z_{G,m}(s,1)=\prod_v\zeta(m_vs).
\]

Let \(r=\min_vm_v\) and fix \(0<q\le1\). Put \(\gamma(q)=\sum_{m_v=r}q^{d_v}\). Then the first nonconstant local term is \(\gamma(q)x^r\), the Euler product converges for real \(s>1/r\), and

\[
 Z_{G,m}(s,q)=\zeta(rs)^{\gamma(q)}H_{G,m}(s,q),
\]

with a positive nonzero regular factor near \(s=1/r\). Therefore its leading real singular exponent there is \(\gamma(q)\).

**Proof.** The shift and endpoint arguments are unchanged after adding masses. The least positive weighted volume is \(r\), attained exactly by the profiles \(e_v\) with \(m_v=r\). Their energies are \(d_v\). Every remaining weighted volume is an integer at least \(r+1\). Multiplication by \((1-x^r)^{\gamma(q)}\) leaves \(1+O(x^{r+1})\), and the same proof as Theorem SNG-A11 gives the regular factor. At least one vertex has minimum mass and \(q>0\), so \(\gamma(q)>0\); logarithmic divergence at \(s=1/r\) also proves the sharp real convergence threshold. \(\square\)

This extension changes the arithmetic size observable while retaining the same graph energy. It need not be interpreted as adding physical masses. Its exact purpose is to remember how many original coordinates have been identified, or how strongly their integer sizes are weighted. Ignoring those weights after contraction would move the synchronized zeta factor to the wrong argument.

## Optional extension: partial edge synchronization

Allow one energy weight \(q_e\in[0,1]\) for every edge. The local weight is \(\prod_eq_e^{(a_u-a_v)^2}\). Setting a selected edge weight to zero imposes equality of its endpoint heights. Equality propagates through the connected components of the selected-edge subgraph.

**Theorem SNG-A18 — exact contraction under zero edge weights.** Let \(F\subseteq E\), and set \(q_e=0\) for \(e\in F\). Let \(C_1,\ldots,C_t\) be the components of \((V,F)\). Replace each component by one vertex of mass \(|C_i|\). An unselected edge between \(C_i\) and \(C_j\) contributes its original factor \(q_e^{(b_i-b_j)^2}\); an internal unselected edge contributes one. Then the resulting weighted, possibly multiple-edge local series equals the original specialized local series exactly. The equality also holds for the Euler products on every common domain of absolute convergence.

**Proof.** A profile survives the zero weights exactly when it is constant on each \(C_i\). Such profiles correspond bijectively to \(b\in\mathbb Z_{\ge0}^t\). Its original volume is \(\sum_i|C_i|b_i\). Internal edges have zero difference, and every remaining edge retains its stated difference and weight. This is equality term by term. Euler assembly follows on an absolutely convergent domain. \(\square\)

Parallel surviving edges can be combined: their weights multiply, since \(q_1^{d^2}q_2^{d^2}=(q_1q_2)^{d^2}\). Their presence is therefore supported mathematically even if the core graph class remains simple. The contraction description is an optional extended representation, not a request to accept duplicate edges silently in the ordinary constructor.

Contraction order does not matter. Applying zero constraints in stages produces the equivalence relation generated by all selected edges. Vertex masses add associatively, internal edges disappear, and external weights multiply associatively. This is a direct consequence of the termwise bijection, not an appeal to an unspecified categorical equivalence. If the selected edges connect the entire graph, the result is one vertex of mass \(k\), recovering \(\zeta(ks)\).

One can retain separate complex size parameters \(s_v\) as well. A synchronized component then has parameter \(s_{C_i}=\sum_{v\in C_i}s_v\). A sufficient domain before contraction is \(\Re s_v>1\) for every vertex; after contraction the less restrictive sufficient condition is \(\Re s_{C_i}>1\) for every component. The exact local identity remains valid wherever the relevant sums converge. This multivariate refinement records how contraction redistributes size exponents without claiming a complete several-variable continuation theory.

## Positive ordering and probabilistic derivatives

There is a further useful consequence of retaining positive weights. If \(G\subseteq H\) on the same vertex set, then \(E_H(a)\ge E_G(a)\). Hence, for \(q\in[0,1]\), every local coefficient and every real convergent arithmetic value satisfies \(L_H\le L_G\) and \(Z_H\le Z_G\). Adding constraints reduces the positive population weight. The corresponding ratio need not be monotone in \(s\), and no such stronger ordering is asserted.

For real \(s>1\) and \(q=e^{-\beta}\), normalize the integer-tuple weights by \(Z_G\). This defines an ordinary probability distribution. Its sufficient statistics are \(U(n)=\log\prod_vn_v\) and \(V(n)=\mathcal E_G(n)\). On compact parameter sets with \(s>1\) and \(\beta\ge0\), all their polynomial moments are finite. Differentiating gives

\[
 \partial_s\log Z=-\mathbb E[U],\qquad
 \partial_\beta\log Z=-\mathbb E[V],
\]

\[
 \nabla^2_{(s,\beta)}\log Z
 =\begin{pmatrix}\operatorname{Var}(U)&\operatorname{Cov}(U,V)\\
 \operatorname{Cov}(U,V)&\operatorname{Var}(V)\end{pmatrix}\succeq0.
 \tag{8.6}
\]

To justify finiteness, note that local energy is at most a graph-dependent constant times squared local volume, while the local geometric coefficient majorant has every polynomial volume moment at \(p^{-s}\). Summing their prime contributions and logarithmic size factors is uniformly convergent when \(s\) stays above one. Alternatively, global energy is bounded by a constant times \((\log\prod_vn_v)^2\), and products of powers of logarithms remain summable against \(\prod_vn_v^{-s}\). Dominated differentiation follows. The covariance identity is a general property of a normalized exponential family, used here with an explicitly defined arithmetic population.

These derivative identities supply rigorous sensitivity observations. They do not add a physical interpretation, empirical model, or claim of a thermodynamic phase transition. The proved limiting phenomenon is the uniform arithmetic boundary layer in Theorem SNG-A16. Its higher-order corrections, sharp graph-dependent constants, and possible multivariate visibility geometries remain separate analytic research questions.

## A worked contraction sequence

Take the four-vertex path \(0-1-2-3\), initially with mass one at every vertex and a common positive edge weight \(q\). Its leading exponent at \(s=1\) is \(2q+2q^2\), because its endpoint degrees are one and its internal degrees are two. Now set the weight on edge \(01\) to zero while retaining weight \(q\) on the other edges. The surviving local profiles are exactly \((a,a,b,c)\), and their local series is

\[
 \sum_{a,b,c\ge0}x^{2a+b+c}
 q^{(a-b)^2+(b-c)^2}.
 \tag{8.7}
\]

The contracted path has masses \(2,1,1\). Its light vertices have degrees two and one, so Theorem SNG-A17 gives leading exponent \(q^2+q\) at \(s=1\). The heavy vertex is still part of the graph energy, but it cannot occur in the lowest-volume profile. This is why simply counting contracted vertices would give the wrong answer.

Next synchronize edge \(23\) as well. The surviving profiles are \((a,a,b,b)\). There are two contracted vertices, each of mass two, joined by the original middle edge. The local factor is exactly \(L_{K_2}(x^2,q)\), and its arithmetic product is \(Z_{K_2}(2s,q)\). The first divergence moves to \(s=1/2\), with exponent \(2q\). Finally synchronize the middle edge; all four heights become equal and the product becomes \(\zeta(4s)\), whose first divergence is at \(s=1/4\).

The changes in threshold have a direct combinatorial explanation. A minimal positive shift of a synchronized block raises every original coordinate in that block. Its arithmetic denominator is therefore the corresponding power of an integer, rather than the first power associated with a single original vertex. The contraction operation preserves that information through its masses. The example also shows why a statement about an exactly zero coupling should not be inferred from small positive couplings without a uniform estimate: rare violations of the equality constraint can restore a divergence at a different location.

For the derivative identities (8.6), values at \(\beta=0\) mean derivatives from the allowed side \(\beta\ge0\). At an interior value \(\beta>0\), ordinary derivatives are available in a neighborhood. The one-sided convention is necessary because rewarding unbounded quadratic energy with \(\beta<0\) makes even a local height series diverge. This is a domain issue in the mathematical definition, not a numerical instability that can be fixed by increasing a cutoff.
