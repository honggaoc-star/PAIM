"""Immutable practitioner-facing read DTOs with exact authoritative basis."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any


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


@dataclass(frozen=True, slots=True)
class ExplanationView:
    state: ReadState
    reason: str
    owning_action: str
    identity_established: bool
    software_access: bool
    context_visible: bool
    accountability: str
    substantive_authority: str
    basis_version_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class AttentionItemView:
    key: str
    label: str
    summary: str
    href: str
    explanation: ExplanationView


@dataclass(frozen=True, slots=True)
class ConfigurationView:
    configuration_id: str
    version_id: str
    maturity: str
    purpose: str
    content: dict[str, Any]
    is_governing: bool
    basis: SourceBasis


@dataclass(frozen=True, slots=True)
class GovernedRecordView:
    record_id: str
    version_id: str
    family: str
    label: str
    state: str
    content: dict[str, Any]
    basis: SourceBasis


@dataclass(frozen=True, slots=True)
class AnalyticalLaneView:
    lane: str
    candidates: tuple[GovernedRecordView, ...]
    fitness: tuple[GovernedRecordView, ...]
    selections: tuple[GovernedRecordView, ...]
    selection_state: ReadState
    explanation: ExplanationView


@dataclass(frozen=True, slots=True)
class CaseWorkspaceView:
    actor: ActorContext
    case: CaseSummary
    lifecycle_state: str
    configurations: tuple[ConfigurationView, ...]
    governing_state: ReadState
    governing_configuration_version_ids: tuple[str, ...]
    governing_explanation: ExplanationView
    evidence: tuple[GovernedRecordView, ...]
    authority: tuple[GovernedRecordView, ...]
    authority_gaps: tuple[GovernedRecordView, ...]
    applicability: tuple[GovernedRecordView, ...]
    value: AnalyticalLaneView
    risk: AnalyticalLaneView
    attention: tuple[AttentionItemView, ...]
    effective_at: datetime
    known_at: datetime
