from __future__ import annotations

from paim.application.practitioner import exact_current_integration_basis
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
    exact_basis = exact_current_integration_basis(
        integration,
        value=with_integration.value,
        risk=with_integration.risk,
    )
    assert exact_basis is not None
    assert integration.content == {
        **integration.content,
        "value_input_version_id": exact_basis.value_input.version_id,
        "value_acceptance_version_id": exact_basis.value_selection.version_id,
        "value_fitness_version_id": exact_basis.value_fitness.version_id,
        "risk_input_version_id": exact_basis.risk_input.version_id,
        "risk_acceptance_version_id": exact_basis.risk_selection.version_id,
        "risk_fitness_version_id": exact_basis.risk_fitness.version_id,
        "use_context": exact_basis.use_context,
        "purpose": exact_basis.purpose,
    }

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


def test_m1c_old_chain_fails_closed_after_current_lane_selection_changes(
    web_fixture: WebFixture,
) -> None:
    establish_m1b_path(web_fixture)
    _grant_m1c(web_fixture)
    base = f"/cases/{web_fixture.visible_case_id}"
    initial = web_fixture.operational.practitioner_workspace(
        web_fixture.admin_session, web_fixture.visible_case_id
    )
    assert initial is not None
    configuration = next(item for item in initial.configurations if item.is_governing)

    for target in ("configuration_defined", "evidence_analysis", "ready_for_integration"):
        assert (
            _review_commit(
                web_fixture.client,
                f"{base}/case-lifecycle-advance/review",
                {"target_state": target, "effective_at": initial.effective_at.isoformat()},
            )[2].status_code
            == 303
        )
    assert (
        _review_commit(
            web_fixture.client,
            f"{base}/integration-create/review",
            {
                "status": "completed",
                "reinforcing_effects": "Exact current lanes remain separate.",
                "conflicts": "No conflict is silently resolved.",
                "tradeoffs": "The explicit Risk constraint remains.",
                "remaining_uncertainty": "Recorded uncertainty remains explicit.",
                "proposed_judgment": "Continue only inside the exact Boundary.",
                "accountable_mechanism": "governed:m1c-current-basis-oracle",
                "rationale": "Bind the exact current Value and Risk basis.",
                "effective_at": initial.effective_at.isoformat(),
            },
        )[2].status_code
        == 303
    )
    integrated = web_fixture.operational.practitioner_workspace(
        web_fixture.admin_session, web_fixture.visible_case_id
    )
    assert integrated is not None
    integration = integrated.decision.integrations[0]
    assert (
        _review_commit(
            web_fixture.client,
            f"{base}/case-lifecycle-advance/review",
            {
                "target_state": "decision_pending",
                "effective_at": initial.effective_at.isoformat(),
            },
        )[2].status_code
        == 303
    )
    boundary_data = {
        "integration_version_id": integration.version_id,
        "status": "finalized",
        "clause_type": "capacity",
        "effect": "limited",
        "target_reference": "requests-per-minute",
        "operator": "LTE",
        "structured_value": "100",
        "verification_mode": "mechanically_testable",
        "narrative": "Capacity remains at or below 100 rpm.",
        "clause_rationale": "Retain the exact Risk boundary.",
        "provenance": "exact-current-basis",
        "narrative_rationale": "Explicit bounded-operation envelope.",
        "effective_at": initial.effective_at.isoformat(),
    }
    assert (
        _review_commit(web_fixture.client, f"{base}/boundary-create/review", boundary_data)[
            2
        ].status_code
        == 303
    )
    bounded = web_fixture.operational.practitioner_workspace(
        web_fixture.admin_session, web_fixture.visible_case_id
    )
    assert bounded is not None
    boundary = bounded.decision.boundaries[0]
    proposal_data = {
        "integration_version_id": integration.version_id,
        "boundary_snapshot_version_id": boundary.version_id,
        "status": "pending_authorization",
        "proposed_action": "Continue within the exact finalized Boundary.",
        "operating_state": "bounded continuation",
        "rationale": "The exact current Value/Risk basis controls.",
        "effective_at": initial.effective_at.isoformat(),
    }
    assert (
        _review_commit(web_fixture.client, f"{base}/decision-propose/review", proposal_data)[
            2
        ].status_code
        == 303
    )
    assert (
        _review_commit(
            web_fixture.client,
            f"{base}/authority/review",
            {
                "configuration_id": configuration.configuration_id,
                "configuration_version_id": configuration.version_id,
                "category": "decision-right",
                "source": "authority-register:current-basis-oracle",
                "scope": "narrow-scope",
                "requirement": "Authorize bounded continuation.",
                "provenance": "accepted authority register",
                "notes": "Exact scope only.",
                "effective_at": initial.effective_at.isoformat(),
            },
        )[2].status_code
        == 303
    )
    assignment_id, assignment_version_id = RecordId.new(), RecordVersionId.new()
    web_fixture.operational.run_command(
        web_fixture.admin_session,
        action="role.assign",
        idempotency_key="m1c-current-basis-decision-authority",
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
                "m1c-current-basis-decision-authority",
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
    decision = ready.decision.decisions[0]
    authority = ready.authority[0]

    def review(path: str, data: dict[str, str]):
        response = web_fixture.client.post(
            path,
            data={
                "csrf_token": csrf_from(web_fixture.client.get(f"{base}/decision").text),
                **data,
            },
            headers={"Origin": ORIGIN},
            follow_redirects=False,
        )
        assert response.status_code == 303, response.text
        confirmation = web_fixture.client.get(response.headers["location"])
        assert confirmation.status_code == 200
        return confirmation

    boundary_confirmation = review(f"{base}/boundary-create/review", boundary_data)
    proposal_confirmation = review(f"{base}/decision-propose/review", proposal_data)
    authorization_data = {
        "decision_version_id": decision.version_id,
        "authority_assignment_version_id": str(assignment_version_id),
        "authority_record_version_id": authority.version_id,
        "authorized_scope": "narrow-scope",
        "decision_type": "bounded operation",
        "effective_at": initial.effective_at.isoformat(),
    }
    authorization_confirmation = review(f"{base}/decision-authorize/review", authorization_data)

    candidate = ready.value.candidates[0]
    fitness = next(item for item in ready.value.fitness if item.state == "SUPPORTABLE")
    applicability = next(
        item
        for item in ready.applicability
        if item.content.get("target_version_id") == candidate.version_id
    )
    assert (
        _review_commit(
            web_fixture.client,
            f"{base}/value/selection/review",
            {
                "configuration_id": configuration.configuration_id,
                "configuration_version_id": configuration.version_id,
                "input_version_id": candidate.version_id,
                "fitness_version_id": fitness.version_id,
                "use_context": "bounded-operation",
                "purpose": "bounded-management",
                "rationale": "A new current selection conflicts with the old exact basis.",
                "accountable_mechanism": "governed:m1c-current-basis-change",
                "material_applicability_version_ids": applicability.version_id,
                "effective_at": initial.effective_at.isoformat(),
            },
        )[2].status_code
        == 303
    )
    changed = web_fixture.operational.practitioner_workspace(
        web_fixture.admin_session, web_fixture.visible_case_id
    )
    assert changed is not None
    assert changed.value.selection_state.value == "CONFLICT"
    assert changed.decision.integration_state.value == "ABSENT"
    assert changed.decision.integrations == ()
    assert changed.decision.boundaries == ()
    assert changed.decision.decisions == ()
    current_page = web_fixture.client.get(f"{base}/decision")
    assert integration.version_id not in current_page.text
    assert boundary.version_id not in current_page.text
    assert decision.version_id not in current_page.text

    counts_before = tuple(
        web_fixture.operational.domain_store.count_rows(table)
        for table in (
            "integration_versions",
            "boundary_snapshot_versions",
            "decision_versions",
            "decision_authorization_basis_versions",
        )
    )
    for confirmation in (
        boundary_confirmation,
        proposal_confirmation,
        authorization_confirmation,
    ):
        response = web_fixture.client.post(
            confirmation.request.url.path.replace("/confirm/", "/commit/"),
            data={"csrf_token": csrf_from(confirmation.text)},
            headers={"Origin": ORIGIN},
        )
        assert response.status_code in {400, 409}
        assert "production command revalidated the exact submitted basis" in response.text

    for path, data in (
        (f"{base}/boundary-create/review", boundary_data),
        (f"{base}/decision-propose/review", proposal_data),
        (f"{base}/decision-authorize/review", authorization_data),
    ):
        response = web_fixture.client.post(
            path,
            data={
                "csrf_token": csrf_from(web_fixture.client.get(f"{base}/decision").text),
                **data,
            },
            headers={"Origin": ORIGIN},
        )
        assert response.status_code == 409
        assert "No governed record was changed" in response.text

    counts_after = tuple(
        web_fixture.operational.domain_store.count_rows(table)
        for table in (
            "integration_versions",
            "boundary_snapshot_versions",
            "decision_versions",
            "decision_authorization_basis_versions",
        )
    )
    assert counts_after == counts_before
    reconstructed = web_fixture.operational.practitioner_workspace(
        web_fixture.admin_session, web_fixture.visible_case_id
    )
    assert reconstructed is not None
    historical_version_ids = {item.version_id for item in reconstructed.decision.history}
    assert {integration.version_id, boundary.version_id, decision.version_id} <= (
        historical_version_ids
    )
    history = web_fixture.client.get(f"{base}/history")
    assert "Integration" in history.text
    assert "Boundary Snapshot" in history.text
    assert "Decision" in history.text
    assert integration.version_id not in history.text
    assert "technical inspection is deferred" in history.text
