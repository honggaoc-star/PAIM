"""Immutable practitioner-facing read DTOs with exact authoritative basis."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
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
class PractitionerExceptionView:
    intended_action: str
    condition: str
    why_it_matters: str
    resolution: str


@dataclass(frozen=True, slots=True)
class OrientationItemView:
    key: str
    label: str
    summary: str
    href: str
    exception: PractitionerExceptionView | None = None


@dataclass(frozen=True, slots=True)
class ConfigurationView:
    configuration_id: str
    version_id: str
    maturity: str
    purpose: str
    content: dict[str, Any]
    is_governing: bool
    practitioner_label: str
    context_summary: str
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
class AnalyticalAssessmentView:
    """One visible analytical Input with only its exact governed relations."""

    input: GovernedRecordView
    statuses: tuple[str, ...]
    applicability: tuple[GovernedRecordView, ...]
    fitness: tuple[GovernedRecordView, ...]
    selections: tuple[GovernedRecordView, ...]

    @property
    def ready(self) -> bool:
        return "ready" in self.statuses or "frozen" in self.statuses

    @property
    def frozen(self) -> bool:
        return "frozen" in self.statuses

    @property
    def actionable(self) -> bool:
        return not {"withdrawn", "superseded", "refresh_required"}.intersection(self.statuses)


@dataclass(frozen=True, slots=True)
class AnalyticalLaneView:
    lane: str
    candidates: tuple[GovernedRecordView, ...]
    fitness: tuple[GovernedRecordView, ...]
    selections: tuple[GovernedRecordView, ...]
    selection_state: ReadState
    explanation: ExplanationView
    assessments: tuple[AnalyticalAssessmentView, ...] = ()
    task_stage: str = "DEVELOP"
    action_access: Mapping[str, bool] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DecisionWorkspaceView:
    selected_value: GovernedRecordView | None
    selected_risk: GovernedRecordView | None
    integrations: tuple[GovernedRecordView, ...]
    boundaries: tuple[GovernedRecordView, ...]
    decisions: tuple[GovernedRecordView, ...]
    authorizations: tuple[GovernedRecordView, ...]
    authority_assignments: tuple[GovernedRecordView, ...]
    history: tuple[GovernedRecordView, ...]
    integration_state: ReadState
    boundary_state: ReadState
    decision_state: ReadState
    authorization_state: ReadState
    integration_explanation: ExplanationView
    boundary_explanation: ExplanationView
    decision_explanation: ExplanationView
    authorization_explanation: ExplanationView


@dataclass(frozen=True, slots=True)
class CaseWorkspaceView:
    actor: ActorContext
    case: CaseSummary
    lifecycle_state: str
    configurations: tuple[ConfigurationView, ...]
    governing_state: ReadState
    governing_configuration_version_ids: tuple[str, ...]
    governing_explanation: ExplanationView
    current_position: str
    evidence: tuple[GovernedRecordView, ...]
    available_information: tuple[GovernedRecordView, ...]
    explicitly_unavailable_information: tuple[GovernedRecordView, ...]
    information_action_access: Mapping[str, bool]
    authority: tuple[GovernedRecordView, ...]
    authority_gaps: tuple[GovernedRecordView, ...]
    applicability: tuple[GovernedRecordView, ...]
    value: AnalyticalLaneView
    risk: AnalyticalLaneView
    decision: DecisionWorkspaceView
    available_work: tuple[OrientationItemView, ...]
    required_prerequisite: OrientationItemView | None
    unresolved_conditions: tuple[OrientationItemView, ...]
    effective_at: datetime
    known_at: datetime
