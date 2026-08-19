"""Typed Increment 7 Shared Dependency and Management Register values."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from paim.integrity import EffectiveInterval, RecordId, RecordVersionId
from paim.integrity.records import JsonValue, RelationshipType


class SharedDependencyAccountabilityFunction(StrEnum):
    DETERMINER = "Shared Dependency Determiner"


class EquivalenceOutcome(StrEnum):
    EQUIVALENT = "EQUIVALENT"
    NOT_EQUIVALENT = "NOT_EQUIVALENT"
    INDETERMINATE = "INDETERMINATE"


class RegisterLifecycle(StrEnum):
    CURRENT_ATTENTION = "CURRENT_ATTENTION"
    CURRENT_CONFLICT = "CURRENT_CONFLICT"
    CURRENT_INFORMATIONAL = "CURRENT_INFORMATIONAL"
    RESOLVED_HISTORICAL = "RESOLVED_HISTORICAL"
    SUPERSEDED_HISTORICAL = "SUPERSEDED_HISTORICAL"
    WITHDRAWN_OR_INELIGIBLE_HISTORICAL = "WITHDRAWN_OR_INELIGIBLE_HISTORICAL"
    PROJECTION_STALE_OR_INCONSISTENT = "PROJECTION_STALE_OR_INCONSISTENT"


class SourceDisposition(StrEnum):
    ATTENTION = "ATTENTION"
    INFORMATIONAL = "INFORMATIONAL"
    RESOLVED = "RESOLVED"
    SUPERSEDED = "SUPERSEDED"
    WITHDRAWN_OR_INELIGIBLE = "WITHDRAWN_OR_INELIGIBLE"


class ProjectionConsistency(StrEnum):
    CURRENT = "CURRENT"
    STALE = "STALE"
    INCONSISTENT = "INCONSISTENT"


class RegisterAction(StrEnum):
    ASSIGN_OWNER = "ASSIGN_OWNER"
    ACKNOWLEDGE = "ACKNOWLEDGE"
    READ = "READ"
    SNOOZE = "SNOOZE"
    DEFER = "DEFER"
    ACCEPT_RESIDUAL_CONCERN = "ACCEPT_RESIDUAL_CONCERN"
    LINK_SHARED_DEPENDENCY = "LINK_SHARED_DEPENDENCY"
    LINK_DUPLICATE = "LINK_DUPLICATE"
    CREATE_TRIGGER = "CREATE_TRIGGER"
    CREATE_REASSESSMENT = "CREATE_REASSESSMENT"
    CREATE_OR_MODIFY_DECISION = "CREATE_OR_MODIFY_DECISION"
    CREATE_OR_MODIFY_INTERVENTION = "CREATE_OR_MODIFY_INTERVENTION"
    MARK_RESOLVED = "MARK_RESOLVED"


@dataclass(frozen=True, slots=True)
class SharedDependencyVersionInput:
    dependency_id: RecordId
    version_id: RecordVersionId
    dependency_kind: str
    purpose: str
    declared_scope: str
    organizational_context: str | None
    provenance: dict[str, JsonValue]
    rationale: str
    effective: EffectiveInterval
    withdrawn: bool = False
    expected_version_id: RecordVersionId | None = None
    relationship_type: RelationshipType = RelationshipType.SUPERSESSION
    relationship_reason: str | None = None


@dataclass(frozen=True, slots=True)
class DependencyCandidateMember:
    source_family: str
    source_record_id: RecordId
    source_version_id: RecordVersionId
    dependency_kind: str


@dataclass(frozen=True, slots=True)
class DependencyCandidateSetVersionInput:
    candidate_set_id: RecordId
    version_id: RecordVersionId
    members: tuple[DependencyCandidateMember, ...]
    dependency_kind: str
    equivalence_scope: str
    purpose: str
    organizational_context: str | None
    provenance: dict[str, JsonValue]
    rationale: str
    effective: EffectiveInterval
    withdrawn: bool = False
    expected_version_id: RecordVersionId | None = None
    relationship_type: RelationshipType = RelationshipType.SUPERSESSION
    relationship_reason: str | None = None


@dataclass(frozen=True, slots=True)
class SharedDependencyMechanismVersionInput:
    mechanism_id: RecordId
    version_id: RecordVersionId
    target_type: str
    target_id: str
    accountable_actor_id: RecordId
    rule_id: str
    rule_version: str
    authority_source: str
    limits: tuple[str, ...]
    effective: EffectiveInterval
    expected_version_id: RecordVersionId | None = None
    relationship_type: RelationshipType = RelationshipType.SUPERSESSION
    relationship_reason: str | None = None


@dataclass(frozen=True, slots=True)
class EquivalenceDeterminationVersionInput:
    determination_id: RecordId
    version_id: RecordVersionId
    candidate_set_version_id: RecordVersionId
    shared_dependency_version_id: RecordVersionId | None
    dependency_kind: str
    equivalence_scope: str
    outcome: EquivalenceOutcome
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
class SharedDependencyAccountabilityFound:
    assignment_version_id: RecordVersionId | None
    mechanism_version_id: RecordVersionId | None
    actor_id: RecordId


@dataclass(frozen=True, slots=True)
class SharedDependencyAccountabilityNotEstablished:
    reason: str = "SHARED DEPENDENCY ACCOUNTABILITY NOT ESTABLISHED"


@dataclass(frozen=True, slots=True)
class SharedDependencyAccountabilityConflict:
    candidate_version_ids: frozenset[RecordVersionId]
    reason: str = "SHARED DEPENDENCY ACCOUNTABILITY CONFLICT — UNRESOLVED"


type SharedDependencyAccountability = (
    SharedDependencyAccountabilityFound
    | SharedDependencyAccountabilityNotEstablished
    | SharedDependencyAccountabilityConflict
)


@dataclass(frozen=True, slots=True)
class EquivalenceDeterminationFound:
    version_id: RecordVersionId
    outcome: EquivalenceOutcome
    shared_dependency_version_id: RecordVersionId | None


@dataclass(frozen=True, slots=True)
class EquivalenceDeterminationNotEstablished:
    reason: str = "SHARED DEPENDENCY EQUIVALENCE NOT ESTABLISHED"


@dataclass(frozen=True, slots=True)
class EquivalenceDeterminationConflict:
    version_ids: frozenset[RecordVersionId]
    reason: str = "SHARED DEPENDENCY EQUIVALENCE CONFLICT — UNRESOLVED"


type EquivalenceDeterminationSelection = (
    EquivalenceDeterminationFound
    | EquivalenceDeterminationNotEstablished
    | EquivalenceDeterminationConflict
)


@dataclass(frozen=True, slots=True)
class RegisterConcernKey:
    case_id: RecordId
    configuration_id: RecordId | None
    concern_kind: str
    source_family: str
    source_record_id: RecordId

    def canonical(self) -> str:
        configuration = str(self.configuration_id) if self.configuration_id else "NOT_ESTABLISHED"
        return (
            f"case:{self.case_id}|configuration:{configuration}|kind:{self.concern_kind}|"
            f"family:{self.source_family}|record:{self.source_record_id}"
        )


@dataclass(frozen=True, slots=True)
class RegisterSourceSelection:
    key: RegisterConcernKey
    selected_source_version_ids: tuple[RecordVersionId, ...]
    disposition: SourceDisposition
    source_labels: tuple[str, ...] = ()
    due_at: datetime | None = None
    blocker_present: bool = False
    dependency_record_id: RecordId | None = None
    dependency_version_id: RecordVersionId | None = None


@dataclass(frozen=True, slots=True)
class RegisterQuery:
    case_ids: frozenset[RecordId]
    configuration_ids: frozenset[RecordId]
    effective_at: datetime
    known_at: datetime | None
    rule_id: str
    rule_version: str
    access_context: str
    accessible_case_ids: frozenset[RecordId]
    lifecycle_filter: frozenset[RegisterLifecycle] = frozenset()
    order_by: tuple[str, ...] = ("stable_identity",)
    processed_watermark: datetime | None = None


@dataclass(frozen=True, slots=True)
class RegisterConcernEntry:
    key: RegisterConcernKey
    lifecycle: RegisterLifecycle
    selected_source_version_ids: tuple[RecordVersionId, ...]
    source_labels: tuple[str, ...]
    due_at: datetime | None
    blocker_present: bool
    dependency_record_id: RecordId | None
    dependency_version_id: RecordVersionId | None


@dataclass(frozen=True, slots=True)
class SharedDependencyGroup:
    dependency_record_id: RecordId
    dependency_version_ids: frozenset[RecordVersionId]
    constituent_keys: tuple[RegisterConcernKey, ...]
    visible_case_ids: frozenset[RecordId]
    visible_configuration_ids: frozenset[RecordId]
    concern_counts: tuple[tuple[str, int], ...]
    lifecycle_counts: tuple[tuple[RegisterLifecycle, int], ...]
    unresolved_count: int
    conflict_count: int
    blocker_present: bool
    visible_constituent_count: int
    global_constituent_count: int | None
    access_filtered: bool


@dataclass(frozen=True, slots=True)
class RegisterView:
    entries: tuple[RegisterConcernEntry, ...]
    groups: tuple[SharedDependencyGroup, ...]
    generated_at: datetime
    effective_at: datetime
    known_at: datetime
    rule_id: str
    rule_version: str
    source_high_water: datetime | None
    processed_watermark: datetime | None
    consistency: ProjectionConsistency
    access_context: str
    filters: tuple[str, ...]
    ordering: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RegisterManifest:
    manifest_id: str
    output_kind: str
    content_json: str
    checksum: str
    generated_at: datetime


@dataclass(frozen=True, slots=True)
class NotificationIntent:
    intent_id: str
    manifest_id: str
    concern_key: str
    concern_lifecycle: RegisterLifecycle
    channel: str
    recipient_scope: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class RegisterActionLaunch:
    action: RegisterAction
    authoritative: bool
    owning_family: str
    command_contract: str
    source_version_ids: tuple[RecordVersionId, ...]
    launch_context: str
