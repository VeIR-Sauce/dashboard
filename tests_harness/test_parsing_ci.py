import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from scripts.parsing_history import merge_receipts, restore, publish
from tests_harness.test_parsing import parser_receipt
from veir_suite.model import InvalidData, file_digest
from veir_suite.parsing import digest_text, run_parsing


class HistoryPublicationTests(unittest.TestCase):
    def test_first_publication_restoration_and_append_preserve_receipts(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            remote, first, second = [tmp / name for name in ['remote.git', 'first', 'second']]
            def git(root, *args):
                return subprocess.run(['git', '-C', str(root), *args], check=True, capture_output=True)
            subprocess.run(['git', 'init', '--bare', str(remote)], check=True, capture_output=True)
            for root in [first, second]:
                root.mkdir()
                git(root, 'init')
                git(root, 'config', 'user.name', 'Test')
                git(root, 'config', 'user.email', 'test@example.invalid')
                git(root, 'remote', 'add', 'origin', str(remote))
                path = root / 'evidence/parsing-unit/parsing.json'
                path.parent.mkdir(parents=True)
                path.write_text(json.dumps(parser_receipt()))
                git(root, 'add', 'evidence')
                git(root, 'commit', '-m', 'Test seed')
            history = first / '.artifacts/history'
            restore(first, history)
            publish(first, history)
            original = (history / 'evidence/parsing-unit/parsing.json').read_bytes()
            history2 = second / '.artifacts/history'
            restore(second, history2)
            report = copy.deepcopy(parser_receipt()); report['id'] = 'parsing-new'
            receipt = second / '.artifacts/parsing/parsing-new/parsing.json'
            receipt.parent.mkdir(parents=True); receipt.write_text(json.dumps(report))
            publish(second, history2)
            self.assertEqual(original, (history2 / 'evidence/parsing-unit/parsing.json').read_bytes())
            self.assertTrue((history2 / 'evidence/parsing-new/parsing.json').is_file())
            # A stale writer cannot overwrite the newer branch.
            receipt = first / '.artifacts/parsing/parsing-other/parsing.json'
            receipt.parent.mkdir(parents=True); report['id'] = 'parsing-other'
            receipt.write_text(json.dumps(report))
            with self.assertRaises(subprocess.CalledProcessError):
                publish(first, history)

    def test_conflicting_receipt_is_never_replaced(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            source, destination = tmp / 'source', tmp / 'destination'
            path = source / 'parsing-unit/parsing.json'; path.parent.mkdir(parents=True)
            path.write_text(json.dumps(parser_receipt()))
            merge_receipts(source, destination)
            original = (destination / 'parsing-unit/parsing.json').read_bytes()
            changed = parser_receipt(); changed['finished_at'] = '2026-09-26T00:00:00Z'
            path.write_text(json.dumps(changed))
            with self.assertRaises(InvalidData):
                merge_receipts(source, destination)
            self.assertEqual(original, (destination / 'parsing-unit/parsing.json').read_bytes())


class RebuiltReferenceTests(unittest.TestCase):
    def test_revalidation_is_explicit_and_reference_rejection_prevents_completion(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); veir = root / 'veir'; reference = root / 'mlir-opt'
            for directory in ['requirements', 'cases', 'veir_suite', 'veir/.lake/build/bin']:
                (root / directory).mkdir(parents=True)
            reference.write_text('rebuilt reference')
            (veir / '.lake/build/bin/veir-opt').write_text('parser')
            for filename in ['parsing.py', 'process.py']:
                (root / 'veir_suite' / filename).write_text('test harness')
            text = '"llvm.add"() : () -> ()\n'; (root / 'cases/add.mlir').write_text(text)
            catalog = root / 'requirements/catalog.json'
            catalog.write_text(json.dumps({'operations': [{'name': 'llvm.add'}]}))
            (root / 'requirements/parsing.json').write_text(json.dumps({
                'catalog_sha256': file_digest(catalog), 'reference_sha256': 'old binary',
                'llvm_revision': 'pinned', 'cases': [{'operation': 'llvm.add',
                    'input': 'cases/add.mlir', 'input_sha256': digest_text(text)}]}))
            with self.assertRaises(InvalidData):
                run_parsing(root, veir, reference, root / 'out')
            reject_reference = False
            def execute(command, **kwargs):
                step = {'kind': 'exit', 'exit_code': 0, 'stdout': text, 'stderr': '', 'command': command}
                if command[0] == str(reference) and reject_reference:
                    step.update(exit_code=1, stderr='reference rejects this example')
                elif 'malformed.mlir' in command[1]:
                    step.update(exit_code=1, stderr='syntax error')
                elif len(command) == 2:
                    step.update(exit_code=1, stderr='Error verifying input program: ill-typed add')
                return step
            with patch('veir_suite.parsing.execute', side_effect=execute), patch(
                    'veir_suite.parsing.git_identity', return_value={'commit': 'current', 'dirty': False}):
                report, code = run_parsing(root, veir, reference, root / 'out', revalidate_reference=True)
                self.assertEqual(code, 0)
                self.assertEqual(report['tools']['mlir_opt']['sha256'], file_digest(reference))
                reject_reference = True
                report, code = run_parsing(root, veir, reference, root / 'out', revalidate_reference=True)
                self.assertEqual(code, 2)
                self.assertEqual(report['results'][0]['cases'][0]['strict']['status'], 'not_tested')
