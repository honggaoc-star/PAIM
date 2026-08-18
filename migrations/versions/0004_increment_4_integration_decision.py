"""Create Increment 4 Integration, Boundary, Decision, and authorization schema.

Revision ID: 0004_increment_4
Revises: 0003_increment_3
"""

from collections.abc import Sequence

from alembic import op

from paim.persistence.sqlite.schema import (
    boundary_clause_records,
    boundary_clause_versions,
    boundary_determination_evidence,
    boundary_determination_records,
    boundary_determination_versions,
    boundary_snapshot_records,
    boundary_snapshot_versions,
    bounded_proceed_boundary_clauses,
    bounded_proceed_records,
    bounded_proceed_versions,
    decision_authority_gaps,
    decision_authority_records,
    decision_authorization_basis_records,
    decision_authorization_basis_versions,
    decision_authorization_delegations,
    decision_authorization_gaps,
    decision_records,
    decision_uncertainty_links,
    decision_versions,
    integration_authority_gaps,
    integration_authority_records,
    integration_material_applicability,
    integration_records,
    integration_versions,
    uncertainty_classification_records,
    uncertainty_classification_versions,
)

revision: str = "0004_increment_4"
down_revision: str | Sequence[str] | None = "0003_increment_3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = (
    integration_records,
    integration_versions,
    integration_material_applicability,
    integration_authority_records,
    integration_authority_gaps,
    uncertainty_classification_records,
    uncertainty_classification_versions,
    boundary_snapshot_records,
    boundary_snapshot_versions,
    boundary_clause_records,
    boundary_clause_versions,
    boundary_determination_records,
    boundary_determination_versions,
    boundary_determination_evidence,
    decision_records,
    decision_versions,
    decision_uncertainty_links,
    decision_authority_records,
    decision_authority_gaps,
    bounded_proceed_records,
    bounded_proceed_versions,
    bounded_proceed_boundary_clauses,
    decision_authorization_basis_records,
    decision_authorization_basis_versions,
    decision_authorization_delegations,
    decision_authorization_gaps,
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
                  SELECT RAISE(ABORT, 'Increment 4 authoritative history is append-only');
                END"""
            )


def downgrade() -> None:
    bind = op.get_bind()
    for table in reversed(_TABLES):
        for action in ("DELETE", "UPDATE"):
            op.execute(f"DROP TRIGGER IF EXISTS prevent_{table.name}_{action.casefold()}")
        table.drop(bind=bind, checkfirst=False)
