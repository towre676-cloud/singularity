# Reading guide {.unnumbered}

This is the enriched Claude Code implementation handoff for 36 new expansion tracks and 108 acceptance units. It supplies mathematical designs, conceptual explanations, worked examples, source reuse and bounded implementation gates. Proposed results are not presented as completed work. The complete executable baseline and companion selections travel with the archive.


# Start here: the 36-track Claude Code expansion handoff

This package prepares all NX01-NX36 designs from the expansion discussion. It contains mathematical implementation packets, 108 acceptance-sized push units, a dependency ledger, complete Singularity v0.4.0 baseline source, pinned companion reference code, and an assembled equation-rendered handbook. It is a handoff for new implementation. All NX units begin proposed; writing this package does not complete their mathematics or code.

## Open the right directory

In the outer ZIP, open `repository/` as the Claude Code working directory. This directory contains the full working source snapshot and this handoff at `handoff/nx36/`. Begin with this file, then `CLAUDE_START_PROMPT.md`, `architecture/PROGRAM_DESIGN.md`, and the first ready packet. The outer archive also contains a baseline Git bundle so the release history can be recovered offline. Read `architecture/RECOVERY_AND_RELEASE.md` before attaching the snapshot to an existing Git repository.

If Claude is already running in a current Singularity checkout, inspect the worktree and remote first. Compare its revision with the pinned baseline rather than overwriting it. Integrate only the handoff and compatible source changes. The reference bundle is a recovery baseline, not permission to reset a newer branch.

## First commands

Run the lightweight roadmap tools from the repository root:

```sh
python handoff/nx36/tools/handoff.py verify
python handoff/nx36/tools/handoff.py status
python handoff/nx36/tools/handoff.py next --limit 3
python handoff/nx36/tools/handoff.py show NX01
```

Then run the actual baseline suite before modifying executable code:

```sh
PYTHONPATH=src python -m unittest discover -s tests -q
PYTHONPATH=src python scripts/reproduce.py --check
python scripts/check_repository.py
python scripts/check_links.py
```

PowerShell uses `$env:PYTHONPATH='src'` before the Python commands. Core checks require Python 3.10 or later and the standard library. Optional numerical, symbolic, document, and Lean toolchains have separate dependency contracts. A missing optional tool does not prevent the exact scalar first batch.

## First implementation batch

The recommended initial session is NX01-A, NX01-B, and NX01-C: recover the existing candidate-specific radii, define exact heterogeneous interval separation, and integrate a finite-pool panel result. These are three acceptance units, not necessarily three commits. Read the full NX01 packet before touching the optimizer. Candidate-specific bounds already exist in thermal records; the current panel optimizer uses the common envelope. Reuse the former and extend the latter carefully.

After that, pursue the finite fault population NX03 and the correlated geometry NX02. A scalar pair-mask cover cannot represent every joint correlated separation. Do not weaken NX02 to independent errors merely to reuse the old set-cover interface. NX07 then designs a sensor/actuator language worth buying for the larger population.

Independent mathematical lanes can start sooner: incremental local compilation NX16, low-rank fault transport NX17, integer quotients NX19, and moving-quotient preparation NX31. The machine ledger distinguishes hard dependencies from supporting tracks. Many conceptual bridges need no new implementation of capabilities already available in a companion engine.

## What is actually frozen

The source baseline is published Singularity main commit `438ed423d7d389a1a483c61e0b50eca6a9fc0827`, tree `47a88f7b9ebf4fc24bf2c8cf589ebd9ed3ab87b0`. The local release tree was compared with that tree before authoring. Its 432 unit tests passed again while this handoff was being built. Its monograph and focused papers are included in the complete source snapshot. Read `provenance/BASELINE.json` for exact evidence and `provenance/COMPANION_SOURCES.json` for the three pinned companion selections.

Older P01-P36 and OE01-OE14 work must not be reopened because a historical chat says Lean was missing, PDFs were stale, or a task was still open. Those descriptions belong to earlier checkpoints. The NX namespace is a new expansion plan and leaves the original ledgers intact.

## Where each kind of information lives

| Material | Location | Interpretation |
|---|---|---|
| Execution-ready packets | `packets/NX01.md` through `packets/NX36.md` | Mathematical scope, source reuse, proposed interfaces, examples, and acceptance pushes. |
| Machine roadmap | `roadmap.json` and `ROADMAP.csv` | Current proposed statuses, hard dependencies, supporting tracks, and 108 units. |
| Shared semantics | `architecture/PROGRAM_DESIGN.md` | Candidate identity, targets, operations, costs, uncertainty, and output contracts. |
| Cross-program integration | `architecture/SOURCE_REUSE.md` | Existing APIs and the precise new integration. |
| Runtime inventory | `provenance/SOURCE_API_INDEX.json` | AST-derived names actually present in bundled core source. |
| Historical bridges | `provenance/HISTORICAL_BRIDGES.md` | Dated prior-chat concepts and their remaining empirical or source obligations. |
| Companion code | `companion_sources/` | Unchanged pinned reference subsets, with explicit missing assets. |
| Mathematical review | `validation/` | Independent packet review and checks run while packaging. |
| Dense handbook | `HANDBOOK.md`, `HANDBOOK.html`, `HANDBOOK.pdf` | Assembled readable design document, not acceptance evidence. |

## Session completion

Complete a bounded batch and leave a usable checkpoint. State the exact accepted unit IDs, mathematical scope, changed files, tests actually run, measurement conditions, commit, remote status, and next dependency-ready unit. Include a complete source ZIP and current monograph/handbook links for a release. Do not make an outside reader reconstruct a result from chronological chat logs.

The user has authorized implementation, commits, and pushes within this project and prefers routine work to proceed without repeated confirmation. Preserve other contributors' changes, do not force-push, and do not treat an unresolved research question as an invitation to manufacture success. A bounded negative result with a precise family and an independently replayable witness can be a useful accepted result when the packet allows it.


# Paste this into Claude Code

You are continuing Singularity using the complete NX36 handoff. Work from the repository root. Read `CLAUDE.md`, `handoff/nx36/START_HERE.md`, and `handoff/nx36/architecture/PROGRAM_DESIGN.md`; run the new handoff CLI `verify`, `status`, and `next`. The old P01-P36 and OE01-OE14 programs are completed at the supplied release baseline. Preserve their evidence. NX01-NX36 are new proposed expansion tracks with 108 acceptance units; they have not been implemented merely because their packets exist.

Inspect the working tree and remote before editing, preserve unrelated changes, and integrate any newer compatible main work. The frozen reference is main `438ed423d7d389a1a483c61e0b50eca6a9fc0827`; do not reset a newer checkout to it. Run the core baseline suite. Use the bundle only for offline recovery, following its guide.

Begin with NX01-A/B/C unless a newer accepted checkpoint makes another unit dependency-ready. Read the complete packet and actual source before implementing. The thermal records already contain candidate-specific error bounds; reuse them. Build the exact heterogeneous scalar layer and independently check a finite-pool optimum. Keep reset semantics, strict separation, original candidate identities, rational costs, and measurement units explicit.

Use at most three accepted NX units in one bounded session unless I explicitly give a wider implementation scope. A research push is an acceptance unit, not one Git commit. Complete the proof or exact finite result, implementation, independent checks, retained evidence, manuscript update, and release/checkpoint needed by the selected scope. Commit and push compatible completed work without asking routine permission. Never force-push or discard another contributor's changes.

Reuse the pinned PerfectJet, PerfectPower, and DynaComp reference engines before creating a competing implementation. Inspect `COMPANION_SOURCES.json`: selected companion source is not a promise that every external runtime asset is present. In particular, PerfectPower already has differential-observable algorithms; NX31 should adapt them, then add target transport. DynaComp already has stability, correlated bounds, reduction, and recurrence machinery; new tracks integrate them into experiment selection.

Read the packet's hypotheses literally. Keep formal interface vectors separate from graph-realizable kernels, fixed-budget results separate from full-series results, scalar box panels separate from joint correlated sets, fixed parameters separate from adversarial switching, and finite candidate recognition separate from arbitrary fault discovery. Preserve the negative held-out scouting evidence and distinguish synthetic pilots from archive or physical measurements.

Use the exact standard-library core when sufficient. Optional heavy solvers need a concrete purpose, bounded work, and an explicit trust/dependency record. Estimate state spaces before enumeration. Return exact refusals or bounded unresolved intervals when resources are exhausted. Do not turn failed proof routes into negative mathematical theorems.

Update only the NX progress records relevant to accepted work. Each completed unit needs a concrete summary, existing evidence artifacts, checks actually run with scope, mathematical status, and a commit. A metadata validator cannot establish that a proof or physical model is true; supply the actual argument and independent comparison required by the packet. Keep proposed branches visibly proposed.

Finish with the accepted IDs and exact result, what changed and why, validation, commit and verified remote state, a complete packaged ZIP, the readable monograph/handbook link, and the next ready unit. The output should be understandable in plain words as well as formally specified in the documents.


# Program design: targets, populations, operations, and experiments

## The central object

An experiment program consists of a population of original candidates, a requested target, legal interventions, observation semantics, uncertainty, and cost. It may be finite and exact, continuous with certified bounds, or a restricted algebraic family. The backend must declare which class it supports. There is no claim of a universal algorithm deciding arbitrary nonlinear identification problems.

Write an original candidate as \(c\in\Omega\), its hidden state as \(x\), and its target as \(T(c,x)\). The target can be fault identity, a material property, a graph coefficient, a future wind functional, a period combination, or a movement-response contrast. Candidate identities and their multiplicities survive every compiled representation. A quotient preserving one target need not preserve another.

For a fixed experiment or terminating policy \(\pi\), define \(\mathcal Y_c^\pi\) as the complete set of possible observation transcripts under the declared model and uncertainty. Zero-error target identification is possible exactly when the transcript sets for target-incompatible candidates are disjoint. This formulation covers scalar intervals, joint zonotopes, finite noisy channels, and properly bounded stateful histories, but each needs its own effective decision method.

## Linear observable closure

In the exact finite-dimensional sector, states lie in \(V\), interventions are \(M_i\), and direct output rows form \(L\). The least future-observation space is

\[
W=\operatorname{span}\{\ell M_{i_k}\cdots M_{i_1}:\ell\in L,\ k\ge0\}.
\]

Finite dimension supplies an exact stopping rule: retain independent rows until every generator extension lies in their span. If basis rows form \(B\), return factorizations \(L=AB\) and \(BM_i=T_iB\). They certify that the quotient keeps every observation in the allowed language. Invisible vectors are \(\ker B\). This minimality is linear and relative to the formal state space and declared language. A restricted graph-realizable population can admit additional nonlinear or combinatorial compression.

Chronological words act on states with the latest matrix on the left. Every returned experiment must carry a chronological witness and be replayed in that convention. Parallel graph attachments commute, so they alone cannot reveal an ordering bug. Retain asymmetric/noncommuting examples as regression evidence.

## Costs and robustness are distinct

Positive attachment costs make affordable exact row search finite after rational costs are scaled to integer units. Cost-ordered span pruning preserves the cheapest nonzero distinction because a discarded row and every extension are combinations of no-more-expensive retained rows. It does not preserve the largest margin, best conditioning, or best noise amplification. Robust search requires those quantities explicitly.

For independent scalar error intervals, experiment \(e\) covers pair \(a,b\) when \(\lvert r_{e,a}-r_{e,b}\rvert>\rho_{e,a}+\rho_{e,b}\). Equality leaves a shared endpoint and is not separation. A finite panel is a weighted pair-cover problem under this geometry. Joint correlated panels instead compare complete sets; they can succeed even when every coordinate fails its individual interval test. Do not use scalar set cover as a substitute for joint convex separation.

Installation cost, intervention cost, observation cost, setup computation, per-query computation, and arithmetic bit cost should be recorded separately. Combining them requires declared conversion weights. Current thermal cost units are normalized accounting units, not measured money or electricity. A low per-query cost does not establish a setup-inclusive advantage before the break-even number of uses.

## Uncertainty contracts

Separate source-model discrepancy, discretization/transformation error, reduction residual, machine arithmetic, initial-state uncertainty, process disturbance, and sensor error. Add scalar bounds only after they refer to the same output and units. Preserve correlation when a nuisance is fixed across observations. Allow independent nuisance values in alternative candidate explanations unless a shared cross-hypothesis relation is independently known.

The thermal baseline starts at zero excess-temperature centre with a bounded reset box. Reset occurs independently before every panel member. A shared physical history has different semantics and cannot reuse the reset Bellman equation. The latter needs beliefs retaining original identity, possible current state, persistent nuisance, and the entire information prefix.

Uniform identification over continuous severity is generally impossible when every fault family approaches nominal at severity zero. Either bound severity away from zero, estimate a target interval, or return an unresolved class. A model-rejection outcome means no declared candidate fits; it does not guarantee detection of every possible unmodelled fault.

## Algebraic parameters and fibres

A parameter observation map \(\Phi_E(\theta)\) identifies target \(T(\theta)\) only when the target is constant on each admissible fibre. The tangent inclusion \(\ker D\Phi_E\subseteq\ker DT\) is a local necessary diagnostic in regular settings. It does not remove disconnected global branches. Quadratic targets on affine fibres admit explicit linear and Hessian conditions; curved fibres require the constraint geometry as well.

For a polynomial observation matrix, determine exceptional rank using the full determinantal ideal or its one-variable divisors. A selected basis determinant can vanish while another basis retains full rank. Denominators, excluded singular loci, and real parameter domains belong to the result. An algebraic root outside the declared interval is not an experimental obstruction inside it.

## Dynamic and differential extension

Physical-time linear responses have rational generating functions because a finite transition matrix advances time. An untruncated graph-height coefficient sequence need not have that transition structure and is not made rational by this analogy. Effective finite-prefix results need a closed recurrence, finite algebraic argument, or equivalent advance operator; coefficient-vector finiteness at one truncation is insufficient.

For parameter-dependent systems \(x'=A(t)x\), moving coordinates \(z=B(t)x\) are exact when \(B'+BA=TB\). Target recovery also requires \(c=LB\). Gauge changes \(z\mapsto G(t)z\) add the derivative term \(G'G^{-1}\) to the reduced connection. These equations make the quotient/transport bridge precise on constant-rank regular charts. Exceptional points require stratification rather than a fictional fixed-rank global bundle.

## Four kinds of result

Keep established mathematical background, proved project statements, exact finite computations, and proposed research targets explicit. A finite negative graph search is scoped to its population. A conditional external arithmetic result keeps its premise. A synthetic diagnostic result is not an empirical physical advantage. A held-out negative prediction result must not be relabelled as an advantage because a new feature is elegant.

The package's worked examples establish understanding and provide initial regression targets. They do not replace the full packet acceptance criteria. A roadmap tool verifies dependency and evidence-record consistency; it cannot make a future theorem true or validate a physical source model.

## Recommended outcome

For every accepted unit, leave a compact exact statement, an explanation in human sentences, the implementation and proposed/actual API distinction, a meaningful independent comparison, bounded retained evidence, and the effect on the full program. The eventual product answers a practical question: which action or measurement changes the target uncertainty enough to justify its total cost?


# Source reuse and integration boundaries

The complete Singularity baseline is executable source, not a scaffold. The companion directory contains pinned selections from three other projects. Read its manifest before attempting broad imports. Optional assets and unresolved imports are documented rather than replaced by guessed fixtures.

| Existing engine | Actual role | New integration in NX tracks |
|---|---|---|
| `singularity.observability` | Exact operator systems, invariant observation closure, cost filtration, cheapest distinguishing witnesses, replayable factorizations. | Typed spaces, arithmetic-compatible quotients, new application adapters. |
| `singularity.experiment_design` | Exact rational metrics, polynomial Gram matrices, orthogonal bases, finite-pool experiment scoring. | Stable target-specific sensor design and reconstruction conditioning. It is not the cheapest-word engine. |
| `singularity.robust_search` | Exhaustive and certified bounded margin searches on declared operator languages. | Expanded candidate sets and joint fidelity/experiment planning. |
| `singularity.panels` | Exact finite weighted panels and supported error geometries. | Heterogeneous radii, joint uncertainty oracles, optimistic/certain refinement bounds. |
| `singularity.thermal_diagnostics` | Source-bound full-model plate pilot, protocol pool, error bounds, symmetry and independent flux comparisons. | Larger faults, severity, adaptive history, sensor/actuator acquisition. |
| `singularity.locality`, `charges`, `separator_compiler` | Connected-support and charge/separator exact compilation. | Incremental local edits and reuse across structured populations. |
| `singularity.parametric`, `parameters` | Polynomial observability, rank/discrepancy strata, exact real-root isolation. | Larger observable modules and finite parameter-wide experiment designs. |
| `singularity.conductor`, `periodic` | Cyclotomic residues, finite sufficient cutoffs in periodic sectors. | Multi-frequency histogram recovery and more general effective-prefix questions. |
| PerfectJet Observatory selection | Adaptive finite-state diagnosis, preserved initial targets, action/order semantics. | Reset and shared-history thermal policies. |
| PerfectPower planning/lattice selection | Exact constrained populations, arithmetic transport, reconstruction, count/rank/unrank. | Fault-population compilation and integral observable quotients. |
| PerfectPower differential selection | Existing rational differential modules, scalar observable equations, period transport references. | NX31 target-transport adapter and NX33 moving-quotient integration. |
| DynaComp source selection | Sparse dynamics, reduction, correlated bounds, stability, long-time error, generating functions, certified machine execution. | Decide which model fidelity and physical experiment to buy. |

## Prevent duplicate implementations

Search for the required capability and read its tests before adding a module. A generic name in an old chat does not prove the source exists; conversely, a new roadmap name does not mean the mathematics needs rebuilding. The source inventory is AST-derived and records actual classes/functions from the bundled code. It is an orientation aid, not an exhaustive semantic dependency analysis.

PerfectPower already computes differential observation rows and universal scalar equations for supported modules. DynaComp already contains Lyapunov, recurrence, correlated-error, and machine-error tools. Singularity already has all-future exact closure and cheapest witnesses. Their new common use is a target-directed experimental decision with preserved identity, uncertainty, and cost.

## Companion import strategy

Keep companion files unchanged as reference snapshots. Initial adapters should either call a clearly optional dependency or port a small justified interface with attribution and exact cross-checks. Never silently add a second `perfectpower` package to the core import path and assume all of its catalogue/runtime assets are bundled. Use subprocess isolation or distinct development environments when package names or versions conflict.

Run the companion manifest byte check and selected smoke tests using its supplied helper. The successful smoke scopes are named in that evidence; they do not certify every selected module or the original complete repositories. Missing external datasets remain missing until acquired and bound to a concrete experiment.

## Source-state precedence

Current pinned source outranks old progress descriptions for implementation state. Historical chats explain motivations and hypotheses. The packet and ledger specify the new acceptance target. When they conflict, write a short decision explaining the source observation and corrected scope before coding. Preserve the original mathematical meaning of volume, energy, normalization, candidate target, and chronological word order.


# Shared exact interchange and experiment semantics

## Purpose

The packets propose several future APIs. This document is authoritative for shared NX interchange fields so that individually sensible implementations do not become mutually incompatible. Existing upstream schemas retain their established encodings. Import them through explicit validated adapters rather than silently renaming or weakening them.

## Exact numbers and matrices

Portable NX JSON represents a rational by `[numerator, denominator]`, both JSON integers, denominator strictly positive, greatest common divisor one, and zero represented as `[0,1]`. Reject booleans, floats, nonfinite values, duplicate keys, zero denominators, and noncanonical pairs in exact fields. Human-facing tables can display fractions normally. An upstream rational string or numerator/denominator object can be accepted by a named adapter with strict round-trip tests; it is not the same wire format.

A rational matrix records row and column counts and a rectangular list of rational entries. Empty dimensions need explicit shape rather than inference from an empty list. A positive-definite metric, positive-semidefinite form, covariance matrix, and arbitrary symmetric matrix are distinct semantic types even when their storage is identical. State the norm or uncertainty set a matrix represents.

For polynomial or rational-function values, record the coefficient field, variable order, exact coefficient encoding, sparse or dense convention, denominator, and excluded domain. An identity after denominator clearing is valid only where the original expressions are defined. Algebraic numbers need a defining polynomial and an isolating specification; a decimal approximation is not an exact algebraic identifier.

## Identity and populations

Candidate IDs refer to original configurations, not compiled aliases. Store target labels and reconstruction maps separately. If several configurations share a state or observation, retain their multiplicities. A count is not a posterior probability unless weights or a prior are declared. A finite population description must actually bound every free variable.

Models have source revisions and a semantic identity including parameter values, normalization, state ordering, boundary type, input and sensor maps, and units. A digest binds bytes; a mathematical source map explains what those bytes mean. No certificate can infer a physical calibration guarantee merely from a hash.

## Words, policies, and reset

Store intervention words in chronological order. For linear state maps the last operation acts on the left: word `[a,b]` sends a state to `M_b M_a v`. Observation rows and retained witnesses must use the same convention. List legal source and target types when an action changes the boundary or state space.

Every panel or policy records whether each experiment independently resets, continues from the preceding physical state, or uses a specified partial reset. Fixed calibration nuisances may persist across readings. Initial target labels remain attached to candidates after destructive actions. A current state alone is insufficient for a history-sensitive identification claim.

## Error geometry

An independent scalar interval, a joint box, a zonotope, an ellipsoid, and a stochastic likelihood are different contracts. A persistent common offset is not two fresh independent errors. Cross-candidate explanations generally quantify their unknown nuisance parameters independently. Within one candidate history, preserve the correlation assumptions actually justified by the model.

For ellipsoid shape matrix R, the convention is \(\eta^{\mathsf T} R^{-1} \eta \le \epsilon^{2}\), with R positive definite. Whitened observation weighting is therefore R^-1. If R is instead a precision matrix, label it explicitly and change the formulas. For movement signatures, the antisymmetric level-two statistic is twice the conventional signed area of the straight-line-closed path; retain that declared scale.

Strict separation excludes touching boundaries. Store open or closed parameter endpoints explicitly. Do not encode unresolved or unbounded results as JSON Infinity or a very large finite number; use a status with the applicable bounds and assumptions.

## Cost and optimization

Installation, reset, heating, switching, observation, setup computation, and repeated execution costs have named units. A combined objective records conversion coefficients and number of planned repetitions. Attachment costs are positive for the finite affordable-language guarantees; direct observation costs can be nonnegative where the theorem permits it.

An optimum names its search space: a supplied finite pool, every word up to a cost bound, a generated grammar, or a proved all-horizon family. A greedy result is a baseline. A feasible result is an upper bound. An independently checked lower bound is required to claim optimality. Exact span dependence supports cheapest nonzero distinction, not arbitrary noise-margin pruning.

## Progress evidence

The initial roadmap has 36 proposed tracks and 108 proposed units. Complete units need a nonempty evidence summary, existing repository-relative artifacts, actual check commands and scopes with successful exit codes, a commit, and a mathematical status. The handoff tool checks metadata consistency and evidence presence; it does not rerun arbitrary saved commands or decide whether the underlying research claim is true.

Supported statuses are `proposed`, `in_progress`, `blocked`, and `complete`. A track is complete exactly when its three units are complete. Mark blockers concretely. Preserve scoped negative results and counterexamples where allowed; do not manufacture completion by silently replacing a requested theorem with a weaker computation.


# Execution map

The ledger is authoritative for hard dependencies. Historical or packet prose links can be supporting connections. All 108 units initially remain proposed.

| Track | Design | Hard prerequisites | Supporting tracks | Units |
|---|---|---|---|---|
| NX01 | Candidate-specific uncertainty | None | None | A / B / C |
| NX02 | Correlated observation geometry | NX01 | None | A / B / C |
| NX03 | Whole populations of faults | NX01 | None | A / B / C |
| NX04 | Continuous severity and calibration freedom | NX03, NX02 | None | A / B / C |
| NX05 | Adaptive experiments with resets | NX01, NX03 | None | A / B / C |
| NX06 | Experiments with shared physical history | NX05, NX02, NX03 | None | A / B / C |
| NX07 | Purchase the intervention language | NX01, NX03 | None | A / B / C |
| NX08 | Stable target recovery | None | None | A / B / C |
| NX09 | Joint experiment, rank, and precision selection | NX01, NX08 | None | A / B / C |
| NX10 | All-horizon stopping certificates | None | None | A / B / C |
| NX11 | Remote-time evaluation | None | None | A / B / C |
| NX12 | Complete constrained protocol populations | NX01 | None | A / B / C |
| NX13 | Typed operator languages | None | None | A / B / C |
| NX14 | Parameter-wide observable modules | None | None | A / B / C |
| NX15 | Graph-realizable invisible directions | None | None | A / B / C |
| NX16 | Incremental connected-support compilation | None | None | A / B / C |
| NX17 | Low-rank physical fault transport | None | None | A / B / C |
| NX18 | Recovery conditioning and bit complexity | None | None | A / B / C |
| NX19 | Integer-compatible observational quotients | None | None | A / B / C |
| NX20 | Pell and residue experiment automata | None | NX19 | A / B / C |
| NX21 | Symmetry-adapted experiment channels | None | NX07, NX13 | A / B / C |
| NX22 | Multi-frequency arithmetic probing | None | NX14 | A / B / C |
| NX23 | Population geometry with preserved multiplicities | NX03, NX19 | None | A / B / C |
| NX24 | Effective finite-prefix theorems | None | NX13, NX14 | A / B / C |
| NX25 | Forecast-target sensor design | NX08, NX10 | None | A / B / C |
| NX26 | Nonlinear ambiguity witnesses | None | None | A / B / C |
| NX27 | Target-preserving multiscale transport | NX08, NX09 | None | A / B / C |
| NX28 | Reactive transport observability | NX25, NX26, NX27 | None | A / B / C |
| NX29 | Identifiable movement-test design | NX08 | None | A / B / C |
| NX30 | Ordered movement signatures | NX29 | None | A / B / C |
| NX31 | Target-directed period transport | None | None | A / B / C |
| NX32 | Monodromy as an experiment language | None | NX31 | A / B / C |
| NX33 | Moving observable quotients | NX31 | None | A / B / C |
| NX34 | Larger certified analytic visibility regions | None | None | A / B / C |
| NX35 | Proof-directed computational refinement | NX01, NX09 | None | A / B / C |
| NX36 | End-to-end experiment certificates | NX01, NX35 | None | A / B / C |


# NX01 - Candidate-specific uncertainty

## Scope, status, and the question being answered

This is a proposed expansion, not an accepted result. Preserve the existing thermal pilot and its source-pinned synthetic interpretation. The new task is to optimize and decode experiments using a different justified uncertainty radius for each candidate and experiment. No physical calibration, new fault population, global parameter robustness, or correlated-error claim is implied. The central question is whether replacing a conservative common envelope with the bounds already computed for individual candidates changes the cheapest guaranteed diagnosis.

Read `CLAUDE.md`, `docs/research/THERMAL_DIAGNOSTICS.md`, `src/singularity/thermal_diagnostics.py`, `src/singularity/panels.py`, and their tests before editing. The current function `protocol_pool` already returns `DiagnosticPool.error_bounds[e][c]`. It also sets `epsilon[e] = max(error_bounds[e])`; `DiagnosticPool.panel_epsilon` passes that common envelope to the existing panel backend. This is deliberate, documented conservatism rather than a missing simulator. `panels.coverage_masks`, `minimum_cost_panel`, `exhaustive_minimum_panel`, and `consistent_candidates` currently interpret a common positive radius per experiment, or exact separation when the radius argument is `None`. They do not accept a candidate-by-experiment radius matrix.

Reuse `AffineCandidate`, `simulate_protocol`, the sparse prefix cache inside `protocol_pool`, and the source fixture. Do not recompute radii through an unrelated adapter or alter the six candidate identities. Read `tests/test_thermal_diagnostics.py::test_exact_radius_propagation_and_cost` for the attained bound and negative-entry case. `robust_search.py::bounded_family_search` maximizes a single experiment's normalized margin; it is not the shared-panel optimizer and cannot replace this task.

## Mathematical semantics and derivation

For experiment \(e\), candidate \(c\), exact central reading \(r_{ec}\), and nonnegative rational radius \(\rho_{ec}\), define the closed interval

\[
I_{ec}=[r_{ec}-\rho_{ec},r_{ec}+\rho_{ec}].
\]

Under independently reset experiments and the declared product uncertainty contract, a panel \(P\) admits the box \(Y_c(P)=\prod_{e\in P}I_{ec}\). Two such boxes intersect exactly when their scalar intervals intersect in every coordinate. Therefore

\[
Y_a(P)\cap Y_b(P)=\varnothing
\iff \exists e\in P:\quad
|r_{ea}-r_{eb}|>\rho_{ea}+\rho_{eb}.
\]

The inequality is strict because closed intervals touching at one endpoint have a common possible observation. This equivalence makes minimum-cost panel selection weighted set cover on unordered candidate pairs, with heterogeneous masks. The robust decoder retains candidate \(c\) precisely when every selected reading belongs to \(I_{ec}\). A panel covers all required pairs if and only if this decoder identifies every candidate for every allowed observation vector. If the task only requires a target label, omit pairs sharing that target; retain the original identities in the result.

The thermal bound remains

\[
b_{0,c}=\rho_0\mathbf1,\qquad
b_{t+1,c}=|A_c|b_{t,c}+d_c,\qquad
\rho_{ec}=|C_{c,j}|b_{T,c}+\sigma_{ec}+\varepsilon_{ec}^{\rm red}.
\]

The current implementation accepts common scalar process, sensor, and reduction bounds. Candidate-specific panel logic must not silently turn those scalars into new certified physical bounds. Additional bound-generation interfaces need separately justified assumptions. For the current positive plate with normalized positive sensors and uniform initial/process boxes, the scalar expression is attained by the same-sign extreme disturbance. For arbitrary signed sparse models, absolute-value propagation is safe but can be conservative.

The refinement has a useful monotonicity check. Let \(\epsilon_e=\max_c\rho_{ec}\). Every common-envelope separating pair is also heterogeneously separated because \(\rho_{ea}+\rho_{eb}\le2\epsilon_e\). Consequently every old feasible panel remains feasible and the new optimum cannot cost more. This comparison concerns the same readings, costs, population, and uncertainty sets; changing any of them invalidates the simple inequality.

## Exact worked example

Take two candidates with readings \(r_a=0,r_b=1\), radii \(\rho_a=1/10,\rho_b=1/2\), and one experiment costing three units. Their intervals are \([-1/10,1/10]\) and \([1/2,3/2]\), so their gap is \(2/5\) and the experiment guarantees identification. Replacing both radii by \(1/2\) gives touching intervals \([-1/2,1/2]\) and \([1/2,3/2]\); that larger contract cannot guarantee identification. This is a gain from sharper assumptions, not evidence of a new measurement. Add a second example with reading difference equal to the radius sum and verify that separation is rejected.

## Proposed interfaces and retained data

The following names are proposals, not existing imports. Add `CandidateBoxPool(pool, radii, target_labels)` with an immutable `radii[e][c]` matrix, and `candidate_box_masks`, `minimum_candidate_box_panel`, `candidate_box_consistent`, and `candidate_box_ambiguity`. Accept zero radii directly, including mixtures of zero and positive entries; do not inherit the common backend's strictly positive noisy-margin restriction. Serialize exact rationals as canonical strings, never binary floats. A receipt records `schema: singularity.candidate-box-panel/1`, candidate IDs, protocol labels, exact readings, full radii, costs, target labels, selected indices, covered-pair mapping, optimal cost, search nodes, and independent-oracle cost.

Refactor the set-cover search through a small internal validated-mask kernel only if compatibility tests show old public behavior unchanged. The kernel must validate mask widths, nonnegative costs, candidate-pair order, and work budgets. Do not export a mask interface that permits unverified callers to pretend masks arose from valid readings. Keep the production conversion from radii separate from the independent oracle's direct interval-intersection calculation.

## Three concrete push units

**NX01-A - Contract and heterogeneous geometry.** Dependencies: current thermal and panel baseline. Add proposed `src/singularity/candidate_boxes.py`, `tests/test_candidate_boxes.py`, and `docs/research/CANDIDATE_BOXES.md`. Implement validation, masks, decoder, and overlapping-observation witnesses. Acceptance: exact intervals, zero-radius mixtures, touching endpoints, target-equivalent candidates, empty pools, duplicate original identities, malformed shapes, and old-envelope mask inclusion all behave as proved. Independently compute interval endpoints in tests without calling production mask helpers.

**NX01-B - Exact optimization and dual comparison.** Depends on NX01-A. Introduce the minimum-cost solver adapter and a genuinely separate small exhaustive oracle scanning subsets and testing box intersections directly. Acceptance: all tiny rational pools match the oracle in feasibility and optimum; compare against independent Dijkstra search on pair-cover subsets. Test dominated experiments and zero-cost experiments without creating infinite repeated-word searches. Never claim the greedy result is optimal merely because it matches one fixture.

**NX01-C - Thermal integration and retained result.** Depends on NX01-B. Add proposed `scripts/candidate_box_thermal.py`, `results/candidate_box_thermal.json`, and an application subsection. Compile the unchanged 112-protocol pool and six source-derived candidates. Acceptance: all central readings and individual radii match the original diagnostic compilation; the common-envelope optimum remains a valid incumbent; independent oracle agrees where affordable. Retain unchanged or improved cost honestly. An improvement is not required for mathematical acceptance.

## Complexity, budgets, and failure modes

Mask construction costs \(O(EK^2)\) rational comparisons for \(E\) experiments and \(K\) candidates. Exact weighted set cover is worst-case exponential. Preserve `max_nodes=10**6` as an explicit default ceiling, and give exhaustive comparison a separately bounded subset budget. For the six-candidate pool there are only 15 pair bits; an independent cover-state oracle has at most \(2^{15}\) masks. Record arithmetic bit lengths as horizons grow. Do not build the dense 870-dimensional homogeneous lift for six 144-state models; `affine_operator_system` deliberately refuses dimensions above its default 256 bound.

Repeated tests with adversarial bounded errors do not automatically average noise away. Correlated persistent nuisance invalidates product-box necessity, although box separation remains sufficient for a larger uncertainty set. A lower computed radius without a proof is an unsupported change of problem. Unknown faults remain outside this finite population; an empty consistency set is a model-contract failure signal, not identification of a new fault.

## Stop, resume, and acceptance bookkeeping

Run focused new tests, original thermal/panel tests, `python scripts/thermal_diagnostics.py --check`, and repository/link checks after integration. Do not mark NX01 accepted until the independent optimization comparison and manuscript statement agree. Save a checkpoint containing candidate/source hashes, chosen protocols, exact uncertainty contract, command lines, checks actually run, solver budgets, open concerns, and next dependency-ready push. An exceeded search budget is `inconclusive`, never `infeasible`. Preserve the old receipt rather than overwriting its historically different common-envelope claim.

### Compatibility and reproducibility gate

Before accepting any refactor, run `PYTHONPATH=src python -m unittest discover -s tests -p 'test_panels.py' -v` and the matching thermal test file, then compare the old retained result without regenerating it. Test a deliberately asymmetric radius matrix whose transpose has the same total entry count: shape validation alone may miss accidental axis reversal when experiment and candidate counts coincide. Include distinct candidate identifiers with identical centers but different radii; they remain distinct possible hypotheses and cannot be declared separated when their closed intervals share the common center. A receipt should expose the raw margin \(\Delta_{eab}=|r_{ea}-r_{eb}|-\rho_{ea}-\rho_{eb}\), making every positive, zero, or negative coverage decision inspectable.


# NX02 - Correlated observation geometry

## Scope and inherited implementation

This proposed track replaces independent-coordinate error boxes by joint affine uncertainty sets for a finite panel. It does not assume every uncertainty source is correlated, nor that every correlation is beneficial. The objective is guaranteed identification under a declared persistent-nuisance model, with checkable witnesses of separation or overlap. Distinguish an exact uncertainty-set model from a safe outer approximation throughout the implementation.

The actual source `src/singularity/thermal_diagnostics.py::protocol_pool` propagates a componentwise radius and compiles one common scalar envelope per protocol. Its comments explicitly say every panel member has a separate reset. `DiagnosticPool.error_bounds` retains candidate-specific scalar bounds, but not shared calibration generators. `src/singularity/panels.py` has box and Euclidean-ball APIs: `coverage_masks`, `minimum_cost_panel`, `l2_separates`, `minimum_cost_l2_panel`, and consistency/ambiguity routines. None is a correlated-zonotope solver. `src/singularity/experiment_design.py::RationalMetric` is an exact metric object, not a substitute for a structured feasible observation set. `robust_search.py` assumes one noise bound per observation and optimizes a single experiment.

Reuse exact readings, rational validation conventions, candidate identity, and protocol labels. Read `docs/research/THERMAL_DIAGNOSTICS.md`, `docs/research/PANELS.md`, `tests/test_panels.py`, and `tests/test_thermal_diagnostics.py`. The older DynaComp correlated-domain work motivates this track, but do not invent an existing Singularity import for that external machinery. The first implementation should remain standard-library based and bounded to small exact feasibility problems.

## Geometry, semantics, and the separating theorem

For a selected panel with \(p\) readings, declare

\[
Y_c=\mu_c+G_c[-1,1]^{m_c},
\]

where \(\mu_c\in\mathbb Q^p\) contains central predictions and generator columns encode bounded nuisance sources. A persistent sensor offset uses one column shared across all relevant readings. Independent reading errors use separate diagonal columns. Independent physical resets do not reset a persistent calibration parameter unless the contract explicitly says so.

Two candidates are compatible with the same observation exactly when

\[
G_a\xi-G_b\eta=\mu_b-\mu_a,
\qquad -1\le\xi_i,\eta_j\le1.
\]

Use independent nuisance vectors for competing hypotheses unless a problem explicitly asks for comparison at the same nuisance value. The alternatives are different possible worlds. Artificially coupling \(\xi=\eta\) can manufacture a distinction that no observer can guarantee. Within each world, however, the same persistent source must remain shared across its panel coordinates.

A rational contrast \(w\) gives the support radius

\[
h_c(w)=\|G_c^\top w\|_1.
\]

If

\[
|w^\top(\mu_a-\mu_b)|>h_a(w)+h_b(w),
\]

then the projected intervals are disjoint, so the full sets are disjoint. Conversely, disjoint compact convex polytopes have a strict separating hyperplane; with rational input one can choose a rational witness. Thus either a primal overlap witness or a strict rational contrast can certify a pair. A floating solver's status string is not the certificate. The replay checker should verify the displayed equality and coordinate bounds, or the displayed strict rational inequality, directly.

The support proof is elementary: maximize \(w^\top G\xi\) over independent \(\xi_i\in[-1,1]\), choosing each sign to match \((G^\top w)_i\). Summing absolute coefficients yields the exact support. If a nonlinear physical uncertainty map is enclosed by a zonotope, separation proves robustness for that enclosure; intersection may be only inconclusive because the enclosure can contain physically impossible combinations.

## Exact worked example

Let

\[
\mu_a=(0,0),\quad\mu_b=(1,-1),\quad
G_a=G_b=\begin{pmatrix}1&1/10&0\\1&0&1/10\end{pmatrix}.
\]

The first generator is a persistent offset and the other two are independent sensor errors. Every individual reading interval overlaps between candidates. For \(w=(1,-1)\), however, the persistent column cancels. The center difference has absolute contrast two, and each candidate's support radius is \(1/5\). Hence \(2>2/5\), proving joint identification. Replacing the persistent column by independent unit columns destroys this guarantee. The benefit comes from a justified shared error source, not from changing the central readings.

## Proposed API and schemas

Proposed `JointObservationFamily` stores ordered candidate IDs, experiment IDs, rational centers, generators, source labels, reset semantics, and an `exact_set` flag. Proposed `project_panel`, `joint_pair_certificate`, `verify_joint_certificate`, `joint_consistent_candidates`, and `minimum_joint_panel` are future functions. Do not mark them as current public APIs. A certificate record uses `schema: singularity.joint-observations/1`, candidate pair, panel coordinates, generator hashes, `kind: overlap` with bounded coordinates, or `kind: separating_contrast` with rational coefficients and a positive support gap.

Generator labels need provenance such as `persistent:ambient_offset`, `reset:e12:initial_cell_7`, or `measurement:e12:sensor_noise`. Coordinate projection must preserve the same generator column across experiments. Applying a fresh interval envelope independently to each row discards the information this track exists to retain. Unknown solver outcomes must remain explicit. Rational infeasibility can be checked through an elementary Fourier-Motzkin elimination certificate for tiny systems, or a carefully specified exact linear-programming certificate. Avoid adding a large optional solver dependency without documenting why the core cannot provide the bounded fixture checker.

## Three concrete push units

**NX02-A - Joint sets and rational witness checker.** Depends on NX01's candidate-specific contract. Add proposed `src/singularity/joint_uncertainty.py`, `tests/test_joint_uncertainty.py`, and `docs/research/JOINT_UNCERTAINTY.md`. Acceptance: support functions, projection, overlap witnesses, strict contrasts, zero generators, rank-deficient sets, touching sets, and malformed dimensions are checked exactly. Reject a contrast whose gap is zero. Independently verify the worked example by eliminating the common offset algebraically.

**NX02-B - Complete small-panel optimizer.** Depends on NX02-A. Add a bounded exact feasibility engine and exhaustive panel search. For each panel require every target-distinct candidate pair to be disjoint. Acceptance: a second tiny-polytope oracle agrees, all subset choices up to a declared experiment count are considered, and both successful and ambiguous panels have replayable witnesses. The optimum is over that finite panel pool. Do not reuse weighted set cover: joint separation can occur without any coordinate separating a pair.

**NX02-C - Persistent thermal nuisance pilot.** Depends on NX02-B. Add proposed `scripts/joint_thermal.py` and `results/joint_thermal.json`. Introduce a persistent output offset with explicit bounds, independent sensor noise, and separately reset initial boxes. Acceptance: exact predicted centers match the old simulator; generator assembly agrees with a separately derived affine observation map; selected-panel results are compared with box outer approximations. Retain any cost change and an explicit contrast. Do not model multiplicative uncertain gain as affine unless the nonlinear remainder is enclosed or the model is exactly affine in that gain.

## Complexity and resource discipline

Support checking costs polynomial time in displayed matrix size. Finding a feasible overlap or separating witness is a linear-programming problem; naive elimination can grow exponentially. Selecting a cheapest panel is combinatorial and generally remains exponential. Begin with at most ten panel coordinates, six candidates, and twelve nuisance generators per candidate, with explicit elimination-row and subset ceilings. Record rational numerator/denominator bit lengths. Expand only after a retained small complete comparison exists. A budget refusal must not be interpreted as separation or intersection.

## Counterexamples and stop/resume rules

A covariance matrix does not define a deterministic bounded uncertainty set. A Gaussian confidence region is a different probabilistic contract and cannot silently replace worst-case robustness. A shared nuisance should not be forced equal across competing hypotheses unless externally known. Outer-set intersection cannot disprove physical identifiability. A linear dependence among reading rows does not imply a reading is useless for robust geometry or averaging under a separately stated stochastic model.

Checkpoint after each unit with matrix/source hashes, nuisance provenance, exact-set versus enclosure status, solver budgets, primal or separating witnesses, and commands actually run. Preserve the current independent-reset pilot unchanged as a historical comparison. Run original panel, thermal, metric tests and link checks. If exact feasibility remains unimplemented, finish NX02-A honestly and leave B/C pending; a library of sufficient contrasts alone is not a complete joint-panel optimizer.

### Cost and comparison protocol

A joint panel costs the sum of its actual separately reset experiments, as in the existing pilot. Shared calibration is a statistical or deterministic relation between their outputs; it does not imply shared heating or a cheaper reset. Compare three models using identical central readings: the original common boxes, NX01 heterogeneous boxes, and the justified joint generators. Each smaller set can only enlarge the feasible panel collection, but strict improvement is empirical and need not occur. Check an example where a falsely correlated generator gives a cheap but invalid answer, then restore independent generator columns and verify that the alleged certificate fails. This adversarial fixture is more useful than another easy successful separation.


# NX03 - Whole populations of faults

## Scope and baseline

The current six thermal candidates are a finite demonstration, not an exhaustive fault catalogue. This proposed track defines a constrained population of actual bond-fault configurations, preserves every original mask, and connects its exact completion counts to experiment design. Its first population is twelve selected bonds with at most two fully blocked bonds: \(1+12+\binom{12}{2}=79\) masks. Global conductance, heater, and loss hypotheses are not automatically crossed with those masks.

Read `src/singularity/thermal_diagnostics.py::build_plate_candidates`, `AffineCandidate`, `protocol_pool`, `src/singularity/panels.py`, and the retained source fixture. The existing plate builder explicitly assembles six named models and only two particular blocked bonds. Its model definition is reusable; its fixed candidate list is not a general fault population. `src/singularity/population.py::HeightPopulation` enumerates bounded integer graph-height assignments with graph-energy constraints. It demonstrates original-object count/rank/unrank discipline, but it is not a Boolean fault-mask engine and should not be repurposed under misleading names.

The older PerfectPower completion planner supplies the conceptual pattern: count completions of a prefix, preserve multiplicity, and reconstruct the original feasible object. This packet does not claim its external code is already vendored or formally proves the new population. Existing thermal tests have an independent undirected-flux oracle and enforce preservation of row sums when a bond is removed. Reuse those mathematical checks, extending the oracle to arbitrary declared bond sets without importing the new matrix assembler.

## Population and physics contract

Let the canonical source graph have ordered undirected bonds \(e_1,\ldots,e_m\). A mask \(\theta\in\{0,1\}^m\) satisfies declared integer constraints \(R\theta\le b\), including \(\sum_i\theta_i\le s\). Set

\[
\Omega=\{\theta\in\{0,1\}^m:R\theta\le b\},\qquad
A_\theta=A_0+k\sum_i\theta_i v_iv_i^\top,
\quad v_i=e_{u_i}-e_{v_i}.
\]

For fully removed distinct bonds, this update deletes the two off-diagonal conductances and restores each conductance on its endpoint diagonal. It preserves the original row sum \(1-\lambda\). Removing only off-diagonal entries changes ambient loss and describes a different fault model. Repeated bond IDs must be rejected or canonicalized before interpreting a Boolean mask; double-removing one bond creates a nonphysical negative conductance. Preserve original cell and bond labels even when graph automorphisms exchange them.

A 12 by 12 nearest-neighbour plate has \(2\cdot12\cdot11=264\) bonds. The full up-to-two-edge-fault population has \(1+264+\binom{264}{2}=34,981\) masks. This count does not imply that simulating every mask under 112 long protocols is affordable or that every location is identifiable. Start with the 79-mask constrained pilot and only expand after reporting measured cost and exact cover-state dimensions.

For a prefix \(p\), let \(C(p)\) count feasible completions. Then

\[
C(p)=C(p0)+C(p1),\qquad
\operatorname{rank}(p1\cdots)=C(p0)+\operatorname{rank}_{p1}(\cdots).
\]

Lexicographic ordering makes rank and unrank exact inverses. Memoization may merge prefixes with identical future constraint states, but its stored completion counts retain the number of original masks. Conditioning on observations defines \(\Omega_D\); count it by retaining masks whose predicted observation sets contain the data. A count is not a probability unless a prior over original masks is declared. Uniform over compressed states is generally not uniform over faults.

## Exact worked example

Take three ordered bonds and at most one fault. The four masks are \(000,001,010,100\) in lexicographic order. Define two illustrative exact readings

\[
r_1(\theta)=\theta_1+\theta_2,
\qquad r_2(\theta)=\theta_2+2\theta_3.
\]

The reading pairs for \(000,001,010,100\) are respectively \((0,0),(0,2),(1,1),(1,0)\). Either coordinate alone leaves ambiguity; both identify all original masks. Prefix `0` has three completions, so mask `100` has rank three. This is an algebraic population fixture, not a claim that these exact linear readings occur on the plate. For a physical tiny check, a two-by-two plate has four bonds and eleven configurations with at most two removed bonds; enumerate these independently by combinations.

## Proposed API and data records

Proposed `FaultPopulation` accepts canonical bond IDs, Boolean linear constraints, and work budgets. Methods `count`, `rank`, `unrank`, `iterate_masks`, and `condition` are new interfaces. Proposed `fault_candidate(source, mask)` produces an `AffineCandidate` whose identifier includes a canonical original-mask encoding. Store structural equivalence as extra metadata only; never delete equal-reading candidates unless the target explicitly identifies them.

A population manifest uses `schema: singularity.fault-population/1`, source-model digest, ordered labeled bonds, constraint matrix and bounds, lexicographic order, exact count, selected masks or reconstruction rules, completion-state count, and independent comparison. A diagnostic receipt records whether the target is exact location, fault count, any-fault detection, or another declared map \(T(\theta)\). Only pairs with distinct targets require separation; original masks must remain recoverable when returning an ambiguity class.

## Three concrete push units

**NX03-A - Exact constrained mask population.** Dependencies: existing source fixture and model contract. Add proposed `src/singularity/fault_population.py`, `tests/test_fault_population.py`, and `docs/research/FAULT_POPULATIONS.md`. Acceptance: tiny populations agree with direct products and combinations, every rank/unrank round trip succeeds, conditional counts sum correctly, infeasible constraints yield zero, and malformed or unbounded non-Boolean domains are rejected. Include constraints coupling nearby bonds, not only cardinality caps.

**NX03-B - Physical candidate compilation.** Depends on NX03-A. Add a generalized blocked-bond constructor without changing `build_plate_candidates` defaults. Acceptance: source nominal model is identical; every tiny mask matches independent undirected-flux evolution; row sums, symmetry, nonnegativity, and heater/sensor definitions are preserved. Exact configuration IDs survive identical predicted outputs. Check a two-bond shared-endpoint defect explicitly and retain all eleven tiny physical candidates.

**NX03-C - Seventy-nine-configuration diagnosis.** Depends on NX03-B and NX01. Add proposed `scripts/fault_population_diagnostics.py` and `results/fault_population_diagnostics.json`. Acceptance: all 79 original masks are counted, assembled, and available to the decoder; retained readings and bounds are independently spot-checked through flux evolution; selected panels have checkable pair coverage and a stated optimality or budget-limited status. Report unavoidable symmetry classes honestly. An exact optimum is required only when the bounded optimizer actually completes; otherwise the push remains computationally partial.

## Complexity, bounds, and interpretation

For a simple cardinality cap, completion counts have closed forms and compact dynamic programming. General Boolean inequalities can require exponentially many residual states. Enumerating \(K\) candidates and \(E\) protocols costs roughly \(O(KPs+KEn)\) sparse rational operations with prefix sharing, where \(P\) is the number of distinct prefixes, \(s\) matrix nonzeros, and \(n\) the state dimension; shared prefixes must not be charged an extra horizon factor. Pair coverage has \(K(K-1)/2\) bits: 3,081 for 79 candidates. A cover-state Dijkstra oracle would have an infeasible \(2^{3081}\) ceiling, so reserve it for restricted subpopulations and use independently checked feasibility plus bounded search for the larger pilot.

Keep the first full population at 79 masks and a protocol subset chosen by a declared rule, then measure simulation, pair construction, and search separately. Do not call a heuristic answer a globally cheapest panel. Source hashing establishes provenance; it does not prove that the real plate follows this model. An unknown real fault can remain consistent with a retained configuration or with none.

## Stop and resume

Leave exact prefix counts, model digests, candidate-ID mapping, observation contracts, measured work, search bounds, and unfinished pairs in the checkpoint. Run the existing source replay and focused population/thermal/panel tests. Preserve P01-P36 and OE ledger statuses; this future NX track starts pending. A symmetry obstruction is a useful mathematical outcome and can direct NX07's sensor-language repair. It is not permission to quotient away location identities that the stated target requires.

### Completion and identity audit

Choose and retain the twelve pilot bonds by explicit row-major endpoint pairs, not a selection rule that can change when another module changes iteration order. Store the exact ordered list in the population manifest. Independently verify that summing completion counts over a full prefix partition equals 79 and that every returned mask respects all original constraints. When conditioning on data, preserve an exact original-mask witness for every nonempty compressed state. If many configurations have identical predictions, report both the number of behavioral classes and the number of original configurations in each class. Neither the class count nor a uniformly sampled class is a substitute for the complete original population.


# NX04 - Continuous severity and calibration freedom

## Scope, dependencies, and existing source crosswalk

This proposed track upgrades a finite point-hypothesis catalogue into families with partial bond blockage and uncertain calibration. Its purpose is to locate guaranteed detectable-severity regions, unavoidable family overlaps, and parameter cells needing better sensors. It does not infer physical parameter intervals from the synthetic source. The user or a separately documented modelling argument must supply those intervals.

The current `build_plate_candidates` uses exact point values: nominal conductance \(1/8\), nominal loss \(1/100\), half conductance, half heater gain, doubled loss, and two fully removed bonds. `AffineCandidate` stores rational matrices, heater, and sensors. `simulate_protocol` and `protocol_pool` evaluate exact rational parameter samples; they do not certify every point of a continuum. `tests/test_thermal_diagnostics.py` checks positivity and row sums only for the retained finite models. `src/singularity/parameters.py` and `src/singularity/parametric.py` exist in this repository, but inspect their actual domains before reusing them: a graph discrepancy root or operator-rank stratum is not automatically a nonlinear thermal identification solver.

Read `docs/research/THERMAL_DIAGNOSTICS.md`, the source fixture, `src/singularity/thermal_diagnostics.py`, and NX01/NX02 uncertainty contracts. NX03's canonical bond IDs provide the location catalogue. The historical PerfectJet fibre criterion explains the aim: a target is identifiable if it is constant on every observation fibre. Rank at one parameter point provides only local information and cannot prove global uniqueness across the complete box.

## Model family and severity semantics

Use \(\alpha=0\) for nominal conductance and \(\alpha=1\) for a fully blocked specified bond. With \(v=e_u-e_v\), define

\[
A_{f}(\theta,\alpha)=(1-\lambda)I-kL+k\alpha vv^\top,
\quad b(\theta)=g b_0,
\quad \theta=(k,\lambda,g)\in\Theta.
\]

The remaining conductance on that bond is \(k(1-\alpha)\). For the grid, \(k\ge0\), \(\lambda>0\), and \(4k+\lambda\le1\) suffice for entrywise nonnegativity of the nominal stencil; removing conductance preserves that property and row sum \(1-\lambda\). The box \(\Theta\) must be intersected with these admissibility conditions. A parameter family violating them is not covered by the simple positivity/contractivity proof.

For panel \(P\), write \(\Phi_P(f,\theta,\alpha)\) for its exact predicted vector and \(Y_f(P)\) for all predictions plus allowed observation error. Guaranteed distinction requires

\[
Y_f(P)\cap Y_h(P)=\varnothing.
\]

Competing candidates may use different admissible calibration parameters \(\theta_f\) and \(\theta_h\). Requiring equality of their nuisance parameters answers the easier and different question of discrimination with known shared calibration. Within a single possible world, its fixed parameters persist across separately reset experiments. Do not replace that shared parameter by independent choices in each coordinate unless deliberately forming a conservative outer enclosure.

Finite-horizon observations are polynomial in parameters when the matrix and input map are polynomial in them. Repeated multiplication increases degree with horizon, so exact symbolic expressions can grow quickly. Derivative rank can locate local identifiability, while global separation requires optimization or exclusion over both competing parameter sets. Interval or Bernstein subdivision may certify a positive gap, but a zero/touching gap can prevent termination. Return `unresolved`, not a spurious proof of equality or separation.

## Why a positive minimum severity matters

At \(\alpha=0\), every location-labelled fault family contains the nominal model. By continuity, as \(\alpha\downarrow0\), any fixed finite panel's fault discrepancy tends to zero. With positive additive observation error, uniform robust detection across every \(\alpha>0\) generally fails. Therefore define a detectable frontier over \(\alpha\in[\alpha_{\min},1]\), or ask for a parameter-dependent margin rather than falsely claiming detection arbitrarily close to nominal.

Exact zero-noise identification is a different question and must be reported separately. Two different fault locations can also remain related by reflection throughout an entire severity interval when the heater and sensors are symmetric. More parameter samples cannot overcome that all-horizon obstruction. Such an overlap is a precise reason to invoke NX07's sensor/actuator repair.

## Exact worked example

Consider the scalar family

\[
x_{t+1}=a(\alpha)x_t+gu_t,\quad
 a(\alpha)=1/2-\alpha/4,\quad g\in[1,2],\quad x_0=0.
\]

Apply \(u_0=1,u_1=0\) and record both times. The noiseless transcript is \((y_1,y_2)=(g,a(\alpha)g)\), so \(y_2/y_1=a(\alpha)\), with a denominator uniformly bounded below by one. A first-time reading alone reveals gain but no severity. The second-time scalar families for nominal \(\alpha=0\) and fault \(\alpha\in[1/2,1]\) overlap: nominal values range from \(1/2\) to one, while faulty values include that range's lower part. The joint transcripts are disjoint because their slopes are respectively \(1/2\) and at most \(3/8\). This is a concrete global-nuisance example, not merely a Jacobian argument. For an explicit robust bound, use the contrast \(h=y_1/2-y_2\). Its noiseless nominal value is zero and its faulty value is at least \(1/8\). If each reading error is at most \(\delta\), each contrast error is at most \(3\delta/2\); the two families are certainly separated whenever \(\delta<1/24\). This avoids dividing noisy intervals and provides a rational certificate independently of symbolic subdivision.

## Proposed interfaces and data schemas

Proposed `ThermalParameterDomain` records rational bounds, admissibility inequalities, fixed-within-world parameter names, severity convention, and source digest. Proposed `ParametricFaultFamily`, `panel_parameter_map`, `certify_family_separation`, and `severity_frontier` are future APIs. A result uses `schema: singularity.parametric-fault-separation/1`, competing family IDs, independent parameter domains, selected panel, observation-error contract, proof kind, rational covering cells, separation lower bounds, explicit overlap witnesses where available, and unresolved cells. Distinguish a sample evaluation receipt from a continuum certificate.

A witness of overlap contains two complete parameter assignments and a common possible observation, checked against both family maps and error sets. A separation certificate covers the full compact product domain with validated strict gaps or another complete exact argument. Generic rank, finitely many successful samples, and plotting apparent separation do not satisfy that obligation.

## Three concrete push units

**NX04-A - Family semantics and exact sample oracle.** Depends on NX03. Add proposed `src/singularity/thermal_parameters.py`, tests, and `docs/research/THERMAL_PARAMETERS.md`. Acceptance: \(\alpha=0,1\) reproduce nominal and full blockage exactly; arbitrary rational severities match independent edge-flux updates; admissibility and nuisance-sharing semantics are validated. Retain the scalar worked example and reject ambiguous severity conventions.

**NX04-B - Certified small-domain separation.** Depends on NX04-A and NX02. Build symbolic or validated polynomial maps for a tiny plate and short panels. Acceptance: a full-domain certificate agrees with independent rational sample checks and analytic examples, but samples are not the proof. Include an explicit family-overlap witness, a strict separating region, a zero-margin touching region, and budget-limited unresolved output. Record all subdivisions and error sources.

**NX04-C - Location/severity frontier pilot.** Depends on NX04-B. Add proposed `scripts/thermal_severity.py` and `results/thermal_severity.json`. Begin with two reflected and two non-reflected bonds, then expand toward 264 locations only after resource estimation. Acceptance: report the complete declared domain, certified severity bands, sensor-dependent ambiguity classes, and exact or enclosed margins. A negative result explaining calibration mimicry is acceptable and valuable; an unproved uniform frontier is not.

## Complexity, failure modes, and checkpoints

Polynomial degree grows with horizon and multivariate coefficient counts can grow combinatorially. Product-domain subdivision doubles nuisance dimensions when comparing hypotheses. Begin with at most three free calibration parameters, one severity parameter per hypothesis, four bonds, and horizon four; set explicit cell, degree, coefficient, and wall-time budgets. Avoid launching a full 264-location continuum comparison before a retained tiny certificate works.

Nonzero sensitivity does not imply global identifiability; a locally full-rank map can fold and intersect itself. Replacing independently unknown nuisance values by a common value can invent robustness. Sampling only extrema fails for nonmonotone parameter responses. Endpoint overlap is genuine ambiguity for closed uncertainty sets. Save the exact domain, map-generation code version, subdivision frontier, certified cells, witness assignments, and remaining unresolved comparisons. Resume from that certificate frontier without silently tightening parameter ranges. Keep this track pending until every claimed continuum region has a replayable proof or validated enclosure argument.

### Independent continuum checks

Choose at least one short-horizon response whose polynomial can be derived manually from two sparse updates. Compare every symbolic coefficient with this independent derivation, not just evaluations produced by the same matrix builder. For a certified parameter cell, replay the enclosure from rational endpoints and the displayed polynomial, and verify that the cells cover the entire declared domain without gaps. Subdivision cells may share boundaries; the strict margin requirement must also hold on those boundaries. Preserve a rational interior overlap witness where possible so that ambiguity does not depend on trusting a numerical optimizer. The source-level nominal fixture remains the anchor when changing parameter coordinates or gain conventions.


# NX05 - Adaptive experiments with resets

## Task and current implementation boundary

This is a proposed exact decision-policy engine for a finite candidate population and a finite experiment pool. Every test starts from its own declared reset; the chosen next test may depend on all observations so far. The initial version assumes a memoryless uncertainty contract across resets: for each candidate and test, any value in its declared interval can occur independently of earlier tests. Persistent nuisance and shared physical state belong to NX02/NX06 and require larger beliefs.

The existing `src/singularity/panels.py::minimum_cost_panel` chooses a fixed set before observing outcomes. `consistent_candidates` decodes a completed fixed panel. `src/singularity/robust_search.py` selects one bounded-cost experiment by margin, not an adaptive tree. The thermal `protocol_pool` already supplies separately reset experiment labels, exact rational readings, and costs. NX01 supplies heterogeneous intervals and target-label semantics. These pieces provide a grounded input representation; there is no existing adaptive-policy function in the reviewed thermal module.

Read `CLAUDE.md`, `docs/research/PANELS.md`, `src/singularity/panels.py`, `src/singularity/thermal_diagnostics.py`, and NX01. The historical PerfectJet adaptive examples motivate the Bellman design, but do not assume their solver is integrated here or that their reported two-versus-three examples are thermal measurements. The new solver needs independent small-tree comparison and correct continuous-observation branching.

## Finite abstraction of continuous bounded readings

Let \(S\) be the current set of possible original candidate IDs, with target \(T(c)\). Test \(e\) produces a scalar value in closed interval \(I_{ec}\) if \(c\) is true. After observing \(y\), update

\[
S_{e,y}=\{c\in S:y\in I_{ec}\}.
\]

Collect all distinct interval endpoints for the candidates in \(S\). Candidate membership is constant on each open interval between consecutive endpoints and on the two exterior rays; it can differ at each endpoint itself. Therefore enumerate singleton endpoint cells separately from open interval cells. Rational midpoints represent bounded open cells; suitable rational exterior representatives handle rays. Ignore empty-consistency cells in worst-case analysis, while preserving an explicit runtime response for an observation outside every declared candidate interval.

Closed endpoint semantics matter. For \(I_a=[0,1]\) and \(I_b=[1,2]\), every value below one indicates only \(a\), every value above one indicates only \(b\), but the endpoint one leaves both possible. A brancher using open intervals alone incorrectly claims guaranteed identification. Zero-radius intervals require singleton cells and work naturally with this representation.

For worst-case cost, a terminal belief has a single target label, not necessarily a single original candidate. Define

\[
V(S)=0\quad\text{if }T\text{ is constant on }S,
\qquad
V(S)=\min_e\left[c_e+\max_{Q\in\mathcal C_e(S)}V(S_{e,Q})\right].
\]

Here \(\mathcal C_e(S)\) contains all nonempty realizable membership cells. Costs are positive rational numbers. Under the initial memoryless interval model, the set \(S\) is a sufficient state: past numeric values matter only through the candidates they eliminate. If a test has a possible branch equal to \(S\), it cannot be the first move of an optimal finite worst-case stationary policy; the adversary can choose that non-progress branch, and paying for it cannot improve the remaining same-state problem. Retain this as a proved restriction or use a bounded-depth Bellman definition before claiming an unrestricted optimum.

A proper guaranteed policy can be reduced to strictly shrinking beliefs along every nonterminal branch, giving depth at most \(K-1\) for \(K\) original candidates. This argument relies on the declared memoryless reset semantics and no hidden parameter learning. Repeated noisy tests do not average adversarial bounded error away. If an earlier reading constrains a persistent gain, then \(S\) alone is not sufficient and this theorem no longer applies.

## Exact worked example

Take four candidates \(A,B,C,D\), zero error, and three tests of unit cost. Test \(e_0\) reads zero on \(A,B\) and one on \(C,D\). Test \(e_L\) reads one only on \(B\), and test \(e_R\) reads one only on \(D\). Adaptively use \(e_0\), then \(e_L\) on the zero branch or \(e_R\) on the one branch. Every candidate is identified after cost two.

Every fixed two-test subset fails: \(e_0,e_L\) leaves \(C,D\) equal; \(e_0,e_R\) leaves \(A,B\) equal; \(e_L,e_R\) leaves \(A,C\) equal. All three fixed tests suffice, at cost three. No one-test policy succeeds, so the adaptive optimum is exactly two. This is a tiny exact fixture establishing semantics and a strict adaptive benefit. It does not predict an improvement over the existing thermal cost-20 single-test solution, whose optimum may already be unaffected by adaptation.

## Proposed interfaces and certificate format

Proposed `ResetExperimentFamily` stores costs, target labels, candidate-specific closed intervals, and experiment labels. Proposed `observation_cells`, `minimum_reset_policy`, `replay_policy`, and `verify_reset_policy` are future functions. A policy node records candidate IDs, chosen experiment, exact cell boundaries and endpoint closure, child nodes, and certified subtree worst-case cost. Leaves record a target label and all remaining original IDs. Reject cycles in a purported finite decision tree.

Use `schema: singularity.reset-policy/1`, explicit `uncertainty_semantics: independent-adversarial-per-reset`, candidate/model digests, root belief, policy nodes, exact cost, lower-bound or dynamic-programming table, search budget, and independent oracle comparison. A receipt must say whether it optimizes worst-case cost or expected cost. Expected cost requires a prior and observation law; interval bounds alone do not assign branch probabilities.

## Three concrete push units

**NX05-A - Exact observation-cell compiler.** Depends on NX01. Add proposed `src/singularity/reset_policies.py`, `tests/test_reset_policies.py`, and `docs/research/RESET_POLICIES.md`. Acceptance: every endpoint and open interval has correct membership; touching, nested, point, duplicate, disjoint, and empty intervals are handled. Compare cell memberships with a separately written direct inequality evaluator, including every endpoint explicitly.

**NX05-B - Bellman solver and independent tree oracle.** Depends on NX05-A. Implement target-aware proper-policy search with memoized candidate masks, positive costs, explicit policy budgets, and impossible outcomes. Acceptance: the four-candidate example has adaptive cost two and fixed-panel cost three; every tiny random rational instance matches independent finite-depth tree enumeration. The certificate checker verifies all possible observation branches and exact worst-case cost, not just a simulated successful branch.

**NX05-C - Reset thermal policy comparison.** Depends on NX05-B and NX03's retained pilot. Add proposed `scripts/adaptive_thermal.py` and `results/adaptive_thermal.json`. First compare on the unchanged six-candidate pool, then on a bounded subset of the 79 fault configurations. Acceptance: static and adaptive policies use identical costs, protocols, radii, and targets; each path is robustly decoded; full optimality is claimed only when search completes. Retain an unchanged optimum honestly and identify which ambiguity branches drive costs.

## Resource limits and failure cases

There are at most \(2^K\) candidate beliefs and \(O(K)\) scalar membership cells per test before duplicate child sets are merged. Bellman work can be exponential in \(K\), and 79 candidates are not automatically manageable. Begin with six to twelve candidates, at most twelve experiments, and a 100,000-belief ceiling. The depth oracle should stay at \(K\le5\). Track states, transitions, bit lengths, and wall time separately. A search cap is inconclusive, not proof that adaptation fails.

Avoid posterior probabilities without an observation distribution. Do not replace adversarial repeated noise by independent Gaussian averaging. Do not infer an adaptive optimum from greedy information gain. Empty runtime beliefs indicate an observation outside the contract and require a visible model-rejection result. Save every policy branch, endpoint partition, target map, costs, completed Bellman states, unresolved bounds, and independent checks. Resume with the same semantics; adding persistent nuisance requires a new belief representation and fresh proof rather than quietly reusing the candidate-set recurrence.

### Lower bounds and independent policy replay

For the retained tiny fixtures, the checker should recompute each leaf's possible original candidates from the complete path of interval constraints, independently of the solver's cached belief. Compute policy cost by summing actual tests along every root-to-leaf path and taking the maximum. Independently prove the worked example's one-test lower bound by listing each test's largest ambiguity cell. For larger cases, store the completed Bellman recurrence or admissible lower bounds rather than just the selected tree. A policy with cheap average branches can still have an expensive worst-case branch; the receipt must identify that branch and must not summarize its mean as the guaranteed cost.


# NX06 - Experiments with shared physical history

## Scope and why this is a different problem

This proposed track permits heating, observing, changing the input, and observing again on one evolving system. It removes the assumption that each panel member receives an independent reset. Actions may destroy information about the original fault or initial condition. A valid belief therefore retains original target identity, current physical possibilities, persistent nuisance, and the full observation constraints accumulated so far. The first implementation is a bounded exact finite-state or tiny rational fixture, followed by certified affine-set propagation.

The current `src/singularity/thermal_diagnostics.py::simulate_protocol` already evolves a complete chronological input word and returns one final reading. `protocol_pool` shares deterministic prefixes for speed, but its docstring explicitly says each selected protocol independently resets to a zero-centered initial box. Prefix caching is not permission to reuse a physical state across panel members. `AffineCandidate.step` and `.observe` are useful evolution primitives. `affine_operator_system` uses the correct homogeneous lift \(H_{c,u}=\begin{pmatrix}A_c&b_cu\\0&1\end{pmatrix}\) for small exact models, but its default dense budget of 256 rules out indiscriminate use on all six 144-state candidates.

`panels.py` adds independently purchased experiment costs and checks final-vector consistency; it does not price shared heating, intermediate readings, or reset actions. `robust_search.py` handles chronological words for one readout, not adaptive partially observed continuous trajectories. Read these files, `tests/test_thermal_diagnostics.py::test_generic_lift_order_nonzero_initial_and_sparse_duplicate_entries`, and NX05's narrower reset-policy specification before changing semantics.

## Belief-state definition and transition law

For a candidate \(c\), initial state \(x_0\), persistent nuisance \(\eta\), and current state \(x_t\), retain a feasible set

\[
\mathcal B_t=\{(c,x_0,\eta,x_t):\text{all prior actions and observations are satisfied}\}.
\]

The target \(T(c,x_0,\eta)\) refers to the original world. It must not be overwritten by the target of a later reset state. A control action propagates \(x_{t+1}=A_cx_t+b_cu_t+d_t\). An observation intersects the belief with \(y_t-C_{c,j}x_t\in E_{t,c,j}(\eta)\). A reset action replaces current state by a declared reset relation while retaining original identity and any nuisance sources not reset by physics.

The sequential update is the exact set-image followed by intersection. A finite-state implementation can enumerate these operations literally. For affine continuous models with polytopic uncertainty, maintain constraints over shared latent variables and the current state. A zonotope image is easy, but conditioning on observations may not remain an ordinary zonotope. A box or zonotope outer approximation is safe for claiming separation but may lose the very correlations that make a shared history informative. Never label that enclosure as an exact posterior set.

A policy terminates correctly when its feasible target set is a singleton. Its cost includes each actual control, reading, wait, and reset once. Two readings after one heat pulse should not be charged as two independent resets, nor may they be priced as free if sensor or elapsed costs were declared. Policies require a finite horizon or a proved proper termination condition; positive action costs alone do not prove a search over infinitely many histories terminates.

## Destruction, memory, and a worked example

The simplest destructive fixture starts with original bit \(x_0\in\{0,1\}\), target \(T=x_0\), and an erase action mapping both states to zero. After erasure, a current-state-only representation contains only zero and falsely declares the original target resolved if it relabels that state. The correct belief retains both original bits, permanently ambiguous under later identity/erase actions. Observing before erasure identifies the bit. This is a direct test of historical semantics, not a thermal claim.

For a shared physical trajectory, let

\[
x_{t+1}=a x_t+g u_t,\qquad
x_0=0,\quad a\in\{1/2,3/4\},\quad g\in[1,2].
\]

Apply one unit pulse and observe \(y_1=g\); then apply zero and observe \(y_2=ag\). The full transcript lies on one of two line segments with slopes \(1/2\) and \(3/4\), so it determines \(a\) exactly. The final scalar intervals are \([1/2,1]\) and \([3/4,3/2]\), which overlap. The first observation measures the persistent gain, making the second interpretable. Resetting and then applying only zero destroys that evolving-state information. Separate resets could reproduce the pair through two full experiments, but at different costs and with separately declared reset uncertainty. This distinction is precisely what the new solver must price.

For a direct robust check, the contrast \(h=y_2-y_1/2\) is zero for the first family and at least \(1/4\) for the second. Per-reading errors bounded by \(\delta\) perturb either contrast by at most \(3\delta/2\), so \(\delta<1/12\) is a sufficient guaranteed separation condition. With general sensor errors, derive separation on the joint feasible transcript sets. Independent gain intervals per time would incorrectly erase the shared-gain relation. Conversely, forcing the same gain under competing models without allowing each world its own \(g\) could overstate distinction. These two apparently opposite errors are avoided by maintaining per-world shared latent variables.

## Proposed APIs and serializable evidence

Proposed `HistoryModel` contains candidate-specific dynamics, legal controls, measurement channels, reset relations, latent uncertainty, target map, and exact action costs. Proposed `HistoryBelief`, `advance_belief`, `condition_belief`, `history_policy_search`, and `verify_history_policy` are future interfaces. Keep target identity separate from current-state keys. Use canonical action records such as `control`, `observe`, `wait`, and `reset`, with declared legality and effect.

A receipt uses `schema: singularity.history-policy/1`, initial feasible sets, source/candidate digests, persistent/reset-local nuisance labels, exact or outer-set semantics, action and observation traces, target labels at leaves, costs, horizon, and independently checked transition certificates. Every reset must list which variables are redrawn and which persist. A state compression needs a proof that all allowed future actions and target observations are preserved; matching the current measurement alone is insufficient.

## Three concrete push units

**NX06-A - Exact finite-history semantics.** Depends on NX05's policy/certificate conventions. Add proposed `src/singularity/history_experiments.py`, `tests/test_history_experiments.py`, and `docs/research/HISTORY_EXPERIMENTS.md`. Implement tiny finite worlds with partial legal actions, original targets, observations, and reset relations. Acceptance: the erase example remains ambiguous after erasure; observe-before-erase succeeds; infeasible actions are distinguished from indistinguishable outputs. Exhaustive history enumeration independently agrees with belief updates.

**NX06-B - Bounded exact affine conditioning.** Depends on NX06-A and NX02. Implement small rational polytopic trajectory constraints or an equally explicit bounded feasibility method. Acceptance: the two-slope example identifies \(a\) from shared history; final-only observation remains ambiguous; persistent gain and fresh sensor errors are represented correctly; noncommuting action order and reset-local uncertainty match direct substitution. Store exact overlap or separating certificates. Approximate enclosure-only results must carry that label.

**NX06-C - Shared-history thermal pilot.** Depends on NX06-B and NX03. Add proposed `scripts/history_thermal.py` and `results/history_thermal.json`. Begin on a four-by-four plate with two or three defects, short words, and intermediate measurements. Acceptance: every deterministic center trajectory matches the independent neighbour-flux oracle; all reset and sensor costs are accounted once; the policy is compared fairly with separately reset panels under the same model assumptions. Report savings only after setup, action, and uncertainty differences are explicit. Expand to the 144-state model only after a validated resource estimate.

## Complexity, limitations, and checkpoints

Even finite partially observed policy search can be exponential in the number of worlds and horizon. Continuous conditioning adds polyhedral feasibility growth and history-dependent nuisance dimensions. Begin with at most eight finite worlds or three affine candidates of dimension at most four, horizon six, and explicit search/cell/constraint budgets. The four-by-four thermal stage should initially use fixed short schedules and exact transcript verification before adaptive branching. Dense 870-dimensional lifts are unnecessary and prohibited by the existing default budget unless a separately accepted design justifies them.

A path with successful simulated observations does not certify all possible observations. Current-output equivalence is not all-future equivalence. Outer-set overlap is inconclusive; outer-set separation is safe when the enclosure proof is correct. Unknown faults and out-of-contract readings require a rejection/undetermined outcome. Save the complete action history, initial-target mapping, latent-variable constraints, reset semantics, solver frontier, cost bounds, and every certificate checker command. Resume from that exact belief contract. Do not replace it by candidate IDs alone merely to make the next search cheaper.

### Comparing histories fairly

A shared-trajectory protocol and two separately reset experiments may have different reset uncertainty even when their central readings match. Report those domains explicitly before attributing a cost difference to better planning. If the reset draws a fresh initial state, retain that variable only for the corresponding segment; if it redraws no calibration quantities, persistent gain remains the same latent variable after reset. Check both conventions in tiny fixtures. Keep an original-world identifier even after two current-state sets become equal, because the requested target may still differ. An all-future quotient that merges such worlds is valid only when its observation and target contract explicitly permits that merger.


# NX07 - Purchase the intervention language

**Status:** proposed integration and optimization; not implemented by this handoff. **Priority:** immediate after uncertainty/population contracts. **Required track dependencies:** NX01 and NX03. **Useful later integrations:** NX04 continuous severity, NX05 adaptive policies, NX08 conditioning, NX12 protocol grammars. NX07 can prototype on the existing six-model discrete pilot while waiting for dependencies, but acceptance on the expanded population requires them. Every claim is relative to a declared candidate family, target labels, finite capability catalogue, legal protocol language, cost horizon and uncertainty set.

## Problem and conceptual bridge

The thermal pilot already proves that certain symmetric sensors cannot distinguish two reflected faults under every permitted symmetric heater word. Repeating experiments within that language cannot fix the obstruction. The new decision is which capability to install: a local sensor, an asymmetric heater, or both. This joins PerfectJet's action-language equivalence to PerfectPower's resource-constrained population and Singularity's exact panel optimization. The goal is to buy useful new distinctions and retain their original physical labels, rather than optimize only among experiments somebody happened to list.

Let capability catalogue K contain sensors and actuators. Each experiment e has requirement set R_e contained in K, runtime cost c_e, and its already validated candidate observations. Choose installation bits z_k and experiment bits x_e. For a deployment of N independently reset diagnoses, minimize

\[
\min_{z,x}\ \sum_{k\in K}a_kz_k+N\sum_e c_ex_e,
\quad x_e\le z_k\ (k\in R_e),
\quad\sum_{e:\{u,v\}\in S_e}x_e\ge1\quad(T(u)\ne T(v)).
\]

Here a_k is a declared one-time installation cost; S_e is the set of robustly separated candidate pairs under the actual error contract; T is the requested target. Models sharing a target need not be distinguished. N is a positive integer accounting horizon, not an empirical forecast. A single fixed panel reused N times is the initial scope. Candidate-dependent policies, installation budgets over changing populations and shared multi-reading run costs require distinct extensions.

This is weighted set cover with installation activation. It remains finite and generally exponential. For a small catalogue, enumerate installed subsets J, keep experiments with R_e contained in J, and call the existing panel backend. Add installation cost and choose the minimum. No integer-programming dependency is necessary for a first complete result. Dominance is safe only when one installation option permits at least the same experiments at no larger installation cost, with all calibration/error effects accounted for. Merely adding a sensor should not silently change existing sensor noise.

## Source-verified crosswalk

| Existing source | Reusable contract | New obligation |
|---|---|---|
| `src/singularity/panels.py::reading_pool` | Validated rational experiment readings/costs; candidate identities retained. | Add requirements and installation costs outside this immutable pool. |
| `panels.py::minimum_cost_panel`, `exhaustive_minimum_panel` | Finite exact/box pair-cover optimum and a small exhaustive oracle. | NX01 heterogeneous uncertainties need compatible pair masks, not a falsely common radius. |
| `panels.py::coverage_masks`, `separates_all` | Existing exact/common-box coverage semantics. | Target-equivalent pairs must be omitted explicitly, with label provenance. |
| `thermal_diagnostics.py::AffineCandidate`, `build_plate_candidates`, `simulate_protocol`, `protocol_pool` | Sparse exact discrete dynamics, original six candidate IDs, separately reset protocols. | Define extra sensor/heater models and capability requirements without changing the original fixture. |
| `observability.py::OperatorSystem`, `observable_closure`, `verify_certificate` | All-future observation closure for a fixed finite-dimensional language. | Recompile when available generators or observations change. |
| DynaComp `src/dynacomp/thermal.py::plate_model` | Pinned nominal discrete source. | New asymmetric hardware is synthetic unless externally calibrated. |

The present `AffineCandidate` has one heater vector; it does not represent independently controllable multiple heaters. The first actuator catalogue may create one candidate family per selected heater location, with words selecting amplitudes for that installed heater. Simultaneous independently addressed heaters require an explicitly generalized input matrix adapter; do not overload scalar amplitudes as heater identities. Preserve zero-centered excess-temperature resets and the distinction between accounting units and money.

## Symmetry proof and tiny exact example

If a permutation P maps candidates a,b by A_b=P A_a P^{-1}, B_b=P B_a, x_{0,b}=P x_{0,a}, and all available sensors obey C_bP=C_a, every input word yields identical readings. The assertion follows by induction on the chronological state update. A sensor whose row violates invariance makes separation possible in principle, but is not itself proof that any permitted finite-cost experiment succeeds. Reachability, parameter values and noise can still prevent it. Return both the old-language blindness certificate and the new-language witness.

For a rational installation example, take target candidates with states v_1=(0,0), v_2=(1,0), v_3=(0,1). Sensor s_1 reads x_1 and s_2 reads x_2; each costs 2 to install and 1 per reading. A combined sensor s_3 reads x_1+2x_2, costs 5 to install and 1 per reading. Noise radius is 1/10 per reading. s_3 yields 0,1,2 and robustly separates all pairs. The pair {s_1,s_2} also does. At N=1 their total costs are both 6; at N=2 the combined sensor costs 7 and the pair costs 8. A correct solver preserves both N=1 optima and the N=2 change. A constant sensor with zero installation cost and positive runtime cost provides no distinction and should not alter the optimum.

## Proposed API and portable receipt

Create proposed `src/singularity/language_design.py`, tests `tests/test_language_design.py`, replay script `scripts/language_design.py` and `docs/research/LANGUAGE_DESIGN.md`. Suggested immutable classes are `Capability(identifier, install_cost, kind, source_contract)`, `RequiredExperiment(identifier, requires, readings, radii, run_cost, protocol)` and `LanguageDesignProblem(capabilities, experiments, candidate_ids, target_labels, deployments)`. Proposed functions `minimum_installation_panel(problem, *, max_catalogue_subsets, max_panel_nodes)`, `verify_installation_result(problem, result)` and `enumerate_installation_frontier(problem, deployments)` must reject invalid requirements, duplicate capability IDs, negative costs and malformed target labels.

A `singularity.language-design/1` receipt stores exact fractions as canonical numerator/denominator pairs, source hashes, target map, complete finite catalogue, original candidate IDs, all requirements, cost model, selected installation/panel, separated-pair witnesses, solver limits and an optimality certificate or exhaustive-search replay recipe. Integrity hashes bind bytes; they do not establish optimality. Unknown or exhausted search must never serialize as `optimal`.

## Three bounded acceptance pushes

**NX07-A - Catalogue semantics and exact activation objective.** Implement validation, objective evaluation and a tiny complete subset solver. Supply the three-candidate example, target-coarsening examples and a human proof of the activation formulation. Artifacts are code, focused tests and a receipt with both tied optima. Acceptance requires an independent plain-loop oracle enumerating capability subsets and panel subsets; it must not call the optimized activation solver.

**NX07-B - Symmetry-aware thermal capability catalogue.** Add at most eight sensor/heater options to a 4-by-4 synthetic plate, preserve the original six-model fixture and state all new hardware assumptions. Retain the all-word symmetry proof for the old language and an actual separating protocol after installation. Independently simulate flux for every selected witness, compare installation frontiers for N in {1,2,10,100}, and report ties. A null result or a noisy unseparable population is a legitimate output with its precise contract.

**NX07-C - Expanded-population optimization and release evidence.** Use the NX03 79-configuration bounded fault population or another explicitly accepted finite population. Produce a Pareto frontier of installation cost versus per-diagnosis cost, with original fault reconstruction. Independently verify all coverage and costs. Extend the monograph, retained receipt and complete release archive only after the track's actual acceptance conditions pass. Preserve comparison with the original finite pool and do not call catalogue optimality hardware-global optimality.

## Complexity, failure modes and resume record

For k capabilities, m experiments and p target-distinct pairs, a transparent method uses at most 2^k calls to an exponential panel solver. Start k<=8, m<=128, p small; estimate the search before increasing bounds. Cache only identical validated masks/cost subproblems. A single shared physical run measuring two sensors has a different cost and joint-noise semantics from two reset experiments; represent it as a separate experiment or defer it. Finite candidate identity can be preserved even when target equivalence intentionally groups candidates.

Stop after one to three accepted pushes under repository session rules. Record catalogue hash, population hash, uncertainty contract, deployment N, current incumbent, proven lower bound, unfinished subset queue and exact command. A budget refusal should return the best feasible design plus `optimality_unresolved`, not a cheap-looking unsupported conclusion. The next session must reproduce the tiny oracle before resuming a saved large search.


# NX08 - Stable target recovery

**Status:** proposed exact target-conditioning integration, not a new general observability theorem. **Priority:** high mathematical foundation for experimental design. **Required track dependencies:** none beyond the shipped baseline. **Useful downstream tracks:** NX07 language purchase, NX09 fidelity selection, NX25 forecasting and NX26 nonlinear fibres. The first version is finite-dimensional, linear, rational and Euclidean. Nonlinear/global, statistical and physical claims require separate hypotheses.

## Question and inherited work

PerfectJet and the older WIND/SOE work use the condition ker(H) contained in ker(G): observations Hx determine a requested target Gx. Singularity proves complete observation spaces for declared future languages, and DynaComp already provides exact linear quotients and rational quadratic metrics. NX08 asks a different decision question: when recovery is possible, how strongly does measurement error propagate into the target? Identical ranks can hide wildly different practical usefulness. The expansion is target-specific conditioning and sensor selection, not reimplementation of DynaComp's stability or quotient compilers.

Let x=x_c+Qz range over an affine admissible subspace, with Q a rational full-column-rank basis and z unrestricted in the initial theorem. Subtract known centres from observations and targets. Set H_0=HQ and G_0=GQ. The exact target condition is

\[
\ker H_0\subseteq\ker G_0\iff G_0=LH_0\text{ for some }L.
\]

For Euclidean errors, the sharp amplification constant is

\[
\kappa_* =\sup_{H_0z\ne0}\frac{\|G_0z\|_2}{\|H_0z\|_2},
\quad G_0^TG_0\preceq\kappa^2H_0^TH_0.
\]

When the kernel condition fails, amplification is infinite: an invisible direction changes the target. When it holds, choose the minimum-norm extension L=G_0 H_0^+; its norm equals the target amplification on the observation image, with zero action on its orthogonal complement. The rational implementation need not expose floating pseudoinverses: exact row-space coordinates yield a valid recovery map, and a separate positive-semidefinite inequality certifies an upper bound. An arbitrary recovery map may amplify off-image noise unnecessarily, so report its actual norm or certify the chosen decoder. No zero-noise identifiability claim alone certifies noisy recovery.

## Exact certificates and non-Euclidean variants

For rational alpha>=0, test S(alpha)=alpha H_0^TH_0-G_0^TG_0 positive semidefinite. A rational congruence/LDL certificate with nonnegative diagonal pivots can certify PSD; a strict positive-definiteness routine cannot simply be reused because invisible nuisance directions force zero eigenvalues. Handle zero pivots correctly: for a PSD matrix a zero diagonal entry forces the corresponding row/column to vanish after the relevant congruence step. Rational bisection gives lower/upper brackets on kappa_*^2. An exact vector z with z^T S(alpha)z<0 proves that alpha is too small.

If noise is bounded in a positive-definite metric R, whiten conceptually with R^{-1}; equivalently certify G_0^TG_0<=alpha H_0^T R^{-1}H_0 and retain rational R. Here R is the positive-definite ellipsoid shape matrix: measurement noise eta satisfies eta^T R^{-1} eta <= epsilon^2. This assumes that declared ellipsoid and an appropriate decoder. For box noise, the relevant recovery error is a support-function calculation, not automatically the Euclidean kappa. An invertible coordinate change x'=Tx changes H to HT^{-1}, G to GT^{-1}, and the admissible-domain metric accordingly. Holding the old Euclidean state norm after an arbitrary change of units changes the problem. Physical target and observation units belong in the receipt.

Bounded feasible sets offer a complementary nonlinear optimization of target diameter, but NX08-A does not claim that every global fibre must be an affine subspace. A bounded domain can eliminate an otherwise unbounded direction without producing the unrestricted linear norm theorem. Forecast targets G_tau=GF^tau fit the same formulation for a fixed known linear transition F; uncertainty in F must be propagated separately.

## Verified source crosswalk

| Existing source | Actual reusable API | Scope boundary |
|---|---|---|
| `src/singularity/observability.py` | `OperatorSystem`, `observable_closure`, `verify_certificate`, `quotient_state`, `future_equivalent` | Exact all-future distinguishability and linear quotient; no target-conditioning API yet. |
| `src/singularity/experiment_design.py` | `RationalMetric`, `monomial_gram`, `minimum_separation`, `nearest_candidate` | Existing finite candidate geometry and integral polynomial metrics; not the continuous target inequality above. |
| `src/singularity/thermal_diagnostics.py` | `AffineCandidate`, `simulate_protocol` | Supplies rational candidate models and outputs; the finite-candidate problem differs from continuous-state target recovery. |
| DynaComp `src/dynacomp/rational.py` | `rref`, `nullspace`, `coordinates`, `inverse`, matrix operations | Existing exact rational linear algebra; optional integration must preserve stdlib Singularity core. |
| DynaComp `stability.py` | `positive_definite`, `contraction_holds`, `quadratic_certificate` | Stability metrics already exist. PSD target dominance with singular H is a separate, carefully checked adapter. |
| DynaComp `linear.py` | `LinearModel`, `compile_linear`, `closure_witness` | Exact observable reduction already exists and must not be described as newly invented. |

Do not import DynaComp private numerical helpers into Singularity core. A small local exact PSD certificate verifier is reasonable if required by the accepted target problem, with a clear derivation and independent oracle. Alternatively retain DynaComp as an optional source-pinned adapter and use existing rational structures.

## Tiny rational examples

Take target G=(0,1). The sensor layout H_a=diag(1,1/100) has full rank and kappa_*=100; H_b=I also has full rank but kappa_*=1. With Euclidean observation error at most 1/1000, their target-error guarantees are respectively 1/10 and 1/1000. Rank alone cannot rank these designs. Rational witnesses z=(0,1) attain both constants, and S(10000) and S(1) are PSD with the required zero pivot.

Now let H=(1,0), G=(0,1). z=(0,1) is a hidden-target witness, so no finite amplification constant exists. Add the admissible constraint x_2=2x_1, Q=(1,2)^T; then H_0=(1), G_0=(2), and kappa_*=2. This shows why admissible constraints must enter before rank or metric analysis. Finally use zero target G=0: kappa_*=0 even if H is empty. Empty observations with nonzero admissible target must be unobservable, not a division-by-zero success.

## Proposed interface and evidence

Proposed `src/singularity/target_recovery.py` exposes `TargetRecoveryProblem(observations, target, admissible_basis, observation_metric=None, units=None)`, `target_identifiability(problem)`, `certify_target_amplification(problem, alpha_squared)`, `bracket_target_amplification(problem, tolerance, max_steps)` and `recover_target(problem, observed, certificate)`. Results distinguish `unobservable`, `certified_upper_bound`, `bracketed_sharp_constant` and `resource_limit`. A `singularity.target-recovery/1` receipt stores rational matrices, rank/nullspace witnesses, admissible centres/basis, target/measurement units, PSD congruence certificate, lower witnesses and decoder identities. Verify both G_0=LH_0 and the claimed decoder norm bound when claiming an operational error guarantee.

**NX08-A - Kernel and exact bound semantics.** Implement source-preserving validation, target row-space witnesses and exact PSD certificates. Retain all tiny examples, zero-dimensional edge cases and singular feasible cases. Independent checks should enumerate small rational directions for lower witnesses and use a separate fraction-free elimination or principal-minor oracle for tiny PSD matrices. Tamper with Q, L and PSD factors to ensure rejection.

**NX08-B - Sensor-layout optimization.** Search a bounded catalogue of sensor rows for minimum installation cost meeting kappa<=kappa_max. Keep rank-feasibility and conditioning objectives separate. Exhaustively enumerate tiny catalogues, then compare with a pruned implementation. Artifacts include a conditioning-versus-cost frontier and examples where equal-rank cheap sensors are unusable at the demanded tolerance.

**NX08-C - Forecast and model integration.** Apply to one small thermal state target and one synthetic linear forecast target G_tau. Include admissible nuisance subspaces and units. Compare predicted worst errors with attained adversarial noise/state witnesses; document when bounds are conservative. Link the result to NX09 without claiming calibrated physical performance or nonlinear global identifiability.

## Resource limits, completion and continuation

For n admissible coordinates and m sensors, dense rational elimination is polynomial in operation count, approximately cubic in n for the PSD test, but bit growth can dominate. Initial defaults n<=16, at most 12 sensor options and at most 2^12 catalogue subsets are sufficient. The sharp value is often algebraic, so rational brackets are an intended final result. Do not promise an exact rational optimum when none exists. Stop on unresolved PSD boundaries with explicit interval status.

Record selected sensor IDs, target map, Q hash, units, alpha bracket, attained lower witnesses, exact upper certificate and remaining catalogue queue. Resume by replaying certificates before continuing bisection or optimization. A formal proof extension may later verify the norm implication, but until compiled and audited these are exact computation plus human proof, not new Lean coverage.


# NX09 - Joint experiment, rank, and precision selection

**Status:** proposed decision-layer integration of existing reduction and arithmetic guarantees. **Priority:** high after uncertainty semantics. **Required track dependencies:** NX01 and NX08. **Useful integrations:** NX07 capability purchase, NX10 stopping, NX35 refinement. Nothing in this packet authorizes relabeling an uncertified numerical backend as certified or transferring one candidate's certificate to another model.

## Problem and conceptual interpretation

DynaComp already computes reduced models, uniform output-error bounds, exact stability decisions and execution-error contracts. Singularity already chooses finite experiments and panels. The new problem is which model fidelity to use for each candidate-experiment evaluation while still making a certified experimental decision. A striking physical discrepancy may need only a low-rank inexpensive model. A close discrepancy may justify a larger rank, a supported machine protocol, exact arithmetic, or a different experiment. The decision engine should spend computational effort where it can change the optimum.

For experiment e, candidate c and evaluator configuration f, let the certified simulated reading be hat(r)_{e,c,f}. Separate the physical uncertainty radius rho_phys from the computational radius rho_comp. The composed scalar set is

\[
I_{e,c,f}=\widehat r_{e,c,f}+[-(\rho_{\mathrm{phys},e,c}+\rho_{\mathrm{comp},e,c,f}),\rho_{\mathrm{phys},e,c}+\rho_{\mathrm{comp},e,c,f}].
\]

If every error source is expressed in the same output units and time convention, triangle inequality gives

\[
\rho_{\mathrm{comp}}\le\rho_{\mathrm{source}}+\rho_{\mathrm{transformation}}+\rho_{\mathrm{reduction}}+\rho_{\mathrm{execution}}.
\]

The sum need not be sharp; correlation can support a tighter joint composition only if represented and proved. Sensor error is a physical observation uncertainty, not simulation roundoff. Initial-state and process disturbances must not be counted twice through both source domains and an added unexplained radius. Every bound must bind the source matrices, input/reset domain, sensors, horizon, evaluator and arithmetic protocol.

A panel decision chooses x_e and evaluator options f_{e,c}. Minimize physical experiment cost plus deployment-weighted compute and setup costs, subject to robust target separation. Setup costs shared across evaluations require activation variables: compiling a rank-r model once is not charged again for every reading. A minimal first problem fixes a finite menu and deterministic accounting units; measured runtime is reported as a benchmark distribution, not inserted as an exact rational physical law.

## Scope of available precision

The current DynaComp machine layer certifies specified binary64 protocols. `certify_execution` covers a particular exact-dot-then-round execution, and the separate native layer covers a checked sequential executor. An arbitrary BLAS, NumPy, GPU or user-selected p-bit computation is not certified by either. Therefore the first supported menu is exact rational evaluation plus the actual certified binary64 routes, with optional internal certificate precision parameters where their API explicitly supports them. Generic half/single/quad precision selection is future research requiring its own arithmetic model. Do not infer that changing a certificate's interval precision changes executable arithmetic.

The original thermal pilot's full exact simulation has zero reduction error. Its initial state is zero excess temperature with a declared radius, not the older DynaComp workbench's [18,22] domain. The existing nine-state corner-mean certificate cannot be reused for new left/right sensors or blocked-bond candidates. Each candidate/sensor/domain change needs reconstruction or a separately proved uniform family certificate.

## Source-verified API crosswalk

| Existing source | Verified reusable function/class | Integration boundary |
|---|---|---|
| `src/singularity/thermal_diagnostics.py` | `protocol_pool(..., reduction_error=0, ...)`, `simulate_protocol`, `AffineCandidate` | Current reduction_error is a caller-supplied uniform number; NX09 must replace assertions with bound-source evidence. |
| `src/singularity/panels.py` | `reading_pool`, `minimum_cost_panel`, `exhaustive_minimum_panel` | Reuse finite pair-cover search after evaluator-specific certified readings are constructed. |
| DynaComp `uniform.py` | `sharp_box_bound`, `uniform_enrichment`, `replay_uniform` | Exact finite-horizon model reduction error already exists. |
| DynaComp `validated.py` | `validated_box`, `replay_validated` | Enclosed execution of sharp-box certificates; keep source/domain binding. |
| DynaComp `machine.py` | `certify_execution`, `compose_execution`, `replay_execution`, `replay_machine_composition`, `Binary64Runtime` | Specified exact-dot binary64 protocol and composed source error. |
| DynaComp `native.py` | `certify_sequential`, `compose_sequential`, `replay_sequential_composition`, `PreparedSequential` | Separate sequential native execution contract. |
| DynaComp `engineering.py` | `output_contract`, `replay_import`, `EngineeringRunner` | Transformation/feedthrough units and endpoint semantics already implemented. |

Optional adapters must pin the DynaComp source revision and preserve Singularity's stdlib core. Vendor only small audited fixtures or portable receipts where practical; do not copy an entire numerical dependency stack into core. Existing replay functions establish their stated arithmetic identities, not physical calibration of the imported source.

## Tiny rational decision example

Take two candidates with certified simulated centres 0 and 1/2. Physical uncertainty is 1/20 per candidate. A cheap evaluator costs 1 and has computational radius 1/4 per candidate. Its total radii sum to 3/5, exceeding the centre difference; this evaluator cannot certify separation. A more accurate evaluator costs 3 with computational radius 1/20 per candidate, so the total radii sum to 1/5 and separation is certified. A third physical experiment costing 1 additional unit gives centres 0 and 1; even the cheap evaluator now certifies separation because 1>3/5. An integrated decision may prefer changing the physical test over buying computational accuracy.

Store the centres as observations of the approximate evaluator and the error bounds as proven envelopes. If instead centres are known exact values, claiming they “move” when rank changes is inconsistent. Also test a two-sided interval for the centre difference crossing the strict threshold: equality gives overlapping closed sets, so a strict separation certificate must refuse it.

## Proposed API and receipt schema

Proposed files are `src/singularity/fidelity_design.py`, `tests/test_fidelity_design.py`, `scripts/fidelity_design.py` and `docs/research/FIDELITY_DESIGN.md`. Suggested immutable structures: `EvaluatorOption(identifier, candidate_id, sensor_ids, domain_id, arithmetic_protocol, rank, setup_key, setup_cost, run_cost, bound_receipt)`, `BoundedReading(center, physical_radius, computational_radius, source_ids)` and `FidelityPanelResult` retaining selected experiment/evaluator combinations. Proposed functions `bind_evaluator(option, source)`, `compose_reading_contract(...)`, `minimum_fidelity_panel(...)` and `replay_fidelity_result(...)` must reject orphaned source IDs, mismatched units, stale horizons and unrecognized arithmetic protocols.

A `singularity.fidelity-design/1` receipt stores full provenance of source, transformation, reduction and execution subreceipts, candidate identities, uncertainty decomposition, setup sharing rules, exact accounting costs, selected panel and lower-bound evidence. Numerical timing trials belong in a separate benchmark section with machine/software metadata. If selected options share a setup, the receipt must show that its cache key binds every property relevant to the claimed guarantee.

## Three bounded acceptance pushes

**NX09-A - Typed error and cost composition.** Implement finite exact menu validation and reading-interval construction. Retain the tiny decision example, shared-setup and incompatible-domain cases. Independently enumerate all evaluator assignments and panels on tiny instances. Acceptance requires strict-threshold tests, stale-certificate rejection and a proof explaining every error term and its units.

**NX09-B - Source-pinned DynaComp evaluator adapter.** Integrate two actual ranks for one small thermal family and exact/binary64 options supported by replayable upstream contracts. Compare independently simulated full rational outputs against every enclosure over exhaustive tiny input boxes/vertices where feasible. Preserve rejected options; a bound exceeding tolerance is `not_certified`, not a false candidate or physical refutation.

**NX09-C - Setup-inclusive optimal diagnostic plan.** Optimize the current thermal finite pool or a bounded NX03 population using the accepted menu. Report selected experiment, rank, arithmetic protocol, guaranteed separation, setup cost, repeated-query break-even and independent full-model verification. Compare with “full exact everywhere” and “same rank everywhere.” A no-speedup result is valid if accounting is honest; do not claim an improvement from warm-only timings while hiding setup.

## Complexity and continuation

If e experiments, k candidates and f evaluator options per evaluation are unrestricted, naive assignment search can scale as f^(ek), before panel combinatorics. Initial scope should share one evaluator choice per candidate/sensor/domain or use dominated-option pruning justified by contained error sets and no larger setup/run cost. Start k<=6, e<=16 and f<=3, then use interval-certified branch bounds. The output certificate should remain small even if proposal search is expensive.

On stopping, save source hashes, validated evaluator menu, measured versus exact cost distinction, incumbent plan, lower bound, unresolved evaluator assignments and the exact replay command. Do not mark optimal when budget exhaustion leaves cheaper possibilities unresolved. Complete the accepted batch with manuscript, status and archive updates at integration time; this handoff itself contains no new implemented fidelity engine.


# NX10 - All-horizon stopping certificates

**Status:** proposed decision-level use of existing stability and all-time bounds. **Priority:** high for useful experiments and honest stopping. **Required track dependencies:** none beyond baseline; NX01 refines uncertainty, NX09 supplies certified approximate readings, NX11 accelerates distant evaluation. Initial acceptance covers constant-input step protocols or a declared fixed repeated block, not arbitrary adaptive or switched inputs.

## Decision problem

The current thermal pool lists finitely many horizons. It can establish an optimum within that pool, but cannot establish that a later step experiment would be better, useless, or necessary. DynaComp already proves all-time reduction-error guarantees, so NX10 should not recreate that machinery. The new work is to turn stable pair-response tails into experiment-selection stopping certificates. It must explain whether waiting longer can cross a robust separation threshold or improve a bounded objective enough to matter.

For fixed candidate c under constant input u, x_{t+1}=A_cx_t+B_cu. If A_c is Schur stable, x_c^*=(I-A_c)^{-1}B_cu and

\[
r_c(t)=C_cx_c^*+C_cA_c^t(x_{0,c}-x_c^*).
\]

For two candidates a,b, set delta(t)=r_a(t)-r_b(t), delta_infinity=C_ax_a^*-C_bx_b^*. If A_c^TP_cA_c<=gamma_c^2P_c with 0<=gamma_c<1, then

\[
|\delta(t)-\delta_\infty|\le K_a\gamma_a^t+K_b\gamma_b^t=:U(t),
\quad K_c=\|C_c\|_{P_c,*}\|x_{0,c}-x_c^*\|_{P_c}.
\]

Rational upper enclosures for square roots make U computable with exact acceptance. For t>=T, monotonicity gives U(t)<=U(T). Thus |delta(t)| lies between max(0,|delta_infinity|-U(T)) and |delta_infinity|+U(T) for every later t. These are sufficient certified bounds, not necessarily the sharp future maximum.

With candidate-specific error radii \(\rho_a(t),\rho_b(t)\), robust separation requires \(\lvert\delta(t)\rvert>\rho_a(t)+\rho_b(t)\). Suppose, for every \(t\ge T\),

\[
R_{\min}(T)\le\rho_a(t)+\rho_b(t)\le R_{\max}(T).
\]

Then \(\lvert\delta_\infty\rvert-U(T)>R_{\max}(T)\) proves eventual uniform separation, while \(\lvert\delta_\infty\rvert+U(T)\le R_{\min}(T)\) proves no later separation. Without a positive lower bound on future noise, the second conclusion may be unavailable. Constant sensor noise supplies one; reduction/process errors cannot be assumed to be positive attained lower bounds merely because an upper bound exists.

## Cost and optimality implications

A no-separation tail plus exhaustive evaluation through T proves that no constant-input experiment in this sensor/input family distinguishes the pair at any horizon. A separation tail provides a useful horizon guarantee, but not the cheapest separating time unless all earlier times are checked or excluded. With strictly increasing elapsed cost, an incumbent feasible experiment of cost C already bounds potentially cheaper horizons. This simple accounting cutoff can be stronger than a spectral tail for minimum-cost selection.

For maximum-margin search without a budget, a stable response may have a finite unattained supremum. Existing path results demonstrate this phenomenon. Return a certified supremum bracket or an epsilon-optimal finite experiment; never invent an attained global optimum. If a tail upper bound falls below an incumbent finite margin, the finite prefix maximum is certified globally optimal for that declared protocol family. Equality needs exact treatment because a tie can occur or a limit can be approached from below.

For a fixed repeated input block, compile its affine block map (A_block,b_block), subtract its fixed point and analyze block indices. Different within-block observation phases need separate outputs and initial offsets. Arbitrary switching requires a common invariant/contracting certificate or another dedicated theorem; individually stable modes do not suffice. The affine homogeneous lift has an eigenvalue 1, so do not send that lift to a Schur-stability test and call the original stable dynamics unstable. Subtract a steady state before applying contraction arguments.

## Verified source crosswalk

| Existing source | Reusable mechanism | New integration obligation |
|---|---|---|
| DynaComp `src/dynacomp/stability.py` | `schur_stable`, `quadratic_certificate`, `contraction_holds`, `replay_quadratic`, `sqrt_up` | Reuse stability proposals and exact metric acceptance; verify whether stored gamma is a squared contraction factor. |
| DynaComp `src/dynacomp/forever.py` | `all_time_bound`, `replay_all_time`, `moment_rows`, `all_time_enrichment` | Existing all-time reduction error is not automatically a candidate-pair separation bound. Construct the correct pair problem. |
| DynaComp `src/dynacomp/fastforward.py` | `repeat_affine`, `repeat_input_block` | Reuse fixed-block composition with explicit chronological and observation-phase semantics. |
| `src/singularity/thermal_diagnostics.py` | `AffineCandidate`, `simulate_protocol`, `protocol_pool` | Exact finite-prefix readings and declared initial/process/sensor uncertainty. |
| `src/singularity/robust_search.py` | `bounded_margin_search`, `bounded_family_search` | Existing bounded-word objective; do not silently extend its certificate to unbounded times. |
| `tests/test_path_margin.py` | Retained all-budget unattained-supremum example | Regression guard against claiming every unbounded optimum is attained. |

The DynaComp metric convention in its packet may use A^TPA<=gamma P and rho=sqrt(gamma), while the displayed theorem here uses gamma_c as the norm contraction. Record the distinction explicitly. Source code is authoritative; an off-by-a-square error can invalidate every tail.

## Tiny exact examples

With x_0=0, unit constant input, C=1, A_a=1/2 and A_b=1/3, B_a=B_b=1, the responses are r_a(t)=2(1-2^{-t}) and r_b(t)=(3/2)(1-3^{-t}). Therefore delta_infinity=1/2 and U(T)=2*2^{-T}+(3/2)*3^{-T}. At T=4, U=31/216, giving |delta(t)|>=77/216 for all t>=4. Noise radius 1/20 under each candidate has sum 1/10, so every t>=4 separates robustly.

For a late-time impossibility example choose B_a=1/2 and B_b=2/3 instead. Both steady responses equal 1, and |delta(t)|=|3^{-t}-2^{-t}|<=3^{-t}+2^{-t}. At T=6, U=793/46656<1/50. With sensor radius 1/100 per candidate, no t>=6 can separate, even though a small horizon can. This is a precise reason that “wait longer” is not a universal repair.

## Proposed interface and three pushes

Create proposed `src/singularity/horizon_design.py`, `tests/test_horizon_design.py`, `scripts/horizon_design.py` and `docs/research/HORIZON_DESIGN.md`. Proposed APIs: `StepFamily(candidate_ids, input, sensors, reset_contract)`, `certify_response_tail(...)`, `future_separation_status(pair, tail, error_contract)`, `minimum_step_horizon(...)` and `replay_horizon_result(...)`. Results distinguish `eventually_separating`, `never_separating_after`, `finite_optimum_certified`, `supremum_bracket`, `inconclusive_tail` and `resource_limit`. Store source and fixed-point identities, exact metric certificate, contraction semantics, prefix, tail constants, cost and strict threshold conventions in `singularity.horizon-design/1`.

**NX10-A - Pair-tail theorem and replay.** Implement constant-input exact pair tails and the two scalar examples. Independently evaluate closed-form responses and rational matrix powers. Reject altered steady states, invalid metrics, gamma>=1 and inconsistent units. Test marginally stable and nonnormal matrices without confusing certificate failure with instability.

**NX10-B - All-horizon decision integration.** Combine a checked prefix with upper/lower future bounds and monotone costs. Verify one finite global optimum, one late-time impossibility and one epsilon-optimal unattained-limit case. The independent oracle should use exact analytic scalar sequences or separately derived inequalities, not the production tail routine.

**NX10-C - Thermal and repeated-block demonstration.** Apply to at most four small-plate candidate pairs and two fixed blocks. Replay exact finite-prefix readings by neighbour flux, compare new decisions with the existing finite pool and retain inconclusive cases. Report certified computational effort and explicitly avoid calibrated physical-time or arbitrary-input claims.

## Complexity and stop/resume

Dense exact metrics are cubic or worse in dimension and can dominate the tiny tail arithmetic; cache certificates by source matrix, not merely model label. Start dimensions <=16 and prefix <=128, then use sparse/exact observable reductions where valid. Stop at a declared maximum prefix, precision and metric-search budget. A loose bound is an inconclusive result, not evidence that no better experiment exists. Save source hashes, protocol family, current prefix, contraction certificate, tail interval, incumbent and unresolved pairs; replay before extending the horizon. Preserve accepted upstream all-time capabilities as existing results and describe this track's new contribution as certified experimental stopping.

## Error-domain extensions that must remain explicit

A persistent bounded process input does not generally decay to zero uncertainty. For the scalar recurrence x'=a x+v with |a|<1 and |v_t|<=d, its contribution is at most d(1-|a|^t)/(1-|a|), approaching a nonzero floor. A tail proof that treats this contribution as initial-condition error would make late observations appear artificially precise. Candidate-specific loss rates can make even initial-error envelopes decay at different speeds; retain their actual time dependence rather than substituting an unjustified common lower radius.

Correlated uncertainty across repeated readings also changes the question. This track's scalar-horizon comparison may use a marginal bound for each independent-reset experiment. A shared-trajectory panel can sometimes cancel persistent bias, but its joint uncertainty set belongs to NX02/NX06 and must be preserved when deriving all-horizon stopping. A scalar no-separation conclusion does not prove that a vector of readings at several times is uninformative. Conversely, all-future exact observability does not promise a finite noisy separation margin. Keep these four objects distinct in the receipt: one scalar late reading, a fixed multi-time panel, all legal words, and an adaptive policy.


# NX11 - Remote-time evaluation

**Status:** proposed experiment-query integration of already implemented exact rational generating functions and realizations. **Priority:** supporting infrastructure, not a new claim that arbitrary graph series are rational. **Required track dependencies:** none. **Useful downstream integrations:** NX10 tails, NX12 large protocol sets, NX17 low-rank defect transport and NX31 period observables. Initial acceptance concerns finite-dimensional fixed linear models and fixed constant or periodically repeated input words.

## Mathematical contract and conceptual use

For a fixed exact state matrix A, initial state x and scalar output C, the sequence s_n=CA^n x satisfies a finite linear recurrence and has ordinary generating function

\[
S(z)=C(I-zA)^{-1}x=P(z)/Q(z),\quad Q(0)=1.
\]

DynaComp already constructs this fraction, cancels invisible factors, supplies a minimal autonomous realization and a Hankel witness, and evaluates nth coefficients by binary matrix powering. NX11 makes that machinery usable by the experiment optimizer, with correct physical indexing, source binding, resource estimates and candidate-pair cancellation. It is not permission to infer rationality for Singularity's positive-q graph-height generating functions: their index is total integer height, not a step in a fixed finite linear transition system.

For x_{t+1}=Ax_t+Bu_t, y_t=Cx_t and x_0=0, a unit impulse u_0=1 yields y_0=0 and y_{n+1}=CA^nB. The transfer expression z C(I-zA)^{-1}B includes that delay. With direct feedthrough D u_t, y_t=Cx_t+D u_t and a held-input endpoint convention must be declared. A sequence realization s_n=CA^nx is not automatically a zero-state input-output realization. This distinction is already explicit upstream and must survive the adapter.

For constant input u, an affine homogeneous matrix H_u=[[A,Bu],[0,1]] yields y_t=(C,0)H_u^t(x_0,1). This gives a rational sequence even though H_u need not be stable. When A is stable, subtracting the fixed point often lowers the transient representation and supports NX10 tails. For a repeated block, compile its affine map once, then power that block; within-block observation phase is part of the query.

## Pair cancellation and finite equality certificates

For candidates a,b, build their scalar difference sequence. A block-diagonal representation diag(A_a,A_b), initial (x_a,x_b) and row (C_a,-C_b) is a correct upper-bound realization. Algebraic cancellation can lower the actual minimal order drastically. If reduced difference fraction P_delta/Q_delta has P_delta=0, the observations agree for every index in this sequence family. This is stronger than a long finite agreement but remains restricted to the fixed input/initial/output semantics.

If P_delta is a polynomial of known degree d, agreement of coefficients through d proves P_delta=0 after multiplication by the known nonzero constant denominator. More generally a verified recurrence plus a sufficient initial prefix determines all future coefficients. Retain both fraction identities and the actual initial prefix; a fitted recurrence from sampled outputs is not a completeness certificate. The existing minimal Hankel determinant certifies the prescribed scalar sequence's order, not every-state observability or every-input equivalence.

## Source-verified API crosswalk

| Source | Reusable existing API | Adapter obligation |
|---|---|---|
| DynaComp `src/dynacomp/generating.py` | `RationalGF`, `from_state(A, initial, C)`, `from_recurrence(coefficients, initial)`, `periodic_gf` | Preserve constant-first polynomial coefficients and recurrence ordering. |
| Same module `RationalGF` | `coefficients`, `nth`, `realize`, `subsequence`, `packet`, `tail` | Reuse exact GF arithmetic; its tail concerns series evaluation, not automatically a physical-time response tail. |
| Same module | `replay_generating` | Independently replay normalized source fraction and realization identities through the existing checker. |
| DynaComp `realization.py` | `minimal_realization`, `markov_parameter`, `hankel_submatrix`, `replay_realization` | Existing zero-state MIMO minimal realization and source-derived Hankel rank certificate. |
| DynaComp `fastforward.py` | `compose`, `repeat_affine`, `repeat_input_block` | Actual fixed-block acceleration already implemented. |
| `src/singularity/thermal_diagnostics.py` | `simulate_protocol`, `AffineCandidate` | Independent sparse finite-horizon comparison and original candidate labels. |
| `src/singularity/observability.py` | `apply_word`, `experiment` | Chronological convention: the first word symbol acts first. |

The GF source limits a realization to 128 states and exact values to a 16384-bit budget; coefficient count is bounded at 10000. The 144-state plate therefore cannot simply be passed to `from_state` unchanged. Obtain a valid exact reduced response first, use a small plate, or refuse under the budget. A mostly zero 870-dimensional multi-candidate homogeneous lift is especially inappropriate. Preserve the core's optional integration boundary and pin any upstream source used for receipts.

## Tiny rational example and resource meaning

Take A=diag(1/2,1/3), x=(1,1) and C=(1,-1). Then s_n=2^{-n}-3^{-n}, so

\[
S(z)=\frac{z/6}{1-5z/6+z^2/6},\quad s_0=0,\ s_1=1/6,\ s_2=5/36,
\quad s_{n+2}=\tfrac56s_{n+1}-\tfrac16s_n.
\]

The leading 2-by-2 Hankel determinant is det([[0,1/6],[1/6,5/36]])=-1/36, proving minimal scalar order 2. Verify nth independently from (3^n-2^n)/6^n. The number of matrix-powering stages is logarithmic in n, but the exact denominator has order n bits. Evaluating n=10^100 as an explicit rational answer is infeasible and should be refused. Modular evaluation at a prime not dividing 6 can support huge indices with bounded-size residues, but requires a separately declared modular query, not a silent replacement for the rational output.

A cancellation example is A=diag(1/2,1/3,1/5), x=(1,1,1), C=(1,-1,0): the invisible third eigenmode must disappear. A transient guard is z/(1-z), whose sequence is 0,1,1,... and whose autonomous minimal dimension is 2; the constant sequence 1,1,... has dimension 1. Pure finite polynomials require enough states to retain the transient. Zero sequences must normalize to 0/1 and avoid the nonzero-realization path.

## Proposed query contract

Create proposed `src/singularity/remote_queries.py`, `tests/test_remote_queries.py`, `scripts/remote_queries.py` and `docs/research/REMOTE_QUERIES.md`. Suggested structures: `SequenceQuery(candidate_id, source_id, initial_id, protocol_family, sensor_id, sample_convention)`, `CompiledResponse(sequence_packet, source_binding, index_map)` and `RemoteValue(index, value, arithmetic_mode, cost_metadata)`. Proposed functions `compile_response(query, adapter)`, `compile_pair_difference(first, second)`, `query_index(compiled, n, max_bits=...)`, `query_progression(compiled, stride, offset)` and `verify_remote_value(...)` should preserve all source and index semantics.

Receipt `singularity.remote-response/1` contains the fixed source matrices or upstream bound packet, input/initial/output convention, exact rational GF, recurrence, source-derived initial prefix, Hankel witness, query index, value and resource limits. A modular extension must state modulus and require denominator invertibility. It certifies a residue, not a real-valued observation, and cannot establish a physical noise margin without additional bounds.

## Three acceptance pushes

**NX11-A - Source-bound scalar query adapter.** Reuse the upstream GF engine through a documented optional adapter. Retain the two-mode sequence, zero, invisible-mode cancellation, polynomial transient and direct-feedthrough indexing tests. Independently evaluate small indices by sparse stepping and closed form. Verify malformed indices, dimensions and source-binding tampering are rejected.

**NX11-B - Pair-response and repeated-block compilation.** Build actual candidate differences and periodic blocks. Compare all indices 0..32 against `simulate_protocol` on small exact models. Demonstrate an order reduction after cancellation and an all-index equality certificate. The independent oracle must not call the GF recurrence used by the production path.

**NX11-C - Resource-aware distant experiment integration.** Connect remote queries to an NX10 or finite experiment selector. Report compilation, cold/warm query and output-bit costs separately. Show exact large-index refusal and optionally a separately labeled modular huge-index check. Add at least one example where setup dominates and one repeated-query break-even calculation; no universal speedup is required.

## Bounded rollout and resume

Start with dimension <=16, no more than six scalar candidate responses, rational queries with estimated answer size below 4096 bits and independently checkable horizons <=64. Matrix powering costs roughly O(r^3 log n) rational operations in a dense r-state realization, but cancellation and bit growth govern actual cost. Retain the compiled fraction, index convention, source hash, replay outcome, query queue and benchmark workload. On resume, replay the source packet and one short-index oracle before using cached remote results. If state reduction is approximate, its time-domain error must be propagated through NX09/NX10 rather than presenting the approximate rational sequence as the exact original response.

## Adapter validation details

For the displayed recurrence, the upstream `from_recurrence` coefficients are `(-1/6, 5/6)`, ordered so that a[n+2]=c[0]a[n]+c[1]a[n+1]. Do not reverse that tuple by confusing denominator order with chronological recurrence order. The optional adapter should validate ints/Fractions and reject bools and binary floats before calling upstream, because Singularity's public exact-number contract is intentionally stricter than arbitrary Fraction coercion. A portable receipt should use its documented canonical rational encoding and a strict parser; upstream string-friendly internal packets do not justify accepting arbitrary unchecked numeric strings at every public boundary.


# NX12 - Complete constrained protocol populations

**Status:** proposed finite protocol compiler and optimizer integration. **Priority:** high after the first expanded fault population and uncertainty contracts. **Required track dependencies:** NX01 for robust acceptance semantics. **Useful connections:** NX03 fault populations, NX05 adaptive policies, NX07 capability restrictions, NX11 remote fixed blocks and NX35 proof-directed refinement. Initial scope counts and reconstructs legal nonadaptive protocols; adaptive policy trees are a different combinatorial population.

## Mathematical object and inherited insight

PerfectPower's completion planner preserves enormous populations through exact conditional completion counts, original-object ranking and reconstruction. Singularity already enumerates all affordable unconstrained operator words and optimizes panels on finite pools. The thermal default pool, however, is a handpicked list of step/pulse/alternating words at selected horizons. NX12 makes the declared experiment family complete under explicit laboratory constraints, while retaining every original protocol and its chronological interpretation.

Let A be a finite alphabet of legal interventions. A deterministic finite automaton has states q, initial q_0, transition delta and accepting states F. Each symbol has positive rational elapsed/action cost and nonnegative integer resource increments. Legal terminal sensors have their own requirements and costs. Define

\[
\Omega_C=\{(w,j):\delta(q_0,w)\in F,\ c(w)+c_j\le C,\ R(w)\le b,\ |w|\le H\}.
\]

Examples of resources are total heat, switch count and cooldown limits. Sensor identity is part of the experiment even when two sensors happen to produce equal readings. A protocol compiler counts original words, not unique resulting vectors or masks. Dynamic equivalence may later compress decision evaluation, but multiplicities and rank/unrank inverses must remain available.

## Completion recursion and exact reconstruction

Scale rational costs to integers with a common denominator if reasonably sized; refuse impractical denominator blowup rather than silently round. A memoized completion state records automaton state q, remaining cost B, remaining resources b, remaining horizon h and any last-symbol memory needed to count switches. Let C(q,B,b,h) count all accepting continuations including legal terminal sensor choices. Then

\[
C(q,B,b,h)=\operatorname{terminal}(q,B,b)+\sum_{a:\mathrm{feasible}}C(\delta(q,a),B-c_a,b-r_a,h-1).
\]

The terminal term counts all currently legal sensors; it must not count an unaccepted empty word unless the grammar permits it. For ranking, fix a total order on alphabet symbols, sensor labels and termination. Sum completion counts of preceding branches, then descend the chosen branch. Unranking chooses the unique cumulative-count interval containing an index. These operations preserve the original word and terminal sensor. Uniform sampling by a uniform rank is mathematically exact; a seeded pseudorandom implementation is reproducible but is not a proof of physical randomness.

Determinism matters: an ambiguous nondeterministic grammar can have several accepting derivations for one word. Counting derivations would inflate the protocol population. Determinize within a stated state budget or reject ambiguous grammar semantics; do not deduplicate after huge enumeration and call that the same compiler. Zero-cost symbols can make a cost-bounded language infinite unless an independent horizon/resource decreases; positive per-step elapsed cost is the clean default. Zero amplitude still consumes elapsed time. Empty words and zero-cost terminal observations need explicit conventions.

## Existing source crosswalk

| Source | Existing contract | New work |
|---|---|---|
| `src/singularity/panels.py::experiment_pool` | All chronological operator experiments affordable under positive attachment costs, bounded by max_experiments. | Constrain by a DFA and multiple resources; preserve count/rank/unrank. |
| `panels.py::explicit_pool`, `reading_pool` | Validated finite readings and labels. | Stream or materialize the accepted population without losing original IDs. |
| `panels.py::minimum_cost_panel`, `exhaustive_minimum_panel` | Exact finite exact/common-box pair cover. | Use NX01 heterogeneous pair coverage where required; completeness of language is a separate certificate. |
| `observability.py::experiment`, `apply_word`, `minimum_distinguishing_experiment` | Chronological evaluation and cheapest exact witness in the declared unrestricted language. | Grammar restriction must preserve or augment state; unrestricted witnesses may be illegal. |
| `robust_search.py::bounded_margin_search`, `exhaustive_margin_search` | Bounded robust single-experiment optimization. | Grammar/resource-aware bounds need their own admissibility proof. |
| `thermal_diagnostics.py::default_protocols`, `protocol_pool` | Current finite 112-experiment baseline and sparse prefix caching. | Keep this baseline untouched for comparison; add complete constrained populations separately. |
| `src/singularity/population.py::HeightPopulation` | Original labeled bounded graph-height assignments. | This is not a protocol-word population; do not stretch it into an incompatible API. |

The PerfectPower completion planner is an architectural precedent, not a source API verified in this packet. Locate and read its current implementation before importing anything. A small stdlib DFA completion engine is a new domain adapter justified by the protocol problem, not a replacement for the existing graph-height population class.

## Tiny rational population

Use amplitudes {0,2}, nonempty horizon at most 3, total amplitude at most 4, and at most one change between consecutive symbols. The initial symbol does not itself count as a switch. Legal length-one words are 0 and 2. All four length-two words are legal. Legal length-three words are 000,002,022,200,220; 222 exceeds heat, while 020 and 202 exceed switching. There are 11 words. With two terminal sensors there are exactly 22 original experiments, regardless of duplicate readings.

Let reset cost be 1, elapsed cost 1 per step, heat cost half the amplitude sum and each sensor cost 1. At total budget 4, only words 0,2,00 are affordable, giving six experiments. Verify these counts by a separate Cartesian-product enumeration. Preserve lexicographic rank/unrank and sample every rank in the 22-member population. This tiny example catches initial-switch ambiguity, mistaken alphabet interpretation, sensor multiplicity loss and cost-rounding errors.

## Proposed API and portable evidence

Create proposed `src/singularity/protocol_population.py`, `tests/test_protocol_population.py`, `scripts/protocol_population.py` and `docs/research/PROTOCOL_POPULATIONS.md`. Proposed immutable types are `ProtocolAlphabet`, `DeterministicProtocolGrammar`, `ProtocolResources`, `ProtocolPopulation` and `Protocol(identifier, word, sensor)`. Methods `count(prefix=())`, `rank(protocol)`, `unrank(index)`, `conditional_count(prefix, terminal_sensor=None)`, `iter_protocols(max_members)` and `compile_pool(candidates, max_members)` must state ordering, exact units and validation exceptions.

Receipt `singularity.protocol-population/1` stores alphabet IDs and their physical amplitudes, DFA transitions, acceptance states, switch semantics, resource/cost vectors, rational scale, terminal sensors, ordering, exact count, selected rank/protocol pairs, completion-table integrity and source/readout bindings. A digest only provides integrity. Small independent replay recomputes all counts; larger receipts can expose a locally checkable DAG of completion equations with root count, acyclicity and terminal cases. This certifies grammar counts, not the physical model or optimal experiment.

## Three bounded acceptance pushes

**NX12-A - Complete constrained counts and inverses.** Implement deterministic grammar validation, completion recurrence and rank/unrank with exact costs. Retain the 22/6 examples, empty-language and unreachable-state cases, all ranks, and malformed/zero-cost-cycle refusals. Independent tests enumerate products without using the completion recursion. Randomized tiny grammars compare every word and sensor.

**NX12-B - Physical protocol adapter and complete optimization.** Connect alphabet IDs to actual scalar heater amplitudes and evaluate a bounded 4-by-4 thermal population. Compare every short output against independent neighbour-flux stepping. Materialize no more than 4096 experiments initially and compare its optimum with exhaustive panels where possible. Demonstrate exactly which protocols the handpicked baseline omitted, even if the optimum does not improve.

**NX12-C - Completion-aware search and certificates.** Add grammar/resource-aware branch-and-bound for one objective, preferably cheapest robust single experiment or target pair-cover on a bounded materialized pool. Prove each pruning bound, return original protocol witnesses and certify all cheaper protocols excluded. Retain full population counts even when dominated decision representatives are compressed. Update mathematical explanation and archive through the integration owner.

## Complexity, safe pruning and continuation

The dynamic program is polynomial in the number of reachable resource states, not in the numeric bit-length of arbitrary budgets: it is pseudo-polynomial. Its memory is O(number of reachable memo states), and counts can have many bits. With alphabet size a, full explicit words can grow as a^H. Start a<=3, H<=12, grammar states<=16 and explicit pool<=4096. Estimate counts before evaluating all physical trajectories; use prefix caches already present in `protocol_pool`.

Linear dependence is not a safe generic pruning rule for robust margin: an observation dependent on retained rows may amplify a difference much more strongly at useful cost. Likewise two words with identical nominal output but different uncertainty, cost, resource state or future legal continuations cannot be merged indiscriminately. A future grammar-aware all-word closure can use a product automaton and typed observation spaces, but requires a separate theorem and cost semantics.

Save grammar/source hashes, exact rational scale, root counts, memo-table version, ordering, remaining search frontier, incumbent and lower bound. A population-size refusal is a resource limit, not a negative scientific result. Resume by replaying the complete tiny population and all saved rank/unrank witnesses before extending horizon or resources.


# NX13 - Typed operator languages

Status: proposed expansion of existing exact operator machinery. This packet does not announce an implemented typed compiler or a new graph separation theorem. Its output is a finite, explicitly typed experiment language with certificates that all legal future experiments factor through its quotient.

## Why this belongs in the program

The present observation engine has one ambient state space. That is natural when every action leaves two ordered terminals in place. A separator computation, however, introduces a terminal, forgets one, joins independent blocks, or changes the boundary convention. Those actions have different source and target spaces. Forcing all of them into a single matrix can hide illegal compositions or fill large matrices with irrelevant coordinates. The appropriate extension is a finite directed type graph, with an exact vector space at each vertex and compatible operators on its arrows. The mathematical gain is a certificate about every well-typed future word, rather than a collection of unrelated local reductions.

This directly extends the user's older SOE principle that action legality is part of behavior. In the present linear setting legality is initially a property of the declared type. State-dependent guards need a richer semantics and are excluded from the first implementation. Similarly, graph assembly must use fresh interior copies, preserve terminal order, and prevent duplicate terminal edges. A matrix identity does not establish that an arbitrary sequence assembles a legal graph.

## Verified inherited crosswalk

| Existing source | Verified object | Reuse and boundary |
|---|---|---|
| `src/singularity/observability.py` | `OperatorSystem`, `Experiment`, `ClosureCertificate`, `observable_closure`, `verify_certificate`, `certificate_bundle`, `replay_bundle` | Exact `Fraction` arithmetic, retained realizable witness rows, nullspaces, row-coordinate certificates. Current systems are single-type square systems. |
| `src/singularity/terminal_moves.py` | `OrderedContextAttachment`, `OrderedMoveSystem`, `compile_graph`, `assemble`, `direct_observations`, `operator_system` | Existing ordered, genuinely asymmetric graph contexts and terminal extensions. No terminal-terminal context edge is allowed. |
| `src/singularity/charges.py` | `parallel_interfaces`, `forget_terminal`, `kernel_from_charges` | Verified charge-level graph operations, with complete `max_volume` depth metadata and explicit terminal order. |
| `src/singularity/separator_compiler.py` | `empty_interface`, `introduce_terminal`, `run_schedule`, `compile_interface`, `build_step_operator` | Existing introduce/forget schedules and sparse step operators. Do not rebuild these algorithms. |
| `tests/test_terminal_moves.py`, `tests/test_observability.py` | Direct assembled-graph oracle; generic certificate failure cases | Independent checks of chronology and graph semantics. |

Read `docs/research/ORDERED_CONTEXTS.md` and the operator chapter before assigning any new theorem identifier. Existing words are chronological: `(i1,i2)` means apply `i1` first, giving observation row `L M_i2 M_i1`. Backward row exploration therefore prepends an action, not appends it.

## Formal specification and derivation

Let `B` be a finite set of types. Type `b` has a finite-dimensional rational column space \(V_b=\mathbb Q^{d_b}\). An action `a:s(a)->t(a)` has matrix `M_a` of shape `d_t by d_s`. Observations at type `b` are rows `L_bj` of length `d_b`. Costs are positive rationals for actions and nonnegative rationals for observations. A legal word is a directed path; its reading is the observation at its final type multiplied by the matrices in reverse chronological order.

Define \(W_b^0=\operatorname{span}_{\mathbb Q}\{L_{bj}\}\) and iterate simultaneously

\[
W_b^{k+1}=W_b^k+\sum_{a:s(a)=b}W_{t(a)}^kM_a.
\]

The total rank can increase at most `sum_b d_b` times. A pass with no new independent rows at any type proves closure. Every longer legal experiment lies in the resulting row space by induction on path length. Conversely each retained row must carry an actual legal path and final observation, so the computed spaces contain only linear combinations of available measurements. Both inclusions are necessary: arbitrary row reduction residuals are not physical experiments.

Choose retained witness rows `B_b` spanning `W_b`. The replayable identities are

\[
L_b=A_bB_b,\qquad B_{t(a)}M_a=T_aB_{s(a)}.
\]

Here `T_a` has shape `r_t by r_s`, not necessarily square. The observable state is `z_b=B_bx`. Its update is exactly `z_t=T_a z_s`. If `N_b=ker B_b`, then for `x in N_s` the identity gives `B_tM_ax=T_aB_sx=0`; hence `M_aN_s` is contained in `N_t`. This proves the quotient dynamics is well defined. Minimality is among linear compressions preserving every declared future reading: any such compression must have kernel contained in `N_b`, and therefore dimension at least `rank B_b`.

Cost-ordered span pruning extends only with type-aware accounting. A dependent row can be replaced by earlier rows at the same source type; every legal preceding extension then remains legal and has no larger cost. This supports cheapest exact distinguishing witnesses. It does not support maximum-margin pruning: a dependent measurement may have a much larger useful discrepancy under noise.

## Tiny exact worked example

Take type `a` with \(V_a=\mathbb Q^{2}\) and type `b` with `V_b=Q`. There is no direct observation at `a`; at `b` observe `L_b=(1)`. Let

\[
M_f=(1\quad1):V_a\to V_b,\qquad
M_g=\begin{pmatrix}1\\0\end{pmatrix}:V_b\to V_a,
\]

with costs two and three. The first backward step discovers `(1,1)` at `a`. Returning around the cycle gives `L_bM_fM_g=(1)`, so no new row appears. Thus `B_a=(1,1)`, `B_b=(1)`, `N_a=span{(1,-1)}`, and `N_b=0`. Quotient matrices on both arrows are `(1)`. States `(2,0)` and `(0,2)` at type `a` are indistinguishable forever; `(2,0)` and `(0,3)` are distinguished by action `f` at cost two. Trying to read `L_b` directly at type `a` must be rejected. This tests rectangular maps, empty observation collections, cycles, nullspaces, and typed legality without relying on graph enumeration.

## Proposed API and portable data

Add `src/singularity/typed_observability.py`, leaving the existing public API unchanged. Proposed constructors are `StateType(identifier, dimension)`, `TypedAction(identifier, source, target, matrix, cost)`, `TypedObservation(identifier, type_id, row, cost)`, and `TypedOperatorSystem(types, actions, observations)`. Public functions should include `typed_closure`, `typed_experiment`, `typed_apply_word`, `verify_typed_certificate`, and `minimum_typed_distinction`. Start with immutable tuples and exact rationals; reject booleans, floats, duplicate identifiers, undeclared types, shape errors, and illegal paths.

The proposed schema `singularity.typed-operator-closure/1` records each type's dimension, witness paths, basis rows, observation coordinates, action coordinates, and nullspace. Each action records ordered source/target identifiers. Rationals use the existing canonical numerator/denominator representation. Empty matrices must carry their intended dimensions explicitly; a zero-rank source or target is legal and cannot be inferred from an empty tuple. A graph adapter adds the volume convention, terminal labels, permitted edges, and graph-assembly rule as separate provenance. Generic algebraic replay does not prove that adapter.

## Three acceptance pushes

| Unit | Dependencies and artifacts | Required acceptance and independent check |
|---|---|---|
| **NX13-A: typed algebra contract** | Existing operator module; new module, specification note, tiny fixtures and `tests/test_typed_observability.py`. | Prove closure, quotient invariance, and per-type linear minimality in human-readable form. Verify rectangular example above by handwritten arithmetic and by a local oracle independent of closure insertion. Reject ill-typed paths and malformed dimensions. |
| **NX13-B: graph adapters** | NX13-A; existing charges/separator/terminal moves. New adapter and `scripts/typed_contexts.py`. | Select a finite grammar whose boundary types and fixed-volume coordinates genuinely close. For all legal short paths on tiny graphs, compare adapter matrices with `local_coefficients` on actual assembled graphs. Include noncommuting paths and duplicate-edge rejection. |
| **NX13-C: certificates and costs** | NX13-B. JSON receipt, replay command, manuscript proposition and cost tests. | Replay all identities with no compiler invocation. Compare cheapest witnesses with exhaustive legal-path search under a finite cost bound. Test zero-rank types, empty outputs, cycles, distinct start/end dimensions, and deliberate word reversal. |

## Resources, failure modes, and stop point

Use two to four types and total dimension below 100 initially. Closure is polynomial in matrix dimensions but exact numerator growth can dominate. Record type ranks, nonzeros, coefficient bits, legal path counts, and verification time separately. Sparse representations can follow correctness; do not erase declared zero-dimensional spaces to optimize formatting.

The principal failure is an apparently finite type system that is not closed under its graph operations. Terminal creation can produce unbounded types; edge-status changes can require additional boundary metadata; minimum-zero normalization can change composition rules. Fix the finite grammar before claiming termination. A refused grammar is an implementation boundary, not a theorem that the graph operation is impossible. Stop after an independently replayed finite grammar, exact cheapest witnesses, and an explicit limitations paragraph. State-dependent guards, nonlinear charge joins, infinite type collections, physical thermal semantics, and full-series equivalence remain outside this packet unless separately scoped and proved.


# NX14 - Parameter-wide observable modules

Status: proposed expansion of the existing univariate polynomial observability implementation. The current repository already computes complete parameter-aware observation modules and exact exceptional ranks for the standard two symmetric graph contexts through volume four. This packet extends their scale, parameter coverage, certificates, and explanatory theory. It must not be presented as the first implementation of polynomial observability.

## Purpose and inherited significance

A rank calculation at `q=1/2` answers one specialization. A generic calculation over `Q(q)` answers almost every specialization, while potentially missing exceptional ones. The actual goal is a partition of the declared parameter domain into regions and points with certified observable rank, together with usable experiment bases on each region. This realizes the older PerfectJet principle that a change in parameter can change which questions are answerable, not just alter numerical readings.

The standard graph receipt currently has dimensions 3, 7, 13, and 22 at budgets one through four. Every parameter in `(0,1)` gives full rank for those declared systems. Their complete determinantal divisors factor into powers of `q`, `q-1`, `q+1`, and cyclotomic polynomials. This is finite exact evidence. It does not prove a cyclotomic factor theorem at arbitrary budget, and the fixed-parameter rank `69 of 70` at budget seven does not establish parameter-wide rank 69.

## Verified inherited crosswalk

| Existing source | Exact API or result | What the new work should add |
|---|---|---|
| `src/singularity/parametric.py` | `PolynomialOperatorSystem`, `generic_closure`, `observation_module`, `ObservationModule` | Broader resource-aware calculations and explicit basis/transition certificates, retaining current semantics. |
| Same module | `determinantal_divisor`, `determinantal_divisor_by_minors`, `smith_invariant_factors` | Independent routes to rank-drop polynomials; do not substitute one selected determinant. |
| Same module | `rank_at_rational`, `rank_at_algebraic`, `factor_over_q`, `real_roots`, `parametric_observability` | Certified specialization and root isolation, with explicit partial-factorization outcomes. |
| Same module | `symbolic_boundary_system` | Symbolic graph context compiler, independently specialized against `BoundaryExperimentSystem`. |
| `tests/test_parametric.py` | Leibniz determinant oracle, sparse polynomial arithmetic, explicit word enumeration | Existing oracle design should remain independent of HNF code. |
| `docs/research/PARAMETRIC_OBSERVABILITY.md`, `results/parametric_observability.json` | Scope, factor tables, finite resource record | Read and extend instead of replacing with a weaker generic-rank summary. |

## Mathematical machinery

For dimension `D`, polynomial operators `M_i(q)`, and observation rows `L_j(q)`, let `N_k` be the `Q[q]`-module generated by words of length at most `k`. Then

\[
N_{k+1}=\langle L_j\rangle+\sum_i N_kM_i.
\]

The polynomial ring is Noetherian, so the chain stabilizes. Rank stabilization over `Q(q)` is insufficient: a full-rank submodule can still enlarge while its polynomial index decreases. The current Hermite implementation explicitly preserves this distinction. Once `N_{k+1}=N_k`, its basis generates every future experiment over `Q[q]`.

Write `W(q)` for a finite generator matrix of the relevant module, generic rank `r`. Define

\[
D_r(q)=\gcd\{\det W_{I,J}(q):|I|=|J|=r\},
\]

monically normalized. At an algebraic specialization `alpha`, the rank falls below `r` if and only if every maximal minor vanishes, equivalently `D_r(alpha)=0`. The implication uses a univariate PID. For several parameters the common zero set of minors is generally an ideal variety, not the roots of one gcd. A two-parameter implementation needs ideals or a sound stratification method; applying the univariate gcd recipe silently is incorrect.

For rank at least `k`, some `k`-minor must be nonzero. A Bezout identity among suitable maximal minors can prove full rank throughout a domain when their gcd has no root there. This gives a useful certificate architecture: exact module-generation identities, determinantal-divisor witnesses, and separate real-root exclusion. It allows an auditor to replay algebra without rerunning the most expensive symbolic closure.

The standard contexts have polynomial entries, but other transport matrices can have Laurent or rational-function entries. Introduce a declared common denominator `h(q)` and domain guard `h(q)!=0`; multiply to polynomial matrices only after accounting for how operator words acquire powers of `h`. Excluding a pole is not proving a rank drop there. Laurent powers of `q` are harmless only on a domain excluding zero, and the schema must say so.

## Tiny exact example: false and true exceptions

Let `a(q)=q-1/2`, observations `L1=(1,0)`, `L2=(0,a)`, and

\[
M=\begin{pmatrix}0&1\\0&0\end{pmatrix}.
\]

The generic basis may select `L1,L2`, whose determinant is `a`. At `q=1/2` that chosen basis loses rank. But `L1 M=(0,1)` is a legal experiment, and the complete observation module contains both standard coordinate rows. Its maximal determinantal divisor is one, so no exception exists. This is an exact interior-domain example of why generic-basis roots are only candidate exceptions.

For a true exception take a single observation `L=(1,a)` and `M=diag(1,2)`. The two rows `L,LM` form

\[
\begin{pmatrix}1&a\\1&2a\end{pmatrix},\qquad \det=a.
\]

All later rows have form \((1,2^k a)\). At `q=1/2`, every row is `(1,0)`; away from it, the first two rows span \(\mathbb Q^{2}\). Thus the rank function is exactly one at the exception and two elsewhere. Both examples belong in permanent receipts because sampled rank checks can overlook either failure mode.

## Proposed API and output schema

Preserve `parametric.py` APIs. Add resource and certificate options to a wrapper, proposed `parameter_module_receipt(system, domain, limits, replay=True)`, rather than changing the meaning of existing return values. Suggested limits are maximum dimension, polynomial degree, coefficient bits, module steps, factoring time, and root-isolation subdivisions. A return state is `complete`, `module_complete_factor_partial`, or `budget_refusal`; no partial factorization may be serialized as a complete exceptional set.

Proposed schema `singularity.parameter-module/1` records the polynomial system, coefficient domain, excluded denominator set, generic rank, Hermite module basis, closure-coordinate identities, maximal determinantal divisor, factors with independent factorization evidence, isolated real roots, and specialized ranks. Distinguish actual experiment rows from polynomial combinations. Chart records list witness words and a determinant guaranteed nonzero on their parameter region. Use exact rational endpoints for domains and intervals. Algebraic roots carry an irreducible polynomial and isolating interval, not a decimal identifier.

## Three acceptance pushes

| Unit | Dependencies and artifacts | Required acceptance and independent check |
|---|---|---|
| **NX14-A: resource-bounded module certificates** | Existing parametric machinery. Add wrapper, replay schema, two worked fixtures, tests and specification. | Verify module closure identities and determinantal divisors independently on tiny explicit-word matrices. Reproduce false and true interior exceptions above. Deliberately alter a module generator or factor and require rejection. |
| **NX14-B: next graph budgets** | NX14-A. Extend `scripts/parametric_observability.py` or add a separate opt-in receipt. | Attempt budget five first with logged limits. Compare rational specializations with `observable_closure`; use modular ranks only as lower-bound/generic-witness evidence. Report any incomplete symbolic calculation honestly, without promoting sampled ranks to interval theorems. |
| **NX14-C: parameter atlas and explanation** | NX14-B; optional NX13 for typed systems, not required for the first untyped atlas. | Produce bases covering certified parameter cells and exact ranks at exceptions. Prove any new factor claim only when the calculation or independent argument establishes it. Add a bounded rational-function example with a pole guard and independently check specialization. |

## Resources, hazards, and stop point

The existing budget-four calculation already has a determinantal divisor of degree 371. Dimension and degree are separate cost drivers; sparse input matrices can produce dense HNF intermediates. Record maximum numerator bits, polynomial degrees, module-step counts, wall time, peak memory, and excluded cases. Start with one larger budget and a strict time budget. Do not enumerate all experiment words at graph-scale dimension.

A selected minor is not the determinantal divisor; generic rank is not interval rank; a modular nonzero minor is not an upper-bound certificate; rational samples do not exclude irrational roots; and a partially factored polynomial is not a completely classified exceptional locus. These are mathematical scope errors, not formatting problems. The clean stopping point is a replayable new complete finite calculation or a bounded refusal plus the exact remaining symbolic bottleneck. An all-budget cyclotomic theorem, multi-parameter elimination, and full-series graph identifiability remain independent research targets.


# NX15 - Graph-realizable invisible directions

Status: proposed constrained graph search and rigidity work. No graph pair realizing either frontier vector has been exhibited. The first remaining candidate budgets are 38 when simple terminal-edge contexts are allowed, and 11 for the edge-free symmetric context class, under the current rational-parameter interpolation hypotheses. Those are necessary coefficient-level frontiers, not existence theorems.

## The mathematical question

The observable quotient describes which formal interface differences are invisible. A graph interface occupies a much smaller structured subset of that formal vector space: its coefficients come from the same adjacency matrix, nonnegative height populations, terminal degrees, and compatible interior slices. The next important question is whether the quotient's surviving directions meet differences of actual graph states. A positive answer gives a real limitation of the experiment language. A negative answer within a broad structural family gives a graph rigidity result stronger than arbitrary-vector observability.

This is a natural bridge to PerfectPower's constrained populations. Search actual original objects with reconstruction witnesses, rather than solve for an arbitrary vector and label it a graph. Canonical isomorphism keys can avoid repeating equivalent blocks, but coefficient counts must still count the original labeled height assignments. Quotienting height populations by graph automorphisms silently changes the invariant.

## Verified inherited code and evidence

| Existing source | Verified machinery | Intended role |
|---|---|---|
| `src/singularity/contexts.py` | `interface_status`, `diagonal_defects`, `top_degree_kernel`, `lower_degree_condition` | Reproduce the precise formal and slice-constrained frontier being searched. |
| Same module | `realizable="interpolated"`, `boundary_determinant`, `interpolation_rank` | Unequal-degree slice interpolation is already integrated for rational `q in (0,1)`; do not reopen it as an unimplemented item. |
| Same module | `interior_zero_coefficient`, `recover_by_finite_differences` | Degree constraints and independent delayed-observation diagnostics. |
| `src/singularity/terminals.py` | `terminal_kernel`, `glue_graphs` | Exact block kernels and actual glued graph construction. |
| `src/singularity/charges.py` | `charge_interface`, `kernel_from_charges`, `charge_chart` | Strong shared-charge constraints and economical compilation for suitable blocks. |
| `src/singularity/separator_compiler.py`, `src/singularity/population.py` | Existing exact compilation and original-object populations | Reuse for constrained families; broad volume-38 enumeration is not a sensible default. |
| `tests/test_contexts.py` | First free budgets 38 and 11 in interpolated mode | Existing fixtures distinguish formal modes, slice modes, and balanced hypotheses. |

Read the interior-slice propositions and their parameter conditions in the graph-interface chapter. The exceptional irrational interpolation example matters: do not state the rational-parameter cutoff as an unrestricted theorem for every real `q`.

## Exact objects and compatibility conditions

For an ordered two-terminal block `G`, write

\[
K_G(s,t;x,q)=\sum_{h\ge0}x^{|h|}q^{E_G(s,t,h)},\qquad
Y_{(s,t),v}=[x^{v-s-t}]K_G(s,t;x,q).
\]

For a symmetric interface combine `(s,t)` and `(t,s)` exactly once according to the existing `symmetrize` convention; do not average coefficients. A target pair must satisfy every lower-volume equality, the entire context-observation constraint at the frontier, and a nonzero difference in the permitted invisible direction. Checking only the highlighted collision coordinates is insufficient: the two graphs can differ elsewhere and immediately become distinguishable.

The interior-zero slice is determined by terminal interior degrees. At slice `j`, after removing the zero-height factor, the polynomial has degree at most `j` in each of \(U=q^{-2s}\) and \(V=q^{-2t}\). At rational `q` the triangular interpolation theorem forces a slice from samples of total volume at most `3j`. Thus a graph candidate must simultaneously satisfy all these low-slice restrictions. Matching terminal degrees alone leaves many forbidden coefficient vectors.

Additional constraints come from charge populations. An interface table records counts indexed by interior volume `j`, boundary charge `Q`, and interior energy. They are nonnegative integers. The same terminal-neighborhood patterns and interior graph generate every row. Treating rows as independent integer variables produces false realizations. One can use a relaxed charge feasibility problem to reject pairs, but satisfying the relaxation does not prove a graph exists.

## Tiny exact frontier calculations

For the terminal-edge frontier the three terminal states are

\[
(1,18),\ (6,17),\ (10,15),\qquad s^2+t^2=325.
\]

Their terminal sums are 19, 23, and 25, so at total volume 38 the interior volumes are 19, 15, and 13. Let \(y=(q^{289},q^{121},q^{25})\), using \((s-t)^{2}\). The coefficient vector

\[
v=(y_3-y_2,\ y_1-y_3,\ y_2-y_1)
\]

obeys `sum_i v_i=0` and `sum_i y_i v_i=0` by direct cancellation. It is therefore the two-row annihilator on that collision group. At `q=1/2`, multiply by \(2^{289}\) to obtain an integer vector if desired. Its enormous coordinate sizes are exact arithmetic data; they are not multiplicities of an already constructed graph difference. A realizing pair must produce one common scalar multiple and every other required coordinate equality.

For the edge-free frontier, `(0,5)` and `(3,4)` both have energy radius 25. At total volume 11 their interior volumes are six and four. The vector `e_(0,5)-e_(3,4)` is annihilated by the single group-sum observation. Again this says only that the formal direction survives. The simultaneous slice and graph constraints are the research problem.

As a very small negative sanity check, two terminal placements of a three-vertex path can have the same immediate closed series yet different interfaces. Existing terminal-extension experiments distinguish them. The search must therefore distinguish blindness under its declared symmetric context class from blindness under a larger language with terminal moves. Changing the language changes the claim.

## Proposed search contract and schema

Add `scripts/realizable_interfaces.py` with a small supporting module only where reusable logic is necessary. Proposed `SearchFamily` records vertex bound, allowed degrees, connectedness, terminal ordering, terminal-edge policy, graph constructor, and exact parameter. `search_frontier(family, R, kappa, mode, limits)` first buckets by cheap necessary invariants, then by exact low-volume kernels or charges, and only then computes expensive target coefficients. A pair witness stores both labeled edge lists, terminals, coefficient convention, all lower equalities, frontier difference, scalar multiplier, and independent direct-gluing comparisons.

The schema `singularity.realizability-search/1` must distinguish `pair_found`, `complete_bounded_exclusion`, and `incomplete_budget`. Completeness of a bounded exclusion requires a complete enumerator of the declared graph family, with counts or rank/unrank witnesses. A digest of visited graphs gives integrity, not completeness. For a structural constructor such as trees or bounded-width strips, record its exact parameter range and duplicate-removal method. State whether equality is polynomial in `q` or only at one rational specialization; the latter is weaker and must not be silently upgraded.

## Three acceptance pushes

| Unit | Dependencies and artifacts | Required acceptance and independent check |
|---|---|---|
| **NX15-A: realization specification and filters** | Existing contexts, interpolation and charge modules; no new rank-module work required. Specification, small search module, fixtures. | Reproduce both frontier vectors and rational slice bounds. Reject deliberately inconsistent nonnegative-charge relaxations. Compare all filters with direct tiny-graph kernels to ensure no valid graph pair is discarded. |
| **NX15-B: complete bounded families** | NX15-A; optional NX16 for incremental reuse. Retained search manifests and population counts. | Exhaust at least two declared small structural families using independent constructor checks. Confirm every surviving pair by a separate coefficient engine. A finite negative result must quote graph counts, bounds, parameter and language. |
| **NX15-C: witness or rigidity advance** | NX15-B. New manuscript proposition and independently replayable receipt. | Either exhibit a full actual pair with its entire truncated kernel difference and glued-observation checks, or prove a new structural incompatibility eliminating a stated family of candidates. Do not require a positive pair to call the bounded work useful. |

## Resource design, hazards, and stopping

Estimate weak-composition work before each stage: a graph with `m` interiors has `binom(j+m-1,m-1)` profiles at interior volume `j`. At frontier 38 these counts quickly overwhelm direct enumeration. Start with the volume-11 edge-free case, low treewidth, small charge-pattern dimension, and high-information low slices. Use the separator compiler only after checking width and charge-state growth. Record profile counts, peak cells, exact coefficient bits, and time.

A nonzero formal null vector is not a graph pair. Finite agreement is not full-series equality. An isomorphism census does not authorize orbit-counting heights. A stronger observation language can invalidate a previously hidden pair. Modular equalities are filters, never equality proofs. Stop at a replayable bounded exclusion or a fully verified witness, with an explicit next family. There is no instruction to launch an unbounded graph census until a desired result appears.


# NX16 - Incremental connected-support compilation

Status: proposed incremental extension of an existing exact locality compiler. The repository already computes pinned series and local series from connected supports, with memoized decorated support types. The new result is exact reuse after local graph or nonnegative edge-weight changes, including a sound cache invalidation rule and independently checked update complexity.

## Concept and inherited bridge

Current locality says that coefficients through volume `R` depend on connected supports of at most `R` vertices. A local defect should therefore change only support contributions touching that defect. This converts repeated graph compilation into local update work. The subtlety is that a deleted edge can destroy connectivity, and even a singleton touching a modified edge changes its ambient-degree decoration. Updating only supports that contain both endpoints is wrong. The safe formulation uses the union support graph and recomputes every potentially affected contribution containing either endpoint.

This links the graph program to the thermal fault population without identifying their physical models. Both profit from compiling a nominal object once and reusing it across local changes. The graph invariant remains a height-population series. The thermal model remains a discrete evolution equation. The shared computational principle is localized dependence, not an assertion that graph height energy is a temperature model.

## Verified inherited crosswalk

| Existing source | Verified API | Reuse and limitation |
|---|---|---|
| `src/singularity/locality.py` | `connected_sets`, `connected_supersets`, `exact_support_log`, `pinned_log`, `series_from_log` | Enumerates exact supports and reconstructs the series from its formal logarithm. Current graph input is simple unweighted `Graph`. |
| Same module | `_type_key`, `_restricted_log`, `_components` | Ambient-degree decorations are part of memo keys; exact AHU tree keys and bounded canonicalization avoid false sharing. Private functions are implementation details, not a promised public interface. |
| Same module | `pinned_series`, `pinned_series_by_enumeration` | Existing independent composition oracle for unweighted examples. |
| `src/singularity/weighted.py` | `WeightedGraph`, `weighted_coefficients` | Existing weighted enumeration has its own positive integral weight contract; inspect before attempting a new zero-weight representation. |
| `tests/test_locality.py` | Brute-force support checks, direct coefficient comparisons, no-global-edge-scan test | Preserve independent oracles and bounded-degree scaling evidence. |
| `src/singularity/charges.py` and `separator_compiler.py` | Boundary charge tables and independent separator compilation | Useful cross-check for suitable graph blocks, not required in the first incremental core. |

The current locality compiler already contains cycle and moment extensions. Do not rewrite them or claim their existing functionality as the new incremental advance.

## Exact weighted formulation

On a fixed vertex set use symmetric nonnegative integral edge weights `w_uv` and nonnegative integral pinning `lambda_v`. Put

\[
E_w(h)=\sum_{u<v}w_{uv}(h_u-h_v)^2+\sum_v\lambda_vh_v^2.
\]

Then \(F_w=\sum_h x^{\lvert h\rvert}q^{E_w(h)}\) has ordinary nonnegative energy exponents. A zero edge is absence. Rational weights require an explicitly declared common energy unit converting every exponent to an integer; otherwise the current polynomial-in-`q` representation is not applicable. Negative weights are excluded from this initial contract because the energy and bounded-exponent arguments change.

Introduce separate variables `x_v`. For `Z_T`, set `x_v=0` outside `T`, retaining the full ambient weighted degree of vertices in `T`. Define

\[
\Phi_S(w)=\sum_{T\subseteq S}(-1)^{|S|-|T|}\log Z_T(w).
\]

This is exactly the part of `log F_w` whose multivariate monomials use every vertex in `S`. Therefore it vanishes below volume `|S|`. If `S` is disconnected in the positive-weight support graph, restricted partition functions factor over components and `Phi_S=0`. This proves

\[
\log F_w\pmod{x^{R+1}}=\sum_{S\text{ connected},\ |S|\le R}\Phi_S(w).
\]

Now compare `w` and `w'` and let `D` be all endpoints of changed edges plus changed pinning vertices. Let `U` have an edge whenever either graph has positive weight there. Any nonzero contribution in either version is connected in `U`. If `S` misses `D`, its internal weights, vertex pinning, and ambient degrees are unchanged, so `Phi_S(w')=Phi_S(w)`. Hence

\[
\Delta\log F=\sum_{\substack{S\text{ connected in }U\\|S|\le R,\ S\cap D\ne\varnothing}}\bigl(\Phi_S(w')-\Phi_S(w)\bigr)\pmod{x^{R+1}}.
\]

This union-graph formula covers insertions, deletions, and zeroing weights. It is safe to include a support connected only in `U`: the vanished side contributes zero. Filtering solely with the new graph misses old contributions removed by deletion. Filtering solely with the old graph misses newly connected contributions after insertion.

## Tiny exact worked example

Compare two isolated vertices with a single edge, with zero pinning. For the isolated graph,

\[
F_0=1+2x+3x^2+O(x^3),\quad \log F_0=2x+x^2+O(x^3).
\]

For the edge,

\[
F_1=1+2qx+(1+2q^4)x^2+O(x^3),
\]

so \(\log F_1=2q x+(1+2q^{4}-2q^{2})x^{2}+O(x^{3})\). Each singleton has support contribution \(q x+(q^{4}-q^{2}/2)x^{2}\); the pair contribution is \((1-q^{2})x^{2}\). The singleton terms change because the edge changes ambient degrees, even though no singleton contains both endpoints. This is the mandatory regression example for correct invalidation.

At `q=1/2`, \(\Delta \log F=-x-3x^{2}/8+O(x^{3})\). Reconstructing by formal exponentiation gives \(F_1=1+x+9x^{2}/8\), versus \(F_0=1+2x+3x^{2}\). Reversing the update must recover the original series exactly. A weight change from one to zero is the same deletion, not a separate approximate case.

## Proposed API, metadata, and certificates

Propose `LocalityCompilation(graph_spec, max_volume, pinning, support_index, contributions)` and `compile_locality`, `apply_local_changes`, `verify_local_update`. Keep the existing `pinned_log` API unchanged. Graph specifications include immutable vertex identifiers, nonzero integral weights, per-vertex pinning, and the energy unit. A `LocalChange` records old and new weight, or old and new pinning; stale-old-value edits must be rejected to prevent applying a patch to the wrong baseline.

The new schema `singularity.locality-update/1` stores baseline graph data, baseline series or logarithm, exact changes, declared union graph, affected endpoint set, truncation depth, affected support list, old/new support contributions, and the resulting logarithm. Counts and polynomial coefficients use existing exact representations. Cache keys must include all internal weights, ambient weighted degrees, pinning labels, variable conventions, and truncation depth. A set-only fallback key is safe only within its graph/version namespace; reusing that fallback across unrelated graphs can create false collisions.

A replay certificate can sum listed corrections cheaply, but completeness of the affected support list needs a separate check: re-enumerate union-graph supports meeting `D` or validate a complete combinatorial enumerator. A digest cannot certify that an omitted support was zero. The independent tiny oracle remains full weak-composition enumeration using edge differences directly, without calling the support compiler.

## Three acceptance pushes

| Unit | Dependencies and artifacts | Required acceptance and independent check |
|---|---|---|
| **NX16-A: weighted locality contract** | Existing locality and weighted modules. Specification, weighted support helper, tests. | Prove the union-graph difference identity and implement exact nonnegative integral weights including zero deletion. Reproduce the two-vertex example and compare tiny weighted graphs against an independent direct energy oracle. |
| **NX16-B: incremental cache and updates** | NX16-A. New update module, invalidation index, `scripts/incremental_locality.py`. | For every edge insertion, deletion, and weight change in a small complete graph family, compare incremental updates to full recompilation and independent enumeration. Test sequential edits, reversal, stale patches, changed pinning, and cross-graph cache isolation. |
| **NX16-C: scaling and reusable receipts** | NX16-B; optional charges for boundary-aware follow-up. Retained receipts, benchmark, manuscript proposition. | Demonstrate fixed-budget local update work independent of total graph size on a bounded-degree family, after setup. Report support updates, polynomial operations, coefficient bits and wall time separately. Replay exact updated coefficients. |

## Resources, failure modes, and stopping

For maximum union degree `Delta`, affected connected supports of size at most `R` lie in radius at most `R-1` of `D`; a coarse count grows like \(\lvert D\rvert(c \Delta)^{R-1}\). This is a fixed-parameter statement, not a useful bound for large `R` or dense union graphs. Type reuse can help, but canonicalization costs and coefficient degrees remain visible. Count polynomial arithmetic operations separately from bit complexity. Formal exponentiation can touch every coefficient even when the log correction is local, so do not promise constant-time complete series output.

Stop at exact weighted local updates with a bounded-degree reuse benchmark. General vertex deletion, charge-aware boundary updates, continuous edge weights, arbitrary signed energies, and dynamic canonicalization can follow in distinct pushes. An impressive speed ratio is meaningful only when setup, identical output, memory, and arithmetic bit sizes are reported.


# NX17 - Low-rank physical fault transport

Status: proposed exact reuse layer for the existing source-derived discrete thermal model. This is a statement about its declared finite-dimensional stencil, not continuum thermal calibration or measured hardware. Removing one bond is a rank-one change in the discrete transition matrix. Its transfer functions can therefore share a nominal resolvent, giving an economical path toward many fault locations and continuous severities.

## Why this is a strong cross-program expansion

The present diagnostic pilot simulates six candidate matrices directly. Expanding to every bond and combinations quickly repeats almost identical work. The original PerfectPower and DynaComp themes suggest a better representation: preserve one nominal operator and describe each fault by a small exact correction, with original fault identity retained. This can produce useful symbolic severity formulas as well as faster batches. Whether it is actually faster depends on setup, polynomial degrees, requested horizons, coefficient growth, and candidate count; the packet requires those costs to be measured.

The old graph-height and thermal models must remain separate. The same plate adjacency may appear in both, but `L_G(x,q)` is a population over nonnegative integer heights, whereas the thermal pilot evolves an excess-temperature vector with input. This packet uses physical-time generating functions of a finite discrete model. Their rationality does not imply rationality of the positive-parameter graph-height series.

## Verified inherited crosswalk

| Existing source | Verified API or convention | Intended reuse |
|---|---|---|
| `src/singularity/thermal_diagnostics.py` | `AffineCandidate`, `.step`, `.observe`, `build_plate_candidates`, `simulate_protocol` | Exact sparse full-model oracle; candidate IDs are never deduplicated. |
| Same module | `default_protocols`, `protocol_pool`, `DiagnosticPool` | Existing readings, declared protocol costs, and uncertainty contract. This packet does not silently alter them. |
| Same module | `affine_operator_system` | Optional finite homogeneous lift; avoid a dense block lift for the full many-candidate population. |
| `applications/thermal_diagnostics/source_fixture.json` and `dynacomp_plate_source.py.txt` | Pinned source-derived stencil and its source provenance | Keep source-derived entries and transformed entries distinguishable. |
| `scripts/thermal_diagnostics.py`, `tests/test_thermal_diagnostics.py` | Independent neighbor-flux replay and source-fixture tests | Direct flux updates must remain independent of resolvent algebra. |
| DynaComp existing rational realizations | \(C(I-zA)^{-1}B\), minimal output recurrences | Reuse through a documented adapter after inspecting its actual source; do not claim a newly built minimal-realization engine here. |

The nominal pilot is `A0=I-kL-loss*I`, with `k=1/8`, `loss=1/100`, zero-centered initial excess temperature, and normalized heater/sensor vectors. A blocked bond removes its two positive off-diagonal entries and adds the old conductance back to both diagonal entries. This preserves row sum `1-loss`. The sign below follows from this exact convention.

## Derivation with the correct bond-removal sign

Let `b=e_u-e_v` for a bond `(u,v)`. Its unit Laplacian contribution is \(bb^{\mathsf T}\). Removing fraction `alpha in [0,1]` of its conductance gives

\[
L_f=L_0-\alpha bb^\top,\qquad
A_f=I-kL_f-\ell I=A_0+\delta bb^\top,\qquad \delta=k\alpha\ge0.
\]

The perturbation is positive rank one in `A`, although it removes a physical coupling. A minus sign here would model stronger conduction rather than blockage and would fail the source fixture.

Let \(R_0(z)=(I-zA_0)^(-1)\). Sherman--Morrison, interpreted as an identity of formal rational functions, yields

\[
R_f(z)=R_0(z)+\frac{z\delta R_0(z)b b^\top R_0(z)}{1-z\delta b^\top R_0(z)b}.
\]

For a heater column `B` and sensor row `C`, the impulse transfer correction is

\[
\Delta H(z)=\frac{z\delta\,[CR_0(z)b]\,[b^\top R_0(z)B]}{1-z\delta\,[b^\top R_0(z)b]}.
\]

Thus each bond requires two terminal-response factors and one scalar self-interaction factor. At a regular numerical value `z0`, the denominator guard must be checked. As a formal power series it has constant term one, so inversion and truncation at every finite horizon are well defined even when the rational function has poles elsewhere.

For several faults collect bond columns in `U` and severities in a diagonal `D`, so \(A_f=A_0+UDU^{\mathsf T}\). A form allowing zero severities is

\[
R_f=R_0+zR_0UD(I-zU^\top R_0UD)^{-1}U^\top R_0.
\]

The inner inverse is only as large as the number of selected bonds. The ordering of `D` and the Gram matrix matters; do not move factors through a noncommuting matrix. Determinant identities provide an independent denominator check. A small inverse does not imply small exact polynomials after expansion, and several faults can share linearly dependent bond columns without causing an invalid formula.

Input words are handled by convolution. With zero initial state and `x_{t+1}=Ax_t+Bu_t`,

\[
y_T=\sum_{t=0}^{T-1}CA^{T-1-t}B\,u_t.
\]

Nonzero initial states add \(CA^{\mathsf T} x_0\). Error propagation is still governed by each candidate's actual `|A|` dynamics or a valid alternative bound. A transfer formula for nominal readings does not automatically transport uncertainty certificates.

## Tiny exact worked example

Take two vertices, `k=1/4`, `loss=1/4`, one unit bond, heater \(B=(1,0)^{\mathsf T}\), and sensor `C=(0,1)`. Then

\[
A_0=\begin{pmatrix}1/2&1/4\\1/4&1/2\end{pmatrix},\qquad
A_f=\begin{pmatrix}3/4&0\\0&3/4\end{pmatrix}
=A_0+\tfrac14\begin{pmatrix}1&-1\\-1&1\end{pmatrix}.
\]

The first impulse readings are `CB=0` and `CA0B=1/4`, while `CAfB=0`. The nominal transfer is

\[
H_0(z)=\frac{z/4}{(1-3z/4)(1-z/4)}.
\]

For \(b=(1,-1)^{\mathsf T}\), \(b^{\mathsf T}R_0b=2/(1-z/4)\), `CR0b=-1/(1-z/4)`, and \(b^{\mathsf T}R_0B=1/(1-z/4)\). Substituting gives `Delta H=-H0`, exactly canceling the transfer after complete blockage. For a two-step constant unit input, direct simulation gives sensor output `1/4` nominal and zero blocked. This checks sign, time indexing, transfer coefficients, and cancellation without a large model.

## Proposed API and schemas

Add `src/singularity/fault_transport.py` with `BondFault(u, v, removed_conductance)`, `NominalTransferCache`, `bond_transfer`, `fault_set_transfer`, and `protocol_from_impulse`. The initial contract is exact rational data, stable source-derived matrices when claiming all-time conclusions, and finite-horizon formal operations otherwise. A cache records source dimension, nominal sparse matrix, heater/sensor channels, maximum retained horizon, and either rational function or truncated series representations. It must not deduplicate physically different faults just because current readings coincide.

The proposed schema `singularity.bond-fault-transport/1` records the nominal fixture identity, each oriented bond column, rational removed conductance, transfer factors, formal denominator, requested horizon, recovered coefficients, and direct oracle checks. Orientation of `b` is arbitrary because \(bb^{\mathsf T}\) is unchanged; changing its sign must leave outputs invariant. Record whether a denominator is represented exactly, truncated, factored, or sampled. Physical provenance and calibrated units remain a separate application responsibility.

## Three acceptance pushes

| Unit | Dependencies and artifacts | Required acceptance and independent check |
|---|---|---|
| **NX17-A: exact rank-one contract** | Existing thermal source fixture. New module, two-node fixture, specification and tests. | Prove and implement the sign-correct identity. Check full and partial blockage, zero severity, bond orientation reversal, row sums, symmetry and unchanged nominal heater/sensors. Compare coefficients with direct sparse powers and independent flux updates. |
| **NX17-B: multi-fault and protocol reuse** | NX17-A; NX03/NX04 integration optional. Add small-matrix Woodbury path and convolution receipt. | Compare every pair of a small bond catalogue and multiple rational severities with direct candidate construction. Verify arbitrary short input words and nonzero initial states. Reject severity exceeding the available conductance unless explicitly changing the model. |
| **NX17-C: full plate population benchmark** | NX17-B. Retained all-bond receipt and setup-inclusive benchmark. | Cover the 264 bonds of the 12-by-12 plate at a declared finite horizon. Compare all selected outputs to sparse simulation, retain every candidate identity, and report break-even query count, bits, memory and runtime. Test reflected indistinguishability on invariant sensors. |

## Resources, hazards, and stop point

Start with truncated series through horizons four to twenty, since dense rational inversion of a 144-state matrix may be slower than sparse direct simulation. Compile shared nominal response sequences before attempting symbolic determinants. The speed objective is a hypothesis to test, not an acceptance substitute for exactness. Generating all sensor/bond factors can still be large; cache only declared channels and horizons.

Do not infer stable switching from individually stable faults. A candidate with uncertain severity fixed throughout a protocol differs from severity changing adversarially at every step. A rational pole location does not by itself certify physical instability, since transfer cancellations may remove unobserved modes. Stop with exact shared transfer computation, independent direct comparisons, and a costed population benchmark. Continuum identification, hardware calibration, arbitrary nonlinear thermal faults, and a universal speed theorem remain outside scope.


# NX18 - Recovery conditioning and bit complexity

Status: proposed quantitative extension of exact interface recovery and experiment design. Existing theorems establish injectivity and exact reconstruction in declared regimes. This packet determines how much numerical precision, coefficient storage, and measurement accuracy those reconstructions require. Full rank is necessary for recovery; it says nothing by itself about affordable accuracy.

## Purpose and links to older work

The user previously emphasized that polynomial coefficients are coordinates, while integral polynomial size uses a Gram matrix rather than the ordinary coefficient dot product. That observation becomes important here. A change of basis can improve arithmetic or numerical behavior, but a norm-dependent margin must transform with its uncertainty and metric. It is incorrect to rescale a row by a large constant, claim a larger signal, and leave its sensor error unchanged.

The older PerfectPower exact-arithmetic work also distinguishes operation count from bit complexity. A quotient with fewer coordinates can contain enormous rational numbers. The existing `K_2,3` family already supplies explicit denominator growth. Bringing these threads together gives a meaningful comparison between finite-difference recovery, weighted-edge restoration, charge charts, and direct observations: delay, number of probes, bit count, and certified noise amplification should all be reported.

## Verified inherited crosswalk

| Existing source | Verified machinery | New quantitative task |
|---|---|---|
| `src/singularity/contexts.py` | `tau`, `finite_difference_budget`, `finite_difference_probe_set`, `recover_by_finite_differences` | Expose reconstruction matrices and exact error amplification without changing the proved recovery theorem. |
| Same module | `recover_symmetrized_kernel`, `weighted_probe`, `max_group_size` | Compare fixed-budget weighted restoration with delayed edge-free recovery. |
| `src/singularity/charges.py` | `chart_matrix`, `chart_transport`, `recover_from_chart`, `closure_operator`, `recover_sequence` | Exact triangular or chart inverse operators, including Laurent values at rational `q`. |
| `src/singularity/experiment_design.py` | `RationalMetric`, `monomial_gram`, `integral_inner_product`, `orthogonal_polynomial_basis`, `minimum_separation` | Preserve actual integral or rational metrics under basis changes. |
| `src/singularity/robust_search.py` | `margin`, `bounded_margin_search`, `exhaustive_margin_search` | Independent robust optimization comparison; current exact span pruning must not replace this search. |
| `tests/test_charges.py` | `K_2,3` denominators exactly \(2^(2j^{2})\) with odd numerator | Baseline bit-growth fixture, not a general bound for every graph. |

Read `docs/research/ROBUST_SEARCH.md`, `docs/research/ORDERED_CONTEXTS.md`, and existing compression notes. The all-budget path margin law supplies a useful check on saturation and unattained robustness suprema; it is a different result from cheapest exact distinction.

## Reconstruction and error propagation

At a fixed rational parameter, write the finite measurements as `y=Av` with full-column-rank `A`. An exact left inverse `R` satisfies `RA=I`. If each reading error obeys `|eta_i|<=epsilon_i`, then reconstructed coordinate error satisfies

\[
|\widehat v-v|\le |R|\epsilon
\]

componentwise. For a scalar target \(g^{\mathsf T} v\),

\[
|g^T(\widehat v-v)|\le\sum_i |(g^TR)_i|\epsilon_i.
\]

This target-specific bound can be far smaller than full-state error. For an overdetermined experiment matrix, different exact left inverses can have different box-noise amplification. Selecting a left inverse for one target is an optimization problem: find `w` with \(w^{\mathsf T} A=g^{\mathsf T}\) minimizing `sum_i epsilon_i |w_i|`. With rational coefficients this is a linear program, for which a primal/dual rational certificate can be checked. The first implementation can enumerate tiny active sets rather than add a compulsory dependency.

Within one collision circle, finite-difference reconstruction uses nodes `tau_i`; weighted-edge restoration uses nodes \(y_i=q^{(s_i-t_i)^{2}}\). The Vandermonde determinant is

\[
\det V=\prod_{i<j}(z_j-z_i),\qquad V_{ri}=z_i^r.
\]

Distinct nodes guarantee exact invertibility. Small node gaps can make inverse entries huge. For finite differences of order `j`, coefficients \((-1)^{j-c} \binom{j}{c}\) have total absolute value \(2^j\); under independent equal box bounds this preprocessing alone can amplify worst-case error by \(2^j\). Correlation may reduce that amplification, but must be represented explicitly. Additional inversion can amplify further.

The present delayed budget theorem gives a sufficient budget `R+m_R-1`, with \(m_R=R^{o(1)}\). It does not state that the delay is optimal or that the required precision is subpolynomial. A useful new theorem would bound amplification in terms of circle multiplicity and minimal `tau` gap over a declared `q` interval. Endpoints near zero or one require special treatment; taking an infimum over an open interval can produce zero separation.

## Tiny exact worked example

Let two unknown coordinates be measured by

\[
y_0=v_1+v_2,\qquad y_1=v_1+(1+\delta)v_2,
\qquad \delta>0.
\]

The determinant is `delta`, so the map is injective for every positive rational `delta`. Reconstruction is

\[
v_2=(y_1-y_0)/\delta,\qquad
v_1=((1+\delta)y_0-y_1)/\delta.
\]

If each reading error is bounded by `epsilon`, then the sharp independent-box coordinate bounds are `2 epsilon/delta` for `v2` and `(2+delta)epsilon/delta` for `v1`. At `delta=1/16`, these become `32 epsilon` and `33 epsilon`. Choosing `eta0=-epsilon,eta1=epsilon` attains the first bound, so this is not a loose floating-point estimate.

Now consider candidate difference `d=(0,1)`, rows `w1=(0,1)`, `w2=(0,100)`, and equal physical noise bound one. The second row is linearly dependent on the first, yet has discrepancy 100 rather than one. Exact span pruning may discard it for distinguishability, but doing so destroys the robust optimum if it is an available measurement at an allowed cost. Conversely if `w2` is merely postprocessing `100*w1`, its noise also becomes 100 and there is no improvement. The API must distinguish a new physical observation from rescaling an existing reading.

## Exact representation and proposed schema

Add `src/singularity/recovery_metrics.py` with `reconstruction_map`, `box_amplification`, `target_amplification`, `rational_size`, and `compare_recovery_designs`. A design records measurement rows, physical noise bounds, costs, preprocessing matrix, left inverse, target map, and completeness budget. It does not infer uncertainty from the magnitude of a row. Existing fixed-parameter recovery methods can optionally return their linear reconstruction data through a new wrapper rather than changing existing return types.

The schema `singularity.recovery-metrics/1` stores exact matrices `A,P,R`, identity checks, numerator and denominator bit lengths, nonzero counts, requested coordinate or target errors, and attained tiny-box witnesses. Distinguish raw measurement error from processed error. For a rational `a/b` in lowest terms, report numerator bits, denominator bits, and a declared encoding total; zeros and signs need a consistent convention. Summed cell bits are a reproducible representation metric, not the memory used by Python objects.

For metric changes `v'=Tv`, use transformed forward maps and target/noise contracts. In polynomial space a monomial Gram matrix `G` gives \(\lVert p\rVert^2=c^{\mathsf T}Gc\); an orthogonal basis diagonalizes that metric but does not alter the mathematical information. Basis optimization should therefore report both arithmetic size and the unchanged physical norm.

## Three acceptance pushes

| Unit | Dependencies and artifacts | Required acceptance and independent check |
|---|---|---|
| **NX18-A: exact amplification contract** | Existing exact matrix utilities and experiment metrics. New module, specification, tiny fixtures. | Prove left-inverse box bounds and implement exact propagation. Reproduce `32 epsilon` and `33 epsilon` above, independently checking all box vertices for tiny dimensions. Include dependent-row robust counterexample and rescaling-noise correction. |
| **NX18-B: recovery family comparison** | NX18-A; current contexts and charge charts. New script and retained finite receipts. | Compare delayed finite differences, weighted restoration, and charge reconstruction at identical declared targets. Report probe count, volume, measurement cost, amplification and coefficient bits. Compare reconstruction against direct graph kernels on tiny real blocks. |
| **NX18-C: certified target design** | NX18-B; optional NX08 stable-target work and NX09 precision selection. Manuscript theorem, optimization receipt. | For a bounded design menu, certify the least cost meeting a target error. On a compact rational parameter interval, prove any uniform bound using exact inequalities or certified root isolation. Verify tiny primal/dual left-inverse certificates independently. |

## Resource limits, failure modes, and stop point

Start with collision groups of size two or three and modest budgets. Explicit inverse matrices can be much denser than the original observation system. Reuse triangular solves for application and materialize full inverses only when needed for certificates. Record arithmetic operations, peak rational bit length, total encoded output, and runtime separately. A measured speedup from one family is not a universal complexity theorem.

Do not confuse singular values under an arbitrary coefficient norm with physical measurement stability. Do not normalize away noise. Do not apply exact span pruning to robust margins. Do not interpret finite parameter samples as interval conditioning bounds. Stop with exact amplification receipts, one useful target-specific optimization, and a clear tradeoff table. General optimal recovery under correlated nonpolyhedral uncertainty, all-budget sharp precision asymptotics, and a proof that delayed observation is optimal remain distinct research problems.


# NX19 - Integer-compatible observational quotients

## Mission and completion boundary

Build a lattice-aware companion to the existing rational observation quotient. The deliverable must preserve which quotient coordinates come from actual integer states, recover every original bounded state in a requested fibre, and preserve its multiplicity. It is not enough to preserve rational row rank. This is a proposed expansion: no `integer_quotient` API or Smith-form certificate in this packet should be described as already implemented. Complete the three pushes below in order, with a retained exact receipt, documentation, and release integration at each accepted checkpoint.

The distinction matters whenever coefficient vectors encode counts, integer charges, graph profiles, or exact populations. A rational elimination can compress observations perfectly while forgetting a congruence such as “the output must be even.” Rational coordinate changes can also destroy the original lexicographic order or turn one integer completion into several apparently fractional choices. The design must retain the original coordinate map and population semantics throughout.

## Grounded crosswalk and inherited ideas

Locally verified Singularity sources are `src/singularity/observability.py`, especially `OperatorSystem`, `observable_closure`, `ClosureCertificate`, `quotient_state`, `quotient_update`, and `replay_bundle`; and `src/singularity/population.py`, especially `HeightPopulation.count`, `contains`, `rank`, and `unrank`. The former computes exact rational row spaces and checks identities of the form $L=AB$, $BM_i=T_iB$. The latter counts original labeled tuples using shared completion states. It explicitly refuses populations lacking a finiteness certificate. Existing tests are `tests/test_observability.py` and `tests/test_population.py`.

The older PerfectPower bridge is chat-sourced unless independently checked in the receiving checkout: constructive Smith/Hermite presentations, saturated integer kernels, affine integer fibres, all-tie nearest settings, and completion-count rank/unrank. Reuse their mathematical contract rather than copying an unverified historical implementation. No PerfectPower global integral-point completeness or saturation result follows from this packet.

## Mathematical specification

Let $B\in\mathbb Q^{r\times D}$ be an observation-basis matrix from the existing engine. Choose a positive diagonal integer matrix $S$ clearing row denominators, and retain $A=SB\in\mathbb Z^{r\times D}$. Scaling an observation is a representation change, not a change to its physical noise or cost. A target quotient coordinate $y=Ax$, $x\in\mathbb Z^D$, belongs to the image lattice $A\mathbb Z^D$, which can be a proper sublattice of its rational span.

Compute a Smith certificate

\[
UAV=\operatorname{diag}(d_1,\ldots,d_s,0,\ldots),\qquad
U,V\text{ unimodular},\quad d_i>0,\quad d_i\mid d_{i+1}.
\]

For rectangular matrices the right side is rectangular, with $s=\operatorname{rank}_{\mathbb Q}A$. Membership is equivalent to

\[
(Uy)_i\equiv0\pmod{d_i}\ (i\le s),\qquad (Uy)_i=0\ (i>s).
\]

When membership holds, set $z_i=(Uy)_i/d_i$ for $i\le s$; coordinates $z_{s+1},\ldots,z_D$ are free integers, and $x=Vz$. This gives an integer particular solution plus an integer-kernel basis. The kernel $\ker(A)\cap\mathbb Z^D$ is saturated in $\mathbb Z^D$, but the image lattice need not be all integer points of its rational span. Keep those two assertions distinct.

If a transition $M\in\mathbb Z^{D\times D}$ preserves the ambient integer state lattice and $BM=TB$, it induces a well-defined map on realizable quotient states. The rational matrix $STS^{-1}$ may contain fractions; those fractions are harmless only because its domain is the certified image lattice, not arbitrary integer vectors. If $M$ itself is rational, do not assume integer preservation: require a declared invariant lattice or restrict to the explicitly checked population and transitions. Affine updates require a homogeneous coordinate and the additional constraint that it equals one.

## Tiny exact example

Take $A=(2\quad2)$ and binary states $x\in\{0,1\}^2$. The possible outputs are $0,2,4$, with multiplicities $1,2,1$. A Smith right transformation is

\[
V=\begin{pmatrix}1&-1\\0&1\end{pmatrix},\qquad AV=(2\quad0).
\]

An output $y=1$ is impossible even though a rational solution exists. At $y=2$, every integer solution is $x=(1-t,t)$; the binary bounds leave exactly $t=0,1$. Thus the two original states $(1,0)$, $(0,1)$ remain separate objects in one observational class. Swapping the coordinates preserves the class and its multiplicity. The output quotient alone must not silently collapse its population count from two to one.

## Proposed API and portable data

Propose `src/singularity/integer_quotients.py` with `integer_image_certificate(A)`, `verify_integer_image_certificate(cert)`, `image_contains(cert, y)`, `integer_fibre(cert, y)`, and `bounded_fibre_population(cert, y, constraints)`. These names are a design target, not a compatibility promise. Reuse exact integer/rational validators and reject booleans masquerading as integers. A portable `singularity.integer-image/1` bundle should include the original matrix, denominator-clearing factors when present, $U,V$, diagonal entries, rank, determinant witnesses or independently checkable unimodularity inverses, original coordinate order, and finite-domain contract.

Do not serialize a dense list of all solutions as the only fibre representation. Retain a particular solution and free integer basis, followed by original-coordinate constraints. Ranking must be defined in original tuple order, not arbitrary Smith-coordinate order, unless a different order is explicitly exposed as a separate API. A quotient-state identifier never substitutes for the count or list of original objects it represents.

## Three implementation pushes

| Push | Artifacts and work | Acceptance and independent oracle |
|---|---|---|
| NX19-A - Exact image-lattice certificates | Implement certificate checking, integer membership, kernel and particular solutions; document rectangular, rank-zero, and full-rank cases. Add `scripts/integer_quotients.py` and a retained receipt. | Verify every matrix identity directly with integer arithmetic. Exhaustively enumerate small bounded states for all tiny matrices in a declared bounded-entry corpus. Check determinant $\pm1$ or supplied integer inverses. Reject forged divisibility and nonunimodular transformations. |
| NX19-B - Original-object fibre populations | Add finite original-coordinate constraints, count/rank/unrank, and population pushforward with multiplicities. Integrate a bounded height-population example. | Compare every fibre and rank inverse with direct lexicographic enumeration. Retain the binary $A=(2,2)$ example and a nontrivial denominator-clearing example. Prove total pushforward mass equals original population size. |
| NX19-C - Operator-compatible lattice quotients | Attach invariant-lattice contracts to rational observation certificates and certify quotient updates on realizable integer coordinates. | Compare quotient evolution with original evolution for all states and short words in a finite corpus. Include a rational transition that fails lattice preservation and must be rejected. Keep rational closure tests passing without altering their existing meaning. |

## Resources, failure modes, and development notes

Smith computation can exhibit coefficient growth; record input dimensions, maximum entry bits, transformation-entry bits, and elapsed time. A resource refusal must be explicit and must never be reported as “not in the image.” Bounding the output does not necessarily bound the original fibre when the kernel is nonzero. Require an existing finiteness proof, explicit original bounds, or a separately justified coercive objective before counting.

A rational nullspace basis need not generate the complete integer kernel. Multiplying its vectors independently by denominators can leave a sublattice of finite index and omit solutions. Similarly, dividing every observation by its gcd without recording the image lattice loses physical and arithmetic semantics. Include both as regression counterexamples. Original graph labels and original population weights remain part of identity; no automorphism quotient is licensed by this design.

For an explicit kernel regression, take $A=(2,1,1)$. Rational elimination can return $(-1/2,1,0)$ and $(-1/2,0,1)$. Clearing denominators independently gives $(-1,2,0)$ and $(-1,0,2)$, whose integer span misses the valid integer-kernel vector $(-1,1,1)$. The missing vector is half their sum. This small case tests saturation directly and prevents a superficially plausible “integer kernel” implementation from silently omitting original solutions.

The independent verifier should be substantially smaller than the Smith constructor. Its job is to multiply matrices, check diagonal divisibility and inverse identities, and validate the finite-domain contract. Formalization can target these certificate implications later; do not claim that the Smith algorithm, population recursion, or every external arithmetic object has become Lean-verified merely because a small identity checker is proved.

## Handoff finish criterion

Call NX19 complete only when an outsider can take an exact observation quotient, test integer realizability, reconstruct a finite original fibre, and replay transitions without losing divisibility or multiplicity. Publish a human explanation with the binary example, a schema example, resource limits, and a clear statement that minimal rational dimension and faithful integer representation are different optimization goals.

For cross-track integration, expose integer membership as a predicate rather than forcing every consumer to adopt Smith coordinates. NX20 can attach it to seed representations, NX23 can sum original weights over its fibres, and NX15 can use it as a necessary graph-realizability filter. It is not a sufficient graph-realizability criterion: satisfying all congruences of a linear observation map does not manufacture an adjacency matrix or enforce nonlinear slice identities. This boundary should appear in both API documentation and the retained example index.


# NX20 - Pell and residue experiment automata

## Mission and scope

Connect exact quadratic-unit dynamics with the existing finite experiment engine. The first target is a declared finite population of seed classes modulo a declared modulus, together with costed residue observations and explicitly legal arithmetic actions. Compute future equivalence, cheapest distinguishing experiments, and remote transitions while preserving the connection to each original seed. This packet does not assert complete seed enumeration for an arbitrary Pell equation and does not convert a finite modular calculation into a global integer-solution theorem.

The useful conceptual move is to view a residue measurement as an experiment on an arithmetic dynamical system. Different measurements can reveal different coordinates of an orbit. A finite residue quotient permits exhaustive semantic checks and exact closure, while matrix powering can evaluate very distant indices. The arithmetic object remains the original unit orbit; a residue class is a limited observation of it.

## Existing sources and historical bridge

Locally verified implementation anchors are `src/singularity/observability.py` for costed word semantics, closure, quotient updates, and replay; `src/singularity/conductor.py` for exact cyclotomic elements and remote coefficient calculations; `src/singularity/congruence.py` for congruence-filter conventions; and `src/singularity/population.py` for original-object populations. These modules do not already provide a Pell seed-completeness engine. Read their public contracts before proposing adapters.

The PerfectPower bridge is chat-sourced: earlier work reported exact Pell recurrences, modular orbit filters, distant-index evaluation, and preservation of original coordinates. Recover and inspect the relevant PerfectPower source if available; otherwise implement a narrow independent adapter with explicit assumptions. The PerfectJet bridge is also chat-sourced: finite partial actions, noncommuting arithmetic experiments, and all-future behavioral classes. Those ideas motivate the experiment semantics, but the present module must be tested against actual integer matrices and residue transitions.

## Mathematical model

Fix a nonsquare integer $D>0$ and a certified unit $a+b\sqrt D$ of norm one, so $a^2-Db^2=1$. With column coordinates $v=(x,y)^\top$, multiplication is

\[
U=\begin{pmatrix}a&Db\\ b&a\end{pmatrix},\qquad
U\binom{x}{y}=\binom{ax+Dby}{bx+ay},\qquad
\det U=1.
\]

It preserves $x^2-Dy^2=N$. Modulo $m\ge1$, $U$ is invertible and acts on the finite set $(\mathbb Z/m\mathbb Z)^2$. A chosen invariant subset, such as all residues satisfying a norm congruence, can be enumerated exactly. It is not necessarily the reduction of the chosen global integral seed population; retain the actual image of the seeds when that is the intended population.

For a finite state set $S$, encode transition $f_i:S\to S$ by a column-state matrix $M_i e_s=e_{f_i(s)}$. Residue observations can be numeric rows or indicator rows for every output symbol. Indicator encoding preserves exact output equality without confusing addition in a finite field with rational linear algebra. With one-hot states, the existing rational closure can determine finite-state observational equivalence. A state-space quotient is behavioral, not a statement that two integer Pell orbits are the same orbit.

Chronological word semantics must match the existing engine: $(i_1,\ldots,i_k)$ applies $i_1$ first, and a row observation evaluates $L_jM_{i_k}\cdots M_{i_1}e_s$. The current row expansion prepends letters. Do not reverse witness words when adapting a finite automaton.

## Tiny exact example

For $D=2$, use $a=3,b=2$: $U=\begin{pmatrix}3&4\\2&3\end{pmatrix}$. Starting from $(1,0)$, the first integer states are $(1,0),(3,2),(17,12),(99,70)$, each satisfying $x^2-2y^2=1$. Modulo five, the cycle is

\[
(1,0)\to(3,2)\to(2,2)\to(4,0)\to(2,3)\to(3,3)\to(1,0).
\]

Verify that list independently before retaining it; it is a testable proposed fixture, not a source citation. Generate the cycle from arithmetic and check every edge with a separate direct oracle rather than treating the handoff text as computational evidence.

For a simpler accepted local assertion, the first two reductions are $(1,0)\to(3,2)\to(2,2)$. Two different seeds $(1,0)$ and $(4,0)$ have equal $y\bmod5$ initially. After one unit action their $y$-values are $2$ and $3$, so the single residue sensor distinguishes them at cost one if the action costs one. Both are legal states in a suitable declared modular norm class, although they need not belong to the same positive global seed convention.

## Commutation and intervention restrictions

Multiplication by units in one quadratic field commutes: $U_1U_2=U_2U_1$. Therefore a language consisting solely of such multiplications does not acquire order sensitivity by adding more units. If an order-sensitive demonstration is desired, add a separately justified operation, such as conjugation $J=\operatorname{diag}(1,-1)$, with $JUJ=U^{-1}$. On an appropriate signed state population this is a legal norm-preserving action. Its effect on positivity and chosen seed conventions must be checked.

An arbitrary reset, translation, or projection can leave the norm surface or erase the initial target. Declare it as a different action type with guards and semantics; do not call it a Pell symmetry. For partial actions, either use the existing SOE framework after inspecting its implementation or encode undefinedness as a distinguished observable state. Never silently totalize a forbidden operation as an identity transition.

## Proposed API and data contract

Propose `src/singularity/arithmetic_automata.py` with `QuadraticUnit(D,a,b)`, `ResidueOrbitSystem(modulus,seeds,actions,observations)`, `remote_residue(seed,index)`, and `compile_operator_system()`. An `arithmetic-orbit/1` receipt records exact $D,N,m,U$, seeds with stable IDs, their provenance and scope, action costs, observation alphabets, all transition tables, legal-state checks, orbit/cycle data, and links back to the original integer-coordinate convention. Negative indices require an explicit invertible-action contract; the default remote index is nonnegative.

## Three implementation pushes

| Push | Artifacts and work | Acceptance and independent oracle |
|---|---|---|
| NX20-A - Arithmetic residue adapter | Implement certified norm-one units, exact residue transitions, finite seed populations, cycle discovery, and strict serialization. | Check norm preservation in integers; compare repeated transitions with direct quadratic multiplication and independent matrix powering for bounded indices. Exercise $m=1$, composite moduli, negative residues, and malformed units. |
| NX20-B - Costed observation closure | Compile residue symbols to indicator observations and expose future equivalence and cheapest witnesses through existing closure APIs. | Exhaust all short words in a small finite system; compare behavioral partitions with a direct finite-machine refinement oracle. Retain equal-current-output states separated after one action and a genuinely forever-equivalent pair. |
| NX20-C - Remote indices and restricted noncommuting language | Add cycle/powering cross-checks, multiple sensor costs, and an optional conjugation action with explicit signed-state semantics. | Check indices with thousands of decimal digits modulo a retained cycle using independent modular exponentiation. Demonstrate commuting unit actions and, separately, a verified conjugation order witness. Package original-seed maps and exact costs. |

## Resources and counterexamples

A full residue state space has $m^2$ elements; a one-hot dense operator representation has quadratic matrix storage in that size. Prefer sparse transitions or orbit restrictions and declare limits before allocation. Distinct global seeds can collide modulo every selected modulus in a finite test panel; no global distinction follows without a proved bound or complete reconstruction theorem. Conversely, a modular distinction is a valid integer distinction for states known to reduce to those residues.

Record bit growth separately from arithmetic operation counts. Computing an enormous integer Pell coordinate is expensive even when its index can be powered in logarithmically many matrix multiplications; a residue at the same index may be cheap. Do not advertise distant exact coordinates when only residues were computed. Retain a regression where norm-congruence solutions include residues not licensed by the chosen global seed population.

## Finish criterion

Completion means a user can declare seeds, modulus, legal arithmetic operations, sensors, and costs, then obtain exact behavioral classes and replayable distinguishing experiments with original-coordinate provenance. The output must state that completeness concerns this finite experiment language and seed population. Any claim about all integral Pell solutions requires a separate mathematical seed-completeness theorem.

Keep two projections in the result: original seed ID to modular state, and modular state to behavioral class. Different seeds may already coincide at the first projection; others may coincide only after the chosen observations forget a coordinate. Counting the final classes cannot replace counting original seeds or histories. If a later PerfectPower adapter carries several branches of the same global equation, its provenance must say whether branches overlap and how duplicate original solutions are removed.


# NX21 - Symmetry-adapted experiment channels

## Mission and completion boundary

Build an exact symmetry layer that explains inaccessible observation channels and proposes specific sensors or actions that reach them. The layer should identify what a symmetry forces to be invisible, use that structure to reduce experiment calculations, and verify that a proposed repair actually distinguishes the required candidates. Merely breaking a symmetry is not a completeness proof: different obstructions can remain after the symmetry disappears.

This packet proposes new APIs and integration. It does not claim a universal symmetry decomposition of every Singularity graph interface or that a Weil commutant dimension formula applies to a thermal plate. Deliver a small exact reflection case first, then finite-group channels and costed repair. Keep the original operator, sensor, target, noise, and cost semantics visible through every basis change.

## Local source crosswalk and historical provenance

Locally inspected anchors are `src/singularity/observability.py`, `src/singularity/conductor.py`, and `src/singularity/periodic.py`. The first supplies rational state operators, output rows, exact closure, and future-equivalence certificates. The latter two supply integer cyclotomic-ring arithmetic and periodic graph phases, but not a general rational-cyclotomic representation package. Additional integration sources to inspect are `src/singularity/thermal_diagnostics.py`, `src/singularity/contexts.py`, and `src/singularity/terminal_moves.py`.

The older PerfectPower commutant and Fourier/Heisenberg work is chat-sourced unless its repository source is checked. It motivates exact channel decomposition and phase-consistent orbit sums. Its odd/even formulas concern a specific representation and must not be transferred to a new action without proof. Likewise, the reported Coxeter-Raghava correspondence distinguishes 384 primitive phases, eight eigenphases with multiplicity, 264 refinement branches, and 240 E8 roots; these are different populations. The useful inherited principle is to derive channels from the actual representation, not to identify unrelated objects by suggestive counts.

The PerfectJet bridge is also chat-sourced: observability depends on the permitted experiment language, and adding an asymmetric or noncommuting action can refine behavioral classes. Existing Singularity closure is the local implementation to reuse.

## Mathematical specification

Let a finite group $\Gamma$ act on a finite-dimensional state space through an explicitly checked representation $\rho(\gamma)$. If every allowed state operator satisfies

\[
M_i\rho(\gamma)=\rho(\gamma)M_i,
\]

then the operators preserve the representation's isotypic components. Over a splitting field of characteristic zero, central idempotents are

\[
P_\lambda=\frac{d_\lambda}{|\Gamma|}
\sum_{\gamma\in\Gamma}\chi_\lambda(\gamma^{-1})\rho(\gamma).
\]

Check $P_\lambda^2=P_\lambda$, orthogonality, completeness, and commutation with every declared $M_i$. Character values and division by $|\Gamma|$ require exact arithmetic in an appropriate field. Existing CyclotomicRing stores integer quotient elements; it does not by itself represent arbitrary rational cyclotomic coefficients. Either introduce that coefficient layer deliberately or begin with rational projectors and numerator identities.

For a channel $V_\lambda=\operatorname{im}P_\lambda$, a symmetric sensor may satisfy $LP_\lambda=0$. No allowed sequence reveals that channel, since

\[
LM_{i_k}\cdots M_{i_1}P_\lambda
=LP_\lambda M_{i_k}\cdots M_{i_1}=0.
\]

This is a complete all-word blindness proof for that channel under the commutation assumptions. The reachable channel from a fixed input or initial population is a separate question. Compute reachability and observability together if claiming that a hidden channel matters for actual candidates.

A second theorem covers related candidate models rather than a single commuting model. Suppose $A_b=PA_aP^{-1}$, the same input satisfies $PB=B$, candidate initial states obey $x_{0,b}=Px_{0,a}$, and a sensor satisfies $CP=C$. Every shared input history produces equal outputs. This applies to reflection-related faults even when the faulted matrix itself does not commute with reflection. Do not confuse this conjugate-model theorem with the single-system isotypic theorem.

## Tiny exact example

Let

\[
P=\begin{pmatrix}0&1\\1&0\end{pmatrix},\quad
A=\begin{pmatrix}1/2&1/4\\1/4&1/2\end{pmatrix},\quad
P_\pm=\frac{I\pm P}{2}.
\]

The symmetric and antisymmetric channels have eigenvalues $3/4$ and $1/4$. With $C_+=(1,1)/2$, initial states $e_1,e_2$ are indistinguishable at every time: their difference lies in the minus channel and $C_+P_-=0$. A new sensor $C_-=(1,-1)$ gives outputs $1,-1$ at time zero, and the difference at time $t$ is $2(1/4)^t$.

The example has two lessons. First, a structural blindness certificate can be exact at all times. Second, an asymmetric sensor can reveal the channel, but waiting makes this particular distinction weaker. Assigning sensor cost and error therefore changes which repair is useful. With absolute output error $\epsilon$ per model, time $t$ robustly separates only when $2(1/4)^t>2\epsilon$.

## Proposed API and certificate structure

Propose `src/singularity/symmetry_channels.py` with FiniteRepresentation, verify_representation, reflection_channels, verify_channel_decomposition, channel_observability, and minimum_channel_repair. The first implementation may support rational matrices and involutions only. Make broader character-field support an explicit subsequent capability rather than silently using floating eigendecompositions.

A proposed singularity.symmetry-channels/1 receipt records group elements or a checked presentation, exact representation matrices, coefficient field, projectors, operator-commutation identities, sensor restrictions, reachable-channel witnesses, target restrictions, and candidate IDs. A repair receipt adds the allowed sensor/action catalogue, installation costs, experiment costs, error contract, resulting observation certificate, and optimality scope. Store the actual new experiment word; a statement that some channel became nonzero is not sufficient evidence for the requested target.

Do not transport an uncertainty ball through a nonorthogonal basis as if it remained the same ball. Transform its actual set or Gram matrix. Similarly, an abstract sensor row may have negative coefficients even when physically available sensors only measure local averages. Implementable contrasts must retain their constituent readings, error correlation, and aggregate cost.

## Three implementation pushes

| Push | Artifacts and work | Acceptance and independent oracle |
|---|---|---|
| NX21-A - Rational reflection channels | Implement exact involution projectors, commutation/conjugacy checks, channel sensor restrictions, and strict receipts. Add the two-state example. | Verify all matrix identities independently. Compare all times through a declared horizon with direct simulation, then retain the symbolic all-time proof hypotheses. Reject a perturbed matrix that no longer commutes. |
| NX21-B - Finite-group decompositions | Add a small rational representation corpus and, only when necessary, a documented rational-cyclotomic coefficient field. Compile per-channel closure. | Compare full closure rank with the sum of independently constructed channel ranks under verified decomposition assumptions. Test repeated irreducible multiplicities and real versus complex field conventions. |
| NX21-C - Costed symmetry repair | Integrate the thermal reflection pair and a finite catalogue of local sensors or asymmetric inputs with robust panel selection. | Reproduce the original conjugate-model blindness. Find the cheapest certified target-separating repair within the catalogue. Independently enumerate all smaller installations and declared experiments. Retain a symmetry-breaking repair that still fails, as a counterexample to sufficiency. |

## Resources, counterexamples, and precise claims

Group enumeration can dominate computation. Declare maximum group order, matrix dimension, coefficient-field degree, and bit sizes. If only generator relations are checked, explain why those relations establish the intended representation; an incomplete presentation can admit unintended groups. A numerical eigenspace is not an exact projector certificate.

A symmetry of the unlabeled graph need not preserve terminal labels, sensors, edge weights, or target identity. The action relevant to the theorem must preserve the full experiment contract. Conversely, quotienting states by a visually obvious symmetry can destroy a target that distinguishes its orbit members. The target must be invariant under any identification being used.

An action that fails to commute may couple channels, but that alone neither proves full observability nor guarantees a useful separation margin. Run actual closure and candidate tests afterward. For the thermal family, distinguish a sensor that breaks left/right reflection from one that robustly separates every competing fault and severity.

## Finish criterion

NX21 is complete when it produces exact blindness explanations, a verified channel decomposition where applicable, and a costed repair whose observations are replayable on the original models. The human-facing explanation should say which physical or arithmetic direction was invisible, why no old experiment could reveal it, and which new capability makes the requested distinction possible.


# NX22 - Multi-frequency arithmetic probing

## Mission and scope

Use several exact root-of-unity evaluations to reconstruct finite-volume energy histograms that a single periodic specialization can collapse. This is a finite coefficient reconstruction theorem with an explicit degree bound. It does not say that finitely many phase observations determine an unrestricted positive-parameter graph-height series at every volume, and it does not supply an experiment implementation for complex phase weights in a physical thermal system.

The central design is useful because Singularity already has exact phase arithmetic, periodic residue models, and independent height enumeration. We can make the relationship between phase observations and polynomial coefficients constructive, then compare complete Fourier sampling with sparse or adaptive probing under separately stated assumptions.

## Existing implementation and historical bridge

Locally verified sources are `src/singularity/conductor.py`, including CyclotomicRing, cyclotomic_polynomial, residue_numerator, and remote_coefficient; `src/singularity/periodic.py`, including PeriodicModel, direct_coefficients, residue_numerator, and series_from_numerator; and `tests/test_periodic.py`. The periodic tests enumerate 524 declared small models with signed phase exponents and compare direct coefficients with residue splitting. Existing periodic rationality and palindromic numerator cutoffs are genuine local contracts; do not rebrand them as new.

Additional local sources to inspect are `src/singularity/heights.py`, `src/singularity/polynomials.py`, and `src/singularity/edge_factors.py`, which provide independent coefficient and marked-edge routes. The older PerfectPower Fourier/commutant work and PerfectJet polynomial-as-vector observations are chat-sourced design bridges unless their code is independently inspected. They motivate choosing an exact phase basis and preserving coefficient semantics.

## Finite-volume reconstruction theorem

For an unweighted simple graph $G$ of maximum degree $\Delta$, write

\[
P_r(q)=\sum_{\substack{h\in\mathbb N^{V(G)}\\ |h|=r}}q^{Q_G(h)}
=\sum_{e=0}^{E_r}a_{r,e}q^e,\qquad
Q_G(h)=\sum_{uv\in E}(h_u-h_v)^2.
\]

Every coefficient $a_{r,e}$ is a nonnegative integer counting original labeled profiles. Since heights are nonnegative,

\[
Q_G(h)=\sum_v d_vh_v^2-2\sum_{uv\in E}h_uh_v
\le\Delta\sum_vh_v^2\le\Delta r^2.
\]

Thus one safe uniform bound through volume $R$ is $E_{\max}=\Delta R^2$. Choose an integer $M>E_{\max}$ and a primitive $M$th root $\zeta$. Then

\[
a_{r,e}=\frac1M\sum_{k=0}^{M-1}P_r(\zeta^k)\zeta^{-ke},
\qquad 0\le e\le E_{\max}.
\]

Orthogonality proves the result: the inner sum over $k$ is $M$ when two exponents agree modulo $M$, and zero otherwise; the strict degree bound prevents distinct exponents from sharing a residue. Use one consistent field containing $\zeta$ for all evaluations. If $M$ is composite, the list includes nonprimitive phases; collecting only primitive conjugates does not automatically provide the full discrete transform.

For nonnegative weighted edges replace $\Delta$ by the maximum weighted degree, with an integer exponent scale fixed in advance. Signed weights give a Laurent polynomial: record lower and upper exponent bounds, shift by the lower bound, and require $M$ greater than the exponent-range width. Arbitrary real exponents are outside this exact cyclotomic theorem.

## Tiny exact example and aliasing counterexample

For a single edge on two labeled vertices, volume two has profiles $(0,2),(1,1),(2,0)$ with energies $4,0,4$, so

\[
P_2(q)=1+2q^4.
\]

Here $\Delta=1$, and $M=5$ is sufficient. Exact evaluations at $1,\zeta,\zeta^2,\zeta^3,\zeta^4$ reconstruct histogram $(1,0,0,0,2)$. With $M=4$, the energy-four term aliases to residue zero and every phase evaluation equals three. The invalid reconstruction would be the constant polynomial three. This demonstrates why $M>\Delta R^2$ is a sufficient strict condition, rather than $M\ge\Delta R^2$.

At $q=1$, $P_r(1)=\binom{r+n-1}{n-1}$, independent of graph edges. That is a useful checksum and an equally useful warning: one phase observation can discard nearly all graph structure. At $M=2$, existing periodic calculations already exhibit nonisomorphic models with equal entire specialized series. Several frequencies repair finite-volume aliasing only when their information and degree assumptions justify reconstruction.

## Proposed API and exact arithmetic contract

Propose `src/singularity/phase_probes.py` with energy_degree_bound(graph,R), phase_table(graph,R,M), recover_energy_histograms(table,bound), and verify_phase_reconstruction(bundle). An optional phase_subset_identification should distinguish finite-candidate identification from full unrestricted histogram recovery. A small phase subset can identify a declared population even when it cannot recover every possible polynomial of the degree bound.

The proposed singularity.phase-reconstruction/1 schema contains original graph/weight metadata or a source digest, volume bound, exponent interval, phase order, exact cyclotomic polynomial, every sample's exponent label, transform convention, recovered integer histograms, and degree-bound evidence. Include the $k=0$ evaluation explicitly. Reject duplicate or missing phase indices in a full-transform certificate.

The inverse transform formally divides by $M$. An implementation can sum in the exact cyclotomic ring, verify that the result reduces to an integer multiple of the ring unit, and divide that integer exactly. Do not replace exact division by a floating tolerance. If a rational-cyclotomic layer is introduced for other packets, its field embedding and canonical encoding must remain compatible.

## Three implementation pushes

| Push | Artifacts and work | Acceptance and independent oracle |
|---|---|---|
| NX22-A - Exact complete phase transforms | Implement the safe degree bound, phase tables, inverse reconstruction, and strict certificate replay. | Check every coefficient against direct height-profile enumeration on a declared small graph census. Retain the single-edge $R=2,M=5$ success and $M=4$ aliasing failure. Verify total histogram mass and nonnegativity. |
| NX22-B - Compiler and periodic integration | Allow phase samples from existing direct, connected-support, or residue routes when their assumptions apply. Store the route and source contract. | Compare at least two structurally independent sample routes, then compare reconstructed histograms with symbolic coefficient enumeration. Include composite $M$, disconnected graphs, isolated vertices, and nonprimitive phases. |
| NX22-C - Sparse and candidate-specific probe design | Add a finite-candidate costed phase selector and an explicitly conditional sparse-histogram experiment. | Independently exhaust all smaller phase panels in a tiny declared candidate population. State whether a certificate identifies candidates or reconstructs unrestricted histograms. Do not assert sparse uniqueness without a separate theorem and checked support assumptions. |

## Complexity, interpretation, and failure cases

The complete method uses $M$ evaluations, where the safe order grows quadratically with $R$. A naive residue box costs $M^n$ and is unsuitable for large graphs; direct finite-volume enumeration costs $\binom{R+n}{n}$. Record which algorithm actually ran, field degree, coefficient bits, profiles or support types visited, and peak storage. Exact Fourier arithmetic does not remove these costs.

The same coefficient polynomial can be reconstructed by sufficiently many distinct rational parameter evaluations using ordinary interpolation, but conditioning and denominator growth differ. Compare that alternative rather than assuming phase probing is always superior. Positive-parameter measurements have a different operational interpretation from formal complex phases.

Any claimed reconstruction with an underestimated degree bound can be exactly wrong while every internal arithmetic operation is correct. Include a forged-bound rejection test that independently checks the supplied graph bound, and a schema mode where externally supplied bounds are clearly assumptions rather than verified facts.

## Finish criterion

Completion requires a finite-volume reconstruction tool with exact histograms, multiplicities, declared degree bounds, independent sample oracles, and explicit aliasing examples. The release explanation must say precisely what the additional frequencies recover and must preserve the distinction between periodic full-series equality and finite-volume reconstruction of the original energy polynomial.

## Integration experiment and publication table

Retain a single comparison table with graph ID, volume, proven exponent bound, chosen phase order, cyclotomic field degree, number of phase samples, direct histogram entries, reconstructed entries, and total original profile mass. Include two graphs that coincide at one phase but separate as energy polynomials. This demonstrates recovered information without claiming an improvement that was already visible to a direct coefficient oracle.

The runtime comparison should include direct polynomial enumeration as well as phase reconstruction; otherwise a large transform cost can be hidden behind an attractive algebraic statement. An optional compressed-sensing or sparse-interpolation branch remains research unless support uniqueness and alias avoidance are proved. Its report should expose failed reconstructions as well as successes, and should never mark full NX22-C complete merely because a heuristic found a small panel on a few examples.


# NX23 - Population geometry with preserved multiplicities

## Mission and completion boundary

Build an exact bridge between compressed finite populations, exponential tilting, target-specific statistical decisions, and costed experiment selection. Every compressed state must retain the total weight of the original objects it represents. The first deliverable should work with finite rational weights and finite rational observation channels, so counts, posterior risks, and acceptance results can be checked exactly. Entropy and continuous likelihoods are optional later layers with explicit approximation contracts.

The conceptual gain is that one population representation can support several questions without changing its original objects: worst-case separation, probability of a target, expected identification error, and sensitivity to a declared weighting. These questions are not interchangeable. A uniform count gives a probability only when a uniform prior over original objects is actually intended, and a chosen exponential tilt is a model assumption rather than an empirical discovery.

## Existing sources and historical bridge

Locally verified `src/singularity/population.py` implements HeightPopulation over original labeled height tuples. Its completion recursion shares future problems but does not identify original tuples; count returns an arbitrary-precision integer and rank/unrank retain lexicographic identity. The constructor requires certified finiteness from height, volume, span, or connected min-zero energy constraints. Reuse those contracts rather than adding an implicit sampling cutoff.

Other local integration sources to inspect are `src/singularity/panels.py`, `src/singularity/experiment_design.py`, `src/singularity/robust_search.py`, and `src/singularity/thermal_diagnostics.py`. Their worst-case or robust claims must remain unchanged unless a new explicitly named probabilistic mode is requested.

The historical bridge is chat-sourced PerfectPower completion planning and PerfectJet history populations: many original histories can share a sufficient feature vector while retaining their multiplicities. Earlier reported compression of millions of walks to a few dozen type-count vectors motivates the API, but reproduce an actual receiving-repository example before using any historical benchmark as evidence. This packet does not assert predictive success for NFL data or an empirically calibrated thermal fault prior.

## Mathematical specification

Let a certified finite original population be $\Omega$, with nonnegative rational weights $w_\omega$, not all zero. Let $f:\Omega\to\mathbb Z^d$ be an explicitly defined statistic. The compressed mass table is

\[
m_z=\sum_{\omega:f(\omega)=z}w_\omega.
\]

For positive parameters $t_i$, define

\[
Z(t)=\sum_zm_z\prod_i t_i^{z_i},\qquad
p_t(\omega)=\frac{w_\omega\prod_i t_i^{f_i(\omega)}}{Z(t)}.
\]

Nonnegative statistics give a polynomial; bounded signed statistics give a Laurent polynomial. At positive rational $t_i$, all masses and expectations of rational targets are exact rationals. Writing $t_i=e^{u_i}$ gives the familiar differential identities

\[
\partial_{u_i}\log Z=\mathbb E_t[f_i],\qquad
\partial_{u_i}\partial_{u_j}\log Z=\operatorname{Cov}_t(f_i,f_j).
\]

These identities can be evaluated with polynomial derivatives without approximating logarithms. The covariance is positive semidefinite. Its null directions are precisely linear combinations of $f$ that are constant on the positive-weight support. This describes the geometry of the declared population weighting; it is not automatically an observation-rank theorem or a physical Fisher-information claim.

If a target $T(\omega)$ is not determined by $f(\omega)$, retaining only $m_z$ is insufficient for target inference. Store the joint table $m_{z,\tau}$ for a finite target, or conditional sufficient summaries justified for the intended loss. If future experiments depend on more than $f$, enrich the compressed key until their likelihoods and legal transitions are well defined. “Sufficient for counting” does not imply “sufficient for every future experiment.”

## Tiny exact example

Let $\Omega=\{0,1\}^2$, unit original weights, and $f(x)=x_1+x_2$. The three feature values $0,1,2$ have masses $1,2,1$, so

\[
Z(t)=1+2t+t^2=(1+t)^2.
\]

At $t=2$, the feature probabilities are $(1,4,4)/9$, the expectation is $4/3$, and variance is $4/9$. Treating the three compressed classes as equally weighted would instead give $Z_{\rm wrong}=1+t+t^2$ and expectation $10/7$ at $t=2$. At $t=1$, the event $f=1$ has probability $1/2$, not $1/3$.

The example also distinguishes feature and target sufficiency. If $T(x)=x_1$, the class $f=1$ contains targets zero and one. A feature-only table loses that conditional ambiguity; a joint feature/target table preserves it. An observation of $x_2$ can update the target probability differently within that class, so its observation channel must also be represented.

## Exact decision layer

For finite observation alphabet $\mathcal Y_e$, declare rational likelihoods $K_e(y\mid\omega)$ with nonnegative entries and $\sum_yK_e(y\mid\omega)=1$. A prior $p$ produces posterior mass by Bayes' rule whenever the observation has positive probability. Zero-probability observations need an explicit model-rejection path rather than division by zero.

For finite target labels and zero-one loss, the optimal expected error after experiment $e$ is

\[
R(e)=1-\sum_{y\in\mathcal Y_e}\max_\tau
\sum_{\omega:T(\omega)=\tau}p(\omega)K_e(y\mid\omega).
\]

This is an exact rational objective. It avoids introducing floating entropy into the first optimizer. Costs can constrain $e$ or be combined through an explicitly declared tradeoff coefficient; do not invent units or a value of target error. A bounded-error consistency set supplies a robust decision problem, not a unique likelihood. Keep robust and Bayesian modes separately named.

## Proposed API and schema

Propose `src/singularity/population_geometry.py` with WeightedPopulation, pushforward_mass, joint_target_mass, tilted_moments, FiniteObservationChannel, posterior_target, and minimum_expected_target_risk. Preserve stable original IDs and an original-object rank/unrank adapter. A proposed singularity.population-geometry/1 bundle records the finiteness certificate, original weight definition, compression key, joint target table, observation-channel semantics, parameter domain, exact normalization, and cost/loss units.

Portable receipts should include checksums of exact rational tables and enough information for a direct original-object replay on the retained small instance. Do not store only decimal probabilities or unnamed “information scores.” When parameters are symbolic, record the polynomial or Laurent exponent convention and common denominators.

## Three implementation pushes

| Push | Artifacts and work | Acceptance and independent oracle |
|---|---|---|
| NX23-A - Exact weighted pushforwards | Implement finite rational mass tables, target-enriched compression, tilting, means, and covariance. | Compare every value with direct summation over original objects. Retain the binary example, zero-weight support, signed features, and a compressed class containing multiple target labels. Verify mass conservation. |
| NX23-B - Finite-channel target decisions | Add rational observation channels, posterior target distributions, and exact zero-one Bayes risk. | Independently enumerate observations and targets to check every posterior and risk. Reject invalid likelihood rows, zero total mass, unsupported observations, and compressed keys that cannot define the proposed channel. |
| NX23-C - Costed population-aware experiment design | Integrate a declared small fault population and an explicit prior, comparing population-weighted panels with robust panels. | Exhaust all cheaper candidate experiments or panels in a tiny corpus. Report assumptions, expected risk, worst-case failures, total original mass, and reconstruction maps. Include a case where Bayes-optimal and worst-case-optimal choices differ. |

## Resources and failure cases

Compression can fail to save space when every original object has a distinct sufficient key. Report original population size, number of compressed keys, target multiplicities, completion states, and coefficient bit sizes separately. Exact probabilities may develop large denominators; record that cost rather than reporting only the number of keys.

Never infer a uniform prior on physical fault configurations merely because the finite catalogue is unweighted. Nor should averaging over arbitrary nuisance parameters be presented as a robust guarantee. If a prior is estimated from data, preserve training/held-out separation and uncertainty in that estimate. The first exact examples are synthetic model decisions.

Order-sensitive experiments can distinguish histories with identical unordered feature counts. For that case, either retain an ordered sufficient representation or explicitly restrict the experiment language to observations determined by the unordered statistic. A counterexample must demonstrate the loss before claiming a compressed key supports future inference.

## Finish criterion

NX23 is complete when original-object weighted populations can be compressed, reweighted, observed, and optimized without losing target ambiguity or multiplicity. The release should show an exact expected-risk certificate, an exact robust comparison, and a clear explanation of which conclusions follow from combinatorics and which depend on the chosen probabilistic model.


# NX24 - Effective finite-prefix theorems

## Mission and completion boundary

Turn a finite-prefix existence argument into a constructive, independently checkable cutoff for at least one restricted nonperiodic family. The central requirement is a proved rule controlling every later coefficient. Neither a long run of agreement nor one repeated ideal in an incremental computation supplies that rule.

This packet deliberately separates three objects: a Noetherian existence theorem, a specific effective construction, and the original graph-height series. A finite parameter space or a finite coefficient-vector dimension alone does not imply a finite transition system for advancing the coefficient index. Likewise, existing rationality in the root-of-unity sector does not imply rationality at ordinary positive parameters. The successful result can be narrow if its assumptions, cutoff, and certificate are precise.

## Grounded local crosswalk and older bridge

Locally inspected `scripts/vakil_bridge.py` records exact triangle moment and symmetry experiments. Its scope text explicitly says that no effective Noetherian cutoff is computed. It links mathematical discussion to `docs/research/VAKIL_BRIDGES.md`; read that file before revising the proof narrative. The script checks ordinary and marked probe Jacobian ranks at generic, two-equal, and all-equal parameter points, with direct rational arithmetic.

Locally inspected `src/singularity/observability.py` supplies a different effective mechanism: finite row-space closure with checked output and transition identities. Locally inspected `src/singularity/periodic.py` proves $F=P/(1-x^M)^n$ with palindromic numerator degree at most $n(M-1)$, yielding the sufficient same-$n,M$ cutoff $\lfloor n(M-1)/2\rfloor$. Its tests check a declared 524-model finite population against direct enumeration. Reuse these as baselines, not new discoveries.

The older PerfectPower rational recurrence and Picard-Fuchs work is chat-sourced until checked in source. The historical Vakil discussion motivates finite generation; it does not license attributing an explicit algorithmic bound to Noetherianity itself. A new effective theorem should cite its actual algebraic mechanism.

## Existence argument and its missing algorithm

Let $\theta$ range over a fixed finite list of algebraic parameters and let

\[
F_\theta(x)=\sum_{n\ge0}f_n(\theta)x^n,\qquad
f_n\in\mathbb Q[\theta].
\]

Introduce an independent parameter copy $\eta$ and coefficient differences $g_n=f_n(\theta)-f_n(\eta)$. In the fixed Noetherian ring $\mathbb Q[\theta,\eta]$, the ideal

\[
I=\langle g_0,g_1,\ldots\rangle
\]

has a finite generating subset. Therefore some finite coefficient prefix generates $I$, and equality on that prefix implies equality of every coefficient. This supplies existence of a cutoff for the fixed polynomial family. It does not tell an implementation when its current prefix has reached that cutoff.

If coefficients are rational functions, specify a localization or a parameter domain excluding every denominator being cleared. Multiplying by denominators can create spurious solutions on exceptional parameter sets. If parameters are constrained, quotient or saturate by the appropriate relations and preserve the domain contract. Vanishing on a real semialgebraic region may call for real-algebraic methods rather than blindly substituting an ordinary complex radical computation.

## Counterexample to a false stopping rule

Take parameters $(a,b)$ and a fixed but arbitrarily large integer $K$, with coefficients $f_n=a^{n+1}$ for $n<K$ and $f_K=b$. Every early difference lies in the ideal $\langle a-a'\rangle$, and $I_N=I_{N+1}$ can hold for many steps. At index $K$, the new difference $b-b'$ changes the ideal. Thus a temporary equality of consecutive prefix ideals is not evidence that every future coefficient is controlled.

A still simpler delayed family has $F_b(x)=b x^K$. Every coefficient before $K$ is zero although the family is nonconstant. No cutoff derived only from the parameter count or observed current rank can exclude this delay. Add this regression to any proposed cutoff engine.

## Valid constructive mechanisms

One sufficient mechanism is a proved state transition for the coefficient index:

\[
s_{n+1}(\theta)=A(\theta)s_n(\theta),\qquad
f_n(\theta)=c(\theta)s_n(\theta),
\]

with fixed finite dimension and a correctness theorem for the original series. For comparing two specializations, block-diagonalize their two transition matrices and use an output row subtracting the two outputs. An effective cutoff follows from a checked finite observable closure. The transition theorem is essential; defining $s_n$ to contain the unknown whole future is not a finite construction.

A second mechanism is a proved recurrence with polynomial-in-index coefficients:

\[
\sum_{j=0}^{r}a_j(n,\theta)f_{n+j}(\theta)=0.
\]

If the leading coefficient is nonzero throughout the declared integer-index and parameter domain after a certified threshold, an initial finite block plus the finite exceptional-index treatment determines the sequence. Such a recurrence may apply to a nonrational generating function. Singular parameter values or integer indices where the leading term vanishes require separate strata; a recurrence guessed from sample coefficients is not a proof.

For comparison across two parameter values, a recurrence for each individual sequence is not enough to propagate their equality. The checker needs a common proved recurrence for the difference sequence, or a combined comparison system with a certified uniqueness argument. If the recurrence coefficients differ with the parameters, canceling two individual recurrences as though they were identical is invalid. Record the comparison recurrence and its nonvanishing-leading-term domain explicitly.

A third mechanism is a certified finite ideal closure under an explicitly proved coefficient-generation operation. The checker must verify that future generation preserves the ideal or submodule generated by the retained prefix. This may give an effective theorem without a rational generating function. Choose the easiest genuinely supported mechanism first rather than promising a general graph-series decision algorithm.

## Tiny exact positive example

For $F_\theta(x)=(1-\theta x)^{-1}$, $f_n(\theta)=\theta^n$. The first coefficient $f_0=1$ gives no information, while $f_1=\theta$ determines the entire series. A one-dimensional transition $s_{n+1}=\theta s_n$, $s_0=1$, proves that assertion. For comparing two specializations, the two-dimensional block system is constructive even though direct algebra gives the sharper cutoff one.

Contrast this with a nonrational candidate such as a family governed by a validated polynomial-index recurrence. Its sequence can still have an effective uniqueness prefix without a constant finite matrix transition. The implementation must record which mechanism was proved and avoid describing every finite-cutoff result as rationality.

## Proposed API and schema

Propose `src/singularity/prefix_certificates.py` with separate certificate classes FiniteStatePrefixCertificate, RecurrencePrefixCertificate, and IdealClosurePrefixCertificate. A shared interface can expose compare_prefix, cutoff, parameter_domain, exceptional_strata, and verify_certificate, but no class should infer missing structure from a supplied finite sample.

A proposed singularity.prefix-certificate/1 receipt records the original family definition and source digest, coefficient ring, parameter relations, denominator exclusions, exact transition/recurrence/closure identities, all exceptional cases, sufficient cutoff, comparison convention, and a proof or independently checked derivation connecting the certificate to the original coefficients. Label a merely conjectured recurrence separately and prevent it from returning certified equality.

## Three implementation pushes

| Push | Artifacts and work | Acceptance and independent oracle |
|---|---|---|
| NX24-A - Unified effective-cutoff contracts | Encode existing finite-state and periodic certificates without changing their scope. Add delayed-coefficient counterexamples and strict certificate parsing. | Replay periodic examples against direct enumeration and finite-state examples against independent matrix powers. A finite sample or temporary ideal stabilization must never produce a certified cutoff. |
| NX24-B - One new restricted nonperiodic theorem | Select a source-supported recurrence or ideal-generation family, derive its identities, handle singular indices/parameters, and retain its explicit sufficient cutoff. | Independently compute coefficients beyond the cutoff, verify the governing identity symbolically or by a separate exact derivation, and publish the full uniqueness proof. Beyond-cutoff agreement supports the proof but does not replace it. |
| NX24-C - Family comparison and exceptional strata | Integrate parameter-domain decomposition, compare two models, and expose first difference or certified equality with the mechanism recorded. | Exhaust a declared finite parameter census against a separate coefficient oracle; retain singular and regular cases, forged recurrence rejections, and denominator-degeneration counterexamples. Include resource limits and resume data. |

## Resources and finish criterion

Polynomial ideal computations can have severe degree and coefficient growth. Record ring variables, monomial order, degrees, term counts, coefficient bits, runtime, and memory. A timeout leaves the research task open; it is not evidence of infinite ambiguity or absence of a cutoff. Modular calculations can disprove an alleged identity, but modular agreement alone cannot establish a characteristic-zero theorem without reconstruction bounds and verification.

Call NX24 complete only when the new effective result has a mechanism-level proof, an explicit cutoff, exact exceptional-case handling, and an independent original-coefficient oracle. If only the existing periodic theorem is repackaged, mark NX24-A complete and leave NX24-B/C open. The scientific value is an honest effective theorem, not a premature universal stopping claim.


# NX25 - Forecast-target sensor design

Status: proposed implementation packet, not an accepted result. This packet inherits exact observation and error machinery while turning an older WIND idea into a reproducible experiment-design problem. Its application target is a future quantity, not reconstruction of an entire atmospheric state. All historical WIND comparisons below are chat-derived context. This handoff does not contain the reported radar archive, its derived arrays, or a reproduced operational forecast advantage.

## The question and the mathematical object

Suppose a declared finite-dimensional model evolves by

\[
 x_{t+1}=Fx_t+Bu_t,\qquad y=Hx_0+e,\qquad J_\tau=g^\top x_\tau.
\]

If inputs are known, their contribution to the future target is known. The unknown contribution is \(G_\tau x_0\), with \(G_\tau=g^\top F^\tau\). Present-target recovery requires \(\ker H\subseteq\ker g^\top\); future-target recovery requires the different condition

\[
 \boxed{\ker(HZ)\subseteq\ker(G_\tau Z)}.
\]

Here columns of \(Z\) span the admissible perturbation subspace after exact affine constraints and fixed nuisance directions have been accounted for. Specify the affine centre separately. An observation can be excellent for the present target while remaining blind to its driver and therefore useless for a later target. This is the conceptual bridge to the older WIND driver-versus-direct-target experiments, whose numerical gains must not be transferred to new data.

For exact linear recovery, search for \(L\) satisfying \(G_\tau Z=LHZ\). A successful factorization is a certificate, not a regression fit. Its conditioning matters. In Euclidean norms a bound

\[
 Z^\top G_\tau^\top G_\tau Z\preceq\kappa^2 Z^\top H^\top HZ
\]

implies \(\lVert G_\tau Zz\rVert\le\kappa\lVert HZz\rVert\). For correlated uncertainty use the corresponding declared metric or attainable observation sets. Rank establishes possibility; the smallest justified \(\kappa\), or a target interval diameter, establishes error amplification. Do not invert a nearly singular numerical matrix and call the resulting decimal a certificate.

## A small exact example that must ship

Let state \(x=(p,v)\), where \(p\) is present position and \(v\) a persistent driver, and take

\[
 F=\begin{pmatrix}1&1\\0&1\end{pmatrix},\quad
 g^\top=(1,0),\quad H_p=(1,0),\quad G_3=(1,3).
\]

States \((0,1)\) and \((0,-1)\) have identical present observations and future targets \(3\) and \(-3\). The null vector \((0,1)\) witnesses the impossibility of recovering the future target from present position alone. If position is already known and the extra measurement reads velocity, that measurement repairs the target. If both are uncertain, both information channels are needed, or one must directly measure the appropriate combination.

With independent deterministic errors \(\lvert e_p\rvert\le1/10\) and \(\lvert e_v\rvert\le1/5\), the reconstructed horizon-three target has worst-case error \(1/10+3/5=7/10\), attained by aligned error signs. Retain both the factorization and this attainability witness. An independent enumeration of error-box vertices should recover the same bound. The example teaches why forecasting depends on a horizon-specific row, and why a sensor ranking cannot be reused for every horizon.

## Verified source crosswalk and boundaries

`src/singularity/observability.py` contains `OperatorSystem`, `observable_closure`, `verify_certificate`, `minimum_distinguishing_experiment`, and explicit chronological experiment construction. It provides exact rational row closure and all-future equivalence under a declared operator language. It does not supply a meteorological forecast model. `src/singularity/experiment_design.py` contains `RationalMetric`, `minimum_separation`, and `nearest_candidate`; integral polynomial metrics are not automatically sensor-noise covariances. `src/singularity/panels.py` supplies finite-pool exact panel comparison and an exhaustive small-instance oracle. Preserve the distinction between recovery of a continuous linear target and identification of finitely many candidate labels.

The inspected sibling DynaComp checkout contains `linear.py::LinearModel`, `compile_linear`, `closure_witness`, `distinguishing_horizon`, and `replay_linear`. In particular, `compile_linear` closes target rows under a transition, and replay checks exact algebraic identities. `uniform.py::output_box_range` and `sharp_box_bound` give relevant correlated/domain-aware output bounding machinery. These files are cross-repository references, not guaranteed importable dependencies of this ZIP. Pin a fetched source revision before integration; do not add DynaComp as an undeclared core dependency.

Historical WIND material reports a 272-volume provenance-matched NEXRAD archive and studies of low cuts, structural invisibility, and driver-aware synthetic forecast comparisons. Those statements are research leads. Request or locate their source manifests before quoting them as newly reproduced evidence. The reported lower-cut information was not a measurement of ten-metre wind; this packet must not collapse radar sampling height into a ground-level target.

## Proposed implementation and artifact contracts

Add an optional application layer `applications/forecast_targets/` and, only after interface review, a reusable `src/singularity/forecast_targets.py`. Proposed records are `ForecastTarget(A, B, target_rows, horizon, state_domain)`, `SensorBlock(identifier, H, noise_contract, cost)`, and `TargetRecoveryReceipt`. A receipt records rational matrices as numerator/denominator strings, units, sampling interval, horizon, admissible-state basis, input assumptions, selected sensors, factorization or null witness, target bounds, and provenance hashes.

Proposed APIs are `forecast_row(model, horizon)`, `target_factorization(H, G, basis=None)`, `target_null_witness(H, G, basis=None)`, and `select_target_panel(blocks, target, budget, uncertainty)`. The selector should reject unknown units, incompatible dimensions, negative costs, and unsupported error geometries. An undecided optimization returns bounds and a work-budget status rather than a fabricated optimum. Keep a forecast target's physical definition separate from a surrogate score used to rank sensors.

## Three concrete acceptance pushes

**NX25-A - Exact target specification and synthetic witnesses.** Implement the horizon-row compiler and exact factorization/null-witness path. Add the two-state example and a constrained-state example in which full ambient rank is irrelevant. Acceptance requires exact comparisons against direct trajectory powers through horizon eight, independent row-kernel reconstruction, malformed-schema tests, and a human-readable derivation in `docs/research/FORECAST_TARGETS.md`. Retain `results/forecast_targets_synthetic.json` with synthetic evidence labels.

**NX25-B - Costed robust target panel.** Add a finite catalogue of at most twelve sensor blocks, horizons at most sixteen, and declared bounded initial/noise domains. Optimize an explicitly chosen target-loss bound. Exhaustive comparison over at most \(2^{12}\) panels is the independent oracle. Acceptance includes an equal-rank/different-conditioning pair, an infeasible target with a null witness, and a finite noise threshold with strict boundary handling. No claimed improvement may be caused solely by changing the uncertainty model between baseline and candidate.

**NX25-C - Frozen archive pilot.** Acquire or recover one manifest-bound real-data subset, freeze the forecast target, truth source, training dates, and evaluation dates before fitting. Compare direct-target, driver-aware, and generic information policies at matched acquisition cost. Acceptance is a reproducible report even if no improvement occurs. Target missingness, time alignment, radar geometry, and unavailable ground truth must be visible in the report. A model-derived forecast variance is not an empirical forecast skill score.

## Source acquisition, budgets, and failure modes

Begin with a source inventory in the user's existing WIND workspaces and provided GitHub repositories, recording accessible paths and hashes. If archives are absent, discover public NOAA/NEXRAD object listings or another primary source through documented anonymous HTTP interfaces. Fetch metadata and one tiny permitted sample first, never assume a Kaggle or cloud sign-in session. Record download URL, timestamp, bytes, checksum, units, decoder revision, and reuse terms. Limit the first real pilot to twelve volumes or two gigabytes, whichever is reached first; synthetic exact dimensions stay at twelve and a replay should finish within two minutes on the declared machine. Larger acquisition is a separately accepted expansion.

Failure modes include using future information during sensor selection, confusing present and future target rows, extrapolating an unvalidated transition model, changing costs across baselines, treating a posterior variance as empirical truth, and applying a local linearization outside its certified neighbourhood. Unknown input disturbances require additional columns or uncertainty sets. Nonstationarity requires a declared model family, not a single frozen matrix silently reused. Deliver a negative result when the target is structurally invisible or the forecast model lacks validation. The central output is an explicit explanation of what information a future target needs, with an experiment capable of acquiring that information under the stated assumptions.

## Interpretation contract

A selected sensor is a decision about information under a declared model. It is not permission to claim that the model predicts the atmosphere accurately. Record separately whether the target is an instantaneous value, a time average, an event threshold, or a conditional probability; these have different observation requirements. When threshold decisions are requested, propagate the complete target interval and return an unresolved label whenever that interval crosses the threshold. Never select the favourable endpoint. This creates a usable abstention contract alongside exact identifiability.


# NX26 - Nonlinear ambiguity witnesses

Status: proposed mathematical and software expansion. The deliverable is an explicit pair of admissible states with the same observations and different target values, or a proof of constancy in a precisely bounded class. This is stronger than reporting a poorly conditioned fit and more honest than treating a local Jacobian rank calculation as a global identification theorem. The historical inspiration comes from the user's WIND observation-fibre and SOE target-fibre discussions; those archived calculations are not bundled or newly replayed here.

## Define the fibre before calculating ranks

Let the admissible state domain be a compact semialgebraic set \(D\), with exact rational polynomial constraints \(C(x)=0\), inequalities \(b_j(x)\ge0\), observation map \(H\), and scalar target \(T\). For an exact observation \(y\), define

\[
 \mathcal F_y=\{x\in D:H(x)=y,\ C(x)=0\},\qquad
 A_T(y)=\sup_{x,x'\in\mathcal F_y}|T(x)-T(x')|.
\]

If \(A_T(y)>0\), the target is ambiguous. A witness consists of two valid states and independently checked observation equality plus a positive target gap. It proves ambiguity without solving the global supremum. A claimed exact diameter needs both feasible extremizers and a valid upper bound. Compactness prevents a missing boundedness hypothesis from turning the target diameter infinite or unattained. For bounded measurement error, replace equality by the declared observation set; do not round a small floating residual to exact equality.

At a regular point, tangent directions satisfy \(DH(x)n=0\) and \(DC(x)n=0\). If \(DT(x)n\ne0\), the target varies locally along an admissible fibre curve under suitable regularity. The converse is false without higher-order and global analysis. A target can have zero first derivative and still vary quadratically; several disconnected branches can share observations even when every local chart is invertible.

## Exact affine-fibre theorem and its limits

For an affine fibre \(x=x_0+Nz\) and quadratic target

\[
 T(x)=g^\top x+\tfrac12x^\top Qx,\qquad Q=Q^\top,
\]

substitution yields

\[
 T(x_0+Nz)=T(x_0)+z^\top N^\top(g+Qx_0)
 +\tfrac12z^\top N^\top QNz.
\]

On a fibre domain containing a relatively open neighbourhood, constancy is equivalent to both \(N^\top(g+Qx_0)=0\) and \(N^\top QN=0\). The open-domain hypothesis matters: a finite admissible subset can make a nonzero polynomial accidentally constant. Retain this theorem and the distinction between unrestricted affine fibres, constrained pieces, and finite samples. If target matrices are supplied nonsymmetrically, symmetrize explicitly or reject the input instead of applying the wrong gradient.

A first exact example is \(H(x_1,x_2)=x_1\), \(T=x_2^2\), \(D=[-1,1]^2\), and observation zero. At the origin the target gradient vanishes, but states \((0,0)\) and \((0,1)\) have target gap one. The fibre diameter is exactly one, witnessed by nonnegativity and \(|x_2|\le1\). A second example is \(H(x)=x^2\), \(T(x)=x\), \(D=[-1,1]\): at observation one, states minus one and one have target gap two although the observation derivative is nonzero at both points. Local identifiability is not global branch identification.

## Curved fibres require a curvature correction

Let \(K=(H-y,C)\) collect equality constraints. For a curve \(x(s)\) on the fibre with tangent \(n=x'(0)\) and acceleration \(a=x''(0)\), differentiating twice gives

\[
 DK\,a+\big(n^\top\nabla^2K_i\,n\big)_i=0,
\qquad
 \frac{d^2}{ds^2}T(x(s))\bigg|_0
 =n^\top\nabla^2T\,n+DT\,a.
\]

If \(DT=\lambda^\top DK\) at a regular stationary point on the fibre, this becomes

\[
 n^\top\left(\nabla^2T-\sum_i\lambda_i\nabla^2K_i\right)n.
\]

The projected ambient Hessian alone is therefore insufficient. For the parabola \(K(x,y)=y-x^2=0\) and target \(T=y\), at the origin the tangent is \(n=(1,0)\), ambient target Hessian is zero, and \(DT=DK\). The corrected Hessian gives two, exactly matching \(T(s,s^2)=s^2\). This tiny example must be a permanent regression test. At singular constraint points no regular tangent-manifold claim is allowed; the report must return a singular-stratum status or use a separate algebraic argument.

## Source crosswalk and proposed interfaces

Verified Singularity sources are `src/singularity/observability.py` for exact linear nullspaces and future equivalence, `experiment_design.py` for rational metrics and finite-candidate separation, and `panels.py` for finite sensor-panel selection. They do not currently prove nonlinear fibre constancy. The inspected DynaComp `polynomial.py` provides exact sparse polynomial validation, evaluation, composition, and target-preserving polynomial compilation with explicit degree/term limits. Its compiler is useful for finite closed polynomial lifts; it is not a complete real-algebraic feasibility solver. Keep external symbolic algebra optional, versioned, and outside the standard-library core.

Propose `applications/nonlinear_fibres/` with `PolynomialFibre`, `TargetWitness`, `LocalFibreAnalysis`, and `DiameterEnclosure` records. Proposed operations are `verify_witness`, `affine_quadratic_constancy`, `regular_tangent_test`, and `curved_second_variation`. Witness schemas include exact states or algebraic isolating data, domain inequalities, observation/noise contract, target gap lower bound, arithmetic mode, and algorithm status. Replays substitute into original constraints instead of trusting a transformed chart. Numerical candidate finding may suggest states, but acceptance requires exact substitution or validated enclosures proving all required claims.

## Three concrete acceptance pushes

**NX26-A - Affine fibres and exact witnesses.** Implement quadratic constancy and replay for rational polynomial witnesses. Ship all three small examples above, plus malformed and unbounded-domain cases. Independently expand the substituted target coefficients and compare with the matrix criterion. Acceptance requires a clear distinction among witness gap, diameter lower bound, and certified complete diameter.

**NX26-B - Curvature-aware local analysis.** Add regular constraint Jacobians, Lagrange-multiplier second variations, and explicit singular-point handling. Verify the parabola correction by direct rational parametrization. Include a circle chart with the same target analysed in two overlapping parametrizations and equal intrinsic second variation at a stationary point. Acceptance requires differentiating the constraint identities independently from the Hessian implementation; merely calling the same symbolic differentiation routine twice is not an oracle.

**NX26-C - Sensor repair on a bounded nonlinear pilot.** Use at most four state variables, degree four, six candidate sensor polynomials, and exact or interval-validated witnesses. Add a measurement that separates every retained witness pair and compare its panel cost with exhaustive subsets. Report whether it resolves the entire fibre or only the retained finite witness population. Acceptance includes a case where every sampled witness disappears but a new branch remains, demonstrating why finite witness coverage is not a global theorem.

## Acquisition, resource budgets, and useful negative results

Historical WIND discussions mention hidden-gradient examples, target curvature, and observations that leave substantial target uncertainty. Recover the original equations, domain assumptions, units, and decoder/model manifests before making quantitative comparisons. Search existing supplied workspaces and public project files first; if a source is unavailable, retain a `source_missing` record and proceed with the fully specified synthetic cases. No login, private archive, or unprovided ground-truth field may be assumed. Public physical examples should come from documented primary equations and anonymously accessible data with a source manifest.

Default exact pilots use at most four variables, degree four, thirty-two sparse monomials per polynomial, 256 witness candidates, and a two-minute replay budget. Cap interval subdivision at 10,000 boxes and one gigabyte. A refusal must retain its remaining boxes and status, not assert constancy. Optional computer-algebra work is a separate bounded job. Failed positivity, unbounded fibres, singular strata, disconnected branches, invalid charts, and observations near the noise threshold are mathematically informative outcomes. The purpose is to say precisely which worlds remain consistent with the measurements and what additional observation would eliminate their target disagreement.

## Connecting a witness to an experiment

For a finite witness pair, a candidate sensor polynomial \(S\) repairs that pair only if its two possible reading sets are disjoint under the same uncertainty contract. A nonzero symbolic difference is insufficient if the declared sensor noise is larger than the gap. Conversely, a sensor that resolves one witness need not resolve all states on the fibre. Store both the original witness and its repaired reading gap, and keep the original domain unchanged while comparing sensors. For a compact semialgebraic domain, interval subdivision can supply conservative range enclosures, but polynomial extrema need not occur at box vertices. Vertex enumeration is exact only for the specific affine or multilinear objectives whose hypotheses justify it. A midpoint grid cannot certify a global maximum. The implementation should therefore distinguish exact algebraic certificates, validated range enclosures, feasible lower-bound witnesses, and exploratory numerical candidates in its status field.


# NX27 - Target-preserving multiscale transport

Status: proposed implementation and analysis packet. This track connects the user's older multiscale WIND/μ-Arena ambitions with exact quotient dynamics, approximation-error transport, and a target-aware stopping rule. It does not claim an existing atmospheric simulator, a continuum-to-ground transfer theorem, or a validated physical replacement of unresolved turbulence. Deliver a small, explicit fine/coarse model pair first, then decide whether an empirical application is justified.

## The model and the commutation defect

Let fine dynamics be \(x_{t+1}=F_f(x_t,u_t)\), let \(E\) map fine states to coarse coordinates, and let coarse dynamics be \(z_{t+1}=F_c(z_t,u_t)\). Define coarse-state error \(e_t=Ex_t-z_t\) and the local commutation defect

\[
 d_t=EF_f(x_t,u_t)-F_c(Ex_t,u_t).
\]

If the coarse map is \(L_t\)-Lipschitz over a proved reachable domain, then

\[
 \|e_{t+1}\|\le L_t\|e_t\|+\|d_t\|,
\quad
 \|e_T\|\le\Big(\prod_{j<T}L_j\Big)\|e_0\|
 +\sum_{t<T}\Big(\prod_{j=t+1}^{T-1}L_j\Big)\|d_t\|.
\]

For a constant Lipschitz bound this reduces to \(L^T\|e_0\|+\sum_{t<T}L^{T-1-t}\delta_t\). The defect measures failure of reduction and evolution to commute. It is a mathematical object to bound on an admissible set, not the residual on one convenient trajectory. Numerical evidence of a small defect along training states is not a uniform bound.

A target needs its own compatibility condition. If \(J_f(x)\) and \(J_c(z)\) are fine and coarse targets, bound

\[
 |J_f(x_T)-J_c(z_T)|\le
 |J_f(x_T)-J_c(Ex_T)|+L_J\|e_T\|.
\]

The first term is representation mismatch; the second is dynamic propagation. A coarse state may approximate selected averages well while losing a target sensitive to a fine gradient. Keep source-model error, discretization error, reduction error, observation error, and arithmetic error separately named. Adding validated bounds is permitted; calling an unmeasured residual “physical model error” is not.

## An exact four-state pilot

Use a path of four cells with unit graph Laplacian \(L\), fine step \(A_f=I-L/8\), and coarse pair averages

\[
 E=\tfrac12\begin{pmatrix}1&1&0&0\\0&0&1&1\end{pmatrix},
 \quad V=\begin{pmatrix}1&0\\1&0\\0&1\\0&1\end{pmatrix},
 \quad A_c=EA_fV=\begin{pmatrix}15/16&1/16\\1/16&15/16\end{pmatrix}.
\]

Here \(EV=I\), but that identity does not imply exact dynamic closure. With fine initial state \(x=(0,1,0,0)^\top\), the projected fine next state is \((7/16,1/16)^\top\); evolving its coarse average gives \((15/32,1/32)^\top\). Thus

\[
 (EA_f-A_cE)x=(-1/32,1/32)^\top.
\]

Retain this counterexample. It prevents a projection/reconstruction pair from being mistaken for an exact quotient. Conversely, total mass is preserved by the reflecting path diffusion: the target \(\mathbf1^\top x\) has an exact one-dimensional closed evolution. The same fine dynamics therefore admit an exact mass target and an approximate pair-average state. This is the design principle: closure requirements depend on the target.

For a linear fine/coarse pair the defect matrix is \(D=EA_f-A_cE\). On a box \(|x-x_*|\le r\), each component is bounded by \(|Dx_*|+|D|r\). This is an attainable componentwise box bound, though the component maxima need not occur at one common state. Independent enumeration of the sixteen box vertices checks the four-cell example. For correlated domains, retain the generators instead of inflating immediately to a box.

## Existing code and what must remain external

`src/singularity/observability.py` provides exact operator closure and replay identities. `src/singularity/thermal_diagnostics.py::AffineCandidate` supplies sparse rational steps and observations, with `simulate_protocol` and `protocol_pool` explicitly using separately reset experiments. Those sources give a useful discrete toy environment; the graph-height energy series is not a physical heat equation.

The inspected DynaComp `linear.py::compile_linear` constructs exact target-preserving linear closure. `bounds.py::finite_horizon_bound`, `box_horizon_bound`, and `absolute_apply` provide relevant error propagation. `uniform.py::sharp_box_bound`, `uniform_enrichment`, and `replay_uniform` address bounded domains and certified reduction. Reuse or adapt their mathematical contracts after pinning source revisions, rather than inventing a second incompatible error API. These sibling files are references; their presence in the current workspace does not make them bundled dependencies.

The historical μ-Arena discussions propose global, mesoscopic, boundary, microphysical, and equipment-response states, with chemistry and aerosols. They motivate the transfer-map question but do not establish that every scale transition has a valid Lipschitz constant or that a spectral tail bounds every physical target. Any Hilbert-space singular-value tail theorem must state its chosen metric, approximation class, and norm; it is not a universal multiscale error formula.

## Proposed application contract

Use `applications/multiscale_transport/` for pilot models and source manifests. Proposed records are `ScaleMap(E, V, fine_units, coarse_units)`, `DynamicsPair`, `ReachableDomain`, `CommutationDefectBound`, and `TargetTransferReceipt`. Methods are `linear_commutation_defect`, `box_defect_bound`, `propagate_scale_error`, and `target_transfer_bound`. A receipt contains norms, induced operator bounds, horizon, initial error, input domain, source hashes, representation mismatch, and separate arithmetic/reduction budgets. Shape compatibility is insufficient: units and time-step conventions must agree.

The API must permit exact target closure even when the requested coarse coordinates fail to close. It must also permit a refusal when a reachable-domain enclosure is missing. A proposed coarse model can be rejected by one exact defect witness without rejecting every possible reduction of the fine model.

## Three concrete acceptance pushes

**NX27-A - Exact transfer algebra.** Implement linear defect calculation and target compatibility. Ship the four-cell example, its exact mass quotient, and a case where unit conversion changes the map. Acceptance compares all matrix entries with a direct cell-flux update; verifies the displayed fractions; and checks zero-defect equivalence against the existing closure machinery on tiny examples. Retain a derivation and exact JSON receipt.

**NX27-B - Certified horizon bounds and enrichment.** Add finite-horizon error propagation for bounded inputs and box/correlated initial domains. On at most sixteen fine states, compare against exhaustive vertices and direct trajectories. Enrich a failed coarse model with one missing target-relevant coordinate. Acceptance requires that old bounds remain valid, new bounds improve on a retained case, and numerical smallness never substitute for a reachable-domain proof.

**NX27-C - One physical-data-facing scale transfer.** Recover an existing WIND or μ-Arena manifest, or select one anonymously accessible primary benchmark with a documented coarse/fine relationship. Freeze a scalar target and compare the coarse prediction with fine reference output at matched times. Separate numerical reference agreement from agreement with measurements. Acceptance is an honest transfer-error report, including a negative result if the target cannot survive the chosen coarse representation.

## Resource and acquisition discipline

Keep the first exact pilot at sixteen states, three scale maps, four input channels, horizon thirty-two, and one thousand exact trajectories. Replays should take less than two minutes and one gigabyte; larger grids require a separate measured experiment. Cache rational operator products but record numerator/denominator growth. A two-minute cutoff returns a partial bound and unresolved tasks, not a false uniform certificate.

Locate old manifests before downloading replacement datasets. When absent, search documented primary repositories and anonymous HTTP/object-store listings, retain their metadata and license, and fetch a small sample before bulk acquisition. Cap first external ingestion at two gigabytes. Never infer ten-metre wind from radar sampling height without a separately validated transfer model. Stability on a nominal grid does not prove stability under switching parameters, arbitrary boundary changes, unresolved forcing, or nonlinear chemistry. Those are new hypotheses and should be represented explicitly. The useful final artifact tells a developer exactly which target survives which scale change, under which domain and error bound, and what additional coordinate is needed when it fails.

## Composition across three scales

If a later extension introduces fine, middle, and coarse spaces, first verify whether the direct scale map equals the composed map: \(E_{fc}=E_{mc}E_{fm}\). If it does, derive the direct defect by adding the transported fine-to-middle defect to the middle-to-coarse defect, with the appropriate operator norm. If the maps differ, the discrepancy is an additional representation term and must not disappear into a residual label. A useful acceptance fixture uses three rational diffusion grids and checks this composition identity entry by entry. An especially informative negative example has both neighbouring reductions accurate for average mass but their composition poor for a boundary-gradient target. This prevents a developer from assuming that individually good scale maps compose into a good target model. Keep those target and norm assumptions in every receipt, including intermediate artifacts.


# NX28 - Reactive transport observability

Status: proposed bounded synthetic application, followed by a separately sourced pilot if justified. This packet connects the user's WIND chemistry/aerosol ambitions to target-specific observation design. It does not authorize claims of operational air-quality forecasting, exposure estimation, or physical calibration. A reduced reaction network is a model whose parameters and range of validity must be declared, not a chemical measurement generated by algebra alone.

## Start from a conservative, explicit model

A conceptual continuum equation is

\[
 \partial_t c+u\cdot\nabla c=\nabla\cdot(D\nabla c)+R(c),
\]

where \(c\) is a vector of species concentrations, \(u\) velocity, \(D\) diffusivity, and \(R\) reaction production/loss. The first implementation should use a finite conservative cell discretization with exact rational coefficients, not attempt a full continuum solver. A reaction step needs positivity and stoichiometric balance checks; a transport step needs declared boundary fluxes and units. The observation operator can measure species mixtures, regional averages, or a conserved total. The target can be one species at a location and horizon.

For a linearized or linear network, write \(c_{t+1}=Ac_t+Bu_t\), \(y=Hc_t\), and target \(J_\tau=g^\top A^\tau c_0\). A conserved row \(\ell^\top\) with \(\ell^\top A=\ell^\top\) makes the total easy to recover, but says nothing about recoverability of each species. The exact obstruction is a vector \(n\) satisfying \(HA^tn=0\) for every permitted observation time while \(g^\top A^\tau n\ne0\). The existing finite-dimensional row-closure mechanism can certify that obstruction. It must not be extrapolated to an unvalidated nonlinear mechanism.

For nonlinear chemistry, target sensitivities and tangent kernels are useful local design tools. They do not establish global fibre constancy. Use NX26's explicit witness and curvature contracts for global ambiguity questions, and NX27's source/representation/dynamic-error separation for scale changes.

## Exact pilot: conversion hidden by total concentration

Consider two cells and two species \(A\to B\). Let the spatial mixing matrix be

\[
 D=\begin{pmatrix}7/8&1/8\\1/8&7/8\end{pmatrix},
\quad
 K=\begin{pmatrix}3/4&0\\1/4&1\end{pmatrix}.
\]

In state order \((A_1,A_2,B_1,B_2)\), reaction plus mixing gives

\[
 M=\begin{pmatrix}(3/4)D&0\\(1/4)D&D\end{pmatrix},
 \qquad H=\begin{pmatrix}1&0&1&0\\0&1&0&1\end{pmatrix},
 \qquad HM=DH.
\]

Thus cellwise total concentrations evolve autonomously under mixing. Initial states \(c=(1,0,0,0)\) and \(c'=(0,0,1,0)\) have identical total observations at every time. Their total \(B\) concentrations differ after one step by \(3/4\), and after \(T\) steps by \((3/4)^T\). Measuring the total more accurately or more often cannot identify the species target. A species-selective measurement can repair this structural blindness. Note that waiting makes the target discrepancy smaller in this example; “more time” is not automatically “more information.”

Both states are nonnegative, have total mass one, and the matrix is nonnegative and column stochastic. Those facts make the example physically interpretable as a discrete conservative toy, but they do not validate any named atmospheric reaction. The independent oracle should update reaction and cell fluxes separately and compare with the block matrix. Keep total-target and species-target outputs in the receipt so the reason for failure is transparent.

An uncertainty extension lets the initial species fraction vary continuously. A total-only observation leaves an interval of possible \(B\) targets; the interval shrinks dynamically according to the declared conversion rate. A repair sensor's required precision follows from the interval gap, rather than from nominal-state rank alone. Reaction-rate uncertainty may overlap different species hypotheses and must be included before asserting detectability.

## Source crosswalk and proposed software boundary

`src/singularity/thermal_diagnostics.py::AffineCandidate` is a verified generic sparse rational affine-model record despite its application-oriented module name. It supplies exact `step` and `observe` methods and keeps candidate identities distinct. `observability.py` provides closure certificates and all-future equality for finite rational operator languages. `panels.py` can optimize a declared finite set of species/location/time readings. Its existing common-error panel contracts should not be silently generalized to arbitrary correlated chemistry uncertainty.

The inspected DynaComp `linear.py` supplies exact target-preserving reduction and independent identity replay, `polynomial.py` supplies sparse polynomial operations and bounded controlled closure, and `uniform.py` supplies domain-aware output bounds for linear reductions. These are reusable mathematical ingredients, not an integrated reaction simulator. A fetched cross-repository source must be pinned, its dependency boundary documented, and the core standard-library guarantee preserved unless a concrete accepted optional layer needs more.

Propose `applications/reactive_transport/` with `ReactionTransportModel`, `SpeciesUnits`, `ConservationLaw`, `ReactiveTarget`, and `SpeciesSensor` records. A model schema includes stoichiometry, transport stencil, boundary conditions, time step, concentration units, reaction convention, initial nonnegative domain, input domain, exact arithmetic, and source status. Proposed functions are `verify_conservation`, `verify_positive_step`, `reactive_target_rows`, and `species_sensor_panel`. Replays substitute into original stoichiometry and cell fluxes instead of trusting a preassembled matrix.

## Three concrete acceptance pushes

**NX28-A - Conservative exact toy and blindness proof.** Implement the two-cell conversion model and all displayed identities. Independently update reaction and transport, verify total mass on every simplex vertex, and retain the target gap at horizons zero through eight. Acceptance includes an exact invisible direction and a species-selective repair, with a readable explanation of why total concentration is insufficient.

**NX28-B - Costed species/location/time design.** Extend to at most four cells, three species, eight sensor channels, and sixteen horizons. Optimize a finite candidate panel under bounded initial-state and sensor errors. Compare with exhaustive subset search over at most twelve experiments. Include one case with uncertain reaction rate where nominal rank suggests recovery but robust hypothesis sets overlap. An infeasibility result is acceptable and should include a concrete ambiguity witness.

**NX28-C - One provenance-bound primary-data pilot.** Select one measured species target and a documented reduced mechanism. Recover old source manifests first; otherwise locate anonymously accessible official bulk data or a primary benchmark with explicit units and time stamps. Freeze site, dates, target horizon, training data, evaluation data, and baseline before fitting. Acceptance is a reproducible model/measurement discrepancy report, not a promised forecast gain. No synthetic latent species may be scored as if independently measured truth.

## Acquisition and bounded execution

Historical chats mention HOx-NOx-VOC-ozone reduction and two-moment aerosols. They do not supply a complete mechanism, rates, aerosol parameters, or archived measurements in this handoff. Recover those inputs with provenance before expanding beyond the toy. For public observations, discover official bulk-download routes and verify anonymous access; do not assume an API key, Kaggle session, private sensor feed, or manual spreadsheet upload. Record source URL, download hash, measurement method, detection limit, unit conversions, clock convention, and missing-value codes. First download at most fifty megabytes of metadata/sample data, then cap the accepted pilot at one gigabyte.

Default synthetic replay uses at most twelve state variables, degree two for any optional nonlinear extension, 512 bounded candidate states, and two minutes of CPU time. Nonlinear stiffness can invalidate an explicit step despite positive nominal rates; positivity and time-step restrictions must be checked. Open boundaries can destroy conservation. Unknown reactions can mimic a fault. Aggregated measurements can hide species changes. Unobserved forcing and calibration drift need explicit nuisance terms. A numerical trajectory outside the positivity domain is a model or discretization failure, not an unusual physical prediction. The final receipt should state the target, what observation information is missing, and whether the proposed sensor repair actually resolves the declared uncertainty family.

## Sensor meanings and target units

A species sensor is a specified linear or nonlinear response to concentrations, not necessarily a direct concentration coordinate. If the instrument cross-reacts with several species, include its response coefficients and calibration uncertainty in \(H\). If the target is a mass while observations are molar concentrations, record molecular conversion factors and cell volumes explicitly. A physically conserved quantity can then have a different row from the unweighted sum of state entries. Retain one fixture where a wrongly unweighted conservation row fails and the correctly weighted row succeeds. This is an independent dimensional check and protects the more ambitious chemistry extension from achieving fictitious closure by mixing incompatible units.


# NX29 - Identifiable movement-test design

Status: proposed measurement-design work, followed by a separately frozen empirical study. The target is a movement capability defined by a response model and a demand distribution. It is not a claim that a mathematical feature predicts football success. Historical results are chat-derived and must be recovered with their source manifests before quotation as newly reproduced evidence. This handoff does not contain the reported player videos, recruiting tables, tracking archive, or held-out predictions.

## The inherited scientific problem

The older movement work used a four-coefficient stress-response model,

\[
 \eta(s,a)=\beta_0+\beta_1s+\beta_2a+\beta_3sa,
 \qquad \phi(s,a)=(1,s,a,sa)^\top.
\]

Here \(s\) and \(a\) are declared normalized movement conditions, not automatically raw speed and acceleration in interchangeable units. Given drill design matrix \(X_D\), the observed response is \(r=X_D\beta+e\). A requested capability is \(h^\top\beta\). It is identifiable from noiseless data exactly when

\[
 \boxed{h\in\operatorname{row}(X_D)}
 \quad\Longleftrightarrow\quad
 \ker X_D\subseteq\ker h^\top.
\]

If the target is an average over a demand distribution \(q(s,a)\), then

\[
 h=\int\phi(s,a)q(s,a)\,ds\,da.
\]

That target need not require identification of all four coefficients. Conversely, repeated measurements under the same deficient conditions cannot recover a missing interaction coefficient. A model may fit existing drill outputs while leaving the requested capability undetermined. The right result is a target-specific missing-information witness and a cheapest admissible drill repair.

Historical chats report that 93.2% of player/drill panels lacked enough distinct conditions for all four coefficients; that percentage belongs to its original cohort, feature extraction, and rank tolerance. It is not a universal population statistic and must not be reused on a new archive without recomputation. The same history reports improved measurement stability from angular-progress alignment, but earlier held-out prediction tests often worsened when movement features were added. Preserve these distinctions: identification, reliability, and predictive value are three separate questions.

## Exact four-condition example

Use normalized design points \((0,0),(1,0),(0,1)\). Then

\[
 X_3=\begin{pmatrix}1&0&0&0\\1&1&0&0\\1&0&1&0\end{pmatrix},
 \quad n=(0,0,0,1)^\top,
 \quad X_3n=0.
\]

For target condition \((1,1)\), \(h=(1,1,1,1)^\top\), so \(h^\top n=1\). Coefficients \(\beta\) and \(\beta+n\) fit every existing drill identically but predict target responses differing by one. Adding the fourth condition \((1,1)\) produces a square matrix with determinant one and identifies the coefficients exactly. This example must be retained as rational arithmetic, with direct substitution independent of row reduction.

The restricted target \(h_0=(1,1,0,0)^\top\) is already recoverable from the \((1,0)\) observation. This counterexample prevents an API from demanding full profile rank when only one capability is requested. With heteroscedastic or correlated measurement errors, target recovery can be unstable even at full rank. For a linear estimator \(h^\top\hat\beta=w^\top r\), require \(X_D^\top w=h\) and bound target error by the support function of the declared error set; for a box it is \(\sum_i|w_i|\epsilon_i\). Optimize that bound before reporting a reliable individual capability.

## Verified source crosswalk

Singularity's `observability.py` provides exact rational row-space and null-witness tools, but its graph and operator semantics should not be presented as player biomechanics. `experiment_design.py::RationalMetric` provides exact metric validation and nearest-candidate guarantees for a declared finite model family. `panels.py` supports finite-pool exact cost optimization with an exhaustive small-instance oracle. Continuous regression-target identification needs its own factorization contract; a finite-label classifier is not an interchangeable substitute.

The inspected DynaComp `linear.py` provides exact target closure and replay identities; `uniform.py` and `bounds.py` provide bounded-domain error machinery. Those modules can inform API design but are not presently a player-data package. Keep acquisition, identity linking, video feature extraction, and predictive evaluation in an optional application directory, not in graph-height core code. No sibling repository or historical file should be silently assumed included in the handoff ZIP.

## Proposed interfaces and data provenance

Propose `applications/movement_design/` with `MovementCondition`, `DrillObservation`, `DemandTarget`, `DesignWitness`, and `DrillRepairReceipt`. Records must include athlete identity namespace, event identifier, date, drill protocol, normalized condition values and transforms, units, observed response definition, extraction version, uncertainty, source hash, and missingness. Store raw source identities alongside canonical linked identities. Recruiting identifiers and roster identifiers can inhabit different namespaces; numeric equality is not evidence of athlete identity.

Proposed APIs are `target_identifiable(design, target)`, `target_null_witness`, `bounded_target_estimator`, and `minimum_drill_repair(existing, candidates, target, cost_contract)`. The repair function minimizes cost within a finite declared catalogue, not the cost of every imaginable drill. Allow athlete-specific admissibility constraints and return `unsupported_target` when the response model cannot define the requested capability. Do not turn a drill score into intrinsic athletic ability without a separately validated interpretation.

## Three concrete acceptance pushes

**NX29-A - Exact design specification.** Implement the four-condition example, target-specific row-span certificates, and invisible coefficient directions. Retain rational JSON fixtures and a conceptual derivation. Acceptance compares factorization and null-witness outputs with direct polynomial evaluation; includes a full-profile-rank failure with a recoverable target; and rejects inconsistent scaling or missing response definitions. Add no real-data performance claim at this stage.

**NX29-B - Robust minimum-cost repair.** Build a catalogue of at most twelve additional conditions and target intervals under a fixed uncertainty model. Compare selected repairs with exhaustive subsets. Include equal-rank designs with different target error bounds, replicated observations that improve noise but not structural rank, and a finite candidate catalogue that cannot identify the target. Acceptance requires exact accounting for drill cost, repetition cost, and athlete/domain feasibility constraints.

**NX29-C - Frozen multi-source athlete pilot.** Recover the previous manifests and matched player identities; add public primary sources only when provenance and linkage are explicit. Freeze a chronological split and player-held-out evaluation before building new predictive features. Compare conventional measurements, identified capability estimates, and uncertainty-aware estimates at matched sample populations. Report missingness, coverage, calibration, and uncertainty intervals, including a negative predictive result. No player may appear in both training and evaluation through another drill attempt or linked record.

## Acquisition without sign-in assumptions

Search existing workspaces and provided repository manifests for source paths first. Discover primary official combine results, documented public roster/recruiting archives, and openly licensed tracking/video samples through anonymous URLs. Validate one file before expanding. Do not assume a Kaggle login, request manual downloads as the default workflow, or treat inaccessible licensed film as available. Retain URLs, bytes, hashes, retrieval timestamps, source identity namespaces, and licensing/access notes. Video decoding and geometric extraction need separate environment/version records. Limit initial acquisition to two hundred athletes or two gigabytes, whichever comes first.

The synthetic exact pilot uses four coefficients, twelve candidate conditions, at most 4096 panel subsets, and a two-minute replay budget. The first empirical batch should use no more than three prespecified target definitions and one frozen primary prediction outcome; broad exploratory searches belong in a separately labeled discovery report. Historical pressure-rate tests reportedly deteriorated by about 10.69% when combined movement features were added in one player-held-out comparison, while other retrospective improvements had intervals including zero. Recover the exact report before quoting those figures, and treat them as a warning against leakage and cherry-picking, not evidence that every future design must fail. A successful measurement-design result can be valuable even when no predictive advantage appears. The accepted artifact should say which capability becomes identifiable, how reliably it can be estimated, and whether that additional information actually improves the frozen external task.

## Distinguishing structural and statistical repairs

A new drill condition can add a missing row-space direction; repeated attempts at an existing condition can reduce uncertainty only under an explicit repeat-error model. Independent zero-mean noise, persistent calibration bias, and bounded adversarial errors produce different repetition benefits. Store the assumed dependence structure before comparing repeated and novel drills. For player evaluation, demand-distribution weights should be fixed from an external role definition or training population, not fitted to evaluation outcomes. If different football roles require different targets, report the role-specific target and missing-information witness rather than presenting one aggregate scalar as universal ability. A reliable identified score may still carry no incremental predictive information beyond conventional measurements, and that is a legitimate final result.


# NX30 - Ordered movement signatures

Status: proposed trajectory-feature and uncertainty pipeline, followed by a frozen empirical evaluation. This packet translates the user's older movement-language and noncommuting-history work into exact, order-sensitive geometry. It does not assume that order-sensitive features improve scouting prediction, that the historical segmentations are bundled, or that one algebraic signature identifies every physical trajectory.

## What order adds mathematically

For a piecewise-linear path \(X:[0,T]\to\mathbb R^d\), define first and second signature levels

\[
 S_i^{(1)}=\int dX_i,\qquad
 S_{ij}^{(2)}=\int_{s<t}dX_i(s)\,dX_j(t).
\]

Level one records displacement. Level two records the order in which channel increments occur. Its antisymmetric component \(A_{ij}=S_{ij}^{(2)}-S_{ji}^{(2)}\) is a doubled oriented-area statistic in the corresponding channel plane. If channels have different units, this area has their product units and requires an explicit scaling convention. The ordinary dot product of raw mixed-unit coefficients is not a justified metric.

For paths concatenated as \(X*Y\), Chen's identity at level two is

\[
 S^{(1)}(X*Y)=a+b,\qquad
 S^{(2)}(X*Y)=A+B+a\otimes b,
\]

where \((a,A)\) and \((b,B)\) are their truncated signatures. A straight increment \(v\) has signature \((v,\tfrac12v\otimes v)\). Therefore an exact streaming update is

\[
 A\leftarrow A+\tfrac12v\otimes v+a\otimes v,
 \qquad a\leftarrow a+v,
\]

using the old value of \(a\). Retain this order explicitly: updating \(a\) first gives the wrong cross term. Concatenation is associative but generally noncommutative. This is a concrete bridge to the operator-language work, without identifying a geometric path feature with an arbitrary action matrix.

## Exact order-sensitive example

Path \(P\) moves from \((0,0)\) to \((1,0)\) and then to \((1,1)\); path \(Q\) moves to \((0,1)\) and then to \((1,1)\). Both have the same endpoint, displacement, path length, and duration if each segment takes one unit. Nevertheless,

\[
 S^{(1)}(P)=S^{(1)}(Q)=(1,1),
\]
\[
 S^{(2)}(P)=\begin{pmatrix}1/2&1\\0&1/2\end{pmatrix},\qquad
 S^{(2)}(Q)=\begin{pmatrix}1/2&0\\1&1/2\end{pmatrix}.
\]

The doubled oriented-area statistics are plus one and minus one; conventional signed areas after straight-line closure are plus one-half and minus one-half. A two-dimensional rational segment-integral oracle must reproduce these values independently of the streaming update. Reversing the order of a braking and turning channel can therefore be visible even when totals agree, provided those channels and their physical interpretation have been defined and measured.

A monotone reparametrization of the same geometric path preserves these geometric integrals, so timing information must be included as a channel when timing matters. Translation does not change increment signatures. Scaling coordinates scales each level by the corresponding tensor factors. Truncation can leave different paths indistinguishable; even full geometric signatures have known equivalence limitations. Do not advertise universal trajectory reconstruction from level two. The initial pilot asks whether particular order contrasts are measured reliably and useful for one declared task.

## Segmentation uncertainty is a population

Let \(\Omega\) be the finite set of admissible phase segmentations, with \(X_\omega\) the path after applying segmentation \(\omega\). Retain the multiset

\[
 \mathcal S=\{(S(X_\omega),m_\omega):\omega\in\Omega\}
\]

or an exact compressed representation preserving multiplicities. Report the range of a feature, number of attainable values, and population-weighted summaries only under declared weights. A uniform distribution over segmentations is a modelling choice, not a biological probability. Replacing correlated trajectory variants by an independent feature box may be conservative and can create unattainable combinations; label that relaxation.

For a small finite population, exact enumeration is the oracle. For a large population, dynamic programming may compose phase signatures through Chen's identity, but state merging must preserve every future feature used by the target. Counting identical current summaries without proving closure can lose order information later. PerfectPower's historical completion/rank/unrank machinery motivates this extension; Singularity's `HeightPopulation` is specifically a graph-height population and should not be misrepresented as an existing generic segmentation engine.

## Verified source crosswalk and proposed schema

`src/singularity/experiment_design.py` provides rational Gram metrics, exact nearest-candidate checks, and the distinction between coefficient geometry and function-space geometry. `observability.py` provides chronological word conventions and independent certificate replay. `panels.py` provides finite experiment-pool comparisons. These support reliable representation and evaluation contracts, but no inspected current module is a complete trajectory signature extractor.

The inspected DynaComp `polynomial.py` provides exact sparse polynomial composition and bounded polynomial closure. It can represent low-order signature updates on a fixed channel space, although degree and term limits must remain explicit. Cross-repository code requires a pinned source and optional integration decision. Historical movement work reports many admissible segmentations, angular-progress alignment improvements, and earlier negative predictive tests; those reports are chat-derived leads, not reproduced measurements in this handoff.

Propose `applications/ordered_movement/` with `RationalPath`, `ChannelDefinition`, `TruncatedSignature`, `SegmentationPopulation`, and `SignatureUncertaintyReceipt`. APIs are `signature_level_two`, `chen_compose`, `signature_population`, and `feature_uncertainty`. Schemas include channel units, coordinate frame, sampling times, interpolation rule, scaling, segmentation constraints, original object identifiers, multiplicities, source hashes, and whether the output is exact, enclosed, or sampled. A missing sample and a zero increment are different states and must not be conflated.

## Three concrete acceptance pushes

**NX30-A - Exact geometry and composition.** Implement level-two streaming, direct segment integration, and Chen composition. Ship the two axis-order paths, a three-segment path, time augmentation, translation checks, and a nonuniform monotone reparametrization of the same piecewise-linear trace. Acceptance requires agreement between genuinely separate integration and streaming implementations, associative composition over rational paths, and a test that detects updating the first level too early.

**NX30-B - Exact segmentation population and robust features.** Use at most eight candidate breakpoints, three phases, and 1024 admissible segmentations. Preserve original segmentation identities and multiplicities. Compare compressed summaries with full enumeration; retain a case where current feature equality does not permit safe merging under later concatenation. Propagate uncertainty into one finite-candidate distinction, including a failure when the attainable feature sets overlap. A sampled feature range is not a certified complete range.

**NX30-C - Frozen movement prediction pilot.** Recover source manifests and verified athlete links, predeclare one outcome, and freeze chronological player-held-out evaluation. Compare conventional measurements, order-insensitive totals, ordered features, and uncertainty-aware ordered features on identical athletes. Acceptance includes feature reliability under admissible segmentations, matched-sample performance, calibration, and uncertainty intervals. No improvement is an acceptable result; post-hoc subgroup gains must remain exploratory until separately held out.

## Acquisition, budgets, and failure cases

First recover the user's existing movement extraction scripts, source manifests, and previous validation reports. Search supplied repositories and workspaces before downloading duplicates. Public primary combine results or openly licensed tracking/video examples can seed a fresh small pilot, but no Kaggle sign-in, licensed film account, or inaccessible private feed may be assumed. Record retrieval URLs, hashes, athlete identity namespaces, time bases, camera geometry, pixel-to-distance calibration, and data reuse conditions. Avoid combining unrelated recruiting and roster numeric identifiers. Start with twenty athletes or fifty video attempts and a two-gigabyte acquisition cap.

The exact kernel uses at most four channels, level two, sixty-four path segments, 1024 segmentation variants, and a two-minute replay budget. Higher signature levels grow exponentially in channel count and require a separate cost estimate. Camera motion, projection distortion, irregular sampling, smoothing, and phase-label leakage can generate spurious area contrasts. A signature can be perfectly computed from a poorly measured path. Earlier movement-feature studies reportedly improved extraction stability while worsening one held-out prediction comparison; preserve that negative result as the baseline context. The useful end product states which order contrasts are robustly observed and whether they survive an honest external predictive test.

## A reproducible feature-selection boundary

Do not expand channel count, signature level, smoothing settings, and outcome definitions simultaneously on the same held-out athletes. Freeze the extraction transform from training data, apply it unchanged to evaluation attempts, and retain all attempted feature families in the discovery log. Compare order-sensitive features with a baseline having the same channels, sampling, and normalization but discarding order; otherwise a gain could come from newly introduced measurements rather than ordering. Include a trajectory reversal and a reflection fixture to document sign conventions. If rotational alignment is estimated from a player's full future attempt, verify that the intended deployment also has that entire attempt available; a real-time forecast cannot use a future-defined frame.


# NX31 - Target-directed period transport

## Purpose, provenance, and current status

This is a proposed integration track, not an accepted result. Its aim is to make the period combinations needed by a particular question the primary computational object. The historical bridge is the user's August 2026 V11 account of an exact connection and validated transport engine exercised on a rank-four mirror-quintic family, together with the October PerfectPower observable-row construction. Those historical descriptions are context, not proof that the corresponding source or integral normalization is present in this archive. Inspect the companion-source manifest before importing an external engine. The current Singularity repository supplies exact finite-dimensional observation closure in `src/singularity/observability.py`, especially `OperatorSystem`, `observable_closure`, and `verify_certificate`. The pinned PerfectPower companion already supplies `DifferentialModule.observable` in `python/perfectpower/differential_modules.py` and `CurveFamily._observable`/`observable` in `python/perfectpower/curve_families.py`; the latter performs differential row closure and records apparent-singularity factors. Their integration into Singularity and validated target transport remain proposed.

The existing finite operator engine should remain stable. Put the proposed continuous-parameter adapter in a separate module, initially `src/singularity/period_observations.py`, and retain separate arithmetic backends for rational functions and validated numerical transport. No generic identity between graph-height states and geometric periods is asserted. The connection is the shared observable-closure operation.

## Objects and assumptions

Let \(K\) be a computable characteristic-zero coefficient field, initially \(\mathbb Q\). On a simply connected chart avoiding connection poles, a period vector satisfies

\[
\Pi'(t)=A(t)\Pi(t),\qquad A(t)\in K(t)^{n\times n}.
\]

The requested output is \(y(t)=c(t)\Pi(t)\), with \(c(t)\in K(t)^{1\times n}\). Distinguish three inputs: a formally supplied rational connection; a geometrically derived connection; and a connection with a specified integral period basis. They carry increasingly strong interpretations. Solving the first does not establish the other two.

Define the differential pullback of an observation row by

\[
\mathcal D_A(c)=c'+cA,\qquad c_0=c,\quad c_{j+1}=\mathcal D_A(c_j).
\]

Then \(y^{(j)}=c_j\Pi\). Over \(K(t)\), at most \(n\) rows can be independent. If the first dependence is

\[
c_r=\sum_{j=0}^{r-1}a_j(t)c_j,
\]

the target obeys \(y^{(r)}=\sum_{j<r}a_j(t)y^{(j)}\). This is a constructive scalar differential equation for the selected target. Its minimality is relative to the supplied connection module and output: special initial periods can satisfy a smaller equation. Exceptional parameter points at which chosen denominators or pivots vanish need another chart or explicit singular analysis.

## Why this matters conceptually

The full period vector can contain components irrelevant to the selected prediction. Observable differentiation asks which components are forced into the computation as the target evolves. It gives both a reduction and a precise list of additional information required to advance the target. This combines the user's target-first observability program with the older period-transport program without relying on an analogy between their underlying objects.

For multiple outputs, seed the closure with all their rows. Close under \(\mathcal D_A\), producing a basis matrix \(B(t)\) and a reduced connection \(T(t)\) satisfying \(B'+BA=TB\). NX33 develops the chart and quotient consequences. Here the initial deliverable is target reduction and validated prediction on a fixed regular chart.

## Exact worked example

Take

\[
A=\begin{pmatrix}0&1&0\\0&0&0\\0&0&2\end{pmatrix},\qquad c=(1,0,0).
\]

The output rows are \(c_0=(1,0,0)\), \(c_1=(0,1,0)\), and \(c_2=0\). Thus \(y''=0\), even though the third component evolves exponentially. For \(\Pi(0)=(a,b,d)^\top\), the answer is \(y(t)=a+bt\), independent of \(d\). A reduction preserving only \(y(0)\) would fail because the initial derivative \(b\) is also required. A target seeded by \((0,1,0)\) closes at dimension one. These are exact rational tests and expose both under-reduction and over-reduction errors.

## Proposed interface and records

Use a proposed `RationalConnection` record with field identifier, dimension, rational-function matrix, declared chart domain, and excluded denominators. `DifferentialObservation` supplies target rows and labels. `DifferentialClosure` returns basis rows, their derivative-coordinate matrix, row-reduction reconstruction data, and all denominator factors introduced during reduction. Serialize rational functions as coprime integer coefficient arrays with an explicit denominator, not floating-point strings. A separate `TransportContract` records the path, initial enclosure, arithmetic enclosure, and output error norm.

Do not require a symbolic algebra package in the core merely for this track. Begin with polynomial matrices or a small optional exact rational-function backend. If adopting companion code, preserve its license and pin its source revision. The packet specifies proposed names; they are not existing Singularity APIs.

## Three acceptance pushes

### NX31-A - Differential observation closure

Adapt the existing pinned PerfectPower differential-observable implementation for dimensions at most four and coefficient degrees at most six. Add a new backend only after documenting a concrete interoperability gap; do not duplicate the existing scalar-equation engine. Deliver the new module, focused tests, and a mathematical note deriving the scalar relation. Acceptance requires direct symbolic equality of every returned row identity, the exact three-state example above, a target with zero output, a full-dimensional case, and a parameter pivot requiring chart splitting. An independent oracle differentiates explicit polynomial solutions on nilpotent examples instead of calling the closure routine.

### NX31-B - Target transport with explicit error

Connect a verified external or newly bounded numerical transport routine on a regular chart. Return target intervals with initial-condition and numerical errors separated. Acceptance requires containment of an independently computed solution, propagation of uncertainty in all initially required derivative coordinates, and honest refusal when the path crosses an excluded pole. Start with rational/nilpotent examples; do not begin with a difficult geometric family.

### NX31-C - One source-grounded geometric application

Select a curve or period family whose source connection and independent period integral are actually available. Compare full transport, target-reduced transport, and direct quadrature under the same normalization. Publish setup-inclusive runtime and enclosure widths. If the mirror-quintic source cannot be recovered, retain that dependency as unavailable and finish on the supported family. No flux-vacuum claim follows without the separate integral symplectic basis and flux covectors.

## Resources, failure cases, and resume

Exact rational-function elimination can suffer coefficient swell. Record numerator and denominator degrees and bit lengths; impose a configurable work cap before determinant expansion. A smaller scalar equation can have worse numerical conditioning than the first-order system, so reduction is not automatically a speed or accuracy improvement. Singularities introduced by elimination may be apparent but still affect an implementation. Chart selection must distinguish them from singularities of the supplied connection.

Resume with NX31-A after checking existing companion capabilities. NX33 is a downstream conceptual integration, not a dependency that should block the fixed-chart pilot. Store the connection revision, target rows, chart, exact relation, independent oracle output, and measured cost in the session record. Mark this track accepted only after the three declared scopes have evidence, or explicitly narrow the accepted scope.


# NX32 - Monodromy as an experiment language

## Purpose and inherited work

This proposed track connects the user's October 2025 anchor-period and continuation-loop ideas to the later noncommuting arithmetic experiments and Singularity's finite operator closure. The useful question is precise: which period-state differences can be exposed by analytically continuing around an allowed collection of loops and reading declared linear functionals? It concerns continuation experiments in a specified mathematical family. It does not claim that a continuation loop is automatically a laboratory operation.

Reuse `src/singularity/observability.py` for the exact operator semantics and its `minimum_distinguishing_experiment` function for cheapest exact words. Use `src/singularity/robust_search.py` for bounded robust-margin search after checking current signatures. Reuse the chronological-word tests in `tests/test_observability.py` and the noncommuting terminal semantics in `src/singularity/terminal_moves.py`. The new adapter is proposed as `src/singularity/monodromy_experiments.py`. External geometric matrices require separate provenance; the toy matrices below do not supply that provenance.

## Mathematical objects

Fix a punctured parameter domain, a regular basepoint, a chosen basis of a rank-\(n\) local system, and allowed based loops \(\gamma_1,\ldots,\gamma_m\). Their certified transport matrices are \(T_i\). A state is an initial period vector \(v\), and an output is a row \(c_j\). For chronological word \(w=(i_1,\ldots,i_k)\), the state is \(T_{i_k}\cdots T_{i_1}v\) and the reading is

\[
r_{j,w}(v)=c_jT_{i_k}\cdots T_{i_1}v.
\]

The observation-row closure is finite-dimensional:

\[
W_0=\operatorname{span}\{c_j\},\qquad W_{r+1}=W_r+\sum_i W_rT_i.
\]

At stabilization, the annihilator is invisible under every allowed loop word. Although row extensions reverse the perspective on chronological composition, the retained witness must always be replayed with the state convention above. Reusing a generic row-space argument without replaying word order is an important failure mode.

If inverse loops are available, include \(T_i^{-1}\) with their own positive costs. Do not silently make every inverse free or assume every topological loop is in the available language. Homotopic words may represent the same matrix; a word certificate should record both the actual sequence and its matrix action.

## Gauge and interpretation

Under basis change \(v'=Sv\), the consistent transforms are

\[
T_i'=ST_iS^{-1},\qquad c_j'=c_jS^{-1}.
\]

Every reading is unchanged. Numerical equality of raw matrices in unrelated bases is therefore the wrong comparison. A target might be a marked period, a gauge-invariant pairing, or a supplied integral charge functional; each needs its own declared transformation law. Recovering an arbitrary complex period vector from exact observations is a formal question. Physical interpretations involving integral charges require a justified integral basis and pairing.

## Exact toy calculation

Let

\[
T_0=\begin{pmatrix}1&1\\0&1\end{pmatrix},\quad
T_1=\begin{pmatrix}1&0\\1&1\end{pmatrix},\quad
v=(1,0)^\top,\quad c=(1,0).
\]

First loop 0, then loop 1 gives \(T_1T_0v=(1,1)^\top\), hence reading 1. First loop 1, then loop 0 gives \(T_0T_1v=(2,1)^\top\), hence reading 2. Both words have the same action counts and length. Their distinction is entirely due to order. The direct row \(c\), together with \(cT_0=(1,1)\), spans the full two-dimensional dual. Thus every nonzero state difference has a distinguishing allowed experiment, although a particular difference may already be visible without a loop.

These matrices are a standalone algebraic example. Acceptance must not describe them as the monodromy of a specific family unless that identification is separately established.

## Proposed data model

A `MonodromyLanguage` record should hold a basepoint identifier, basis identifier, matrices with exact coefficient field, loop descriptions, observation rows, positive cost model, and a source revision. A `LoopWitness` includes a chronological word, exact product, output functional, state difference or candidate pair, and value. A geometric witness adds path discretization, local continuation bounds, singularity-avoidance evidence, and the transformation taking the computed basis to the declared basis.

For algebraic-number matrices, initially use a common explicit number field or a cyclotomic field already supported by a companion implementation. Do not cast them into rational arithmetic by numerical rounding. An approximate matrix with interval entries requires an approximate robustness contract; the rational closure theorem cannot silently certify it.

## Three acceptance pushes

### NX32-A - Exact loop-language adapter

Implement the adapter around existing operator closure. Deliver the exact toy example, gauge-transformed copies, inverse-loop validation, and a source schema. Acceptance requires chronological replay of every returned word and exact equality of all readings under several invertible rational basis changes. Exhaustive words through length six provide an independent finite comparison, while invariant closure supplies the all-future statement.

### NX32-B - Costed and robust continuation experiments

Assign costs reflecting a declared continuation workload, initially loop counts and later path length or precision. Return cheapest distinguishing words and finite-budget robust alternatives. Acceptance requires exhaustive agreement on the toy language, including a case in which the cheapest nonzero response is poorly conditioned and a more expensive response tolerates larger error. Report the scalar error model used in the comparison.

### NX32-C - Actual monodromy source integration

Choose a recovered, explicitly normalized family. Bind the matrices to source equations and paths. Compare exact matrix relations with independently validated continuation around the loops. Record the representation relations actually checked. If exact recovery from numerics requires integrality, prove or supply the prerequisite lattice normalization; otherwise retain validated enclosures and a correspondingly limited statement.

## Resource and research boundaries

Word enumeration grows exponentially; exact span closure grows only to the finite state dimension, but rational or algebraic coefficient growth can dominate. Retain dimensions, field degrees, denominator sizes, and matrix bit lengths. A finite loop alphabet may reveal less than the full monodromy group. That is an experimentally meaningful limitation, not an implementation defect.

The most useful research output is a gauge-covariant observability statement for a concrete local system, with an explicit word exposing a previously hidden target. It is stronger than reporting noncommuting matrices and narrower than reconstructing an entire geometric object from its monodromy. Resume with NX32-A after checking the cost engine; defer geometric claims until NX32-C has an actual source and normalization.


# NX33 - Moving observable quotients

## Purpose and status

This proposed track gives a precise mathematical form to the user's older ambient-system, quotient, obstruction, lift, gauge, and holonomy chain. It combines the present finite operator quotient with the differential pullback in NX31. The goal is an exact reduced system whose meaningful coordinates can vary over parameter space. No canonical manifold, motivic identification, or universal physical reduction is assumed.

The existing algebraic model is `src/singularity/observability.py`: a basis matrix \(B\) has closed updates \(BM_i=T_iB\). The differential, parameter-dependent construction below is proposed as `src/singularity/moving_quotients.py`. It should use an optional exact rational-function adapter rather than perturbing the rational finite-operator engine. Read NX31 and the source interface inventory before coding.

## Derivation of the compatibility condition

Let \(x'=A(t)x\), where \(A\) is a matrix of regular functions on a chart. Let \(B(t)\) have constant row rank \(r\), and define reduced coordinates \(z=B(t)x\). Differentiation gives

\[
z'=(B'+BA)x.
\]

An exact closed reduced law \(z'=T(t)z\) exists if and only if

\[
\boxed{B'+BA=TB.}
\]

Pointwise, this means every vector in \(\ker B\) is annihilated by \(B'+BA\). On a constant-rank chart, a regular right inverse or a nonvanishing pivot minor gives regular coefficients for \(T\). Because \(B\) is surjective onto the reduced coordinate space, \(T\) is unique when it exists. A pointwise identity at one parameter value does not establish closure on a neighbourhood.

There is a geometric interpretation that can be checked without invoking additional geometry. A horizontal hidden state satisfies \(x'=Ax\). If initially \(Bx=0\), closure gives \((Bx)'=T(Bx)\), so it remains hidden. Thus the moving kernel is preserved by transport. Conversely, failure of the displayed factorization supplies a direction that is currently invisible but changes a future reduced observation.

## Gauge transformation

If \(\widetilde z=G(t)z\) for invertible \(G(t)\), then

\[
\widetilde B=GB,\qquad
\widetilde T=G'G^{-1}+GTG^{-1}.
\]

The derivative term is essential. Conjugation alone is correct only for constant \(G\). This is the same transformation law encountered for a connection. It gives a direct way to join chartwise observable reductions while preserving target predictions.

For an original target \(y=c(t)x\), exact recovery through the reduction additionally requires \(c=LB\). Then \(y=Lz\); the target row \(L\) must transform as \(\widetilde L=LG^{-1}\). Preserve this output condition separately from dynamic closure. A closed reduction can still omit the requested target.

## Exact examples and obstruction

Take \(B(t)=(1,t)\) and

\[
A=\begin{pmatrix}0&-1\\0&0\end{pmatrix}.
\]

Then \(B'=(0,1)\), \(BA=(0,-1)\), and \(B'+BA=0\). The one-dimensional reduced law is \(z'=0\). Explicitly, \(x_2=b\), \(x_1=a-bt\), so \(x_1+tx_2=a\). The coordinates move but the retained information is exactly constant.

Now use the same \(B\) with \(A=\operatorname{diag}(0,1)\). Then \(B'+BA=(0,1+t)\). No scalar \(T\) can satisfy \((0,1+t)=T(1,t)\) on an interval: the first coordinate forces \(T=0\), while the second is generally nonzero. The hidden vector \((-t,1)^\top\) is exposed at rate \(1+t\). At \(t=-1\) that instantaneous rate vanishes, but this isolated equality does not create a closed reduction nearby.

As a gauge test on the first example, choose \(G(t)=1+t\) on a chart avoiding \(-1\). Then \(\widetilde T=1/(1+t)\), and \(\widetilde z=(1+t)a\). A checker missing the derivative term will reject this correct prediction or incorrectly claim \(\widetilde z\) is constant.

## Proposed records and algorithms

Define a proposed `MovingQuotient` with source connection, basis rows, reduced connection, target factorization, chart domain, excluded factors, and exact identity witnesses. Initially take rational-function entries and reduce identities to polynomial numerators after denominators are cleared. Denominator clearing must retain the excluded set; a cleared polynomial identity never licenses evaluation where the original expression is undefined.

For a fixed target seed, use repeated \(c\mapsto c'+cA\) as in NX31. This constructs a closed observable submodule on a regular chart. For a user-supplied proposed reduction, directly test whether each row of \(B'+BA\) lies in the row span of \(B\). On failure, return a rational-function hidden direction or a rational sample where the obstruction is nonzero. A sample demonstrates failure; it does not prove closure.

## Three acceptance pushes

### NX33-A - Exact compatibility and obstruction

Deliver an identity checker and a constructor for the reduced connection on a chosen regular chart. Acceptance includes both examples above, zero and full-rank cases, a reduction that closes but loses its target, and a polynomial identity valid only after an explicitly recorded exclusion. Independently compare with explicit solutions for nilpotent or diagonal source systems.

### NX33-B - Chart and gauge transport

Implement overlap transformations between two reductions of the same constant-rank observable subspace. Verify \(\widetilde B=GB\), the derivative gauge law, and target transformation. Acceptance requires transport along two subdivided paths to give compatible target enclosures and deliberately corrupted overlap maps to fail exact identities. A chart singularity must trigger a switch or refusal, not an unbounded numerical division.

### NX33-C - One integrated parameter-family application

Choose a source-grounded parameter-dependent dynamical or period family. Publish the observable rank strata, reductions on regular cells, overlap maps, and an example of hidden-information leakage when an invalid smaller reduction is attempted. Include independently checked target predictions. Claims about loop holonomy require actual continuation around a valid loop, not merely a local gauge formula.

## Complexity, limits, and resume

Rank may jump at exceptional parameters. A global vector bundle of fixed rank cannot be assumed across such points; stratify the domain and state what is compared on each stratum. Differentiation and rational elimination can grow polynomial degrees substantially, so begin with dimension at most four and low-degree entries. Multi-parameter connections require compatibility in each direction and the relevant integrability conditions; one-parameter acceptance does not settle that extension.

Resume with NX33-A after the rational-function representation in NX31 is stable. The proposed theorem is a compatibility criterion under explicit regularity and rank hypotheses. Its value to the wider program is operational: it tells the compiler exactly when a parameter-varying reduction remains sufficient and exactly what obstruction requires enrichment.


# NX34 - Larger certified analytic visibility regions

## Purpose and existing baseline

This proposed track returns to the original analytic purpose of Singularity: explaining where a first unmatched local graph coefficient becomes visible in a primewise lift. The real-axis comparison is already established. Do not repackage its proof as a new result. Read `docs/chapters/07_visibility_singularities.md`, `src/singularity/arithmetic.py`, `src/singularity/certified.py`, `scripts/certified_k.py`, and their tests. The existing explicit complex discs are deliberately small because the derivative bound for small-prime factors is crude. This track replaces that bottleneck with validated local zero analysis.

The historical bridge is the user's October 2025 instruction to put a Cauchy/residue gate before geometric interpretations, together with the later validated-transport work. The new deliverable is a larger rigorously supported continuation neighbourhood, not a claim of global continuation or discovery of a new physical pole.

## Analytic setting

For a fixed finite graph and \(q\in[0,1]\), write

\[
F_G(z,q)=\sum_{n\ge0}a_{G,n}(q)z^n.
\]

For a \(k\)-vertex graph with \(k\ge1\), nonnegative weights imply

\[
0\le a_{G,n}(q)\le\binom{n+k-1}{k-1}.
\]

Consequently the series converges absolutely for \(\lvert z\rvert<1\). With \(P_N(z,q)=\sum_{n=0}^N a_{G,n}(q)z^n\), a sufficient uniform tail on \(\lvert z\rvert\le r<1\) is

\[
T_N(r)=(1-r)^{-k}-\sum_{n=0}^N\binom{n+k-1}{k-1}r^n.
\]

This is an exact rational expression when \(r\) is rational. It is conservative because it ignores graph energy. Better source-bound coefficients or weighted tail estimates can replace it only with a recorded proof. The same absolute coefficient bound works for complex \(q\) with \(\lvert q\rvert\le1\), but does not justify arbitrary complex energy parameters outside that domain.

## The zero-count mechanism

Let \(D\) be a bounded Jordan domain, with its closure contained in \(\lvert z\rvert\le r<1\). If

\[
\inf_{z\in\partial D}\lvert P_N(z,q)\rvert>T_N(r),
\]

Rouche's theorem gives the same number of zeros for \(P_N\) and \(F_G\) inside \(D\), counting multiplicities. To conclude that \(F_G\) is zero-free, separately certify that \(P_N\) has zero zeros there. A boundary comparison alone does not supply this missing root count. Alternatively, a certified lower bound for \(\lvert P_N\rvert\) throughout the whole domain that strictly exceeds \(T_N(r)\) gives a direct zero-free bound.

For the Euler comparison, the local arguments are \(z=p^{-s}=\exp(-s\log p)\). Enclose the image of the proposed \(s\)-disc for finitely many small primes. Certify numerator and denominator factors on the corresponding local domains, then control the large-prime logarithmic tail uniformly. Start from `arithmetic.complex_disc_certificate` and its existing holomorphic-tail theorem; a real-axis remainder helper alone does not establish the needed complex estimate. Treat the branch of each fractional power explicitly. A zero-free local factor and a chosen basepoint allow a consistent logarithm on a simply connected disc.

## Exact sanity example

For \(F(z)=(1-z)^{-1}\), take \(P_3=1+z+z^2+z^3\). On \(\lvert z\rvert=1/2\),

\[
\lvert P_3(z)\rvert=\frac{\lvert1-z^4\rvert}{\lvert1-z\rvert}
\ge\frac{1-1/16}{3/2}=\frac58,
\quad
\lvert F-P_3\rvert\le\frac{1/16}{1/2}=\frac18.
\]

The three roots of \(P_3\) lie on the unit circle, so the polynomial is zero-free in this half-radius disc. Thus the two independent premises are both checked. A deliberately chosen polynomial with an interior zero should pass an appropriate same-zero-count comparison but must never receive a zero-free certificate.

## Proposed software and evidence

Add an optional validated-complex module, initially `src/singularity/complex_visibility.py`, rather than forcing floating-point interval libraries into the standard-library core. The certificate should contain graph identity, coefficient source, fixed parameter, truncation, local domain, tail bound, root-count method, boundary subdivision, and all strict comparison endpoints. Rational rectangles or discs are preferable to unrecorded floating-point plots.

A polynomial root-count routine may use a certified argument principle, exact transformations to real-algebraic tests, or a suitable independently audited interval library. Record which route is used. Refusing a coarse subdivision is a computational limitation; it is not evidence of a zero. The existing algebraic and real-analytic records remain unchanged.

## Three acceptance pushes

### NX34-A - Local series tail and zero-free certificates

Implement exact combinatorial tails and validated bounds for a declared small polynomial/domain class. Deliver the geometric-series example, a case with a genuine zero, a case in which subdivision is necessary, and tests against independently known polynomial root locations. Separate `zero_count` from `zero_free` in the result schema.

### NX34-B - Small-prime image transport

Map a proposed complex \(s\)-disc into certified local \(z\)-domains for each retained small prime. Check factor nonvanishing and logarithm branches. Independently compare pointwise enclosures at rational sample parameters, but use domain bounds for the actual theorem. Record directed rounding and transcendental-function bounds; ordinary complex floating point is only exploratory.

### NX34-C - Improved retained visibility region

For a reference graph pair, combine local certificates with the existing large-prime tail machinery and publish a strictly larger disc than its current retained certificate. Report which bound limits the new radius. If improvement fails, retain the exact local obstructions and a bounded negative method result rather than claiming the actual analytic domain is small. Distinguish a fractional branch point from a pole whenever the discrepancy exponent is nonintegral.

## Resources and resume

The prime-two factor near the critical point may require a high coefficient cutoff. Use separator or support compilation only when its arithmetic contract matches the desired interval calculation. Exact positive-real coefficient data do not automatically provide stable complex cancellation bounds. Start with the cheapest reference pair and estimate coefficient, interval-subdivision, and prime-cutoff work before raising all three.

Resume with NX34-A independently of the thermal application. Existing formal real-axis proofs need not be rerun as a substitute for the new complex-domain evidence. Keep new analytic hypotheses in the manuscript and distinguish proved inequalities, validated finite computations, and exploratory radius searches.


# NX35 - Proof-directed computational refinement

## Purpose and existing connections

This proposed integration asks the experiment optimizer to decide where better simulation is worth its cost. It joins DynaComp error contracts, PerfectPower finite optimization, and Singularity robust experiment panels. Existing implementation references are `src/singularity/experiment_design.py`, `src/singularity/panels.py`, `src/singularity/robust_search.py`, and `src/singularity/thermal_diagnostics.py`. Read the actual signatures before extending them. The new orchestrator is proposed as `src/singularity/refinement_planner.py`.

The goal is decision correctness and, in a finite declared catalogue, decision optimality. Computing every model at maximum fidelity is one possible baseline, but it should not be the only route to a proof. A sufficiently wide discrepancy can be certified with a cheap bound. Precision is needed when it can change feasibility or eliminate a cheaper competitor.

## Scope of the initial theorem

Initially use a finite experiment pool, positive rational experiment costs, and independent scalar interval observations whose robust pair coverage is represented by masks. For experiment \(e\) and candidate pair \(a,b\), define

\[
m_{e,ab}=\lvert r_{e,a}-r_{e,b}\rvert-\rho_{e,a}-\rho_{e,b}.
\]

Strictly positive margin means that experiment robustly separates the pair. A panel identifies all requested target classes when its covered-pair union contains the required pair universe. This reduction is valid for the declared scalar box model. Joint correlated uncertainty can separate through combinations even when no individual coordinate separates; NX02 therefore requires a richer panel-separation oracle and must not be silently forced into this mask theorem.

Suppose computation returns certified margin enclosures \([m^-_{e,ab},m^+_{e,ab}]\). Define

\[
S_e^- =\{ab:m^-_{e,ab}>0\},\qquad
S_e^+ =\{ab:m^+_{e,ab}>0\}.
\]

The true coverage lies between these sets. An optimistic minimum-cover problem using \(S_e^+\) gives a lower bound on the true optimum; a feasible cover using \(S_e^-\) gives an upper bound. Thus

\[
\operatorname{OPT}(S^+)\le\operatorname{OPT}(S)\le
\operatorname{cost}(E^-).
\]

If lower and upper bounds coincide, a concrete certainly feasible panel is globally optimal within the declared pool. This conclusion does not require every margin to be precisely evaluated.

## Conceptual explanation

The optimizer maintains two worlds. In the optimistic world, every unresolved test is granted every separation it might still achieve. In the conservative world, only proved separations count. If even the optimistic world cannot beat a known conservative plan, more numerical work cannot improve the decision. Otherwise refine computations that support the currently threatening cheaper plan.

Refinement must tighten a justified enclosure. Increasing decimal digits without changing a bound on source or reduction error may leave the interval unchanged. Track the separate error contributions so the planner can buy the kind of accuracy that matters: more states, a better source model, more arithmetic precision, or an additional physical observation.

## Small exact example

Take candidates \(a,b,c\) and required pairs \(ab,ac,bc\). Test \(e_1\) costs 1 and truly reads \((0,1,1)\); test \(e_2\) costs 1 and reads \((0,0,1)\). Test \(e_3\) costs 3 and reads three distinct values. With zero error, \(e_1\) covers \(ab,ac\), \(e_2\) covers \(ac,bc\), and \(e_3\) covers all pairs.

Initially a coarse enclosure for \(e_1\) may leave \(bc\) unresolved, making the optimistic optimum 1. The certain panel \(\{e_1,e_2\}\) costs 2. Refine only the unresolved \(bc\) margin of \(e_1\), proving it is zero. The optimistic lower bound becomes 2 and matches the existing feasible upper bound. No high-fidelity computation of the expensive test is needed to certify optimality.

Include sensor error in realistic examples: equality at the separation threshold never counts as coverage. Use exact rational endpoint comparisons, including the distinction between \(m=0\) and \(m>0\).

## Proposed records and scheduling

A `MarginOracle` returns candidate IDs, experiment ID, model revision, fidelity choice, predicted intervals, uncertainty contributions, and margin bounds. `RefinementState` contains current enclosures, certain/possible masks, an incumbent panel, an optimistic lower-bound witness, and a reproducible refinement queue. `DecisionCertificate` records the terminal equality or the unresolved gap.

Begin with deterministic refinement choices: choose an unresolved pair in a cheapest optimistic competitor, break ties by estimated refinement cost, and stop at declared work limits. More sophisticated value-of-computation policies are a later experiment. They must not affect the soundness of the bound logic. A work refusal returns a valid incumbent and gap, not a fabricated optimum.

## Three acceptance pushes

### NX35-A - Enclosure-to-coverage bounds

Implement strict margin classification and optimistic/conservative cover construction. Deliver the exact example and cases with equality, negative bounds, zero-radius candidates, and inconsistent oracle records. Independently enumerate every panel in tiny pools to verify both bounding inequalities.

### NX35-B - Deterministic refinement planner

Implement an explicit bounded queue and incumbent/lower-bound updates. Acceptance requires the same optimum as exhaustive full-fidelity search, monotone enclosures or recorded reconciliation of different valid bounds, and a retained instance with fewer full evaluations. Report total setup and refinement work, not only the count of cheap oracle calls.

### NX35-C - DynaComp/thermal integration

Use actual source-bound error contracts for several fidelity choices on the existing thermal application. Compare the chosen experiment and finite-pool optimum with full exact predictions. Each fault/sensor/reduction combination must carry an appropriate bound; the nominal model certificate cannot be reused without justification. Retain a case where arithmetic refinement fails to help because source uncertainty dominates.

## Complexity, boundaries, and resume

Minimum weighted set cover remains combinatorial. For small candidate counts, pair-mask dynamic programming is practical; for larger populations use the exact bounded planner with explicit lower bounds and time limits. Oracle memoization must include model, candidate, sensor, input word, and uncertainty contract. A cached answer from a different reset convention is invalid even when the nominal numerical reading happens to match.

Resume after NX01 and NX09 establish the scalar uncertainty and fidelity interfaces. NX12 supplies a larger legal protocol population but is optional for a first finite-pool demonstration. The accepted statement should explicitly name the pool, target pairs, costs, uncertainty geometry, and computations actually refined.


# NX36 - End-to-end experiment certificates

## Purpose and scope

This proposed track makes a completed experimental decision independently checkable from its declared mathematical inputs. It extends the project's existing exact closure, graph certificate, formal, and cost evidence with uncertainty-set separation and finite-panel optimality. It is not a request for a new permission workflow or a promise that a software certificate establishes physical calibration. The point is that another implementation can check the result without trusting the optimizer's search history.

Read `src/singularity/observability.py`, `src/singularity/certificates.py`, `src/singularity/experiment_design.py`, `src/singularity/panels.py`, `formal/README.md`, and the actual Lean source tree. The generic closure theorem and natural-number cost arguments already exist in scoped form. The new work is the composed robust decision layer, including the original candidate population and uncertainty semantics.

## Claim to be checked

For a finite declared candidate population \(\Omega\), target map \(T\), and admissible observation sets \(\mathcal Y_{c,E}\), robust identification by panel \(E\) means

\[
T(a)\ne T(b)\Longrightarrow
\mathcal Y_{a,E}\cap\mathcal Y_{b,E}=\varnothing.
\]

For a finite experiment catalogue with specified costs, optimality additionally means no cheaper admissible panel meets that condition. These are separate obligations. A feasible panel without a lower-bound argument is not certified optimal. A cost lower bound without a feasible witness is not a diagnostic plan.

The initial checker should accept scalar interval geometry, where strict separation has a short exact rational proof, then separately support zonotope contrasts. For symmetric zonotopes, a witness \(w\) verifies disjointness if

\[
\lvert w^\top(\mu_a-\mu_b)\rvert>
\lVert G_a^\top w\rVert_1+
\lVert G_b^\top w\rVert_1.
\]

All terms are rational when the data and witness are rational. This supplies a compact separation proof without requiring the checker to rerun a linear optimizer. General feasibility or infeasibility certificates require the corresponding exact primal or Farkas-style dual data and validated dimensions.

## Original-object semantics

Keep a map from every original candidate ID to its compiled state and target label. Two candidates may share a compiled state only when all claims preserve the relevant target and experiment semantics. Never deduplicate the fault population merely because nominal predictions agree. Multiplicities matter for counts and priors even when two candidates are observationally equivalent.

A closure certificate can establish that future permitted operations add no new distinctions at a fixed budget. A finite panel certificate establishes separation for its selected tests. A measurement-error certificate supplies the possible readings. A source map binds those tests to the stated model. Their composition is valid only when their candidate IDs, parameter, normalizations, reset convention, operator order, and units agree. Treat these as typed fields, not prose that the checker ignores.

## Proposed schema

Use the proposed namespace `nx.experiment_decision/1`, leaving existing `singularity.certificate/1` records unchanged. A record contains schema version, source revisions, finite population description or reconstruction witness, target labels, model and experiment definitions, exact costs, uncertainty contract, selected panel or policy, pair-separation witnesses, and an optimality witness. Rational numbers use normalized integer numerator/positive-denominator pairs. Floats are invalid in exact fields.

The verifier must reject unknown mandatory semantics, malformed dimensions, duplicate candidate IDs, nonpositive denominators, unsupported error norms, and mismatched resets. A source digest supports integrity and binding; it does not itself prove a mathematical equation or authenticate real-world data. If a certificate references an external model bound as a premise, display that premise in the accepted claim.

## Exact example

Take two candidates with output intervals \([0,1/10]\) and \([3/10,4/10]\) under experiment \(e\), costing 2. Their positive gap is \(1/5\). Suppose every catalogue experiment cheaper than 2 has intersecting candidate intervals and no combination of them is cheaper and separating. A complete finite lower-bound witness plus the interval gap proves that \(e\) is optimal. Changing the second interval to \([1/10,2/10]\) makes the sets meet at one endpoint. A strict-disjointness checker must reject the old witness even though the interval centres differ.

For a tiny catalogue, exhaustive panel enumeration is the best independent oracle. Larger cases may carry a pair-mask dynamic-program table or a branch-and-bound proof tree. The checker validates local transitions and terminal bounds, not a bare `optimal=true` flag.

## Three acceptance pushes

### NX36-A - Exact robust feasibility records

Implement strict scalar-interval and rational-contrast checkers in a proposed `src/singularity/decision_certificates.py`. Deliver schema documentation, finite examples, serialization round trips, and an independent direct-set checker for tiny cases. Deliberately alter costs, endpoints, target labels, dimensions, and source bindings; every alteration that invalidates the claim must be rejected. Avoid tests that only mirror parser branches.

### NX36-B - Optimality and reconstruction composition

Add a finite-pool lower-bound certificate and original-population reconstruction checks. Verify the complete toy catalogue by independent enumeration, then retain one thermal result. Distinguish a catalogue optimum from an optimum over all legal protocols. If the catalogue is generated by NX12, bind the completeness evidence or state the finite-pool limitation explicitly.

### NX36-C - Scoped formal theorem and release integration

Formalize the finite soundness statement connecting accepted pair-separation witnesses and a cost lower bound to target identification and optimality. Reuse existing finite operator facts where their hypotheses match; rational cost scaling needs an explicit positive common denominator if a natural-number cost theorem is used. Compile the actual proof files and report their coverage. No blanket statement about the Python optimizer, external interval engine, or physical model should follow from a narrower checker theorem.

## Complexity and operational delivery

A certificate should be substantially easier to check than to discover, but this is an objective to measure rather than an automatic theorem. Record proof-table size, rational bit lengths, checker time, and optimizer time. Exponential certificate growth can erase the benefit on large panels. Begin with small exact populations and allow declared budgets.

The final user-facing decision should state the target, selected experiment, cost, supported error range, and unresolved equivalences in plain words. Keep implementation hashes and proof tables in the downloadable evidence. They should support the decision without becoming the product's primary interface.

Resume after the scalar interval layer of NX01 and the bound logic of NX35 exist. NX02 is required only for the zonotope extension. This track is accepted when its exact scope is independently replayable, its formal claims compile where stated, and its complete package contains the model assumptions and reconstruction data needed to interpret the result.


# Historical bridges behind NX01-NX36

This document preserves the mathematical connections that motivated the roadmap. It summarizes older conversations retrieved for the planning discussion and relates them to actual pinned companion source files. It is **not** an export of the original conversations, a new proof of an old claim, or a claim that all old datasets are bundled. Source files take precedence for current API and implementation behavior; the old conversation record supplies intent, examples, and ideas that may not yet have become source.

The historical material spans the quotient/obstruction/geometric program of late 2025 and April 2026, the August 2026 exact-connection/transport work, September 2026 WIND and multiscale design, and the October 2026 arithmetic, observational, movement and dynamical programs. Speculative geometric correspondences in older chats are not treated as established identifications. Proposed NX bridges are new work even when every ingredient already has a working implementation elsewhere.

## Reading rule and provenance levels

The authoritative current Singularity baseline is pinned separately by the main handoff. Companion DynaComp, PerfectJet and PerfectPower sources have exact per-file identities in `COMPANION_SOURCES.json`. A historical mathematical formula below may be an existing theorem under specified assumptions, an exact finite experiment, or a design suggestion. These statuses must remain distinct. In particular, finite formal-vector blindness is not a graph realization; target observability is not predictive accuracy; source-complete selected modules do not mean the full application and external runtime assets have been included.

| Tracks | Historical anchor and status | Mathematical mechanism carried forward | What remains to be built or independently checked |
|---|---|---|---|
| NX01 | October DynaComp uniform/validated output bounds; actual pinned implementation | Preserve the candidate-specific radius \(\rho_{c,e}\) instead of replacing all radii with a maximum. Scalar guaranteed separation is \(\lvert r_{a,e}-r_{b,e}\rvert>\rho_{a,e}+\rho_{b,e}\). | Rebuild pair coverage and the optimization receipt under the sharper contract. The new optimum can equal the old one; an improvement is not assumed. |
| NX02 | DynaComp correlated zonotopes; older SOE observation fibres | A panel has a joint feasible set \(\mu_c+G_c[-1,1]^p\). Shared disturbances can cancel in a contrast, while separately widened intervals lose that information. | Source and validate the correlation assumptions. Persistent ambient error differs from an independently redrawn sensor error. Test exact intersection and separating contrasts. |
| NX03, NX12 | October 2026 PerfectPower completion planning, integer populations, original-object ranking | Completion counts support counting, rank/unrank, conditional populations and optimization without visiting every original object. The selected source includes completion planning and its state quotient. | Compile fault populations and legal protocol languages. Count each original configuration once. A count is not a probability without a prior. The full large Petersen population computation is not newly formalized by copying the source. |
| NX04 | PerfectJet parameter strata, fibres and calibration; DynaComp parameter families | Competing fault hypotheses each describe a set of nuisance parameters. Separation compares complete observation sets, potentially with different nuisance values under the two hypotheses. | Detectability thresholds must exclude arbitrarily tiny faults if nominal and faulty families touch. A shared-nuisance comparison answers a different question from independent nuisance freedom. |
| NX05 | PerfectJet Observatory adaptive examples, October 2026 | A contingent second experiment can distinguish candidates that a fixed schedule cannot distinguish at the same cost. The source includes the branching-lab fixture and exact adaptive routines. | Extend to uncertainty intervals and finite observation cells; certify worst-case or prior-weighted policy cost. Do not conflate the older example with two adaptive probes versus three fixed probes with a later example having no successful fixed schedule. |
| NX06 | PerfectJet destructive actions and SOE history semantics | A belief must retain the initial target identity, current possible state, and full observation prefix. Reset can erase useful present-state distinctions. | Build shared-trajectory continuous-state diagnosis with a sound belief update. The current separately reset thermal panels are insufficient evidence for this extension. |
| NX07 | SOE action-language equivalence and PerfectJet all-future experiments; Singularity reflection example | Permanent blindness is relative to a declared sensor and intervention language. Purchasing a capability changes the language itself and can remove an invariant ambiguity. | Optimize installation plus repeated use. Breaking a symmetry is a useful necessary design step in a symmetric example, not an automatic completeness proof. |
| NX08 | September WIND and October SOE target identifiability | \(\ker H\subseteq\ker G\) is equivalent to a linear factorization \(G=LH\) on the declared finite-dimensional admissible space. The stable form asks for \(G^\top G\preceq\kappa^2H^\top H\). | Restrict to admissible state differences, normalize the physical units and error metric, and compute a target-specific condition certificate. Full rank alone gives no useful numerical margin. |
| NX09, NX35 | DynaComp reduction, native arithmetic and all-time error budgeting | Source, transformation, reduction, rounding and sensor errors can be composed into a justified output contract; coarse computations may already certify a design decision. | Prove compatibility of error terms, refine only unresolved comparisons, and include setup costs. A nominal reduced model is not automatically certified for changed faults, inputs or sensors. |
| NX10 | DynaComp FOREVER/stability work and Singularity's thermal diminishing returns | Stable dynamics supply an exact steady response plus a decaying tail. A Lyapunov metric can certify \(A^\top PA\preceq\gamma^2P\). | Derive experiment-specific late-time upper bounds. Fixed dynamics and arbitrary switching are different claims; the latter requires a suitable common or otherwise justified switching certificate. |
| NX11 | PerfectPower recurrences, PerfectJet accepted-history series and DynaComp minimal realizations | A finite linear physical-time system has rational transfer series \(C(I-zA)^{-1}B\); coefficient recurrences and matrix powers evaluate distant horizons. | Certify pairwise cancellation and a minimal realization, then compare independent far-index evaluations. This does not imply rationality of positive-parameter graph-height generating series. Bit growth remains part of cost. |
| NX13 | SOE partial machines, graph terminal extensions and charge introduce/forget/join semantics | Operators can map between typed spaces. Observable rows pull backward across a compatible attachment and invisible spaces push forward. | Prove completeness for a finite declared type grammar and volume budget. Do not silently identify different boundary conventions or permit illegal compositions. |
| NX14 | PerfectJet rank strata and Singularity's parameter-wide observability modules | Determinantal divisors describe genuine rank drops. One chosen generic basis minor can vanish even while another basis remains full rank. | Enlarge the certified budget and isolate all exceptional real parameters with denominator exclusions explicit. Finite sampled ranks are not a parameter-wide theorem. |
| NX15 | Singularity F49-F52 quotient and slice-rigidity development | Polynomial slice constraints tie formal interface coordinates together. A linear null vector may fail every graph's degree or charge consistency conditions. | Search actual graph pairs at the stated R=38 and R=11 frontiers or certify an exclusion in a declared bounded family. No current realizing pair is asserted. Arithmetic specialization and slice hypotheses must be carried into the search manifest. |
| NX16 | Singularity F55 connected-support locality and charge-aware compilation | Only local support terms meeting the modified vertices can change after an edge edit. Shared unchanged support shapes can reuse exact computations. | Implement incremental updates and compare with full recomputation for every retained edit. Enumerate support sets in a graph containing both edge versions so deleted-edge supports are not lost. |
| NX17 | DynaComp thermal Laplacian structure and the older reusable operator-transport idea | A bond modification is a rank-one update \(A_f=A_0+k\alpha bb^\top\); the resolvent follows an exact rank-one update identity. | Establish sign and convention from the actual plate source, handle multiple faults through a small matrix denominator, and benchmark exact bit size as well as arithmetic count. |
| NX18 | Singularity finite differences, Vandermonde restoration, and the polynomial-as-vector discussion | Distinct interpolation nodes guarantee invertibility, but inverse norms and rational denominators determine usable recovery. A polynomial norm requires its Gram matrix unless an orthonormal basis is used. | Quantify noise amplification, parameter sensitivity and bit complexity. Do not infer practical robustness from exact rank or advertise coordinate-count savings as an end-to-end speed theorem. |
| NX19 | PerfectPower integer fibres, saturated kernels, closest-integer ties and chart domains | Integer observational equivalence needs an image lattice, not merely a rational subspace. Smith data preserve divisibility and saturated fibres. | Recover all original bounded integer objects after compression and preserve rank/unrank. Chart denominators, divisibility guards and lattice index conditions are part of correctness. |
| NX20 | October Pell orbit powering, modular filters and arithmetic interferometer | A norm-one unit acts by \(\begin{pmatrix}a&Db\\b&a\end{pmatrix}\) on coefficients of \(x+y\sqrt D\); reduction modulo a declared modulus gives a finite experiment system. | Preserve seed classes and original coordinates. Completeness of all global Pell solutions requires justified seeds. Unit actions in one fixed quadratic field commute; noncommuting experiments require extra operators. |
| NX21 | October Weil commutant/orbit calculations, Coxeter phase work, thermal reflection | Symmetry projectors expose input/output channels. Reflection yields \(P_\pm=(I\pm P)/2\); a hidden channel needs an input or readout coupling to it. | Verify the actual group representation before applying any character formula. The Weil commutant counts from one representation are not dimensions of arbitrary thermal or graph quotients. The 384 primitive phases, eight eigenphases, 264 branches and 240 E8 roots are different objects. |
| NX22 | Singularity root-of-unity rationality and PerfectPower exact Fourier arithmetic | A sufficiently long discrete Fourier grid recovers a bounded energy polynomial from all its phase values. One phase alone can collapse substantial structure. | Prove the energy degree bound for the actual graph weights and volume convention, then independently reconstruct retained polynomials. Periodic-sector finite cutoffs do not establish positive-parameter completeness. |
| NX23 | PerfectJet history populations and older exact multiplicity compression | \(Z(u)=\sum_\omega w_\omega e^{u^\top f(\omega)}\) supplies expected features and covariance under declared positive weights. Original multiplicities survive compression. | Supply a defensible prior and likelihood for expected risk. Population count, expected information gain and worst-case target identification solve different optimization problems. Order-dependent targets need representations that retain order. |
| NX24 | The Vakil/Noetherian finite-prefix discussion and exact transition-closure work | Within a fixed algebraic parameter family, coefficient-difference ideals can stabilize; effective cutoffs require a mechanism controlling every later coefficient. | Prove a new explicit cutoff with a recurrence, algebraic transition closure or comparable certificate. Observing \(I_N=I_{N+1}\) once does not prove permanent stabilization. Finite coefficient-vector dimension by itself is insufficient. |
| NX25 | September WIND forecast-driver experiments, synthetic tests and archive acquisition | A future linear target has row \(g^\top F^\tau\). Present target observability need not imply future target observability. Driver measurements can be more informative for a forecast. | Use fixed censored observations and withheld real archive truth. The reported synthetic driver advantage is not a verified radar gain. The archive's 272 acquired volumes are not bundled here. |
| NX26 | WIND nonlinear ambiguity witnesses and SOE quadratic-fibre tests | For affine fibres \(x=x_0+Nz\), a quadratic target is constant exactly when its linear fibre term and \(N^\top QN\) vanish. More general fibres can retain curvature ambiguity after tangent tests pass. | Construct admissible matched-observation pairs and verify the requested target gap. Nonlinear constraint curvature must be included; a tangent-space rank test is only local. |
| NX27 | September multiscale mu-Arena and April quotient/manifold proposals | A fine/coarse evolution defect \(EF_f-F_cE\), together with Lipschitz propagation, bounds target error across scales. | Define the norm, transfer map, domain, boundary forcing and target. A Hilbert spectral-tail formula applies only under its actual approximation assumptions; old normally-hyperbolic persistence arguments do not supply a canonical physical coarse model automatically. |
| NX28 | September reduced HOx-NOx-VOC-ozone and aerosol design | Reactive transport couples advection, diffusion and reaction; conserved totals need not identify reaction progress or a species-specific target. | Begin with a small fully specified model and sensor catalogue. This handoff contains no new chemical calibration data, environmental validation or biological claim. |
| NX29 | October 14-15 movement stress-response model | The design vector \((1,s,a,sa)\) supplies four coefficients; a target \(h^\top\beta\) is identifiable precisely when \(h\) lies in the drill design's row space. | Select informative drill conditions and propagate measurement uncertainty. The historical 93.2% underidentified panels and 34.1% alignment-stability improvement are scoped old results, not a claim of predictive success. |
| NX30 | October ordered movement language and segmentation populations | Second-order antisymmetric trajectory integrals retain order lost by totals. Exact admissible segmentation populations describe feature uncertainty. | Predeclare one prediction question and use chronological, player-held-out evaluation. Older combined movement features worsened one held-out experiment by 10.69%; a new geometric feature is not assumed to reverse that result. Actual player data are not bundled. |
| NX31 | August V11 user-reported exact connection/validated transport and October PerfectPower period modules | For \(\Pi'=A\Pi\), observable derivatives obey \(c_{k+1}=c_k'+c_kA\). `DifferentialModule.observable` and `CurveFamily.observable` already implement scalar extraction; their bundled backend is `symmetry_quotients.PolynomialCurve.observable`. | Reuse existing scalar extraction and add target-specific validated transport and error contracts. Source the intended family, branch choices and normalization, compare full transport and independent quadrature. The old V11 workspace and its complete mirror-quintic data are not bundled. |
| NX32 | Late-2025 anchor periods, analytic continuation and the later noncommuting experiment engine | Monodromy acts as a loop language \(cT_{\gamma_m}\cdots T_{\gamma_1}\Pi\). Sequence order can matter. | Use certified matrices and path conventions; distinguish covariant conclusions from raw matrix equality in different gauges. Physical flux claims require the appropriate integral symplectic basis and physical covectors, still separate from an exact connection calculation. |
| NX33 | April 2026 quotient-obstruction-lift-gauge-holonomy chain | For \(z=B(t)x\), a closed reduced differential system exists when \(B'+BA=TB\). This is the moving-coordinate counterpart of finite operator closure. | Prove compatible reduced transport on constant-rank charts, test overlaps, and identify leakage when the closure equation fails. Rank-changing strata require separate treatment; old speculative universal geometric identifications are not prerequisites. |
| NX34 | Original Singularity Euler products and older analytic residue/Cauchy gates | A validated truncation and boundary tail can establish local zero information by Rouche's theorem, provided the comparison polynomial's zero count is known. | Enlarge a retained complex nonvanishing disc with explicit local-factor and prime-tail bounds. Fractional-power branch singularities are not poles, and a numerical plot is not a zero-count certificate. |
| NX36 | SOE Lean kernels, exact witnesses and source-bound release practice across the programs | A final decision can carry checked population semantics, legal actions, uncertainty separation and a lower-cost exclusion certificate. | Formalize the relevant finite decision layer and test deliberate corruption. Existing Lean proofs do not automatically verify Python search, physical calibration, external data acquisition or unbundled full-instance computations. |

## Most important design consequences

The project should preserve its earlier distinction between original objects and their compiled states. Compression is useful only when the target, future legal operations, uncertainty and required reconstruction remain valid. In the finite exact setting, closing observation rows under all permitted operators gives an all-future quotient. In a robust setting, span closure alone does not preserve the largest margin: a dependent row can still be a valuable low-noise experiment. In an integer population, a rational quotient alone can lose the image lattice. In an adaptive physical process, forgetting the initial target or a correlated disturbance can change the problem itself.

The older WIND work is particularly valuable because it supplies hard ambiguity rather than a convenient classification toy. A model can fit every available measurement and remain wrong about the desired tendency or future target. The movement work supplies a complementary failure mode: a representation can become more stable without becoming more predictive. Both require a target-specific experiment design and an independent empirical evaluation. They should be used as tests of the new methods, not as marketing claims inherited without rechecking.

The older geometric work supplies a different kind of bridge. Exact connection transport, monodromy loops and moving observation quotients can share operator machinery without asserting a universal physical correspondence between the underlying objects. The ambitious mathematical deliverable is a theorem with explicit domains, gauges and compatibility equations. A numerological resemblance among point counts or a speculative older identification is not a substitute.

## Missing material and reacquisition contract

WIND/NEXRAD volumes, the mu-Arena release archive and reactive-transport datasets are not bundled. NFL raw attempts, player identity joins, outcomes, chronological splits and admissible segmentations are not bundled. The old V11 connection workspace, integral H3 marking and physical flux covectors are not bundled. PerfectPower's large native planning population, all external arithmetic assets and full application catalogue are not bundled. None should be reconstructed from a prose statistic. Before a track uses one of these objects, acquire the exact source, save provenance and hashes, define the held-out or independent comparison, and update the track manifest with the actual object identity.

Existing source snapshots are reusable implementation evidence. Historical ideas are design context. New theorem statements, new experiments and new measured gains require their own receipts and must enter the NX ledger only after the corresponding acceptance contract has been met.


# Recovery, Git history, and release discipline

## Three distinct copies

The outer archive supplies a ready-to-read repository snapshot, a baseline Git bundle, and a readable handbook. The snapshot contains complete baseline source plus the new handoff; it intentionally omits `.git`, build caches, and recursive release archives. The Git bundle carries the baseline history and can initialize an offline checkout. The source manifest identifies every archived byte. None of these objects should overwrite a newer working tree without inspection.

For an existing connected checkout, fetch main, preserve user changes, and integrate the handoff at `handoff/nx36/`. Run its tools from that checkout. For a fresh online setup, clone the actual GitHub repository and compare the included handoff with the current tracked version. The handoff publication may already be on main by the time Claude begins.

For offline baseline recovery, from the extracted outer directory run:

```sh
git bundle verify baseline/Singularity-v040-baseline.bundle
git clone --branch nx36-source-baseline baseline/Singularity-v040-baseline.bundle recovered-singularity
```

Then copy the supplied `repository/handoff/nx36/` into the recovered checkout, preserving its other files. This overlays planning documents on the pinned baseline; it does not invent a Git ancestry for future published handoff commits. Before eventual online publication, set the origin to the actual project, fetch main, and integrate compatible newer commits. Never force-push an offline snapshot over newer work.

## Unit and session discipline

A track contains three acceptance units. The recommended default is at most three accepted units in one session. This is a bounded execution contract, not a three-commit cap. Several commits may be needed for one result; one commit may package several small accepted units. The user can explicitly authorize a wider scope. Do not interpret the existence of 108 proposed units as an unlimited unattended session.

The new ledger is separate from `handoff/push_status.json`. Do not renumber P01-P36, retroactively change their meanings, or mark a historical proposal P54 accepted because an NX packet is related to it. Keep mathematical results, roadmap units, commits, and network pushes distinguishable.

## Evidence and checkpoint

For each accepted unit record a summary of the actual result, existing artifact paths, check commands and scopes, mathematical status, and commit. Formal statements require compiled source with the claimed theorem and hypotheses. Exact finite computations need the declared population and independent comparison. Negative searches require explicit graph size, class, parameter, volume, and resource limits. Empirical improvements require the source data and evaluation split, not only a synthetic illustration.

Run checks appropriate to changed code. The baseline core suite and retained results remain useful; do not rerun every expensive global proof after a prose-only edit as a substitute for inspecting its mathematical content. Conversely, a documentation label cannot make untested executable changes safe to release. Record exactly what was run.

## Complete packages

Every research release should include source, the relevant manuscript, retained results, source/provenance definitions, and an exact checkpoint. Avoid recursive ZIP inclusion: package a single complete snapshot and optionally the clearly labelled baseline bundle. Update links when filenames change. Test a clean extraction and do not promise an archive that was never built.

Use the NX handoff build helper for reproducible handbook assembly and package validation. The final file hashes are integrity aids, not mathematical proofs. Do not claim remote CI success until the actual run has been observed. A successful local suite and a queued remote run are different facts.

## Resume record template

| Field | Required content |
|---|---|
| Source | Actual branch, commit, worktree state, and compatible remote head. |
| Accepted unit | NX ID and exact narrowed or complete scope. |
| Mathematics | Definitions, hypotheses, proof or finite result, and unresolved obligations. |
| Implementation | Actual public API and original-object semantics. |
| Independent comparison | Different route, population, and precise agreement claim. |
| Resources | Runtime, memory/state counts where relevant, and exhaustion behaviour. |
| Publication | Commit, push result, archive, readable document, and observed CI status. |
| Next | First dependency-ready unit and the exact file or command to start with. |

Keep the user-facing checkpoint concise and intelligible. The dense documents support the result; the final status should tell the user what changed, why it matters, and what is ready next.


# Independent mathematical review of NX31-NX36

## Scope and method

This review concerns the proposed handoff packets, not implementation of their future APIs. The reviewer read NX31 through NX36, inspected the cited Singularity source interfaces and formal coverage, and recomputed the displayed examples using Python standard-library `fractions.Fraction` and direct matrix arithmetic. The calculation did not import the implementation routines it was checking. SymPy was not installed and was not needed. No claim of formal verification, a new geometric-family result, or a full repository test run follows from this review.

The packet hypotheses are generally appropriately scoped. Historical period-engine descriptions are explicitly treated as context requiring source recovery. Proposed module paths are marked proposed. No missing path was found that was explicitly presented as an already-existing file. One existing-module capability cross-reference needs correction, and NX34 needs explicit analytic hypotheses and one stronger lower-bound phrase. These corrections were communicated to the primary agent; this report intentionally does not edit the packets.

## Review outcome table

| Packet | Core mathematics | Exact examples | Required clarification |
|---|---|---|---|
| NX31 | Differential observation recurrence and first-dependence closure are correct over the stated differential field. | Three-state example yields rows \((1,0,0),(0,1,0),0\), hence \(y''=0\). | Minimality concerns the connection module and chosen output, not every special solution; the packet already records this distinction. |
| NX32 | Chronological products, invariant row closure, and constant gauge law are correct. | Words 0 then 1 and 1 then 0 give states \((1,1)\) and \((2,1)\), readings 1 and 2. | Cheapest exact words live in `observability.minimum_distinguishing_experiment`; `experiment_design.rank_experiments` only ranks a supplied pool. |
| NX33 | Closure \(B'+BA=TB\), uniqueness under full row rank, and the derivative gauge term are correct. | Moving constant coordinate, leakage example, and gauge \(G=1+t\) all check. | Statements are chartwise and constant-rank; extension across rank drops is correctly left conditional. |
| NX34 | Coefficient majorant, tail, and Rouché mechanism are correct with explicit domain hypotheses. | Geometric example gives polynomial lower bound \(5/8\), tail \(1/8\), strict gap \(1/2\). | Require an admissible bounded contour/domain and \(\overline D\subseteq\{|z|\le r\}\), \(r<1\). A direct global lower bound must exceed the tail, not merely be positive. |
| NX35 | Certain/possible coverage inclusions and optimum sandwich are correct. | True optimum 2, initial optimistic lower bound 1, refined lower bound 2. | The theorem is for scalar-box pair masks; correlated panels require the different NX02 oracle, as already stated. |
| NX36 | Pairwise set disjointness gives target identification; feasibility and optimality are separate. | Interval gap is \(1/5\); changing an endpoint to create contact correctly invalidates strict separation. | Formal soundness must be restricted to the actual checker and its premises; the packet already avoids blanket Python or physical-model verification. |

## NX31: differential closure and target reduction

For \(\Pi'=A\Pi\) and a parameter-dependent row \(c\), the product rule gives \((c\Pi)'=(c'+cA)\Pi\). This validates the recurrence \(c_{j+1}=c_j'+c_jA\). Once the first row dependence occurs over \(K(t)\), the previous rows form a differential-stable span: differentiating a rational coefficient adds its derivative, and differentiating each retained row gives the next row or the displayed dependence. Thus the resulting scalar equation is valid for every solution of the supplied connection.

The packet correctly distinguishes this module-level order from the possibly smaller annihilator of one special initial vector. It also records excluded denominators and parameter pivots. On a regular chart, reduction identities can be checked by clearing denominators while preserving those exclusions; evaluating a cleared identity at a forbidden pole is not legitimate.

Independent arithmetic confirmed the nilpotent two-coordinate subsystem and the unused exponential third coordinate. The sample therefore tests a real reduction: the requested output needs both initial position and slope but is independent of the third initial component. No actual geometric connection or integral normalization is established by this toy calculation.

## NX32: chronological loops and gauge

The matrices are

\[
T_0=\begin{pmatrix}1&1\\0&1\end{pmatrix},\qquad
T_1=\begin{pmatrix}1&0\\1&1\end{pmatrix}.
\]

Direct multiplication gives \(T_1T_0(1,0)^\top=(1,1)^\top\) and \(T_0T_1(1,0)^\top=(2,1)^\top\). The output row \((1,0)\) reads one and two. Moreover \(cT_0=(1,1)\), so the direct row and this row span the full dual. This validates the intended order-sensitive fixture independently of graph attachment conventions.

An additional gauge replay used \(S=\begin{pmatrix}1&2\\0&1\end{pmatrix}\), its explicit integer inverse, transformed states \(Sv\), transformed rows \(cS^{-1}\), and transformed matrices \(ST_iS^{-1}\). Both chronological readings were unchanged. The packet's constant-basis law is correct; a parameter-dependent gauge for a differential connection requires the additional derivative term developed in NX33.

The opening cross-reference to `experiment_design.py` for affordable distinguishing experiments should be made precise. That module contains `rank_experiments`, which scores a fixed supplied pool by an explicit separation/cost/noise ratio. It does not enumerate all words or return a globally cheapest word. Use `observability.minimum_distinguishing_experiment` for exact cheapest distinctions and `robust_search.bounded_margin_search` or `bounded_family_search` for bounded single-experiment margin optimization.

## NX33: compatibility, leakage, and gauge

Differentiation gives \(z'=(B'+BA)x\). Since full-row-rank \(B\) is surjective, an exact law depending only on \(z=Bx\) exists precisely when \(B'+BA\) annihilates \(\ker B\), equivalently when it factors as \(TB\). Full row rank also makes \(T\) unique. This is an exact local linear algebra criterion with regularity of the selected chart, not a claim of a canonical global reduction.

For \(B=(1,t)\) and \(A=\begin{pmatrix}0&-1\\0&0\end{pmatrix}\), the sum is zero. For \(A=\operatorname{diag}(0,1)\), the sum is \((0,1+t)\), whose value on the hidden vector \((-t,1)^\top\) is \(1+t\). The isolated zero at \(t=-1\) does not produce neighbourhood closure.

With \(\widetilde B=GB\), expansion gives

\[
\widetilde B'+\widetilde BA
=(G'+GT)B
=(G'G^{-1}+GTG^{-1})\widetilde B.
\]

For \(G=1+t\) and original \(T=0\), the reduced connection is \(1/(1+t)\), exactly as stated. The source target also needs its independent factorization \(c=LB\); dynamic closure alone does not prove target retention. The packet includes this obligation correctly.

## NX34: coefficient tails and the nonvanishing argument

For a nonnegative integer-height counting series on a graph with \(k\ge1\) vertices and fixed \(q\in[0,1]\), the number of profiles of total volume \(n\) is \(\binom{n+k-1}{k-1}\). Every weight lies between zero and one, giving the coefficient majorant. For complex \(q\) with modulus at most one, the corresponding absolute-value majorant remains valid. Specify which local series is being bounded; an arbitrary ratio or logarithm does not inherit nonnegative coefficients automatically.

For \(0\le r<1\), subtracting the finite head from \((1-r)^{-k}\) is the exact majorant tail. The geometric example checks independently:

\[
\frac{1-(1/2)^4}{1+1/2}=5/8,
\qquad
\frac{(1/2)^4}{1-1/2}=1/8.
\]

The roots of \(1+z+z^2+z^3\) are the fourth roots of unity other than one, so none lies in the half-radius disc.

The Rouché statement should explicitly use a bounded Jordan domain, or another domain with an argument-principle-admissible boundary, with both functions holomorphic on a neighbourhood of its closure. Also require \(\sup_{\overline D}|z|\le r<1\), so the displayed tail actually bounds the boundary error. The polynomial zero count is a separate necessary premise, correctly emphasized in the packet.

One sentence needs strengthening: a positive lower bound for \(|P_N|\) throughout the domain proves only that the polynomial is zero-free. To deduce the infinite series is zero-free directly, that lower bound must strictly exceed the uniform tail. The correct inequality is \(\inf_{\overline D}|P_N|>T_N(r)\), giving \(|F_G|\ge\inf|P_N|-T_N(r)>0\).

The source has both real-axis tail helpers and `arithmetic.complex_disc_certificate`. Do not reuse a real-axis-only logarithmic estimate as a uniform complex-domain theorem without its holomorphic majorant argument. Small-prime nonvanishing and large-prime normal convergence remain distinct obligations. Fractional branch factors must retain a chosen cut and basepoint.

## NX35: optimistic and certain covers

From \(m^-\le m\le m^+\), strict positivity gives \(S^-\subseteq S\subseteq S^+\). Therefore an exact cover optimum computed with possible masks is a lower bound, while any actual cover of certain masks is a valid upper-bound witness. Equality certifies the concrete certainly feasible panel as optimal. This conclusion does not require the optimistic masks to be jointly realizable by one set of uncertain simulator values; granting impossible extra coverage only makes the lower bound weaker, not unsound.

Independent subset enumeration of the three-test fixture found the true optimum \((2,\{e_1,e_2\})\). Adding the unresolved pair to \(e_1\)'s possible mask gives lower bound one; excluding that pair after refinement returns lower bound two. A coarse oracle must actually retain the other positive and zero decisions as stated for this progression. Zero upper endpoints do not enter possible coverage because separation requires strict positivity.

No termination guarantee follows merely from increasing arithmetic precision. An exact zero margin, source-error floor, or unresolved model term can block classification. A valid work-limited output is an incumbent and certified gap. Joint correlated geometry falls outside the mask theorem, as the packet correctly states.

## NX36: certificate scope and existing formal claims

Every pair of target-distinct observation sets must be disjoint for guaranteed target identification. A compact scalar or contrast witness can prove that condition; proving no cheaper admissible panel works additionally needs a complete finite-catalogue lower-bound argument. The stated example's interval gap is exactly \(3/10-1/10=1/5\). Endpoint contact invalidates strictness.

The reviewed source contains `formal/Singularity/Operators.lean`, including `quotient_complete`, `affordable_basis_iff`, and `cheapest_witness`, with costs in `Nat`. This supports the packet's scoped claim that generic closure and natural-cost arguments already exist. It does not formally verify the Python search, rational scaling, arbitrary uncertainty propagation, physical calibration, or future decision checker. The packet explicitly separates those future obligations.

For a rational-to-natural cost adapter, the certificate should show a positive common denominator and order-preserving scaling of every relevant finite cost. Original candidate reconstruction, source binding, uncertainty contracts, reset semantics, and word order must agree across composed certificates. Hashes supply binding and integrity, not mathematical truth or authentication of a physical source.

## Opportunistic cross-packet checks

NX01's strict heterogeneous interval criterion and monotonicity against the old largest-radius envelope are correct. NX02's two-reading common-offset example has contrast magnitude two and total support radius \(2/5\), giving strict separation even though each coordinate overlaps. NX03's twelve-bond up-to-two count is 79, while all 264 plate bonds give 34,981 configurations; these remain original masks, not behavioral-class counts. NX04's scalar contrast gives a sufficient per-reading error threshold \(\delta<1/24\). NX05's four-candidate adaptive tree costs two and every two-test fixed subset fails; endpoint singleton cells are essential. NX06's shared-gain contrast gives the stated sufficient threshold \(\delta<1/12\), and its destructive-state example correctly preserves initial identity.

The six new tracks should remain pending. Their proof sketches and toy checks are an implementation specification, not evidence that all proposed engines or full-domain certificates have already been built.


# NX36 handoff - Independent cross-track review

Review date: 2026-10-19 UTC. Scope: all 36 NX packet files, the six group metadata files as present during review, the cited Singularity source, the copied DynaComp source, selected PerfectPower differential sources, and the small exact examples listed below. This is a handoff-design review, not acceptance of 108 implemented pushes. No new implementation theorem, empirical improvement, physical calibration, remote CI result, or complete proof-assistant coverage is asserted by this review.

The reviewer authored NX13-NX18 and therefore independently reviewed the other packet groups; the graph-group arithmetic was separately replayed against literal rational identities. Review did not run every future algorithm because those algorithms are proposed rather than implemented. Other authors' packet files were not changed.

## Overall assessment

The design covers 36 unique tracks and 108 acceptance units. Using the six packet-local `group_*.json` files, every referenced track dependency exists and the directed graph is acyclic. The packets consistently distinguish finite exact calculations, human-readable proofs, proposed implementations, empirical pilots, and formal coverage. The scientific scopes are substantially more careful than a list of attractive analogies: original-object multiplicities, target-specific observability, uncertainty semantics, graph realizability, chronology, and independent oracles recur throughout.

No fatal algebraic error was found in the displayed small examples. The highest-priority corrections are integration details: reuse an existing differential-observable engine in NX31; clarify source-reference snapshots versus runnable companion packages; standardize portable rational encoding; and avoid optional mathematical bridges becoming unnecessary hard dependencies. Two smaller wording clarifications concern doubled signature area and the metric convention in target recovery.

## Findings sent to the integration owner

| Finding | Evidence and risk | Required integration action |
|---|---|---|
| **NX31 already has a companion differential-observable constructor.** | `companion_sources/perfectpower/python/perfectpower/differential_modules.py::DifferentialModule.observable` delegates to `symmetry_quotients.PolynomialCurve.observable`; `curve_families.py::_observable` and `observable` also construct successive `c' + cA` rows, detect first dependence, return the scalar equation and explain universal-versus-special-cycle minimality. NX31-A currently describes implementing much of that algebra. | Make the first push an adapter, independent oracle, target/noise/transport contract, and source integration around the existing engine. Write a new constructor only for a documented unsupported backend or contract gap. Name the concrete inherited APIs. |
| **A source excerpt is not necessarily an importable package.** | Running the copied `DifferentialModule.observable([1,0,0])` on NX31's three-state toy reached the inherited code but failed through `symmetry_quotients -> algebraic_local_curves -> local_curve_execution`, absent at that moment. The copied PerfectPower tree also contains lazy imports into other omitted modules. A later source-copy pass can change this status. DynaComp's scanned relative modules were present. | State clearly whether companions are reference snapshots or supported executable adapters. If execution is promised, include required transitive modules and an import-and-call smoke test of each promised entry point. Do not duplicate the engine merely because a partial snapshot fails to import. |
| **Portable rational encodings differ across packets.** | NX01 requests canonical rational strings, some application packets mention numerator/denominator strings, and NX36 specifies integer numerator/positive-denominator pairs. Existing upstream and closure packets have their own exact encodings. | Define one root NX interchange convention, or require explicit schema-specific validated adapters. Do not solve incompatibility with permissive `Fraction` coercion that accepts floats, booleans, or unchecked strings. |
| **Several dependency edges are optional rather than mathematical prerequisites.** | NX20's first residue automaton does not need NX19's Smith quotient; NX22's exact Fourier reconstruction uses existing phase arithmetic without NX14; NX24 can establish a restricted effective prefix using existing closure without typed NX13 or parameter NX14. NX21-A rational reflection also does not require typed NX13. | Keep useful integration edges as `supports`/optional dependencies, or explain why the expanded acceptance contract requires them. Do not delay an independently useful narrow theorem behind an unrelated completed track. The current graph is acyclic even with those stronger edges. |
| **NX30 uses doubled area.** | Its equations correctly give `A_ij=S2_ij-S2_ji=+1/-1` for the axis-order paths. Ordinary signed geometric area after closing each path by a straight segment is `A_ij/2=+1/2/-1/2`. | Say "antisymmetric area statistic" or explicitly declare the doubled-area convention. No equation or order-sensitive example needs to change. |
| **NX08 must name its measurement-metric convention.** | The displayed weighting \(H^{\mathsf T} R^{-1} H\) is appropriate when `R` describes the noise ellipsoid \(\eta^{\mathsf T} R^{-1} \eta \le \epsilon^{2}\). If `R` instead directly names the norm Gram matrix, the weighting convention changes. | Give the ellipsoid equation in the public record/API and retain it through basis or unit changes. The Euclidean target theorem is unaffected. |

During review, root and packet copies of `group_d.json` briefly duplicated NX19-NX24. This is metadata normalization, not a mathematical conflict. The reviewer's own `group_c.json` was moved into `packets/group_c.json` and its root duplicate removed. The integration owner should enumerate only one canonical source for each group when assembling the manifest.

## Source and API checks

Qualified existing `file.py::function` references that resolved uniquely were checked against the Python AST, including methods and classes. No invented qualified local reference was found. An explicit AST-backed DynaComp crosswalk check covered 52 referenced functions/classes across `rational`, `stability`, `linear`, `uniform`, `validated`, `machine`, `native`, `engineering`, `forever`, `generating`, `realization`, `fastforward`, and `bounds`; all were defined or imported by their referenced module. This checks names, not the complete correctness of an adapter that has yet to be written.

Every `existing_sources` path in the graph-group metadata exists in the actual repository. Other groups deliberately use `DynaComp:` prefixes or GitHub URLs. These are external-source references, not broken local file claims; the integration owner's prefix/URL mapping must bind them to copied source and pinned provenance. A metadata path check must not misclassify a future `proposed_sources` file as a missing current capability.

Existing capabilities are generally identified accurately: Singularity already has exact observation closure, ordered terminal moves, parameter modules, periodic rationality and improved cutoffs, charge/separator compilation, robust bounded search, and the source-derived thermal pilot. DynaComp already has exact reductions, rational GFs and minimal realizations, stability, correlated-domain bounds, all-time error machinery, engineering import, and particular binary64 execution contracts. Proposed NX work should integrate and extend them rather than count a renamed wrapper as their first invention.

The historical arithmetic and geometric references correctly avoid treating the 384 primitive phases, eight conductor-30 eigenphases with multiplicity, 264 branches, and 240 E8 roots as interchangeable populations. Current phase Fourier recovery and Pell residue automata remain finite specified arithmetic questions, not unproved physical correspondences.

## Mathematical and semantic checks

| Track range | Reviewed mathematical boundary | Assessment |
|---|---|---|
| NX01-NX02 | Candidate-specific boxes need strict interval gaps; joint nuisance sets permit combination-only separation; independent competing-world nuisance differs from within-world shared nuisance. | Correct. The union of pair masks is complete only for the product-box contract. The correlated track explicitly refuses to reuse that necessity theorem. |
| NX03-NX04 | Distinct bond removals add positive rank-one corrections to the discrete transition; continuous severity includes nominal at zero; competing calibration values are independent worlds. | Correct. Counts `79` and `34,981` are exact for their separately declared populations. Continuous robust detection needs a severity gap or a different zero-noise question. |
| NX05-NX06 | Memoryless reset intervals yield finite endpoint cells and strictly shrinking proper beliefs; persistent nuisance and destructive history require a larger belief. | Correct. Endpoint singleton branches and initial-target memory are explicitly retained. Positive cost alone is not used to assert arbitrary infinite-horizon policy-search termination. |
| NX07-NX12 | Capability purchase, target conditioning, evaluator contracts, step-response tails, remote GF indexing, and complete constrained protocol words answer different optimization problems. | Correct under the displayed scopes. All-time step/block results do not claim arbitrary switching. Remote rational output growth is distinguished from huge-index residues. Protocol completion is pseudo-polynomial, with original words retained. |
| NX13-NX14 | Rectangular typed closure preserves legal paths; polynomial module stabilization differs from generic rank stabilization; one selected determinant can have false exceptions. | Correct. Multivariate ideals and rational-function poles are explicitly outside the univariate gcd shortcut. |
| NX15-NX18 | Formal graph null vectors need actual realizations; local graph edits affect ambient singleton degrees; thermal removals have a positive rank-one sign; exact span pruning does not preserve robust margin. | Correct. The R38/R11 quantities are candidate frontiers at the stated rational-parameter hypotheses, not exhibited pairs. Union-graph support enumeration handles edge deletion and insertion. |
| NX19-NX24 | Smith lattices preserve integrality and multiplicity; unit actions commute; representation projectors need their actual field; DFT requires an exponent bound; priors are declared; temporary ideal repetition is not a stopping rule. | Correct. The finite-prefix packet explicitly requires a comparison recurrence when recurrence coefficients differ across hypotheses. |
| NX25-NX30 | Forecast targets change the observable row; nonlinear fibres need curvature corrections; scale maps need defect bounds; conserved totals do not identify species; reliable drills need not predict outcomes; order signatures have limited equivalence. | Correct. Historical data and performance numbers are consistently described as unreproduced leads, with frozen empirical comparisons and missing-source outcomes. Clarify NX30's area convention. |
| NX31-NX36 | Differential quotient closure needs the derivative term; monodromy needs basis/path provenance; Rouché needs a separate polynomial zero count; optimistic/conservative masks bound decision cost; feasibility and optimality certificates differ. | Correct in scope. Concrete inherited differential APIs should be named and reused in NX31. |

## Exact example checks actually performed

Literal `Fraction` calculations verified NX13's rectangular cycle `f=(1,1)`, \(g=(1,0)^{\mathsf T}\), its invisible direction and quotient identities; NX14's true exceptional determinant `q-1/2`; NX15's three-node two-row annihilator at `q=1/2`; NX16's two-vertex update \(\Delta \log F=-x-3x^{2}/8\) and edge coefficient `9/8`; NX17's positive rank-one bond-removal matrix, row sums and two-step impulse distinction; and NX18's attained box amplification constants `32 epsilon` and `33 epsilon`.

Additional displayed examples were checked by direct algebra during review: the six-state Pell cycle modulo five; the scalar step-tail values `31/216`, `77/216`, and `793/46656`; the protocol population counts 22 and 6 under its stated budgets; the binary tilted-population expectation `4/3` and variance `4/9`; the four-cell coarse-map defect; species-conversion total closure; the movement four-condition determinant; and the two noncommuting loop words. These are small design sanity checks, not tests of future implementations.

## Empirical and formal claim handling

The WIND packets do not assume the 272-volume archive is bundled, equate lower radar sampling with ten-metre wind, or convert synthetic posterior variance into operational forecasting skill. The scouting packets preserve the previously negative held-out feature result as a research lead and require recovery of manifests before reusing quantitative claims. They distinguish measurement stability, identifiability, reliability, and prediction. No future acceptance unit requires a positive predictive gain, speedup, or graph collision regardless of evidence.

Formal expansion is scoped to checker implications. Neither a small Lean identity result nor a source digest is promoted to proof of an optimizer, data acquisition, graph census, physical source law, or full arithmetic classification. Existing natural-number-cost proofs do not silently become verified rational-cost implementations. The final handoff should retain these distinctions in its root acceptance instructions and generated index.

## Recommended integration release gate

Before packaging, rerun the canonical metadata uniqueness/dependency check, normalize external source prefixes, ensure all 36 packets and 108 pushes remain pending, resolve the NX31 reuse note, and declare the companion execution boundary. A compact root schema policy should govern costs, rational encodings, candidate identity, units, reset semantics, chronological words, exact-versus-outer uncertainty, budget refusals, and independent oracle evidence. No additional permission workflow is needed. These are requirements for a concrete useful research handoff, not claims that all proposed science has already been completed.
