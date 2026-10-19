"""Independent, model-free replay of retained pretrained experiment evidence.

No benchmark script or scoring implementation is imported. These tests read
the public receipts, observations and readable per-target traces directly.
"""
from collections import Counter, defaultdict
import base64
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import statistics
import unittest

try:
    import numpy as np
except ImportError:
    np = None

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "applications/training_lab/results"
AUDITS = RESULTS / "pretrained_audit"
PREDICTIONS = RESULTS / "pretrained_prediction"
MIN_COMPLETE_AUDITS = 3
MIN_COMPLETE_PREDICTIONS = 3
CONTINUOUS = ("top_logprob", "entropy", "continuation_logprob")
DOMAINS = ("reference_prose", "legal_prose", "source_code")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def comparison(actual, expected, tolerance, tie_margin):
    """Independent comparison of finite observations, including tie masking."""
    bad_length, mismatches = False, 0
    for field in ("argmax", "continuation"):
        if field not in expected:
            continue
        observed = actual.get(field, [])
        if len(observed) != len(expected[field]):
            bad_length = True
            continue
        for index, (got, want) in enumerate(zip(observed, expected[field])):
            tied = field == "argmax" and expected.get("top_gap", [math.inf] * len(observed))[index] <= tie_margin
            mismatches += int(got != want and not tied)
    deviations = {}
    for field in CONTINUOUS:
        if field not in expected:
            continue
        observed = actual.get(field, [])
        if len(observed) != len(expected[field]):
            bad_length = True
            continue
        deviations[field] = max((abs(got - want) for got, want in zip(observed, expected[field])), default=0.)
    return {"length_mismatch": bad_length, "discrete_mismatches": mismatches, "max_abs": deviations,
            "flags": bool(bad_length or mismatches or any(v > tolerance[k] for k, v in deviations.items()))}


def exhaustive_cost(costs, flags_by_fault, required):
    masks = [sum(1 << i for i, flag in enumerate(values) if flag) for values in flags_by_fault]
    best = math.inf
    for panel in range(1 << len(costs)):
        if all((panel & mask).bit_count() >= required for mask in masks):
            cost = sum(value for i, value in enumerate(costs) if panel >> i & 1)
            best = min(best, cost)
    return best


def logsumexp(values):
    largest = max(values)
    return largest + math.log(math.fsum(math.exp(v - largest) for v in values))


def mixture_loss(left_loss, right_loss, alpha):
    if alpha == 0:
        return left_loss
    if alpha == 1:
        return right_loss
    return -logsumexp((-left_loss + math.log1p(-alpha), -right_loss + math.log(alpha)))


def compressed_trace(record):
    output = io.BytesIO()
    with gzip.GzipFile(filename="", fileobj=output, mode="wb", mtime=0) as handle:
        handle.write(canonical(record))
    return output.getvalue()


def load_trace(relative):
    compressed = PREDICTIONS / relative
    plaintext = compressed.parent.parent / "traces" / compressed.name.removesuffix(".gz")
    if plaintext.exists():
        record = read(plaintext)
        if compressed.exists():
            if record != json.loads(gzip.decompress(compressed.read_bytes())):
                raise ValueError("readable and compressed traces disagree")
        return record, compressed_trace(record)
    return json.loads(gzip.decompress(compressed.read_bytes())), compressed.read_bytes()


def selected_documents(protocol):
    source = ROOT / protocol["document_source"]
    if sha(source.read_bytes()) != protocol["document_source_sha256"]:
        raise ValueError("original public source archive changed")
    candidates = json.loads(gzip.decompress(source.read_bytes()))["documents"]
    selected = []
    for domain in DOMAINS:
        members = [d for d in candidates if d["domain"] == domain]
        members.sort(key=lambda d: sha(("singularity-pretrained-v1/" + domain + "/" + d["name"]).encode()))
        for document in members[:protocol["documents_per_domain"]]:
            selected.append({key: document[key] for key in ("domain", "name", "bytes", "sha256", "base64")})
    return selected


class PretrainedAuditEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.completed = sorted(AUDITS.glob("*/results.json"))
        if not cls.completed:
            raise AssertionError("required pretrained audit evidence is missing")

    def test_complete_audit_population_and_frozen_identity(self):
        self.assertGreaterEqual(len(self.completed), MIN_COMPLETE_AUDITS)
        for path in self.completed:
            with self.subTest(model=path.parent.name):
                protocol, result, package = read(path.parent / "protocol.json"), read(path), read(path.parent / "package.json")
                self.assertEqual(sha(canonical(protocol["protocol"])), protocol["protocol_sha256"])
                self.assertEqual(result["protocol_sha256"], protocol["protocol_sha256"])
                self.assertEqual(sha((path.parent / "frozen_panel.json").read_bytes()), result["frozen_panel_sha256"])
                self.assertTrue(read(path.parent / "frozen_panel.json")["frozen_before_heldout_observations"])
                for filename, digest in protocol["dependency_sha256"].items():
                    self.assertEqual(sha((ROOT / filename).read_bytes()), digest, filename)
                self.assertEqual(package["contract"]["checkpoint_provenance"],
                                 {"model_id": protocol["model_id"], "revision": protocol["revision"],
                                  "snapshot_manifest_sha256": sha(canonical(protocol["snapshot_manifest"]))})
                self.assertEqual(package["contract"]["dtype"], "torch." + protocol["dtype"])
                self.assertEqual(result["environment"]["dtype"], protocol["dtype"])

    def tables(self, directory):
        protocol, observations = read(directory / "protocol.json"), read(directory / "observations.json")
        specification = protocol["protocol"]["tolerance"]
        runs = [observations["reference"], *observations["calibration"],
                *observations["construction"].values(), *observations["heldout"].values(),
                *observations["clean_audit"].values()]
        for run in runs:
            self.assertEqual(len(run), len(protocol["probes"]))
            for observation in run:
                for field in (*CONTINUOUS, "top_gap"):
                    self.assertTrue(all(math.isfinite(value) for value in observation.get(field, [])))
        tolerances = []
        for index, expected in enumerate(observations["reference"]):
            maxima = {field: 0. for field in CONTINUOUS if field in expected}
            for clean in observations["calibration"]:
                differences = comparison(clean[index], expected, {key: math.inf for key in maxima}, specification["tie_margin"])
                self.assertFalse(differences["length_mismatch"] or differences["discrete_mismatches"])
                maxima = {field: max(value, differences["max_abs"][field]) for field, value in maxima.items()}
            self.assertEqual(maxima, observations["calibration_maxima"][index])
            tolerances.append({field: specification["factor"] * value + specification["floor"] for field, value in maxima.items()})
        self.assertEqual(tolerances, observations["tolerances"])
        reports = {name: [comparison(row, reference, tolerance, specification["tie_margin"])
                          for row, reference, tolerance in zip(rows, observations["reference"], tolerances)]
                   for name, rows in {**observations["construction"], **observations["heldout"], **observations["clean_audit"]}.items()}
        return protocol, observations, reports

    def test_observations_recompute_flags_exact_optimum_and_erasures(self):
        for path in self.completed:
            with self.subTest(model=path.parent.name):
                protocol, observations, reports = self.tables(path.parent)
                result, package = read(path), read(path.parent / "package.json")
                probes, selection = protocol["probes"], result["selection"]
                index = {probe["id"]: i for i, probe in enumerate(probes)}
                requirement = protocol["protocol"]["requirement"]
                for probe, observed in zip(probes, observations["reference"]):
                    self.assertEqual(probe["cost"], max(len(observed["argmax"]), probe.get("pad_to", 0)))
                flags = {name: [r["flags"] for r in rows] for name, rows in reports.items()}
                self.assertEqual(set(observations["construction"]), set(protocol["protocol"]["construction_faults"]))
                self.assertEqual(set(observations["heldout"]), set(protocol["protocol"]["heldout_faults"]))
                eligible = {name for name in observations["construction"] if sum(flags[name]) >= requirement}
                self.assertEqual(set(selection["eligible_faults"]), eligible)
                self.assertEqual(selection["unavailable_faults"],
                                 {name: sum(flags[name]) for name in observations["construction"] if name not in eligible})
                self.assertEqual(result["pool_separator_counts"],
                                 {name: sum(flags[name]) for name in (*observations["construction"], *observations["heldout"])})
                optimum = exhaustive_cost([p["cost"] for p in probes], [flags[n] for n in sorted(eligible)], requirement)
                self.assertEqual(optimum, selection["exact"]["cost"])
                self.assertEqual(optimum, selection["independent_enumeration"]["minimum_cost"])
                self.assertEqual(selection["independent_enumeration"]["subsets"], 1 << len(probes))
                self.assertEqual(result["full_pool_cost"], sum(p["cost"] for p in probes))
                for label in ("exact", "greedy"):
                    panel = result["panels"][label]
                    members = [index[identifier] for identifier in panel["probe_ids"]]
                    self.assertEqual(panel["cost"], sum(probes[i]["cost"] for i in members))
                    for name, report in panel["faults"].items():
                        count = sum(flags[name][i] for i in members)
                        self.assertEqual((count, count > 0, count >= requirement),
                                         (report["separating_probes"], report["detected"], report["robust"]))
                        if name in eligible:
                            self.assertGreaterEqual(count, requirement)
                    for name, reported in panel["clean_false_alarms"].items():
                        self.assertEqual(reported, [probes[i]["id"] for i in members if flags[name][i]])
                for lost, evidence in result["all_single_probe_erasures"].items():
                    for fault, separated in evidence.items():
                        actual = any(flags[fault][index[p["id"]]] for p in package["probes"] if p["id"] != lost)
                        self.assertEqual(actual, separated)
                        self.assertTrue(actual)

    def test_package_digest_witness_and_fault_evidence_bind_observations(self):
        for path in self.completed:
            with self.subTest(model=path.parent.name):
                protocol, observations, reports = self.tables(path.parent)
                package, result = read(path.parent / "package.json"), read(path)
                self.assertEqual(package["package_sha256"], sha(canonical({k: v for k, v in package.items() if k != "package_sha256"})))
                self.assertEqual(package["deficient_faults"], [])
                index = {p["id"]: i for i, p in enumerate(protocol["probes"])}
                ids = {p["id"] for p in package["probes"]}
                for p in package["probes"]:
                    self.assertEqual(p["expected"], observations["reference"][index[p["id"]]])
                    self.assertEqual(p["tolerance"], observations["tolerances"][index[p["id"]]])
                self.assertEqual({w["distinction"] for w in package["witness"]}, set(package["coverage"]))
                for witness in package["witness"]:
                    fault, selected = witness["distinction"], witness["separating_probes"]
                    self.assertEqual(len(set(selected)), package["requirement"])
                    self.assertTrue(set(selected) <= ids)
                    self.assertTrue(all(reports[fault][index[i]]["flags"] for i in selected))
                for fault, evidence in package["fault_evidence"].items():
                    self.assertEqual(evidence, {identifier: reports[fault][index[identifier]] for identifier in sorted(ids)})
                    self.assertEqual(package["coverage"][fault], sum(reports[fault][index[i]]["flags"] for i in ids))
                for name, check in result["package_checks_from_retained_observations"].items():
                    flagged = [p["id"] for p in package["probes"] if reports[name][index[p["id"]]]["flags"]]
                    self.assertEqual(check["flagged_probes"], flagged)
                    self.assertEqual(check["verdict"], "changed" if flagged else "unchanged")
                timing = result["timing"]
                medians = {label: statistics.median(r[label] for r in timing["pairs"]) for label in ("full_pool", "panel_check")}
                self.assertEqual(medians, timing["median_seconds"])
                self.assertEqual(medians["full_pool"] / medians["panel_check"], timing["speed_ratio_full_over_panel"])


class PretrainedPredictionEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.completed = sorted(PREDICTIONS.glob("models/*/results.json"))
        if not cls.completed:
            raise AssertionError("required pretrained prediction evidence is missing")
        cls.protocol = read(PREDICTIONS / "protocol.json")

    def records(self, report):
        rows = []
        for relative, digest in report["trace_files_sha256"].items():
            record, compressed = load_trace(relative)
            self.assertEqual(sha(compressed), digest)
            rows.append(record)
        return sorted(rows, key=lambda r: r["document"])

    def test_complete_prediction_population_and_document_identity(self):
        self.assertGreaterEqual(len(self.completed), MIN_COMPLETE_PREDICTIONS)
        documents = selected_documents(self.protocol)
        self.assertEqual(sha(canonical(documents)), self.protocol["documents_sha256"])
        self.assertEqual(len(documents), 3 * self.protocol["documents_per_domain"])
        for document in documents:
            raw = base64.b64decode(document["base64"], validate=True)
            self.assertEqual((len(raw), sha(raw)), (document["bytes"], document["sha256"]))
        for source, digest in self.protocol["dependency_sha256"].items():
            self.assertEqual(sha((ROOT / source).read_bytes()), digest)
        for path in self.completed:
            report = read(path)
            self.assertEqual(report["protocol_receipt_sha256"], sha((PREDICTIONS / "protocol.json").read_bytes()))
            identity = self.protocol["models"][report["model"]]
            self.assertEqual(sha(canonical(identity["files"])), report["model_files_manifest_sha256"])
            self.assertEqual(report["environment"]["dtype"], identity["dtype"])
            self.assertEqual(report["neural_training_updates"], 0)
            rows = self.records(report)
            self.assertEqual(len(rows), len(documents))
            for row, encoded in zip(rows, identity["encoded_documents"]):
                self.assertEqual(row["document"], encoded["document"])
                self.assertEqual(row["source_sha256"], documents[row["document"]]["sha256"])
                self.assertEqual(row["token_ids_sha256"], sha(canonical(encoded["token_ids"])))
                self.assertEqual(row["targets"], len(encoded["token_ids"]) - 1)

    def test_hex_losses_causal_counts_and_bayesian_regret_replay(self):
        for path in self.completed:
            report = read(path)
            identity = self.protocol["models"][report["model"]]
            encoded = {row["document"]: row for row in identity["encoded_documents"]}
            for row in self.records(report):
                with self.subTest(model=report["model"], document=row["document"]):
                    losses = {arm: [float.fromhex(v) for v in values] for arm, values in row["losses_hex"].items()}
                    self.assertEqual(set(losses), set(self.protocol["arms"]))
                    for arm, values in losses.items():
                        self.assertEqual(len(values), row["targets"])
                        self.assertTrue(all(math.isfinite(v) and v >= 0 for v in values))
                        self.assertEqual(math.fsum(values).hex(), row["arms"][arm]["loss_sum_nats_hex"])
                        self.assertTrue(0 <= row["arms"][arm]["correct"] <= row["targets"])
                    # Initially no target has been observed: uniform backoff.
                    vocabulary = round(math.exp(losses["adaptive_count"][0]))
                    self.assertEqual(vocabulary, identity["tokenizer_length"])
                    self.assertAlmostEqual(math.log(vocabulary), losses["adaptive_count"][0], places=11)
                    tokens = encoded[row["document"]]["token_ids"]
                    events, totals, followers = Counter(), Counter(), defaultdict(set)
                    for i, target in enumerate(tokens[1:]):
                        prefix = tokens[:i + 1]
                        contexts = [tuple(prefix[-order:]) if order else () for order in range(min(4, len(prefix)) + 1)]
                        uniform, backed = 1 / vocabulary, math.exp(-losses["neural"][i])
                        for context in contexts:
                            if totals[context]:
                                distinct = len(followers[context])
                                denominator = totals[context] + distinct
                                uniform = (events[context, target] + distinct * uniform) / denominator
                                backed = (events[context, target] + distinct * backed) / denominator
                        self.assertAlmostEqual(-math.log(uniform), losses["adaptive_count"][i], places=10)
                        self.assertAlmostEqual(-math.log(backed), losses["neural_backed_adaptive"][i], places=10)
                        for context in contexts:
                            events[context, target] += 1
                            totals[context] += 1
                            followers[context].add(target)
                        self.assertAlmostEqual(mixture_loss(losses["neural"][i], losses["adaptive_count"][i], .5),
                                               losses["fixed_half_blend"][i], places=10)
                    for arm, expert in (("online_blend", "adaptive_count"), ("online_neural_backed", "neural_backed_adaptive")):
                        cumulative = [0.] * 21
                        replay = []
                        weights = [float.fromhex(v) for v in row["prior_to_target_count_weights_hex"][arm]]
                        for i, (neural, count) in enumerate(zip(losses["neural"], losses[expert])):
                            before = [value - math.log(21) for value in cumulative]
                            evidence = logsumexp(before)
                            alpha = math.fsum((k / 20) * math.exp(value - evidence) for k, value in enumerate(before))
                            self.assertAlmostEqual(alpha, weights[i], places=9)
                            grid = [-mixture_loss(neural, count, k / 20) for k in range(21)]
                            cumulative = [old + new for old, new in zip(cumulative, grid)]
                            predictive_loss = evidence - logsumexp([v - math.log(21) for v in cumulative])
                            replay.append(predictive_loss)
                            self.assertAlmostEqual(predictive_loss, losses[arm][i], places=8)
                        audit = row["online_audits"][arm]
                        best = -max(cumulative)
                        online = math.fsum(losses[arm])
                        self.assertAlmostEqual(best, audit["best_fixed_grid_cumulative_nll"], places=7)
                        self.assertAlmostEqual(online - best, audit["regret_nats"], places=7)
                        self.assertLessEqual(online - best, math.log(21) + 1e-7)

    @unittest.skipIf(np is None, "optional NumPy unavailable for document bootstrap")
    def test_aggregates_and_document_cluster_intervals_replay(self):
        for path in self.completed:
            report = read(path)
            rows = self.records(report)
            for domain, summary in report["domains"].items():
                members = [r for r in rows if domain == "all_domains" or r["domain"] == domain]
                sizes = np.array([r["targets"] for r in members])
                self.assertEqual(summary["targets"], int(sizes.sum()))
                self.assertEqual(summary["documents"], len(members))
                for arm, metric in summary["arms"].items():
                    total = math.fsum(float.fromhex(r["arms"][arm]["loss_sum_nats_hex"]) for r in members)
                    self.assertEqual(total / int(sizes.sum()), metric["nll_nats_per_token"])
                    self.assertEqual(sum(r["arms"][arm]["correct"] for r in members) / int(sizes.sum()), metric["accuracy"])
                for name, paired in summary["paired"].items():
                    left, right = name.split("_minus_")
                    differences = np.array([float.fromhex(r["arms"][left]["loss_sum_nats_hex"])
                                            - float.fromhex(r["arms"][right]["loss_sum_nats_hex"]) for r in members])
                    draws = np.random.default_rng(90211).integers(0, len(members), size=(10000, len(members)))
                    interval = np.quantile(differences[draws].sum(1) / sizes[draws].sum(1), [.025, .975])
                    np.testing.assert_allclose(interval, paired["percentile_95_interval"], rtol=0, atol=1e-12)
                    self.assertEqual(float(differences.sum() / sizes.sum()), paired["difference_nats_per_token"])
                    self.assertEqual(int((differences < 0).sum()), paired["documents_first_better"])


class PretrainedProtectedPriorEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = PREDICTIONS / "posthoc_prior_analysis.json"
        if not path.exists():
            raise AssertionError("required explicitly posthoc prior analysis is missing")
        cls.report = read(path)
        cls.protocol = read(PREDICTIONS / "protocol.json")

    def test_posthoc_status_all_models_and_primary_receipts_are_preserved(self):
        report = self.report
        self.assertTrue(report["analysis_status"].startswith("POSTHOC"))
        self.assertEqual(report["model_forward_calls"], 0)
        self.assertEqual(report["neural_training_updates"], 0)
        self.assertEqual(report["protocol_receipt_sha256"], sha((PREDICTIONS / "protocol.json").read_bytes()))
        self.assertEqual(set(report["models"]), set(self.protocol["models"]))
        self.assertEqual(set(report["all_frozen_models_included"]), set(self.protocol["models"]))
        self.assertGreaterEqual(len(report["models"]), MIN_COMPLETE_PREDICTIONS)
        self.assertEqual(report["weight_grid"], [i / 20 for i in range(21)])
        self.assertAlmostEqual(report["initial_prior"][0], .95, places=14)
        self.assertAlmostEqual(math.fsum(report["initial_prior"]), 1., places=14)
        self.assertTrue(all(value > 0 for value in report["initial_prior"]))
        ceiling = -math.log(report["initial_prior"][0])
        self.assertEqual(report["neural_excess_loss_ceiling_nats_per_document"], ceiling)
        self.assertEqual(report["neural_excess_loss_ceiling_nats_per_token_at512_targets"], ceiling / 512)
        total_documents = 0
        for name, model in report["models"].items():
            primary_path = PREDICTIONS / "models" / name / "results.json"
            primary = read(primary_path)
            self.assertEqual(model["primary_results_sha256"], sha(primary_path.read_bytes()))
            self.assertEqual(model["primary_trace_files_sha256"], primary["trace_files_sha256"])
            self.assertEqual({r["document"] for r in model["documents"]},
                             {r["document"] for r in self.protocol["models"][name]["encoded_documents"]})
            total_documents += len(model["documents"])
        self.assertGreaterEqual(total_documents, 72)
        self.assertEqual(report["trigger_results_sha256"],
                         report["models"][report["trigger_model"]]["primary_results_sha256"])
        for source, digest in report["source_sha256"].items():
            self.assertEqual(sha((ROOT / source).read_bytes()), digest)

    def test_all_document_joint_likelihoods_causal_weights_and_neural_ceiling(self):
        priors, grid = self.report["initial_prior"], self.report["weight_grid"]
        log_priors = [math.log(value) for value in priors]
        for name, model in self.report["models"].items():
            primary = read(PREDICTIONS / "models" / name / "results.json")
            originals = {}
            for relative, digest in primary["trace_files_sha256"].items():
                original, compressed = load_trace(relative)
                self.assertEqual(sha(compressed), digest)
                originals[original["document"]] = original
            for row in model["documents"]:
                with self.subTest(model=name, document=row["document"]):
                    original = originals[row["document"]]
                    neural = [float.fromhex(v) for v in original["losses_hex"]["neural"]]
                    count = [float.fromhex(v) for v in original["losses_hex"]["adaptive_count"]]
                    losses = [float.fromhex(v) for v in row["protected_target_losses_hex"]]
                    weights = [float.fromhex(v) for v in row["protected_prior_to_target_count_weights_hex"]]
                    self.assertEqual(len(losses), original["targets"])
                    self.assertEqual(len(weights), original["targets"])
                    # Independently form each fixed expert's joint loss, then
                    # the nonuniform mixture of their JOINT likelihoods.
                    grid_rows = [[mixture_loss(left, right, alpha) for left, right in zip(neural, count)] for alpha in grid]
                    fixed_losses = [math.fsum(values) for values in grid_rows]
                    joint_loss = -logsumexp([prior - loss for prior, loss in zip(log_priors, fixed_losses)])
                    protected_total = float.fromhex(row["arms"]["neural_protected_prior_blend"]["loss_sum_nats_hex"])
                    self.assertEqual(math.fsum(losses).hex(), protected_total.hex())
                    self.assertAlmostEqual(joint_loss, protected_total, delta=1e-8)
                    neural_total = math.fsum(neural)
                    ceiling = -log_priors[0]
                    self.assertLessEqual(joint_loss - neural_total, ceiling + 1e-8)
                    self.assertAlmostEqual(row["observed_protected_minus_neural_nats"], protected_total - neural_total, delta=1e-10)
                    guarantee = row["prior_guarantee"]
                    self.assertEqual(guarantee["initial_prior"], priors)
                    self.assertAlmostEqual(guarantee["pure_neural_extra_loss_ceiling_nats"], ceiling, delta=1e-14)
                    self.assertAlmostEqual(guarantee["best_prior_adjusted_cumulative_nll"],
                                           min(loss - prior for loss, prior in zip(fixed_losses, log_priors)), delta=1e-8)
                    for actual, expected in zip(guarantee["fixed_grid_cumulative_nll"], fixed_losses):
                        self.assertAlmostEqual(actual, expected, delta=1e-8)
                    cumulative, evidence = [0.] * len(grid), logsumexp(log_priors)
                    for i, recorded in enumerate(losses):
                        alpha = math.fsum(weight * math.exp(prior - loss - evidence)
                                          for weight, prior, loss in zip(grid, log_priors, cumulative))
                        self.assertAlmostEqual(alpha, weights[i], delta=1e-9)
                        cumulative = [old + values[i] for old, values in zip(cumulative, grid_rows)]
                        updated = logsumexp([prior - loss for prior, loss in zip(log_priors, cumulative)])
                        self.assertAlmostEqual(evidence - updated, recorded, delta=1e-8)
                        evidence = updated

    @unittest.skipIf(np is None, "optional NumPy unavailable for document bootstrap")
    def test_posthoc_domain_aggregates_and_cluster_intervals(self):
        for model in self.report["models"].values():
            rows = model["documents"]
            for domain, summary in model["domains"].items():
                members = [r for r in rows if domain == "all_domains" or r["domain"] == domain]
                sizes = np.array([r["targets"] for r in members])
                self.assertEqual(summary["documents"], len(members))
                self.assertEqual(summary["targets"], int(sizes.sum()))
                self.assertTrue(summary["all_documents_within_neural_excess_loss_ceiling"])
                self.assertEqual(summary["total_neural_excess_loss_ceiling_nats"],
                                 math.fsum(r["prior_guarantee"]["pure_neural_extra_loss_ceiling_nats"] for r in members))
                for arm, metrics in summary["arms"].items():
                    total = math.fsum(float.fromhex(r["arms"][arm]["loss_sum_nats_hex"]) for r in members)
                    self.assertEqual(metrics["nll_nats_per_token"], total / int(sizes.sum()))
                for name, paired in summary["paired"].items():
                    left, right = name.split("_minus_")
                    differences = np.array([float.fromhex(r["arms"][left]["loss_sum_nats_hex"])
                                            - float.fromhex(r["arms"][right]["loss_sum_nats_hex"]) for r in members])
                    draws = np.random.default_rng(90211).integers(0, len(members), size=(10000, len(members)))
                    interval = np.quantile(differences[draws].sum(1) / sizes[draws].sum(1), [.025, .975])
                    np.testing.assert_allclose(interval, paired["percentile_95_interval"], rtol=0, atol=1e-12)
                    self.assertEqual(float(differences.sum() / sizes.sum()), paired["difference_nats_per_token"])
                    self.assertEqual(int((differences < 0).sum()), paired["documents_first_better"])


if __name__ == "__main__":
    unittest.main()
