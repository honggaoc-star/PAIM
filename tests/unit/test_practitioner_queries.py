from __future__ import annotations

import pytest

from paim.application.practitioner import ReadState
from paim.operational import AccessEffect, Permission, ScopeType
from tests.web_support import WebFixture, grant


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
