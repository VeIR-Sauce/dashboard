#!/usr/bin/env python3
"""Snapshot existing LLVM round-trip fixtures with their original provenance."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--veir", type=Path, required=True)
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = p.parse_args()
    revision = subprocess.check_output(["git", "--no-lazy-fetch", "-C", str(args.veir), "rev-parse", "HEAD"], text=True).strip()
    tests, requirements = [], []
    target = args.root / "cases/upstream"
    target.mkdir(parents=True, exist_ok=True)
    for source in sorted((args.veir / "Test/LLVM").glob("*.mlir")):
        content = source.read_text()
        if "// RUN: MLIR_ROUNDTRIP\n" not in content:
            continue
        relative = f"cases/upstream/{source.name}"
        (args.root / relative).write_text(content)
        ops = sorted(set(re.findall(r'"(llvm\.[a-zA-Z0-9_.]+)"\(', content)))
        provenance = {"revision": revision, "path": str(source.relative_to(args.veir)),
                      "url": f"https://github.com/opencompl/veir/blob/{revision}/{source.relative_to(args.veir)}"}
        for stage, kind in [("verification", "verify"), ("roundtrip", "roundtrip")]:
            id = f"upstream.{source.stem}.{stage}"
            req = {"id": id, "title": source.stem.replace("_", " ") + " · " + stage,
                   "scope": "llvm-compat", "stage": stage, "state": "specified", "operations": ops, "source_groups": [],
                   "test_ids": [id + ".fixture"], "provenance": provenance,
                   "contract": "Both tools accept the original upstream fixture with registered LLVM operations." if kind == "verify" else
                   "Preserve all properties and structure of this pinned upstream fixture through strict VeIR parsing/printing, as judged by independent canonical MLIR and stable VeIR reprinting. This is a file-level contract, not complete operation semantics."}
            requirements.append(req)
            test = {"id": id + ".fixture", "kind": kind, "input": relative,
                    "input_sha256": hashlib.sha256(content.encode()).hexdigest()}
            if kind == "verify": test["expect"] = "accept"
            tests.append(test)
    output = args.root / "requirements/imports/native.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"schema_version": 1, "source_revision": revision, "requirements": requirements, "tests": tests}, indent=2) + "\n")
    print(f"Imported {len(tests)//2} upstream fixtures with separate verification and preservation contracts")


if __name__ == "__main__": main()
