"""Persistence ports for the bounded Increment 4 domain service."""

from __future__ import annotations

from contextlib import AbstractContextManager
from datetime import datetime
from typing import Protocol

from paim.domain.increment3_ports import Increment3Store, Increment3Transaction
from paim.domain.increment4 import (
    AuthorizationBasisDetail,
    BoundaryClauseInput,
    BoundarySnapshotDetail,
    DecisionDetail,
    IntegrationDetail,
)
from paim.integrity import RecordId, RecordVersionId


class Increment4Transaction(Increment3Transaction, Protocol):
    def add_integration(
        self,
        *,
        integration_id: RecordId,
        version_id: RecordVersionId,
        case_id: RecordId,
        configuration_id: RecordId,
        configuration_version_id: RecordVersionId,
        use_context: str,
        purpose: str,
        value_input_version_id: RecordVersionId,
        value_acceptance_version_id: RecordVersionId,
        value_fitness_version_id: RecordVersionId,
        risk_input_version_id: RecordVersionId,
        risk_acceptance_version_id: RecordVersionId,
        risk_fitness_version_id: RecordVersionId,
        integrator_actor_id: RecordId,
        owner_assignment_version_id: RecordVersionId | None,
        accountable_mechanism: str | None,
        status: str,
        material_applicability_version_ids: tuple[RecordVersionId, ...],
        authority_record_version_ids: tuple[RecordVersionId, ...],
        authority_gap_version_ids: tuple[RecordVersionId, ...],
    ) -> None: ...

    def integration_detail(self, version_id: RecordVersionId) -> IntegrationDetail | None: ...

    def integration_versions_for_context(
        self, *, case_id: RecordId, configuration_version_id: RecordVersionId
    ) -> tuple[RecordVersionId, ...]: ...

    def add_uncertainty_classification(
        self,
        *,
        classification_id: RecordId,
        version_id: RecordVersionId,
        integration_version_id: RecordVersionId,
        proposed_decision_context: str,
        proposed_operating_state: str,
        source_reference: str,
        source_input_version_id: RecordVersionId | None,
        source_evidence_version_id: RecordVersionId | None,
        classification: str,
        accountable_assignment_version_id: RecordVersionId | None,
        accountable_mechanism: str | None,
    ) -> None: ...

    def add_boundary_snapshot(
        self,
        *,
        snapshot_id: RecordId,
        version_id: RecordVersionId,
        case_id: RecordId,
        configuration_id: RecordId,
        configuration_version_id: RecordVersionId,
        integration_id: RecordId,
        integration_version_id: RecordVersionId,
        owner_actor_id: RecordId,
        status: str,
        clauses: tuple[BoundaryClauseInput, ...],
        recorded_at: datetime,
        effective_at: datetime,
    ) -> None: ...

    def boundary_snapshot_detail(
        self, version_id: RecordVersionId
    ) -> BoundarySnapshotDetail | None: ...

    def add_boundary_determination(
        self,
        *,
        determination_id: RecordId,
        version_id: RecordVersionId,
        snapshot_version_id: RecordVersionId,
        clause_id: RecordId,
        clause_version_id: RecordVersionId,
        outcome: str,
        actor_id: RecordId,
        accountable_assignment_version_id: RecordVersionId | None,
        accountable_mechanism: str | None,
        evidence_version_ids: tuple[RecordVersionId, ...],
    ) -> None: ...

    def current_boundary_determination(
        self,
        *,
        snapshot_version_id: RecordVersionId,
        clause_version_id: RecordVersionId,
        effective_at: datetime,
        known_at: datetime,
    ) -> tuple[RecordVersionId, str] | None: ...

    def add_decision(
        self,
        *,
        decision_id: RecordId,
        version_id: RecordVersionId,
        case_id: RecordId,
        configuration_id: RecordId,
        configuration_version_id: RecordVersionId,
        integration_id: RecordId,
        integration_version_id: RecordVersionId,
        boundary_snapshot_id: RecordId,
        boundary_snapshot_version_id: RecordVersionId,
        proposed_action: str,
        operating_state: str,
        status: str,
        accepted_uncertainty_version_ids: tuple[RecordVersionId, ...],
        decision_limiting_uncertainty_version_ids: tuple[RecordVersionId, ...],
        authority_record_version_ids: tuple[RecordVersionId, ...],
        authority_gap_version_ids: tuple[RecordVersionId, ...],
    ) -> None: ...

    def decision_detail(self, version_id: RecordVersionId) -> DecisionDetail | None: ...

    def decision_versions(
        self, *, case_id: RecordId, configuration_version_id: RecordVersionId
    ) -> tuple[RecordVersionId, ...]: ...

    def add_bounded_proceed(
        self,
        *,
        determination_id: RecordId,
        version_id: RecordVersionId,
        decision_version_id: RecordVersionId,
        unresolved_gap_version_id: RecordVersionId,
        blocked_broader_decision: str,
        narrower_scope: str,
        boundary_clause_version_ids: tuple[RecordVersionId, ...],
        operating_state: str,
        actor_id: RecordId,
        authority_assignment_version_id: RecordVersionId | None,
        authority_mechanism: str | None,
    ) -> None: ...

    def bounded_proceed_detail(self, version_id: RecordVersionId) -> dict[str, str] | None: ...

    def add_authorization_basis(
        self,
        *,
        basis_id: RecordId,
        version_id: RecordVersionId,
        decision_version_id: RecordVersionId,
        decision_authority_identity: str,
        authority_assignment_version_id: RecordVersionId | None,
        authority_mechanism: str | None,
        authority_record_version_id: RecordVersionId | None,
        delegation_chain_version_ids: tuple[RecordVersionId, ...],
        authorized_scope: str,
        configuration_id: RecordId,
        configuration_version_id: RecordVersionId,
        operating_state_coverage: tuple[str, ...],
        decision_type: str,
        organizational_unit: str | None,
        authorization_event_id: str,
        authorization_actor_id: RecordId,
        authorization_effective_at: datetime,
        authority_gap_version_ids: tuple[RecordVersionId, ...],
        bounded_proceed_version_id: RecordVersionId | None,
    ) -> None: ...

    def authorization_basis_detail(
        self, version_id: RecordVersionId
    ) -> AuthorizationBasisDetail | None: ...

    def authorization_basis_versions(
        self, *, decision_version_id: RecordVersionId
    ) -> tuple[RecordVersionId, ...]: ...

    def authority_record_scope(self, version_id: RecordVersionId) -> str | None: ...


class Increment4Store(Increment3Store, Protocol):
    def semantic_transaction(self) -> AbstractContextManager[Increment4Transaction]: ...

    def read_transaction(self) -> AbstractContextManager[Increment4Transaction]: ...
