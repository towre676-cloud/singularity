"""Bounded CPU FP32 TorchScript export for eager Llama causal models.

The saved artifact contains an executable traced graph and its parameters,
not merely a reloaded Hugging Face state dictionary. An explicit additive
causal/padding mask avoids tracing the Python control flow of transformers'
mask-selection utilities. Batch and sequence dimensions remain tensor-derived.

This deliberately narrow contract supports no KV cache, no dynamic RoPE
scaling, int64 CPU token/mask/position tensors, and the declared shape bounds.
The callable returned by ``load_causal_graph`` enforces those bounds outside
the graph. Observational agreement on deployment probes must still be checked;
a successful trace is not a general proof of equivalence.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

__all__ = ["export_causal_graph", "load_causal_graph", "trace_and_load"]


def _file_sha256(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def _wrapper(model):
    import torch

    class ExplicitMaskCausalGraph(torch.nn.Module):
        def __init__(self, source):
            super().__init__()
            self.model = source

        def forward(self, input_ids, attention_mask, position_ids):
            width = input_ids.shape[1]
            index = torch.arange(width, device=input_ids.device)
            causal = index[None, :] <= index[:, None]
            allowed = causal[None, None, :, :] & attention_mask[:, None, None, :].bool()
            additive = torch.zeros(allowed.shape, dtype=torch.float32, device=input_ids.device)
            additive = additive.masked_fill(~allowed, torch.finfo(torch.float32).min)
            return self.model(input_ids=input_ids, attention_mask=additive,
                              position_ids=position_ids, use_cache=False, return_dict=False)[0]

    return ExplicitMaskCausalGraph(model).eval()


def export_causal_graph(model, path, *, max_context=96, max_batch_size=3):
    """Trace and save an eager CPU FP32 Llama, returning a JSON manifest.

    No weights are copied into a second resident model here. The caller may
    delete its source before ``load_causal_graph`` to control peak memory.
    The deterministic trace input has two rows where the bound permits it;
    shape portability is checked separately by the unit/deployment studies.
    """
    import torch
    import transformers

    for name, value in (("max_context", max_context), ("max_batch_size", max_batch_size)):
        if type(value) is not int or value < 1:
            raise ValueError(name + " must be a positive integer")
    config = model.config
    if getattr(config, "model_type", None) != "llama":
        raise ValueError("only LlamaForCausalLM-style eager models are supported")
    if getattr(config, "_attn_implementation", None) != "eager":
        raise ValueError("export requires the eager attention implementation")
    if getattr(config, "rope_scaling", None):
        raise ValueError("dynamic or scaled RoPE is outside the export contract")
    if max_context > config.max_position_embeddings:
        raise ValueError("max_context exceeds the model positional contract")
    if model.training:
        raise ValueError("export requires model.eval()")
    parameters = list(model.parameters())
    if not parameters or any(p.device.type != "cpu" or p.dtype != torch.float32 for p in parameters):
        raise ValueError("export requires all parameters to be CPU float32")
    destination = Path(path)
    if destination.exists():
        raise FileExistsError("refusing to replace an existing graph artifact")
    destination.parent.mkdir(parents=True, exist_ok=True)
    batch, width = min(max_batch_size, 2), min(max_context, 8)
    ids = torch.arange(batch * width, dtype=torch.long).reshape(batch, width) % config.vocab_size
    mask = torch.ones_like(ids)
    positions = torch.arange(width, dtype=torch.long)[None, :].expand(batch, -1).contiguous()
    with torch.inference_mode():
        graph = torch.jit.trace(_wrapper(model), (ids, mask, positions), check_trace=True, strict=True)
        graph.save(str(destination))
    return {"schema": "singularity.causal-torchscript/1", "graph_export": True,
            "format": "torch.jit.trace executable graph with parameters; no KV cache",
            "model_class": type(model).__name__, "model_type": config.model_type,
            "torch_version": torch.__version__, "transformers_version": transformers.__version__,
            "dtype": "torch.float32", "device": "cpu", "attention": "explicit additive causal and key-padding mask",
            "missing_attention_mask": "all token positions are visible subject to causality",
            "max_context": max_context, "max_batch_size": max_batch_size,
            "vocabulary_size": int(config.vocab_size), "max_position_id": max_context - 1,
            "inputs": "three CPU int64 rank-two tensors of equal shape: token ids, binary mask, position ids",
            "trace_shape": [batch, width], "use_cache": False,
            "artifact_bytes": destination.stat().st_size, "artifact_sha256": _file_sha256(destination)}


class _LoadedCausalGraph:
    def __init__(self, graph, manifest):
        self.graph, self.manifest = graph, json.loads(json.dumps(manifest))

    def __call__(self, input_ids, attention_mask, position_ids):
        return self.forward(input_ids, attention_mask, position_ids)

    def forward(self, input_ids, attention_mask, position_ids):
        import torch

        if attention_mask is None:
            attention_mask = torch.ones_like(input_ids)
        tensors = (input_ids, attention_mask, position_ids)
        if any(not isinstance(x, torch.Tensor) or x.dtype != torch.long or x.device.type != "cpu"
               or x.ndim != 2 for x in tensors):
            raise ValueError("graph inputs must be CPU int64 rank-two tensors")
        if any(x.shape != input_ids.shape for x in tensors):
            raise ValueError("graph input shapes must agree")
        batch, width = input_ids.shape
        if not 1 <= batch <= self.manifest["max_batch_size"] or not 1 <= width <= self.manifest["max_context"]:
            raise ValueError("graph input exceeds declared batch/sequence bounds")
        if bool(((input_ids < 0) | (input_ids >= self.manifest["vocabulary_size"])).any()):
            raise ValueError("token id is outside the exported vocabulary")
        if bool(((attention_mask != 0) & (attention_mask != 1)).any()):
            raise ValueError("attention mask must be binary")
        if bool(((position_ids < 0) | (position_ids > self.manifest["max_position_id"])).any()):
            raise ValueError("position id is outside the declared export bound")
        return self.graph(input_ids, attention_mask, position_ids)


def load_causal_graph(path, manifest):
    """Verify the local exported artifact and load its executable graph."""
    import torch

    if manifest.get("schema") != "singularity.causal-torchscript/1" or not manifest.get("graph_export"):
        raise ValueError("unknown graph manifest schema")
    if Path(path).stat().st_size != manifest["artifact_bytes"] or _file_sha256(path) != manifest["artifact_sha256"]:
        raise ValueError("graph artifact does not match its manifest")
    graph = torch.jit.load(str(path), map_location="cpu").eval()
    return _LoadedCausalGraph(graph, manifest)


def trace_and_load(model, path, *, max_context=96, max_batch_size=3):
    """Convenience export/load pair; source and graph coexist in memory."""
    manifest = export_causal_graph(model, path, max_context=max_context, max_batch_size=max_batch_size)
    return load_causal_graph(path, manifest), manifest
