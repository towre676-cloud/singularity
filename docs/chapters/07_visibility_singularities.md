# Visibility singularities: the first distinction survives arithmetic assembly

A comparison is strongest when simpler explanations have been removed explicitly. Two graphs can have the same degree multiset and therefore the same leading divergence. They can agree on additional finite invariants and still differ in a later local height coefficient. The arithmetic question is then not whether an Euler product can be attached to each graph: that is already automatic. The useful question is where the first unmatched local observation becomes analytically visible.

For \(0\le q\le1\), put \(\ell_{G,n}(q)=[x^n]L_G(x,q)\). In this chapter, \(q\) is fixed before an analytic comparison is made. Polynomial equality in \(q\) is stronger than numerical equality at a selected parameter. A polynomial discrepancy can vanish at an endpoint or an interior root, in which case the first visible volume at that numerical parameter can change.

## A precise first-discrepancy theorem

**Theorem SNG-A11 — first-discrepancy ratio law.** Let \(G,H\) have the same finite number \(k\) of vertices. Fix \(q\in[0,1]\). Suppose

\[
 \ell_{G,n}(q)=\ell_{H,n}(q)\quad(0\le n<r),
 \qquad
 \delta=\ell_{G,r}(q)-\ell_{H,r}(q)\ne0.
 \tag{7.1}
\]

For real \(s>1/r\), the ratio product

\[
 R_{G,H}(s,q)=\prod_p
 \frac{L_G(p^{-s},q)}{L_H(p^{-s},q)}
 \tag{7.2}
\]

converges absolutely to a positive number. It agrees with \(Z_G/Z_H\) on the original domain \(s>1\). Define

\[
 K_{G,H}(s,q)=\prod_p
 (1-p^{-rs})^\delta
 \frac{L_G(p^{-s},q)}{L_H(p^{-s},q)}.
 \tag{7.3}
\]

The latter product converges absolutely and is positive for real \(s>1/(r+1)\). It is holomorphic and nonzero in a complex neighborhood of \(s_0=1/r\). For real \(s>s_0\),

\[
 R_{G,H}(s,q)=\zeta(rs)^\delta K_{G,H}(s,q),
 \qquad
 R_{G,H}(s,q)\sim
 C(q)(rs-1)^{-\delta},
 \tag{7.4}
\]

where \(C(q)=K_{G,H}(1/r,q)>0\).

**Proof.** Condition (7.1) gives

\[
 \frac{L_G(x,q)}{L_H(x,q)}
 =1+\delta x^r+O(x^{r+1})
\]

near zero, because the denominator has constant term one. The prime sum of the deviation converges for \(rs>1\). No local denominator vanishes on the positive real axis: both local series have nonnegative coefficients and constant term one. Thus the product is positive, and its logarithm converges absolutely. Multiplication by \((1-x^r)^\delta\) cancels the first discrepancy, leaving \(1+O(x^{r+1})\). This proves convergence of (7.3) on the stated real interval.

To obtain a complex neighborhood, separate finitely many small primes from the normally convergent tail. Every small-prime denominator is positive at \(s_0\), hence nonzero in a sufficiently small disk about that point. The tail is analytic and nonzero there by its convergent logarithm. The factors \((1-p^{-rs})^\delta\) use the analytic logarithm defined on \(\Re s>0\). This gives the asserted local holomorphic nonzero function. On \(s>1/r\), the ordinary zeta Euler product yields the factorization. Finally \(\zeta(1+t)\sim1/t\) with \(t=rs-1\). \(\square\)

A positive discrepancy makes the ratio diverge at its visibility point; a negative discrepancy makes it tend to zero. Interchanging the graphs reverses that interpretation. If \(\delta\) is nonintegral, the complex singularity is a fractional-power branch singularity. It should not be called a pole. The theorem supplies a local branch and a positive-real asymptotic, not a globally single-valued meromorphic function.

There is also no requirement that the original partition functions converge separately at \(s_0\). Their common low-order divergences have been canceled in the ratio product before the limit is taken. This cancellation is the main analytic mechanism. It makes a comparison meaningful farther left without pretending that either original positive Dirichlet series has acquired an absolutely convergent definition there.

The positive-real comparison now has a complete Lean proof over actual Mathlib real numbers and the Riemann zeta function. In `formal-analysis/`, `SingularityAnalysis.visibility_of_coefficients` proves the theorem for nonnegative polynomial-growth coefficient sequences, and `SingularityAnalysis.graph_visibility` applies it to graph height coefficients for \(q\in[0,1]\). The chain proves the local logarithmic expansion, prime-product convergence and boundary continuity, the zeta Euler product and its residue limit. It identifies the continued ratio with the quotient of the original prime products for \(s>1\). The concrete statements `SingularityAnalysis.spectral_visibility_half` and `SingularityAnalysis.binary_visibility_half` import P33 and prove the exact exponents at \(q=1/2\). No unverified analytic premise structure remains. The local-complex holomorphy and branch-continuation argument in this chapter, and the later interval endpoints, remain ordinary or computer-assisted mathematics rather than part of that real-analytic Lean theorem.


## A volume-two calculation and its actual meaning

At volume two there are only two kinds of profile: \(2e_v\), and \(e_u+e_v\) with \(u<v\). Their energies give the identity

\[
 \ell_{G,2}(q)=\sum_vq^{4d_v}
 +\sum_{u<v}q^{d_u+d_v-2A_{uv}}.
 \tag{7.5}
\]

For graphs with the same degree multiset, define the edge degree-sum polynomial

\[
 M_G(q)=\sum_{\{u,v\}\in E}q^{d_u+d_v}.
\]

Then

\[
 \ell_{G,2}-\ell_{H,2}
 =(q^{-2}-1)(M_G-M_H).
 \tag{7.6}
\]

Although written with \(q^{-2}\), the right side is a polynomial: every edge has degree sum at least two. Formula (7.6) follows by starting with the sum over all unordered vertex pairs and correcting the exponent by minus two precisely on edges.

**Calculation SNG-A12 — first reference pair.** On vertices \(0,\ldots,6\), take

\[
 \begin{aligned}
 E(G)&=\{01,02,03,04,12,35,36\},\\
 E(H)&=\{01,02,03,04,15,16,56\}.
 \end{aligned}
\]

Both have degree multiset \(\{4,3,2,2,1,1,1\}\). Exact profile enumeration gives equality at volume one and

\[
 \delta_2(q)=\ell_{G,2}-\ell_{H,2}
 =2q^2-4q^3+4q^5-2q^6
 =2q^2(1-q)^3(1+q).
 \tag{7.7}
\]

It is positive on \(0<q<1\), so Theorem SNG-A11 applies with \(r=2\). At \(q=1/2\),

\[
 R_{G,H}(s,1/2)\sim C_2(2s-1)^{-3/32}.
\]

The arithmetic conclusion is exact. Its local source is also elementary: \(M_G-M_H=2q^4(1-q)^2\). Thus this example illustrates arithmetic visibility of degree-assortativity information. It does not demonstrate that volume two captures a fundamentally higher-order graph relation. Matching more demanding invariants is a separate task, and the interpretation of a collision should state precisely which invariants were matched.

## A volume-three witness beyond the binary census

At volume three, the profile types are \(3e_v\), \(2e_u+e_v\) with \(u\ne v\), and indicators of three-element subsets. Hence

\[
 \ell_{G,3}(q)=\sum_vq^{9d_v}
 +\sum_{u\ne v}q^{4d_u+d_v-4A_{uv}}
 +\sum_{|S|=3}q^{|\partial S|}.
 \tag{7.8}
\]

This identity keeps the explanation transparent. The last term is binary. The middle term tests unequal heights at two vertices. It can distinguish a joint degree-mixing pattern that the degree-sum polynomial merges. Every energy remains a sum of pairwise edge terms; a later observation order does not introduce a new three-body interaction.

**Calculation SNG-A13 — binary-census reference pair.** Take

\[
 \begin{aligned}
 E(G)&=\{03,04,06,12,13,23,24,35\},\\
 E(H)&=\{01,04,06,15,16,26,36,45\}.
 \end{aligned}
\]

Both have degree multiset \(\{4,3,3,2,2,1,1\}\). The exact finite binary census agrees for every subset size and cut size. The local coefficients agree through volume two, but their volume-three difference is

\[
 \begin{aligned}
 \delta_3(q)={}&q^3-q^4-2q^6+2q^8+q^9+3q^{10}
 -3q^{11}-q^{12}-2q^{13}\\
 &+2q^{15}+q^{17}-q^{18}\\
 ={}&q^3(1-q)^5(1+q)^2
 (1+2q+5q^2+6q^3+8q^4\\
 &\qquad\qquad+6q^5+5q^6+2q^7+q^8).
 \end{aligned}
 \tag{7.9}
\]

The factorization proves positivity throughout \(0<q<1\); it is not a numerical sign test. At \(q=1/2\), the discrepancy is \(11025/262144\). Therefore

\[
 R_{G,H}(s,1/2)
 \sim C_3(3s-1)^{-11025/262144}
 \qquad(s\downarrow1/3).
 \tag{7.10}
\]

The finite calculation can be reproduced without a symbolic algebra system. Generate every weak composition of volumes zero through three into seven labeled coordinates, evaluate the integer energy from the supplied edges, and accumulate multiplicities by energy. There are only \(1,7,28,84\) profiles at those volumes. Subtract the two energy histograms. Multiplication of the explicit factors in (7.9) independently checks the polynomial identity. The full binary claim requires the separate exhaustive census of \(2^7\) subsets; it is not inferred from the first four height coefficients.

This pair does not match the full joint degree table on edges. Its degree-sum polynomial agrees, but the more refined table does not. Consequently the witness proves that the unequal-height sector carries information beyond the aggregated binary census. It does not prove survival after every degree-assortativity statistic has been matched. A stronger search should match that full table as well and seek discrepancies at volume four or later. The first-discrepancy theorem will still apply; the difficult new work is finding and interpreting the local witness.

## Effective control of the finite-prime approximation

A singularity law is more useful when its regular factor can be bounded rather than merely named. The following bounds require only local coefficient estimates and ordinary convergent sums. They do not require assumptions about prime gaps or an unproved asymptotic formula for primes.

For an integer cutoff \(P\ge2\), define \(Z_{\le P}\) by retaining primes at most \(P\). For real \(s>1\), put \(\rho=P^{-s}<1\). Since

\[
 0\le\log L(t,q)\le L(t,q)-1
 \le\frac{kt}{(1-\rho)^{k+1}}
 \qquad(0\le t\le\rho),
\]

we obtain the explicit interval

\[
 0\le\log Z_G(s,q)-\log Z_{\le P}(s,q)
 \le\frac{k}{(1-\rho)^{k+1}}
 \frac{P^{1-s}}{s-1}.
 \tag{7.11}
\]

Here the tail over primes was bounded by the tail over all integers, followed by the integral test. Exponentiating gives a multiplicative enclosure. The bound is deliberately conservative near \(s=1\), where raw Euler products converge slowly.

For the regularized ratio factor a faster bound is available. Set \(A_n=\binom{n+k-1}{k-1}\), choose \(0<\rho<1\), and define the explicit nonnegative constants

\[
 D=\frac{(1-\rho)^{-k}-1}{\rho},\qquad
 T=\frac{2}{\rho^{r+1}}
 \left((1-\rho)^{-k}-\sum_{n=0}^{r}A_n\rho^n\right),
\]

\[
 C=T+|\delta|D+
 \frac{|\delta|\rho^{r-1}}{2(1-\rho^r)}.
 \tag{7.12}
\]

**Theorem SNG-A14 — computable regularized tail.** Under the assumptions of Theorem SNG-A11, if real \(s>1/(r+1)\) and \(P^{-s}\le\rho\), then

\[
 \left|\log K_{G,H}(s,q)-\log K_{G,H,\le P}(s,q)\right|
 \le C\frac{P^{1-(r+1)s}}{(r+1)s-1}.
 \tag{7.13}
\]

**Proof.** Write \(A=L_G(t,q)\), \(B=L_H(t,q)\), and \(D_t=A-B\). Matching the coefficients below \(r\) gives

\[
 |D_t-\delta t^r|\le Tt^{r+1},\qquad
 \max(A-1,B-1)\le Dt.
\]

Because \(A,B\ge1\),

\[
 \log A-\log B=\int_0^1\frac{D_t}{B+uD_t}\,du.
\]

The denominator is at least one. Subtracting \(\delta t^r\) therefore gives an error at most \((T+|\delta|D)t^{r+1}\). Finally

\[
 |\log(1-t^r)+t^r|
 \le\frac{t^{2r}}{2(1-\rho^r)}
 \le\frac{\rho^{r-1}t^{r+1}}{2(1-\rho^r)}.
\]

Adding these estimates bounds the absolute logarithm of one regularized factor by \(Ct^{r+1}\). Sum over primes beyond \(P\), enlarge to all integers, and apply the integral test. \(\square\)

The constant (7.12) is implemented exactly as `regularized_tail_constant` in `src/singularity/arithmetic.py`. Its proof uses only \(0\le\ell_n(q)\le A_n\), valid for \(q\in[0,1]\), and \(t\le\rho<1\). The older routine `normalized_ratio_tail_constant` bounds the same quantity through the coefficient \(\ell^1\) norm of the logarithm. It requires \(U=(1-\rho)^{-k}-1<1\) and is far weaker: for the binary pair at \(q=1/2\) and \(\rho=1/32\) it gives about \(6.9\times10^5\), against about \(451\) from (7.12). Both are retained, and (7.12) is preferred. For rational \(s=a/b\) the cutoff is taken as \(P=N^b\), so the tail bound \(CP^{1-(r+1)s}/((r+1)s-1)\) and the radius condition \(P^{-s}=N^{-a}\le\rho\) are exact rational statements. Primes \(p\le P\) are kept exactly in the finite product, and those beyond it satisfy \(p^{-s}<\rho\). At \(s=1/r\) the bound is \(Cr/N\). The function `certified_tail_record` recomputes \(r\) and \(\delta\) from the two supplied coefficient prefixes at the chosen \(q\) before it produces a bound. It records the remaining hypotheses explicitly, refuses a prefix that ends before the discrepancy, and refuses a parameter such as \(q=1\) at which the discrepancy vanishes. The retained records for the three reference pairs at \(q=1/2\) are in `results/tail_records.json`. A test also checks the local inequality for the spectral pair at three rational points \(t\le\rho\), using rigorous rational enclosures of both local series by (7.14) and of \((1-t^r)^\delta\) by Bernoulli's inequalities, with no floating point.

**Theorem SNG-F35 (an explicit complex disc around the visibility point).** Keep the hypotheses of SNG-A11 with \(q\in[0,1]\) fixed, and let \(s_0=1/r\), \(D_\eta=\{s:|s-s_0|\le\eta\}\) and \(\sigma=s_0-\eta\). Suppose
\[
\text{(a) }(r+1)\sigma>1,\qquad
\text{(b) }r\eta\le\tfrac14,\qquad
\text{(c) }\frac{\eta\,k}{e\,\sigma}\,(1-2^{-\sigma})^{-(k+1)}<1 .
\]
Then for every prime \(p\) and every \(s\in D_\eta\), the local factors \(L_G(p^{-s},q)\) and \(L_H(p^{-s},q)\) have positive real part, and so does \(1-p^{-rs}\). With principal logarithms, the function
\[
K(s)=\exp\sum_p\bigl(\log L_G(p^{-s})-\log L_H(p^{-s})+\delta\log(1-p^{-rs})\bigr)
\]
is holomorphic and nonzero on \(D_\eta\), the series converges uniformly there, and \(K\) equals the positive product (7.3) on \(D_\eta\cap\mathbb R\). On \(D_\eta\setminus[s_0-\eta,s_0]\),
\[
R(s)=(rs-1)^{-\delta}\bigl((rs-1)\zeta(rs)\bigr)^{\delta}K(s),
\]
with principal powers, continues the Euler-product ratio from \(s\in(s_0,s_0+\eta]\). For nonintegral \(\delta\), \(s_0\) is a branch point, not a pole. For integral \(\delta\), \(R\) is meromorphic on \(D_\eta\) with a pole of order \(\delta\) (or a zero of order \(-\delta\)) at \(s_0\).

*Proof.* Write \(t=p^{-s}\) and \(t_0=p^{-s_0}\). Then \(|t|=p^{-\Re s}\le p^{-\sigma}\), and \(|t-t_0|\le|s-s_0|\log p\max_{w\in[s_0,s]}|p^{-w}|\le\eta\log p\,p^{-\sigma}\). For a local series \(L=\sum\ell_nt^n\) with \(0\le\ell_n\le A_n\) (true for \(q\in[0,1]\)), \(|L(t)-L(t_0)|\le|t-t_0|\sup_{|u|\le p^{-\sigma}}|L'(u)|\le|t-t_0|\,k(1-p^{-\sigma})^{-k-1}\). Using \(\max_{u>1}u^{-\sigma}\log u=1/(e\sigma)\) and \(p\ge2\), condition (c) makes this less than \(1\le L(t_0)\), so \(\Re L(t)>0\), and the principal logarithm is holomorphic in \(s\). Also \(|p^{-rs}|<1\), so \(\Re(1-p^{-rs})>0\). Let \(h_p(s)\) be the summand. As a function of \(t\), \(h(t)=\log L_G(t)-\log L_H(t)+\delta\log(1-t^r)\) is holomorphic for \(|t|\le\rho\) when \(U(\rho)=(1-\rho)^{-k}-1<1\). By (7.1) it vanishes to order \(r+1\) at \(t=0\), and \(|h|\le M=2U/(1-U)+|\delta|\rho^r/(1-\rho^r)\) there, using \(|\log(1+z)|\le|z|/(1-|z|)\). Schwarz's lemma applied to \(h(t)/M\) gives \(|h(t)|\le M(|t|/\rho)^{r+1}\). This is the constant of `normalized_ratio_tail_constant`, which is therefore valid for complex \(t\), unlike (7.12), whose proof used positivity. For \(p>P\) with \(P^{-\sigma}\le\rho\) we get \(|h_p(s)|\le Mp^{-(r+1)\sigma}/\rho^{r+1}\). By (a) the tail converges uniformly on \(D_\eta\), and \(K\) is holomorphic and nonzero as the exponential of a uniform limit of holomorphic functions. For real \(s\) the principal logarithms are real, so \(K\) agrees with (7.3). Finally, with \(w=rs\) and \(|w-1|\le r\eta\le\frac14\), the representation \((w-1)\zeta(w)=w-w(w-1)\int_1^\infty\{u\}u^{-w-1}\,du\) for \(\Re w>0\) gives \(|(w-1)\zeta(w)-1|\le|w-1|\bigl(1+|w|/\Re w\bigr)\le\frac14\bigl(1+\frac{5/4}{3/4}\bigr)=\frac23\). The principal power \(((w-1)\zeta(w))^\delta\) is therefore holomorphic on \(D_\eta\). For real \(s>s_0\), the identity \(R=\zeta(rs)^\delta K\) of SNG-A11 holds with positive real powers. The displayed expression is that identity rewritten, and \((rs-1)^{-\delta}\) with the principal branch is holomorphic off the cut. \(\square\)

The disc is explicit and very small. `complex_disc_certificate` in `src/singularity/arithmetic.py` checks (a)–(c) exactly, using the rational bounds \(2^{-\sigma}\le2^{-1/r}(1+\eta)\) and \(e>27/10\). It admits \(\eta=10^{-5}\) for the spectral pair (\(k=7\), \(r=2\)), \(\eta=10^{-7}\) for the binary pair (\(r=3\)) and \(\eta=10^{-9}\) for the cube and Möbius ladder (\(k=8\), \(r=4\)), and it refuses \(\eta=10^{-4}\), \(10^{-6}\) and \(10^{-8}\) respectively. The radius is limited by the crude derivative bound at \(p=2\). It is not a claim that larger discs contain zeros. Nothing here concerns complex energy parameters \(q\), whose local factors need their own zero analysis, or a global continuation.

**Theorem SNG-F39 (normalized local factors are entire).** Let \(G\) be connected on \(n\ge2\) vertices with diameter \(D\), and fix \(0<q<1\). Then \(B_G(t,q)=(1-t^n)L_G(t,q)\) is an entire function of \(t\), and \(L_G(t,q)\) is meromorphic in \(t\), with poles at most at the \(n\)-th roots of unity. For every \(H\ge0\) and complex \(t\),
\[
\begin{aligned}
\bigl|B_G(t,q)-B_{G,\le H}(t,q)\bigr|
&\le\sum_{h>H}N_n(h)\max(|t|^h,|t|^{(n-1)h})q^{\lceil h^2/D\rceil},\\
N_n(h)&=(h+1)^n-2h^n+(h-1)^n.
\end{aligned}
\]
where \(B_{G,\le H}\) sums over minimum-zero profiles of maximum at most \(H\).

*Proof.* A minimum-zero profile of maximum \(h\) has a vertex at height \(0\) and one at \(h\), joined by a path of at most \(D\) edges. Cauchy–Schwarz along that path gives \(h^2\le D\,E_G(a)\). Its volume lies in \([h,(n-1)h]\), and \(N_n(h)\) counts the profiles in \(\{0,\ldots,h\}^n\) with minimum \(0\) and maximum \(h\), by inclusion–exclusion. This proves the tail bound. A profile of volume \(m\) has \(h\ge m/(n-1)\), so \(|[t^m]B_G|\le\binom{m+n-1}{n-1}q^{m^2/((n-1)^2D)}\). Hence \(|[t^m]B_G|^{1/m}\to0\), and the radius of convergence is infinite. \(\square\)

For disconnected graphs the zero-energy profiles that are constant on components give \(B_G(t,0)\)-type poles at roots of unity of the component sizes (SNG-F19), so connectedness is necessary. The theorem concerns one local factor at fixed \(q\). It says nothing about continuation of the product over primes.

**Theorem SNG-F38 (certified enclosure of the regularized product).** Under SNG-A11 with \(G,H\) connected and \(q\in(0,1)\) rational, fix rational \(s=a/b\) with \((r+1)s>1\), an integer \(N\), the cutoff \(P=N^b\) and \(\rho=N^{-a}=P^{-s}\). Let \(\ell_n,m_n\) be the local coefficients of \(G\) and \(H\) at \(q\) for \(n\le M\), \(A_n=\binom{n+k-1}{k-1}\), and \(S_M=(1-\rho)^{-k}-\sum_{n\le M}A_n\rho^n\). Put
\[
\begin{aligned}
T'&=\sum_{r<n\le M}|\ell_n-m_n|\rho^{n-r-1}+\frac{2S_M}{\rho^{r+1}},\\
D'&=\sum_{1\le n\le M}\max(\ell_n,m_n)\rho^{n-1}+\frac{S_M}\rho,\\
C'&=T'+|\delta|D'+\frac{|\delta|\rho^{r-1}}{2(1-\rho^r)}.
\end{aligned}
\]
For the finite summands, abbreviate
\[
\theta_p(s)=\delta\log(1-p^{-rs})
+\log\frac{B_G(p^{-s})}{B_H(p^{-s})}.
\]
Then
\[
\left|\log K_{G,H}(s,q)-\sum_{p\le P}\theta_p(s)\right|
\le C'\frac{P^{1-(r+1)s}}{(r+1)s-1},
\]
and each finite summand is enclosed by rational intervals computed from: integer-root enclosures of \(p^{-a/b}\); monotonicity of \(B\) in \(t\ge0\); the height tail of SNG-F39; outward-rounded sums over a checked tree decomposition; and series enclosures of logarithms.

*Proof.* \(L_G/L_H=B_G/B_H\) because the orders agree. The bound for omitted primes repeats the proof of (7.12) with sharper majorants. For \(0\le t\le\rho\), \(|L_G(t)-L_H(t)-\delta t^r|\le\sum_{n>r}|\ell_n-m_n|t^n\le T't^{r+1}\), using \(|\ell_n-m_n|\le2A_n\) beyond \(M\). Likewise \(\max(L_G,L_H)-1\le\sum_{n\ge1}\max(\ell_n,m_n)t^n\le D't\), using \(0\le\ell_n,m_n\le A_n\). Hence one regularized logarithm is at most \(C't^{r+1}\). Primes \(p>P\) satisfy \(p^{-s}<\rho\). Summing \(C'p^{-(r+1)s}\) over all integers \(p>P\) and applying the integral test gives the displayed bound. The finite enclosures were justified above: \(B_G\) has nonnegative coefficients, so it is increasing on \(t\ge0\), and rounding every product of nonnegative fixed-point numbers down (respectively up) gives a lower (respectively upper) bound. \(\square\)

`src/singularity/certified.py` implements the theorem with 256 fractional bits. The minimum-zero condition is carried as a flag in the bag messages, so no subtraction of enclosures occurs. For \(t=p^{-a/b}\) the factor \((1-t^r)\) is exact when \(b\mid ra\), in particular at \(s=1/r\). The retained results, with exact dyadic endpoints, are in `results/certified_k.json`. All are at \(q=1/2\). The spectral pair has \(r=2\), \(\delta=3/32\); the binary pair has \(r=3\), \(\delta=11025/262144\):

| Pair | \(s\) | Primes kept | Omitted log bound | \(K\) lower | \(K\) upper |
|---|---|---:|---:|---:|---:|
| spectral | \(1/2\) | 1229 (\(\le10^4\)) | \(4.6\times10^{-3}\) | 0.84973 | 0.85750 |
| spectral | \(3/5\) | 985 (\(\le6^5\)) | \(2.2\times10^{-4}\) | 0.89931 | 0.89971 |
| spectral | \(1\) | 168 (\(\le10^3\)) | \(1.1\times10^{-7}\) | 0.9678188 | 0.9678191 |
| binary | \(1/3\) | 2961 (\(\le30^3\)) | \(2.2\times10^{-2}\) | 0.90084 | 0.94230 |

The local height tails total below \(4\times10^{-16}\) in every run, so the width comes almost entirely from the omitted primes; arithmetic rounding is below \(10^{-60}\). With \(R=\zeta(rs)^\delta K\), the tables exhibit the proved branch singularity \((rs-1)^{-\delta}\) with an explicitly enclosed positive constant \(K(1/r,1/2)\). The singularity exponent is proved by SNG-A11, not fitted. Narrowing the binary interval needs either more primes or a smaller constant \(C'\); the bound decays only like \(P^{-1/3}\) at \(s=1/3\). A separate test checks the following. A run at a smaller cutoff with 160-bit arithmetic overlaps the \(s=1/2\) enclosure. Reversing the pair negates the finite log enclosure. Identical graphs give a log ratio enclosing zero.

Local factors themselves can also be enclosed by finitely many height coefficients. If \(L_N(t,q)=\sum_{n=0}^N\ell_n(q)t^n\), choose any \(t<R<1\). Then

\[
 0\le L(t,q)-L_N(t,q)
 \le (t/R)^{N+1}(1-R)^{-k}.
 \tag{7.14}
\]

Indeed each omitted term gains at most \((t/R)^{N+1}\), and the complete series at \(R\) is bounded by \((1-R)^{-k}\). Since \(L_N\ge1\), its logarithmic error is at most the same bound. Finite-prime and finite-height errors can thus be propagated separately and added in logarithmic coordinates. A numerical implementation claiming a rigorous enclosure must also bound its arithmetic rounding; the inequalities alone do not certify an unchecked floating-point product.

These results establish controllable local witnesses, arithmetic visibility, and finite approximation. They leave a genuine open inverse question: which graph distinctions are invisible to the entire univariate volume-marked local series? The examples show strict separations from specified coarser observations. They do not answer that complete question or establish historical priority for the construction.

## The complete binary comparison and the remaining elementary distinction

For the second reference pair, the common binary polynomial at each side size is small enough to display completely. Let \(C_j(q)=\sum_{|S|=j}q^{|\partial S|}\). Complementation gives \(C_j=C_{7-j}\), and the common values are

| Side sizes | Common cut-energy polynomial |
|---|---|
| \(0,7\) | \(1\) |
| \(1,6\) | \(2q+2q^2+2q^3+q^4\) |
| \(2,5\) | \(2q^2+8q^3+5q^4+4q^5+2q^6\) |
| \(3,4\) | \(q^2+4q^3+13q^4+10q^5+5q^6+2q^7\) |

Evaluating a row at \(q=1\) gives respectively \(1,7,21,35\), the appropriate binomial subset counts. This check does not prove equality of the polynomials, but it catches a missing subset in a proposed census. The actual equality is coefficientwise, obtained by evaluating each labeled subset against the original edges.

The edge joint-degree table identifies information the common binary census has merged. Entries not displayed are zero in both graphs.

| Unordered endpoint degrees | Edges in \(G\) | Edges in \(H\) |
|---|---:|---:|
| \((1,3)\) | 1 | 0 |
| \((1,4)\) | 1 | 2 |
| \((2,2)\) | 0 | 1 |
| \((2,3)\) | 3 | 2 |
| \((2,4)\) | 1 | 0 |
| \((3,3)\) | 0 | 1 |
| \((3,4)\) | 2 | 2 |

Both columns total eight edges. Collapsing endpoint degrees to their sum makes the tables agree: sums four, five, six, seven occur with multiplicities one, four, one, two. This explains agreement at volume two. Unequal heights two and one weight the endpoint degrees differently, through \(4d_u+d_v\), so the collapse no longer hides the difference. The height witness can therefore be understood without asserting an unexplained new source of graph information.

The distinction also lies in a specific span sector. Volume-three profiles of the form \(3e_v\) have span three and agree because degrees agree. Binary profiles have span one and agree because the full binary census agrees. The entire discrepancy (7.9) is consequently in span two. Retaining a span mark would isolate that sector directly. After setting the span mark to one, the same discrepancy survives, but the proof that it came from that sector uses the separate matched observations.

## A secondary boundary layer at an endpoint

The first-discrepancy exponent itself can become small near an endpoint. This produces a second controlled scaling law, now for graph ratios rather than the original synchronized partition function.

**Theorem SNG-A20 — endpoint scaling of visibility.** Suppose the polynomial local coefficients of two graphs agree below volume \(r\) for every \(q\in[0,1]\). Let \(q_*\in[0,1]\) be a value where the entire local series agree, and write \(\delta(q)=\ell_{G,r}(q)-\ell_{H,r}(q)\). Let \(q_j\to q_*\), \(\varepsilon_j\downarrow0\), with

\[
 \delta(q_j)\log(1/\varepsilon_j)\longrightarrow\tau\in\mathbb R.
\]

Then

\[
 R_{G,H}((1+\varepsilon_j)/r,q_j)\longrightarrow e^\tau.
 \tag{7.15}
\]

**Proof.** The normalized local ratio in (7.3) has its first \(r\) nonconstant coefficients canceled identically in \(q\). Its \(O(x^{r+1})\) estimate can be chosen uniformly on the compact weight interval. Therefore the regularized prime product is jointly continuous near \((1/r,q_*)\), by uniform convergence of the large-prime logarithmic tail and positivity of the finitely many remaining factors. At \(q_*\), every local ratio is one and \(\delta(q_*)=0\), so \(K(1/r,q_*)=1\). Finally

\[
 \log R=\delta(q_j)\log\zeta(1+\varepsilon_j)+\log K.
\]

The second term tends to zero, while \(\log\zeta(1+\varepsilon)-\log(1/\varepsilon)\to0\) and \(\delta\) stays bounded. This proves the limit. \(\square\)

For the volume-two pair, \(\delta_2(q)\sim4(1-q)^3\) as \(q\uparrow1\). For the volume-three pair, \(\delta_3(q)\sim144(1-q)^5\), because the final polynomial factor in (7.9) has value 36 at one. Thus \((1-q)^5\log(1/\varepsilon)\to t\) yields the ratio limit \(e^{144t}\) for the second pair at \(s=(1+\varepsilon)/3\). Near zero the corresponding leading behaviors are \(\delta_2\sim2q^2\) and \(\delta_3\sim q^3\). These are proved parameter scales for particular exact witnesses. They do not establish a universal exponent for all graph pairs.
