#!/usr/bin/env python3
"""Add reference-validated core variants without changing the operation inventory."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.import_parsing_cases import OP
from veir_suite.model import file_digest, load_registry, read_json
from veir_suite.parsing import digest_text
from veir_suite.process import execute


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--mlir-opt', type=Path, required=True)
    args = parser.parse_args()
    root, tool = args.root.resolve(), args.mlir_opt.resolve()
    baseline = read_json(root / 'requirements/parsing.json')
    if file_digest(tool) != baseline['reference_sha256']:
        parser.error('Use the reference binary that validated the baseline examples')
    registry = load_registry(root)
    core = {case['operation'] for case in baseline['cases'] if not case['operation'].startswith('llvm.intr.')}
    mapped = {}
    for req in registry['requirements']:
        for test_id in req['test_ids']:
            mapped.setdefault(test_id, set()).update(set(req['operations']) & core)
    requests = []
    for test in sorted(registry['tests'], key=lambda test: test['id']):
        positive = test['kind'] == 'roundtrip' or (test['kind'] == 'verify' and test.get('expect') == 'accept')
        if positive and mapped.get(test['id']):
            parts = test['id'].split('.')
            label = parts[1].replace('_', ' ') if parts[0] == 'upstream' else ' · '.join(parts[2:])
            requests.append({'id': test['id'], 'label': label,
                'input': test['input'], 'operations': sorted(mapped[test['id']]), 'normalize': True})
    regressions = root / 'cases/parsing-regressions/manifest.json'
    if regressions.exists():
        requests.extend(read_json(regressions)['cases'])
    selected, seen, cache = [], {}, {}
    for case in baseline['cases']:
        seen[(case['operation'], case['input_sha256'])] = None
    output = root / 'cases/parsing-variants'; output.mkdir(exist_ok=True)
    artifact = root / '.artifacts'; artifact.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=artifact, prefix='expand-parsing-') as scratch:
        work = Path(scratch)
        for index, request in enumerate(requests):
            source = (root / request['input']).resolve()
            if not source.is_relative_to(root):
                raise ValueError('Variant input escapes the repository')
            key = (source, request['normalize'])
            if key not in cache:
                command = [str(tool), str(source)]
                command += ['--mlir-print-op-generic', '--mlir-print-local-scope'] if request['normalize'] else ['-o', '/dev/null']
                result = execute(command, cwd=work, timeout=10)
                if result['kind'] != 'exit' or result['exit_code'] != 0:
                    raise ValueError(f'Reference rejected {request["id"]}: {result["stderr"]}')
                cache[key] = result['stdout'] if request['normalize'] else source.read_text()
            text = cache[key]; checksum = digest_text(text)
            actual = set(OP.findall(text))
            for operation in request['operations']:
                if operation not in core or operation not in actual:
                    continue  # Only explicitly mapped operations present in this fixture.
                duplicate = seen.get((operation, checksum), False)
                if duplicate is not False:
                    if duplicate is not None:
                        duplicate['source']['test_ids'].append(request['id'])
                    continue
                identifier = operation + '.' + request['id']
                path = output / (identifier + '.mlir'); path.write_text(text)
                case = {'id': identifier, 'operation': operation, 'label': request['label'],
                    'input': str(path.relative_to(root)), 'input_sha256': checksum,
                    'contains': sorted(actual), 'method': 'core-variant' if request['normalize'] else 'parser-regression',
                    'source': {'repository': 'VeIR-Sauce/dashboard', 'path': request['input'],
                        'sha256': file_digest(source), 'test_ids': [request['id']]}}
                selected.append(case); seen[(operation, checksum)] = case
            if (index + 1) % 25 == 0:
                print(f'{index+1}/{len(requests)} candidates: {len(selected)} distinct additional cases', flush=True)
    manifest = {'schema_version': 1, 'reference_sha256': file_digest(tool),
        'catalog_sha256': baseline['catalog_sha256'], 'baseline_sha256': file_digest(root / 'requirements/parsing.json'),
        'description': 'Additional positive core-operation examples, deduplicated by operation and generic input hash. Negative verifier tests are excluded.',
        'cases': sorted(selected, key=lambda case: case['id'])}
    (root / 'requirements/parsing-variants.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'additional_cases': len(selected), 'expanded_operations': len({c['operation'] for c in selected})}, indent=2))


if __name__ == '__main__':
    main()
