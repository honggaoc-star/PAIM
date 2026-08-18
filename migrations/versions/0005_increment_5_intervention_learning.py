"""Create Increment 5 Intervention, activation, and Learning schema.

Revision ID: 0005_increment_5
Revises: 0004_increment_4
"""

from collections.abc import Sequence

from alembic import op

from paim.persistence.sqlite.schema import (
    activation_authorization_delegations,
    activation_authorization_records,
    activation_authorization_versions,
    completion_acceptance_delegations,
    completion_acceptance_records,
    completion_acceptance_versions,
    completion_acceptor_mechanism_records,
    completion_acceptor_mechanism_versions,
    completion_result_criteria,
    completion_result_evidence,
    completion_result_records,
    completion_result_versions,
    continued_validity_delegations,
    continued_validity_mechanism_records,
    continued_validity_mechanism_versions,
    continued_validity_records,
    continued_validity_versions,
    decision_preauthorized_activation_mechanisms,
    intervention_records,
    intervention_replacement_records,
    intervention_replacement_versions,
    intervention_versions,
    learning_item_evidence,
    learning_item_records,
    learning_item_versions,
    obligation_records,
    obligation_set_records,
    obligation_set_versions,
    obligation_versions,
    prerequisite_evaluation_basis_items,
    prerequisite_evaluation_basis_records,
    prerequisite_evaluation_basis_versions,
    target_activation_events,
)

revision: str = "0005_increment_5"
down_revision: str | Sequence[str] | None = "0004_increment_4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = (
    decision_preauthorized_activation_mechanisms,
    intervention_records,
    intervention_versions,
    obligation_set_records,
    obligation_set_versions,
    obligation_records,
    obligation_versions,
    completion_result_records,
    completion_result_versions,
    completion_result_criteria,
    completion_result_evidence,
    completion_acceptor_mechanism_records,
    completion_acceptor_mechanism_versions,
    completion_acceptance_records,
    completion_acceptance_versions,
    completion_acceptance_delegations,
    intervention_replacement_records,
    intervention_replacement_versions,
    continued_validity_mechanism_records,
    continued_validity_mechanism_versions,
    continued_validity_records,
    continued_validity_versions,
    continued_validity_delegations,
    prerequisite_evaluation_basis_records,
    prerequisite_evaluation_basis_versions,
    prerequisite_evaluation_basis_items,
    activation_authorization_records,
    activation_authorization_versions,
    activation_authorization_delegations,
    target_activation_events,
    learning_item_records,
    learning_item_versions,
    learning_item_evidence,
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
                  SELECT RAISE(ABORT, 'Increment 5 authoritative history is append-only');
                END"""
            )


def downgrade() -> None:
    bind = op.get_bind()
    for table in reversed(_TABLES):
        for action in ("DELETE", "UPDATE"):
            op.execute(f"DROP TRIGGER IF EXISTS prevent_{table.name}_{action.casefold()}")
        table.drop(bind=bind, checkfirst=False)
