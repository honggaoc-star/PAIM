from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import timedelta

import pytest

from paim.application import Increment3ApplicationService
from paim.assessment_review import AssessmentLane, RelianceFacts
from paim.audit import ActorResolution
from paim.case_continuity.service import CaseContinuityService
from paim.continuing_review import (
    BeginReviewEpisodeCommand,
    CompleteReviewEpisodeCommand,
    ContinuingReviewConflict,
    ContinuingReviewService,
    EstablishPlannedReviewPointCommand,
    EstablishRequiredReviewConstraintCommand,
    PlannedReviewPointSpec,
    RecordEventReviewAttentionCommand,
    ReviewConstraintOperator,
    ReviewFocus,
    ReviewOrigin,
    ReviewOutcome,
    ReviewRecordFacts,
    ReviewSelectionKind,
)
from paim.domain import AuthorityVersionInput, CommandMeta
from paim.integrity import CommandId, EffectiveInterval, FixedClock, RecordId, RecordVersionId
from paim.integrity.semantics import SemanticContractRef
from paim.practitioner_queries import PractitionerQueryService
from paim.prospective_decision import (
    AuthorizationFacts,
    AuthorizeDecisionCommand,
    ConfirmationFacts,
    ConfirmDecisionCommand,
    IntegrationFacts,
    ProspectiveDecisionService,
    ReliedLaneBasis,
)
from paim.responsibility.models import ObligationKind
from tests.integration.test_gate8_slice_b_case_continuity import NOW, RECORDED
from tests.integration.test_gate8_slice_c_assessment_review import (
    ASSESSED_SCOPE,
    DECISION_USE,
    KNOWLEDGE,
    ResponsibilityBasis,
    SelectiveSourceAccess,
    adequacy_command,
    establish_responsibility,
    finish_command,
    identity,
    reliance_command,
)
from tests.integration.test_gate8_slice_d_integration_decision import (
    CONTRACT as DECISION_CONTRACT,
)
from tests.integration.test_gate8_slice_d_integration_decision import (
    SliceDFixture,
    integration_command,
    proposal_command,
    slice_d_fixture,
)

CONTRACT = SemanticContractRef("paim.continuing-review", "1.0")
REVIEW_PURPOSE = "continuing management review"


@dataclass(frozen=True)
class SliceEFixture:
    source: SliceDFixture
    service: ContinuingReviewService
    integration_version_id: RecordVersionId
    decision_version_id: RecordVersionId
    confirmation_record_id: RecordId
    responsibilities: dict[ObligationKind, ResponsibilityBasis]
    review_authority_version_id: RecordVersionId
    evidence_version_id: RecordVersionId
    applicability_version_id: RecordVersionId


def review_authority(store: object, fx: SliceDFixture, key: str) -> RecordVersionId:
    record_id, version_id = RecordId.new(), RecordVersionId.new()
    Increment3ApplicationService(
        store,  # type: ignore[arg-type]
        FixedClock(RECORDED + timedelta(seconds=6)),
    ).commit_authority_record(
        CommandMeta(
            CommandId.new(),
            "gate8-slice-e",
            key,
            "principal:slice-c",
            str(fx.source.actor_a),
            ActorResolution.PROVIDED,
        ),
        AuthorityVersionInput(
            record_id,
            version_id,
            fx.source.opened.facts.case_id,  # type: ignore[attr-defined]
            fx.source.opened.facts.configuration_id,  # type: ignore[attr-defined]
            fx.source.opened.facts.configuration_version_id,  # type: ignore[attr-defined]
            "prospective-review-authority",
            "bounded-review-charter",
            {"source": "fresh Slice-E vertical proof"},
            ASSESSED_SCOPE,
            "exact separate review timing authority",
            {
                "prospective_review_authority": {
                    "actor_id": str(fx.source.actor_a),
                    "allowed_actions": [
                        "ESTABLISH_REQUIRED_REVIEW_CONSTRAINT",
                        "WITHDRAW_REQUIRED_REVIEW_CONSTRAINT",
                        "CHANGE_DECISION_REVIEW_CONDITION",
                    ],
                    "allowed_case_ids": [
                        str(fx.source.opened.facts.case_id)  # type: ignore[attr-defined]
                    ],
                    "context_digest": fx.source.opened.context.digest,  # type: ignore[attr-defined]
                }
            },
            EffectiveInterval(NOW),
        ),
    )
    return version_id


def slice_e_fixture(store: object, key: str) -> SliceEFixture:
    fx = slice_d_fixture(store, key)
    integration = integration_command(fx, f"{key}-integration")
    fx.service.integrate_value_risk(integration)
    proposal = proposal_command(fx, integration, f"{key}-proposal")
    fx.service.propose_decision(proposal)
    authority = fx.responsibilities[ObligationKind.AUTHORIZE_MANAGEMENT_DECISION]
    authorize = AuthorizeDecisionCommand(
        identity(fx.source.actor_a, f"{key}-authorize"),
        AuthorizationFacts.new(),
        DECISION_CONTRACT,
        proposal.context,
        proposal.case_id,
        proposal.configuration_version_id,
        proposal.facts.version_id,
        integration.facts.version_id,
        DECISION_USE,
        ASSESSED_SCOPE,
        authority.responsibility_version_id,
        authority.assignment_version_id,
        fx.decision_authority,
        "bounded Decision Authority",
        ASSESSED_SCOPE,
        ("no broader use",),
        ("remain inside exact boundary",),
        (),
        NOW,
        KNOWLEDGE,
    )
    fx.service.authorize_decision(authorize)
    obligations = (
        ObligationKind.PLAN_NEXT_REVIEW,
        ObligationKind.NORMALIZE_REQUIRED_REVIEW_CONSTRAINT,
        ObligationKind.BEGIN_CONTINUING_REVIEW,
        ObligationKind.COMPLETE_CONTINUING_REVIEW,
    )
    responsibilities = {
        obligation: establish_responsibility(
            store,
            case_id=fx.source.opened.facts.case_id,  # type: ignore[attr-defined]
            actor_id=fx.source.actor_a,
            assigned_actor_id=fx.source.actor_a,
            context=fx.source.opened.context,  # type: ignore[attr-defined]
            obligation=obligation,
            key=f"{key}-{obligation.value}",
        )
        for obligation in obligations
    }
    evidence_version_id: RecordVersionId | None = None
    applicability_version_id: RecordVersionId | None = None
    with store.read_transaction() as tx:  # type: ignore[attr-defined]
        for version_id in fx.source.information_basis:
            rows = tx.projection_rows("evidence_applicability_versions", version_id=str(version_id))
            if rows:
                applicability_version_id = version_id
                evidence_version_id = RecordVersionId.parse(str(rows[0]["evidence_version_id"]))
    assert evidence_version_id is not None and applicability_version_id is not None
    return SliceEFixture(
        fx,
        ContinuingReviewService(
            store,  # type: ignore[arg-type]
            FixedClock(RECORDED + timedelta(seconds=8)),
            fx.source.access,
        ),
        integration.facts.version_id,
        authorize.facts.decision_version_id,
        authorize.facts.authorization_record_id,
        responsibilities,
        review_authority(store, fx, f"{key}-review-authority"),
        evidence_version_id,
        applicability_version_id,
    )


def planned_command(
    fx: SliceEFixture,
    key: str,
    *,
    review_at=NOW + timedelta(days=30),
) -> EstablishPlannedReviewPointCommand:
    accountability = fx.responsibilities[ObligationKind.PLAN_NEXT_REVIEW]
    source = fx.source.source
    return EstablishPlannedReviewPointCommand(
        identity(source.actor_a, key),
        CONTRACT,
        source.opened.context,  # type: ignore[attr-defined]
        source.opened.facts.case_id,  # type: ignore[attr-defined]
        source.opened.facts.configuration_version_id,  # type: ignore[attr-defined]
        fx.decision_version_id,
        REVIEW_PURPOSE,
        ASSESSED_SCOPE,
        PlannedReviewPointSpec(
            ReviewRecordFacts.new(),
            review_at,
            "practitioner selected the next bounded review point",
            (fx.decision_version_id,),
        ),
        accountability.responsibility_version_id,
        accountability.assignment_version_id,
        None,
        False,
        NOW,
        KNOWLEDGE,
    )


def constraint_command(
    fx: SliceEFixture,
    key: str,
    operator: ReviewConstraintOperator,
    start,
    end,
) -> EstablishRequiredReviewConstraintCommand:
    accountability = fx.responsibilities[ObligationKind.NORMALIZE_REQUIRED_REVIEW_CONSTRAINT]
    source = fx.source.source
    return EstablishRequiredReviewConstraintCommand(
        identity(source.actor_a, key),
        ReviewRecordFacts.new(),
        CONTRACT,
        source.opened.context,  # type: ignore[attr-defined]
        source.opened.facts.case_id,  # type: ignore[attr-defined]
        source.opened.facts.configuration_version_id,  # type: ignore[attr-defined]
        fx.decision_version_id,
        REVIEW_PURPOSE,
        ASSESSED_SCOPE,
        fx.evidence_version_id,
        fx.review_authority_version_id,
        fx.applicability_version_id,
        operator,
        start,
        end,
        ("exact governed service only",),
        "normalize one exact applicable governing review requirement",
        accountability.responsibility_version_id,
        accountability.assignment_version_id,
        None,
        None,
        NOW,
        KNOWLEDGE,
    )


def test_planned_and_required_timing_remain_separate_and_attention_is_non_substantive(
    sqlite_store: object,
) -> None:
    fx = slice_e_fixture(sqlite_store, "timing")
    plan = planned_command(fx, "timing-plan")
    fx.service.establish_planned_review_point(plan)
    not_before = constraint_command(
        fx,
        "timing-not-before",
        ReviewConstraintOperator.NOT_BEFORE,
        NOW + timedelta(days=20),
        None,
    )
    by = constraint_command(
        fx,
        "timing-by",
        ReviewConstraintOperator.BY,
        None,
        NOW + timedelta(days=60),
    )
    fx.service.establish_required_review_constraint(not_before)
    fx.service.establish_required_review_constraint(by)

    source = fx.source.source
    query = {
        "principal_id": "principal:slice-c",
        "actor_id": source.actor_a,
        "case_id": source.opened.facts.case_id,  # type: ignore[attr-defined]
        "configuration_version_id": source.opened.facts.configuration_version_id,  # type: ignore[attr-defined]
        "decision_version_id": fx.decision_version_id,
        "context": source.opened.context,  # type: ignore[attr-defined]
        "review_purpose": REVIEW_PURPOSE,
        "bounded_scope": ASSESSED_SCOPE,
        "effective_at": NOW,
        "known_at": RECORDED + timedelta(seconds=9),
    }
    selected_plan = fx.service.select_planned_review_point(**query)
    required = fx.service.required_review_window(**query)
    attention = fx.service.review_attention(**query)
    assert selected_plan.kind is ReviewSelectionKind.ONE
    assert selected_plan.version_ids == (plan.spec.facts.version_id,)
    assert required.kind is ReviewSelectionKind.ONE
    assert required.window_start == NOW + timedelta(days=20)
    assert required.window_end == NOW + timedelta(days=60)
    assert set(required.constraint_version_ids) == {
        not_before.facts.version_id,
        by.facts.version_id,
    }
    assert not attention.due
    assert not attention.substantive_change_inferred
    assert not attention.priority_inferred
    due = fx.service.review_attention(**{**query, "effective_at": NOW + timedelta(days=31)})
    assert due.due and due.kinds == ("PLANNED REVIEW DUE",)
    with sqlite_store.read_transaction() as tx:  # type: ignore[attr-defined]
        assert tx.count_rows("trigger_versions") == 0
        assert tx.count_rows("reassessment_versions") == 0
        assert tx.count_rows("assessment_candidate_versions") == 2
        assert tx.count_rows("prospective_decision_versions") == 2

    impossible = constraint_command(
        fx,
        "timing-impossible-by",
        ReviewConstraintOperator.BY,
        None,
        NOW + timedelta(days=10),
    )
    fx.service.establish_required_review_constraint(impossible)
    conflict = fx.service.required_review_window(**query)
    assert conflict.kind is ReviewSelectionKind.CONFLICT
    assert conflict.reason == "REQUIRED REVIEW TIMING CONFLICT — UNRESOLVED"


def test_practitioner_composition_filters_review_sources_before_dates_and_attention(
    sqlite_store: object,
) -> None:
    fx = slice_e_fixture(sqlite_store, "composition")
    plan = planned_command(fx, "composition-plan", review_at=NOW + timedelta(days=5))
    constraint = constraint_command(
        fx,
        "composition-constraint",
        ReviewConstraintOperator.BY,
        None,
        NOW + timedelta(days=40),
    )
    fx.service.establish_planned_review_point(plan)
    fx.service.establish_required_review_constraint(constraint)
    source = fx.source.source

    def compose(hidden: frozenset[RecordVersionId]) -> tuple[object, object]:
        access = SelectiveSourceAccess(hidden)
        queries = PractitionerQueryService(
            sqlite_store,  # type: ignore[arg-type]
            CaseContinuityService(
                sqlite_store,  # type: ignore[arg-type]
                FixedClock(RECORDED + timedelta(seconds=10)),
                access,
            ),
            access,
        )
        common = {
            "principal_id": "principal:slice-c",
            "actor_id": source.actor_a,
            "effective_at": NOW + timedelta(days=6),
            "known_at": RECORDED + timedelta(seconds=10),
        }
        case = queries.case(
            **common,
            case_id=source.opened.facts.case_id,  # type: ignore[attr-defined]
        )
        home = queries.home(
            **common,
            candidate_case_ids=(source.opened.facts.case_id,),  # type: ignore[attr-defined]
        )
        return case, home

    visible_case, visible_home = compose(frozenset())
    review = visible_case.continuing_review_position  # type: ignore[attr-defined]
    assert review is not None
    assert review.planned_state == "PLANNED"
    assert review.next_planned_review_at == NOW + timedelta(days=5)
    assert review.required_state == "EXACT MECHANICAL CONSTRAINT INTERSECTION"
    assert review.required_window_end == NOW + timedelta(days=40)
    assert review.attention_reasons == ("The visible planned review point is due.",)
    assert any(item.kind == "CONTINUING_REVIEW" for item in visible_home.items)  # type: ignore[attr-defined]

    hidden_case, hidden_home = compose(frozenset({plan.spec.facts.version_id}))
    hidden = hidden_case.continuing_review_position  # type: ignore[attr-defined]
    assert hidden is not None
    assert hidden.planned_state == "STATUS NOT SAFELY AVAILABLE"
    assert hidden.next_planned_review_at is None
    assert hidden.attention_reasons == ()
    assert not any(item.kind == "CONTINUING_REVIEW" for item in hidden_home.items)  # type: ignore[attr-defined]
    assert str(plan.spec.facts.version_id) not in repr(hidden_case)
    assert str(plan.spec.facts.version_id) not in repr(hidden_home)


def test_planned_review_replay_mismatch_and_stale_successor_are_atomic(
    sqlite_store: object,
) -> None:
    fx = slice_e_fixture(sqlite_store, "plan-integrity")
    first = planned_command(fx, "plan-integrity-first")
    first_outcome = fx.service.establish_planned_review_point(first)
    assert fx.service.establish_planned_review_point(first) == first_outcome
    with sqlite_store.read_transaction() as tx:  # type: ignore[attr-defined]
        before = tx.count_rows("planned_review_point_versions")
    mismatch = replace(
        first,
        spec=replace(first.spec, rationale="same key with a materially different payload"),
    )
    with pytest.raises(ContinuingReviewConflict, match="IDEMPOTENCY KEY REUSE CONFLICT"):
        fx.service.establish_planned_review_point(mismatch)
    with sqlite_store.read_transaction() as tx:  # type: ignore[attr-defined]
        assert tx.count_rows("planned_review_point_versions") == before

    successor_template = planned_command(
        fx,
        "plan-integrity-successor",
        review_at=NOW + timedelta(days=45),
    )
    successor = replace(
        successor_template,
        spec=replace(
            successor_template.spec,
            facts=ReviewRecordFacts.new(first.spec.facts.record_id),
            predecessor_version_id=first.spec.facts.version_id,
            expected_current_version_id=first.spec.facts.version_id,
        ),
    )
    later = ContinuingReviewService(
        sqlite_store,  # type: ignore[arg-type]
        FixedClock(RECORDED + timedelta(seconds=9)),
        fx.source.source.access,
    )
    successor_outcome = later.establish_planned_review_point(successor)
    assert successor_outcome.relationship_ids
    stale_template = planned_command(
        fx,
        "plan-integrity-stale",
        review_at=NOW + timedelta(days=60),
    )
    stale = replace(
        stale_template,
        spec=replace(
            stale_template.spec,
            facts=ReviewRecordFacts.new(first.spec.facts.record_id),
            predecessor_version_id=first.spec.facts.version_id,
            expected_current_version_id=first.spec.facts.version_id,
        ),
    )
    with pytest.raises(ContinuingReviewConflict, match="stale exact review predecessor"):
        later.establish_planned_review_point(stale)
    with sqlite_store.read_transaction() as tx:  # type: ignore[attr-defined]
        assert tx.count_rows("planned_review_point_versions") == before + 1
        successor_rows = tx.projection_rows(
            "planned_review_point_versions", version_id=str(successor.spec.facts.version_id)
        )
        assert successor_rows[0]["predecessor_version_id"] == str(first.spec.facts.version_id)


def test_event_review_can_complete_with_exact_unchanged_decision_and_atomic_next_point(
    sqlite_store: object,
) -> None:
    fx = slice_e_fixture(sqlite_store, "unchanged")
    source = fx.source.source
    begin_basis = fx.responsibilities[ObligationKind.BEGIN_CONTINUING_REVIEW]
    event = RecordEventReviewAttentionCommand(
        identity(source.actor_a, "unchanged-event"),
        ReviewRecordFacts.new(),
        CONTRACT,
        source.opened.context,  # type: ignore[attr-defined]
        source.opened.facts.case_id,  # type: ignore[attr-defined]
        source.opened.facts.configuration_version_id,  # type: ignore[attr-defined]
        fx.decision_version_id,
        fx.evidence_version_id,
        REVIEW_PURPOSE,
        ASSESSED_SCOPE,
        (ReviewFocus.NO_SUBSTANTIVE_CHANGE,),
        "exact accepted information merits bounded review attention only",
        begin_basis.responsibility_version_id,
        begin_basis.assignment_version_id,
        NOW,
        KNOWLEDGE,
    )
    fx.service.record_event_review_attention(event)
    episode = BeginReviewEpisodeCommand(
        identity(source.actor_a, "unchanged-begin"),
        ReviewRecordFacts.new(),
        CONTRACT,
        source.opened.context,  # type: ignore[attr-defined]
        source.opened.facts.case_id,  # type: ignore[attr-defined]
        source.opened.facts.configuration_version_id,  # type: ignore[attr-defined]
        fx.decision_version_id,
        fx.integration_version_id,
        ReviewOrigin.EVENT_TRIGGER,
        (event.facts.version_id,),
        (ReviewFocus.NO_SUBSTANTIVE_CHANGE, ReviewFocus.DECISION_CONFIRMATION),
        fx.source.value.reliance_version_id,
        fx.source.risk.reliance_version_id,
        begin_basis.responsibility_version_id,
        begin_basis.assignment_version_id,
        None,
        NOW,
        KNOWLEDGE,
    )
    fx.service.begin_review_episode(episode)
    confirmation_basis = fx.source.responsibilities[ObligationKind.CONFIRM_MANAGEMENT_DECISION]
    confirmation = ConfirmDecisionCommand(
        identity(source.actor_a, "unchanged-confirm"),
        ConfirmationFacts.new(),
        DECISION_CONTRACT,
        source.opened.context,  # type: ignore[attr-defined]
        source.opened.facts.case_id,  # type: ignore[attr-defined]
        source.opened.facts.configuration_version_id,  # type: ignore[attr-defined]
        fx.decision_version_id,
        fx.integration_version_id,
        DECISION_USE,
        ASSESSED_SCOPE,
        "focused review found the exact authorized Decision remains unchanged",
        confirmation_basis.responsibility_version_id,
        confirmation_basis.assignment_version_id,
        fx.source.decision_authority,
        NOW,
        KNOWLEDGE,
    )
    ProspectiveDecisionService(
        sqlite_store,  # type: ignore[arg-type]
        FixedClock(RECORDED + timedelta(seconds=9)),
        source.access,
    ).confirm_decision(confirmation)
    completion_basis = fx.responsibilities[ObligationKind.COMPLETE_CONTINUING_REVIEW]
    planning_basis = fx.responsibilities[ObligationKind.PLAN_NEXT_REVIEW]
    next_point = PlannedReviewPointSpec(
        ReviewRecordFacts.new(),
        NOW + timedelta(days=90),
        "practitioner selected the next point after completing this review",
        (episode.facts.version_id, confirmation.facts.version_id),
    )
    complete = CompleteReviewEpisodeCommand(
        identity(source.actor_a, "unchanged-complete"),
        ReviewRecordFacts(episode.facts.record_id, RecordVersionId.new()),
        CONTRACT,
        source.opened.context,  # type: ignore[attr-defined]
        source.opened.facts.case_id,  # type: ignore[attr-defined]
        source.opened.facts.configuration_version_id,  # type: ignore[attr-defined]
        episode.facts.version_id,
        ReviewOutcome.UNCHANGED_DECISION_CONFIRMED,
        (),
        fx.source.value.reliance_version_id,
        fx.source.risk.reliance_version_id,
        confirmation.facts.version_id,
        None,
        "focused review completed without changing substantive management judgment",
        completion_basis.responsibility_version_id,
        completion_basis.assignment_version_id,
        next_point,
        planning_basis.responsibility_version_id,
        planning_basis.assignment_version_id,
        NOW,
        KNOWLEDGE,
    )
    completion_service = ContinuingReviewService(
        sqlite_store,  # type: ignore[arg-type]
        FixedClock(RECORDED + timedelta(seconds=10)),
        source.access,
    )
    outcome = completion_service.complete_review_episode(complete)
    assert completion_service.complete_review_episode(complete) == outcome
    current = completion_service.select_review_episode(
        principal_id="principal:slice-c",
        actor_id=source.actor_a,
        case_id=source.opened.facts.case_id,  # type: ignore[attr-defined]
        configuration_version_id=source.opened.facts.configuration_version_id,  # type: ignore[attr-defined]
        context=source.opened.context,  # type: ignore[attr-defined]
        effective_at=NOW,
        known_at=RECORDED + timedelta(seconds=11),
    )
    historical = completion_service.select_review_episode(
        principal_id="principal:slice-c",
        actor_id=source.actor_a,
        case_id=source.opened.facts.case_id,  # type: ignore[attr-defined]
        configuration_version_id=source.opened.facts.configuration_version_id,  # type: ignore[attr-defined]
        context=source.opened.context,  # type: ignore[attr-defined]
        effective_at=NOW,
        known_at=RECORDED + timedelta(seconds=9),
    )
    assert current.status == "COMPLETED"
    assert historical.status == "OPEN"
    next_selection = completion_service.select_planned_review_point(
        principal_id="principal:slice-c",
        actor_id=source.actor_a,
        case_id=source.opened.facts.case_id,  # type: ignore[attr-defined]
        configuration_version_id=source.opened.facts.configuration_version_id,  # type: ignore[attr-defined]
        decision_version_id=fx.decision_version_id,
        context=source.opened.context,  # type: ignore[attr-defined]
        review_purpose=REVIEW_PURPOSE,
        bounded_scope=ASSESSED_SCOPE,
        effective_at=NOW,
        known_at=RECORDED + timedelta(seconds=11),
    )
    assert next_selection.kind is ReviewSelectionKind.ONE
    assert next_selection.version_ids == (next_point.facts.version_id,)
    with sqlite_store.read_transaction() as tx:  # type: ignore[attr-defined]
        assert tx.count_rows("assessment_candidate_versions") == 2
        assert tx.count_rows("assessment_reliance_versions") == 2
        assert tx.count_rows("prospective_decision_versions") == 2
        assert tx.count_rows("prospective_decision_confirmation_versions") == 1
        assert tx.count_rows("planned_review_point_versions") == 1
        assert tx.count_rows("review_episode_versions") == 2


def test_focused_value_refresh_preserves_risk_and_requires_explicit_decision_successor(
    sqlite_store: object,
) -> None:
    fx = slice_e_fixture(sqlite_store, "changed")
    source = fx.source.source
    begin_basis = fx.responsibilities[ObligationKind.BEGIN_CONTINUING_REVIEW]
    event = RecordEventReviewAttentionCommand(
        identity(source.actor_a, "changed-event"),
        ReviewRecordFacts.new(),
        CONTRACT,
        source.opened.context,  # type: ignore[attr-defined]
        source.opened.facts.case_id,  # type: ignore[attr-defined]
        source.opened.facts.configuration_version_id,  # type: ignore[attr-defined]
        fx.decision_version_id,
        fx.evidence_version_id,
        REVIEW_PURPOSE,
        ASSESSED_SCOPE,
        (
            ReviewFocus.VALUE_REFRESH,
            ReviewFocus.ADEQUACY_RELIANCE_RECONSIDERATION,
            ReviewFocus.INTEGRATION_REFRESH,
            ReviewFocus.DECISION_SUCCESSOR,
        ),
        "new exact information affects Value only and creates review attention",
        begin_basis.responsibility_version_id,
        begin_basis.assignment_version_id,
        NOW,
        KNOWLEDGE,
    )
    fx.service.record_event_review_attention(event)
    episode = BeginReviewEpisodeCommand(
        identity(source.actor_a, "changed-begin"),
        ReviewRecordFacts.new(),
        CONTRACT,
        source.opened.context,  # type: ignore[attr-defined]
        source.opened.facts.case_id,  # type: ignore[attr-defined]
        source.opened.facts.configuration_version_id,  # type: ignore[attr-defined]
        fx.decision_version_id,
        fx.integration_version_id,
        ReviewOrigin.EVENT_TRIGGER,
        (event.facts.version_id,),
        event.affected_focus,
        fx.source.value.reliance_version_id,
        fx.source.risk.reliance_version_id,
        begin_basis.responsibility_version_id,
        begin_basis.assignment_version_id,
        None,
        NOW,
        KNOWLEDGE,
    )
    fx.service.begin_review_episode(episode)

    with sqlite_store.read_transaction() as tx:  # type: ignore[attr-defined]
        prior_value = tx.get_version(fx.source.value.assessment_version_id)
        prior_reliance = tx.get_version(fx.source.value.reliance_version_id)
        before_risk = tx.count_rows("assessment_candidate_versions")
        assert prior_value is not None
        assert prior_reliance is not None
    finish_template = finish_command(source, AssessmentLane.VALUE, "changed-value-finish")
    refreshed_finish = replace(
        finish_template,
        facts=replace(finish_template.facts, assessment_record_id=prior_value.record_id),
        expected_assessment_version_id=fx.source.value.assessment_version_id,
    )
    refreshed_adequacy = adequacy_command(source, refreshed_finish, "changed-value-adequacy")
    reliance_template = reliance_command(
        source,
        refreshed_finish,
        refreshed_adequacy,
        "changed-value-reliance",
        source.actor_a,
    )
    refreshed_reliance = replace(
        reliance_template,
        facts=RelianceFacts.new(prior_reliance.record_id),
        expected_reliance_version_id=fx.source.value.reliance_version_id,
    )
    source.service.finish_assessment(refreshed_finish)
    source.service.determine_adequacy(refreshed_adequacy)
    source.service.designate_reliance(refreshed_reliance)
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
        FixedClock(RECORDED + timedelta(seconds=11)),
        source.access,
    )
    integration_template = integration_command(fx.source, "changed-new-integration")
    new_integration = replace(
        integration_template,
        facts=IntegrationFacts.new(),
        value_basis=refreshed_value,
        risk_basis=fx.source.risk,
    )
    prospective.integrate_value_risk(new_integration)
    successor_template = proposal_command(fx.source, new_integration, "changed-successor-proposal")
    successor_proposal = replace(
        successor_template,
        predecessor_decision_version_id=fx.decision_version_id,
        expected_current_decision_version_id=fx.decision_version_id,
    )
    prospective.propose_decision(successor_proposal)
    authority = fx.source.responsibilities[ObligationKind.AUTHORIZE_MANAGEMENT_DECISION]
    successor_authorization = AuthorizeDecisionCommand(
        identity(source.actor_a, "changed-successor-authorize"),
        AuthorizationFacts.new(),
        DECISION_CONTRACT,
        source.opened.context,  # type: ignore[attr-defined]
        source.opened.facts.case_id,  # type: ignore[attr-defined]
        source.opened.facts.configuration_version_id,  # type: ignore[attr-defined]
        successor_proposal.facts.version_id,
        new_integration.facts.version_id,
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

    completion_basis = fx.responsibilities[ObligationKind.COMPLETE_CONTINUING_REVIEW]
    complete = CompleteReviewEpisodeCommand(
        identity(source.actor_a, "changed-complete"),
        ReviewRecordFacts(episode.facts.record_id, RecordVersionId.new()),
        CONTRACT,
        source.opened.context,  # type: ignore[attr-defined]
        source.opened.facts.case_id,  # type: ignore[attr-defined]
        source.opened.facts.configuration_version_id,  # type: ignore[attr-defined]
        episode.facts.version_id,
        ReviewOutcome.SUCCESSOR_DECISION_PATH,
        (
            refreshed_finish.facts.assessment_version_id,
            refreshed_finish.facts.readiness_version_id,
            refreshed_adequacy.facts.version_id,
            refreshed_reliance.facts.version_id,
            new_integration.facts.version_id,
            successor_authorization.facts.decision_version_id,
        ),
        refreshed_reliance.facts.version_id,
        fx.source.risk.reliance_version_id,
        None,
        successor_authorization.facts.decision_version_id,
        "Value changed; Risk remained exact; management used an explicit successor path",
        completion_basis.responsibility_version_id,
        completion_basis.assignment_version_id,
        None,
        None,
        None,
        NOW,
        KNOWLEDGE,
    )
    ContinuingReviewService(
        sqlite_store,  # type: ignore[arg-type]
        FixedClock(RECORDED + timedelta(seconds=12)),
        source.access,
    ).complete_review_episode(complete)
    with sqlite_store.read_transaction() as tx:  # type: ignore[attr-defined]
        completed = tx.projection_rows(
            "review_episode_versions", version_id=str(complete.facts.version_id)
        )[0]
        assert completed["continued_value_reliance_version_id"] == str(
            refreshed_reliance.facts.version_id
        )
        assert completed["continued_risk_reliance_version_id"] == str(
            fx.source.risk.reliance_version_id
        )
        assert tx.count_rows("assessment_candidate_versions") == before_risk + 1
        assert tx.count_rows("prospective_decision_versions") == 4
        old_decision = tx.get_version(fx.decision_version_id)
        assert old_decision is not None
        assert old_decision.content["integration_version_id"] == str(fx.integration_version_id)
