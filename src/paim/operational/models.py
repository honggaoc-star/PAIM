"""Typed values for the bounded Increment 8 local operational boundary."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path

from paim.integrity import RecordId, RecordVersionId, require_utc
from paim.integrity.records import JsonValue


class OperationalError(RuntimeError):
    """Base error for local operational behavior."""


class ConfigurationError(OperationalError):
    """Required local configuration is missing or unsafe."""


class AuthenticationFailed(OperationalError):
    """Credentials did not establish one enabled local principal."""


class AccessDenied(OperationalError):
    """Software access policy denied an attempted operation."""


class IntakeConflict(OperationalError):
    """An adapter replay identity was reused with different material."""


class RecoveryRejected(OperationalError):
    """A backup or restore candidate failed verification."""


class UnsupportedCapability(OperationalError):
    """A capability is explicitly unavailable in PAIM v0.1."""


class PrincipalStatus(StrEnum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"
    REVOKED = "REVOKED"


class Permission(StrEnum):
    LOGIN = "LOGIN"
    CASE_READ = "CASE_READ"
    CONFIGURATION_READ = "CONFIGURATION_READ"
    COMMAND = "COMMAND"
    EXPORT = "EXPORT"
    DELIVERY = "DELIVERY"
    OPERATIONAL_ADMIN = "OPERATIONAL_ADMIN"


class ScopeType(StrEnum):
    GLOBAL = "GLOBAL"
    CASE = "CASE"
    CONFIGURATION = "CONFIGURATION"


class AccessEffect(StrEnum):
    ALLOW = "ALLOW"
    DENY = "DENY"


class AdapterType(StrEnum):
    VALUE = "VALUE"
    RISK = "RISK"
    EVIDENCE = "EVIDENCE"
    AUTHORITY = "AUTHORITY"
    EXTERNAL_TRIGGER = "EXTERNAL_TRIGGER"


class IntakeStatus(StrEnum):
    PROPOSED = "PROPOSED"
    QUARANTINED = "QUARANTINED"
    REJECTED = "REJECTED"


class DeliveryStatus(StrEnum):
    PENDING = "PENDING"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"


class ReadinessState(StrEnum):
    READY = "READY"
    DEGRADED = "DEGRADED"


@dataclass(frozen=True, slots=True)
class LocalConfiguration:
    database_path: Path
    credential_env: str
    intake_directory: Path
    spool_directory: Path
    export_directory: Path
    backup_directory: Path
    event_log_path: Path

    @property
    def database_url(self) -> str:
        return f"sqlite+pysqlite:///{self.database_path.resolve().as_posix()}"


@dataclass(frozen=True, slots=True)
class PrincipalVersion:
    principal_id: str
    sequence: int
    actor_id: RecordId | None
    status: PrincipalStatus
    credential_salt: str
    credential_verifier: str
    credential_iterations: int


@dataclass(frozen=True, slots=True)
class AuthenticatedSession:
    principal_id: str
    actor_id: RecordId | None
    correlation_id: str
    authenticated_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "authenticated_at", require_utc(self.authenticated_at))


@dataclass(frozen=True, slots=True)
class AccountableAssignmentView:
    """One exact current accountable Role Assignment safe for practitioner display."""

    assignment_version_id: str
    actor_name: str
    function: str

    @property
    def practitioner_label(self) -> str:
        return f"{self.actor_name} — {self.function}"


@dataclass(frozen=True, slots=True)
class AccountabilityCheck:
    """Authoritative browser-facing resolution without an inferred winner."""

    state: str
    assignments: tuple[AccountableAssignmentView, ...]


@dataclass(frozen=True, slots=True)
class AccessGrantInput:
    permission: Permission
    action: str
    scope_type: ScopeType
    scope_id: RecordId | RecordVersionId | None
    effect: AccessEffect


@dataclass(frozen=True, slots=True)
class SourceAccessGrantInput:
    """One durable exact-source visibility fact; never substantive authority."""

    action: str
    case_id: RecordId
    source_version_id: RecordVersionId
    source_family: str
    effect: AccessEffect
    effective_from: datetime
    effective_to: datetime | None = None
    configuration_id: RecordId | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "effective_from", require_utc(self.effective_from))
        if self.effective_to is not None:
            object.__setattr__(self, "effective_to", require_utc(self.effective_to))
            if self.effective_to <= self.effective_from:
                raise ValueError("source-access effective end must follow its start")
        if not self.action.strip() or not self.source_family.strip():
            raise ValueError("source-access action and family are required")


@dataclass(frozen=True, slots=True)
class IntakeEnvelope:
    adapter_type: AdapterType
    source_system: str
    source_object_id: str
    source_version: str | None
    source_effective_at: datetime
    payload: dict[str, JsonValue]
    replay_id: str
    mapper_rule_id: str
    mapper_rule_version: str
    target_case_id: RecordId | None = None
    target_configuration_id: RecordId | None = None
    management_context: str | None = None
    payload_reference: str | None = None
    unmapped_material: dict[str, JsonValue] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_effective_at", require_utc(self.source_effective_at))


@dataclass(frozen=True, slots=True)
class IntakeResult:
    intake_id: str
    status: IntakeStatus
    payload_checksum: str
    replayed: bool
    quarantine_reason: str | None
    supersedes_intake_id: str | None


@dataclass(frozen=True, slots=True)
class DeliveryResult:
    intent_id: str
    attempt_id: str
    status: DeliveryStatus
    spool_reference: str | None
    replayed: bool


@dataclass(frozen=True, slots=True)
class HealthReport:
    process_alive: bool
    database_reachable: bool
    schema_compatible: bool
    integrity_usable: bool
    foreign_keys_usable: bool
    directories_usable: bool
    spool_usable: bool
    projection_path_usable: bool
    state: ReadinessState
    reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class BackupManifest:
    application_version: str
    schema_revision: str
    created_at: datetime
    source_database_label: str
    backup_file: str
    backup_checksum: str
    backup_size: int
    source_high_water_us: int | None
    included_derived_outputs: bool
    record_counts: dict[str, int]
    operator_principal_id: str
    audit_event_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "created_at", require_utc(self.created_at))


UNSUPPORTED_CAPABILITIES: frozenset[str] = frozenset(
    {
        "OBSERVATION_RECORD",
        "OBSERVATION_AUTOMATION",
        "TELEMETRY_TO_EVIDENCE",
        "TELEMETRY_TO_TRIGGER",
        "TELEMETRY_TO_REGISTER",
        "OPERATING_STATE_RANKING",
        "OPERATING_STATE_STRENGTH_INFERENCE",
        "SEMANTIC_DEPENDENCY_MATCHING_AUTHORITY",
        "LIVE_PROVIDER_INTEGRATION",
        "GENERIC_WORKFLOW_ENGINE",
        "CROSS_CASE_AUTHORITY_TRANSFER",
        "GENERIC_REGISTER_RESOLUTION",
        "DISTRIBUTED_PRODUCTION_TOPOLOGY",
    }
)
