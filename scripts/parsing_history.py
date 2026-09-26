#!/usr/bin/env python3
"""Keep append-only receipts on a Git branch, independently of artifact expiry.

The workflow serializes writers. Pushes are ordinary fast-forwards; a competing
writer causes failure, never a force push or a silently discarded measurement.
"""
import argparse
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from veir_suite.history import record_receipt

BRANCH = 'measurement-history'


def git(root, *args, check=True):
    return subprocess.run(['git', '-C', str(root), *args], check=check,
                          text=True, capture_output=True)


def merge_receipts(source, destination):
    for filename in ['report.json', 'native.json', 'parsing.json']:
        for receipt in sorted(source.glob('*/' + filename)):
            record_receipt(receipt, destination)


def restore(root, checkout):
    advertised = git(root, 'ls-remote', '--exit-code', 'origin', 'refs/heads/' + BRANCH, check=False)
    if advertised.returncode == 0:
        git(root, 'fetch', '--no-tags', 'origin', 'refs/heads/' + BRANCH)
        git(root, 'worktree', 'add', '--detach', str(checkout), 'FETCH_HEAD')
    elif advertised.returncode == 2:  # No branch yet; authentication/network failures are fatal.
        git(root, 'worktree', 'add', '--detach', str(checkout), 'HEAD')
        git(checkout, 'switch', '--orphan', 'initial-measurement-history')
    else:
        raise RuntimeError('Could not read measurement-history: ' + advertised.stderr)
    merge_receipts(root / 'evidence', checkout / 'evidence')


def publish(root, checkout):
    merge_receipts(root / '.artifacts/parsing', checkout / 'evidence')
    git(checkout, 'add', 'evidence')
    changed = git(checkout, 'diff', '--cached', '--quiet', check=False)
    if changed.returncode not in {0, 1}:
        changed.check_returncode()
    if changed.returncode:
        git(checkout, 'commit', '-m', 'Record immutable VeIR measurement receipts')
        git(checkout, 'push', 'origin', 'HEAD:refs/heads/' + BRANCH)
    print('Measurement history retained on ' + BRANCH)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['restore', 'publish'])
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    checkout = root / '.artifacts/measurement-history'
    (restore if args.command == 'restore' else publish)(root, checkout)


if __name__ == '__main__':
    main()
