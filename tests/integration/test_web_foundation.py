from __future__ import annotations

from datetime import timedelta

from jinja2 import StrictUndefined

from paim.domain import ActorVersionInput, CaseVersionInput
from paim.integrity import EffectiveInterval, RecordId, RecordVersionId
from paim.operational import (
    AccessEffect,
    HealthReport,
    Permission,
    PrincipalStatus,
    ReadinessState,
    ScopeType,
)
from tests.helpers import utc
from tests.web_support import ORIGIN, TOKEN, WebFixture, csrf_from, grant, login


def test_login_rotation_home_cases_no_js_paths_and_security_headers(
    web_fixture: WebFixture,
) -> None:
    client = web_fixture.client
    login_page = client.get("/login")
    assert login_page.status_code == 200
    assert '<main id="main-content"' in login_page.text
    assert 'class="skip-link"' in login_page.text
    cookie_header = login_page.headers["set-cookie"]
    assert "HttpOnly" in cookie_header
    assert "SameSite=strict" in cookie_header
    assert "Path=/" in cookie_header
    assert "Secure" not in cookie_header
    assert "Domain=" not in cookie_header

    before = client.cookies["paim_session"]
    result = client.post(
        "/session",
        data={
            "principal_id": "principal:web-practitioner",
            "credential": TOKEN,
            "csrf_token": csrf_from(login_page.text),
        },
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    assert result.status_code == 303
    assert result.headers["location"] == "/home"
    assert client.cookies["paim_session"] != before

    home = client.get("/home")
    assert home.status_code == 200
    assert "M1A Practitioner" in home.text
    assert "Visible Cases" in home.text
    assert ">1<" in home.text
    assert "Visible governed service" in home.text
    assert "Protected hidden service" not in home.text
    assert str(web_fixture.hidden_case_id) not in home.text
    assert "script src=" in home.text
    assert "default-src 'self'" in home.headers["content-security-policy"]
    assert "frame-ancestors 'none'" in home.headers["content-security-policy"]
    assert home.headers["x-content-type-options"] == "nosniff"
    assert home.headers["referrer-policy"] == "no-referrer"
    assert home.headers["cache-control"] == "no-store"
    assert "access-control-allow-origin" not in home.headers

    cases = client.get("/cases")
    assert cases.status_code == 200
    assert "Visible governed service" in cases.text
    orientation = client.get(f"/cases/{web_fixture.visible_case_id}")
    assert orientation.status_code == 200
    assert "Exact authoritative source basis" in orientation.text
    assert "Read-only foundation" in orientation.text

    logout_result = client.post(
        "/logout",
        data={"csrf_token": csrf_from(home.text)},
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    assert logout_result.status_code == 303
    assert logout_result.headers["location"] == "/login"
    assert client.get("/home", follow_redirects=False).status_code == 303


def test_hidden_case_search_and_not_found_have_no_existence_leak(
    web_fixture: WebFixture,
) -> None:
    _, response = login(web_fixture.client)
    assert response.status_code == 303

    search = web_fixture.client.get("/cases?q=Protected+hidden")
    assert "0 visible results" in search.text
    assert "Protected hidden service" not in search.text
    assert str(web_fixture.hidden_case_id) not in search.text

    hidden = web_fixture.client.get(f"/cases/{web_fixture.hidden_case_id}")
    unknown = web_fixture.client.get(f"/cases/{RecordId.new()}")
    malformed = web_fixture.client.get("/cases/not-an-identity")
    assert hidden.status_code == unknown.status_code == malformed.status_code == 404
    assert hidden.text == unknown.text == malformed.text


def test_authentication_csrf_origin_host_body_and_credential_redaction(
    web_fixture: WebFixture,
) -> None:
    client = web_fixture.client
    login_page = client.get("/login")
    token = csrf_from(login_page.text)
    data = {
        "principal_id": "principal:web-practitioner",
        "credential": "wrong-protected-credential-value",
        "csrf_token": token,
    }
    missing_origin = client.post("/session", data=data)
    assert missing_origin.status_code == 403
    invalid_origin = client.post(
        "/session", data=data, headers={"Origin": "http://example.invalid"}
    )
    assert invalid_origin.status_code == 403
    unproven_null_origin = client.post("/session", data=data, headers={"Origin": "null"})
    assert unproven_null_origin.status_code == 403
    invalid_csrf = client.post(
        "/session", data={**data, "csrf_token": "invalid"}, headers={"Origin": ORIGIN}
    )
    assert invalid_csrf.status_code == 403
    bad_auth = client.post("/session", data=data, headers={"Origin": ORIGIN})
    assert bad_auth.status_code == 401
    assert "Authentication was not established" in bad_auth.text
    assert "wrong-protected-credential-value" not in bad_auth.text
    assert "wrong-protected-credential-value" not in web_fixture.config.event_log_path.read_text(
        encoding="utf-8"
    )

    bad_host = client.get("/login", headers={"Host": "example.invalid"})
    assert bad_host.status_code == 400
    large = client.post(
        "/session",
        content=b"x" * 8_193,
        headers={"Origin": ORIGIN, "Content-Type": "application/x-www-form-urlencoded"},
    )
    assert large.status_code == 413
    get_mutation = client.get("/session")
    assert get_mutation.status_code == 405


def test_referer_fallback_throttling_autoescape_and_degraded_shell(
    web_fixture: WebFixture, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    client = web_fixture.client
    login_page = client.get("/login")
    referer_login = client.post(
        "/session",
        data={
            "principal_id": "principal:web-practitioner",
            "credential": TOKEN,
            "csrf_token": csrf_from(login_page.text),
        },
        headers={"Referer": f"{ORIGIN}/login"},
        follow_redirects=False,
    )
    assert referer_login.status_code == 303

    malicious_case = RecordId.new()
    web_fixture.operational.run_command(
        web_fixture.admin_session,
        action="case.create",
        idempotency_key="web-escaped-case",
        operation=lambda service, meta: service.commit_case(
            meta,
            CaseVersionInput(
                malicious_case,
                RecordVersionId.new(),
                "<script>alert('not executable')</script>",
                EffectiveInterval(utc(2026, 1, 1)),
            ),
        ),
    )
    grant(web_fixture, Permission.CASE_READ, "read", ScopeType.CASE, malicious_case)
    cases = client.get("/cases")
    assert "<script>alert" not in cases.text
    assert "&lt;script&gt;alert" in cases.text
    assert client.app.state.templates.env.undefined is StrictUndefined

    degraded = HealthReport(
        process_alive=True,
        database_reachable=True,
        schema_compatible=True,
        integrity_usable=True,
        foreign_keys_usable=True,
        directories_usable=False,
        spool_usable=True,
        projection_path_usable=True,
        state=ReadinessState.DEGRADED,
        reasons=("REQUIRED_DIRECTORY_UNAVAILABLE",),
    )
    monkeypatch.setattr(web_fixture.operational, "health", lambda: degraded)
    home = client.get("/home")
    assert home.status_code == 200
    assert "Application health: DEGRADED" in home.text
    assert "REQUIRED_DIRECTORY_UNAVAILABLE" in home.text


def test_session_expiry_principal_remap_and_visibility_change_apply_next_request(
    web_fixture: WebFixture,
) -> None:
    _, response = login(web_fixture.client)
    assert response.status_code == 303
    assert "Visible governed service" in web_fixture.client.get("/home").text

    grant(
        web_fixture,
        Permission.CASE_READ,
        "read",
        ScopeType.CASE,
        web_fixture.visible_case_id,
        AccessEffect.DENY,
    )
    changed = web_fixture.client.get("/home")
    assert "Visible governed service" not in changed.text
    assert ">0<" in changed.text

    replacement = RecordId.new()
    web_fixture.operational.run_command(
        web_fixture.admin_session,
        action="actor.create",
        idempotency_key="web-replacement-actor",
        operation=lambda service, meta: service.commit_actor(
            meta,
            ActorVersionInput(
                replacement,
                RecordVersionId.new(),
                "Replacement Actor",
                EffectiveInterval(utc(2026, 1, 1)),
            ),
        ),
    )
    web_fixture.operational.provision_principal(
        web_fixture.admin_session,
        principal_id="principal:web-practitioner",
        token=TOKEN,
        actor_id=replacement,
        status=PrincipalStatus.ENABLED,
    )
    invalidated = web_fixture.client.get("/home", follow_redirects=False)
    assert invalidated.status_code == 303
    assert invalidated.headers["location"].startswith("/login")

    # A fresh browser session expires after the fixed inactivity boundary.
    web_fixture.client.cookies.clear()
    _, relogin = login(web_fixture.client)
    assert relogin.status_code == 303
    web_fixture.now.advance(timedelta(minutes=31))
    expired = web_fixture.client.get("/home", follow_redirects=False)
    assert expired.status_code == 303


def test_principal_disable_invalidates_browser_session_on_next_request(
    web_fixture: WebFixture,
) -> None:
    _, response = login(web_fixture.client)
    assert response.status_code == 303
    web_fixture.operational.provision_principal(
        web_fixture.admin_session,
        principal_id="principal:web-practitioner",
        token=TOKEN,
        actor_id=web_fixture.actor_id,
        status=PrincipalStatus.DISABLED,
    )
    invalidated = web_fixture.client.get("/home", follow_redirects=False)
    assert invalidated.status_code == 303
    assert invalidated.headers["location"].startswith("/login")
