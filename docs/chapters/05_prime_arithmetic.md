# Prime arithmetic: assembling relational height populations

The height population becomes an arithmetic object when one integer height is assigned to every prime valuation. This step has a precise meaning. A vertex is no longer assigned one nonnegative integer; it is assigned a positive integer, whose exponent at each prime supplies a local height. The graph compares those exponents independently at each prime. Unique factorization then assembles the comparisons into an Euler product. No relation of the form \(n_u+n_v=n_w\) is imposed, and numerical closeness of two ordinary integers is not the quantity being measured. The construction records multiplicative disagreement, prime by prime.

Throughout this chapter, \(G=(V,E)\) is a finite loopless simple graph with \(k\ge2\) vertices. Connectedness is stated where needed. For a nonnegative height vector \(a\), write

\[
 |a|=\sum_{v\in V}a_v,\qquad
 E_G(a)=\sum_{\{u,v\}\in E}(a_u-a_v)^2,
 \qquad
 L_G(x,q)=\sum_{a\ge0}x^{|a|}q^{E_G(a)}.
\]

The coefficient of every fixed power of \(x\) is a polynomial in \(q\) with nonnegative integer coefficients. Thus this definition is meaningful formally before convergence is discussed. For numerical analysis we take \(0\le q\le1\), use \(0^0=1\), and initially require \(|x|<1\). At fixed volume \(n\), there are exactly \(\binom{n+k-1}{k-1}\) labeled profiles. Consequently

\[
 |L_G(x,q)|\le(1-|x|)^{-k}\qquad(|q|\le1).
\]

This elementary majorant will support every exchange of sums made below. The number of vertices, rather than the number of edges, controls this convenient uniform bound. Graph structure remains in the distribution of energy among profiles of the same volume.

## The arithmetic weight and its exact assembly

For a positive integer tuple \(n=(n_v)_{v\in V}\), define its relational valuation energy by

\[
 \mathcal E_G(n)=\sum_{p\ {
m prime}}
 E_G\bigl((v_p(n_v))_{v\in V}\bigr).
\]

Only finitely many terms are nonzero. The definition is invariant under simultaneously multiplying all coordinates by the same positive integer: this adds the same prime valuation to every local height and does not change any difference. Such multiplication does change the product \(\prod_vn_v\), so energy and size remain separate statistics. Define

\[
 Z_G(s,q)=\sum_{n_v\ge1}
 \frac{q^{\mathcal E_G(n)}}{(\prod_vn_v)^s}.
\]

**Theorem SNG-A01 — valuation assembly.** For \(0\le q\le1\) and \(\Re s>1\), the preceding Dirichlet series is absolutely convergent and

\[
 Z_G(s,q)=\prod_pL_G(p^{-s},q).
\]

**Proof.** Absolute values of the summands are bounded by \(\prod_vn_v^{-\sigma}\), where \(\sigma=\Re s\). Their sum is \(\zeta(\sigma)^k<\infty\). Restrict first to tuples supported on a finite set of primes. Unique factorization identifies such a tuple with one height vector for each of those primes. Its denominator factors as \(\prod_pp^{s|a(p)|}\), and its weight factors as \(\prod_pq^{E_G(a(p))}\). Multiplication of the finitely many absolutely convergent local series gives the finite Euler product. Increasing the finite prime set exhausts all tuples. Dominated convergence, or monotone convergence for real positive \(s\), proves the identity. The local estimate \(L_G(p^{-s},q)=1+O_G(p^{-\sigma})\) also establishes absolute convergence directly. \(\square\)

The theorem does not claim that arithmetic assembly creates extra information about the graph. The complete local series determines the Euler product. Its value is that it transfers a local relational statistic into an analytic language in which the first surviving distinction has a sharply identifiable singularity. Subsequent chapters prove that transfer rather than treating the Euler product as decoration.

Consider a single edge with heights \(a,b\). Its energy is \((a-b)^2\). At a prime dividing only one coordinate to exponent one, the local penalty is \(q\). A common factor at that prime contributes no penalty. A quotient with valuation difference two contributes \(q^4\), not \(q^2\). Thus the energy is more sensitive to repeated unequal valuation than a simple count of unmatched prime factors. The quadratic choice is part of the definition, not a claim that it is uniquely natural. Other edge costs can be studied, but their theorems require separate hypotheses.

## Removing the common factor exactly

Translation invariance of energy has a local and a global consequence. Locally it removes the common minimum height. Globally it removes the greatest common divisor of all coordinates. These are the same operation viewed through prime valuations.

**Theorem SNG-A02 — common-shift factorization.** Put

\[
 B_G(x,q)=\sum_{\substack{a\ge0\\\min_va_v=0}}x^{|a|}q^{E_G(a)}.
\]

Then, as a formal power series and for \(|x|<1\),

\[
 L_G(x,q)=\frac{B_G(x,q)}{1-x^k}.
\]

Equivalently, on the quotient lattice \(\mathbb Z^k/\mathbb Z\mathbf1\), define

\[
 \nu([a])=\sum_va_v-k\min_va_v.
\]

This function is well defined, and

\[
 B_G(x,q)=\sum_{[a]\in\mathbb Z^k/\mathbb Z\mathbf1}
 x^{\nu([a])}q^{E_G(a)}.
\]

**Proof.** Every nonnegative profile has a unique decomposition \(a=b+m\mathbf1\), with \(m=\min a\) and \(\min b=0\). Its energy equals \(E_G(b)\), and its volume is \(|b|+km\). Summing \(x^{km}\) over \(m\ge0\) gives the geometric factor. Every integer profile has a unique translate with minimum zero, which proves the quotient-lattice formula. \(\square\)

The quotient formula explains what the volume mark retains. The quadratic form \(E_G\) measures distances transverse to the constant direction. The function \(\nu\) additionally remembers the distinguished positive cone supplied by vertex coordinates. An abstract isometry of quadratic lattices need not preserve that function. Removing common shifts does not discard the order information; it records it on a canonical representative. This distinction is central when two unmarked energy distributions agree but their volume-marked distributions differ.

**Corollary SNG-A03 — primitive tuple factorization.** For \(\Re s>1\),

\[
 \frac{Z_G(s,q)}{\zeta(ks)}
 =\sum_{\substack{n_v\ge1\\\gcd(n_v:v\in V)=1}}
 \frac{q^{\mathcal E_G(n)}}{(\prod_vn_v)^s}
 =\prod_pB_G(p^{-s},q).
\]

**Proof.** Write every integer tuple uniquely as \(n_v=d\,m_v\), where the coordinates of \(m\) have common gcd one. Its energy is unchanged, and its denominator gains \(d^{ks}\). Alternatively, common gcd one says that at every prime the minimum coordinate valuation is zero, exactly the defining local condition for \(B_G\). Absolute convergence justifies both factorizations. \(\square\)

Here “primitive” means a common gcd of one. It does not mean pairwise coprime coordinates. A tuple can share a factor between two vertices while having no factor common to every vertex. Confusing these conditions would change the local population and invalidate the shift factor.

## Synchronization and independence as exact endpoints

At \(q=1\), all energy penalties disappear. At \(q=0\), only zero-energy profiles survive. For a connected graph these are precisely the constant profiles. Thus the same family interpolates between independent coordinates and complete synchronization, in an exact combinatorial sense.

**Theorem SNG-A04 — endpoint identities.** If \(G\) is connected, then

\[
 \begin{array}{c|c|c|c}
 q&L_G(x,q)&B_G(x,q)&Z_G(s,q)\\\hline
 1&(1-x)^{-k}&(1-x^k)(1-x)^{-k}&\zeta(s)^k\\
 0&(1-x^k)^{-1}&1&\zeta(ks).
 \end{array}
\]

The Euler products converge respectively for \(\Re s>1\) and \(\Re s>1/k\). If the graph has connected component sizes \(k_1,\ldots,k_c\), the synchronized endpoint is instead \(\prod_j\zeta(k_js)\).

**Proof.** Independence gives a geometric series for each vertex. At zero energy every edge has equal endpoint heights, and therefore heights are constant on each connected component. The arithmetic tuple is correspondingly constant on each component. The indicated geometric and zeta factors follow. \(\square\)

These endpoint identities require no limiting argument. A limit involving both \(q\) and \(s\) is a different problem because the singularity at \(s=1\) can amplify a small nonzero energy weight. Chapter 8 proves a uniform estimate that makes this distinction quantitative.

## Minimum cuts are the first arithmetic correction

Assume now that the graph is connected, and let \(\lambda(G)\) be its edge connectivity. A minimum cut is a nonempty proper vertex set whose edge boundary has size \(\lambda\). We count both sides: \(S\) and \(V\setminus S\) are separate height profiles and generally have different volumes.

**Theorem SNG-A05 — first positive energy.** Among nonconstant integer profiles, the least energy is \(\lambda\). Among minimum-zero profiles, the profiles of energy \(\lambda\) are exactly \(\mathbf1_S\) for minimum cuts \(S\). Consequently

\[
 [q^\lambda]B_G(x,q)=
 \sum_{\substack{\varnothing\ne S\subsetneq V\\|\partial S|=\lambda}}x^{|S|},
 \qquad [q^e]B_G=0\quad(0<e<\lambda).
\]

**Proof.** For an integer difference \(d\), \(d^2\ge|d|\). If \(a\) has minimum zero and span \(h\), then the discrete coarea identity gives

\[
 \sum_{\{u,v\}}|a_u-a_v|
 =\sum_{t=0}^{h-1}|\partial\{v:a_v>t\}|.
\]

Every level set in that sum is nonempty and proper, so \(E_G(a)\ge\lambda h\). A nonzero minimum-zero profile has \(h\ge1\). A binary minimum-cut profile attains energy \(\lambda\). If energy equals \(\lambda\), the bound forces \(h=1\), and the profile is the indicator of a minimum cut. \(\square\)

Write \(P(z)=\sum_pp^{-z}\) for the prime zeta function on its initial half-plane. The first positive energy coefficient now has an exact analytic description.

**Theorem SNG-A06 — minimum-cut prime-zeta coefficient.** Initially for \(\Re s>1\),

\[
 [q^\lambda]\log\frac{Z_G(s,q)}{\zeta(ks)}
 =\sum_{\substack{\varnothing\ne S\subsetneq V\\|\partial S|=\lambda}}
 P(|S|s).
\]

**Proof.** The constant coefficient in \(q\) of \(B_G\) is one, and there are no positive coefficients below degree \(\lambda\). Hence its first positive coefficient is unchanged by the formal logarithm. Apply Theorem SNG-A05 to \(\log B_G(p^{-s},q)\), and sum over primes. Absolute convergence on \(\Re s>1\), uniformly for \(q\) in a sufficiently small complex disk, justifies coefficient extraction. This uniformity also follows from the local majorant and the fact that each normalized factor equals one at \(q=0\). \(\square\)

A cut with a large side contributes at a different scaled argument than a cut with a small side. The coefficient therefore contains the sizes of oriented minimum-cut sides, not merely their number. It also identifies the scope of this first correction: it sees minimum cuts only. Higher energy coefficients mix larger cuts with profiles having several height levels. Extracting those sectors requires retained marks or additional identities; the first coefficient alone does not reconstruct the graph.

## Two small models that expose the retained information

For the graph consisting of a single edge, a minimum-zero profile is either \((0,0)\), \((h,0)\), or \((0,h)\), with \(h\ge1\). Thus there is a closed local formula

\[
 B_{K_2}(x,q)=1+2\sum_{h\ge1}q^{h^2}x^h,
 \qquad
 L_{K_2}(x,q)=\frac{1+2\sum_{h\ge1}q^{h^2}x^h}{1-x^2}.
 \tag{5.1}
\]

The exponent \(h^2\) records a genuinely unequal-height sector. Replacing it by \(h\) would give a different model even though the first positive-energy coefficient would agree. The first minimum-cut correction is \(2P(s)\): either coordinate can be the raised endpoint. At volume two the three original profiles are \((2,0),(1,1),(0,2)\), with energy histogram \(1+2q^4\). Normalization removes the common-shift profile \((1,1)\), leaving \(2q^4\). This small calculation separates labeled population counting, common-factor removal, and energy weighting without relying on a large graph example.

For the path on three vertices, choose its middle vertex as a root and write the edge differences as \(u=a_1-a_0\) and \(v=a_2-a_0\). There is one integer profile modulo common translation for every pair \((u,v)\in\mathbb Z^2\). Its minimum-zero volume is

\[
 \nu=u+v-3\min(0,u,v),
 \qquad E=u^2+v^2.
\]

Consequently

\[
 B_{P_3}(x,q)=\sum_{u,v\in\mathbb Z}
 q^{u^2+v^2}x^{u+v-3\min(0,u,v)}.
 \tag{5.2}
\]

The energy has independent coordinates, but the volume does not. The minimum couples them through which vertex is lowest. This is a direct elementary instance of metric information being simpler than order information. It also illustrates why a factorization of an unmarked theta series does not automatically factor its volume-marked refinement.

**Theorem SNG-A19 — all trees share the unmarked energy theta.** Let \(T\) be any tree with \(k\) vertices, and let

\[
 \vartheta(q)=\sum_{h\in\mathbb Z}q^{h^2}.
\]

For \(0\le q<1\),

\[
 B_T(1,q)=\vartheta(q)^{k-1}.
 \tag{5.3}
\]

**Proof.** Choose a root and orient every edge away from it. Sending a vertex profile modulo common integer translation to its \(k-1\) oriented edge differences is a bijection with \(\mathbb Z^{k-1}\). Injectivity follows by propagating equal differences along the unique root-to-vertex paths. Surjectivity follows by starting the root at zero and integrating the prescribed integer differences along those paths. Energy becomes the sum of squares of the independent edge differences. At \(x=1\), the minimum-zero representative introduces no extra weight, so the sum factors into \(k-1\) copies of \(\vartheta\). Absolute convergence follows from the convergent one-dimensional Gaussian series. \(\square\)

This is a useful family of exact collisions, not merely a single searched pair. Every tree of a fixed order has the same unmarked energy distribution. The marked series can already distinguish a four-vertex path from a four-vertex star at volume one: the first has degree polynomial \(2q+2q^2\), the second \(3q+q^3\). Their unmarked quadratic lattices agree, yet the coordinate cone places the lattice vectors into different volume layers. More demanding matched examples must remove this elementary degree explanation, but the family makes the logical source of the restored information unmistakable.

Connectedness matters to an unmarked specialization. If the graph has several components, removing one global common shift leaves independent relative component shifts of zero energy. The sum \(B_G(1,q)\) then diverges, even when \(q<1\). The local series at \(|x|<1\) remains perfectly well defined. On disconnected graphs it is preferable to normalize one common shift per component before setting the volume variable to one. Ordinary component factorization gives

\[
 L_G(x,q)=\prod_{j=1}^cL_{G_j}(x,q),
\]

while the single-shift normalized series is

\[
 B_G(x,q)=
 \frac{1-x^k}{\prod_j(1-x^{k_j})}\prod_jB_{G_j}(x,q).
\]

The remaining denominator is the exact record of those unconstrained relative shifts. This is an example where checking the meaning of a normalization prevents a misleading finite theta interpretation.
