"""Prospective continuing-review values for Gate 8 Slice E."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from paim.assessment_review.models import AssessmentLane, CommandIdentity
from paim.integrity.ids import RecordId, RecordVersionId
from paim.integrity.semantics import ExactContextSet, SemanticContractRef
from paim.integrity.time import require_utc


class ReviewConstraintOperator(StrEnum):
    BY = "BY"
    NOT_BEFORE = "NOT_BEFORE"
    WINDOW = "WINDOW"


class ReviewOrigin(StrEnum):
    PLANNED_POINT = "PLANNED_POINT"
    REQUIRED_CONSTRAINT = "REQUIRED_CONSTRAINT"
    EVENT_TRIGGER = "EVENT_TRIGGER"
    EXPLICIT_INITIATION = "EXPLICIT_INITIATION"


class ReviewEpisodeStatus(StrEnum):
    OPEN = "OPEN"
    COMPLETED = "COMPLETED"


class ReviewOutcome(StrEnum):
    UNCHANGED_DECISION_CONFIRMED = "UNCHANGED_DECISION_CONFIRMED"
    SUCCESSOR_DECISION_PATH = "SUCCESSOR_DECISION_PATH"


class ReviewFocus(StrEnum):
    VALUE_REFRESH = "VALUE_REFRESH"
    RISK_REFRESH = "RISK_REFRESH"
    ADEQUACY_RELIANCE_RECONSIDERATION = "ADEQUACY_RELIANCE_RECONSIDERATION"
    INTEGRATION_REFRESH = "INTEGRATION_REFRESH"
    DECISION_CONFIRMATION = "DECISION_CONFIRMATION"
    DECISION_SUCCESSOR = "DECISION_SUCCESSOR"
    NO_SUBSTANTIVE_CHANGE = "NO_SUBSTANTIVE_CHANGE"


class ReviewSelectionKind(StrEnum):
    ONE = "ONE"
    ABSENT = "NOT ESTABLISHED"
    CONFLICT = "CONFLICT — UNRESOLVED"


@dataclass(frozen=True, slots=True)
class ReviewRecordFacts:
    record_id: RecordId
    version_id: RecordVersionId

    @classmethod
    def new(cls, record_id: RecordId | None = None) -> ReviewRecordFacts:
        return cls(record_id or RecordId.new(), RecordVersionId.new())


@dataclass(frozen=True, slots=True)
class PlannedReviewPointSpec:
    facts: ReviewRecordFacts
    review_at: datetime
    rationale: str
    source_basis_version_ids: tuple[RecordVersionId, ...]
    predecessor_version_id: RecordVersionId | None = None
    expected_current_version_id: RecordVersionId | None = None

    def __post_init__(self) -> None:
        require_utc(self.review_at)
        if not self.rationale.strip() or not self.source_basis_version_ids:
            raise ValueError("planned review point requires rationale and exact basis")
        if self.predecessor_version_id != self.expected_current_version_id:
            raise ValueError(
                "planned review predecessor must be the exact expected current Version"
            )


@dataclass(frozen=True, slots=True)
class EstablishPlannedReviewPointCommand:
    identity: CommandIdentity
    contract: SemanticContractRef
    context: ExactContextSet
    case_id: RecordId
    configuration_version_id: RecordVersionId
    decision_version_id: RecordVersionId
    review_purpose: str
    bounded_scope: str
    spec: PlannedReviewPointSpec
    responsibility_version_id: RecordVersionId
    assignment_version_id: RecordVersionId
    planning_authority_source_version_id: RecordVersionId | None
    decision_condition: bool
    effective_at: datetime
    knowledge_cutoff: datetime

    def __post_init__(self) -> None:
        require_utc(self.effective_at)
        require_utc(self.knowledge_cutoff)
        if not self.review_purpose.strip() or not self.bounded_scope.strip():
            raise ValueError("planned review purpose and bounded scope are required")
        if self.decision_condition and self.planning_authority_source_version_id is None:
            raise ValueError("a Decision-condition review point requires exact authority")


@dataclass(frozen=True, slots=True)
class EstablishRequiredReviewConstraintCommand:
    identity: CommandIdentity
    facts: ReviewRecordFacts
    contract: SemanticContractRef
    context: ExactContextSet
    case_id: RecordId
    configuration_version_id: RecordVersionId
    decision_version_id: RecordVersionId
    review_purpose: str
    bounded_scope: str
    source_version_id: RecordVersionId
    source_authority_version_id: RecordVersionId
    applicability_version_id: RecordVersionId
    operator: ReviewConstraintOperator
    window_start: datetime | None
    window_end: datetime | None
    limitations: tuple[str, ...]
    rationale: str
    responsibility_version_id: RecordVersionId
    assignment_version_id: RecordVersionId
    predecessor_version_id: RecordVersionId | None
    expected_current_version_id: RecordVersionId | None
    effective_at: datetime
    knowledge_cutoff: datetime

    def __post_init__(self) -> None:
        require_utc(self.effective_at)
        require_utc(self.knowledge_cutoff)
        if self.window_start is not None:
            require_utc(self.window_start)
        if self.window_end is not None:
            require_utc(self.window_end)
        if not self.review_purpose.strip() or not self.bounded_scope.strip() or not self.rationale:
            raise ValueError("required review constraint meaning is incomplete")
        if self.predecessor_version_id != self.expected_current_version_id:
            raise ValueError("constraint predecessor must be the exact expected current Version")
        if self.operator is ReviewConstraintOperator.BY and (
            self.window_start is not None or self.window_end is None
        ):
            raise ValueError("BY requires only an end")
        if self.operator is ReviewConstraintOperator.NOT_BEFORE and (
            self.window_start is None or self.window_end is not None
        ):
            raise ValueError("NOT_BEFORE requires only a start")
        if self.operator is ReviewConstraintOperator.WINDOW and (
            self.window_start is None
            or self.window_end is None
            or self.window_start >= self.window_end
        ):
            raise ValueError("WINDOW requires ordered start and end")


@dataclass(frozen=True, slots=True)
class WithdrawRequiredReviewConstraintCommand:
    identity: CommandIdentity
    facts: ReviewRecordFacts
    contract: SemanticContractRef
    context: ExactContextSet
    case_id: RecordId
    configuration_version_id: RecordVersionId
    constraint_version_id: RecordVersionId
    reason: str
    responsibility_version_id: RecordVersionId
    assignment_version_id: RecordVersionId
    source_authority_version_id: RecordVersionId
    effective_at: datetime
    knowledge_cutoff: datetime

    def __post_init__(self) -> None:
        require_utc(self.effective_at)
        require_utc(self.knowledge_cutoff)
        if not self.reason.strip():
            raise ValueError("constraint withdrawal reason is required")


@dataclass(frozen=True, slots=True)
class RecordEventReviewAttentionCommand:
    identity: CommandIdentity
    facts: ReviewRecordFacts
    contract: SemanticContractRef
    context: ExactContextSet
    case_id: RecordId
    configuration_version_id: RecordVersionId
    decision_version_id: RecordVersionId
    event_source_version_id: RecordVersionId
    review_purpose: str
    bounded_scope: str
    affected_focus: tuple[ReviewFocus, ...]
    reason: str
    responsibility_version_id: RecordVersionId
    assignment_version_id: RecordVersionId
    effective_at: datetime
    knowledge_cutoff: datetime

    def __post_init__(self) -> None:
        require_utc(self.effective_at)
        require_utc(self.knowledge_cutoff)
        if not self.affected_focus or not self.reason.strip():
            raise ValueError("event attention requires exact focused reason")


@dataclass(frozen=True, slots=True)
class BeginReviewEpisodeCommand:
    identity: CommandIdentity
    facts: ReviewRecordFacts
    contract: SemanticContractRef
    context: ExactContextSet
    case_id: RecordId
    configuration_version_id: RecordVersionId
    decision_version_id: RecordVersionId
    integration_version_id: RecordVersionId
    origin: ReviewOrigin
    origin_version_ids: tuple[RecordVersionId, ...]
    focused_scope: tuple[ReviewFocus, ...]
    prior_value_reliance_version_id: RecordVersionId
    prior_risk_reliance_version_id: RecordVersionId
    responsibility_version_id: RecordVersionId
    assignment_version_id: RecordVersionId
    expected_current_episode_version_id: RecordVersionId | None
    effective_at: datetime
    knowledge_cutoff: datetime

    def __post_init__(self) -> None:
        require_utc(self.effective_at)
        require_utc(self.knowledge_cutoff)
        if not self.origin_version_ids or not self.focused_scope:
            raise ValueError("Review Episode requires exact origin and focused scope")


@dataclass(frozen=True, slots=True)
class CompleteReviewEpisodeCommand:
    identity: CommandIdentity
    facts: ReviewRecordFacts
    contract: SemanticContractRef
    context: ExactContextSet
    case_id: RecordId
    configuration_version_id: RecordVersionId
    episode_version_id: RecordVersionId
    outcome: ReviewOutcome
    refreshed_result_version_ids: tuple[RecordVersionId, ...]
    continued_value_reliance_version_id: RecordVersionId
    continued_risk_reliance_version_id: RecordVersionId
    decision_confirmation_version_id: RecordVersionId | None
    successor_decision_version_id: RecordVersionId | None
    completion_rationale: str
    responsibility_version_id: RecordVersionId
    assignment_version_id: RecordVersionId
    next_planned_point: PlannedReviewPointSpec | None
    planning_responsibility_version_id: RecordVersionId | None
    planning_assignment_version_id: RecordVersionId | None
    effective_at: datetime
    knowledge_cutoff: datetime

    def __post_init__(self) -> None:
        require_utc(self.effective_at)
        require_utc(self.knowledge_cutoff)
        if not self.completion_rationale.strip():
            raise ValueError("review completion rationale is required")
        unchanged = self.decision_confirmation_version_id is not None
        successor = self.successor_decision_version_id is not None
        if unchanged == successor:
            raise ValueError("completion requires exactly one Decision continuation path")
        if unchanged != (self.outcome is ReviewOutcome.UNCHANGED_DECISION_CONFIRMED):
            raise ValueError("review outcome must match the exact Decision continuation path")
        planning = (
            self.planning_responsibility_version_id is not None
            and self.planning_assignment_version_id is not None
        )
        if (self.next_planned_point is not None) != planning:
            raise ValueError("optional next point requires its separate planning accountability")


@dataclass(frozen=True, slots=True)
class ReviewSelection:
    kind: ReviewSelectionKind
    version_ids: tuple[RecordVersionId, ...]
    status: str | None = None


@dataclass(frozen=True, slots=True)
class RequiredReviewWindow:
    kind: ReviewSelectionKind
    constraint_version_ids: tuple[RecordVersionId, ...]
    window_start: datetime | None
    window_end: datetime | None
    reason: str


@dataclass(frozen=True, slots=True)
class ReviewAttention:
    due: bool
    kinds: tuple[str, ...]
    source_version_ids: tuple[RecordVersionId, ...]
    substantive_change_inferred: bool = False
    priority_inferred: bool = False


def refreshed_lanes(focus: tuple[ReviewFocus, ...]) -> frozenset[AssessmentLane]:
    """Return only explicitly focused analytical lanes; never infer the other lane."""
    lanes: set[AssessmentLane] = set()
    if ReviewFocus.VALUE_REFRESH in focus:
        lanes.add(AssessmentLane.VALUE)
    if ReviewFocus.RISK_REFRESH in focus:
        lanes.add(AssessmentLane.RISK)
    return frozenset(lanes)
