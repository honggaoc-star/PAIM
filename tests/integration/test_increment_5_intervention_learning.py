from __future__ import annotations

from dataclasses import dataclass, replace

import pytest

from paim.application import DomainRuleViolation, Increment5ApplicationService
from paim.domain import (
    ActivationAuthorityKind,
    ActivationRequest,
    AggregatePrerequisiteResult,
    CaseLifecycleState,
    CompletionAcceptanceOutcome,
    CompletionAcceptanceStatus,
    CompletionAcceptanceVersionInput,
    CompletionAcceptorMechanismVersionInput,
    CompletionCriterionResult,
    CompletionResultVersionInput,
    CriterionOutcome,
    DelegationEffect,
    EvidenceAttention,
    EvidenceClassification,
    EvidenceVersionInput,
    InterventionStatus,
    InterventionVersionInput,
    LearningItemVersionInput,
    LearningStatus,
    ObligationResult,
    ObligationSetVersionInput,
    ObligationVersionInput,
    PreauthorizedActivationMechanismInput,
    RequirementType,
    ReuseDeterminationVersionInput,
    RoleAssignmentVersionInput,
    RoleTargetType,
)
from paim.integrity import EffectiveInterval, FixedClock, RecordId, RecordVersionId
from paim.persistence.sqlite import SQLiteIntegrityStore
from tests.helpers import utc
from tests.integration.test_increment_3_foundation import meta
from tests.integration.test_increment_4_foundation import (
    EFFECTIVE,
    Foundation,
    authorization,
    foundation,
)

NOW = utc(2026, 2, 1)


@dataclass(frozen=True)
class Increment5Fixture:
    service: Increment5ApplicationService
    foundation: Foundation
    authorization_basis_version_id: RecordVersionId
    intervention_id: RecordId
    intervention_version_id: RecordVersionId
    obligation_set_version_id: RecordVersionId
    obligation_id: RecordId | None
    obligation_version_id: RecordVersionId | None
    acceptor_assignment_version_id: RecordVersionId | None
    evidence_version_id: RecordVersionId


def _setup(
    store: SQLiteIntegrityStore,
    key: str,
    *,
    requirement_type: RequirementType | None = RequirementType.REQUIRED_BEFORE_OPERATION,
    intervention_status: InterventionStatus = InterventionStatus.COMPLETED,
    acceptor_target: RoleTargetType | None = RoleTargetType.INTERVENTION,
    acceptor_effective: EffectiveInterval = EFFECTIVE,
    preauthorized: tuple[PreauthorizedActivationMechanismInput, ...] = (),
) -> Increment5Fixture:
    fx = foundation(store, key)
    service = Increment5ApplicationService(store, FixedClock(NOW))
    basis = replace(
        authorization(fx, key),
        preauthorized_activation_mechanisms=preauthorized,
    )
    service.authorize_decision(meta(f"{key}-authorize"), basis)

    intervention_id, intervention_version_id = RecordId.new(), RecordVersionId.new()
    service.commit_intervention(
        meta(f"{key}-intervention"),
        InterventionVersionInput(
            intervention_id,
            intervention_version_id,
            fx.context.case_id,
            fx.decision_version_id,
            fx.context.configuration_id,
            fx.context.configuration_version_id,
            fx.context.assessor_id,
            None,
            "governed:intervention-owner",
            intervention_status,
            "Bounded operating intervention",
            "exact authorized Decision and Configuration",
            {"source": "implementation-record"},
            ("control installed",),
            "suspend and remediate",
            EFFECTIVE,
        ),
    )

    assignment_version_id: RecordVersionId | None = None
    if acceptor_target is not None:
        target_id = {
            RoleTargetType.INTERVENTION: intervention_id,
            RoleTargetType.DECISION: fx.decision_id,
            RoleTargetType.CONFIGURATION: fx.context.configuration_id,
            RoleTargetType.CASE: fx.context.case_id,
        }[acceptor_target]
        assignment_id, assignment_version_id = RecordId.new(), RecordVersionId.new()
        service.commit_role_assignment(
            meta(f"{key}-acceptor"),
            RoleAssignmentVersionInput(
                assignment_id,
                assignment_version_id,
                fx.context.assessor_id,
                "Intervention Completion Acceptor",
                acceptor_target,
                str(target_id),
                fx.context.case_id,
                True,
                "completion-acceptance",
                DelegationEffect.NONE,
                None,
                acceptor_effective,
            ),
        )

    obligation_id: RecordId | None = None
    obligation_version_id: RecordVersionId | None = None
    obligations: tuple[ObligationVersionInput, ...] = ()
    if requirement_type is not None:
        obligation_id, obligation_version_id = RecordId.new(), RecordVersionId.new()
        obligations = (
            ObligationVersionInput(
                obligation_id,
                obligation_version_id,
                intervention_id,
                intervention_version_id,
                requirement_type,
                ("control installed",),
                (fx.clause_version_id,),
                ("bounded continuation only",),
                ("control:capacity",),
                ("do not exceed boundary",),
                "exact Decision prerequisite",
                {"source": "authorized-decision"},
                requirement_type is RequirementType.REQUIRED_AFTER_OPERATION,
                (
                    ("complete within 30 days",)
                    if requirement_type is RequirementType.REQUIRED_AFTER_OPERATION
                    else ()
                ),
            ),
        )
    obligation_set_id, obligation_set_version_id = RecordId.new(), RecordVersionId.new()
    service.commit_obligation_set(
        meta(f"{key}-obligation-set"),
        ObligationSetVersionInput(
            obligation_set_id,
            obligation_set_version_id,
            fx.decision_id,
            fx.decision_version_id,
            fx.context.case_id,
            fx.context.configuration_id,
            fx.context.configuration_version_id,
            obligations,
            "explicit activation prerequisite basis",
            EFFECTIVE,
        ),
    )

    evidence_id, evidence_version_id = RecordId.new(), RecordVersionId.new()
    service.commit_evidence(
        meta(f"{key}-evidence"),
        EvidenceVersionInput(
            evidence_id,
            evidence_version_id,
            fx.context.case_id,
            fx.context.configuration_id,
            fx.context.configuration_version_id,
            EvidenceClassification.OBSERVED,
            "completion-source:v1",
            {"source_version": "v1"},
            {"control_installed": True},
            utc(2026, 1, 15),
            EFFECTIVE,
            EvidenceAttention.CURRENT,
        ),
    )
    return Increment5Fixture(
        service,
        fx,
        basis.version_id,
        intervention_id,
        intervention_version_id,
        obligation_set_version_id,
        obligation_id,
        obligation_version_id,
        assignment_version_id,
        evidence_version_id,
    )


def _complete(
    value: Increment5Fixture,
    key: str,
    *,
    accept: bool = True,
    acceptance_status: CompletionAcceptanceStatus = CompletionAcceptanceStatus.CURRENT,
    mechanism_version_id: RecordVersionId | None = None,
) -> tuple[RecordVersionId, RecordVersionId]:
    assert value.obligation_version_id is not None
    result_id, result_version_id = RecordId.new(), RecordVersionId.new()
    value.service.commit_completion_result(
        meta(f"{key}-result"),
        CompletionResultVersionInput(
            result_id,
            result_version_id,
            value.obligation_version_id,
            value.intervention_version_id,
            value.foundation.decision_version_id,
            value.foundation.context.configuration_version_id,
            (CompletionCriterionResult("control installed", CriterionOutcome.MET, "verified"),),
            (value.evidence_version_id,),
            {"source": "completion-inspection"},
            value.foundation.context.assessor_id,
            (),
            None,
            None,
            EFFECTIVE,
        ),
    )
    acceptance_id, acceptance_version_id = RecordId.new(), RecordVersionId.new()
    value.service.commit_completion_acceptance(
        meta(f"{key}-acceptance"),
        CompletionAcceptanceVersionInput(
            acceptance_id,
            acceptance_version_id,
            value.obligation_version_id,
            value.intervention_version_id,
            result_version_id,
            value.foundation.decision_version_id,
            value.foundation.context.configuration_version_id,
            ("capacity boundary",),
            (
                CompletionAcceptanceOutcome.ACCEPTED
                if accept
                else CompletionAcceptanceOutcome.REJECTED
            ),
            "accountable assessment of the exact Completion Result",
            (),
            (),
            value.foundation.context.assessor_id,
            value.acceptor_assignment_version_id,
            mechanism_version_id,
            (),
            EFFECTIVE,
            status=acceptance_status,
        ),
    )
    return result_version_id, acceptance_version_id


def _successor_obligation(
    store: SQLiteIntegrityStore,
    value: Increment5Fixture,
    key: str,
    *,
    effective: EffectiveInterval,
) -> RecordVersionId:
    assert value.obligation_id is not None and value.obligation_version_id is not None
    prior_set = store.get_version(value.obligation_set_version_id)
    assert prior_set is not None
    successor_set_version_id = RecordVersionId.new()
    successor_obligation_version_id = RecordVersionId.new()
    value.service.commit_obligation_set(
        meta(f"{key}-successor-obligation-set"),
        ObligationSetVersionInput(
            prior_set.record_id,
            successor_set_version_id,
            value.foundation.decision_id,
            value.foundation.decision_version_id,
            value.foundation.context.case_id,
            value.foundation.context.configuration_id,
            value.foundation.context.configuration_version_id,
            (
                ObligationVersionInput(
                    value.obligation_id,
                    successor_obligation_version_id,
                    value.intervention_id,
                    value.intervention_version_id,
                    RequirementType.REQUIRED_BEFORE_OPERATION,
                    ("control installed",),
                    (value.foundation.clause_version_id,),
                    ("bounded continuation only",),
                    ("control:capacity",),
                    ("do not exceed boundary",),
                    "successor obligation requires explicit continued validity",
                    {"source": "successor-obligation"},
                    expected_version_id=value.obligation_version_id,
                    relationship_reason="successor obligation version",
                ),
            ),
            "successor obligation set",
            effective,
            expected_version_id=value.obligation_set_version_id,
            relationship_reason="successor obligation set version",
        ),
    )
    return successor_obligation_version_id


def _reuse(
    value: Increment5Fixture,
    key: str,
    *,
    successor_obligation_version_id: RecordVersionId,
    prior_result_version_id: RecordVersionId,
    prior_acceptance_version_id: RecordVersionId,
    effective: EffectiveInterval,
) -> RecordVersionId:
    assignment_id, assignment_version_id = RecordId.new(), RecordVersionId.new()
    value.service.commit_role_assignment(
        meta(f"{key}-continued-validity-acceptor"),
        RoleAssignmentVersionInput(
            assignment_id,
            assignment_version_id,
            value.foundation.context.assessor_id,
            "Continued Validity Acceptor",
            RoleTargetType.CASE,
            str(value.foundation.context.case_id),
            value.foundation.context.case_id,
            True,
            "continued-validity",
            DelegationEffect.NONE,
            None,
            effective,
        ),
    )
    determination_id, determination_version_id = RecordId.new(), RecordVersionId.new()
    value.service.commit_reuse_determination(
        meta(f"{key}-continued-validity"),
        ReuseDeterminationVersionInput(
            determination_id,
            determination_version_id,
            successor_obligation_version_id,
            prior_result_version_id,
            prior_acceptance_version_id,
            value.foundation.context.assessor_id,
            assignment_version_id,
            None,
            True,
            True,
            True,
            True,
            True,
            True,
            "exact prospective continued-validity basis",
            effective,
        ),
    )
    return determination_version_id


def _change_acceptance_status(
    store: SQLiteIntegrityStore,
    value: Increment5Fixture,
    key: str,
    *,
    result_version_id: RecordVersionId,
    acceptance_version_id: RecordVersionId,
    status: CompletionAcceptanceStatus,
    effective: EffectiveInterval,
) -> RecordVersionId:
    prior = store.get_version(acceptance_version_id)
    assert prior is not None and value.obligation_version_id is not None
    successor_version_id = RecordVersionId.new()
    value.service.commit_completion_acceptance(
        meta(f"{key}-acceptance-{status.value}"),
        CompletionAcceptanceVersionInput(
            prior.record_id,
            successor_version_id,
            value.obligation_version_id,
            value.intervention_version_id,
            result_version_id,
            value.foundation.decision_version_id,
            value.foundation.context.configuration_version_id,
            ("capacity boundary",),
            CompletionAcceptanceOutcome.ACCEPTED,
            f"prior Acceptance is now {status.value}",
            (),
            (),
            value.foundation.context.assessor_id,
            value.acceptor_assignment_version_id,
            None,
            (),
            effective,
            expected_version_id=acceptance_version_id,
            relationship_reason=f"Acceptance status changed to {status.value}",
            status=status,
        ),
    )
    return successor_version_id


def _mechanism(
    value: Increment5Fixture,
    key: str,
    *,
    effective: EffectiveInterval = EFFECTIVE,
    accountable_actor_id: RecordId | None = None,
) -> RecordVersionId:
    mechanism_id, mechanism_version_id = RecordId.new(), RecordVersionId.new()
    value.service.commit_completion_acceptor_mechanism(
        meta(f"{key}-completion-acceptor-mechanism"),
        CompletionAcceptorMechanismVersionInput(
            mechanism_id,
            mechanism_version_id,
            value.foundation.context.case_id,
            value.intervention_id,
            value.intervention_version_id,
            value.foundation.decision_version_id,
            value.foundation.context.configuration_id,
            value.foundation.context.configuration_version_id,
            accountable_actor_id or value.foundation.context.assessor_id,
            "completion-acceptance-policy-v1",
            "exact intervention completion acceptance",
            "organizational-authority-register:v1",
            effective,
        ),
    )
    return mechanism_version_id


def _activation(
    value: Increment5Fixture, *, mechanism: RecordVersionId | None = None
) -> ActivationRequest:
    fx = value.foundation
    return ActivationRequest(
        RecordId.new(),
        RecordVersionId.new(),
        RecordId.new(),
        RecordVersionId.new(),
        str(RecordId.new()),
        fx.context.case_id,
        fx.decision_version_id,
        fx.context.configuration_id,
        fx.context.configuration_version_id,
        fx.snapshot_version_id,
        "bounded continuation",
        (
            ActivationAuthorityKind.ORGANIZATIONAL_MECHANISM
            if mechanism
            else ActivationAuthorityKind.DECISION_AUTHORITY
        ),
        None if mechanism else fx.context.assessor_id,
        None if mechanism else fx.authority_assignment_version_id,
        mechanism,
        value.authorization_basis_version_id,
        "narrow-scope",
        ("bounded continuation only",),
        EFFECTIVE,
        (),
        "activate only after exact prerequisites pass",
        EFFECTIVE.start,
    )


def test_completion_requires_separate_current_acceptance_and_preserves_conflict(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    value = _setup(sqlite_store, "acceptance")
    assert value.obligation_version_id is not None
    before = value.service.evaluate_prerequisites(
        decision_version_id=value.foundation.decision_version_id,
        configuration_version_id=value.foundation.context.configuration_version_id,
        effective_at=EFFECTIVE.start,
    )
    assert before.result is AggregatePrerequisiteResult.NOT_ESTABLISHED

    _complete(value, "acceptance-first")
    accepted = value.service.evaluate_prerequisites(
        decision_version_id=value.foundation.decision_version_id,
        configuration_version_id=value.foundation.context.configuration_version_id,
        effective_at=EFFECTIVE.start,
    )
    assert accepted.result is AggregatePrerequisiteResult.SATISFIED
    assert accepted.obligations[0].result is ObligationResult.SATISFIED

    _complete(value, "acceptance-second")
    conflict = value.service.evaluate_prerequisites(
        decision_version_id=value.foundation.decision_version_id,
        configuration_version_id=value.foundation.context.configuration_version_id,
        effective_at=EFFECTIVE.start,
    )
    assert conflict.result is AggregatePrerequisiteResult.CONFLICT


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (InterventionStatus.PROPOSED, AggregatePrerequisiteResult.INCOMPLETE),
        (InterventionStatus.PARTIALLY_COMPLETED, AggregatePrerequisiteResult.INCOMPLETE),
        (InterventionStatus.BLOCKED, AggregatePrerequisiteResult.BLOCKED),
        (InterventionStatus.FAILED, AggregatePrerequisiteResult.BLOCKED),
        (InterventionStatus.CANCELLED, AggregatePrerequisiteResult.BLOCKED),
    ],
)
def test_intervention_status_has_deterministic_prerequisite_mapping(
    sqlite_store: SQLiteIntegrityStore,
    status: InterventionStatus,
    expected: AggregatePrerequisiteResult,
) -> None:
    value = _setup(sqlite_store, f"status-{status.value}", intervention_status=status)
    evaluation = value.service.evaluate_prerequisites(
        decision_version_id=value.foundation.decision_version_id,
        configuration_version_id=value.foundation.context.configuration_version_id,
        effective_at=EFFECTIVE.start,
    )
    assert evaluation.result is expected


def test_required_after_optional_and_explicit_zero_do_not_block_activation_gate(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    for key, requirement in (
        ("required-after", RequirementType.REQUIRED_AFTER_OPERATION),
        ("optional", RequirementType.OPTIONAL),
        ("zero", None),
    ):
        value = _setup(sqlite_store, key, requirement_type=requirement)
        evaluation = value.service.evaluate_prerequisites(
            decision_version_id=value.foundation.decision_version_id,
            configuration_version_id=value.foundation.context.configuration_version_id,
            effective_at=EFFECTIVE.start,
        )
        assert evaluation.result is AggregatePrerequisiteResult.NOT_REQUIRED


def test_completion_acceptor_exact_scope_and_overlap_rules(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    case_scoped = _setup(sqlite_store, "case-acceptor", acceptor_target=RoleTargetType.CASE)
    _complete(case_scoped, "case-acceptor")
    assert (
        case_scoped.service.evaluate_prerequisites(
            decision_version_id=case_scoped.foundation.decision_version_id,
            configuration_version_id=case_scoped.foundation.context.configuration_version_id,
            effective_at=EFFECTIVE.start,
        ).result
        is AggregatePrerequisiteResult.SATISFIED
    )

    conflict = _setup(sqlite_store, "acceptor-overlap", acceptor_target=RoleTargetType.CASE)
    assignment_id, assignment_version_id = RecordId.new(), RecordVersionId.new()
    conflict.service.commit_role_assignment(
        meta("acceptor-overlap-second-acceptor"),
        RoleAssignmentVersionInput(
            assignment_id,
            assignment_version_id,
            conflict.foundation.context.assessor_id,
            "Intervention Completion Acceptor",
            RoleTargetType.INTERVENTION,
            str(conflict.intervention_id),
            conflict.foundation.context.case_id,
            True,
            "overlapping accountable assignment",
            DelegationEffect.NONE,
            None,
            EFFECTIVE,
        ),
    )
    with pytest.raises(DomainRuleViolation, match="CONFLICT"):
        _complete(conflict, "acceptor-overlap")


def test_withdrawn_acceptance_is_historical_but_not_future_eligible(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    value = _setup(sqlite_store, "withdrawn")
    _complete(value, "withdrawn", acceptance_status=CompletionAcceptanceStatus.WITHDRAWN)
    evaluation = value.service.evaluate_prerequisites(
        decision_version_id=value.foundation.decision_version_id,
        configuration_version_id=value.foundation.context.configuration_version_id,
        effective_at=EFFECTIVE.start,
    )
    assert evaluation.result is AggregatePrerequisiteResult.NOT_ESTABLISHED
    assert sqlite_store.count_rows("completion_acceptance_versions") == 1


def test_exact_prior_acceptance_supports_reuse_and_role_expiry_does_not_rewrite_it(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    reuse_effective = EffectiveInterval(utc(2026, 1, 10))
    valid = _setup(sqlite_store, "reuse-valid")
    result_id, acceptance_id = _complete(valid, "reuse-valid")
    successor_id = _successor_obligation(
        sqlite_store, valid, "reuse-valid", effective=reuse_effective
    )
    _reuse(
        valid,
        "reuse-valid",
        successor_obligation_version_id=successor_id,
        prior_result_version_id=result_id,
        prior_acceptance_version_id=acceptance_id,
        effective=reuse_effective,
    )
    assert (
        valid.service.evaluate_prerequisites(
            decision_version_id=valid.foundation.decision_version_id,
            configuration_version_id=valid.foundation.context.configuration_version_id,
            effective_at=reuse_effective.start,
        ).result
        is AggregatePrerequisiteResult.SATISFIED
    )

    expired_role = _setup(
        sqlite_store,
        "reuse-expired-role",
        acceptor_effective=EffectiveInterval(utc(2026, 1, 1), utc(2026, 1, 5)),
    )
    expired_result, expired_acceptance = _complete(expired_role, "reuse-expired-role")
    expired_successor = _successor_obligation(
        sqlite_store,
        expired_role,
        "reuse-expired-role",
        effective=reuse_effective,
    )
    _reuse(
        expired_role,
        "reuse-expired-role",
        successor_obligation_version_id=expired_successor,
        prior_result_version_id=expired_result,
        prior_acceptance_version_id=expired_acceptance,
        effective=reuse_effective,
    )
    assert (
        expired_role.service.evaluate_prerequisites(
            decision_version_id=expired_role.foundation.decision_version_id,
            configuration_version_id=expired_role.foundation.context.configuration_version_id,
            effective_at=reuse_effective.start,
        ).result
        is AggregatePrerequisiteResult.SATISFIED
    )


def test_ineligible_prior_acceptance_blocks_reuse_determination_commit(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    value = _setup(sqlite_store, "reuse-commit-withdrawn")
    result_id, acceptance_id = _complete(value, "reuse-commit-withdrawn")
    withdrawn_effective = EffectiveInterval(utc(2026, 1, 5))
    _change_acceptance_status(
        sqlite_store,
        value,
        "reuse-commit-withdrawn",
        result_version_id=result_id,
        acceptance_version_id=acceptance_id,
        status=CompletionAcceptanceStatus.WITHDRAWN,
        effective=withdrawn_effective,
    )
    reuse_effective = EffectiveInterval(utc(2026, 1, 10))
    successor_id = _successor_obligation(
        sqlite_store,
        value,
        "reuse-commit-withdrawn",
        effective=reuse_effective,
    )
    with pytest.raises(DomainRuleViolation, match="prior basis is ineligible"):
        _reuse(
            value,
            "reuse-commit-withdrawn",
            successor_obligation_version_id=successor_id,
            prior_result_version_id=result_id,
            prior_acceptance_version_id=acceptance_id,
            effective=reuse_effective,
        )


@pytest.mark.parametrize(
    "status",
    [CompletionAcceptanceStatus.WITHDRAWN, CompletionAcceptanceStatus.SUPERSEDED],
)
def test_withdrawn_or_superseded_prior_acceptance_cannot_satisfy_future_reuse(
    sqlite_store: SQLiteIntegrityStore,
    status: CompletionAcceptanceStatus,
) -> None:
    value = _setup(sqlite_store, f"reuse-future-{status.value}")
    result_id, acceptance_id = _complete(value, f"reuse-future-{status.value}")
    reuse_effective = EffectiveInterval(utc(2026, 1, 10))
    successor_id = _successor_obligation(
        sqlite_store,
        value,
        f"reuse-future-{status.value}",
        effective=reuse_effective,
    )
    _reuse(
        value,
        f"reuse-future-{status.value}",
        successor_obligation_version_id=successor_id,
        prior_result_version_id=result_id,
        prior_acceptance_version_id=acceptance_id,
        effective=reuse_effective,
    )
    assert (
        value.service.evaluate_prerequisites(
            decision_version_id=value.foundation.decision_version_id,
            configuration_version_id=value.foundation.context.configuration_version_id,
            effective_at=reuse_effective.start,
        ).result
        is AggregatePrerequisiteResult.SATISFIED
    )

    future_effective = EffectiveInterval(utc(2026, 1, 20))
    _change_acceptance_status(
        sqlite_store,
        value,
        f"reuse-future-{status.value}",
        result_version_id=result_id,
        acceptance_version_id=acceptance_id,
        status=status,
        effective=future_effective,
    )
    evaluation = value.service.evaluate_prerequisites(
        decision_version_id=value.foundation.decision_version_id,
        configuration_version_id=value.foundation.context.configuration_version_id,
        effective_at=future_effective.start,
    )
    assert evaluation.result is AggregatePrerequisiteResult.NOT_ESTABLISHED
    assert "prospective Acceptance eligibility" in evaluation.obligations[0].diagnostics[-1]


def test_completion_acceptor_mechanism_must_be_established_exact_and_effective(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    fabricated = _setup(sqlite_store, "mechanism-fabricated", acceptor_target=None)
    with pytest.raises(DomainRuleViolation, match="ACCOUNTABILITY NOT ESTABLISHED"):
        _complete(
            fabricated,
            "mechanism-fabricated",
            mechanism_version_id=RecordVersionId.new(),
        )

    target = _setup(sqlite_store, "mechanism-target", acceptor_target=None)
    unrelated = _setup(sqlite_store, "mechanism-unrelated", acceptor_target=None)
    unrelated_version = _mechanism(unrelated, "mechanism-unrelated")
    with pytest.raises(DomainRuleViolation, match="ACCOUNTABILITY NOT ESTABLISHED"):
        _complete(target, "mechanism-target", mechanism_version_id=unrelated_version)

    ineffective = _setup(sqlite_store, "mechanism-ineffective", acceptor_target=None)
    ineffective_version = _mechanism(
        ineffective,
        "mechanism-ineffective",
        effective=EffectiveInterval(utc(2026, 1, 15)),
    )
    with pytest.raises(DomainRuleViolation, match="ACCOUNTABILITY NOT ESTABLISHED"):
        _complete(
            ineffective,
            "mechanism-ineffective",
            mechanism_version_id=ineffective_version,
        )


def test_exact_governed_completion_acceptor_mechanism_succeeds_and_binds_actor(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    overlap = _setup(sqlite_store, "mechanism-assignment-overlap")
    _mechanism(overlap, "mechanism-assignment-overlap")
    with pytest.raises(DomainRuleViolation, match="CONFLICT"):
        _complete(overlap, "mechanism-assignment-overlap")

    actor_source = _setup(sqlite_store, "mechanism-actor-source")
    mismatched = _setup(sqlite_store, "mechanism-actor-mismatch", acceptor_target=None)
    mismatched_version = _mechanism(
        mismatched,
        "mechanism-actor-mismatch",
        accountable_actor_id=actor_source.foundation.context.assessor_id,
    )
    with pytest.raises(DomainRuleViolation, match="actor/mechanism mismatch"):
        _complete(
            mismatched,
            "mechanism-actor-mismatch",
            mechanism_version_id=mismatched_version,
        )

    valid = _setup(sqlite_store, "mechanism-valid", acceptor_target=None)
    valid_version = _mechanism(valid, "mechanism-valid")
    _complete(valid, "mechanism-valid", mechanism_version_id=valid_version)
    assert (
        valid.service.evaluate_prerequisites(
            decision_version_id=valid.foundation.decision_version_id,
            configuration_version_id=valid.foundation.context.configuration_version_id,
            effective_at=EFFECTIVE.start,
        ).result
        is AggregatePrerequisiteResult.SATISFIED
    )


def test_activation_is_atomic_and_requires_genuine_authority(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    value = _setup(sqlite_store, "activation")
    _complete(value, "activation")
    rejected = replace(_activation(value), authority_scope="unrelated-scope")
    before = (
        sqlite_store.count_rows("prerequisite_evaluation_basis_versions"),
        sqlite_store.count_rows("activation_authorization_versions"),
        sqlite_store.count_rows("target_activation_events"),
    )
    with pytest.raises(DomainRuleViolation, match="does not cover exact target"):
        value.service.activate_target(meta("activation-invalid"), rejected)
    assert before == (
        sqlite_store.count_rows("prerequisite_evaluation_basis_versions"),
        sqlite_store.count_rows("activation_authorization_versions"),
        sqlite_store.count_rows("target_activation_events"),
    )
    result = value.service.activate_target(meta("activation-valid"), _activation(value))
    assert result.activated
    assert (
        value.service.current_lifecycle_state(
            case_id=value.foundation.context.case_id,
            effective_at=EFFECTIVE.start,
        )
        is CaseLifecycleState.OPERATING_OBSERVING
    )


def test_exact_preauthorized_mechanism_and_learning_are_bounded(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    mechanism_version_id = RecordVersionId.new()
    mechanism = PreauthorizedActivationMechanismInput(
        RecordId.new(),
        mechanism_version_id,
        "activation-rule-v1",
        "narrow-scope",
        "authority-policy:v1",
        ("bounded continuation only",),
        EFFECTIVE,
    )
    value = _setup(sqlite_store, "mechanism", requirement_type=None, preauthorized=(mechanism,))
    result = value.service.activate_target(
        meta("mechanism-activation"), _activation(value, mechanism=mechanism_version_id)
    )
    assert result.activated

    decision = sqlite_store.get_version(value.foundation.decision_version_id)
    assert decision is not None
    uncertainty_version_id = RecordVersionId.parse(
        str(decision.content["decision_limiting_uncertainty_version_ids"][0])
    )
    learning_id, learning_version_id = RecordId.new(), RecordVersionId.new()
    value.service.commit_learning_item(
        meta("mechanism-learning"),
        LearningItemVersionInput(
            learning_id,
            learning_version_id,
            value.foundation.context.case_id,
            value.foundation.decision_version_id,
            value.foundation.context.configuration_id,
            value.foundation.context.configuration_version_id,
            uncertainty_version_id,
            "Does the control remain effective?",
            "reduce decision-limiting uncertainty",
            "longitudinal control evidence",
            value.foundation.context.assessor_id,
            None,
            "governed:learning-owner",
            "monthly observation",
            LearningStatus.ACTIVE,
            None,
            (),
            (),
            None,
            None,
            {"source": "decision-learning-plan"},
            EFFECTIVE,
        ),
    )
    stored = sqlite_store.get_version(learning_version_id)
    assert stored is not None and stored.family == "learning-item"
    assert stored.content["successor_decision_version_id"] is None
