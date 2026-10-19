"""PyTorch and Hugging Face adapters producing audit observations.

Every adapter turns probe dicts (``text``, optional ``pad_to`` and
``continuation_tokens``) into the observation lists of ``core``. Inputs are
encoded, truncated to the last ``truncate_to`` tokens, left padded to
``pad_to`` with an explicit pad id (``truncate_to`` defaults to ``max_context``), and scored teacher-forced at every real
position. Continuations are greedy and incremental: with ``use_cache`` they
reuse key/value caches and explicit positions; without it they recompute the
whole prefix. No sampling or logits processor is applied; ``temperature``
divides logits before the softmax and is part of the declared contract.

``contract()`` returns the declared execution settings that ``check_package``
compares. The study harness can give an adapter a ``declared_contract`` that
differs from its executed behavior; that is how silent deployment faults are
simulated. Users should normally leave it unset.
"""
from __future__ import annotations

import hashlib
import json
import unicodedata

__all__ = ["LogitAdapter", "TorchCallableAdapter", "ByteTransformerAdapter", "HuggingFaceCausalAdapter",
           "tokenizer_fingerprint"]


def _normalize(text, normalization):
    if normalization in (None, "none"):
        return text
    if normalization not in ("NFC", "NFD", "NFKC", "NFKD"):
        raise ValueError("unknown Unicode normalization")
    return unicodedata.normalize(normalization, text)


class LogitAdapter:
    """Shared observation logic; subclasses provide ``encode`` and ``_logits``."""

    def __init__(self, *, max_context, pad_id, normalization="none", temperature=1., pass_attention_mask=True,
                 position_correction=True, use_cache=True, batch_size=8, truncate_to=None, declared_contract=None):
        if not isinstance(max_context, int) or max_context < 1:
            raise ValueError("max_context must be a positive integer")
        if not temperature > 0:
            raise ValueError("temperature must be positive")
        self.max_context, self.pad_id, self.normalization = max_context, pad_id, normalization
        self.temperature, self.pass_attention_mask = float(temperature), pass_attention_mask
        self.position_correction, self.use_cache, self.batch_size = position_correction, use_cache, batch_size
        self.truncate_to = max_context if truncate_to is None else truncate_to
        if not isinstance(self.truncate_to, int) or not 1 <= self.truncate_to <= max_context:
            raise ValueError("truncate_to must be between one and max_context")
        self._declared = declared_contract

    # Subclass interface -------------------------------------------------
    def encode(self, text):
        raise NotImplementedError

    def _logits(self, ids, attention_mask, position_ids, past=None):
        """Return (logits[B,T,V], new_past or None)."""
        raise NotImplementedError

    def _identity(self):
        return {}

    # Shared behavior ----------------------------------------------------
    def contract(self):
        if self._declared is not None:
            return dict(self._declared)
        return {"adapter": type(self).__name__, "max_context": self.max_context, "pad_id": self.pad_id,
                "padding_side": "left", "truncate_to": self.truncate_to, "truncation": "keep last tokens", "normalization": self.normalization,
                "temperature": self.temperature, "attention_mask": self.pass_attention_mask,
                "position_ids": "offset by left padding" if self.position_correction else "absolute",
                "use_cache": self.use_cache, "decoding": "greedy, no logits processors", **self._identity()}

    def _prepare(self, probe):
        tokens = self.encode(_normalize(probe["text"], self.normalization))[-self.truncate_to:]
        if not tokens:
            raise ValueError("probe encodes to no tokens")
        width = max(len(tokens), int(probe.get("pad_to", len(tokens))))
        if width > self.max_context:
            raise ValueError("pad_to exceeds max_context")
        return tokens, width - len(tokens)

    def _positions(self, torch, pads, width):
        base = torch.arange(width)[None, :].repeat(len(pads), 1)
        if self.position_correction:
            base = (base - pads[:, None]).clamp(min=0)
        return base

    def observe(self, probes):
        import torch

        prepared = [self._prepare(probe) for probe in probes]
        groups = {}
        for index, (tokens, pad) in enumerate(prepared):
            key = (len(tokens) + pad, int(probes[index].get("continuation_tokens", 0)))
            groups.setdefault(key, []).append(index)
        observations = [None] * len(probes)
        with torch.inference_mode():
            for (width, steps), members in sorted(groups.items()):
                for start in range(0, len(members), self.batch_size):
                    chunk = members[start:start + self.batch_size]
                    for index, observation in zip(chunk, self._observe_group(torch, [prepared[i] for i in chunk], width, steps)):
                        observations[index] = observation
        return observations

    def _observe_group(self, torch, items, width, steps):
        ids = torch.tensor([[self.pad_id] * pad + tokens for tokens, pad in items], dtype=torch.long)
        pads = torch.tensor([pad for _, pad in items], dtype=torch.long)
        mask = (torch.arange(width)[None, :] >= pads[:, None]).long()
        positions = self._positions(torch, pads, width)
        logits, past = self._logits(ids, mask if self.pass_attention_mask else None, positions,
                                    past=None if steps == 0 or not self.use_cache else "start")
        logp = (logits.double() / self.temperature).log_softmax(-1)
        top2 = logp.topk(2, dim=-1)
        entropy = -(logp.exp() * logp).sum(-1)
        observations = []
        for row, (_, pad) in enumerate(items):
            observations.append({"argmax": logp[row, pad:].argmax(-1).tolist(),
                                 "top_logprob": top2.values[row, pad:, 0].tolist(),
                                 "top_gap": (top2.values[row, pad:, 0] - top2.values[row, pad:, 1]).tolist(),
                                 "entropy": entropy[row, pad:].tolist()})
        if steps:
            tokens, values = self._continue(torch, ids, mask, positions, logp[:, -1], past, steps)
            for row, observation in enumerate(observations):
                observation["continuation"] = tokens[row]
                observation["continuation_logprob"] = values[row]
        return observations

    def _continue(self, torch, ids, mask, positions, last, past, steps):
        tokens, values = [[] for _ in range(len(ids))], [[] for _ in range(len(ids))]
        for step in range(steps):
            choice = last.argmax(-1)
            for row in range(len(ids)):
                tokens[row].append(int(choice[row]))
                values[row].append(float(last[row, choice[row]]))
            if step == steps - 1:
                break
            mask = torch.cat((mask, torch.ones((len(ids), 1), dtype=mask.dtype)), 1)
            next_position = positions[:, -1:] + 1
            positions = torch.cat((positions, next_position), 1)
            if self.use_cache and past is not None:
                logits, past = self._logits(choice[:, None], mask if self.pass_attention_mask else None,
                                            self._cache_positions(next_position, step), past=past)
            else:
                ids = torch.cat((ids, choice[:, None]), 1)
                if ids.shape[1] > self.max_context:
                    raise ValueError("continuation would exceed max_context")
                logits, _ = self._logits(ids, mask if self.pass_attention_mask else None, positions)
            last = (logits[:, -1].double() / self.temperature).log_softmax(-1)
        return tokens, values

    def _cache_positions(self, next_position, step):
        return next_position


class TorchCallableAdapter(LogitAdapter):
    """Adapter for any resident PyTorch callable.

    ``forward(input_ids, attention_mask, position_ids)`` must return logits
    ``[batch, length, vocabulary]``; ``attention_mask`` may be None. Caches are
    not used. ``identity`` is a JSON-serializable dict added to the contract
    (for example tokenizer and weight digests).
    """

    def __init__(self, forward, encode, *, identity=None, **settings):
        settings.setdefault("use_cache", False)
        super().__init__(**settings)
        self._forward, self._encode, self._identity_value = forward, encode, dict(identity or {})

    def encode(self, text):
        return list(self._encode(text))

    def _identity(self):
        return dict(self._identity_value)

    def _logits(self, ids, attention_mask, position_ids, past=None):
        return self._forward(ids, attention_mask, position_ids), None


class ByteTransformerAdapter(LogitAdapter):
    """The training lab's ``CausalTransformer`` byte models (UTF-8 bytes).

    Attention blocks later keys and, with an attention mask, left-padding
    keys; every query may attend to itself so padded rows stay finite.
    ``encoding`` and ``newline`` declare text-to-byte conversion.
    """

    def __init__(self, model, *, encoding_errors="strict", newline="\n", **settings):
        settings.setdefault("max_context", model.seq_len)
        settings.setdefault("pad_id", 0)
        settings.setdefault("use_cache", False)
        super().__init__(**settings)
        if self.max_context > model.seq_len:
            raise ValueError("max_context exceeds the model's positional table")
        self.model, self.encoding_errors, self.newline = model.eval(), encoding_errors, newline
        self.heads = model.body.layers[0].self_attn.num_heads

    def encode(self, text):
        if self.newline != "\n":
            text = text.replace("\n", self.newline)
        if self.encoding_errors == "strict":
            return list(text.encode("utf-8"))
        return list(text.encode("ascii", errors=self.encoding_errors))

    def _identity(self):
        from ..training.runner import model_sha256
        return {"model_tensor_sha256": model_sha256(self.model), "vocabulary": "UTF-8 bytes 0..255",
                "text_encoding": "utf-8" if self.encoding_errors == "strict" else f"ascii/{self.encoding_errors}",
                "newline": self.newline.encode().hex()}

    def _logits(self, ids, attention_mask, position_ids, past=None):
        import torch

        model, (batch, width) = self.model, ids.shape
        h = model.token(ids) + model.position(position_ids)
        blocked = torch.ones((width, width), dtype=torch.bool).triu(1)[None].repeat(batch, 1, 1)
        if attention_mask is not None:
            blocked |= (attention_mask == 0)[:, None, :]
            blocked &= ~torch.eye(width, dtype=torch.bool)[None]
        h = model.norm(model.body(h, mask=blocked.repeat_interleave(self.heads, 0)))
        return model.head(h), None


def tokenizer_fingerprint(tokenizer):
    vocabulary = sorted(tokenizer.get_vocab().items())
    return {"tokenizer_class": type(tokenizer).__name__,
            "tokenizer_vocabulary_sha256": hashlib.sha256(json.dumps(vocabulary).encode()).hexdigest(),
            "tokenizer_vocabulary_size": len(vocabulary),
            "tokenizer_special_tokens": {k: str(v) for k, v in sorted(tokenizer.special_tokens_map.items())},
            "tokenizer_name_or_path": str(getattr(tokenizer, "name_or_path", ""))}


class HuggingFaceCausalAdapter(LogitAdapter):
    """Hugging Face ``AutoModelForCausalLM``-style models with a tokenizer.

    Tokenization uses ``add_special_tokens=False`` so probes declare every
    token. The pad id defaults to the tokenizer's pad, then eos, token. The
    contract records tokenizer identity, model class and configuration digest,
    dtype, padding, positions, cache use and decoding.
    """

    def __init__(self, model, tokenizer, **settings):
        pad = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else tokenizer.eos_token_id
        if pad is None:
            raise ValueError("tokenizer needs a pad or eos token for left padding")
        settings.setdefault("pad_id", int(pad))
        settings.setdefault("max_context", int(getattr(model.config, "n_positions",
                                                       getattr(model.config, "max_position_embeddings", 1024))))
        super().__init__(**settings)
        self.model, self.tokenizer = model.eval(), tokenizer

    def encode(self, text):
        return list(self.tokenizer(text, add_special_tokens=False)["input_ids"])

    def _identity(self):
        config = self.model.config.to_dict()
        config.pop("_name_or_path", None)
        config.pop("transformers_version", None)
        return {**tokenizer_fingerprint(self.tokenizer), "model_class": type(self.model).__name__,
                "model_config_sha256": hashlib.sha256(json.dumps(config, sort_keys=True, default=str).encode()).hexdigest(),
                "dtype": str(next(self.model.parameters()).dtype)}

    def _logits(self, ids, attention_mask, position_ids, past=None):
        arguments = {"input_ids": ids, "position_ids": position_ids, "use_cache": past is not None}
        if attention_mask is not None:
            arguments["attention_mask"] = attention_mask
        if past is not None and past != "start":
            arguments["past_key_values"] = past
        output = self.model(**arguments)
        return output.logits, (output.past_key_values if past is not None else None)
