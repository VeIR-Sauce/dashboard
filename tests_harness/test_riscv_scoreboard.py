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
            return 'b' * 40 + '\n'
        if args[0] == 'log':
            return '2026-10-21T11:36:18Z\n'
        if args[0] == 'show':
            return committed[args[1].split(':leaderboard/results/', 1)[1]]
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
                lambda d: d['builds'][0]['operations'][0].update(left=11),
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
