"""Atomic prospective Responsibility and durable Work application boundary."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, cast

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
from paim.integrity.selection import SelectionAbsent, SelectionFound, SelectionQuery
from paim.integrity.semantics import ExactContextSet, SemanticContractRef
from paim.integrity.time import Clock, EffectiveInterval, require_utc, to_epoch_microseconds
from paim.operational.models import Permission, PrincipalStatus, ScopeType
from paim.operational.store import OperationalStore
from paim.persistence.ports import CommandOutcome, IdempotencyFact
from paim.responsibility.models import (
    ObligationKind,
    ResponsibilityResolution,
    ResponsibilityResolutionKind,
    responsibility_signature,
)


class SliceATransaction(Protocol):
    def get_idempotency(self, scope: str, key: str) -> IdempotencyFact | None: ...
    def add_idempotency(self, fact: IdempotencyFact) -> None: ...
    def add_version(self, version: FinalizedRecordVersion) -> None: ...
    def add_audit(self, fact: AuditFact) -> None: ...
    def add_status_event(self, event: StatusEvent) -> None: ...
    def add_relationship(self, relationship: VersionRelationship) -> None: ...
    def select_current(self, query: SelectionQuery) -> object: ...
    def insert_projection(self, table_name: str, values: dict[str, object]) -> None: ...
    def projection_rows(
        self, table_name: str, **equals: object
    ) -> tuple[dict[str, object], ...]: ...


class SliceAStore(Protocol):
    def semantic_transaction(self) -> AbstractContextManager[SliceATransaction]: ...

    def read_transaction(self) -> AbstractContextManager[SliceATransaction]: ...


class SliceAAccessPolicy(Protocol):
    def authorize(
        self,
        *,
        principal_id: str,
        actor_id: str,
        action: str,
        case_id: RecordId,
        write: bool,
    ) -> bool: ...


class OperationalSliceAAccessPolicy:
    """Adapter to the current durable principal and software-access boundary."""

    def __init__(self, store: OperationalStore) -> None:
        self._store = store

    def authorize(
        self,
        *,
        principal_id: str,
        actor_id: str,
        action: str,
        case_id: RecordId,
        write: bool,
    ) -> bool:
        principal = self._store.current_principal(principal_id)
        if (
            principal is None
            or principal.status is not PrincipalStatus.ENABLED
            or principal.actor_id is None
            or str(principal.actor_id) != actor_id
        ):
            return False
        visible = self._store.permission_allowed(
            principal_id, Permission.CASE_READ, "read", ScopeType.CASE, case_id
        )
        return visible and (
            not write
            or self._store.permission_allowed(
                principal_id, Permission.COMMAND, action, ScopeType.CASE, case_id
            )
        )


class SliceAConflict(RuntimeError):
    pass


class SliceAAccessDenied(RuntimeError):
    def __init__(self) -> None:
        super().__init__("software access not established")


@dataclass(frozen=True, slots=True)
class ProjectionFact:
    table: str
    values: dict[str, object]


@dataclass(frozen=True, slots=True)
class SliceACommand:
    command_id: CommandId
    idempotency_scope: str
    idempotency_key: str
    principal_id: str
    actor_id: str
    record_id: RecordId
    version_id: RecordVersionId
    family: str
    scope: str
    content: dict[str, JsonValue]
    effective_at: datetime
    contract: SemanticContractRef
    context: ExactContextSet
    owning_case_id: RecordId
    action: str
    projections: tuple[ProjectionFact, ...]
    expected_version_id: RecordVersionId | None = None
    consumer_id: str = "gate8-slice-a"

    def __post_init__(self) -> None:
        require_utc(self.effective_at)
        if not self.idempotency_scope or not self.idempotency_key:
            raise ValueError("idempotency identity is required")

    def digest(self) -> str:
        return canonical_command_digest(
            {
                "record_id": str(self.record_id),
                "version_id": str(self.version_id),
                "family": self.family,
                "scope": self.scope,
                "content": self.content,
                "effective_at": self.effective_at.isoformat(),
                "semantic_contract": self.contract.key,
                "exact_context_digest": self.context.digest,
                "owning_case_id": str(self.owning_case_id),
                "action": self.action,
                "expected_version_id": (
                    str(self.expected_version_id) if self.expected_version_id else None
                ),
                "projections": cast(
                    JsonValue,
                    [dict(table=f.table, values=f.values) for f in self.projections],
                ),
                "consumer_id": self.consumer_id,
                "actor_id": self.actor_id,
                "principal_id": self.principal_id,
            }
        )


class ResponsibilityWorkService:
    """Commit prospective Slice-A facts through one existing semantic transaction."""

    def __init__(self, store: SliceAStore, clock: Clock, access_policy: SliceAAccessPolicy) -> None:
        self._store = store
        self._clock = clock
        self._access_policy = access_policy

    def commit(
        self,
        command: SliceACommand,
        *,
        extra_writer: Callable[[SliceATransaction, datetime], tuple[RecordVersionId, ...]]
        | None = None,
        failure_injector: Callable[[str], None] | None = None,
    ) -> CommandOutcome:
        digest = command.digest()
        recorded_at = self._clock.now()
        if not self._access_policy.authorize(
            principal_id=command.principal_id,
            actor_id=command.actor_id,
            action=command.action,
            case_id=command.owning_case_id,
            write=True,
        ):
            raise SliceAAccessDenied()
        self._validate_plan(command, has_result_writer=extra_writer is not None)
        with self._store.semantic_transaction() as transaction:
            existing = transaction.get_idempotency(
                command.idempotency_scope, command.idempotency_key
            )
            if existing is not None:
                if existing.digest != digest:
                    raise SliceAConflict("IDEMPOTENCY KEY REUSE CONFLICT")
                return existing.outcome
            self._ensure_contract_and_context(transaction, command, recorded_at)
            observed = transaction.select_current(
                SelectionQuery(
                    family=command.family,
                    scope=command.scope,
                    effective_at=command.effective_at,
                    known_at=recorded_at,
                    record_id=command.record_id,
                )
            )
            if command.expected_version_id is None:
                if not isinstance(observed, SelectionAbsent):
                    raise SliceAConflict("expected absent prospective record")
            elif not (
                isinstance(observed, SelectionFound)
                and observed.candidate.version_id == command.expected_version_id
            ):
                raise SliceAConflict("stale exact predecessor; no retarget permitted")
            version = FinalizedRecordVersion(
                command.record_id,
                command.version_id,
                command.family,
                command.scope,
                canonical_json(command.content),
                recorded_at,
                EffectiveInterval(command.effective_at),
                command.actor_id,
            )
            transaction.add_version(version)
            transaction.insert_projection(
                "record_version_semantics",
                {
                    "version_id": str(command.version_id),
                    "contract_key": command.contract.key,
                    "context_digest": command.context.digest,
                    "consumer_id": command.consumer_id,
                    "adapter_key": None,
                },
            )
            extra_versions = extra_writer(transaction, recorded_at) if extra_writer else ()
            for projection in command.projections:
                transaction.insert_projection(projection.table, projection.values)
            relationship_ids: tuple[RelationshipId, ...] = ()
            status_ids: tuple[EventId, ...] = ()
            if command.expected_version_id is not None:
                relationship = VersionRelationship(
                    RelationshipId.new(),
                    command.expected_version_id,
                    command.version_id,
                    RelationshipType.SUPERSESSION,
                    recorded_at,
                    "exact prospective successor",
                )
                transaction.add_relationship(relationship)
                transaction.insert_projection(
                    "version_relationship_semantics",
                    {
                        "relationship_id": str(relationship.relationship_id),
                        "contract_key": command.contract.key,
                        "context_digest": command.context.digest,
                    },
                )
                status = StatusEvent(
                    EventId.new(),
                    command.expected_version_id,
                    "CURRENT",
                    "SUPERSEDED",
                    recorded_at,
                    command.effective_at,
                    command.actor_id,
                    "exact prospective successor",
                )
                transaction.add_status_event(status)
                transaction.insert_projection(
                    "status_event_semantics",
                    {
                        "event_id": str(status.event_id),
                        "contract_key": command.contract.key,
                        "context_digest": command.context.digest,
                    },
                )
                relationship_ids = (relationship.relationship_id,)
                status_ids = (status.event_id,)
            if failure_injector:
                failure_injector("after_authoritative_facts")
            audit = AuditFact(
                AuditId.new(),
                command.principal_id,
                command.actor_id,
                ActorResolution.PROVIDED,
                "SLICE_A_SEMANTIC_COMMIT",
                "COMMITTED",
                command.command_id,
                command.idempotency_scope,
                command.idempotency_key,
                None,
                None,
                command.record_id,
                (command.version_id, *extra_versions),
                "EXACT_CONTEXT",
                command.context.digest,
                command.effective_at,
                recorded_at,
                ("SEMANTIC_CONTRACT_BOUND", "EXACT_CONTEXT_BOUND"),
                digest,
            )
            transaction.add_audit(audit)
            outcome = CommandOutcome(
                str(command.command_id),
                str(command.record_id),
                tuple(str(value) for value in (command.version_id, *extra_versions)),
                tuple(str(value) for value in status_ids),
                tuple(str(value) for value in relationship_ids),
                str(audit.audit_id),
            )
            transaction.add_idempotency(
                IdempotencyFact(
                    command.idempotency_scope,
                    command.idempotency_key,
                    digest,
                    str(command.command_id),
                    outcome,
                    recorded_at,
                )
            )
            return outcome

    @staticmethod
    def _validate_plan(command: SliceACommand, *, has_result_writer: bool) -> None:
        """Fail closed before storage when an internal projection plan is incoherent."""
        allowed = {
            "responsibility": {"responsibility_records", "responsibility_versions"},
            "assignment-basis": {"assignment_basis_records", "assignment_basis_versions"},
            "responsibility-assignment": {
                "responsibility_assignment_records",
                "responsibility_assignment_versions",
            },
            "case-work": {"case_work_records", "case_work_versions", "case_work_result_links"},
        }
        permitted = allowed.get(command.family)
        if permitted is None or any(fact.table not in permitted for fact in command.projections):
            raise ValueError("Slice-A family/projection contract is not established")
        version_rows = [
            fact.values for fact in command.projections if fact.table.endswith("_versions")
        ]
        if len(version_rows) != 1:
            raise ValueError("one exact family Version projection is required")
        version_row = version_rows[0]
        if version_row.get("version_id") != str(command.version_id):
            raise ValueError("projection Version identity does not match command")
        if version_row.get("record_id") != str(command.record_id):
            raise ValueError("projection Record identity does not match command")
        if (
            "context_digest" in version_row
            and version_row["context_digest"] != command.context.digest
        ):
            raise ValueError("projection exact context does not match command")
        if "owning_case_id" in version_row and version_row["owning_case_id"] != str(
            command.owning_case_id
        ):
            raise ValueError("projection owning Case does not match command")
        if command.family == "case-work":
            state = version_row.get("state")
            if state == "COMPLETED" and not has_result_writer:
                raise ValueError("Work completion requires the owning governed-result writer")
            if state != "COMPLETED" and has_result_writer:
                raise ValueError("governed-result writer is only valid for Work completion")
        if command.family == "responsibility":
            try:
                expected_signature = responsibility_signature(
                    contract=command.contract,
                    obligation_kind=ObligationKind(str(version_row["obligation_kind"])),
                    owning_case_id=command.owning_case_id,
                    context=command.context,
                    purpose=str(command.content["purpose_discriminator"]),
                    use=str(command.content["use_discriminator"]),
                    scope=str(command.content["scope_discriminator"]),
                )
            except (KeyError, ValueError) as error:
                raise ValueError("Responsibility signature inputs are not established") from error
            if version_row.get("signature_digest") != expected_signature:
                raise ValueError("Responsibility obligation signature is not canonical")

    def resolve_responsibility(
        self,
        *,
        principal_id: str,
        actor_id: str,
        owning_case_id: RecordId,
        signature_digest: str,
        effective_at: datetime,
        known_at: datetime,
    ) -> ResponsibilityResolution:
        require_utc(effective_at)
        require_utc(known_at)
        if not self._access_policy.authorize(
            principal_id=principal_id,
            actor_id=actor_id,
            action="responsibility.read",
            case_id=owning_case_id,
            write=False,
        ):
            raise SliceAAccessDenied()
        with self._store.read_transaction() as transaction:
            rows = transaction.projection_rows(
                "responsibility_assignment_versions", signature_digest=signature_digest
            )
        applicable = [
            row
            for row in rows
            if cast(int, row["effective_from_us"]) <= to_epoch_microseconds(effective_at)
            and cast(int, row["recorded_at_us"]) <= to_epoch_microseconds(known_at)
            and (
                row["effective_to_us"] is None
                or to_epoch_microseconds(effective_at) < cast(int, row["effective_to_us"])
            )
        ]
        current_by_record: dict[str, dict[str, object]] = {}
        for row in applicable:
            identity = str(row["record_id"])
            prior = current_by_record.get(identity)
            order = (cast(int, row["effective_from_us"]), cast(int, row["recorded_at_us"]))
            if prior is None or order > (
                cast(int, prior["effective_from_us"]),
                cast(int, prior["recorded_at_us"]),
            ):
                current_by_record[identity] = row
        eligible = [row for row in current_by_record.values() if row["state"] == "ASSIGNED"]
        if not eligible:
            return ResponsibilityResolution(ResponsibilityResolutionKind.VACANCY, ())
        actors = {str(row["actor_id"]) for row in eligible}
        ids = tuple(sorted(str(row["version_id"]) for row in eligible))
        if len(eligible) != 1 or len(actors) != 1:
            return ResponsibilityResolution(ResponsibilityResolutionKind.CONFLICT, ids)
        return ResponsibilityResolution(ResponsibilityResolutionKind.ONE, ids, actors.pop())

    @staticmethod
    def _ensure_contract_and_context(
        transaction: SliceATransaction, command: SliceACommand, recorded_at: datetime
    ) -> None:
        if not transaction.projection_rows("semantic_contracts", contract_key=command.contract.key):
            transaction.insert_projection(
                "semantic_contracts",
                {
                    "contract_key": command.contract.key,
                    "contract_id": command.contract.contract_id,
                    "contract_version": command.contract.version,
                    "owner": "PAIM",
                    "interpretation_source": "docs/system/specifications",
                    "recorded_at_us": to_epoch_microseconds(recorded_at),
                },
            )
        if not transaction.projection_rows(
            "semantic_contract_families",
            contract_key=command.contract.key,
            record_family=command.family,
        ):
            transaction.insert_projection(
                "semantic_contract_families",
                {"contract_key": command.contract.key, "record_family": command.family},
            )
        if not transaction.projection_rows(
            "exact_context_sets", context_digest=command.context.digest
        ):
            transaction.insert_projection(
                "exact_context_sets",
                {
                    "context_digest": command.context.digest,
                    "canonical_json": command.context.canonical_json,
                    "recorded_at_us": to_epoch_microseconds(recorded_at),
                },
            )
            for member in command.context.members:
                transaction.insert_projection(
                    "exact_context_members",
                    {
                        "context_digest": command.context.digest,
                        "slot": member.slot,
                        "member_kind": member.kind.value,
                        "identity": member.identity,
                    },
                )
