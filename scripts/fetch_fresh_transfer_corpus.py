#!/usr/bin/env python3
"""Acquire a fixed, readable dev/heldout corpus without scoring any model.

Only selected public-domain book fragments and PSF-licensed CPython fragments
are retained. Full source downloads remain in an external cache. Selection,
splits, source hashes and overlap checks are recorded before any inference.
"""
from __future__ import annotations

import argparse
import base64
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import re
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "applications/training_lab/data/fresh_transfer"
PRIOR = ROOT / "applications/training_lab/results/cross_domain/documents.json.gz"
CPYTHON_REVISION = "0fb18b02c8ad56299d6a2910be0bab8ad601ef24"
SALT = "singularity-deployment-transfer-20261019"
CHARS = 16384
BOOKS = (
    (11, "alice_in_wonderland", "Lewis Carroll"),
    (84, "frankenstein", "Mary Shelley"),
    (1342, "pride_and_prejudice", "Jane Austen"),
    (2701, "moby_dick", "Herman Melville"),
    (1661, "adventures_of_sherlock_holmes", "Arthur Conan Doyle"),
    (36, "war_of_the_worlds", "H. G. Wells"),
    (35, "time_machine", "H. G. Wells"),
    (345, "dracula", "Bram Stoker"),
    (33, "scarlet_letter", "Nathaniel Hawthorne"),
    (1400, "great_expectations", "Charles Dickens"),
    (1260, "jane_eyre", "Charlotte Bronte"),
    (1184, "count_of_monte_cristo", "Alexandre Dumas"),
)
REFERENCE = ("asyncio-task", "sqlite3", "pathlib", "itertools", "functools", "decimal",
             "argparse", "logging", "unittest", "concurrent.futures", "multiprocessing", "typing")
MODULES = ("argparse", "fractions", "ipaddress", "inspect", "shutil", "subprocess",
           "threading", "tokenize", "traceback", "statistics", "pathlib", "configparser")
BOOK_TITLE_PHRASES = {
    "alice_in_wonderland": "ALICE'S ADVENTURES IN WONDERLAND",
    "frankenstein": "FRANKENSTEIN", "pride_and_prejudice": "PRIDE AND PREJUDICE",
    "moby_dick": "MOBY DICK", "adventures_of_sherlock_holmes": "ADVENTURES OF SHERLOCK HOLMES",
    "war_of_the_worlds": "WAR OF THE WORLDS", "time_machine": "TIME MACHINE",
    "dracula": "DRACULA", "scarlet_letter": "SCARLET LETTER",
    "great_expectations": "GREAT EXPECTATIONS", "jane_eyre": "JANE EYRE",
    "count_of_monte_cristo": "COUNT OF MONTE CRISTO",
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def specifications():
    rows = []
    for number, name, author in BOOKS:
        rows.append({"domain": "literary_prose", "name": name, "author": author,
                     "expected_title_phrase": BOOK_TITLE_PHRASES[name],
                     "source_url": f"https://www.gutenberg.org/cache/epub/{number}/pg{number}.txt",
                     "source_identifier": f"Project Gutenberg ebook {number}",
                     "license": "Public domain in the United States; book text only, Gutenberg header/footer excluded",
                     "license_url": "https://www.gutenberg.org/policy/license.html",
                     "offset_characters": 2000})
    for domain, names, folder, extension in (
            ("technical_reference", REFERENCE, "Doc/library", "rst"),
            ("python_source", MODULES, "Lib", "py")):
        for name in names:
            rows.append({"domain": domain, "name": f"{name}.{extension}",
                         "source_url": f"https://raw.githubusercontent.com/python/cpython/{CPYTHON_REVISION}/{folder}/{name}.{extension}",
                         "source_identifier": f"python/cpython@{CPYTHON_REVISION}:{folder}/{name}.{extension}",
                         "source_revision": CPYTHON_REVISION, "source_release": "v3.12.0",
                         "license": "Python Software Foundation License Version 2, with retained CPython license notices",
                         "license_url": f"https://raw.githubusercontent.com/python/cpython/{CPYTHON_REVISION}/LICENSE",
                         "offset_characters": 0})
    return rows


def get(url, cache):
    path = cache / sha(url.encode())
    if not path.exists():
        request = urllib.request.Request(url, headers={"User-Agent": "Singularity reproducible corpus acquisition/0.9"})
        with urllib.request.urlopen(request, timeout=120) as response:
            raw = response.read()
        path.write_bytes(raw)
    return path.read_bytes()


def shingles(text):
    words = re.findall(r"\w+", text.casefold())
    return {tuple(words[i:i + 5]) for i in range(max(0, len(words) - 4))}


def similarity(a, b):
    intersection = len(a & b)
    return {"jaccard_5word": intersection / len(a | b) if a | b else 0.,
            "containment_5word": intersection / min(len(a), len(b)) if a and b else 0.}


def verify(output):
    manifest = json.loads((output / "manifest.json").read_text())
    counts = {}
    for row in manifest["documents"]:
        path = output / row["text_path"]
        raw = path.read_bytes()
        doc = json.loads(raw)
        if sha(raw) != row["json_sha256"] or sha(doc["text"].encode()) != row["sha256"]:
            raise ValueError("corpus identity mismatch: " + row["name"])
        if len(doc["text"]) != row["characters"] or path.stat().st_size >= 65536:
            raise ValueError("corpus size mismatch: " + row["name"])
        key = (row["domain"], row["split"])
        counts[key] = counts.get(key, 0) + 1
    if len(manifest["documents"]) != 36 or sorted(counts.values()) != [4, 4, 4, 8, 8, 8]:
        raise ValueError("split counts changed")
    print(json.dumps({"verified_documents": 36, "split_counts": {f"{a}/{b}": n for (a, b), n in sorted(counts.items())}}, sort_keys=True))
    return manifest


def fetch(output, cache):
    if (output / "manifest.json").exists():
        return verify(output)
    cache.mkdir(parents=True, exist_ok=True)
    specs = specifications()
    for domain in sorted({row["domain"] for row in specs}):
        group = sorted((r for r in specs if r["domain"] == domain),
                       key=lambda r: sha(f"{SALT}/{domain}/{r['name']}".encode()))
        for index, row in enumerate(group):
            row["split"] = "dev" if index < 4 else "heldout"
            row["split_rank"] = index
            row["split_key_sha256"] = sha(f"{SALT}/{domain}/{row['name']}".encode())
    prior_raw = PRIOR.read_bytes()
    prior_payload = json.loads(gzip.decompress(prior_raw))
    prior = [{"domain": r["domain"], "name": r["name"], "sha256": r["sha256"],
              "text": base64.b64decode(r["base64"]).decode("utf-8", errors="replace")}
             for r in prior_payload["documents"]]
    old_source_names = {r["name"] for r in prior if r["domain"] == "source_code"}
    if old_source_names & {r["name"] for r in specs if r["domain"] == "python_source"}:
        raise ValueError("source module overlaps prior corpus")
    old_shingles = [(r, shingles(r["text"])) for r in prior]
    def acquire(row):
        raw = get(row["source_url"], cache)
        text = raw.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
        marker = None
        if row["domain"] == "literary_prose":
            start = re.search(r"^\*\*\* START OF (?:THE|THIS) PROJECT GUTENBERG EBOOK.*?\*\*\*\s*$", text, re.MULTILINE)
            end = re.search(r"^\*\*\* END OF (?:THE|THIS) PROJECT GUTENBERG EBOOK.*?\*\*\*\s*$", text, re.MULTILINE)
            if not start or not end or end.start() <= start.end():
                raise ValueError("Gutenberg boundaries unavailable: " + row["name"])
            marker = start.group(0).strip()
            if row["expected_title_phrase"] not in marker.upper():
                raise ValueError("source book title does not match declaration: " + row["name"])
            text = text[start.end():end.start()]
        offset = row["offset_characters"]
        fragment = text[offset:offset + CHARS]
        if len(fragment) != CHARS:
            raise ValueError("source shorter than fixed selection: " + row["name"])
        doc = {**row, "text": fragment, "sha256": sha(fragment.encode()), "characters": len(fragment),
               "bytes": len(fragment.encode()), "source_sha256": sha(raw), "source_bytes": len(raw),
               "normalization": "UTF-8-sig strict; CRLF/CR to LF; fixed Unicode-character offsets; no other edits",
               "selection": "book body after START marker and before END marker, then offset2000" if marker else "source body from character0, retaining comments and license notices",
               "gutenberg_start_marker": marker}
        own = shingles(fragment)
        matches = [{"domain": old["domain"], "name": old["name"], **similarity(own, old_set)} for old, old_set in old_shingles]
        matches.sort(key=lambda r: (r["containment_5word"], r["jaccard_5word"]), reverse=True)
        if any(old["sha256"] == doc["sha256"] for old in prior) or matches[0]["containment_5word"] >= .35:
            raise ValueError("exact/near duplicate with prior corpus: " + row["name"])
        doc["prior_overlap"] = {"exact_match": False, "max_5word_containment_match": matches[0], "all_matches": matches}
        return doc
    with ThreadPoolExecutor(max_workers=6) as pool:
        documents = list(pool.map(acquire, specs))
    for index, doc in enumerate(documents):
        own = shingles(doc["text"])
        candidates = [{"domain": other["domain"], "name": other["name"], **similarity(own, shingles(other["text"]))}
                      for j, other in enumerate(documents) if j != index]
        closest = max(candidates, key=lambda r: (r["containment_5word"], r["jaccard_5word"]))
        if closest["containment_5word"] >= .35:
            raise ValueError("new corpus near duplicates: " + doc["name"])
        doc["fresh_corpus_overlap"] = closest
    output.mkdir(parents=True, exist_ok=True)
    license_raw = get(f"https://raw.githubusercontent.com/python/cpython/{CPYTHON_REVISION}/LICENSE", cache)
    (output / "CPYTHON_LICENSE.txt").write_bytes(license_raw)
    rows = []
    for doc in sorted(documents, key=lambda r: (r["domain"], r["split_rank"])):
        path = Path("documents") / doc["domain"] / (doc["name"] + ".json")
        write_json(output / path, doc)
        rows.append({key: value for key, value in doc.items() if key not in (
            "text", "prior_overlap", "normalization", "selection", "gutenberg_start_marker", "expected_title_phrase")})
        rows[-1].update({"text_path": path.as_posix(), "json_sha256": sha((output / path).read_bytes()),
                         "prior_overlap_max": doc["prior_overlap"]["max_5word_containment_match"]})
    write_json(output / "manifest.json", {
        "schema": "singularity.fresh-transfer-corpus/1", "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "Fresh development and heldout documents for prospective predictive adaptation; no inference during selection",
        "split_rule": f"Per domain rank12 fixed names by sha256('{SALT}/'+domain+'/'+name); first4 dev, remaining8 heldout",
        "selection_rule": "Fixed16384 Unicode characters: book body offset2000 after Gutenberg START marker; pinned CPython source/docs offset0",
        "previous_corpus": {"path": str(PRIOR.relative_to(ROOT)), "sha256": sha(prior_raw), "documents": len(prior)},
        "deduplication": {"exact": "selected UTF-8 SHA256 compared against all40 previous document identities",
                          "near": "casefold Unicode word5-shingles; every selected fragment against all40 prior documents and all35 other new fragments",
                          "rejection_threshold": "intersection/min(set sizes) >=0.35; stop acquisition, no automatic replacement"},
        "cpython_release": "v3.12.0", "cpython_annotated_tag_sha": "0fb6e700c2f94ae0717ee1be7d4e50b2dd480d14",
        "cpython_revision": CPYTHON_REVISION, "cpython_license_sha256": sha(license_raw),
        "literary_license": "Original English-language book text, public domain in the United States; Gutenberg header/footer/trademark license text excluded. Source URL and SHA bind acquisition; mutable source URLs may later change.",
        "limitations": "Fresh relative to this repository's prior experiments, not guaranteed absent from model pretraining; dev/heldout share broad source collections.",
        "documents": rows})
    return verify(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--cache", type=Path)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.verify:
        verify(args.output)
    elif args.cache:
        fetch(args.output, args.cache)
    else:
        parser.error("--cache outside the repository is required for acquisition")


if __name__ == "__main__":
    main()
