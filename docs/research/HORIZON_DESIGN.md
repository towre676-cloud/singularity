# All-horizon stopping certificates (NX10): response tails

**Status.** NX10-A, the constant-input response-tail certificates, is complete. NX10-B (horizon optimisation with future bounds) and NX10-C (thermal pairs and fixed blocks) are proposed. `src/singularity/horizon_design.py` already contains drafts of their search routines. Those routines are not covered by this unit's tests or receipt and carry no claim.

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
