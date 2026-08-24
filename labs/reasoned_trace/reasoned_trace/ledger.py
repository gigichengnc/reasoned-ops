"""Append-only, hash-chained provenance events for human-AI workflows."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from difflib import unified_diff
from hashlib import sha256
import json
from typing import Any, Iterable
from uuid import uuid4


GENESIS_HASH = "0" * 64


@dataclass(frozen=True, slots=True)
class TraceEvent:
    """One observable event in a human-AI decision trace.

    ``payload`` should contain only information the application actually observed.
    It must not be presented as access to hidden model chain-of-thought.
    """

    event_id: str
    trace_id: str
    parent_event_id: str | None
    actor_type: str
    actor_id: str
    actor_version: str | None
    event_type: str
    timestamp: str
    payload: dict[str, Any]
    previous_event_hash: str
    event_hash: str

    def without_hash(self) -> dict[str, Any]:
        data = asdict(self)
        data.pop("event_hash")
        return data


class EventLedger:
    """In-memory append-only trace with deterministic hash verification."""

    def __init__(self, trace_id: str | None = None) -> None:
        self.trace_id = trace_id or str(uuid4())
        self._events: list[TraceEvent] = []

    @property
    def events(self) -> tuple[TraceEvent, ...]:
        """Return an immutable view of the current event sequence."""
        return tuple(self._events)

    def append(
        self,
        *,
        actor_type: str,
        actor_id: str,
        event_type: str,
        payload: dict[str, Any],
        actor_version: str | None = None,
        parent_event_id: str | None = None,
        timestamp: str | None = None,
        event_id: str | None = None,
    ) -> TraceEvent:
        """Append a new event without mutating any previous event."""
        if not actor_type.strip():
            raise ValueError("actor_type must not be blank")
        if not actor_id.strip():
            raise ValueError("actor_id must not be blank")
        if not event_type.strip():
            raise ValueError("event_type must not be blank")
        if parent_event_id is not None and parent_event_id not in {
            event.event_id for event in self._events
        }:
            raise ValueError("parent_event_id must refer to an existing event")

        previous_hash = self._events[-1].event_hash if self._events else GENESIS_HASH
        raw = {
            "event_id": event_id or str(uuid4()),
            "trace_id": self.trace_id,
            "parent_event_id": parent_event_id,
            "actor_type": actor_type,
            "actor_id": actor_id,
            "actor_version": actor_version,
            "event_type": event_type,
            "timestamp": timestamp or datetime.now(UTC).isoformat(),
            "payload": payload,
            "previous_event_hash": previous_hash,
        }
        digest = _hash_payload(raw)
        event = TraceEvent(**raw, event_hash=digest)
        self._events.append(event)
        return event

    def verify(self) -> tuple[bool, list[str]]:
        """Verify event hashes, chain links, trace IDs, and parent references."""
        issues: list[str] = []
        known_ids: set[str] = set()
        expected_previous = GENESIS_HASH

        for index, event in enumerate(self._events):
            label = f"event[{index}] {event.event_id}"
            if event.trace_id != self.trace_id:
                issues.append(f"{label}: trace_id mismatch")
            if event.previous_event_hash != expected_previous:
                issues.append(f"{label}: previous_event_hash mismatch")
            expected_hash = _hash_payload(event.without_hash())
            if event.event_hash != expected_hash:
                issues.append(f"{label}: event_hash mismatch")
            if event.parent_event_id is not None and event.parent_event_id not in known_ids:
                issues.append(f"{label}: parent_event_id is not an earlier event")
            if event.event_id in known_ids:
                issues.append(f"{label}: duplicate event_id")

            known_ids.add(event.event_id)
            expected_previous = event.event_hash

        return not issues, issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "reasoned-trace-event-ledger-v0",
            "trace_id": self.trace_id,
            "events": [asdict(event) for event in self._events],
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            indent=indent,
            sort_keys=True,
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EventLedger:
        if data.get("schema") != "reasoned-trace-event-ledger-v0":
            raise ValueError("unsupported or missing ReasonedTrace schema")
        trace_id = str(data["trace_id"])
        ledger = cls(trace_id=trace_id)
        ledger._events = [TraceEvent(**event) for event in data.get("events", [])]
        return ledger

    @classmethod
    def from_json(cls, value: str) -> EventLedger:
        return cls.from_dict(json.loads(value))

    def events_of_type(self, event_type: str) -> tuple[TraceEvent, ...]:
        return tuple(event for event in self._events if event.event_type == event_type)

    def latest_effective_output(self) -> TraceEvent | None:
        outputs = self.events_of_type("effective_output")
        return outputs[-1] if outputs else None


def unified_text_diff(
    before: str,
    after: str,
    *,
    before_label: str = "model_proposal",
    after_label: str = "human_revision",
) -> str:
    """Return a human-readable unified diff between two text outputs."""
    lines: Iterable[str] = unified_diff(
        before.splitlines(keepends=True),
        after.splitlines(keepends=True),
        fromfile=before_label,
        tofile=after_label,
    )
    return "".join(lines)


def _canonical_json(data: dict[str, Any]) -> str:
    try:
        return json.dumps(
            data,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("event payload must be JSON-serializable") from exc


def _hash_payload(data: dict[str, Any]) -> str:
    return sha256(_canonical_json(data).encode("utf-8")).hexdigest()
