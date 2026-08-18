"""Programmatic Alembic upgrade entrypoint for local tests and adapters."""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config


def upgrade_database(database_url: str, config_path: Path | None = None) -> None:
    root = Path(__file__).resolve().parents[4]
    config = Config(str(config_path or root / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    command.upgrade(config, "head")
