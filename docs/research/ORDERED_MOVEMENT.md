# NX30 — Order-sensitive geometry with a finite uncertainty population

The ordered_movement module implements rational level-two signatures, exact phase populations and finite candidate separation. It does not claim that level two reconstructs every trajectory or improves scouting prediction.

## Geometric information that totals discard

For a piecewise-linear path,
\[
S^{(1)}_i=\int dX_i,\qquad
S^{(2)}_{ij}=\int_{s<t}dX_i(s)\,dX_j(t).
\]
Level one is displacement. Antisymmetry \(S^{(2)}_{ij}-S^{(2)}_{ji}\) is doubled signed area after straight-line closure. Units are products of channel units. Paths retain sampling times, interpolation convention, channel units and coordinate frame; signatures preserve frame identity. Composition across incompatible units or frames is rejected.

For signatures \((a,A),(b,B)\), Chen composition is
\[
(a,A)*(b,B)=(a+b,A+B+a\otimes b).
\]
A straight increment \(v\) contributes \((v,\frac12v\otimes v)\). Streaming therefore updates
\[
A\leftarrow A+\tfrac12v\otimes v+a\otimes v,\qquad
a\leftarrow a+v,
\]
using the old displacement \(a\). Updating displacement first introduces a wrong extra tensor term.

The independent integration oracle sums the triangular within-segment integral and every ordered pair of distinct segment increments:
\[
S^{(2)}=\frac12\sum_r v_r\otimes v_r+\sum_{r<s}v_r\otimes v_s.
\]
It does not reuse the streaming recurrence. Associativity follows from tensor expansion and is independently tested over three segments.

| Path | First level | Second level | Doubled area |
|---|---|---|---|
| right, then up | \((1,1)\) | \(\left(\begin{smallmatrix}1/2&1\\0&1/2\end{smallmatrix}\right)\) | \(1\) |
| up, then right | \((1,1)\) | \(\left(\begin{smallmatrix}1/2&0\\1&1/2\end{smallmatrix}\right)\) | \(-1\) |

Translation and monotone reparametrization preserve the geometric signature. Timing must be added as an explicit channel when the target uses timing. Reflection and path reversal fixtures retain sign conventions. None of these algebraic invariances makes an incorrectly calibrated camera trajectory physically accurate.

## Segmentation is a population, not one preferred answer

For at most eight candidate breakpoints and three phases, segmentation_population enumerates all admissible ordered cuts and retains their original identities, multiplicities, phase signatures and concatenated feature coordinates. The pilot budget is at most 1,024 variants. Population compression groups only complete signatures with identical units and coordinate frame, and retains every original identifier.

Full signatures are closed under future Chen composition. A smaller current summary may fail that closure: horizontal and vertical single-segment paths both have zero current area, but after appending the same vertical segment their future areas differ. They cannot be safely merged merely because one current feature agrees.

Finite feature uncertainty reports exact coordinate ranges and distinct attainable vectors. Weights are declared population weights, not biological probabilities. No independent feature box is substituted for correlated attainable variants. For two finite candidate sets with minimum squared distance \(\delta^2\), common Euclidean error radius \(\epsilon\) guarantees separation only when \(\delta^2>4\epsilon^2\). Shared attainable values and touching error balls are explicit refusal cases.

## Real trajectories and a preserved negative result

NX29's recovered official sources support the same frozen twenty-athlete, player-held-out comparison. One earliest valid attempt per athlete is extracted, so twenty attempts remain below the fifty-attempt cap. Each path uses at most 33 uniformly indexed samples, yielding at most 32 geometric segments, and carries official field coordinates in yards with elapsed time in seconds. Full attempts are available for offline scouting; this extraction is not advertised as causal real-time forecasting.

The same geometric channels support the order-insensitive baseline and ordered features. The baseline uses displacement, duration and path length; ordered features add antisymmetric x-y, x-time and y-time areas. A prespecified phase-weighted feature population over three phases supplies segmentation ranges. Across the twenty athletes, 560 admissible variants are retained. Large phase-feature ranges are a reliability finding, not a claim of biological variation.

| Matched athlete model | Held-out MSE |
|---|---:|
| Conventional measurements | 0.0457271 |
| Same plus order-insensitive trajectory totals | 3.05464 |
| Same channels plus ordered areas | 6.56017 |
| Phase-population/residual-adjusted ordered features | 1.60353 |

The primary ordering comparison is ordered versus order-insensitive on the same channels, sampling and normalization. Both perform poorly on this small selected held-out sample. The uncertainty-aware construction is less bad here, but it is not a certified physical uncertainty correction. No feature family is tuned on held-out outcomes, and all attempted families remain in the receipt.

The output includes missingness, identity linkage, training-residual coverage and descriptive bootstrap intervals. With ten evaluation athletes these are exploratory measurements, not general performance estimates. Raw official trajectories and individual predictions are restricted and are not included in public artifacts.

Public replay completely checks the exact geometry, finite uncertainty population, source hashes and aggregate integrity. Authorized owners can rerun the private-data empirical pipeline; ordinary public CI explicitly does not reprocess restricted athlete rows.
