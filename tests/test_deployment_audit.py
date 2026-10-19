"""Deployment-specific causal faults and matched-comparator invariants."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("confirm_deployment_audit", ROOT / "scripts/confirm_deployment_audit.py")
DEPLOY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DEPLOY)


class DeploymentComparatorTests(unittest.TestCase):
    def test_optimal_pruning_beats_arbitrary_deletion_and_random_meets_same_coverage(self):
        probes = [{"id": f"p{i}", "cost": cost} for i, cost in enumerate([4, 1, 1, 3])]
        separates = {"a": [True, True, False, True], "b": [True, False, True, True], "absent": [False]*4}
        result = DEPLOY.comparators(probes, separates)
        self.assertEqual(result["exact"]["cost"], 5)
        self.assertEqual(result["pruned_greedy"]["cost"], 5)
        self.assertEqual(result["unavailable_faults"], {"absent": 0})
        self.assertEqual(len(result["random_panels"]), 64)
        for row in result["random_panels"]:
            self.assertEqual(row["cost"], sum(probes[e]["cost"] for e in row["indices"]))
            self.assertLessEqual(row["cost"], row["unpruned_cost"])
            self.assertTrue(all(sum(separates[f][e] for e in row["indices"]) >= 2 for f in ("a", "b")))

    def test_shards_bind_exact_list_coordinates_and_stay_under_publication_budget(self):
        probes = [{"id": f"p{i}"} for i in range(18)]
        rows = [{"argmax": [e]*96, "entropy": [0.125]*96} for e in range(18)]
        original = {"reference": rows, "calibration": [rows, rows], "heldout": {"case": rows}, "tolerances": [{"entropy": 1e-5}]*18}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            DEPLOY.shard_observations(path, original, probes)
            manifest = json.loads((path / "observations_manifest.json").read_text())
            self.assertEqual(DEPLOY.digest(manifest["entries"]), manifest["entries_sha256"])
            collections = {}
            for entry in manifest["entries"]:
                content = path / entry["file"]
                self.assertEqual(DEPLOY.file_digest(content), entry["sha256"])
                self.assertLessEqual(content.stat().st_size, 65536)
                shard = json.loads(content.read_text())
                recovered = collections.setdefault(tuple(entry["collection"]), [None]*18)
                for index, row in zip(entry["probe_indices"], shard["rows"]):
                    recovered[index] = row
            self.assertEqual(collections[("reference",)], rows)
            self.assertEqual(collections[("calibration", 1)], rows)
            self.assertEqual(collections[("heldout", "case")], rows)

    def test_clean_quantized_batch_and_cache_scope_is_declared_before_results(self):
        self.assertTrue(all(c.get("batch_size", 1) == 1 for c in DEPLOY.PROTOCOL["calibration"]["dynamic_int8"]))
        self.assertFalse(any("cache_split" in c.get("change", {}) for c in DEPLOY.PROTOCOL["calibration"]["dynamic_int8"]))
        self.assertIn("service_cache_prefix_dropped_half", DEPLOY.CONSTRUCTION)
        self.assertIn("service_cache_prefix_dropped_third", DEPLOY.HELDOUT)
        self.assertIn("torchscript_batch3_threads2_reverse", DEPLOY.PROTOCOL["clean_heldout"])


try:
    import torch
except ImportError:
    torch = None


@unittest.skipUnless(torch is not None, "PyTorch optional")
class DeploymentServiceTests(unittest.TestCase):
    class Tokenizer:
        def __call__(self, text, **kwargs):
            return {"input_ids": list(text.encode())}

    def test_text_changes_are_executed_in_service_and_leave_original_text_untouched(self):
        text = "caf\u00e9\n\ufb01nal"*20
        service = DEPLOY.DeploymentService(None, self.Tokenizer(), {"normalization": "NFKC", "newline": "\r\n", "truncate": 48})
        self.assertEqual(len(service.encode(text)), 48)
        self.assertEqual(text, "caf\u00e9\n\ufb01nal"*20)
        self.assertNotEqual(service.encode(text), DEPLOY.DeploymentService(None, self.Tokenizer()).encode(text))

    def test_quantized_packed_state_digest_survives_weights_only_serialization(self):
        if "fbgemm" not in torch.backends.quantized.supported_engines:
            self.skipTest("fbgemm unavailable")
        torch.backends.quantized.engine = "fbgemm"
        base = torch.nn.Sequential(torch.nn.Linear(3, 4), torch.nn.ReLU(), torch.nn.Linear(4, 2)).eval()
        model = torch.ao.quantization.quantize_dynamic(base, {torch.nn.Linear}, dtype=torch.qint8)
        before = DEPLOY.tensor_state_digest(model)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.pt"
            torch.save(model.state_dict(), path)
            reconstructed = torch.ao.quantization.quantize_dynamic(base, {torch.nn.Linear}, dtype=torch.qint8)
            reconstructed.load_state_dict(torch.load(path, weights_only=True))
            self.assertEqual(DEPLOY.tensor_state_digest(reconstructed), before)
        with torch.no_grad():
            reconstructed[0]._packed_params.set_weight_bias(reconstructed[0].weight(), reconstructed[0].bias()+1)
        self.assertNotEqual(DEPLOY.tensor_state_digest(reconstructed), before)

    def test_service_cache_and_external_graph_are_real_separate_execution_paths(self):
        from types import SimpleNamespace
        calls = []
        class Model:
            def __call__(self, input_ids, attention_mask, position_ids, use_cache, return_dict, past_key_values=None):
                prefix = 0 if past_key_values is None else past_key_values.get_seq_length()
                calls.append({"width": input_ids.shape[1], "prefix": prefix, "cache": use_cache})
                length = prefix+input_ids.shape[1]
                return SimpleNamespace(logits=(input_ids.float()+prefix)[..., None].repeat(1, 1, 3),
                                       past_key_values=SimpleNamespace(get_seq_length=lambda: length))
        ids = torch.tensor([[1, 2, 3, 4, 5, 6]])
        mask = torch.ones_like(ids)
        positions = torch.arange(6)[None]
        service = DEPLOY.DeploymentService(Model(), self.Tokenizer(), {"cache_split": .5})
        logits = service.forward(ids, mask, positions)
        self.assertEqual(logits.shape, (1, 6, 3))
        self.assertEqual(calls[1]["prefix"], 3)
        self.assertTrue(service.cache_receipts[0]["cache_passed_to_suffix"])
        calls.clear()
        broken = DEPLOY.DeploymentService(Model(), self.Tokenizer(), {"cache_split": .5, "drop_cache": True})
        self.assertFalse(torch.equal(logits, broken.forward(ids, mask, positions)))
        self.assertEqual(calls[1]["prefix"], 0)
        graph_calls = []
        def graph(*args):
            graph_calls.append(args)
            return torch.zeros((1, 6, 3))
        graph_service = DEPLOY.DeploymentService(None, self.Tokenizer(), graph=graph)
        graph_service.forward(ids, mask, positions)
        self.assertEqual(len(graph_calls), 1)
        self.assertEqual(graph_service.graph_calls, 1)


if __name__ == "__main__":
    unittest.main()
