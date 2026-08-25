"""Add prospective Responsibility and durable Case Work.

Revision ID: 0010_gate8_responsibility_work
Revises: 0009_gate8_common_semantics
"""

from collections.abc import Sequence

from alembic import op

from paim.persistence.sqlite.schema import (
    assignment_basis_records,
    assignment_basis_versions,
    case_work_records,
    case_work_result_links,
    case_work_versions,
    practical_role_catalog,
    responsibility_assignment_records,
    responsibility_assignment_versions,
    responsibility_practical_roles,
    responsibility_records,
    responsibility_versions,
)

revision: str = "0010_gate8_responsibility_work"
down_revision: str | Sequence[str] | None = "0009_gate8_common_semantics"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = (
    practical_role_catalog,
    responsibility_records,
    responsibility_versions,
    responsibility_practical_roles,
    assignment_basis_records,
    assignment_basis_versions,
    responsibility_assignment_records,
    responsibility_assignment_versions,
    case_work_records,
    case_work_versions,
    case_work_result_links,
)


def _append_only(name: str) -> None:
    for action in ("UPDATE", "DELETE"):
        op.execute(f"""CREATE TRIGGER prevent_{name}_{action.casefold()}
        BEFORE {action} ON {name} BEGIN
          SELECT RAISE(ABORT, 'Responsibility and Work history is append-only');
        END""")


def upgrade() -> None:
    bind = op.get_bind()
    for table in _TABLES:
        table.create(bind=bind, checkfirst=False)
    op.bulk_insert(
        practical_role_catalog,
        [
            {"role_code": "CASE_COORDINATOR"},
            {"role_code": "ASSESSOR"},
            {"role_code": "REVIEWER"},
        ],
    )
    for table in _TABLES:
        _append_only(table.name)


def downgrade() -> None:
    bind = op.get_bind()
    for table in reversed(_TABLES):
        for action in ("DELETE", "UPDATE"):
            op.execute(f"DROP TRIGGER IF EXISTS prevent_{table.name}_{action.casefold()}")
        table.drop(bind=bind, checkfirst=False)
