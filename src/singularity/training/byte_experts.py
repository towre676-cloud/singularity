"""Portable TRAIN-only byte counts and frozen probability mixtures.

The count expert is an ordinary smoothed n-gram, not a new optimizer. Its
history resets at each causal input window, exactly as the training lab does.
PyTorch is imported only by the tensor/inference helpers, so a saved count
expert can also be fitted, inspected and scored with the standard library.
"""
from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path


VOCABULARY_SIZE = 256
FORMAT = "singularity.byte-count-expert/1"


def sha256_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def _positive_integer(value, name):
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError(name + " must be a positive integer")


def byte_events(raw, sequence_length=64):
    """Yield history and next-byte target, once per noninitial corpus byte.

    History contains at most the two most recent *input* bytes and never
    crosses an input-window boundary. In particular, a trigram backs off to a
    bigram for the first target of each window, including the first window.
    """
    _positive_integer(sequence_length, "sequence_length")
    if not isinstance(raw, bytes) or len(raw) < 2:
        raise ValueError("raw must contain at least two bytes")
    for index in range(len(raw) - 1):
        start = max((index // sequence_length) * sequence_length, index - 1)
        yield raw[start:index + 1], raw[index + 1]


@dataclass
class CountByteExpert:
    """A fitted, add-alpha order-1/2/3 expert with auditable TRAIN identity.

    Evaluation reads the tables without updating them. An unseen context has
    the uniform distribution, rather than silently backing off by frequency.
    Only insufficient history at a window boundary triggers shorter history.
    """
    tables: dict
    order: int
    alpha: float
    sequence_length: int
    train_sha256: str
    train_bytes: int

    def __post_init__(self):
        if not isinstance(self.order, int) or isinstance(self.order, bool) or self.order not in (1, 2, 3):
            raise ValueError("order must be 1, 2 or 3")
        if isinstance(self.alpha, bool) or not math.isfinite(self.alpha) or self.alpha <= 0:
            raise ValueError("alpha must be positive and finite")
        self.alpha = float(self.alpha)
        _positive_integer(self.sequence_length, "sequence_length")
        if not isinstance(self.train_bytes, int) or isinstance(self.train_bytes, bool) or self.train_bytes < 2:
            raise ValueError("train_bytes must be at least two")
        if not isinstance(self.train_sha256, str) or len(self.train_sha256) != 64:
            raise ValueError("train_sha256 must contain 64 lowercase hex digits")
        try:
            if self.train_sha256 != bytes.fromhex(self.train_sha256).hex():
                raise ValueError("noncanonical TRAIN hash")
        except ValueError as exc:
            raise ValueError("train_sha256 must contain 64 lowercase hex digits") from exc
        if set(self.tables) != {0, 1, 2}:
            raise ValueError("counts require history tables 0, 1 and 2")
        for length, table in self.tables.items():
            if not isinstance(table, dict):
                raise ValueError("each count table must be a dictionary")
            for context, row in table.items():
                if not isinstance(context, bytes) or len(context) != length or not isinstance(row, dict) or not row:
                    raise ValueError("invalid count-table context or row")
                for target, count in row.items():
                    if not isinstance(target, int) or isinstance(target, bool) or not 0 <= target < 256:
                        raise ValueError("count-table target must be a byte")
                    _positive_integer(count, "transition count")
        # Every event contributes once to these two tables. Higher-order rows
        # intentionally omit targets whose current window lacks two inputs.
        if set(self.tables[0]) != {b""}:
            raise ValueError("missing unigram count row")
        expected = self.train_bytes - 1
        for length in (0, 1):
            if sum(sum(row.values()) for row in self.tables[length].values()) != expected:
                raise ValueError("count totals disagree with TRAIN length")
        expected_two = expected - (expected + self.sequence_length - 1) // self.sequence_length
        if sum(sum(row.values()) for row in self.tables[2].values()) != expected_two:
            raise ValueError("trigram counts disagree with causal window boundaries")

    @classmethod
    def fit(cls, raw, order=3, alpha=.01, sequence_length=64):
        """Fit only the supplied TRAIN bytes; no other split is accessed."""
        tables = {length: defaultdict(Counter) for length in range(3)}
        for history, target in byte_events(raw, sequence_length):
            tables[0][b""][target] += 1
            tables[1][history[-1:]][target] += 1
            if len(history) == 2:
                tables[2][history][target] += 1
        plain = {length: {context: dict(row) for context, row in table.items()}
                 for length, table in tables.items()}
        return cls(plain, order, alpha, sequence_length, sha256_bytes(raw), len(raw))

    def probabilities(self, history):
        """Return a normalized 256-byte distribution for available history."""
        if not isinstance(history, bytes):
            raise ValueError("history must be bytes")
        length = min(self.order - 1, len(history))
        context = history[-length:] if length else b""
        row = self.tables[length].get(context, {})
        denominator = sum(row.values()) + 256 * self.alpha
        return tuple((row.get(byte, 0) + self.alpha) / denominator for byte in range(256))

    def to_dict(self):
        return {"schema": FORMAT, "order": self.order, "alpha": self.alpha,
                "sequence_length": self.sequence_length, "train_sha256": self.train_sha256,
                "train_bytes": self.train_bytes, "fit_split": "TRAIN only",
                "context_convention": "target raw[i+1]; input starts at floor(i/sequence_length)*sequence_length",
                "smoothing": "(count+alpha)/(context_total+256*alpha); unseen context uniform",
                "tables": {str(length): [{"context_hex": context.hex(),
                                            "counts": [[byte, count] for byte, count in sorted(row.items())]}
                                           for context, row in sorted(table.items())]
                           for length, table in sorted(self.tables.items())}}

    @classmethod
    def from_dict(cls, payload):
        if payload.get("schema") != FORMAT or payload.get("fit_split") != "TRAIN only":
            raise ValueError("unsupported count-expert schema or fit split")
        if set(payload.get("tables", {})) != {"0", "1", "2"}:
            raise ValueError("counts require history tables 0, 1 and 2")
        tables = {}
        for length, entries in payload["tables"].items():
            table = {}
            for entry in entries:
                context = bytes.fromhex(entry["context_hex"])
                pairs = entry["counts"]
                row = dict(pairs)
                if context in table or len(row) != len(pairs):
                    raise ValueError("duplicate context or transition in serialized counts")
                table[context] = row
            tables[int(length)] = table
        return cls(tables, payload["order"], payload["alpha"], payload["sequence_length"],
                   payload["train_sha256"], payload["train_bytes"])

    def save(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")
        return sha256_bytes(path.read_bytes())

    @classmethod
    def load(cls, path):
        """Load portable JSON counts; no executable checkpoint is deserialized."""
        return cls.from_dict(json.loads(Path(path).read_text()))


def count_log_probs(expert, input_ids):
    """Return [window, position, 256] log-probabilities using past inputs only."""
    import torch

    if input_ids.ndim != 2 or not 1 <= input_ids.shape[1] <= expert.sequence_length:
        raise ValueError("input_ids must contain causal windows within the expert context length")
    if input_ids.dtype not in (torch.int8, torch.int16, torch.int32, torch.int64, torch.uint8):
        raise ValueError("input_ids must contain integer raw bytes")
    rows = input_ids.detach().cpu().tolist()
    if any(not 0 <= token < 256 for row in rows for token in row):
        raise ValueError("input token outside byte vocabulary")
    cache, result = {}, []
    for row in rows:
        current = []
        for position in range(len(row)):
            history = bytes(row[max(0, position - 1):position + 1])
            length = min(expert.order - 1, len(history))
            key = history[-length:] if length else b""
            if key not in cache:
                cache[key] = torch.tensor(expert.probabilities(history), dtype=torch.float64).log()
            current.append(cache[key])
        result.append(torch.stack(current))
    if not result:
        return torch.empty((*input_ids.shape, 256), dtype=torch.float64, device=input_ids.device)
    return torch.stack(result).to(input_ids.device)


def mixture_log_probs(neural_log_probs, count_log_probabilities, neural_weight):
    """Stable ordinary convex probability blend with a frozen supplied weight.

    Inputs are normalized log-probabilities with matching shapes. The weight
    multiplies the neural distribution; one minus the weight multiplies counts.
    Endpoint weights retain their expert exactly, including zero probabilities.
    """
    import torch

    if isinstance(neural_weight, bool) or not math.isfinite(neural_weight) or not 0 <= neural_weight <= 1:
        raise ValueError("neural_weight must be finite and between zero and one")
    if neural_log_probs.shape != count_log_probabilities.shape or neural_log_probs.ndim < 1:
        raise ValueError("expert distributions must have matching shapes")
    left, right = neural_log_probs.double(), count_log_probabilities.double()
    if left.device != right.device:
        raise ValueError("expert distributions must use the same device")
    for value in (left, right):
        if torch.isnan(value).any() or torch.isposinf(value).any():
            raise ValueError("expert log-probabilities must be finite or negative infinity")
        normalization = torch.logsumexp(value, dim=-1)
        if not torch.allclose(normalization, torch.zeros_like(normalization), atol=1e-5, rtol=0):
            raise ValueError("expert log-probabilities must be normalized")
    if neural_weight == 0:
        return right
    if neural_weight == 1:
        return left
    return torch.logaddexp(left + math.log(neural_weight), right + math.log1p(-neural_weight))


def score_frozen_mixture(model, expert, raw, neural_weight, batch_size=64,
                         return_target_losses=False):
    """Score every noninitial byte once; fit neither expert nor blend weight.

    All summaries share the same shifted targets. Padded tail positions are
    ignored; count history resets at the same boundaries as neural attention.
    Optional per-target losses/correctness support paired external audits.
    This helper never selects a weight or decides which corpus is TEST.
    """
    import torch
    from .data import _byte_windows

    _positive_integer(batch_size, "batch_size")
    # Validate weight even if a caller supplies a pathological empty model.
    if isinstance(neural_weight, bool) or not math.isfinite(neural_weight) or not 0 <= neural_weight <= 1:
        raise ValueError("neural_weight must be finite and between zero and one")
    rows = _byte_windows(raw, expert.sequence_length)
    device = next(model.parameters(), torch.empty(0)).device
    previous_mode = model.training
    records = {name: {"losses": [], "correct": []} for name in ("neural", "count", "mixture")}
    model.eval()
    try:
        with torch.no_grad():
            for start in range(0, len(rows["labels"]), batch_size):
                x = rows["input_ids"][start:start + batch_size].to(device)
                labels = rows["labels"][start:start + batch_size].to(device)
                logits = model(x)
                if logits.shape != (*x.shape, 256):
                    raise ValueError("model must emit unshifted [window, position, 256] byte logits")
                neural = logits.double().log_softmax(-1)
                counts = count_log_probs(expert, x)
                mixture = mixture_log_probs(neural, counts, neural_weight)
                valid = labels != -100
                targets = labels[valid]
                for name, distribution in (("neural", neural), ("count", counts), ("mixture", mixture)):
                    selected = distribution[valid]
                    losses = -selected.gather(-1, targets[:, None]).squeeze(-1)
                    records[name]["losses"].extend(losses.cpu().tolist())
                    records[name]["correct"].extend((selected.argmax(-1) == targets).cpu().tolist())
    finally:
        model.train(previous_mode)
    summaries = {}
    for name, record in records.items():
        count = len(record["losses"])
        nll = math.fsum(record["losses"]) / count
        summaries[name] = {"nll_nats_per_byte": nll, "bits_per_byte": nll / math.log(2),
                           "accuracy": sum(record["correct"]) / count,
                           "correct": sum(record["correct"]), "valid_targets": count}
        if return_target_losses:
            summaries[name]["target_nll_nats"] = record["losses"]
            summaries[name]["target_correct"] = record["correct"]
    return {"neural_weight": float(neural_weight), "count_weight": 1 - float(neural_weight),
            "sequence_length": expert.sequence_length, "corpus_sha256": sha256_bytes(raw),
            "corpus_bytes": len(raw), "experts": summaries,
            "weight_fitting": "none; caller supplied a frozen weight",
            "window_convention": "one target shift; every noninitial byte once; padding ignored"}
