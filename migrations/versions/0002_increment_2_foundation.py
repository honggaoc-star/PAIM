"""Create Increment 2 Case, Configuration, lifecycle, and Roles schema.

Revision ID: 0002_increment_2
Revises: 0001_increment_1a
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_increment_2"
down_revision: str | Sequence[str] | None = "0001_increment_1a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "paim_cases",
        sa.Column("case_id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["records.record_id"]),
        sa.PrimaryKeyConstraint("case_id"),
    )
    op.create_table(
        "paim_case_versions",
        sa.Column("version_id", sa.String(length=36), nullable=False),
        sa.Column("case_id", sa.String(length=36), nullable=False),
        sa.Column("initial_lifecycle_state", sa.Text(), nullable=False),
        sa.CheckConstraint("initial_lifecycle_state = 'open'", name="ck_case_initial_state_open"),
        sa.ForeignKeyConstraint(["case_id"], ["paim_cases.case_id"]),
        sa.ForeignKeyConstraint(["version_id"], ["record_versions.version_id"]),
        sa.PrimaryKeyConstraint("version_id"),
    )
    op.create_index("ix_case_versions_case", "paim_case_versions", ["case_id"])
    op.create_table(
        "paim_case_links",
        sa.Column("link_id", sa.String(length=36), nullable=False),
        sa.Column("source_case_id", sa.String(length=36), nullable=False),
        sa.Column("target_case_id", sa.String(length=36), nullable=False),
        sa.Column("relationship_type", sa.Text(), nullable=False),
        sa.Column("recorded_at_us", sa.BigInteger(), nullable=False),
        sa.Column("effective_at_us", sa.BigInteger(), nullable=False),
        sa.Column("actor_id", sa.String(length=36), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.CheckConstraint("source_case_id <> target_case_id", name="ck_case_link_distinct_cases"),
        sa.ForeignKeyConstraint(["source_case_id"], ["paim_cases.case_id"]),
        sa.ForeignKeyConstraint(["target_case_id"], ["paim_cases.case_id"]),
        sa.PrimaryKeyConstraint("link_id"),
    )
    op.create_index(
        "ix_case_links_cases_time",
        "paim_case_links",
        ["source_case_id", "target_case_id", "effective_at_us"],
    )
    op.create_table(
        "managed_configurations",
        sa.Column("configuration_id", sa.String(length=36), nullable=False),
        sa.Column("owning_case_id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(["configuration_id"], ["records.record_id"]),
        sa.ForeignKeyConstraint(["owning_case_id"], ["paim_cases.case_id"]),
        sa.PrimaryKeyConstraint("configuration_id"),
    )
    op.create_index("ix_configurations_owning_case", "managed_configurations", ["owning_case_id"])
    op.create_table(
        "managed_configuration_versions",
        sa.Column("version_id", sa.String(length=36), nullable=False),
        sa.Column("configuration_id", sa.String(length=36), nullable=False),
        sa.Column("maturity", sa.Text(), nullable=False),
        sa.Column("purpose", sa.Text(), nullable=False),
        sa.CheckConstraint("maturity IN ('draft', 'finalized')", name="ck_configuration_maturity"),
        sa.CheckConstraint(
            "purpose IN ('candidate', 'proposed', 'experimental', 'alternative', 'fallback')",
            name="ck_configuration_purpose",
        ),
        sa.ForeignKeyConstraint(["configuration_id"], ["managed_configurations.configuration_id"]),
        sa.ForeignKeyConstraint(["version_id"], ["record_versions.version_id"]),
        sa.PrimaryKeyConstraint("version_id"),
    )
    op.create_index(
        "ix_configuration_versions_identity",
        "managed_configuration_versions",
        ["configuration_id"],
    )
    op.create_table(
        "paim_actors",
        sa.Column("actor_id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["records.record_id"]),
        sa.PrimaryKeyConstraint("actor_id"),
    )
    op.create_table(
        "paim_actor_versions",
        sa.Column("version_id", sa.String(length=36), nullable=False),
        sa.Column("actor_id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["paim_actors.actor_id"]),
        sa.ForeignKeyConstraint(["version_id"], ["record_versions.version_id"]),
        sa.PrimaryKeyConstraint("version_id"),
    )
    op.create_index("ix_actor_versions_identity", "paim_actor_versions", ["actor_id"])
    op.create_table(
        "role_assignments",
        sa.Column("assignment_id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(["assignment_id"], ["records.record_id"]),
        sa.PrimaryKeyConstraint("assignment_id"),
    )
    op.create_table(
        "role_assignment_versions",
        sa.Column("version_id", sa.String(length=36), nullable=False),
        sa.Column("assignment_id", sa.String(length=36), nullable=False),
        sa.Column("actor_id", sa.String(length=36), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("target_type", sa.Text(), nullable=False),
        sa.Column("target_id", sa.Text(), nullable=False),
        sa.Column("case_context_id", sa.String(length=36), nullable=True),
        sa.Column("accountable", sa.Boolean(), nullable=False),
        sa.Column("compatibility_key", sa.Text(), nullable=False),
        sa.Column("delegation_effect", sa.Text(), nullable=False),
        sa.Column("delegated_from_version_id", sa.String(length=36), nullable=True),
        sa.CheckConstraint(
            "target_type IN ('organization', 'business_unit', 'case', 'configuration', "
            "'decision', 'intervention', 'authority_domain')",
            name="ck_role_target_type",
        ),
        sa.CheckConstraint(
            "(target_type IN ('organization', 'business_unit') AND case_context_id IS NULL) OR "
            "(target_type = 'case' AND case_context_id = target_id) OR "
            "(target_type = 'configuration' AND case_context_id IS NOT NULL) OR "
            "(target_type IN ('decision', 'intervention', 'authority_domain'))",
            name="ck_role_case_context",
        ),
        sa.CheckConstraint(
            "delegation_effect IN ('none', 'supplement', 'transfer', 'retain')",
            name="ck_role_delegation_effect",
        ),
        sa.CheckConstraint(
            "(delegation_effect = 'none' AND delegated_from_version_id IS NULL) OR "
            "(delegation_effect <> 'none' AND delegated_from_version_id IS NOT NULL)",
            name="ck_role_delegation_source",
        ),
        sa.ForeignKeyConstraint(["actor_id"], ["paim_actors.actor_id"]),
        sa.ForeignKeyConstraint(["assignment_id"], ["role_assignments.assignment_id"]),
        sa.ForeignKeyConstraint(["case_context_id"], ["paim_cases.case_id"]),
        sa.ForeignKeyConstraint(
            ["delegated_from_version_id"], ["role_assignment_versions.version_id"]
        ),
        sa.ForeignKeyConstraint(["version_id"], ["record_versions.version_id"]),
        sa.PrimaryKeyConstraint("version_id"),
    )
    op.create_index(
        "ix_role_assignments_resolution",
        "role_assignment_versions",
        ["role", "target_type", "target_id", "case_context_id"],
    )
    op.create_table(
        "governing_configuration_designations",
        sa.Column("version_id", sa.String(length=36), nullable=False),
        sa.Column("case_id", sa.String(length=36), nullable=False),
        sa.Column("configuration_version_id", sa.String(length=36), nullable=False),
        sa.Column("accountable_assignment_version_id", sa.String(length=36), nullable=True),
        sa.Column("accountable_mechanism", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "(accountable_assignment_version_id IS NOT NULL AND accountable_mechanism IS NULL) OR "
            "(accountable_assignment_version_id IS NULL AND accountable_mechanism IS NOT NULL)",
            name="ck_governing_accountability_exactly_one",
        ),
        sa.ForeignKeyConstraint(
            ["accountable_assignment_version_id"], ["role_assignment_versions.version_id"]
        ),
        sa.ForeignKeyConstraint(["case_id"], ["paim_cases.case_id"]),
        sa.ForeignKeyConstraint(
            ["configuration_version_id"], ["managed_configuration_versions.version_id"]
        ),
        sa.ForeignKeyConstraint(["version_id"], ["record_versions.version_id"]),
        sa.PrimaryKeyConstraint("version_id"),
    )
    op.create_index(
        "ix_governing_designation_case", "governing_configuration_designations", ["case_id"]
    )
    op.create_table(
        "configuration_determinations",
        sa.Column("version_id", sa.String(length=36), nullable=False),
        sa.Column("configuration_version_id", sa.String(length=36), nullable=False),
        sa.Column("determination_kind", sa.Text(), nullable=False),
        sa.Column("outcome", sa.Text(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("accountable_assignment_version_id", sa.String(length=36), nullable=True),
        sa.Column("accountable_mechanism", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "determination_kind IN ('materiality', 'identity_continuity')",
            name="ck_determination_kind",
        ),
        sa.CheckConstraint(
            "(determination_kind = 'materiality' AND outcome IN ('material', 'non_material')) OR "
            "(determination_kind = 'identity_continuity' AND "
            "outcome IN ('same_identity', 'new_identity'))",
            name="ck_determination_outcome",
        ),
        sa.CheckConstraint("length(trim(rationale)) > 0", name="ck_determination_rationale"),
        sa.CheckConstraint(
            "(accountable_assignment_version_id IS NOT NULL AND accountable_mechanism IS NULL) OR "
            "(accountable_assignment_version_id IS NULL AND accountable_mechanism IS NOT NULL)",
            name="ck_determination_accountability_exactly_one",
        ),
        sa.ForeignKeyConstraint(
            ["accountable_assignment_version_id"], ["role_assignment_versions.version_id"]
        ),
        sa.ForeignKeyConstraint(
            ["configuration_version_id"], ["managed_configuration_versions.version_id"]
        ),
        sa.ForeignKeyConstraint(["version_id"], ["record_versions.version_id"]),
        sa.PrimaryKeyConstraint("version_id"),
    )
    op.create_index(
        "ix_determination_configuration_kind",
        "configuration_determinations",
        ["configuration_version_id", "determination_kind"],
    )

    for table in (
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
    ):
        for action in ("UPDATE", "DELETE"):
            trigger = f"prevent_{table}_{action.casefold()}"
            op.execute(
                f"""CREATE TRIGGER {trigger}
                BEFORE {action} ON {table}
                BEGIN
                  SELECT RAISE(ABORT, 'Increment 2 authoritative history is append-only');
                END"""
            )


def downgrade() -> None:
    for table in reversed(
        (
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
        )
    ):
        for action in ("DELETE", "UPDATE"):
            op.execute(f"DROP TRIGGER IF EXISTS prevent_{table}_{action.casefold()}")
    op.drop_index("ix_determination_configuration_kind", table_name="configuration_determinations")
    op.drop_table("configuration_determinations")
    op.drop_index(
        "ix_governing_designation_case", table_name="governing_configuration_designations"
    )
    op.drop_table("governing_configuration_designations")
    op.drop_index("ix_role_assignments_resolution", table_name="role_assignment_versions")
    op.drop_table("role_assignment_versions")
    op.drop_table("role_assignments")
    op.drop_index("ix_actor_versions_identity", table_name="paim_actor_versions")
    op.drop_table("paim_actor_versions")
    op.drop_table("paim_actors")
    op.drop_index("ix_configuration_versions_identity", table_name="managed_configuration_versions")
    op.drop_table("managed_configuration_versions")
    op.drop_index("ix_configurations_owning_case", table_name="managed_configurations")
    op.drop_table("managed_configurations")
    op.drop_index("ix_case_links_cases_time", table_name="paim_case_links")
    op.drop_table("paim_case_links")
    op.drop_index("ix_case_versions_case", table_name="paim_case_versions")
    op.drop_table("paim_case_versions")
    op.drop_table("paim_cases")
