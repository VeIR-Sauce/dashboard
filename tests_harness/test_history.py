from __future__ import annotations

import copy
from collections import Counter
import gzip
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock
import urllib.error
import zipfile

from test_suite import registry_fixture, report_fixture
from veir_suite.github_history import GitHub, find_artifact, restore_archive
from veir_suite.history import record_receipt, read_all_history
from veir_suite.measurement import measurement_cohort
from veir_suite.model import InvalidData, digest, read_json
from veir_suite.native import native_completion, validate_native
from veir_suite.runner import validate_report
from veir_suite.site import build_site
from scripts.measurement_gate import gate as contract_gate
from scripts.native_gate import gate as native_gate


def native_fixture(identifier="native-unit"):
    manifest = {"lit": [{"path": "Test/a.mlir", "sha256": "fixture"}],
                "lean_modules": [{"path": "UnitTest.lean", "sha256": "fixture"}],
                "test_support": [{"path": "Test/lit.cfg.py", "sha256": "fixture"}]}
    return {"schema_version": 2, "kind": "veir-native", "id": identifier,
            "started_at": "2026-01-01T00:00:00Z", "finished_at": "2026-01-01T00:00:01Z",
            "manifest": manifest, "manifest_sha256": digest(manifest),
            "harness_sha256": "native-harness", "profile": {"label": "unit"},
            "source": {"commit": "abc", "dirty": False}, "tools": {},
            "source_unchanged_during_run": True, "harness_unchanged_during_run": True,
            "binaries_unchanged_during_tests": True, "tools_unchanged_during_run": True,
            "commands": [{"kind": "exit", "exit_code": 0} for _ in range(4)],
            "tests": [{"name": "VeIR :: a.mlir", "code": "PASS"}],
            "counts": {"PASS": 1}, "complete": True}


def zip_blob(entries):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, payload in entries:
            archive.writestr(name, payload)
    return stream.getvalue()


class RefactorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.registry = registry_fixture(self.root)
        self.report = report_fixture(self.registry)
        self.history = self.root / "history"

    def v2(self, registry):
        report = report_fixture(registry)
        report["schema_version"] = 2
        report["cohort"] = measurement_cohort(registry, report["harness_sha256"], report["profile"])
        return report

    def test_administrative_edits_keep_cohort_but_preserve_full_receipt_hash(self):
        before = self.v2(self.registry)
        changed = copy.deepcopy(self.registry)
        changed["name"] = "Renamed tracker"
        changed["scopes"][0]["title"] = "A different display title"
        changed["requirements"][0].update(title="A better title", owner="Review team",
            priority="P1", next_action="Discuss on Tuesday", decision_record="Discussion link")
        after = self.v2(changed)
        self.assertEqual(before["cohort"], after["cohort"])
        self.assertNotEqual(before["registry_sha256"], after["registry_sha256"])
        validate_report(after)
        after["registry_sha256"] = before["registry_sha256"]
        with self.assertRaises(InvalidData):
            validate_report(after)

    def test_acceptance_criteria_and_unknown_settings_change_cohort(self):
        baseline = self.v2(self.registry)["cohort"]
        for change in [
            lambda r: r["requirements"][0].update(contract="Different observable result"),
            lambda r: r["requirements"][0].update(state="needs_decision"),
            lambda r: r["tests"][0].update(expect="reject"),
            lambda r: r["tests"][0].update(input_sha256="changed source"),
            lambda r: r.update(new_acceptance_setting=True),
        ]:
            with self.subTest(change=change):
                changed = copy.deepcopy(self.registry)
                change(changed)
                self.assertNotEqual(baseline, self.v2(changed)["cohort"])

    def test_legacy_cohort_is_unchanged_and_not_joined_to_v2(self):
        validate_report(self.report)
        self.assertEqual(self.report["cohort"],
            measurement_cohort(self.registry, "test-harness", {"label": "unit-test-only"}, version=1))
        self.assertNotEqual(self.report["cohort"], self.v2(self.registry)["cohort"])

    def test_record_is_idempotent_and_conflicts_preserve_original(self):
        source = self.root / "report.json"
        source.write_text(json.dumps(self.report))
        destination = record_receipt(source, self.history)
        before = destination.stat().st_mtime_ns
        self.assertEqual(record_receipt(source, self.history), destination)
        self.assertEqual(before, destination.stat().st_mtime_ns)
        self.report["started_at"] = "2025-01-01T00:00:00Z"
        source.write_text(json.dumps(self.report))
        with self.assertRaisesRegex(InvalidData, "different receipt"):
            record_receipt(source, self.history)
        self.assertEqual(read_json(destination)["started_at"], "2026-01-01T00:00:00Z")

    def test_record_rejects_cross_kind_and_symlink_escape(self):
        source = self.root / "report.json"
        source.write_text(json.dumps(self.report))
        directory = self.history / self.report["id"]
        directory.mkdir(parents=True)
        (directory / "native.json").write_text(json.dumps(native_fixture(self.report["id"])))
        with self.assertRaisesRegex(InvalidData, "different kind"):
            record_receipt(source, self.history)
        (directory / "native.json").unlink()
        directory.rmdir()
        directory.symlink_to(self.root, target_is_directory=True)
        with self.assertRaisesRegex(InvalidData, "symlink"):
            record_receipt(source, self.history)

    def test_archive_validation_finishes_before_any_receipt_is_written(self):
        payload = json.dumps(self.report)
        good = (self.report["id"] + "/report.json", payload)
        for bad in [("../escape/report.json", payload),
                    ("different-id/report.json", payload),
                    ("bad/report.json", '{"schema_version":1,"schema_version":2}'),
                    ("bad/notes.txt", "not evidence")]:
            with self.subTest(bad=bad):
                with self.assertRaises((InvalidData, KeyError)):
                    restore_archive(zip_blob([good, bad]), self.history)
                self.assertFalse(self.history.exists())
        self.assertEqual(restore_archive(zip_blob([good]), self.history), 1)
        target = self.history / good[0]
        before = target.stat().st_mtime_ns
        self.assertEqual(restore_archive(zip_blob([good]), self.history), 1)
        self.assertEqual(before, target.stat().st_mtime_ns)

    def test_archive_rejects_existing_conflict_before_writing_new_receipt(self):
        original = self.root / "original.json"
        original.write_text(json.dumps(self.report))
        record_receipt(original, self.history)
        changed = copy.deepcopy(self.report)
        changed["started_at"] = "2025-01-01T00:00:00Z"
        new = copy.deepcopy(self.report)
        new["id"] = "another"
        with self.assertRaisesRegex(InvalidData, "Conflicting"):
            restore_archive(zip_blob([
                ("another/report.json", json.dumps(new)),
                (self.report["id"] + "/report.json", json.dumps(changed))
            ]), self.history)
        self.assertFalse((self.history / "another").exists())

    def test_history_rejects_same_id_across_receipt_kinds(self):
        for folder, filename, report in [("a", "report.json", self.report),
                ("b", "native.json", native_fixture(self.report["id"]))]:
            directory = self.history / folder
            directory.mkdir(parents=True)
            (directory / filename).write_text(json.dumps(report))
        with self.assertRaisesRegex(InvalidData, "reuse"):
            read_all_history(self.history)

    def test_native_completeness_checks_commands_manifest_and_provenance(self):
        validate_native(native_fixture())
        mutations = [
            lambda r: r["commands"].pop(),
            lambda r: r["commands"][0].update(exit_code=1),
            lambda r: r["commands"][3].update(kind="timeout"),
            lambda r: r["tests"].clear(),
            lambda r: r.update(harness_unchanged_during_run=False),
            lambda r: r.update(binaries_unchanged_during_tests=False),
            lambda r: r.update(tools_unchanged_during_run=False),
            lambda r: r["tests"][0].update(code="UNRESOLVED"),
        ]
        for mutate in mutations:
            report = native_fixture()
            mutate(report)
            report["counts"] = dict(Counter(test["code"] for test in report["tests"]))
            with self.subTest(mutate=mutate):
                self.assertFalse(native_completion(report))
                with self.assertRaisesRegex(InvalidData, "completion"):
                    validate_native(report)
                report["complete"] = False
                validate_native(report)

    def test_native_rejects_duplicate_tests_and_changed_manifest(self):
        report = native_fixture()
        report["tests"] *= 2
        report["counts"] = {"PASS": 2}
        with self.assertRaisesRegex(InvalidData, "Invalid native"):
            validate_native(report)
        report = native_fixture()
        report["manifest"]["lit"][0]["sha256"] = "changed"
        with self.assertRaisesRegex(InvalidData, "manifest digest"):
            validate_native(report)

    def test_native_legacy_evidence_remains_readable(self):
        report = native_fixture()
        report["schema_version"] = 1
        for key in ["harness_unchanged_during_run", "binaries_unchanged_during_tests", "tools_unchanged_during_run"]:
            del report[key]
        validate_native(report)

    def test_gates_ignore_future_incomplete_and_incompatible_baselines(self):
        previous = copy.deepcopy(self.report)
        previous.update(id="before", finished_at="2025-01-01T00:00:00Z")
        current = report_fixture(self.registry, "FAIL")
        self.assertTrue(contract_gate(current, []))
        with self.assertRaisesRegex(InvalidData, "Regressed"):
            contract_gate(current, [previous])
        previous["finished_at"] = "2027-01-01T00:00:00Z"
        self.assertTrue(contract_gate(current, [previous]))
        current["complete"] = False
        with self.assertRaises(InvalidData):
            contract_gate(current, [])

        before, after = native_fixture("before"), native_fixture("after")
        after["finished_at"] = "2026-01-02T00:00:01Z"
        after["tests"][0]["code"] = "FAIL"
        after["counts"] = {"FAIL": 1}
        after["commands"][-1]["exit_code"] = 1
        with self.assertRaisesRegex(InvalidData, "regressions"):
            native_gate(after, [before])
        before["harness_sha256"] = "other harness"
        self.assertTrue(native_gate(after, [before]))

    def test_site_compacts_history_and_escapes_embedded_data(self):
        requirement = self.registry["requirements"][0]
        requirement.update(title="=SUM(1,2)", contract="</script><script>window.injected=1</script>",
                           operations=[], source_groups=[])
        requirements = self.root / "requirements"
        (requirements / "sources").mkdir(parents=True)
        for filename, payload in [("registry.json", self.registry), ("catalog.json", {}),
                                  ("sources/mathieu.json", {})]:
            (requirements / filename).write_text(json.dumps(payload))
        (self.root / "web").mkdir()
        (self.root / "web/index.html").write_text('<script id="data">__DATA__</script>')
        for name in ["model.js", "app.js", "style.css"]:
            (self.root / "web" / name).write_text("")
        for index in range(1, 4):
            contract = report_fixture(self.registry, "ENV_ERROR" if index == 3 else "PASS")
            contract.update(id=f"run{index}", finished_at=f"2026-01-0{index}T00:00:00Z",
                            sources={"veir": {"commit": "abc", "dirty": False}})
            native = native_fixture(f"native{index}")
            native["finished_at"] = contract["finished_at"]
            for report, filename in [(contract, "report.json"), (native, "native.json")]:
                directory = self.history / report["id"]
                directory.mkdir(parents=True)
                (directory / filename).write_text(json.dumps(report))
        output = self.root / "site"
        build_site(self.root, self.history, output)
        html = (output / "index.html").read_text()
        self.assertNotIn("</script><script>", html)
        embedded = json.loads(html.removeprefix('<script id="data">').removesuffix("</script>"))
        self.assertNotIn("manifest", embedded["native"][0])
        self.assertNotIn("results", embedded["reports"][0])
        self.assertEqual(embedded["reports"][1]["results"][0]["status"], "PASS")
        self.assertEqual(embedded["reports"][2]["results"][0]["status"], "ENV_ERROR")
        self.assertEqual(json.loads(gzip.decompress((output / "data/run1.json.gz").read_bytes()))["id"], "run1")
        self.assertTrue((output / "data/native1.json.gz").is_file())
        self.assertIn("'=SUM", (output / "data/requirements.csv").read_text())


class GitHubHistoryTests(unittest.TestCase):
    def artifact(self, **kwargs):
        return {"id": 8, "expired": False, "created_at": "2026-01-01T00:00:00Z",
                "workflow_run": {"id": 7, "head_branch": "main", "head_repository_id": 42, "head_sha": "abc"},
                **kwargs}

    def provenance(self, event="push"):
        return {"event": event, "head_branch": "main", "repository": {"id": 42},
                "head_repository": {"id": 42}, "head_sha": "abc", "status": "completed"}

    def test_only_completed_same_repository_default_branch_non_pr_events_are_trusted(self):
        for event in ["pull_request", "pull_request_target", "push", "schedule", "workflow_dispatch"]:
            api = Mock(side_effect=[{"artifacts": [self.artifact()]}, self.provenance(event)])
            result = find_artifact(api, "owner/repo", 42, "main", 99)
            self.assertEqual(result is not None, event in {"push", "schedule", "workflow_dispatch"})
        for key, value in [("head_sha", "different"), ("head_repository", {"id": 9}),
                           ("repository", {"id": 9}), ("head_branch", "topic"), ("status", "in_progress")]:
            run = self.provenance()
            run[key] = value
            api = Mock(side_effect=[{"artifacts": [self.artifact()]}, run])
            self.assertIsNone(find_artifact(api, "owner/repo", 42, "main", 99))

    def test_full_pagination_limit_is_an_error_not_a_new_baseline(self):
        api = Mock(return_value={"artifacts": [self.artifact(expired=True)] * 100})
        with self.assertRaisesRegex(InvalidData, "page limit"):
            find_artifact(api, "owner/repo", 42, "main", 99, max_pages=2)
        self.assertEqual(api.call_count, 2)

    def test_redirect_never_forwards_token_and_responses_are_bounded(self):
        url = "https://api.github.com/repos/owner/repo/actions/artifacts/8/zip"
        opener = Mock()
        opener.open.side_effect = [
            urllib.error.HTTPError(url, 302, "redirect", {"Location": "https://blob.example/archive"}, None),
            io.BytesIO(b"zip"),
        ]
        self.assertEqual(GitHub("unit-test-token", opener).archive(url), b"zip")
        first, second = [call.args[0] for call in opener.open.call_args_list]
        self.assertEqual(first.get_header("Authorization"), "Bearer unit-test-token")
        self.assertIsNone(second.get_header("Authorization"))
        with self.assertRaisesRegex(InvalidData, "outside"):
            GitHub("unit-test-token", opener).archive("https://blob.example/archive")
        opener.open.side_effect = [io.BytesIO(b"12345")]
        with self.assertRaisesRegex(InvalidData, "transfer budget"):
            GitHub("unit-test-token", opener).get(url, 4)
