#!/usr/bin/env python3
"""Prepare pinned real WikiText-2 byte streams; never generates replacement text."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

REVISION = "b08601e04326c79dfdd32d625aee71d232d685c3"
BASE = f"https://huggingface.co/datasets/Salesforce/wikitext/resolve/{REVISION}/wikitext-2-raw-v1"

def prepare(output: Path, train_bytes: int=262144, eval_bytes: int=32768):
    import pyarrow.parquet as pq
    if min(train_bytes,eval_bytes)<256:
        raise ValueError("corpus budgets must be at least 256 bytes")
    output.mkdir(parents=True,exist_ok=True)
    records={}
    for role, split in (("train","train"),("tune","validation"),("test","test")):
        name=f"{split}-00000-of-00001.parquet"
        url=f"{BASE}/{name}"
        target=output/name
        if not target.exists():
            with urllib.request.urlopen(url,timeout=90) as response:
                payload=response.read()
            temporary=target.with_suffix(".part")
            temporary.write_bytes(payload)
            temporary.replace(target)
        table=pq.read_table(target,columns=["text"])
        texts=[row for row in table.column("text").to_pylist() if row and row.strip()]
        stream=("\n".join(texts)+"\n").encode("utf-8")
        limit=train_bytes if role=="train" else eval_bytes
        if len(stream)<limit:
            raise ValueError(f"{role} corpus is smaller than requested prefix")
        selected=stream[:limit]
        path=output/f"{role}.txt"
        path.write_bytes(selected)
        records[role]={"source_url":url,"parquet_sha256":hashlib.sha256(target.read_bytes()).hexdigest(),
            "source_rows":table.num_rows,"nonempty_rows":len(texts),"source_stream_bytes":len(stream),
            "selection":"fixed byte prefix after joining nonempty rows with newline",
            "selected_bytes":len(selected),"selected_sha256":hashlib.sha256(selected).hexdigest(),
            "file":path.name}
    manifest={"schema":"singularity.wiktext-byte-source/1","dataset":"Salesforce/wikitext",
        "configuration":"wikitext-2-raw-v1","revision":REVISION,
        "source_card":"https://huggingface.co/datasets/Salesforce/wikitext",
        "license":["cc-by-sa-3.0","gfdl"],"attribution":"WikiText by Stephen Merity et al.; source articles from Wikipedia. Dataset card and pinned source URLs retain provenance.",
        "benchmark_scope":"Byte-level learning on declared prefixes of original official splits; not standard word-level WikiText perplexity.",
        "splits":records}
    (output/"source_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    return manifest

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--train-bytes",type=int,default=262144)
    parser.add_argument("--eval-bytes",type=int,default=32768)
    args=parser.parse_args()
    print(json.dumps(prepare(args.output,args.train_bytes,args.eval_bytes),indent=2))

