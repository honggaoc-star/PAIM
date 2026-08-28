from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from uvicorn import Config

from paim.web import cli
from tests.web_support import WebFixture


def test_web_cli_rejects_non_loopback_and_invalid_port() -> None:
    with pytest.raises(SystemExit, match=r"only to 127\.0\.0\.1"):
        cli.main(["--config", "unused.json", "--host", "0.0.0.0"])
    with pytest.raises(SystemExit, match="between 1024 and 65535"):
        cli.main(["--config", "unused.json", "--port", "80"])


def test_web_cli_runs_one_worker_without_reload_and_announces_url(
    web_fixture: WebFixture, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    observed: dict[str, object] = {}

    monkeypatch.setattr(cli, "load_configuration", lambda _path: web_fixture.config)
    monkeypatch.setattr(cli, "upgrade_database", lambda _url: None)
    monkeypatch.setattr(cli, "OperationalApplication", lambda _config: web_fixture.operational)
    monkeypatch.setattr(cli, "configuration_fingerprint", lambda _path: "exact-test-instance")

    class TestServer:
        def __init__(self, configuration: Config) -> None:
            observed.update(
                {
                    "host": configuration.host,
                    "port": configuration.port,
                    "workers": configuration.workers,
                    "reload": configuration.reload,
                    "access_log": configuration.access_log,
                }
            )
            self.configuration = configuration
            self.should_exit = False

        def run(self) -> None:
            with TestClient(self.configuration.app, base_url="http://127.0.0.1:8899") as client:
                assert client.get("/healthz").json()["state"] == "READY"
                assert client.get("/lifecyclez").json() == {
                    "application": "PAIM",
                    "state": "RUNNING",
                    "instance": "exact-test-instance",
                }

    monkeypatch.setattr(cli.uvicorn, "Server", TestServer)
    assert cli.main(["--config", "unused.json", "--port", "8899"]) == 0
    assert observed == {
        "host": "127.0.0.1",
        "port": 8899,
        "workers": 1,
        "reload": False,
        "access_log": True,
    }
    assert "PAIM local URL: http://127.0.0.1:8899" in capsys.readouterr().out
