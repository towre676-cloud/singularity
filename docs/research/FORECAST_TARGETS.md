# NX25 — Future targets require information about their drivers

This is an exact finite linear application layer with a separate measured ASOS pilot. The algebra does not validate a weather model. Source: src/singularity/forecast_targets.py. Exact evidence: results/forecast_targets_synthetic.json. Pre-fit configuration: applications/nx25_30/PILOT_FREEZE.json.

## A target is a row, not an entire reconstructed state

For declared dynamics \(x_{t+1}=Ax_t+Bu_t\),
\[
J_\tau=g^\top A^\tau x_0+
\sum_{t=0}^{\tau-1}g^\top A^{\tau-1-t}Bu_t.
\]
Known inputs contribute the known offset. Unknown disturbances require extra state directions or a separate uncertainty population. The known_input_offset function evaluates forcing by forward dynamics; forecast_row compiles \(G_\tau=g^\top A^\tau\). State schema, target interpretation, time interval and admissible domain must be declared.

For \(x_0=x_c+Zz\) and \(y=Hx_0+e\), exact recovery is equivalent to
\[
G_\tau Z=LHZ
\quad\Longleftrightarrow\quad
\ker(HZ)\subseteq\ker(G_\tau Z).
\]
The forward implication follows by applying the factorization to a null vector. Conversely, define the linear map \(HZz\mapsto G_\tau Zz\) on the image of \(HZ\). The kernel inclusion makes it well defined, and a linear extension gives \(L\). Rational elimination constructs a decoder or an invisible direction \(n=Zz\), \(Hn=0\), \(G_\tau n\ne0\). To turn a direction into two finite admissible states, the declared domain must actually contain their displacement.

The affine decoder is \(G_\tau x_c+L(y-Hx_c)\), plus known forcing. Ambient full rank is unnecessary: when velocity is fixed to zero, position alone determines a future position even though the observation has ambient rank one. Centres are retained separately from admissible directions.

## Cost and attainable error

For a scalar decoder with \(w^\top HZ=G_\tau Z\) and deterministic coordinate-box noise,
\[
\sup_{|e_i|\le\epsilon_i}|w^\top e|
=\sum_i|w_i|\epsilon_i.
\]
Aligned error signs attain this bound. The implementation minimizes it over all exact linear estimators, rather than taking the first available decoder. Splitting weights into nonnegative positive/negative parts gives a linear program. Some optimum has at most the equality rank in nonzero variables and an independent row support; opposite signs on the same coordinate can be cancelled without increasing cost. Enumerating independent supports therefore finds a global optimum, including zero noise radii.

The finite panel solver minimizes acquisition cost subject to a declared error cap, then error as a tie breaker. Without a cap it minimizes error first. Strict and closed thresholds are different contracts. An infeasible panel catalogue can fail through structural blindness or excessive noise; only structural failure necessarily supplies a null witness. Arbitrary correlated noise and shared setup costs are not silently substituted into this box contract.

| Exact fixture | Result | Meaning |
|---|---|---|
| \(A=\left(\begin{smallmatrix}1&1\\0&1\end{smallmatrix}\right)\), \(g=(1,0)\), \(\tau=3\) | \(G_3=(1,3)\) | Future position needs its persistent driver |
| Position alone | \(n=(0,1)\) | Velocities \(1,-1\) conceal target gap six |
| Errors \(1/10,1/5\) on position/velocity | \(7/10\) | Exact, attained worst-case error |
| Closed cap \(7/10\) | Two cost-one sensors feasible | Boundary included |
| Strict cap \(<7/10\) | Retained catalogue infeasible | Touching intervals do not become separated through rounding |

Tests independently evolve states through horizons zero to eight, enumerate box vertices, and compare the panel solver with a direct two-dimensional determinant oracle over all 64 panels of six sensors. The oracle uses no elimination helper. The declared state box and known-input assumptions are retained in the synthetic receipt.

## What the measured pilot establishes

The actual WIND continuation archive was recovered. Its BOS ASOS source receipt binds the original CSV to SHA-256 a7def62ca977d281a51fbae632252dce6afefc8c45aed5afbb032f1372a2c21a. The four-day public subset and source receipt are bundled. This is an ASOS station pilot, not a replay of the older 272-volume NEXRAD claim or a validated radar-to-ground transfer.

The target is reported sustained wind in knots at exactly +60 minutes. Training uses September 25–26, 2026, and training targets also stay before September 27. Evaluation uses September 27–28. Missing observations are not interpolated. Each policy uses two prespecified scalar features at declared equal feature cost and identical complete cases. Feature cost is bookkeeping, not a claim about equal instrument purchase prices.

| Policy | Frozen features | Held-out MAE, knots | Held-out MSE |
|---|---|---:|---:|
| Direct target | current wind, wind 30 minutes earlier | 2.18648 | 8.49312 |
| Driver aware | current wind, 30-minute altimeter change | 2.16858 | 8.14812 |
| Generic information | current altimeter, current direction | 5.33963 | 35.54742 |

There are 192 training and 57 evaluation cases. Among 1,219 source reports, 258 lack an exact required lag/future timestamp and 705 lack a required field. Only two evaluation days support the descriptive day-block bootstrap. The small driver-policy gain is not evidence of a general operational advantage. Direction is a declared scalar feature, not a circular physical metric.

The optional NumPy runner fits standardized training-only least squares. The public standard-library checker independently fits rational normal equations and replays point scores to \(10^{-9}\). Bootstrap summaries are integrity checked. None of these numerical checks bounds atmospheric model error.

Offline replay: python3 scripts/nx25_30_replay.py --check.
