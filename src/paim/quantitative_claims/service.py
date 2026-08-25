"""Atomic optional quantitative claims and bounded exact comparison."""

from __future__ import annotations

import json
from contextlib import AbstractContextManager
from dataclasses import fields, is_dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Protocol, cast

from paim.audit.models import ActorResolution, AuditFact
from paim.case_continuity.service import ContinuityAccessPolicy, ContinuityTransaction
from paim.integrity.commands import canonical_command_digest
from paim.integrity.ids import AuditId, EventId, RecordId, RecordVersionId, RelationshipId
from paim.integrity.records import (
    FinalizedRecordVersion,
    JsonValue,
    RelationshipType,
    StatusEvent,
    VersionRelationship,
    canonical_json,
)
from paim.integrity.selection import (
    SelectionAbsent,
    SelectionConflict,
    SelectionFound,
    SelectionQuery,
)
from paim.integrity.semantics import ExactContextSet, SemanticContractRef
from paim.integrity.time import Clock, EffectiveInterval, to_epoch_microseconds
from paim.persistence.ports import CommandOutcome, IdempotencyFact
from paim.quantitative_claims.models import (
    ClaimComparison,
    ClaimSelection,
    ComparisonState,
    EstablishComparabilityCommand,
    QuantitativeClaimCommand,
    QuantitativeClaimType,
    QuantityRepresentation,
)
from paim.responsibility.models import ObligationKind

type QuantitativeCommand = QuantitativeClaimCommand | EstablishComparabilityCommand


class QuantitativeClaimStore(Protocol):
    def semantic_transaction(self) -> AbstractContextManager[ContinuityTransaction]: ...
    def read_transaction(self) -> AbstractContextManager[ContinuityTransaction]: ...


class QuantitativeClaimConflict(RuntimeError):
    pass


class QuantitativeClaimAccessDenied(RuntimeError):
    def __init__(self) -> None:
        super().__init__("software access not established")


class QuantitativeClaimService:
    """Preserves exact numeric meaning without substituting numbers for judgment."""

    def __init__(
        self,
        store: QuantitativeClaimStore,
        clock: Clock,
        access: ContinuityAccessPolicy,
    ) -> None:
        self._store = store
        self._clock = clock
        self._access = access

    def record_claim(self, command: QuantitativeClaimCommand) -> CommandOutcome:
        action = "quantitative.claim.record"
        digest = self._digest(command)
        self._require_access(command, action)
        recorded_at = self._clock.now()
        with self._store.semantic_transaction() as tx:
            replay = self._replay(tx, command, digest)
            if replay is not None:
                return replay
            self._require_access(command, action)
            self._validate_claim_successor(tx, command)
            self._validate_case_context(tx, command, recorded_at)
            self._validate_accountability(
                tx,
                command,
                command.responsibility_version_id,
                command.assignment_version_id,
                ObligationKind.AUTHOR_QUANTITATIVE_CLAIM,
                recorded_at,
            )
            required = set(command.source_version_ids) | set(command.applicability_version_ids)
            required.update(
                {
                    command.configuration_version_id,
                    command.responsibility_version_id,
                    command.assignment_version_id,
                }
            )
            for optional in (
                command.assessment_version_id,
                command.review_episode_version_id,
                command.authority_source_version_id,
            ):
                if optional is not None:
                    required.add(optional)
            self._validate_sources(tx, command, required, recorded_at)
            self._validate_optional_links(tx, command, recorded_at)
            if command.authority_source_version_id is not None:
                self._validate_claim_authority(tx, command, recorded_at)
            self._ensure_contract_context(tx, command.contract, command.context, recorded_at)
            scope = self._claim_scope(command)
            selected = tx.select_current(
                SelectionQuery(
                    "quantitative-claim",
                    scope,
                    command.effective_at,
                    recorded_at,
                    command.facts.record_id,
                )
            )
            self._expect(selected, command.expected_current_version_id, "quantitative claim")
            content = cast(
                "dict[str, JsonValue]",
                {
                    "case_id": str(command.case_id),
                    "configuration_version_id": str(command.configuration_version_id),
                    "context_digest": command.context.digest,
                    "lane": command.lane.value,
                    "claim_type": command.claim_type.value,
                    "construct_id": command.construct_id,
                    "metric_id": command.metric_id,
                    "quantity_kind": command.quantity_kind.value,
                    "representation": command.quantity.representation.value,
                    "central": command.quantity.central,
                    "lower": command.quantity.lower,
                    "upper": command.quantity.upper,
                    "distribution": [list(pair) for pair in command.quantity.distribution],
                    "unit": command.unit,
                    "currency": command.currency,
                    "scale": command.scale,
                    "direction": command.direction,
                    "population": command.population,
                    "denominator": command.denominator,
                    "temporal_basis": command.temporal_basis.value,
                    "period_start": command.period_start.isoformat()
                    if command.period_start
                    else None,
                    "period_end": command.period_end.isoformat() if command.period_end else None,
                    "horizon": command.horizon,
                    "baseline": command.baseline,
                    "gross_net": command.gross_net,
                    "nominal_real": command.nominal_real,
                    "method_id": command.method_id,
                    "assumptions": list(command.assumptions),
                    "uncertainty": command.uncertainty,
                    "limitations": list(command.limitations),
                    "source_version_ids": self._ids(command.source_version_ids),
                    "applicability_version_ids": self._ids(command.applicability_version_ids),
                    "assessment_version_id": self._optional_id(command.assessment_version_id),
                    "review_episode_version_id": self._optional_id(
                        command.review_episode_version_id
                    ),
                    "authority_source_version_id": self._optional_id(
                        command.authority_source_version_id
                    ),
                    "optional_support_not_judgment": True,
                    "precision_preserved_as_supplied": True,
                },
            )
            self._add_version(
                tx,
                command.facts.record_id,
                command.facts.version_id,
                "quantitative-claim",
                scope,
                content,
                command,
                recorded_at,
            )
            if command.expected_current_version_id is None:
                tx.insert_projection(
                    "quantitative_claim_records", {"record_id": str(command.facts.record_id)}
                )
            tx.insert_projection(
                "quantitative_claim_versions",
                {
                    "version_id": str(command.facts.version_id),
                    "record_id": str(command.facts.record_id),
                    "case_id": str(command.case_id),
                    "configuration_version_id": str(command.configuration_version_id),
                    "context_digest": command.context.digest,
                    "lane": command.lane.value,
                    "claim_type": command.claim_type.value,
                    "construct_id": command.construct_id,
                    "metric_id": command.metric_id,
                    "quantity_kind": command.quantity_kind.value,
                    "representation": command.quantity.representation.value,
                    "central_value_text": command.quantity.central,
                    "lower_value_text": command.quantity.lower,
                    "upper_value_text": command.quantity.upper,
                    "distribution_json": json.dumps(command.quantity.distribution),
                    "unit": command.unit,
                    "currency": command.currency,
                    "scale": command.scale,
                    "direction": command.direction,
                    "population": command.population,
                    "denominator": command.denominator,
                    "temporal_basis": command.temporal_basis.value,
                    "period_start_us": to_epoch_microseconds(cast(datetime, command.period_start)),
                    "period_end_us": to_epoch_microseconds(command.period_end)
                    if command.period_end
                    else None,
                    "horizon": command.horizon,
                    "baseline": command.baseline,
                    "gross_net": command.gross_net,
                    "nominal_real": command.nominal_real,
                    "method_id": command.method_id,
                    "assumptions_json": json.dumps(command.assumptions),
                    "uncertainty": command.uncertainty,
                    "limitations_json": json.dumps(command.limitations),
                    "assessment_version_id": self._optional_id(command.assessment_version_id),
                    "review_episode_version_id": self._optional_id(
                        command.review_episode_version_id
                    ),
                    "authority_source_version_id": self._optional_id(
                        command.authority_source_version_id
                    ),
                    "responsibility_version_id": str(command.responsibility_version_id),
                    "assignment_version_id": str(command.assignment_version_id),
                    "predecessor_version_id": self._optional_id(
                        command.expected_current_version_id
                    ),
                    "knowledge_cutoff_us": to_epoch_microseconds(command.knowledge_cutoff),
                },
            )
            for role, values in (
                ("SOURCE", command.source_version_ids),
                ("APPLICABILITY", command.applicability_version_ids),
            ):
                for source_id in values:
                    tx.insert_projection(
                        "quantitative_claim_basis_links",
                        {
                            "claim_version_id": str(command.facts.version_id),
                            "source_version_id": str(source_id),
                            "link_role": role,
                        },
                    )
            relationships, statuses = self._successor_history(
                tx,
                command.expected_current_version_id,
                command.facts.version_id,
                command,
                recorded_at,
            )
            return self._finish(
                tx,
                command,
                digest,
                command.facts.record_id,
                (command.facts.version_id,),
                statuses,
                relationships,
                recorded_at,
                "QUANTITATIVE_CLAIM_RECORDED",
                ("OPTIONAL_SUPPORT_ONLY", "NO_SCORE_OR_JUDGMENT_SUBSTITUTION"),
            )

    def establish_comparability(self, command: EstablishComparabilityCommand) -> CommandOutcome:
        action = "quantitative.comparability.establish"
        digest = self._digest(command)
        self._require_access(command, action)
        recorded_at = self._clock.now()
        with self._store.semantic_transaction() as tx:
            replay = self._replay(tx, command, digest)
            if replay is not None:
                return replay
            self._require_access(command, action)
            self._validate_comparability_successor(tx, command)
            self._validate_case_context(tx, command, recorded_at)
            left = self._claim_row(tx, command.left_claim_version_id)
            right = self._claim_row(tx, command.right_claim_version_id)
            self._validate_pair_context(command, left, right)
            self._require_current(
                tx, command.left_claim_version_id, command.effective_at, recorded_at
            )
            self._require_current(
                tx, command.right_claim_version_id, command.effective_at, recorded_at
            )
            self._validate_accountability(
                tx,
                command,
                command.responsibility_version_id,
                command.assignment_version_id,
                ObligationKind.ESTABLISH_QUANTITATIVE_COMPARABILITY,
                recorded_at,
            )
            self._validate_comparability_authority(tx, command, recorded_at)
            sources = {
                command.left_claim_version_id,
                command.right_claim_version_id,
                command.responsibility_version_id,
                command.assignment_version_id,
                command.authority_source_version_id,
            }
            sources.update(self._claim_bases(tx, command.left_claim_version_id))
            sources.update(self._claim_bases(tx, command.right_claim_version_id))
            self._validate_sources(tx, command, sources, recorded_at)
            mismatches = self._mechanical_mismatches(left, right)
            if command.outcome is ComparisonState.COMPARABLE and mismatches:
                raise QuantitativeClaimConflict(
                    "mechanically incompatible claims cannot be declared comparable"
                )
            self._ensure_contract_context(tx, command.contract, command.context, recorded_at)
            scope = self._comparison_scope(
                command.left_claim_version_id, command.right_claim_version_id
            )
            selected = tx.select_current(
                SelectionQuery(
                    "quantitative-comparability",
                    scope,
                    command.effective_at,
                    recorded_at,
                    command.facts.record_id,
                )
            )
            self._expect(selected, command.expected_current_version_id, "comparability basis")
            content = cast(
                "dict[str, JsonValue]",
                {
                    "case_id": str(command.case_id),
                    "configuration_version_id": str(command.configuration_version_id),
                    "context_digest": command.context.digest,
                    "left_claim_version_id": str(command.left_claim_version_id),
                    "right_claim_version_id": str(command.right_claim_version_id),
                    "outcome": command.outcome.value,
                    "rationale": command.rationale,
                    "mechanical_dimensions_checked": list(self._comparison_dimensions()),
                    "substantive_judgment_explicit": True,
                },
            )
            self._add_version(
                tx,
                command.facts.record_id,
                command.facts.version_id,
                "quantitative-comparability",
                scope,
                content,
                command,
                recorded_at,
            )
            if command.expected_current_version_id is None:
                tx.insert_projection(
                    "quantitative_comparability_records",
                    {"record_id": str(command.facts.record_id)},
                )
            tx.insert_projection(
                "quantitative_comparability_versions",
                {
                    "version_id": str(command.facts.version_id),
                    "record_id": str(command.facts.record_id),
                    "case_id": str(command.case_id),
                    "configuration_version_id": str(command.configuration_version_id),
                    "context_digest": command.context.digest,
                    "left_claim_version_id": str(command.left_claim_version_id),
                    "right_claim_version_id": str(command.right_claim_version_id),
                    "outcome": command.outcome.value,
                    "rationale": command.rationale,
                    "responsibility_version_id": str(command.responsibility_version_id),
                    "assignment_version_id": str(command.assignment_version_id),
                    "authority_source_version_id": str(command.authority_source_version_id),
                    "predecessor_version_id": self._optional_id(
                        command.expected_current_version_id
                    ),
                    "knowledge_cutoff_us": to_epoch_microseconds(command.knowledge_cutoff),
                },
            )
            relationships, statuses = self._successor_history(
                tx,
                command.expected_current_version_id,
                command.facts.version_id,
                command,
                recorded_at,
            )
            return self._finish(
                tx,
                command,
                digest,
                command.facts.record_id,
                (command.facts.version_id,),
                statuses,
                relationships,
                recorded_at,
                "QUANTITATIVE_COMPARABILITY_ESTABLISHED",
                ("EXPLICIT_PRACTITIONER_JUDGMENT", "NO_LABEL_ONLY_EQUIVALENCE"),
            )

    def select_claim(
        self,
        *,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        configuration_version_id: RecordVersionId,
        context_digest: str,
        lane: str,
        claim_type: str,
        construct_id: str,
        metric_id: str,
        effective_at: datetime,
        known_at: datetime,
    ) -> ClaimSelection:
        scope = self._claim_scope_values(
            case_id,
            configuration_version_id,
            context_digest,
            lane,
            claim_type,
            construct_id,
            metric_id,
        )
        with self._store.read_transaction() as tx:
            selected = tx.select_current(
                SelectionQuery("quantitative-claim", scope, effective_at, known_at)
            )
            if isinstance(selected, SelectionAbsent):
                return ClaimSelection("ABSENT", ())
            assert isinstance(selected, (SelectionFound, SelectionConflict))
            candidates = (
                (selected.candidate,)
                if isinstance(selected, SelectionFound)
                else selected.candidates
            )
            visible: list[RecordVersionId] = []
            hidden = False
            for candidate in candidates:
                bases = self._claim_bases(tx, candidate.version_id) | {candidate.version_id}
                if all(
                    self._source_visible(principal_id, actor_id, case_id, source_id)
                    for source_id in bases
                ):
                    visible.append(candidate.version_id)
                else:
                    hidden = True
            if hidden:
                return ClaimSelection("NOT_SAFELY_AVAILABLE", ())
            return ClaimSelection("ONE" if len(visible) == 1 else "CONFLICT", tuple(visible))

    def compare(
        self,
        *,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        left_claim_version_id: RecordVersionId,
        right_claim_version_id: RecordVersionId,
        effective_at: datetime,
        known_at: datetime,
    ) -> ClaimComparison:
        with self._store.read_transaction() as tx:
            left_bases = self._claim_bases(tx, left_claim_version_id) | {left_claim_version_id}
            right_bases = self._claim_bases(tx, right_claim_version_id) | {right_claim_version_id}
            if not all(
                self._source_visible(principal_id, actor_id, case_id, version_id)
                for version_id in left_bases | right_bases
            ):
                raise QuantitativeClaimAccessDenied()
            left = self._claim_row(tx, left_claim_version_id)
            right = self._claim_row(tx, right_claim_version_id)
            self._require_knowable(tx, left_claim_version_id, effective_at, known_at)
            self._require_knowable(tx, right_claim_version_id, effective_at, known_at)
            if left["case_id"] != str(case_id) or right["case_id"] != str(case_id):
                raise QuantitativeClaimAccessDenied()
            mismatches = self._mechanical_mismatches(left, right)
            if mismatches:
                return ClaimComparison(
                    ComparisonState.MECHANICALLY_INCOMPATIBLE,
                    mismatches,
                    left_claim_version_id,
                    right_claim_version_id,
                )
            scope = self._comparison_scope(left_claim_version_id, right_claim_version_id)
            selected = tx.select_current(
                SelectionQuery("quantitative-comparability", scope, effective_at, known_at)
            )
            if not isinstance(selected, SelectionFound):
                return ClaimComparison(
                    ComparisonState.SUBSTANTIVE_COMPARABILITY_REQUIRES_JUDGMENT,
                    ("mechanical compatibility does not establish substantive comparability",),
                    left_claim_version_id,
                    right_claim_version_id,
                )
            basis_id = selected.candidate.version_id
            basis = tx.projection_rows(
                "quantitative_comparability_versions", version_id=str(basis_id)
            )
            if len(basis) != 1:
                raise QuantitativeClaimAccessDenied()
            self._require_knowable(tx, basis_id, effective_at, known_at)
            self._require_current(tx, basis_id, effective_at, known_at)
            basis_row = basis[0]
            if (
                basis_row["left_claim_version_id"] != str(left_claim_version_id)
                or basis_row["right_claim_version_id"] != str(right_claim_version_id)
                or basis_row["case_id"] != str(case_id)
                or basis_row["configuration_version_id"] != left["configuration_version_id"]
                or basis_row["context_digest"] != left["context_digest"]
                or basis_row["configuration_version_id"] != right["configuration_version_id"]
                or basis_row["context_digest"] != right["context_digest"]
                or basis_row["outcome"]
                not in {
                    ComparisonState.COMPARABLE.value,
                    ComparisonState.NOT_COMPARABLE.value,
                }
            ):
                raise QuantitativeClaimConflict(
                    "comparability basis does not match the exact requested pair and context"
                )
            basis_sources = {
                basis_id,
                RecordVersionId.parse(str(basis_row["responsibility_version_id"])),
                RecordVersionId.parse(str(basis_row["assignment_version_id"])),
                RecordVersionId.parse(str(basis_row["authority_source_version_id"])),
            }
            self._expand_assignment_sources(tx, basis_sources)
            if not all(
                self._source_visible(principal_id, actor_id, case_id, version_id)
                for version_id in basis_sources
            ):
                raise QuantitativeClaimAccessDenied()
            if basis_row["outcome"] == ComparisonState.NOT_COMPARABLE.value:
                return ClaimComparison(
                    ComparisonState.NOT_COMPARABLE,
                    (str(basis_row["rationale"]),),
                    left_claim_version_id,
                    right_claim_version_id,
                    basis_id,
                )
            if left["representation"] != QuantityRepresentation.SCALAR.value:
                return ClaimComparison(
                    ComparisonState.COMPARABLE,
                    (
                        "comparable non-scalar claims retain exact values without "
                        "invented arithmetic",
                    ),
                    left_claim_version_id,
                    right_claim_version_id,
                    basis_id,
                )
            left_value = Decimal(str(left["central_value_text"]))
            right_value = Decimal(str(right["central_value_text"]))
            difference = right_value - left_value
            ratio = None if left_value == 0 else right_value / left_value
            percentage = None if left_value == 0 else (difference / left_value) * Decimal("100")
            reasons: tuple[str, ...] = (
                "exact arithmetic only; no causal, success, adequacy, or Decision inference",
            )
            if left_value == 0:
                reasons += ("ratio and percentage change unavailable because baseline is zero",)
            return ClaimComparison(
                ComparisonState.COMPARABLE,
                reasons,
                left_claim_version_id,
                right_claim_version_id,
                basis_id,
                self._decimal_text(difference),
                self._decimal_text(ratio) if ratio is not None else None,
                self._decimal_text(percentage) if percentage is not None else None,
            )

    @staticmethod
    def _claim_row(tx: ContinuityTransaction, version_id: RecordVersionId) -> dict[str, object]:
        rows = tx.projection_rows("quantitative_claim_versions", version_id=str(version_id))
        if len(rows) != 1:
            raise QuantitativeClaimConflict("exact quantitative claim is unavailable")
        return rows[0]

    @staticmethod
    def _claim_bases(
        tx: ContinuityTransaction, version_id: RecordVersionId
    ) -> set[RecordVersionId]:
        return {
            RecordVersionId.parse(str(row["source_version_id"]))
            for row in tx.projection_rows(
                "quantitative_claim_basis_links", claim_version_id=str(version_id)
            )
        }

    @classmethod
    def _mechanical_mismatches(
        cls, left: dict[str, object], right: dict[str, object]
    ) -> tuple[str, ...]:
        mismatches = tuple(
            f"{dimension} differs"
            for dimension in cls._comparison_dimensions()
            if left.get(dimension) != right.get(dimension)
        )
        if (
            str(left["claim_type"])
            not in {
                QuantitativeClaimType.ESTIMATE_EXPECTATION.value,
                QuantitativeClaimType.TARGET_OBJECTIVE.value,
            }
            or str(right["claim_type"]) != QuantitativeClaimType.OBSERVED_RESULT.value
        ):
            mismatches += (
                "comparison orientation requires expectation/target left and observed result right",
            )
        return mismatches

    @staticmethod
    def _validate_claim_successor(
        tx: ContinuityTransaction, command: QuantitativeClaimCommand
    ) -> None:
        predecessor_id = command.expected_current_version_id
        if predecessor_id is None:
            return
        predecessor = tx.get_version(predecessor_id)
        rows = tx.projection_rows("quantitative_claim_versions", version_id=str(predecessor_id))
        if (
            predecessor is None
            or len(rows) != 1
            or predecessor.record_id != command.facts.record_id
            or predecessor.family != "quantitative-claim"
            or predecessor.scope != QuantitativeClaimService._claim_scope(command)
        ):
            raise QuantitativeClaimConflict(
                "claim successor must preserve one exact Record and semantic identity"
            )
        row = rows[0]
        expected_identity: dict[str, object] = {
            "case_id": str(command.case_id),
            "configuration_version_id": str(command.configuration_version_id),
            "context_digest": command.context.digest,
            "lane": command.lane.value,
            "claim_type": command.claim_type.value,
            "construct_id": command.construct_id,
            "metric_id": command.metric_id,
            "quantity_kind": command.quantity_kind.value,
            "representation": command.quantity.representation.value,
            "unit": command.unit,
            "currency": command.currency,
            "scale": command.scale,
            "direction": command.direction,
            "population": command.population,
            "denominator": command.denominator,
            "temporal_basis": command.temporal_basis.value,
            "horizon": command.horizon,
            "baseline": command.baseline,
            "gross_net": command.gross_net,
            "nominal_real": command.nominal_real,
            "method_id": command.method_id,
            "assessment_version_id": QuantitativeClaimService._optional_id(
                command.assessment_version_id
            ),
            "review_episode_version_id": QuantitativeClaimService._optional_id(
                command.review_episode_version_id
            ),
        }
        if any(row[field] != value for field, value in expected_identity.items()):
            raise QuantitativeClaimConflict(
                "claim successor cannot change identity-defining semantics"
            )

    @staticmethod
    def _validate_comparability_successor(
        tx: ContinuityTransaction, command: EstablishComparabilityCommand
    ) -> None:
        predecessor_id = command.expected_current_version_id
        if predecessor_id is None:
            return
        predecessor = tx.get_version(predecessor_id)
        rows = tx.projection_rows(
            "quantitative_comparability_versions", version_id=str(predecessor_id)
        )
        if (
            predecessor is None
            or len(rows) != 1
            or predecessor.record_id != command.facts.record_id
            or predecessor.family != "quantitative-comparability"
            or predecessor.scope
            != QuantitativeClaimService._comparison_scope(
                command.left_claim_version_id, command.right_claim_version_id
            )
            or rows[0]["left_claim_version_id"] != str(command.left_claim_version_id)
            or rows[0]["right_claim_version_id"] != str(command.right_claim_version_id)
            or rows[0]["case_id"] != str(command.case_id)
            or rows[0]["configuration_version_id"] != str(command.configuration_version_id)
            or rows[0]["context_digest"] != command.context.digest
        ):
            raise QuantitativeClaimConflict(
                "comparability successor must preserve the exact oriented pair and context"
            )

    @staticmethod
    def _comparison_dimensions() -> tuple[str, ...]:
        return (
            "case_id",
            "configuration_version_id",
            "context_digest",
            "lane",
            "construct_id",
            "metric_id",
            "quantity_kind",
            "representation",
            "unit",
            "currency",
            "scale",
            "direction",
            "population",
            "denominator",
            "temporal_basis",
            "period_start_us",
            "period_end_us",
            "horizon",
            "baseline",
            "gross_net",
            "nominal_real",
            "method_id",
        )

    @staticmethod
    def _validate_pair_context(
        command: EstablishComparabilityCommand,
        left: dict[str, object],
        right: dict[str, object],
    ) -> None:
        expected = (
            str(command.case_id),
            str(command.configuration_version_id),
            command.context.digest,
        )
        for row in (left, right):
            if (row["case_id"], row["configuration_version_id"], row["context_digest"]) != expected:
                raise QuantitativeClaimConflict("claim pair does not match exact governed context")

    def _validate_case_context(
        self,
        tx: ContinuityTransaction,
        command: QuantitativeCommand,
        known_at: datetime,
    ) -> None:
        records = tx.projection_rows("case_continuity_status_records", case_id=str(command.case_id))
        if len(records) != 1:
            raise QuantitativeClaimConflict("exact prospective OPEN Case is not established")
        selected = tx.select_current(
            SelectionQuery(
                "case-continuity-status",
                f"case:{command.case_id}",
                command.effective_at,
                known_at,
                RecordId.parse(str(records[0]["record_id"])),
            )
        )
        if not isinstance(selected, SelectionFound):
            raise QuantitativeClaimConflict("Case continuity is absent or conflicting")
        statuses = tx.projection_rows(
            "case_continuity_status_versions", version_id=str(selected.candidate.version_id)
        )
        governing = tx.select_current(
            SelectionQuery(
                "governing-configuration", f"case:{command.case_id}", command.effective_at, known_at
            )
        )
        if (
            len(statuses) != 1
            or statuses[0]["status"] != "OPEN"
            or not isinstance(governing, SelectionFound)
        ):
            raise QuantitativeClaimConflict("prospective Case/configuration is not current")
        rows = tx.projection_rows(
            "governing_configuration_designations", version_id=str(governing.candidate.version_id)
        )
        semantics = tx.projection_rows(
            "record_version_semantics", version_id=str(command.configuration_version_id)
        )
        if (
            len(rows) != 1
            or rows[0]["configuration_version_id"] != str(command.configuration_version_id)
            or len(semantics) != 1
            or semantics[0]["context_digest"] != command.context.digest
        ):
            raise QuantitativeClaimConflict("exact governing Configuration/context mismatch")

    def _validate_optional_links(
        self,
        tx: ContinuityTransaction,
        command: QuantitativeClaimCommand,
        known_at: datetime,
    ) -> None:
        if command.assessment_version_id is not None:
            rows = tx.projection_rows(
                "assessment_candidate_versions", version_id=str(command.assessment_version_id)
            )
            if (
                len(rows) != 1
                or rows[0]["case_id"] != str(command.case_id)
                or rows[0]["configuration_version_id"] != str(command.configuration_version_id)
                or rows[0]["context_digest"] != command.context.digest
                or rows[0]["lane"] != command.lane.value
            ):
                raise QuantitativeClaimConflict("assessment link does not match exact lane/context")
            self._require_current(tx, command.assessment_version_id, command.effective_at, known_at)
        if command.review_episode_version_id is not None:
            rows = tx.projection_rows(
                "review_episode_versions", version_id=str(command.review_episode_version_id)
            )
            if (
                len(rows) != 1
                or rows[0]["case_id"] != str(command.case_id)
                or rows[0]["configuration_version_id"] != str(command.configuration_version_id)
                or rows[0]["context_digest"] != command.context.digest
            ):
                raise QuantitativeClaimConflict("Review Episode link does not match exact context")
            self._require_current(
                tx, command.review_episode_version_id, command.effective_at, known_at
            )

    def _validate_sources(
        self,
        tx: ContinuityTransaction,
        command: QuantitativeCommand,
        version_ids: set[RecordVersionId],
        known_at: datetime,
    ) -> None:
        self._expand_assignment_sources(tx, version_ids)
        for version_id in version_ids:
            if tx.get_version(version_id) is None or not self._source_visible(
                str(command.identity.principal_id),
                command.identity.actor_id,
                command.case_id,
                version_id,
            ):
                raise QuantitativeClaimAccessDenied()
        for version_id in set(version_ids) - {
            command.responsibility_version_id,
            command.assignment_version_id,
        }:
            self._require_current(tx, version_id, command.effective_at, known_at)

    def _validate_accountability(
        self,
        tx: ContinuityTransaction,
        command: QuantitativeCommand,
        responsibility_id: RecordVersionId,
        assignment_id: RecordVersionId,
        obligation: ObligationKind,
        known_at: datetime,
    ) -> None:
        responsibilities = tx.projection_rows(
            "responsibility_versions", version_id=str(responsibility_id)
        )
        assignments = tx.projection_rows(
            "responsibility_assignment_versions", version_id=str(assignment_id)
        )
        if len(responsibilities) != 1 or len(assignments) != 1:
            raise QuantitativeClaimConflict("exact Responsibility/assignment is not established")
        responsibility, assignment = responsibilities[0], assignments[0]
        if (
            responsibility["obligation_kind"] != obligation.value
            or responsibility["owning_case_id"] != str(command.case_id)
            or responsibility["context_digest"] != command.context.digest
            or assignment["responsibility_version_id"] != str(responsibility_id)
            or assignment["actor_id"] != str(command.identity.actor_id)
            or assignment["state"] != "ASSIGNED"
        ):
            raise QuantitativeClaimConflict("accountability does not match exact quantitative act")
        self._require_current(tx, responsibility_id, command.effective_at, known_at)
        self._require_current(tx, assignment_id, command.effective_at, known_at)
        eligible: list[dict[str, object]] = []
        for row in tx.projection_rows(
            "responsibility_assignment_versions",
            signature_digest=str(responsibility["signature_digest"]),
        ):
            try:
                self._require_current(
                    tx,
                    RecordVersionId.parse(str(row["version_id"])),
                    command.effective_at,
                    known_at,
                )
            except QuantitativeClaimConflict:
                continue
            if row["state"] == "ASSIGNED":
                eligible.append(row)
        if len(eligible) != 1 or eligible[0]["version_id"] != str(assignment_id):
            raise QuantitativeClaimConflict("quantitative Responsibility vacancy or conflict")
        basis = tx.projection_rows(
            "assignment_basis_versions", version_id=str(assignment["assignment_basis_version_id"])
        )
        if len(basis) != 1 or basis[0]["state"] != "ACTIVE":
            raise QuantitativeClaimConflict("exact Assignment Basis is not active")
        source_id = RecordVersionId.parse(str(basis[0]["basis_source_version_id"]))
        self._require_current(tx, source_id, command.effective_at, known_at)
        source = tx.get_version(source_id)
        authority = source.content.get("assignment_authority") if source else None
        if (
            not isinstance(authority, dict)
            or obligation.value
            not in cast(list[str], authority.get("allowed_obligation_kinds", []))
            or str(command.case_id) not in cast(list[str], authority.get("allowed_case_ids", []))
            or str(responsibility["signature_digest"])
            not in cast(list[str], authority.get("allowed_signature_digests", []))
            or authority.get("context_digest") != command.context.digest
        ):
            raise QuantitativeClaimConflict(
                "Assignment Basis does not authorize exact quantitative act"
            )

    def _validate_claim_authority(
        self, tx: ContinuityTransaction, command: QuantitativeClaimCommand, known_at: datetime
    ) -> None:
        assert command.authority_source_version_id is not None
        self._validate_authority(
            tx,
            command,
            command.authority_source_version_id,
            "AUTHOR_THRESHOLD_CONSTRAINT",
            known_at,
        )

    def _validate_comparability_authority(
        self, tx: ContinuityTransaction, command: EstablishComparabilityCommand, known_at: datetime
    ) -> None:
        self._validate_authority(
            tx,
            command,
            command.authority_source_version_id,
            "ESTABLISH_QUANTITATIVE_COMPARABILITY",
            known_at,
        )

    def _validate_authority(
        self,
        tx: ContinuityTransaction,
        command: QuantitativeCommand,
        version_id: RecordVersionId,
        action: str,
        known_at: datetime,
    ) -> None:
        self._require_current(tx, version_id, command.effective_at, known_at)
        source = tx.get_version(version_id)
        authority = source.content.get("quantitative_claim_authority") if source else None
        if (
            not isinstance(authority, dict)
            or authority.get("actor_id") != str(command.identity.actor_id)
            or action not in cast(list[str], authority.get("allowed_actions", []))
            or str(command.case_id) not in cast(list[str], authority.get("allowed_case_ids", []))
            or authority.get("context_digest") != command.context.digest
        ):
            raise QuantitativeClaimConflict(
                "exact substantive quantitative authority is not established"
            )

    def _source_visible(
        self, principal_id: str, actor_id: RecordId, case_id: RecordId, version_id: RecordVersionId
    ) -> bool:
        return self._access.authorize(
            principal_id=principal_id,
            actor_id=str(actor_id),
            action="source.read",
            case_id=case_id,
            write=False,
            source_version_id=version_id,
            source_family=None,
        )

    def _require_access(self, command: QuantitativeCommand, action: str) -> None:
        if not self._access.authorize(
            principal_id=str(command.identity.principal_id),
            actor_id=str(command.identity.actor_id),
            action=action,
            case_id=command.case_id,
            write=True,
        ):
            raise QuantitativeClaimAccessDenied()

    @staticmethod
    def _require_current(
        tx: ContinuityTransaction,
        version_id: RecordVersionId,
        effective_at: datetime,
        known_at: datetime,
    ) -> None:
        version = tx.get_version(version_id)
        if version is None:
            raise QuantitativeClaimConflict("exact Version unavailable")
        selected = tx.select_current(
            SelectionQuery(version.family, version.scope, effective_at, known_at, version.record_id)
        )
        if not isinstance(selected, SelectionFound) or selected.candidate.version_id != version_id:
            raise QuantitativeClaimConflict("exact Version is stale or conflicting")

    @staticmethod
    def _require_knowable(
        tx: ContinuityTransaction,
        version_id: RecordVersionId,
        effective_at: datetime,
        known_at: datetime,
    ) -> None:
        version = tx.get_version(version_id)
        if (
            version is None
            or version.recorded_at > known_at
            or not version.effective.contains(effective_at)
        ):
            raise QuantitativeClaimConflict("exact claim was not knowable at the requested cutoff")

    @staticmethod
    def _expect(selected: object, expected: RecordVersionId | None, subject: str) -> None:
        if expected is None and not isinstance(selected, SelectionAbsent):
            raise QuantitativeClaimConflict(f"expected absent {subject}")
        if expected is not None and not (
            isinstance(selected, SelectionFound) and selected.candidate.version_id == expected
        ):
            raise QuantitativeClaimConflict(
                f"stale exact {subject} predecessor; no retarget permitted"
            )

    @staticmethod
    def _replay(
        tx: ContinuityTransaction, command: QuantitativeCommand, digest: str
    ) -> CommandOutcome | None:
        fact = tx.get_idempotency(
            str(command.identity.idempotency_scope), str(command.identity.idempotency_key)
        )
        if fact is None:
            return None
        if fact.digest != digest:
            raise QuantitativeClaimConflict("IDEMPOTENCY KEY REUSE CONFLICT")
        return fact.outcome

    @staticmethod
    def _add_version(
        tx: ContinuityTransaction,
        record_id: RecordId,
        version_id: RecordVersionId,
        family: str,
        scope: str,
        content: dict[str, JsonValue],
        command: QuantitativeCommand,
        recorded_at: datetime,
    ) -> None:
        tx.add_version(
            FinalizedRecordVersion(
                record_id,
                version_id,
                family,
                scope,
                canonical_json(content),
                recorded_at,
                EffectiveInterval(command.effective_at),
                str(command.identity.actor_id),
            )
        )
        tx.insert_projection(
            "record_version_semantics",
            {
                "version_id": str(version_id),
                "contract_key": command.contract.key,
                "context_digest": command.context.digest,
                "consumer_id": "gate8-slice-f",
                "adapter_key": None,
            },
        )

    @staticmethod
    def _successor_history(
        tx: ContinuityTransaction,
        predecessor: RecordVersionId | None,
        successor: RecordVersionId,
        command: QuantitativeCommand,
        recorded_at: datetime,
    ) -> tuple[tuple[RelationshipId, ...], tuple[EventId, ...]]:
        if predecessor is None:
            return (), ()
        before, after = tx.get_version(predecessor), tx.get_version(successor)
        if (
            before is None
            or after is None
            or before.record_id != after.record_id
            or before.family != after.family
            or before.scope != after.scope
        ):
            raise QuantitativeClaimConflict(
                "succession requires one exact Record, family, and scope"
            )
        relationship = VersionRelationship(
            RelationshipId.new(),
            predecessor,
            successor,
            RelationshipType.SUPERSESSION,
            recorded_at,
            "exact quantitative successor",
        )
        status = StatusEvent(
            EventId.new(),
            predecessor,
            "CURRENT",
            "SUPERSEDED",
            recorded_at,
            command.effective_at,
            str(command.identity.actor_id),
            "exact quantitative successor",
        )
        tx.add_relationship(relationship)
        tx.add_status_event(status)
        tx.insert_projection(
            "version_relationship_semantics",
            {
                "relationship_id": str(relationship.relationship_id),
                "contract_key": command.contract.key,
                "context_digest": command.context.digest,
            },
        )
        tx.insert_projection(
            "status_event_semantics",
            {
                "event_id": str(status.event_id),
                "contract_key": command.contract.key,
                "context_digest": command.context.digest,
            },
        )
        return (relationship.relationship_id,), (status.event_id,)

    @staticmethod
    def _finish(
        tx: ContinuityTransaction,
        command: QuantitativeCommand,
        digest: str,
        record_id: RecordId,
        versions: tuple[RecordVersionId, ...],
        statuses: tuple[EventId, ...],
        relationships: tuple[RelationshipId, ...],
        recorded_at: datetime,
        action: str,
        reasons: tuple[str, ...],
    ) -> CommandOutcome:
        audit = AuditFact(
            AuditId.new(),
            str(command.identity.principal_id),
            str(command.identity.actor_id),
            ActorResolution.PROVIDED,
            action,
            "COMMITTED",
            command.identity.command_id,
            str(command.identity.idempotency_scope),
            str(command.identity.idempotency_key),
            None,
            None,
            record_id,
            versions,
            "EXACT_CONTEXT_AND_EXPECTED_BASIS",
            command.context.digest,
            command.effective_at,
            recorded_at,
            reasons,
            digest,
        )
        tx.add_audit(audit)
        outcome = CommandOutcome(
            str(command.identity.command_id),
            str(record_id),
            tuple(str(value) for value in versions),
            tuple(str(value) for value in statuses),
            tuple(str(value) for value in relationships),
            str(audit.audit_id),
        )
        tx.add_idempotency(
            IdempotencyFact(
                str(command.identity.idempotency_scope),
                str(command.identity.idempotency_key),
                digest,
                str(command.identity.command_id),
                outcome,
                recorded_at,
            )
        )
        return outcome

    @staticmethod
    def _ensure_contract_context(
        tx: ContinuityTransaction,
        contract: SemanticContractRef,
        context: ExactContextSet,
        recorded_at: datetime,
    ) -> None:
        if not tx.projection_rows("semantic_contracts", contract_key=contract.key):
            tx.insert_projection(
                "semantic_contracts",
                {
                    "contract_key": contract.key,
                    "contract_id": contract.contract_id,
                    "contract_version": contract.version,
                    "owner": "PAIM",
                    "interpretation_source": "docs/system/specifications",
                    "recorded_at_us": to_epoch_microseconds(recorded_at),
                },
            )
        if not tx.projection_rows("exact_context_sets", context_digest=context.digest):
            tx.insert_projection(
                "exact_context_sets",
                {
                    "context_digest": context.digest,
                    "canonical_json": context.canonical_json,
                    "recorded_at_us": to_epoch_microseconds(recorded_at),
                },
            )
            for member in context.members:
                tx.insert_projection(
                    "exact_context_members",
                    {
                        "context_digest": context.digest,
                        "slot": member.slot,
                        "member_kind": member.kind.value,
                        "identity": member.identity,
                    },
                )
        for family in ("quantitative-claim", "quantitative-comparability"):
            if not tx.projection_rows(
                "semantic_contract_families", contract_key=contract.key, record_family=family
            ):
                tx.insert_projection(
                    "semantic_contract_families",
                    {"contract_key": contract.key, "record_family": family},
                )

    @staticmethod
    def _expand_assignment_sources(
        tx: ContinuityTransaction, required: set[RecordVersionId]
    ) -> None:
        for version_id in tuple(required):
            assignments = tx.projection_rows(
                "responsibility_assignment_versions", version_id=str(version_id)
            )
            if not assignments:
                continue
            basis_id = RecordVersionId.parse(str(assignments[0]["assignment_basis_version_id"]))
            required.add(basis_id)
            bases = tx.projection_rows("assignment_basis_versions", version_id=str(basis_id))
            if len(bases) == 1:
                required.add(RecordVersionId.parse(str(bases[0]["basis_source_version_id"])))

    @staticmethod
    def _claim_scope(command: QuantitativeClaimCommand) -> str:
        return QuantitativeClaimService._claim_scope_values(
            command.case_id,
            command.configuration_version_id,
            command.context.digest,
            command.lane.value,
            command.claim_type.value,
            command.construct_id,
            command.metric_id,
        )

    @staticmethod
    def _claim_scope_values(
        case_id: RecordId,
        configuration_version_id: RecordVersionId,
        context_digest: str,
        lane: str,
        claim_type: str,
        construct_id: str,
        metric_id: str,
    ) -> str:
        return (
            f"quantitative:case:{case_id}:configuration:{configuration_version_id}:"
            f"context:{context_digest}:lane:{lane}:role:{claim_type}:"
            f"construct:{construct_id}:metric:{metric_id}"
        )

    @staticmethod
    def _comparison_scope(left: RecordVersionId, right: RecordVersionId) -> str:
        return f"quantitative-comparison:left:{left}:right:{right}"

    @staticmethod
    def _ids(values: tuple[RecordVersionId, ...]) -> list[str]:
        return [str(value) for value in values]

    @staticmethod
    def _optional_id(value: RecordVersionId | None) -> str | None:
        return str(value) if value is not None else None

    @staticmethod
    def _decimal_text(value: Decimal) -> str:
        return format(value, "f")

    @classmethod
    def _digest(cls, command: QuantitativeCommand) -> str:
        return canonical_command_digest(cast("dict[str, JsonValue]", cls._jsonable(command)))

    @classmethod
    def _jsonable(cls, value: object) -> JsonValue:
        if isinstance(value, Enum):
            return cls._jsonable(value.value)
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, (RecordId, RecordVersionId)):
            return str(value)
        if is_dataclass(value) and not isinstance(value, type):
            return {
                field.name: cls._jsonable(getattr(value, field.name)) for field in fields(value)
            }
        if isinstance(value, dict):
            return {str(key): cls._jsonable(item) for key, item in value.items()}
        if isinstance(value, (tuple, list)):
            return [cls._jsonable(item) for item in value]
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        return str(value)
