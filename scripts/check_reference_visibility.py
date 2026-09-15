#!/usr/bin/env python3
"""Exercise real lit discovery/worker behavior when the reference is unavailable."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--veir", type=Path, required=True)
parser.add_argument("--lit", required=True)
args = parser.parse_args()
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    tool = root / "mlir-opt"
    tool.write_text('#!/bin/sh\necho "LLVM version 999.0.0"\n')
    tool.chmod(0o755)
    env = os.environ.copy()
    env["PATH"] = str(root) + os.pathsep + env["PATH"]
    env.pop("VEIR_REQUIRE_MLIR", None)
    command = [args.lit, str(args.veir / "Test/LLVM/exact_disjoint.mlir"), "-j", "2", "-o", str(root / "lit.json")]
    optional = subprocess.run(command, env=env, capture_output=True, text=True, timeout=30)
    assert optional.returncode == 0, optional.stderr
    tests = json.loads((root / "lit.json").read_text())["tests"]
    assert len(tests) == 1 and tests[0]["code"] == "UNSUPPORTED", tests
    env["VEIR_REQUIRE_MLIR"] = "1"
    required = subprocess.run(command, env=env, capture_output=True, text=True, timeout=30)
    assert required.returncode != 0 and "unsupported" in required.stderr, required.stderr
print("Unavailable reference: optional lane is UNSUPPORTED; required lane fails discovery.")
