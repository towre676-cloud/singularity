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
