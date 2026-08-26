"""Non-authoritative Slice-G reconstruction and decision-audit values."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from paim.integrity.ids import RecordId, RecordVersionId


class ReconstructionState(StrEnum):
    AVAILABLE = "AVAILABLE"
    ABSENT = "NOT ESTABLISHED"
    CONFLICT = "CONFLICT — UNRESOLVED"
    NOT_SAFELY_AVAILABLE = "NOT SAFELY AVAILABLE"
    MALFORMED = "RECONSTRUCTION PROBLEM"


@dataclass(frozen=True, slots=True)
class SourceReference:
    record_id: RecordId
    version_id: RecordVersionId
    family: str
    effective_from: datetime
    effective_to: datetime | None
    recorded_at: datetime


@dataclass(frozen=True, slots=True)
class SourceManifest:
    sources: tuple[SourceReference, ...]
    effective_at: datetime
    known_at: datetime
    rule: str = "gate8-slice-g-exact-visible-source-manifest-v1"

    @property
    def version_ids(self) -> tuple[RecordVersionId, ...]:
        return tuple(source.version_id for source in self.sources)


@dataclass(frozen=True, slots=True)
class PositionComponent:
    state: ReconstructionState
    version_ids: tuple[RecordVersionId, ...]
    source_manifest: SourceManifest


@dataclass(frozen=True, slots=True)
class LanePosition:
    lane: str
    assessment_version_id: RecordVersionId
    readiness_version_id: RecordVersionId
    adequacy_version_id: RecordVersionId
    reliance_version_id: RecordVersionId
    information_basis_version_ids: tuple[RecordVersionId, ...]
    source_manifest: SourceManifest


@dataclass(frozen=True, slots=True)
class ManagementPosition:
    state: ReconstructionState
    case_id: RecordId
    effective_at: datetime
    known_at: datetime
    value_state: ReconstructionState
    risk_state: ReconstructionState
    continuity: PositionComponent | None
    governing_configuration: PositionComponent | None
    value: LanePosition | None
    risk: LanePosition | None
    integration: PositionComponent | None
    decision: PositionComponent | None
    review: PositionComponent | None
    quantitative_claims: PositionComponent | None
    responsibility_work: PositionComponent | None
    source_manifest: SourceManifest
    authoritative_master_status_persisted: bool = False
    reader_principal_id: str = ""
    reader_actor_id: RecordId | None = None


@dataclass(frozen=True, slots=True)
class QuantitativePairChange:
    left_claim_version_id: RecordVersionId
    right_claim_version_id: RecordVersionId
    comparability_version_id: RecordVersionId
    difference: str | None
    ratio: str | None
    percentage_change: str | None
    source_manifest: SourceManifest


@dataclass(frozen=True, slots=True)
class PositionChange:
    component: str
    prior_version_ids: tuple[RecordVersionId, ...]
    current_version_ids: tuple[RecordVersionId, ...]
    changed: bool
    source_set_changed: bool = False
    better_or_worse_inferred: bool = False
    causality_inferred: bool = False
    decision_requirement_inferred: bool = False
    quantitative_comparison_established: bool | None = None
    quantitative_pair_changes: tuple[QuantitativePairChange, ...] = ()


@dataclass(frozen=True, slots=True)
class ThenNowComparison:
    state: ReconstructionState
    prior: ManagementPosition | None
    current: ManagementPosition | None
    changes: tuple[PositionChange, ...]
    prior_manifest: SourceManifest
    current_manifest: SourceManifest
    value_risk_netted: bool = False
    decision_quality_inferred: bool = False


@dataclass(frozen=True, slots=True)
class DecisionAuditNarrative:
    state: ReconstructionState
    decision_version_id: RecordVersionId | None
    decision_effective_at: datetime | None
    decision_recorded_at: datetime | None
    action: str | None
    rationale: str | None
    conditions: tuple[str, ...]
    accountable_actor_id: RecordId | None
    responsibility_version_id: RecordVersionId | None
    assignment_version_id: RecordVersionId | None
    assignment_basis_version_id: RecordVersionId | None
    authority_source_version_id: RecordVersionId | None
    integration_version_id: RecordVersionId | None
    value_reliance_version_id: RecordVersionId | None
    risk_reliance_version_id: RecordVersionId | None
    successor_decision_version_ids: tuple[RecordVersionId, ...]
    continuing_review_version_ids: tuple[RecordVersionId, ...]
    subsequent_visible_changes: tuple[PositionChange, ...]
    source_manifest: SourceManifest
    derived_explanation_only: bool = True
    hindsight_error_inferred: bool = False


@dataclass(frozen=True, slots=True)
class TimelineItem:
    family: str
    record_id: RecordId
    version_id: RecordVersionId
    effective_at: datetime
    recorded_at: datetime
    description: str
    source_manifest: SourceManifest
    action: str | None = None
    rationale: str | None = None
    conditions: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CaseTimeline:
    state: ReconstructionState
    case_id: RecordId
    effective_at: datetime
    known_at: datetime
    items: tuple[TimelineItem, ...]
    source_manifest: SourceManifest
    workflow_phase_inferred: bool = False


@dataclass(frozen=True, slots=True)
class CaseHistoryView:
    current_position: ManagementPosition
    prior_position: ManagementPosition
    comparison: ThenNowComparison
    audit: DecisionAuditNarrative
    timeline: CaseTimeline
