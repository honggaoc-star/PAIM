from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Self

import pytest

from paim.web import launcher


class FakeLock:
    acquired = True

    def __init__(self, _path: Path) -> None:
        pass

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_args: object) -> None:
        pass


class FakeProcess:
    def __init__(self) -> None:
        self.terminated = False
        self.killed = False

    def poll(self) -> None:
        return None

    def wait(self, timeout: float | None = None) -> int:
        del timeout
        return 0

    def terminate(self) -> None:
        self.terminated = True

    def kill(self) -> None:
        self.killed = True


def configure_launcher(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    acquired: bool = True,
) -> Path:
    config = tmp_path / "paim.json"
    config.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        launcher,
        "load_configuration",
        lambda _path: SimpleNamespace(credential_env="PAIM_TEST_SECRET"),
    )
    monkeypatch.setattr(launcher, "configuration_fingerprint", lambda _path: "exact-instance")
    monkeypatch.setattr(
        launcher,
        "_credential_environment",
        lambda _name: {"PAIM_TEST_SECRET": "protected-value"},
    )
    monkeypatch.setattr(launcher, "_application_root", lambda: tmp_path / "local")

    class ConfiguredLock(FakeLock):
        pass

    ConfiguredLock.acquired = acquired
    monkeypatch.setattr(launcher, "InstanceLock", ConfiguredLock)
    return config


def test_launcher_waits_for_exact_readiness_and_keeps_secret_out_of_command(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config = configure_launcher(monkeypatch, tmp_path)
    probes = iter((False, False, True))
    monkeypatch.setattr(launcher, "_probe", lambda _url, _fingerprint: next(probes))
    opened: list[str] = []
    monkeypatch.setattr(launcher, "_open_browser", opened.append)
    monkeypatch.setattr(launcher.time, "sleep", lambda _seconds: None)
    process = FakeProcess()
    spawned: dict[str, object] = {}

    def popen(command: tuple[str, ...], **kwargs: object) -> FakeProcess:
        spawned["command"] = command
        spawned.update(kwargs)
        return process

    monkeypatch.setattr(launcher.subprocess, "Popen", popen)

    assert launcher.launch(config) == 0
    command = tuple(spawned["command"])
    assert command == (
        launcher.sys.executable,
        "-m",
        "paim.web.cli",
        "--config",
        str(config.resolve()),
        "--host",
        "127.0.0.1",
        "--port",
        "8841",
    )
    assert "protected-value" not in " ".join(command)
    assert spawned["env"] == {"PAIM_TEST_SECRET": "protected-value"}
    assert opened == ["http://127.0.0.1:8841"]
    assert process.terminated is False
    assert process.killed is False


def test_duplicate_launcher_opens_only_the_exact_ready_instance(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config = configure_launcher(monkeypatch, tmp_path, acquired=False)
    monkeypatch.setattr(
        launcher,
        "_probe",
        lambda url, fingerprint: (
            (url, fingerprint)
            == (
                "http://127.0.0.1:8841",
                "exact-instance",
            )
        ),
    )
    opened: list[str] = []
    monkeypatch.setattr(launcher, "_open_browser", opened.append)
    monkeypatch.setattr(
        launcher.subprocess,
        "Popen",
        lambda *_args, **_kwargs: pytest.fail("duplicate launch started another process"),
    )

    assert launcher.launch(config) == 0
    assert opened == ["http://127.0.0.1:8841"]


def test_duplicate_launcher_fails_closed_for_wrong_or_unready_instance(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config = configure_launcher(monkeypatch, tmp_path, acquired=False)
    monkeypatch.setattr(launcher, "_probe", lambda _url, _fingerprint: False)

    with pytest.raises(launcher.LauncherError, match="already starting or running"):
        launcher.launch(config)


def test_launcher_rejects_non_loopback_and_invalid_port(tmp_path: Path) -> None:
    config = tmp_path / "unused.json"
    with pytest.raises(launcher.LauncherError, match="only the local computer"):
        launcher.launch(config, host="0.0.0.0")
    with pytest.raises(launcher.LauncherError, match="port is invalid"):
        launcher.launch(config, port=80)


def test_launcher_reports_child_failure_without_exposing_secret(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config = configure_launcher(monkeypatch, tmp_path)
    monkeypatch.setattr(launcher, "_probe", lambda _url, _fingerprint: False)

    class FailedProcess(FakeProcess):
        def poll(self) -> int:
            return 7

    monkeypatch.setattr(launcher.subprocess, "Popen", lambda *_args, **_kwargs: FailedProcess())

    with pytest.raises(launcher.LauncherError) as raised:
        launcher.launch(config)
    assert "protected-value" not in str(raised.value)


def test_timeout_stops_only_the_exact_owned_child(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config = configure_launcher(monkeypatch, tmp_path)
    monkeypatch.setattr(launcher, "_probe", lambda _url, _fingerprint: False)
    ticks = iter((0.0, 0.0, 2.0))
    monkeypatch.setattr(launcher.time, "monotonic", lambda: next(ticks))
    monkeypatch.setattr(launcher.time, "sleep", lambda _seconds: None)
    process = FakeProcess()
    monkeypatch.setattr(launcher.subprocess, "Popen", lambda *_args, **_kwargs: process)

    with pytest.raises(launcher.LauncherError, match="did not become ready"):
        launcher.launch(config, readiness_timeout=1)
    assert process.terminated is True
    assert process.killed is False


def test_launcher_module_uses_no_broad_process_termination() -> None:
    source = Path(launcher.__file__).read_text(encoding="utf-8")
    for prohibited in ("taskkill", "Stop-Process", "os._exit", "pkill"):
        assert prohibited not in source
    assert "subprocess.CREATE_NO_WINDOW" in source
    assert "process.terminate()" in source
    assert subprocess.CREATE_NO_WINDOW >= 0
