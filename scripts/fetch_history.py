#!/usr/bin/env python3
"""Restore validated history from an earlier trusted default-branch workflow."""
import argparse
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from veir_suite.github_history import GitHub, find_artifact, restore_archive


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    api = GitHub(os.environ["GH_TOKEN"])
    artifact = find_artifact(api.json, os.environ["GITHUB_REPOSITORY"],
                             int(os.environ["GITHUB_REPOSITORY_ID"]),
                             os.environ.get("HISTORY_BRANCH", "main"),
                             int(os.environ["GITHUB_RUN_ID"]))
    if artifact is None:
        print("No earlier trusted artifact found; starting from checked-in evidence.")
        return
    count = restore_archive(api.archive(artifact["archive_download_url"]), args.out)
    print(f"Restored {count} receipts from artifact {artifact['id']}, run {artifact['workflow_run']['id']}")


if __name__ == "__main__":
    main()
