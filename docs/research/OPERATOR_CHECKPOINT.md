# Operator experiment checkpoint (superseded)

The recovered checkpoint `21953a9` has been completed and released as version 0.3.0. The mathematics, proofs and limitations are in [Chapter 15](../chapters/15_operators_experiments.md). The public contracts are in [OPERATORS-v1](../specifications/OPERATORS-v1.md), the exact evidence is in [operator_experiments.json](../../results/operator_experiments.json), and the release record is [operator_checkpoint.json](../../results/operator_checkpoint.json).

The release made the following changes relative to the checkpoint.

- **Fixed defects.**
  - Rank-zero closures are certified: reconstruction now uses the ambient dimension.
  - The in-memory verifier enforces exact types, as portable replay already did.
  - The graph adapter rejects floating-point and Boolean numbers.
- **Restored components.**
  - The periodic sector, `periodic.py`.
  - Dedicated regression suites for the engine, the graph compiler, the metrics and the periodic sector. They use independent enumeration oracles.
- **Rerun results.**
  - The R=7 rank-69 calculation, rerun on the released code.
  - The R=4 certificate, regenerated with identical content.
- **New proposition.** The top-volume corank bound (SNG-O06) explains the R=7 invisible direction.

The original Vakil work is preserved at local commit `0ea8807`. The recovered operator, graph and metric modules came from local `09aa342`/`38b71c5`.
