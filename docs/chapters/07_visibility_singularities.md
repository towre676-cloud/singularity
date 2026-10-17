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
 &\hspace{38mm}+6q^5+5q^6+2q^7+q^8).
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
