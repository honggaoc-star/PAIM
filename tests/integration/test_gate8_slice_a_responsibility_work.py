from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime

import pytest

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
from tests.integration.test_increment_2_foundation import add_actor, add_case

NOW = utc(2026, 8, 24)
CONTRACT = SemanticContractRef("paim-gate8-slice-a", "1")


class ExactAccess:
    def __init__(self, *, allowed: bool = True) -> None:
        self.allowed = allowed

    def authorize(self, **_: object) -> bool:
        return self.allowed


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


def test_responsibility_work_vertical_proof_replay_restart_and_atomic_failure(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    case_id, case_version_id = add_case(sqlite_store, "slice-a")
    actor_a, actor_a_version = add_actor(sqlite_store, "slice-a-a")
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
                    "practical_role": "REVIEWER",
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
                    "practical_role": "REVIEWER",
                    "owning_case_id": str(case_id),
                    "context_digest": exact_context.digest,
                    "signature_digest": signature_digest,
                },
            ),
        ),
    )
    first = svc.commit(responsibility)
    assert svc.commit(responsibility) == first
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

    # The exact Actor Version is the explicit, bounded policy/basis source for this proof.
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
                    "basis_source_version_id": str(actor_a_version),
                    "allowed_obligation_kinds_json": json.dumps([obligation]),
                    "allowed_case_ids_json": json.dumps([str(case_id)]),
                    "limits_json": "{}",
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
        actor_id=str(actor_b),
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
