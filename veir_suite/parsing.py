"""A separate, reference-validated generic-MLIR parsing measurement lane."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import uuid

from .model import InvalidData, digest, file_digest, git_identity, read_json
from .process import execute

MODES = {'strict': [], 'permissive': ['--allow-unregistered-dialect']}
STATUSES = {'parsed', 'rejected', 'blocked', 'error', 'not_tested'}


def controls_ok(controls: dict) -> bool:
    if set(controls) != {'verification_disabled', 'verification_enabled', 'malformed_rejected'}:
        return False
    return all(step.get('kind') == 'exit' for step in controls.values()) and (
        controls['verification_disabled'].get('exit_code') == 0
        and controls['verification_enabled'].get('exit_code') == 1
        and 'Error verifying input program:' in controls['verification_enabled'].get('stderr', '')
        and controls['malformed_rejected'].get('exit_code') == 1)


def classify(step: dict, operation: str, text: str) -> str:
    if step.get('kind') != 'exit':
        return 'error'
    if step.get('exit_code') == 0:
        return 'parsed' if f'"{operation}"(' in step.get('stdout', '') else 'error'
    if step.get('exit_code') != 1:
        return 'error'
    diagnostic = step.get('stderr', '')
    unregistered = re.search(r"op '([^']+)' is not registered", diagnostic)
    if unregistered:
        return 'rejected' if unregistered[1] == operation else 'blocked'
    location = re.search(r':(\d+):(\d+):', diagnostic)
    if location:
        lines = text.splitlines()
        line = int(location[1]) - 1
        return 'rejected' if 0 <= line < len(lines) and f'"{operation}"(' in lines[line] else 'blocked'
    return 'error'  # CLI/environment/printing errors cannot become parser rejections.


def counts(rows: list[dict]) -> dict:
    return {mode: dict(sorted(Counter(row[mode]['status'] for row in rows).items())) for mode in MODES}


def validate_parsing(report: dict) -> dict:
    if report.get('kind') != 'veir-parsing' or report.get('schema_version') != 1:
        raise InvalidData('Unknown parsing receipt schema')
    manifest = report['manifest']
    if digest(manifest) != report['manifest_sha256']:
        raise InvalidData('Parsing manifest hash mismatch')
    if manifest.get('modes') != MODES or manifest.get('veir_arguments') != ['--disable-verifiers', '--print-op-generic']:
        raise InvalidData('Unexpected parsing mode or verifier policy')
    if report.get('controls_ok') is not controls_ok(report.get('controls', {})):
        raise InvalidData('Parsing controls contradict their command evidence')
    expected = {op['name'] for op in manifest['catalog']['operations']}
    rows = report['results']
    if len(rows) != len(expected) or {row['operation'] for row in rows} != expected:
        raise InvalidData('Parsing receipt must account for every catalog operation exactly once')
    cases = {case['operation']: case for case in manifest['cases']}
    if len(cases) != len(manifest['cases']) or set(cases) - expected:
        raise InvalidData('Invalid parsing case mapping')
    for row in rows:
        case = cases.get(row['operation'])
        if case:
            if digest_text(case['text']) != case['input_sha256']:
                raise InvalidData('Parsing input hash mismatch')
            if row.get('input_sha256') != case['input_sha256']:
                raise InvalidData('Parsing result refers to another input')
            if not re.search(r'^\s*(?:%[^=\n]+ = )?"' + re.escape(row['operation']) + r'"\(', case['text'], re.M):
                raise InvalidData('Parsing example does not contain its target operation')
        reference_ok = case and row['reference'].get('kind') == 'exit' and row['reference'].get('exit_code') == 0
        for mode in MODES:
            status = row[mode]['status']
            step = row[mode].get('step')
            if step:
                command = step.get('command', [])
                if (len(command) != 4 + len(MODES[mode]) or command[0] != report['tools']['veir_opt']['path']
                        or command[2:] != manifest['veir_arguments'] + MODES[mode]):
                    raise InvalidData('Parsing command does not match its mode')
            derived = classify(row[mode]['step'], row['operation'], case['text']) if reference_ok and row[mode].get('step') else 'not_tested'
            if status not in STATUSES or status != derived:
                raise InvalidData('Parsing status contradicts its command evidence')
    if report['counts'] != counts(rows):
        raise InvalidData('Parsing counts contradict their observations')
    complete = report.get('unchanged') is True and report.get('controls_ok') is True and all(
        row[mode]['status'] in {'parsed', 'rejected', 'blocked'} for row in rows for mode in MODES)
    if report.get('complete') is not complete:
        raise InvalidData('False parsing completion claim')
    if not report.get('finished_at') or not report.get('id'):
        raise InvalidData('Missing parsing receipt metadata')
    return report


def digest_text(text: str) -> str:
    import hashlib
    return hashlib.sha256(text.encode()).hexdigest()


def run_parsing(root: Path, veir: Path, mlir_opt: Path, out: Path, timeout: float = 10) -> tuple[dict, int]:
    root, veir, mlir_opt = root.resolve(), veir.resolve(), mlir_opt.resolve()
    if timeout <= 0:
        raise InvalidData('Timeout must be positive')
    catalog = read_json(root / 'requirements/catalog.json')
    imported = read_json(root / 'requirements/parsing.json')
    if imported['catalog_sha256'] != file_digest(root / 'requirements/catalog.json'):
        raise InvalidData('Parsing fixtures use a different catalog')
    if imported['reference_sha256'] != file_digest(mlir_opt):
        raise InvalidData('Reference binary differs from the fixture import; reimport with the intended reference')
    cases = []
    for case in imported['cases']:
        path = (root / case['input']).resolve()
        if not path.is_relative_to(root) or file_digest(path) != case['input_sha256']:
            raise InvalidData('Escaping or stale parsing fixture')
        cases.append({**case, 'text': path.read_text()})
    binary = veir / '.lake/build/bin/veir-opt'
    tools = {name: {'path': str(path), 'sha256': file_digest(path)} for name, path in [('veir_opt', binary), ('mlir_opt', mlir_opt)]}
    source = git_identity(veir)
    harness = digest([[name, file_digest(root / 'veir_suite' / name)] for name in ['parsing.py', 'process.py']])
    identifier = 'parsing-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
    directory = out.resolve() / identifier; directory.mkdir(parents=True, exist_ok=False)
    now = lambda: datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')
    manifest = {'catalog': catalog, 'cases': cases, 'timeout_seconds': timeout, 'modes': MODES,
                'syntax': 'generic MLIR', 'veir_arguments': ['--disable-verifiers', '--print-op-generic'],
                'llvm_revision': imported['llvm_revision']}
    report = {'schema_version': 1, 'kind': 'veir-parsing', 'id': identifier,
              'started_at': now(), 'source': source, 'tools': tools, 'harness_sha256': harness,
              'manifest': manifest, 'manifest_sha256': digest(manifest), 'results': [], 'complete': False}
    (directory / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n')
    # An ill-typed add parses but must fail verification; malformed syntax must fail.
    control = directory / 'control.mlir'
    control.write_text('''"builtin.module"() ({
  "llvm.func"() <{sym_name = "control", function_type = !llvm.func<void (i32, i64)>}> ({
  ^bb0(%a: i32, %b: i64):
    %r = "llvm.add"(%a, %b) : (i32, i64) -> i32
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()
''')
    invoke = lambda command: execute(command, cwd=directory, timeout=timeout)
    controls = {'verification_disabled': invoke([str(binary), str(control), '--disable-verifiers', '--print-op-generic']),
                'verification_enabled': invoke([str(binary), str(control)])}
    bad = directory / 'malformed.mlir'; bad.write_text('not an operation\n')
    controls['malformed_rejected'] = invoke([str(binary), str(bad), '--disable-verifiers'])
    report['controls'] = controls
    report['controls_ok'] = controls_ok(controls)
    by_name = {case['operation']: case for case in cases}
    for index, operation in enumerate(catalog['operations']):
        name = operation['name']; case = by_name.get(name)
        row = {'operation': name, **{mode: {'status': 'not_tested'} for mode in MODES}}
        if case:
            path = directory / f'{name}.mlir'; path.write_text(case['text'])
            row['input_sha256'] = case['input_sha256']
            row['reference'] = invoke([str(mlir_opt), str(path), '-o', '/dev/null'])
            if report['controls_ok'] and row['reference']['kind'] == 'exit' and row['reference']['exit_code'] == 0:
                for mode, flags in MODES.items():
                    step = invoke([str(binary), str(path), '--disable-verifiers', '--print-op-generic', *flags])
                    row[mode] = {'status': classify(step, name, case['text']), 'step': step}
        report['results'].append(row)
        if (index + 1) % 25 == 0 or index + 1 == len(catalog['operations']):
            print(f'{index + 1}/{len(catalog["operations"])} {name}: {row["strict"]["status"]} / {row["permissive"]["status"]}', flush=True)
    report['unchanged'] = (source == git_identity(veir) and all(file_digest(Path(t['path'])) == t['sha256'] for t in tools.values())
        and harness == digest([[name, file_digest(root / 'veir_suite' / name)] for name in ['parsing.py', 'process.py']])
        and all(file_digest(root / c['input']) == c['input_sha256'] for c in cases))
    report['counts'] = counts(report['results'])
    report['complete'] = report['unchanged'] and report['controls_ok'] and all(
        row[mode]['status'] in {'parsed', 'rejected', 'blocked'} for row in report['results'] for mode in MODES)
    report['finished_at'] = now()
    validate_parsing(report)
    temporary = directory / 'parsing.json.tmp'; temporary.write_text(json.dumps(report, indent=2) + '\n')
    temporary.replace(directory / 'parsing.json')
    print(json.dumps({'report': str(directory / 'parsing.json'), 'complete': report['complete'], 'counts': report['counts']}, indent=2))
    return report, 0 if report['complete'] else 2
