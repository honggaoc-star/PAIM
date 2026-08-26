from __future__ import annotations

from datetime import timedelta

import pytest
from playwright.sync_api import Browser

from paim.operational import Permission, PrincipalStatus, ScopeType
from tests.browser.test_m1a_browser import live_server
from tests.integration.test_gate8_slice_b_case_continuity import RECORDED
from tests.integration.test_gate8_slice_c_assessment_review import (
    fixture as slice_c_fixture,
)
from tests.integration.test_gate8_slice_h0_prerequisites import (
    NOW,
    establish_authority,
    prepare_permissions,
)
from tests.integration.test_gate8_slice_h_ui import (
    _establish_value_work,
    _grant_all_case_sources,
    _use_fixture_clock,
)
from tests.web_support import TOKEN, WebFixture, grant


@pytest.mark.browser
def test_slice_h_disposable_harborlight_case_start_survives_no_javascript(
    web_fixture: WebFixture, browser: Browser
) -> None:
    """A real browser crosses the production H0 command without client-side continuity."""

    web_fixture.now.value = NOW
    _use_fixture_clock(web_fixture)
    prepare_permissions(web_fixture)
    grant(web_fixture, Permission.OPERATIONAL_ADMIN, "access.manage")
    establish_authority(
        web_fixture,
        web_fixture.operational._case_continuity,  # type: ignore[attr-defined]
    )

    with live_server(web_fixture) as origin:
        context = browser.new_context(java_script_enabled=False)
        page = context.new_page()
        page.goto(f"{origin}/login")
        page.get_by_label("Principal ID").fill("principal:web-practitioner")
        page.get_by_label("Protected credential").fill(TOKEN)
        page.get_by_role("button", name="Sign in").click()
        assert page.url == f"{origin}/home", page.content()
        assert page.get_by_text("Nothing currently needs your attention.").is_visible()

        page.get_by_role("link", name="Cases", exact=True).click()
        page.get_by_role("link", name="Start a Case").click()
        page.get_by_label("Case name").fill("Harborlight Assist - disposable browser proof")
        page.locator("#bounded-use").fill(
            "small-business lending assistance with accountable human judgment."
        )
        page.get_by_label("Decision or management question").fill(
            "Should Harborlight use bounded AI assistance in lending review?"
        )
        page.get_by_label("Starting scope or setup").fill(
            "Scenario A assistance only; no autonomous lending Decision."
        )
        page.get_by_role("button", name="Review Case start").click()
        assert page.get_by_role("heading", name="Start this Case?").is_visible()
        assert page.get_by_text("does not complete Value or Risk assessments").is_visible()
        assert page.get_by_text(
            "Should Harborlight use bounded AI assistance in lending review?"
        ).is_visible()
        page.get_by_role("button", name="Start Case", exact=True).click()
        assert "/start/commit/" not in page.url, page.content()

        assert page.get_by_role(
            "heading", name="Harborlight Assist - disposable browser proof"
        ).is_visible()
        assert page.get_by_text(
            "small-business lending assistance with accountable human judgment."
        ).is_visible()
        assert page.get_by_text(
            "Should Harborlight use bounded AI assistance in lending review?"
        ).is_visible()
        assert page.get_by_role("heading", name="Potential Value").is_visible()
        assert page.get_by_role("heading", name="Risks and safeguards").is_visible()
        page.reload()
        assert page.get_by_role(
            "heading", name="Harborlight Assist - disposable browser proof"
        ).is_visible()
        page.get_by_role("link", name="Open History & decisions").click()
        assert page.get_by_role("heading", name="History & decisions").is_visible()
        assert page.get_by_role("heading", name="What happened?").is_visible()
        assert page.get_by_text("Advanced time reconstruction and audit sources").is_visible()
        context.close()


@pytest.mark.browser
def test_slice_h_value_action_is_practitioner_specific_in_a_real_browser(
    web_fixture: WebFixture, browser: Browser
) -> None:
    """A real browser presents and confirms the revised Value judgment."""

    fixture = slice_c_fixture(web_fixture.operational.domain_store, "slice-h-browser-value")
    work = _establish_value_work(web_fixture, fixture, "slice-h-browser-value-work")
    case_id = fixture.opened.facts.case_id
    configuration_id = fixture.opened.facts.configuration_id
    web_fixture.now.value = RECORDED + timedelta(seconds=10)
    _use_fixture_clock(web_fixture)
    web_fixture.operational.provision_principal(
        web_fixture.admin_session,
        principal_id="principal:web-practitioner",
        token=TOKEN,
        actor_id=fixture.actor_a,
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

    with live_server(web_fixture) as origin:
        context = browser.new_context(java_script_enabled=False)
        page = context.new_page()
        page.goto(f"{origin}/login")
        page.get_by_label("Principal ID").fill("principal:web-practitioner")
        page.get_by_label("Protected credential").fill(TOKEN)
        page.get_by_role("button", name="Sign in").click()
        page.goto(f"{origin}/cases/{case_id}/tasks/{work.version_id}")
        page.get_by_role("link", name="Continue to this action").click()

        assert page.get_by_role("heading", name="Finish the Value assessment").is_visible()
        assert page.get_by_label("What improvement or benefit are we expecting?").is_visible()
        assert page.get_by_label("What could go wrong or require attention?").count() == 0
        page.get_by_label("What improvement or benefit are we expecting?").fill(
            "Faster review preparation for accountable lending staff."
        )
        page.get_by_label(
            "How is this AI use expected to contribute, and where might it not?"
        ).fill("It may organize evidence; it does not make the lending decision.")
        page.get_by_label("What information supports or limits that expectation?").fill(
            "The exact visible Harborlight information basis."
        )
        page.get_by_label("What important uncertainty should the decision maker understand?").fill(
            "Benefit may vary with case complexity."
        )
        page.get_by_label("What does this imply for the management decision?").fill(
            "Consider the bounded benefit alongside the separate Risk assessment."
        )
        page.get_by_label("Why is this Value assessment ready for independent review?").fill(
            "The expected benefit, limits, information, and uncertainty are explicit."
        )
        page.get_by_role("button", name="Review the Value assessment").click()

        assert page.get_by_role("heading", name="Record this Value assessment?").is_visible()
        assert page.get_by_text("What this does not change:", exact=True).is_visible()
        assert page.get_by_text(
            "Risk, suitability, reliance, and the management decision are not changed."
        ).is_visible()
        assert page.get_by_text("Faster review preparation").is_visible()
        context.close()
