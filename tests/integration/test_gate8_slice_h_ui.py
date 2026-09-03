from __future__ import annotations

import json
from dataclasses import replace
from datetime import timedelta

import pytest

from paim.application import Increment3ApplicationService
from paim.assessment_review import (
    AssessmentContent,
    AssessmentLane,
    AssessmentReviewService,
)
from paim.audit import ActorResolution
from paim.case_continuity import CaseContinuityService, CaseInitiationAuthorityState
from paim.continuing_review import (
    ContinuingReviewService,
    RecordEventReviewAttentionCommand,
    ReviewFocus,
    ReviewRecordFacts,
)
from paim.domain import AuthorityVersionInput, CommandMeta
from paim.integrity import CommandId, EffectiveInterval, FixedClock, RecordId, RecordVersionId
from paim.operational import (
    AccessEffect,
    AccessGrantInput,
    OperationalApplication,
    Permission,
    PrincipalStatus,
    ScopeType,
    SourceAccessGrantInput,
)
from paim.operational.models import AccessDenied
from paim.prospective_decision import ProspectiveDecisionService
from paim.quantitative_claims import QuantitativeClaimService, QuantitativeClaimType
from paim.responsibility.initial_setup import InitialAssessmentSetupService
from paim.responsibility.models import ObligationKind
from paim.responsibility.service import (
    OperationalSliceAAccessPolicy,
    ProjectionFact,
    ResponsibilityWorkService,
)
from tests.integration.test_gate8_slice_a_responsibility_work import (
    command as slice_a_command,
)
from tests.integration.test_gate8_slice_b_case_continuity import NOW as PROSPECTIVE_NOW
from tests.integration.test_gate8_slice_b_case_continuity import RECORDED, ExactAccess
from tests.integration.test_gate8_slice_c_assessment_review import (
    adequacy_command,
    finish_command,
    identity,
)
from tests.integration.test_gate8_slice_c_assessment_review import (
    fixture as slice_c_fixture,
)
from tests.integration.test_gate8_slice_d_integration_decision import (
    SliceDFixture,
    integration_command,
    proposal_command,
    slice_d_fixture,
)
from tests.integration.test_gate8_slice_e_continuing_review import (
    ASSESSED_SCOPE,
    CONTRACT,
    KNOWLEDGE,
    REVIEW_PURPOSE,
    slice_e_fixture,
)
from tests.integration.test_gate8_slice_f_quantitative_claims import (
    KNOWN as QUANTITATIVE_KNOWN,
)
from tests.integration.test_gate8_slice_f_quantitative_claims import (
    SliceFFixture,
    claim_command,
    comparability_command,
)
from tests.integration.test_gate8_slice_h0_prerequisites import (
    NOW as H0_NOW,
)
from tests.integration.test_gate8_slice_h0_prerequisites import (
    establish_authority,
    prepare_permissions,
)
from tests.integration.test_gate8_slice_h0_prerequisites import identity as h0_identity
from tests.web_support import ORIGIN, TOKEN, WebFixture, csrf_from, grant, login

_PROSPECTIVE_VERSION_TABLES = (
    "case_continuity_status_versions",
    "governing_configuration_designations",
    "responsibility_versions",
    "assignment_basis_versions",
    "responsibility_assignment_versions",
    "case_work_versions",
    "assessment_candidate_versions",
    "assessment_readiness_versions",
    "assessment_adequacy_versions",
    "assessment_reliance_versions",
    "prospective_integration_versions",
    "prospective_decision_versions",
    "prospective_decision_authorization_versions",
    "prospective_decision_confirmation_versions",
    "planned_review_point_versions",
    "review_attention_event_versions",
    "review_episode_versions",
    "quantitative_claim_versions",
    "quantitative_comparability_versions",
)


def _prepare_browser_access(fixture: WebFixture, case_id: RecordId) -> None:
    grant(fixture, Permission.CASE_READ, "read", ScopeType.CASE, case_id)
    grant(fixture, Permission.OPERATIONAL_ADMIN, "source-access.manage")
    for action in ("integration.complete", "decision.propose", "decision.authorize"):
        grant(fixture, Permission.COMMAND, action, ScopeType.CASE, case_id)


def _use_fixture_clock(fixture: WebFixture) -> None:
    clock = FixedClock(fixture.now.value)
    policy = OperationalSliceAAccessPolicy(fixture.operational.operational_store)
    fixture.operational.clock = clock
    fixture.operational._case_continuity = CaseContinuityService(  # type: ignore[attr-defined]
        fixture.operational.domain_store, clock, policy
    )
    fixture.operational._initial_assessment_setup = (  # type: ignore[attr-defined]
        InitialAssessmentSetupService(fixture.operational.domain_store, clock, policy)
    )
    fixture.operational._assessment_review = AssessmentReviewService(  # type: ignore[attr-defined]
        fixture.operational.domain_store, clock, policy
    )
    fixture.operational._prospective_decision = ProspectiveDecisionService(  # type: ignore[attr-defined]
        fixture.operational.domain_store, clock, policy
    )
    fixture.operational._continuing_review = ContinuingReviewService(  # type: ignore[attr-defined]
        fixture.operational.domain_store, clock, policy
    )


def _grant_all_case_sources(
    fixture: WebFixture,
    case_id: RecordId,
    configuration_id: RecordId,
    *,
    principal_id: str = "principal:web-practitioner",
    effective_from=None,
) -> None:
    sources: dict[RecordVersionId, str] = {}
    for source in fixture.operational.domain_store.m1b_versions(
        case_id=case_id,
        visible_configuration_ids=frozenset({configuration_id}),
    ):
        sources[source.version_id] = source.family
    with fixture.operational.domain_store.read_transaction() as tx:
        for table in _PROSPECTIVE_VERSION_TABLES:
            for row in tx.projection_rows(table):
                version_id = RecordVersionId.parse(str(row["version_id"]))
                source = tx.get_version(version_id)
                if source is not None:
                    sources[version_id] = source.family
                if table == "assignment_basis_versions":
                    authority_id = RecordVersionId.parse(str(row["basis_source_version_id"]))
                    authority = tx.get_version(authority_id)
                    if authority is not None:
                        sources[authority_id] = authority.family
        for member in tx.projection_rows("exact_context_members"):
            if member["member_kind"] == "VERSION":
                version_id = RecordVersionId.parse(str(member["identity"]))
                source = tx.get_version(version_id)
                if source is not None:
                    sources[version_id] = source.family
        for version_id in tuple(sources):
            closure = (
                fixture.operational._reconstruction._source_closure(tx, version_id)  # type: ignore[attr-defined]
            )
            if closure is None:
                continue
            for source_id in closure:
                source = tx.get_version(source_id)
                if source is not None:
                    sources[source_id] = source.family
    for version_id, family in sources.items():
        fixture.operational.grant_source_access(
            fixture.admin_session,
            principal_id=principal_id,
            grant=SourceAccessGrantInput(
                "source.read",
                case_id,
                version_id,
                family,
                AccessEffect.ALLOW,
                effective_from or fixture.now.value,
            ),
        )


def _submit_action(
    fixture: WebFixture,
    *,
    case_id: RecordId,
    responsibility_version_id: RecordVersionId,
    payload: dict[str, str],
) -> None:
    path = f"/cases/{case_id}/actions/{responsibility_version_id}"
    page = fixture.client.get(path)
    assert page.status_code == 200, page.text
    reviewed = fixture.client.post(
        f"{path}/review",
        data={"csrf_token": csrf_from(page.text), **payload},
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    assert reviewed.status_code == 303
    confirmation = fixture.client.get(reviewed.headers["location"])
    assert confirmation.status_code == 200
    committed = fixture.client.post(
        confirmation.url.path.replace("/confirm/", "/commit/"),
        data={"csrf_token": csrf_from(confirmation.text)},
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    assert committed.status_code == 303, committed.text
    assert committed.headers["location"] == f"/cases/{case_id}"


def _establish_value_work(web_fixture: WebFixture, fx: object, key: str) -> object:
    opened = fx.opened  # type: ignore[attr-defined]
    actor = fx.actor_a  # type: ignore[attr-defined]
    responsibility = fx.responsibilities[(AssessmentLane.VALUE, "finish")]  # type: ignore[attr-defined]
    work = slice_a_command(
        case_id=opened.facts.case_id,
        actor_id=actor,
        exact_context=opened.context,
        family="case-work",
        key=key,
        projections=(),
    )
    work = replace(
        work,
        effective_at=PROSPECTIVE_NOW,
        content={
            "question": "What Value could this bounded AI use create?",
            "instruction": "Use the exact visible information to finish the Value assessment.",
            "consequence": "The assessment will become ready for independent review.",
            "permitted_action": "Finish the independent Value assessment.",
        },
        projections=(
            ProjectionFact("case_work_records", {"record_id": str(work.record_id)}),
            ProjectionFact(
                "case_work_versions",
                {
                    "version_id": str(work.version_id),
                    "record_id": str(work.record_id),
                    "owning_case_id": str(opened.facts.case_id),
                    "context_digest": opened.context.digest,
                    "responsibility_version_id": str(responsibility.responsibility_version_id),
                    "assignment_version_id": str(responsibility.assignment_version_id),
                    "requester_actor_id": str(actor),
                    "assignee_actor_id": str(actor),
                    "state": "READY",
                    "reason": "Finish the independent Value assessment.",
                    "prerequisites_json": json.dumps(
                        [str(responsibility.responsibility_version_id)]
                    ),
                    "expected_result_family": "assessment-candidate",
                    "due_at_us": None,
                    "result_version_id": None,
                    "return_context_digest": opened.context.digest,
                    "predecessor_version_id": None,
                },
            ),
        ),
    )
    ResponsibilityWorkService(
        web_fixture.operational.domain_store,
        FixedClock(RECORDED + timedelta(seconds=3)),
        ExactAccess(),
    ).commit(work)
    return work


def _prepare_authorization_action(
    web_fixture: WebFixture, key: str
) -> tuple[SliceDFixture, RecordId, RecordId, str]:
    fx = slice_d_fixture(web_fixture.operational.domain_store, key)
    integration = integration_command(fx, f"{key}-integration")
    fx.service.integrate_value_risk(integration)
    proposal = proposal_command(fx, integration, f"{key}-proposal")
    fx.service.propose_decision(proposal)
    source = fx.source
    case_id = source.opened.facts.case_id
    configuration_id = source.opened.facts.configuration_id
    web_fixture.now.value = RECORDED + timedelta(seconds=10)
    _use_fixture_clock(web_fixture)
    web_fixture.operational.provision_principal(
        web_fixture.admin_session,
        principal_id="principal:web-practitioner",
        token=TOKEN,
        actor_id=source.actor_a,
        status=PrincipalStatus.ENABLED,
    )
    web_fixture.admin_session = web_fixture.operational.authenticate(
        "principal:web-practitioner", TOKEN
    )
    grant(web_fixture, Permission.CASE_READ, "read", ScopeType.CASE, case_id)
    grant(web_fixture, Permission.OPERATIONAL_ADMIN, "source-access.manage")
    grant(
        web_fixture,
        Permission.COMMAND,
        "decision.authorize",
        ScopeType.CASE,
        case_id,
    )
    _grant_all_case_sources(web_fixture, case_id, configuration_id)
    _, logged_in = login(web_fixture.client)
    assert logged_in.status_code == 303
    responsibility = fx.responsibilities[
        ObligationKind.AUTHORIZE_MANAGEMENT_DECISION
    ].responsibility_version_id
    return fx, case_id, configuration_id, f"/cases/{case_id}/actions/{responsibility}"


def test_harborlight_integrated_decision_path_uses_contextual_production_commands(
    web_fixture: WebFixture,
) -> None:
    """Fresh disposable Harborlight proof: browser intent -> Slices D production services."""

    fx = slice_d_fixture(web_fixture.operational.domain_store, "slice-h-harborlight")
    source = fx.source
    case_id = source.opened.facts.case_id
    configuration_id = source.opened.facts.configuration_id
    web_fixture.now.value = RECORDED + timedelta(seconds=10)
    _use_fixture_clock(web_fixture)
    web_fixture.operational.provision_principal(
        web_fixture.admin_session,
        principal_id="principal:web-practitioner",
        token=TOKEN,
        actor_id=source.actor_a,
        status=PrincipalStatus.ENABLED,
    )
    web_fixture.admin_session = web_fixture.operational.authenticate(
        "principal:web-practitioner", TOKEN
    )
    _prepare_browser_access(web_fixture, case_id)
    assert web_fixture.operational.operational_store.permission_allowed(
        "principal:web-practitioner",
        Permission.COMMAND,
        "integration.complete",
        ScopeType.CASE,
        case_id,
    )
    _grant_all_case_sources(web_fixture, case_id, configuration_id)
    _, logged_in = login(web_fixture.client)
    assert logged_in.status_code == 303

    integration_responsibility = fx.responsibilities[
        ObligationKind.COMPLETE_VALUE_RISK_INTEGRATION
    ].responsibility_version_id
    assert web_fixture.admin_session.actor_id is not None
    web_fixture.operational.slice_h_action_context(
        web_fixture.admin_session,
        case_id,
        integration_responsibility,
    )
    required = set(fx.value.version_ids + fx.risk.version_ids)
    required.update(
        {
            source.opened.facts.configuration_version_id,
            integration_responsibility,
            fx.responsibilities[
                ObligationKind.COMPLETE_VALUE_RISK_INTEGRATION
            ].assignment_version_id,
            fx.integration_authority,
        }
    )
    with web_fixture.operational.domain_store.read_transaction() as tx:
        for version_id in tuple(required):
            assignments = tx.projection_rows(
                "responsibility_assignment_versions", version_id=str(version_id)
            )
            if assignments:
                basis = RecordVersionId.parse(str(assignments[0]["assignment_basis_version_id"]))
                required.add(basis)
                rows = tx.projection_rows("assignment_basis_versions", version_id=str(basis))
                required.add(RecordVersionId.parse(str(rows[0]["basis_source_version_id"])))
    policy = OperationalSliceAAccessPolicy(web_fixture.operational.operational_store)
    for version_id in required:
        allowed = policy.authorize(
            principal_id="principal:web-practitioner",
            actor_id=str(source.actor_a),
            action="source.read",
            case_id=case_id,
            write=False,
            source_version_id=version_id,
            effective_at=web_fixture.now.value,
            known_at=web_fixture.now.value,
        )
        with web_fixture.operational.domain_store.read_transaction() as tx:
            exact = tx.get_version(version_id)
        assert allowed, (version_id, exact.family if exact else "ABSENT")
    _submit_action(
        web_fixture,
        case_id=case_id,
        responsibility_version_id=integration_responsibility,
        payload={
            "rationale": "Consider independent Value and Risk without netting either lane.",
            "material_tensions": "Opportunity remains bounded by the stated safeguards.",
            "limitations": "Harborlight Scenario A only.",
            "uncertainty": "Observed outcomes remain uncertain.",
            "unresolved_conditions": "",
        },
    )
    proposal_responsibility = fx.responsibilities[
        ObligationKind.PROPOSE_MANAGEMENT_DECISION
    ].responsibility_version_id
    _submit_action(
        web_fixture,
        case_id=case_id,
        responsibility_version_id=proposal_responsibility,
        payload={
            "proposed_action": "Proceed with bounded assistance and human review.",
            "operating_state": "bounded pilot",
            "rationale": "The exact independent positions support a bounded proposal.",
            "conditions": "Human review remains required.",
            "alternatives": "Do not proceed.",
        },
    )
    authorization_responsibility = fx.responsibilities[
        ObligationKind.AUTHORIZE_MANAGEMENT_DECISION
    ].responsibility_version_id
    authorization_path = f"/cases/{case_id}/actions/{authorization_responsibility}"
    authorization_page = web_fixture.client.get(authorization_path)
    assert authorization_page.status_code == 200
    assert 'name="authority_identity"' not in authorization_page.text
    _submit_action(
        web_fixture,
        case_id=case_id,
        responsibility_version_id=authorization_responsibility,
        payload={
            "authority_identity": "browser input must not control authority",
            "authority_limits": "Harborlight Scenario A only.",
            "conditions": "Human review remains required.",
            "dissent": "",
        },
    )

    case_page = web_fixture.client.get(f"/cases/{case_id}")
    assert case_page.status_code == 200
    assert "Authorized" in case_page.text
    assert "Proceed with bounded assistance and human review." in case_page.text
    assert "The exact independent positions support a bounded proposal." in case_page.text
    assert "Human review remains required." in case_page.text
    assert "Value and Risk are assessed separately" in case_page.text
    assert "value score" not in case_page.text.casefold()
    assert "risk score" not in case_page.text.casefold()
    web_fixture.operational.slice_h_timeline(web_fixture.admin_session, case_id)
    history = web_fixture.client.get(f"/cases/{case_id}/history-decisions")
    assert history.status_code == 200
    assert "What happened?" in history.text
    assert "Why:" in history.text
    assert "Proceed with bounded assistance and human review." in history.text
    assert "Advanced time reconstruction and audit sources" in history.text
    reconstructed = web_fixture.client.get(
        f"/cases/{case_id}/history-decisions",
        params={
            "effective_at": PROSPECTIVE_NOW.isoformat(),
            "known_at": (RECORDED + timedelta(seconds=4)).isoformat(),
        },
    )
    assert reconstructed.status_code == 200
    assert "What changed since" in reconstructed.text
    assert "No quality, causality, or Decision conclusion is inferred" not in (reconstructed.text)
    with web_fixture.operational.domain_store.read_transaction() as tx:
        assert tx.count_rows("prospective_integration_versions") == 1
        assert tx.count_rows("prospective_decision_versions") == 2
        authorization_rows = tx.projection_rows("prospective_decision_authorization_versions")
        assert len(authorization_rows) == 1
        authorization_source = tx.get_version(
            RecordVersionId.parse(str(authorization_rows[0]["version_id"]))
        )
        assert authorization_source is not None
        assert authorization_source.content["authority_identity"] == str(source.actor_a)
        assert "browser input must not control authority" not in str(authorization_source.content)


def test_hidden_decision_authority_fails_closed_without_semantic_mutation(
    web_fixture: WebFixture,
) -> None:
    fx, case_id, _configuration_id, action_path = _prepare_authorization_action(
        web_fixture, "slice-h-hidden-authority"
    )
    action = web_fixture.client.get(action_path)
    assert action.status_code == 200
    assert 'name="authority_identity"' not in action.text
    reviewed = web_fixture.client.post(
        f"{action_path}/review",
        data={
            "csrf_token": csrf_from(action.text),
            "authority_identity": "tampered browser authority",
            "authority_limits": "Scenario A only.",
            "conditions": "Human review remains required.",
            "dissent": "",
        },
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    assert reviewed.status_code == 303
    confirmation = web_fixture.client.get(reviewed.headers["location"])
    assert confirmation.status_code == 200
    assert "tampered browser authority" not in confirmation.text
    with web_fixture.operational.domain_store.read_transaction() as tx:
        authority_source = tx.get_version(fx.decision_authority)
        before_decisions = tx.count_rows("prospective_decision_versions")
        before_authorizations = tx.count_rows("prospective_decision_authorization_versions")
    assert authority_source is not None
    web_fixture.operational.grant_source_access(
        web_fixture.admin_session,
        principal_id="principal:web-practitioner",
        grant=SourceAccessGrantInput(
            "source.read",
            case_id,
            fx.decision_authority,
            authority_source.family,
            AccessEffect.DENY,
            web_fixture.now.value,
        ),
    )
    denied = web_fixture.client.post(
        confirmation.url.path.replace("/confirm/", "/commit/"),
        data={"csrf_token": csrf_from(confirmation.text)},
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    assert denied.status_code == 409
    assert str(fx.decision_authority) not in denied.text
    with web_fixture.operational.domain_store.read_transaction() as tx:
        assert tx.count_rows("prospective_decision_versions") == before_decisions
        assert (
            tx.count_rows("prospective_decision_authorization_versions")
            == before_authorizations
            == 0
        )


def test_stale_reviewed_authority_source_fails_closed_without_retarget(
    web_fixture: WebFixture,
) -> None:
    fx, case_id, configuration_id, action_path = _prepare_authorization_action(
        web_fixture, "slice-h-stale-authority"
    )
    action = web_fixture.client.get(action_path)
    reviewed = web_fixture.client.post(
        f"{action_path}/review",
        data={
            "csrf_token": csrf_from(action.text),
            "authority_limits": "Scenario A only.",
            "conditions": "Human review remains required.",
            "dissent": "",
        },
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    confirmation = web_fixture.client.get(reviewed.headers["location"])
    assert confirmation.status_code == 200
    with web_fixture.operational.domain_store.read_transaction() as tx:
        prior = tx.get_version(fx.decision_authority)
        before_decisions = tx.count_rows("prospective_decision_versions")
    assert prior is not None
    successor_id = RecordVersionId.new()
    Increment3ApplicationService(
        web_fixture.operational.domain_store,
        FixedClock(web_fixture.now.value + timedelta(seconds=1)),
    ).commit_authority_record(
        CommandMeta(
            CommandId.new(),
            "slice-h-practitioner-action",
            "slice-h-stale-authority-successor",
            "principal:web-practitioner",
            str(fx.source.actor_a),
            ActorResolution.PROVIDED,
        ),
        AuthorityVersionInput(
            prior.record_id,
            successor_id,
            case_id,
            configuration_id,
            fx.source.opened.facts.configuration_version_id,
            str(prior.content["category"]),
            str(prior.content["source"]),
            dict(prior.content["provenance"]),
            str(prior.content["scope"]),
            str(prior.content["requirement"]),
            {
                "prospective_substantive_authority": dict(
                    prior.content["prospective_substantive_authority"]
                )
            },
            EffectiveInterval(web_fixture.now.value),
            expected_version_id=fx.decision_authority,
            relationship_reason="current authority source successor",
        ),
    )
    reviewed_effective_at = web_fixture.now.value
    _grant_all_case_sources(
        web_fixture,
        case_id,
        configuration_id,
        effective_from=reviewed_effective_at,
    )
    web_fixture.now.advance(timedelta(seconds=2))
    _use_fixture_clock(web_fixture)
    stale = web_fixture.client.post(
        confirmation.url.path.replace("/confirm/", "/commit/"),
        data={"csrf_token": csrf_from(confirmation.text)},
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    assert stale.status_code == 409
    assert str(fx.decision_authority) not in stale.text
    assert str(successor_id) not in stale.text
    with web_fixture.operational.domain_store.read_transaction() as tx:
        assert tx.count_rows("prospective_decision_versions") == before_decisions
        assert tx.count_rows("prospective_decision_authorization_versions") == 0


def test_slice_h_primary_navigation_and_quiet_home_are_burden_bounded(
    web_fixture: WebFixture,
) -> None:
    _, logged_in = login(web_fixture.client)
    assert logged_in.status_code == 303
    home = web_fixture.client.get("/home")
    home_view = web_fixture.operational.slice_h_home(web_fixture.admin_session)
    assert "Nothing currently needs your attention." in home.text, tuple(
        (item.kind, item.question) for item in home_view.items
    )
    assert home.text.count('<a href="/home"') == 1
    assert home.text.count('<a href="/cases"') >= 1
    assert home.text.count('<a href="/learn"') == 1
    assert "View Existing Cases" in home.text
    assert "Open Cases" not in home.text
    for prohibited in (
        "semantic contract",
        "context digest",
        "assignment basis",
        "source closure",
        "transaction member",
    ):
        assert prohibited not in home.text.casefold()


def test_durable_work_leads_to_action_and_hidden_or_stale_responsibility_never_retargets(
    web_fixture: WebFixture,
) -> None:
    """Home -> durable Task -> action survives restart and fails closed on exact source change."""

    fx = slice_c_fixture(web_fixture.operational.domain_store, "slice-h-durable-work")
    case_id = fx.opened.facts.case_id
    configuration_id = fx.opened.facts.configuration_id
    responsibility = fx.responsibilities[(AssessmentLane.VALUE, "finish")]
    work = _establish_value_work(web_fixture, fx, "slice-h-value-work")
    web_fixture.now.value = RECORDED + timedelta(seconds=10)
    _use_fixture_clock(web_fixture)
    web_fixture.operational.provision_principal(
        web_fixture.admin_session,
        principal_id="principal:web-practitioner",
        token=TOKEN,
        actor_id=fx.actor_a,
        status=PrincipalStatus.ENABLED,
    )
    web_fixture.admin_session = web_fixture.operational.authenticate(
        "principal:web-practitioner", TOKEN
    )
    grant(web_fixture, Permission.CASE_READ, "read", ScopeType.CASE, case_id)
    grant(web_fixture, Permission.OPERATIONAL_ADMIN, "source-access.manage")
    grant(
        web_fixture,
        Permission.COMMAND,
        "assessment.finish.value",
        ScopeType.CASE,
        case_id,
    )
    _grant_all_case_sources(web_fixture, case_id, configuration_id)
    _, logged_in = login(web_fixture.client)
    assert logged_in.status_code == 303

    task_path = f"/cases/{case_id}/tasks/{work.version_id}"  # type: ignore[attr-defined]
    action_path = f"/cases/{case_id}/actions/{responsibility.responsibility_version_id}"
    home = web_fixture.client.get("/home")
    assert task_path in home.text
    task = web_fixture.client.get(task_path)
    assert task.status_code == 200
    assert action_path in task.text
    assert "Continue to this action" in task.text

    with OperationalApplication(web_fixture.config, FixedClock(web_fixture.now.value)) as restarted:
        restarted_session = restarted.authenticate("principal:web-practitioner", TOKEN)
        reconstructed = restarted.slice_h_task(
            restarted_session,
            case_id,
            work.version_id,  # type: ignore[attr-defined]
        )
        assert reconstructed.responsibility_version_id == (responsibility.responsibility_version_id)
        assert reconstructed.return_path == fx.opened.context.digest

    action = web_fixture.client.get(action_path)
    assert action.status_code == 200
    reviewed = web_fixture.client.post(
        f"{action_path}/review",
        data={
            "csrf_token": csrf_from(action.text),
            "finding": "Bounded assistance may improve review consistency.",
            "boundary": "Harborlight Scenario A only.",
            "uncertainty": "Observed outcomes remain limited.",
            "implication": "Retain accountable human lending judgment.",
            "provenance": "Exact visible bounded information.",
            "rationale": "Ready for independent review.",
            "limitations": "No autonomous lending Decision.",
        },
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    confirmation = web_fixture.client.get(reviewed.headers["location"])
    committed = web_fixture.client.post(
        confirmation.url.path.replace("/confirm/", "/commit/"),
        data={"csrf_token": csrf_from(confirmation.text)},
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    assert committed.status_code == 303
    assert committed.headers["location"] == f"/cases/{case_id}"

    web_fixture.operational.grant_source_access(
        web_fixture.admin_session,
        principal_id="principal:web-practitioner",
        grant=SourceAccessGrantInput(
            "source.read",
            case_id,
            responsibility.responsibility_version_id,
            "responsibility",
            AccessEffect.DENY,
            web_fixture.now.value,
        ),
    )
    hidden_task = web_fixture.client.get(task_path)
    assert hidden_task.status_code == 409
    assert str(responsibility.responsibility_version_id) not in hidden_task.text
    web_fixture.operational.grant_source_access(
        web_fixture.admin_session,
        principal_id="principal:web-practitioner",
        grant=SourceAccessGrantInput(
            "source.read",
            case_id,
            responsibility.responsibility_version_id,
            "responsibility",
            AccessEffect.ALLOW,
            web_fixture.now.value,
        ),
    )

    with web_fixture.operational.domain_store.read_transaction() as tx:
        responsibility_row = tx.projection_rows(
            "responsibility_versions",
            version_id=str(responsibility.responsibility_version_id),
        )[0]
        responsibility_source = tx.get_version(responsibility.responsibility_version_id)
    assert responsibility_source is not None
    successor = slice_a_command(
        case_id=case_id,
        actor_id=fx.actor_a,
        exact_context=fx.opened.context,
        family="responsibility",
        key="slice-h-stale-responsibility",
        projections=(),
    )
    successor = replace(
        successor,
        record_id=responsibility_source.record_id,
        expected_version_id=responsibility.responsibility_version_id,
        effective_at=web_fixture.now.value,
        content=dict(responsibility_source.content),
        projections=(
            ProjectionFact(
                "responsibility_versions",
                {
                    **responsibility_row,
                    "version_id": str(successor.version_id),
                    "record_id": str(responsibility_source.record_id),
                },
            ),
        ),
    )
    ResponsibilityWorkService(
        web_fixture.operational.domain_store,
        FixedClock(web_fixture.now.value),
        ExactAccess(),
    ).commit(successor)
    stale_task = web_fixture.client.get(task_path)
    assert stale_task.status_code == 200
    assert action_path not in stale_task.text
    assert "This action is not safely available" in stale_task.text
    stale_action = web_fixture.client.get(action_path)
    assert stale_action.status_code == 409
    assert str(successor.version_id) not in stale_action.text


def test_case_start_preflight_blocks_data_entry_without_disclosing_authority_sources(
    web_fixture: WebFixture,
) -> None:
    _, logged_in = login(web_fixture.client)
    assert logged_in.status_code == 303
    page = web_fixture.client.get("/cases/new")
    assert page.status_code == 200
    assert "Case start is not available" in page.text
    assert 'name="title"' not in page.text
    assert "case_initiation_authority" not in page.text
    assert "version_id" not in page.text


def test_case_start_provider_classification_and_dependency_description_are_bounded(
    web_fixture: WebFixture,
) -> None:
    web_fixture.now.value = H0_NOW
    _use_fixture_clock(web_fixture)
    prepare_permissions(web_fixture)
    establish_authority(
        web_fixture,
        web_fixture.operational._case_continuity,  # type: ignore[attr-defined]
    )
    _, logged_in = login(web_fixture.client)
    assert logged_in.status_code == 303
    page = web_fixture.client.get("/cases/new")
    for classification in (
        "Internally developed",
        "Commercial product or service",
        "Open-source",
        "Combination / mixed",
        "Other",
    ):
        assert f'value="{classification}"' in page.text
    assert 'name="provider_source_other"' in page.text
    assert 'name="dependency_1_type"' not in page.text
    assert "what the AI use receives from, relies on, connects to, or requires" in page.text

    common = {
        "csrf_token": csrf_from(page.text),
        "title": "Harborlight classified intake proof",
        "ai_name": "Harborlight Assist",
        "ai_description": "A lending-review assistance service.",
        "provider_source_type": "Other",
        "capabilities": "Summarizes application information.",
        "bounded_use": "small-business lending assistance",
        "management_question": "Should this bounded use proceed?",
        "setup_description": "Accountable human review remains required.",
        "effective_at": H0_NOW.isoformat(),
        "dependency_count": "1",
        "dependency_1_name": "Lending policy library",
        "dependency_1_why": (
            "The AI use retrieves current policy material and depends on its maintained accuracy."
        ),
    }
    missing_other = web_fixture.client.post(
        "/cases/start/review",
        data=common,
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    assert missing_other.status_code == 400
    assert "needs a description" in missing_other.text

    reviewed = web_fixture.client.post(
        "/cases/start/review",
        data={**common, "provider_source_other": "Cooperative industry service"},
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    assert reviewed.status_code == 303
    confirmation = web_fixture.client.get(reviewed.headers["location"])
    assert "Other: Cooperative industry service" in confirmation.text
    assert "Lending policy library" in confirmation.text
    assert "(Internal)" not in confirmation.text
    edited = web_fixture.client.get(confirmation.url.path.replace("/confirm/", "/edit/"))
    assert 'value="Other" selected' in edited.text
    assert 'value="Cooperative industry service"' in edited.text


def test_new_case_exposes_explicit_assessment_responsibility_setup(
    web_fixture: WebFixture,
) -> None:
    """A new Case stays minimal, then offers an explicit accountable next step."""

    web_fixture.now.value = H0_NOW
    _use_fixture_clock(web_fixture)
    prepare_permissions(web_fixture)
    establish_authority(
        web_fixture,
        web_fixture.operational._case_continuity,  # type: ignore[attr-defined]
    )
    grant(
        web_fixture,
        Permission.OPERATIONAL_ADMIN,
        "source-access.manage",
        effect=AccessEffect.DENY,
    )
    _, logged_in = login(web_fixture.client)
    assert logged_in.status_code == 303
    new_case = web_fixture.client.get("/cases/new")
    assert new_case.status_code == 200
    for expected in (
        "Case name",
        "AI name",
        "What is this AI?",
        "Source or provider type",
        "Relevant capabilities",
        "AI use",
        "Decision or management question",
        "Operating context",
        "Add AI details",
        "Add dependency",
    ):
        assert expected in new_case.text
    for prohibited in (
        "risk tier",
        "review cadence",
        "semantic metadata",
        "responsibility matrix",
        "authority mapping",
    ):
        assert prohibited not in new_case.text.casefold()
    cancelled_review = web_fixture.client.post(
        "/cases/start/review",
        data={
            "csrf_token": csrf_from(new_case.text),
            "title": "Harborlight cancelled Case",
            "ai_name": "Harborlight Assist",
            "ai_description": "A lending-review assistance service.",
            "provider_source_type": "Commercial product or service",
            "capabilities": "Summarizes application information.",
            "bounded_use": "small-business lending assistance",
            "management_question": "Should this cancelled request proceed?",
            "setup_description": "Accountable human review remains required.",
            "effective_at": H0_NOW.isoformat(),
        },
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    cancelled_page = web_fixture.client.get(cancelled_review.headers["location"])
    cancelled = web_fixture.client.post(
        cancelled_page.url.path.replace("/confirm/", "/cancel/"),
        data={"csrf_token": csrf_from(cancelled_page.text)},
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    assert cancelled.status_code == 303
    with web_fixture.operational.domain_store.read_transaction() as tx:
        assert tx.count_rows("case_continuity_status_versions") == 0
    missing_question = web_fixture.client.post(
        "/cases/start/review",
        data={
            "csrf_token": csrf_from(new_case.text),
            "title": "Harborlight Assist — incomplete request",
            "ai_name": "Harborlight Assist",
            "ai_description": "A lending-review assistance service.",
            "provider_source_type": "Commercial product or service",
            "capabilities": "Summarizes application information.",
            "bounded_use": "small-business lending assistance",
            "management_question": "",
            "setup_description": "Bounded assistance only.",
            "effective_at": H0_NOW.isoformat(),
        },
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    assert missing_question.status_code == 400
    with web_fixture.operational.domain_store.read_transaction() as tx:
        assert tx.count_rows("case_continuity_status_versions") == 0
    reviewed = web_fixture.client.post(
        "/cases/start/review",
        data={
            "csrf_token": csrf_from(new_case.text),
            "title": "Harborlight Assist — disposable Slice H Case",
            "ai_name": "Harborlight Assist",
            "ai_description": "A lending-review assistance service.",
            "provider_source_type": "Commercial product or service",
            "capabilities": "Summarizes application information.",
            "bounded_use": "small-business lending assistance",
            "management_question": (
                "Should Harborlight use bounded AI assistance in its lending review?"
            ),
            "setup_description": "Assistance only; accountable human lending judgment remains.",
            "effective_at": H0_NOW.isoformat(),
        },
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    assert reviewed.status_code == 303
    confirmation = web_fixture.client.get(reviewed.headers["location"])
    assert confirmation.status_code == 200
    assert "Check the details below before starting this Case." in confirmation.text
    assert "Should Harborlight use bounded AI assistance in its lending review?" in (
        confirmation.text
    )
    committed = web_fixture.client.post(
        confirmation.url.path.replace("/confirm/", "/commit/"),
        data={"csrf_token": csrf_from(confirmation.text)},
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    assert committed.status_code == 303
    replayed = web_fixture.client.post(
        confirmation.url.path.replace("/confirm/", "/commit/"),
        data={"csrf_token": csrf_from(confirmation.text)},
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    assert replayed.status_code == 303
    assert replayed.headers["location"] == committed.headers["location"]
    case_page = web_fixture.client.get(committed.headers["location"])
    assert case_page.status_code == 200
    assert "Harborlight Assist" in case_page.text
    assert "Commercial product or service" in case_page.text
    assert "PAIM-" in case_page.text
    assert "small-business lending assistance" in case_page.text
    assert "Should Harborlight use bounded AI assistance in its lending review?" in case_page.text
    assert "Set up responsibility for Value and Risk assessments" in case_page.text
    assert "Case continuity — assigned to you" in case_page.text
    assert ">One<" not in case_page.text
    case_id = RecordId.parse(committed.headers["location"].rsplit("/", 1)[1])
    setup_path = f"/cases/{case_id}/setup/initial-assessments"
    grant(
        web_fixture,
        Permission.COMMAND,
        "case.create_open",
        effect=AccessEffect.DENY,
    )
    blocked_case = web_fixture.client.get(committed.headers["location"])
    assert "An authorized practitioner must establish" in blocked_case.text
    assert setup_path not in blocked_case.text
    blocked_setup = web_fixture.client.get(setup_path)
    assert blocked_setup.status_code == 409
    with web_fixture.operational.domain_store.read_transaction() as tx:
        assert tx.count_rows("responsibility_versions") == 1
    grant(web_fixture, Permission.COMMAND, "case.create_open")
    authenticated = web_fixture.operational.authenticate("principal:web-practitioner", TOKEN)
    exact_setup = web_fixture.operational.slice_h_initial_assessment_setup_context(
        authenticated, case_id
    )
    with pytest.raises(AccessDenied, match="context changed"):
        web_fixture.operational.slice_h_commit_initial_assessment_setup(
            authenticated,
            case_id=case_id,
            expected_source_version_ids=exact_setup.source_version_ids[:-1],
            authority_source="Harborlight AI governance charter",
            authority_provenance="Charter HL-AI-2026 section 4.2",
            authority_scope="This exact Case and its initial independent assessments",
            authority_requirement="The initiator establishes accountable assessment work.",
            effective_at=H0_NOW,
            idempotency_key="tampered-initial-assessment-setup",
        )
    with web_fixture.operational.domain_store.read_transaction() as tx:
        assert tx.count_rows("responsibility_versions") == 1
    setup = web_fixture.client.get(setup_path)
    assert setup.status_code == 200
    assert "Software access, responsibility, and substantive authority remain separate" in (
        setup.text
    )
    for guidance in (
        "Illustrative example: an approved AI governance charter.",
        "Illustrative example: charter section 4.2 or a policy record reference.",
        "Illustrative example: this exact Case and its initial independent assessments.",
        "Illustrative example: the named governance role may assign",
        "Do not enter a software permission or invent authority",
    ):
        assert guidance in setup.text
    incomplete_setup = web_fixture.client.post(
        f"{setup_path}/review",
        data={
            "csrf_token": csrf_from(setup.text),
            "authority_source": "",
            "authority_provenance": "",
            "authority_scope": "",
            "authority_requirement": "",
        },
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    assert incomplete_setup.status_code == 400
    with web_fixture.operational.domain_store.read_transaction() as tx:
        assert tx.count_rows("responsibility_versions") == 1
    reviewed_setup = web_fixture.client.post(
        f"{setup_path}/review",
        data={
            "csrf_token": csrf_from(setup.text),
            "authority_source": "Harborlight AI governance charter",
            "authority_provenance": "Charter HL-AI-2026 section 4.2",
            "authority_scope": "This exact Case and its initial independent assessments",
            "authority_requirement": (
                "The Case initiator establishes accountable Value and Risk assessment work."
            ),
        },
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    assert reviewed_setup.status_code == 303
    setup_confirmation = web_fixture.client.get(reviewed_setup.headers["location"])
    assert setup_confirmation.status_code == 200
    assert "will not" in setup_confirmation.text
    setup_committed = web_fixture.client.post(
        setup_confirmation.url.path.replace("/confirm/", "/commit/"),
        data={"csrf_token": csrf_from(setup_confirmation.text)},
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    assert setup_committed.status_code == 303, setup_committed.text
    actionable_case = web_fixture.client.get(setup_committed.headers["location"])
    assert "Finish the Value assessment" in actionable_case.text
    assert "Finish the Risk assessment" in actionable_case.text
    assert "Value assessment — assigned to you" in actionable_case.text
    assert "Risk assessment — assigned to you" in actionable_case.text
    assert "This assessment is assigned to you and has not yet been completed." in (
        actionable_case.text
    )
    assert "The governed act cannot proceed until accountability is exact." not in (
        actionable_case.text
    )
    for action in ("assessment.finish.value", "assessment.finish.risk"):
        assert web_fixture.operational.operational_store.permission_allowed(
            "principal:web-practitioner",
            Permission.COMMAND,
            action,
            ScopeType.CASE,
            case_id,
        )
        assert not web_fixture.operational.operational_store.permission_allowed(
            "principal:web-practitioner", Permission.COMMAND, action
        )
        assert not web_fixture.operational.operational_store.permission_allowed(
            "principal:web-practitioner",
            Permission.COMMAND,
            action,
            ScopeType.CASE,
            RecordId.new(),
        )
    setup_audit = tuple(
        row
        for row in web_fixture.operational.operational_store.audit_rows()
        if row["reason_category"] == "EXACT_INITIAL_ASSESSMENT_ACCESS_ESTABLISHED"
    )
    assert len(setup_audit) == 1
    setup_details = json.loads(str(setup_audit[0]["details_json"]))
    assert setup_details["software_access_only"] is True
    assert setup_details["substantive_authority_granted"] is False
    assert len(setup_details["source_version_ids"]) == 6
    visible_cases = web_fixture.client.get("/cases")
    assert visible_cases.status_code == 200
    assert "Harborlight Assist" in visible_cases.text
    assert web_fixture.operational.operational_store.permission_allowed(
        "principal:web-practitioner",
        Permission.CASE_READ,
        "read",
        ScopeType.CASE,
        case_id,
    )
    assert not web_fixture.operational.operational_store.permission_allowed(
        "principal:web-practitioner",
        Permission.CASE_READ,
        "read",
        ScopeType.CASE,
        RecordId.new(),
    )
    assert not web_fixture.operational.operational_store.permission_allowed(
        "principal:web-practitioner",
        Permission.CASE_READ,
        "read",
    )
    creator_visibility = tuple(
        row
        for row in web_fixture.operational.operational_store.audit_rows()
        if row["reason_category"] == "CASE_CREATOR_EXACT_VISIBILITY_ESTABLISHED"
    )
    assert len(creator_visibility) == 1
    assert creator_visibility[0]["case_id"] == str(case_id)
    assert creator_visibility[0]["principal_id"] == "principal:web-practitioner"
    details = json.loads(str(creator_visibility[0]["details_json"]))
    assert details["scope"] == "EXACT_CREATED_CASE"
    assert details["substantive_authority_granted"] is False
    assert len(details["source_version_ids"]) == 8
    with web_fixture.operational.domain_store.read_transaction() as tx:
        assert tx.count_rows("case_continuity_status_versions") == 1
        assert tx.count_rows("governing_configuration_designations") == 1
        assert tx.count_rows("responsibility_versions") == 3
        assert tx.count_rows("assignment_basis_versions") == 2
        assert tx.count_rows("responsibility_assignment_versions") == 3
        assert tx.count_rows("assessment_candidate_versions") == 0
        assert tx.count_rows("prospective_integration_versions") == 0
        assert tx.count_rows("prospective_decision_versions") == 0
        assert tx.count_rows("review_episode_versions") == 0


def test_case_start_visibility_failure_rolls_back_the_entire_opening(
    web_fixture: WebFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exact creator visibility is one failure-closed Case-start transaction."""

    web_fixture.now.value = H0_NOW
    _use_fixture_clock(web_fixture)
    prepare_permissions(web_fixture)
    establish_authority(
        web_fixture,
        web_fixture.operational._case_continuity,  # type: ignore[attr-defined]
    )
    _, logged_in = login(web_fixture.client)
    assert logged_in.status_code == 303
    page = web_fixture.client.get("/cases/new")
    reviewed = web_fixture.client.post(
        "/cases/start/review",
        data={
            "csrf_token": csrf_from(page.text),
            "title": "Atomic visibility failure proof",
            "ai_name": "Harborlight Assist",
            "ai_description": "A lending-review assistance service.",
            "provider_source_type": "Commercial product or service",
            "capabilities": "Summarizes application information.",
            "bounded_use": "small-business lending assistance",
            "management_question": "Should this bounded use proceed?",
            "setup_description": "Accountable human review remains required.",
            "effective_at": H0_NOW.isoformat(),
        },
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    confirmation = web_fixture.client.get(reviewed.headers["location"])
    tables = (
        "paim_cases",
        "records",
        "record_versions",
        "idempotency_facts",
        "software_access_grants",
        "source_access_grants",
        "audit_facts",
        "operational_audit_facts",
    )
    before = web_fixture.operational.operational_store.table_counts(tables)

    def reject_visibility(*_args: object, **_kwargs: object) -> dict[str, object]:
        raise ValueError("injected exact creator visibility failure")

    monkeypatch.setattr(
        web_fixture.operational.operational_store,
        "establish_case_creator_visibility",
        reject_visibility,
    )
    result = web_fixture.client.post(
        confirmation.url.path.replace("/confirm/", "/commit/"),
        data={"csrf_token": csrf_from(confirmation.text)},
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    assert result.status_code == 409
    assert "exact creator visibility could not be established" in result.text
    assert web_fixture.operational.operational_store.table_counts(tables) == before


def test_case_start_form_survives_session_expiry_without_governed_mutation(
    web_fixture: WebFixture,
) -> None:
    """Reauthentication restores exact uncommitted form state for the same principal."""

    web_fixture.now.value = H0_NOW
    _use_fixture_clock(web_fixture)
    prepare_permissions(web_fixture)
    active_authority = establish_authority(
        web_fixture,
        web_fixture.operational._case_continuity,  # type: ignore[attr-defined]
    )
    _, logged_in = login(web_fixture.client)
    assert logged_in.status_code == 303
    page = web_fixture.client.get("/cases/new")
    csrf_token = csrf_from(page.text)
    form = {
        "csrf_token": csrf_token,
        "title": "Harborlight restored Case",
        "ai_name": "Harborlight Assist",
        "ai_description": "A commercial lending-review assistance service.",
        "provider_source_type": "Commercial product or service",
        "capabilities": "Summarizes application information for this AI use.",
        "bounded_use": "small-business lending assistance",
        "management_question": "Should Harborlight use AI assistance in lending review?",
        "setup_description": "Human lending judgment remains required.",
        "effective_at": H0_NOW.isoformat(),
        "dependency_count": "3",
        "dependency_1_name": "Application data",
        "dependency_1_why": "Provides the application facts.",
        "dependency_2_name": "AI service",
        "dependency_2_why": "Provides the assistance capability.",
        "dependency_3_name": "Human review",
        "dependency_3_why": "Retains accountable judgment.",
        "form_action": "review",
        "credential": "must-not-enter-recovery-state",
    }
    before = web_fixture.operational.operational_store.table_counts(
        (
            "paim_cases",
            "case_number_allocations",
            "case_continuity_status_versions",
            "responsibility_versions",
        )
    )

    web_fixture.now.advance(timedelta(minutes=31))
    expired = web_fixture.client.post(
        "/cases/start/review",
        data=form,
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    assert expired.status_code == 303
    assert expired.headers["location"] == "/login?reason=session&resume=case-start"
    assert web_fixture.sessions.recovery_count == 1
    assert web_fixture.operational.operational_store.table_counts(tuple(before)) == before

    login_page = web_fixture.client.get(expired.headers["location"])
    assert "restore the information you entered" in login_page.text
    restored = web_fixture.client.post(
        "/session",
        data={
            "principal_id": "principal:web-practitioner",
            "credential": TOKEN,
            "csrf_token": csrf_from(login_page.text),
        },
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    assert restored.status_code == 303
    assert restored.headers["location"].startswith("/cases/start/edit/")
    restored_page = web_fixture.client.get(restored.headers["location"])
    assert restored_page.status_code == 200
    assert "Case information was restored" in restored_page.text
    assert "must-not-enter-recovery-state" not in restored_page.text
    for exact_value in (
        form["title"],
        form["management_question"],
        form["dependency_1_name"],
        form["dependency_2_name"],
        form["dependency_3_name"],
    ):
        assert exact_value in restored_page.text
    assert web_fixture.sessions.recovery_count == 0
    assert web_fixture.operational.operational_store.table_counts(tuple(before)) == before

    withdrawn = replace(
        active_authority,
        identity=h0_identity("withdraw-restored-case-start", web_fixture.actor_id),
        version_id=RecordVersionId.new(),
        state=CaseInitiationAuthorityState.WITHDRAWN,
        expected_version_id=active_authority.version_id,
    )
    web_fixture.operational._case_continuity.record_case_initiation_authority(  # type: ignore[attr-defined]
        withdrawn
    )
    intent_id = restored.headers["location"].split("/edit/", 1)[1].split("?", 1)[0]
    retry_form = {**form, "csrf_token": csrf_from(restored_page.text), "intent_id": intent_id}
    denied = web_fixture.client.post(
        "/cases/start/review",
        data=retry_form,
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    assert denied.status_code == 403
    assert "Case start is not available" in denied.text
    assert web_fixture.operational.operational_store.table_counts(tuple(before)) == before

    cancelled = web_fixture.client.post(
        f"/cases/start/cancel/{intent_id}",
        data={"csrf_token": csrf_from(restored_page.text)},
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    assert cancelled.status_code == 303
    assert cancelled.headers["location"] == "/cases"
    assert web_fixture.operational.operational_store.table_counts(tuple(before)) == before


def test_case_start_revalidates_withdrawn_mandate_and_commits_nothing(
    web_fixture: WebFixture,
) -> None:
    web_fixture.now.value = H0_NOW
    _use_fixture_clock(web_fixture)
    prepare_permissions(web_fixture)
    active = establish_authority(
        web_fixture,
        web_fixture.operational._case_continuity,  # type: ignore[attr-defined]
    )
    _, logged_in = login(web_fixture.client)
    assert logged_in.status_code == 303
    page = web_fixture.client.get("/cases/new")
    reviewed = web_fixture.client.post(
        "/cases/start/review",
        data={
            "csrf_token": csrf_from(page.text),
            "title": "Harborlight stale mandate proof",
            "ai_name": "Harborlight Assist",
            "ai_description": "A lending-review assistance service.",
            "provider_source_type": "Commercial product or service",
            "capabilities": "Summarizes application information.",
            "bounded_use": "small-business lending assistance",
            "management_question": "Should this bounded use proceed?",
            "setup_description": "Accountable human review remains required.",
            "effective_at": H0_NOW.isoformat(),
        },
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    confirmation = web_fixture.client.get(reviewed.headers["location"])
    withdrawn = replace(
        active,
        identity=h0_identity("withdraw-before-browser-commit", web_fixture.actor_id),
        version_id=RecordVersionId.new(),
        state=CaseInitiationAuthorityState.WITHDRAWN,
        expected_version_id=active.version_id,
    )
    web_fixture.operational._case_continuity.record_case_initiation_authority(  # type: ignore[attr-defined]
        withdrawn
    )
    before = web_fixture.operational.operational_store.table_counts(
        ("paim_cases", "case_number_allocations", "case_continuity_status_versions")
    )
    result = web_fixture.client.post(
        confirmation.url.path.replace("/confirm/", "/commit/"),
        data={"csrf_token": csrf_from(confirmation.text)},
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    assert result.status_code == 403
    assert "Case start is no longer available" in result.text
    assert web_fixture.operational.operational_store.table_counts(tuple(before)) == before


def test_value_risk_tasks_preserve_independence_and_real_practitioner_handoff(
    web_fixture: WebFixture,
) -> None:
    """One Actor handles common work; a separately accountable Actor receives Risk reliance."""

    fx = slice_c_fixture(web_fixture.operational.domain_store, "slice-h-lanes")
    case_id = fx.opened.facts.case_id
    configuration_id = fx.opened.facts.configuration_id
    web_fixture.now.value = RECORDED + timedelta(seconds=10)
    _use_fixture_clock(web_fixture)
    web_fixture.operational.provision_principal(
        web_fixture.admin_session,
        principal_id="principal:web-practitioner",
        token=TOKEN,
        actor_id=fx.actor_a,
        status=PrincipalStatus.ENABLED,
    )
    web_fixture.admin_session = web_fixture.operational.authenticate(
        "principal:web-practitioner", TOKEN
    )
    grant(web_fixture, Permission.CASE_READ, "read", ScopeType.CASE, case_id)
    grant(web_fixture, Permission.OPERATIONAL_ADMIN, "source-access.manage")
    for action in (
        "assessment.finish.value",
        "assessment.finish.risk",
        "assessment.adequacy.value",
        "assessment.adequacy.risk",
        "assessment.reliance.value",
    ):
        grant(web_fixture, Permission.COMMAND, action, ScopeType.CASE, case_id)
    _grant_all_case_sources(web_fixture, case_id, configuration_id)
    _, logged_in = login(web_fixture.client)
    assert logged_in.status_code == 303

    for lane in (AssessmentLane.VALUE, AssessmentLane.RISK):
        finish = fx.responsibilities[(lane, "finish")]
        _submit_action(
            web_fixture,
            case_id=case_id,
            responsibility_version_id=finish.responsibility_version_id,
            payload={
                "finding": (
                    "AI assistance may improve review consistency."
                    if lane is AssessmentLane.VALUE
                    else "Automation bias and uneven records require attention."
                ),
                "boundary": "Harborlight small-business lending assistance only.",
                "uncertainty": "Observed outcomes remain limited.",
                "implication": "Use only inside the bounded human-review process.",
                "provenance": "The exact visible Harborlight information basis.",
                "rationale": "This independent assessment is ready for review.",
                "limitations": "No autonomous lending judgment.",
            },
        )
        adequacy = fx.responsibilities[(lane, "adequacy")]
        _submit_action(
            web_fixture,
            case_id=case_id,
            responsibility_version_id=adequacy.responsibility_version_id,
            payload={
                "outcome": "ADEQUATE",
                "rationale": "The bounded assessment is adequate for this exact decision use.",
                "material_reasons": "",
                "uncertainty": "The stated uncertainty remains visible.",
                "limitations": "The judgment does not approve the Case.",
            },
        )

    value_reliance = fx.responsibilities[(AssessmentLane.VALUE, "reliance")]
    home_after_adequacy = web_fixture.client.get("/home")
    assert "Which adequate Value assessment" not in home_after_adequacy.text
    case_after_adequacy = web_fixture.client.get(f"/cases/{case_id}")
    assert (
        f"/cases/{case_id}/actions/{value_reliance.responsibility_version_id}"
        not in case_after_adequacy.text
    )
    risk_reliance = fx.responsibilities[(AssessmentLane.RISK, "reliance")]
    unavailable = web_fixture.client.get(
        f"/cases/{case_id}/actions/{risk_reliance.responsibility_version_id}"
    )
    assert unavailable.status_code == 409

    second_principal = "principal:slice-h-risk-reviewer"
    second_token = "slice-h-risk-reviewer-disposable-token-00001"
    web_fixture.operational.provision_principal(
        web_fixture.admin_session,
        principal_id=second_principal,
        token=second_token,
        actor_id=fx.actor_b,
        status=PrincipalStatus.ENABLED,
    )
    for access in (
        AccessGrantInput(Permission.LOGIN, "use", ScopeType.GLOBAL, None, AccessEffect.ALLOW),
        AccessGrantInput(
            Permission.CASE_READ,
            "read",
            ScopeType.CASE,
            case_id,
            AccessEffect.ALLOW,
        ),
        AccessGrantInput(
            Permission.COMMAND,
            "assessment.reliance.risk",
            ScopeType.CASE,
            case_id,
            AccessEffect.ALLOW,
        ),
        AccessGrantInput(
            Permission.OPERATIONAL_ADMIN,
            "source-access.manage",
            ScopeType.GLOBAL,
            None,
            AccessEffect.ALLOW,
        ),
    ):
        web_fixture.operational.grant_access(
            web_fixture.admin_session,
            principal_id=second_principal,
            grant=access,
        )
    _grant_all_case_sources(
        web_fixture,
        case_id,
        configuration_id,
        principal_id=second_principal,
    )
    current_page = web_fixture.client.get("/account")
    logged_out = web_fixture.client.post(
        "/logout",
        data={"csrf_token": csrf_from(current_page.text)},
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    assert logged_out.status_code == 303
    login_page = web_fixture.client.get("/login")
    second_login = web_fixture.client.post(
        "/session",
        data={
            "principal_id": second_principal,
            "credential": second_token,
            "csrf_token": csrf_from(login_page.text),
        },
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    assert second_login.status_code == 303
    _submit_action(
        web_fixture,
        case_id=case_id,
        responsibility_version_id=risk_reliance.responsibility_version_id,
        payload={"rationale": "Use this exact adequate Risk assessment."},
    )

    with web_fixture.operational.domain_store.read_transaction() as tx:
        value = tx.projection_rows("assessment_reliance_versions", lane="VALUE")
        risk = tx.projection_rows("assessment_reliance_versions", lane="RISK")
        assert len(value) == len(risk) == 1
        assert value[0]["assignment_version_id"] == str(value_reliance.assignment_version_id)
        assert risk[0]["assignment_version_id"] == str(risk_reliance.assignment_version_id)
        value_source = tx.get_version(RecordVersionId.parse(str(value[0]["version_id"])))
        assert value_source is not None
        assert "exactly one eligible adequate Value assessment" in str(
            value_source.content["rationale"]
        )


def test_multiple_adequate_candidates_present_bounded_reliance_choice(
    web_fixture: WebFixture,
) -> None:
    """No recency/display winner replaces the accountable explicit candidate choice."""

    fx = slice_c_fixture(web_fixture.operational.domain_store, "slice-h-choice")
    case_id = fx.opened.facts.case_id
    configuration_id = fx.opened.facts.configuration_id
    first = finish_command(fx, AssessmentLane.VALUE, "slice-h-choice-first")
    second = finish_command(fx, AssessmentLane.VALUE, "slice-h-choice-second")
    first = replace(
        first,
        content=AssessmentContent(
            "Option A emphasizes service consistency.",
            first.content.boundary,
            first.content.uncertainty,
            first.content.implication,
            first.content.provenance,
        ),
    )
    second = replace(
        second,
        content=AssessmentContent(
            "Option B emphasizes staff capacity.",
            second.content.boundary,
            second.content.uncertainty,
            second.content.implication,
            second.content.provenance,
        ),
    )
    first_adequacy = adequacy_command(fx, first, "slice-h-choice-first-adequacy")
    second_adequacy = adequacy_command(fx, second, "slice-h-choice-second-adequacy")
    fx.service.finish_assessment(first)
    fx.service.finish_assessment(second)
    fx.service.determine_adequacy(first_adequacy)
    fx.service.determine_adequacy(second_adequacy)

    web_fixture.now.value = RECORDED + timedelta(seconds=10)
    _use_fixture_clock(web_fixture)
    web_fixture.operational.provision_principal(
        web_fixture.admin_session,
        principal_id="principal:web-practitioner",
        token=TOKEN,
        actor_id=fx.actor_a,
        status=PrincipalStatus.ENABLED,
    )
    web_fixture.admin_session = web_fixture.operational.authenticate(
        "principal:web-practitioner", TOKEN
    )
    grant(web_fixture, Permission.CASE_READ, "read", ScopeType.CASE, case_id)
    grant(web_fixture, Permission.OPERATIONAL_ADMIN, "source-access.manage")
    grant(
        web_fixture,
        Permission.COMMAND,
        "assessment.reliance.value",
        ScopeType.CASE,
        case_id,
    )
    _grant_all_case_sources(web_fixture, case_id, configuration_id)
    _, logged_in = login(web_fixture.client)
    assert logged_in.status_code == 303
    with web_fixture.operational.domain_store.read_transaction() as tx:
        assert tx.count_rows("assessment_reliance_versions") == 0
    responsibility = fx.responsibilities[(AssessmentLane.VALUE, "reliance")]
    action_path = f"/cases/{case_id}/actions/{responsibility.responsibility_version_id}"
    action = web_fixture.client.get(action_path)
    assert action.status_code == 200
    assert "Which assessment should be used for this decision?" in action.text
    assert "Option A emphasizes service consistency." in action.text
    assert "Option B emphasizes staff capacity." in action.text
    assert str(first.facts.assessment_version_id) not in action.text
    assert str(second.facts.assessment_version_id) not in action.text
    reviewed = web_fixture.client.post(
        f"{action_path}/review",
        data={
            "csrf_token": csrf_from(action.text),
            "candidate_choice": "candidate-1",
            "rationale": "Use the explicitly chosen bounded assessment; do not infer a winner.",
        },
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    assert reviewed.status_code == 303
    confirmation = web_fixture.client.get(reviewed.headers["location"])
    committed = web_fixture.client.post(
        confirmation.url.path.replace("/confirm/", "/commit/"),
        data={"csrf_token": csrf_from(confirmation.text)},
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    assert committed.status_code == 303, committed.text
    with web_fixture.operational.domain_store.read_transaction() as tx:
        reliance = tx.projection_rows("assessment_reliance_versions", lane="VALUE")
        assert len(reliance) == 1
        dispositions = reliance[0]["candidate_dispositions_json"]
        assert "NOT_SELECTED_FOR_THIS_USE" in str(dispositions)


def test_history_shows_only_explicitly_comparable_expected_observed_change(
    web_fixture: WebFixture,
) -> None:
    """Optional measures appear only through the exact Slice-F comparability basis."""

    fx = SliceFFixture(web_fixture.operational.domain_store, "slice-h-quantitative")
    expected = claim_command(
        fx,
        "slice-h-expected",
        QuantitativeClaimType.ESTIMATE_EXPECTATION,
        "30",
    )
    observed = claim_command(
        fx,
        "slice-h-observed",
        QuantitativeClaimType.OBSERVED_RESULT,
        "24",
    )
    fx.service.record_claim(expected)
    later = QuantitativeClaimService(
        web_fixture.operational.domain_store,
        FixedClock(QUANTITATIVE_KNOWN + timedelta(seconds=1)),
        fx.access,
    )
    later.record_claim(observed)
    comparison = comparability_command(
        fx,
        expected.facts.version_id,
        observed.facts.version_id,
        "slice-h-quantitative-comparison",
    )
    later.establish_comparability(comparison)

    web_fixture.now.value = QUANTITATIVE_KNOWN
    _use_fixture_clock(web_fixture)
    web_fixture.operational.provision_principal(
        web_fixture.admin_session,
        principal_id="principal:web-practitioner",
        token=TOKEN,
        actor_id=fx.actor_id,
        status=PrincipalStatus.ENABLED,
    )
    web_fixture.admin_session = web_fixture.operational.authenticate(
        "principal:web-practitioner", TOKEN
    )
    grant(web_fixture, Permission.CASE_READ, "read", ScopeType.CASE, fx.case_id)
    grant(web_fixture, Permission.OPERATIONAL_ADMIN, "source-access.manage")
    _grant_all_case_sources(
        web_fixture,
        fx.case_id,
        fx.configuration_id,
        effective_from=PROSPECTIVE_NOW,
    )
    web_fixture.now.value = QUANTITATIVE_KNOWN + timedelta(seconds=2)
    _use_fixture_clock(web_fixture)
    _, logged_in = login(web_fixture.client)
    assert logged_in.status_code == 303
    comparison_view = web_fixture.operational.slice_h_comparison(
        web_fixture.admin_session,
        fx.case_id,
        prior_effective_at=PROSPECTIVE_NOW,
        prior_known_at=QUANTITATIVE_KNOWN,
        current_effective_at=web_fixture.now.value,
        current_known_at=web_fixture.now.value,
    )
    prior_position = web_fixture.operational._reconstruction.current_position(  # type: ignore[attr-defined]
        principal_id="principal:web-practitioner",
        actor_id=fx.actor_id,
        case_id=fx.case_id,
        effective_at=PROSPECTIVE_NOW,
        known_at=QUANTITATIVE_KNOWN,
    )
    current_position = web_fixture.operational._reconstruction.current_position(  # type: ignore[attr-defined]
        principal_id="principal:web-practitioner",
        actor_id=fx.actor_id,
        case_id=fx.case_id,
        effective_at=web_fixture.now.value,
        known_at=web_fixture.now.value,
    )
    assert prior_position.state.value == "AVAILABLE", prior_position
    assert current_position.state.value == "AVAILABLE", current_position
    assert any(change.quantitative_pair_changes for change in comparison_view.changes), (
        comparison_view
    )
    history = web_fixture.client.get(
        f"/cases/{fx.case_id}/history-decisions",
        params={
            "effective_at": PROSPECTIVE_NOW.isoformat(),
            "known_at": QUANTITATIVE_KNOWN.isoformat(),
        },
    )
    assert history.status_code == 200
    assert "Explicitly comparable result" in history.text
    assert "difference -6" in history.text
    assert "No quality, causality, or Decision conclusion is inferred" in history.text
    for prohibited in ("better", "worse", "successful decision", "wrong decision"):
        assert prohibited not in history.text.casefold()


def test_focused_review_uses_exact_event_and_unchanged_decision_production_path(
    web_fixture: WebFixture,
) -> None:
    """Event attention begins and completes one focused review without lane fabrication."""

    fx = slice_e_fixture(web_fixture.operational.domain_store, "slice-h-focused-review")
    source = fx.source.source
    case_id = source.opened.facts.case_id
    configuration_id = source.opened.facts.configuration_id
    web_fixture.now.value = RECORDED + timedelta(seconds=10)
    _use_fixture_clock(web_fixture)
    web_fixture.operational.provision_principal(
        web_fixture.admin_session,
        principal_id="principal:web-practitioner",
        token=TOKEN,
        actor_id=source.actor_a,
        status=PrincipalStatus.ENABLED,
    )
    web_fixture.admin_session = web_fixture.operational.authenticate(
        "principal:web-practitioner", TOKEN
    )
    grant(web_fixture, Permission.CASE_READ, "read", ScopeType.CASE, case_id)
    grant(web_fixture, Permission.OPERATIONAL_ADMIN, "source-access.manage")
    for action in (
        "review.episode.begin",
        "decision.confirm",
        "review.episode.complete",
        "review.plan",
    ):
        grant(web_fixture, Permission.COMMAND, action, ScopeType.CASE, case_id)
    begin = fx.responsibilities[ObligationKind.BEGIN_CONTINUING_REVIEW]
    event = RecordEventReviewAttentionCommand(
        identity(source.actor_a, "slice-h-focused-event"),
        ReviewRecordFacts.new(),
        CONTRACT,
        source.opened.context,
        case_id,
        source.opened.facts.configuration_version_id,
        fx.decision_version_id,
        fx.evidence_version_id,
        REVIEW_PURPOSE,
        ASSESSED_SCOPE,
        (ReviewFocus.NO_SUBSTANTIVE_CHANGE, ReviewFocus.DECISION_CONFIRMATION),
        "One exact visible information change calls for bounded review only.",
        begin.responsibility_version_id,
        begin.assignment_version_id,
        web_fixture.now.value,
        KNOWLEDGE,
    )
    fx.service.record_event_review_attention(event)
    _grant_all_case_sources(web_fixture, case_id, configuration_id)
    _, logged_in = login(web_fixture.client)
    assert logged_in.status_code == 303

    _submit_action(
        web_fixture,
        case_id=case_id,
        responsibility_version_id=begin.responsibility_version_id,
        payload={"acknowledgment": "BEGIN"},
    )
    confirmation = fx.source.responsibilities[ObligationKind.CONFIRM_MANAGEMENT_DECISION]
    _submit_action(
        web_fixture,
        case_id=case_id,
        responsibility_version_id=confirmation.responsibility_version_id,
        payload={
            "rationale": "The exact focused information does not change the current Decision."
        },
    )
    completion = fx.responsibilities[ObligationKind.COMPLETE_CONTINUING_REVIEW]
    _submit_action(
        web_fixture,
        case_id=case_id,
        responsibility_version_id=completion.responsibility_version_id,
        payload={"rationale": "The bounded focused review is complete with no substantive change."},
    )
    planning = fx.responsibilities[ObligationKind.PLAN_NEXT_REVIEW]
    _submit_action(
        web_fixture,
        case_id=case_id,
        responsibility_version_id=planning.responsibility_version_id,
        payload={
            "review_at": (web_fixture.now.value + timedelta(days=30)).isoformat(),
            "rationale": "Review this continuing Case again in thirty days.",
        },
    )

    case_page = web_fixture.client.get(f"/cases/{case_id}")
    assert case_page.status_code == 200
    assert "No Open Review" in case_page.text
    home = web_fixture.client.get("/home")
    home_view = web_fixture.operational.slice_h_home(web_fixture.admin_session)
    assert "Nothing currently needs your attention." in home.text, tuple(
        (item.kind, item.question) for item in home_view.items
    )
    with web_fixture.operational.domain_store.read_transaction() as tx:
        assert tx.count_rows("review_attention_event_versions") == 1
        assert tx.count_rows("review_episode_versions") == 2
        completed = tx.projection_rows("review_episode_versions", status="COMPLETED")
        assert len(completed) == 1
        assert completed[0]["outcome"] == "UNCHANGED_DECISION_CONFIRMED"
        assert tx.count_rows("assessment_candidate_versions") == 2


def test_stale_intent_and_hidden_exact_source_fail_closed_without_mutation(
    web_fixture: WebFixture,
) -> None:
    """No stale retarget or source-existence disclosure crosses the browser adapter."""

    fx = slice_d_fixture(web_fixture.operational.domain_store, "slice-h-stale-hidden")
    source = fx.source
    case_id = source.opened.facts.case_id
    configuration_id = source.opened.facts.configuration_id
    web_fixture.now.value = RECORDED + timedelta(seconds=10)
    _use_fixture_clock(web_fixture)
    web_fixture.operational.provision_principal(
        web_fixture.admin_session,
        principal_id="principal:web-practitioner",
        token=TOKEN,
        actor_id=source.actor_a,
        status=PrincipalStatus.ENABLED,
    )
    web_fixture.admin_session = web_fixture.operational.authenticate(
        "principal:web-practitioner", TOKEN
    )
    _prepare_browser_access(web_fixture, case_id)
    _grant_all_case_sources(web_fixture, case_id, configuration_id)
    _, logged_in = login(web_fixture.client)
    assert logged_in.status_code == 303

    responsibility = fx.responsibilities[
        ObligationKind.COMPLETE_VALUE_RISK_INTEGRATION
    ].responsibility_version_id
    action_path = f"/cases/{case_id}/actions/{responsibility}"
    action_page = web_fixture.client.get(action_path)
    assert action_page.status_code == 200
    reviewed = web_fixture.client.post(
        f"{action_path}/review",
        data={
            "csrf_token": csrf_from(action_page.text),
            "rationale": "Review the exact independent lanes.",
            "material_tensions": "",
            "limitations": "",
            "uncertainty": "Bounded uncertainty remains.",
            "unresolved_conditions": "",
        },
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    assert reviewed.status_code == 303
    confirmation_page = web_fixture.client.get(reviewed.headers["location"])
    assert confirmation_page.status_code == 200

    competing = integration_command(fx, "slice-h-stale-competing")
    fx.service.integrate_value_risk(competing)
    _grant_all_case_sources(web_fixture, case_id, configuration_id)
    with web_fixture.operational.domain_store.read_transaction() as tx:
        before = tx.count_rows("prospective_integration_versions")
    stale = web_fixture.client.post(
        confirmation_page.url.path.replace("/confirm/", "/commit/"),
        data={"csrf_token": csrf_from(confirmation_page.text)},
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    assert stale.status_code == 409
    assert "No governed record was changed" in stale.text
    with web_fixture.operational.domain_store.read_transaction() as tx:
        assert tx.count_rows("prospective_integration_versions") == before == 1

    hidden_version_id = fx.value.assessment_version_id
    hidden_source = web_fixture.operational.domain_store.get_version(hidden_version_id)
    assert hidden_source is not None
    web_fixture.operational.grant_source_access(
        web_fixture.admin_session,
        principal_id="principal:web-practitioner",
        grant=SourceAccessGrantInput(
            "source.read",
            case_id,
            hidden_version_id,
            hidden_source.family,
            AccessEffect.DENY,
            web_fixture.now.value,
        ),
    )
    hidden_case = web_fixture.client.get(f"/cases/{case_id}")
    assert hidden_case.status_code == 200
    assert str(hidden_version_id) not in hidden_case.text
    assert action_path not in hidden_case.text
    denied_action = web_fixture.client.get(action_path)
    assert denied_action.status_code == 409
    assert str(hidden_version_id) not in denied_action.text
    with web_fixture.operational.domain_store.read_transaction() as tx:
        assert tx.count_rows("prospective_integration_versions") == 1

    with OperationalApplication(web_fixture.config, FixedClock(web_fixture.now.value)) as restarted:
        restarted_session = restarted.authenticate("principal:web-practitioner", TOKEN)
        restarted_view = restarted.slice_h_case(restarted_session, case_id)
        assert restarted_view.case_id == case_id
        assert restarted_view.value_position is not None
        assert "NOT AVAILABLE" in restarted_view.value_position.assessment
        assert restarted.slice_h_timeline(restarted_session, case_id).case_id == case_id
