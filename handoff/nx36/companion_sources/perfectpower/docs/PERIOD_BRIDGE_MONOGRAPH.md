# Exact Integral Families, Cyclotomic Filters, and an E8 Spectral Bridge

**A Raghava-centered mathematical and software synthesis. PerfectPower, 16 October 2026.**

The central achievement of this release is an executable chain from a recognizable integral to its finite algebraic structure. A sine integral becomes a finite residue sum. An inverse-binomial series becomes an arcsine moment. A collection of 240 cyclotomic integral values becomes two values. The actual E8 root system supplies an order-30 operator whose spectrum gives an exact Mellin identity and a logarithmic moment. Each construction retains its hypotheses and an independently checkable finite output.

The most useful lesson drawn from K. Srinivasa Raghava's work is methodological: choose parameters and weights so that unwanted terms disappear for an identifiable reason. The software implements that approach through exact recurrences, endpoint derivatives, root-of-unity filters, and replayable transformation paths. It does not turn a visually suggestive numerical coincidence into an equivalence of mathematical structures. Existing theorems retain their attribution, and none of the identities below is presented as a historically novel discovery.

## The mathematical objects behind the pictures

The project inputs include the two public Claude artifacts attributed by the user to Cody Lakeland: the [Categorical–Spectral–Cyclotomic visualization](https://claude.ai/public/artifacts/1db99748-b7fd-477b-8a9c-1bb54fb33a19) and the [384–264 Resonance visualization](https://claude.ai/public/artifacts/4fd0f32a-22b6-4fae-b2d2-1f3732d324af). The earlier source audit found canvas visualizations with fixed phase labels and comments proposing categorical connections. They motivate the mathematical inputs used here. The author's Facebook identity and the original Facebook posts were not independently recovered.

Write

\[
q=e^{i\pi/840}=\zeta_{1680},\qquad
Q=e^{i\pi/221760}=\zeta_{443520}.
\]

Here \(\zeta_n=e^{2\pi i/n}\). Since \(221760=264\cdot840\), the elementary phase identity is

\[
Q^{264}=q.
\]

This is an actual map between roots of unity. The three important counts have different meanings:

| Quantity | Exact value | Meaning |
|---|---:|---|
| \(\varphi(1680)\) | 384 | Degree of \(\mathbb Q(q)\) over \(\mathbb Q\) |
| \(443520/1680\) | 264 | Number of branches solving \(z^{264}=q\) |
| \(\varphi(443520)/\varphi(1680)\) | 240 | Number of conjugates of \(Q\) over \(\mathbb Q(q)\) |
| \(\varphi(1680)/2\) | 192 | Degree of the maximal real subfield of \(\mathbb Q(q)\) |

Thus a branch count of 264 is not the relative field degree, which is 240. The degree 96 belongs to other related conductors, including \(\varphi(420)\), and cannot serve as the maximal real degree at conductor 1680. Such distinctions determine which averaging operation is mathematically available. They also specify what a future categorical interpretation would have to explain.

## One integral kernel for every rational phase

For \(\Re s>1\) and \(|z|=1\), define

\[
I_s(z)=\frac{1}{\Gamma(s)}
\int_0^1\frac{z(-\log x)^{s-1}}{1-zx}\,dx.
\]

The power of the positive real number \(-\log x\) uses its real logarithm. Expanding the geometric kernel and integrating each monomial gives

\[
\frac{1}{\Gamma(s)}\int_0^1x^{n-1}(-\log x)^{s-1}\,dx=n^{-s},
\qquad
I_s(z)=\sum_{n\ge1}\frac{z^n}{n^s}=\operatorname{Li}_s(z).
\]

Absolute convergence on the stated half-plane justifies the interchange, including \(z=1\). This common domain is intentionally used throughout the phase-filter engine. Some individual kernels admit wider domains, but those continuations are separate analytic statements. The integral representation and polylogarithm conventions are recorded in the [NIST Digital Library of Mathematical Functions, §25.12](https://dlmf.nist.gov/25.12).

The finite Fourier identity

\[
\sum_{j=0}^{d-1}e^{2\pi ijn/d}
=d\,\mathbf{1}_{d\mid n}
\]

then proves the distribution formula

\[
\sum_{j=0}^{d-1}I_s(ze^{2\pi ij/d})
=d^{1-s}I_s(z^d).
\]

The reduction is structural. Every disallowed series index cancels before any numerical approximation. For the artifact parameters it reads

\[
\sum_{j=0}^{263}I_s(Qe^{2\pi ij/264})
=264^{1-s}I_s(q).
\]

More generally, a periodic coefficient sequence \(c_1,\ldots,c_N\) defines a rational kernel

\[
\frac{\sum_{r=1}^{N}c_rx^{r-1}}{1-x^N}.
\]

Its Mellin integral is the Dirichlet series with those periodic coefficients. Discrete Fourier inversion expresses that series as a finite combination of \(I_s(\zeta_N^j)\). This is the operational bridge between rational logarithmic integrals and finite phase geometry. It recognizes an entire family rather than matching a single decimal constant.

## From 240 conjugates to two periods

The complete 264-branch fiber contains nonprimitive roots. The conjugate fiber relevant to the field extension retains precisely the primitive roots. Its exponents are

\[
u=1+1680t,\qquad 0\le t<264,\qquad \gcd(u,443520)=1.
\]

Only the prime 11 is new when passing from conductor 1680 to 443520. All other prime divisors already divide 1680 and cannot divide \(1+1680t\). Since \(1680\equiv8\pmod{11}\), the excluded class is \(t\equiv4\pmod{11}\). There are 24 excluded values, leaving 240.

The complete fiber reduces to \(264^{1-s}I_s(q)\). The excluded exponents have the form \(6721+18480k\), \(0\le k<24\), and their 24th powers have phase

\[
\frac{24\cdot6721}{443520}
=\frac{611}{1680}\pmod1.
\]

A second Fourier distribution therefore subtracts exactly the 24-branch contribution. Write \(U\) for the retained 240 values of \(t\). Then

\[
\boxed{
\sum_{t\in U}
I_s\!\left(\zeta_{443520}^{1+1680t}\right)
=264^{1-s}I_s(q)-24^{1-s}I_s(q^{611}).
}
\]

The same calculation works for arbitrary \(n\mid N\), not merely these conductors. Suppose \(\gcd(a,n)=1\), and let \(P\) contain the prime divisors of \(N\) absent from \(n\). Write \(U_{n,N,a}\) for the primitive residues modulo \(N\) congruent to \(a\) modulo \(n\). Inclusion-exclusion over the squarefree products of primes in \(P\) gives

\[
\sum_{u\in U_{n,N,a}}
I_s(\zeta_N^u)
=\sum_{d\mid\prod_{p\in P}p}
\mu(d)\left(\frac{N}{nd}\right)^{1-s}
I_s\!\left(\zeta_n^{a d^{-1}\bmod n}\right).
\]

Indeed, imposing \(d\mid u\) and writing \(u=dv\) changes the congruence to \(v\equiv ad^{-1}\pmod n\). The resulting full fiber contains \(N/(nd)\) roots, so its distribution formula gives the displayed term. If \(a\) is not a unit modulo \(n\), the primitive fiber is empty. This case is represented explicitly rather than passed through an invalid modular inverse.

For even weight \(2k\), the Bernoulli Fourier identity gives

\[
\Re I_{2k}(e^{2\pi it})
=\frac{(-1)^{k+1}2^{2k-1}}{(2k)!}B_{2k}(t)\pi^{2k},
\qquad 0\le t<1.
\]

The [DLMF Bernoulli Fourier expansions](https://dlmf.nist.gov/24.8) fix the normalization. Consequently every rational phase at positive even weight has an exact rational real coefficient. Here the weight-two and weight-four reductions are

\[
\Re\sum_{u}I_2(\zeta_{443520}^u)
=\frac{22537}{6773760}\pi^2,
\]

\[
\Re\sum_{u}I_4(\zeta_{443520}^u)
=\frac{21467004594397}{43971386730872832000}\pi^4.
\]

The software computes the source-side Bernoulli sum independently of the reduced side. Agreement therefore tests both the retained fiber and the reduction coefficients; it does not merely reevaluate a stored formula.

## Raghava's sine-over-pole family

The recovered [ICTP interview](https://ictp.global/news/13119204) displays Raghava's first seven sine-over-pole examples and credits Abdulhafeez Abdulsalam with the all-order generalization. The implementation preserves those separate roles. A useful parameter extension follows directly from the same elementary residue calculation.

For an integer \(k\ge1\) and positive real \(a,b\), put

\[
J_k(a,b)=\int_{-\infty}^{\infty}
\left(\frac{\sin(ax)}{x-ib}\right)^kdx.
\]

For \(k\ge2\) the integral is absolutely convergent. For \(k=1\), each half-line converges as an ordinary oscillatory improper integral. Expand

\[
\sin(ax)^k=(2i)^{-k}\sum_{j=0}^{k}
(-1)^j\binom{k}{j}e^{ia(k-2j)x}.
\]

For a positive frequency \(c\), closing the contour above gives

\[
\int_{\mathbb R}\frac{e^{icx}}{(x-ib)^k}\,dx
=\frac{2\pi i(ic)^{k-1}}{(k-1)!}e^{-bc}.
\]

Negative frequencies close below and contribute zero. The zero-frequency term, when present, also integrates to zero for \(k\ge2\). Thus

\[
\boxed{
J_k(a,b)=\frac{\pi a^{k-1}}{2^{k-1}(k-1)!}
\sum_{j=0}^{\lfloor(k-1)/2\rfloor}
(-1)^j\binom{k}{j}(k-2j)^{k-1}e^{-ab(k-2j)}.
}
\]

For example, \(J_1(a,b)=\pi e^{-ab}\), \(J_2(a,b)=\pi a e^{-2ab}\), and

\[
J_3(a,b)=\frac{\pi a^2}{8}
\left(9e^{-3ab}-3e^{-ab}\right).
\]

The substitution \(y=ax\) independently checks the scale relation \(J_k(a,b)=a^{k-1}J_k(1,ab)\). The exact output consists of rational coefficients and exponential powers. Its optional binary64 evaluation is separately labeled because severe cancellation can reduce floating-point accuracy at high order.

## Arcsine kernels as exact coefficient machines

Raghava's current [arcsine and inverse-binomial paper](https://arxiv.org/html/2607.09904v2) supplies the specific harmonic and two-order constructions implemented here. The paper explicitly traces its evaluations to classical hypergeometric transformations and inverse-sine expansions. The release follows that attribution and implements a bounded range of the formulas, rather than claiming a new summation principle.

Set \(y(t)=\cos(2u\arcsin(t/2))\), using the inverse-sine branch that vanishes at the origin. Direct differentiation gives

\[
(4-t^2)y''-ty'+4u^2y=0,
\qquad y(0)=1,\quad y'(0)=0.
\]

Writing \(y=\sum c_nt^{2n}\) gives a complete rational recurrence:

\[
c_0=1,\qquad
c_{n+1}=\frac{n^2-u^2}{2(n+1)(2n+1)}c_n.
\]

This proves the kernel expansion

\[
\cos(2u\arcsin(t/2))
=1-u^2\sum_{n\ge1}
\frac{t^{2n}}{n^2\binom{2n}{n}}
\prod_{j=1}^{n-1}\left(1-\frac{u^2}{j^2}\right),
\qquad |t|<2.
\]

For integer \(u\), the recurrence terminates. For example, \(u=3\) gives the polynomial \(1-9t^2/2+3t^4-t^6/2\). This provides an independent finite check without evaluating inverse trigonometric functions numerically.

Define elementary symmetric factors by

\[
\prod_{j=1}^{n-1}(1+z/j^2)=\sum_{r\ge0}e_r(n)z^r.
\]

They satisfy the finite update

\[
e_r(n+1)=e_r(n)+n^{-2}e_{r-1}(n),
\qquad e_0(n)=1.
\]

Extracting the coefficient of \(u^{2j}\) from the kernel and cosine expansions proves

\[
\boxed{
\sum_{n\ge1}\frac{e_{j-1}(n)t^{2n}}
{n^2\binom{2n}{n}}
=\frac{4^j}{(2j)!}\arcsin(t/2)^{2j}.
}
\]

At \(t=2\sin(\pi/840)\), the principal inverse sine recovers \(\pi/840\). Therefore the first moments equal \(\pi^2/352800\) and \(\pi^4/746807040000\). The refined artifact angle \(\pi/221760\) produces the same identities with an additional factor \(264^{-2j}\). This directly connects the two phase resolutions to an all-order harmonic series family.

The rational-input evaluator also produces a rigorous truncation bound. Since

\[
0\le e_r(n)\le\frac{2^r}{r!},\qquad
\binom{2n}{n}\ge\frac{4^n}{2n+1},
\]

the tail beyond \(M\) terms of the \(j\)-th moment, with \(\rho=t^2/4<1\), is bounded by

\[
\frac{3\,2^{j-1}}{(j-1)!}
\frac{\rho^{M+1}}{(M+1)(1-\rho)}.
\]

The bound is conservative but exact and transparent. Algebraic angle specializations and rational-input enclosures use different APIs, so an expression such as \(2\sin(\pi/840)\) is never silently substituted into an API that promises an exact rational argument.

## Deliberate cancellation of two selected orders

A second use of Raghava's construction chooses an odd polynomial and a harmonic weight so that unwanted Fourier constants vanish. Let \(\alpha=\pi/6\), and define Lidstone polynomials by

\[
\ell_0(v)=v,\qquad \ell_k''=\ell_{k-1},\qquad
\ell_k(0)=\ell_k(1)=0\quad(k\ge1).
\]

Their even endpoint derivatives select individual orders. For \(1\le r<s\), write \(\lambda_k=\ell_k'(0)\) and form

\[
P_{r,s}(\theta)=\alpha^{2s-1}(2s-1)!
\left[\ell_{s-1}(\theta/\alpha)
-\frac{\lambda_{s-1}}{\lambda_{r-1}}
\ell_{r-1}(\theta/\alpha)\right].
\]

The linear term cancels. Only the even endpoint derivatives corresponding to orders \(r\) and \(s\) can remain. Choose

\[
D=2^{2r+2s-2},\qquad
A=D+2^{2r-1}+2^{2s-1}.
\]

Then the Fourier multiplier factors exactly as

\[
1+(D-A)z+Dz^2
=(1-2^{2r-1}z)(1-2^{2s-1}z).
\]

Its two roots are precisely \(2^{1-2r}\) and \(2^{1-2s}\). The polynomial removes every other even sine order, and the multiplier removes the two selected orders. This is cancellation by construction, with an explicit finite reason for every vanished coefficient.

The relation to an integral follows from elementary harmonic insertion. For \(P(\theta)=\sum p_j\theta^{2j-1}\), set

\[
w_P(n)=\sum_j\frac{p_j(2j-1)!}{4^j}e_{j-1}(n).
\]

The inverse-binomial generating function and \(t=2\sin\theta\) give

\[
\sum_{n\ge1}\frac{w_P(n)}{n^2\binom{2n}{n}}
\left(H_{2n}+AH_n-\frac D{2n}\right)
=\int_0^{\alpha}P(\theta)L_{A,D}(\theta)\,d\theta,
\]

\[
L_{A,D}(\theta)=-(A+1)\log(1-2\sin\theta)
-A\log(1+2\sin\theta)+D\log(2\sin\theta).
\]

The logarithmic endpoint singularities are integrable. Repeated integration by parts in the Fourier expansion gives a finite combination of odd zeta values once the even sine coefficients have canceled.

For \((r,s)=(2,3)\), the software reproduces \(A=296\), \(D=256\), and \(P(\theta)=\theta^5-\alpha^2\theta^3\). The resulting published specialization is

\[
\sum_{n\ge1}\frac{e_2(n)-\pi^2e_1(n)/180}
{n^2\binom{2n}{n}}
\left(H_{2n}+296H_n-\frac{128}{n}\right)
=\frac{61\pi^4\zeta(3)}{3645}
-\frac{20153\pi^2\zeta(5)}{9720}
+\frac{24563\zeta(7)}{1296}.
\]

Each finite coefficient, endpoint derivative, and multiplier is retained in the computation receipt. The current implementation supports every pair \(1\le r<s\le16\), giving 120 pairs. The theorem covers arbitrary fixed pairs; that theorem and this finite execution range are different statements. Its classification concerns the specified polynomial cancellation mechanism and does not classify all inverse-binomial or odd-zeta identities.

## A genuine E8 operator inside the phase circle

E8 enters through its actual roots and reflections. In Euclidean coordinates, its roots are the 112 vectors \(\pm e_i\pm e_j\), \(i<j\), together with the 128 vectors whose eight coordinates are \(\pm1/2\) with an even number of minus signs. The implementation doubles all coordinates, retaining integers throughout. Every doubled root has squared norm eight.

A displayed simple-root basis has the E8 Cartan matrix. Exact inversion verifies that every root has integral coefficients of one sign in this basis, with 120 positive and 120 negative roots. The highest positive-root height is 29. Each simple reflection permutes the complete root set, and their ordered product defines the Coxeter operator \(C\).

Its characteristic polynomial is

\[
\Phi_{30}(x)=x^8+x^7-x^5-x^4-x^3+x+1.
\]

Integer matrix multiplication checks \(C^{30}=1\), with no smaller positive power equal to the identity. Its eigenphases are \(\zeta_{30}^{m}\), where

\[
m\in\{1,7,11,13,17,19,23,29\}.
\]

These are exactly the primitive 30th-root phases. The identification with the artifact circle is the actual power map \(q^{56}=\zeta_{30}\). Enumerating all 384 primitive exponents modulo 1680 shows each of the eight exponents modulo 30 occurs 48 times. Consequently the conductor-1680 rational cyclotomic representation restricts to 48 copies of this eight-dimensional Coxeter representation.

This construction realizes a field \(\mathbb Q(\zeta_{30})\) inside \(\operatorname{End}_{\mathbb Q}(\mathbb Q^8)\). Such cyclotomic structures on root lattices are established mathematical objects; [Mark Reeder's paper](https://www.math.utah.edu/~ptrapa/math-library/reeder/reeder-cyclotomic-root-lattices-2008.pdf) develops them systematically. [David Richter's triacontagonal coordinates](https://arxiv.org/abs/0704.3091) give a complementary 30-fold geometric realization. The explicit 112-plus-128 root description is also explained by [John Baez](https://math.ucr.edu/home/baez/octonions/integers/integers_3.html).

There are two relevant representations. The reflection representation has dimension eight and the primitive eigenphases above. The permutation representation on the actual roots has dimension 240 and decomposes into eight genuine orbits of length 30. Equality between the number of roots and the earlier relative field degree 240 does not supply an equivariant identification of those objects. The release supplies no arbitrary bijection between their labels.

## An exact spectral zero and a logarithmic integral

The trace of \(C^n\) is the Ramanujan sum

\[
c_{30}(n)=\sum_{d\mid\gcd(30,n)}d\mu(30/d).
\]

Summing \(c_{30}(n)n^{-s}\), or applying the primitive-root filter, proves

\[
\operatorname{Tr}\operatorname{Li}_s(C)
=\zeta(s)(2^{1-s}-1)(3^{1-s}-1)(5^{1-s}-1).
\]

At weight two this is \(-2\pi^2/45\). Independently summing the eight Bernoulli values gives the same exact result. The root permutation contributes \(8\cdot30^{1-s}\zeta(s)\), since each of its eight regular cyclic orbits contributes the complete root distribution.

Take the direct sum of these two verified cyclic representations. Its dimension is 248. We call it the **root-permutation-plus-Cartan spectral model**. Identification with a particular Lie-group adjoint lift would also require checking the phases of its root-space action and is not asserted here. Its normalized Mellin trace is

\[
Z(s)=\zeta(s)30^{1-s}
\left[8-(2^{s-1}-1)(3^{s-1}-1)(5^{s-1}-1)\right].
\]

For real \(s>1\), the three factors in the product are positive and strictly increasing. Their product equals eight exactly at \(s=2\). Thus \(Z(s)\) is positive on \((1,2)\), vanishes at two, and is negative above two. This proves its unique zero on that real domain. Analogous weight-two cancellations occur for other root systems; no claim of E8 exclusivity or historical novelty follows.

The characteristic polynomial provides an explicit rational integral kernel. Because \(\det(1-xC)=\Phi_{30}(x)\), logarithmic differentiation yields

\[
\operatorname{Tr}\bigl(C(1-xC)^{-1}\bigr)
=-\frac{\Phi_{30}'(x)}{\Phi_{30}(x)}.
\]

Combining the two representations gives

\[
K(x)=\frac{240x^{29}}{1-x^{30}}
-\frac{\Phi_{30}'(x)}{\Phi_{30}(x)},
\qquad
Z(s)=\frac1{\Gamma(s)}\int_0^1(-\log x)^{s-1}K(x)\,dx.
\]

Consequently

\[
\boxed{\int_0^1(-\log x)K(x)\,dx=0.}
\]

Differentiating at \(s=2\) is legitimate on a neighborhood inside \(\Re s>1\). The derivative of the gamma normalization multiplies \(Z(2)=0\), so it disappears. Differentiating the finite Euler-factor expression gives

\[
\boxed{
\int_0^1(-\log x)\log(-\log x)K(x)\,dx
=-\frac{\pi^2}{180}
\left(16\log2+12\log3+10\log5\right).
}
\]

The right side is approximately \(-2.213427747844811\). This formula illustrates the practical return from retaining a parameterized family: a proved spectral identity automatically supplies a different logarithmically weighted integral. It does not require guessing a constant from numerical quadrature.

## What the transport layer means

The finite semantic objects are exact phase multiplicity packets. At conductor \(N\), a packet records a rational combination of characters \(e^{2\pi ik/N}\). Nonnegative integral multiplicities describe an actual complex representation of the cyclic group; general rational coefficients describe a formal element of its rationalized representation ring. Direct sum adds multiplicities, tensor product convolves exponents, and duality negates exponents. Conductor lifts preserve the represented phases, while subgroup restriction evaluates the original generator at the appropriate power.

The implementation checks composable paths of explicitly supported operations. A transport receipt states its source, target, operations, parameters, and whether the complete phase packet is preserved. Replaying the operations must reproduce every stated field. An operation that changes the spectrum is retained as a change, rather than automatically being declared an integral identity. These arrows are checked rewrite paths; they are not unspecified equivariant maps between Lie or fusion categories.

Period evaluation is additive under direct sums. It is generally not multiplicative under tensor products. Even the one-dimensional trivial character demonstrates the distinction: its period is \(\zeta(s)\), its tensor square is the same character, and its period remains \(\zeta(s)\), rather than \(\zeta(s)^2\). A tensor operation on representations therefore cannot be replaced by multiplication of evaluated integrals.

Likewise, equality of one observed integral value is weaker than equality of spectral objects. The 248-dimensional model above has zero weight-two period while retaining a nonzero representation. In contrast, the entire cyclic character, observed at every power of the generator, determines the multiplicities by discrete Fourier inversion. This is the same semantic discipline used elsewhere in PerfectPower's partial-state and observation machinery: equality under a selected observation must be distinguished from equality under every relevant observation.

The release reuses the existing exact arithmetic and the rational \(\pi\)-enclosure machinery in `cyclotomic_real.py`. Even-weight intervals multiply an exact Bernoulli coefficient by an existing certified rational interval for a power of \(\pi\). These are exact Python enclosures based on explicit analytic bounds, not new Lean theorems. Elliptic and higher-genus periods retain their existing cycle, branch, and marking obligations; a rational phase label does not by itself identify such a period with a polylogarithm.

## Reproduction, limits, and application delivery

The implementation is divided by mathematical responsibility. `raghava_periods.py` constructs sine-pole coefficients, arcsine recurrences, harmonic moments, selected-order cancellation, and bounded partial sums. `cyclotomic_periods.py` constructs complete and primitive root-fiber reductions and exact even-weight coefficients. `e8_periods.py` builds actual roots, reflections, the Coxeter matrix, orbit decompositions, and spectral Mellin values. `period_transport.py` supplies normalized phase objects and replayable operation paths. The main command `python -m perfectpower integral-families --explain` exposes the retained summary; `--details` exposes the detailed receipts.

From the repository root, `PYTHONPATH=python python python/develop_period_bridge.py` regenerates the research receipts. The focused mathematical modules are testable through standard-library `unittest` discovery. For example, `PYTHONPATH=python python -m unittest discover -s python/tests -p test_e8_periods.py -v` independently checks the E8 geometry, matrix action, all proper Coxeter powers, divisor traces, Bernoulli values, and exact cancellation. The release retains 331 replayed Raghava receipts, 1,930 root-filter cases for \(n\mid N\le48\), with 5,790 exact comparisons at weights two, four, and six, six checked transport paths, and closure over 31 conductors. Those finite checks supplement the general derivation; they do not establish correctness for every possible input by enumeration.

Separate diagnostics compare all 120 supported selected-order identities against zeta values computed through an independent Euler transformation, using Decimal precision 200. They remain numerical diagnostics: neither the finite \(\pi\) literal nor that numerical zeta evaluation is presented as a rigorous enclosure. The exact partial-sum tail bounds are retained separately. Independent SciPy quadrature also reproduces the E8 weight-two zero to about \(10^{-15}\) and the logarithmic moment within its reported numerical error estimate. These integrations provide an alternative calculation, not the proof of either identity.

Execution bounds remain explicit. The sine-pole constructor accepts integer order through 256 and positive rational parameters subject to a bit budget. The real arcsine enclosure accepts bounded rational \(u\), rational \(|t|<2\), and at most 4096 retained terms. The moment constructor accepts \(j\le32\). The selected-order constructor accepts \(s\le16\); its bounded partial-sum routine accepts at most 2048 terms. The transport layer guards dense cyclotomic trace allocation by a conductor budget and guards finite closure by an object budget. The mathematical identities have their stated wider domains, but unsupported computations fail rather than silently weakening the requested result.

The public research feed is regenerated with `python scripts/export_explorer_live.py`. Refreshing a research feed and publishing browser assets are separate deployment actions. A native executable requires its own rebuilt package; a live data receipt does not rewrite installed executable code. The release archive and PDF monograph accompany the exact source snapshot, while application synchronization is recorded by the release process.

The recovered sourcebook is a discovery collection, not a proof library: source URLs, archive entries, and formula transcriptions have different units of counting, and repeated publications can point to the same integral. Direct Facebook recovery remained incomplete. This release's implemented families are the explicitly derived and tested subset. Wider retrieval can add candidate kernels without changing which formulas have mathematical derivations, exact arithmetic receipts, or rigorous remainder estimates.

The source audit's categorical comments become concrete here only where a mathematical object and a supported operation have been supplied. The phase maps, cyclic representations, E8 reflection operator, root permutation, finite reductions, and Mellin integrals are explicit. A fusion category, higher categorical colimit, categorical trace of 264, or equivalence assembling all these structures would require additional definitions and theorems. The present machinery gives those future constructions actual data to respect and immediate exact calculations to perform.

## Primary sources and attribution

K. Srinivasa Raghava, *Arcsine kernels, inverse-binomial harmonic sums, and classical hypergeometric transformations*, version 2, 15 October 2026, [arXiv:2607.09904v2](https://arxiv.org/html/2607.09904v2). This is the source for the implemented arcsine and selected-order families, with its stated classical antecedents and scope.

*Srinivasa Raghava: Patterns, Primes, and the Ramanujan Influence*, [ICTP Global Science Portal](https://ictp.global/news/13119204). The displayed sine-pole examples are credited to Raghava and the all-order generalization to Abdulhafeez Abdulsalam.

NIST, [DLMF §25.12, Polylogarithms](https://dlmf.nist.gov/25.12), and [DLMF §24.8, Bernoulli and Euler Fourier Series](https://dlmf.nist.gov/24.8). These fix the classical integral and Fourier conventions used for the phase-period engine.

Mark Reeder, *Cyclotomic structures on root lattices*, [author's paper](https://www.math.utah.edu/~ptrapa/math-library/reeder/reeder-cyclotomic-root-lattices-2008.pdf). David A. Richter, *Triacontagonal coordinates for the E(8) root system*, [arXiv:0704.3091](https://arxiv.org/abs/0704.3091). John Baez, [Integer Octonions, Part 3](https://math.ucr.edu/home/baez/octonions/integers/integers_3.html), for the explicit root-coordinate explanation.

The two supplied Claude artifact URLs are project references attributed by the user to Cody Lakeland. Their mathematical motivation is preserved without treating explanatory comments or visual labels as proofs. All finite computation receipts in this release remain Python computations; this release makes no claim that its new analytic identities have been checked by the Lean kernel.
