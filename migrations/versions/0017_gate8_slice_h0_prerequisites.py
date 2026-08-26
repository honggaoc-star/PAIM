"""Add Slice-H0 Case-initiation authority and exact-source access.

Revision ID: 0017_gate8_slice_h0_prerequisites
Revises: 0016_gate8_reconstruction_support
"""

from collections.abc import Sequence

from alembic import op

from paim.persistence.sqlite.schema import (
    case_initiation_authority_versions,
    source_access_grants,
)

revision: str = "0017_gate8_slice_h0_prerequisites"
down_revision: str | Sequence[str] | None = "0016_gate8_reconstruction_support"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = (case_initiation_authority_versions, source_access_grants)


def _append_only(name: str) -> None:
    for action in ("UPDATE", "DELETE"):
        op.execute(
            f"""CREATE TRIGGER prevent_{name}_{action.casefold()}
            BEFORE {action} ON {name} BEGIN
              SELECT RAISE(ABORT, 'Slice-H0 authority/access history is append-only');
            END"""
        )


def upgrade() -> None:
    bind = op.get_bind()
    for table in _TABLES:
        table.create(bind=bind, checkfirst=False)
        _append_only(table.name)


def downgrade() -> None:
    bind = op.get_bind()
    if any(
        bind.exec_driver_sql(f"SELECT COUNT(*) FROM {table.name}").scalar_one() for table in _TABLES
    ):
        raise RuntimeError("0017 contains authoritative facts; destructive rollback is prohibited")
    for table in reversed(_TABLES):
        for action in ("DELETE", "UPDATE"):
            op.execute(f"DROP TRIGGER IF EXISTS prevent_{table.name}_{action.casefold()}")
        table.drop(bind=bind, checkfirst=False)
