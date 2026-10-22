#!/usr/bin/env python3
"""Fetch only interpreter results; publish a strict projection, never raw blobs.

No checkout, archives, logs, source history, or upstream code execution. New test
names or schema fields require review instead of automatically becoming public.
"""
import argparse
import base64
import os
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from veir_suite.model import parse_json, read_json
from veir_suite.scoreboards import REPOSITORY, normalize_interpreter, sha, timestamp, write_snapshot


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args):
        return None


def get(endpoint):
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'veir-dashboard'}
    if os.environ.get('GH_TOKEN'):
        headers['Authorization'] = 'Bearer ' + os.environ['GH_TOKEN']
    request = urllib.request.Request(f'https://api.github.com/repos/{REPOSITORY}/{endpoint}', headers=headers)
    opener = urllib.request.build_opener(NoRedirect)
    for attempt in range(3):
        try:
            with opener.open(request, timeout=30) as response:
                payload = response.read(1024 * 1024 + 1)
            break
        except urllib.error.HTTPError as error:
            error.close()
            if attempt == 2 or error.code not in {429, 500, 502, 503, 504}:
                raise
        except (urllib.error.URLError, TimeoutError):
            if attempt == 2:
                raise
        time.sleep(2 ** attempt)

    if len(payload) > 1024 * 1024:
        raise ValueError('Source exceeds import size limit')
    return parse_json('{"response":' + payload.decode() + '}', 'external API')['response']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    try:
        commit = get('commits?path=results.json&per_page=1')[0]
        revision = sha(commit['sha'])
        date = timestamp(commit['commit']['committer']['date'])
        blob = get('contents/results.json?ref=' + revision)
        if blob.get('encoding') != 'base64':
            raise ValueError('Unexpected encoding')
        raw = parse_json(base64.b64decode(blob['content']).decode(), 'external results')
        safe = normalize_interpreter(raw, revision, date, read_json(root / 'requirements/interpreter-tests.json')['tests'])
        write_snapshot(args.out, safe)
        print(f'Imported {len(safe["tests"])} reviewed test results at {revision}')
    except Exception as error:
        # Even JSON parser error messages may contain untrusted secret bytes.
        print('Scoreboard import failed; previous snapshot preserved. Error type: ' + type(error).__name__, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
