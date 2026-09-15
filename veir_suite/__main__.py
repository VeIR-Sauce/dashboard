from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

from .model import InvalidData, load_registry, read_json
from .runner import regressions, run, validate_report


def main():
    parser = argparse.ArgumentParser(description="VeIR requirements, independent tests and measured progress")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("validate", help="Validate all contracts, IDs, mappings and fixture hashes")
    p = commands.add_parser("run", help="Run a complete selected manifest, preserving every failure")
    p.add_argument("--veir", type=Path, required=True)
    p.add_argument("--out", type=Path, default=Path(".artifacts/runs"))
    p.add_argument("--scope", action="append", default=[])
    p.add_argument("--timeout", type=float, default=15.0)
    p.add_argument("--profile", default="local")
    p.add_argument("--reference-revision", default="unknown")
    p = commands.add_parser("parse", help="Measure reference-validated LLVM examples without VeIR verification")
    p.add_argument("--veir", type=Path, required=True)
    p.add_argument("--mlir-opt", type=Path, required=True)
    p.add_argument("--out", type=Path, default=Path(".artifacts/parsing"))
    p.add_argument("--timeout", type=float, default=10.0)
    p = commands.add_parser("report-check", help="Reject incomplete, altered or inconsistent receipts")
    p.add_argument("report", type=Path)
    p = commands.add_parser("compare", help="Gate regressions within one fixed cohort")
    p.add_argument("before", type=Path)
    p.add_argument("after", type=Path)
    p = commands.add_parser("site", help="Build an offline site / GitHub Pages artifact")
    p.add_argument("--history", type=Path, default=Path("evidence"))
    p.add_argument("--out", type=Path, default=Path("site-output"))
    p = commands.add_parser("native", help="Build and account for the existing Lean, ExArray and lit suites")
    p.add_argument("--veir", type=Path, required=True)
    p.add_argument("--out", type=Path, default=Path(".artifacts/native"))
    p.add_argument("--lake", required=True)
    p.add_argument("--lit", required=True)
    p.add_argument("--jobs", type=int, default=2)
    p = commands.add_parser("record", help="Add a validated receipt to append-only history")
    p.add_argument("report", type=Path)
    p.add_argument("--history", type=Path, default=Path("evidence"))
    args = parser.parse_args()
    try:
        if args.command == "validate":
            registry = load_registry(args.root.resolve())
            print(f"Valid: {len(registry['requirements'])} requirements; {len(registry['tests'])} tests")
        elif args.command == "run":
            if args.timeout <= 0:
                raise InvalidData("Timeout must be positive")
            _, code = run(args.root.resolve(), args.veir.resolve(), args.out, scopes=args.scope,
                          timeout=args.timeout, profile=args.profile, reference_revision=args.reference_revision)
            return code
        elif args.command == "parse":
            from .parsing import run_parsing
            _, code = run_parsing(args.root, args.veir, args.mlir_opt, args.out, args.timeout)
            return code
        elif args.command == "report-check":
            from .history import validate_receipt
            report = validate_receipt(read_json(args.report))
            print(json.dumps({"id": report["id"], "complete": report["complete"], "cohort": report.get("cohort")}))
            return 0 if report["complete"] else 2
        elif args.command == "compare":
            failures = regressions(read_json(args.before), read_json(args.after))
            print(json.dumps({"regressions": failures}, indent=2))
            return int(bool(failures))
        elif args.command == "site":
            from .site import build_site
            build_site(args.root.resolve(), args.history.resolve(), args.out.resolve())
        elif args.command == "native":
            from .native import run_native
            _, code = run_native(args.veir.resolve(), args.out, lake=args.lake, lit=args.lit, jobs=args.jobs)
            return code
        elif args.command == "record":
            from .history import record_receipt
            print(record_receipt(args.report, args.history))
        return 0
    except (InvalidData, OSError, KeyError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
