"""Domain-neutral integrity primitives."""

from paim.integrity.ids import (
    AuditId,
    CommandId,
    EventId,
    RecordId,
    RecordVersionId,
    RelationshipId,
)
from paim.integrity.records import (
    DraftRecord,
    FinalizedRecordVersion,
    RelationshipType,
    StatusEvent,
    VersionRelationship,
)
from paim.integrity.selection import (
    CurrentSelection,
    SelectionAbsent,
    SelectionCandidate,
    SelectionConflict,
    SelectionFound,
    SelectionQuery,
    select_current,
)
from paim.integrity.time import (
    Clock,
    EffectiveInterval,
    FixedClock,
    SystemClock,
    from_epoch_microseconds,
    require_utc,
    to_epoch_microseconds,
)

__all__ = [
    "AuditId",
    "Clock",
    "CommandId",
    "CurrentSelection",
    "DraftRecord",
    "EffectiveInterval",
    "EventId",
    "FinalizedRecordVersion",
    "FixedClock",
    "RecordId",
    "RecordVersionId",
    "RelationshipId",
    "RelationshipType",
    "SelectionAbsent",
    "SelectionCandidate",
    "SelectionConflict",
    "SelectionFound",
    "SelectionQuery",
    "StatusEvent",
    "SystemClock",
    "VersionRelationship",
    "from_epoch_microseconds",
    "require_utc",
    "select_current",
    "to_epoch_microseconds",
]
