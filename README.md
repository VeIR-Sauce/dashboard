# VeIR progress and correctness tracker

This repository contains the standalone tracker and its tested HTML interface.
The deployment target is [VeIR-Sauce/dashboard](https://github.com/VeIR-Sauce/dashboard),
with the website at [veir-sauce.github.io/dashboard](https://veir-sauce.github.io/dashboard/).
The reviewable static snapshot also opens locally from `docs/index.html`.

An executable **proposed test contract**, a capability tracker, and an offline / GitHub Pages dashboard. The two burndowns measure requirements without completed test evidence and requirements whose stated tests do not yet pass. Passing samples are not proofs, and a missing interpreter is not a completed feature.

The initial registry contains **254 requirements and 564 executable checks**. It spans LLVM dialect verification and preservation, scalar execution, selected small programs and optimization pipelines, VeIR-specific poison/UB behavior, and explicit unfinished work for core IR, other dialects, end-to-end programs and proofs. It is a starting contract to review, not a claim that the complete VeIR project is tested.

## Open the dashboard

Python 3.11 or later is sufficient; no JavaScript packages, server or network connection are needed.

```sh
python3 -m veir_suite validate
python3 -m veir_suite site --history evidence --out site-output
```

Open `site-output/index.html`. Select **Current plan** for the full roadmap and decision queue, or a recorded measurement for its exact scope and evidence. Filter by scope, stage or status, expand requirements, inspect the operation matrix and download the receipts. A scope absent from a measurement is marked unavailable. Each chart point comes from an actual complete measurement. A first baseline is a point, not an invented trend or completion forecast.

## What is the goal?

VeIR describes MLIR-style infrastructure and interoperability. A commitment to all MLIR dialects, passes, execution models and APIs has **not** been assumed. The project decision queue asks humans to choose required programs and dialects, observable behavior, equality/refinement, the compatibility-version policy, and the trusted boundary.

Mathieu's supplied Markdown document is narrower: **44 groups of verifier observations concerning 89 LLVM dialect operations**, with 272 links to LLVM definitions. The original Zulip message and the VeIR revision used for the comparison are unknown. Its linked LLVM revision is recorded separately from our reference build. All 44 source observations remain traceable and open for a deliberate audit; an operation smoke test does not close an entire source observation.

`requirements/catalog.json` independently inventories **344 operations** from pinned `LLVMOps.td` and `LLVMIntrinsicOps.td`. It is a candidate catalogue, not 344 approved project milestones. Other MLIR dialects and target-specific intrinsic definition files are outside it. A registered name is only a source observation, never a claim of complete implementation.

## Run the new suite

The runner uses `veir-opt`, `veir-interpret --json`, `mlir-opt`, `mlir-translate` and `lli`. The verifier, translator and execution engine should come from the **same LLVM commit**. `profiles/ci.json` supplies the initial exact source pins; actual binary hashes and version output are also captured in every run.

The companion VeIR change is currently carried in `integrations/veir-test-instrumentation.patch`. It adds lossless JSON results and makes unavailable native MLIR checks explicit. Prepare an isolated checkout of the pinned base with:

```sh
bash scripts/prepare_veir.sh .artifacts/veir
```

Build that checkout with its declared Lean toolchain. Alternatively point the runner at an already built checkout containing the companion change. On this shared workstation, use the existing `agent-scoped` launcher for builds and execution, and check the current disk budget before growing work. The example assumes all tools have already been built:

```sh
mkdir -p .artifacts
agent-scoped 4G -- env \
  MLIR_OPT=/path/to/llvm/bin/mlir-opt \
  MLIR_TRANSLATE=/path/to/llvm/bin/mlir-translate \
  LLI=/path/to/llvm/bin/lli \
  python3 -u -m veir_suite run \
    --veir /path/to/veir \
    --profile my-pinned-reference \
    --reference-revision FULL_LLVM_COMMIT \
    > .artifacts/run.log 2>&1
```

Use repeated `--scope` options to measure an explicit subset, for example `--scope llvm-compat`. A subset gets its own cohort and denominator. Each run gets a unique directory in `.artifacts/runs/`; `manifest.json` is written before execution, and `report.json` is published atomically after every selected check is accounted for. Per-case inputs, transformed IR, commands and diagnostics are retained there.

Exit codes are `0` for all selected checks passing, `1` for a complete observation containing product failures/missing capabilities, and `2` for incomplete or invalid evidence. Requirements without tests or awaiting decisions remain open even when all executable checks pass.

The old `scripts/run-test.sh` now delegates to this runner (`VEIR_DIR` is required). Its old positional fixture names are replaced by explicit scope selection. `scripts/convert.py` and the three original fixtures remain as historical material; the new oracle never uses that converter.

## Record a measurement

```sh
python3 -m veir_suite report-check .artifacts/runs/RUN_ID/report.json
python3 -m veir_suite record .artifacts/runs/RUN_ID/report.json --history evidence
python3 -m veir_suite site --history evidence --out site-output
```

`record` validates receipts and refuses to overwrite different evidence with the same ID. Incomplete attempts may be recorded and inspected, but do not lower a burndown line. The site retains the last complete measurement and identifies a newer incomplete attempt. Raw receipts describe commands, source commits and hashes, local source changes, tool identities, case hashes and outcomes. They are reproducibility evidence, not cryptographic attestations or formal correctness certificates.

A cohort fixes the acceptance criteria, measurement implementation and reference profile. Changes to VeIR itself can show progress within a cohort. Changes to the contract, tests, oracle binaries or measurement logic start a new cohort; lines never join across those changes. In schema 2, display titles, owners, priorities, next actions and decision-record references do not reset cohorts; the full registry remains hashed for integrity. Schema 1 receipts retain their original identities. Older downloads are compressed, and chart history is reduced to per-scope counts, so the interactive page does not embed every historical command log or native file manifest.

```sh
python3 -m veir_suite compare BEFORE/report.json AFTER/report.json
```

This gates PASS-to-non-PASS regressions only for compatible complete cohorts. It refuses comparisons across changed contracts. `scripts/measurement_gate.py` adds explicit first-baseline handling for CI; a healthy initial measurement can contain known failures and is not a conformance badge.

## Existing VeIR tests

The native lane builds VeIR, runs `lake test`, runs ExArray's test executable and invokes lit with a complete source-file manifest. Install its small Python dependencies into an isolated environment using `requirements-dev.txt`, then run:

```sh
agent-scoped 4G -- python3 -u -m veir_suite native \
  --veir /path/to/veir --lake /path/to/lake --lit /path/to/lit \
  > .artifacts/native.log 2>&1
python3 -m veir_suite record .artifacts/native/RUN_ID/native.json --history evidence
```

Put the intended host `clang`, MLIR tools and lit environment on `PATH`. The runner appends Lake's directory so `Tools/vcc` can find it without overriding a selected host compiler. Native receipts distinguish PASS, XFAIL, FAIL and unavailable/unresolved results; no file count closes an unrelated semantic or proof obligation. The initial source snapshot has 34 Lean unit-test source modules and 1,124 lit files after the three new JSON CLI tests.

Missing or unsupported MLIR is never replaced by a successful `true` command. Optional native runs report affected files as `UNSUPPORTED`; `VEIR_REQUIRE_MLIR=1`, used by the native lane, fails discovery. `scripts/check_reference_visibility.py` exercises both behaviors with real lit workers.

## Extend or change the contract

- `scripts/generate_cases.py` owns generated fixtures and seed contracts. Regenerate, review the diff, and validate hashes after a change.
- Hand-authored additional contracts and tests can live in `requirements/imports/*.json`, with readable fixtures under `cases/`. Every executable test must map to a requirement, and every specified requirement must name its tests.
- `requirements/overrides.json` can assign owners, refine wording and resolve decisions without editing generated files. Do not claim `specified` until executable test mappings exist. Record the human decision and its rationale in version control.
- `scripts/import_native_cases.py --veir CHECKOUT` deliberately snapshots the existing LLVM round-trip fixtures and their source revision. Verification and preservation remain separate contracts.
- `scripts/import_catalog.py` reads `llvm-tblgen --dump-json` output for the two LLVM definition files. Regeneration is explicit and requires a full reference commit ID.

Requirement stages are verification, round-trip, execution, transformation, regression and proof. States are `specified`, `needs_tests` and `needs_decision`. Each requirement has a stable ID, scope, exact acceptance criteria, operation/source links and test IDs. “Satisfied” means that stated bounded test contract passed. It does not mean all behavior of an operation is supported.

## What the checks guarantee

See [the measurement contract](docs/measurement-contract.md) for the exact counting and oracle rules, and [the human decision queue](docs/human-decisions.md) for the connection to human-in-the-loop development.

The reference execution path verifies and translates the **original fixture**, never VeIR's output or a converted substitute. A narrow wrapper calls its zero-argument integer-returning `main` and prints all result bits in 64-bit chunks; return values are not inferred from the process exit code. Defined cases also have independent mathematical expectations. The wrapper currently supports integer results up to 256 bits on the recorded native profile. Memory snapshots, I/O, arbitrary ABIs, external calls, nondeterministic results and general floating-point execution are not claimed.

Negative tests require ordinary rejection and a relevant diagnostic. Crashes, timeouts, missing tools, malformed results and oracle failures remain distinct. LLVM execution is not used as an oracle for undefined behavior or poison; those cases have separately labelled VeIR model contracts. The .fail branch of `Interp.isRefinedBy` remains an explicit human-review item and cannot make an unsupported executable test pass.

## GitHub Pages and CI

The generated snapshot in `docs/` can be opened locally. To refresh it after
recording a validated measurement:

```sh
python3 -m veir_suite site --history evidence --out docs
```

The `checks.yml` workflow runs the harness and browser checks on branch pushes
and PRs, verifies that the committed HTML matches the evidence, and uploads a
reviewable site artifact. It does not build LLVM or Lean.

The `progress.yml` workflow runs the full pinned native and contract measurements
on manual dispatch, with cumulative history and site artifacts. A cold run can
require several hours. Only completed same-repository default-branch push,
scheduled or manual runs can seed history. PR artifacts, incomplete searches,
invalid archives and failed restores cannot silently reset a baseline.

For `VeIR-Sauce/dashboard`, configure GitHub Pages to **Deploy from a branch**,
select branch **codex/veir-progress**, and select **/docs**. This publishes the
committed, tested snapshot at <https://veir-sauce.github.io/dashboard/>. Later
pushes that update `docs/` publish the new snapshot at the same address. The
organization owns this Pages site independently of any personal Pages site.

The complete scheduled measurement and Actions-based Pages deployment template
is retained in `integrations/progress-actions.yml`. Switching to that template
also requires switching the Pages publishing source to **GitHub Actions**. The
manual measurement workflow currently produces reviewable artifacts; recording
that evidence and regenerating `docs/` is a separate reviewed update.

## Validate this implementation

```sh
python3 -m unittest discover -s tests_harness -v
node --test tests_harness/web_model.test.cjs
python3 scripts/generate_cases.py
python3 -m veir_suite validate
python3 -m veir_suite site --history evidence --out site-output
```

The harness tests cover complete manifests, stale fixtures, duplicate IDs/JSON fields, path escapes, truthful completion, missing oracles, compatible cohorts, full-width results, independent inputs, output bounds, timeouts and crashes. They also exercise trusted-history restoration, regression gates and compact site generation. The JavaScript tests check plan selection, incomplete attempts and missing scopes. `scripts/check_browser.cjs` exercises the generated page in an installed Chromium, including filters, receipts and desktop/mobile layouts, without downloading browser packages.
