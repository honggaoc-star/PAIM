from __future__ import annotations

import json
from dataclasses import replace
from datetime import timedelta

import pytest

from paim.case_continuity import (
    CaseContinuityConflict,
    CaseContinuityService,
    ClosureGuardManifest,
    CommandIdentity,
    ConfigurationSuccessorCommand,
    ConfigurationSuccessorFacts,
    ContinuityStatus,
    DeterminationKind,
    DeterminationOutcome,
    OpenCaseCommand,
    OpeningFacts,
    TransitionCaseCommand,
    TransitionFacts,
)
from paim.integrity import (
    CommandId,
    EffectiveInterval,
    FixedClock,
    RecordId,
    RecordVersionId,
)
from paim.integrity.records import FinalizedRecordVersion, canonical_json
from paim.integrity.semantics import (
    ContextMemberKind,
    ExactContextMember,
    ExactContextSet,
    SemanticContractRef,
)
from paim.practitioner_queries import PractitionerQueryService
from paim.responsibility.models import ObligationKind, responsibility_signature
from paim.responsibility.service import (
    ProjectionFact,
    ResponsibilityWorkService,
    SliceACommand,
    SliceAConflict,
)
from tests.helpers import utc
from tests.integration.test_increment_2_foundation import add_actor

NOW = utc(2026, 8, 25)
RECORDED = NOW + timedelta(days=20)
CONTRACT = SemanticContractRef("paim.case-continuity", "1.0")


class ExactAccess:
    def __init__(self, hidden: frozenset[RecordId] = frozenset()) -> None:
        self.hidden = hidden

    def authorize(self, *, case_id: RecordId, **_: object) -> bool:
        return case_id not in self.hidden


def context(facts: OpeningFacts, use: str) -> ExactContextSet:
    return ExactContextSet.create(
        (
            ExactContextMember("case", ContextMemberKind.RECORD, str(facts.case_id)),
            ExactContextMember(
                "configuration_version",
                ContextMemberKind.VERSION,
                str(facts.configuration_version_id),
            ),
            ExactContextMember("bounded_use", ContextMemberKind.LITERAL, use),
        )
    )


def add_authority(
    sqlite_store: object,
    *,
    actor_id: RecordId,
    case_id: RecordId,
    exact_context: ExactContextSet,
    suffix: str,
    assignment_signature: str | None = None,
    assignment_actor_id: RecordId | None = None,
    assignment_effective: EffectiveInterval | None = None,
) -> RecordVersionId:
    record_id, version_id = RecordId.new(), RecordVersionId.new()
    with sqlite_store.semantic_transaction() as tx:  # type: ignore[attr-defined]
        tx.add_version(
            FinalizedRecordVersion(
                record_id,
                version_id,
                "authority-record",
                f"case:{case_id}",
                canonical_json(
                    {
                        "source": f"bounded-board-{suffix}",
                        "case_continuity_authority": {
                            "actor_id": str(actor_id),
                            "allowed_case_ids": [str(case_id)],
                            "allowed_actions": [
                                "CREATE_OPEN_CASE",
                                "SAME_OR_NEW_CASE",
                                "CASE_CLOSURE",
                                "CASE_REOPENING",
                                "CASE_SUPERSESSION",
                            ],
                            "context_digest": exact_context.digest,
                        },
                        **(
                            {
                                "assignment_authority": {
                                    "assigning_actor_id": str(assignment_actor_id or actor_id),
                                    "allowed_case_ids": [str(case_id)],
                                    "allowed_obligation_kinds": [
                                        ObligationKind.DETERMINE_CASE_CONTINUITY.value
                                    ],
                                    "allowed_signature_digests": [assignment_signature],
                                    "context_digest": exact_context.digest,
                                    "max_active_assignments": 1,
                                    "limits": {
                                        "continuity_actions": [
                                            value.value for value in DeterminationKind
                                        ]
                                    },
                                }
                            }
                            if assignment_signature is not None
                            else {}
                        ),
                    }
                ),
                NOW,
                assignment_effective or EffectiveInterval(NOW),
                str(actor_id),
            )
        )
    return version_id


def opening(
    sqlite_store: object,
    actor_id: RecordId,
    suffix: str,
    *,
    assignment_authority: bool = True,
    assignment_actor_id: RecordId | None = None,
    assignment_effective: EffectiveInterval | None = None,
) -> tuple[OpenCaseCommand, RecordVersionId]:
    facts = OpeningFacts.new()
    exact_context = context(facts, f"bounded-use-{suffix}")
    authority = add_authority(
        sqlite_store,
        actor_id=actor_id,
        case_id=facts.case_id,
        exact_context=exact_context,
        suffix=suffix,
    )
    assignment_signature = responsibility_signature(
        contract=CONTRACT,
        obligation_kind=ObligationKind.DETERMINE_CASE_CONTINUITY,
        owning_case_id=facts.case_id,
        context=exact_context,
        purpose="continuing-case",
        use=f"bounded-use-{suffix}",
        scope=f"Should bounded use {suffix} continue?",
    )
    assignment_source = add_authority(
        sqlite_store,
        actor_id=actor_id,
        case_id=facts.case_id,
        exact_context=exact_context,
        suffix=f"{suffix}-assignment",
        assignment_signature=(assignment_signature if assignment_authority else None),
        assignment_actor_id=assignment_actor_id,
        assignment_effective=assignment_effective,
    )
    command = OpenCaseCommand(
        CommandIdentity(CommandId.new(), "slice-b-open", suffix, "principal:slice-b", actor_id),
        facts,
        CONTRACT,
        exact_context,
        f"Prospective Case {suffix}",
        f"bounded-use-{suffix}",
        f"Should bounded use {suffix} continue?",
        {"system": suffix, "bounded_use": f"bounded-use-{suffix}"},
        "finalized",
        "candidate",
        authority,
        assignment_source,
        NOW,
        NOW,
    )
    # Subsequent accountable continuity determinations bind the exact source of
    # the opening assignment. That source independently carries the bounded
    # continuity authority needed by those determinations.
    return command, assignment_source


def transition(
    opened: OpenCaseCommand,
    authority: RecordVersionId,
    *,
    status_version: RecordVersionId,
    status: ContinuityStatus,
    kind: DeterminationKind,
    outcome: DeterminationOutcome,
    key: str,
    effective_at: object,
    closure: ClosureGuardManifest | None = None,
    successor: RecordId | None = None,
) -> TransitionCaseCommand:
    return TransitionCaseCommand(
        CommandIdentity(
            CommandId.new(),
            "slice-b-transition",
            key,
            "principal:slice-b",
            opened.identity.actor_id,
        ),
        TransitionFacts.new(),
        CONTRACT,
        opened.context,
        opened.facts.case_id,
        opened.facts.status_record_id,
        status_version,
        status,
        kind,
        outcome,
        opened.facts.responsibility_version_id,
        opened.facts.assignment_version_id,
        authority,
        f"accountable {key} determination",
        ("bounded management subject", "exact changed basis"),
        effective_at,  # type: ignore[arg-type]
        effective_at,  # type: ignore[arg-type]
        closure,
        successor,
    )


def add_ready_work(sqlite_store: object, opened: OpenCaseCommand) -> SliceACommand:
    work = SliceACommand(
        CommandId.new(),
        "slice-b-work",
        "ready",
        "principal:slice-b",
        str(opened.identity.actor_id),
        RecordId.new(),
        RecordVersionId.new(),
        "case-work",
        f"case:{opened.facts.case_id}",
        {
            "question": "Resolve the closure preparation obligation.",
            "instruction": "Complete or explicitly dispose this bounded work.",
            "return_path": "Return to the Case continuity task.",
        },
        NOW,
        CONTRACT,
        opened.context,
        opened.facts.case_id,
        "case-work.update",
        (),
    )
    return replace(
        work,
        projections=(
            ProjectionFact("case_work_records", {"record_id": str(work.record_id)}),
            ProjectionFact(
                "case_work_versions",
                {
                    "version_id": str(work.version_id),
                    "record_id": str(work.record_id),
                    "owning_case_id": str(opened.facts.case_id),
                    "context_digest": opened.context.digest,
                    "responsibility_version_id": str(opened.facts.responsibility_version_id),
                    "assignment_version_id": str(opened.facts.assignment_version_id),
                    "requester_actor_id": str(opened.identity.actor_id),
                    "assignee_actor_id": str(opened.identity.actor_id),
                    "state": "READY",
                    "reason": "resolve closure preparation",
                    "prerequisites_json": json.dumps([str(opened.facts.responsibility_version_id)]),
                    "expected_result_family": "case-continuity-determination",
                    "due_at_us": None,
                    "result_version_id": None,
                    "return_context_digest": opened.context.digest,
                    "predecessor_version_id": None,
                },
            ),
        ),
    )


@pytest.mark.parametrize(
    ("suffix", "opening_options", "expected"),
    (
        (
            "continuity-authority-only",
            {"assignment_authority": False},
            "ASSIGNMENT AUTHORITY NOT ESTABLISHED",
        ),
        (
            "wrong-assignment-authority",
            {"assignment_actor_id": RecordId.new()},
            "ASSIGNMENT BASIS EXCEEDS EXACT AUTHORITY SOURCE",
        ),
        (
            "stale-assignment-authority",
            {
                "assignment_effective": EffectiveInterval(
                    NOW - timedelta(days=2), NOW - timedelta(days=1)
                )
            },
            "ASSIGNMENT AUTHORITY SOURCE NOT CURRENT",
        ),
    ),
)
def test_open_case_requires_exact_slice_a_assignment_authority_with_zero_mutation(
    sqlite_store: object,
    suffix: str,
    opening_options: dict[str, object],
    expected: str,
) -> None:
    actor_id, _ = add_actor(sqlite_store, f"slice-b-{suffix}")  # type: ignore[arg-type]
    command, _ = opening(
        sqlite_store,
        actor_id,
        suffix,
        **opening_options,  # type: ignore[arg-type]
    )
    before_versions = sqlite_store.count_rows("record_versions")  # type: ignore[attr-defined]
    before_cases = sqlite_store.count_rows("paim_cases")  # type: ignore[attr-defined]

    with pytest.raises(SliceAConflict, match=expected):
        CaseContinuityService(
            sqlite_store,
            FixedClock(RECORDED),
            ExactAccess(),
        ).open_case(command)  # type: ignore[arg-type]

    assert sqlite_store.count_rows("record_versions") == before_versions  # type: ignore[attr-defined]
    assert sqlite_store.count_rows("paim_cases") == before_cases  # type: ignore[attr-defined]
    with sqlite_store.read_transaction() as tx:  # type: ignore[attr-defined]
        assert not tx.case_exists(command.facts.case_id)
        assert not tx.projection_rows(
            "assignment_basis_versions",
            version_id=str(command.facts.assignment_basis_version_id),
        )
        assert not tx.projection_rows(
            "responsibility_assignment_versions",
            version_id=str(command.facts.assignment_version_id),
        )


def test_open_case_atomically_requires_and_uses_both_exact_authority_sources(
    sqlite_store: object,
) -> None:
    actor_id, _ = add_actor(sqlite_store, "slice-b-exact-authority")  # type: ignore[arg-type]
    command, assignment_authority = opening(sqlite_store, actor_id, "exact-authority")

    outcome = CaseContinuityService(
        sqlite_store,
        FixedClock(RECORDED),
        ExactAccess(),
    ).open_case(command)  # type: ignore[arg-type]

    assert len(outcome.version_ids) == 7
    assert command.assignment_authority_source_version_id == assignment_authority
    assert command.authority_source_version_id != assignment_authority
    with sqlite_store.read_transaction() as tx:  # type: ignore[attr-defined]
        basis = tx.projection_rows(
            "assignment_basis_versions",
            version_id=str(command.facts.assignment_basis_version_id),
        )
        assignment = tx.projection_rows(
            "responsibility_assignment_versions",
            version_id=str(command.facts.assignment_version_id),
        )
    assert basis[0]["basis_source_version_id"] == str(
        command.assignment_authority_source_version_id
    )
    assert assignment[0]["assignment_basis_version_id"] == str(
        command.facts.assignment_basis_version_id
    )


def test_slice_b_vertical_proof_atomic_restart_history_and_no_retarget(
    sqlite_store: object,
) -> None:
    actor_id, _ = add_actor(sqlite_store, "slice-b")  # type: ignore[arg-type]
    access = ExactAccess()
    service = CaseContinuityService(sqlite_store, FixedClock(RECORDED), access)  # type: ignore[arg-type]
    opened, authority = opening(sqlite_store, actor_id, "primary")
    first = service.open_case(opened)
    assert service.open_case(opened) == first
    assert (
        service.select_status(
            principal_id="principal:slice-b",
            actor_id=actor_id,
            case_id=opened.facts.case_id,
            effective_at=NOW,
            known_at=RECORDED + timedelta(seconds=3),
        ).status
        is ContinuityStatus.OPEN
    )

    queries = PractitionerQueryService(sqlite_store, service, access)  # type: ignore[arg-type]
    case_view = queries.case(
        principal_id="principal:slice-b",
        actor_id=actor_id,
        case_id=opened.facts.case_id,
        effective_at=NOW,
        known_at=RECORDED,
    )
    assert case_view.continuity_status is ContinuityStatus.OPEN
    assert case_view.governing_configuration_version_id == opened.facts.configuration_version_id
    assert not case_view.authoritative_master_status_persisted

    work = add_ready_work(sqlite_store, opened)
    work_service = ResponsibilityWorkService(
        sqlite_store,
        FixedClock(RECORDED + timedelta(seconds=1)),
        access,  # type: ignore[arg-type]
    )
    work_service.commit(work)
    home = queries.home(
        principal_id="principal:slice-b",
        actor_id=actor_id,
        candidate_case_ids=(opened.facts.case_id,),
        effective_at=NOW,
        known_at=RECORDED + timedelta(seconds=2),
    )
    assert any(item.work_version_id == work.version_id for item in home.items)
    task = queries.task(
        principal_id="principal:slice-b",
        actor_id=actor_id,
        case_id=opened.facts.case_id,
        work_version_id=work.version_id,
        effective_at=NOW,
        known_at=RECORDED + timedelta(seconds=2),
    )
    assert task.return_path == "Return to the Case continuity task."
    service = CaseContinuityService(
        sqlite_store,
        FixedClock(RECORDED + timedelta(seconds=3)),
        access,  # type: ignore[arg-type]
    )

    close = transition(
        opened,
        authority,
        status_version=opened.facts.status_version_id,
        status=ContinuityStatus.OPEN,
        kind=DeterminationKind.CASE_CLOSURE,
        outcome=DeterminationOutcome.CLOSE,
        key="close",
        effective_at=NOW + timedelta(days=1),
        closure=ClosureGuardManifest(
            False,
            (opened.facts.configuration_version_id,),
            "none unresolved",
            "retain exact history",
        ),
    )
    before = sqlite_store.count_rows("record_versions")  # type: ignore[attr-defined]
    with pytest.raises(CaseContinuityConflict, match="Work remains"):
        service.transition_case(close)
    assert sqlite_store.count_rows("record_versions") == before  # type: ignore[attr-defined]

    cancelled = replace(
        work,
        command_id=CommandId.new(),
        idempotency_key="cancelled",
        version_id=RecordVersionId.new(),
        expected_version_id=work.version_id,
        content={"state": "CANCELLED", "reason": "validly disposed"},
    )
    cancelled = replace(
        cancelled,
        projections=(
            ProjectionFact(
                "case_work_versions",
                {
                    **work.projections[1].values,
                    "version_id": str(cancelled.version_id),
                    "state": "CANCELLED",
                    "predecessor_version_id": str(work.version_id),
                },
            ),
        ),
    )
    ResponsibilityWorkService(
        sqlite_store,
        FixedClock(RECORDED + timedelta(seconds=2)),
        access,  # type: ignore[arg-type]
    ).commit(cancelled)
    close_outcome = service.transition_case(close)
    closed_version = RecordVersionId.parse(close_outcome.version_ids[-1])
    assert (
        service.select_status(
            principal_id="principal:slice-b",
            actor_id=actor_id,
            case_id=opened.facts.case_id,
            effective_at=NOW + timedelta(days=1),
            known_at=RECORDED + timedelta(seconds=3),
        ).status
        is ContinuityStatus.CLOSED
    )

    reopen = transition(
        opened,
        authority,
        status_version=closed_version,
        status=ContinuityStatus.CLOSED,
        kind=DeterminationKind.CASE_REOPENING,
        outcome=DeterminationOutcome.REOPEN_SAME_CASE,
        key="reopen",
        effective_at=NOW + timedelta(days=2),
    )
    reopen_outcome = service.transition_case(reopen)
    reopened_version = RecordVersionId.parse(reopen_outcome.version_ids[-1])
    assert (
        service.select_status(
            principal_id="principal:slice-b",
            actor_id=actor_id,
            case_id=opened.facts.case_id,
            effective_at=NOW + timedelta(days=2),
            known_at=RECORDED + timedelta(seconds=3),
        ).status
        is ContinuityStatus.OPEN
    )
    history = sqlite_store.get_history(opened.facts.status_record_id)  # type: ignore[attr-defined]
    assert len(history.versions) == 3
    assert all(version.content.get("status") != "REOPENED" for version in history.versions)

    successor = ConfigurationSuccessorCommand(
        CommandIdentity(
            CommandId.new(), "slice-b-configuration", "successor", "principal:slice-b", actor_id
        ),
        ConfigurationSuccessorFacts(
            RecordId.new(),
            RecordVersionId.new(),
            opened.facts.configuration_id,
            RecordVersionId.new(),
            RecordVersionId.new(),
            str(RecordId.new()),
        ),
        CONTRACT,
        opened.context,
        opened.facts.case_id,
        opened.facts.status_record_id,
        reopened_version,
        opened.facts.configuration_id,
        opened.facts.configuration_version_id,
        opened.facts.designation_record_id,
        opened.facts.designation_version_id,
        {"system": "primary-v2", "bounded_use": "bounded-use-primary"},
        "finalized",
        "candidate",
        opened.facts.responsibility_version_id,
        opened.facts.assignment_version_id,
        authority,
        "same bounded management subject",
        ("same use", "changed configuration"),
        NOW + timedelta(days=3),
        NOW + timedelta(days=3),
    )
    service.continue_configuration(successor)
    # The durable Work remains bound to its original context and never retargets.
    with sqlite_store.read_transaction() as tx:  # type: ignore[attr-defined]
        old = tx.projection_rows("case_work_versions", version_id=str(work.version_id))[0]
    assert old["context_digest"] == opened.context.digest

    other, _ = opening(sqlite_store, actor_id, "materially-different")
    service.open_case(other)
    new_case = transition(
        opened,
        authority,
        status_version=reopened_version,
        status=ContinuityStatus.OPEN,
        kind=DeterminationKind.SAME_OR_NEW_CASE,
        outcome=DeterminationOutcome.NEW_CASE_REQUIRED,
        key="new-case-required",
        effective_at=NOW + timedelta(days=4),
        successor=other.facts.case_id,
    )
    service.relate_new_case(new_case)
    supersede = transition(
        opened,
        authority,
        status_version=reopened_version,
        status=ContinuityStatus.OPEN,
        kind=DeterminationKind.CASE_SUPERSESSION,
        outcome=DeterminationOutcome.SUPERSEDE_WITH_SUCCESSOR,
        key="supersede",
        effective_at=NOW + timedelta(days=5),
        successor=other.facts.case_id,
    )
    service.transition_case(supersede)
    restarted = CaseContinuityService(sqlite_store, FixedClock(RECORDED), access)  # type: ignore[arg-type]
    assert (
        restarted.select_status(
            principal_id="principal:slice-b",
            actor_id=actor_id,
            case_id=opened.facts.case_id,
            effective_at=NOW + timedelta(days=5),
            known_at=RECORDED + timedelta(seconds=3),
        ).status
        is ContinuityStatus.SUPERSEDED
    )
    prohibited = replace(
        work,
        command_id=CommandId.new(),
        idempotency_key="work-after-supersession",
        record_id=RecordId.new(),
        version_id=RecordVersionId.new(),
        effective_at=NOW + timedelta(days=6),
        expected_version_id=None,
    )
    prohibited = replace(
        prohibited,
        projections=(
            ProjectionFact("case_work_records", {"record_id": str(prohibited.record_id)}),
            ProjectionFact(
                "case_work_versions",
                {
                    **work.projections[1].values,
                    "version_id": str(prohibited.version_id),
                    "record_id": str(prohibited.record_id),
                },
            ),
        ),
    )
    before_terminal = sqlite_store.count_rows("record_versions")  # type: ignore[attr-defined]
    with pytest.raises(SliceAConflict, match="not OPEN"):
        ResponsibilityWorkService(
            sqlite_store,
            FixedClock(RECORDED + timedelta(seconds=4)),
            access,  # type: ignore[arg-type]
        ).commit(prohibited)
    assert sqlite_store.count_rows("record_versions") == before_terminal  # type: ignore[attr-defined]


def test_access_before_composition_hidden_case_does_not_change_visible_result(
    sqlite_store: object,
) -> None:
    actor_id, _ = add_actor(sqlite_store, "slice-b-access")  # type: ignore[arg-type]
    visible, _ = opening(sqlite_store, actor_id, "visible")
    hidden, _ = opening(sqlite_store, actor_id, "hidden")
    initial_access = ExactAccess()
    service = CaseContinuityService(sqlite_store, FixedClock(RECORDED), initial_access)  # type: ignore[arg-type]
    service.open_case(visible)
    service.open_case(hidden)
    filtered = ExactAccess(frozenset({hidden.facts.case_id}))
    queries = PractitionerQueryService(
        sqlite_store,  # type: ignore[arg-type]
        CaseContinuityService(sqlite_store, FixedClock(RECORDED), filtered),  # type: ignore[arg-type]
        filtered,
    )
    one = queries.home(
        principal_id="principal:slice-b",
        actor_id=actor_id,
        candidate_case_ids=(visible.facts.case_id,),
        effective_at=NOW,
        known_at=RECORDED,
    )
    both = queries.home(
        principal_id="principal:slice-b",
        actor_id=actor_id,
        candidate_case_ids=(visible.facts.case_id, hidden.facts.case_id),
        effective_at=NOW,
        known_at=RECORDED,
    )
    assert both == one


def test_only_three_statuses_and_indeterminate_commands_mutate_nothing(
    sqlite_store: object,
) -> None:
    assert {value.value for value in ContinuityStatus} == {"OPEN", "CLOSED", "SUPERSEDED"}
    actor_id, _ = add_actor(sqlite_store, "slice-b-fail")  # type: ignore[arg-type]
    opened, authority = opening(sqlite_store, actor_id, "fail")
    service = CaseContinuityService(sqlite_store, FixedClock(RECORDED), ExactAccess())  # type: ignore[arg-type]
    service.open_case(opened)
    invalid = transition(
        opened,
        authority,
        status_version=opened.facts.status_version_id,
        status=ContinuityStatus.OPEN,
        kind=DeterminationKind.SAME_OR_NEW_CASE,
        outcome=DeterminationOutcome.SAME_CASE,
        key="no-heuristic-transition",
        effective_at=NOW + timedelta(days=1),
    )
    before = sqlite_store.count_rows("record_versions")  # type: ignore[attr-defined]
    with pytest.raises(CaseContinuityConflict, match="does not permit"):
        service.transition_case(invalid)
    assert sqlite_store.count_rows("record_versions") == before  # type: ignore[attr-defined]
    assert (
        service.legacy_lifecycle(
            principal_id="principal:slice-b",
            actor_id=actor_id,
            case_id=RecordId.new(),
        ).limitation
        == "LEGACY PHASES ARE NOT PROSPECTIVE CONTINUITY STATUS"
    )
