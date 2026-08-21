"""Immutable practitioner-facing read DTOs with exact authoritative basis."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class ReadState(StrEnum):
    ESTABLISHED = "ESTABLISHED"
    ABSENT = "ABSENT"
    CONFLICT = "CONFLICT"
    INDETERMINATE = "INDETERMINATE"
    INACCESSIBLE = "INACCESSIBLE"


@dataclass(frozen=True, slots=True)
class SourceBasis:
    record_id: str
    version_ids: tuple[str, ...]
    effective_at: datetime
    known_at: datetime


@dataclass(frozen=True, slots=True)
class ActorContext:
    principal_id: str
    actor_id: str
    display_name: str
    basis: SourceBasis


@dataclass(frozen=True, slots=True)
class CaseSummary:
    case_id: str
    title: str
    state: ReadState
    explanation: str
    visible_configuration_count: int
    basis: SourceBasis


@dataclass(frozen=True, slots=True)
class HomeView:
    actor: ActorContext
    health: str
    health_reasons: tuple[str, ...]
    visible_case_count: int
    cases: tuple[CaseSummary, ...]
    effective_at: datetime
    known_at: datetime


@dataclass(frozen=True, slots=True)
class CaseListView:
    actor: ActorContext
    cases: tuple[CaseSummary, ...]
    visible_case_count: int
    search_text: str
    effective_at: datetime
    known_at: datetime


@dataclass(frozen=True, slots=True)
class CaseOrientationView:
    actor: ActorContext
    case: CaseSummary
    effective_at: datetime
    known_at: datetime
