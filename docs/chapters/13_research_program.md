# 13. A mathematical research program with distinct proof routes

## 13.1 The question that organizes the program

The program asks how much relational information survives when labeled integer height profiles are counted by volume and quadratic edge energy, and how a first finite discrepancy becomes visible in an arithmetic Euler product. It is a question about explicit combinatorial and analytic objects. It does not require a universal theory of every obstruction, a claim that all graph information has been recovered, or an interpretation of the Euler product as a source of additional graph data. The local series supplies the data; the arithmetic product changes where and how a discrepancy is expressed.

Three levels of progress should remain distinct. A structural theorem explains an entire graph class or a transformation law. An exact counterexample separates two stated invariants. A complete finite census establishes a bounded classification relative to a documented input population. Each can support a paper, but they answer different questions. The 36 pushes in `docs/development/PUSHES.md` are a dependency plan for obtaining these results, not a list of results already achieved. Negative outcomes are legitimate endpoints when they are recorded with the same precision as successful separations.

## 13.2 Tree messages and separator geometry

Trees provide the first substantial algorithmic theorem target because conditioning on a vertex height separates the descendant subtrees. Root a tree and let \(F_v(t;x,q)\) count assignments on the subtree at \(v\), with \(a_v=t\). With heights bounded by \(H\), the exact recursion is

\[
F_v(t)=x^t\prod_{u\text{ child of }v}\left(\sum_{j=0}^{H}q^{(t-j)^2}F_u(j)\right).
\]

The local bounded-height polynomial is \(\sum_tF_{\rm root}(t)\). Truncating every product modulo \(x^{R+1}\) preserves all coefficients through volume \(R\), because every volume exponent is nonnegative. Taking \(H=R\) therefore computes the unrestricted local series through that volume. A proof should specify where the root vertex weight is charged and where each edge is charged; double-counting either invalidates an otherwise plausible recursion.

The same bounded-height computation recovers span marking without tracking both extrema in every message. Let \(C_H\) count profiles with every height in \(\{0,\ldots,H\}\), and set \(C_{-1}=0\). The polynomial \(D_H=C_H-x^n C_{H-1}\) counts profiles with minimum zero and maximum at most \(H\). Hence \(D_H-D_{H-1}\) counts exact span \(H\). This follows by subtracting profiles whose minimum is positive and shifting them down by one. It is a useful proposed implementation path because its correctness reduces to a simple bijection rather than an enlarged and difficult-to-audit message state.

For general graphs, a tree decomposition replaces a single parent height by a tuple of heights on a separator. The number of assignments to a bag of size \(w+1\) is \((H+1)^{w+1}\); this is only the state-count contribution, not the full arithmetic complexity. Volume and energy polynomials still require exact convolutions. The research objective is a correctness theorem together with measured support growth on paths, stars, balanced trees, cycles, and bounded-width constructions. A speed claim should compare complete identical coefficient ranges against the reference enumerator, not compare a marked computation with an unmarked one.

## 13.3 What nested boundaries remember

The span-one sector records a cut-size distribution indexed by the size of a side. Span two introduces ordered nested pairs \(T\subseteq S\), with volume \(|S|+|T|\) and energy \(|\delta S|+|\delta T|+2e(T,V\setminus S)\). Thus two cuts with the same individual sizes and boundary sizes can contribute differently because the graph places their boundaries differently. This is an explicit refinement mechanism. It should not be described as a higher-body interaction: the original energy remains a sum over graph edges.

A useful new intermediate object is the finite nested-pair census indexed by \((|S|,|T|,|\delta S|,|\delta T|,e(T,V\setminus S))\). Its purpose is diagnostic. If binary-equivalent graphs first separate at span two, the census can identify which mixed boundary statistic causes that separation. Higher nested censuses are defined similarly, but their dimension grows quickly. The right theorem is not that more marks are always better; it is an explicit projection identity and, when available, a pair of graphs demonstrating that one projection loses information retained by another.

Minimum cuts provide a complementary asymptotic direction. On a connected graph, a nonconstant binary profile has positive energy, and the least such energy is the edge-connectivity. Its side-size multiplicities are visible in the marked binary sector. Nonbinary profiles can have energy tied to several nested boundaries, so identifying the first low-energy terms of the complete normalized series requires an argument about all heights. A promising target is a characterization of the minimum positive energy and its minimizing profiles, followed by a classification of the next energy layer. Each statement should distinguish energy ordering from volume ordering, since the Euler visibility theorem uses the latter.

## 13.4 Matroids, cut lattices, and the role of a positive chamber

The quadratic form \(a\mapsto a^\top L_Ga\) factors through integer height vectors modulo constants. Sending a height vector to its oriented edge differences identifies this quotient, in the connected case, with the integral cut lattice equipped with its Euclidean energy. This is established territory. The additional marks in this project are not automatically invariants of an abstract lattice: choosing the minimum-zero representative and taking its coordinate sum uses the vertex-height realization of that lattice. Span also uses that realization.

The corresponding research question is precise: which parts of \(B_G(x,q,z)\) are determined by the metric cut lattice, which are determined by the graphic matroid, and which require additional vertex information? Whitney switches are a natural test population because they preserve cycle-matroid structure under the appropriate hypotheses. A complete search can either produce a separating pair, thereby disproving a proposed factorization through the matroid, or identify a transformation law worth proving. Failure to find a small separating pair is not proof of matroid invariance.

This path is especially useful because it can explain a collision rather than merely record one. If an equality comes from an integral lattice isometry that also preserves the chosen height chamber and marks, then a structural bijection may exist. If an isometry preserves energy but moves the chamber or the volume functional, the resulting failure identifies exactly which extra structure the series observes. The intended publication contribution would be a theorem describing such preservation or failure, with an explicit worked graph pair, rather than a broad claim that graph polynomials and lattices are connected.

## 13.5 Root-of-unity specializations as finite exact laboratories

Let \(\omega\) have order \(m\). Write every nonnegative height uniquely as \(a_i=r_i+mb_i\), with \(0\le r_i<m\). Since energy is an integer quadratic form, \(E_G(a)\equiv E_G(r)\pmod m\). Summing the independent nonnegative \(b_i\) gives the exact identity

\[
L_G(x,\omega)=\frac{\sum_{r\in\{0,\ldots,m-1\}^n}x^{\sum_i r_i}\omega^{E_G(r)}}{(1-x^m)^n}.
\]

An infinite height population therefore becomes a finite residue-cube numerator at each root-of-unity specialization. This identity is a direct consequence of residue decomposition; it is not a claim of new arithmetic theory. It offers a particularly clean computational bridge because all coefficients can be represented exactly in a cyclotomic ring, and equality can be decided by reduction modulo its defining polynomial.

At \(q=-1\), the result collapses further. Squares agree with their bases modulo two, so \(E_G(a)\equiv\sum_i d_i a_i\pmod2\), and

\[
L_G(x,-1)=\prod_i\bigl(1-(-1)^{d_i}x\bigr)^{-1}.
\]

This specialization sees only degree parity counts. It supplies both a theorem and a warning: an elegant arithmetic specialization can discard most graph information. At odd primes, evaluating the finite numerator at \(x=1\) produces a quadratic Gauss sum for the Laplacian over a finite field. Rank and the discriminant of its nonsingular part become relevant. The singular constant direction must be accounted for, and prime powers need their own lifting argument; an odd-prime formula must not be reused at two.

There is a separate root-of-unity filter in the volume variable. Averaging \(L_G(\omega^j x,q)\) with character weights isolates volumes in a chosen congruence class. It does not isolate binary profiles or recover span after setting \(z=1\). Both kinds of specialization are worthwhile because they provide finite exact comparison problems with different information loss. The positive-real visibility theorem for \(0<q<1\) does not automatically extend to complex \(q\), where local factors may vanish and a logarithm needs an explicitly chosen domain.

## 13.6 Order chambers and weighted lattice-point geometry

Every height profile has a unique order obtained by sorting vertices first by height and then by label. For a permutation \(\pi\) in that order, introduce \(d_0=a_{\pi_1}\) and \(d_j=a_{\pi_{j+1}}-a_{\pi_j}\) for \(1\le j<n\). These gaps are nonnegative, with \(d_j>0\) whenever \(\pi_j>\pi_{j+1}\), because an adjacent descent cannot occur inside a tied block. The resulting chambers are disjoint, including their prescribed boundaries. Volume becomes \(nd_0+\sum_{j=1}^{n-1}(n-j)d_j\), and energy becomes an explicit quadratic form in the remaining gaps.

This description links the population to familiar order and lattice-point methods while retaining a concrete accounting benefit. It can expose which cross terms depend on the relative placement of cuts, and it gives another independent enumerator. The marks are not automatically Ehrhart polynomials. Unweighted integer points in a dilated fixed rational polytope admit established Ehrhart theory; weighting them by \(q\) to a quadratic energy introduces an additional structure. Any reciprocity statement must specify whether it concerns unweighted counts, a formal weighted series, or a transformed analytic function, and must prove the claimed boundary terms.

The intended order-theoretic theorem target is a chamber formula with a correct treatment of ties, followed by reductions for graph families with a controlled set of chamber types. An algorithm summing all \(n!\) orders may be a useful check without being a useful large-scale algorithm. A later symmetry reduction must preserve the original labeled multiplicities. Successful chamber identities would provide exact explanations for some coefficient factorizations, rather than relying on numerical pattern recognition.

## 13.7 Visibility strata and formal proof priorities

For fixed graph pairs, coefficient differences are polynomials in \(q\). Their common vanishing defines exceptional parameter values where the first discrepancy moves to a later volume. The generic first discrepancy and its exceptional set should be computed separately. At a rational parameter, direct substitution determines whether a proposed exponent survives. At an algebraic parameter, reduction by a minimal polynomial gives an exact test. Sampling several real values cannot prove that a discrepancy has no interior zero.

The analytic path starts with a finite certified coefficient discrepancy, then proves a local factor expansion and a uniformly convergent normalized prime product in the stated real domain. More cancellations can move the remainder convergence boundary; they do not justify a global meromorphic continuation of the original product. Nonintegral exponents require positive-real branches or explicitly described local complex branches. The project should seek quantitative remainder bounds uniform on compact parameter intervals away from exceptional points, so numerical demonstrations become reproducible approximations to an already stated theorem.

Formalization should follow the dependency order of the mathematics. First prove finite graph energy definitions, translation normalization, binary extraction, and the nested-level identity. Next verify finite coefficient tables and polynomial discrepancy certificates. Only then formalize the analytic comparison theorem against whatever zeta and infinite-product library is actually available. If a library theorem is assumed or imported externally, state that boundary. The central objective is a short chain from an explicit labeled population to a specific real singularity, with every link visible to a reader and no broader reconstruction or formal-verification claim added by implication.
