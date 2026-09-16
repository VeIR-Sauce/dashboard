import unittest
import copy

from veir_suite.site import parsing_evidence, parsing_form
from veir_suite.parsing import MODES, aggregate_operation, case_counts, case_id, classify, controls_ok, counts, digest_text, operation_results, validate_parsing
from veir_suite.model import InvalidData, digest
from scripts.import_parsing_cases import split_types, leaf_example


class ParsingEvidenceTests(unittest.TestCase):
    def test_scalar_vector_partition_uses_input_types_not_labels_or_comments(self):
        for text in ['"llvm.add"(%a, %b) : (i32, i32) -> i32',
                     '// vector<4xi32> example\n"llvm.add"()',
                     '"llvm.func"() <{sym_name = "vector<4xi32>"}>',
                     '/* vector<4xi32> */ "llvm.mlir.global"()',
                     '"name with \\" vector<4xi32>"']:
            self.assertEqual(parsing_form(text), 'scalar', text)
        for text in ['"llvm.add"(%a, %b) : (vector<4xi32>, vector<4xi32>) -> vector<4xi32>',
                     '!v = vector<[4]xi32>\n"llvm.func"()',
                     '"llvm.func"() <{function_type = !llvm.func<i32 (vector<4xi32>)>}>',
                     '"llvm.mlir.constant"() <{value = dense<0> : vector<4xi32>}>']:
            self.assertEqual(parsing_form(text), 'vector', text)

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


class ParserVariantTests(unittest.TestCase):
    def fixture(self):
        report = copy.deepcopy(parser_receipt())
        report['schema_version'] = 2
        first = report['manifest']['cases'][0]
        first['id'] = case_id(first)
        second = {**first, 'id': 'llvm.add.scalable', 'label': 'Scalable vector',
                  'text': '"llvm.add"() : () -> vector<[4]xi32>\n'}
        second['input_sha256'] = digest_text(second['text'])
        report['manifest']['cases'].append(second)
        report['manifest_sha256'] = digest(report['manifest'])
        a = {**report['results'][0], 'id': first['id']}
        b = copy.deepcopy(a); b.update(id=second['id'], input_sha256=second['input_sha256'])
        for mode in MODES:
            b[mode] = {'status': 'rejected', 'step': {**b[mode]['step'], 'exit_code': 1,
                'stdout': '', 'stderr': 'case.mlir:1:24: error: vector type expected'}}
        report['results'] = [aggregate_operation('llvm.add', [a, b])]
        report['counts'] = counts(report['results'])
        report['case_counts'] = case_counts(report['results'])
        return report

    def test_partial_counts_do_not_turn_one_pass_into_complete_operation_support(self):
        report = self.fixture(); validate_parsing(report)
        self.assertEqual(report['results'][0]['strict']['status'], 'partial')
        self.assertEqual(report['results'][0]['strict']['parsed'], 1)
        self.assertEqual(report['results'][0]['strict']['total'], 2)
        self.assertEqual(report['counts']['strict'], {'partial': 1})
        self.assertEqual(report['case_counts']['strict'], {'parsed': 1, 'rejected': 1})

    def test_missing_duplicate_and_cross_operation_cases_fail_closed(self):
        for change in [
            lambda r: r['results'][0]['cases'].pop(),
            lambda r: r['results'][0]['cases'].append(r['results'][0]['cases'][0]),
            lambda r: r['results'][0]['cases'][0].update(operation='llvm.sub'),
            lambda r: r['results'][0]['strict'].update(parsed=2),
            lambda r: r['case_counts']['strict'].update(parsed=2),
        ]:
            report = self.fixture(); change(report)
            with self.assertRaises(InvalidData):
                validate_parsing(report)

    def test_error_in_one_variant_makes_measurement_incomplete_even_with_another_pass(self):
        report = self.fixture()
        cases = report['results'][0]['cases']
        cases[1]['strict']['step']['kind'] = 'timeout'; cases[1]['strict']['status'] = 'error'
        report['results'] = [aggregate_operation('llvm.add', cases)]
        report['counts'] = counts(report['results']); report['case_counts'] = case_counts(report['results'])
        with self.assertRaisesRegex(InvalidData, 'completion'):
            validate_parsing(report)
        report['complete'] = False; validate_parsing(report)

    def test_legacy_receipts_display_as_single_cases_without_mutation(self):
        report = parser_receipt(); original = copy.deepcopy(report)
        rows = operation_results(report)
        self.assertEqual(len(rows[0]['cases']), 1)
        self.assertEqual(rows[0]['strict']['total'], 1)
        self.assertEqual(rows[0]['cases'][0]['id'], 'llvm.add.baseline')
        self.assertEqual(report, original)
