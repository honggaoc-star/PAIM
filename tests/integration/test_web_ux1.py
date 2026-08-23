from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from typing import Any

import pytest
from fastapi.testclient import TestClient

from paim.application.practitioner import PractitionerQueryService, ReadState
from paim.integrity import RecordId
from paim.operational import AccessEffect, Permission, ScopeType
from tests.web_support import ORIGIN, WebFixture, csrf_from, grant, login


def _grant_ux1(fixture: WebFixture) -> None:
    grant(fixture, Permission.CONFIGURATION_READ, "read")
    for action in (
        "configuration.create",
        "configuration.designate",
        "value-input.create",
        "value-input.select",
        "risk-input.create",
        "risk-input.select",
        "integration.create",
    ):
        grant(
            fixture,
            Permission.COMMAND,
            action,
            ScopeType.CASE,
            fixture.visible_case_id,
        )


def _review_commit(client: TestClient, path: str, data: dict[str, str]) -> None:
    base = "/".join(path.split("/")[:3])
    reviewed = client.post(
        path,
        data={**data, "csrf_token": csrf_from(client.get(base).text)},
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    assert reviewed.status_code == 303, reviewed.text
    confirmation = client.get(reviewed.headers["location"])
    committed = client.post(
        confirmation.request.url.path.replace("/confirm/", "/commit/"),
        data={"csrf_token": csrf_from(confirmation.text)},
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    assert committed.status_code == 303, committed.text


def _create_setup(
    fixture: WebFixture, *, purpose: str, system: str, intended_use: str
) -> tuple[str, str]:
    case_id = str(fixture.visible_case_id)
    current = fixture.operational.practitioner_workspace(
        fixture.admin_session, fixture.visible_case_id
    )
    assert current is not None
    _review_commit(
        fixture.client,
        f"/cases/{case_id}/configuration/review",
        {
            "purpose": purpose,
            "system": system,
            "intended_use": intended_use,
            "effective_at": current.effective_at.isoformat(),
        },
    )
    updated = fixture.operational.practitioner_workspace(
        fixture.admin_session, fixture.visible_case_id
    )
    assert updated is not None
    setup = next(item for item in updated.configurations if item.content.get("system") == system)
    return setup.configuration_id, setup.version_id


def _establish_proposed_setup(fixture: WebFixture) -> tuple[str, str]:
    configuration_id, version_id = _create_setup(
        fixture,
        purpose="candidate",
        system="Proposed eight-week pilot",
        intended_use="Assist document organization; no automated lending action",
    )
    workspace = fixture.operational.practitioner_workspace(
        fixture.admin_session, fixture.visible_case_id
    )
    assert workspace is not None
    _review_commit(
        fixture.client,
        f"/cases/{fixture.visible_case_id}/configuration/designation/review",
        {
            "configuration_id": configuration_id,
            "configuration_version_id": version_id,
            "accountable_mechanism": "governed:ux1-setup-review",
            "effective_at": workspace.effective_at.isoformat(),
        },
    )
    return configuration_id, version_id


def test_ux1_orientation_keeps_proposed_governing_setup_separate_from_operation(
    web_fixture: WebFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    _grant_ux1(web_fixture)
    assert login(web_fixture.client)[1].status_code == 303
    _create_setup(
        web_fixture,
        purpose="fallback",
        system="Manual process",
        intended_use="Human organization and drafting for comparison",
    )
    proposed_id, proposed_version_id = _establish_proposed_setup(web_fixture)

    permission_checks: set[str] = set()
    original: Callable[..., bool] = web_fixture.operational.operational_store.permission_allowed

    def observed_permission(*args: Any, **kwargs: Any) -> bool:
        action = kwargs.get("action")
        if not isinstance(action, str) and len(args) >= 3:
            action = args[2]
        if isinstance(action, str):
            permission_checks.add(action)
        return original(*args, **kwargs)

    monkeypatch.setattr(
        web_fixture.operational.operational_store,
        "permission_allowed",
        observed_permission,
    )
    record_count = web_fixture.operational.domain_store.count_rows("records")
    page = web_fixture.client.get(f"/cases/{web_fixture.visible_case_id}")
    assert page.status_code == 200
    assert web_fixture.operational.domain_store.count_rows("records") == record_count

    view = web_fixture.operational.practitioner_workspace(
        web_fixture.admin_session, web_fixture.visible_case_id
    )
    assert view is not None
    proposed = next(item for item in view.configurations if item.configuration_id == proposed_id)
    comparison = next(
        item for item in view.configurations if item.content.get("system") == "Manual process"
    )
    assert proposed.is_governing
    assert proposed.practitioner_label == "Proposed setup under review"
    assert "does not authorize or start operation" in proposed.context_summary
    assert comparison.practitioner_label == "Comparison option"
    assert not comparison.is_governing

    available = {item.key for item in view.available_work}
    assert available == {"review-known", "value-assessment", "risk-assessment"}
    assert view.required_prerequisite is None
    assert "Assess Value" in page.text and "Assess Risk" in page.text
    assert "not a ranking" in page.text
    assert "Authorized setup" not in page.text
    assert "Operating setup" not in page.text
    assert "Current operating process" not in page.text
    assert "Current attention" not in page.text
    assert "Software access" not in page.text
    assert "Exact governed context" not in page.text
    assert proposed_id not in page.text
    assert proposed_version_id not in page.text
    assert {"configuration.designate", "value-input.create", "risk-input.create"} <= (
        permission_checks
    )
    assert "attention" not in view.__dataclass_fields__
    assert "next_task" not in view.__dataclass_fields__


def test_ux1_unique_prerequisite_is_distinct_from_peer_work_and_unresolved_conditions(
    web_fixture: WebFixture,
) -> None:
    _grant_ux1(web_fixture)
    assert login(web_fixture.client)[1].status_code == 303
    _establish_proposed_setup(web_fixture)
    view = web_fixture.operational.practitioner_workspace(
        web_fixture.admin_session, web_fixture.visible_case_id
    )
    assert view is not None

    value_selected = replace(view.value, selection_state=ReadState.ESTABLISHED)
    available, required, unresolved = PractitionerQueryService._orientation_items(
        case_id=web_fixture.visible_case_id,
        governing_state=ReadState.ESTABLISHED,
        evidence=view.evidence,
        authority_gaps=view.authority_gaps,
        applicability=view.applicability,
        value=value_selected,
        risk=view.risk,
        decision=view.decision,
        action_access={
            "risk-input.create": True,
            "risk-input.select": True,
            "integration.create": True,
        },
    )

    assert required is not None
    assert required.key == "risk-assessment"
    assert required.exception is not None
    assert required.exception.intended_action == "Record the management judgment"
    assert {item.key for item in available} == {"review-known"}
    assert all(item.key != required.key for item in unresolved)


def test_ux1_hidden_governing_setup_fails_closed_without_orientation_leak(
    web_fixture: WebFixture,
) -> None:
    _grant_ux1(web_fixture)
    assert login(web_fixture.client)[1].status_code == 303
    hidden_id, hidden_version_id = _establish_proposed_setup(web_fixture)
    grant(
        web_fixture,
        Permission.CONFIGURATION_READ,
        "read",
        ScopeType.CONFIGURATION,
        RecordId.parse(hidden_id),
        AccessEffect.DENY,
    )

    records_before = web_fixture.operational.domain_store.count_rows("records")
    view = web_fixture.operational.practitioner_workspace(
        web_fixture.admin_session, web_fixture.visible_case_id
    )
    assert view is not None
    assert view.governing_state is ReadState.INACCESSIBLE
    assert view.governing_configuration_version_ids == ()
    assert view.required_prerequisite is not None
    assert view.required_prerequisite.exception is not None
    assert "restore access" in view.required_prerequisite.exception.resolution

    page = web_fixture.client.get(f"/cases/{web_fixture.visible_case_id}")
    assert page.status_code == 200
    assert "assessment setup is not visible in this session" in page.text
    assert "Proposed eight-week pilot" not in page.text
    assert "Proposed setup under review" not in page.text
    assert hidden_id not in page.text
    assert hidden_version_id not in page.text
    assert "current attention item" not in page.text
    assert web_fixture.operational.domain_store.count_rows("records") == records_before
