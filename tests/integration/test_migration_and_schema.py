from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import DBAPIError

from paim.application import IntegrityApplicationService
from paim.integrity import FixedClock
from paim.persistence.sqlite import SQLiteIntegrityStore
from tests.helpers import utc, version_command


def alembic_config(database_url: str) -> Config:
    root = Path(__file__).resolve().parents[2]
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    return config


def test_alembic_head_foreign_keys_and_immutability_triggers_exist(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    with sqlite_store.engine.connect() as connection:
        assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == 1
        assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == (
            "0002_increment_2"
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
        "prevent_managed_configurations_update",
        "prevent_governing_configuration_designations_update",
        "prevent_role_assignment_versions_update",
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


def test_increment_2_schema_tables_constraints_indexes_and_upgrade_from_increment_1a(
    tmp_path: Path,
) -> None:
    database_path = (tmp_path / "upgrade-from-increment-1a.sqlite3").as_posix()
    database_url = f"sqlite+pysqlite:///{database_path}"
    config = alembic_config(database_url)
    command.upgrade(config, "0001_increment_1a")
    engine = create_engine(database_url)
    try:
        before = inspect(engine)
        assert "paim_cases" not in before.get_table_names()
        command.upgrade(config, "head")
        inspector = inspect(engine)
        expected_tables = {
            "paim_cases",
            "paim_case_versions",
            "paim_case_links",
            "managed_configurations",
            "managed_configuration_versions",
            "paim_actors",
            "paim_actor_versions",
            "role_assignments",
            "role_assignment_versions",
            "governing_configuration_designations",
            "configuration_determinations",
        }
        assert expected_tables <= set(inspector.get_table_names())
        assert {index["name"] for index in inspector.get_indexes("role_assignment_versions")} >= {
            "ix_role_assignments_resolution"
        }
        assert {
            constraint["name"]
            for constraint in inspector.get_check_constraints("role_assignment_versions")
        } >= {
            "ck_role_target_type",
            "ck_role_case_context",
            "ck_role_delegation_effect",
            "ck_role_delegation_source",
        }
        with engine.connect() as connection:
            assert connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one() == ("0002_increment_2")
    finally:
        engine.dispose()
