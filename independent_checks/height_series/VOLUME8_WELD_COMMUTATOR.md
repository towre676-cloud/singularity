# Weld rings and the ordering commutator

The eighth height observation distinguishes two connected cubic graphs
built from exactly the same four units. Their first seven observations
agree, and every individual connected leafless pattern on at most seven
vertices has the same count. The distinction is the order in which the
units are welded together. This gives both a compact exact witness for
the eighth-order law and an all-order method for constructing further
witnesses.

## Two-port units and their exact transfer kernels

A **two-port unit** is a finite simple connected graph with two distinct
specified vertices of degree two, called its left and right ports; every
other vertex has degree three. For units $U_1,\ldots,U_m$, take disjoint
copies and add an edge from the right port of $U_i$ to the left port of
$U_{i+1}$, with indices cyclically interpreted. For $m\ge2$ this produces
a simple connected cubic graph, denoted $\mathcal R(U_1\cdots U_m)$.
The two joining edges in a two-unit ring have different endpoints because
the ports within each unit are distinct.

For a cubic graph $G$, its height series is

$$
L_G(x,q)=\sum_{h:V(G)\to\mathbb Z_{\ge0}}
 x^{\sum_v h_v}q^{\sum_{uv\in E(G)}(h_u-h_v)^2}.
$$

Since every vertex has degree three, the exponent can also be written

$$
3\sum_v h_v^2-2\sum_{uv\in E(G)}h_uh_v.
$$

For a unit $U$ with ports $\lambda,\rho$, define the matrix kernel

$$
F_U(a,b;x,q)=
\sum_{\substack{h:V(U)\to\mathbb Z_{\ge0}\\h_\lambda=a,\ h_\rho=b}}
 x^{\sum_vh_v}
 q^{3\sum_vh_v^2-2\sum_{uv\in E(U)}h_uh_v},
\qquad a,b\ge0.
$$

A weld between heights $b$ and $c$ contributes the factor
$J(b,c)=q^{-2bc}$. Put $T_U=F_UJ$. The vertex-square terms are already
included in $F_U$, so this weld factor completes the cubic energy without
counting a vertex weight twice.

**Transfer theorem.** For every ring of two-port units,

$$
L_{\mathcal R(U_1\cdots U_m)}(x,q)
 =\mathrm{tr}(T_{U_1}\cdots T_{U_m}).
$$

Here the trace has a precise finite meaning at every requested volume.
Fix $R$ and work over
$\mathbb Q[q,q^{-1}][x]/(x^{R+1})$. Restrict every port height to
$0,\ldots,R$, enumerate internal unit assignments of total height at
most $R$, and form the resulting $(R+1)\times(R+1)$ matrices. Any
assignment with any port or internal height exceeding $R$ has total
height greater than $R$, so no omitted assignment can contribute.
Consequently these finite matrices compute the full graph series through
volume $R$, with no limiting or convergence assumption.

To prove the theorem, expand the trace and the finite matrix products.
The summed indices give precisely the left and right port heights in
every unit, including the cyclic closing weld. The internal summations
then give each global height assignment once. Its $x$ exponent is its
total height, and its $q$ exponent is the cubic energy displayed above.
This establishes the identity coefficient by coefficient for every $R$.

## The all-order commutator identity

Let $A,D$ be any two two-port units. Apply the transfer theorem to the
rings $AADD$ and $ADAD$. For every finite volume truncation, cyclicity
of trace over the commutative coefficient ring gives

$$
\begin{aligned}
\mathrm{tr}([T_A,T_D]^2)
 &=\mathrm{tr}(T_AT_DT_AT_D)
   -\mathrm{tr}(T_AT_D^2T_A)\\
 &\quad-\mathrm{tr}(T_DT_A^2T_D)
   +\mathrm{tr}(T_DT_AT_DT_A)\\
 &=2\mathrm{tr}(T_AT_DT_AT_D)
   -2\mathrm{tr}(T_A^2T_D^2).
\end{aligned}
$$

Thus the exact formal-series identity is

$$
\boxed{
L_{\mathcal R(ADAD)}-L_{\mathcal R(AADD)}
 =\tfrac12\mathrm{tr}([T_A,T_D]^2).
}
$$

The matrices in this expression are the finite matrices at whichever
order is being computed. The right-hand coefficient is independent of
any larger truncation, so the identities for all $R$ assemble into the
stated formal-series identity. Symmetry or commutativity of the unit
matrices is not required. The factor one-half is legitimate over the
rational coefficient ring, and the trace difference shows directly that
the resulting height coefficients are integers.

The identity separates unit content from unit order. If the transfer
matrices commute, these two ring orders have the same entire height
series. Whenever the commutator-square trace is nonzero, its first nonzero
coefficient identifies the first observation that can distinguish their
order. This
provides a reusable construction at arbitrary volume rather than a
search restricted to one finite graph pool.

## An explicit twenty-vertex eighth-order witness

Take $A$ to be the triangular prism with one spoke deleted. The following
labelling specifies it completely:

$$
V(A)=\{0,1,2,3,4,5\},\qquad
E(A)=\{01,03,05,12,15,23,24,34\},
$$

with left port $4$ and right port $5$. Take $D$ to be a diamond:

$$
V(D)=\{0,1,2,3\},\qquad
E(D)=\{01,02,03,12,13\},
$$

with left port $2$ and right port $3$. In both units the named ports
have degree two and every other vertex has degree three.

Define

$$
G=\mathcal R(AADD),\qquad H=\mathcal R(ADAD).
$$

Both graphs are simple, connected and cubic, with $20$ vertices and
$30$ edges. Their exact difference is

$$
[x^r](L_H-L_G)=0\qquad(0\le r\le7),
$$

and

$$
\boxed{
[x^8](L_H-L_G)
 =-q^2(1-q^2)^9(1+2q^2)^2
 =-\kappa^8f(f+3)^2,
}
$$

where $\kappa=q(1-q^2)$ and $f=q^{-2}-1$. The expanded polynomial
is meaningful also at $q=0$; the abbreviations involving $f$ are
Laurent identities.

In integer coefficients, the eighth difference is

$$
-q^2+5q^4-4q^6-24q^8+66q^{10}-42q^{12}-84q^{14}
 +204q^{16}-201q^{18}+109q^{20}-32q^{22}+4q^{24}.
$$

This factor is nonzero and is negative for every real $0<q<1$.
Thus the eighth observation separates these graphs throughout that
physical parameter interval, even though all seven earlier observation
polynomials agree identically.

## Identification of the eighth motifs

Exact connected-subgraph enumeration shows that every connected
leafless pattern on at most seven vertices has the same count in $G$
and $H$. The only nonzero differences among eight-vertex leafless
patterns are as follows. Masks use the decreasing-degree canonical
convention of `vol8_lib.py`; each mask is completely determined by its
integer and the fixed lexicographic ordering of the pairs $ij$, $i<j$.

| Eight-vertex pattern mask | Edge count | $N_Y(H)-N_Y(G)$ |
|---|---:|---:|
| 365424 | 9 | -4 |
| 984673 | 9 | -1 |
| 5321176 | 10 | -4 |
| 5375716 | 9 | -4 |
| 5600337 | 11 | -1 |
| 12693829 | 10 | -2 |

The mask-to-edge table is supplied by the certificate; the grouped
contributions are

$$
\Delta S_9=-9,\qquad \Delta S_{10}=-6,\qquad
\Delta S_{11}=-1,
$$

where $S_e$ sums the connected leafless eight-vertex pattern counts
with $e$ edges. These grouped counts give
$-\kappa^8(9f+6f^2+f^3)$, exactly the direct height calculation.
The mask-specific edge counts in the table are verified against
`vol8_lib.py` when generating the certificate.

## Exact replay

Run:

```bash
python independent_checks/height_series/vol8_weld.py --replay
```

The replay reconstructs the two graphs from their units, verifies
cubicity, computes every coefficient through eight using the two-port
transfer algorithm, and independently enumerates every global weak
height composition at every volume from one to eight. These global
calculations use only the original edge lists and squared edge
differences; they do not use the correction law, cumulants or leaf
reduction. At each volume the sum of the height multiplicities is also
checked against $\binom{20+r-1}{r}$. Finally it recounts the leafless
patterns and checks the saved exact certificate `vol8_weld.json`.

The transfer theorem and commutator identity above hold at all orders.
The displayed leading coefficient and motif census are finite exact
claims discharged by the replayable calculations.
