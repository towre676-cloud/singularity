# Trees: energy shells, modular collapse, and a proved reconstruction class

Supplement to the supplied *What Must Survive II* archive. November 4, 2026.

The attachment already contains the two-edge formula and the survivor edge lists. This supplement independently checks those inputs and advances the proof attempt. The main new conclusions are: the entire root-of-unity sector of a tree is determined by its first energy shell; the remaining information has a nonnegative residue-lift decomposition; and the full series is complete on spider trees among all trees. A compatible linear ambiguity in the contraction observations is also exhibited for every total weight at least 10. Full tree completeness remains open. No priority or formal-verification claim is made.

## 1. The two-edge formula and exactly what it forgets

Let T have n vertices and let S_e(x)=[q^e]M_T(x,q). Integer edge differences z identify its cut lattice with Z^(n-1), and energy is sum z_e^2.

Deleting edges e,f leaves three components of sizes a,b,c, with b in the middle. The four possible signs give normalized component heights

| Heights on (a,b,c) | Volume |
|---|---:|
| (0,1,2) | b+2c |
| (0,1,0) | b |
| (1,0,1) | a+c |
| (2,1,0) | 2a+b |

Therefore, putting d=a-c,

$$S_2(x)=\sum_{\{e,f\}}\left(x^b+x^{n-b}+x^{n+d}+x^{n-d}\right).$$

There are no other energy-2 configurations. The two-edge census enters through two separate marginals: the histogram of |a-c| and the histogram of the unordered pair {b,n-b}. Terms above degree n recover the positive imbalances; the coefficient at n gives twice the number with imbalance zero. Subtracting these terms leaves the symmetrized middle-size histogram. The association of those two marginals is lost. This is an exact description of the observation operator; it does not assert that every formal ambiguity is realizable by a pair of trees.

## 2. A general collapse of all modular specializations

### Theorem 1. For trees, energy 1 determines every n-th-root character theta series

Let a_e be either side size of the cut made by deleting edge e. In the ring Z[x]/(x^n-1), interpreted coefficientwise in q,

$$M_T(x,q)\equiv\prod_{e\in E(T)}\left(\sum_{z\in\mathbb Z}x^{a_e z}q^{z^2}\right)\pmod{x^n-1}.$$

Negative powers of x are reduced modulo x^n-1. The choice between a_e and n-a_e does not matter. Consequently two n-vertex trees with the same energy-1 polynomial have equal M_T(zeta,q) at every zeta^n=1, at every energy.

**Proof.** Root T and orient edges away from the root. Set root height to zero, and let a_e be the number of vertices below e. Then sum_v h_v=sum_e a_e z_e. Normalizing by subtracting min h changes that sum by a multiple of n. Energy is sum_e z_e^2. Summing independent integer z_e factors the theta series. Changing a_e to n-a_e negates its residue modulo n, and z -> -z leaves its theta factor unchanged. Finally,

$$S_1(x)=\sum_e(x^{a_e}+x^{n-a_e})$$

recovers the multiset of unordered side sizes. A balanced edge contributes twice at x^(n/2). QED.

This is substantially stronger than saying that root-of-unity evaluations lose volume modulo n: on trees **all of their information is already present at energy 1**. More sophisticated modular calculations on those specializations cannot restore higher incidence information.

### Corollary 1. Divisibility at every energy

If S_1(T)=S_1(U), then

$$x^n-1\ \mid\ S_e(T)-S_e(U)\qquad\text{for every }e.$$

The divisibility is over Z[x]. No modular fingerprint or finite energy cutoff is involved.

### Theorem 2. A nonnegative residue-lift decomposition

Let R_e(x) be the representative of S_e modulo x^n-1 of degree less than n. By Theorem 1, the entire sequence R_e is determined by S_1. There is a unique decomposition

$$S_e(x)=R_e(x)+(x^n-1)H_e(x),\qquad H_e\in\mathbb Z_{\ge0}[x].$$

To see positivity, write V=r+kn with 0<=r<n. A configuration of volume V contributes x^r to R_e and

$$x^r+x^{r+n}+\cdots+x^{r+(k-1)n}$$

to H_e; for k=0 this sum is empty. Equivalently,

$$[x^{r+jn}]H_e=\sum_{k>j}[x^{r+kn}]S_e.$$

Thus H_e records the tail counts of the number of complete n-volume blocks, separately in each residue class. Completeness on trees is equivalently reconstruction from the edge splits together with all of these residue-lift tail polynomials. This restatement isolates the missing information; it does not recover the addition law.

**Example.** The supplied 10-vertex pair has

$$\Delta S_3=-x(1-x)^2(1-x^{10}),\qquad \Delta H_3=x(1-x)^2.$$

Its modular specialization misses the difference identically. The residue-lift difference sees it in three coefficients.

## 3. A reconstruction theorem: spiders

A spider is a tree with exactly one vertex of degree at least 3; paths are included separately as the case with no branching vertex. Its arm lengths are the positive distances from the branching vertex to the leaves.

### Theorem 3. M_T determines every spider among all finite trees

**Proof.** For n>1,

$$[x]M_T(x,q)=\sum_{v\in V(T)}q^{\deg(v)}.$$

Hence equality of M recovers the degree histogram and identifies the class with exactly one branching vertex (or the unique path class). It remains to recover the unordered arm lengths from S_1.

Suppose there are b>=3 arms of lengths L_1,...,L_b, with sum L_i=n-1. Define A_k=#{i:L_i>=k}. For k<n/2, the coefficient c_k=[x^k]S_1 satisfies

$$c_k=A_k+A_{n-k}.$$

If n is even, define the folded midpoint count f_(n/2)=c_(n/2)/2; elsewhere f_k=c_k for 1<=k<=floor(n/2).

If no arm exceeds n/2, then f_k=A_k throughout this range. The sequence is nonincreasing, and its successive differences recover the arm-length multiplicities.

If one arm has length L>n/2, it is the only such arm. Put s=n-L. All other arms have total length s-1 and, because there are at least two of them, each has length at most s-2. Therefore c_(s-1)=1 and c_s=2. This is the unique upward jump in the folded counts; it occurs strictly before the even midpoint, if there is one. It recovers L=n-s. For 1<=k<s, the tails of the remaining arms are c_k-1, and their successive differences recover all remaining arm lengths.

Conversely a spider with no long arm has no upward jump. The two cases are therefore recognizable from the data. An unordered list of arm lengths determines the spider. QED.

This is a conventional proof for every order, not an extrapolation from a census. The reconstruction algorithm was independently checked on all **7,169 spiders with 4 through 25 vertices**. No claim that this elementary spider reconstruction is new in the literature is made.

## 4. Exact survivor checks and their interpretation

The supplied archive contains the four pairs surviving the volume-7 fingerprints at n=18. Each was checked directly from its edge list. All four have

$$\Delta S_1=-x^8+2x^9-x^{10}.$$

Thus their first separating energy is exactly 1. No all-tree enumeration was needed to verify these witnesses. Their earlier-volume agreement is taken from the source census; it was not independently recomputed here.

The supplied archive also gives one shell-3 survivor pair at n=16, one at n=17, and six of the eleven pairs at n=18. For all **eight supplied pairs**, direct integer calculations establish:

- equality of every shell through energy 3;
- equality of the full weighted three-edge contraction census;
- inequality of the four-edge contraction census;
- separation at energy 4.

The other five n=18 shell-3 pairs are not supplied as edge lists and were not regenerated here. The new receipt deliberately claims only the eight checked pairs.

There is a useful qualification: these are not yet hard examples for the entire series. Six of the eight have different degree histograms, visible already in volume 1. The other two have identical degrees but different edge degree-sum histograms, visible in volume 2.

For any simple graph with n>=3 put

$$D(q)=\sum_vq^{\deg(v)},\qquad J(q)=\sum_{uv\in E}q^{\deg(u)+\deg(v)}.$$

A single vertex of height 2 and two vertices of height 1 give

$$[x^2]M_T=D(q^4)+\frac{D(q)^2-D(q^2)}2+(q^{-2}-1)J(q).$$

Therefore D and [x^2]M recover J exactly. This observation applies to connected simple graphs as well as trees, with the same formula for their normalized height series when n>=3.

For the two degree-matched n=18 pairs,

$$\Delta J=q^6-2q^7+q^8,\qquad
\Delta[x^2]M=q^4-2q^5+2q^7-q^8.$$

So a benchmark for the unresolved compatibility problem should match these readily available statistics too. Merely surviving three energy shells does not mean that the full series is close to a collision.

## 5. Exact support filtration and fourth-shell decontamination

Let C_k(T) be the multiset of weighted trees obtained by retaining k chosen edges and contracting every other edge; each contracted vertex receives the number of original vertices it contains. For a weighted quotient W, define Psi_W by summing only assignments with nonzero difference on every edge. Its energy is the sum of the squares of those differences and its volume is the weighted height sum after min normalization. Grouping configurations by their nonzero edge support gives the exact identity

$$M_T=1+\sum_{k=1}^{n-1}\ \sum_W C_k(T;W)\,\Psi_W.$$

The lowest energy in Psi_W is k. Let Phi_W be that coefficient, the polynomial from its 2^k sign choices. Then S_2 and S_3 are the observations of C_2 and C_3 under Phi. At energy 4 there are only two square partitions, 1+1+1+1 and 4, so

$$S_4(x)=\sum_W C_4(T;W)\Phi_W(x)+S_1(x^2).$$

The doubled-edge contribution is exactly removable. At energy 5, the mixed pattern 4+1 appears; its contribution depends on two-edge configurations with unequal jump magnitudes, not merely on the observed polynomial S_2. Thus this simple removal argument does not automatically extend to every energy.

## 6. Why a linear inversion of the contraction data cannot be assumed

Let partial denote the operation summing over the contractions of one edge of a weighted tree. With m=n-1 original edges,

$$\partial C_k(T)=(m-k+1)C_{k-1}(T).$$

**Proof.** Each retained (k-1)-edge set can be extended to a k-edge set in m-k+1 ways. Contracting the added edge gives its original weighted quotient. Count with multiplicity. QED.

Even imposing this exact lower-census consistency leaves a kernel in the shell observation map on formal censuses.

For an ordered weighted path write P(a,b,c,d); reversing the order denotes the same object. For every integer t>=0, consider the following two multisets, each with four objects and total weight n=t+10:

| Positive side | Negative side |
|---|---|
| P(1,1,t+4,4) | P(1,1,t+5,3) |
| P(1,2,t+5,2) | P(1,2,t+2,5) |
| P(1,3,t+1,5) | P(1,3,t+4,2) |
| P(1,4,t+2,3) | P(1,4,t+1,4) |

Let v be their signed difference. Then exactly

$$\sum_Wv_W\Phi_W(x)=0,\qquad \partial v=0.$$

This is an all-parameter identity. The supplied checker compares affine exponents in t rather than testing finitely many values. For the boundary it uses

$$\partial P(a,b,c,d)=P(a+b,c,d)+P(a,b+c,d)+P(a,b,c+d),$$

where the three-vertex path is identified with its reversal. For Phi it enumerates the eight unit-sign configurations. All terms cancel on both sides.

A simpler individual ambiguity is

$$\Phi_{P(a,b,b,a)}=\Phi_{P(b,a,a,b)}
=2\bigl(x^{a+b}+x^{3a+b}+x^{a+3b}+x^{3a+3b}\bigr).$$

The eight-term relation is stronger because it also preserves the full lower weighted census.

### Realizability matters: the formal ambiguity is not a tree collision

There is even a nonnegative integer formal census based on an actual tree: add v to C_3(P_n), the three-edge census of the n-vertex path. Every path composition in the negative side occurs in that census, so all resulting coefficients remain nonnegative; the total mass, boundary and shell observation are unchanged.

But this altered census is **not realizable by any n-vertex tree**. All of its types are paths. A tree with any vertex of degree at least 3 has a three-edge star quotient, obtained by retaining three edges incident to that vertex. Hence a realizer would have to be the n-vertex path itself, whose census is different.

This gives a precise obstruction to a proposed linear proof: nonnegative counts, all lower contraction consistency, and the shell polynomial still do not encode the global realization constraints. It does not disprove injectivity on realizable tree censuses, and it does not disprove completeness of M_T.

## 7. What the proof attempt establishes

**Proved for all orders:** the two-edge formula; collapse of all n-th-root theta specializations to the first energy shell; the nonnegative residue-lift decomposition; reconstruction of spider trees among all trees; the support filtration and contraction-boundary identities; and the infinite formal compatible-kernel relation.

**Checked exactly:** the four requested volume-7 survivor pairs; the eight supplied shell-3 pairs; the residue and fourth-shell identities on all 200 trees with 2 through 10 vertices; and spider reconstruction on 7,169 spiders through 25 vertices. The matrix ranks in the optional kernel scripts use exact rational arithmetic. No floating-point tests, modular fingerprints, or rank-table engine computations are used in these new checks.

**Still open:** completeness on arbitrary trees and recovery of the addition law. The data now suggest a disciplined next target: use residue-lift polynomials together with realizability constraints, after accounting for degrees and the edge degree-sum polynomial. A proof based only on inverting each individual shell's linear contraction transform would omit a demonstrated ambiguity.

The main archive was not edited. The input pair lists were extracted from receipts/tree_shells_ext.json and receipts/tree_joint.json of the supplied ZIP. Its broader census claims, asymptotic profile-extraction theorem, promotion calculations and formalization claims were not re-audited in this supplement.

## Replay and limits

Python dependencies: networkx, sympy. Run `python replay.py` from this directory. Inputs are included, so no original /root/wms paths or compiled source executables are needed. Replaying recomputes the receipts with exact integers and rationals. These scripts are independent checks and finite demonstrations, not a proof assistant verification of the general arguments.
