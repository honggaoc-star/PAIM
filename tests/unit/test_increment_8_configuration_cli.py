from __future__ import annotations

import json
from pathlib import Path

import pytest

from paim.operational.cli import main
from paim.operational.configuration import load_configuration
from paim.operational.models import ConfigurationError


def configuration_file(tmp_path: Path) -> Path:
    path = tmp_path / "paim-local.json"
    path.write_text(
        json.dumps(
            {
                "database_path": "state/paim.sqlite3",
                "credential_env": "PAIM_TEST_LOCAL_TOKEN",
                "intake_directory": "intake",
                "spool_directory": "spool",
                "export_directory": "export",
                "backup_directory": "backup",
                "event_log_path": "events/operational.jsonl",
            }
        ),
        encoding="utf-8",
    )
    return path


def test_configuration_fails_closed_without_external_credential(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = configuration_file(tmp_path)
    monkeypatch.delenv("PAIM_TEST_LOCAL_TOKEN", raising=False)
    with pytest.raises(ConfigurationError, match="credential source"):
        load_configuration(path)


def test_cli_bootstrap_actor_mapping_restart_and_secret_hygiene(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = configuration_file(tmp_path)
    token = "cli-explicit-external-token-0001"
    monkeypatch.setenv("PAIM_TEST_LOCAL_TOKEN", token)
    assert (
        main(
            [
                "--config",
                str(path),
                "bootstrap",
                "--principal",
                "principal:cli-owner",
                "--admin",
                "--allow-command",
                "actor.create",
            ]
        )
        == 0
    )
    capsys.readouterr()
    assert (
        main(
            [
                "--config",
                str(path),
                "actor-create",
                "--principal",
                "principal:cli-owner",
                "--display-name",
                "CLI Owner",
                "--effective-at",
                "2026-08-19T00:00:00+00:00",
            ]
        )
        == 0
    )
    actor_output = json.loads(capsys.readouterr().out)
    assert (
        main(
            [
                "--config",
                str(path),
                "principal-update",
                "--principal",
                "principal:cli-owner",
                "--subject-principal",
                "principal:cli-owner",
                "--subject-token-env",
                "PAIM_TEST_LOCAL_TOKEN",
                "--actor-id",
                actor_output["actor_id"],
                "--status",
                "ENABLED",
            ]
        )
        == 0
    )
    capsys.readouterr()
    assert (
        main(
            [
                "--config",
                str(path),
                "health",
                "--principal",
                "principal:cli-owner",
            ]
        )
        == 0
    )
    health = json.loads(capsys.readouterr().out)
    assert health["state"] == "READY"
    assert token not in path.read_text(encoding="utf-8")
    assert token not in (tmp_path / "events" / "operational.jsonl").read_text(encoding="utf-8")
