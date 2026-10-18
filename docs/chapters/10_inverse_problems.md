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

A twist changes the graph but preserves its cycle matroid, so the cut lattice and its energy theta series are unchanged. A block whose kernel is symmetric without an exchanging automorphism would therefore give two graphs with identical scalar height series. Among all connected blocks with at most five vertices and balanced terminals, the kernel through volume six is symmetric exactly when such an automorphism exists. This finite search does not decide the question in general. `src/singularity/terminals.py` computes kernels on a checked decomposition, with the terminals in every bag, and checks them against enumeration. `tests/test_terminals.py` verifies the gluing formulas for two and three terminals, the twist identity, invisibility for symmetric blocks, and the depth formula and identification above for \(B_{m,k}\) with \(m\le4\).

## What should be searched next?

The first inverse question is whether full marked equality implies graph isomorphism on any substantial class. Trees are an attractive target because the ordinary cut lattice of every tree is a standard integer lattice and therefore discards almost all attachment geometry. The marked volume population could preserve some of that geometry. Completeness on trees is a question, not a conclusion. A single pair of nonisomorphic trees with equal full marked series would refute it; a finite census without a collision would only establish a bounded result.

A second question is whether the full hierarchy eventually stops improving on a fixed graph order. Since there are finitely many isomorphism classes on \(n\) vertices, if the full marked invariant is complete on that order then some finite maximum distinguishing depth exists. This existence is purely finite and does not supply a useful bound. If the invariant has collisions, the same argument instead gives a finite depth at which its equivalence partition stabilizes to its final, possibly nontrivial partition. A search can record that stabilization for a finite census, while a theorem must control all higher depths.

A third question concerns the loss of the span marker. It is possible that the unmarked series is complete on a class where no simple proof recovers the binary sector. It is also possible that different marked populations collapse to the same unmarked series. Neither possibility is settled by the current examples. The appropriate experiment compares marked equality and unmarked equality separately, rather than assuming that agreement or disagreement of one automatically decides the other.

A useful search ledger should retain graph order, component sizes, degree polynomial, binary profile, first different volume, first different span, and exact difference polynomial. It should separate pairs selected to collide under a background invariant from arbitrary pairs that happen to be easy to distinguish. Regular graphs with equal triangle count offer controlled difficult cases after the easy volume-three obstructions have been removed. Trees offer a different challenge, in which lattice isometry is automatic but attachment structure varies. Graphs related by changes of attachment within a common block structure test whether the volume marker preserves the intended vertex realization.

These are falsifiable targets. The hypothesis that depth two distinguishes all binary-profile collisions can be rejected by one depth-two collision. The hypothesis that a finite volume cutoff suffices for all graphs of a stated order needs a census whose completeness is itself justified. The hypothesis that a coefficient depends only on a known motif census can be tested by deriving its assignment patterns before scanning data. Every negative result would locate an exact limit of the representation. Such a limit would still be useful mathematics, because it would say what relational information the population has actually retained.
