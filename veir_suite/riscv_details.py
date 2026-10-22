"""Explicitly reviewed diagnostic excerpts, tied to a single result snapshot."""
from html import escape
from .model import read_json
from .scoreboards import require


def validate_details(details, snapshot):
    require(isinstance(details, dict) and set(details) == {'source_revision', 'builds'})
    require(details['source_revision'] == snapshot['source_revision'])
    require(isinstance(details['builds'], dict))
    require(set(details['builds']) == {b['program'] + '/' + b['preset'] for b in snapshot['builds']})
    for build in snapshot['builds']:
        reviewed = details['builds'][build['program'] + '/' + build['preset']]
        require(isinstance(reviewed, dict) and set(reviewed) == {'diagnostics', 'examples'})
        require(isinstance(reviewed['diagnostics'], list) and len(reviewed['diagnostics']) <= len(build['stages']))
        stages = []
        for diagnostic in reviewed['diagnostics']:
            require(isinstance(diagnostic, dict) and set(diagnostic) == {'stage', 'error'})
            require(diagnostic['stage'] in [s['stage'] for s in build['stages']])
            require(isinstance(diagnostic['error'], str) and 0 < len(diagnostic['error']) <= 16384)
            stages.append(diagnostic['stage'])
        require(len(set(stages)) == len(stages))
        require(isinstance(reviewed['examples'], list) and len(reviewed['examples']) <= 1000)
        names = []; counts = {}
        operations = {op['operation']: op['left'] for op in build['operations']}
        for example in reviewed['examples']:
            require(isinstance(example, dict) and set(example) == {'op', 'types', 'left', 'function', 'line', 'definition'})
            require(isinstance(example['op'], str) and example['op'] in operations)
            for key in ('types', 'function', 'definition'):
                require(isinstance(example[key], str) and len(example[key]) <= 16384)
            require(bool(example['types']) and bool(example['definition']))
            require(type(example['line']) is int and 0 < example['line'] <= 10000000)
            require(type(example['left']) is int and 0 < example['left'] <= operations[example['op']])
            names.append((example['op'], example['types']))
            counts[example['op']] = counts.get(example['op'], 0) + example['left']
        require(len(set(names)) == len(names))
        require(all(count <= operations[op] for op, count in counts.items()))
    return details


def load_details(root, snapshot):
    path = root / 'requirements/riscv-reviewed-details.json'
    return validate_details(read_json(path), snapshot) if path.exists() else None


def build_slug(build):
    return 'riscv-' + build['program'] + '-' + build['preset']


def detail_tables(builds, reviewed, source):
    if reviewed is None:
        return '<p class="muted">Diagnostic text and examples have not been imported for this snapshot.</p>'
    diagnostics = []; examples = []
    for build in builds:
        name = build['program'] + '/' + build['preset']
        label = f'<a href="{build_slug(build)}.html">{escape(name)}</a>'
        detail = reviewed['builds'][name]
        for row in detail['diagnostics']:
            diagnostics.append(f'<tr><td>{label}</td><td><code>{escape(row["stage"])}</code></td>'
                               f'<td><pre class="parse-diagnostic">{escape(row["error"])}</pre></td></tr>')
        for row in detail['examples']:
            location = (('@' + row['function'] + ', ') if row['function'] else 'Module scope, ') + 'line ' + str(row['line'])
            href = f'{source}/leaderboard/results/{name}/veir-opt.mlir#L{row["line"]}'
            examples.append(f'<tr><td>{label}<br><a href="{href}">{escape(location)} ↗</a></td>'
                            f'<td><code>{escape(row["op"])}</code><br><code>{escape(row["types"])}</code></td>'
                            f'<td>{row["left"]}</td><td><pre class="parse-input">{escape(row["definition"])}</pre></td></tr>')
    return (f'<details class="disclosure" id="riscv-diagnostics"><summary>Exact recorded diagnostics ({len(diagnostics)})</summary>'
            '<div class="panel"><p>Diagnostic excerpts recorded by the upstream tracker. Full logs are linked from each upstream build page.</p>'
            '<div class="table-scroll"><table><thead><tr><th>Build</th><th>Stage</th><th>Diagnostic</th></tr></thead><tbody>'
            + (''.join(diagnostics) or '<tr><td colspan="3">No diagnostics recorded.</td></tr>') + '</tbody></table></div></div></details>'
            f'<details class="disclosure" id="riscv-examples"><summary>Unlowered operations by type, with examples ({len(examples)})</summary>'
            '<div class="panel"><p>Each excerpt includes the first recorded instruction and its dependencies. Source links require access to the private upstream repository.</p>'
            '<div class="table-scroll"><table><thead><tr><th>Build / source</th><th>Operation / types</th><th>Remaining</th><th>Example</th></tr></thead><tbody>'
            + (''.join(examples) or '<tr><td colspan="4">No examples recorded.</td></tr>') + '</tbody></table></div></div></details>')
