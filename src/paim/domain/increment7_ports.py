"""Persistence ports for the bounded Increment 7 service."""

from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Protocol

from paim.domain.increment6_ports import Increment6Store, Increment6Transaction
from paim.integrity import RecordId, RecordVersionId


class Increment7Transaction(Increment6Transaction, Protocol):
    def add_shared_dependency(self, **values: object) -> None: ...

    def shared_dependency_detail(self, version_id: RecordVersionId) -> dict[str, object] | None: ...

    def add_dependency_candidate_set(self, **values: object) -> None: ...

    def candidate_set_detail(self, version_id: RecordVersionId) -> dict[str, object] | None: ...

    def candidate_set_members(
        self, version_id: RecordVersionId
    ) -> tuple[dict[str, object], ...]: ...

    def add_shared_dependency_mechanism(self, **values: object) -> None: ...

    def shared_dependency_mechanism_detail(
        self, version_id: RecordVersionId
    ) -> dict[str, object] | None: ...

    def shared_dependency_mechanism_versions(
        self, *, target_type: str, target_id: str
    ) -> tuple[RecordVersionId, ...]: ...

    def add_equivalence_determination(self, **values: object) -> None: ...

    def equivalence_determination_rows(
        self,
        *,
        candidate_set_version_id: RecordVersionId,
        dependency_kind: str,
        equivalence_scope: str,
    ) -> tuple[dict[str, object], ...]: ...

    def add_register_manifest(self, **values: object) -> None: ...

    def register_manifest(self, manifest_id: str) -> dict[str, object] | None: ...

    def add_notification_intent(self, **values: object) -> None: ...

    def notification_intents(self, manifest_id: str) -> tuple[dict[str, object], ...]: ...

    def record_versions_for_register(
        self, version_ids: tuple[RecordVersionId, ...]
    ) -> tuple[dict[str, object], ...]: ...

    def register_record_identities(
        self, families: tuple[str, ...]
    ) -> tuple[dict[str, str], ...]: ...

    def role_assignment_records(
        self, *, role: str, targets: tuple[tuple[str, str], ...]
    ) -> tuple[RecordId, ...]: ...


class Increment7Store(Increment6Store, Protocol):
    def semantic_transaction(self) -> AbstractContextManager[Increment7Transaction]: ...

    def read_transaction(self) -> AbstractContextManager[Increment7Transaction]: ...
