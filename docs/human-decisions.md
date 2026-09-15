# Where human judgment belongs

The earlier `veir-what-could-be-automated` discussion distinguished a progress metric from a specification and a way to establish correctness. An agent can complete intermediate implementation and proof work once the endpoints and correctness relation are fixed. A decreasing chart cannot decide whether those endpoints describe the intended system.

The registry turns that distinction into explicit work:

| Decision | Why it matters | Concrete outcome to record |
| --- | --- | --- |
| Required programs and dialects | “MLIR parity” can mean syntax, verifier behavior, operations, execution, transformations, APIs or an enormous collection of dialects. | A chosen milestone with supported programs and inputs, named dialects, required layers and explicit exclusions. |
| Observations | Matching one return value can miss memory, I/O, exceptions, external calls or termination. | The observable behavior and relevant ABI/data layout for each endpoint. |
| Correctness relation | Equality, refinement and permitted nondeterminism are different guarantees. | The exact relation under which a transformation or compilation endpoint is correct. |
| Failure semantics | Rejecting or failing to interpret every interesting program must not count as successful development. | Required support as a separate obligation and a reviewed treatment of unsupported behavior. |
| Trusted boundary | A valid theorem can concern an inaccurate model or depend on unwanted axioms. | The trusted parser, interpreter/model fidelity, theorem dependencies, axioms, external tools and hardware assumptions. |
| Reference policy | A moving MLIR target can change old tests without any VeIR change. | An approved pinned revision/release policy and a procedure for reviewing new baselines. |

`Interp.isRefinedBy` in the current VeIR source treats a source `.fail` as permitting any target. That can be useful for a partial interpreter, but it cannot establish that a required feature has been implemented. The suite reports unsupported interpretation as `MISSING_CAPABILITY`; the refinement decision remains open. Likewise, compile-time Lean success is not automatically an axiom-free end-to-end compiler proof.

Agents can add cases, implement missing behavior, minimize failures, run independent checks, produce patches and attempt proofs against a reviewed contract. Human attention should focus on changing the model, expanding/narrowing the required support, choosing assumptions, reviewing proof dependencies, or diagnosing tasks that stall because the contract is wrong. Routine green checks do not require a new human interaction.

The first useful milestone can be smaller than all MLIR. For example, a chosen LLVM core fragment plus a few representative programs would permit well-defined support and semantic claims while the wider operation catalogue remains candidate work. The tracker does not select that milestone on the user's behalf. Its existing scope filters and stable requirement IDs allow the choice to be made without discarding the measurement design.

Record decisions alongside the code. `requirements/project.json` defines the scope list; `requirements/overrides.json` refines generated requirements and may include fields such as `owner`, `priority`, `decision_record` and `next_action`. New hand-authored obligations belong in `requirements/imports/`. Resolving a decision normally turns it into work needing tests or proofs, not an immediately satisfied requirement. The changed contract creates a distinct cohort so a human decision cannot be confused with implementation progress.
