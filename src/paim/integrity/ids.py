"""Opaque, nominal UUIDv7 identity types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from uuid6 import uuid7


@dataclass(frozen=True, slots=True)
class _UuidIdentity:
    value: UUID

    def __post_init__(self) -> None:
        if self.value.version != 7:
            raise ValueError(f"{type(self).__name__} requires an RFC 9562 UUIDv7")

    @classmethod
    def new(cls) -> Self:
        return cls(uuid7())

    @classmethod
    def parse(cls, value: str) -> Self:
        return cls(UUID(value))

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True, slots=True)
class RecordId(_UuidIdentity):
    """Stable identity for one continuing management subject."""


@dataclass(frozen=True, slots=True)
class RecordVersionId(_UuidIdentity):
    """Identity for one immutable content version."""


@dataclass(frozen=True, slots=True)
class CommandId(_UuidIdentity):
    """Identity for one semantic command."""


@dataclass(frozen=True, slots=True)
class EventId(_UuidIdentity):
    """Identity for one status event."""


@dataclass(frozen=True, slots=True)
class RelationshipId(_UuidIdentity):
    """Identity for one exact-version relationship."""


@dataclass(frozen=True, slots=True)
class AuditId(_UuidIdentity):
    """Identity for one authoritative audit fact."""
