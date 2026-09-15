import unittest

from veir_suite.site import parsing_evidence


class ParsingEvidenceTests(unittest.TestCase):
    def report(self, kind="verify", expect="accept", exit_code=0, status="PASS"):
        return {"registry": {
            "requirements": [{"id": "add", "operations": ["llvm.add"], "test_ids": ["sample"]}],
            "tests": [{"id": "sample", "kind": kind, "expect": expect, "input": "cases/sample.mlir"}]},
            "results": [{"id": "sample", "status": status, "input_sha256": "input hash", "steps": [
                {"phase": "veir.verification" if kind == "verify" else "veir.roundtrip",
                 "kind": "exit", "exit_code": exit_code}]}]}

    def test_positive_verification_proves_only_the_mapped_example_parsed(self):
        result = parsing_evidence(self.report())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["operation"], "llvm.add")
        self.assertEqual(result[0]["input_sha256"], "input hash")

    def test_negative_cases_and_verifier_failures_do_not_establish_parsing(self):
        self.assertEqual(parsing_evidence(self.report(expect="reject")), [])
        self.assertEqual(parsing_evidence(self.report(exit_code=1, status="FAIL")), [])
        self.assertEqual(parsing_evidence(self.report(kind="execute")), [])

    def test_later_roundtrip_failure_does_not_erase_a_successful_parse(self):
        report = self.report(kind="roundtrip", status="FAIL")
        report["results"][0]["steps"].append({"phase": "reference.canonicalize-veir-output", "kind": "exit", "exit_code": 1})
        self.assertEqual(len(parsing_evidence(report)), 1)

    def test_missing_or_nonexit_observations_remain_unknown(self):
        report = self.report()
        report["results"][0]["steps"][0]["kind"] = "timeout"
        self.assertEqual(parsing_evidence(report), [])
        report["results"] = []
        self.assertEqual(parsing_evidence(report), [])
