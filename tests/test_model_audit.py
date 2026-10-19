"""Audit packages: tolerance, robust selection, model-free verification, adapters."""
import copy
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from singularity.model_audit import (build_package, check_package, deviation, flags, load_package,
                                     package_digest, save_package, tolerances_from_clean, verify_package)

try:
    import torch
except ImportError:
    torch = None
try:
    import transformers
except ImportError:
    transformers = None

ROOT = Path(__file__).resolve().parents[1]


def obs(argmax, top, gap=None, entropy=None):
    return {"argmax": list(argmax), "top_logprob": list(top), "top_gap": list(gap or [1.] * len(argmax)),
            "entropy": list(entropy or [0.] * len(argmax))}


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.probes = [{"id": f"p{i}", "text": f"probe {i}", "cost": c} for i, c in enumerate((4, 1, 1, 3))]
        self.reference = [obs([1, 2], [-.5, -.7]) for _ in range(4)]
        self.clean = [[obs([1, 2], [-.5 + 1e-7, -.7]) for _ in range(4)]]
        shifted = obs([1, 2], [-.6, -.7])
        changed = obs([1, 3], [-.5, -.7])
        # fault a: probes 0,1,3; fault b: probes 0,2,3.
        self.faults = {"a": [shifted, shifted, self.reference[2], changed],
                       "b": [changed, self.reference[1], shifted, shifted]}

    def package(self, **kwargs):
        return build_package(self.probes, self.reference, self.clean, self.faults,
                             contract={"adapter": "test", "temperature": 1.}, **kwargs)

    def test_tie_positions_do_not_count_and_lengths_do(self):
        expected = obs([1, 2], [-.1, -.1], gap=[0., .5])
        report = deviation(obs([9, 2], [-.1, -.1]), expected, tie_margin=1e-4)
        self.assertEqual((report["discrete_mismatches"], report["tie_positions_ignored"]), (0, 1))
        self.assertEqual(deviation(obs([1, 9], [-.1, -.1]), expected, 1e-4)["discrete_mismatches"], 1)
        self.assertTrue(deviation(obs([1], [-.1]), expected)["length_mismatch"])
        with self.assertRaises(ValueError):
            deviation({"argmax": [1], "bogus": [1]}, expected)

    def test_tolerance_rule_and_unstable_reference(self):
        tolerances, maxima = tolerances_from_clean(self.reference, self.clean, 4., 1e-6, 1e-4)
        self.assertAlmostEqual(tolerances[0]["top_logprob"], 4e-7 + 1e-6, places=12)
        self.assertEqual(maxima[0]["entropy"], 0.)
        with self.assertRaises(ValueError):
            tolerances_from_clean(self.reference, [[obs([1, 5], [-.5, -.7])] * 4], 4., 1e-6, 1e-4)
        with self.assertRaises(ValueError):
            tolerances_from_clean(self.reference, self.clean, .5, 1e-6, 1e-4)

    def test_robust_panel_is_minimum_cost_and_survives_one_missing_result(self):
        package = self.package(requirement=2)
        self.assertEqual(sorted(p["id"] for p in package["probes"]), ["p1", "p2", "p3"])
        self.assertEqual(package["selection"]["exact_cost"], 5)
        self.assertEqual(package["coverage"], {"a": 2, "b": 2})
        self.assertTrue(verify_package(package)["verified"])
        single = self.package(requirement=1)
        self.assertEqual(([p["id"] for p in single["probes"]], single["selection"]["exact_cost"]), (["p1", "p2"], 2))

    def test_verification_recomputes_separation_and_detects_tampering(self):
        package = self.package()
        loose = copy.deepcopy(package)
        loose["probes"][0]["tolerance"]["top_logprob"] = 1.
        loose["package_sha256"] = package_digest(loose)
        report = verify_package(loose)
        self.assertFalse(report["verified"])
        self.assertTrue(any("witness" in problem for problem in report["problems"]))
        edited = copy.deepcopy(package)
        edited["requirement"] = 1
        self.assertIn("package digest mismatch", verify_package(edited)["problems"])

    def test_check_detects_change_reports_contract_and_missing_results(self):
        package = self.package()
        index = {p["id"]: i for i, p in enumerate(self.probes)}

        def observer(source):
            return lambda probes: [copy.deepcopy(source[index[p["id"]]]) for p in probes]

        contract = {"adapter": "test", "temperature": 1.}
        self.assertEqual(check_package(package, observer(self.reference), contract)["verdict"], "unchanged")
        report = check_package(package, observer(self.faults["a"]), contract)
        self.assertEqual((report["verdict"], report["flagged_probes"]), ("changed", ["p1", "p3"]))
        partial = check_package(package, observer(self.faults["a"]), contract, missing=["p3"])
        self.assertEqual(partial["flagged_probes"], ["p1"])
        self.assertTrue(all(partial["construction_faults_still_separated"].values()))
        mismatch = check_package(package, observer(self.reference), {"adapter": "test", "temperature": 1.3})
        self.assertEqual(mismatch["verdict"], "changed")
        self.assertEqual(mismatch["contract_mismatches"][0]["key"], "temperature")
        with self.assertRaises(ValueError):
            check_package(package, observer(self.reference), contract, missing=["nope"])

    def test_frozen_panel_reports_coverage_that_did_not_transfer(self):
        package = self.package(panel_ids=["p1", "p3"])
        self.assertEqual(package["deficient_faults"], ["b"])
        self.assertEqual(package["coverage"], {"a": 2, "b": 1})
        report = verify_package(package)
        self.assertFalse(report["verified"])
        self.assertTrue(any("deficient" in problem for problem in report["problems"]))
        with self.assertRaises(ValueError):
            self.package(panel_ids=["p1", "p1"])

    def test_infeasible_requirement_is_an_error_not_a_package(self):
        with self.assertRaises(ValueError):
            self.package(requirement=4)

    def test_cli_snapshot_identity_is_recomputed_from_supplied_weights(self):
        from singularity.model_audit.__main__ import _local_hf_provenance
        with tempfile.TemporaryDirectory() as directory:
            weights = Path(directory) / "model.safetensors"
            weights.write_bytes(b"first weight snapshot")
            (Path(directory) / "config.json").write_text("{}\n")
            declared = {"model_id": "example/model", "revision": "a" * 40,
                        "snapshot_manifest_sha256": "untrusted label"}
            original = _local_hf_provenance(directory, declared)
            self.assertNotEqual(original["snapshot_manifest_sha256"], "untrusted label")
            weights.write_bytes(b"a different weight snapshot")
            changed = _local_hf_provenance(directory, declared)
            self.assertNotEqual(original["snapshot_manifest_sha256"], changed["snapshot_manifest_sha256"])
            self.assertEqual(declared["snapshot_manifest_sha256"], "untrusted label")
            self.assertEqual(changed["revision"], declared["revision"])


@unittest.skipIf(torch is None, "optional PyTorch unavailable")
class ByteAdapterTests(unittest.TestCase):
    def setUp(self):
        from singularity.training.models import CausalTransformer
        from singularity.model_audit.adapters import ByteTransformerAdapter
        torch.manual_seed(5)
        self.model = CausalTransformer(256, 32, d_model=16, heads=2, layers=2).eval()
        self.Adapter = ByteTransformerAdapter
        self.probes = [{"id": "short", "text": "abc def", "pad_to": 24, "cost": 24},
                       {"id": "plain", "text": "hello world", "cost": 11},
                       {"id": "accent", "text": "café ﬁne", "cost": 12},
                       {"id": "long", "text": "x" * 30, "cost": 30}]

    def test_left_padding_with_mask_and_offset_positions_matches_unpadded(self):
        adapter = self.Adapter(self.model)
        padded, plain = adapter.observe([{"text": "abc def", "pad_to": 24}, {"text": "abc def"}])
        self.assertEqual(padded["argmax"], plain["argmax"])
        self.assertLess(max(abs(a - b) for a, b in zip(padded["top_logprob"], plain["top_logprob"])), 1e-6)
        with torch.inference_mode():
            direct = self.model(torch.tensor([list(b"abc def")])).double().log_softmax(-1)
        self.assertEqual(plain["argmax"], direct.argmax(-1)[0].tolist())

    def test_silent_faults_move_only_the_probes_that_can_see_them(self):
        healthy = self.Adapter(self.model)
        contract = healthy.contract()
        reference = healthy.observe(self.probes)
        clean = [self.Adapter(self.model, batch_size=1).observe(self.probes)]
        faults = {
            "no_mask": self.Adapter(self.model, pass_attention_mask=False, declared_contract=contract),
            "nfkc": self.Adapter(self.model, normalization="NFKC", declared_contract=contract),
            "ascii": self.Adapter(self.model, encoding_errors="replace", declared_contract=contract),
            "truncate": self.Adapter(self.model, truncate_to=16, declared_contract=contract),
            "temperature": self.Adapter(self.model, temperature=1.3, declared_contract=contract),
        }
        observed = {name: adapter.observe(self.probes) for name, adapter in faults.items()}
        tolerances, _ = tolerances_from_clean(reference, clean, 4., 1e-6, 1e-4)
        separated = {name: [p["id"] for p, o, r, t in zip(self.probes, rows, reference, tolerances)
                            if flags(deviation(o, r, 1e-4), t)] for name, rows in observed.items()}
        self.assertEqual(separated["no_mask"], ["short"])
        self.assertEqual(separated["nfkc"], ["accent"])
        self.assertEqual(separated["ascii"], ["accent"])
        self.assertEqual(separated["truncate"], ["long"])
        self.assertEqual(separated["temperature"], [p["id"] for p in self.probes])
        same_winners = [o["argmax"] == r["argmax"] for o, r in zip(observed["temperature"], reference)]
        self.assertTrue(all(same_winners))
        self.assertEqual(faults["temperature"].contract(), contract)

    def test_package_round_trip_and_command_line(self):
        from singularity.model_audit.__main__ import main
        healthy = self.Adapter(self.model)
        reference = healthy.observe(self.probes)
        faults = {"temperature": self.Adapter(self.model, temperature=1.3).observe(self.probes)}
        package = build_package(self.probes, reference, [self.Adapter(self.model, batch_size=1).observe(self.probes)],
                                faults, contract=healthy.contract(), requirement=2)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.json"
            save_package(package, path)
            self.assertEqual(load_package(path), package)
            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main(["verify", str(path)]), 0)
            self.assertTrue(json.loads(output.getvalue())["verified"])
        report = check_package(package, healthy.observe, healthy.contract())
        self.assertEqual(report["verdict"], "unchanged")
        other = copy.deepcopy(self.model)
        with torch.no_grad():
            other.head.bias.add_(1e-3 * torch.arange(256))
        changed = self.Adapter(other)
        report = check_package(package, changed.observe, changed.contract())
        self.assertEqual(report["contract_mismatches"][0]["key"], "model_tensor_sha256")


@unittest.skipIf(torch is None or transformers is None, "optional transformers unavailable")
class HuggingFaceAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from tokenizers import Tokenizer, decoders, models, pre_tokenizers, trainers
        from transformers import GPT2Config, GPT2LMHeadModel, PreTrainedTokenizerFast
        from transformers.utils import logging
        logging.set_verbosity_error()
        core = Tokenizer(models.BPE())
        core.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
        core.decoder = decoders.ByteLevel()
        core.train_from_iterator(["the cat sat on the mat. " * 20, "def f(x):\n    return x + 1\n" * 20],
                                 trainers.BpeTrainer(vocab_size=300, special_tokens=["<|endoftext|>"],
                                                     initial_alphabet=pre_tokenizers.ByteLevel.alphabet()))
        cls.tokenizer = PreTrainedTokenizerFast(tokenizer_object=core, eos_token="<|endoftext|>",
                                                pad_token="<|endoftext|>")
        torch.manual_seed(0)
        eos = cls.tokenizer.eos_token_id
        cls.model = GPT2LMHeadModel(GPT2Config(vocab_size=len(cls.tokenizer), n_positions=64, n_embd=32,
                                               n_layer=2, n_head=2, bos_token_id=eos, eos_token_id=eos)).eval()

    def test_cache_padding_and_positions(self):
        from singularity.model_audit.adapters import HuggingFaceCausalAdapter
        probes = [{"text": "the cat sat", "pad_to": 20, "continuation_tokens": 4},
                  {"text": "the cat sat", "continuation_tokens": 4}]
        cached = HuggingFaceCausalAdapter(self.model, self.tokenizer).observe(probes)
        uncached = HuggingFaceCausalAdapter(self.model, self.tokenizer, use_cache=False).observe(probes)
        for a, b in ((cached[0], cached[1]), (cached[0], uncached[0])):
            self.assertEqual(a["continuation"], b["continuation"])
            self.assertLess(max(abs(x - y) for x, y in zip(a["continuation_logprob"], b["continuation_logprob"])), 1e-5)
            self.assertLess(max(abs(x - y) for x, y in zip(a["top_logprob"], b["top_logprob"])), 1e-5)

        class StaleCachePositions(HuggingFaceCausalAdapter):
            def _cache_positions(self, next_position, step):
                return torch.zeros_like(next_position) + step

        stale = StaleCachePositions(self.model, self.tokenizer).observe(probes)
        self.assertGreater(max(abs(x - y) for x, y in zip(stale[0]["continuation_logprob"],
                                                         cached[0]["continuation_logprob"])), 1e-3)
        unmasked = HuggingFaceCausalAdapter(self.model, self.tokenizer, pass_attention_mask=False).observe(probes[:1])
        self.assertGreater(max(abs(x - y) for x, y in zip(unmasked[0]["top_logprob"], cached[0]["top_logprob"])), 1e-3)

    def test_contract_records_tokenizer_and_configuration_identity(self):
        from singularity.model_audit.adapters import HuggingFaceCausalAdapter
        contract = HuggingFaceCausalAdapter(self.model, self.tokenizer).contract()
        self.assertEqual(contract["tokenizer_vocabulary_size"], len(self.tokenizer))
        self.assertEqual(contract["max_context"], 64)
        changed = copy.deepcopy(self.tokenizer)
        changed.add_tokens(["<extra>"])
        self.assertNotEqual(HuggingFaceCausalAdapter(self.model, changed).contract()["tokenizer_vocabulary_sha256"],
                            contract["tokenizer_vocabulary_sha256"])
        relocated = copy.deepcopy(self.tokenizer)
        relocated.name_or_path = "/a/different/local/snapshot"
        self.assertEqual(HuggingFaceCausalAdapter(self.model, relocated).contract(), contract)

    def test_backend_fingerprint_detects_processing_changes_with_identical_vocab(self):
        from tokenizers import normalizers
        from singularity.model_audit.adapters import HuggingFaceCausalAdapter
        original = HuggingFaceCausalAdapter(self.model, self.tokenizer)
        changed_tokenizer = copy.deepcopy(self.tokenizer)
        changed_tokenizer.backend_tokenizer.normalizer = normalizers.Lowercase()
        changed = HuggingFaceCausalAdapter(self.model, changed_tokenizer)
        left, right = original.contract(), changed.contract()
        self.assertEqual(left["tokenizer_vocabulary_sha256"], right["tokenizer_vocabulary_sha256"])
        self.assertNotEqual(left["tokenizer_backend_sha256"], right["tokenizer_backend_sha256"])
        self.assertNotEqual(original.encode("THE CAT"), changed.encode("THE CAT"))
        before = original.contract()["tokenizer_backend_sha256"]
        original.observe([{"text": "the cat sat", "pad_to": 20}])
        self.assertEqual(original.contract()["tokenizer_backend_sha256"], before)
        self.assertEqual(left["tokenizer_encode_settings"],
                         {"add_special_tokens": False, "padding": False, "truncation": False})

    def test_pinned_provenance_is_copied_and_distinguishes_weight_files(self):
        from singularity.model_audit.adapters import HuggingFaceCausalAdapter
        source = {"model_repo": "example/model", "revision": "a" * 40,
                  "weight_files": {"model.safetensors": "b" * 64}}
        adapter = HuggingFaceCausalAdapter(self.model, self.tokenizer, provenance=source)
        source["weight_files"]["model.safetensors"] = "c" * 64
        contract = adapter.contract()
        self.assertEqual(contract["checkpoint_provenance"]["weight_files"]["model.safetensors"], "b" * 64)
        contract["checkpoint_provenance"]["weight_files"]["model.safetensors"] = "d" * 64
        self.assertEqual(adapter.contract()["checkpoint_provenance"]["weight_files"]["model.safetensors"], "b" * 64)
        other = HuggingFaceCausalAdapter(self.model, self.tokenizer, provenance=source)
        self.assertNotEqual(adapter.contract()["checkpoint_provenance"], other.contract()["checkpoint_provenance"])
        with self.assertRaises(ValueError):
            HuggingFaceCausalAdapter(self.model, self.tokenizer, provenance={"bad": float("nan")})
        with self.assertRaises(ValueError):
            HuggingFaceCausalAdapter(self.model, self.tokenizer, provenance=["not an object"])

    def test_cli_reloads_local_bfloat16_pipeline_and_snapshot_identity(self):
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from singularity.model_audit.adapters import HuggingFaceCausalAdapter
        from singularity.model_audit.__main__ import _local_hf_provenance, main
        with tempfile.TemporaryDirectory() as directory:
            snapshot = Path(directory) / "snapshot"
            copy.deepcopy(self.model).to(torch.bfloat16).save_pretrained(snapshot)
            self.tokenizer.save_pretrained(snapshot)
            model = AutoModelForCausalLM.from_pretrained(snapshot, torch_dtype=torch.bfloat16,
                                                         local_files_only=True, trust_remote_code=False)
            tokenizer = AutoTokenizer.from_pretrained(snapshot, local_files_only=True, trust_remote_code=False)
            provenance = _local_hf_provenance(snapshot, {"model_id": "local/test", "revision": "a" * 40,
                                                        "snapshot_manifest_sha256": ""})
            adapter = HuggingFaceCausalAdapter(model, tokenizer, provenance=provenance)
            probes = [{"id": "sentence", "text": "the cat sat", "cost": len(adapter.encode("the cat sat"))}]
            reference = adapter.observe(probes)
            fault = HuggingFaceCausalAdapter(model, tokenizer, provenance=provenance, temperature=1.3)
            package = build_package(probes, reference, [adapter.observe(probes)],
                                    {"temperature": fault.observe(probes)}, contract=adapter.contract(), requirement=1)
            path = Path(directory) / "package.json"
            save_package(package, path)
            with redirect_stdout(io.StringIO()) as output:
                status = main(["check", str(path), "--hf-model", str(snapshot)])
            report = json.loads(output.getvalue())
            self.assertEqual((status, report["verdict"]), (0, "unchanged"))
            self.assertEqual(report["contract_mismatches"], [])


if __name__ == "__main__":
    unittest.main()
