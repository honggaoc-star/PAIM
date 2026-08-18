"""Typed Increment 5 Intervention, activation, and Learning values."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from paim.integrity import EffectiveInterval, RecordId, RecordVersionId
from paim.integrity.records import JsonValue, RelationshipType


class RequirementType(StrEnum):
    REQUIRED_BEFORE_OPERATION = "REQUIRED_BEFORE_OPERATION"
    REQUIRED_AFTER_OPERATION = "REQUIRED_AFTER_OPERATION"
    OPTIONAL = "OPTIONAL"


class InterventionStatus(StrEnum):
    PROPOSED = "PROPOSED"
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    PARTIALLY_COMPLETED = "PARTIALLY_COMPLETED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    SUPERSEDED = "SUPERSEDED"


class CriterionOutcome(StrEnum):
    MET = "MET"
    NOT_MET = "NOT_MET"
    INDETERMINATE = "INDETERMINATE"


class CompletionAcceptanceOutcome(StrEnum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class CompletionAcceptanceStatus(StrEnum):
    CURRENT = "CURRENT"
    WITHDRAWN = "WITHDRAWN"
    SUPERSEDED = "SUPERSEDED"


class ObligationResult(StrEnum):
    SATISFIED = "SATISFIED"
    NOT_ESTABLISHED = "NOT_ESTABLISHED"
    INCOMPLETE = "INCOMPLETE"
    BLOCKED = "BLOCKED"
    CONFLICT = "CONFLICT"


class AggregatePrerequisiteResult(StrEnum):
    SATISFIED = "SATISFIED"
    NOT_REQUIRED = "NOT_REQUIRED"
    NOT_ESTABLISHED = "NOT_ESTABLISHED"
    INCOMPLETE = "INCOMPLETE"
    BLOCKED = "BLOCKED"
    CONFLICT = "CONFLICT"


class ActivationAuthorityKind(StrEnum):
    DECISION_AUTHORITY = "DECISION_AUTHORITY"
    ORGANIZATIONAL_MECHANISM = "ORGANIZATIONAL_MECHANISM"


class LearningStatus(StrEnum):
    PROPOSED = "PROPOSED"
    ACTIVE = "ACTIVE"
    AWAITING_EVIDENCE = "AWAITING_EVIDENCE"
    COMPLETED = "COMPLETED"
    INCONCLUSIVE = "INCONCLUSIVE"
    CANCELLED = "CANCELLED"
    SUPERSEDED = "SUPERSEDED"


@dataclass(frozen=True, slots=True)
class InterventionVersionInput:
    intervention_id: RecordId
    version_id: RecordVersionId
    case_id: RecordId
    decision_version_id: RecordVersionId
    configuration_id: RecordId
    configuration_version_id: RecordVersionId
    owner_actor_id: RecordId
    owner_assignment_version_id: RecordVersionId | None
    accountable_mechanism: str | None
    status: InterventionStatus
    title: str
    scope: str
    implementation_provenance: dict[str, JsonValue]
    completion_criteria: tuple[str, ...]
    fallback_and_remediation: str | None
    effective: EffectiveInterval
    expected_version_id: RecordVersionId | None = None
    relationship_type: RelationshipType = RelationshipType.SUPERSESSION
    relationship_reason: str | None = None


@dataclass(frozen=True, slots=True)
class ObligationVersionInput:
    obligation_id: RecordId
    version_id: RecordVersionId
    intervention_id: RecordId
    intervention_version_id: RecordVersionId
    requirement_type: RequirementType
    completion_criteria: tuple[str, ...]
    boundary_clause_version_ids: tuple[RecordVersionId, ...]
    decision_conditions: tuple[str, ...]
    control_references: tuple[str, ...]
    prohibitions: tuple[str, ...]
    rationale: str
    provenance: dict[str, JsonValue]
    post_operation_permitted: bool = False
    post_operation_timing_conditions: tuple[str, ...] = ()
    expected_version_id: RecordVersionId | None = None
    relationship_type: RelationshipType = RelationshipType.SUPERSESSION
    relationship_reason: str | None = None


@dataclass(frozen=True, slots=True)
class ObligationSetVersionInput:
    obligation_set_id: RecordId
    version_id: RecordVersionId
    decision_id: RecordId
    decision_version_id: RecordVersionId
    case_id: RecordId
    configuration_id: RecordId
    configuration_version_id: RecordVersionId
    obligations: tuple[ObligationVersionInput, ...]
    rationale: str
    effective: EffectiveInterval
    expected_version_id: RecordVersionId | None = None
    relationship_type: RelationshipType = RelationshipType.SUPERSESSION
    relationship_reason: str | None = None


@dataclass(frozen=True, slots=True)
class CompletionCriterionResult:
    criterion: str
    outcome: CriterionOutcome
    rationale: str


@dataclass(frozen=True, slots=True)
class CompletionResultVersionInput:
    result_id: RecordId
    version_id: RecordVersionId
    obligation_version_id: RecordVersionId
    intervention_version_id: RecordVersionId
    decision_version_id: RecordVersionId
    configuration_version_id: RecordVersionId
    criteria: tuple[CompletionCriterionResult, ...]
    evidence_version_ids: tuple[RecordVersionId, ...]
    evidence_provenance: dict[str, JsonValue]
    performer_actor_id: RecordId
    limitations: tuple[str, ...]
    residual_exposure: str | None
    fallback_remediation_state: str | None
    effective: EffectiveInterval
    expected_version_id: RecordVersionId | None = None
    relationship_type: RelationshipType = RelationshipType.SUPERSESSION
    relationship_reason: str | None = None


@dataclass(frozen=True, slots=True)
class CompletionAcceptorMechanismVersionInput:
    mechanism_id: RecordId
    version_id: RecordVersionId
    case_id: RecordId
    intervention_id: RecordId
    intervention_version_id: RecordVersionId
    decision_version_id: RecordVersionId
    configuration_id: RecordId
    configuration_version_id: RecordVersionId
    accountable_actor_id: RecordId
    rule_version: str
    authority_scope: str
    authority_source: str
    effective: EffectiveInterval
    expected_version_id: RecordVersionId | None = None
    relationship_type: RelationshipType = RelationshipType.SUPERSESSION
    relationship_reason: str | None = None


@dataclass(frozen=True, slots=True)
class CompletionAcceptanceVersionInput:
    acceptance_id: RecordId
    version_id: RecordVersionId
    obligation_version_id: RecordVersionId
    intervention_version_id: RecordVersionId
    completion_result_version_id: RecordVersionId
    decision_version_id: RecordVersionId
    configuration_version_id: RecordVersionId
    boundary_condition_references: tuple[str, ...]
    outcome: CompletionAcceptanceOutcome
    rationale: str
    exceptions: tuple[str, ...]
    limitations: tuple[str, ...]
    accountable_actor_id: RecordId
    accountable_assignment_version_id: RecordVersionId | None
    accountable_mechanism_version_id: RecordVersionId | None
    delegation_chain_version_ids: tuple[RecordVersionId, ...]
    effective: EffectiveInterval
    expected_version_id: RecordVersionId | None = None
    relationship_type: RelationshipType = RelationshipType.SUPERSESSION
    relationship_reason: str | None = None
    status: CompletionAcceptanceStatus = CompletionAcceptanceStatus.CURRENT


@dataclass(frozen=True, slots=True)
class ReplacementVersionInput:
    replacement_id: RecordId
    version_id: RecordVersionId
    obligation_version_id: RecordVersionId
    predecessor_intervention_version_id: RecordVersionId
    replacement_intervention_version_id: RecordVersionId
    substantive_change: bool
    successor_decision_version_id: RecordVersionId | None
    rationale: str
    effective: EffectiveInterval
    expected_version_id: RecordVersionId | None = None
    relationship_type: RelationshipType = RelationshipType.SUPERSESSION
    relationship_reason: str | None = None


@dataclass(frozen=True, slots=True)
class ReuseDeterminationVersionInput:
    determination_id: RecordId
    version_id: RecordVersionId
    successor_obligation_version_id: RecordVersionId
    prior_completion_result_version_id: RecordVersionId
    prior_acceptance_version_id: RecordVersionId
    accountable_actor_id: RecordId
    accountable_assignment_version_id: RecordVersionId | None
    accountable_mechanism: str | None
    unchanged_configuration_content: bool
    boundary_conditions_covered: bool
    completion_criteria_covered: bool
    evidence_applicability_covered: bool
    acceptance_scope_covered: bool
    changed_configuration_version_covered: bool
    rationale: str
    effective: EffectiveInterval
    expected_version_id: RecordVersionId | None = None
    relationship_type: RelationshipType = RelationshipType.SUPERSESSION
    relationship_reason: str | None = None


@dataclass(frozen=True, slots=True)
class InterventionDetail:
    intervention_id: RecordId
    version_id: RecordVersionId
    case_id: RecordId
    decision_version_id: RecordVersionId
    configuration_id: RecordId
    configuration_version_id: RecordVersionId
    owner_actor_id: RecordId
    status: InterventionStatus


@dataclass(frozen=True, slots=True)
class ObligationDetail:
    obligation_id: RecordId
    version_id: RecordVersionId
    obligation_set_version_id: RecordVersionId
    decision_version_id: RecordVersionId
    configuration_version_id: RecordVersionId
    intervention_id: RecordId
    intervention_version_id: RecordVersionId
    requirement_type: RequirementType
    post_operation_permitted: bool
    post_operation_timing_conditions: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ObligationSetDetail:
    obligation_set_id: RecordId
    version_id: RecordVersionId
    decision_id: RecordId
    decision_version_id: RecordVersionId
    case_id: RecordId
    configuration_id: RecordId
    configuration_version_id: RecordVersionId
    obligation_version_ids: tuple[RecordVersionId, ...]


@dataclass(frozen=True, slots=True)
class CompletionResultDetail:
    result_id: RecordId
    version_id: RecordVersionId
    obligation_version_id: RecordVersionId
    intervention_version_id: RecordVersionId
    decision_version_id: RecordVersionId
    configuration_version_id: RecordVersionId
    criteria: tuple[CompletionCriterionResult, ...]
    evidence_version_ids: tuple[RecordVersionId, ...]

    @property
    def all_met(self) -> bool:
        return bool(self.criteria) and all(
            item.outcome is CriterionOutcome.MET for item in self.criteria
        )


@dataclass(frozen=True, slots=True)
class CompletionAcceptanceDetail:
    acceptance_id: RecordId
    version_id: RecordVersionId
    obligation_version_id: RecordVersionId
    intervention_version_id: RecordVersionId
    completion_result_version_id: RecordVersionId
    decision_version_id: RecordVersionId
    configuration_version_id: RecordVersionId
    outcome: CompletionAcceptanceOutcome
    accountable_actor_id: RecordId
    accountable_assignment_version_id: RecordVersionId | None
    accountable_mechanism_version_id: RecordVersionId | None
    status: CompletionAcceptanceStatus


@dataclass(frozen=True, slots=True)
class CompletionAccountabilityFound:
    assignment_version_id: RecordVersionId | None
    mechanism_version_id: RecordVersionId | None


@dataclass(frozen=True, slots=True)
class CompletionAccountabilityNotEstablished:
    reason: str = "COMPLETION ACCEPTANCE ACCOUNTABILITY NOT ESTABLISHED"


@dataclass(frozen=True, slots=True)
class CompletionAccountabilityConflict:
    candidate_version_ids: frozenset[RecordVersionId]
    reason: str = "COMPLETION ACCEPTANCE ACCOUNTABILITY CONFLICT — UNRESOLVED"


type CompletionAccountabilityResolution = (
    CompletionAccountabilityFound
    | CompletionAccountabilityNotEstablished
    | CompletionAccountabilityConflict
)


@dataclass(frozen=True, slots=True)
class CompletionAcceptanceFound:
    acceptance_version_id: RecordVersionId
    outcome: CompletionAcceptanceOutcome


@dataclass(frozen=True, slots=True)
class CompletionAcceptanceNotEstablished:
    reason: str = "ACCEPTANCE NOT ESTABLISHED"


@dataclass(frozen=True, slots=True)
class CompletionAcceptanceConflict:
    acceptance_version_ids: frozenset[RecordVersionId]
    reason: str = "COMPLETION ACCEPTANCE CONFLICT — UNRESOLVED"


type CompletionAcceptanceSelection = (
    CompletionAcceptanceFound | CompletionAcceptanceNotEstablished | CompletionAcceptanceConflict
)


@dataclass(frozen=True, slots=True)
class ObligationSetFound:
    obligation_set_version_id: RecordVersionId


@dataclass(frozen=True, slots=True)
class ObligationSetNotEstablished:
    reason: str = "OBLIGATION SET NOT ESTABLISHED"


@dataclass(frozen=True, slots=True)
class ObligationSetConflict:
    obligation_set_version_ids: frozenset[RecordVersionId]
    reason: str = "OBLIGATION SET CONFLICT — UNRESOLVED"


type ObligationSetSelection = (
    ObligationSetFound | ObligationSetNotEstablished | ObligationSetConflict
)


@dataclass(frozen=True, slots=True)
class ObligationEvaluation:
    obligation_version_id: RecordVersionId
    result: ObligationResult
    intervention_version_id: RecordVersionId | None
    completion_result_version_id: RecordVersionId | None
    completion_acceptance_version_id: RecordVersionId | None
    replacement_version_id: RecordVersionId | None
    reuse_determination_version_id: RecordVersionId | None
    diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PrerequisiteEvaluation:
    decision_version_id: RecordVersionId
    configuration_version_id: RecordVersionId
    obligation_set_version_id: RecordVersionId | None
    result: AggregatePrerequisiteResult
    obligations: tuple[ObligationEvaluation, ...]
    diagnostics: tuple[str, ...]
    effective_at: datetime
    known_at: datetime


@dataclass(frozen=True, slots=True)
class ActivationRequest:
    basis_id: RecordId
    basis_version_id: RecordVersionId
    authorization_id: RecordId
    authorization_version_id: RecordVersionId
    activation_event_id: str
    case_id: RecordId
    decision_version_id: RecordVersionId
    configuration_id: RecordId
    configuration_version_id: RecordVersionId
    boundary_snapshot_version_id: RecordVersionId
    operating_state: str
    authority_kind: ActivationAuthorityKind
    authority_actor_id: RecordId | None
    authority_assignment_version_id: RecordVersionId | None
    preauthorized_mechanism_version_id: RecordVersionId | None
    decision_authorization_basis_version_id: RecordVersionId
    authority_scope: str
    authority_limits: tuple[str, ...]
    authority_effective: EffectiveInterval
    delegation_chain_version_ids: tuple[RecordVersionId, ...]
    rationale: str
    effective_at: datetime
    known_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class ActivationResult:
    activated: bool
    reason: str
    basis_version_id: RecordVersionId | None = None
    authorization_version_id: RecordVersionId | None = None
    lifecycle_event_id: str | None = None


@dataclass(frozen=True, slots=True)
class LearningItemVersionInput:
    learning_item_id: RecordId
    version_id: RecordVersionId
    case_id: RecordId
    decision_version_id: RecordVersionId
    configuration_id: RecordId
    configuration_version_id: RecordVersionId
    uncertainty_version_id: RecordVersionId
    question_or_hypothesis: str
    purpose: str
    expected_knowledge_gain: str
    owner_actor_id: RecordId
    owner_assignment_version_id: RecordVersionId | None
    accountable_mechanism: str | None
    method_activity: str
    status: LearningStatus
    result: str | None
    limitations: tuple[str, ...]
    evidence_version_ids: tuple[RecordVersionId, ...]
    successor_decision_version_id: RecordVersionId | None
    reassessment_extension_reference: str | None
    provenance: dict[str, JsonValue]
    effective: EffectiveInterval
    expected_version_id: RecordVersionId | None = None
    relationship_type: RelationshipType = RelationshipType.SUPERSESSION
    relationship_reason: str | None = None
