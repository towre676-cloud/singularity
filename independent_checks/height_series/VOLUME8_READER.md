# Exact coefficient extraction at volume eight

The reader recovers **differences** of seven invariants from two complete compatible height calculations, with convention **Δ = B − A**. It extends PR #9 at `b85a3c1b8554c79637dbfcdff5fc31d186d9c541`, which depends on PR #8 at `facb4506d1e9b1667b877815777566296572a4fb`. No existing volume-six, seven, or eight proof file is modified. Open `vol8_reader.html` for the offline interactive observation explorer.

## Derivation and independent source verification

Write κ = q(1−q²), f = q⁻²−1 and a = (1+q²)³−1. Under equality of every height polynomial through volume seven,

ΔL₈ = κ⁸ (ΔQ₀ + f ΔQ₁ + f² ΔS₈,₁₀ + f³ ΔS₈,₁₁ + f⁴ ΔS₈,₁₂ − a ΔN_T + fa ΔN_D).

Here L denotes the **formal logarithm** of the height series, Q₀=S₈,₈+N_B and Q₁=S₈,₉−2N_P+N_D, as defined in `VOLUME8_PROOF.md`. The returned coordinate order is Q₀, Q₁, S₈,₁₀, S₈,₁₁, S₈,₁₂, N_T, N_D. These are corrected aggregate counts and motif counts, not all 60 individual eight-vertex motifs. Under the agreement hypothesis ΔL₈=ΔH₈.

Expand the seven factors into q-polynomials. Taking degrees (2,6,8,18,22,28,30) gives a 7×7 integer matrix M. `vol8_reader_certificate.json` retains M and its exact rational inverse, determinant 224000, maximum absolute inverse entry 6, and inverse infinity norm 133/10. In particular the last two rows give ΔN_T=−c₂₈−6c₃₀ and ΔN_D=c₂₈+5c₃₀.

The independent check does not merely re-evaluate these seven factors. It loads every exact source row from `vol8_law.json`, subtracts the proposed seven-factor expression with the natural observable definitions, and verifies that **every residual coefficient row lies in the rank-17 lower observation span**, using exact rational elimination. It separately verifies both inverse identities and checks both supported panels against all 67 retained isolated witness pairs, in both directions. The connected 12-vertex witness is re-enumerated directly from its edges, using both weak compositions and support enumeration at order eight, then compared with independently enumerated motif counts. The retained 20-vertex weld pair is also read and compared with its motif differences; `vol8_verify.py` independently re-enumerates those complete graphs.

## Reusable input and output

Import `extract(A, B, panel=PANEL)` from `vol8_reader.py`, or run:

```sh
python independent_checks/height_series/vol8_reader.py calculations.json
python independent_checks/height_series/vol8_reader.py calculations.json --panel optimal
```

The JSON file contains objects `A` and `B`. Each calculation has this structure:

```json
{
  "schema": "singularity.height-calculation.v1",
  "kind": "height",
  "graph_class": "finite_simple_cubic",
  "q_convention": "vol8_lib",
  "coefficients": {
    "0": {"0": "1"},
    "1": {}, "2": {}, "3": {}, "4": {},
    "5": {}, "6": {}, "7": {}, "8": {}
  }
}
```

This schematic represents the empty graph's height series; replace each polynomial with the complete calculated polynomial. Sparse dictionaries omit **zero degrees**, never unknown degrees. All volumes 0–8 are mandatory for `kind: height`; `kind: log` instead requires volumes 1–8. Values are integers or rational strings (e.g. `"3/2"`); floating point is rejected. Height inputs require H₀=1. The conversion uses nLₙ=nHₙ−Σₖ₌₁ⁿ⁻¹ kLₖHₙ₋ₖ.

The reader enforces compatible class/convention metadata and exact lower-order polynomial agreement. It then solves with rational arithmetic, reconstructs the **entire** eighth polynomial, and rejects inconsistent residuals or nonintegral invariant differences. Output is an exact integer **algebraic** certificate conditional on the supplied graph calculations being correct. It does not certify graph realizability, connectedness, or the computation that produced the input. A full zero difference returns seven zeros. No rounding of a noninteger answer is permitted.

## Minimality and an optimized alternative

The measurement model consists of seven distinct, unscaled single q-coefficients of the eighth difference, with equal independent absolute error bounds. The domain is the full seven-dimensional observation quotient for finite simple cubic graphs, including disconnected graphs.

Seven scalar linear observations are sufficient and necessary. Necessity follows from rank seven: fewer rational coefficient rows have a nonzero rational kernel. Clearing denominators produces an integer relation; the seven isolated integral observation witnesses, scaled to a common multiple of their realization scales, realize it by disjoint unions of their positive and negative cubic components. Thus the ambiguity is realizable in the declared graph class. This argument does not assert the same minimum under a restriction to connected graphs, adaptive nonlinear queries, or prior bounded-count constraints.

The exact exhaustive search checks all C(16,7)=11440 subsets of the nonzero even degrees 0–30; 10710 are invertible. Degrees outside this set give zero rows and cannot improve a full-rank seven-panel. With error bound ε on each measured difference coefficient, the exact worst-case coordinate bound is ||M⁻¹||∞ ε. The unique optimum is

**(4,8,12,14,18,24,26)**, det M=916192200, ||M⁻¹||∞=93093/14165 ≈ 6.57204.

This improves the default panel's 13.3 error gain by about 50.6%. It is global for the declared objective, not a claim of optimal spectral condition number, relative-error stability, unequal sensor errors, or scaled measurements. The default tail-readable panel remains useful because its final two observations isolate T and D directly. `vol8_reader_optimization.json` retains the full search summary; `--optimize` reproduces it deterministically with exact rational arithmetic.

## Approximate measurements

`sensitivity(samples, radii, panel=PANEL)` accepts seven approximate **difference** measurements and their nonnegative error radii. It returns numerical coordinate estimates and Σⱼ |(M⁻¹)ᵢⱼ| εⱼ. If separate A and B calculations each have error ε, their difference radius is at most 2ε. No lower-order compatibility is inferred from approximate samples: exact agreement and validity of the observation model are explicit assumptions. Bounds cover measurement propagation; Python floating-point evaluation is not outward rounded and is not an interval certificate. Overflow, NaNs and negative radii are rejected. No integer certificate or rounding claim is returned.

For CLI use, supply JSON `{"samples":[0,0,0,0,0,0,0],"radii":[0.01,0.01,0.01,0.01,0.01,0.01,0.01]}` and run `vol8_reader.py measurements.json --sensitivity --panel optimal`.

## Reproduction

```sh
python independent_checks/height_series/vol8_verify.py
python independent_checks/height_series/vol8_reader_check.py --enumerate --optimize
python independent_checks/height_series/vol8_reader_visual.py
```

All computation uses the Python standard library. The reader CI runs the unchanged full dependency replay, reproduces all isolated observation witnesses, checks the source-row identity, re-enumerates the small pair, repeats exhaustive optimization, and verifies deterministic certificate/HTML generation. The explorer is a self-contained offline HTML file; its browser arithmetic is illustrative and separate from the exact reader.
