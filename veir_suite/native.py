"""Account for the existing VeIR suite without equating it to feature coverage."""
from __future__ import annotations
from collections import Counter
import json
import os
import platform
from pathlib import Path
import subprocess
import shutil
import uuid

from .model import InvalidData, digest, file_digest, git_identity, read_json
from .process import execute
from .runner import utc_now

NATIVE_CODES = {"PASS", "FAIL", "XFAIL", "XPASS", "UNSUPPORTED", "UNRESOLVED", "TIMEOUT", "EXCLUDED", "SKIPPED"}


def native_harness() -> str:
    root = Path(__file__).resolve().parent
    return digest([[name, file_digest(root / name)] for name in ["native.py", "process.py", "model.py"]])


def native_cohort(report: dict) -> str:
    return digest({"manifest": report["manifest_sha256"], "harness": report.get("harness_sha256"),
                   "profile": report.get("profile"),
                   "tools": {k: v["sha256"] for k, v in report.get("tools", {}).items()}})


def native_completion(report: dict) -> bool:
    """One completion rule for both the writer and the receipt reader."""
    expected = {"VeIR :: " + row["path"][len("Test/"):] for row in report["manifest"]["lit"]}
    names = [test["name"] for test in report["tests"]]
    commands = report["commands"]
    if len(commands) != 4 or len(names) != len(set(names)) or set(names) != expected:
        return False
    if not all(row["kind"] == "exit" and row["exit_code"] == 0 for row in commands[:3]):
        return False
    if commands[-1]["kind"] != "exit" or commands[-1]["exit_code"] not in (0, 1):
        return False
    if report.get("source_unchanged_during_run") is not True:
        return False
    if report["schema_version"] == 2 and not all(report.get(key) is True for key in
            ["harness_unchanged_during_run", "binaries_unchanged_during_tests", "tools_unchanged_during_run"]):
        return False
    return not any(test["code"] in {"UNRESOLVED", "TIMEOUT", "SKIPPED", "EXCLUDED"} for test in report["tests"])


def validate_native(report: dict) -> dict:
    if type(report.get("schema_version")) is not int or report["schema_version"] not in {1, 2} or report.get("kind") != "veir-native":
        raise InvalidData("Unknown native receipt schema")
    manifest = report["manifest"]
    for category in ["lit", "lean_modules", "test_support"]:
        paths = [row["path"] for row in manifest.get(category, [])]
        if len(paths) != len(set(paths)) or any(Path(path).is_absolute() or ".." in Path(path).parts for path in paths):
            raise InvalidData("Invalid or duplicate native manifest paths")
    if not manifest.get("lit") or not manifest.get("lean_modules") or any(not row["path"].startswith("Test/") for row in manifest["lit"]):
        raise InvalidData("Native receipt lacks its source-test manifest")
    tests = report.get("tests", [])
    names = [test["name"] for test in tests]
    if len(names) != len(set(names)) or any(test["code"] not in NATIVE_CODES for test in tests):
        raise InvalidData("Invalid native test results")
    if report.get("manifest_sha256") != digest(manifest):
        raise InvalidData("Native manifest digest mismatch")
    if report.get("counts") != dict(sorted(Counter(test["code"] for test in tests).items())):
        raise InvalidData("Native counts disagree with test evidence")
    if report.get("complete") is not native_completion(report):
        raise InvalidData("False native completion claim")
    return report


def veir_binary_hashes(veir: Path) -> dict:
    return {name: file_digest(veir / ".lake/build/bin" / name)
            for name in ["veir-opt", "veir-interpret", "veir2mir", "run-benchmarks"]
            if (veir / ".lake/build/bin" / name).is_file()}


def run_native(veir: Path, out: Path, *, lake: str, lit: str, jobs: int = 2) -> tuple[dict, int]:
    source = git_identity(veir)
    harness = native_harness()
    files = subprocess.check_output(["git", "--no-lazy-fetch", "--no-optional-locks", "-C", str(veir), "ls-files", "--cached", "--others", "--exclude-standard", "-z"], text=True).split("\0")
    manifest = {"lit": [], "lean_modules": [], "test_support": []}
    for name in sorted(set(files)):
        path = veir / name
        if name.startswith("Test/") and path.suffix in {".mlir", ".ll", ".c"}:
            manifest["lit"].append({"path": name, "sha256": file_digest(path)})
        if (name == "UnitTest.lean" or name.startswith("UnitTest/")) and path.suffix == ".lean":
            manifest["lean_modules"].append({"path": name, "sha256": file_digest(path)})
        if (name.startswith("Test/") and (path.suffix == ".py" or path.name in {"lit.cfg", "lit.local.cfg"})) or name == "Tools/veir_lit.py":
            manifest["test_support"].append({"path": name, "sha256": file_digest(path)})
    id = "native-" + utc_now().replace(":", "").replace("-", "") + "-" + uuid.uuid4().hex[:8]
    directory = out.resolve() / id
    directory.mkdir(parents=True, exist_ok=False)
    env = os.environ.copy()
    env["VEIR_REQUIRE_MLIR"] = "1"
    env["ELAN_TOOLCHAIN"] = (veir / "lean-toolchain").read_text().strip()
    lake_path = shutil.which(lake)
    if not lake_path:
        raise InvalidData(f"Lake is unavailable: {lake}")
    # Tools/vcc invokes lake itself. Append its directory so an explicitly
    # selected host clang still takes precedence over Lean's bundled clang.
    env["PATH"] = env.get("PATH", "") + os.pathsep + str(Path(lake_path).parent)
    report = {"schema_version": 2, "kind": "veir-native", "id": id, "started_at": utc_now(), "source": source,
              "suite_source": git_identity(Path(__file__).resolve().parents[1]), "harness_sha256": harness,
              "manifest": manifest, "manifest_sha256": digest(manifest), "commands": [], "tests": [], "tools": {},
              "profile": {"lean_toolchain": env["ELAN_TOOLCHAIN"], "platform": platform.system(),
                          "machine": platform.machine(), "jobs": jobs}}
    for name in [lake, lit, "mlir-opt", "mlir-translate", "clang", "opt"]:
        resolved = shutil.which(name, path=env["PATH"])
        report["tools"][Path(name).name] = {"path": resolved, "sha256": file_digest(Path(resolved)) if resolved else None}
    built_binaries = None
    for command, cwd, limit in [([lake, "build"], veir, 1800), ([lake, "test"], veir, 900),
                                ([lake, "exe", "test"], veir / "ExArray", 900),
                                ([lit, "Test", "-j", str(jobs), "--timeout=30", "-o", str(directory / "lit.json")], veir, 1200)]:
        print("Running " + " ".join(command), flush=True)
        report["commands"].append(execute(command, cwd=cwd, env=env, timeout=limit, output_limit=8*1024*1024))
        if len(report["commands"]) == 1:
            built_binaries = veir_binary_hashes(veir)
    if (directory / "lit.json").exists():
        report["tests"] = read_json(directory / "lit.json")["tests"]
    expected = {"VeIR :: " + row["path"][len("Test/"):] for row in manifest["lit"]}
    actual = {row["name"] for row in report["tests"]}
    report["missing"] = sorted(expected - actual)
    report["unexpected"] = sorted(actual - expected)
    report["source_unchanged_during_run"] = source == git_identity(veir)
    report["harness_unchanged_during_run"] = harness == native_harness()
    report["veir_binaries"] = veir_binary_hashes(veir)
    report["binaries_unchanged_during_tests"] = bool(built_binaries) and built_binaries == report["veir_binaries"]
    report["tools_unchanged_during_run"] = all(
        not tool["path"] or (Path(tool["path"]).is_file() and file_digest(Path(tool["path"])) == tool["sha256"])
        for tool in report["tools"].values())
    report["counts"] = dict(sorted(Counter(t["code"] for t in report["tests"]).items()))
    report["complete"] = native_completion(report)
    report["finished_at"] = utc_now()
    validate_native(report)
    (directory / "native.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"report": str(directory / "native.json"), "complete": report["complete"], "counts": report["counts"],
                      "lean_source_modules": len(manifest["lean_modules"]), "missing": report["missing"]}, indent=2), flush=True)
    return report, 2 if not report["complete"] else 1 if any(c in report["counts"] for c in ["FAIL", "XPASS"]) else 0
