from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from dataclasses import dataclass, replace
from pathlib import Path

import pytest
from sqlalchemy import inspect

from paim.application import Increment7ApplicationService
from paim.domain import (
    ActorVersionInput,
    ApplicabilityOutcome,
    ApplicabilityTargetType,
    AuthorityGapOutcome,
    AuthorityGapVersionInput,
    CaseLifecycleState,
    CompletionAcceptanceStatus,
    DependencyCandidateMember,
    EvidenceApplicabilityVersionInput,
    EvidenceAttention,
    EvidenceClassification,
    EvidenceVersionInput,
    LearningItemVersionInput,
    LearningStatus,
    ProjectionConsistency,
    ReassessmentDeterminationKind,
    ReassessmentDeterminationOutcome,
    ReassessmentDeterminationVersionInput,
    ReassessmentStatus,
    RegisterAction,
    TriggerCoverageState,
    TriggerDeterminationOutcome,
    TriggerDeterminationVersionInput,
)
from paim.integrity import EffectiveInterval, FixedClock, RecordId, RecordVersionId
from paim.operational import (
    AccessEffect,
    AdapterType,
    AuthenticationFailed,
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
from paim.persistence.sqlite import upgrade_database
from tests.helpers import utc
from tests.integration.test_increment_5_intervention_learning import _activation, _complete, _setup
from tests.integration.test_increment_6_reassessment import (
    confirmation,
    context,
    disposition,
    ready_for_completion,
    reassessment_input,
    trigger_input,
)
from tests.integration.test_increment_7_management_register import (
    candidate_set,
    determiner_assignment,
    equivalence,
    shared_dependency,
)
from tests.integration.test_increment_8_operational import (
    allow,
    case_and_configuration,
    envelope,
    grant,
)

NOW = utc(2026, 2, 1)
EFFECTIVE = EffectiveInterval(utc(2026, 1, 1))
TOKEN = "increment-9-explicit-local-token"


@dataclass
class Increment9Gateway:
    config: LocalConfiguration
    app: OperationalApplication
    session: object
    actor_id: RecordId


@pytest.fixture
def increment9_gateway(tmp_path: Path) -> Iterator[Increment9Gateway]:
    config = LocalConfiguration(
        database_path=tmp_path / "paim.sqlite3",
        credential_env="PAIM_INCREMENT_9_TOKEN",
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
    app.bootstrap_principal(
        principal_id="principal:increment-9-practitioner",
        token=TOKEN,
        actor_id=None,
        grants=(
            allow(Permission.LOGIN, "use"),
            allow(Permission.COMMAND, "actor.create"),
            allow(Permission.OPERATIONAL_ADMIN, "principal.manage"),
            allow(Permission.OPERATIONAL_ADMIN, "access.manage"),
            allow(Permission.OPERATIONAL_ADMIN, "backup.create"),
            allow(Permission.OPERATIONAL_ADMIN, "restore.verify"),
            allow(Permission.OPERATIONAL_ADMIN, "observability.read"),
        ),
    )
    unresolved = app.authenticate("principal:increment-9-practitioner", TOKEN)
    actor_id = RecordId.new()
    app.run_command(
        unresolved,
        action="actor.create",
        idempotency_key="increment-9-practitioner-actor",
        operation=lambda service, meta: service.commit_actor(
            meta,
            ActorVersionInput(
                actor_id,
                RecordVersionId.new(),
                "Increment 9 validating practitioner",
                EFFECTIVE,
            ),
        ),
    )
    app.provision_principal(
        unresolved,
        principal_id="principal:increment-9-practitioner",
        token=TOKEN,
        actor_id=actor_id,
        status=PrincipalStatus.ENABLED,
    )
    session = app.authenticate("principal:increment-9-practitioner", TOKEN)
    try:
        yield Increment9Gateway(config, app, session, actor_id)
    finally:
        app.close()


def run_gateway[T](
    ctx: Increment9Gateway,
    *,
    action: str,
    key: str,
    operation: Callable[[Increment7ApplicationService, object], T],
    case_id: RecordId | None = None,
    configuration_id: RecordId | None = None,
    claimed_actor: bool = False,
) -> T:
    grant(
        ctx,  # type: ignore[arg-type]
        Permission.COMMAND,
        action,
        ScopeType.CASE if case_id else ScopeType.GLOBAL,
        case_id,
        principal_id="principal:increment-9-practitioner",
    )
    return ctx.app.run_command(
        ctx.session,  # type: ignore[arg-type]
        action=action,
        idempotency_key=key,
        operation=operation,  # type: ignore[arg-type]
        case_id=case_id,
        configuration_id=configuration_id,
        claimed_actor_id=ctx.actor_id if claimed_actor else None,
    )


def grant_path_scope(ctx: Increment9Gateway, case_id: RecordId, configuration_id: RecordId) -> None:
    grant(
        ctx,  # type: ignore[arg-type]
        Permission.CASE_READ,
        "read",
        ScopeType.CASE,
        case_id,
        principal_id="principal:increment-9-practitioner",
    )
    grant(
        ctx,  # type: ignore[arg-type]
        Permission.CONFIGURATION_READ,
        "read",
        ScopeType.CONFIGURATION,
        configuration_id,
        principal_id="principal:increment-9-practitioner",
    )


def test_i9_p1_case_to_authorized_operation_through_actual_gateway(
    increment9_gateway: Increment9Gateway,
) -> None:
    ctx = increment9_gateway
    fixture = run_gateway(
        ctx,
        action="decision.authorize",
        key="i9-p1-authorized-foundation",
        claimed_actor=True,
        operation=lambda service, _meta: _setup(
            ctx.app.domain_store,
            "i9-p1",
            service=service,
            assessor_id=ctx.actor_id,
        ),
    )
    case_id = fixture.foundation.context.case_id
    configuration_id = fixture.foundation.context.configuration_id
    configuration_version_id = fixture.foundation.context.configuration_version_id
    grant_path_scope(ctx, case_id, configuration_id)

    evidence_id, evidence_version_id = RecordId.new(), RecordVersionId.new()
    run_gateway(
        ctx,
        action="evidence.create",
        key="i9-p1-evidence",
        case_id=case_id,
        configuration_id=configuration_id,
        operation=lambda service, meta: service.commit_evidence(
            meta,
            EvidenceVersionInput(
                evidence_id,
                evidence_version_id,
                case_id,
                configuration_id,
                configuration_version_id,
                EvidenceClassification.OBSERVED,
                "practitioner-source:v1",
                {"source_version": "v1", "capture": "bounded"},
                {"control_effective": True},
                utc(2026, 8, 18),
                EFFECTIVE,
                EvidenceAttention.CURRENT,
            ),
        ),
    )
    applicability_version_id = RecordVersionId.new()
    run_gateway(
        ctx,
        action="evidence.applicability",
        key="i9-p1-applicability",
        case_id=case_id,
        configuration_id=configuration_id,
        operation=lambda service, meta: service.commit_evidence_applicability(
            meta,
            EvidenceApplicabilityVersionInput(
                RecordId.new(),
                applicability_version_id,
                evidence_id,
                evidence_version_id,
                ApplicabilityTargetType.MANAGED_CONFIGURATION_VERSION,
                str(configuration_id),
                configuration_version_id,
                "operating-plan",
                "bounded-scope",
                case_id,
                configuration_id,
                configuration_version_id,
                ApplicabilityOutcome.APPLICABLE,
                (),
                (),
                "exact Configuration Version applicability",
                ctx.actor_id,
                None,
                "governed:evidence-applicability-board",
                EFFECTIVE,
            ),
        ),
    )

    result_version_id, acceptance_version_id = run_gateway(
        ctx,
        action="completion.accept",
        key="i9-p1-completion",
        case_id=case_id,
        configuration_id=configuration_id,
        claimed_actor=True,
        operation=lambda _service, _meta: _complete(
            fixture,
            "i9-p1",
            acceptance_status=CompletionAcceptanceStatus.CURRENT,
        ),
    )
    activation = run_gateway(
        ctx,
        action="activation.authorize",
        key="i9-p1-activation",
        case_id=case_id,
        configuration_id=configuration_id,
        claimed_actor=True,
        operation=lambda service, meta: service.activate_target(meta, _activation(fixture)),
    )
    assert activation.activated
    assert (
        ctx.app._service.current_lifecycle_state(case_id=case_id, effective_at=EFFECTIVE.start)
        is CaseLifecycleState.OPERATING_OBSERVING
    )

    decision = ctx.app.domain_store.get_version(fixture.foundation.decision_version_id)
    assert decision is not None
    uncertainty_version_id = RecordVersionId.parse(
        str(decision.content["decision_limiting_uncertainty_version_ids"][0])
    )
    learning_version_id = RecordVersionId.new()
    run_gateway(
        ctx,
        action="learning.create",
        key="i9-p1-learning",
        case_id=case_id,
        configuration_id=configuration_id,
        operation=lambda service, meta: service.commit_learning_item(
            meta,
            LearningItemVersionInput(
                RecordId.new(),
                learning_version_id,
                case_id,
                fixture.foundation.decision_version_id,
                configuration_id,
                configuration_version_id,
                uncertainty_version_id,
                "Does the bounded control remain effective?",
                "reduce exact Decision-Limiting Uncertainty",
                "longitudinal control evidence",
                ctx.actor_id,
                None,
                "governed:learning-owner",
                "bounded monthly review",
                LearningStatus.ACTIVE,
                None,
                (),
                (),
                None,
                None,
                {"source": "authorized-decision-learning-plan"},
                EFFECTIVE,
            ),
        ),
    )

    integration = ctx.app.domain_store.get_version(fixture.foundation.integration_version_id)
    assert integration is not None
    assert (
        integration.content["value_input_version_id"]
        != integration.content["risk_input_version_id"]
    )
    assert ctx.app.domain_store.get_version(applicability_version_id) is not None
    assert ctx.app.domain_store.get_version(result_version_id) is not None
    assert ctx.app.domain_store.get_version(acceptance_version_id) is not None
    assert ctx.app.domain_store.get_version(learning_version_id) is not None
    assert ctx.app.domain_store.get_history(fixture.foundation.decision_id).versions
    assert ctx.app.domain_store.get_history(fixture.foundation.snapshot_id).versions
    assert all(
        row["actor_id"] in {None, str(ctx.actor_id)}
        for row in ctx.app.operational_store.audit_rows()
    )


def test_i9_p2_trigger_to_completed_reassessment_and_boundaries_through_gateway(
    increment9_gateway: Increment9Gateway,
) -> None:
    gateway = increment9_gateway
    ctx = run_gateway(
        gateway,
        action="decision.authorize",
        key="i9-p2-authorized-context",
        claimed_actor=True,
        operation=lambda service, _meta: context(
            gateway.app.domain_store,
            "i9-p2",
            service=service,
            assessor_id=gateway.actor_id,
        ),
    )
    case_id = ctx.foundation.context.case_id
    configuration_id = ctx.foundation.context.configuration_id
    grant_path_scope(gateway, case_id, configuration_id)
    grant(
        gateway,  # type: ignore[arg-type]
        Permission.COMMAND,
        "intake.external_trigger",
        principal_id="principal:increment-9-practitioner",
    )

    source = envelope(
        AdapterType.EXTERNAL_TRIGGER,
        case_id,
        configuration_id,
        replay="i9-p2-event-1",
        source_object="incident-17",
        source_version="v1",
        context_text="Does the exact current Decision require reassessment?",
    )
    proposed = gateway.app.intake(gateway.session, source)  # type: ignore[arg-type]
    replayed = gateway.app.intake(gateway.session, source)  # type: ignore[arg-type]
    assert proposed.status is IntakeStatus.PROPOSED
    assert replayed.replayed and replayed.intake_id == proposed.intake_id

    trigger = replace(
        trigger_input(
            ctx,
            "i9-p2-primary",
            scope=frozenset({"service:a", "service:b", "service:c"}),
        ),
        source_record_id=source.source_object_id,
        source_version_id=source.source_version,
        source_event_id=source.replay_id,
        source_system=source.source_system,
        provenance={"intake_id": proposed.intake_id, "payload_checksum": proposed.payload_checksum},
    )
    grant(
        gateway,
        Permission.COMMAND,
        "trigger.create",
        ScopeType.CASE,
        case_id,
        principal_id="principal:increment-9-practitioner",
    )  # type: ignore[arg-type]
    gateway.app.promote_intake(
        gateway.session,  # type: ignore[arg-type]
        intake_id=proposed.intake_id,
        action="trigger.create",
        idempotency_key="i9-p2-trigger-create",
        operation=lambda service, meta: service.commit_trigger(meta, trigger),
    )
    assert ctx.trigger_determiner_assignment is not None
    run_gateway(
        gateway,
        action="trigger.determine",
        key="i9-p2-trigger-determination",
        case_id=case_id,
        configuration_id=configuration_id,
        operation=lambda service, meta: service.commit_trigger_determination(
            meta,
            TriggerDeterminationVersionInput(
                RecordId.new(),
                RecordVersionId.new(),
                trigger.version_id,
                case_id,
                ctx.foundation.decision_version_id,
                ctx.foundation.context.configuration_version_id,
                TriggerDeterminationOutcome.REASSESSMENT_REQUIRED,
                "exact source occurrence requires reassessment",
                gateway.actor_id,
                ctx.trigger_determiner_assignment,
                None,
                (),
                EFFECTIVE,
            ),
        ),
    )
    reassessment = reassessment_input(
        ctx,
        "i9-p2",
        (trigger.version_id,),
        scope=frozenset({"service:a", "service:b", "service:c"}),
    )
    run_gateway(
        gateway,
        action="reassessment.create",
        key="i9-p2-reassessment",
        case_id=case_id,
        configuration_id=configuration_id,
        operation=lambda service, meta: service.commit_reassessment(meta, reassessment),
    )

    second_trigger = trigger_input(
        ctx,
        "i9-p2-overlap",
        scope=frozenset({"service:b"}),
    )
    run_gateway(
        gateway,
        action="trigger.create",
        key="i9-p2-overlap-trigger",
        case_id=case_id,
        configuration_id=configuration_id,
        operation=lambda service, meta: service.commit_trigger(meta, second_trigger),
    )
    run_gateway(
        gateway,
        action="trigger.determine",
        key="i9-p2-overlap-determination",
        case_id=case_id,
        configuration_id=configuration_id,
        operation=lambda service, meta: service.commit_trigger_determination(
            meta,
            TriggerDeterminationVersionInput(
                RecordId.new(),
                RecordVersionId.new(),
                second_trigger.version_id,
                case_id,
                ctx.foundation.decision_version_id,
                ctx.foundation.context.configuration_version_id,
                TriggerDeterminationOutcome.REASSESSMENT_REQUIRED,
                "overlapping exact source occurrence",
                gateway.actor_id,
                ctx.trigger_determiner_assignment,
                None,
                (),
                EFFECTIVE,
            ),
        ),
    )
    overlapping = reassessment_input(
        ctx,
        "i9-p2-overlap",
        (second_trigger.version_id,),
        scope=frozenset({"service:b"}),
    )
    run_gateway(
        gateway,
        action="reassessment.create",
        key="i9-p2-overlap-created",
        case_id=case_id,
        configuration_id=configuration_id,
        operation=lambda service, meta: service.commit_reassessment(meta, overlapping),
    )
    unresolved_overlap = ctx.service.reassessment_overlap(
        first_version_id=reassessment.version_id,
        second_version_id=overlapping.version_id,
        effective_at=NOW,
    )
    assert not unresolved_overlap.compatible
    assert unresolved_overlap.reason == "REASSESSMENT OVERLAP CONFLICT — UNRESOLVED"
    assert ctx.coordination_assignment is not None
    run_gateway(
        gateway,
        action="reassessment.coordinate",
        key="i9-p2-overlap-coordination",
        case_id=case_id,
        configuration_id=configuration_id,
        claimed_actor=True,
        operation=lambda service, meta: service.commit_reassessment_determination(
            meta,
            ReassessmentDeterminationVersionInput(
                RecordId.new(),
                RecordVersionId.new(),
                ReassessmentDeterminationKind.COEXISTENCE,
                ReassessmentDeterminationOutcome.COEXISTENCE_AUTHORIZED,
                case_id,
                ctx.foundation.decision_version_id,
                ctx.foundation.context.configuration_version_id,
                frozenset({"service:b"}),
                (),
                (reassessment.version_id, overlapping.version_id),
                gateway.actor_id,
                ctx.coordination_assignment,
                None,
                (),
                "accountable coexistence after explicit overlap review",
                EFFECTIVE,
            ),
        ),
    )
    assert ctx.service.reassessment_overlap(
        first_version_id=reassessment.version_id,
        second_version_id=overlapping.version_id,
        effective_at=NOW,
    ).compatible

    run_gateway(
        gateway,
        action="interim-disposition.create",
        key="i9-p2-disposition-a",
        case_id=case_id,
        configuration_id=configuration_id,
        operation=lambda _service, _meta: disposition(
            ctx,
            "i9-p2-a",
            reassessment,
            operating_state="state-z",
            allowed=frozenset({"read", "review"}),
            required=frozenset({"control:a"}),
            scope=frozenset({"service:a", "service:b"}),
        ),
    )
    run_gateway(
        gateway,
        action="interim-disposition.create",
        key="i9-p2-disposition-b",
        case_id=case_id,
        configuration_id=configuration_id,
        operation=lambda _service, _meta: disposition(
            ctx,
            "i9-p2-b",
            reassessment,
            operating_state="state-a",
            allowed=frozenset({"review"}),
            required=frozenset({"control:b"}),
            scope=frozenset({"service:b", "service:c"}),
        ),
    )
    effective = ctx.service.effective_operating_disposition(
        case_id=case_id,
        decision_version_id=ctx.foundation.decision_version_id,
        configuration_version_id=ctx.foundation.context.configuration_version_id,
        effective_at=NOW,
    )
    partitions = {item.affected_scope: item for item in effective.partitions}
    assert not partitions[frozenset({"service:a"})].suspended
    assert partitions[frozenset({"service:b"})].suspended
    assert partitions[frozenset({"service:b"})].operating_state_values == frozenset(
        {"state-a", "state-z"}
    )
    assert not partitions[frozenset({"service:c"})].suspended

    ready = run_gateway(
        gateway,
        action="reassessment.advance",
        key="i9-p2-ready",
        case_id=case_id,
        configuration_id=configuration_id,
        operation=lambda _service, _meta: ready_for_completion(ctx, "i9-p2", reassessment),
    )
    run_gateway(
        gateway,
        action="reassessment.coordinate",
        key="i9-p2-overlap-revalidated",
        case_id=case_id,
        configuration_id=configuration_id,
        claimed_actor=True,
        operation=lambda service, meta: service.commit_reassessment_determination(
            meta,
            ReassessmentDeterminationVersionInput(
                RecordId.new(),
                RecordVersionId.new(),
                ReassessmentDeterminationKind.COEXISTENCE,
                ReassessmentDeterminationOutcome.COEXISTENCE_AUTHORIZED,
                case_id,
                ctx.foundation.decision_version_id,
                ctx.foundation.context.configuration_version_id,
                frozenset({"service:b"}),
                (),
                (ready.version_id, overlapping.version_id),
                gateway.actor_id,
                ctx.coordination_assignment,
                None,
                (),
                "prospective exact-version coexistence revalidation",
                EFFECTIVE,
            ),
        ),
    )
    completed = run_gateway(
        gateway,
        action="reassessment.confirm",
        key="i9-p2-confirm",
        case_id=case_id,
        configuration_id=configuration_id,
        claimed_actor=True,
        operation=lambda service, meta: service.complete_confirmed(meta, confirmation(ctx, ready)),
    )
    assert completed.status is ReassessmentStatus.COMPLETED_CONFIRMED
    coverage = ctx.service.trigger_coverage(
        trigger_version_id=trigger.version_id,
        effective_at=NOW,
    )
    assert coverage.state is TriggerCoverageState.SATISFIED_BY_COMPLETED_REASSESSMENT
    assert len(gateway.app.domain_store.get_history(reassessment.reassessment_id).versions) == 3
    assert (
        "observation"
        not in " ".join(inspect(gateway.app.domain_store.engine).get_table_names()).lower()
    )

    similar = gateway.app.intake(
        gateway.session,  # type: ignore[arg-type]
        replace(source, replay_id="i9-p2-event-2", source_object_id="incident-18"),
    )
    assert similar.intake_id != proposed.intake_id
    assert gateway.app.domain_store.count_rows("trigger_versions") == 2


def test_i9_p3_multicase_register_to_owning_domain_action_through_gateway(
    increment9_gateway: Increment9Gateway,
) -> None:
    ctx = increment9_gateway
    visible_case, visible_configuration = case_and_configuration(
        ctx,  # type: ignore[arg-type]
        "i9-p3-visible",
        principal_id="principal:increment-9-practitioner",
    )
    hidden_case, hidden_configuration = case_and_configuration(
        ctx,  # type: ignore[arg-type]
        "i9-p3-hidden",
        principal_id="principal:increment-9-practitioner",
    )
    gap_values: list[tuple[RecordId, RecordVersionId]] = []
    for key, case_id, configuration_id in (
        ("visible", visible_case, visible_configuration),
        ("hidden", hidden_case, hidden_configuration),
    ):
        configuration_versions = ctx.app.domain_store.get_history(configuration_id).versions
        assert len(configuration_versions) == 1
        configuration_version_id = next(iter(configuration_versions)).version_id
        gap_id, gap_version_id = RecordId.new(), RecordVersionId.new()

        def commit_gap(
            service: Increment7ApplicationService,
            meta: object,
            *,
            gap_key: str = key,
            gap_record_id: RecordId = gap_id,
            gap_record_version_id: RecordVersionId = gap_version_id,
            gap_case_id: RecordId = case_id,
            gap_configuration_id: RecordId = configuration_id,
            gap_configuration_version_id: RecordVersionId = configuration_version_id,
        ) -> object:
            return service.commit_authority_gap(
                meta,  # type: ignore[arg-type]
                AuthorityGapVersionInput(
                    gap_record_id,
                    gap_record_version_id,
                    gap_case_id,
                    gap_configuration_id,
                    gap_configuration_version_id,
                    f"Q-{gap_key}",
                    "Who may authorize this exact bounded operation?",
                    "bounded-scope",
                    "authority remains explicitly unresolved",
                    {"source": f"authority-register:{gap_key}"},
                    EFFECTIVE,
                    outcome=AuthorityGapOutcome.UNRESOLVED,
                ),
            )

        run_gateway(
            ctx,
            action="authority-gap.create",
            key=f"i9-p3-gap-{key}",
            case_id=case_id,
            configuration_id=configuration_id,
            operation=commit_gap,
        )
        gap_values.append((gap_id, gap_version_id))

    def establish_dependency(
        service: Increment7ApplicationService, _meta: object
    ) -> RecordVersionId:
        candidate_id, candidate_version, _ = candidate_set(
            ctx.app.domain_store,
            service,
            "i9-p3",
            members=tuple(
                DependencyCandidateMember("authority-gap", record_id, version_id, "provider")
                for record_id, version_id in gap_values
            ),
        )
        dependency_id, dependency_version = shared_dependency(service, "i9-p3")
        assignment = determiner_assignment(
            service,
            "i9-p3",
            ctx.actor_id,
            candidate_version,
        )
        equivalence(
            service,
            "i9-p3",
            candidate_version,
            ctx.actor_id,
            assignment,
            dependency_version,
        )
        assert candidate_id and dependency_id
        return dependency_version

    dependency_version = run_gateway(
        ctx,
        action="shared-dependency.determine",
        key="i9-p3-dependency",
        claimed_actor=True,
        operation=establish_dependency,
    )
    grant(
        ctx,  # type: ignore[arg-type]
        Permission.EXPORT,
        "register.output",
        principal_id="principal:increment-9-practitioner",
    )
    grant(
        ctx,  # type: ignore[arg-type]
        Permission.EXPORT,
        "register.export",
        principal_id="principal:increment-9-practitioner",
    )
    grant(
        ctx,  # type: ignore[arg-type]
        Permission.DELIVERY,
        "notification.deliver",
        principal_id="principal:increment-9-practitioner",
    )
    grant(
        ctx,  # type: ignore[arg-type]
        Permission.COMMAND,
        "register.assign_owner",
        principal_id="principal:increment-9-practitioner",
    )

    complete_view = ctx.app.derive_register(
        ctx.session,  # type: ignore[arg-type]
        requested_case_ids=frozenset({visible_case, hidden_case}),
        requested_configuration_ids=frozenset({visible_configuration, hidden_configuration}),
        effective_at=NOW,
        known_at=NOW,
        rule_id="management-register-population",
        rule_version="v0.1",
    )
    assert complete_view.consistency is ProjectionConsistency.CURRENT
    assert {entry.key.case_id for entry in complete_view.entries} == {
        visible_case,
        hidden_case,
    }
    assert len(complete_view.groups) == 1
    assert complete_view.groups[0].dependency_version_ids == frozenset({dependency_version})
    assert not complete_view.groups[0].access_filtered

    grant(
        ctx,  # type: ignore[arg-type]
        Permission.CASE_READ,
        "read",
        ScopeType.CASE,
        hidden_case,
        principal_id="principal:increment-9-practitioner",
        effect=AccessEffect.DENY,
    )
    view = ctx.app.derive_register(
        ctx.session,  # type: ignore[arg-type]
        requested_case_ids=frozenset({visible_case, hidden_case}),
        requested_configuration_ids=frozenset({visible_configuration, hidden_configuration}),
        effective_at=NOW,
        known_at=NOW,
        rule_id="management-register-population",
        rule_version="v0.1",
    )
    assert view.consistency is ProjectionConsistency.CURRENT
    assert {entry.key.case_id for entry in view.entries} == {visible_case}
    assert len(view.groups) == 1
    assert view.groups[0].dependency_version_ids == frozenset({dependency_version})
    assert view.groups[0].access_filtered
    assert view.groups[0].global_constituent_count is None
    represented = json.dumps(ctx.app._service._view_content(view), sort_keys=True)
    assert str(hidden_case) not in represented
    assert str(hidden_configuration) not in represented

    manifest = ctx.app.persist_register_output(ctx.session, view, output_kind="EXPORT")  # type: ignore[arg-type]
    json_path = ctx.app.export_manifest(ctx.session, manifest.manifest_id, output_format="json")  # type: ignore[arg-type]
    csv_path = ctx.app.export_manifest(ctx.session, manifest.manifest_id, output_format="csv")  # type: ignore[arg-type]
    first_entry = view.entries[0]
    launch = ctx.app.launch_register_action(
        ctx.session,
        view,
        RegisterAction.ASSIGN_OWNER,
        first_entry,  # type: ignore[arg-type]
    )
    assert launch.owning_family == first_entry.key.source_family
    assert launch.source_version_ids == first_entry.selected_source_version_ids
    assert launch.authoritative

    intents = run_gateway(
        ctx,
        action="register.notification.generate",
        key="i9-p3-notification",
        operation=lambda service, _meta: service.generate_notification_intents(
            manifest,
            view,
            channel="local-spool",
            recipient_scope="case-owner",
        ),
    )
    delivery = ctx.app.deliver_notification(
        ctx.session,  # type: ignore[arg-type]
        intent_id=intents[0].intent_id,
        attempt_id="i9-p3-delivery",
    )
    assert delivery.status.value == "DELIVERED"
    assert (
        json.loads(json_path.read_text(encoding="utf-8"))["manifest_checksum"] == manifest.checksum
    )
    assert "manifest_checksum" in csv_path.read_text(encoding="utf-8")
    with pytest.raises(UnsupportedCapability):
        ctx.app.require_supported("GENERIC_REGISTER_RESOLUTION")


def test_i9_security_recovery_degraded_and_excluded_boundaries(
    increment9_gateway: Increment9Gateway,
) -> None:
    ctx = increment9_gateway
    case_id, _configuration_id = case_and_configuration(
        ctx,  # type: ignore[arg-type]
        "i9-ops",
        principal_id="principal:increment-9-practitioner",
    )
    with pytest.raises(AuthenticationFailed):
        ctx.app.authenticate("principal:increment-9-practitioner", "wrong-token-value-000000")

    for capability in (
        "OBSERVATION_RECORD",
        "OBSERVATION_AUTOMATION",
        "TELEMETRY_TO_EVIDENCE",
        "TELEMETRY_TO_TRIGGER",
        "TELEMETRY_TO_REGISTER",
        "OPERATING_STATE_RANKING",
        "OPERATING_STATE_STRENGTH_INFERENCE",
    ):
        with pytest.raises(UnsupportedCapability):
            ctx.app.require_supported(capability)

    backup, manifest_path, manifest = ctx.app.backup(ctx.session, label="i9-release")  # type: ignore[arg-type]
    restored_path = ctx.config.backup_directory / "i9-restored.sqlite3"
    restored = ctx.app.restore(
        ctx.session,  # type: ignore[arg-type]
        backup_path=backup,
        manifest_path=manifest_path,
        target_path=restored_path,
    )
    assert restored.backup_checksum == manifest.backup_checksum
    restored_config = replace(ctx.config, database_path=restored_path)
    with OperationalApplication(restored_config, FixedClock(NOW)) as restored_app:
        resumed = restored_app.authenticate("principal:increment-9-practitioner", TOKEN)
        assert resumed.actor_id == ctx.actor_id
        assert restored_app.domain_store.get_history(case_id).versions
        assert restored_app.health().state is ReadinessState.READY

    tampered = ctx.config.backup_directory / "i9-tampered.sqlite3"
    tampered.write_bytes(backup.read_bytes() + b"tamper")
    with pytest.raises(RecoveryRejected):
        ctx.app.restore(
            ctx.session,  # type: ignore[arg-type]
            backup_path=tampered,
            manifest_path=manifest_path,
            target_path=ctx.config.backup_directory / "i9-tampered-restore.sqlite3",
        )
    incompatible_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    incompatible_data["schema_revision"] = "0007_increment_7"
    incompatible = ctx.config.backup_directory / "i9-incompatible.manifest.json"
    incompatible.write_text(json.dumps(incompatible_data), encoding="utf-8")
    with pytest.raises(RecoveryRejected):
        ctx.app.restore(
            ctx.session,  # type: ignore[arg-type]
            backup_path=backup,
            manifest_path=incompatible,
            target_path=ctx.config.backup_directory / "i9-incompatible.sqlite3",
        )

    ctx.config.spool_directory.rmdir()
    degraded = ctx.app.health()
    assert degraded.process_alive and degraded.state is ReadinessState.DEGRADED
    assert "DELIVERY_SPOOL_UNAVAILABLE" in degraded.reasons
    ctx.config.spool_directory.mkdir()
    assert ctx.app.domain_store.get_history(case_id).versions
    assert not any(
        "observation" in table.lower()
        for table in inspect(ctx.app.domain_store.engine).get_table_names()
    )
    forbidden = ("token", "password", "secret", "credential")
    for row in ctx.app.operational_store.audit_rows():
        details = str(row["details_json"]).lower()
        assert not any(name in details for name in forbidden)
