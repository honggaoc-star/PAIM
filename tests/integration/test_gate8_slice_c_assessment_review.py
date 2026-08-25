from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import timedelta

import pytest
from alembic import command as alembic_command

from paim.application import Increment3ApplicationService
from paim.assessment_review import (
    AdequacyFacts,
    AdequacyOutcome,
    AssessmentContent,
    AssessmentLane,
    AssessmentReviewAccessDenied,
    AssessmentReviewConflict,
    AssessmentReviewService,
    CandidateDisposition,
    CommandIdentity,
    CompleteReviewCommand,
    DesignateRelianceCommand,
    DetermineAdequacyCommand,
    FinishAssessmentCommand,
    FinishFacts,
    RelianceFacts,
    ReviewSelectionKind,
)
from paim.audit import ActorResolution
from paim.case_continuity import CaseContinuityService
from paim.domain import (
    ApplicabilityOutcome,
    ApplicabilityTargetType,
    CommandMeta,
    EvidenceApplicabilityVersionInput,
    EvidenceAttention,
    EvidenceClassification,
    EvidenceVersionInput,
)
from paim.integrity import (
    CommandId,
    EffectiveInterval,
    FixedClock,
    RecordId,
    RecordVersionId,
)
from paim.integrity.semantics import SemanticContractRef
from paim.integrity.time import to_epoch_microseconds
from paim.practitioner_queries import CaseView, HomeView, PractitionerQueryService
from paim.responsibility.models import ObligationKind, responsibility_signature
from paim.responsibility.service import ProjectionFact, ResponsibilityWorkService
from tests.integration.test_gate8_slice_a_responsibility_work import (
    CONTRACT as RESPONSIBILITY_CONTRACT,
)
from tests.integration.test_gate8_slice_a_responsibility_work import (
    assignment_command,
    authority_source,
    basis_command,
)
from tests.integration.test_gate8_slice_a_responsibility_work import (
    command as slice_a_command,
)
from tests.integration.test_gate8_slice_b_case_continuity import (
    NOW,
    RECORDED,
    ExactAccess,
    opening,
)
from tests.integration.test_migration_and_schema import alembic_config

CONTRACT = SemanticContractRef("paim.assessment-review", "1.0")
DECISION_USE = "bounded operating decision"
ASSESSED_SCOPE = "exact governed service"
KNOWLEDGE = RECORDED + timedelta(seconds=2)


@dataclass(frozen=True)
class ResponsibilityBasis:
    responsibility_version_id: RecordVersionId
    assignment_version_id: RecordVersionId


@dataclass(frozen=True)
class Fixture:
    service: AssessmentReviewService
    access: ExactAccess
    actor_a: RecordId
    actor_b: RecordId
    opened: object
    information_basis: tuple[RecordVersionId, ...]
    responsibilities: dict[tuple[AssessmentLane, str], ResponsibilityBasis]


class SelectiveSourceAccess(ExactAccess):
    def __init__(self, hidden_versions: frozenset[RecordVersionId] = frozenset()) -> None:
        super().__init__()
        self.hidden_versions = hidden_versions

    def authorize(
        self,
        *,
        case_id: RecordId,
        source_version_id: RecordVersionId | None = None,
        **_: object,
    ) -> bool:
        return case_id not in self.hidden and (
            source_version_id is None or source_version_id not in self.hidden_versions
        )


def meta(key: str, actor_id: RecordId) -> CommandMeta:
    return CommandMeta(
        CommandId.new(),
        "gate8-slice-c",
        key,
        "principal:slice-c",
        str(actor_id),
        ActorResolution.PROVIDED,
    )


def establish_responsibility(
    store: object,
    *,
    case_id: RecordId,
    actor_id: RecordId,
    assigned_actor_id: RecordId,
    context: object,
    obligation: ObligationKind,
    key: str,
) -> ResponsibilityBasis:
    exact_context = context
    signature = responsibility_signature(
        contract=RESPONSIBILITY_CONTRACT,
        obligation_kind=obligation,
        owning_case_id=case_id,
        context=exact_context,  # type: ignore[arg-type]
        purpose="prospective-assessment-review",
        use=DECISION_USE,
        scope=ASSESSED_SCOPE,
    )
    responsibility = slice_a_command(
        case_id=case_id,
        actor_id=actor_id,
        exact_context=exact_context,  # type: ignore[arg-type]
        family="responsibility",
        key=f"{key}-responsibility",
        projections=(),
    )
    responsibility = replace(
        responsibility,
        effective_at=NOW,
        content={
            "purpose_discriminator": "prospective-assessment-review",
            "use_discriminator": DECISION_USE,
            "scope_discriminator": ASSESSED_SCOPE,
        },
        projections=(
            ProjectionFact("responsibility_records", {"record_id": str(responsibility.record_id)}),
            ProjectionFact(
                "responsibility_versions",
                {
                    "version_id": str(responsibility.version_id),
                    "record_id": str(responsibility.record_id),
                    "obligation_kind": obligation.value,
                    "owning_case_id": str(case_id),
                    "context_digest": exact_context.digest,  # type: ignore[attr-defined]
                    "signature_digest": signature,
                },
            ),
        ),
    )
    service = ResponsibilityWorkService(
        store,
        FixedClock(RECORDED + timedelta(seconds=2)),
        ExactAccess(),  # type: ignore[arg-type]
    )
    service.commit(responsibility)
    source = authority_source(
        store,  # type: ignore[arg-type]
        case_id=case_id,
        assigning_actor_id=actor_id,
        exact_context=exact_context,  # type: ignore[arg-type]
        signature_digest=signature,
        obligation=obligation.value,
    )
    basis = basis_command(
        case_id=case_id,
        assigning_actor_id=actor_id,
        exact_context=exact_context,  # type: ignore[arg-type]
        source_version_id=source,
        obligation=obligation.value,
        signature_digest=signature,
        key=f"{key}-basis",
    )
    basis_version = dict(basis.projections[-1].values)
    basis_version["effective_from_us"] = to_epoch_microseconds(NOW)
    basis = replace(
        basis,
        effective_at=NOW,
        projections=(
            basis.projections[0],
            ProjectionFact("assignment_basis_versions", basis_version),
        ),
    )
    service.commit(basis)
    assignment = assignment_command(
        case_id=case_id,
        assigning_actor_id=actor_id,
        assigned_actor_id=assigned_actor_id,
        exact_context=exact_context,  # type: ignore[arg-type]
        responsibility=responsibility,
        signature_digest=signature,
        basis=basis,
        key=f"{key}-assignment",
    )
    assignment_version = dict(assignment.projections[-1].values)
    assignment_version["effective_from_us"] = to_epoch_microseconds(NOW)
    assignment = replace(
        assignment,
        effective_at=NOW,
        projections=(
            assignment.projections[0],
            ProjectionFact("responsibility_assignment_versions", assignment_version),
        ),
    )
    service.commit(assignment)
    return ResponsibilityBasis(responsibility.version_id, assignment.version_id)


def fixture(store: object, key: str = "vertical") -> Fixture:
    actor_a, _ = __import__(
        "tests.integration.test_increment_2_foundation", fromlist=["add_actor"]
    ).add_actor(store, f"slice-c-{key}-a")
    actor_b, _ = __import__(
        "tests.integration.test_increment_2_foundation", fromlist=["add_actor"]
    ).add_actor(store, f"slice-c-{key}-b")
    opened, _ = opening(store, actor_a, f"slice-c-{key}")
    access = ExactAccess()
    CaseContinuityService(store, FixedClock(RECORDED), access).open_case(opened)
    inc3 = Increment3ApplicationService(store, FixedClock(RECORDED + timedelta(seconds=1)))
    evidence_id, evidence_version = RecordId.new(), RecordVersionId.new()
    inc3.commit_evidence(
        meta(f"{key}-evidence", actor_a),
        EvidenceVersionInput(
            evidence_id,
            evidence_version,
            opened.facts.case_id,
            opened.facts.configuration_id,
            opened.facts.configuration_version_id,
            EvidenceClassification.OBSERVED,
            "bounded-source:v1",
            {"source_version": "v1"},
            {"fact": "material bounded information"},
            NOW - timedelta(days=1),
            EffectiveInterval(NOW),
            EvidenceAttention.CURRENT,
        ),
    )
    applicability_id, applicability_version = RecordId.new(), RecordVersionId.new()
    inc3.commit_evidence_applicability(
        meta(f"{key}-applicability", actor_a),
        EvidenceApplicabilityVersionInput(
            applicability_id,
            applicability_version,
            evidence_id,
            evidence_version,
            ApplicabilityTargetType.MANAGED_CONFIGURATION_VERSION,
            str(opened.facts.configuration_id),
            opened.facts.configuration_version_id,
            DECISION_USE,
            ASSESSED_SCOPE,
            opened.facts.case_id,
            opened.facts.configuration_id,
            opened.facts.configuration_version_id,
            ApplicabilityOutcome.APPLICABLE,
            (),
            (),
            "material information applies to the exact bounded use",
            actor_a,
            None,
            "prospective assessment information board",
            EffectiveInterval(NOW),
        ),
    )
    obligations = {
        (AssessmentLane.VALUE, "finish"): (ObligationKind.FINISH_VALUE_ASSESSMENT, actor_a),
        (AssessmentLane.VALUE, "adequacy"): (
            ObligationKind.REVIEW_VALUE_ASSESSMENT_ADEQUACY,
            actor_a,
        ),
        (AssessmentLane.VALUE, "reliance"): (
            ObligationKind.DESIGNATE_VALUE_ASSESSMENT_RELIANCE,
            actor_a,
        ),
        (AssessmentLane.RISK, "finish"): (ObligationKind.FINISH_RISK_ASSESSMENT, actor_a),
        (AssessmentLane.RISK, "adequacy"): (
            ObligationKind.REVIEW_RISK_ASSESSMENT_ADEQUACY,
            actor_a,
        ),
        (AssessmentLane.RISK, "reliance"): (
            ObligationKind.DESIGNATE_RISK_ASSESSMENT_RELIANCE,
            actor_b,
        ),
    }
    responsibilities = {
        slot: establish_responsibility(
            store,
            case_id=opened.facts.case_id,
            actor_id=actor_a,
            assigned_actor_id=assigned,
            context=opened.context,
            obligation=obligation,
            key=f"{key}-{slot[0].value}-{slot[1]}",
        )
        for slot, (obligation, assigned) in obligations.items()
    }
    return Fixture(
        AssessmentReviewService(store, FixedClock(RECORDED + timedelta(seconds=3)), access),
        access,
        actor_a,
        actor_b,
        opened,
        (evidence_version, applicability_version),
        responsibilities,
    )


def identity(actor: RecordId, key: str) -> CommandIdentity:
    return CommandIdentity(CommandId.new(), "gate8-slice-c", key, "principal:slice-c", actor)


def finish_command(fx: Fixture, lane: AssessmentLane, key: str) -> FinishAssessmentCommand:
    basis = fx.responsibilities[(lane, "finish")]
    return FinishAssessmentCommand(
        identity(fx.actor_a, key),
        FinishFacts.new(),
        CONTRACT,
        fx.opened.context,  # type: ignore[attr-defined]
        lane,
        fx.opened.facts.case_id,  # type: ignore[attr-defined]
        fx.opened.facts.configuration_version_id,  # type: ignore[attr-defined]
        AssessmentContent(
            f"{lane.value} conclusion, preserved independently",
            ASSESSED_SCOPE,
            "material uncertainty remains explicit",
            f"{lane.value} implication only",
            "exact bounded information basis",
        ),
        DECISION_USE,
        ASSESSED_SCOPE,
        fx.information_basis,
        basis.responsibility_version_id,
        basis.assignment_version_id,
        None,
        "producer confirms completion for independent review",
        ("bounded uncertainty remains",),
        NOW,
        KNOWLEDGE,
    )


def adequacy_command(
    fx: Fixture,
    finish: FinishAssessmentCommand,
    key: str,
    *,
    outcome: AdequacyOutcome = AdequacyOutcome.ADEQUATE,
) -> DetermineAdequacyCommand:
    basis = fx.responsibilities[(finish.lane, "adequacy")]
    return DetermineAdequacyCommand(
        identity(fx.actor_a, key),
        AdequacyFacts.new(),
        CONTRACT,
        finish.context,
        finish.lane,
        finish.case_id,
        finish.configuration_version_id,
        finish.facts.assessment_version_id,
        finish.facts.readiness_version_id,
        DECISION_USE,
        ASSESSED_SCOPE,
        fx.information_basis,
        outcome,
        () if outcome is AdequacyOutcome.ADEQUATE else ("material use limitation",),
        "neutral suitability judgment; not endorsement or acceptable-Risk judgment",
        ("bounded uncertainty remains",),
        "uncertainty was reviewed explicitly",
        basis.responsibility_version_id,
        basis.assignment_version_id,
        None,
        NOW,
        KNOWLEDGE,
    )


def reliance_command(
    fx: Fixture,
    finish: FinishAssessmentCommand,
    adequacy: DetermineAdequacyCommand,
    key: str,
    actor: RecordId,
) -> DesignateRelianceCommand:
    basis = fx.responsibilities[(finish.lane, "reliance")]
    return DesignateRelianceCommand(
        identity(actor, key),
        RelianceFacts.new(),
        CONTRACT,
        finish.context,
        finish.lane,
        finish.case_id,
        finish.configuration_version_id,
        finish.facts.assessment_version_id,
        finish.facts.readiness_version_id,
        adequacy.facts.version_id,
        DECISION_USE,
        ASSESSED_SCOPE,
        fx.information_basis,
        (),
        "explicitly designate this exact adequate assessment for the bounded use",
        basis.responsibility_version_id,
        basis.assignment_version_id,
        None,
        NOW,
        KNOWLEDGE,
    )


def practitioner_views(
    store: object, fx: Fixture, access: ExactAccess
) -> tuple[CaseView, HomeView]:
    queries = PractitionerQueryService(
        store,  # type: ignore[arg-type]
        CaseContinuityService(
            store,
            FixedClock(RECORDED + timedelta(seconds=5)),
            access,  # type: ignore[arg-type]
        ),
        access,
    )
    case = queries.case(
        principal_id="principal:slice-c",
        actor_id=fx.actor_a,
        case_id=fx.opened.facts.case_id,  # type: ignore[attr-defined]
        effective_at=NOW,
        known_at=RECORDED + timedelta(seconds=5),
    )
    home = queries.home(
        principal_id="principal:slice-c",
        actor_id=fx.actor_a,
        candidate_case_ids=(fx.opened.facts.case_id,),  # type: ignore[attr-defined]
        effective_at=NOW,
        known_at=RECORDED + timedelta(seconds=5),
    )
    return case, home


def test_two_lane_vertical_combined_and_separate_actor_paths(sqlite_store: object) -> None:
    fx = fixture(sqlite_store)
    value = finish_command(fx, AssessmentLane.VALUE, "value-finish")
    first = fx.service.finish_assessment(value)
    assert fx.service.finish_assessment(value) == first
    assert sqlite_store.count_rows("assessment_adequacy_versions") == 0  # type: ignore[attr-defined]
    assert sqlite_store.count_rows("assessment_reliance_versions") == 0  # type: ignore[attr-defined]
    value_adequacy = adequacy_command(fx, value, "value-review")
    value_reliance = reliance_command(fx, value, value_adequacy, "value-review", fx.actor_a)
    value_reliance = replace(value_reliance, identity=value_adequacy.identity)
    fx.service.complete_review(CompleteReviewCommand(value_adequacy, value_reliance))
    assert (
        fx.service.select_reliance(
            lane=AssessmentLane.VALUE,
            case_id=value.case_id,
            configuration_version_id=value.configuration_version_id,
            decision_use=DECISION_USE,
            effective_at=NOW,
            known_at=RECORDED + timedelta(seconds=4),
        ).kind
        is ReviewSelectionKind.ONE
    )
    assert (
        fx.service.select_reliance(
            lane=AssessmentLane.RISK,
            case_id=value.case_id,
            configuration_version_id=value.configuration_version_id,
            decision_use=DECISION_USE,
            effective_at=NOW,
            known_at=RECORDED + timedelta(seconds=4),
        ).kind
        is ReviewSelectionKind.ABSENT
    )

    risk = finish_command(fx, AssessmentLane.RISK, "risk-finish")
    fx.service.finish_assessment(risk)
    risk_adequacy = adequacy_command(fx, risk, "risk-adequacy")
    fx.service.determine_adequacy(risk_adequacy)
    risk_reliance = reliance_command(fx, risk, risk_adequacy, "risk-reliance", fx.actor_b)
    fx.service.designate_reliance(risk_reliance)
    assert sqlite_store.count_rows("assessment_readiness_versions") == 2  # type: ignore[attr-defined]
    assert sqlite_store.count_rows("assessment_adequacy_versions") == 2  # type: ignore[attr-defined]
    assert sqlite_store.count_rows("assessment_reliance_versions") == 2  # type: ignore[attr-defined]
    assert sqlite_store.count_rows("integration_versions") == 0  # type: ignore[attr-defined]
    assert sqlite_store.count_rows("decision_versions") == 0  # type: ignore[attr-defined]


@pytest.mark.parametrize("outcome", (AdequacyOutcome.NOT_ADEQUATE, AdequacyOutcome.INDETERMINATE))
def test_adverse_adequacy_never_creates_reliance_or_other_lane_result(
    sqlite_store: object, outcome: AdequacyOutcome
) -> None:
    fx = fixture(sqlite_store, f"adverse-{outcome.value.casefold()}")
    risk = finish_command(fx, AssessmentLane.RISK, "adverse-risk-finish")
    fx.service.finish_assessment(risk)
    adverse = adequacy_command(fx, risk, "adverse-risk-adequacy", outcome=outcome)
    fx.service.determine_adequacy(adverse)
    before = sqlite_store.count_rows("record_versions")  # type: ignore[attr-defined]
    with pytest.raises(AssessmentReviewConflict, match="positive adequacy"):
        fx.service.designate_reliance(
            reliance_command(fx, risk, adverse, "adverse-risk-reliance", fx.actor_b)
        )
    assert sqlite_store.count_rows("record_versions") == before  # type: ignore[attr-defined]
    assert sqlite_store.count_rows("assessment_reliance_versions") == 0  # type: ignore[attr-defined]
    assert sqlite_store.count_rows("assessment_candidate_versions") == 1  # type: ignore[attr-defined]


def test_combined_review_is_atomic_replay_safe_and_rejects_mismatch(
    sqlite_store: object,
) -> None:
    fx = fixture(sqlite_store, "combined-guards")
    value = finish_command(fx, AssessmentLane.VALUE, "combined-value-finish")
    fx.service.finish_assessment(value)
    adequacy = adequacy_command(fx, value, "combined-value-review")
    reliance = replace(
        reliance_command(fx, value, adequacy, "combined-value-review", fx.actor_a),
        identity=adequacy.identity,
    )
    wrong_reliance = replace(
        reliance,
        responsibility_version_id=fx.responsibilities[
            (AssessmentLane.RISK, "reliance")
        ].responsibility_version_id,
        assignment_version_id=fx.responsibilities[
            (AssessmentLane.RISK, "reliance")
        ].assignment_version_id,
    )
    before = sqlite_store.count_rows("record_versions")  # type: ignore[attr-defined]
    with pytest.raises(AssessmentReviewConflict, match="accountability"):
        fx.service.complete_review(CompleteReviewCommand(adequacy, wrong_reliance))
    assert sqlite_store.count_rows("record_versions") == before  # type: ignore[attr-defined]
    assert sqlite_store.count_rows("assessment_adequacy_versions") == 0  # type: ignore[attr-defined]
    assert sqlite_store.count_rows("assessment_reliance_versions") == 0  # type: ignore[attr-defined]

    outcome = fx.service.complete_review(CompleteReviewCommand(adequacy, reliance))
    assert fx.service.complete_review(CompleteReviewCommand(adequacy, reliance)) == outcome
    before_mismatch = sqlite_store.count_rows("record_versions")  # type: ignore[attr-defined]
    with pytest.raises(AssessmentReviewConflict, match="IDEMPOTENCY KEY REUSE CONFLICT"):
        fx.service.complete_review(
            CompleteReviewCommand(
                replace(adequacy, rationale="changed adequacy rationale"), reliance
            )
        )
    assert sqlite_store.count_rows("record_versions") == before_mismatch  # type: ignore[attr-defined]
    assert sqlite_store.count_rows("assessment_adequacy_versions") == 1  # type: ignore[attr-defined]
    assert sqlite_store.count_rows("assessment_reliance_versions") == 1  # type: ignore[attr-defined]


def test_multiple_adequate_candidates_require_dispositions_and_can_conflict(
    sqlite_store: object,
) -> None:
    fx = fixture(sqlite_store, "candidate-choice")
    first = finish_command(fx, AssessmentLane.VALUE, "candidate-first-finish")
    second = finish_command(fx, AssessmentLane.VALUE, "candidate-second-finish")
    fx.service.finish_assessment(first)
    fx.service.finish_assessment(second)
    first_adequacy = adequacy_command(fx, first, "candidate-first-adequacy")
    second_adequacy = adequacy_command(fx, second, "candidate-second-adequacy")
    fx.service.determine_adequacy(first_adequacy)
    fx.service.determine_adequacy(second_adequacy)

    choose_first = reliance_command(fx, first, first_adequacy, "candidate-choose-first", fx.actor_a)
    before = sqlite_store.count_rows("record_versions")  # type: ignore[attr-defined]
    with pytest.raises(AssessmentReviewConflict, match="competing adequate candidate"):
        fx.service.designate_reliance(choose_first)
    assert sqlite_store.count_rows("record_versions") == before  # type: ignore[attr-defined]
    choose_first = replace(
        choose_first,
        candidate_dispositions=(
            CandidateDisposition(
                second.facts.assessment_version_id,
                "NOT_SELECTED_FOR_THIS_USE",
                "the first exact candidate is designated for this bounded use",
            ),
        ),
    )
    fx.service.designate_reliance(choose_first)
    assert (
        fx.service.select_reliance(
            lane=AssessmentLane.VALUE,
            case_id=first.case_id,
            configuration_version_id=first.configuration_version_id,
            decision_use=DECISION_USE,
            effective_at=NOW,
            known_at=RECORDED + timedelta(seconds=4),
        ).kind
        is ReviewSelectionKind.ONE
    )

    choose_second = replace(
        reliance_command(fx, second, second_adequacy, "candidate-choose-second", fx.actor_a),
        candidate_dispositions=(
            CandidateDisposition(
                first.facts.assessment_version_id,
                "NOT_SELECTED_FOR_THIS_USE",
                "the second exact candidate is designated for this bounded use",
            ),
        ),
    )
    fx.service.designate_reliance(choose_second)
    selected = fx.service.select_reliance(
        lane=AssessmentLane.VALUE,
        case_id=first.case_id,
        configuration_version_id=first.configuration_version_id,
        decision_use=DECISION_USE,
        effective_at=NOW,
        known_at=RECORDED + timedelta(seconds=4),
    )
    assert selected.kind is ReviewSelectionKind.CONFLICT
    assert set(selected.version_ids) == {
        choose_first.facts.version_id,
        choose_second.facts.version_id,
    }


def test_correction_preserves_history_and_stale_relied_basis_never_retargets(
    sqlite_store: object,
) -> None:
    fx = fixture(sqlite_store, "correction")
    value = finish_command(fx, AssessmentLane.VALUE, "correction-value-finish")
    fx.service.finish_assessment(value)
    adequacy = adequacy_command(fx, value, "correction-value-review")
    reliance = replace(
        reliance_command(fx, value, adequacy, "correction-value-review", fx.actor_a),
        identity=adequacy.identity,
    )
    fx.service.complete_review(CompleteReviewCommand(adequacy, reliance))
    successor = replace(
        finish_command(fx, AssessmentLane.VALUE, "correction-value-successor"),
        facts=FinishFacts.new(value.facts.assessment_record_id),
        expected_assessment_version_id=value.facts.assessment_version_id,
        content=replace(value.content, finding="materially corrected Value conclusion"),
    )
    fx.service.finish_assessment(successor)
    before = sqlite_store.count_rows("record_versions")  # type: ignore[attr-defined]
    with pytest.raises(AssessmentReviewConflict, match="assessment candidate is stale"):
        fx.service.designate_reliance(
            replace(
                reliance,
                identity=identity(fx.actor_a, "stale-reliance-attempt"),
                facts=RelianceFacts.new(),
            )
        )
    assert sqlite_store.count_rows("record_versions") == before  # type: ignore[attr-defined]
    history = sqlite_store.get_history(value.facts.assessment_record_id)  # type: ignore[attr-defined]
    assert {item.version_id for item in history.versions} == {
        value.facts.assessment_version_id,
        successor.facts.assessment_version_id,
    }
    assert (
        sqlite_store.get_version(value.facts.assessment_version_id).content["finding"]
        != (  # type: ignore[attr-defined,union-attr]
            sqlite_store.get_version(successor.facts.assessment_version_id).content["finding"]  # type: ignore[attr-defined,union-attr]
        )
    )
    assert (
        fx.service.select_reliance(
            lane=AssessmentLane.VALUE,
            case_id=value.case_id,
            configuration_version_id=value.configuration_version_id,
            decision_use=DECISION_USE,
            effective_at=NOW,
            known_at=RECORDED + timedelta(seconds=4),
        ).kind
        is ReviewSelectionKind.ABSENT
    )
    successor_adequacy = adequacy_command(fx, successor, "correction-successor-complete-review")
    successor_reliance = replace(
        reliance_command(
            fx,
            successor,
            successor_adequacy,
            "correction-successor-complete-review",
            fx.actor_a,
        ),
        identity=successor_adequacy.identity,
    )
    fx.service.complete_review(CompleteReviewCommand(successor_adequacy, successor_reliance))
    selected = fx.service.select_reliance(
        lane=AssessmentLane.VALUE,
        case_id=value.case_id,
        configuration_version_id=value.configuration_version_id,
        decision_use=DECISION_USE,
        effective_at=NOW,
        known_at=RECORDED + timedelta(seconds=4),
    )
    assert selected.kind is ReviewSelectionKind.ONE
    assert selected.version_ids == (successor_reliance.facts.version_id,)
    assert selected.assessment_version_id == successor.facts.assessment_version_id
    restarted = AssessmentReviewService(
        sqlite_store,
        FixedClock(RECORDED + timedelta(seconds=5)),
        fx.access,  # type: ignore[arg-type]
    )
    assert (
        restarted.select_reliance(
            lane=AssessmentLane.VALUE,
            case_id=value.case_id,
            configuration_version_id=value.configuration_version_id,
            decision_use=DECISION_USE,
            effective_at=NOW,
            known_at=RECORDED + timedelta(seconds=5),
        )
        == selected
    )
    restarted_case = PractitionerQueryService(
        sqlite_store,  # type: ignore[arg-type]
        CaseContinuityService(
            sqlite_store,
            FixedClock(RECORDED + timedelta(seconds=5)),
            fx.access,  # type: ignore[arg-type]
        ),
        fx.access,
    ).case(
        principal_id="principal:slice-c",
        actor_id=fx.actor_a,
        case_id=value.case_id,
        effective_at=NOW,
        known_at=RECORDED + timedelta(seconds=5),
    )
    assert restarted_case.value_position is not None
    assert restarted_case.value_position.assessment == "PRESENT"
    assert restarted_case.value_position.reliance == "RELIED"
    assert successor_reliance.facts.version_id in (restarted_case.value_position.source_version_ids)
    assert reliance.facts.version_id not in restarted_case.value_position.source_version_ids


def test_wrong_accountability_access_and_query_composition_fail_closed(
    sqlite_store: object,
) -> None:
    fx = fixture(sqlite_store, "guards")
    value = finish_command(fx, AssessmentLane.VALUE, "guard-value-finish")
    wrong = replace(
        value,
        assignment_version_id=fx.responsibilities[
            (AssessmentLane.RISK, "finish")
        ].assignment_version_id,
    )
    before = sqlite_store.count_rows("record_versions")  # type: ignore[attr-defined]
    with pytest.raises(AssessmentReviewConflict, match="accountability"):
        fx.service.finish_assessment(wrong)
    assert sqlite_store.count_rows("record_versions") == before  # type: ignore[attr-defined]
    hidden = ExactAccess(frozenset({value.case_id}))
    with pytest.raises(AssessmentReviewAccessDenied):
        AssessmentReviewService(
            sqlite_store,
            FixedClock(RECORDED + timedelta(seconds=3)),
            hidden,  # type: ignore[arg-type]
        ).finish_assessment(replace(value, identity=identity(fx.actor_a, "hidden")))
    fx.service.finish_assessment(value)
    queries = PractitionerQueryService(
        sqlite_store,  # type: ignore[arg-type]
        CaseContinuityService(sqlite_store, FixedClock(RECORDED + timedelta(seconds=3)), fx.access),
        fx.access,
    )
    case = queries.case(
        principal_id="principal:slice-c",
        actor_id=fx.actor_a,
        case_id=value.case_id,
        effective_at=NOW,
        known_at=RECORDED + timedelta(seconds=4),
    )
    assert case.value_position is not None
    assert case.value_position.readiness == "READY FOR INDEPENDENT REVIEW"
    assert case.risk_position is None
    home = queries.home(
        principal_id="principal:slice-c",
        actor_id=fx.actor_a,
        candidate_case_ids=(value.case_id,),
        effective_at=NOW,
        known_at=RECORDED + timedelta(seconds=4),
    )
    assert any(item.kind == "VALUE_REVIEW" for item in home.items)
    assert all(item.kind != "VALUE_ASSESSMENT" for item in home.items)
    hidden_home = PractitionerQueryService(
        sqlite_store,  # type: ignore[arg-type]
        queries._continuity,  # type: ignore[attr-defined]
        hidden,
    ).home(
        principal_id="principal:slice-c",
        actor_id=fx.actor_a,
        candidate_case_ids=(value.case_id,),
        effective_at=NOW,
        known_at=RECORDED + timedelta(seconds=4),
    )
    assert hidden_home.items == ()
    assert hidden_home.visible_case_ids == ()


def test_finish_requires_exact_complete_information_applicability_basis(
    sqlite_store: object,
) -> None:
    fx = fixture(sqlite_store, "prerequisite-guards")
    value = finish_command(fx, AssessmentLane.VALUE, "missing-applicability")
    incomplete = replace(value, information_basis_version_ids=(fx.information_basis[0],))
    before = sqlite_store.count_rows("record_versions")  # type: ignore[attr-defined]
    with pytest.raises(AssessmentReviewConflict, match="Applicability prerequisite"):
        fx.service.finish_assessment(incomplete)
    assert sqlite_store.count_rows("record_versions") == before  # type: ignore[attr-defined]
    assert sqlite_store.count_rows("assessment_candidate_versions") == 0  # type: ignore[attr-defined]
    assert sqlite_store.count_rows("assessment_readiness_versions") == 0  # type: ignore[attr-defined]


def test_selectively_hidden_slice_c_sources_are_filtered_before_composition(
    sqlite_store: object,
) -> None:
    fx = fixture(sqlite_store, "source-nondisclosure")
    initial_case, initial_home = practitioner_views(sqlite_store, fx, SelectiveSourceAccess())
    assert initial_case.value_position is None

    value = finish_command(fx, AssessmentLane.VALUE, "visible-value-finish")
    fx.service.finish_assessment(value)
    finished_case, finished_home = practitioner_views(sqlite_store, fx, SelectiveSourceAccess())
    assert finished_case.value_position is not None
    assert finished_case.value_position.readiness == "READY FOR INDEPENDENT REVIEW"
    assert any(item.kind == "VALUE_REVIEW" for item in finished_home.items)

    hidden_assessment_case, hidden_assessment_home = practitioner_views(
        sqlite_store,
        fx,
        SelectiveSourceAccess(frozenset({value.facts.assessment_version_id})),
    )
    assert hidden_assessment_case == initial_case
    assert hidden_assessment_home == initial_home

    hidden_readiness_case, hidden_readiness_home = practitioner_views(
        sqlite_store,
        fx,
        SelectiveSourceAccess(frozenset({value.facts.readiness_version_id})),
    )
    assert hidden_readiness_case.value_position is not None
    assert hidden_readiness_case.value_position.assessment == "PRESENT"
    assert hidden_readiness_case.value_position.readiness == "NOT ESTABLISHED"
    assert value.facts.readiness_version_id not in (
        hidden_readiness_case.value_position.source_version_ids
    )
    assert any(item.kind == "VALUE_ASSESSMENT" for item in hidden_readiness_home.items)
    assert all(item.kind != "VALUE_REVIEW" for item in hidden_readiness_home.items)

    adequacy = adequacy_command(fx, value, "visible-value-adequacy")
    fx.service.determine_adequacy(adequacy)
    adequate_case, adequate_home = practitioner_views(sqlite_store, fx, SelectiveSourceAccess())
    assert adequate_case.value_position is not None
    assert adequate_case.value_position.adequacy == "ADEQUATE"
    assert any(item.kind == "VALUE_RELIANCE" for item in adequate_home.items)
    hidden_adequacy_case, hidden_adequacy_home = practitioner_views(
        sqlite_store,
        fx,
        SelectiveSourceAccess(frozenset({adequacy.facts.version_id})),
    )
    assert hidden_adequacy_case == finished_case
    assert hidden_adequacy_home == finished_home

    reliance = reliance_command(fx, value, adequacy, "visible-value-reliance", fx.actor_a)
    fx.service.designate_reliance(reliance)
    relied_case, _relied_home = practitioner_views(sqlite_store, fx, SelectiveSourceAccess())
    assert relied_case.value_position is not None
    assert relied_case.value_position.reliance == "RELIED"
    assert practitioner_views(
        sqlite_store,
        fx,
        SelectiveSourceAccess(frozenset({value.facts.assessment_version_id})),
    ) == (initial_case, initial_home)
    assert practitioner_views(
        sqlite_store,
        fx,
        SelectiveSourceAccess(frozenset({value.facts.readiness_version_id})),
    ) == (hidden_readiness_case, hidden_readiness_home)
    assert practitioner_views(
        sqlite_store,
        fx,
        SelectiveSourceAccess(frozenset({adequacy.facts.version_id})),
    ) == (finished_case, finished_home)
    hidden_reliance_case, hidden_reliance_home = practitioner_views(
        sqlite_store,
        fx,
        SelectiveSourceAccess(frozenset({reliance.facts.version_id})),
    )
    assert hidden_reliance_case == adequate_case
    assert hidden_reliance_home == adequate_home

    for hidden_information_version in fx.information_basis:
        hidden_information_case, hidden_information_home = practitioner_views(
            sqlite_store,
            fx,
            SelectiveSourceAccess(frozenset({hidden_information_version})),
        )
        assert hidden_information_case == initial_case
        assert hidden_information_home == initial_home
        assert hidden_information_version not in (
            hidden_information_case.source_manifest.version_ids
        )

    finish_basis = fx.responsibilities[(AssessmentLane.VALUE, "finish")]
    hidden_responsibility_case, hidden_responsibility_home = practitioner_views(
        sqlite_store,
        fx,
        SelectiveSourceAccess(frozenset({finish_basis.responsibility_version_id})),
    )
    assert hidden_responsibility_case.value_position is None
    assert finish_basis.responsibility_version_id not in (
        hidden_responsibility_case.source_manifest.version_ids
    )
    assert all(not item.kind.startswith("VALUE_") for item in hidden_responsibility_home.items)
    with sqlite_store.read_transaction() as transaction:  # type: ignore[attr-defined]
        assignment_rows = transaction.projection_rows(
            "responsibility_assignment_versions",
            version_id=str(finish_basis.assignment_version_id),
        )
    assert len(assignment_rows) == 1
    assignment_basis_version_id = RecordVersionId.parse(
        str(assignment_rows[0]["assignment_basis_version_id"])
    )
    for hidden_accountability_version in (
        finish_basis.assignment_version_id,
        assignment_basis_version_id,
    ):
        hidden_basis_case, hidden_basis_home = practitioner_views(
            sqlite_store,
            fx,
            SelectiveSourceAccess(frozenset({hidden_accountability_version})),
        )
        assert hidden_basis_case.value_position is None
        assert hidden_accountability_version not in (hidden_basis_case.source_manifest.version_ids)
        assert all(not item.kind.startswith("VALUE_") for item in hidden_basis_home.items)

    before_hidden_work = practitioner_views(sqlite_store, fx, SelectiveSourceAccess())
    work = slice_a_command(
        case_id=value.case_id,
        actor_id=fx.actor_a,
        exact_context=value.context,
        family="case-work",
        key="hidden-source-work",
        projections=(),
    )
    work = replace(
        work,
        effective_at=NOW,
        content={
            "question": "Review the exact Value assessment basis.",
            "instruction": "Use only the visible exact governed context.",
        },
        projections=(
            ProjectionFact("case_work_records", {"record_id": str(work.record_id)}),
            ProjectionFact(
                "case_work_versions",
                {
                    "version_id": str(work.version_id),
                    "record_id": str(work.record_id),
                    "owning_case_id": str(value.case_id),
                    "context_digest": value.context.digest,
                    "responsibility_version_id": str(finish_basis.responsibility_version_id),
                    "assignment_version_id": str(finish_basis.assignment_version_id),
                    "requester_actor_id": str(fx.actor_a),
                    "assignee_actor_id": str(fx.actor_a),
                    "state": "READY",
                    "reason": "review exact prospective Value basis",
                    "prerequisites_json": "[]",
                    "expected_result_family": "prospective-assessment",
                    "due_at_us": None,
                    "result_version_id": None,
                    "return_context_digest": value.context.digest,
                    "predecessor_version_id": None,
                },
            ),
        ),
    )
    ResponsibilityWorkService(
        sqlite_store,
        FixedClock(RECORDED + timedelta(seconds=6)),
        ExactAccess(),  # type: ignore[arg-type]
    ).commit(work)
    hidden_work_views = practitioner_views(
        sqlite_store,
        fx,
        SelectiveSourceAccess(frozenset({work.version_id})),
    )
    assert hidden_work_views == before_hidden_work


def test_slice_c_schema_is_additive_append_only_and_not_backfilled(sqlite_store: object) -> None:
    tables = {
        "assessment_candidate_records",
        "assessment_candidate_versions",
        "assessment_readiness_records",
        "assessment_readiness_versions",
        "assessment_adequacy_records",
        "assessment_adequacy_versions",
        "assessment_reliance_records",
        "assessment_reliance_versions",
    }
    from sqlalchemy import inspect, text

    inspector = inspect(sqlite_store.engine)  # type: ignore[attr-defined]
    assert tables <= set(inspector.get_table_names())
    with sqlite_store.engine.connect() as connection:  # type: ignore[attr-defined]
        triggers = set(
            connection.execute(
                text("SELECT name FROM sqlite_master WHERE type = 'trigger'")
            ).scalars()
        )
        assert all(
            connection.execute(text(f"SELECT count(*) FROM {table}")).scalar_one() == 0
            for table in tables
        )
    for table in tables:
        assert f"prevent_{table}_update" in triggers
        assert f"prevent_{table}_delete" in triggers
    assert {
        item["name"] for item in inspector.get_check_constraints("assessment_adequacy_versions")
    } >= {"ck_assessment_adequacy_lane", "ck_assessment_adequacy_outcome"}


def test_slice_c_facts_prohibit_destructive_migration_downgrade(sqlite_store: object) -> None:
    fx = fixture(sqlite_store, "downgrade-guard")
    fx.service.finish_assessment(finish_command(fx, AssessmentLane.VALUE, "downgrade-guard-finish"))
    config = alembic_config(str(sqlite_store.engine.url))  # type: ignore[attr-defined]
    with pytest.raises(RuntimeError, match="destructive rollback is prohibited"):
        alembic_command.downgrade(config, "0011_gate8_case_continuity")
    with sqlite_store.engine.connect() as connection:  # type: ignore[attr-defined]
        assert connection.exec_driver_sql(
            "SELECT version_num FROM alembic_version"
        ).scalar_one() == ("0012_gate8_assessment_review")
