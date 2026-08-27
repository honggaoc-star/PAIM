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


def test_gate8_slice_e_upgrades_exact_slice_d_head_without_backfill(
    tmp_path: Path,
) -> None:
    database_url = f"sqlite+pysqlite:///{(tmp_path / 'gate8-from-0013.sqlite3').as_posix()}"
    config = alembic_config(database_url)
    command.upgrade(config, "0013_gate8_integration_decision_basis")
    engine = create_engine(database_url)
    legacy_tables = (
        "prospective_decision_versions",
        "assessment_reliance_versions",
        "reassessment_versions",
    )
    with engine.connect() as connection:
        before = {
            table: connection.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one()
            for table in legacy_tables
        }
    command.upgrade(config, "head")
    inspector = inspect(engine)
    expected = {
        "planned_review_point_records",
        "planned_review_point_versions",
        "required_review_constraint_records",
        "required_review_constraint_versions",
        "review_attention_event_records",
        "review_attention_event_versions",
        "review_episode_records",
        "review_episode_versions",
        "review_episode_result_links",
    }
    assert expected <= set(inspector.get_table_names())
    assert {index["name"] for index in inspector.get_indexes("planned_review_point_versions")} >= {
        "ix_planned_review_point_selection"
    }
    assert {
        index["name"] for index in inspector.get_indexes("required_review_constraint_versions")
    } >= {"ix_required_review_constraint_selection"}
    assert {index["name"] for index in inspector.get_indexes("review_episode_versions")} >= {
        "ix_review_episode_selection"
    }
    assert {
        constraint["name"]
        for constraint in inspector.get_check_constraints("required_review_constraint_versions")
    } >= {
        "ck_required_review_state",
        "ck_required_review_operator",
        "ck_required_review_window",
    }
    assert {
        constraint["name"]
        for constraint in inspector.get_check_constraints("review_episode_versions")
    } >= {"ck_review_episode_status", "ck_review_episode_decision_path"}
    assert {
        foreign_key["referred_table"]
        for foreign_key in inspector.get_foreign_keys("review_episode_versions")
    } >= {
        "record_versions",
        "prospective_decision_versions",
        "prospective_integration_versions",
        "assessment_reliance_versions",
        "responsibility_assignment_versions",
    }
    with engine.connect() as connection:
        assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == (
            "0018_issue167_case_identity"
        )
        assert before == {
            table: connection.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one()
            for table in legacy_tables
        }
        triggers = {
            value
            for value in connection.execute(
                text("SELECT name FROM sqlite_master WHERE type='trigger'")
            ).scalars()
        }
        for table in expected:
            assert f"prevent_{table}_update" in triggers
            assert f"prevent_{table}_delete" in triggers
    engine.dispose()


def test_gate8_slice_d_upgrades_exact_slice_c_head_without_backfill(
    tmp_path: Path,
) -> None:
    database_url = f"sqlite+pysqlite:///{(tmp_path / 'gate8-from-0012.sqlite3').as_posix()}"
    config = alembic_config(database_url)
    command.upgrade(config, "0012_gate8_assessment_review")
    engine = create_engine(database_url)
    legacy_tables = (
        "integration_versions",
        "decision_versions",
        "assessment_reliance_versions",
    )
    with engine.connect() as connection:
        before = {
            table: connection.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one()
            for table in legacy_tables
        }
    command.upgrade(config, "head")
    inspector = inspect(engine)
    expected = {
        "prospective_integration_records",
        "prospective_integration_versions",
        "prospective_decision_records",
        "prospective_decision_versions",
        "prospective_decision_authorization_records",
        "prospective_decision_authorization_versions",
        "prospective_decision_confirmation_records",
        "prospective_decision_confirmation_versions",
    }
    assert expected <= set(inspector.get_table_names())
    assert {
        index["name"] for index in inspector.get_indexes("prospective_integration_versions")
    } >= {"ix_prospective_integration_selection"}
    assert {index["name"] for index in inspector.get_indexes("prospective_decision_versions")} >= {
        "ix_prospective_decision_selection"
    }
    with engine.connect() as connection:
        assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == (
            "0018_issue167_case_identity"
        )
        assert before == {
            table: connection.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one()
            for table in legacy_tables
        }
        triggers = {
            value
            for value in connection.execute(
                text("SELECT name FROM sqlite_master WHERE type='trigger'")
            ).scalars()
        }
        for table in expected:
            assert f"prevent_{table}_update" in triggers
            assert f"prevent_{table}_delete" in triggers
    assert {
        foreign_key["referred_table"]
        for foreign_key in inspector.get_foreign_keys("prospective_decision_versions")
    } >= {
        "record_versions",
        "prospective_integration_versions",
        "assessment_reliance_versions",
        "responsibility_assignment_versions",
    }
    engine.dispose()


def test_alembic_head_foreign_keys_and_immutability_triggers_exist(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    with sqlite_store.engine.connect() as connection:
        assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == 1
        assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == (
            "0018_issue167_case_identity"
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


def test_gate8_slice_a_schema_is_additive_append_only_and_not_backfilled(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    inspector = inspect(sqlite_store.engine)
    common = {
        "semantic_contracts",
        "semantic_contract_families",
        "semantic_contract_adapters",
        "semantic_contract_successors",
        "exact_context_sets",
        "exact_context_members",
        "record_version_semantics",
        "status_event_semantics",
        "version_relationship_semantics",
        "semantic_consumer_cutover_versions",
    }
    responsibility_work = {
        "practical_role_catalog",
        "responsibility_records",
        "responsibility_versions",
        "responsibility_practical_roles",
        "assignment_basis_records",
        "assignment_basis_versions",
        "responsibility_assignment_records",
        "responsibility_assignment_versions",
        "case_work_records",
        "case_work_versions",
        "case_work_result_links",
    }
    assert common | responsibility_work <= set(inspector.get_table_names())
    with sqlite_store.engine.connect() as connection:
        triggers = set(
            connection.execute(
                text("SELECT name FROM sqlite_master WHERE type = 'trigger'")
            ).scalars()
        )
        assert (
            connection.execute(text("SELECT count(*) FROM record_version_semantics")).scalar_one()
            == 0
        )
        roles = set(
            connection.execute(text("SELECT role_code FROM practical_role_catalog")).scalars()
        )
    assert roles == {"CASE_COORDINATOR", "ASSESSOR", "REVIEWER"}
    assert "practical_role" not in {
        column["name"] for column in inspector.get_columns("responsibility_versions")
    }
    assert {
        column["name"] for column in inspector.get_columns("responsibility_practical_roles")
    } == {"responsibility_version_id", "role_code"}
    assert {
        "owning_case_id",
        "context_digest",
        "allowed_signature_digests_json",
        "max_active_assignments",
        "state",
        "effective_from_us",
        "effective_to_us",
        "recorded_at_us",
        "predecessor_version_id",
    } <= {column["name"] for column in inspector.get_columns("assignment_basis_versions")}
    assert {
        constraint["name"]
        for constraint in inspector.get_check_constraints("assignment_basis_versions")
    } >= {"ck_assignment_basis_state", "ck_assignment_basis_positive_limit"}
    for table in common | responsibility_work:
        assert f"prevent_{table}_update" in triggers
        assert f"prevent_{table}_delete" in triggers


def test_gate8_slice_a_upgrades_from_increment_8_without_legacy_backfill(
    tmp_path: Path,
) -> None:
    database_url = f"sqlite+pysqlite:///{(tmp_path / 'gate8-from-0008.sqlite3').as_posix()}"
    config = alembic_config(database_url)
    command.upgrade(config, "0008_increment_8")
    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO records (record_id, family, scope) "
                "VALUES ('legacy-record', 'legacy-family', 'legacy-scope')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO record_versions "
                "(version_id, record_id, content_json, finalized, recorded_at_us, "
                " effective_from_us, effective_to_us, creator) "
                "VALUES ('legacy-version', 'legacy-record', :content, "
                "1, 1, 1, NULL, 'legacy')"
            ),
            {"content": '{"legacy":true}'},
        )
    command.upgrade(config, "head")
    with engine.connect() as connection:
        assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == (
            "0018_issue167_case_identity"
        )
        assert connection.execute(
            text("SELECT content_json FROM record_versions")
        ).scalar_one() == ('{"legacy":true}')
        assert (
            connection.execute(text("SELECT count(*) FROM record_version_semantics")).scalar_one()
            == 0
        )
    engine.dispose()


def test_gate8_responsibility_work_upgrades_from_common_semantics_revision(
    tmp_path: Path,
) -> None:
    database_url = f"sqlite+pysqlite:///{(tmp_path / 'gate8-from-0009.sqlite3').as_posix()}"
    config = alembic_config(database_url)
    command.upgrade(config, "0009_gate8_common_semantics")
    command.upgrade(config, "head")
    engine = create_engine(database_url)
    with engine.connect() as connection:
        assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == (
            "0018_issue167_case_identity"
        )
        assert set(
            connection.execute(text("SELECT role_code FROM practical_role_catalog")).scalars()
        ) == {"CASE_COORDINATOR", "ASSESSOR", "REVIEWER"}
    engine.dispose()


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
                == "0018_issue167_case_identity"
            )
    finally:
        engine.dispose()


def test_gate8_case_continuity_schema_and_upgrade_from_slice_a(tmp_path: Path) -> None:
    database_path = (tmp_path / "upgrade-from-slice-a.sqlite3").as_posix()
    database_url = f"sqlite+pysqlite:///{database_path}"
    config = alembic_config(database_url)
    command.upgrade(config, "0010_gate8_responsibility_work")
    engine = create_engine(database_url)
    try:
        assert "case_continuity_status_versions" not in inspect(engine).get_table_names()
        command.upgrade(config, "head")
        inspector = inspect(engine)
        expected = {
            "case_continuity_status_records",
            "case_continuity_status_versions",
            "case_continuity_determination_records",
            "case_continuity_determination_versions",
            "case_continuity_relationships",
            "configuration_continuity_links",
        }
        assert expected <= set(inspector.get_table_names())
        assert {
            item["name"]
            for item in inspector.get_check_constraints("case_continuity_status_versions")
        } >= {
            "ck_case_continuity_status",
            "ck_case_continuity_transition_basis",
            "ck_case_continuity_successor",
        }
        assert {
            item["name"] for item in inspector.get_indexes("case_continuity_status_versions")
        } >= {"ix_case_continuity_status_selection"}
        with engine.connect() as connection:
            assert (
                connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
                == "0018_issue167_case_identity"
            )
            triggers = set(
                connection.execute(
                    text("SELECT name FROM sqlite_master WHERE type = 'trigger'")
                ).scalars()
            )
            assert (
                connection.execute(
                    text("SELECT COUNT(*) FROM case_continuity_status_versions")
                ).scalar_one()
                == 0
            )
            assert (
                connection.execute(
                    text("SELECT COUNT(*) FROM case_continuity_determination_versions")
                ).scalar_one()
                == 0
            )
        for table_name in expected:
            assert f"prevent_{table_name}_update" in triggers
            assert f"prevent_{table_name}_delete" in triggers
    finally:
        engine.dispose()


def test_gate8_assessment_review_upgrades_exact_slice_b_head_without_backfill(
    tmp_path: Path,
) -> None:
    database_url = f"sqlite+pysqlite:///{(tmp_path / 'gate8-from-0011.sqlite3').as_posix()}"
    config = alembic_config(database_url)
    command.upgrade(config, "0011_gate8_case_continuity")
    engine = create_engine(database_url)
    with engine.connect() as connection:
        legacy_counts = {
            table: connection.execute(text(f"SELECT count(*) FROM {table}")).scalar_one()
            for table in ("records", "record_versions", "analytical_input_versions")
        }
    command.upgrade(config, "head")
    slice_c_tables = {
        "assessment_candidate_records",
        "assessment_candidate_versions",
        "assessment_readiness_records",
        "assessment_readiness_versions",
        "assessment_adequacy_records",
        "assessment_adequacy_versions",
        "assessment_reliance_records",
        "assessment_reliance_versions",
    }
    inspector = inspect(engine)
    assert slice_c_tables <= set(inspector.get_table_names())
    with engine.connect() as connection:
        assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == (
            "0018_issue167_case_identity"
        )
        assert legacy_counts == {
            table: connection.execute(text(f"SELECT count(*) FROM {table}")).scalar_one()
            for table in legacy_counts
        }
        assert all(
            connection.execute(text(f"SELECT count(*) FROM {table}")).scalar_one() == 0
            for table in slice_c_tables
        )
        triggers = set(
            connection.execute(
                text("SELECT name FROM sqlite_master WHERE type = 'trigger'")
            ).scalars()
        )
    assert all(
        f"prevent_{table}_{action}" in triggers
        for table in slice_c_tables
        for action in ("update", "delete")
    )
    assert {index["name"] for index in inspector.get_indexes("assessment_reliance_versions")} >= {
        "ix_assessment_reliance_selection"
    }
    assert {
        tuple(foreign_key["constrained_columns"])
        for foreign_key in inspector.get_foreign_keys("assessment_reliance_versions")
    } >= {
        ("assessment_version_id",),
        ("readiness_version_id",),
        ("adequacy_version_id",),
        ("responsibility_version_id",),
        ("assignment_version_id",),
    }
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
            ).scalar_one() == ("0018_issue167_case_identity")
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
                == "0018_issue167_case_identity"
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
        "continued_validity_mechanism_records",
        "continued_validity_mechanism_versions",
        "continued_validity_records",
        "continued_validity_versions",
        "continued_validity_delegations",
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
    assert {
        item["name"] for item in inspector.get_check_constraints("continued_validity_versions")
    } >= {"ck_continued_validity_accountability"}
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
    continued_validity_foreign_keys = {
        tuple(item["constrained_columns"])
        for item in inspector.get_foreign_keys("continued_validity_versions")
    }
    assert {
        ("version_id",),
        ("successor_obligation_version_id",),
        ("prior_completion_result_version_id",),
        ("prior_acceptance_version_id",),
        ("accountable_actor_id",),
        ("accountable_assignment_version_id",),
        ("accountable_mechanism_version_id",),
    } <= continued_validity_foreign_keys
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
                == "0018_issue167_case_identity"
            )
    finally:
        engine.dispose()


def test_increment_6_normalized_schema_constraints_indexes_triggers_and_foreign_keys(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    inspector = inspect(sqlite_store.engine)
    increment_6_tables = {
        "reassessment_mechanism_records",
        "reassessment_mechanism_versions",
        "trigger_records",
        "trigger_versions",
        "trigger_determination_records",
        "trigger_determination_versions",
        "reassessment_records",
        "reassessment_versions",
        "trigger_membership_records",
        "trigger_membership_versions",
        "trigger_set_members",
        "reassessment_determination_records",
        "reassessment_determination_versions",
        "reassessment_determination_triggers",
        "reassessment_determination_reassessments",
        "interim_disposition_records",
        "interim_disposition_versions",
        "decision_confirmation_records",
        "decision_confirmation_versions",
        "reassessment_completion_outcomes",
    }
    assert increment_6_tables <= set(inspector.get_table_names())
    assert {
        item["name"] for item in inspector.get_check_constraints("trigger_determination_versions")
    } >= {
        "ck_trigger_determination_outcome",
        "ck_trigger_determination_accountability",
    }
    assert {item["name"] for item in inspector.get_check_constraints("reassessment_versions")} >= {
        "ck_reassessment_status",
        "ck_reassessment_owner_accountability",
    }
    assert {
        item["name"] for item in inspector.get_check_constraints("reassessment_completion_outcomes")
    } >= {"ck_reassessment_exactly_one_completion"}
    assert {item["name"] for item in inspector.get_indexes("trigger_versions")} >= {
        "ix_trigger_case_source_question"
    }
    assert {item["name"] for item in inspector.get_indexes("reassessment_versions")} >= {
        "ix_reassessment_case_context"
    }
    assert {item["name"] for item in inspector.get_indexes("interim_disposition_versions")} >= {
        "ix_interim_disposition_context_time"
    }
    membership_foreign_keys = {
        tuple(item["constrained_columns"])
        for item in inspector.get_foreign_keys("trigger_membership_versions")
    }
    assert {
        ("version_id",),
        ("membership_id",),
        ("trigger_version_id",),
        ("reassessment_version_id",),
    } <= membership_foreign_keys
    disposition_foreign_keys = {
        tuple(item["constrained_columns"])
        for item in inspector.get_foreign_keys("interim_disposition_versions")
    }
    assert {
        ("version_id",),
        ("reassessment_version_id",),
        ("decision_version_id",),
        ("configuration_version_id",),
        ("boundary_snapshot_version_id",),
        ("authority_basis_version_id",),
        ("authority_actor_id",),
    } <= disposition_foreign_keys
    with sqlite_store.engine.connect() as connection:
        triggers = set(
            connection.execute(
                text("SELECT name FROM sqlite_master WHERE type = 'trigger'")
            ).scalars()
        )
    for table in increment_6_tables:
        assert f"prevent_{table}_update" in triggers
        assert f"prevent_{table}_delete" in triggers
    with (
        sqlite_store.engine.begin() as connection,
        pytest.raises(DBAPIError, match="FOREIGN KEY"),
    ):
        connection.execute(
            text(
                """INSERT INTO trigger_set_members
                (reassessment_version_id, ordinal, trigger_version_id, membership_version_id)
                VALUES ('missing-reassessment', 0, 'missing-trigger', 'missing-membership')"""
            )
        )


def test_upgrade_from_increment_5_revision_to_increment_6_head(tmp_path: Path) -> None:
    database_path = (tmp_path / "upgrade-from-increment-5.sqlite3").as_posix()
    database_url = f"sqlite+pysqlite:///{database_path}"
    config = alembic_config(database_url)
    command.upgrade(config, "0005_increment_5")
    engine = create_engine(database_url)
    try:
        before = inspect(engine)
        assert "trigger_versions" not in before.get_table_names()
        assert "reassessment_versions" not in before.get_table_names()
        command.upgrade(config, "head")
        assert {
            "trigger_versions",
            "trigger_determination_versions",
            "reassessment_versions",
            "trigger_membership_versions",
            "interim_disposition_versions",
            "decision_confirmation_versions",
            "reassessment_completion_outcomes",
        } <= set(inspect(engine).get_table_names())
        with engine.connect() as connection:
            assert connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one() == ("0018_issue167_case_identity")
    finally:
        engine.dispose()


def test_increment_7_schema_constraints_indexes_triggers_and_no_concern_row_table(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    inspector = inspect(sqlite_store.engine)
    increment_7_tables = {
        "shared_dependency_records",
        "shared_dependency_versions",
        "dependency_candidate_set_records",
        "dependency_candidate_set_versions",
        "dependency_candidate_set_members",
        "shared_dependency_mechanism_records",
        "shared_dependency_mechanism_versions",
        "shared_dependency_equivalence_records",
        "shared_dependency_equivalence_versions",
        "shared_dependency_equivalence_delegations",
        "register_output_manifests",
        "register_notification_intents",
    }
    table_names = set(inspector.get_table_names())
    assert increment_7_tables <= table_names
    assert "management_register_concern_rows" not in table_names
    assert "observation_records" not in table_names
    assert "portfolio_scores" not in table_names
    role_checks = {
        item["name"]: item["sqltext"]
        for item in inspector.get_check_constraints("role_assignment_versions")
    }
    assert "dependency_candidate_set" in role_checks["ck_role_target_type"]
    assert "shared_dependency" in role_checks["ck_role_target_type"]
    assert {item["name"] for item in inspector.get_indexes("dependency_candidate_set_members")} >= {
        "ix_candidate_member_source"
    }
    assert {
        item["name"] for item in inspector.get_indexes("shared_dependency_equivalence_versions")
    } >= {"ix_equivalence_selection"}
    with sqlite_store.engine.connect() as connection:
        triggers = set(
            connection.execute(
                text("SELECT name FROM sqlite_master WHERE type = 'trigger'")
            ).scalars()
        )
    for table in increment_7_tables:
        assert f"prevent_{table}_update" in triggers
        assert f"prevent_{table}_delete" in triggers


def test_upgrade_from_increment_6_revision_to_increment_7_head(tmp_path: Path) -> None:
    database_path = (tmp_path / "upgrade-from-increment-6.sqlite3").as_posix()
    database_url = f"sqlite+pysqlite:///{database_path}"
    config = alembic_config(database_url)
    command.upgrade(config, "0006_increment_6")
    engine = create_engine(database_url)
    try:
        assert "shared_dependency_versions" not in inspect(engine).get_table_names()
        command.upgrade(config, "head")
        inspector = inspect(engine)
        assert {
            "shared_dependency_versions",
            "dependency_candidate_set_members",
            "shared_dependency_equivalence_versions",
            "register_output_manifests",
            "register_notification_intents",
        } <= set(inspector.get_table_names())
        with engine.connect() as connection:
            assert (
                connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
                == "0018_issue167_case_identity"
            )
    finally:
        engine.dispose()


def test_increment_7_upgrade_preserves_existing_role_assignments(tmp_path: Path) -> None:
    from paim.domain import RoleTargetType
    from tests.integration.test_increment_2_foundation import add_actor, add_case, add_role

    database_path = (tmp_path / "upgrade-role-data-from-increment-6.sqlite3").as_posix()
    database_url = f"sqlite+pysqlite:///{database_path}"
    config = alembic_config(database_url)
    command.upgrade(config, "0006_increment_6")
    store = SQLiteIntegrityStore(database_url)
    try:
        case_id, _ = add_case(store, "increment-7-upgrade")
        actor_id, _ = add_actor(store, "increment-7-upgrade")
        _, assignment_version_id = add_role(
            store,
            "increment-7-upgrade",
            actor_id,
            role="Case Owner",
            target_type=RoleTargetType.CASE,
            target_id=str(case_id),
            case_context_id=case_id,
            accountable=True,
        )
    finally:
        store.dispose()
    command.upgrade(config, "head")
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            row = connection.execute(
                text(
                    "SELECT target_type, target_id FROM role_assignment_versions "
                    "WHERE version_id=:version_id"
                ),
                {"version_id": str(assignment_version_id)},
            ).one()
            assert row == ("case", str(case_id))
    finally:
        engine.dispose()


def test_increment_8_operational_schema_constraints_indexes_triggers_and_foreign_keys(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    inspector = inspect(sqlite_store.engine)
    tables = {
        "operational_principals",
        "operational_principal_versions",
        "software_access_grants",
        "operational_audit_facts",
        "adapter_intakes",
        "notification_delivery_events",
        "operational_register_rebuild_bases",
    }
    assert tables <= set(inspector.get_table_names())
    assert "observation_records" not in inspector.get_table_names()
    principal_checks = {
        item["name"] for item in inspector.get_check_constraints("operational_principal_versions")
    }
    assert {
        "ck_operational_principal_status",
        "ck_operational_principal_sequence",
        "ck_operational_credential_iterations",
    } <= principal_checks
    grant_checks = {
        item["name"] for item in inspector.get_check_constraints("software_access_grants")
    }
    assert {
        "ck_software_access_permission",
        "ck_software_access_scope_type",
        "ck_software_access_scope_identity",
        "ck_software_access_effect",
    } <= grant_checks
    assert {item["name"] for item in inspector.get_indexes("adapter_intakes")} >= {
        "ix_adapter_replay",
        "ix_adapter_source_version",
    }
    assert {item["name"] for item in inspector.get_indexes("notification_delivery_events")} >= {
        "ix_delivery_intent_status",
        "uq_delivery_one_success_per_intent",
    }
    assert {
        item["name"] for item in inspector.get_indexes("operational_register_rebuild_bases")
    } >= {"ix_operational_rebuild_checksum"}
    assert {item["name"] for item in inspector.get_indexes("operational_audit_facts")} >= {
        "ix_operational_audit_time_category"
    }
    principal_foreign_keys = {
        (item["referred_table"], tuple(item["referred_columns"]))
        for item in inspector.get_foreign_keys("operational_principal_versions")
    }
    assert ("paim_actors", ("actor_id",)) in principal_foreign_keys
    delivery_foreign_keys = {
        item["referred_table"]
        for item in inspector.get_foreign_keys("notification_delivery_events")
    }
    assert "register_notification_intents" in delivery_foreign_keys
    with sqlite_store.engine.connect() as connection:
        triggers = set(
            connection.execute(
                text("SELECT name FROM sqlite_master WHERE type = 'trigger'")
            ).scalars()
        )
    for table in tables:
        assert f"prevent_{table}_update" in triggers
        assert f"prevent_{table}_delete" in triggers


def test_upgrade_from_increment_7_to_increment_8_preserves_history(tmp_path: Path) -> None:
    database_path = (tmp_path / "upgrade-from-increment-7.sqlite3").as_posix()
    database_url = f"sqlite+pysqlite:///{database_path}"
    config = alembic_config(database_url)
    command.upgrade(config, "0007_increment_7")
    store = SQLiteIntegrityStore(database_url)
    try:
        outcome = IntegrityApplicationService(store, FixedClock(utc(2026, 8, 19))).commit_version(
            version_command(idempotency_key="increment-8-upgrade-preserved")
        )
        preserved_version_id = outcome.version_ids[0]
        assert store.get_version(preserved_version_id) is not None
    finally:
        store.dispose()
    engine = create_engine(database_url)
    try:
        assert "operational_principals" not in inspect(engine).get_table_names()
        command.upgrade(config, "head")
        assert {
            "operational_principals",
            "adapter_intakes",
            "operational_audit_facts",
            "operational_register_rebuild_bases",
        } <= set(inspect(engine).get_table_names())
        with engine.connect() as connection:
            assert connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one() == ("0018_issue167_case_identity")
            assert (
                connection.execute(
                    text("SELECT COUNT(*) FROM record_versions WHERE version_id=:version_id"),
                    {"version_id": str(preserved_version_id)},
                ).scalar_one()
                == 1
            )
    finally:
        engine.dispose()


def test_gate8_slice_f_schema_and_exact_0014_upgrade(tmp_path: Path) -> None:
    database_path = (tmp_path / "upgrade-from-slice-e.sqlite3").as_posix()
    database_url = f"sqlite+pysqlite:///{database_path}"
    config = alembic_config(database_url)
    command.upgrade(config, "0014_gate8_continuing_review")
    engine = create_engine(database_url)
    try:
        assert "quantitative_claim_versions" not in inspect(engine).get_table_names()
        command.upgrade(config, "head")
        inspector = inspect(engine)
        tables = {
            "quantitative_claim_records",
            "quantitative_claim_versions",
            "quantitative_claim_basis_links",
            "quantitative_comparability_records",
            "quantitative_comparability_versions",
        }
        assert tables <= set(inspector.get_table_names())
        assert {
            "ck_quantitative_claim_lane",
            "ck_quantitative_claim_type",
            "ck_quantitative_quantity_kind",
            "ck_quantitative_representation",
            "ck_quantitative_value_shape",
            "ck_quantitative_currency",
            "ck_quantitative_period",
            "ck_quantitative_threshold_authority",
        } <= {
            item["name"] for item in inspector.get_check_constraints("quantitative_claim_versions")
        }
        assert {
            "ix_quantitative_claim_selection",
            "ix_quantitative_claim_assessment",
            "ix_quantitative_claim_review",
        } <= {item["name"] for item in inspector.get_indexes("quantitative_claim_versions")}
        foreign_keys = {
            item["referred_table"]
            for item in inspector.get_foreign_keys("quantitative_claim_versions")
        }
        assert {
            "record_versions",
            "quantitative_claim_records",
            "paim_cases",
            "managed_configuration_versions",
            "exact_context_sets",
            "responsibility_versions",
            "responsibility_assignment_versions",
        } <= foreign_keys
        with engine.connect() as connection:
            assert (
                connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
                == "0018_issue167_case_identity"
            )
            triggers = set(
                connection.execute(
                    text("SELECT name FROM sqlite_master WHERE type = 'trigger'")
                ).scalars()
            )
        for table in tables:
            assert f"prevent_{table}_update" in triggers
            assert f"prevent_{table}_delete" in triggers
    finally:
        engine.dispose()


def test_gate8_slice_g_exact_0015_upgrade_adds_only_measured_reconstruction_index(
    tmp_path: Path,
) -> None:
    database_path = (tmp_path / "upgrade-from-slice-f.sqlite3").as_posix()
    database_url = f"sqlite+pysqlite:///{database_path}"
    config = alembic_config(database_url)
    command.upgrade(config, "0015_gate8_quantitative_claims")
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO records (record_id, family, scope) "
                    "VALUES ('slice-g-preserved-record', 'test-family', 'test-scope')"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO record_versions "
                    "(version_id, record_id, content_json, finalized, recorded_at_us, "
                    "effective_from_us, effective_to_us, creator) VALUES "
                    "('slice-g-preserved-version', 'slice-g-preserved-record', '{}', 1, "
                    "100, 50, NULL, 'test')"
                )
            )
        before_tables = set(inspect(engine).get_table_names())
        command.upgrade(config, "head")
        inspector = inspect(engine)
        assert set(inspector.get_table_names()) == before_tables | {
            "case_initiation_authority_versions",
            "case_number_allocations",
            "source_access_grants",
        }
        indexes = {item["name"]: item for item in inspector.get_indexes("record_versions")}
        assert indexes["ix_versions_reconstruction_cutoff"]["column_names"] == [
            "recorded_at_us",
            "effective_from_us",
            "record_id",
        ]
        with engine.connect() as connection:
            assert (
                connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
                == "0018_issue167_case_identity"
            )
            assert (
                connection.execute(
                    text(
                        "SELECT content_json FROM record_versions "
                        "WHERE version_id='slice-g-preserved-version'"
                    )
                ).scalar_one()
                == "{}"
            )
            plan = " ".join(
                str(value)
                for row in connection.execute(
                    text(
                        "EXPLAIN QUERY PLAN SELECT record_id FROM record_versions "
                        "WHERE recorded_at_us <= 200 AND effective_from_us <= 200 "
                        "ORDER BY recorded_at_us, effective_from_us, record_id"
                    )
                )
                for value in row
            )
            assert "ix_versions_reconstruction_cutoff" in plan
        command.downgrade(config, "0015_gate8_quantitative_claims")
        assert "ix_versions_reconstruction_cutoff" not in {
            item["name"] for item in inspect(engine).get_indexes("record_versions")
        }
        with engine.connect() as connection:
            assert (
                connection.execute(
                    text(
                        "SELECT content_json FROM record_versions "
                        "WHERE version_id='slice-g-preserved-version'"
                    )
                ).scalar_one()
                == "{}"
            )
        command.upgrade(config, "head")
    finally:
        engine.dispose()


def test_gate8_slice_h0_exact_0016_upgrade_adds_bounded_append_only_contracts(
    tmp_path: Path,
) -> None:
    database_url = f"sqlite+pysqlite:///{(tmp_path / 'upgrade-from-slice-g.sqlite3').as_posix()}"
    config = alembic_config(database_url)
    command.upgrade(config, "0016_gate8_reconstruction_support")
    engine = create_engine(database_url)
    try:
        before = set(inspect(engine).get_table_names())
        command.upgrade(config, "head")
        inspector = inspect(engine)
        added = {
            "case_initiation_authority_versions",
            "case_number_allocations",
            "source_access_grants",
        }
        assert set(inspector.get_table_names()) == before | added
        source_fks = {
            item["referred_table"] for item in inspector.get_foreign_keys("source_access_grants")
        }
        assert {
            "operational_principals",
            "paim_cases",
            "managed_configurations",
            "record_versions",
        } <= source_fks
        authority_fks = {
            item["referred_table"]
            for item in inspector.get_foreign_keys("case_initiation_authority_versions")
        }
        assert {"records", "record_versions", "paim_actors"} <= authority_fks
        with engine.connect() as connection:
            assert connection.scalar(text("PRAGMA foreign_keys")) == 0
            assert connection.scalar(text("SELECT version_num FROM alembic_version")) == (
                "0018_issue167_case_identity"
            )
            triggers = set(
                connection.scalars(text("SELECT name FROM sqlite_master WHERE type='trigger'"))
            )
        for table in added:
            assert f"prevent_{table}_update" in triggers
            assert f"prevent_{table}_delete" in triggers
        indexes = {item["name"] for item in inspector.get_indexes("source_access_grants")}
        assert "ix_source_access_resolution" in indexes
        indexes = {
            item["name"] for item in inspector.get_indexes("case_initiation_authority_versions")
        }
        assert "ix_case_initiation_authority_selection" in indexes
    finally:
        engine.dispose()


def test_issue167_case_numbers_backfill_once_and_are_immutable(tmp_path: Path) -> None:
    database_url = f"sqlite+pysqlite:///{(tmp_path / 'issue167-case-number.sqlite3').as_posix()}"
    config = alembic_config(database_url)
    command.upgrade(config, "0017_gate8_slice_h0_prerequisites")
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO records (record_id, family, scope) "
                    "VALUES ('legacy-case', 'case', 'legacy')"
                )
            )
            connection.execute(text("INSERT INTO paim_cases (case_id) VALUES ('legacy-case')"))
        command.upgrade(config, "head")
        with engine.connect() as connection:
            assert (
                connection.scalar(
                    text(
                        "SELECT case_number FROM case_number_allocations "
                        "WHERE case_id='legacy-case'"
                    )
                )
                == "PAIM-0001"
            )
        with (
            pytest.raises(DBAPIError, match="Case-number history is immutable"),
            engine.begin() as connection,
        ):
            connection.execute(
                text(
                    "UPDATE case_number_allocations SET case_number='PAIM-9999' "
                    "WHERE case_id='legacy-case'"
                )
            )
    finally:
        engine.dispose()
