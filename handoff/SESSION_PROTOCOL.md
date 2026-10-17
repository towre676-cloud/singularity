# Session protocol

## 1. Orient and audit

Read the project instructions, short orientation files and current checkpoint. Run `python scripts/handoff.py verify`, `status`, and `next --limit 3` as separate invocations to inspect the handoff and candidates. Record the checkout commit, branch, working-tree state and relationship to the remote. Preserve unrelated changes. Run the baseline core suite, retained-example replay, repository checker and link checker. An old successful report is evidence of a past run; it does not certify a changed checkout.

Use `python scripts/handoff.py show P01` with the selected ID to retrieve its ledger record. Read the matching original acceptance/audit sections and any referenced task packet, then the complete relevant source, tests and proof sections. Check prerequisite evidence similarly. Load additional records when needed; do not repeatedly load the entire audit, JSON ledger and monograph by default. Use the ledger's defined statuses consistently. Existing partial implementations can reduce work; they cannot remove acceptance requirements. Keep blockers explicit, including unavailable proof-assistant infrastructure. Do not close a formalization push with an ordinary Python test.

## 2. Make the batch concrete

Select at most three pushes unless the user specifies a different batch. Respect dependencies. If a prerequisite appears complete but lacks evidence, audit and close that prerequisite first. State, for each selected item:

| Required field | Meaning |
|---|---|
| Question and claim | The precise statement being proved or implemented. |
| Domain | Graph class, height/volume bounds, parameter restrictions and normalization. |
| Output | Proof, algorithm, data schema, counterexample or focused manuscript change. |
| Oracle | An independent argument or implementation that could expose an error. |
| Cost | Number of graphs/profiles/states and the computation budget. |
| Acceptance | Evidence satisfying every original criterion, or explicit remaining gaps. |

Use source files as the working specification where appropriate, and resolve inconsistencies with a recorded decision rather than silently choosing convenient semantics.

## 3. Develop and challenge

Write definitions before introducing new claims. In prose explain what the formula counts, why the construction is exhaustive and disjoint, where hypotheses enter, and how an example illustrates the result. Distinguish theorem, conditional proposition, experimental observation and conjecture. Preserve stable result identifiers and cite primary sources when a literature claim requires verification.

For code, retain integer/Fraction arithmetic and deterministic serialization. Validate malformed inputs and finite bounds. Share helper code where useful, but keep an independent oracle independent in the mathematical step it checks. A second wrapper around the same enumerator is not a second enumeration method. Preserve fixture labels and all retained first-discrepancy results.

Estimate enumeration before running it. At volume at most R on n vertices, the unrestricted profile count is `comb(R+n,n)`; a height box has `(H+1)^n` profiles; an order-m residue cube has `m^n`. Nested-chain and graph-population sizes require their own estimates. Begin with small cases that exercise repeats, disconnected graphs, ties, zero bounds and invalid inputs. Record actual bounds and cost. Stop or narrow the calculation when its budget is exceeded; increasing a cutoff is a decision requiring a mathematical purpose.

## 4. Accept evidence, not activity

Before marking a push accepted, check all of the following:

- Every original criterion is met or an explicitly permitted negative result is proved.
- The proof states its domain and handles boundary cases.
- New code matches an independent oracle on a declared population.
- Relevant regressions and retained-example replay pass.
- Any formal verification claim has a real successful build with no admitted target lemmas.
- Generated outputs match their sources, or blocked regeneration is recorded without claiming release completeness.
- New links resolve; data records include inputs, bounds, schema and interpretation.
- The status ledger cites concrete repository evidence and the session log explains remaining uncertainty.

Run the full inexpensive core suite after integrated code changes, plus the affected targeted checks. Broaden expensive testing only for an unresolved concern. Avoid repeatedly rerunning a large census after unrelated prose edits. If two implementations disagree, retain the smallest failing instance and resolve it before reporting acceptance.

## 5. Integrate, publish and checkpoint

Review the diff, remove accidental generated caches, check whitespace and ensure each change belongs to the batch. Use one coherent reviewable commit per accepted push when practical; tightly coupled work may share a commit if its evidence distinguishes the IDs. Partial work can be committed with a clearly partial description, but remains partial in the ledger.

The primary session may commit and push under the user's existing authorization. Delegated agents leave their assigned changes to the primary integrator. Never force-push or overwrite concurrent work. After pushing, compare the remote branch hash with the intended local commit. Observe CI before claiming CI success; local passing checks and pending CI are separate facts.

Append a continuation entry to `handoff/SESSION_LOG.md`: date, starting commit, selected IDs, result and proof/evidence paths, commands and outcomes, final commits, remote verification, unresolved questions and next task. Do not put credentials or private tokens in logs. The final message should let a fresh reader know what changed and resume the work without reading the entire conversation.

End at the bounded checkpoint. Continuing beyond the batch is a new session decision, not an automatic infinite loop.
