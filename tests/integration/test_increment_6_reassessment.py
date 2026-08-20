from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime

import pytest

from paim.application import DomainPreconditionFailed, DomainRuleViolation
from paim.application.increment6 import Increment6ApplicationService
from paim.domain import (
    AccountabilityFunction,
    AuthorizedDecisionFound,
    BoundaryClauseEffect,
    BoundaryClauseInput,
    BoundarySnapshotVersionInput,
    BoundaryVerificationMode,
    DecisionConfirmationVersionInput,
    DecisionStatus,
    DecisionVersionInput,
    DelegationEffect,
    InterimOperatingDispositionVersionInput,
    MembershipVersionInput,
    ReassessmentDeterminationConflict,
    ReassessmentDeterminationFound,
    ReassessmentDeterminationKind,
    ReassessmentDeterminationNotEstablished,
    ReassessmentDeterminationOutcome,
    ReassessmentDeterminationVersionInput,
    ReassessmentMechanismVersionInput,
    ReassessmentStatus,
    ReassessmentTerminationRequest,
    ReassessmentVersionInput,
    RoleAssignmentVersionInput,
    RoleTargetType,
    SuccessorDecisionCompletionRequest,
    TriggerCoverageState,
    TriggerDeterminationConflict,
    TriggerDeterminationFound,
    TriggerDeterminationOutcome,
    TriggerDeterminationVersionInput,
    TriggerSourceKind,
    TriggerVersionInput,
)
from paim.integrity import EffectiveInterval, FixedClock, RecordId, RecordVersionId
from paim.persistence.sqlite import SQLiteIntegrityStore
from paim.persistence.sqlite.schema import metadata
from tests.helpers import utc
from tests.integration.test_increment_2_foundation import add_role
from tests.integration.test_increment_3_foundation import meta
from tests.integration.test_increment_4_foundation import Foundation, authorization, foundation

NOW = utc(2026, 2, 1)
EFFECTIVE = EffectiveInterval(utc(2026, 1, 1))


@dataclass(frozen=True)
class Increment6Context:
    store: SQLiteIntegrityStore
    service: Increment6ApplicationService
    foundation: Foundation
    authorization_basis_version_id: RecordVersionId
    trigger_determiner_assignment: RecordVersionId | None
    reassessment_owner_assignment: RecordVersionId | None
    coordination_assignment: RecordVersionId | None


def context(
    store: SQLiteIntegrityStore,
    key: str,
    *,
    roles: bool = True,
    service: Increment6ApplicationService | None = None,
    assessor_id: RecordId | None = None,
) -> Increment6Context:
    service = service or Increment6ApplicationService(store, FixedClock(NOW))
    fx = foundation(store, key, service=service, assessor_id=assessor_id)
    basis = authorization(fx, key)
    fx.context.service.authorize_decision(meta(f"{key}-authorize"), basis)
    trigger_determiner: RecordVersionId | None = None
    owner: RecordVersionId | None = None
    coordination: RecordVersionId | None = None
    if roles:
        assignments: list[RecordVersionId] = []
        for role in (
            AccountabilityFunction.TRIGGER_DETERMINER,
            AccountabilityFunction.REASSESSMENT_OWNER,
            AccountabilityFunction.REASSESSMENT_COORDINATION_AUTHORITY,
        ):
            _, version_id = add_role(
                store,
                f"{key}-{role.value}",
                fx.context.assessor_id,
                role=role.value,
                target_type=RoleTargetType.CASE,
                target_id=str(fx.context.case_id),
                case_context_id=fx.context.case_id,
                accountable=True,
                application_service=service,
            )
            assignments.append(version_id)
        trigger_determiner, owner, coordination = assignments
    return Increment6Context(
        store,
        service,
        fx,
        basis.version_id,
        trigger_determiner,
        owner,
        coordination,
    )


def trigger_input(
    ctx: Increment6Context,
    key: str,
    *,
    trigger_id: RecordId | None = None,
    version_id: RecordVersionId | None = None,
    question: str = "Does the current Decision require reassessment?",
    scope: frozenset[str] = frozenset({"service:payments"}),
    source_event: str | None = None,
    source_version: str | None = None,
    expected_version_id: RecordVersionId | None = None,
    withdrawn: bool = False,
    effective: EffectiveInterval = EFFECTIVE,
) -> TriggerVersionInput:
    return TriggerVersionInput(
        trigger_id or RecordId.new(),
        version_id or RecordVersionId.new(),
        ctx.foundation.context.case_id,
        ctx.foundation.decision_version_id,
        ctx.foundation.context.configuration_version_id,
        "EXTERNAL_CHANGE",
        question,
        scope,
        TriggerSourceKind.HUMAN_EXTERNAL,
        "external-event",
        f"source-{key}",
        source_version or f"source-version-{key}",
        source_event or f"event-{key}",
        NOW,
        f"Trigger {key}",
        "Exact source occurrence requires accountable triage",
        (f"external:{key}",),
        {"provider": "test-provider", "occurrence": key},
        effective,
        source_system="test-provider",
        source_actor="provider-monitor",
        withdrawn=withdrawn,
        expected_version_id=expected_version_id,
        relationship_reason=("material source correction" if expected_version_id else None),
    )


def commit_trigger(
    ctx: Increment6Context,
    key: str,
    *,
    outcome: TriggerDeterminationOutcome = TriggerDeterminationOutcome.REASSESSMENT_REQUIRED,
    determine: bool = True,
    **changes: object,
) -> TriggerVersionInput:
    value = trigger_input(ctx, key, **changes)  # type: ignore[arg-type]
    ctx.service.commit_trigger(meta(f"{key}-trigger"), value)
    if determine:
        assert ctx.trigger_determiner_assignment is not None
        ctx.service.commit_trigger_determination(
            meta(f"{key}-trigger-determination"),
            TriggerDeterminationVersionInput(
                RecordId.new(),
                RecordVersionId.new(),
                value.version_id,
                value.case_id,
                value.decision_version_id,
                value.configuration_version_id,
                outcome,
                "Accountable exact Trigger Determination",
                ctx.foundation.context.assessor_id,
                ctx.trigger_determiner_assignment,
                None,
                (),
                value.effective,
            ),
        )
    return value


def grouping(
    ctx: Increment6Context,
    key: str,
    triggers: tuple[RecordVersionId, ...],
    *,
    outcome: ReassessmentDeterminationOutcome = ReassessmentDeterminationOutcome.COMPATIBLE,
) -> ReassessmentDeterminationVersionInput:
    assert ctx.coordination_assignment is not None
    value = ReassessmentDeterminationVersionInput(
        RecordId.new(),
        RecordVersionId.new(),
        ReassessmentDeterminationKind.GROUPING,
        outcome,
        ctx.foundation.context.case_id,
        ctx.foundation.decision_version_id,
        ctx.foundation.context.configuration_version_id,
        frozenset({"service:payments"}),
        triggers,
        (),
        ctx.foundation.context.assessor_id,
        ctx.coordination_assignment,
        None,
        (),
        "Accountable exact compatibility determination",
        EFFECTIVE,
    )
    ctx.service.commit_reassessment_determination(meta(f"{key}-grouping"), value)
    return value


def reassessment_input(
    ctx: Increment6Context,
    key: str,
    triggers: tuple[RecordVersionId, ...],
    *,
    reassessment_id: RecordId | None = None,
    version_id: RecordVersionId | None = None,
    scope: frozenset[str] = frozenset({"service:payments"}),
    expected_version_id: RecordVersionId | None = None,
    status: ReassessmentStatus = ReassessmentStatus.OPEN,
) -> ReassessmentVersionInput:
    assert ctx.reassessment_owner_assignment is not None
    return ReassessmentVersionInput(
        reassessment_id or RecordId.new(),
        version_id or RecordVersionId.new(),
        ctx.foundation.context.case_id,
        ctx.foundation.decision_version_id,
        ctx.foundation.context.configuration_version_id,
        "Review the current management Decision",
        scope,
        ctx.foundation.context.assessor_id,
        ctx.reassessment_owner_assignment,
        None,
        tuple(
            MembershipVersionInput(
                RecordId.new(), RecordVersionId.new(), trigger, next(iter(scope), "indeterminate")
            )
            for trigger in triggers
        ),
        status,
        "Exact Trigger Set requires reassessment",
        (ctx.foundation.integration_version_id, ctx.foundation.decision_version_id),
        EFFECTIVE,
        expected_version_id=expected_version_id,
        relationship_reason=("atomic Trigger Set successor" if expected_version_id else None),
    )


def commit_reassessment(
    ctx: Increment6Context,
    key: str,
    triggers: tuple[RecordVersionId, ...],
    **changes: object,
) -> ReassessmentVersionInput:
    value = reassessment_input(ctx, key, triggers, **changes)  # type: ignore[arg-type]
    ctx.service.commit_reassessment(meta(f"{key}-reassessment"), value)
    return value


def ready_for_completion(
    ctx: Increment6Context,
    key: str,
    value: ReassessmentVersionInput,
) -> ReassessmentVersionInput:
    triggers = tuple(item.trigger_version_id for item in value.memberships)
    analysis = commit_reassessment(
        ctx,
        f"{key}-analysis",
        triggers,
        reassessment_id=value.reassessment_id,
        scope=value.affected_scope,
        expected_version_id=value.version_id,
        status=ReassessmentStatus.ANALYSIS_IN_PROGRESS,
    )
    return commit_reassessment(
        ctx,
        f"{key}-authority",
        triggers,
        reassessment_id=value.reassessment_id,
        scope=value.affected_scope,
        expected_version_id=analysis.version_id,
        status=ReassessmentStatus.AWAITING_DECISION_AUTHORITY,
    )


def confirmation(
    ctx: Increment6Context,
    reassessment: ReassessmentVersionInput,
) -> DecisionConfirmationVersionInput:
    integration = ctx.store.get_version(ctx.foundation.integration_version_id)
    assert integration is not None
    value_version_id = RecordVersionId.parse(str(integration.content["value_input_version_id"]))
    risk_version_id = RecordVersionId.parse(str(integration.content["risk_input_version_id"]))
    return DecisionConfirmationVersionInput(
        RecordId.new(),
        RecordVersionId.new(),
        reassessment.version_id,
        ctx.foundation.decision_version_id,
        ctx.foundation.context.configuration_version_id,
        ctx.foundation.snapshot_version_id,
        ctx.authorization_basis_version_id,
        ctx.foundation.context.assessor_id,
        tuple(item.trigger_version_id for item in reassessment.memberships),
        (
            ctx.foundation.integration_version_id,
            ctx.foundation.decision_version_id,
            ctx.foundation.context.configuration_version_id,
            ctx.foundation.snapshot_version_id,
            ctx.foundation.authority_version_id,
            ctx.foundation.clause_version_id,
            value_version_id,
            risk_version_id,
        ),
        "The exact authorized Decision and Boundary remain valid",
        NOW,
        NOW,
        {
            "evidence": (str(ctx.foundation.integration_version_id),),
            "authority": (str(ctx.foundation.authority_version_id),),
            "configuration": (str(ctx.foundation.context.configuration_version_id),),
            "value": (str(value_version_id),),
            "risk": (str(risk_version_id),),
            "control": (str(ctx.foundation.clause_version_id),),
            "uncertainty": (str(ctx.foundation.integration_version_id),),
            "boundary": (str(ctx.foundation.snapshot_version_id),),
        },
        ("scheduled-review",),
    )


def coordination_determination(
    ctx: Increment6Context,
    key: str,
    *,
    kind: ReassessmentDeterminationKind,
    outcome: ReassessmentDeterminationOutcome,
    triggers: tuple[RecordVersionId, ...] = (),
    reassessments: tuple[RecordVersionId, ...] = (),
    target: RecordVersionId | None = None,
    canonical: RecordVersionId | None = None,
) -> ReassessmentDeterminationVersionInput:
    assert ctx.coordination_assignment is not None
    value = ReassessmentDeterminationVersionInput(
        RecordId.new(),
        RecordVersionId.new(),
        kind,
        outcome,
        ctx.foundation.context.case_id,
        ctx.foundation.decision_version_id,
        ctx.foundation.context.configuration_version_id,
        frozenset({"service:payments"}),
        triggers,
        reassessments,
        ctx.foundation.context.assessor_id,
        ctx.coordination_assignment,
        None,
        (),
        f"Accountable {kind.value} determination",
        EFFECTIVE,
        target_reassessment_version_id=target,
        canonical_trigger_version_id=canonical,
    )
    ctx.service.commit_reassessment_determination(meta(f"{key}-{kind.value}"), value)
    return value


def disposition(
    ctx: Increment6Context,
    key: str,
    reassessment: ReassessmentVersionInput,
    *,
    operating_state: str | None = "bounded continuation",
    allowed: frozenset[str] = frozenset({"read", "review"}),
    required: frozenset[str] = frozenset({"manual review"}),
    prohibited: frozenset[str] = frozenset({"deploy"}),
    suspend: bool = False,
    expiry_at: datetime | None = None,
    scope: frozenset[str] | None = None,
) -> InterimOperatingDispositionVersionInput:
    value = InterimOperatingDispositionVersionInput(
        RecordId.new(),
        RecordVersionId.new(),
        reassessment.version_id,
        ctx.foundation.context.case_id,
        ctx.foundation.decision_version_id,
        ctx.foundation.context.configuration_version_id,
        ctx.foundation.snapshot_version_id,
        reassessment.affected_scope if scope is None else scope,
        operating_state,
        allowed,
        required,
        prohibited,
        frozenset({"remain inside exact Boundary"}),
        suspend,
        "Restrictive interim operation while reassessment remains active",
        ctx.authorization_basis_version_id,
        ctx.foundation.context.assessor_id,
        expiry_at,
        NOW,
        EFFECTIVE,
    )
    ctx.service.commit_interim_disposition(meta(f"{key}-disposition"), value)
    return value


def successor_request(
    ctx: Increment6Context,
    reassessment: ReassessmentVersionInput,
    *,
    effective_at: datetime = NOW,
) -> SuccessorDecisionCompletionRequest:
    effective = EffectiveInterval(effective_at)
    clause = BoundaryClauseInput(
        RecordId.new(),
        RecordVersionId.new(),
        "capacity",
        BoundaryClauseEffect.LIMITED,
        "requests-per-minute",
        "metric:rpm",
        "LTE",
        "80",
        "rpm",
        "successor capacity remains bounded",
        "Reassessment narrows the exact Boundary",
        (f"integration:{ctx.foundation.integration_version_id}",),
        BoundaryVerificationMode.MECHANICAL,
        "suspend affected activity",
        predecessor_clause_version_id=ctx.foundation.clause_version_id,
        relationship_reason="Reassessment successor clause",
    )
    boundary = BoundarySnapshotVersionInput(
        ctx.foundation.snapshot_id,
        RecordVersionId.new(),
        ctx.foundation.context.case_id,
        ctx.foundation.context.configuration_id,
        ctx.foundation.context.configuration_version_id,
        ctx.foundation.integration_id,
        ctx.foundation.integration_version_id,
        ctx.foundation.context.assessor_id,
        "finalized",
        (clause,),
        "Reassessment successor Boundary",
        (),
        effective,
        expected_version_id=ctx.foundation.snapshot_version_id,
        relationship_reason="Reassessment successor Boundary",
    )
    decision = DecisionVersionInput(
        ctx.foundation.decision_id,
        RecordVersionId.new(),
        ctx.foundation.context.case_id,
        ctx.foundation.context.configuration_id,
        ctx.foundation.context.configuration_version_id,
        ctx.foundation.integration_id,
        ctx.foundation.integration_version_id,
        boundary.snapshot_id,
        boundary.version_id,
        "continue within a narrowed exact Boundary",
        "bounded continuation",
        "Reassessment supports an authorized successor Decision",
        ("do not exceed 80 rpm",),
        (),
        (),
        ("suspend",),
        ("policy:bounded-operation",),
        (ctx.foundation.authority_version_id,),
        (),
        (),
        (),
        ("reassess on control failure",),
        DecisionStatus.PROPOSED,
        effective,
        expected_version_id=ctx.foundation.decision_version_id,
        relationship_reason="Reassessment successor Decision",
    )
    basis = authorization(ctx.foundation, f"successor-{decision.version_id}")
    basis = replace(
        basis,
        basis_id=RecordId.new(),
        version_id=RecordVersionId.new(),
        decision_version_id=decision.version_id,
        authorization_event_id=f"authorization-{decision.version_id}",
        authorization_effective_at=effective.start,
        effective=effective,
    )
    return SuccessorDecisionCompletionRequest(
        reassessment.version_id,
        ctx.foundation.decision_version_id,
        boundary,
        decision,
        basis,
        effective.start,
        NOW,
    )


def test_01_one_trigger_one_reassessment_has_exact_active_coverage(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    ctx = context(sqlite_store, "oracle-01")
    trigger = commit_trigger(ctx, "oracle-01")
    reassessment = commit_reassessment(ctx, "oracle-01", (trigger.version_id,))
    coverage = ctx.service.trigger_coverage(trigger_version_id=trigger.version_id, effective_at=NOW)
    assert coverage.state is TriggerCoverageState.LINKED_ACTIVE
    assert coverage.supporting_version_ids == frozenset({reassessment.version_id})


def test_proposed_reassessment_preserves_owner_vacancy_until_accountability_exists(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    ctx = context(sqlite_store, "owner-vacancy")
    proposed = replace(
        reassessment_input(ctx, "owner-vacancy", (), status=ReassessmentStatus.PROPOSED),
        owner_assignment_version_id=None,
        memberships=(),
    )
    ctx.service.commit_reassessment(meta("owner-vacancy-proposed"), proposed)
    trigger = commit_trigger(ctx, "owner-vacancy")
    opened = reassessment_input(
        ctx,
        "owner-vacancy-open",
        (trigger.version_id,),
        reassessment_id=proposed.reassessment_id,
        expected_version_id=proposed.version_id,
        status=ReassessmentStatus.OPEN,
    )
    ctx.service.commit_reassessment(meta("owner-vacancy-open"), opened)


def test_02_two_compatible_triggers_require_accountable_prestart_grouping(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    ctx = context(sqlite_store, "oracle-02")
    first = commit_trigger(ctx, "oracle-02-a")
    second = commit_trigger(ctx, "oracle-02-b", scope=frozenset({"service:payments"}))
    proposed = reassessment_input(ctx, "oracle-02", (first.version_id, second.version_id))
    with pytest.raises(DomainRuleViolation, match="GROUPING NOT ESTABLISHED"):
        ctx.service.commit_reassessment(meta("oracle-02-reject"), proposed)
    grouping(ctx, "oracle-02", (first.version_id, second.version_id))
    ctx.service.commit_reassessment(meta("oracle-02-accept"), proposed)


def test_grouping_selection_reports_explicit_conflict_without_a_winner(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    ctx = context(sqlite_store, "grouping-conflict")
    first = commit_trigger(ctx, "grouping-conflict-a")
    second = commit_trigger(ctx, "grouping-conflict-b")
    triggers = (first.version_id, second.version_id)
    grouping(ctx, "grouping-conflict-compatible", triggers)
    grouping(
        ctx,
        "grouping-conflict-incompatible",
        triggers,
        outcome=ReassessmentDeterminationOutcome.INCOMPATIBLE,
    )
    selected = ctx.service.current_coordination_determination(
        kind=ReassessmentDeterminationKind.GROUPING,
        trigger_version_ids=triggers,
        effective_at=NOW,
    )
    assert isinstance(selected, ReassessmentDeterminationConflict)
    assert selected.reason == "TRIGGER GROUPING CONFLICT — UNRESOLVED"


def test_03_later_trigger_creates_successor_immutable_trigger_set(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    ctx = context(sqlite_store, "oracle-03")
    first = commit_trigger(ctx, "oracle-03-a")
    initial = commit_reassessment(ctx, "oracle-03-a", (first.version_id,))
    second = commit_trigger(ctx, "oracle-03-b")
    grouping(ctx, "oracle-03", (first.version_id, second.version_id))
    successor = commit_reassessment(
        ctx,
        "oracle-03-b",
        (first.version_id, second.version_id),
        reassessment_id=initial.reassessment_id,
        expected_version_id=initial.version_id,
    )
    with sqlite_store.read_transaction() as transaction:
        assert tuple(item[0] for item in transaction.trigger_set(initial.version_id)) == (
            first.version_id,
        )
        assert tuple(item[0] for item in transaction.trigger_set(successor.version_id)) == (
            first.version_id,
            second.version_id,
        )


def test_04_exact_replay_returns_original_and_payload_mismatch_rejects(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    ctx = context(sqlite_store, "oracle-04")
    value = trigger_input(ctx, "oracle-04")
    command = meta("oracle-04-trigger")
    original = ctx.service.commit_trigger(command, value)
    assert ctx.service.commit_trigger(command, value) == original
    with pytest.raises(DomainPreconditionFailed, match="IDEMPOTENCY KEY REUSE CONFLICT"):
        ctx.service.commit_trigger(command, replace(value, description="payload mismatch"))
    assert sqlite_store.count_rows("trigger_records") == 1


def test_05_material_source_update_creates_successor_trigger_version(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    ctx = context(sqlite_store, "oracle-05")
    first = commit_trigger(ctx, "oracle-05", determine=False)
    second = trigger_input(
        ctx,
        "oracle-05",
        trigger_id=first.trigger_id,
        source_event=first.source_event_id,
        source_version="source-version-2",
        expected_version_id=first.version_id,
    )
    ctx.service.commit_trigger(meta("oracle-05-successor"), second)
    assert {item.version_id for item in sqlite_store.get_history(first.trigger_id).versions} == {
        first.version_id,
        second.version_id,
    }


def test_06_shared_external_event_remains_separate_across_cases(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    first_ctx = context(sqlite_store, "oracle-06-a")
    second_ctx = context(sqlite_store, "oracle-06-b")
    first = commit_trigger(first_ctx, "oracle-06-a", source_event="shared-provider-event")
    second = commit_trigger(second_ctx, "oracle-06-b", source_event="shared-provider-event")
    assert first.trigger_id != second.trigger_id
    assert first.case_id != second.case_id
    assert first.source_event_id == second.source_event_id


def test_07_unrelated_same_case_triggers_do_not_auto_group(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    ctx = context(sqlite_store, "oracle-07")
    first = commit_trigger(ctx, "oracle-07-a", scope=frozenset({"service:a"}))
    second = commit_trigger(ctx, "oracle-07-b", scope=frozenset({"service:b"}))
    with pytest.raises(DomainRuleViolation, match="GROUPING NOT ESTABLISHED"):
        commit_reassessment(ctx, "oracle-07", (first.version_id, second.version_id))
    assert (
        ctx.service.trigger_coverage(trigger_version_id=first.version_id, effective_at=NOW).state
        is TriggerCoverageState.REASSESSMENT_REQUIRED_UNASSIGNED
    )


def test_08_structurally_disjoint_reassessments_may_coexist(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    ctx = context(sqlite_store, "oracle-08")
    first = commit_trigger(ctx, "oracle-08-a", scope=frozenset({"service:a"}))
    second = commit_trigger(ctx, "oracle-08-b", scope=frozenset({"service:b"}))
    first_reassessment = commit_reassessment(
        ctx, "oracle-08-a", (first.version_id,), scope=frozenset({"service:a"})
    )
    second_reassessment = commit_reassessment(
        ctx, "oracle-08-b", (second.version_id,), scope=frozenset({"service:b"})
    )
    assert ctx.service.reassessment_overlap(
        first_version_id=first_reassessment.version_id,
        second_version_id=second_reassessment.version_id,
        effective_at=NOW,
    ).compatible


def test_09_overlapping_reassessments_conflict_and_block_completion(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    ctx = context(sqlite_store, "oracle-09")
    first = commit_trigger(ctx, "oracle-09-a")
    second = commit_trigger(ctx, "oracle-09-b")
    first_reassessment = commit_reassessment(ctx, "oracle-09-a", (first.version_id,))
    second_reassessment = commit_reassessment(ctx, "oracle-09-b", (second.version_id,))
    overlap = ctx.service.reassessment_overlap(
        first_version_id=first_reassessment.version_id,
        second_version_id=second_reassessment.version_id,
        effective_at=NOW,
    )
    assert not overlap.compatible
    assert overlap.reason == "REASSESSMENT OVERLAP CONFLICT — UNRESOLVED"
    first_reassessment = ready_for_completion(ctx, "oracle-09", first_reassessment)
    with pytest.raises(DomainRuleViolation, match="overlap conflict"):
        ctx.service.complete_confirmed(
            meta("oracle-09-complete"), confirmation(ctx, first_reassessment)
        )


def test_10_trigger_cannot_be_consumed_without_exact_membership(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    ctx = context(sqlite_store, "oracle-10")
    first = commit_trigger(ctx, "oracle-10-a", scope=frozenset({"service:a"}))
    second = commit_trigger(ctx, "oracle-10-b", scope=frozenset({"service:b"}))
    reassessment = commit_reassessment(
        ctx, "oracle-10", (first.version_id,), scope=frozenset({"service:a"})
    )
    assert (
        ctx.service.trigger_coverage(trigger_version_id=second.version_id, effective_at=NOW).state
        is TriggerCoverageState.REASSESSMENT_REQUIRED_UNASSIGNED
    )
    with sqlite_store.read_transaction() as transaction:
        assert tuple(item[0] for item in transaction.trigger_set(reassessment.version_id)) == (
            first.version_id,
        )


def test_11_merge_is_rejected_without_history_change(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    ctx = context(sqlite_store, "oracle-11")
    before = sqlite_store.count_rows("reassessment_versions")
    with pytest.raises(DomainRuleViolation, match="MERGE UNSUPPORTED"):
        ctx.service.reject_merge("anything")
    assert sqlite_store.count_rows("reassessment_versions") == before


def test_12_supersession_preserves_history_and_transfers_coverage_atomically(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    ctx = context(sqlite_store, "oracle-12")
    trigger = commit_trigger(ctx, "oracle-12")
    predecessor = commit_reassessment(ctx, "oracle-12-a", (trigger.version_id,))
    successor = commit_reassessment(ctx, "oracle-12-b", (trigger.version_id,))
    determination = coordination_determination(
        ctx,
        "oracle-12",
        kind=ReassessmentDeterminationKind.SUPERSESSION,
        outcome=ReassessmentDeterminationOutcome.SUPERSESSION_AUTHORIZED,
        reassessments=(predecessor.version_id,),
        target=predecessor.version_id,
    )
    ctx.service.terminate_reassessment(
        meta("oracle-12-terminate"),
        ReassessmentTerminationRequest(
            predecessor.reassessment_id,
            predecessor.version_id,
            determination.version_id,
            NOW,
            successor.version_id,
        ),
        supersede=True,
    )
    coverage = ctx.service.trigger_coverage(trigger_version_id=trigger.version_id, effective_at=NOW)
    assert coverage.state is TriggerCoverageState.LINKED_ACTIVE
    assert coverage.supporting_version_ids == frozenset({successor.version_id})
    assert sqlite_store.get_history(predecessor.reassessment_id).versions


def test_13_trigger_withdrawal_preserves_completed_historical_basis(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    ctx = context(sqlite_store, "oracle-13")
    trigger = commit_trigger(ctx, "oracle-13")
    reassessment = commit_reassessment(ctx, "oracle-13", (trigger.version_id,))
    reassessment = ready_for_completion(ctx, "oracle-13", reassessment)
    result = ctx.service.complete_confirmed(
        meta("oracle-13-complete"), confirmation(ctx, reassessment)
    )
    withdrawn = trigger_input(
        ctx,
        "oracle-13",
        trigger_id=trigger.trigger_id,
        source_event=trigger.source_event_id,
        source_version="withdrawn-source-version",
        expected_version_id=trigger.version_id,
        withdrawn=True,
    )
    ctx.service.commit_trigger(meta("oracle-13-withdraw"), withdrawn)
    old_coverage = ctx.service.trigger_coverage(
        trigger_version_id=trigger.version_id, effective_at=NOW
    )
    assert old_coverage.state is None
    assert result.status is ReassessmentStatus.COMPLETED_CONFIRMED
    with sqlite_store.read_transaction() as transaction:
        assert transaction.reassessment_completion(reassessment.version_id) is not None


def test_15_exactly_one_unchanged_completion_path_commits_atomically(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    ctx = context(sqlite_store, "oracle-15")
    trigger = commit_trigger(ctx, "oracle-15")
    reassessment = commit_reassessment(ctx, "oracle-15", (trigger.version_id,))
    reassessment = ready_for_completion(ctx, "oracle-15", reassessment)
    valid_confirmation = confirmation(ctx, reassessment)
    incomplete_confirmation = replace(
        valid_confirmation,
        confirmation_id=RecordId.new(),
        version_id=RecordVersionId.new(),
        reviewed_domains={
            key: references
            for key, references in valid_confirmation.reviewed_domains.items()
            if key != "risk"
        },
    )
    with pytest.raises(DomainRuleViolation, match="confirmation knowledge/rationale is invalid"):
        ctx.service.complete_confirmed(meta("oracle-15-incomplete"), incomplete_confirmation)
    assert sqlite_store.count_rows("reassessment_completion_outcomes") == 0
    result = ctx.service.complete_confirmed(meta("oracle-15-complete"), valid_confirmation)
    assert result.completed and result.status is ReassessmentStatus.COMPLETED_CONFIRMED
    assert sqlite_store.count_rows("decision_confirmation_versions") == 1
    assert sqlite_store.count_rows("reassessment_completion_outcomes") == 1
    with pytest.raises(DomainRuleViolation, match="AWAITING_DECISION_AUTHORITY"):
        ctx.service.complete_confirmed(
            meta("oracle-15-second-path"), confirmation(ctx, reassessment)
        )
    assert sqlite_store.count_rows("reassessment_completion_outcomes") == 1


def test_16_one_completion_does_not_auto_close_another_reassessment(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    ctx = context(sqlite_store, "oracle-16")
    first = commit_trigger(ctx, "oracle-16-a", scope=frozenset({"service:a"}))
    second = commit_trigger(ctx, "oracle-16-b", scope=frozenset({"service:b"}))
    first_reassessment = commit_reassessment(
        ctx, "oracle-16-a", (first.version_id,), scope=frozenset({"service:a"})
    )
    second_reassessment = commit_reassessment(
        ctx, "oracle-16-b", (second.version_id,), scope=frozenset({"service:b"})
    )
    first_reassessment = ready_for_completion(ctx, "oracle-16", first_reassessment)
    second_reassessment = commit_reassessment(
        ctx,
        "oracle-16-b-analysis",
        (second.version_id,),
        reassessment_id=second_reassessment.reassessment_id,
        scope=second_reassessment.affected_scope,
        expected_version_id=second_reassessment.version_id,
        status=ReassessmentStatus.ANALYSIS_IN_PROGRESS,
    )
    ctx.service.complete_confirmed(
        meta("oracle-16-complete"), confirmation(ctx, first_reassessment)
    )
    with sqlite_store.read_transaction() as transaction:
        assert (
            transaction.current_reassessment_status(
                reassessment_version_id=second_reassessment.version_id,
                effective_at=NOW,
                known_at=NOW,
            )
            == ReassessmentStatus.ANALYSIS_IN_PROGRESS.value
        )


def test_17_authorized_successor_blocks_stale_predecessor_completion(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    ctx = context(sqlite_store, "oracle-17")
    first = commit_trigger(ctx, "oracle-17-a", scope=frozenset({"service:a"}))
    second = commit_trigger(ctx, "oracle-17-b", scope=frozenset({"service:b"}))
    first_reassessment = commit_reassessment(
        ctx, "oracle-17-a", (first.version_id,), scope=frozenset({"service:a"})
    )
    second_reassessment = commit_reassessment(
        ctx, "oracle-17-b", (second.version_id,), scope=frozenset({"service:b"})
    )
    first_reassessment = ready_for_completion(ctx, "oracle-17-a", first_reassessment)
    second_reassessment = ready_for_completion(ctx, "oracle-17-b", second_reassessment)
    successor = successor_request(ctx, first_reassessment)
    invalid_boundary = replace(
        successor.successor_boundary,
        clauses=(
            replace(
                successor.successor_boundary.clauses[0],
                verification_mode=BoundaryVerificationMode.HUMAN,
            ),
        ),
    )
    before_decisions = sqlite_store.count_rows("decision_versions")
    with pytest.raises(DomainRuleViolation, match="bundle mismatch"):
        ctx.service.complete_with_successor(
            meta("oracle-17-invalid-successor"),
            replace(successor, successor_boundary=invalid_boundary),
        )
    assert sqlite_store.count_rows("decision_versions") == before_decisions
    assert sqlite_store.count_rows("reassessment_completion_outcomes") == 0
    result = ctx.service.complete_with_successor(meta("oracle-17-successor"), successor)
    assert result.status is ReassessmentStatus.COMPLETED_SUCCESSOR_DECISION
    with pytest.raises(DomainRuleViolation, match="current authorized Decision not established"):
        ctx.service.complete_confirmed(
            meta("oracle-17-stale-completion"), confirmation(ctx, second_reassessment)
        )


def test_18_disjoint_dispositions_remain_independently_effective(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    ctx = context(sqlite_store, "oracle-18")
    first = commit_trigger(ctx, "oracle-18-a", scope=frozenset({"service:a"}))
    second = commit_trigger(ctx, "oracle-18-b", scope=frozenset({"service:b"}))
    first_reassessment = commit_reassessment(
        ctx, "oracle-18-a", (first.version_id,), scope=frozenset({"service:a"})
    )
    second_reassessment = commit_reassessment(
        ctx, "oracle-18-b", (second.version_id,), scope=frozenset({"service:b"})
    )
    disposition(
        ctx,
        "oracle-18-a",
        first_reassessment,
        allowed=frozenset({"read", "review"}),
        prohibited=frozenset({"deploy"}),
    )
    disposition(
        ctx,
        "oracle-18-b",
        second_reassessment,
        operating_state="manual-only",
        allowed=frozenset({"review"}),
        prohibited=frozenset({"read"}),
    )
    effective = ctx.service.effective_operating_disposition(
        case_id=ctx.foundation.context.case_id,
        decision_version_id=ctx.foundation.decision_version_id,
        configuration_version_id=ctx.foundation.context.configuration_version_id,
        effective_at=NOW,
    )
    partitions = {partition.affected_scope: partition for partition in effective.partitions}
    assert set(partitions) == {frozenset({"service:a"}), frozenset({"service:b"})}
    assert not partitions[frozenset({"service:a"})].suspended
    assert partitions[frozenset({"service:a"})].allowed_actions == frozenset({"read", "review"})
    assert not partitions[frozenset({"service:b"})].suspended
    assert partitions[frozenset({"service:b"})].allowed_actions == frozenset({"review"})


def test_overlapping_compatible_dispositions_intersect_only_on_overlap(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    ctx = context(sqlite_store, "overlap-compatible")
    trigger = commit_trigger(
        ctx, "overlap-compatible", scope=frozenset({"service:a", "service:b", "service:c"})
    )
    reassessment = commit_reassessment(
        ctx,
        "overlap-compatible",
        (trigger.version_id,),
        scope=frozenset({"service:a", "service:b", "service:c"}),
    )
    disposition(
        ctx,
        "overlap-compatible-a",
        reassessment,
        allowed=frozenset({"read", "review"}),
        required=frozenset({"control:a"}),
        scope=frozenset({"service:a", "service:b"}),
    )
    disposition(
        ctx,
        "overlap-compatible-b",
        reassessment,
        allowed=frozenset({"review"}),
        required=frozenset({"control:b"}),
        scope=frozenset({"service:b", "service:c"}),
    )
    effective = ctx.service.effective_operating_disposition(
        case_id=ctx.foundation.context.case_id,
        decision_version_id=ctx.foundation.decision_version_id,
        configuration_version_id=ctx.foundation.context.configuration_version_id,
        effective_at=NOW,
    )
    partitions = {partition.affected_scope: partition for partition in effective.partitions}
    overlap = partitions[frozenset({"service:b"})]
    assert overlap.allowed_actions == frozenset({"review"})
    assert overlap.required_controls == frozenset({"control:a", "control:b"})
    assert not overlap.suspended
    assert partitions[frozenset({"service:a"})].allowed_actions == frozenset({"read", "review"})
    assert partitions[frozenset({"service:c"})].required_controls == frozenset({"control:b"})


def test_overlapping_indeterminate_dispositions_suspend_only_the_overlap(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    ctx = context(sqlite_store, "overlap-indeterminate")
    trigger = commit_trigger(
        ctx, "overlap-indeterminate", scope=frozenset({"service:a", "service:b", "service:c"})
    )
    reassessment = commit_reassessment(
        ctx,
        "overlap-indeterminate",
        (trigger.version_id,),
        scope=frozenset({"service:a", "service:b", "service:c"}),
    )
    disposition(
        ctx,
        "overlap-indeterminate-a",
        reassessment,
        operating_state="state-a",
        scope=frozenset({"service:a", "service:b"}),
    )
    disposition(
        ctx,
        "overlap-indeterminate-b",
        reassessment,
        operating_state="state-b",
        scope=frozenset({"service:b", "service:c"}),
    )
    effective = ctx.service.effective_operating_disposition(
        case_id=ctx.foundation.context.case_id,
        decision_version_id=ctx.foundation.decision_version_id,
        configuration_version_id=ctx.foundation.context.configuration_version_id,
        effective_at=NOW,
    )
    partitions = {partition.affected_scope: partition for partition in effective.partitions}
    assert not partitions[frozenset({"service:a"})].suspended
    assert partitions[frozenset({"service:b"})].suspended
    assert partitions[frozenset({"service:b"})].operating_state_values == frozenset(
        {"state-a", "state-b"}
    )
    assert not partitions[frozenset({"service:c"})].suspended


def test_unrelated_scope_is_unchanged_by_an_indeterminate_overlap(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    ctx = context(sqlite_store, "overlap-unrelated")
    trigger = commit_trigger(
        ctx,
        "overlap-unrelated",
        scope=frozenset({"service:a", "service:b", "service:unrelated"}),
    )
    reassessment = commit_reassessment(
        ctx,
        "overlap-unrelated",
        (trigger.version_id,),
        scope=frozenset({"service:a", "service:b", "service:unrelated"}),
    )
    disposition(
        ctx,
        "overlap-unrelated-a",
        reassessment,
        operating_state="state-a",
        scope=frozenset({"service:a", "service:b"}),
    )
    disposition(
        ctx,
        "overlap-unrelated-b",
        reassessment,
        operating_state="state-b",
        scope=frozenset({"service:b"}),
    )
    disposition(
        ctx,
        "overlap-unrelated-c",
        reassessment,
        operating_state="unrelated-state",
        allowed=frozenset({"observe"}),
        required=frozenset({"unrelated-control"}),
        prohibited=frozenset({"unrelated-prohibition"}),
        scope=frozenset({"service:unrelated"}),
    )
    effective = ctx.service.effective_operating_disposition(
        case_id=ctx.foundation.context.case_id,
        decision_version_id=ctx.foundation.decision_version_id,
        configuration_version_id=ctx.foundation.context.configuration_version_id,
        effective_at=NOW,
    )
    partitions = {partition.affected_scope: partition for partition in effective.partitions}
    assert partitions[frozenset({"service:b"})].suspended
    unrelated = partitions[frozenset({"service:unrelated"})]
    assert not unrelated.suspended
    assert unrelated.operating_state_values == frozenset({"unrelated-state"})
    assert unrelated.allowed_actions == frozenset({"observe"})
    assert unrelated.required_controls == frozenset({"unrelated-control"})
    assert unrelated.prohibitions == frozenset({"unrelated-prohibition"})


def test_19_operating_state_values_are_not_ranked(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    ctx = context(sqlite_store, "oracle-19")
    trigger = commit_trigger(ctx, "oracle-19")
    reassessment = commit_reassessment(ctx, "oracle-19", (trigger.version_id,))
    disposition(ctx, "oracle-19-a", reassessment, operating_state="state-z")
    disposition(ctx, "oracle-19-b", reassessment, operating_state="state-a")
    effective = ctx.service.effective_operating_disposition(
        case_id=ctx.foundation.context.case_id,
        decision_version_id=ctx.foundation.decision_version_id,
        configuration_version_id=ctx.foundation.context.configuration_version_id,
        effective_at=NOW,
    )
    assert len(effective.partitions) == 1
    partition = effective.partitions[0]
    assert partition.suspended
    assert partition.operating_state_values == frozenset({"state-a", "state-z"})


def test_20_exact_paim_record_or_external_provenance_needs_no_observation(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    ctx = context(sqlite_store, "oracle-20")
    value = replace(
        trigger_input(ctx, "oracle-20"),
        source_kind=TriggerSourceKind.PAIM_RECORD,
        source_family="boundary-snapshot",
        source_record_id=str(ctx.foundation.snapshot_id),
        source_version_id=str(ctx.foundation.snapshot_version_id),
        source_system=None,
        source_actor=None,
    )
    ctx.service.commit_trigger(meta("oracle-20-trigger"), value)
    assert sqlite_store.count_rows("trigger_versions") == 1
    assert not any("observation" in name for name in metadata.tables)


def test_21_queue_timestamp_and_severity_cannot_coordinate(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    ctx = context(sqlite_store, "oracle-21")
    first = commit_trigger(ctx, "oracle-21-a")
    second = commit_trigger(ctx, "oracle-21-b")
    asserted_queue_metadata = {"queue": "priority-1", "severity": "critical", "newest": second}
    assert asserted_queue_metadata
    with pytest.raises(DomainRuleViolation, match="GROUPING NOT ESTABLISHED"):
        commit_reassessment(ctx, "oracle-21", (first.version_id, second.version_id))


def test_22_later_role_expiry_preserves_historical_determination(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    ctx = context(sqlite_store, "oracle-22", roles=False)
    assignment_version_id = RecordVersionId.new()
    ctx.service.commit_role_assignment(
        meta("oracle-22-expiring-role"),
        RoleAssignmentVersionInput(
            RecordId.new(),
            assignment_version_id,
            ctx.foundation.context.assessor_id,
            AccountabilityFunction.TRIGGER_DETERMINER.value,
            RoleTargetType.CASE,
            str(ctx.foundation.context.case_id),
            ctx.foundation.context.case_id,
            True,
            "bounded historical Trigger Determination",
            DelegationEffect.NONE,
            None,
            EffectiveInterval(utc(2026, 1, 1), utc(2026, 1, 20)),
        ),
    )
    ctx = replace(ctx, trigger_determiner_assignment=assignment_version_id)
    trigger = commit_trigger(
        ctx,
        "oracle-22",
        effective=EffectiveInterval(utc(2026, 1, 10)),
    )
    selected = ctx.service.current_trigger_determination(
        trigger_version_id=trigger.version_id,
        effective_at=utc(2026, 1, 15),
        known_at=NOW,
    )
    assert isinstance(selected, TriggerDeterminationFound)
    later = commit_trigger(
        ctx,
        "oracle-22-later",
        determine=False,
        effective=EffectiveInterval(utc(2026, 2, 1)),
    )
    with pytest.raises(DomainRuleViolation, match="ACCOUNTABILITY NOT ESTABLISHED"):
        ctx.service.commit_trigger_determination(
            meta("oracle-22-later-determination"),
            TriggerDeterminationVersionInput(
                RecordId.new(),
                RecordVersionId.new(),
                later.version_id,
                later.case_id,
                later.decision_version_id,
                later.configuration_version_id,
                TriggerDeterminationOutcome.REASSESSMENT_REQUIRED,
                "Expired assignment cannot support prospective reliance",
                ctx.foundation.context.assessor_id,
                assignment_version_id,
                None,
                (),
                EffectiveInterval(utc(2026, 2, 1)),
            ),
        )


def test_23_unauthorized_duplicate_coordination_is_blocked(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    ctx = context(sqlite_store, "oracle-23", roles=False)
    first = commit_trigger(ctx, "oracle-23-a", determine=False)
    second = commit_trigger(ctx, "oracle-23-b", determine=False)
    value = ReassessmentDeterminationVersionInput(
        RecordId.new(),
        RecordVersionId.new(),
        ReassessmentDeterminationKind.DUPLICATE,
        ReassessmentDeterminationOutcome.DUPLICATE,
        ctx.foundation.context.case_id,
        ctx.foundation.decision_version_id,
        ctx.foundation.context.configuration_version_id,
        frozenset({"service:payments"}),
        (first.version_id, second.version_id),
        (),
        ctx.foundation.context.assessor_id,
        None,
        None,
        (),
        "Software permission is not substantive authority",
        EFFECTIVE,
        canonical_trigger_version_id=first.version_id,
    )
    with pytest.raises(DomainRuleViolation, match="ACCOUNTABILITY NOT ESTABLISHED"):
        ctx.service.commit_reassessment_determination(meta("oracle-23-duplicate"), value)
    selected = ctx.service.current_coordination_determination(
        kind=ReassessmentDeterminationKind.DUPLICATE,
        trigger_version_ids=(first.version_id, second.version_id),
        effective_at=NOW,
    )
    assert isinstance(selected, ReassessmentDeterminationNotEstablished)


def test_14_requiring_unassigned_trigger_remains_authoritatively_queryable(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    ctx = context(sqlite_store, "oracle-14")
    trigger = commit_trigger(ctx, "oracle-14")
    coverage = ctx.service.trigger_coverage(trigger_version_id=trigger.version_id, effective_at=NOW)
    assert coverage.state is TriggerCoverageState.REASSESSMENT_REQUIRED_UNASSIGNED
    assert sqlite_store.count_rows("trigger_versions") == 1


def test_24_reassessment_domain_has_no_management_register_dependency(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    ctx = context(sqlite_store, "oracle-24")
    trigger = commit_trigger(ctx, "oracle-24")
    commit_reassessment(ctx, "oracle-24", (trigger.version_id,))
    assert (
        ctx.service.trigger_coverage(trigger_version_id=trigger.version_id, effective_at=NOW).state
        is TriggerCoverageState.LINKED_ACTIVE
    )
    assert not any("management_register" in name for name in metadata.tables)


def test_25_incompatible_current_trigger_determinations_return_conflict(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    ctx = context(sqlite_store, "oracle-25")
    trigger = commit_trigger(ctx, "oracle-25")
    assert ctx.trigger_determiner_assignment is not None
    ctx.service.commit_trigger_determination(
        meta("oracle-25-second"),
        TriggerDeterminationVersionInput(
            RecordId.new(),
            RecordVersionId.new(),
            trigger.version_id,
            trigger.case_id,
            trigger.decision_version_id,
            trigger.configuration_version_id,
            TriggerDeterminationOutcome.MONITOR,
            "Independent incompatible eligible determination",
            ctx.foundation.context.assessor_id,
            ctx.trigger_determiner_assignment,
            None,
            (),
            EFFECTIVE,
        ),
    )
    selected = ctx.service.current_trigger_determination(
        trigger_version_id=trigger.version_id, effective_at=NOW
    )
    assert isinstance(selected, TriggerDeterminationConflict)
    assert selected.reason == "TRIGGER DETERMINATION CONFLICT — UNRESOLVED"


def test_26_same_context_without_grouping_does_not_group(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    ctx = context(sqlite_store, "oracle-26")
    first = commit_trigger(ctx, "oracle-26-a")
    second = commit_trigger(ctx, "oracle-26-b")
    with pytest.raises(DomainRuleViolation, match="GROUPING NOT ESTABLISHED"):
        commit_reassessment(ctx, "oracle-26", (first.version_id, second.version_id))


def test_27_indeterminate_scope_cannot_prove_non_overlap(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    ctx = context(sqlite_store, "oracle-27")
    first = commit_trigger(ctx, "oracle-27-a", scope=frozenset())
    second = commit_trigger(ctx, "oracle-27-b", scope=frozenset())
    first_reassessment = commit_reassessment(
        ctx, "oracle-27-a", (first.version_id,), scope=frozenset()
    )
    second_reassessment = commit_reassessment(
        ctx, "oracle-27-b", (second.version_id,), scope=frozenset()
    )
    assert not ctx.service.reassessment_overlap(
        first_version_id=first_reassessment.version_id,
        second_version_id=second_reassessment.version_id,
        effective_at=NOW,
    ).compatible


def test_28_cancellation_without_atomic_trigger_coverage_has_no_partial_effect(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    ctx = context(sqlite_store, "oracle-28")
    trigger = commit_trigger(ctx, "oracle-28")
    reassessment = commit_reassessment(ctx, "oracle-28", (trigger.version_id,))
    determination = coordination_determination(
        ctx,
        "oracle-28",
        kind=ReassessmentDeterminationKind.CANCELLATION,
        outcome=ReassessmentDeterminationOutcome.CANCELLATION_AUTHORIZED,
        reassessments=(reassessment.version_id,),
        target=reassessment.version_id,
    )
    with pytest.raises(DomainRuleViolation, match="no-lost-trigger coverage"):
        ctx.service.terminate_reassessment(
            meta("oracle-28-cancel"),
            ReassessmentTerminationRequest(
                reassessment.reassessment_id,
                reassessment.version_id,
                determination.version_id,
                NOW,
            ),
            supersede=False,
        )
    with sqlite_store.read_transaction() as transaction:
        assert (
            transaction.current_reassessment_status(
                reassessment_version_id=reassessment.version_id,
                effective_at=NOW,
                known_at=NOW,
            )
            == ReassessmentStatus.OPEN.value
        )
    assert (
        ctx.service.trigger_coverage(trigger_version_id=trigger.version_id, effective_at=NOW).state
        is TriggerCoverageState.LINKED_ACTIVE
    )


def test_29_incompatible_current_coverage_results_return_conflict(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    ctx = context(sqlite_store, "oracle-29")
    trigger = commit_trigger(ctx, "oracle-29")
    first = commit_reassessment(ctx, "oracle-29-a", (trigger.version_id,))
    second = commit_reassessment(ctx, "oracle-29-b", (trigger.version_id,))
    coverage = ctx.service.trigger_coverage(trigger_version_id=trigger.version_id, effective_at=NOW)
    assert coverage.state is TriggerCoverageState.BLOCKED_CONFLICT
    assert coverage.supporting_version_ids == frozenset({first.version_id, second.version_id})
    assert coverage.reason == "TRIGGER COVERAGE CONFLICT — UNRESOLVED"


def test_30_identity_level_duplicate_disposition_names_canonical_trigger(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    ctx = context(sqlite_store, "oracle-30")
    canonical = commit_trigger(ctx, "oracle-30-a")
    duplicate = commit_trigger(ctx, "oracle-30-b")
    determination = coordination_determination(
        ctx,
        "oracle-30",
        kind=ReassessmentDeterminationKind.DUPLICATE,
        outcome=ReassessmentDeterminationOutcome.DUPLICATE,
        triggers=(canonical.version_id, duplicate.version_id),
        canonical=canonical.version_id,
    )
    canonical_coverage = ctx.service.trigger_coverage(
        trigger_version_id=canonical.version_id, effective_at=NOW
    )
    duplicate_coverage = ctx.service.trigger_coverage(
        trigger_version_id=duplicate.version_id, effective_at=NOW
    )
    assert canonical_coverage.state is TriggerCoverageState.REASSESSMENT_REQUIRED_UNASSIGNED
    assert duplicate_coverage.state is TriggerCoverageState.DUPLICATE_DISPOSITIONED
    assert duplicate_coverage.supporting_version_ids == frozenset({determination.version_id})
    selected = ctx.service.current_coordination_determination(
        kind=ReassessmentDeterminationKind.DUPLICATE,
        trigger_version_ids=(canonical.version_id, duplicate.version_id),
        effective_at=NOW,
    )
    assert isinstance(selected, ReassessmentDeterminationFound)


def test_31_fabricated_governed_mechanism_token_is_rejected(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    ctx = context(sqlite_store, "oracle-31", roles=False)
    trigger = commit_trigger(ctx, "oracle-31", determine=False)
    with pytest.raises(DomainRuleViolation, match="GOVERNED MECHANISM NOT ESTABLISHED"):
        ctx.service.commit_trigger_determination(
            meta("oracle-31-determination"),
            TriggerDeterminationVersionInput(
                RecordId.new(),
                RecordVersionId.new(),
                trigger.version_id,
                trigger.case_id,
                trigger.decision_version_id,
                trigger.configuration_version_id,
                TriggerDeterminationOutcome.REASSESSMENT_REQUIRED,
                "Fabricated mechanism must fail",
                ctx.foundation.context.assessor_id,
                None,
                RecordVersionId.new(),
                (),
                EFFECTIVE,
            ),
        )


def test_32_genuine_exact_governed_mechanism_is_accepted(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    ctx = context(sqlite_store, "oracle-32", roles=False)
    mechanism = ReassessmentMechanismVersionInput(
        RecordId.new(),
        RecordVersionId.new(),
        AccountabilityFunction.TRIGGER_DETERMINER,
        ctx.foundation.context.case_id,
        ctx.foundation.decision_version_id,
        ctx.foundation.context.configuration_version_id,
        ctx.foundation.context.assessor_id,
        "trigger-policy-v1",
        "exact Case/Decision/Configuration",
        "approved operating charter",
        ("no cross-Case authority",),
        EFFECTIVE,
    )
    ctx.service.commit_reassessment_mechanism(meta("oracle-32-mechanism"), mechanism)
    trigger = commit_trigger(ctx, "oracle-32", determine=False)
    ctx.service.commit_trigger_determination(
        meta("oracle-32-determination"),
        TriggerDeterminationVersionInput(
            RecordId.new(),
            RecordVersionId.new(),
            trigger.version_id,
            trigger.case_id,
            trigger.decision_version_id,
            trigger.configuration_version_id,
            TriggerDeterminationOutcome.REASSESSMENT_REQUIRED,
            "Governed mechanism is exact and current",
            ctx.foundation.context.assessor_id,
            None,
            mechanism.version_id,
            (),
            EFFECTIVE,
        ),
    )
    selected = ctx.service.current_trigger_determination(
        trigger_version_id=trigger.version_id, effective_at=NOW
    )
    assert isinstance(selected, TriggerDeterminationFound)


def test_33_stale_expected_trigger_set_precondition_rejects_without_rebase(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    ctx = context(sqlite_store, "oracle-33")
    first = commit_trigger(ctx, "oracle-33-a")
    initial = commit_reassessment(ctx, "oracle-33-a", (first.version_id,))
    second = commit_trigger(ctx, "oracle-33-b")
    grouping(ctx, "oracle-33", (first.version_id, second.version_id))
    successor = commit_reassessment(
        ctx,
        "oracle-33-b",
        (first.version_id, second.version_id),
        reassessment_id=initial.reassessment_id,
        expected_version_id=initial.version_id,
    )
    stale = reassessment_input(
        ctx,
        "oracle-33-stale",
        (first.version_id, second.version_id),
        reassessment_id=initial.reassessment_id,
        expected_version_id=initial.version_id,
    )
    with pytest.raises(DomainPreconditionFailed, match=r"expected .*; observed"):
        ctx.service.commit_reassessment(meta("oracle-33-stale"), stale)
    assert {
        item.version_id for item in sqlite_store.get_history(initial.reassessment_id).versions
    } == {
        initial.version_id,
        successor.version_id,
    }


def test_34_future_effective_successor_changes_eligibility_only_when_effective(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    ctx = context(sqlite_store, "oracle-34")
    trigger = commit_trigger(ctx, "oracle-34")
    reassessment = commit_reassessment(ctx, "oracle-34", (trigger.version_id,))
    reassessment = ready_for_completion(ctx, "oracle-34", reassessment)
    future = utc(2026, 3, 1)
    request = successor_request(ctx, reassessment, effective_at=future)
    successor_recorded_at = utc(2026, 2, 2)
    successor_service = Increment6ApplicationService(
        sqlite_store, FixedClock(successor_recorded_at)
    )
    successor_service.complete_with_successor(meta("oracle-34-successor"), request)
    before = successor_service.current_authorized_decision(
        case_id=ctx.foundation.context.case_id,
        configuration_version_id=ctx.foundation.context.configuration_version_id,
        effective_at=utc(2026, 2, 15),
        known_at=successor_recorded_at,
    )
    after = successor_service.current_authorized_decision(
        case_id=ctx.foundation.context.case_id,
        configuration_version_id=ctx.foundation.context.configuration_version_id,
        effective_at=future,
        known_at=successor_recorded_at,
    )
    before_successor_was_known = successor_service.current_authorized_decision(
        case_id=ctx.foundation.context.case_id,
        configuration_version_id=ctx.foundation.context.configuration_version_id,
        effective_at=future,
        known_at=NOW,
    )
    assert isinstance(before, AuthorizedDecisionFound)
    assert isinstance(after, AuthorizedDecisionFound)
    assert isinstance(before_successor_was_known, AuthorizedDecisionFound)
    assert before.decision_version_id == ctx.foundation.decision_version_id
    assert after.decision_version_id == request.successor_decision.version_id
    assert before_successor_was_known.decision_version_id == ctx.foundation.decision_version_id
    with sqlite_store.read_transaction() as transaction:
        assert (
            transaction.current_reassessment_status(
                reassessment_version_id=reassessment.version_id,
                effective_at=utc(2026, 2, 15),
                known_at=successor_recorded_at,
            )
            == ReassessmentStatus.AWAITING_DECISION_AUTHORITY.value
        )
        assert (
            transaction.current_reassessment_status(
                reassessment_version_id=reassessment.version_id,
                effective_at=future,
                known_at=successor_recorded_at,
            )
            == ReassessmentStatus.COMPLETED_SUCCESSOR_DECISION.value
        )


@pytest.mark.parametrize(
    "source_category",
    (
        "incident",
        "control-failure",
        "provider-model-change",
        "authority-resolution",
        "capacity-change",
        "completed-learning",
        "stronger-state-request",
        "scheduled-review",
    ),
)
def test_35_all_required_source_categories_preserve_exact_completed_provenance(
    sqlite_store: SQLiteIntegrityStore,
    source_category: str,
) -> None:
    ctx = context(sqlite_store, f"oracle-35-{source_category}")
    trigger = replace(
        trigger_input(ctx, f"oracle-35-{source_category}"),
        trigger_type=source_category,
        source_family=source_category,
        provenance={"category": source_category, "exact": True},
    )
    ctx.service.commit_trigger(meta(f"oracle-35-{source_category}-trigger"), trigger)
    assert ctx.trigger_determiner_assignment is not None
    ctx.service.commit_trigger_determination(
        meta(f"oracle-35-{source_category}-determination"),
        TriggerDeterminationVersionInput(
            RecordId.new(),
            RecordVersionId.new(),
            trigger.version_id,
            trigger.case_id,
            trigger.decision_version_id,
            trigger.configuration_version_id,
            TriggerDeterminationOutcome.REASSESSMENT_REQUIRED,
            "Same exact cardinality rule for every source category",
            ctx.foundation.context.assessor_id,
            ctx.trigger_determiner_assignment,
            None,
            (),
            EFFECTIVE,
        ),
    )
    reassessment = commit_reassessment(ctx, f"oracle-35-{source_category}", (trigger.version_id,))
    reassessment = ready_for_completion(ctx, f"oracle-35-{source_category}", reassessment)
    result = ctx.service.complete_confirmed(
        meta(f"oracle-35-{source_category}-complete"), confirmation(ctx, reassessment)
    )
    stored = sqlite_store.get_version(trigger.version_id)
    assert result.status is ReassessmentStatus.COMPLETED_CONFIRMED
    assert stored is not None and stored.content["provenance"] == {
        "category": source_category,
        "exact": True,
    }
