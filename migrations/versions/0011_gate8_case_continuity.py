"""Add prospective continuing Case persistence.

Revision ID: 0011_gate8_case_continuity
Revises: 0010_gate8_responsibility_work
"""

from collections.abc import Sequence

from alembic import op

from paim.persistence.sqlite.schema import (
    case_continuity_determination_records,
    case_continuity_determination_versions,
    case_continuity_relationships,
    case_continuity_status_records,
    case_continuity_status_versions,
    configuration_continuity_links,
)

revision: str = "0011_gate8_case_continuity"
down_revision: str | Sequence[str] | None = "0010_gate8_responsibility_work"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = (
    case_continuity_determination_records,
    case_continuity_status_records,
    case_continuity_determination_versions,
    case_continuity_status_versions,
    case_continuity_relationships,
    configuration_continuity_links,
)


def _append_only(name: str) -> None:
    for action in ("UPDATE", "DELETE"):
        op.execute(
            f"""CREATE TRIGGER prevent_{name}_{action.casefold()}
            BEFORE {action} ON {name} BEGIN
              SELECT RAISE(ABORT, 'prospective Case continuity history is append-only');
            END"""
        )


def upgrade() -> None:
    bind = op.get_bind()
    # The status/determination projections reference each other. SQLite permits
    # creation before the referenced table exists inside the same migration.
    for table in _TABLES:
        table.create(bind=bind, checkfirst=False)
    for table in _TABLES:
        _append_only(table.name)


def downgrade() -> None:
    bind = op.get_bind()
    if any(
        bind.exec_driver_sql(f"SELECT COUNT(*) FROM {table.name}").scalar_one() for table in _TABLES
    ):
        raise RuntimeError(
            "0011 contains prospective Case continuity facts; destructive rollback is prohibited"
        )
    # An empty development schema may still be downgraded. Once authoritative
    # facts exist the guard above makes this revision forward-only.
    for table in reversed(_TABLES):
        for action in ("DELETE", "UPDATE"):
            op.execute(f"DROP TRIGGER IF EXISTS prevent_{table.name}_{action.casefold()}")
        table.drop(bind=bind, checkfirst=False)
