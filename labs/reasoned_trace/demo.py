"""Small ReasonedTrace demonstration with no external model dependency."""

from __future__ import annotations

import sys
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB_ROOT))

from reasoned_trace import EventLedger, unified_text_diff


def main() -> None:
    ledger = EventLedger(trace_id="demo-compliance-review")

    human = ledger.append(
        actor_type="human",
        actor_id="user-01",
        event_type="human_input",
        payload={
            "text": "Can we say that Company A complies with the regulation?",
        },
    )

    proposal_text = "Company A appears to comply with the regulation."
    model = ledger.append(
        actor_type="model",
        actor_id="example-model",
        actor_version="demo-v0",
        event_type="model_proposal",
        parent_event_id=human.event_id,
        payload={
            "text": proposal_text,
            "rationale_summary": (
                "The available documents contain no obvious contradiction. "
                "This is model-generated output, not hidden chain-of-thought."
            ),
        },
    )

    evidence = ledger.append(
        actor_type="tool",
        actor_id="document-retriever",
        event_type="evidence_retrieval",
        parent_event_id=model.event_id,
        payload={
            "items": [
                {"id": "annual-report", "status": "retrieved"},
                {"id": "regulator-register", "status": "retrieved"},
                {"id": "company-website", "status": "retrieved"},
            ],
            "completeness_established": False,
        },
    )

    policy = ledger.append(
        actor_type="policy",
        actor_id="claim-boundary-v0",
        event_type="policy_check",
        parent_event_id=evidence.event_id,
        payload={
            "result": "caution",
            "reason": "Retrieved evidence does not establish complete regulatory compliance.",
        },
    )

    revised_text = (
        "The available evidence is insufficient to conclude that Company A "
        "complies with all applicable requirements."
    )
    review = ledger.append(
        actor_type="human",
        actor_id="reviewer-01",
        event_type="human_override",
        parent_event_id=policy.event_id,
        payload={
            "action": "edit",
            "reason": "The regulator register does not establish compliance with every requirement.",
            "before_event_id": model.event_id,
            "before_text": proposal_text,
            "after_text": revised_text,
        },
    )

    ledger.append(
        actor_type="system",
        actor_id="reasoned-trace-demo",
        event_type="effective_output",
        parent_event_id=review.event_id,
        payload={
            "text": revised_text,
            "approved_by": "reviewer-01",
        },
    )

    print("ReasonedTrace demo")
    print("=" * 60)
    for index, event in enumerate(ledger.events, start=1):
        print(
            f"{index:02d}  {event.event_type:<20} "
            f"actor={event.actor_type}:{event.actor_id} "
            f"hash={event.event_hash[:10]}…"
        )

    print("\nModel → human diff")
    print("-" * 60)
    print(unified_text_diff(proposal_text, revised_text) or "(no changes)")

    valid, issues = ledger.verify()
    print("Verification:", "PASS" if valid else "FAIL")
    if issues:
        for issue in issues:
            print(" -", issue)

    print("\nLatest effective output")
    print("-" * 60)
    effective = ledger.latest_effective_output()
    if effective is not None:
        print(effective.payload["text"])

    print("\nJSON export is available via ledger.to_json().")


if __name__ == "__main__":
    main()
