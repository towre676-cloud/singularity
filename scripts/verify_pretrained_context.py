#!/usr/bin/env python3
"""Independently replay the post-hoc full-prefix GPT-2 sensitivity check."""
import gzip
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "applications/training_lab/results"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def trace(directory, path, expected):
    compressed = directory / path
    readable = compressed.parent.parent / "traces" / compressed.name.removesuffix(".gz")
    if readable.exists():
        value = json.loads(readable.read_text())
        raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        # Frozen gzip uses an empty filename, mtime zero and level nine.
        import io
        output = io.BytesIO()
        with gzip.GzipFile(filename="", fileobj=output, mode="wb", mtime=0) as handle:
            handle.write(raw)
        if hashlib.sha256(output.getvalue()).hexdigest() != expected:
            raise ValueError("readable trace differs from frozen compressed receipt")
        return value
    if sha(compressed) != expected:
        raise ValueError("compressed trace differs from receipt")
    return json.loads(gzip.decompress(compressed.read_bytes()))


def replay():
    source = BASE / "pretrained_prediction"
    destination = BASE / "pretrained_context512"
    original = json.loads((source / "models/gpt2/results.json").read_text())
    result_path = destination / "models/gpt2/results.json"
    result = json.loads(result_path.read_text())
    protocol = json.loads((destination / "protocol.json").read_text())
    original_protocol = json.loads((source / "protocol.json").read_text())
    assert protocol["context_length"] == 512 and protocol["max_targets_per_document"] == 512
    assert protocol["models"]["gpt2"]["encoded_documents"] == original_protocol["models"]["gpt2"]["encoded_documents"]
    assert protocol["models"]["gpt2"]["files_manifest_sha256"] == original_protocol["models"]["gpt2"]["files_manifest_sha256"]
    assert result["model_files_manifest_sha256"] == original["model_files_manifest_sha256"]
    assert result["protocol_receipt_sha256"] == sha(destination / "protocol.json")
    checks = []
    for relative, expected in result["trace_files_sha256"].items():
        current = trace(destination, relative, expected)
        previous = trace(source, relative, original["trace_files_sha256"][relative])
        assert current["losses_hex"]["adaptive_count"] == previous["losses_hex"]["adaptive_count"]
        neural = [float.fromhex(v) for v in current["losses_hex"]["neural"]]
        counts = [float.fromhex(v) for v in current["losses_hex"]["adaptive_count"]]
        fixed = []
        for k in range(21):
            alpha = k / 20
            fixed.append(-math.fsum(math.log((1-alpha)*math.exp(-n)+alpha*math.exp(-c))
                                    for n, c in zip(neural, counts)))
        best = min(fixed)
        joint = best - math.log(math.fsum(math.exp(best-loss) for loss in fixed)/21)
        observed = math.fsum(float.fromhex(v) for v in current["losses_hex"]["online_blend"])
        assert abs(observed-joint) <= 1e-8
        assert joint <= best+math.log(21)+1e-8
        old_neural = [float.fromhex(v) for v in previous["losses_hex"]["neural"]]
        checks.append({"document": current["document"], "targets": len(neural),
                       "closed_form_mixture_identity_error_nats": observed-joint,
                       "count_trace_identical_to_primary": True,
                       "first_256_neural_loss_max_abs_difference": max(abs(a-b) for a, b in zip(neural[:256], old_neural[:256]))})
    arms = result["domains"]["all_domains"]["arms"]
    return {"analysis_status": "POSTHOC context sensitivity; same documents, not independent confirmation",
            "verified": True, "documents": len(checks), "targets": sum(r["targets"] for r in checks),
            "context_tokens": 512, "neural_has_entire_available_prefix": True,
            "neural_nll": arms["neural"]["nll_nats_per_token"],
            "online_nll": arms["online_blend"]["nll_nats_per_token"],
            "loss_reduction_percent": 100*(1-arms["online_blend"]["nll_nats_per_token"]/arms["neural"]["nll_nats_per_token"]),
            "documents_improved": result["domains"]["all_domains"]["paired"]["online_blend_minus_neural"]["documents_first_better"],
            "result_sha256": sha(result_path), "checks": checks}


if __name__ == "__main__":
    record = replay()
    destination = BASE / "pretrained_context512/independent_replay.json"
    destination.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in record.items() if k != "checks"}))
