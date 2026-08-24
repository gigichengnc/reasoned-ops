# ReasonedTrace (experimental lab)

> An append-only provenance layer for human–AI decisions.

ReasonedTrace is an experimental side project inside the ReasonedOps repository. It generalises one idea from ReasonedOps: a human override should not erase the machine proposal that came before it.

ReasonedOps v1 remains frozen. Nothing under `labs/reasoned_trace/` is part of the published `reasoned-ops` package or its v1 API.

## Research question

Can a human–AI output workflow be represented as an append-only, vendor-neutral decision ledger that remains reconstructable and tamper-evident without exposing hidden chain-of-thought?

## What this MVP records

A trace is a sequence of observable events such as:

1. human input;
2. model proposal;
3. evidence/tool retrieval;
4. policy or guardrail result;
5. human confirmation, edit, or rejection;
6. effective output.

Each event stores the actor, event type, payload, timestamp, parent event, previous event hash, and its own hash.

The MVP intentionally records **observable provenance**, not hidden model reasoning. A model-supplied rationale may be stored only if the application actually received it, and it should be labelled as model output rather than ground-truth internal reasoning.

## Properties the MVP tries to prove

### 1. Reconstructability

The trace keeps the original model proposal and the final human-approved output as separate events.

### 2. Non-overwrite

A human edit appends another event. It does not mutate or replace the earlier model event.

### 3. Tamper evidence

Events are hash-chained. Modifying a historical event after the fact breaks verification for that event or a later link in the chain.

This is **tamper-evident, not tamper-proof**. An attacker who can rewrite the entire ledger and recompute every hash can create a new internally consistent history. Stronger guarantees would require signatures, trusted timestamps, or an external transparency log.

## Run the demo

From the repository root:

```bash
python labs/reasoned_trace/demo.py
```

Run the lab tests:

```bash
pytest labs/reasoned_trace/tests
```

## Example trace

```text
human_input
    ↓
model_proposal
    ↓
evidence_retrieval
    ↓
policy_check
    ↓
human_override
    ↓
effective_output
```

The demo also prints a unified diff between the model proposal and the human-edited response.

## Scope boundary

This MVP does **not** provide:

- access to hidden chain-of-thought;
- proof that a model rationale is faithful;
- authentication, RBAC, or production privacy controls;
- cryptographic signatures or trusted timestamping;
- OpenTelemetry or W3C PROV adapters yet;
- a real LLM integration.

Those are later research steps only if the core ledger is useful.

## Possible next steps

1. define a stable event schema and JSON Schema;
2. add OpenTelemetry GenAI import/export;
3. add W3C PROV export;
4. add signed events or external anchoring;
5. build a small review UI showing model proposal → human diff → effective output;
6. evaluate reconstruction accuracy and reviewer usefulness on controlled human–AI tasks.
