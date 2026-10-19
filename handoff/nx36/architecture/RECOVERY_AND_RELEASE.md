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
