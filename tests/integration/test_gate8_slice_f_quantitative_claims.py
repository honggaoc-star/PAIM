from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

import pytest

from paim.application import Increment3ApplicationService
from paim.application.practitioner import PractitionerQueryService
from paim.assessment_review import AssessmentLane
from paim.audit import ActorResolution
from paim.continuing_review import (
    BeginReviewEpisodeCommand,
    RecordEventReviewAttentionCommand,
    ReviewFocus,
    ReviewOrigin,
    ReviewRecordFacts,
)
from paim.domain import AuthorityVersionInput, CommandMeta
from paim.integrity import CommandId, EffectiveInterval, FixedClock, RecordId, RecordVersionId
from paim.integrity.semantics import (
    ContextMemberKind,
    ExactContextMember,
    ExactContextSet,
    SemanticContractRef,
)
from paim.quantitative_claims import (
    ClaimFacts,
    ComparabilityFacts,
    ComparisonState,
    EstablishComparabilityCommand,
    QuantitativeClaimCommand,
    QuantitativeClaimConflict,
    QuantitativeClaimService,
    QuantitativeClaimType,
    QuantityKind,
    QuantityRepresentation,
    QuantityValue,
    TemporalBasis,
)
from paim.responsibility.models import ObligationKind
from tests.integration.test_gate8_slice_b_case_continuity import NOW, RECORDED
from tests.integration.test_gate8_slice_c_assessment_review import (
    ASSESSED_SCOPE,
    ResponsibilityBasis,
    SelectiveSourceAccess,
    establish_responsibility,
    fixture,
    identity,
)
from tests.integration.test_gate8_slice_e_continuing_review import (
    REVIEW_PURPOSE,
    slice_e_fixture,
)

CONTRACT = SemanticContractRef("paim.quantitative-claims", "1.0")
KNOWN = RECORDED + timedelta(seconds=20)


def quantitative_authority(
    store: object,
    *,
    case_id: RecordId,
    configuration_id: RecordId,
    configuration_version_id: RecordVersionId,
    context_digest: str,
    actor_id: RecordId,
    key: str,
) -> RecordVersionId:
    record_id, version_id = RecordId.new(), RecordVersionId.new()
    Increment3ApplicationService(
        store, FixedClock(RECORDED + timedelta(seconds=10))
    ).commit_authority_record(  # type: ignore[arg-type]
        CommandMeta(
            CommandId.new(),
            "gate8-slice-f",
            key,
            "principal:slice-c",
            str(actor_id),
            ActorResolution.PROVIDED,
        ),
        AuthorityVersionInput(
            record_id,
            version_id,
            case_id,
            configuration_id,
            configuration_version_id,
            "quantitative-claim-authority",
            "bounded-quantitative-charter",
            {"source": "fresh disposable Slice-F proof"},
            ASSESSED_SCOPE,
            "separate authority for threshold and comparability judgments",
            {
                "quantitative_claim_authority": {
                    "actor_id": str(actor_id),
                    "allowed_actions": [
                        "AUTHOR_THRESHOLD_CONSTRAINT",
                        "SUPPORT_QUANTITATIVE_CLAIM",
                        "ESTABLISH_QUANTITATIVE_COMPARABILITY",
                    ],
                    "allowed_case_ids": [str(case_id)],
                    "context_digest": context_digest,
                }
            },
            EffectiveInterval(NOW),
        ),
    )
    return version_id


class SliceFFixture:
    def __init__(
        self, store: object, key: str, access: SelectiveSourceAccess | None = None
    ) -> None:
        self.base = fixture(store, key)
        self.access = access or SelectiveSourceAccess()
        self.service = QuantitativeClaimService(
            store,  # type: ignore[arg-type]
            FixedClock(KNOWN),
            self.access,
        )
        self.case_id = self.base.opened.facts.case_id  # type: ignore[attr-defined]
        self.configuration_id = self.base.opened.facts.configuration_id  # type: ignore[attr-defined]
        self.configuration_version_id = self.base.opened.facts.configuration_version_id  # type: ignore[attr-defined]
        self.context = self.base.opened.context  # type: ignore[attr-defined]
        self.actor_id = self.base.actor_a
        self.source_version_id, self.applicability_version_id = self.base.information_basis
        self.responsibilities = {
            obligation: establish_responsibility(
                store,
                case_id=self.case_id,
                actor_id=self.actor_id,
                assigned_actor_id=self.actor_id,
                context=self.context,
                obligation=obligation,
                key=f"{key}-{obligation.value}",
            )
            for obligation in (
                ObligationKind.AUTHOR_QUANTITATIVE_CLAIM,
                ObligationKind.ESTABLISH_QUANTITATIVE_COMPARABILITY,
            )
        }
        self.authority_id = quantitative_authority(
            store,
            case_id=self.case_id,
            configuration_id=self.configuration_id,
            configuration_version_id=self.configuration_version_id,
            context_digest=self.context.digest,
            actor_id=self.actor_id,
            key=f"{key}-authority",
        )


def claim_command(
    fx: SliceFFixture,
    key: str,
    claim_type: QuantitativeClaimType,
    value: str = "12.30",
    *,
    facts: ClaimFacts | None = None,
    expected: RecordVersionId | None = None,
    lane: AssessmentLane = AssessmentLane.VALUE,
    metric: str = "approval-turnaround",
    unit: str = "days",
    denominator: str | None = "per completed application",
    horizon: str = "first 90 days after launch",
    method: str = "controlled cohort method v1",
    authority: RecordVersionId | None = None,
) -> QuantitativeClaimCommand:
    accountability: ResponsibilityBasis = fx.responsibilities[
        ObligationKind.AUTHOR_QUANTITATIVE_CLAIM
    ]
    return QuantitativeClaimCommand(
        identity(fx.actor_id, key),
        facts or ClaimFacts.new(),
        CONTRACT,
        fx.context,
        fx.case_id,
        fx.configuration_version_id,
        lane,
        claim_type,
        "bounded-service-timeliness",
        metric,
        QuantityKind.CONTINUOUS_MEASURE,
        QuantityValue(QuantityRepresentation.SCALAR, central=value),
        unit,
        None,
        "one supplied decimal unit",
        "lower is faster; sign follows observed minus expected",
        "completed applications in bounded cohort",
        denominator,
        TemporalBasis.POINT_IN_TIME,
        NOW,
        None,
        horizon,
        "same bounded launch cohort",
        "gross",
        "not applicable",
        method,
        ("cohort definition remains stable",),
        "no probabilistic confidence asserted",
        ("local operational observation only",),
        (fx.source_version_id,),
        (fx.applicability_version_id,),
        None,
        None,
        authority,
        accountability.responsibility_version_id,
        accountability.assignment_version_id,
        expected,
        NOW,
        KNOWN,
    )


def comparability_command(
    fx: SliceFFixture,
    left: RecordVersionId,
    right: RecordVersionId,
    key: str,
    *,
    facts: ComparabilityFacts | None = None,
    outcome: ComparisonState = ComparisonState.COMPARABLE,
    expected: RecordVersionId | None = None,
) -> EstablishComparabilityCommand:
    accountability = fx.responsibilities[ObligationKind.ESTABLISH_QUANTITATIVE_COMPARABILITY]
    return EstablishComparabilityCommand(
        identity(fx.actor_id, key),
        facts or ComparabilityFacts.new(),
        CONTRACT,
        fx.context,
        fx.case_id,
        fx.configuration_version_id,
        left,
        right,
        outcome,
        "Practitioner confirms the same bounded construct, cohort, method, basis, and horizon.",
        accountability.responsibility_version_id,
        accountability.assignment_version_id,
        fx.authority_id,
        expected,
        NOW,
        KNOWN,
    )


def review_linked_fixture(
    store: object, key: str
) -> tuple[SliceFFixture, RecordVersionId, RecordVersionId, RecordVersionId]:
    review = slice_e_fixture(store, key)
    source = review.source.source
    begin_basis = review.responsibilities[ObligationKind.BEGIN_CONTINUING_REVIEW]
    event = RecordEventReviewAttentionCommand(
        identity(source.actor_a, f"{key}-event"),
        ReviewRecordFacts.new(),
        SemanticContractRef("paim.continuing-review", "1.0"),
        source.opened.context,  # type: ignore[attr-defined]
        source.opened.facts.case_id,  # type: ignore[attr-defined]
        source.opened.facts.configuration_version_id,  # type: ignore[attr-defined]
        review.decision_version_id,
        review.evidence_version_id,
        REVIEW_PURPOSE,
        ASSESSED_SCOPE,
        (ReviewFocus.VALUE_REFRESH,),
        "bounded quantitative source is explicitly admitted to review attention",
        begin_basis.responsibility_version_id,
        begin_basis.assignment_version_id,
        NOW,
        KNOWN,
    )
    review.service.record_event_review_attention(event)
    episode = BeginReviewEpisodeCommand(
        identity(source.actor_a, f"{key}-episode"),
        ReviewRecordFacts.new(),
        SemanticContractRef("paim.continuing-review", "1.0"),
        source.opened.context,  # type: ignore[attr-defined]
        source.opened.facts.case_id,  # type: ignore[attr-defined]
        source.opened.facts.configuration_version_id,  # type: ignore[attr-defined]
        review.decision_version_id,
        review.integration_version_id,
        ReviewOrigin.EVENT_TRIGGER,
        (event.facts.version_id,),
        (ReviewFocus.VALUE_REFRESH,),
        review.source.value.reliance_version_id,
        review.source.risk.reliance_version_id,
        begin_basis.responsibility_version_id,
        begin_basis.assignment_version_id,
        None,
        NOW,
        KNOWN,
    )
    review.service.begin_review_episode(episode)

    fx = object.__new__(SliceFFixture)
    fx.base = source
    fx.access = SelectiveSourceAccess()
    fx.case_id = source.opened.facts.case_id  # type: ignore[attr-defined]
    fx.configuration_id = source.opened.facts.configuration_id  # type: ignore[attr-defined]
    fx.configuration_version_id = source.opened.facts.configuration_version_id  # type: ignore[attr-defined]
    fx.context = source.opened.context  # type: ignore[attr-defined]
    fx.actor_id = source.actor_a
    fx.source_version_id = review.evidence_version_id
    fx.applicability_version_id = review.applicability_version_id
    fx.responsibilities = {
        obligation: establish_responsibility(
            store,
            case_id=fx.case_id,
            actor_id=fx.actor_id,
            assigned_actor_id=fx.actor_id,
            context=fx.context,
            obligation=obligation,
            key=f"{key}-{obligation.value}",
        )
        for obligation in (
            ObligationKind.AUTHOR_QUANTITATIVE_CLAIM,
            ObligationKind.ESTABLISH_QUANTITATIVE_COMPARABILITY,
        )
    }
    fx.authority_id = quantitative_authority(
        store,
        case_id=fx.case_id,
        configuration_id=fx.configuration_id,
        configuration_version_id=fx.configuration_version_id,
        context_digest=fx.context.digest,
        actor_id=fx.actor_id,
        key=f"{key}-quantitative-authority",
    )
    fx.service = QuantitativeClaimService(
        store,  # type: ignore[arg-type]
        FixedClock(KNOWN),
        fx.access,
    )
    return (
        fx,
        review.source.value.assessment_version_id,
        episode.facts.version_id,
        review.source.risk.assessment_version_id,
    )


def test_optional_typed_claims_preserve_precision_and_do_not_substitute_for_judgment(
    sqlite_store: object,
) -> None:
    fx = SliceFFixture(sqlite_store, "optional-six-types")
    before = {
        table: sqlite_store.count_rows(table)  # type: ignore[attr-defined]
        for table in (
            "assessment_adequacy_versions",
            "assessment_reliance_versions",
            "prospective_decision_versions",
        )
    }
    # The fresh Case and its qualitative assessment fixture existed with no claim: absence is valid.
    assert sqlite_store.count_rows("quantitative_claim_versions") == 0  # type: ignore[attr-defined]
    for index, claim_type in enumerate(QuantitativeClaimType):
        command = claim_command(
            fx,
            f"six-types-{index}",
            claim_type,
            value="12.30" if index == 0 else str(index + 1),
            metric=f"metric-{index}",
            lane=AssessmentLane.VALUE if index % 2 == 0 else AssessmentLane.RISK,
            authority=fx.authority_id
            if claim_type is QuantitativeClaimType.THRESHOLD_CONSTRAINT
            else None,
        )
        fx.service.record_claim(command)
    with sqlite_store.read_transaction() as tx:  # type: ignore[attr-defined]
        rows = tx.projection_rows("quantitative_claim_versions")
    assert {row["claim_type"] for row in rows} == {item.value for item in QuantitativeClaimType}
    assert rows[0]["central_value_text"] == "12.30"
    assert {row["lane"] for row in rows} == {"VALUE", "RISK"}
    assert before == {
        table: sqlite_store.count_rows(table)  # type: ignore[attr-defined]
        for table in before
    }


def test_expected_observed_requires_judgment_then_returns_exact_non_causal_arithmetic(
    sqlite_store: object,
) -> None:
    fx = SliceFFixture(sqlite_store, "expected-observed")
    expected = claim_command(fx, "expected", QuantitativeClaimType.ESTIMATE_EXPECTATION, "12.30")
    observed = claim_command(fx, "observed", QuantitativeClaimType.OBSERVED_RESULT, "10.20")
    fx.service.record_claim(expected)
    fx.service.record_claim(observed)
    with pytest.raises(QuantitativeClaimConflict, match="not knowable"):
        fx.service.compare(
            principal_id="principal:slice-c",
            actor_id=fx.actor_id,
            case_id=fx.case_id,
            left_claim_version_id=expected.facts.version_id,
            right_claim_version_id=observed.facts.version_id,
            effective_at=NOW,
            known_at=KNOWN - timedelta(microseconds=1),
        )
    population = fx.service.readable_claim_population(
        principal_id="principal:slice-c",
        actor_id=fx.actor_id,
        case_id=fx.case_id,
        claim_version_ids=(expected.facts.version_id,),
        effective_at=NOW,
        known_at=KNOWN,
    )
    highlights = PractitionerQueryService(sqlite_store).quantitative_highlights(  # type: ignore[arg-type]
        population=population, effective_at=NOW, known_at=KNOWN
    )
    assert highlights.state == "AVAILABLE"
    assert len(highlights.highlights) == 1
    assert highlights.highlights[0].supplied_value == "12.30"
    assert not highlights.highlights[0].judgment_established
    assert not highlights.highlights[0].ranking_inferred
    before = fx.service.compare(
        principal_id="principal:slice-c",
        actor_id=fx.actor_id,
        case_id=fx.case_id,
        left_claim_version_id=expected.facts.version_id,
        right_claim_version_id=observed.facts.version_id,
        effective_at=NOW,
        known_at=KNOWN,
    )
    assert before.state is ComparisonState.SUBSTANTIVE_COMPARABILITY_REQUIRES_JUDGMENT
    basis = comparability_command(
        fx, expected.facts.version_id, observed.facts.version_id, "confirm-comparable"
    )
    fx.service.establish_comparability(basis)
    result = fx.service.compare(
        principal_id="principal:slice-c",
        actor_id=fx.actor_id,
        case_id=fx.case_id,
        left_claim_version_id=expected.facts.version_id,
        right_claim_version_id=observed.facts.version_id,
        effective_at=NOW,
        known_at=KNOWN,
    )
    assert result.state is ComparisonState.COMPARABLE
    assert result.difference == "-2.10"
    assert result.ratio is not None and result.percentage_change is not None
    assert not result.causality_inferred
    assert not result.decision_quality_inferred
    assert not result.score_inferred


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ({"unit": "hours"}, "unit differs"),
        ({"denominator": "per approved application"}, "denominator differs"),
        ({"horizon": "first year after launch"}, "horizon differs"),
        ({"method": "uncontrolled survey"}, "method_id differs"),
    ],
)
def test_mismatch_blocks_arithmetic_without_label_only_equivalence(
    sqlite_store: object, change: dict[str, str], reason: str
) -> None:
    fx = SliceFFixture(sqlite_store, f"mismatch-{reason}")
    expected = claim_command(fx, "left", QuantitativeClaimType.ESTIMATE_EXPECTATION)
    observed = claim_command(
        fx,
        "right",
        QuantitativeClaimType.OBSERVED_RESULT,
        **change,  # type: ignore[arg-type]
    )
    fx.service.record_claim(expected)
    fx.service.record_claim(observed)
    result = fx.service.compare(
        principal_id="principal:slice-c",
        actor_id=fx.actor_id,
        case_id=fx.case_id,
        left_claim_version_id=expected.facts.version_id,
        right_claim_version_id=observed.facts.version_id,
        effective_at=NOW,
        known_at=KNOWN,
    )
    assert result.state is ComparisonState.MECHANICALLY_INCOMPATIBLE
    assert reason in result.reasons
    assert result.difference is result.ratio is result.percentage_change is None
    with pytest.raises(QuantitativeClaimConflict, match="mechanically incompatible"):
        fx.service.establish_comparability(
            comparability_command(
                fx, expected.facts.version_id, observed.facts.version_id, "invalid-basis"
            )
        )


def test_zero_baseline_history_replay_stale_write_and_hidden_source_are_fail_closed(
    sqlite_store: object,
) -> None:
    fx = SliceFFixture(sqlite_store, "history-access")
    original = claim_command(fx, "original", QuantitativeClaimType.ESTIMATE_EXPECTATION, "0.00")
    first = fx.service.record_claim(original)
    assert fx.service.record_claim(original) == first
    mismatch = replace(original, unit="hours")
    with pytest.raises(QuantitativeClaimConflict, match="IDEMPOTENCY"):
        fx.service.record_claim(mismatch)
    successor = claim_command(
        fx,
        "successor",
        QuantitativeClaimType.ESTIMATE_EXPECTATION,
        "1.00",
        facts=ClaimFacts(original.facts.record_id, RecordVersionId.new()),
        expected=original.facts.version_id,
    )
    fx.service.record_claim(successor)
    with pytest.raises(QuantitativeClaimConflict, match="stale exact"):
        fx.service.record_claim(
            replace(
                claim_command(
                    fx,
                    "stale",
                    QuantitativeClaimType.ESTIMATE_EXPECTATION,
                    "2.00",
                    facts=ClaimFacts(original.facts.record_id, RecordVersionId.new()),
                    expected=original.facts.version_id,
                )
            )
        )
    observed = claim_command(fx, "zero-observed", QuantitativeClaimType.OBSERVED_RESULT, "5.00")
    fx.service.record_claim(observed)
    basis = comparability_command(
        fx, successor.facts.version_id, observed.facts.version_id, "zero-comparable"
    )
    fx.service.establish_comparability(basis)
    zero_expected = claim_command(
        fx,
        "zero-current",
        QuantitativeClaimType.ESTIMATE_EXPECTATION,
        "0.00",
        metric="zero-baseline-metric",
    )
    zero_observed = claim_command(
        fx,
        "zero-current-observed",
        QuantitativeClaimType.OBSERVED_RESULT,
        "5.00",
        metric="zero-baseline-metric",
    )
    fx.service.record_claim(zero_expected)
    fx.service.record_claim(zero_observed)
    fx.service.establish_comparability(
        comparability_command(
            fx,
            zero_expected.facts.version_id,
            zero_observed.facts.version_id,
            "zero-current-comparable",
        )
    )
    zero_result = fx.service.compare(
        principal_id="principal:slice-c",
        actor_id=fx.actor_id,
        case_id=fx.case_id,
        left_claim_version_id=zero_expected.facts.version_id,
        right_claim_version_id=zero_observed.facts.version_id,
        effective_at=NOW,
        known_at=KNOWN,
    )
    assert zero_result.difference == "5.00"
    assert zero_result.ratio is None and zero_result.percentage_change is None
    # Historical original remains exact and later correction is not projected backward.
    history = sqlite_store.get_history(original.facts.record_id)  # type: ignore[attr-defined]
    assert {item.version_id for item in history.versions} == {
        original.facts.version_id,
        successor.facts.version_id,
    }
    assert any(
        relation.source_version_id == original.facts.version_id
        and relation.target_version_id == successor.facts.version_id
        for relation in history.relationships
    )
    hidden = QuantitativeClaimService(
        sqlite_store,  # type: ignore[arg-type]
        FixedClock(KNOWN),
        SelectiveSourceAccess(frozenset({fx.source_version_id})),
    )
    with pytest.raises(Exception, match="software access not established"):
        hidden.compare(
            principal_id="principal:slice-c",
            actor_id=fx.actor_id,
            case_id=fx.case_id,
            left_claim_version_id=successor.facts.version_id,
            right_claim_version_id=observed.facts.version_id,
            effective_at=NOW,
            known_at=KNOWN,
        )


def test_claim_successor_preserves_exact_semantic_identity_with_zero_mutation(
    sqlite_store: object,
) -> None:
    fx = SliceFFixture(sqlite_store, "successor-identity")
    original = claim_command(fx, "identity-original", QuantitativeClaimType.ESTIMATE_EXPECTATION)
    fx.service.record_claim(original)

    other_context = ExactContextSet.create(
        (
            ExactContextMember("case", ContextMemberKind.RECORD, str(fx.case_id)),
            ExactContextMember(
                "configuration_version",
                ContextMemberKind.VERSION,
                str(fx.configuration_version_id),
            ),
            ExactContextMember("bounded_use", ContextMemberKind.LITERAL, "different use"),
        )
    )
    mutations: tuple[dict[str, object], ...] = (
        {"lane": AssessmentLane.RISK},
        {"claim_type": QuantitativeClaimType.OBSERVED_RESULT},
        {"construct_id": "different-construct"},
        {"metric_id": "different-metric"},
        {"case_id": RecordId.new()},
        {"configuration_version_id": RecordVersionId.new()},
        {"context": other_context},
        {"facts": ClaimFacts.new()},
    )
    guarded_tables = (
        "records",
        "record_versions",
        "quantitative_claim_records",
        "quantitative_claim_versions",
        "status_events",
        "version_relationships",
        "audit_facts",
        "idempotency_facts",
    )
    for index, changes in enumerate(mutations):
        before = {
            table: sqlite_store.count_rows(table)  # type: ignore[attr-defined]
            for table in guarded_tables
        }
        replacement: dict[str, object] = {
            "identity": identity(fx.actor_id, f"identity-invalid-{index}"),
            "facts": ClaimFacts(original.facts.record_id, RecordVersionId.new()),
            "expected_current_version_id": original.facts.version_id,
        }
        replacement.update(changes)
        command = replace(original, **replacement)  # type: ignore[arg-type]
        with pytest.raises(QuantitativeClaimConflict, match=r"semantic identity|exact Record"):
            fx.service.record_claim(command)
        assert before == {
            table: sqlite_store.count_rows(table)  # type: ignore[attr-defined]
            for table in guarded_tables
        }

    correction = replace(
        original,
        identity=identity(fx.actor_id, "identity-valid-correction"),
        facts=ClaimFacts(original.facts.record_id, RecordVersionId.new()),
        quantity=QuantityValue(QuantityRepresentation.SCALAR, central="11.75"),
        uncertainty="corrected source transcription; no probabilistic confidence asserted",
        expected_current_version_id=original.facts.version_id,
    )
    fx.service.record_claim(correction)
    history = sqlite_store.get_history(original.facts.record_id)  # type: ignore[attr-defined]
    assert {item.version_id for item in history.versions} == {
        original.facts.version_id,
        correction.facts.version_id,
    }
    assert any(
        relation.source_version_id == original.facts.version_id
        and relation.target_version_id == correction.facts.version_id
        for relation in history.relationships
    )


def test_comparison_enforces_orientation_exact_pair_and_dual_time_basis(
    sqlite_store: object,
) -> None:
    fx = SliceFFixture(sqlite_store, "comparison-basis")
    expected = claim_command(
        fx, "basis-expected", QuantitativeClaimType.ESTIMATE_EXPECTATION, "10.00"
    )
    observed = claim_command(fx, "basis-observed", QuantitativeClaimType.OBSERVED_RESULT, "8.00")
    other_expected = claim_command(
        fx,
        "basis-other-expected",
        QuantitativeClaimType.ESTIMATE_EXPECTATION,
        "20.00",
        metric="other-metric",
    )
    other_observed = claim_command(
        fx,
        "basis-other-observed",
        QuantitativeClaimType.OBSERVED_RESULT,
        "19.00",
        metric="other-metric",
    )
    for command in (expected, observed, other_expected, other_observed):
        fx.service.record_claim(command)

    reversed_result = fx.service.compare(
        principal_id="principal:slice-c",
        actor_id=fx.actor_id,
        case_id=fx.case_id,
        left_claim_version_id=observed.facts.version_id,
        right_claim_version_id=expected.facts.version_id,
        effective_at=NOW,
        known_at=KNOWN,
    )
    assert reversed_result.state is ComparisonState.MECHANICALLY_INCOMPATIBLE
    assert "orientation requires" in reversed_result.reasons[-1]
    with pytest.raises(QuantitativeClaimConflict, match="mechanically incompatible"):
        fx.service.establish_comparability(
            comparability_command(
                fx,
                observed.facts.version_id,
                expected.facts.version_id,
                "reversed-basis",
            )
        )

    unrelated_basis = comparability_command(
        fx,
        other_expected.facts.version_id,
        other_observed.facts.version_id,
        "unrelated-basis",
    )
    fx.service.establish_comparability(unrelated_basis)
    no_wrong_pair_reuse = fx.service.compare(
        principal_id="principal:slice-c",
        actor_id=fx.actor_id,
        case_id=fx.case_id,
        left_claim_version_id=expected.facts.version_id,
        right_claim_version_id=observed.facts.version_id,
        effective_at=NOW,
        known_at=KNOWN,
    )
    assert no_wrong_pair_reuse.state is ComparisonState.SUBSTANTIVE_COMPARABILITY_REQUIRES_JUDGMENT

    first = comparability_command(
        fx, expected.facts.version_id, observed.facts.version_id, "current-basis"
    )
    fx.service.establish_comparability(first)
    successor = replace(
        first,
        identity=identity(fx.actor_id, "not-comparable-successor"),
        facts=ComparabilityFacts(first.facts.record_id, RecordVersionId.new()),
        outcome=ComparisonState.NOT_COMPARABLE,
        rationale="Later accountable review rejects substantive comparability.",
        expected_current_version_id=first.facts.version_id,
        knowledge_cutoff=KNOWN + timedelta(seconds=1),
    )
    later_service = QuantitativeClaimService(
        sqlite_store,  # type: ignore[arg-type]
        FixedClock(KNOWN + timedelta(seconds=1)),
        fx.access,
    )
    later_service.establish_comparability(successor)

    historical = fx.service.compare(
        principal_id="principal:slice-c",
        actor_id=fx.actor_id,
        case_id=fx.case_id,
        left_claim_version_id=expected.facts.version_id,
        right_claim_version_id=observed.facts.version_id,
        effective_at=NOW,
        known_at=KNOWN,
    )
    assert historical.state is ComparisonState.COMPARABLE
    assert historical.comparability_version_id == first.facts.version_id
    current = later_service.compare(
        principal_id="principal:slice-c",
        actor_id=fx.actor_id,
        case_id=fx.case_id,
        left_claim_version_id=expected.facts.version_id,
        right_claim_version_id=observed.facts.version_id,
        effective_at=NOW,
        known_at=KNOWN + timedelta(seconds=1),
    )
    assert current.state is ComparisonState.NOT_COMPARABLE
    assert current.comparability_version_id == successor.facts.version_id

    hidden_basis_service = QuantitativeClaimService(
        sqlite_store,  # type: ignore[arg-type]
        FixedClock(KNOWN + timedelta(seconds=1)),
        SelectiveSourceAccess(frozenset({fx.authority_id})),
    )
    with pytest.raises(Exception, match="software access not established"):
        hidden_basis_service.compare(
            principal_id="principal:slice-c",
            actor_id=fx.actor_id,
            case_id=fx.case_id,
            left_claim_version_id=expected.facts.version_id,
            right_claim_version_id=observed.facts.version_id,
            effective_at=NOW,
            known_at=KNOWN + timedelta(seconds=1),
        )


def test_complete_claim_source_closure_prevents_select_compare_and_highlight_leakage(
    sqlite_store: object,
) -> None:
    fx, assessment_id, episode_id, unrelated_id = review_linked_fixture(
        sqlite_store, "full-read-closure"
    )
    expected = replace(
        claim_command(
            fx,
            "closure-expected",
            QuantitativeClaimType.ESTIMATE_EXPECTATION,
            "14.00",
        ),
        assessment_version_id=assessment_id,
        review_episode_version_id=episode_id,
        authority_source_version_id=fx.authority_id,
    )
    observed = replace(
        claim_command(
            fx,
            "closure-observed",
            QuantitativeClaimType.OBSERVED_RESULT,
            "12.00",
        ),
        assessment_version_id=assessment_id,
        review_episode_version_id=episode_id,
        authority_source_version_id=fx.authority_id,
    )
    fx.service.record_claim(expected)
    fx.service.record_claim(observed)
    fx.service.establish_comparability(
        comparability_command(
            fx,
            expected.facts.version_id,
            observed.facts.version_id,
            "closure-comparability",
        )
    )
    author = fx.responsibilities[ObligationKind.AUTHOR_QUANTITATIVE_CLAIM]
    with sqlite_store.read_transaction() as tx:  # type: ignore[attr-defined]
        assignment = tx.projection_rows(
            "responsibility_assignment_versions",
            version_id=str(author.assignment_version_id),
        )[0]
        assignment_basis_id = RecordVersionId.parse(str(assignment["assignment_basis_version_id"]))
        assignment_basis = tx.projection_rows(
            "assignment_basis_versions", version_id=str(assignment_basis_id)
        )[0]
        assignment_authority_source_id = RecordVersionId.parse(
            str(assignment_basis["basis_source_version_id"])
        )

    selection_arguments = {
        "principal_id": "principal:slice-c",
        "actor_id": fx.actor_id,
        "case_id": fx.case_id,
        "configuration_version_id": fx.configuration_version_id,
        "context_digest": fx.context.digest,
        "lane": AssessmentLane.VALUE.value,
        "claim_type": QuantitativeClaimType.ESTIMATE_EXPECTATION.value,
        "construct_id": "bounded-service-timeliness",
        "metric_id": "approval-turnaround",
        "effective_at": NOW,
        "known_at": KNOWN,
    }
    comparison_arguments = {
        "principal_id": "principal:slice-c",
        "actor_id": fx.actor_id,
        "case_id": fx.case_id,
        "left_claim_version_id": expected.facts.version_id,
        "right_claim_version_id": observed.facts.version_id,
        "effective_at": NOW,
        "known_at": KNOWN,
    }
    population_arguments = {
        "principal_id": "principal:slice-c",
        "actor_id": fx.actor_id,
        "case_id": fx.case_id,
        "claim_version_ids": (expected.facts.version_id,),
        "effective_at": NOW,
        "known_at": KNOWN,
    }

    assert fx.service.select_claim(**selection_arguments).state == "ONE"  # type: ignore[arg-type]
    assert fx.service.compare(**comparison_arguments).state is ComparisonState.COMPARABLE  # type: ignore[arg-type]
    visible_population = fx.service.readable_claim_population(**population_arguments)  # type: ignore[arg-type]
    visible_highlights = PractitionerQueryService(sqlite_store).quantitative_highlights(  # type: ignore[arg-type]
        population=visible_population,
        effective_at=NOW,
        known_at=KNOWN,
    )
    assert visible_population.state == "AVAILABLE"
    assert visible_highlights.state == "AVAILABLE"
    assert len(visible_highlights.highlights) == 1
    assert visible_highlights.highlights[0].metric_label == "approval-turnaround"

    governed_sources = {
        "assessment": assessment_id,
        "review_episode": episode_id,
        "claim_authority": fx.authority_id,
        "responsibility": author.responsibility_version_id,
        "assignment": author.assignment_version_id,
        "assignment_basis": assignment_basis_id,
        "assignment_authority_source": assignment_authority_source_id,
    }
    for label, hidden_id in governed_sources.items():
        hidden_service = QuantitativeClaimService(
            sqlite_store,  # type: ignore[arg-type]
            FixedClock(KNOWN),
            SelectiveSourceAccess(frozenset({hidden_id})),
        )
        assert hidden_service.select_claim(**selection_arguments).state == (  # type: ignore[arg-type]
            "NOT_SAFELY_AVAILABLE"
        ), label
        with pytest.raises(Exception, match="software access not established"):
            hidden_service.compare(**comparison_arguments)  # type: ignore[arg-type]
        hidden_population = hidden_service.readable_claim_population(  # type: ignore[arg-type]
            **population_arguments
        )
        hidden_highlights = PractitionerQueryService(
            sqlite_store  # type: ignore[arg-type]
        ).quantitative_highlights(
            population=hidden_population,
            effective_at=NOW,
            known_at=KNOWN,
        )
        assert hidden_population.state == "NOT_SAFELY_AVAILABLE", label
        assert hidden_population.versions == (), label
        assert hidden_highlights.state == "NOT_SAFELY_AVAILABLE", label
        assert hidden_highlights.highlights == (), label

    unrelated_service = QuantitativeClaimService(
        sqlite_store,  # type: ignore[arg-type]
        FixedClock(KNOWN),
        SelectiveSourceAccess(frozenset({unrelated_id})),
    )
    assert unrelated_service.select_claim(**selection_arguments).state == "ONE"  # type: ignore[arg-type]
    assert unrelated_service.compare(**comparison_arguments).state is ComparisonState.COMPARABLE  # type: ignore[arg-type]
    unrelated_population = unrelated_service.readable_claim_population(  # type: ignore[arg-type]
        **population_arguments
    )
    assert unrelated_population.state == "AVAILABLE"
    assert len(unrelated_population.versions) == 1
