# What Must Survive II — parallel research advance

This package keeps separate from the other session's fourth-jet lift.

## Completed here

- Primary-source priority review, including a precise relation between the leading pattern weights and the Watanabe-Fukumizu polynomial.
- Recovery of the actual annular rank-three source note, exact Krylov determinants for the two elliptic coordinate readouts, and an explicit physical transfer contract.
- Exact rational volume-fourteen unrestricted consecutive-window certificate: earlier rank 109; adding energies 0,2,...,64 gives 142, equal to the full rank.
- Exact reduction of a general window law to injectivity of the d-jet at t=0; a necessary promotion-onset bound conditional on the amplitude divisibility.
- A finite collision benchmark: one nonisomorphic pair from each of 42 connected seven-vertex binary-height collision classes, all separated by integer heights at volume three or four.
- Lean 4.20.0 certificate checker soundness and the actual order-seventeen encoded row witness, with axiom audits.

## Not completed

Order twenty-seven or later promotion attainment; the all-volume window theorem; completeness of L_G; the physical annular state/readout transfer; or end-to-end formal verification of the C++ engine. The literature review is a first pass and does not certify novelty.

## Read in this order

1. WINDOW_AND_PROMOTION_TARGETS.md
2. ANNULAR_TRANSFER_CONTRACT.md
3. PRIORITY_REVIEW.md
4. FORMALIZATION_STATUS.md

The authoritative annular source note is available at https://chatgpt.com/library?file_id=libfile_3b054f3aa130819191b2e2a77585d619&account_id=personal . It was read in full, version 1. The older full report's ordinary physical activation is kept separate from the current rank-three and twisted-regulator comparisons.

## Reproduce numerical and symbolic checks

Dependencies used: Python 3.12, SymPy 1.14.0, python-flint 0.9.0, NetworkX 3.7.

    python prepare_input.py
    python annular_readout.py
    python window14.py
    python completeness_probe.py

The source rational rows are copied from Revision 4's certified input; the modular engine is not regenerated. The atlas experiment uses all connected atlas graphs through seven vertices to find collision classes, and tests one pair per class, not every pair in a larger class. It is not a cubic-graph census.

## Reproduce Lean checks

With official Lean 4.20.0 and the current directory on LEAN_PATH:

    lean -o CertificateKernel.olean CertificateKernel.lean
    LEAN_PATH=. lean Witness17.lean
    lean ResidueUniqueness.lean

On Windows set LEAN_PATH to the current directory using the shell's syntax. No Mathlib dependency is required. The concrete `by decide` proof can take several minutes. Source generation is provided separately; its normalization is outside the formal semantic boundary, as explained in FORMALIZATION_STATUS.md. Standard source and data hashes appear in SHA256.json; axiom audits are in lean_audit.txt.
