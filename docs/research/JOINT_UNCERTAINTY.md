# NX02: exact joint observation geometry

This module completes the three NX02 units with a bounded exact rational engine,
a complete finite panel optimizer and a source-derived thermal pilot. Its
uncertainty sets are deterministic sets, not covariance matrices or probability
laws. The guarantee is relative to the stated affine nuisance model.

## Contract and data orientation

`JointObservationFamily` records original candidate identifiers, ordered
experiment identifiers, positive rational experiment costs, target labels,
candidate-major central vectors and candidate-major generator matrices. For
candidate c, its possible panel observations are

\[
Y_c=\mu_c+G_c[-1,1]^{m_c}.
\]

Generator columns, rather than rows, identify nuisance sources. A persistent
offset has the same column in every reading coordinate. A separately reset
initial condition has its own column block for that experiment. A sensor error
has a separate diagonal column. `source_labels` identifies these distinctions;
projection selects rows while retaining the complete generator-column identity.
The `exact_set` flag distinguishes an exact affine image from a deliberately
conservative enclosure. Every separation certificate remains safe for an outer
enclosure; overlap of that enclosure need not be physically realizable.

Each competing candidate receives its own nuisance vector. Reusing a source
label across hypotheses does not impose equality of its unknown value. The
possible-world quantifier is

\[
\exists\xi\in[-1,1]^{m_a},\ \eta\in[-1,1]^{m_b}:
\mu_a+G_a\xi=\mu_b+G_b\eta.
\]

Forcing xi=eta would change the model and could invent identification.

## Support and completeness theorem

**SNG-NX02-01.** For a rational contrast w,

\[
h_c(w)=\max_{z\in[-1,1]^{m_c}}w^TG_cz
=\sum_j|(G_c^Tw)_j|.
\]

Each coordinate z_j may independently choose the sign of its coefficient, so
the upper bound from the triangle inequality is attained. Consequently

\[
|w^T(\mu_a-\mu_b)|>h_a(w)+h_b(w)
\]

certifies disjoint sets. The strict inequality matters: equality can leave a
common boundary point and is rejected by the checker.

`joint_pair_certificate` solves the exact overlap problem, rather than merely
searching a list of sufficient contrasts. Set A=[G_a,-G_b] and b=mu_b-mu_a.
The solver converts Az=b and -1<=z<=1 into rational inequalities. It repeatedly
eliminates the last variable by pairing a positive-coefficient inequality with
a negative-coefficient inequality. A zero-coefficient inequality is retained.
If one side has no bound, elimination imposes no extra condition from that side.
These are exactly the conditions that the lower bounds on the eliminated
variable do not exceed its upper bounds. Induction proves equivalence of the
projected feasible set and the eliminated system.

Every generated row carries nonnegative multipliers on the original rows.
An impossible constant row therefore supplies an exact Farkas certificate.
For a feasible final system, back substitution selects zero where possible and
otherwise an available rational endpoint. The returned point is replayed against
every original inequality before being reported.

To obtain a separating contrast from an infeasibility certificate, let
lambda_i be the multiplier on the positive equality row minus that on its
negative copy. The nonnegative box-bound multipliers have total at least
||A^T lambda||_1, because their signed difference cancels A^T lambda. The
negative constant row implies

\[
\lambda^Tb+\textstyle\sum\text{bound multipliers}<0.
\]

Thus |lambda^T b|>||A^T lambda||_1. Splitting A into its two candidate blocks
gives exactly the support inequality above. This proves that, whenever the
bounded exact elimination finishes, the engine returns either a primal overlap
witness or a strict rational separating contrast. It does not depend on a
floating optimization status or a generic convex-separation assertion.

`verify_joint_certificate` checks the displayed affine equality and all nuisance
bounds, or independently recomputes the displayed support gap. Zero generators,
rank-deficient sets, point observations and touching sets are included.

## Complete finite panel optimization

`minimum_joint_panel` sorts every subset of the declared finite experiment pool
by total cost, then cardinality and index order. It checks all target-distinct
candidate pairs on each projected joint family. The first all-separated panel
is globally cheapest in that finite pool. Earlier failed panels retain overlap
certificates, and the successful panel retains strict contrasts. If no panel
works, all subsets have been exhausted. Joint separation is not a weighted
set-cover property: two individually ambiguous readings can jointly separate.

For exact observation sets these statuses are `optimal` and `impossible`.
For outer enclosures they are instead `optimal_for_outer_enclosure` and
`not_certified`: a physical optimum or physical impossibility does not follow
from optimizing over conservative sets. The result carries that scope explicitly.

The default subset budget is 4,096. The elimination budget is 20,000 generated
rows, including all positive-negative pairs before duplicate reduction. Either
budget can cause `GeometryBudgetExceeded`; that exception means no complete
verdict was obtained. Exponential elimination and subset selection remain real
limitations. Structural zero nuisance columns are eliminated internally and
their displayed overlap coordinates are restored as zero, preserving the
original generator/source contract.

## Persistent thermal nuisance pilot

`affine_protocol_family` derives the exact affine observation map for the
existing `AffineCandidate` dynamics. Its centers are the old simulator's values.
For every independently reset experiment and every initial cell, it propagates
a unit initial state through the zero-input linear dynamics. This yields the
initial-box generator columns. The heater contribution belongs to the center;
it is not accidentally added to the sensitivities. A persistent additive output
offset and fresh sensor errors occupy the explicitly labelled extra columns.
There is no uncertain multiplicative gain approximation in this adapter.

The retained four-by-four plate pilot compares the original left- and
right-blocked-bond models using the left and right center sensors after word
(2,0). Each experiment costs seven units under the original cost convention;
their separately reset joint panel costs fourteen. Each candidate has a
persistent offset bounded by 1/10 and independent sensor errors bounded by
1/10,000. The two candidate left-minus-right central contrasts are +1/32 and
-1/32. The persistent offset cancels, and each world's sensor-error support
in this contrast is 1/5,000. The strict gap is

\[
\frac1{16}-\frac2{5000}=\frac{621}{10000}>0.
\]

Each scalar interval overlaps, so the box outer approximation cannot identify
the pair using this pool. Replacing the persistent source by independent output
offsets produces a genuine overlap witness and invalidates the alleged joint
distinction. This adversarial comparison guards the modelling assumption that
creates the benefit. The source model is synthetic and source-pinned; these
uncertainty bounds are declared assumptions, not measured calibration.

## Independent checks and replay

The tests use an independently written active-vertex enumeration oracle for
small bounded polyhedra. It enumerates square active systems, solves them by
Gaussian elimination, then checks the original equalities and bounds; it never
calls production elimination. Twenty-four random pair instances agree, and
twelve three-candidate families compare the complete subset optimum against
independent pair feasibility. Separate tests cover false correlation, endpoints,
malformed shapes, zero generators and explicit budget refusal. The thermal map
is independently checked by substituting a nonzero reset cell, offset and
sensor-error assignment into the original simulator.

Run `PYTHONPATH=src python scripts/joint_thermal.py --check`. The receipt stores
the full family, all selected and cheaper rejected panel certificates, source
provenance, exact costs, maximum rational bit lengths and work limits.
