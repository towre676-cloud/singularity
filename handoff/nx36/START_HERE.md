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
