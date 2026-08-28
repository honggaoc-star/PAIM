from __future__ import annotations

import socket
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager

import pytest
import uvicorn
from playwright.sync_api import Browser, Page

from paim.web import create_web_application
from paim.web.sessions import SessionRegistry
from tests.web_support import TOKEN, WebFixture


@contextmanager
def live_server(fixture: WebFixture) -> Iterator[str]:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = int(probe.getsockname()[1])
    origin = f"http://127.0.0.1:{port}"
    app = create_web_application(
        fixture.config,
        operational=fixture.operational,
        sessions=SessionRegistry(now=fixture.now),
        expected_origin=origin,
        now=fixture.now,
    )
    server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning", access_log=False)
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 10
    while not server.started and thread.is_alive() and time.monotonic() < deadline:
        time.sleep(0.01)
    if not server.started:
        server.should_exit = True
        thread.join(timeout=5)
        raise RuntimeError("bounded M1A browser server did not start")
    try:
        yield origin
    finally:
        server.should_exit = True
        thread.join(timeout=10)


def perform_no_javascript_path(page: Page, origin: str, hidden_case_id: str) -> None:
    page.goto(f"{origin}/login")
    page.get_by_label("User ID").fill("principal:web-practitioner")
    page.get_by_label("Password or access credential").fill(TOKEN)
    page.get_by_role("button", name="Sign in").click()
    assert page.url == f"{origin}/home", page.content()
    assert page.get_by_role("heading", name="Home", exact=True).is_visible()
    page.get_by_role("link", name="Cases", exact=True).click()
    page.wait_for_url(f"{origin}/cases")
    assert page.get_by_role("heading", name="Cases", exact=True).is_visible()
    assert "Protected hidden service" not in page.content()
    assert hidden_case_id not in page.content()
    page.get_by_role("button", name="Sign out").click()
    page.wait_for_url(f"{origin}/login")


@pytest.mark.browser
def test_login_home_cases_keyboard_logout_and_no_javascript(
    web_fixture: WebFixture, browser: Browser
) -> None:
    with live_server(web_fixture) as origin:
        context = browser.new_context()
        page = context.new_page()
        page.goto(f"{origin}/login")
        page.keyboard.press("Tab")
        assert page.locator(":focus").inner_text() == "Skip to main content"
        page.get_by_label("User ID").fill("principal:web-practitioner")
        page.get_by_label("Password or access credential").fill(TOKEN)
        page.get_by_role("button", name="Sign in").click()
        assert page.url == f"{origin}/home", page.content()
        assert page.get_by_role("heading", name="Home", exact=True).is_visible()
        page.get_by_role("link", name="Cases", exact=True).click()
        assert page.get_by_text("Visible governed service").is_visible()
        assert "Protected hidden service" not in page.content()
        page.get_by_role("link", name="Account", exact=True).first.click()
        assert page.get_by_role("button", name="Sign out").count() == 1
        page.get_by_role("button", name="Sign out").click()
        page.wait_for_url(f"{origin}/login")
        context.close()

        no_javascript = browser.new_context(java_script_enabled=False)
        perform_no_javascript_path(
            no_javascript.new_page(), origin, str(web_fixture.hidden_case_id)
        )
        no_javascript.close()
