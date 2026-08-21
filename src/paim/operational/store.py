"""SQLite operational persistence isolated from substantive PAIM authority."""

from __future__ import annotations

import json
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from sqlalchemy import Connection, Engine, and_, create_engine, event, func, insert, select

from paim.integrity import RecordId, to_epoch_microseconds
from paim.integrity.records import JsonValue
from paim.operational.models import (
    AccessEffect,
    AccessGrantInput,
    AdapterType,
    IntakeStatus,
    Permission,
    PrincipalStatus,
    PrincipalVersion,
    ScopeType,
)
from paim.persistence.sqlite.schema import (
    adapter_intakes,
    managed_configurations,
    notification_delivery_events,
    operational_audit_facts,
    operational_principal_versions,
    operational_principals,
    operational_register_rebuild_bases,
    paim_cases,
    register_notification_intents,
    register_output_manifests,
    software_access_grants,
)


def _enable_foreign_keys(dbapi_connection: Any, _connection_record: Any) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


class OperationalStore:
    """Append-preserving local operational records and access resolution."""

    def __init__(self, database_url: str, event_log_path: Path) -> None:
        self.engine: Engine = create_engine(database_url)
        event.listen(self.engine, "connect", _enable_foreign_keys)
        self._event_log_path = event_log_path

    @contextmanager
    def transaction(self) -> Iterator[Connection]:
        with self.engine.begin() as connection:
            yield connection

    @contextmanager
    def read(self) -> Iterator[Connection]:
        with self.engine.connect() as connection:
            yield connection

    def dispose(self) -> None:
        self.engine.dispose()

    def principal_exists(self, principal_id: str) -> bool:
        with self.read() as connection:
            return (
                connection.scalar(
                    select(func.count())
                    .select_from(operational_principals)
                    .where(operational_principals.c.principal_id == principal_id)
                )
                == 1
            )

    def add_principal_version(
        self,
        *,
        version_id: str,
        principal_id: str,
        actor_id: RecordId | None,
        status: PrincipalStatus,
        credential_salt: str,
        credential_verifier: str,
        credential_iterations: int,
        recorded_at: datetime,
        recorded_by: str,
    ) -> PrincipalVersion:
        at_us = to_epoch_microseconds(recorded_at)
        with self.transaction() as connection:
            exists = connection.scalar(
                select(func.count())
                .select_from(operational_principals)
                .where(operational_principals.c.principal_id == principal_id)
            )
            if not exists:
                connection.execute(
                    insert(operational_principals).values(
                        principal_id=principal_id, created_at_us=at_us
                    )
                )
            sequence = (
                int(
                    connection.scalar(
                        select(func.max(operational_principal_versions.c.sequence)).where(
                            operational_principal_versions.c.principal_id == principal_id
                        )
                    )
                    or 0
                )
                + 1
            )
            connection.execute(
                insert(operational_principal_versions).values(
                    version_id=version_id,
                    principal_id=principal_id,
                    sequence=sequence,
                    actor_id=str(actor_id) if actor_id else None,
                    status=status.value,
                    credential_salt=credential_salt,
                    credential_verifier=credential_verifier,
                    credential_iterations=credential_iterations,
                    recorded_at_us=at_us,
                    recorded_by=recorded_by,
                )
            )
        return PrincipalVersion(
            principal_id,
            sequence,
            actor_id,
            status,
            credential_salt,
            credential_verifier,
            credential_iterations,
        )

    def current_principal(self, principal_id: str) -> PrincipalVersion | None:
        with self.read() as connection:
            row = (
                connection.execute(
                    select(operational_principal_versions)
                    .where(operational_principal_versions.c.principal_id == principal_id)
                    .order_by(operational_principal_versions.c.sequence.desc())
                    .limit(1)
                )
                .mappings()
                .one_or_none()
            )
        if row is None:
            return None
        actor_text = cast("str | None", row["actor_id"])
        return PrincipalVersion(
            principal_id=cast("str", row["principal_id"]),
            sequence=cast("int", row["sequence"]),
            actor_id=RecordId.parse(actor_text) if actor_text else None,
            status=PrincipalStatus(cast("str", row["status"])),
            credential_salt=cast("str", row["credential_salt"]),
            credential_verifier=cast("str", row["credential_verifier"]),
            credential_iterations=cast("int", row["credential_iterations"]),
        )

    def add_access_grant(
        self,
        *,
        grant_id: str,
        principal_id: str,
        value: AccessGrantInput,
        recorded_at: datetime,
        recorded_by: str,
    ) -> None:
        scope_id = str(value.scope_id) if value.scope_id else None
        with self.transaction() as connection:
            sequence = (
                int(
                    connection.scalar(
                        select(func.max(software_access_grants.c.sequence)).where(
                            and_(
                                software_access_grants.c.principal_id == principal_id,
                                software_access_grants.c.permission == value.permission.value,
                                software_access_grants.c.action == value.action,
                                software_access_grants.c.scope_type == value.scope_type.value,
                                software_access_grants.c.scope_id.is_(scope_id)
                                if scope_id is None
                                else software_access_grants.c.scope_id == scope_id,
                            )
                        )
                    )
                    or 0
                )
                + 1
            )
            connection.execute(
                insert(software_access_grants).values(
                    grant_id=grant_id,
                    principal_id=principal_id,
                    sequence=sequence,
                    permission=value.permission.value,
                    action=value.action,
                    scope_type=value.scope_type.value,
                    scope_id=scope_id,
                    effect=value.effect.value,
                    recorded_at_us=to_epoch_microseconds(recorded_at),
                    recorded_by=recorded_by,
                )
            )

    @staticmethod
    def _current_grants(
        connection: Connection, principal_id: str
    ) -> tuple[Mapping[str, object], ...]:
        rows = connection.execute(
            select(software_access_grants).where(
                software_access_grants.c.principal_id == principal_id
            )
        ).mappings()
        current: dict[tuple[str, str, str, str | None], Mapping[str, object]] = {}
        for row in rows:
            key = (
                cast("str", row["permission"]),
                cast("str", row["action"]),
                cast("str", row["scope_type"]),
                cast("str | None", row["scope_id"]),
            )
            prior = current.get(key)
            if prior is None or cast("int", row["sequence"]) > cast("int", prior["sequence"]):
                current[key] = cast("Mapping[str, object]", row)
        return tuple(current.values())

    def permission_allowed(
        self,
        principal_id: str,
        permission: Permission,
        action: str,
        scope_type: ScopeType = ScopeType.GLOBAL,
        scope_id: RecordId | None = None,
    ) -> bool:
        with self.read() as connection:
            grants = self._current_grants(connection, principal_id)
        scope_text = str(scope_id) if scope_id else None
        candidates = [
            row
            for row in grants
            if row["permission"] == permission.value
            and row["action"] in {action, "*"}
            and (
                (row["scope_type"] == scope_type.value and row["scope_id"] == scope_text)
                or (row["scope_type"] == ScopeType.GLOBAL.value and row["scope_id"] is None)
            )
        ]
        if not candidates:
            return False
        candidates.sort(
            key=lambda row: (
                row["scope_type"] == scope_type.value,
                row["action"] == action,
                cast("int", row["sequence"]),
            ),
            reverse=True,
        )
        return candidates[0]["effect"] == AccessEffect.ALLOW.value

    def accessible_case_ids(self, principal_id: str) -> frozenset[RecordId]:
        if self.permission_allowed(principal_id, Permission.CASE_READ, "read"):
            candidates = self.all_case_ids()
        else:
            candidates = self._scoped_allowed_ids(
                principal_id, Permission.CASE_READ, "read", ScopeType.CASE
            )
            if not candidates:
                return frozenset()
            with self.read() as connection:
                existing = frozenset(
                    RecordId.parse(item)
                    for item in connection.scalars(
                        select(paim_cases.c.case_id).where(
                            paim_cases.c.case_id.in_(tuple(str(item) for item in candidates))
                        )
                    ).all()
                )
            candidates &= existing
        return frozenset(
            case_id
            for case_id in candidates
            if self.permission_allowed(
                principal_id,
                Permission.CASE_READ,
                "read",
                ScopeType.CASE,
                case_id,
            )
        )

    def all_case_ids(self) -> frozenset[RecordId]:
        with self.read() as connection:
            return frozenset(
                RecordId.parse(item)
                for item in connection.scalars(select(paim_cases.c.case_id)).all()
            )

    def all_configuration_ids(self) -> frozenset[RecordId]:
        with self.read() as connection:
            return frozenset(
                RecordId.parse(item)
                for item in connection.scalars(
                    select(managed_configurations.c.configuration_id)
                ).all()
            )

    def accessible_configuration_ids(
        self, principal_id: str, case_ids: frozenset[RecordId]
    ) -> frozenset[RecordId]:
        if not case_ids:
            return frozenset()
        global_read = self.permission_allowed(principal_id, Permission.CONFIGURATION_READ, "read")
        scoped_candidates = (
            frozenset()
            if global_read
            else self._scoped_allowed_ids(
                principal_id,
                Permission.CONFIGURATION_READ,
                "read",
                ScopeType.CONFIGURATION,
            )
        )
        if not global_read and not scoped_candidates:
            return frozenset()
        with self.read() as connection:
            statement = select(
                managed_configurations.c.configuration_id,
                managed_configurations.c.owning_case_id,
            ).where(
                managed_configurations.c.owning_case_id.in_(tuple(str(item) for item in case_ids))
            )
            if not global_read:
                statement = statement.where(
                    managed_configurations.c.configuration_id.in_(
                        tuple(str(item) for item in scoped_candidates)
                    )
                )
            rows = connection.execute(statement).all()
        visible: set[RecordId] = set()
        for configuration_text, _case_text in rows:
            configuration_id = RecordId.parse(cast("str", configuration_text))
            if self.permission_allowed(
                principal_id,
                Permission.CONFIGURATION_READ,
                "read",
                ScopeType.CONFIGURATION,
                configuration_id,
            ):
                visible.add(configuration_id)
        return frozenset(visible)

    def _scoped_allowed_ids(
        self,
        principal_id: str,
        permission: Permission,
        action: str,
        scope_type: ScopeType,
    ) -> frozenset[RecordId]:
        with self.read() as connection:
            grants = self._current_grants(connection, principal_id)
        values: set[RecordId] = set()
        for row in grants:
            if (
                row["permission"] != permission.value
                or row["action"] not in {action, "*"}
                or row["scope_type"] != scope_type.value
                or row["scope_id"] is None
                or row["effect"] != AccessEffect.ALLOW.value
            ):
                continue
            try:
                values.add(RecordId.parse(cast("str", row["scope_id"])))
            except ValueError:
                continue
        return frozenset(values)

    def configuration_case(self, configuration_id: RecordId) -> RecordId | None:
        with self.read() as connection:
            value = connection.scalar(
                select(managed_configurations.c.owning_case_id).where(
                    managed_configurations.c.configuration_id == str(configuration_id)
                )
            )
        return RecordId.parse(cast("str", value)) if value else None

    def audit(
        self,
        *,
        event_id: str,
        category: str,
        outcome: str,
        principal_id: str | None,
        actor_id: RecordId | None,
        action: str,
        recorded_at: datetime,
        reason_category: str,
        details: Mapping[str, JsonValue],
        case_id: RecordId | None = None,
        configuration_id: RecordId | None = None,
        correlation_id: str | None = None,
        causation_id: str | None = None,
    ) -> str:
        _validate_safe_details(details)
        details_json = json.dumps(details, sort_keys=True, separators=(",", ":"))
        row = {
            "event_id": event_id,
            "category": category,
            "outcome": outcome,
            "principal_id": principal_id,
            "actor_id": str(actor_id) if actor_id else None,
            "action": action,
            "case_id": str(case_id) if case_id else None,
            "configuration_id": str(configuration_id) if configuration_id else None,
            "correlation_id": correlation_id,
            "causation_id": causation_id,
            "reason_category": reason_category,
            "details_json": details_json,
            "recorded_at_us": to_epoch_microseconds(recorded_at),
        }
        with self.transaction() as connection:
            connection.execute(insert(operational_audit_facts).values(**row))
        try:
            self._event_log_path.parent.mkdir(parents=True, exist_ok=True)
            with self._event_log_path.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
        except OSError:
            # The durable database fact is controlling. Health exposes an
            # unavailable log destination rather than rolling back evidence.
            pass
        return event_id

    def operational_counts(self) -> dict[str, int]:
        with self.read() as connection:
            rows = connection.execute(
                select(
                    operational_audit_facts.c.category,
                    operational_audit_facts.c.outcome,
                    func.count(),
                ).group_by(
                    operational_audit_facts.c.category,
                    operational_audit_facts.c.outcome,
                )
            ).all()
        return {f"{category}:{outcome}": cast("int", count) for category, outcome, count in rows}

    def intake_replays(
        self, adapter_type: AdapterType, source_system: str, replay_id: str
    ) -> tuple[Mapping[str, object], ...]:
        with self.read() as connection:
            return tuple(
                cast("Mapping[str, object]", row)
                for row in connection.execute(
                    select(adapter_intakes)
                    .where(
                        and_(
                            adapter_intakes.c.adapter_type == adapter_type.value,
                            adapter_intakes.c.source_system == source_system,
                            adapter_intakes.c.replay_id == replay_id,
                        )
                    )
                    .order_by(adapter_intakes.c.ingested_at_us, adapter_intakes.c.intake_id)
                )
                .mappings()
                .all()
            )

    def latest_source_intake(
        self, adapter_type: AdapterType, source_system: str, source_object_id: str
    ) -> Mapping[str, object] | None:
        with self.read() as connection:
            row = (
                connection.execute(
                    select(adapter_intakes)
                    .where(
                        and_(
                            adapter_intakes.c.adapter_type == adapter_type.value,
                            adapter_intakes.c.source_system == source_system,
                            adapter_intakes.c.source_object_id == source_object_id,
                            adapter_intakes.c.status == IntakeStatus.PROPOSED.value,
                        )
                    )
                    .order_by(adapter_intakes.c.ingested_at_us.desc())
                    .limit(1)
                )
                .mappings()
                .one_or_none()
            )
            return cast("Mapping[str, object] | None", row)

    def add_intake(self, values: Mapping[str, object]) -> None:
        with self.transaction() as connection:
            connection.execute(insert(adapter_intakes).values(**values))

    def intake(self, intake_id: str) -> Mapping[str, object] | None:
        with self.read() as connection:
            row = (
                connection.execute(
                    select(adapter_intakes).where(adapter_intakes.c.intake_id == intake_id)
                )
                .mappings()
                .one_or_none()
            )
            return cast("Mapping[str, object] | None", row)

    def notification_intent(self, intent_id: str) -> Mapping[str, object] | None:
        with self.read() as connection:
            row = (
                connection.execute(
                    select(register_notification_intents).where(
                        register_notification_intents.c.intent_id == intent_id
                    )
                )
                .mappings()
                .one_or_none()
            )
            return cast("Mapping[str, object] | None", row)

    def delivered_intent(self, intent_id: str) -> Mapping[str, object] | None:
        with self.read() as connection:
            row = (
                connection.execute(
                    select(notification_delivery_events)
                    .where(
                        and_(
                            notification_delivery_events.c.intent_id == intent_id,
                            notification_delivery_events.c.status == "DELIVERED",
                        )
                    )
                    .order_by(notification_delivery_events.c.recorded_at_us)
                    .limit(1)
                )
                .mappings()
                .one_or_none()
            )
            return cast("Mapping[str, object] | None", row)

    def delivery_attempt(self, attempt_id: str) -> tuple[Mapping[str, object], ...]:
        with self.read() as connection:
            return tuple(
                cast("Mapping[str, object]", row)
                for row in connection.execute(
                    select(notification_delivery_events)
                    .where(notification_delivery_events.c.attempt_id == attempt_id)
                    .order_by(notification_delivery_events.c.sequence)
                )
                .mappings()
                .all()
            )

    def add_delivery_event(
        self,
        *,
        event_id: str,
        intent_id: str,
        attempt_id: str,
        status: str,
        recorded_at: datetime,
        spool_reference: str | None = None,
        reason: str | None = None,
    ) -> None:
        with self.transaction() as connection:
            sequence = (
                int(
                    connection.scalar(
                        select(func.max(notification_delivery_events.c.sequence)).where(
                            notification_delivery_events.c.attempt_id == attempt_id
                        )
                    )
                    or 0
                )
                + 1
            )
            connection.execute(
                insert(notification_delivery_events).values(
                    event_id=event_id,
                    intent_id=intent_id,
                    attempt_id=attempt_id,
                    sequence=sequence,
                    status=status,
                    spool_reference=spool_reference,
                    reason=reason,
                    recorded_at_us=to_epoch_microseconds(recorded_at),
                )
            )

    def manifests(self) -> tuple[Mapping[str, object], ...]:
        with self.read() as connection:
            return tuple(
                cast("Mapping[str, object]", row)
                for row in connection.execute(select(register_output_manifests)).mappings().all()
            )

    def add_register_rebuild_basis(
        self, *, manifest_id: str, query_json: str, query_checksum: str, recorded_at: datetime
    ) -> None:
        with self.transaction() as connection:
            connection.execute(
                insert(operational_register_rebuild_bases).values(
                    manifest_id=manifest_id,
                    query_json=query_json,
                    query_checksum=query_checksum,
                    recorded_at_us=to_epoch_microseconds(recorded_at),
                )
            )

    def register_rebuild_bases(self) -> tuple[Mapping[str, object], ...]:
        with self.read() as connection:
            return tuple(
                cast("Mapping[str, object]", row)
                for row in connection.execute(select(operational_register_rebuild_bases))
                .mappings()
                .all()
            )

    def schema_revision(self) -> str | None:
        with self.read() as connection:
            try:
                value = connection.exec_driver_sql(
                    "SELECT version_num FROM alembic_version"
                ).scalar()
            except Exception:
                return None
        return cast("str | None", value)

    def recorded_high_water(self) -> int | None:
        with self.read() as connection:
            value = connection.exec_driver_sql(
                "SELECT MAX(recorded_at_us) FROM record_versions"
            ).scalar()
        return cast("int | None", value)

    def table_counts(self, names: tuple[str, ...]) -> dict[str, int]:
        with self.read() as connection:
            return {
                name: int(
                    connection.exec_driver_sql(f'SELECT COUNT(*) FROM "{name}"').scalar() or 0
                )
                for name in names
            }

    def audit_rows(self) -> tuple[Mapping[str, object], ...]:
        with self.read() as connection:
            return tuple(
                cast("Mapping[str, object]", row)
                for row in connection.execute(
                    select(operational_audit_facts).order_by(
                        operational_audit_facts.c.recorded_at_us,
                        operational_audit_facts.c.event_id,
                    )
                )
                .mappings()
                .all()
            )


def _validate_safe_details(value: Mapping[str, JsonValue]) -> None:
    forbidden = ("password", "token", "secret", "credential", "payload", "content")

    def visit(item: JsonValue, path: str) -> None:
        if isinstance(item, dict):
            for key, nested in item.items():
                if any(term in key.casefold() for term in forbidden):
                    raise ValueError(f"sensitive operational audit detail prohibited at {path}")
                visit(nested, f"{path}.{key}")
        elif isinstance(item, list):
            for index, nested in enumerate(item):
                visit(nested, f"{path}[{index}]")

    visit(dict(value), "details")
