# Euler analysis: formal coordinates and controlled analytic factors

An Euler product has two distinct kinds of structure in this project. Its coefficients are exact finite polynomials, so logarithms and Euler transforms can be manipulated formally. Its values are infinite products, so analytic conclusions additionally require convergence and choices of branches. The distinction is useful rather than restrictive. Formal calculations reveal which factor ought to be removed; a remainder estimate proves where that removal has analytic meaning. The results below keep those two steps explicit.

Fix a graph with \(k\) vertices, write

\[
 L(x,q)=1+\sum_{n\ge1}\ell_n(q)x^n,
 \qquad
 \ell_n(q)=\sum_{|a|=n}q^{E(a)},
\]

and initially regard \(q\) as an indeterminate. Every \(\ell_n\) belongs to \(\mathbb Z_{\ge0}[q]\). Formal logarithms belong to \(\mathbb Q[q][[x]]\), because division by positive integers enters the logarithm expansion. No numerical approximation to \(q\), the coefficients, or the graph enters this part of the theory.

## Logarithmic coordinates from finite data

Put \(\log L=\sum_{n\ge1}c_n(q)x^n\). The identity \(L'=L(\log L)'\) gives a triangular recurrence that computes each logarithmic coefficient using only the local coefficients through the same volume:

\[
 c_n=\ell_n-\frac1n\sum_{j=1}^{n-1}j\,c_j\ell_{n-j}.
 \tag{6.1}
\]

In particular,

\[
 c_1=\ell_1,\quad
 c_2=\ell_2-\ell_1^2/2,\quad
 c_3=\ell_3-\ell_1\ell_2+\ell_1^3/3.
\]

The recurrence is a coefficient identity, not a fitted model. If two graphs agree through volume \(r-1\), they also agree in logarithmic coordinates through that volume, and their difference at volume \(r\) is unchanged. This triangular property is the reason first-discrepancy singularities can be read directly from the original local coefficients.

**Theorem SNG-A07 — rational polynomial Euler transform.** There is a unique sequence \(b_m(q)\in\mathbb Q[q]\) such that, formally in \(x\),

\[
 L(x,q)=\prod_{m\ge1}(1-x^m)^{-b_m(q)}.
 \tag{6.2}
\]

It is given by

\[
 b_m(q)=\sum_{d\mid m}\frac{\mu(d)}d\,c_{m/d}(q).
 \tag{6.3}
\]

Only factors with \(m\le N\) affect coefficients through volume \(N\).

**Proof.** Taking formal logarithms of the proposed product gives

\[
 c_n=\frac1n\sum_{m\mid n}m b_m.
\]

Ordinary Möbius inversion gives (6.3). Conversely those coefficients satisfy the displayed logarithmic identity, and formal exponential recovers \(L\). Uniqueness follows from the same triangular relation. Rational polynomial exponents are meaningful through the formal exponential definition of \((1-x^m)^{-b_m}\). \(\square\)

The first exponents are

\[
 b_1=\ell_1,\qquad
 b_2=\ell_2-\frac{\ell_1^2+\ell_1}{2},
\]

\[
 b_3=\ell_3-\ell_1\ell_2+\frac{\ell_1^3-\ell_1}{3}.
\]

These formulas are economical coordinates for local information. They do not make every exponent nonnegative or integral as a polynomial in \(q\). Such claims would be false for general integer-coefficient series. The existence theorem is over \(\mathbb Q[q]\), where the necessary divisions are legitimate.

Common-shift removal has an especially simple Euler-coordinate description. If \(B=(1-x^k)L\), then

\[
 b_m(L)=b_m(B)+\mathbf1_{m=k}.
\]

At the connected synchronized endpoint the only nonzero exponent is \(b_k=1\). At the independent endpoint the only nonzero exponent is \(b_1=k\). These are useful exact consistency checks, but they do not determine intermediate exponents from the endpoints.

## A different transform keeps integral bidegrees

There is a second, genuinely different product decomposition. Instead of putting a polynomial exponent on \(1-x^m\), retain energy inside the individual factors:

\[
 L(x,q)=\prod_{m\ge1}\prod_{e\ge0}
 (1-x^m q^e)^{-N_{m,e}}.
 \tag{6.4}
\]

At each fixed \(m\), only finitely many \(N_{m,e}\) are nonzero. The exponents can be negative. This is a formal decomposition and does not identify an actual population of positive “atoms” without a separate positivity theorem.

**Theorem SNG-A08 — integral bidegree transform.** For every series \(L\in1+x\mathbb Z[q][[x]]\), there are unique integers \(N_{m,e}\) satisfying (6.4). Their generating series is the plethystic logarithm

\[
 \sum_{m,e}N_{m,e}x^m q^e
 =\sum_{d\ge1}\frac{\mu(d)}d\log L(x^d,q^d).
 \tag{6.5}
\]

**Proof.** Suppose all factors of volume below \(m\) have been removed. The remaining series has the form \(1+x^mP_m(q)+O(x^{m+1})\), with integral polynomial \(P_m\). For every coefficient \(N_{m,e}=[q^e]P_m\), multiply by \((1-x^mq^e)^{N_{m,e}}\). This removes volume \(m\) and preserves integrality. Induction gives existence and uniqueness. Taking logarithms of (6.4), and applying Möbius inversion to the simultaneous substitutions \((x,q)\mapsto(x^d,q^d)\), gives (6.5). Thus the apparently rational expression in (6.5) has integral coefficients. \(\square\)

The substitution \(q\mapsto q^d\) is essential. Omitting it computes the transform in Theorem SNG-A07 rather than the bidegree transform. The two descriptions organize the same formal series differently. For example, a factor \((1-xq)^{-1}\) has one bidegree atom, yet its ordinary exponents \(b_m(q)\) are generally nontrivial polynomials. Coefficient-level equality permits conversion; the interpretations should remain distinct.

The corresponding weighted arithmetic factor is

\[
 \mathcal Z_{m,e}(s,q)=\prod_p(1-q^ep^{-ms})^{-1},
\]

with logarithm, on its absolutely convergent domain,

\[
 \log\mathcal Z_{m,e}(s,q)
 =\sum_{j\ge1}\frac{q^{ej}}jP(mjs).
\]

It is not equal to \(\zeta(ms)^{q^e}\). Replacing one expression by the other discards all the terms involving \(q^{ej}\) for \(j>1\). The ordinary rational-exponent transform and the integral bidegree transform therefore lead to different useful analytic factorizations.

## Leading divergence and what it forgets

The first local coefficient has a simple graph formula:

\[
 \alpha_G(q)=\ell_1(q)=\sum_{v\in V}q^{d_v}.
\]

Only one vertex has height one in a volume-one profile. Its energy is the number of incident edges. Thus the dominant singularity records the degree multiset and no finer graph information.

**Theorem SNG-A09 — leading real singularity.** For fixed \(0\le q\le1\), define

\[
 H_G(s,q)=\prod_p(1-p^{-s})^{\alpha_G(q)}L_G(p^{-s},q).
 \tag{6.6}
\]

The product is holomorphic for \(\Re s>1/2\), using the analytic logarithm of \(1-p^{-s}\) defined by its convergent power series on \(\Re s>0\). It is positive at the real point \(s=1\) and holomorphic and nonzero in a complex neighborhood of that point. Initially for \(\Re s>1\),

\[
 Z_G(s,q)=\zeta(s)^{\alpha_G(q)}H_G(s,q).
\]

Along the positive real axis,

\[
 Z_G(1+\varepsilon,q)
 \sim H_G(1,q)\varepsilon^{-\alpha_G(q)}
 \qquad(\varepsilon\downarrow0).
 \tag{6.7}
\]

**Proof.** Locally \(L=1+\alpha x+O(x^2)\), uniformly for \(q\in[0,1]\). Multiplication by \((1-x)^\alpha\) cancels the linear coefficient, leaving \(1+O(x^2)\). The prime sum of the remainder converges normally on compact subsets of \(\Re s>1/2\). Each individual factor is holomorphic there; \(L\) is analytic on \(|x|<1\), and the chosen power is holomorphic on \(\Re s>0\). For real positive \(s\), all factors are positive. The infinite tail is nonzero by absolute convergence of its logarithm; finitely many remaining factors are nonzero in a neighborhood of \(s=1\). The factorization follows on the original domain from the usual zeta Euler product. Finally \(\zeta(1+\varepsilon)\sim1/\varepsilon\). \(\square\)

The word “holomorphic” in the theorem does not assert that \(H_G\) is zero-free throughout its half-plane. A finite local factor can have complex zeros. Nonvanishing is asserted near the positive real point where it is proved. Similarly, fractional powers of zeta are unambiguous on the original half-plane but need branch choices if continued around zeros or poles elsewhere.

## Finite-order zeta factorization

**Theorem SNG-A10 — controlled finite Euler extraction.** Fix an integer \(M\ge1\) and a numerical \(q\in[0,1]\). Put

\[
 H_{G,M}(s,q)=\prod_p L_G(p^{-s},q)
 \prod_{m=1}^{M}(1-p^{-ms})^{b_m(q)}.
 \tag{6.8}
\]

This product is holomorphic on \(\Re s>1/(M+1)\). It is positive for real \(s>1/(M+1)\), and nonzero in a neighborhood of every point on that positive real interval. On the initial half-plane,

\[
 Z_G(s,q)=
 \left(\prod_{m=1}^{M}\zeta(ms)^{b_m(q)}\right)H_{G,M}(s,q).
 \tag{6.9}
\]

**Proof.** Theorem SNG-A07 implies

\[
 L_G(x,q)\prod_{m=1}^M(1-x^m)^{b_m(q)}=1+O(x^{M+1})
\]

near zero. For primes sufficiently large, this estimate is uniform on any compact subset of the indicated half-plane, and its prime sum converges. The finitely many small-prime factors are holomorphic on \(\Re s>0\); the powers use the logarithms specified above. Positivity on the real axis follows directly from (6.8), and absolute logarithmic convergence proves local nonvanishing there. Equation (6.9) follows by finite multiplication of zeta Euler products on \(\Re s>1\). \(\square\)

This theorem removes any need to assume convergence of the infinite product over all \(m\) in an analytic setting. Formal identity (6.2) does not by itself license an unrestricted exchange of its two infinite products, over primes and over volumes. Small-prime local zeros can limit the radius of the logarithmic power series, and the exponents can grow. Keeping \(M\) finite is both sufficient for a prescribed visibility calculation and analytically safer.

Equation (6.9) supplies local continuations after branches have been chosen in regions avoiding relevant zeta zeros and poles. It is not a blanket meromorphic-continuation theorem. Nonintegral exponents generally produce branched functions. Even on the positive real axis below one, separate zeta factors can be negative, so assigning real fractional powers independently does not reproduce an automatically positive partition function. The positive quantity directly defined there is the remainder product (6.8); its relation to a continued \(Z_G\) must respect the chosen branches.

## Why ratios are cleaner than individual continuations

If two graphs have identical low-volume coefficients, their low-order zeta exponents cancel before any continuation is attempted. The quotient Euler product can consequently converge farther left as a positive real product. Its first remaining zeta factor has argument approaching one from above. No lower-argument zeta powers are needed to state the resulting real asymptotic. This is the analytic advantage of comparing matched structures rather than interpreting every formal singularity of an individual object as an independently observable feature.

The hierarchy is exact but limited. It proves where a known local distinction appears arithmetically. It does not prove that a distinction always exists between nonisomorphic graphs, nor that all formal exponent locations are actual singularities after every cancellation. If the local series agree, every arithmetic lift in this chapter agrees. If the first discrepancy vanishes at a special numerical \(q\), the visibility order at that parameter must be recomputed. These qualifications identify the genuine inverse problem rather than weakening a theorem that never claimed more.

## A complete low-order transform example

The single-edge model makes the difference between polynomial exponents and positive constituent populations concrete. Its first coefficients are

\[
 \ell_1=2q,\qquad
 \ell_2=1+2q^4,\qquad
 \ell_3=2q+2q^9.
\]

Substitution into the rational Euler transform gives

\[
 \begin{aligned}
 b_1(q)&=2q,\\
 b_2(q)&=1+2q^4-2q^2-q,\\
 b_3(q)&=2q^9-4q^5+(8q^3-2q)/3.
 \end{aligned}
 \tag{6.10}
\]

At \(q=1/2\), these are \(1,1/8,-31/256\). Thus a valid finite extraction reads

\[
 Z_{K_2}(s,1/2)=
 \zeta(s)\zeta(2s)^{1/8}\zeta(3s)^{-31/256}
 H_{K_2,3}(s,1/2)
 \qquad(\Re s>1).
 \tag{6.11}
\]

The negative third exponent is not a negative number of arithmetic objects. It is a subtraction introduced by logarithmic and Möbius coordinates. Likewise, the exponent one eighth does not describe one eighth of an independent integer coordinate. Those are exact algebraic coordinates on a positive local series. They are useful precisely because they can cancel lower-order contributions, not because each factor has a separate population interpretation.

At the endpoints the same formulas reduce correctly: at \(q=0\), the second exponent is one and the other displayed exponents are zero; at \(q=1\), the first exponent is two and the next two are zero. Agreement at both endpoints therefore places only weak restrictions on the intermediate polynomial behavior. The coefficient recurrence supplies the actual intermediate values. A numerical plot interpolating only the endpoints would have no authority to invent them.

The bidegree decomposition has a different bookkeeping purpose. Its first volume layer contains the atom count \(N_{1,1}=2\). Removing \((1-xq)^{-2}\) from the single-edge series leaves, at volume two, the polynomial \(1-3q^2+2q^4\). Hence the second bidegree layer already contains a negative exponent, \(N_{2,2}=-3\). Even integral bidegree exponents are therefore not automatically positive atoms. The notation “plethystic” supplies a formal inversion rule; it does not establish a free-generation theorem for an underlying combinatorial class.

## Uniformity and the boundary of the weight parameter

For each fixed extraction order \(M\), the remainder product in Theorem SNG-A10 is jointly continuous in real \(q\in[0,1]\) and real \(s>1/(M+1)\). On compact subsets of that parameter region its large-prime logarithmic tail converges uniformly. To see this, the finitely many polynomials \(b_m(q)\) are bounded on the compact weight interval, and the coefficient majorant bounds the Taylor remainders uniformly for \(x\) in a small fixed disk. The canceled coefficients through order \(M\) are identically zero as polynomials, so the remaining estimate is uniformly \(O(x^{M+1})\). A convergent prime-power sum dominates the tail. Finitely many positive real local factors then preserve continuity and local nonvanishing.

This continuity statement is often enough to pass a weight limit through a regularized product. It does not mean that the unregularized Euler product converges uniformly as \(s\downarrow1\). The leading zeta factor carries the obstruction to that stronger statement. Chapter 8 isolates it in a quantitative estimate rather than suppressing it through a formal exchange of limits.

The chosen weight range also has a mathematical boundary. Suppose the graph has an edge, choose a vertex of positive degree \(d_v\), and fix \(0<x<1\). The terms coming from profiles \(ne_v\) are \(q^{d_vn^2}x^n\). For every real \(q>1\), these terms fail even to tend to zero as \(n\to\infty\). Thus the unbounded local height series diverges. The restriction \(q\le1\) cannot simply be removed by calling the series a partition function. A finite height cutoff would define a different object and would require its own limiting argument.

For \(|q|<1\), the local series is analytic in the complex weight parameter. At a boundary value such as \(q=1\), derivatives from the allowed real side can still exist to every finite order, because each derivative introduces only polynomial energy factors and the geometric volume decay dominates them. Such smooth one-sided behavior should not be mistaken for an unrestricted analytic extension beyond the unit disk. These domain distinctions matter especially when symbolic exponents are evaluated numerically: exact polynomial coefficients can be evaluated anywhere, while the infinite series from which they were extracted has the domain proved for it.
