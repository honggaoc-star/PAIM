"""Add optional quantitative claims and explicit comparability.

Revision ID: 0015_gate8_quantitative_claims
Revises: 0014_gate8_continuing_review
"""

from collections.abc import Sequence

from alembic import op

from paim.persistence.sqlite.schema import (
    quantitative_claim_basis_links,
    quantitative_claim_records,
    quantitative_claim_versions,
    quantitative_comparability_records,
    quantitative_comparability_versions,
)

revision: str = "0015_gate8_quantitative_claims"
down_revision: str | Sequence[str] | None = "0014_gate8_continuing_review"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = (
    quantitative_claim_records,
    quantitative_comparability_records,
    quantitative_claim_versions,
    quantitative_claim_basis_links,
    quantitative_comparability_versions,
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
                  SELECT RAISE(ABORT, 'quantitative claim history is append-only');
                END"""
            )


def downgrade() -> None:
    bind = op.get_bind()
    if any(
        bind.exec_driver_sql(f"SELECT COUNT(*) FROM {table.name}").scalar_one() for table in _TABLES
    ):
        raise RuntimeError(
            "0015 contains quantitative claim facts; destructive rollback is prohibited"
        )
    for table in reversed(_TABLES):
        for action in ("DELETE", "UPDATE"):
            op.execute(f"DROP TRIGGER IF EXISTS prevent_{table.name}_{action.casefold()}")
        table.drop(bind=bind, checkfirst=False)
