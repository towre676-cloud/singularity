"""Frozen modular orbits and strict, separately supplied byte corpora."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import random

import torch
import torch.nn.functional as F


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


@dataclass
class TaskData:
    splits: dict
    metadata: dict

    def sample(self, batch_size, generator):
        rows = self.splits["train"]
        index = torch.randint(len(rows["labels"]), (batch_size,), generator=generator)
        return {k: v[index] for k, v in rows.items()}


def _prime(p):
    return isinstance(p, int) and not isinstance(p, bool) and p >= 5 and p % 2 and all(p % d for d in range(3, int(p**0.5) + 1, 2))


def modular_addition(p, split_seed=1729, train_fraction=.5, tune_fraction=.25,
                     train_orbits_per_label=None, tune_orbits_per_label=None,
                     test_orbits_per_label=None):
    """Partition unordered input orbits per output class, then expand order.

    Every pair appears in exactly one split. Explicit orbit counts must consume
    the complete per-label population (p+1)//2; no hidden leftover population.
    """
    if not _prime(p):
        raise ValueError("p must be an odd prime at least five")
    population = (p + 1) // 2
    explicit = (train_orbits_per_label, tune_orbits_per_label, test_orbits_per_label)
    if any(x is not None for x in explicit):
        if any(not isinstance(x, int) or isinstance(x, bool) or x < 1 for x in explicit):
            raise ValueError("supply three positive integer orbit counts")
        counts = explicit
        if sum(counts) != population:
            raise ValueError("orbit counts must cover the complete label population")
    else:
        if not 0 < train_fraction < 1 or not 0 < tune_fraction < 1 or train_fraction + tune_fraction >= 1:
            raise ValueError("train/tune fractions must leave a positive test fraction")
        nt = max(1, int(population * train_fraction))
        nv = max(1, int(population * tune_fraction))
        if nt + nv >= population:
            nt = population - nv - 1
        counts = nt, nv, population - nt - nv
        if min(counts) < 1:
            raise ValueError("not enough orbits for three nonempty splits")
    rng = random.Random(split_seed)
    pairs = {k: [] for k in ("train", "tune", "test")}
    labels = {k: [] for k in pairs}
    orbits = {k: [] for k in pairs}
    for y in range(p):
        candidates = [(a, b) for a in range(p) for b in range(a, p) if (a + b) % p == y]
        rng.shuffle(candidates)
        offset = 0
        for split, n in zip(pairs, counts):
            for a, b in candidates[offset:offset+n]:
                orbits[split].append([a, b, y])
                for pair in ([(a, b)] if a == b else [(a, b), (b, a)]):
                    pairs[split].append(pair)
                    labels[split].append(y)
            offset += n
    splits = {s: {"input_ids": torch.tensor(pairs[s], dtype=torch.long),
                  "labels": torch.tensor(labels[s], dtype=torch.long)} for s in pairs}
    metadata = {"task": "modular_addition", "p": p, "split_seed": split_seed,
                "split_unit": "unordered input orbit {a,b}, stratified by (a+b)%p",
                "orbits_per_label": dict(zip(pairs, counts)), "orbits": orbits,
                "counts": {s: {"examples": len(labels[s]), "orbits": len(orbits[s]),
                               "valid_targets": len(labels[s])} for s in pairs},
                "split_sha256": canonical_hash(orbits)}
    return TaskData(splits, metadata)


def _byte_windows(raw, seq_len):
    if len(raw) < 2:
        raise ValueError("each byte corpus needs at least two bytes")
    tokens = torch.tensor(list(raw), dtype=torch.long)
    n = (len(tokens) - 1 + seq_len - 1) // seq_len
    x = torch.zeros((n, seq_len), dtype=torch.long)
    y = torch.full((n, seq_len), -100, dtype=torch.long)
    for i in range(n):
        start = i * seq_len
        take = min(seq_len, len(tokens) - start - 1)
        x[i, :take] = tokens[start:start+take]
        y[i, :take] = tokens[start+1:start+take+1]
    return {"input_ids": x, "labels": y}


def byte_language(train_path, tune_path, test_path, seq_len=64):
    """Every noninitial corpus byte is a target once; padding labels ignored.

    The caller supplies separate corpus files. No download or fallback corpus is
    substituted. Distinct paths and distinct content hashes are required.
    """
    if not isinstance(seq_len, int) or seq_len < 1:
        raise ValueError("seq_len must be positive")
    paths = [Path(p).expanduser().resolve(strict=True) for p in (train_path, tune_path, test_path)]
    if len(set(paths)) != 3:
        raise ValueError("train, tune, test must be separate paths")
    raw = [p.read_bytes() for p in paths]
    hashes = [hashlib.sha256(b).hexdigest() for b in raw]
    if len(set(hashes)) != 3:
        raise ValueError("identical corpus contents cannot occupy distinct splits")
    splits = {s: _byte_windows(b, seq_len) for s, b in zip(("train", "tune", "test"), raw)}
    metadata = {"task": "byte_lm", "vocabulary": "raw bytes 0..255", "seq_len": seq_len,
                "target_shift": "one byte, constructed here; model returns unshifted logits",
                "padding_target": -100, "corpora": {s: {"path": str(p), "bytes": len(b), "sha256": h}
                  for s, p, b, h in zip(splits, paths, raw, hashes)},
                "counts": {s: {"examples": len(v["labels"]), "valid_targets": int((v["labels"] != -100).sum())}
                           for s, v in splits.items()}}
    metadata["split_sha256"] = canonical_hash(metadata["corpora"])
    return TaskData(splits, metadata)


def loss_from_logits(logits, batch):
    target = batch["labels"]
    return F.cross_entropy(logits.reshape(-1, logits.shape[-1]), target.reshape(-1), ignore_index=-100)


def build_data(cfg):
    task = cfg.get("task", "modular_addition")
    task_cfg = task if isinstance(task, dict) else {"name": task}
    name = task_cfg.get("name", "modular_addition")
    d = {**cfg.get("data", {}), **task_cfg}
    if name in ("modular_addition", "modular"):
        split = {**cfg.get("split", {}), **d.get("split", {})}
        keys = ("split_seed", "train_fraction", "tune_fraction", "train_orbits_per_label", "tune_orbits_per_label", "test_orbits_per_label")
        return modular_addition(int(d.get("p", cfg.get("p", 31))), **{k: split.get(k, d.get(k)) for k in keys if split.get(k, d.get(k)) is not None})
    if name in ("byte_lm", "byte"):
        return byte_language(d["train_path"], d["tune_path"], d["test_path"], int(d.get("seq_len", 64)))
    raise ValueError("unknown task: " + str(name))
