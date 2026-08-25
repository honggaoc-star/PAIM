"""Prospective semantic-contract and exact-context primitives.

These types are deliberately domain-neutral.  A digest identifies canonical bytes; it
does not imply authority, equivalence, priority, applicability, or satisfaction.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum
from typing import Self

from paim.integrity.ids import RecordId, RecordVersionId


class ContextMemberKind(StrEnum):
    RECORD = "RECORD"
    VERSION = "VERSION"
    LITERAL = "LITERAL"


@dataclass(frozen=True, slots=True, order=True)
class ExactContextMember:
    slot: str
    kind: ContextMemberKind
    identity: str

    def __post_init__(self) -> None:
        if not self.slot or self.slot != self.slot.strip() or not self.slot.isascii():
            raise ValueError("context slot must be non-empty canonical ASCII")
        if not self.identity or self.identity != self.identity.strip():
            raise ValueError("context identity must be non-empty and canonical")
        if self.kind is ContextMemberKind.RECORD:
            RecordId.parse(self.identity)
        elif self.kind is ContextMemberKind.VERSION:
            RecordVersionId.parse(self.identity)


@dataclass(frozen=True, slots=True)
class ExactContextSet:
    members: tuple[ExactContextMember, ...]
    canonical_json: str
    digest: str

    @classmethod
    def create(cls, members: tuple[ExactContextMember, ...]) -> Self:
        if not members:
            raise ValueError("exact context set cannot be empty")
        ordered = tuple(sorted(members))
        if len(set(ordered)) != len(ordered):
            raise ValueError("duplicate exact context member")
        # A slot is a controlled semantic position, not an ordered list position.
        slots = [member.slot for member in ordered]
        if len(set(slots)) != len(slots):
            raise ValueError("exact context slots must be unique")
        represented = [
            {"identity": member.identity, "kind": member.kind.value, "slot": member.slot}
            for member in ordered
        ]
        canonical = json.dumps(represented, sort_keys=True, separators=(",", ":"))
        return cls(ordered, canonical, hashlib.sha256(canonical.encode("utf-8")).hexdigest())


@dataclass(frozen=True, slots=True)
class SemanticContractRef:
    contract_id: str
    version: str

    def __post_init__(self) -> None:
        for value in (self.contract_id, self.version):
            if not value or value != value.strip():
                raise ValueError("semantic contract identity and version are required")

    @property
    def key(self) -> str:
        return f"{self.contract_id}@{self.version}"
