# Environment, commands and publishing

## Core environment

Use Python 3.10+ and Git. The mathematical Python runtime and tests use only the standard library. Core development does not require Lean, Mathlib or a document compiler. Claude Code is installed and authenticated separately by the user; the project contains no credentials and changes no tool permissions.

From the repository root:

```sh
python scripts/handoff.py doctor
python scripts/handoff.py verify
python scripts/handoff.py status
python scripts/handoff.py next --limit 3
```

`doctor` runs the Python suite, retained-example replay, repository and link checks with `PYTHONPATH` configured. It does not rebuild PDFs or prove Lean theorems. `verify` checks ledger/packet structure. The original P01–P36 selector is now empty because those units are complete; select new work from `docs/papers/second_paper_choice.md`, not by reopening P01. Use `python3` if `python` names another interpreter.

Individual core commands are:

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python scripts/reproduce.py --check
python scripts/check_repository.py
python scripts/check_links.py
```

On PowerShell set `$env:PYTHONPATH='src'` before the first two commands, or use `doctor`. An editable install is optional; packaging-backend installation may need network access even though the mathematical runtime does not.

For structural work, use the relevant retained checks, including `scripts/locality_family.py --check`, `scripts/overlap_hierarchy.py --check` and `scripts/loop_series.py --check`, with `PYTHONPATH=src`. These have declared scopes; inspect costs before adding a larger census.

## Optional formal proof setup

Both packages pin Lean 4.12.0. With that toolchain's `lake` on `PATH`, the core-only package needs no Mathlib:

```sh
python formal/tools/gen_certificates.py --check
python scripts/check_formal.py
```

The core audit covers 91 release declarations. The actual real-analytic completion is in the separate `formal-analysis/` package, with pinned Mathlib and transitive dependency manifests. Follow `formal-analysis/README.md` for dependency initialization and its targeted Mathlib cache download. These setup steps may require network access and disk space; the archive intentionally excludes `.lake` caches.

After that setup, from the repository root:

```sh
python scripts/check_formal_analysis.py --clean --receipt results/formal_analysis_audit.json
```

This builds the actual real-analysis chain and audits 79 declarations against the standard-axiom allowlist. It proves positive-real Euler-product factorization and the boundary limit, including the two certified pairs. The older conditional core theorem is not the final analytic result. An existing source-bound receipt records the release run; a claim about a changed checkout requires a new successful build. Neither the receipt nor a Python test substitutes for that build.

## Document tooling

Reading PDF, Markdown or HTML needs no TeX installation. Regeneration uses Pandoc, XeLaTeX, `xdvipdfmx`, DejaVu fonts and the TeX packages in `scripts/build_documents.py`; Poppler's `pdfinfo` validates output readability. The build runs XeLaTeX synchronously in no-PDF mode before converting XDV to PDF. Matplotlib is needed only to redraw the optional illustration. Record tool versions when rebuilding documents.

After mathematical manuscript changes, build, inspect warnings, check page counts and render representative pages. A successful TeX exit alone does not establish that a PDF is complete or readable. Current outputs are a 146-page monograph, a ten-page visibility article and an eight-page locality article. Exact whitespace-delimited source counts, including equations and tables, live in `results/manuscript_counts.json`. The old 105-page/34,147-word monograph and six-page article describe v0.1.0 only.

## Claude Code entry point

Open an interactive Claude Code session from the repository root using `claude`, then paste `handoff/CLAUDE_START_PROMPT.md`. `CLAUDE.md` supplies project instructions; detailed working state belongs in records and task documents. Official entry-point documentation was checked on 2026-10-17:

- https://code.claude.com/docs/en/memory
- https://code.claude.com/docs/en/cli-reference

The handoff requires no particular paid model, permission bypass, custom hook or plugin. Existing organization settings may affect loaded instructions; the prompt names the relevant files explicitly.

## Git and exact archive format

The owner authorizes meaningful commits and ordinary pushes to `https://github.com/towre676-cloud/singularity`. Inspect status and remote history, preserve unrelated work, commit bounded results and verify the remote hash after pushing. Never force-push, rewrite shared history or report a local commit as published. Authentication belongs to the user's environment; do not search unrelated files for credentials. Offline work needs no publishing credentials.

`releases/Singularity-v0.2.0-complete.zip` is a plain snapshot with a single top-level `singularity/` directory. It contains source, tests, results, documentation, three PDFs, proof sources and dependency manifests. It contains no `.git` directory, no embedded `repository.bundle`, and no Lean/Mathlib build caches. `results/archive_manifest.json` supplies per-file hashes and names its own self-hash exclusion. Extract, enter `singularity/` and run the local checks. For normal history and publishing, clone the GitHub repository separately and deliberately import any offline edits; do not create unrelated replacement history in the populated remote.

Earlier handoff archives used a different layout with a bundle. Those instructions are historical and do not apply to the v0.2.0 complete archive. `scripts/package_release.py` rebuilds the current snapshot and validates its member hashes.
