#!/usr/bin/env python3
"""Gate measurement health and regressions; report a new cohort explicitly."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from veir_suite.model import InvalidData, read_json
from veir_suite.runner import regressions, validate_report
from veir_suite.history import previous_complete, read_history


def gate(report: dict, history: list[dict]) -> list[str]:
    validate_report(report)
    if not report["complete"]:
        raise InvalidData("Incomplete measurement: oracle, harness, timeout or source-provenance failure")
    previous = previous_complete(history, report, lambda item: item["cohort"])
    messages = []
    if previous:
        reopened = regressions(previous, report)
        if reopened:
            raise InvalidData("Regressed checks: " + ", ".join(reopened))
        messages.append("No regressions against the previous complete measurement in this cohort.")
    else:
        messages.append("New cohort: first complete measurement, not a claim of conformance. Review the contract/profile change.")
    messages.append(f"{report['summary']['conformance_remaining']} requirements remain open.")
    return messages


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--history", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        for message in gate(read_json(args.report), read_history(args.history)):
            print(message)
    except (InvalidData, OSError, KeyError, ValueError) as error:
        parser.exit(1, str(error) + "\n")


if __name__ == "__main__":
    main()
