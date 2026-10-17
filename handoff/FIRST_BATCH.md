# First bounded development batch

## Goal

Close the first three original acceptance units, P01–P03, using the existing engine as the baseline. This is a recommended sequence, not a claim they are complete. Re-audit the current checkout: a later maintainer may already have closed one. The batch should make the mathematics independently executable and the acceptance record trustworthy before pursuing larger graph populations or new theories.

## P01: audit and freeze the semantics

Read PROJECT_CONTRACT.md, handoff/RESEARCH_CONTEXT.md, the actual public functions and CLI, and the P01 packet. Produce a versioned coefficient/data specification in a new documentation path such as docs/specifications/coefficients-v1.md. Cover graph labels; simple versus weighted graph inputs; nonnegative heights; total volume; squared edge energy; local, minimum-zero and span-marked series; disconnected global versus componentwise shifts; exact rational polynomial representation; invalid inputs and truncation meaning.

Existing tests and prose already establish much of this. Add or retain a small disconnected example showing that global minimum zero permits a component to remain entirely positive, while separately normalizing every component does not. Supply a public-API crosswalk to the specification. Avoid rewriting valid algorithms merely to create activity. Close P01 only when the specification, actual interfaces and boundary examples agree.

## P02: implement the missing independent enumerator

Generate weakly nested chains of nonempty subsets whose first set is proper, with repetitions allowed. The empty chain represents the all-zero assignment. Bound total volume by the sum of level-set sizes; each nonempty level costs at least one, so the chain length is at most the volume bound. A direct recursive extension from an outer set to any nonempty subset gives a genuinely different enumeration path from weak compositions.

For each chain, compute its volume, span and quadratic energy using cut sizes and mixed crossing counts. Preserve labeled multiplicities. Do not call marked_coefficients to generate the same outputs and call that independent. Use it only as an external oracle in tests. A proposed chains.py module can be small and exact before it is fast.

Begin with all simple graphs on one through four vertices and total volume at most six. That is a declared finite population, includes disconnected graphs, and is inexpensive enough to exercise exhaustive equality. Add explicit gap-height examples, singleton input, empty-chain normalization and repeated levels. Prove the chain/profile bijection and account for each edge cross term. Record the number of tested graphs and profiles, not just a passing Boolean.

## P03: strengthen portable certificates without breaking the schema

The repository already has singularity.certificate/1 packets and an independent replay implementation. Audit and reuse them. Resolve the original roadmap's proposed relational-height/1 name in the specification and record the decision: preserve the existing format unless a justified migration is actually implemented and tested. Existing packets must remain replayable or have an explicit checked migration path.

Integrate the newly independent chain enumeration as a second route for marked counts within a small declared replay budget. Audit malformed inputs, type-sensitive integers, duplicate polynomial terms, graph edge validation, normalization and comparison claims. A certificate must reject altered counts even when a success flag or digest is left unchanged. Preserve the existing replay work limit and make any additional cost explicit. A parser can be independently tested without pretending it verifies an unbounded mathematical theorem.

## Batch acceptance and checkpoint

The three tasks should yield a specification, an independently generated exact population, stronger replay evidence and updated acceptance records. They should not change the three reference discrepancies, replace original graph labels, grow the small census bound or claim Lean verification. Run the inexpensive full suite and reproduce.py --check; run handoff verification and link checks. Update the ledger only after each complete acceptance check, commit reviewable changes, push under the existing authorization when possible, and leave the next dependency-ready item identified.

P07 becomes eligible after P01, but introducing an actual proof-assistant project is a separate task. P09 can be audited against the working forest engine after P02 is accepted. Dependency readiness, concrete evidence and available tools should determine the next batch; elapsed time is not a reason to invent acceptance.
