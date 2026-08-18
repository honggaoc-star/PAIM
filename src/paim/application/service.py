"""All-or-nothing semantic commit orchestration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from paim.audit.models import ActorResolution, AuditFact
from paim.integrity.commands import canonical_command_digest
from paim.integrity.ids import (
    AuditId,
    CommandId,
    EventId,
    RecordId,
    RecordVersionId,
    RelationshipId,
)
from paim.integrity.records import (
    FinalizedRecordVersion,
    JsonValue,
    RelationshipType,
    StatusEvent,
    VersionRelationship,
    canonical_json,
)
from paim.integrity.selection import (
    CurrentSelection,
    SelectionAbsent,
    SelectionConflict,
    SelectionFound,
    SelectionQuery,
)
from paim.integrity.time import Clock, EffectiveInterval, require_utc
from paim.persistence.ports import CommandOutcome, IdempotencyFact, IntegrityStore


class IdempotencyKeyReuseConflict(RuntimeError):
    """Same idempotency identity was reused for a different semantic command."""

    def __init__(self) -> None:
        super().__init__("IDEMPOTENCY KEY REUSE CONFLICT")


class StalePrecondition(RuntimeError):
    """Expected current/absence no longer matches authoritative state."""


@dataclass(frozen=True, slots=True)
class CommitVersionCommand:
    command_id: CommandId
    idempotency_scope: str
    idempotency_key: str
    record_id: RecordId
    version_id: RecordVersionId
    family: str
    scope: str
    content: dict[str, JsonValue]
    effective: EffectiveInterval
    precondition_at: datetime
    expected_version_id: RecordVersionId | None
    principal_id: str
    actor_id: str | None
    actor_resolution: ActorResolution
    creator: str
    relationship_type: RelationshipType | None = None
    relationship_reason: str | None = None
    end_predecessor_status: str | None = None
    correlation_id: str | None = None
    causation_id: str | None = None
    reason_outcomes: tuple[str, ...] = ("P0_INTEGRITY_VALID",)

    def __post_init__(self) -> None:
        if not self.idempotency_scope or not self.idempotency_key:
            raise ValueError("idempotency scope and key are required")
        if self.actor_resolution is ActorResolution.PROVIDED and self.actor_id is None:
            raise ValueError("provided actor resolution requires actor ID")
        if self.actor_resolution is not ActorResolution.PROVIDED and self.actor_id is not None:
            raise ValueError("unresolved/not-applicable actor cannot carry actor ID")
        if self.expected_version_id is None:
            if self.relationship_type is not None or self.end_predecessor_status is not None:
                raise ValueError("initial version cannot relate to or end an absent predecessor")
        elif self.relationship_type is None or not self.relationship_reason:
            raise ValueError("successor version requires relationship type and reason")
        object.__setattr__(self, "precondition_at", require_utc(self.precondition_at))

    def digest(self) -> str:
        payload: dict[str, JsonValue] = {
            "record_id": str(self.record_id),
            "version_id": str(self.version_id),
            "family": self.family,
            "scope": self.scope,
            "content": self.content,
            "effective_from": self.effective.start.isoformat(),
            "effective_to": self.effective.end.isoformat() if self.effective.end else None,
            "precondition_at": self.precondition_at.isoformat(),
            "expected_version_id": (
                str(self.expected_version_id) if self.expected_version_id is not None else None
            ),
            "principal_id": self.principal_id,
            "actor_id": self.actor_id,
            "actor_resolution": self.actor_resolution.value,
            "creator": self.creator,
            "relationship_type": (
                self.relationship_type.value if self.relationship_type is not None else None
            ),
            "relationship_reason": self.relationship_reason,
            "end_predecessor_status": self.end_predecessor_status,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "reason_outcomes": list(self.reason_outcomes),
        }
        return canonical_command_digest(payload)


@dataclass(frozen=True, slots=True)
class CommitStatusCommand:
    command_id: CommandId
    idempotency_scope: str
    idempotency_key: str
    record_id: RecordId
    target_version_id: RecordVersionId
    family: str
    scope: str
    precondition_at: datetime
    prior_status: str
    new_status: str
    effective_at: datetime
    basis: str
    principal_id: str
    actor_id: str | None
    actor_resolution: ActorResolution
    correlation_id: str | None = None
    causation_id: str | None = None
    reason_outcomes: tuple[str, ...] = ("P0_STATUS_EVENT_VALID",)

    def __post_init__(self) -> None:
        if not self.idempotency_scope or not self.idempotency_key:
            raise ValueError("idempotency scope and key are required")
        if self.actor_resolution is ActorResolution.PROVIDED and self.actor_id is None:
            raise ValueError("provided actor resolution requires actor ID")
        if self.actor_resolution is not ActorResolution.PROVIDED and self.actor_id is not None:
            raise ValueError("unresolved/not-applicable actor cannot carry actor ID")
        object.__setattr__(self, "precondition_at", require_utc(self.precondition_at))
        object.__setattr__(self, "effective_at", require_utc(self.effective_at))

    def digest(self) -> str:
        payload: dict[str, JsonValue] = {
            "record_id": str(self.record_id),
            "target_version_id": str(self.target_version_id),
            "family": self.family,
            "scope": self.scope,
            "precondition_at": self.precondition_at.isoformat(),
            "prior_status": self.prior_status,
            "new_status": self.new_status,
            "effective_at": self.effective_at.isoformat(),
            "basis": self.basis,
            "principal_id": self.principal_id,
            "actor_id": self.actor_id,
            "actor_resolution": self.actor_resolution.value,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "reason_outcomes": list(self.reason_outcomes),
        }
        return canonical_command_digest(payload)


def _observed_precondition(selection: CurrentSelection) -> str:
    if isinstance(selection, SelectionAbsent):
        return "ABSENT"
    if isinstance(selection, SelectionFound):
        return str(selection.candidate.version_id)
    assert isinstance(selection, SelectionConflict)
    identifiers = sorted(str(candidate.version_id) for candidate in selection.candidates)
    return "CONFLICT:" + ",".join(identifiers)


def _precondition_matches(expected: RecordVersionId | None, selection: CurrentSelection) -> bool:
    if expected is None:
        return isinstance(selection, SelectionAbsent)
    return isinstance(selection, SelectionFound) and selection.candidate.version_id == expected


class IntegrityApplicationService:
    """One synchronous application boundary for bounded authoritative writes."""

    def __init__(self, store: IntegrityStore, clock: Clock) -> None:
        self._store = store
        self._clock = clock

    def commit_version(
        self,
        command: CommitVersionCommand,
        *,
        failure_injector: Callable[[str], None] | None = None,
    ) -> CommandOutcome:
        digest = command.digest()
        recorded_at = self._clock.now()
        query = SelectionQuery(
            family=command.family,
            scope=command.scope,
            effective_at=command.precondition_at,
            known_at=recorded_at,
            record_id=command.record_id,
        )
        with self._store.semantic_transaction() as transaction:
            existing = transaction.get_idempotency(
                command.idempotency_scope, command.idempotency_key
            )
            if existing is not None:
                if existing.digest != digest:
                    raise IdempotencyKeyReuseConflict()
                return existing.outcome

            observed = transaction.select_current(query)
            observed_text = _observed_precondition(observed)
            if not _precondition_matches(command.expected_version_id, observed):
                expected_text = (
                    "ABSENT"
                    if command.expected_version_id is None
                    else str(command.expected_version_id)
                )
                raise StalePrecondition(
                    f"expected {expected_text}; authoritative current state is {observed_text}"
                )

            version = FinalizedRecordVersion(
                record_id=command.record_id,
                version_id=command.version_id,
                family=command.family,
                scope=command.scope,
                content_json=canonical_json(command.content),
                recorded_at=recorded_at,
                effective=command.effective,
                creator=command.creator,
            )
            transaction.add_version(version)

            relationship_ids: tuple[RelationshipId, ...] = ()
            status_event_ids: tuple[EventId, ...] = ()
            if command.expected_version_id is not None:
                assert command.relationship_type is not None
                assert command.relationship_reason is not None
                relationship = VersionRelationship(
                    relationship_id=RelationshipId.new(),
                    source_version_id=command.expected_version_id,
                    target_version_id=command.version_id,
                    relationship_type=command.relationship_type,
                    recorded_at=recorded_at,
                    reason=command.relationship_reason,
                )
                transaction.add_relationship(relationship)
                relationship_ids = (relationship.relationship_id,)
                if command.end_predecessor_status is not None:
                    status = StatusEvent(
                        event_id=EventId.new(),
                        target_version_id=command.expected_version_id,
                        prior_status="finalized",
                        new_status=command.end_predecessor_status,
                        recorded_at=recorded_at,
                        effective_at=command.effective.start,
                        actor=command.actor_id or command.actor_resolution.value,
                        basis=command.relationship_reason,
                    )
                    transaction.add_status_event(status)
                    status_event_ids = (status.event_id,)

            if failure_injector is not None:
                failure_injector("after_authoritative_facts")

            affected: tuple[RecordVersionId, ...] = (command.version_id,)
            if command.expected_version_id is not None:
                affected = (command.expected_version_id, command.version_id)
            audit = AuditFact(
                audit_id=AuditId.new(),
                principal_id=command.principal_id,
                actor_id=command.actor_id,
                actor_resolution=command.actor_resolution,
                operation="FINALIZE_VERSION",
                result="COMMITTED",
                command_id=command.command_id,
                idempotency_scope=command.idempotency_scope,
                idempotency_key=command.idempotency_key,
                correlation_id=command.correlation_id,
                causation_id=command.causation_id,
                target_record_id=command.record_id,
                affected_version_ids=affected,
                expected_precondition=(
                    "ABSENT"
                    if command.expected_version_id is None
                    else str(command.expected_version_id)
                ),
                observed_precondition=observed_text,
                effective_at=command.effective.start,
                recorded_at=recorded_at,
                reason_outcomes=command.reason_outcomes,
                request_digest=digest,
            )
            transaction.add_audit(audit)

            if failure_injector is not None:
                failure_injector("after_audit")

            outcome = CommandOutcome(
                command_id=str(command.command_id),
                record_id=str(command.record_id),
                version_ids=(str(command.version_id),),
                status_event_ids=tuple(str(value) for value in status_event_ids),
                relationship_ids=tuple(str(value) for value in relationship_ids),
                audit_id=str(audit.audit_id),
            )
            transaction.add_idempotency(
                IdempotencyFact(
                    scope=command.idempotency_scope,
                    key=command.idempotency_key,
                    digest=digest,
                    command_id=str(command.command_id),
                    outcome=outcome,
                    recorded_at=recorded_at,
                )
            )

            if failure_injector is not None:
                failure_injector("before_commit")
            return outcome

    def commit_status(
        self,
        command: CommitStatusCommand,
        *,
        failure_injector: Callable[[str], None] | None = None,
    ) -> CommandOutcome:
        digest = command.digest()
        recorded_at = self._clock.now()
        query = SelectionQuery(
            family=command.family,
            scope=command.scope,
            effective_at=command.precondition_at,
            known_at=recorded_at,
            record_id=command.record_id,
        )
        with self._store.semantic_transaction() as transaction:
            existing = transaction.get_idempotency(
                command.idempotency_scope, command.idempotency_key
            )
            if existing is not None:
                if existing.digest != digest:
                    raise IdempotencyKeyReuseConflict()
                return existing.outcome

            observed = transaction.select_current(query)
            observed_text = _observed_precondition(observed)
            if not _precondition_matches(command.target_version_id, observed):
                raise StalePrecondition(
                    f"expected {command.target_version_id}; "
                    f"authoritative current state is {observed_text}"
                )

            event = StatusEvent(
                event_id=EventId.new(),
                target_version_id=command.target_version_id,
                prior_status=command.prior_status,
                new_status=command.new_status,
                recorded_at=recorded_at,
                effective_at=command.effective_at,
                actor=command.actor_id or command.actor_resolution.value,
                basis=command.basis,
            )
            transaction.add_status_event(event)
            if failure_injector is not None:
                failure_injector("after_authoritative_facts")

            audit = AuditFact(
                audit_id=AuditId.new(),
                principal_id=command.principal_id,
                actor_id=command.actor_id,
                actor_resolution=command.actor_resolution,
                operation="APPEND_STATUS_EVENT",
                result="COMMITTED",
                command_id=command.command_id,
                idempotency_scope=command.idempotency_scope,
                idempotency_key=command.idempotency_key,
                correlation_id=command.correlation_id,
                causation_id=command.causation_id,
                target_record_id=command.record_id,
                affected_version_ids=(command.target_version_id,),
                expected_precondition=str(command.target_version_id),
                observed_precondition=observed_text,
                effective_at=command.effective_at,
                recorded_at=recorded_at,
                reason_outcomes=command.reason_outcomes,
                request_digest=digest,
            )
            transaction.add_audit(audit)
            if failure_injector is not None:
                failure_injector("after_audit")

            outcome = CommandOutcome(
                command_id=str(command.command_id),
                record_id=str(command.record_id),
                version_ids=(),
                status_event_ids=(str(event.event_id),),
                relationship_ids=(),
                audit_id=str(audit.audit_id),
            )
            transaction.add_idempotency(
                IdempotencyFact(
                    scope=command.idempotency_scope,
                    key=command.idempotency_key,
                    digest=digest,
                    command_id=str(command.command_id),
                    outcome=outcome,
                    recorded_at=recorded_at,
                )
            )
            if failure_injector is not None:
                failure_injector("before_commit")
            return outcome
