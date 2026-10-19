#!/usr/bin/env python3
"""Rebuild frozen binary receipts from public sources and readable JSON.

The selected documents already exist in the repository's licensed public
cross-domain corpus. New per-target scientific traces are published as plain
JSON so they can be inspected directly. This helper reconstructs the original
deterministic gzip files without changing any frozen protocol or result hash.
Audit cases and post-hoc document reports are also published as readable JSON
shards; their manifests restore the original JSON receipts byte for byte.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("pretrained_prediction", ROOT / "scripts/confirm_pretrained_prediction.py")
STUDY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(STUDY)


def _set_shard_path(root, path, value):
    if not path or any(isinstance(part, bool) or not isinstance(part, (str, int)) for part in path):
        raise ValueError("invalid shard value path")
    node = root
    for index, part in enumerate(path):
        last = index == len(path) - 1
        child = None if last else ([] if isinstance(path[index + 1], int) else {})
        if isinstance(node, list):
            if not isinstance(part, int) or not 0 <= part < 1000000:
                raise ValueError("invalid shard array index")
            node.extend([None] * (part + 1 - len(node)))
            if last:
                if node[part] is not None:
                    raise ValueError("duplicate shard value path")
                node[part] = value
            elif node[part] is None:
                node[part] = child
        elif isinstance(node, dict) and isinstance(part, str):
            if last:
                if part in node:
                    raise ValueError("shard would replace manifest metadata")
                node[part] = value
            elif part not in node:
                node[part] = child
        else:
            raise ValueError("shard path has an incompatible container")
        if not last:
            node = node[part]


def restore_json_shards(results):
    """Restore declared JSON receipts after checking every readable shard.

    No model is loaded. Relative paths must remain inside the result/shard
    directories, and a conflicting existing receipt is never overwritten.
    The final byte count and SHA-256 bind formatting as well as scientific
    values to the original receipt.
    """
    results = Path(results).resolve()
    restored = []
    for manifest_path in sorted(results.glob("**/*.shards/manifest.json")):
        manifest = json.loads(manifest_path.read_bytes())
        if manifest["schema"] != "singularity.readable-evidence-shards/1":
            raise ValueError("unsupported readable evidence manifest")
        value = manifest["base"]
        for entry in manifest["shards"]:
            shard_path = (manifest_path.parent / entry["file"]).resolve()
            if not shard_path.is_relative_to(manifest_path.parent.resolve()):
                raise ValueError("shard path escapes its manifest directory")
            raw = shard_path.read_bytes()
            if len(raw) != entry["bytes"] or hashlib.sha256(raw).hexdigest() != entry["sha256"]:
                raise ValueError("readable evidence shard differs from manifest: " + entry["file"])
            shard = json.loads(raw)
            if shard["schema"] != "singularity.readable-evidence-shard/1" or shard["path"] != entry["path"]:
                raise ValueError("readable evidence shard identity mismatch")
            _set_shard_path(value, entry["path"], shard["payload"])
        formatting = manifest["serialization"]
        if formatting != {"indent": formatting["indent"], "sort_keys": True,
                          "ensure_ascii": True, "trailing_newline": True} or formatting["indent"] not in (1, 2):
            raise ValueError("unsupported receipt serialization")
        raw = (json.dumps(value, indent=formatting["indent"], sort_keys=True,
                          ensure_ascii=True, allow_nan=False) + "\n").encode()
        if len(raw) != manifest["target_bytes"] or hashlib.sha256(raw).hexdigest() != manifest["target_sha256"]:
            raise ValueError("assembled JSON differs from the original receipt")
        target = (results / manifest["target_relative_to_results"]).resolve()
        if not target.is_relative_to(results):
            raise ValueError("receipt path escapes the result directory")
        if target.exists():
            if target.read_bytes() != raw:
                raise ValueError("existing JSON receipt conflicts with its readable shards")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_suffix(target.suffix + ".materializing")
            temporary.write_bytes(raw)
            os.replace(temporary, target)
        restored.append(str(target.relative_to(results)))
    return restored


def materialize(output, export=False):
    receipts = restore_json_shards(ROOT / "applications/training_lab/results")
    protocol = json.loads((output / "protocol.json").read_text())
    source = ROOT / protocol["document_source"]
    if STUDY.file_sha(source) != protocol["document_source_sha256"]:
        raise ValueError("original public corpus differs from frozen receipt")
    documents = STUDY.source_documents(protocol["documents_per_domain"])
    if STUDY.sha(STUDY.canonical(documents)) != protocol["documents_sha256"]:
        raise ValueError("reconstructed document selection differs from receipt")
    document_path = output / "documents.json.gz"
    if not document_path.exists():
        STUDY.write_gzip(document_path, documents)
    elif STUDY.read_gzip(document_path) != documents:
        raise ValueError("existing document materialization differs")
    count = 0
    for result_path in sorted((output / "models").glob("*/results.json")):
        report = json.loads(result_path.read_text())
        for relative, expected in report["trace_files_sha256"].items():
            compressed = output / relative
            readable = result_path.parent / "traces" / (compressed.name.removesuffix(".gz"))
            if export:
                if STUDY.file_sha(compressed) != expected:
                    raise ValueError("original trace differs from frozen result: " + relative)
                record = STUDY.read_gzip(compressed)
                if readable.exists() and json.loads(readable.read_text()) != record:
                    raise ValueError("readable trace already has different contents")
                readable.parent.mkdir(parents=True, exist_ok=True)
                readable.write_text(json.dumps(record, indent=1, sort_keys=True, allow_nan=False) + "\n")
            else:
                record = json.loads(readable.read_text())
                if not compressed.exists():
                    STUDY.write_gzip(compressed, record)
                if STUDY.file_sha(compressed) != expected or STUDY.read_gzip(compressed) != record:
                    raise ValueError("reconstructed trace differs from frozen result: " + relative)
            count += 1
    return {"documents": len(documents), "traces": count, "json_receipts": len(receipts),
            "mode": "export" if export else "materialize"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("export", "materialize"))
    parser.add_argument("--output", type=Path, default=STUDY.OUTPUT)
    args = parser.parse_args()
    print(json.dumps(materialize(args.output, args.phase == "export")))
