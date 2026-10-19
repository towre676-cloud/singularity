# FR01: exact connected pole divisors and a controlled reconstruction sector

This companion result concerns the complete local series at one fixed real
parameter, not a finite-prefix extrapolation. It is independent of the NX36
implementation programme. It strengthens the existing entire-normalization
theorem SNG-F39: for a connected graph, every possible root-of-unity pole is
actually present. It also gives a rigorous, explicitly restricted sector in
which poles recover the component-size population.

The new results are proved below in ordinary mathematical prose. The Python
module implements rational bounds, finite cyclotomic Gaussian enclosures, and
the combinatorial inversion. No proof-assistant formalization is claimed.

## 1. Objects and the question left by entire normalization

Let G be a finite simple graph on n vertices, let 0<q<1, and write

\[
 E_G(a)=\sum_{uv\in E(G)}(a_u-a_v)^2,
 \qquad
 L_G(x,q)=\sum_{a\in\mathbb Z_{\ge0}^n}x^{\sum_v a_v}q^{E_G(a)}.
\]

For a connected graph, common translation partitions the original labeled
height population into disjoint infinite rays. The representative of a ray
has minimum zero. Consequently

\[
 L_G(x,q)=\frac{B_G(x,q)}{1-x^n},\qquad
 B_G(x,q)=\sum_{\substack{a\ge0\\\min a=0}}
                x^{\sum a_v}q^{E_G(a)}.
\]

SNG-F39 proves that B_G is entire in x. This proves only that the poles of
L_G are *among* the nth roots of unity. A numerator zero could in principle
remove a denominator zero. The present first theorem rules this out exactly
at the roots belonging to the connected component itself.

## 2. The connected noncancellation theorem

**Theorem FR01.1.** For every connected n-vertex graph and every fixed
0<q<1, B_G(zeta,q) is a strictly positive real number whenever zeta^n=1.
Thus L_G has a simple pole at every nth root of unity and no other poles.
More precisely,

\[
 \lim_{r\uparrow1}(1-r)L_G(r\zeta,q)
       =\frac{B_G(\zeta,q)}{n}>0,
 \qquad
 \operatorname{Res}_{x=\zeta}L_G(x,q)
       =-\frac{\zeta}{n}B_G(\zeta,q).
\]

The adjective positive concerns B_G and the displayed radial normalization;
the complex residue itself need not be positive real.

**Proof.** Choose a root vertex 0. Every height class modulo common integer
translation has a unique anchored representative z with z_0=0 and
(z_1,...,z_{n-1}) in Z^(n-1). Its minimum-zero representative is
a=z-(min z)1. Therefore

\[
 E_G(a)=E_G(z),\qquad
 \sum a_v=\sum_{v\ne0}z_v-n\min z.
\]

The last term disappears from the phase at zeta^n=1. If Q is the reduced
Laplacian obtained by deleting row and column 0, then

\[
 B_G(\zeta,q)
    =\sum_{z\in\mathbb Z^{n-1}}
       q^{z^TQz}\zeta^{\mathbf1^Tz}.
\]

Connectedness makes Q positive definite: a vector of zero energy is constant
on every edge, hence constant on the connected graph, and anchoring forces
that constant to be zero. In particular this Gaussian series converges
absolutely. Write s=-log q>0 and zeta=exp(2*pi*i*k/n), and set
alpha=(k/n)1. Gaussian Fourier transform and Poisson summation give

\[
 \boxed{
 B_G(\zeta,q)=
 \frac{\pi^{(n-1)/2}}{s^{(n-1)/2}\sqrt{\det Q}}
 \sum_{m\in\mathbb Z^{n-1}}
 \exp\!\left[-\frac{\pi^2}{s}
 (m-\alpha)^TQ^{-1}(m-\alpha)\right].}
\]

Every summand on the right is a strictly positive real number, and the sum
converges. Hence B_G(zeta,q)>0. Since 1-x^n has a simple zero at zeta,
the quotient has exactly the claimed simple pole. The radial formula follows
from (1-r^n)/(1-r)->n; the residue follows from the derivative -n*zeta^(n-1).
For n=1, Q has dimension zero, B_G=1 and L_G=1/(1-x), so the same result
holds directly. This completes all cases. QED.

**Why the argument is specific.** The phase is a character of the quotient
height lattice only when zeta^n=1. At an unrelated unit-circle point, the
factor zeta^(-n min z) remains. Dropping that factor would turn a proof for
the graph's own denominator roots into a false proof for every root of unity.

**Consequence FR01.2.** The full fixed-q local series determines whether G
is connected. For a connected graph it determines its vertex count from
the complete set of poles. This does not determine the connected graph's
isomorphism type. Full-series equality of two connected graphs forces equal
orders, but the connected fixed-q completeness problem remains open.

## 3. Disconnected products and the cancellation obstruction

Let G have connected components H_1,...,H_c with sizes n_i. Independence of
the original assignments gives

\[
 L_G(x,q)=\prod_{i=1}^c L_{H_i}(x,q)
         =\frac{\prod_i B_{H_i}(x,q)}{\prod_i(1-x^{n_i})}.
\]

At x=1, every numerator is positive by Theorem FR01.1. Therefore the pole
order at 1 is exactly c, with no additional hypothesis. In particular a
disconnected graph has pole order at least two there, proving the first
assertion of Consequence FR01.2.

At a primitive dth root zeta, components with d dividing n_i each have a
simple pole. But a component with d not dividing n_i has no denominator
pole there and its entire numerator has not been proved nonzero there.
Such an analytic factor could cancel a pole of a different component.
Thus the tempting general assertion

\[
 \operatorname{poleord}_{\zeta}L_G
 \stackrel{?}{=}\#\{i:d\mid n_i\}
\]

is **not** an unconditional result of the connected theorem. This package
neither exhibits such a cancellation nor proves that it cannot occur.
Unknown cancellation is kept explicit in the API.

At a given zeta the exact signed order, with zeros counted negatively, is

\[
 \sum_{i:d\mid n_i}1
  -\sum_{i:d\nmid n_i}\operatorname{ord}_{\zeta} B_{H_i}.
\]

The second sum is the precise missing datum. A finite numerical sample
showing it to be zero cannot establish an all-graph noncancellation theorem.

## 4. A uniform zero-free sector from a spanning tree

Define the scalar Gaussian theta value

\[
 \vartheta(q)=\sum_{k\in\mathbb Z}q^{k^2}
            =1+2\sum_{k\ge1}q^{k^2}.
\]

**Lemma FR01.3.** If H is connected on m vertices, then

\[
 B_H(1,q)\le\vartheta(q)^{m-1}.
\]

**Proof.** Choose a spanning tree T and orient it away from a root. The
integer differences on its m-1 edges are independent integer coordinates
on the anchored height lattice. Tree energy is the sum of their squares.
Every extra graph edge adds a nonnegative square. As 0<q<1,
q^(E_H)<=q^(E_T) term by term. Summing over the tree coordinates factors
the upper bound into m-1 copies of vartheta. For m=1 it is the identity
1<=1. QED.

Since the normalized series has constant term 1 and nonnegative real
coefficients, for every |x|<=1,

\[
 |B_H(x,q)-1|\le B_H(1,q)-1
                   \le\vartheta(q)^{m-1}-1.
\]

**Theorem FR01.4.** Fix an integer N>=1. If

\[
 \boxed{\vartheta(q)^{N-1}<2,}
\]

then the numerator of every connected graph of size at most N is zero-free
on the entire closed unit disk. Consequently, for any graph whose component
sizes are at most N, the primitive-d root pole order is exactly

\[
 p_d=\sum_{k\ge1}b_{kd},
\]

where b_m is the number of m-vertex components. This is a sufficient
small-q sector, not an assertion that zeros appear outside that sector.

The strict inequality matters: an enclosure reaching 2 does not give the
strict distance from zero used by the triangle inequality.

For a simple explicit sufficient inequality, k^2>=k gives

\[
 \vartheta(q)\le\frac{1+q}{1-q},\qquad
 \left(\frac{1+q}{1-q}\right)^{N-1}<2.
\]

For implementation we use a much sharper rational enclosure. For K>=0,

\[
 \vartheta(q)\le U_K(q):=
 1+2\sum_{k=1}^Kq^{k^2}
 +\frac{2q^{(K+1)^2}}{1-q^{2K+3}}.
\]

Indeed each successive exponent increment in the omitted tail is at least
2K+3. Exact rational comparison of U_K(q)^(N-1) with 2 certifies the
condition. At q=1/16 the implementation certifies all components of size
at most six. At q=1/2 the bound fails already for size two; this refusal
does not contradict the unconditional connected theorem at q=1/2.

## 5. Inverting the component-size population

Assume the full profile p_1,...,p_N has been justified, for example by
Theorem FR01.4. Descending inversion gives

\[
 \boxed{b_m=p_m-\sum_{k\ge2}b_{km},\qquad m=N,N-1,\ldots,1.}
\]

Equivalently, with the classical integer Mobius function,

\[
 b_m=\sum_{k\ge1}\mu(k)p_{km}.
\]

These sums are finite because no component exceeds N. For the component
population (1,1,2,3,3,6), the profile is
(p_1,...,p_6)=(6,2,3,0,0,1), and inversion returns exactly two isolated
vertices, one size-two component, two size-three components, and one
size-six component. No multiplicity is divided by an automorphism count.

**Corollary FR01.5.** On cluster graphs (disjoint unions of complete graphs)
whose largest component has size at most N, the complete fixed-q local
series is a complete isomorphism invariant whenever the small-q hypothesis
of Theorem FR01.4 holds. The proof recovers b_m from the divisor; these
multiplicities determine the graph because a complete component of each
size has only one isomorphism type.

For general graphs the same result recovers component sizes only, not the
isomorphism types of their connected components. There is no claim that a
finite coefficient prefix reveals the poles or provides a completeness
cutoff. The theorem uses the full analytic function determined by the series.

## 6. An unconditional all-q class

Suppose every nontrivial component has the same size m>=2, with any number
of isolated vertices. At every denominator root of a nontrivial component,
all nontrivial components satisfy zeta^m=1 and hence have positive normalized
numerators. Isolated factors 1/(1-x) never vanish. Thus the divisor formula
p_d=sum_{d|n_i}1 is valid for this class at every 0<q<1.

In particular the complete fixed-q local series distinguishes every graph

\[
 kK_m\;\sqcup\;\ell K_1
 \quad(k\ge1,\ m\ge2,\ \ell\ge0)
\]

from every other graph in that class. The largest primitive pole order is
m; its multiplicity is k; the pole order at 1 is k+ell. Purely isolated
graphs are handled separately by (1-x)^(-ell). This is an infinite class
of disconnected interiors beyond the cycle-union reconstruction family,
but its result concerns the unpinned local series specified here.

## 7. Generic parameters in a fixed finite family

For a fixed connected H and a fixed unit root zeta, B_H(zeta,q) is
holomorphic in |q|<1. Uniform absolute convergence on compact subdisks
follows by domination by B_H(1,|q|) and the Gaussian lattice bound.
Its value at q=0 is 1, since connected zero-energy normalized profiles
contain only the all-zero assignment. Therefore it is not identically
zero and its zeros are locally discrete.

For any fixed finite graph family, there are only finitely many components
and relevant roots. Outside a locally discrete exceptional set of q in
(0,1), every off-denominator cancellation is absent and the divisor
inversion is valid. On every compact subinterval strictly inside (0,1)
the exceptional set is finite. This does not locate it, certify q=1/2,
or exclude rational exceptional values. No such arithmetic strengthening
is claimed.

## 8. Exact finite Gaussian enclosures

`anchored_gaussian_box` uses integer differences r_e on a rooted spanning
tree, rather than bounding the heights themselves. It sums exactly over
|r_e|<=H in the cyclotomic ring Q[zeta]. There are
(2H+1)^(n-1) profiles, checked against a budget before enumeration.

Let theta_H=1+2 sum_{k=1}^H q^(k^2). As E_G>=sum_e r_e^2, the absolute
mass outside this difference box is bounded by

\[
 \vartheta(q)^{n-1}-\vartheta_H(q)^{n-1}
 \le U_K(q)^{n-1}-\vartheta_H(q)^{n-1},\qquad K\ge H.
\]

This gives a rational absolute complex-error radius around the exact
cyclotomic partial sum. Different spanning-tree boxes need not sum the
same finite populations; their certified balls nevertheless contain the
same full theta value. Tests exercise this root-choice failure mode.
For K_2, the character at -1 reduces independently to
sum_{z=-H}^H (-1)^z q^(z^2), and at q=1/2,H=4 the enclosure already
proves strict positivity by rational arithmetic. A triangle at a primitive
third root is checked independently in direct rooted height coordinates.

The finite Gaussian calculation is evidence and an evaluable bound. The
all-graph noncancellation theorem follows from Poisson positivity, not from
checking many boxes or observing positive floating-point approximations.

## 9. Scope relative to the main frontiers

The series A_H(x,q)=sum_a x^(sum a) q^(E_H(a)+2 sum a_v^2), used by
dominating-terminal pinning, has an absolute quadratic pinning term. It
is entire in x and does not have the translation denominator 1-x^n.
Therefore this pole theorem does not prove completeness for the fixed-pinned
A_H series. It provides a separate invariant for unpinned L_H and a
controlled class where full-series reconstruction is proved.

The work does not realize a symmetric-interface null vector, settle
fixed-pinning completeness, extend a finite-prefix cutoff, or duplicate
NX36's proposed parameter-observability and ideal-closure projects.
The surviving questions remain explicit: unit-circle zeros of arbitrary
off-denominator numerators; effective localization of their q exceptions;
full-series collisions in connected graphs; and reconstruction under
quadratic pinning. These are logical next problems, not completed claims.

## 10. Reproduction

From the repository root:

```sh
PYTHONPATH=src python -m unittest tests/test_pole_divisors.py -v
PYTHONPATH=src python scripts/fr01_pole_divisors.py --check
```

The retained JSON records exact rational certificates and bounded Gaussian
examples. Its profile inversion assumes the analytic hypotheses stated
in each record; the inverter alone cannot validate supplied analytic data.
