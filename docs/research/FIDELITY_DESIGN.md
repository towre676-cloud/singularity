# Experiment, rank and executable arithmetic selection (NX09)

A computational envelope and a physical observation uncertainty play different roles. The centre produced by an approximate evaluator need not equal the exact full-model reading. Its certified computational radius encloses that difference. Sensor error surrounds the actual physical observation. With all terms in the same output units and at the same chronological sample,

\[
I_{e,c,f}=\widehat r_{e,c,f}+[-\rho_{\rm phys}-\rho_{\rm comp},\rho_{\rm phys}+\rho_{\rm comp}],
\qquad
\rho_{\rm comp}\le\rho_{\rm source}+\rho_{\rm transformation}+\rho_{\rm reduction}+\rho_{\rm execution}.
\]

Each summand is nonnegative and is retained individually in source evidence. Triangle inequality proves this composition. It does not prove sharpness, statistical independence, calibration of a synthetic source, or attainability of every envelope endpoint. Initial-state/process uncertainty is included in the declared source domain; adding it again as an unexplained radius would double count it.

## Typed binding and supported arithmetic

`BoundedReading` carries centre, physical radius, computational radius, source IDs, units, horizon and domain ID. `EvaluatorOption` additionally carries candidate and sensor identities, actual retained rank, executable arithmetic protocol, setup key, exact setup/run costs and a bound receipt. The constructor rejects orphaned IDs, stale horizons, unit/domain mismatch, unsupported executable protocols, negative radii and conflicting shared setup bindings.

`DynaCompAdapter` is optional and loaded only when requested. It hashes the names and bytes of every Python module in the selected upstream package. Relative imports run under an isolated package name, so the core has no import-time third-party dependency. The handoff contains the pinned source tree. Every replay rechecks its digest; changing source bytes invalidates an old adapter binding.

The implemented upstream evaluator routes are exact rational reduced dynamics and DynaComp's **integer-exact-dot, one RN-even binary64 rounding per row** executor. This is not NumPy, BLAS, an arbitrary sequential float loop, GPU arithmetic or user-selectable \(p\)-bit arithmetic. Generic precision remains unsupported. The typed menu reserves the separate sequential protocol identifier, but this adapter refuses it until a native contract is explicitly supplied.

For every candidate/sensor/fixed-input domain the adapter rebuilds `uniform_enrichment`, replays its exact sharp-box certificate, and retains \(E,G,H,D\). Requested rank is a budget; actual retained rank is authoritative because an exact low-rank response may close early. Exact reduced dynamics are

\[
z_0=Ex_0,\qquad z_{t+1}=Gz_t+Hu_t,\qquad \widehat y_t=Dz_t.
\]

The binary64 option then calls and replays `certify_execution` on these same matrices and this same domain. Its centre is extracted from the actual certified bit executor, not converted from an unrelated Python float. Reduction and execution bounds at the queried output time are summed. Source and transformation errors are zero only because these examples directly use the declared discrete rational source without an additional source transformation.

## Finite optimizer and setup theorem

For each physical experiment, choose either no experiment or one compatible evaluator for each candidate. The robust pair mask follows the same strict interval-separation rule as NX07. A plan's objective is

\[
\sum_{s\in\text{activated setups}}a_s+
N\sum_{e\in\text{panel}}\left(c_e+\sum_c b_{e,c,f_{e,c}}\right).
\]

The current accounting model recomputes the selected evaluations per diagnosis. Setup costs are paid once per exact setup key. Two options may share a key only if their setup cost and complete setup-binding fingerprint agree. Binding includes the source, output projection, domain, arithmetic and upstream bytes; rank alone is not a cache key.

The search enumerates skip/assignment branches for every experiment. At a partial node, all future costs are nonnegative, so a cost exceeding an incumbent cannot improve the objective. A full target mask is feasible and may terminate that branch because extra evaluations cannot lower cost. Induction on the finite branch tree proves that exhaustion gives the minimum objective among the supplied finite menus. Search exhaustion returns an unresolved status with an incumbent when available. This is not a global theorem that the chosen reduction rank is best among every possible subspace.

## Independent evidence and reference plans

The tiny example has centres zero and \(1/2\), physical radii \(1/20\), cheap computational radii \(1/4\), and accurate radii \(1/20\). The cheap close experiment cannot certify separation because \(1/2\le3/5\). A wider physical test with centre difference one can use the cheap evaluator. Tests enumerate every evaluator assignment and panel by independent plain loops and check exact costs, strict equality refusal, target coarsening, stale source rejection and shared-setup consistency.

The thermal receipt checks two actual ranks, exact and binary64 execution, two candidates and every vertex word in \(\{0,1\}^2\): 32 independently bounded executions. Each full-model output is recomputed by conservative neighbour-flux stepping, and every deviation lies within the retained envelope. Rank-two requests that close at rank one are represented honestly.

The diagnostic menu uses the nominal and heater-half candidates, two physical horizons, candidate-specific evaluator assignments and explicit setup prices. It retains deployment plans for 1, 2, 10 and 100 diagnoses and compares full-exact and same-rank references. These prices are declared accounting units. The relation

\[
S_1+NQ_1<S_2+NQ_2
\]

is an exact repeated-query break-even test; it is not inferred from one warm benchmark. The complete menu, source-bound upstream packets and selected envelopes are retained for replay. A loose bound means `not_certified`, not that the physical candidate is refuted.

Run `python scripts/nx_decision_recovery.py --track NX09 --check` and `python -m unittest tests.test_fidelity_design`.

## Retained measured setup and query work

`results/nx_decision_benchmarks.json` separately records actual source-bound certification/setup, executor preparation, cold total and repeated warm query medians from `perf_counter_ns`. It uses the same two candidates, sensor, input word and accepted projection packets as the decision demonstration. Full exact reference queries call the original sparse simulator. Rank-one/rank-two exact and certified binary64 routes are all measured; no timing becomes an exact rational price in the optimizer.

For observed setup \(S\), warm-query time \(Q\) and direct-query time \(D\), the recorded first strictly cheaper repeated-query count is

\[
N_{\rm break}=\left\lfloor S/(D-Q)\right\rfloor+1\quad\text{if }Q<D,
\]

and is absent when there is no positive runtime saving. The chosen rank-one binary64 evaluator can require hundreds of diagnoses to amortize certificate setup on this machine, while exact reduced evaluation amortizes sooner. These are machine-specific measured comparisons, including setup, rather than a universal acceleration theorem. The declared-price plan separately records its exact break-even, which is already favorable at the first diagnosis in this finite menu.

The same receipt includes eight vertex checks of one nondegenerate two-input box \([0,1]^2\) at two actual rank budgets. Upstream uniform reduction and binary64 execution are certified on the entire box; each vertex is independently stepped through the full rational source. This is distinct from the fixed-input domains used by the optimizer.

Actual upstream options are replayed at optimization entry, not merely checked for matching labels. Replacing a certified computational radius by zero while keeping its source IDs would otherwise create an unsupported separation. A dedicated regression rejects that forgery. Handwritten toy menus remain explicitly declared mathematical envelope assumptions; they are not promoted to physical or upstream numerical certificates.
