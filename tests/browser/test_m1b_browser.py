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
    page.locator("form[data-submit-lock] button").click()
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
        assert "Choose the task that fits the work you are doing now." in page.content()
        assert "display order is not a ranking" not in page.content()
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
        assert page.get_by_role("heading", name="Review and confirm this action").is_visible()
        _confirm(page)
        workspace = web_fixture.operational.practitioner_workspace(
            web_fixture.admin_session, web_fixture.visible_case_id
        )
        assert workspace is not None
        evidence = workspace.evidence[0]

        page.get_by_role("link", name="Value & Risk", exact=True).click()
        assert page.locator(".peer-summary .lane-summary").count() == 2
        assert page.locator("section.lane-work").count() == 2
        assert page.locator(".peer-lanes").count() == 0
        assert page.locator("section.lane-work").first.bounding_box()["width"] > 800  # type: ignore[index]
        assert page.evaluate(
            "document.documentElement.scrollWidth <= document.documentElement.clientWidth"
        )

        for lane_name, slug in (("Value", "value"), ("Risk", "risk")):
            page.get_by_role("link", name="Value & Risk", exact=True).click()
            lane = page.locator("section.lane-work").filter(
                has=page.get_by_role("heading", name=lane_name)
            )
            create = lane.locator("details").filter(has_text=f"Develop the {lane_name} assessment")
            create.get_by_label("Purpose of this assessment").fill("bounded-management")
            finding_question = (
                "What potential Value is supported?"
                if lane_name == "Value"
                else "What Risks or adverse pathways are supported?"
            )
            boundary_question = (
                "Where would that Value apply?"
                if lane_name == "Value"
                else "Where do these Risk conclusions apply?"
            )
            create.get_by_label(finding_question).fill(f"Independent {lane_name} finding")
            create.get_by_label(boundary_question).fill("exact governed Configuration")
            create.get_by_label("What remains uncertain?").fill(
                f"{lane_name} uncertainty remains explicit"
            )
            create.get_by_label(
                f"What action does this {lane_name} assessment alone support?"
            ).fill(f"Retain exact {lane_name} basis")
            create.get_by_label("How was this assessment produced?").fill(
                f"{slug}-browser-analysis:v1"
            )
            create.get_by_label(
                "Which available information is used in this assessment?"
            ).select_option(evidence.version_id)
            create.get_by_role("button", name=f"Review {lane_name} assessment").click()
            assert page.get_by_role(
                "heading", name=f"Review and record {lane_name} assessment"
            ).is_visible()
            _confirm(page)
            workspace = web_fixture.operational.practitioner_workspace(
                web_fixture.admin_session, web_fixture.visible_case_id
            )
            assert workspace is not None
            lane_view = workspace.value if slug == "value" else workspace.risk
            candidate = lane_view.candidates[0]
            assert candidate.version_id not in page.locator("body").inner_text()
            if lane_name == "Value":
                assert (
                    page.locator(".lane-summary")
                    .filter(has_text="Risk assessment")
                    .filter(has_text="Develop assessment")
                    .count()
                    == 1
                )

            lane = page.locator("section.lane-work").filter(
                has=page.get_by_role("heading", name=lane_name)
            )
            candidate_card = lane.locator("article.assessment-card").filter(
                has_text=f"Independent {lane_name} finding"
            )
            candidate_card.get_by_label("Why is it ready for review?").fill(
                f"Exact {lane_name} review complete"
            )
            candidate_card.get_by_role("button", name="Review readiness").click()
            assert page.get_by_role(
                "heading", name=f"Confirm {lane_name} assessment is ready for review"
            ).is_visible()
            _confirm(page)
            candidate_card = page.locator("article.assessment-card").filter(
                has_text=f"Independent {lane_name} finding"
            )
            assert candidate_card.get_by_text("0 of 1 information items reviewed").is_visible()
            candidate_card.get_by_role("link", name="Continue information review").click()
            assert page.get_by_role(
                "heading",
                name=f"Review how the information used in this {lane_name} assessment applies",
            ).is_visible()
            assert page.locator('select[name="evidence_choice"]').count() == 0
            assert page.locator('select[name="target_choice"]').count() == 0
            applicability = page.locator("form.contextual-review-form")
            applicability.get_by_label("Scope of this judgment").fill(
                "exact governed Configuration"
            )
            applicability.get_by_label("Why", exact=True).fill(f"Exact {lane_name} basis")
            applicability.get_by_label("Responsible governance process").fill(
                "governed:m1b-browser-applicability"
            )
            applicability.get_by_role("button", name="Review this information judgment").click()
            assert page.get_by_role(
                "heading", name="Confirm how this information applies"
            ).is_visible()
            assert not page.get_by_text("evidence.applicability", exact=True).is_visible()
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
            lane = page.locator("section.lane-work").filter(
                has=page.get_by_role("heading", name=lane_name)
            )
            fitness_form = lane.locator("details").filter(
                has_text="Is this assessment sufficiently supported for this proposed use?"
            )
            assert lane.locator("form.selection-form").count() == 0
            fitness_form.locator("summary").click()
            fitness_form.get_by_label("Use context").fill("bounded-operation")
            fitness_form.get_by_label("Your support judgment").select_option("SUPPORTABLE")
            fitness_form.get_by_label("Does this limit a later management decision?").select_option(
                "FALSE"
            )
            fitness_form.get_by_label("Role this information plays").fill("material support")
            fitness_form.get_by_label("Is this information required support?").select_option("TRUE")
            fitness_form.get_by_label("Scope supported by this judgment").fill(
                "exact governed Configuration"
            )
            fitness_form.get_by_label("Rationale").fill("Exact material support is supportable")
            fitness_form.get_by_label("Responsible governance process").fill(
                f"governed:m1b-browser-{slug}-fitness"
            )
            fitness_form.get_by_role("button", name="Review support judgment").click()
            assert page.get_by_role(
                "heading",
                name=f"Confirm whether the {lane_name} assessment is sufficiently supported",
            ).is_visible()
            assert page.get_by_text("Sufficiently supported for this use", exact=True).is_visible()
            assert page.get_by_text("material support", exact=True).is_visible()
            assert page.get_by_role("button", name="Record support judgment").is_visible()
            _confirm(page)
            workspace = web_fixture.operational.practitioner_workspace(
                web_fixture.admin_session, web_fixture.visible_case_id
            )
            assert workspace is not None
            lane_view = workspace.value if slug == "value" else workspace.risk
            assert lane_view.fitness[0].state == "SUPPORTABLE"

            lane = page.locator("section.lane-work").filter(
                has=page.get_by_role("heading", name=lane_name)
            )
            selection = lane.locator("form.selection-form").filter(
                has_text=f"Use this {lane_name} assessment"
            )
            assert selection.count() == 1
            selection.get_by_label("Why should management use this assessment?").fill(
                f"Exact {lane_name} selection"
            )
            selection.get_by_label("Responsible governance process").fill(
                f"governed:m1b-browser-{slug}-acceptance"
            )
            selection.get_by_role("button", name="Review use of this assessment").click()
            assert page.get_by_role(
                "heading", name=f"Confirm use of this {lane_name} assessment"
            ).is_visible()
            assert page.get_by_role("button", name=f"Choose {lane_name} assessment").is_visible()
            assert page.get_by_text(
                "It does not authorize a Decision or operation.", exact=False
            ).is_visible()
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
        assert "Integration and management judgment remain separate" in page.content()
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
