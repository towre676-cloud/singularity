# Source-bound distant response queries (NX11)

For one fixed finite linear state system, initial state and scalar output,

\[
s_n=CA^n x_0,\qquad S(z)=C(I-zA)^{-1}x_0=P(z)/Q(z),\qquad Q(0)=1.
\]

This coefficient index is physical discrete time (or a repeated-block index). It is not the graph-height volume index. Nothing in this adapter asserts rationality for a general positive-\(q\) graph-height series.

## Actual upstream reuse and indexing

The optional source-pinned adapter calls DynaComp `generating.from_state`, which derives a denominator by exact Faddeev–LeVerrier arithmetic and cancels common factors. It retains the normalized rational GF packet, its autonomous realization, initial prefix and a nonzero minimal Hankel determinant. Replay first checks the source matrices and their hash, then recomputes the GF from those matrices, then checks the packet. A recurrence fitted to a sample prefix would not suffice.

A unit impulse in \(x_{t+1}=Ax_t+Bu_t,\ y_t=Cx_t\), with zero reset, yields \(y_0=0\) and \(y_{n+1}=CA^nB\). The extra factor \(z\) is therefore real. The autonomous sequence \(CA^nx\) is not silently reinterpreted as an impulse transfer sequence. Direct feedthrough, when present in a source interpretation, must be represented explicitly. Tests retain an exact delayed impulse example and zero/finite-transient cases.

For held input \(u\), the source-state compiler uses the affine lift

\[
H_u=\begin{pmatrix}A&Bu\\0&1\end{pmatrix},\qquad
x_{\rm lift,0}=\binom{x_0}{1},\quad C_{\rm lift}=(C,0).
\]

The lift is used for sequence generation, not submitted as a Schur-stable matrix. A repeated block is composed chronologically using upstream `fastforward.compose`. Observation phase changes both the output row and its offset. The receipt records block length and phase, and independent neighbour-flux stepping checks every block index 0 through 32 for two real 4-by-4 candidate sources.

## Difference cancellation and all-index equality

Compile both exact fractions and subtract. The common numerator/denominator cancellation is performed symbolically upstream. A zero reduced numerator proves equality at every index under the declared reset/input/output semantics. An invisible third mode disappears in the retained tests. A pair of two-mode responses sharing the \(1/2\) mode reduces from a four-state block sum to two scalar modes. This is fixed-family equality, not every-input equivalence.

For \(A=\operatorname{diag}(1/2,1/3)\), \(x=(1,1)\), \(C=(1,-1)\),

\[
S(z)=\frac{z/6}{1-5z/6+z^2/6},\qquad
s_n=2^{-n}-3^{-n},\qquad
\det\begin{pmatrix}0&1/6\\1/6&5/36\end{pmatrix}=-1/36.
\]

Independent closed-form arithmetic checks all indices 0 through 32. The recurrence convention is chronological: \(s_{n+2}=\frac56s_{n+1}-\frac16s_n\).

## Resource contract and finite experiment integration

Binary powering uses logarithmically many stages, but rational numerator and denominator bit lengths can grow linearly with the index. The public query performs a conservative source-derived bit preflight and enforces an explicit final output-bit budget. A refused query is a resource limit. It is not a zero reading and not evidence of a physical ambiguity. The two-mode query at \(10^{100}\) is refused as an explicit rational value.

A separately labelled modular query requires every rational denominator to be invertible modulo the declared modulus. Matrix powering then returns only a residue. The receipt's huge-index check modulo 101 is independently compared with modular powers of 2 and 3. Such a residue is not a real observation and cannot certify a physical noise margin.

`remote_panel_pool` exposes exact queried readings at a supplied finite set of indices to the existing panel optimizer. It preserves the source candidate ordering separately from the backend's numeric candidate count. Its objective includes declared reset and elapsed costs. The result is optimal in this finite menu, not all horizons; NX10 supplies separate all-horizon stopping arguments.

Compilation/setup and repeated queries are different costs. The retained accounting example uses setup 100, compiled query one and direct query ten. One compiled query costs 101 versus ten, so setup dominates. The first strict break-even is twelve queries because \(100+N<10N\) exactly when \(N>100/9\). This is an explicit rational accounting illustration, not a benchmark claim. A separate benchmark report records actual compilation, cold query, warm queries and output bits without polluting deterministic scientific receipts.

## Portable replay

`response_receipt` uses canonical integer numerator/positive-denominator pairs. `replay_remote_receipt` rejects extra top-level fields, noncanonical rationals, incompatible source bindings, modified fractions, malformed indices and unknown arithmetic modes. Full source-state or recursive pair-difference evidence travels with the receipt. The upstream source digest binds executable bytes; actual recomputation establishes the identities. Public exact inputs reject booleans, floats and unchecked numeric strings.

Run `python scripts/nx_decision_recovery.py --track NX11 --check` and `python -m unittest tests.test_remote_queries`.

The retained actual timing example is deliberately unfavorable to distant GF evaluation at index 128: source-pinned per-query replay is more expensive than independently stepping this two-mode scalar source. The measured break-even is therefore absent. The report also records an index-one case where compilation plus checked query greatly exceeds direct stepping. This is an honest setup-dominance result; the logarithmic algebraic powering theorem alone does not imply a wall-clock speedup at these small horizons.

Physical maps are part of the source binding. A repeated block of length \(L\) and phase \(j\) has map \(t(k)=Lk+j\). Progression sampling composes maps exactly. A finite pool rejects mixed maps or incompatible sample conventions and prices the actual physical index as reset plus elapsed price times \(Lk+j\), rather than silently charging only the block counter.
