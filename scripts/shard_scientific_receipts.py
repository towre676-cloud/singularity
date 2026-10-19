#!/usr/bin/env python3
"""Package canonical scientific JSON as bounded, readable semantic subtrees.

The existing materialize_pretrained_evidence.restore_json_shards reconstructs
these receipts byte for byte. Scientific producers and their frozen hashes do
not change. Original receipts are retained; removing/ignoring a monolithic
receipt is a separate publication decision.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "applications/training_lab/results"
_MOVED = object()


def _serialized(value, indent=1):
    return (json.dumps(value, indent=indent, sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n").encode()


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _partition(value, max_shard_bytes, metadata_bytes):
    entries, files = [], {}

    def visit(node, path):
        if path:
            chunk = {"schema": "singularity.readable-evidence-shard/1", "path": path, "payload": node}
            raw = _serialized(chunk)
            if len(raw) <= max_shard_bytes:
                name = f"{len(entries):05d}.json"
                entries.append({"file": name, "path": path, "bytes": len(raw), "sha256": _sha(raw)})
                files[name] = raw
                return _MOVED
        if isinstance(node, dict):
            result = {}
            for key, child in sorted(node.items()):
                # Small top-level metadata stays directly readable in the
                # manifest; larger values retain their complete semantic path.
                if not path and len(_serialized(child)) <= metadata_bytes:
                    result[key] = child
                    continue
                part = visit(child, path + [key])
                if part is not _MOVED:
                    result[key] = part
            return result
        if isinstance(node, list):
            result = []
            for index, child in enumerate(node):
                if index >= 1000000:
                    raise ValueError("array coordinate exceeds the existing restoration contract")
                part = visit(child, path + [index])
                # The restoration helper fills these holes at explicit list
                # coordinates; retained nested containers can be filled too.
                result.append(None if part is _MOVED else part)
            return result
        raise ValueError("a scalar subtree exceeds the shard budget at " + json.dumps(path))

    base = visit(value, [])
    return base, entries, files


def shard_receipt(source, *, results_root=None, max_shard_bytes=63 * 1024, max_manifest_bytes=64 * 1024):
    """Publish subtrees without changing the receipt or its serialization.

    Only sorted, ASCII-escaped, finite pretty JSON with indent 1 or 2 and a
    trailing newline is supported by the existing restoration format. The
    output directory is SOURCE.stem.shards. Repeating the identical operation
    is safe; conflicting existing packaging is rejected without overwriting.
    """
    source = Path(source).resolve()
    if source.suffix != ".json":
        raise ValueError("source must be a .json receipt")
    if type(max_shard_bytes) is not int or max_shard_bytes < 256:
        raise ValueError("max_shard_bytes must be an integer of at least 256")
    if type(max_manifest_bytes) is not int or max_manifest_bytes < 256:
        raise ValueError("max_manifest_bytes must be an integer of at least 256")
    if results_root is None:
        results_root = RESULTS if source.is_relative_to(RESULTS.resolve()) else source.parent
    results_root = Path(results_root).resolve()
    if not source.is_relative_to(results_root):
        raise ValueError("source must be inside results_root")
    original = source.read_bytes()
    value = json.loads(original)
    if not isinstance(value, dict):
        raise ValueError("receipt root must be a JSON object")
    indent = next((width for width in (1, 2) if _serialized(value, width) == original), None)
    if indent is None:
        raise ValueError("source must use canonical sorted finite JSON, indent 1 or 2, and a trailing newline")
    manifest = None
    for metadata_bytes in (4096, 0):
        base, entries, files = _partition(value, max_shard_bytes, metadata_bytes)
        manifest = {"schema": "singularity.readable-evidence-shards/1", "base": base, "shards": entries,
                    "serialization": {"indent": indent, "sort_keys": True, "ensure_ascii": True, "trailing_newline": True},
                    "target_relative_to_results": str(source.relative_to(results_root)),
                    "target_bytes": len(original), "target_sha256": _sha(original)}
        manifest_raw = _serialized(manifest)
        if len(manifest_raw) <= max_manifest_bytes:
            break
    else:
        raise ValueError("manifest exceeds the publication budget; receipt has too many semantic subtrees")
    files["manifest.json"] = manifest_raw
    directory = source.with_name(source.stem + ".shards")
    if directory.exists():
        existing = {str(path.relative_to(directory)): path.read_bytes() for path in directory.rglob("*") if path.is_file()}
        if existing != files:
            raise FileExistsError("existing readable shards conflict with this receipt or packaging budget")
    else:
        # Complete the directory before exposing its manifest to restoration.
        with tempfile.TemporaryDirectory(prefix=directory.name + ".building-", dir=directory.parent) as temporary:
            staging = Path(temporary) / "complete"
            staging.mkdir()
            for name, raw in files.items():
                (staging / name).write_bytes(raw)
            os.replace(staging, directory)
    return {"source": str(source), "manifest": str(directory / "manifest.json"),
            "original_retained": True, "target_sha256": manifest["target_sha256"],
            "shards": len(entries), "max_shard_bytes": max((entry["bytes"] for entry in entries), default=0),
            "manifest_bytes": len(manifest_raw)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--results-root", type=Path)
    parser.add_argument("--max-shard-bytes", type=int, default=63 * 1024)
    parser.add_argument("--max-manifest-bytes", type=int, default=64 * 1024)
    args = parser.parse_args()
    print(json.dumps(shard_receipt(args.source, results_root=args.results_root,
                                  max_shard_bytes=args.max_shard_bytes,
                                  max_manifest_bytes=args.max_manifest_bytes), sort_keys=True))
