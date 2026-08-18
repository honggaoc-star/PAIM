from __future__ import annotations

from dataclasses import dataclass, replace

import pytest

from paim.application import DomainRuleViolation, Increment4ApplicationService
from paim.domain import (
    ActorVersionInput,
    AnalyticalLane,
    AuthorityGapVersionInput,
    AuthorityVersionInput,
    AuthorizedDecisionFound,
    BoundaryClauseEffect,
    BoundaryClauseInput,
    BoundaryComparisonOutcome,
    BoundaryDeterminationVersionInput,
    BoundaryEvaluationOutcome,
    BoundarySnapshotVersionInput,
    BoundaryVerificationMode,
    BoundedProceedVersionInput,
    CaseLifecycleState,
    CaseVersionInput,
    ConfigurationMaturity,
    ConfigurationPurpose,
    ConfigurationVersionInput,
    DecisionAuthorizationBasisVersionInput,
    DecisionStatus,
    DecisionVersionInput,
    DelegationEffect,
    GoverningDesignationInput,
    IntegrationStatus,
    IntegrationVersionInput,
    RoleAssignmentVersionInput,
    RoleTargetType,
    UncertaintyClassification,
    UncertaintyClassificationVersionInput,
)
from paim.integrity import EffectiveInterval, FixedClock, RecordId, RecordVersionId
from paim.persistence.sqlite import SQLiteIntegrityStore
from tests.helpers import utc
from tests.integration.test_increment_3_foundation import accept, analytical_input, meta

NOW = utc(2026, 2, 1)
EFFECTIVE = EffectiveInterval(utc(2026, 1, 1))


@dataclass(frozen=True)
class C4Context:
    service: Increment4ApplicationService
    case_id: RecordId
    configuration_id: RecordId
    configuration_version_id: RecordVersionId
    assessor_id: RecordId


@dataclass(frozen=True)
class Foundation:
    context: C4Context
    integration_id: RecordId
    integration_version_id: RecordVersionId
    snapshot_id: RecordId
    snapshot_version_id: RecordVersionId
    clause_id: RecordId
    clause_version_id: RecordVersionId
    decision_id: RecordId
    decision_version_id: RecordVersionId
    authority_id: RecordId
    authority_version_id: RecordVersionId
    authority_assignment_version_id: RecordVersionId
    authority_gap_version_id: RecordVersionId | None


def c4_context(store: SQLiteIntegrityStore, key: str) -> C4Context:
    service = Increment4ApplicationService(store, FixedClock(NOW))
    case_id, case_version_id = RecordId.new(), RecordVersionId.new()
    service.commit_case(
        meta(f"{key}-case"),
        CaseVersionInput(case_id, case_version_id, key, EFFECTIVE),
    )
    configuration_id, configuration_version_id = RecordId.new(), RecordVersionId.new()
    service.commit_configuration(
        meta(f"{key}-configuration"),
        ConfigurationVersionInput(
            configuration_id,
            configuration_version_id,
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
            configuration_version_id,
            EFFECTIVE,
            accountable_mechanism="configuration-currentness board",
        ),
    )
    actor_id = RecordId.new()
    service.commit_actor(
        meta(f"{key}-actor"),
        ActorVersionInput(actor_id, RecordVersionId.new(), "Decision Authority", EFFECTIVE),
    )
    return C4Context(service, case_id, configuration_id, configuration_version_id, actor_id)


def foundation(
    store: SQLiteIntegrityStore,
    key: str,
    *,
    human_clause: bool = False,
    include_authority_gap: bool = False,
) -> Foundation:
    ctx = c4_context(store, key)
    gap_version_id: RecordVersionId | None = None
    if include_authority_gap:
        gap_id, gap_version_id = RecordId.new(), RecordVersionId.new()
        ctx.service.commit_authority_gap(
            meta(f"{key}-gap"),
            AuthorityGapVersionInput(
                gap_id,
                gap_version_id,
                ctx.case_id,
                ctx.configuration_id,
                ctx.configuration_version_id,
                "Q-BROAD",
                "Who may authorize broader deployment?",
                "broader-scope",
                "broader authority remains unresolved",
                {"source": "authority-register"},
                EFFECTIVE,
            ),
        )
    authority_gap_version_ids = (gap_version_id,) if gap_version_id is not None else ()
    value_id, value_version = analytical_input(ctx, f"{key}-value", AnalyticalLane.VALUE)
    value_acceptance = accept(ctx, f"{key}-value", AnalyticalLane.VALUE, value_id, value_version)
    risk_id, risk_version = analytical_input(ctx, f"{key}-risk", AnalyticalLane.RISK)
    risk_acceptance = accept(ctx, f"{key}-risk", AnalyticalLane.RISK, risk_id, risk_version)
    value_acceptance_detail = store.get_version(value_acceptance)
    risk_acceptance_detail = store.get_version(risk_acceptance)
    assert value_acceptance_detail is not None and risk_acceptance_detail is not None
    value_fitness = RecordVersionId.parse(
        str(value_acceptance_detail.content["fitness_version_id"])
    )
    risk_fitness = RecordVersionId.parse(str(risk_acceptance_detail.content["fitness_version_id"]))

    assert ctx.service.transition_case(
        meta(f"{key}-configuration-defined"),
        case_id=ctx.case_id,
        target_state=CaseLifecycleState.CONFIGURATION_DEFINED,
        effective_at=EFFECTIVE.start,
    ).accepted
    assert ctx.service.transition_case(
        meta(f"{key}-evidence-analysis"),
        case_id=ctx.case_id,
        target_state=CaseLifecycleState.EVIDENCE_ANALYSIS,
        effective_at=EFFECTIVE.start,
    ).accepted
    assert ctx.service.transition_case(
        meta(f"{key}-ready"),
        case_id=ctx.case_id,
        target_state=CaseLifecycleState.READY_FOR_INTEGRATION,
        effective_at=EFFECTIVE.start,
        use_context="integration-path-a",
        purpose="operating-plan",
    ).accepted

    integration_id, integration_version_id = RecordId.new(), RecordVersionId.new()
    ctx.service.commit_integration(
        meta(f"{key}-integration"),
        IntegrationVersionInput(
            integration_id,
            integration_version_id,
            ctx.case_id,
            ctx.configuration_id,
            ctx.configuration_version_id,
            "integration-path-a",
            "operating-plan",
            value_version,
            value_acceptance,
            value_fitness,
            risk_version,
            risk_acceptance,
            risk_fitness,
            (),
            ("policy:bounded-operation",),
            (),
            authority_gap_version_ids,
            ctx.assessor_id,
            None,
            "integration board",
            IntegrationStatus.COMPLETED,
            {
                "reinforcement": "both lanes support bounded operation",
                "conflict": "none rewritten",
            },
            ({"alternative": "suspend", "disposition": "not selected"},),
            {"action": "continue inside boundary", "state": "bounded continuation"},
            "independent lane conclusions support bounded continuation",
            EFFECTIVE,
        ),
    )
    assert ctx.service.transition_case(
        meta(f"{key}-decision-pending"),
        case_id=ctx.case_id,
        target_state=CaseLifecycleState.DECISION_PENDING,
        effective_at=EFFECTIVE.start,
    ).accepted

    accepted_id, accepted_version = RecordId.new(), RecordVersionId.new()
    ctx.service.commit_uncertainty_classification(
        meta(f"{key}-accepted-uncertainty"),
        UncertaintyClassificationVersionInput(
            accepted_id,
            accepted_version,
            integration_version_id,
            "decision-a",
            "bounded continuation",
            "value uncertainty 1",
            value_version,
            None,
            UncertaintyClassification.ACCEPTED,
            "compatible inside the proposed boundary",
            "observe monthly",
            None,
            "integration board",
            EFFECTIVE,
        ),
    )
    limiting_id, limiting_version = RecordId.new(), RecordVersionId.new()
    ctx.service.commit_uncertainty_classification(
        meta(f"{key}-limiting-uncertainty"),
        UncertaintyClassificationVersionInput(
            limiting_id,
            limiting_version,
            integration_version_id,
            "decision-a",
            "bounded continuation",
            "risk uncertainty 1",
            risk_version,
            None,
            UncertaintyClassification.DECISION_LIMITING,
            "blocks broader deployment but not bounded continuation",
            "longitudinal control evidence required",
            None,
            "integration board",
            EFFECTIVE,
        ),
    )

    snapshot_id, snapshot_version_id = RecordId.new(), RecordVersionId.new()
    clause_id, clause_version_id = RecordId.new(), RecordVersionId.new()
    verification = (
        BoundaryVerificationMode.HUMAN if human_clause else BoundaryVerificationMode.MECHANICAL
    )
    clause = BoundaryClauseInput(
        clause_id,
        clause_version_id,
        "capacity",
        BoundaryClauseEffect.LIMITED,
        "requests-per-minute",
        "metric:rpm",
        None if human_clause else "LTE",
        None if human_clause else "100",
        None if human_clause else "rpm",
        "capacity remains bounded and reviewed",
        "preserves the Risk boundary",
        (f"value-input:{value_version}", f"risk-input:{risk_version}"),
        verification,
        "suspend affected activity",
    )
    ctx.service.commit_boundary_snapshot(
        meta(f"{key}-boundary"),
        BoundarySnapshotVersionInput(
            snapshot_id,
            snapshot_version_id,
            ctx.case_id,
            ctx.configuration_id,
            ctx.configuration_version_id,
            integration_id,
            integration_version_id,
            ctx.assessor_id,
            "finalized",
            (clause,),
            "hybrid boundary for authorization",
            (),
            EFFECTIVE,
        ),
    )
    decision_id, decision_version_id = RecordId.new(), RecordVersionId.new()
    ctx.service.commit_decision_proposal(
        meta(f"{key}-decision"),
        DecisionVersionInput(
            decision_id,
            decision_version_id,
            ctx.case_id,
            ctx.configuration_id,
            ctx.configuration_version_id,
            integration_id,
            integration_version_id,
            snapshot_id,
            snapshot_version_id,
            "continue within the exact finalized boundary",
            "bounded continuation",
            "Value and Risk remain independently supportable inside the boundary",
            ("do not exceed 100 rpm",),
            (accepted_version,),
            (limiting_version,),
            ("suspend", "redesign"),
            ("policy:bounded-operation",),
            (),
            authority_gap_version_ids,
            (),
            ("collect longitudinal control evidence",),
            ("reassess on control failure",),
            DecisionStatus.PENDING_AUTHORIZATION,
            EFFECTIVE,
        ),
    )

    authority_id, authority_version_id = RecordId.new(), RecordVersionId.new()
    ctx.service.commit_authority_record(
        meta(f"{key}-authority-record"),
        AuthorityVersionInput(
            authority_id,
            authority_version_id,
            ctx.case_id,
            ctx.configuration_id,
            ctx.configuration_version_id,
            "decision-right",
            "authority-register:v1",
            {"version": "v1"},
            "narrow-scope",
            "authorize bounded continuation",
            {"limit": "narrow-scope"},
            EFFECTIVE,
        ),
    )
    assignment_id, assignment_version_id = RecordId.new(), RecordVersionId.new()
    ctx.service.commit_role_assignment(
        meta(f"{key}-decision-authority"),
        RoleAssignmentVersionInput(
            assignment_id,
            assignment_version_id,
            ctx.assessor_id,
            "Decision Authority",
            RoleTargetType.CASE,
            str(ctx.case_id),
            ctx.case_id,
            True,
            "decision-authority",
            DelegationEffect.NONE,
            None,
            EFFECTIVE,
        ),
    )
    return Foundation(
        ctx,
        integration_id,
        integration_version_id,
        snapshot_id,
        snapshot_version_id,
        clause_id,
        clause_version_id,
        decision_id,
        decision_version_id,
        authority_id,
        authority_version_id,
        assignment_version_id,
        gap_version_id,
    )


def authorization(
    fx: Foundation,
    key: str,
    *,
    operating_states: tuple[str, ...] = ("bounded continuation",),
    gaps: tuple[RecordVersionId, ...] = (),
    bounded_proceed_version_id: RecordVersionId | None = None,
) -> DecisionAuthorizationBasisVersionInput:
    return DecisionAuthorizationBasisVersionInput(
        RecordId.new(),
        RecordVersionId.new(),
        fx.decision_id,
        fx.decision_version_id,
        str(fx.context.assessor_id),
        fx.authority_assignment_version_id,
        None,
        fx.authority_version_id,
        (),
        "narrow-scope",
        ("bounded continuation only",),
        fx.context.configuration_id,
        fx.context.configuration_version_id,
        operating_states,
        "management-operation",
        None,
        f"authorization-{key}",
        fx.context.assessor_id,
        EFFECTIVE.start,
        (),
        (),
        None,
        gaps,
        bounded_proceed_version_id,
        EFFECTIVE,
    )


def bounded_proceed(
    fx: Foundation,
    *,
    authority_assignment_version_id: RecordVersionId,
    delegation_chain_version_ids: tuple[RecordVersionId, ...] = (),
) -> BoundedProceedVersionInput:
    assert fx.authority_gap_version_id is not None
    return BoundedProceedVersionInput(
        determination_id=RecordId.new(),
        version_id=RecordVersionId.new(),
        decision_version_id=fx.decision_version_id,
        unresolved_gap_version_id=fx.authority_gap_version_id,
        blocked_broader_decision="broader deployment",
        narrower_scope="narrow-scope",
        boundary_clause_version_ids=(fx.clause_version_id,),
        operating_state="bounded continuation",
        rationale="broader authority is unresolved; narrower operation is covered",
        conditions=("remain inside exact Boundary",),
        review_trigger="authority resolution or Boundary change",
        actor_id=fx.context.assessor_id,
        authority_assignment_version_id=authority_assignment_version_id,
        authority_mechanism=None,
        authority_record_version_id=fx.authority_version_id,
        delegation_chain_version_ids=delegation_chain_version_ids,
        effective=EFFECTIVE,
    )


def test_integration_preserves_exact_independent_analytical_basis_and_is_not_decision(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    fx = foundation(sqlite_store, "integration")
    integration = sqlite_store.get_version(fx.integration_version_id)
    decision = sqlite_store.get_version(fx.decision_version_id)
    assert integration is not None and decision is not None
    value = sqlite_store.get_version(
        RecordVersionId.parse(str(integration.content["value_input_version_id"]))
    )
    risk = sqlite_store.get_version(
        RecordVersionId.parse(str(integration.content["risk_input_version_id"]))
    )
    assert value is not None and value.content["implication"] == "VALUE implication"
    assert risk is not None and risk.content["implication"] == "RISK implication"
    assert "score" not in integration.content
    assert (
        fx.context.service.current_authorized_decision(
            case_id=fx.context.case_id,
            configuration_version_id=fx.context.configuration_version_id,
            effective_at=EFFECTIVE.start,
        ).reason
        == "AUTHORIZED DECISION NOT ESTABLISHED"
    )  # type: ignore[union-attr]


def test_missing_or_conflicting_lane_selection_blocks_integration_atomically(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    def fitness(acceptance_version_id: RecordVersionId) -> RecordVersionId:
        accepted = sqlite_store.get_version(acceptance_version_id)
        assert accepted is not None
        return RecordVersionId.parse(str(accepted.content["fitness_version_id"]))

    def attempt(
        ctx: C4Context,
        key: str,
        value_version: RecordVersionId,
        value_acceptance: RecordVersionId,
        risk_version: RecordVersionId,
        risk_acceptance: RecordVersionId,
    ) -> None:
        ctx.service.commit_integration(
            meta(f"{key}-integration"),
            IntegrationVersionInput(
                RecordId.new(),
                RecordVersionId.new(),
                ctx.case_id,
                ctx.configuration_id,
                ctx.configuration_version_id,
                "integration-path-a",
                "operating-plan",
                value_version,
                value_acceptance,
                fitness(value_acceptance),
                risk_version,
                risk_acceptance,
                (
                    fitness(risk_acceptance)
                    if sqlite_store.get_version(risk_acceptance)
                    else risk_acceptance
                ),
                (),
                (),
                (),
                (),
                ctx.assessor_id,
                None,
                "integration board",
                IntegrationStatus.COMPLETED,
                {"conflict": "preserved"},
                (),
                {"action": "bounded"},
                "attempt exact handoff",
                EFFECTIVE,
            ),
        )

    missing = c4_context(sqlite_store, "integration-missing")
    value_record, value_version = analytical_input(
        missing, "integration-missing-value", AnalyticalLane.VALUE
    )
    value_acceptance = accept(
        missing,
        "integration-missing-value",
        AnalyticalLane.VALUE,
        value_record,
        value_version,
    )
    _, risk_version = analytical_input(missing, "integration-missing-risk", AnalyticalLane.RISK)
    with pytest.raises(DomainRuleViolation, match="INPUT SELECTION NOT ESTABLISHED"):
        attempt(
            missing,
            "integration-missing",
            value_version,
            value_acceptance,
            risk_version,
            RecordVersionId.new(),
        )
    assert sqlite_store.count_rows("integration_versions") == 0

    conflict = c4_context(sqlite_store, "integration-conflict")
    value_record, value_version = analytical_input(
        conflict, "integration-conflict-value", AnalyticalLane.VALUE
    )
    first = accept(
        conflict,
        "integration-conflict-value-first",
        AnalyticalLane.VALUE,
        value_record,
        value_version,
    )
    accept(
        conflict,
        "integration-conflict-value-second",
        AnalyticalLane.VALUE,
        value_record,
        value_version,
    )
    risk_record, risk_version = analytical_input(
        conflict, "integration-conflict-risk", AnalyticalLane.RISK
    )
    risk_acceptance = accept(
        conflict,
        "integration-conflict-risk",
        AnalyticalLane.RISK,
        risk_record,
        risk_version,
    )
    with pytest.raises(DomainRuleViolation, match="INPUT SELECTION CONFLICT"):
        attempt(
            conflict,
            "integration-conflict",
            value_version,
            first,
            risk_version,
            risk_acceptance,
        )
    assert sqlite_store.count_rows("integration_versions") == 0


def test_boundary_mechanical_human_and_comparison_outcomes(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    fx = foundation(sqlite_store, "boundary")
    assert (
        fx.context.service.evaluate_boundary_clause(
            snapshot_version_id=fx.snapshot_version_id,
            clause_version_id=fx.clause_version_id,
            observed_value="90",
            observed_unit="rpm",
            effective_at=EFFECTIVE.start,
        ).outcome
        is BoundaryEvaluationOutcome.PASS
    )
    assert (
        fx.context.service.evaluate_boundary_clause(
            snapshot_version_id=fx.snapshot_version_id,
            clause_version_id=fx.clause_version_id,
            observed_value="110",
            observed_unit="rpm",
            effective_at=EFFECTIVE.start,
        ).outcome
        is BoundaryEvaluationOutcome.BREACH
    )
    assert (
        fx.context.service.evaluate_boundary_clause(
            snapshot_version_id=fx.snapshot_version_id,
            clause_version_id=fx.clause_version_id,
            observed_value=None,
            observed_unit=None,
            effective_at=EFFECTIVE.start,
        ).outcome
        is BoundaryEvaluationOutcome.INDETERMINATE
    )

    def successor(value: str, key: str) -> RecordVersionId:
        snapshot_id, snapshot_version = RecordId.new(), RecordVersionId.new()
        fx.context.service.commit_boundary_snapshot(
            meta(f"boundary-{key}"),
            BoundarySnapshotVersionInput(
                snapshot_id,
                snapshot_version,
                fx.context.case_id,
                fx.context.configuration_id,
                fx.context.configuration_version_id,
                fx.integration_id,
                fx.integration_version_id,
                fx.context.assessor_id,
                "finalized",
                (
                    BoundaryClauseInput(
                        RecordId.new(),
                        RecordVersionId.new(),
                        "capacity",
                        BoundaryClauseEffect.LIMITED,
                        "requests-per-minute",
                        "metric:rpm",
                        "LTE",
                        value,
                        "rpm",
                        "capacity remains bounded and reviewed",
                        "exact successor comparison",
                        (f"integration:{fx.integration_version_id}",),
                        BoundaryVerificationMode.MECHANICAL,
                        "suspend affected activity",
                    ),
                ),
                "successor comparison fixture",
                (),
                EFFECTIVE,
            ),
        )
        return snapshot_version

    assert (
        fx.context.service.compare_boundaries(
            predecessor_version_id=fx.snapshot_version_id,
            successor_version_id=successor("100", "unchanged"),
        )
        is BoundaryComparisonOutcome.UNCHANGED
    )
    assert (
        fx.context.service.compare_boundaries(
            predecessor_version_id=fx.snapshot_version_id,
            successor_version_id=successor("80", "narrowed"),
        )
        is BoundaryComparisonOutcome.NARROWED
    )
    assert (
        fx.context.service.compare_boundaries(
            predecessor_version_id=fx.snapshot_version_id,
            successor_version_id=successor("120", "broadened"),
        )
        is BoundaryComparisonOutcome.BROADENED
    )

    def custom_snapshot(clauses: tuple[BoundaryClauseInput, ...], key: str) -> RecordVersionId:
        version_id = RecordVersionId.new()
        fx.context.service.commit_boundary_snapshot(
            meta(f"boundary-custom-{key}"),
            BoundarySnapshotVersionInput(
                RecordId.new(),
                version_id,
                fx.context.case_id,
                fx.context.configuration_id,
                fx.context.configuration_version_id,
                fx.integration_id,
                fx.integration_version_id,
                fx.context.assessor_id,
                "finalized",
                clauses,
                "custom comparison fixture",
                (),
                EFFECTIVE,
            ),
        )
        return version_id

    broader_capacity = BoundaryClauseInput(
        RecordId.new(),
        RecordVersionId.new(),
        "capacity",
        BoundaryClauseEffect.LIMITED,
        "requests-per-minute",
        "metric:rpm",
        "LTE",
        "120",
        "rpm",
        "capacity remains bounded and reviewed",
        "broader capacity",
        (f"integration:{fx.integration_version_id}",),
        BoundaryVerificationMode.MECHANICAL,
        "suspend",
    )
    added_requirement = BoundaryClauseInput(
        RecordId.new(),
        RecordVersionId.new(),
        "human-review",
        BoundaryClauseEffect.REQUIRED,
        "approval",
        "control:human-review",
        "EQ",
        "present",
        None,
        "human review is required",
        "narrows the boundary",
        (f"integration:{fx.integration_version_id}",),
        BoundaryVerificationMode.MECHANICAL,
        "block activity",
    )
    mixed = custom_snapshot((broader_capacity, added_requirement), "mixed")
    assert (
        fx.context.service.compare_boundaries(
            predecessor_version_id=fx.snapshot_version_id,
            successor_version_id=mixed,
        )
        is BoundaryComparisonOutcome.MIXED
    )
    indeterminate = custom_snapshot(
        (
            replace(
                broader_capacity,
                clause_id=RecordId.new(),
                clause_version_id=RecordVersionId.new(),
                operator=None,
                value=None,
                unit=None,
                narrative="capacity requires substantive review",
                verification_mode=BoundaryVerificationMode.HUMAN,
            ),
        ),
        "indeterminate",
    )
    assert (
        fx.context.service.compare_boundaries(
            predecessor_version_id=fx.snapshot_version_id,
            successor_version_id=indeterminate,
        )
        is BoundaryComparisonOutcome.INDETERMINATE
    )


def test_human_determination_absence_blocks_then_exact_determination_allows(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    fx = foundation(sqlite_store, "human", human_clause=True)
    basis = authorization(fx, "human")
    with pytest.raises(DomainRuleViolation, match="determination absent"):
        fx.context.service.authorize_decision(meta("human-auth-fail"), basis)
    assert sqlite_store.count_rows("decision_authorization_basis_versions") == 0
    assert (
        fx.context.service.current_lifecycle_state(
            case_id=fx.context.case_id, effective_at=EFFECTIVE.start
        )
        is CaseLifecycleState.DECISION_PENDING
    )
    fx.context.service.commit_boundary_determination(
        meta("human-determination"),
        BoundaryDeterminationVersionInput(
            RecordId.new(),
            RecordVersionId.new(),
            fx.snapshot_version_id,
            fx.clause_id,
            fx.clause_version_id,
            BoundaryEvaluationOutcome.PASS,
            fx.context.assessor_id,
            None,
            "boundary review board",
            (),
            "narrative clause is satisfied for the bounded use",
            "review monthly",
            EFFECTIVE,
        ),
    )
    fx.context.service.authorize_decision(meta("human-auth-pass"), basis)
    assert (
        fx.context.service.current_lifecycle_state(
            case_id=fx.context.case_id, effective_at=EFFECTIVE.start
        )
        is CaseLifecycleState.DECIDED
    )


def test_authority_negative_rollback_atomic_success_idempotency_and_current_query(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    fx = foundation(sqlite_store, "authorization")
    invalid = authorization(fx, "bad-state", operating_states=("targeted scale",))
    with pytest.raises(DomainRuleViolation, match="operating-state coverage mismatch"):
        fx.context.service.authorize_decision(meta("authorization-invalid"), invalid)
    assert sqlite_store.count_rows("decision_authorization_basis_versions") == 0
    assert (
        fx.context.service.current_lifecycle_state(
            case_id=fx.context.case_id, effective_at=EFFECTIVE.start
        )
        is CaseLifecycleState.DECISION_PENDING
    )

    valid = authorization(fx, "valid")
    command = meta("authorization-valid")
    first = fx.context.service.authorize_decision(command, valid)
    replay = fx.context.service.authorize_decision(command, valid)
    assert replay == first
    assert sqlite_store.count_rows("decision_authorization_basis_versions") == 1
    assert (
        fx.context.service.current_lifecycle_state(
            case_id=fx.context.case_id, effective_at=EFFECTIVE.start
        )
        is CaseLifecycleState.DECIDED
    )
    selected = fx.context.service.current_authorized_decision(
        case_id=fx.context.case_id,
        configuration_version_id=fx.context.configuration_version_id,
        effective_at=EFFECTIVE.start,
    )
    assert isinstance(selected, AuthorizedDecisionFound)
    assert selected.decision_version_id == fx.decision_version_id
    assert selected.authorization_basis_version_id == valid.version_id


@pytest.mark.parametrize(
    ("failure", "message"),
    [
        ("technical-permission", "missing authority"),
        ("unrelated-scope", "unrelated-scope"),
        ("conflict", "explicit conflict"),
        ("delegation", "invalid, expired"),
        ("configuration", "Configuration coverage mismatch"),
        ("missing-source", "missing required Authority Record"),
    ],
)
def test_authority_chain_failures_are_explicit_and_leave_no_partial_commit(
    sqlite_store: SQLiteIntegrityStore, failure: str, message: str
) -> None:
    fx = foundation(sqlite_store, f"negative-{failure}")
    basis = authorization(fx, failure)
    if failure == "technical-permission":
        basis = replace(
            basis,
            authority_assignment_version_id=None,
            authority_record_version_id=None,
        )
    elif failure == "unrelated-scope":
        other_case, other_case_version = RecordId.new(), RecordVersionId.new()
        fx.context.service.commit_case(
            meta(f"negative-{failure}-other-case"),
            CaseVersionInput(other_case, other_case_version, "other case", EFFECTIVE),
        )
        unrelated_version = RecordVersionId.new()
        fx.context.service.commit_role_assignment(
            meta(f"negative-{failure}-assignment"),
            RoleAssignmentVersionInput(
                RecordId.new(),
                unrelated_version,
                fx.context.assessor_id,
                "Decision Authority",
                RoleTargetType.CASE,
                str(other_case),
                other_case,
                True,
                "unrelated-authority",
                DelegationEffect.NONE,
                None,
                EFFECTIVE,
            ),
        )
        basis = replace(basis, authority_assignment_version_id=unrelated_version)
    elif failure == "conflict":
        other_actor = RecordId.new()
        fx.context.service.commit_actor(
            meta("negative-conflict-other-actor"),
            ActorVersionInput(other_actor, RecordVersionId.new(), "Other Authority", EFFECTIVE),
        )
        fx.context.service.commit_role_assignment(
            meta("negative-conflict-assignment"),
            RoleAssignmentVersionInput(
                RecordId.new(),
                RecordVersionId.new(),
                other_actor,
                "Decision Authority",
                RoleTargetType.CONFIGURATION,
                str(fx.context.configuration_id),
                fx.context.case_id,
                True,
                "competing-authority",
                DelegationEffect.NONE,
                None,
                EFFECTIVE,
            ),
        )
    elif failure == "delegation":
        basis = replace(
            basis,
            delegation_chain_version_ids=(
                RecordVersionId.new(),
                fx.authority_assignment_version_id,
            ),
        )
    elif failure == "configuration":
        basis = replace(basis, configuration_id=RecordId.new())
    elif failure == "missing-source":
        basis = replace(basis, authority_record_version_id=None)
    with pytest.raises(DomainRuleViolation, match=message):
        fx.context.service.authorize_decision(meta(f"negative-{failure}-authorize"), basis)
    assert sqlite_store.count_rows("decision_authorization_basis_versions") == 0
    assert (
        fx.context.service.current_lifecycle_state(
            case_id=fx.context.case_id, effective_at=EFFECTIVE.start
        )
        is CaseLifecycleState.DECISION_PENDING
    )


def test_uncertainty_is_decision_relative_and_does_not_infer_operating_state(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    fx = foundation(sqlite_store, "uncertainty")
    first = RecordVersionId.new()
    fx.context.service.commit_uncertainty_classification(
        meta("uncertainty-first"),
        UncertaintyClassificationVersionInput(
            RecordId.new(),
            first,
            fx.integration_version_id,
            "bounded-decision",
            "bounded continuation",
            "shared source uncertainty",
            None,
            None,
            UncertaintyClassification.ACCEPTED,
            "compatible with bounded continuation",
            "observe",
            None,
            "integration board",
            EFFECTIVE,
        ),
    )
    second = RecordVersionId.new()
    fx.context.service.commit_uncertainty_classification(
        meta("uncertainty-second"),
        UncertaintyClassificationVersionInput(
            RecordId.new(),
            second,
            fx.integration_version_id,
            "scale-decision",
            "targeted scale",
            "shared source uncertainty",
            None,
            None,
            UncertaintyClassification.DECISION_LIMITING,
            "blocks the different proposed decision",
            "new evidence required",
            None,
            "integration board",
            EFFECTIVE,
        ),
    )
    first_record = sqlite_store.get_version(first)
    second_record = sqlite_store.get_version(second)
    assert first_record is not None and second_record is not None
    assert first_record.content["classification"] == "ACCEPTED_UNCERTAINTY"
    assert second_record.content["classification"] == "DECISION_LIMITING_UNCERTAINTY"
    assert first_record.content["proposed_operating_state"] == "bounded continuation"
    assert second_record.content["proposed_operating_state"] == "targeted scale"
    assert "inferred_operating_state" not in first_record.content


def test_bounded_proceed_keeps_gap_unresolved_and_requires_exact_scope(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    fx = foundation(sqlite_store, "bounded", include_authority_gap=True)
    assert fx.authority_gap_version_id is not None
    gap_version = fx.authority_gap_version_id
    bounded_id, bounded_version = RecordId.new(), RecordVersionId.new()
    fx.context.service.commit_bounded_proceed(
        meta("bounded-determination"),
        BoundedProceedVersionInput(
            bounded_id,
            bounded_version,
            fx.decision_version_id,
            gap_version,
            "broader deployment",
            "narrow-scope",
            (fx.clause_version_id,),
            "bounded continuation",
            "broader authority is unresolved; narrower operation is covered",
            ("remain inside exact Boundary",),
            "authority resolution or Boundary change",
            fx.context.assessor_id,
            fx.authority_assignment_version_id,
            None,
            fx.authority_version_id,
            (),
            EFFECTIVE,
        ),
    )
    basis = authorization(
        fx,
        "bounded",
        gaps=(gap_version,),
        bounded_proceed_version_id=bounded_version,
    )
    fx.context.service.authorize_decision(meta("bounded-auth"), basis)
    assert isinstance(
        fx.context.service.current_authorized_decision(
            case_id=fx.context.case_id,
            configuration_version_id=fx.context.configuration_version_id,
            effective_at=EFFECTIVE.start,
        ),
        AuthorizedDecisionFound,
    )
    assert sqlite_store.get_version(gap_version) is not None
    with sqlite_store.read_transaction() as transaction:
        assert gap_version in transaction.current_authority_gap_versions(
            case_id=fx.context.case_id,
            configuration_version_id=fx.context.configuration_version_id,
            effective_at=EFFECTIVE.start,
            known_at=NOW,
        )
    assert sqlite_store.count_rows("decision_authorization_basis_versions") == 1


def test_bounded_proceed_rejects_unrelated_scope_decision_authority(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    fx = foundation(sqlite_store, "bounded-unrelated", include_authority_gap=True)
    unrelated_case_id = RecordId.new()
    fx.context.service.commit_case(
        meta("bounded-unrelated-scope-case"),
        CaseVersionInput(
            unrelated_case_id,
            RecordVersionId.new(),
            "unrelated authority scope",
            EFFECTIVE,
        ),
    )
    unrelated_assignment = RecordVersionId.new()
    fx.context.service.commit_role_assignment(
        meta("bounded-unrelated-authority"),
        RoleAssignmentVersionInput(
            RecordId.new(),
            unrelated_assignment,
            fx.context.assessor_id,
            "Decision Authority",
            RoleTargetType.CASE,
            str(unrelated_case_id),
            unrelated_case_id,
            True,
            "unrelated-decision-authority",
            DelegationEffect.NONE,
            None,
            EFFECTIVE,
        ),
    )
    with pytest.raises(DomainRuleViolation, match="unrelated-scope"):
        fx.context.service.commit_bounded_proceed(
            meta("bounded-unrelated-attempt"),
            bounded_proceed(
                fx,
                authority_assignment_version_id=unrelated_assignment,
            ),
        )
    assert sqlite_store.count_rows("bounded_proceed_versions") == 0


def test_bounded_proceed_rejects_competing_applicable_decision_authority(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    fx = foundation(sqlite_store, "bounded-conflict", include_authority_gap=True)
    fx.context.service.commit_role_assignment(
        meta("bounded-conflict-configuration-authority"),
        RoleAssignmentVersionInput(
            RecordId.new(),
            RecordVersionId.new(),
            fx.context.assessor_id,
            "Decision Authority",
            RoleTargetType.CONFIGURATION,
            str(fx.context.configuration_id),
            fx.context.case_id,
            True,
            "competing-decision-authority",
            DelegationEffect.NONE,
            None,
            EFFECTIVE,
        ),
    )
    with pytest.raises(DomainRuleViolation, match="explicit conflict"):
        fx.context.service.commit_bounded_proceed(
            meta("bounded-conflict-attempt"),
            bounded_proceed(
                fx,
                authority_assignment_version_id=fx.authority_assignment_version_id,
            ),
        )
    assert sqlite_store.count_rows("bounded_proceed_versions") == 0


def test_bounded_proceed_rejects_expired_exact_delegation_chain(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    fx = foundation(sqlite_store, "bounded-expired", include_authority_gap=True)
    expired_delegation = RecordVersionId.new()
    fx.context.service.commit_role_assignment(
        meta("bounded-expired-intermediate"),
        RoleAssignmentVersionInput(
            RecordId.new(),
            expired_delegation,
            fx.context.assessor_id,
            "Decision Authority",
            RoleTargetType.CONFIGURATION,
            str(fx.context.configuration_id),
            fx.context.case_id,
            True,
            "delegated-decision-authority",
            DelegationEffect.SUPPLEMENT,
            fx.authority_assignment_version_id,
            EffectiveInterval(utc(2025, 12, 1), utc(2025, 12, 31)),
        ),
    )
    terminal_delegation = RecordVersionId.new()
    fx.context.service.commit_role_assignment(
        meta("bounded-expired-terminal"),
        RoleAssignmentVersionInput(
            RecordId.new(),
            terminal_delegation,
            fx.context.assessor_id,
            "Decision Authority",
            RoleTargetType.DECISION,
            str(fx.decision_id),
            fx.context.case_id,
            True,
            "delegated-decision-authority",
            DelegationEffect.SUPPLEMENT,
            expired_delegation,
            EFFECTIVE,
        ),
    )
    with pytest.raises(DomainRuleViolation, match="invalid, expired"):
        fx.context.service.commit_bounded_proceed(
            meta("bounded-expired-attempt"),
            bounded_proceed(
                fx,
                authority_assignment_version_id=terminal_delegation,
                delegation_chain_version_ids=(
                    fx.authority_assignment_version_id,
                    expired_delegation,
                    terminal_delegation,
                ),
            ),
        )
    assert sqlite_store.count_rows("bounded_proceed_versions") == 0


def test_bounded_proceed_valid_exact_narrower_delegation_chain_succeeds(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    fx = foundation(sqlite_store, "bounded-delegated", include_authority_gap=True)
    delegated_assignment = RecordVersionId.new()
    fx.context.service.commit_role_assignment(
        meta("bounded-delegated-authority"),
        RoleAssignmentVersionInput(
            RecordId.new(),
            delegated_assignment,
            fx.context.assessor_id,
            "Decision Authority",
            RoleTargetType.CONFIGURATION,
            str(fx.context.configuration_id),
            fx.context.case_id,
            True,
            "delegated-decision-authority",
            DelegationEffect.SUPPLEMENT,
            fx.authority_assignment_version_id,
            EFFECTIVE,
        ),
    )
    exact_chain = (fx.authority_assignment_version_id, delegated_assignment)
    bounded = bounded_proceed(
        fx,
        authority_assignment_version_id=delegated_assignment,
        delegation_chain_version_ids=exact_chain,
    )
    fx.context.service.commit_bounded_proceed(meta("bounded-delegated-determination"), bounded)
    assert fx.authority_gap_version_id is not None
    basis = replace(
        authorization(
            fx,
            "bounded-delegated",
            gaps=(fx.authority_gap_version_id,),
            bounded_proceed_version_id=bounded.version_id,
        ),
        authority_assignment_version_id=delegated_assignment,
        delegation_chain_version_ids=exact_chain,
    )
    fx.context.service.authorize_decision(meta("bounded-delegated-auth"), basis)
    assert sqlite_store.count_rows("bounded_proceed_versions") == 1
    assert sqlite_store.count_rows("bounded_proceed_delegations") == 2
    assert isinstance(
        fx.context.service.current_authorized_decision(
            case_id=fx.context.case_id,
            configuration_version_id=fx.context.configuration_version_id,
            effective_at=EFFECTIVE.start,
        ),
        AuthorizedDecisionFound,
    )


def test_successor_decision_and_later_authority_change_preserve_historical_reconstruction(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    fx = foundation(sqlite_store, "successor")
    initial_basis = authorization(fx, "initial")
    fx.context.service.authorize_decision(meta("successor-initial-auth"), initial_basis)
    original = sqlite_store.get_version(fx.decision_version_id)
    assert original is not None
    successor_effective = EffectiveInterval(utc(2026, 1, 15))
    successor_version = RecordVersionId.new()
    accepted = tuple(
        RecordVersionId.parse(item)
        for item in original.content["accepted_uncertainty_version_ids"]  # type: ignore[union-attr]
    )
    limiting = tuple(
        RecordVersionId.parse(item)
        for item in original.content["decision_limiting_uncertainty_version_ids"]  # type: ignore[union-attr]
    )
    fx.context.service.commit_decision_proposal(
        meta("successor-amendment-decision"),
        DecisionVersionInput(
            fx.decision_id,
            successor_version,
            fx.context.case_id,
            fx.context.configuration_id,
            fx.context.configuration_version_id,
            fx.integration_id,
            fx.integration_version_id,
            fx.snapshot_id,
            fx.snapshot_version_id,
            "continue within the exact finalized boundary",
            "bounded continuation",
            "successor rationale preserves the same exact analytical and Boundary basis",
            ("do not exceed 100 rpm",),
            accepted,
            limiting,
            ("suspend", "redesign"),
            ("policy:bounded-operation",),
            (),
            (),
            (),
            ("collect longitudinal control evidence",),
            ("reassess on control failure",),
            DecisionStatus.PENDING_AUTHORIZATION,
            successor_effective,
            expected_version_id=fx.decision_version_id,
            relationship_reason="accountable successor Decision",
        ),
    )
    successor_basis = replace(
        authorization(fx, "successor"),
        basis_id=RecordId.new(),
        version_id=RecordVersionId.new(),
        decision_version_id=successor_version,
        authorization_event_id="authorization-successor-exact",
        authorization_effective_at=successor_effective.start,
        effective=successor_effective,
    )
    fx.context.service.authorize_decision(meta("successor-auth"), successor_basis)

    historical = fx.context.service.current_authorized_decision(
        case_id=fx.context.case_id,
        configuration_version_id=fx.context.configuration_version_id,
        effective_at=EFFECTIVE.start,
    )
    current = fx.context.service.current_authorized_decision(
        case_id=fx.context.case_id,
        configuration_version_id=fx.context.configuration_version_id,
        effective_at=utc(2026, 1, 20),
    )
    assert isinstance(historical, AuthorizedDecisionFound)
    assert historical.decision_version_id == fx.decision_version_id
    assert isinstance(current, AuthorizedDecisionFound)
    assert current.decision_version_id == successor_version
    assert current.boundary_snapshot_version_id == fx.snapshot_version_id

    changed_authority = RecordVersionId.new()
    fx.context.service.commit_authority_record(
        meta("successor-authority-change"),
        AuthorityVersionInput(
            fx.authority_id,
            changed_authority,
            fx.context.case_id,
            fx.context.configuration_id,
            fx.context.configuration_version_id,
            "decision-right",
            "authority-register:v2",
            {"version": "v2"},
            "different-future-scope",
            "future decisions require a different authority scope",
            {"limit": "future"},
            EffectiveInterval(utc(2026, 2, 1)),
            expected_version_id=fx.authority_version_id,
            relationship_reason="prospective authority change",
        ),
    )
    reconstructed = fx.context.service.current_authorized_decision(
        case_id=fx.context.case_id,
        configuration_version_id=fx.context.configuration_version_id,
        effective_at=EFFECTIVE.start,
    )
    assert isinstance(reconstructed, AuthorizedDecisionFound)
    assert reconstructed.authorization_basis_version_id == initial_basis.version_id
    assert sqlite_store.get_version(fx.authority_version_id) is not None


def test_unresolved_gap_without_bounded_proceed_or_beyond_scope_is_blocked(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    fx = foundation(sqlite_store, "bounded-negative", include_authority_gap=True)
    assert fx.authority_gap_version_id is not None
    gap_version = fx.authority_gap_version_id
    with pytest.raises(DomainRuleViolation, match="bounded-proceed determination"):
        fx.context.service.authorize_decision(
            meta("bounded-negative-absent"),
            authorization(fx, "absent", gaps=(gap_version,)),
        )
    with pytest.raises(DomainRuleViolation, match="scope does not cover exact Decision"):
        fx.context.service.commit_bounded_proceed(
            meta("bounded-negative-overbroad"),
            BoundedProceedVersionInput(
                RecordId.new(),
                RecordVersionId.new(),
                fx.decision_version_id,
                gap_version,
                "unbounded deployment",
                "broader-scope",
                (fx.clause_version_id,),
                "bounded continuation",
                "attempts to exceed the established narrower authority",
                (),
                "review now",
                fx.context.assessor_id,
                fx.authority_assignment_version_id,
                None,
                fx.authority_version_id,
                (),
                EFFECTIVE,
            ),
        )
    assert sqlite_store.count_rows("bounded_proceed_versions") == 0
    assert sqlite_store.count_rows("decision_authorization_basis_versions") == 0
