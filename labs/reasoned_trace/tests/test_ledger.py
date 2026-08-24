from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT))

from reasoned_trace import EventLedger, unified_text_diff


def test_human_override_preserves_model_proposal() -> None:
    ledger = EventLedger(trace_id="trace-1")
    proposal = ledger.append(
        actor_type="model",
        actor_id="model-a",
        event_type="model_proposal",
        payload={"text": "Approve the claim."},
    )
    ledger.append(
        actor_type="human",
        actor_id="reviewer-1",
        event_type="human_override",
        parent_event_id=proposal.event_id,
        payload={
            "before_event_id": proposal.event_id,
            "before_text": "Approve the claim.",
            "after_text": "Evidence is insufficient to approve the claim.",
        },
    )

    assert ledger.events[0].payload["text"] == "Approve the claim."
    assert ledger.events[1].payload["after_text"] == (
        "Evidence is insufficient to approve the claim."
    )
    assert len(ledger.events) == 2


def test_round_trip_remains_verifiable() -> None:
    ledger = EventLedger(trace_id="trace-2")
    first = ledger.append(
        actor_type="human",
        actor_id="user",
        event_type="human_input",
        payload={"text": "Question"},
    )
    ledger.append(
        actor_type="model",
        actor_id="model",
        event_type="model_proposal",
        parent_event_id=first.event_id,
        payload={"text": "Draft"},
    )

    restored = EventLedger.from_json(ledger.to_json())
    valid, issues = restored.verify()

    assert valid is True
    assert issues == []
    assert restored.to_dict() == ledger.to_dict()


def test_tampering_is_detected() -> None:
    ledger = EventLedger(trace_id="trace-3")
    ledger.append(
        actor_type="model",
        actor_id="model",
        event_type="model_proposal",
        payload={"text": "Original"},
    )
    ledger.append(
        actor_type="system",
        actor_id="app",
        event_type="effective_output",
        payload={"text": "Original"},
    )

    original = ledger._events[0]
    ledger._events[0] = replace(original, payload={"text": "Silently changed"})

    valid, issues = ledger.verify()

    assert valid is False
    assert any("event_hash mismatch" in issue for issue in issues)


def test_parent_must_reference_an_earlier_event() -> None:
    ledger = EventLedger(trace_id="trace-4")

    try:
        ledger.append(
            actor_type="model",
            actor_id="model",
            event_type="model_proposal",
            parent_event_id="missing-event",
            payload={"text": "Draft"},
        )
    except ValueError as exc:
        assert "parent_event_id" in str(exc)
    else:
        raise AssertionError("missing parent should have been rejected")


def test_effective_output_is_separate_from_model_proposal() -> None:
    ledger = EventLedger(trace_id="trace-5")
    ledger.append(
        actor_type="model",
        actor_id="model",
        event_type="model_proposal",
        payload={"text": "Model text"},
    )
    ledger.append(
        actor_type="system",
        actor_id="app",
        event_type="effective_output",
        payload={"text": "Human-approved text"},
    )

    effective = ledger.latest_effective_output()

    assert effective is not None
    assert effective.payload["text"] == "Human-approved text"
    assert ledger.events_of_type("model_proposal")[0].payload["text"] == "Model text"


def test_unified_diff_surfaces_human_edit() -> None:
    diff = unified_text_diff(
        "Company A complies.\n",
        "Evidence is insufficient to conclude compliance.\n",
    )

    assert "-Company A complies." in diff
    assert "+Evidence is insufficient to conclude compliance." in diff
