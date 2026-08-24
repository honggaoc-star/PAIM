from __future__ import annotations

import pytest
from playwright.sync_api import Browser

from paim.operational import Permission, ScopeType
from tests.browser.test_m1a_browser import live_server
from tests.browser.test_m1b_browser import (
    test_m1b_browser_exact_evidence_and_independent_lane_path as establish_m1b_browser_path,
)
from tests.web_support import TOKEN, WebFixture, grant


@pytest.mark.browser
def test_m1c_no_javascript_exact_integration_review(
    web_fixture: WebFixture, browser: Browser
) -> None:
    establish_m1b_browser_path(web_fixture, browser)
    for action in ("case.lifecycle.advance", "integration.create"):
        grant(
            web_fixture,
            Permission.COMMAND,
            action,
            ScopeType.CASE,
            web_fixture.visible_case_id,
        )

    with live_server(web_fixture) as origin:
        context = browser.new_context(java_script_enabled=False)
        page = context.new_page()
        page.goto(f"{origin}/login")
        page.get_by_label("Principal ID").fill("principal:web-practitioner")
        page.get_by_label("Protected credential").fill(TOKEN)
        page.get_by_role("button", name="Sign in").click()
        page.goto(f"{origin}/cases/{web_fixture.visible_case_id}/decision")
        assert page.get_by_role("heading", name="Integration, Boundary, and Decision").is_visible()
        assert page.get_by_text("Independent Value finding", exact=True).is_visible()
        assert page.get_by_text("Independent Risk finding", exact=True).is_visible()
        assert page.get_by_text("No automatic synthesis:").is_visible()

        for expected in (
            "Configuration Defined",
            "Evidence Analysis",
            "Ready For Integration",
        ):
            assert page.get_by_text(f"Exact next state: {expected}").is_visible()
            page.get_by_role("button", name="Review lifecycle transition").click()
            page.locator("form[data-submit-lock] button").click()

        form = page.locator("details").filter(has_text="Record explicit Integration")
        form.locator("summary").click()
        form.get_by_label("Integration status").select_option("completed")
        form.get_by_label("Reinforcing effects").fill("Both exact lanes support bounded use.")
        form.get_by_label("Conflicts").fill("No conflict is silently resolved.")
        form.get_by_label("Tradeoffs").fill("The Risk constraint remains explicit.")
        form.get_by_label("Remaining uncertainty").fill("Recorded uncertainty remains.")
        form.get_by_label("Proposed judgment").fill("Continue within an explicit Boundary.")
        form.get_by_label("Accountable mechanism").fill("governed:m1c-browser-board")
        form.get_by_label("Integration rationale").fill("Exact lane basis supports integration.")
        form.get_by_role("button", name="Review explicit Integration").click()
        assert page.get_by_role("heading", name="Review and confirm this action").is_visible()
        assert page.get_by_text("Independent Value finding", exact=False).is_visible()
        page.locator("form[data-submit-lock] button").click()
        assert page.get_by_text("Integration — Value:", exact=False).first.is_visible()
        context.close()
