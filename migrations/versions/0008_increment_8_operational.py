"""Create Increment 8 local operational support schema.

Revision ID: 0008_increment_8
Revises: 0007_increment_7
"""

from collections.abc import Sequence

from alembic import op

from paim.persistence.sqlite.schema import (
    adapter_intakes,
    notification_delivery_events,
    operational_audit_facts,
    operational_principal_versions,
    operational_principals,
    operational_register_rebuild_bases,
    software_access_grants,
)

revision: str = "0008_increment_8"
down_revision: str | Sequence[str] | None = "0007_increment_7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = (
    operational_principals,
    operational_principal_versions,
    software_access_grants,
    operational_audit_facts,
    adapter_intakes,
    notification_delivery_events,
    operational_register_rebuild_bases,
)


def _append_only(table_name: str) -> None:
    for action in ("UPDATE", "DELETE"):
        op.execute(
            f"""CREATE TRIGGER prevent_{table_name}_{action.casefold()}
            BEFORE {action} ON {table_name}
            BEGIN
              SELECT RAISE(ABORT, 'Increment 8 operational history is append-only');
            END"""
        )


def upgrade() -> None:
    bind = op.get_bind()
    for table in _TABLES:
        table.create(bind=bind, checkfirst=False)
    for table in _TABLES:
        _append_only(table.name)


def downgrade() -> None:
    bind = op.get_bind()
    for table in reversed(_TABLES):
        for action in ("DELETE", "UPDATE"):
            op.execute(f"DROP TRIGGER IF EXISTS prevent_{table.name}_{action.casefold()}")
        table.drop(bind=bind, checkfirst=False)
