from __future__ import annotations

import pytest
from playwright.sync_api import Browser

from paim.operational import Permission
from tests.browser.test_m1a_browser import live_server
from tests.integration.test_gate8_slice_h0_prerequisites import (
    NOW,
    establish_authority,
    prepare_permissions,
)
from tests.integration.test_gate8_slice_h_ui import _use_fixture_clock
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
        page.get_by_label("What should people recognize this Case as?").fill(
            "Harborlight Assist - disposable browser proof"
        )
        page.get_by_label("What AI use are you considering?").fill(
            "small-business lending assistance with accountable human judgment."
        )
        page.get_by_label("What setup or scope should this Case begin with?").fill(
            "Scenario A assistance only; no autonomous lending Decision."
        )
        page.get_by_role("button", name="Review Case start").click()
        assert page.get_by_role("heading", name="Start this Case?").is_visible()
        assert page.get_by_text("does not grant Value, Risk, Decision").is_visible()
        page.get_by_role("button", name="Start Case", exact=True).click()
        assert "/start/commit/" not in page.url, page.content()

        assert page.get_by_role(
            "heading", name="Harborlight Assist - disposable browser proof"
        ).is_visible()
        assert page.get_by_text(
            "small-business lending assistance with accountable human judgment."
        ).is_visible()
        assert page.get_by_role("heading", name="Potential Value").is_visible()
        assert page.get_by_role("heading", name="Risks and safeguards").is_visible()
        page.reload()
        assert page.get_by_role(
            "heading", name="Harborlight Assist - disposable browser proof"
        ).is_visible()
        page.get_by_role("link", name="Open History & decisions").click()
        assert page.get_by_role("heading", name="History & decisions").is_visible()
        assert page.get_by_text("What happened, what was known, and why").is_visible()
        context.close()
