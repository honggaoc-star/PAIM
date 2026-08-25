"""Add prospective semantic contracts and exact contexts.

Revision ID: 0009_gate8_common_semantics
Revises: 0008_increment_8
"""

from collections.abc import Sequence

from alembic import op

from paim.persistence.sqlite.schema import (
    exact_context_members,
    exact_context_sets,
    record_version_semantics,
    semantic_consumer_cutover_versions,
    semantic_contract_adapters,
    semantic_contract_families,
    semantic_contract_successors,
    semantic_contracts,
    status_event_semantics,
    version_relationship_semantics,
)

revision: str = "0009_gate8_common_semantics"
down_revision: str | Sequence[str] | None = "0008_increment_8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = (
    semantic_contracts,
    semantic_contract_families,
    semantic_contract_adapters,
    semantic_contract_successors,
    exact_context_sets,
    exact_context_members,
    record_version_semantics,
    status_event_semantics,
    version_relationship_semantics,
    semantic_consumer_cutover_versions,
)


def _append_only(name: str) -> None:
    for action in ("UPDATE", "DELETE"):
        op.execute(f"""CREATE TRIGGER prevent_{name}_{action.casefold()}
        BEFORE {action} ON {name} BEGIN
          SELECT RAISE(ABORT, 'prospective semantic history is append-only');
        END""")


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
