# 3. Nested heights and the interaction of boundaries

## 3.1 A height profile is a stack of threshold sets

A binary profile chooses a subset of vertices: height one on the subset and zero outside. A general integer profile chooses several nested subsets. This description is exact, but only if consecutive threshold sets are allowed to be equal. A jump of three at one vertex crosses three integer levels even if the set of vertices above those levels never changes.

For a normalized profile \(a\ge0\) with \(\min a=0\) and \(\max a=h\), define
\[
S_t(a)=\{i\in V:a_i\ge t\},\qquad 1\le t\le h.
\]
Then
\[
\varnothing\ne S_h\subseteq S_{h-1}\subseteq\cdots\subseteq S_1\subsetneq V,
\qquad
a=\sum_{t=1}^h\mathbf1_{S_t}.
\]
The inclusions are weak. Replacing them by strict inclusions changes the population by discarding legitimate profiles.

**Theorem SNG-F09 (threshold-chain bijection).** Normalized profiles of span \(h\ge1\) are in bijection with weakly nested chains of \(h\) nonempty proper vertex subsets. The inverse map is \(a_i=\#\{t:i\in S_t\}\), and
\[
|a|=\sum_{t=1}^h|S_t|.
\]

*Proof.* Threshold sets of a profile have the stated nesting. Because some coordinate is zero, \(S_1\) is proper; because some coordinate is \(h\), \(S_h\) is nonempty. Conversely, nesting implies that, for each vertex, membership occurs at an initial segment of the thresholds. Thus the formula for \(a_i\) gives exactly the original membership sets when thresholds are taken again. A vertex outside \(S_1\) has height zero and a vertex in \(S_h\) has height \(h\), proving normalization and span. The volume identity follows by counting all incidences \((i,t)\) with \(i\in S_t\) in two orders. \(\square\)

The chain is not an auxiliary encoding with multiple extensions. It is uniquely determined by the original profile, and it reconstructs that profile uniquely. Consequently a chain-based counting algorithm preserves original assignment multiplicity without an additional correction factor.

## 3.2 Squared differences do not add level by level

Write \(c_G(S)=|\partial S|\) for the number of edges with one endpoint in \(S\) and one outside. For disjoint vertex sets \(U,W\), write \(e_G(U,W)\) for the number of edges joining them. The ordinary integer coarea identity says
\[
\sum_{\{i,j\}\in E}|a_i-a_j|=\sum_{t=1}^h c_G(S_t).
\]
Our energy uses squares, so this identity alone is insufficient. An edge crossing two levels contributes four, not two. Cross terms record which nested boundaries are crossed by the same edge.

**Theorem SNG-F10 (nested-boundary energy formula).** For the threshold chain of a normalized profile,
\[
E_G(a)=\sum_{t=1}^h c_G(S_t)
+2\sum_{1\le r<t\le h}e_G(S_t,V\setminus S_r).
\]
Equivalently,
\[
E_G(a)=\sum_{r,t=1}^h
e_G\bigl(S_{\max(r,t)},V\setminus S_{\min(r,t)}\bigr).
\]

*Proof.* Use the oriented edge-difference matrix \(\partial\) from Chapter 2 and substitute \(a=\sum_t\mathbf1_{S_t}\) into \(E_G(a)=\|\partial a\|_2^2\). Diagonal inner products equal \(c_G(S_t)\). If \(S_t\subseteq S_r\), an edge contributes to both gradients exactly when it joins \(S_t\) to \(V\setminus S_r\). On such an edge the two gradient signs agree, irrespective of the chosen orientation; otherwise at least one gradient is zero. Their inner product is therefore \(e_G(S_t,V\setminus S_r)\). Expanding the squared norm proves the first formula, and pairing the two orders of each off-diagonal term proves the second. \(\square\)

An edgewise proof gives the same mechanism. If endpoint heights are \(u<v\), the edge crosses exactly \(v-u\) thresholds. The ordered pairs of crossed thresholds number \((v-u)^2\). The double sum counts those pairs edge by edge. This argument also explains why repeated threshold sets must remain: an edge can cross several numerically different thresholds whose vertex subsets happen to coincide.

The formula concerns pairwise edge energies throughout. The cross terms are interactions between observations of nested boundaries; they do not turn the graph Hamiltonian into a new three-body or higher-body edge law. Several boundaries can jointly reveal information that isolated boundary histograms lose, even though the underlying energy remains a sum over edges.

## 3.3 Two examples where repetition matters

Consider the path \(0-1-2\). For \(a=(0,2,2)\), the threshold chain is
\[
S_1=S_2=\{1,2\}.
\]
Each set has cut size one. The sum of the two cut sizes is two, but the actual energy is \((0-2)^2+(2-2)^2=4\). The cross term contributes the missing two, because one edge joins \(S_2\) to \(V\setminus S_1\). A strict-chain enumeration would omit this profile entirely.

For \(a=(0,1,3)\), the same path gives
\[
S_1=\{1,2\},\qquad S_2=S_3=\{2\}.
\]
The diagonal cut sum is three. The boundaries of \(S_1\) and \(S_2\) lie on different edges, so their overlap term is zero; the same holds for \(S_1,S_3\). The repeated pair \(S_2,S_3\) contributes two. The total is five, agreeing with \(1^2+2^2\).

| Path profile | Volume | Span | Diagonal cut sum | Cross-term contribution | Energy |
|---|---:|---:|---:|---:|---:|
| \((0,1,1)\) | 2 | 1 | 1 | 0 | 1 |
| \((0,2,2)\) | 4 | 2 | 2 | 2 | 4 |
| \((0,1,3)\) | 4 | 3 | 3 | 2 | 5 |
| \((0,1,2)\) | 3 | 2 | 2 | 0 | 2 |

The last row is also useful. Distinct boundaries can have no overlap, making the squared energy equal the coarea sum. There is no universal rule replacing the cross terms by a fixed function of the individual cut sizes. Their value depends on how the boundaries sit together in the same graph.

A four-cycle makes this failure especially explicit while holding both individual sizes and individual cut counts fixed. Let the cycle be \(0-1-2-3-0\), and let \(S=\{0,1,2\}\). Consider either \(T=\{0\}\) or \(T'=\{1\}\) as the inner threshold set. Both chains have outer size three, inner size one, and cut counts two and two. However,
\[
e_G(T,V\setminus S)=1,
\qquad e_G(T',V\setminus S)=0.
\]
The two profiles are \((2,1,1,0)\) and \((1,2,1,0)\); both have volume four and span two. Their energies are respectively six and four. Thus even the ordered list of threshold sizes and cut counts does not determine the height energy. One must also retain which boundary edges are shared.

This example does not prove that two graphs with equal complete binary cut polynomials must have different height series. Both profiles occur in the same graph, and a global inverse implication could in principle use information unavailable in this two-boundary summary. What the example proves is the narrower and useful fact that the displayed chain energy cannot be computed from its separate boundary marginals alone.

## 3.4 An exact chain expansion of the marked series

Combining the bijection and energy formula gives
\[
\mathcal B_G(x,q,z)=1+
\sum_{h\ge1}z^h
\sum_{\varnothing\ne S_h\subseteq\cdots\subseteq S_1\subsetneq V}
x^{\sum_t|S_t|}
q^{\sum_t c_G(S_t)+2\sum_{r<t}e_G(S_t,V\setminus S_r)}.
\]
This is an identity of formal series. At a specified total volume \(m\), only chains of length at most \(m\) can contribute, so the coefficient remains a finite sum. The expression is also a useful specification for an independent implementation: direct weak-composition enumeration and threshold-chain enumeration must return the same marked cells.

The expansion shows exactly what a binary observation omits. The binary sector reports one subset at a time, through its size and cut. A chain term refers to several nested subsets in the same graph and additionally uses their boundary-overlap counts. Separate histograms of subset sizes and cuts do not retain the correspondence needed to form these overlaps.

This statement is directional. The full marked series certainly contains the binary histogram because its span-one coefficient extracts it. It does not follow that the two-variable specialization \(B_G(x,q)=\mathcal B_G(x,q,1)\) permits that same extraction. After span is forgotten, a cell of given volume and energy can receive both binary and nonbinary contributions. No inversion of that mixture is proved here.

## 3.5 The binary sector and its reciprocity

Define the binary cut polynomial
\[
I_G(x,q)=\sum_{S\subseteq V}x^{|S|}q^{c_G(S)}.
\]
Its height interpretation overlaps the external-field Ising polynomial studied in [AM2009], subject to the stated normalization of the energy and spin variables. The present definition is explicit, so no external convention is needed to compute it.

**Theorem SNG-F11 (binary sector extraction).** For \(k\ge2\),
\[
[z]\mathcal B_G(x,q,z)=I_G(x,q)-1-x^k.
\]
Also \(I_G(x,q)=x^kI_G(x^{-1},q)\).

*Proof.* A minimum-zero span-one profile takes values zero and one and contains both values. It is uniquely the indicator of a nonempty proper subset. Its volume is subset size and its energy is cut size. The omitted empty and full subsets give \(1\) and \(x^k\). Complementation preserves cut size and sends subset size to \(k-|S|\), proving reciprocity. \(\square\)

The symmetry pairs the two sides of a cut. We count both sides as different profiles. A side of size \(r\) and its complement of size \(k-r\) appear at their respective powers of \(x\); when the sizes are equal they still contribute two unless other multiplicities happen to coincide.

## 3.6 Minimum cuts are the first positive energy shell

For a connected graph on \(k\ge2\) vertices, define edge connectivity by
\[
\lambda(G)=\min_{\varnothing\ne S\subsetneq V}c_G(S)>0.
\]
This definition suffices here; no equivalence with a disjoint-path formulation is needed.

**Theorem SNG-F12 (minimum-energy shell).** Every nonzero normalized profile of span \(h\) obeys
\[
E_G(a)\ge\lambda(G)h.
\]
The smallest positive energy is \(\lambda(G)\), and its full marked population is
\[
[q^{\lambda(G)}]\mathcal B_G(x,q,z)
=z\sum_{\substack{\varnothing\ne S\subsetneq V\\c_G(S)=\lambda(G)}}x^{|S|}.
\]

*Proof.* For every nonnegative integer \(d\), \(d^2\ge d\). Hence the energy is at least the absolute-difference sum, which by coarea is \(\sum_t c_G(S_t)\). Every threshold set is nonempty and proper, so each cut is at least \(\lambda(G)\). This gives the bound. An indicator of a minimum cut has energy \(\lambda(G)\), so the bound is attained. If a nonzero profile has that energy, the bound forces \(h=1\), and then its subset must be a minimum cut. \(\square\)

For a path, \(\lambda=1\), so the first positive shell consists of the two orientations of every bridge cut. For a triangle, \(\lambda=2\), and its six nonempty proper subsets give
\[
[q^2]\mathcal B_{K_3}(x,q,z)=3z(x+x^2).
\]
These formulas identify the very first nonconstant energy sector. They do not recover arbitrary boundary overlaps at higher energy.

## 3.7 Support restrictions useful for exact computation

Several finite bounds follow directly from the profile interpretation. They identify impossible marked cells before any enumeration and provide consistency checks afterward.

**Theorem SNG-F13 (volume, span, and extreme energy).** Let \(k\ge2\), and let \(a\) be a nonzero normalized profile of volume \(m\) and span \(h\). Then
\[
h\le m\le(k-1)h.
\]
If \(G\) is connected,
\[
E_G(a)\ge\max\left\{\lambda(G)h,
\left\lceil\frac{h^2}{\operatorname{diam}(G)}\right\rceil\right\}.
\]
For any graph with maximum degree \(\Delta>0\), the largest energy among normalized volume-\(m\) profiles is \(\Delta m^2\), attained exactly by \(a=m e_i\) at maximum-degree vertices.

*Proof.* Some coordinate equals \(h\), so the sum is at least \(h\). At least one coordinate is zero and every other coordinate is at most \(h\), giving the upper bound. The minimum-cut bound was proved above. Choose a shortest path between a minimum-height and a maximum-height vertex. If its length is \(\ell\), telescoping and Cauchy–Schwarz give \(h^2\le\ell\sum_{e\text{ on path}}(\partial a)_e^2\le\operatorname{diam}(G)E_G(a)\). Energy is integral, giving the ceiling. Finally, the bound \(E_G(a)\le\Delta\sum_i a_i^2\le\Delta m^2\) was proved in Chapter 1. The profile \(m e_i\) at a maximum-degree vertex attains it. If equality holds and \(\Delta>0\), then \(\sum_i a_i^2=m^2\). Expanding \(m^2\) shows that all products \(a_i a_j\), \(i\ne j\), vanish; exactly one coordinate is nonzero. Its degree must be \(\Delta\). \(\square\)

Thus only
\[
\left\lceil\frac{m}{k-1}\right\rceil\le h\le m
\]
can occur in a nonzero volume-\(m\) normalized population. For fixed \(h\), complementation from Chapter 2 pairs volumes \(m\) and \(kh-m\). A computation violating either restriction has lost a normalization condition or a multiplicity.

Nested thresholds provide the human explanation for the hierarchy studied next. One occupied unit reveals a degree. Two units reveal degree mixing. Several units can occupy different heights and thereby test several linked boundaries. The information comes from their shared placement in one relation, not from replacing the original edge law with an unrelated interaction.

## 3.8 Primitive height scale and exact dilation

Repeated sets also encode a common integer scale. If every nonzero coordinate of a normalized profile is divisible by \(d\), division by \(d\) gives another normalized profile. Volumes and spans divide by \(d\), while energy divides by \(d^2\). This is an exact quadratic scaling law, not an approximation valid only at large height.

Call a nonzero normalized profile primitive when the greatest common divisor of its coordinates is one; zeros do not change that greatest common divisor. Let
\[
\mathcal P_G(x,q,z)
=\sum_{\substack{a\ge0,\ \min a=0\\a\ne0,\ \gcd(a_0,\ldots,a_{k-1})=1}}
x^{|a|}q^{E_G(a)}z^{\max a}.
\]
The zero profile is excluded because its common divisor is not a positive scale.

**Theorem SNG-F20 (primitive-height decomposition).** For every graph on \(k\ge2\) vertices,
\[
\mathcal B_G(x,q,z)-1
=\sum_{d\ge1}\mathcal P_G(x^d,q^{d^2},z^d).
\]
If \(\mu\) is the arithmetic Möbius function, characterized by \(\sum_{d\mid n}\mu(d)=1\) for \(n=1\) and zero otherwise, then
\[
\mathcal P_G(x,q,z)
=\sum_{d\ge1}\mu(d)
\bigl(\mathcal B_G(x^d,q^{d^2},z^d)-1\bigr).
\]
Both identities are coefficientwise finite in every positive volume.

*Proof.* Every nonzero integer profile has a unique positive greatest common divisor \(d\), and a unique primitive quotient \(b=a/d\). Normalization is preserved. Direct substitution gives \(|a|=d|b|\), \(E_G(a)=d^2E_G(b)\), and \(\max a=d\max b\), proving the first identity. For inversion, write \(T_dF=F(x^d,q^{d^2},z^d)\); then \(T_dT_e=T_{de}\). Substitute the first identity in the proposed inverse. The coefficient multiplying \(T_n\mathcal P_G\) is \(\sum_{d\mid n}\mu(d)\), leaving only \(n=1\). At volume \(m>0\), only \(d\mid m\) can contribute, so the rearrangement is finite coefficientwise. \(\square\)

For the path example \((0,2,2)\), the primitive quotient is \((0,1,1)\): volume two becomes four, energy one becomes four, and span one becomes two. This decomposition distinguishes a genuinely new shape of height profile from an integral dilation of an earlier shape. It provides another exact observation hierarchy that can be implemented independently of threshold-chain enumeration.

Primitive height here refers only to common divisibility of integer coordinates. It does not mean a primitive graph, a primitive conductor phase, or an element primitive in a different lattice. Those notions may interact in later calculations, but their definitions must not be merged because they share a word. The decomposition itself uses no connectedness assumption, so it also applies when nonconstant componentwise profiles have zero energy.
