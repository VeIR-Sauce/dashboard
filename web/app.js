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
for (const report of [...(data.parsing || [])].reverse()) {
  const option = node("option", `${report.finished_at.replace("T", " ").replace("Z", " UTC")}${report.complete ? "" : " · incomplete"}`);
  option.value = report.id; $("parse-run").append(option);
}
const scopes = new Map(data.registry.scopes.map(s => [s.id, s]));
for (const registry of Object.values(data.cohorts)) for (const scope of registry.scopes) if (!scopes.has(scope.id)) scopes.set(scope.id, scope);
for (const scope of scopes.values()) { const option = node("option", scope.title); option.value = scope.id; $("scope").append(option); }
let state = {}, showAllOperations = false, fullView = false, parsingView = false, routeWarning = "";
const disclosures = ["measurement-controls", "progress-details", "context-details", "requirement-details", "catalog-details", "ledger-details"];
function selection(extra = {}) {
  return {scope: $("scope").value, cohort: $("cohort").value, stage: $("stage").value,
    status: $("status").value, search: $("search").value, full: fullView, parsing: parsingView,
    parsingSearch: $("parse-search").value, parsingStatus: $("parse-status").value,
    parsingMode: $("parse-mode").value, parsingRun: $("parse-run").value, parsingCategory: $("parse-category").value, ...extra};
}
function syncLink() {
  const hash = progress.viewHash(selection());
  history.replaceState(null, "", hash); $("share-view").href = hash;
}
function requirementLink(req, label) {
  return link(label || req.title, progress.viewHash(selection({requirement: req.id, search: "", stage: "all", status: "all", parsing: false})));
}
function applyRoute() {
  const route = progress.route(data, location.hash);
  if (!route) {
    parsingView = false;
    document.body.classList.remove("parsing-view"); $("parsing-page").hidden = true;
    render();
    const section = location.hash.slice(1);
    $(section === "catalog" ? "catalog-details" : "requirement-details").open = true;
    $(section).scrollIntoView();
    return;
  }
  fullView = route.full; parsingView = route.parsing; routeWarning = route.warning;
  document.body.classList.toggle("parsing-view", parsingView);
  $("parsing-page").hidden = !parsingView;
  $("scope").value = route.scope; $("cohort").value = route.cohort;
  $("stage").value = route.stage; $("status").value = route.status;
  $("search").value = route.requirement || route.search;
  $("parse-search").value = route.parsingSearch; $("parse-status").value = route.parsingStatus;
  $("parse-mode").value = route.parsingMode;
  $("parse-category").value = route.parsingCategory;
  $("parse-run").value = (data.parsing || []).some(r => r.id === route.parsingRun) ? route.parsingRun : "";
  if (route.parsingRun && !$("parse-run").value) routeWarning = "The linked parser run is unavailable; showing the latest available run.";
  for (const id of disclosures) $(id).open = fullView;
  render();
  $("share-view").href = progress.viewHash(selection({requirement: route.requirement}));
  if (route.requirement) {
    $("requirement-details").open = true;
    const detail = $("req-" + route.requirement);
    if (detail) { detail.open = true; detail.scrollIntoView({block: "start"}); }
    else $("row-count").textContent = "This requirement is not present in the linked measurement. Try the Current plan view.";
  } else window.scrollTo(0, 0);
}

function chart(id, runs, field, color, total) {
  const container = $(id); container.replaceChildren();
  if (!runs.length) { container.append(node("div", state.currentPlan ? "This is a plan. Choose a recorded measurement to see a burndown." : "No complete measurement for this scope yet.", "empty")); return; }
  if (runs.length === 1) container.append(node("p", `Baseline: ${runs[0].value[field]} of ${total} requirements ${field === "coverage_remaining" ? "lack complete evidence" : "remain open"}. A second measurement is needed to show change.`, "baseline"));
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
  const scopeTitle = $("scope").value === "all" ? "VeIR" : scopes.get($("scope").value)?.title || "VeIR";
  $("view-title").textContent = state.currentPlan ? "Decide what VeIR should support." : scopeTitle + ": what needs work?";
  $("view-intro").textContent = state.currentPlan ? "Agree the open contracts, then define the examples and evidence needed to close them." : "Pick an open contract, inspect its failing examples, then use the receipt to reproduce the result.";
  $("selection-label").textContent = `${scopeTitle} · ${state.currentPlan ? "current proposed plan" : "recorded measurement"} · change selection`;
  document.querySelectorAll("[data-view]").forEach(a => {
    const activeView = parsingView ? "llvm-parse" : fullView ? "all" : state.currentPlan ? "plan" : $("scope").value === "llvm-compat" ? "llvm" : "overview";
    if (a.dataset.view === activeView) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current");
  });
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
  if (routeWarning) $("notice").textContent = routeWarning + " " + $("notice").textContent;
  const values = state.points;
  chart("conformance-chart", values, "conformance_remaining", "#117d75", requirements.length);
  chart("coverage-chart", values, "coverage_remaining", "#466bc3", requirements.length);
  $("history-note").textContent = !scopeAvailable ? "No measurement covers this scope in the selected cohort." : state.currentPlan ? "The current plan is an inventory, not a measurement. Recorded cohorts retain their original contracts and evidence." : complete.length === 1 ? "First complete measurement. This is a real baseline point; no earlier progress or forecast has been invented." : `${complete.length} complete measurements in this fixed cohort. Scope or oracle changes start a new cohort; lines never join incompatible baselines.`;
  $("progress-details").querySelector("summary").textContent = `Progress and burndown · ${state.currentPlan || !scopeAvailable ? "no measurement for this selection" : `${remaining.conformance_remaining} open · ${complete.length} measurement${complete.length === 1 ? "" : "s"}`}`;
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
    const item = requirementLink(req); item.className = "attention-item"; item.append(node("span", req.scope + " · " + req.stage));
    $("attention").append(item);
  }
  if (!decisions.length) $("attention").append(node("p", scopeAvailable ? "No unresolved contract decisions in this selection. The Current plan view includes the wider decision queue." : "Select Current plan to inspect this scope.", "muted"));
  if (decisions.length > 5) $("attention").append(node("p", `${decisions.length - 5} more decisions are visible with the tracker’s “Needs decision” filter.`, "muted"));
  if (parsingView) {
    $("view-title").textContent = "LLVM dialect: parsing";
    $("view-intro").textContent = "Actual parser-only results, with a valid input and diagnostics for each operation.";
  }
  renderParsing(); renderActions(); renderRequirements(); renderCatalog(); renderLedger();
}

function renderParsing() {
  const parsed = progress.parsingView(data, $("parse-run").value, $("parse-mode").value, $("parse-status").value, $("parse-search").value, $("parse-category").value);
  const {report, rows, total} = parsed;
  $("parsing-note").textContent = report ? `${report.counts.strict.parsed || 0} of ${total} examples parse strictly; ${report.counts.permissive.parsed || 0} parse with unregistered operations allowed. Measured ${report.finished_at.replace("T", " ").replace("Z", " UTC")} with VeIR ${report.source.commit.slice(0, 12)}${report.source.dirty ? " + local changes" : ""}, MLIR ${report.llvm_revision.slice(0, 12)}.${report.complete ? "" : " This attempt is incomplete."}` : "No parser-only measurement has been recorded yet.";
  if (routeWarning) $("parsing-note").textContent += " " + routeWarning;
  $("parsing-receipt").hidden = !report;
  if (report) $("parsing-receipt").href = report.download;
  $("parsing-categories").replaceChildren();
  for (const category of parsed.categories) {
    const card = link("", progress.viewHash(selection({parsing: true, parsingCategory: category.id, parsingSearch: "", parsingStatus: "all"})));
    card.className = "parse-category";
    if ($("parse-category").value === category.id) card.setAttribute("aria-current", "true");
    card.append(node("strong", category.title), node("span", `${category.strict.parsed} / ${category.total} parsed strictly`));
    card.append(node("small", `${category.permissive.parsed} / ${category.total} with unregistered allowed`));
    $("parsing-categories").append(card);
  }
  $("parsing-count").textContent = `${rows.length} of ${total} operations shown`;
  $("parsing-operations").replaceChildren();
  const labels = {parsed: "Parsed", rejected: "Rejected", blocked: "Blocked", not_tested: "Not tested", error: "Error"};
  for (const op of rows) {
    const row = node("tr"), name = node("td"), evidence = node("td");
    name.append(link(op.operation, op.url)); row.append(name);
    for (const mode of ["strict", "permissive"]) row.append(node("td", labels[op[mode].status], "parse-" + op[mode].status));
    if (op.input) {
      const details = node("details", undefined, "parse-examples");
      details.append(node("summary", "Inspect example"));
      const links = node("p", undefined, "parse-links");
      links.append(link("Download input", op.input.download));
      links.append(link("Link to this result", progress.viewHash(selection({parsing: true, parsingSearch: op.operation, parsingStatus: "all", parsingRun: report.id}))));
      const source = op.input.source;
      if (source.repository === "llvm/llvm-project") links.append(link("LLVM source", `https://github.com/llvm/llvm-project/blob/${source.revision}/${source.path}`));
      details.append(links, node("pre", op.input.text, "parse-input"));
      for (const mode of ["strict", "permissive"]) {
        if (op[mode].diagnostic) {
          details.append(node("p", (mode === "strict" ? "Strict" : "Allow unregistered") + " diagnostic", "diagnostic-label"));
          details.append(node("pre", op[mode].diagnostic, "parse-diagnostic"));
        }
      }
      if (op.reference_diagnostic) details.append(node("pre", op.reference_diagnostic, "parse-diagnostic"));
      details.append(node("p", `Input SHA-256: ${op.input.sha256}`, "input-hash"));
      evidence.append(details);
    } else evidence.append(node("span", "No reference-validated input recorded", "muted"));
    row.append(evidence); $("parsing-operations").append(row);
  }
}

function renderActions() {
  const items = progress.actionItems(state), failing = items.filter(x => x.status === "failed");
  $("actions").replaceChildren();
  $("actions-title").textContent = state.currentPlan ? "Decisions and missing tests" : "Open contracts to investigate";
  $("action-note").textContent = !state.scopeAvailable ? "This scope has no recorded evidence in the selected measurement. Choose Current plan to see its proposed work." :
    failing.length ? `${failing.length} contracts have failing checks or missing capabilities. Showing ${Math.min(5, items.length)} open contracts, with the most failing examples first. Check counts do not measure workload impact.` :
    state.currentPlan ? "Proposed work, without a passing measurement. Decisions come first; expand a contract to read its acceptance criteria." :
    items.length ? "Open work in this measurement. Expand a contract to inspect the missing evidence." : "All stated contracts pass in this measurement.";
  for (const {requirement: req, failures, status} of items.slice(0, 5)) {
    const item = node("article", undefined, "action-item"), heading = node("h3");
    heading.append(requirementLink(req)); item.append(heading);
    item.append(node("p", failures.length ? `${failures.length} failing or unsupported checks · ${stageNames[req.stage]}` : displayState(req)[1], "state " + status));
    item.append(node("p", req.next_action || req.contract));
    if (failures.length) item.append(node("code", failures[0].message, "action-diagnostic"));
    item.append(requirementLink(req, failures.length ? "Inspect examples and diagnostics →" : "Read contract →"));
    $("actions").append(item);
  }
  $("all-actions").textContent = `Browse ${items.length} open contracts ↓`;
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
    body.append(requirementLink(req, "Link to this contract ↗"));
    if (req.owner || req.priority) body.append(node("p", `Owner: ${req.owner || "unassigned"} · Priority: ${req.priority || "unprioritised"}`, "muted"));
    if (req.next_action) body.append(node("p", "Next action: " + req.next_action));
    if (req.decision_record) body.append(node("p", "Decision record: " + req.decision_record, "muted"));
    if (req.operations.length) body.append(node("p", req.operations.join(" · "), "revision"));
    if (req.source_groups.length) body.append(node("p", "Source observations: " + req.source_groups.join(", ") + ". A related test does not automatically close the entire source observation.", "muted"));
    if (!req.test_ids.length) body.append(node("p", "No complete test contract is mapped yet. This requirement remains open.", "muted"));
    for (const id of req.test_ids) {
      const result = state.tests[id], line = node("div", undefined, "test-line");
      line.append(node("code", id), node("span", result?.status || "NOT_RUN", result?.status === "PASS" ? "yes" : "no"), node("span", result?.message || "No completed measurement")); body.append(line);
      if (result?.diagnostic) {
        const diagnostic = node("details", undefined, "diagnostic"); diagnostic.append(node("summary", `${result.diagnostic_phase || "Failure"} diagnostic`), node("pre", result.diagnostic)); body.append(diagnostic);
      }
      const fixture = state.registry.tests?.find(test => test.id === id);
      if (fixture?.input) body.append(link("Test input: " + fixture.input,
        "https://github.com/VeIR-Sauce/dashboard/blob/codex%2Fveir-progress/" + fixture.input.split("/").map(encodeURIComponent).join("/")));
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
for (const id of ["scope", "cohort"]) $(id).addEventListener("change", () => { routeWarning = ""; render(); syncLink(); });
for (const id of ["search", "stage", "status"]) $(id).addEventListener("input", () => { renderRequirements(); syncLink(); });
$("all-actions").addEventListener("click", event => {
  event.preventDefault(); $("search").value = ""; $("stage").value = "all"; $("status").value = "open";
  renderRequirements(); syncLink(); $("requirement-details").open = true; $("requirements").scrollIntoView();
});
$("op-search").addEventListener("input", renderCatalog);
for (const id of ["parse-search", "parse-status", "parse-mode", "parse-run", "parse-category"]) $(id).addEventListener("input", () => { renderParsing(); syncLink(); });
$("more-ops").addEventListener("click", () => { showAllOperations = true; renderCatalog(); });
window.addEventListener("hashchange", applyRoute);
// Render once before following an old section-only URL.
render(); applyRoute();
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
