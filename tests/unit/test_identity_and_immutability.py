from dataclasses import FrozenInstanceError

import pytest

from paim.integrity import (
    DraftRecord,
    EffectiveInterval,
    EventId,
    RecordId,
    RecordVersionId,
    StatusEvent,
)
from tests.helpers import utc


def test_record_and_version_ids_are_distinct_nominal_types_and_values() -> None:
    record_id = RecordId.new()
    version_id = RecordVersionId.new()

    assert type(record_id) is RecordId
    assert type(version_id) is RecordVersionId
    assert record_id.value != version_id.value


def test_draft_mutates_only_before_finalization() -> None:
    draft = DraftRecord(RecordId.new(), "opaque", "scope", {"value": "draft"})
    draft.mutate({"value": "revised"})
    finalized = draft.finalize(
        recorded_at=utc(2026, 1, 2),
        effective=EffectiveInterval(utc(2026, 1, 1)),
        creator="actor",
    )

    with pytest.raises(RuntimeError, match="finalized"):
        draft.mutate({"value": "illegal"})
    with pytest.raises(FrozenInstanceError):
        finalized.creator = "another"  # type: ignore[misc]

    detached = finalized.content
    detached["value"] = "caller mutation"
    assert finalized.content == {"value": "revised"}


def test_relied_upon_draft_cannot_be_mutated_or_finalized() -> None:
    draft = DraftRecord(RecordId.new(), "opaque", "scope", {"value": "cited"})
    draft.mark_relied_upon()

    with pytest.raises(RuntimeError, match="relied upon"):
        draft.mutate({"value": "illegal"})
    with pytest.raises(RuntimeError, match="relied-upon"):
        draft.finalize(
            recorded_at=utc(2026, 1, 2),
            effective=EffectiveInterval(utc(2026, 1, 1)),
            creator="actor",
        )


def test_substantive_change_requires_a_distinct_version() -> None:
    draft = DraftRecord(RecordId.new(), "opaque", "scope", {"value": "one"})
    original = draft.finalize(
        recorded_at=utc(2026, 1, 2),
        effective=EffectiveInterval(utc(2026, 1, 1)),
        creator="actor",
    )
    successor = original.substantive_successor(
        content={"value": "two"},
        recorded_at=utc(2026, 2, 2),
        effective=EffectiveInterval(utc(2026, 2, 1)),
        creator="actor",
    )

    assert successor.record_id == original.record_id
    assert successor.version_id != original.version_id
    assert original.content == {"value": "one"}


def test_status_event_does_not_alter_finalized_content() -> None:
    draft = DraftRecord(RecordId.new(), "opaque", "scope", {"value": "fixed"})
    finalized = draft.finalize(
        recorded_at=utc(2026, 1, 2),
        effective=EffectiveInterval(utc(2026, 1, 1)),
        creator="actor",
    )
    event = StatusEvent(
        EventId.new(),
        finalized.version_id,
        "finalized",
        "withdrawn",
        utc(2026, 2, 1),
        utc(2026, 2, 1),
        "actor",
        "basis",
    )

    assert event.target_version_id == finalized.version_id
    assert finalized.content == {"value": "fixed"}
