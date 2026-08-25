"""Immutable non-authoritative practitioner read compositions for Slice B."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from paim.case_continuity.models import ContinuitySelectionKind, ContinuityStatus
from paim.integrity.ids import RecordId, RecordVersionId


@dataclass(frozen=True, slots=True)
class SourceManifest:
    version_ids: tuple[RecordVersionId, ...]
    effective_at: datetime
    known_at: datetime
    rule: str = "gate8-slice-b-practitioner-composition-v1"


@dataclass(frozen=True, slots=True)
class AttentionItem:
    case_id: RecordId
    kind: str
    question: str
    consequence: str
    responsibility_version_id: RecordVersionId | None
    work_version_id: RecordVersionId | None
    source_manifest: SourceManifest


@dataclass(frozen=True, slots=True)
class HomeView:
    heading: str
    items: tuple[AttentionItem, ...]
    visible_case_ids: tuple[RecordId, ...]
    ranked: bool = False


@dataclass(frozen=True, slots=True)
class LanePosition:
    lane: str
    assessment: str
    readiness: str
    adequacy: str
    reliance: str
    source_version_ids: tuple[RecordVersionId, ...]


@dataclass(frozen=True, slots=True)
class GovernedPosition:
    state: str
    source_version_ids: tuple[RecordVersionId, ...]


@dataclass(frozen=True, slots=True)
class CaseView:
    case_id: RecordId
    title: str
    continuity_kind: ContinuitySelectionKind
    continuity_status: ContinuityStatus | None
    governing_configuration_version_id: RecordVersionId | None
    governing_configuration_state: str
    responsibility_state: str
    work_state: str
    current_management_position: tuple[str, ...]
    source_manifest: SourceManifest
    authoritative_master_status_persisted: bool = False
    value_position: LanePosition | None = None
    risk_position: LanePosition | None = None
    integration_position: GovernedPosition | None = None
    decision_position: GovernedPosition | None = None


@dataclass(frozen=True, slots=True)
class TaskView:
    case_id: RecordId
    work_version_id: RecordVersionId
    responsibility_version_id: RecordVersionId
    question: str
    instruction: str
    consequence: str
    return_path: str
    permitted_action: str
    authority_boundary: str
    source_manifest: SourceManifest
