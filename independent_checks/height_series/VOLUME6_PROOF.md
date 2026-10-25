# Volume 6: the $x^6$ correction formula — proof

**Status: PROVED** (modulo the standing input SNG-F55 and the proved
volume-4 and volume-5 theorems), by the same route as the volume-5
proof: Bell bridge to cumulants, subgraph-matrix invertibility at sizes
$\le 5$, explicit pattern formulas, connected-support decomposition at
size 6, and double-counting identities proved by hand. The finite
exact steps (subgraph matrices, $\beta$-tables, type-level identities)
are machine-discharged in exact rational arithmetic and are
hand-auditable; every determination identity below is additionally
verified on 5,518 pool graphs and on component-rich audit graphs
(`vol6_k4fix.py`). Computational evidence and per-term test status are
in `REPORT.md`; this file contains the proof.

## Setting and statement

For a cubic graph $G$ let
$L_G(x,q)=\sum_{h:V\to\mathbb Z_{\ge0}} x^{\sum_v h_v}
q^{\sum_{uv\in E}(h_u-h_v)^2}$ and $\ell_G=\log L_G$. Write
$a=q^3$, $f=q^{-2}-1$, $\kappa=af=q(1-q^2)$, so $a^6f^e=\kappa^6 f^{e-6}$.
$N_Y(G)$ is the number of (not necessarily induced) subgraphs of $G$
isomorphic to $Y$. The volume-$\le5$ invariant vector is

$$I_5(G)=\big(N_3,\;N_4,\;N_{\mathrm{dia}},\;N_{K_4},\;N_5,\;
N_{K_{2,3}},\;N_{\Theta(1,2,3)},\;N_{K_{2,3}+e}\big).$$

The eleven size-6 patterns in the formula are:

* $C_6$, the hexagon ($e=6$);
* $\Theta(1,2,4)$, $\Theta(2,2,3)$, $\Theta(1,3,3)$ and the **barbell**
  (two triangles joined by a bridge) ($e=7$);
* **prism-minus-triangle-edge**; **prism-minus-spoke**; the **closed
  diamond**: a diamond whose two apex vertices are joined by an
  additional path of length 3 (equivalently $C_6$ with two parallel
  chords); and $K_{3,3}-e$ ($e=8$);
* $K_{3,3}$ and the triangular prism ($e=9$).

**Theorem (volume 6).** *Let $A,B$ be cubic graphs on the same number
of vertices agreeing through volume 5 — equivalently, by the volume-4
and volume-5 theorems, $I_5(A)=I_5(B)$. Then*

$$\Delta[x^6]L=\kappa^6\big[\Delta N_{C_6}
+f\big(\Delta N_{\Theta(1,2,4)}+\Delta N_{\Theta(2,2,3)}
+\Delta N_{\Theta(1,3,3)}+\Delta N_{\mathrm{barbell}}\big)$$
$$+\;f^2\big(\Delta N_{\mathrm{prism}-\triangle}
+\Delta N_{\mathrm{prism}-\mathrm{spoke}}
+\Delta N_{\mathrm{closed\ diamond}}
+\Delta N_{K_{3,3}-e}\big)
+f^3\big(\Delta N_{K_{3,3}}+\Delta N_{\mathrm{prism}}\big)\big].$$

**Specialisations.** If both graphs have girth $\ge5$, every pattern
except $C_6$ contains a 3- or 4-cycle, so
$\Delta[x^6]L=\kappa^6\Delta N_{C_6}$: at volume 6 the pure cycle term
is the whole story, exactly as SNG-F61 is at volume 5. If both have
girth $\ge4$ (triangle-free), the formula reduces to
$\kappa^6[\Delta N_{C_6}+f(\Delta N_{\Theta(2,2,3)}+\Delta N_{\Theta(1,3,3)})
+f^2\Delta N_{K_{3,3}-e}+f^3\Delta N_{K_{3,3}}]$.

## Step 1: the Bell bridge at volume 6

$L=\exp\ell$ gives $[x^6]L$ as a polynomial in
$\ell_0,\dots,\ell_6$ (Bell polynomials). Agreement through volume 5
gives $\Delta\ell_r=0$ for $r\le5$ and $\Delta L_r=0$ for $r\le5$;
every monomial of the volume-6 Bell polynomial except $\ell_6$ itself
involves only $\ell_r$, $r\le5$ (with $\ell_0$ a function of $n$).
Hence $\Delta[x^6]L=\Delta\ell_6$.

## Step 2: cumulant decomposition (SNG-F55)

As at volume 5, $\ell_6(G)=\sum_{k\le6}\sum_{\tau\text{ connected}}
s_\tau(G)\,c_\tau$ with $c_\tau=[x^6]\Phi_\tau$, $s_\tau$ the induced
counts, $\Phi_\tau$ the connected-support kernel of SNG-F55. Write
$\ell_6=S_{\le5}^{(6)}+T_6$, the sums over $k\le5$ and $k=6$.

## Step 3 (Lemma A): $S_{\le5}^{(6)}$ is a function of $I_5$

For each $k\le5$ let $M_k=(\mathrm{sub}_Y(\tau))_{\tau,Y}$ be the
subgraph matrix (rows: all types $\tau$ on $k$ vertices; columns: all
patterns $Y$). $M_k$ is invertible: ranks $2,4,11,34$ at
$k=2,3,4,5$ (exact; `vol6_libtest.py`). Extend $c^{(6)}$ to all types
by $0$ on disconnected types and set
$\beta^{(k)}=M_k^{-1}c^{(6)}$ (a vector of $q$-polynomials). Then
$\sum_{\tau\text{ conn}}s_\tau c_\tau=\sum_Y\beta^{(k)}_Y N_Y$ at each
size $k$, by the defining identity $N_Y=\sum_\tau s_\tau\mathrm{sub}_Y(\tau)$.
The $\beta$-supports are small (sizes $2,3,4,5$: $1,2,6,21$ patterns;
full coefficient tables in `vol6_relations.json`), every pattern in
them is connected, and its count is determined by $I_5$:

* invariants themselves: $N_3,N_4,N_{\mathrm{dia}},N_{K_4}$ (size $\le4$);
  $C_5$, $K_{2,3}$, $\Theta(1,2,3)$, $K_{2,3}+e$ (size 5);
* vacuous patterns (a vertex of degree $\ge4$): $N_Y=0$ in every cubic
  graph, since a subgraph's degrees are at most the host's;
* $N_{K_1}=n$; $N_{\text{edge}}=\frac32n$; $N_{P_3}=3n$
  ($=\sum_v\binom{\deg v}{2}$);
* $N_{K_{1,3}}=n$ (each vertex is the centre of exactly one copy, its
  three neighbours being forced);
* $N_{P_4}=6n-3N_3$ and $N_{\mathrm{paw}}=3N_3$: for the paw, each
  triangle carries exactly 3 copies, one per vertex with its forced
  external edge, and a paw has a unique triangle;
* size 5: $N_{\mathrm{fork}}=6n-6N_3$,
  $N_{P_5}=12n-9N_3-4N_4$, $N_{\triangle+2\mathrm{pend}}=3N_3-2N_{\mathrm{dia}}$,
  $N_{\mathrm{tadpole}}=6N_3-4N_{\mathrm{dia}}$,
  $N_{C_4+\mathrm{pend}}=4N_4-2N_{\mathrm{dia}}$ (these five are the
  volume-5 Step-6 identities), and
  $N_{\mathrm{dia+tail}}=2N_{\mathrm{dia}}-12N_{K_4}$: each diamond has
  2 apex vertices with a forced external edge; inside a $K_4$
  component all $6\cdot2=12$ such configurations per $K_4$ collapse
  onto 4 vertices, contributing the correction. (The $-12N_{K_4}$ term
  is invisible on connected graphs with $n>4$ and does not affect any
  $\Delta$ under $I_5$-agreement; it is needed for the identity to
  hold for arbitrary cubic graphs.)

Each identity is a direct double count of the volume-5 kind; all are
verified exactly on 5,518 pool graphs and on $K_4/K_{3,3}$/prism
audit graphs (`vol6_k4fix.py`: the only corrections anywhere are
multiples of $N_{K_4}$ as displayed). With the size-1 term
$n\cdot c_{K_1}^{(6)}$ (a function of $n$), Lemma A follows:
$\Delta S_{\le5}^{(6)}=0$ under $I_5$-agreement. Direct confirmation:
$S_{\le5}^{(6)}=\sum_Y\beta_Y N_Y$ holds for every one of the 5,518
pool graphs, and $S_{\le5}^{(6)}$ has zero collisions on
$(n,I_5)$-classes (`vol6_relations.py`).

## Step 4: the raw size-6 identity

For a connected type $\tau$ on 6 vertices, the multilinear coefficient
of $\Phi_\tau$ is $[x^6]\Phi_\tau=a^6P(\tau)$, where $P(\tau)$ is the
spanning polynomial; this is verified exactly for all 112 connected
6-types (and $\Phi_\tau$ vanishes below volume 6) in
`vol6_libtest.py`, by the same computation as volume 5, Step 3. The
alpha identity $P_j(\tau)=\sum_{Y\text{ conn},\,e(Y)=j}\mathrm{sub}_Y(\tau)$
holds for all 112 types at size 6 (verified ibid.), so exactly as at
volume 5,

$$T_6(G)=a^6\sum_{Y\text{ connected},\,|Y|=6}N_Y(G)\,f^{e(Y)}.$$

This per-graph identity is also verified directly on all 5,518 pool
graphs (`vol6_main.py`).

## Step 5: vacuity at size 6

A connected 6-pattern with a vertex of degree $\ge4$ has $N_Y=0$ in
every cubic graph. Of the 112 connected 6-types, exactly **29** are
non-vacuous (catalogue: `vol6_types6.json`).

## Step 6: determination of the eighteen non-formula patterns

**Method (rigid core).** For each pattern $Y$ below, prune leaves to
get the 2-core $C$; every copy of $Y$ is obtained from a unique copy
of $C$ by forced external edges at the core's degree-$\le2$ vertices
(in a cubic host the external edge at such a vertex is unique when it
exists in the pattern). Count configurations as
(core count) $\times$ (forced choices); a configuration fails to be a
copy of $Y$ only when identifications collapse its vertex set, and
then $(S,E')$ is a denser pattern from the finite catalogue — either
an $I_5$ invariant or, inside a $K_4$ component, a $K_4$ correction
($N_{K_4}\in I_5$, so determination is unaffected; audit graphs with
$K_4$ components exposed exactly six such corrections, all verified).
Each identity below is verified exactly on all 5,518 pool graphs and
on the audit graphs $K_4$, $K_4^{\sqcup2}$, $K_4\sqcup K_{3,3}$,
$K_{3,3}$, prism, $K_{3,3}\sqcup$prism, prism$\sqcup$Petersen
(`vol6_k4fix.py`, zero failures).

*Trees* (walk counts with cycle corrections; the counts of injective
paths are extracted from closed-walk moments, whose non-injective
terms are exactly the cycle corrections shown):

* $N_{P_6}=24n-24N_3-12N_4+6N_{\mathrm{dia}}-5N_5$
* $N_{T(1,1,3)}=12n-12N_3-8N_4+4N_{\mathrm{dia}}$,
  $N_{T(1,2,2)}=12n-21N_3-4N_4+8N_{\mathrm{dia}}$
* $N_{S_{2,2}}=\frac32n-3N_3+N_{\mathrm{dia}}$: one candidate per edge
  (both centres' leaf pairs are forced); it fails iff the edge lies
  in a triangle; writing $3N_3=T_1+2T_2$ for edges in exactly
  $1$ resp. $2$ triangles and $T_2=N_{\mathrm{dia}}$ (spine bijection)
  gives the formula.

*Unicyclic* (core = the unique cycle; tails forced):

* $N_{C_5+\mathrm{pend}}=5N_5-2N_{\Theta(1,2,3)}$: 5 attachment points
  per pentagon; the lost ones are the 2 spine vertices of a house,
  whose external edge is the chord, one pentagon per house.
* $N_{C_4+P_2\mathrm{tail}}=8N_4-4N_{\mathrm{dia}}-6N_{K_{2,3}}-2N_{\Theta(1,2,3)}$
* $N_{C_4+2\mathrm{pend,opp}}=2N_4-N_{\mathrm{dia}}-3N_{K_{2,3}}$,
  $N_{C_4+2\mathrm{pend,adj}}=4N_4-4N_{\mathrm{dia}}-N_{\Theta(1,2,3)}+12N_{K_4}$
* $N_{\triangle+\mathrm{cherry}}=3N_3-4N_{\mathrm{dia}}+12N_{K_4}$
* $N_{\triangle+\mathrm{pend}+P_2\mathrm{tail}}
  =12N_3-12N_{\mathrm{dia}}-2N_{\Theta(1,2,3)}+24N_{K_4}$
* $N_{\triangle+P_3\mathrm{tail}}=12N_3-8N_{\mathrm{dia}}-2N_{\Theta(1,2,3)}$
* $N_{\triangle+3\mathrm{pend}}=N_3-2N_{\mathrm{dia}}+8N_{K_4}$

*Bicyclic* (core = diamond, $K_{2,3}$, or house):

* $N_{\mathrm{dia}+2\mathrm{pend}}
  =N_{\mathrm{dia}}-N_{K_{2,3}+e}-6N_{K_4}$: one configuration per
  diamond; the apex edges share a neighbour iff the configuration is
  a $K_{2,3}+e$ (unique diamond per $K_{2,3}+e$: its spine is the only
  edge in two triangles), or close inside a $K_4$ (6 per $K_4$).
* $N_{\mathrm{dia}+P_2\mathrm{tail}}=4N_{\mathrm{dia}}-2N_{K_{2,3}+e}-24N_{K_4}$
* $N_{K_{2,3}+\mathrm{pend}}=3N_{K_{2,3}}-2N_{K_{2,3}+e}$
* $N_{\mathrm{house}+\mathrm{pend@apex}}=N_{\Theta(1,2,3)}-4N_{K_{2,3}+e}$,
  $N_{\mathrm{house}+\mathrm{pend@corner}}=2N_{\Theta(1,2,3)}-4N_{K_{2,3}+e}$

*Tricyclic:*

* $N_{(K_{2,3}+e)+\mathrm{pend}}=N_{K_{2,3}+e}$: $K_{2,3}+e$ has a
  unique degree-2 vertex; its forced external edge gives a bijection
  (the 2-core of the result is the original copy).

No identity is asserted for $K_{3,3}-e$: it is **not** determined by
$I_5$ — see Step 7 — and it appears in the formula.

## Step 7: assembly, and why the eleven terms are exactly right

Under $I_5$-agreement, Steps 1–3 give $\Delta[x^6]L=\Delta T_6$; by
Steps 4–5, $\Delta L_6=\kappa^6\sum_{Y\text{ non-vacuous}}f^{e(Y)-6}\Delta N_Y$;
by Step 6 every summand vanishes except the eleven patterns of the
theorem. This proves the formula. The eleven are genuinely
independent invariants, not artefacts of the proof: their difference
vectors span a space of full rank $11$ over the agreeing pairs
constructed in `REPORT.md` (rank 8 within the random pools, plus the
prism component pairs, plus the weld pairs, separating the remaining
three), and each coefficient is forced by the raw identity of Step 4.
In particular $K_{3,3}-e$ could not be absorbed: no formula for
$N_{K_{3,3}-e}$ over $I_5$ (or over $I_5$ plus the other eight pool
invariants, with polynomial coefficients) fits the data
(`vol6_m2012.py`), and the weld pairs show $\Delta N_{K_{3,3}-e}=-6,-7$
on agreeing pairs — the same phenomenon as $K_4$ at volume 4: a
saturated-adjacent pattern that only component-level constructions
can move.
