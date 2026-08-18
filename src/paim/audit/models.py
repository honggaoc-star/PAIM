"""Append-only authoritative audit facts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from paim.integrity.ids import AuditId, CommandId, RecordId, RecordVersionId
from paim.integrity.time import require_utc


class ActorResolution(StrEnum):
    PROVIDED = "provided"
    UNRESOLVED = "unresolved"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True, slots=True)
class AuditFact:
    audit_id: AuditId
    principal_id: str
    actor_id: str | None
    actor_resolution: ActorResolution
    operation: str
    result: str
    command_id: CommandId
    idempotency_scope: str
    idempotency_key: str
    correlation_id: str | None
    causation_id: str | None
    target_record_id: RecordId
    affected_version_ids: tuple[RecordVersionId, ...]
    expected_precondition: str
    observed_precondition: str
    effective_at: datetime
    recorded_at: datetime
    reason_outcomes: tuple[str, ...]
    request_digest: str

    def __post_init__(self) -> None:
        if self.actor_resolution is ActorResolution.PROVIDED and self.actor_id is None:
            raise ValueError("provided actor resolution requires an actor ID")
        if self.actor_resolution is not ActorResolution.PROVIDED and self.actor_id is not None:
            raise ValueError("unresolved/not-applicable actor attribution cannot carry an actor ID")
        object.__setattr__(self, "effective_at", require_utc(self.effective_at))
        object.__setattr__(self, "recorded_at", require_utc(self.recorded_at))
