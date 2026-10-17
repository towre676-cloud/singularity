# Environment, commands and publishing

## Core environment

Use Python 3.10 or later and Git. The mathematical runtime and tests use only the Python standard library. The baseline CI matrix is Python 3.10 and 3.12. Claude Code is an external tool installed and authenticated by the user; this repository does not install it, hold its credentials, select a paid model or change its permissions.

From the repository root, these commands work without installing the package:

```sh
python scripts/handoff.py doctor
python scripts/handoff.py verify
python scripts/handoff.py next --limit 3
python scripts/handoff.py show P02
```

doctor runs the standard-library test suite, reproduction checks, repository checks and document-link checks with PYTHONPATH configured internally. It does not rebuild PDFs, contact a remote service, install dependencies or regenerate a large census. verify checks the handoff ledger and packet structure. Use python3 if python names a different interpreter on the target machine.

The underlying POSIX commands are:

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python scripts/reproduce.py --check
python scripts/check_repository.py
python scripts/check_links.py
```

On Windows PowerShell, set $env:PYTHONPATH='src' before the first two commands, or use doctor to avoid shell-specific environment syntax. An editable install is optional: python -m pip install -e . may need network access for packaging dependencies even though the mathematical core does not.

## Document tooling

Reading the committed PDF, Markdown and HTML needs no TeX installation. Regeneration uses Pandoc, XeLaTeX, DejaVu fonts and the TeX packages named in scripts/build_documents.py. Drawing the graph illustration uses matplotlib, which is optional and outside the core runtime. No version of these external tools is pinned by the initial project; record versions when regenerating figures or PDFs. A missing document tool is an environment limitation, not a reason to replace a valid committed PDF with a partial build.

After a substantive manuscript change, build the documents, inspect log warnings, render representative pages and check mathematical layout. A clean TeX exit alone does not prove a page is readable. The baseline book has 105 pages and 34,147 whitespace-delimited source words, including equations and tables; the companion paper has six pages. These measurements are historical and should be updated if the manuscripts actually change.

## Claude Code entry point

Open an interactive Claude Code session from the repository root using claude, then paste handoff/CLAUDE_START_PROMPT.md. Root CLAUDE.md contains concise project instructions. Keep detailed working notes in the handoff ledger, session records and task packets rather than continually expanding the automatically loaded file. Official documentation was checked on 2026-10-17:

- https://code.claude.com/docs/en/memory
- https://code.claude.com/docs/en/cli-reference

The handoff uses ordinary repository files and an interactive prompt. It does not require a particular Claude model, a permission bypass, custom hooks, a plugin or a remote agent service. Existing user or organization settings may affect which instructions Claude Code loads; the startup prompt explicitly names the required files so the task remains reviewable.

## Git workflow

The owner has authorized meaningful commits and ordinary pushes to https://github.com/towre676-cloud/singularity. Before changing files, inspect status and the remote head. Preserve unrelated local work. Make small reviewable commits tied to a push ID and report what passed. Push accepted work when credentials are available; never force-push, rewrite shared history or silently claim a local commit is remote.

During creation of the baseline, command-line Git could fetch this public repository but had no push credentials. The connected GitHub app successfully published it. That app connection is not contained in this archive. On the target machine, use the user's existing Git/GitHub authentication. If publishing is blocked, retain the local commits and record the exact failure; do not probe unrelated files for credentials. No new credentials or platform permissions are needed to work offline.

The archive includes a self-contained Git bundle and a plain repository snapshot. The bundle preserves the source commit and its ancestors; the snapshot is useful for inspection and environments without Git. Build metadata identifies the pinned source commit. Fetching a newer main is a deliberate update from that baseline, so rerun doctor and inspect ledger changes after doing so.
