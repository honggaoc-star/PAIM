from __future__ import annotations

from paim.domain import DelegationEffect, RoleAssignmentVersionInput, RoleTargetType
from paim.integrity import RecordId, RecordVersionId
from paim.operational import Permission, ScopeType
from tests.integration.test_web_m1b import _review_commit
from tests.integration.test_web_m1b import (
    test_m1b_workspace_exact_configuration_and_independent_value_risk_path as establish_m1b_path,
)
from tests.web_support import EFFECTIVE, ORIGIN, WebFixture, csrf_from, grant


def _grant_m1c(fixture: WebFixture) -> None:
    for action in (
        "case.lifecycle.advance",
        "integration.create",
        "boundary.create",
        "decision.propose",
        "decision.authorize",
        "role.assign",
    ):
        grant(fixture, Permission.COMMAND, action, ScopeType.CASE, fixture.visible_case_id)


def test_m1c_browser_path_keeps_proposal_and_authorization_separate(
    web_fixture: WebFixture,
) -> None:
    establish_m1b_path(web_fixture)
    _grant_m1c(web_fixture)
    base = f"/cases/{web_fixture.visible_case_id}"

    view = web_fixture.operational.practitioner_workspace(
        web_fixture.admin_session, web_fixture.visible_case_id
    )
    assert view is not None
    configuration = next(item for item in view.configurations if item.is_governing)
    assert view.decision.selected_value is not None
    assert view.decision.selected_risk is not None
    page = web_fixture.client.get(f"{base}/decision")
    assert page.status_code == 200
    assert "No automatic synthesis" in page.text
    assert "separate substantive authorization" in page.text
    assert str(web_fixture.hidden_case_id) not in page.text

    # The lifecycle remains explicit and advances one exact successor at a time.
    for target in ("configuration_defined", "evidence_analysis", "ready_for_integration"):
        result = _review_commit(
            web_fixture.client,
            f"{base}/case-lifecycle-advance/review",
            {"target_state": target, "effective_at": view.effective_at.isoformat()},
        )[2]
        assert result.status_code == 303, result.text

    integration_commit = _review_commit(
        web_fixture.client,
        f"{base}/integration-create/review",
        {
            "status": "completed",
            "reinforcing_effects": "Both exact lanes support bounded operation.",
            "conflicts": "No conflict is silently resolved.",
            "tradeoffs": "The bounded scope retains the Risk constraint.",
            "remaining_uncertainty": "The recorded lane uncertainty remains explicit.",
            "alternatives": "Suspend operation",
            "proposed_judgment": "Continue only within the explicit Boundary.",
            "constraint_references": "policy:bounded-operation",
            "authority_record_version_ids": "",
            "authority_gap_version_ids": "",
            "accountable_mechanism": "governed:m1c-integration-board",
            "rationale": "Exact selected Value and Risk support bounded integration.",
            "effective_at": view.effective_at.isoformat(),
        },
    )[2]
    assert integration_commit.status_code == 303, integration_commit.text

    with_integration = web_fixture.operational.practitioner_workspace(
        web_fixture.admin_session, web_fixture.visible_case_id
    )
    assert with_integration is not None
    assert with_integration.decision.integration_state.value == "ESTABLISHED"
    integration = with_integration.decision.integrations[0]
    assert integration.content["value_input_version_id"] == (
        with_integration.decision.selected_value.version_id
    )
    assert integration.content["risk_input_version_id"] == (
        with_integration.decision.selected_risk.version_id
    )

    pending = _review_commit(
        web_fixture.client,
        f"{base}/case-lifecycle-advance/review",
        {"target_state": "decision_pending", "effective_at": view.effective_at.isoformat()},
    )[2]
    assert pending.status_code == 303, pending.text

    boundary_commit = _review_commit(
        web_fixture.client,
        f"{base}/boundary-create/review",
        {
            "integration_version_id": integration.version_id,
            "status": "finalized",
            "clause_type": "capacity",
            "effect": "limited",
            "target_reference": "requests-per-minute",
            "structured_reference": "metric:rpm",
            "operator": "LTE",
            "structured_value": "100",
            "unit": "rpm",
            "verification_mode": "mechanically_testable",
            "narrative": "Capacity remains at or below 100 rpm.",
            "clause_rationale": "Retains the exact Risk boundary.",
            "provenance": "value-selection\nrisk-selection",
            "breach_consequence": "Suspend affected operation.",
            "narrative_rationale": "Explicit bounded-operation envelope.",
            "unresolved_items": "",
            "effective_at": view.effective_at.isoformat(),
        },
    )[2]
    assert boundary_commit.status_code == 303, boundary_commit.text

    boundary_view = web_fixture.operational.practitioner_workspace(
        web_fixture.admin_session, web_fixture.visible_case_id
    )
    assert boundary_view is not None
    boundary = boundary_view.decision.boundaries[0]
    proposal_commit = _review_commit(
        web_fixture.client,
        f"{base}/decision-propose/review",
        {
            "integration_version_id": integration.version_id,
            "boundary_snapshot_version_id": boundary.version_id,
            "status": "pending_authorization",
            "proposed_action": "Continue within the exact finalized Boundary.",
            "operating_state": "bounded continuation",
            "rationale": "Value and Risk remain independent inputs to the proposal.",
            "conditions_and_limits": "Do not exceed 100 rpm.",
            "alternatives_considered": "Suspend operation",
            "constraint_references": "policy:bounded-operation",
            "authority_record_version_ids": "",
            "authority_gap_version_ids": "",
            "intervention_declarations": "",
            "learning_declarations": "Collect longitudinal evidence.",
            "reassessment_declarations": "Reassess on Boundary breach.",
            "effective_at": view.effective_at.isoformat(),
        },
    )[2]
    assert proposal_commit.status_code == 303, proposal_commit.text
    proposed = web_fixture.operational.practitioner_workspace(
        web_fixture.admin_session, web_fixture.visible_case_id
    )
    assert proposed is not None
    assert proposed.decision.decision_state.value == "ESTABLISHED"
    assert proposed.decision.authorization_state.value == "ABSENT"
    assert (
        web_fixture.operational.domain_store.count_rows("decision_authorization_basis_versions")
        == 0
    )

    authority_commit = _review_commit(
        web_fixture.client,
        f"{base}/authority/review",
        {
            "configuration_id": configuration.configuration_id,
            "configuration_version_id": configuration.version_id,
            "category": "decision-right",
            "source": "authority-register:v1",
            "scope": "narrow-scope",
            "requirement": "Authorize bounded continuation.",
            "provenance": "accepted authority register",
            "notes": "Exact scope only.",
            "effective_at": view.effective_at.isoformat(),
        },
    )[2]
    assert authority_commit.status_code == 303, authority_commit.text

    without_assignment = web_fixture.client.post(
        f"{base}/decision-authorize/review",
        data={
            "csrf_token": csrf_from(web_fixture.client.get(f"{base}/decision").text),
            "decision_version_id": proposed.decision.decisions[0].version_id,
            "authority_assignment_version_id": str(RecordVersionId.new()),
            "authority_record_version_id": web_fixture.operational.practitioner_workspace(
                web_fixture.admin_session, web_fixture.visible_case_id
            )
            .authority[0]
            .version_id,
            "authorized_scope": "narrow-scope",
            "decision_type": "bounded operation",
            "effective_at": view.effective_at.isoformat(),
        },
        headers={"Origin": ORIGIN},
    )
    assert without_assignment.status_code == 409
    assert "Decision Authority assignment" in without_assignment.text
    assert (
        web_fixture.operational.domain_store.count_rows("decision_authorization_basis_versions")
        == 0
    )

    assignment_id, assignment_version_id = RecordId.new(), RecordVersionId.new()
    web_fixture.operational.run_command(
        web_fixture.admin_session,
        action="role.assign",
        idempotency_key="m1c-decision-authority",
        case_id=web_fixture.visible_case_id,
        operation=lambda service, meta: service.commit_role_assignment(
            meta,
            RoleAssignmentVersionInput(
                assignment_id,
                assignment_version_id,
                web_fixture.actor_id,
                "Decision Authority",
                RoleTargetType.CASE,
                str(web_fixture.visible_case_id),
                web_fixture.visible_case_id,
                True,
                "m1c-decision-authority",
                DelegationEffect.NONE,
                None,
                EFFECTIVE,
            ),
        ),
    )
    ready = web_fixture.operational.practitioner_workspace(
        web_fixture.admin_session, web_fixture.visible_case_id
    )
    assert ready is not None
    authority = ready.authority[0]
    decision = ready.decision.decisions[0]
    assert any(
        item.version_id == str(assignment_version_id)
        for item in ready.decision.authority_assignments
    )

    _, authorization_confirmation, authorization_commit = _review_commit(
        web_fixture.client,
        f"{base}/decision-authorize/review",
        {
            "decision_version_id": decision.version_id,
            "authority_assignment_version_id": str(assignment_version_id),
            "authority_record_version_id": authority.version_id,
            "decision_authority_identity": "M1A Practitioner",
            "authorized_scope": "narrow-scope",
            "limits": "Do not exceed 100 rpm.",
            "decision_type": "bounded operation",
            "organizational_unit": "",
            "conditions": "Retain explicit Boundary.",
            "dissent": "",
            "exception": "",
            "effective_at": view.effective_at.isoformat(),
        },
    )
    assert authorization_commit.status_code == 303, authorization_commit.text
    authorization_count = web_fixture.operational.domain_store.count_rows(
        "decision_authorization_basis_versions"
    )
    duplicate = web_fixture.client.post(
        authorization_confirmation.request.url.path.replace("/confirm/", "/commit/"),
        data={"csrf_token": csrf_from(authorization_confirmation.text)},
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    assert duplicate.status_code == 303
    assert (
        web_fixture.operational.domain_store.count_rows("decision_authorization_basis_versions")
        == authorization_count
    )
    authorized = web_fixture.operational.practitioner_workspace(
        web_fixture.admin_session, web_fixture.visible_case_id
    )
    assert authorized is not None
    assert authorized.decision.authorization_state.value == "ESTABLISHED"
    assert authorized.lifecycle_state == "decided"
    assert (
        authorized.value.selections[0].content["input_version_id"]
        != (authorized.risk.selections[0].content["input_version_id"])
    )
    history = web_fixture.client.get(f"{base}/history")
    assert "Integration — Value: Independent Value finding" in history.text
    assert "Boundary — Explicit bounded-operation envelope." in history.text
    assert "Proposed Decision — Continue within the exact finalized Boundary." in history.text
    assert "Authorized Decision — Continue within the exact finalized Boundary." in history.text
    assert str(web_fixture.hidden_case_id) not in history.text


def test_m1c_tampered_exact_version_fails_closed(web_fixture: WebFixture) -> None:
    establish_m1b_path(web_fixture)
    _grant_m1c(web_fixture)
    base = f"/cases/{web_fixture.visible_case_id}"
    view = web_fixture.operational.practitioner_workspace(
        web_fixture.admin_session, web_fixture.visible_case_id
    )
    assert view is not None
    before = web_fixture.operational.domain_store.count_rows("integration_versions")
    response = web_fixture.client.post(
        f"{base}/boundary-create/review",
        data={
            "csrf_token": csrf_from(web_fixture.client.get(f"{base}/decision").text),
            "integration_version_id": str(RecordVersionId.new()),
            "status": "finalized",
            "clause_type": "capacity",
            "effect": "limited",
            "narrative": "Tampered exact basis must be rejected.",
            "clause_rationale": "No substitute is permitted.",
            "provenance": "tamper-oracle",
            "verification_mode": "mechanically_testable",
            "narrative_rationale": "Must not commit.",
        },
        headers={"Origin": ORIGIN},
    )
    assert response.status_code == 409
    assert "no longer one exact visible Version" in response.text
    assert str(web_fixture.hidden_case_id) not in response.text
    assert web_fixture.operational.domain_store.count_rows("integration_versions") == before


def test_m1c_changed_selected_lane_basis_fails_closed_before_integration(
    web_fixture: WebFixture,
) -> None:
    establish_m1b_path(web_fixture)
    _grant_m1c(web_fixture)
    base = f"/cases/{web_fixture.visible_case_id}"
    view = web_fixture.operational.practitioner_workspace(
        web_fixture.admin_session, web_fixture.visible_case_id
    )
    assert view is not None
    integration_review = web_fixture.client.post(
        f"{base}/integration-create/review",
        data={
            "csrf_token": csrf_from(web_fixture.client.get(f"{base}/decision").text),
            "status": "completed",
            "reinforcing_effects": "Exact reviewed effect.",
            "conflicts": "No silent resolution.",
            "tradeoffs": "Explicit tradeoff.",
            "remaining_uncertainty": "Explicit uncertainty.",
            "proposed_judgment": "Reviewed judgment.",
            "accountable_mechanism": "governed:m1c-stale-oracle",
            "rationale": "Exact reviewed basis.",
            "effective_at": view.effective_at.isoformat(),
        },
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    assert integration_review.status_code == 303
    confirmation = web_fixture.client.get(integration_review.headers["location"])
    assert confirmation.status_code == 200

    value = view.value
    candidate = value.candidates[0]
    fitness = next(item for item in value.fitness if item.state == "SUPPORTABLE")
    applicability = next(
        item
        for item in view.applicability
        if item.content.get("target_version_id") == candidate.version_id
    )
    conflicting_selection = _review_commit(
        web_fixture.client,
        f"{base}/value/selection/review",
        {
            "configuration_id": view.configurations[0].configuration_id,
            "configuration_version_id": view.configurations[0].version_id,
            "input_version_id": candidate.version_id,
            "fitness_version_id": fitness.version_id,
            "use_context": "bounded-operation",
            "purpose": "bounded-management",
            "rationale": "Second explicit selection creates conflict.",
            "accountable_mechanism": "governed:m1c-conflict-oracle",
            "material_applicability_version_ids": applicability.version_id,
            "effective_at": view.effective_at.isoformat(),
        },
    )[2]
    assert conflicting_selection.status_code == 303
    conflicted = web_fixture.operational.practitioner_workspace(
        web_fixture.admin_session, web_fixture.visible_case_id
    )
    assert conflicted is not None
    assert conflicted.value.selection_state.value == "CONFLICT"

    before = web_fixture.operational.domain_store.count_rows("integration_versions")
    stale_commit = web_fixture.client.post(
        confirmation.request.url.path.replace("/confirm/", "/commit/"),
        data={"csrf_token": csrf_from(confirmation.text)},
        headers={"Origin": ORIGIN},
    )
    assert stale_commit.status_code in {400, 409}
    assert "one exact Value selection is required" in stale_commit.text
    assert web_fixture.operational.domain_store.count_rows("integration_versions") == before
