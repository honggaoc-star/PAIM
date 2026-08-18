"""Create Increment 3 Evidence, Authority, Applicability, and analytical-lane schema.

Revision ID: 0003_increment_3
Revises: 0002_increment_2
"""

from collections.abc import Sequence

from alembic import op

from paim.persistence.sqlite.schema import (
    affected_use_references,
    analytical_input_versions,
    analytical_inputs,
    authority_gap_versions,
    authority_gaps,
    authority_record_versions,
    authority_records,
    candidate_disposition_versions,
    candidate_dispositions,
    evidence_applicability_records,
    evidence_applicability_versions,
    evidence_records,
    evidence_versions,
    exact_evidence_links,
    input_acceptance_records,
    input_acceptance_versions,
    lane_fitness_records,
    lane_fitness_versions,
    material_evidence_basis,
)

revision: str = "0003_increment_3"
down_revision: str | Sequence[str] | None = "0002_increment_2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = (
    evidence_records,
    evidence_versions,
    authority_records,
    authority_record_versions,
    authority_gaps,
    authority_gap_versions,
    exact_evidence_links,
    affected_use_references,
    evidence_applicability_records,
    analytical_inputs,
    analytical_input_versions,
    evidence_applicability_versions,
    candidate_dispositions,
    candidate_disposition_versions,
    lane_fitness_records,
    lane_fitness_versions,
    material_evidence_basis,
    input_acceptance_records,
    input_acceptance_versions,
)


def upgrade() -> None:
    bind = op.get_bind()
    for table in _TABLES:
        table.create(bind=bind, checkfirst=False)

    for table in _TABLES:
        for action in ("UPDATE", "DELETE"):
            trigger = f"prevent_{table.name}_{action.casefold()}"
            op.execute(
                f"""CREATE TRIGGER {trigger}
                BEFORE {action} ON {table.name}
                BEGIN
                  SELECT RAISE(ABORT, 'Increment 3 authoritative history is append-only');
                END"""
            )


def downgrade() -> None:
    bind = op.get_bind()
    for table in reversed(_TABLES):
        for action in ("DELETE", "UPDATE"):
            op.execute(f"DROP TRIGGER IF EXISTS prevent_{table.name}_{action.casefold()}")
        table.drop(bind=bind, checkfirst=False)
