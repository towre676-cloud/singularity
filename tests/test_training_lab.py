"""Small scientific-contract checks for the optional real-training package.

These tests use no downloaded corpus, pretrained weights, or long training run.
The exact standard-library suite can still be discovered without PyTorch.
"""

import copy
import json
import math
from pathlib import Path
import tempfile
import unittest

try:
    import torch
except ImportError:
    torch = None


@unittest.skipIf(torch is None, "optional training tests require PyTorch")
class TrainingLabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._previous_threads = torch.get_num_threads()
        torch.set_num_threads(1)

    @classmethod
    def tearDownClass(cls):
        torch.set_num_threads(cls._previous_threads)

    def assertNestedEqual(self, actual, expected):
        if isinstance(actual, torch.Tensor):
            self.assertTrue(torch.equal(actual, expected))
        elif isinstance(actual, dict):
            self.assertEqual(set(actual), set(expected))
            for key in actual:
                self.assertNestedEqual(actual[key], expected[key])
        elif isinstance(actual, (tuple, list)):
            self.assertEqual(type(actual), type(expected))
            self.assertEqual(len(actual), len(expected))
            for left, right in zip(actual, expected):
                self.assertNestedEqual(left, right)
        else:
            self.assertEqual(actual, expected)

    def test_modular_split_excludes_reversed_pair_leakage(self):
        from singularity.training.data import modular_addition

        data = modular_addition(7, train_orbits_per_label=2,
                                tune_orbits_per_label=1, test_orbits_per_label=1)
        seen_pairs, split_orbits = set(), {}
        for name, batch in data.splits.items():
            inputs = batch["input_ids"].tolist()
            labels = batch["labels"].tolist()
            self.assertEqual(len(inputs), len(labels))
            current = set()
            for (a, b), y in zip(inputs, labels):
                self.assertEqual(y, (a + b) % 7)
                self.assertNotIn((a, b), seen_pairs)
                seen_pairs.add((a, b))
                current.add(tuple(sorted((a, b))))
            split_orbits[name] = current
        self.assertEqual(seen_pairs, {(a, b) for a in range(7) for b in range(7)})
        self.assertEqual([len(split_orbits[s]) for s in ("train", "tune", "test")],
                         [14, 7, 7])
        for left, right in (("train", "tune"), ("train", "test"), ("tune", "test")):
            self.assertFalse(split_orbits[left] & split_orbits[right])

    def test_modular_split_is_reproducible_and_rejects_leftovers(self):
        from singularity.training.data import modular_addition

        first = modular_addition(7, split_seed=23)
        second = modular_addition(7, split_seed=23)
        self.assertEqual(first.metadata, second.metadata)
        self.assertNestedEqual(first.splits, second.splits)
        with self.assertRaises(ValueError):
            modular_addition(7, train_orbits_per_label=1,
                             tune_orbits_per_label=1, test_orbits_per_label=1)

    def test_byte_targets_shift_once_and_do_not_cross_corpus_boundaries(self):
        from singularity.training.data import byte_language

        corpora = {"train": b"\x00ABCDEF", "tune": b"uvwxy", "test": b"12345"}
        with tempfile.TemporaryDirectory() as tmp:
            paths = {}
            for name, raw in corpora.items():
                paths[name] = Path(tmp) / (name + ".bin")
                paths[name].write_bytes(raw)
            data = byte_language(paths["train"], paths["tune"], paths["test"], seq_len=4)
            for name, raw in corpora.items():
                batch = data.splits[name]
                valid = batch["labels"] != -100
                self.assertEqual(batch["input_ids"][valid].tolist(), list(raw[:-1]))
                self.assertEqual(batch["labels"][valid].tolist(), list(raw[1:]))
            self.assertEqual(data.splits["train"]["input_ids"][0, 0].item(), 0)
            self.assertEqual(data.splits["train"]["labels"][0, 0].item(), ord("A"))
            self.assertEqual(data.splits["train"]["labels"][-1].tolist(),
                             [ord("E"), ord("F"), -100, -100])
            paths["test"].write_bytes(corpora["train"])
            with self.assertRaises(ValueError):
                byte_language(paths["train"], paths["tune"], paths["test"], seq_len=4)

    def test_lm_loss_uses_aligned_targets_and_ignores_padding(self):
        from singularity.training.data import loss_from_logits

        logits = torch.zeros(1, 3, 4, dtype=torch.float64)
        logits[0, 0, 1] = 4
        logits[0, 1, 2] = 4
        logits[0, 2, 3] = -100
        batch = {"labels": torch.tensor([[1, 2, -100]])}
        expected = torch.logsumexp(logits[0, 0], dim=-1) - 4
        self.assertAlmostEqual(loss_from_logits(logits, batch).item(), expected.item(), places=12)
        altered = logits.clone()
        altered[0, 2] = torch.tensor([1000., -1000., 1000., -1000.])
        self.assertEqual(loss_from_logits(logits, batch).item(),
                         loss_from_logits(altered, batch).item())

    def test_transformer_cannot_read_future_tokens(self):
        from singularity.training.models import CausalTransformer

        torch.manual_seed(31)
        model = CausalTransformer(11, 4, d_model=8, heads=2, layers=1).eval()
        inputs = torch.tensor([[1, 2, 3, 4], [1, 2, 8, 9]])
        with torch.no_grad():
            outputs = model(inputs)
        self.assertEqual(tuple(outputs.shape), (2, 4, 11))
        torch.testing.assert_close(outputs[0, :2], outputs[1, :2], rtol=0, atol=1e-6)
        self.assertFalse(torch.allclose(outputs[0, 2:], outputs[1, 2:]))

    def test_entropy_gap_uses_one_psd_spectrum_and_has_the_correct_sign(self):
        from singularity.training.telemetry import spectrum_summary

        for matrix in (torch.diag(torch.tensor([1., 0.])), torch.eye(3),
                       torch.diag(torch.tensor([.9, .1], dtype=torch.float64))):
            result = spectrum_summary(matrix)
            self.assertTrue(result["available"])
            self.assertLessEqual(result["delta"], 1e-12)
            self.assertTrue(result["delta_sanity_nonpositive"])
            self.assertGreaterEqual(result["rho"] * result["effective_rank"], 1 - 1e-12)
        unequal = spectrum_summary(torch.diag(torch.tensor([.9, .1], dtype=torch.float64)))
        self.assertAlmostEqual(unequal["delta"], .1 * math.log(.1 / .9), places=12)
        empty = spectrum_summary(torch.zeros(2, 2))
        self.assertFalse(empty["available"])
        for key in ("rho", "entropy", "delta", "effective_rank"):
            self.assertIsNone(empty[key])

    def test_update_sketch_preserves_missing_and_centered_distinctions(self):
        from singularity.training.telemetry import UpdateSketch

        sketch = UpdateSketch(3, dimension=4, window=3, seed=11)
        before = sketch.summary()
        self.assertFalse(before["available"])
        self.assertEqual(before["updates_seen"], 0)
        for _ in range(3):
            sketch.update(torch.tensor([1., 2., 4.]))
        constant = sketch.summary()
        self.assertFalse(constant["centered"]["available"])
        self.assertTrue(constant["uncentered"]["available"])
        self.assertIsNone(constant["centered"]["delta"])
        sketch.update(torch.zeros(3))
        varying = sketch.summary()
        self.assertEqual(varying["updates_seen"], 4)
        self.assertEqual(varying["window_updates"], 3)
        self.assertTrue(varying["centered"]["available"])
        self.assertLessEqual(varying["centered"]["delta"], 1e-12)
        with self.assertRaises(ValueError):
            sketch.update(torch.tensor([float("nan"), 1., 2.]))

    @staticmethod
    def _scalar_meta_fixture():
        model = torch.nn.Linear(1, 1, bias=False).double()
        with torch.no_grad():
            model.weight.fill_(.8)
        opt = torch.optim.AdamW(model.parameters(), lr=.1, weight_decay=.2,
                               betas=(.8, .9), eps=.25, amsgrad=True)
        parameter = model.weight
        opt.state[parameter] = {"step": torch.tensor(4.),
                                "exp_avg": torch.full_like(parameter, .3),
                                "exp_avg_sq": torch.full_like(parameter, .7),
                                "max_exp_avg_sq": torch.full_like(parameter, .9)}
        train = {"input_ids": torch.tensor([[1.]], dtype=torch.float64),
                 "labels": torch.tensor([[0.]], dtype=torch.float64)}
        tune = {"input_ids": torch.tensor([[2.]], dtype=torch.float64),
                "labels": torch.tensor([[1.]], dtype=torch.float64)}

        def half_square(outputs, batch):
            return .5 * (outputs - batch["labels"]).square().mean()

        return model, opt, train, tune, half_square

    def test_functional_hypergradients_match_moment_aware_scalar_and_finite_differences(self):
        from singularity.training.optim import meta_proposal

        model, opt, train, tune, loss_fn = self._scalar_meta_fixture()
        proposal = meta_proposal(model, opt, train, tune, loss_fn,
                                 {"max_backtracks": 0, "normalize_hypergradient": False})
        # Independent next-step oracle: step 5, real stored moments, AMSGrad,
        # and epsilon outside the bias-corrected variance square root.
        moment = (.8 * .3 + .2 * .8) / (1 - .8 ** 5)
        variance = max(.9, .9 * .7 + .1 * .8 ** 2) / (1 - .9 ** 5)
        direction = moment / (math.sqrt(variance) + .25)
        theta_next = (1 - .1 * .2) * .8 - .1 * direction
        validation_gradient = 2 * (2 * theta_next - 1)
        expected = {"log_lr": -.1 * validation_gradient * (direction + .2 * .8),
                    "log_shifted_weight_decay": -(.2 + 1e-4) * .1 * validation_gradient * .8}
        self.assertAlmostEqual(proposal["baseline_tune_loss"],
                               .5 * (2 * theta_next - 1) ** 2, places=12)

        def independent_loss(log_lr, log_decay):
            eta, decay = math.exp(log_lr), math.exp(log_decay) - 1e-4
            updated = (1 - eta * decay) * .8 - eta * direction
            return .5 * (2 * updated - 1) ** 2

        coordinates = [math.log(.1), math.log(.2 + 1e-4)]
        for index, name in enumerate(("log_lr", "log_shifted_weight_decay")):
            actual = proposal["hypergradients"][name]
            self.assertAlmostEqual(actual, expected[name], places=12)
            upper, lower = coordinates.copy(), coordinates.copy()
            upper[index] += 1e-6
            lower[index] -= 1e-6
            finite_difference = (independent_loss(*upper) - independent_loss(*lower)) / 2e-6
            self.assertAlmostEqual(actual, finite_difference, places=8)

    def test_meta_proposal_does_not_mutate_live_model_moments_gradients_or_rng(self):
        from singularity.training.optim import meta_proposal

        model, opt, train, tune, loss_fn = self._scalar_meta_fixture()
        model.train()
        model.weight.grad = torch.full_like(model.weight, 17.)
        state_before = copy.deepcopy(model.state_dict())
        optimizer_before = copy.deepcopy(opt.state_dict())
        grad_before = model.weight.grad.clone()
        rng_before = torch.get_rng_state().clone()
        proposal = meta_proposal(model, opt, train, tune, loss_fn, {"max_backtracks": 3})
        self.assertIsNotNone(proposal["hypergradients"])
        self.assertNestedEqual(model.state_dict(), state_before)
        self.assertNestedEqual(opt.state_dict(), optimizer_before)
        self.assertTrue(torch.equal(model.weight.grad, grad_before))
        self.assertTrue(torch.equal(torch.get_rng_state(), rng_before))
        self.assertTrue(model.training)
        if proposal["accepted"]:
            self.assertLess(proposal["candidate_tune_loss"], proposal["baseline_tune_loss"])

    def test_identical_tiny_runs_pair_states_and_keep_test_sealed(self):
        from singularity.training.runner import load_checkpoint, run

        config = {"task": "modular_addition", "p": 7, "seed": 77,
                  "split": {"train_orbits_per_label": 2, "tune_orbits_per_label": 1,
                            "test_orbits_per_label": 1},
                  "model": {"name": "mlp", "hidden": 8},
                  "optimizer": {"lr": .01, "weight_decay": .1},
                  "steps": 2, "eval_every": 2, "batch_size": 8,
                  "evaluate_test": False,
                  "telemetry": {"sketch_dimension": 4, "sketch_window": 4}}
        prior_determinism = torch.are_deterministic_algorithms_enabled()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                directories = [Path(tmp) / "first", Path(tmp) / "second"]
                results = [run(config, directory) for directory in directories]
                self.assertEqual(results[0]["final_train"], results[1]["final_train"])
                self.assertEqual(results[0]["final_tune"], results[1]["final_tune"])
                checkpoints = [load_checkpoint(directory / "checkpoint.pt")[2]
                               for directory in directories]
                for key in ("model", "optimizer", "torch_rng", "python_rng", "sampler_rng"):
                    self.assertNestedEqual(checkpoints[0][key], checkpoints[1][key])
                for result, directory in zip(results, directories):
                    self.assertEqual(result["optimizer_updates"], 2)
                    self.assertEqual(result["test_evaluations"], 0)
                    self.assertIsNone(result["final_test"])
                    records = [json.loads(line) for line in
                               (directory / "metrics.jsonl").read_text().splitlines()]
                    self.assertEqual(len(records), 2)
                    self.assertTrue(all("test" not in record for record in records))
        finally:
            torch.use_deterministic_algorithms(prior_determinism)

    def test_fixed_tune_probe_is_randomized_reproducible_and_not_the_train_rng(self):
        from singularity.training.data import modular_addition
        from singularity.training.runner import load_checkpoint, run

        split = {"train_orbits_per_label": 2, "tune_orbits_per_label": 1,
                 "test_orbits_per_label": 1}
        data = modular_addition(7, **split)
        probe_seed, probe_size = 271828, 8
        expected_probe = torch.randperm(len(data.splits["tune"]["labels"]),
                                       generator=torch.Generator().manual_seed(probe_seed))[:probe_size]
        self.assertNotEqual(expected_probe.tolist(), list(range(probe_size)))
        self.assertGreater(len(set(data.splits["tune"]["labels"][expected_probe].tolist())), 1)
        config = {"task": "modular_addition", "p": 7, "seed": 77, "split": split,
                  "model": {"name": "mlp", "hidden": 8},
                  "optimizer": {"lr": .01, "weight_decay": .1},
                  "steps": 2, "eval_every": 2, "batch_size": 8,
                  "evaluate_test": False, "variant": "meta",
                  # No proposal is due in this test: isolate probe selection
                  # from both adaptation and the stochastic training stream.
                  "meta": {"every": 99, "probe_seed": probe_seed, "batch_size": probe_size},
                  "telemetry": {"sketch_dimension": 4, "sketch_window": 4}}
        prior_determinism = torch.are_deterministic_algorithms_enabled()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                first_dir, second_dir, baseline_dir = (Path(tmp) / name for name in
                                                       ("meta77", "meta78", "baseline77"))
                first = run(config, first_dir)
                second = run({**config, "seed": 78}, second_dir)
                run({**config, "variant": "baseline"}, baseline_dir)
                for result, directory in ((first, first_dir), (second, second_dir)):
                    saved = json.loads((directory / "meta_probe.json").read_text())
                    self.assertEqual(saved, result["meta_probe"])
                    self.assertEqual(saved["indices"], expected_probe.tolist())
                    self.assertEqual(saved["seed"], probe_seed)
                first_state = load_checkpoint(first_dir / "checkpoint.pt")[2]
                baseline_state = load_checkpoint(baseline_dir / "checkpoint.pt")[2]
                expected_train_rng = torch.Generator().manual_seed(77 + 104729)
                for _ in range(2):
                    torch.randint(len(data.splits["train"]["labels"]), (8,), generator=expected_train_rng)
                self.assertTrue(torch.equal(first_state["sampler_rng"], expected_train_rng.get_state()))
                self.assertNestedEqual(first_state["sampler_rng"], baseline_state["sampler_rng"])
                self.assertNestedEqual(first_state["model"], baseline_state["model"])
        finally:
            torch.use_deterministic_algorithms(prior_determinism)


if __name__ == "__main__":
    unittest.main()
