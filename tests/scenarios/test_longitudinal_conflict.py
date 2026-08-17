from paim.application import IntegrityApplicationService, StalePrecondition
from paim.integrity import (
    FixedClock,
    RelationshipType,
    SelectionConflict,
    SelectionQuery,
)
from paim.persistence.sqlite import SQLiteIntegrityStore
from tests.helpers import utc, version_command


def test_overlapping_successor_surfaces_conflict_and_blocks_silent_follow_on(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    initial = version_command(idempotency_key="scenario-initial")
    IntegrityApplicationService(sqlite_store, FixedClock(utc(2026, 1, 2))).commit_version(initial)

    competing = version_command(
        record_id=initial.record_id,
        expected_version_id=initial.version_id,
        content={"value": "competing"},
        effective_from=utc(2026, 1, 1),
        precondition_at=utc(2026, 1, 10),
        idempotency_key="scenario-competing",
        relationship_type=RelationshipType.AMENDMENT,
        relationship_reason="overlap intentionally retained for accountable resolution",
    )
    IntegrityApplicationService(sqlite_store, FixedClock(utc(2026, 1, 3))).commit_version(competing)

    current = sqlite_store.select_current(
        SelectionQuery("opaque-family", "opaque-scope", utc(2026, 1, 10))
    )
    assert isinstance(current, SelectionConflict)
    assert {candidate.version_id for candidate in current.candidates} == {
        initial.version_id,
        competing.version_id,
    }

    attempted_silent_winner = version_command(
        record_id=initial.record_id,
        expected_version_id=competing.version_id,
        content={"value": "must remain blocked"},
        effective_from=utc(2026, 1, 10),
        precondition_at=utc(2026, 1, 10),
        idempotency_key="scenario-blocked",
        relationship_type=RelationshipType.SUPERSESSION,
        relationship_reason="cannot select a winner while current is conflicted",
        end_predecessor_status="superseded",
    )
    try:
        IntegrityApplicationService(sqlite_store, FixedClock(utc(2026, 1, 4))).commit_version(
            attempted_silent_winner
        )
    except StalePrecondition as error:
        assert "CONFLICT:" in str(error)
    else:
        raise AssertionError("conflicted current state must block an implicit winner")

    assert sqlite_store.count_rows("record_versions") == 2
