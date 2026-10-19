#!/usr/bin/env python3
"""Read-only NX36 roadmap inspection; stdlib only, Python 3.10+.

Verification checks metadata consistency and evidence presence. It does not
establish the truth of mathematical proofs, successful execution of recorded
commands, remote publication, or calibration of any physical model.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

SCHEMA = "singularity.nx-roadmap/1"
STATUSES = frozenset(("proposed", "in_progress", "blocked", "complete"))
MATH_STATUSES = frozenset(("proved", "exact_finite", "counterexample",
                           "scoped_negative", "implemented", "formal"))
TRACK_IDS = tuple(f"NX{i:02d}" for i in range(1, 37))
DISCLAIMER = ("Metadata consistency and evidence presence only; not proof truth, "
              "recorded-command execution, remote publication, or physical calibration.")


def _nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def _strings(value, *, nonempty=False):
    return (isinstance(value, list) and (bool(value) or not nonempty)
            and all(_nonempty(item) for item in value))


def _duplicates(values):
    return sorted(key for key, count in Counter(values).items() if count > 1)


def _relative(base, value):
    if not _nonempty(value) or "\\" in value:
        raise ValueError("portable nonempty relative POSIX path required")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or re.match(r"^[A-Za-z]:", value):
        raise ValueError("absolute/traversing path is not permitted")
    result = (base / value).resolve()
    if result != base.resolve() and base.resolve() not in result.parents:
        raise ValueError("path escapes the declared root")
    return result


def project_root(root):
    """NX36 lives at repository/handoff/nx36, including in the handoff ZIP."""
    return root.resolve().parent.parent


def _object_no_duplicates(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError(f"duplicate JSON key: {key}")
        obj[key] = value
    return obj


def load_roadmap(root):
    path = root / "roadmap.json"
    return json.loads(path.read_text(encoding="utf-8"),
                      object_pairs_hook=_object_no_duplicates)


def _cycles(graph):
    colors, stack, errors = {}, [], []

    def visit(node):
        colors[node] = 1
        stack.append(node)
        for dep in graph[node]:
            if dep not in graph:
                continue
            if colors.get(dep, 0) == 0:
                visit(dep)
            elif colors.get(dep) == 1:
                start = stack.index(dep)
                errors.append(" -> ".join(stack[start:] + [dep]))
        stack.pop()
        colors[node] = 2

    for node in sorted(graph):
        if colors.get(node, 0) == 0:
            visit(node)
    return errors


def _evidence_errors(unit, repository):
    tag = unit.get("id", "unknown unit")
    evidence = unit.get("evidence")
    if not isinstance(evidence, dict):
        return [f"{tag}: complete requires evidence object"]
    errors = []
    if not _nonempty(evidence.get("summary")):
        errors.append(f"{tag}: evidence.summary must be nonempty")
    artifacts = evidence.get("artifacts")
    if not _strings(artifacts, nonempty=True):
        errors.append(f"{tag}: evidence.artifacts must be a nonempty path list")
    else:
        for artifact in artifacts:
            try:
                path = _relative(repository, artifact)
                if not path.exists():
                    errors.append(f"{tag}: missing evidence artifact: {artifact}")
            except ValueError as exc:
                errors.append(f"{tag}: invalid evidence artifact {artifact!r}: {exc}")
    checks = evidence.get("checks")
    if not isinstance(checks, list) or not checks:
        errors.append(f"{tag}: evidence.checks must be a nonempty list")
    else:
        for index, check in enumerate(checks):
            if (not isinstance(check, dict)
                    or not _nonempty(check.get("command"))
                    or type(check.get("exit_code")) is not int
                    or check.get("exit_code") != 0
                    or not _nonempty(check.get("scope"))):
                errors.append(f"{tag}: evidence.checks[{index}] needs command, integer exit_code 0, scope")
    commit = evidence.get("commit")
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-fA-F]{7,40}", commit):
        errors.append(f"{tag}: evidence.commit must be a 7..40 digit hexadecimal commit")
    if (not isinstance(evidence.get("math_status"), str)
            or evidence.get("math_status") not in MATH_STATUSES):
        errors.append(f"{tag}: invalid evidence.math_status")
    return errors


def validate_roadmap(data, root):
    """Return every metadata error that can safely be checked without execution."""
    errors = []
    if not isinstance(data, dict):
        return ["roadmap must be a JSON object"]
    if data.get("schema") != SCHEMA:
        errors.append(f"schema must be {SCHEMA}")
    tracks = data.get("tracks")
    if not isinstance(tracks, list):
        return errors + ["tracks must be a list"]
    if len(tracks) != 36:
        errors.append(f"expected 36 tracks, got {len(tracks)}")
    if any(not isinstance(track, dict) for track in tracks):
        return errors + ["every track must be an object"]
    ids = [track.get("id") for track in tracks]
    if any(not isinstance(identifier, str) for identifier in ids):
        return errors + ["every track ID must be a string"]
    if set(ids) != set(TRACK_IDS) or _duplicates(ids):
        errors.append("track IDs must be NX01..NX36, each exactly once")
    track_map = {track["id"]: track for track in tracks}
    track_graph, units, unit_graph = {}, {}, {}
    repository = project_root(root)
    for track in tracks:
        tag = track["id"]
        for field in ("title", "priority", "summary"):
            if not _nonempty(track.get(field)):
                errors.append(f"{tag}: {field} must be nonempty")
        if not isinstance(track.get("status"), str) or track.get("status") not in STATUSES:
            errors.append(f"{tag}: invalid status {track.get('status')!r}")
        for field in ("existing_sources", "proposed_sources", "acceptance"):
            if not _strings(track.get(field), nonempty=(field == "acceptance")):
                errors.append(f"{tag}: {field} must be a string list")
        deps = track.get("depends_on")
        if not _strings(deps):
            errors.append(f"{tag}: depends_on must be a string list")
            deps = []
        elif _duplicates(deps):
            errors.append(f"{tag}: duplicate track dependencies")
        for dep in deps:
            if dep not in track_map:
                errors.append(f"{tag}: unknown track dependency {dep}")
        track_graph[tag] = deps
        packet = track.get("packet")
        if packet != f"packets/{tag}.md":
            errors.append(f"{tag}: packet must be packets/{tag}.md")
        else:
            try:
                text = _relative(root, packet).read_text(encoding="utf-8")
                if not text.strip():
                    errors.append(f"{tag}: packet is empty")
            except (OSError, UnicodeError, ValueError) as exc:
                errors.append(f"{tag}: unreadable packet: {exc}")
        pushes = track.get("pushes")
        if not isinstance(pushes, list) or len(pushes) != 3:
            errors.append(f"{tag}: expected exactly three pushes")
            continue
        if any(not isinstance(unit, dict) for unit in pushes):
            errors.append(f"{tag}: every push must be an object")
            continue
        expected = {f"{tag}-{suffix}" for suffix in "ABC"}
        found = [unit.get("id") for unit in pushes]
        if (any(not isinstance(identifier, str) for identifier in found)
                or set(found) != expected or len(set(found)) != 3):
            errors.append(f"{tag}: push IDs must be {tag}-A/B/C exactly once")
        for unit in pushes:
            uid = unit.get("id")
            if not isinstance(uid, str):
                continue
            if uid in units:
                errors.append(f"duplicate unit ID {uid}")
            units[uid] = unit
            if not _nonempty(unit.get("title")):
                errors.append(f"{uid}: title must be nonempty")
            if not isinstance(unit.get("status"), str) or unit.get("status") not in STATUSES:
                errors.append(f"{uid}: invalid status {unit.get('status')!r}")
            if not _strings(unit.get("acceptance"), nonempty=True):
                errors.append(f"{uid}: acceptance must be a nonempty string list")
            udeps = unit.get("depends_on")
            if not _strings(udeps):
                errors.append(f"{uid}: depends_on must be a string list")
                udeps = []
            elif _duplicates(udeps):
                errors.append(f"{uid}: duplicate unit dependencies")
            unit_graph[uid] = udeps
            if uid in expected:
                expected_deps = ([f"{dep}-C" for dep in deps] if uid.endswith("-A")
                                 else [f"{tag}-A"] if uid.endswith("-B") else [f"{tag}-B"])
                if set(udeps) != set(expected_deps):
                    errors.append(f"{uid}: dependency contract requires {sorted(expected_deps)}")
            if unit.get("status") == "complete":
                errors.extend(_evidence_errors(unit, repository))
        complete = all(unit.get("status") == "complete" for unit in pushes)
        if (track.get("status") == "complete") != complete:
            errors.append(f"{tag}: track complete iff all three units are complete")
    if len(units) != 108:
        errors.append(f"expected 108 unique units, got {len(units)}")
    for uid, deps in unit_graph.items():
        for dep in deps:
            if dep not in units:
                errors.append(f"{uid}: unknown unit dependency {dep}")
            elif units[uid].get("status") == "complete" and units[dep].get("status") != "complete":
                errors.append(f"{uid}: complete but dependency {dep} is not complete")
    errors.extend(f"track dependency cycle: {cycle}" for cycle in _cycles(track_graph))
    errors.extend(f"unit dependency cycle: {cycle}" for cycle in _cycles(unit_graph))
    return errors


def _unit_map(data):
    return {unit["id"]: unit for track in data["tracks"] for unit in track["pushes"]}


def ready_units(data, limit=3):
    units = _unit_map(data)
    ready = []
    for track in sorted(data["tracks"], key=lambda track: track["id"]):
        if track["status"] == "blocked":
            continue
        for unit in sorted(track["pushes"], key=lambda unit: unit["id"]):
            if unit["status"] not in ("proposed", "in_progress"):
                continue
            if all(units[dep]["status"] == "complete" for dep in unit["depends_on"]):
                ready.append({"id": unit["id"], "title": unit["title"],
                              "status": unit["status"], "track": track["id"],
                              "priority": track["priority"], "packet": track["packet"],
                              "depends_on": unit["depends_on"]})
    ready.sort(key=lambda unit: (unit["status"] != "in_progress", unit["id"]))
    return ready[:limit]


def status_report(data):
    units = _unit_map(data)
    return {"tracks": len(data["tracks"]), "units": len(units),
            "track_status": dict(sorted(Counter(t["status"] for t in data["tracks"]).items())),
            "unit_status": dict(sorted(Counter(u["status"] for u in units.values()).items())),
            "ready_units": len(ready_units(data, len(units))), "verification_scope": DISCLAIMER}


def source_location(source, root):
    """Resolve portable source names without fetching or executing companion code."""
    if re.match(r"^[A-Za-z]:[/\\]", source) or source.startswith(("/", "\\")):
        return None, "external absolute source path is not portable; inspect manually"
    if source.startswith(("https://", "http://")):
        return None, "remote reference not fetched by preflight"
    prefix, sep, rest = source.partition(":")
    companions = {"dynacomp": "dynacomp", "perfectjet": "perfectjet", "perfectpower": "perfectpower"}
    if sep and prefix.casefold() in companions:
        base = root / "companion_sources" / companions[prefix.casefold()]
        try:
            return _relative(base, rest), None
        except ValueError as exc:
            return None, str(exc)
    base = root if source.startswith("companion_sources/") else project_root(root)
    try:
        return _relative(base, source), None
    except ValueError as exc:
        return None, str(exc)


def preflight(root, data):
    warnings, verified, missing = [], [], []
    sources = sorted({source for track in data["tracks"] for source in track["existing_sources"]})
    for source in sources:
        location, note = source_location(source, root)
        if note:
            warnings.append({"source": source, "note": note})
        elif location.exists():
            verified.append(source)
        else:
            missing.append(source)
    if missing:
        warnings.append({"missing_source_references": missing,
                         "note": "Source references are advisory; inspect companion/source manifest before implementation."})
    repository = project_root(root)
    src = repository / "src"
    result = {"python": sys.version.split()[0], "python_supported": sys.version_info >= (3, 10),
              "source_references": len(sources), "existing_source_references": len(verified),
              "warnings": warnings, "verification_scope": DISCLAIMER,
              "expensive_checks_run": False}
    if not (src / "singularity" / "__init__.py").is_file():
        result.update(baseline_import="unavailable", version=None,
                      note="No baseline package in the declared repository layout; source-only handoff remains inspectable.")
        result["ok"] = result["python_supported"]
        return result
    code = ("import json,sys;sys.path.insert(0,sys.argv[1]);"
            "import singularity;print(json.dumps({'version':getattr(singularity,'__version__',None),"
            "'module':singularity.__file__}))")
    try:
        completed = subprocess.run([sys.executable, "-I", "-B", "-c", code, str(src)],
                                   capture_output=True, text=True, timeout=10, check=False)
        if completed.returncode:
            result.update(baseline_import="failed", error=completed.stderr.strip()[:1000], ok=False)
        else:
            details = json.loads(completed.stdout)
            result.update(baseline_import="passed", **details, ok=result["python_supported"])
    except (OSError, subprocess.TimeoutExpired, ValueError) as exc:
        result.update(baseline_import="failed", error=str(exc), ok=False)
    return result


class JsonParser(argparse.ArgumentParser):
    def error(self, message):
        print(json.dumps({"ok": False, "error": message}), file=sys.stderr)
        raise SystemExit(2)


def main(argv=None):
    parser = JsonParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    sub = parser.add_subparsers(dest="command", required=True, parser_class=JsonParser)
    for command in ("verify", "status", "next", "show", "preflight"):
        child = sub.add_parser(command)
        child.add_argument("--root", type=Path, default=argparse.SUPPRESS)
        if command == "next":
            child.add_argument("--limit", type=int, default=3)
        elif command == "show":
            child.add_argument("identifier")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        data = load_roadmap(root)
        errors = validate_roadmap(data, root)
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        print(json.dumps({"ok": False, "errors": [str(exc)]}, indent=2))
        return 1
    if errors:
        print(json.dumps({"ok": False, "errors": errors, "verification_scope": DISCLAIMER}, indent=2))
        return 1
    if args.command == "verify":
        result = {"ok": True, "schema": SCHEMA, "tracks": 36, "units": 108,
                  "packets": 36, "verification_scope": DISCLAIMER}
    elif args.command == "status":
        result = {"ok": True, **status_report(data)}
    elif args.command == "next":
        if args.limit < 1:
            print(json.dumps({"ok": False, "error": "limit must be positive"}))
            return 2
        result = {"ok": True, "units": ready_units(data, args.limit),
                  "ordering": "in_progress first, then ID; blocked units/tracks omitted",
                  "verification_scope": DISCLAIMER}
    elif args.command == "show":
        records = {track["id"]: track for track in data["tracks"]}
        records.update(_unit_map(data))
        if args.identifier not in records:
            print(json.dumps({"ok": False, "error": f"unknown ID {args.identifier}"}))
            return 2
        result = {"ok": True, "record": records[args.identifier], "verification_scope": DISCLAIMER}
    else:
        result = preflight(root, data)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
