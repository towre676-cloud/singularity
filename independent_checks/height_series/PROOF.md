# The diamond correction at volume 4: a complete proof

**Result.** Let $A$ and $B$ be cubic (3-regular) graphs on the same number
$n$ of vertices whose height series agree through volume 3,
$L_A \equiv L_B \pmod{x^4}$. Then

$$
[x^4]\bigl(L_A - L_B\bigr)
\;=\;
\Delta N_4 \cdot q^{4}(1-q^2)^{4}
\;+\;
\Delta N_{\mathrm{dia}} \cdot q^{2}(1-q^2)^{5}
\;+\;
\Delta N_{K_4} \cdot (1-q^2)^{6},
$$

where $\Delta$ denotes the difference $A$ minus $B$, $N_4$ counts
4-cycles (squares) as subgraphs, $N_{\mathrm{dia}}$ counts diamonds
(pairs of triangles sharing an edge), and $N_{K_4}$ counts $K_4$
subgraphs. In particular, if $A$ and $B$ are **connected** and $n > 4$,
then $N_{K_4} = 0$ for both and the conjectured two-term formula holds
exactly as stated:

$$
[x^4]\bigl(L_A - L_B\bigr)
= \Delta N_4\, q^{4}(1-q^2)^{4} + \Delta N_{\mathrm{dia}}\, q^{2}(1-q^2)^{5}.
$$

The proof follows the repository's own connected-support method
(`docs/chapters/10_inverse_problems.md`, Theorems SNG-F55, SNG-F56,
SNG-F61). In fact the $g=3$, $R=4$ case of SNG-F61 already contains the
normalised form $N_4 + fN_{\mathrm{diamond}} + f^2 N_{K_4}$ at the level
of $\log F_\lambda$; what is proved here is the complete transfer of that
statement to $L$ itself, with every step made explicit: the log/series
bridge (§2), the enumeration of all connected supports of size $\le 4$
with their exact polynomials (§4), the moment identities that absorb
every non-target term into a universal function of $(n, N_3)$ (§5), the
deduction $N_3(A) = N_3(B)$ from the agreement hypothesis (§3), and the
$K_4$ analysis (§6). All finite enumerations and identities are verified
by exact computation in `verify_proof.py` (see §8 and the STATUS
section).

---

## 1. Setup and the repository's framework

For a graph $G$ on vertices $V$, $|V| = n$, the height series is

$$
L_G(x,q) \;=\; \sum_{h \in \mathbb{N}^{V}} x^{|h|}\,
q^{\sum_{uv \in E} (h_u - h_v)^2},
\qquad |h| = \sum_v h_v .
$$

This is the $\lambda = 0$, $d$-regular case of the series $F_\lambda(H)$
of chapter 10: writing $w_v = \deg(v) + \lambda$ and expanding the square,

$$
\sum_{uv \in E}(h_u-h_v)^2
= \sum_v \deg(v)\, h_v^2 - 2\sum_{uv \in E} h_u h_v ,
$$

so $L_G = F_0(G)$ with all weights $w_v = 3$. For a set $S \subseteq V$
let $Z_S$ be the same sum restricted to heights supported in $S$ (the
ambient degrees $w_v = 3$ are kept), and define the cumulant

$$
\Phi_S \;=\; \sum_{T \subseteq S} (-1)^{|S|-|T|} \log Z_T .
$$

**Theorem SNG-F55 (repo).** $\Phi_S = 0$ unless $G[S]$ is connected;
$\Phi_S = O(x^{|S|})$; $\Phi_S$ depends only on the isomorphism type of
$G[S]$ decorated by the weights $w_v$; and
$\log L_G = \sum_{S : G[S] \text{ connected}} \Phi_S$.

Since every vertex of a cubic graph has the same weight $w_v = 3$, the
decoration is constant and $\Phi_S$ depends only on the isomorphism type
of the induced subgraph $G[S]$. We write $\varphi_\tau$ for the common
value of $\Phi_S$ over sets $S$ of type $\tau$, and
$\ell_G = \log L_G$, $\ell_r = [x^r]\ell_G$, $L_r = [x^r]L_G$ (polynomials
in $q$).

Set, following the chapter,

$$
a = q^{3}, \qquad f = q^{-2} - 1 = \frac{1-q^2}{q^2},
\qquad \kappa = af = q(1-q^2).
$$

Note for later: $\kappa^4 = q^4(1-q^2)^4$,
$\kappa^4 f = q^2(1-q^2)^5$, $\kappa^4 f^2 = (1-q^2)^6$.

## 2. Step 1 — the log bridge: disconnected supports and products of lower terms

The coefficient $L_4$ of $L_G$ itself receives contributions from
*disconnected* supports: a height assignment of volume 4 can be a product
of assignments of volumes $1+3$, $2+2$, $1+1+2$, $1+1+1+1$ on disjoint
vertex sets. These are exactly the terms produced by exponentiating
$\ell_G$, and the agreement hypothesis disposes of all of them at once.
For any formal power series with $L_0 = 1$ and $\ell = \log L$,

$$
L_1 = \ell_1,\qquad
L_2 = \ell_2 + \tfrac12 \ell_1^2,\qquad
L_3 = \ell_3 + \ell_1\ell_2 + \tfrac16 \ell_1^3,
$$

$$
L_4 = \ell_4 + \ell_1\ell_3 + \tfrac12\ell_2^2
      + \tfrac12\ell_1^2\ell_2 + \tfrac1{24}\ell_1^4
$$

(the complete exponential Bell polynomials; verified symbolically in
`verify_proof.py`, §E). The system is triangular: $L_r$ for $r \le 3$
determines $\ell_r$ for $r \le 3$ and conversely
($\ell_1 = L_1$, $\ell_2 = L_2 - L_1^2/2$,
$\ell_3 = L_3 - L_1L_2 + L_1^3/3$). Hence

$$
L_A \equiv L_B \pmod{x^4}
\iff
\ell_A \equiv \ell_B \pmod{x^4},
\qquad\text{and then}\qquad
\Delta L_4 = \Delta \ell_4,
$$

because every term of $L_4$ other than $\ell_4$ is a polynomial in
$\ell_1, \ell_2, \ell_3$, which agree. **It therefore suffices to prove
the formula for $[x^4]\log L_G$**, where by SNG-F55 only *connected*
supports occur. This is the complete treatment of disconnected-support
products: they are precisely the Bell terms, and they cancel by the
hypothesis.

## 3. Step 2 — agreement through volume 3 forces $N_3(A) = N_3(B)$

Apply Theorem SNG-F56 with $g = 3$, $d = 3$, $\lambda = 0$. The girth
hypothesis is vacuous at $g = 3$ (every graph has girth $\ge 3$ in the
chapter's convention that the first possible cycle has length 3), so for
any two cubic graphs on $n$ vertices,

$$
[x^3]\bigl(L_A - L_B\bigr)
= \bigl(N_3(A) - N_3(B)\bigr)\, q^{3}(1-q^2)^{3}.
$$

(Indeed, at volume 3 the only connected supports that can distinguish
two cubic graphs are triangles: Proposition SNG-I008 gives the explicit
volume-$\le 3$ coefficients in terms of $n$, $d$, $m$, and $N_3$.) The
agreement hypothesis makes the left side zero, hence

$$
N_3(A) = N_3(B).
$$

Conversely, equal $N_3$ (with equal $n$) implies agreement through
volume 3, so the hypothesis "agree through volume 3" in the conjecture
is exactly "equal triangle counts", as observed in all samples.

## 4. Step 3 — connected supports of size at most 4 and their polynomials

By SNG-F55,
$[x^4]\ell_G = \sum_{S \text{ connected}} [x^4]\Phi_S$, and
$\Phi_S = O(x^{|S|})$, so only $|S| \le 4$ contributes.

### 4.1 Supports of size at most 3

Their contributions depend only on the type counts, which are functions
of $(n, N_3)$ alone:

* $|S| = 1$: one type, $K_1$; count $n$.
* $|S| = 2$: one connected type, $K_2$; count $m = 3n/2$.
* $|S| = 3$: two connected types, $P_3$ and $K_3$. Counting wedges
  (paths of length 2) in a cubic graph gives
  $W = \sum_v \binom{3}{2} = 3n$. Each $P_3$-inducing 3-set contains
  exactly one wedge and each triangle exactly three, so the number of
  $P_3$-inducing 3-sets is $3n - 3N_3$ and the number of $K_3$ sets is
  $N_3$.

Hence
$\sum_{|S|\le 3} [x^4]\Phi_S
= n\varphi_{K_1} + m\varphi_{K_2} + (3n - 3N_3)\varphi_{P_3}
+ N_3\varphi_{K_3}$,
a universal function of $(n, N_3)$. By §3 it is identical for $A$ and
$B$. This disposes, in particular, of all *triangle supports*: their
volume-4 shadow is already fixed by the volume-3 datum $N_3$.

### 4.2 Supports of size 4: the multilinear coefficient

For $|S| = 4$, $\Phi_S = O(x^4)$ with all monomials supported exactly on
$S$, so $[x^4]\Phi_S$ is precisely the multilinear coefficient
$[\prod_{v\in S} x_v]\,\Phi_S$, which equals
$[\prod_{v\in S} x_v]\log Z_S$ (the terms $\log Z_T$, $T \subsetneq S$,
in $\Phi_S$ involve only variables in $T$). The cumulant expansion used
in the proof of SNG-F56 computes it: write $z_T$ for the multilinear
coefficient of $Z_S$ at $\prod_{v\in T}x_v$; a height with $h_v = 1$ on
$T$ and $0$ elsewhere has energy $\sum_{v\in T} w_v - 2e(T)$, so
$z_T = a^{|T|} q^{-2e(T)}$ where $e(T)$ is the number of edges inside
$T$. The exponential (subset-convolution) formula says
$[\prod_{v\in S}x_v]\log Z_S$ is the unique quantity $c_S$ with
$z_S = \sum_{\pi} \prod_{B \in \pi} c_B$ over set partitions $\pi$ of
$S$. The same identity is satisfied by
$c_T = a^{|T|}\sum_{E'} f^{|E'|}$, summed over *connected spanning* edge
sets $E'$ of $G[T]$: an arbitrary spanning edge set splits uniquely into
connected components, giving
$\sum_\pi \prod_{B\in\pi} c_B
= a^{|S|}\sum_{E'} f^{|E'|}
= a^{|S|}(1+f)^{e(S)} = a^{|S|}q^{-2e(S)} = z_S$.
Therefore

$$
[x^4]\Phi_S \;=\; a^{4}\, P(G[S]),
\qquad
P(H) := \sum_{\substack{E' \subseteq E(H)\\ E' \text{ spanning, connected}}}
f^{|E'|}.
$$

### 4.3 Enumeration of the connected types on 4 vertices

There are exactly **six** connected graphs on four vertices. This is
classical, and it is also brute-force verified in `verify_proof.py` (§A):
all $2^6 = 64$ labelled graphs on 4 vertices were enumerated, the 38
connected ones grouped by isomorphism type, giving labelled counts
$P_4 : 12$, $K_{1,3} : 4$, $C_4 : 3$, paw $: 12$, diamond $: 6$,
$K_4 : 1$ ($12+4+3+12+6+1 = 38$). For each type, $P(H)$ was computed by
brute force over spanning edge subsets (§B) and is easily checked by
hand:

| type $H$ | edges | spanning connected $E'$ | $P(H)$ |
|---|---|---|---|
| $P_4$ (path) | 3 | only $H$ itself | $f^3$ |
| $K_{1,3}$ (star) | 3 | only $H$ itself | $f^3$ |
| $C_4$ (square) | 4 | 4 spanning trees, $H$ itself | $4f^3 + f^4$ |
| paw (triangle + pendant) | 4 | pendant edge forced, 3 choices of 2 triangle edges; $H$ itself | $3f^3 + f^4$ |
| diamond ($K_4$ minus edge) | 5 | 8 spanning trees, all five 4-edge subsets, $H$ itself | $8f^3 + 5f^4 + f^5$ |
| $K_4$ | 6 | 16 spanning trees, all fifteen 4-edge subsets, 6 five-edge subsets, $H$ itself | $16f^3 + 15f^4 + 6f^5 + f^6$ |

(The spanning-tree counts are the classical ones: $\tau(C_4) = 4$,
$\tau(\text{diamond}) = 8$, $\tau(K_4) = 16$. Every 4-edge subset of
$K_4$ is connected — a disconnected spanning subgraph on 4 vertices has
at most 3 edges — and every 4-edge subset of the diamond is connected,
including the rim $C_4$ obtained by deleting the shared edge.)

So with $s_\tau(G)$ = the number of 4-subsets of $V(G)$ inducing type
$\tau$,

$$
\sum_{|S| = 4} [x^4]\Phi_S
= a^4 \sum_\tau s_\tau(G)\, P(\tau).
$$

## 5. Step 4 — moment identities: everything except squares, diamonds, $K_4$ is universal

Induced-subset counts $s_\tau$ individually depend on the graph (two
cubic graphs on $n$ vertices generally have different numbers of induced
$P_4$'s). What saves the formula is that the *weighted sum*
$\sum_\tau s_\tau P(\tau)$ decomposes into a universal part plus the
three target counts. Define, for a 4-vertex graph $H$, the functionals

* $u_0(H) = 1$,
* $u_1(H) = e(H)$ (edges),
* $u_2(H) = \binom{e(H)}{2}$ (edge pairs),
* $u_3(H) =$ number of triangles in $H$,
* $u_5(H) =$ number of pairs $(T, e)$ with $T$ a triangle of $H$ and $e$
  an edge of $H$ outside $T$ but incident to $T$ (paw incidences),
* $t(H) = \mathrm{sq}(H) + f\,\mathrm{dia}(H) + f^2\,\mathrm{k4}(H)$,
  where $\mathrm{sq}$, $\mathrm{dia}$, $\mathrm{k4}$ count 4-cycle,
  diamond, and $K_4$ *subgraphs* of $H$.

Their values on the six types (brute-force verified, §C):

| type | $u_1$ | $u_2$ | $u_3$ | $u_5$ | $\mathrm{sq}$ | $\mathrm{dia}$ | $\mathrm{k4}$ |
|---|---|---|---|---|---|---|---|
| $P_4$ | 3 | 3 | 0 | 0 | 0 | 0 | 0 |
| $K_{1,3}$ | 3 | 3 | 0 | 0 | 0 | 0 | 0 |
| $C_4$ | 4 | 6 | 0 | 0 | 1 | 0 | 0 |
| paw | 4 | 6 | 1 | 1 | 0 | 0 | 0 |
| diamond | 5 | 10 | 2 | 4 | 1 | 1 | 0 |
| $K_4$ | 6 | 15 | 4 | 12 | 3 | 6 | 1 |

**Lemma 1 (pointwise decomposition).** With
$r_0 = (1, 1, 4, 3, 8, 16)$ on
$(P_4, K_{1,3}, C_4, \mathrm{paw}, \mathrm{diamond}, K_4)$,

$$
P(H) \;=\; f^3 r_0(H) \;+\; f^4 u_5(H) \;+\; f^4 t(H)
\qquad \text{for every connected 4-vertex } H,
$$

and
$r_0 = 4u_0 - 3u_1 + 2u_2 - \tfrac32 u_3 + \tfrac12 u_5$ as functions on
the six types.

*Check.* $C_4$: $f^3\cdot 4 + f^4\cdot 0 + f^4\cdot 1 = 4f^3 + f^4$. ✓
Paw: $3f^3 + f^4 + 0$. ✓ Diamond:
$8f^3 + 4f^4 + f^4(1 + f) = 8f^3 + 5f^4 + f^5$. ✓ $K_4$:
$16f^3 + 12f^4 + f^4(3 + 6f + f^2) = 16f^3 + 15f^4 + 6f^5 + f^6$. ✓
Trees: $r_0 = 1$, $u_5 = t = 0$. ✓ And $r_0$ from the functionals, e.g.
diamond: $4 - 15 + 20 - 3 + 2 = 8$; $K_4$: $4 - 18 + 30 - 6 + 6 = 16$; all
six are verified symbolically in `verify_proof.py` (§D). ∎

**Lemma 2 (the functional sums are universal).** For every cubic graph
$G$ on $n$ vertices,

$$
\sum_S u_0 = \tbinom{n}{4},\quad
\sum_S u_1 = m\tbinom{n-2}{2},\quad
\sum_S u_2 = 3n(n-3) + \Bigl(\tbinom{m}{2} - 3n\Bigr),\quad
\sum_S u_3 = N_3 (n-3),\quad
\sum_S u_5 = 3N_3,
$$

$$
\sum_S \mathrm{sq}(G[S]) = N_4,\qquad
\sum_S \mathrm{dia}(G[S]) = N_{\mathrm{dia}},\qquad
\sum_S \mathrm{k4}(G[S]) = N_{K_4},
$$

where all sums run over 4-subsets $S$ and $m = 3n/2$.

*Proof.* Each identity is a double count. $u_0$: trivial. $u_1$: each
edge lies in $\binom{n-2}{2}$ four-subsets. $u_2$: each pair of edges
sharing a vertex (there are $\sum_v \binom{3}{2} = 3n$ such pairs, the
wedges) spans 3 vertices, hence lies in $n - 3$ four-subsets; each
disjoint pair ($\binom{m}{2} - 3n$ of them) spans 4 vertices, hence lies
in exactly one. $u_3$: each triangle lies in $n - 3$ four-subsets.
$u_5$: a pair $(T, e)$ with $T$ a triangle and $e$ an edge incident to
$T$ but not in $T$ spans exactly 4 vertices, so it is counted for
exactly one $S$; and in a cubic graph each triangle has exactly 3 such
edges — one at each vertex, since each vertex of $T$ already uses two of
its three stubs inside $T$ — giving $3N_3$ pairs in total. Finally, a
4-cycle subgraph, a diamond subgraph, or a $K_4$ subgraph has exactly 4
vertices, so it appears inside $G[S]$ for exactly one $S$ (namely its
own vertex set), and the sums recover the global counts; note
$\mathrm{dia}(H)$ counts pairs of triangles of $H$ sharing an edge, so
$\sum_S \mathrm{dia}(G[S])$ counts each global diamond once. ∎

**Assembly.** Combining §4.1, §4.2, Lemma 1 and Lemma 2,

$$
[x^4]\ell_G \;=\; U(n, N_3) \;+\; a^4 f^4\,
\Bigl( N_4 + f N_{\mathrm{dia}} + f^2 N_{K_4} \Bigr),
$$

where $U(n, N_3)$ collects the size-$\le 3$ supports, the $f^3 r_0$ part
(a fixed rational combination of the universal sums of
$u_0, u_1, u_2, u_3, u_5$), and the $f^4 u_5$ part $a^4 f^4 \cdot 3N_3$ —
all functions of $(n, N_3)$ only. Since $a^4 f^4 = \kappa^4$, taking the
difference between $A$ and $B$ (same $n$, same $N_3$ by §3) kills $U$
and leaves

$$
\Delta \ell_4
= \Delta N_4\, \kappa^4 + \Delta N_{\mathrm{dia}}\, \kappa^4 f
  + \Delta N_{K_4}\, \kappa^4 f^2
= \Delta N_4\, q^4(1-q^2)^4 + \Delta N_{\mathrm{dia}}\, q^2(1-q^2)^5
  + \Delta N_{K_4}\, (1-q^2)^6 .
$$

By §2, $\Delta L_4 = \Delta \ell_4$. This is the three-term formula of
the Result. ∎ (modulo §6 for dropping the last term)

**Why paths, stars, and the other trees cancel.** $P_4$ and $K_{1,3}$
have $P = f^3$ exactly — a tree has a unique spanning connected edge
set, itself — and after Lemma 1 their whole contribution is inside the
$f^3 r_0$ term, which Lemma 2 shows is a function of $(n, N_3)$ alone.
It is *not* claimed that two cubic graphs have the same number of
induced paths or stars (they do not); the claim is that the specific
combination in which all six types' $f^3$-parts enter is universal. The
same applies to the $f^4$ part of the paw: it is absorbed by $u_5 = 3N_3$.

**Consistency with the repository.** The assembled formula for
$[x^4]\log F_\lambda$ is exactly the $g = 3$, $R = 4$ case of Theorem
SNG-F61 (normalised combination $N_4 + fN_{\mathrm{diamond}} + f^2
N_{K_4}$ with prefactor $\kappa^4$), and the $K_4$ coefficient agrees with
the chapter's rook-versus-Shrikhande check (both 6-regular: the
difference is $8 q^{12}(1-q^2)^6 = \kappa^4 f^2 \Delta N_{K_4}$ with
$\kappa = q^{d-2}(1-q^2)$ at $d=6$). The present proof makes the cubic,
$\lambda = 0$ case fully explicit for $L$ itself rather than only for the
normalised log series.

## 6. Step 5 — the $K_4$ term

A $K_4$ subgraph of a cubic graph saturates the degree of all four of
its vertices, so it is a union of connected components — in fact a whole
component $K_4$. Hence a **connected** cubic graph on $n > 4$ vertices
has $N_{K_4} = 0$, and the third term vanishes, proving the conjectured
formula as stated. For $n = 4$ the only connected cubic graph is $K_4$
itself, so there is nothing to compare. Disconnected cubic graphs can
have $N_{K_4} > 0$, and then the third term is genuinely needed: §8
exhibits $A = K_4 \sqcup K_{3,3}$ versus a connected stored graph with
the same $N_3 = 4$, agreeing through volume 3, whose volume-4 difference
is the two-term prediction **plus exactly** $(1-q^2)^6$.

## 7. What the proof does and does not use

The proof uses only: SNG-F55 (support locality and type-dependence),
the cumulant computation already present in the proof of SNG-F56,
SNG-F56 at $g = 3$, the classification of connected graphs on four
vertices, and elementary double counting in cubic graphs. No girth
assumption is made anywhere: triangles are fully allowed, which is
exactly why the paw support contributes the extra incidence functional
$u_5$ and why the diamond — two triangles sharing an edge, i.e. the
unique multicyclic 4-vertex type below $K_4$ — appears with the extra
factor $f = q^{-2}-1$, turning $q^4(1-q^2)^4$ into $q^2(1-q^2)^5$.

## 8. Verification against the stored computational data

`verify_proof.py` (stdlib only, exact integer/rational arithmetic,
independent height-series enumerator and independent counters for
$N_3, N_4, N_{\mathrm{dia}}, N_{K_4}$) checks, and `verify_results.json`
records:

* **Enumeration (§A–C).** All 64 labelled graphs on 4 vertices: exactly
  the six claimed connected types with labelled counts
  $12, 4, 3, 12, 6, 1$; the polynomials $P(\tau)$ and all functional
  values of the table in §5 reproduced by brute force.
* **Identities (§D–E).** Lemma 1 pointwise on all six types; the
  Bell identity of §2 on exp-consistent rational series, including
  $\Delta L_4 = \Delta \ell_4$ when $\ell_1, \ell_2, \ell_3$ agree.
* **Stored data at $n = 10$ and $n = 12$** (all named + sampled
  records of `singularity_extension.json`, 303 and 153 graphs):
  recomputed counts match the stored $N_3, N_4, N_{\mathrm{dia}}$ for
  every graph; over all pairs, agreement through volume 3 holds iff
  $N_3$ agrees (0 exceptions); the proved formula holds for **all
  10,971 agreeing pairs at $n=10$ and all 3,234 at $n=12$ (0
  failures)**, matching the stored tallies exactly, while the
  squares-only formula fails for exactly the stored numbers of
  agreeing pairs (1,144 at $n=10$; 410 at $n=12$).
* **Stored counterexamples.** All 10 stored counterexample pairs at
  each of $n=10$ and $n=12$ were recomputed from their stored edge
  lists: the stored volume-4 differences are reproduced exactly, the
  squares-only prediction differs, and the corrected formula holds.
  Example ($n=10$, `n10_g1` vs `n10_g46`, both $N_3 = 2$): actual
  difference $\{q^2: -1, q^4: 1, q^6: 6, q^8: -14, q^{10}: 11,
  q^{12}: -3\}$ — the $q^2$ term is impossible for any multiple of
  $q^4(1-q^2)^4$ — and it equals
  $-4\cdot q^4(1-q^2)^4 \;-\; 1\cdot q^2(1-q^2)^5$ with
  $\Delta N_4 = 2 - 6$ and $\Delta N_{\mathrm{dia}} = 0 - 1$.
* **$n = 8$.** Cube versus Möbius ladder recomputed directly
  ($\Delta = 2q^4(1-q^2)^4$, $N_{\mathrm{dia}}$ equal); the sampled
  pool (60 graphs, seed 20261024, edge lists regenerated with the
  original sampler, all checks recomputed here) gives 1,891 pairs,
  555 agreeing, 0 formula failures. Together with $n=10,12$ this is
  $555 + 10{,}971 + 3{,}234 = 14{,}760$ agreeing pairs, matching the
  conjecture's evidence base exactly.
* **Disconnected $K_4$ test (§G).** $K_4 \sqcup K_{3,3}$ versus the
  stored graph `n10_g3` (both $N_3 = 4$): they agree through volume 3,
  the three-term formula holds, and the two-term formula is off by
  exactly $(1-q^2)^6 = \{1, -6, 15, -20, 15, -6, 1\}$ at
  $q^0, q^2, \dots, q^{12}$, confirming both the necessity and the
  exact form of the $K_4$ term outside the connected class.

Run it with `python3 verify_proof.py` (about 5 seconds); the console
log of the run reported here is `verify_log.txt`.

---

## STATUS

**Proved (complete, no remaining lemma).** The three-term formula above
for arbitrary cubic $A, B$ on $n$ vertices agreeing through volume 3,
and hence the conjectured two-term formula for connected cubic graphs
on $n > 4$ vertices. The proof is self-contained modulo the repository's
own Theorems SNG-F55 and SNG-F56, whose connected-support/cumulant
method it follows; the only external inputs are those two repo results.

**Computation-dependent (finite, exact, replayable).** Three finite
steps are discharged by `verify_proof.py` rather than by hand: (i) the
enumeration of connected graphs on 4 vertices and of their spanning
connected edge sets (also verified by hand above — classical spanning
tree counts $4, 8, 16$ and the "at most 3 edges" argument for $K_4$'s
4-edge subsets); (ii) the pointwise polynomial identity of Lemma 1 and
the rational identity for $r_0$ on the six types (also checked by hand
in §5); (iii) the Bell-polynomial identity of §2 on rational test
series (a standard identity, included for completeness). None of these
is statistical: each is an exact finite check that the script performs
with integer/Fraction arithmetic, and each is small enough to audit by
hand from the tables printed in §4–§5. The verification against the
stored data (§8) is evidence *for the conjecture's dataset*, not a step
of the proof.

**Still open.** Nothing within the stated task. Natural continuations
outside its scope: the analogous volume-5 analysis (where SNG-F61
predicts the first bicycle corrections, e.g. $K_{2,3}$ at $b_4 = 5$ for
girth-4 graphs and theta/diamond-chain terms for cubic graphs with
triangles), and a Lean or independently reviewed formalisation of
SNG-F55/F56 themselves, which this proof takes as given from the
repository.
