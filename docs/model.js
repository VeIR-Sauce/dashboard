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

  return {CURRENT_PLAN, cohortIds, view, requirementState};
});
