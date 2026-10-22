import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from veir_suite.model import InvalidData
from veir_suite.scoreboards import normalize_interpreter, validate_interpreter, build_scoreboards


def fixture():
    return {'veir': 'a' * 40, 'tests': {
        'clean/main2': {'finished': True, 'agrees': {'llubi': True, 'alive-exec': None}},
        'ub/unreachable': {'finished': False, 'agrees': {'llubi': None, 'alive-exec': None}},
    }}


class ScoreboardTests(unittest.TestCase):
    def normalize(self, data):
        return normalize_interpreter(data, 'b' * 40, '2026-10-22T16:00:00Z', fixture()['tests'])

    def test_preserves_unknown_and_false_results_without_inventing_passes(self):
        raw = fixture(); raw['tests']['clean/main2']['agrees']['alive-exec'] = False
        result = self.normalize(raw)
        self.assertIsNone(result['tests']['ub/unreachable']['agrees']['llubi'])
        self.assertIs(result['tests']['clean/main2']['agrees']['alive-exec'], False)
        self.assertEqual(result, validate_interpreter(result, fixture()['tests']))

    def test_secrets_and_unreviewed_schema_cannot_cross_import_boundary(self):
        marker = 'DO_NOT_PUBLISH_SYNTHETIC_CREDENTIAL'
        mutations = [lambda d: d.update(api_key=marker),
            lambda d: d.update(log=marker),
            lambda d: d['tests']['clean/main2'].update(token=marker),
            lambda d: d['tests']['clean/main2']['agrees'].update(llubi=marker),
            lambda d: d['tests']['clean/main2'].update(finished=marker),
            lambda d: d.update(veir=marker),
            lambda d: d['tests'].update({marker: d['tests']['clean/main2']}),
            lambda d: d['tests'].pop('ub/unreachable'),
            lambda d: d['tests']['clean/main2']['agrees'].update(llubi=1),
            lambda d: d['tests']['ub/unreachable']['agrees'].update(llubi=True)]
        for mutate in mutations:
            raw = copy.deepcopy(fixture()); mutate(raw)
            with self.assertRaises(InvalidData) as raised:
                self.normalize(raw)
            self.assertNotIn(marker, str(raised.exception))

    def test_bad_import_retains_previous_file_and_never_logs_rejected_values(self):
        import contextlib
        import io
        from scripts import import_scoreboards
        marker = 'DO_NOT_PUBLISH_SYNTHETIC_CREDENTIAL'
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'results.json'; out.write_text('original')
            log = io.StringIO()
            with patch('sys.argv', ['import', '--out', str(out)]), patch.object(
                    import_scoreboards, 'get', side_effect=ValueError(marker)), contextlib.redirect_stderr(log):
                self.assertEqual(import_scoreboards.main(), 1)
            self.assertEqual(out.read_text(), 'original')
            self.assertNotIn(marker, log.getvalue())

    def test_site_uses_latest_snapshot_and_preserves_source_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); out = root / 'site'; (out / 'data').mkdir(parents=True)
            (root / 'requirements').mkdir()
            (root / 'requirements/interpreter-tests.json').write_text(json.dumps({'tests': list(fixture()['tests'])}))
            data = self.normalize(fixture())
            (root / 'trackers').mkdir(); (root / 'trackers/interpreter.json').write_text(json.dumps(data))
            build_scoreboards(root, out, root / 'evidence')
            html = (out / 'interpreter.html').read_text()
            self.assertIn('Naveen Seth Hanig', html)
            self.assertIn('1/2', html); self.assertIn('Not comparable', html)
            self.assertIn('No result', html); self.assertIn('void', html)
            self.assertIn('/blob/' + 'b' * 40, html)
            self.assertIn('Results awaiting import', (out / 'riscv.html').read_text())
            history = root / 'remote/evidence'; history.mkdir(parents=True)
            (history.parent / 'trackers').mkdir()
            data['source_revision'] = 'c' * 40
            (history.parent / 'trackers/interpreter.json').write_text(json.dumps(data))
            build_scoreboards(root, out, history)
            self.assertIn('/blob/' + 'c' * 40, (out / 'interpreter.html').read_text())
