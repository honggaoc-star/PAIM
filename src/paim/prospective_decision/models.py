"""Prospective Integration and Decision values for Gate 8 Slice D."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from paim.assessment_review.models import AssessmentLane, CommandIdentity
from paim.integrity.ids import RecordId, RecordVersionId
from paim.integrity.semantics import ExactContextSet, SemanticContractRef
from paim.integrity.time import require_utc


class ProspectiveDecisionStatus(StrEnum):
    PROPOSED = "PROPOSED"
    AUTHORIZED = "AUTHORIZED"


class ProspectiveSelectionKind(StrEnum):
    ONE = "ONE"
    ABSENT = "NOT ESTABLISHED"
    CONFLICT = "CONFLICT — UNRESOLVED"


@dataclass(frozen=True, slots=True)
class ReliedLaneBasis:
    lane: AssessmentLane
    assessment_version_id: RecordVersionId
    readiness_version_id: RecordVersionId
    adequacy_version_id: RecordVersionId
    reliance_version_id: RecordVersionId
    information_basis_version_ids: tuple[RecordVersionId, ...]

    def __post_init__(self) -> None:
        if not self.information_basis_version_ids:
            raise ValueError("relied lane requires exact information/Applicability basis")

    @property
    def version_ids(self) -> tuple[RecordVersionId, ...]:
        return (
            self.assessment_version_id,
            self.readiness_version_id,
            self.adequacy_version_id,
            self.reliance_version_id,
            *self.information_basis_version_ids,
        )


@dataclass(frozen=True, slots=True)
class IntegrationFacts:
    record_id: RecordId
    version_id: RecordVersionId

    @classmethod
    def new(cls, record_id: RecordId | None = None) -> IntegrationFacts:
        return cls(record_id or RecordId.new(), RecordVersionId.new())


@dataclass(frozen=True, slots=True)
class IntegrateValueRiskCommand:
    identity: CommandIdentity
    facts: IntegrationFacts
    contract: SemanticContractRef
    context: ExactContextSet
    case_id: RecordId
    configuration_version_id: RecordVersionId
    decision_use: str
    bounded_scope: str
    value_basis: ReliedLaneBasis
    risk_basis: ReliedLaneBasis
    integration_rationale: str
    material_tensions: tuple[str, ...]
    limitations: tuple[str, ...]
    uncertainty: str
    unresolved_conditions: tuple[str, ...]
    responsibility_version_id: RecordVersionId
    assignment_version_id: RecordVersionId
    authority_source_version_id: RecordVersionId
    expected_integration_version_id: RecordVersionId | None
    effective_at: datetime
    knowledge_cutoff: datetime

    def __post_init__(self) -> None:
        require_utc(self.effective_at)
        require_utc(self.knowledge_cutoff)
        if self.value_basis.lane is not AssessmentLane.VALUE:
            raise ValueError("Value basis must remain in the Value lane")
        if self.risk_basis.lane is not AssessmentLane.RISK:
            raise ValueError("Risk basis must remain in the Risk lane")
        if not all(
            value.strip()
            for value in (
                self.decision_use,
                self.bounded_scope,
                self.integration_rationale,
                self.uncertainty,
            )
        ):
            raise ValueError("bounded Integration meaning is required")


@dataclass(frozen=True, slots=True)
class DecisionFacts:
    record_id: RecordId
    version_id: RecordVersionId

    @classmethod
    def new(cls, record_id: RecordId | None = None) -> DecisionFacts:
        return cls(record_id or RecordId.new(), RecordVersionId.new())


@dataclass(frozen=True, slots=True)
class ProposeDecisionCommand:
    identity: CommandIdentity
    facts: DecisionFacts
    contract: SemanticContractRef
    context: ExactContextSet
    case_id: RecordId
    configuration_version_id: RecordVersionId
    integration_version_id: RecordVersionId
    decision_use: str
    bounded_scope: str
    proposed_action: str
    operating_state: str
    rationale: str
    conditions_and_limits: tuple[str, ...]
    alternatives_considered: tuple[str, ...]
    responsibility_version_id: RecordVersionId
    assignment_version_id: RecordVersionId
    predecessor_decision_version_id: RecordVersionId | None
    expected_current_decision_version_id: RecordVersionId | None
    effective_at: datetime
    knowledge_cutoff: datetime

    def __post_init__(self) -> None:
        require_utc(self.effective_at)
        require_utc(self.knowledge_cutoff)
        if not all(
            value.strip()
            for value in (
                self.decision_use,
                self.bounded_scope,
                self.proposed_action,
                self.operating_state,
                self.rationale,
            )
        ):
            raise ValueError("complete proposed Decision meaning is required")


@dataclass(frozen=True, slots=True)
class AuthorizationFacts:
    decision_version_id: RecordVersionId
    authorization_record_id: RecordId
    authorization_version_id: RecordVersionId

    @classmethod
    def new(cls) -> AuthorizationFacts:
        return cls(RecordVersionId.new(), RecordId.new(), RecordVersionId.new())


@dataclass(frozen=True, slots=True)
class AuthorizeDecisionCommand:
    identity: CommandIdentity
    facts: AuthorizationFacts
    contract: SemanticContractRef
    context: ExactContextSet
    case_id: RecordId
    configuration_version_id: RecordVersionId
    proposal_version_id: RecordVersionId
    integration_version_id: RecordVersionId
    decision_use: str
    bounded_scope: str
    responsibility_version_id: RecordVersionId
    assignment_version_id: RecordVersionId
    authority_source_version_id: RecordVersionId
    authority_identity: str
    authorized_scope: str
    authority_limits: tuple[str, ...]
    conditions: tuple[str, ...]
    dissent: tuple[str, ...]
    effective_at: datetime
    knowledge_cutoff: datetime

    def __post_init__(self) -> None:
        require_utc(self.effective_at)
        require_utc(self.knowledge_cutoff)
        if not self.authority_identity.strip() or not self.authorized_scope.strip():
            raise ValueError("exact Decision authority identity and scope are required")


@dataclass(frozen=True, slots=True)
class ConfirmationFacts:
    record_id: RecordId
    version_id: RecordVersionId

    @classmethod
    def new(cls) -> ConfirmationFacts:
        return cls(RecordId.new(), RecordVersionId.new())


@dataclass(frozen=True, slots=True)
class ConfirmDecisionCommand:
    identity: CommandIdentity
    facts: ConfirmationFacts
    contract: SemanticContractRef
    context: ExactContextSet
    case_id: RecordId
    configuration_version_id: RecordVersionId
    decision_version_id: RecordVersionId
    integration_version_id: RecordVersionId
    decision_use: str
    bounded_scope: str
    rationale: str
    responsibility_version_id: RecordVersionId
    assignment_version_id: RecordVersionId
    authority_source_version_id: RecordVersionId
    effective_at: datetime
    knowledge_cutoff: datetime

    def __post_init__(self) -> None:
        require_utc(self.effective_at)
        require_utc(self.knowledge_cutoff)
        if not self.rationale.strip():
            raise ValueError("unchanged-Decision confirmation rationale is required")


@dataclass(frozen=True, slots=True)
class ProspectiveSelection:
    kind: ProspectiveSelectionKind
    version_ids: tuple[RecordVersionId, ...]
    status: str | None = None
