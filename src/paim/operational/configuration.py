"""Fail-closed local configuration loading for Increment 8."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import cast

from paim.operational.models import ConfigurationError, LocalConfiguration

_REQUIRED_PATHS = (
    "database_path",
    "intake_directory",
    "spool_directory",
    "export_directory",
    "backup_directory",
    "event_log_path",
)


def load_configuration(path: Path) -> LocalConfiguration:
    if not path.is_file():
        raise ConfigurationError("PAIM configuration file is not established")
    try:
        raw = cast("dict[str, object]", json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError, TypeError) as error:
        raise ConfigurationError("PAIM configuration is unreadable or invalid") from error
    missing = [key for key in (*_REQUIRED_PATHS, "credential_env") if not raw.get(key)]
    if missing:
        raise ConfigurationError("required PAIM configuration is missing")
    credential_env = str(raw["credential_env"])
    if credential_env not in os.environ or not os.environ[credential_env]:
        raise ConfigurationError("configured credential source is unavailable")

    def resolved(key: str) -> Path:
        value = Path(str(raw[key])).expanduser()
        return value if value.is_absolute() else (path.parent / value).resolve()

    config = LocalConfiguration(
        database_path=resolved("database_path"),
        credential_env=credential_env,
        intake_directory=resolved("intake_directory"),
        spool_directory=resolved("spool_directory"),
        export_directory=resolved("export_directory"),
        backup_directory=resolved("backup_directory"),
        event_log_path=resolved("event_log_path"),
    )
    if (
        len(
            {
                config.intake_directory,
                config.spool_directory,
                config.export_directory,
                config.backup_directory,
            }
        )
        != 4
    ):
        raise ConfigurationError("operational directories must be distinct")
    if config.database_path in {
        config.intake_directory,
        config.spool_directory,
        config.export_directory,
        config.backup_directory,
    }:
        raise ConfigurationError("database path cannot be an operational directory")
    for directory in (
        config.database_path.parent,
        config.intake_directory,
        config.spool_directory,
        config.export_directory,
        config.backup_directory,
        config.event_log_path.parent,
    ):
        directory.mkdir(parents=True, exist_ok=True)
    return config


def credential_from_environment(config: LocalConfiguration) -> str:
    value = os.environ.get(config.credential_env)
    if not value:
        raise ConfigurationError("configured credential source is unavailable")
    return value
