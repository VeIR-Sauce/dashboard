import unittest
import copy

from veir_suite.site import parsing_evidence
from veir_suite.parsing import MODES, classify, controls_ok, counts, digest_text, validate_parsing
from veir_suite.model import InvalidData, digest
from scripts.import_parsing_cases import split_types, leaf_example


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


def parser_receipt():
    text = '"llvm.add"() : () -> ()\n'
    manifest = {'catalog': {'operations': [{'name': 'llvm.add'}]},
                'cases': [{'operation': 'llvm.add', 'text': text, 'input_sha256': digest_text(text)}],
                'modes': MODES, 'veir_arguments': ['--disable-verifiers', '--print-op-generic']}
    step = {'kind': 'exit', 'exit_code': 0, 'stdout': text, 'stderr': ''}
    row = {'operation': 'llvm.add', 'input_sha256': digest_text(text), 'reference': step}
    for mode, flags in MODES.items():
        row[mode] = {'status': 'parsed', 'step': {**step, 'command': ['veir-opt', 'case.mlir', *manifest['veir_arguments'], *flags]}}
    controls = {'verification_disabled': step,
        'verification_enabled': {**step, 'exit_code': 1, 'stderr': 'Error verifying input program: invalid add'},
        'malformed_rejected': {**step, 'exit_code': 1}}
    return {'kind': 'veir-parsing', 'schema_version': 1, 'id': 'parsing-unit',
        'finished_at': '2026-09-15T00:00:00Z', 'manifest': manifest, 'manifest_sha256': digest(manifest),
        'tools': {'veir_opt': {'path': 'veir-opt'}}, 'results': [row], 'counts': counts([row]),
        'controls': controls, 'controls_ok': True, 'unchanged': True, 'complete': True}


class ParserOnlyTests(unittest.TestCase):
    def test_success_requires_target_in_printed_output(self):
        self.assertEqual(classify({'kind': 'exit', 'exit_code': 0, 'stdout': '"llvm.add"()'}, 'llvm.add', ''), 'parsed')
        self.assertEqual(classify({'kind': 'exit', 'exit_code': 0, 'stdout': ''}, 'llvm.add', ''), 'error')

    def test_unregistered_target_and_scaffolding_failures_are_distinct(self):
        step = {'kind': 'exit', 'exit_code': 1, 'stderr': "op 'llvm.invoke' is not registered"}
        self.assertEqual(classify(step, 'llvm.invoke', ''), 'rejected')
        self.assertEqual(classify(step, 'llvm.landingpad', ''), 'blocked')

    def test_source_location_and_worker_failure_attribution(self):
        text = '"llvm.func"()\n  %0 = "llvm.add"()'
        step = {'kind': 'exit', 'exit_code': 1, 'stderr': 'case.mlir:2:7: error: type expected'}
        self.assertEqual(classify(step, 'llvm.add', text), 'rejected')
        self.assertEqual(classify({**step, 'stderr': 'case.mlir:1:7: error: type expected'}, 'llvm.add', text), 'blocked')
        for kind in ['timeout', 'crash', 'output_limit', 'not_found']:
            self.assertEqual(classify({**step, 'kind': kind}, 'llvm.add', text), 'error')
        self.assertEqual(classify({**step, 'stderr': 'Unrecognized flag'}, 'llvm.add', text), 'error')

    def test_complete_receipt_and_controls_are_validated(self):
        receipt = parser_receipt()
        validate_parsing(receipt)
        self.assertTrue(controls_ok(receipt['controls']))
        receipt['controls']['verification_enabled']['exit_code'] = 0
        with self.assertRaisesRegex(InvalidData, 'controls'):
            validate_parsing(receipt)

    def test_receipt_rejects_missing_rows_stale_input_and_wrong_mode(self):
        for change in [
            lambda r: r.update(results=[]),
            lambda r: r['results'][0].update(input_sha256='changed'),
            lambda r: r['results'][0]['strict']['step']['command'].append('--allow-unregistered-dialect'),
            lambda r: r['results'][0]['reference'].update(exit_code=1),
            lambda r: r['results'][0]['strict'].update(status='rejected'),
            lambda r: r.update(counts={}),
        ]:
            report = copy.deepcopy(parser_receipt()); change(report)
            with self.assertRaises(InvalidData):
                validate_parsing(report)

    def test_nested_operand_types_are_kept_intact_when_isolating_an_op(self):
        self.assertEqual(split_types('!llvm.struct<(i32, ptr)>, vector<4xi32>, !llvm.array<2 x i64>'),
                         ['!llvm.struct<(i32, ptr)>', 'vector<4xi32>', '!llvm.array<2 x i64>'])
        example = leaf_example('  %4 = "llvm.extractvalue"(%3) <{position = array<i64: 1>}> : (!llvm.struct<(i32, i64)>) -> i64', '')
        self.assertIn('llvm.func @sample(%arg0: !llvm.struct<(i32, i64)>)', example)
        self.assertIn('"llvm.extractvalue"(%arg0)', example)
