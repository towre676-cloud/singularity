#!/usr/bin/env python3
"""Replay incomplete retained logs without treating repeats as independent seeds."""
from __future__ import annotations
import argparse
from contextlib import nullcontext
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import time

class _CapturedLog:
    """Keep the streamed records and atomically seal the complete byte payload."""
    def __init__(self, handle, path, original_open):
        self.handle, self.path, self.original_open = handle, path, original_open
        self.chunks = []
    def __enter__(self): return self
    def write(self, value):
        self.chunks.append(value)
        return self.handle.write(value)
    def flush(self): return self.handle.flush()
    def __exit__(self, kind, value, traceback):
        self.handle.close()
        if kind is None:
            temporary = self.path.with_name(self.path.name + '.sealed')
            with self.original_open(temporary, 'wb') as target:
                target.write(''.join(self.chunks).encode('utf-8'))
                target.flush()
                os.fsync(target.fileno())
            os.replace(temporary, self.path)

class _CaptureContext:
    def __enter__(self):
        self.original_open = Path.open
        original = self.original_open
        def intercepted(path, mode='r', *args, **kwargs):
            handle = original(path, mode, *args, **kwargs)
            if path.name == 'metrics.jsonl' and mode == 'w':
                return _CapturedLog(handle, path, original)
            return handle
        Path.open = intercepted
        return self
    def __exit__(self, *args): Path.open = self.original_open

def equal(a,b):
    import torch
    if isinstance(a,torch.Tensor):return isinstance(b,torch.Tensor) and torch.equal(a,b)
    if isinstance(a,dict):return isinstance(b,dict) and a.keys()==b.keys() and all(equal(a[k],b[k]) for k in a)
    if isinstance(a,(list,tuple)):return type(a)==type(b) and len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
    return a==b

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def replay(root):
    import torch
    from singularity.training.runner import run
    root=root.resolve()
    manifest_path=root/"integrity_replays.json"
    manifest=json.loads(manifest_path.read_text()) if manifest_path.exists() else {
      "schema":"singularity.training-integrity-replays/1","entries":[],
      "reason":"Raw JSONL audit detected incomplete saved logs despite complete checkpoint hashes; original artifacts quarantined and identical deterministic configs replayed.",
      "interpretation":"Verification repeats are additional computation, not new independent seeds. Canonical run folders mirror validated replay artifacts."}
    summaries=[p for p in root.rglob("summary.json") if
       not any(part in ("integrity_archive","integrity_replays") for part in p.relative_to(root).parts)]
    for summary_path in sorted(summaries):
        summary=json.loads(summary_path.read_text())
        if "checkpoint_sha256" not in summary:continue
        folder=summary_path.parent
        raw=folder/"metrics.jsonl"
        if not raw.exists():continue
        actual=sha(raw)
        rows=raw.read_bytes().splitlines()
        if actual==summary["metrics_sha256"] and len(rows)==summary["optimizer_updates"]:continue
        relative=folder.relative_to(root)
        cfg=json.loads((folder/"config.json").read_text())
        if sha(folder/"checkpoint.pt")!=summary["checkpoint_sha256"]:
            raise ValueError("Checkpoint is corrupt; refusing log-only replay: "+str(relative))
        original=torch.load(folder/"checkpoint.pt",map_location="cpu",weights_only=False)
        archive=root/"integrity_archive"/relative
        if not archive.exists(): shutil.copytree(folder,archive)
        base=root/"integrity_replays"/relative
        attempt=1
        out=base
        while out.exists():
            previous_summary=out/'summary.json'
            if previous_summary.exists():
                previous=json.loads(previous_summary.read_text())
                ident=str(out.relative_to(root))
                known={entry['replay_dir'] for entry in manifest['entries']}
                known.update(entry['replay_dir'] for entry in manifest.get('failed_attempts',[]))
                if ident not in known:
                    manifest.setdefault('failed_attempts',[]).append({
                        'relative_path':str(relative),'replay_dir':ident,
                        'reason':'Model and outcome matched but replay JSONL coverage was incomplete',
                        'additional_wall_seconds':previous['wall_seconds_including_monitoring'],
                        'extra_optimizer_updates':previous['optimizer_updates'],
                        'extra_test_evaluations':previous['test_evaluations']})
            attempt+=1
            out=base.with_name(base.name+f'_attempt_{attempt}')
        context=nullcontext()
        if cfg.get("model",{}).get("name")=="basis_mlp":
            source=Path(__file__).resolve().parents[1]/"applications/training_lab/basis_study.py"
            spec=importlib.util.spec_from_file_location("basis_replay",source)
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            context=module.basis_factory()
        print(json.dumps({"event":"integrity_replay_started","run":str(relative),
                          "retained_records":len(rows),"expected":summary["optimizer_updates"]}),flush=True)
        started=time.perf_counter()
        with context, _CaptureContext(): fresh=run(cfg,out)
        extra=time.perf_counter()-started
        restored=torch.load(out/"checkpoint.pt",map_location="cpu",weights_only=False)
        checks={"model_equal":equal(original["model"],restored["model"]),
                "optimizer_equal":equal(original["optimizer"],restored["optimizer"]),
                "tune_equal":summary["final_tune"]==fresh["final_tune"],
                "test_equal":summary["final_test"]==fresh["final_test"]}
        if not all(checks.values()):raise ValueError("Deterministic replay changed outcome: "+str(checks))
        payload=(out/"metrics.jsonl").read_bytes()
        if hashlib.sha256(payload).hexdigest()!=fresh["metrics_sha256"] or len(payload.splitlines())!=fresh["optimizer_updates"]:
            raise ValueError("Replay log itself failed integrity")
        for file in out.iterdir():
            if file.is_file():shutil.copyfile(file,folder/file.name)
        entry={"relative_path":str(relative),"original_retained_records":len(rows),
             "expected_records":summary["optimizer_updates"],"original_metrics_actual_sha256":actual,
             "original_metrics_recorded_sha256":summary["metrics_sha256"],
             "original_checkpoint_sha256":summary["checkpoint_sha256"],
             "replayed_checkpoint_sha256":fresh["checkpoint_sha256"],**checks,
             "additional_wall_seconds":extra,"extra_optimizer_updates":fresh["optimizer_updates"],
             "extra_test_evaluations":fresh["test_evaluations"],
             "archive_dir":str(archive.relative_to(root)),"replay_dir":str(out.relative_to(root))}
        manifest["entries"].append(entry)
        all_repeats=manifest['entries']+manifest.get('failed_attempts',[])
        manifest["additional_wall_seconds_total"]=sum(e["additional_wall_seconds"] for e in all_repeats)
        manifest["extra_optimizer_updates"]=sum(e["extra_optimizer_updates"] for e in all_repeats)
        manifest["extra_test_evaluations"]=sum(e["extra_test_evaluations"] for e in all_repeats)
        manifest_path.write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
        print(json.dumps({"event":"integrity_replay_verified","entry":entry}),flush=True)
    return manifest

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--results",type=Path,required=True)
    args=p.parse_args()
    print(json.dumps(replay(args.results),indent=2))
