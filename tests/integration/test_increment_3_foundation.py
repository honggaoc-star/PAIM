from __future__ import annotations

from dataclasses import dataclass

import pytest

from paim.application import DomainRuleViolation, Increment3ApplicationService
from paim.audit import ActorResolution
from paim.domain import (
    AcceptanceSelectionVersionInput,
    ActorVersionInput,
    AnalyticalInputVersionInput,
    AnalyticalLane,
    ApplicabilityConflict,
    ApplicabilityFound,
    ApplicabilityNotEstablished,
    ApplicabilityOutcome,
    ApplicabilityTargetType,
    AuthorityGapVersionInput,
    AuthorityVersionInput,
    CaseVersionInput,
    CommandMeta,
    ConfigurationMaturity,
    ConfigurationPurpose,
    ConfigurationVersionInput,
    DelegationEffect,
    EvidenceApplicabilityVersionInput,
    EvidenceAttention,
    EvidenceClassification,
    EvidenceVersionInput,
    FitnessOutcome,
    GoverningDesignationInput,
    InputSelectionConflict,
    InputSelectionFound,
    InputSelectionNotEstablished,
    LaneFitnessVersionInput,
    MaterialEvidenceBasisInput,
    RoleAssignmentVersionInput,
    RoleTargetType,
)
from paim.integrity import (
    CommandId,
    EffectiveInterval,
    FixedClock,
    RecordId,
    RecordVersionId,
    RelationshipType,
)
from paim.persistence.sqlite import SQLiteIntegrityStore
from tests.helpers import utc

NOW = utc(2026, 2, 1)
EFFECTIVE = EffectiveInterval(utc(2026, 1, 1))


def meta(key: str) -> CommandMeta:
    return CommandMeta(
        command_id=CommandId.new(),
        idempotency_scope="increment-3-tests",
        idempotency_key=key,
        principal_id="principal:test",
        actor_id="actor:test",
        actor_resolution=ActorResolution.PROVIDED,
    )


@dataclass(frozen=True)
class Context:
    service: Increment3ApplicationService
    case_id: RecordId
    configuration_id: RecordId
    configuration_version_id: RecordVersionId
    assessor_id: RecordId


def context(store: SQLiteIntegrityStore, key: str) -> Context:
    service = Increment3ApplicationService(store, FixedClock(NOW))
    case_id, case_version = RecordId.new(), RecordVersionId.new()
    service.commit_case(
        meta(f"{key}-case"),
        CaseVersionInput(case_id, case_version, key, EFFECTIVE),
    )
    configuration_id, configuration_version = RecordId.new(), RecordVersionId.new()
    service.commit_configuration(
        meta(f"{key}-configuration"),
        ConfigurationVersionInput(
            configuration_id,
            configuration_version,
            case_id,
            ConfigurationMaturity.FINALIZED,
            ConfigurationPurpose.CANDIDATE,
            {"system": key},
            EFFECTIVE,
        ),
    )
    service.commit_governing_designation(
        meta(f"{key}-governing"),
        GoverningDesignationInput(
            RecordId.new(),
            RecordVersionId.new(),
            case_id,
            configuration_version,
            EFFECTIVE,
            accountable_mechanism="configuration-currentness board",
        ),
    )
    assessor_id = RecordId.new()
    service.commit_actor(
        meta(f"{key}-assessor"),
        ActorVersionInput(assessor_id, RecordVersionId.new(), "Assessor", EFFECTIVE),
    )
    return Context(service, case_id, configuration_id, configuration_version, assessor_id)


def evidence(
    ctx: Context,
    key: str,
    *,
    attention: EvidenceAttention = EvidenceAttention.CURRENT,
) -> tuple[RecordId, RecordVersionId]:
    evidence_id, version_id = RecordId.new(), RecordVersionId.new()
    ctx.service.commit_evidence(
        meta(f"{key}-evidence"),
        EvidenceVersionInput(
            evidence_id,
            version_id,
            ctx.case_id,
            ctx.configuration_id,
            ctx.configuration_version_id,
            EvidenceClassification.OBSERVED,
            "source-system:v1",
            {"source_version": "v1", "captured_by": "test"},
            {"measurement": 42},
            utc(2025, 12, 31),
            EFFECTIVE,
            attention,
        ),
    )
    return evidence_id, version_id


def analytical_input(
    ctx: Context,
    key: str,
    lane: AnalyticalLane,
    evidence_version_ids: tuple[RecordVersionId, ...] = (),
) -> tuple[RecordId, RecordVersionId]:
    input_id, version_id = RecordId.new(), RecordVersionId.new()
    ctx.service.commit_analytical_input(
        meta(f"{key}-input"),
        AnalyticalInputVersionInput(
            input_id,
            version_id,
            lane,
            ctx.case_id,
            ctx.configuration_id,
            ctx.configuration_version_id,
            "operating-plan",
            f"{lane.value} finding",
            "bounded-scope",
            ("known uncertainty",),
            f"{lane.value} implication",
            {"method": "independent-lane-analysis"},
            evidence_version_ids,
            EFFECTIVE,
        ),
    )
    ctx.service.mark_input_ready(
        meta(f"{key}-ready"),
        input_version_id=version_id,
        effective_at=EFFECTIVE.start,
        rationale="analytical review complete",
    )
    return input_id, version_id


def applicability(
    ctx: Context,
    key: str,
    evidence_id: RecordId,
    evidence_version_id: RecordVersionId,
    input_id: RecordId,
    input_version_id: RecordVersionId,
    lane: AnalyticalLane,
    outcome: ApplicabilityOutcome = ApplicabilityOutcome.APPLICABLE,
    *,
    assessed_scope: str = "bounded-scope",
    conditions: tuple[str, ...] = (),
    limitations: tuple[str, ...] = (),
    displaced: tuple[RecordVersionId, ...] = (),
) -> tuple[RecordId, RecordVersionId]:
    applicability_id, version_id = RecordId.new(), RecordVersionId.new()
    target_type = (
        ApplicabilityTargetType.VALUE_INPUT_VERSION
        if lane is AnalyticalLane.VALUE
        else ApplicabilityTargetType.RISK_INPUT_VERSION
    )
    ctx.service.commit_evidence_applicability(
        meta(f"{key}-applicability"),
        EvidenceApplicabilityVersionInput(
            applicability_id,
            version_id,
            evidence_id,
            evidence_version_id,
            target_type,
            str(input_id),
            input_version_id,
            "operating-plan",
            assessed_scope,
            ctx.case_id,
            ctx.configuration_id,
            ctx.configuration_version_id,
            outcome,
            conditions,
            limitations,
            "bounded assessor judgment",
            ctx.assessor_id,
            None,
            "evidence-applicability board",
            EFFECTIVE,
            displaced_applicability_version_ids=displaced,
        ),
    )
    return applicability_id, version_id


def accept(
    ctx: Context,
    key: str,
    lane: AnalyticalLane,
    input_id: RecordId,
    input_version_id: RecordVersionId,
    *,
    use_context: str = "integration-path-a",
    evidence_basis: tuple[tuple[RecordVersionId, RecordVersionId], ...] = (),
) -> RecordVersionId:
    fitness_id, fitness_version = RecordId.new(), RecordVersionId.new()
    material = tuple(
        MaterialEvidenceBasisInput(
            evidence_version_id,
            applicability_version_id,
            "finding-support",
            True,
            "bounded-scope",
        )
        for evidence_version_id, applicability_version_id in evidence_basis
    )
    ctx.service.commit_lane_fitness(
        meta(f"{key}-fitness"),
        LaneFitnessVersionInput(
            fitness_id,
            fitness_version,
            lane,
            input_version_id,
            ctx.case_id,
            ctx.configuration_id,
            ctx.configuration_version_id,
            use_context,
            "operating-plan",
            FitnessOutcome.SUPPORTABLE,
            "bounded evidence remains supportable",
            None,
            False,
            None,
            "lane-fitness board",
            material,
            EFFECTIVE,
        ),
    )
    acceptance_id, acceptance_version = RecordId.new(), RecordVersionId.new()
    ctx.service.commit_acceptance_selection(
        meta(f"{key}-acceptance"),
        AcceptanceSelectionVersionInput(
            acceptance_id,
            acceptance_version,
            lane,
            input_id,
            input_version_id,
            ctx.case_id,
            ctx.configuration_id,
            ctx.configuration_version_id,
            use_context,
            "operating-plan",
            "accepted for bounded use",
            None,
            "lane-acceptance board",
            fitness_version,
            tuple(item[1] for item in evidence_basis),
            EFFECTIVE,
        ),
    )
    return acceptance_version


def test_evidence_authority_history_and_provenance_are_immutable(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    ctx = context(sqlite_store, "records")
    evidence_id, first = evidence(ctx, "records")
    second = RecordVersionId.new()
    ctx.service.commit_evidence(
        meta("records-evidence-correction"),
        EvidenceVersionInput(
            evidence_id,
            second,
            ctx.case_id,
            ctx.configuration_id,
            ctx.configuration_version_id,
            EvidenceClassification.OBSERVED,
            "source-system:v2",
            {"source_version": "v2"},
            {"measurement": 43},
            utc(2026, 1, 15),
            EffectiveInterval(utc(2026, 1, 15)),
            expected_version_id=first,
            relationship_type=RelationshipType.CORRECTION,
            relationship_reason="source correction",
        ),
    )
    history = sqlite_store.get_history(evidence_id)
    assert {item.version_id for item in history.versions} == {first, second}
    assert sqlite_store.get_version(first).content["measurement"] == 42  # type: ignore[union-attr]
    assert sqlite_store.get_version(second).content["provenance"] == {  # type: ignore[union-attr]
        "source_version": "v2"
    }

    authority_id, authority_version = RecordId.new(), RecordVersionId.new()
    ctx.service.commit_authority_record(
        meta("records-authority"),
        AuthorityVersionInput(
            authority_id,
            authority_version,
            ctx.case_id,
            ctx.configuration_id,
            ctx.configuration_version_id,
            "policy",
            "policy-register:v7",
            {"register_version": "v7"},
            "bounded-scope",
            "approval required",
            {"clause": "7.2"},
            EFFECTIVE,
            (first,),
        ),
    )
    gap_id, gap_version = RecordId.new(), RecordVersionId.new()
    ctx.service.commit_authority_gap(
        meta("records-gap"),
        AuthorityGapVersionInput(
            gap_id,
            gap_version,
            ctx.case_id,
            ctx.configuration_id,
            ctx.configuration_version_id,
            "Q-1",
            "Who may approve the exception?",
            "bounded-scope",
            "authority not established",
            {"policy_version": "v7"},
            EFFECTIVE,
            (first,),
        ),
    )
    assert sqlite_store.get_version(authority_version).family == "authority-record"  # type: ignore[union-attr]
    assert sqlite_store.get_version(gap_version).content["question_id"] == "Q-1"  # type: ignore[union-attr]


def test_applicability_exact_context_outcomes_conflict_and_history(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    ctx = context(sqlite_store, "applicability")
    evidence_id, evidence_version = evidence(ctx, "applicability")
    input_id, input_version = analytical_input(
        ctx, "applicability", AnalyticalLane.VALUE, (evidence_version,)
    )
    outcomes = tuple(ApplicabilityOutcome)
    first_applicability: RecordVersionId | None = None
    for index, outcome in enumerate(outcomes):
        scope = f"scope-{index}"
        conditional = outcome in {
            ApplicabilityOutcome.CONDITIONALLY_APPLICABLE,
            ApplicabilityOutcome.PARTIALLY_APPLICABLE,
        }
        _, version = applicability(
            ctx,
            f"applicability-{index}",
            evidence_id,
            evidence_version,
            input_id,
            input_version,
            AnalyticalLane.VALUE,
            outcome,
            assessed_scope=scope,
            conditions=("inside scope",) if conditional else (),
            limitations=("not beyond scope",) if conditional else (),
        )
        if index == 0:
            first_applicability = version
        selected = ctx.service.select_evidence_applicability(
            evidence_version_id=evidence_version,
            target_type=ApplicabilityTargetType.VALUE_INPUT_VERSION,
            target_id=str(input_id),
            target_version_id=input_version,
            purpose="operating-plan",
            assessed_scope=scope,
            effective_at=EFFECTIVE.start,
        )
        assert selected == ApplicabilityFound(version)

    assert isinstance(
        ctx.service.select_evidence_applicability(
            evidence_version_id=evidence_version,
            target_type=ApplicabilityTargetType.VALUE_INPUT_VERSION,
            target_id=str(input_id),
            target_version_id=RecordVersionId.new(),
            purpose="operating-plan",
            assessed_scope="scope-0",
            effective_at=EFFECTIVE.start,
        ),
        ApplicabilityNotEstablished,
    )
    _, competing = applicability(
        ctx,
        "applicability-conflict",
        evidence_id,
        evidence_version,
        input_id,
        input_version,
        AnalyticalLane.VALUE,
        assessed_scope="scope-0",
    )
    conflict = ctx.service.select_evidence_applicability(
        evidence_version_id=evidence_version,
        target_type=ApplicabilityTargetType.VALUE_INPUT_VERSION,
        target_id=str(input_id),
        target_version_id=input_version,
        purpose="operating-plan",
        assessed_scope="scope-0",
        effective_at=EFFECTIVE.start,
    )
    assert isinstance(conflict, ApplicabilityConflict)
    assert competing in conflict.applicability_version_ids
    assert first_applicability is not None
    _, resolution = applicability(
        ctx,
        "applicability-resolution",
        evidence_id,
        evidence_version,
        input_id,
        input_version,
        AnalyticalLane.VALUE,
        assessed_scope="scope-0",
        displaced=(first_applicability, competing),
    )
    assert ctx.service.select_evidence_applicability(
        evidence_version_id=evidence_version,
        target_type=ApplicabilityTargetType.VALUE_INPUT_VERSION,
        target_id=str(input_id),
        target_version_id=input_version,
        purpose="operating-plan",
        assessed_scope="scope-0",
        effective_at=EFFECTIVE.start,
    ) == ApplicabilityFound(resolution)
    assert sqlite_store.get_version(first_applicability) is not None
    assert sqlite_store.get_version(competing) is not None


def test_ready_candidates_are_not_selected_and_value_risk_remain_independent(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    ctx = context(sqlite_store, "independent")
    value_a = analytical_input(ctx, "value-a", AnalyticalLane.VALUE)
    analytical_input(ctx, "value-b", AnalyticalLane.VALUE)
    risk = analytical_input(ctx, "risk", AnalyticalLane.RISK)
    assert isinstance(
        ctx.service.select_input(
            lane=AnalyticalLane.VALUE,
            configuration_version_id=ctx.configuration_version_id,
            use_context="integration-path-a",
            purpose="operating-plan",
            effective_at=EFFECTIVE.start,
        ),
        InputSelectionNotEstablished,
    )
    accept(ctx, "risk", AnalyticalLane.RISK, *risk)
    assert isinstance(
        ctx.service.select_input(
            lane=AnalyticalLane.RISK,
            configuration_version_id=ctx.configuration_version_id,
            use_context="integration-path-a",
            purpose="operating-plan",
            effective_at=EFFECTIVE.start,
        ),
        InputSelectionFound,
    )
    assert isinstance(
        ctx.service.select_input(
            lane=AnalyticalLane.VALUE,
            configuration_version_id=ctx.configuration_version_id,
            use_context="integration-path-a",
            purpose="operating-plan",
            effective_at=EFFECTIVE.start,
        ),
        InputSelectionNotEstablished,
    )
    assert value_a != risk


def test_acceptance_atomic_freeze_reuse_conflict_and_withdrawal(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    ctx = context(sqlite_store, "selection")
    first = analytical_input(ctx, "selection-first", AnalyticalLane.VALUE)
    first_acceptance = accept(ctx, "selection-first", AnalyticalLane.VALUE, *first)
    selected = ctx.service.select_input(
        lane=AnalyticalLane.VALUE,
        configuration_version_id=ctx.configuration_version_id,
        use_context="integration-path-a",
        purpose="operating-plan",
        effective_at=EFFECTIVE.start,
    )
    assert selected == InputSelectionFound(first[1], first_acceptance)

    later_use = accept(
        ctx,
        "selection-reuse",
        AnalyticalLane.VALUE,
        *first,
        use_context="integration-path-b",
    )
    assert ctx.service.select_input(
        lane=AnalyticalLane.VALUE,
        configuration_version_id=ctx.configuration_version_id,
        use_context="integration-path-b",
        purpose="operating-plan",
        effective_at=EFFECTIVE.start,
    ) == InputSelectionFound(first[1], later_use)

    second = analytical_input(ctx, "selection-second", AnalyticalLane.VALUE)
    with pytest.raises(DomainRuleViolation, match="competitors require explicit"):
        accept(ctx, "selection-second-blocked", AnalyticalLane.VALUE, *second)

    ctx.service.change_acceptance_eligibility(
        meta("selection-withdraw"),
        acceptance_version_id=first_acceptance,
        new_status="withdrawn",
        effective_at=utc(2026, 1, 20),
        rationale="withdraw before handoff",
    )
    assert isinstance(
        ctx.service.select_input(
            lane=AnalyticalLane.VALUE,
            configuration_version_id=ctx.configuration_version_id,
            use_context="integration-path-a",
            purpose="operating-plan",
            effective_at=utc(2026, 1, 21),
        ),
        InputSelectionNotEstablished,
    )
    historical = ctx.service.select_input(
        lane=AnalyticalLane.VALUE,
        configuration_version_id=ctx.configuration_version_id,
        use_context="integration-path-a",
        purpose="operating-plan",
        effective_at=utc(2026, 1, 10),
    )
    assert historical == InputSelectionFound(first[1], first_acceptance)


def test_material_fitness_attention_scope_indeterminate_and_handoff(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    ctx = context(sqlite_store, "handoff")
    evidence_id, evidence_version = evidence(ctx, "handoff")
    value = analytical_input(ctx, "handoff-value", AnalyticalLane.VALUE, (evidence_version,))
    _, value_app = applicability(
        ctx,
        "handoff-value",
        evidence_id,
        evidence_version,
        *value,
        AnalyticalLane.VALUE,
    )
    accept(
        ctx,
        "handoff-value",
        AnalyticalLane.VALUE,
        *value,
        evidence_basis=((evidence_version, value_app),),
    )
    blocked = ctx.service.analytical_handoff_readiness(
        case_id=ctx.case_id,
        use_context="integration-path-a",
        purpose="operating-plan",
        effective_at=EFFECTIVE.start,
    )
    assert not blocked.eligible
    assert "INPUT SELECTION NOT ESTABLISHED" in blocked.diagnostics

    risk = analytical_input(ctx, "handoff-risk", AnalyticalLane.RISK, (evidence_version,))
    _, risk_app = applicability(
        ctx,
        "handoff-risk",
        evidence_id,
        evidence_version,
        *risk,
        AnalyticalLane.RISK,
    )
    accept(
        ctx,
        "handoff-risk",
        AnalyticalLane.RISK,
        *risk,
        evidence_basis=((evidence_version, risk_app),),
    )
    ready = ctx.service.analytical_handoff_readiness(
        case_id=ctx.case_id,
        use_context="integration-path-a",
        purpose="operating-plan",
        effective_at=EFFECTIVE.start,
    )
    assert ready.eligible
    assert isinstance(ready.value_selection, InputSelectionFound)
    assert isinstance(ready.risk_selection, InputSelectionFound)

    stale_evidence_id, stale_evidence_version = evidence(
        ctx, "stale", attention=EvidenceAttention.REFRESH_REQUIRED
    )
    stale_input = analytical_input(ctx, "stale", AnalyticalLane.VALUE, (stale_evidence_version,))
    _, stale_app = applicability(
        ctx,
        "stale",
        stale_evidence_id,
        stale_evidence_version,
        *stale_input,
        AnalyticalLane.VALUE,
    )
    with pytest.raises(DomainRuleViolation, match="REFRESH REQUIRED"):
        accept(
            ctx,
            "stale",
            AnalyticalLane.VALUE,
            *stale_input,
            use_context="stale-use",
            evidence_basis=((stale_evidence_version, stale_app),),
        )


def test_acceptance_conflict_has_no_implicit_winner(sqlite_store: SQLiteIntegrityStore) -> None:
    ctx = context(sqlite_store, "conflict")
    first = analytical_input(ctx, "conflict-first", AnalyticalLane.VALUE)
    first_acceptance = accept(ctx, "conflict-first", AnalyticalLane.VALUE, *first)
    second = analytical_input(ctx, "conflict-second", AnalyticalLane.VALUE)
    # Disposition of the competing first candidate permits the second acceptance; it does not
    # silently withdraw the already-current first Acceptance Version.
    from paim.domain import CandidateDisposition, CandidateDispositionVersionInput

    ctx.service.commit_candidate_disposition(
        meta("conflict-disposition"),
        CandidateDispositionVersionInput(
            RecordId.new(),
            RecordVersionId.new(),
            first[1],
            AnalyticalLane.VALUE,
            ctx.configuration_version_id,
            "integration-path-a",
            "operating-plan",
            CandidateDisposition.NON_SELECTED,
            "alternative retained",
            EFFECTIVE,
        ),
    )
    second_acceptance = accept(ctx, "conflict-second", AnalyticalLane.VALUE, *second)
    selection = ctx.service.select_input(
        lane=AnalyticalLane.VALUE,
        configuration_version_id=ctx.configuration_version_id,
        use_context="integration-path-a",
        purpose="operating-plan",
        effective_at=EFFECTIVE.start,
    )
    assert isinstance(selection, InputSelectionConflict)
    assert selection.acceptance_version_ids == {first_acceptance, second_acceptance}


def test_exact_accountability_and_atomic_acceptance_rollback(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    ctx = context(sqlite_store, "accountability")
    evidence_id, evidence_version = evidence(ctx, "accountability")
    value = analytical_input(ctx, "accountability", AnalyticalLane.VALUE, (evidence_version,))
    unrelated_case = RecordId.new()
    ctx.service.commit_case(
        meta("accountability-unrelated-case"),
        CaseVersionInput(
            unrelated_case,
            RecordVersionId.new(),
            "Unrelated case",
            EFFECTIVE,
        ),
    )
    role_id, role_version = RecordId.new(), RecordVersionId.new()
    ctx.service.commit_role_assignment(
        meta("accountability-unrelated-role"),
        RoleAssignmentVersionInput(
            role_id,
            role_version,
            ctx.assessor_id,
            "case analyst",
            RoleTargetType.CASE,
            str(unrelated_case),
            unrelated_case,
            True,
            "analysis",
            DelegationEffect.NONE,
            None,
            EFFECTIVE,
        ),
    )
    with pytest.raises(DomainRuleViolation):
        ctx.service.commit_evidence_applicability(
            meta("accountability-wrong-scope"),
            EvidenceApplicabilityVersionInput(
                RecordId.new(),
                RecordVersionId.new(),
                evidence_id,
                evidence_version,
                ApplicabilityTargetType.VALUE_INPUT_VERSION,
                str(value[0]),
                value[1],
                "operating-plan",
                "bounded-scope",
                ctx.case_id,
                ctx.configuration_id,
                ctx.configuration_version_id,
                ApplicabilityOutcome.APPLICABLE,
                (),
                (),
                "wrong accountability scope",
                ctx.assessor_id,
                role_version,
                None,
                EFFECTIVE,
            ),
        )

    exact_version = RecordVersionId.new()
    ctx.service.commit_role_assignment(
        meta("accountability-exact-configuration-role"),
        RoleAssignmentVersionInput(
            RecordId.new(),
            exact_version,
            ctx.assessor_id,
            "Applicability Owner",
            RoleTargetType.CONFIGURATION,
            str(ctx.configuration_id),
            ctx.case_id,
            True,
            "applicability-accountability",
            DelegationEffect.NONE,
            None,
            EFFECTIVE,
        ),
    )
    ctx.service.commit_evidence_applicability(
        meta("accountability-exact-valid"),
        EvidenceApplicabilityVersionInput(
            RecordId.new(),
            RecordVersionId.new(),
            evidence_id,
            evidence_version,
            ApplicabilityTargetType.VALUE_INPUT_VERSION,
            str(value[0]),
            value[1],
            "operating-plan",
            "exact-accountability-scope",
            ctx.case_id,
            ctx.configuration_id,
            ctx.configuration_version_id,
            ApplicabilityOutcome.APPLICABLE,
            (),
            (),
            "exact Configuration assignment applies",
            ctx.assessor_id,
            exact_version,
            None,
            EFFECTIVE,
        ),
    )
    ctx.service.commit_role_assignment(
        meta("accountability-broad-case-role"),
        RoleAssignmentVersionInput(
            RecordId.new(),
            RecordVersionId.new(),
            ctx.assessor_id,
            "Applicability Owner",
            RoleTargetType.CASE,
            str(ctx.case_id),
            ctx.case_id,
            True,
            "applicability-accountability",
            DelegationEffect.NONE,
            None,
            EFFECTIVE,
        ),
    )
    with pytest.raises(DomainRuleViolation, match="conflicting target-context"):
        ctx.service.commit_evidence_applicability(
            meta("accountability-broad-narrow-conflict"),
            EvidenceApplicabilityVersionInput(
                RecordId.new(),
                RecordVersionId.new(),
                evidence_id,
                evidence_version,
                ApplicabilityTargetType.VALUE_INPUT_VERSION,
                str(value[0]),
                value[1],
                "operating-plan",
                "conflict-accountability-scope",
                ctx.case_id,
                ctx.configuration_id,
                ctx.configuration_version_id,
                ApplicabilityOutcome.APPLICABLE,
                (),
                (),
                "Case and Configuration accountability conflict",
                ctx.assessor_id,
                exact_version,
                None,
                EFFECTIVE,
            ),
        )

    fitness_id, fitness_version = RecordId.new(), RecordVersionId.new()
    ctx.service.commit_lane_fitness(
        meta("accountability-fitness"),
        LaneFitnessVersionInput(
            fitness_id,
            fitness_version,
            AnalyticalLane.VALUE,
            value[1],
            ctx.case_id,
            ctx.configuration_id,
            ctx.configuration_version_id,
            "vacant-use",
            "operating-plan",
            FitnessOutcome.SUPPORTABLE,
            "no material evidence declared for this bounded test",
            None,
            False,
            None,
            "lane-fitness board",
            (),
            EFFECTIVE,
        ),
    )
    before = sqlite_store.count_rows("input_acceptance_versions")
    with pytest.raises(DomainRuleViolation, match="exactly one accountable"):
        ctx.service.commit_acceptance_selection(
            meta("accountability-vacant-acceptance"),
            AcceptanceSelectionVersionInput(
                RecordId.new(),
                RecordVersionId.new(),
                AnalyticalLane.VALUE,
                value[0],
                value[1],
                ctx.case_id,
                ctx.configuration_id,
                ctx.configuration_version_id,
                "vacant-use",
                "operating-plan",
                "must roll back",
                None,
                None,
                fitness_version,
                (),
                EFFECTIVE,
            ),
        )
    assert sqlite_store.count_rows("input_acceptance_versions") == before
    assert isinstance(
        ctx.service.select_input(
            lane=AnalyticalLane.VALUE,
            configuration_version_id=ctx.configuration_version_id,
            use_context="vacant-use",
            purpose="operating-plan",
            effective_at=EFFECTIVE.start,
        ),
        InputSelectionNotEstablished,
    )


def test_authority_gap_question_applicability_is_exact_and_reconstructable(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    ctx = context(sqlite_store, "gap-question")
    evidence_id, evidence_version = evidence(ctx, "gap-question")
    gap_id, gap_version = RecordId.new(), RecordVersionId.new()
    ctx.service.commit_authority_gap(
        meta("gap-question-record"),
        AuthorityGapVersionInput(
            gap_id,
            gap_version,
            ctx.case_id,
            ctx.configuration_id,
            ctx.configuration_version_id,
            "AUTH-Q-17",
            "Which authority controls this bounded use?",
            "privacy-authority",
            "authority remains unresolved",
            {"source": "policy register"},
            EFFECTIVE,
        ),
    )
    first_id, first_version = RecordId.new(), RecordVersionId.new()
    ctx.service.commit_evidence_applicability(
        meta("gap-question-first"),
        EvidenceApplicabilityVersionInput(
            first_id,
            first_version,
            evidence_id,
            evidence_version,
            ApplicabilityTargetType.AUTHORITY_GAP,
            "AUTH-Q-17",
            None,
            "authority-resolution",
            "privacy-authority",
            ctx.case_id,
            ctx.configuration_id,
            ctx.configuration_version_id,
            ApplicabilityOutcome.APPLICABLE,
            (),
            (),
            "evidence bears on the exact authority question",
            ctx.assessor_id,
            None,
            "authority-applicability board",
            EFFECTIVE,
        ),
    )
    assert ctx.service.select_evidence_applicability(
        evidence_version_id=evidence_version,
        target_type=ApplicabilityTargetType.AUTHORITY_GAP,
        target_id="AUTH-Q-17",
        target_version_id=None,
        purpose="authority-resolution",
        assessed_scope="privacy-authority",
        effective_at=EFFECTIVE.start,
        case_id=ctx.case_id,
        configuration_version_id=ctx.configuration_version_id,
    ) == ApplicabilityFound(first_version)
    assert isinstance(
        ctx.service.select_evidence_applicability(
            evidence_version_id=evidence_version,
            target_type=ApplicabilityTargetType.AUTHORITY_GAP,
            target_id="AUTH-Q-18",
            target_version_id=None,
            purpose="authority-resolution",
            assessed_scope="privacy-authority",
            effective_at=EFFECTIVE.start,
            case_id=ctx.case_id,
            configuration_version_id=ctx.configuration_version_id,
        ),
        ApplicabilityNotEstablished,
    )
    assert isinstance(
        ctx.service.select_evidence_applicability(
            evidence_version_id=evidence_version,
            target_type=ApplicabilityTargetType.AUTHORITY_GAP,
            target_id="AUTH-Q-17",
            target_version_id=None,
            purpose="authority-resolution",
            assessed_scope="privacy-authority",
            effective_at=EFFECTIVE.start,
            case_id=RecordId.new(),
            configuration_version_id=RecordVersionId.new(),
        ),
        ApplicabilityNotEstablished,
    )

    later = Increment3ApplicationService(sqlite_store, FixedClock(utc(2026, 3, 1)))
    second_version = RecordVersionId.new()
    later.commit_evidence_applicability(
        meta("gap-question-correction"),
        EvidenceApplicabilityVersionInput(
            first_id,
            second_version,
            evidence_id,
            evidence_version,
            ApplicabilityTargetType.AUTHORITY_GAP,
            "AUTH-Q-17",
            None,
            "authority-resolution",
            "privacy-authority",
            ctx.case_id,
            ctx.configuration_id,
            ctx.configuration_version_id,
            ApplicabilityOutcome.CONDITIONALLY_APPLICABLE,
            ("policy interpretation confirmed",),
            ("no broader authority inference",),
            "corrected bounded judgment",
            ctx.assessor_id,
            None,
            "authority-applicability board",
            EFFECTIVE,
            expected_version_id=first_version,
            relationship_type=RelationshipType.CORRECTION,
            relationship_reason="correct authority-question assessment",
        ),
    )
    assert later.select_evidence_applicability(
        evidence_version_id=evidence_version,
        target_type=ApplicabilityTargetType.AUTHORITY_GAP,
        target_id="AUTH-Q-17",
        target_version_id=None,
        purpose="authority-resolution",
        assessed_scope="privacy-authority",
        effective_at=EFFECTIVE.start,
        known_at=utc(2026, 2, 15),
        case_id=ctx.case_id,
        configuration_version_id=ctx.configuration_version_id,
    ) == ApplicabilityFound(first_version)
    assert later.select_evidence_applicability(
        evidence_version_id=evidence_version,
        target_type=ApplicabilityTargetType.AUTHORITY_GAP,
        target_id="AUTH-Q-17",
        target_version_id=None,
        purpose="authority-resolution",
        assessed_scope="privacy-authority",
        effective_at=EFFECTIVE.start,
        case_id=ctx.case_id,
        configuration_version_id=ctx.configuration_version_id,
    ) == ApplicabilityFound(second_version)
    assert sqlite_store.get_version(first_version) is not None


def test_non_configuration_authority_applicability_uses_typed_accountability(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    ctx = context(sqlite_store, "authority-accountability")
    evidence_id, evidence_version = evidence(ctx, "authority-accountability")
    authority_id, authority_version = RecordId.new(), RecordVersionId.new()
    ctx.service.commit_authority_record(
        meta("authority-accountability-record"),
        AuthorityVersionInput(
            authority_id,
            authority_version,
            None,
            None,
            None,
            "policy",
            "enterprise-policy:v3",
            {"policy_version": "v3"},
            "privacy-domain",
            "privacy review required",
            {"clause": "P-12"},
            EFFECTIVE,
        ),
    )

    exact_id, exact_version = RecordId.new(), RecordVersionId.new()
    ctx.service.commit_role_assignment(
        meta("authority-accountability-exact-role"),
        RoleAssignmentVersionInput(
            exact_id,
            exact_version,
            ctx.assessor_id,
            "Authority Owner",
            RoleTargetType.AUTHORITY_DOMAIN,
            "privacy-domain",
            None,
            True,
            "authority-accountability",
            DelegationEffect.NONE,
            None,
            EFFECTIVE,
        ),
    )
    applicability_id, applicability_version = RecordId.new(), RecordVersionId.new()
    ctx.service.commit_evidence_applicability(
        meta("authority-accountability-valid"),
        EvidenceApplicabilityVersionInput(
            applicability_id,
            applicability_version,
            evidence_id,
            evidence_version,
            ApplicabilityTargetType.AUTHORITY_RECORD_VERSION,
            str(authority_id),
            authority_version,
            "authority-maintenance",
            "privacy-domain",
            None,
            None,
            None,
            ApplicabilityOutcome.APPLICABLE,
            (),
            (),
            "exact authority-domain accountability",
            ctx.assessor_id,
            exact_version,
            None,
            EFFECTIVE,
        ),
    )
    assert ctx.service.select_evidence_applicability(
        evidence_version_id=evidence_version,
        target_type=ApplicabilityTargetType.AUTHORITY_RECORD_VERSION,
        target_id=str(authority_id),
        target_version_id=authority_version,
        purpose="authority-maintenance",
        assessed_scope="privacy-domain",
        effective_at=EFFECTIVE.start,
    ) == ApplicabilityFound(applicability_version)

    unrelated_version = RecordVersionId.new()
    ctx.service.commit_role_assignment(
        meta("authority-accountability-unrelated-role"),
        RoleAssignmentVersionInput(
            RecordId.new(),
            unrelated_version,
            ctx.assessor_id,
            "Authority Owner",
            RoleTargetType.AUTHORITY_DOMAIN,
            "security-domain",
            None,
            True,
            "authority-accountability",
            DelegationEffect.NONE,
            None,
            EFFECTIVE,
        ),
    )
    with pytest.raises(DomainRuleViolation, match="target-context accountability"):
        ctx.service.commit_evidence_applicability(
            meta("authority-accountability-unrelated-rejected"),
            EvidenceApplicabilityVersionInput(
                RecordId.new(),
                RecordVersionId.new(),
                evidence_id,
                evidence_version,
                ApplicabilityTargetType.AUTHORITY_RECORD_VERSION,
                str(authority_id),
                authority_version,
                "authority-maintenance",
                "unrelated-check",
                None,
                None,
                None,
                ApplicabilityOutcome.APPLICABLE,
                (),
                (),
                "unrelated assignment must not authorize",
                ctx.assessor_id,
                unrelated_version,
                None,
                EFFECTIVE,
            ),
        )
