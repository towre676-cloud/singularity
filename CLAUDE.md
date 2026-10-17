# Singularity: instructions for Claude Code

You are developing an exact mathematical research project, with working code and a substantial manuscript. The task is to advance the existing 36-push program with reviewable evidence. Read this file before changing code. Start with `handoff/START_HERE.md`, then follow `handoff/CLAUDE_START_PROMPT.md` and `handoff/SESSION_PROTOCOL.md`.

## Authority and working mode

The user has authorized continued implementation, mathematical expansion, commits and pushes to `https://github.com/towre676-cloud/singularity`. Proceed within that scope without asking for routine confirmation. The primary session integrates and commits accepted work; delegated agents write only their assigned files and leave integration to the primary session. This is the meaning of the ownership paragraph in `PROJECT_CONTRACT.md`, which originated during the initial coordinated build. A research push is an acceptance unit, not a synonym for one Git commit or network push.

Inspect the working tree and remote before editing. Preserve existing user changes. Never force-push, rewrite published history, delete unknown files, or send messages, issues, invitations or comments to other people as part of this assignment. Work on the current authorized branch unless the user specifies another one. If the remote has advanced, fetch and inspect it; integrate compatible changes without discarding work. Authentication failure, incompatible concurrent edits or a genuinely ambiguous mathematical requirement can justify a checkpoint. A missing optional document compiler does not block core development.

Use a bounded batch: at most three accepted roadmap pushes per session unless the user explicitly specifies another scope. Deliver the batch, verify the remote commit when pushing is available, and leave an exact checkpoint. Do not install a scheduler, start an unlimited autonomous loop or change permission settings.

## Source of truth and reading order

1. Orient with `handoff/START_HERE.md`, `handoff/RESEARCH_CONTEXT.md`, `handoff/ARCHITECTURE.md`, `handoff/FIRST_BATCH.md`, and the latest decisions/session-log entries.
2. Run `python scripts/handoff.py verify`, `python scripts/handoff.py status`, and `python scripts/handoff.py next --limit 3` to validate the handoff and identify candidate work.
3. For each candidate, run `python scripts/handoff.py show P01` (substitute its actual ID). Read that ledger record, its matching sections in `docs/development/PUSHES.md` and `handoff/PUSH_AUDIT.md`, and any referenced task packet.
4. Read the full source modules, tests and manuscript sections needed to check that selected push's obligations. Load other roadmap records only for dependencies or a concrete comparison; do not blindly load the entire audit, JSON ledger or monograph on every session.

The original release baseline is `89fb96d25bef0463e41feb74d987b464e5fd534f`. The current checkout may contain later work. Audit it before assuming the handoff's baseline counts or statuses remain current. Existing modules overlap several planned pushes; overlap is not acceptance. Preserve P01–P36 identifiers and their dependencies. Never mark a push complete merely because a function, chapter, certificate or roadmap entry exists. Record exact evidence, remaining criteria and blockers in `handoff/push_status.json` and the session log.

## Mathematical contract

For a finite labeled simple loopless graph on `0,...,n-1`, heights are nonnegative integers,

\[
E_G(a)=\sum_{uv\in E(G)}(a_u-a_v)^2,\qquad
L_G(x,q)=\sum_{a\ge0}x^{\sum_i a_i}q^{E_G(a)}.
\]

Volume is total integer height. Counts preserve original labeled assignments; quotienting by graph automorphisms changes the problem. The normalized series is `B=(1-x^n)L`, represented by `min(a)=0`. This removes one common translation even when the graph is disconnected; independent component translations require separate bookkeeping. On these representatives, span is `max(a)`. The full span-marked series retains the binary sector, with constant binary profiles treated separately. Extracting that sector from the unmarked `z=1` projection is not established.

Threshold sets form a weakly nested chain; levels can repeat when heights have gaps. The squared-difference energy includes mixed terms between levels. It is not the absolute-difference cut sum. A pairwise energy can require observations of several nested boundaries without becoming a different interaction law.

The primewise lift uses the same local series: `Z_G(s,q)=product_p L_G(p^(-s),q)`. It introduces no extra graph information. Analytic statements must retain their hypotheses: connectedness where required, admissible `q`, positive-real branch or explicit local complex domain, and controlled remainders. A first discrepancy at volume `r` gives the stated zeta-factor comparison only within the theorem's scope. Do not infer global meromorphic continuation from finite formal coefficients or real-axis estimates.

Keep four categories explicit: established literature; proved project results; exact computations over a declared finite population; conjectures or research targets. Finite agreement does not prove full-series equality, graph isomorphism, completeness or a separation bound for an infinite family. Human-readable proofs should define the objects, explain the idea, give all cases and hypotheses, and state what remains open. Expand machinery when a question requires it; avoid terminology or word-count padding.

## Software contract and commands

The core uses Python 3.10+ and the standard library only. Keep it so unless a concrete accepted task requires an optional dependency with a documented reason. Run from the repository root without installation:

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python scripts/reproduce.py --check
python scripts/check_repository.py
python scripts/check_links.py
```

Use `PYTHONPATH=src python -m singularity --help` for the current CLI. On PowerShell set `$env:PYTHONPATH='src'` before Python commands. `pip install -e .` is optional and can require a packaging backend; it is not needed for baseline checks.

Important current interfaces:

| Module | Contract |
|---|---|
| `graph.py` | `Graph(n, edges)` validates immutable labeled simple graphs; `degrees` is a property; `connected` is a property; energy returns an integer. |
| `heights.py` | Local coefficients: list of `{energy: integer_count}` through a supplied volume. Marked coefficients: `{(volume, energy, span): integer_count}` on minimum-zero profiles. |
| `population.py` | Exact constrained count/rank/unrank on original labeled assignments; finite constraints must really bound the population. |
| `polynomials.py`, `euler.py` | Sparse rational `q` polynomials use `Fraction`; ordinary Euler exponents are not automatically integer multiplicities. |
| `transfer.py` | Exact bounded-height forest messages, optional safe volume truncation and minimum-zero subtraction; cycles are rejected. |
| `certificates.py` | Actual format is `singularity.certificate/1`; replay recomputes finite claims independently. A graph digest gives integrity, not proof or authentication. |
| `conductor.py` | Exact cyclotomic ring and residue-box enumeration with an explicit work budget; arbitrary output index does not imply cheap arbitrary graph/order. |
| `weighted.py` | Positive integral vertex masses, edge weights and hard contractions; no silent change to the unweighted API. |

P03's proposed `relational-height/1` name differs from the existing certificate format. Resolve that explicitly in the specification and migration plan; do not silently rename working records. Retain the four original fixture labels and the cube–Möbius comparison. Preserve their first discrepancies at volumes 2, 3 and 4 and all declared normalizations.

Independent enumeration oracles must not reuse the implementation whose correctness they claim to check. Tests should target mathematical failure modes, malformed input and independent identities. Do not add tests that only duplicate control flow. A source hash or a success field is not an independent correctness argument. Never claim formal verification unless the relevant proof-assistant files compile without admitted results in the stated environment.

## Resource and release discipline

Before enumeration estimate the actual state space: fixed-volume weak compositions, height boxes, subset chains or residue cubes as appropriate. Default to tiny exhaustive populations plus targeted examples. Do not launch larger graph censuses or remove replay budgets to make a result look stronger. Log graph class, bounds, profile counts, exact output, software versions and measured cost. A budget refusal is neither a counterexample nor mathematical failure.

For each accepted push update the smallest relevant proof, implementation, tests and status evidence. Regenerate manuscript/index/release outputs when their sources change and the tools are available. Pandoc and XeLaTeX are optional document-build tools, separate from the core; report stale generated artifacts explicitly if regeneration is blocked. Validate all introduced links. Do not claim remote CI success without observing the actual run. Finish with accepted IDs, precise results, checks actually run, commit and remote status, open issues, and the next dependency-ready item.
