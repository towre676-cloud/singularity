"""Small models with explicit causal masks and no internal target shifting."""
import torch
from torch import nn
import torch.nn.functional as F


class ModularMLP(nn.Module):
    def __init__(self, p, hidden=128):
        super().__init__()
        self.p = p
        self.net = nn.Sequential(nn.Linear(2 * p, hidden), nn.GELU(), nn.Linear(hidden, p))

    def forward(self, input_ids):
        x = F.one_hot(input_ids, self.p).float().flatten(1)
        return self.net(x)


class CausalTransformer(nn.Module):
    def __init__(self, vocab_size, seq_len, d_model=64, heads=4, layers=2,
                 classifier=False, num_classes=None):
        super().__init__()
        if d_model % heads:
            raise ValueError("d_model must be divisible by heads")
        self.classifier = classifier
        self.seq_len = seq_len
        self.vocab_size = vocab_size
        self.token = nn.Embedding(vocab_size, d_model)
        self.position = nn.Embedding(seq_len, d_model)
        layer = nn.TransformerEncoderLayer(d_model, heads, dim_feedforward=4*d_model,
                 dropout=0.0, activation="gelu", batch_first=True, norm_first=True)
        self.body = nn.TransformerEncoder(layer, layers, enable_nested_tensor=False)
        self.norm = nn.LayerNorm(d_model)
        self.head = nn.Linear(d_model, num_classes if classifier else vocab_size)

    def forward(self, input_ids):
        if self.classifier:
            eq = torch.full((len(input_ids), 1), self.vocab_size - 1, device=input_ids.device, dtype=torch.long)
            input_ids = torch.cat((input_ids, eq), dim=1)
        n = input_ids.shape[1]
        if n > self.seq_len:
            raise ValueError("input exceeds model context length")
        positions = torch.arange(n, device=input_ids.device)
        h = self.token(input_ids) + self.position(positions)
        # True entries block attention to later positions. Targets are never input
        # to this function except as previous context tokens in a causal window.
        mask = torch.ones((n, n), device=input_ids.device, dtype=torch.bool).triu(1)
        h = self.norm(self.body(h, mask=mask))
        return self.head(h[:, -1] if self.classifier else h)


def build_model(cfg, metadata):
    mc = cfg.get("model", "mlp")
    mc = dict(mc) if isinstance(mc, dict) else {"name": mc}
    name = mc.get("name", "mlp")
    if metadata["task"] == "modular_addition":
        p = metadata["p"]
        if name == "mlp":
            return ModularMLP(p, int(mc.get("hidden", 128)))
        if name in ("transformer", "causal_transformer"):
            return CausalTransformer(p+1, 3, int(mc.get("d_model", 64)), int(mc.get("heads", 4)),
                                     int(mc.get("layers", 1)), True, p)
    elif name in ("transformer", "causal_transformer", "byte_transformer"):
        return CausalTransformer(256, metadata["seq_len"], int(mc.get("d_model", 48)),
                                 int(mc.get("heads", 4)), int(mc.get("layers", 2)))
    raise ValueError("model/task combination not supported")
