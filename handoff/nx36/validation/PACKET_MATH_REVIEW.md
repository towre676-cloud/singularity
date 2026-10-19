# Independent mathematical review of NX31–NX36

## Scope and method

This review concerns the proposed handoff packets, not implementation of their future APIs. The reviewer read NX31 through NX36, inspected the cited Singularity source interfaces and formal coverage, and recomputed the displayed examples using Python standard-library `fractions.Fraction` and direct matrix arithmetic. The calculation did not import the implementation routines it was checking. SymPy was not installed and was not needed. No claim of formal verification, a new geometric-family result, or a full repository test run follows from this review.

The packet hypotheses are generally appropriately scoped. Historical period-engine descriptions are explicitly treated as context requiring source recovery. Proposed module paths are marked proposed. No missing path was found that was explicitly presented as an already-existing file. One existing-module capability cross-reference needs correction, and NX34 needs explicit analytic hypotheses and one stronger lower-bound phrase. These corrections were communicated to the primary agent; this report intentionally does not edit the packets.

## Review outcome table

| Packet | Core mathematics | Exact examples | Required clarification |
|---|---|---|---|
| NX31 | Differential observation recurrence and first-dependence closure are correct over the stated differential field. | Three-state example yields rows \((1,0,0),(0,1,0),0\), hence \(y''=0\). | Minimality concerns the connection module and chosen output, not every special solution; the packet already records this distinction. |
| NX32 | Chronological products, invariant row closure, and constant gauge law are correct. | Words 0 then 1 and 1 then 0 give states \((1,1)\) and \((2,1)\), readings 1 and 2. | Cheapest exact words live in `observability.minimum_distinguishing_experiment`; `experiment_design.rank_experiments` only ranks a supplied pool. |
| NX33 | Closure \(B'+BA=TB\), uniqueness under full row rank, and the derivative gauge term are correct. | Moving constant coordinate, leakage example, and gauge \(G=1+t\) all check. | Statements are chartwise and constant-rank; extension across rank drops is correctly left conditional. |
| NX34 | Coefficient majorant, tail, and Rouché mechanism are correct with explicit domain hypotheses. | Geometric example gives polynomial lower bound \(5/8\), tail \(1/8\), strict gap \(1/2\). | Require an admissible bounded contour/domain and \(\overline D\subseteq\{|z|\le r\}\), \(r<1\). A direct global lower bound must exceed the tail, not merely be positive. |
| NX35 | Certain/possible coverage inclusions and optimum sandwich are correct. | True optimum 2, initial optimistic lower bound 1, refined lower bound 2. | The theorem is for scalar-box pair masks; correlated panels require the different NX02 oracle, as already stated. |
| NX36 | Pairwise set disjointness gives target identification; feasibility and optimality are separate. | Interval gap is \(1/5\); changing an endpoint to create contact correctly invalidates strict separation. | Formal soundness must be restricted to the actual checker and its premises; the packet already avoids blanket Python or physical-model verification. |

## NX31: differential closure and target reduction

For \(\Pi'=A\Pi\) and a parameter-dependent row \(c\), the product rule gives \((c\Pi)'=(c'+cA)\Pi\). This validates the recurrence \(c_{j+1}=c_j'+c_jA\). Once the first row dependence occurs over \(K(t)\), the previous rows form a differential-stable span: differentiating a rational coefficient adds its derivative, and differentiating each retained row gives the next row or the displayed dependence. Thus the resulting scalar equation is valid for every solution of the supplied connection.

The packet correctly distinguishes this module-level order from the possibly smaller annihilator of one special initial vector. It also records excluded denominators and parameter pivots. On a regular chart, reduction identities can be checked by clearing denominators while preserving those exclusions; evaluating a cleared identity at a forbidden pole is not legitimate.

Independent arithmetic confirmed the nilpotent two-coordinate subsystem and the unused exponential third coordinate. The sample therefore tests a real reduction: the requested output needs both initial position and slope but is independent of the third initial component. No actual geometric connection or integral normalization is established by this toy calculation.

## NX32: chronological loops and gauge

The matrices are

\[
T_0=\begin{pmatrix}1&1\\0&1\end{pmatrix},\qquad
T_1=\begin{pmatrix}1&0\\1&1\end{pmatrix}.
\]

Direct multiplication gives \(T_1T_0(1,0)^\top=(1,1)^\top\) and \(T_0T_1(1,0)^\top=(2,1)^\top\). The output row \((1,0)\) reads one and two. Moreover \(cT_0=(1,1)\), so the direct row and this row span the full dual. This validates the intended order-sensitive fixture independently of graph attachment conventions.

An additional gauge replay used \(S=\begin{pmatrix}1&2\\0&1\end{pmatrix}\), its explicit integer inverse, transformed states \(Sv\), transformed rows \(cS^{-1}\), and transformed matrices \(ST_iS^{-1}\). Both chronological readings were unchanged. The packet's constant-basis law is correct; a parameter-dependent gauge for a differential connection requires the additional derivative term developed in NX33.

The opening cross-reference to `experiment_design.py` for affordable distinguishing experiments should be made precise. That module contains `rank_experiments`, which scores a fixed supplied pool by an explicit separation/cost/noise ratio. It does not enumerate all words or return a globally cheapest word. Use `observability.minimum_distinguishing_experiment` for exact cheapest distinctions and `robust_search.bounded_margin_search` or `bounded_family_search` for bounded single-experiment margin optimization.

## NX33: compatibility, leakage, and gauge

Differentiation gives \(z'=(B'+BA)x\). Since full-row-rank \(B\) is surjective, an exact law depending only on \(z=Bx\) exists precisely when \(B'+BA\) annihilates \(\ker B\), equivalently when it factors as \(TB\). Full row rank also makes \(T\) unique. This is an exact local linear algebra criterion with regularity of the selected chart, not a claim of a canonical global reduction.

For \(B=(1,t)\) and \(A=\begin{pmatrix}0&-1\\0&0\end{pmatrix}\), the sum is zero. For \(A=\operatorname{diag}(0,1)\), the sum is \((0,1+t)\), whose value on the hidden vector \((-t,1)^\top\) is \(1+t\). The isolated zero at \(t=-1\) does not produce neighbourhood closure.

With \(\widetilde B=GB\), expansion gives

\[
\widetilde B'+\widetilde BA
=(G'+GT)B
=(G'G^{-1}+GTG^{-1})\widetilde B.
\]

For \(G=1+t\) and original \(T=0\), the reduced connection is \(1/(1+t)\), exactly as stated. The source target also needs its independent factorization \(c=LB\); dynamic closure alone does not prove target retention. The packet includes this obligation correctly.

## NX34: coefficient tails and the nonvanishing argument

For a nonnegative integer-height counting series on a graph with \(k\ge1\) vertices and fixed \(q\in[0,1]\), the number of profiles of total volume \(n\) is \(\binom{n+k-1}{k-1}\). Every weight lies between zero and one, giving the coefficient majorant. For complex \(q\) with modulus at most one, the corresponding absolute-value majorant remains valid. Specify which local series is being bounded; an arbitrary ratio or logarithm does not inherit nonnegative coefficients automatically.

For \(0\le r<1\), subtracting the finite head from \((1-r)^{-k}\) is the exact majorant tail. The geometric example checks independently:

\[
\frac{1-(1/2)^4}{1+1/2}=5/8,
\qquad
\frac{(1/2)^4}{1-1/2}=1/8.
\]

The roots of \(1+z+z^2+z^3\) are the fourth roots of unity other than one, so none lies in the half-radius disc.

The Rouché statement should explicitly use a bounded Jordan domain, or another domain with an argument-principle-admissible boundary, with both functions holomorphic on a neighbourhood of its closure. Also require \(\sup_{\overline D}|z|\le r<1\), so the displayed tail actually bounds the boundary error. The polynomial zero count is a separate necessary premise, correctly emphasized in the packet.

One sentence needs strengthening: a positive lower bound for \(|P_N|\) throughout the domain proves only that the polynomial is zero-free. To deduce the infinite series is zero-free directly, that lower bound must strictly exceed the uniform tail. The correct inequality is \(\inf_{\overline D}|P_N|>T_N(r)\), giving \(|F_G|\ge\inf|P_N|-T_N(r)>0\).

The source has both real-axis tail helpers and `arithmetic.complex_disc_certificate`. Do not reuse a real-axis-only logarithmic estimate as a uniform complex-domain theorem without its holomorphic majorant argument. Small-prime nonvanishing and large-prime normal convergence remain distinct obligations. Fractional branch factors must retain a chosen cut and basepoint.

## NX35: optimistic and certain covers

From \(m^-\le m\le m^+\), strict positivity gives \(S^-\subseteq S\subseteq S^+\). Therefore an exact cover optimum computed with possible masks is a lower bound, while any actual cover of certain masks is a valid upper-bound witness. Equality certifies the concrete certainly feasible panel as optimal. This conclusion does not require the optimistic masks to be jointly realizable by one set of uncertain simulator values; granting impossible extra coverage only makes the lower bound weaker, not unsound.

Independent subset enumeration of the three-test fixture found the true optimum \((2,\{e_1,e_2\})\). Adding the unresolved pair to \(e_1\)'s possible mask gives lower bound one; excluding that pair after refinement returns lower bound two. A coarse oracle must actually retain the other positive and zero decisions as stated for this progression. Zero upper endpoints do not enter possible coverage because separation requires strict positivity.

No termination guarantee follows merely from increasing arithmetic precision. An exact zero margin, source-error floor, or unresolved model term can block classification. A valid work-limited output is an incumbent and certified gap. Joint correlated geometry falls outside the mask theorem, as the packet correctly states.

## NX36: certificate scope and existing formal claims

Every pair of target-distinct observation sets must be disjoint for guaranteed target identification. A compact scalar or contrast witness can prove that condition; proving no cheaper admissible panel works additionally needs a complete finite-catalogue lower-bound argument. The stated example's interval gap is exactly \(3/10-1/10=1/5\). Endpoint contact invalidates strictness.

The reviewed source contains `formal/Singularity/Operators.lean`, including `quotient_complete`, `affordable_basis_iff`, and `cheapest_witness`, with costs in `Nat`. This supports the packet's scoped claim that generic closure and natural-cost arguments already exist. It does not formally verify the Python search, rational scaling, arbitrary uncertainty propagation, physical calibration, or future decision checker. The packet explicitly separates those future obligations.

For a rational-to-natural cost adapter, the certificate should show a positive common denominator and order-preserving scaling of every relevant finite cost. Original candidate reconstruction, source binding, uncertainty contracts, reset semantics, and word order must agree across composed certificates. Hashes supply binding and integrity, not mathematical truth or authentication of a physical source.

## Opportunistic cross-packet checks

NX01's strict heterogeneous interval criterion and monotonicity against the old largest-radius envelope are correct. NX02's two-reading common-offset example has contrast magnitude two and total support radius \(2/5\), giving strict separation even though each coordinate overlaps. NX03's twelve-bond up-to-two count is 79, while all 264 plate bonds give 34,981 configurations; these remain original masks, not behavioral-class counts. NX04's scalar contrast gives a sufficient per-reading error threshold \(\delta<1/24\). NX05's four-candidate adaptive tree costs two and every two-test fixed subset fails; endpoint singleton cells are essential. NX06's shared-gain contrast gives the stated sufficient threshold \(\delta<1/12\), and its destructive-state example correctly preserves initial identity.

The six new tracks should remain pending. Their proof sketches and toy checks are an implementation specification, not evidence that all proposed engines or full-domain certificates have already been built.
