from __future__ import annotations

from dataclasses import replace

import pytest

from paim.case_continuity import (
    CaseContinuityConflict,
    CaseContinuityService,
    CaseInitiationAuthorityCommand,
    CaseInitiationAuthorityState,
    CommandIdentity,
    MinimalOpenCaseCommand,
)
from paim.domain import AuthorityVersionInput
from paim.integrity import CommandId, EffectiveInterval, FixedClock, RecordId, RecordVersionId
from paim.integrity.semantics import (
    ContextMemberKind,
    ExactContextMember,
    ExactContextSet,
    SemanticContractRef,
)
from paim.operational import AccessEffect, Permission, ScopeType, SourceAccessGrantInput
from paim.operational.application import OperationalApplication
from paim.practitioner_queries import PractitionerQueryService
from paim.responsibility.service import OperationalSliceAAccessPolicy
from tests.helpers import utc
from tests.web_support import WebFixture, grant

NOW = utc(2026, 8, 25)
CONTRACT = SemanticContractRef("paim.case-continuity", "1.0")
PRINCIPAL = "principal:web-practitioner"
ORG = "local:harborlight-disposable"


def identity(key: str, actor_id: RecordId) -> CommandIdentity:
    return CommandIdentity(CommandId.new(), "slice-h0", key, PRINCIPAL, actor_id)


def authority_context(actor_id: RecordId) -> ExactContextSet:
    return ExactContextSet.create(
        (
            ExactContextMember("authorized_actor", ContextMemberKind.RECORD, str(actor_id)),
            ExactContextMember("organization_scope", ContextMemberKind.LITERAL, ORG),
        )
    )


def establish_authority(
    fixture: WebFixture,
    service: CaseContinuityService,
    *,
    state: CaseInitiationAuthorityState = CaseInitiationAuthorityState.ACTIVE,
    use_prefix: str = "small-business",
    key: str = "authority",
) -> CaseInitiationAuthorityCommand:
    command = CaseInitiationAuthorityCommand(
        identity(key, fixture.actor_id),
        RecordId.new(),
        RecordVersionId.new(),
        fixture.actor_id,
        ORG,
        (use_prefix,),
        {
            "authoritative_source": "Harborlight board mandate",
            "source_version": "2026-08-25",
            "scope": ORG,
        },
        state,
        NOW,
        CONTRACT,
        authority_context(fixture.actor_id),
    )
    service.record_case_initiation_authority(command)
    return command


def minimal(
    actor_id: RecordId, *, key: str = "open", use: str = "small-business lending"
) -> MinimalOpenCaseCommand:
    return MinimalOpenCaseCommand(
        identity(key, actor_id),
        CONTRACT,
        ORG,
        "Harborlight Assist — disposable prospective proof",
        use,
        "Whether and how Harborlight should use AI assistance",
        {"system": "Harborlight Assist", "scope": "bounded prospective proof"},
        "finalized",
        "candidate",
        NOW,
        NOW,
    )


def prepare_permissions(fixture: WebFixture) -> None:
    grant(fixture, Permission.OPERATIONAL_ADMIN, "case.initiation-authority.record")
    grant(fixture, Permission.OPERATIONAL_ADMIN, "source-access.manage")
    grant(fixture, Permission.COMMAND, "case.create_open")


def test_minimal_case_initiation_is_atomic_exact_replay_and_grants_no_downstream_authority(
    web_fixture: WebFixture,
) -> None:
    prepare_permissions(web_fixture)
    policy = OperationalSliceAAccessPolicy(web_fixture.operational.operational_store)
    service = CaseContinuityService(web_fixture.operational.domain_store, FixedClock(NOW), policy)
    authority = establish_authority(web_fixture, service)
    request = minimal(web_fixture.actor_id)

    outcome = service.initiate_case(request)
    assert service.initiate_case(request) == outcome
    with pytest.raises(CaseContinuityConflict, match="IDEMPOTENCY KEY REUSE CONFLICT"):
        service.initiate_case(replace(request, bounded_use="small-business changed"))

    case_id = RecordId.parse(outcome.record_id)
    with web_fixture.operational.domain_store.read_transaction() as tx:
        assert tx.case_exists(case_id)
        bases = tx.projection_rows(
            "assignment_basis_versions", basis_source_version_id=str(authority.version_id)
        )
        assignments = tx.projection_rows("responsibility_assignment_versions")
        responsibilities = tx.projection_rows(
            "responsibility_versions", owning_case_id=str(case_id)
        )
        assert len(bases) == len(assignments) == len(responsibilities) == 1
        assert bases[0]["owning_case_id"] == str(case_id)
        source = tx.get_version(authority.version_id)
        assert source is not None
        assert source.content["case_initiation_authority"]["downstream_authority_granted"] is False  # type: ignore[index]

    assert len(outcome.version_ids) == 7


@pytest.mark.parametrize(
    ("permission", "state", "use", "reason"),
    (
        (False, CaseInitiationAuthorityState.ACTIVE, "small-business lending", "software access"),
        (True, CaseInitiationAuthorityState.WITHDRAWN, "small-business lending", "not established"),
        (True, CaseInitiationAuthorityState.ACTIVE, "unrelated domain", "not established"),
    ),
)
def test_missing_access_withdrawn_or_out_of_scope_initiation_has_zero_mutation(
    web_fixture: WebFixture,
    permission: bool,
    state: CaseInitiationAuthorityState,
    use: str,
    reason: str,
) -> None:
    grant(web_fixture, Permission.OPERATIONAL_ADMIN, "case.initiation-authority.record")
    if permission:
        grant(web_fixture, Permission.COMMAND, "case.create_open")
    policy = OperationalSliceAAccessPolicy(web_fixture.operational.operational_store)
    service = CaseContinuityService(web_fixture.operational.domain_store, FixedClock(NOW), policy)
    establish_authority(web_fixture, service, state=state)
    before = web_fixture.operational.operational_store.table_counts(
        ("paim_cases", "record_versions", "assignment_basis_versions")
    )
    with pytest.raises(RuntimeError, match=reason):
        service.initiate_case(minimal(web_fixture.actor_id, use=use))
    assert web_fixture.operational.operational_store.table_counts(tuple(before)) == before


def test_identity_practical_role_and_other_authority_cannot_substitute_for_initiation(
    web_fixture: WebFixture,
) -> None:
    grant(web_fixture, Permission.COMMAND, "case.create_open")
    grant(
        web_fixture,
        Permission.COMMAND,
        "authority.create",
        ScopeType.CASE,
        web_fixture.visible_case_id,
    )
    web_fixture.operational.run_command(
        web_fixture.admin_session,
        action="authority.create",
        idempotency_key="h0-non-substitute-authority",
        case_id=web_fixture.visible_case_id,
        operation=lambda application, meta: application.commit_authority_record(
            meta,
            AuthorityVersionInput(
                RecordId.new(),
                RecordVersionId.new(),
                None,
                None,
                None,
                "decision authority",
                "existing governed authority",
                {"authoritative_source": "bounded decision mandate"},
                "one existing Case",
                "authorize one later Decision only",
                {
                    "case_initiation_authority": {
                        "authorized_actor_id": str(web_fixture.actor_id),
                        "organization_scope": ORG,
                    }
                },
                EffectiveInterval(NOW),
            ),
        ),
    )
    service = CaseContinuityService(
        web_fixture.operational.domain_store,
        FixedClock(NOW),
        OperationalSliceAAccessPolicy(web_fixture.operational.operational_store),
    )
    before = web_fixture.operational.operational_store.table_counts(
        ("paim_cases", "assignment_basis_versions")
    )
    with pytest.raises(
        CaseContinuityConflict, match="pre-Case initiation authority not established"
    ):
        service.initiate_case(minimal(web_fixture.actor_id))
    assert web_fixture.operational.operational_store.table_counts(tuple(before)) == before


def test_withdrawn_successor_makes_predecessor_ineligible_without_retarget(
    web_fixture: WebFixture,
) -> None:
    prepare_permissions(web_fixture)
    service = CaseContinuityService(
        web_fixture.operational.domain_store,
        FixedClock(NOW),
        OperationalSliceAAccessPolicy(web_fixture.operational.operational_store),
    )
    active = establish_authority(web_fixture, service)
    withdrawn = replace(
        active,
        identity=identity("authority-withdraw", web_fixture.actor_id),
        version_id=RecordVersionId.new(),
        state=CaseInitiationAuthorityState.WITHDRAWN,
        expected_version_id=active.version_id,
    )
    service.record_case_initiation_authority(withdrawn)
    before = web_fixture.operational.operational_store.table_counts(
        ("paim_cases", "assignment_basis_versions")
    )
    with pytest.raises(CaseContinuityConflict, match="not established"):
        service.initiate_case(minimal(web_fixture.actor_id))
    assert web_fixture.operational.operational_store.table_counts(tuple(before)) == before
    with web_fixture.operational.domain_store.read_transaction() as tx:
        history = tx.get_history(active.record_id)
    assert {value.version_id for value in history.versions} == {
        active.version_id,
        withdrawn.version_id,
    }


def test_production_source_access_is_exact_durable_and_composition_is_neutral(
    web_fixture: WebFixture,
) -> None:
    prepare_permissions(web_fixture)
    policy = OperationalSliceAAccessPolicy(web_fixture.operational.operational_store)
    service = CaseContinuityService(web_fixture.operational.domain_store, FixedClock(NOW), policy)
    establish_authority(web_fixture, service)
    outcome = service.initiate_case(minimal(web_fixture.actor_id))
    case_id = RecordId.parse(outcome.record_id)
    grant(web_fixture, Permission.CASE_READ, "read", ScopeType.CASE, case_id)

    with web_fixture.operational.domain_store.read_transaction() as tx:
        versions = tuple(
            tx.get_version(RecordVersionId.parse(value)) for value in outcome.version_ids
        )
    assert all(value is not None for value in versions)
    responsibility_version_id = RecordVersionId.parse(outcome.version_ids[2])
    for source in versions:
        assert source is not None
        web_fixture.operational.grant_source_access(
            web_fixture.admin_session,
            principal_id=PRINCIPAL,
            grant=SourceAccessGrantInput(
                "source.read",
                case_id,
                source.version_id,
                source.family,
                (
                    AccessEffect.DENY
                    if source.version_id == responsibility_version_id
                    else AccessEffect.ALLOW
                ),
                NOW,
            ),
        )

    queries = PractitionerQueryService(web_fixture.operational.domain_store, service, policy)
    view = queries.case(
        principal_id=PRINCIPAL,
        actor_id=web_fixture.actor_id,
        case_id=case_id,
        effective_at=NOW,
        known_at=NOW,
    )
    assert view.title.startswith("Harborlight Assist")
    assert view.responsibility_state == "RESPONSIBILITY STATUS NOT SAFELY AVAILABLE"
    assert responsibility_version_id not in view.source_manifest.version_ids
    visible_case_version_id = RecordVersionId.parse(outcome.version_ids[0])
    assert visible_case_version_id in view.source_manifest.version_ids
    assert (
        policy.authorize(
            principal_id=PRINCIPAL,
            actor_id=str(web_fixture.actor_id),
            action="source.read",
            case_id=case_id,
            write=False,
            source_version_id=responsibility_version_id,
            source_family="responsibility",
        )
        is False
    )
    assert policy.authorize(
        principal_id=PRINCIPAL,
        actor_id=str(web_fixture.actor_id),
        action="source.read",
        case_id=case_id,
        write=False,
        source_version_id=visible_case_version_id,
        source_family=None,
    )

    with OperationalApplication(web_fixture.config, FixedClock(NOW)) as restarted:
        restarted_policy = OperationalSliceAAccessPolicy(restarted.operational_store)
        restarted_service = CaseContinuityService(
            restarted.domain_store, FixedClock(NOW), restarted_policy
        )
        restarted_view = PractitionerQueryService(
            restarted.domain_store, restarted_service, restarted_policy
        ).case(
            principal_id=PRINCIPAL,
            actor_id=web_fixture.actor_id,
            case_id=case_id,
            effective_at=NOW,
            known_at=NOW,
        )
        assert restarted_view == view


def test_source_access_successor_is_dual_time_exact_and_family_bound(
    web_fixture: WebFixture,
) -> None:
    prepare_permissions(web_fixture)
    policy = OperationalSliceAAccessPolicy(web_fixture.operational.operational_store)
    service = CaseContinuityService(web_fixture.operational.domain_store, FixedClock(NOW), policy)
    establish_authority(web_fixture, service)
    outcome = service.initiate_case(minimal(web_fixture.actor_id))
    case_id = RecordId.parse(outcome.record_id)
    source_id = RecordVersionId.parse(outcome.version_ids[0])
    grant(web_fixture, Permission.CASE_READ, "read", ScopeType.CASE, case_id)
    source = SourceAccessGrantInput(
        "source.read",
        case_id,
        source_id,
        "prospective-case",
        AccessEffect.ALLOW,
        NOW,
    )
    web_fixture.operational.grant_source_access(
        web_fixture.admin_session, principal_id=PRINCIPAL, grant=source
    )
    later = utc(2026, 8, 26)
    web_fixture.operational.clock = FixedClock(later)
    web_fixture.operational.grant_source_access(
        web_fixture.admin_session,
        principal_id=PRINCIPAL,
        grant=replace(source, effect=AccessEffect.DENY, effective_from=later),
    )
    store = web_fixture.operational.operational_store
    assert store.source_access_allowed(
        principal_id=PRINCIPAL,
        action="source.read",
        case_id=case_id,
        source_version_id=source_id,
        source_family="prospective-case",
        effective_at=NOW,
        known_at=NOW,
    )
    assert not store.source_access_allowed(
        principal_id=PRINCIPAL,
        action="source.read",
        case_id=case_id,
        source_version_id=source_id,
        source_family="prospective-case",
        effective_at=later,
        known_at=later,
    )
    assert not store.source_access_allowed(
        principal_id=PRINCIPAL,
        action="source.read",
        case_id=case_id,
        source_version_id=source_id,
        source_family="authority-record",
        effective_at=NOW,
        known_at=NOW,
    )
