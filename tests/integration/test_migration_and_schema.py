import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from paim.application import IntegrityApplicationService
from paim.integrity import FixedClock
from paim.persistence.sqlite import SQLiteIntegrityStore
from tests.helpers import utc, version_command


def test_alembic_head_foreign_keys_and_immutability_triggers_exist(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    with sqlite_store.engine.connect() as connection:
        assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == 1
        assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == (
            "0001_increment_1a"
        )
        trigger_names = set(
            connection.execute(
                text("SELECT name FROM sqlite_master WHERE type = 'trigger'")
            ).scalars()
        )
    assert {
        "prevent_finalized_version_update",
        "prevent_record_version_delete",
        "prevent_status_event_update",
        "prevent_relationship_update",
        "prevent_idempotency_update",
        "prevent_audit_update",
    } <= trigger_names


def test_database_rejects_finalized_content_update_and_foreign_key_violation(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    command = version_command()
    IntegrityApplicationService(sqlite_store, FixedClock(utc(2026, 1, 2))).commit_version(command)

    with (
        sqlite_store.engine.begin() as connection,
        pytest.raises(DBAPIError, match="finalized content is immutable"),
    ):
        connection.execute(
            text("UPDATE record_versions SET content_json = '{}' WHERE version_id = :version_id"),
            {"version_id": str(command.version_id)},
        )

    with (
        sqlite_store.engine.begin() as connection,
        pytest.raises(DBAPIError, match="FOREIGN KEY"),
    ):
        connection.execute(
            text(
                """INSERT INTO status_events
                (event_id, target_version_id, prior_status, new_status,
                 recorded_at_us, effective_at_us, actor, basis)
                VALUES (:event_id, :target, 'a', 'b', 1, 1, 'actor', 'basis')"""
            ),
            {"event_id": "00000000-0000-7000-8000-000000000001", "target": "missing"},
        )
