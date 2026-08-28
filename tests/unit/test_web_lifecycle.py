from __future__ import annotations

import threading
from pathlib import Path

from paim.web.lifecycle import (
    LifecycleCoordinator,
    LocalLifecycleState,
    configuration_fingerprint,
)


def test_lifecycle_stop_is_process_local_idempotent_and_waitable() -> None:
    lifecycle = LifecycleCoordinator()
    observed: list[bool] = []
    waiter = threading.Thread(target=lambda: observed.append(lifecycle.wait_for_stop(1)))
    waiter.start()

    assert lifecycle.state is LocalLifecycleState.RUNNING
    assert lifecycle.request_stop() is True
    assert lifecycle.request_stop() is False
    waiter.join(timeout=2)

    assert observed == [True]
    assert lifecycle.state is LocalLifecycleState.STOPPING


def test_configuration_fingerprint_binds_exact_path_and_content(tmp_path: Path) -> None:
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    first.write_text('{"credential_env":"TOKEN"}', encoding="utf-8")
    second.write_text('{"credential_env":"TOKEN"}', encoding="utf-8")

    original = configuration_fingerprint(first)
    assert configuration_fingerprint(first) == original
    assert configuration_fingerprint(second) != original

    first.write_text('{"credential_env":"OTHER_TOKEN"}', encoding="utf-8")
    assert configuration_fingerprint(first) != original
