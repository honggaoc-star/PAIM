from __future__ import annotations

from dataclasses import replace
from datetime import datetime

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from paim.application import (
    DomainPreconditionFailed,
    DomainRuleViolation,
    Increment2ApplicationService,
)
from paim.audit import ActorResolution
from paim.domain import (
    AccountabilityConflict,
    AccountabilityFound,
    AccountabilityVacant,
    ActorVersionInput,
    CaseLifecycleState,
    CaseLinkInput,
    CaseVersionInput,
    CommandMeta,
    ConfigurationDeterminationInput,
    ConfigurationMaturity,
    ConfigurationPurpose,
    ConfigurationVersionInput,
    DelegationEffect,
    DeterminationKind,
    DeterminationOutcome,
    GoverningConfigurationAbsent,
    GoverningConfigurationConflict,
    GoverningConfigurationFound,
    GoverningDesignationInput,
    RoleAssignmentVersionInput,
    RoleTargetType,
)
from paim.integrity import (
    AuditId,
    CommandId,
    EffectiveInterval,
    FixedClock,
    RecordId,
    RecordVersionId,
)
from paim.persistence.ports import WriterContention
from paim.persistence.sqlite import SQLiteIntegrityStore
from tests.helpers import utc


def meta(key: str, *, actor_id: str | None = "actor:human") -> CommandMeta:
    resolution = ActorResolution.PROVIDED if actor_id is not None else ActorResolution.UNRESOLVED
    return CommandMeta(
        command_id=CommandId.new(),
        idempotency_scope="increment-2-tests",
        idempotency_key=key,
        principal_id="principal:technical",
        actor_id=actor_id,
        actor_resolution=resolution,
    )


def service(
    store: SQLiteIntegrityStore, recorded_at: datetime | None = None
) -> Increment2ApplicationService:
    return Increment2ApplicationService(store, FixedClock(recorded_at or utc(2026, 1, 2)))


def add_case(
    store: SQLiteIntegrityStore,
    key: str,
    *,
    case_id: RecordId | None = None,
    version_id: RecordVersionId | None = None,
) -> tuple[RecordId, RecordVersionId]:
    identity = case_id or RecordId.new()
    version = version_id or RecordVersionId.new()
    service(store).commit_case(
        meta(f"{key}-case"),
        CaseVersionInput(identity, version, f"Case {key}", EffectiveInterval(utc(2026, 1, 1))),
    )
    return identity, version


def add_configuration(
    store: SQLiteIntegrityStore,
    key: str,
    case_id: RecordId,
    *,
    configuration_id: RecordId | None = None,
    version_id: RecordVersionId | None = None,
    purpose: ConfigurationPurpose = ConfigurationPurpose.CANDIDATE,
) -> tuple[RecordId, RecordVersionId]:
    identity = configuration_id or RecordId.new()
    version = version_id or RecordVersionId.new()
    service(store).commit_configuration(
        meta(f"{key}-configuration"),
        ConfigurationVersionInput(
            identity,
            version,
            case_id,
            ConfigurationMaturity.FINALIZED,
            purpose,
            {"system": key},
            EffectiveInterval(utc(2026, 1, 1)),
        ),
    )
    return identity, version


def add_actor(
    store: SQLiteIntegrityStore, key: str, *, actor_id: RecordId | None = None
) -> tuple[RecordId, RecordVersionId]:
    identity = actor_id or RecordId.new()
    version = RecordVersionId.new()
    service(store).commit_actor(
        meta(f"{key}-actor"),
        ActorVersionInput(identity, version, f"Actor {key}", EffectiveInterval(utc(2026, 1, 1))),
    )
    return identity, version


def add_role(
    store: SQLiteIntegrityStore,
    key: str,
    actor_id: RecordId,
    *,
    role: str = "configuration steward",
    target_type: RoleTargetType,
    target_id: str,
    case_context_id: RecordId | None,
    accountable: bool,
    delegation_effect: DelegationEffect = DelegationEffect.NONE,
    delegated_from: RecordVersionId | None = None,
    effective_from: datetime | None = None,
) -> tuple[RecordId, RecordVersionId]:
    identity = RecordId.new()
    version = RecordVersionId.new()
    service(store).commit_role_assignment(
        meta(f"{key}-role"),
        RoleAssignmentVersionInput(
            identity,
            version,
            actor_id,
            role,
            target_type,
            target_id,
            case_context_id,
            accountable,
            "compatible-performer",
            delegation_effect,
            delegated_from,
            EffectiveInterval(effective_from or utc(2026, 1, 1)),
        ),
    )
    return identity, version


def designate(
    store: SQLiteIntegrityStore,
    key: str,
    case_id: RecordId,
    configuration_version_id: RecordVersionId,
    *,
    recorded_at: datetime | None = None,
    designation_id: RecordId | None = None,
    version_id: RecordVersionId | None = None,
    expected_version_id: RecordVersionId | None = None,
) -> tuple[RecordId, RecordVersionId]:
    identity = designation_id or RecordId.new()
    version = version_id or RecordVersionId.new()
    service(store, recorded_at or utc(2026, 1, 2)).commit_governing_designation(
        meta(f"{key}-designation"),
        GoverningDesignationInput(
            identity,
            version,
            case_id,
            configuration_version_id,
            EffectiveInterval(utc(2026, 1, 1)),
            accountable_mechanism="governed configuration-currentness board",
            expected_version_id=expected_version_id,
            relationship_reason=("correct prior designation" if expected_version_id else None),
        ),
    )
    return identity, version


def test_case_configuration_history_ownership_and_finalized_immutability(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    case_id, _ = add_case(sqlite_store, "history")
    configuration_id, first_version = add_configuration(sqlite_store, "history", case_id)
    second_version = RecordVersionId.new()
    service(sqlite_store, utc(2026, 2, 2)).commit_configuration(
        meta("history-configuration-successor"),
        ConfigurationVersionInput(
            configuration_id,
            second_version,
            case_id,
            ConfigurationMaturity.FINALIZED,
            ConfigurationPurpose.CANDIDATE,
            {"system": "changed but not auto-judged"},
            EffectiveInterval(utc(2026, 2, 1)),
            expected_version_id=first_version,
            relationship_reason="authoritative content revision",
        ),
    )

    history = sqlite_store.get_history(configuration_id)
    assert {version.version_id for version in history.versions} == {first_version, second_version}
    assert sqlite_store.count_rows("configuration_determinations") == 0
    with (
        sqlite_store.engine.begin() as connection,
        pytest.raises(DBAPIError, match="finalized content is immutable"),
    ):
        connection.execute(
            text("UPDATE record_versions SET content_json = '{}' WHERE version_id = :version"),
            {"version": str(second_version)},
        )

    other_case, _ = add_case(sqlite_store, "other-owner")
    with pytest.raises(DomainPreconditionFailed):
        service(sqlite_store).commit_configuration(
            meta("ownership-transfer"),
            ConfigurationVersionInput(
                configuration_id,
                RecordVersionId.new(),
                other_case,
                ConfigurationMaturity.FINALIZED,
                ConfigurationPurpose.CANDIDATE,
                {"system": "illegal owner transfer"},
                EffectiveInterval(utc(2026, 3, 1)),
                expected_version_id=second_version,
                relationship_reason="must not transfer",
            ),
        )


def test_configuration_requires_existing_exactly_one_owner_and_rolls_back(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    before_records = sqlite_store.count_rows("records")
    with pytest.raises(DomainRuleViolation, match="existing owning Case"):
        service(sqlite_store).commit_configuration(
            meta("missing-owner"),
            ConfigurationVersionInput(
                RecordId.new(),
                RecordVersionId.new(),
                RecordId.new(),
                ConfigurationMaturity.FINALIZED,
                ConfigurationPurpose.CANDIDATE,
                {"system": "orphan"},
                EffectiveInterval(utc(2026, 1, 1)),
            ),
        )
    assert sqlite_store.count_rows("records") == before_records
    assert sqlite_store.count_rows("managed_configurations") == 0


@pytest.mark.parametrize(
    "purpose",
    [
        ConfigurationPurpose.PROPOSED,
        ConfigurationPurpose.EXPERIMENTAL,
        ConfigurationPurpose.ALTERNATIVE,
        ConfigurationPurpose.FALLBACK,
    ],
)
def test_non_governing_purpose_cannot_be_designated_selected_or_satisfy_lifecycle(
    sqlite_store: SQLiteIntegrityStore,
    purpose: ConfigurationPurpose,
) -> None:
    case_id, _ = add_case(sqlite_store, f"ineligible-{purpose.value}")
    _, configuration_version = add_configuration(
        sqlite_store,
        f"ineligible-{purpose.value}",
        case_id,
        purpose=purpose,
    )
    domain = service(sqlite_store)
    with pytest.raises(DomainRuleViolation, match="ineligible for governing designation"):
        designate(
            sqlite_store,
            f"attempt-{purpose.value}",
            case_id,
            configuration_version,
        )
    assert isinstance(
        domain.select_governing_configuration(case_id=case_id, effective_at=utc(2026, 1, 1)),
        GoverningConfigurationAbsent,
    )
    transition = domain.transition_case(
        meta(f"transition-ineligible-{purpose.value}"),
        case_id=case_id,
        target_state=CaseLifecycleState.CONFIGURATION_DEFINED,
        effective_at=utc(2026, 1, 1),
    )
    assert not transition.accepted
    assert "NOT ESTABLISHED" in transition.reason
    assert sqlite_store.count_rows("governing_configuration_designations") == 0


def test_candidate_designation_selects_and_same_case_candidates_conflict_without_winner(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    case_id, _ = add_case(sqlite_store, "governing-candidate")
    _, first_configuration = add_configuration(sqlite_store, "candidate-first", case_id)
    _, second_configuration = add_configuration(sqlite_store, "candidate-second", case_id)
    domain = service(sqlite_store)
    designate(sqlite_store, "candidate-first", case_id, first_configuration)
    selected = domain.select_governing_configuration(case_id=case_id, effective_at=utc(2026, 1, 1))
    assert isinstance(selected, GoverningConfigurationFound)
    assert selected.configuration_version_id == first_configuration
    designate(sqlite_store, "candidate-second", case_id, second_configuration)
    conflict = domain.select_governing_configuration(case_id=case_id, effective_at=utc(2026, 1, 1))
    assert isinstance(conflict, GoverningConfigurationConflict)
    assert conflict.configuration_version_ids == frozenset(
        {first_configuration, second_configuration}
    )


def test_governing_known_at_reconstruction_preserves_later_correction_history(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    case_id, _ = add_case(sqlite_store, "reconstruction")
    _, first_configuration = add_configuration(sqlite_store, "reconstruction-first", case_id)
    _, corrected_configuration = add_configuration(
        sqlite_store, "reconstruction-corrected", case_id
    )
    designation_id, first_designation = designate(
        sqlite_store,
        "reconstruction-first",
        case_id,
        first_configuration,
        recorded_at=utc(2026, 1, 2),
    )
    _, corrected_designation = designate(
        sqlite_store,
        "reconstruction-correction",
        case_id,
        corrected_configuration,
        recorded_at=utc(2026, 1, 4),
        designation_id=designation_id,
        expected_version_id=first_designation,
    )
    domain = service(sqlite_store, utc(2026, 1, 5))
    before_knowledge = domain.select_governing_configuration(
        case_id=case_id,
        effective_at=utc(2026, 1, 1),
        known_at=utc(2026, 1, 3),
    )
    after_knowledge = domain.select_governing_configuration(
        case_id=case_id,
        effective_at=utc(2026, 1, 1),
        known_at=utc(2026, 1, 5),
    )
    assert isinstance(before_knowledge, GoverningConfigurationFound)
    assert before_knowledge.configuration_version_id == first_configuration
    assert isinstance(after_knowledge, GoverningConfigurationFound)
    assert after_knowledge.configuration_version_id == corrected_configuration
    history = sqlite_store.get_history(designation_id)
    assert {version.version_id for version in history.versions} == {
        first_designation,
        corrected_designation,
    }


def test_linked_cases_support_independent_concurrent_governing_configurations(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    first_case, _ = add_case(sqlite_store, "linked-one")
    second_case, _ = add_case(sqlite_store, "linked-two")
    _, first_configuration = add_configuration(sqlite_store, "linked-one", first_case)
    _, second_configuration = add_configuration(sqlite_store, "linked-two", second_case)
    domain = service(sqlite_store)
    domain.link_cases(
        meta("link-cases"),
        CaseLinkInput(
            str(RecordId.new()),
            first_case,
            second_case,
            "related-independent-governance",
            utc(2026, 1, 1),
            "independent concurrent governing configurations",
        ),
    )
    designate(sqlite_store, "linked-one", first_case, first_configuration)
    designate(sqlite_store, "linked-two", second_case, second_configuration)
    first = domain.select_governing_configuration(case_id=first_case, effective_at=utc(2026, 1, 1))
    second = domain.select_governing_configuration(
        case_id=second_case, effective_at=utc(2026, 1, 1)
    )
    assert isinstance(first, GoverningConfigurationFound)
    assert isinstance(second, GoverningConfigurationFound)
    assert first.configuration_version_id == first_configuration
    assert second.configuration_version_id == second_configuration
    assert sqlite_store.count_rows("paim_case_links") == 1


def test_lifecycle_guards_absence_conflict_and_later_layer_boundary(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    domain = service(sqlite_store)
    absent_case, _ = add_case(sqlite_store, "lifecycle-absent")
    _, alternative = add_configuration(
        sqlite_store,
        "lifecycle-alternative",
        absent_case,
        purpose=ConfigurationPurpose.ALTERNATIVE,
    )
    absent = domain.transition_case(
        meta("transition-absent"),
        case_id=absent_case,
        target_state=CaseLifecycleState.CONFIGURATION_DEFINED,
        effective_at=utc(2026, 1, 1),
    )
    assert not absent.accepted
    assert "NOT ESTABLISHED" in absent.reason
    assert alternative is not None

    conflict_case, _ = add_case(sqlite_store, "lifecycle-conflict")
    _, first = add_configuration(sqlite_store, "lifecycle-conflict-one", conflict_case)
    _, second = add_configuration(sqlite_store, "lifecycle-conflict-two", conflict_case)
    designate(sqlite_store, "lifecycle-conflict-one", conflict_case, first)
    designate(sqlite_store, "lifecycle-conflict-two", conflict_case, second)
    conflict = domain.transition_case(
        meta("transition-conflict"),
        case_id=conflict_case,
        target_state=CaseLifecycleState.CONFIGURATION_DEFINED,
        effective_at=utc(2026, 1, 1),
    )
    assert not conflict.accepted
    assert "CONFLICT" in conflict.reason

    valid_case, valid_case_version = add_case(sqlite_store, "lifecycle-valid")
    _, governing = add_configuration(sqlite_store, "lifecycle-valid", valid_case)
    designate(sqlite_store, "lifecycle-valid", valid_case, governing)
    transition_meta = meta("transition-valid")
    accepted = domain.transition_case(
        transition_meta,
        case_id=valid_case,
        target_state=CaseLifecycleState.CONFIGURATION_DEFINED,
        effective_at=utc(2026, 1, 1),
    )
    replay = domain.transition_case(
        transition_meta,
        case_id=valid_case,
        target_state=CaseLifecycleState.CONFIGURATION_DEFINED,
        effective_at=utc(2026, 1, 1),
    )
    assert accepted.accepted and replay == accepted
    status_count = sqlite_store.count_rows("status_events")
    later = domain.transition_case(
        meta("transition-later-layer"),
        case_id=valid_case,
        target_state=CaseLifecycleState.EVIDENCE_ANALYSIS,
        effective_at=utc(2026, 1, 2),
    )
    assert not later.accepted
    assert "VALUE/RISK/EVIDENCE" in later.reason
    assert sqlite_store.count_rows("status_events") == status_count
    with pytest.raises(DomainRuleViolation, match="invalid or duplicate"):
        domain.transition_case(
            meta("transition-invalid-duplicate"),
            case_id=valid_case,
            target_state=CaseLifecycleState.CONFIGURATION_DEFINED,
            effective_at=utc(2026, 1, 2),
        )
    assert sqlite_store.count_rows("status_events") == status_count
    service(sqlite_store, utc(2026, 2, 2)).commit_case(
        meta("lifecycle-case-successor"),
        CaseVersionInput(
            valid_case,
            RecordVersionId.new(),
            "Case lifecycle-valid renamed",
            EffectiveInterval(utc(2026, 2, 1)),
            expected_version_id=valid_case_version,
            relationship_reason="rename without lifecycle reset",
        ),
    )
    assert (
        domain.current_lifecycle_state(
            case_id=valid_case, effective_at=utc(2026, 2, 1), known_at=utc(2026, 2, 3)
        )
        is CaseLifecycleState.CONFIGURATION_DEFINED
    )


def test_role_typed_targets_and_actor_principal_separation(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    case_id, _ = add_case(sqlite_store, "roles")
    configuration_id, _ = add_configuration(sqlite_store, "roles", case_id)
    actor_id, _ = add_actor(sqlite_store, "roles")
    _, org_version = add_role(
        sqlite_store,
        "organization",
        actor_id,
        target_type=RoleTargetType.ORGANIZATION,
        target_id="organization:alpha",
        case_context_id=None,
        accountable=False,
    )
    _, business_unit_version = add_role(
        sqlite_store,
        "business-unit",
        actor_id,
        target_type=RoleTargetType.BUSINESS_UNIT,
        target_id="business-unit:alpha",
        case_context_id=None,
        accountable=False,
    )
    _, config_version = add_role(
        sqlite_store,
        "configuration",
        actor_id,
        target_type=RoleTargetType.CONFIGURATION,
        target_id=str(configuration_id),
        case_context_id=case_id,
        accountable=False,
    )
    assert sqlite_store.get_version(org_version) is not None
    assert sqlite_store.get_version(business_unit_version) is not None
    assert sqlite_store.get_version(config_version) is not None
    with pytest.raises(DomainRuleViolation, match="owning-Case context"):
        add_role(
            sqlite_store,
            "wrong-config-context",
            actor_id,
            target_type=RoleTargetType.CONFIGURATION,
            target_id=str(configuration_id),
            case_context_id=RecordId.new(),
            accountable=False,
        )
    with pytest.raises(DomainRuleViolation, match="existing PAIM actor"):
        add_role(
            sqlite_store,
            "principal-is-not-actor",
            RecordId.new(),
            target_type=RoleTargetType.CASE,
            target_id=str(case_id),
            case_context_id=case_id,
            accountable=True,
        )


def test_compatible_performers_and_accountability_one_vacancy_conflict(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    case_id, _ = add_case(sqlite_store, "accountability")
    configuration_id, _ = add_configuration(sqlite_store, "accountability", case_id)
    first_actor, _ = add_actor(sqlite_store, "performer-one")
    second_actor, _ = add_actor(sqlite_store, "performer-two")
    add_role(
        sqlite_store,
        "performer-one",
        first_actor,
        target_type=RoleTargetType.CONFIGURATION,
        target_id=str(configuration_id),
        case_context_id=case_id,
        accountable=False,
    )
    add_role(
        sqlite_store,
        "performer-two",
        second_actor,
        target_type=RoleTargetType.CONFIGURATION,
        target_id=str(configuration_id),
        case_context_id=case_id,
        accountable=False,
    )
    domain = service(sqlite_store)
    performers = domain.resolve_role_performers(
        role="configuration steward",
        target_type=RoleTargetType.CONFIGURATION,
        target_id=str(configuration_id),
        effective_at=utc(2026, 1, 1),
    )
    assert len(performers) == 2
    vacant = domain.resolve_accountability(
        role="configuration steward",
        target_type=RoleTargetType.CONFIGURATION,
        target_id=str(configuration_id),
        effective_at=utc(2026, 1, 1),
    )
    assert isinstance(vacant, AccountabilityVacant)

    _, accountable_version = add_role(
        sqlite_store,
        "accountable-config",
        first_actor,
        target_type=RoleTargetType.CONFIGURATION,
        target_id=str(configuration_id),
        case_context_id=case_id,
        accountable=True,
    )
    found = domain.resolve_accountability(
        role="configuration steward",
        target_type=RoleTargetType.CONFIGURATION,
        target_id=str(configuration_id),
        effective_at=utc(2026, 1, 1),
    )
    assert found == AccountabilityFound(accountable_version, None)
    _, broad_accountable = add_role(
        sqlite_store,
        "accountable-case",
        second_actor,
        target_type=RoleTargetType.CASE,
        target_id=str(case_id),
        case_context_id=case_id,
        accountable=True,
    )
    conflict = domain.resolve_accountability(
        role="configuration steward",
        target_type=RoleTargetType.CONFIGURATION,
        target_id=str(configuration_id),
        effective_at=utc(2026, 1, 1),
    )
    assert isinstance(conflict, AccountabilityConflict)
    assert conflict.assignment_version_ids == frozenset({accountable_version, broad_accountable})


def test_explicit_delegation_supplement_and_transfer_semantics(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    case_id, _ = add_case(sqlite_store, "delegation")
    first_actor, _ = add_actor(sqlite_store, "delegator")
    second_actor, _ = add_actor(sqlite_store, "delegate")
    _, source = add_role(
        sqlite_store,
        "delegation-source",
        first_actor,
        target_type=RoleTargetType.CASE,
        target_id=str(case_id),
        case_context_id=case_id,
        accountable=True,
    )
    _, supplement = add_role(
        sqlite_store,
        "delegation-supplement",
        second_actor,
        target_type=RoleTargetType.CASE,
        target_id=str(case_id),
        case_context_id=case_id,
        accountable=False,
        delegation_effect=DelegationEffect.SUPPLEMENT,
        delegated_from=source,
    )
    domain = service(sqlite_store)
    performers = domain.resolve_role_performers(
        role="configuration steward",
        target_type=RoleTargetType.CASE,
        target_id=str(case_id),
        effective_at=utc(2026, 1, 1),
    )
    assert set(performers) == {source, supplement}
    assert domain.resolve_accountability(
        role="configuration steward",
        target_type=RoleTargetType.CASE,
        target_id=str(case_id),
        effective_at=utc(2026, 1, 1),
    ) == AccountabilityFound(source, None)
    _, transferred = add_role(
        sqlite_store,
        "delegation-transfer",
        second_actor,
        target_type=RoleTargetType.CASE,
        target_id=str(case_id),
        case_context_id=case_id,
        accountable=True,
        delegation_effect=DelegationEffect.TRANSFER,
        delegated_from=source,
        effective_from=utc(2026, 2, 1),
    )
    assert domain.resolve_accountability(
        role="configuration steward",
        target_type=RoleTargetType.CASE,
        target_id=str(case_id),
        effective_at=utc(2026, 1, 15),
    ) == AccountabilityFound(source, None)
    assert domain.resolve_accountability(
        role="configuration steward",
        target_type=RoleTargetType.CASE,
        target_id=str(case_id),
        effective_at=utc(2026, 2, 1),
    ) == AccountabilityFound(transferred, None)


def test_delegation_retain_keeps_delegator_accountable_and_exposes_conflict(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    case_id, _ = add_case(sqlite_store, "delegation-retain")
    delegator, _ = add_actor(sqlite_store, "retain-delegator")
    delegate, _ = add_actor(sqlite_store, "retain-delegate")
    _, source = add_role(
        sqlite_store,
        "retain-source",
        delegator,
        target_type=RoleTargetType.CASE,
        target_id=str(case_id),
        case_context_id=case_id,
        accountable=True,
    )
    _, retained = add_role(
        sqlite_store,
        "retain-delegate",
        delegate,
        target_type=RoleTargetType.CASE,
        target_id=str(case_id),
        case_context_id=case_id,
        accountable=True,
        delegation_effect=DelegationEffect.RETAIN,
        delegated_from=source,
    )
    result = service(sqlite_store).resolve_accountability(
        role="configuration steward",
        target_type=RoleTargetType.CASE,
        target_id=str(case_id),
        effective_at=utc(2026, 1, 1),
    )
    assert isinstance(result, AccountabilityConflict)
    assert result.assignment_version_ids == frozenset({source, retained})


def test_governing_and_determination_require_non_conflicting_accountability(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    case_id, _ = add_case(sqlite_store, "determination")
    configuration_id, configuration_version = add_configuration(
        sqlite_store, "determination", case_id
    )
    first_actor, _ = add_actor(sqlite_store, "determination-one")
    second_actor, _ = add_actor(sqlite_store, "determination-two")
    _, first_assignment = add_role(
        sqlite_store,
        "determination-one",
        first_actor,
        target_type=RoleTargetType.CONFIGURATION,
        target_id=str(configuration_id),
        case_context_id=case_id,
        accountable=True,
    )
    domain = service(sqlite_store)
    determination_id = RecordId.new()
    determination_version = RecordVersionId.new()
    domain.commit_determination(
        meta("determination-material"),
        ConfigurationDeterminationInput(
            determination_id,
            determination_version,
            configuration_version,
            DeterminationKind.MATERIALITY,
            DeterminationOutcome.MATERIAL,
            "Accountable human judged boundary-relevant change",
            EffectiveInterval(utc(2026, 1, 1)),
            accountable_assignment_version_id=first_assignment,
        ),
    )
    stored = sqlite_store.get_version(determination_version)
    assert stored is not None
    assert stored.content["configuration_version_id"] == str(configuration_version)
    assert stored.content["outcome"] == "material"
    assert stored.content["rationale"] == "Accountable human judged boundary-relevant change"
    assert stored.content["accountable_assignment_version_id"] == str(first_assignment)
    assert stored.recorded_at == utc(2026, 1, 2)
    corrected_version = RecordVersionId.new()
    service(sqlite_store, utc(2026, 1, 3)).commit_determination(
        meta("determination-correction"),
        ConfigurationDeterminationInput(
            determination_id,
            corrected_version,
            configuration_version,
            DeterminationKind.MATERIALITY,
            DeterminationOutcome.NON_MATERIAL,
            "Corrected accountable judgment with preserved predecessor",
            EffectiveInterval(utc(2026, 1, 1)),
            accountable_assignment_version_id=first_assignment,
            expected_version_id=determination_version,
            relationship_reason="correct prior materiality judgment",
        ),
    )
    determination_history = sqlite_store.get_history(determination_id)
    assert {version.version_id for version in determination_history.versions} == {
        determination_version,
        corrected_version,
    }
    assert len(determination_history.relationships) == 1

    add_role(
        sqlite_store,
        "determination-two",
        second_actor,
        target_type=RoleTargetType.CASE,
        target_id=str(case_id),
        case_context_id=case_id,
        accountable=True,
    )
    with pytest.raises(DomainRuleViolation, match="vacant or conflicting"):
        domain.commit_determination(
            meta("determination-blocked-conflict"),
            ConfigurationDeterminationInput(
                RecordId.new(),
                RecordVersionId.new(),
                configuration_version,
                DeterminationKind.IDENTITY_CONTINUITY,
                DeterminationOutcome.SAME_IDENTITY,
                "Must not commit under conflicting accountability",
                EffectiveInterval(utc(2026, 1, 1)),
                accountable_assignment_version_id=first_assignment,
            ),
        )
    with pytest.raises(DomainRuleViolation, match="exactly one accountable"):
        domain.commit_determination(
            meta("determination-missing-accountability"),
            ConfigurationDeterminationInput(
                RecordId.new(),
                RecordVersionId.new(),
                configuration_version,
                DeterminationKind.IDENTITY_CONTINUITY,
                DeterminationOutcome.NEW_IDENTITY,
                "Explicit human outcome but missing accountable provenance",
                EffectiveInterval(utc(2026, 1, 1)),
            ),
        )
    assert sqlite_store.count_rows("configuration_determinations") == 2


def test_authoritative_provenance_is_bound_to_the_relevant_configuration_scope(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    relevant_case, _ = add_case(sqlite_store, "provenance-relevant")
    relevant_configuration, relevant_version = add_configuration(
        sqlite_store, "provenance-relevant", relevant_case
    )
    unrelated_case, _ = add_case(sqlite_store, "provenance-unrelated")
    unrelated_configuration, _ = add_configuration(
        sqlite_store, "provenance-unrelated", unrelated_case
    )
    unrelated_actor, _ = add_actor(sqlite_store, "provenance-unrelated")
    _, unrelated_assignment = add_role(
        sqlite_store,
        "provenance-unrelated",
        unrelated_actor,
        target_type=RoleTargetType.CONFIGURATION,
        target_id=str(unrelated_configuration),
        case_context_id=unrelated_case,
        accountable=True,
    )
    domain = service(sqlite_store)

    with pytest.raises(DomainRuleViolation, match="vacant or conflicting"):
        domain.commit_governing_designation(
            meta("provenance-unrelated-governing"),
            GoverningDesignationInput(
                RecordId.new(),
                RecordVersionId.new(),
                relevant_case,
                relevant_version,
                EffectiveInterval(utc(2026, 1, 1)),
                accountable_assignment_version_id=unrelated_assignment,
            ),
        )
    with pytest.raises(DomainRuleViolation, match="vacant or conflicting"):
        domain.commit_determination(
            meta("provenance-unrelated-determination"),
            ConfigurationDeterminationInput(
                RecordId.new(),
                RecordVersionId.new(),
                relevant_version,
                DeterminationKind.MATERIALITY,
                DeterminationOutcome.MATERIAL,
                "Unrelated accountability must not authorize this assessment",
                EffectiveInterval(utc(2026, 1, 1)),
                accountable_assignment_version_id=unrelated_assignment,
            ),
        )
    assert sqlite_store.count_rows("governing_configuration_designations") == 0
    assert sqlite_store.count_rows("configuration_determinations") == 0

    relevant_actor, _ = add_actor(sqlite_store, "provenance-relevant")
    _, owning_case_assignment = add_role(
        sqlite_store,
        "provenance-owning-case",
        relevant_actor,
        target_type=RoleTargetType.CASE,
        target_id=str(relevant_case),
        case_context_id=relevant_case,
        accountable=True,
    )
    domain.commit_governing_designation(
        meta("provenance-owning-case-governing"),
        GoverningDesignationInput(
            RecordId.new(),
            RecordVersionId.new(),
            relevant_case,
            relevant_version,
            EffectiveInterval(utc(2026, 1, 1)),
            accountable_assignment_version_id=owning_case_assignment,
        ),
    )
    domain.commit_determination(
        meta("provenance-owning-case-determination"),
        ConfigurationDeterminationInput(
            RecordId.new(),
            RecordVersionId.new(),
            relevant_version,
            DeterminationKind.IDENTITY_CONTINUITY,
            DeterminationOutcome.SAME_IDENTITY,
            "Owning-Case accountability is applicable to this Configuration",
            EffectiveInterval(utc(2026, 1, 1)),
            accountable_assignment_version_id=owning_case_assignment,
        ),
    )
    assert sqlite_store.count_rows("governing_configuration_designations") == 1
    assert sqlite_store.count_rows("configuration_determinations") == 1

    narrower_actor, _ = add_actor(sqlite_store, "provenance-narrower")
    add_role(
        sqlite_store,
        "provenance-narrower",
        narrower_actor,
        target_type=RoleTargetType.CONFIGURATION,
        target_id=str(relevant_configuration),
        case_context_id=relevant_case,
        accountable=True,
    )
    with pytest.raises(DomainRuleViolation, match="vacant or conflicting"):
        domain.commit_determination(
            meta("provenance-broad-narrow-conflict"),
            ConfigurationDeterminationInput(
                RecordId.new(),
                RecordVersionId.new(),
                relevant_version,
                DeterminationKind.MATERIALITY,
                DeterminationOutcome.NON_MATERIAL,
                "No implicit precedence may resolve broad and narrow accountability",
                EffectiveInterval(utc(2026, 1, 1)),
                accountable_assignment_version_id=owning_case_assignment,
            ),
        )
    assert sqlite_store.count_rows("configuration_determinations") == 1


def test_domain_idempotency_stale_precondition_contention_and_audit_attribution(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    case_id = RecordId.new()
    version_id = RecordVersionId.new()
    command_meta = meta("domain-idempotency")
    value = CaseVersionInput(
        case_id, version_id, "Idempotent Case", EffectiveInterval(utc(2026, 1, 1))
    )
    domain = service(sqlite_store)
    original = domain.commit_case(command_meta, value)
    replay = domain.commit_case(command_meta, value)
    assert replay == original
    assert sqlite_store.count_rows("paim_cases") == 1
    assert sqlite_store.count_rows("paim_case_versions") == 1
    audit = sqlite_store.get_audit(AuditId.parse(original.audit_id))
    assert audit is not None
    assert audit.principal_id == "principal:technical"
    assert audit.actor_id == "actor:human"
    assert audit.principal_id != audit.actor_id

    with pytest.raises(DomainPreconditionFailed):
        domain.commit_case(
            meta("domain-stale"),
            replace(value, version_id=RecordVersionId.new(), title="stale write"),
        )
    assert sqlite_store.count_rows("paim_case_versions") == 1

    blocked_value = CaseVersionInput(
        RecordId.new(),
        RecordVersionId.new(),
        "Contended Case",
        EffectiveInterval(utc(2026, 1, 1)),
    )
    with sqlite_store.engine.connect() as blocker:
        blocker.exec_driver_sql("BEGIN IMMEDIATE")
        with pytest.raises(WriterContention):
            domain.commit_case(meta("domain-contention"), blocked_value)
        blocker.rollback()
    assert sqlite_store.get_version(blocked_value.version_id) is None
