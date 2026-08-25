from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

import pytest

from paim.application import Increment3ApplicationService
from paim.application.practitioner import PractitionerQueryService
from paim.assessment_review import AssessmentLane
from paim.audit import ActorResolution
from paim.domain import AuthorityVersionInput, CommandMeta
from paim.integrity import CommandId, EffectiveInterval, FixedClock, RecordId, RecordVersionId
from paim.integrity.semantics import SemanticContractRef
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
) -> EstablishComparabilityCommand:
    accountability = fx.responsibilities[ObligationKind.ESTABLISH_QUANTITATIVE_COMPARABILITY]
    return EstablishComparabilityCommand(
        identity(fx.actor_id, key),
        ComparabilityFacts.new(),
        CONTRACT,
        fx.context,
        fx.case_id,
        fx.configuration_version_id,
        left,
        right,
        ComparisonState.COMPARABLE,
        "Practitioner confirms the same bounded construct, cohort, method, basis, and horizon.",
        accountability.responsibility_version_id,
        accountability.assignment_version_id,
        fx.authority_id,
        None,
        NOW,
        KNOWN,
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
    expected_version = sqlite_store.get_version(expected.facts.version_id)  # type: ignore[attr-defined]
    assert expected_version is not None
    highlights = PractitionerQueryService(sqlite_store).quantitative_highlights(  # type: ignore[arg-type]
        visible_claims=(expected_version,), effective_at=NOW, known_at=KNOWN
    )
    assert len(highlights) == 1
    assert highlights[0].supplied_value == "12.30"
    assert not highlights[0].judgment_established
    assert not highlights[0].ranking_inferred
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
