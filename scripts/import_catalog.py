#!/usr/bin/env python3
"""Import pinned TableGen inventories; registration is never called implementation."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ops", type=Path, required=True)
    p.add_argument("--intrinsics", type=Path, required=True)
    p.add_argument("--llvm-revision", required=True)
    p.add_argument("--veir", type=Path, required=True)
    p.add_argument("--out", type=Path, default=Path("requirements/catalog.json"))
    args = p.parse_args()
    if not re.fullmatch("[a-f0-9]{40}", args.llvm_revision):
        p.error("LLVM revision must be a full commit SHA")
    ops = {}
    sources = []
    for path in [args.ops, args.intrinsics]:
        data = json.loads(path.read_text())
        sources.append({"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        for key in data["!instanceof"]["Op"]:
            row = data[key]
            if row["opDialect"]["def"] != "LLVM_Dialect":
                continue
            name = "llvm." + row["opName"]
            location = row["!locs"][0]
            file, line = location.rsplit(":", 1)
            record = {"name": name, "definition": key, "summary": row.get("summary", "").strip(),
                      "url": f"https://github.com/llvm/llvm-project/blob/{args.llvm_revision}/mlir/include/mlir/Dialect/LLVMIR/{file}#L{line}"}
            if name in ops and ops[name] != record:
                raise ValueError(f"Conflicting operation: {name}")
            ops[name] = record
    source = (args.veir / "Veir/Dialects/LLVM/OpInfo.lean").read_text()
    constructors = source.split("inductive Llvm where", 1)[1].split("deriving", 1)[0]
    registered = {"llvm." + x.replace("__", ".") for x in re.findall(r"^\| ([a-z][a-z0-9_]*)\s*$", constructors, re.M)}
    for op in ops.values():
        op["registered_in_veir_snapshot"] = op["name"] in registered
    revision = subprocess.check_output(["git", "--no-lazy-fetch", "-C", str(args.veir), "rev-parse", "HEAD"], text=True).strip()
    result = {"schema_version": 1, "llvm_revision": args.llvm_revision, "veir_revision": revision,
              "source_dumps": sources, "scope": "LLVMOps.td and LLVMIntrinsicOps.td, excluding target-specific dialects and other MLIR dialects",
              "interpretation": "Candidate inventory. Registration is a source observation, not verifier, execution, or proof evidence. No full-MLIR parity commitment is implied.",
              "operations": sorted(ops.values(), key=lambda x: x["name"]),
              "veir_only_names": sorted(registered - ops.keys())}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(f"Imported {len(ops)} operations; {len(registered & ops.keys())} registered names in the VeIR snapshot")


if __name__ == "__main__":
    main()
