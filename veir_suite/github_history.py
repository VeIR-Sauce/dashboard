"""Bounded GitHub history restoration: establish provenance, then validate all bytes."""
from __future__ import annotations

import io
from pathlib import Path, PurePosixPath
import stat
import urllib.error
import urllib.parse
import urllib.request
import zipfile

from .history import check_receipt_id, read_all_history, receipt_filename, validate_receipt
from .model import InvalidData, parse_json

API_LIMIT = 4 * 1024 * 1024
ARCHIVE_LIMIT = 64 * 1024 * 1024
EXPANDED_LIMIT = 256 * 1024 * 1024


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *unused):
        return None


class GitHub:
    def __init__(self, token: str, opener=None):
        self.token = token
        self.opener = opener or urllib.request.build_opener(NoRedirect)

    def get(self, url: str, limit: int, *, authenticated=True, redirects=0) -> bytes:
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme != "https" or parsed.username or parsed.password:
            raise InvalidData("History URLs must use HTTPS without embedded credentials")
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if authenticated:
            if parsed.netloc != "api.github.com":
                raise InvalidData("Refusing to send a GitHub token outside the API")
            headers["Authorization"] = "Bearer " + self.token
        try:
            with self.opener.open(urllib.request.Request(url, headers=headers), timeout=60) as response:
                payload = response.read(limit + 1)
        except urllib.error.HTTPError as error:
            if error.code not in {301, 302, 303, 307, 308} or redirects >= 5:
                raise
            destination = urllib.parse.urljoin(url, error.headers["Location"])
            # Never forward the token, including on subsequent redirects.
            return self.get(destination, limit, authenticated=False, redirects=redirects + 1)
        if len(payload) > limit:
            raise InvalidData("History response exceeds its transfer budget")
        return payload

    def json(self, url: str) -> dict:
        return parse_json(self.get(url, API_LIMIT).decode("utf-8"), "GitHub response")

    def archive(self, url: str) -> bytes:
        return self.get(url, ARCHIVE_LIMIT)


def find_artifact(get_json, repository: str, repository_id: int, branch: str,
                  current_run: int, *, max_pages=20) -> dict | None:
    base = f"https://api.github.com/repos/{repository}/actions"
    for page in range(1, max_pages + 1):
        artifacts = get_json(f"{base}/artifacts?name=veir-progress-history&per_page=100&page={page}")["artifacts"]
        candidates = []
        for artifact in artifacts:
            run = artifact.get("workflow_run", {})
            if (artifact["expired"] or run.get("head_branch") != branch
                    or run.get("head_repository_id") != repository_id or run.get("id") == current_run):
                continue
            provenance = get_json(f"{base}/runs/{run['id']}")
            if (provenance["event"] in {"push", "schedule", "workflow_dispatch"}
                    and provenance["head_branch"] == branch
                    and provenance["repository"]["id"] == repository_id
                    and provenance["head_repository"]["id"] == repository_id
                    and provenance["head_sha"] == run["head_sha"]
                    and provenance["status"] == "completed"):
                candidates.append(artifact)
        if candidates:
            return max(candidates, key=lambda item: (item["created_at"], item["id"]))
        if len(artifacts) < 100:
            return None
    raise InvalidData("History search reached its page limit; refusing to assume an empty history")


def restore_archive(blob: bytes, out: Path) -> int:
    """Validate the entire archive and existing evidence before creating any files."""
    if len(blob) > ARCHIVE_LIMIT:
        raise InvalidData("History archive exceeds its transfer budget")
    contract, native = read_all_history(out)
    existing_ids = {report['id'] for report in contract + native}
    pending, identifiers = [], set()
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        if sum(info.file_size for info in archive.infolist()) > EXPANDED_LIMIT:
            raise InvalidData("History exceeds its extraction budget")
        for info in archive.infolist():
            relative = PurePosixPath(info.filename)
            if relative.is_absolute() or ".." in relative.parts or "\\" in info.filename:
                raise InvalidData("Unexpected history archive path")
            mode = stat.S_IFMT(info.external_attr >> 16)
            if mode not in {0, stat.S_IFREG, stat.S_IFDIR}:
                raise InvalidData("History cannot contain special files or links")
            if info.is_dir():
                if len(relative.parts) != 1:
                    raise InvalidData("Unexpected history directory")
                continue
            if len(relative.parts) != 2 or relative.name not in {"report.json", "native.json"}:
                raise InvalidData("Unexpected history archive member")
            payload = archive.read(info)
            report = validate_receipt(parse_json(payload.decode("utf-8"), info.filename))
            identifier = check_receipt_id(report)
            if relative.parts != (identifier, receipt_filename(report)) or identifier in identifiers:
                raise InvalidData("Duplicate receipt or mismatched archive path")
            identifiers.add(identifier)
            target = out / identifier / relative.name
            if not target.resolve().is_relative_to(out.resolve()):
                raise InvalidData("History path escapes through a symlink")
            other = target.with_name("native.json" if target.name == "report.json" else "report.json")
            if other.exists():
                raise InvalidData("Receipt ID belongs to a different kind of measurement")
            if target.exists():
                if target.read_bytes() != payload:
                    raise InvalidData("Conflicting evidence; refusing to overwrite a receipt")
            else:
                if identifier in existing_ids:
                    raise InvalidData("Receipt ID already exists at a different history path")
                pending.append((target, payload))
    for target, payload in pending:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(payload)
    return len(identifiers)
