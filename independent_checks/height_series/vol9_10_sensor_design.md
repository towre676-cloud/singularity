# Exact volume-nine and volume-ten sensor design

| Volume | Cubic graphs | Minimum sensors | Established gain | Global optimum |
| --- | --- | ---: | ---: | ---: |
| 9 | General | 10 | 3218423 | 2283261919/403723320 |
| 9 | Connected | 10 | 1 | 1 |
| 10 | General | 14 | 2006752078/5 | 1073461009715/22189301316 |
| 10 | Connected | 12 | 1 | 1 |

These gains measure worst-case absolute error in the established reader
coordinates (research coordinates in general mode, measured coefficients in
connected mode), with the infinity norm on both errors and coordinate output.
Each linear sensor has coefficient weights of ℓ₁ norm at most one. Unit-bounded
adversarial coefficient errors induce unit-bounded normalized sensor errors.
The lower-bound witnesses work for both a common coefficient-error vector and
independently bounded sensor readings. The reported gains make no assertion
about stochastic noise, a different normalization or a different output norm.
The existing lower-volume agreement and graph-class hypotheses apply. The
existing minimum-count results and the gains in the table concern different
objectives. All displayed designs attain the gain using the minimum count.

## Attaining designs

The connected cases retain the established panels. Volume ten general uses
single coefficients of degrees **2, 6, 10, 14, 16, 20, 22, 24, 28, 30, 32,
36, 38, 44** in that order. Its full inverse is in the certificate.

Volume nine general uses ten mixed sensors with diagonal decoding. In
zero-based reader-coordinate order, start with the inverse of the response
matrix on degrees **3, 9, 11, 15, 17, 19, 21, 25, 31, 35**. Take each
coordinate's inverse row on that panel, except for rows 0, 1 and 8, which use
the corresponding inverse row from the alternate panel below.

| Coordinate | Degrees used for its inverse row |
| --- | --- |
| corrected_S9_9 | 5, 9, 11, 13, 15, 19, 25, 27, 31, 33 |
| corrected_S9_10 | 5, 9, 13, 15, 17, 21, 25, 27, 29, 35 |
| delayed_7_44337 | 3, 9, 11, 15, 17, 21, 25, 27, 31, 33 |

Divide each inverse row by its ℓ₁ norm to get the sensor weights. Multiply
each sensor reading by that same norm to recover the corresponding coordinate.
The JSON certificate gives every weight and decoder entry explicitly as a
rational. For any of the four designs, apply the decoder and then expand in
the established polynomial basis to recover every coefficient of **B − A**.

## Exact optimality proof

Write R for the all-degree response matrix and y for the stored dual
coordinate vector. The certificate verifies |(Ry)ₑ| ≤ 1 at every available
degree. Any matrix S of normalized sensor weights then satisfies
‖SRy‖∞ ≤ 1. An exact decoder D satisfies DSR = I, so
‖D‖∞ ≥ |yᵢ| for the critical coordinate i. The proposed decoder attains that
bound. A common coefficient error Ry also induces SRy in the sensor readings,
so the same extremal error is feasible when all readings share one underlying
coefficient-error vector.

At volume nine general, exactly ten degrees satisfy |(Ry)ₑ| = 1. Equality
for the critical coordinate requires every nonzero coefficient in its linear
decoding formula to lie on those degrees. Their response matrix is invertible
and its critical inverse row uses all ten. Thus any ten-sensor pure coefficient
panel attaining the bound would have to use exactly those ten degrees.
Its gain is **890287017/53829776**, strictly above the global optimum.
Permuting the degrees cannot change this gain, and scaling individual
coefficient sensors down cannot improve it. This proves a strict advantage
for mixing at the minimum sensor count.

## Replay

The search used linear programs minimizing the ℓ₁ norm of a coefficient
representation of a coordinate unit vector, and the corresponding polar
programs maximizing the dual coordinate under −1 ≤ Ry ≤ 1.
LP solutions were used to identify support and active constraints. The
generator reconstructs the displayed witnesses from those choices using
exact inverses, including the pinned PerfectJet panel certificate routine
for volume ten general. Neither replay nor verification uses an LP solver.

From the repository root, with PerfectJet at the pin from Singularity PR #15
(`a9b0e61d6bf6c57c38399cfd1005e4733d016952`) available on the Python path:

```bash
cd independent_checks/height_series
python vol9_10_sensor_design.py > /tmp/vol9_10_sensor_certificates.json
cmp /tmp/vol9_10_sensor_certificates.json vol9_10_sensor_certificates.json
python vol9_10_sensor_verify.py vol9_10_sensor_certificates.json
python -m unittest -v test_vol9_10_sensor_design vol9_10_reader_check
```

The independent verifier uses only the Python standard library and the
unchanged reader-model JSON. It checks every sensor cost, baseline inverse
and gain, exact decoder product, all-degree polynomial identity, dual
constraint and primal–dual equality. The tests also compare a signed rational
reconstruction with the original reader in each case and reject corrupted
certificates.
