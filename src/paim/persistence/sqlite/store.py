"""SQLite + SQLAlchemy Core implementation of the integrity persistence ports."""

from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, cast

from sqlalchemy import Connection, Engine, create_engine, event, func, insert, or_, select
from sqlalchemy.engine import RowMapping
from sqlalchemy.exc import OperationalError

from paim.audit.models import ActorResolution, AuditFact
from paim.domain.models import (
    ConfigurationVersionContext,
    DelegationEffect,
    GoverningDesignationDetail,
    RoleAssignmentDetail,
    RoleTargetType,
)
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
    RelationshipType,
    StatusEvent,
    VersionRelationship,
)
from paim.integrity.selection import (
    CurrentSelection,
    SelectionCandidate,
    SelectionQuery,
    select_current,
)
from paim.integrity.time import EffectiveInterval, from_epoch_microseconds, to_epoch_microseconds
from paim.persistence.ports import (
    CommandOutcome,
    IdempotencyFact,
    NestedSemanticCommit,
    RecordHistory,
    WriterContention,
)
from paim.persistence.sqlite.schema import (
    audit_facts,
    configuration_determinations,
    governing_configuration_designations,
    idempotency_facts,
    managed_configuration_versions,
    managed_configurations,
    metadata,
    paim_actor_versions,
    paim_actors,
    paim_case_links,
    paim_case_versions,
    paim_cases,
    record_versions,
    records,
    role_assignment_versions,
    role_assignments,
    status_events,
    version_relationships,
)

_semantic_active: ContextVar[bool] = ContextVar("paim_semantic_transaction_active", default=False)


def _enable_foreign_keys(dbapi_connection: Any, _connection_record: Any) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def _outcome_json(outcome: CommandOutcome) -> str:
    return json.dumps(
        {
            "command_id": outcome.command_id,
            "record_id": outcome.record_id,
            "version_ids": list(outcome.version_ids),
            "status_event_ids": list(outcome.status_event_ids),
            "relationship_ids": list(outcome.relationship_ids),
            "audit_id": outcome.audit_id,
            "result": outcome.result,
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def _parse_outcome(value: str) -> CommandOutcome:
    data = cast("dict[str, Any]", json.loads(value))
    return CommandOutcome(
        command_id=cast("str", data["command_id"]),
        record_id=cast("str", data["record_id"]),
        version_ids=tuple(cast("list[str]", data["version_ids"])),
        status_event_ids=tuple(cast("list[str]", data["status_event_ids"])),
        relationship_ids=tuple(cast("list[str]", data["relationship_ids"])),
        audit_id=cast("str", data["audit_id"]),
        result=cast("str", data["result"]),
    )


def _version_from_row(row: RowMapping) -> FinalizedRecordVersion:
    end_us = cast("int | None", row["effective_to_us"])
    return FinalizedRecordVersion(
        record_id=RecordId.parse(cast("str", row["record_id"])),
        version_id=RecordVersionId.parse(cast("str", row["version_id"])),
        family=cast("str", row["family"]),
        scope=cast("str", row["scope"]),
        content_json=cast("str", row["content_json"]),
        recorded_at=from_epoch_microseconds(cast("int", row["recorded_at_us"])),
        effective=EffectiveInterval(
            from_epoch_microseconds(cast("int", row["effective_from_us"])),
            from_epoch_microseconds(end_us) if end_us is not None else None,
        ),
        creator=cast("str", row["creator"]),
    )


def _event_from_row(row: RowMapping) -> StatusEvent:
    return StatusEvent(
        event_id=EventId.parse(cast("str", row["event_id"])),
        target_version_id=RecordVersionId.parse(cast("str", row["target_version_id"])),
        prior_status=cast("str", row["prior_status"]),
        new_status=cast("str", row["new_status"]),
        recorded_at=from_epoch_microseconds(cast("int", row["recorded_at_us"])),
        effective_at=from_epoch_microseconds(cast("int", row["effective_at_us"])),
        actor=cast("str", row["actor"]),
        basis=cast("str", row["basis"]),
    )


def _relationship_from_row(row: RowMapping) -> VersionRelationship:
    return VersionRelationship(
        relationship_id=RelationshipId.parse(cast("str", row["relationship_id"])),
        source_version_id=RecordVersionId.parse(cast("str", row["source_version_id"])),
        target_version_id=RecordVersionId.parse(cast("str", row["target_version_id"])),
        relationship_type=RelationshipType(cast("str", row["relationship_type"])),
        recorded_at=from_epoch_microseconds(cast("int", row["recorded_at_us"])),
        reason=cast("str", row["reason"]),
    )


def _audit_from_row(row: RowMapping) -> AuditFact:
    return AuditFact(
        audit_id=AuditId.parse(cast("str", row["audit_id"])),
        principal_id=cast("str", row["principal_id"]),
        actor_id=cast("str | None", row["actor_id"]),
        actor_resolution=ActorResolution(cast("str", row["actor_resolution"])),
        operation=cast("str", row["operation"]),
        result=cast("str", row["result"]),
        command_id=CommandId.parse(cast("str", row["command_id"])),
        idempotency_scope=cast("str", row["idempotency_scope"]),
        idempotency_key=cast("str", row["idempotency_key"]),
        correlation_id=cast("str | None", row["correlation_id"]),
        causation_id=cast("str | None", row["causation_id"]),
        target_record_id=RecordId.parse(cast("str", row["target_record_id"])),
        affected_version_ids=tuple(
            RecordVersionId.parse(value)
            for value in cast(
                "list[str]", json.loads(cast("str", row["affected_version_ids_json"]))
            )
        ),
        expected_precondition=cast("str", row["expected_precondition"]),
        observed_precondition=cast("str", row["observed_precondition"]),
        effective_at=from_epoch_microseconds(cast("int", row["effective_at_us"])),
        recorded_at=from_epoch_microseconds(cast("int", row["recorded_at_us"])),
        reason_outcomes=tuple(
            cast("list[str]", json.loads(cast("str", row["reason_outcomes_json"])))
        ),
        request_digest=cast("str", row["request_digest"]),
    )


class SQLiteIntegrityTransaction:
    """Operations bound to one explicit database transaction."""

    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    def get_idempotency(self, scope: str, key: str) -> IdempotencyFact | None:
        row = (
            self._connection.execute(
                select(idempotency_facts).where(
                    idempotency_facts.c.scope == scope,
                    idempotency_facts.c.idempotency_key == key,
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return None
        return IdempotencyFact(
            scope=cast("str", row["scope"]),
            key=cast("str", row["idempotency_key"]),
            digest=cast("str", row["digest"]),
            command_id=cast("str", row["command_id"]),
            outcome=_parse_outcome(cast("str", row["outcome_json"])),
            recorded_at=from_epoch_microseconds(cast("int", row["recorded_at_us"])),
        )

    def add_idempotency(self, fact: IdempotencyFact) -> None:
        self._connection.execute(
            insert(idempotency_facts).values(
                scope=fact.scope,
                idempotency_key=fact.key,
                digest=fact.digest,
                command_id=fact.command_id,
                outcome_json=_outcome_json(fact.outcome),
                recorded_at_us=to_epoch_microseconds(fact.recorded_at),
            )
        )

    def add_version(self, version: FinalizedRecordVersion) -> None:
        existing = (
            self._connection.execute(
                select(records).where(records.c.record_id == str(version.record_id))
            )
            .mappings()
            .one_or_none()
        )
        if existing is None:
            self._connection.execute(
                insert(records).values(
                    record_id=str(version.record_id), family=version.family, scope=version.scope
                )
            )
        elif existing["family"] != version.family or existing["scope"] != version.scope:
            raise ValueError("Record ID cannot be reused for another family or scope")
        self._connection.execute(
            insert(record_versions).values(
                version_id=str(version.version_id),
                record_id=str(version.record_id),
                content_json=version.content_json,
                finalized=True,
                recorded_at_us=to_epoch_microseconds(version.recorded_at),
                effective_from_us=to_epoch_microseconds(version.effective.start),
                effective_to_us=(
                    to_epoch_microseconds(version.effective.end)
                    if version.effective.end is not None
                    else None
                ),
                creator=version.creator,
            )
        )

    def case_exists(self, case_id: RecordId) -> bool:
        return (
            self._connection.scalar(
                select(func.count())
                .select_from(paim_cases)
                .where(paim_cases.c.case_id == str(case_id))
            )
            == 1
        )

    def add_case(self, case_id: RecordId, version_id: RecordVersionId) -> None:
        if not self.case_exists(case_id):
            self._connection.execute(insert(paim_cases).values(case_id=str(case_id)))
        self._connection.execute(
            insert(paim_case_versions).values(
                version_id=str(version_id),
                case_id=str(case_id),
                initial_lifecycle_state="open",
            )
        )

    def add_case_link(
        self,
        *,
        link_id: str,
        source_case_id: RecordId,
        target_case_id: RecordId,
        relationship_type: str,
        recorded_at_us: int,
        effective_at_us: int,
        actor_id: str,
        reason: str,
    ) -> None:
        self._connection.execute(
            insert(paim_case_links).values(
                link_id=link_id,
                source_case_id=str(source_case_id),
                target_case_id=str(target_case_id),
                relationship_type=relationship_type,
                recorded_at_us=recorded_at_us,
                effective_at_us=effective_at_us,
                actor_id=actor_id,
                reason=reason,
            )
        )

    def configuration_owning_case(self, configuration_id: RecordId) -> RecordId | None:
        value = self._connection.scalar(
            select(managed_configurations.c.owning_case_id).where(
                managed_configurations.c.configuration_id == str(configuration_id)
            )
        )
        return RecordId.parse(cast("str", value)) if value is not None else None

    def add_configuration(
        self,
        *,
        configuration_id: RecordId,
        version_id: RecordVersionId,
        owning_case_id: RecordId,
        maturity: str,
        purpose: str,
    ) -> None:
        existing_owner = self.configuration_owning_case(configuration_id)
        if existing_owner is None:
            self._connection.execute(
                insert(managed_configurations).values(
                    configuration_id=str(configuration_id), owning_case_id=str(owning_case_id)
                )
            )
        elif existing_owner != owning_case_id:
            raise ValueError("Configuration identity cannot change its owning Case")
        self._connection.execute(
            insert(managed_configuration_versions).values(
                version_id=str(version_id),
                configuration_id=str(configuration_id),
                maturity=maturity,
                purpose=purpose,
            )
        )

    def configuration_version_context(
        self, version_id: RecordVersionId
    ) -> ConfigurationVersionContext | None:
        row = (
            self._connection.execute(
                select(
                    managed_configuration_versions.c.configuration_id,
                    managed_configurations.c.owning_case_id,
                    managed_configuration_versions.c.maturity,
                    managed_configuration_versions.c.purpose,
                )
                .join(
                    managed_configurations,
                    managed_configurations.c.configuration_id
                    == managed_configuration_versions.c.configuration_id,
                )
                .where(managed_configuration_versions.c.version_id == str(version_id))
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return None
        return ConfigurationVersionContext(
            configuration_id=RecordId.parse(cast("str", row["configuration_id"])),
            owning_case_id=RecordId.parse(cast("str", row["owning_case_id"])),
            maturity=cast("str", row["maturity"]),
            purpose=cast("str", row["purpose"]),
        )

    def actor_exists(self, actor_id: RecordId) -> bool:
        return (
            self._connection.scalar(
                select(func.count())
                .select_from(paim_actors)
                .where(paim_actors.c.actor_id == str(actor_id))
            )
            == 1
        )

    def add_actor(self, actor_id: RecordId, version_id: RecordVersionId) -> None:
        if not self.actor_exists(actor_id):
            self._connection.execute(insert(paim_actors).values(actor_id=str(actor_id)))
        self._connection.execute(
            insert(paim_actor_versions).values(version_id=str(version_id), actor_id=str(actor_id))
        )

    def add_role_assignment(
        self,
        *,
        assignment_id: RecordId,
        version_id: RecordVersionId,
        actor_id: RecordId,
        role: str,
        target_type: str,
        target_id: str,
        case_context_id: RecordId | None,
        accountable: bool,
        compatibility_key: str,
        delegation_effect: str,
        delegated_from_version_id: RecordVersionId | None,
    ) -> None:
        exists = self._connection.scalar(
            select(func.count())
            .select_from(role_assignments)
            .where(role_assignments.c.assignment_id == str(assignment_id))
        )
        if exists != 1:
            self._connection.execute(
                insert(role_assignments).values(assignment_id=str(assignment_id))
            )
        self._connection.execute(
            insert(role_assignment_versions).values(
                version_id=str(version_id),
                assignment_id=str(assignment_id),
                actor_id=str(actor_id),
                role=role,
                target_type=target_type,
                target_id=target_id,
                case_context_id=str(case_context_id) if case_context_id is not None else None,
                accountable=accountable,
                compatibility_key=compatibility_key,
                delegation_effect=delegation_effect,
                delegated_from_version_id=(
                    str(delegated_from_version_id)
                    if delegated_from_version_id is not None
                    else None
                ),
            )
        )

    def role_assignment_records(
        self, *, role: str, targets: tuple[tuple[str, str], ...]
    ) -> tuple[RecordId, ...]:
        if not targets:
            return ()
        predicates = tuple(
            (role_assignment_versions.c.target_type == target_type)
            & (role_assignment_versions.c.target_id == target_id)
            for target_type, target_id in targets
        )
        values = self._connection.execute(
            select(role_assignment_versions.c.assignment_id)
            .where(role_assignment_versions.c.role == role, or_(*predicates))
            .distinct()
        ).scalars()
        return tuple(RecordId.parse(cast("str", value)) for value in values)

    def role_assignment_detail(self, version_id: RecordVersionId) -> RoleAssignmentDetail | None:
        row = (
            self._connection.execute(
                select(role_assignment_versions).where(
                    role_assignment_versions.c.version_id == str(version_id)
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return None
        case_context = cast("str | None", row["case_context_id"])
        delegated_from = cast("str | None", row["delegated_from_version_id"])
        return RoleAssignmentDetail(
            version_id=RecordVersionId.parse(cast("str", row["version_id"])),
            assignment_id=RecordId.parse(cast("str", row["assignment_id"])),
            actor_id=RecordId.parse(cast("str", row["actor_id"])),
            role=cast("str", row["role"]),
            target_type=RoleTargetType(cast("str", row["target_type"])),
            target_id=cast("str", row["target_id"]),
            case_context_id=RecordId.parse(case_context) if case_context is not None else None,
            accountable=cast("bool", row["accountable"]),
            compatibility_key=cast("str", row["compatibility_key"]),
            delegation_effect=DelegationEffect(cast("str", row["delegation_effect"])),
            delegated_from_version_id=(
                RecordVersionId.parse(delegated_from) if delegated_from is not None else None
            ),
        )

    def add_governing_designation(
        self,
        *,
        version_id: RecordVersionId,
        case_id: RecordId,
        configuration_version_id: RecordVersionId,
        accountable_assignment_version_id: RecordVersionId | None,
        accountable_mechanism: str | None,
    ) -> None:
        self._connection.execute(
            insert(governing_configuration_designations).values(
                version_id=str(version_id),
                case_id=str(case_id),
                configuration_version_id=str(configuration_version_id),
                accountable_assignment_version_id=(
                    str(accountable_assignment_version_id)
                    if accountable_assignment_version_id is not None
                    else None
                ),
                accountable_mechanism=accountable_mechanism,
            )
        )

    def governing_designation_detail(
        self, version_id: RecordVersionId
    ) -> GoverningDesignationDetail | None:
        row = (
            self._connection.execute(
                select(governing_configuration_designations).where(
                    governing_configuration_designations.c.version_id == str(version_id)
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return None
        return GoverningDesignationDetail(
            version_id=RecordVersionId.parse(cast("str", row["version_id"])),
            case_id=RecordId.parse(cast("str", row["case_id"])),
            configuration_version_id=RecordVersionId.parse(
                cast("str", row["configuration_version_id"])
            ),
        )

    def add_configuration_determination(
        self,
        *,
        version_id: RecordVersionId,
        configuration_version_id: RecordVersionId,
        determination_kind: str,
        outcome: str,
        rationale: str,
        accountable_assignment_version_id: RecordVersionId | None,
        accountable_mechanism: str | None,
    ) -> None:
        self._connection.execute(
            insert(configuration_determinations).values(
                version_id=str(version_id),
                configuration_version_id=str(configuration_version_id),
                determination_kind=determination_kind,
                outcome=outcome,
                rationale=rationale,
                accountable_assignment_version_id=(
                    str(accountable_assignment_version_id)
                    if accountable_assignment_version_id is not None
                    else None
                ),
                accountable_mechanism=accountable_mechanism,
            )
        )

    def add_status_event(self, status: StatusEvent) -> None:
        self._connection.execute(
            insert(status_events).values(
                event_id=str(status.event_id),
                target_version_id=str(status.target_version_id),
                prior_status=status.prior_status,
                new_status=status.new_status,
                recorded_at_us=to_epoch_microseconds(status.recorded_at),
                effective_at_us=to_epoch_microseconds(status.effective_at),
                actor=status.actor,
                basis=status.basis,
            )
        )

    def add_relationship(self, relationship: VersionRelationship) -> None:
        self._connection.execute(
            insert(version_relationships).values(
                relationship_id=str(relationship.relationship_id),
                source_version_id=str(relationship.source_version_id),
                target_version_id=str(relationship.target_version_id),
                relationship_type=relationship.relationship_type.value,
                recorded_at_us=to_epoch_microseconds(relationship.recorded_at),
                reason=relationship.reason,
            )
        )

    def add_audit(self, fact: AuditFact) -> None:
        self._connection.execute(
            insert(audit_facts).values(
                audit_id=str(fact.audit_id),
                principal_id=fact.principal_id,
                actor_id=fact.actor_id,
                actor_resolution=fact.actor_resolution.value,
                operation=fact.operation,
                result=fact.result,
                command_id=str(fact.command_id),
                idempotency_scope=fact.idempotency_scope,
                idempotency_key=fact.idempotency_key,
                correlation_id=fact.correlation_id,
                causation_id=fact.causation_id,
                target_record_id=str(fact.target_record_id),
                affected_version_ids_json=json.dumps(
                    [str(value) for value in fact.affected_version_ids], separators=(",", ":")
                ),
                expected_precondition=fact.expected_precondition,
                observed_precondition=fact.observed_precondition,
                effective_at_us=to_epoch_microseconds(fact.effective_at),
                recorded_at_us=to_epoch_microseconds(fact.recorded_at),
                reason_outcomes_json=json.dumps(fact.reason_outcomes, separators=(",", ":")),
                request_digest=fact.request_digest,
            )
        )

    def get_version(self, version_id: RecordVersionId) -> FinalizedRecordVersion | None:
        statement = (
            select(
                record_versions,
                records.c.family,
                records.c.scope,
            )
            .join(records, records.c.record_id == record_versions.c.record_id)
            .where(record_versions.c.version_id == str(version_id))
        )
        row = self._connection.execute(statement).mappings().one_or_none()
        return _version_from_row(row) if row is not None else None

    def get_history(self, record_id: RecordId) -> RecordHistory:
        version_rows = (
            self._connection.execute(
                select(record_versions, records.c.family, records.c.scope)
                .join(records, records.c.record_id == record_versions.c.record_id)
                .where(record_versions.c.record_id == str(record_id))
            )
            .mappings()
            .all()
        )
        versions = tuple(_version_from_row(row) for row in version_rows)
        version_ids = tuple(str(version.version_id) for version in versions)
        if not version_ids:
            return RecordHistory(
                versions=frozenset(), status_events=frozenset(), relationships=frozenset()
            )
        event_rows = (
            self._connection.execute(
                select(status_events).where(status_events.c.target_version_id.in_(version_ids))
            )
            .mappings()
            .all()
        )
        relationship_rows = (
            self._connection.execute(
                select(version_relationships).where(
                    or_(
                        version_relationships.c.source_version_id.in_(version_ids),
                        version_relationships.c.target_version_id.in_(version_ids),
                    )
                )
            )
            .mappings()
            .all()
        )
        return RecordHistory(
            versions=frozenset(versions),
            status_events=frozenset(_event_from_row(row) for row in event_rows),
            relationships=frozenset(_relationship_from_row(row) for row in relationship_rows),
        )

    def select_current(self, query: SelectionQuery) -> CurrentSelection:
        statement = (
            select(record_versions, records.c.family, records.c.scope)
            .join(records, records.c.record_id == record_versions.c.record_id)
            .where(records.c.family == query.family, records.c.scope == query.scope)
        )
        if query.record_id is not None:
            statement = statement.where(records.c.record_id == str(query.record_id))
        version_rows = self._connection.execute(statement).mappings().all()
        candidates: list[SelectionCandidate] = []
        for row in version_rows:
            version = _version_from_row(row)
            event_rows = (
                self._connection.execute(
                    select(status_events).where(
                        status_events.c.target_version_id == str(version.version_id)
                    )
                )
                .mappings()
                .all()
            )
            candidates.append(
                SelectionCandidate(
                    record_id=version.record_id,
                    version_id=version.version_id,
                    family=version.family,
                    scope=version.scope,
                    recorded_at=version.recorded_at,
                    effective=version.effective,
                    finalized=cast("bool", row["finalized"]),
                    status_events=frozenset(_event_from_row(event) for event in event_rows),
                )
            )
        return select_current(query, tuple(candidates))

    def count_rows(self, table_name: str) -> int:
        table = metadata.tables.get(table_name)
        if table is None:
            raise ValueError(f"unknown table: {table_name}")
        return int(self._connection.scalar(select(func.count()).select_from(table)) or 0)


class SQLiteIntegrityStore:
    """Synchronous local adapter with one explicit writer per semantic commit."""

    def __init__(self, database_url: str, *, timeout_seconds: float = 0.25) -> None:
        self.engine: Engine = create_engine(
            database_url,
            connect_args={"timeout": timeout_seconds},
        )
        event.listen(self.engine, "connect", _enable_foreign_keys)

    @contextmanager
    def read_transaction(self) -> Iterator[SQLiteIntegrityTransaction]:
        """Use one consistent read connection without acquiring the writer boundary."""
        with self.engine.connect() as connection:
            yield SQLiteIntegrityTransaction(connection)

    @contextmanager
    def semantic_transaction(self) -> Iterator[SQLiteIntegrityTransaction]:
        if _semantic_active.get():
            raise NestedSemanticCommit("nested independent semantic commits are prohibited")
        token = _semantic_active.set(True)
        try:
            with self.engine.connect() as connection:
                try:
                    connection.exec_driver_sql("BEGIN IMMEDIATE")
                except OperationalError as error:
                    if "locked" in str(error).casefold() or "busy" in str(error).casefold():
                        raise WriterContention("SQLITE WRITER CONTENTION") from error
                    raise
                transaction = SQLiteIntegrityTransaction(connection)
                try:
                    yield transaction
                    connection.commit()
                except BaseException:
                    connection.rollback()
                    raise
        finally:
            _semantic_active.reset(token)

    def get_version(self, version_id: RecordVersionId) -> FinalizedRecordVersion | None:
        with self.engine.connect() as connection:
            return SQLiteIntegrityTransaction(connection).get_version(version_id)

    def get_history(self, record_id: RecordId) -> RecordHistory:
        with self.engine.connect() as connection:
            return SQLiteIntegrityTransaction(connection).get_history(record_id)

    def select_current(self, query: SelectionQuery) -> CurrentSelection:
        with self.engine.connect() as connection:
            return SQLiteIntegrityTransaction(connection).select_current(query)

    def get_audit(self, audit_id: AuditId) -> AuditFact | None:
        with self.engine.connect() as connection:
            row = (
                connection.execute(
                    select(audit_facts).where(audit_facts.c.audit_id == str(audit_id))
                )
                .mappings()
                .one_or_none()
            )
            return _audit_from_row(row) if row is not None else None

    def count_rows(self, table_name: str) -> int:
        with self.engine.connect() as connection:
            return SQLiteIntegrityTransaction(connection).count_rows(table_name)

    def dispose(self) -> None:
        self.engine.dispose()
