/* Pure view selection, shared by the offline page and dependency-free tests. */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.VeirProgress = api;
})(globalThis, function () {
  "use strict";
  const CURRENT_PLAN = "current-plan";

  function cohortIds(data) {
    return [...new Set([...data.reports].reverse().map(report => report.cohort))];
  }

  function view(data, cohort, scope = "all") {
    const currentPlan = cohort === CURRENT_PLAN;
    const reports = currentPlan ? [] : data.reports.filter(report => report.cohort === cohort);
    if (!currentPlan && !reports.length) throw new Error("Unknown measurement cohort");
    const complete = reports.filter(report => report.complete);
    const active = complete.at(-1), attempted = reports.at(-1);
    const registry = currentPlan ? data.registry : data.cohorts[cohort];
    if (!registry) throw new Error("Missing cohort registry");
    const scopeAvailable = scope === "all" || registry.scopes.some(item => item.id === scope);
    const selected = items => items.filter(item => scope === "all" || item.scope === scope);
    const requirements = selected(registry.requirements);
    const rows = active ? selected(active.summary.rows) : requirements.map(requirement => ({
      id: requirement.id, stage: requirement.stage, scope: requirement.scope,
      covered: false, satisfied: false, test_statuses: []
    }));
    // An incomplete first attempt can still expose its individual observations.
    // It cannot contribute a chart point or satisfy an entire requirement.
    const detailReport = active || attempted;
    const tests = Object.fromEntries((detailReport?.results || []).map(result => [result.id, result]));
    const points = scopeAvailable ? complete.map(report => {
      const counts = report.counts_by_scope[scope];
      if (!counts) throw new Error("Missing recorded counts for a cohort scope");
      return {...report, value: counts};
    }) : [];
    return {currentPlan, reports, complete, active, attempted, detailReport,
      registry, requirements, scopeAvailable, points,
      rowList: rows, rows: Object.fromEntries(rows.map(row => [row.id, row])), tests};
  }

  function requirementState(requirement, state) {
    const row = state.rows[requirement.id];
    if (requirement.state === "needs_decision") return ["decision", "Needs decision"];
    if (row?.satisfied) return ["satisfied", "Satisfied"];
    if (requirement.test_ids.some(id => ["FAIL", "MISSING_CAPABILITY"].includes(state.tests[id]?.status))) {
      return ["failed", "Failing checks"];
    }
    if (!requirement.test_ids.length) return ["uncovered", "Needs tests"];
    if (!row?.covered) return ["uncovered", "No complete evidence"];
    return ["open", "Open"];
  }

  const statuses = ["all", "open", "satisfied", "uncovered", "decision", "failed"];
  const stages = ["all", "verification", "roundtrip", "execution", "transformation", "regression", "proof"];
  const parsingStatuses = ["parsed", "rejected", "blocked", "error", "not_tested"];
  const parsingCategories = {core: "Core operations", intrinsics: "Intrinsics", experimental: "Experimental intrinsics"};
  function parsingCategory(name) {
    return name.startsWith("llvm.intr.experimental.") ? "experimental" : name.startsWith("llvm.intr.") ? "intrinsics" : "core";
  }

  function route(data, hash = "") {
    const [name, query = ""] = hash.replace(/^#/, "").split("?", 2);
    if (["requirements", "catalog"].includes(name)) return null; // Existing section links.
    const params = new URLSearchParams(query);
    const scopeIds = new Set(["all", ...data.registry.scopes.map(s => s.id),
      ...Object.values(data.cohorts).flatMap(r => r.scopes.map(s => s.id))]);
    const preset = name === "llvm" ? "llvm-compat" : scopeIds.has(name) ? name : "all";
    const requestedScope = params.get("scope") || preset;
    const scope = scopeIds.has(requestedScope) ? requestedScope : "all";
    const cohorts = cohortIds(data);
    const defaultCohort = name === "plan" ? CURRENT_PLAN :
      cohorts.find(id => scope === "all" || data.cohorts[id].scopes.some(s => s.id === scope)) || CURRENT_PLAN;
    const requestedCohort = params.get("cohort") || defaultCohort;
    const cohort = requestedCohort === CURRENT_PLAN || cohorts.includes(requestedCohort) ? requestedCohort : defaultCohort;
    const full = name === "all" || params.get("layout") === "full";
    const status = params.get("status") || (name === "plan" ? "decision" : full ? "all" : "open");
    return {scope, cohort, full, parsing: name === "llvm-parse", status: statuses.includes(status) ? status : "all",
      stage: stages.includes(params.get("stage")) ? params.get("stage") : "all",
      search: params.get("q") || "", requirement: params.get("req") || "",
      parsingSearch: params.get("op") || "",
      parsingStatus: params.get("evidence") === "observed" ? "parsed" : params.get("evidence") === "unknown" ? "not_tested" : parsingStatuses.includes(params.get("evidence")) ? params.get("evidence") : "all",
      parsingMode: params.get("mode") === "permissive" ? "permissive" : "strict",
      parsingRun: params.get("run") || "",
      parsingCategory: Object.hasOwn(parsingCategories, params.get("category")) ? params.get("category") : "all",
      warning: requestedCohort !== cohort ? "The linked measurement is unavailable; showing the latest available view." : ""};
  }

  function viewHash(selection) {
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries({scope: selection.scope, cohort: selection.cohort,
      stage: selection.stage, status: selection.status, q: selection.search,
      req: selection.requirement, layout: selection.full ? "full" : ""})) {
      if (value && value !== "all") params.set(key, value);
    }
    // Preserve an explicit all-status filter instead of reverting to open.
    if (selection.status === "all") params.set("status", "all");
    if (selection.parsing && selection.parsingSearch) params.set("op", selection.parsingSearch);
    if (selection.parsing && parsingStatuses.includes(selection.parsingStatus)) params.set("evidence", selection.parsingStatus);
    if (selection.parsing && selection.parsingMode === "permissive") params.set("mode", "permissive");
    if (selection.parsing && selection.parsingRun) params.set("run", selection.parsingRun);
    if (selection.parsing && Object.hasOwn(parsingCategories, selection.parsingCategory)) params.set("category", selection.parsingCategory);
    return (selection.parsing ? "#llvm-parse?" : "#view?") + params.toString();
  }

  function actionItems(state) {
    return state.requirements.map(requirement => {
      const failures = requirement.test_ids.map(id => state.tests[id])
        .filter(test => test && ["FAIL", "MISSING_CAPABILITY"].includes(test.status));
      return {requirement, failures, status: requirementState(requirement, state)[0]};
    }).filter(item => item.status !== "satisfied").sort((a, b) => {
      const rank = {failed: 0, decision: 1, uncovered: 2, open: 3};
      return rank[a.status] - rank[b.status] || b.failures.length - a.failures.length ||
        a.requirement.id.localeCompare(b.requirement.id);
    });
  }

  function parsingView(data, runId = "", mode = "strict", status = "all", query = "", category = "all") {
    const reports = data.parsing || [];
    const report = reports.find(r => r.id === runId) || reports.findLast(r => r.complete) || reports.at(-1);
    const byName = new Map((report?.results || []).map(row => [row.operation, row]));
    const operations = report?.operations || data.catalog.operations;
    const rows = operations.map(op => ({...op, ...(byName.get(op.name) || {
      operation: op.name, strict: {status: "not_tested"}, permissive: {status: "not_tested"}})}));
    const categories = Object.entries(parsingCategories).map(([id, title]) => {
      const selected = rows.filter(row => parsingCategory(row.operation) === id);
      const count = mode => Object.fromEntries(parsingStatuses.map(status => [status, selected.filter(row => row[mode].status === status).length]));
      return {id, title, total: selected.length, strict: count("strict"), permissive: count("permissive")};
    });
    return {report, total: operations.length, categories,
      warning: runId && runId !== report?.id ? "The linked parser run is unavailable; showing the latest available run." : "",
      rows: rows.filter(row => row.operation.includes(query.toLowerCase()) && (status === "all" || row[mode].status === status) &&
        (category === "all" || parsingCategory(row.operation) === category))};
  }

  return {CURRENT_PLAN, cohortIds, view, requirementState, route, viewHash, actionItems, parsingView, parsingCategory};
});
