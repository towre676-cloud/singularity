# Decision record

Append decisions with their mathematical or software reason, alternatives considered, evidence and consequences. Preserve prior entries unless correcting an explicit error. Do not store secrets or claim a decision was validated by a tool that did not run.

## D001: preserve the 36-push program

The original P01–P36 identifiers, scopes and dependencies remain the program. The later impact discussion supplies optional X01–X04 proposals. A formal roadmap change must record which acceptance obligations move or remain; renumbering silently makes old checkpoints unusable.

## D002: distinguish implementation from acceptance

Several planned outcomes are already partly or substantially implemented. Their dependency and validation criteria are not automatically complete. The status ledger therefore records existing evidence and exact gaps. Never use a percentage-complete estimate as a replacement for those gaps.

## D003: keep the working certificate format

The baseline format is singularity.certificate/1, implemented in certificates.py and used by retained packets. The roadmap's relational-height/1 was a proposed name. P03 must resolve its specification and compatibility explicitly; no automatic rename is authorized by a stale proposal.

## D004: release integrity means observed remote content

The first bootstrap README temporarily linked to files not yet published. The complete baseline was subsequently verified against GitHub's recursive tree, including all 86 blob hashes and all twelve README/monograph relative targets, and CI passed. Future publishing must verify the actual remote commit and referenced files before reporting completion. A local build or successful blob upload alone does not make a file reachable on main.

## D005: use portable session context

CLAUDE.md holds concise persistent project instructions. Detailed task packets, evidence, decisions and session logs remain ordinary versioned files. The handoff archive contains no service credentials, private account memory, cached conversation transcript or proprietary agent connection. This keeps the work usable by another competent development environment.

## D006: bound autonomous work by acceptance units

The initial prompt requests at most three accepted roadmap pushes, then a checkpoint. This bounds a session while respecting the user's authorization for implementation and ordinary commits/pushes. It does not require repeated permission for reversible routine choices. It does not install a recurring automation or an unlimited background agent.

## D007: singularity.certificate/1 satisfies P03's relational-height/1

P03's roadmap text named a format `relational-height/1`. The implemented, tested and retained format is `singularity.certificate/1`. P03 is accepted against the existing format; the roadmap identifier is amended to mean that format. No rename or migration was made, so all retained packets replay unchanged. Alternatives considered: (a) renaming, which would invalidate retained packets without a mathematical reason; (b) a second reader accepting both names, which would create two names for one schema. The reader rejects `relational-height/1` with an explicit superseded-name diagnostic rather than "unrecognized format", and the specification records the decision in `docs/specifications/COEFFICIENTS-v1.md`, section 9. A future incompatible change would be `singularity.certificate/2` with a checked migration.

## D008: session scope "build as much as you can"

On 2026-10-17 the user asked the session to "build as much as you can". This is read as the explicit scope override that CLAUDE.md permits for the three-push batch limit. Each push is still accepted only against its original criteria, committed separately where practical, and recorded in the ledger. The session remains bounded: no scheduler or unattended loop is installed, and it ends at a checkpoint.

## D009: formal pushes remain open without a proof-assistant toolchain

P07, and through it P08, P13, P14, P15, P33 and P34, need a kernel-checked development. In the 2026-10-17/18 session no Lean, Coq or Isabelle installation was present, and the environment's network policy returned HTTP 403 for the Lean release hosts, so no toolchain could be installed. Python tests and manuscript proofs are not substituted for the formal criterion. P07 stays `planned`, and the ledger records the blocker. The next session with a proof assistant should start with P07 as specified in its packet.

## D010: generated documents without XeLaTeX

`scripts/build_documents.py --no-pdf` regenerates `docs/MONOGRAPH.md`, `docs/monograph.tex`, `docs/monograph.html` and `results/manuscript_counts.json` with Pandoc, and leaves the PDFs unchanged. In this session the LaTeX/HTML/Markdown outputs were regenerated after every manuscript change. `output/pdf/monograph.pdf` and `output/pdf/visibility_paper.pdf` are therefore stale relative to the chapters until a build with XeLaTeX runs. The companion paper source did not change. The v0.1.0 release archive is historical and was not rebuilt.

## D011: a pinned core Lean toolchain from the GitHub release

On 2026-10-18 the network policy allowed GitHub release downloads, although the Lean release host still failed. The session downloaded `lean-4.12.0-linux.tar.zst` from `github.com/leanprover/lean4/releases`, unpacked it with the Python `zstandard` module in the scratch directory, and built `formal/` with core Lean only (no Mathlib, whose cache hosts were not used). CI repeats this in the `formal-lean` job and runs `scripts/check_formal.py`, which fails on any axiom outside `propext`, `Quot.sound` and `Classical.choice`. This supersedes the blocker in D009 for P07 and P08. Formal pushes that need Mathlib-scale libraries would require a further decision.
