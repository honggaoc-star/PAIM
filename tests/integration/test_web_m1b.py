from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from paim.operational import AccessEffect, Permission, ScopeType
from tests.web_support import ORIGIN, WebFixture, csrf_from, grant, login


def _grant_m1b(fixture: WebFixture) -> None:
    grant(fixture, Permission.CONFIGURATION_READ, "read")
    for action in (
        "configuration.create",
        "configuration.designate",
        "evidence.create",
        "authority.create",
        "authority-gap.create",
        "evidence.applicability",
        "value-input.create",
        "value-input.ready",
        "value-fitness.create",
        "value-input.select",
        "risk-input.create",
        "risk-input.ready",
        "risk-fitness.create",
        "risk-input.select",
    ):
        grant(
            fixture,
            Permission.COMMAND,
            action,
            ScopeType.CASE,
            fixture.visible_case_id,
        )


def _review_commit(client: TestClient, path: str, data: dict[str, str]) -> tuple[Any, Any, Any]:
    workspace = client.get("/".join(path.split("/")[:3]))
    csrf = csrf_from(workspace.text)
    reviewed = client.post(
        path,
        data={**data, "csrf_token": csrf},
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    assert reviewed.status_code == 303, reviewed.text
    confirmation = client.get(reviewed.headers["location"])
    assert confirmation.status_code == 200, confirmation.text
    committed = client.post(
        confirmation.request.url.path.replace("/confirm/", "/commit/"),
        data={"csrf_token": csrf_from(confirmation.text)},
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    return reviewed, confirmation, committed


def test_m1b_workspace_exact_configuration_and_independent_value_risk_path(
    web_fixture: WebFixture,
) -> None:
    _grant_m1b(web_fixture)
    assert login(web_fixture.client)[1].status_code == 303
    case_id = str(web_fixture.visible_case_id)
    base = f"/cases/{case_id}"
    initial = web_fixture.client.get(base)
    assert initial.status_code == 200
    assert "no single setup is established for assessment" in initial.text
    assert "Establish one setup for assessment" in initial.text
    assert "Required for the action you chose" not in initial.text
    assert "Material conditions still unresolved" in initial.text
    assert "Current attention" not in initial.text
    assert "Software access" not in initial.text
    assert "Exact governed context" not in initial.text
    assert f"{base}/configuration" in initial.text
    assert f"{base}/assessment#value" not in initial.text
    assert "Add or revise a setup" not in initial.text
    assert "Assess Evidence Applicability" not in initial.text
    assert "Determine fitness for a bounded use" not in initial.text
    assert str(web_fixture.hidden_case_id) not in initial.text
    assert "M1B phase" not in initial.text and "future M1C" not in initial.text
    assert "Administration" not in initial.text

    configuration_page = web_fixture.client.get(f"{base}/configuration")
    evidence_page = web_fixture.client.get(f"{base}/evidence")
    assessment_page = web_fixture.client.get(f"{base}/assessment")
    history_page = web_fixture.client.get(f"{base}/history")
    for page in (configuration_page, evidence_page, assessment_page, history_page):
        assert str(web_fixture.hidden_case_id) not in page.text
    assert "Add or revise a setup" in configuration_page.text
    assert "Add Evidence" not in configuration_page.text
    assert "What we know" in evidence_page.text
    assert "Establish one setup for assessment" in evidence_page.text
    assert "Determine fitness for a bounded use" not in evidence_page.text
    assert "Value &amp; Risk" in assessment_page.text
    assert "Add or revise a setup" not in assessment_page.text
    assert "Source, history, and governance basis" in history_page.text
    assert "/review" not in history_page.text

    workspace = web_fixture.operational.practitioner_workspace(
        web_fixture.admin_session, web_fixture.visible_case_id
    )
    assert workspace is not None
    configuration = workspace.configurations[0]
    _review_commit(
        web_fixture.client,
        f"{base}/configuration/designation/review",
        {
            "configuration_id": configuration.configuration_id,
            "configuration_version_id": configuration.version_id,
            "accountable_mechanism": "governed:m1b-configuration-board",
            "effective_at": workspace.effective_at.isoformat(),
        },
    )
    established = web_fixture.operational.practitioner_workspace(
        web_fixture.admin_session, web_fixture.visible_case_id
    )
    assert established is not None
    assert established.governing_state.value == "ESTABLISHED"

    _, _, evidence_commit = _review_commit(
        web_fixture.client,
        f"{base}/evidence/review",
        {
            "configuration_id": configuration.configuration_id,
            "configuration_version_id": configuration.version_id,
            "classification": "observed",
            "source": "m1b-practitioner-source:v1",
            "provenance": "bounded practitioner capture",
            "statement": "The bounded control was observed.",
            "attention": "current",
            "effective_at": workspace.effective_at.isoformat(),
        },
    )
    assert evidence_commit.status_code == 303
    with_evidence = web_fixture.operational.practitioner_workspace(
        web_fixture.admin_session, web_fixture.visible_case_id
    )
    assert with_evidence is not None and len(with_evidence.evidence) == 1
    evidence = with_evidence.evidence[0]

    assert (
        _review_commit(
            web_fixture.client,
            f"{base}/applicability/review",
            {
                "configuration_id": configuration.configuration_id,
                "configuration_version_id": configuration.version_id,
                "evidence_choice": evidence.version_id,
                "target_choice": configuration.version_id,
                "purpose": "bounded-management",
                "assessed_scope": "exact governed Configuration",
                "outcome": "APPLICABLE",
                "rationale": "Exact Configuration material basis",
                "accountable_mechanism": "governed:m1b-applicability-board",
                "effective_at": workspace.effective_at.isoformat(),
            },
        )[2].status_code
        == 303
    )

    for lane, slug in (("VALUE", "value"), ("RISK", "risk")):
        _, _, input_commit = _review_commit(
            web_fixture.client,
            f"{base}/{slug}/input/review",
            {
                "configuration_id": configuration.configuration_id,
                "configuration_version_id": configuration.version_id,
                "purpose": "bounded-management",
                "finding": f"Independent {lane.title()} finding",
                "boundary": "exact governed Configuration",
                "uncertainties": f"{lane.title()} uncertainty remains explicit",
                "implication": f"Retain exact {lane.title()} basis",
                "provenance": f"{slug}-analysis:v1",
                "evidence_version_ids": evidence.version_id,
                "effective_at": workspace.effective_at.isoformat(),
            },
        )
        assert input_commit.status_code == 303
        current = web_fixture.operational.practitioner_workspace(
            web_fixture.admin_session, web_fixture.visible_case_id
        )
        assert current is not None
        lane_view = current.value if lane == "VALUE" else current.risk
        candidate = lane_view.candidates[0]

        _, applicability_confirmation, applicability_commit = _review_commit(
            web_fixture.client,
            f"{base}/applicability/review",
            {
                "configuration_id": configuration.configuration_id,
                "configuration_version_id": configuration.version_id,
                "evidence_choice": evidence.version_id,
                "target_choice": candidate.version_id,
                "purpose": "bounded-management",
                "assessed_scope": "exact governed Configuration",
                "outcome": "APPLICABLE",
                "rationale": f"Exact {lane.title()} material basis",
                "accountable_mechanism": "governed:m1b-applicability-board",
                "effective_at": workspace.effective_at.isoformat(),
            },
        )
        assert applicability_commit.status_code == 303
        assert evidence.label in applicability_confirmation.text
        assert candidate.label in applicability_confirmation.text
        current = web_fixture.operational.practitioner_workspace(
            web_fixture.admin_session, web_fixture.visible_case_id
        )
        assert current is not None
        applicability = next(
            item
            for item in current.applicability
            if item.content["target_version_id"] == candidate.version_id
        )

        readiness_data = {
            "input_version_id": candidate.version_id,
            "rationale": "Exact lane review complete",
            "effective_at": workspace.effective_at.isoformat(),
        }
        if lane == "VALUE":
            csrf = csrf_from(web_fixture.client.get(base).text)
            first_review = web_fixture.client.post(
                f"{base}/{slug}/readiness/review",
                data={**readiness_data, "csrf_token": csrf},
                headers={"Origin": ORIGIN},
                follow_redirects=False,
            )
            second_review = web_fixture.client.post(
                f"{base}/{slug}/readiness/review",
                data={**readiness_data, "csrf_token": csrf},
                headers={"Origin": ORIGIN},
                follow_redirects=False,
            )
            first_confirmation = web_fixture.client.get(first_review.headers["location"])
            second_confirmation = web_fixture.client.get(second_review.headers["location"])
            first_ready = web_fixture.client.post(
                first_confirmation.request.url.path.replace("/confirm/", "/commit/"),
                data={"csrf_token": csrf_from(first_confirmation.text)},
                headers={"Origin": ORIGIN},
                follow_redirects=False,
            )
            assert first_ready.status_code == 303
            stale_ready = web_fixture.client.post(
                second_confirmation.request.url.path.replace("/confirm/", "/commit/"),
                data={"csrf_token": csrf_from(second_confirmation.text)},
                headers={"Origin": ORIGIN},
            )
            assert stale_ready.status_code == 409
            assert "Exact analytical state changed" in stale_ready.text
        else:
            assert (
                _review_commit(
                    web_fixture.client,
                    f"{base}/{slug}/readiness/review",
                    readiness_data,
                )[2].status_code
                == 303
            )
        fitness_data = {
            "configuration_id": configuration.configuration_id,
            "configuration_version_id": configuration.version_id,
            "input_version_id": candidate.version_id,
            "use_context": "bounded-operation",
            "purpose": "bounded-management",
            "outcome": "SUPPORTABLE",
            "decision_limiting": "FALSE",
            "indeterminate_treatment": "",
            "rationale": "Exact material basis is supportable",
            "accountable_mechanism": f"governed:m1b-{slug}-fitness",
            "evidence_version_id": evidence.version_id,
            "applicability_version_id": applicability.version_id,
            "evidence_role": "material support",
            "required_support": "TRUE",
            "claimed_scope": "exact governed Configuration",
            "effective_at": workspace.effective_at.isoformat(),
        }
        _, fitness_confirmation, fitness_commit = _review_commit(
            web_fixture.client,
            f"{base}/{slug}/fitness/review",
            fitness_data,
        )
        assert fitness_commit.status_code == 303
        assert "SUPPORTABLE" in fitness_confirmation.text
        assert "Required Support" in fitness_confirmation.text
        assert "TRUE" in fitness_confirmation.text
        current = web_fixture.operational.practitioner_workspace(
            web_fixture.admin_session, web_fixture.visible_case_id
        )
        assert current is not None
        lane_view = current.value if lane == "VALUE" else current.risk
        fitness = next(
            item for item in lane_view.fitness if item.content["outcome"] == "SUPPORTABLE"
        )
        assert fitness.content["decision_limiting"] is False
        assert fitness.content["material_evidence"][0]["required_support"] is True
        if lane == "RISK":
            blocked_data = {
                **fitness_data,
                "outcome": "BLOCKED",
                "decision_limiting": "TRUE",
                "indeterminate_treatment": "Escalate unresolved lane evidence",
                "rationale": "Exact Risk evidence remains decision-limiting",
                "required_support": "FALSE",
            }
            _, blocked_confirmation, blocked_commit = _review_commit(
                web_fixture.client,
                f"{base}/{slug}/fitness/review",
                blocked_data,
            )
            assert blocked_commit.status_code == 303
            assert "BLOCKED" in blocked_confirmation.text
            assert "Escalate unresolved lane evidence" in blocked_confirmation.text
            current = web_fixture.operational.practitioner_workspace(
                web_fixture.admin_session, web_fixture.visible_case_id
            )
            assert current is not None
            blocked = next(
                item for item in current.risk.fitness if item.content["outcome"] == "BLOCKED"
            )
            assert blocked.content["input_version_id"] == candidate.version_id
            assert blocked.content["decision_limiting"] is True
            assert blocked.content["indeterminate_treatment"] == (
                "Escalate unresolved lane evidence"
            )
            assert blocked.content["material_evidence"][0]["required_support"] is False
            assessment = web_fixture.client.get(f"{base}/assessment")
            fitness_choices = "".join(
                part.split("</select>", maxsplit=1)[0]
                for part in assessment.text.split('<select name="fitness_version_id"')[1:]
            )
            assert f'value="{fitness.version_id}"' in fitness_choices
            assert f'value="{blocked.version_id}"' not in fitness_choices
            overview_before_selection = web_fixture.client.get(base)
            assert "Assess Risk" in overview_before_selection.text
            assert "Required for the action you chose" not in overview_before_selection.text
            assert "Risk assessment blocked for a recorded use" not in (
                overview_before_selection.text
            )

            selection_count = web_fixture.operational.domain_store.count_rows(
                "input_acceptance_versions"
            )
            rejected = web_fixture.client.post(
                f"{base}/{slug}/selection/review",
                data={
                    "csrf_token": csrf_from(assessment.text),
                    "configuration_id": configuration.configuration_id,
                    "configuration_version_id": configuration.version_id,
                    "input_version_id": candidate.version_id,
                    "fitness_version_id": blocked.version_id,
                    "material_applicability_version_ids": applicability.version_id,
                },
                headers={"Origin": ORIGIN},
            )
            assert rejected.status_code == 409
            assert "selected fitness determination is not SUPPORTABLE" in rejected.text
            assert blocked.version_id not in rejected.text
            assert (
                web_fixture.operational.domain_store.count_rows("input_acceptance_versions")
                == selection_count
            )
        assert (
            _review_commit(
                web_fixture.client,
                f"{base}/{slug}/selection/review",
                {
                    "configuration_id": configuration.configuration_id,
                    "configuration_version_id": configuration.version_id,
                    "input_version_id": candidate.version_id,
                    "fitness_version_id": fitness.version_id,
                    "use_context": "bounded-operation",
                    "purpose": "bounded-management",
                    "rationale": f"Exact {lane.title()} selection",
                    "accountable_mechanism": f"governed:m1b-{slug}-acceptance",
                    "material_applicability_version_ids": applicability.version_id,
                    "effective_at": workspace.effective_at.isoformat(),
                },
            )[2].status_code
            == 303
        )

    completed = web_fixture.operational.practitioner_workspace(
        web_fixture.admin_session, web_fixture.visible_case_id
    )
    assert completed is not None
    assert completed.value.selection_state.value == "ESTABLISHED"
    assert completed.risk.selection_state.value == "ESTABLISHED"
    assert {item.content["outcome"] for item in completed.value.fitness} == {"SUPPORTABLE"}
    assert {item.content["outcome"] for item in completed.risk.fitness} == {
        "SUPPORTABLE",
        "BLOCKED",
    }
    assert {item.record_id for item in completed.value.fitness}.isdisjoint(
        item.record_id for item in completed.risk.fitness
    )
    assert (
        completed.value.selections[0].content["input_version_id"]
        != completed.risk.selections[0].content["input_version_id"]
    )
    applicability_labels = {
        "Applicable — m1b-practitioner-source:v1 → visible",
        ("Applicable — m1b-practitioner-source:v1 → Value analysis: Independent Value finding"),
        ("Applicable — m1b-practitioner-source:v1 → Risk analysis: Independent Risk finding"),
    }
    assert {item.label for item in completed.applicability} == applicability_labels
    assert all(
        item.label.startswith("Value fitness — ")
        and "Independent Value finding" in item.label
        and "Independent Risk finding" not in item.label
        for item in completed.value.fitness
    )
    assert all(
        item.label.startswith("Risk fitness — ")
        and "Independent Risk finding" in item.label
        and "Independent Value finding" not in item.label
        for item in completed.risk.fitness
    )
    assert completed.value.selections[0].label == (
        "Value assessment selected — Independent Value finding"
    )
    assert completed.risk.selections[0].label == (
        "Risk assessment selected — Independent Risk finding"
    )
    page = web_fixture.client.get(f"{base}/assessment")
    evidence_page = web_fixture.client.get(f"{base}/evidence")
    history_page = web_fixture.client.get(f"{base}/history")
    for label in applicability_labels:
        assert label in evidence_page.text
        assert label in history_page.text
        assert label in page.text
    for label in (
        "Value fitness — Supportable — Independent Value finding",
        "Risk fitness — Supportable — Independent Risk finding",
        "Risk fitness — Blocked — Independent Risk finding",
        "Value assessment selected — Independent Value finding",
        "Risk assessment selected — Independent Risk finding",
    ):
        assert label in history_page.text
    assert "shared score" in page.text
    assert "It does not integrate them" in page.text
    assert "M1C" not in page.text and "future milestone" not in page.text
    overview = web_fixture.client.get(base)
    assert "Risk assessment blocked for a recorded use" not in overview.text
    assert "Risk assessment not yet selected" not in overview.text
    assert "Choose the task that fits the work you are doing now." in overview.text
    assert "not a ranking, recommendation, or priority" not in overview.text


def test_m1b_stale_configuration_successor_stops_and_duplicate_intent_is_idempotent(
    web_fixture: WebFixture,
) -> None:
    _grant_m1b(web_fixture)
    assert login(web_fixture.client)[1].status_code == 303
    case_id = str(web_fixture.visible_case_id)
    base = f"/cases/{case_id}"
    view = web_fixture.operational.practitioner_workspace(
        web_fixture.admin_session, web_fixture.visible_case_id
    )
    assert view is not None
    configuration = view.configurations[0]
    _reviewed, confirmation, first = _review_commit(
        web_fixture.client,
        f"{base}/configuration/review",
        {
            "configuration_choice": configuration.version_id,
            "relationship_reason": "bounded successor",
            "purpose": "candidate",
            "system": "visible successor",
            "intended_use": "bounded M1B",
            "effective_at": view.effective_at.isoformat(),
        },
    )
    assert first.status_code == 303
    count = web_fixture.operational.domain_store.count_rows("managed_configuration_versions")
    duplicate = web_fixture.client.post(
        confirmation.request.url.path.replace("/confirm/", "/commit/"),
        data={"csrf_token": csrf_from(confirmation.text)},
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    assert duplicate.status_code == 303
    assert (
        web_fixture.operational.domain_store.count_rows("managed_configuration_versions") == count
    )

    stale_review = web_fixture.client.post(
        f"{base}/configuration/review",
        data={
            "csrf_token": csrf_from(web_fixture.client.get(f"{base}/configuration").text),
            "configuration_choice": configuration.version_id,
            "relationship_reason": "stale attempted successor",
            "purpose": "candidate",
            "system": "stale candidate",
            "intended_use": "must stop",
            "effective_at": view.effective_at.isoformat(),
        },
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    assert stale_review.status_code == 409
    assert "Selected source is unavailable" in stale_review.text
    assert "no longer one exact visible Version" in stale_review.text
    assert (
        web_fixture.operational.domain_store.count_rows("managed_configuration_versions") == count
    )


def test_m1b_case_authority_gap_and_access_error_boundaries(web_fixture: WebFixture) -> None:
    _grant_m1b(web_fixture)
    grant(web_fixture, Permission.CASE_READ, "read")
    assert login(web_fixture.client)[1].status_code == 303
    role_count = web_fixture.operational.domain_store.count_rows("role_assignment_versions")
    new_page = web_fixture.client.get("/cases/new")
    reviewed = web_fixture.client.post(
        "/cases/new/review",
        data={
            "csrf_token": csrf_from(new_page.text),
            "title": "M1B exact browser-created Case",
            "effective_at": web_fixture.now().isoformat(),
        },
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    confirmation = web_fixture.client.get(reviewed.headers["location"])
    created = web_fixture.client.post(
        confirmation.request.url.path.replace("/confirm/", "/commit/"),
        data={"csrf_token": csrf_from(confirmation.text)},
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    assert created.status_code == 303
    assert (
        "M1B exact browser-created Case" in web_fixture.client.get(created.headers["location"]).text
    )
    assert web_fixture.operational.domain_store.count_rows("role_assignment_versions") == role_count

    case_id = str(web_fixture.visible_case_id)
    base = f"/cases/{case_id}"
    view = web_fixture.operational.practitioner_workspace(
        web_fixture.admin_session, web_fixture.visible_case_id
    )
    assert view is not None
    configuration = view.configurations[0]
    _review_commit(
        web_fixture.client,
        f"{base}/configuration/designation/review",
        {
            "configuration_id": configuration.configuration_id,
            "configuration_version_id": configuration.version_id,
            "accountable_mechanism": "governed:m1b-configuration-board",
            "effective_at": view.effective_at.isoformat(),
        },
    )
    evidence_actions = web_fixture.client.get(f"{base}/evidence").text
    assert "Add a requirement or authority source" in evidence_actions
    assert "Record an unresolved requirement or authority question" in evidence_actions
    assert "Review how information applies" not in evidence_actions
    assert (
        _review_commit(
            web_fixture.client,
            f"{base}/authority/review",
            {
                "configuration_id": configuration.configuration_id,
                "configuration_version_id": configuration.version_id,
                "category": "policy",
                "source": "authority-register:v1",
                "scope": "bounded-use",
                "requirement": "Human oversight is required.",
                "provenance": "approved policy register",
                "effective_at": view.effective_at.isoformat(),
            },
        )[2].status_code
        == 303
    )
    assert (
        _review_commit(
            web_fixture.client,
            f"{base}/authority-gap/review",
            {
                "configuration_id": configuration.configuration_id,
                "configuration_version_id": configuration.version_id,
                "question_id": "m1b-authority-question",
                "question": "Who may authorize the bounded use?",
                "scope": "bounded-use",
                "rationale": "The exact authorization source remains unresolved.",
                "provenance": "practitioner authority review",
                "effective_at": view.effective_at.isoformat(),
            },
        )[2].status_code
        == 303
    )
    current = web_fixture.operational.practitioner_workspace(
        web_fixture.admin_session, web_fixture.visible_case_id
    )
    assert current is not None
    assert len(current.authority) == 1
    assert len(current.authority_gaps) == 1
    assert current.authority_gaps[0].state == "UNRESOLVED"
    attention = web_fixture.client.get(base)
    assert "Unresolved authority question" in attention.text
    assert f"{base}/evidence" in attention.text

    applicability_count = web_fixture.operational.domain_store.count_rows(
        "evidence_applicability_versions"
    )
    tampered = web_fixture.client.post(
        f"{base}/applicability/review",
        data={
            "csrf_token": csrf_from(web_fixture.client.get(f"{base}/evidence").text),
            "evidence_choice": str(web_fixture.hidden_case_id),
            "target_choice": configuration.version_id,
        },
        headers={"Origin": ORIGIN},
    )
    assert tampered.status_code == 409
    assert "Selected source is unavailable" in tampered.text
    assert str(web_fixture.hidden_case_id) not in tampered.text
    assert (
        web_fixture.operational.domain_store.count_rows("evidence_applicability_versions")
        == applicability_count
    )

    grant(
        web_fixture,
        Permission.COMMAND,
        "evidence.create",
        ScopeType.CASE,
        web_fixture.visible_case_id,
        AccessEffect.DENY,
    )
    denied = _review_commit(
        web_fixture.client,
        f"{base}/evidence/review",
        {
            "configuration_id": configuration.configuration_id,
            "configuration_version_id": configuration.version_id,
            "classification": "observed",
            "source": "denied-source",
            "provenance": "must not commit",
            "statement": "Must remain absent.",
            "effective_at": view.effective_at.isoformat(),
        },
    )[2]
    assert denied.status_code == 403
    assert "Software access or exact visibility denied" in denied.text
    assert "accountability or substantive authority" in denied.text


def test_m1b_governing_configuration_conflict_is_explicit_without_implicit_winner(
    web_fixture: WebFixture,
) -> None:
    _grant_m1b(web_fixture)
    assert login(web_fixture.client)[1].status_code == 303
    case_id = str(web_fixture.visible_case_id)
    base = f"/cases/{case_id}"
    initial = web_fixture.operational.practitioner_workspace(
        web_fixture.admin_session, web_fixture.visible_case_id
    )
    assert initial is not None
    first = initial.configurations[0]
    _review_commit(
        web_fixture.client,
        f"{base}/configuration/designation/review",
        {
            "configuration_id": first.configuration_id,
            "configuration_version_id": first.version_id,
            "accountable_mechanism": "governed:first-designation",
            "effective_at": initial.effective_at.isoformat(),
        },
    )
    assert (
        _review_commit(
            web_fixture.client,
            f"{base}/configuration/review",
            {
                "purpose": "candidate",
                "system": "second exact candidate",
                "intended_use": "explicit conflict oracle",
                "effective_at": initial.effective_at.isoformat(),
            },
        )[2].status_code
        == 303
    )
    with_second = web_fixture.operational.practitioner_workspace(
        web_fixture.admin_session, web_fixture.visible_case_id
    )
    assert with_second is not None
    second = next(
        item
        for item in with_second.configurations
        if item.configuration_id != first.configuration_id
    )
    _review_commit(
        web_fixture.client,
        f"{base}/configuration/designation/review",
        {
            "configuration_id": second.configuration_id,
            "configuration_version_id": second.version_id,
            "accountable_mechanism": "governed:second-designation",
            "effective_at": initial.effective_at.isoformat(),
        },
    )
    conflicted = web_fixture.operational.practitioner_workspace(
        web_fixture.admin_session, web_fixture.visible_case_id
    )
    assert conflicted is not None
    assert conflicted.governing_state.value == "CONFLICT"
    assert set(conflicted.governing_configuration_version_ids) == {
        first.version_id,
        second.version_id,
    }
    page = web_fixture.client.get(f"{base}/configuration")
    assert "The assessment setup is conflicted" in page.text
    assert "More than one setup claims to be the current assessment basis" in page.text
    overview = web_fixture.client.get(base)
    assert "Why this blocks work and how to resolve it" in overview.text
    assert "PAIM cannot choose" in overview.text
