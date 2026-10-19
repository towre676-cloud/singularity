"""Focused contract tests for the read-only NX36 inspection CLI (stdlib only)."""
from __future__ import annotations

from contextlib import redirect_stdout, redirect_stderr
from copy import deepcopy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location("nx36_handoff_tool", Path(__file__).with_name("handoff.py"))
TOOL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TOOL)


class HandoffToolTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repository = Path(self.temp.name) / "repository"
        self.root = self.repository / "handoff" / "nx36"
        (self.root / "packets").mkdir(parents=True)
        (self.repository / "src" / "singularity").mkdir(parents=True)
        (self.repository / "src" / "singularity" / "__init__.py").write_text('__version__ = "0.4.0"\n')
        (self.repository / "README.md").write_text("Evidence fixture.\n")
        self.data = {"schema": TOOL.SCHEMA, "tracks": []}
        for number in range(1, 37):
            tag = f"NX{number:02d}"
            dependencies = ["NX01"] if number == 2 else []
            track = {"id": tag, "title": f"Track {number}", "status": "proposed",
                     "depends_on": dependencies, "packet": f"packets/{tag}.md",
                     "priority": "high", "summary": "Proposed bounded work.",
                     "existing_sources": ["src/singularity/__init__.py"],
                     "proposed_sources": [f"src/singularity/nx{number:02d}.py"],
                     "acceptance": ["Independent evidence."], "pushes": []}
            for suffix in "ABC":
                deps = ([f"{dep}-C" for dep in dependencies] if suffix == "A"
                        else [f"{tag}-A"] if suffix == "B" else [f"{tag}-B"])
                track["pushes"].append({"id": f"{tag}-{suffix}", "title": f"Unit {suffix}",
                                        "status": "proposed", "depends_on": deps,
                                        "acceptance": ["Check the declared contract."]})
            self.data["tracks"].append(track)
            (self.root / track["packet"]).write_text(f"# {tag}\nProposed packet.\n")
        self.save()

    def save(self):
        (self.root / "roadmap.json").write_text(json.dumps(self.data))

    def evidence(self):
        return {"summary": "Fixture only; not a mathematical claim.",
                "artifacts": ["README.md"],
                "checks": [{"command": "python harmless_fixture.py", "exit_code": 0,
                            "scope": "fixture contract"}],
                "commit": "abcdef012345", "math_status": "exact_finite"}

    def complete(self, track_number, suffix):
        track = self.data["tracks"][track_number - 1]
        unit = track["pushes"]["ABC".index(suffix)]
        unit["status"] = "complete"
        unit["evidence"] = self.evidence()
        if all(item["status"] == "complete" for item in track["pushes"]):
            track["status"] = "complete"

    def invoke(self, *args):
        output, error = io.StringIO(), io.StringIO()
        with redirect_stdout(output), redirect_stderr(error):
            code = TOOL.main(["--root", str(self.root), *args])
        return code, json.loads(output.getvalue()), error.getvalue()

    def test_initial_36_tracks_108_units_and_packets_validate(self):
        self.assertEqual(TOOL.validate_roadmap(self.data, self.root), [])
        code, result, _ = self.invoke("verify")
        self.assertEqual(code, 0)
        self.assertEqual((result["tracks"], result["units"], result["packets"]), (36, 108, 36))
        self.assertIn("not proof truth", result["verification_scope"])

    def test_readiness_respects_track_and_unit_dependency_chain(self):
        initial = [unit["id"] for unit in TOOL.ready_units(self.data, 3)]
        self.assertEqual(initial, ["NX01-A", "NX03-A", "NX04-A"])
        self.complete(1, "A")
        ready = [unit["id"] for unit in TOOL.ready_units(self.data, 108)]
        self.assertIn("NX01-B", ready)
        self.assertNotIn("NX01-C", ready)
        self.assertNotIn("NX02-A", ready)
        self.complete(1, "B")
        self.complete(1, "C")
        self.assertEqual(TOOL.validate_roadmap(self.data, self.root), [])
        ready = [unit["id"] for unit in TOOL.ready_units(self.data, 108)]
        self.assertIn("NX02-A", ready)
        self.assertNotIn("NX01-A", ready)

    def test_blocked_track_and_unit_omitted_in_progress_first(self):
        self.data["tracks"][0]["status"] = "blocked"
        self.data["tracks"][2]["pushes"][0]["status"] = "blocked"
        self.data["tracks"][4]["pushes"][0]["status"] = "in_progress"
        ready = [unit["id"] for unit in TOOL.ready_units(self.data, 3)]
        self.assertEqual(ready, ["NX05-A", "NX04-A", "NX06-A"])

    def test_forged_complete_without_evidence_rejected(self):
        self.data["tracks"][0]["pushes"][0]["status"] = "complete"
        self.assertTrue(any("complete requires evidence" in error
                            for error in TOOL.validate_roadmap(self.data, self.root)))

    def test_completed_unit_requires_completed_dependencies(self):
        self.complete(2, "A")
        errors = TOOL.validate_roadmap(self.data, self.root)
        self.assertTrue(any("dependency NX01-C is not complete" in error for error in errors))

    def test_track_completion_is_exactly_three_completed_units(self):
        self.data["tracks"][0]["status"] = "complete"
        self.assertTrue(any("track complete iff" in error
                            for error in TOOL.validate_roadmap(self.data, self.root)))
        self.data["tracks"][0]["status"] = "proposed"
        for suffix in "ABC":
            self.complete(1, suffix)
        self.data["tracks"][0]["status"] = "in_progress"
        self.assertTrue(any("track complete iff" in error
                            for error in TOOL.validate_roadmap(self.data, self.root)))

    def test_evidence_checks_and_commit_contract(self):
        self.complete(1, "A")
        unit = self.data["tracks"][0]["pushes"][0]
        unit["evidence"]["checks"][0]["exit_code"] = False
        unit["evidence"]["commit"] = "not-a-commit"
        unit["evidence"]["math_status"] = "universal_physical_truth"
        errors = TOOL.validate_roadmap(self.data, self.root)
        self.assertTrue(any("integer exit_code 0" in error for error in errors))
        self.assertTrue(any("hexadecimal commit" in error for error in errors))
        self.assertTrue(any("math_status" in error for error in errors))

    def test_evidence_missing_or_traversing_artifacts_rejected(self):
        self.complete(1, "A")
        unit = self.data["tracks"][0]["pushes"][0]
        unit["evidence"]["artifacts"] = ["missing.txt", "../outside.txt"]
        errors = TOOL.validate_roadmap(self.data, self.root)
        self.assertTrue(any("missing evidence artifact" in error for error in errors))
        self.assertTrue(any("invalid evidence artifact" in error for error in errors))

    def test_cycle_detected_in_both_track_and_unit_graphs(self):
        self.data["tracks"][0]["depends_on"] = ["NX02"]
        self.data["tracks"][0]["pushes"][0]["depends_on"] = ["NX02-C"]
        errors = TOOL.validate_roadmap(self.data, self.root)
        self.assertTrue(any("track dependency cycle" in error for error in errors))
        self.assertTrue(any("unit dependency cycle" in error for error in errors))

    def test_unknown_and_dropped_dependencies_rejected(self):
        self.data["tracks"][0]["pushes"][1]["depends_on"] = ["NX99-C"]
        errors = TOOL.validate_roadmap(self.data, self.root)
        self.assertTrue(any("dependency contract requires" in error for error in errors))
        self.assertTrue(any("unknown unit dependency" in error for error in errors))

    def test_missing_packet_and_duplicate_track_rejected(self):
        (self.root / "packets" / "NX09.md").unlink()
        self.data["tracks"][1]["id"] = "NX01"
        errors = TOOL.validate_roadmap(self.data, self.root)
        self.assertTrue(any("each exactly once" in error for error in errors))
        self.assertTrue(any("unreadable packet" in error for error in errors))

    def test_packet_escape_is_rejected(self):
        self.data["tracks"][0]["packet"] = "../../README.md"
        self.assertTrue(any("packet must be" in error
                            for error in TOOL.validate_roadmap(self.data, self.root)))

    def test_unknown_status_rejected(self):
        self.data["tracks"][0]["pushes"][0]["status"] = "tests_passed_so_complete"
        self.assertTrue(any("invalid status" in error
                            for error in TOOL.validate_roadmap(self.data, self.root)))

    def test_malformed_container_status_is_a_validation_error(self):
        self.data["tracks"][0]["status"] = ["complete"]
        self.data["tracks"][0]["pushes"][0]["status"] = {"complete": True}
        errors = TOOL.validate_roadmap(self.data, self.root)
        self.assertEqual(sum("invalid status" in error for error in errors), 2)

    def test_cli_status_show_next_and_root_after_command(self):
        code, report, _ = self.invoke("status")
        self.assertEqual(code, 0)
        self.assertEqual(report["unit_status"], {"proposed": 108})
        code, report, _ = self.invoke("show", "NX02-A")
        self.assertEqual(report["record"]["depends_on"], ["NX01-C"])
        code, report, _ = self.invoke("next", "--limit", "1")
        self.assertEqual([unit["id"] for unit in report["units"]], ["NX01-A"])
        output = io.StringIO()
        with redirect_stdout(output):
            code = TOOL.main(["verify", "--root", str(self.root)])
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(output.getvalue())["ok"])

    def test_cli_unknown_identifier_and_bad_limit(self):
        self.assertEqual(self.invoke("show", "NX99")[0], 2)
        self.assertEqual(self.invoke("next", "--limit", "0")[0], 2)

    def test_duplicate_json_keys_rejected(self):
        (self.root / "roadmap.json").write_text('{"schema":"x","schema":"y","tracks":[]}')
        code, result, _ = self.invoke("verify")
        self.assertEqual(code, 1)
        self.assertIn("duplicate JSON key", result["errors"][0])

    def test_preflight_case_insensitive_companions_and_advisory_missing(self):
        companion = self.root / "companion_sources" / "dynacomp" / "src" / "dynacomp"
        companion.mkdir(parents=True)
        (companion / "stability.py").write_text("# source fixture only\n")
        self.data["tracks"][0]["existing_sources"] += [
            "dYnAcOmP:src/dynacomp/stability.py", "PerfectPower:missing.py", "/old/workspace/source.py"]
        self.save()
        code, result, _ = self.invoke("preflight")
        self.assertEqual(code, 0)
        self.assertEqual(result["baseline_import"], "passed")
        self.assertEqual(result["version"], "0.4.0")
        self.assertEqual(result["existing_source_references"], 2)
        self.assertFalse(result["expensive_checks_run"])
        self.assertGreaterEqual(len(result["warnings"]), 2)

    def test_preflight_does_not_execute_recorded_check(self):
        self.complete(1, "A")
        marker = self.repository / "must_not_exist"
        self.data["tracks"][0]["pushes"][0]["evidence"]["checks"][0]["command"] = (
            f"python -c \"open({str(marker)!r},'w').write('bad')\"")
        self.save()
        code, result, _ = self.invoke("preflight")
        self.assertEqual(code, 0)
        self.assertFalse(marker.exists())
        self.assertIn("not proof truth", result["verification_scope"])

    def test_source_only_preflight_is_explicitly_unavailable(self):
        (self.repository / "src" / "singularity" / "__init__.py").unlink()
        self.save()
        code, report, _ = self.invoke("preflight")
        self.assertEqual(code, 0)
        self.assertEqual(report["baseline_import"], "unavailable")
        self.assertIsNone(report["version"])


if __name__ == "__main__":
    unittest.main()
