# Exact examples: what the new population distinguishes

This chapter records the finite evidence on which the first release rests. The examples are deliberately small enough that their defining populations can be examined without numerical approximation. They serve a precise purpose: to show that integer heights retain relational information that certain familiar summaries discard. They do not establish that the resulting invariant determines every graph, that the Euler product adds information to its local factor, or that the construction has historical priority. The claims below distinguish direct arguments from exact finite computations. The computations can be repeated through the standard-library package accompanying this manuscript.

Throughout the chapter a graph is simple, undirected, and has the labeled vertex set \(V=\{0,1,\ldots,6\}\). Labels specify the input and the assignments being counted. The resulting polynomials are unchanged by relabeling the graph, because a permutation of vertices induces a bijection on all height assignments. An edge written \(03\) means the unordered pair \(\{0,3\}\). The height energy is

\[
E_G(a)=\sum_{\{i,j\}\in E(G)}(a_i-a_j)^2,
\qquad |a|=\sum_i a_i.
\]

The unnormalized local population and the normalized marked population are

\[
P_G(x,q)=\sum_{a\in\mathbb N^7}x^{|a|}q^{E_G(a)},
\]

\[
B_G(x,q,z)=\sum_{\substack{a\in\mathbb N^7\\\min_i a_i=0}}
x^{|a|}q^{E_G(a)}z^{\max_i a_i}.
\]

Volume means total integer height. The variable \(z\) records height span after the common minimum has been removed. Consequently \(B_G(x,q,1)=(1-x^7)P_G(x,q)\). For volumes below seven, the coefficients of the unmarked normalized and unnormalized series agree. Every assignment of such a volume already has a zero coordinate. This observation lets us discuss the first local coefficients and their span decomposition without changing normalization halfway through an argument.

## Two different comparisons

The first pair has equal Laplacian spectra. The second pair has equal complete binary cut-volume populations. These are separate examples, and keeping them separate prevents an unsupported inference about a single pair defeating every existing invariant.

| Name in this chapter | Package name | Edge set | Degrees in vertex order |
|---|---|---|---|
| \(G_{\mathrm{sp}}\) | `spectral_g` | \(01,02,03,04,12,35,36\) | \((4,2,2,3,1,1,1)\) |
| \(H_{\mathrm{sp}}\) | `spectral_h` | \(01,02,03,04,15,16,56\) | \((4,3,1,1,1,2,2)\) |
| \(G_{\mathrm{bin}}\) | `binary_g` | \(03,04,06,12,13,23,24,35\) | \((3,2,3,4,2,1,1)\) |
| \(H_{\mathrm{bin}}\) | `binary_h` | \(01,04,06,15,16,26,36,45\) | \((3,3,1,1,2,2,4)\) |

All four graphs are connected. Each spectral graph has one triangle and four bridges. Each binary graph has the same two-connected block, a theta graph with three internally disjoint paths of lengths one, two, and three, together with two attached bridges. The attachments differ. This distinction between a common block structure and different vertex attachments will matter when we compare the marked population with an ordinary cut-lattice theta series.

**Proposition SNG-E001: the spectral graphs are nonisomorphic.** Each graph has a unique vertex of degree four, namely vertex zero. In \(G_{\mathrm{sp}}\), that vertex lies in the triangle \(0,1,2\). In \(H_{\mathrm{sp}}\), the only triangle is \(1,5,6\), which excludes vertex zero. An isomorphism preserves vertex degrees and triangle membership. It would therefore have to send the degree-four vertex to the degree-four vertex while preserving a property that differs, which is impossible.

**Proposition SNG-E002: the binary graphs are nonisomorphic.** The unique degree-four vertex of \(G_{\mathrm{bin}}\) is vertex three, and its neighbors are \(0,1,2,5\). Exactly one of these neighbors, vertex five, is a leaf. The unique degree-four vertex of \(H_{\mathrm{bin}}\) is vertex six, with neighbors \(0,1,2,3\). Exactly two of those neighbors are leaves. The number of leaf neighbors of a specified degree class is invariant under isomorphism. The graphs are therefore nonisomorphic.

These short arguments are logically independent of the population computation. A differing graph invariant would also prove nonisomorphism, but an elementary structural witness makes the examples easier to inspect. It also guards against a mistaken interpretation in which a relabeling of one graph has merely been counted in a different order.

## The exact Laplacian comparison

The graph Laplacian has entries \(L_{ii}=d_i\) and \(L_{ij}=-\epsilon_{ij}\), where \(d_i\) is vertex degree and \(\epsilon_{ij}\) is the adjacency indicator. We use the characteristic-polynomial convention \(\chi_G(t)=\det(tI-L_G)\). The following values are exact finite computational results, obtained using integer arithmetic. They are not floating-point eigenvalue comparisons and are not described as proof-assistant-checked theorems.

| Graphs | Characteristic polynomial |
|---|---|
| Both spectral graphs | \(t^7-14t^6+73t^5-178t^4+209t^3-112t^2+21t\) |
| \(G_{\mathrm{bin}}\) | \(t^7-16t^6+98t^5-290t^4+430t^3-300t^2+77t\) |
| \(H_{\mathrm{bin}}\) | \(t^7-16t^6+98t^5-290t^4+432t^3-302t^2+77t\) |

The spectral pair is therefore Laplacian-cospectral. The binary pair is not. In particular, the second example must not be advertised as a simultaneous collision of the Laplacian spectrum and the binary cut polynomial. Its role is to isolate a different information gap. Both members of a pair have the same number of spanning trees: three for the spectral pair and eleven for the binary pair. These counts follow independently from the matrix-tree theorem or from the coefficient of \(t\), whose absolute value is seven times the spanning-tree count in these connected seven-vertex graphs.

An integer implementation can compute the characteristic polynomial through traces of powers and Newton identities. If \(p_j=\operatorname{tr}(L^j)\) and \(c_0=1\), the descending coefficients satisfy

\[
c_r=-\frac1r\sum_{j=1}^r c_{r-j}p_j.
\]

Every division is exact for a matrix characteristic polynomial. This supplies one transparent computational route, although a determinant calculation is equally legitimate. The manuscript's conclusion depends on the exact resulting polynomial, not on a choice of numerical eigensolver or an eigenvalue tolerance.

## All binary cut-volume profiles

For a subset \(S\subseteq V\), let \(\partial S\) be its edge boundary and define

\[
I_{G,r}(q)=\sum_{\substack{S\subseteq V\\ |S|=r}}q^{|\partial S|}.
\]

The full binary polynomial is \(C_G(x,q)=\sum_{r=0}^7x^rI_{G,r}(q)\). Its coefficients count every original subset. A graph automorphism does not reduce a coefficient by identifying subsets in the same orbit. Complementation gives \(I_{G,r}=I_{G,7-r}\), because the two sides of a cut have the same boundary. At \(q=1\), the row sum is \(\binom7r\). Both relations provide simple consistency checks on the tables.

| \(r\) | \(I_{G_{\mathrm{sp}},r}(q)\) | \(I_{H_{\mathrm{sp}},r}(q)\) |
|---:|---|---|
| 0 | \(1\) | \(1\) |
| 1 | \(3q+2q^2+q^3+q^4\) | \(3q+2q^2+q^3+q^4\) |
| 2 | \(6q^2+7q^3+3q^4+5q^5\) | \(4q^2+11q^3+3q^4+q^5+2q^6\) |
| 3 | \(q+q^2+8q^3+15q^4+7q^5+3q^6\) | \(q+3q^2+4q^3+15q^4+11q^5+q^6\) |
| 4 | \(q+q^2+8q^3+15q^4+7q^5+3q^6\) | \(q+3q^2+4q^3+15q^4+11q^5+q^6\) |
| 5 | \(6q^2+7q^3+3q^4+5q^5\) | \(4q^2+11q^3+3q^4+q^5+2q^6\) |
| 6 | \(3q+2q^2+q^3+q^4\) | \(3q+2q^2+q^3+q^4\) |
| 7 | \(1\) | \(1\) |

The spectral graphs already differ in the binary sector. Their local height distinction does not require heights above one. This is useful evidence beyond the spectrum, but it does not yet demonstrate a benefit from nested thresholds. The binary pair was selected to make that second issue explicit.

| \(r\) | Common value \(I_{G_{\mathrm{bin}},r}=I_{H_{\mathrm{bin}},r}\) | Row sum at \(q=1\) |
|---:|---|---:|
| 0 | \(1\) | 1 |
| 1 | \(2q+2q^2+2q^3+q^4\) | 7 |
| 2 | \(2q^2+8q^3+5q^4+4q^5+2q^6\) | 21 |
| 3 | \(q^2+4q^3+13q^4+10q^5+5q^6+2q^7\) | 35 |
| 4 | \(q^2+4q^3+13q^4+10q^5+5q^6+2q^7\) | 35 |
| 5 | \(2q^2+8q^3+5q^4+4q^5+2q^6\) | 21 |
| 6 | \(2q+2q^2+2q^3+q^4\) | 7 |
| 7 | \(1\) | 1 |

**Exact computation SNG-E003.** Enumeration of all \(2^7=128\) binary assignments gives the second table identically for both binary graphs. This is equality of the complete two-variable binary polynomial, not merely equality at a chosen value of \(q\), equality of a few moments, or equality of one minimum-cut statistic. Under the usual changes of variables it is the same binary information encoded by an Ising polynomial with a field. The connection to that established literature does not make the next height sector redundant: it identifies exactly what the example must improve upon.

## The first local coefficients and their span decomposition

The coefficients of \(P_G\) are easy to derive at small volume. A volume-two vector either puts height two at one vertex or height one at each of two vertices. A volume-three vector has one of the patterns \(3\), \(2+1\), or \(1+1+1\). Evaluating the edge energy on each pattern gives

\[
A_1(q):=[x]P_G=\sum_iq^{d_i},
\]

\[
A_2(q):=[x^2]P_G=
\sum_iq^{4d_i}+\sum_{i<j}q^{d_i+d_j-2\epsilon_{ij}},
\]

\[
\begin{aligned}
A_3(q):=[x^3]P_G={}&\sum_iq^{9d_i}
+\sum_{i\ne j}q^{4d_i+d_j-4\epsilon_{ij}}\\
&+\sum_{i<j<\ell}q^{d_i+d_j+d_\ell
-2(\epsilon_{ij}+\epsilon_{i\ell}+\epsilon_{j\ell})}.
\end{aligned}
\]

These identities are **Proposition SNG-E004**, valid for every finite simple graph. For the interpretation as separate normalized span sectors at these volumes, there must be a zero coordinate; seven vertices certainly suffice. In the marked population, the three summands of \(A_3\) belong respectively to \(z^3,z^2,z^1\). The middle sum is over ordered pairs: the vertex receiving height two is distinguished from the vertex receiving height one. Its population size at \(q=1\) is \(7\cdot6=42\). The other two populations have sizes seven and thirty-five, adding to the eighty-four weak compositions of three into seven parts.

For the spectral pair the common linear coefficient is

\[
A_1=3q+2q^2+q^3+q^4.
\]

The two quadratic coefficients are

\[
A_{2,G_{\mathrm{sp}}}=6q^2+7q^3+6q^4+5q^5+2q^8+q^{12}+q^{16},
\]

\[
A_{2,H_{\mathrm{sp}}}=4q^2+11q^3+6q^4+q^5+2q^6+2q^8+q^{12}+q^{16}.
\]

Subtracting and factoring gives the exact identity

\[
\boxed{[x^2](P_{G_{\mathrm{sp}}}-P_{H_{\mathrm{sp}}})
=2q^2(1-q)^3(1+q).}
\tag{SNG-E005}
\]

The height-two-at-one-vertex terms cancel because the degree multisets coincide. The difference is entirely in the binary span-one sector. It is positive for every real \(0<q<1\), with exact value \(3/32\) at \(q=1/2\). Thus the distinction is not a numerical coincidence at one parameter or a sign-sensitive coefficient observed only after rounding.

The binary pair has common first and second coefficients

\[
A_1=2q+2q^2+2q^3+q^4,
\]

\[
A_2=2q^2+8q^3+7q^4+4q^5+2q^6+2q^8+2q^{12}+q^{16}.
\]

The span-one part of its cubic coefficient agrees because the binary table agrees. Its span-three part also agrees, since it only depends on degree:

\[
[x^3z^3]B_{G_{\mathrm{bin}}}
=[x^3z^3]B_{H_{\mathrm{bin}}}
=2q^9+2q^{18}+2q^{27}+q^{36}.
\]

It remains to inspect exactly forty-two ordered height patterns in the span-two part. The complete nonzero energy profiles are as follows; omitted energies have multiplicity zero in both graphs.

| Energy | \(G_{\mathrm{bin}}\) multiplicity | \(H_{\mathrm{bin}}\) multiplicity | Difference |
|---:|---:|---:|---:|
| 3 | 1 | 0 | 1 |
| 4 | 1 | 2 | -1 |
| 5 | 2 | 2 | 0 |
| 6 | 4 | 6 | -2 |
| 7 | 6 | 6 | 0 |
| 8 | 2 | 0 | 2 |
| 9 | 5 | 4 | 1 |
| 10 | 5 | 2 | 3 |
| 11 | 1 | 4 | -3 |
| 12 | 3 | 4 | -1 |
| 13 | 4 | 6 | -2 |
| 14 | 2 | 2 | 0 |
| 15 | 4 | 2 | 2 |
| 17 | 1 | 0 | 1 |
| 18 | 1 | 2 | -1 |
| Total | 42 | 42 | 0 |

**Exact computation SNG-E006.** The difference polynomial obtained from this profile is

\[
\begin{aligned}
\Delta(q)={}&q^3-q^4-2q^6+2q^8+q^9+3q^{10}-3q^{11}\\
&-q^{12}-2q^{13}+2q^{15}+q^{17}-q^{18}\\
={}&\boxed{q^3(1-q)(1-q^3)^2(1-q^4)^2}.
\end{aligned}
\]

The factorization is an exact polynomial identity, checkable by multiplication. Enumeration over all ternary assignments in \(\{0,1,2\}^7\) independently reproduces the same \(x^3\) span-two difference. Therefore

\[
[x^3z^2](B_{G_{\mathrm{bin}}}-B_{H_{\mathrm{bin}}})
=[x^3](P_{G_{\mathrm{bin}}}-P_{H_{\mathrm{bin}}})=\Delta(q).
\]

For every \(0<q<1\), this is strictly positive. At one half it is exactly \(11025/262144\). The factors at zero and one have straightforward meanings: zero eliminates all nonconstant heights on a connected graph, while one forgets energy and leaves the same number of assignments on seven coordinates. The additional factors at cube and fourth roots are an algebraic feature of this finite difference; no universal cyclotomic cancellation rule is inferred from them.

## What the analytic signatures see

For the primewise Euler lift, the singularity exponent at \(s=1\) is the common degree polynomial \(c_G(q)=\sum_iq^{d_i}\). Accordingly neither pair is distinguished by that leading exponent. The spectral pair shares

\[
c_{\mathrm{sp}}(q)=3q+2q^2+q^3+q^4,
\]

and the binary pair shares

\[
c_{\mathrm{bin}}(q)=2q+2q^2+2q^3+q^4.
\]

Both zero-parameter Euler products are \(\zeta(7s)\), because all four graphs are connected. The first minimum-cut correction also agrees within each pair. For the spectral graphs, the oriented minimum-cut side sizes occur with multiplicities three, one, one, three at sizes one, three, four, six. For the binary graphs only sizes one and six occur, each twice. If \(\mathcal P(s)=\sum_pp^{-s}\), the respective first corrections to \(\log(Z_G/\zeta(7s))\) are

\[
q\bigl(3\mathcal P(s)+\mathcal P(3s)+\mathcal P(4s)+3\mathcal P(6s)\bigr)
\]

and

\[
2q\bigl(\mathcal P(s)+\mathcal P(6s)\bigr).
\]

Those common signatures illustrate why a hierarchy is necessary. A graph can share degree data, a leading singular exponent, and its entire minimum-cut volume census with another graph while differing at a later local coefficient. After cancellation of the lower equal local coefficients, the first ratio singularity occurs at \(s=1/2\) for the spectral pair and \(s=1/3\) for the binary pair. Its exponent is respectively \(2q^2(1-q)^3(1+q)\) or \(\Delta(q)\). This is a local continuation statement on the positive-real branch for the ratio after cancellation; it is not a blanket meromorphic continuation of either original product.

The finite evidence supports a sharply bounded conclusion. The height-span marked invariant is strictly finer than its binary sector, and its unmarked specialization can distinguish a displayed Laplacian-cospectral pair. Both examples also distinguish vertex realizations with isometric ordinary cut lattices. The evidence does not prove completeness, does not show that the unmarked series always recovers the binary sector, and does not establish an efficient algorithm for general graph isomorphism. What has been established is a concrete, exact relational distinction and an analytic language that records where that distinction first appears.

## A regular calibration: the cube and the Möbius ladder

A third comparison tests the low-volume blindness of regular graphs proved in the inverse-problems chapter. Let \(Q_3\) be the cube graph on binary vertex labels \(0,\ldots,7\), with an edge whenever two labels differ in one binary digit. Let \(M_8\) be the eight-cycle together with the four opposite-vertex chords. Their edge sets are fixed here to make the computation reproducible.

| Graph | Edge set |
|---|---|
| \(Q_3\) | \(01,02,04,13,15,23,26,37,45,46,57,67\) |
| \(M_8\) | \(01,04,07,12,15,23,26,34,37,45,56,67\) |

Both graphs have eight vertices, twelve edges, degree three at every vertex, and no triangles. They are nonisomorphic for a simple reason. The cube is bipartite: the parity of the number of ones in the binary label changes across every edge. The ladder contains the five-cycle \(0,1,2,3,4,0\), using its opposite chord \(04\), and therefore is not bipartite. No spectral calculation is needed for that nonisomorphism witness.

The common local coefficients through volume three are

\[
A_0=1,\qquad A_1=8q^3,
\]

\[
A_2=12q^4+16q^6+8q^{12},
\]

\[
A_3=24q^5+24q^7+8q^9+24q^{11}+32q^{15}+8q^{27}.
\]

Their span decompositions also agree. This agreement is predicted by the theorem that order, regular degree and triangle count determine the marked coefficients through volume three. It is therefore a mathematically controlled delay, rather than an unexplained failure of the population calculation. At volume four the binary subsets already distinguish the graphs:

| Graph | Binary four-vertex cut polynomial | Number of subsets |
|---|---|---:|
| \(Q_3\) | \(6q^4+32q^6+30q^8+2q^{12}\) | 70 |
| \(M_8\) | \(4q^4+40q^6+18q^8+8q^{10}\) | 70 |

The six cube subsets of boundary size four are its six square faces. Its two four-vertex subsets of boundary size twelve are its bipartition classes, each containing no internal edges. The ladder has no such boundary-twelve four-subset, consistently with the absence of a bipartition into independent four-sets. The other coefficients count the remaining labeled subsets, rather than quotienting them by graph symmetries.

**Exact computation SNG-E007.** The first full local difference is

\[
[x^4](P_{Q_3}-P_{M_8})
=[x^4z](B_{Q_3}-B_{M_8})
=\boxed{2q^4(1-q^2)^4}.
\]

All other span sectors at volume four agree. The value at \(q=1/2\) is \(81/2048\). At the next volume the difference moves to span two:

\[
[x^5](P_{Q_3}-P_{M_8})
=[x^5z^2](B_{Q_3}-B_{M_8})
=\boxed{8q^9(1-q^2)^2(1-q^4)^2}.
\]

Its value at one half is \(2025/262144\). These identities were replayed using exact coefficient enumeration with the displayed edges. Their status is exact finite computation, followed by exact polynomial factorization. The first ratio singularity of this pair is at \(s=1/4\), with exponent \(2q^4(1-q^2)^4\), after the equal lower-volume terms are cancelled. The common leading exponent at \(s=1\) is \(8q^3\).

This pair is not another collision of the complete binary polynomial. It agrees only in the early coefficients and separates in a binary sector at volume four. The nonbinary discrepancy at volume five adds an example of how span information is distributed, but is not needed to distinguish the graphs once the binary four-subset census is available. Its role is calibration: it demonstrates a predicted limitation of very early coefficients and provides a positive check that the next level responds to a concrete structural difference.

## Reading the examples as a controlled experiment

The two pairs answer related but different objections. One might first suspect that the construction is simply a complicated way to reproduce the eigenvalues of a graph Laplacian. The spectral pair rules out that interpretation: the entire Laplacian characteristic polynomial agrees, while a positive difference appears at volume two for every interior real parameter. One might then suspect that the extra information is entirely the familiar information obtained by considering all binary cuts and remembering their side sizes. The binary pair rules out that second interpretation: every binary coefficient agrees, while a positive difference appears in the next height span. The experimental sequence is therefore a sequence of exact controls, not a ranking based on a few numerical scores.

The controls are intentionally strong within their stated scope. Both pairs have the same degree multiset, so a singleton degree statistic cannot explain either separation. Both also share their number of components, spanning-tree count, edge connectivity and minimum-cut volume census. Those equalities do not make the examples universally difficult. A simple neighborhood statistic separates each pair, and the second pair has different Laplacian spectra. The point is to identify a definite piece of information that the height population retains, not to pretend that no other mathematical description can retain it.

For the binary pair, the first additional statistic is particularly transparent. An ordered pair \((i,j)\) receives heights two and one. Its energy is \(4d_i+d_j-4\epsilon_{ij}\). A binary pair only sees \(d_i+d_j-2\epsilon_{ij}\), without distinguishing which endpoint is emphasized. The complete binary triple census adds many constraints, but it still does not force the displayed ordered-pair energy distribution. The table supplies a direct counterexample. The new information is a degree and adjacency mixing statistic that is visible through an asymmetric height pattern and is then aggregated without labels.

The analytic ratio does not create that statistic. It transports an already established local discrepancy into a location on the real singularity ladder. The spectral pair first differs at an exponent sum of two and therefore has its first ratio singularity at one half. The binary pair first differs at an exponent sum of three and therefore has its first ratio singularity at one third. This interpretation is helpful because it connects a combinatorial order of distinction to an analytic scale, while keeping the logical direction clear: the exact coefficient calculation comes first, and the analytic statement follows from it.
