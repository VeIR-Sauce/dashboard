# LLVM parsing measurement

The [parsing page](https://veir-sauce.github.io/dashboard/#llvm-parse) answers a
bounded question: can the measured VeIR binary parse a valid example containing
this LLVM operation in generic MLIR syntax, with VeIR verification disabled?
It does not infer parsing from the compatibility suite or from registration.

## Read a result

Choose a category, find an operation, and open **Inspect example**. The input is
the exact generic MLIR used in the receipt, downloadable from the static site.
The receipt includes its hash, upstream derivation, binary hashes, VeIR source
identity, commands, stdout, stderr, timeouts and verification-mode controls.
**Link to this result** pins the measurement ID; category and outcome filters
also survive reloads. Parser runs are independent of compatibility cohorts.

Both modes pass `--disable-verifiers --print-op-generic` to `veir-opt`.
The second also passes `--allow-unregistered-dialect`.

| Outcome | Evidence |
| --- | --- |
| Parsed | The entire example parsed and printed successfully, including the target operation. |
| Rejected | Ordinary parser rejection names the target operation or points to its source line. |
| Blocked | Another operation, enclosing type, attribute, or surrounding input failed first. |
| Not tested | There is no example, the reference rejected it, or mode controls failed. |
| Error | Timeout, crash, output limit, missing tool, or an unattributable invocation failure. |

A blocked row is not a claim that the target operation itself is unsupported.
Allowing unregistered operations may preserve them as opaque operations. It
does not demonstrate verification, interpretation, lowering or semantic support.
Successful printing establishes a completed invocation, not round-trip fidelity.
Custom assembly syntax and exhaustive type/attribute combinations are outside
this matrix. They need additional explicit cases.

The three categories are disjoint and defined by names:

- **Experimental intrinsics:** `llvm.intr.experimental.*`.
- **Intrinsics:** other `llvm.intr.*` names.
- **Core operations:** the remaining catalogue, including functions, globals,
  structural operations and the `llvm.call_intrinsic` wrapper.

These are navigation categories, not an agreed priority order or a promise of
complete LLVM/MLIR parity. The catalogue remains the pinned `LLVMOps.td` and
`LLVMIntrinsicOps.td` inventory of 344 names.

## Reproduce the matrix

Use an existing built VeIR checkout and the pinned LLVM checkout/reference tool.
No VeIR source modification, interpreter, translator or execution engine is needed.
The importer reads LLVM tests without executing their RUN comments. It extracts
small operations or top-level units with symbol dependencies, validates them
with `mlir-opt`, and prints generic syntax with aliases expanded inline.
Nine handwritten supplements provide four absent operations and five smaller
core examples; they must pass the same reference validation. Derived LLVM inputs
retain source provenance and the Apache-2.0 WITH LLVM-exception license.

```sh
python3 scripts/import_parsing_cases.py \
  --llvm /path/to/pinned/llvm-project \
  --mlir-opt /path/to/pinned/build/bin/mlir-opt
python3 -m veir_suite parse \
  --veir /path/to/built/veir \
  --mlir-opt /path/to/pinned/build/bin/mlir-opt
python3 -m veir_suite report-check .artifacts/parsing/RUN_ID/parsing.json
python3 -m veir_suite record .artifacts/parsing/RUN_ID/parsing.json --history evidence
python3 -m veir_suite site --history evidence --out docs
```

On the shared workstation, run the importer and measurement inside an
`agent-scoped 2G` work scope with output redirected to an SSD log. They use
existing binaries and need no large build or download. On another machine,
reimport with its reference binary before measuring; the runner requires the
same binary hash as the fixture import and revalidates every input anyway.

Before the matrix, controls check that an ill-typed add parses when verification
is disabled, fails verification when enabled, and malformed syntax is rejected.
Every invocation has a deadline and bounded output. Timeouts and crashes stay
distinct from parser rejection. Source, fixture, harness and binary changes
during a run prevent a complete measurement.

`parsing.json` is a separate append-only receipt kind. Every catalogue operation
must have exactly one result, including operations lacking an example. A complete
run means every row produced a usable observation in both modes; rejected or
blocked inputs are still observations. Completeness never means all inputs pass.
The static site copies inputs from the immutable receipt, not the current fixture
directory. Later fixture edits therefore cannot change old evidence links.

The parser lane deliberately does not lower either compatibility burndown.
It has different acceptance criteria, and the initial parser measurement supplies
one baseline rather than an invented trend.
