from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass, replace
from pathlib import Path

import pytest
from sqlalchemy import inspect

from paim.application import (
    DomainRuleViolation,
    Increment7ApplicationService,
    IntegrityApplicationService,
)
from paim.domain import (
    ActorVersionInput,
    CaseVersionInput,
    ConfigurationMaturity,
    ConfigurationPurpose,
    ConfigurationVersionInput,
    ProjectionConsistency,
    RegisterAction,
)
from paim.integrity import EffectiveInterval, FixedClock, RecordId, RecordVersionId
from paim.operational import (
    AccessDenied,
    AccessEffect,
    AccessGrantInput,
    AdapterType,
    AuthenticationFailed,
    IntakeEnvelope,
    IntakeStatus,
    LocalConfiguration,
    OperationalApplication,
    Permission,
    PrincipalStatus,
    ReadinessState,
    RecoveryRejected,
    ScopeType,
    UnsupportedCapability,
)
from paim.persistence.ports import WriterContention
from paim.persistence.sqlite import upgrade_database
from tests.helpers import utc, version_command
from tests.integration.test_increment_4_foundation import authorization, foundation
from tests.integration.test_increment_6_reassessment import context, trigger_input
from tests.integration.test_increment_7_management_register import shared_dependency

NOW = utc(2026, 8, 19)
EFFECTIVE = EffectiveInterval(utc(2026, 1, 1))
TOKEN = "increment-8-explicit-local-token"


@dataclass
class OperationalContext:
    config: LocalConfiguration
    app: OperationalApplication
    session: object
    actor_id: RecordId


def allow(
    permission: Permission,
    action: str,
    scope_type: ScopeType = ScopeType.GLOBAL,
    scope_id: RecordId | None = None,
) -> AccessGrantInput:
    return AccessGrantInput(permission, action, scope_type, scope_id, AccessEffect.ALLOW)


@pytest.fixture
def operational(tmp_path: Path) -> Iterator[OperationalContext]:
    config = LocalConfiguration(
        database_path=tmp_path / "paim.sqlite3",
        credential_env="PAIM_TEST_TOKEN",
        intake_directory=tmp_path / "intake",
        spool_directory=tmp_path / "spool",
        export_directory=tmp_path / "export",
        backup_directory=tmp_path / "backup",
        event_log_path=tmp_path / "events" / "operational.jsonl",
    )
    for directory in (
        config.intake_directory,
        config.spool_directory,
        config.export_directory,
        config.backup_directory,
        config.event_log_path.parent,
    ):
        directory.mkdir(parents=True)
    upgrade_database(config.database_url)
    app = OperationalApplication(config, FixedClock(NOW))
    admin_actions = (
        "principal.manage",
        "access.manage",
        "backup.create",
        "restore.verify",
        "observability.read",
    )
    app.bootstrap_principal(
        principal_id="principal:local-owner",
        token=TOKEN,
        actor_id=None,
        grants=(
            allow(Permission.LOGIN, "use"),
            allow(Permission.COMMAND, "actor.create"),
            *(allow(Permission.OPERATIONAL_ADMIN, action) for action in admin_actions),
        ),
    )
    unresolved = app.authenticate("principal:local-owner", TOKEN)
    actor_id = RecordId.new()
    app.run_command(
        unresolved,
        action="actor.create",
        idempotency_key="bootstrap-actor",
        operation=lambda service, meta: service.commit_actor(
            meta,
            ActorVersionInput(
                actor_id,
                RecordVersionId.new(),
                "Local PAIM Owner",
                EFFECTIVE,
            ),
        ),
    )
    app.provision_principal(
        unresolved,
        principal_id="principal:local-owner",
        token=TOKEN,
        actor_id=actor_id,
        status=PrincipalStatus.ENABLED,
    )
    session = app.authenticate("principal:local-owner", TOKEN)
    try:
        yield OperationalContext(config, app, session, actor_id)
    finally:
        app.close()


def grant(
    ctx: OperationalContext,
    permission: Permission,
    action: str,
    scope_type: ScopeType = ScopeType.GLOBAL,
    scope_id: RecordId | None = None,
    *,
    principal_id: str = "principal:local-owner",
    effect: AccessEffect = AccessEffect.ALLOW,
) -> None:
    ctx.app.grant_access(
        ctx.session,  # type: ignore[arg-type]
        principal_id=principal_id,
        grant=AccessGrantInput(permission, action, scope_type, scope_id, effect),
    )


def case_and_configuration(ctx: OperationalContext, key: str) -> tuple[RecordId, RecordId]:
    case_id, configuration_id = RecordId.new(), RecordId.new()
    grant(ctx, Permission.COMMAND, "case.create")
    ctx.app.run_command(
        ctx.session,  # type: ignore[arg-type]
        action="case.create",
        idempotency_key=f"{key}-case",
        operation=lambda service, meta: service.commit_case(
            meta,
            CaseVersionInput(
                case_id,
                RecordVersionId.new(),
                f"Case {key}",
                EFFECTIVE,
            ),
        ),
    )
    grant(ctx, Permission.CASE_READ, "read", ScopeType.CASE, case_id)
    grant(ctx, Permission.COMMAND, "configuration.create", ScopeType.CASE, case_id)
    ctx.app.run_command(
        ctx.session,  # type: ignore[arg-type]
        action="configuration.create",
        idempotency_key=f"{key}-configuration",
        case_id=case_id,
        operation=lambda service, meta: service.commit_configuration(
            meta,
            ConfigurationVersionInput(
                configuration_id,
                RecordVersionId.new(),
                case_id,
                ConfigurationMaturity.FINALIZED,
                ConfigurationPurpose.CANDIDATE,
                {"system": key},
                EFFECTIVE,
            ),
        ),
    )
    grant(
        ctx,
        Permission.CONFIGURATION_READ,
        "read",
        ScopeType.CONFIGURATION,
        configuration_id,
    )
    return case_id, configuration_id


def envelope(
    adapter_type: AdapterType,
    case_id: RecordId | None,
    configuration_id: RecordId | None,
    *,
    replay: str,
    payload: dict[str, str] | None = None,
    source_object: str = "object-1",
    source_version: str = "v1",
    context_text: str | None = None,
) -> IntakeEnvelope:
    return IntakeEnvelope(
        adapter_type=adapter_type,
        source_system=f"fixture:{adapter_type.value.lower()}",
        source_object_id=source_object,
        source_version=source_version,
        source_effective_at=utc(2026, 8, 18),
        payload=payload or {"finding": "bounded source material"},
        replay_id=replay,
        mapper_rule_id=f"{adapter_type.value.lower()}-fixture",
        mapper_rule_version="v0.1",
        target_case_id=case_id,
        target_configuration_id=configuration_id,
        management_context=context_text,
        payload_reference=f"{source_object}.json",
    )


def test_authentication_exact_actor_gateway_restart_and_audit(
    operational: OperationalContext,
) -> None:
    case_id, _ = case_and_configuration(operational, "restart")
    session = operational.session
    assert session.actor_id == operational.actor_id  # type: ignore[attr-defined]
    operational.app.close()
    restarted = OperationalApplication(operational.config, FixedClock(NOW))
    try:
        resumed = restarted.authenticate("principal:local-owner", TOKEN)
        assert resumed.actor_id == operational.actor_id
        assert restarted.domain_store.get_history(case_id).versions
        assert restarted.operational_store.audit_rows()
    finally:
        restarted.close()


def test_unmapped_disabled_and_bad_credentials_fail_closed(
    operational: OperationalContext,
) -> None:
    app = operational.app
    session = operational.session
    app.provision_principal(
        session,  # type: ignore[arg-type]
        principal_id="principal:unmapped",
        token="unmapped-explicit-token-0001",
        actor_id=None,
        status=PrincipalStatus.ENABLED,
    )
    grant(
        operational,
        Permission.LOGIN,
        "use",
        principal_id="principal:unmapped",
    )
    grant(
        operational,
        Permission.COMMAND,
        "case.create",
        principal_id="principal:unmapped",
    )
    unresolved = app.authenticate("principal:unmapped", "unmapped-explicit-token-0001")
    with pytest.raises(AccessDenied):
        app.run_command(
            unresolved,
            action="case.create",
            idempotency_key="unmapped-case",
            operation=lambda service, meta: service.commit_case(
                meta,
                CaseVersionInput(RecordId.new(), RecordVersionId.new(), "No", EFFECTIVE),
            ),
        )
    app.provision_principal(
        session,  # type: ignore[arg-type]
        principal_id="principal:unmapped",
        token="unmapped-explicit-token-0002",
        actor_id=None,
        status=PrincipalStatus.DISABLED,
    )
    with pytest.raises(AuthenticationFailed):
        app.authenticate("principal:unmapped", "unmapped-explicit-token-0002")
    with pytest.raises(AuthenticationFailed):
        app.authenticate("principal:local-owner", "wrong-explicit-token-value")
    log = operational.config.event_log_path.read_text(encoding="utf-8")
    assert TOKEN not in log
    assert "wrong-explicit-token-value" not in log


def test_operational_admin_and_software_permission_do_not_create_decision_authority(
    operational: OperationalContext,
) -> None:
    fx = foundation(operational.app.domain_store, "ops-authority")
    basis = authorization(fx, "ops-authority")
    case_id = fx.context.case_id
    configuration_id = fx.context.configuration_id
    grant(operational, Permission.CASE_READ, "read", ScopeType.CASE, case_id)
    grant(
        operational,
        Permission.CONFIGURATION_READ,
        "read",
        ScopeType.CONFIGURATION,
        configuration_id,
    )
    with pytest.raises(AccessDenied):
        operational.app.run_command(
            operational.session,  # type: ignore[arg-type]
            action="decision.authorize",
            idempotency_key="admin-is-not-authority",
            case_id=case_id,
            configuration_id=configuration_id,
            operation=lambda service, meta: service.authorize_decision(meta, basis),
        )
    grant(
        operational,
        Permission.COMMAND,
        "decision.authorize",
        ScopeType.CASE,
        case_id,
    )
    unauthorized_basis = replace(
        basis,
        authorization_actor_id=operational.actor_id,
        decision_authority_identity=str(operational.actor_id),
    )
    with pytest.raises(DomainRuleViolation):
        operational.app.run_command(
            operational.session,  # type: ignore[arg-type]
            action="decision.authorize",
            idempotency_key="permission-is-not-authority",
            case_id=case_id,
            configuration_id=configuration_id,
            claimed_actor_id=operational.actor_id,
            operation=lambda service, meta: service.authorize_decision(meta, unauthorized_basis),
        )


def _register_sources(
    operational: OperationalContext,
) -> tuple[RecordId, RecordId, RecordId, RecordId]:
    visible_case, visible_configuration = case_and_configuration(operational, "visible")
    hidden_case, hidden_configuration = case_and_configuration(operational, "hidden")
    grant(
        operational,
        Permission.CASE_READ,
        "read",
        ScopeType.CASE,
        hidden_case,
        effect=AccessEffect.DENY,
    )
    service = Increment7ApplicationService(operational.app.domain_store, FixedClock(NOW))
    _dependency_id, dependency_version = shared_dependency(service, "operational")
    integrity = IntegrityApplicationService(operational.app.domain_store, FixedClock(NOW))
    for key, case_id, configuration_id in (
        ("visible", visible_case, visible_configuration),
        ("hidden", hidden_case, hidden_configuration),
    ):
        identity, version = RecordId.new(), RecordVersionId.new()
        integrity.commit_version(
            version_command(
                record_id=identity,
                version_id=version,
                family="authority-gap",
                scope=f"authority-gap:{identity}",
                content={
                    "case_id": str(case_id),
                    "configuration_id": str(configuration_id),
                    "shared_dependency_version_id": str(dependency_version),
                    "outcome": "UNRESOLVED",
                    "source": key,
                },
                idempotency_key=f"operational-register-{key}",
            )
        )
    return visible_case, visible_configuration, hidden_case, hidden_configuration


def test_register_query_filters_hidden_case_and_group_without_count_or_id_leak(
    operational: OperationalContext,
) -> None:
    visible_case, visible_configuration, hidden_case, hidden_configuration = _register_sources(
        operational
    )
    view = operational.app.derive_register(
        operational.session,  # type: ignore[arg-type]
        requested_case_ids=frozenset({visible_case, hidden_case}),
        requested_configuration_ids=frozenset({visible_configuration, hidden_configuration}),
        effective_at=NOW,
        known_at=NOW,
        rule_id="management-register-population",
        rule_version="v0.1",
    )
    assert {entry.key.case_id for entry in view.entries} == {visible_case}
    assert len(view.groups) == 1
    group = view.groups[0]
    assert group.access_filtered
    assert group.global_constituent_count is None
    represented = json.dumps(
        operational.app._service._view_content(view),
        sort_keys=True,
    )
    assert str(hidden_case) not in represented
    assert str(hidden_configuration) not in represented


@pytest.mark.parametrize(
    "adapter_type,table",
    [
        (AdapterType.VALUE, "analytical_input_versions"),
        (AdapterType.RISK, "analytical_input_versions"),
        (AdapterType.EVIDENCE, "evidence_versions"),
        (AdapterType.AUTHORITY, "authority_record_versions"),
    ],
)
def test_manual_adapter_intake_is_proposed_independent_and_non_authoritative(
    operational: OperationalContext,
    adapter_type: AdapterType,
    table: str,
) -> None:
    case_id, configuration_id = case_and_configuration(operational, adapter_type.value)
    grant(operational, Permission.COMMAND, f"intake.{adapter_type.value.lower()}")
    before = operational.app.domain_store.count_rows(table)
    result = operational.app.intake(
        operational.session,  # type: ignore[arg-type]
        envelope(adapter_type, case_id, configuration_id, replay=f"replay-{adapter_type.value}"),
    )
    assert result.status is IntakeStatus.PROPOSED
    assert operational.app.domain_store.count_rows(table) == before
    value_rows = operational.app.operational_store.intake_replays(
        adapter_type, f"fixture:{adapter_type.value.lower()}", f"replay-{adapter_type.value}"
    )
    assert len(value_rows) == 1


def test_value_risk_independence_and_adapter_failure_create_no_authoritative_record(
    operational: OperationalContext, monkeypatch: pytest.MonkeyPatch
) -> None:
    case_id, configuration_id = case_and_configuration(operational, "independent")
    grant(operational, Permission.COMMAND, "intake.value")
    grant(operational, Permission.COMMAND, "intake.risk")
    value = operational.app.intake(
        operational.session,  # type: ignore[arg-type]
        envelope(AdapterType.VALUE, case_id, configuration_id, replay="value-only"),
    )
    risk = operational.app.intake(
        operational.session,  # type: ignore[arg-type]
        envelope(AdapterType.RISK, case_id, configuration_id, replay="risk-only"),
    )
    assert value.intake_id != risk.intake_id
    assert operational.app.operational_store.intake(value.intake_id)["adapter_type"] == "VALUE"
    assert operational.app.operational_store.intake(risk.intake_id)["adapter_type"] == "RISK"
    assert operational.app.domain_store.count_rows("analytical_input_versions") == 0

    def fail_intake(*_: object, **__: object) -> None:
        raise OSError("fixture adapter unavailable")

    monkeypatch.setattr(operational.app.operational_store, "add_intake", fail_intake)
    with pytest.raises(OSError, match="adapter unavailable"):
        operational.app.intake(
            operational.session,  # type: ignore[arg-type]
            envelope(AdapterType.VALUE, case_id, configuration_id, replay="failed-value"),
        )
    assert operational.app.domain_store.count_rows("analytical_input_versions") == 0


def test_adapter_quarantine_replay_mismatch_and_source_successor(
    operational: OperationalContext,
) -> None:
    case_id, configuration_id = case_and_configuration(operational, "adapter")
    grant(operational, Permission.COMMAND, "intake.evidence")
    first = envelope(AdapterType.EVIDENCE, case_id, configuration_id, replay="same")
    accepted = operational.app.intake(operational.session, first)  # type: ignore[arg-type]
    replayed = operational.app.intake(operational.session, first)  # type: ignore[arg-type]
    assert replayed.replayed and replayed.intake_id == accepted.intake_id
    mismatch = operational.app.intake(
        operational.session,  # type: ignore[arg-type]
        replace(first, payload={"finding": "changed"}),
    )
    assert mismatch.status is IntakeStatus.QUARANTINED
    assert mismatch.quarantine_reason == "REPLAY_ID_PAYLOAD_MISMATCH"
    successor = operational.app.intake(
        operational.session,  # type: ignore[arg-type]
        replace(first, replay_id="next", source_version="v2", payload={"finding": "changed"}),
    )
    assert successor.status is IntakeStatus.PROPOSED
    assert successor.supersedes_intake_id == accepted.intake_id
    ambiguous = operational.app.intake(
        operational.session,  # type: ignore[arg-type]
        envelope(AdapterType.EVIDENCE, None, None, replay="ambiguous"),
    )
    assert ambiguous.status is IntakeStatus.QUARANTINED


def test_external_event_promotes_exact_trigger_without_observation_or_semantic_deduplication(
    operational: OperationalContext,
) -> None:
    ctx = context(operational.app.domain_store, "external-trigger")
    case_id = ctx.foundation.context.case_id
    configuration_id = ctx.foundation.context.configuration_id
    grant(operational, Permission.CASE_READ, "read", ScopeType.CASE, case_id)
    grant(
        operational,
        Permission.CONFIGURATION_READ,
        "read",
        ScopeType.CONFIGURATION,
        configuration_id,
    )
    grant(operational, Permission.COMMAND, "intake.external_trigger")
    grant(
        operational,
        Permission.COMMAND,
        "trigger.create",
        ScopeType.CASE,
        case_id,
    )
    first = operational.app.intake(
        operational.session,  # type: ignore[arg-type]
        envelope(
            AdapterType.EXTERNAL_TRIGGER,
            case_id,
            configuration_id,
            replay="event-1",
            source_object="event-1",
            context_text="Does the exact current Decision require reassessment?",
        ),
    )
    trigger = trigger_input(ctx, "external-event")
    operational.app.promote_intake(
        operational.session,  # type: ignore[arg-type]
        intake_id=first.intake_id,
        action="trigger.create",
        idempotency_key="external-trigger-create",
        operation=lambda service, meta: service.commit_trigger(meta, trigger),
    )
    similar = operational.app.intake(
        operational.session,  # type: ignore[arg-type]
        envelope(
            AdapterType.EXTERNAL_TRIGGER,
            case_id,
            configuration_id,
            replay="event-2",
            source_object="event-2",
            context_text="Does the exact current Decision require reassessment?",
        ),
    )
    assert similar.intake_id != first.intake_id
    assert operational.app.domain_store.count_rows("trigger_versions") == 1
    assert (
        "observation_records" not in inspect(operational.app.domain_store.engine).get_table_names()
    )


def _manifest_and_intent(
    operational: OperationalContext,
) -> tuple[str, str, int]:
    visible_case, visible_configuration, hidden_case, hidden_configuration = _register_sources(
        operational
    )
    grant(operational, Permission.EXPORT, "register.output")
    grant(operational, Permission.EXPORT, "register.export")
    grant(operational, Permission.DELIVERY, "notification.deliver")
    view = operational.app.derive_register(
        operational.session,  # type: ignore[arg-type]
        requested_case_ids=frozenset({visible_case, hidden_case}),
        requested_configuration_ids=frozenset({visible_configuration, hidden_configuration}),
        effective_at=NOW,
        known_at=NOW,
        rule_id="management-register-population",
        rule_version="v0.1",
    )
    manifest = operational.app.persist_register_output(
        operational.session,
        view,
        output_kind="EXPORT",  # type: ignore[arg-type]
    )
    intents = operational.app._service.generate_notification_intents(
        manifest, view, channel="local-spool", recipient_scope="case-owner"
    )
    return (
        manifest.manifest_id,
        intents[0].intent_id,
        operational.app.domain_store.count_rows("authority_gap_versions"),
    )


def test_notification_failure_retry_and_exact_json_csv_exports(
    operational: OperationalContext,
) -> None:
    manifest_id, intent_id, authoritative_before = _manifest_and_intent(operational)
    failed = operational.app.deliver_notification(
        operational.session,  # type: ignore[arg-type]
        intent_id=intent_id,
        attempt_id="attempt-failed",
        simulate_failure=True,
    )
    assert failed.status.value == "FAILED"
    assert operational.app.domain_store.count_rows("authority_gap_versions") == authoritative_before
    delivered = operational.app.deliver_notification(
        operational.session,  # type: ignore[arg-type]
        intent_id=intent_id,
        attempt_id="attempt-retry",
    )
    replay = operational.app.deliver_notification(
        operational.session,  # type: ignore[arg-type]
        intent_id=intent_id,
        attempt_id="attempt-retry",
    )
    assert delivered.status.value == "DELIVERED"
    assert replay.replayed
    another_attempt = operational.app.deliver_notification(
        operational.session,  # type: ignore[arg-type]
        intent_id=intent_id,
        attempt_id="attempt-after-delivered",
    )
    assert another_attempt.replayed
    assert another_attempt.attempt_id == "attempt-retry"
    assert len(tuple(operational.config.spool_directory.glob("*.json"))) == 1
    json_path = operational.app.export_manifest(
        operational.session,
        manifest_id,
        output_format="json",  # type: ignore[arg-type]
    )
    csv_path = operational.app.export_manifest(
        operational.session,
        manifest_id,
        output_format="csv",  # type: ignore[arg-type]
    )
    exported = json.loads(json_path.read_text(encoding="utf-8"))
    assert exported["manifest_id"] == manifest_id
    assert exported["manifest_checksum"]
    assert exported["processed_watermark"] == exported["content"]["processed_watermark"]
    csv_text = csv_path.read_text(encoding="utf-8")
    assert "manifest_checksum" in csv_text
    assert "access_filtered" in csv_text


def test_backup_restore_integrity_tamper_schema_and_restart_preservation(
    operational: OperationalContext,
) -> None:
    case_id, _ = case_and_configuration(operational, "backup")
    _manifest_and_intent(operational)
    backup, manifest_path, manifest = operational.app.backup(
        operational.session,
        label="clean",  # type: ignore[arg-type]
    )
    restored = operational.config.backup_directory / "restored.sqlite3"
    result = operational.app.restore(
        operational.session,  # type: ignore[arg-type]
        backup_path=backup,
        manifest_path=manifest_path,
        target_path=restored,
    )
    assert result.backup_checksum == manifest.backup_checksum
    restored_config = replace(operational.config, database_path=restored)
    with OperationalApplication(restored_config, FixedClock(NOW)) as restored_app:
        resumed = restored_app.authenticate("principal:local-owner", TOKEN)
        assert resumed.actor_id == operational.actor_id
        assert restored_app.domain_store.get_history(case_id).versions
        assert restored_app.health().state is ReadinessState.READY

    tampered = operational.config.backup_directory / "tampered.sqlite3"
    tampered.write_bytes(backup.read_bytes() + b"tamper")
    with pytest.raises(RecoveryRejected):
        operational.app.restore(
            operational.session,  # type: ignore[arg-type]
            backup_path=tampered,
            manifest_path=manifest_path,
            target_path=operational.config.backup_directory / "tampered-restore.sqlite3",
        )
    incompatible_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    incompatible_data["schema_revision"] = "0007_increment_7"
    incompatible = operational.config.backup_directory / "incompatible.manifest.json"
    incompatible.write_text(json.dumps(incompatible_data), encoding="utf-8")
    with pytest.raises(RecoveryRejected):
        operational.app.restore(
            operational.session,  # type: ignore[arg-type]
            backup_path=backup,
            manifest_path=incompatible,
            target_path=operational.config.backup_directory / "incompatible.sqlite3",
        )


def test_health_degraded_database_failure_unsupported_boundaries_and_counters(
    operational: OperationalContext,
) -> None:
    assert operational.app.health().state is ReadinessState.READY
    operational.config.spool_directory.rmdir()
    degraded = operational.app.health()
    assert degraded.process_alive
    assert degraded.state is ReadinessState.DEGRADED
    assert "DELIVERY_SPOOL_UNAVAILABLE" in degraded.reasons
    operational.config.spool_directory.mkdir()
    for capability in (
        "OBSERVATION_AUTOMATION",
        "OPERATING_STATE_RANKING",
        "LIVE_PROVIDER_INTEGRATION",
        "GENERIC_REGISTER_RESOLUTION",
    ):
        with pytest.raises(UnsupportedCapability):
            operational.app.require_supported(capability)
    counters = operational.app.counters(operational.session)  # type: ignore[arg-type]
    assert counters["AUTHENTICATION:SUCCESS"] >= 1
    assert not any(
        "OBSERVATION" in table
        for table in operational.app.operational_store.table_counts(("adapter_intakes",))
    )


def test_database_contention_blocks_commit_and_stale_register_blocks_action(
    operational: OperationalContext,
) -> None:
    grant(operational, Permission.COMMAND, "case.create")

    def contention(_: Increment7ApplicationService, __: object) -> None:
        raise WriterContention("SQLITE WRITER CONTENTION")

    with pytest.raises(WriterContention):
        operational.app.run_command(
            operational.session,  # type: ignore[arg-type]
            action="case.create",
            idempotency_key="contention-blocks-commit",
            operation=contention,  # type: ignore[arg-type]
        )
    failure = operational.app.operational_store.audit_rows()[-1]
    assert failure["category"] == "COMMAND"
    assert failure["outcome"] == "FAILURE"
    assert failure["reason_category"] == "WRITERCONTENTION"

    current_view = operational.app.derive_register(
        operational.session,  # type: ignore[arg-type]
        requested_case_ids=frozenset(),
        requested_configuration_ids=frozenset(),
        effective_at=NOW,
        known_at=NOW,
        rule_id="management-register-population",
        rule_version="v0.1",
        processed_watermark=utc(2026, 8, 18),
    )
    view = replace(current_view, consistency=ProjectionConsistency.STALE)
    with pytest.raises(DomainRuleViolation, match="stale or inconsistent"):
        operational.app.launch_register_action(
            operational.session,  # type: ignore[arg-type]
            view,
            RegisterAction.READ,
            None,  # type: ignore[arg-type]
        )
