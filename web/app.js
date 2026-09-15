"use strict";
const data = JSON.parse(document.getElementById("data").textContent);
const progress = VeirProgress;
const $ = id => document.getElementById(id);
const node = (tag, text, className) => { const el = document.createElement(tag); if (text !== undefined) el.textContent = text; if (className) el.className = className; return el; };
const link = (label, href) => { const el = node("a", label); el.href = href; return el; };
const stageNames = {verification: "Verification", roundtrip: "Round-trip", execution: "Execution", transformation: "Transformation", regression: "Regression", proof: "Proof"};
const groups = progress.cohortIds(data);
const planOption = node("option", `Current plan · ${data.registry.requirements.length} requirements`);
planOption.value = progress.CURRENT_PLAN; $("cohort").append(planOption);
for (const cohort of groups) {
  const report = data.reports.findLast(r => r.cohort === cohort);
  const option = node("option", `${report.profile.label} · ${data.cohorts[cohort].requirements.length} requirements · ${cohort.slice(0, 8)}`);
  option.value = cohort; $("cohort").append(option);
}
$("cohort").value = groups[0] || progress.CURRENT_PLAN;
const scopes = new Map(data.registry.scopes.map(s => [s.id, s]));
for (const registry of Object.values(data.cohorts)) for (const scope of registry.scopes) if (!scopes.has(scope.id)) scopes.set(scope.id, scope);
for (const scope of scopes.values()) { const option = node("option", scope.title); option.value = scope.id; $("scope").append(option); }
let state = {}, showAllOperations = false;

function chart(id, runs, field, color, total) {
  const container = $(id); container.replaceChildren();
  if (!runs.length) { container.append(node("div", "No complete measurement in this cohort yet.", "empty")); return; }
  const ns = "http://www.w3.org/2000/svg", svg = document.createElementNS(ns, "svg");
  svg.setAttribute("viewBox", "0 0 560 245"); svg.setAttribute("role", "img");
  svg.setAttribute("aria-label", `${field === "coverage_remaining" ? "Coverage" : "Conformance"} remaining: ${runs.map(r => r.value[field]).join(", ")} across ${runs.length} complete measurements.`);
  function add(tag, attrs, text) { const el = document.createElementNS(ns, tag); for (const [key, value] of Object.entries(attrs)) el.setAttribute(key, value); if (text !== undefined) el.textContent = text; svg.append(el); return el; }
  const maximum = Math.max(total, 1), left = 43, right = 526, top = 21, bottom = 196;
  const start = Date.parse(runs[0].finished_at), end = Date.parse(runs.at(-1).finished_at);
  const x = r => end === start ? (left + right) / 2 : left + (Date.parse(r.finished_at) - start) / (end - start) * (right - left);
  const y = value => bottom - value / maximum * (bottom - top);
  const ticks = [...new Set([0, Math.round(maximum / 4), Math.round(maximum / 2), Math.round(maximum * .75), maximum])];
  for (const tick of ticks) { add("line", {x1: left, x2: right, y1: y(tick), y2: y(tick), stroke: "#e7edf0", "stroke-dasharray": "3 4"}); add("text", {x: left - 12, y: y(tick) + 4, "text-anchor": "end"}, tick); }
  if (runs.length > 1) add("path", {d: runs.map((r, i) => `${i ? "L" : "M"} ${x(r)} ${y(r.value[field])}`).join(" "), fill: "none", stroke: color, "stroke-width": 2.5});
  for (const run of runs) { const circle = add("circle", {cx: x(run), cy: y(run.value[field]), r: 5, fill: color, stroke: "white", "stroke-width": 2}); const title = document.createElementNS(ns, "title"); title.textContent = `${run.finished_at}: ${run.value[field]} remaining / ${total}`; circle.append(title); }
  const last = runs.at(-1); add("text", {x: x(last), y: Math.max(15, y(last.value[field]) - 14), "text-anchor": "middle", class: "value"}, last.value[field]);
  const dateLabel = r => r.finished_at.slice(5, 10) + " " + r.finished_at.slice(11, 16) + " UTC";
  if (runs.length === 1) add("text", {x: x(last), y: 226, "text-anchor": "middle"}, dateLabel(last));
  else { add("text", {x: left, y: 226}, dateLabel(runs[0])); add("text", {x: right, y: 226, "text-anchor": "end"}, dateLabel(last)); }
  container.append(svg);
}

function totals(rows) { return {coverage_remaining: rows.filter(r => !r.covered).length, conformance_remaining: rows.filter(r => !r.satisfied).length}; }
function displayState(req) { return progress.requirementState(req, state); }

function render() {
  state = progress.view(data, $("cohort").value, $("scope").value);
  const {reports, complete, active, attempted, registry, requirements, scopeAvailable} = state;
  const rows = state.rowList;
  const remaining = totals(rows), ids = new Set(requirements.flatMap(r => r.test_ids));
  $("contract-state").textContent = (registry.contract_status || "proposed") + " contract";
  const results = (active?.results || []).filter(r => ids.has(r.id));
  $("remaining").textContent = scopeAvailable ? remaining.conformance_remaining : "—"; $("denominator").textContent = scopeAvailable ? `of ${requirements.length} tracked requirements` : "Scope outside this measurement";
  $("coverage").textContent = scopeAvailable ? remaining.coverage_remaining : "—";
  $("decisions").textContent = scopeAvailable ? requirements.filter(r => r.state === "needs_decision").length : "—";
  $("passing").textContent = active && scopeAvailable ? results.filter(r => r.status === "PASS").length : "—";
  $("test-count").textContent = scopeAvailable ? `${ids.size} selected executable checks · samples, not proofs` : "No measurement for this scope";
  $("updated").textContent = active && scopeAvailable ? `Measured ${active.finished_at.replace("T", " ").replace("Z", " UTC")}` : "Baseline pending";
  $("notice").textContent = !scopeAvailable ? "This scope was not included in the selected measurement. Select Current plan to inspect its requirements; it has no measured zero or completion claim here." :
    state.currentPlan ? "Current proposed plan. Its requirements are visible together; choose a recorded measurement to inspect evidence and burndown history." :
    !attempted.complete ? "The latest attempt is incomplete. The charts retain the last complete measurement, when available; the ledger links the recorded observations." :
    "Measured against one explicit reference profile. Select Current plan for the full roadmap and its human decisions.";
  const values = state.points;
  chart("conformance-chart", values, "conformance_remaining", "#117d75", requirements.length);
  chart("coverage-chart", values, "coverage_remaining", "#466bc3", requirements.length);
  $("history-note").textContent = !scopeAvailable ? "No measurement covers this scope in the selected cohort." : state.currentPlan ? "The current plan is an inventory, not a measurement. Recorded cohorts retain their original contracts and evidence." : complete.length === 1 ? "First complete measurement. This is a real baseline point; no earlier progress or forecast has been invented." : `${complete.length} complete measurements in this fixed cohort. Scope or oracle changes start a new cohort; lines never join incompatible baselines.`;
  $("stages").replaceChildren();
  for (const [stage, name] of Object.entries(stageNames)) {
    const subset = rows.filter(r => r.stage === stage), done = subset.filter(r => r.satisfied).length;
    const row = node("div", undefined, "stage-row"), track = node("div", undefined, "stage-track"), fill = node("div", undefined, "stage-fill");
    fill.style.width = `${subset.length ? done / subset.length * 100 : 0}%`; track.append(fill);
    row.append(node("span", name), track, node("span", subset.length ? `${done} / ${subset.length}` : "No contract")); $("stages").append(row);
  }
  $("attention").replaceChildren();
  const decisions = requirements.filter(r => r.state === "needs_decision");
  for (const req of decisions.slice(0, 5)) {
    const item = link(req.title, "#req-" + req.id); item.className = "attention-item"; item.append(node("span", req.scope + " · " + req.stage));
    item.addEventListener("click", () => { $("search").value = req.id; $("status").value = "all"; $("stage").value = "all"; renderRequirements(); const detail = $("req-" + req.id); if (detail) detail.open = true; });
    $("attention").append(item);
  }
  if (!decisions.length) $("attention").append(node("p", scopeAvailable ? "No unresolved contract decisions in this selection. The Current plan view includes the wider decision queue." : "Select Current plan to inspect this scope.", "muted"));
  if (decisions.length > 5) $("attention").append(node("p", `${decisions.length - 5} more decisions are visible with the tracker’s “Needs decision” filter.`, "muted"));
  renderRequirements(); renderCatalog(); renderLedger();
}

function renderRequirements() {
  if (!state.scopeAvailable) {
    $("row-count").textContent = "This scope is outside the selected measurement.";
    $("rows").replaceChildren(node("p", "Select Current plan to browse its requirements.", "empty"));
    return;
  }
  const query = $("search").value.toLowerCase(), filter = $("status").value, stage = $("stage").value;
  const rows = state.requirements.filter(req => {
    const [status] = displayState(req);
    return (stage === "all" || req.stage === stage) && JSON.stringify(req).toLowerCase().includes(query) &&
      (filter === "all" || filter === status || (filter === "open" && status !== "satisfied") || (filter === "uncovered" && !state.rows[req.id]?.covered));
  });
  $("row-count").textContent = `${rows.length} of ${state.requirements.length} requirements shown`;
  $("rows").replaceChildren();
  for (const req of rows) {
    const [status, label] = displayState(req), detail = node("details", undefined, "requirement"), summary = node("summary");
    detail.id = "req-" + req.id;
    const title = node("span", req.title, "req-title"); title.append(node("span", `${req.id} · ${req.stage}`, "req-meta"));
    summary.append(title, node("span", label, "state " + status)); detail.append(summary);
    const body = node("div", undefined, "req-body"); body.append(node("p", req.contract));
    if (req.owner || req.priority) body.append(node("p", `Owner: ${req.owner || "unassigned"} · Priority: ${req.priority || "unprioritised"}`, "muted"));
    if (req.next_action) body.append(node("p", "Next action: " + req.next_action));
    if (req.decision_record) body.append(node("p", "Decision record: " + req.decision_record, "muted"));
    if (req.operations.length) body.append(node("p", req.operations.join(" · "), "revision"));
    if (req.source_groups.length) body.append(node("p", "Source observations: " + req.source_groups.join(", ") + ". A related test does not automatically close the entire source observation.", "muted"));
    if (!req.test_ids.length) body.append(node("p", "No complete test contract is mapped yet. This requirement remains open.", "muted"));
    for (const id of req.test_ids) {
      const result = state.tests[id], line = node("div", undefined, "test-line");
      line.append(node("code", id), node("span", result?.status || "NOT_RUN", result?.status === "PASS" ? "yes" : "no"), node("span", result?.message || "No completed measurement")); body.append(line);
    }
    if (state.detailReport && req.test_ids.length) body.append(link("Full commands, diagnostics and typed results ↗", state.detailReport.download));
    detail.append(body); $("rows").append(detail);
  }
}

function renderCatalog() {
  const catalog = data.catalog, query = $("op-search").value.toLowerCase();
  $("catalog-note").textContent = `${catalog.operations.length} LLVM operations from LLVMOps.td and LLVMIntrinsicOps.td at ${catalog.llvm_revision.slice(0, 12)}. Candidate scope for discussion; other MLIR dialects and target intrinsics are outside this inventory.`;
  let operations = catalog.operations.filter(op => op.name.includes(query));
  if (!showAllOperations && !query) operations = operations.slice(0, 30);
  $("operations").replaceChildren();
  for (const op of operations) {
    const row = node("tr"), name = node("td"); name.append(link(op.name, op.url)); row.append(name);
    row.append(node("td", op.registered_in_veir_snapshot ? "Yes" : "No", op.registered_in_veir_snapshot ? "yes" : "unknown"));
    for (const stage of ["verification", "roundtrip", "execution", "proof"]) {
      const reqs = state.requirements.filter(r => r.stage === stage && r.operations.includes(op.name));
      const done = reqs.filter(r => state.rows[r.id]?.satisfied).length;
      const cell = node("td", reqs.length ? `${done} / ${reqs.length} contracts` : "No contract", !reqs.length ? "unknown" : done === reqs.length ? "yes" : "");
      row.append(cell);
    }
    $("operations").append(row);
  }
  $("more-ops").hidden = showAllOperations || !!query;
}

function renderLedger() {
  $("ledger").replaceChildren();
  for (const report of [...data.reports].reverse()) {
    const row = node("tr"), evidence = node("td"), source = report.sources.veir;
    row.append(node("td", report.finished_at.replace("T", " ").replace("Z", "")), node("td", report.complete ? "Complete measurement" : "Incomplete attempt", report.complete ? "yes" : "no"), node("td", source.commit.slice(0, 12) + (source.dirty ? " + local changes" : ""), "revision"), node("td", report.cohort.slice(0, 12), "revision"));
    evidence.append(link("Receipt JSON ↗", report.download)); row.append(evidence); $("ledger").append(row);
  }
}
for (const id of ["scope", "cohort"]) $(id).addEventListener("change", render);
for (const id of ["search", "stage", "status"]) $(id).addEventListener("input", renderRequirements);
$("op-search").addEventListener("input", renderCatalog);
$("more-ops").addEventListener("click", () => { showAllOperations = true; renderCatalog(); });
render();
const native = data.native.at(-1);
if (native) {
  $("native").append(node("p", `${native.lit_file_count} lit files · ${native.lean_module_count} Lean source modules · ${native.complete ? "complete accounting" : "incomplete attempt"}`));
  $("native").append(node("p", Object.entries(native.counts).map(([k,v]) => `${v} ${k}`).join(" · "), "muted"));
  $("native").append(link(`Full native receipt · ${native.finished_at}`, native.download));
  if (data.native.length > 1) {
    const history = node("details"); history.append(node("summary", "Earlier native measurements"));
    for (const report of [...data.native].reverse().slice(1)) {
      const row = node("p"); row.append(link(`${report.finished_at} · ${report.complete ? "complete" : "incomplete"}`, report.download)); history.append(row);
    }
    $("native").append(history);
  }
} else $("native").append(node("p", "No native-suite measurement imported yet.", "muted"));
