"""Typed Increment 2 domain values and explicit resolution outcomes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from paim.audit import ActorResolution
from paim.integrity import CommandId, EffectiveInterval, RecordId, RecordVersionId
from paim.integrity.records import JsonValue


class CaseLifecycleState(StrEnum):
    OPEN = "open"
    CONFIGURATION_DEFINED = "configuration_defined"
    EVIDENCE_ANALYSIS = "evidence_analysis"
    READY_FOR_INTEGRATION = "ready_for_integration"


class ConfigurationMaturity(StrEnum):
    DRAFT = "draft"
    FINALIZED = "finalized"


class ConfigurationPurpose(StrEnum):
    CANDIDATE = "candidate"
    PROPOSED = "proposed"
    EXPERIMENTAL = "experimental"
    ALTERNATIVE = "alternative"
    FALLBACK = "fallback"


class RoleTargetType(StrEnum):
    ORGANIZATION = "organization"
    BUSINESS_UNIT = "business_unit"
    CASE = "case"
    CONFIGURATION = "configuration"
    DECISION = "decision"
    INTERVENTION = "intervention"
    AUTHORITY_DOMAIN = "authority_domain"


class DelegationEffect(StrEnum):
    NONE = "none"
    SUPPLEMENT = "supplement"
    TRANSFER = "transfer"
    RETAIN = "retain"


class DeterminationKind(StrEnum):
    MATERIALITY = "materiality"
    IDENTITY_CONTINUITY = "identity_continuity"


class DeterminationOutcome(StrEnum):
    MATERIAL = "material"
    NON_MATERIAL = "non_material"
    SAME_IDENTITY = "same_identity"
    NEW_IDENTITY = "new_identity"


@dataclass(frozen=True, slots=True)
class CommandMeta:
    command_id: CommandId
    idempotency_scope: str
    idempotency_key: str
    principal_id: str
    actor_id: str | None
    actor_resolution: ActorResolution
    correlation_id: str | None = None
    causation_id: str | None = None

    def __post_init__(self) -> None:
        if not self.idempotency_scope or not self.idempotency_key:
            raise ValueError("idempotency scope and key are required")
        if self.actor_resolution is ActorResolution.PROVIDED and self.actor_id is None:
            raise ValueError("provided actor resolution requires actor ID")
        if self.actor_resolution is not ActorResolution.PROVIDED and self.actor_id is not None:
            raise ValueError("unresolved/not-applicable actor cannot carry actor ID")


@dataclass(frozen=True, slots=True)
class CaseVersionInput:
    case_id: RecordId
    version_id: RecordVersionId
    title: str
    effective: EffectiveInterval
    expected_version_id: RecordVersionId | None = None
    relationship_reason: str | None = None


@dataclass(frozen=True, slots=True)
class ConfigurationVersionInput:
    configuration_id: RecordId
    version_id: RecordVersionId
    owning_case_id: RecordId
    maturity: ConfigurationMaturity
    purpose: ConfigurationPurpose
    content: dict[str, JsonValue]
    effective: EffectiveInterval
    expected_version_id: RecordVersionId | None = None
    relationship_reason: str | None = None


@dataclass(frozen=True, slots=True)
class ActorVersionInput:
    actor_id: RecordId
    version_id: RecordVersionId
    display_name: str
    effective: EffectiveInterval
    expected_version_id: RecordVersionId | None = None
    relationship_reason: str | None = None


@dataclass(frozen=True, slots=True)
class RoleAssignmentVersionInput:
    assignment_id: RecordId
    version_id: RecordVersionId
    paim_actor_id: RecordId
    role: str
    target_type: RoleTargetType
    target_id: str
    case_context_id: RecordId | None
    accountable: bool
    compatibility_key: str
    delegation_effect: DelegationEffect
    delegated_from_version_id: RecordVersionId | None
    effective: EffectiveInterval
    expected_version_id: RecordVersionId | None = None
    relationship_reason: str | None = None


@dataclass(frozen=True, slots=True)
class GoverningDesignationInput:
    designation_id: RecordId
    version_id: RecordVersionId
    case_id: RecordId
    configuration_version_id: RecordVersionId
    effective: EffectiveInterval
    accountable_assignment_version_id: RecordVersionId | None = None
    accountable_mechanism: str | None = None
    expected_version_id: RecordVersionId | None = None
    relationship_reason: str | None = None


@dataclass(frozen=True, slots=True)
class ConfigurationDeterminationInput:
    determination_id: RecordId
    version_id: RecordVersionId
    configuration_version_id: RecordVersionId
    kind: DeterminationKind
    outcome: DeterminationOutcome
    rationale: str
    effective: EffectiveInterval
    accountable_assignment_version_id: RecordVersionId | None = None
    accountable_mechanism: str | None = None
    expected_version_id: RecordVersionId | None = None
    relationship_reason: str | None = None


@dataclass(frozen=True, slots=True)
class CaseLinkInput:
    link_id: str
    source_case_id: RecordId
    target_case_id: RecordId
    relationship_type: str
    effective_at: datetime
    reason: str


@dataclass(frozen=True, slots=True)
class ConfigurationVersionContext:
    configuration_id: RecordId
    owning_case_id: RecordId
    maturity: str
    purpose: str


@dataclass(frozen=True, slots=True)
class RoleAssignmentDetail:
    version_id: RecordVersionId
    assignment_id: RecordId
    actor_id: RecordId
    role: str
    target_type: RoleTargetType
    target_id: str
    case_context_id: RecordId | None
    accountable: bool
    compatibility_key: str
    delegation_effect: DelegationEffect
    delegated_from_version_id: RecordVersionId | None


@dataclass(frozen=True, slots=True)
class GoverningDesignationDetail:
    version_id: RecordVersionId
    case_id: RecordId
    configuration_version_id: RecordVersionId


@dataclass(frozen=True, slots=True)
class GoverningConfigurationFound:
    designation_version_id: RecordVersionId
    configuration_version_id: RecordVersionId


@dataclass(frozen=True, slots=True)
class GoverningConfigurationAbsent:
    reason: str = "GOVERNING CONFIGURATION NOT ESTABLISHED"


@dataclass(frozen=True, slots=True)
class GoverningConfigurationConflict:
    designation_version_ids: frozenset[RecordVersionId]
    configuration_version_ids: frozenset[RecordVersionId]
    reason: str = "GOVERNING CONFIGURATION CONFLICT — UNRESOLVED"


type GoverningConfigurationSelection = (
    GoverningConfigurationFound | GoverningConfigurationAbsent | GoverningConfigurationConflict
)


@dataclass(frozen=True, slots=True)
class AccountabilityFound:
    assignment_version_id: RecordVersionId | None
    mechanism: str | None


@dataclass(frozen=True, slots=True)
class AccountabilityVacant:
    reason: str = "ACCOUNTABILITY NOT ESTABLISHED"


@dataclass(frozen=True, slots=True)
class AccountabilityConflict:
    assignment_version_ids: frozenset[RecordVersionId]
    reason: str = "ACCOUNTABILITY CONFLICT — UNRESOLVED"


type AccountabilityResolution = AccountabilityFound | AccountabilityVacant | AccountabilityConflict


@dataclass(frozen=True, slots=True)
class LifecycleTransitionResult:
    accepted: bool
    state: CaseLifecycleState
    reason: str
    status_event_id: str | None = None
