from __future__ import annotations

from datetime import timedelta

import pytest
from playwright.sync_api import Browser

from paim.assessment_review import AssessmentLane
from paim.integrity import RecordVersionId
from paim.operational import AccessEffect, Permission, PrincipalStatus, ScopeType
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
    establish_authority(
        web_fixture,
        web_fixture.operational._case_continuity,  # type: ignore[attr-defined]
    )
    grant(
        web_fixture,
        Permission.OPERATIONAL_ADMIN,
        "source-access.manage",
        effect=AccessEffect.DENY,
    )
    grant(
        web_fixture,
        Permission.OPERATIONAL_ADMIN,
        "access.manage",
        effect=AccessEffect.DENY,
    )

    with live_server(web_fixture) as origin:
        context = browser.new_context(java_script_enabled=False)
        page = context.new_page()
        page.goto(f"{origin}/login")
        page.get_by_label("User ID").fill("principal:web-practitioner")
        page.get_by_label("Password or access credential").fill(TOKEN)
        page.get_by_role("button", name="Sign in").click()
        assert page.url == f"{origin}/home", page.content()
        assert page.get_by_text("Nothing currently needs your attention.").is_visible()

        page.get_by_role("link", name="Learn", exact=True).click()
        assert page.get_by_role("heading", name="Learn about Practical AI Management").is_visible()
        assert page.get_by_role(
            "heading", name="Value and Risk answer different questions"
        ).is_visible()
        assert "docs/system" not in page.locator("main").inner_text()

        page.get_by_role("link", name="Cases", exact=True).click()
        page.get_by_role("link", name="Start a Case").click()
        page.get_by_label("Case name").fill("Harborlight Assist - disposable browser proof")
        page.get_by_label("AI name").fill("Harborlight Assist")
        page.get_by_label("What is this AI?").fill(
            "A commercial assistance service for bounded lending-review support."
        )
        page.get_by_label("Source or provider type").select_option("Commercial product or service")
        page.get_by_label("Relevant capabilities").fill(
            "Summarizes application material for accountable staff."
        )
        page.locator("#bounded-use").fill(
            "small-business lending assistance with accountable human judgment."
        )
        page.get_by_label("Decision or management question").fill(
            "Should Harborlight use bounded AI assistance in lending review?"
        )
        page.get_by_label("Operating context").fill(
            "Scenario A assistance only; no autonomous lending Decision."
        )
        page.locator("summary", has_text="Add dependency").click()
        page.locator('[name="dependency_1_name"]').fill("Application data service")
        page.locator('[name="dependency_1_why"]').fill("Provides bounded application facts.")
        page.get_by_role("button", name="Add dependency", exact=True).click()
        page.locator('[name="dependency_2_name"]').fill("Commercial AI API")
        page.locator('[name="dependency_2_why"]').fill("Provides the assistance capability.")
        page.get_by_role("button", name="Add another dependency").click()
        page.locator('[name="dependency_3_name"]').fill("Human lending review")
        page.locator('[name="dependency_3_why"]').fill("Retains accountable judgment.")
        web_fixture.now.advance(timedelta(minutes=31))
        _use_fixture_clock(web_fixture)
        page.get_by_role("button", name="Review Case").click()
        assert page.get_by_role("heading", name="Sign in to PAIM").is_visible()
        assert "restore the information you entered" in page.locator("main").inner_text()
        page.get_by_label("User ID").fill("principal:web-practitioner")
        page.get_by_label("Password or access credential").fill(TOKEN)
        page.get_by_role("button", name="Sign in").click()
        assert page.get_by_text("Case information was restored").is_visible()
        assert page.locator('[name="dependency_1_name"]').input_value() == (
            "Application data service"
        )
        assert page.locator('[name="dependency_2_name"]').input_value() == "Commercial AI API"
        assert page.locator('[name="dependency_3_name"]').input_value() == "Human lending review"
        page.get_by_role("button", name="Review Case").click()
        assert page.get_by_role("heading", name="Review Case").is_visible()
        assert page.get_by_text(
            "Should Harborlight use bounded AI assistance in lending review?"
        ).is_visible()
        page.get_by_role("link", name="Back to edit").click()
        assert page.locator('[name^="dependency_"][name$="_name"]').count() == 3
        assert page.locator('[name="dependency_1_name"]').input_value() == (
            "Application data service"
        )
        assert page.locator('[name="dependency_2_name"]').input_value() == "Commercial AI API"
        assert page.locator('[name="dependency_3_name"]').input_value() == ("Human lending review")
        page.get_by_label("Case name").fill("Harborlight Assist - edited disposable browser proof")
        page.get_by_role("button", name="Review Case").click()
        assert page.get_by_text("Harborlight Assist - edited disposable browser proof").is_visible()
        page.get_by_role("button", name="Start Case", exact=True).click()
        assert "/start/commit/" not in page.url, page.content()

        assert page.get_by_role(
            "heading", name="Harborlight Assist - edited disposable browser proof"
        ).is_visible()
        assert page.get_by_text(
            "small-business lending assistance with accountable human judgment."
        ).is_visible()
        assert page.get_by_text(
            "Should Harborlight use bounded AI assistance in lending review?"
        ).is_visible()
        assert page.get_by_role("heading", name="Potential Value").is_visible()
        assert page.get_by_role("heading", name="Risks and safeguards").is_visible()
        assert page.get_by_role("heading", name="AI", exact=True).is_visible()
        assert page.get_by_text("Application data service", exact=False).is_visible()
        assert page.get_by_text("Commercial AI API", exact=False).is_visible()
        assert page.get_by_text("Human lending review", exact=False).is_visible()
        assert page.get_by_text("PAIM-", exact=False).first.is_visible()
        setup_card = page.locator("article.attention-card").filter(
            has_text="Set up responsibility for Value and Risk assessments"
        )
        assert setup_card.is_visible()
        setup_card.get_by_role("link", name="Continue this work").click()
        assert page.get_by_role(
            "heading", name="Set up responsibility for Value and Risk assessments"
        ).is_visible()
        page.get_by_label("Authority source").fill("Harborlight AI governance charter")
        page.get_by_label("Source reference").fill("Charter HL-AI-2026 section 4.2")
        page.get_by_label("Scope of this assignment authority").fill(
            "This exact Case and its initial independent assessments"
        )
        page.get_by_label("Requirement or rule that permits these assignments").fill(
            "The initiator establishes accountable Value and Risk assessment work."
        )
        page.get_by_role("button", name="Review responsibility setup").click()
        assert page.get_by_role("heading", name="Confirm assessment responsibility").is_visible()
        page.get_by_role("button", name="Record responsibility setup").click()
        assert page.get_by_text("Finish the Value assessment", exact=False).is_visible(), (
            page.locator("main").inner_text()
        )
        assert page.get_by_text("Finish the Risk assessment", exact=False).is_visible()
        assert page.get_by_text("Value assessment — assigned to you").is_visible()
        assert page.get_by_text("Risk assessment — assigned to you").is_visible()
        page.reload()
        assert page.get_by_role(
            "heading", name="Harborlight Assist - edited disposable browser proof"
        ).is_visible()
        page.get_by_role("link", name="Open History & decisions").click()
        assert page.get_by_role("heading", name="History & decisions").is_visible()
        assert page.get_by_role("heading", name="What happened?").is_visible()
        assert page.get_by_text("Advanced time reconstruction and audit sources").is_visible()
        page.get_by_label("Primary").get_by_role("link", name="Cases", exact=True).click()
        assert page.get_by_text(
            "Harborlight Assist - edited disposable browser proof", exact=True
        ).is_visible()
        context.close()


@pytest.mark.browser
def test_case_start_reveals_other_provider_description_only_for_other(
    web_fixture: WebFixture, browser: Browser
) -> None:
    web_fixture.now.value = NOW
    _use_fixture_clock(web_fixture)
    prepare_permissions(web_fixture)
    establish_authority(
        web_fixture,
        web_fixture.operational._case_continuity,  # type: ignore[attr-defined]
    )
    with live_server(web_fixture) as origin:
        context = browser.new_context()
        page = context.new_page()
        page.goto(f"{origin}/login")
        page.get_by_label("User ID").fill("principal:web-practitioner")
        page.get_by_label("Password or access credential").fill(TOKEN)
        page.get_by_role("button", name="Sign in").click()
        page.goto(f"{origin}/cases/new")
        source_type = page.get_by_label("Source or provider type")
        other = page.get_by_label("Please specify (when Other)")
        assert other.is_hidden()
        source_type.select_option("Other")
        assert other.is_visible()
        source_type.select_option("Internally developed")
        assert other.is_hidden()
        context.close()


@pytest.mark.browser
def test_slice_h_value_and_risk_actions_capture_five_judgments_in_a_real_browser(
    web_fixture: WebFixture, browser: Browser
) -> None:
    """A no-JavaScript browser records independent five-question lane judgments."""

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
    grant(
        web_fixture,
        Permission.COMMAND,
        "assessment.finish.risk",
        ScopeType.CASE,
        case_id,
    )
    _grant_all_case_sources(web_fixture, case_id, configuration_id)

    with live_server(web_fixture) as origin:
        context = browser.new_context(java_script_enabled=False)
        page = context.new_page()
        page.goto(f"{origin}/login")
        page.get_by_label("User ID").fill("principal:web-practitioner")
        page.get_by_label("Password or access credential").fill(TOKEN)
        page.get_by_role("button", name="Sign in").click()
        page.goto(f"{origin}/cases/{case_id}/tasks/{work.version_id}")
        page.get_by_role("link", name="Continue to this action").click()

        assert page.get_by_role("heading", name="Finish the Value assessment").is_visible()
        assert page.get_by_label("What value are we expecting from this AI use?").is_visible()
        assert page.get_by_label("What could go wrong or require attention?").count() == 0
        page.get_by_label("What value are we expecting from this AI use?").fill(
            "Reduce accountable review preparation time by about 20%."
        )
        page.get_by_label("How is the AI use expected to contribute to that value?").fill(
            "It may organize the exact visible information for accountable staff."
        )
        page.get_by_label("What constraints or limitations could affect the expected value?").fill(
            "Benefit depends on source quality and does not include lending judgment."
        )
        page.get_by_label(
            "What uncertainty about the AI use and its expected value should the "
            "decision maker be aware of?"
        ).fill("The time benefit may vary with application complexity.")
        page.get_by_label(
            "If the AI use is adopted, should its value be reassessed? If so, when or how often?"
        ).fill("Reassess quarterly after adoption using observed preparation time.")
        assert (
            page.get_by_label("Why is this Value assessment ready for independent review?").count()
            == 0
        )
        assert page.get_by_label("Other important limitations").count() == 0
        page.get_by_role("button", name="Review the Value assessment").click()

        assert page.get_by_role("heading", name="Record this Value assessment?").is_visible()
        assert page.get_by_text("What this does not change:", exact=True).is_visible()
        assert page.get_by_text(
            "Risk, suitability, reliance, and the management decision are not changed."
        ).is_visible()
        assert page.get_by_text("Reduce accountable review preparation time").is_visible()
        assert page.get_by_text("Reassess quarterly after adoption").is_visible()
        page.get_by_role("button", name="Record Value assessment").click()

        risk_card = page.locator("article.attention-card").filter(
            has_text="Finish the Risk assessment"
        )
        assert risk_card.is_visible(), page.locator("main").inner_text()
        risk_card.get_by_role("link", name="Continue this work").click()
        assert page.get_by_role("heading", name="Finish the Risk assessment").is_visible()
        page.get_by_label("What could go wrong or cause harm from this AI use?").fill(
            "A misleading summary could distort an accountable review."
        )
        page.get_by_label(
            "Under what conditions or circumstances could these risks occur or become significant?"
        ).fill("Risk increases when source information is incomplete or contradictory.")
        page.get_by_label(
            "What safeguards or controls are expected to reduce or manage these risks?"
        ).fill("Source citation and accountable human review are expected to detect errors.")
        page.get_by_label(
            "What important residual risk or uncertainty should the decision maker be aware of?"
        ).fill("Reviewers may still over-trust a fluent but inaccurate summary.")
        page.get_by_label(
            "If the AI use is adopted, should its risks and safeguards be reassessed? "
            "If so, when or how often?"
        ).fill("Reassess monthly after adoption and after any material incident.")
        assert (
            page.get_by_label("Why is this Risk assessment ready for independent review?").count()
            == 0
        )
        page.get_by_role("button", name="Review the Risk assessment").click()
        assert page.get_by_role("heading", name="Record this Risk assessment?").is_visible()
        assert page.get_by_text(
            "Value, suitability, reliance, and the management decision are not changed."
        ).is_visible()
        assert page.get_by_text("misleading summary could distort").is_visible()
        page.get_by_role("button", name="Record Risk assessment").click()

        assert page.url == f"{origin}/cases/{case_id}"
        context.close()

    with web_fixture.operational.domain_store.read_transaction() as tx:
        rows = tx.projection_rows("assessment_candidate_versions", case_id=str(case_id))
        assert {str(row["lane"]) for row in rows} == {"VALUE", "RISK"}
        sources = {
            str(row["lane"]): tx.get_version(RecordVersionId.parse(str(row["version_id"])))
            for row in rows
        }
        assert tx.count_rows("prospective_integration_versions") == 0
        assert tx.count_rows("prospective_decision_versions") == 0
        assert tx.count_rows("planned_review_point_versions") == 0
        assert tx.count_rows("review_episode_versions") == 0

    value = sources[AssessmentLane.VALUE.value]
    risk = sources[AssessmentLane.RISK.value]
    assert value is not None and risk is not None
    assert value.record_id != risk.record_id
    assert value.content["finding"] == "Reduce accountable review preparation time by about 20%."
    assert value.content["boundary"] == (
        "It may organize the exact visible information for accountable staff."
    )
    assert value.content["provenance"] == (
        "Benefit depends on source quality and does not include lending judgment."
    )
    assert value.content["uncertainty"] == (
        "The time benefit may vary with application complexity."
    )
    assert value.content["implication"] == (
        "Reassess quarterly after adoption using observed preparation time."
    )
    assert risk.content["finding"] == ("A misleading summary could distort an accountable review.")
    assert risk.content["boundary"] == (
        "Risk increases when source information is incomplete or contradictory."
    )
    assert risk.content["provenance"] == (
        "Source citation and accountable human review are expected to detect errors."
    )
    assert risk.content["uncertainty"] == (
        "Reviewers may still over-trust a fluent but inaccurate summary."
    )
    assert risk.content["implication"] == (
        "Reassess monthly after adoption and after any material incident."
    )
