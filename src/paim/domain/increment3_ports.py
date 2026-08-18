"""Persistence ports required by the bounded Increment 3 domain service."""

from __future__ import annotations

from contextlib import AbstractContextManager
from datetime import datetime
from typing import Protocol

from paim.domain.increment3 import (
    AcceptanceSelectionDetail,
    AnalyticalInputDetail,
    ApplicabilityTargetType,
    EvidenceApplicabilityDetail,
    LaneFitnessDetail,
    MaterialEvidenceBasisInput,
)
from paim.domain.ports import Increment2Transaction
from paim.integrity import RecordId, RecordVersionId


class Increment3Transaction(Increment2Transaction, Protocol):
    def add_evidence(
        self,
        *,
        evidence_id: RecordId,
        version_id: RecordVersionId,
        case_id: RecordId | None,
        configuration_id: RecordId | None,
        configuration_version_id: RecordVersionId | None,
        classification: str,
        source: str,
        provenance_json: str,
        observed_at_us: int | None,
        attention: str,
    ) -> None: ...

    def add_authority_record(
        self,
        *,
        authority_id: RecordId,
        version_id: RecordVersionId,
        case_id: RecordId | None,
        configuration_id: RecordId | None,
        configuration_version_id: RecordVersionId | None,
        category: str,
        source: str,
        provenance_json: str,
        authority_scope: str,
        requirement: str,
    ) -> None: ...

    def add_authority_gap(
        self,
        *,
        gap_id: RecordId,
        version_id: RecordVersionId,
        case_id: RecordId,
        configuration_id: RecordId,
        configuration_version_id: RecordVersionId,
        question_id: str,
        question: str,
        authority_scope: str,
        rationale: str,
        provenance_json: str,
    ) -> None: ...

    def add_exact_evidence_link(
        self,
        *,
        source_version_id: RecordVersionId,
        evidence_version_id: RecordVersionId,
        link_role: str,
    ) -> None: ...

    def add_affected_use_reference(
        self, *, source_version_id: RecordVersionId, use_reference: str
    ) -> None: ...

    def add_evidence_applicability(
        self,
        *,
        applicability_id: RecordId,
        version_id: RecordVersionId,
        evidence_version_id: RecordVersionId,
        target_type: str,
        target_id: str,
        target_version_id: RecordVersionId | None,
        purpose: str,
        assessed_scope: str,
        case_id: RecordId | None,
        configuration_id: RecordId | None,
        configuration_version_id: RecordVersionId | None,
        outcome: str,
        conditions_json: str,
        limitations_json: str,
        rationale: str,
        assessor_actor_id: RecordId,
        accountable_assignment_version_id: RecordVersionId | None,
        accountable_mechanism: str | None,
    ) -> None: ...

    def evidence_applicability_detail(
        self, version_id: RecordVersionId
    ) -> EvidenceApplicabilityDetail | None: ...

    def add_analytical_input(
        self,
        *,
        input_id: RecordId,
        version_id: RecordVersionId,
        lane: str,
        case_id: RecordId,
        configuration_id: RecordId,
        configuration_version_id: RecordVersionId,
        purpose: str,
        finding: str,
        boundary: str,
        uncertainties_json: str,
        implication: str,
        provenance_json: str,
    ) -> None: ...

    def analytical_input_detail(
        self, version_id: RecordVersionId
    ) -> AnalyticalInputDetail | None: ...

    def analytical_input_versions(
        self,
        *,
        lane: str,
        configuration_version_id: RecordVersionId,
        purpose: str,
    ) -> tuple[RecordVersionId, ...]: ...

    def add_candidate_disposition(
        self,
        *,
        disposition_id: RecordId,
        version_id: RecordVersionId,
        input_version_id: RecordVersionId,
        lane: str,
        configuration_version_id: RecordVersionId,
        use_context: str,
        purpose: str,
        disposition: str,
        rationale: str,
        accountable_assignment_version_id: RecordVersionId | None,
        accountable_mechanism: str | None,
    ) -> None: ...

    def candidate_has_disposition(
        self,
        *,
        input_version_id: RecordVersionId,
        lane: str,
        configuration_version_id: RecordVersionId,
        use_context: str,
        purpose: str,
        effective_at: datetime,
        known_at: datetime,
    ) -> bool: ...

    def add_lane_fitness(
        self,
        *,
        fitness_id: RecordId,
        version_id: RecordVersionId,
        lane: str,
        input_version_id: RecordVersionId,
        case_id: RecordId,
        configuration_id: RecordId,
        configuration_version_id: RecordVersionId,
        use_context: str,
        purpose: str,
        outcome: str,
        rationale: str,
        indeterminate_treatment: str | None,
        decision_limiting: bool,
        accountable_assignment_version_id: RecordVersionId | None,
        accountable_mechanism: str | None,
        material_evidence: tuple[MaterialEvidenceBasisInput, ...],
    ) -> None: ...

    def lane_fitness_detail(self, version_id: RecordVersionId) -> LaneFitnessDetail | None: ...

    def material_evidence_basis(
        self, fitness_version_id: RecordVersionId
    ) -> tuple[MaterialEvidenceBasisInput, ...]: ...

    def add_acceptance_selection(
        self,
        *,
        acceptance_id: RecordId,
        version_id: RecordVersionId,
        lane: str,
        input_version_id: RecordVersionId,
        case_id: RecordId,
        configuration_id: RecordId,
        configuration_version_id: RecordVersionId,
        use_context: str,
        purpose: str,
        rationale: str,
        accountable_assignment_version_id: RecordVersionId | None,
        accountable_mechanism: str | None,
        fitness_version_id: RecordVersionId,
    ) -> None: ...

    def acceptance_selection_detail(
        self, version_id: RecordVersionId
    ) -> AcceptanceSelectionDetail | None: ...

    def version_statuses(
        self,
        *,
        version_id: RecordVersionId,
        effective_at: datetime,
        known_at: datetime,
    ) -> tuple[str, ...]: ...

    def evidence_attention(self, version_id: RecordVersionId) -> str | None: ...

    def current_authority_gap_versions(
        self,
        *,
        case_id: RecordId,
        configuration_version_id: RecordVersionId,
        effective_at: datetime,
        known_at: datetime,
    ) -> tuple[RecordVersionId, ...]: ...

    def exact_target_exists(
        self,
        *,
        target_type: ApplicabilityTargetType,
        target_id: str,
        target_version_id: RecordVersionId | None,
    ) -> bool: ...


class Increment3Store(Protocol):
    def semantic_transaction(self) -> AbstractContextManager[Increment3Transaction]: ...

    def read_transaction(self) -> AbstractContextManager[Increment3Transaction]: ...
