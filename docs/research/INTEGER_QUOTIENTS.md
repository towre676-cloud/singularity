# NX19: integer-compatible observational quotients

The rational observable quotient answers which directions can ever affect an experiment. It does not automatically describe which integer coordinates are attainable, how many original objects lie above one output, or which congruences a quotient transition must preserve. This companion supplies those arithmetic contracts using exact Smith certificates and finite original-coordinate populations.

## Denominator clearing retains the original observation map

Given an exact rational observation matrix \(B\), clear each row's denominators separately with a positive integer diagonal matrix \(S\). The constructor retains

\[
 A=SB\in\mathbb Z^{r\times D}
\]

and the individual row scales. Its image lattice is \(A\mathbb Z^D\), not necessarily all integer points of the rational row-image space. A row scale changes representation; it does not rescale a physical noise bound or measurement cost unless the caller also supplies that change.

The certificate stores integer matrices \(U,V\) with determinant \(\pm1\), and a rectangular Smith diagonal

\[
 UAV=\operatorname{diag}(d_1,\ldots,d_s,0,\ldots),\qquad
 d_i>0,\quad d_i\mid d_{i+1}.
\]

The constructor uses elementary row and column additions, swaps and signs. Euclidean reduction clears the pivot row and column. If the resulting pivot does not divide a trailing entry, that row is added back to the pivot row and Euclidean reduction continues with a smaller pivot. When it divides every trailing entry, the algorithm advances. Explicit operation and entry-bit budgets stop coefficient growth honestly.

The verifier is smaller than this construction. It validates dimensions and integer types, multiplies \(UAV\), checks every diagonal and zero entry, checks positivity/divisibility, and computes the two determinants exactly. It never calls the Smith constructor. Booleans are rejected as integer entries.

## Image membership and a saturated fibre

For a proposed integral output \(y\), write \(u=Uy\). Unimodularity gives an exact integer change of coordinates \(x=Vz\), so

\[
 y\in A\mathbb Z^D
 \iff d_i\mid u_i\ (i\le s),\qquad u_i=0\ (i>s).
\]

When these conditions hold, put \(z_i=u_i/d_i\) for \(i\le s\), and set remaining coordinates to zero for one particular solution. Every integer solution is

\[
 x=x_0+\sum_{j=s+1}^D t_j V_{[:,j]},\qquad t_j\in\mathbb Z.
\]

**Proposition NX19.1.** A replayed Smith certificate, the displayed divisibility test, and the displayed affine basis describe exactly the integral image and the full integer fibre.

**Proof.** Because \(U\) and \(V\) are integer unimodular matrices, both coordinate changes and their inverses preserve integer vectors. The equation becomes a diagonal system. Each nonzero diagonal coordinate has the unique stated integer solution; zero diagonal coordinates require zero transformed output and leave all corresponding \(z_j\) free. Transforming back gives all and only original integer solutions. □

The integer kernel is saturated: if \(k x\) is in the kernel for a nonzero integer \(k\), then \(kAx=0\) in the torsion-free group \(\mathbb Z^r\), so \(Ax=0\). The image need not be saturated. These statements are different.

For \(A=(2,1,1)\), independently clearing denominators of a rational nullspace basis can give \((-1,2,0)\) and \((-1,0,2)\), whose integer span misses \((-1,1,1)\). The Smith fibre contains the missing vector. This permanent regression prevents a rational kernel from being mislabeled a complete integer kernel.

## Original objects, finite completion counts, and multiplicity

An affine integer fibre can be infinite. Counting requires explicit inclusive bounds on every original coordinate. `BoundedFibrePopulation` retains the original tuple order and memoizes completion counts by coordinate position and residual output. Before branching, exact rowwise lower/upper bounds discard impossible residuals. The resulting recursion counts original labeled tuples without enumerating a Smith-coordinate box or sorting by a transformed order.

`count`, `contains`, `rank` and `unrank` all refer to those original tuples. Rank is zero-based lexicographic rank. `pushforward_population` enumerates a separately bounded original domain and sums multiplicities over outputs. Its total mass equals the original domain size by construction, and tests compare every fibre and every rank inverse with independent direct lexicographic enumeration.

For \(A=(2,2)\) and binary original states, the image is \(\{0,2,4\}\) with weights \(1,2,1\). Output one is impossible despite a rational solution. Output two has two original states, \((0,1)\) and \((1,0)\). The quotient identifier does not collapse their multiplicity. The retained JSON stores the affine description and the two bounded objects separately.

The exhaustive Smith corpus contains 837 matrices: every matrix with entries in \(\{-1,0,1\}\) of shapes \(1\times3\), \(2\times2\), and \(3\times2\). All 8,019 original states in the declared small boxes are independently checked for image membership. Additional population tests cover rank zero, full rank, rectangular maps, nontrivial denominator clearing and the saturation regression.

## Quotient updates and the image-lattice domain

Suppose an ambient transition \(M\) preserves \(\mathbb Z^D\). This implementation requires every entry of \(M\) to be integral; a rational matrix can preserve the standard integer lattice only under that condition. A different invariant lattice needs a different explicit contract.

The transition descends to the observation quotient exactly when it preserves the observation kernel. The constructor checks this on the full Smith integer-kernel basis. It then constructs a rational output map \(Q\) and verifies directly

\[
 QA=AM.
\]

The map \(Q\) may contain fractions. Its certified domain is \(A\mathbb Z^D\), and every accepted update checks membership before application. For example, with \(A=\operatorname{diag}(2,1)\) and coordinate swap \(M\),

\[
 Q=\begin{pmatrix}0&2\\1/2&0\end{pmatrix}.
\]

It sends the realizable output \((2,3)\) to \((6,1)\). An arbitrary integer vector \((1,3)\) is rejected before its fractional update can be mistaken for a legal state. A rational ambient half-scaling is rejected for failure of standard-lattice preservation. A diagonal ambient update that does not preserve an observation kernel is rejected for a different reason.

Integer states and their multiplicities are preserved through these transitions. The packet does not authorize merging original seeds, graph labels, or height assignments after quotienting. An affine update can be handled only after adding and constraining a homogeneous coordinate; no unconstrained affine API is claimed here.

## Portable contract and reproduction

The schema `singularity.integer-image/1` includes the canonical original rational matrix, its cleared integral matrix, row scales, \(U,V\), diagonal, rank, original coordinate order and operation/bit resource counts. Malformed diagonals, nonunimodular transformations and forged identities fail replay. Changing a row scale without changing the original-map identity also fails replay. Zero-row input denotes a zero-by-zero map; a zero observation on a positive-dimensional state should be represented by an explicit all-zero row so dimension is retained.

Implementation: `src/singularity/integer_quotients.py`. Tests: `tests/test_integer_quotients.py`. Run `python scripts/integer_quotients.py --check`. Other tracks can consume `image_contains` as a necessary membership predicate without adopting Smith coordinates. In particular, arithmetic compatibility of an interface vector is not sufficient graph realizability: nonlinear slice identities and a common adjacency matrix remain additional constraints. Rational minimal dimension and faithful integer population representation are distinct optimization goals.
