"""Strict public-data boundary for external trackers; never copy raw source blobs."""
from datetime import datetime
from html import escape
import json
from pathlib import Path
import re
import tempfile

from .model import InvalidData, read_json

REPOSITORY = 'opencompl/veir-interpreter-scoreboard'
REFERENCES = ('llubi', 'alive-exec')


def require(condition):
    if not condition:
        # Never include rejected values: a malformed value could be a credential.
        raise InvalidData('External scoreboard failed its public-data schema; no source values logged')


def sha(value):
    require(isinstance(value, str) and re.fullmatch(r'[0-9a-f]{40}', value))
    return value


def timestamp(value):
    require(isinstance(value, str) and re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ', value))
    datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')
    return value


def normalize_interpreter(raw, revision, recorded_at, allowed):
    require(isinstance(raw, dict) and set(raw) == {'veir', 'tests'})
    require(isinstance(raw['tests'], dict) and set(raw['tests']) == set(allowed))
    tests = {}
    for name in sorted(allowed):
        require(re.fullmatch(r'(clean|ub)/[a-z0-9_-]+', name) is not None)
        value = raw['tests'][name]
        require(isinstance(value, dict) and set(value) == {'finished', 'agrees'})
        require(type(value['finished']) is bool)
        require(isinstance(value['agrees'], dict) and set(value['agrees']) == set(REFERENCES))
        for reference in REFERENCES:
            require(value['agrees'][reference] is None or type(value['agrees'][reference]) is bool)
            require(value['finished'] or value['agrees'][reference] is None)
        tests[name] = {'finished': value['finished'],
                       'agrees': {ref: value['agrees'][ref] for ref in REFERENCES}}
    return {'schema_version': 1, 'source_revision': sha(revision),
            'recorded_at': timestamp(recorded_at), 'veir': sha(raw['veir']), 'tests': tests}


def validate_interpreter(data, allowed):
    require(isinstance(data, dict) and set(data) == {
        'schema_version', 'source_revision', 'recorded_at', 'veir', 'tests'})
    require(type(data['schema_version']) is int and data['schema_version'] == 1)
    return normalize_interpreter({'veir': data['veir'], 'tests': data['tests']},
                                 data['source_revision'], data['recorded_at'], allowed)


def write_snapshot(path, data):
    """Replace a validated snapshot atomically, with no shared temporary filename."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                         prefix='.' + path.name + '.', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(json.dumps(data, indent=2) + '\n')
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def build_scoreboards(root: Path, out: Path, history: Path):
    allowed = read_json(root / 'requirements/interpreter-tests.json')['tests']
    # Fresh normalized external snapshots live next to the permanent history.
    source = history.parent / 'trackers/interpreter.json'
    if not source.exists():
        source = root / 'trackers/interpreter.json'
    data = validate_interpreter(read_json(source), allowed)
    (out / 'data/interpreter.json').write_text(json.dumps(data, indent=2) + '\n')
    total = len(data['tests']); finished = sum(t['finished'] for t in data['tests'].values())
    metrics = f'<div><strong>{finished}/{total}</strong><span>tests ran to a result</span></div>'
    for reference in REFERENCES:
        values = [t['agrees'][reference] for t in data['tests'].values()]
        comparable = sum(v is not None for v in values)
        metrics += f'<div><strong>{sum(v is True for v in values)}/{comparable}</strong><span>agree with {reference}</span></div>'
    base = f'https://github.com/{REPOSITORY}/blob/{data["source_revision"]}'
    rows = ''
    for name, value in sorted(data['tests'].items(), key=lambda x: (x[1]['finished'], x[0])):
        state = 'finished' if value['finished'] else 'unfinished'
        mismatch = any(v is False for v in value['agrees'].values())
        cells = ''.join('<td>' + ('Agrees' if value['agrees'][ref] is True else 'Disagrees' if value['agrees'][ref] is False else 'Not comparable') + '</td>' for ref in REFERENCES)
        rows += (f'<tr data-name="{escape(name)}" data-state="{state}" data-mismatch="{str(mismatch).lower()}">'
                 f'<td><a href="{base}/llubi-tests/{name}.ll">{escape(name)}</a></td>'
                 f'<td>{"Ran to a result" if value["finished"] else "No result"}</td>{cells}</tr>')
    body = f'''<h1>VeIR interpreter</h1>
<p>Tracker by <strong>Naveen Seth Hanig</strong>. Compares VeIR with LLVM's <code>llubi</code> and Alive2's <code>alive-exec</code> on selected llubi tests.</p>
<p class="muted">Results recorded {data['recorded_at'].replace('T', ' ').replace('Z', ' UTC')} · VeIR <a href="https://github.com/opencompl/veir/commit/{data['veir']}">{data['veir'][:12]}</a></p>
<p><a href="{base}/SCOREBOARD.md">Upstream scoreboard and diagnostics ↗</a> · <a href="data/interpreter.json">Download reviewed results</a></p>
<section class="metrics">{metrics}</section>
<p>Agreement counts only tests with comparable results. Some agree trivially because they only return <code>void</code>; this JSON does not distinguish those cases. Agreement is not proof of full semantic correctness.</p>
<p><strong>No result</strong> means the interpreter did not produce a result. It can reflect unsupported input or a harness/interface problem; it is not automatically a disagreement. <strong>Not comparable</strong> means one side has no comparable result. <code>clean/</code> tests return normally; <code>ub/</code> tests exercise undefined behavior.</p>
<div class="filters"><label class="search">Test <input id="test-search" type="search" placeholder="Search tests"></label><label>Show <select id="test-filter"><option value="all">All tests</option><option value="unfinished">No result</option><option value="mismatch">Disagreements</option><option value="finished">Ran to a result</option></select></label></div>
<p id="test-count" aria-live="polite">{total} tests</p>
<div class="table-scroll"><table><thead><tr><th>Test</th><th>VeIR</th><th>llubi</th><th>alive-exec</th></tr></thead><tbody>{rows}</tbody></table></div>
<p class="caption">The website checks for published upstream results hourly. The date above is the source commit's date, not a new measurement made by this website. <a href="https://github.com/{REPOSITORY}/actions">Upstream workflow status ↗</a></p>'''
    write_page(out, 'interpreter', 'VeIR interpreter', body)
    write_page(out, 'riscv', 'RISC-V backend', '''<h1>RISC-V backend</h1>
<p>Tracker by <strong>Naveen Seth Hanig</strong>.</p>
<section class="panel"><h2>Results awaiting import</h2><p>The source repository is currently private. Its results have not yet been imported into this website. No performance or correctness score is claimed here.</p>
<p><a href="https://github.com/opencompl/llvm-riscv-backend-evaluation/blob/main/leaderboard/LEADERBOARD.md">Upstream leaderboard (repository access required) ↗</a></p></section>''')


def write_page(out, slug, title, body):
    nav = '<a href="index.html">Overview</a><a href="index.html#llvm-parse">LLVM parsing</a><a href="interpreter.html">Interpreter</a><a href="riscv.html">RISC-V backend</a>'
    (out / f'{slug}.html').write_text(f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} · VeIR progress</title><link rel="stylesheet" href="style.css"><script src="scoreboards.js" defer></script></head><body><header><nav><a class="brand" href="index.html">VeIR / progress</a></nav></header><main><div class="view-links">{nav}</div>{body}</main></body></html>\n''')
