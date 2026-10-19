# NX36: independent end-to-end finite decision certificates

The `nx.experiment_decision/1` format binds the original candidate IDs, target
map, complete finite catalogue, positive exact costs, scalar closed observation
intervals, source premises, model revision, reset convention, units, parameter
and chronological operator order. Unknown mandatory semantics and unsupported
geometries are rejected. Exact rationals are reduced integer numerator/positive
denominator pairs; booleans and floats are invalid exact integers.

The public checker requires an independently supplied expected problem. This
prevents an old valid certificate from being silently rebound to changed
endpoints, costs, labels or reset conventions. An integrity digest binds those
bytes; it neither authenticates calibration nor proves the source equations.
Source-bound model enclosures remain visible premises of the accepted claim.

## Separation and optimality are distinct obligations

For every target-distinct pair, the certificate names one selected test and its
strict positive interval gap. Closed intervals meeting at one endpoint are not
separated. Checking the endpoints is enough to validate each witness; an
optimizer is not involved. A separate exact helper checks symmetric-zonotope
contrasts:

\[
|w^T(\mu_a-\mu_b)|-
\sum_{g\in G_a}|w^Tg|-
\sum_{g\in G_b}|w^Tg|>0.
\]

These contrasts are feasible separation witnesses, not a claim that the helper
solves every zonotope intersection problem or that scalar masks suffice for
correlated panels. The complete optimality schema currently certifies scalar
interval geometry.

For catalogue optimality, the certificate carries a prefix pair-mask dynamic
table. At prefix zero only mask zero has cost zero. At the next prefix every
state can omit the test or add its coverage mask and cost. The checker validates
the complete local recurrence, including absence of extra/missing states and
minimum costs, without importing any proposal optimizer or protocol compiler.
Induction on prefixes proves every table entry is the minimum cost of an
original subset producing that union. At the final full-pair mask, equality of
its minimum cost with the explicitly feasible selected panel proves catalogue
optimality. The proof table may itself grow exponentially; verification being
cheaper than discovery is a measured goal, not an unconditional theorem.

A positive common cost denominator is retained and checked: each cost times
that denominator is a positive integer. Natural-cost formal statements thereby
apply to a consistently scaled rational cost model. Scaling does not change
the comparison order. The Python checker validates the arithmetic scaling;
the Lean result does not claim to verify that parser or rational implementation.

## Original-object and physical-source reconstruction

The retained thermal certificate includes all three original hypothesis IDs,
their full sparse model matrices, heater and sensor rows, and the two original
chronological reset words. Its independent source replay performs plain sparse
scalar stepping directly from the serialized definitions. It imports neither
`AffineCandidate`, the reduction engine, the protocol population compiler nor a
panel search routine. Each output interval must equal the independently
reconstructed exact reading plus/minus the stated physical radius. The selected
left-pulse experiment costs one and strictly identifies all three supplied
target classes. The mask proof excludes every cheaper panel in the two-member
catalogue.

This is explicitly a finite-catalogue optimum. The source binding does not call
the catalogue complete over all heater words; that separate claim would need
the protocol-population completeness evidence. Multiplicities and original
candidate identities remain present even when outputs happen to agree.

Run `PYTHONPATH=src python scripts/check_nx_decision.py` for the independent
source and decision replay. Mutation tests change endpoints, costs, labels,
source revisions, reset domains, proof-table entries and claimed gaps. Every
change invalidating the original claim is rejected. Separate plain-loop tests
enumerate all tiny subsets and check direct interval intersections.

## Actual compiled formal coverage

`formal/Singularity/NXDecision.lean` proves three scoped semantic results in
core Lean 4.12.0: strict ordered gaps prevent a common reading; accepted
pair-separation witnesses imply target identification; and a feasible admissible
panel plus exclusion of every cheaper admissible panel implies optimality.
`formal/NXDecisionAudit.lean` prints their actual axiom dependencies. All three
compiled and reported no axiom dependencies. There are no admitted results or
custom axiom declarations in this module.

The source-bound audit is replayed by
`python scripts/check_nx_decision_formal.py`; `LEAN` or `--lean` selects the
actual compiler. The retained audit binds source and audit hashes and records
the compiler revision. The theorem treats uncertainty sets, target maps and
costs semantically. It does not verify Python execution, the JSON parser,
external analytic transport, DynaComp source correctness or real-world physical
calibration. Those are separate obligations, kept explicit in the receipt.
