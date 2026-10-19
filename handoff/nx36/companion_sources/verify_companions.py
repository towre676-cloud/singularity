"""Verify pinned source bytes, optionally repeating explicitly scoped smoke tests."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    base = here.parent
    manifest = json.loads((base / "provenance/COMPANION_SOURCES.json").read_text())
    total = 0
    for item in manifest["files"]:
        data = (base / item["bundled_relative_path"]).read_bytes()
        if len(data) != item["bytes"] or hashlib.sha256(data).hexdigest() != item["sha256"]:
            raise SystemExit(f"Pinned source mismatch: {item['bundled_relative_path']}")
        blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        if blob != item["git_blob_sha1"]:
            raise SystemExit(f"Git blob mismatch: {item['bundled_relative_path']}")
        total += len(data)
    print(f"Verified {len(manifest['files'])} pinned files; {total:,} source bytes.")
    if args.smoke:
        for run in manifest["passing_smoke_checks"]:
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=run["pythonpath"])
            print(run["label"], flush=True)
            subprocess.run([sys.executable, *run["python_arguments"]], cwd=here / run["directory"], env=env, check=True)


if __name__ == "__main__":
    main()
