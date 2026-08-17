"""Adapter-neutral persistence contracts for Increment 1A."""

from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from paim.audit.models import AuditFact
from paim.integrity.ids import AuditId, EventId, RecordId, RecordVersionId, RelationshipId
from paim.integrity.records import FinalizedRecordVersion, StatusEvent, VersionRelationship
from paim.integrity.selection import CurrentSelection, SelectionQuery


class WriterContention(RuntimeError):
    """Another writer owns the SQLite write boundary."""


class NestedSemanticCommit(RuntimeError):
    """A semantic transaction attempted to open an independent nested commit."""


@dataclass(frozen=True, slots=True)
class CommandOutcome:
    command_id: str
    record_id: str
    version_ids: tuple[str, ...]
    status_event_ids: tuple[str, ...]
    relationship_ids: tuple[str, ...]
    audit_id: str
    result: str = "COMMITTED"


@dataclass(frozen=True, slots=True)
class IdempotencyFact:
    scope: str
    key: str
    digest: str
    command_id: str
    outcome: CommandOutcome
    recorded_at: datetime


@dataclass(frozen=True, slots=True)
class RecordHistory:
    versions: frozenset[FinalizedRecordVersion]
    status_events: frozenset[StatusEvent]
    relationships: frozenset[VersionRelationship]


class IntegrityTransaction(Protocol):
    def get_idempotency(self, scope: str, key: str) -> IdempotencyFact | None: ...

    def add_idempotency(self, fact: IdempotencyFact) -> None: ...

    def add_version(self, version: FinalizedRecordVersion) -> None: ...

    def add_status_event(self, event: StatusEvent) -> None: ...

    def add_relationship(self, relationship: VersionRelationship) -> None: ...

    def add_audit(self, fact: AuditFact) -> None: ...

    def get_version(self, version_id: RecordVersionId) -> FinalizedRecordVersion | None: ...

    def get_history(self, record_id: RecordId) -> RecordHistory: ...

    def select_current(self, query: SelectionQuery) -> CurrentSelection: ...

    def count_rows(self, table_name: str) -> int: ...


class IntegrityStore(Protocol):
    def semantic_transaction(self) -> AbstractContextManager[IntegrityTransaction]: ...

    def get_version(self, version_id: RecordVersionId) -> FinalizedRecordVersion | None: ...

    def get_history(self, record_id: RecordId) -> RecordHistory: ...

    def select_current(self, query: SelectionQuery) -> CurrentSelection: ...

    def get_audit(self, audit_id: AuditId) -> AuditFact | None: ...

    def count_rows(self, table_name: str) -> int: ...


type CreatedIdentity = AuditId | EventId | RecordVersionId | RelationshipId
