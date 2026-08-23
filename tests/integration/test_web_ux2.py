from __future__ import annotations

from paim.application.practitioner import ConfigurationView
from paim.domain import EvidenceAttention, EvidenceClassification, EvidenceVersionInput
from paim.integrity import RecordId, RecordVersionId
from paim.operational import AccessEffect, Permission, ScopeType
from tests.integration.test_web_m1b import _grant_m1b, _review_commit
from tests.web_support import EFFECTIVE, WebFixture, grant, login


def _establish_setup(web_fixture: WebFixture) -> tuple[str, ConfigurationView]:
    _grant_m1b(web_fixture)
    assert login(web_fixture.client)[1].status_code == 303
    case_id = str(web_fixture.visible_case_id)
    view = web_fixture.operational.practitioner_workspace(
        web_fixture.admin_session, web_fixture.visible_case_id
    )
    assert view is not None
    configuration = view.configurations[0]
    assert (
        _review_commit(
            web_fixture.client,
            f"/cases/{case_id}/configuration/designation/review",
            {
                "configuration_id": configuration.configuration_id,
                "configuration_version_id": configuration.version_id,
                "accountable_mechanism": "governed:ux2-setup-review",
                "effective_at": view.effective_at.isoformat(),
            },
        )[2].status_code
        == 303
    )
    return case_id, configuration


def _record_information(
    web_fixture: WebFixture,
    configuration: ConfigurationView,
    *,
    key: str,
    classification: EvidenceClassification,
    statement: str,
    content: dict[str, object] | None = None,
) -> tuple[RecordId, RecordVersionId]:
    evidence_id = RecordId.new()
    version_id = RecordVersionId.new()
    configuration_id = RecordId.parse(configuration.configuration_id)
    configuration_version_id = RecordVersionId.parse(configuration.version_id)
    web_fixture.operational.run_command(
        web_fixture.admin_session,
        action="evidence.create",
        idempotency_key=f"ux2-information-{key}",
        case_id=web_fixture.visible_case_id,
        configuration_id=configuration_id,
        operation=lambda service, meta: service.commit_evidence(
            meta,
            EvidenceVersionInput(
                evidence_id,
                version_id,
                web_fixture.visible_case_id,
                configuration_id,
                configuration_version_id,
                classification,
                f"ux2-source:{key}",
                {"source": f"ux2-provenance:{key}"},
                {"statement": statement, **(content or {})},
                None,
                EFFECTIVE,
                EvidenceAttention.CURRENT,
            ),
        ),
    )
    return evidence_id, version_id


def test_ux2_information_groups_require_explicit_governed_unavailability(
    web_fixture: WebFixture,
) -> None:
    case_id, configuration = _establish_setup(web_fixture)
    observed_id, observed_version = _record_information(
        web_fixture,
        configuration,
        key="observed",
        classification=EvidenceClassification.OBSERVED,
        statement="The documented review was completed.",
        content={"limitation": "This does not establish downstream applicability."},
    )
    neutral_unknown_id, neutral_unknown_version = _record_information(
        web_fixture,
        configuration,
        key="neutral-unknown",
        classification=EvidenceClassification.UNKNOWN,
        statement="The vendor response is recorded without a positive finding.",
        content={"unknown": True},
    )
    unavailable_id, unavailable_version = _record_information(
        web_fixture,
        configuration,
        key="explicitly-unavailable",
        classification=EvidenceClassification.UNKNOWN,
        statement="No live applicant outcome evidence is available.",
        content={
            "unknown": True,
            "not_a_positive_finding": True,
            "limitation": "No production population was observed.",
        },
    )

    view = web_fixture.operational.practitioner_workspace(
        web_fixture.admin_session, web_fixture.visible_case_id
    )
    assert view is not None
    assert {item.version_id for item in view.available_information} == {
        str(observed_version),
        str(neutral_unknown_version),
    }
    assert {item.version_id for item in view.explicitly_unavailable_information} == {
        str(unavailable_version)
    }
    assert len(view.evidence) == 3
    assert not view.applicability
    assert not view.value.candidates and not view.risk.candidates

    applicability_count = web_fixture.operational.domain_store.count_rows(
        "evidence_applicability_versions"
    )
    page = web_fixture.client.get(f"/cases/{case_id}/evidence")
    assert page.status_code == 200
    known = page.text.split('id="known-heading"', maxsplit=1)[1].split("</section>", maxsplit=1)[0]
    unavailable = page.text.split('id="unknown-heading"', maxsplit=1)[1].split(
        "</section>", maxsplit=1
    )[0]
    assert "The documented review was completed." in known
    assert "The vendor response is recorded without a positive finding." in known
    assert "No live applicant outcome evidence is available." not in known
    assert "No live applicant outcome evidence is available." in unavailable
    assert "This is not a positive finding." in unavailable
    assert "Recorded information" not in known
    assert "Explicitly unavailable" not in unavailable
    assert "Repository silence" not in page.text
    assert "No additional gap is inferred." not in unavailable
    assert "not_a_positive_finding" not in page.text
    assert "Identity and provenance" not in page.text
    assert str(observed_id) not in known and str(observed_version) not in known
    assert str(neutral_unknown_id) not in known and str(neutral_unknown_version) not in known
    assert str(unavailable_id) not in unavailable and str(unavailable_version) not in unavailable
    assert (
        web_fixture.operational.domain_store.count_rows("evidence_applicability_versions")
        == applicability_count
    )


def test_ux2_authority_review_and_access_boundaries_remain_fail_closed(
    web_fixture: WebFixture,
) -> None:
    case_id, configuration = _establish_setup(web_fixture)
    _, evidence_version = _record_information(
        web_fixture,
        configuration,
        key="protected",
        classification=EvidenceClassification.OBSERVED,
        statement="Protected exact information for the visible setup.",
    )
    base = f"/cases/{case_id}"
    view = web_fixture.operational.practitioner_workspace(
        web_fixture.admin_session, web_fixture.visible_case_id
    )
    assert view is not None
    assert (
        _review_commit(
            web_fixture.client,
            f"{base}/authority/review",
            {
                "configuration_id": configuration.configuration_id,
                "configuration_version_id": configuration.version_id,
                "category": "policy",
                "source": "Practitioner review policy",
                "scope": "the current assessment setup",
                "requirement": "A named reviewer must assess the supplied information.",
                "provenance": "ux2-policy-source",
                "evidence_version_ids": str(evidence_version),
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
                "question_id": "ux2-reviewer-authority",
                "question": "Who may approve the review conclusion?",
                "scope": "the current assessment setup",
                "rationale": "No eligible approval assignment is established.",
                "provenance": "ux2-unresolved-question",
                "evidence_version_ids": str(evidence_version),
                "effective_at": view.effective_at.isoformat(),
            },
        )[2].status_code
        == 303
    )

    decision_authority_count = web_fixture.operational.domain_store.count_rows(
        "decision_authorization_basis_versions"
    )
    role_count = web_fixture.operational.domain_store.count_rows("role_assignment_versions")
    page = web_fixture.client.get(f"{base}/evidence")
    assert "Practitioner review policy" in page.text
    assert "recorded scope and requirement" in page.text
    assert "A source does not by itself authorize a person or action." not in page.text
    assert "Who may approve the review conclusion?" in page.text
    assert "Unresolved question" in page.text
    assert "Review how information applies" in page.text
    assert "Record what the information bears on, its scope and limits, and why." in page.text
    assert "explicit judgments or questions that remain separate" not in page.text
    assert (
        "Value"
        not in page.text.split('id="known-heading"', maxsplit=1)[1].split("</section>", maxsplit=1)[
            0
        ]
    )
    assert (
        web_fixture.operational.domain_store.count_rows("decision_authorization_basis_versions")
        == decision_authority_count
    )
    assert web_fixture.operational.domain_store.count_rows("role_assignment_versions") == role_count
    current = web_fixture.operational.practitioner_workspace(
        web_fixture.admin_session, web_fixture.visible_case_id
    )
    assert current is not None
    assert len(current.authority_gaps) == 1
    assert current.authority_gaps[0].state == "UNRESOLVED"
    assert not current.applicability

    grant(
        web_fixture,
        Permission.CONFIGURATION_READ,
        "read",
        ScopeType.CONFIGURATION,
        web_fixture.visible_configuration_id,
        AccessEffect.DENY,
    )
    filtered = web_fixture.client.get(f"{base}/evidence")
    assert filtered.status_code == 200
    for protected in (
        "Protected exact information for the visible setup.",
        "Practitioner review policy",
        "Who may approve the review conclusion?",
        str(evidence_version),
    ):
        assert protected not in filtered.text
    assert "Review how information applies" not in filtered.text
