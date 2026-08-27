"""Prospective continuing-Case values for Gate 8 Slice B."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from paim.integrity.ids import CommandId, RecordId, RecordVersionId
from paim.integrity.records import JsonValue
from paim.integrity.semantics import ExactContextSet, SemanticContractRef
from paim.integrity.time import require_utc


class ContinuityStatus(StrEnum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    SUPERSEDED = "SUPERSEDED"


class DeterminationKind(StrEnum):
    SAME_OR_NEW_CASE = "SAME_OR_NEW_CASE"
    CASE_CLOSURE = "CASE_CLOSURE"
    CASE_REOPENING = "CASE_REOPENING"
    CASE_SUPERSESSION = "CASE_SUPERSESSION"


class DeterminationOutcome(StrEnum):
    SAME_CASE = "SAME_CASE"
    NEW_CASE_REQUIRED = "NEW_CASE_REQUIRED"
    CLOSE = "CLOSE"
    REMAIN_OPEN = "REMAIN_OPEN"
    REOPEN_SAME_CASE = "REOPEN_SAME_CASE"
    REMAIN_CLOSED = "REMAIN_CLOSED"
    SUPERSEDE_WITH_SUCCESSOR = "SUPERSEDE_WITH_SUCCESSOR"
    DO_NOT_SUPERSEDE = "DO_NOT_SUPERSEDE"


class ContinuitySelectionKind(StrEnum):
    ONE = "ONE"
    ABSENT = "CASE CONTINUITY STATUS NOT ESTABLISHED"
    CONFLICT = "CASE CONTINUITY STATUS CONFLICT — UNRESOLVED"
    NOT_SAFELY_AVAILABLE = "CASE CONTINUITY STATUS NOT SAFELY AVAILABLE"


@dataclass(frozen=True, slots=True)
class ContinuitySelection:
    kind: ContinuitySelectionKind
    version_ids: tuple[RecordVersionId, ...]
    status: ContinuityStatus | None = None


@dataclass(frozen=True, slots=True)
class ClosureGuardManifest:
    """Exact available-family closure facts; no future-family truth is fabricated."""

    operation_continues: bool
    required_version_ids: tuple[RecordVersionId, ...]
    unresolved_item_treatment: str
    retention_basis: str

    def __post_init__(self) -> None:
        if not self.unresolved_item_treatment.strip() or not self.retention_basis.strip():
            raise ValueError("closure treatment and retention basis are required")


@dataclass(frozen=True, slots=True)
class CommandIdentity:
    command_id: CommandId
    idempotency_scope: str
    idempotency_key: str
    principal_id: str
    actor_id: RecordId

    def __post_init__(self) -> None:
        if not self.idempotency_scope or not self.idempotency_key:
            raise ValueError("idempotency identity is required")


@dataclass(frozen=True, slots=True)
class OpeningFacts:
    case_id: RecordId
    case_version_id: RecordVersionId
    configuration_id: RecordId
    configuration_version_id: RecordVersionId
    designation_record_id: RecordId
    designation_version_id: RecordVersionId
    status_record_id: RecordId
    status_version_id: RecordVersionId
    responsibility_record_id: RecordId
    responsibility_version_id: RecordVersionId
    assignment_basis_record_id: RecordId
    assignment_basis_version_id: RecordVersionId
    assignment_record_id: RecordId
    assignment_version_id: RecordVersionId

    @classmethod
    def new(cls) -> OpeningFacts:
        return cls(
            RecordId.new(),
            RecordVersionId.new(),
            RecordId.new(),
            RecordVersionId.new(),
            RecordId.new(),
            RecordVersionId.new(),
            RecordId.new(),
            RecordVersionId.new(),
            RecordId.new(),
            RecordVersionId.new(),
            RecordId.new(),
            RecordVersionId.new(),
            RecordId.new(),
            RecordVersionId.new(),
        )


@dataclass(frozen=True, slots=True)
class OpenCaseCommand:
    identity: CommandIdentity
    facts: OpeningFacts
    contract: SemanticContractRef
    context: ExactContextSet
    title: str
    bounded_use: str
    management_question: str
    configuration_content: dict[str, JsonValue]
    configuration_maturity: str
    configuration_purpose: str
    authority_source_version_id: RecordVersionId
    assignment_authority_source_version_id: RecordVersionId
    effective_at: datetime
    knowledge_cutoff: datetime
    initiation_scope: str | None = None
    ai_profile: dict[str, JsonValue] | None = None
    dependencies: tuple[dict[str, JsonValue], ...] = ()

    def __post_init__(self) -> None:
        require_utc(self.effective_at)
        require_utc(self.knowledge_cutoff)
        if (
            not self.title.strip()
            or not self.bounded_use.strip()
            or not self.management_question.strip()
        ):
            raise ValueError("Case title, bounded use, and management question are required")
        if self.ai_profile is not None and not str(self.ai_profile.get("name", "")).strip():
            raise ValueError("AI name is required when an AI profile is supplied")
        if any(not str(item.get("name", "")).strip() for item in self.dependencies):
            raise ValueError("each dependency requires a name")


class CaseInitiationAuthorityState(StrEnum):
    ACTIVE = "ACTIVE"
    WITHDRAWN = "WITHDRAWN"


@dataclass(frozen=True, slots=True)
class CaseInitiationAuthorityCommand:
    """Record an externally grounded organizational mandate before a Case exists."""

    identity: CommandIdentity
    record_id: RecordId
    version_id: RecordVersionId
    authorized_actor_id: RecordId
    organization_scope: str
    allowed_use_prefixes: tuple[str, ...]
    provenance: dict[str, JsonValue]
    state: CaseInitiationAuthorityState
    effective_at: datetime
    contract: SemanticContractRef
    context: ExactContextSet
    expected_version_id: RecordVersionId | None = None

    def __post_init__(self) -> None:
        require_utc(self.effective_at)
        if not self.organization_scope.strip() or not self.provenance:
            raise ValueError("organizational scope and authoritative provenance are required")
        if any(not value.strip() for value in self.allowed_use_prefixes):
            raise ValueError("allowed management-use prefixes must be non-empty")


@dataclass(frozen=True, slots=True)
class MinimalOpenCaseCommand:
    """Natural practitioner request; all PAIM identities are generated internally."""

    identity: CommandIdentity
    contract: SemanticContractRef
    organization_scope: str
    title: str
    bounded_use: str
    management_question: str
    configuration_content: dict[str, JsonValue]
    configuration_maturity: str
    configuration_purpose: str
    effective_at: datetime
    knowledge_cutoff: datetime
    ai_profile: dict[str, JsonValue] | None = None
    dependencies: tuple[dict[str, JsonValue], ...] = ()

    def __post_init__(self) -> None:
        require_utc(self.effective_at)
        require_utc(self.knowledge_cutoff)
        if not all(
            value.strip()
            for value in (
                self.organization_scope,
                self.title,
                self.bounded_use,
                self.management_question,
            )
        ):
            raise ValueError("minimal Case initiation fields are required")
        if self.ai_profile is not None and not str(self.ai_profile.get("name", "")).strip():
            raise ValueError("AI name is required when an AI profile is supplied")
        if any(not str(item.get("name", "")).strip() for item in self.dependencies):
            raise ValueError("each dependency requires a name")


@dataclass(frozen=True, slots=True)
class TransitionFacts:
    determination_record_id: RecordId
    determination_version_id: RecordVersionId
    status_version_id: RecordVersionId

    @classmethod
    def new(cls) -> TransitionFacts:
        return cls(RecordId.new(), RecordVersionId.new(), RecordVersionId.new())


@dataclass(frozen=True, slots=True)
class TransitionCaseCommand:
    identity: CommandIdentity
    facts: TransitionFacts
    contract: SemanticContractRef
    context: ExactContextSet
    case_id: RecordId
    status_record_id: RecordId
    expected_status_version_id: RecordVersionId
    expected_status: ContinuityStatus
    kind: DeterminationKind
    outcome: DeterminationOutcome
    responsibility_version_id: RecordVersionId
    assignment_version_id: RecordVersionId
    authority_basis_version_id: RecordVersionId
    rationale: str
    factors: tuple[str, ...]
    effective_at: datetime
    knowledge_cutoff: datetime
    closure_manifest: ClosureGuardManifest | None = None
    successor_case_id: RecordId | None = None

    def __post_init__(self) -> None:
        require_utc(self.effective_at)
        require_utc(self.knowledge_cutoff)
        if not self.rationale.strip() or not self.factors:
            raise ValueError("accountable rationale and factors are required")


@dataclass(frozen=True, slots=True)
class ConfigurationSuccessorFacts:
    determination_record_id: RecordId
    determination_version_id: RecordVersionId
    configuration_id: RecordId
    configuration_version_id: RecordVersionId
    designation_version_id: RecordVersionId
    relationship_id: str


@dataclass(frozen=True, slots=True)
class ConfigurationSuccessorCommand:
    identity: CommandIdentity
    facts: ConfigurationSuccessorFacts
    contract: SemanticContractRef
    context: ExactContextSet
    case_id: RecordId
    status_record_id: RecordId
    expected_status_version_id: RecordVersionId
    predecessor_configuration_id: RecordId
    predecessor_configuration_version_id: RecordVersionId
    designation_record_id: RecordId
    expected_designation_version_id: RecordVersionId
    configuration_content: dict[str, JsonValue]
    configuration_maturity: str
    configuration_purpose: str
    responsibility_version_id: RecordVersionId
    assignment_version_id: RecordVersionId
    authority_basis_version_id: RecordVersionId
    rationale: str
    factors: tuple[str, ...]
    effective_at: datetime
    knowledge_cutoff: datetime

    def __post_init__(self) -> None:
        require_utc(self.effective_at)
        require_utc(self.knowledge_cutoff)


@dataclass(frozen=True, slots=True)
class LegacyLifecycleView:
    source_version_ids: tuple[RecordVersionId, ...]
    phase_labels: tuple[str, ...]
    limitation: str = "LEGACY PHASES ARE NOT PROSPECTIVE CONTINUITY STATUS"
