"""Atomic continuing-review commands and access-first selectors for Gate 8 Slice E."""

from __future__ import annotations

import json
from contextlib import AbstractContextManager
from dataclasses import fields, is_dataclass
from datetime import datetime
from enum import Enum
from typing import Protocol, cast

from paim.audit.models import ActorResolution, AuditFact
from paim.case_continuity.service import ContinuityAccessPolicy, ContinuityTransaction
from paim.continuing_review.models import (
    BeginReviewEpisodeCommand,
    CompleteReviewEpisodeCommand,
    EstablishPlannedReviewPointCommand,
    EstablishRequiredReviewConstraintCommand,
    PlannedReviewPointSpec,
    RecordEventReviewAttentionCommand,
    RequiredReviewWindow,
    ReviewAttention,
    ReviewEpisodeStatus,
    ReviewFocus,
    ReviewOrigin,
    ReviewOutcome,
    ReviewSelection,
    ReviewSelectionKind,
    WithdrawRequiredReviewConstraintCommand,
    refreshed_lanes,
)
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
from paim.integrity.time import (
    Clock,
    EffectiveInterval,
    from_epoch_microseconds,
    require_utc,
    to_epoch_microseconds,
)
from paim.persistence.ports import CommandOutcome, IdempotencyFact
from paim.responsibility.models import ObligationKind

type ReviewCommand = (
    EstablishPlannedReviewPointCommand
    | EstablishRequiredReviewConstraintCommand
    | WithdrawRequiredReviewConstraintCommand
    | RecordEventReviewAttentionCommand
    | BeginReviewEpisodeCommand
    | CompleteReviewEpisodeCommand
)


class ContinuingReviewStore(Protocol):
    def semantic_transaction(self) -> AbstractContextManager[ContinuityTransaction]: ...
    def read_transaction(self) -> AbstractContextManager[ContinuityTransaction]: ...


class ContinuingReviewConflict(RuntimeError):
    pass


class ContinuingReviewAccessDenied(RuntimeError):
    def __init__(self) -> None:
        super().__init__("software access not established")


class ContinuingReviewService:
    """Keeps plan, requirement, attention, review, and Decision truth separate."""

    def __init__(
        self,
        store: ContinuingReviewStore,
        clock: Clock,
        access: ContinuityAccessPolicy,
    ) -> None:
        self._store = store
        self._clock = clock
        self._access = access

    def establish_planned_review_point(
        self, command: EstablishPlannedReviewPointCommand
    ) -> CommandOutcome:
        action = "review.plan"
        digest = self._digest(command)
        self._require_access(command, action)
        recorded_at = self._clock.now()
        with self._store.semantic_transaction() as tx:
            replay = self._replay(tx, command, digest)
            if replay is not None:
                return replay
            self._require_access(command, action)
            self._validate_case_context(
                tx,
                command.case_id,
                command.configuration_version_id,
                command.context.digest,
                command.effective_at,
                recorded_at,
            )
            self._validate_decision(
                tx,
                command.decision_version_id,
                command.case_id,
                command.configuration_version_id,
                command.context.digest,
                command.effective_at,
                recorded_at,
                current=True,
            )
            self._validate_accountability(
                tx,
                command,
                command.responsibility_version_id,
                command.assignment_version_id,
                ObligationKind.PLAN_NEXT_REVIEW,
                recorded_at,
            )
            if command.decision_condition:
                assert command.planning_authority_source_version_id is not None
                self._validate_review_authority(
                    tx,
                    command,
                    command.planning_authority_source_version_id,
                    "CHANGE_DECISION_REVIEW_CONDITION",
                    recorded_at,
                )
            sources = set(command.spec.source_basis_version_ids)
            sources.update(
                {
                    command.configuration_version_id,
                    command.decision_version_id,
                    command.responsibility_version_id,
                    command.assignment_version_id,
                }
            )
            if command.planning_authority_source_version_id is not None:
                sources.add(command.planning_authority_source_version_id)
            self._validate_sources_visible(tx, command, sources, recorded_at)
            self._ensure_contract_context(tx, command.contract, command.context, recorded_at)
            scope = self._planned_scope(command)
            selected = tx.select_current(
                SelectionQuery(
                    "planned-review-point",
                    scope,
                    command.effective_at,
                    recorded_at,
                    command.spec.facts.record_id,
                )
            )
            self._expect(selected, command.spec.expected_current_version_id)
            versions, statuses, relationships = self._append_planned_point(
                tx,
                command,
                command.spec,
                command.decision_version_id,
                command.responsibility_version_id,
                command.assignment_version_id,
                command.planning_authority_source_version_id,
                recorded_at,
            )
            return self._finish(
                tx,
                command,
                digest,
                command.spec.facts.record_id,
                versions,
                statuses,
                relationships,
                recorded_at,
                "PLANNED_REVIEW_POINT_ESTABLISHED",
                ("NO_UNIVERSAL_CADENCE", "PLAN_DISTINCT_FROM_REQUIREMENT"),
            )

    def establish_required_review_constraint(
        self, command: EstablishRequiredReviewConstraintCommand
    ) -> CommandOutcome:
        action = "review.constraint.establish"
        digest = self._digest(command)
        self._require_access(command, action)
        recorded_at = self._clock.now()
        with self._store.semantic_transaction() as tx:
            replay = self._replay(tx, command, digest)
            if replay is not None:
                return replay
            self._require_access(command, action)
            self._validate_case_context(
                tx,
                command.case_id,
                command.configuration_version_id,
                command.context.digest,
                command.effective_at,
                recorded_at,
            )
            self._validate_decision(
                tx,
                command.decision_version_id,
                command.case_id,
                command.configuration_version_id,
                command.context.digest,
                command.effective_at,
                recorded_at,
                current=True,
            )
            self._validate_accountability(
                tx,
                command,
                command.responsibility_version_id,
                command.assignment_version_id,
                ObligationKind.NORMALIZE_REQUIRED_REVIEW_CONSTRAINT,
                recorded_at,
            )
            self._validate_review_authority(
                tx,
                command,
                command.source_authority_version_id,
                "ESTABLISH_REQUIRED_REVIEW_CONSTRAINT",
                recorded_at,
            )
            self._validate_constraint_applicability(tx, command, recorded_at)
            sources = {
                command.configuration_version_id,
                command.decision_version_id,
                command.source_version_id,
                command.source_authority_version_id,
                command.applicability_version_id,
                command.responsibility_version_id,
                command.assignment_version_id,
            }
            self._validate_sources_visible(tx, command, sources, recorded_at)
            self._ensure_contract_context(tx, command.contract, command.context, recorded_at)
            scope = self._constraint_scope(command)
            selected = tx.select_current(
                SelectionQuery(
                    "required-review-constraint",
                    scope,
                    command.effective_at,
                    recorded_at,
                    command.facts.record_id,
                )
            )
            self._expect(selected, command.expected_current_version_id)
            content = cast(
                "dict[str, JsonValue]",
                {
                    "case_id": str(command.case_id),
                    "configuration_version_id": str(command.configuration_version_id),
                    "decision_version_id": str(command.decision_version_id),
                    "context_digest": command.context.digest,
                    "review_purpose": command.review_purpose,
                    "bounded_scope": command.bounded_scope,
                    "state": "ACTIVE",
                    "operator": command.operator.value,
                    "window_start": self._datetime(command.window_start),
                    "window_end": self._datetime(command.window_end),
                    "source_version_id": str(command.source_version_id),
                    "source_authority_version_id": str(command.source_authority_version_id),
                    "applicability_version_id": str(command.applicability_version_id),
                    "limitations": list(command.limitations),
                    "rationale": command.rationale,
                },
            )
            self._add_version(
                tx,
                command.facts.record_id,
                command.facts.version_id,
                "required-review-constraint",
                scope,
                content,
                command.effective_at,
                recorded_at,
                command,
            )
            if command.predecessor_version_id is None:
                tx.insert_projection(
                    "required_review_constraint_records",
                    {"record_id": str(command.facts.record_id)},
                )
            tx.insert_projection(
                "required_review_constraint_versions",
                self._constraint_projection(command, "ACTIVE"),
            )
            relationships, statuses = self._successor_history(
                tx,
                command.predecessor_version_id,
                command.facts.version_id,
                "required review constraint successor",
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
                "REQUIRED_REVIEW_CONSTRAINT_ESTABLISHED",
                ("SOURCE_APPLICABILITY_EXACT", "NO_REQUIREMENT_WINNER"),
            )

    def withdraw_required_review_constraint(
        self, command: WithdrawRequiredReviewConstraintCommand
    ) -> CommandOutcome:
        action = "review.constraint.withdraw"
        digest = self._digest(command)
        self._require_access(command, action)
        recorded_at = self._clock.now()
        with self._store.semantic_transaction() as tx:
            replay = self._replay(tx, command, digest)
            if replay is not None:
                return replay
            self._require_access(command, action)
            rows = tx.projection_rows(
                "required_review_constraint_versions",
                version_id=str(command.constraint_version_id),
            )
            if len(rows) != 1 or rows[0]["state"] != "ACTIVE":
                raise ContinuingReviewConflict("exact active constraint is not established")
            row = rows[0]
            self._validate_case_context(
                tx,
                command.case_id,
                command.configuration_version_id,
                command.context.digest,
                command.effective_at,
                recorded_at,
            )
            self._require_current(
                tx,
                command.constraint_version_id,
                command.effective_at,
                recorded_at,
                "constraint is stale",
            )
            self._validate_accountability(
                tx,
                command,
                command.responsibility_version_id,
                command.assignment_version_id,
                ObligationKind.NORMALIZE_REQUIRED_REVIEW_CONSTRAINT,
                recorded_at,
            )
            self._validate_review_authority(
                tx,
                command,
                command.source_authority_version_id,
                "WITHDRAW_REQUIRED_REVIEW_CONSTRAINT",
                recorded_at,
            )
            self._validate_sources_visible(
                tx,
                command,
                {
                    command.constraint_version_id,
                    command.source_authority_version_id,
                    command.responsibility_version_id,
                    command.assignment_version_id,
                },
                recorded_at,
            )
            predecessor = tx.get_version(command.constraint_version_id)
            if predecessor is None:
                raise ContinuingReviewConflict("constraint predecessor is unavailable")
            if command.facts.record_id != predecessor.record_id:
                raise ContinuingReviewConflict(
                    "constraint withdrawal must succeed the exact same governed Record"
                )
            content = predecessor.content
            content.update({"state": "WITHDRAWN", "withdrawal_reason": command.reason})
            self._add_version(
                tx,
                predecessor.record_id,
                command.facts.version_id,
                "required-review-constraint",
                predecessor.scope,
                content,
                command.effective_at,
                recorded_at,
                command,
            )
            values = dict(row)
            values.update(
                {
                    "version_id": str(command.facts.version_id),
                    "record_id": str(predecessor.record_id),
                    "state": "WITHDRAWN",
                    "responsibility_version_id": str(command.responsibility_version_id),
                    "assignment_version_id": str(command.assignment_version_id),
                    "source_authority_version_id": str(command.source_authority_version_id),
                    "predecessor_version_id": str(command.constraint_version_id),
                    "knowledge_cutoff_us": to_epoch_microseconds(command.knowledge_cutoff),
                }
            )
            tx.insert_projection("required_review_constraint_versions", values)
            relationships, statuses = self._successor_history(
                tx,
                command.constraint_version_id,
                command.facts.version_id,
                "authorized required review constraint withdrawal",
                command,
                recorded_at,
            )
            return self._finish(
                tx,
                command,
                digest,
                predecessor.record_id,
                (command.facts.version_id,),
                statuses,
                relationships,
                recorded_at,
                "REQUIRED_REVIEW_CONSTRAINT_WITHDRAWN",
                ("HISTORY_PRESERVED",),
            )

    def record_event_review_attention(
        self, command: RecordEventReviewAttentionCommand
    ) -> CommandOutcome:
        action = "review.attention.record_event"
        digest = self._digest(command)
        self._require_access(command, action)
        recorded_at = self._clock.now()
        with self._store.semantic_transaction() as tx:
            replay = self._replay(tx, command, digest)
            if replay is not None:
                return replay
            self._require_access(command, action)
            self._validate_case_context(
                tx,
                command.case_id,
                command.configuration_version_id,
                command.context.digest,
                command.effective_at,
                recorded_at,
            )
            self._validate_decision(
                tx,
                command.decision_version_id,
                command.case_id,
                command.configuration_version_id,
                command.context.digest,
                command.effective_at,
                recorded_at,
                current=False,
            )
            self._require_current(
                tx,
                command.event_source_version_id,
                command.effective_at,
                recorded_at,
                "event source is stale",
            )
            self._validate_accountability(
                tx,
                command,
                command.responsibility_version_id,
                command.assignment_version_id,
                ObligationKind.BEGIN_CONTINUING_REVIEW,
                recorded_at,
            )
            self._validate_sources_visible(
                tx,
                command,
                {
                    command.configuration_version_id,
                    command.decision_version_id,
                    command.event_source_version_id,
                    command.responsibility_version_id,
                    command.assignment_version_id,
                },
                recorded_at,
            )
            self._ensure_contract_context(tx, command.contract, command.context, recorded_at)
            scope = self._event_scope(command)
            self._expect(
                tx.select_current(
                    SelectionQuery(
                        "review-attention-event",
                        scope,
                        command.effective_at,
                        recorded_at,
                        command.facts.record_id,
                    )
                ),
                None,
            )
            content = cast(
                "dict[str, JsonValue]",
                {
                    "case_id": str(command.case_id),
                    "configuration_version_id": str(command.configuration_version_id),
                    "decision_version_id": str(command.decision_version_id),
                    "event_source_version_id": str(command.event_source_version_id),
                    "review_purpose": command.review_purpose,
                    "bounded_scope": command.bounded_scope,
                    "affected_focus": [value.value for value in command.affected_focus],
                    "reason": command.reason,
                    "substantive_change_inferred": False,
                },
            )
            self._add_version(
                tx,
                command.facts.record_id,
                command.facts.version_id,
                "review-attention-event",
                scope,
                content,
                command.effective_at,
                recorded_at,
                command,
            )
            tx.insert_projection(
                "review_attention_event_records", {"record_id": str(command.facts.record_id)}
            )
            tx.insert_projection(
                "review_attention_event_versions",
                {
                    "version_id": str(command.facts.version_id),
                    "record_id": str(command.facts.record_id),
                    "case_id": str(command.case_id),
                    "configuration_version_id": str(command.configuration_version_id),
                    "decision_version_id": str(command.decision_version_id),
                    "context_digest": command.context.digest,
                    "event_source_version_id": str(command.event_source_version_id),
                    "review_purpose": command.review_purpose,
                    "bounded_scope": command.bounded_scope,
                    "affected_focus_json": self._json(
                        tuple(value.value for value in command.affected_focus)
                    ),
                    "reason": command.reason,
                    "responsibility_version_id": str(command.responsibility_version_id),
                    "assignment_version_id": str(command.assignment_version_id),
                    "knowledge_cutoff_us": to_epoch_microseconds(command.knowledge_cutoff),
                },
            )
            return self._finish(
                tx,
                command,
                digest,
                command.facts.record_id,
                (command.facts.version_id,),
                (),
                (),
                recorded_at,
                "EVENT_REVIEW_ATTENTION_RECORDED",
                ("ATTENTION_NOT_SUBSTANTIVE_TRUTH", "NO_AUTOMATIC_REASSESSMENT"),
            )

    def begin_review_episode(self, command: BeginReviewEpisodeCommand) -> CommandOutcome:
        action = "review.episode.begin"
        digest = self._digest(command)
        self._require_access(command, action)
        recorded_at = self._clock.now()
        with self._store.semantic_transaction() as tx:
            replay = self._replay(tx, command, digest)
            if replay is not None:
                return replay
            self._require_access(command, action)
            self._validate_case_context(
                tx,
                command.case_id,
                command.configuration_version_id,
                command.context.digest,
                command.effective_at,
                recorded_at,
            )
            decision = self._validate_decision(
                tx,
                command.decision_version_id,
                command.case_id,
                command.configuration_version_id,
                command.context.digest,
                command.effective_at,
                recorded_at,
                current=False,
            )
            if decision["integration_version_id"] != str(command.integration_version_id):
                raise ContinuingReviewConflict("prior Decision/Integration basis mismatch")
            integration = tx.projection_rows(
                "prospective_integration_versions",
                version_id=str(command.integration_version_id),
            )
            if (
                len(integration) != 1
                or integration[0]["value_reliance_version_id"]
                != str(command.prior_value_reliance_version_id)
                or integration[0]["risk_reliance_version_id"]
                != str(command.prior_risk_reliance_version_id)
            ):
                raise ContinuingReviewConflict("exact prior Value/Risk management basis mismatch")
            self._validate_origins(tx, command, recorded_at)
            self._validate_accountability(
                tx,
                command,
                command.responsibility_version_id,
                command.assignment_version_id,
                ObligationKind.BEGIN_CONTINUING_REVIEW,
                recorded_at,
            )
            sources = set(command.origin_version_ids)
            sources.update(
                {
                    command.configuration_version_id,
                    command.decision_version_id,
                    command.integration_version_id,
                    command.prior_value_reliance_version_id,
                    command.prior_risk_reliance_version_id,
                    command.responsibility_version_id,
                    command.assignment_version_id,
                }
            )
            self._validate_sources_visible(tx, command, sources, recorded_at)
            self._ensure_contract_context(tx, command.contract, command.context, recorded_at)
            scope = self._episode_scope(
                command.case_id, command.configuration_version_id, command.context
            )
            self._expect(
                tx.select_current(
                    SelectionQuery("review-episode", scope, command.effective_at, recorded_at)
                ),
                command.expected_current_episode_version_id,
            )
            content = cast(
                "dict[str, JsonValue]",
                {
                    "case_id": str(command.case_id),
                    "configuration_version_id": str(command.configuration_version_id),
                    "context_digest": command.context.digest,
                    "status": ReviewEpisodeStatus.OPEN.value,
                    "origin": command.origin.value,
                    "origin_version_ids": self._ids(command.origin_version_ids),
                    "focused_scope": [value.value for value in command.focused_scope],
                    "prior_decision_version_id": str(command.decision_version_id),
                    "prior_integration_version_id": str(command.integration_version_id),
                    "prior_value_reliance_version_id": str(command.prior_value_reliance_version_id),
                    "prior_risk_reliance_version_id": str(command.prior_risk_reliance_version_id),
                    "substantive_result_established": False,
                },
            )
            self._add_version(
                tx,
                command.facts.record_id,
                command.facts.version_id,
                "review-episode",
                scope,
                content,
                command.effective_at,
                recorded_at,
                command,
            )
            tx.insert_projection(
                "review_episode_records", {"record_id": str(command.facts.record_id)}
            )
            tx.insert_projection(
                "review_episode_versions",
                {
                    "version_id": str(command.facts.version_id),
                    "record_id": str(command.facts.record_id),
                    "case_id": str(command.case_id),
                    "configuration_version_id": str(command.configuration_version_id),
                    "context_digest": command.context.digest,
                    "status": ReviewEpisodeStatus.OPEN.value,
                    "origin": command.origin.value,
                    "origin_version_ids_json": self._json(command.origin_version_ids),
                    "focused_scope_json": self._json(
                        tuple(value.value for value in command.focused_scope)
                    ),
                    "prior_decision_version_id": str(command.decision_version_id),
                    "prior_integration_version_id": str(command.integration_version_id),
                    "prior_value_reliance_version_id": str(command.prior_value_reliance_version_id),
                    "prior_risk_reliance_version_id": str(command.prior_risk_reliance_version_id),
                    "refreshed_result_version_ids_json": "[]",
                    "continued_value_reliance_version_id": None,
                    "continued_risk_reliance_version_id": None,
                    "decision_confirmation_version_id": None,
                    "successor_decision_version_id": None,
                    "outcome": None,
                    "completion_rationale": None,
                    "responsibility_version_id": str(command.responsibility_version_id),
                    "assignment_version_id": str(command.assignment_version_id),
                    "predecessor_version_id": None,
                    "knowledge_cutoff_us": to_epoch_microseconds(command.knowledge_cutoff),
                },
            )
            for origin in command.origin_version_ids:
                tx.insert_projection(
                    "review_episode_result_links",
                    {
                        "episode_version_id": str(command.facts.version_id),
                        "result_version_id": str(origin),
                        "link_role": "ORIGIN",
                    },
                )
            return self._finish(
                tx,
                command,
                digest,
                command.facts.record_id,
                (command.facts.version_id,),
                (),
                (),
                recorded_at,
                "REVIEW_EPISODE_BEGUN",
                ("FOCUSED_SCOPE_ONLY", "NO_AUTOMATIC_ASSESSMENT_OR_DECISION"),
            )

    def complete_review_episode(self, command: CompleteReviewEpisodeCommand) -> CommandOutcome:
        action = "review.episode.complete"
        digest = self._digest(command)
        self._require_access(command, action)
        recorded_at = self._clock.now()
        with self._store.semantic_transaction() as tx:
            replay = self._replay(tx, command, digest)
            if replay is not None:
                return replay
            self._require_access(command, action)
            rows = tx.projection_rows(
                "review_episode_versions", version_id=str(command.episode_version_id)
            )
            if len(rows) != 1 or rows[0]["status"] != ReviewEpisodeStatus.OPEN.value:
                raise ContinuingReviewConflict("exact open Review Episode is not established")
            episode = rows[0]
            if (
                episode["case_id"] != str(command.case_id)
                or episode["configuration_version_id"] != str(command.configuration_version_id)
                or episode["context_digest"] != command.context.digest
            ):
                raise ContinuingReviewConflict("Review Episode context mismatch")
            self._require_current(
                tx,
                command.episode_version_id,
                command.effective_at,
                recorded_at,
                "Review Episode is stale",
            )
            self._validate_case_context(
                tx,
                command.case_id,
                command.configuration_version_id,
                command.context.digest,
                command.effective_at,
                recorded_at,
            )
            self._validate_accountability(
                tx,
                command,
                command.responsibility_version_id,
                command.assignment_version_id,
                ObligationKind.COMPLETE_CONTINUING_REVIEW,
                recorded_at,
            )
            focus = tuple(
                ReviewFocus(value) for value in json.loads(cast(str, episode["focused_scope_json"]))
            )
            self._validate_focused_continuation(tx, command, episode, focus, recorded_at)
            continuation_id = self._validate_decision_continuation(tx, command, episode)
            sources = set(command.refreshed_result_version_ids)
            sources.update(
                {
                    command.episode_version_id,
                    command.continued_value_reliance_version_id,
                    command.continued_risk_reliance_version_id,
                    continuation_id,
                    command.responsibility_version_id,
                    command.assignment_version_id,
                }
            )
            self._validate_sources_visible(tx, command, sources, recorded_at)
            predecessor = tx.get_version(command.episode_version_id)
            if predecessor is None:
                raise ContinuingReviewConflict("Review Episode predecessor is unavailable")
            content = predecessor.content
            content.update(
                {
                    "status": ReviewEpisodeStatus.COMPLETED.value,
                    "outcome": command.outcome.value,
                    "refreshed_result_version_ids": cast(
                        "list[JsonValue]", self._ids(command.refreshed_result_version_ids)
                    ),
                    "continued_value_reliance_version_id": str(
                        command.continued_value_reliance_version_id
                    ),
                    "continued_risk_reliance_version_id": str(
                        command.continued_risk_reliance_version_id
                    ),
                    "decision_confirmation_version_id": self._optional(
                        command.decision_confirmation_version_id
                    ),
                    "successor_decision_version_id": self._optional(
                        command.successor_decision_version_id
                    ),
                    "completion_rationale": command.completion_rationale,
                }
            )
            self._add_version(
                tx,
                command.facts.record_id,
                command.facts.version_id,
                "review-episode",
                predecessor.scope,
                content,
                command.effective_at,
                recorded_at,
                command,
            )
            tx.insert_projection(
                "review_episode_versions",
                {
                    "version_id": str(command.facts.version_id),
                    "record_id": str(command.facts.record_id),
                    "case_id": str(command.case_id),
                    "configuration_version_id": str(command.configuration_version_id),
                    "context_digest": command.context.digest,
                    "status": ReviewEpisodeStatus.COMPLETED.value,
                    "origin": episode["origin"],
                    "origin_version_ids_json": episode["origin_version_ids_json"],
                    "focused_scope_json": episode["focused_scope_json"],
                    "prior_decision_version_id": episode["prior_decision_version_id"],
                    "prior_integration_version_id": episode["prior_integration_version_id"],
                    "prior_value_reliance_version_id": episode["prior_value_reliance_version_id"],
                    "prior_risk_reliance_version_id": episode["prior_risk_reliance_version_id"],
                    "refreshed_result_version_ids_json": self._json(
                        command.refreshed_result_version_ids
                    ),
                    "continued_value_reliance_version_id": str(
                        command.continued_value_reliance_version_id
                    ),
                    "continued_risk_reliance_version_id": str(
                        command.continued_risk_reliance_version_id
                    ),
                    "decision_confirmation_version_id": self._optional(
                        command.decision_confirmation_version_id
                    ),
                    "successor_decision_version_id": self._optional(
                        command.successor_decision_version_id
                    ),
                    "outcome": command.outcome.value,
                    "completion_rationale": command.completion_rationale,
                    "responsibility_version_id": str(command.responsibility_version_id),
                    "assignment_version_id": str(command.assignment_version_id),
                    "predecessor_version_id": str(command.episode_version_id),
                    "knowledge_cutoff_us": to_epoch_microseconds(command.knowledge_cutoff),
                },
            )
            for result in command.refreshed_result_version_ids:
                tx.insert_projection(
                    "review_episode_result_links",
                    {
                        "episode_version_id": str(command.facts.version_id),
                        "result_version_id": str(result),
                        "link_role": "REFRESHED_RESULT",
                    },
                )
            tx.insert_projection(
                "review_episode_result_links",
                {
                    "episode_version_id": str(command.facts.version_id),
                    "result_version_id": str(continuation_id),
                    "link_role": "DECISION_CONTINUATION",
                },
            )
            for origin in json.loads(cast(str, episode["origin_version_ids_json"])):
                origin_id = RecordVersionId.parse(str(origin))
                if tx.projection_rows("review_attention_event_versions", version_id=str(origin_id)):
                    tx.insert_projection(
                        "review_episode_result_links",
                        {
                            "episode_version_id": str(command.facts.version_id),
                            "result_version_id": str(origin_id),
                            "link_role": "ADDRESSED_EVENT_ORIGIN",
                        },
                    )
            relationships, statuses = self._successor_history(
                tx,
                command.episode_version_id,
                command.facts.version_id,
                "focused Review Episode completion",
                command,
                recorded_at,
            )
            versions: tuple[RecordVersionId, ...] = (command.facts.version_id,)
            if command.next_planned_point is not None:
                assert command.planning_responsibility_version_id is not None
                assert command.planning_assignment_version_id is not None
                self._validate_accountability(
                    tx,
                    command,
                    command.planning_responsibility_version_id,
                    command.planning_assignment_version_id,
                    ObligationKind.PLAN_NEXT_REVIEW,
                    recorded_at,
                )
                next_decision = command.successor_decision_version_id or RecordVersionId.parse(
                    str(episode["prior_decision_version_id"])
                )
                decision_rows = tx.projection_rows(
                    "prospective_decision_versions", version_id=str(next_decision)
                )
                if len(decision_rows) != 1:
                    raise ContinuingReviewConflict(
                        "next planned point requires the exact Decision context"
                    )
                integration_rows = tx.projection_rows(
                    "prospective_integration_versions",
                    version_id=str(decision_rows[0]["integration_version_id"]),
                )
                if len(integration_rows) != 1:
                    raise ContinuingReviewConflict(
                        "next planned point requires the exact Integration scope"
                    )
                next_review_purpose = "continuing management review"
                next_bounded_scope = str(integration_rows[0]["bounded_scope"])
                next_scope = self._planned_scope_values(
                    command.case_id,
                    command.configuration_version_id,
                    next_decision,
                    command.context.digest,
                    next_review_purpose,
                    next_bounded_scope,
                )
                selected = tx.select_current(
                    SelectionQuery(
                        "planned-review-point",
                        next_scope,
                        command.effective_at,
                        recorded_at,
                        command.next_planned_point.facts.record_id,
                    )
                )
                self._expect(selected, command.next_planned_point.expected_current_version_id)
                synthetic = self._append_next_point_from_completion(
                    tx,
                    command,
                    command.next_planned_point,
                    next_decision,
                    command.planning_responsibility_version_id,
                    command.planning_assignment_version_id,
                    next_scope,
                    next_review_purpose,
                    next_bounded_scope,
                    recorded_at,
                )
                versions += synthetic[0]
                statuses += synthetic[1]
                relationships += synthetic[2]
            return self._finish(
                tx,
                command,
                digest,
                command.facts.record_id,
                versions,
                statuses,
                relationships,
                recorded_at,
                "REVIEW_EPISODE_COMPLETED",
                ("DECISION_CONTINUATION_EXACT", "NO_AUTOMATIC_CARRY_FORWARD"),
            )

    def select_planned_review_point(
        self,
        *,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        configuration_version_id: RecordVersionId,
        decision_version_id: RecordVersionId,
        context: ExactContextSet,
        review_purpose: str,
        bounded_scope: str,
        effective_at: datetime,
        known_at: datetime,
    ) -> ReviewSelection:
        scope = self._planned_scope_values(
            case_id,
            configuration_version_id,
            decision_version_id,
            context.digest,
            review_purpose,
            bounded_scope,
        )
        return self._select_visible(
            principal_id,
            actor_id,
            case_id,
            "planned-review-point",
            "planned_review_point_versions",
            scope,
            effective_at,
            known_at,
            (
                "configuration_version_id",
                "decision_version_id",
                "responsibility_version_id",
                "assignment_version_id",
            ),
            ("source_basis_version_ids_json",),
        )

    def required_review_window(
        self,
        *,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        configuration_version_id: RecordVersionId,
        decision_version_id: RecordVersionId,
        context: ExactContextSet,
        review_purpose: str,
        bounded_scope: str,
        effective_at: datetime,
        known_at: datetime,
    ) -> RequiredReviewWindow:
        require_utc(effective_at)
        require_utc(known_at)
        rows: list[dict[str, object]] = []
        with self._store.read_transaction() as tx:
            for row in tx.projection_rows(
                "required_review_constraint_versions",
                case_id=str(case_id),
                configuration_version_id=str(configuration_version_id),
                decision_version_id=str(decision_version_id),
                context_digest=context.digest,
                review_purpose=review_purpose,
                bounded_scope=bounded_scope,
                state="ACTIVE",
            ):
                version_id = RecordVersionId.parse(str(row["version_id"]))
                version = tx.get_version(version_id)
                if version is None:
                    continue
                selected = tx.select_current(
                    SelectionQuery(
                        version.family,
                        version.scope,
                        effective_at,
                        known_at,
                        version.record_id,
                    )
                )
                if not (
                    isinstance(selected, SelectionFound)
                    and selected.candidate.version_id == version_id
                    and self._row_visible(
                        tx,
                        principal_id,
                        actor_id,
                        case_id,
                        effective_at,
                        known_at,
                        row,
                        (
                            "version_id",
                            "configuration_version_id",
                            "decision_version_id",
                            "source_version_id",
                            "source_authority_version_id",
                            "applicability_version_id",
                            "responsibility_version_id",
                            "assignment_version_id",
                        ),
                        (),
                    )
                ):
                    continue
                rows.append(row)
        if not rows:
            return RequiredReviewWindow(
                ReviewSelectionKind.ABSENT, (), None, None, "REQUIRED REVIEW NOT ESTABLISHED"
            )
        starts = [
            cast(int, row["window_start_us"]) for row in rows if row["window_start_us"] is not None
        ]
        ends = [cast(int, row["window_end_us"]) for row in rows if row["window_end_us"] is not None]
        start = max(starts) if starts else None
        end = min(ends) if ends else None
        ids = tuple(
            sorted((RecordVersionId.parse(str(row["version_id"])) for row in rows), key=str)
        )
        if start is not None and end is not None and start > end:
            return RequiredReviewWindow(
                ReviewSelectionKind.CONFLICT,
                ids,
                from_epoch_microseconds(start),
                from_epoch_microseconds(end),
                "REQUIRED REVIEW TIMING CONFLICT — UNRESOLVED",
            )
        return RequiredReviewWindow(
            ReviewSelectionKind.ONE,
            ids,
            from_epoch_microseconds(start) if start is not None else None,
            from_epoch_microseconds(end) if end is not None else None,
            "EXACT MECHANICAL CONSTRAINT INTERSECTION",
        )

    def review_attention(
        self,
        *,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        configuration_version_id: RecordVersionId,
        decision_version_id: RecordVersionId,
        context: ExactContextSet,
        review_purpose: str,
        bounded_scope: str,
        effective_at: datetime,
        known_at: datetime,
    ) -> ReviewAttention:
        plan = self.select_planned_review_point(
            principal_id=principal_id,
            actor_id=actor_id,
            case_id=case_id,
            configuration_version_id=configuration_version_id,
            decision_version_id=decision_version_id,
            context=context,
            review_purpose=review_purpose,
            bounded_scope=bounded_scope,
            effective_at=effective_at,
            known_at=known_at,
        )
        required = self.required_review_window(
            principal_id=principal_id,
            actor_id=actor_id,
            case_id=case_id,
            configuration_version_id=configuration_version_id,
            decision_version_id=decision_version_id,
            context=context,
            review_purpose=review_purpose,
            bounded_scope=bounded_scope,
            effective_at=effective_at,
            known_at=known_at,
        )
        kinds: list[str] = []
        sources: set[RecordVersionId] = set()
        now_us = to_epoch_microseconds(effective_at)
        if plan.kind is ReviewSelectionKind.ONE:
            with self._store.read_transaction() as tx:
                row = tx.projection_rows(
                    "planned_review_point_versions", version_id=str(plan.version_ids[0])
                )[0]
            if cast(int, row["review_at_us"]) <= now_us:
                kinds.append("PLANNED REVIEW DUE")
                sources.update(plan.version_ids)
        if required.kind is ReviewSelectionKind.CONFLICT:
            kinds.append("REQUIRED REVIEW TIMING CONFLICT — UNRESOLVED")
            sources.update(required.constraint_version_ids)
        elif required.window_end is not None and required.window_end <= effective_at:
            kinds.append("REQUIRED REVIEW DUE")
            sources.update(required.constraint_version_ids)
        with self._store.read_transaction() as tx:
            addressed_event_ids = self._visible_addressed_event_ids(
                tx,
                principal_id,
                actor_id,
                case_id,
                effective_at,
                known_at,
            )
            for row in tx.projection_rows(
                "review_attention_event_versions",
                case_id=str(case_id),
                configuration_version_id=str(configuration_version_id),
                decision_version_id=str(decision_version_id),
                context_digest=context.digest,
                review_purpose=review_purpose,
                bounded_scope=bounded_scope,
            ):
                version_id = RecordVersionId.parse(str(row["version_id"]))
                version = tx.get_version(version_id)
                if (
                    version is None
                    or version.recorded_at > known_at
                    or version_id in addressed_event_ids
                ):
                    continue
                if self._row_visible(
                    tx,
                    principal_id,
                    actor_id,
                    case_id,
                    effective_at,
                    known_at,
                    row,
                    (
                        "version_id",
                        "configuration_version_id",
                        "decision_version_id",
                        "event_source_version_id",
                        "responsibility_version_id",
                        "assignment_version_id",
                    ),
                    (),
                ):
                    kinds.append("EXPLICIT EVENT REVIEW ATTENTION")
                    sources.add(version_id)
        return ReviewAttention(
            bool(kinds), tuple(sorted(set(kinds))), tuple(sorted(sources, key=str))
        )

    def _visible_addressed_event_ids(
        self,
        tx: ContinuityTransaction,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        effective_at: datetime,
        known_at: datetime,
    ) -> set[RecordVersionId]:
        addressed: set[RecordVersionId] = set()
        for link in tx.projection_rows(
            "review_episode_result_links", link_role="ADDRESSED_EVENT_ORIGIN"
        ):
            episode_id = RecordVersionId.parse(str(link["episode_version_id"]))
            rows = tx.projection_rows("review_episode_versions", version_id=str(episode_id))
            if len(rows) != 1 or rows[0]["status"] != ReviewEpisodeStatus.COMPLETED.value:
                continue
            version = tx.get_version(episode_id)
            if (
                version is None
                or version.recorded_at > known_at
                or not version.effective.contains(effective_at)
            ):
                continue
            selected = tx.select_current(
                SelectionQuery(
                    version.family,
                    version.scope,
                    effective_at,
                    known_at,
                    version.record_id,
                )
            )
            if not (
                isinstance(selected, SelectionFound) and selected.candidate.version_id == episode_id
            ):
                continue
            if self._row_visible(
                tx,
                principal_id,
                actor_id,
                case_id,
                effective_at,
                known_at,
                rows[0],
                (
                    "version_id",
                    "configuration_version_id",
                    "prior_decision_version_id",
                    "prior_integration_version_id",
                    "prior_value_reliance_version_id",
                    "prior_risk_reliance_version_id",
                    "continued_value_reliance_version_id",
                    "continued_risk_reliance_version_id",
                    "decision_confirmation_version_id",
                    "successor_decision_version_id",
                    "responsibility_version_id",
                    "assignment_version_id",
                ),
                ("origin_version_ids_json", "refreshed_result_version_ids_json"),
            ):
                addressed.add(RecordVersionId.parse(str(link["result_version_id"])))
        return addressed

    def select_review_episode(
        self,
        *,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        configuration_version_id: RecordVersionId,
        context: ExactContextSet,
        effective_at: datetime,
        known_at: datetime,
    ) -> ReviewSelection:
        return self._select_visible(
            principal_id,
            actor_id,
            case_id,
            "review-episode",
            "review_episode_versions",
            self._episode_scope(case_id, configuration_version_id, context),
            effective_at,
            known_at,
            (
                "configuration_version_id",
                "prior_decision_version_id",
                "prior_integration_version_id",
                "prior_value_reliance_version_id",
                "prior_risk_reliance_version_id",
                "responsibility_version_id",
                "assignment_version_id",
            ),
            ("origin_version_ids_json", "refreshed_result_version_ids_json"),
        )

    def _select_visible(
        self,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        family: str,
        table: str,
        scope: str,
        effective_at: datetime,
        known_at: datetime,
        scalar_source_fields: tuple[str, ...],
        json_source_fields: tuple[str, ...],
    ) -> ReviewSelection:
        require_utc(effective_at)
        require_utc(known_at)
        with self._store.read_transaction() as tx:
            selected = tx.select_current(SelectionQuery(family, scope, effective_at, known_at))
            if isinstance(selected, SelectionAbsent):
                return ReviewSelection(ReviewSelectionKind.ABSENT, ())
            candidates = (
                selected.candidates
                if isinstance(selected, SelectionConflict)
                else (cast(SelectionFound, selected).candidate,)
            )
            visible: list[RecordVersionId] = []
            for candidate in candidates:
                rows = tx.projection_rows(table, version_id=str(candidate.version_id))
                if len(rows) == 1 and self._row_visible(
                    tx,
                    principal_id,
                    actor_id,
                    case_id,
                    effective_at,
                    known_at,
                    rows[0],
                    ("version_id", *scalar_source_fields),
                    json_source_fields,
                ):
                    visible.append(candidate.version_id)
            ids = tuple(sorted(visible, key=str))
            if not ids:
                return ReviewSelection(ReviewSelectionKind.ABSENT, ())
            if len(ids) > 1:
                return ReviewSelection(ReviewSelectionKind.CONFLICT, ids)
            version = tx.get_version(ids[0])
            return ReviewSelection(
                ReviewSelectionKind.ONE,
                ids,
                str(version.content.get("status")) if version else None,
            )

    def _append_planned_point(
        self,
        tx: ContinuityTransaction,
        command: ReviewCommand,
        spec: PlannedReviewPointSpec,
        decision_version_id: RecordVersionId,
        responsibility_version_id: RecordVersionId,
        assignment_version_id: RecordVersionId,
        authority_source_version_id: RecordVersionId | None,
        recorded_at: datetime,
        scope: str | None = None,
        review_purpose: str | None = None,
        bounded_scope_value: str | None = None,
    ) -> tuple[tuple[RecordVersionId, ...], tuple[EventId, ...], tuple[RelationshipId, ...]]:
        actual_scope = scope or self._planned_scope(
            cast(EstablishPlannedReviewPointCommand, command)
        )
        content = cast(
            "dict[str, JsonValue]",
            {
                "case_id": str(command.case_id),
                "configuration_version_id": str(command.configuration_version_id),
                "decision_version_id": str(decision_version_id),
                "context_digest": command.context.digest,
                "review_at": spec.review_at.isoformat(),
                "rationale": spec.rationale,
                "source_basis_version_ids": self._ids(spec.source_basis_version_ids),
                "no_universal_cadence": True,
            },
        )
        self._add_version(
            tx,
            spec.facts.record_id,
            spec.facts.version_id,
            "planned-review-point",
            actual_scope,
            content,
            command.effective_at,
            recorded_at,
            command,
        )
        if spec.predecessor_version_id is None:
            tx.insert_projection(
                "planned_review_point_records", {"record_id": str(spec.facts.record_id)}
            )
        purpose = review_purpose or (
            command.review_purpose
            if isinstance(command, EstablishPlannedReviewPointCommand)
            else "continuing management review"
        )
        bounded_scope = bounded_scope_value or (
            command.bounded_scope
            if isinstance(command, EstablishPlannedReviewPointCommand)
            else "continuing management scope"
        )
        tx.insert_projection(
            "planned_review_point_versions",
            {
                "version_id": str(spec.facts.version_id),
                "record_id": str(spec.facts.record_id),
                "case_id": str(command.case_id),
                "configuration_version_id": str(command.configuration_version_id),
                "decision_version_id": str(decision_version_id),
                "context_digest": command.context.digest,
                "review_purpose": purpose,
                "bounded_scope": bounded_scope,
                "review_at_us": to_epoch_microseconds(spec.review_at),
                "rationale": spec.rationale,
                "source_basis_version_ids_json": self._json(spec.source_basis_version_ids),
                "responsibility_version_id": str(responsibility_version_id),
                "assignment_version_id": str(assignment_version_id),
                "planning_authority_source_version_id": self._optional(authority_source_version_id),
                "decision_condition": bool(authority_source_version_id),
                "predecessor_version_id": self._optional(spec.predecessor_version_id),
                "knowledge_cutoff_us": to_epoch_microseconds(command.knowledge_cutoff),
            },
        )
        relationships, statuses = self._successor_history(
            tx,
            spec.predecessor_version_id,
            spec.facts.version_id,
            "planned review point successor",
            command,
            recorded_at,
        )
        return (spec.facts.version_id,), statuses, relationships

    def _append_next_point_from_completion(
        self,
        tx: ContinuityTransaction,
        command: CompleteReviewEpisodeCommand,
        spec: PlannedReviewPointSpec,
        decision_version_id: RecordVersionId,
        responsibility_version_id: RecordVersionId,
        assignment_version_id: RecordVersionId,
        scope: str,
        review_purpose: str,
        bounded_scope: str,
        recorded_at: datetime,
    ) -> tuple[tuple[RecordVersionId, ...], tuple[EventId, ...], tuple[RelationshipId, ...]]:
        return self._append_planned_point(
            tx,
            command,
            spec,
            decision_version_id,
            responsibility_version_id,
            assignment_version_id,
            None,
            recorded_at,
            scope,
            review_purpose,
            bounded_scope,
        )

    def _validate_focused_continuation(
        self,
        tx: ContinuityTransaction,
        command: CompleteReviewEpisodeCommand,
        episode: dict[str, object],
        focus: tuple[ReviewFocus, ...],
        known_at: datetime,
    ) -> None:
        lanes = refreshed_lanes(focus)
        prior_value = RecordVersionId.parse(str(episode["prior_value_reliance_version_id"]))
        prior_risk = RecordVersionId.parse(str(episode["prior_risk_reliance_version_id"]))
        if (
            ReviewFocus.VALUE_REFRESH not in focus
            and command.continued_value_reliance_version_id != prior_value
        ):
            raise ContinuingReviewConflict("Value cannot change without exact Value refresh scope")
        if (
            ReviewFocus.RISK_REFRESH not in focus
            and command.continued_risk_reliance_version_id != prior_risk
        ):
            raise ContinuingReviewConflict("Risk cannot change without exact Risk refresh scope")
        for version_id in (
            command.continued_value_reliance_version_id,
            command.continued_risk_reliance_version_id,
        ):
            rows = tx.projection_rows("assessment_reliance_versions", version_id=str(version_id))
            if len(rows) != 1:
                raise ContinuingReviewConflict("exact continued Reliance is not established")
            self._require_current(
                tx, version_id, command.effective_at, known_at, "continued Reliance is stale"
            )
        if len(lanes) == 1:
            unaffected = (
                command.continued_risk_reliance_version_id
                if next(iter(lanes)).value == "VALUE"
                else command.continued_value_reliance_version_id
            )
            if unaffected not in {prior_value, prior_risk}:
                raise ContinuingReviewConflict("focused review cannot silently refresh both lanes")
        for version_id in command.refreshed_result_version_ids:
            if tx.get_version(version_id) is None:
                raise ContinuingReviewConflict("refreshed result link is unavailable")

    @staticmethod
    def _validate_decision_continuation(
        tx: ContinuityTransaction,
        command: CompleteReviewEpisodeCommand,
        episode: dict[str, object],
    ) -> RecordVersionId:
        prior_decision = str(episode["prior_decision_version_id"])
        if command.outcome is ReviewOutcome.UNCHANGED_DECISION_CONFIRMED:
            assert command.decision_confirmation_version_id is not None
            rows = tx.projection_rows(
                "prospective_decision_confirmation_versions",
                version_id=str(command.decision_confirmation_version_id),
            )
            if len(rows) != 1 or rows[0]["decision_version_id"] != prior_decision:
                raise ContinuingReviewConflict(
                    "unchanged review requires exact Slice-D Decision Confirmation"
                )
            return command.decision_confirmation_version_id
        assert command.successor_decision_version_id is not None
        rows = tx.projection_rows(
            "prospective_decision_versions",
            version_id=str(command.successor_decision_version_id),
        )
        if len(rows) != 1 or rows[0]["status"] != "AUTHORIZED":
            raise ContinuingReviewConflict("changed review requires exact authorized successor")
        proposal_id = rows[0]["proposal_version_id"]
        proposals = tx.projection_rows("prospective_decision_versions", version_id=str(proposal_id))
        if len(proposals) != 1 or proposals[0]["predecessor_version_id"] != prior_decision:
            raise ContinuingReviewConflict("Decision successor path does not bind prior Decision")
        return command.successor_decision_version_id

    def _validate_origins(
        self, tx: ContinuityTransaction, command: BeginReviewEpisodeCommand, known_at: datetime
    ) -> None:
        allowed = {
            ReviewOrigin.PLANNED_POINT: {"planned-review-point"},
            ReviewOrigin.REQUIRED_CONSTRAINT: {"required-review-constraint"},
            ReviewOrigin.EVENT_TRIGGER: {"review-attention-event", "trigger"},
            ReviewOrigin.EXPLICIT_INITIATION: {
                "responsibility",
                "case-work",
                "review-attention-event",
            },
        }[command.origin]
        for version_id in command.origin_version_ids:
            version = tx.get_version(version_id)
            if version is None or version.family not in allowed or version.recorded_at > known_at:
                raise ContinuingReviewConflict("Review Episode origin is not exact or eligible")

    def _validate_constraint_applicability(
        self,
        tx: ContinuityTransaction,
        command: EstablishRequiredReviewConstraintCommand,
        known_at: datetime,
    ) -> None:
        self._require_current(
            tx,
            command.source_version_id,
            command.effective_at,
            known_at,
            "required review source is stale",
        )
        self._require_current(
            tx,
            command.applicability_version_id,
            command.effective_at,
            known_at,
            "required review Applicability is stale",
        )
        applicability = tx.get_version(command.applicability_version_id)
        exact = applicability.content if applicability else {}
        review_applicability = exact.get("review_constraint_applicability")
        evidence_rows = tx.projection_rows(
            "evidence_applicability_versions",
            version_id=str(command.applicability_version_id),
        )
        evidence_ok = bool(
            len(evidence_rows) == 1
            and evidence_rows[0]["evidence_version_id"] == str(command.source_version_id)
            and evidence_rows[0]["configuration_version_id"]
            == str(command.configuration_version_id)
            and evidence_rows[0]["outcome"] in {"APPLICABLE", "APPLICABLE_WITH_LIMITATIONS"}
        )
        explicit_ok = bool(
            isinstance(review_applicability, dict)
            and review_applicability.get("outcome") == "APPLICABLE"
            and review_applicability.get("case_id") == str(command.case_id)
            and review_applicability.get("configuration_version_id")
            == str(command.configuration_version_id)
            and review_applicability.get("source_version_id") == str(command.source_version_id)
        )
        if not (evidence_ok or explicit_ok):
            raise ContinuingReviewConflict(
                "source presence alone does not establish required review Applicability"
            )

    def _validate_decision(
        self,
        tx: ContinuityTransaction,
        version_id: RecordVersionId,
        case_id: RecordId,
        configuration_version_id: RecordVersionId,
        context_digest: str,
        effective_at: datetime,
        known_at: datetime,
        *,
        current: bool,
    ) -> dict[str, object]:
        rows = tx.projection_rows("prospective_decision_versions", version_id=str(version_id))
        if (
            len(rows) != 1
            or rows[0]["status"] != "AUTHORIZED"
            or rows[0]["case_id"] != str(case_id)
            or rows[0]["configuration_version_id"] != str(configuration_version_id)
            or rows[0]["context_digest"] != context_digest
        ):
            raise ContinuingReviewConflict("exact authorized Decision context is unavailable")
        if current:
            self._require_current(
                tx, version_id, effective_at, known_at, "authorized Decision is stale"
            )
        return rows[0]

    def _validate_case_context(
        self,
        tx: ContinuityTransaction,
        case_id: RecordId,
        configuration_version_id: RecordVersionId,
        context_digest: str,
        effective_at: datetime,
        known_at: datetime,
    ) -> None:
        records = tx.projection_rows("case_continuity_status_records", case_id=str(case_id))
        if len(records) != 1:
            raise ContinuingReviewConflict("exact prospective OPEN Case is not established")
        selected = tx.select_current(
            SelectionQuery(
                "case-continuity-status",
                f"case:{case_id}",
                effective_at,
                known_at,
                RecordId.parse(str(records[0]["record_id"])),
            )
        )
        if not isinstance(selected, SelectionFound):
            raise ContinuingReviewConflict("Case continuity is absent or conflicting")
        statuses = tx.projection_rows(
            "case_continuity_status_versions", version_id=str(selected.candidate.version_id)
        )
        if len(statuses) != 1 or statuses[0]["status"] != "OPEN":
            raise ContinuingReviewConflict("prospective Case is not OPEN")
        governing = tx.select_current(
            SelectionQuery("governing-configuration", f"case:{case_id}", effective_at, known_at)
        )
        if not isinstance(governing, SelectionFound):
            raise ContinuingReviewConflict("governing Configuration is absent or conflicting")
        rows = tx.projection_rows(
            "governing_configuration_designations", version_id=str(governing.candidate.version_id)
        )
        semantics = tx.projection_rows(
            "record_version_semantics", version_id=str(configuration_version_id)
        )
        if (
            len(rows) != 1
            or rows[0]["configuration_version_id"] != str(configuration_version_id)
            or len(semantics) != 1
            or semantics[0]["context_digest"] != context_digest
        ):
            raise ContinuingReviewConflict("exact governing Configuration/context mismatch")

    def _validate_accountability(
        self,
        tx: ContinuityTransaction,
        command: ReviewCommand,
        responsibility_version_id: RecordVersionId,
        assignment_version_id: RecordVersionId,
        obligation: ObligationKind,
        known_at: datetime,
    ) -> None:
        responsibilities = tx.projection_rows(
            "responsibility_versions", version_id=str(responsibility_version_id)
        )
        assignments = tx.projection_rows(
            "responsibility_assignment_versions", version_id=str(assignment_version_id)
        )
        if len(responsibilities) != 1 or len(assignments) != 1:
            raise ContinuingReviewConflict("exact Responsibility/assignment is not established")
        responsibility, assignment = responsibilities[0], assignments[0]
        if (
            responsibility["obligation_kind"] != obligation.value
            or responsibility["owning_case_id"] != str(command.case_id)
            or responsibility["context_digest"] != command.context.digest
            or assignment["responsibility_version_id"] != str(responsibility_version_id)
            or assignment["actor_id"] != str(command.identity.actor_id)
            or assignment["state"] != "ASSIGNED"
        ):
            raise ContinuingReviewConflict("accountability does not match exact review act")
        self._require_current(
            tx,
            responsibility_version_id,
            command.effective_at,
            known_at,
            "review Responsibility is stale",
        )
        self._require_current(
            tx,
            assignment_version_id,
            command.effective_at,
            known_at,
            "review assignment is stale",
        )
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
                    "",
                )
            except ContinuingReviewConflict:
                continue
            if row["state"] == "ASSIGNED":
                eligible.append(row)
        if len(eligible) != 1 or eligible[0]["version_id"] != str(assignment_version_id):
            raise ContinuingReviewConflict("review Responsibility vacancy or conflict")
        basis = tx.projection_rows(
            "assignment_basis_versions",
            version_id=str(assignment["assignment_basis_version_id"]),
        )
        if len(basis) != 1 or basis[0]["state"] != "ACTIVE":
            raise ContinuingReviewConflict("exact Assignment Basis is not active")
        source_id = RecordVersionId.parse(str(basis[0]["basis_source_version_id"]))
        self._require_current(
            tx, source_id, command.effective_at, known_at, "assignment authority source is stale"
        )
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
            raise ContinuingReviewConflict("Assignment Basis does not authorize exact review act")

    def _validate_review_authority(
        self,
        tx: ContinuityTransaction,
        command: ReviewCommand,
        version_id: RecordVersionId,
        action: str,
        known_at: datetime,
    ) -> None:
        self._require_current(
            tx, version_id, command.effective_at, known_at, "review authority source is stale"
        )
        source = tx.get_version(version_id)
        authority = source.content.get("prospective_review_authority") if source else None
        if (
            not isinstance(authority, dict)
            or authority.get("actor_id") != str(command.identity.actor_id)
            or action not in cast(list[str], authority.get("allowed_actions", []))
            or str(command.case_id) not in cast(list[str], authority.get("allowed_case_ids", []))
            or authority.get("context_digest") != command.context.digest
        ):
            raise ContinuingReviewConflict("exact substantive review authority is not established")

    def _validate_sources_visible(
        self,
        tx: ContinuityTransaction,
        command: ReviewCommand,
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
                command.effective_at,
                known_at,
            ):
                raise ContinuingReviewAccessDenied()

    def _row_visible(
        self,
        tx: ContinuityTransaction,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        effective_at: datetime,
        known_at: datetime,
        row: dict[str, object],
        scalar_fields: tuple[str, ...],
        json_fields: tuple[str, ...],
    ) -> bool:
        values: set[RecordVersionId] = set()
        try:
            for field in scalar_fields:
                if row.get(field):
                    values.add(RecordVersionId.parse(str(row[field])))
            for field in json_fields:
                if row.get(field):
                    values.update(
                        RecordVersionId.parse(value) for value in json.loads(cast(str, row[field]))
                    )
            self._expand_assignment_sources(tx, values)
        except (ValueError, TypeError, json.JSONDecodeError):
            return False
        return all(
            self._source_visible(
                principal_id,
                actor_id,
                case_id,
                version_id,
                effective_at,
                known_at,
            )
            for version_id in values
        )

    def _source_visible(
        self,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        version_id: RecordVersionId,
        effective_at: datetime,
        known_at: datetime,
    ) -> bool:
        return self._access.authorize(
            principal_id=principal_id,
            actor_id=str(actor_id),
            action="source.read",
            case_id=case_id,
            write=False,
            source_version_id=version_id,
            source_family=None,
            effective_at=effective_at,
            known_at=known_at,
        )

    def _require_access(self, command: ReviewCommand, action: str) -> None:
        if not self._access.authorize(
            principal_id=str(command.identity.principal_id),
            actor_id=str(command.identity.actor_id),
            action=action,
            case_id=command.case_id,
            write=True,
        ):
            raise ContinuingReviewAccessDenied()

    @staticmethod
    def _require_current(
        tx: ContinuityTransaction,
        version_id: RecordVersionId,
        effective_at: datetime,
        known_at: datetime,
        reason: str,
    ) -> None:
        version = tx.get_version(version_id)
        if version is None:
            raise ContinuingReviewConflict(reason or "exact Version unavailable")
        selected = tx.select_current(
            SelectionQuery(version.family, version.scope, effective_at, known_at, version.record_id)
        )
        if not isinstance(selected, SelectionFound) or selected.candidate.version_id != version_id:
            raise ContinuingReviewConflict(reason or "exact Version is not current")

    @staticmethod
    def _expect(selected: object, expected: RecordVersionId | None) -> None:
        if expected is None and not isinstance(selected, SelectionAbsent):
            raise ContinuingReviewConflict("expected absent prospective review record")
        if expected is not None and not (
            isinstance(selected, SelectionFound) and selected.candidate.version_id == expected
        ):
            raise ContinuingReviewConflict("stale exact review predecessor; no retarget permitted")

    @staticmethod
    def _replay(
        tx: ContinuityTransaction, command: ReviewCommand, digest: str
    ) -> CommandOutcome | None:
        fact = tx.get_idempotency(
            str(command.identity.idempotency_scope), str(command.identity.idempotency_key)
        )
        if fact is None:
            return None
        if fact.digest != digest:
            raise ContinuingReviewConflict("IDEMPOTENCY KEY REUSE CONFLICT")
        return fact.outcome

    @staticmethod
    def _add_version(
        tx: ContinuityTransaction,
        record_id: RecordId,
        version_id: RecordVersionId,
        family: str,
        scope: str,
        content: dict[str, JsonValue],
        effective_at: datetime,
        recorded_at: datetime,
        command: ReviewCommand,
    ) -> None:
        tx.add_version(
            FinalizedRecordVersion(
                record_id,
                version_id,
                family,
                scope,
                canonical_json(content),
                recorded_at,
                EffectiveInterval(effective_at),
                str(command.identity.actor_id),
            )
        )
        tx.insert_projection(
            "record_version_semantics",
            {
                "version_id": str(version_id),
                "contract_key": command.contract.key,
                "context_digest": command.context.digest,
                "consumer_id": "gate8-slice-e",
                "adapter_key": None,
            },
        )

    @staticmethod
    def _successor_history(
        tx: ContinuityTransaction,
        predecessor: RecordVersionId | None,
        successor: RecordVersionId,
        reason: str,
        command: ReviewCommand,
        recorded_at: datetime,
    ) -> tuple[tuple[RelationshipId, ...], tuple[EventId, ...]]:
        if predecessor is None:
            return (), ()
        before = tx.get_version(predecessor)
        after = tx.get_version(successor)
        if (
            before is None
            or after is None
            or before.record_id != after.record_id
            or before.family != after.family
            or before.scope != after.scope
        ):
            raise ContinuingReviewConflict(
                "review succession requires one exact Record, family, and scope"
            )
        relationship = VersionRelationship(
            RelationshipId.new(),
            predecessor,
            successor,
            RelationshipType.SUPERSESSION,
            recorded_at,
            reason,
        )
        status = StatusEvent(
            EventId.new(),
            predecessor,
            "CURRENT",
            "SUPERSEDED",
            recorded_at,
            command.effective_at,
            str(command.identity.actor_id),
            reason,
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
        command: ReviewCommand,
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
        for family in (
            "planned-review-point",
            "required-review-constraint",
            "review-attention-event",
            "review-episode",
        ):
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
    def _planned_scope(command: EstablishPlannedReviewPointCommand) -> str:
        return ContinuingReviewService._planned_scope_values(
            command.case_id,
            command.configuration_version_id,
            command.decision_version_id,
            command.context.digest,
            command.review_purpose,
            command.bounded_scope,
        )

    @staticmethod
    def _planned_scope_values(
        case_id: RecordId,
        configuration_version_id: RecordVersionId,
        decision_version_id: RecordVersionId,
        context_digest: str,
        review_purpose: str,
        bounded_scope: str,
    ) -> str:
        return (
            f"planned-review:case:{case_id}:configuration:{configuration_version_id}:"
            f"decision:{decision_version_id}:context:{context_digest}:"
            f"purpose:{review_purpose}:scope:{bounded_scope}"
        )

    @staticmethod
    def _constraint_scope(command: EstablishRequiredReviewConstraintCommand) -> str:
        return f"required-review-constraint:record:{command.facts.record_id}"

    @staticmethod
    def _event_scope(command: RecordEventReviewAttentionCommand) -> str:
        return f"review-attention-event:record:{command.facts.record_id}"

    @staticmethod
    def _episode_scope(
        case_id: RecordId,
        configuration_version_id: RecordVersionId,
        context: ExactContextSet,
    ) -> str:
        return (
            f"review-episode:case:{case_id}:configuration:{configuration_version_id}:"
            f"context:{context.digest}"
        )

    @staticmethod
    def _constraint_projection(
        command: EstablishRequiredReviewConstraintCommand, state: str
    ) -> dict[str, object]:
        return {
            "version_id": str(command.facts.version_id),
            "record_id": str(command.facts.record_id),
            "case_id": str(command.case_id),
            "configuration_version_id": str(command.configuration_version_id),
            "decision_version_id": str(command.decision_version_id),
            "context_digest": command.context.digest,
            "review_purpose": command.review_purpose,
            "bounded_scope": command.bounded_scope,
            "state": state,
            "operator": command.operator.value,
            "window_start_us": (
                to_epoch_microseconds(command.window_start)
                if command.window_start is not None
                else None
            ),
            "window_end_us": (
                to_epoch_microseconds(command.window_end)
                if command.window_end is not None
                else None
            ),
            "limitations_json": ContinuingReviewService._json(command.limitations),
            "rationale": command.rationale,
            "source_version_id": str(command.source_version_id),
            "source_authority_version_id": str(command.source_authority_version_id),
            "applicability_version_id": str(command.applicability_version_id),
            "responsibility_version_id": str(command.responsibility_version_id),
            "assignment_version_id": str(command.assignment_version_id),
            "predecessor_version_id": ContinuingReviewService._optional(
                command.predecessor_version_id
            ),
            "knowledge_cutoff_us": to_epoch_microseconds(command.knowledge_cutoff),
        }

    @staticmethod
    def _digest(command: ReviewCommand) -> str:
        normalized = ContinuingReviewService._normalize(command)
        assert isinstance(normalized, dict)
        return canonical_command_digest(normalized)

    @staticmethod
    def _normalize(value: object) -> JsonValue:
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, Enum):
            return ContinuingReviewService._normalize(value.value)
        if is_dataclass(value) and not isinstance(value, type):
            return {
                field.name: ContinuingReviewService._normalize(getattr(value, field.name))
                for field in fields(value)
            }
        if isinstance(value, (tuple, list, set, frozenset)):
            return [ContinuingReviewService._normalize(item) for item in value]
        if isinstance(value, dict):
            return {
                str(key): ContinuingReviewService._normalize(item) for key, item in value.items()
            }
        return str(value)

    @staticmethod
    def _json(values: tuple[object, ...]) -> str:
        return json.dumps([str(value) for value in values], separators=(",", ":"))

    @staticmethod
    def _ids(values: tuple[RecordVersionId, ...]) -> list[str]:
        return [str(value) for value in values]

    @staticmethod
    def _optional(value: RecordVersionId | None) -> str | None:
        return str(value) if value is not None else None

    @staticmethod
    def _datetime(value: datetime | None) -> str | None:
        return value.isoformat() if value is not None else None
