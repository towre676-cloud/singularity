# FR02: arithmetic recovery from a single fixed-pinning coefficient

**Status.** Proved project result, exact decoder, independently enumerated finite checks. This companion does not implement an NX36 work packet. It establishes a new necessary condition for fixed-pinning equality and a reconstruction theorem for one restricted family. It does not prove completeness of the unmarked graph series.

## 1. What information can survive a rational specialization?

The existing exact machinery retains an energy polynomial at each volume. If that polynomial is available, its largest exponent is an obvious source of graph information. A more difficult question is whether the information remains available after replacing the polynomial variable by a single rational number. Different integer energy polynomials can have the same rational value. Indeed, the example below has two different maximum degrees and an equal first coefficient at the project's working value \(q=1/2\).

Nevertheless, sufficiently concentrated height profiles leave a recoverable denominator signature. The signature is not the whole degree distribution. It is the largest degree and the number of vertices having that degree. The decoder needs only one rational coefficient, the graph order, and the declared pinning parameter. It does not receive the graph, the coefficient's energy support, a marked series, or a second value of \(q\).

The same argument applies directly to the dominating-terminal interior sequence already used by the charge interface. Introduce an integer diagonal shift \(\lambda\ge0\) and write

\[
F_{G,\lambda}(x,q)
 =\sum_{h\in\mathbb Z_{\ge0}^{n}}
 x^{\sum_vh_v}\,
 q^{E_G(h)+\lambda\sum_vh_v^2},
\qquad
E_G(h)=\sum_{uv\in E(G)}(h_u-h_v)^2.
\]

The case \(\lambda=0\) is the raw local series \(L_G\). The case \(\lambda=2\) is the existing interior series \(A_G\) for two dominating terminals. This is the diagonal pinning already present in that interface, rather than a new observation variable. Define

\[
a_R(G;q,\lambda)=[x^R]F_{G,\lambda}(x,q),
\qquad
\Delta=\max_v\deg_G(v),
\]

\[
m=\#\{v:\deg_G(v)=\Delta\},
\qquad c=\Delta+\lambda.
\]

Every graph in this note is finite, simple, undirected, and has known order \(n\ge1\). The supplied coefficient is a coefficient of the full nonnegative-height series. Multiplying by \(1-x^n\), imposing minimum zero, restricting span, or changing to componentwise normalization changes the input and is outside the decoder's contract.

## 2. The concentration gap

**SNG-R02.1 — Extremal-energy gap.** Let \(R\ge2\). If \(c\ge1\), the largest exponent in \(a_R(G;q,\lambda)\), considered as a polynomial in \(q\), is

\[
K=cR^2,
\]

and its coefficient is exactly \(m\). Every other exponent is at most \(K-g\), where

\[
\boxed{g=\min\{R^2,\;2c(R-1)\}.}
\]

To see this, expand the quadratic form as

\[
E_G(h)+\lambda\sum_vh_v^2
 =\sum_v(\deg_G(v)+\lambda)h_v^2
   -2\sum_{uv\in E(G)}h_uh_v
 \le c\sum_vh_v^2.
\]

All heights are nonnegative, so the last edge term can only lower the energy. Placing the entire volume at a vertex of maximum degree gives energy \(cR^2\). There are exactly \(m\) such labeled assignments. No division by graph automorphisms is involved.

There are two other kinds of assignment, and both must be considered. A spike placed at a lower-degree vertex has energy at most \((c-1)R^2\), hence gap at least \(R^2\). An assignment with at least two positive coordinates satisfies

\[
\sum_vh_v^2\le(R-1)^2+1
 =R^2-2(R-1),
\]

because concentrating all but one of the units in a single coordinate maximizes that sum. Its energy is at most \(cR^2-2c(R-1)\). Taking the smaller of the two guaranteed gaps proves the result.

The minimum in the displayed formula is essential. A large maximum degree does not make a lower-degree spike disappear. For example, at \(R=2\) a maximum-degree-four vertex and a degree-three vertex produce spike energies separated by only four, even though the nonsingle-spike bound alone would suggest a gap of eight. The implementation has an explicit regression test for that case.

If \(c=0\), then \(\lambda=0\) and \(G\) is edgeless. Every profile has energy zero, and

\[
a_R(G;q,0)=\binom{n+R-1}{R}.
\]

This case is handled separately. An edgeless graph with \(\lambda=2\) belongs to the nondegenerate \(c=2\) case and must not use the unpinned edgeless shortcut.

## 3. A denominator invariant without factoring the denominator

Fix a reduced rational

\[
q=A/B,\qquad 0<A<B,\qquad \gcd(A,B)=1.
\]

The integer \(B\) may be composite. For an integer \(u\ne0\), let

\[
\operatorname{ord}_B(u)=\max\{r\ge0:B^r\mid u\}.
\]

For composite \(B\), this is a divisibility depth and should not be confused with a valuation: in general it is not additive under multiplication. What we use is only that multiplying by a unit modulo \(B\) preserves this depth.

For a positive reduced denominator \(D\), define its clearing depth

\[
\kappa_B(D)=\min\{k\ge0:D\mid B^k\}.
\]

If no such integer exists, \(D\) contains a prime absent from \(B\) and cannot occur in a coefficient of this rational specialization. The following procedure computes the clearing depth without factoring either integer:

\[
D_0=D,
\qquad
D_{r+1}=D_r/\gcd(D_r,B),
\]

stopping when \(D_r=1\). If \(D_r>1\) and its gcd with \(B\) is one, the procedure rejects. For justification, if a prime occurs in \(D\) with exponent \(e\) and in \(B\) with exponent \(b>0\), each step removes up to \(b\) copies of that prime. It disappears after exactly \(\lceil e/b\rceil\) steps. Thus the total number of steps is the least exponent whose power of \(B\) contains the entire denominator. Factoring is useful for this proof but is not performed by the algorithm.

For example,

\[
\kappa_6(72)=3,
\qquad
\kappa_{12}(8)=2,
\qquad
\kappa_{12}(18)=2.
\]

Taking a single prime valuation or treating \(B\) as prime would give the wrong general API.

## 4. The inverse theorem

Choose any \(R\ge2\) satisfying the strict inequality

\[
\boxed{B^{2(R-1)}>n.}
\]

Let \(D\) be the positive reduced denominator of the exact rational coefficient \(a_R(G;A/B,\lambda)\), and put \(k=\kappa_B(D)\).

**SNG-R02.2 — Single-coefficient rational recovery.** With the hypotheses above,

\[
\boxed{
\Delta=\left\lceil\frac{k}{R^2}\right\rceil-\lambda
}
\]

except that the unpinned edgeless case has \(k=0\), \(\Delta=0\), and \(m=n\). Once \(\Delta\) is recovered and \(c=\Delta+\lambda\ge1\), put

\[
K=cR^2,
\qquad
g=\min\{R^2,2c(R-1)\},
\]

\[
M=B^g,
\qquad
N=B^K a_R(G;A/B,\lambda)\in\mathbb Z.
\]

Then

\[
\boxed{
m\equiv N(A^K)^{-1}\pmod M,
\qquad 1\le m\le n<M.
}
\]

Consequently the least nonnegative residue on the right is the actual multiplicity, not merely a congruence class containing several admissible values.

**Proof.** The concentration gap gives

\[
N=mA^K+B^gT
\]

for some integer \(T\): every term below the leading exponent contributes at least \(g\) powers of \(B\) after multiplication by \(B^K\). Because \(R\ge2\) and \(c\ge1\),

\[
g\ge2(R-1),
\qquad
B^g>n\ge m.
\]

Write \(h=\operatorname{ord}_B(m)\). The last inequality gives \(h<g\). The leading summand has exactly divisibility depth \(h\), since \(A\) is coprime to \(B\); the other summand is divisible by \(B^g\). After division by \(B^h\), the first summand is nonzero modulo \(B\), whereas the second is zero modulo \(B\). Hence

\[
\operatorname{ord}_B(N)=h.
\]

No additivity assertion about composite-base divisibility depth has been used.

Now \(a_R=N/B^K\). For every \(0\le r\le K\), the rational number \(B^r a_R\) is an integer exactly when \(B^{K-r}\mid N\). Its first integral value therefore occurs at \(r=K-h\), so

\[
k=K-h=cR^2-h.
\]

Moreover \(B^{2(R-1)}>n\ge m\) implies \(h<2(R-1)<R^2\). Thus

\[
(c-1)R^2<k\le cR^2,
\]

which proves \(c=\lceil k/R^2\rceil\), and subtraction of the declared shift gives \(\Delta\). Finally reduce the congruence for \(N\) modulo \(B^g\) and invert \(A^K\), which is a unit modulo \(B^g\). Since \(m\le n<B^g\), the residue is unique in the admissible range. This proves the multiplicity formula.

The smallest permitted observation volume is

\[
R_*(n,B)=\min\{R\ge2:B^{2(R-1)}>n\}.
\]

It grows logarithmically with known order for fixed \(B\). The code finds it using integer multiplication, avoiding logarithm rounding at the strict boundary. Larger supplied volumes are valid as well.

## 5. What this says about fixed-pinning completeness

For known order and the same declared shift, equality of the entire fixed-rational series forces equality of \(\Delta\) and \(m\), because equality includes the coefficient at \(R_*\). In fact, agreement at that single coefficient is enough for these two invariants. Thus any proposed full-series collision with different maximum degrees, or different numbers of maximum-degree vertices, is impossible.

This statement is useful both for \(L_G\) and for the fixed-pinning interior sequence \(A_G\). It supplies a genuine necessary condition for future collision searches without confusing a finite observation with full equality. The conclusion goes only one way:

\[
F_{G,\lambda}(x,A/B)=F_{H,\lambda}(x,A/B)
\quad\Longrightarrow\quad
(\Delta_G,m_G)=(\Delta_H,m_H)
\]

when the graph orders agree. Equal recovered extrema do not imply equal series, equal graphs, equal degree distributions, or equal component structure. No such converse is asserted.

Known order is part of the input. This theorem does not infer the number of vertices from one coefficient, and it does not compare series with different numbers of vertices by silently inserting isolated vertices. Diagonal shift is also part of the input: \(A_H\) and \(L_H\) must not be decoded using each other's convention.

## 6. A first-coefficient collision that the decoder resolves

Let \(G\) be the complete multipartite graph with twelve singleton parts and two parts of size three. Let \(H\) be the complete multipartite graph with nine parts of size two. Both have order eighteen. Their degree data are

| Graph | Maximum degree | Multiplicity | Other degrees |
|---|---:|---:|---|
| \(G=K_{1,\ldots,1,3,3}\) | 17 | 12 | Six vertices of degree 15 |
| \(H=K_{2,\ldots,2}\) | 16 | 18 | None |

At \(q=1/2\), the first coefficients agree exactly:

\[
[x]L_G
 =12\cdot2^{-17}+6\cdot2^{-15}
 =18\cdot2^{-16}
 =[x]L_H
 =\frac9{32768}.
\]

This is a concrete warning against reading a specialized degree polynomial as if its exponents remained visible. For order eighteen, the recovery cutoff is \(R_*=4\). Exact independent enumeration at that volume gives:

| Quantity | \(G\) | \(H\) |
|---|---:|---:|
| Profiles enumerated | 5,985 | 5,985 |
| \(R^2\) | 16 | 16 |
| Leading energy \(K\) | 272 | 256 |
| Reduced denominator clearing depth \(k\) | 270 | 255 |
| \(\lceil k/16\rceil\) | 17 | 16 |
| Guaranteed gap \(g\) | 16 | 16 |
| Residue modulus \(2^g\) | 65,536 | 65,536 |
| Recovered multiplicity | 12 | 18 |

The denominator-depth losses of two and one are exactly \(\operatorname{ord}_2(12)\) and \(\operatorname{ord}_2(18)\). The numerator congruence recovers the multiplicities despite that cancellation. The retained JSON contains both full rational coefficients; this table omits their long numerators only to keep the mathematical mechanism visible.

## 7. A restricted reconstruction theorem beyond cycle interiors

Consider the complete split graph obtained by joining a clique of size \(c\) to an independent set of size \(n-c\). The word "complete" here describes the full join: every clique vertex is connected to every independent vertex. The family is a strict subclass of the split graphs and is not the family of all graphs admitting a clique/independent partition.

If \(0<c\le n-2\), the clique vertices have degree \(n-1\), whereas the independent vertices have degree \(c\). Thus

\[
\Delta=n-1,
\qquad m=c.
\]

The case \(c=0\) is edgeless. The presentations \(c=n-1\) and \(c=n\) describe the same complete graph, so the canonical answer for a complete graph is \((c,n-c)=(n,0)\). With this convention, the recovered extremum identifies the isomorphism type throughout this known-order family, using one rational coefficient at \(R_*\). The same is true using its pinned \(A_H\) coefficient at shift two.

**SNG-R02.3 — Complete-split reconstruction.** Within the declared known-order complete-split family, either the raw local coefficient or the shift-two pinned coefficient at \(R_*\) uniquely determines the graph up to isomorphism. The reconstruction consists of the arithmetic decoder followed by the elementary degree cases above.

The caller must supply the family-membership hypothesis. An arbitrary graph can share the same extremal degrees with a complete split graph. The software therefore does not claim to recognize complete split graphs from this invariant alone.

This is a reconstruction result beyond cycle interiors, but it is deliberately limited. These graphs are highly structured; their isomorphism types are controlled by a single nontrivial integer parameter. The theorem does not supply a universal graph reconstruction algorithm or an efficient coefficient compiler for arbitrary dense graphs.

## 8. Computation, reproducibility, and cost

The implementation uses only Python's standard library. The public decoder in `denominator_recovery.py` takes `order`, exact rational `q`, exact rational `coefficient`, an optional declared `volume`, and nonnegative integer `diagonal_shift`. It rejects floating point input and booleans, checks the strict observation cutoff, bounds denominator clearing depth by the maximum possible diagonal energy, and validates that the recovered multiplicity lies between one and the supplied order. These are useful consistency checks, not a complete recognizer for graph-realizable rational coefficients.

The companion receipt enumerates every labeled simple graph through order five: 1,099 graphs. For each graph it uses \(q=1/2,2/3,5/6\), with both shifts zero and two. This gives 6,594 exact decoder comparisons and 138,570 height-profile evaluations. The population oracle uses stars-and-bars separator positions and direct edge energy. It does not call the decoder to compute a coefficient, nor does it infer the expected answer from denominator data. The expected maximum degree and multiplicity come directly from graph adjacency.

| Evidence | Declared population or purpose |
|---|---|
| Exhaustive receipt | All labeled simple graphs of orders 1–5; three rational pinnings; shifts 0 and 2 |
| Focused unit population | All labeled graphs of orders 1–4, both series, all three pinnings |
| Composite denominator cases | Uneven prime exponents in clearing depth; multiplicities divisible by the full composite base |
| Degenerate cases | One vertex, edgeless unpinned series, edgeless pinned series |
| Gap regression | Lower-degree spike controls the gap when the nonsingle bound is too large |
| Family reconstruction | All complete-split parameters through order seven, with canonical complete graphs |
| Retained collision | Two order-eighteen multipartite graphs with equal first coefficient |

The exact coefficient can still be expensive to obtain. Direct enumeration uses

\[
\binom{n+R-1}{R}
\]

profiles at a fixed volume. A logarithmic observation index therefore does not imply a polynomial-time coefficient algorithm in the graph order. The rational coefficient also has substantial bit length: its unreduced denominator divides \(B^{(n-1+\lambda)R^2}\). The arithmetic decoder operates on that exact input. It does not turn approximate decimal measurements into exact denominator data, and its guarantee is not a robustness statement under measurement error.

Reproduction commands from the repository root are:

```sh
PYTHONPATH=src python -m unittest discover -s tests -p test_denominator_recovery.py -v
PYTHONPATH=src python scripts/fr02_denominator_recovery.py --check
```

The receipt is `results/fr02_denominator_recovery.json`. Re-running the script without `--check` regenerates it deterministically.

## 9. Follow-on questions without claiming their answers

The theorem naturally suggests asking which other extremal statistics can be recovered after rational specialization. Peeling the leading energy term from one coefficient is insufficient to recover a whole degree distribution: lower-energy nonsingle profiles overlap the contributions from lower-degree spikes, and subtraction must respect that interference. A valid next theorem would need a second isolation argument, rather than a repeated invocation of this one.

The coefficient's numerator is as important as its denominator. Denominator depth identifies the leading diagonal size up to cancellation by its multiplicity; the residue then removes the cancellation. This pattern may be useful for other finite lattice populations with an isolated extremal energy, provided one proves an explicit gap and a uniform bound on its leading multiplicity. That is a general method to investigate, not an already established extension to arbitrary interactions.

For the present fixed-pinning frontier, the immediate contribution is precise: any equal full pinned sequence at rational \(q\) and known order must preserve maximum degree and its multiplicity. Candidate searches can impose these two conditions before expensive coefficient comparisons. The complete-split family is reconstructible from the resulting arithmetic data. The larger questions of general completeness, a genuine full-series collision, and the realization of symmetric-interface ambiguities remain open.
