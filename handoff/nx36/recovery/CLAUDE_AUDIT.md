# Recovery audit of Claude's interrupted NX36 session

The published working branch ended at `926dce28c4018e55b37e89e48325e802d97376ef`.
Main remained at `2ae86788537b8b69c628c9f265d1d7bfc98f1d0b`, so the latest
Claude implementation was not visible on main. The branch contains eleven
new commits after main, including the original handoff integration.

## What actually exists

| Track | Recorded state | Implemented content |
|---|---|---|
| NX01 | A/B/C complete | Candidate-specific boxes, bounded exact panel optimization, independent cover oracles and the source-derived thermal comparison |
| NX08 | A/B/C complete | Target identifiability, hidden-target witnesses, exact amplification and decoder certificates, sensor-layout selection |
| NX13 | A/B/C complete | Typed rectangular operator closure, legal graph grammar, portable certificates and cheapest legal witnesses |
| NX16 | A/B/C complete | Weighted connected-support compilation, union-support cache invalidation and independently replayable local edits |
| NX10 | A complete | Exact quadratic-metric response tails with nonnormal examples and tamper rejection |
| NX10 | B/C proposed | The module contains substantial search drafts, but their presence alone was not accepted as evidence |
| Remaining tracks | Proposed | Ninety-three other units, giving ninety-five unfinished units in total |

The six new test files contain 83 tests. GitHub's Python 3.12 job and both
formal jobs were observed passing on the interrupted branch while Python 3.10
was still running; the final recovery records supersede that intermediate
observation. The existing formal jobs concern the previously stated Lean scope,
not newly formalized versions of these NX results.

The roadmap metadata verifier passed with 36 tracks, 108 units, four complete
tracks, one in progress, and thirteen complete units. Metadata verification
does not execute the recorded checks or validate physical calibration. The
recovery separately runs tests, exact receipts, independent examples and the
acceptance-specific evidence.

## Exact source recovery

The command runner's automatic approval review repeatedly failed with a model
capacity error during network fetches. No permission settings or sandbox rules
were changed. The already available GitHub connector supplied the branch's
read-only tree, blobs and signed commit metadata.

All 31 missing blobs were restored and checked against their Git object hashes.
The eleven signed commits were reproduced byte for byte from their original
payloads and signatures and checked against their published commit hashes.
The complete recovered tree is
`49cf9378b1d25477425dd83bd91bfd2a6dd5811a`.
Local fast-forward integration preserved Claude's commits and all earlier
frontier work. No unrelated checkout or user edit was reset.

## Completion scope

The user explicitly requested all unfinished work, superseding the routine
three-unit session limit for this recovery. Six disjoint workstreams cover the
remaining tracks. Each must provide source, substantive proof, independent
tests, a deterministic retained replay, and unit-specific evidence. A missing
mandatory empirical dataset or a failed proof remains an explicit acceptance
gap; neither is replaced by an invented measurement or a success flag.

The original P and OE ledgers and FR01-FR05 remain intact. NX acceptance is
recorded only after its own requirements and dependencies have been checked.
