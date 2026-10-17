#!/usr/bin/env python3
"""Inspect, validate, and package the portable Claude Code research handoff."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tarfile
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://github.com/towre676-cloud/singularity.git"
BASELINE = "89fb96d25bef0463e41feb74d987b464e5fd534f"
STATUSES = {"planned", "partial", "implemented_pending_acceptance", "blocked", "complete"}
REQUIRED = [
    "CLAUDE.md", "handoff/START_HERE.md", "handoff/CLAUDE_START_PROMPT.md",
    "handoff/SESSION_PROTOCOL.md", "handoff/RESEARCH_CONTEXT.md",
    "handoff/ARCHITECTURE.md", "handoff/ENVIRONMENT.md", "handoff/FIRST_BATCH.md",
    "handoff/STRATEGIC_EXTENSIONS.md", "handoff/DECISIONS.md",
    "handoff/SESSION_LOG.md", "handoff/PUSH_AUDIT.md", "handoff/push_status.json",
]


def read_ledger(root=ROOT):
    return json.loads((Path(root) / "handoff/push_status.json").read_text(encoding="utf-8"))


def validate_ledger(ledger, root=ROOT):
    """Validate acceptance metadata, real evidence paths, and a dependency DAG."""
    root = Path(root)
    errors = []
    if not isinstance(ledger, dict):
        return ["Push ledger must be a JSON object"]
    if ledger.get("schema") != "singularity.push-status/1":
        errors.append("Unsupported push ledger schema")
    if not re.fullmatch(r"[0-9a-f]{40}", ledger.get("baseline_commit", "")):
        errors.append("Missing valid baseline commit")
    pushes = ledger.get("pushes", [])
    if not isinstance(pushes, list) or not all(isinstance(p, dict) for p in pushes):
        return errors + ["Pushes must be a list of records"]
    expected = {f"P{i:02d}" for i in range(1, 37)}
    ids = [p.get("id") for p in pushes]
    if not all(isinstance(identifier, str) for identifier in ids):
        return errors + ["Push IDs must be strings"]
    if len(ids) != 36 or set(ids) != expected:
        errors.append("Exactly one record for each P01-P36 is required")
    index = {p.get("id"): p for p in pushes}
    for push in pushes:
        identifier = push.get("id", "<missing>")
        if not isinstance(push.get("status"), str) or push["status"] not in STATUSES:
            errors.append(f"{identifier}: invalid status")
        if type(push.get("priority")) is not int or push["priority"] < 0:
            errors.append(f"{identifier}: priority must be a nonnegative integer")
        if not isinstance(push.get("effort"), str) or push["effort"] not in {"S", "M", "L"}:
            errors.append(f"{identifier}: effort must be S, M or L")
        for field in ("title", "next_action", "packet"):
            if not isinstance(push.get(field), str) or not push[field].strip():
                errors.append(f"{identifier}: missing {field}")
        lists_valid = True
        for field in ("dependencies", "evidence", "acceptance_gaps"):
            if not isinstance(push.get(field), list) or not all(isinstance(v, str) for v in push[field]):
                errors.append(f"{identifier}: {field} must be a list of strings")
                lists_valid = False
        if not lists_valid:
            continue
        dependencies = push.get("dependencies", [])
        if any(dep not in expected or dep == identifier for dep in dependencies):
            errors.append(f"{identifier}: invalid dependency")
        if push.get("status") == "complete":
            if push.get("acceptance_gaps"):
                errors.append(f"{identifier}: completed push still has acceptance gaps")
            if not push.get("evidence"):
                errors.append(f"{identifier}: completed push has no evidence")
            if any(index.get(dep, {}).get("status") != "complete" for dep in dependencies):
                errors.append(f"{identifier}: completed push has unaccepted dependencies")
        for name in push.get("evidence", []) + [push.get("packet", "")]:
            path = PurePosixPath(name)
            if not name or path.is_absolute() or ".." in path.parts or not (root / name).is_file():
                errors.append(f"{identifier}: missing or unsafe evidence path {name!r}")
        packet = root / push.get("packet", "<missing>")
        if packet.is_file() and not packet.read_text(encoding="utf-8").startswith(f"# {identifier} "):
            errors.append(f"{identifier}: packet heading does not match ID")
    pending = {identifier: set(p["dependencies"]) for identifier, p in index.items()
               if isinstance(p.get("dependencies"), list) and all(isinstance(v, str) for v in p["dependencies"])}
    while pending:
        ready = {identifier for identifier, deps in pending.items() if not deps}
        if not ready:
            errors.append("Dependency graph contains a cycle or unknown node")
            break
        pending = {identifier: deps - ready for identifier, deps in pending.items() if identifier not in ready}
    return errors


def verify_handoff(root=ROOT):
    root = Path(root)
    errors = [f"Missing {name}" for name in REQUIRED if not (root / name).is_file()]
    if (root / "handoff/push_status.json").is_file():
        ledger = read_ledger(root)
        errors += validate_ledger(ledger, root)
        roadmap = (root / "docs/development/PUSHES.md").read_text(encoding="utf-8")
        if re.findall(r"^## (P\d{2})\s", roadmap, re.M) != [f"P{i:02d}" for i in range(1, 37)]:
            errors.append("Original roadmap IDs changed or are incomplete")
    if errors:
        raise ValueError("\n".join(errors))
    return {"status": "passed", "pushes": 36, "task_packets": 36, "dependency_graph": "acyclic"}


def next_pushes(ledger, limit=3):
    accepted = {p["id"] for p in ledger["pushes"] if p["status"] == "complete"}
    eligible = [p for p in ledger["pushes"] if p["status"] not in {"complete", "blocked"}
                and set(p["dependencies"]) <= accepted]
    return sorted(eligible, key=lambda p: (p["priority"], p["id"]))[:limit]


def doctor():
    """Run the inexpensive core checks with an interpreter-local environment."""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src") + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    link_documents = ["README.md", "docs/MONOGRAPH.md", "CLAUDE.md"] + [
        p.relative_to(ROOT).as_posix() for p in sorted((ROOT / "handoff").rglob("*.md"))
    ]
    commands = [
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        [sys.executable, "scripts/reproduce.py", "--check"],
        [sys.executable, "scripts/check_repository.py"],
        [sys.executable, "scripts/check_links.py", *link_documents],
    ]
    results = []
    for command in commands:
        print("Running:", " ".join(command), flush=True)
        result = subprocess.run(command, cwd=ROOT, env=env, timeout=180)
        results.append({"command": command[1:], "returncode": result.returncode})
    print(json.dumps({"checks": results, "status": "passed" if all(r["returncode"] == 0 for r in results) else "failed"}, indent=2))
    return 0 if all(r["returncode"] == 0 for r in results) else 1


def verify_archive(path):
    """Verify every archived byte and reject unsafe/unmanifested members."""
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate archive member")
        for name in names:
            p = PurePosixPath(name)
            if p.is_absolute() or ".." in p.parts or "\\" in name:
                raise ValueError(f"Unsafe archive member: {name}")
        if archive.testzip() is not None:
            raise ValueError("ZIP CRC check failed")
        manifest = json.loads(archive.read("singularity-handoff/MANIFEST.json"))
        if manifest.get("schema") != "singularity.claude-handoff/1":
            raise ValueError("Unsupported handoff archive schema")
        entries = manifest["files"]
        paths = [entry["path"] for entry in entries]
        if len(paths) != len(set(paths)):
            raise ValueError("Duplicate manifest path")
        if set(names) != set(paths) | {"singularity-handoff/MANIFEST.json"}:
            raise ValueError("Archive/manifest membership differs")
        for entry in entries:
            data = archive.read(entry["path"])
            if len(data) != entry["bytes"] or hashlib.sha256(data).hexdigest() != entry["sha256"]:
                raise ValueError(f"Hash or length mismatch: {entry['path']}")
    return {"status": "passed", "files": len(entries), "source_commit": manifest["source_commit"]}


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def package(output):
    verify_handoff()
    if git("status", "--porcelain").strip():
        raise ValueError("Commit the reviewed source before packaging; tracked snapshot must be clean")
    head = git("rev-parse", "HEAD").decode().strip()
    tree = git("rev-parse", "HEAD^{tree}").decode().strip()
    branch = git("symbolic-ref", "--short", "HEAD").decode().strip()
    members = {}
    tar_data = git("archive", "--format=tar", head)
    with tarfile.open(fileobj=io.BytesIO(tar_data)) as source:
        for member in source.getmembers():
            if not member.isfile():
                continue
            if member.name.startswith("releases/Singularity-Claude-Code-Handoff"):
                continue  # The package cannot contain itself.
            members["singularity-handoff/repository/" + member.name] = source.extractfile(member).read()
    with tempfile.TemporaryDirectory(prefix="singularity-bundle-") as tmp:
        bundle = Path(tmp) / "repository.bundle"
        subprocess.run(["git", "bundle", "create", str(bundle), branch], cwd=ROOT, check=True, capture_output=True)
        subprocess.run(["git", "bundle", "verify", str(bundle)], cwd=ROOT, check=True, capture_output=True)
        members["singularity-handoff/repository.bundle"] = bundle.read_bytes()
    start = f"""# Singularity: Claude Code handoff

Source commit: {head}
Branch: {branch}
Research baseline: {BASELINE}

This package contains all 36 task packets, the audited status/dependency ledger,
the full source/documents/results snapshot, and a self-contained Git bundle.

Preferred Git workflow from this extracted directory:

    git clone --branch {branch} repository.bundle singularity
    cd singularity
    git remote set-url origin {ORIGIN}
    python scripts/handoff.py verify
    python scripts/handoff.py doctor

Then launch Claude Code in that repository and paste CLAUDE_START_PROMPT.md
from this package, or handoff/CLAUDE_START_PROMPT.md inside the repository.

For inspection without Git, enter repository/ and read handoff/START_HERE.md.
The snapshot has no .git directory. Preserve its files when transferring edits.
The bundle and snapshot share the pinned source commit; neither requires access
to previous ChatGPT conversations. The bundle does not contain the later commit
that publishes this generated ZIP itself.

Check archive integrity before transferring work:

    python repository/scripts/handoff.py verify --archive ../Singularity-Claude-Code-Handoff.zip

Run the archive command from this extracted directory, adjusting the ZIP path
if it is elsewhere. No credentials, account connection or permission settings
are included. A normal GitHub authentication is required only for publishing.
"""
    members["singularity-handoff/START_HERE.md"] = start.encode()
    members["singularity-handoff/CLAUDE_START_PROMPT.md"] = (ROOT / "handoff/CLAUDE_START_PROMPT.md").read_bytes()
    info = {"source_commit": head, "source_tree": tree, "branch": branch, "origin": ORIGIN,
            "research_baseline": BASELINE, "snapshot_excludes": "generated handoff ZIP itself; .git directory and untracked files",
            "git_bundle": "repository.bundle", "task_packets": 36}
    members["singularity-handoff/HANDOFF_INFO.json"] = (json.dumps(info, indent=2, sort_keys=True) + "\n").encode()
    entries = [{"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
               for name, data in sorted(members.items())]
    manifest = {"schema": "singularity.claude-handoff/1", "source_commit": head, "source_tree": tree,
                "files": entries, "manifest_self_hash_excluded": True}
    members["singularity-handoff/MANIFEST.json"] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    output = Path(output)
    if not output.is_absolute():
        output = ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    commit_time = int(git("show", "-s", "--format=%ct", head).decode())
    dt = datetime.fromtimestamp(commit_time, timezone.utc)
    stamp = (max(1980, dt.year), dt.month, dt.day, dt.hour, dt.minute, dt.second)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(members.items()):
            item = zipfile.ZipInfo(name, date_time=stamp)
            item.external_attr = 0o100644 << 16
            item.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(item, data)
    report = verify_archive(output)
    report.update({"archive": str(output), "bytes": output.stat().st_size,
                   "sha256": hashlib.sha256(output.read_bytes()).hexdigest()})
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")
    check = sub.add_parser("verify")
    check.add_argument("--archive", type=Path)
    sub.add_parser("status")
    nxt = sub.add_parser("next")
    nxt.add_argument("--limit", type=int, default=3)
    show = sub.add_parser("show")
    show.add_argument("id")
    build = sub.add_parser("package")
    build.add_argument("--output", default="releases/Singularity-Claude-Code-Handoff.zip")
    args = parser.parse_args(argv)
    try:
        if args.command == "doctor":
            return doctor()
        if args.command == "verify":
            report = verify_archive(args.archive) if args.archive else verify_handoff()
        elif args.command == "package":
            report = package(args.output)
        else:
            verify_handoff()
            ledger = read_ledger()
            if args.command == "status":
                report = {"baseline_commit": ledger["baseline_commit"],
                          "counts": dict(Counter(p["status"] for p in ledger["pushes"])),
                          "pushes": [{k: p[k] for k in ("id", "title", "status", "dependencies")} for p in ledger["pushes"]]}
            elif args.command == "next":
                if args.limit < 1:
                    raise ValueError("--limit must be positive")
                report = {"ready_now": [{k: p[k] for k in ("id", "title", "status", "packet", "next_action")}
                                        for p in next_pushes(ledger, args.limit)],
                          "rule": "Only complete prerequisites unlock a push; blocked records require their stated blocker to be resolved"}
            else:
                push = next((p for p in ledger["pushes"] if p["id"] == args.id.upper()), None)
                if push is None:
                    raise ValueError("Unknown push ID; use P01-P36")
                print(json.dumps(push, indent=2))
                print((ROOT / push["packet"]).read_text(encoding="utf-8"))
                return 0
        print(json.dumps(report, indent=2))
        return 0
    except (ValueError, KeyError, OSError, subprocess.SubprocessError, zipfile.BadZipFile) as exc:
        print(f"Handoff check failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
