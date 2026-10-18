# 4. Visibility depth and the loss of correspondence

## 4.1 Increasing volume as an observation hierarchy

The coefficient \(C_{G,m}(q)=[x^m]L_G(x,q)\) reports every energy attainable with exactly \(m\) units of nonnegative integer height, together with original assignment multiplicities. Increasing \(m\) enlarges the set of placements that can be tested. It does not simply increase numerical precision in an unchanged observation. New occupancy patterns become available: repeated occupation of one vertex, occupation of several vertices, and different heights on linked supports.

For equal-order graphs, normalization does not change the first place at which their scalar-height observations differ. If \(k\) is fixed, multiplication by \(1-x^k\) has constant term one. A first nonzero coefficient cannot be removed by that multiplication because no earlier nonzero coefficient exists to cancel it.

The hierarchy must be specified before it is interpreted. A volume prefix of the two-variable series is one hierarchy; a span prefix of the fully marked series is another. The binary sector is one span layer, not one volume layer: a binary subset of size ten has volume ten and span one. Conversely, a one-vertex profile of height ten has the same volume and span ten. Keeping those distinctions prevents an observation about a binary cut polynomial from being silently transferred to an unmarked height specialization.

## 4.2 The first coefficients can be read by hand

Write \(e_i\) for the unit profile at vertex \(i\). At volume one the only profiles are \(e_i\), and
\[
E_G(e_i)=d_i.
\]
At volume two the profiles are \(2e_i\) and \(e_i+e_j\), \(i<j\). The latter subtracts two from the sum of endpoint degrees precisely when the endpoints are adjacent. This is the first layer that couples local degrees to a relation between vertices.

**Theorem SNG-F14 (coefficients through volume three).** For every simple graph,
\[
C_{G,0}(q)=1,
\qquad C_{G,1}(q)=\sum_iq^{d_i},
\]
\[
C_{G,2}(q)=\sum_iq^{4d_i}
+\sum_{i<j}q^{d_i+d_j-2A_{ij}},
\]
and
\[
\begin{aligned}
C_{G,3}(q)={}&\sum_iq^{9d_i}
+\sum_{i\ne j}q^{4d_i+d_j-4A_{ij}}\\
&+\sum_{i<j<\ell}q^{d_i+d_j+d_\ell-2e_G(\{i,j,\ell\})}.
\end{aligned}
\]
Here \(e_G(S)\) denotes the number of edges induced by \(S\). Empty index sums are zero. For normalized coefficients,
\[
[x^m]B_G=C_{G,m}-C_{G,m-k},
\]
where \(C_{G,t}=0\) for \(t<0\).

*Proof.* Partition the weak compositions of one, two, and three by their positive parts. The possibilities are respectively \(1\); \(2\) or \(1+1\); and \(3\), \(2+1\), or \(1+1+1\). Substitute each profile in
\[
E_G(a)=\sum_i d_i a_i^2-2\sum_{\{i,j\}\in E}a_i a_j.
\]
The pattern \(2e_i+e_j\) is indexed by ordered distinct vertices because the heights distinguish the two positions. The three-unit pattern is indexed by unordered triples. These are disjoint exhaustive cases, giving the formulas without missing multiplicities. The normalized identity is coefficient extraction from Theorem SNG-F02. \(\square\)

The classification can be read as a table. Write \(N_d\) for the number of vertices of degree \(d\), \(P_{a,b}^{\epsilon}\) for the number of **ordered** pairs \((i,j)\), \(i\ne j\), with \(d_i=a\), \(d_j=b\), \(A_{ij}=\epsilon\), and \(T_{s,t}\) for the number of unordered triples with degree sum \(s\) spanning \(t\) edges. These statistics are defined from degrees and adjacency alone.

| Volume | Pattern | Index set | Support | Span | Energy |
|---:|---|---|---:|---:|---|
| 1 | \(e_i\) | vertices | 1 | 1 | \(d_i\) |
| 2 | \(2e_i\) | vertices | 1 | 2 | \(4d_i\) |
| 2 | \(e_i+e_j\) | unordered pairs | 2 | 1 | \(d_i+d_j-2A_{ij}\) |
| 3 | \(3e_i\) | vertices | 1 | 3 | \(9d_i\) |
| 3 | \(2e_i+e_j\) | ordered pairs | 2 | 2 | \(4d_i+d_j-4A_{ij}\) |
| 3 | \(e_i+e_j+e_k\) | unordered triples | 3 | 1 | \(d_i+d_j+d_k-2e_G(\{i,j,k\})\) |

The corresponding coefficient contributions are separated below so each formula remains readable.

| Volume | Pattern | Contribution |
|---:|---|---|
| 1 | \(e_i\) | \(\sum_dN_dq^d\) |
| 2 | \(2e_i\) | \(\sum_dN_dq^{4d}\) |
| 2 | \(e_i+e_j\) | \(\tfrac12\sum P_{a,b}^{\epsilon}q^{a+b-2\epsilon}\) |
| 3 | \(3e_i\) | \(\sum_dN_dq^{9d}\) |
| 3 | \(2e_i+e_j\) | \(\sum P_{a,b}^{\epsilon}q^{4a+b-4\epsilon}\) |
| 3 | \(e_i+e_j+e_k\) | \(\sum T_{s,t}q^{s-2t}\) |

A pattern lies in the normalized population exactly when its support is smaller than \(k\); then its span is the displayed value. For \(k\le3\) some patterns cover every vertex and are translations instead: the profile \((1,1)\) on two vertices, \((2,1)\) and \((1,2)\) on two vertices, and \((1,1,1)\) on three. The normalized identity removes exactly these. The table is implemented without profile enumeration in `src/singularity/lowvolume.py`. `tests/test_low_volume.py` compares its local, normalized and marked outputs with both the weak-composition and the level-chain enumerators on all 75 labeled graphs with at most four vertices, on the fixed pairs, and on regular graphs including the cube, the Möbius ladder, the Petersen graph, \(K_4\), \(K_{3,3}\), \(C_5\) and two disjoint triangles, where the closed form in terms of order, degree and triangle count (Proposition SNG-I008) is also checked.

For example, \(C_{G,1}\) determines the degree histogram exactly: its coefficient of \(q^d\) is the number of vertices of degree \(d\). It does not identify which vertex has each degree, because coordinate labels have been summed out. That missing assignment of degrees to positions is already a small instance of lost correspondence.

Normalization matters at low volume in small graphs. For \(k=2\), \([x^2]B_G=C_{G,2}-1\), removing the constant profile \((1,1)\). For \(k=3\), the corresponding first subtraction occurs at volume three. The uniform formula is safer than assuming that normalized and unnormalized coefficients agree at every displayed low order.

## 4.3 What the second coefficient adds

Define the edge degree-sum polynomial
\[
J_G(q)=\sum_{\{i,j\}\in E}q^{d_i+d_j}.
\]
This is one measure of how degrees mix across edges. It is coarser than the full joint degree matrix because different degree pairs can have the same sum, but it is already more relational than the degree histogram alone.

**Theorem SNG-F15 (second-layer degree mixing).** For every graph,
\[
C_{G,2}(q)=\sum_iq^{4d_i}
+\sum_{i<j}q^{d_i+d_j}
+(q^{-2}-1)J_G(q).
\]
The expression is a polynomial: every edge has \(d_i+d_j\ge2\). For graphs \(G,H\) with the same degree histogram,
\[
C_{G,2}=C_{H,2}\quad\Longleftrightarrow\quad J_G=J_H.
\]

*Proof.* Separate the pair sum in Theorem SNG-F14 into edges and nonedges. Start by assigning \(q^{d_i+d_j}\) to every pair; on an edge replace it by \(q^{d_i+d_j-2}\). The change is the displayed correction. If degree histograms agree, both of the first two sums agree, so the difference of second coefficients is \((q^{-2}-1)(J_G-J_H)\). A nonzero Laurent polynomial cannot annihilate another nonzero Laurent polynomial over the integers. Thus the difference vanishes exactly when \(J_G-J_H\) does. \(\square\)

This proposition prevents overinterpreting an attractive example. Suppose an exact comparison gives
\[
C_{G,2}-C_{H,2}=2q^2(1-q)^3(1+q).
\]
If the graphs have the same degree histogram, then
\[
J_G-J_H=2q^4(1-q)^2.
\]
The observation has detected a difference in degree mixing. That is a valid strict separation from any matched invariants, but it is not evidence that a genuinely high-order height interaction was needed. A stronger next example should first match \(J_G\), then look for a later discrepancy.

| Volume | Allowed positive height patterns | Direct information visible in the formula |
|---:|---|---|
| 0 | Empty support | One zero profile |
| 1 | \(1\) | Degree histogram |
| 2 | \(2\), \(1+1\) | Degree data and edge degree-sum mixing |
| 3 | \(3\), \(2+1\), \(1+1+1\) | Ordered degree-adjacency weights and degree-decorated triple edge counts |
| \(m\) | Integer partitions of \(m\) placed on vertices | Aggregated degree-decorated supports of size at most \(m\) |

The final row deliberately says “aggregated.” It is not a claim that every decorated induced-subgraph count can be independently recovered from one coefficient polynomial. Different patterns can contribute the same power of \(q\), and their multiplicities are then added.

## 4.4 A precise finite-depth comparison

For graphs \(G,H\) of the same order, define their scalar-height visibility depth by
\[
r(G,H)=\min\{m\ge0:C_{G,m}(q)\ne C_{H,m}(q)\},
\]
with \(r=\infty\) when no discrepancy exists. The same definition using \([x^m]B_G\) gives the same value. A depth records how much total height is required to separate the two exact observations. It is not a claim about computation time, and it is not automatically a graph-theoretic reconstruction radius.

**Theorem SNG-F16 (prefix equivalence and an ultrapseudometric).** For each \(M\ge0\), agreement of \(C_{G,m}\) for all \(m\le M\) is an equivalence relation on graphs of fixed order. Visibility depths satisfy
\[
r(G,H)\ge\min\{r(G,K),r(K,H)\}.
\]
Consequently \(d(G,H)=2^{-r(G,H)}\), with \(2^{-\infty}=0\), is an ultrapseudometric. It is a metric on the quotient obtained by identifying graphs with identical full scalar-height series.

*Proof.* Equality of finite coefficient lists is reflexive, symmetric, and transitive. If both pairs \((G,K)\) and \((K,H)\) agree below an index \(r_0\), then \(G,H\) agree below that index as well. This gives the displayed inequality, including infinite depths. Exponentiating reverses the inequality and gives \(d(G,H)\le\max\{d(G,K),d(K,H)\}\). Zero distance means equality of the full series, which is exactly the relation used in the stated quotient. \(\square\)

**Proposition SNG-F33 (finite visibility filtration).** Fix a domain \(\mathcal D\): the symbolic coefficients in \(\mathbb Z[q]\), the span-marked counts, or the values at a parameter \(q_0\) that is rational or an isolated real algebraic number. For a finite family of series with common prefix through \(R\), let \(\sim_v\) be agreement in \(\mathcal D\) of every coefficient at volumes \(0,\ldots,v\). Then (i) each \(\sim_v\) is an equivalence relation and \(\sim_{v+1}\) refines \(\sim_v\); (ii) if two series are \(\sim_{v-1}\)-equivalent and differ at \(v\), then \(v\) is their first difference in \(\mathcal D\), and the signed difference at \(v\) is a witness; (iii) symbolic equivalence implies equivalence at every parameter, and marked equivalence implies symbolic equivalence, while the converses can fail; (iv) a class that survives to \(R\) records agreement through \(R\) only.

*Proof.* (i) Agreement of finitely many values in a set with equality is an equivalence relation, and agreeing through \(v+1\) includes agreeing through \(v\). (ii) follows from the definition of \(\sim_{v-1}\). (iii) Evaluation at \(q_0\) and forgetting the span mark are functions of the finer data, so they preserve equality. The converses fail: at \(q=1\) every series on \(n\) vertices has coefficients \(\binom{m+n-1}{n-1}\), so the spectral and binary pairs merge there although they differ symbolically. (iv) The data beyond \(R\) were not examined. \(\square\)

`src/singularity/visibility.py` computes these partitions with deterministic class identifiers, memberships at every volume, and a signed witness for every split. For an algebraic parameter it decides equality exactly through SNG-F31's gcd test. It refuses a bound beyond the common prefix, and a marked dictionary must be given the bound it was computed through, since it carries no length of its own. On the census of CENSUS-v1, the symbolic and marked class counts at each volume equal those of `results/small_census.json`. Every connected graph with at most six vertices is separated from every other by volume six (`results/visibility_filtration.json`). This is a finite statement about that population, not a separation bound for larger graphs.

Calling this a pseudometric is substantive caution. If nonisomorphic graphs share the entire series, their distance is zero. Proving that this cannot happen in a graph class would be a reconstruction theorem for that class. The present definitions do not assume it.

## 4.5 What an occupancy coefficient can depend on

A profile of volume \(m\) has at most \(m\) occupied vertices. Its energy depends on the induced adjacency among those vertices and on their ambient degrees. Edges from an occupied vertex to an unoccupied vertex contribute through its degree; no further structure among unoccupied vertices enters that profile's energy.

To state this precisely, regard the induced graph \(G[S]\) as decorated by the ambient degree \(d_i\) at every vertex of \(S\). Two decorated induced graphs are isomorphic when a graph isomorphism also matches those degree labels. Let the decorated \(t\)-deck record how many subsets of size \(t\) have each such type.

**Theorem SNG-F17 (decorated-deck sufficiency for a prefix).** If two graphs of the same order have equal decorated \(t\)-decks for every \(t\le M\), then their scalar-height coefficients agree for every \(m\le M\). Their fully marked coefficients agree at those volumes as well.

*Proof.* Fix a nonempty support \(S\) of size \(t\le m\). Profiles with that exact support assign positive integers \(b_i\) to its vertices, summing to \(m\). Their energies are
\[
\sum_{i\in S}d_i b_i^2
-2\sum_{\{i,j\}\in E(G[S])}b_i b_j.
\]
A degree-preserving induced-graph isomorphism gives a coordinate-permutation bijection on these positive assignments, preserving volume, energy, and span. For normalized profiles, exact supports are proper subsets; the full-support case is excluded on both graphs because their common order is the same. Summing over matching decorated support types proves equality at each \(m\le M\). The zero profile contributes equally. \(\square\)

This is a one-way implication. The coefficient hierarchy can be coarser than the decorated decks because it aggregates different supports and positive assignments into the same energy cells. The proposition identifies a sufficient source of indistinguishability and explains the local nature of a bounded-volume experiment without asserting an unproved inversion.

It suggests several distinct research questions. Can nonisomorphic graph families have arbitrarily large finite visibility depth? Which natural graph classes admit a uniform depth bound? Can decorated-deck constructions produce exact equal-series examples, or do higher heights eventually distinguish them? These are precise targets. Finite searches can provide examples and exclusions within their declared range, but cannot settle the unrestricted questions merely by growing a table.

## 4.6 Why labeled probes make reconstruction easy

Consider instead the fully vertex-marked series
\[
\mathscr L_G(z_0,\ldots,z_{k-1};q)
=\sum_{a\ge0}\bigl(\prod_i z_i^{a_i}\bigr)q^{E_G(a)}.
\]
The variables now identify where each unit was placed. This is a much stronger observation than scalar total height.

**Theorem SNG-F18 (labeled reconstruction at degree two).** The coefficients of \(\mathscr L_G\) through total \(z\)-degree two determine the labeled adjacency matrix of \(G\).

*Proof.* The coefficient of \(z_i\) is the single monomial \(q^{d_i}\), recovering \(d_i\). For distinct \(i,j\), the coefficient of \(z_i z_j\) is \(q^{d_i+d_j-2A_{ij}}\). Its exponent, together with the two recovered degrees, gives
\[
A_{ij}=\frac{d_i+d_j-\deg_q([z_i z_j]\mathscr L_G)}2.
\]
Every coefficient used is a single monomial with coefficient one, so its exponent is unambiguous. \(\square\)

Thus a theorem saying that arbitrary vertex-marked probes determine the graph would not resolve the difficult scalar-height inverse problem. The correspondence that makes reconstruction easy has been retained explicitly. The interesting restriction is the specialization \(z_i=x\) for all \(i\), which merges those individually identifiable monomials into common volume cells.

This is the same reason that general graph-observation frameworks must be compared with their actual permitted test families. Results for all graph homomorphism counts, as discussed in [Lovasz2012], concern an enormously rich set of probes. One particular partition function or one particular family of height weights does not acquire the same reconstruction power by resemblance.

## 4.7 Marks, specializations, and the conclusions they permit

For any observation, forgetting a mark is a deterministic map on its data. Equality before forgetting implies equality afterward. A discrepancy afterward also proves a discrepancy beforehand. The reverse implications need not hold. In particular, full span-marked equality implies binary-profile equality by Theorem SNG-F11; scalar-height equality alone is not presently proved to imply it.

Numerical specialization of \(q\) can lose information as well. The endpoints are extreme examples: at \(q=1\) every graph of the same order has the same scalar-height series, while at \(q=0\) every connected graph has \(B_G=1\). More generally, a nonzero polynomial discrepancy can vanish at a selected algebraic value of \(q\). Exact polynomial comparison is stronger than comparison at one such value. If \(q_0\) is transcendental, no nonzero integer polynomial vanishes there, so an exact evaluation would preserve coefficient distinctions; that logical observation does not provide an effective exact arithmetic method for an arbitrary transcendental input.

| Established implication | Reason | Converse available here? |
|---|---|---|
| Graph isomorphism \(\Rightarrow\) full marked equality | Coordinate-permutation bijection | Not proved |
| Full marked equality \(\Rightarrow\) scalar-height equality | Set \(z=1\) | Not proved |
| Full marked equality \(\Rightarrow\) binary-profile equality | Extract \([z]\) | Not proved |
| Connected scalar-height equality \(\Rightarrow\) unmarked theta equality | Sum finite energy shells | Not proved |
| Same decorated decks through size \(M\) \(\Rightarrow\) height-prefix equality through volume \(M\) | Support decomposition | Not proved |
| Exact coefficient discrepancy \(\Rightarrow\) different graph observations | Definition of equality | Yes, at some coefficient if the formal series differ |

Finally, a later primewise Euler lift of \(L_G\) should be understood as an analytic reorganization. Its coefficient at a prime power recovers the corresponding local coefficient, and the local coefficients specify every Euler factor. That lift can expose useful singularities and arithmetic asymptotics, but it does not restore correspondence already discarded by the local histogram. The forward computation, the observation hierarchy, and the inverse reconstruction problem remain distinct throughout.

The resulting program is deliberately open in the right place. We can prove what the first layers observe, identify exact sources of finite-depth agreement, and formulate complete-series reconstruction as a concrete question. We can also search for persistent blindness and treat an exact counterexample as a mathematical result. What we cannot do is promote a successful prefix calculation into a conclusion about every unseen layer. The hierarchy provides the language for making the next calculation precise.
