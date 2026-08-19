"""Create Increment 6 Trigger, Reassessment, and Interim Disposition schema.

Revision ID: 0006_increment_6
Revises: 0005_increment_5
"""

from collections.abc import Sequence

from alembic import op

from paim.persistence.sqlite.schema import (
    decision_confirmation_records,
    decision_confirmation_versions,
    interim_disposition_records,
    interim_disposition_versions,
    reassessment_completion_outcomes,
    reassessment_determination_reassessments,
    reassessment_determination_records,
    reassessment_determination_triggers,
    reassessment_determination_versions,
    reassessment_mechanism_records,
    reassessment_mechanism_versions,
    reassessment_records,
    reassessment_versions,
    trigger_determination_records,
    trigger_determination_versions,
    trigger_membership_records,
    trigger_membership_versions,
    trigger_records,
    trigger_set_members,
    trigger_versions,
)

revision: str = "0006_increment_6"
down_revision: str | Sequence[str] | None = "0005_increment_5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = (
    reassessment_mechanism_records,
    reassessment_mechanism_versions,
    trigger_records,
    trigger_versions,
    trigger_determination_records,
    trigger_determination_versions,
    reassessment_records,
    reassessment_versions,
    trigger_membership_records,
    trigger_membership_versions,
    trigger_set_members,
    reassessment_determination_records,
    reassessment_determination_versions,
    reassessment_determination_triggers,
    reassessment_determination_reassessments,
    interim_disposition_records,
    interim_disposition_versions,
    decision_confirmation_records,
    decision_confirmation_versions,
    reassessment_completion_outcomes,
)


def upgrade() -> None:
    bind = op.get_bind()
    for table in _TABLES:
        table.create(bind=bind, checkfirst=False)
    for table in _TABLES:
        for action in ("UPDATE", "DELETE"):
            trigger = f"prevent_{table.name}_{action.casefold()}"
            op.execute(
                f"""CREATE TRIGGER {trigger}
                BEFORE {action} ON {table.name}
                BEGIN
                  SELECT RAISE(ABORT, 'Increment 6 authoritative history is append-only');
                END"""
            )


def downgrade() -> None:
    bind = op.get_bind()
    for table in reversed(_TABLES):
        for action in ("DELETE", "UPDATE"):
            op.execute(f"DROP TRIGGER IF EXISTS prevent_{table.name}_{action.casefold()}")
        table.drop(bind=bind, checkfirst=False)
