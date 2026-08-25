"""SQLite-safe backup, separate restore verification, and readiness checks."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
from contextlib import closing
from dataclasses import asdict, replace
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, cast

from paim.application import Increment7ApplicationService
from paim.domain import RegisterLifecycle, RegisterQuery
from paim.integrity import FixedClock, RecordId
from paim.integrity.records import JsonValue
from paim.operational.models import (
    AuthenticatedSession,
    BackupManifest,
    HealthReport,
    ReadinessState,
    RecoveryRejected,
)
from paim.persistence.sqlite import SQLiteIntegrityStore

if TYPE_CHECKING:
    from paim.operational.application import OperationalApplication

_EXPECTED_REVISION = "0011_gate8_case_continuity"
_APPLICATION_VERSION = "0.1.0"
_OPERATIONAL_TABLES = (
    "operational_principals",
    "operational_principal_versions",
    "software_access_grants",
    "operational_audit_facts",
    "adapter_intakes",
    "notification_delivery_events",
    "operational_register_rebuild_bases",
)
_CORE_TRIGGER_NAMES = {
    "prevent_finalized_version_update",
    "prevent_record_version_delete",
    "prevent_status_event_update",
    "prevent_status_event_delete",
    "prevent_relationship_update",
    "prevent_relationship_delete",
    "prevent_idempotency_update",
    "prevent_idempotency_delete",
    "prevent_audit_update",
    "prevent_audit_delete",
}
_OPERATIONAL_TRIGGER_NAMES = {
    f"prevent_{table}_{action}" for table in _OPERATIONAL_TABLES for action in ("update", "delete")
}


def _checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def _all_table_counts(connection: sqlite3.Connection) -> dict[str, int]:
    names = tuple(
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' AND name <> 'alembic_version' ORDER BY name"
        )
    )
    return {
        name: int(connection.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0])
        for name in names
    }


def _manifest_json(manifest: BackupManifest) -> str:
    value = asdict(manifest)
    value["created_at"] = manifest.created_at.isoformat()
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _parse_manifest(path: Path) -> BackupManifest:
    try:
        raw = cast("dict[str, object]", json.loads(path.read_text(encoding="utf-8")))
        created_at = datetime.fromisoformat(cast("str", raw["created_at"]))
        counts = {
            str(key): int(cast("str | int | float", value))
            for key, value in cast("dict[str, object]", raw["record_counts"]).items()
        }
        return BackupManifest(
            application_version=cast("str", raw["application_version"]),
            schema_revision=cast("str", raw["schema_revision"]),
            created_at=created_at,
            source_database_label=cast("str", raw["source_database_label"]),
            backup_file=cast("str", raw["backup_file"]),
            backup_checksum=cast("str", raw["backup_checksum"]),
            backup_size=int(cast("int", raw["backup_size"])),
            source_high_water_us=cast("int | None", raw["source_high_water_us"]),
            included_derived_outputs=bool(raw["included_derived_outputs"]),
            record_counts=counts,
            operator_principal_id=cast("str", raw["operator_principal_id"]),
            audit_event_id=cast("str", raw["audit_event_id"]),
        )
    except (OSError, ValueError, TypeError, KeyError) as error:
        raise RecoveryRejected("backup manifest is invalid or incomplete") from error


def create_backup(
    app: OperationalApplication,
    session: AuthenticatedSession,
    *,
    label: str,
) -> tuple[Path, Path, BackupManifest]:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", label):
        raise ValueError("backup label must be a bounded safe filename component")
    audit_event_id = app._audit_session(
        session,
        category="BACKUP",
        outcome="PENDING",
        action="backup.create",
        reason="APPLICATION_CONSISTENT_SNAPSHOT_STARTED",
        details={"backup_label": label},
    )
    created_at = app.clock.now()
    backup_path = app.config.backup_directory / f"{label}.sqlite3"
    manifest_path = app.config.backup_directory / f"{label}.manifest.json"
    if backup_path.exists() or manifest_path.exists():
        raise FileExistsError("backup label already exists")
    try:
        with closing(sqlite3.connect(app.config.database_path)) as source:
            source.execute("PRAGMA foreign_keys=ON")
            with closing(sqlite3.connect(backup_path)) as target:
                source.backup(target)
            counts = _all_table_counts(source)
            row = source.execute("SELECT MAX(recorded_at_us) FROM record_versions").fetchone()
            high_water = cast("int | None", row[0])
            revision = cast(
                "str", source.execute("SELECT version_num FROM alembic_version").fetchone()[0]
            )
        if revision != _EXPECTED_REVISION:
            raise RecoveryRejected("active database schema is not compatible with this PAIM binary")
        manifest = BackupManifest(
            application_version=_APPLICATION_VERSION,
            schema_revision=revision,
            created_at=created_at,
            source_database_label=app.config.database_path.name,
            backup_file=backup_path.name,
            backup_checksum=_checksum(backup_path),
            backup_size=backup_path.stat().st_size,
            source_high_water_us=high_water,
            included_derived_outputs=True,
            record_counts=counts,
            operator_principal_id=session.principal_id,
            audit_event_id=audit_event_id,
        )
        manifest_path.write_text(_manifest_json(manifest), encoding="utf-8")
    except BaseException:
        if backup_path.exists():
            backup_path.unlink()
        if manifest_path.exists():
            manifest_path.unlink()
        app._audit_session(
            session,
            category="BACKUP",
            outcome="FAILURE",
            action="backup.create",
            reason="SNAPSHOT_NOT_ESTABLISHED",
            details={"backup_label": label},
        )
        raise
    app._audit_session(
        session,
        category="BACKUP",
        outcome="SUCCESS",
        action="backup.create",
        reason="SNAPSHOT_AND_MANIFEST_ESTABLISHED",
        details={
            "backup_label": label,
            "backup_checksum": manifest.backup_checksum,
            "backup_size": manifest.backup_size,
        },
    )
    return backup_path, manifest_path, manifest


def restore_backup(
    app: OperationalApplication,
    session: AuthenticatedSession,
    *,
    backup_path: Path,
    manifest_path: Path,
    target_path: Path,
) -> BackupManifest:
    active = app.config.database_path.resolve()
    backup = backup_path.resolve()
    target = target_path.resolve()
    if target in (active, backup):
        raise RecoveryRejected("restore target must be separate from active and backup databases")
    if target.exists():
        raise RecoveryRejected("restore target already exists")
    manifest = _parse_manifest(manifest_path)
    if backup.name != manifest.backup_file:
        raise RecoveryRejected("backup filename does not match manifest")
    if (
        _checksum(backup) != manifest.backup_checksum
        or backup.stat().st_size != manifest.backup_size
    ):
        raise RecoveryRejected("backup checksum or size does not match manifest")
    if (
        manifest.schema_revision != _EXPECTED_REVISION
        or manifest.application_version != _APPLICATION_VERSION
    ):
        raise RecoveryRejected("backup schema or application version is incompatible")
    temporary = target.with_name(f".{target.name}.{RecordId.new()}.candidate")
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with (
            closing(sqlite3.connect(backup)) as source,
            closing(sqlite3.connect(temporary)) as candidate,
        ):
            source.backup(candidate)
        _verify_database(temporary, manifest)
        _verify_register_manifests(temporary)
        os.replace(temporary, target)
    except BaseException:
        if temporary.exists():
            temporary.unlink()
        app._audit_session(
            session,
            category="RESTORE",
            outcome="REJECTED",
            action="restore.verify",
            reason="RESTORE_CANDIDATE_REJECTED",
            details={"backup_checksum": manifest.backup_checksum},
        )
        raise
    app._audit_session(
        session,
        category="RESTORE",
        outcome="SUCCESS",
        action="restore.verify",
        reason="SEPARATE_RESTORE_VERIFIED",
        details={"backup_checksum": manifest.backup_checksum, "target_label": target.name},
    )
    return manifest


def _verify_database(path: Path, manifest: BackupManifest) -> None:
    try:
        with closing(sqlite3.connect(path)) as connection:
            connection.execute("PRAGMA foreign_keys=ON")
            revision_row = connection.execute("SELECT version_num FROM alembic_version").fetchone()
            if revision_row is None or revision_row[0] != manifest.schema_revision:
                raise RecoveryRejected("restored schema revision does not match manifest")
            integrity = connection.execute("PRAGMA integrity_check").fetchall()
            if integrity != [("ok",)]:
                raise RecoveryRejected("SQLite integrity check failed")
            if connection.execute("PRAGMA foreign_key_check").fetchall():
                raise RecoveryRejected("SQLite foreign-key check failed")
            triggers = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='trigger'"
                ).fetchall()
            }
            if not triggers >= (_CORE_TRIGGER_NAMES | _OPERATIONAL_TRIGGER_NAMES):
                raise RecoveryRejected("required append-only triggers are not established")
            counts = _all_table_counts(connection)
            if counts != manifest.record_counts:
                raise RecoveryRejected("restored record counts do not match backup basis")
            high_water = connection.execute(
                "SELECT MAX(recorded_at_us) FROM record_versions"
            ).fetchone()[0]
            if high_water != manifest.source_high_water_us:
                raise RecoveryRejected("restored source high-water does not match manifest")
    except sqlite3.DatabaseError as error:
        raise RecoveryRejected(
            "restore candidate is not a valid compatible SQLite database"
        ) from error


def _verify_register_manifests(path: Path) -> None:
    database_url = f"sqlite+pysqlite:///{path.as_posix()}"
    store = SQLiteIntegrityStore(database_url)
    try:
        with store.read_transaction() as transaction:
            rows = tuple(
                transaction.connection.exec_driver_sql(
                    "SELECT manifest_id, content_json, checksum FROM register_output_manifests"
                ).mappings()
            )
            bases = {
                cast("str", row["manifest_id"]): row
                for row in transaction.connection.exec_driver_sql(
                    "SELECT manifest_id, query_json, query_checksum "
                    "FROM operational_register_rebuild_bases"
                ).mappings()
            }
            for row in rows:
                content_json = cast("str", row["content_json"])
                checksum = hashlib.sha256(content_json.encode("utf-8")).hexdigest()
                if checksum != row["checksum"]:
                    raise RecoveryRejected("retained Register manifest checksum is inconsistent")
                content = cast("dict[str, JsonValue]", json.loads(content_json))
                _validate_register_content(content)
                basis = bases.get(cast("str", row["manifest_id"]))
                if basis is not None:
                    _verify_register_rebuild(store, content_json, content, basis)
    finally:
        store.dispose()


def _validate_register_content(content: dict[str, JsonValue]) -> None:
    required = {
        "generated_at",
        "effective_at",
        "known_at",
        "rule_id",
        "rule_version",
        "source_high_water",
        "processed_watermark",
        "consistency",
        "access_context",
        "filters",
        "ordering",
        "entries",
        "groups",
    }
    if not required <= content.keys():
        raise RecoveryRejected("Register manifest reconstruction basis is incomplete")
    entries = content["entries"]
    groups = content["groups"]
    if not isinstance(entries, list) or not isinstance(groups, list):
        raise RecoveryRejected("Register manifest rows are invalid")
    # The exact retained source/version basis must remain internally
    # reconstructable. Full semantic re-derivation is exercised by the
    # Increment 8 backup/restore scenario with a caller-specific query.
    for entry in entries:
        if not isinstance(entry, dict) or not entry.get("key") or not entry.get("source_versions"):
            raise RecoveryRejected("Register entry reconstruction basis is incomplete")
    for group in groups:
        if not isinstance(group, dict) or not group.get("dependency_record_id"):
            raise RecoveryRejected("Register group reconstruction basis is incomplete")


def _verify_register_rebuild(
    store: SQLiteIntegrityStore,
    content_json: str,
    content: dict[str, JsonValue],
    basis: object,
) -> None:
    row = cast("dict[str, object]", basis)
    query_json = cast("str", row["query_json"])
    if hashlib.sha256(query_json.encode("utf-8")).hexdigest() != row["query_checksum"]:
        raise RecoveryRejected("Register rebuild query checksum is inconsistent")
    try:
        raw = cast("dict[str, object]", json.loads(query_json))
        generated_at = datetime.fromisoformat(cast("str", content["generated_at"]))
        known_text = cast("str | None", raw["known_at"])
        watermark_text = cast("str | None", raw["processed_watermark"])
        query = RegisterQuery(
            case_ids=frozenset(RecordId.parse(item) for item in cast("list[str]", raw["case_ids"])),
            configuration_ids=frozenset(
                RecordId.parse(item) for item in cast("list[str]", raw["configuration_ids"])
            ),
            effective_at=datetime.fromisoformat(cast("str", raw["effective_at"])),
            known_at=datetime.fromisoformat(known_text) if known_text else None,
            rule_id=cast("str", raw["rule_id"]),
            rule_version=cast("str", raw["rule_version"]),
            access_context=cast("str", raw["access_context"]),
            accessible_case_ids=frozenset(
                RecordId.parse(item) for item in cast("list[str]", raw["accessible_case_ids"])
            ),
            lifecycle_filter=frozenset(
                RegisterLifecycle(item) for item in cast("list[str]", raw["lifecycle_filter"])
            ),
            order_by=tuple(cast("list[str]", raw["order_by"])),
            processed_watermark=(
                datetime.fromisoformat(watermark_text) if watermark_text else None
            ),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise RecoveryRejected("Register rebuild query basis is invalid") from error
    service = Increment7ApplicationService(store, FixedClock(generated_at))
    rebuilt = service.derive_management_register(query)
    rebuilt = replace(
        rebuilt,
        filters=(
            "case_ids:ACCESS_SCOPED",
            "configuration_ids:ACCESS_SCOPED",
            "lifecycle:" + ",".join(sorted(item.value for item in query.lifecycle_filter)),
            f"access_context:{query.access_context}",
        ),
    )
    rebuilt_json = json.dumps(service._view_content(rebuilt), sort_keys=True, separators=(",", ":"))
    if rebuilt_json != content_json:
        raise RecoveryRejected("Management Register deterministic rebuild does not match manifest")


def health_report(app: OperationalApplication) -> HealthReport:
    reasons: list[str] = []
    database_reachable = False
    schema_compatible = False
    integrity_usable = False
    foreign_keys_usable = False
    projection_usable = False
    try:
        with closing(sqlite3.connect(app.config.database_path)) as connection:
            database_reachable = connection.execute("SELECT 1").fetchone() == (1,)
            revision = connection.execute("SELECT version_num FROM alembic_version").fetchone()
            schema_compatible = revision is not None and revision[0] == _EXPECTED_REVISION
            integrity_usable = connection.execute("PRAGMA quick_check").fetchall() == [("ok",)]
            foreign_keys_usable = not connection.execute("PRAGMA foreign_key_check").fetchall()
            manifests = connection.execute(
                "SELECT content_json, checksum FROM register_output_manifests"
            ).fetchall()
            projection_usable = all(
                hashlib.sha256(content.encode("utf-8")).hexdigest() == checksum
                for content, checksum in manifests
            )
    except (OSError, sqlite3.DatabaseError):
        reasons.append("DATABASE_UNAVAILABLE")
    if database_reachable and not schema_compatible:
        reasons.append("SCHEMA_REVISION_MISMATCH")
    if database_reachable and not integrity_usable:
        reasons.append("DATABASE_INTEGRITY_UNAVAILABLE")
    if database_reachable and not foreign_keys_usable:
        reasons.append("FOREIGN_KEY_INTEGRITY_UNAVAILABLE")
    if database_reachable and not projection_usable:
        reasons.append("REGISTER_PROJECTION_PATH_UNAVAILABLE")
    directories_usable = True
    for directory in (
        app.config.intake_directory,
        app.config.export_directory,
        app.config.backup_directory,
        app.config.event_log_path.parent,
    ):
        if not directory.is_dir() or not os.access(directory, os.R_OK | os.W_OK):
            directories_usable = False
    if not directories_usable:
        reasons.append("REQUIRED_DIRECTORY_UNAVAILABLE")
    spool_usable = app.config.spool_directory.is_dir() and os.access(
        app.config.spool_directory, os.R_OK | os.W_OK
    )
    if not spool_usable:
        reasons.append("DELIVERY_SPOOL_UNAVAILABLE")
    ready = all(
        (
            database_reachable,
            schema_compatible,
            integrity_usable,
            foreign_keys_usable,
            directories_usable,
            spool_usable,
            projection_usable,
        )
    )
    return HealthReport(
        process_alive=True,
        database_reachable=database_reachable,
        schema_compatible=schema_compatible,
        integrity_usable=integrity_usable,
        foreign_keys_usable=foreign_keys_usable,
        directories_usable=directories_usable,
        spool_usable=spool_usable,
        projection_path_usable=projection_usable,
        state=ReadinessState.READY if ready else ReadinessState.DEGRADED,
        reasons=tuple(reasons),
    )
