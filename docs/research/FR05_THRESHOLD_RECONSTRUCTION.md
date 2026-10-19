# FR05 — Fixed-rational reconstruction of threshold interiors

**Status:** proved under the stated threshold-class hypothesis, implemented with exact arithmetic, and checked against independent height populations. This companion uses the arithmetic extremum decoder of FR02. It neither implements an NX36 packet nor settles fixed-pinning completeness for unrestricted graphs.

## The inverse problem and its answer

Write

\[
 F_{G,\lambda}(x,q)=\sum_{h\in\mathbb Z_{\ge0}^{V(G)}}
 x^{\sum_vh_v}q^{E_G(h)+\lambda\sum_vh_v^2},
 \qquad E_G(h)=\sum_{uv\in E(G)}(h_u-h_v)^2.
\]

Here \(\lambda\) is a known nonnegative integer and \(q=A/B\in(0,1)\) is a known reduced rational, with \(B\ge2\). The raw local series is \(\lambda=0\); the dominating-terminal interior sequence already used in the project is \(\lambda=2\). Heights and assignment multiplicities retain their original meanings. No graph-isomorphism quotient enters the sum.

A threshold graph is obtained from one vertex by successively adjoining an isolated vertex or a vertex adjacent to every earlier vertex. Encode those choices by a binary creation word, choosing its first bit to be zero. This elementary characterization is classical; see Diaconis, Holmes and Janson, *Threshold Graph Limits and Random Threshold Graphs*, Internet Mathematics 5 (2008), 267–320, DOI [10.1080/15427951.2008.10129166](https://doi.org/10.1080/15427951.2008.10129166), also [arXiv:0908.2448](https://arxiv.org/abs/0908.2448). The arithmetic reconstruction below is derived here; no broad historical priority claim is made.

**Theorem FR05.1.** Suppose the unknown graph \(G\) is promised to be a threshold graph of known order \(n\ge1\). Define

\[
 R_* = \min\{R\ge2:B^{2(R-1)}>n\}.
\]

Then the exact coefficient prefix of \(F_{G,\lambda}(x,A/B)\) through volume \(R_*\) determines \(G\) up to isomorphism. An explicit algorithm reconstructs its canonical creation word using only \(n,q,\lambda\) and that prefix. Every peeling step uses the same supplied prefix budget: the observation cutoff never grows during reconstruction.

Equivalently, for two promised threshold graphs of the same known order,

\[
 [x^r]F_{G,\lambda}(x,q)=[x^r]F_{H,\lambda}(x,q)
 \quad(0\le r\le R_*)
 \quad\Longrightarrow\quad G\cong H.
\]

This is a completeness theorem within a specified graph class, rather than a report that a finite census happened to separate. Its cutoff is sufficient; no claim of minimality is made. For fixed denominator \(B\), it is \(O(\log_B n)\). The strict inequality matters: at \(q=1/2\), order 256 requires \(R_*=6\), whereas order 128 requires \(R_*=5\).

## Why the high-volume denominator reveals a layer

FR02 recovers the maximum degree \(\Delta\) and its multiplicity \(m\) from the single coefficient at any volume satisfying the cutoff. For clarity, its mechanism is restated in the form required here. Put \(D=\Delta+\lambda\). If \(D>0\), the maximum possible energy at volume \(R\) is

\[
 K=D R^2,
\]

attained exactly by placing all mass on one of the \(m\) maximum-degree vertices. For a profile with at least two positive coordinates,

\[
 E_G(h)+\lambda\sum_vh_v^2
 \le D\sum_vh_v^2
 \le D((R-1)^2+1).
\]

A spike at a lower-degree vertex instead loses at least \(R^2\) energy. Both alternatives must be included. Thus every nonleading profile lies at least

\[
 g=\min\{R^2,\ 2D(R-1)\}\ge2(R-1)
\]

below the leading energy. For \(a_R=[x^R]F_{G,\lambda}(x,A/B)\), clearing the full energy denominator gives an integer of the form

\[
 B^K a_R=mA^K+B^g T,\qquad T\in\mathbb Z.
\]

Because \(B^g>n\ge m\), the leading multiplicity cannot disappear arbitrarily far into a denominator cancellation. Let \(\kappa\) be the least nonnegative integer such that the reduced denominator of \(a_R\) divides \(B^\kappa\). Then

\[
 D=\left\lceil\frac\kappa{R^2}\right\rceil,
 \qquad \Delta=D-\lambda,
\]

and, once \(K\) and \(g\) are known,

\[
 m\equiv (B^Ka_R)A^{-K}\pmod{B^g},\qquad 1\le m\le n<B^g.
\]

The residue is the actual integer \(m\), not merely a congruence class left to guess. Coprimality of \(A\) and \(B\) makes the inverse valid, including composite \(B\). The edgeless unpinned case has \(D=0\) and is handled separately. This inversion depends on exact coefficients: floating approximations discard the denominator information that drives it.

## Two exact operations remove every threshold layer

The class structure supplies the interpretation of the decoded extremum. If \(\Delta=0\), the residual graph is edgeless. If \(0<\Delta<n-1\), all isolated vertices can be removed at once: their number is

\[
 k=n-\Delta-1.
\]

Indeed, after deleting trailing isolated additions from a threshold creation word, its last remaining addition is universal. That vertex is adjacent to every nonisolated vertex, so the nonisolated induced graph has order \(\Delta+1\). If \(\Delta=n-1\), the recovered multiplicity \(m\) is precisely the number of universal vertices, and those vertices form a clique.

The corresponding transformations of the series preserve the observation budget. These identities also explain why the uniform diagonal shift must be tracked rather than silently reset after a join.

| Layer | Graph identity | Series operation | New shift |
|---|---|---|---|
| \(k\) isolates | \(G=H\sqcup I_k\) | Divide by \(f_\lambda(x,q)^k\) | \(\lambda\) |
| \(m\) universal vertices | \(G=K_m\vee H\) | Invert the unit-triangular join transform | \(\lambda+m\) |
| Edgeless residual | \(G=I_n\) | Check the known isolated factor | Terminal step |

Here

\[
 f_\lambda(x,q)=\sum_{h\ge0}x^h q^{\lambda h^2}.
\]

Its constant coefficient is one, so division in the truncated formal-series ring is exact. If \(c_r=[x^r]f_\lambda^k\), the residual coefficients satisfy

\[
 b_0=1,\qquad
 b_R=a_R-\sum_{j=1}^R c_jb_{R-j}.
\]

For universal vertices, write their heights as \(u_1,\ldots,u_m\), with sum \(j\), and let the remaining heights have total volume \(k\). Expanding all clique and join edges gives

\[
 E_G(u,v)+\lambda(\sum_i u_i^2+\sum_wv_w^2)
 =E_H(v)+(\lambda+m)\sum_wv_w^2
 +(n+\lambda)\sum_i u_i^2-j^2-2jk.
\]

Consequently define

\[
 C_{m,j}^{(n,\lambda)}(q)
 =q^{-j^2}[z^j]\left(\sum_{u\ge0}z^u q^{(n+\lambda)u^2}\right)^m.
\]

If \(b_k=[x^k]F_{H,\lambda+m}(x,q)\), then

\[
 a_R=\sum_{j=0}^R C_{m,j}^{(n,\lambda)}(q)
 q^{-2j(R-j)}b_{R-j}.
\]

The coefficient of \(b_R\) is \(C_{m,0}=1\). The exact inverse is therefore

\[
 b_R=a_R-\sum_{j=1}^R C_{m,j}^{(n,\lambda)}(q)
 q^{-2j(R-j)}b_{R-j}.
\]

Negative displayed powers of \(q\) are evaluated as exact rationals. Their appearance in the transform does not change the underlying nonnegative energy of actual assignments. At \(q=A/B\), no numerical interpolation or rounding is involved.

## Proof that the algorithm terminates and is unique

Every iteration removes at least one vertex. Threshold membership is preserved by deleting isolated or universal vertices. The initial condition \(B^{2(R_*-1)}>n\) remains sufficient for every smaller residual order, so FR02 can be applied repeatedly at the same volume. The current shift remains a known nonnegative integer. Recovered layer counts are exact, and both series inversions are unit triangular. Induction on the remaining order proves that the residual series is the series of the residual threshold graph after each step.

The empty residual is represented by the formal series one. The implementation never instantiates a zero-vertex `Graph`, whose public contract requires positive order. Reversing the removed layers reconstructs the binary creation word; its first bit is set to zero because the first vertex has no earlier vertices. At every branch, the next layer is forced by \(\Delta\) and \(m\). This proves uniqueness of the resulting word and completes the reconstruction theorem.

The implementation uses an iterative loop rather than recursive function calls, so a long alternating creation word does not hit Python's recursion limit. This is an engineering detail with a mathematical consequence: there is no hidden finite layer bound in the implemented peeling procedure.

## A single declared closure reconstructs threshold interiors

**Corollary FR05.2.** Let a two-terminal block have nonadjacent terminals, each adjacent to every vertex of an unknown threshold interior \(H\) of known order \(n\). Use any fixed, known closing context covered by the existing SNG-F53/F54 raw-series convention. Its closure coefficients through the same cutoff \(R_*\) reconstruct \(H\) up to isomorphism.

Indeed, `charges.dominating_sequence` is exactly

\[
 A_H(x,q)=F_{H,2}(x,q).
\]

The implemented `closure_operator` gives \(Z_C=T_C A_H\), with \(T_C\) independent of the interior graph, lower triangular and unit diagonal. Its forward-substitution inverse recovers the \(A_H\) prefix at the original volume budget. Applying Theorem FR05.1 with \(\lambda=2\) completes the reconstruction. Consequently, two nonisomorphic threshold interiors of equal known order are distinguished by **each** such declared single closure by volume \(R_*\); no search over closing contexts is required. This statement concerns the proved raw closure operator, not an arbitrary renormalization, unproved observation chart or unspecified experimental language. It reuses the existing transport theorem rather than introducing another context compiler.

## A collision that a single low coefficient cannot resolve

At \(q=1/2\), the two order-eight creation words below give the same coefficient at volume one. This is a genuine limitation even inside the promised class.

| Canonical creation word | Degree multiset, in creation order | \([x]F_{G,0}\) | \([x^2]F_{G,0}\) |
|---|---|---|---|
| `01000011` | \(3,3,2,2,2,2,7,7\) | \(81/64\) | \(104955905/134217728\) |
| `01101110` | \(5,5,5,3,6,6,6,0\) | \(81/64\) | \(22368307/16777216\) |

The second coefficient separates this particular pair. The general theorem uses the sufficient volume-three prefix and reconstructs each entire graph. The receipt shows that volume-one signatures are distinct for all threshold graphs through order seven, but only 127 signatures occur among the 128 order-eight creation words. These finite counts motivate the theorem; they do not replace its proof.

## Implementation, evidence, and limits

`src/singularity/threshold_reconstruction.py` provides `reconstruct_threshold`, the creation-word constructor, isolated-factor division, and forward/inverse universal-clique transforms. The inverse function receives no graph. Its return value contains the reconstructed graph, canonical word, observation volume and a sequence of layer receipts. Exact integer and `Fraction` inputs are required; booleans, floats, malformed prefixes and insufficient observation cutoffs are rejected.

`tests/test_threshold_reconstruction.py` contains eight tests. Its independent oracle uses stars-and-bars height assignments and direct edge energies. It checks every creation word through order six at three rational pinnings and shifts zero and two, giving 378 reconstructions, and separately checks the join and isolated identities, strict validation, the retained collision, complete graphs, edgeless graphs and longer prefixes. An additional end-to-end test counts the actual raw glued graphs for both collision interiors under a terminal-edge context and a shared-neighbor context, then inverts the existing closure operator and reconstructs both words.

`scripts/fr05_threshold_reconstruction.py --check` replays the retained census through order ten. It covers all **1,023** canonical threshold creation words, at \(q=1/2,2/3,5/6\) and shifts \(0,2\), for **6,138 exact reconstructions**. Both graph construction and height-population enumeration are independent of the inverse operations. `results/fr05_threshold_reconstruction.json` stores the aggregate counts, the complete worked collision receipts, and four independently counted raw closure reconstructions.

The optional `--benchmark` mode retains larger exact algebraic roundtrips. It constructs a prefix by forward isolated/universal identities and decodes that prefix back to the original alternating word. This is a scale check of the proved transforms; it is explicitly **not** another independent population-enumeration oracle. The retained timings below are machine-specific, and `--check` does not rerun or compare their wall-clock values.

| Order | Volume cutoff | Prefix generation | Inverse decoding | Largest denominator, bits | Peeling steps |
|---|---|---|---|---|---|
| 128 | 5 | 0.026 s | 0.032 s | 3,176 | 127 |
| 256 | 6 | 0.261 s | 0.287 s | 9,181 | 255 |
| 1,000 | 6 | 7.662 s | 7.577 s | 35,965 | 999 |

The order-1,000 example illustrates both the benefit and the resource distinction: six exact nonconstant coefficients suffice, but those coefficients carry tens of thousands of denominator bits. A short observation prefix does not mean a low-precision experiment. Building the canonical graph object also explicitly produces its edges; that output cost must be included when comparing implementations.

The formal-series convolutions and inversions require \(O(nR^2)\) rational arithmetic operations with the elementary implementation, because the total number of removed vertices is \(n\). That bound excludes the separate denominator-depth decoder and the bit cost of rational arithmetic. The decoder's precise current arithmetic implementation belongs to FR02. Observation volume, input precision, coefficient acquisition and reconstruction time are distinct resources; this theorem bounds the first and gives an explicit algorithm for the last. It does not make exact coefficients easy to measure physically, nor does it bound the cost of obtaining them from an arbitrary unknown graph.

The graph-class promise is essential. Passing arithmetic checks does not certify that arbitrary supplied coefficients arise from a threshold graph. The decoder is not a general graph recognizer, and the theorem provides neither unrestricted fixed-pinning completeness nor a full-series collision outside the class. Its contribution is a new family beyond cycle interiors where a finite exact prefix has a proved inverse interpretation, with an observation budget that grows logarithmically in known graph order.
