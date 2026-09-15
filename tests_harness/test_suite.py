from __future__ import annotations
import copy
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import tempfile
import unittest
from unittest.mock import patch

from veir_suite.checks import CheckFailure, check, parse_interpreter_json, parse_reference_result, reference_wrapper
from veir_suite.model import InvalidData, digest, load_registry, read_json, safe_path, summarize
from veir_suite.process import execute
from veir_suite.runner import regressions, validate_report
from veir_suite.site import read_history


def int_result(width=128, value=(1 << 100) + 257):
    return {"schema_version": 1, "outcome": "ok", "results": [{"kind": "int", "width": width, "value": str(value)}]}


def registry_fixture(root):
    source = '"builtin.module"() ({}) : () -> ()\n'
    (root / "input.mlir").write_text(source)
    registry = {"schema_version": 1, "scopes": [{"id": "llvm", "title": "LLVM"}],
                "requirements": [{"id": "req", "title": "A contract", "scope": "llvm", "stage": "verification", "state": "specified", "contract": "Accept this input", "test_ids": ["test"]}],
                "tests": [{"id": "test", "kind": "verify", "input": "input.mlir", "input_sha256": hashlib.sha256(source.encode()).hexdigest(), "expect": "accept"}]}
    return registry


def report_fixture(registry, status="PASS"):
    results = [{"id": "test", "status": status, "input_sha256": registry["tests"][0]["input_sha256"]}]
    report = {"schema_version": 1, "id": "unit-test-only", "started_at": "2026-01-01T00:00:00Z", "finished_at": "2026-01-01T00:00:01Z", "registry": registry,
              "registry_sha256": digest(registry), "harness_sha256": "test-harness", "profile": {"label": "unit-test-only"},
              "source_unchanged_during_run": True, "complete": status in {"PASS", "FAIL", "MISSING_CAPABILITY"},
              "results": results, "summary": summarize(registry, results)}
    report["cohort"] = digest({"registry": registry, "harness": report["harness_sha256"], "profile": report["profile"]})
    return report


class ProtocolTests(unittest.TestCase):
    def test_arbitrary_width_string_is_lossless(self):
        expected = int_result()
        self.assertEqual(parse_interpreter_json(json.dumps(expected)), expected)

    def test_all_runtime_kinds_and_multiple_values(self):
        result = int_result()
        result["results"] += [{"kind": "int", "width": 32, "poison": True}, {"kind": "byte", "width": 16, "value": "17", "poison_mask": "65280"},
                              {"kind": "float", "type": "f32", "width": 32, "bits": "2147483648"}, {"kind": "address", "width": 64, "value": "123"},
                              {"kind": "register", "width": 64, "value": "18446744073709551615"}, {"kind": "felt", "type": "babybear", "value": "42"}]
        self.assertEqual(parse_interpreter_json(json.dumps(result)), result)

    def test_invalid_payloads_fail_closed(self):
        cases = []
        for value in [{"kind": "int", "width": 8, "value": 255}, {"kind": "int", "width": 8, "value": "256"},
                      {"kind": "int", "width": 8, "value": "-1"}, {"kind": "int", "width": 8, "poison": False},
                      {"kind": "byte", "width": 8, "value": "1"}, {"kind": "float", "width": 32, "bits": "0"},
                      {"kind": "register", "width": 32, "value": "1"}, {"kind": "felt", "type": "f", "value": "-1"}]:
            result = int_result(); result["results"] = [value]; cases.append(json.dumps(result))
        cases += ['{"schema_version":1,"schema_version":1,"outcome":"ok","results":[]}',
                  '{"schema_version":true,"outcome":"ok","results":[]}',
                  json.dumps(int_result()) + "\nProgram output: 1", "", "[]"]
        for text in cases:
            with self.subTest(text=text), self.assertRaises(CheckFailure):
                parse_interpreter_json(text)

    def test_ub_is_distinct_from_unsupported_and_empty_success(self):
        outcomes = [parse_interpreter_json(json.dumps({"schema_version": 1, "outcome": x, "results": []})) for x in ["ok", "undefined_behavior", "unsupported_interpretation"]]
        self.assertEqual(len({x["outcome"] for x in outcomes}), 3)
        invalid = int_result(); invalid["outcome"] = "undefined_behavior"
        with self.assertRaises(CheckFailure): parse_interpreter_json(json.dumps(invalid))

    def test_reference_all_bits_not_exit_code(self):
        value = (1 << 100) + 257
        text = f"VEIR-RESULT 128 {value % (1 << 64)} {value >> 64}\n"
        self.assertEqual(parse_reference_result(text, 128), int_result(128, value))
        with self.assertRaises(CheckFailure): parse_reference_result("VEIR-RESULT 128 1\n", 128)
        with self.assertRaises(CheckFailure): parse_reference_result("VEIR-RESULT 8 257\n", 8)
        with self.assertRaises(CheckFailure): parse_reference_result("debug\nVEIR-RESULT 8 1\n", 8)

    def test_wrapper_preserves_original_computation(self):
        source = "define i128 @main() {\n  ret i128 1267650600228229401496703205633\n}\n"
        wrapped = reference_wrapper(source, 128)
        self.assertIn("ret i128 1267650600228229401496703205633", wrapped)
        self.assertIn("lshr i128 %value, 64", wrapped)
        self.assertEqual(wrapped.count("define i32 @main()"), 1)
        with self.assertRaises(CheckFailure): reference_wrapper(source, 64)
        with self.assertRaises(CheckFailure): reference_wrapper(source + "declare i32 @printf(ptr, ...)", 128)


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.registry = registry_fixture(self.root)
        (self.root / "requirements").mkdir()

    def load(self):
        (self.root / "requirements/registry.json").write_text(json.dumps(self.registry))
        return load_registry(self.root)

    def test_valid_manifest(self): self.assertEqual(self.load(), self.registry)

    def test_fixture_drift_is_not_accepted(self):
        (self.root / "input.mlir").write_text("changed")
        with self.assertRaisesRegex(InvalidData, "digest mismatch"): self.load()

    def test_duplicate_ids_are_not_merged(self):
        self.registry["tests"].append(copy.deepcopy(self.registry["tests"][0]))
        with self.assertRaisesRegex(InvalidData, "Duplicate"): self.load()

    def test_missing_negative_diagnostic_rejected(self):
        self.registry["tests"][0]["expect"] = "reject"
        with self.assertRaisesRegex(InvalidData, "diagnostic"): self.load()

    def test_paths_cannot_escape_through_parent_or_symlink(self):
        for relative in ["../outside", "/etc/passwd"]:
            with self.assertRaises(InvalidData): safe_path(self.root, relative)
        (self.root / "link").symlink_to("/etc")
        with self.assertRaises(InvalidData): safe_path(self.root, "link/passwd")

    def test_missing_and_duplicate_results_rejected(self):
        with self.assertRaises(InvalidData): summarize(self.registry, [])
        with self.assertRaises(InvalidData): summarize(self.registry, [{"id": "test", "status": "PASS"}] * 2)

    def test_no_vacuous_coverage_for_empty_contract(self):
        self.registry["requirements"][0].update(state="needs_decision", test_ids=[])
        self.registry["tests"] = []
        summary = summarize(self.registry, [])
        self.assertEqual((summary["covered"], summary["satisfied"], summary["needs_decision"]), (0, 0, 1))

    def test_product_failure_measures_coverage_but_not_conformance(self):
        summary = summarize(self.registry, [{"id": "test", "status": "FAIL"}])
        self.assertEqual((summary["coverage_remaining"], summary["conformance_remaining"]), (0, 1))

    def test_missing_oracle_is_not_a_completed_measurement(self):
        report = report_fixture(self.registry, "ENV_ERROR")
        self.assertFalse(validate_report(report)["complete"])
        report["complete"] = True
        with self.assertRaisesRegex(InvalidData, "completion"): validate_report(report)

    def test_tampered_summary_and_stale_fixture_rejected(self):
        report = report_fixture(self.registry)
        report["summary"]["satisfied"] = 100
        with self.assertRaises(InvalidData): validate_report(report)
        report = report_fixture(self.registry)
        report["results"][0]["input_sha256"] = "wrong"
        with self.assertRaisesRegex(InvalidData, "stale"): validate_report(report)

    def test_regressions_require_compatible_complete_cohorts(self):
        before, after = report_fixture(self.registry), report_fixture(self.registry, "FAIL")
        self.assertEqual(regressions(before, after), ["test"])
        after["profile"] = {"label": "different"}
        after["cohort"] = digest({"registry": self.registry, "harness": after["harness_sha256"], "profile": after["profile"]})
        with self.assertRaisesRegex(InvalidData, "different contracts"): regressions(before, after)

    def test_duplicate_history_id_rejected(self):
        for folder in ["a", "b"]:
            (self.root / folder).mkdir()
            (self.root / folder / "report.json").write_text(json.dumps(report_fixture(self.registry)))
        with self.assertRaisesRegex(InvalidData, "duplicate run"): read_history(self.root)

    def test_duplicate_json_keys_rejected(self):
        path = self.root / "bad.json"; path.write_text('{"complete":false,"complete":true}')
        with self.assertRaisesRegex(InvalidData, "Duplicate"): read_json(path)


class ProcessTests(unittest.TestCase):
    def invoke(self, source, **kwargs):
        return execute([sys.executable, "-c", source], cwd=Path.cwd(), **kwargs)

    def test_separate_streams_and_nonzero_exit(self):
        result = self.invoke('import sys; print("out"); print("error",file=sys.stderr); sys.exit(7)')
        self.assertEqual((result["kind"], result["exit_code"], result["stdout"], result["stderr"]), ("exit", 7, "out\n", "error\n"))

    def test_timeout_even_when_child_closes_pipes(self):
        result = self.invoke("import os,time; os.close(1); os.close(2); time.sleep(10)", timeout=.15)
        self.assertEqual(result["kind"], "timeout")
        self.assertLess(result["seconds"], 2)

    def test_output_is_bounded(self):
        result = self.invoke('import sys; sys.stdout.write("x"*1000000)', output_limit=1024)
        self.assertEqual(result["kind"], "output_limit")
        self.assertLessEqual(len(result["stdout"]) + len(result["stderr"]), 1024)

    def test_signal_is_not_ordinary_negative_rejection(self):
        result = self.invoke("import os,signal; os.kill(os.getpid(),signal.SIGTERM)")
        self.assertEqual((result["kind"], result["exit_code"]), ("crash", -signal.SIGTERM))

    def test_missing_executable_is_environment_error(self):
        result = execute(["/definitely/not/a/tool"], cwd=Path.cwd())
        self.assertEqual(result["kind"], "not_found")


class IndependentOracleTests(unittest.TestCase):
    def test_reference_never_consumes_veir_printing_or_converted_source(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); source = "// ORIGINAL, including its flags\n"
            (root / "input.mlir").write_text(source)
            test = {"id": "independent", "input": "input.mlir", "input_sha256": hashlib.sha256(source.encode()).hexdigest(), "kind": "differential", "result_width": 64}
            commands = []
            def fake(command, **kwargs):
                commands.append(command)
                record = {"command": command, "kind": "exit", "exit_code": 0, "stdout": "", "stderr": "", "seconds": 0}
                if command[0] in {"mlir_opt", "mlir_translate", "veir_interpret"}:
                    self.assertEqual(Path(command[-1]).read_text(), source)
                if command[0] == "mlir_translate": record["stdout"] = "define i64 @main() { ret i64 257 }\n"
                if command[0] == "lli": record["stdout"] = "VEIR-RESULT 64 257\n"
                if command[0] == "veir_interpret": record["stdout"] = json.dumps(int_result(64, 1))
                return record
            with patch("veir_suite.checks.execute", side_effect=fake):
                result = check(test, {k: k for k in ["mlir_opt", "mlir_translate", "lli", "veir_interpret"]}, root, root / "work", 5)
            self.assertEqual(result["status"], "FAIL")  # 257 and 1 have the same exit-status byte.
            self.assertEqual([c[0] for c in commands], ["mlir_opt", "mlir_translate", "lli", "veir_interpret"])

    def test_crashing_verifier_does_not_satisfy_reject_expectation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); (root / "input.mlir").write_text("invalid")
            test = {"id": "negative", "input": "input.mlir", "input_sha256": "unused", "kind": "verify", "expect": "reject", "reference": False, "diagnostics": {"veir": "type"}}
            with patch("veir_suite.checks.execute", return_value={"kind": "crash", "exit_code": -11, "stdout": "", "stderr": "type error", "seconds": 0}):
                result = check(test, {"veir_opt": "veir-opt"}, root, root / "work", 5)
            self.assertEqual(result["status"], "CRASH")


if __name__ == "__main__": unittest.main()
