# Operator and experiment ledger (OE01–OE14)

The original P01–P36 ledger is complete and unchanged. These identifiers track the operator and experiment program started from checkpoint `21953a9` (decision D015). An item is `complete` only with the evidence listed; a dependency must be complete first.

| ID | Unit | Depends on | Status | Evidence / remaining |
|---|---|---|---|---|
| OE01 | Closure engine correctness: rank-zero, exact-type verifier, quotient maps | — | complete | `observability.py`; `tests/test_observability.py` (26 tests); the unfixed module fails 9 of them |
| OE02 | Cost-filtered cheapest witnesses (SNG-O03, SNG-O04) | OE01 | complete | Chapter 15 proof; oracle tests over 60 random systems; amplification counterexample |
| OE03 | Graph compiler evidence (SNG-O05, SNG-O06): R=4 sequence, R=7 direction, path fixture | OE01 | complete | `tests/test_graph_experiments.py`; `results/operator_experiments.json` |
| OE04 | Exact robustness (SNG-O07) | — | complete | `experiment_design.py` docstring; exhaustive lattice identification test |
| OE05 | Periodic sector (SNG-O08, SNG-O09) | — | complete | `periodic.py`; `tests/test_periodic.py`; 524-model exhaustion |
| OE06 | Release 0.3.0: receipt in CI, manuscript, spec, documents, archive | OE01–OE05 | complete | source 6761037 (CI run 53 green), archive 6d6b333 (CI run 54 green); clean-extraction checks passed |
| OE07 | Cost-bounded robust (margin) experiment search (SNG-O15) | OE02 | complete | `robust_search.py`; `tests/test_robust_search.py` (12); `results/robust_search.json`; `docs/research/ROBUST_SEARCH.md`; amplification, non-attained supremum and pruned-optimum counterexamples |
| OE08 | Shared experiment panels for candidate families (SNG-O16) | OE02, OE04 | complete | `panels.py`; `tests/test_panels.py` (14); `results/panels.json`; `docs/research/PANELS.md`; set-cover hardness stated; graph threshold 278513/2097152 |
| OE09 | Parameter-aware observability over Q(q) (SNG-O19) | OE01 | complete | `parametric.py`; `tests/test_parametric.py` (15); `results/parametric_observability.json`; `docs/research/PARAMETRIC_OBSERVABILITY.md`; full rank on all of (0,1) for R<=4 |
| OE10 | Graph-family compression of realizable states (SNG-O13, SNG-O14) | OE03 | complete | `compression.py`; `tests/test_compression.py` (10); `results/compression.json`; cyclicity theorem for R<=6 (no closed-family savings), star-family bound with cubic-minus-quadratic savings |
| OE11 | Charge-aware separator compiler (SNG-O21) | OE10 | complete | `separator_compiler.py` (extends `charges.py`); `tests/test_separator_compiler.py` (20); `results/separator_compiler.json`; `docs/research/SEPARATOR_COMPILER.md`; exactness, cell and bit bounds proved; benchmarks to n=200 |
| OE12 | Lean formalization of closure, quotient, cost filtration, periodic complement | OE01–OE05 | complete | 37 new audited declarations; 128 core declarations; `formal/Singularity/{Operators,OperatorExamples,Periodic,PeriodicSeries}.lean`; `results/formal_operator_audit.json`. Natural-cost semantic pruning is proved; Python termination, linear dimension minimality, rational-cost scaling, and the cyclotomic denominator decomposition retain their explicitly separate scope. |
| OE13 | Sharper periodic cutoffs; noncommuting graph operations (SNG-O17, O18, O20) | OE05, OE03 | complete | period reduction and M=2 closed form in `periodic.py`; `terminal_moves.py` with ordered states; `tests/test_periodic.py`, `tests/test_terminal_moves.py`; M=3 gap and larger-budget completeness open |
| OE14 | Ordered asymmetric contexts and all-budget graph margin (SNG-O22) | OE03, OE07, OE13 | complete | Checked `OrderedContextAttachment`; independent assembled asymmetric word checks; `tests/test_path_margin.py`; all-budget proof and sharp finite-experiment noise frontier in Chapter 15 and `docs/research/ORDERED_CONTEXTS.md`. |

## Thermal integration (v0.4.0)

The subsequent source-derived 144-state thermal pilot is complete for its declared six candidates, 112 experiments and common box-error envelope. `results/thermal_diagnostics.json` retains all 672 independent reading checks, the separate pair-mask shortest-path optimum, reset/noise sensitivity and model/source provenance. At reset radius and sensor noise both 1/100, robust optimum cost is 20, greedy cost is 31, and the fixed twenty-step local-sensor baseline costs 44. Chapter 16 proves the affine candidate lift, safe error composition and all-word reflection obstruction. This is a synthetic discrete-model result, not a physical fault-data claim; no thermal Lean coverage is asserted.
