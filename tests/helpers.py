from __future__ import annotations

from datetime import UTC, datetime

from paim.application import CommitVersionCommand
from paim.audit import ActorResolution
from paim.integrity import CommandId, EffectiveInterval, RecordId, RecordVersionId
from paim.integrity.records import JsonValue, RelationshipType


def utc(year: int, month: int, day: int, hour: int = 0, microsecond: int = 0) -> datetime:
    return datetime(year, month, day, hour, 0, 0, microsecond, tzinfo=UTC)


def version_command(
    *,
    record_id: RecordId | None = None,
    version_id: RecordVersionId | None = None,
    expected_version_id: RecordVersionId | None = None,
    family: str = "opaque-family",
    scope: str = "opaque-scope",
    content: dict[str, JsonValue] | None = None,
    effective_from: datetime | None = None,
    precondition_at: datetime | None = None,
    idempotency_key: str = "command-1",
    relationship_type: RelationshipType | None = None,
    relationship_reason: str | None = None,
    end_predecessor_status: str | None = None,
    principal_id: str = "principal:technical",
    actor_id: str | None = "actor:accountable",
    actor_resolution: ActorResolution = ActorResolution.PROVIDED,
) -> CommitVersionCommand:
    start = effective_from or utc(2026, 1, 1)
    return CommitVersionCommand(
        command_id=CommandId.new(),
        idempotency_scope="test-scope",
        idempotency_key=idempotency_key,
        record_id=record_id or RecordId.new(),
        version_id=version_id or RecordVersionId.new(),
        family=family,
        scope=scope,
        content=content or {"value": "one"},
        effective=EffectiveInterval(start),
        precondition_at=precondition_at or start,
        expected_version_id=expected_version_id,
        principal_id=principal_id,
        actor_id=actor_id,
        actor_resolution=actor_resolution,
        creator=actor_id or principal_id,
        relationship_type=relationship_type,
        relationship_reason=relationship_reason,
        end_predecessor_status=end_predecessor_status,
    )
