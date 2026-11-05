# Formal verification: completed certificate layer and remaining engine semantics

## Checked now

Lean 4.20.0 was installed and used to check CertificateKernel.lean. The theorem allZero_sound turns Boolean acceptance of a finite integer row-annihilation test into the corresponding universal equality statement. accepted_sound adds the nonzero target pairing. Their axiom audits list only propext and Quot.sound.

Witness17.lean encodes the actual supplied order-seventeen witness, restricted to its 31 supported variables. Every earlier source row was multiplied to integral form; nonzero rows were made primitive, and zero/duplicate rows removed. The resulting 118 distinct rows are checked together with the target energy-73 row. The concrete certificateAccepted declaration has no axioms. earlierRowsVanish and targetSurvives depend only on the standard axioms of the generic soundness theorem. A separate shapes theorem checks the row lengths; dot itself deliberately has a total truncated-list definition, so that shape check matters.

ResidueUniqueness.lean also checks uniqueness of a bounded natural-number representative of a specified residue, using only propext. This is a building block, not an entire Chinese-remainder reconstruction theorem.

No native_decide, sorry, or user-added axiom is used in the delivered proofs.

## What is not formalized

The C++ engine, its graph generator, the loop-series identity, coefficient reconstruction bounds, and the semantic relation between the source rows and L_G are not proved in Lean here. Normalization and extraction of the finite rows were performed by Python; the generated concrete Lean data is checked, but the Python source-to-data transformation is not itself formalized. The code and hashes are supplied so that this boundary is explicit.

Thus the result is a kernel-checked finite witness, not end-to-end formal verification of graph measurement minima or of the engine.

## Minimal further modules

1. Finite graph and height-function semantics, with energy and volume definitions.
2. Completeness of weak-composition enumeration at each volume and proof of the energy bound.
3. Truncated-series operations and their coefficient semantics.
4. Bethe recurrence and coefficientwise treatment of the infinite alphabet.
5. Leaf cancellation, generalized-loop identity and polymer logarithm.
6. Coefficient-bound and CRT reconstruction soundness, tied to the actual generator output.
7. Rational row-relation and rank certificates, including class-specific realizability.

Use the existing generator as an untrusted producer and export small algebraic certificates to a proved checker, instead of beginning with a formal transcription of every C++ optimization.

## Runtime note

The execution environment lacks the usual /proc/<pid>/exe link. Lean's official runtime uses readlink on that path to locate its installation. The optional app_path.c shim supplied in this package returns the actual Lean executable path for that lookup only. It changes installation discovery, not arithmetic or proof checking. Ordinary Linux/Windows installations do not need it. Lean source consulted: https://github.com/leanprover/lean4/blob/v4.20.0/src/runtime/io.cpp .
