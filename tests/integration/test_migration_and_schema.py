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
            "0003_increment_3"
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


def test_increment_3_normalized_schema_constraints_indexes_and_triggers(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    inspector = inspect(sqlite_store.engine)
    increment_3_tables = {
        "evidence_records",
        "evidence_versions",
        "authority_records",
        "authority_record_versions",
        "authority_gaps",
        "authority_gap_versions",
        "exact_evidence_links",
        "affected_use_references",
        "evidence_applicability_records",
        "evidence_applicability_versions",
        "analytical_inputs",
        "analytical_input_versions",
        "candidate_dispositions",
        "candidate_disposition_versions",
        "lane_fitness_records",
        "lane_fitness_versions",
        "material_evidence_basis",
        "input_acceptance_records",
        "input_acceptance_versions",
    }
    assert increment_3_tables <= set(inspector.get_table_names())
    assert {
        constraint["name"]
        for constraint in inspector.get_check_constraints("evidence_applicability_versions")
    } >= {"ck_applicability_outcome", "ck_applicability_target_type"}
    assert {
        constraint["name"]
        for constraint in inspector.get_check_constraints("analytical_input_versions")
    } >= {"ck_analytical_input_version_lane"}
    assert {
        index["name"] for index in inspector.get_indexes("evidence_applicability_versions")
    } >= {"ix_applicability_exact_context"}
    applicability_foreign_keys = {
        tuple(foreign_key["constrained_columns"])
        for foreign_key in inspector.get_foreign_keys("evidence_applicability_versions")
    }
    assert {
        ("version_id",),
        ("evidence_version_id",),
        ("target_version_id",),
        ("assessor_actor_id",),
        ("accountable_assignment_version_id",),
    } <= applicability_foreign_keys
    with sqlite_store.engine.connect() as connection:
        triggers = set(
            connection.execute(
                text("SELECT name FROM sqlite_master WHERE type = 'trigger'")
            ).scalars()
        )
    for table in increment_3_tables:
        assert f"prevent_{table}_update" in triggers
        assert f"prevent_{table}_delete" in triggers
    with (
        sqlite_store.engine.begin() as connection,
        pytest.raises(DBAPIError, match="FOREIGN KEY"),
    ):
        connection.execute(
            text(
                """INSERT INTO exact_evidence_links
                (source_version_id, evidence_version_id, link_role)
                VALUES (:source, :evidence, 'invalid-fk-oracle')"""
            ),
            {
                "source": "00000000-0000-7000-8000-000000000101",
                "evidence": "00000000-0000-7000-8000-000000000102",
            },
        )


def test_upgrade_from_increment_2_revision_to_increment_3_head(tmp_path: Path) -> None:
    database_path = (tmp_path / "upgrade-from-increment-2.sqlite3").as_posix()
    database_url = f"sqlite+pysqlite:///{database_path}"
    config = alembic_config(database_url)
    command.upgrade(config, "0002_increment_2")
    engine = create_engine(database_url)
    try:
        assert "evidence_records" not in inspect(engine).get_table_names()
        command.upgrade(config, "head")
        inspector = inspect(engine)
        assert {
            "evidence_records",
            "evidence_applicability_versions",
            "analytical_input_versions",
            "input_acceptance_versions",
        } <= set(inspector.get_table_names())
        with engine.connect() as connection:
            assert (
                connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
                == "0003_increment_3"
            )
    finally:
        engine.dispose()


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
            ).scalar_one() == ("0003_increment_3")
    finally:
        engine.dispose()
