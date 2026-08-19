"""Typed Increment 6 Trigger, Reassessment, and Interim Disposition values."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from paim.domain.increment4 import (
    BoundarySnapshotVersionInput,
    DecisionAuthorizationBasisVersionInput,
    DecisionVersionInput,
)
from paim.integrity import EffectiveInterval, RecordId, RecordVersionId
from paim.integrity.records import JsonValue, RelationshipType


class TriggerSourceKind(StrEnum):
    PAIM_RECORD = "PAIM_RECORD"
    HUMAN_EXTERNAL = "HUMAN_EXTERNAL"


class TriggerDeterminationOutcome(StrEnum):
    INFORMATIONAL = "INFORMATIONAL"
    MONITOR = "MONITOR"
    ANALYTICAL_REFRESH = "ANALYTICAL_REFRESH"
    REASSESSMENT_REQUIRED = "REASSESSMENT_REQUIRED"
    IMMEDIATE_DISPOSITION_AND_REASSESSMENT = "IMMEDIATE_DISPOSITION_AND_REASSESSMENT"


class ReassessmentStatus(StrEnum):
    PROPOSED = "PROPOSED"
    OPEN = "OPEN"
    ANALYSIS_IN_PROGRESS = "ANALYSIS_IN_PROGRESS"
    AWAITING_DECISION_AUTHORITY = "AWAITING_DECISION_AUTHORITY"
    BLOCKED_CONFLICT = "BLOCKED_CONFLICT"
    COMPLETED_CONFIRMED = "COMPLETED_CONFIRMED"
    COMPLETED_SUCCESSOR_DECISION = "COMPLETED_SUCCESSOR_DECISION"
    CANCELLED = "CANCELLED"
    SUPERSEDED = "SUPERSEDED"


class AccountabilityFunction(StrEnum):
    TRIGGER_DETERMINER = "Trigger Determiner"
    REASSESSMENT_OWNER = "Reassessment Owner"
    REASSESSMENT_COORDINATION_AUTHORITY = "Reassessment Coordination Authority"


class ReassessmentDeterminationKind(StrEnum):
    GROUPING = "GROUPING"
    DUPLICATE = "DUPLICATE"
    COEXISTENCE = "COEXISTENCE"
    CANCELLATION = "CANCELLATION"
    SUPERSESSION = "SUPERSESSION"


class ReassessmentDeterminationOutcome(StrEnum):
    COMPATIBLE = "COMPATIBLE"
    INCOMPATIBLE = "INCOMPATIBLE"
    DUPLICATE = "DUPLICATE"
    COEXISTENCE_AUTHORIZED = "COEXISTENCE_AUTHORIZED"
    CANCELLATION_AUTHORIZED = "CANCELLATION_AUTHORIZED"
    SUPERSESSION_AUTHORIZED = "SUPERSESSION_AUTHORIZED"


@dataclass(frozen=True, slots=True)
class ReassessmentDeterminationFound:
    version_id: RecordVersionId
    outcome: ReassessmentDeterminationOutcome


@dataclass(frozen=True, slots=True)
class ReassessmentDeterminationNotEstablished:
    reason: str


@dataclass(frozen=True, slots=True)
class ReassessmentDeterminationConflict:
    version_ids: frozenset[RecordVersionId]
    reason: str


type ReassessmentDeterminationSelection = (
    ReassessmentDeterminationFound
    | ReassessmentDeterminationNotEstablished
    | ReassessmentDeterminationConflict
)


class TriggerCoverageState(StrEnum):
    REASSESSMENT_REQUIRED_UNASSIGNED = "REASSESSMENT_REQUIRED_UNASSIGNED"
    LINKED_ACTIVE = "LINKED_ACTIVE"
    BLOCKED_CONFLICT = "BLOCKED_CONFLICT"
    SATISFIED_BY_COMPLETED_REASSESSMENT = "SATISFIED_BY_COMPLETED_REASSESSMENT"
    DUPLICATE_DISPOSITIONED = "DUPLICATE_DISPOSITIONED"


@dataclass(frozen=True, slots=True)
class ReassessmentMechanismVersionInput:
    mechanism_id: RecordId
    version_id: RecordVersionId
    function: AccountabilityFunction
    case_id: RecordId
    decision_version_id: RecordVersionId
    configuration_version_id: RecordVersionId
    accountable_actor_id: RecordId
    rule_version: str
    authority_scope: str
    authority_source: str
    limits: tuple[str, ...]
    effective: EffectiveInterval
    intervention_version_id: RecordVersionId | None = None
    expected_version_id: RecordVersionId | None = None
    relationship_type: RelationshipType = RelationshipType.SUPERSESSION
    relationship_reason: str | None = None


@dataclass(frozen=True, slots=True)
class TriggerVersionInput:
    trigger_id: RecordId
    version_id: RecordVersionId
    case_id: RecordId
    decision_version_id: RecordVersionId
    configuration_version_id: RecordVersionId
    trigger_type: str
    management_question: str
    affected_scope: frozenset[str]
    source_kind: TriggerSourceKind
    source_family: str
    source_record_id: str
    source_version_id: str
    source_event_id: str
    source_knowledge_at: datetime
    description: str
    rationale: str
    affected_references: tuple[str, ...]
    provenance: dict[str, JsonValue]
    effective: EffectiveInterval
    source_system: str | None = None
    source_actor: str | None = None
    withdrawn: bool = False
    expected_version_id: RecordVersionId | None = None
    relationship_type: RelationshipType = RelationshipType.SUPERSESSION
    relationship_reason: str | None = None


@dataclass(frozen=True, slots=True)
class TriggerDeterminationVersionInput:
    determination_id: RecordId
    version_id: RecordVersionId
    trigger_version_id: RecordVersionId
    case_id: RecordId
    decision_version_id: RecordVersionId
    configuration_version_id: RecordVersionId
    outcome: TriggerDeterminationOutcome
    rationale: str
    actor_id: RecordId
    accountable_assignment_version_id: RecordVersionId | None
    accountable_mechanism_version_id: RecordVersionId | None
    delegation_chain_version_ids: tuple[RecordVersionId, ...]
    effective: EffectiveInterval
    expected_version_id: RecordVersionId | None = None
    relationship_type: RelationshipType = RelationshipType.SUPERSESSION
    relationship_reason: str | None = None


@dataclass(frozen=True, slots=True)
class TriggerDeterminationFound:
    version_id: RecordVersionId
    outcome: TriggerDeterminationOutcome


@dataclass(frozen=True, slots=True)
class TriggerDeterminationNotEstablished:
    reason: str = "TRIGGER DETERMINATION NOT ESTABLISHED"


@dataclass(frozen=True, slots=True)
class TriggerDeterminationConflict:
    version_ids: frozenset[RecordVersionId]
    reason: str = "TRIGGER DETERMINATION CONFLICT — UNRESOLVED"


type TriggerDeterminationSelection = (
    TriggerDeterminationFound | TriggerDeterminationNotEstablished | TriggerDeterminationConflict
)


@dataclass(frozen=True, slots=True)
class MembershipVersionInput:
    membership_id: RecordId
    version_id: RecordVersionId
    trigger_version_id: RecordVersionId
    membership_scope: str
    active: bool = True


@dataclass(frozen=True, slots=True)
class ReassessmentVersionInput:
    reassessment_id: RecordId
    version_id: RecordVersionId
    case_id: RecordId
    decision_version_id: RecordVersionId
    configuration_version_id: RecordVersionId
    purpose: str
    affected_scope: frozenset[str]
    owner_actor_id: RecordId
    owner_assignment_version_id: RecordVersionId | None
    owner_mechanism_version_id: RecordVersionId | None
    memberships: tuple[MembershipVersionInput, ...]
    status: ReassessmentStatus
    rationale: str
    reviewed_basis_version_ids: tuple[RecordVersionId, ...]
    effective: EffectiveInterval
    expected_version_id: RecordVersionId | None = None
    relationship_type: RelationshipType = RelationshipType.SUPERSESSION
    relationship_reason: str | None = None


@dataclass(frozen=True, slots=True)
class ReassessmentDeterminationVersionInput:
    determination_id: RecordId
    version_id: RecordVersionId
    kind: ReassessmentDeterminationKind
    outcome: ReassessmentDeterminationOutcome
    case_id: RecordId
    decision_version_id: RecordVersionId
    configuration_version_id: RecordVersionId
    affected_scope: frozenset[str]
    trigger_version_ids: tuple[RecordVersionId, ...]
    reassessment_version_ids: tuple[RecordVersionId, ...]
    actor_id: RecordId
    accountable_assignment_version_id: RecordVersionId | None
    accountable_mechanism_version_id: RecordVersionId | None
    delegation_chain_version_ids: tuple[RecordVersionId, ...]
    rationale: str
    effective: EffectiveInterval
    target_reassessment_version_id: RecordVersionId | None = None
    canonical_trigger_version_id: RecordVersionId | None = None
    expected_version_id: RecordVersionId | None = None
    relationship_type: RelationshipType = RelationshipType.SUPERSESSION
    relationship_reason: str | None = None


@dataclass(frozen=True, slots=True)
class TriggerCoverage:
    trigger_version_id: RecordVersionId
    state: TriggerCoverageState | None
    supporting_version_ids: frozenset[RecordVersionId]
    reason: str


@dataclass(frozen=True, slots=True)
class ReassessmentOverlap:
    compatible: bool
    reason: str
    determination_version_id: RecordVersionId | None = None


@dataclass(frozen=True, slots=True)
class ReassessmentTerminationRequest:
    reassessment_id: RecordId
    expected_reassessment_version_id: RecordVersionId
    determination_version_id: RecordVersionId
    effective_at: datetime
    successor_reassessment_version_id: RecordVersionId | None = None


@dataclass(frozen=True, slots=True)
class InterimOperatingDispositionVersionInput:
    disposition_id: RecordId
    version_id: RecordVersionId
    reassessment_version_id: RecordVersionId
    case_id: RecordId
    decision_version_id: RecordVersionId
    configuration_version_id: RecordVersionId
    boundary_snapshot_version_id: RecordVersionId
    affected_scope: frozenset[str]
    operating_state: str | None
    allowed_actions: frozenset[str]
    required_controls: frozenset[str]
    prohibitions: frozenset[str]
    conditions: frozenset[str]
    suspend_scope: bool
    rationale: str
    authority_basis_version_id: RecordVersionId
    authority_actor_id: RecordId
    expiry_at: datetime | None
    knowledge_cutoff: datetime
    effective: EffectiveInterval
    expected_version_id: RecordVersionId | None = None
    relationship_type: RelationshipType = RelationshipType.SUPERSESSION
    relationship_reason: str | None = None


@dataclass(frozen=True, slots=True)
class EffectiveOperatingDispositionPartition:
    suspended: bool
    affected_scope: frozenset[str]
    operating_state_values: frozenset[str]
    allowed_actions: frozenset[str]
    required_controls: frozenset[str]
    prohibitions: frozenset[str]
    conditions: frozenset[str]
    disposition_version_ids: frozenset[RecordVersionId]
    reason: str


@dataclass(frozen=True, slots=True)
class EffectiveOperatingDisposition:
    partitions: tuple[EffectiveOperatingDispositionPartition, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class DecisionConfirmationVersionInput:
    confirmation_id: RecordId
    version_id: RecordVersionId
    reassessment_version_id: RecordVersionId
    decision_version_id: RecordVersionId
    configuration_version_id: RecordVersionId
    boundary_snapshot_version_id: RecordVersionId
    authority_basis_version_id: RecordVersionId
    confirmer_actor_id: RecordId
    trigger_version_ids: tuple[RecordVersionId, ...]
    reviewed_basis_version_ids: tuple[RecordVersionId, ...]
    rationale: str
    effective_at: datetime
    knowledge_cutoff: datetime
    reviewed_domains: dict[str, tuple[str, ...]]
    next_trigger_learning_references: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ReassessmentCompletionResult:
    completed: bool
    status: ReassessmentStatus
    outcome_version_id: RecordVersionId
    reason: str


@dataclass(frozen=True, slots=True)
class SuccessorDecisionCompletionRequest:
    reassessment_version_id: RecordVersionId
    predecessor_decision_version_id: RecordVersionId
    successor_boundary: BoundarySnapshotVersionInput
    successor_decision: DecisionVersionInput
    authorization_basis: DecisionAuthorizationBasisVersionInput
    effective_at: datetime
    knowledge_cutoff: datetime
