"""Prospective independent Value/Risk assessment review values for Gate 8 Slice C."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from paim.integrity.ids import CommandId, RecordId, RecordVersionId
from paim.integrity.semantics import ExactContextSet, SemanticContractRef
from paim.integrity.time import require_utc


class AssessmentLane(StrEnum):
    VALUE = "VALUE"
    RISK = "RISK"


class AdequacyOutcome(StrEnum):
    ADEQUATE = "ADEQUATE"
    NOT_ADEQUATE = "NOT_ADEQUATE"
    INDETERMINATE = "INDETERMINATE"


class ReviewSelectionKind(StrEnum):
    ONE = "ONE"
    ABSENT = "NOT ESTABLISHED"
    CONFLICT = "CONFLICT — UNRESOLVED"


@dataclass(frozen=True, slots=True)
class AssessmentContent:
    finding: str
    boundary: str
    uncertainty: str
    implication: str
    provenance: str

    def __post_init__(self) -> None:
        if any(not value.strip() for value in self.values()):
            raise ValueError("complete five-part assessment content is required")

    def values(self) -> tuple[str, ...]:
        return (
            self.finding,
            self.boundary,
            self.uncertainty,
            self.implication,
            self.provenance,
        )

    def as_dict(self) -> dict[str, str]:
        return dict(
            finding=self.finding,
            boundary=self.boundary,
            uncertainty=self.uncertainty,
            implication=self.implication,
            provenance=self.provenance,
        )


@dataclass(frozen=True, slots=True)
class CommandIdentity:
    command_id: CommandId
    idempotency_scope: str
    idempotency_key: str
    principal_id: str
    actor_id: RecordId


@dataclass(frozen=True, slots=True)
class FinishFacts:
    assessment_record_id: RecordId
    assessment_version_id: RecordVersionId
    readiness_record_id: RecordId
    readiness_version_id: RecordVersionId

    @classmethod
    def new(cls, assessment_record_id: RecordId | None = None) -> FinishFacts:
        return cls(
            assessment_record_id or RecordId.new(),
            RecordVersionId.new(),
            RecordId.new(),
            RecordVersionId.new(),
        )


@dataclass(frozen=True, slots=True)
class FinishAssessmentCommand:
    identity: CommandIdentity
    facts: FinishFacts
    contract: SemanticContractRef
    context: ExactContextSet
    lane: AssessmentLane
    case_id: RecordId
    configuration_version_id: RecordVersionId
    content: AssessmentContent
    decision_use: str
    assessed_scope: str
    information_basis_version_ids: tuple[RecordVersionId, ...]
    responsibility_version_id: RecordVersionId
    assignment_version_id: RecordVersionId
    expected_assessment_version_id: RecordVersionId | None
    rationale: str
    limitations: tuple[str, ...]
    effective_at: datetime
    knowledge_cutoff: datetime

    def __post_init__(self) -> None:
        require_utc(self.effective_at)
        require_utc(self.knowledge_cutoff)
        if not self.decision_use.strip() or not self.assessed_scope.strip():
            raise ValueError("bounded decision use and assessed scope are required")
        if not self.information_basis_version_ids:
            raise ValueError("exact information/Applicability basis is required")


@dataclass(frozen=True, slots=True)
class AdequacyFacts:
    record_id: RecordId
    version_id: RecordVersionId

    @classmethod
    def new(cls, record_id: RecordId | None = None) -> AdequacyFacts:
        return cls(record_id or RecordId.new(), RecordVersionId.new())


@dataclass(frozen=True, slots=True)
class DetermineAdequacyCommand:
    identity: CommandIdentity
    facts: AdequacyFacts
    contract: SemanticContractRef
    context: ExactContextSet
    lane: AssessmentLane
    case_id: RecordId
    configuration_version_id: RecordVersionId
    assessment_version_id: RecordVersionId
    readiness_version_id: RecordVersionId
    decision_use: str
    assessed_scope: str
    information_basis_version_ids: tuple[RecordVersionId, ...]
    outcome: AdequacyOutcome
    material_reasons: tuple[str, ...]
    rationale: str
    limitations: tuple[str, ...]
    uncertainty: str
    responsibility_version_id: RecordVersionId
    assignment_version_id: RecordVersionId
    expected_adequacy_version_id: RecordVersionId | None
    effective_at: datetime
    knowledge_cutoff: datetime

    def __post_init__(self) -> None:
        require_utc(self.effective_at)
        require_utc(self.knowledge_cutoff)
        if not self.rationale.strip():
            raise ValueError("neutral adequacy rationale is required")
        if self.outcome is not AdequacyOutcome.ADEQUATE and not self.material_reasons:
            raise ValueError("adverse or indeterminate adequacy requires material reasons")


@dataclass(frozen=True, slots=True)
class CandidateDisposition:
    assessment_version_id: RecordVersionId
    disposition: str
    rationale: str

    def __post_init__(self) -> None:
        if not self.disposition.strip() or not self.rationale.strip():
            raise ValueError("material candidate disposition and rationale are required")


@dataclass(frozen=True, slots=True)
class RelianceFacts:
    record_id: RecordId
    version_id: RecordVersionId

    @classmethod
    def new(cls, record_id: RecordId | None = None) -> RelianceFacts:
        return cls(record_id or RecordId.new(), RecordVersionId.new())


@dataclass(frozen=True, slots=True)
class DesignateRelianceCommand:
    identity: CommandIdentity
    facts: RelianceFacts
    contract: SemanticContractRef
    context: ExactContextSet
    lane: AssessmentLane
    case_id: RecordId
    configuration_version_id: RecordVersionId
    assessment_version_id: RecordVersionId
    readiness_version_id: RecordVersionId
    adequacy_version_id: RecordVersionId
    decision_use: str
    assessed_scope: str
    information_basis_version_ids: tuple[RecordVersionId, ...]
    candidate_dispositions: tuple[CandidateDisposition, ...]
    rationale: str
    responsibility_version_id: RecordVersionId
    assignment_version_id: RecordVersionId
    expected_reliance_version_id: RecordVersionId | None
    effective_at: datetime
    knowledge_cutoff: datetime

    def __post_init__(self) -> None:
        require_utc(self.effective_at)
        require_utc(self.knowledge_cutoff)
        if not self.rationale.strip():
            raise ValueError("explicit reliance rationale is required")


@dataclass(frozen=True, slots=True)
class CompleteReviewCommand:
    adequacy: DetermineAdequacyCommand
    reliance: DesignateRelianceCommand


@dataclass(frozen=True, slots=True)
class AssessmentSelection:
    kind: ReviewSelectionKind
    version_ids: tuple[RecordVersionId, ...]
    assessment_version_id: RecordVersionId | None = None
    outcome: str | None = None
