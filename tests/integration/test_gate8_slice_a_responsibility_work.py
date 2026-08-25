from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime

import pytest

from paim.application import Increment3ApplicationService
from paim.audit import ActorResolution
from paim.domain import CommandMeta, RoleTargetType
from paim.domain.increment3 import AuthorityVersionInput
from paim.integrity import CommandId, EffectiveInterval, FixedClock, RecordId, RecordVersionId
from paim.integrity.records import FinalizedRecordVersion, canonical_json
from paim.integrity.semantics import (
    ContextMemberKind,
    ExactContextMember,
    ExactContextSet,
    SemanticContractRef,
)
from paim.integrity.time import to_epoch_microseconds
from paim.persistence.sqlite import SQLiteIntegrityStore
from paim.responsibility.models import (
    ObligationKind,
    ResponsibilityResolutionKind,
    responsibility_signature,
)
from paim.responsibility.service import (
    ProjectionFact,
    ResponsibilityWorkService,
    SliceAAccessDenied,
    SliceACommand,
    SliceAConflict,
    SliceATransaction,
)
from tests.helpers import utc
from tests.integration.test_increment_2_foundation import add_actor, add_case, add_role

NOW = utc(2026, 8, 24)
CONTRACT = SemanticContractRef("paim-gate8-slice-a", "1")


class ExactAccess:
    def __init__(self, *, allowed: bool = True) -> None:
        self.allowed = allowed

    def authorize(self, **_: object) -> bool:
        return self.allowed


class RevokedAtCommitAccess:
    def __init__(self) -> None:
        self.calls = 0

    def authorize(self, **_: object) -> bool:
        self.calls += 1
        return self.calls == 1


def context(case_id: RecordId, case_version_id: RecordVersionId) -> ExactContextSet:
    return ExactContextSet.create(
        (
            ExactContextMember("owning_case", ContextMemberKind.RECORD, str(case_id)),
            ExactContextMember(
                "owning_case_version", ContextMemberKind.VERSION, str(case_version_id)
            ),
            ExactContextMember("purpose", ContextMemberKind.LITERAL, "slice-a-proof"),
        )
    )


def command(
    *,
    case_id: RecordId,
    actor_id: RecordId,
    exact_context: ExactContextSet,
    family: str,
    key: str,
    projections: tuple[ProjectionFact, ...],
) -> SliceACommand:
    return SliceACommand(
        CommandId.new(),
        "gate8-slice-a-tests",
        key,
        "principal:slice-a",
        str(actor_id),
        RecordId.new(),
        RecordVersionId.new(),
        family,
        f"case:{case_id}",
        {"kind": family},
        NOW,
        CONTRACT,
        exact_context,
        case_id,
        f"{family}.commit",
        projections,
    )


def signature(exact_context: ExactContextSet, obligation: str) -> str:
    case_member = next(member for member in exact_context.members if member.slot == "owning_case")
    return responsibility_signature(
        contract=CONTRACT,
        obligation_kind=ObligationKind(obligation),
        owning_case_id=RecordId.parse(case_member.identity),
        context=exact_context,
        purpose="continuing-review",
        use="case-management",
        scope="exact-case-context",
    )


def authority_source(
    store: SQLiteIntegrityStore,
    *,
    case_id: RecordId,
    assigning_actor_id: RecordId,
    exact_context: ExactContextSet,
    signature_digest: str,
    obligation: str,
    maximum: int = 2,
) -> RecordVersionId:
    authority_id, version_id = RecordId.new(), RecordVersionId.new()
    Increment3ApplicationService(store, FixedClock(NOW)).commit_authority_record(
        CommandMeta(
            CommandId.new(),
            "gate8-slice-a-tests",
            f"authority-{version_id}",
            "principal:slice-a",
            str(assigning_actor_id),
            ActorResolution.PROVIDED,
        ),
        AuthorityVersionInput(
            authority_id,
            version_id,
            None,
            None,
            None,
            "assignment-authority",
            "governance-charter",
            {"source": "slice-a-oracle"},
            "exact Responsibility assignment",
            "assignment requires exact bounded basis",
            {
                "assignment_authority": {
                    "assigning_actor_id": str(assigning_actor_id),
                    "allowed_case_ids": [str(case_id)],
                    "allowed_obligation_kinds": [obligation],
                    "allowed_signature_digests": [signature_digest],
                    "context_digest": exact_context.digest,
                    "max_active_assignments": maximum,
                    "limits": {"max_active_assignments": maximum},
                }
            },
            EffectiveInterval(NOW),
        ),
    )
    return version_id


def responsibility_command(
    *,
    case_id: RecordId,
    actor_id: RecordId,
    exact_context: ExactContextSet,
    obligation: str,
    key: str,
    practical_role: str | None = None,
) -> tuple[SliceACommand, str]:
    digest = signature(exact_context, obligation)
    result = command(
        case_id=case_id,
        actor_id=actor_id,
        exact_context=exact_context,
        family="responsibility",
        key=key,
        projections=(),
    )
    projections = [
        ProjectionFact("responsibility_records", {"record_id": str(result.record_id)}),
        ProjectionFact(
            "responsibility_versions",
            {
                "version_id": str(result.version_id),
                "record_id": str(result.record_id),
                "obligation_kind": obligation,
                "owning_case_id": str(case_id),
                "context_digest": exact_context.digest,
                "signature_digest": digest,
            },
        ),
    ]
    if practical_role is not None:
        projections.append(
            ProjectionFact(
                "responsibility_practical_roles",
                {
                    "responsibility_version_id": str(result.version_id),
                    "role_code": practical_role,
                },
            )
        )
    result = replace(
        result,
        content={
            "purpose_discriminator": "continuing-review",
            "use_discriminator": "case-management",
            "scope_discriminator": "exact-case-context",
        },
        projections=tuple(projections),
    )
    return result, digest


def basis_command(
    *,
    case_id: RecordId,
    assigning_actor_id: RecordId,
    exact_context: ExactContextSet,
    source_version_id: RecordVersionId,
    obligation: str,
    signature_digest: str,
    key: str,
    maximum: int = 2,
    record_id: RecordId | None = None,
    version_id: RecordVersionId | None = None,
    expected_version_id: RecordVersionId | None = None,
    state: str = "ACTIVE",
) -> SliceACommand:
    result = command(
        case_id=case_id,
        actor_id=assigning_actor_id,
        exact_context=exact_context,
        family="assignment-basis",
        key=key,
        projections=(),
    )
    result = replace(
        result,
        record_id=record_id or result.record_id,
        version_id=version_id or result.version_id,
        expected_version_id=expected_version_id,
    )
    return replace(
        result,
        projections=(
            *(
                ()
                if expected_version_id
                else (
                    ProjectionFact(
                        "assignment_basis_records", {"record_id": str(result.record_id)}
                    ),
                )
            ),
            ProjectionFact(
                "assignment_basis_versions",
                {
                    "version_id": str(result.version_id),
                    "record_id": str(result.record_id),
                    "assigning_actor_id": str(assigning_actor_id),
                    "basis_source_version_id": str(source_version_id),
                    "owning_case_id": str(case_id),
                    "context_digest": exact_context.digest,
                    "allowed_obligation_kinds_json": json.dumps([obligation]),
                    "allowed_case_ids_json": json.dumps([str(case_id)]),
                    "allowed_signature_digests_json": json.dumps([signature_digest]),
                    "limits_json": json.dumps({"max_active_assignments": maximum}),
                    "max_active_assignments": maximum,
                    "state": state,
                    "effective_from_us": to_epoch_microseconds(NOW),
                    "effective_to_us": None,
                    "recorded_at_us": 0,
                    "predecessor_version_id": (
                        str(expected_version_id) if expected_version_id else None
                    ),
                },
            ),
        ),
    )


def assignment_command(
    *,
    case_id: RecordId,
    assigning_actor_id: RecordId,
    assigned_actor_id: RecordId,
    exact_context: ExactContextSet,
    responsibility: SliceACommand,
    signature_digest: str,
    basis: SliceACommand,
    key: str,
) -> SliceACommand:
    result = command(
        case_id=case_id,
        actor_id=assigning_actor_id,
        exact_context=exact_context,
        family="responsibility-assignment",
        key=key,
        projections=(),
    )
    return replace(
        result,
        projections=(
            ProjectionFact(
                "responsibility_assignment_records", {"record_id": str(result.record_id)}
            ),
            ProjectionFact(
                "responsibility_assignment_versions",
                {
                    "version_id": str(result.version_id),
                    "record_id": str(result.record_id),
                    "responsibility_version_id": str(responsibility.version_id),
                    "signature_digest": signature_digest,
                    "actor_id": str(assigned_actor_id),
                    "assignment_basis_version_id": str(basis.version_id),
                    "state": "ASSIGNED",
                    "effective_from_us": to_epoch_microseconds(NOW),
                    "effective_to_us": None,
                    "recorded_at_us": 0,
                    "predecessor_version_id": None,
                },
            ),
        ),
    )


def test_responsibility_work_vertical_proof_replay_restart_and_atomic_failure(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    case_id, case_version_id = add_case(sqlite_store, "slice-a")
    actor_a, _ = add_actor(sqlite_store, "slice-a-a")
    actor_b, _ = add_actor(sqlite_store, "slice-a-b")
    exact_context = context(case_id, case_version_id)
    svc = ResponsibilityWorkService(sqlite_store, FixedClock(NOW), ExactAccess())
    obligation = "COMPLETE_CONTINUING_REVIEW"
    signature_digest = signature(exact_context, obligation)

    responsibility = command(
        case_id=case_id,
        actor_id=actor_a,
        exact_context=exact_context,
        family="responsibility",
        key="responsibility",
        projections=(
            ProjectionFact("responsibility_records", {}),
            ProjectionFact(
                "responsibility_versions",
                {
                    "obligation_kind": obligation,
                    "owning_case_id": str(case_id),
                    "context_digest": exact_context.digest,
                    "signature_digest": signature_digest,
                },
            ),
        ),
    )
    # Projection identities are exact command identities, filled without hidden inference.
    responsibility = replace(
        responsibility,
        content={
            "purpose_discriminator": "continuing-review",
            "use_discriminator": "case-management",
            "scope_discriminator": "exact-case-context",
        },
        projections=(
            ProjectionFact("responsibility_records", {"record_id": str(responsibility.record_id)}),
            ProjectionFact(
                "responsibility_versions",
                {
                    "version_id": str(responsibility.version_id),
                    "record_id": str(responsibility.record_id),
                    "obligation_kind": obligation,
                    "owning_case_id": str(case_id),
                    "context_digest": exact_context.digest,
                    "signature_digest": signature_digest,
                },
            ),
        ),
    )
    first = svc.commit(responsibility)
    assert svc.commit(responsibility) == first
    with sqlite_store.read_transaction() as transaction:
        stored_practical_roles = transaction.projection_rows(
            "responsibility_practical_roles",
            responsibility_version_id=str(responsibility.version_id),
        )
    assert stored_practical_roles == ()
    assert (
        svc.resolve_responsibility(
            principal_id="principal:slice-a",
            actor_id=str(actor_a),
            owning_case_id=case_id,
            signature_digest=signature_digest,
            effective_at=NOW,
            known_at=NOW,
        ).kind
        is ResponsibilityResolutionKind.VACANCY
    )

    source_version = authority_source(
        sqlite_store,
        case_id=case_id,
        assigning_actor_id=actor_a,
        exact_context=exact_context,
        signature_digest=signature_digest,
        obligation=obligation,
    )
    basis = command(
        case_id=case_id,
        actor_id=actor_a,
        exact_context=exact_context,
        family="assignment-basis",
        key="basis",
        projections=(),
    )
    basis = replace(
        basis,
        projections=(
            ProjectionFact("assignment_basis_records", {"record_id": str(basis.record_id)}),
            ProjectionFact(
                "assignment_basis_versions",
                {
                    "version_id": str(basis.version_id),
                    "record_id": str(basis.record_id),
                    "assigning_actor_id": str(actor_a),
                    "basis_source_version_id": str(source_version),
                    "owning_case_id": str(case_id),
                    "context_digest": exact_context.digest,
                    "allowed_obligation_kinds_json": json.dumps([obligation]),
                    "allowed_case_ids_json": json.dumps([str(case_id)]),
                    "allowed_signature_digests_json": json.dumps([signature_digest]),
                    "limits_json": json.dumps({"max_active_assignments": 2}),
                    "max_active_assignments": 2,
                    "state": "ACTIVE",
                    "effective_from_us": to_epoch_microseconds(NOW),
                    "effective_to_us": None,
                    "recorded_at_us": 0,
                    "predecessor_version_id": None,
                },
            ),
        ),
    )
    svc.commit(basis)

    assignment = command(
        case_id=case_id,
        actor_id=actor_a,
        exact_context=exact_context,
        family="responsibility-assignment",
        key="assignment-a",
        projections=(),
    )
    assignment = replace(
        assignment,
        projections=(
            ProjectionFact(
                "responsibility_assignment_records", {"record_id": str(assignment.record_id)}
            ),
            ProjectionFact(
                "responsibility_assignment_versions",
                {
                    "version_id": str(assignment.version_id),
                    "record_id": str(assignment.record_id),
                    "responsibility_version_id": str(responsibility.version_id),
                    "signature_digest": signature_digest,
                    "actor_id": str(actor_a),
                    "assignment_basis_version_id": str(basis.version_id),
                    "state": "ASSIGNED",
                    "effective_from_us": to_epoch_microseconds(NOW),
                    "effective_to_us": None,
                    "recorded_at_us": to_epoch_microseconds(NOW),
                    "predecessor_version_id": None,
                },
            ),
        ),
    )
    svc.commit(assignment)
    resolution = svc.resolve_responsibility(
        principal_id="principal:slice-a",
        actor_id=str(actor_a),
        owning_case_id=case_id,
        signature_digest=signature_digest,
        effective_at=NOW,
        known_at=NOW,
    )
    assert resolution.kind is ResponsibilityResolutionKind.ONE
    assert resolution.actor_id == str(actor_a)

    work = command(
        case_id=case_id,
        actor_id=actor_a,
        exact_context=exact_context,
        family="case-work",
        key="work-ready",
        projections=(),
    )
    work = replace(
        work,
        projections=(
            ProjectionFact("case_work_records", {"record_id": str(work.record_id)}),
            ProjectionFact(
                "case_work_versions",
                {
                    "version_id": str(work.version_id),
                    "record_id": str(work.record_id),
                    "owning_case_id": str(case_id),
                    "context_digest": exact_context.digest,
                    "responsibility_version_id": str(responsibility.version_id),
                    "assignment_version_id": str(assignment.version_id),
                    "requester_actor_id": str(actor_a),
                    "assignee_actor_id": str(actor_a),
                    "state": "READY",
                    "reason": "complete bounded continuing review",
                    "prerequisites_json": json.dumps([str(responsibility.version_id)]),
                    "expected_result_family": "slice-a-test-governed-result",
                    "due_at_us": None,
                    "result_version_id": None,
                    "return_context_digest": None,
                    "predecessor_version_id": None,
                },
            ),
        ),
    )
    svc.commit(work)

    result_record_id, result_version_id = RecordId.new(), RecordVersionId.new()
    completed = replace(
        work,
        command_id=CommandId.new(),
        idempotency_key="work-completed",
        version_id=RecordVersionId.new(),
        content={"state": "COMPLETED"},
        expected_version_id=work.version_id,
    )
    completed = replace(
        completed,
        projections=(
            ProjectionFact(
                "case_work_versions",
                {
                    **work.projections[1].values,
                    "version_id": str(completed.version_id),
                    "state": "COMPLETED",
                    "result_version_id": str(result_version_id),
                    "return_context_digest": exact_context.digest,
                    "predecessor_version_id": str(work.version_id),
                },
            ),
            ProjectionFact(
                "case_work_result_links",
                {
                    "work_version_id": str(completed.version_id),
                    "result_version_id": str(result_version_id),
                    "return_context_digest": exact_context.digest,
                },
            ),
        ),
    )

    def append_test_result(
        transaction: SliceATransaction, recorded_at: datetime
    ) -> tuple[RecordVersionId, ...]:
        # Explicit test-only governed-result port: no Slice-B domain semantics are invented.
        transaction.add_version(
            FinalizedRecordVersion(
                result_record_id,
                result_version_id,
                "slice-a-test-governed-result",
                f"case:{case_id}",
                canonical_json({"result": "established"}),
                recorded_at,
                EffectiveInterval(NOW),
                str(actor_a),
            )
        )
        transaction.insert_projection(
            "record_version_semantics",
            {
                "version_id": str(result_version_id),
                "contract_key": CONTRACT.key,
                "context_digest": exact_context.digest,
                "consumer_id": "gate8-slice-a-test-result",
                "adapter_key": None,
            },
        )
        return (result_version_id,)

    completed_outcome = svc.commit(completed, extra_writer=append_test_result)
    assert str(result_version_id) in completed_outcome.version_ids
    assert sqlite_store.get_history(work.record_id).relationships

    stale = replace(
        completed,
        command_id=CommandId.new(),
        idempotency_key="work-stale",
        version_id=RecordVersionId.new(),
        content={"state": "CANCELLED"},
    )
    stale = replace(
        stale,
        projections=(
            ProjectionFact(
                "case_work_versions",
                {
                    **work.projections[1].values,
                    "version_id": str(stale.version_id),
                    "state": "CANCELLED",
                    "predecessor_version_id": str(work.version_id),
                },
            ),
        ),
    )
    with pytest.raises(SliceAConflict, match="stale exact predecessor"):
        svc.commit(stale)

    other = replace(
        assignment,
        command_id=CommandId.new(),
        idempotency_key="assignment-b",
        record_id=RecordId.new(),
        version_id=RecordVersionId.new(),
        actor_id=str(actor_a),
    )
    other = replace(
        other,
        projections=(
            ProjectionFact(
                "responsibility_assignment_records", {"record_id": str(other.record_id)}
            ),
            ProjectionFact(
                "responsibility_assignment_versions",
                {
                    **assignment.projections[1].values,
                    "version_id": str(other.version_id),
                    "record_id": str(other.record_id),
                    "actor_id": str(actor_b),
                },
            ),
        ),
    )
    svc.commit(other)
    assert (
        svc.resolve_responsibility(
            principal_id="principal:slice-a",
            actor_id=str(actor_a),
            owning_case_id=case_id,
            signature_digest=signature_digest,
            effective_at=NOW,
            known_at=NOW,
        ).kind
        is ResponsibilityResolutionKind.CONFLICT
    )

    third = replace(
        other,
        command_id=CommandId.new(),
        idempotency_key="assignment-limit-exceeded",
        record_id=RecordId.new(),
        version_id=RecordVersionId.new(),
    )
    third = replace(
        third,
        projections=(
            ProjectionFact(
                "responsibility_assignment_records", {"record_id": str(third.record_id)}
            ),
            ProjectionFact(
                "responsibility_assignment_versions",
                {
                    **other.projections[1].values,
                    "version_id": str(third.version_id),
                    "record_id": str(third.record_id),
                },
            ),
        ),
    )
    before_limit = sqlite_store.count_rows("record_versions")
    with pytest.raises(SliceAConflict, match="LIMIT EXCEEDED"):
        svc.commit(third)
    assert sqlite_store.count_rows("record_versions") == before_limit

    before = sqlite_store.count_rows("record_versions")
    failed = replace(
        responsibility,
        command_id=CommandId.new(),
        idempotency_key="atomic-failure",
        record_id=RecordId.new(),
        version_id=RecordVersionId.new(),
    )
    failed = replace(
        failed,
        projections=(
            ProjectionFact("responsibility_records", {"record_id": str(failed.record_id)}),
            ProjectionFact(
                "responsibility_versions",
                {
                    **responsibility.projections[1].values,
                    "version_id": str(failed.version_id),
                    "record_id": str(failed.record_id),
                },
            ),
        ),
    )
    with pytest.raises(RuntimeError, match="injected"):
        svc.commit(
            failed, failure_injector=lambda _: (_ for _ in ()).throw(RuntimeError("injected"))
        )
    assert sqlite_store.count_rows("record_versions") == before

    with pytest.raises(SliceAConflict, match="IDEMPOTENCY"):
        changed_context = ExactContextSet.create(
            (
                ExactContextMember("owning_case", ContextMemberKind.RECORD, str(case_id)),
                ExactContextMember("purpose", ContextMemberKind.LITERAL, "changed"),
            )
        )
        changed = replace(responsibility, context=changed_context)
        changed = replace(
            changed,
            projections=(
                changed.projections[0],
                ProjectionFact(
                    "responsibility_versions",
                    {
                        **changed.projections[1].values,
                        "context_digest": changed_context.digest,
                        "signature_digest": responsibility_signature(
                            contract=CONTRACT,
                            obligation_kind=ObligationKind(obligation),
                            owning_case_id=case_id,
                            context=changed_context,
                            purpose="continuing-review",
                            use="case-management",
                            scope="exact-case-context",
                        ),
                    },
                ),
            ),
        )
        svc.commit(changed)

    restarted = ResponsibilityWorkService(sqlite_store, FixedClock(NOW), ExactAccess())
    assert (
        restarted.resolve_responsibility(
            principal_id="principal:slice-a",
            actor_id=str(actor_a),
            owning_case_id=case_id,
            signature_digest=signature_digest,
            effective_at=NOW,
            known_at=NOW,
        ).kind
        is ResponsibilityResolutionKind.CONFLICT
    )


def test_access_denial_precedes_composition_and_does_not_mutate(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    case_id, case_version_id = add_case(sqlite_store, "slice-a-hidden")
    actor_id, _ = add_actor(sqlite_store, "slice-a-hidden")
    svc = ResponsibilityWorkService(sqlite_store, FixedClock(NOW), ExactAccess(allowed=False))
    candidate = command(
        case_id=case_id,
        actor_id=actor_id,
        exact_context=context(case_id, case_version_id),
        family="responsibility",
        key="hidden",
        projections=(),
    )
    before = sqlite_store.count_rows("record_versions")
    with pytest.raises(SliceAAccessDenied, match="software access not established"):
        svc.commit(candidate)
    assert sqlite_store.count_rows("record_versions") == before

    responsibility, _ = responsibility_command(
        case_id=case_id,
        actor_id=actor_id,
        exact_context=context(case_id, case_version_id),
        obligation="COORDINATE_CASE",
        key="revoked-at-commit",
    )
    revoked = ResponsibilityWorkService(sqlite_store, FixedClock(NOW), RevokedAtCommitAccess())
    with pytest.raises(SliceAAccessDenied, match="software access not established"):
        revoked.commit(responsibility)
    assert sqlite_store.count_rows("record_versions") == before


def test_assignment_authority_fail_closed_matrix_has_zero_failed_mutation(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    case_id, case_version_id = add_case(sqlite_store, "authority-matrix")
    other_case_id, other_case_version_id = add_case(sqlite_store, "authority-matrix-other")
    assigning_actor, assigning_actor_version = add_actor(sqlite_store, "authority-assigner")
    assigned_actor, _ = add_actor(sqlite_store, "authority-assignee")
    add_role(
        sqlite_store,
        "authority-role-alone",
        assigning_actor,
        role="Case Coordinator",
        target_type=RoleTargetType.CASE,
        target_id=str(case_id),
        case_context_id=case_id,
        accountable=True,
    )
    exact_context = context(case_id, case_version_id)
    other_context = context(other_case_id, other_case_version_id)
    svc = ResponsibilityWorkService(sqlite_store, FixedClock(NOW), ExactAccess())
    responsibility, signature_digest = responsibility_command(
        case_id=case_id,
        actor_id=assigning_actor,
        exact_context=exact_context,
        obligation="COMPLETE_CONTINUING_REVIEW",
        key="matrix-responsibility",
        practical_role="CASE_COORDINATOR",
    )
    svc.commit(responsibility)

    # Practical role plus command access cannot manufacture assignment authority.
    unauthorized_basis = basis_command(
        case_id=case_id,
        assigning_actor_id=assigning_actor,
        exact_context=exact_context,
        source_version_id=assigning_actor_version,
        obligation="COMPLETE_CONTINUING_REVIEW",
        signature_digest=signature_digest,
        key="matrix-role-is-not-authority",
        maximum=1,
    )
    before = sqlite_store.count_rows("record_versions")
    with pytest.raises(SliceAConflict, match="AUTHORITY SOURCE NOT ESTABLISHED"):
        svc.commit(unauthorized_basis)
    assert sqlite_store.count_rows("record_versions") == before

    command_only_basis = basis_command(
        case_id=case_id,
        assigning_actor_id=assigned_actor,
        exact_context=exact_context,
        source_version_id=assigning_actor_version,
        obligation="COMPLETE_CONTINUING_REVIEW",
        signature_digest=signature_digest,
        key="matrix-command-access-is-not-authority",
        maximum=1,
    )
    before = sqlite_store.count_rows("record_versions")
    with pytest.raises(SliceAConflict, match="AUTHORITY SOURCE NOT ESTABLISHED"):
        svc.commit(command_only_basis)
    assert sqlite_store.count_rows("record_versions") == before

    source = authority_source(
        sqlite_store,
        case_id=case_id,
        assigning_actor_id=assigning_actor,
        exact_context=exact_context,
        signature_digest=signature_digest,
        obligation="COMPLETE_CONTINUING_REVIEW",
        maximum=1,
    )
    basis = basis_command(
        case_id=case_id,
        assigning_actor_id=assigning_actor,
        exact_context=exact_context,
        source_version_id=source,
        obligation="COMPLETE_CONTINUING_REVIEW",
        signature_digest=signature_digest,
        key="matrix-valid-basis",
        maximum=1,
    )
    svc.commit(basis)

    wrong_actor = assignment_command(
        case_id=case_id,
        assigning_actor_id=assigned_actor,
        assigned_actor_id=assigned_actor,
        exact_context=exact_context,
        responsibility=responsibility,
        signature_digest=signature_digest,
        basis=basis,
        key="matrix-wrong-assigning-actor",
    )
    before = sqlite_store.count_rows("record_versions")
    with pytest.raises(SliceAConflict, match="NOT AUTHORIZED"):
        svc.commit(wrong_actor)
    assert sqlite_store.count_rows("record_versions") == before

    wrong_case = assignment_command(
        case_id=other_case_id,
        assigning_actor_id=assigning_actor,
        assigned_actor_id=assigned_actor,
        exact_context=other_context,
        responsibility=responsibility,
        signature_digest=signature_digest,
        basis=basis,
        key="matrix-wrong-case",
    )
    before = sqlite_store.count_rows("record_versions")
    with pytest.raises(SliceAConflict, match="AUTHORIZE"):
        svc.commit(wrong_case)
    assert sqlite_store.count_rows("record_versions") == before

    other_responsibility, other_signature = responsibility_command(
        case_id=case_id,
        actor_id=assigning_actor,
        exact_context=exact_context,
        obligation="PRODUCE_VALUE_INPUT",
        key="matrix-other-obligation",
    )
    svc.commit(other_responsibility)
    wrong_kind = assignment_command(
        case_id=case_id,
        assigning_actor_id=assigning_actor,
        assigned_actor_id=assigned_actor,
        exact_context=exact_context,
        responsibility=other_responsibility,
        signature_digest=other_signature,
        basis=basis,
        key="matrix-wrong-kind",
    )
    before = sqlite_store.count_rows("record_versions")
    with pytest.raises(SliceAConflict, match="AUTHORIZE"):
        svc.commit(wrong_kind)
    assert sqlite_store.count_rows("record_versions") == before

    valid = assignment_command(
        case_id=case_id,
        assigning_actor_id=assigning_actor,
        assigned_actor_id=assigned_actor,
        exact_context=exact_context,
        responsibility=responsibility,
        signature_digest=signature_digest,
        basis=basis,
        key="matrix-valid-assignment",
    )
    svc.commit(valid)
    exceeded = assignment_command(
        case_id=case_id,
        assigning_actor_id=assigning_actor,
        assigned_actor_id=assigning_actor,
        exact_context=exact_context,
        responsibility=responsibility,
        signature_digest=signature_digest,
        basis=basis,
        key="matrix-limit-exceeded",
    )
    before = sqlite_store.count_rows("record_versions")
    with pytest.raises(SliceAConflict, match="LIMIT EXCEEDED"):
        svc.commit(exceeded)
    assert sqlite_store.count_rows("record_versions") == before

    successor = basis_command(
        case_id=case_id,
        assigning_actor_id=assigning_actor,
        exact_context=exact_context,
        source_version_id=source,
        obligation="COMPLETE_CONTINUING_REVIEW",
        signature_digest=signature_digest,
        key="matrix-basis-successor",
        maximum=1,
        record_id=basis.record_id,
        expected_version_id=basis.version_id,
    )
    svc.commit(successor)
    stale_basis = assignment_command(
        case_id=case_id,
        assigning_actor_id=assigning_actor,
        assigned_actor_id=assigned_actor,
        exact_context=exact_context,
        responsibility=responsibility,
        signature_digest=signature_digest,
        basis=basis,
        key="matrix-stale-basis",
    )
    before = sqlite_store.count_rows("record_versions")
    with pytest.raises(SliceAConflict, match="STALE OR SUPERSEDED"):
        svc.commit(stale_basis)
    assert sqlite_store.count_rows("record_versions") == before

    withdrawn = basis_command(
        case_id=case_id,
        assigning_actor_id=assigning_actor,
        exact_context=exact_context,
        source_version_id=source,
        obligation="COMPLETE_CONTINUING_REVIEW",
        signature_digest=signature_digest,
        key="matrix-basis-withdrawn",
        maximum=1,
        record_id=basis.record_id,
        expected_version_id=successor.version_id,
        state="WITHDRAWN",
    )
    svc.commit(withdrawn)
    withdrawn_assignment = assignment_command(
        case_id=case_id,
        assigning_actor_id=assigning_actor,
        assigned_actor_id=assigned_actor,
        exact_context=exact_context,
        responsibility=responsibility,
        signature_digest=signature_digest,
        basis=withdrawn,
        key="matrix-withdrawn-basis",
    )
    before = sqlite_store.count_rows("record_versions")
    with pytest.raises(SliceAConflict, match="WITHDRAWN"):
        svc.commit(withdrawn_assignment)
    assert sqlite_store.count_rows("record_versions") == before
