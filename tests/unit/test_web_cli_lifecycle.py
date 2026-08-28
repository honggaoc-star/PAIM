from __future__ import annotations

import time
from pathlib import Path
from types import SimpleNamespace
from typing import ClassVar

import pytest

from paim.operational import ReadinessState
from paim.web import cli
from paim.web.lifecycle import LifecycleCoordinator


class FakeOperationalApplication:
    closed = False

    def __init__(self, _config: object) -> None:
        type(self).closed = False

    def health(self) -> object:
        return SimpleNamespace(state=ReadinessState.READY)

    def close(self) -> None:
        type(self).closed = True


class FakeServer:
    instances: ClassVar[list[FakeServer]] = []
    lifecycle: ClassVar[LifecycleCoordinator]

    def __init__(self, _configuration: object) -> None:
        self.should_exit = False
        type(self).instances.append(self)

    def run(self) -> None:
        type(self).lifecycle.request_stop()
        deadline = time.monotonic() + 2
        while not self.should_exit and time.monotonic() < deadline:
            time.sleep(0.001)
        assert self.should_exit is True


def test_cli_observes_application_stop_and_closes_resources(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config_path = tmp_path / "paim.json"
    config_path.write_text("{}", encoding="utf-8")
    config = SimpleNamespace(database_url="sqlite+pysqlite:///unused")
    FakeServer.instances.clear()
    monkeypatch.setattr(cli, "load_configuration", lambda _path: config)
    monkeypatch.setattr(cli, "upgrade_database", lambda _url: None)
    monkeypatch.setattr(cli, "OperationalApplication", FakeOperationalApplication)
    monkeypatch.setattr(cli, "configuration_fingerprint", lambda _path: "exact-instance")

    def create_application(*_args: object, **kwargs: object) -> object:
        lifecycle = kwargs["lifecycle"]
        assert isinstance(lifecycle, LifecycleCoordinator)
        FakeServer.lifecycle = lifecycle
        return object()

    monkeypatch.setattr(cli, "create_web_application", create_application)
    monkeypatch.setattr(cli.uvicorn, "Config", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(cli.uvicorn, "Server", FakeServer)

    assert cli.main(["--config", str(config_path)]) == 0
    assert len(FakeServer.instances) == 1
    assert FakeServer.instances[0].should_exit is True
    assert FakeOperationalApplication.closed is True
