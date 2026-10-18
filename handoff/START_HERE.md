# Handing Singularity to Claude Code

**Current checkpoint (v0.2.0, 18 October 2026): the original P01-P36 program is accepted.** Start with the final session-log entry, reproduce the release, and read the precise open agenda in `docs/papers/second_paper_choice.md`. The original first-batch instructions below are historical onboarding material, not a request to repeat completed pushes.

This package prepares a new development session to continue the 36-push program. It contains the existing mathematics and code, an audit of what the initial release actually established, a dependency/status ledger, a first-batch plan and an operating protocol. The original P01–P36 program remains authoritative. The later chat ideas about terminal interfaces and delayed visibility are proposed strategic extensions; they do not replace or silently complete that program.

The repository is `https://github.com/towre676-cloud/singularity`. The verified release baseline used for this handoff is commit `89fb96d25bef0463e41feb74d987b464e5fd534f`. Compare the current checkout with it; this file is a starting point, not a claim that the remote will never advance.

## Start from Git when connected

Use a fresh clone if you do not already have a working checkout:

```sh
git clone https://github.com/towre676-cloud/singularity.git
cd singularity
git status --short --branch
git log -5 --oneline
```

Open that directory in your available Claude Code environment and paste `handoff/CLAUDE_START_PROMPT.md`. This handoff does not assume that Claude Code is already installed or prescribe unstable vendor-specific invocation flags. `CLAUDE.md` at the repository root is the project instruction file.

For an existing checkout, inspect uncommitted changes before fetching. Use `git fetch origin` and compare the local branch with the remote. Preserve changes and integrate deliberately; do not reset or force-push to obtain a superficially clean baseline.

## Start from the downloadable package

The package's `repository/` directory is an offline source snapshot. Its root `START_HERE.md` explains the package layout; this file explains the project workflow. When a `repository.bundle` is supplied, it preserves Git history and can initialize an offline clone:

```sh
git clone repository.bundle singularity
cd singularity
git remote set-url origin https://github.com/towre676-cloud/singularity.git
```

A plain source snapshot can be read, tested and edited offline. It is not itself proof of current remote contents. Prefer importing work into a normal clone before publishing, preserving source changes and comparing any existing history. Do not create unrelated replacement history in an already populated remote. Offline work must be reported as local until a push and remote verification succeed.

## Load context in stages

Begin with `CLAUDE.md`, the short research context and architecture map, FIRST_BATCH, and the latest decision/session-log entries. Then ask the local helper for a compact view:

```sh
python scripts/handoff.py doctor
python scripts/handoff.py verify
python scripts/handoff.py status
python scripts/handoff.py next --limit 3
python scripts/handoff.py show P01
```

Substitute the chosen ID in `show`. Its record directs the detailed read: the matching original roadmap and audit sections, any task packet, dependency evidence, and relevant source/tests/manuscript sections. Read that selected material fully. The complete files below are references, not a requirement to load the entire roadmap, audit and JSON ledger before every session.

| File | Purpose |
|---|---|
| `CLAUDE.md` | Mathematical conventions, authorization and development constraints. |
| `handoff/RESEARCH_CONTEXT.md` | The problem, original motivation, current results and boundaries. |
| `handoff/ARCHITECTURE.md` | Source/test/data map and current interfaces. |
| `docs/development/PUSHES.md` | Original 36 acceptance units and dependencies. |
| `handoff/PUSH_AUDIT.md` | Existing evidence versus criteria still unmet. |
| `handoff/push_status.json` | Machine-readable status and evidence ledger. |
| `handoff/FIRST_BATCH.md` | Recommended initial batch, subject to current audit. |
| `handoff/SESSION_PROTOCOL.md` | How to accept, record and deliver work. |
| `handoff/DECISIONS.md`, `handoff/SESSION_LOG.md` | Decisions and continuation checkpoints. |

Read only the relevant monograph chapters initially. Never treat 36 entries, 55 baseline tests or pre-existing machinery as 36 completed pushes.

## Establish a runnable baseline

Python 3.10+ with the standard library is enough for the core. From the repository root:

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python scripts/reproduce.py --check
python scripts/check_repository.py
python scripts/check_links.py
```

PowerShell users can first run `$env:PYTHONPATH='src'` and then the same Python commands without the `PYTHONPATH=src` prefix. Installing the package is optional. Document regeneration separately requires Pandoc and XeLaTeX; existing PDFs can be read without them. Check `handoff/ENVIRONMENT.md` for dependencies and build limits.

The recommended first session completes at most three dependency-ready accepted pushes. It records a bounded result, commits reviewable changes, pushes when connected and authorized, verifies the remote, and leaves the next task ready. The user already authorized this workflow; routine implementation choices do not need repeated permission questions.
