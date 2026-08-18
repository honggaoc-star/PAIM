"""Persistence ports required by the bounded Increment 2 domain service."""

from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Protocol

from paim.domain.models import (
    ConfigurationVersionContext,
    GoverningDesignationDetail,
    RoleAssignmentDetail,
)
from paim.integrity import RecordId, RecordVersionId
from paim.persistence.ports import IntegrityTransaction


class Increment2Transaction(IntegrityTransaction, Protocol):
    def case_exists(self, case_id: RecordId) -> bool: ...

    def add_case(self, case_id: RecordId, version_id: RecordVersionId) -> None: ...

    def add_case_link(
        self,
        *,
        link_id: str,
        source_case_id: RecordId,
        target_case_id: RecordId,
        relationship_type: str,
        recorded_at_us: int,
        effective_at_us: int,
        actor_id: str,
        reason: str,
    ) -> None: ...

    def configuration_owning_case(self, configuration_id: RecordId) -> RecordId | None: ...

    def add_configuration(
        self,
        *,
        configuration_id: RecordId,
        version_id: RecordVersionId,
        owning_case_id: RecordId,
        maturity: str,
        purpose: str,
    ) -> None: ...

    def configuration_version_context(
        self, version_id: RecordVersionId
    ) -> ConfigurationVersionContext | None: ...

    def actor_exists(self, actor_id: RecordId) -> bool: ...

    def add_actor(self, actor_id: RecordId, version_id: RecordVersionId) -> None: ...

    def add_role_assignment(
        self,
        *,
        assignment_id: RecordId,
        version_id: RecordVersionId,
        actor_id: RecordId,
        role: str,
        target_type: str,
        target_id: str,
        case_context_id: RecordId | None,
        accountable: bool,
        compatibility_key: str,
        delegation_effect: str,
        delegated_from_version_id: RecordVersionId | None,
    ) -> None: ...

    def role_assignment_records(
        self, *, role: str, targets: tuple[tuple[str, str], ...]
    ) -> tuple[RecordId, ...]: ...

    def role_assignment_detail(
        self, version_id: RecordVersionId
    ) -> RoleAssignmentDetail | None: ...

    def add_governing_designation(
        self,
        *,
        version_id: RecordVersionId,
        case_id: RecordId,
        configuration_version_id: RecordVersionId,
        accountable_assignment_version_id: RecordVersionId | None,
        accountable_mechanism: str | None,
    ) -> None: ...

    def governing_designation_detail(
        self, version_id: RecordVersionId
    ) -> GoverningDesignationDetail | None: ...

    def add_configuration_determination(
        self,
        *,
        version_id: RecordVersionId,
        configuration_version_id: RecordVersionId,
        determination_kind: str,
        outcome: str,
        rationale: str,
        accountable_assignment_version_id: RecordVersionId | None,
        accountable_mechanism: str | None,
    ) -> None: ...


class Increment2Store(Protocol):
    def semantic_transaction(self) -> AbstractContextManager[Increment2Transaction]: ...

    def read_transaction(self) -> AbstractContextManager[Increment2Transaction]: ...
