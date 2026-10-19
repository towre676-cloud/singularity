# Operator and experiment ledger (OE01–OE13)

The original P01–P36 ledger is complete and unchanged. These identifiers track the operator and experiment program started from checkpoint `21953a9` (decision D015). An item is `complete` only with the evidence listed; a dependency must be complete first.

| ID | Unit | Depends on | Status | Evidence / remaining |
|---|---|---|---|---|
| OE01 | Closure engine correctness: rank-zero, exact-type verifier, quotient maps | — | complete | `observability.py`; `tests/test_observability.py` (26 tests); the unfixed module fails 9 of them |
| OE02 | Cost-filtered cheapest witnesses (SNG-O03, SNG-O04) | OE01 | complete | Chapter 15 proof; oracle tests over 60 random systems; amplification counterexample |
| OE03 | Graph compiler evidence (SNG-O05, SNG-O06): R=4 sequence, R=7 direction, path fixture | OE01 | complete | `tests/test_graph_experiments.py`; `results/operator_experiments.json` |
| OE04 | Exact robustness (SNG-O07) | — | complete | `experiment_design.py` docstring; exhaustive lattice identification test |
| OE05 | Periodic sector (SNG-O08, SNG-O09) | — | complete | `periodic.py`; `tests/test_periodic.py`; 524-model exhaustion |
| OE06 | Release 0.3.0: receipt in CI, manuscript, spec, documents, archive | OE01–OE05 | in progress | completes when the pushed release commit's CI run is observed green and the archive passes clean-extraction checks |
| OE07 | Cost-bounded robust (margin) experiment search (SNG-O15) | OE02 | complete | `robust_search.py`; `tests/test_robust_search.py` (12); `results/robust_search.json`; `docs/research/ROBUST_SEARCH.md`; amplification, non-attained supremum and pruned-optimum counterexamples |
| OE08 | Shared experiment panels for candidate families (SNG-O16) | OE02, OE04 | complete | `panels.py`; `tests/test_panels.py` (14); `results/panels.json`; `docs/research/PANELS.md`; set-cover hardness stated; graph threshold 278513/2097152 |
| OE09 | Parameter-aware observability over Q(q) | OE01 | planned | generic rank versus rank at every q; exceptional values isolated exactly |
| OE10 | Graph-family compression of realizable states (SNG-O13, SNG-O14) | OE03 | complete | `compression.py`; `tests/test_compression.py` (10); `results/compression.json`; cyclicity theorem for R<=6 (no closed-family savings), star-family bound with cubic-minus-quadratic savings |
| OE11 | Charge-aware separator/connected-support compiler | OE10 | planned | operations proved against direct enumeration; separate cost measurements |
| OE12 | Lean formalization of closure, quotient, cost filtration, periodic complement | OE01–OE05 | in progress | delegated; accepted only for statements that compile without admitted results |
| OE13 | Sharper periodic cutoffs; noncommuting graph operations | OE05, OE03 | planned | closed state semantics required before completeness claims |
