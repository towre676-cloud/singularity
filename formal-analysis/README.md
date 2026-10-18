# Real analytic visibility in Lean

This package completes the positive-real comparison behind SNG-A11 using
Mathlib's actual real numbers, powers, limits, infinite sums and products, and
Riemann zeta function. The older core-only package in `../formal` remains
independently buildable. Its `RealFacts` conditional theorem is retained as an
abstract factorization argument; it is not an assumption of this package's
concrete analytic theorems.

The toolchain is Lean **4.12.0**. Mathlib is pinned to **v4.12.0** and its exact
commit, together with all transitive dependency commits, is recorded in
`lake-manifest.json`. The core `Singularity` package is a path dependency on
the released source in `../formal`.

## Build and audit

With the pinned Lean toolchain installed, initialize dependencies and obtain
Mathlib's precompiled artifacts from this directory:

```sh
lake update
lake exe cache get \
  Mathlib/NumberTheory/EulerProduct/DirichletLSeries.lean \
  Mathlib/Analysis/SpecialFunctions/Pow/Continuity.lean \
  Mathlib/Analysis/SpecialFunctions/Log/Deriv.lean \
  Mathlib/Analysis/NormedSpace/FunctionSeries.lean \
  Mathlib/Analysis/SpecialFunctions/Pow/Asymptotics.lean \
  Mathlib/Tactic/NormNum.lean \
  Mathlib/Tactic/Linarith.lean \
  Mathlib/Tactic/GCongr.lean \
  Mathlib/Tactic/Ring.lean
```

From the repository root, build the package and audit its release theorems:

```sh
python scripts/check_formal_analysis.py --clean \
  --receipt results/formal_analysis_audit.json
```

The checker accepts only Lean's standard `propext`, `Quot.sound` and
`Classical.choice` axioms. It rejects a missing declaration or `sorryAx`.
`--clean` removes only this package's generated build directory; it preserves
the downloaded dependency cache. `AnalysisAxiomAudit.lean` gives the complete
audited declaration list. The JSON receipt binds those checks to source and
dependency-manifest SHA-256 digests.

## Checked mathematical chain

`LocalSeries.lean` evaluates the same certified weak-composition enumerator as
P33. For `0 ≤ q ≤ 1` its graph coefficients satisfy
`0 ≤ ell_V(q) ≤ (V+1)^n`. This gives absolute convergence for `|x| < 1`, locally
uniform convergence, continuity, positivity on `(0,1)`, an exact factorized
Taylor remainder, and the first-discrepancy estimate.

`LogExpansion.lean` uses an explicit bound on the remainder of the real
logarithm. Agreement below volume `r` gives `log(L_G/L_H) = O(x^r)`; with
`delta = ell_G,r - ell_H,r`, the regularized logarithm
`log(L_G/L_H) + delta log(1-x^r)` is `O(x^(r+1))`. These statements are proved
from coefficient bounds and finite-prefix agreement.

`PrimeProduct.lean` proves that a continuous logarithmic factor bounded by
`C x^m` near zero has an absolutely convergent prime logarithm when `ms > 1`.
It proves locally uniform convergence in `s`, continuity, positivity of the
exponential of the sum, and `HasProd` for the actual positive local factors.
Nonprimes have factor one in the natural-number indexing convention.

`ZetaReal.lean` proves the real Euler product and right-hand residue-one limit
by connecting to Mathlib's `riemannZeta_eulerProduct_hasProd` and
`riemannZeta_residue_one`. The real zeta function here is the real part of
Mathlib's complex Riemann zeta evaluated on the real axis, with the coercion
identity proved for `s > 1`.

`VisibilityReal.lean` combines those results into the actual real product
factorization and boundary asymptotic. `CoefficientVisibility.lean`
discharges its local logarithmic bounds for polynomially bounded,
nonnegative unit-constant coefficient sequences. `CertificateReal.lean`
connects those sequences to P33's kernel-checked graph tables and proves the
exact half-parameter exponents. `SpectralVisibility.lean` supplies the
spectral and binary pair instances. `EulerRatio.lean` identifies the ratio
product with the ratio of the individual graph Euler products on `s > 1`.

## Precise scope

For a first differing volume `r ≥ 1`, admissible `0 ≤ q ≤ 1`, and
`delta = ell_G,r(q)-ell_H,r(q)`, the normalized product is positive and
continuous on `(r+1)s > 1`. On `rs > 1`, the ratio product factors as
`R(s) = zeta(rs)^delta K(s)`, and as real `s` decreases to `1/r`,
`(rs-1)^delta R(s)` tends to the strictly positive value `K(1/r)`.

For the spectral pair at `q=1/2`, the exponent is exactly `3/32`; for the
binary-census pair it is exactly `11025/262144`. Their finite agreement and
discrepancy are derived from P33, not assumed as analytic facts.

The final declarations are `SingularityAnalysis.graph_visibility`,
`spectral_visibility`, `binary_visibility`, `spectral_visibility_half` and
`binary_visibility_half` in `SingularityAnalysis/SpectralVisibility.lean`.
Their `GraphVisibility` conclusion includes both convergent prime products,
zeta factorization, the strictly positive boundary value, the right-hand
normalized limit, and identification with the original quotient on `s > 1`.
The only graph theorem hypotheses are `0 ≤ q ≤ 1`, `r ≥ 1`, finite coefficient
agreement below `r`, and `r*s0=1`; the two concrete pair instances discharge
all of those finite conditions, leaving just the stated parameter range.

The theorem is a positive-real comparison. It does not assert global
meromorphic continuation or formalize a complex branch. The numerical
interval experiment and the specific effective constant of SNG-A14 are
separate computational and manuscript results; they are not used as
substitutes for analytic premises in this proof.
