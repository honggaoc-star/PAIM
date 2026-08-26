from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

from paim.assessment_review import (
    AssessmentContent,
    AssessmentLane,
    AssessmentReviewService,
)
from paim.case_continuity import CaseContinuityService
from paim.continuing_review import (
    ContinuingReviewService,
    RecordEventReviewAttentionCommand,
    ReviewFocus,
    ReviewRecordFacts,
)
from paim.integrity import FixedClock, RecordId, RecordVersionId
from paim.operational import (
    AccessEffect,
    AccessGrantInput,
    OperationalApplication,
    Permission,
    PrincipalStatus,
    ScopeType,
    SourceAccessGrantInput,
)
from paim.prospective_decision import ProspectiveDecisionService
from paim.quantitative_claims import QuantitativeClaimService, QuantitativeClaimType
from paim.responsibility.models import ObligationKind
from paim.responsibility.service import OperationalSliceAAccessPolicy
from tests.integration.test_gate8_slice_b_case_continuity import NOW as PROSPECTIVE_NOW
from tests.integration.test_gate8_slice_b_case_continuity import RECORDED
from tests.integration.test_gate8_slice_c_assessment_review import (
    adequacy_command,
    finish_command,
    identity,
)
from tests.integration.test_gate8_slice_c_assessment_review import (
    fixture as slice_c_fixture,
)
from tests.integration.test_gate8_slice_d_integration_decision import (
    integration_command,
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
from tests.web_support import ORIGIN, TOKEN, WebFixture, csrf_from, grant, login

_PROSPECTIVE_VERSION_TABLES = (
    "case_continuity_status_versions",
    "governing_configuration_designations",
    "responsibility_versions",
    "assignment_basis_versions",
    "responsibility_assignment_versions",
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
    _submit_action(
        web_fixture,
        case_id=case_id,
        responsibility_version_id=authorization_responsibility,
        payload={
            "authority_identity": "Harborlight bounded Decision mandate",
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
    assert "Value and Risk remain independent" in case_page.text
    assert "value score" not in case_page.text.casefold()
    assert "risk score" not in case_page.text.casefold()
    web_fixture.operational.slice_h_timeline(web_fixture.admin_session, case_id)
    history = web_fixture.client.get(f"/cases/{case_id}/history-decisions")
    assert history.status_code == 200
    assert "What happened, what was known, and why" in history.text
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
    for prohibited in (
        "semantic contract",
        "context digest",
        "assignment basis",
        "source closure",
        "transaction member",
    ):
        assert prohibited not in home.text.casefold()


def test_minimal_case_start_uses_h0_authority_and_creates_no_later_governance(
    web_fixture: WebFixture,
) -> None:
    """The ordinary New Case form invokes H0 and asks no later-domain questionnaire."""

    web_fixture.now.value = H0_NOW
    _use_fixture_clock(web_fixture)
    prepare_permissions(web_fixture)
    grant(web_fixture, Permission.OPERATIONAL_ADMIN, "access.manage")
    establish_authority(
        web_fixture,
        web_fixture.operational._case_continuity,  # type: ignore[attr-defined]
    )
    _, logged_in = login(web_fixture.client)
    assert logged_in.status_code == 303
    new_case = web_fixture.client.get("/cases/new")
    assert new_case.status_code == 200
    for prohibited in (
        "risk tier",
        "review cadence",
        "semantic metadata",
        "responsibility matrix",
        "authority mapping",
    ):
        assert prohibited not in new_case.text.casefold()
    reviewed = web_fixture.client.post(
        "/cases/start/review",
        data={
            "csrf_token": csrf_from(new_case.text),
            "title": "Harborlight Assist — disposable Slice H Case",
            "bounded_use": "small-business lending assistance",
            "setup_description": "Assistance only; accountable human lending judgment remains.",
            "effective_at": H0_NOW.isoformat(),
        },
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    assert reviewed.status_code == 303
    confirmation = web_fixture.client.get(reviewed.headers["location"])
    assert confirmation.status_code == 200
    assert "does not grant Value, Risk, Decision" in confirmation.text
    committed = web_fixture.client.post(
        confirmation.url.path.replace("/confirm/", "/commit/"),
        data={"csrf_token": csrf_from(confirmation.text)},
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    assert committed.status_code == 303
    case_page = web_fixture.client.get(committed.headers["location"])
    assert case_page.status_code == 200
    assert "Harborlight Assist" in case_page.text
    assert "small-business lending assistance" in case_page.text
    assert "What continuing management attention does this bounded AI use require?" in (
        case_page.text
    )
    with web_fixture.operational.domain_store.read_transaction() as tx:
        assert tx.count_rows("case_continuity_status_versions") == 1
        assert tx.count_rows("governing_configuration_designations") == 1
        assert tx.count_rows("responsibility_versions") == 1
        assert tx.count_rows("assessment_candidate_versions") == 0
        assert tx.count_rows("prospective_integration_versions") == 0
        assert tx.count_rows("prospective_decision_versions") == 0
        assert tx.count_rows("review_episode_versions") == 0


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
    _submit_action(
        web_fixture,
        case_id=case_id,
        responsibility_version_id=value_reliance.responsibility_version_id,
        payload={"rationale": "Use this exact adequate Value assessment."},
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
    current_page = web_fixture.client.get("/home")
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
