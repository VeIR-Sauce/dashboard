"""A self-contained, dependency-free GitHub Pages site with auditable downloads."""
from __future__ import annotations
import csv
import io
import gzip
import json
import re
from pathlib import Path
import shutil

from .model import InvalidData, load_registry, read_json
from .history import read_all_history, read_history, read_parsing_history
from .parsing import case_id, case_counts, counts, operation_results


def parsing_evidence(report: dict) -> list[dict]:
    """Positive examples whose successful VeIR invocation establishes parsing.

    A rejected negative case, registered name, or failed verifier invocation
    does not establish whether the parser accepts a positive input.
    """
    tests = {t["id"]: t for t in report["registry"].get("tests", [])}
    results = {r["id"]: r for r in report["results"]}
    observed = {}
    for requirement in report["registry"]["requirements"]:
        for test_id in requirement["test_ids"]:
            test, result = tests.get(test_id, {}), results.get(test_id, {})
            positive = test.get("kind") == "roundtrip" or (
                test.get("kind") == "verify" and test.get("expect") == "accept")
            parsed = positive and any(
                step.get("phase") in {"veir.verification", "veir.roundtrip"}
                and step.get("kind") == "exit" and step.get("exit_code") == 0
                for step in result.get("steps", []))
            if not parsed:
                continue
            for operation in requirement.get("operations", []):
                observed[(operation, test_id)] = {
                    "operation": operation, "test_id": test_id,
                    "requirement": requirement["id"], "input": test.get("input"),
                    "input_sha256": result.get("input_sha256"),
                }
    return [observed[key] for key in sorted(observed)]


def build_site(root: Path, history: Path, out: Path) -> None:
    root, history, out = root.resolve(), history.resolve(), out.resolve()
    if out == root or root.is_relative_to(out) or out == history or history.is_relative_to(out):
        raise InvalidData("Site output must not contain the source or evidence directory")
    registry = load_registry(root)
    reports, native = read_all_history(history)
    catalog = read_json(root / "requirements/catalog.json")
    sources = read_json(root / "requirements/sources/mathieu.json")
    out.mkdir(parents=True, exist_ok=True)
    downloads = out / "data"
    downloads.mkdir(exist_ok=True)
    compact, cohorts = [], {}
    latest_complete = {r["cohort"]: r["id"] for r in reports if r["complete"]}
    latest_attempt = {r["cohort"]: r["id"] for r in reports}
    for report in reports:
        detailed = report["id"] in {latest_complete.get(report["cohort"]), latest_attempt[report["cohort"]]}
        target = downloads / (report["id"] + (".json" if detailed else ".json.gz"))
        serialized = (json.dumps(report, indent=2) + "\n").encode()
        target.write_bytes(serialized if detailed else gzip.compress(serialized, mtime=0))
        item = {key: report[key] for key in ["id", "started_at", "finished_at", "complete", "cohort", "profile", "sources"]}
        cohorts[report["cohort"]] = report["registry"]
        item["counts_by_scope"] = {}
        for scope in ["all"] + [s["id"] for s in report["registry"]["scopes"]]:
            rows = [r for r in report["summary"]["rows"] if scope == "all" or r["scope"] == scope]
            item["counts_by_scope"][scope] = {"coverage_remaining": sum(not r["covered"] for r in rows),
                                              "conformance_remaining": sum(not r["satisfied"] for r in rows)}
        if detailed:
            item["summary"] = report["summary"]
            item["parsing"] = parsing_evidence(report)
            item["results"] = [{key: value for key, value in r.items() if key != "steps"} for r in report["results"]]
            for result, original in zip(item["results"], report["results"]):
                if result["status"] in {"FAIL", "MISSING_CAPABILITY"}:
                    failed_steps = [s for s in original.get("steps", []) if s.get("exit_code") not in (None, 0)]
                    if failed_steps:
                        step = failed_steps[-1]
                        diagnostic = step.get("stderr") or step.get("stdout") or ""
                        result["diagnostic"] = diagnostic[:1200]
                        result["diagnostic_phase"] = step.get("phase", "")
        # Per-case steps are available without exposing local file:// links.
        item["download"] = "data/" + target.name
        compact.append(item)
    native_entries = []
    latest_native = {native[-1]["id"]} if native else set()
    latest_complete_native = next((r for r in reversed(native) if r["complete"]), None)
    if latest_complete_native:
        latest_native.add(latest_complete_native["id"])
    for report in native:
        detailed = report["id"] in latest_native
        target = downloads / (report["id"] + (".json" if detailed else ".json.gz"))
        serialized = (json.dumps(report, indent=2) + "\n").encode()
        target.write_bytes(serialized if detailed else gzip.compress(serialized, mtime=0))
        item = {key: report[key] for key in ["id", "complete", "finished_at", "counts", "source"]}
        item.update(lit_file_count=len(report["manifest"]["lit"]),
                    lean_module_count=len(report["manifest"]["lean_modules"]),
                    download="data/" + target.name)
        native_entries.append(item)
    parsing_entries = []
    parsing_reports = read_parsing_history(history)
    identifiers = [r['id'] for r in reports + native + parsing_reports]
    if len(set(identifiers)) != len(identifiers):
        raise InvalidData('Different measurement kinds reuse the same receipt ID')
    for report in parsing_reports:
        target = downloads / (report['id'] + '.json')
        target.write_text(json.dumps(report, indent=2) + '\n')
        cases = {case_id(case): case for case in report['manifest']['cases']}
        rows = []
        inputs = downloads / report['id']; inputs.mkdir(exist_ok=True)
        operations = operation_results(report)
        for result in operations:
            if not re.fullmatch(r'llvm\.[a-z0-9_.]+', result['operation']):
                raise InvalidData('Invalid parsing operation name')
            row = {'operation': result['operation'], 'cases': [], **{mode: result[mode] for mode in ['strict', 'permissive']}}
            for observation in result['cases']:
                case = cases[observation['id']]
                filename = (case['operation'] if report['schema_version'] == 1 else case['id']) + '.mlir'
                (inputs / filename).write_text(case['text'])
                example = {'id': observation['id'], 'label': case.get('label', 'Baseline example')}
                example['input'] = {'download': f'data/{report["id"]}/{filename}',
                    'text': case['text'], 'sha256': case['input_sha256'],
                    'method': case['method'], 'source': case['source']}
                for mode in ['strict', 'permissive']:
                    value = observation[mode]
                    example[mode] = {'status': value['status'],
                        'diagnostic': value.get('step', {}).get('stderr', '')[:2000]}
                if observation.get('reference', {}).get('exit_code') != 0:
                    example['reference_diagnostic'] = observation.get('reference', {}).get('stderr', 'No validated example recorded')[:2000]
                row['cases'].append(example)
            rows.append(row)
        parsing_entries.append({key: report[key] for key in ['id', 'finished_at', 'complete', 'counts', 'source']} |
            {'download': 'data/' + target.name, 'llvm_revision': report['manifest']['llvm_revision'],
             'counts': counts(operations), 'case_counts': case_counts(operations), 'case_total': len(cases),
             'operations': report['manifest']['catalog']['operations'], 'results': rows})
    data = {"registry": registry, "catalog": catalog, "sources": sources, "reports": compact,
            "cohorts": cohorts, "native": native_entries, "parsing": parsing_entries}
    # Safe even if a diagnostic, title or source contains </script> or HTML.
    embedded = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    template = (root / "web/index.html").read_text()
    (out / "index.html").write_text(template.replace("__DATA__", embedded))
    for name in ["model.js", "app.js", "style.css"]:
        shutil.copyfile(root / "web" / name, out / name)
    (out / ".nojekyll").touch()
    for name, value in [("registry", registry), ("catalog", catalog), ("sources", sources)]:
        (downloads / f"{name}.json").write_text(json.dumps(value, indent=2) + "\n")
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(["id", "title", "scope", "stage", "state", "contract", "tests", "operations"])
    for req in registry["requirements"]:
        row = [req[k] for k in ["id", "title", "scope", "stage", "state", "contract"]] + [" ".join(req["test_ids"]), " ".join(req["operations"])]
        writer.writerow(["'"+v if isinstance(v, str) and v.startswith(("=", "+", "-", "@")) else v for v in row])
    (downloads / "requirements.csv").write_text(stream.getvalue())
    print(f"Built {out / 'index.html'} from {len(reports)} recorded runs")
