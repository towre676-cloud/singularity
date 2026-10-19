#!/usr/bin/env python3
"""Download pinned public safetensors checkpoints and record content hashes.

Weights stay outside the repository. No remote Python code or pickle weights
are downloaded. A completed manifest binds the Hub revision and every file
used in the experiment; reruns verify existing files against the manifest.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
import urllib.parse
import urllib.request

MODELS = {
    "gpt2": "openai-community/gpt2",
    "smollm2-360m": "HuggingFaceTB/SmolLM2-360M",
    "smollm2-1.7b": "HuggingFaceTB/SmolLM2-1.7B",
}
SMALL_FILES = {"config.json", "generation_config.json", "tokenizer.json",
               "tokenizer_config.json", "special_tokens_map.json", "vocab.json",
               "merges.txt", "README.md", "LICENSE", "LICENSE.txt"}


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            value.update(block)
    return value.hexdigest()


def fetch_json(url):
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.load(response)


def download_model(key, destination, revision=None, receipt_path=None):
    model_id = MODELS[key]
    receipt_raw = Path(receipt_path).read_bytes() if receipt_path else None
    receipt = json.loads(receipt_raw) if receipt_raw else None
    if receipt:
        if receipt["model_id"] != model_id or (revision and revision != receipt["revision"]):
            raise ValueError("receipt model/revision does not match the requested checkpoint")
        revision = receipt["revision"]
    directory = destination / key
    directory.mkdir(parents=True, exist_ok=True)
    manifest_path = directory / "download_manifest.json"
    if manifest_path.exists():
        manifest = receipt or json.loads(manifest_path.read_text())
        if revision and manifest["revision"] != revision:
            raise ValueError("existing checkpoint has a different revision")
        for record in manifest["files"]:
            if digest(directory / record["path"]) != record["sha256"]:
                raise ValueError("checkpoint file changed: " + record["path"])
        if receipt_raw:
            manifest_path.write_bytes(receipt_raw)
        print(key, "verified", manifest["revision"], flush=True)
        return manifest
    suffix = "/revision/" + urllib.parse.quote(revision, safe="") if revision else ""
    metadata = fetch_json(f"https://huggingface.co/api/models/{model_id}{suffix}?blobs=true")
    pinned = metadata["sha"]
    files = [entry for entry in metadata["siblings"]
             if entry["rfilename"] in SMALL_FILES or entry["rfilename"].endswith((".safetensors", ".safetensors.index.json"))]
    if not any(entry["rfilename"].endswith(".safetensors") for entry in files):
        raise ValueError("no safe tensor weights available")

    def one(entry):
        name = entry["rfilename"]
        target = directory / name
        target.parent.mkdir(parents=True, exist_ok=True)
        expected = entry.get("lfs", {}).get("sha256")
        if not target.exists() or (expected and digest(target) != expected):
            url = f"https://huggingface.co/{model_id}/resolve/{pinned}/{urllib.parse.quote(name)}?download=true"
            for attempt in range(3):
                temporary = target.with_suffix(target.suffix + ".partial")
                try:
                    # A unique query avoids stale CDN redirects with expired signatures.
                    with urllib.request.urlopen(url + f"&attempt={time.time_ns()}", timeout=180) as response, temporary.open("wb") as handle:
                        while block := response.read(8 << 20):
                            handle.write(block)
                    actual = digest(temporary)
                    if expected and actual != expected:
                        raise ValueError("Hub LFS hash mismatch for " + name)
                    temporary.replace(target)
                    break
                except Exception:
                    if attempt == 2:
                        raise
            print(key, name, target.stat().st_size, flush=True)
        return {"path": name, "bytes": target.stat().st_size, "sha256": digest(target),
                "hub_lfs_sha256": expected}

    with ThreadPoolExecutor(max_workers=3) as pool:
        records = list(pool.map(one, files))
    manifest = {"schema": "singularity.pretrained-download/1", "model_id": model_id,
                "revision": pinned, "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
                "license": metadata.get("cardData", {}).get("license"),
                "files": sorted(records, key=lambda row: row["path"])}
    if receipt:
        actual = {r["path"]: (r["bytes"], r["sha256"]) for r in manifest["files"]}
        expected = {r["path"]: (r["bytes"], r["sha256"]) for r in receipt["files"]}
        if actual != expected:
            raise ValueError("downloaded snapshot does not reproduce the supplied receipt")
        manifest_path.write_bytes(receipt_raw)
        manifest = receipt
    else:
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(key, "complete", pinned, flush=True)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--model", choices=MODELS, action="append")
    parser.add_argument("--revision", help="optional exact Hub revision, with one --model")
    parser.add_argument("--receipt", type=Path, help="restore a retained acquisition receipt after verifying every file")
    arguments = parser.parse_args()
    selected = arguments.model or list(MODELS)
    if (arguments.revision or arguments.receipt) and len(selected) != 1:
        parser.error("--revision/--receipt requires exactly one --model")
    for key in selected:
        download_model(key, arguments.destination, arguments.revision, arguments.receipt)


if __name__ == "__main__":
    main()
