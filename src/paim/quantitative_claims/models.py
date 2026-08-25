"""Typed optional quantitative claims for Gate 8 Slice F."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from enum import StrEnum

from paim.assessment_review.models import AssessmentLane, CommandIdentity
from paim.integrity.ids import RecordId, RecordVersionId
from paim.integrity.semantics import ExactContextSet, SemanticContractRef
from paim.integrity.time import require_utc


class QuantitativeClaimType(StrEnum):
    ESTIMATE_EXPECTATION = "ESTIMATE_EXPECTATION"
    TARGET_OBJECTIVE = "TARGET_OBJECTIVE"
    OBSERVED_RESULT = "OBSERVED_RESULT"
    THRESHOLD_CONSTRAINT = "THRESHOLD_CONSTRAINT"
    RISK_ESTIMATE = "RISK_ESTIMATE"
    COST_RESOURCE_MEASURE = "COST_RESOURCE_MEASURE"


class QuantityRepresentation(StrEnum):
    SCALAR = "SCALAR"
    RANGE = "RANGE"
    INTERVAL = "INTERVAL"
    DISTRIBUTION = "DISTRIBUTION"
    PROPORTION = "PROPORTION"
    RATE = "RATE"
    COUNT = "COUNT"
    CURRENCY = "CURRENCY"
    TIME = "TIME"
    OTHER_BOUNDED = "OTHER_BOUNDED"


class QuantityKind(StrEnum):
    ABSOLUTE_AMOUNT = "ABSOLUTE_AMOUNT"
    RATE = "RATE"
    RATIO = "RATIO"
    PERCENTAGE = "PERCENTAGE"
    COUNT = "COUNT"
    CONTINUOUS_MEASURE = "CONTINUOUS_MEASURE"
    CURRENCY = "CURRENCY"
    TIME = "TIME"


class TemporalBasis(StrEnum):
    POINT_IN_TIME = "POINT_IN_TIME"
    PERIODIC = "PERIODIC"
    CUMULATIVE = "CUMULATIVE"


class ComparisonState(StrEnum):
    MECHANICALLY_INCOMPATIBLE = "MECHANICALLY_INCOMPATIBLE"
    SUBSTANTIVE_COMPARABILITY_REQUIRES_JUDGMENT = "SUBSTANTIVE_COMPARABILITY_REQUIRES_JUDGMENT"
    COMPARABLE = "COMPARABLE"
    NOT_COMPARABLE = "NOT_COMPARABLE"


@dataclass(frozen=True, slots=True)
class ClaimFacts:
    record_id: RecordId
    version_id: RecordVersionId

    @classmethod
    def new(cls, record_id: RecordId | None = None) -> ClaimFacts:
        return cls(record_id or RecordId.new(), RecordVersionId.new())


@dataclass(frozen=True, slots=True)
class QuantityValue:
    representation: QuantityRepresentation
    central: str | None = None
    lower: str | None = None
    upper: str | None = None
    distribution: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        supplied = tuple(
            value for value in (self.central, self.lower, self.upper) if value is not None
        ) + tuple(value for pair in self.distribution for value in pair)
        if not supplied:
            raise ValueError("a quantitative claim requires a supplied quantity")
        for value in supplied:
            try:
                Decimal(value)
            except InvalidOperation as error:
                raise ValueError("quantity values must be exact decimal text") from error
        if self.representation in {
            QuantityRepresentation.RANGE,
            QuantityRepresentation.INTERVAL,
        }:
            if self.lower is None or self.upper is None or self.central is not None:
                raise ValueError("range/interval requires exact lower and upper only")
            if Decimal(self.lower) > Decimal(self.upper):
                raise ValueError("quantity lower bound exceeds upper bound")
        elif self.representation is QuantityRepresentation.DISTRIBUTION:
            if not self.distribution or any(
                value is not None for value in (self.central, self.lower, self.upper)
            ):
                raise ValueError("distribution requires only explicit point/weight pairs")
        elif self.central is None or any(value is not None for value in (self.lower, self.upper)):
            raise ValueError("non-range quantity requires one exact central value")


@dataclass(frozen=True, slots=True)
class QuantitativeClaimCommand:
    identity: CommandIdentity
    facts: ClaimFacts
    contract: SemanticContractRef
    context: ExactContextSet
    case_id: RecordId
    configuration_version_id: RecordVersionId
    lane: AssessmentLane
    claim_type: QuantitativeClaimType
    construct_id: str
    metric_id: str
    quantity_kind: QuantityKind
    quantity: QuantityValue
    unit: str
    currency: str | None
    scale: str
    direction: str
    population: str
    denominator: str | None
    temporal_basis: TemporalBasis
    period_start: datetime | None
    period_end: datetime | None
    horizon: str
    baseline: str
    gross_net: str
    nominal_real: str
    method_id: str
    assumptions: tuple[str, ...]
    uncertainty: str
    limitations: tuple[str, ...]
    source_version_ids: tuple[RecordVersionId, ...]
    applicability_version_ids: tuple[RecordVersionId, ...]
    assessment_version_id: RecordVersionId | None
    review_episode_version_id: RecordVersionId | None
    authority_source_version_id: RecordVersionId | None
    responsibility_version_id: RecordVersionId
    assignment_version_id: RecordVersionId
    expected_current_version_id: RecordVersionId | None
    effective_at: datetime
    knowledge_cutoff: datetime

    def __post_init__(self) -> None:
        require_utc(self.effective_at)
        require_utc(self.knowledge_cutoff)
        if self.period_start is not None:
            require_utc(self.period_start)
        if self.period_end is not None:
            require_utc(self.period_end)
        required = (
            self.construct_id,
            self.metric_id,
            self.unit,
            self.scale,
            self.direction,
            self.population,
            self.horizon,
            self.baseline,
            self.gross_net,
            self.nominal_real,
            self.method_id,
            self.uncertainty,
        )
        if any(not value.strip() for value in required):
            raise ValueError("material quantitative semantics must be explicit")
        if not self.source_version_ids or not self.applicability_version_ids:
            raise ValueError("exact provenance and Applicability are required")
        if self.temporal_basis is TemporalBasis.POINT_IN_TIME:
            if self.period_start is None or self.period_end is not None:
                raise ValueError("point-in-time claims require one exact point")
        elif (
            self.period_start is None
            or self.period_end is None
            or self.period_start >= self.period_end
        ):
            raise ValueError("periodic/cumulative claims require an ordered period")
        if self.quantity_kind is QuantityKind.CURRENCY and not self.currency:
            raise ValueError("currency claims require an exact currency basis")
        if self.claim_type is QuantitativeClaimType.THRESHOLD_CONSTRAINT and (
            self.authority_source_version_id is None
        ):
            raise ValueError("threshold constraints require an exact governing authority source")


@dataclass(frozen=True, slots=True)
class ComparabilityFacts:
    record_id: RecordId
    version_id: RecordVersionId

    @classmethod
    def new(cls, record_id: RecordId | None = None) -> ComparabilityFacts:
        return cls(record_id or RecordId.new(), RecordVersionId.new())


@dataclass(frozen=True, slots=True)
class EstablishComparabilityCommand:
    identity: CommandIdentity
    facts: ComparabilityFacts
    contract: SemanticContractRef
    context: ExactContextSet
    case_id: RecordId
    configuration_version_id: RecordVersionId
    left_claim_version_id: RecordVersionId
    right_claim_version_id: RecordVersionId
    outcome: ComparisonState
    rationale: str
    responsibility_version_id: RecordVersionId
    assignment_version_id: RecordVersionId
    authority_source_version_id: RecordVersionId
    expected_current_version_id: RecordVersionId | None
    effective_at: datetime
    knowledge_cutoff: datetime

    def __post_init__(self) -> None:
        require_utc(self.effective_at)
        require_utc(self.knowledge_cutoff)
        if self.outcome not in {ComparisonState.COMPARABLE, ComparisonState.NOT_COMPARABLE}:
            raise ValueError("practitioner comparability outcome must be explicit")
        if not self.rationale.strip() or self.left_claim_version_id == self.right_claim_version_id:
            raise ValueError("comparability requires two exact claims and rationale")


@dataclass(frozen=True, slots=True)
class ClaimSelection:
    state: str
    version_ids: tuple[RecordVersionId, ...]


@dataclass(frozen=True, slots=True)
class ClaimComparison:
    state: ComparisonState
    reasons: tuple[str, ...]
    left_claim_version_id: RecordVersionId
    right_claim_version_id: RecordVersionId
    comparability_version_id: RecordVersionId | None = None
    difference: str | None = None
    ratio: str | None = None
    percentage_change: str | None = None
    causality_inferred: bool = False
    decision_quality_inferred: bool = False
    score_inferred: bool = False
