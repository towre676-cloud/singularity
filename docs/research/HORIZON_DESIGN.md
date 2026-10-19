# All-horizon stopping certificates (NX10): response tails

**Status.** NX10-A remains complete. NX10-B and NX10-C now have separate acceptance tests and retained decision receipts in `results/nx_10_decision_recovery.json`; the original response-tail receipt is preserved. The all-horizon claims below are restricted to the declared fixed protocol, reset and scalar reading semantics.

## Setting

A step experiment applies a fixed input from a declared reset state:

\[
x_{k+1}=Ax_k+b,\qquad y_k=cx_k+e .
\]

When \(I-A\) is invertible, the unique fixed point is \(x^*=(I-A)^{-1}b\), and

\[
y_k=y_\infty+cA^k(x_0-x^*),\qquad y_\infty=cx^*+e .
\]

Contraction is tested on \(A\) itself, never on the affine lift, which always has eigenvalue one.

## Theorem (response tail)

Suppose:

- \(P\) is symmetric positive definite;
- \(\gamma^2P-A^{\mathsf T}PA\) is positive semidefinite;
- \(\rho^2\ge\gamma^2\) and \(\rho<1\).

Then for every \(k\ge T\),

\[
|y_k-y_\infty|\le K\rho^{\,k-T},\qquad K\ \ge\ \|c\|_{P,*}\,\|x_T-x^*\|_P ,
\]

where \(\|v\|_P^2=v^{\mathsf T}Pv\) and \(\|c\|_{P,*}^2=cP^{-1}c^{\mathsf T}\).

**Proof.** The semidefinite condition says \(\|Av\|_P^2\le\gamma^2\|v\|_P^2\le\rho^2\|v\|_P^2\) for every \(v\). Induction gives \(\|A^jv\|_P\le\rho^j\|v\|_P\). By Cauchy–Schwarz in the \(P\)-inner product, \(|cw|\le\|c\|_{P,*}\|w\|_P\). Apply this to \(w=A^{k-T}(x_T-x^*)\), using \(y_k-y_\infty=cA^{k-T}(x_T-x^*)\). The constant \(K\) is a rational upper enclosure of the square root, computed by `sqrt_up`. \(\square\)

In plain words: once a metric certifies that the error shrinks by a fixed factor each step, every future reading stays inside an explicit band around its limit. A finite prefix plus this band therefore describes every horizon, not just the computed ones.

## Exactness and certification

The certificate is exact in the following senses.

- **Semidefinite test.** The condition is tested exactly by clearing denominators and running fraction-free Bareiss elimination on the integer matrix \(s g^2P_I-tA_I^{\mathsf T}P_IA_I\).
- **Proposed metrics.** When \(P\) is not supplied, it is proposed by exact dyadic Smith doubling and then accepted only by that exact test.
- **Refusals.** Marginal or unstable matrices, such as eigenvalue \(\pm1\) or a diagonal block with value one, are refused with `not_schur_stable`. A failed proposal is reported as `proposal_failed`, not as instability.

## Evidence

`tests/test_horizon_design.py` compares the bound with independent forward iteration and exact closed forms:

- \(A=1/2\): \(y_k=2(1-2^{-k})\), with \(K=2\), which is sharp;
- \(A=-1/3\): \(y_k=\tfrac32(1-(-\tfrac13)^k)\);
- the non-normal matrix \(\begin{pmatrix}1/2&10\\0&1/2\end{pmatrix}\). Its free response \(y_k=10k\,2^{1-k}\) rises from \(0\) to \(10\) before decaying, and the certified band covers that transient.

The tests also cover tamper rejection: \(\rho^2<\gamma^2\), a failed contraction, a \(P\) that is not positive definite, a metric certified for a different matrix, and an altered serialized \(\rho\). `scripts/horizon_design.py --check` retains the steady outputs, \(\rho\), \(K\) and the bound check for the first 40 readings.

## Limitations

- **Experiment type.** Only fixed, constant-input step experiments with independent resets are covered.
- **Excluded inputs and histories.** Adaptive or switched inputs and shared physical histories are out of scope.
- **Conservatism.** For non-normal \(A\), \(\rho\) can be much closer to one than the spectral radius, which makes \(K\rho^k\) conservative.
- **Formal status.** None of this is formalized in Lean.


## NX10-B: decision-level proof and independent scalar examples

A checked prefix and a proved future bound perform different jobs. For minimum elapsed cost, the first strict separating index is globally cheapest in that fixed family because `IndexCost.per_index` is positive. Every earlier index has been checked exactly. An external incumbent accounting cutoff can only be used when that incumbent is already known feasible; the bare price is not itself a physical feasibility proof.

For maximum certified margin, write

\[
m(k)=|\delta(k)|-\rho_a(k)-\rho_b(k).
\]

After exact states at index \(T\), the tail engine bounds all later deviations by \(U_{\rm after}(T)\). Together with a lower bound on the declared future radius envelopes,

\[
\sup_{k>T}m(k)\le |\delta_\infty|+U_{\rm after}(T)
-\inf_{k>T}(\rho_a(k)+\rho_b(k))=:F(T).
\]

If \(F(T)\) is no greater than the best checked prefix margin, the global optimal value is attained by a recorded prefix index. A strict inequality also excludes later ties. If \(F(T)-m_{\rm best}\le\varepsilon\), the retained finite index is epsilon-optimal even when no finite exact maximum exists. Its receipt says `supremum_bracket`, not attained optimum.

The first independent scalar example has steady outputs both equal to one and difference magnitude \(2^{-k}-3^{-k}\) for \(k\ge1\). Its successive difference is

\[
-\tfrac12 2^{-k}+\tfrac23 3^{-k}<0\quad(k\ge1),
\]

so the exact global maximum is at index one. At \(k\ge6\), the independent inequality \(2^{-k}+3^{-k}<1/50\) proves late-time impossibility with radius \(1/100\) under each candidate. The tests verify both the optimal finite index and the late-time stopping receipt.

A second example has difference \(1-2\cdot2^{-k}+3^{-k}\). It is below one at every finite index and tends to one. The retained response is therefore an epsilon-optimal finite experiment with explicitly unproved attainment. No finite-prefix heuristic is used to assert the supremum.

The optional pair quotient is derived from a finite exact source system and checked against that source for enough terms to invoke Cayley–Hamilton. For source dimensions \(n_a,n_b\) and quotient order \(r\), the difference between source and quotient sequences obeys a monic recurrence of order at most \(n_a+n_b+r\). That many consecutive exact zeros imply all-index equality. A fitted recurrence without this source-derived identity check would be insufficient. In the reflected blocked-bond symmetric sensor example, the checked quotient has order zero and certifies exact equality for the fixed protocol family.

Radius envelopes are declared upper bounds for uncertainty. A `never_separating_after` conclusion means that no later reading meets this certified separation test. Physical overlapping-box impossibility is asserted only through the separately attainable sensor component and the receipt's `indistinguishable_all_indices` flag. A loose computational or process upper bound alone does not establish actual physical ambiguity.

## NX10-C: source-derived thermal blocks

The additional receipt considers at most four candidate pairs on the synthetic 4-by-4 plate and two fixed chronological blocks, \((1,0)\) and \((1,1,0)\). Each block compiler records phase and uses its exact affine block map. Every recorded short output is independently checked by conservative neighbour-flux stepping. Tests also exercise every within-block phase on the nominal, heater-half and two reflected blocked-bond candidates.

For these symmetric nonnegative source stencils, a row-sum bound suggests \(P=I\) and norm factor at most \(99/100\) per update. The implementation still performs the exact matrix contraction acceptance test. Block factors use \((99/100)^L\), with the squared metric convention retained. Individual stability is never promoted to arbitrary-switching stability.

The receipt retains feasible finite decisions and inconclusive tails. Every result states actual prefix and metric effort. The comparison has no calibrated seconds, continuum-error claim, arbitrary-input optimum, multitime-panel guarantee or adaptive-policy guarantee. It accompanies the finite pool with a separately proved fixed-family stopping decision.

Replay the new decisions with `python scripts/nx_decision_recovery.py --track NX10 --check` and `python -m unittest tests.test_horizon_decisions`.
