# NX17 — Exact low-rank physical fault transport

This release implements NX17-A/B/C for a declared finite-horizon, source-derived discrete thermal model. It establishes exact algebra and reuse costs, not continuum calibration or measured physical diagnostic performance. The reference source is `applications/thermal_diagnostics/source_fixture.json`; the receipt pins its SHA256. Graph-height populations and thermal state dynamics remain separate mathematical models.

## Model and sign

A thermal candidate is the existing `AffineCandidate` contract
\[
 x_{t+1}=Ax_t+Bu_t,\qquad y_t=Cx_t.
\]
For the plate, \(A_0=I-kL-\ell I\), \(k=1/8\), \(\ell=1/100\). For a physical bond with column \(b=e_u-e_v\), removing conductance \(\delta\in[0,k]\) means
\[
 A_f=A_0+\delta bb^T.
\]
The positive diagonal update and negative off-diagonal update preserve every row sum \(1-\ell\), preserve symmetry, and preserve the heater and sensor definitions. `BondFault` canonically stores the unordered original endpoints; orientation reversal does not change its meaning. Repeated declarations of one bond add severities, and their sum must not exceed the nominal available symmetric positive coupling. Zero severity is valid. The original fault ID remains an application-level population identity: no models are deduplicated merely because outputs coincide.

## Formal Sherman–Morrison and Woodbury

Write \(R_0(z)=(I-zA_0)^{-1}\). Formal inversion is valid because the constant matrix is the identity. The exact rank-one formula is
\[
 R_f=R_0+\frac{z\delta R_0bb^TR_0}{1-z\delta b^TR_0b}.
\]
Consequently the sensor correction is
\[
 \Delta H(z)=\frac{z\delta(CR_0b)(b^TR_0B)}{1-z\delta b^TR_0b}.
\]
`bond_transfer_factors` retains all factors through the requested horizon, including the unit-constant scalar denominator. These are truncated formal series; they are not evaluations at an unguarded numerical \(z\), and they are not claimed to be factored exact rational functions.

For selected bond columns \(U\) and their diagonal severity matrix \(D\),
\[
 R_f=R_0+zR_0UD(I-zU^TR_0UD)^{-1}U^TR_0.
\]
This formula handles zero severities and dependent bond columns. The factor order is significant. In particular the inner matrix is \(I-zGD\), not a casually reordered product.

## Coefficient implementation and proof

The implementation uses a small Volterra system, coefficient-wise equivalent to the Woodbury inverse. Let
\[
 v_j(t)=b_j^TA_0^tB,\quad G_{ji}(t)=b_j^TA_0^tb_i,\quad
 c_{si}(t)=C_sA_0^tb_i.
\]
Duhamel's identity follows by induction from \(A_f=A_0+UDU^T\):
\[
 A_f^t=A_0^t+\sum_{r=0}^{t-1}A_0^{t-1-r}UDU^TA_f^r.
\]
Therefore, setting \(w_j(t)=b_j^TA_f^tB\),
\[
 w_j(t)=v_j(t)+\sum_{r=0}^{t-1}\sum_i\delta_iG_{ji}(t-1-r)w_i(r),
\]
\[
 C_sA_f^tB=C_sA_0^tB+
 \sum_{r=0}^{t-1}\sum_i\delta_ic_{si}(t-1-r)w_i(r).
\]
Every right side uses only earlier \(w\). Thus induction proves all retained impulse coefficients exactly. This is an independent reuse calculation, not simulation of another full faulted state matrix. The nominal heater powers and lazily requested nominal bond powers are shared across all queries.

For input words and a declared initial state,
\[
 y_T=\sum_{t=0}^{T-1}CA_f^{T-1-t}Bu_t+CA_f^Tx_0.
\]
`protocol_from_impulse` implements the convolution and accepts the explicitly supplied initial-state contribution. An initial-state response is computed by requesting the same transport with `input_vector=x0`. Input amplitudes may be arbitrary exact rationals, including negative diagnostic pulses; physical implementability is an application restriction.

## Acceptance evidence

| Unit | Retained evidence |
|---|---|
| NX17-A | Two-node full/half/zero blockage, orientation reversal, exact impulse cancellation, source sign and heater/sensor invariance; direct sparse powers and an independent neighbor-flux oracle |
| NX17-B | Every pair of six small-plate bonds at two severities; short arbitrary input words, nonzero initial states, symmetry and row sums; excessive total severity rejected |
| NX17-C | Every one of the 264 distinct bonds of the 12-by-12 plate at horizon six; four sensor channels, all seven retained impulse coefficients, exact direct original-model replay; all 264 reflection comparisons on invariant sensors |

The deterministic receipt is `results/fault_transport.json`; its benchmark is retained separately from the reproducibility-critical exact data. In one measured run the first population required about 1.47 seconds including nominal setup, compared with about 3.08 seconds for direct sparse impulse simulation. Recursive owned-cache storage was about 18.2 MB with shared Python object identities counted once. This is an object-graph memory measurement, not peak process RSS. Coefficient bit sizes and retained vector-cell counts are also recorded. The break-even calculation uses the measured setup and population-average query costs; it is machine-specific, and no universal speed theorem is asserted.

The cache has explicit horizon, selected-fault and retained-cell limits. These are resource refusals, not mathematical claims of non-identifiability. No uncertainty certificate is transported by this module: original interval/disturbance propagation remains the responsibility of the existing physical diagnostic contract. Individually stable static faults do not imply stability of adversarially switched faults.

Run `python scripts/fault_transport.py --check` to replay the whole population.
