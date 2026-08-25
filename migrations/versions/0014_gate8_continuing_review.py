"""Add prospective continuing-review persistence.

Revision ID: 0014_gate8_continuing_review
Revises: 0013_gate8_integration_decision_basis
"""

from collections.abc import Sequence

from alembic import op

from paim.persistence.sqlite.schema import (
    planned_review_point_records,
    planned_review_point_versions,
    required_review_constraint_records,
    required_review_constraint_versions,
    review_attention_event_records,
    review_attention_event_versions,
    review_episode_records,
    review_episode_result_links,
    review_episode_versions,
)

revision: str = "0014_gate8_continuing_review"
down_revision: str | Sequence[str] | None = "0013_gate8_integration_decision_basis"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = (
    planned_review_point_records,
    required_review_constraint_records,
    review_attention_event_records,
    review_episode_records,
    planned_review_point_versions,
    required_review_constraint_versions,
    review_attention_event_versions,
    review_episode_versions,
    review_episode_result_links,
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
                  SELECT RAISE(ABORT, 'prospective continuing-review history is append-only');
                END"""
            )


def downgrade() -> None:
    bind = op.get_bind()
    if any(
        bind.exec_driver_sql(f"SELECT COUNT(*) FROM {table.name}").scalar_one() for table in _TABLES
    ):
        raise RuntimeError(
            "0014 contains prospective continuing-review facts; destructive rollback is prohibited"
        )
    for table in reversed(_TABLES):
        for action in ("DELETE", "UPDATE"):
            op.execute(f"DROP TRIGGER IF EXISTS prevent_{table.name}_{action.casefold()}")
        table.drop(bind=bind, checkfirst=False)
