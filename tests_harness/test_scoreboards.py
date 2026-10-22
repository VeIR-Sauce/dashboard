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

    def test_snapshot_write_failure_keeps_old_bytes_and_cleans_temporary_file(self):
        from veir_suite.scoreboards import write_snapshot
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'result.json'; out.write_text('previous')
            with patch.object(Path, 'replace', side_effect=OSError('disk full')), self.assertRaises(OSError):
                write_snapshot(out, self.normalize(fixture()))
            self.assertEqual(out.read_text(), 'previous')
            self.assertEqual(list(Path(tmp).iterdir()), [out])

    def test_import_pins_results_to_source_commit_and_rejects_duplicate_json_fields(self):
        import base64
        import contextlib
        import io
        from scripts import import_scoreboards as importer
        revision = 'b' * 40
        commit = [{'sha': revision, 'commit': {'committer': {'date': '2026-10-22T16:00:00Z'}}}]
        allowed = {'tests': list(fixture()['tests'])}
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'result.json'
            for payload, success in [(json.dumps(fixture()), True),
                    ('{"veir":"' + 'a' * 40 + '","veir":"' + 'a' * 40 + '","tests":{}}', False)]:
                blob = {'encoding': 'base64', 'content': base64.b64encode(payload.encode()).decode()}
                previous = out.read_bytes() if out.exists() else None
                log = io.StringIO()
                with patch('sys.argv', ['import', '--out', str(out)]), patch.object(importer, 'get',
                        side_effect=[commit, blob]) as get, patch.object(importer, 'read_json', return_value=allowed), contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                    self.assertEqual(importer.main(), 0 if success else 1)
                    self.assertEqual(get.call_args_list[1].args, ('contents/results.json?ref=' + revision,))
                if success:
                    self.assertEqual(json.loads(out.read_text()), self.normalize(fixture()))
                else:
                    self.assertEqual(out.read_bytes(), previous)

    def test_transport_retries_only_transient_errors_and_bounds_response_size(self):
        import io
        import urllib.error
        from scripts import import_scoreboards as importer
        from unittest.mock import Mock
        for code, calls in [(503, 3), (429, 3), (403, 1), (404, 1), (302, 1)]:
            opener = Mock()
            opener.open.side_effect = [urllib.error.HTTPError('https://api.github.com/', code, 'private', {}, None) for _ in range(3)]
            with patch.object(importer.urllib.request, 'build_opener', return_value=opener), patch.object(importer.time, 'sleep'), self.assertRaises(urllib.error.HTTPError):
                importer.get('results')
            self.assertEqual(opener.open.call_count, calls)
        opener = Mock(); opener.open.side_effect = [TimeoutError(), io.BytesIO(b'{"ok":true}')]
        with patch.object(importer.urllib.request, 'build_opener', return_value=opener), patch.object(importer.time, 'sleep'):
            self.assertEqual(importer.get('results'), {'ok': True})
        opener.open.side_effect = None; opener.open.return_value = io.BytesIO(b' ' * (1024 * 1024 + 1))
        with patch.object(importer.urllib.request, 'build_opener', return_value=opener), self.assertRaises(ValueError):
            importer.get('results')

    def test_redirect_cannot_forward_authorization(self):
        import io
        import urllib.error
        import urllib.request
        import urllib.response
        from scripts import import_scoreboards as importer
        requests = []

        class Redirect(urllib.request.HTTPSHandler):
            def https_open(self, request):
                requests.append(request)
                response = urllib.response.addinfourl(io.BytesIO(b''),
                    {'location': 'https://example.invalid/steal'}, request.full_url, 302)
                response.msg = 'Found'
                return response

        opener = urllib.request.build_opener(importer.NoRedirect, Redirect)
        with patch.dict('os.environ', {'GH_TOKEN': 'synthetic-token'}), patch.object(
                importer.urllib.request, 'build_opener', return_value=opener), self.assertRaises(urllib.error.HTTPError):
            importer.get('results')
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0].host, 'api.github.com')
        self.assertEqual(requests[0].get_header('Authorization'), 'Bearer synthetic-token')
