# Actual rank-three annular source: recovered data and remaining physical interface

Authoritative note read: RANK_THREE_PARABOLIC_OBSTRUCTION_THEOREM.md, Library ID libfile_3b054f3aa130819191b2e2a77585d619, version 1. Its theorem concerns the actual rational connection extracted from B11_polynomial_gauge.json, with state order (y5,E1,E2).

The note establishes nonsplitting over C(s) and every finite algebraic extension, identifies the Legendre factor and invokes its irreducible, Zariski-dense SL2 monodromy. It does not establish the proposed physical mixed-meridian values or the selected physical contour normalization. In particular the candidate integral lattice is not a physically certified lattice.

## New exact readout certificates

For z'=Az and lambda a rational row, define lambda_0=lambda, lambda_(j+1)=lambda_j'+lambda_j A. For lambda=(0,1,0), the determinant of the first three rows is

-512 (s^3+20s^2+32s-192) /
 [s^4 (s-4)^2 (s+12)^2 (s+16)^2].

Its value at s=8 is -29/460800. For lambda=(0,0,1), the corresponding value is -643/1638400. Both coordinate readouts therefore generate the full rank-three observable module. The character readout (1,0,0) closes at order one; f5=sqrt(s/(s+4)^3) has logarithmic derivative b5 exactly.

These certify observable modules, not the order of an unspecified physical period. The selected state must also have nonzero character component. If sigma lies in E, its elliptic readout can instead have scalar order two.

## Precise remaining transfer data

1. Specify the physical scalar and its source state, including whether it is an uncut integral, a continued variation, or a lower-sector-subtracted quantity. An observable inside a rank-three subsystem need not be the entire physical function.
2. Supply the rational gauge/projection P from the original physical connection A_phys to this ordered rank-three frame, with the exact identity P'+P A_phys=A3 P.
3. Supply the readout correspondence. If it does not factor through P exactly, retain every residual readout and justify its subtraction or its annihilation by a specified continuation word.
4. Supply the selected boundary state or a validated enclosure for its projected y5 component at a nonsingular anchor. An interval excluding zero suffices for state excitation; an integer-fit monodromy does not.
5. Match the branch and normalization of f5 and the elliptic fundamental matrix to that physical state. A coordinate determinant cannot substitute for this comparison.

## Reconciliation with the older full report

annular-periods-report.html, Library ID libfile_f0702be6da808191be1350c9911904e2, version 7, section 48 records ordinary physical activation in a larger system and a nonzero validated readout. Section 49 gives the full 65-master readout at zero-based index 60. These are different statements from an exact scalar-order theorem for the current rank-three subsystem. The older activation result cannot be substituted for the missing P and state/readout comparison. The later rank-three note also separately leaves the twisted first-regulator physical contour comparison open. No identification between these certificates is made here.

The source note is now available to the other session; absence of that note is no longer the blocker. The blocker is the explicit physical transfer data listed above.
