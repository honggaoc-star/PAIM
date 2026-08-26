"""Add measured dual-time reconstruction query support.

Revision ID: 0016_gate8_reconstruction_support
Revises: 0015_gate8_quantitative_claims
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0016_gate8_reconstruction_support"
down_revision: str | Sequence[str] | None = "0015_gate8_quantitative_claims"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_INDEX = "ix_versions_reconstruction_cutoff"


def upgrade() -> None:
    op.create_index(
        _INDEX,
        "record_versions",
        ("recorded_at_us", "effective_from_us", "record_id"),
        unique=False,
    )


def downgrade() -> None:
    # This migration contains query support only. Dropping the index cannot
    # destroy or reinterpret any authoritative fact.
    op.drop_index(_INDEX, table_name="record_versions")
