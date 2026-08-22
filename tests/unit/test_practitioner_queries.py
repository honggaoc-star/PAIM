from __future__ import annotations

import json

import pytest

from paim.application.practitioner import PractitionerQueryService, ReadState
from paim.integrity import EffectiveInterval, FinalizedRecordVersion, RecordId, RecordVersionId
from paim.operational import AccessEffect, Permission, ScopeType
from tests.helpers import utc
from tests.web_support import WebFixture, grant


def _version(
    family: str,
    content: dict[str, object],
    *,
    record_id: RecordId | None = None,
    version_id: RecordVersionId | None = None,
) -> FinalizedRecordVersion:
    return FinalizedRecordVersion(
        record_id or RecordId.new(),
        version_id or RecordVersionId.new(),
        family,
        f"test:{family}",
        json.dumps(content),
        utc(2026, 8, 21),
        EffectiveInterval(utc(2026, 1, 1)),
        "test-practitioner",
    )


def test_access_filter_precedes_case_aggregation_and_retains_exact_basis(
    web_fixture: WebFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    def reject_global_case_enumeration() -> frozenset[object]:
        raise AssertionError("scoped access must not enumerate the global Case population")

    monkeypatch.setattr(
        web_fixture.operational.operational_store,
        "all_case_ids",
        reject_global_case_enumeration,
    )
    records_before = web_fixture.operational.domain_store.count_rows("records")
    view = web_fixture.operational.practitioner_home(web_fixture.admin_session)

    assert view.visible_case_count == 1
    assert len(view.cases) == 1
    case = view.cases[0]
    assert case.case_id == str(web_fixture.visible_case_id)
    assert case.title == "Visible governed service"
    assert case.state is ReadState.ESTABLISHED
    assert case.visible_configuration_count == 1
    assert case.basis.record_id == str(web_fixture.visible_case_id)
    assert len(case.basis.version_ids) == 1
    assert case.basis.effective_at == case.basis.known_at
    represented = repr(view)
    assert str(web_fixture.hidden_case_id) not in represented
    assert "Protected hidden service" not in represented
    assert web_fixture.operational.domain_store.count_rows("records") == records_before


def test_neutral_ordering_search_and_next_request_access_change(
    web_fixture: WebFixture,
) -> None:
    grant(
        web_fixture,
        Permission.CASE_READ,
        "read",
        ScopeType.CASE,
        web_fixture.hidden_case_id,
    )
    ordered = web_fixture.operational.practitioner_cases(web_fixture.admin_session)
    assert [item.title for item in ordered.cases] == [
        "Protected hidden service",
        "Visible governed service",
    ]

    initial = web_fixture.operational.practitioner_cases(
        web_fixture.admin_session, search_text="visible"
    )
    assert [item.title for item in initial.cases] == ["Visible governed service"]
    assert initial.visible_case_count == 1

    grant(
        web_fixture,
        Permission.CASE_READ,
        "read",
        ScopeType.CASE,
        web_fixture.hidden_case_id,
        AccessEffect.DENY,
    )

    grant(
        web_fixture,
        Permission.CASE_READ,
        "read",
        ScopeType.CASE,
        web_fixture.visible_case_id,
        AccessEffect.DENY,
    )
    changed = web_fixture.operational.practitioner_cases(web_fixture.admin_session)
    assert changed.cases == ()
    assert changed.visible_case_count == 0


def test_contextual_labels_require_unambiguous_exact_visible_relationships() -> None:
    evidence = _version("evidence", {"source": "visible pilot evidence"})
    value_input = _version("value-input", {"lane": "VALUE", "finding": "Visible Value finding"})
    applicability = _version(
        "evidence-applicability",
        {
            "evidence_id": str(evidence.record_id),
            "evidence_version_id": str(evidence.version_id),
            "target_id": str(value_input.record_id),
            "target_version_id": str(value_input.version_id),
            "target_type": "value_input_version",
            "outcome": "APPLICABLE",
        },
    )
    visible = PractitionerQueryService._exact_visible_version_index(
        (evidence, value_input, applicability)
    )
    assert PractitionerQueryService._contextual_label(applicability, visible, "opaque") == (
        "Applicable — visible pilot evidence → Value analysis: Visible Value finding"
    )

    hidden_input = _version("value-input", {"lane": "VALUE", "finding": "Protected hidden finding"})
    inaccessible = _version(
        "evidence-applicability",
        {
            "evidence_id": str(evidence.record_id),
            "evidence_version_id": str(evidence.version_id),
            "target_id": str(hidden_input.record_id),
            "target_version_id": str(hidden_input.version_id),
            "target_type": "value_input_version",
            "outcome": "APPLICABLE",
        },
    )
    inaccessible_label = PractitionerQueryService._contextual_label(
        inaccessible,
        PractitionerQueryService._exact_visible_version_index((evidence, inaccessible)),
        "opaque",
    )
    assert inaccessible_label == "Applicability — exact related records unavailable"
    assert "Protected hidden finding" not in inaccessible_label

    ambiguous = PractitionerQueryService._exact_visible_version_index(
        (evidence, evidence, value_input, applicability)
    )
    assert (
        PractitionerQueryService._contextual_label(applicability, ambiguous, "opaque")
        == "Applicability — exact related records unavailable"
    )


def test_lane_labels_do_not_cross_bind_or_guess_missing_selection_basis() -> None:
    value_input = _version("value-input", {"lane": "VALUE", "finding": "Exact Value finding"})
    risk_input = _version("risk-input", {"lane": "RISK", "finding": "Exact Risk finding"})
    valid_value_fitness = _version(
        "lane-evidence-fitness",
        {
            "lane": "VALUE",
            "input_version_id": str(value_input.version_id),
            "outcome": "SUPPORTABLE",
        },
    )
    crossed_value_fitness = _version(
        "lane-evidence-fitness",
        {
            "lane": "VALUE",
            "input_version_id": str(risk_input.version_id),
            "outcome": "SUPPORTABLE",
        },
    )
    selection = _version(
        "input-acceptance-selection",
        {
            "lane": "VALUE",
            "input_id": str(value_input.record_id),
            "input_version_id": str(value_input.version_id),
            "fitness_version_id": str(valid_value_fitness.version_id),
        },
    )
    visible = PractitionerQueryService._exact_visible_version_index(
        (value_input, risk_input, valid_value_fitness, crossed_value_fitness, selection)
    )
    assert (
        PractitionerQueryService._contextual_label(valid_value_fitness, visible, "opaque")
        == "Value fitness — Supportable — Exact Value finding"
    )
    crossed_label = PractitionerQueryService._contextual_label(
        crossed_value_fitness, visible, "opaque"
    )
    assert crossed_label == "Value fitness — exact analysis unavailable"
    assert "Exact Risk finding" not in crossed_label
    assert (
        PractitionerQueryService._contextual_label(selection, visible, "opaque")
        == "Value assessment selected — Exact Value finding"
    )

    missing_fitness = PractitionerQueryService._exact_visible_version_index(
        (value_input, selection)
    )
    assert (
        PractitionerQueryService._contextual_label(selection, missing_fitness, "opaque")
        == "Value assessment selection — exact analysis unavailable"
    )
