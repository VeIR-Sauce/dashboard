const test = require("node:test");
const assert = require("node:assert/strict");
const {CURRENT_PLAN, cohortIds, view, requirementState} = require("../web/model.js");

function fixture() {
  const requirement = {id: "a", scope: "llvm", stage: "verification", state: "specified", test_ids: ["case"]};
  const registry = {scopes: [{id: "llvm"}], requirements: [requirement]};
  const report = {id: "r1", cohort: "old", complete: true, counts_by_scope: {
    all: {coverage_remaining: 0, conformance_remaining: 0},
    llvm: {coverage_remaining: 0, conformance_remaining: 0}},
    summary: {rows: [{...requirement, covered: true, satisfied: true}]},
    results: [{id: "case", status: "PASS"}]};
  return {registry: {scopes: [...registry.scopes, {id: "core"}],
    requirements: [...registry.requirements, {id: "b", scope: "core", stage: "proof", state: "needs_decision", test_ids: []}]},
    cohorts: {old: registry}, reports: [report]};
}

test("current plan exposes the full decision queue without claiming measured success", () => {
  const state = view(fixture(), CURRENT_PLAN);
  assert.equal(state.requirements.length, 2);
  assert.equal(state.points.length, 0);
  assert.equal(state.rows.a.satisfied, false);
  assert.deepEqual(requirementState(state.requirements[1], state), ["decision", "Needs decision"]);
});

test("unmeasured scope has no fabricated zero point", () => {
  const state = view(fixture(), "old", "core");
  assert.equal(state.scopeAvailable, false);
  assert.deepEqual(state.points, []);
  assert.deepEqual(state.requirements, []);
});

test("a newer incomplete attempt retains the last complete baseline and observations", () => {
  const data = fixture();
  data.reports.push({...data.reports[0], id: "r2", complete: false,
    results: [{id: "case", status: "ENV_ERROR"}]});
  const state = view(data, "old");
  assert.equal(state.active.id, "r1");
  assert.equal(state.attempted.id, "r2");
  assert.equal(state.points.length, 1);
  assert.equal(state.tests.case.status, "PASS");
});

test("an incomplete first attempt exposes failures without closing requirements", () => {
  const data = fixture();
  data.reports[0].complete = false;
  data.reports[0].results[0].status = "FAIL";
  const state = view(data, "old");
  assert.equal(state.points.length, 0);
  assert.equal(state.rows.a.satisfied, false);
  assert.equal(state.tests.case.status, "FAIL");
  assert.deepEqual(requirementState(state.requirements[0], state), ["failed", "Failing checks"]);
});

test("cohorts are ordered by their latest observation, with no joined line", () => {
  const data = fixture();
  data.cohorts.other = data.cohorts.old;
  data.reports.push({...data.reports[0], id: "r2", cohort: "other"},
                    {...data.reports[0], id: "r3", cohort: "old"});
  assert.deepEqual(cohortIds(data), ["old", "other"]);
  assert.deepEqual(view(data, "old").points.map(p => p.id), ["r1", "r3"]);
});

test("missing evidence counts and unknown cohorts fail explicitly", () => {
  const data = fixture();
  delete data.reports[0].counts_by_scope.llvm;
  assert.throws(() => view(data, "old", "llvm"), /Missing recorded counts/);
  assert.throws(() => view(data, "absent"), /Unknown measurement cohort/);
});
