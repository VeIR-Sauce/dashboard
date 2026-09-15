#!/usr/bin/env python3
"""Gate native-suite regressions without relabelling legacy failures as success."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from veir_suite.model import InvalidData, read_json
from veir_suite.native import native_cohort, validate_native
from veir_suite.history import previous_complete, read_native_history


def gate(report: dict, history: list[dict]) -> list[str]:
    validate_native(report)
    if not report["complete"]:
        raise InvalidData("Incomplete native-suite accounting")
    previous = previous_complete(history, report, native_cohort)
    messages = []
    if previous:
        before = {test["name"]: test["code"] for test in previous["tests"]}
        reopened = [test["name"] for test in report["tests"]
                    if before[test["name"]] == "PASS" and test["code"] != "PASS"]
        if reopened:
            raise InvalidData("Native regressions: " + ", ".join(reopened))
        messages.append("No native regressions within the same source-test, harness and reference cohort.")
    else:
        messages.append("First native measurement for this test manifest, harness and reference profile; review the baseline.")
    messages.append(str(report["counts"]))
    return messages


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--history", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        for message in gate(read_json(args.report), read_native_history(args.history)):
            print(message)
    except (InvalidData, OSError, KeyError, ValueError) as error:
        parser.exit(1, str(error) + "\n")


if __name__ == "__main__":
    main()
