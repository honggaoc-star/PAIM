"""Add durable public Case numbers.

Revision ID: 0018_issue167_case_identity
Revises: 0017_gate8_slice_h0_prerequisites
"""

from collections.abc import Sequence

from alembic import op

from paim.persistence.sqlite.schema import case_number_allocations

revision: str = "0018_issue167_case_identity"
down_revision: str | Sequence[str] | None = "0017_gate8_slice_h0_prerequisites"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    case_number_allocations.create(bind=bind, checkfirst=False)
    case_ids = tuple(
        bind.exec_driver_sql("SELECT case_id FROM paim_cases ORDER BY rowid, case_id").scalars()
    )
    for sequence, case_id in enumerate(case_ids, start=1):
        bind.exec_driver_sql(
            "INSERT INTO case_number_allocations "
            "(sequence_number, case_id, case_number) VALUES (?, ?, ?)",
            (sequence, case_id, f"PAIM-{sequence:04d}"),
        )
    for action in ("UPDATE", "DELETE"):
        op.execute(
            f"""CREATE TRIGGER prevent_case_number_allocations_{action.casefold()}
            BEFORE {action} ON case_number_allocations BEGIN
              SELECT RAISE(ABORT, 'Case-number history is immutable');
            END"""
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.exec_driver_sql("SELECT COUNT(*) FROM case_number_allocations").scalar_one():
        raise RuntimeError("durable Case numbers exist; destructive rollback is prohibited")
    for action in ("DELETE", "UPDATE"):
        op.execute(f"DROP TRIGGER IF EXISTS prevent_case_number_allocations_{action.casefold()}")
    case_number_allocations.drop(bind=bind, checkfirst=False)
