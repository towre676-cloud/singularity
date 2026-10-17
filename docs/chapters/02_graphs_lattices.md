# 2. Graphs, integral cut lattices, and the height mark

## 2.1 The quadratic form and its kernel

Let \(G\) have adjacency matrix \(A\), degree matrix \(D=\operatorname{diag}(d_i)\), and combinatorial Laplacian \(\Delta_G=D-A\). Expanding each square in the definition of energy gives
\[
E_G(a)=a^\top\Delta_Ga
=\sum_i d_i a_i^2-2\sum_{\{i,j\}\in E}a_i a_j.
\]
The Laplacian is symmetric and positive semidefinite. This is stronger than a numerical spectral observation: the displayed edge-sum expression proves positivity for every real vector.

**Theorem SNG-F04 (zero energy and component constants).** For \(a\in\mathbb R^k\), \(E_G(a)=0\) if and only if \(a\) is constant on each connected component. In particular, for connected \(G\), \(\ker\Delta_G=\mathbb R\mathbf1\).

*Proof.* A finite sum of nonnegative squares vanishes precisely when every summand vanishes. Thus adjacent vertices must have equal coordinates. Equality propagates along paths, proving constancy on every component. The converse follows because every edge lies within a component. Finally, \(\Delta_Ga=0\) implies \(a^\top\Delta_Ga=0\); component constancy also directly implies \(\Delta_Ga=0\). \(\square\)

For connected graphs, the zero direction is common translation. For disconnected graphs there are additional zero directions: different components can be shifted independently. This difference matters when a formal series is evaluated without its height mark. Quotienting only by global translation does not remove all zero modes of a disconnected graph.

## 2.2 An orientation is a bookkeeping choice

Choose an arbitrary orientation of every edge. Let \(\partial\) be the \(|E|\)-by-\(k\) matrix whose row for an oriented edge \(i\to j\) has \(-1\) in column \(i\), \(+1\) in column \(j\), and zero elsewhere. Then
\[
(\partial a)_{i\to j}=a_j-a_i,
\qquad \partial^\top\partial=\Delta_G.
\]
The image
\[
\mathcal C(G)=\partial\mathbb Z^k\subseteq\mathbb Z^E
\]
is the integral cut, or tension, lattice in this convention. It consists of edge differences produced by integer vertex potentials. An arbitrary integer edge vector need not lie in this image: differences around every oriented cycle must sum to zero.

Reversing an edge orientation multiplies the corresponding coordinate by \(-1\). This is an integral orthogonal transformation of \(\mathbb Z^E\). It preserves inner products, squared lengths, and every energy count. An orientation is therefore needed to write vectors, but none of the observations depends on it.

**Theorem SNG-F05 (integer quotient and cut-lattice coordinates).** If \(G\) is connected, \(a\mapsto\partial a\) induces an isomorphism of abelian groups
\[
\mathbb Z^k/\mathbb Z\mathbf1\ \cong\ \mathcal C(G).
\]
Under this isomorphism, squared lattice length is \(E_G(a)\). If a root vertex \(r\) is fixed and \(\Delta_G^{(r)}\) is obtained by deleting row and column \(r\), the energy in rooted coordinates is the positive-definite integral form
\[
u^\top\Delta_G^{(r)}u,\qquad u\in\mathbb Z^{k-1}.
\]

*Proof.* The map is surjective onto its stated image. Its integer kernel consists of constant integer vectors by Theorem SNG-F04. The first isomorphism theorem gives the quotient description. The equality of squared length and energy follows from \(\partial^\top\partial=\Delta_G\). Every integer translation class has a unique representative with coordinate \(a_r=0\), obtained by subtracting \(a_r\mathbf1\). Substitution gives the reduced quadratic form. If that form vanishes, its full representative is constant and has root coordinate zero, so it is zero. The form is therefore positive definite. \(\square\)

The root-zero representative is particularly convenient for linear algebra. It may have negative coordinates. The minimum-zero representative used by \(B_G\) is particularly convenient for a nonnegative height mark. These are two coordinate choices on the same quotient, not two different populations of translation classes.

## 2.3 A determinant that counts trees

The determinant of the reduced Laplacian gives a useful consistency check connecting the integer form with ordinary graph structure. We include a proof because it makes clear which combinatorial data enter the lattice and because no floating-point eigenvalue calculation is needed.

**Theorem SNG-F06 (matrix-tree determinant).** For connected \(G\) on \(k\ge2\) vertices and any root \(r\),
\[
\det\Delta_G^{(r)}=\tau(G),
\]
where \(\tau(G)\) is the number of spanning trees of \(G\).

*Proof.* Delete column \(r\) of \(\partial\), obtaining \(M\). Then \(\Delta_G^{(r)}=M^\top M\). The Cauchy–Binet formula gives
\[
\det(M^\top M)
=\sum_{F\subseteq E,\ |F|=k-1}\det(M_F)^2,
\]
where \(M_F\) restricts \(M\) to the selected edge rows. If \((V,F)\) is disconnected, choose a component not containing \(r\). Its indicator vector, restricted to nonroot coordinates, is a nonzero vector killed by \(M_F\), so the determinant is zero. A connected graph with \(k\) vertices and \(k-1\) edges is a tree. For a tree, the determinant is \(\pm1\): repeatedly choose a nonroot leaf, expand in its column, and delete the leaf and its incident edge. Each expansion contributes a sign and an entry \(\pm1\); the final empty determinant is one. Thus exactly the spanning-tree subsets contribute one to the sum. \(\square\)

The theorem identifies a lattice determinant. It does not say that this determinant determines the lattice or the graph. Many nonisomorphic graphs have the same number of spanning trees. Even a complete list of real Laplacian eigenvalues describes the quadratic form only up to real orthogonal change of coordinates, whereas an integer height population depends on where the integer lattice sits inside that real space.

This distinction is elementary but decisive. A real orthogonal matrix preserves lengths of all real vectors. It need not map \(\mathbb Z^{k-1}\) to itself. An integral change of lattice basis must lie in \(\mathrm{GL}_{k-1}(\mathbb Z)\), a much more restrictive group. Consequently equal real spectra alone do not supply a bijection between integer height profiles.

## 2.4 Unmarked theta and the extra information in a mark

For connected \(G\), the unmarked cut-lattice theta series is
\[
\Theta_G(q)=\sum_{u\in\mathbb Z^{k-1}}
q^{u^\top\Delta_G^{(r)}u}.
\]
Changing the root changes the integral coordinates but not the translation classes being counted. Likewise, an integral isometry of cut lattices preserves this series. Graph cut lattices and their relationship with graph structure have a substantial established theory; [BHN1997] provides relevant background. No converse classification from theta-series equality is assumed here.

**Theorem SNG-F07 (finite energy shells and convergence).** If \(G\) is connected and \(k\ge2\), every energy coefficient of \(\Theta_G\) is finite, and the series converges absolutely for \(|q|<1\). Moreover,
\[
\Theta_G(q)=B_G(1,q)
\]
as a coefficientwise formal energy series and, for \(|q|<1\), as a convergent sum.

*Proof.* In root-zero coordinates, join \(r\) to each vertex \(i\) by a simple path of length at most \(k-1\). The telescoping sum of edge differences and Cauchy–Schwarz give
\[
u_i^2\le(k-1)E_G(u),\qquad
\sum_{i\ne r}u_i^2\le(k-1)^2E_G(u).
\]
An energy shell \(E_G(u)=e\) therefore lies in a finite integer box. If \(0<\rho<1\), then
\[
\rho^{E_G(u)}
\le\rho^{\|u\|_2^2/(k-1)^2},
\]
and the sum of the right side is a product of convergent one-dimensional Gaussian sums. The case \(q=0\) is immediate. Finally, root-zero and minimum-zero profiles each select exactly one representative of every translation class and preserve energy. Their energy sums coincide. \(\square\)

For a disconnected graph with at least two nonempty components, \(B_G(1,q)\) generally diverges, even for \(0<q<1\): set one component to height zero and another to arbitrary common height. These are distinct normalized zero-energy profiles. The true cut lattice quotients by componentwise constants, while our normalization quotients by one global constant. Those constructions must not be silently identified.

The total-height mark retains a feature that the lattice norm alone does not name. For an arbitrary integer representative \(a\), define
\[
\mu([a])=\sum_i a_i-k\min_i a_i,
\qquad
\eta([a])=\max_i a_i-\min_i a_i.
\]
Both are well defined on translation classes. They equal volume and span on the minimum-zero representative. The marked theta population is therefore a lattice together with extra functions on its elements. An abstract norm-preserving lattice bijection need not preserve those functions.

## 2.5 The height mark is an asymmetric gauge

The function \(\mu\) is not a linear functional on the quotient. A change in which vertex attains the minimum changes its formula. This nonlinearity is part of what the mark observes, rather than a defect in the normalization.

**Theorem SNG-F08 (gauge identities and complement reciprocity).** On \(\mathbb Z^k/\mathbb Z\mathbf1\), the functions \(\mu\) and \(\eta\) satisfy
\[
\mu(\alpha+\beta)\le\mu(\alpha)+\mu(\beta),
\qquad \mu(t\alpha)=t\mu(\alpha)\quad(t\in\mathbb Z_{\ge0}),
\]
\[
\mu(\alpha)+\mu(-\alpha)=k\eta(\alpha).
\]
For fixed span \(h\), put \(B_{G,h}(x,q)=[z^h]\mathcal B_G(x,q,z)\). This is a polynomial and obeys
\[
B_{G,h}(x,q)=x^{kh}B_{G,h}(x^{-1},q).
\]

*Proof.* For representatives \(a,b\), \(\min_i(a_i+b_i)\ge\min_i a_i+\min_i b_i\); subtracting \(k\) times this inequality from the coordinate sum proves subadditivity. Nonnegative integer homogeneity is immediate. Also \(\min(-a)=-\max(a)\), so adding the formulas for \(\mu([a])\) and \(\mu([-a])\) gives \(k(\max a-\min a)\). For reciprocity, every normalized span-\(h\) profile has coordinates in \(\{0,\ldots,h\}\), so the set is finite. The involution \(a\mapsto h\mathbf1-a\) preserves energy, exchanges minimum and maximum, and changes volume from \(m\) to \(kh-m\). Summing over the involution proves the identity. \(\square\)

The reciprocity is spanwise. After setting \(z=1\), profiles with many different \(h\) are merged, and there is no single factor \(x^{kh}\) applying to their sum. This is a concrete example of a relation visible with the full mark but not immediately expressible after that mark is forgotten.

| Structure retained | Natural coordinate change | Quantity necessarily preserved |
|---|---|---|
| Real quadratic space | Real orthogonal isometry | Real energy |
| Integral cut lattice | Integral lattice isometry | Integer energy shells |
| Height-marked lattice population | Bijection preserving energy and \(\mu\) | Joint volume-energy counts |
| Fully marked population | Bijection preserving energy, \(\mu\), and \(\eta\) | Joint volume-energy-span counts |

These rows are preservation requirements, not a claim that every bijection in a lower row arises from graph relabeling. The inverse problem asks precisely how much of the source graph is forced by increasingly restrictive observations.

## 2.6 Two endpoint calculations

At \(q=1\), energy is forgotten completely. Every coordinate contributes its own geometric series, so
\[
L_G(x,1)=\frac1{(1-x)^k},\qquad
B_G(x,1)=\frac{1-x^k}{(1-x)^k}.
\]
No edge appears in these expressions. At \(q=0\), only zero-energy assignments remain. If the connected components have sizes \(k_1,\ldots,k_c\), Theorem SNG-F04 gives
\[
L_G(x,0)=\prod_{j=1}^c\frac1{1-x^{k_j}},
\qquad
B_G(x,0)=(1-x^k)\prod_{j=1}^c\frac1{1-x^{k_j}}.
\]
For connected graphs this reduces to \(L_G(x,0)=1/(1-x^k)\) and \(B_G(x,0)=1\). Thus both endpoints erase most graph structure: one ignores every edge energy, and the other retains only exact agreement within components. An inverse experiment must retain intermediate energy information rather than relying on these endpoint values alone.

## 2.7 Disjoint unions and recoverable component sizes

The unnormalized series factors naturally over independent components. Normalization by one global minimum does not factor in the same way, because choosing the minimum of the combined profile couples the choice of representatives in its components. This is a useful instance in which an exact quotient must be carried through an otherwise simple product rule.

**Theorem SNG-F19 (component factorization and its endpoint inverse).** For graphs \(G,H\) on \(k,\ell\ge1\) vertices,
\[
L_{G\sqcup H}(x,q)=L_G(x,q)L_H(x,q),
\]
\[
B_{G\sqcup H}(x,q)
=\frac{1-x^{k+\ell}}{(1-x^k)(1-x^\ell)}B_G(x,q)B_H(x,q).
\]
Moreover, the zero-energy series \(L_G(x,0)\) determines the multiset of connected-component sizes.

*Proof.* A profile on a disjoint union is uniquely a pair of profiles on its components. Both volume and energy add, proving the first identity. Substituting \(L_G=B_G/(1-x^k)\), and the corresponding formulas for \(H\) and the union, proves the second identity in formal series. For the final assertion, let \(c_j\) be the number of components of size \(j\). Then
\[
L_G(x,0)=\prod_{j\ge1}(1-x^j)^{-c_j}.
\]
Formal logarithms are legitimate because the constant term is one. Expanding \(-\log(1-x^j)=\sum_{r\ge1}x^{jr}/r\), put \(b_n=n[x^n]\log L_G(x,0)\). Then
\[
b_n=\sum_{j\mid n}j c_j.
\]
Recover \(c_1=b_1\) and recursively
\[
c_n=\frac1n\left(b_n-\sum_{\substack{j\mid n\\j<n}}j c_j\right).
\]
This uniquely determines every component-size multiplicity. Only finitely many are nonzero. \(\square\)

The inverse statement is deliberately modest. Zero energy knows component sizes but not the edges within a component. A path and a complete graph on the same connected vertex set have identical zero-energy series. The formal logarithm extracts exactly the available component information without pretending that it contains finer internal structure.

There is a related warning about the full span mark. The span of a concatenated pair of arbitrary profiles depends on their relative vertical placement, not just on the two individual spans. Consequently one should not multiply \(\mathcal B_G\) and \(\mathcal B_H\) and declare the result to be \(\mathcal B_{G\sqcup H}\). A correct marked factorization would need enough additional data to retain minima, maxima, and their relative shifts. The scalar unnormalized product avoids that missing correspondence because it sums actual coordinates before applying a quotient.

The cut-lattice description clarifies why integer heights are a useful meeting point. They retain the arithmetic placement of a quadratic form, while their minimum-zero representatives supply a nonlinear order mark. The next chapter expresses that order mark through nested threshold sets. This reveals precisely what lies beyond a single binary cut.
