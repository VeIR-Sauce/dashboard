"""Validate the human-readable registry and identify the exact tested sources."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

SCHEMA_VERSION = 1
STAGES = {"verification", "roundtrip", "execution", "transformation", "regression", "proof"}
KINDS = {"verify", "roundtrip", "interpret", "differential", "pipeline"}
RESULTS = {"PASS", "FAIL", "MISSING_CAPABILITY", "ORACLE_ERROR", "HARNESS_ERROR", "ENV_ERROR", "CRASH", "TIMEOUT", "OUTPUT_LIMIT", "NOT_RUN"}
MEASURED = {"PASS", "FAIL", "MISSING_CAPABILITY"}
ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/-]*$")


class InvalidData(ValueError):
    """A malformed contract or report must not become a successful result."""


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def file_digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def parse_json(text: str, source: str = "JSON") -> dict:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise InvalidData(f"Duplicate JSON key: {key}")
            result[key] = value
        return result
    try:
        result = json.loads(text, object_pairs_hook=unique)
    except json.JSONDecodeError as error:
        raise InvalidData(f"Cannot parse {source}: {error}") from error
    if not isinstance(result, dict):
        raise InvalidData(f"Expected an object in {source}")
    return result


def read_json(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise InvalidData(f"Cannot read {path}: {error}") from error
    return parse_json(text, str(path))


def safe_path(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise InvalidData(f"Expected a relative path: {relative!r}")
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise InvalidData(f"Path escapes repository: {relative}")
    return path


def _index(items: list, label: str) -> dict:
    if not isinstance(items, list):
        raise InvalidData(f"{label} must be a list")
    result = {}
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not ID.fullmatch(item["id"]):
            raise InvalidData(f"Invalid {label} ID: {item!r}")
        if item["id"] in result:
            raise InvalidData(f"Duplicate {label} ID: {item['id']}")
        result[item["id"]] = item
    return result


def load_registry(root: Path) -> dict:
    registry = read_json(root / "requirements/registry.json")
    if registry.get("schema_version") != SCHEMA_VERSION:
        raise InvalidData("Unsupported registry schema")
    scopes = _index(registry.get("scopes"), "scope")
    if "all" in scopes:
        raise InvalidData("The scope ID 'all' is reserved for the aggregate view")
    requirements = _index(registry.get("requirements"), "requirement")
    tests = _index(registry.get("tests"), "test")
    for requirement in requirements.values():
        if requirement.get("scope") not in scopes or requirement.get("stage") not in STAGES:
            raise InvalidData(f"Invalid scope/stage: {requirement['id']}")
        if not requirement.get("contract") or not requirement.get("title"):
            raise InvalidData(f"Missing requirement contract: {requirement['id']}")
        if requirement.get("state") not in {"specified", "needs_tests", "needs_decision"}:
            raise InvalidData(f"Invalid requirement state: {requirement['id']}")
        ids = requirement.get("test_ids")
        if not isinstance(ids, list) or len(set(ids)) != len(ids) or any(x not in tests for x in ids):
            raise InvalidData(f"Invalid test mapping: {requirement['id']}")
        if requirement["state"] == "specified" and not ids:
            raise InvalidData(f"Specified requirement has no tests: {requirement['id']}")
    linked = {t for requirement in requirements.values() for t in requirement["test_ids"]}
    if linked != set(tests):
        raise InvalidData(f"Unmapped tests: {sorted(set(tests) - linked)}")
    for test in tests.values():
        if test.get("kind") not in KINDS:
            raise InvalidData(f"Invalid check kind: {test['id']}")
        path = safe_path(root, test.get("input"))
        if not path.is_file():
            raise InvalidData(f"Missing fixture: {test['id']}: {path}")
        if file_digest(path) != test.get("input_sha256"):
            raise InvalidData(f"Fixture digest mismatch: {test['id']}; regenerate the registry deliberately")
        if test["kind"] == "verify":
            if type(test.get("reference", True)) is not bool:
                raise InvalidData(f"Invalid reference switch: {test['id']}")
            if test.get("expect") not in {"accept", "reject"}:
                raise InvalidData(f"Missing verifier expectation: {test['id']}")
            if test["expect"] == "reject":
                for side in ["veir", "reference"] if test.get("reference", True) else ["veir"]:
                    if not test.get("diagnostics", {}).get(side):
                        raise InvalidData(f"Negative test lacks {side} diagnostic: {test['id']}")
                    try:
                        re.compile(test["diagnostics"][side])
                    except re.error as error:
                        raise InvalidData(f"Invalid diagnostic expression: {test['id']}") from error
        if test["kind"] == "interpret" and not isinstance(test.get("expected_result"), dict):
            raise InvalidData(f"Missing semantic expectation: {test['id']}")
        if test["kind"] == "pipeline" and not test.get("pipeline"):
            raise InvalidData(f"Missing pass pipeline: {test['id']}")
        if test["kind"] in {"differential", "pipeline"}:
            width = test.get("result_width")
            if type(width) is not int or not 1 <= width <= 256:
                raise InvalidData(f"Invalid reference result width: {test['id']}")
            if test.get("defined_behavior") is not True:
                raise InvalidData(f"Differential execution needs an explicit defined-behavior contract: {test['id']}")
        if "expected_result" in test:
            from .checks import parse_interpreter_json, CheckFailure
            try:
                expected = parse_interpreter_json(json.dumps(test["expected_result"]))
            except CheckFailure as error:
                raise InvalidData(f"Invalid semantic expectation for {test['id']}: {error.message}") from error
            if expected["outcome"] == "unsupported_interpretation":
                raise InvalidData("An unsupported interpreter cannot satisfy a capability contract")
            if test["kind"] in {"differential", "pipeline"}:
                values = expected["results"]
                if expected["outcome"] != "ok" or len(values) != 1 or values[0].get("kind") != "int" or values[0].get("width") != test["result_width"] or "value" not in values[0]:
                    raise InvalidData(f"Defined reference execution requires one concrete integer result: {test['id']}")
    return registry


def git_identity(path: Path) -> dict:
    def git(*args):
        return subprocess.check_output(["git", "--no-lazy-fetch", "--no-optional-locks", "-C", str(path), *args])
    try:
        head = git("rev-parse", "HEAD").decode().strip()
        names = git("ls-files", "--cached", "--others", "--exclude-standard", "-z").decode().split("\0")
        files = []
        for name in sorted(set(filter(None, names))):
            p = path / name
            if p.is_symlink():
                files.append([name, "symlink", str(p.readlink())])
            elif p.is_file():
                files.append([name, file_digest(p)])
            else:
                files.append([name, "absent"])
        return {"commit": head, "dirty": bool(git("status", "--porcelain")),
                "source_digest": digest(files), "file_count": len(files)}
    except (OSError, subprocess.CalledProcessError) as error:
        raise InvalidData(f"Cannot identify source repository {path}: {error}") from error


def summarize(registry: dict, results: list[dict]) -> dict:
    expected = {test["id"] for test in registry["tests"]}
    indexed = _index(results, "result")
    if set(indexed) != expected:
        raise InvalidData(f"Result set differs from selected tests; missing={sorted(expected-set(indexed))}, extra={sorted(set(indexed)-expected)}")
    if any(row.get("status") not in RESULTS for row in results):
        raise InvalidData("Unknown result status")
    rows = []
    for req in registry["requirements"]:
        statuses = [indexed[t]["status"] for t in req["test_ids"]]
        covered = req["state"] == "specified" and bool(statuses) and all(s in MEASURED for s in statuses)
        satisfied = covered and all(s == "PASS" for s in statuses)
        rows.append({"id": req["id"], "scope": req["scope"], "stage": req["stage"],
                     "covered": covered, "satisfied": satisfied,
                     "needs_decision": req["state"] == "needs_decision", "test_statuses": statuses})
    return {"requirements": len(rows), "covered": sum(r["covered"] for r in rows),
            "satisfied": sum(r["satisfied"] for r in rows),
            "coverage_remaining": sum(not r["covered"] for r in rows),
            "conformance_remaining": sum(not r["satisfied"] for r in rows),
            "needs_decision": sum(r["needs_decision"] for r in rows),
            "test_counts": {status: sum(r["status"] == status for r in results) for status in sorted(RESULTS)},
            "rows": rows}
