"""Reviewed RISC-V result schema and presentation. No raw source HTML or logs."""
import json
from html import escape
from .riscv_details import load_details, build_slug, detail_tables
from .model import read_json
from .scoreboards import require, sha, timestamp, write_page

STAGES = ('clang', 'mlir-translate', 'veir-opt', 'veir2mir', 'llc-regalloc', 'llc-emit', 'link')
VERDICTS = {'PASS', 'MISMATCH', 'UNSUPPORTED', 'TIMEOUT', 'CRASH'}


def validate_riscv(data, allowed):
    require(isinstance(data, dict) and set(data) == {'schema_version', 'source_revision', 'recorded_at', 'veir', 'builds'})
    require(type(data['schema_version']) is int and data['schema_version'] == 1)
    sha(data['source_revision']); sha(data['veir']); timestamp(data['recorded_at'])
    require(isinstance(data['builds'], list) and len(data['builds']) == 2)
    identities = []
    for build in data['builds']:
        require(isinstance(build, dict) and set(build) == {'program', 'preset', 'stages', 'operations', 'runs'})
        require(build['program'] == 'sudoku' and build['preset'] in ('O2', 'inline'))
        identities.append((build['program'], build['preset']))
        require(isinstance(build['stages'], list) and len(build['stages']) == len(STAGES))
        for stage, name in zip(build['stages'], STAGES):
            require(isinstance(stage, dict) and set(stage) == {'stage', 'status'})
            require(stage['stage'] == name and stage['status'] in ('passed', 'failed', 'skipped'))
        require(isinstance(build['operations'], list) and len(build['operations']) <= len(allowed))
        names = []
        for op in build['operations']:
            require(isinstance(op, dict) and set(op) == {'operation', 'given', 'left'})
            require(isinstance(op['operation'], str) and op['operation'] in allowed)
            names.append(op['operation'])
            # Lowering can introduce or duplicate operations; this is not a subset count.
            require(all(type(op[key]) is int and 0 <= op[key] <= 10000000 for key in ('given', 'left')))
        require(len(set(names)) == len(names))
        require(isinstance(build['runs'], list) and len(build['runs']) == 1)
        run = build['runs'][0]
        require(isinstance(run, dict) and set(run) == {'input', 'verdict'})
        require(run['input'] == 'sud1' and isinstance(run['verdict'], str) and run['verdict'] in VERDICTS)
        compiled = all(stage['status'] == 'passed' for stage in build['stages'])
        require(run['verdict'] == 'UNSUPPORTED' or compiled)
    require(set(identities) == {('sudoku', 'O2'), ('sudoku', 'inline')})
    return data


def build_riscv(root, out):
    path = root / 'trackers/riscv.json'
    if not path.exists():
        return
    data = validate_riscv(read_json(path), read_json(root / 'requirements/riscv-operations.json')['operations'])
    reviewed = load_details(root, data)
    (out / 'data/riscv.json').write_text(json.dumps(data, indent=2) + '\n')
    if reviewed is not None:
        (out / 'data/riscv-details.json').write_text(json.dumps(reviewed, indent=2) + '\n')
    source = 'https://github.com/opencompl/llvm-riscv-backend-evaluation/blob/' + data['source_revision']
    detail_download = ' · <a href="data/riscv-details.json">Download diagnostics and examples</a>' if reviewed is not None else ''
    builds = data['builds']; runs = [run for build in builds for run in build['runs']]
    ops = [op for build in builds for op in build['operations']]
    passed = sum(run['verdict'] == 'PASS' for run in runs)
    compiled = sum(all(s['status'] == 'passed' for s in b['stages']) for b in builds)
    left, given = sum(op['left'] for op in ops), sum(op['given'] for op in ops)
    summary = ''.join(f'<div><strong>{value}</strong><span>{label}</span></div>' for value, label in [
        (f'{passed}/{len(runs)}', 'runs pass'), (f'{compiled}/{len(builds)}', 'builds compile'),
        (f'{left:,}/{given:,}', 'operations left unlowered')])
    remaining = []
    for name in sorted({op['operation'] for op in ops}):
        count = sum(op['left'] for op in ops if op['operation'] == name)
        if count:
            affected = sum(any(op['operation'] == name and op['left'] for op in b['operations']) for b in builds)
            remaining.append((count, name, affected))
    op_rows = ''.join(f'<tr><td><code>{name}</code></td><td>{count}</td><td>{affected}/{len(builds)}</td></tr>'
                      for count, name, affected in sorted(remaining, reverse=True))
    build_rows = ''
    for build in builds:
        failed = next((s['stage'] for s in build['stages'] if s['status'] == 'failed'), None)
        first_failure = failed or ('None' if all(s['status'] == 'passed' for s in build['stages']) else 'Not reached')
        build_left = sum(op['left'] for op in build['operations'])
        build_given = sum(op['given'] for op in build['operations'])
        verdict = build['runs'][0]['verdict']
        build_rows += (f'<tr><td><a href="{build_slug(build)}.html">Sudoku · {build["preset"]}</a></td>'
                       f'<td>{verdict}</td><td>{first_failure}</td><td>{build_left:,} / {build_given:,}</td></tr>')
        stage_rows = ''.join(f'<tr><td><code>{stage["stage"]}</code></td><td>{stage["status"]}</td></tr>' for stage in build['stages'])
        operation_rows = ''.join(f'<tr><td><code>{escape(op["operation"])}</code></td><td>{op["given"]}</td><td>{op["left"]}</td></tr>'
                                 for op in sorted(build['operations'], key=lambda op: (-op['left'], op['operation'])))
        name = build['program'] + '/' + build['preset']
        upstream = f'{source}/leaderboard/results/{name}/LEADERBOARD_{build["program"]}_{build["preset"]}.md'
        page = f'''<p><a href="riscv.html">← RISC-V leaderboard</a></p><h1>Sudoku · {build['preset']}</h1>
<p>Tracker by <strong>Naveen Seth Hanig</strong>. Recorded {data['recorded_at'].replace('T', ' ').replace('Z', ' UTC')} · VeIR <a href="https://github.com/opencompl/veir/commit/{data['veir']}">{data['veir'][:12]}</a></p>
<p><a href="{upstream}">Upstream build, logs and IR (access required) ↗</a> · <a href="data/riscv.json">Download results</a>{detail_download}</p>
<p>Run verdict for <code>sud1</code>: <strong>{verdict}</strong></p>
<section class="metrics"><div><strong>{int(verdict == "PASS")}/1</strong><span>runs pass</span></div><div><strong>{build_left:,}/{build_given:,}</strong><span>operations left unlowered</span></div></section>
<section class="panel"><h2>Compilation stages</h2><p>First failed stage: <strong>{first_failure}</strong></p><div class="table-scroll"><table><thead><tr><th>Stage</th><th>Status</th></tr></thead><tbody>{stage_rows}</tbody></table></div></section>
{detail_tables([build], reviewed, source)}
<details class="disclosure" id="riscv-operation-counts"><summary>All operation counts ({len(build['operations'])})</summary><div class="panel"><div class="table-scroll"><table><thead><tr><th>Operation</th><th>In input</th><th>Unlowered</th></tr></thead><tbody>{operation_rows}</tbody></table></div></div></details>
<p class="caption">This is a dated snapshot and is not yet refreshed automatically.</p>'''
        write_page(out, build_slug(build), 'Sudoku · ' + build['preset'], page)
    details = ('<section class="panel"><h2>Builds</h2><p>Open a program and preset for its stages, diagnostics and examples.</p>'
               '<div class="table-scroll"><table><thead><tr><th>Build</th><th>Run verdict</th><th>First failure</th><th>Unlowered / input</th></tr></thead><tbody>'
               + build_rows + '</tbody></table></div></section>' + detail_tables(builds, reviewed, source))
    body = f'''<h1>RISC-V backend</h1>
<p>Tracker by <strong>Naveen Seth Hanig</strong>. Compiles whole C programs through VeIR's RISC-V backend and compares their execution under gem5 with LLVM GlobalISel. A run passes when output and exit code agree.</p>
<p class="muted">Snapshot recorded {data['recorded_at'].replace('T', ' ').replace('Z', ' UTC')} · VeIR <a href="https://github.com/opencompl/veir/commit/{data['veir']}">{data['veir'][:12]}</a></p>
<p><a href="data/riscv.json">Download reviewed results</a>{detail_download} · <a href="{source}/leaderboard/LEADERBOARD.md">Upstream leaderboard (access required) ↗</a></p>
<section class="metrics">{summary}</section>
<p>This snapshot covers Sudoku with two compiler presets, not a broad performance suite. <code>O2</code> uses <code>-O2 -fno-vectorize -fno-slp-vectorize</code>; <code>inline</code> additionally encourages inlining. Unlowered operations measure remaining translation work, not execution speed.</p>
<section class="panel"><h2>Operations still unlowered</h2><div class="table-scroll"><table><thead><tr><th>Operation</th><th>Remaining</th><th>Builds affected</th></tr></thead><tbody>{op_rows}</tbody></table></div></section>
{details}
<p class="caption">Imported from a reviewed, user-supplied snapshot. This tracker is not yet refreshed automatically because the source repository is private. Selected diagnostic excerpts and IR examples are available above; full logs and IR remain upstream.</p>'''
    write_page(out, 'riscv', 'RISC-V backend', body)
