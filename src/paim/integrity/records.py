"""Draft, finalized-version, status-event, and relationship primitives."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import cast

from paim.integrity.ids import EventId, RecordId, RecordVersionId, RelationshipId
from paim.integrity.time import EffectiveInterval, require_utc

type JsonScalar = str | int | float | bool | None
type JsonValue = JsonScalar | list[JsonValue] | dict[str, JsonValue]


def canonical_json(content: dict[str, JsonValue]) -> str:
    """Produce the versioned kernel's deterministic JSON representation."""
    return json.dumps(content, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@dataclass(slots=True)
class DraftRecord:
    """Mutable content that has not crossed finalization or reliance boundaries."""

    record_id: RecordId
    family: str
    scope: str
    content: dict[str, JsonValue]
    _relied_upon: bool = field(default=False, init=False, repr=False)
    _finalized_version_id: RecordVersionId | None = field(default=None, init=False, repr=False)

    def mutate(self, content: dict[str, JsonValue]) -> None:
        if self._relied_upon:
            raise RuntimeError("draft relied upon by authoritative history cannot be mutated")
        if self._finalized_version_id is not None:
            raise RuntimeError("finalized content cannot be mutated in place")
        self.content = content

    def mark_relied_upon(self) -> None:
        if self._finalized_version_id is not None:
            raise RuntimeError("finalized content is already immutable")
        self._relied_upon = True

    def finalize(
        self,
        *,
        recorded_at: datetime,
        effective: EffectiveInterval,
        creator: str,
        version_id: RecordVersionId | None = None,
    ) -> FinalizedRecordVersion:
        if self._relied_upon:
            raise RuntimeError(
                "a relied-upon draft must be preserved, not finalized after mutation"
            )
        if self._finalized_version_id is not None:
            raise RuntimeError("draft has already been finalized")
        finalized = FinalizedRecordVersion(
            record_id=self.record_id,
            version_id=version_id or RecordVersionId.new(),
            family=self.family,
            scope=self.scope,
            content_json=canonical_json(self.content),
            recorded_at=recorded_at,
            effective=effective,
            creator=creator,
        )
        self._finalized_version_id = finalized.version_id
        return finalized


@dataclass(frozen=True, slots=True)
class FinalizedRecordVersion:
    """Immutable substantive content for one exact version."""

    record_id: RecordId
    version_id: RecordVersionId
    family: str
    scope: str
    content_json: str
    recorded_at: datetime
    effective: EffectiveInterval
    creator: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "recorded_at", require_utc(self.recorded_at))
        parsed = json.loads(self.content_json)
        if not isinstance(parsed, dict):
            raise ValueError("finalized content must be a JSON object")
        normalized = canonical_json(cast("dict[str, JsonValue]", parsed))
        object.__setattr__(self, "content_json", normalized)

    @property
    def content(self) -> dict[str, JsonValue]:
        """Return a detached value; callers cannot mutate authoritative content."""
        return cast("dict[str, JsonValue]", json.loads(self.content_json))

    def substantive_successor(
        self,
        *,
        content: dict[str, JsonValue],
        recorded_at: datetime,
        effective: EffectiveInterval,
        creator: str,
        version_id: RecordVersionId | None = None,
    ) -> FinalizedRecordVersion:
        successor_id = version_id or RecordVersionId.new()
        if successor_id == self.version_id:
            raise ValueError("substantive successor requires a distinct Record Version ID")
        return FinalizedRecordVersion(
            record_id=self.record_id,
            version_id=successor_id,
            family=self.family,
            scope=self.scope,
            content_json=canonical_json(content),
            recorded_at=recorded_at,
            effective=effective,
            creator=creator,
        )


@dataclass(frozen=True, slots=True)
class StatusEvent:
    """Append-only lifecycle fact that does not change substantive content."""

    event_id: EventId
    target_version_id: RecordVersionId
    prior_status: str
    new_status: str
    recorded_at: datetime
    effective_at: datetime
    actor: str
    basis: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "recorded_at", require_utc(self.recorded_at))
        object.__setattr__(self, "effective_at", require_utc(self.effective_at))


class RelationshipType(StrEnum):
    """P0 relationship meanings with no record-family workflow attached."""

    PREDECESSOR_SUCCESSOR = "predecessor_successor"
    CORRECTION = "correction"
    AMENDMENT = "amendment"
    SUPERSESSION = "supersession"
    WITHDRAWAL = "withdrawal"
    EXACT_VERSION_DEPENDENCY = "exact_version_dependency"


@dataclass(frozen=True, slots=True)
class VersionRelationship:
    """Append-only relationship between exact immutable versions."""

    relationship_id: RelationshipId
    source_version_id: RecordVersionId
    target_version_id: RecordVersionId
    relationship_type: RelationshipType
    recorded_at: datetime
    reason: str

    def __post_init__(self) -> None:
        if self.source_version_id == self.target_version_id:
            raise ValueError("relationship source and target versions must differ")
        object.__setattr__(self, "recorded_at", require_utc(self.recorded_at))
