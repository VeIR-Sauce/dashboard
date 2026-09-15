"""Independent verification, preservation and execution checks."""
from __future__ import annotations

import json
from pathlib import Path
import re

from .process import execute, process_problem


class CheckFailure(Exception):
    def __init__(self, status: str, message: str):
        self.status, self.message = status, message


def parse_interpreter_json(text: str) -> dict:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate field: {key}")
            result[key] = value
        return result
    try:
        result = json.loads(text, object_pairs_hook=unique)
    except ValueError as error:
        raise CheckFailure("HARNESS_ERROR", f"Interpreter did not produce one JSON result: {error}") from error
    if not isinstance(result, dict) or set(result) != {"schema_version", "outcome", "results"}:
        raise CheckFailure("HARNESS_ERROR", "Invalid interpreter result fields")
    if type(result["schema_version"]) is not int or result["schema_version"] != 1 or result["outcome"] not in {"ok", "undefined_behavior", "unsupported_interpretation"}:
        raise CheckFailure("HARNESS_ERROR", "Unknown interpreter result version/outcome")
    if not isinstance(result["results"], list) or (result["outcome"] != "ok" and result["results"]):
        raise CheckFailure("HARNESS_ERROR", "Invalid interpreter result list")
    for value in result["results"]:
        if not isinstance(value, dict) or value.get("kind") not in {"int", "float", "byte", "address", "register", "felt"}:
            raise CheckFailure("HARNESS_ERROR", "Unrecognized typed runtime value")
        if value["kind"] != "felt":
            width = value.get("width")
            if type(width) is not int or not 0 <= width <= 1048576:
                raise CheckFailure("HARNESS_ERROR", "Invalid result width")
            for field in ("value", "bits", "poison_mask"):
                if field in value:
                    number = value[field]
                    if not isinstance(number, str) or len(number) > 4096 or not re.fullmatch(r"0|[1-9][0-9]*", number) or int(number) >= 1 << width:
                        raise CheckFailure("HARNESS_ERROR", f"Invalid {field} for i{width}")
        if value["kind"] == "int":
            keys = set(value)
            if keys == {"kind", "width", "poison"}:
                if value["poison"] is not True:
                    raise CheckFailure("HARNESS_ERROR", "Invalid poison marker")
            elif keys != {"kind", "width", "value"}:
                raise CheckFailure("HARNESS_ERROR", "Invalid integer result fields")
        else:
            fields = {"byte": {"kind", "width", "value", "poison_mask"},
                      "float": {"kind", "type", "width", "bits"},
                      "address": {"kind", "width", "value"}, "register": {"kind", "width", "value"},
                      "felt": {"kind", "type", "value"}}[value["kind"]]
            if set(value) != fields:
                raise CheckFailure("HARNESS_ERROR", "Invalid typed result fields")
            if value["kind"] in {"address", "register"} and value["width"] != 64:
                raise CheckFailure("HARNESS_ERROR", "Invalid address/register width")
            if "type" in fields and (not isinstance(value["type"], str) or not value["type"]):
                raise CheckFailure("HARNESS_ERROR", "Missing runtime type")
            if value["kind"] == "felt" and (not isinstance(value["value"], str) or not re.fullmatch(r"0|[1-9][0-9]*", value["value"])):
                raise CheckFailure("HARNESS_ERROR", "Invalid field representative")
    return result


def reference_wrapper(llvm_ir: str, width: int) -> str:
    """Wrap the original translated program; emit all bits rather than exit status."""
    if not 1 <= width <= 256:
        raise CheckFailure("HARNESS_ERROR", "Reference wrapper supports integer results of 1–256 bits")
    declarations = re.findall(r"^define\b[^\n{]*\bi([0-9]+)\s+@main\(\)", llvm_ir, re.MULTILINE)
    if declarations != [str(width)]:
        raise CheckFailure("HARNESS_ERROR", "Reference input must define exactly main() with the declared integer result")
    if any(name in llvm_ir for name in ["@__veir_subject", "@__veir_format", "@printf"]):
        raise CheckFailure("HARNESS_ERROR", "Reference wrapper symbol collision")
    subject = llvm_ir.replace("@main(", "@__veir_subject(")
    chunks = (width + 63) // 64
    fmt = "VEIR-RESULT " + str(width) + " %llu" * chunks + "\n"
    escaped = fmt.replace("\n", "\\0A") + "\\00"
    body = [f"  %value = call i{width} @__veir_subject()"]
    arguments = []
    for index in range(chunks):
        value = "%value"
        if index:
            value = f"%shift{index}"
            body.append(f"  {value} = lshr i{width} %value, {64 * index}")
        if width != 64:
            converted = f"%word{index}"
            cast = "zext" if width < 64 else "trunc"
            body.append(f"  {converted} = {cast} i{width} {value} to i64")
            value = converted
        arguments.append(f"i64 {value}")
    body.append("  %written = call i32 (ptr, ...) @printf(ptr @__veir_format, " + ", ".join(arguments) + ")")
    body.append("  ret i32 0")
    return subject + f'\n@__veir_format = private constant [{len(fmt)+1} x i8] c"{escaped}"\n' + \
        "declare i32 @printf(ptr, ...)\ndefine i32 @main() {\n" + "\n".join(body) + "\n}\n"


def parse_reference_result(text: str, width: int) -> dict:
    match = re.fullmatch(r"VEIR-RESULT ([0-9]+)((?: [0-9]+)+)\n?", text)
    if not match or int(match[1]) != width:
        raise CheckFailure("HARNESS_ERROR", "Invalid reference result protocol")
    words = [int(x) for x in match[2].split()]
    if len(words) != (width + 63) // 64 or any(x >= 1 << 64 for x in words):
        raise CheckFailure("HARNESS_ERROR", "Truncated or oversized reference result")
    value = sum(word << (64 * index) for index, word in enumerate(words))
    if value >= 1 << width:
        raise CheckFailure("HARNESS_ERROR", "Reference result exceeds its declared width")
    return {"schema_version": 1, "outcome": "ok", "results": [{"kind": "int", "width": width, "value": str(value)}]}


def check(test: dict, tools: dict, root: Path, work: Path, timeout: float) -> dict:
    work.mkdir(parents=True, exist_ok=False)
    source = (root / test["input"]).read_text()
    input_path = work / "input.mlir"
    input_path.write_text(source)
    result = {"id": test["id"], "status": "NOT_RUN", "message": "", "steps": [], "input_sha256": test["input_sha256"]}

    def run(tool: str, arguments: list[str], phase: str) -> dict:
        if not tools.get(tool):
            raise CheckFailure("ENV_ERROR", f"Missing required tool: {tool}")
        record = execute([tools[tool], *arguments], cwd=work, timeout=timeout)
        record["phase"] = phase
        result["steps"].append(record)
        problem = process_problem(record)
        if problem:
            raise CheckFailure(problem, f"{phase}: {record['kind']}")
        return record

    def accept(record: dict, *, reference: bool = False) -> None:
        if record["exit_code"]:
            text = record["stderr"] + record["stdout"]
            if not reference and re.search(r"is not registered|unregistered op|unsupported top-level", text):
                raise CheckFailure("MISSING_CAPABILITY", f"{record['phase']}: required capability unavailable")
            raise CheckFailure("ORACLE_ERROR" if reference else "FAIL", f"{record['phase']}: expected success, exit {record['exit_code']}")

    def verify_record(record: dict, side: str) -> None:
        if test["expect"] == "accept":
            accept(record, reference=side == "reference")
        else:
            if record["exit_code"] != 1:
                raise CheckFailure("ORACLE_ERROR" if side == "reference" else "FAIL", f"{side}: expected ordinary rejection, got exit {record['exit_code']}")
            diagnostic = record["stderr"] + record["stdout"]
            if not re.search(test["diagnostics"][side], diagnostic, re.IGNORECASE):
                raise CheckFailure("ORACLE_ERROR" if side == "reference" else "FAIL", f"{side}: rejected for an unexpected reason")

    def interpret(path: Path) -> dict:
        record = run("veir_interpret", ["--json", str(path)], "veir.execution")
        parsed = parse_interpreter_json(record["stdout"]) if record["stdout"].strip() else None
        if parsed and parsed["outcome"] == "unsupported_interpretation":
            raise CheckFailure("MISSING_CAPABILITY", "VeIR reports unsupported interpretation")
        accept(record)
        if parsed is None:
            raise CheckFailure("HARNESS_ERROR", "VeIR returned no machine-readable result")
        return parsed

    def reference_execution() -> dict:
        verified = run("mlir_opt", [str(input_path)], "reference.verification")
        accept(verified, reference=True)
        translated = run("mlir_translate", ["--mlir-to-llvmir", str(input_path)], "reference.translation")
        accept(translated, reference=True)
        ll = work / "reference.ll"
        ll.write_text(reference_wrapper(translated["stdout"], test["result_width"]))
        executed = run("lli", [str(ll)], "reference.execution")
        accept(executed, reference=True)
        return parse_reference_result(executed["stdout"], test["result_width"])

    try:
        kind = test["kind"]
        if kind == "verify":
            if test.get("reference", True):
                verify_record(run("mlir_opt", [str(input_path)], "reference.verification"), "reference")
            verified = run("veir_opt", ["--print-op-generic", str(input_path)], "veir.verification")
            verify_record(verified, "veir")
        elif kind == "roundtrip":
            canonical_args = ["--mlir-print-op-generic", "--mlir-print-local-scope"]
            before = run("mlir_opt", [*canonical_args, str(input_path)], "reference.canonicalize-original")
            accept(before, reference=True)
            printed = run("veir_opt", ["--print-op-generic", str(input_path)], "veir.roundtrip")
            accept(printed)
            output = work / "printed.mlir"
            output.write_text(printed["stdout"])
            reparsed = run("veir_opt", ["--print-op-generic", str(output)], "veir.reparse")
            accept(reparsed)
            if reparsed["stdout"].strip() != printed["stdout"].strip():
                raise CheckFailure("FAIL", "VeIR generic printing is not stable on reparse")
            after = run("mlir_opt", [*canonical_args, str(output)], "reference.canonicalize-veir-output")
            accept(after)
            if before["stdout"].strip() != after["stdout"].strip():
                raise CheckFailure("FAIL", "Round-trip changed the reference's canonical IR")
        elif kind == "interpret":
            observed = interpret(input_path)
            result["observed_result"] = observed
            if observed != test["expected_result"]:
                raise CheckFailure("FAIL", "Typed execution result differs from the specified result")
        elif kind in {"differential", "pipeline"}:
            expected = reference_execution()
            result["reference_result"] = expected
            if "expected_result" in test and expected != test["expected_result"]:
                raise CheckFailure("ORACLE_ERROR", "Reference disagrees with the independently specified result")
            original = interpret(input_path)
            if original != expected:
                raise CheckFailure("FAIL", "VeIR execution differs from the independent reference path")
            if kind == "pipeline":
                optimized = run("veir_opt", ["--print-op-generic", "-p=" + test["pipeline"], str(input_path)], "veir.transformation")
                accept(optimized)
                output = work / "optimized.mlir"
                output.write_text(optimized["stdout"])
                checked = run("mlir_opt", [str(output)], "reference.verify-transformed")
                accept(checked)
                observed = interpret(output)
            else:
                observed = original
            result["observed_result"] = observed
            if observed != expected:
                raise CheckFailure("FAIL", "Transformed execution differs from the original reference program")
        result.update(status="PASS", message="All required checks satisfied")
    except CheckFailure as error:
        result.update(status=error.status, message=error.message)
    result["seconds"] = round(sum(step["seconds"] for step in result["steps"]), 6)
    (work / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    return result
