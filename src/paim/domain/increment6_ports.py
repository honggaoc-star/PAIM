"""Persistence ports for the bounded Increment 6 domain service."""

from __future__ import annotations

from contextlib import AbstractContextManager
from datetime import datetime
from typing import Protocol

from paim.domain.increment5_ports import Increment5Store, Increment5Transaction
from paim.integrity import RecordId, RecordVersionId


class Increment6Transaction(Increment5Transaction, Protocol):
    def add_reassessment_mechanism(self, **values: object) -> None: ...

    def reassessment_mechanism_detail(
        self, version_id: RecordVersionId
    ) -> dict[str, object] | None: ...

    def add_trigger(self, **values: object) -> None: ...

    def trigger_detail(self, version_id: RecordVersionId) -> dict[str, object] | None: ...

    def trigger_versions_for_identity(
        self, trigger_id: RecordId
    ) -> tuple[RecordVersionId, ...]: ...

    def add_trigger_determination(self, **values: object) -> None: ...

    def trigger_determination_rows(
        self, trigger_version_id: RecordVersionId
    ) -> tuple[dict[str, object], ...]: ...

    def add_reassessment(self, **values: object) -> None: ...

    def reassessment_detail(self, version_id: RecordVersionId) -> dict[str, object] | None: ...

    def reassessment_versions_for_case(self, case_id: RecordId) -> tuple[RecordVersionId, ...]: ...

    def trigger_set(
        self, reassessment_version_id: RecordVersionId
    ) -> tuple[tuple[RecordVersionId, RecordVersionId], ...]: ...

    def membership_rows_for_trigger(
        self, trigger_version_id: RecordVersionId
    ) -> tuple[dict[str, object], ...]: ...

    def add_reassessment_determination(self, **values: object) -> None: ...

    def reassessment_determination_detail(
        self, version_id: RecordVersionId
    ) -> dict[str, object] | None: ...

    def reassessment_determination_rows(
        self,
        *,
        kind: str,
        trigger_version_id: RecordVersionId | None = None,
        reassessment_version_ids: tuple[RecordVersionId, ...] = (),
    ) -> tuple[dict[str, object], ...]: ...

    def add_interim_disposition(self, **values: object) -> None: ...

    def interim_disposition_rows(
        self,
        *,
        case_id: RecordId,
        decision_version_id: RecordVersionId,
        configuration_version_id: RecordVersionId,
    ) -> tuple[dict[str, object], ...]: ...

    def add_decision_confirmation(self, **values: object) -> None: ...

    def add_reassessment_completion(self, **values: object) -> None: ...

    def reassessment_completion(
        self, reassessment_version_id: RecordVersionId
    ) -> dict[str, object] | None: ...

    def current_reassessment_status(
        self,
        *,
        reassessment_version_id: RecordVersionId,
        effective_at: datetime,
        known_at: datetime,
    ) -> str: ...


class Increment6Store(Increment5Store, Protocol):
    def semantic_transaction(self) -> AbstractContextManager[Increment6Transaction]: ...

    def read_transaction(self) -> AbstractContextManager[Increment6Transaction]: ...
