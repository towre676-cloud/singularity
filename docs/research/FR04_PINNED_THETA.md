# FR04 — What the far coefficients remember under fixed positive pinning

**Companion status:** proved necessary invariants and exact small-instance
certificates. This document does not prove completeness of fixed pinning and
does not exhibit a full-series collision. It is independent of the NX36
implementation packets. The graph may be connected or disconnected; positive
pinning makes the quadratic form coercive in either case.

## 1. The question and the change of scale

Let \(G\) be a finite simple graph with \(n\ge1\) labeled vertices, let
\(\lambda\) be a fixed positive integer, and fix \(0<q<1\). Write

\[
 A_{G,R}^{(\lambda)}(q)
 =\sum_{\substack{h\in\mathbb Z_{\ge0}^{n}\\\sum_i h_i=R}}
 q^{E_G(h)+\lambda\sum_i h_i^2},
 \qquad
 E_G(h)=\sum_{\{u,v\}\in E(G)}(h_u-h_v)^2.
\]

For the dominating-terminal interface already used in the project, the
relevant pinning is \(\lambda=2\). These are coefficients of the raw
nonnegative-height series. No minimum-height normalization is applied and no
multiplicity is divided by an automorphism-group order.

A large volume forces a large common mean height. The pinning alone charges
approximately \(\lambda R^2/n\) for that mean, while graph energy is unchanged
by common translation. Consequently the original coefficients become very
small even when their fluctuations retain substantial structure. The right
object is the rescaled coefficient

\[
 S_{G,R}(q)=q^{-\lambda R^2/n}A_{G,R}^{(\lambda)}(q).
\]

The rescaled sequence does not ordinarily have a single limit. There are
\(n\) residue classes, because an integer height vector cannot be translated
by a nonintegral common height. Each residue class has its own affine lattice
of fluctuations, its own limiting theta value, and an explicit boundary error.

| Object | Definition | Information retained |
|---|---|---|
| Pinned coefficient | \(A_{G,R}^{(\lambda)}(q)\) | All nonnegative profiles at one volume |
| Gaussian scale | \(q^{\lambda R^2/n}\) | Graph order when \(\lambda,q\) are known |
| Centered coefficient | \(S_{G,R}=q^{-\lambda R^2/n}A_{G,R}\) | Fluctuations subject to the nonnegative boundary |
| Affine lattice | \(\Lambda_r=\{z-r\mathbf1/n:z\in\mathbb Z^n,\sum z_i=r\}\) | Integer fluctuations for \(R\equiv r\pmod n\) |
| Theta limit | \(\Theta_{G,r}=\sum_{y\in\Lambda_r}q^{y^{\mathsf T}(L_G+\lambda I)y}\) | Necessary full-series invariant after the boundary recedes |
| Boundary deficit | \(\epsilon_{G,R}=\Theta_{G,r}-S_{G,R}\) | Positive information omitted by the limiting invariant |

## 2. Order is already an intrinsic full-series invariant

**Theorem FR04.1 (quadratic coefficient decay).** For every \(R\ge0\),

\[
 q^{\lambda R^2/n+|E(G)|+\lambda n/4}
 \le A_{G,R}^{(\lambda)}(q)
 \le \binom{R+n-1}{n-1}q^{\lambda R^2/n}.
 \tag{1}
\]

In particular,

\[
 \boxed{\displaystyle
 \lim_{R\to\infty}\frac{\log A_{G,R}^{(\lambda)}(q)}{R^2}
 =\frac{\lambda}{n}\log q.}
 \tag{2}
\]

Thus equality of the complete pinned series at the same known
\(\lambda>0\) and \(q\in(0,1)\) forces equal graph order.

**Proof.** Cauchy–Schwarz gives \(\sum_i h_i^2\ge R^2/n\), and graph energy is
nonnegative. Every summand is therefore at most \(q^{\lambda R^2/n}\).
There are exactly \(\binom{R+n-1}{n-1}\) labeled weak compositions of \(R\),
which proves the upper bound.

For the lower bound, put \(R=kn+r\), where \(0\le r<n\), and choose one
profile with \(r\) coordinates equal to \(k+1\) and the rest equal to \(k\).
Every edge contributes either zero or one, so its graph energy is at most
\(|E(G)|\). Its squared norm is

\[
 (n-r)k^2+r(k+1)^2
 =R^2/n+r(n-r)/n
 \le R^2/n+n/4.
\]

Its single positive summand proves the lower bound. Taking logarithms of
(1), dividing by \(R^2\), and using
\(\log\binom{R+n-1}{n-1}=O_n(\log R)\) proves (2). The number
\(\lambda\log q\) is nonzero, so its quotient by the limit determines \(n\).
This last statement is a full-series assertion. It does not supply a universal
finite-volume procedure for reading the limit from an arbitrary prefix. ∎

The theorem has a useful methodological consequence. A completeness question
formulated for the full pinned series need not assume graph order is externally
provided: the complete series contains it. An algorithm using only finitely
many coefficients must still declare how it knows or bounds the order.

## 3. The centered lattice and the exact boundary decomposition

Let \(L_G\) be the graph Laplacian and set

\[
 C_G=L_G+\lambda I.
\]

Since \(L_G\mathbf1=0\) and \(\lambda>0\),

\[
 C_G\mathbf1=\lambda\mathbf1,
 \qquad C_G\succeq\lambda I>0.
\]

For \(R=kn+r\), translate each profile by the integer common height \(k\):

\[
 z=h-k\mathbf1,
 \quad \sum_i z_i=r,
 \quad z_i\ge-k.
\]

Its centered version is

\[
 y=z-\frac r n\mathbf1=h-\frac Rn\mathbf1\in\Lambda_r.
\]

The cross term vanishes because \(\sum_i y_i=0\). Hence the exact identity is

\[
 \boxed{E_G(h)+\lambda\|h\|^2
 =\lambda R^2/n+y^{\mathsf T}C_Gy.}
 \tag{3}
\]

The nonnegative-height condition becomes a moving orthant boundary:

\[
 h_i\ge0\quad\Longleftrightarrow\quad y_i\ge-R/n.
\]

Define the complete affine-root-lattice theta value

\[
 \Theta_{G,r}^{(\lambda)}(q)
 =\sum_{y\in\Lambda_r}q^{y^{\mathsf T}C_Gy}.
 \tag{4}
\]

This is a scalar evaluated at the declared fixed parameter. It is not being
identified with the theta series as a formal function of \(q\). All sums
converge absolutely: positive definiteness bounds them by products of
one-dimensional Gaussian sums.

**Theorem FR04.2 (residue-class limits).** For \(R=kn+r\),

\[
 S_{G,R}(q)
 =\sum_{\substack{y\in\Lambda_r\\y_i\ge-R/n\ \forall i}}
 q^{y^{\mathsf T}C_Gy}
 \nearrow \Theta_{G,r}^{(\lambda)}(q)
 \qquad(k\to\infty).
 \tag{5}
\]

For \(n\ge2\) every increase \(R\mapsto R+n\) is strict. For \(n=1\), the
rescaled coefficients and the unique theta limit are identically one.
Furthermore,

\[
 \boxed{\Theta_{G,r}^{(\lambda)}(q)
 =\Theta_{G,n-r}^{(\lambda)}(q),\qquad 1\le r<n.}
 \tag{6}
\]

Consequently there are at most \(\lfloor n/2\rfloor+1\) distinct limiting
values after reflection.

**Proof.** Formula (3) gives (5) at every finite \(R\). Along one residue
class the affine lattice is fixed and the lower coordinate threshold drops
by one each time. The domains are nested and exhaust the entire lattice.
All summands are positive, so monotone convergence proves the limit. When
\(n\ge2\), there are lattice vectors with one coordinate exactly equal to
the newly admitted lower height, and the remaining coordinates can be chosen
to have the required sum. At least one positive summand is therefore added.
For \(n=1\), \(y=0\) is the only lattice vector.

Reflection \(y\mapsto-y\) preserves the quadratic form. If
\(y=z-r\mathbf1/n\), then

\[
 -y=(\mathbf1-z)-(n-r)\mathbf1/n,
 \quad \sum_i(1-z_i)=n-r.
\]

It maps \(\Lambda_r\) bijectively to \(\Lambda_{n-r}\), proving (6). ∎

## 4. A Gaussian error bound with all constants visible

Put

\[
 T_{n,r}(q)=\sum_{z\in\mathbb Z}q^{\lambda(z-r/n)^2},
 \qquad a_R=R/n+1.
\]

**Theorem FR04.3 (boundary correction).** With \(r=R\bmod n\),

\[
 0\le\epsilon_{G,R}
 :=\Theta_{G,r}^{(\lambda)}(q)-S_{G,R}(q)
 \le nT_{n,r}(q)^{n-1}
 \frac{q^{\lambda a_R^2}}
 {1-q^{\lambda(2a_R+1)}}.
 \tag{7}
\]

The error is identically zero for \(n=1\). For \(n\ge2\), it is positive at
every finite \(R\). The formula deliberately drops graph energy and the sum
constraint when bounding omitted vectors, so it is conservative.

**Proof.** An omitted vector has at least one coordinate
\(y_i<-R/n\). On the shifted integer lattice the first such value is exactly
\(-R/n-1\), followed by \(-R/n-2,\ldots\). Since
\(y^{\mathsf T}C_Gy\ge\lambda\sum_i y_i^2\), a union bound over the chosen
bad coordinate, followed by removal of the zero-sum constraint, gives

\[
 \epsilon_{G,R}
 \le nT_{n,r}(q)^{n-1}
 \sum_{m\ge0}q^{\lambda(a_R+m)^2}.
\]

Successive exponents differ by \(\lambda(2a_R+2m+1)\), which is at least
\(\lambda(2a_R+1)\). The tail is bounded by a geometric series with the
first term and largest successive ratio shown in (7). ∎

Combining the exact decomposition with positivity of the theta limit gives

\[
 A_{G,R}^{(\lambda)}(q)
 =q^{\lambda R^2/n}
 \left(\Theta_{G,r}^{(\lambda)}(q)-\epsilon_{G,R}\right),
 \tag{8}
\]

\[
 \log A_{G,R}^{(\lambda)}(q)
 =\frac{\lambda R^2}{n}\log q
 +\log\Theta_{G,r}^{(\lambda)}(q)+o(1)
 \quad(R\equiv r\pmod n).
 \tag{9}
\]

There is a quadratic scale, a bounded residue-dependent term, and a Gaussian
boundary correction. A further consequence along a residue class is

\[
 \frac{A_{G,R+n}^{(\lambda)}(q)}{A_{G,R}^{(\lambda)}(q)}
 q^{-\lambda(2R+n)}\longrightarrow1.
 \tag{10}
\]

These are asymptotic structural identities, not claims that finitely many
nearby coefficients certify full-series equality.

## 5. Exact arithmetic without pretending fractional powers are rational

Even for rational \(q\), the scaling factor \(q^{-\lambda R^2/n}\) need not
be rational. An implementation must not silently replace such algebraic
numbers by rounded floats and call the result an exact certificate.

The centered-theta APIs first choose a transparent exact sector:

\[
 t\in\mathbb Q\cap(0,1),\qquad q=t^{n^2}.
 \tag{11}
\]

Write \(w_i=nz_i-r\). The centered exponent is now

\[
 q^{y^{\mathsf T}C_Gy}
 =t^{\,n^2E_G(z)+\lambda\sum_i(nz_i-r)^2},
 \tag{12}
\]

an integer power of a rational number. Equivalently,

\[
 S_{G,R}(t^{n^2})
 =t^{-n\lambda R^2}A_{G,R}^{(\lambda)}(t^{n^2}).
\]

The exponent in each centered summand is nonnegative. Thus every finite sum,
interval endpoint, and error bound in the checker is an exact `Fraction`.
This arithmetic restriction belongs to these centered-theta APIs, while
Theorems FR04.1–FR04.3 hold for every real \(0<q<1\). The affine-lift APIs
below remove the restriction and work at every rational parameter.

For any positive integer \(b\), define the rational tail bound

\[
 U(b)=\frac{t^{\lambda b^2}}
 {1-t^{\lambda(2bn+n^2)}}
 \ge\sum_{m\ge0}t^{\lambda(b+nm)^2}.
 \tag{13}
\]

For a declared integer half-width \(H\ge0\), put

\[
 T^{\mathrm{up}}_{n,r,H}
 =\sum_{z=-H}^{H+1}t^{\lambda(nz-r)^2}
 +U(n(H+2)-r)+U(n(H+1)+r).
 \tag{14}
\]

This bounds the complete one-coordinate Gaussian. The asymmetric finite
window \([-H,H+1]\) is intentional: the reflection
\(z\mapsto1-z\) preserves it for the pair \(r,n-r\). In particular the two
finite theta lower sums agree exactly, not merely approximately.

Two independent enclosures are implemented:

| Route | Exact lower endpoint | Certified upper-minus-lower |
|---|---|---|
| One coefficient | \(S_{G,R}(t^{n^2})\) | \(n(T^{\mathrm{up}}_{n,r,H})^{n-1}U(R+n)\) |
| Lattice window | Sum (12) over \(\sum z_i=r\), \(-H\le z_i\le H+1\) | \(n(T^{\mathrm{up}}_{n,r,H})^{n-1}[U(n(H+2)-r)+U(n(H+1)+r)]\) |

The first route sums nonnegative profiles at one volume. The second sums
signed profiles in an affine lattice window. Their certified intervals must
overlap, and their finite sums come from different domains. The checker uses
this relation alongside an independent product-box coefficient oracle.

The window enumeration determines the last coordinate from the first
\(n-1\), so it visits at most \((2H+2)^{n-1}\) candidate prefixes. The
coefficient route visits \(\binom{R+n-1}{n-1}\) profiles. Both APIs reject a
request exceeding the caller's declared state budget before enumerating.
Neither route is advertised as a large-graph compiler.

### 5.1 Exact affine lifts at the working parameter \(q=1/2\)

A graph-independent change of coordinates also makes the complete calculation
rational at every rational \(q\in(0,1)\). Retain the residue-dependent scale
instead of extracting its fractional power. Define

\[
 \Psi_{G,r}^{(\lambda)}(q)
 =\sum_{\substack{z\in\mathbb Z^n\\\sum_i z_i=r}}
 q^{E_G(z)+\lambda\sum_i z_i^2}
 =q^{\lambda r^2/n}\Theta_{G,r}^{(\lambda)}(q).
 \tag{16}
\]

This scale depends on \(n,r,\lambda,q\), but not on the graph edges. It
therefore preserves all comparisons between graphs of the same order. For
\(R=kn+r\), the exact increasing approximation is

\[
 P_{G,R}(q)
 :=q^{-\lambda(nk^2+2kr)}A_{G,R}^{(\lambda)}(q)
 =\sum_{\substack{z\in\mathbb Z^n,\ \sum_i z_i=r\\z_i\ge-k}}
 q^{E_G(z)+\lambda\sum_i z_i^2}
 \nearrow\Psi_{G,r}^{(\lambda)}(q).
 \tag{17}
\]

Every exponent in the sum is a nonnegative integer. Every normalization
exponent is an integer. Exact arithmetic at \(q=1/2\), or any other rational
parameter, needs neither algebraic-number support nor an approximation to an
\(n\)-th root. The original centered-theta APIs remain useful for expressing
the intrinsic Gaussian scale, while the affine-lift APIs are the natural
implementation for exact fixed-rational experiments.

Reflection now includes its scale factor:

\[
 \boxed{\Psi_{G,n-r}^{(\lambda)}(q)
 =q^{\lambda(n-2r)}\Psi_{G,r}^{(\lambda)}(q),\qquad1\le r<n.}
 \tag{18}
\]

This follows directly from \(z\mapsto\mathbf1-z\): graph energy is unchanged,
and \(\|\mathbf1-z\|^2=\|z\|^2+n-2r\).

Let

\[
 T(q)=\sum_{z\in\mathbb Z}q^{\lambda z^2},
 \qquad
 V(b)=\frac{q^{\lambda b^2}}{1-q^{\lambda(2b+1)}}
 \quad(b\ge1).
\]

The same geometric-tail proof gives

\[
 0\le\Psi_{G,r}(q)-P_{G,R}(q)
 \le nT(q)^{n-1}V(k+1).
 \tag{19}
\]

For an exact rational upper bound, use

\[
 T^{\mathrm{up}}_H(q)
 =\sum_{z=-H}^{H+1}q^{\lambda z^2}+V(H+2)+V(H+1).
 \tag{20}
\]

A signed-lattice window with \(-H\le z_i\le H+1\) and \(\sum z_i=r\)
therefore has omitted mass at most

\[
 n\bigl(T^{\mathrm{up}}_H(q)\bigr)^{n-1}
 \bigl(V(H+2)+V(H+1)\bigr).
 \tag{21}
\]

These bounds drop both the graph energy and the sum constraint after selecting
an omitted coordinate. They are intentionally conservative, but every endpoint
is rational. `affine_lift_enclosure` implements the lattice window;
`affine_boundary_enclosure` implements the one-coefficient approximation.
The retained receipt checks their intersection for every residue at
\(q=1/2\), verifies (18) exactly, and obtains disjoint intervals for the
three-vertex path and the disconnected three-vertex single-edge graph. Thus
the method supplies a valid full-series inequivalence certificate at the
project's working parameter, without requiring connectedness of the candidates.

## 6. What this contributes to the fixed-pinning frontier

If two graphs have equal complete pinned series at the same \(\lambda,q\),
Theorem FR04.1 forces equal order, and Theorem FR04.2 forces equality of every
residue-class theta limit. This gives a hierarchy of necessary conditions:

\[
 \begin{aligned}
 \text{full equality}&\Longrightarrow (n_G=n_H,\ \Theta_{G,r}=\Theta_{H,r}\ \forall r),\\
 &\Longrightarrow \text{equal quadratic decay rate}.
 \end{aligned}
 \tag{15}
\]

No converse arrow is asserted. Passing from the full coefficients to the theta
limits removes the moving nonnegative boundary. Equation (8) displays exactly
what was removed: the entire sequence of boundary deficits. Equal limiting
values do not, by themselves, force those deficits to agree. A prefix
collision does not establish equality of the limits, and equality of limits
does not establish a full-series collision.

This distinction gives the next structural question a precise form. A genuine
full-series collision must match both the centered bulk theta data and every
boundary correction. A completeness proof could instead explain why matching
all these corrections forces a graph isomorphism. The present result supplies
the decomposition and certified access to its limiting part; it proves neither
of those further statements.

A practical use is one-sided rejection. Suppose two candidate graphs have the
same order and fixed pinning. If exact theta enclosures for one residue are
disjoint, their theta limits differ, so their complete pinned series differ.
That is a valid full-series inequivalence certificate even when an earlier
finite prefix agreed. The converse remains one-sided: overlapping intervals
merely mean that this computation has not separated the candidates.

## 7. API and acceptance evidence

| API in `singularity.pinned_theta` | Contract |
|---|---|
| `pinned_coefficient(G,R,lambda,q)` | Exact raw coefficient at rational \(q\), with a composition-count budget |
| `scaled_pinned_coefficient(G,R,lambda,t)` | Exact centered coefficient for \(q=t^{n^2}\) |
| `theta_enclosure(G,lambda,t,r,H)` | Rational interval for the complete affine theta limit |
| `boundary_enclosure(G,R,lambda,t)` | Rational interval for that same theta limit from one coefficient |
| `affine_lift_enclosure(G,lambda,q,r,H)` | Exact rational interval for \(\Psi_{G,r}(q)\), for every rational \(q\) |
| `affine_boundary_enclosure(G,R,lambda,q)` | Exact interval for \(\Psi_{G,r}(q)\) from one translated coefficient |
| `coefficient_decay_bounds(G,R,lambda,t)` | Exact lower and upper bounds underlying the order invariant |
| `RationalEnclosure` | Inclusive rational endpoints, exact width, retained-term count |

Tests check raw coefficients against an independent product-box enumeration;
integer centering against explicit multiplication by the scaling factor;
strictly increasing residue subsequences; intersection of the coefficient and
lattice enclosures; reflection; nested lattice windows; the one-vertex edge
case; relabeling; decay inequalities; exact-input validation; and rejection
before over-budget enumeration. No floating-point approximation participates
in the certificates.

The retained receipt is `results/fr04_pinned_theta.json`. Reproduce it with:

```bash
PYTHONPATH=src python scripts/fr04_pinned_theta.py --check
```

The scope remains intentionally narrow: fixed known positive pinning, fixed
positive parameter, raw nonnegative-height populations, and necessary
full-series invariants. Finite-prefix agreement remains separate from the
full-series questions motivating this companion.
