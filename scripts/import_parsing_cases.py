#!/usr/bin/env python3
"""Extract small, reference-verified parser examples from pinned LLVM tests.

No RUN lines are executed. Each candidate must pass mlir-opt verification. The
generic printer provides operation names and the exact input syntax for VeIR.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from veir_suite.model import file_digest
from veir_suite.process import execute

OP = re.compile(r'^\s*(?:%[^=\n]+ = )?"(llvm\.[\w.]+)"\(', re.M)


def split_types(text: str) -> list[str]:
    """Split a generic operation's operand types, respecting nested type syntax."""
    result, start, stack, quoted, escaped = [], 0, [], False, False
    for i, char in enumerate(text):
        if quoted:
            if char == '"' and not escaped:
                quoted = False
            escaped = char == '\\' and not escaped
        elif char == '"':
            quoted = True
        elif char in '<([{':
            stack.append(char)
        elif char in '>)]}':
            if stack:
                stack.pop()
        elif char == ',' and not stack:
            result.append(text[start:i].strip()); start = i + 1
    if text[start:].strip():
        result.append(text[start:].strip())
    return result


def leaf_example(line: str, aliases: str) -> str | None:
    match = re.fullmatch(r'\s*((?:%[^=\n]+ = )?"llvm\.[\w.]+")\(([^)]*)\)(.*) : \((.*)\) -> (.*)', line)
    if not match or '({' in match[3]:
        return None
    types = split_types(match[4])
    operands = [f'%arg{i}' for i in range(len(types))]
    signature = ', '.join(f'{arg}: {ty}' for arg, ty in zip(operands, types))
    operation = f'{match[1]}({", ".join(operands)}){match[3]} : ({match[4]}) -> {match[5]}'
    return f'{aliases}module {{\n  llvm.func @sample({signature}) {{\n    {operation}\n    llvm.return\n  }}\n}}\n'


def candidates(generic: str):
    marker = generic.find('"builtin.module"')
    aliases = generic[:marker] if marker >= 0 else ''
    for line in generic.splitlines():
        if OP.match(line):
            leaf = leaf_example(line, aliases)
            if leaf:
                yield 'isolated-operation', leaf
    # The reference printer places each module-level op at indentation two.
    starts = [m.start() for m in re.finditer(r'^  (?:%[^=\n]+ = )?"[\w.]+"\(', generic, re.M)]
    end = generic.rfind('\n})')
    if marker >= 0 and end >= 0:
        units = [generic[start:stop].rstrip() for start, stop in zip(starts, starts[1:] + [end])]
        symbols = {}
        for i, unit in enumerate(units):
            symbol = re.search(r'\bsym_name = "([\w.$-]+)"', unit.splitlines()[0])
            if symbol:
                symbols[symbol[1]] = i
        for i in sorted(range(len(units)), key=lambda j: len(units[j])):
            indices = {i}
            while True:
                dependencies = {symbols[name] for j in indices for name in re.findall(r'@([\w.$-]+)', units[j]) if name in symbols}
                if dependencies <= indices:
                    break
                indices |= dependencies
            body = '\n'.join(units[j] for j in sorted(indices))
            yield 'isolated-top-level', aliases + '"builtin.module"() ({\n' + body + '\n}) : () -> ()\n'
    if len(generic) <= 65536:
        yield 'reference-test-chunk', generic


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--llvm', type=Path, required=True)
    parser.add_argument('--mlir-opt', type=Path, required=True)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root, llvm, tool = args.root.resolve(), args.llvm.resolve(), args.mlir_opt.resolve()
    catalog = json.loads((root / 'requirements/catalog.json').read_text())
    revision = subprocess.check_output(['git', '-C', str(llvm), 'rev-parse', 'HEAD'], text=True).strip()
    if revision != catalog['llvm_revision']:
        parser.error('LLVM checkout must match the catalog revision')
    names = {op['name'] for op in catalog['operations']}
    selected, seen, rejected = {}, set(), 0
    output = root / 'cases/parsing'
    output.mkdir(parents=True, exist_ok=True)
    artifact = root / '.artifacts'; artifact.mkdir(exist_ok=True)
    priority = [llvm / 'mlir/test/Target/LLVMIR/llvmir-intrinsics.mlir',
                llvm / 'mlir/test/Target/LLVMIR/llvmir.mlir',
                llvm / 'mlir/test/Dialect/LLVMIR/roundtrip.mlir']
    paths = priority + sorted((llvm / 'mlir/test').rglob('*.mlir'))
    visited = set()
    with tempfile.TemporaryDirectory(dir=artifact, prefix='import-parsing-') as scratch:
        work = Path(scratch)
        def normalize(text):
            source = work / 'candidate.mlir'; source.write_text(text)
            result = execute([str(tool), str(source), '--mlir-print-op-generic', '--mlir-print-local-scope'], cwd=work, timeout=10)
            return result['stdout'] if result['kind'] == 'exit' and result['exit_code'] == 0 else None
        for path in paths:
            if path in visited or len(selected) == len(names):
                continue
            visited.add(path)
            raw = path.read_text()
            remaining = names - selected.keys()
            if not remaining.intersection(re.findall(r'\bllvm\.[\w.]+', raw)):
                continue
            for chunk_index, chunk in enumerate(re.split(r'^//\s*-{5,}.*$', raw, flags=re.M)):
                if not (names - selected.keys()).intersection(re.findall(r'\bllvm\.[\w.]+', chunk)):
                    continue
                generic = normalize(chunk)
                if not generic:
                    rejected += 1; continue
                present = set(OP.findall(generic)) & names
                seen.update(present)
                for method, candidate in candidates(generic):
                    desired = (set(OP.findall(candidate)) & present) - selected.keys()
                    if method == 'isolated-operation':
                        # Scaffolding is not the intended target of this extraction.
                        desired -= {'llvm.func', 'llvm.return'}
                    if not desired:
                        continue
                    verified = normalize(candidate)
                    if not verified:
                        continue
                    actual = sorted(set(OP.findall(verified)) & names)
                    for operation in sorted(desired & set(actual)):
                        target = output / f'{operation}.mlir'
                        target.write_text(verified)
                        selected[operation] = {'operation': operation, 'input': str(target.relative_to(root)),
                            'input_sha256': file_digest(target), 'contains': actual, 'method': method,
                            'source': {'repository': 'llvm/llvm-project', 'revision': revision,
                                'path': str(path.relative_to(llvm)), 'sha256': file_digest(path),
                                'chunk': chunk_index}}
                print(f'{len(selected)}/{len(names)} examples: {path.relative_to(llvm)} chunk {chunk_index}', flush=True)
        for path in sorted((root / 'cases/parsing-seeds').glob('*.mlir')):
            operation = path.stem
            verified = normalize(path.read_text())
            if not verified or operation not in OP.findall(verified) or operation not in names:
                raise ValueError(f'Invalid supplemental example: {path}')
            target = output / f'{operation}.mlir'; target.write_text(verified)
            selected[operation] = {'operation': operation, 'input': str(target.relative_to(root)),
                'input_sha256': file_digest(target), 'contains': sorted(set(OP.findall(verified)) & names),
                'method': 'handwritten-reference-verified',
                'source': {'repository': 'VeIR-Sauce/dashboard', 'path': str(path.relative_to(root)), 'sha256': file_digest(path)}}
    manifest = {'schema_version': 1, 'llvm_revision': revision, 'reference_sha256': file_digest(tool),
                'catalog_sha256': file_digest(root / 'requirements/catalog.json'),
                'description': 'Reference-verified generic MLIR examples isolated from pinned LLVM tests. One example per operation; not all syntax or type variants.',
                'license': 'LLVM test-derived examples: Apache-2.0 WITH LLVM-exception; see cases/parsing/LICENSE.txt.',
                'cases': [selected[name] for name in sorted(selected)],
                'missing': sorted(names - selected.keys()), 'rejected_source_chunks': rejected}
    (root / 'requirements/parsing.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (output / 'LICENSE.txt').write_text((llvm / 'LICENSE.TXT').read_text().rstrip() + '\n')
    print(json.dumps({'examples': len(selected), 'missing': manifest['missing']}, indent=2))


if __name__ == '__main__':
    main()
