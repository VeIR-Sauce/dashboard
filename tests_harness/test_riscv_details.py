import copy
import csv
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import import_riscv_scoreboard as importer
from tests_harness.test_riscv_scoreboard import ALLOWED, MARKER, source_fixture
from veir_suite.model import InvalidData
from veir_suite.riscv_details import validate_details
from veir_suite.riscv_scoreboard import build_riscv


def reviewed_fixture(root):
    committed, git = source_fixture(root)
    reviewed = {'source_revision': 'b' * 40, 'builds': {}}
    for preset in ['O2', 'inline']:
        prefix = 'sudoku/' + preset + '/'
        stages = committed[prefix + 'stages.csv'].replace(MARKER, '')
        error = 'error: cannot allocate register <v100> in main'
        stages = stages.replace('llc-regalloc,1,\n', 'llc-regalloc,1,' + error + '\n')
        committed[prefix + 'stages.csv'] = stages
        (root / 'leaderboard/results' / prefix / 'stages.csv').write_text(stages)
        example = {'op': 'llvm.alloca', 'types': '(i32) -> !llvm.ptr', 'left': 2, 'function': 'main',
                   'line': 17, 'definition': '<script>alert(1)</script>\n"llvm.alloca"()'}
        buffer = io.StringIO(); writer = csv.DictWriter(buffer, fieldnames=list(example), lineterminator='\n')
        writer.writeheader(); writer.writerow(example)
        committed[prefix + 'unlowered.csv'] = buffer.getvalue()
        (root / 'leaderboard/results' / prefix / 'unlowered.csv').write_text(buffer.getvalue())
        reviewed['builds']['sudoku/' + preset] = {
            'diagnostics': [{'stage': 'llc-regalloc', 'error': error}], 'examples': [example]}
    return committed, git, reviewed


class RiscvDetailTests(unittest.TestCase):
    def test_exact_review_required_for_private_text_and_known_credentials_still_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); committed, git, reviewed = reviewed_fixture(root)
            with patch.object(importer, 'git', side_effect=git):
                importer.import_snapshot(root, ALLOWED, reviewed)
                path = root / 'leaderboard/results/sudoku/O2/stages.csv'
                committed['sudoku/O2/stages.csv'] = path.read_text().replace('cannot allocate register <v100> in main', MARKER)
                path.write_text(committed['sudoku/O2/stages.csv'])
                with self.assertRaises(InvalidData) as error:
                    importer.import_snapshot(root, ALLOWED, reviewed)
                self.assertNotIn(MARKER, str(error.exception))
                # Even an accidentally approved known credential must not pass.
                reviewed['builds']['sudoku/O2']['diagnostics'][0]['error'] = 'error: ' + MARKER
                with self.assertRaises(InvalidData):
                    importer.import_snapshot(root, ALLOWED, reviewed)

    def test_pages_link_to_each_build_and_escape_diagnostics_and_examples(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); _, git, reviewed = reviewed_fixture(root)
            with patch.object(importer, 'git', side_effect=git):
                snapshot = importer.import_snapshot(root, ALLOWED, reviewed)
            (root / 'trackers').mkdir(); (root / 'trackers/riscv.json').write_text(json.dumps(snapshot))
            (root / 'requirements').mkdir()
            (root / 'requirements/riscv-operations.json').write_text(json.dumps({'operations': ALLOWED}))
            (root / 'requirements/riscv-reviewed-details.json').write_text(json.dumps(reviewed))
            out = root / 'site'; (out / 'data').mkdir(parents=True)
            build_riscv(root, out)
            main = (out / 'riscv.html').read_text()
            for preset in ['O2', 'inline']:
                filename = 'riscv-sudoku-' + preset + '.html'
                self.assertIn('href="' + filename + '"', main)
                page = (out / filename).read_text()
                self.assertIn('href="riscv.html"', page)
                self.assertIn('Compilation stages', page)
                self.assertIn('error: cannot allocate register &lt;v100&gt; in main', page)
                self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', page)
                self.assertNotIn('<script>alert', page)
                self.assertIn('/veir-opt.mlir#L17', page)
                self.assertIn('All operation counts', page)
            self.assertEqual(json.loads((out / 'data/riscv-details.json').read_text()), reviewed)

    def test_stale_details_invalid_shapes_and_counts_cannot_be_published(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); _, git, reviewed = reviewed_fixture(root)
            with patch.object(importer, 'git', side_effect=git):
                snapshot = importer.import_snapshot(root, ALLOWED, reviewed)
            changes = [lambda d: d.update(source_revision='c' * 40),
                       lambda d: d['builds'].pop('sudoku/inline'),
                       lambda d: d['builds']['sudoku/O2']['diagnostics'][0].update(token=MARKER),
                       lambda d: d['builds']['sudoku/O2']['examples'][0].update(left=3),
                       lambda d: d['builds']['sudoku/O2']['examples'][0].update(line=0),
                       lambda d: d['builds']['sudoku/O2']['examples'][0].update(definition=None)]
            for change in changes:
                data = copy.deepcopy(reviewed); change(data)
                with self.assertRaises(InvalidData):
                    validate_details(data, snapshot)
