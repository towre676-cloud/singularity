#!/usr/bin/env python3
"""Read-only launch check for the extracted Claude Code handoff."""
from pathlib import Path
import subprocess
import sys

base = Path(__file__).resolve().parent
repository = base / "repository"
if not repository.is_dir():
    repository = Path(__file__).resolve().parents[3]
handoff = repository / "handoff/nx36"
if not (handoff / "START_HERE.md").is_file():
    raise SystemExit("Extract the complete ZIP first; repository/handoff/nx36 is missing.")
if "--prompt" in sys.argv:
    print((handoff / "CLAUDE_START_PROMPT.md").read_text(encoding="utf-8"))
else:
    subprocess.run([sys.executable, str(handoff / "tools/handoff.py"), "verify"], check=True)
    print("\nOpen this directory in Claude Code:\n" + str(repository))
    print("\nRead: " + str(handoff / "START_HERE.md"))
    print("Paste: " + str(handoff / "CLAUDE_START_PROMPT.md"))
    print("First bounded implementation session: NX01-A, NX01-B, NX01-C.")
