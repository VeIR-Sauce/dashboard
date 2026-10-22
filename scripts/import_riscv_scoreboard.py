#!/usr/bin/env python3
"""Import selected CSV cells from a locally supplied RISC-V tracker snapshot.

Never copy its repository, credentials, logs, error text, IR or Markdown. All
string fields are fixed reviewed identifiers, status enums or validated hashes.
The caller must confirm the source transfer is complete before invoking this.
"""
import argparse
import configparser
import csv
from datetime import datetime, timezone
import io
import json
import re
import stat
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from veir_suite.model import read_json
from veir_suite.scoreboards import require, sha, timestamp, write_snapshot
from veir_suite.riscv_scoreboard import STAGES, validate_riscv


def git(root, *args):
    result = subprocess.run(['git', '--no-lazy-fetch', '--no-optional-locks', '--no-replace-objects', '-C', str(root),
                             '-c', 'core.fsmonitor=false', *args], capture_output=True, check=True, timeout=30)
    return result.stdout


def import_snapshot(source, allowed):
    revision = sha(git(source, 'rev-parse', 'HEAD').decode().strip())
    # Pin every read to the same commit, even if the source branch moves mid-import.
    date = datetime.fromisoformat(git(source, 'log', '-1', '--format=%cI', revision,
                                     '--', 'leaderboard/results').decode().strip())
    require(date.tzinfo is not None)
    recorded_at = timestamp(date.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))
    committed_paths = git(source, 'ls-tree', '-r', '--name-only', '-z', revision,
                          '--', 'leaderboard/results').decode().split('\0')
    result_csvs = {p for p in committed_paths if p.endswith(('/ops.csv', '/stages.csv', '/runs.csv'))}
    expected = {'leaderboard/results/sudoku/' + preset + '/' + name + '.csv'
                for preset in ('O2', 'inline') for name in ('ops', 'stages', 'runs')}
    # A new benchmark must be reviewed, not silently omitted from a fresh snapshot.
    require(result_csvs == expected)

    def read_private(path):
        require(path.resolve().is_relative_to(source.resolve()) and not path.is_symlink())
        require(stat.S_ISREG(path.stat().st_mode))
        with path.open('rb') as handle:
            raw = handle.read(1024 * 1024 + 1)
        require(len(raw) <= 1024 * 1024)
        return raw

    def rows(relative, columns):
        path = source / 'leaderboard/results' / relative
        raw = read_private(path)
        obj = revision + ':leaderboard/results/' + relative
        require(int(git(source, 'cat-file', '-s', obj)) == len(raw))
        require(raw == git(source, 'show', obj))
        text = raw.decode('utf-8')
        reader = csv.DictReader(io.StringIO(text))
        require(reader.fieldnames == columns)
        data = list(reader)
        require(all(None not in row and all(value is not None for value in row.values()) for row in data))
        return data
    manifest = rows('manifest.csv', ['component', 'version', 'sha256'])
    by_tool = {row['component']: row for row in manifest}
    require(len(by_tool) == len(manifest))
    veir = sha(by_tool['veir-opt']['version'])
    require(by_tool['veir2mir']['version'] == veir)
    builds = []
    for preset in ['O2', 'inline']:
        prefix = 'sudoku/' + preset + '/'
        operations = rows(prefix + 'ops.csv', ['op', 'given', 'left'])
        require({row['op'] for row in operations} <= set(allowed))
        require(len({row['op'] for row in operations}) == len(operations))
        ops = []
        for row in operations:
            require(row['given'].isdigit() and row['left'].isdigit())
            ops.append({'operation': row['op'], 'given': int(row['given']), 'left': int(row['left'])})
        stages = rows(prefix + 'stages.csv', ['stage', 'status', 'error'])
        require([row['stage'] for row in stages] == list(STAGES))
        safe_stages = []
        for row in stages:
            status = row['status']
            require(status in {'TIMEOUT', 'SKIPPED'} or re.fullmatch(r'-?(0|[1-9][0-9]{0,2})', status))
            normalized = 'passed' if status == '0' else 'skipped' if status == 'SKIPPED' else 'failed'
            safe_stages.append({'stage': row['stage'], 'status': normalized})
        runs = rows(prefix + 'runs.csv', ['input', 'verdict', 'veir_exit', 'gisel_exit'])
        require(len(runs) == 1 and runs[0]['input'] == 'sud1')
        # The raw exit strings and diagnostics are deliberately excluded.
        builds.append({'program': 'sudoku', 'preset': preset, 'stages': safe_stages,
                       'operations': ops, 'runs': [{'input': 'sud1', 'verdict': runs[0]['verdict']}]})
    result = validate_riscv({'schema_version': 1, 'source_revision': revision,
                             'recorded_at': recorded_at, 'veir': veir, 'builds': builds}, allowed)
    # Check known credentials without printing, hashing, or persisting their values.
    config = source / 'zuliprc'
    if config.exists():
        cp = configparser.ConfigParser(interpolation=None)
        cp.read_string(read_private(config).decode('utf-8'))
        payload = json.dumps(result)
        for section in cp.sections():
            for key, value in cp.items(section):
                if key.lower() in {'key', 'api_key', 'token', 'password', 'email'} and value:
                    require(value not in payload)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        root = Path(__file__).resolve().parents[1]
        allowed = read_json(root / 'requirements/riscv-operations.json')['operations']
        safe = import_snapshot(args.source, allowed)
        write_snapshot(args.out, safe)
        print('Imported reviewed RISC-V results at ' + safe['source_revision'])
    except Exception as error:
        print('RISC-V import rejected; previous data retained. Error type: ' + type(error).__name__, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
