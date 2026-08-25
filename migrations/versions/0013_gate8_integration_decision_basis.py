"""Add prospective Integration and Decision basis persistence.

Revision ID: 0013_gate8_integration_decision_basis
Revises: 0012_gate8_assessment_review
"""

from collections.abc import Sequence

from alembic import op

from paim.persistence.sqlite.schema import (
    prospective_decision_authorization_records,
    prospective_decision_authorization_versions,
    prospective_decision_confirmation_records,
    prospective_decision_confirmation_versions,
    prospective_decision_records,
    prospective_decision_versions,
    prospective_integration_records,
    prospective_integration_versions,
)

revision: str = "0013_gate8_integration_decision_basis"
down_revision: str | Sequence[str] | None = "0012_gate8_assessment_review"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = (
    prospective_integration_records,
    prospective_decision_records,
    prospective_decision_authorization_records,
    prospective_decision_confirmation_records,
    prospective_integration_versions,
    prospective_decision_versions,
    prospective_decision_authorization_versions,
    prospective_decision_confirmation_versions,
)


def upgrade() -> None:
    bind = op.get_bind()
    for table in _TABLES:
        table.create(bind=bind, checkfirst=False)
    for table in _TABLES:
        for action in ("UPDATE", "DELETE"):
            op.execute(
                f"""CREATE TRIGGER prevent_{table.name}_{action.casefold()}
                BEFORE {action} ON {table.name} BEGIN
                  SELECT RAISE(ABORT, 'prospective Integration/Decision history is append-only');
                END"""
            )


def downgrade() -> None:
    bind = op.get_bind()
    if any(
        bind.exec_driver_sql(f"SELECT COUNT(*) FROM {table.name}").scalar_one() for table in _TABLES
    ):
        raise RuntimeError(
            "0013 contains prospective Integration/Decision facts; "
            "destructive rollback is prohibited"
        )
    for table in reversed(_TABLES):
        for action in ("DELETE", "UPDATE"):
            op.execute(f"DROP TRIGGER IF EXISTS prevent_{table.name}_{action.casefold()}")
        table.drop(bind=bind, checkfirst=False)
