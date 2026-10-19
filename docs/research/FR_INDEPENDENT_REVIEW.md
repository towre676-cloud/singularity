# Independent mathematical review of the frontier companion

This review separates mathematical consequences of complete generating series from evidence obtained from a finite coefficient prefix. It does not certify either general fixed-pinning completeness or the realization of a surviving symmetric-interface ambiguity.

## FR01: connected pole divisors

**Verdict: sound, subject to the stated connectedness and positive-parameter hypotheses.** Let \(G\) be connected of order \(n\), \(0<q<1\), and \(B_G=(1-x^n)L_G\). The previously established entire continuation of \(B_G\) is used, rather than asserted as a new result. At \(\zeta^n=1\), translation classes of integral heights can be represented either by their minimum-zero representative or by an anchored representative \(u\in\mathbb Z^{n-1}\). The volume phase is independent of the representative because translation changes volume by a multiple of \(n\). Therefore

\[
 B_G(\zeta,q)=\sum_{u\in\mathbb Z^{n-1}}
 \exp(-\beta u^TQ u)\exp(2\pi i\alpha^Tu),\qquad \beta=-\log q>0,
\]

where \(Q\) is the positive-definite reduced graph Laplacian and \(\alpha=(k/n)\mathbf1\) when \(\zeta=e^{2\pi i k/n}\). Poisson summation gives

\[
 B_G(\zeta,q)=\frac{(\pi/\beta)^{(n-1)/2}}{\sqrt{\det Q}}
 \sum_{m\in\mathbb Z^{n-1}}
 \exp\!\left[-\frac{\pi^2}{\beta}(m-\alpha)^TQ^{-1}(m-\alpha)\right]>0.
\]

The absolute convergence and strict positivity are immediate from positive definiteness. Consequently every \(n\)-th root is a genuine simple pole of \(L_G\), with residue \(-\zeta B_G(\zeta,q)/n\). Order one is covered by \(B_G=1\).

**The disconnected caveat is essential.** A different component numerator might vanish at a root that is not one of its own denominator roots. A sum of denominator pole orders is therefore not established at unrestricted positive \(q\). The implementation correctly refuses the general claim. The same-size component case is safe, including arbitrary isolated vertices, because every nontrivial component has the same denominator-root set and every isolated numerator is one.

The uniform zero-free certificate is sound: a spanning-tree difference parametrization gives

\[
 \sup_{|x|\le1}|B_H(x,q)-1|
 \le \vartheta(q)^{|H|-1}-1,
 \quad \vartheta(q)=\sum_{z\in\mathbb Z}q^{z^2}.
\]

Thus any rigorous upper bound \(U\ge\vartheta(q)\) with \(U^{N-1}<2\) excludes all unit-disc numerator zeros for all connected components of order at most \(N\). The scalar theta tail bound used in the code follows from successive exponent increments at least \(2T+3\) beyond index \(T+1\). Gaussian-box errors likewise dominate omitted spanning-tree difference assignments. Cyclotomic coefficient vectors are exact partial sums; their absolute-error bound concerns evaluation on the complex unit circle, not a coordinatewise positivity assertion.

## FR02: denominator reconstruction

**Verdict: sound, including composite denominator bases and uniform pinning.** For \(q=A/B\) in reduced form, \(0<A<B\), diagonal shift \(\lambda\ge0\) an integer, and \(\Lambda=\Delta+\lambda>0\), the maximum energy at volume \(R\ge2\) is

\[
 K=\Lambda R^2,
\]

achieved precisely by spikes on the \(m\) maximum-degree vertices. Every other profile has energy at most \(K-g\), with the valid universal gap

\[
 g=\min\{R^2,\,2\Lambda(R-1)\}.
\]

The minimum is necessary: a spike at a lower-degree vertex has gap only \(R^2\), which need not exceed \(2\Lambda(R-1)\). Non-spikes are bounded using \(E_G(h)+\lambda\sum h_i^2\le\Lambda\sum h_i^2\) and \(\sum h_i^2\le(R-1)^2+1\).

With \(B^{2(R-1)}>n\), we have \(B^g>n\ge m\), so

\[
 B^K a_R=mA^K+B^gT,\qquad T\in\mathbb Z.
\]

If \(\operatorname{ord}_B(m)=\max\{e:B^e\mid m\}\), then the least denominator-clearing depth \(k\) of \(a_R\) is exactly \(K-\operatorname{ord}_B(m)\). This does **not** require \(B\) to be prime. Prime-by-prime, it is the identity

\[
 \max_{p\mid B}\left\lceil\frac{K v_p(B)-v_p(m)}{v_p(B)}\right\rceil
 =K-\min_{p\mid B}\left\lfloor\frac{v_p(m)}{v_p(B)}\right\rfloor.
\]

Because \(\operatorname{ord}_B(m)<R^2\), the decoder recovers

\[
 \Delta=\left\lceil\frac{k}{R^2}\right\rceil-\lambda,
 \qquad
 m\equiv B^K a_R\,A^{-K}\pmod{B^g},\quad 1\le m\le n<B^g.
\]

The residue therefore determines \(m\) uniquely. The unpinned edgeless case \(\Lambda=0\) has integer coefficient equal to the number of compositions and must be treated separately; the implementation does so. Pinned edgeless graphs with \(\lambda=2\) instead have \(\Lambda=2,m=n\), and are handled by the general branch.

An independent implementation, written directly from compositions and graph edge energies rather than the new decoder, checked **450 exact cases**: every labeled graph of orders one through four, \(q=1/2,2/3,5/6\), and shifts zero and two. Every recovered maximum degree and multiplicity agreed. This is finite corroboration of the theorem, not a substitute for the gap proof.

The new module's input validation and final modular-divisibility clearing procedure were inspected. For denominator D>1, every supported prime exponent is smaller than D.bit_length(), so the modular-power support test uses a valid universal upper bound; divisibility is monotone and binary search returns the exact least clearing depth. The optional maximum-depth bound and D=1 case are handled correctly. The caller supplies graph order, family membership where used, and the actual coefficient; the decoder does not prove coefficient realizability. A logarithmic observation volume does not imply a cheap oracle for computing that coefficient.

## FR03: ordered tree positivity and distance

**Verdict: sound for the full ordered kernel and for product height boxes, with explicit failure under a simplex volume truncation.** For a tree, integrate every off-path branch into positive diagonal messages. The remaining terminal path is a product of Gaussian edge kernels and positive diagonal weights. The Gaussian factor is

\[
 q^{(s-t)^2}=q^{s^2}q^{t^2}\exp(2\beta st),\qquad \beta=-\log q>0.
\]

The exponential kernel is strictly totally positive. Cauchy–Binet preserves positivity under finite products with positive diagonals. A common box \(0\le h_v\le H\) has positive minors of order at most \(H+1\) when an internal path vertex exists. Increasing \(H\) gives the full kernel for \(0<x,q<1\); strict positivity persists because a fixed positive intermediate-index contribution supplies a uniform positive lower bound. Absolute convergence follows from domination by \((1-x)^{-(n-2)}\).

For consecutive terminal pins \(0,\ldots,k-1\), let \(d\) be terminal distance, \(c\) the number of edges leaving their unique path, \(S=k(k-1)/2\), and \(T=k(k-1)(2k-1)/6\). Exterior Cauchy–Binet has the unique minimum-volume intermediate index set \(\{0,\ldots,k-1\}\) at each internal path vertex. The Gaussian principal determinant is a Vandermonde product, giving the full hierarchy

\[
 \det[K(i,j)]_{i,j=0}^{k-1}
 =x^{(d-1)S}q^{cT}
 \left[\prod_{r=1}^{k-1}(1-q^{2r})^{k-r}\right]^d
 +O\!\left(x^{(d-1)S+1}\right).
\]

In particular the two-by-two determinant starts at volume \(d-1\), with coefficient \(q^c(1-q^2)^d\), so its first nonzero degree recovers terminal distance. Off-path contributions enter the leading coefficient only through the number of incident branch edges.

Two qualifications must remain explicit. First, an average of an ordered kernel and its transpose is not automatically totally positive, so this theorem is not directly a constraint on an arbitrary symmetrized interface. Second, global volume truncation can destroy positivity: for the four-vertex path truncated at interior volume one,

\[
 K_{\le1}(s,t)=q^{s^2+t^2}\{1+xq^2(q^{-2s}+q^{-2t})\},
\]

and its zero/one minor is \(-x^2q^2(1-q^2)^2<0\). This is a determinant of a truncated kernel, not the correctly truncated determinant of the full kernel. In particular its degree-two coefficient omits kernel degree-two contributions.

The path-message implementation was inspected. It preserves raw interior-volume weighting, leaves terminals unweighted by \(x\), and boxes every interior coordinate separately. Its preflight budget bounds scalar summands, not arbitrary-precision bit complexity.

## FR04: centered pinned theta limits

**Verdict on the mathematical statement: sound.** For a connected or disconnected finite graph, uniform real pinning \(\lambda>0\) makes \(L_G+\lambda I\) positive definite; connectedness is unnecessary. Write \(R=kn+r\), \(0\le r<n\), and \(z=h-k\mathbf1\). Then \(\sum z_i=r\), \(z_i\ge-k\), and

\[
 q^{-\lambda R^2/n}A_R
 =\sum_{\substack{z\in\mathbb Z^n,\ \sum z_i=r\\z_i\ge-k}}
 q^{E_G(z)+\lambda\sum_i(z_i-r/n)^2}.
\]

The summation domains increase with \(k\), so the normalized sequence converges monotonically to the affine root-lattice theta series on the sum-zero coset. Reflection gives residue symmetry \(r\leftrightarrow n-r\), using \(z\mapsto\mathbf1-z\) for \(r>0\) and \(z\mapsto-z\) for \(r=0\). Positive pinning controls Gaussian tails without a connectivity hypothesis.

Balanced profiles and the composition count give

\[
 q^{\lambda R^2/n+|E(G)|+\lambda n/4}
 \le A_R\le {R+n-1\choose n-1}q^{\lambda R^2/n},
 \qquad
 \lim_{R\to\infty}\frac{\log A_R}{R^2}=\frac{\lambda\log q}{n}.
\]

Thus the complete pinned series at known \(q,\lambda\) determines graph order, independently of a supplied order metadata field. Equality of the complete series implies equality of the affine theta limit packet; equality of the packet alone is not proved sufficient for complete-series equality. Exact rational arithmetic with \(q=t^{n^2}\) gives integral exponents when \(\lambda\) is an integer; arbitrary positive real \(\lambda\) is a theorem-level parameter, not automatically an exact-rational runtime input.

The FR04 implementation was independently inspected after it became available. Its reflection-friendly box \([-H,H+1]\) has the correct positive and negative first omitted Gaussian indices; the boundary enclosure uses the exact first omitted centered magnitude \(R+n\). Twenty-eight additional exact cross-checks on connected and disconnected graphs verified box nesting against a larger direct lattice window and checked subsequent residue-subsequence values against the boundary enclosure. All 32 then-current unit tests across FR01–FR04 passed with the source package on the Python path. These checks concern exact arithmetic and enclosure containment, not an empirical proof of the limiting theorem.

### FR04 rational affine lift at the working parameter

The additional affine-lift APIs remove any need to choose a special rational parameter. For every rational \(0<q<1\) and integer pinning \(\lambda>0\), define

\[
 \Psi_r(q)=\sum_{\substack{z\in\mathbb Z^n\\\sum z_i=r}}
 q^{E_G(z)+\lambda\|z\|^2}
 =q^{\lambda r^2/n}\Theta_r(q).
\]

For \(R=kn+r\), the exact rational normalized coefficient satisfies

\[
 q^{-\lambda(nk^2+2kr)}A_R(q)\uparrow\Psi_r(q).
\]

All exponents in the finite arithmetic are integers, including at the working parameter \(q=1/2\). Reflection gives \(\Psi_{n-r}=q^{\lambda(n-2r)}\Psi_r\) for canonical residues \(1\le r<n\). Residue zero reflects to charge \(n\), outside that canonical packet, so it should not be silently identified with a second residue-zero value.

The implementation uses the reflection-friendly product box \([-H,H+1]\). Its omitted one-coordinate positive and negative Gaussian tails start at magnitudes \(H+2\) and \(H+1\), respectively, exactly as coded. For a coefficient at \(R=kn+r\), the missing negative-coordinate tail starts at magnitude \(k+1\). Dropping the charge constraint and using a union bound with a rigorous one-dimensional Gaussian upper bound therefore gives the stated rational enclosure. A further **90 independent exact cases** across connected and disconnected graphs, \(q=1/2,2/3,5/6\), and pinning one and two checked nested boxes, boundary containment, subsequent normalized coefficients and reflected finite-box sums. No new runtime or proof correction was required.

## FR05: promised threshold-graph reconstruction

**Verdict on the inverse theorem: sound for the promised threshold family.** Fix a known order \(n\), rational \(q=A/B\in(0,1)\), and integer diagonal shift \(\lambda\ge0\). Choose one original volume \(R_*\ge2\) with \(B^{2(R_*-1)}>n\), and supply the coefficient prefix through \(R_*\). Every recursive smaller order satisfies that same cutoff, even as the diagonal shift increases.

A threshold graph has at most one nontrivial connected component, and that component has a universal vertex. Therefore if \(0<\Delta<n-1\), the number of isolated vertices is exactly \(k=n-\Delta-1\). Removing them divides the prefix by the unit series

\[
 f_\lambda(x)^k,\qquad f_\lambda(x)=\sum_{h\ge0}q^{\lambda h^2}x^h.
\]

If \(\Delta=n-1\), the multiplicity \(m\) recovered by FR02 is exactly the number of universal vertices. Write \(G=K_m\vee H\), let \(u\) be the universal-clique heights with sum \(j\), and let the residual heights have sum \(S\). The exact energy identity is

\[
 E_G+\lambda\|h,u\|^2
 =E_H+(m+\lambda)\|h\|^2
 +(n+\lambda)\|u\|^2-j^2-2jS.
\]

Hence, with

\[
 C_{m,j}=q^{-j^2}[z^j]
 \left(\sum_{u\ge0}q^{(n+\lambda)u^2}z^u\right)^m,
\]

and \(b_s=[x^s]F_{H,\lambda+m}\), the observed coefficients satisfy

\[
 a_R=\sum_{j=0}^R C_{m,j}q^{-2j(R-j)}b_{R-j},\qquad C_{m,0}=1.
\]

This is a unit lower-triangular transformation, so the entire required residual prefix is recovered recursively without increasing the observation volume. The residual graph remains threshold. The unpinned edgeless branch, the one-vertex branch, and the empty residual must be handled explicitly; the empty residual has formal series one and is not represented by the nonempty-graph constructor.

An independent implementation checked **378 exact cases**, covering all binary threshold constructions through six vertices, \(q=1/2,2/3,5/6\), and initial shifts zero and two. At each elimination step the transformed prefix was compared against direct weak-composition enumeration of the actual residual graph with its updated pinning. Every identity and decoded layer size agreed. The NX36 handoff was searched for threshold-graph reconstruction; this specific inverse theorem and its implementation are not among those packets.

The final implementation was inspected, including the iterative layer-peeling loop, canonical creation-word assembly, and exact empty residual check. Its original recursive depth limitation was removed before integration. All **42** unit tests across FR01–FR05 passed in the final scoped review.

The theorem proves completeness of this finite prefix **inside the promised threshold family**, rather than general graph completeness. The coefficient-computation oracle remains a separate cost. Series multiplication and inversion use \(O(nR_*^2)\) arithmetic operations in the direct implementation. The finalized FR02 helper replaces repeated gcd clearing with logarithmically many modular-divisibility tests in denominator bit length. Those modular tests and exact rational bit sizes must still be accounted for separately from the convolution count.

### FR05 corollary: one known raw closure reconstructs threshold interiors

The corollary was checked against the existing `charges.py` contract. Let the two nonadjacent terminals both dominate an interior \(H\) of known order \(n\). Its compressed sequence is exactly \(A_H=F_{H,2}\). For any supported known closing context \(C\), attached through those terminals with disjoint interiors, the existing operator satisfies

\[
 Z_C=T_C A_H,\qquad T_C\text{ unit lower triangular},
\]

and depends on \(C,n,q\), not the interior edges. Here \(Z_C\) is the **raw local series** of the glued graph. Its prefix through \(R_*\) recovers the same prefix of \(A_H\) by forward substitution. FR05 then reconstructs \(H\) in the promised threshold family. Consequently each one such context distinguishes every pair of nonisomorphic threshold interiors of the same known order by that volume cutoff. A terminal edge in the context is permitted because the dominating block's terminal edge is absent. No conversion to a minimum-zero normalized series is implicit in this corollary, and it does not establish reconstruction for arbitrary interiors. An independent end-to-end check counted raw closed-graph profiles directly for all threshold creation words through five interior vertices and three contexts (empty terminals, terminal edge, and one shared neighbor), then used the existing triangular inverse and FR05: all **93** cases reconstructed the original threshold interior.

## Classical source boundaries

The following are primary-source anchors for classical tools. They do not claim the project-specific graph consequences or arithmetic decoder.

* Christina Roehrig, *Siegel theta series for indefinite quadratic forms*, Research in Number Theory **7** (2021), article 45, section 4: <https://doi.org/10.1007/s40993-021-00272-y>. The proof uses Poisson summation and Fourier transforms of positive-definite Gaussian forms; our connected pole noncancellation argument is the direct positive-definite character specialization written above.
* Kenneth W. Johnson and Donald St. P. Richards, *Hyperdeterminantal Total Positivity*, SIGMA **21** (2025), 055: <https://doi.org/10.3842/SIGMA.2025.055>. Its discussion identifies the classical exponential kernel and Binet–Cauchy composition framework; the tree path, volume and leading-coefficient consequences above are derived separately.

* Persi Diaconis, Susan Holmes and Svante Janson, *Threshold Graph Limits and Random Threshold Graphs*, Internet Mathematics **5** (2008), 267–320: <https://doi.org/10.1080/15427951.2008.10129166>; preprint <https://arxiv.org/abs/0908.2448>. Its introductory characterizations supply the classical threshold-family structure used in FR05; the coefficient inverse and logarithmic observation cutoff are derived here.

## Overall conclusion

The companion supplies analytic, arithmetic and ordered-kernel constraints on proposed full-series collisions and graph realizations. It does not infer full-series equality from an arbitrary finite prefix, settle the three general frontiers, or change NX36 implementation and acceptance statuses.
