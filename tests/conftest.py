from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from paim.persistence.sqlite import SQLiteIntegrityStore, upgrade_database


@pytest.fixture
def sqlite_store(tmp_path: Path) -> Iterator[SQLiteIntegrityStore]:
    database_path = (tmp_path / "integrity.sqlite3").as_posix()
    database_url = f"sqlite+pysqlite:///{database_path}"
    upgrade_database(database_url)
    store = SQLiteIntegrityStore(database_url, timeout_seconds=0.05)
    try:
        yield store
    finally:
        store.dispose()


@pytest.fixture
def integrity_store(sqlite_store: SQLiteIntegrityStore) -> SQLiteIntegrityStore:
    """Adapter-contract seam; future adapters can override this fixture."""
    return sqlite_store
