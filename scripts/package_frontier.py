#!/usr/bin/env python3
"""Package complete source and mathematical PDFs, excluding history and old ZIPs."""

import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {".git", ".lake", "tmp", "releases", "__pycache__", ".venv",
            ".pytest_cache", ".mypy_cache"}
SUFFIXES = (".aux", ".log", ".out", ".toc", ".fls", ".fdb_latexmk",
            ".pyc", ".synctex.gz", ".xdv", ".pending")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    target = args.output.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    source = []
    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT)
        if not path.is_file() or path.resolve() == target:
            continue
        if any(part in EXCLUDED or part.endswith(".egg-info") for part in relative.parts):
            continue
        if path.name == ".git" or path.suffix == ".zip" or str(path).endswith(SUFFIXES):
            continue
        source.append(path)
    source.sort(key=lambda p: p.relative_to(ROOT).as_posix())
    entries = [{"path": p.relative_to(ROOT).as_posix(), "bytes": p.stat().st_size,
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in source]
    manifest = {"schema": "singularity.frontier-archive/1",
                "baseline_commit": "438ed423d7d389a1a483c61e0b50eca6a9fc0827",
                "files": entries,
                "exclusions": "git metadata/history, caches, temporary TeX files, prior ZIPs",
                "nx36_scope": "separate handoff; not included or modified"}
    prefix = "Singularity-Frontier-Companion/"
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=9) as archive:
        for path in source:
            item = zipfile.ZipInfo(prefix + path.relative_to(ROOT).as_posix(),
                                   date_time=(2026, 10, 19, 0, 0, 0))
            item.external_attr = 0o100644 << 16
            item.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(item, path.read_bytes())
        archive.writestr(prefix + "FRONTIER_ARCHIVE_MANIFEST.json",
                         json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    with zipfile.ZipFile(target) as archive:
        if archive.testzip() is not None:
            raise SystemExit("ZIP integrity failed")
        for item in entries:
            digest = hashlib.sha256(archive.read(prefix + item["path"])).hexdigest()
            if digest != item["sha256"]:
                raise SystemExit("Archive hash mismatch: " + item["path"])
    print(json.dumps({"archive": str(target), "bytes": target.stat().st_size,
                      "members": len(source) + 1,
                      "sha256": hashlib.sha256(target.read_bytes()).hexdigest()},
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
