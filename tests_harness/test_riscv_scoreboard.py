import copy
import csv
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import import_riscv_scoreboard as importer
from veir_suite.model import InvalidData
from veir_suite.riscv_scoreboard import STAGES, build_riscv, validate_riscv

MARKER = 'DO_NOT_PUBLISH_SYNTHETIC_CREDENTIAL'
ALLOWED = ['llvm.alloca']


def source_fixture(root):
    committed = {}

    def csv_file(relative, rows):
        buf = io.StringIO(); csv.writer(buf, lineterminator='\n').writerows(rows)
        text = buf.getvalue(); committed[relative] = text
        path = root / 'leaderboard/results' / relative
        path.parent.mkdir(parents=True, exist_ok=True); path.write_text(text)

    csv_file('manifest.csv', [['component', 'version', 'sha256'],
        ['veir-opt', 'a' * 40, ''], ['veir2mir', 'a' * 40, ''], ['clang', MARKER, MARKER]])
    for preset in ['O2', 'inline']:
        prefix = 'sudoku/' + preset + '/'
        csv_file(prefix + 'ops.csv', [['op', 'given', 'left'], ['llvm.alloca', '10', '2']])
        csv_file(prefix + 'stages.csv', [['stage', 'status', 'error']] + [
            [stage, '0' if i < 4 else '1' if i == 4 else 'SKIPPED', MARKER] for i, stage in enumerate(STAGES)])
        csv_file(prefix + 'runs.csv', [['input', 'verdict', 'veir_exit', 'gisel_exit'],
            ['sud1', 'UNSUPPORTED', MARKER, '0']])
    (root / 'zuliprc').write_text('[api]\nkey=' + MARKER + '\nemail=private@example.invalid\n')

    def git(_, *args):
        if args[0] == 'rev-parse':
            return ('b' * 40 + '\n').encode()
        if args[0] == 'log':
            return b'2026-10-21T11:36:18Z\n'
        if args[0] == 'ls-tree':
            return ('\0'.join('leaderboard/results/' + name for name in committed) + '\0').encode()
        if args[0] == 'cat-file':
            return str(len(committed[args[2].split(':leaderboard/results/', 1)[1]].encode())).encode()
        if args[0] == 'show':
            return committed[args[1].split(':leaderboard/results/', 1)[1]].encode()
        raise AssertionError('Unexpected Git operation')

    return committed, git


class RiscvScoreboardTests(unittest.TestCase):
    def test_private_fields_are_discarded_and_public_page_preserves_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); _, git = source_fixture(root)
            with patch.object(importer, 'git', side_effect=git):
                data = importer.import_snapshot(root, ALLOWED)
            self.assertNotIn(MARKER, json.dumps(data))
            self.assertNotIn('private@example.invalid', json.dumps(data))
            self.assertEqual(data['source_revision'], 'b' * 40)
            (root / 'trackers').mkdir(); (root / 'trackers/riscv.json').write_text(json.dumps(data))
            (root / 'requirements').mkdir()
            (root / 'requirements/riscv-operations.json').write_text(json.dumps({'operations': ALLOWED}))
            out = root / 'site'; (out / 'data').mkdir(parents=True)
            build_riscv(root, out)
            html = (out / 'riscv.html').read_text()
            self.assertNotIn(MARKER, html)
            for expected in ['0/2', '4/20', 'llc-regalloc', 'UNSUPPORTED', 'not yet refreshed automatically', '/blob/' + 'b' * 40]:
                self.assertIn(expected, html)
            self.assertEqual(json.loads((out / 'data/riscv.json').read_text()), data)

    def test_modified_source_cannot_claim_committed_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); _, git = source_fixture(root)
            (root / 'leaderboard/results/sudoku/O2/ops.csv').write_text('op,given,left\nllvm.alloca,10,0\n')
            with patch.object(importer, 'git', side_effect=git), self.assertRaises(InvalidData):
                importer.import_snapshot(root, ALLOWED)

    def test_unreviewed_fields_strings_and_false_pass_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); _, git = source_fixture(root)
            with patch.object(importer, 'git', side_effect=git):
                original = importer.import_snapshot(root, ALLOWED)
            mutations = [lambda d: d.update(token=MARKER),
                lambda d: d['builds'][0]['stages'][0].update(error=MARKER),
                lambda d: d['builds'][0]['operations'][0].update(operation=MARKER),
                lambda d: d['builds'][0]['operations'][0].update(left=True),
                lambda d: d['builds'][0]['operations'][0].update(left=-1),
                lambda d: d['builds'][0]['runs'][0].update(verdict=MARKER),
                lambda d: d['builds'][0]['runs'][0].update(verdict='PASS')]
            for mutate in mutations:
                data = copy.deepcopy(original); mutate(data)
                with self.assertRaises(InvalidData) as raised:
                    validate_riscv(data, ALLOWED)
                self.assertNotIn(MARKER, str(raised.exception))

    def test_failed_import_retains_previous_snapshot_and_redacts_errors(self):
        import contextlib
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'out.json'; out.write_text('previous')
            log = io.StringIO()
            with patch('sys.argv', ['import', '--source', tmp, '--out', str(out)]), patch.object(
                    importer, 'import_snapshot', side_effect=ValueError(MARKER)), contextlib.redirect_stderr(log):
                self.assertEqual(importer.main(), 1)
            self.assertEqual(out.read_text(), 'previous')
            self.assertNotIn(MARKER, log.getvalue())

    def test_upstream_run_verdicts_and_expanded_or_empty_operation_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); _, git = source_fixture(root)
            with patch.object(importer, 'git', side_effect=git):
                data = importer.import_snapshot(root, ALLOWED)
            data['builds'][0]['operations'][0].update(given=0, left=3)
            data['builds'][1]['operations'] = []
            validate_riscv(data, ALLOWED)
            for build in data['builds']:
                for stage in build['stages']:
                    stage['status'] = 'passed'
            for verdict in ['PASS', 'MISMATCH', 'CRASH', 'TIMEOUT']:
                data['builds'][0]['runs'][0]['verdict'] = verdict
                self.assertEqual(validate_riscv(data, ALLOWED), data)

    def test_nonzero_exit_codes_signals_and_timeout_are_failures(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); committed, git = source_fixture(root)
            name = 'sudoku/O2/stages.csv'; original = committed[name]
            for status in ['2', '127', '139', '-11', 'TIMEOUT']:
                committed[name] = original.replace('llc-regalloc,1,', 'llc-regalloc,' + status + ',')
                (root / 'leaderboard/results' / name).write_text(committed[name])
                with patch.object(importer, 'git', side_effect=git):
                    result = importer.import_snapshot(root, ALLOWED)
                self.assertEqual(result['builds'][0]['stages'][4]['status'], 'failed')

    def test_new_benchmark_and_malformed_nested_shapes_reject_without_source_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); committed, git = source_fixture(root)
            with patch.object(importer, 'git', side_effect=git):
                data = importer.import_snapshot(root, ALLOWED)
                committed['new-program/O2/stages.csv'] = ''
                with self.assertRaises(InvalidData):
                    importer.import_snapshot(root, ALLOWED)
            mutations = [lambda d: d['builds'].__setitem__(0, None),
                lambda d: d['builds'][0].update(stages=None),
                lambda d: d['builds'][0]['stages'].__setitem__(0, MARKER),
                lambda d: d['builds'][0].update(operations=[None]),
                lambda d: d['builds'][0].update(runs=[{'input': MARKER}])]
            for mutate in mutations:
                changed = copy.deepcopy(data); mutate(changed)
                with self.assertRaises(InvalidData) as error:
                    validate_riscv(changed, ALLOWED)
                self.assertNotIn(MARKER, str(error.exception))

    def test_real_git_provenance_timezone_and_byte_comparison(self):
        import os
        import subprocess
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); source_fixture(root)
            env = dict(os.environ, GIT_AUTHOR_NAME='Test', GIT_AUTHOR_EMAIL='test@example.invalid',
                       GIT_COMMITTER_NAME='Test', GIT_COMMITTER_EMAIL='test@example.invalid',
                       GIT_AUTHOR_DATE='2026-10-21T12:36:18+01:00', GIT_COMMITTER_DATE='2026-10-21T12:36:18+01:00')
            def git(*args):
                return subprocess.check_output(['git', '-C', str(root), *args], env=env, stderr=subprocess.DEVNULL)
            git('init'); git('add', 'leaderboard'); git('-c', 'commit.gpgsign=false', 'commit', '-m', 'Fixture')
            result = importer.import_snapshot(root, ALLOWED)
            self.assertEqual(result['source_revision'], git('rev-parse', 'HEAD').decode().strip())
            self.assertEqual(result['recorded_at'], '2026-10-21T11:36:18Z')
            path = root / 'leaderboard/results/sudoku/O2/ops.csv'
            original = path.read_bytes(); path.write_bytes(original.replace(b'\n', b'\r\n'))
            with self.assertRaises(InvalidData):
                importer.import_snapshot(root, ALLOWED)
            path.unlink(); path.symlink_to(root / 'leaderboard/results/sudoku/inline/ops.csv')
            with self.assertRaises(InvalidData):
                importer.import_snapshot(root, ALLOWED)
