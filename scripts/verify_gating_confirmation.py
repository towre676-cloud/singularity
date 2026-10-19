#!/usr/bin/env python3
"""Independent, model-free standard-library replay of repetition-gate evidence.

No experiment runner, Singularity implementation, neural library or model
checkpoint is imported. Frozen token IDs reconstruct prefix-only count states;
closed-form component likelihoods reconstruct every protected prediction.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "applications/training_lab/results/pretrained_gating"
POLICIES = tuple({"id": f"order{o}_support{s}_alpha{int(a * 100):03d}",
                  "min_order": o, "min_support": s, "alpha": a}
                 for o in (1, 2, 3) for s in (1, 2) for a in (.25, .5, 1.))
NEURAL_PRIOR = .95
CEILING = -math.log(NEURAL_PRIOR)


def read(path):
    return json.loads(Path(path).read_text())


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def near(actual, expected, message, absolute=1e-10):
    require(math.isfinite(actual) and math.isfinite(expected)
            and math.isclose(actual, expected, rel_tol=2e-12, abs_tol=absolute), message)


def relative(directory, path):
    result = (directory / path).resolve()
    require(result.is_relative_to(directory.resolve()), "evidence path escapes its directory")
    return result


def bound_file(directory, path, expected):
    result = relative(directory, path)
    require(file_sha(result) == expected, "bound file bytes differ: " + str(path))
    require(result.stat().st_size <= 65536, "readable evidence exceeds64KiB: " + str(path))
    return result


def log_total(values):
    values = tuple(values)
    maximum = max(values)
    return maximum + math.log(math.fsum(math.exp(value - maximum) for value in values))


def mix_log(neural, count, alpha):
    if alpha == 0:
        return neural
    if alpha == 1:
        return count
    return log_total((neural + math.log1p(-alpha), count + math.log(alpha)))


def count_rows(token_ids, vocabulary_size):
    """Build counts from observed prefix edges; initial token is history only."""
    require(type(vocabulary_size) is int and vocabulary_size > 0, "invalid vocabulary size")
    require(len(token_ids) >= 2 and all(type(t) is int and 0 <= t < vocabulary_size for t in token_ids),
            "native token ID lies outside vocabulary")
    tables = [dict() for _ in range(5)]
    prefix = [token_ids[0]]
    for target in token_ids[1:]:
        history = tuple(prefix[-4:])
        feature = {"context": list(history), "longest_order": -1, "support": 0, "distinct": 0}
        probability = 1 / vocabulary_size
        for order in range(min(4, len(history)) + 1):
            key = history[-order:] if order else ()
            followers = tables[order].get(key)
            if followers:
                total, distinct = sum(followers.values()), len(followers)
                probability = (followers.get(target, 0) + distinct * probability) / (total + distinct)
                feature.update(longest_order=order, support=total, distinct=distinct)
        yield {"target": target, "count_nll_hex": (-math.log(probability)).hex(), "feature": feature}
        # Updating after yield makes accidental target leakage explicit.
        for order in range(min(4, len(history)) + 1):
            key = history[-order:] if order else ()
            tables[order].setdefault(key, Counter())[target] += 1
        prefix.append(target)


def reconstruct(rows, policies=POLICIES):
    """Expand exact retained digest and check an alternate probability identity.

    Prefix likelihood tables are formed first. Posterior t uses table entry t,
    which contains only the preceding t targets, never likelihood t itself.
    """
    require(bool(rows), "empty target trace")
    neural_logs = [-float.fromhex(row["neural_nll_hex"]) for row in rows]
    count_logs = [-float.fromhex(row["count_nll_hex"]) for row in rows]
    require(all(math.isfinite(x) and x <= 0 for x in neural_logs + count_logs), "nonfinite or negative loss")
    alphas, raw_logs, active = {}, {}, {}
    for policy in policies:
        name = policy["id"]
        alphas[name] = [policy["alpha"] if row["feature"]["longest_order"] >= policy["min_order"]
                        and row["feature"]["support"] >= policy["min_support"] else 0. for row in rows]
        active[name] = sum(alpha > 0 for alpha in alphas[name])
        raw_logs[name] = [mix_log(n, c, alpha) for n, c, alpha in zip(neural_logs, count_logs, alphas[name])]
    all_logs = {"neural": neural_logs, **raw_logs,
                "ungated": [mix_log(n, c, .5) for n, c in zip(neural_logs, count_logs)]}
    prefixes = {}
    for name, likelihoods in all_logs.items():
        values = [0.]
        for value in likelihoods:
            values.append(values[-1] + value)
        prefixes[name] = values
    prior = [math.log(NEURAL_PRIOR)] + [math.log((1 - NEURAL_PRIOR) / len(policies))] * len(policies)
    component_names = ["neural", *(p["id"] for p in policies)]
    losses = {"neural": [-x for x in neural_logs], "adaptive_count": [-x for x in count_logs]}
    weights, raw_sums = {}, {}
    for policy in policies:
        name = policy["id"]
        protected, current_weights, previous = [], [], 0.
        for t, alpha in enumerate(alphas[name]):
            before = log_total((math.log(NEURAL_PRIOR) + prefixes["neural"][t],
                                math.log1p(-NEURAL_PRIOR) + prefixes[name][t]))
            policy_mass = math.exp(math.log1p(-NEURAL_PRIOR) + prefixes[name][t] - before)
            current_weights.append(policy_mass * alpha)
            # The public commitment fixes binary64's left-associated
            # (log prior + prefix) + current log likelihood. Preserve that
            # serialization schedule; the direct probability identity below
            # independently checks its mathematical prediction.
            cumulative = -log_total((math.log(NEURAL_PRIOR) + prefixes["neural"][t] + neural_logs[t],
                                     math.log1p(-NEURAL_PRIOR) + prefixes[name][t + 1]))
            protected.append(cumulative - previous)
            # Keep posterior components in log space. Collapsing a posterior
            # extremely near one into 1-count_weight loses the tiny neural
            # mass and can perturb a rare-target loss by several nanonats.
            direct = -log_total((math.log(NEURAL_PRIOR) + prefixes["neural"][t] - before + neural_logs[t],
                                 math.log1p(-NEURAL_PRIOR) + prefixes[name][t] - before + raw_logs[name][t]))
            near(protected[-1], direct, "protected pretarget predictive identity differs", 2e-9)
            require(cumulative <= -prefixes["neural"][t + 1] + CEILING + 2e-8,
                    "protected prefix ceiling failed")
            previous = cumulative
        losses[name], weights[name], raw_sums[name] = protected, current_weights, math.fsum(-v for v in raw_logs[name])
    hierarchy_weights, ungated_weights = [], []
    losses["hierarchy_protected"], losses["ungated_protected"] = [], []
    previous_hierarchy = previous_ungated = 0.
    for t in range(len(rows)):
        joint_before = [pi + prefixes[name][t] for pi, name in zip(prior, component_names)]
        denominator = log_total(joint_before)
        posterior = [math.exp(value - denominator) for value in joint_before]
        hierarchy_weights.append(posterior)
        near(math.fsum(posterior), 1., "hierarchy posterior not normalized")
        after = -log_total(pi + prefixes[name][t + 1] for pi, name in zip(prior, component_names))
        hierarchy_loss = after - previous_hierarchy
        direct_hierarchy = -log_total(value - denominator + all_logs[name][t]
                                      for value, name in zip(joint_before, component_names))
        near(hierarchy_loss, direct_hierarchy, "hierarchy pretarget identity differs", 2e-9)
        losses["hierarchy_protected"].append(hierarchy_loss)
        previous_hierarchy = after
        ungated_before = log_total((math.log(NEURAL_PRIOR) + prefixes["neural"][t],
                                    math.log1p(-NEURAL_PRIOR) + prefixes["ungated"][t]))
        mass = math.exp(math.log1p(-NEURAL_PRIOR) + prefixes["ungated"][t] - ungated_before)
        ungated_weights.append(mass)
        ungated_after = -log_total((math.log(NEURAL_PRIOR) + prefixes["neural"][t + 1],
                                    math.log1p(-NEURAL_PRIOR) + prefixes["ungated"][t + 1]))
        ungated_loss = ungated_after - previous_ungated
        direct_ungated = -log_total((math.log(NEURAL_PRIOR) + prefixes["neural"][t] - ungated_before + neural_logs[t],
                                     math.log1p(-NEURAL_PRIOR) + prefixes["ungated"][t] - ungated_before + all_logs["ungated"][t]))
        near(ungated_loss, direct_ungated, "ungated pretarget identity differs", 2e-9)
        losses["ungated_protected"].append(ungated_loss)
        previous_ungated = ungated_after
    neural_sum = math.fsum(losses["neural"])
    tolerance = 1e-9 + 2**-36 * abs(neural_sum)
    arms = {}
    for name, values in losses.items():
        total = math.fsum(values)
        arms[name] = {"loss_sum_nats_hex": total.hex(), "nll_nats_per_token": total / len(rows)}
        if name not in ("neural", "adaptive_count"):
            slack = neural_sum + CEILING - total
            require(slack >= -tolerance, "whole-document neural protection ceiling failed")
            arms[name]["neural_protection_slack_nats"] = slack
    return {"arms": arms, "losses_hex": {k: [v.hex() for v in values] for k, values in losses.items()},
            "raw_gate_loss_sum_nats_hex": {k: value.hex() for k, value in raw_sums.items()},
            "gate_active_targets": active,
            "prior_to_target_count_weights_hex": {k: [v.hex() for v in values] for k, values in weights.items()},
            "hierarchy_prior_to_target_posterior_hex": [[v.hex() for v in values] for values in hierarchy_weights],
            "ungated_prior_to_target_policy_weight_hex": [v.hex() for v in ungated_weights],
            "neural_extra_loss_ceiling_nats": CEILING, "rounding_allowance_nats": tolerance}


def check_protocol(output):
    protocol = read(output / "protocol.json")
    require(protocol["schema"] == "singularity.pretrained-gating-protocol/1", "unknown frozen protocol")
    require(protocol["documents_scored_before_freeze"] is False, "protocol not declared prospective")
    require(tuple(protocol["policies"]) == POLICIES and len(POLICIES) == 18, "declared policy population differs")
    require(protocol["max_targets"] == 512 and protocol["execution"]["neural_training_updates"] == 0,
            "target/training contract differs")
    source = bound_file(ROOT, protocol["source_path"], protocol["source_sha256"])
    manifest = read(source)
    require(len(manifest["documents"]) == len(protocol["documents"]) == 36, "corpus population differs")
    require(len({d["sha256"] for d in protocol["documents"]}) == 36, "duplicate corpus fragments")
    for name, expected in protocol["dependency_sha256"].items():
        require(file_sha(relative(ROOT, name)) == expected, "frozen code bytes differ: " + name)
    identities, encoded = {}, {}
    for index, (frozen, row) in enumerate(zip(protocol["documents"], manifest["documents"])):
        require(frozen["document"] == index, "document indices not contiguous")
        for key in ("name", "domain", "sha256", "source_url", "license"):
            require(frozen[key] == row[key], "source metadata differs: " + key)
        require(frozen["split"] == {"dev": "development", "heldout": "heldout"}[row["split"]], "source split differs")
        source_record = bound_file(ROOT, frozen["source_record_path"], frozen["source_record_sha256"])
        require(source_record == relative(source.parent, row["text_path"]), "source record path differs")
        doc = read(source_record)
        require(file_sha(source_record) == row["json_sha256"] and hashlib.sha256(doc["text"].encode()).hexdigest() == row["sha256"],
                "source fragment bytes differ")
        require(len(doc["text"]) == 16384 and len(doc["text"].encode()) == frozen["bytes"], "source fragment size differs")
    dev_ids = {d["source_id"] for d in protocol["documents"] if d["split"] == "development"}
    require(not dev_ids & {d["source_id"] for d in protocol["documents"] if d["split"] == "heldout"}, "source identity crosses split")
    for domain in {d["domain"] for d in manifest["documents"]}:
        ranked = sorted((d for d in manifest["documents"] if d["domain"] == domain),
                        key=lambda d: hashlib.sha256(f"singularity-deployment-transfer-20261019/{domain}/{d['name']}".encode()).hexdigest())
        require(len(ranked) == 12 and [r["split"] for r in ranked] == ["dev"] * 4 + ["heldout"] * 8,
                "deterministic source split differs")
    for name, binding in protocol["models"].items():
        identity = read(bound_file(output, binding["identity_path"], binding["sha256"]))
        require(digest(identity["files"]) == identity["files_manifest_sha256"], "model manifest identity differs")
        require(any(p.endswith(".safetensors") for p in identity["files"]), "safe model weight identity missing")
        require(len(identity["encoded_documents"]) == 36, "model encoding population differs")
        identities[name], encoded[name] = identity, {}
        for index, entry in enumerate(identity["encoded_documents"]):
            record = read(bound_file(output, entry["encoding_path"], entry["encoding_sha256"]))
            require(record["document"] == entry["document"] == index, "encoding coordinate differs")
            require(len(record["token_ids"]) == 513 and digest(record["token_ids"]) == entry["token_ids_sha256"] == record["token_ids_sha256"],
                    "frozen native token identity differs")
            require(all(type(t) is int and t >= 0 for t in record["token_ids"]), "invalid native token identity")
            encoded[name][index] = record
    return protocol, identities, encoded


def load_trace(output, binding):
    path = bound_file(output, binding["path"], binding["sha256"])
    record = read(path)
    rows = []
    for chunk in record["target_chunks"]:
        data = read(bound_file(output, chunk["path"], chunk["sha256"]))
        require(data["target_start"] == len(rows), "target chunks overlap or reorder")
        require(1 <= len(data["rows"]) <= 64, "target chunk size differs")
        rows.extend(data["rows"])
    require(len(rows) == record["targets"] == 512, "target population differs")
    return record, rows


def aggregate(records):
    targets = sum(record["targets"] for record in records)
    return {name: {"loss_sum_nats_hex": math.fsum(float.fromhex(r["arms"][name]["loss_sum_nats_hex"]) for r in records).hex(),
                   "nll_nats_per_token": math.fsum(float.fromhex(r["arms"][name]["loss_sum_nats_hex"]) for r in records) / targets}
            for name in records[0]["arms"]}


def verify_target_rows(rows, token_ids, vocabulary_size):
    require(len(rows) == len(token_ids) - 1, "native target population differs")
    for actual, rebuilt in zip(rows, count_rows(token_ids, vocabulary_size)):
        require(all(actual[key] == value for key, value in rebuilt.items()), "count probability or pretarget feature differs")
    return reconstruct(rows)


def parse_time(value):
    moment = datetime.fromisoformat(value)
    require(moment.tzinfo is not None, "receipt timestamp lacks timezone")
    return moment


def verify_selection(protocol, protocol_sha, development, development_path, selection):
    require(selection["schema"] == "singularity.pretrained-gating-selection/1", "unknown selection receipt")
    require(selection["protocol_sha256"] == protocol_sha
            and selection["development_results_sha256"] == file_sha(development_path), "selection source binding differs")
    candidates = ("neural", *(p["id"] for p in POLICIES))
    losses = {name: development["aggregate"][name] for name in candidates}
    require(selection["development_candidate_losses"] == losses, "selection candidate population differs")
    minimum = min(candidates, key=lambda name: (float.fromhex(losses[name]["loss_sum_nats_hex"]), name))
    require(selection["selected_arm"] == minimum, "selected arm is not development minimum")
    require(selection["heldout_scored_before_selection"] is False and selection["selection_rule"] == protocol["selection"],
            "selection not declared prospective")
    require(parse_time(development["created_at_utc"]) <= parse_time(selection["frozen_at_utc"]), "selection predates development")
    return minimum


def verify_split(output, name, split, protocol, identity, encoded, selection=None):
    directory = output / "models" / name / split
    result_path = directory / "results.json"
    result = read(result_path)
    protocol_sha = file_sha(output / "protocol.json")
    selection_sha = file_sha(output / "models" / name / "selection.json") if split == "heldout" else None
    require(result["schema"] == "singularity.pretrained-gating-results/1" and result["model"] == name and result["split"] == split,
            "result coordinates differ")
    require(result["protocol_sha256"] == protocol_sha and result["selection_sha256"] == selection_sha, "result receipt identity differs")
    require(result["environment"]["dtype"] == identity["dtype"], "result dtype differs")
    for key, value in protocol["execution"].items():
        require(result["environment"][key] == value, "execution contract differs: " + key)
    expected = [d["document"] for d in protocol["documents"] if d["split"] == split]
    require([r["document"] for r in result["documents"]] == expected, "result document population differs")
    require(result["trace_files_sha256"] == {r["path"]: r["sha256"] for r in result["documents"]}, "trace manifest differs")
    records = []
    for binding in result["documents"]:
        record, rows = load_trace(output, binding)
        index = binding["document"]
        source = protocol["documents"][index]
        for key in ("document", "name", "domain", "split"):
            require(record[key] == source[key], "trace document metadata differs: " + key)
        require(record["source_sha256"] == source["sha256"] and record["model"] == name
                and record["token_ids_sha256"] == encoded[index]["token_ids_sha256"]
                and record["protocol_sha256"] == protocol_sha and record["selection_sha256"] == selection_sha,
                "trace frozen identity differs")
        replay = verify_target_rows(rows, encoded[index]["token_ids"], result["vocabulary_size"])
        require(digest(replay) == record["replay_sha256"], "expanded posterior/loss commitment differs")
        for key, value in replay.items():
            if key in record:
                require(record[key] == value, "retained replay evidence differs: " + key)
        records.append(record)
    require(aggregate(records) == result["aggregate"], "aggregate loss differs")
    attempts = read(directory / "execution_attempts.json")
    require(bool(attempts) and attempts[-1]["status"] == "completed", "completed execution attempt missing")
    for attempt in attempts:
        require(attempt["status"] in ("aborted", "completed"), "unfinished execution attempt")
        require(attempt["selection_sha256"] == selection_sha, "attempt selection binding differs")
        start, end = parse_time(attempt["started_at_utc"]), parse_time(attempt["ended_at_utc"])
        require(parse_time(protocol["frozen_at_utc"]) <= start <= end, "attempt predates freeze or ends before start")
        if split == "heldout":
            require(selection is not None and parse_time(selection["frozen_at_utc"]) <= start, "heldout execution predates selection")
    require(attempts[-1]["results_sha256"] == file_sha(result_path), "completed attempt result binding differs")
    require(parse_time(attempts[-1]["started_at_utc"]) <= parse_time(result["created_at_utc"])
            <= parse_time(attempts[-1]["ended_at_utc"]), "result timestamp lies outside its completed attempt")
    return result, records


def bootstrap_indices(size, draws=10000):
    """NumPy PCG64(7102026) stream, implemented with Python integers.

    The SeedSequence-derived initial state/increment are fixed below, alongside
    known-answer vectors in the tests. Bounded uint32 draws use Lemire's method;
    no NumPy or producing report code is needed to replay the bootstrap.
    """
    state = 143095656640078439660144695679945508626
    increment = 147064932833925958460441413508850563363
    mask64, mask128 = (1 << 64) - 1, (1 << 128) - 1
    buffered = None
    def uint32():
        nonlocal state, buffered
        if buffered is not None:
            value, buffered = buffered, None
            return value
        state = (state * 47026247687942121848144207491837523525 + increment) & mask128
        shifted, rotation = ((state >> 64) ^ state) & mask64, state >> 122
        raw = ((shifted >> rotation) | (shifted << ((-rotation) & 63))) & mask64
        buffered = raw >> 32
        return raw & ((1 << 32) - 1)
    threshold = ((1 << 32) - size) % size
    for _ in range(draws):
        indices = []
        while len(indices) < size:
            product = uint32() * size
            if (product & ((1 << 32) - 1)) >= threshold:
                indices.append(product >> 32)
        yield indices


def quantile(values, probability):
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def verify_analysis(output, name, protocol, heldout, records, selection):
    report = read(output / "models" / name / "heldout_analysis.json")
    require(report["schema"] == "singularity.pretrained-gating-heldout-analysis/1" and report["model"] == name,
            "analysis coordinates differ")
    require(report["protocol_sha256"] == file_sha(output / "protocol.json")
            and report["selection_sha256"] == file_sha(output / "models" / name / "selection.json")
            and report["heldout_results_sha256"] == file_sha(output / "models" / name / "heldout/results.json")
            and report["selected_arm"] == selection["selected_arm"], "analysis receipt binding differs")
    groups = {"all_domains": records}
    groups.update({domain: [r for r in records if r["domain"] == domain] for domain in sorted({r["domain"] for r in records})})
    require(set(groups) == set(report["comparisons"]), "analysis domain population differs")
    arms = {"primary_selected_minus_neural": selection["selected_arm"],
            "secondary_hierarchy_minus_neural": "hierarchy_protected", "secondary_ungated_minus_neural": "ungated_protected"}
    for domain, members in groups.items():
        require(set(report["comparisons"][domain]) == set(arms), "analysis comparison population differs")
        samples = list(bootstrap_indices(len(members)))
        neural = [float.fromhex(r["arms"]["neural"]["loss_sum_nats_hex"]) for r in members]
        sizes = [r["targets"] for r in members]
        for label, arm in arms.items():
            actual = report["comparisons"][domain][label]
            candidate = [float.fromhex(r["arms"][arm]["loss_sum_nats_hex"]) for r in members]
            differences = [right - left for left, right in zip(neural, candidate)]
            require(actual["arm"] == arm and actual["documents"] == len(members) and actual["targets"] == sum(sizes), "analysis arm/population differs")
            metrics = {"neural_nll_nats_per_token": math.fsum(neural) / sum(sizes),
                       "candidate_nll_nats_per_token": math.fsum(candidate) / sum(sizes),
                       "difference_nats_per_token": math.fsum(differences) / sum(sizes),
                       "loss_reduction_percent": 100 * (math.fsum(neural) - math.fsum(candidate)) / math.fsum(neural)}
            for key, value in metrics.items():
                near(actual[key], value, "analysis metric differs: " + key)
            require(actual["documents_improved"] == sum(d < -1e-10 for d in differences)
                    and actual["documents_worse"] == sum(d > 1e-10 for d in differences)
                    and actual["documents_numerically_tied"] == sum(abs(d) <= 1e-10 for d in differences), "analysis document outcomes differ")
            require(actual["bootstrap_draws"] == 10000 and actual["bootstrap_seed"] == 7102026
                    and actual["document_tie_allowance_nats"] == 1e-10, "bootstrap contract differs")
            boot = [math.fsum(differences[i] for i in draw) / sum(sizes[i] for i in draw) for draw in samples]
            interval = actual["descriptive_paired_document_bootstrap_95_interval"]
            require(isinstance(interval, list) and len(interval) == 2, "bootstrap interval must have two endpoints")
            for got, wanted in zip(interval, (quantile(boot, .025), quantile(boot, .975))):
                near(got, wanted, "descriptive bootstrap interval differs")
    diagnostics = report["all_policy_diagnostics_never_used_for_selection"]
    require(set(diagnostics) == {p["id"] for p in POLICIES}, "diagnostic policy population differs")
    for name, actual in diagnostics.items():
        require(actual["loss_sum_nats_hex"] == heldout["aggregate"][name]["loss_sum_nats_hex"], "diagnostic loss differs")
        near(actual["nll_nats_per_token"], heldout["aggregate"][name]["nll_nats_per_token"], "diagnostic NLL differs")
        require(actual["active_targets"] == sum(r["gate_active_targets"][name] for r in records), "diagnostic activity differs")
        near(actual["raw_unprotected_policy_nll_nats_per_token"],
             math.fsum(float.fromhex(r["raw_gate_loss_sum_nats_hex"][name]) for r in records) / sum(r["targets"] for r in records), "raw diagnostic loss differs")
    require(report["protection_is_not_improvement"] is True, "analysis conflates guarantee with improvement")
    near(report["neural_extra_loss_ceiling_nats_per_document"], CEILING, "analysis ceiling differs")


def verify_study(output=DEFAULT, allow_incomplete=False, models=None):
    output = Path(output).resolve()
    protocol, identities, encoded = check_protocol(output)
    names = list(models) if models else sorted(identities)
    require(set(names) <= set(identities), "unknown model selection")
    completed, targets = [], 0
    for name in names:
        reports, records = {}, {}
        selection_path = output / "models" / name / "selection.json"
        selection = read(selection_path) if selection_path.exists() else None
        for split in ("development", "heldout"):
            path = output / "models" / name / split / "results.json"
            if not path.exists() and allow_incomplete:
                continue
            require(path.exists(), "required split result missing: " + name + "/" + split)
            if split == "heldout":
                require(selection is not None and "development" in reports, "heldout has no frozen development selection")
            result, rows = verify_split(output, name, split, protocol, identities[name], encoded[name], selection)
            reports[split], records[split] = result, rows
            targets += sum(r["targets"] for r in rows)
            completed.append(name + "/" + split)
        if selection is not None:
            require("development" in reports, "selection has no completed development source")
            require(selection["model"] == name, "selection model differs")
            verify_selection(protocol, file_sha(output / "protocol.json"), reports["development"],
                             output / "models" / name / "development/results.json", selection)
            development_attempts = read(output / "models" / name / "development/execution_attempts.json")
            require(parse_time(development_attempts[-1]["ended_at_utc"]) <= parse_time(selection["frozen_at_utc"]),
                    "selection predates completed development attempt")
        if "heldout" in reports:
            analysis = output / "models" / name / "heldout_analysis.json"
            require(analysis.exists() or allow_incomplete, "required heldout analysis missing")
            if analysis.exists():
                verify_analysis(output, name, protocol, reports["heldout"], records["heldout"], selection)
    return {"verified": True, "frozen_models": len(identities), "completed_splits": completed,
            "verified_targets": targets, "documents_per_model": len(protocol["documents"]), "allow_incomplete": allow_incomplete}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT)
    parser.add_argument("--allow-incomplete", action="store_true")
    parser.add_argument("--model", action="append")
    args = parser.parse_args()
    print(json.dumps(verify_study(args.output, args.allow_incomplete, args.model), sort_keys=True))


if __name__ == "__main__":
    main()
