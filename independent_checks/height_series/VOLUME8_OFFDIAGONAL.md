# Two layers beyond the connected-support diagonal

The volume-eight calculation admits a closed formula for its entire
six-vertex-support contribution. More generally, the first two
off-diagonals of the connected-pattern expansion can be computed at
every order from vertex degrees and one- and two-vertex deletions.

Let $G$ be a finite simple $d$-regular graph, and set

$$L_G(x,q)=\sum_{h:V(G)\to\mathbb Z_{\ge0}}x^{\sum_vh_v}
q^{\sum_{uv\in E(G)}(h_u-h_v)^2}.$$

Write $N_H(G)$ for ordinary, possibly non-induced, subgraph counts. The
universal connected-pattern kernels $B_H$ are defined by the exact
identity

$$\log L_G=\sum_{H\text{ connected}}N_H(G)B_H.$$

Vertex inversion followed by edge inversion gives these kernels
uniquely. Fix a connected simple pattern $H$ with $k$ vertices and $e$
edges, and write $d_v=\deg_H(v)$. All statements below are formal
identities in $x$ with Laurent-polynomial coefficients in $q$.

## A partition formula at arbitrary volume

The energy identity

$$\sum_{uv\in E(G)}(h_u-h_v)^2
=d\sum_vh_v^2-2\sum_{uv\in E(G)}h_uh_v$$

allows an occupied site to be treated as a particle of positive height
$h$, with activity $x^hq^{dh^2}$. Two particles at distinct adjacent
sites interact with weight $q^{-2hh'}-1$. Two particles assigned the
same site interact with weight $-1$, which enforces single occupation
when all optional same-site edges are summed.

For each vertex $v$ of $H$, choose a positive particle multiplicity
$m_v$ and give its particles distinct temporary labels. Let $P_v$ be
this label set and let $P$ be their disjoint union. Assign a positive
height $h_p$ to each $p\in P$, with total height $r$. A partition
$\pi$ of $P$ is admissible when each block contains at most one
particle from each $P_v$. Put

$$W_{uv}(\pi,h)=\sum_{C\in\pi}
\sum_{p\in C\cap P_u}\sum_{s\in C\cap P_v}h_ph_s,$$

and $\mu(\pi)=(-1)^{|\pi|-1}(|\pi|-1)!$. Then

$$\boxed{[x^r]B_H
=\sum_{\substack{m_v\ge1,\ h_p\ge1\\\sum_ph_p=r}}
\frac{q^{d\sum_ph_p^2}}{\prod_vm_v!}
\sum_{\pi\text{ admissible}}\mu(\pi)
\prod_{uv\in E(H)}\big(q^{-2W_{uv}(\pi,h)}-1\big).}$$

This is a finite all-order formula. It can be evaluated by the partition
lattice recurrence, or by classifying the excess volume $r-k$ as below.

**Proof.** Expanding $\log(1+u)$ gives the partition coefficient
$\mu(\pi)$ for connected particle graphs. Summing optional edges
within a block gives the product of the corresponding full interaction
factors. A block containing two particles from the same site has the
factor $1-1=0$, leaving exactly the admissible partitions. Edge inversion
over the original edges of $H$ then factorises: the contribution from an
edge $uv$ is its within-block Boltzmann factor minus one, namely
$q^{-2W_{uv}}-1$. The factors $m_v!$ remove the temporary particle
labels at each site. Requiring $m_v\ge1$ performs the vertex-support
inversion. Each fixed $r$ has finitely many particles, heights and
partitions, so every rearrangement is exact. This also proves the
vanishing $[x^r]B_H=0$ for $r<k$.

At $r=k$, every site has one height-one particle. Since $H$ is
connected, a nonzero partition contribution requires all particles in
one block. Hence $[x^k]B_H=q^{dk}(q^{-2}-1)^e$.

## The second off-diagonal theorem

Set

$$z=q^{-2},\qquad f=z-1,\qquad a=z+1,\qquad b=z^2+z+1.$$

For each vertex $v$, let $\mathcal C_v$ be the connected components of
$H-v$, let $c_v=|\mathcal C_v|$, and let

$$b_v(C)=|\{vw\in E(H):w\in C\}|.$$

For an unordered vertex pair $u,v$, let $\varepsilon_{uv}$ indicate
whether $uv$ is an edge. Let $c_{uv}$ be the number of components of
$H-\{u,v\}$, and let $s_{uv}$ count those components whose vertices
have neighbours in exactly one of $u,v$. Empty graphs have zero
components; products over no components equal one.

Define four explicit polynomials:

$$U_3=\sum_v b^{d_v},$$

$$U_{22}=\sum_{u<v}a^{d_u+d_v-\varepsilon_{uv}}
(z^2+1)^{\varepsilon_{uv}},$$

$$M=\sum_v\left[
\prod_{C\in\mathcal C_v}\big(1+a^{b_v(C)}\big)
+2^{c_v-1}\sum_{u\ne v}a^{d_u}\right],$$

$$D=\sum_v3^{c_v-1}
+\sum_{u<v}\left(2^{s_{uv}+1}
-2^{c_{uv}-1}a^{\varepsilon_{uv}}\right).$$

**Theorem.** For every such $H$,

$$\boxed{[x^{k+2}]B_H=f^e\left[
q^{d(k+8)}U_3+q^{d(k+6)}U_{22}
-q^{d(k+4)}M+q^{d(k+2)}D\right].}$$

In the cubic case, the four powers of $q$ are $3k+24$, $3k+18$,
$3k+12$, and $3k+6$. The identity is implemented directly in
`vol8_offdiagonal.py`; it does not call a cumulant enumerator.

## Proof by excess-volume classes

The positive heights and particle multiplicities in the partition
formula have total excess two. There are five possible classes.

**One height-three site.** There is one particle at each site, with one
height three. The site activity is $q^{d(k+8)}$. Each edge incident to
the exceptional vertex has weight

$$q^{-6}-1=f(z^2+z+1)=fb,$$

and every other edge has weight $f$. Summing over the exceptional
vertex gives $f^eq^{d(k+8)}U_3$.

**Two height-two sites.** The site activity is $q^{d(k+6)}$. An edge
incident to exactly one exceptional site has weight $fa$. An edge
joining them has weight

$$q^{-8}-1=f(z+1)(z^2+1).$$

For the pair $u,v$, this gives the factor
$f^ea^{d_u+d_v-\varepsilon_{uv}}(z^2+1)^{\varepsilon_{uv}}$.
Summation gives $f^eq^{d(k+6)}U_{22}$.

**A duplicated site and one height-two particle.** There are two
subcases, both with site activity $q^{d(k+4)}$. Duplicating a site
creates two particle blocks, whose partition coefficient is $-1$.
Every component of $H-v$ lies wholly in one of those blocks.

If the two particles at $v$ have heights one and two, the temporary
label permutations cancel the $2!$ denominator. For a component $C$,
assigning it to the height-one particle gives boundary factor
$f^{b_v(C)}$, while assigning it to the height-two particle gives
$f^{b_v(C)}a^{b_v(C)}$. This produces
$-f^e\prod_C(1+a^{b_v(C)})$.

If both particles at $v$ have height one and a different vertex $u$
has height two, the component assignments give $2^{c_v}$ choices and
the two identical particles give denominator $2!$. All edges incident
to $u$ acquire the same additional factor $a$, independently of these
choices. This produces $-f^e2^{c_v-1}a^{d_u}$. The two subcases sum
to $-f^eq^{d(k+4)}M$.

**One site represented three times.** All particles have height one,
so the site activity is $q^{d(k+2)}$. The three copies occupy three
different blocks. Their partition coefficient is $2$; each component
of $H-v$ chooses one of the three blocks; division by $3!$ gives
$3^{c_v-1}$. Summing over $v$ gives the first part of $D$.

**Two sites each represented twice.** Again all heights are one and
the site activity is $q^{d(k+2)}$. Divide by $2!2!=4$. Admissible
partitions of the four copies have two, three, or four blocks.

With two blocks, the copies of $u$ and $v$ are paired in two possible
matchings. Every component of $H-\{u,v\}$ chooses one of the two
blocks. The partition coefficient is $-1$. If $uv$ is an edge, it
appears in both blocks, giving $q^{-4}-1=fa$ in place of $f$.
The total is therefore $-f^e2^{c_{uv}-1}a^{\varepsilon_{uv}}$.

With three blocks, exactly one $u$-copy is paired with one $v$-copy;
there are four choices. A component touching both $u$ and $v$ must
join that paired block. Each one-sided component chooses either of
the two blocks containing a copy of the vertex it touches. The
partition coefficient is $2$, so the total after division by four is
$f^e2^{s_{uv}+1}$.

Four blocks make no contribution. If $uv$ is an edge, its edge factor
is zero because no block contains both sites. If $uv$ is absent,
connectedness of $H$ forces a component of $H-\{u,v\}$ to touch both
vertices, and that component cannot be assigned to any block. These
two surviving cases give the pair sum in $D$ and finish the proof.

## Verification and use

`vol8_independent_check.py` compares this expression against the full
edge-inverted cumulant calculation for every connected subcubic pattern
on one through six vertices. It checks the first off-diagonal expression
on one through seven vertices. Its support kernels are recomputed by
Boolean vertex inversion and the power-series definition of the
logarithm, and its edge transform uses raw edge subsets rather than
isomorphism-grouped subtraction.

At volume eight, the top eight-vertex row is the diagonal
$q^{24}f^e$; the seven-vertex row follows from the first off-diagonal
theorem; the six-vertex row follows from the theorem above. Only
supports of size at most five require a further off-diagonal expansion.
At volume $r$, the same identities provide the support-size $r$,
$r-1$, and $r-2$ rows. The partition formula supplies the exact
recurrence for the remaining rows.
