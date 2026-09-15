"""A self-contained, dependency-free GitHub Pages site with auditable downloads."""
from __future__ import annotations
import csv
import io
import gzip
import json
from pathlib import Path
import shutil

from .model import InvalidData, load_registry, read_json
from .history import read_all_history, read_history


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
            item["results"] = [{key: value for key, value in r.items() if key != "steps"} for r in report["results"]]
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
    data = {"registry": registry, "catalog": catalog, "sources": sources, "reports": compact,
            "cohorts": cohorts, "native": native_entries}
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
