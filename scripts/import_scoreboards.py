#!/usr/bin/env python3
"""Fetch only interpreter results; publish a strict projection, never raw blobs.

No checkout, archives, logs, source history, or upstream code execution. New test
names or schema fields require review instead of automatically becoming public.
"""
import argparse
import base64
import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from veir_suite.model import parse_json, read_json
from veir_suite.scoreboards import REPOSITORY, normalize_interpreter, sha, timestamp


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args):
        return None


def get(endpoint):
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'veir-dashboard'}
    if os.environ.get('GH_TOKEN'):
        headers['Authorization'] = 'Bearer ' + os.environ['GH_TOKEN']
    request = urllib.request.Request(f'https://api.github.com/repos/{REPOSITORY}/{endpoint}', headers=headers)
    with urllib.request.build_opener(NoRedirect).open(request, timeout=30) as response:
        payload = response.read(1024 * 1024 + 1)
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
        args.out.parent.mkdir(parents=True, exist_ok=True)
        temp = args.out.with_suffix('.tmp')
        temp.write_text(json.dumps(safe, indent=2) + '\n')
        temp.replace(args.out)
        print(f'Imported {len(safe["tests"])} reviewed test results at {revision}')
    except Exception as error:
        # Even JSON parser error messages may contain untrusted secret bytes.
        print('Scoreboard import failed; previous snapshot preserved. Error type: ' + type(error).__name__, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
