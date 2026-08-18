"""Persistence ports for the bounded Increment 5 domain service."""

from __future__ import annotations

from contextlib import AbstractContextManager
from datetime import datetime
from typing import Protocol

from paim.domain.increment4 import PreauthorizedActivationMechanismInput
from paim.domain.increment4_ports import Increment4Store, Increment4Transaction
from paim.domain.increment5 import (
    CompletionAcceptanceDetail,
    CompletionCriterionResult,
    CompletionResultDetail,
    InterventionDetail,
    ObligationDetail,
    ObligationSetDetail,
)
from paim.integrity import RecordId, RecordVersionId


class Increment5Transaction(Increment4Transaction, Protocol):
    def add_preauthorized_activation_mechanisms(
        self,
        *,
        basis_version_id: RecordVersionId,
        mechanisms: tuple[PreauthorizedActivationMechanismInput, ...],
    ) -> None: ...

    def preauthorized_activation_mechanism(
        self,
        *,
        basis_version_id: RecordVersionId,
        mechanism_version_id: RecordVersionId,
    ) -> dict[str, object] | None: ...

    def add_intervention(
        self,
        *,
        intervention_id: RecordId,
        version_id: RecordVersionId,
        case_id: RecordId,
        decision_version_id: RecordVersionId,
        configuration_id: RecordId,
        configuration_version_id: RecordVersionId,
        owner_actor_id: RecordId,
        owner_assignment_version_id: RecordVersionId | None,
        accountable_mechanism: str | None,
        status: str,
    ) -> None: ...

    def intervention_detail(self, version_id: RecordVersionId) -> InterventionDetail | None: ...

    def add_obligation_set(
        self,
        *,
        obligation_set_id: RecordId,
        version_id: RecordVersionId,
        decision_id: RecordId,
        decision_version_id: RecordVersionId,
        case_id: RecordId,
        configuration_id: RecordId,
        configuration_version_id: RecordVersionId,
    ) -> None: ...

    def add_obligation(
        self,
        *,
        obligation_id: RecordId,
        version_id: RecordVersionId,
        obligation_set_version_id: RecordVersionId,
        decision_version_id: RecordVersionId,
        configuration_version_id: RecordVersionId,
        intervention_id: RecordId,
        intervention_version_id: RecordVersionId,
        requirement_type: str,
        post_operation_permitted: bool,
        post_operation_timing_conditions: tuple[str, ...],
    ) -> None: ...

    def obligation_set_detail(self, version_id: RecordVersionId) -> ObligationSetDetail | None: ...

    def obligation_set_versions(
        self,
        *,
        decision_version_id: RecordVersionId,
        configuration_version_id: RecordVersionId,
    ) -> tuple[RecordVersionId, ...]: ...

    def obligation_detail(self, version_id: RecordVersionId) -> ObligationDetail | None: ...

    def add_completion_result(
        self,
        *,
        result_id: RecordId,
        version_id: RecordVersionId,
        obligation_version_id: RecordVersionId,
        intervention_version_id: RecordVersionId,
        decision_version_id: RecordVersionId,
        configuration_version_id: RecordVersionId,
        criteria: tuple[CompletionCriterionResult, ...],
        evidence_version_ids: tuple[RecordVersionId, ...],
        performer_actor_id: RecordId,
    ) -> None: ...

    def completion_result_detail(
        self, version_id: RecordVersionId
    ) -> CompletionResultDetail | None: ...

    def completion_result_versions(
        self, *, obligation_version_id: RecordVersionId
    ) -> tuple[RecordVersionId, ...]: ...

    def add_completion_acceptor_mechanism(
        self,
        *,
        mechanism_id: RecordId,
        version_id: RecordVersionId,
        case_id: RecordId,
        intervention_id: RecordId,
        intervention_version_id: RecordVersionId,
        decision_version_id: RecordVersionId,
        configuration_id: RecordId,
        configuration_version_id: RecordVersionId,
        accountable_actor_id: RecordId,
        rule_version: str,
        authority_scope: str,
        authority_source: str,
    ) -> None: ...

    def completion_acceptor_mechanism_detail(
        self, version_id: RecordVersionId
    ) -> dict[str, object] | None: ...

    def completion_acceptor_mechanism_versions(
        self,
        *,
        case_id: RecordId,
        intervention_id: RecordId,
        decision_version_id: RecordVersionId,
        configuration_id: RecordId,
        configuration_version_id: RecordVersionId,
    ) -> tuple[RecordVersionId, ...]: ...

    def add_completion_acceptance(
        self,
        *,
        acceptance_id: RecordId,
        version_id: RecordVersionId,
        obligation_version_id: RecordVersionId,
        intervention_version_id: RecordVersionId,
        completion_result_version_id: RecordVersionId,
        decision_version_id: RecordVersionId,
        configuration_version_id: RecordVersionId,
        outcome: str,
        status: str,
        accountable_actor_id: RecordId,
        accountable_assignment_version_id: RecordVersionId | None,
        accountable_mechanism_version_id: RecordVersionId | None,
        delegation_chain_version_ids: tuple[RecordVersionId, ...],
    ) -> None: ...

    def completion_acceptance_detail(
        self, version_id: RecordVersionId
    ) -> CompletionAcceptanceDetail | None: ...

    def completion_acceptance_versions(
        self, *, obligation_version_id: RecordVersionId
    ) -> tuple[RecordVersionId, ...]: ...

    def add_replacement(
        self,
        *,
        replacement_id: RecordId,
        version_id: RecordVersionId,
        obligation_version_id: RecordVersionId,
        predecessor_intervention_version_id: RecordVersionId,
        replacement_intervention_version_id: RecordVersionId,
        substantive_change: bool,
        successor_decision_version_id: RecordVersionId | None,
    ) -> None: ...

    def replacement_versions(
        self, *, obligation_version_id: RecordVersionId
    ) -> tuple[RecordVersionId, ...]: ...

    def replacement_detail(self, version_id: RecordVersionId) -> dict[str, object] | None: ...

    def add_continued_validity_mechanism(
        self,
        *,
        mechanism_id: RecordId,
        version_id: RecordVersionId,
        successor_obligation_version_id: RecordVersionId,
        case_id: RecordId,
        intervention_id: RecordId,
        intervention_version_id: RecordVersionId,
        decision_version_id: RecordVersionId,
        configuration_id: RecordId,
        configuration_version_id: RecordVersionId,
        accountable_actor_id: RecordId,
        rule_version: str,
        authority_scope: str,
        authority_source: str,
    ) -> None: ...

    def continued_validity_mechanism_detail(
        self, version_id: RecordVersionId
    ) -> dict[str, object] | None: ...

    def continued_validity_mechanism_versions(
        self, *, successor_obligation_version_id: RecordVersionId
    ) -> tuple[RecordVersionId, ...]: ...

    def add_reuse_determination(
        self,
        *,
        determination_id: RecordId,
        version_id: RecordVersionId,
        successor_obligation_version_id: RecordVersionId,
        prior_completion_result_version_id: RecordVersionId,
        prior_acceptance_version_id: RecordVersionId,
        accountable_actor_id: RecordId,
        accountable_assignment_version_id: RecordVersionId | None,
        accountable_mechanism_version_id: RecordVersionId | None,
        delegation_chain_version_ids: tuple[RecordVersionId, ...],
        all_coverage_established: bool,
    ) -> None: ...

    def reuse_determination_versions(
        self, *, successor_obligation_version_id: RecordVersionId
    ) -> tuple[RecordVersionId, ...]: ...

    def reuse_determination_detail(
        self, version_id: RecordVersionId
    ) -> dict[str, object] | None: ...

    def add_prerequisite_evaluation_basis(
        self,
        *,
        basis_id: RecordId,
        version_id: RecordVersionId,
        decision_version_id: RecordVersionId,
        configuration_version_id: RecordVersionId,
        boundary_snapshot_version_id: RecordVersionId,
        obligation_set_version_id: RecordVersionId,
        aggregate_result: str,
        effective_at: datetime,
        knowledge_cutoff: datetime,
    ) -> None: ...

    def add_prerequisite_basis_item(
        self,
        *,
        basis_version_id: RecordVersionId,
        ordinal: int,
        obligation_version_id: RecordVersionId,
        intervention_version_id: RecordVersionId | None,
        completion_result_version_id: RecordVersionId | None,
        completion_acceptance_version_id: RecordVersionId | None,
        replacement_version_id: RecordVersionId | None,
        reuse_determination_version_id: RecordVersionId | None,
        result: str,
        diagnostics: tuple[str, ...],
    ) -> None: ...

    def add_activation_authorization(
        self,
        *,
        authorization_id: RecordId,
        version_id: RecordVersionId,
        decision_version_id: RecordVersionId,
        configuration_version_id: RecordVersionId,
        operating_state: str,
        boundary_snapshot_version_id: RecordVersionId,
        prerequisite_basis_version_id: RecordVersionId,
        authority_kind: str,
        authority_actor_id: RecordId | None,
        authority_assignment_version_id: RecordVersionId | None,
        mechanism_version_id: RecordVersionId | None,
        decision_authorization_basis_version_id: RecordVersionId,
        authority_scope: str,
        authority_limits: tuple[str, ...],
        authority_effective_from: datetime,
        authority_effective_to: datetime | None,
        delegation_chain_version_ids: tuple[RecordVersionId, ...],
        activation_effective_at: datetime,
    ) -> None: ...

    def add_target_activation_event(
        self,
        *,
        event_id: str,
        case_id: RecordId,
        decision_version_id: RecordVersionId,
        configuration_version_id: RecordVersionId,
        boundary_snapshot_version_id: RecordVersionId,
        prerequisite_basis_version_id: RecordVersionId,
        activation_authorization_version_id: RecordVersionId,
        operating_state: str,
        lifecycle_event_id: str,
        effective_at: datetime,
        recorded_at: datetime,
        knowledge_cutoff: datetime,
    ) -> None: ...

    def add_learning_item(
        self,
        *,
        learning_item_id: RecordId,
        version_id: RecordVersionId,
        case_id: RecordId,
        decision_version_id: RecordVersionId,
        configuration_id: RecordId,
        configuration_version_id: RecordVersionId,
        uncertainty_version_id: RecordVersionId,
        owner_actor_id: RecordId,
        owner_assignment_version_id: RecordVersionId | None,
        accountable_mechanism: str | None,
        status: str,
        evidence_version_ids: tuple[RecordVersionId, ...],
        successor_decision_version_id: RecordVersionId | None,
    ) -> None: ...


class Increment5Store(Increment4Store, Protocol):
    def semantic_transaction(self) -> AbstractContextManager[Increment5Transaction]: ...

    def read_transaction(self) -> AbstractContextManager[Increment5Transaction]: ...
