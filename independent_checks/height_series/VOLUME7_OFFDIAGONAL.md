# The first off-diagonal connected-subgraph coefficient

Let $G$ be a finite simple cubic graph and let

$$L_G(x,q)=\sum_{h:V(G)\to\mathbb Z_{\ge0}}x^{\sum_vh_v}
q^{\sum_{uv\in E(G)}(h_u-h_v)^2}.$$

For a connected simple subcubic pattern $H$, write $k=|V(H)|$,
$e=|E(H)|$, $d_H(v)=\deg_H(v)$, and let $c_v$ be the number of
connected components of $H-v$. Set $c_v=0$ when $H$ has one vertex.
As throughout this contribution, $N_H(G)$ counts ordinary, possibly
non-induced subgraphs. There are universal formal series $B_H(x,q)$ with

$$\log L_G(x,q)=\sum_{H\text{ connected}}N_H(G)B_H(x,q),$$

where only patterns with at most $r$ vertices contribute to $[x^r]$.
The connected-support vertex inversion followed by edge inversion defines
these series without any fitting or assumption on the host graph.

**Theorem.** Put $f=q^{-2}-1$. For every connected simple subcubic $H$,

$$[x^r]B_H=0\quad(r<k),\qquad [x^k]B_H=q^{3k}f^e,$$

and

$$\boxed{[x^{k+1}]B_H
=q^{3k+9}f^e\sum_{v\in V(H)}(f+2)^{d_H(v)}
-q^{3k+3}f^e\sum_{v\in V(H)}2^{c_v-1}.}$$

The formula concerns the coefficient before the cubic leaf-reduction
identities are applied. It is an all-order identity, rather than an
interpolation of the volume-seven tables.

## Proof

Use the cubic energy identity

$$\sum_{uv\in E(G)}(h_u-h_v)^2
=3\sum_vh_v^2-2\sum_{uv\in E(G)}h_uh_v.$$

Introduce a separate activity variable at each occupied site. Expanding
each interaction as $q^{-2h_uh_v}=1+(q^{-2h_uh_v}-1)$ and then expanding
the logarithm gives the usual connected graph expansion. Alternatively,
this expansion follows directly by multiplying the formal identity
$\log(1+u)=\sum_{j\ge1}(-1)^{j+1}u^j/j$ and grouping its terms by their
occupied vertices and selected interaction edges. Each fixed volume has
only finitely many terms, so this rearrangement is formal and exact.

To make the repeated-site bookkeeping explicit, view an occupied site as
a particle carrying a positive integer height. Particles at distinct sites
have interaction $q^{-2hh'}-1$; two particles assigned the same site have
interaction $-1$, enforcing the rule that a site carries one height.
The exponential graph expansion with the $1/j!$ particle factor reproduces
the original partition series: all configurations with a repeated site
cancel when their optional same-site interaction is summed. Taking the
logarithm retains connected particle graphs.

At least one unit of volume is needed at each of the $k$ sites of $H$.
At volume $k$ there is exactly one height-one particle at each site. Edge
inversion selects every edge of $H$, giving $q^{3k}f^e$.

At volume $k+1$ there are precisely two possibilities.

First, one site $v$ carries height two and every other site carries height
one. The site weights multiply to $q^{12+3(k-1)}=q^{3k+9}$.
Every incident edge at $v$ has interaction

$$q^{-4}-1=(q^{-2}-1)(q^{-2}+1)=f(f+2);$$

the other edges have interaction $f$. Summing over $v$ gives the first
term of the theorem.

Second, one site $v$ is represented twice by height-one particles, with
all other sites represented once. The site weights multiply to
$q^{3(k+1)}$. Distinguish the two copies temporarily. Edge inversion
requires each original edge incident to $v$ to appear at one or both
copies, while every edge of $H-v$ is fixed. The interaction edge between
the copies has weight $-1$.

If the graph obtained without the copy-to-copy edge already connects the
two copies, its connected contribution cancels against the same graph
with that edge added. In particular every assignment using both copies
for one original incident edge cancels. The surviving assignments have
each original edge at exactly one copy and have the two copies in
different components before that edge is added. This happens exactly
when all edges from any one component of $H-v$ are assigned to the same
copy: a component touching both would connect them. Because $H$ is
connected, every component of $H-v$ touches $v$. There are therefore
$2^{c_v}$ surviving assignments. Each contributes $-f^e$, and division
by the $2!$ for the two identical copies gives
$-2^{c_v-1}q^{3k+3}f^e$. Summing over $v$ proves the formula. The same
argument includes $k=1$, where it gives the familiar singleton term
$q^{12}-q^6/2$.

## Consequences for the volume-seven calculation

For a two-connected $H$ with $k\ge2$, every $c_v=1$. The second sum is
then $k$. If $H$ also has minimum degree two and maximum degree three,
its degree multiset is determined by $k$ and $e$. Thus all such
two-connected patterns of a given size and edge count share the first
off-diagonal coefficient.

Articulations are detected by the correction
$\sum_v2^{c_v-1}$. For example, the three six-vertex theta patterns and
the six-vertex barbell all have degree multiset $(3,3,2,2,2,2)$ and seven
edges. The theta patterns have articulation sum $6$, while the barbell
has sum $8$. Their raw volume-seven coefficients differ by
$-2q^{21}f^7$. These raw contributions must still be combined with the
seven-vertex leaf-extension terms. The full cubic reduction and quotient
by the coefficients through volume six perform exactly that combination;
the final conditional correction is stated in `VOLUME7_PROOF.md`.

The theorem supplies an explicit first off-diagonal row at every order.
Only the degree multiset and the component counts after one vertex is
deleted are needed. It therefore replaces repeated symbolic cumulant
expansion for the entire support-size-$r-1$ part of coefficient $r$.
The same proof applies to every finite simple $d$-regular host: replace
$q^{3k}$, $q^{3k+9}$, and $q^{3k+3}$ by $q^{dk}$,
$q^{d(k+3)}$, and $q^{d(k+1)}$, respectively. The interaction variable
$f=q^{-2}-1$ and the articulation sum are unchanged.

## Independent exact replay

`python vol7_independent_check.py` verifies the formula against the full
edge-inverted cumulant calculation for every connected subcubic pattern
on one through six vertices. The same checker recomputes all 113
connected-support kernels through seven vertices using Boolean vertex
inversion and the power-series definition of the logarithm, independently
checks all edge-inverted coefficient tables, and verifies direct graph
height coefficients against injective-embedding pattern counts.
