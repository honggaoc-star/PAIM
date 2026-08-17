"""Reusable adapter contract; replace ``integrity_store`` to validate another adapter."""

from paim.application import CommitStatusCommand, IntegrityApplicationService
from paim.audit import ActorResolution
from paim.integrity import (
    CommandId,
    FixedClock,
    RecordVersionId,
    RelationshipType,
    SelectionAbsent,
    SelectionFound,
    SelectionQuery,
)
from paim.persistence.ports import IntegrityStore
from tests.helpers import utc, version_command


def test_exact_version_history_dual_time_and_withdrawal_contract(
    integrity_store: IntegrityStore,
) -> None:
    original_command = version_command(
        effective_from=utc(2026, 1, 1),
        precondition_at=utc(2026, 1, 20),
        idempotency_key="original",
    )
    IntegrityApplicationService(integrity_store, FixedClock(utc(2026, 1, 2))).commit_version(
        original_command
    )

    exact_original = integrity_store.get_version(original_command.version_id)
    assert exact_original is not None
    assert exact_original.content == {"value": "one"}

    correction_id = RecordVersionId.new()
    correction_command = version_command(
        record_id=original_command.record_id,
        version_id=correction_id,
        expected_version_id=original_command.version_id,
        content={"value": "corrected"},
        effective_from=utc(2026, 1, 10),
        precondition_at=utc(2026, 1, 20),
        idempotency_key="correction",
        relationship_type=RelationshipType.CORRECTION,
        relationship_reason="repair source error",
        end_predecessor_status="superseded",
    )
    IntegrityApplicationService(integrity_store, FixedClock(utc(2026, 2, 1))).commit_version(
        correction_command
    )

    prior_known = integrity_store.select_current(
        SelectionQuery("opaque-family", "opaque-scope", utc(2026, 1, 20), utc(2026, 1, 20))
    )
    current_knowledge = integrity_store.select_current(
        SelectionQuery("opaque-family", "opaque-scope", utc(2026, 1, 20))
    )
    assert isinstance(prior_known, SelectionFound)
    assert prior_known.candidate.version_id == original_command.version_id
    assert isinstance(current_knowledge, SelectionFound)
    assert current_knowledge.candidate.version_id == correction_id

    history = integrity_store.get_history(original_command.record_id)
    assert {version.version_id for version in history.versions} == {
        original_command.version_id,
        correction_id,
    }
    assert len(history.status_events) == 1
    assert {event.new_status for event in history.status_events} == {"superseded"}
    assert len(history.relationships) == 1
    assert {relationship.relationship_type for relationship in history.relationships} == {
        RelationshipType.CORRECTION
    }
    assert integrity_store.get_version(original_command.version_id) == exact_original

    withdrawal = CommitStatusCommand(
        command_id=CommandId.new(),
        idempotency_scope="test-scope",
        idempotency_key="withdrawal",
        record_id=original_command.record_id,
        target_version_id=correction_id,
        family="opaque-family",
        scope="opaque-scope",
        precondition_at=utc(2026, 2, 20),
        prior_status="finalized",
        new_status="withdrawn",
        effective_at=utc(2026, 2, 15),
        basis="prospective reliance ended",
        principal_id="principal:technical",
        actor_id=None,
        actor_resolution=ActorResolution.UNRESOLVED,
    )
    IntegrityApplicationService(integrity_store, FixedClock(utc(2026, 3, 1))).commit_status(
        withdrawal
    )

    withdrawn_now = integrity_store.select_current(
        SelectionQuery("opaque-family", "opaque-scope", utc(2026, 2, 20))
    )
    before_withdrawal_was_known = integrity_store.select_current(
        SelectionQuery("opaque-family", "opaque-scope", utc(2026, 2, 20), utc(2026, 2, 20))
    )
    assert isinstance(withdrawn_now, SelectionAbsent)
    assert isinstance(before_withdrawal_was_known, SelectionFound)
    assert before_withdrawal_was_known.candidate.version_id == correction_id

    final_history = integrity_store.get_history(original_command.record_id)
    assert len(final_history.status_events) == 2
    withdrawal_events = [
        event for event in final_history.status_events if event.new_status == "withdrawn"
    ]
    assert len(withdrawal_events) == 1
    assert withdrawal_events[0].actor == "unresolved"
    assert integrity_store.get_version(correction_id) is not None
    assert integrity_store.get_version(correction_id).content == {"value": "corrected"}  # type: ignore[union-attr]
