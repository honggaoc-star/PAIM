from __future__ import annotations

import pytest
from playwright.sync_api import Browser, Page

from paim.operational import Permission, ScopeType
from tests.browser.test_m1a_browser import live_server
from tests.web_support import TOKEN, WebFixture, grant


def _grant_browser_path(fixture: WebFixture) -> None:
    grant(fixture, Permission.CONFIGURATION_READ, "read")
    for action in (
        "configuration.designate",
        "evidence.create",
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


def _confirm(page: Page) -> None:
    page.get_by_role("button", name="Confirm and revalidate").click()
    page.wait_for_load_state("domcontentloaded")


@pytest.mark.browser
def test_m1b_browser_exact_evidence_and_independent_lane_path(
    web_fixture: WebFixture, browser: Browser
) -> None:
    _grant_browser_path(web_fixture)
    with live_server(web_fixture) as origin:
        page = browser.new_page()
        page.goto(f"{origin}/login")
        page.get_by_label("Principal ID").fill("principal:web-practitioner")
        page.get_by_label("Protected credential").fill(TOKEN)
        page.get_by_role("button", name="Sign in").click()
        page.get_by_role("link", name="Cases", exact=True).click()
        page.get_by_role("link", name="Visible governed service").click()
        assert page.get_by_role("heading", name="Overview").is_visible()
        assert "Protected hidden service" not in page.content()
        assert str(web_fixture.hidden_case_id) not in page.content()

        page.get_by_label("Exact accountable mechanism").fill("governed:m1b-browser-configuration")
        page.get_by_role("button", name="Review governing designation").click()
        _confirm(page)
        assert "Governing Configuration: ESTABLISHED" in page.content()

        evidence_form = page.locator("details").filter(has_text="Create Evidence")
        evidence_form.locator("summary").click()
        evidence_form.get_by_label("Source").fill("browser-observation:v1")
        evidence_form.get_by_label("Provenance").fill("bounded browser capture")
        evidence_form.get_by_label("Statement").fill("The exact control was observed.")
        evidence_form.get_by_role("button", name="Review Evidence").click()
        assert page.get_by_role("heading", name="Confirm exact action").is_visible()
        _confirm(page)
        workspace = web_fixture.operational.practitioner_workspace(
            web_fixture.admin_session, web_fixture.visible_case_id
        )
        assert workspace is not None
        evidence = workspace.evidence[0]

        for lane_name, slug in (("Value", "value"), ("Risk", "risk")):
            lane = page.locator("section.lane").filter(
                has=page.get_by_role("heading", name=lane_name)
            )
            create = lane.locator("details").filter(has_text=f"Create a {lane_name} Input")
            create.locator("summary").click()
            create.get_by_label("Purpose").fill("bounded-management")
            create.get_by_label("Finding").fill(f"Independent {lane_name} finding")
            create.get_by_label("Boundary of analysis").fill("exact governed Configuration")
            create.get_by_label("Uncertainties, one per line").fill(
                f"{lane_name} uncertainty remains explicit"
            )
            create.get_by_label("Management implication").fill(f"Retain exact {lane_name} basis")
            create.get_by_label("Provenance source").fill(f"{slug}-browser-analysis:v1")
            create.get_by_label("Exact Evidence Version IDs, one per line").fill(
                evidence.version_id
            )
            create.get_by_role("button", name=f"Review exact {lane_name} Input").click()
            _confirm(page)
            workspace = web_fixture.operational.practitioner_workspace(
                web_fixture.admin_session, web_fixture.visible_case_id
            )
            assert workspace is not None
            lane_view = workspace.value if slug == "value" else workspace.risk
            candidate = lane_view.candidates[0]

            applicability = page.locator("details").filter(
                has_text="Assess exact Evidence Applicability"
            )
            applicability.locator("summary").click()
            applicability.get_by_label("Evidence Record ID").fill(evidence.record_id)
            applicability.get_by_label("Evidence Version ID").fill(evidence.version_id)
            applicability.get_by_label("Target type").select_option(f"{slug}_input_version")
            applicability.get_by_label("Target Record ID").fill(candidate.record_id)
            applicability.get_by_label("Target Version ID").fill(candidate.version_id)
            applicability.get_by_label("Purpose").fill("bounded-management")
            applicability.get_by_label("Assessed scope").fill("exact governed Configuration")
            applicability.get_by_label("Rationale").fill(f"Exact {lane_name} basis")
            applicability.get_by_label("Accountable mechanism").fill(
                "governed:m1b-browser-applicability"
            )
            applicability.get_by_role("button", name="Review exact Applicability").click()
            _confirm(page)
            workspace = web_fixture.operational.practitioner_workspace(
                web_fixture.admin_session, web_fixture.visible_case_id
            )
            assert workspace is not None
            applicability_view = next(
                item
                for item in workspace.applicability
                if item.content["target_version_id"] == candidate.version_id
            )

            lane = page.locator("section.lane").filter(
                has=page.get_by_role("heading", name=lane_name)
            )
            candidate_card = lane.locator("article.record-card").filter(
                has_text=f"Independent {lane_name} finding"
            )
            candidate_card.get_by_role("button", name="Review readiness record").click()
            _confirm(page)
            lane = page.locator("section.lane").filter(
                has=page.get_by_role("heading", name=lane_name)
            )
            fitness_form = lane.locator("details").filter(has_text=f"Record {lane_name} fitness")
            fitness_form.locator("summary").click()
            fitness_form.get_by_label("Exact Input Version ID").fill(candidate.version_id)
            fitness_form.get_by_label("Use context").fill("bounded-operation")
            fitness_form.get_by_label("Purpose").fill("bounded-management")
            fitness_form.get_by_label("Exact Evidence Version ID").fill(evidence.version_id)
            fitness_form.get_by_label("Exact Applicability Version ID").fill(
                applicability_view.version_id
            )
            fitness_form.get_by_label("Claimed scope").fill("exact governed Configuration")
            fitness_form.get_by_label("Rationale").fill("Exact material support is supportable")
            fitness_form.get_by_label("Accountable mechanism").fill(
                f"governed:m1b-browser-{slug}-fitness"
            )
            fitness_form.get_by_role("button", name="Review exact fitness").click()
            _confirm(page)
            workspace = web_fixture.operational.practitioner_workspace(
                web_fixture.admin_session, web_fixture.visible_case_id
            )
            assert workspace is not None
            lane_view = workspace.value if slug == "value" else workspace.risk
            fitness = lane_view.fitness[0]

            lane = page.locator("section.lane").filter(
                has=page.get_by_role("heading", name=lane_name)
            )
            selection = lane.locator("details").filter(
                has_text=f"Select one exact {lane_name} Input"
            )
            selection.locator("summary").click()
            selection.get_by_label("Input Record ID").fill(candidate.record_id)
            selection.get_by_label("Input Version ID").fill(candidate.version_id)
            selection.get_by_label("Fitness Version ID").fill(fitness.version_id)
            selection.get_by_label("Use context").fill("bounded-operation")
            selection.get_by_label("Purpose").fill("bounded-management")
            selection.get_by_label("Material Applicability Version IDs, one per line").fill(
                applicability_view.version_id
            )
            selection.get_by_label("Rationale").fill(f"Exact {lane_name} selection")
            selection.get_by_label("Accountable mechanism").fill(
                f"governed:m1b-browser-{slug}-acceptance"
            )
            selection.get_by_role("button", name="Review exact selection").click()
            _confirm(page)

        final = web_fixture.operational.practitioner_workspace(
            web_fixture.admin_session, web_fixture.visible_case_id
        )
        assert final is not None
        assert final.value.selection_state.value == "ESTABLISHED"
        assert final.risk.selection_state.value == "ESTABLISHED"
        assert (
            final.value.selections[0].content["input_version_id"]
            != final.risk.selections[0].content["input_version_id"]
        )
        assert page.get_by_text("Exact identity and provenance").first.is_visible()
        assert "future M1C" in page.content()
        page.close()
