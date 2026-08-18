"""Typed Increment 4 Integration, Boundary, Decision, and authorization values."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from paim.integrity import EffectiveInterval, RecordId, RecordVersionId
from paim.integrity.records import JsonValue, RelationshipType


class IntegrationStatus(StrEnum):
    DRAFT = "draft"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DECISION_PENDING = "decision_pending"
    SUPERSEDED = "superseded"
    WITHDRAWN = "withdrawn"


class UncertaintyClassification(StrEnum):
    ACCEPTED = "ACCEPTED_UNCERTAINTY"
    DECISION_LIMITING = "DECISION_LIMITING_UNCERTAINTY"


class BoundaryClauseEffect(StrEnum):
    PERMITTED = "permitted"
    EXCLUDED = "excluded"
    REQUIRED = "required"
    LIMITED = "limited"
    CONDITIONAL = "conditional"
    INDETERMINATE = "indeterminate"


class BoundaryVerificationMode(StrEnum):
    MECHANICAL = "mechanically_testable"
    HUMAN = "human_determination_required"
    EXTERNAL = "external_determination_required"
    INDETERMINATE = "indeterminate"


class BoundaryEvaluationOutcome(StrEnum):
    PASS = "PASS"
    BREACH = "BREACH"
    INDETERMINATE = "INDETERMINATE"


class BoundaryComparisonOutcome(StrEnum):
    UNCHANGED = "UNCHANGED"
    NARROWED = "NARROWED"
    BROADENED = "BROADENED"
    MIXED = "MIXED"
    INDETERMINATE = "INDETERMINATE"


class DecisionStatus(StrEnum):
    PROPOSED = "proposed"
    PENDING_AUTHORIZATION = "pending_authorization"
    AUTHORIZED = "authorized"
    SUPERSEDED = "superseded"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"


@dataclass(frozen=True, slots=True)
class PreauthorizedActivationMechanismInput:
    mechanism_id: RecordId
    mechanism_version_id: RecordVersionId
    rule_version: str
    scope: str
    authority_source: str
    limits: tuple[str, ...]
    effective: EffectiveInterval


@dataclass(frozen=True, slots=True)
class IntegrationVersionInput:
    integration_id: RecordId
    version_id: RecordVersionId
    case_id: RecordId
    configuration_id: RecordId
    configuration_version_id: RecordVersionId
    use_context: str
    purpose: str
    value_input_version_id: RecordVersionId
    value_acceptance_version_id: RecordVersionId
    value_fitness_version_id: RecordVersionId
    risk_input_version_id: RecordVersionId
    risk_acceptance_version_id: RecordVersionId
    risk_fitness_version_id: RecordVersionId
    material_applicability_version_ids: tuple[RecordVersionId, ...]
    constraint_references: tuple[str, ...]
    authority_record_version_ids: tuple[RecordVersionId, ...]
    authority_gap_version_ids: tuple[RecordVersionId, ...]
    integrator_actor_id: RecordId
    owner_assignment_version_id: RecordVersionId | None
    accountable_mechanism: str | None
    status: IntegrationStatus
    interaction_analysis: dict[str, JsonValue]
    alternatives: tuple[dict[str, JsonValue], ...]
    proposed_judgment: dict[str, JsonValue]
    rationale: str
    effective: EffectiveInterval
    expected_version_id: RecordVersionId | None = None
    relationship_type: RelationshipType = RelationshipType.SUPERSESSION
    relationship_reason: str | None = None


@dataclass(frozen=True, slots=True)
class UncertaintyClassificationVersionInput:
    classification_id: RecordId
    version_id: RecordVersionId
    integration_version_id: RecordVersionId
    proposed_decision_context: str
    proposed_operating_state: str
    source_reference: str
    source_input_version_id: RecordVersionId | None
    source_evidence_version_id: RecordVersionId | None
    classification: UncertaintyClassification
    rationale: str
    observation_or_requirement: str
    accountable_assignment_version_id: RecordVersionId | None
    accountable_mechanism: str | None
    effective: EffectiveInterval
    expected_version_id: RecordVersionId | None = None
    relationship_type: RelationshipType = RelationshipType.SUPERSESSION
    relationship_reason: str | None = None


@dataclass(frozen=True, slots=True)
class BoundaryClauseInput:
    clause_id: RecordId
    clause_version_id: RecordVersionId
    clause_type: str
    effect: BoundaryClauseEffect
    target_reference: str | None
    structured_reference: str | None
    operator: str | None
    value: str | None
    unit: str | None
    narrative: str
    rationale: str
    provenance: tuple[str, ...]
    verification_mode: BoundaryVerificationMode
    breach_consequence: str | None
    predecessor_clause_version_id: RecordVersionId | None = None
    relationship_reason: str | None = None


@dataclass(frozen=True, slots=True)
class BoundarySnapshotVersionInput:
    snapshot_id: RecordId
    version_id: RecordVersionId
    case_id: RecordId
    configuration_id: RecordId
    configuration_version_id: RecordVersionId
    integration_id: RecordId
    integration_version_id: RecordVersionId
    owner_actor_id: RecordId
    status: str
    clauses: tuple[BoundaryClauseInput, ...]
    narrative_rationale: str
    unresolved_items: tuple[str, ...]
    effective: EffectiveInterval
    expected_version_id: RecordVersionId | None = None
    relationship_type: RelationshipType = RelationshipType.SUPERSESSION
    relationship_reason: str | None = None


@dataclass(frozen=True, slots=True)
class BoundaryDeterminationVersionInput:
    determination_id: RecordId
    version_id: RecordVersionId
    snapshot_version_id: RecordVersionId
    clause_id: RecordId
    clause_version_id: RecordVersionId
    outcome: BoundaryEvaluationOutcome
    actor_id: RecordId
    accountable_assignment_version_id: RecordVersionId | None
    accountable_mechanism: str | None
    evidence_version_ids: tuple[RecordVersionId, ...]
    rationale: str
    review_condition: str | None
    effective: EffectiveInterval
    expected_version_id: RecordVersionId | None = None
    relationship_type: RelationshipType = RelationshipType.SUPERSESSION
    relationship_reason: str | None = None


@dataclass(frozen=True, slots=True)
class DecisionVersionInput:
    decision_id: RecordId
    version_id: RecordVersionId
    case_id: RecordId
    configuration_id: RecordId
    configuration_version_id: RecordVersionId
    integration_id: RecordId
    integration_version_id: RecordVersionId
    boundary_snapshot_id: RecordId
    boundary_snapshot_version_id: RecordVersionId
    proposed_action: str
    operating_state: str
    rationale: str
    conditions_and_limits: tuple[str, ...]
    accepted_uncertainty_version_ids: tuple[RecordVersionId, ...]
    decision_limiting_uncertainty_version_ids: tuple[RecordVersionId, ...]
    alternatives_considered: tuple[str, ...]
    constraint_references: tuple[str, ...]
    authority_record_version_ids: tuple[RecordVersionId, ...]
    authority_gap_version_ids: tuple[RecordVersionId, ...]
    intervention_declarations: tuple[str, ...]
    learning_declarations: tuple[str, ...]
    reassessment_declarations: tuple[str, ...]
    status: DecisionStatus
    effective: EffectiveInterval
    expected_version_id: RecordVersionId | None = None
    relationship_type: RelationshipType = RelationshipType.AMENDMENT
    relationship_reason: str | None = None


@dataclass(frozen=True, slots=True)
class BoundedProceedVersionInput:
    determination_id: RecordId
    version_id: RecordVersionId
    decision_version_id: RecordVersionId
    unresolved_gap_version_id: RecordVersionId
    blocked_broader_decision: str
    narrower_scope: str
    boundary_clause_version_ids: tuple[RecordVersionId, ...]
    operating_state: str
    rationale: str
    conditions: tuple[str, ...]
    review_trigger: str
    actor_id: RecordId
    authority_assignment_version_id: RecordVersionId | None
    authority_mechanism: str | None
    authority_record_version_id: RecordVersionId | None
    delegation_chain_version_ids: tuple[RecordVersionId, ...]
    effective: EffectiveInterval
    expected_version_id: RecordVersionId | None = None
    relationship_type: RelationshipType = RelationshipType.SUPERSESSION
    relationship_reason: str | None = None


@dataclass(frozen=True, slots=True)
class DecisionAuthorizationBasisVersionInput:
    basis_id: RecordId
    version_id: RecordVersionId
    decision_id: RecordId
    decision_version_id: RecordVersionId
    decision_authority_identity: str
    authority_assignment_version_id: RecordVersionId | None
    authority_mechanism: str | None
    authority_record_version_id: RecordVersionId | None
    delegation_chain_version_ids: tuple[RecordVersionId, ...]
    authorized_scope: str
    limits: tuple[str, ...]
    configuration_id: RecordId
    configuration_version_id: RecordVersionId
    operating_state_coverage: tuple[str, ...]
    decision_type: str
    organizational_unit: str | None
    authorization_event_id: str
    authorization_actor_id: RecordId
    authorization_effective_at: datetime
    conditions: tuple[str, ...]
    dissent: tuple[str, ...]
    exception: str | None
    authority_gap_version_ids: tuple[RecordVersionId, ...]
    bounded_proceed_version_id: RecordVersionId | None
    effective: EffectiveInterval
    expected_version_id: RecordVersionId | None = None
    relationship_type: RelationshipType = RelationshipType.SUPERSESSION
    relationship_reason: str | None = None
    preauthorized_activation_mechanisms: tuple[PreauthorizedActivationMechanismInput, ...] = ()


@dataclass(frozen=True, slots=True)
class IntegrationDetail:
    integration_id: RecordId
    version_id: RecordVersionId
    case_id: RecordId
    configuration_id: RecordId
    configuration_version_id: RecordVersionId
    use_context: str
    purpose: str
    value_input_version_id: RecordVersionId
    value_acceptance_version_id: RecordVersionId
    value_fitness_version_id: RecordVersionId
    risk_input_version_id: RecordVersionId
    risk_acceptance_version_id: RecordVersionId
    risk_fitness_version_id: RecordVersionId
    status: IntegrationStatus


@dataclass(frozen=True, slots=True)
class BoundaryClauseDetail:
    clause_id: RecordId
    clause_version_id: RecordVersionId
    clause_type: str
    effect: BoundaryClauseEffect
    target_reference: str | None
    structured_reference: str | None
    operator: str | None
    value: str | None
    unit: str | None
    narrative: str
    verification_mode: BoundaryVerificationMode


@dataclass(frozen=True, slots=True)
class BoundarySnapshotDetail:
    snapshot_id: RecordId
    version_id: RecordVersionId
    case_id: RecordId
    configuration_id: RecordId
    configuration_version_id: RecordVersionId
    integration_id: RecordId
    integration_version_id: RecordVersionId
    status: str
    clauses: tuple[BoundaryClauseDetail, ...]


@dataclass(frozen=True, slots=True)
class DecisionDetail:
    decision_id: RecordId
    version_id: RecordVersionId
    case_id: RecordId
    configuration_id: RecordId
    configuration_version_id: RecordVersionId
    integration_id: RecordId
    integration_version_id: RecordVersionId
    boundary_snapshot_id: RecordId
    boundary_snapshot_version_id: RecordVersionId
    proposed_action: str
    operating_state: str
    status: DecisionStatus


@dataclass(frozen=True, slots=True)
class AuthorizationBasisDetail:
    basis_id: RecordId
    version_id: RecordVersionId
    decision_version_id: RecordVersionId
    authority_assignment_version_id: RecordVersionId | None
    authority_mechanism: str | None
    authority_record_version_id: RecordVersionId | None
    authorized_scope: str
    configuration_id: RecordId
    configuration_version_id: RecordVersionId
    operating_state_coverage: tuple[str, ...]
    bounded_proceed_version_id: RecordVersionId | None


@dataclass(frozen=True, slots=True)
class BoundaryEvaluation:
    clause_version_id: RecordVersionId
    outcome: BoundaryEvaluationOutcome
    reason: str


@dataclass(frozen=True, slots=True)
class AuthorizedDecisionFound:
    decision_version_id: RecordVersionId
    boundary_snapshot_version_id: RecordVersionId
    authorization_basis_version_id: RecordVersionId


@dataclass(frozen=True, slots=True)
class AuthorizedDecisionNotEstablished:
    reason: str = "AUTHORIZED DECISION NOT ESTABLISHED"


@dataclass(frozen=True, slots=True)
class AuthorizedDecisionConflict:
    decision_version_ids: frozenset[RecordVersionId]
    authorization_basis_version_ids: frozenset[RecordVersionId]
    reason: str = "AUTHORIZED DECISION CONFLICT — UNRESOLVED"


type AuthorizedDecisionSelection = (
    AuthorizedDecisionFound | AuthorizedDecisionNotEstablished | AuthorizedDecisionConflict
)
