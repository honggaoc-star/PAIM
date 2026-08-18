from dataclasses import replace

import pytest

from paim.application import (
    IdempotencyKeyReuseConflict,
    IntegrityApplicationService,
    StalePrecondition,
)
from paim.audit import ActorResolution
from paim.integrity import AuditId, FixedClock
from paim.persistence import ports
from paim.persistence.sqlite import SQLiteIntegrityStore
from tests.helpers import utc, version_command


def test_accepted_bundle_commits_version_idempotency_and_distinct_actor_audit(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    command = version_command(principal_id="principal:p1", actor_id="actor:a1")
    outcome = IntegrityApplicationService(sqlite_store, FixedClock(utc(2026, 1, 2))).commit_version(
        command
    )

    assert sqlite_store.count_rows("records") == 1
    assert sqlite_store.count_rows("record_versions") == 1
    assert sqlite_store.count_rows("idempotency_facts") == 1
    assert sqlite_store.count_rows("audit_facts") == 1
    audit = sqlite_store.get_audit(AuditId.parse(outcome.audit_id))
    assert audit is not None
    assert audit.principal_id == "principal:p1"
    assert audit.actor_id == "actor:a1"
    assert audit.actor_resolution is ActorResolution.PROVIDED
    assert audit.principal_id != audit.actor_id
    assert audit.request_digest == command.digest()


@pytest.mark.parametrize(
    "failure_stage", ["after_authoritative_facts", "after_audit", "before_commit"]
)
def test_injected_failure_rolls_back_entire_bundle_and_orphan_audit(
    sqlite_store: SQLiteIntegrityStore, failure_stage: str
) -> None:
    command = version_command(idempotency_key=f"fail-{failure_stage}")

    def fail(stage: str) -> None:
        if stage == failure_stage:
            raise RuntimeError("injected failure")

    with pytest.raises(RuntimeError, match="injected failure"):
        IntegrityApplicationService(sqlite_store, FixedClock(utc(2026, 1, 2))).commit_version(
            command, failure_injector=fail
        )

    for table in ("records", "record_versions", "audit_facts", "idempotency_facts"):
        assert sqlite_store.count_rows(table) == 0


def test_stale_expected_absence_creates_no_partial_write(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    initial = version_command(idempotency_key="first")
    service = IntegrityApplicationService(sqlite_store, FixedClock(utc(2026, 1, 2)))
    service.commit_version(initial)
    stale = version_command(
        record_id=initial.record_id,
        idempotency_key="stale",
        content={"value": "must not commit"},
    )

    with pytest.raises(StalePrecondition):
        service.commit_version(stale)

    assert sqlite_store.count_rows("record_versions") == 1
    assert sqlite_store.count_rows("audit_facts") == 1
    assert sqlite_store.count_rows("idempotency_facts") == 1


def test_same_key_same_digest_replays_original_without_duplicate_rows(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    command = version_command(idempotency_key="replay")
    service = IntegrityApplicationService(sqlite_store, FixedClock(utc(2026, 1, 2)))

    original = service.commit_version(command)
    replay = service.commit_version(command)

    assert replay == original
    assert sqlite_store.count_rows("record_versions") == 1
    assert sqlite_store.count_rows("audit_facts") == 1
    assert sqlite_store.count_rows("idempotency_facts") == 1


def test_same_key_different_digest_is_explicit_conflict_without_write(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    command = version_command(idempotency_key="reuse")
    service = IntegrityApplicationService(sqlite_store, FixedClock(utc(2026, 1, 2)))
    original = service.commit_version(command)
    mismatched = replace(command, content={"value": "different"})

    with pytest.raises(IdempotencyKeyReuseConflict, match="IDEMPOTENCY KEY REUSE CONFLICT"):
        service.commit_version(mismatched)

    assert sqlite_store.get_version(command.version_id) is not None
    assert sqlite_store.count_rows("record_versions") == 1
    assert sqlite_store.count_rows("audit_facts") == 1
    assert sqlite_store.get_audit(AuditId.parse(original.audit_id)) is not None


def test_writer_contention_is_explicit_and_not_rebased(sqlite_store: SQLiteIntegrityStore) -> None:
    command = version_command(idempotency_key="contention")
    with sqlite_store.engine.connect() as blocker:
        blocker.exec_driver_sql("BEGIN IMMEDIATE")
        with pytest.raises(ports.WriterContention, match="WRITER CONTENTION"):
            IntegrityApplicationService(sqlite_store, FixedClock(utc(2026, 1, 2))).commit_version(
                command
            )
        blocker.rollback()

    assert sqlite_store.count_rows("record_versions") == 0


def test_nested_independent_semantic_commit_is_prohibited(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    with (
        sqlite_store.semantic_transaction(),
        pytest.raises(ports.NestedSemanticCommit),
        sqlite_store.semantic_transaction(),
    ):
        pass
