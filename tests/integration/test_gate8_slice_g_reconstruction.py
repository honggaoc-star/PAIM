from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

from sqlalchemy import inspect

from paim.assessment_review import (
    AssessmentLane,
    AssessmentReviewService,
    CandidateDisposition,
    RelianceFacts,
)
from paim.continuing_review import ReviewConstraintOperator
from paim.integrity import FixedClock, RecordVersionId
from paim.prospective_decision import (
    AuthorizationFacts,
    AuthorizeDecisionCommand,
    IntegrationFacts,
    ProspectiveDecisionService,
    ReliedLaneBasis,
)
from paim.quantitative_claims import QuantitativeClaimType
from paim.reconstruction import ReconstructionService, ReconstructionState
from paim.responsibility.models import ObligationKind
from tests.integration.test_gate8_slice_b_case_continuity import RECORDED
from tests.integration.test_gate8_slice_c_assessment_review import (
    ASSESSED_SCOPE,
    DECISION_USE,
    KNOWLEDGE,
    NOW,
    SelectiveSourceAccess,
    adequacy_command,
    finish_command,
    fixture,
    identity,
    reliance_command,
)
from tests.integration.test_gate8_slice_d_integration_decision import (
    CONTRACT as DECISION_CONTRACT,
)
from tests.integration.test_gate8_slice_d_integration_decision import (
    integration_command,
    proposal_command,
)
from tests.integration.test_gate8_slice_e_continuing_review import (
    constraint_command,
    planned_command,
    slice_e_fixture,
)
from tests.integration.test_gate8_slice_f_quantitative_claims import (
    KNOWN,
    claim_command,
    comparability_command,
    review_linked_fixture,
)
from tests.integration.test_increment_2_foundation import (
    add_case,
    add_configuration,
    designate,
)


def test_exact_decision_time_current_comparison_audit_and_timeline(
    sqlite_store: object,
) -> None:
    fx = slice_e_fixture(sqlite_store, "slice-g-vertical")
    plan = planned_command(fx, "slice-g-plan")
    fx.service.establish_planned_review_point(plan)
    constraint = constraint_command(
        fx,
        "slice-g-constraint",
        ReviewConstraintOperator.BY,
        None,
        NOW + timedelta(days=60),
    )
    fx.service.establish_required_review_constraint(constraint)
    source = fx.source.source
    case_id = source.opened.facts.case_id  # type: ignore[attr-defined]
    service = ReconstructionService(sqlite_store, source.access)  # type: ignore[arg-type]
    cutoff = RECORDED + timedelta(seconds=10)

    prior = service.decision_time_position(
        principal_id="principal:slice-c",
        actor_id=source.actor_a,
        case_id=case_id,
        decision_version_id=fx.decision_version_id,
        effective_at=NOW,
        known_at=cutoff,
    )
    assert prior.state is ReconstructionState.AVAILABLE
    assert prior.decision is not None
    assert prior.decision.version_ids == (fx.decision_version_id,)
    assert prior.integration is not None
    assert prior.integration.version_ids == (fx.integration_version_id,)
    assert prior.value is not None and prior.risk is not None
    assert prior.value.reliance_version_id == fx.source.value.reliance_version_id
    assert prior.risk.reliance_version_id == fx.source.risk.reliance_version_id
    assert fx.decision_version_id in prior.source_manifest.version_ids

    current = service.current_position(
        principal_id="principal:slice-c",
        actor_id=source.actor_a,
        case_id=case_id,
        effective_at=NOW,
        known_at=cutoff,
    )
    assert current.state is ReconstructionState.AVAILABLE, "|".join(
        f"{name}:{getattr(current, name).state}"
        for name in (
            "continuity",
            "governing_configuration",
            "integration",
            "decision",
            "review",
            "quantitative_claims",
            "responsibility_work",
        )
    )
    comparison = service.compare(prior, current)
    assert comparison.state is ReconstructionState.AVAILABLE
    assert not any(change.better_or_worse_inferred for change in comparison.changes)
    assert not any(change.causality_inferred for change in comparison.changes)
    assert not any(change.decision_requirement_inferred for change in comparison.changes)
    assert not comparison.value_risk_netted
    assert not comparison.decision_quality_inferred

    audit = service.decision_audit(
        principal_id="principal:slice-c",
        actor_id=source.actor_a,
        prior=prior,
        current=current,
    )
    assert audit.state is ReconstructionState.AVAILABLE
    assert audit.decision_version_id == fx.decision_version_id
    assert audit.decision_effective_at == NOW
    assert audit.decision_recorded_at is not None
    assert audit.assignment_version_id is not None
    assert audit.assignment_basis_version_id is not None
    assert audit.integration_version_id == fx.integration_version_id
    assert audit.value_reliance_version_id == fx.source.value.reliance_version_id
    assert audit.risk_reliance_version_id == fx.source.risk.reliance_version_id
    assert audit.derived_explanation_only
    assert not audit.hindsight_error_inferred
    assert set(audit.continuing_review_version_ids) >= {
        plan.spec.facts.version_id,
        constraint.facts.version_id,
    }
    assert set(audit.source_manifest.version_ids) >= set(current.source_manifest.version_ids)

    timeline = service.timeline(
        principal_id="principal:slice-c",
        actor_id=source.actor_a,
        case_id=case_id,
        effective_at=NOW + timedelta(days=1),
        known_at=cutoff,
    )
    assert timeline.state is ReconstructionState.AVAILABLE
    assert tuple(
        (item.effective_at, item.recorded_at, str(item.version_id)) for item in timeline.items
    ) == tuple(
        sorted(
            (item.effective_at, item.recorded_at, str(item.version_id)) for item in timeline.items
        )
    )
    assert {item.family for item in timeline.items} >= {
        "prospective-decision",
        "prospective-integration",
        "planned-review-point",
        "required-review-constraint",
    }
    assert not timeline.workflow_phase_inferred


def test_hidden_exact_source_suppresses_position_difference_timeline_and_manifest(
    sqlite_store: object,
) -> None:
    fx = slice_e_fixture(sqlite_store, "slice-g-hidden")
    source = fx.source.source
    case_id = source.opened.facts.case_id  # type: ignore[attr-defined]
    service = ReconstructionService(sqlite_store, source.access)  # type: ignore[arg-type]
    cutoff = RECORDED + timedelta(seconds=10)
    visible = service.decision_time_position(
        principal_id="principal:slice-c",
        actor_id=source.actor_a,
        case_id=case_id,
        decision_version_id=fx.decision_version_id,
        effective_at=NOW,
        known_at=cutoff,
    )
    assert visible.state is ReconstructionState.AVAILABLE

    hidden_id = fx.source.value.reliance_version_id
    restricted = ReconstructionService(sqlite_store, SelectiveSourceAccess(frozenset({hidden_id})))  # type: ignore[arg-type]
    hidden = restricted.decision_time_position(
        principal_id="principal:slice-c",
        actor_id=source.actor_a,
        case_id=case_id,
        decision_version_id=fx.decision_version_id,
        effective_at=NOW,
        known_at=cutoff,
    )
    assert hidden.state is ReconstructionState.NOT_SAFELY_AVAILABLE
    assert not hidden.source_manifest.sources
    comparison = restricted.compare(visible, hidden)
    assert comparison.state is ReconstructionState.NOT_SAFELY_AVAILABLE
    assert comparison.changes == ()
    assert comparison.prior is None and comparison.current is None
    hidden_current = restricted.current_position(
        principal_id="principal:slice-c",
        actor_id=source.actor_a,
        case_id=case_id,
        effective_at=NOW,
        known_at=cutoff,
    )
    assert hidden_current.state is ReconstructionState.NOT_SAFELY_AVAILABLE
    current_side_comparison = restricted.compare(visible, hidden_current)
    assert current_side_comparison.state is ReconstructionState.NOT_SAFELY_AVAILABLE
    assert current_side_comparison.changes == ()
    assert not current_side_comparison.prior_manifest.sources
    assert not current_side_comparison.current_manifest.sources
    timeline = restricted.timeline(
        principal_id="principal:slice-c",
        actor_id=source.actor_a,
        case_id=case_id,
        effective_at=NOW,
        known_at=cutoff,
    )
    assert hidden_id not in timeline.source_manifest.version_ids
    assert fx.decision_version_id not in tuple(item.version_id for item in timeline.items)


def test_known_at_before_decision_does_not_project_later_fact_backward(
    sqlite_store: object,
) -> None:
    fx = slice_e_fixture(sqlite_store, "slice-g-dual-time")
    source = fx.source.source
    case_id = source.opened.facts.case_id  # type: ignore[attr-defined]
    service = ReconstructionService(sqlite_store, source.access)  # type: ignore[arg-type]
    before_recording = service.decision_time_position(
        principal_id="principal:slice-c",
        actor_id=source.actor_a,
        case_id=case_id,
        decision_version_id=fx.decision_version_id,
        effective_at=NOW,
        known_at=RECORDED + timedelta(seconds=3),
    )
    after_recording = service.decision_time_position(
        principal_id="principal:slice-c",
        actor_id=source.actor_a,
        case_id=case_id,
        decision_version_id=fx.decision_version_id,
        effective_at=NOW,
        known_at=RECORDED + timedelta(seconds=10),
    )
    assert before_recording.state is ReconstructionState.ABSENT
    assert after_recording.state is ReconstructionState.AVAILABLE
    assert not before_recording.source_manifest.version_ids
    assert fx.decision_version_id in after_recording.source_manifest.version_ids


def test_optional_quantitative_change_requires_explicit_comparability_and_no_decision_inference(
    sqlite_store: object,
) -> None:
    fx, _assessment_id, _episode_id, _unrelated_id = review_linked_fixture(
        sqlite_store, "slice-g-quantitative"
    )
    expected = claim_command(
        fx, "slice-g-expected", QuantitativeClaimType.ESTIMATE_EXPECTATION, "30"
    )
    observed = claim_command(fx, "slice-g-observed", QuantitativeClaimType.OBSERVED_RESULT, "24")
    fx.service.record_claim(expected)
    fx.service.record_claim(observed)
    comparison_basis = comparability_command(
        fx, expected.facts.version_id, observed.facts.version_id, "slice-g-comparable"
    )
    with sqlite_store.read_transaction() as tx:  # type: ignore[attr-defined]
        decision_rows = tuple(
            row
            for row in tx.projection_rows("prospective_decision_versions", case_id=str(fx.case_id))
            if row["status"] == "AUTHORIZED"
        )
    assert len(decision_rows) == 1
    decision_id = RecordVersionId.parse(str(decision_rows[0]["version_id"]))
    service = ReconstructionService(sqlite_store, fx.access)  # type: ignore[arg-type]
    prior = service.decision_time_position(
        principal_id="principal:slice-c",
        actor_id=fx.actor_id,
        case_id=fx.case_id,
        decision_version_id=decision_id,
        effective_at=NOW,
        known_at=RECORDED + timedelta(seconds=10),
    )
    not_comparable = service.current_position(
        principal_id="principal:slice-c",
        actor_id=fx.actor_id,
        case_id=fx.case_id,
        effective_at=NOW,
        known_at=KNOWN + timedelta(seconds=1),
    )
    unsupported_change = next(
        change
        for change in service.compare(prior, not_comparable).changes
        if change.component == "quantitative_claims"
    )
    assert not unsupported_change.changed
    assert unsupported_change.quantitative_comparison_established is False

    fx.service.establish_comparability(comparison_basis)
    current = service.current_position(
        principal_id="principal:slice-c",
        actor_id=fx.actor_id,
        case_id=fx.case_id,
        effective_at=NOW,
        known_at=KNOWN + timedelta(seconds=1),
    )
    assert prior.state is ReconstructionState.AVAILABLE
    assert prior.quantitative_claims is not None
    assert prior.quantitative_claims.state is ReconstructionState.ABSENT
    assert current.state is ReconstructionState.AVAILABLE, "|".join(
        f"{name}:{getattr(current, name).state}"
        for name in (
            "continuity",
            "governing_configuration",
            "integration",
            "decision",
            "review",
            "quantitative_claims",
            "responsibility_work",
        )
        if getattr(current, name) is not None
    )
    assert current.quantitative_claims is not None
    assert set(current.quantitative_claims.version_ids) == {
        expected.facts.version_id,
        observed.facts.version_id,
        comparison_basis.facts.version_id,
    }
    delta = service.compare(prior, current)
    quantitative_change = next(
        change for change in delta.changes if change.component == "quantitative_claims"
    )
    assert quantitative_change.changed
    assert quantitative_change.quantitative_comparison_established is True
    assert not quantitative_change.decision_requirement_inferred
    assert not delta.decision_quality_inferred
    assert not delta.value_risk_netted


def test_each_decision_basis_source_is_required_but_unrelated_hidden_source_is_not(
    sqlite_store: object,
) -> None:
    fx = slice_e_fixture(sqlite_store, "slice-g-complete-closure")
    source = fx.source.source
    case_id = source.opened.facts.case_id  # type: ignore[attr-defined]
    cutoff = RECORDED + timedelta(seconds=10)
    visible_service = ReconstructionService(sqlite_store, source.access)  # type: ignore[arg-type]
    visible = visible_service.decision_time_position(
        principal_id="principal:slice-c",
        actor_id=source.actor_a,
        case_id=case_id,
        decision_version_id=fx.decision_version_id,
        effective_at=NOW,
        known_at=cutoff,
    )
    assert visible.state is ReconstructionState.AVAILABLE
    required: set[RecordVersionId] = {
        fx.decision_version_id,
        fx.integration_version_id,
        fx.source.value.assessment_version_id,
        fx.source.value.reliance_version_id,
        fx.source.risk.assessment_version_id,
        fx.source.risk.reliance_version_id,
    }
    with sqlite_store.read_transaction() as tx:  # type: ignore[attr-defined]
        decision = tx.projection_rows(
            "prospective_decision_versions", version_id=str(fx.decision_version_id)
        )[0]
        assignment_id = decision["assignment_version_id"]
        required.update(
            RecordVersionId.parse(str(value))
            for value in (
                decision["authority_source_version_id"],
                decision["responsibility_version_id"],
                assignment_id,
            )
        )
        assignment = tx.projection_rows(
            "responsibility_assignment_versions", version_id=str(assignment_id)
        )[0]
        required.add(RecordVersionId.parse(str(assignment["assignment_basis_version_id"])))
        unrelated = next(
            item.version_id
            for item in tx.get_history(source.actor_b).versions
            if item.version_id not in visible.source_manifest.version_ids
        )
    for hidden_id in required:
        restricted = ReconstructionService(
            sqlite_store, SelectiveSourceAccess(frozenset({hidden_id}))
        )
        hidden = restricted.decision_time_position(
            principal_id="principal:slice-c",
            actor_id=source.actor_a,
            case_id=case_id,
            decision_version_id=fx.decision_version_id,
            effective_at=NOW,
            known_at=cutoff,
        )
        assert hidden.state is ReconstructionState.NOT_SAFELY_AVAILABLE
        assert hidden.source_manifest.version_ids == ()
    unrelated_hidden = ReconstructionService(
        sqlite_store, SelectiveSourceAccess(frozenset({unrelated}))
    ).decision_time_position(
        principal_id="principal:slice-c",
        actor_id=source.actor_a,
        case_id=case_id,
        decision_version_id=fx.decision_version_id,
        effective_at=NOW,
        known_at=cutoff,
    )
    assert unrelated_hidden == visible


def test_restart_reconstruction_is_identical_and_persists_no_summary_truth(
    sqlite_store: object,
) -> None:
    fx = slice_e_fixture(sqlite_store, "slice-g-restart")
    source = fx.source.source
    case_id = source.opened.facts.case_id  # type: ignore[attr-defined]
    values = dict(
        principal_id="principal:slice-c",
        actor_id=source.actor_a,
        case_id=case_id,
        decision_version_id=fx.decision_version_id,
        effective_at=NOW,
        known_at=RECORDED + timedelta(seconds=10),
    )
    first = ReconstructionService(sqlite_store, source.access).decision_time_position(**values)  # type: ignore[arg-type]
    second = ReconstructionService(sqlite_store, source.access).decision_time_position(**values)  # type: ignore[arg-type]
    assert first == second
    tables = inspect(sqlite_store.engine).get_table_names()  # type: ignore[attr-defined]
    assert "management_position_snapshots" not in tables
    assert "decision_reconstruction_snapshots" not in tables


def test_prospective_reconstruction_never_falls_back_to_legacy_case_facts(
    sqlite_store: object,
) -> None:
    case_id, case_version_id = add_case(sqlite_store, "slice-g-legacy-only")  # type: ignore[arg-type]
    _configuration_id, configuration_version_id = add_configuration(
        sqlite_store,
        "slice-g-legacy-only",
        case_id,  # type: ignore[arg-type]
    )
    _designation_id, designation_version_id = designate(
        sqlite_store,
        "slice-g-legacy-only",
        case_id,
        configuration_version_id,  # type: ignore[arg-type]
    )
    access = SelectiveSourceAccess()
    service = ReconstructionService(sqlite_store, access)  # type: ignore[arg-type]
    current = service.current_position(
        principal_id="principal:slice-c",
        actor_id=case_id,
        case_id=case_id,
        effective_at=NOW,
        known_at=RECORDED + timedelta(seconds=20),
    )
    assert current.continuity is not None
    assert current.continuity.state is ReconstructionState.ABSENT
    assert current.governing_configuration is not None
    assert current.governing_configuration.state is ReconstructionState.ABSENT
    assert not current.source_manifest.sources
    assert case_version_id not in current.source_manifest.version_ids
    assert configuration_version_id not in current.source_manifest.version_ids
    assert designation_version_id not in current.source_manifest.version_ids
    timeline = service.timeline(
        principal_id="principal:slice-c",
        actor_id=case_id,
        case_id=case_id,
        effective_at=NOW,
        known_at=RECORDED + timedelta(seconds=20),
    )
    assert not timeline.items
    assert not timeline.source_manifest.sources


def test_current_position_preserves_explicit_lane_conflict_without_a_winner(
    sqlite_store: object,
) -> None:
    fx = fixture(sqlite_store, "slice-g-lane-conflict")
    first = finish_command(fx, AssessmentLane.VALUE, "slice-g-first-value")
    second = finish_command(fx, AssessmentLane.VALUE, "slice-g-second-value")
    fx.service.finish_assessment(first)
    fx.service.finish_assessment(second)
    first_adequacy = adequacy_command(fx, first, "slice-g-first-adequacy")
    second_adequacy = adequacy_command(fx, second, "slice-g-second-adequacy")
    fx.service.determine_adequacy(first_adequacy)
    fx.service.determine_adequacy(second_adequacy)
    first_reliance = replace(
        reliance_command(fx, first, first_adequacy, "slice-g-first-reliance", fx.actor_a),
        candidate_dispositions=(
            CandidateDisposition(
                second.facts.assessment_version_id,
                "NOT_SELECTED_FOR_THIS_USE",
                "the first exact candidate is selected for this bounded use",
            ),
        ),
    )
    second_reliance = replace(
        reliance_command(fx, second, second_adequacy, "slice-g-second-reliance", fx.actor_a),
        candidate_dispositions=(
            CandidateDisposition(
                first.facts.assessment_version_id,
                "NOT_SELECTED_FOR_THIS_USE",
                "the second exact candidate is selected for this bounded use",
            ),
        ),
    )
    fx.service.designate_reliance(first_reliance)
    fx.service.designate_reliance(second_reliance)

    current = ReconstructionService(sqlite_store, fx.access).current_position(  # type: ignore[arg-type]
        principal_id="principal:slice-c",
        actor_id=fx.actor_a,
        case_id=fx.opened.facts.case_id,  # type: ignore[attr-defined]
        effective_at=NOW,
        known_at=RECORDED + timedelta(seconds=10),
    )
    assert current.state is ReconstructionState.CONFLICT
    assert current.value_state is ReconstructionState.CONFLICT
    assert current.value is None
    assert set(current.source_manifest.version_ids) >= {
        first_reliance.facts.version_id,
        second_reliance.facts.version_id,
    }
    assert current.risk_state is ReconstructionState.ABSENT
    assert current.integration is not None
    assert current.integration.state is ReconstructionState.ABSENT
    assert current.decision is not None
    assert current.decision.state is ReconstructionState.ABSENT


def test_lane_change_requires_explicit_integration_and_decision_successors(
    sqlite_store: object,
) -> None:
    fx = slice_e_fixture(sqlite_store, "slice-g-successor")
    source = fx.source.source
    case_id = source.opened.facts.case_id  # type: ignore[attr-defined]
    service = ReconstructionService(sqlite_store, source.access)  # type: ignore[arg-type]
    prior = service.decision_time_position(
        principal_id="principal:slice-c",
        actor_id=source.actor_a,
        case_id=case_id,
        decision_version_id=fx.decision_version_id,
        effective_at=NOW,
        known_at=RECORDED + timedelta(seconds=10),
    )
    assert prior.state is ReconstructionState.AVAILABLE

    with sqlite_store.read_transaction() as tx:  # type: ignore[attr-defined]
        prior_value = tx.get_version(fx.source.value.assessment_version_id)
        prior_reliance = tx.get_version(fx.source.value.reliance_version_id)
        assert prior_value is not None and prior_reliance is not None
    finish_template = finish_command(source, AssessmentLane.VALUE, "slice-g-value-successor")
    refreshed_finish = replace(
        finish_template,
        facts=replace(finish_template.facts, assessment_record_id=prior_value.record_id),
        expected_assessment_version_id=fx.source.value.assessment_version_id,
    )
    refreshed_adequacy = adequacy_command(source, refreshed_finish, "slice-g-value-adequacy")
    reliance_template = reliance_command(
        source,
        refreshed_finish,
        refreshed_adequacy,
        "slice-g-value-reliance",
        source.actor_a,
    )
    refreshed_reliance = replace(
        reliance_template,
        facts=RelianceFacts.new(prior_reliance.record_id),
        expected_reliance_version_id=fx.source.value.reliance_version_id,
    )
    corrected_assessments = AssessmentReviewService(
        sqlite_store,  # type: ignore[arg-type]
        FixedClock(RECORDED + timedelta(seconds=11)),
        source.access,
    )
    corrected_assessments.finish_assessment(refreshed_finish)
    corrected_assessments.determine_adequacy(refreshed_adequacy)
    corrected_assessments.designate_reliance(refreshed_reliance)
    refreshed_value = ReliedLaneBasis(
        AssessmentLane.VALUE,
        refreshed_finish.facts.assessment_version_id,
        refreshed_finish.facts.readiness_version_id,
        refreshed_adequacy.facts.version_id,
        refreshed_reliance.facts.version_id,
        source.information_basis,
    )

    prospective = ProspectiveDecisionService(
        sqlite_store,  # type: ignore[arg-type]
        FixedClock(RECORDED + timedelta(seconds=12)),
        source.access,
    )
    integration_template = integration_command(fx.source, "slice-g-revised-integration")
    successor_integration = replace(
        integration_template,
        facts=IntegrationFacts.new(),
        value_basis=refreshed_value,
        risk_basis=fx.source.risk,
    )
    prospective.integrate_value_risk(successor_integration)
    proposal_template = proposal_command(
        fx.source, successor_integration, "slice-g-revised-proposal"
    )
    successor_proposal = replace(
        proposal_template,
        predecessor_decision_version_id=fx.decision_version_id,
        expected_current_decision_version_id=fx.decision_version_id,
    )
    prospective.propose_decision(successor_proposal)
    authority = fx.source.responsibilities[ObligationKind.AUTHORIZE_MANAGEMENT_DECISION]
    successor_authorization = AuthorizeDecisionCommand(
        identity(source.actor_a, "slice-g-revised-authorize"),
        AuthorizationFacts.new(),
        DECISION_CONTRACT,
        source.opened.context,  # type: ignore[attr-defined]
        case_id,
        source.opened.facts.configuration_version_id,  # type: ignore[attr-defined]
        successor_proposal.facts.version_id,
        successor_integration.facts.version_id,
        DECISION_USE,
        ASSESSED_SCOPE,
        authority.responsibility_version_id,
        authority.assignment_version_id,
        fx.source.decision_authority,
        "bounded Decision Authority",
        ASSESSED_SCOPE,
        ("no broader use",),
        ("remain inside exact boundary",),
        (),
        NOW,
        KNOWLEDGE,
    )
    prospective.authorize_decision(successor_authorization)

    with sqlite_store.read_transaction() as tx:  # type: ignore[attr-defined]
        integration_rows = tx.projection_rows(
            "prospective_integration_versions", case_id=str(case_id)
        )
        exact_matches = tuple(
            row
            for row in integration_rows
            if row["value_reliance_version_id"] == str(refreshed_reliance.facts.version_id)
            and row["risk_reliance_version_id"] == str(fx.source.risk.reliance_version_id)
        )
    assert len(exact_matches) == 1, exact_matches

    before_correction = service.current_position(
        principal_id="principal:slice-c",
        actor_id=source.actor_a,
        case_id=case_id,
        effective_at=NOW,
        known_at=RECORDED + timedelta(seconds=10),
    )
    assert before_correction.state is ReconstructionState.AVAILABLE
    assert before_correction.value is not None
    assert before_correction.value.reliance_version_id == fx.source.value.reliance_version_id
    assert before_correction.integration is not None
    assert before_correction.integration.version_ids == (fx.integration_version_id,)
    assert before_correction.decision is not None
    assert before_correction.decision.version_ids == (fx.decision_version_id,)

    current = service.current_position(
        principal_id="principal:slice-c",
        actor_id=source.actor_a,
        case_id=case_id,
        effective_at=NOW,
        known_at=RECORDED + timedelta(seconds=20),
    )
    assert current.state is ReconstructionState.AVAILABLE, "|".join(
        f"{name}:{getattr(current, name).state}"
        for name in (
            "continuity",
            "governing_configuration",
            "integration",
            "decision",
            "review",
            "quantitative_claims",
            "responsibility_work",
        )
        if getattr(current, name) is not None
    )
    assert current.value is not None and current.risk is not None
    assert current.value.reliance_version_id == refreshed_reliance.facts.version_id
    assert current.risk.reliance_version_id == fx.source.risk.reliance_version_id
    assert current.integration is not None
    assert current.integration.version_ids == (successor_integration.facts.version_id,)
    assert current.decision is not None
    assert current.decision.version_ids == (successor_authorization.facts.decision_version_id,)
    comparison = service.compare(prior, current)
    changed = {item.component: item.changed for item in comparison.changes}
    assert changed["value"]
    assert not changed["risk"]
    assert changed["integration"] and changed["decision"]
    assert not comparison.value_risk_netted
    assert not comparison.decision_quality_inferred
    audit = service.decision_audit(
        principal_id="principal:slice-c",
        actor_id=source.actor_a,
        prior=prior,
        current=current,
    )
    assert successor_proposal.facts.version_id in audit.successor_decision_version_ids
    with sqlite_store.read_transaction() as tx:  # type: ignore[attr-defined]
        assert tx.get_version(fx.integration_version_id) is not None
        assert tx.get_version(fx.decision_version_id) is not None
