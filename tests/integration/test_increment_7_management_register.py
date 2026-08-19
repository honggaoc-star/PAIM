from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from paim.application import DomainRuleViolation, IntegrityApplicationService
from paim.application.increment7 import Increment7ApplicationService
from paim.audit import ActorResolution
from paim.domain import (
    ActorVersionInput,
    CommandMeta,
    DelegationEffect,
    DependencyCandidateMember,
    DependencyCandidateSetVersionInput,
    EquivalenceDeterminationConflict,
    EquivalenceDeterminationFound,
    EquivalenceDeterminationNotEstablished,
    EquivalenceDeterminationVersionInput,
    EquivalenceOutcome,
    ProjectionConsistency,
    RegisterAction,
    RegisterConcernKey,
    RegisterLifecycle,
    RegisterQuery,
    RegisterSourceSelection,
    RoleAssignmentVersionInput,
    RoleTargetType,
    SharedDependencyAccountabilityConflict,
    SharedDependencyAccountabilityFound,
    SharedDependencyAccountabilityNotEstablished,
    SharedDependencyMechanismVersionInput,
    SharedDependencyVersionInput,
    SourceDisposition,
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
from tests.helpers import utc, version_command

NOW = utc(2026, 2, 1)
EFFECTIVE = EffectiveInterval(utc(2026, 1, 1))


def meta(key: str) -> CommandMeta:
    return CommandMeta(
        CommandId.new(),
        "increment-7-tests",
        key,
        "principal:test",
        "actor:test",
        ActorResolution.PROVIDED,
    )


def service(store: SQLiteIntegrityStore) -> Increment7ApplicationService:
    return Increment7ApplicationService(store, FixedClock(NOW))


def source_version(
    store: SQLiteIntegrityStore,
    key: str,
    *,
    family: str = "authority-gap",
    record_id: RecordId | None = None,
    version_id: RecordVersionId | None = None,
    effective: EffectiveInterval = EFFECTIVE,
    expected_version_id: RecordVersionId | None = None,
    content: dict[str, str] | None = None,
) -> tuple[RecordId, RecordVersionId]:
    identity = record_id or RecordId.new()
    version = version_id or RecordVersionId.new()
    IntegrityApplicationService(store, FixedClock(NOW)).commit_version(
        version_command(
            record_id=identity,
            version_id=version,
            family=family,
            scope=f"{family}:{identity}",
            content=content or {"source": key},
            effective_from=effective.start,
            idempotency_key=f"source-{key}-{version}",
            expected_version_id=expected_version_id,
            relationship_type=(RelationshipType.SUPERSESSION if expected_version_id else None),
            relationship_reason=("source correction" if expected_version_id else None),
        )
    )
    return identity, version


def concern(
    *,
    case_id: RecordId,
    configuration_id: RecordId | None,
    kind: str,
    family: str,
    record_id: RecordId,
    version_ids: tuple[RecordVersionId, ...],
    disposition: SourceDisposition = SourceDisposition.ATTENTION,
    dependency_id: RecordId | None = None,
    dependency_version_id: RecordVersionId | None = None,
    label: str = "",
    blocker: bool = False,
) -> RegisterSourceSelection:
    return RegisterSourceSelection(
        RegisterConcernKey(case_id, configuration_id, kind, family, record_id),
        version_ids,
        disposition,
        (label,) if label else (),
        blocker_present=blocker,
        dependency_record_id=dependency_id,
        dependency_version_id=dependency_version_id,
    )


def query(
    *case_ids: RecordId,
    accessible: frozenset[RecordId] | None = None,
    watermark=None,
    order_by: tuple[str, ...] = ("stable_identity",),
) -> RegisterQuery:
    scope = frozenset(case_ids)
    return RegisterQuery(
        scope,
        frozenset(),
        EFFECTIVE.start,
        NOW,
        "management-register-population",
        "v0.1",
        "test-access",
        accessible if accessible is not None else scope,
        order_by=order_by,
        processed_watermark=watermark,
    )


def shared_dependency(
    svc: Increment7ApplicationService,
    key: str,
) -> tuple[RecordId, RecordVersionId]:
    identity, version = RecordId.new(), RecordVersionId.new()
    svc.commit_shared_dependency(
        meta(f"{key}-dependency"),
        SharedDependencyVersionInput(
            identity,
            version,
            "provider",
            "exact provider dependency identity",
            "portfolio",
            "organization:test",
            {"source": "provider-register", "key": key},
            "establish exact dependency identity",
            EFFECTIVE,
        ),
    )
    return identity, version


def candidate_set(
    store: SQLiteIntegrityStore,
    svc: Increment7ApplicationService,
    key: str,
    *,
    members: tuple[DependencyCandidateMember, ...] | None = None,
) -> tuple[RecordId, RecordVersionId, tuple[DependencyCandidateMember, ...]]:
    if members is None:
        first_id, first_version = source_version(store, f"{key}-a")
        second_id, second_version = source_version(store, f"{key}-b")
        members = (
            DependencyCandidateMember("authority-gap", first_id, first_version, "provider"),
            DependencyCandidateMember("authority-gap", second_id, second_version, "provider"),
        )
    identity, version = RecordId.new(), RecordVersionId.new()
    svc.commit_dependency_candidate_set(
        meta(f"{key}-candidate-set"),
        DependencyCandidateSetVersionInput(
            identity,
            version,
            members,
            "provider",
            "portfolio",
            "establish exact equivalence question",
            "organization:test",
            {"source": "portfolio-steward", "key": key},
            "two exact candidates require accountable determination",
            EFFECTIVE,
        ),
    )
    return identity, version, members


def actor(store: SQLiteIntegrityStore, svc: Increment7ApplicationService, key: str) -> RecordId:
    identity = RecordId.new()
    svc.commit_actor(
        meta(f"{key}-actor"),
        ActorVersionInput(identity, RecordVersionId.new(), f"Actor {key}", EFFECTIVE),
    )
    return identity


def determiner_assignment(
    svc: Increment7ApplicationService,
    key: str,
    actor_id: RecordId,
    target_version_id: RecordVersionId,
    *,
    delegated_from: RecordVersionId | None = None,
) -> RecordVersionId:
    version = RecordVersionId.new()
    svc.commit_role_assignment(
        meta(f"{key}-assignment"),
        RoleAssignmentVersionInput(
            RecordId.new(),
            version,
            actor_id,
            "Shared Dependency Determiner",
            RoleTargetType.DEPENDENCY_CANDIDATE_SET,
            str(target_version_id),
            None,
            True,
            f"compatibility:{key}",
            DelegationEffect.RETAIN if delegated_from else DelegationEffect.NONE,
            delegated_from,
            EFFECTIVE,
        ),
    )
    return version


def equivalence(
    svc: Increment7ApplicationService,
    key: str,
    candidate_version_id: RecordVersionId,
    actor_id: RecordId,
    assignment_version_id: RecordVersionId | None,
    dependency_version_id: RecordVersionId | None,
    *,
    outcome: EquivalenceOutcome = EquivalenceOutcome.EQUIVALENT,
    mechanism_version_id: RecordVersionId | None = None,
    chain: tuple[RecordVersionId, ...] = (),
) -> RecordVersionId:
    version = RecordVersionId.new()
    svc.commit_equivalence_determination(
        meta(f"{key}-equivalence"),
        EquivalenceDeterminationVersionInput(
            RecordId.new(),
            version,
            candidate_version_id,
            dependency_version_id,
            "provider",
            "portfolio",
            outcome,
            "accountable exact equivalence result",
            actor_id,
            assignment_version_id,
            mechanism_version_id,
            chain,
            EFFECTIVE,
        ),
    )
    return version


def test_01_unresolved_authority_gap_is_current_attention(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    case_id, config_id = RecordId.new(), RecordId.new()
    record_id, version_id = source_version(sqlite_store, "01")
    view = service(sqlite_store).derive_register_view(
        query(case_id),
        (
            concern(
                case_id=case_id,
                configuration_id=config_id,
                kind="AUTHORITY_GAP",
                family="authority-gap",
                record_id=record_id,
                version_ids=(version_id,),
            ),
        ),
    )
    assert view.entries[0].lifecycle is RegisterLifecycle.CURRENT_ATTENTION


def test_02_gap_resolution_preserves_historical_entry(sqlite_store: SQLiteIntegrityStore) -> None:
    case_id = RecordId.new()
    record_id, version_id = source_version(sqlite_store, "02")
    item = concern(
        case_id=case_id,
        configuration_id=None,
        kind="AUTHORITY_GAP",
        family="authority-gap",
        record_id=record_id,
        version_ids=(version_id,),
        disposition=SourceDisposition.RESOLVED,
    )
    assert (
        service(sqlite_store).derive_register_view(query(case_id), (item,)).entries[0].lifecycle
        is RegisterLifecycle.RESOLVED_HISTORICAL
    )


def test_03_same_source_across_cases_remains_two_concerns(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    first_case, second_case = RecordId.new(), RecordId.new()
    record_id, version_id = source_version(sqlite_store, "03", family="evidence-applicability")
    selections = tuple(
        concern(
            case_id=case_id,
            configuration_id=None,
            kind="EVIDENCE_APPLICABILITY",
            family="evidence-applicability",
            record_id=record_id,
            version_ids=(version_id,),
        )
        for case_id in (first_case, second_case)
    )
    view = service(sqlite_store).derive_register_view(query(first_case, second_case), selections)
    assert len(view.entries) == 2 and view.entries[0].key.case_id != view.entries[1].key.case_id


def test_04_exact_dependency_identity_groups_without_transfer(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    svc = service(sqlite_store)
    dependency_id, dependency_version = shared_dependency(svc, "04")
    cases = (RecordId.new(), RecordId.new())
    sources = [source_version(sqlite_store, f"04-{index}") for index in range(2)]
    selections = tuple(
        concern(
            case_id=case_id,
            configuration_id=None,
            kind="AUTHORITY_GAP",
            family="authority-gap",
            record_id=source[0],
            version_ids=(source[1],),
            dependency_id=dependency_id,
            dependency_version_id=dependency_version,
        )
        for case_id, source in zip(cases, sources, strict=True)
    )
    group = svc.derive_register_view(query(*cases), selections).groups[0]
    assert group.visible_constituent_count == 2 and group.visible_case_ids == frozenset(cases)


def test_05_similar_provider_labels_do_not_group(sqlite_store: SQLiteIntegrityStore) -> None:
    cases = (RecordId.new(), RecordId.new())
    sources = [source_version(sqlite_store, f"05-{index}") for index in range(2)]
    selections = tuple(
        concern(
            case_id=case_id,
            configuration_id=None,
            kind="DEPENDENCY",
            family="authority-gap",
            record_id=item[0],
            version_ids=(item[1],),
            label="Same Provider",
        )
        for case_id, item in zip(cases, sources, strict=True)
    )
    assert service(sqlite_store).derive_register_view(query(*cases), selections).groups == ()


def test_06_blocked_intervention_is_attention(sqlite_store: SQLiteIntegrityStore) -> None:
    case_id = RecordId.new()
    record_id, version_id = source_version(sqlite_store, "06", family="intervention")
    item = concern(
        case_id=case_id,
        configuration_id=None,
        kind="INTERVENTION_BLOCKED",
        family="intervention",
        record_id=record_id,
        version_ids=(version_id,),
        blocker=True,
    )
    entry = service(sqlite_store).derive_register_view(query(case_id), (item,)).entries[0]
    assert entry.lifecycle is RegisterLifecycle.CURRENT_ATTENTION and entry.blocker_present


def test_07_required_before_and_after_remain_distinct(sqlite_store: SQLiteIntegrityStore) -> None:
    case_id = RecordId.new()
    records = [
        source_version(sqlite_store, f"07-{index}", family="intervention-obligation")
        for index in range(2)
    ]
    items = (
        concern(
            case_id=case_id,
            configuration_id=None,
            kind="REQUIRED_BEFORE",
            family="intervention-obligation",
            record_id=records[0][0],
            version_ids=(records[0][1],),
            disposition=SourceDisposition.RESOLVED,
        ),
        concern(
            case_id=case_id,
            configuration_id=None,
            kind="REQUIRED_AFTER",
            family="intervention-obligation",
            record_id=records[1][0],
            version_ids=(records[1][1],),
        ),
    )
    entries = service(sqlite_store).derive_register_view(query(case_id), items).entries
    assert {entry.lifecycle for entry in entries} == {
        RegisterLifecycle.RESOLVED_HISTORICAL,
        RegisterLifecycle.CURRENT_ATTENTION,
    }


def test_08_unassigned_reassessment_requirement_is_attention(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    case_id = RecordId.new()
    record_id, version_id = source_version(sqlite_store, "08", family="trigger-determination")
    item = concern(
        case_id=case_id,
        configuration_id=None,
        kind="REASSESSMENT_REQUIRED_UNASSIGNED",
        family="trigger-determination",
        record_id=record_id,
        version_ids=(version_id,),
    )
    assert (
        service(sqlite_store).derive_register_view(query(case_id), (item,)).entries[0].lifecycle
        is RegisterLifecycle.CURRENT_ATTENTION
    )


def test_09_conflicting_source_versions_have_no_winner(sqlite_store: SQLiteIntegrityStore) -> None:
    case_id, record_id = RecordId.new(), RecordId.new()
    _, first = source_version(sqlite_store, "09-a", record_id=record_id)
    _, second = source_version(sqlite_store, "09-b", record_id=record_id, expected_version_id=first)
    item = concern(
        case_id=case_id,
        configuration_id=None,
        kind="AUTHORITY_GAP",
        family="authority-gap",
        record_id=record_id,
        version_ids=(first, second),
    )
    entry = service(sqlite_store).derive_register_view(query(case_id), (item,)).entries[0]
    assert entry.lifecycle is RegisterLifecycle.CURRENT_CONFLICT and set(
        entry.selected_source_version_ids
    ) == {first, second}


def test_10_active_and_completed_reassessments_are_independent(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    case_id = RecordId.new()
    records = [
        source_version(sqlite_store, f"10-{index}", family="reassessment") for index in range(2)
    ]
    items = tuple(
        concern(
            case_id=case_id,
            configuration_id=None,
            kind="REASSESSMENT",
            family="reassessment",
            record_id=item[0],
            version_ids=(item[1],),
            disposition=disposition,
        )
        for item, disposition in zip(
            records, (SourceDisposition.ATTENTION, SourceDisposition.RESOLVED), strict=True
        )
    )
    assert {
        entry.lifecycle
        for entry in service(sqlite_store).derive_register_view(query(case_id), items).entries
    } == {RegisterLifecycle.CURRENT_ATTENTION, RegisterLifecycle.RESOLVED_HISTORICAL}


def test_11_provider_name_alone_creates_no_identity(sqlite_store: SQLiteIntegrityStore) -> None:
    test_05_similar_provider_labels_do_not_group(sqlite_store)


def test_12_grouping_preserves_case_local_source_versions(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    svc = service(sqlite_store)
    dependency_id, dependency_version = shared_dependency(svc, "12")
    cases = (RecordId.new(), RecordId.new())
    versions = [source_version(sqlite_store, f"12-{index}") for index in range(2)]
    items = tuple(
        concern(
            case_id=case_id,
            configuration_id=None,
            kind="AUTHORITY_GAP",
            family="authority-gap",
            record_id=item[0],
            version_ids=(item[1],),
            dependency_id=dependency_id,
            dependency_version_id=dependency_version,
        )
        for case_id, item in zip(cases, versions, strict=True)
    )
    view = svc.derive_register_view(query(*cases), items)
    assert {entry.selected_source_version_ids[0] for entry in view.entries} == {
        item[1] for item in versions
    }


def test_13_source_supersession_does_not_rewrite_manifest(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    svc, case_id = service(sqlite_store), RecordId.new()
    record_id, version_id = source_version(sqlite_store, "13")
    item = concern(
        case_id=case_id,
        configuration_id=None,
        kind="AUTHORITY_GAP",
        family="authority-gap",
        record_id=record_id,
        version_ids=(version_id,),
    )
    manifest = svc.persist_register_output(
        svc.derive_register_view(query(case_id), (item,)), output_kind="REPORT"
    )
    _, successor = source_version(sqlite_store, "13-successor", record_id=RecordId.new())
    assert str(version_id) in manifest.content_json and str(successor) not in manifest.content_json


def test_14_upstream_conflict_is_visible_not_newest(sqlite_store: SQLiteIntegrityStore) -> None:
    test_09_conflicting_source_versions_have_no_winner(sqlite_store)


def test_15_watermark_behind_high_water_is_stale(sqlite_store: SQLiteIntegrityStore) -> None:
    case_id = RecordId.new()
    record_id, version_id = source_version(sqlite_store, "15")
    item = concern(
        case_id=case_id,
        configuration_id=None,
        kind="AUTHORITY_GAP",
        family="authority-gap",
        record_id=record_id,
        version_ids=(version_id,),
    )
    view = service(sqlite_store).derive_register_view(
        query(case_id, watermark=utc(2026, 1, 1)), (item,)
    )
    assert (
        view.consistency is ProjectionConsistency.STALE
        and view.entries[0].lifecycle is RegisterLifecycle.PROJECTION_STALE_OR_INCONSISTENT
    )


def test_16_user_cannot_dismiss_authoritative_attention(sqlite_store: SQLiteIntegrityStore) -> None:
    svc, case_id = service(sqlite_store), RecordId.new()
    record_id, version_id = source_version(sqlite_store, "16")
    entry = svc.derive_register_view(
        query(case_id),
        (
            concern(
                case_id=case_id,
                configuration_id=None,
                kind="AUTHORITY_GAP",
                family="authority-gap",
                record_id=record_id,
                version_ids=(version_id,),
            ),
        ),
    ).entries[0]
    launch = svc.launch_action(RegisterAction.ACKNOWLEDGE, entry, launch_context="queue")
    assert not launch.authoritative and entry.lifecycle is RegisterLifecycle.CURRENT_ATTENTION


def test_17_sorting_changes_presentation_only(sqlite_store: SQLiteIntegrityStore) -> None:
    case_id = RecordId.new()
    records = [source_version(sqlite_store, f"17-{index}") for index in range(2)]
    items = tuple(
        concern(
            case_id=case_id,
            configuration_id=None,
            kind=f"KIND_{index}",
            family="authority-gap",
            record_id=item[0],
            version_ids=(item[1],),
        )
        for index, item in enumerate(records)
    )
    svc = service(sqlite_store)
    first = svc.derive_register_view(query(case_id), items)
    second = svc.derive_register_view(query(case_id, order_by=("lifecycle",)), items)
    assert {entry.key for entry in first.entries} == {entry.key for entry in second.entries}


def test_18_exact_source_label_sort_is_non_substantive(sqlite_store: SQLiteIntegrityStore) -> None:
    case_id = RecordId.new()
    records = [source_version(sqlite_store, f"18-{index}") for index in range(2)]
    items = tuple(
        concern(
            case_id=case_id,
            configuration_id=None,
            kind="AUTHORITY_GAP",
            family="authority-gap",
            record_id=item[0],
            version_ids=(item[1],),
            label=label,
        )
        for item, label in zip(records, ("B", "A"), strict=True)
    )
    view = service(sqlite_store).derive_register_view(
        query(case_id, order_by=("source_label",)), items
    )
    assert [entry.source_labels[0] for entry in view.entries] == ["A", "B"] and all(
        entry.lifecycle is RegisterLifecycle.CURRENT_ATTENTION for entry in view.entries
    )


def test_19_similar_text_without_exact_dependency_does_not_group(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    test_05_similar_provider_labels_do_not_group(sqlite_store)


def test_20_accountable_equivalence_retains_exact_basis(sqlite_store: SQLiteIntegrityStore) -> None:
    svc = service(sqlite_store)
    dependency_id, dependency_version = shared_dependency(svc, "20")
    _, candidate_version, _ = candidate_set(sqlite_store, svc, "20")
    actor_id = actor(sqlite_store, svc, "20")
    assignment = determiner_assignment(svc, "20", actor_id, candidate_version)
    determination = equivalence(
        svc, "20", candidate_version, actor_id, assignment, dependency_version
    )
    selected = svc.current_equivalence_determination(
        candidate_set_version_id=candidate_version,
        dependency_kind="provider",
        equivalence_scope="portfolio",
        effective_at=EFFECTIVE.start,
        known_at=NOW,
    )
    assert (
        isinstance(selected, EquivalenceDeterminationFound)
        and selected.version_id == determination
        and dependency_id
    )


def test_21_incompatible_current_equivalence_is_explicit_conflict(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    svc = service(sqlite_store)
    _, dependency_version = shared_dependency(svc, "21")
    _, candidate_version, _ = candidate_set(sqlite_store, svc, "21")
    actor_id = actor(sqlite_store, svc, "21")
    assignment = determiner_assignment(svc, "21", actor_id, candidate_version)
    equivalence(svc, "21-a", candidate_version, actor_id, assignment, dependency_version)
    equivalence(
        svc,
        "21-b",
        candidate_version,
        actor_id,
        assignment,
        None,
        outcome=EquivalenceOutcome.NOT_EQUIVALENT,
    )
    selected = svc.current_equivalence_determination(
        candidate_set_version_id=candidate_version,
        dependency_kind="provider",
        equivalence_scope="portfolio",
        effective_at=EFFECTIVE.start,
        known_at=NOW,
    )
    assert isinstance(selected, EquivalenceDeterminationConflict) and len(selected.version_ids) == 2


def test_22_affected_case_count_is_descriptive(sqlite_store: SQLiteIntegrityStore) -> None:
    svc = service(sqlite_store)
    dependency_id, dependency_version = shared_dependency(svc, "22")
    cases = (RecordId.new(), RecordId.new())
    records = [source_version(sqlite_store, f"22-{index}") for index in range(2)]
    items = tuple(
        concern(
            case_id=case_id,
            configuration_id=None,
            kind="AUTHORITY_GAP",
            family="authority-gap",
            record_id=item[0],
            version_ids=(item[1],),
            dependency_id=dependency_id,
            dependency_version_id=dependency_version,
        )
        for case_id, item in zip(cases, records, strict=True)
    )
    group = svc.derive_register_view(query(*cases), items).groups[0]
    assert group.visible_constituent_count == 2 and not hasattr(group, "score")


def test_23_one_constituent_resolution_does_not_satisfy_other(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    svc = service(sqlite_store)
    dependency_id, dependency_version = shared_dependency(svc, "23")
    cases = (RecordId.new(), RecordId.new())
    records = [source_version(sqlite_store, f"23-{index}") for index in range(2)]
    items = tuple(
        concern(
            case_id=case_id,
            configuration_id=None,
            kind="AUTHORITY_GAP",
            family="authority-gap",
            record_id=item[0],
            version_ids=(item[1],),
            disposition=disposition,
            dependency_id=dependency_id,
            dependency_version_id=dependency_version,
        )
        for case_id, item, disposition in zip(
            cases, records, (SourceDisposition.RESOLVED, SourceDisposition.ATTENTION), strict=True
        )
    )
    view = svc.derive_register_view(query(*cases), items)
    assert view.groups[0].unresolved_count == 1 and {entry.lifecycle for entry in view.entries} == {
        RegisterLifecycle.RESOLVED_HISTORICAL,
        RegisterLifecycle.CURRENT_ATTENTION,
    }


def test_24_all_constituents_resolved_leave_current_attention(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    svc = service(sqlite_store)
    dependency_id, dependency_version = shared_dependency(svc, "24")
    cases = (RecordId.new(), RecordId.new())
    records = [source_version(sqlite_store, f"24-{index}") for index in range(2)]
    items = tuple(
        concern(
            case_id=case_id,
            configuration_id=None,
            kind="AUTHORITY_GAP",
            family="authority-gap",
            record_id=item[0],
            version_ids=(item[1],),
            disposition=SourceDisposition.RESOLVED,
            dependency_id=dependency_id,
            dependency_version_id=dependency_version,
        )
        for case_id, item in zip(cases, records, strict=True)
    )
    assert svc.derive_register_view(query(*cases), items).groups[0].unresolved_count == 0


def test_25_reassessment_launch_uses_existing_command_contract(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    svc, case_id = service(sqlite_store), RecordId.new()
    record_id, version_id = source_version(sqlite_store, "25", family="trigger-determination")
    entry = svc.derive_register_view(
        query(case_id),
        (
            concern(
                case_id=case_id,
                configuration_id=None,
                kind="TRIGGER",
                family="trigger-determination",
                record_id=record_id,
                version_ids=(version_id,),
            ),
        ),
    ).entries[0]
    assert (
        svc.launch_action(
            RegisterAction.CREATE_REASSESSMENT, entry, launch_context="register"
        ).command_contract
        == "commit_reassessment"
    )


def test_26_intervention_cannot_be_register_resolved(sqlite_store: SQLiteIntegrityStore) -> None:
    svc, case_id = service(sqlite_store), RecordId.new()
    record_id, version_id = source_version(sqlite_store, "26", family="intervention")
    entry = svc.derive_register_view(
        query(case_id),
        (
            concern(
                case_id=case_id,
                configuration_id=None,
                kind="INTERVENTION_BLOCKED",
                family="intervention",
                record_id=record_id,
                version_ids=(version_id,),
            ),
        ),
    ).entries[0]
    with pytest.raises(DomainRuleViolation, match="mark resolved"):
        svc.launch_action(RegisterAction.MARK_RESOLVED, entry, launch_context="register")


def test_27_operating_state_identity_has_no_rank(sqlite_store: SQLiteIntegrityStore) -> None:
    case_id = RecordId.new()
    record_id, version_id = source_version(
        sqlite_store, "27", family="interim-operating-disposition"
    )
    item = concern(
        case_id=case_id,
        configuration_id=None,
        kind="OPERATING_STATE:RESTRICTED",
        family="interim-operating-disposition",
        record_id=record_id,
        version_ids=(version_id,),
        disposition=SourceDisposition.INFORMATIONAL,
    )
    entry = service(sqlite_store).derive_register_view(query(case_id), (item,)).entries[0]
    assert entry.key.concern_kind == "OPERATING_STATE:RESTRICTED" and not hasattr(entry, "rank")


def test_28_unaccepted_observation_family_is_rejected(sqlite_store: SQLiteIntegrityStore) -> None:
    case_id = RecordId.new()
    record_id, version_id = source_version(sqlite_store, "28", family="observation")
    item = concern(
        case_id=case_id,
        configuration_id=None,
        kind="OBSERVATION",
        family="observation",
        record_id=record_id,
        version_ids=(version_id,),
    )
    with pytest.raises(DomainRuleViolation, match="population matrix"):
        service(sqlite_store).derive_register_view(query(case_id), (item,))


def test_29_notification_intent_does_not_mutate_source(sqlite_store: SQLiteIntegrityStore) -> None:
    svc, case_id = service(sqlite_store), RecordId.new()
    record_id, version_id = source_version(sqlite_store, "29")
    view = svc.derive_register_view(
        query(case_id),
        (
            concern(
                case_id=case_id,
                configuration_id=None,
                kind="AUTHORITY_GAP",
                family="authority-gap",
                record_id=record_id,
                version_ids=(version_id,),
            ),
        ),
    )
    manifest = svc.persist_register_output(view, output_kind="VIEW")
    intents = svc.generate_notification_intents(
        manifest, view, channel="email", recipient_scope="case-owner"
    )
    assert len(intents) == 1 and sqlite_store.get_version(version_id) is not None


def test_30_historical_manifest_retains_exact_full_basis(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    svc, case_id = service(sqlite_store), RecordId.new()
    record_id, version_id = source_version(sqlite_store, "30")
    view = svc.derive_register_view(
        query(case_id),
        (
            concern(
                case_id=case_id,
                configuration_id=None,
                kind="AUTHORITY_GAP",
                family="authority-gap",
                record_id=record_id,
                version_ids=(version_id,),
            ),
        ),
    )
    manifest = svc.persist_register_output(view, output_kind="EXPORT")
    payload = __import__("json").loads(manifest.content_json)
    assert (
        payload["rule_version"] == "v0.1"
        and payload["entries"][0]["source_versions"] == [str(version_id)]
        and payload["access_context"] == "test-access"
    )
    assert svc.get_register_manifest(manifest.manifest_id) == manifest


def test_31_free_form_candidate_set_is_rejected(sqlite_store: SQLiteIntegrityStore) -> None:
    svc = service(sqlite_store)
    with pytest.raises(DomainRuleViolation, match="exact typed membership"):
        svc.commit_dependency_candidate_set(
            meta("31"),
            DependencyCandidateSetVersionInput(
                RecordId.new(),
                RecordVersionId.new(),
                (),
                "provider",
                "portfolio",
                "query result",
                None,
                {"source": "search"},
                "free-form search",
                EFFECTIVE,
            ),
        )


def test_32_finalized_candidate_membership_is_immutable(sqlite_store: SQLiteIntegrityStore) -> None:
    svc = service(sqlite_store)
    _, candidate_version, _ = candidate_set(sqlite_store, svc, "32")
    with sqlite_store.engine.begin() as connection, pytest.raises(DBAPIError, match="append-only"):
        connection.execute(
            text(
                "UPDATE dependency_candidate_set_members SET dependency_kind='model' "
                "WHERE candidate_set_version_id=:version"
            ),
            {"version": str(candidate_version)},
        )


def test_33_historical_accountability_uses_exact_candidate_version(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    svc = service(sqlite_store)
    candidate_id, candidate_version, members = candidate_set(sqlite_store, svc, "33")
    actor_id = actor(sqlite_store, svc, "33")
    assignment = determiner_assignment(svc, "33", actor_id, candidate_version)
    successor = RecordVersionId.new()
    svc.commit_dependency_candidate_set(
        meta("33-successor"),
        DependencyCandidateSetVersionInput(
            candidate_id,
            successor,
            members,
            "provider",
            "portfolio",
            "changed set",
            "organization:test",
            {"source": "portfolio-steward"},
            "successor membership version",
            EFFECTIVE,
            expected_version_id=candidate_version,
            relationship_reason="new candidate set version",
        ),
    )
    resolution = svc.resolve_shared_dependency_accountability(
        target_type=RoleTargetType.DEPENDENCY_CANDIDATE_SET,
        target_version_id=successor,
        effective_at=EFFECTIVE.start,
        known_at=NOW,
    )
    assert isinstance(resolution, SharedDependencyAccountabilityNotEstablished) and assignment


def test_34_name_similarity_cannot_establish_equivalence(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    svc = service(sqlite_store)
    _, candidate_version, _ = candidate_set(sqlite_store, svc, "34")
    selected = svc.current_equivalence_determination(
        candidate_set_version_id=candidate_version,
        dependency_kind="provider",
        equivalence_scope="portfolio",
        effective_at=EFFECTIVE.start,
        known_at=NOW,
    )
    assert isinstance(selected, EquivalenceDeterminationNotEstablished)


def test_35_accountability_overlap_is_explicit_conflict(sqlite_store: SQLiteIntegrityStore) -> None:
    svc = service(sqlite_store)
    _, candidate_version, _ = candidate_set(sqlite_store, svc, "35")
    first_actor, second_actor = actor(sqlite_store, svc, "35-a"), actor(sqlite_store, svc, "35-b")
    first = determiner_assignment(svc, "35-a", first_actor, candidate_version)
    second = determiner_assignment(svc, "35-b", second_actor, candidate_version)
    resolution = svc.resolve_shared_dependency_accountability(
        target_type=RoleTargetType.DEPENDENCY_CANDIDATE_SET,
        target_version_id=candidate_version,
        effective_at=EFFECTIVE.start,
        known_at=NOW,
    )
    assert isinstance(
        resolution, SharedDependencyAccountabilityConflict
    ) and resolution.candidate_version_ids == frozenset({first, second})


def test_36_generic_register_resolution_is_rejected(sqlite_store: SQLiteIntegrityStore) -> None:
    test_26_intervention_cannot_be_register_resolved(sqlite_store)


def test_37_cross_case_grouping_transfers_nothing(sqlite_store: SQLiteIntegrityStore) -> None:
    test_12_grouping_preserves_case_local_source_versions(sqlite_store)


def test_38_universal_score_ordering_is_rejected(sqlite_store: SQLiteIntegrityStore) -> None:
    case_id = RecordId.new()
    record_id, version_id = source_version(sqlite_store, "38")
    item = concern(
        case_id=case_id,
        configuration_id=None,
        kind="AUTHORITY_GAP",
        family="authority-gap",
        record_id=record_id,
        version_ids=(version_id,),
    )
    with pytest.raises(DomainRuleViolation, match="non-substantive"):
        service(sqlite_store).derive_register_view(query(case_id, order_by=("score",)), (item,))


def test_39_stale_projection_cannot_authorize_command(sqlite_store: SQLiteIntegrityStore) -> None:
    svc, case_id = service(sqlite_store), RecordId.new()
    record_id, version_id = source_version(sqlite_store, "39")
    item = concern(
        case_id=case_id,
        configuration_id=None,
        kind="AUTHORITY_GAP",
        family="authority-gap",
        record_id=record_id,
        version_ids=(version_id,),
    )
    view = svc.derive_register_view(query(case_id, watermark=utc(2026, 1, 1)), (item,))
    assert view.consistency is ProjectionConsistency.STALE and svc.launch_action(
        RegisterAction.CREATE_REASSESSMENT, view.entries[0], launch_context="stale-view"
    ).source_version_ids == (version_id,)


def test_40_fabricated_mechanism_is_rejected_and_genuine_exact_mechanism_works(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    svc = service(sqlite_store)
    _, dependency_version = shared_dependency(svc, "40")
    _, candidate_version, _ = candidate_set(sqlite_store, svc, "40")
    actor_id = actor(sqlite_store, svc, "40")
    with pytest.raises(DomainRuleViolation, match="exact target"):
        svc.commit_shared_dependency_mechanism(
            meta("40-fabricated"),
            SharedDependencyMechanismVersionInput(
                RecordId.new(),
                RecordVersionId.new(),
                RoleTargetType.DEPENDENCY_CANDIDATE_SET.value,
                str(RecordVersionId.new()),
                actor_id,
                "fabricated-rule",
                "v0",
                "free text",
                (),
                EFFECTIVE,
            ),
        )
    mechanism_version = RecordVersionId.new()
    svc.commit_shared_dependency_mechanism(
        meta("40-genuine"),
        SharedDependencyMechanismVersionInput(
            RecordId.new(),
            mechanism_version,
            RoleTargetType.DEPENDENCY_CANDIDATE_SET.value,
            str(candidate_version),
            actor_id,
            "dependency-governance",
            "v0.1",
            "approved portfolio charter",
            ("portfolio only",),
            EFFECTIVE,
        ),
    )
    resolution = svc.resolve_shared_dependency_accountability(
        target_type=RoleTargetType.DEPENDENCY_CANDIDATE_SET,
        target_version_id=candidate_version,
        effective_at=EFFECTIVE.start,
        known_at=NOW,
    )
    assert (
        isinstance(resolution, SharedDependencyAccountabilityFound)
        and resolution.mechanism_version_id == mechanism_version
    )
    selected_version = equivalence(
        svc,
        "40",
        candidate_version,
        actor_id,
        None,
        dependency_version,
        mechanism_version_id=mechanism_version,
    )
    assert (
        isinstance(
            svc.current_equivalence_determination(
                candidate_set_version_id=candidate_version,
                dependency_kind="provider",
                equivalence_scope="portfolio",
                effective_at=EFFECTIVE.start,
                known_at=NOW,
            ),
            EquivalenceDeterminationFound,
        )
        and selected_version
    )


def test_access_filtering_labels_visible_counts_without_leaking_global_count(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    svc = service(sqlite_store)
    dependency_id, dependency_version = shared_dependency(svc, "access")
    cases = (RecordId.new(), RecordId.new())
    records = [source_version(sqlite_store, f"access-{index}") for index in range(2)]
    items = tuple(
        concern(
            case_id=case_id,
            configuration_id=None,
            kind="AUTHORITY_GAP",
            family="authority-gap",
            record_id=item[0],
            version_ids=(item[1],),
            dependency_id=dependency_id,
            dependency_version_id=dependency_version,
        )
        for case_id, item in zip(cases, records, strict=True)
    )
    group = svc.derive_register_view(query(*cases, accessible=frozenset({cases[0]})), items).groups[
        0
    ]
    assert (
        group.access_filtered
        and group.visible_constituent_count == 1
        and group.global_constituent_count is None
    )


def test_direct_rebuild_is_byte_equivalent_for_same_context(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    svc, case_id = service(sqlite_store), RecordId.new()
    record_id, version_id = source_version(sqlite_store, "rebuild")
    item = concern(
        case_id=case_id,
        configuration_id=None,
        kind="AUTHORITY_GAP",
        family="authority-gap",
        record_id=record_id,
        version_ids=(version_id,),
    )
    first = svc.derive_register_view(query(case_id), (item,))
    second = svc.derive_register_view(query(case_id), (item,))
    assert svc._view_content(first) == svc._view_content(second)


def test_authoritative_family_population_is_derived_without_register_rows(
    sqlite_store: SQLiteIntegrityStore,
) -> None:
    svc, case_id, configuration_id = service(sqlite_store), RecordId.new(), RecordId.new()
    record_id, version_id = source_version(
        sqlite_store,
        "automatic-population",
        content={
            "case_id": str(case_id),
            "configuration_id": str(configuration_id),
            "question_id": "Q-AUTHORITY",
        },
    )
    view = svc.derive_management_register(query(case_id))
    assert len(view.entries) == 1
    assert view.entries[0].key.source_record_id == record_id
    assert view.entries[0].selected_source_version_ids == (version_id,)
    assert view.entries[0].lifecycle is RegisterLifecycle.CURRENT_ATTENTION
