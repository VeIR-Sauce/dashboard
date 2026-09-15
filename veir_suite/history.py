"""Validated receipt history shared by recording, CI gates and presentation."""
from __future__ import annotations

from pathlib import Path
import re

from .model import InvalidData, read_json
from .runner import validate_report
from .native import validate_native
from .parsing import validate_parsing


def validate_receipt(report: dict) -> dict:
    if report.get("kind") == "veir-parsing":
        return validate_parsing(report)
    return (validate_native if report.get("kind") == "veir-native" else validate_report)(report)


def receipt_filename(report: dict) -> str:
    if report.get("kind") == "veir-parsing":
        return "parsing.json"
    return "native.json" if report.get("kind") == "veir-native" else "report.json"


def check_receipt_id(report: dict) -> str:
    identifier = report.get("id")
    if not isinstance(identifier, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", identifier):
        raise InvalidData("Invalid receipt ID")
    return identifier


def _read(path: Path, filename: str, validator) -> list[dict]:
    reports, identifiers = [], set()
    for source in sorted(path.rglob(filename)) if path.exists() else []:
        report = validator(read_json(source))
        identifier = check_receipt_id(report)
        if identifier in identifiers:
            raise InvalidData("Invalid or duplicate run ID in history")
        identifiers.add(identifier)
        reports.append(report)
    return sorted(reports, key=lambda report: (report["finished_at"], report["id"]))


def read_history(path: Path) -> list[dict]:
    return _read(path, "report.json", validate_report)


def read_native_history(path: Path) -> list[dict]:
    return _read(path, "native.json", validate_native)


def read_parsing_history(path: Path) -> list[dict]:
    return _read(path, "parsing.json", validate_parsing)


def read_all_history(path: Path) -> tuple[list[dict], list[dict]]:
    reports, native = read_history(path), read_native_history(path)
    if {r["id"] for r in reports} & {r["id"] for r in native}:
        raise InvalidData("Contract and native receipts reuse the same ID")
    return reports, native


def previous_complete(history: list[dict], current: dict, cohort) -> dict | None:
    candidates = [report for report in history
                  if report["complete"] and report["id"] != current["id"]
                  and report["finished_at"] < current["finished_at"]
                  and cohort(report) == cohort(current)]
    return max(candidates, key=lambda report: (report["finished_at"], report["id"]), default=None)


def record_receipt(source: Path, history: Path) -> Path:
    report = validate_receipt(read_json(source))
    identifier = check_receipt_id(report)
    filename = receipt_filename(report)
    directory = history / identifier
    if any((directory / name).exists() for name in ["report.json", "native.json", "parsing.json"] if name != filename):
        raise InvalidData("Receipt ID already belongs to a different kind of measurement")
    target = directory / filename
    if not target.resolve().is_relative_to(history.resolve()):
        raise InvalidData("Receipt destination escapes through a symlink")
    contract, native = read_all_history(history)
    if not target.exists() and any(item['id'] == identifier for item in contract + native + read_parsing_history(history)):
        raise InvalidData("Receipt ID already exists at a different history path")
    payload = source.read_bytes()
    if target.exists():
        if target.read_bytes() != payload:
            raise InvalidData("Refusing to replace a different receipt with the same ID")
        return target
    directory.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as stream:
        stream.write(payload)
    return target
