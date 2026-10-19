#!/usr/bin/env python3
"""Frozen deployment audit of a pretrained causal LM on a GPU (Colab-ready).

Colab (GPU runtime), one cell:

    !git clone -q https://github.com/towre676-cloud/singularity
    %cd singularity
    !python scripts/colab_deployment_audit.py

The run is fixed before any forward pass. ``protocol.json`` records the
model and its immutable Hub revision, hardware, probes, deployment
variants, tolerance rule, comparators and timing plan; ``run`` refuses to
start if any of them changed. Then:

1. The reference deployment, two calibration clean runs and the construction
   variants are observed on every probe.
2. The exact minimum-cost panel with two separating probes per coverable
   construction variant is selected. It is compared under the same
   requirement with greedy, optimally pruned greedy (best subset of the
   greedy output), a fixed typical-text panel and random panels at the same
   budget. All 2**n subsets are scanned independently.
3. Held-out variants (including families absent from construction) and
   separate clean controls (attention backend, export round-trip, cache off,
   order) measure detection and false alarms. Nothing is reselected.
4. A standalone package is built and verified. Resident full-pool and panel
   checks are timed with CUDA synchronization, cold checks run in fresh
   processes, and break-even counts are computed.

Every variant declares the reference contract, so only executed behavior can
reveal it. Model selection by GPU memory: >=38 GB Qwen2.5-7B, >=20 GB
Qwen2.5-3B, otherwise Qwen2.5-1.5B (all Apache-2.0, not gated). Override with
--model. ``--local-test`` runs every code path on CPU with a tiny random
Qwen2 model and skips the CUDA-only quantized variants.

Results are in --output (default deployment_audit/), including summary.md and
a zip of everything. Exactness covers only the declared construction table.
Detection of held-out variants and false-alarm counts are measurements; a
passing check is not proof of equivalence.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import gc
import hashlib
import json
import math
import os
from pathlib import Path
import random
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
import unicodedata

REPOSITORY = "https://github.com/towre676-cloud/singularity"
BRANCH = "ccr-f4cbebff-f5j47k"


def _locate_root():
    """Find the repository (script, notebook cell or Colab) or clone it.

    Pasting this file into a notebook cell leaves ``__file__`` undefined, so
    also look upwards from the working directory and at /content/singularity.
    """
    candidates = []
    try:
        candidates.append(Path(__file__).resolve().parents[1])
    except NameError:
        pass
    here = Path.cwd().resolve()
    candidates += [here, *here.parents, here / "singularity", Path("/content/singularity")]
    for candidate in candidates:
        if (candidate / "src/singularity/model_audit/core.py").is_file():
            return candidate
    target = Path("/content/singularity") if Path("/content").is_dir() else here / "singularity"
    print(f"Cloning {REPOSITORY} ({BRANCH}) into {target}", flush=True)
    subprocess.check_call(["git", "clone", "-q", "--depth", "1", "-b", BRANCH, REPOSITORY, str(target)])
    return target


ROOT = _locate_root()
SCRIPT_PATH = ROOT / "scripts/colab_deployment_audit.py"
sys.path.insert(0, str(ROOT / "src"))

from singularity.model_audit.core import (  # noqa: E402  standard library only
    build_package, check_package, deviation, flags, load_package, save_package, tolerances_from_clean,
    verify_package,
)
from singularity.robust_coverage import (  # noqa: E402
    coverage_problem, fixed_panel, greedy_robust_panel, minimum_robust_panel,
)

SCHEMA = "singularity.gpu-deployment-audit/1"
REQUIREMENT = 2
CONTINUATION = 8

# (id, text, pad_to tokens or None, continuation tokens). Declared before any observation.
PROBES = [
    ("full_history", "The history of the city begins with a small settlement on the river bank, where traders "
                     "exchanged grain, salt and timber for nearly two centuries before the first bridge was built. "
                     "As the population grew, merchants from the coast arrived each summer, and a market square, "
                     "a customs house and a stone church were added around the old landing place, which remains "
                     "the centre of the town today.", None, 0),
    ("full_science", "In the experiment, the researchers measured how quickly the solution cooled after heating, "
                     "recording the temperature every ten seconds until it returned to room temperature. They "
                     "repeated the procedure with three different containers and found that the insulated flask "
                     "lost heat more slowly than either the glass beaker or the thin metal cup, as their model "
                     "had predicted.", None, CONTINUATION),
    ("full_sport", "During the 1998 season the team won eleven of its sixteen games and reached the final, "
                   "where a late penalty decided the championship in front of a record crowd. The coach, who "
                   "had joined only two years earlier, credited the young defenders and a change in training "
                   "methods, while supporters celebrated in the streets until the early hours of the next "
                   "morning.", None, 0),
    ("full_music", "The album was released in March and reached number four on the national chart, supported by "
                   "a long tour of small venues across the north of the country. Critics praised its quiet "
                   "arrangements and the singer's restrained voice, and two of its songs were later used in "
                   "films, introducing the band to a much wider audience over the following decade.", None, 0),
    ("pad_born", "He was born in 1907 and", 48, CONTINUATION),
    ("pad_river", "The river is long and", 48, CONTINUATION),
    ("pad_capital", "The capital of France is", 32, CONTINUATION),
    ("pad_church", "A church was built there in", 32, 0),
    ("short_population", "The city has a population of", None, CONTINUATION),
    ("short_first", "It was the first time that", None, 0),
    ("short_known", "She is best known for", None, 0),
    ("uni_ligature", "The ﬁnal score was ½ point — a record… and the crowd", None, CONTINUATION),
    ("uni_accents", "Café owners in Montréal and São Paulo said that", None, 0),
    ("uni_padded", "Naïve résumé ² of the", 32, 0),
    ("uni_width", "The ＡＢＣ index rose 3⁴ points in the ①st quarter", None, 0),
    ("nl_code", "def add(a, b):\n    return a + b\n\n\ndef multiply(a, b):\n", None, CONTINUATION),
    ("nl_list", "Shopping list:\n1. Bread\n2. Milk\n3.", 32, CONTINUATION),
    ("nl_header", "= Early life =\nHe grew up in a small town near the coast.\n= Career =\nHe", None, 0),
]
TYPICAL = ["full_history", "full_science", "full_sport", "full_music"]

# Each variant is applied silently: the observing code still declares the reference contract.
CONSTRUCTION = {
    "padding_mask_dropped": {"attention_mask": False},
    "positions_not_offset_for_left_padding": {"position_offset": False},
    "truncate_to_48": {"truncate_to": 48},
    "unicode_nfkc": {"normalization": "NFKC"},
    "temperature_1.3": {"temperature": 1.3},
    "int8_bitsandbytes": {"load": "int8"},
    "half_precision_export_swap": {"load": "export_other_dtype"},
}
HELDOUT = {
    "nf4_4bit_bitsandbytes": {"load": "nf4"},                    # new quantization scheme
    "kv_cache_positions_reset": {"cache_positions_reset": True},  # family absent from construction
    "right_padding_generation": {"padding_side": "right"},        # family absent from construction
    "rope_base_halved": {"rope_scale": 2.0},                      # family absent from construction
    "crlf_newlines": {"newline": "\r\n"},                         # family absent from construction
    "temperature_1.1": {"temperature": 1.1},                      # weaker strength
    "truncate_to_72": {"truncate_to": 72},                        # weaker strength
}
CALIBRATION = {"batch_size_1": {"batch_size": 1}, "batch_size_8": {"batch_size": 8}}
CLEAN_CONTROLS = {
    "eager_attention_backend": {"attention": "eager"},
    "kv_cache_disabled": {"use_cache": False},
    "same_dtype_export_roundtrip": {"load": "export_same_dtype"},
    "reversed_order": {"reverse": True},
}
TOLERANCE = {"factor": 4.0, "floor": 1e-4, "tie_margin": 0.02,
             "rule": "per probe and continuous feature: factor * max calibration deviation + floor (nats)",
             "unstable_positions": "argmax positions that change in any calibration run are treated as ties; "
                                   "a continuation that changes in any calibration run is removed from that probe"}
TIMING = {"warmup_pairs": 3, "measured_pairs": 20, "order_seed": 4401, "cold_repeats": 2}


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def write_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=1, sort_keys=True, allow_nan=False) + "\n")
    os.replace(temporary, path)


def log(message):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}", flush=True)


# ----------------------------------------------------------------- hardware and model
def hardware():
    import torch
    if not torch.cuda.is_available():
        return {"device": "cpu", "gpu": None, "memory_gb": 0., "bf16": False}
    properties = torch.cuda.get_device_properties(0)
    return {"device": "cuda", "gpu": properties.name, "memory_gb": round(properties.total_memory / 2**30, 1),
            "bf16": torch.cuda.is_bf16_supported() and properties.major >= 8,
            "compute_capability": f"{properties.major}.{properties.minor}"}


def choose_model(machine):
    if machine["memory_gb"] >= 38:
        return "Qwen/Qwen2.5-7B"
    if machine["memory_gb"] >= 20:
        return "Qwen/Qwen2.5-3B"
    return "Qwen/Qwen2.5-1.5B"


def resolve_revision(model_id):
    from huggingface_hub import HfApi
    return HfApi().model_info(model_id).sha


def local_test_model(directory):
    """Tiny random Qwen2 model plus a locally trained tokenizer (no downloads)."""
    import torch
    from tokenizers import Tokenizer, decoders, models, pre_tokenizers, trainers
    from transformers import PreTrainedTokenizerFast, Qwen2Config, Qwen2ForCausalLM
    directory = Path(directory)
    if (directory / "config.json").exists():
        return str(directory)
    core = Tokenizer(models.BPE())
    core.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
    core.decoder = decoders.ByteLevel()
    corpus = [text for _, text, _, _ in PROBES] * 5 + ["the cat sat on the mat.\n" * 20]
    core.train_from_iterator(corpus, trainers.BpeTrainer(vocab_size=600, special_tokens=["<|endoftext|>"],
                                                         initial_alphabet=pre_tokenizers.ByteLevel.alphabet()))
    tokenizer = PreTrainedTokenizerFast(tokenizer_object=core, eos_token="<|endoftext|>", pad_token="<|endoftext|>")
    torch.manual_seed(0)
    config = Qwen2Config(vocab_size=len(tokenizer), hidden_size=64, intermediate_size=128, num_hidden_layers=2,
                         num_attention_heads=4, num_key_value_heads=2, max_position_embeddings=256,
                         eos_token_id=tokenizer.eos_token_id, pad_token_id=tokenizer.pad_token_id)
    model = Qwen2ForCausalLM(config)
    model.save_pretrained(directory)
    tokenizer.save_pretrained(directory)
    return str(directory)


class Deployment:
    """Loaded reference model plus on-demand variant models."""

    def __init__(self, source, revision, dtype_name, device, scratch):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.torch, self.source, self.revision, self.device = torch, source, revision, device
        self.dtype_name, self.dtype = dtype_name, getattr(torch, dtype_name)
        self.scratch = Path(scratch)
        kwargs = {"revision": revision} if revision else {}
        self.tokenizer = AutoTokenizer.from_pretrained(source, **kwargs)
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        self.kwargs = kwargs
        self.model = self._load(torch_dtype=self.dtype)

    def _load(self, path=None, **extra):
        from transformers import AutoModelForCausalLM
        kwargs = dict(self.kwargs) if path is None else {}
        kwargs.update(extra)
        if self.device == "cuda" and "device_map" not in kwargs:
            kwargs["device_map"] = {"": 0}
        model = AutoModelForCausalLM.from_pretrained(path or self.source, attn_implementation="sdpa", **kwargs)
        if self.device == "cpu":
            model = model.to("cpu")
        return model.eval()

    def variant_model(self, kind):
        """Load a separate deployment artifact; caller must release it."""
        torch = self.torch
        if kind in ("int8", "nf4"):
            if self.device != "cuda":
                return None
            from transformers import BitsAndBytesConfig
            config = (BitsAndBytesConfig(load_in_8bit=True) if kind == "int8" else
                      BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=self.dtype))
            return self._load(quantization_config=config, torch_dtype=self.dtype)
        # Export the deployed checkpoint as safetensors shards, then load it as a deployment would:
        # in the same dtype (clean control) or in the other half-precision dtype (deployment change).
        target = self.dtype if kind == "export_same_dtype" else (
            torch.float16 if self.dtype == torch.bfloat16 else torch.bfloat16)
        directory = self.scratch / f"export_{kind}"
        shutil.rmtree(directory, ignore_errors=True)
        self.model.save_pretrained(directory, safe_serialization=True, max_shard_size="2GB")
        self.tokenizer.save_pretrained(directory)
        model = self._load(str(directory), torch_dtype=target)
        shutil.rmtree(directory, ignore_errors=True)
        return model

    def contract(self):
        tokenizer = self.tokenizer
        vocabulary = sorted(tokenizer.get_vocab().items())
        config = self.model.config.to_dict()
        for key in ("_name_or_path", "transformers_version", "torch_dtype", "dtype", "_attn_implementation_autoset"):
            config.pop(key, None)
        return {"adapter": "colab_deployment_audit", "model": self.source, "revision": self.revision,
                "dtype": self.dtype_name, "padding_side": "left", "attention_mask": True,
                "position_ids": "offset by left padding", "use_cache": True, "attention": "sdpa",
                "temperature": 1.0, "normalization": "none", "newline": "\\n", "decoding": "greedy, no processors",
                "tokenizer_vocabulary_sha256": sha(json.dumps(vocabulary).encode()),
                "model_config_sha256": sha(json.dumps(config, sort_keys=True, default=str).encode())}


# ----------------------------------------------------------------- observation
def encode(tokenizer, text, change):
    if change.get("normalization"):
        text = unicodedata.normalize(change["normalization"], text)
    if change.get("newline"):
        text = text.replace("\n", change["newline"])
    tokens = tokenizer(text, add_special_tokens=False)["input_ids"]
    return tokens[-change["truncate_to"]:] if change.get("truncate_to") else tokens


def set_attention(model, implementation):
    if hasattr(model, "set_attn_implementation"):
        model.set_attn_implementation(implementation)
    else:
        model.config._attn_implementation = implementation


def scale_rope(model, factor):
    """Multiply every rotary inv_freq buffer by 1/factor; returns an undo function."""
    saved = []
    for module in model.modules():
        if hasattr(module, "inv_freq") and module.inv_freq is not None:
            saved.append((module, module.inv_freq.clone()))
            module.inv_freq.data = module.inv_freq.data / factor
    if not saved:
        raise RuntimeError("no rotary inv_freq buffers found")

    def undo():
        for module, value in saved:
            module.inv_freq.data = value
    return undo


def observe(deployment, model, probes, change):
    """Observation lists in ``model_audit.core`` format for each probe."""
    torch = deployment.torch
    tokenizer, pad = deployment.tokenizer, deployment.tokenizer.pad_token_id
    device = next(model.parameters()).device
    change = dict(change)
    ordered = list(reversed(probes)) if change.get("reverse") else list(probes)
    restore = []
    if change.get("attention"):
        previous = getattr(model.config, "_attn_implementation", "sdpa")
        set_attention(model, change["attention"])
        restore.append(lambda: set_attention(model, previous))
    if change.get("rope_scale"):
        restore.append(scale_rope(model, change["rope_scale"]))
    try:
        prepared = []
        for probe in ordered:
            tokens = encode(tokenizer, probe["text"], change)
            width = max(len(tokens), probe.get("pad_to") or len(tokens))
            prepared.append((tokens, width, probe.get("continuation_tokens", 0)))
        groups = {}
        for index, (tokens, width, steps) in enumerate(prepared):
            groups.setdefault((width, steps), []).append(index)
        results = [None] * len(ordered)
        size = change.get("batch_size", 4)
        with torch.inference_mode():
            for (width, steps), members in sorted(groups.items()):
                for start in range(0, len(members), size):
                    chunk = members[start:start + size]
                    for index, value in zip(chunk, _observe_batch(torch, model, device, pad,
                                                                  [prepared[i][0] for i in chunk], width, steps, change)):
                        results[index] = value
    finally:
        for undo in reversed(restore):
            undo()
    return list(reversed(results)) if change.get("reverse") else results


def _observe_batch(torch, model, device, pad, rows, width, steps, change):
    right = change.get("padding_side") == "right"
    pads = [width - len(tokens) for tokens in rows]
    ids = torch.tensor([tokens + [pad] * p if right else [pad] * p + tokens for tokens, p in zip(rows, pads)], device=device)
    real = torch.tensor([[(j < len(t)) if right else (j >= p) for j in range(width)] for t, p in zip(rows, pads)], device=device)
    mask = real.long()
    base = torch.arange(width, device=device)[None].repeat(len(rows), 1)
    offset = change.get("position_offset", True) and not right
    positions = (base - torch.tensor(pads, device=device)[:, None]).clamp(min=0) if offset else base
    use_cache = bool(steps) and change.get("use_cache", True)
    arguments = {"input_ids": ids, "position_ids": positions, "use_cache": use_cache}
    if change.get("attention_mask", True):
        arguments["attention_mask"] = mask
    output = model(**arguments)
    temperature = change.get("temperature", 1.0)
    logp = (output.logits.float() / temperature).log_softmax(-1)
    top = logp.topk(2, dim=-1)
    entropy = -(logp.exp() * logp).sum(-1)
    observations = []
    for row, (tokens, p) in enumerate(zip(rows, pads)):
        keep = slice(0, len(tokens)) if right else slice(p, width)
        observations.append({"argmax": logp[row, keep].argmax(-1).tolist(),
                             "top_logprob": top.values[row, keep, 0].tolist(),
                             "top_gap": (top.values[row, keep, 0] - top.values[row, keep, 1]).tolist(),
                             "entropy": entropy[row, keep].tolist()})
    if steps:
        # Correct code continues from the last real token; right padding continues from the last column.
        last = logp[:, -1]
        past = output.past_key_values if use_cache else None
        next_position = positions[:, -1:] + 1
        tokens_out = [[] for _ in rows]
        values_out = [[] for _ in rows]
        for step in range(steps):
            choice = last.argmax(-1)
            for row in range(len(rows)):
                tokens_out[row].append(int(choice[row]))
                values_out[row].append(float(last[row, choice[row]]))
            if step == steps - 1:
                break
            mask = torch.cat((mask, torch.ones((len(rows), 1), dtype=mask.dtype, device=device)), 1)
            arguments = {"use_cache": use_cache}
            if change.get("attention_mask", True):
                arguments["attention_mask"] = mask
            if use_cache:
                position = torch.full_like(next_position, step) if change.get("cache_positions_reset") else next_position
                output = model(input_ids=choice[:, None], past_key_values=past, position_ids=position, **arguments)
                past = output.past_key_values
            else:
                ids = torch.cat((ids, choice[:, None]), 1)
                positions = torch.cat((positions, next_position), 1)
                output = model(input_ids=ids, position_ids=positions, **arguments)
            next_position = next_position + 1
            last = (output.logits[:, -1].float() / temperature).log_softmax(-1)
        for row, observation in enumerate(observations):
            observation["continuation"] = tokens_out[row]
            observation["continuation_logprob"] = values_out[row]
    return observations


def run_change(deployment, probes, change):
    """Observe one change; loads and releases separate artifacts when needed."""
    torch = deployment.torch
    kind = change.get("load")
    rest = {k: v for k, v in change.items() if k != "load"}
    if kind is None:
        return observe(deployment, deployment.model, probes, rest)
    model = deployment.variant_model(kind)
    if model is None:
        return None
    try:
        return observe(deployment, model, probes, rest)
    finally:
        del model
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


def stabilize(reference, calibration, tie_margin):
    """Apply the declared unstable-position rule to the reference copy."""
    stable, removed, ties = copy.deepcopy(reference), [], 0
    for index, expected in enumerate(stable):
        for run in calibration:
            got = run[index]
            for position, (a, b) in enumerate(zip(got["argmax"], expected["argmax"])):
                if a != b and expected["top_gap"][position] > tie_margin:
                    expected["top_gap"][position] = 0.
                    ties += 1
            if "continuation" in expected and got.get("continuation") != expected["continuation"]:
                expected.pop("continuation")
                expected.pop("continuation_logprob")
                removed.append(index)
    return stable, sorted(set(removed)), ties


# ----------------------------------------------------------------- phases
def probe_records(tokenizer):
    records = []
    for identifier, text, pad_to, steps in PROBES:
        length = len(tokenizer(text, add_special_tokens=False)["input_ids"])
        if pad_to is not None and length > pad_to:
            raise ValueError(f"probe {identifier} has {length} tokens, more than pad_to={pad_to}")
        record = {"id": identifier, "text": text, "tokens": length, "cost": (pad_to or length) + steps}
        if pad_to is not None:
            record["pad_to"] = pad_to
        if steps:
            record["continuation_tokens"] = steps
        records.append(record)
    return records


def freeze(args, output):
    from transformers import AutoTokenizer
    import torch
    import transformers
    if (output / "protocol.json").exists():
        raise FileExistsError(f"{output}/protocol.json already exists; use a new --output directory")
    machine = hardware()
    if args.local_test:
        model_id, revision = local_test_model(output.parent / "local_test_model"), None
        dtype = "float32"
    else:
        if machine["device"] != "cuda":
            raise SystemExit("No GPU found. In Colab: Runtime > Change runtime type > GPU. Use --local-test for a CPU smoke test.")
        model_id = args.model or choose_model(machine)
        revision = resolve_revision(model_id)
        dtype = "bfloat16" if machine["bf16"] else "float16"
    tokenizer = AutoTokenizer.from_pretrained(model_id, **({"revision": revision} if revision else {}))
    probes = probe_records(tokenizer)
    protocol = {
        "schema": SCHEMA, "model": model_id, "revision": revision, "dtype": dtype, "hardware": machine,
        "software": {"python": sys.version.split()[0], "torch": torch.__version__, "transformers": transformers.__version__},
        "probes": probes, "typical_panel": TYPICAL, "construction_variants": CONSTRUCTION, "heldout_variants": HELDOUT,
        "calibration_clean_runs": CALIBRATION, "clean_controls": CLEAN_CONTROLS, "tolerance": TOLERANCE,
        "requirement": REQUIREMENT, "timing": TIMING,
        "cost": "forwarded tokens: pad width (or token length) plus continuation steps",
        "selection": "exact minimum-cost 2-robust coverage of construction variants with at least two separating probes; "
                     "variants with fewer are reported and excluded from the requirement",
        "comparators": {"greedy": "cost per remaining deficit", "pruned_greedy": "minimum-cost subset of the greedy output meeting the same requirement",
                        "typical": "four full-length typical paragraphs", "random": "1000 seeded random orders filled within the exact budget"},
        "silent_variants": "every variant declares the reference contract",
        "local_test": bool(args.local_test),
        "script_sha256": sha(SCRIPT_PATH.read_bytes()),
        "frozen_at_utc": now(),
        "claim_boundary": "Exact coverage of the declared construction table only; held-out detection, false alarms and timings are measurements on this run.",
    }
    protocol["protocol_sha256"] = sha(canonical({k: v for k, v in protocol.items() if k != "frozen_at_utc"}))
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "protocol.json", protocol)
    log(f"Protocol frozen before any forward pass: {model_id}@{revision} {dtype} sha256={protocol['protocol_sha256'][:16]}")
    return protocol


def checked_protocol(output):
    protocol = json.loads((output / "protocol.json").read_text())
    body = {k: v for k, v in protocol.items() if k not in ("frozen_at_utc", "protocol_sha256")}
    if sha(canonical(body)) != protocol["protocol_sha256"] or protocol["script_sha256"] != sha(SCRIPT_PATH.read_bytes()):
        raise ValueError("protocol or script changed after freezing")
    return protocol


def deployment_for(protocol, output):
    device = "cpu" if protocol["local_test"] else "cuda"
    return Deployment(protocol["model"], protocol["revision"], protocol["dtype"], device, output / "scratch")


def independent_minimum(rows, costs):
    width = len(rows[0])
    masks = [sum(1 << e for e in range(len(rows)) if rows[e][p]) for p in range(width)]
    best = None
    for subset in range(1 << len(rows)):
        if all(bin(subset & m).count("1") >= REQUIREMENT for m in masks):
            cost = sum(costs[e] for e in range(len(rows)) if subset >> e & 1)
            best = cost if best is None or cost < best else best
    return best


def pruned_greedy(problem, greedy_panel):
    best = None
    for size in range(1, len(greedy_panel) + 1):
        for subset in __import__("itertools").combinations(greedy_panel, size):
            report = fixed_panel(problem, subset, REQUIREMENT)
            if report["satisfies_requirement"] and (best is None or report["cost"] < best["cost"]):
                best = report
    return best


def run(args, output):
    protocol = checked_protocol(output)
    if (output / "results.json").exists():
        raise FileExistsError("results already exist; freeze a new --output directory")
    torch_seconds = {}
    probes = protocol["probes"]
    ids = [p["id"] for p in probes]
    spec = protocol["tolerance"]
    started = time.perf_counter()
    log("Loading reference deployment")
    deployment = deployment_for(protocol, output)
    torch_seconds["load_reference"] = time.perf_counter() - started
    contract = deployment.contract()

    observed = {}

    def capture(group, name, change):
        t0 = time.perf_counter()
        rows = run_change(deployment, probes, change)
        observed[f"{group}/{name}"] = rows
        torch_seconds[f"{group}/{name}"] = time.perf_counter() - t0
        log(f"  {group}/{name}: {'skipped (needs CUDA)' if rows is None else f'{time.perf_counter() - t0:.1f}s'}")
        return rows

    construction_started = time.perf_counter()
    reference = capture("reference", "reference", {})
    calibration = [capture("calibration", name, change) for name, change in protocol["calibration_clean_runs"].items()]
    stable, removed, ties = stabilize(reference, calibration, spec["tie_margin"])
    tolerances, maxima = tolerances_from_clean(stable, calibration, spec["factor"], spec["floor"], spec["tie_margin"])
    construction_rows = {name: capture("construction", name, change) for name, change in protocol["construction_variants"].items()}
    construction_rows = {k: v for k, v in construction_rows.items() if v is not None}

    def separation(rows):
        return [flags(deviation(o, r, spec["tie_margin"]), t) for o, r, t in zip(rows, stable, tolerances)]

    table = {name: separation(rows) for name, rows in construction_rows.items()}
    coverable = [name for name in table if sum(table[name]) >= REQUIREMENT]
    excluded = {name: sum(table[name]) for name in table if name not in coverable}
    if not coverable:
        raise RuntimeError("no construction variant has two separating probes")
    rows = [[table[name][e] for name in coverable] for e in range(len(probes))]
    costs = [p["cost"] for p in probes]
    problem = coverage_problem(costs, rows, ids, coverable)
    exact = minimum_robust_panel(problem, REQUIREMENT)
    greedy = greedy_robust_panel(problem, REQUIREMENT)
    oracle = independent_minimum(rows, costs)
    if oracle != exact.cost:
        raise ArithmeticError("exact solver disagrees with independent enumeration")
    pruned = pruned_greedy(problem, greedy.panel)
    typical = fixed_panel(problem, [ids.index(i) for i in protocol["typical_panel"]], REQUIREMENT)
    rng, randoms = random.Random(9137), []
    for _ in range(1000):
        order, chosen, spent = list(range(len(probes))), [], 0
        rng.shuffle(order)
        for e in order:
            if spent + costs[e] <= exact.cost:
                chosen.append(e)
                spent += costs[e]
        randoms.append(fixed_panel(problem, chosen, REQUIREMENT))
    panels = {"exact": list(exact.panel), "greedy": list(greedy.panel), "pruned_greedy": pruned["panel"],
              "typical": [ids.index(i) for i in protocol["typical_panel"]]}
    construction_seconds = time.perf_counter() - construction_started
    frozen = {name: [ids[e] for e in panel] for name, panel in panels.items()}
    write_json(output / "frozen_panels.json", {"panels": frozen, "frozen_at_utc": now(), "before_audit": True})
    log(f"Panels frozen: exact {int(exact.cost)} tokens, pruned greedy {int(pruned['cost'])}, greedy {int(greedy.cost)}, "
        f"full pool {sum(costs)}")

    audit_started = time.perf_counter()
    heldout_rows = {name: capture("heldout", name, change) for name, change in protocol["heldout_variants"].items()}
    heldout_rows = {k: v for k, v in heldout_rows.items() if v is not None}
    control_rows = {name: capture("control", name, change) for name, change in protocol["clean_controls"].items()}
    control_rows = {k: v for k, v in control_rows.items() if v is not None}
    audit_tables = {**{f"construction/{k}": table[k] for k in table},
                    **{f"heldout/{k}": separation(v) for k, v in heldout_rows.items()},
                    **{f"control/{k}": separation(v) for k, v in control_rows.items()}}
    evaluation = {}
    for name, panel in panels.items():
        result = {"probe_ids": [ids[e] for e in panel], "cost": sum(costs[e] for e in panel), "variants": {}}
        for variant, flagged in audit_tables.items():
            count = sum(flagged[e] for e in panel)
            result["variants"][variant] = {"separating_probes": count, "detected": count >= 1, "robust": count >= REQUIREMENT}
        result["construction_robust"] = sum(result["variants"][f"construction/{k}"]["robust"] for k in coverable)
        result["heldout_detected"] = sum(v["detected"] for k, v in result["variants"].items() if k.startswith("heldout/"))
        result["false_alarms"] = [k for k, v in result["variants"].items() if k.startswith("control/") and v["detected"]]
        evaluation[name] = result
    full_pool = {variant: sum(flagged) for variant, flagged in audit_tables.items()}

    package = build_package(probes, stable, calibration, {k: construction_rows[k] for k in coverable}, contract=contract,
                            requirement=REQUIREMENT, tolerance_factor=spec["factor"], tolerance_floor=spec["floor"],
                            tie_margin=spec["tie_margin"], panel_ids=frozen["exact"],
                            metadata={"model": protocol["model"], "revision": protocol["revision"],
                                      "protocol_sha256": protocol["protocol_sha256"]})
    save_package(package, output / "package.json")
    verification = verify_package(package)
    index = {p["id"]: e for e, p in enumerate(probes)}
    package_checks = {}
    every = ([(f"construction/{k}", v) for k, v in construction_rows.items()] +
             [(f"heldout/{k}", v) for k, v in heldout_rows.items()] + [(f"control/{k}", v) for k, v in control_rows.items()])
    for variant, rows_ in every:
        report = check_package(package, lambda ps, rows_=rows_: [rows_[index[p["id"]]] for p in ps], contract)
        package_checks[variant] = {"verdict": report["verdict"], "flagged_probes": report["flagged_probes"]}
    audit_seconds = time.perf_counter() - audit_started

    log("Timing resident checks")
    timing = resident_timing(deployment, probes, package, contract)
    development = construction_seconds + audit_seconds
    saved = timing["full_pool_median_seconds"] - timing["panel_check_median_seconds"]
    results = {
        "schema": SCHEMA, "protocol_sha256": protocol["protocol_sha256"], "created_at_utc": now(),
        "contract": contract, "unstable_reference": {"tie_positions_added": ties, "continuations_removed": [ids[i] for i in removed]},
        "clean_calibration_maxima": maxima, "tolerances": tolerances,
        "construction_separators": {k: sum(v) for k, v in table.items()},
        "construction_excluded_fewer_than_two_separators": excluded, "coverable": coverable,
        "independent_enumeration": {"subsets": 1 << len(probes), "minimum_cost": oracle},
        "panels": evaluation, "full_pool_separators": full_pool,
        "random_at_exact_budget": {"draws": 1000, "meeting_requirement": sum(r["satisfies_requirement"] for r in randoms),
                                   "mean_cost": statistics.fmean(int(r["cost"]) for r in randoms)},
        "exact_vs_pruned_greedy_token_saving": 1 - int(exact.cost) / int(pruned["cost"]),
        "package": {"file": "package.json", "verification": verification, "checks": package_checks,
                    "checks_use": "stored full-pool observations of each variant, restricted by the package to its panel"},
        "skipped_variants": [k.split("/", 1)[1] for k, v in observed.items() if v is None],
        "seconds": {"observations": torch_seconds, "construction": construction_seconds, "audit": audit_seconds,
                    "development_total": development},
        "timing": timing,
        "break_even_checks": {"construction_only": math.ceil(construction_seconds / saved) if saved > 0 else None,
                              "construction_plus_audit": math.ceil(development / saved) if saved > 0 else None},
    }
    observations_path = output / "observations.json"
    write_json(observations_path, {k: v for k, v in observed.items() if v is not None})
    write_json(output / "results.json", results)
    del deployment
    gc.collect()
    if not args.skip_cold:
        results["timing"]["cold_checks"] = cold_checks(output)
        write_json(output / "results.json", results)
    write_summary(output, protocol, results)
    archive = shutil.make_archive(str(output), "zip", output)
    log(f"Done. Summary: {output / 'summary.md'}  Archive: {archive}")
    return results


def resident_timing(deployment, probes, package, contract):
    torch = deployment.torch

    def synchronized(function):
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        t0 = time.perf_counter()
        function()
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        return time.perf_counter() - t0

    full = lambda: observe(deployment, deployment.model, probes, {})
    by_id = {p["id"]: p for p in probes}
    panel = lambda: check_package(package, lambda ps: observe(deployment, deployment.model, [by_id[p["id"]] for p in ps], {}), contract)
    for _ in range(TIMING["warmup_pairs"]):
        full()
        panel()
    rng, records = random.Random(TIMING["order_seed"]), []
    for repeat in range(TIMING["measured_pairs"]):
        order = ["full_pool", "panel_check"]
        rng.shuffle(order)
        records.append({"repeat": repeat, "order": order,
                        **{label: synchronized(full if label == "full_pool" else panel) for label in order}})
    verdict = panel()["verdict"]
    return {"records": records, "full_pool_median_seconds": statistics.median(r["full_pool"] for r in records),
            "panel_check_median_seconds": statistics.median(r["panel_check"] for r in records),
            "speed_ratio": statistics.median(r["full_pool"] for r in records) / statistics.median(r["panel_check"] for r in records),
            "resident_reference_verdict": verdict,
            "includes": "panel time includes package verification and comparison; full-pool time is observation only"}


def cold_checks(output):
    records = []
    for _ in range(TIMING["cold_repeats"]):
        t0 = time.perf_counter()
        completed = subprocess.run([sys.executable, str(SCRIPT_PATH), "--phase", "cold-check", "--output", str(output)],
                                   capture_output=True, text=True)
        record = {"process_wall_seconds": time.perf_counter() - t0, "exit_code": completed.returncode}
        try:
            record.update(json.loads(completed.stdout.strip().splitlines()[-1]))
        except (IndexError, ValueError):
            record["stderr_tail"] = completed.stderr[-2000:]
        records.append(record)
        log(f"  cold check: {record['process_wall_seconds']:.1f}s, verdict {record.get('verdict')}")
    return records


def cold_check(output):
    t0 = time.perf_counter()
    protocol = json.loads((output / "protocol.json").read_text())
    package = load_package(output / "package.json")
    deployment = deployment_for(protocol, output)
    loaded = time.perf_counter()
    by_id = {p["id"]: p for p in protocol["probes"]}
    report = check_package(package, lambda ps: observe(deployment, deployment.model, [by_id[p["id"]] for p in ps], {}),
                           deployment.contract())
    print(json.dumps({"verdict": report["verdict"], "load_seconds": loaded - t0, "check_seconds": time.perf_counter() - loaded}))


def write_summary(output, protocol, results):
    panels = results["panels"]
    lines = [f"# Deployment audit: {protocol['model']}", "",
             f"Revision `{protocol['revision']}`, {protocol['dtype']} on {protocol['hardware'].get('gpu') or 'CPU'}; "
             f"protocol `{protocol['protocol_sha256'][:16]}` frozen {protocol['frozen_at_utc']}.", "",
             "| Panel | Tokens | Construction variants with 2 separators | Held-out detected | False alarms |", "|---|---:|---:|---:|---|"]
    heldout = sum(1 for k in results["full_pool_separators"] if k.startswith("heldout/"))
    for name in ("exact", "pruned_greedy", "greedy", "typical"):
        p = panels[name]
        lines.append(f"| {name} | {p['cost']} | {p['construction_robust']}/{len(results['coverable'])} | "
                     f"{p['heldout_detected']}/{heldout} | {', '.join(p['false_alarms']) or 'none'} |")
    timing = results["timing"]
    lines += ["", f"Full pool: {sum(x['cost'] for x in protocol['probes'])} tokens. Exact panel saves "
                  f"{100 * results['exact_vs_pruned_greedy_token_saving']:.2f}% of tokens versus optimally pruned greedy. "
                  f"Random panels at the exact budget meeting the requirement: {results['random_at_exact_budget']['meeting_requirement']}/1000.",
              f"Excluded construction variants (fewer than two separating probes): {results['construction_excluded_fewer_than_two_separators'] or 'none'}.",
              f"Skipped variants: {results['skipped_variants'] or 'none'}.", "",
              f"Resident: full pool {timing['full_pool_median_seconds']:.4f}s vs panel check {timing['panel_check_median_seconds']:.4f}s "
              f"({timing['speed_ratio']:.2f}x). Break-even: {results['break_even_checks']['construction_only']} checks "
              f"(construction), {results['break_even_checks']['construction_plus_audit']} (construction + audit).",
              f"Cold checks: {[round(c['process_wall_seconds'], 1) for c in timing.get('cold_checks', [])]} seconds.",
              f"Package verified: {results['package']['verification']['verified']}.", "",
              "Per-variant separators in the full pool:", ""]
    lines += [f"- {k}: {v}" for k, v in sorted(results["full_pool_separators"].items())]
    lines += ["", protocol["claim_boundary"]]
    (output / "summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def ensure_dependencies(local_test):
    missing = []
    for module, package in (("transformers", "transformers"), ("accelerate", "accelerate"),
                            ("bitsandbytes", "bitsandbytes"), ("huggingface_hub", "huggingface_hub")):
        if local_test and module == "bitsandbytes":
            continue
        try:
            __import__(module)
        except ImportError:
            missing.append(package)
    if missing:
        log("Installing " + " ".join(missing))
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", *missing])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", help="Hub model id (default: chosen from GPU memory)")
    parser.add_argument("--output", type=Path, default=Path("deployment_audit"))
    parser.add_argument("--phase", choices=("all", "freeze", "run", "cold-check"), default="all")
    parser.add_argument("--local-test", action="store_true", help="CPU smoke test with a tiny random Qwen2 model")
    parser.add_argument("--skip-cold", action="store_true", help="skip fresh-process cold checks")
    # parse_known_args ignores the kernel arguments a notebook passes (e.g. -f kernel.json).
    args, _ = parser.parse_known_args(argv)
    output = args.output.resolve()
    if args.phase == "cold-check":
        return cold_check(output)
    ensure_dependencies(args.local_test)
    if args.phase in ("all", "freeze"):
        freeze(args, output)
    if args.phase in ("all", "run"):
        run(args, output)


if __name__ == "__main__":
    main()
