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
        assert page.locator(".current-position").is_visible()
        assert page.get_by_role("heading", name="Independent work available now").is_visible()
        assert all(item.get_attribute("open") is None for item in page.locator("details.why").all())
        assert "Protected hidden service" not in page.content()
        assert str(web_fixture.hidden_case_id) not in page.content()

        page.get_by_role("link", name="Proposal setup", exact=True).click()
        page.get_by_label("Responsible governance process").fill(
            "governed:m1b-browser-configuration"
        )
        page.get_by_role("button", name="Review using this setup for assessment").click()
        _confirm(page)
        assert "One setup is used for this assessment" in page.content()
        assert "does not authorize or start operation" in page.content()

        page.get_by_role("link", name="Overview", exact=True).click()
        assert page.get_by_role("heading", name="Independent work available now").is_visible()
        assert page.get_by_role("link", name="Assess Value", exact=True).is_visible()
        assert page.get_by_role("link", name="Assess Risk", exact=True).is_visible()
        assert "Their display order is not a ranking" in page.content()
        assert "Current attention" not in page.content()
        assert page.evaluate(
            "document.documentElement.scrollWidth <= document.documentElement.clientWidth"
        )

        page.get_by_role("link", name="What we know", exact=True).click()
        for heading in (
            "What we know",
            "What we still need to know",
            "Requirements and authority",
            "What needs review",
        ):
            assert page.get_by_role("heading", name=heading, exact=True).is_visible()
        assert page.locator(".three-columns").count() == 0
        assert page.evaluate(
            "document.documentElement.scrollWidth <= document.documentElement.clientWidth"
        )
        evidence_form = page.locator("details").filter(has_text="Add information")
        evidence_form.locator("summary").click()
        evidence_form.get_by_label("Source").fill("browser-observation:v1")
        evidence_form.get_by_label("Where this came from").fill("bounded browser capture")
        evidence_form.get_by_label("What was recorded").fill("The exact control was observed.")
        evidence_form.get_by_role("button", name="Review information").click()
        assert page.get_by_role("heading", name="Confirm exact action").is_visible()
        _confirm(page)
        workspace = web_fixture.operational.practitioner_workspace(
            web_fixture.admin_session, web_fixture.visible_case_id
        )
        assert workspace is not None
        evidence = workspace.evidence[0]

        for lane_name, slug in (("Value", "value"), ("Risk", "risk")):
            page.get_by_role("link", name="Value & Risk", exact=True).click()
            lane = page.locator("section.lane").filter(
                has=page.get_by_role("heading", name=lane_name)
            )
            create = lane.locator("details").filter(has_text=f"Add {lane_name} analysis")
            create.locator("summary").click()
            create.get_by_label("Purpose").fill("bounded-management")
            create.get_by_label("Finding").fill(f"Independent {lane_name} finding")
            create.get_by_label("Boundary of analysis").fill("exact governed Configuration")
            create.get_by_label("Uncertainties, one per line").fill(
                f"{lane_name} uncertainty remains explicit"
            )
            create.get_by_label("Management implication").fill(f"Retain exact {lane_name} basis")
            create.get_by_label("Provenance source").fill(f"{slug}-browser-analysis:v1")
            create.get_by_label("Supporting Evidence (optional)").select_option(evidence.version_id)
            create.get_by_role("button", name=f"Review {lane_name} analysis").click()
            _confirm(page)
            workspace = web_fixture.operational.practitioner_workspace(
                web_fixture.admin_session, web_fixture.visible_case_id
            )
            assert workspace is not None
            lane_view = workspace.value if slug == "value" else workspace.risk
            candidate = lane_view.candidates[0]

            page.get_by_role("link", name="What we know", exact=True).click()
            applicability = page.locator("details").filter(
                has_text="Review how information applies"
            )
            applicability.locator("summary").click()
            applicability.locator('select[name="evidence_choice"]').select_option(
                evidence.version_id
            )
            applicability.locator('select[name="target_choice"]').select_option(
                candidate.version_id
            )
            applicability.get_by_label("Purpose for this review").fill("bounded-management")
            applicability.get_by_label("Scope of this judgment").fill(
                "exact governed Configuration"
            )
            applicability.get_by_label("Why", exact=True).fill(f"Exact {lane_name} basis")
            applicability.get_by_label("Responsible governance process").fill(
                "governed:m1b-browser-applicability"
            )
            applicability.get_by_role("button", name="Review applicability judgment").click()
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
            assert applicability_view.label == (
                f"Applicable — browser-observation:v1 → {lane_name} analysis: "
                f"Independent {lane_name} finding"
            )

            page.get_by_role("link", name="Value & Risk", exact=True).click()
            lane = page.locator("section.lane").filter(
                has=page.get_by_role("heading", name=lane_name)
            )
            candidate_card = lane.locator("article.record-card").filter(
                has_text=f"Independent {lane_name} finding"
            )
            candidate_card.get_by_label("Basis for readiness").fill(
                f"Exact {lane_name} review complete"
            )
            candidate_card.get_by_role("button", name="Review readiness determination").click()
            _confirm(page)
            lane = page.locator("section.lane").filter(
                has=page.get_by_role("heading", name=lane_name)
            )
            fitness_form = lane.locator("details").filter(
                has_text="Determine fitness for a bounded use"
            )
            fitness_form.locator("summary").click()
            fitness_form.locator('select[name="input_version_id"]').select_option(
                candidate.version_id
            )
            fitness_form.get_by_label("Use context").fill("bounded-operation")
            fitness_form.get_by_label("Purpose").fill("bounded-management")
            fitness_form.get_by_label("Fitness outcome").select_option("SUPPORTABLE")
            fitness_form.get_by_label("Decision-limiting").select_option("FALSE")
            fitness_form.locator('select[name="evidence_version_id"]').select_option(
                evidence.version_id
            )
            fitness_form.locator('select[name="applicability_version_id"]').select_option(
                applicability_view.version_id
            )
            fitness_form.get_by_label("Material-evidence role").fill("material support")
            fitness_form.get_by_label("Required support").select_option("TRUE")
            fitness_form.get_by_label("Claimed scope").fill("exact governed Configuration")
            fitness_form.get_by_label("Rationale").fill("Exact material support is supportable")
            fitness_form.get_by_label("Accountable mechanism").fill(
                f"governed:m1b-browser-{slug}-fitness"
            )
            fitness_form.get_by_role("button", name="Review fitness determination").click()
            assert page.get_by_text("SUPPORTABLE", exact=True).is_visible()
            assert page.get_by_text("material support", exact=True).is_visible()
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
                has_text="Select an assessment for bounded use"
            )
            selection.locator("summary").click()
            selection.locator('select[name="input_version_id"]').select_option(candidate.version_id)
            selection.get_by_label("Fitness determination").select_option(fitness.version_id)
            selection.get_by_label("Use context").fill("bounded-operation")
            selection.get_by_label("Purpose").fill("bounded-management")
            selection.get_by_label("Material Applicability determinations").select_option(
                applicability_view.version_id
            )
            selection.get_by_label("Rationale").fill(f"Exact {lane_name} selection")
            selection.get_by_label("Accountable mechanism").fill(
                f"governed:m1b-browser-{slug}-acceptance"
            )
            selection.get_by_role("button", name="Review assessment selection").click()
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
        assert "It does not integrate them" in page.content()
        assert "M1C" not in page.content()
        page.get_by_role("link", name="Source & history", exact=True).click()
        assert page.get_by_text(
            "Value fitness — Supportable — Independent Value finding", exact=True
        ).is_visible()
        assert page.get_by_text(
            "Risk fitness — Supportable — Independent Risk finding", exact=True
        ).is_visible()
        assert page.get_by_text(
            "Value assessment selected — Independent Value finding", exact=True
        ).is_visible()
        assert page.get_by_text(
            "Risk assessment selected — Independent Risk finding", exact=True
        ).is_visible()
        assert page.get_by_text("Source, history, and governance basis").first.is_visible()
        assert page.get_by_text("Identity and provenance").count() == 0
        page.close()
