from __future__ import annotations

import json
import os
import re
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

import httpx2
import pytest

from paim.web import launcher
from tests.web_support import TOKEN, WebFixture


def csrf_from_html(text: str) -> str:
    match = re.search(r'name="csrf_token" value="([^"]+)"', text)
    assert match is not None
    return match.group(1)


def external_configuration(fixture: WebFixture, path: Path) -> None:
    config = fixture.config
    path.write_text(
        json.dumps(
            {
                "database_path": str(config.database_path),
                "credential_env": config.credential_env,
                "intake_directory": str(config.intake_directory),
                "spool_directory": str(config.spool_directory),
                "export_directory": str(config.export_directory),
                "backup_directory": str(config.backup_directory),
                "event_log_path": str(config.event_log_path),
            }
        ),
        encoding="utf-8",
    )


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def exercise_and_stop(origin: str, *, expected_case: str) -> None:
    with httpx2.Client(base_url=origin, timeout=10) as client:
        login_page = client.get("/login")
        signed_in = client.post(
            "/session",
            data={
                "principal_id": "principal:web-practitioner",
                "credential": TOKEN,
                "csrf_token": csrf_from_html(login_page.text),
            },
            headers={"Origin": origin},
            follow_redirects=False,
        )
        assert signed_in.status_code == 303
        assert expected_case in client.get("/cases").text
        confirmation = client.get("/account/stop")
        stopped = client.post(
            "/account/stop",
            data={"csrf_token": csrf_from_html(confirmation.text)},
            headers={"Origin": origin},
        )
        assert stopped.status_code == 200
        assert "PAIM is stopping" in stopped.text


@pytest.mark.skipif(sys.platform != "win32", reason="supported launcher is Windows-only")
def test_production_launcher_safe_stop_restart_and_state_continuity(
    web_fixture: WebFixture,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "production-launcher.json"
    external_configuration(web_fixture, config_path)
    monkeypatch.setenv(web_fixture.config.credential_env, TOKEN)
    monkeypatch.setattr(launcher, "_application_root", lambda: tmp_path / "local-app-data")
    port = free_port()
    origin = f"http://127.0.0.1:{port}"

    def launch_stop_and_verify() -> None:
        browser_opened = threading.Event()
        opened: list[str] = []

        def record_open(url: str) -> None:
            opened.append(url)
            browser_opened.set()

        monkeypatch.setattr(launcher, "_open_browser", record_open)
        results: list[int] = []
        failures: list[BaseException] = []

        def run_launcher() -> None:
            try:
                results.append(launcher.launch(config_path, port=port, readiness_timeout=30))
            except BaseException as error:
                failures.append(error)

        thread = threading.Thread(target=run_launcher, daemon=True)
        thread.start()
        assert browser_opened.wait(30), failures
        assert opened == [origin]
        assert launcher._probe(origin, launcher.configuration_fingerprint(config_path))
        exercise_and_stop(origin, expected_case="Visible governed service")
        thread.join(timeout=30)
        assert not thread.is_alive()
        assert failures == []
        assert results == [0]

    launch_stop_and_verify()
    launch_stop_and_verify()

    diagnostics = (tmp_path / "local-app-data" / "logs" / "paim-launcher.log").read_text(
        encoding="utf-8"
    )
    assert TOKEN not in diagnostics
    assert "PAIM local URL:" in diagnostics


@pytest.mark.skipif(sys.platform != "win32", reason="supported launcher is Windows-only")
def test_windows_start_script_uses_locked_python_module_and_safe_stop(
    web_fixture: WebFixture,
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "script-launcher.json"
    external_configuration(web_fixture, config_path)
    settings_path = tmp_path / "launcher-settings.json"
    repository = Path(__file__).resolve().parents[2]
    settings_path.write_text(
        json.dumps(
            {
                "repository_path": str(repository),
                "configuration_path": str(config_path),
            }
        ),
        encoding="utf-8",
    )
    port = 8841
    origin = f"http://127.0.0.1:{port}"
    environment = os.environ.copy()
    environment[web_fixture.config.credential_env] = TOKEN
    environment["LOCALAPPDATA"] = str(tmp_path / "local-app-data")
    environment["BROWSER"] = f"{environment['COMSPEC']} /c echo %s"
    windows_root = environment.get("SystemRoot", environment.get("WINDIR", r"C:\Windows"))
    powershell = Path(windows_root) / "System32/WindowsPowerShell/v1.0/powershell.exe"
    process = subprocess.Popen(
        (
            str(powershell),
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(repository / "tools/windows/Start-PAIM.ps1"),
            "-SettingsPath",
            str(settings_path),
        ),
        cwd=repository,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    fingerprint = launcher.configuration_fingerprint(config_path)
    deadline = time.monotonic() + 30
    try:
        while time.monotonic() < deadline and not launcher._probe(origin, fingerprint):
            if process.poll() is not None:
                output, _ = process.communicate(timeout=5)
                pytest.fail(f"Start-PAIM.ps1 exited before readiness: {output}")
            time.sleep(0.2)
        assert launcher._probe(origin, fingerprint)
        exercise_and_stop(origin, expected_case="Visible governed service")
        output, _ = process.communicate(timeout=30)
        assert process.returncode == 0, output
        assert TOKEN not in output
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=10)

    diagnostics = (tmp_path / "local-app-data/PAIM/logs/paim-launcher.log").read_text(
        encoding="utf-8"
    )
    assert TOKEN not in diagnostics
    assert "PAIM local URL:" in diagnostics
