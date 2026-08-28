"""Supported Windows launcher for one local PAIM browser application."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from contextlib import AbstractContextManager
from hashlib import sha256
from pathlib import Path
from types import TracebackType
from typing import BinaryIO, Self

from paim.operational import load_configuration
from paim.web.cli import DEFAULT_HOST, DEFAULT_PORT
from paim.web.lifecycle import configuration_fingerprint

_READINESS_TIMEOUT_SECONDS = 30.0


class LauncherError(RuntimeError):
    """A plain-language local launch failure."""


class InstanceLock(AbstractContextManager["InstanceLock"]):
    """Hold one configuration-specific Windows file lock for the launcher lifetime."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._stream: BinaryIO | None = None
        self.acquired = False

    def __enter__(self) -> Self:
        if sys.platform != "win32":
            raise LauncherError("The PAIM desktop launcher currently supports Windows only.")
        import msvcrt

        self._path.parent.mkdir(parents=True, exist_ok=True)
        stream = self._path.open("a+b")
        if stream.tell() == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        try:
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            stream.close()
            return self
        self._stream = stream
        self.acquired = True
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._stream is None:
            return
        import msvcrt

        self._stream.seek(0)
        msvcrt.locking(self._stream.fileno(), msvcrt.LK_UNLCK, 1)
        self._stream.close()
        self._stream = None
        self.acquired = False


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="paim-launcher")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--readiness-timeout", type=float, default=_READINESS_TIMEOUT_SECONDS)
    return parser


def _user_environment(name: str) -> str | None:
    if sys.platform != "win32":
        return None
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            value, _kind = winreg.QueryValueEx(key, name)
    except FileNotFoundError:
        return None
    return str(value) if value else None


def _credential_environment(name: str) -> dict[str, str]:
    credential = os.environ.get(name) or _user_environment(name)
    if not credential:
        raise LauncherError(f"The Windows credential environment variable {name} is not available.")
    environment = os.environ.copy()
    environment[name] = credential
    return environment


def _application_root() -> Path:
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        raise LauncherError("The Windows local application-data folder is unavailable.")
    return Path(local) / "PAIM"


def _probe(url: str, expected_fingerprint: str) -> bool:
    try:
        with urllib.request.urlopen(f"{url}/lifecyclez", timeout=1.0) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, ValueError, urllib.error.URLError):
        return False
    return bool(
        payload.get("application") == "PAIM"
        and payload.get("state") == "RUNNING"
        and payload.get("instance") == expected_fingerprint
    )


def _open_browser(url: str) -> None:
    if not webbrowser.open(url, new=1):
        raise LauncherError(f"PAIM started, but the browser could not open. Open {url} manually.")


def _stop_owned_process(process: subprocess.Popen[bytes]) -> None:
    """Bound cleanup to the exact child created by this launcher."""

    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def launch(
    config_path: Path,
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    readiness_timeout: float = _READINESS_TIMEOUT_SECONDS,
) -> int:
    """Start, verify, open, and own one intended local PAIM instance."""

    if host != DEFAULT_HOST:
        raise LauncherError("PAIM desktop launch permits only the local computer address.")
    if not 1_024 <= port <= 65_535:
        raise LauncherError("The configured PAIM browser port is invalid.")
    if readiness_timeout <= 0:
        raise LauncherError("The PAIM readiness timeout must be positive.")
    resolved_config = config_path.resolve(strict=True)
    configuration = load_configuration(resolved_config)
    fingerprint = configuration_fingerprint(resolved_config)
    environment = _credential_environment(configuration.credential_env)
    url = f"http://{host}:{port}"
    application_root = _application_root()
    lock_name = sha256(str(resolved_config).casefold().encode("utf-8")).hexdigest()[:24]
    lock_path = application_root / "locks" / f"{lock_name}.lock"

    with InstanceLock(lock_path) as instance_lock:
        if not instance_lock.acquired:
            if _probe(url, fingerprint):
                _open_browser(url)
                return 0
            raise LauncherError(
                "PAIM is already starting or running, but its local page is not ready."
            )
        if _probe(url, fingerprint):
            _open_browser(url)
            return 0

        log_directory = application_root / "logs"
        log_directory.mkdir(parents=True, exist_ok=True)
        log_path = log_directory / "paim-launcher.log"
        command = (
            sys.executable,
            "-m",
            "paim.web.cli",
            "--config",
            str(resolved_config),
            "--host",
            host,
            "--port",
            str(port),
        )
        creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        with log_path.open("ab", buffering=0) as diagnostics:
            process = subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=diagnostics,
                stderr=subprocess.STDOUT,
                env=environment,
                creationflags=creation_flags,
            )
            deadline = time.monotonic() + readiness_timeout
            while time.monotonic() < deadline:
                result = process.poll()
                if result is not None:
                    raise LauncherError(f"PAIM could not start. Support details are in {log_path}.")
                if _probe(url, fingerprint):
                    try:
                        _open_browser(url)
                    except LauncherError:
                        _stop_owned_process(process)
                        raise
                    return process.wait()
                time.sleep(0.2)
            _stop_owned_process(process)
            raise LauncherError(
                f"PAIM did not become ready in time. Support details are in {log_path}."
            )


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        return launch(
            args.config,
            host=args.host,
            port=args.port,
            readiness_timeout=args.readiness_timeout,
        )
    except (LauncherError, OSError, ValueError) as error:
        print(f"PAIM could not start: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
