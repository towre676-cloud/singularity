# The volume-5 height-series formula for cubic graphs

## Statement

Let \(G\) be a cubic (3-regular) graph on \(n\) vertices, and let

\[
L_G(x,q)=\sum_{h:V\to \mathbb Z_{\ge 0}} x^{\sum_v h_v}\,
q^{\sum_{uv\in E}(h_u-h_v)^2},\qquad \ell_G=\log L_G .
\]

Write \(a=q^{3}\), \(f=q^{-2}-1\), \(\kappa = af = q(1-q^2)\), and let
\(N_Y(G)\) denote the number of (not necessarily induced) subgraphs of \(G\)
isomorphic to \(Y\). The invariants below are: \(N_3\) = triangles,
\(N_4\) = 4-cycles, \(N_{\mathrm{dia}}\) = diamonds (two triangles sharing an
edge), \(N_{K_4}\), \(N_5\) = 5-cycles, \(N_{K_{2,3}}\), \(N_{\Theta(1,2,3)}\) =
"houses" (the theta graph with path lengths \(1,2,3\): a triangle and a square
sharing an edge), and \(N_{K_{2,3}+e}\) = copies of \(K_{2,3}\) with one extra
edge joining two vertices on the 3-side.

**Theorem.** Let \(A,B\) be cubic graphs on \(n\) vertices whose height series
agree through volume 4 (equivalently, by the volume-4 theorem, with
\((N_3,N_4,N_{\mathrm{dia}},N_{K_4})\) equal). Then

\[
[x^5]\bigl(L_A-L_B\bigr)
=\kappa^{5}\Bigl[\Delta N_5
+ f\,\bigl(\Delta N_{K_{2,3}}+\Delta N_{\Theta(1,2,3)}\bigr)\Bigr]
+ \kappa^{5} f^{2}\,\Delta N_{K_{2,3}+e},
\]

where \(\Delta\) denotes the difference \(A\) minus \(B\) of each count.

For girth \(\ge 4\) graphs both triangle-bearing terms vanish
(\(\Theta(1,2,3)\) and \(K_{2,3}+e\) each contain a triangle) and the formula
reduces to \(\kappa^5(\Delta N_5 + f\,\Delta N_{K_{2,3}})\), which is exactly
the repo's SNG-F61 at \(R=5\), with the "bicycle" invariant identified as
\(N_{K_{2,3}}\). The genuinely new content beyond SNG-F61 is the house term at
the same order in \(f\), and the \(f^2\) term \(N_{K_{2,3}+e}\).

## Proof

We follow the volume-4 proof (`closures/diamond_proof/PROOF.md`): the
connected-support expansion of \(\log L\) (repo SNG-F55), the Bell bridge
between \(L\) and \(\ell\), and absorption of all small supports by moment
identities. Steps marked [finite check] are exact rational computations over
finitely many small graphs, reproduced by the scripts in this directory; the
remaining steps are hand arguments.

### Step 1: the Bell bridge at volume 5

The Bell identity
\(L_5=\ell_5+\ell_1\ell_4+\ell_2\ell_3+\tfrac12\ell_1^2\ell_3
+\tfrac12\ell_1\ell_2^2+\tfrac16\ell_1^3\ell_2+\tfrac1{120}\ell_1^5\)
expresses \(L_5\) through \(\ell_5\) and products of \(\ell_k\), \(k\le 4\).
Agreement of \(L\) through volume 4 is equivalent to agreement of \(\ell\)
through volume 4 (the Bell relations are triangular with ones on the
diagonal), so for agreeing pairs every product term cancels in the difference
and \(\Delta L_5=\Delta\ell_5\). \(\square\)

### Step 2: cumulant decomposition

By SNG-F55, \(\ell_G=\sum_{S:\,G[S]\text{ connected}}\Phi_S\) with \(\Phi_S\)
depending only on the isomorphism type \(\tau\) of \(G[S]\) (ambient weights
\(w_v=3\)). Grouping by type,

\[
\ell_5(G)=\sum_{k\le 5}\sum_{|\tau|=k} s_\tau(G)\,c_\tau,
\qquad c_\tau=[x^5]\Phi_\tau,
\]

where \(s_\tau(G)\) is the number of induced copies of \(\tau\) in \(G\)
(\(\Phi_S=0\) for disconnected \(S\)). [Finite check: this identity was
verified exactly for all 518 graphs of the sample pools.] Write
\(\ell_5(G)=S_{\le 4}(G)+\sum_{|\tau|=5}s_\tau(G)c_\tau\), where
\(S_{\le4}\) collects all supports of size \(\le 4\) (the coefficients
\(c_\tau\) for \(|\tau|\le4\) involve height assignments with repeated
values — the "doubled-height" coefficients of the volume-4 proof).

### Step 3: supports of size \(\le 4\) are determined by the old invariants

**Lemma A.** \(S_{\le4}(G)\) is a function of
\((n,N_3,N_4,N_{\mathrm{dia}},N_{K_4})\) alone. Hence \(\Delta S_{\le4}=0\)
for agreeing pairs.

*Proof.* \(S_{\le4}(G)=\sum_{k\le4}\sum_\tau s_\tau(G)d_\tau\) with fixed
\(d_\tau\in\mathbb Q(q)\). For each \(k\le 4\) the induced counts
\(s_\tau\), \(|\tau|=k\), and the subgraph counts \(N_Y\), \(|Y|=k\), are
related by the subgraph matrix \(N_Y=\sum_\tau s_\tau\,\mathrm{sub}_Y(\tau)\),
which is invertible over \(\mathbb Q\) [finite check: ranks \(2/2, 4/4,
11/11\) for \(k=2,3,4\)]. So it suffices that every \(N_Y\), \(|Y|\le4\), is a
function of the old invariants. For \(|Y|\le3\) this is the volume-4 proof.
For \(|Y|=4\) the eleven counts are, with \(m=3n/2\):

| \(Y\) | \(N_Y\) |
|---|---|
| empty | \(\binom n4\) |
| one edge | \(m\binom{n-2}{2}\) |
| \(2K_2\) | \(\binom m2-3n\) |
| \(P_3+\) iso | \(3n(n-3)\) |
| \(P_4\) | \(4m-3N_3\) |
| \(K_{1,3}\) | \(n\) |
| \(C_3+\) iso | \(N_3(n-3)\) |
| \(C_4\) | \(N_4\) |
| paw | \(3N_3\) |
| diamond | \(N_{\mathrm{dia}}\) |
| \(K_4\) | \(N_{K_4}\) |

Each is a direct double count; the only non-immediate one is
\(N_{P_4}=4m-3N_3\): ordered paths \(v_0v_1v_2v_3\) on distinct vertices are
counted by their middle edge \(v_1v_2=e\), giving
\(\sum_e 2\bigl[(d_{v_1}-1)(d_{v_2}-1)-t(e)\bigr]\) with \(t(e)\) the number
of triangles on \(e\); in a cubic graph this is \(2(4m-3N_3)\), and each
\(P_4\) subgraph has exactly two such orderings. [Finite check: all eleven
formulas verified on all 518 pool graphs, zero mismatches; and directly:
among all pool graphs, no two graphs with equal
\((n,N_3,N_4,N_{\mathrm{dia}},N_{K_4})\) have different \(S_{\le4}\) —
zero collisions.] \(\square\)

### Step 4: the size-5 raw identity

For a connected type \(\tau\) on 5 vertices, the multilinear coefficient is
\(c_\tau = a^5 P(\tau)\), where
\(P(\tau)=\sum_{E'} f^{|E'|}\) over connected spanning edge subsets
\(E'\subseteq E(\tau)\) (the spanning polynomial; this is the volume-4
machinery, [finite check: \([x^k]\Phi_\tau=a^kP(\tau)\) verified for all
types on \(\le5\) vertices]). Therefore

\[
\sum_{\tau\text{ conn},\,|\tau|=5} s_\tau(G)\,P(\tau)
=\sum_{\substack{Y\text{ conn}\\|Y|=5}} N_Y(G)\, f^{e(Y)} .
\]

*Proof.* Both sides equal \(\sum_{(S,E')} 1\) grouped two ways, summed over
pairs \((S,E')\) with \(S\subseteq V\), \(|S|=5\), and \(E'\) a connected
spanning edge set of \(G[S]\): the left side groups by the isomorphism type
\(\tau\) of \(G[S]\), using \(N_Y(G)=\sum_\tau s_\tau(G)\,\mathrm{sub}_Y
(\tau)\); the right side groups by the isomorphism type \(Y\) of \((S,E')\).
[Finite check: expanding each power-of-\(f\) coefficient vector of the
\(P(\tau)\) in the basis of pattern functionals \(\mathrm{sub}_Y\) over all
34 graphs \(Y\) on 5 vertices gives the unique solution
\(\alpha_{Y,j}=1\) if \(Y\) is connected with \(e(Y)=j\), else \(0\).] In
particular

\[
\Delta\ell_5 = a^5 \sum_{Y\text{ conn}} f^{e(Y)}\,\Delta N_Y ,
\]

the sum over the 21 connected graphs \(Y\) on 5 vertices (the size \(\le4\)
parts having cancelled by Lemma A, and likewise the size \(\le 3\) parts).

### Step 5: vacuous patterns

If \(Y\) has a vertex of degree \(\ge4\) then \(N_Y(G)=0\) in every cubic
graph, since subgraph degrees do not exceed host degrees. This kills: the
star \(K_{1,4}\) at \(f^4\); one \(f^5\) pattern (degrees \(42211\)); the
bowtie (two triangles at one vertex) and one further pattern (degrees
\(43221\)) at \(f^6\); all three remaining \(f^7\) patterns besides
\(K_{2,3}+e\) (degrees \(44222, 43331, 43322\)); and every pattern at
\(f^8,f^9,f^{10}\) (max degree \(\ge4\) throughout). [Finite check: all these
counts are zero on all 518 pool graphs.] Note in particular that a "bowtie"
term, which one might guess by analogy with the diamond correction, is
**vacuous for cubic graphs**.

### Step 6: determination identities at size 5

The remaining non-target counts are determined by double counting. In each
case the pattern has a unique "rigid core" (triangle, square, or diamond)
and all extensions are forced by 3-regularity, except for explicit collision
corrections.

*Trees (\(f^4\)).* The fork (degrees \(32111\)) bijects with triples
\((c,x,w)\): \(c\) the degree-3 vertex of the tree, \(x\in N(c)\),
\(w\in N(x)\setminus\{c\}\) with \(w\notin N(c)\setminus\{x\}\cup\{c\}\)
(distinctness of the 5 vertices); the number of choices is
\(\sum_c\sum_{x\in N(c)}(2-\tau(cx))=6n-6N_3\), since
\(\sum_{c}\sum_{x\in N(c)}\tau(cx)=6N_3\). Hence
\(N_{\mathrm{fork}}=6n-6N_3\). For \(P_5\): paths biject (up to direction)
with \((c,(x,y),(v_0,v_4))\), \(c\) the middle vertex, \((x,y)\) an ordered
pair of distinct neighbours of \(c\), \(v_0\in N(x)\setminus\{c\}\),
\(v_4\in N(y)\setminus\{c\}\), all vertices distinct; the count with
collisions allowed is \(\sum_c\sum_{(x,y)}(2-t)^2\) (\(=24n-18N_3\), where
\(t=[x\sim y]\)), and the collisions \(v_0=v_4\) are counted by
\(\sum_c\sum_{(x,y)} s(x,y)=\sum_{c\ne w}d_{cw}(d_{cw}-1)
=4\sum_{\{c,w\}}\binom{d_{cw}}2=8N_4\), using
\(\sum_{\{c,w\}}\binom{d_{cw}}2=2N_4\) (a pair of common neighbours of
\(\{c,w\}\) is a 4-cycle with diagonal \(\{c,w\}\), and each \(C_4\) subgraph
has two diagonals). Hence \(N_{P_5}=(24n-18N_3-8N_4)/2=12n-9N_3-4N_4\).

*Unicyclic (\(f^5\)).* Triangle with pendant tails at two distinct vertices:
per triangle, \(\binom 32=3\) choices of the tailed vertices and forced
tails, except when the two tails land on the same vertex \(w\); then
\(w\) is a common neighbour of an edge of the triangle, i.e. the triangle
lies in a diamond and the pair is its spine pair — 2 per diamond. So
\(N=3N_3-2N_{\mathrm{dia}}\). The tadpole (triangle with a pendant path of
length 2 at one vertex): per (triangle, vertex), the first tail step is
forced and the second has 2 choices minus \(\mathrm{bad}\), where
\(\mathrm{bad}\) counts the second step landing back in the triangle;
\((T,v)\mapsto\) bad configurations biject with (edge \(e\), ordered pair of
distinct triangles on \(e\), endpoint of \(e\)), giving
\(\sum_e 2\tau(e)(\tau(e)-1)=4N_{\mathrm{dia}}\). So
\(N_{\mathrm{tadpole}}=6N_3-4N_{\mathrm{dia}}\). Square with a pendant edge:
4 choices of vertex per square, forced edge, except when the edge is the
diagonal of the square (a chord), which happens exactly for the rim square
of a diamond, at its two spine vertices: \(N=4N_4-2N_{\mathrm{dia}}\).

*Bicyclic (\(f^6\)).* Diamond with a pendant edge at an apex: each apex has
exactly one external edge, forced, and the diamond in such a subgraph is
unique: \(N=2N_{\mathrm{dia}}\).

[Finite check: all six identities hold, with these exact coefficients, on
every one of the 518 pool graphs, at each of \(n=8,10,12\) independently.]

The counts that are *not* determined by the old invariants are exactly
\(N_5\) (\(f^5\)), \(N_{K_{2,3}}\) and \(N_{\Theta(1,2,3)}\) (\(f^6\)), and
\(N_{K_{2,3}+e}\) (\(f^7\)). For the last: \(N_{K_{2,3}+e}\) bijects with
pairs \((D,w)\) where \(D\) is a diamond and \(w\) is adjacent to both
apices of \(D\) (the diamond in a \(K_{2,3}+e\) is its unique pair of
triangles sharing an edge, and \(w\) is the degree-2 vertex); whether the
two apex-external edges of a diamond converge on a common vertex is a
second-order configuration not visible to any of the other counts.

### Step 7: assembly

Under agreement, \(\Delta\) of every determined count in Step 6 vanishes,
the vacuous counts contribute nothing, and Step 4 leaves

\[
\Delta\ell_5
= a^5\Bigl[f^5\Delta N_5 + f^6\bigl(\Delta N_{K_{2,3}}
+ \Delta N_{\Theta(1,2,3)}\bigr) + f^7\Delta N_{K_{2,3}+e}\Bigr].
\]

Since \(\kappa^5 = a^5 f^5\), this is the stated formula, and Step 1 gives
\(\Delta L_5=\Delta\ell_5\). \(\square\)

## What is proved, computed, conjectured

*Proved* (modulo the repo's SNG-F55 and the volume-4 theorem): the theorem
above. The hand steps are Steps 1, 5, 6, 7 and the grouping argument of
Step 4; the steps discharged by finite exact computation are: the
cumulant identity per graph (Step 2), invertibility of the subgraph
matrices and the eleven 4-vertex formulas (Step 3), the multilinear
identity \(c_\tau=a^5P(\tau)\) and the decomposition coefficients
\(\alpha_{Y,j}\) (Step 4) — each is an exact rational computation over
finitely many graphs on \(\le5\) vertices, reproduced by `vol5_lib.py`,
`vol5_main.py`, `vol5_decomp2.py`, `vol5_relations.py` with logs in this
directory.

*Computed:* the formula holds on all 5,045 agreeing pairs of the sample
pools (\(n=8,10,12\)) with zero failures (`vol5_final_check.py`), and the
determination identities hold on all 518 pool graphs
(`vol5_relations.py`). The \(f^2\) term, which is vacuous on the pool
pairs, is confirmed on 59 fresh agreeing pairs at \(n=14\) with
\(\Delta N_{K_{2,3}+e}\ne0\): full formula 59/59, formula without the term
0/59 (`vol5_k23e_search.py`).

*Not claimed:* nothing about volumes \(\ge6\); nothing about non-cubic
graphs (vacuity Step 5 and every determination identity use 3-regularity
essentially).
