"""Complete manifests, immutable receipts and reproducible comparison cohorts."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import shutil
import traceback
import uuid

from .checks import check
from .model import InvalidData, digest, file_digest, git_identity, load_registry, summarize, MEASURED
from .process import execute
from .measurement import measurement_cohort

TOOL_ENV = {"veir_opt": "VEIR_OPT", "veir_interpret": "VEIR_INTERPRET", "mlir_opt": "MLIR_OPT",
            "mlir_translate": "MLIR_TRANSLATE", "lli": "LLI"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def identify_tools(veir: Path) -> tuple[dict, dict]:
    paths, identities = {}, {}
    for name, variable in TOOL_ENV.items():
        default = str(veir / ".lake/build/bin" / name.replace("_", "-")) if name.startswith("veir_") else name.replace("_", "-")
        path = shutil.which(os.environ.get(variable, default))
        paths[name] = str(Path(path).resolve()) if path else None
        identity = {"path": paths[name], "sha256": file_digest(Path(path)) if path else None}
        if path and not name.startswith("veir_"):
            version = execute([path, "--version"], cwd=veir, timeout=5, output_limit=8192)
            identity["version"] = (version["stdout"] + version["stderr"]).strip()
            identity["version_ok"] = version["kind"] == "exit" and version["exit_code"] == 0
        identities[name] = identity
    return paths, identities


def harness_identity(root: Path) -> str:
    # Presentation and history-download changes cannot reset a measurement line.
    # Generated inputs/expectations are already included in the registry digest.
    files = [root / "veir_suite" / name for name in ["checks.py", "measurement.py", "model.py", "process.py", "runner.py"]]
    return digest([[str(p.relative_to(root)), file_digest(p)] for p in sorted(files)])


def select_registry(registry: dict, scopes: list[str]) -> dict:
    if not scopes:
        return registry
    if set(scopes) - {s["id"] for s in registry["scopes"]}:
        raise InvalidData("Unknown scope selection")
    selected = dict(registry)
    selected["scopes"] = [s for s in registry["scopes"] if s["id"] in scopes]
    selected["requirements"] = [r for r in registry["requirements"] if r["scope"] in scopes]
    ids = {t for r in selected["requirements"] for t in r["test_ids"]}
    selected["tests"] = [t for t in registry["tests"] if t["id"] in ids]
    return selected


def run(root: Path, veir: Path, out: Path, *, scopes=(), timeout=15.0, profile="local", reference_revision="unknown") -> tuple[dict, int]:
    registry = select_registry(load_registry(root), list(scopes))
    if not registry["tests"]:
        raise InvalidData("This selection has no executable tests; inspect its decision/test backlog in the site")
    paths, tools = identify_tools(veir)
    source = {"suite": git_identity(root), "veir": git_identity(veir)}
    harness = harness_identity(root)
    reference = {k: {"sha256": v["sha256"], "version": v.get("version"), "version_ok": v.get("version_ok")}
                 for k, v in tools.items() if not k.startswith("veir_")}
    profile_data = {"label": profile, "reference_revision": reference_revision, "tools": reference,
                    "platform": platform.system(), "machine": platform.machine(), "timeout_seconds": timeout}
    cohort = measurement_cohort(registry, harness, profile_data)
    id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    directory = out.resolve() / id
    directory.mkdir(parents=True, exist_ok=False)
    receipt = {"schema_version": 2, "id": id, "started_at": utc_now(), "finished_at": None,
               "cohort": cohort, "registry_sha256": digest(registry), "harness_sha256": harness,
               "sources": source, "tools": tools, "profile": profile_data,
               "registry": registry, "results": [], "complete": False}
    (directory / "manifest.json").write_text(json.dumps(receipt, indent=2) + "\n")
    for index, test in enumerate(registry["tests"]):
        # The directory name is independent of user-controlled IDs or separators.
        work = directory / "cases" / f"{index:05d}"
        try:
            result = check(test, paths, root, work, timeout)
        except Exception as error:
            result = {"id": test["id"], "status": "HARNESS_ERROR", "message": f"{type(error).__name__}: {error}",
                      "steps": [], "seconds": 0.0, "input_sha256": test["input_sha256"]}
            work.mkdir(parents=True, exist_ok=True)
            (work / "harness-error.txt").write_text(traceback.format_exc())
            (work / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        result["artifact"] = str(work.relative_to(directory))
        receipt["results"].append(result)
        if (index + 1) % 25 == 0 or index + 1 == len(registry["tests"]):
            print(f"{index+1}/{len(registry['tests'])}: {test['id']} {result['status']}", flush=True)
    receipt["summary"] = summarize(registry, receipt["results"])
    # A concurrent edit cannot silently attribute results to the wrong source or binary.
    unchanged = (git_identity(root) == source["suite"] and git_identity(veir) == source["veir"] and
                 harness_identity(root) == harness and digest(select_registry(load_registry(root), list(scopes))) == receipt["registry_sha256"])
    unchanged = unchanged and all(not p or file_digest(Path(p)) == tools[k]["sha256"] for k, p in paths.items())
    receipt["source_unchanged_during_run"] = unchanged
    receipt["complete"] = unchanged and all(r["status"] in MEASURED for r in receipt["results"])
    receipt["finished_at"] = utc_now()
    receipt["measurement_note"] = "Complete means all selected checks produced usable observations. It does not mean the tests passed, the contract is approved, or the program is proved correct."
    temporary = directory / "report.json.tmp"
    temporary.write_text(json.dumps(receipt, indent=2) + "\n")
    temporary.replace(directory / "report.json")
    print(json.dumps({"report": str(directory / "report.json"), "complete": receipt["complete"],
                      "tests": receipt["summary"]["test_counts"], "requirements": receipt["summary"]["requirements"],
                      "satisfied": receipt["summary"]["satisfied"]}, indent=2), flush=True)
    return receipt, 2 if not receipt["complete"] else 1 if any(r["status"] != "PASS" for r in receipt["results"]) else 0


def validate_report(report: dict) -> dict:
    if type(report.get("schema_version")) is not int or report["schema_version"] not in {1, 2}:
        raise InvalidData("Unknown report schema")
    registry = report["registry"]
    if digest(registry) != report.get("registry_sha256"):
        raise InvalidData("Report registry hash mismatch")
    cohort = measurement_cohort(registry, report["harness_sha256"], report["profile"], version=report["schema_version"])
    if cohort != report.get("cohort"):
        raise InvalidData("Report cohort mismatch")
    summary = summarize(registry, report["results"])
    if summary != report.get("summary"):
        raise InvalidData("Stored summary does not match its evidence")
    expected = {t["id"]: t for t in registry["tests"]}
    if any(r.get("input_sha256") != expected[r["id"]]["input_sha256"] for r in report["results"]):
        raise InvalidData("Result refers to a stale fixture")
    complete = report.get("source_unchanged_during_run") is True and all(r["status"] in MEASURED for r in report["results"])
    if report.get("complete") is not complete:
        raise InvalidData("False completion claim")
    if not report.get("finished_at") or not report.get("id"):
        raise InvalidData("Incomplete report metadata")
    return report


def regressions(before: dict, after: dict) -> list[str]:
    validate_report(before)
    validate_report(after)
    if before["cohort"] != after["cohort"]:
        raise InvalidData("Cannot compare different contracts, harnesses or reference profiles; establish a new baseline")
    if not before["complete"] or not after["complete"]:
        raise InvalidData("Regression comparison needs two complete measurements")
    previous = {r["id"]: r["status"] for r in before["results"]}
    return [r["id"] for r in after["results"] if previous[r["id"]] == "PASS" and r["status"] != "PASS"]
