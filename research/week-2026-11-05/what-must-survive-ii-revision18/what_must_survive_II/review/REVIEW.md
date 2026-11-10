# Revision 18: independent assistant audit and integration

November 5, 2026. This is an independent assistant reading of the supplied arguments, with independently implemented finite checks. It is not external peer review or proof-assistant verification. The unmodified Revision 18 ZIP remains the input of record. No new completeness claim for arbitrary trees is made.

## Verdicts

| Result | Review outcome | Qualifications |
|---|---|---|
| Theorem 35, three shells distinguish caterpillars | Leading-term proof passes this review | Depends on the explicit coupling identity in Theorem 34; independently checked against the recovered spine formula and direct integer energy enumeration on the bounded census below |
| Theorem 38, no fixed union of energy and volume cutoffs is complete | Argument is repairable and the theorem survives | Forest normalization in the printed proof is incorrect; it must use the number of arms. This package corrects it and supplies the finite-dimensional bounds below |
| Theorem 45, ancestor-matrix rigidity and degree-square increase | Passes with the centroid conventions made explicit | Multiplicity bound applies to non-pendant sizes, not leaf size 1; a single centroid and a balanced edge need distinct anchor conventions |
| Rooted injectivity through weight 12 | Retained as the author's computed result | The 7,813-row rank run was not independently rerun here. Full modular rank is logically sufficient if the encoded matrix is correct |
| General tree completeness; Conjectures 33, 39, 46 | Still open | None of the checks below upgrades a finite census to an all-order theorem |

The review repaired wording and supplied omitted details. It found no counterexample to the three audited theorems. That is not a certification of every theorem from 35 through 50.

## 1. Theorem 35: what makes the top coefficient unavoidable

Use the monograph's shifted coordinates N=n-2. Spin sites satisfy 1<=p<N/2. Fold values include neutral doubled cuts with multiplicity two and, if present, the balanced cut with multiplicity one. Let r1 be the smallest spin site. Reflect the second caterpillar if necessary so its spin at r1 is unflipped. A nonisomorphic pair then has a smallest flipped site q*>r1.

Write tau_pq=sigma_p sigma_q-sigma'_p sigma'_q and c_q=sum_{p<q}tau_pq. Every nonzero tau has q>=q* and p>=r1. In the shell-2 relation

    sum tau_pq (x^(-p)-1)(x^q-x^(N-q))=0,

the coefficient at x^(N-q0), for a site q0<q*+r1, comes only from c_q0. Indeed the terms x^(N-q-p) require q+p>=q*+r1, while x^q and x^(q-p) lie strictly below N/2. Therefore c_q=0 for q<q*+r1. In particular c_q*=2 sigma_q* sum_{p<q*}sigma_p=0.

Apply Theorem 34 and set E=2N-q*-r1. Its g_p Pi_q terms have degree at most 2N-2q*<E. Neutral folds below r1 can have larger individual degrees, but their common factor multiplies sum_q c_q h_q. The preceding cancellation lowers that sum's degree to at most N-q*-r1, so these neutral contributions all lie below E.

After those terms are removed, the largest degree in Lambda_p is N-r1. At that degree its coefficient is 2r1+1-nu for p=r1, and 1 for p>r1, where nu counts all fold occurrences below r1. Consequently only q=q* reaches E. The coefficient there is

    -2 sigma_q* [sigma_r1(2r1+1-nu)
                  +sum_{r1<p<q*}sigma_p]
      =-2 sigma_r1 sigma_q*(2r1-nu).

Every fold below the first spin site is neutral and hence doubled. Thus nu is even and nu<=2(r1-1). This both proves nonvanishing and explains why the final half-integer-looking coefficient is an integer.

Remembering that the coupling identity is for 4H3/x and that Delta S3=(1-x^n)Delta H3 gives precisely

    Delta S3 = (1/2)sigma_r1 sigma_q*(2r1-nu)
                  x^(3n-3-q*-r1) + lower powers.

No fixed shell bound for general trees follows: the ordered cut structure was used essentially.

### Independent checks

`check_caterpillars.py` uses the recovered caterpillar formula, not the author's ising/e.py implementation. It enumerates exact A,B polynomial tuples for all nonstar caterpillars with 4 through 18 vertices, with no fingerprints. All 39 excess representatives in collision classes were checked by direct integer edge-difference enumeration through energy 3. The reduced coupling identity and the claimed leading degree and coefficient agree in every case. Another 48 deterministic tests insert neutral doubled or balanced cuts into known collisions, checking the cancellation against the independently recovered formula. Exact coverage is in caterpillar_checks.json.

These finite checks support the algebraic dependency on Theorem 34. They are not a substitute for the all-order degree argument above and do not constitute an end-to-end formalization of the long coupling reduction.

## 2. Theorem 38: corrected normalization and dimension bounds

For a forest W of rho(W) attached rooted arms, the x-constant term is

    G_W(a)|_(x=0)=q^(rho(W)*a^2).

Therefore the object with constant term 1 is

    normalized G_W(a)=q^(-rho(W)*a^2) G_W(a).

Using q^(-a^2) for a general forest is not correct: its constant term need not be 1 and the asserted additive formal logarithm is not defined in the stated x-adic form. The proof already includes the arm-count coordinate, so the error is repairable rather than a counterexample to the theorem. Both HTML versions in this package use the corrected normalization.

Here are the missing finite-dimensional details. Fix d,V and restrict individual arms to at most r vertices. Their edge census must include the attachment edge from the external vertex to each arm root. Each selected edge has its below-edge size as label. The ancestor relation among at most d selected edges is a rooted forest, and disconnected components multiply in a free commutative algebra. The census C(W)=sum_F[Q(F)] is multiplicative for disjoint unions of arms, with constant term 1. Its logarithm truncated at selected-edge degree d is additive.

There are at most f(d)r^d coordinates in this truncated algebra for some constant depending only on d: there are finitely many unlabelled ancestor forests with at most d selected edges, and at most r choices for each size label. Products of connected types are counted by their total selected-edge degree, so taking the logarithm does not destroy this polynomial bound.

For one arm t and a fixed external height 0<=a<=V, a coefficient of x^j in q^(-a^2)G_t(a), j<=V, has q exponents in

    -2aj <= exponent <= r*j^2.

To see this, write the energy minus a^2 as the sum of internal squared differences plus h_root^2-2a h_root, and use sum h=j. Its quadratic positive part is at most r*j^2; its negative part is at least -2aj. Products entering the logarithm at total volume j obey the same loose bounds. Thus all normalized log coefficients through x^V and heights a<=V occupy O_V(r) rational coordinates.

Add weight and arm count to these coordinates. The resulting additive vector space has dimension polynomial in r. There are exponentially many distinct rooted arms of size at most r: a chain carrying one or two leaves at each site already supplies an elementary binary-word family. For sufficiently large r, their vectors satisfy a nonzero rational relation. Clearing denominators and using the positive weight coordinate gives two nonempty, distinct, disjointly supported forests A,B of equal weight and equal arm count. They have equal d-censuses and equal G_A(a),G_B(a) through volume V at each a<=V.

The exchange-square construction then makes T=(2A|2B) and S=(A+B|A+B). A nonzero gradient costs at least one unit of energy, so the census equality gives G_A-G_B energy order at least d+1. The two wedges and the unequal endpoint heights force the difference of the unrooted series to begin at energy at least 2d+3. Taking 2d+2>=E removes all energy coefficients through E.

For volume at most V, only endpoint heights a+b<=V can contribute. The rooted congruences make the corresponding wedges vanish to the needed x order, so every coefficient through volume V agrees as a polynomial in q. Multiplication by 1-x^n transfers the conclusion from L to M.

Finally, each constructed tree has a balanced central edge. A tree has at most one such edge: along a path between two alleged balanced edges, the side sizes cannot both be n/2. An isomorphism would therefore identify the central edges and their rooted halves. One of the halves of T would have to equal a half of S, forcing 2A=A+B or 2B=A+B as multisets of rooted arms. Either implies A=B, a contradiction.

This completes the repaired nonconstructive proof. It produces no full-series collision and gives no practical bound small enough for a census. No numerical experiment can by itself verify its universal quantifiers.

## 3. Theorem 45: centroid conventions and the parent-label argument

Only internal edge sizes s>=2 have multiplicity at most two in a caterpillar. Pendant size 1 may occur arbitrarily often. Root at the unique centroid when there is one. With a balanced edge, remove it and use its two endpoints as two rooted halves, assigning both virtual incoming edges the size n/2. The balanced row is omitted from N because its h factor is zero; when needed in the proof, its common-anchor information is supplied by this explicit convention.

A caterpillar's internal ancestor order is two chains. Label every internal edge by its below-edge size. Labels strictly decrease down a chain, so each label occurs at most once on each chain.

For a child label z occurring once, N gives the complete multiset of its ancestor labels, each at most once along its own path. The smallest ancestor label is its parent label. If there is no ordinary ancestor, the parent is the centroid anchor. Thus the parent label is fixed.

For a label z occurring twice, an ancestor label with N[a,z]=2 is common to the two copies in the sense that each copy has an ancestor of that label; this need not mean distinct ancestor copies. Take the smallest such internal label D, or the centroid anchor when none exists. In the caterpillar, labels appearing exactly once between D and z split into at most two chains. Each is globally single: a globally duplicated label above a duplicated z contributes twice, not once.

Their comparabilities are known from N because these intermediate labels are single. In any realizing tree, incomparable labels cannot lie above the same copy of z. Conversely, comparable intermediate labels cannot be assigned to different copies: the upper would then lie above both copies of z, contradicting its N value of 1. Hence each chain must lead to one copy, and the parent labels of the two copies are the chain minima, with D or the anchor for an empty chain. Which copy receives which chain may change; their parent-size multiset does not.

This recovers the aggregate multiset of direct internal-child labels for each parent size. At a unique-centroid root, its child-size multiset and therefore its degree are fixed separately. At a balanced edge the two virtual roots are treated as the paired parent size n/2.

For a non-centroid internal vertex under an incoming edge of size w,

    d_v-1=(w-1)-sum_children(xi-1).

The same formula holds at each balanced endpoint because the removed balanced edge supplies its parent edge. A unique-centroid root instead has d_root=n-1-sum_children(xi-1), and its contribution to the degree-square difference is zero.

At a size occurring twice, the caterpillar places at most one internal child below each copy. The only way to create a branching internal vertex is to gather its two child labels xi,eta under one copy. The square-sum change is

    (w-1)^2+(w-1-(xi-1)-(eta-1))^2
       -(w-1-(xi-1))^2-(w-1-(eta-1))^2
      =2(xi-1)(eta-1).

The fixed total degree converts the same change for (d-1)^2 to that for d^2. Genuine internal children have xi,eta>=2, so every gathering contributes positively. No such gathering means the internal subgraph still has maximum degree two and the tree is a caterpillar.

### Independent checks

`check_ancestor.py` rebuilt A,B,N from centroid-rooted edge traversals on all 5,445 unlabelled trees with 3 through 14 vertices. Theorem 44's polynomial identity passed on every tree. Grouping by exact A,N gave 2,174 comparisons against caterpillar references, including 734 balanced comparisons and 32 non-caterpillar comparisons. Both the direct-child multiset statement and the degree-square formula passed. The supplied 27-vertex example was independently rebuilt; its two gathering contributions are 50 and 4 and its direct degree-square difference is 54.

These results do not prove Conjecture 46. Equality of A,B has not been shown to force equality of N for impostors.

## 4. What “the sign of Theorem 40” can mean

There is no universal sign for arbitrary four forests in the mixed exchange formula: swapping c1,c2 reverses the sign. Exact finite-height examples in exchange_checks.json attain both signs.

At fixed 0<x,q<1 and a symmetric middle kernel K with nonnegative entries, put

    <f,g>_K=(1/2) sum_(a,b) K(a,b) f(a,b)g(a,b).

The exchange difference is this Gram pairing of the two wedges. Therefore

    |Delta L|^2 <= <W_UV,W_UV>_K <W_c1c2,W_c1c2>_K.

A repeated wedge gives the positive square case. This is an ordinary Cauchy-Schwarz consequence, not a new completeness theorem. The unresolved question must specify structural restrictions that prevent mixed cancellation, or ask whether a pairing can vanish identically as a series. Rooted injectivity alone does not make arbitrary distinct wedge functions nonorthogonal.

## 5. Integration and replay boundaries

The previous caterpillar supplement has been recovered unchanged from its saved ZIP and is now included under supplements/caterpillar_proof_advance. Its complete replay passed, including the two-parameter volume-4 polynomial, the four-spine reconstruction proof and tests, and the earlier errata checks. The old errata patch is historical and is not applied blindly to Revision 18.

`python verify_trees.py` runs the new bounded exact audit without the author's directory layout. It is separate from verify_all.sh. The latter still means the historical graph replay through volume 12, and it was not rerun in this review.

`tree_replay.py` stages historical sources into a local work directory, rewrites the author's absolute paths there, builds selected C++ programs and generates needed census dumps. Relative exec/open assumptions are handled by running each source from its staged source directory. Original historical algorithms remain in src; invoking those files directly may still require their old working-directory assumptions. Use the documented portable entry point.

Successfully replayed historical jobs in this audit: caterpillar family s=1,2,3; caterpillar census dumps through order 18; and the reduced shell-3 bilinear check on their 39 comparisons. Large original hunts, spin enumeration through N=42 and the weight-12 rank run were not rerun. The native C++ replay requires g++ with C++17 and __int128 support; the independent default audit uses Python, networkx and sympy.

The literature comparison is in LITERATURE.md. It identifies close antecedents and missing implications; it does not establish priority. The original author did not review this integration, and no formal or external peer-review label is implied.
