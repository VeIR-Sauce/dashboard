const test = require("node:test");
const assert = require("node:assert/strict");
const {CURRENT_PLAN, cohortIds, view, requirementState, route, viewHash, actionItems} = require("../web/model.js");

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

test("focused links select a relevant measurement or the unmeasured plan", () => {
  const data = fixture();
  data.registry.scopes.push({id: "llvm-compat"});
  data.cohorts.old.scopes.push({id: "llvm-compat"});
  assert.equal(route(data, "#llvm").scope, "llvm-compat");
  assert.equal(route(data, "#llvm").cohort, "old");
  assert.equal(route(data, "#core").cohort, CURRENT_PLAN);
  assert.equal(route(data, "#plan").status, "decision");
  assert.equal(route(data, "#all").full, true);
  assert.equal(route(data, "#requirements"), null);
});

test("view links preserve filters, explicit all status, cohort and contract across reloads", () => {
  const selection = {scope: "llvm", cohort: "old", search: 'vector<4xi32> & poison',
    stage: "verification", status: "all", requirement: "a", full: true};
  const restored = route(fixture(), viewHash(selection));
  assert.deepEqual(restored, {...selection, parsing: false, parsingSearch: "", parsingStatus: "all", parsingMode: "strict", parsingRun: "", parsingCategory: "all", parsingCase: "", warning: ""});
});

test("invalid links fall back safely and report an unavailable measurement", () => {
  const restored = route(fixture(), "#view?scope=absent&cohort=gone&stage=bogus&status=bogus");
  assert.equal(restored.scope, "all");
  assert.equal(restored.cohort, "old");
  assert.equal(restored.stage, "all");
  assert.match(restored.warning, /unavailable/);
  assert.equal(route(fixture(), "#view?cohort=old&scope=core").cohort, "old");
});

test("action queue prioritizes measured failures and does not present passing contracts as work", () => {
  const data = fixture();
  assert.deepEqual(actionItems(view(data, "old")), []);
  data.reports[0].summary.rows[0].satisfied = false;
  data.reports[0].results[0].status = "MISSING_CAPABILITY";
  const items = actionItems(view(data, "old"));
  assert.equal(items.length, 1);
  assert.equal(items[0].failures[0].id, "case");
  assert.equal(actionItems(view(data, CURRENT_PLAN))[0].status, "decision");
});

test("parsing page links retain operation and evidence filters", () => {
  const selection = {...route(fixture(), "#llvm-parse"), parsingSearch: "llvm.add", parsingStatus: "partial", parsingMode: "permissive", parsingRun: "parser-baseline", parsingCategory: "core", parsingCase: "llvm.add.scalable"};
  assert.deepEqual(route(fixture(), viewHash(selection)), selection);
  assert.equal(route(fixture(), "#llvm-parse?evidence=observed").parsingStatus, "parsed");
});

test("parser view uses its own measured catalog and keeps strict and permissive outcomes separate", () => {
  const {parsingView} = require("../web/model.js");
  const data = {...fixture(), catalog: {operations: [{name: "llvm.future"}]}, parsing: [{
    id: "parse-one", complete: true, operations: [{name: "llvm.add"}, {name: "llvm.intr.ceil"}],
    results: [{operation: "llvm.add", strict: {status: "parsed"}, permissive: {status: "parsed"}},
      {operation: "llvm.intr.ceil", strict: {status: "rejected"}, permissive: {status: "parsed"}}]
  }]};
  assert.equal(parsingView(data, "", "strict", "parsed").rows.length, 1);
  assert.equal(parsingView(data, "", "permissive", "parsed").rows.length, 2);
  assert.equal(parsingView(data, "", "permissive", "parsed", "CEIL").rows[0].operation, "llvm.intr.ceil");
  assert.equal(parsingView(data, "", "strict", "all", "", "core").rows.length, 1);
  const categories = parsingView(data).categories;
  assert.equal(categories.find(c => c.id === "core").strict.parsed, 1);
  assert.equal(categories.find(c => c.id === "intrinsics").strict.rejected, 1);
  assert.equal(categories.reduce((total, c) => total + c.total, 0), 2);
  assert.match(parsingView(data, "gone").warning, /unavailable/);
  data.parsing.push({...data.parsing[0], id: "incomplete", complete: false});
  assert.equal(parsingView(data).report.id, "parse-one");
  assert.equal(parsingView(data, "incomplete").report.id, "incomplete");
  assert.equal(parsingView({...data, parsing: []}).rows[0].strict.status, "not_tested");
});

test("adding cases cannot inflate category operation counts and partial support stays visible", () => {
  const {parsingView} = require("../web/model.js");
  const data = {...fixture(), catalog: {operations: [{name: "llvm.add"}]}, parsing: [{
    id: "expanded", complete: true, operations: [{name: "llvm.add"}],
    results: [{operation: "llvm.add", cases: Array(8).fill({}),
      strict: {status: "partial", parsed: 7, total: 8}, permissive: {status: "parsed", parsed: 8, total: 8}}]
  }]};
  const state = parsingView(data, "", "strict", "partial");
  assert.equal(state.total, 1);
  assert.equal(state.categories[0].total, 1);
  assert.equal(state.categories[0].strict.partial, 1);
  assert.equal(state.rows[0].strict.parsed, 7);
  assert.equal(parsingView(data, "", "strict", "parsed").rows.length, 0);
  data.parsing[0].results[0].cases.push(...Array(20).fill({}));
  assert.equal(parsingView(data).categories[0].total, 1);
});

test("experimental intrinsics form a disjoint category", () => {
  const {parsingCategory} = require("../web/model.js");
  assert.equal(parsingCategory("llvm.intr.experimental.constrained.fadd"), "experimental");
  assert.equal(parsingCategory("llvm.intr.fadd"), "intrinsics");
  assert.equal(parsingCategory("llvm.call_intrinsic"), "core");
  assert.equal(route(fixture(), "#llvm-parse?category=toString").parsingCategory, "all");
});
