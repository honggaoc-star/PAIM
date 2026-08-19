"""Create Increment 7 Shared Dependency and Management Register support schema.

Revision ID: 0007_increment_7
Revises: 0006_increment_6
"""

from collections.abc import Sequence

from alembic import op

from paim.persistence.sqlite.schema import (
    dependency_candidate_set_members,
    dependency_candidate_set_records,
    dependency_candidate_set_versions,
    register_notification_intents,
    register_output_manifests,
    shared_dependency_equivalence_delegations,
    shared_dependency_equivalence_records,
    shared_dependency_equivalence_versions,
    shared_dependency_mechanism_records,
    shared_dependency_mechanism_versions,
    shared_dependency_records,
    shared_dependency_versions,
)

revision: str = "0007_increment_7"
down_revision: str | Sequence[str] | None = "0006_increment_6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = (
    shared_dependency_records,
    shared_dependency_versions,
    dependency_candidate_set_records,
    dependency_candidate_set_versions,
    dependency_candidate_set_members,
    shared_dependency_mechanism_records,
    shared_dependency_mechanism_versions,
    shared_dependency_equivalence_records,
    shared_dependency_equivalence_versions,
    shared_dependency_equivalence_delegations,
    register_output_manifests,
    register_notification_intents,
)


def _append_only(table_name: str, label: str = "Increment 7 history") -> None:
    for action in ("UPDATE", "DELETE"):
        trigger = f"prevent_{table_name}_{action.casefold()}"
        op.execute(
            f"""CREATE TRIGGER {trigger}
            BEFORE {action} ON {table_name}
            BEGIN
              SELECT RAISE(ABORT, '{label} is append-only');
            END"""
        )


def upgrade() -> None:
    bind = op.get_bind()
    for table in _TABLES:
        table.create(bind=bind, checkfirst=False)
    for table in _TABLES:
        _append_only(table.name)

    # Increment 7 adds two exact portfolio typed targets to the existing Role
    # Assignment vocabulary. Recreate only the CHECK contracts; all columns,
    # rows, foreign keys, and the established resolution index are preserved.
    for action in ("UPDATE", "DELETE"):
        op.execute(f"DROP TRIGGER prevent_role_assignment_versions_{action.casefold()}")
    with op.batch_alter_table("role_assignment_versions", recreate="always") as batch:
        batch.drop_constraint("ck_role_target_type", type_="check")
        batch.drop_constraint("ck_role_case_context", type_="check")
        batch.create_check_constraint(
            "ck_role_target_type",
            "target_type IN ('organization', 'business_unit', 'case', 'configuration', "
            "'decision', 'intervention', 'authority_domain', "
            "'dependency_candidate_set', 'shared_dependency')",
        )
        batch.create_check_constraint(
            "ck_role_case_context",
            "(target_type IN ('organization', 'business_unit') AND case_context_id IS NULL) OR "
            "(target_type = 'case' AND case_context_id = target_id) OR "
            "(target_type = 'configuration' AND case_context_id IS NOT NULL) OR "
            "(target_type IN ('decision', 'intervention', 'authority_domain', "
            "'dependency_candidate_set', 'shared_dependency'))",
        )
    _append_only("role_assignment_versions", "Increment 2 authoritative history")


def downgrade() -> None:
    # Refuse to silently squeeze Increment 7 typed Role Assignments into an
    # older vocabulary. A downgrade is safe only after the new target types
    # have no rows.
    bind = op.get_bind()
    count = bind.exec_driver_sql(
        "SELECT COUNT(*) FROM role_assignment_versions "
        "WHERE target_type IN ('dependency_candidate_set','shared_dependency')"
    ).scalar_one()
    if count:
        raise RuntimeError("remove Increment 7 typed Role Assignments before downgrade")

    for action in ("UPDATE", "DELETE"):
        op.execute(f"DROP TRIGGER prevent_role_assignment_versions_{action.casefold()}")
    with op.batch_alter_table("role_assignment_versions", recreate="always") as batch:
        batch.drop_constraint("ck_role_target_type", type_="check")
        batch.drop_constraint("ck_role_case_context", type_="check")
        batch.create_check_constraint(
            "ck_role_target_type",
            "target_type IN ('organization', 'business_unit', 'case', 'configuration', "
            "'decision', 'intervention', 'authority_domain')",
        )
        batch.create_check_constraint(
            "ck_role_case_context",
            "(target_type IN ('organization', 'business_unit') AND case_context_id IS NULL) OR "
            "(target_type = 'case' AND case_context_id = target_id) OR "
            "(target_type = 'configuration' AND case_context_id IS NOT NULL) OR "
            "(target_type IN ('decision', 'intervention', 'authority_domain'))",
        )
    _append_only("role_assignment_versions", "Increment 2 authoritative history")

    bind = op.get_bind()
    for table in reversed(_TABLES):
        for action in ("DELETE", "UPDATE"):
            op.execute(f"DROP TRIGGER IF EXISTS prevent_{table.name}_{action.casefold()}")
        table.drop(bind=bind, checkfirst=False)
