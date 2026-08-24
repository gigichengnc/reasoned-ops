# ReasonedTrace research plan

## Core question

Can observable human–AI decision provenance be represented as an append-only, vendor-neutral ledger that supports reconstruction and review without claiming access to hidden chain-of-thought?

## MVP propositions

The first implementation is deliberately narrow. It should demonstrate that:

1. a model proposal can remain available after a human override;
2. the effective output can be identified without rewriting the proposal;
3. a reviewer can reconstruct the sequence of observable actions;
4. post-hoc modification of an event is detectable by hash verification;
5. the representation is model-vendor agnostic because the core ledger stores events, not provider-specific internals.

## What would make this research rather than only engineering?

A later study should evaluate the ledger against a baseline chat/history interface on controlled human–AI tasks.

Possible dependent variables:

- reconstruction accuracy: can reviewers correctly identify what the AI proposed and what the human changed?
- provenance completeness: are evidence/tool/policy events recoverable?
- review time: how long does it take to reconstruct a decision?
- error localisation: can reviewers identify the step where an unsupported claim entered the workflow?
- perceived accountability and usability, reported separately from objective reconstruction performance.

## Candidate experimental conditions

- final-output only;
- ordinary chronological chat/log history;
- ReasonedTrace event timeline;
- ReasonedTrace timeline + structured human diff.

## Known limitations

- Hash chaining alone does not prevent a privileged actor from rebuilding the whole history and recomputing hashes.
- A recorded model rationale is still generated text and is not proof of faithful hidden reasoning.
- Completeness depends on instrumentation: an unrecorded tool call or offline human action cannot be reconstructed from the ledger.
- More logging can create privacy and information-governance risks.
- Auditability does not imply that the underlying decision is correct, fair, lawful, or causal.

## Standards direction

If the MVP remains useful, later work can map the event model to:

- W3C PROV concepts for entities, activities, agents, and derivation;
- OpenTelemetry GenAI semantic conventions for observable model/tool traces.

Those adapters should come after the core event semantics are stable.
