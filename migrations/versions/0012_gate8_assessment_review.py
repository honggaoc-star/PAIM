"""Add prospective independent assessment review persistence.

Revision ID: 0012_gate8_assessment_review
Revises: 0011_gate8_case_continuity
"""

from collections.abc import Sequence

from alembic import op

from paim.persistence.sqlite.schema import (
    assessment_adequacy_records,
    assessment_adequacy_versions,
    assessment_candidate_records,
    assessment_candidate_versions,
    assessment_readiness_records,
    assessment_readiness_versions,
    assessment_reliance_records,
    assessment_reliance_versions,
)

revision: str = "0012_gate8_assessment_review"
down_revision: str | Sequence[str] | None = "0011_gate8_case_continuity"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = (
    assessment_candidate_records,
    assessment_readiness_records,
    assessment_adequacy_records,
    assessment_reliance_records,
    assessment_candidate_versions,
    assessment_readiness_versions,
    assessment_adequacy_versions,
    assessment_reliance_versions,
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
                  SELECT RAISE(ABORT, 'prospective assessment review history is append-only');
                END"""
            )


def downgrade() -> None:
    bind = op.get_bind()
    if any(
        bind.exec_driver_sql(f"SELECT COUNT(*) FROM {table.name}").scalar_one() for table in _TABLES
    ):
        raise RuntimeError(
            "0012 contains prospective assessment review facts; destructive rollback is prohibited"
        )
    for table in reversed(_TABLES):
        for action in ("DELETE", "UPDATE"):
            op.execute(f"DROP TRIGGER IF EXISTS prevent_{table.name}_{action.casefold()}")
        table.drop(bind=bind, checkfirst=False)
