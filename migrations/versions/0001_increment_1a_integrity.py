"""Create the domain-neutral Increment 1A integrity schema.

Revision ID: 0001_increment_1a
Revises: None
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_increment_1a"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "records",
        sa.Column("record_id", sa.String(length=36), nullable=False),
        sa.Column("family", sa.Text(), nullable=False),
        sa.Column("scope", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("record_id"),
        sa.UniqueConstraint("record_id", "family", "scope", name="uq_record_identity_scope"),
    )
    op.create_table(
        "record_versions",
        sa.Column("version_id", sa.String(length=36), nullable=False),
        sa.Column("record_id", sa.String(length=36), nullable=False),
        sa.Column("content_json", sa.Text(), nullable=False),
        sa.Column("finalized", sa.Boolean(), nullable=False),
        sa.Column("recorded_at_us", sa.BigInteger(), nullable=False),
        sa.Column("effective_from_us", sa.BigInteger(), nullable=False),
        sa.Column("effective_to_us", sa.BigInteger(), nullable=True),
        sa.Column("creator", sa.Text(), nullable=False),
        sa.CheckConstraint(
            "effective_to_us IS NULL OR effective_to_us > effective_from_us",
            name="ck_version_effective_interval",
        ),
        sa.ForeignKeyConstraint(["record_id"], ["records.record_id"]),
        sa.PrimaryKeyConstraint("version_id"),
    )
    op.create_index(
        "ix_versions_scope_time",
        "record_versions",
        ["record_id", "effective_from_us", "effective_to_us", "recorded_at_us"],
    )
    op.create_table(
        "status_events",
        sa.Column("event_id", sa.String(length=36), nullable=False),
        sa.Column("target_version_id", sa.String(length=36), nullable=False),
        sa.Column("prior_status", sa.Text(), nullable=False),
        sa.Column("new_status", sa.Text(), nullable=False),
        sa.Column("recorded_at_us", sa.BigInteger(), nullable=False),
        sa.Column("effective_at_us", sa.BigInteger(), nullable=False),
        sa.Column("actor", sa.Text(), nullable=False),
        sa.Column("basis", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["target_version_id"], ["record_versions.version_id"]),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.create_index(
        "ix_status_target_time",
        "status_events",
        ["target_version_id", "effective_at_us", "recorded_at_us"],
    )
    op.create_table(
        "version_relationships",
        sa.Column("relationship_id", sa.String(length=36), nullable=False),
        sa.Column("source_version_id", sa.String(length=36), nullable=False),
        sa.Column("target_version_id", sa.String(length=36), nullable=False),
        sa.Column("relationship_type", sa.Text(), nullable=False),
        sa.Column("recorded_at_us", sa.BigInteger(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.CheckConstraint(
            "source_version_id <> target_version_id", name="ck_relationship_distinct_versions"
        ),
        sa.ForeignKeyConstraint(["source_version_id"], ["record_versions.version_id"]),
        sa.ForeignKeyConstraint(["target_version_id"], ["record_versions.version_id"]),
        sa.PrimaryKeyConstraint("relationship_id"),
    )
    op.create_index(
        "ix_relationship_source_target",
        "version_relationships",
        ["source_version_id", "target_version_id"],
    )
    op.create_table(
        "idempotency_facts",
        sa.Column("scope", sa.Text(), nullable=False),
        sa.Column("idempotency_key", sa.Text(), nullable=False),
        sa.Column("digest", sa.String(length=64), nullable=False),
        sa.Column("command_id", sa.String(length=36), nullable=False),
        sa.Column("outcome_json", sa.Text(), nullable=False),
        sa.Column("recorded_at_us", sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint("scope", "idempotency_key"),
    )
    op.create_table(
        "audit_facts",
        sa.Column("audit_id", sa.String(length=36), nullable=False),
        sa.Column("principal_id", sa.Text(), nullable=False),
        sa.Column("actor_id", sa.Text(), nullable=True),
        sa.Column("actor_resolution", sa.Text(), nullable=False),
        sa.Column("operation", sa.Text(), nullable=False),
        sa.Column("result", sa.Text(), nullable=False),
        sa.Column("command_id", sa.String(length=36), nullable=False),
        sa.Column("idempotency_scope", sa.Text(), nullable=False),
        sa.Column("idempotency_key", sa.Text(), nullable=False),
        sa.Column("correlation_id", sa.Text(), nullable=True),
        sa.Column("causation_id", sa.Text(), nullable=True),
        sa.Column("target_record_id", sa.String(length=36), nullable=False),
        sa.Column("affected_version_ids_json", sa.Text(), nullable=False),
        sa.Column("expected_precondition", sa.Text(), nullable=False),
        sa.Column("observed_precondition", sa.Text(), nullable=False),
        sa.Column("effective_at_us", sa.BigInteger(), nullable=False),
        sa.Column("recorded_at_us", sa.BigInteger(), nullable=False),
        sa.Column("reason_outcomes_json", sa.Text(), nullable=False),
        sa.Column("request_digest", sa.String(length=64), nullable=False),
        sa.CheckConstraint(
            "(actor_resolution = 'provided' AND actor_id IS NOT NULL) OR "
            "(actor_resolution IN ('unresolved', 'not_applicable') AND actor_id IS NULL)",
            name="ck_audit_actor_resolution",
        ),
        sa.ForeignKeyConstraint(["target_record_id"], ["records.record_id"]),
        sa.PrimaryKeyConstraint("audit_id"),
    )
    for name, table, message, condition in (
        (
            "prevent_finalized_version_update",
            "record_versions",
            "finalized content is immutable",
            "WHEN OLD.finalized = 1",
        ),
        (
            "prevent_record_version_delete",
            "record_versions",
            "record version history is append-preserving",
            "",
        ),
        ("prevent_status_event_update", "status_events", "status event history is append-only", ""),
        ("prevent_status_event_delete", "status_events", "status event history is append-only", ""),
        (
            "prevent_relationship_update",
            "version_relationships",
            "version relationships are append-only",
            "",
        ),
        (
            "prevent_relationship_delete",
            "version_relationships",
            "version relationships are append-only",
            "",
        ),
        (
            "prevent_idempotency_update",
            "idempotency_facts",
            "idempotency facts are immutable",
            "",
        ),
        (
            "prevent_idempotency_delete",
            "idempotency_facts",
            "idempotency facts are immutable",
            "",
        ),
        ("prevent_audit_update", "audit_facts", "audit facts are append-only", ""),
        ("prevent_audit_delete", "audit_facts", "audit facts are append-only", ""),
    ):
        action = "UPDATE" if name.endswith("update") else "DELETE"
        op.execute(
            f"""CREATE TRIGGER {name}
            BEFORE {action} ON {table}
            {condition}
            BEGIN
              SELECT RAISE(ABORT, '{message}');
            END"""
        )


def downgrade() -> None:
    for name in (
        "prevent_audit_delete",
        "prevent_audit_update",
        "prevent_idempotency_delete",
        "prevent_idempotency_update",
        "prevent_relationship_delete",
        "prevent_relationship_update",
        "prevent_status_event_delete",
        "prevent_status_event_update",
        "prevent_record_version_delete",
        "prevent_finalized_version_update",
    ):
        op.execute(f"DROP TRIGGER IF EXISTS {name}")
    op.drop_table("audit_facts")
    op.drop_table("idempotency_facts")
    op.drop_index("ix_relationship_source_target", table_name="version_relationships")
    op.drop_table("version_relationships")
    op.drop_index("ix_status_target_time", table_name="status_events")
    op.drop_table("status_events")
    op.drop_index("ix_versions_scope_time", table_name="record_versions")
    op.drop_table("record_versions")
    op.drop_table("records")
