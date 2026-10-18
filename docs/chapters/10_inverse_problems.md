# Inverse problems and the depth of a height population

An invariant is a way of asking questions about an object while discarding its presentation. The inverse problem asks how much of the object can be recovered from the answers. For relational height populations, this question must be posed at several levels. A finite depth, the full marked series, an unmarked specialization, and a primewise Euler product are different data structures. Their relationships can be proved in some directions and remain open in others. Confusing them would replace a promising research question with an unsupported completeness claim.

The purpose of this chapter is to define those relationships and identify useful targets. The small examples show that the construction preserves some information absent from binary cut populations and the Laplacian spectrum. They do not tell us how many nonisomorphic graphs remain indistinguishable. In particular, a hierarchy can improve at one level and still stabilize long before it becomes complete. Determining whether that happens is a central mathematical task, rather than a detail to be deferred until after a universal reconstruction claim.

## Which equivalence is being studied?

Fix the number of vertices \(n\). Graphs are considered up to ordinary graph isomorphism, but every coefficient counts assignments on the original vertex set before relabeling. Let

\[
B_G(x,q,z)=\sum_{\min a=0}x^{|a|}q^{E_G(a)}z^{\max a}
\]

be the normalized marked series. We say that \(G\equiv_{\mathrm{mark}}H\) when these formal series agree. We say that \(G\equiv_{\mathrm{unmark}}H\) when their specializations at \(z=1\) agree. The latter is equivalent to equality of the unnormalized local series \(P_G\) for graphs of the same order, because \(B_G(x,q,1)=(1-x^n)P_G(x,q)\). These are definitions, not claims that either relation is graph isomorphism.

For an integer \(D\ge0\), define the depth-\(D\) population by

\[
B_G^{\le D}(x,q,z)=\sum_{h=0}^{D}z^h[z^h]B_G(x,q,z).
\]

Equality of these finite polynomials is written \(G\equiv_DH\). The depth is the largest height span retained; it is not the total volume and is not an iteration count in a numerical algorithm. For fixed \(D\), every coordinate lies between zero and \(D\), at least one coordinate is zero, and the number of assignments is exactly \((D+1)^n-D^n\). Thus each depth comparison is a finite exact question.

**Proposition SNG-I001: hierarchy implications.** Graph isomorphism implies marked equality. Marked equality implies equality at every finite depth and implies unmarked equality. Equality at depth \(D+1\) implies equality at depth \(D\). Conversely, equality at every finite depth implies equality of the full marked series, because every individual coefficient has a finite span. These statements follow directly from coefficient extraction and specialization. No converse from unmarked equality to marked equality is asserted.

The first depth is precisely the binary cut sector, after its two constant assignments are restored. If

\[
C_G(x,q)=\sum_{S\subseteq V}x^{|S|}q^{|\partial S|},
\]

then

\[
C_G(x,q)=1+x^n+[z]B_G(x,q,z).
\tag{SNG-I002}
\]

The term one is the empty subset and the term \(x^n\) is the full subset. Both have zero boundary. The normalized span-one population excludes them because a representative must attain both zero and one. The binary pair in the preceding chapter agrees at depth one and differs at depth two, proving that this particular hierarchy step is strict. This is a theorem about the defined hierarchy, supported by an exact counterexample to equality of its first two levels.

For two graphs define their first marked distinguishing depth by

\[
d_{\mathrm{span}}(G,H)=\min\{D:G\not\equiv_DH\},
\]

with value infinity when no finite depth distinguishes them. One may separately define a first distinguishing volume by the smallest \(r\) at which a coefficient of \(x^r\) differs. The two measures answer different questions. A large span can be concentrated on one vertex, while a low span can involve many vertices. The binary pair has distinguishing span two and distinguishing volume three. Its difference at volume three belongs specifically to span two; it is not evidence that every depth-two distinction must first occur at volume three.

## Why retaining labels makes reconstruction easy

The intended inverse problem is difficult because vertex labels have been summed out. It is important to explain why a seemingly stronger multivariate formulation would trivialize part of that question. Define the fully labeled local series

\[
\mathscr P_G(x_1,\ldots,x_n;q)
=\sum_{a\in\mathbb N^n}q^{E_G(a)}\prod_i x_i^{a_i}.
\]

Its singleton coefficient is \([x_i]\mathscr P_G=q^{d_i}\), so it determines the degree of every named vertex. Its coefficient at two distinct variables is

\[
[x_ix_j]\mathscr P_G=q^{d_i+d_j-2\epsilon_{ij}}.
\]

The exponent therefore reveals whether the named pair is an edge. This proves **Proposition SNG-I003**: the labeled formal series determines the entire labeled graph using coefficients of total degree at most two. A formal parameter avoids questions of numerical recognition. At a fixed exact real \(q\in(0,1)\), the distinct integer powers are also distinct, but a floating-point implementation should not be substituted for that exact statement without an error analysis.

This easy reconstruction is not the problem Singularity is claiming to solve. The specialization \(x_1=\cdots=x_n=x\) combines many assignments into one volume class. Individual pair identities disappear, and their relational distribution remains. The challenge is to recover a graph from that distribution without quietly reintroducing one coordinate variable per vertex. This distinction also explains why a large formal generating function need not supply an efficient isomorphism algorithm. One can encode the adjacency matrix in a generating function almost immediately; the mathematical question is what survives a specified loss of labels.

## Universal relations within each depth

Several identities are available before any difficult inverse problem is solved. They constrain every valid output and reveal how the hierarchy is organized. They also provide exact checks that are different from merely running the same enumeration twice.

**Proposition SNG-I004: span reflection.** Put \(B_{G,h}(x,q)=[z^h]B_G(x,q,z)\). Then

\[
B_{G,h}(x,q)=x^{nh}B_{G,h}(x^{-1},q).
\]

For a normalized assignment of span \(h\), the reflected assignment \(a'_i=h-a_i\) again has minimum zero and maximum \(h\). Every edge difference changes sign, so energy is unchanged, while volume becomes \(nh-|a|\). Reflection is an involution, proving the identity coefficient by coefficient. For \(h=1\), this is the usual complement symmetry of binary cuts. For the seven-vertex binary pair, its proved \(x^3z^2\) difference therefore also occurs at \(x^{11}z^2\), since \(14-3=11\). This second location follows from a bijection, not from a new empirical claim.

For \(h\ge1\), an assignment of exact span \(h\) has at least one coordinate zero and at least one equal to \(h\). Consequently its volume lies between \(h\) and \((n-1)h\). Its energy is an integer between zero and \(|E|h^2\). If the graph is connected and \(h>0\), the energy is positive. These bounds make \(B_{G,h}\) a finite polynomial with explicitly bounded support. The reflection center \(nh/2\) is consistent with the two volume bounds.

There is an inclusion-exclusion construction that does not require enforcing minimum and maximum conditions separately in a transfer algorithm. Define

\[
T_{G,h}(x,q)=\sum_{a\in\{0,\ldots,h\}^n}x^{|a|}q^{E_G(a)},
\qquad T_{G,-1}=0.
\]

For \(h\ge1\), shift invariance of energy gives

\[
B_{G,h}=T_{G,h}-(1+x^n)T_{G,h-1}+x^nT_{G,h-2}.
\tag{SNG-I005}
\]

Assignments missing the top height contribute \(T_{G,h-1}\). Assignments missing zero can be shifted down by one, contributing \(x^nT_{G,h-1}\). Assignments missing both endpoints have been subtracted twice and contribute \(x^nT_{G,h-2}\). The formula holds for every graph because only common-shift invariance was used. At \(q=1\), it reduces to a universal volume polynomial independent of graph edges. In particular,

\[
B_{G,h}(1,1)=(h+1)^n-2h^n+(h-1)^n.
\]

Summing through depth \(D\) gives \((D+1)^n-D^n\), as required. At unmarked \(q=1\), one obtains the further check

\[
B_G(x,1,1)=\frac{1-x^n}{(1-x)^n}.
\]

These identities explain why all examples coincide when energy is forgotten. A successful distinguishing polynomial must vanish at that specialization. They also clarify why a zero at \(q=1\) is a necessary population constraint, rather than evidence by itself of a special physical or cyclotomic mechanism.

## Connected components and exact recovery at zero parameter

Disconnected graphs require a different normalization argument from connected graphs. Energy zero means that height is constant on each connected component, not that all vertices share a common height. If the component sizes are \(n_1,\ldots,n_c\), then

\[
P_G(x,0)=\prod_{j=1}^c\frac1{1-x^{n_j}},
\qquad
Z_G(s,0)=\prod_{j=1}^c\zeta(n_js).
\tag{SNG-I006}
\]

This statement follows by assigning an arbitrary nonnegative common height to each component. It includes isolated vertices, whose factors are \((1-x)^{-1}\) and \(\zeta(s)\). It shows why the connected-graph claim that the zero-parameter value is finite at \(s=1\) cannot be copied unchanged to a graph with isolated vertices.

**Proposition SNG-I007: the zero-parameter local series determines the multiset of component sizes.** Let \(m_d\) be the number of components of size \(d\), and put \(b_r=r[x^r]\log P_G(x,0)\). Expanding the logarithm gives

\[
b_r=\sum_{d\mid r}d\,m_d.
\]

Möbius inversion yields

\[
m_n=\frac1n\sum_{d\mid n}\mu(n/d)b_d.
\]

All operations here are formal power-series operations; no analytic continuation is needed. This recovers component sizes, not the internal graph on each component. Within a fixed connected component size, all connected graphs have the same zero-energy population.

For unmarked populations, ordinary disjoint union gives \(P_{G\sqcup H}=P_GP_H\). The globally normalized marked population does not simply factor as \(B_GB_H\): the two components may be shifted by different heights before their common global minimum is removed, and the global span depends on those relative shifts. A depth algorithm must retain this information or work first with the bounded boxes \(T_{G,h}\), which do multiply over disjoint components, and then use the inclusion-exclusion formula. Treating marked disjoint union as an automatic product would erase legitimate assignments.

## Easy classes and the limits of degree information

The first local coefficient is the degree polynomial \(c_G(q)=\sum_vq^{d_v}\). It determines the degree multiset, because its coefficient of \(q^d\) is the number of degree-\(d\) vertices. This immediately resolves several inverse questions under explicit class assumptions. Such small results are useful calibration points; they must not be expanded into a claim about arbitrary graphs with the same degree sequence.

For a star \(K_{1,n-1}\),

\[
c_G(q)=(n-1)q+q^{n-1}.
\]

For a path \(P_n\) with \(n\ge3\),

\[
c_G(q)=2q+(n-2)q^2.
\]

The two polynomials differ for \(n\ge4\), while the three-vertex star and path are the same graph. A degree multiset consisting of one degree-\(n-1\) vertex and \(n-1\) leaves forces the star even without a prior star-family promise. A connected graph whose vertices all have degree two is a cycle, so the degree polynomial determines it within that connected class. If connectedness is omitted, a disjoint union of cycles has the same degree polynomial for every partition of the total order into allowed cycle lengths. The zero-parameter component-size series then resolves those different cycle decompositions.

A connected tree of maximum degree at most two is a path: there can be no branch and no cycle. Complete graphs and edgeless graphs are also forced by their degree multisets. Within the family of complete bipartite graphs, the polynomial \(a q^b+b q^a\) determines the unordered pair of part sizes \(\{a,b\}\). This last statement has a family restriction. Other graph families may share that degree sequence, so the polynomial by itself does not certify complete bipartiteness.

The early coefficients become less informative on regular graphs. If \(G\) is \(d\)-regular on \(n\) vertices with \(m=nd/2\), then

\[
A_2=nq^{4d}+m q^{2d-2}
+\left(\binom n2-m\right)q^{2d}.
\]

Thus no two \(d\)-regular graphs of the same order can be distinguished at volume two. At volume three, the ordered \(2+1\) sector is

\[
2m q^{5d-4}+\bigl(n(n-1)-2m\bigr)q^{5d}.
\]

The remaining binary triple sector depends on the numbers \(N_j\) of three-vertex subsets spanning exactly \(j\) edges. If \(T=N_3\) is the triangle count, then

\[
N_2+3T=n\binom d2,
\qquad N_1+2N_2+3T=m(n-2),
\]

\[
N_0+N_1+N_2+T=\binom n3.
\]

These identities count wedges, edge-containing triples, and all triples. They show that \(n,d,T\) determine every \(N_j\). Therefore **Proposition SNG-I008** states that regular graphs with the same order, degree and triangle count have identical marked coefficients through total volume three. This result supplies a useful negative prediction for searches. The heterogeneous degrees of the displayed binary pair are part of why an ordered height pattern can distinguish it so early.

There are also useful support bounds on the coefficients at arbitrary volume. Suppose the graph is connected on \(n\ge2\) vertices, with maximum degree \(d_{\max}>0\) and edge connectivity \(\lambda\). For a nonnegative assignment of volume \(r\),

\[
E_G(a)=\sum_i d_i a_i^2-2\sum_{ij\in E}a_ia_j
\le d_{\max}\sum_i a_i^2\le d_{\max}r^2.
\]

The upper bound is attained by placing all height \(r\) at a maximum-degree vertex. For \(r\ge1\), equality in \(\sum_i a_i^2\le r^2\) requires that only one coordinate be positive. Therefore the coefficient of the highest possible energy \(q^{d_{\max}r^2}\) in \([x^r]P_G\) is exactly the number of maximum-degree vertices. This is **Proposition SNG-I009**, an exact boundary constraint on every local population. It should not be mistaken for a new distinguishing statistic: it is already determined by the first coefficient's degree data.

For a normalized nonzero assignment, let \(h=\max a\). The threshold-cut identity and integrality give \(E_G(a)\ge\lambda h\). At least one coordinate is zero, so \(r\le(n-1)h\). Consequently every occupied coefficient of the normalized population at positive volume satisfies

\[
E_G(a)\ge\lambda\left\lceil\frac r{n-1}\right\rceil.
\]

This lower bound is easy to evaluate and does not require solving an optimization problem over all assignments. It is not asserted to be sharp at every volume. A spectral bound can be stronger at large volume: if \(\lambda_2\) is the first nonzero Laplacian eigenvalue, subtract the mean of \(a\) to obtain

\[
E_G(a)\ge\lambda_2\left(\sum_i a_i^2-\frac{r^2}n\right)
\ge\frac{\lambda_2r^2}{n(n-1)}.
\]

The last step follows because a zero coordinate leaves at most \(n-1\) nonzero coordinates and Cauchy's inequality gives \(\sum_i a_i^2\ge r^2/(n-1)\). These inequalities connect familiar spectral control to the support of the new population without equating the two objects. They help delimit an exact search region, while the examples show that knowledge of the spectrum does not determine the multiplicities within that region.

## A family with exactly controlled visibility depth

The decorated-deck criterion SNG-F17 asks whether nonisomorphic graphs can agree through arbitrarily large volume. They can, with an explicit discrepancy. For \(\ell\ge2\) and \(1\le j\le\ell\), let \(G_{\ell,j}\) be the cycle \(C_{2\ell}\) on \(0,\ldots,2\ell-1\) with a leaf \(u\) attached at vertex \(0\) and a leaf \(w\) attached at vertex \(j\). The graphs have \(n=2\ell+2\) vertices, the same degree sequence and the same multiset of endpoint-degree types on edges when \(j\ge2\). Their cut lattices are isometric: each is the cut lattice of \(C_{2\ell}\) orthogonally summed with \(\mathbb Z^2\) for the two pendant edges, whose differences are free. So the energy theta series that forgets volume is identical. They are not cospectral in general.

**Theorem SNG-F36 (exact visibility depth for pendant cycles).** For \(2\le p<\ell\), the graphs \(G_{\ell,p}\) and \(G_{\ell,\ell}\) have equal local, normalized and span-marked coefficients at every volume \(m\le p\), and
\[
[x^{p+1}]\bigl(L_{G_{\ell,p}}-L_{G_{\ell,\ell}}\bigr)=q^2(1-q)^2(1-q^2)^p .
\]
The discrepancy at volume \(p+1\) lies entirely in span one. More precisely, the complete binary-sector difference is
\[
\sum_{S\subseteq V}z^{|S|}\bigl(q^{c_{G_{\ell,p}}(S)}-q^{c_{G_{\ell,\ell}}(S)}\bigr)
=q^2(1-q)^2(1-q^2)^p\,z^{p+1}(1-z)^2\,U_{\ell-p}(z,q)^2,
\]
where \(U_0=0\), \(U_1=1\) and \(U_k=(1+z)U_{k-1}-z(1-q^2)U_{k-2}\). The binary formula holds for \(1\le p<\ell\).

*Proof.* **Binary sector.** Summing over the leaves first: if its attachment vertex is outside \(S\), a leaf contributes \(1+zq\); if inside, \(q+z=(1+zq)-(1-q)(1-z)\). Write \(\phi(s)=\phi_0-(1-q)(1-z)s\) for \(s\in\{0,1\}\). With \(N=2\ell\), \(T=\begin{pmatrix}1&q\sqrt z\\ q\sqrt z&z\end{pmatrix}\) and \(\Pi=\operatorname{diag}(0,1)\), the cycle part of the binary polynomial with both vertices \(0\) and \(j\) in \(S\) is \(\Gamma(j)=\operatorname{tr}(\Pi T^j\Pi T^{N-j})\). Terms with fewer marked vertices in \(S\) do not depend on \(j\), by rotation and reflection of the cycle. Hence the difference is \((1-q)^2(1-z)^2(\Gamma(p)-\Gamma(\ell))\). With orthonormal eigenvectors \(v_\pm\) and eigenvalues \(\lambda_\pm\) of \(T\),
\[
\Gamma(j)=\sum_{a,b\in\{\pm\}}(v_a)_2^2(v_b)_2^2\lambda_a^j\lambda_b^{N-j}.
\]
The diagonal terms do not depend on \(j\), and \((v_+)_2^2(v_-)_2^2=\beta^2/(\lambda_+-\lambda_-)^2\) for the off-diagonal entry \(\beta=q\sqrt z\). So
\[
\Gamma(p)-\Gamma(\ell)=\frac{q^2z}{(\lambda_+-\lambda_-)^2}\bigl(\lambda_+^p\lambda_-^{N-p}+\lambda_-^p\lambda_+^{N-p}-2(\lambda_+\lambda_-)^\ell\bigr)
=q^2z\,(\lambda_+\lambda_-)^pU_{\ell-p}^2,
\]
with \(\lambda_+\lambda_-=\det T=z(1-q^2)\) and \(U_k=(\lambda_+^k-\lambda_-^k)/(\lambda_+-\lambda_-)\). This satisfies the stated recurrence, since \(\lambda_++\lambda_-=1+z\). Since \(U_k=1+O(z)\), the lowest term is \(q^2(1-q)^2(1-q^2)^pz^{p+1}\).

**Decorated decks of size at most \(p\).** Let \(S\) have \(t\le p\) vertices. Each component of \(G_{\ell,j}[S]\) is either an isolated leaf whose attachment vertex is outside \(S\), or an arc of the cycle with the leaves of its marked vertices that lie in \(S\). An arc containing both marked vertices would need at least \(p+1\) cycle vertices for \(j=p\) and \(\ell+1\) for \(j=\ell\), so each arc contains at most one. The degree-decorated type of \(S\) is therefore a multiset of components of three kinds: free arcs, which contain no marked vertex and are recorded by their lengths; marked arcs, recorded by length, the offset of the degree-three vertex and whether its leaf is present; and isolated leaves. The two marked vertices are interchangeable, each having degree three and one leaf. Fix a type \(\tau\) and an assignment of its marked components to the two marked vertices; then the marked arcs are placed. The free arcs, of total length \(F\) in \(k\) blocks, must be placed pairwise non-adjacent, avoiding the marked vertices and non-adjacent to the marked arcs, in the two segments between the marked regions. Let \(\alpha_1,\alpha_2\) be the segment lengths after removing one obligatory gap next to each marked arc. Placing labeled blocks in one segment of effective length \(\alpha\) has \(k!\binom{\alpha-F+1}{k}\) solutions up to the labeling convention, so the two-segment count is a sum over splits of the blocks of products of binomials.

*Placement lemma.* This sum is a function of \(\alpha_1+\alpha_2\) alone whenever \(\alpha_1,\alpha_2\ge F-1\). Gluing the segments with one separator vertex identifies the count with placements in a line of length \(\alpha_1+\alpha_2+1\), which depends only on the sum, minus placements in which some block covers the separator. The latter decompose, block by block and offset by offset, into the same two-segment problem with one block fewer. By induction on \(k\), the count is a function of the sum once both lengths are at least \(F\). As a polynomial identity in \((\alpha_1,\alpha_2)\) it then holds everywhere. For \(\alpha_i\ge F-1\) every binomial \(\binom{\alpha_i-F_I+1}{|I|}\) has a nonnegative upper argument, so it equals the true count.

For \(G_{\ell,\ell}\) both segments come from arcs with \(\ell-1\ge p\) interior vertices. For \(G_{\ell,p}\) the short arc has \(p-1\) interior vertices, and the marked arcs remove at most \((t-F)\) of them together with their gaps, so \(\alpha_1\ge p-1-(t-F)\ge F-1\); the long arc is larger. The same counting shows that the marked arcs fit in both graphs whenever \(t\le p\). The sum \(\alpha_1+\alpha_2\) depends only on \(\tau\) and the assignment, so both graphs have the same number of subsets of each decorated type and size \(t\le p\).

**Conclusion.** SNG-F17 gives equality of local and marked coefficients through volume \(p\). At volume \(p+1\), its proof matches every profile whose support has at most \(p\) vertices. The remaining profiles have \(p+1\) support vertices and volume \(p+1\), so they are binary. Their difference is the \(z^{p+1}\) coefficient above, and these subsets are proper because \(p+1<n\). \(\square\)

Taking \(\ell=p+1\) gives \(n=2p+4\) and visibility depth \(p+1=(n-2)/2\), linear in the order. The theorem is unconditional and explicit, and it answers the first question raised after SNG-F17. It is not a uniform statement about all graph pairs of a given order.

**Theorem SNG-F37 (sign and monotonicity of the pendant discrepancy).** For real \(0<x<1\) and \(0<q<1\), and \(1\le j\le j'\le\ell\),
\[
L_{G_{\ell,j}}(x,q)\ge L_{G_{\ell,j'}}(x,q).
\]

*Proof.* Let \(f(h)=\sum_{b\ge0}x^bq^{(b-h)^2}\) be the leaf factor, bounded by \(1/(1-x)\). Let \(T\) be the operator on \(\ell^2(\mathbb Z_{\ge0})\) with kernel \(x^{(h+h')/2}q^{(h-h')^2}\). It is Hilbert–Schmidt, and it is positive semidefinite because \(q^{(h-h')^2}=e^{-c(h-h')^2}\) with \(c=-\log q>0\) is a positive-definite Gaussian kernel, and conjugating by the diagonal \(x^{h/2}\) preserves this. Summing over leaf heights and then over cycle heights gives \(L_{G_{\ell,j}}=\operatorname{tr}(FT^jFT^{N-j})\) with \(F=\operatorname{diag}(f)\). In an orthonormal eigenbasis, with \(\lambda_a\ge0\) and \(F_{ab}=\langle v_a,Fv_b\rangle\), the absolutely convergent expansion is
\[
L_{G_{\ell,j}}=\tfrac12\sum_{a,b}F_{ab}^2\bigl(\lambda_a^j\lambda_b^{N-j}+\lambda_b^j\lambda_a^{N-j}\bigr).
\]
For \(\lambda_a,\lambda_b\ge0\) the bracket \(\varphi(j)\) satisfies \(\varphi(j)-\varphi(j+1)=(\lambda_a\lambda_b)^j(\lambda_b^{N-2j-1}-\lambda_a^{N-2j-1})(\lambda_b-\lambda_a)\ge0\) for \(j<\ell\). \(\square\)

In particular \(L_{G_{\ell,p}}-L_{G_{\ell,\ell}}=\frac12\sum F_{ab}^2(\lambda_a\lambda_b)^p(\lambda_a^{\ell-p}-\lambda_b^{\ell-p})^2\) is a sum of squares, consistent with the positive leading coefficient. The arithmetic ratio of SNG-A11 therefore has exponent \(\delta=q^2(1-q)^2(1-q^2)^p>0\) at \(s=1/(p+1)\) for every \(q\in(0,1)\). This exponent is largest at the root \(q_p^*=2/(1+\sqrt{4p+9})\) of \(1-q-(p+2)q^2\), where \(q_p^*\sim p^{-1/2}\) and \(\delta_p(q_p^*)\sim1/(ep)\), whereas \(\delta_p(1/2)=3^p/4^{p+2}\) decays exponentially. Choosing the probe parameter thus turns an exponentially weakening signal into one of inverse-depth size.

The implementation is `src/singularity/families.py`. `tests/test_families.py` and `results/pendant_family.json` check the following: the first difference by weak-composition enumeration for all \(2\le p<\ell\le7\); the closed binary form against complete subset enumeration for \(1\le p<\ell\le7\); and equality of decorated decks for every size up to \(p\), with inequality at \(p+1\), on six pairs. They also check the optimal-probe equation exactly.

## Terminal kernels and the Whitney twist

A **block** is a graph \(G\) with an ordered tuple \(\mathbf s=(s_1,\ldots,s_k)\) of distinct terminal vertices. Write \(I=V\setminus\mathbf s\). Its **terminal kernel** is the family of series
\[
K_G(\mathbf b;x,q)=\sum_{a_I\ge0}x^{\sum_{i\in I}a_i}\,q^{E_G(a_I,\mathbf b)},\qquad\mathbf b\in\mathbb Z_{\ge0}^k,
\]
where \(E_G(a_I,\mathbf b)\) is the energy of the profile equal to \(\mathbf b\) on the terminals and to \(a_I\) inside. Kernels retain terminal heights and interior volume separately, so they compose.

**Theorem SNG-F41 (gluing and the Whitney twist).** Let \((G_1,\mathbf s)\) and \((G_2,\mathbf t)\) be blocks with \(k\) terminals that share no edge, and let \(G_1\cup_\pi G_2\) identify \(s_i\) with \(t_{\pi(i)}\) for a permutation \(\pi\). Then
\[
L_{G_1\cup_\pi G_2}(x,q)=\sum_{\mathbf b}x^{|\mathbf b|}K_{G_1}(\mathbf b)\,K_{G_2}(\pi\cdot\mathbf b).
\]
For \(k=2\), put \(A_j(b_1,b_2)=\frac12\bigl(K_{G_j}(b_1,b_2)-K_{G_j}(b_2,b_1)\bigr)\). Then the straight and twisted gluings satisfy
\[
L_{G_1\cup G_2}-L_{G_1\cup_{\mathrm{tw}}G_2}=2\sum_{\mathbf b}x^{|\mathbf b|}A_1(\mathbf b)A_2(\mathbf b).
\]
In particular the twist is invisible at every volume if either kernel is symmetric, for instance if a block has an automorphism exchanging its terminals.

*Proof.* A profile on the glued graph is a choice of terminal heights \(\mathbf b\) and independent interior profiles of the two blocks. Its volume is \(|\mathbf b|\) plus the two interior volumes. Each edge lies in exactly one block, so its energy is the sum of the two block energies. Summing gives the gluing formula. For \(k=2\) write \(K_j=S_j+A_j\) with \(S_j\) symmetric under exchanging the coordinates of \(\mathbf b\). The weight \(x^{|\mathbf b|}\) is symmetric, so \(\sum_{\mathbf b}x^{|\mathbf b|}F(\mathbf b)=0\) for every antisymmetric \(F\). Expanding \((S_1+A_1)(S_2+A_2)-(S_1+A_1)(S_2-A_2)=2S_1A_2+2A_1A_2\) and dropping the antisymmetric \(S_1A_2\) proves the identity, coefficient by coefficient in \(x\). \(\square\)

**Theorem SNG-F42 (twisting identical blocks).** Let \(G_1=G_2=G\) with terminals \((s,t)\). Write \(2A(\mathbf b)=\sum_vx^vP_{\mathbf b,v}(q)\) with \(P_{\mathbf b,v}\in\mathbb Z[q]\), and let \(v_{\mathbf b}\) be the least \(v\) with \(P_{\mathbf b,v}\ne0\). If \(A\not\equiv0\), the straight and twisted self-gluings first differ at volume
\[
\mu=\min_{\mathbf b}\bigl(|\mathbf b|+2v_{\mathbf b}\bigr),\qquad
[x^\mu]\bigl(L_{G\cup G}-L_{G\cup_{\mathrm{tw}}G}\bigr)=\tfrac12\sum_{|\mathbf b|+2v_{\mathbf b}=\mu}P_{\mathbf b,v_{\mathbf b}}^2\ne0 .
\]
For real \(0<x<1\) and \(0<q<1\), \(L_{G\cup G}\ge L_{G\cup_{\mathrm{tw}}G}\).

*Proof.* By SNG-F41 the difference is \(\frac12\sum_{\mathbf b}x^{|\mathbf b|}(2A(\mathbf b))^2\). A term \(x^{|\mathbf b|+v+v'}P_{\mathbf b,v}P_{\mathbf b,v'}\) is nonzero only if \(v,v'\ge v_{\mathbf b}\), so it has volume at least \(|\mathbf b|+2v_{\mathbf b}\ge\mu\). At volume \(\mu\) only \(v=v'=v_{\mathbf b}\) with \(|\mathbf b|+2v_{\mathbf b}=\mu\) survives. A finite sum of squares of nonzero real polynomials is not the zero polynomial. For real parameters in the unit square every kernel converges absolutely, being dominated by \(L_G\), so the difference is a convergent sum of squares of real numbers. \(\square\)

The pendant-cycle family is an instance. Let \(B_{m,k}\) be the path of length \(2m\) from \(s\) to \(t\) with a leaf at distance \(k<m\) from \(s\). Gluing it to itself gives \(C_{4m}\) with leaves \(2k\) apart, and the twist gives leaves \(2m\) apart. These are \(G_{2m,2k}\) and \(G_{2m,2m}\) of SNG-F36. SNG-F42 then gives depth \(2k+1\) and leading coefficient \(q^2(1-q)^2(1-q^2)^{2k}\), in agreement with SNG-F36, and its positivity is the even case of SNG-F37. The twist representation exists only for even \(p\): with leaves at distances \(a,c\) from \(s\) on the two arcs, the straight gluing gives distance \(a+c\) and the twist \(a+\ell-c\), and matching \((p,\ell)\) forces \(p=2a\). The kernel point of view separates the mechanism from the family. Visibility of a twist is decided by the asymmetry order of the block, the least volume at which the two terminals' decorated neighbourhoods differ, and the sign is always that of a sum of squares.

**Proposition SNG-F43 (marked composition).** For blocks as in SNG-F41, let \(K^{(H)}\) be the box kernel, with every height, terminals included, in \(\{0,\ldots,H\}\). The glued box histogram is \(C_H=\sum_{\mathbf b}x^{|\mathbf b|}K^{(H)}_{G_1}(\mathbf b)K^{(H)}_{G_2}(\pi\cdot\mathbf b)\), and the span-marked series of the glued graph is recovered from these by \(D_H=C_H-x^nC_{H-1}\) and exact span \(D_H-D_{H-1}\).

*Proof.* The gluing argument of SNG-F41 applies verbatim inside the box. SNG-F25 converts box histograms into minimum-zero and exact-span counts, using one global translation of the glued graph. \(\square\)

Global marks are not local: the minimum and maximum of a glued profile may sit in either block, so the marked series cannot be read from the unbounded kernels alone. The box kernels supply exactly the missing information. `marked_glue` in `src/singularity/terminals.py` implements this, and the tests compare it with direct marked enumeration for straight and twisted gluings and for a disconnected block.

**Proposition SNG-F44 (star probes determine a block).** Let \(G\) be a block with \(k\) terminals and \(R\ge0\). For \(\mathbf r\in\{0,\ldots,R\}^k\), let \(S_{\mathbf r}\) be the context with \(r_i\) pendant leaves on terminal \(i\). The series \(L_{G\cup S_{\mathbf r}}\) modulo \(x^{R+1}\), over all \((R+1)^k\) such \(\mathbf r\), determine \(x^{|\mathbf b|}K_G(\mathbf b)\) modulo \(x^{R+1}\) for every \(\mathbf b\), and this holds already after specializing \(q\) to any \(q_0\in(0,1)\). Consequently two \(k\)-terminal blocks satisfy \(L_{G\cup C}=L_{G'\cup C}\) for every edge-disjoint context \(C\) if and only if \(K_G=K_{G'}\).

*Proof.* A leaf on a terminal of height \(h\) contributes \(f(h)=\sum_{c\ge0}x^cq^{(c-h)^2}\), so \(L_{G\cup S_{\mathbf r}}=\sum_{\mathbf b}y_{\mathbf b}\prod_if(b_i)^{r_i}\) with \(y_{\mathbf b}=x^{|\mathbf b|}K_G(\mathbf b)\). Modulo \(x^{R+1}\) only \(|\mathbf b|\le R\) contributes, and in particular only \(b_i\le R\). In the ring \(\mathbb Q(q)[x]/(x^{R+1})\), or \(\mathbb Q[x]/(x^{R+1})\) after specializing \(q\), the differences \(f(h)-f(h')\equiv q^{h^2}-q^{h'^2}\pmod x\) are units for \(h\ne h'\), because their constant terms are nonzero (for \(0<q_0<1\) the numbers \(q_0^{h^2}\) are distinct). The tensor Vandermonde matrix \(\bigl(\prod_if(b_i)^{r_i}\bigr)_{\mathbf r,\mathbf b}\), with \(\mathbf b,\mathbf r\in\{0,\ldots,R\}^k\), is therefore invertible: its determinant is a product of powers of these differences. Solving recovers every \(y_{\mathbf b}\), including those with \(|\mathbf b|>R\), which vanish. The 'if' part of the consequence is the gluing formula; the 'only if' part follows from the star contexts. \(\square\)

So every distinction a block can make in any context is already made by star contexts. The kernel is the complete interface object for edge-disjoint gluing at its terminals. The count can be reduced to exactly \(\binom{R+k}{k}\), the number of unknowns \(y_{\mathbf b}\) with \(|\mathbf b|\le R\). The star probes with \(|\mathbf r|\le R\) suffice. Modulo \(x\), their matrix is monomial interpolation on the lower set \(\{|\mathbf r|\le R\}\) at the grid points \((q^{b_1^2},\ldots,q^{b_k^2})\), \(|\mathbf b|\le R\), and interpolation on a lower set with tensor-grid nodes of distinct coordinates is unisolvent, as the Newton form on lower sets shows. The matrix is therefore invertible over \(\mathbb Q[x]/(x^{R+1})\). The count is optimal in the following sense. The star blocks are themselves realizable \(k\)-terminal blocks, and by the same invertibility their kernels span the whole \(\binom{R+k}{k}\)-dimensional space of truncated \((y_{\mathbf b})\). A family of fewer contexts gives a linear map from that span with a nonzero kernel, so it cannot determine every element of the span. Swap-symmetric contexts are treated below (SNG-F47, SNG-F48); compression with proved savings remains open (P54). `recover_kernel_from_probes` in `src/singularity/terminals.py` carries out the inversion at a rational \(q_0\). The test recovers a two-terminal kernel through volume three from sixteen glued graphs counted by plain enumeration.

**Proposition SNG-F45 (rooted decks bound the asymmetry order).** For a block \(G\) with terminals \((s,t)\) and \(S\subseteq I\), regard \(G[S\cup\{s,t\}]\) as decorated by ambient degrees and by the roles of the two terminals. If for every \(j\le m\) the multiset of these types over \(|S|=j\) is unchanged when the roles of \(s\) and \(t\) are exchanged, then \(K_G(\beta,\gamma)\) and \(K_G(\gamma,\beta)\) agree in every cell of interior volume at most \(m\). Consequently twisting two copies of \(G\) is invisible below volume \(2m+3\), and more generally twisting blocks with rooted-deck symmetry through sizes \(m_1\) and \(m_2\) is invisible below volume \(m_1+m_2+3\).

*Proof.* As in SNG-F17, interior profiles of volume \(v\) with exact support \(S\) have energy determined by the decorated type of \(S\cup\{s,t\}\) and the terminal heights. The edges inside that set are read from the induced graph, and every other edge at a vertex \(u\) of the set contributes \(a_u^2\) times its number, which is fixed by the degree label. A role-respecting isomorphism between a type and the role-exchanged type of another support gives a bijection of positive interior assignments preserving volume and energy, carrying terminal heights \((\beta,\gamma)\) to \((\gamma,\beta)\). Summing over supports of size at most \(v\le m\) gives the equality of cells. In the pairing of SNG-F41 a term at terminal heights \(\mathbf b\) needs nonzero cells of both \(A_1(\mathbf b)\) and \(A_2(\mathbf b)\). These require \(\beta\ne\gamma\), so \(|\mathbf b|\ge1\), and interior volumes at least \(m_1+1\) and \(m_2+1\). Its volume is therefore at least \(m_1+m_2+3\). \(\square\)

In the exhaustive pairing of all 54 distinct asymmetric kernels of connected blocks with at most five vertices, no pairing vanished through volume six, and every twist was visible by volume three. Among blocks with at most six vertices and terminals of equal degree there are 104 distinct asymmetric kernels. None of their 5,460 pairings vanishes through volume six; the first visible volumes are \(3\), \(5\) and \(6\), the last attained by different blocks with \(m_1=1\), \(m_2=2\) as the bound allows. A cancelling pair of asymmetric kernels, which would make a twist invisible without a symmetry, has not been found. Its existence is open.

On every connected block with at most six vertices, with terminals \(0\) and \(1\) (27,474 blocks), the bound is sharp. Whenever the kernel is asymmetric, its least asymmetric interior volume equals the first size \(m+1\) at which the rooted decks lose their swap symmetry; this happens for 24,066 blocks. In the remaining blocks both are symmetric at every size. Whether this equality holds in general is open; it is a finite observation, not a theorem. The path blocks \(B_{m,k}\) attain it with first asymmetric size \(k\).

A systematic census of switches is retained in `results/whitney_switches.json`, produced by `scripts/whitney_switches.py` and checked in CI. Family A glues every connected block on three or four vertices to every such block without the terminal edge. Family B uses a first block on at most five vertices with terminals of equal degree, so that the twist preserves the degree sequence. For each of the 124 pairs kept after removing isomorphic duplicates, the receipt records simplicity, connectedness and cycle-matroid preservation, checked by comparing all circuits under the edge correspondence. It also records isomorphism by canonical code and the first local and marked differences through volume six, by weak compositions and level chains, together with the SNG-F41 prediction. In family A, 68 switches give isomorphic graphs and 28 separate at volume one, where the degree sequence changes. All 28 degree-preserving switches of family B separate at volume two: by SNG-F15 the difference is \((q^{-2}-1)(J_G-J_{G'})\), and the twist changes the edge degree-sum polynomial \(J\). No pair is unresolved at the bound. Deeper twists require blocks whose terminals agree in rooted decks to larger size (SNG-F45), and the path blocks show that the depth can be made arbitrarily large.

A twist changes the graph but preserves its cycle matroid, so the cut lattice and its energy theta series are unchanged. A block whose kernel is symmetric without an exchanging automorphism would therefore give two graphs with identical scalar height series. Among all connected blocks with at most six vertices and balanced terminals (7,456 at six vertices), the kernel through volume six is symmetric exactly when such an automorphism exists. This finite search does not decide the question in general. `src/singularity/terminals.py` computes kernels on a checked decomposition, with the terminals in every bag, and checks them against enumeration. `tests/test_terminals.py` verifies the gluing formulas for two and three terminals, the twist identity, invisibility for symmetric blocks, and the depth formula and identification above for \(B_{m,k}\) with \(m\le4\).

## Restricted contexts and interface rank under a volume budget

SNG-F44 identifies the kernel as the complete interface for unrestricted contexts. A natural restricted class consists of the contexts that cannot tell the two terminals apart. Call a two-terminal context \(C\) *swap-symmetric* if it has an automorphism exchanging its terminals. For terminal heights write an unordered orbit \(o=\{s,t\}\), \(|o|=s+t\), and put \(K^+_G(o)=K_G(s,t)+K_G(t,s)\) for \(s\ne t\) and \(K^+_G(o)=K_G(s,s)\).

**Proposition SNG-F47 (symmetric contexts see the symmetrized kernel).** If \(C\) is swap-symmetric and edge-disjoint from \(G\), then \(L_{G\cup C}=\sum_ox^{|o|}K^+_G(o)K_C(o)\). Hence blocks with \(K^+_G=K^+_{G'}\) are indistinguishable by every swap-symmetric context, in particular \(G\) with terminals \((s,t)\) and with terminals \((t,s)\).

*Proof.* The automorphism carries interior assignments with terminal heights \((s,t)\) to assignments with \((t,s)\), preserving volume and energy, so \(K_C(s,t)=K_C(t,s)\). Group the terms \(\mathbf b\) and its reversal in SNG-F41. \(\square\)

Whether swap-symmetric contexts see all of \(K^+\) is a question of rank. Fix a budget \(R\) and \(q_0\in(0,1)\), and let the unknowns be the coefficients \(Y_o[v]\) of \(Y_o=x^{|o|}K^+_G(o)(x,q_0)\), \(|o|\le v\le R\). The glued coefficient at volume \(w\) is \(\sum_o\sum_{j\le w}Y_o[j]\,K_C(o)[w-j]\), so the probe map is block lower triangular in the degree, and its diagonal blocks are the interior-volume-zero values \(K_C(o)[0]\).

**Theorem SNG-F48 (interface rank of symmetric contexts).** Let \(m_o=s^2+t^2\) and \(d_o=(s-t)^2\).

(a) If \(C\) is swap-symmetric and has no edge between its terminals, then \(K_C(o)[0]=q^{\delta m_o}\), where \(\delta\) is the common degree of the terminals in \(C\). Consequently every vector supported on the top degree, \(\sum_oc_oY_o[R]\) with \(\sum_{m_o=m}c_o=0\) for each \(m\), is invisible to all such contexts at budget \(R\). The rank defect at budget \(R\) is at least the number of orbits with \(|o|\le R\) minus the number of distinct values \(m_o\) among them. It is positive from \(R=7\) on, where \(\{0,5\}\) and \(\{3,4\}\) share \(m=25\).

(b) Let \(C_{\delta,\varepsilon}\) have \(\delta\) pendant leaves on each terminal and \(\varepsilon\in\{0,1\}\) terminal edges, and suppose \(G\) has no terminal edge. If no three orbits with \(|o|\le R\) share a value of \(m_o\), then the \(2M\) series \(L_{G\cup C_{\delta,\varepsilon}}\bmod x^{R+1}\), \(\delta<M\), where \(M\) is the number of distinct \(m_o\), determine every \(Y_o\) modulo \(x^{R+1}\). The hypothesis holds for every \(R\le24\); the first triple is \(325=1^2+18^2=6^2+17^2=10^2+15^2\).

*Proof.* (a) At interior volume zero all interior heights vanish. With no terminal edge the energy is \(\deg_C(s)s^2+\deg_C(t)t^2\), and the automorphism forces the two degrees to be equal. A coordinate \(Y_o[R]\) enters only the glued coefficient at volume \(R\), with coefficient \(K_C(o)[0]\), so the stated vectors give zero in every coordinate.

(b) Induct on \(v\). Once the \(Y_o[j]\), \(j<v\), are known, subtracting their contribution from the volume-\(v\) coefficients leaves \(\sum_{|o|\le v}Y_o[v]q_0^{\delta m_o+\varepsilon d_o}\) for all probes. Suppose a combination \(\sum_oc_oq_0^{\delta m_o+\varepsilon d_o}\) vanishes for \(\delta<M\) and both \(\varepsilon\). The numbers \(q_0^{m}\) are distinct, so the Vandermonde system in \(\delta\) gives \(\sum_{m_o=m}c_oq_0^{\varepsilon d_o}=0\) for each \(m\) and \(\varepsilon\). Two orbits with the same \(m\) and the same \(d\) have the same \(st\) and \(s+t\), so they coincide. A group of at most two orbits therefore has distinct values of \(d\), and the \(2\times2\) system forces \(c_o=0\). Hence the residual system is injective at every degree, and \(Y\) is determined. \(\square\)

Part (b) is constructive: `recover_symmetrized_kernel` in `src/singularity/contexts.py` solves the triangular system exactly. `scripts/symmetric_contexts.py`, checked in CI, replays the recovery at \(R=3\), \(q_0=1/2\), on all 15 connected blocks with at most four vertices and no terminal edge, against the symmetrized kernel computed by bag messages. For the family with \(\delta\) leaves per terminal, \(c\le R\) shared neighbours and an optional terminal edge, it also computes the exact rank of the probe map for \(R\le7\). With the edge the rank is full. Without it the rank equals the number of unknowns minus the top-degree defect of (a): full through \(R=6\), and \(69\) of \(70\) at \(R=7\). The same pattern holds at \(R=8\) (\(94\) of \(95\), full with the edge) and \(R=9\) (\(124\) of \(125\), full with the edge), computed once in the session that introduced it. Lower-degree collisions are thus resolved by the next volume, and the loss is confined to the top degree in the computed range. Whether this holds for all \(R\), and whether the edge-free class determines \(K^+\) without a budget, is open. For comparison, unrestricted contexts have full rank \(\binom{R+3}{3}\) on the ordered unknowns by SNG-F44. With the edge, symmetric contexts reach \(\sum_{v\le R}\#\{o:|o|\le v\}\), and the difference is exactly the information carried by the order of the terminals.

On the realizable side the quotient is no coarser than forced. Among the 12,753 connected blocks with at most six vertices and no terminal edge, grouped by \(K^+\) through volume four, no class contains two kernels unrelated by the terminal swap (451 classes; `--census` mode of the same script). On that population, swap-symmetric contexts lose exactly the order of the terminals. This is a finite statement about one population and one budget.

### The observable interface

Let \(V_R\) be the space of coefficients \(Y_o[v]\), \(|o|\le v\le R\), over \(\mathbb Q(q)\). For a class \(\mathcal C\) of contexts let \(I_{\mathcal C,R}=\bigcap_{C\in\mathcal C}\ker L_C\), where \(L_C\) sends the coefficients to the glued series modulo \(x^{R+1}\). The *observable interface* is \(\mathcal O_{\mathcal C,R}=V_R/I_{\mathcal C,R}\): two blocks have the same image exactly when every context in the class gives the same answer. Write \(\kappa=1\) for the simple swap-symmetric contexts without a terminal edge. Write \(\kappa=2\) for those that may use it, in which case the block has no terminal edge. Group the orbits of each degree by \(m_o\), and put \(y_o=q^{d_o}\) and
\[
\tau_o=q^{1-2s}+q^{1-2t}-q^{2-2(s+t)}.
\]

**Theorem SNG-F49 (the observable interface of simple symmetric contexts).**

(a) *Top degree.* Let \(N_R\) be the space of vectors supported on degree \(R\) whose restriction to each group is annihilated by \(y^e\), \(e<\kappa\). Then \(N_R\subseteq I_{\mathcal C,R}\), \(N_R\) is exactly the kernel of the degree-\(R\) diagonal block of the whole class, and \(\dim N_R=\sum_g\max(0,|g|-\kappa)\). For \(\kappa=2\) the first nonzero \(N_R\) occurs at \(R=25\). It is spanned by
\[
v=\bigl(q^{25}-q^{121},\;q^{289}-q^{25},\;q^{121}-q^{289}\bigr)
\]
on the orbits \(\{1,18\},\{6,17\},\{10,15\}\) of \(325\), whose \(d_o\) are \(289,121,25\).

(b) *Exactness.* Suppose that for every \(v<R\) and every group at degree \(v\) the functionals \(y^e\tau^i\), \(e<\kappa\), \(i\in\{0,1\}\), are linearly independent on the group. Then \(I_{\mathcal C,R}=N_R\). The interface has the explicit coordinates
\[
\mathcal O_{\mathcal C,R}\cong\bigl(Y_o[v]\bigr)_{v<R}\oplus\Bigl(\textstyle\sum_{o\in g}y_o^eY_o[R]\Bigr)_{g,\;e<\kappa}.
\]
The finitely many contexts with \(d\) pendant leaves per terminal, \(c\) shared neighbours and, when \(\kappa=2\), an optional terminal edge span every response of the class. The hypothesis holds for \(\kappa=1\) exactly when \(R\le25\), and for \(\kappa=2\) for every \(R\le91\).

(c) *Realizability.* Let a block have no terminal edge, and let its terminals have internal degrees \(a,b\). Then \(Y_o[|o|]=q^{as^2+bt^2}+q^{bs^2+at^2}\), or \(q^{(a+b)s^2}\) for \(s=t\), and \(Y_{\{0,1\}}[1]=q^a+q^b\) determines \(\{a,b\}\). Hence the difference of two blocks that no context in the class distinguishes vanishes in every coordinate with \(|o|=v\). Parts (a) and (b) hold for such differences with each group restricted to \(|o|<v\), and the exactness hypothesis then holds through \(R=26\) for \(\kappa=1\) and \(R=92\) for \(\kappa=2\). In particular:
- For \(\kappa=2\), simple swap-symmetric contexts separate the truncated symmetrized kernels of any two blocks for every \(R\le25\), and the blind direction \(v\) of (a) is not a difference of two blocks.
- At \(R=26\) the only possible invisible difference allowed by (c) alone is a multiple of \(v\) placed at degree \(26\). SNG-F52 below excludes it as well.
- For \(\kappa=1\), blocks are separated for \(R\le7\). At \(R=8\) the only possible invisible difference allowed by (c) alone is a multiple of \(e_{\{0,5\}}[8]-e_{\{3,4\}}[8]\), which SNG-F52 also excludes.

*Proof.* (a) At interior volume zero a context in the class has kernel \(q^{\delta m_o+ed_o}\), with \(\delta\) the common terminal degree and \(e\in\{0,1\}\) (\(e=0\) if \(\kappa=1\)), as in SNG-F48(a). A coordinate \(Y_o[R]\) enters only the volume-\(R\) coefficient, multiplied by this value. A top-degree vector \(c\) is therefore invisible exactly when \(\sum_oc_oq^{\delta m_o+ed_o}=0\) for every realized pair \((\delta,e)\). Leaves realize every \(\delta\ge0\), and the numbers \(q^m\) are distinct, so a Vandermonde system in \(\delta\) reduces this to \(\sum_{o\in g}c_oy_o^e=0\) for each group and \(e<\kappa\). Within a group the \(y_o\) are distinct (SNG-F48(b)). The \(\kappa\times|g|\) Vandermonde matrix therefore has rank \(\min(\kappa,|g|)\), which gives the dimension, and Cramer's rule gives the basis. For the triple with nodes \(q^{289},q^{121},q^{25}\) the cofactors are \(v\).

(b) Induct on \(v<R\), assuming every coordinate of degree below \(v\) is determined. A leaf on a terminal of height \(h\) contributes \(f(h)=q^{h^2}\bigl(1+xq^{1-2h}+O(x^2)\bigr)\), and a shared neighbour contributes \(q^{m}\bigl(1+xq^{2-2(s+t)}+O(x^2)\bigr)\). The context with \(d\) leaves per terminal, \(c\) shared neighbours and \(e\) terminal edges therefore has kernel
\[
q^{ed_o+(d+c)m_o}\bigl(1+x(d\sigma_o+c\pi_o)+O(x^2)\bigr),\qquad \sigma_o=q^{1-2s}+q^{1-2t},\ \pi_o=q^{2-2(s+t)}.
\]
After the known terms are removed, the volume-\(v\) coefficients give \(\sum_oq^{\delta m_o}y_o^eY_o[v]\). In the volume-\(v+1\) coefficient, \(Y[v+1]\) appears with the split-independent factor \(q^{ed_o+(d+c)m_o}\), and \(Y[v]\) with the factor \(q^{ed_o+(d+c)m_o}(d\sigma_o+c\pi_o)\). Subtracting the context \((d-1,c+1)\) from \((d,c)\) removes \(Y[v+1]\) and leaves \(\sum_oq^{\delta m_o}y_o^e\tau_oY_o[v]\), with \(\delta=d+c\ge1\). The Vandermonde system in \(\delta\) separates the groups. What remains on each group is the functionals \(y^e\tau^i\), which are independent by hypothesis, so degree \(v\) is determined. The induction reaches \(R-1\). At degree \(R\), (a) shows that exactly the group sums are determined, so \(I_{\mathcal C,R}=N_R\). The probes used and the whole class have the same annihilator \(N_R\), so the probes span every response.

For \(\kappa=1\) the hypothesis asks that \((1,\tau_o)\) separate each group. Two orbits of a group have different \(s+t\). Since \(1-2s\) is odd, the only even exponent of \(\tau_o\) is \(2-2(s+t)\), so the two \(\tau_o\) differ and groups of two pass. A group of three cannot be separated by two functionals; the first one is complete at degree \(25\). For \(\kappa=2\), after scaling column \(o\) by \(q^{2(s+t)}\) the four functionals are integer polynomials. Their matrix has full column rank modulo \(2^{61}-1\) at a fixed residue of \(q\) for every prefix, ordered by \(|o|\), of every group with \(s+t\le100\). A nonzero minor modulo \(p\) is nonzero over \(\mathbb Z[q]\). The first failure is the five-orbit group \(4225=0^2+65^2=16^2+63^2=25^2+60^2=33^2+56^2=39^2+52^2\) at degree \(91\).

(c) Interior volume zero is the single profile with every interior height \(0\), and its energy is \(as^2+bt^2\). By (b) at degree \(1\), where \(m=0,1\) are distinct, two indistinguishable blocks have the same \(q^a+q^b\), hence the same \(\{a,b\}\), and so the same coordinates \(Y_o[|o|]\). Repeating (a) and (b) on the remaining coordinates gives the restricted statements. \(\square\)

So the interface has a precise shape. Without the terminal edge, each budget loses the top-degree collision information and nothing else, through \(R=25\). With the edge, the formal interface is complete through \(R=24\) and loses one direction at \(R=25\), and this direction is not realized by blocks. Independently of the proof, the exact rank of the leaf-and-shared-neighbour probe map modulo \(2^{61}-1\) equals \(\dim V_R-\dim N_R\) for every \(R\le18\) without the edge. The values for \(R=8,\ldots,12\) are rechecked in CI. Beyond the stated budgets, whether the higher terms of the \(x\)-expansion keep resolving lower-degree collisions is open.

**Proposition SNG-F50 (weighted terminal coupling).** Let \(\mu_R\) be the largest number of orbits with \(|o|\le R\) that share \(m_o\). Allow contexts to carry a terminal edge of integer weight \(e\in\{0,\ldots,W\}\) with \(W+1\ge\mu_R\). Then the \(M(W+1)\) probes with \(\delta<M\) leaves per terminal and terminal weight \(e\) determine every \(Y_o\) modulo \(x^{R+1}\), at every budget \(R\).

*Proof.* The induction of SNG-F48(b) applies with the Vandermonde system \((q^{ed_o})_{e\le W,\,o\in g}\), whose nodes are distinct within a group. \(\square\)

The multiplicity grows slowly: \(\mu_R=2\) for \(7\le R<25\), \(3\) from \(R=25\), \(4\) from \(R=47\), where \(1105\) has four orbits, and \(5\) from \(R=91\). Weighted coupling therefore enlarges the experimental language by a small and explicit amount. It is the extra capability that removes the obstruction of SNG-F49(a). The script replays weighted recovery on real weighted gluings, counted by weak compositions, for all fifteen blocks with at most four vertices (\(R=3\), weights \(0,1,2\)). It also checks the degree-25 diagonal ranks modulo \(p\): \(181\) of \(182\) with simple contexts, \(169\) of \(169\) on the realizable coordinates, and \(182\) of \(182\) with weights up to \(2\).

*Reuse.* Rank reduction is not the only computational gain. A kernel is compiled once and then answers every attachment query by the contraction of SNG-F41. For a \(2\times6\) ladder with terminals at opposite corners and \(R=6\), compiling the kernel takes \(4.6\) s. Each of \(24\) symmetric-context queries then takes \(7.6\) ms by contraction, against \(1.33\) s for a fresh decomposition of the glued graph, with identical exact output. The compilation pays for itself after about \(3.5\) queries (`--benchmark`, wall-clock on the session machine, retained). A compression theorem with savings that grow along a family remains open (P54).

*Targeted realizability searches.* The following observation gives a route to a symmetric kernel without a swap automorphism. If two blocks \(A,B\) have \(K_A=K_B\), then joining \(A\) in series with the reversal of \(B\), at an internal middle vertex, gives a block with \(K(s,t)=\sum_wx^wK_A(s,w)K_A(t,w)\), which is symmetric. It has no swap automorphism unless such a map carries \(A\) onto the reversal of \(B\). The search for kernel-equal blocks found nothing. The 777 terminal-isomorphism classes of connected blocks with at most six vertices and no terminal edge have 777 distinct kernels through volume four. Among the 7,682 two-terminal trees with at most ten vertices, up to isomorphism, no kernel is symmetric without a swap automorphism. Five pairs of non-isomorphic trees on ten vertices agree through volume four, and all five separate at volume five. For cancelling twists, the pairing of two asymmetric kernels vanishes only if its leading coefficient at volume \(\mu=\min_{\mathbf b}(|\mathbf b|+v_{1,\mathbf b}+v_{2,\mathbf b})\) cancels, and this requires at least two orbits to reach \(\mu\). We tested this on the 1,522 distinct antisymmetric parts, through volume five, of balanced blocks: connected graphs with at most six vertices and two-terminal trees with at most ten vertices. Of the 1,159,003 pairs, self-pairings included, 12,112 have two or more leading orbits, and none has a vanishing leading coefficient. A cancelling pair, if one exists, must therefore come from a richer family or a deeper leading level.

### Recovery with extra volume, and rigidity of realizable interfaces

The obstruction of SNG-F49(a) is tied to a fixed budget. Two questions remain: how much additional observation recovers an interface, and which formal ambiguities actual blocks can realize. The relevant object is \(\ker\mathcal O_R\cap(\mathcal B_R-\mathcal B_R)\), where \(\mathcal B_R\) is the set of truncated interfaces of actual blocks. SNG-F49 describes the first factor; the slice constraints below begin to describe the second.

**Theorem SNG-F51 (recovery with extra volume).** Let \(m_R\) be the largest number of orbits with \(|o|\le R\) sharing a value of \(s^2+t^2\), and let \(G\) be the number of distinct values. Let \(C_{d,c}\) be the context with \(d\) pendant leaves on each terminal, \(c\) shared neighbours and no terminal edge. Then the glued series of a block with the contexts \(C_{d,c}\), \(d+c<G+m_R-1\), through volume \(R+m_R-1\) determine \(Y_o\) modulo \(x^{R+1}\) for every orbit. This holds over \(\mathbb Q(q)\) and at every \(q_0\in(0,1)\). In particular, edge-free symmetric contexts determine every finite prefix of \(K^+\): the obstruction of SNG-F49(a) delays observation by \(m_R-1\) units of volume, and loses nothing.

*Proof.* With \(L_h(x)=\sum_ux^uq^{(u-h)^2}\), a pair of leaves contributes \(P=L_sL_t\) and a shared neighbour contributes \(S=\sum_ux^uq^{(u-s)^2+(u-t)^2}\). Both have constant term \(q^{E}\), \(E=s^2+t^2\), and \(S-P=-q^E\tau_ox+O(x^2)\). The context \(C_{k-c,c}\) contributes \(P^{k-c}S^c\), so for \(k\ge j\)
\[
\sum_{c=0}^{j}(-1)^{j-c}\binom jc P^{k-c}S^c=P^{k-j}(S-P)^j=x^jq^{kE}(-\tau_o)^j+O(x^{j+1}).
\]
This is an exact linear combination of responses of actual contexts, and it vanishes through degree \(j-1\).

Suppose every coordinate of degree below \(n\) is known, and subtract its contribution. At output volume \(n+j\) the differenced measurement is \(\sum_{|o|\le n}q^{kE_o}(-\tau_o)^jY_o[n]\). Coordinates of degree above \(n\) cannot enter, because the context factor supplies at least \(j\) units of volume. For fixed \(j\), varying \(k=j,\ldots,j+G-1\) gives a Vandermonde system in the distinct numbers \(q^E\), which separates the groups. Inside a group, \(j=0,\ldots,|g|-1\) gives a Vandermonde system in the \(\tau_o\).

These are distinct. Write \(\tau_o=1-(q^{1-2s}-1)(q^{1-2t}-1)\). For \(t\ge1\) the pair \(\{0,t\}\) has \(\tau>1\), and pairs with \(s,t\ge1\) have \(\tau<1\). For the latter put \(r=1/q>1\) and \(g(y)=\log(r^{2\sqrt y-1}-1)\) for \(y\ge1\). With \(x=\sqrt y\), \(h(x)=\log(r^{2x-1}-1)\) and \(L=\log r\), one has \(h'=2Lr^{2x-1}/(r^{2x-1}-1)>0\) and \(h''=-4L^2r^{2x-1}/(r^{2x-1}-1)^2<0\). Hence \(g''=(h''-h'/x)/(4x^2)<0\), and on the circle \(s^2+t^2=E\) the sum \(g(s^2)+g(t^2)\) strictly increases toward balance. So \(\tau_o\) strictly decreases toward balance, and distinct orbits of a group have distinct \(\tau_o\). A group at degree \(n\) has at most \(m_R\) orbits, so the output volumes used are at most \(R+m_R-1\). \(\square\)

If only connected contexts are allowed, keep one shared neighbour in every probe. The same argument goes through with the extra factor \(S\), whose constant term is a unit.

The three mechanisms compare as follows. Ordinary symmetric contexts at the original budget give the quotient of SNG-F49. Finite differences, with \(m_R-1\) extra units of volume, produce the powers \(1,\tau,\tau^2,\ldots\) and recover everything (SNG-F51). A weighted terminal edge with weights \(0,\ldots,m_R-1\) produces the powers \(1,y,y^2,\ldots\) and recovers everything at the original budget (SNG-F50). Here \(m_R=2\) for \(7\le R<25\), \(3\) from \(25\), \(4\) from \(47\) and \(5\) from \(91\). `recover_by_finite_differences` in `src/singularity/contexts.py` carries out the reconstruction. `scripts/symmetric_contexts.py` replays it at \(R=7\), where the budget-\(7\) quotient has a defect, with 39 probes through volume \(8\). Their glued series are computed by tree decomposition of each actual glued graph, independently of the contraction formula and of the closed-form context factors.

**Proposition SNG-F52 (interior slices of a block kernel).** Let a block have terminal degrees \(a,b\), let \(e\in\{0,1\}\) count its terminal edge, and put \(Q_0(s,t)=as^2+bt^2-2est\), \(U=q^{-2s}\), \(V=q^{-2t}\). For every \(j\),
\[
[x^j]K(s,t)=q^{Q_0(s,t)}P_j(U,V),
\]
where \(P_j\) has coefficients in \(\mathbb Z_{\ge0}[q]\) and degree at most \(j\) in each variable. In particular \(P_1=\sum_vq^{\deg v}U^{A_{sv}}V^{A_{tv}}\), summed over interior vertices, has at most four monomials whatever the size of the block.

(a) Suppose two blocks have the same \(\{a,b\}\) and \(e\). If their symmetrized kernels agree in interior volume one at the states \((0,0),(1,1),(2,2)\) and \((0,1)\), of total volume at most \(5\), then their interior-volume-one slices of \(K^+\) agree at every state.

(b) If moreover \(a=b\), agreement of slice \(j\) of \(K^+\) at the states with \(s,t\le j\), of total volume at most \(3j\), implies agreement of slice \(j\) at every state.

*Proof.* For interior heights \(h\) of total \(j\), the energy is
\[
Q_0+\Bigl[\sum_{\text{interior edges}}(h_u-h_v)^2+\sum_{v\sim s}h_v^2+\sum_{v\sim t}h_v^2\Bigr]-2s\sum_{v\sim s}h_v-2t\sum_{v\sim t}h_v.
\]
The bracket does not depend on \((s,t)\), and each of the last two sums is at most \(j\). For \(j=1\) the single raised vertex contributes \(q^{\deg v}U^{A_{sv}}V^{A_{tv}}\).

(a) When \(a\ne b\), order the terminals of both blocks so that \(s\) has degree \(a\); this does not change \(K^+\). Let \(P=P_1-P_1'\). At a diagonal state \(K^+(s,s)=K(s,s)\), so agreement at \(s=0,1,2\) says that \(P(z,z)\), of degree at most \(2\), vanishes at the three distinct nodes \(z=1,q^{-2},q^{-4}\). Hence \(P=c(U-V)\). At \(s\ne t\) the symmetrized difference is \(c(U-V)\bigl(q^{Q_0(s,t)}-q^{Q_0(t,s)}\bigr)\). This vanishes identically when \(a=b\). When \(a\ne b\), at \((0,1)\) it equals \(c(1-q^{-2})(q^b-q^a)\), forcing \(c=0\).

(b) With \(a=b\), \(Q_0\) is symmetric, and the symmetrized slice is \(q^{Q_0}\Sigma(U,V)\) with \(\Sigma(U,V)=P_j(U,V)+P_j(V,U)\) off the diagonal, and \(q^{Q_0}\Sigma(z,z)/2\) on it. The symmetric polynomial \(\Sigma\), of degree at most \(j\) in each variable, vanishes on the tensor grid of the \(j+1\) distinct nodes \(q^{-2s}\), \(s\le j\), and is therefore zero. \(\square\)

Together with SNG-F49(c), which fixes interior volume zero, this sharpens the realizable statements. Two indistinguishable blocks agree below degree \(v\) by induction, and the degree data fix \(\{a,b\}\) at degree \(1\) and \(e\) at degree \(2\). So their difference vanishes in slice one at every degree \(v\ge6\), and, when the terminal degrees are equal, in every slice \(j\) with \(3j<v\). Rerunning SNG-F49 on the remaining coordinates (`realizable="slice"` or `"balanced"` in `interface_status`) gives:
- **With the terminal edge (\(\kappa=2\)).** Simple symmetric contexts separate the truncated symmetrized kernels of any two blocks through \(R=26\). This removes the \(R=26\) candidate: its coordinate on \(\{10,15\}\) has interior volume one. At \(R=27\) the only possible invisible difference is \(v\) placed at degree \(27\), at interior volumes \(8,4,2\). For equal terminal degrees, separation holds through \(R=37\).
- **Without the edge (\(\kappa=1\)).** Separation holds through \(R=8\). At \(R=9\) the only possible invisible difference is a multiple of \(e_{\{0,5\}}[9]-e_{\{3,4\}}[9]\). For equal terminal degrees, separation holds through \(R=10\).

On these coordinates the exactness hypothesis of SNG-F49(b) holds for \(R\le27\) (\(\kappa=1\)) and \(R\le93\) (\(\kappa=2\)) in general. For equal terminal degrees it holds for \(R\le38\) and \(R\le120\), the latter being the range checked. All statements are recorded in `results/symmetric_contexts.json`. For unequal terminal degrees, the analogue of (b) for \(j\ge2\) needs an interpolation argument for \(q^{as^2+bt^2}P_j(U,V)+q^{bs^2+at^2}P_j(V,U)\) and is open. So is the question whether the remaining candidates are realized by actual blocks.

## Every late census collision is separated by triangles

For connected graphs with at most six vertices, the symbolic coefficients separate every pair of nonisomorphic graphs by volume three (`results/visibility_filtration.json`). The pairs that survive volume two are fourteen pairs on six vertices; they are retained with their graphs in `results/late_collisions.json`. In each of them the ordered adjacent-degree sector \(2e_i+e_j\) of SNG-F14 also agrees, so the two graphs have the same ordered degree-and-adjacency statistics. The separation comes entirely from the induced-triple sector \(\sum T_{s,t}q^{s-2t}\), and in every pair the triangle counts differ, for example \(K_{3,3}\) against the prism. None of the fourteen pairs is related by a single Whitney twist at a two-vertex separator. Their separation is therefore not the twist mechanism of SNG-F41; it is the classical one of SNG-I008, a different number of triangles under the same degree data. This is a complete finite classification of the late collisions in that population, with an explicit separating pattern for each pair. It is not a statement about larger graphs, where the pendant-cycle and twist families show that collisions can persist to arbitrarily large volume.

The same population is measured across invariants in `results/collision_census.json`, produced by `scripts/collision_census.py` and checked in CI. Counts are of connected isomorphism classes, one representative each. On six vertices, 112 classes give 68 degree sequences and 110 Laplacian spectra (two cospectral pairs). Volume one of the height series also gives 68 classes and volume two gives 100. The binary cut profile, the nested-pair census, and the height prefix through volume three each separate all 112, both symbolically in \(q\) and at \(q=1/2\). Both cospectral pairs are separated by the volume-three height prefix. All ten nontrivial classes of the volume-two prefix are split by the binary profile and also by the spectrum. The report lists every nontrivial class with its graph codes, and the number of classes of each invariant split by every other. It gives a signed difference witness for each pair first separated at volume two or three, and a chain-recomputed sample. There are no unresolved classes at volume three in this population.

## What should be searched next?

The first inverse question is whether full marked equality implies graph isomorphism on any substantial class. Trees are an attractive target because the ordinary cut lattice of every tree is a standard integer lattice and therefore discards almost all attachment geometry. The marked volume population could preserve some of that geometry. Completeness on trees is a question, not a conclusion. A single pair of nonisomorphic trees with equal full marked series would refute it; a finite census without a collision would only establish a bounded result.

A second question is whether the full hierarchy eventually stops improving on a fixed graph order. Since there are finitely many isomorphism classes on \(n\) vertices, if the full marked invariant is complete on that order then some finite maximum distinguishing depth exists. This existence is purely finite and does not supply a useful bound. If the invariant has collisions, the same argument instead gives a finite depth at which its equivalence partition stabilizes to its final, possibly nontrivial partition. A search can record that stabilization for a finite census, while a theorem must control all higher depths.

A third question concerns the loss of the span marker. It is possible that the unmarked series is complete on a class where no simple proof recovers the binary sector. It is also possible that different marked populations collapse to the same unmarked series. Neither possibility is settled by the current examples. The appropriate experiment compares marked equality and unmarked equality separately, rather than assuming that agreement or disagreement of one automatically decides the other.

A useful search ledger should retain graph order, component sizes, degree polynomial, binary profile, first different volume, first different span, and exact difference polynomial. It should separate pairs selected to collide under a background invariant from arbitrary pairs that happen to be easy to distinguish. Regular graphs with equal triangle count offer controlled difficult cases after the easy volume-three obstructions have been removed. Trees offer a different challenge, in which lattice isometry is automatic but attachment structure varies. Graphs related by changes of attachment within a common block structure test whether the volume marker preserves the intended vertex realization.

These are falsifiable targets. The hypothesis that depth two distinguishes all binary-profile collisions can be rejected by one depth-two collision. The hypothesis that a finite volume cutoff suffices for all graphs of a stated order needs a census whose completeness is itself justified. The hypothesis that a coefficient depends only on a known motif census can be tested by deriving its assignment patterns before scanning data. Every negative result would locate an exact limit of the representation. Such a limit would still be useful mathematics, because it would say what relational information the population has actually retained.
