# Measurement contract

The denominator is the set of requirements in an explicitly selected registry, not the number of source files, operations mentioned in a document, generated inputs or successful compiler invocations. Each requirement describes exactly what its examples establish. Large semantic claims without an adequate test or proof contract remain open.

## Two burndowns

**Coverage remaining** counts requirements without a completed mapped test contract. A requirement is covered only when its state is `specified`, its test mapping is nonempty, and all mapped cases yield usable observations: PASS, FAIL or MISSING_CAPABILITY. A useful failing test can reduce this backlog.

**Conformance remaining** counts requirements whose stated contract is not yet satisfied. Satisfaction requires coverage and every mapped test passing. Regressions reopen work. Adding generated cases does not by itself improve this metric. Missing tests, unresolved decisions and unsupported interpretations cannot become vacuous successes.

A run is eligible for either line only when the exact selected test set is present, fixture hashes match, all observations are usable, and sources and binaries stayed unchanged during execution. ORACLE_ERROR, HARNESS_ERROR, ENV_ERROR, CRASH, TIMEOUT, OUTPUT_LIMIT and NOT_RUN make it incomplete. These outcomes remain inspectable, and the last complete point remains visible with its date. A crash is never an expected negative diagnostic.

Complete accounting is not an approved project contract or a correctness proof. Native-suite accounting is separate and can include explicit UNSUPPORTED or XFAIL results; it never closes unrelated requirements by file count.

## Check kinds

| Kind | Required observations | Limits |
| --- | --- | --- |
| `verify` | Reference accepts/rejects the original input; VeIR produces the specified outcome. A rejection must exit normally with code 1 and match a relevant diagnostic. | Bounded examples. No semantic execution claim. |
| `roundtrip` | Reference canonicalization of the original equals reference canonicalization after strict VeIR printing; VeIR printing is also stable on reparse. | Preserves tested IR structure/properties, not arbitrary program behavior. No permissive registration bypass. |
| `differential` | LLVM verifies/translates the original, the wrapped LLVM program returns all bits, VeIR's typed result agrees, and independently specified results agree when supplied. | Only deliberately defined deterministic integer-result cases in the named native profile. |
| `pipeline` | Original differential execution succeeds; the named VeIR pipeline yields reference-verified IR whose VeIR execution agrees with the original independent result. | Return-value observations of the selected programs, not a proof of the pass or full memory/I/O equivalence. |
| `interpret` | Actual structured VeIR output equals an explicit model expectation, including type, width, poison/mask, bits and outcome. | Model tests are labelled separately from agreement with LLVM semantics. |

The reference path never consumes converted input or VeIR's printer output for original-program execution. LLVM IR is wrapped only to rename the zero-argument integer-returning entry point and print its complete result in chunks. It must not collide with wrapper symbols. Unsupported signatures fail explicitly.

The initial native profile is Linux x86-64. Integer results are represented as unsigned decimal **strings**, including widths larger than JavaScript's exact number range. Typed floating-point bits, byte poison masks, addresses, registers and field representatives are available in the VeIR CLI protocol; their presence does not imply an independent differential oracle exists for each kind.

Poison and undefined behavior cannot be validated by treating one arbitrary LLVM execution as the expected answer. Such cases live in the VeIR model scope. Defined-reference tests require a concrete integer result and an explicit defined-behavior declaration. A source or target `unsupported_interpretation` never passes a capability contract.

## Historical comparability

A cohort hashes the selected acceptance criteria, the measurement modules, and the reference profile including binary hashes, version output, platform and limits. The registry includes fixture hashes and expectations. Schema 2 omits only registry names, scope titles, and requirement titles, owners, priorities, next actions and decision-record references from that cohort hash. Contract text, states, test mappings, expectations and unknown future fields remain significant. The full registry has a separate integrity hash. Schema 1 receipts keep their original full-registry cohort identity and never join a schema 2 line implicitly. The tested VeIR revision may change within a cohort; otherwise there could be no implementation-progress line. Source identity also includes a full digest of tracked and nonignored source files, so local changes are not hidden behind a commit label.

Changed test expectations, removed requirements, different oracle binaries or changed measurement logic create new cohorts. No connecting line implies that a narrower target was an implementation improvement. Presentation-only changes do not create cohorts. There is no synthetic history, ideal line, inferred percentage of all MLIR, or extrapolated completion date.

Receipts are appended under unique IDs. They retain the complete result manifest and are checked again during site generation. The page embeds only the newest detailed states and compact per-scope historical counts; older full receipts remain downloadable as gzip files. Their integrity checks detect inconsistent summaries, missing/duplicate results, stale fixture hashes and false completion labels. They are not a substitute for trusted CI execution or review of the harness itself.

## Independent validation still needed

The case generator, expectation arithmetic, diagnostic categories and semantic model remain reviewable parts of the trusted boundary. Passing the harness tests does not prove this boundary correct. The initial source observations lack a recorded VeIR comparison revision. Floating-point semantics, general memory/provenance, atomics, external I/O, divergence and nondeterministic behavior need separate chosen contracts and suitable oracles. The proof stage stays open until named statements are built and their transitive axioms and semantic assumptions are reviewed.
