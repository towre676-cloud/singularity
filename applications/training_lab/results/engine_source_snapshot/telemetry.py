"""Descriptive update sketches, with explicit centering and missingness."""
import math
import torch


def spectrum_summary(matrix):
    """PSD feature concentration, natural entropy and Renyi/Shannon gap.

    Delta = -log(rho)-H is nonpositive for a single normalized PSD spectrum.
    Missing zero trace is not converted into a fictitious uniform spectrum.
    """
    eig = torch.linalg.eigvalsh(matrix.double()).clamp_min(0)
    trace = float(eig.sum())
    if not math.isfinite(trace) or trace <= 1e-30:
        return {"available": False, "reason": "zero or nonfinite trace", "trace": trace,
                "rho": None, "entropy": None, "delta": None, "effective_rank": None}
    p = eig / trace
    positive = p[p > 0]
    rho = float(p.max())
    entropy = float(-(positive * positive.log()).sum())
    delta = -math.log(rho) - entropy
    return {"available": True, "trace": trace, "rho": rho, "entropy": entropy,
            "delta": delta, "effective_rank": math.exp(entropy),
            "entropy_normalized": entropy / math.log(len(p)) if len(p) > 1 else 0.0,
            "delta_sanity_nonpositive": delta <= 1e-10,
            "eigenvalues": [float(x) for x in eig]}


class UpdateSketch:
    def __init__(self, parameter_count, dimension=16, window=32, seed=0):
        if parameter_count < 1 or dimension < 1 or window < 2:
            raise ValueError("positive parameter count/dimension and window at least two required")
        gen = torch.Generator().manual_seed(seed)
        self.indices = torch.randint(dimension, (parameter_count,), generator=gen)
        self.signs = (torch.randint(2, (parameter_count,), generator=gen)*2-1).double()
        self.dimension, self.window = dimension, window
        self.vectors = []
        self.count = 0

    def update(self, flat_update):
        flat_update = flat_update.detach().cpu().reshape(-1).double()
        if len(flat_update) != len(self.indices):
            raise ValueError("parameter dimension changed")
        if not torch.isfinite(flat_update).all():
            raise ValueError("nonfinite update cannot form covariance telemetry")
        sketch = torch.zeros(self.dimension, dtype=torch.double)
        sketch.index_add_(0, self.indices, flat_update * self.signs)
        self.vectors.append(sketch)
        self.vectors = self.vectors[-self.window:]
        self.count += 1

    def summary(self):
        if not self.vectors:
            return {"available": False, "reason": "no updates", "updates_seen": 0,
                    "feature": "CountSketch of actual parameter updates"}
        z = torch.stack(self.vectors)
        mean = z.mean(0)
        second = z.T @ z / len(z)
        centered = second - mean[:, None]*mean[None, :]
        result = {"feature": "CountSketch of actual parameter updates",
                  "projection": "fixed seeded signed coordinate hashing, unnormalized",
                  "dimension": self.dimension, "window_updates": len(z), "updates_seen": self.count,
                  "centered": spectrum_summary(centered), "uncentered": spectrum_summary(second),
                  "interpretation": "feature covariance telemetry; no stability or Hessian certificate"}
        result["available"] = result["centered"]["available"]
        return result


def ffn_rank(model):
    out = []
    for name, p in model.named_parameters():
        if p.ndim == 2 and ("linear1.weight" in name or name == "net.0.weight"):
            squared = torch.linalg.svdvals(p.detach().double()).square()
            weights = squared / squared.sum().clamp_min(1e-300)
            positive = weights[weights > 0]
            out.append({"name": name, "shape": list(p.shape),
                        "numerical_rank": int((squared > squared.max()*1e-12).sum()),
                        "squared_singular_entropy_rank": math.exp(float(-(positive*positive.log()).sum()))})
    return out
