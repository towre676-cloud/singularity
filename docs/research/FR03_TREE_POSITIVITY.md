# FR03 — Ordered tree kernels, positivity, and path witnesses

**Status.** Proved project specialization with exact finite checks. The Gaussian total-positivity mechanism and Cauchy–Binet composition are classical linear algebra; the contribution here is their precise application to this project's height kernel, the resulting path-distance coefficient, the all-order leading-minor hierarchy, and the truncation counterexample. This companion neither implements NX36 nor changes its proposed acceptance units.

## 1. Which object is positive?

Let $T=(V,E)$ be a finite connected tree, let $a,b\in V$ be distinct ordered terminals, and let $0<x,q<1$. Pin their heights to $s,t\in\mathbb Z_{\ge0}$. The ordered kernel is

\[
K_T(s,t;x,q)=
\sum_{h\in\mathbb Z_{\ge0}^{V\setminus\{a,b\}}}
 x^{\sum_{v\ne a,b}h_v}
 q^{\sum_{uv\in E}(h_u-h_v)^2},\qquad h_a=s,\ h_b=t.
\]

The terminals receive no factor of $x$. The kernel retains original labeled interior assignments. It is not a quotient by automorphisms. Every summand is nonnegative, and

\[
0<K_T(s,t;x,q)\le (1-x)^{-(|V|-2)}.
\]

The right side follows by dropping every energy factor, which is at most one. This gives absolute convergence without a height cutoff. For $H\ge0$, write $K_T^{[H]}$ when every interior vertex independently has height in $\{0,\ldots,H\}$. This is a Cartesian height box. It is a different object from keeping only profiles whose **sum** of interior heights is at most $R$.

A kernel is strictly totally positive when, for every $k\ge1$ and every pair of strictly increasing nonnegative integer pin lists $s_1<\cdots<s_k$ and $t_1<\cdots<t_k$,

\[
\det\bigl(K_T(s_i,t_j;x,q)\bigr)_{i,j=1}^k>0.
\]

The two pin lists need not be equal. The matrix need not be symmetric: a tree with an asymmetric terminal placement generally has $K_T(s,t)\ne K_T(t,s)$.

## 2. Gaussian edges are strictly totally positive

For one edge put

\[
G(r,c)=q^{(r-c)^2}
      =q^{r^2+c^2}\bigl(q^{-2r}\bigr)^c.
\]

For increasing rows $r_1<\cdots<r_k$, the numbers $z_i=q^{-2r_i}$ are strictly increasing and positive. Removing positive row and column factors reduces a Gaussian minor to

\[
\det(z_i^{c_j})_{i,j=1}^k,
\qquad 0<z_1<\cdots<z_k,\quad 0\le c_1<\cdots<c_k.
\]

Here is a direct proof of positivity, so the result does not depend on a numerical minor test. A nonzero real polynomial with $k$ nonzero monomials has at most $k-1$ distinct positive zeros. To see this, divide by its lowest power of $z$; differentiation removes its constant term and leaves at most $k-1$ monomials. Rolle's theorem and induction give the claim. If the displayed evaluation determinant vanished, a nonzero linear combination of its columns would give a polynomial with at most $k$ monomials and $k$ distinct positive zeros, a contradiction.

The determinant therefore never vanishes in the connected region of increasing positive nodes. Its sign is constant there. To determine that sign, bring the nodes together near $1$, writing $z_i=1+\varepsilon u_i$ with increasing $u_i$. Taylor expansion gives the first nonzero term

\[
\varepsilon^{k(k-1)/2}
\frac{\prod_{i<j}(u_j-u_i)\prod_{i<j}(c_j-c_i)}
     {\prod_{m=0}^{k-1}m!},
\]

which is positive. Thus every ordered Gaussian minor is positive.

This proof needs distinct row and column indices. Repeated pins give a zero determinant, as they should. Reversing one pin order changes the determinant sign and does not contradict positivity.

## 3. The tree factorization and the full positivity theorem

Let $p_0=a,p_1,\ldots,p_d=b$ be the unique terminal path, so $d\ge1$ is terminal distance. Delete its path edges. Every remaining component meets the path at exactly one vertex. Integrate the heights in these off-path components first. At each path vertex $p_i$, this produces a strictly positive branch factor $B_i(h)$. Internal path vertices additionally carry their factor $x^h$; the terminal vertices do not.

For a common finite box the factorization is

\[
K_T^{[H]}(s,t)=B_0^{[H]}(s)
\bigl[G D_1^{[H]}G D_2^{[H]}\cdots
G D_{d-1}^{[H]}G\bigr]_{s,t}
B_d^{[H]}(t),
\]

where each intermediate Gaussian index ranges from $0$ to $H$, and

\[
D_i^{[H]}(h,h)=x^h B_i^{[H]}(h)>0.
\]

When the terminals are adjacent, the bracket is simply $G(s,t)$. Positive endpoint factors preserve signs of all minors. Cauchy–Binet expands every minor of a product as a sum of products of minors, and every term in this expansion is positive whenever the intermediate index sets have the required size.

**Theorem FR03-A (box and full strict positivity).** If $d\ge2$, every ordered minor of $K_T^{[H]}$ of size $k\le H+1$ is strictly positive. If $k>H+1$, its rank is at most $H+1$, so all such larger minors vanish. If $d=1$, the boxed kernel is strictly totally positive at every order because there is no intermediate path-index bottleneck. In all cases the complete analytic kernel $K_T$ is strictly totally positive at every finite order.

For the last statement, the entries of $K_T^{[H]}$ increase to those of $K_T$, and convergence of entries gives convergence of each finite determinant. A limit of positive determinants need only be nonnegative in general, so one additional argument is essential. Fix the intermediate index set $\{0,\ldots,k-1\}$ at every internal path vertex in one Cauchy–Binet term. For every $H\ge k-1$, that term is present. Its branch factors have strictly positive lower bounds obtained by assigning zero to all off-path interior heights. Its Gaussian minors and powers of $x$ are fixed and strictly positive. This single term supplies a uniform positive lower bound for the full determinant. Its limit is therefore strictly positive.

This is a structural necessary condition for ordered tree kernels. It is not a sufficient characterization of trees, and this note does not classify all matrices satisfying it.

## 4. The first determinant coefficient measures terminal geometry

Write

\[
c=\sum_{v\in\{p_0,\ldots,p_d\}}\deg_T(v)-2d.
\]

Each of the $d$ path edges contributes twice to the degree sum. Thus $c\ge0$ counts precisely the edges leaving the terminal path. It counts attachment edges, not all edges deeper inside the pendant branches.

For $k\ge1$, take the principal pin minor

\[
\Delta_k(x,q)=\det\bigl(K_T(i,j;x,q)\bigr)_{i,j=0}^{k-1},
\quad S_k=\frac{k(k-1)}2,
\quad Q_k=\frac{k(k-1)(2k-1)}6.
\]

**Theorem FR03-B (all-order leading-minor hierarchy).** The exact first term is

\[
\boxed{
\Delta_k(x,q)=
x^{(d-1)S_k}q^{cQ_k}
\left[\prod_{r=1}^{k-1}(1-q^{2r})^{k-r}\right]^d
+O\!\left(x^{(d-1)S_k+1}\right).
}
\]

The coefficient in the box is strictly positive for every real $q\in(0,1)$. Consequently the displayed volume is an exact first nonzero degree, not just a lower bound.

To prove this, apply exterior Cauchy–Binet to the path factorization as a formal series in $x$. Every internal index set of size $k$ consists of distinct nonnegative integers and has sum at least $S_k$. Equality holds for the unique set $I=\{0,\ldots,k-1\}$. There are $d-1$ internal path vertices, so the first possible degree is $(d-1)S_k$, and at that degree there is one choice at every vertex. All off-path interior heights must be zero at this first degree. A branch edge incident to a path vertex of pin height $i$ then contributes $q^{i^2}$; multiplying over the selected indices and attachment edges yields $q^{cQ_k}$.

The remaining factor is one Gaussian principal minor per path edge. Its determinant is explicit:

\[
\det(q^{(i-j)^2})_{i,j=0}^{k-1}
=\prod_{r=1}^{k-1}(1-q^{2r})^{k-r}.
\]

Indeed, extract $q^{i^2}$ from each row and $q^{j^2}$ from each column, then use the ordinary Vandermonde determinant on $q^{-2i}$. The negative powers contributed by the Vandermonde cancel the extracted powers exactly. This proves the formula.

The formal Cauchy–Binet argument is legitimate coefficient by coefficient: to compute through a fixed degree $R$, any interior height above $R$ is irrelevant. One can therefore first use a finite box $H\ge R$, prove the finite identity, and extract the desired coefficient.

The order-two case is particularly readable:

\[
\boxed{
K_T(0,0)K_T(1,1)-K_T(0,1)K_T(1,0)
=x^{d-1}q^c(1-q^2)^d+O(x^d).
}
\]

Thus the first nonzero volume recovers $d$. Once $d$ is known, dividing the leading coefficient by $(1-q^2)^d$ gives $q^c$, which uniquely determines the nonnegative integer $c$ at any fixed $q\in(0,1)$. This recovers terminal distance and the number of branches incident to the terminal path. It does not recover the shapes of those branches or the entire tree.

| Minor order | First nonzero volume | Leading coefficient |
|---|---:|---|
| $k=1$ | $0$ | $1$ |
| $k=2$ | $d-1$ | $q^c(1-q^2)^d$ |
| $k=3$ | $3(d-1)$ | $q^{5c}[(1-q^2)^2(1-q^4)]^d$ |
| $k=4$ | $6(d-1)$ | $q^{14c}[(1-q^2)^3(1-q^4)^2(1-q^6)]^d$ |

The higher minors provide redundant structural consistency checks rather than independent reconstruction of additional path statistics at leading order. Their later coefficients can contain branch information; that inverse problem is left open.

## 5. A volume cutoff can manufacture a negative determinant

Consider the four-vertex path $a-u-v-b$. Retain only interior profiles $h_u+h_v\le1$. The resulting polynomial kernel is

\[
K_{\le1}(s,t)=q^{s^2+t^2}
\bigl[1+xq^2(q^{-2s}+q^{-2t})\bigr].
\]

Its determinant on pins $0,1$ is

\[
\boxed{\det(K_{\le1}(s,t))_{s,t=0,1}
=-x^2q^2(1-q^2)^2<0.}
\]

This is an actual tree, so a negative determinant of a volume-truncated kernel cannot reject tree realizability. The cutoff couples $u$ and $v$; it is not a product domain and does not retain the matrix-product factorization used in the positivity proof.

There is no contradiction with the leading-minor theorem. The true tree has $d=3,c=0$, and its full determinant starts with

\[
x^2(1-q^2)^3.
\]

Computing a determinant coefficient at degree two requires each entry through degree two. Entry data only through degree one determine determinant coefficients through degree one; degree-two terms obtained by taking their ordinary determinant can be wrong because omitted degree-two entries multiply nonzero constant entries.

| Available object | Valid conclusion |
|---|---|
| Complete ordered analytic kernel, $0<x,q<1$ | All ordered finite minors are positive |
| Common interior height box $0,\ldots,H$ | Positive minors through order $H+1$; larger minors vanish if there is an internal path vertex |
| Ordered kernel entry coefficients through volume $R$ | Determinant coefficients are valid only through volume $R$ |
| Ordinary determinant of a volume-truncated kernel evaluated at $x>0$ | No general positivity guarantee |
| Symmetrized interface $K(s,t)+K(t,s)$ | This note establishes no total-positivity rule for it |

## 6. Implementation and exact evidence

`src/singularity/tree_positivity.py` provides an exact rational box evaluator. It integrates off-path subtrees by iterative messages and contracts the unique terminal path. Rational $x,q$ must lie strictly between zero and one; floats and booleans are rejected. A conservative preflight scalar-summand budget prevents silently launching a large box contraction. This budget is not a bound on integer bit complexity: very large pin heights or rational denominators can still make individual arithmetic operations expensive.

The structural helpers return the terminal path, distance, off-path attachment count and exact first minor coefficient. The order-$k$ helper has an explicit declared work bound of $k\le256$. It does not compute an infinite sum or pretend that the formula determines later coefficients.

The tests compare the box evaluator with direct enumeration over every interior assignment, including asymmetric terminals, terminal pins above the interior box, and nontrivial pendant branches. Ordered minors of sizes one, two and three are evaluated exactly. Independent weak-composition enumeration checks the distance coefficient on every terminal pair of every labeled tree through four vertices. Additional tests check higher leading minors at orders three and four and the negative volume-cutoff example.

The retained receipt extends the order-two leading-term check to all labeled trees through five vertices and all unordered terminal pairs, with the ordering fixed by the original labels. It records the exact finite population and does not interpret it as a proof for arbitrary trees; the proof above supplies that theorem. No graph census or surviving symmetric-ambiguity search is performed.

## 7. What this contributes to the remaining frontier

These results add a nonlinear necessary condition and a geometry decoder for an important class of realizable **ordered** interfaces. They can accompany a future candidate search by filtering an ordered tree completion, provided that the data include enough volume and the test respects the stated kernel semantics. They cannot directly eliminate a candidate living only in a symmetrized interface: averaging a matrix with its transpose does not follow from the path factorization, and no preservation theorem for that averaging is proved here.

The natural next problems are to decode pendant-branch statistics from subsequent determinant coefficients, understand which analogous sign constraints survive on unicyclic graphs, and determine which ordered positivity constraints descend to symmetrized data under additional terminal symmetries. None of these is counted as an implemented NX36 unit, a full-series collision, or a complete reconstruction theorem for arbitrary pinned graphs.
