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
            "0005_increment_5"
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
                == "0005_increment_5"
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
            ).scalar_one() == ("0005_increment_5")
    finally:
        engine.dispose()


def test_increment_4_normalized_schema_constraints_indexes_triggers_and_foreign_keys(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    inspector = inspect(sqlite_store.engine)
    increment_4_tables = {
        "integration_records",
        "integration_versions",
        "integration_material_applicability",
        "integration_authority_records",
        "integration_authority_gaps",
        "uncertainty_classification_records",
        "uncertainty_classification_versions",
        "boundary_snapshot_records",
        "boundary_snapshot_versions",
        "boundary_clause_records",
        "boundary_clause_versions",
        "boundary_determination_records",
        "boundary_determination_versions",
        "boundary_determination_evidence",
        "decision_records",
        "decision_versions",
        "decision_uncertainty_links",
        "decision_authority_records",
        "decision_authority_gaps",
        "bounded_proceed_records",
        "bounded_proceed_versions",
        "bounded_proceed_delegations",
        "bounded_proceed_boundary_clauses",
        "decision_authorization_basis_records",
        "decision_authorization_basis_versions",
        "decision_authorization_delegations",
        "decision_authorization_gaps",
    }
    assert increment_4_tables <= set(inspector.get_table_names())
    assert {
        constraint["name"]
        for constraint in inspector.get_check_constraints("boundary_clause_versions")
    } >= {
        "ck_boundary_clause_effect",
        "ck_boundary_clause_verification",
        "ck_boundary_mechanical_structure",
    }
    assert {
        constraint["name"]
        for constraint in inspector.get_check_constraints("decision_authorization_basis_versions")
    } >= {"ck_decision_authorization_authority", "ck_decision_authorization_source"}
    assert {
        constraint["name"]
        for constraint in inspector.get_check_constraints("bounded_proceed_versions")
    } >= {"ck_bounded_proceed_authority", "ck_bounded_proceed_authority_source"}
    assert {index["name"] for index in inspector.get_indexes("decision_versions")} >= {
        "ix_decision_current_context"
    }
    authorization_foreign_keys = {
        tuple(item["constrained_columns"])
        for item in inspector.get_foreign_keys("decision_authorization_basis_versions")
    }
    assert {
        ("version_id",),
        ("decision_version_id",),
        ("authority_assignment_version_id",),
        ("authority_record_version_id",),
        ("configuration_version_id",),
        ("bounded_proceed_version_id",),
    } <= authorization_foreign_keys
    bounded_proceed_foreign_keys = {
        tuple(item["constrained_columns"])
        for item in inspector.get_foreign_keys("bounded_proceed_versions")
    }
    assert {
        ("version_id",),
        ("decision_version_id",),
        ("unresolved_gap_version_id",),
        ("authority_assignment_version_id",),
        ("authority_record_version_id",),
    } <= bounded_proceed_foreign_keys
    with sqlite_store.engine.connect() as connection:
        triggers = set(
            connection.execute(
                text("SELECT name FROM sqlite_master WHERE type = 'trigger'")
            ).scalars()
        )
    for table in increment_4_tables:
        assert f"prevent_{table}_update" in triggers
        assert f"prevent_{table}_delete" in triggers
    with (
        sqlite_store.engine.begin() as connection,
        pytest.raises(DBAPIError, match="FOREIGN KEY"),
    ):
        connection.execute(
            text(
                """INSERT INTO decision_authorization_basis_versions
                (version_id, basis_id, decision_version_id, decision_authority_identity,
                 authority_assignment_version_id, authority_mechanism,
                 authority_record_version_id, authorized_scope, configuration_id,
                 configuration_version_id, operating_state_coverage_json, decision_type,
                 organizational_unit, authorization_event_id, authorization_actor_id,
                 authorization_effective_at_us, bounded_proceed_version_id)
                VALUES ('missing-version', 'missing-basis', 'missing-decision', 'actor',
                        NULL, 'mechanism', NULL, 'scope', 'missing-configuration',
                        'missing-configuration-version', '[]', 'type', NULL, 'event',
                        'missing-actor', 1, NULL)"""
            )
        )


def test_upgrade_from_increment_3_revision_to_increment_4_head(tmp_path: Path) -> None:
    database_path = (tmp_path / "upgrade-from-increment-3.sqlite3").as_posix()
    database_url = f"sqlite+pysqlite:///{database_path}"
    config = alembic_config(database_url)
    command.upgrade(config, "0003_increment_3")
    engine = create_engine(database_url)
    try:
        assert "integration_records" not in inspect(engine).get_table_names()
        command.upgrade(config, "head")
        assert {
            "integration_versions",
            "boundary_snapshot_versions",
            "decision_versions",
            "decision_authorization_basis_versions",
        } <= set(inspect(engine).get_table_names())
        with engine.connect() as connection:
            assert (
                connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
                == "0005_increment_5"
            )
    finally:
        engine.dispose()


def test_increment_5_normalized_schema_constraints_indexes_triggers_and_foreign_keys(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    inspector = inspect(sqlite_store.engine)
    increment_5_tables = {
        "decision_preauthorized_activation_mechanisms",
        "intervention_records",
        "intervention_versions",
        "obligation_set_records",
        "obligation_set_versions",
        "obligation_records",
        "obligation_versions",
        "completion_result_records",
        "completion_result_versions",
        "completion_result_criteria",
        "completion_result_evidence",
        "completion_acceptor_mechanism_records",
        "completion_acceptor_mechanism_versions",
        "completion_acceptance_records",
        "completion_acceptance_versions",
        "completion_acceptance_delegations",
        "intervention_replacement_records",
        "intervention_replacement_versions",
        "continued_validity_records",
        "continued_validity_versions",
        "prerequisite_evaluation_basis_records",
        "prerequisite_evaluation_basis_versions",
        "prerequisite_evaluation_basis_items",
        "activation_authorization_records",
        "activation_authorization_versions",
        "activation_authorization_delegations",
        "target_activation_events",
        "learning_item_records",
        "learning_item_versions",
        "learning_item_evidence",
    }
    assert increment_5_tables <= set(inspector.get_table_names())
    assert {item["name"] for item in inspector.get_check_constraints("intervention_versions")} >= {
        "ck_intervention_status",
        "ck_intervention_accountability",
    }
    assert {
        item["name"] for item in inspector.get_check_constraints("completion_acceptance_versions")
    } >= {
        "ck_completion_acceptance_outcome",
        "ck_completion_acceptance_status",
        "ck_completion_acceptance_accountability",
    }
    assert {
        item["name"]
        for item in inspector.get_check_constraints("activation_authorization_versions")
    } >= {"ck_activation_authority_path"}
    assert {item["name"] for item in inspector.get_indexes("obligation_versions")} >= {
        "ix_obligation_set_type"
    }
    acceptance_foreign_keys = {
        tuple(item["constrained_columns"])
        for item in inspector.get_foreign_keys("completion_acceptance_versions")
    }
    assert {
        ("version_id",),
        ("obligation_version_id",),
        ("intervention_version_id",),
        ("completion_result_version_id",),
        ("decision_version_id",),
        ("configuration_version_id",),
        ("accountable_actor_id",),
        ("accountable_assignment_version_id",),
        ("accountable_mechanism_version_id",),
    } <= acceptance_foreign_keys
    with sqlite_store.engine.connect() as connection:
        triggers = set(
            connection.execute(
                text("SELECT name FROM sqlite_master WHERE type = 'trigger'")
            ).scalars()
        )
    for table in increment_5_tables:
        assert f"prevent_{table}_update" in triggers
        assert f"prevent_{table}_delete" in triggers
    with (
        sqlite_store.engine.begin() as connection,
        pytest.raises(DBAPIError, match="FOREIGN KEY"),
    ):
        connection.execute(
            text(
                """INSERT INTO completion_result_evidence
                (result_version_id, evidence_version_id)
                VALUES ('missing-result', 'missing-evidence')"""
            )
        )


def test_upgrade_from_increment_4_revision_to_increment_5_head(tmp_path: Path) -> None:
    database_path = (tmp_path / "upgrade-from-increment-4.sqlite3").as_posix()
    database_url = f"sqlite+pysqlite:///{database_path}"
    config = alembic_config(database_url)
    command.upgrade(config, "0004_increment_4")
    engine = create_engine(database_url)
    try:
        assert "intervention_versions" not in inspect(engine).get_table_names()
        command.upgrade(config, "head")
        assert {
            "intervention_versions",
            "completion_acceptor_mechanism_versions",
            "completion_acceptance_versions",
            "prerequisite_evaluation_basis_versions",
            "activation_authorization_versions",
            "learning_item_versions",
        } <= set(inspect(engine).get_table_names())
        with engine.connect() as connection:
            assert (
                connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
                == "0005_increment_5"
            )
    finally:
        engine.dispose()
