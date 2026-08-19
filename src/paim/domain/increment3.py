"""Typed Increment 3 Evidence, Authority, Applicability, and analytical-lane values."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from paim.integrity import EffectiveInterval, RecordId, RecordVersionId
from paim.integrity.records import JsonValue, RelationshipType


class EvidenceClassification(StrEnum):
    OBSERVED = "observed"
    SUPPORTED_INFERENCE = "supported_inference"
    ESTIMATE = "estimate"
    ASSUMPTION = "assumption"
    UNKNOWN = "unknown"


class EvidenceAttention(StrEnum):
    CURRENT = "current"
    REFRESH_REQUIRED = "refresh_required"
    STALE = "stale"


class ApplicabilityTargetType(StrEnum):
    MANAGED_CONFIGURATION_VERSION = "managed_configuration_version"
    VALUE_INPUT_VERSION = "value_input_version"
    RISK_INPUT_VERSION = "risk_input_version"
    AUTHORITY_RECORD_VERSION = "authority_record_version"
    AUTHORITY_GAP = "authority_gap"


class ApplicabilityOutcome(StrEnum):
    APPLICABLE = "APPLICABLE"
    CONDITIONALLY_APPLICABLE = "CONDITIONALLY_APPLICABLE"
    PARTIALLY_APPLICABLE = "PARTIALLY_APPLICABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    INDETERMINATE = "INDETERMINATE"


class AnalyticalLane(StrEnum):
    VALUE = "VALUE"
    RISK = "RISK"


class CandidateDisposition(StrEnum):
    NON_SELECTED = "NON_SELECTED"
    DISSENTING = "DISSENTING"
    REJECTED_FOR_USE = "REJECTED_FOR_USE"
    WITHDRAWN = "WITHDRAWN"
    SUPERSEDED = "SUPERSEDED"


class FitnessOutcome(StrEnum):
    SUPPORTABLE = "SUPPORTABLE"
    BLOCKED = "BLOCKED"


class AuthorityGapOutcome(StrEnum):
    UNRESOLVED = "UNRESOLVED"
    REQUIREMENT_ESTABLISHED = "REQUIREMENT_ESTABLISHED"
    PROHIBITION_ESTABLISHED = "PROHIBITION_ESTABLISHED"
    PERMISSION_OR_AUTHORITY_ESTABLISHED = "PERMISSION_OR_AUTHORITY_ESTABLISHED"
    NOT_APPLICABLE_TO_BOUNDED_DECISION = "NOT_APPLICABLE_TO_BOUNDED_DECISION"
    AUTHORIZED_REFRAMING_NO_LONGER_MATERIAL = "AUTHORIZED_REFRAMING_NO_LONGER_MATERIAL"


@dataclass(frozen=True, slots=True)
class EvidenceVersionInput:
    evidence_id: RecordId
    version_id: RecordVersionId
    case_id: RecordId | None
    configuration_id: RecordId | None
    configuration_version_id: RecordVersionId | None
    classification: EvidenceClassification
    source: str
    provenance: dict[str, JsonValue]
    content: dict[str, JsonValue]
    observed_as_of: datetime | None
    effective: EffectiveInterval
    attention: EvidenceAttention = EvidenceAttention.CURRENT
    affected_use_references: tuple[str, ...] = ()
    expected_version_id: RecordVersionId | None = None
    relationship_type: RelationshipType = RelationshipType.SUPERSESSION
    relationship_reason: str | None = None


@dataclass(frozen=True, slots=True)
class AuthorityVersionInput:
    authority_id: RecordId
    version_id: RecordVersionId
    case_id: RecordId | None
    configuration_id: RecordId | None
    configuration_version_id: RecordVersionId | None
    category: str
    source: str
    provenance: dict[str, JsonValue]
    scope: str
    requirement: str
    content: dict[str, JsonValue]
    effective: EffectiveInterval
    evidence_version_ids: tuple[RecordVersionId, ...] = ()
    expected_version_id: RecordVersionId | None = None
    relationship_type: RelationshipType = RelationshipType.SUPERSESSION
    relationship_reason: str | None = None


@dataclass(frozen=True, slots=True)
class AuthorityGapVersionInput:
    gap_id: RecordId
    version_id: RecordVersionId
    case_id: RecordId
    configuration_id: RecordId
    configuration_version_id: RecordVersionId
    question_id: str
    question: str
    scope: str
    rationale: str
    provenance: dict[str, JsonValue]
    effective: EffectiveInterval
    evidence_version_ids: tuple[RecordVersionId, ...] = ()
    expected_version_id: RecordVersionId | None = None
    relationship_type: RelationshipType = RelationshipType.SUPERSESSION
    relationship_reason: str | None = None
    outcome: AuthorityGapOutcome = AuthorityGapOutcome.UNRESOLVED
    resolution_linkage: str | None = None


@dataclass(frozen=True, slots=True)
class EvidenceApplicabilityVersionInput:
    applicability_id: RecordId
    version_id: RecordVersionId
    evidence_id: RecordId
    evidence_version_id: RecordVersionId
    target_type: ApplicabilityTargetType
    target_id: str
    target_version_id: RecordVersionId | None
    purpose: str
    assessed_scope: str
    case_id: RecordId | None
    configuration_id: RecordId | None
    configuration_version_id: RecordVersionId | None
    outcome: ApplicabilityOutcome
    conditions: tuple[str, ...]
    limitations: tuple[str, ...]
    rationale: str
    assessor_actor_id: RecordId
    accountable_assignment_version_id: RecordVersionId | None
    accountable_mechanism: str | None
    effective: EffectiveInterval
    affected_use_references: tuple[str, ...] = ()
    displaced_applicability_version_ids: tuple[RecordVersionId, ...] = ()
    expected_version_id: RecordVersionId | None = None
    relationship_type: RelationshipType = RelationshipType.SUPERSESSION
    relationship_reason: str | None = None


@dataclass(frozen=True, slots=True)
class AnalyticalInputVersionInput:
    input_id: RecordId
    version_id: RecordVersionId
    lane: AnalyticalLane
    case_id: RecordId
    configuration_id: RecordId
    configuration_version_id: RecordVersionId
    purpose: str
    finding: str
    boundary: str
    uncertainties: tuple[str, ...]
    implication: str
    provenance: dict[str, JsonValue]
    evidence_version_ids: tuple[RecordVersionId, ...]
    effective: EffectiveInterval
    expected_version_id: RecordVersionId | None = None
    relationship_type: RelationshipType = RelationshipType.SUPERSESSION
    relationship_reason: str | None = None


@dataclass(frozen=True, slots=True)
class CandidateDispositionVersionInput:
    disposition_id: RecordId
    version_id: RecordVersionId
    input_version_id: RecordVersionId
    lane: AnalyticalLane
    configuration_version_id: RecordVersionId
    use_context: str
    purpose: str
    disposition: CandidateDisposition
    rationale: str
    effective: EffectiveInterval
    accountable_assignment_version_id: RecordVersionId | None = None
    accountable_mechanism: str | None = None
    expected_version_id: RecordVersionId | None = None
    relationship_reason: str | None = None


@dataclass(frozen=True, slots=True)
class MaterialEvidenceBasisInput:
    evidence_version_id: RecordVersionId
    applicability_version_id: RecordVersionId
    role: str
    required_support: bool
    claimed_scope: str


@dataclass(frozen=True, slots=True)
class LaneFitnessVersionInput:
    fitness_id: RecordId
    version_id: RecordVersionId
    lane: AnalyticalLane
    input_version_id: RecordVersionId
    case_id: RecordId
    configuration_id: RecordId
    configuration_version_id: RecordVersionId
    use_context: str
    purpose: str
    outcome: FitnessOutcome
    rationale: str
    indeterminate_treatment: str | None
    decision_limiting: bool
    accountable_assignment_version_id: RecordVersionId | None
    accountable_mechanism: str | None
    material_evidence: tuple[MaterialEvidenceBasisInput, ...]
    effective: EffectiveInterval
    expected_version_id: RecordVersionId | None = None
    relationship_reason: str | None = None


@dataclass(frozen=True, slots=True)
class AcceptanceSelectionVersionInput:
    acceptance_id: RecordId
    version_id: RecordVersionId
    lane: AnalyticalLane
    input_id: RecordId
    input_version_id: RecordVersionId
    case_id: RecordId
    configuration_id: RecordId
    configuration_version_id: RecordVersionId
    use_context: str
    purpose: str
    rationale: str
    accountable_assignment_version_id: RecordVersionId | None
    accountable_mechanism: str | None
    fitness_version_id: RecordVersionId
    material_applicability_version_ids: tuple[RecordVersionId, ...]
    effective: EffectiveInterval
    displaced_acceptance_version_ids: tuple[RecordVersionId, ...] = ()
    expected_version_id: RecordVersionId | None = None
    relationship_reason: str | None = None


@dataclass(frozen=True, slots=True)
class EvidenceApplicabilityDetail:
    version_id: RecordVersionId
    applicability_id: RecordId
    evidence_version_id: RecordVersionId
    target_type: ApplicabilityTargetType
    target_id: str
    target_version_id: RecordVersionId | None
    case_id: RecordId | None
    configuration_version_id: RecordVersionId | None
    purpose: str
    assessed_scope: str
    outcome: ApplicabilityOutcome
    accountable_assignment_version_id: RecordVersionId | None
    accountable_mechanism: str | None


@dataclass(frozen=True, slots=True)
class AuthorityApplicabilityContext:
    case_id: RecordId | None
    configuration_id: RecordId | None
    configuration_version_id: RecordVersionId | None
    authority_scope: str


@dataclass(frozen=True, slots=True)
class AnalyticalInputDetail:
    version_id: RecordVersionId
    input_id: RecordId
    lane: AnalyticalLane
    case_id: RecordId
    configuration_id: RecordId
    configuration_version_id: RecordVersionId
    purpose: str
    implication: str


@dataclass(frozen=True, slots=True)
class LaneFitnessDetail:
    version_id: RecordVersionId
    lane: AnalyticalLane
    input_version_id: RecordVersionId
    configuration_version_id: RecordVersionId
    use_context: str
    purpose: str
    outcome: FitnessOutcome
    rationale: str
    indeterminate_treatment: str | None
    decision_limiting: bool


@dataclass(frozen=True, slots=True)
class AcceptanceSelectionDetail:
    version_id: RecordVersionId
    acceptance_id: RecordId
    lane: AnalyticalLane
    input_version_id: RecordVersionId
    case_id: RecordId
    configuration_id: RecordId
    configuration_version_id: RecordVersionId
    use_context: str
    purpose: str
    fitness_version_id: RecordVersionId


@dataclass(frozen=True, slots=True)
class ApplicabilityFound:
    applicability_version_id: RecordVersionId


@dataclass(frozen=True, slots=True)
class ApplicabilityNotEstablished:
    reason: str = "APPLICABILITY NOT ESTABLISHED"


@dataclass(frozen=True, slots=True)
class ApplicabilityConflict:
    applicability_version_ids: frozenset[RecordVersionId]
    reason: str = "EVIDENCE APPLICABILITY CONFLICT — UNRESOLVED"


type ApplicabilitySelection = (
    ApplicabilityFound | ApplicabilityNotEstablished | ApplicabilityConflict
)


@dataclass(frozen=True, slots=True)
class InputSelectionFound:
    input_version_id: RecordVersionId
    acceptance_version_id: RecordVersionId


@dataclass(frozen=True, slots=True)
class InputSelectionNotEstablished:
    reason: str = "INPUT SELECTION NOT ESTABLISHED"


@dataclass(frozen=True, slots=True)
class InputSelectionConflict:
    acceptance_version_ids: frozenset[RecordVersionId]
    input_version_ids: frozenset[RecordVersionId]
    reason: str = "INPUT SELECTION CONFLICT — UNRESOLVED"


type InputSelection = InputSelectionFound | InputSelectionNotEstablished | InputSelectionConflict


@dataclass(frozen=True, slots=True)
class AnalyticalHandoffReadiness:
    eligible: bool
    configuration_version_id: RecordVersionId | None
    value_selection: InputSelection
    risk_selection: InputSelection
    diagnostics: tuple[str, ...]
    authority_gap_version_ids: tuple[RecordVersionId, ...]
