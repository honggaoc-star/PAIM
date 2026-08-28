"""Process-local lifecycle coordination for the PAIM local application."""

from __future__ import annotations

import hashlib
import threading
from enum import StrEnum
from pathlib import Path


class LocalLifecycleState(StrEnum):
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"


class LifecycleCoordinator:
    """Coordinate one orderly stop request with the owning serving process."""

    def __init__(self) -> None:
        self._stop_requested = threading.Event()

    @property
    def state(self) -> LocalLifecycleState:
        if self._stop_requested.is_set():
            return LocalLifecycleState.STOPPING
        return LocalLifecycleState.RUNNING

    def request_stop(self) -> bool:
        if self._stop_requested.is_set():
            return False
        self._stop_requested.set()
        return True

    def wait_for_stop(self, timeout: float | None = None) -> bool:
        return self._stop_requested.wait(timeout)


def configuration_fingerprint(path: Path) -> str:
    """Return a non-secret identity for one exact external configuration."""

    resolved = path.resolve(strict=True)
    digest = hashlib.sha256()
    digest.update(str(resolved).casefold().encode("utf-8"))
    digest.update(b"\0")
    digest.update(resolved.read_bytes())
    return digest.hexdigest()
