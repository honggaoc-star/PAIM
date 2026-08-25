"""Atomic prospective Value/Risk Finish, Adequacy, and Reliance service."""

from __future__ import annotations

import json
from contextlib import AbstractContextManager
from datetime import datetime
from typing import Protocol, cast

from paim.assessment_review.models import (
    AdequacyOutcome,
    AssessmentLane,
    AssessmentSelection,
    CommandIdentity,
    CompleteReviewCommand,
    DesignateRelianceCommand,
    DetermineAdequacyCommand,
    FinishAssessmentCommand,
    ReviewSelectionKind,
)
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
from paim.integrity.time import Clock, EffectiveInterval, require_utc, to_epoch_microseconds
from paim.persistence.ports import CommandOutcome, IdempotencyFact
from paim.responsibility.models import ObligationKind


class AssessmentStore(Protocol):
    def semantic_transaction(self) -> AbstractContextManager[ContinuityTransaction]: ...
    def read_transaction(self) -> AbstractContextManager[ContinuityTransaction]: ...


class AssessmentReviewConflict(RuntimeError):
    pass


class AssessmentReviewAccessDenied(RuntimeError):
    def __init__(self) -> None:
        super().__init__("software access not established")


_FINISH_OBLIGATION = {
    AssessmentLane.VALUE: ObligationKind.FINISH_VALUE_ASSESSMENT,
    AssessmentLane.RISK: ObligationKind.FINISH_RISK_ASSESSMENT,
}
_ADEQUACY_OBLIGATION = {
    AssessmentLane.VALUE: ObligationKind.REVIEW_VALUE_ASSESSMENT_ADEQUACY,
    AssessmentLane.RISK: ObligationKind.REVIEW_RISK_ASSESSMENT_ADEQUACY,
}
_RELIANCE_OBLIGATION = {
    AssessmentLane.VALUE: ObligationKind.DESIGNATE_VALUE_ASSESSMENT_RELIANCE,
    AssessmentLane.RISK: ObligationKind.DESIGNATE_RISK_ASSESSMENT_RELIANCE,
}
_INFORMATION_FAMILIES = frozenset(
    {"evidence", "evidence-applicability", "authority-record", "authority-gap"}
)


class AssessmentReviewService:
    """Prospective lane service; legacy Fitness/Selection are never candidates."""

    def __init__(
        self, store: AssessmentStore, clock: Clock, access: ContinuityAccessPolicy
    ) -> None:
        self._store = store
        self._clock = clock
        self._access = access

    def finish_assessment(self, command: FinishAssessmentCommand) -> CommandOutcome:
        action = f"assessment.finish.{command.lane.value.casefold()}"
        digest = canonical_command_digest(
            cast("dict[str, JsonValue]", self._finish_payload(command))
        )
        self._require_access(command, action)
        recorded_at = self._clock.now()
        with self._store.semantic_transaction() as tx:
            replay = self._replay(
                tx, command.identity.idempotency_scope, command.identity.idempotency_key, digest
            )
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
            self._validate_information_basis(
                tx,
                command.information_basis_version_ids,
                command.configuration_version_id,
                command.effective_at,
                command.knowledge_cutoff,
            )
            self._validate_accountability(
                tx,
                case_id=command.case_id,
                context_digest=command.context.digest,
                actor_id=command.identity.actor_id,
                responsibility_version_id=command.responsibility_version_id,
                assignment_version_id=command.assignment_version_id,
                obligation=_FINISH_OBLIGATION[command.lane],
                effective_at=command.effective_at,
                known_at=recorded_at,
            )
            self._ensure_contract_context(tx, command.contract, command.context, recorded_at)
            observed = tx.select_current(
                SelectionQuery(
                    "prospective-assessment",
                    self._candidate_scope(command.lane, command.case_id),
                    command.effective_at,
                    recorded_at,
                    command.facts.assessment_record_id,
                )
            )
            self._expect(observed, command.expected_assessment_version_id)
            self._add_version(
                tx,
                command.facts.assessment_record_id,
                command.facts.assessment_version_id,
                "prospective-assessment",
                self._candidate_scope(command.lane, command.case_id),
                cast(
                    "dict[str, JsonValue]",
                    {
                        **command.content.as_dict(),
                        "lane": command.lane.value,
                        "decision_use": command.decision_use,
                        "assessed_scope": command.assessed_scope,
                        "information_basis_version_ids": self._ids(
                            command.information_basis_version_ids
                        ),
                        "limitations": list(command.limitations),
                    },
                ),
                command.effective_at,
                recorded_at,
                command.identity.actor_id,
                command.contract.key,
                command.context.digest,
            )
            if command.expected_assessment_version_id is None:
                tx.insert_projection(
                    "assessment_candidate_records",
                    {
                        "record_id": str(command.facts.assessment_record_id),
                        "lane": command.lane.value,
                        "case_id": str(command.case_id),
                    },
                )
            tx.insert_projection(
                "assessment_candidate_versions",
                {
                    "version_id": str(command.facts.assessment_version_id),
                    "record_id": str(command.facts.assessment_record_id),
                    "lane": command.lane.value,
                    "case_id": str(command.case_id),
                    "configuration_version_id": str(command.configuration_version_id),
                    "context_digest": command.context.digest,
                    "decision_use": command.decision_use,
                    "assessed_scope": command.assessed_scope,
                    "information_basis_version_ids_json": json.dumps(
                        self._ids(command.information_basis_version_ids)
                    ),
                    "responsibility_version_id": str(command.responsibility_version_id),
                    "assignment_version_id": str(command.assignment_version_id),
                    "knowledge_cutoff_us": to_epoch_microseconds(command.knowledge_cutoff),
                    "predecessor_version_id": self._optional(
                        command.expected_assessment_version_id
                    ),
                },
            )
            self._add_version(
                tx,
                command.facts.readiness_record_id,
                command.facts.readiness_version_id,
                "assessment-readiness",
                self._readiness_scope(
                    command.lane,
                    command.case_id,
                    command.configuration_version_id,
                    command.decision_use,
                    command.facts.assessment_version_id,
                ),
                {
                    "lane": command.lane.value,
                    "assessment_version_id": str(command.facts.assessment_version_id),
                    "result": "READY_FOR_INDEPENDENT_REVIEW",
                    "rationale": command.rationale,
                    "limitations": list(command.limitations),
                },
                command.effective_at,
                recorded_at,
                command.identity.actor_id,
                command.contract.key,
                command.context.digest,
            )
            tx.insert_projection(
                "assessment_readiness_records",
                {"record_id": str(command.facts.readiness_record_id)},
            )
            tx.insert_projection(
                "assessment_readiness_versions",
                {
                    "version_id": str(command.facts.readiness_version_id),
                    "record_id": str(command.facts.readiness_record_id),
                    "lane": command.lane.value,
                    "assessment_version_id": str(command.facts.assessment_version_id),
                    "case_id": str(command.case_id),
                    "configuration_version_id": str(command.configuration_version_id),
                    "context_digest": command.context.digest,
                    "decision_use": command.decision_use,
                    "assessed_scope": command.assessed_scope,
                    "information_basis_version_ids_json": json.dumps(
                        self._ids(command.information_basis_version_ids)
                    ),
                    "responsibility_version_id": str(command.responsibility_version_id),
                    "assignment_version_id": str(command.assignment_version_id),
                    "knowledge_cutoff_us": to_epoch_microseconds(command.knowledge_cutoff),
                },
            )
            relationships, statuses = self._successor_history(
                tx,
                command.expected_assessment_version_id,
                command.facts.assessment_version_id,
                command.effective_at,
                recorded_at,
                command.identity.actor_id,
                command.contract.key,
                command.context.digest,
            )
            return self._finish_commit(
                tx,
                command.identity,
                digest,
                command.facts.assessment_record_id,
                (command.facts.assessment_version_id, command.facts.readiness_version_id),
                statuses,
                relationships,
                command.context.digest,
                command.effective_at,
                recorded_at,
                "ASSESSMENT_FINISH_COMMITTED",
            )

    def determine_adequacy(self, command: DetermineAdequacyCommand) -> CommandOutcome:
        return self._adequacy_or_reliance(command, None)

    def designate_reliance(self, command: DesignateRelianceCommand) -> CommandOutcome:
        return self._adequacy_or_reliance(None, command)

    def complete_review(self, command: CompleteReviewCommand) -> CommandOutcome:
        adequacy, reliance = command.adequacy, command.reliance
        if (
            adequacy.identity != reliance.identity
            or adequacy.lane is not reliance.lane
            or adequacy.case_id != reliance.case_id
            or adequacy.configuration_version_id != reliance.configuration_version_id
            or adequacy.assessment_version_id != reliance.assessment_version_id
            or adequacy.readiness_version_id != reliance.readiness_version_id
            or adequacy.context != reliance.context
            or adequacy.contract != reliance.contract
            or adequacy.decision_use != reliance.decision_use
            or adequacy.assessed_scope != reliance.assessed_scope
            or adequacy.information_basis_version_ids != reliance.information_basis_version_ids
            or adequacy.effective_at != reliance.effective_at
            or adequacy.knowledge_cutoff != reliance.knowledge_cutoff
            or adequacy.outcome is not AdequacyOutcome.ADEQUATE
            or adequacy.facts.version_id != reliance.adequacy_version_id
        ):
            raise AssessmentReviewConflict(
                "combined review intended facts are not exact and coherent"
            )
        action = f"assessment.review.complete.{adequacy.lane.value.casefold()}"
        digest = canonical_command_digest(
            cast(
                "dict[str, JsonValue]",
                {
                    "adequacy": self._adequacy_payload(adequacy),
                    "reliance": self._reliance_payload(reliance),
                },
            )
        )
        self._require_access(adequacy, action)
        recorded_at = self._clock.now()
        with self._store.semantic_transaction() as tx:
            replay = self._replay(
                tx, adequacy.identity.idempotency_scope, adequacy.identity.idempotency_key, digest
            )
            if replay is not None:
                return replay
            self._require_access(adequacy, action)
            self._validate_review_common(tx, adequacy, recorded_at)
            self._validate_accountability(
                tx,
                case_id=adequacy.case_id,
                context_digest=adequacy.context.digest,
                actor_id=adequacy.identity.actor_id,
                responsibility_version_id=adequacy.responsibility_version_id,
                assignment_version_id=adequacy.assignment_version_id,
                obligation=_ADEQUACY_OBLIGATION[adequacy.lane],
                effective_at=adequacy.effective_at,
                known_at=recorded_at,
            )
            self._validate_accountability(
                tx,
                case_id=reliance.case_id,
                context_digest=reliance.context.digest,
                actor_id=reliance.identity.actor_id,
                responsibility_version_id=reliance.responsibility_version_id,
                assignment_version_id=reliance.assignment_version_id,
                obligation=_RELIANCE_OBLIGATION[reliance.lane],
                effective_at=reliance.effective_at,
                known_at=recorded_at,
            )
            if self._adequate_candidates(tx, adequacy, recorded_at):
                raise AssessmentReviewConflict(
                    "combined review requires one exact candidate and no competing adequate choice"
                )
            self._write_adequacy(tx, adequacy, recorded_at)
            self._validate_reliance(tx, reliance, recorded_at)
            self._write_reliance(tx, reliance, recorded_at)
            return self._finish_commit(
                tx,
                adequacy.identity,
                digest,
                adequacy.facts.record_id,
                (adequacy.facts.version_id, reliance.facts.version_id),
                (),
                (),
                adequacy.context.digest,
                adequacy.effective_at,
                recorded_at,
                "COMBINED_ASSESSMENT_REVIEW_COMMITTED",
            )

    def select_readiness(self, **values: object) -> AssessmentSelection:
        return self._select("assessment-readiness", **values)

    def select_adequacy(self, **values: object) -> AssessmentSelection:
        return self._select("assessment-adequacy", **values)

    def select_reliance(self, **values: object) -> AssessmentSelection:
        return self._select("assessment-reliance", **values)

    def _adequacy_or_reliance(
        self,
        adequacy: DetermineAdequacyCommand | None,
        reliance: DesignateRelianceCommand | None,
    ) -> CommandOutcome:
        command = adequacy or reliance
        assert command is not None
        kind = "adequacy" if adequacy else "reliance"
        action = f"assessment.{kind}.{command.lane.value.casefold()}"
        payload = (
            self._adequacy_payload(adequacy)
            if adequacy
            else self._reliance_payload(cast(DesignateRelianceCommand, reliance))
        )
        digest = canonical_command_digest(cast("dict[str, JsonValue]", payload))
        self._require_access(command, action)
        recorded_at = self._clock.now()
        with self._store.semantic_transaction() as tx:
            replay = self._replay(
                tx, command.identity.idempotency_scope, command.identity.idempotency_key, digest
            )
            if replay is not None:
                return replay
            self._require_access(command, action)
            if adequacy:
                self._validate_review_common(tx, adequacy, recorded_at)
                self._validate_accountability(
                    tx,
                    case_id=adequacy.case_id,
                    context_digest=adequacy.context.digest,
                    actor_id=adequacy.identity.actor_id,
                    responsibility_version_id=adequacy.responsibility_version_id,
                    assignment_version_id=adequacy.assignment_version_id,
                    obligation=_ADEQUACY_OBLIGATION[adequacy.lane],
                    effective_at=adequacy.effective_at,
                    known_at=recorded_at,
                )
                self._write_adequacy(tx, adequacy, recorded_at)
                record_id, versions = adequacy.facts.record_id, (adequacy.facts.version_id,)
            else:
                assert reliance is not None
                self._validate_reliance(tx, reliance, recorded_at)
                self._validate_accountability(
                    tx,
                    case_id=reliance.case_id,
                    context_digest=reliance.context.digest,
                    actor_id=reliance.identity.actor_id,
                    responsibility_version_id=reliance.responsibility_version_id,
                    assignment_version_id=reliance.assignment_version_id,
                    obligation=_RELIANCE_OBLIGATION[reliance.lane],
                    effective_at=reliance.effective_at,
                    known_at=recorded_at,
                )
                self._write_reliance(tx, reliance, recorded_at)
                record_id, versions = reliance.facts.record_id, (reliance.facts.version_id,)
            return self._finish_commit(
                tx,
                command.identity,
                digest,
                record_id,
                versions,
                (),
                (),
                command.context.digest,
                command.effective_at,
                recorded_at,
                f"ASSESSMENT_{kind.upper()}_COMMITTED",
            )

    def _validate_review_common(
        self, tx: ContinuityTransaction, command: DetermineAdequacyCommand, recorded_at: datetime
    ) -> None:
        self._validate_case_context(
            tx,
            command.case_id,
            command.configuration_version_id,
            command.context.digest,
            command.effective_at,
            recorded_at,
        )
        self._validate_information_basis(
            tx,
            command.information_basis_version_ids,
            command.configuration_version_id,
            command.effective_at,
            command.knowledge_cutoff,
        )
        self._validate_candidate_readiness(
            tx,
            command.lane,
            command.assessment_version_id,
            command.readiness_version_id,
            command.case_id,
            command.configuration_version_id,
            command.context.digest,
            command.decision_use,
            command.assessed_scope,
            command.information_basis_version_ids,
            command.effective_at,
            recorded_at,
        )
        self._ensure_contract_context(tx, command.contract, command.context, recorded_at)
        observed = tx.select_current(
            SelectionQuery(
                "assessment-adequacy",
                self._adequacy_scope(
                    command.lane,
                    command.case_id,
                    command.configuration_version_id,
                    command.decision_use,
                    command.assessment_version_id,
                ),
                command.effective_at,
                recorded_at,
                command.facts.record_id,
            )
        )
        self._expect(observed, command.expected_adequacy_version_id)

    def _validate_reliance(
        self, tx: ContinuityTransaction, command: DesignateRelianceCommand, recorded_at: datetime
    ) -> None:
        self._validate_case_context(
            tx,
            command.case_id,
            command.configuration_version_id,
            command.context.digest,
            command.effective_at,
            recorded_at,
        )
        self._validate_information_basis(
            tx,
            command.information_basis_version_ids,
            command.configuration_version_id,
            command.effective_at,
            command.knowledge_cutoff,
        )
        self._validate_candidate_readiness(
            tx,
            command.lane,
            command.assessment_version_id,
            command.readiness_version_id,
            command.case_id,
            command.configuration_version_id,
            command.context.digest,
            command.decision_use,
            command.assessed_scope,
            command.information_basis_version_ids,
            command.effective_at,
            recorded_at,
        )
        adequacy = tx.projection_rows(
            "assessment_adequacy_versions", version_id=str(command.adequacy_version_id)
        )
        if len(adequacy) != 1:
            raise AssessmentReviewConflict("exact adequacy determination is not established")
        row = adequacy[0]
        self._require_current_version(
            tx,
            command.adequacy_version_id,
            command.effective_at,
            recorded_at,
            "exact adequacy determination is stale",
        )
        selected_adequacy = tx.select_current(
            SelectionQuery(
                "assessment-adequacy",
                self._adequacy_scope(
                    command.lane,
                    command.case_id,
                    command.configuration_version_id,
                    command.decision_use,
                    command.assessment_version_id,
                ),
                command.effective_at,
                recorded_at,
            )
        )
        if not (
            isinstance(selected_adequacy, SelectionFound)
            and selected_adequacy.candidate.version_id == command.adequacy_version_id
        ):
            raise AssessmentReviewConflict(
                "assessment adequacy is absent or conflicting; no reliance winner"
            )
        if (
            row["outcome"] != AdequacyOutcome.ADEQUATE.value
            or row["lane"] != command.lane.value
            or row["assessment_version_id"] != str(command.assessment_version_id)
            or row["readiness_version_id"] != str(command.readiness_version_id)
            or row["case_id"] != str(command.case_id)
            or row["configuration_version_id"] != str(command.configuration_version_id)
            or row["context_digest"] != command.context.digest
            or row["decision_use"] != command.decision_use
            or row["assessed_scope"] != command.assessed_scope
            or json.loads(cast(str, row["information_basis_version_ids_json"]))
            != self._ids(command.information_basis_version_ids)
        ):
            raise AssessmentReviewConflict(
                "reliance requires exact positive adequacy for the same lane and use"
            )
        candidates = self._adequate_candidates(tx, command, recorded_at)
        other = {str(value) for value in candidates if value != command.assessment_version_id}
        dispositions = {
            str(value.assessment_version_id) for value in command.candidate_dispositions
        }
        if other != dispositions or len(dispositions) != len(command.candidate_dispositions):
            raise AssessmentReviewConflict(
                "every materially competing adequate candidate requires explicit disposition"
            )
        observed = tx.select_current(
            SelectionQuery(
                "assessment-reliance",
                self._review_scope(
                    command.lane,
                    command.case_id,
                    command.configuration_version_id,
                    command.decision_use,
                ),
                command.effective_at,
                recorded_at,
                command.facts.record_id,
            )
        )
        self._expect(observed, command.expected_reliance_version_id)
        self._ensure_contract_context(tx, command.contract, command.context, recorded_at)

    def _write_adequacy(
        self, tx: ContinuityTransaction, command: DetermineAdequacyCommand, recorded_at: datetime
    ) -> None:
        self._add_version(
            tx,
            command.facts.record_id,
            command.facts.version_id,
            "assessment-adequacy",
            self._adequacy_scope(
                command.lane,
                command.case_id,
                command.configuration_version_id,
                command.decision_use,
                command.assessment_version_id,
            ),
            cast(
                "dict[str, JsonValue]",
                {
                    "lane": command.lane.value,
                    "assessment_version_id": str(command.assessment_version_id),
                    "outcome": command.outcome.value,
                    "material_reasons": list(command.material_reasons),
                    "rationale": command.rationale,
                    "limitations": list(command.limitations),
                    "uncertainty": command.uncertainty,
                },
            ),
            command.effective_at,
            recorded_at,
            command.identity.actor_id,
            command.contract.key,
            command.context.digest,
        )
        if command.expected_adequacy_version_id is None:
            tx.insert_projection(
                "assessment_adequacy_records", {"record_id": str(command.facts.record_id)}
            )
        tx.insert_projection(
            "assessment_adequacy_versions",
            {
                "version_id": str(command.facts.version_id),
                "record_id": str(command.facts.record_id),
                "lane": command.lane.value,
                "assessment_version_id": str(command.assessment_version_id),
                "readiness_version_id": str(command.readiness_version_id),
                "case_id": str(command.case_id),
                "configuration_version_id": str(command.configuration_version_id),
                "context_digest": command.context.digest,
                "decision_use": command.decision_use,
                "assessed_scope": command.assessed_scope,
                "information_basis_version_ids_json": json.dumps(
                    self._ids(command.information_basis_version_ids)
                ),
                "outcome": command.outcome.value,
                "material_reasons_json": json.dumps(list(command.material_reasons)),
                "limitations_json": json.dumps(list(command.limitations)),
                "rationale": command.rationale,
                "uncertainty": command.uncertainty,
                "responsibility_version_id": str(command.responsibility_version_id),
                "assignment_version_id": str(command.assignment_version_id),
                "knowledge_cutoff_us": to_epoch_microseconds(command.knowledge_cutoff),
                "predecessor_version_id": self._optional(command.expected_adequacy_version_id),
            },
        )
        self._successor_history(
            tx,
            command.expected_adequacy_version_id,
            command.facts.version_id,
            command.effective_at,
            recorded_at,
            command.identity.actor_id,
            command.contract.key,
            command.context.digest,
        )

    def _write_reliance(
        self, tx: ContinuityTransaction, command: DesignateRelianceCommand, recorded_at: datetime
    ) -> None:
        dispositions = [
            {
                "assessment_version_id": str(value.assessment_version_id),
                "disposition": value.disposition,
                "rationale": value.rationale,
            }
            for value in command.candidate_dispositions
        ]
        self._add_version(
            tx,
            command.facts.record_id,
            command.facts.version_id,
            "assessment-reliance",
            self._review_scope(
                command.lane,
                command.case_id,
                command.configuration_version_id,
                command.decision_use,
            ),
            cast(
                "dict[str, JsonValue]",
                {
                    "lane": command.lane.value,
                    "assessment_version_id": str(command.assessment_version_id),
                    "adequacy_version_id": str(command.adequacy_version_id),
                    "candidate_dispositions": dispositions,
                    "rationale": command.rationale,
                },
            ),
            command.effective_at,
            recorded_at,
            command.identity.actor_id,
            command.contract.key,
            command.context.digest,
        )
        if command.expected_reliance_version_id is None:
            tx.insert_projection(
                "assessment_reliance_records", {"record_id": str(command.facts.record_id)}
            )
        tx.insert_projection(
            "assessment_reliance_versions",
            {
                "version_id": str(command.facts.version_id),
                "record_id": str(command.facts.record_id),
                "lane": command.lane.value,
                "assessment_version_id": str(command.assessment_version_id),
                "readiness_version_id": str(command.readiness_version_id),
                "adequacy_version_id": str(command.adequacy_version_id),
                "case_id": str(command.case_id),
                "configuration_version_id": str(command.configuration_version_id),
                "context_digest": command.context.digest,
                "decision_use": command.decision_use,
                "assessed_scope": command.assessed_scope,
                "information_basis_version_ids_json": json.dumps(
                    self._ids(command.information_basis_version_ids)
                ),
                "candidate_dispositions_json": json.dumps(dispositions, sort_keys=True),
                "rationale": command.rationale,
                "responsibility_version_id": str(command.responsibility_version_id),
                "assignment_version_id": str(command.assignment_version_id),
                "knowledge_cutoff_us": to_epoch_microseconds(command.knowledge_cutoff),
                "predecessor_version_id": self._optional(command.expected_reliance_version_id),
            },
        )
        self._successor_history(
            tx,
            command.expected_reliance_version_id,
            command.facts.version_id,
            command.effective_at,
            recorded_at,
            command.identity.actor_id,
            command.contract.key,
            command.context.digest,
        )

    def _validate_candidate_readiness(
        self,
        tx: ContinuityTransaction,
        lane: AssessmentLane,
        assessment_version_id: RecordVersionId,
        readiness_version_id: RecordVersionId,
        case_id: RecordId,
        configuration_version_id: RecordVersionId,
        context_digest: str,
        decision_use: str,
        assessed_scope: str,
        basis: tuple[RecordVersionId, ...],
        effective_at: datetime,
        known_at: datetime,
    ) -> None:
        self._require_current_version(
            tx, assessment_version_id, effective_at, known_at, "exact assessment candidate is stale"
        )
        rows = tx.projection_rows(
            "assessment_readiness_versions", version_id=str(readiness_version_id)
        )
        if len(rows) != 1:
            raise AssessmentReviewConflict("exact assessment readiness is not established")
        row = rows[0]
        self._require_current_version(
            tx, readiness_version_id, effective_at, known_at, "exact assessment readiness is stale"
        )
        selected_readiness = tx.select_current(
            SelectionQuery(
                "assessment-readiness",
                self._readiness_scope(
                    lane,
                    case_id,
                    configuration_version_id,
                    decision_use,
                    assessment_version_id,
                ),
                effective_at,
                known_at,
            )
        )
        if not (
            isinstance(selected_readiness, SelectionFound)
            and selected_readiness.candidate.version_id == readiness_version_id
        ):
            raise AssessmentReviewConflict(
                "assessment readiness is absent or conflicting; no implicit winner"
            )
        if (
            row["lane"] != lane.value
            or row["assessment_version_id"] != str(assessment_version_id)
            or row["case_id"] != str(case_id)
            or row["configuration_version_id"] != str(configuration_version_id)
            or row["context_digest"] != context_digest
            or row["decision_use"] != decision_use
            or row["assessed_scope"] != assessed_scope
            or json.loads(cast(str, row["information_basis_version_ids_json"])) != self._ids(basis)
        ):
            raise AssessmentReviewConflict("readiness does not bind the exact assessment context")

    def _validate_case_context(
        self,
        tx: ContinuityTransaction,
        case_id: RecordId,
        configuration_version_id: RecordVersionId,
        context_digest: str,
        effective_at: datetime,
        known_at: datetime,
    ) -> None:
        status_records = tx.projection_rows("case_continuity_status_records", case_id=str(case_id))
        if len(status_records) != 1:
            raise AssessmentReviewConflict("exact prospective OPEN Case is not established")
        status_record = RecordId.parse(str(status_records[0]["record_id"]))
        selected = tx.select_current(
            SelectionQuery(
                "case-continuity-status", f"case:{case_id}", effective_at, known_at, status_record
            )
        )
        if not isinstance(selected, SelectionFound):
            raise AssessmentReviewConflict("Case continuity status is absent or conflicting")
        status = tx.projection_rows(
            "case_continuity_status_versions", version_id=str(selected.candidate.version_id)
        )
        if len(status) != 1 or status[0]["status"] != "OPEN":
            raise AssessmentReviewConflict("prospective Case is not OPEN")
        governing = tx.select_current(
            SelectionQuery("governing-configuration", f"case:{case_id}", effective_at, known_at)
        )
        if not isinstance(governing, SelectionFound):
            raise AssessmentReviewConflict("governing Configuration is absent or conflicting")
        rows = tx.projection_rows(
            "governing_configuration_designations", version_id=str(governing.candidate.version_id)
        )
        if len(rows) != 1 or rows[0]["configuration_version_id"] != str(configuration_version_id):
            raise AssessmentReviewConflict("command does not bind exact governing Configuration")
        semantics = tx.projection_rows(
            "record_version_semantics", version_id=str(configuration_version_id)
        )
        if len(semantics) != 1 or semantics[0]["context_digest"] != context_digest:
            raise AssessmentReviewConflict("governing Configuration exact context mismatch")

    def _validate_information_basis(
        self,
        tx: ContinuityTransaction,
        basis: tuple[RecordVersionId, ...],
        configuration_version_id: RecordVersionId,
        effective_at: datetime,
        known_at: datetime,
    ) -> None:
        applicability = 0
        for version_id in basis:
            version = tx.get_version(version_id)
            if version is None or version.family not in _INFORMATION_FAMILIES:
                raise AssessmentReviewConflict(
                    "exact information/Applicability prerequisite is unavailable"
                )
            self._require_current_version(
                tx,
                version_id,
                effective_at,
                known_at,
                "information/Applicability prerequisite is stale",
            )
            if version.family == "evidence-applicability":
                rows = tx.projection_rows(
                    "evidence_applicability_versions", version_id=str(version_id)
                )
                if (
                    len(rows) != 1
                    or rows[0]["configuration_version_id"] != str(configuration_version_id)
                    or rows[0]["outcome"] in {"NOT_APPLICABLE", "INDETERMINATE"}
                ):
                    raise AssessmentReviewConflict(
                        "material Evidence Applicability prerequisite is incomplete"
                    )
                applicability += 1
        if applicability == 0:
            raise AssessmentReviewConflict(
                "material Evidence Applicability prerequisite is not established"
            )

    def _validate_accountability(
        self,
        tx: ContinuityTransaction,
        *,
        case_id: RecordId,
        context_digest: str,
        actor_id: RecordId,
        responsibility_version_id: RecordVersionId,
        assignment_version_id: RecordVersionId,
        obligation: ObligationKind,
        effective_at: datetime,
        known_at: datetime,
    ) -> None:
        responsibility = tx.projection_rows(
            "responsibility_versions", version_id=str(responsibility_version_id)
        )
        assignment = tx.projection_rows(
            "responsibility_assignment_versions", version_id=str(assignment_version_id)
        )
        if len(responsibility) != 1 or len(assignment) != 1:
            raise AssessmentReviewConflict(
                "exact lane Responsibility/assignment is not established"
            )
        r, a = responsibility[0], assignment[0]
        if (
            r["obligation_kind"] != obligation.value
            or r["owning_case_id"] != str(case_id)
            or r["context_digest"] != context_digest
            or a["responsibility_version_id"] != str(responsibility_version_id)
            or a["actor_id"] != str(actor_id)
            or a["state"] != "ASSIGNED"
        ):
            raise AssessmentReviewConflict("lane accountability does not match exact context")
        self._require_current_version(
            tx, responsibility_version_id, effective_at, known_at, "lane Responsibility is stale"
        )
        self._require_current_version(
            tx, assignment_version_id, effective_at, known_at, "lane assignment is stale"
        )
        eligible = []
        for row in tx.projection_rows(
            "responsibility_assignment_versions", signature_digest=str(r["signature_digest"])
        ):
            try:
                self._require_current_version(
                    tx, RecordVersionId.parse(str(row["version_id"])), effective_at, known_at, ""
                )
            except AssessmentReviewConflict:
                continue
            if (
                row["state"] == "ASSIGNED"
                and cast(int, row["effective_from_us"]) <= to_epoch_microseconds(effective_at)
                and (
                    row["effective_to_us"] is None
                    or to_epoch_microseconds(effective_at) < cast(int, row["effective_to_us"])
                )
            ):
                eligible.append(row)
        if len(eligible) != 1 or eligible[0]["version_id"] != str(assignment_version_id):
            raise AssessmentReviewConflict("lane Responsibility vacancy or conflict")
        basis = tx.projection_rows(
            "assignment_basis_versions",
            version_id=str(a["assignment_basis_version_id"]),
        )
        if len(basis) != 1 or basis[0]["state"] != "ACTIVE":
            raise AssessmentReviewConflict("exact assignment authority basis is not active")
        basis_row = basis[0]
        basis_version_id = RecordVersionId.parse(str(basis_row["version_id"]))
        self._require_current_version(
            tx,
            basis_version_id,
            effective_at,
            known_at,
            "exact assignment authority basis is stale",
        )
        source_id = RecordVersionId.parse(str(basis_row["basis_source_version_id"]))
        self._require_current_version(
            tx,
            source_id,
            effective_at,
            known_at,
            "assignment authority source is stale",
        )
        source = tx.get_version(source_id)
        authority = source.content.get("assignment_authority") if source else None
        kinds = authority.get("allowed_obligation_kinds") if isinstance(authority, dict) else None
        cases = authority.get("allowed_case_ids") if isinstance(authority, dict) else None
        signatures = (
            authority.get("allowed_signature_digests") if isinstance(authority, dict) else None
        )
        if (
            not isinstance(authority, dict)
            or not isinstance(kinds, list)
            or not isinstance(cases, list)
            or not isinstance(signatures, list)
            or obligation.value not in kinds
            or str(case_id) not in cases
            or str(r["signature_digest"]) not in signatures
            or authority.get("context_digest") != context_digest
            or basis_row["context_digest"] != context_digest
        ):
            raise AssessmentReviewConflict(
                "assignment authority does not permit the exact lane act"
            )

    def _adequate_candidates(
        self,
        tx: ContinuityTransaction,
        command: DetermineAdequacyCommand | DesignateRelianceCommand,
        known_at: datetime,
    ) -> tuple[RecordVersionId, ...]:
        rows = tx.projection_rows(
            "assessment_adequacy_versions",
            lane=command.lane.value,
            case_id=str(command.case_id),
            configuration_version_id=str(command.configuration_version_id),
            decision_use=command.decision_use,
        )
        found: list[RecordVersionId] = []
        for row in rows:
            if row["outcome"] != AdequacyOutcome.ADEQUATE.value:
                continue
            version_id = RecordVersionId.parse(str(row["version_id"]))
            assessment_version_id = RecordVersionId.parse(str(row["assessment_version_id"]))
            readiness_version_id = RecordVersionId.parse(str(row["readiness_version_id"]))
            try:
                self._require_current_version(tx, version_id, command.effective_at, known_at, "")
                self._validate_candidate_readiness(
                    tx,
                    command.lane,
                    assessment_version_id,
                    readiness_version_id,
                    command.case_id,
                    command.configuration_version_id,
                    command.context.digest,
                    command.decision_use,
                    str(row["assessed_scope"]),
                    tuple(
                        RecordVersionId.parse(value)
                        for value in json.loads(
                            cast(str, row["information_basis_version_ids_json"])
                        )
                    ),
                    command.effective_at,
                    known_at,
                )
            except AssessmentReviewConflict:
                continue
            found.append(assessment_version_id)
        return tuple(sorted(set(found), key=str))

    def _select(self, family: str, **values: object) -> AssessmentSelection:
        lane = cast(AssessmentLane, values["lane"])
        case_id = cast(RecordId, values["case_id"])
        configuration_version_id = cast(RecordVersionId, values["configuration_version_id"])
        decision_use = cast(str, values["decision_use"])
        effective_at = cast(datetime, values["effective_at"])
        known_at = cast(datetime, values["known_at"])
        require_utc(effective_at)
        require_utc(known_at)
        scope = self._review_scope(lane, case_id, configuration_version_id, decision_use)
        if family == "assessment-readiness":
            scope = self._readiness_scope(
                lane,
                case_id,
                configuration_version_id,
                decision_use,
                cast(RecordVersionId, values["assessment_version_id"]),
            )
        elif family == "assessment-adequacy":
            scope = self._adequacy_scope(
                lane,
                case_id,
                configuration_version_id,
                decision_use,
                cast(RecordVersionId, values["assessment_version_id"]),
            )
        with self._store.read_transaction() as tx:
            selected = tx.select_current(SelectionQuery(family, scope, effective_at, known_at))
            if isinstance(selected, SelectionAbsent):
                return AssessmentSelection(ReviewSelectionKind.ABSENT, ())
            candidates = (
                selected.candidates
                if isinstance(selected, SelectionConflict)
                else (cast(SelectionFound, selected).candidate,)
            )
            eligible = tuple(
                item
                for item in candidates
                if self._selection_candidate_eligible(
                    tx, family, item.version_id, effective_at, known_at
                )
            )
            if not eligible:
                return AssessmentSelection(ReviewSelectionKind.ABSENT, ())
            if len(eligible) != 1:
                return AssessmentSelection(
                    ReviewSelectionKind.CONFLICT,
                    tuple(sorted((item.version_id for item in eligible), key=str)),
                )
            selected_version_id = eligible[0].version_id
            table = {
                "assessment-readiness": "assessment_readiness_versions",
                "assessment-adequacy": "assessment_adequacy_versions",
                "assessment-reliance": "assessment_reliance_versions",
            }[family]
            rows = tx.projection_rows(table, version_id=str(selected_version_id))
            if len(rows) != 1:
                return AssessmentSelection(ReviewSelectionKind.CONFLICT, (selected_version_id,))
            return AssessmentSelection(
                ReviewSelectionKind.ONE,
                (selected_version_id,),
                RecordVersionId.parse(str(rows[0]["assessment_version_id"])),
                str(rows[0].get("outcome") or "RELIED"),
            )

    def _selection_candidate_eligible(
        self,
        tx: ContinuityTransaction,
        family: str,
        version_id: RecordVersionId,
        effective_at: datetime,
        known_at: datetime,
    ) -> bool:
        table = {
            "assessment-readiness": "assessment_readiness_versions",
            "assessment-adequacy": "assessment_adequacy_versions",
            "assessment-reliance": "assessment_reliance_versions",
        }[family]
        rows = tx.projection_rows(table, version_id=str(version_id))
        if len(rows) != 1:
            return False
        row = rows[0]
        try:
            assessment_version_id = RecordVersionId.parse(str(row["assessment_version_id"]))
            self._require_current_version(tx, assessment_version_id, effective_at, known_at, "")
            if family == "assessment-readiness":
                return True
            readiness_version_id = RecordVersionId.parse(str(row["readiness_version_id"]))
            self._require_current_version(tx, readiness_version_id, effective_at, known_at, "")
            readiness = tx.projection_rows(
                "assessment_readiness_versions", version_id=str(readiness_version_id)
            )
            if len(readiness) != 1 or readiness[0]["assessment_version_id"] != str(
                assessment_version_id
            ):
                return False
            readiness_selected = tx.select_current(
                SelectionQuery(
                    "assessment-readiness",
                    self._readiness_scope(
                        AssessmentLane(str(row["lane"])),
                        RecordId.parse(str(row["case_id"])),
                        RecordVersionId.parse(str(row["configuration_version_id"])),
                        str(row["decision_use"]),
                        assessment_version_id,
                    ),
                    effective_at,
                    known_at,
                )
            )
            if not (
                isinstance(readiness_selected, SelectionFound)
                and readiness_selected.candidate.version_id == readiness_version_id
            ):
                return False
            if family == "assessment-adequacy":
                return True
            adequacy_version_id = RecordVersionId.parse(str(row["adequacy_version_id"]))
            self._require_current_version(tx, adequacy_version_id, effective_at, known_at, "")
            adequacy = tx.projection_rows(
                "assessment_adequacy_versions", version_id=str(adequacy_version_id)
            )
            if (
                len(adequacy) != 1
                or adequacy[0]["assessment_version_id"] != str(assessment_version_id)
                or adequacy[0]["outcome"] != AdequacyOutcome.ADEQUATE.value
            ):
                return False
            adequacy_selected = tx.select_current(
                SelectionQuery(
                    "assessment-adequacy",
                    self._adequacy_scope(
                        AssessmentLane(str(row["lane"])),
                        RecordId.parse(str(row["case_id"])),
                        RecordVersionId.parse(str(row["configuration_version_id"])),
                        str(row["decision_use"]),
                        assessment_version_id,
                    ),
                    effective_at,
                    known_at,
                )
            )
            return bool(
                isinstance(adequacy_selected, SelectionFound)
                and adequacy_selected.candidate.version_id == adequacy_version_id
            )
        except (AssessmentReviewConflict, KeyError, ValueError):
            return False

    @staticmethod
    def _require_current_version(
        tx: ContinuityTransaction,
        version_id: RecordVersionId,
        effective_at: datetime,
        known_at: datetime,
        reason: str,
    ) -> None:
        version = tx.get_version(version_id)
        if version is None:
            raise AssessmentReviewConflict(reason or "exact Version unavailable")
        selected = tx.select_current(
            SelectionQuery(version.family, version.scope, effective_at, known_at, version.record_id)
        )
        if not isinstance(selected, SelectionFound) or selected.candidate.version_id != version_id:
            raise AssessmentReviewConflict(reason or "exact Version is not current")

    @staticmethod
    def _expect(selected: object, expected: RecordVersionId | None) -> None:
        if expected is None and not isinstance(selected, SelectionAbsent):
            raise AssessmentReviewConflict("expected absent prospective record")
        if expected is not None and not (
            isinstance(selected, SelectionFound) and selected.candidate.version_id == expected
        ):
            raise AssessmentReviewConflict("stale exact predecessor; no retarget permitted")

    def _require_access(
        self,
        command: FinishAssessmentCommand | DetermineAdequacyCommand | DesignateRelianceCommand,
        action: str,
    ) -> None:
        identity = command.identity
        case_id = command.case_id
        if not self._access.authorize(
            principal_id=identity.principal_id,
            actor_id=str(identity.actor_id),
            action=action,
            case_id=case_id,
            write=True,
        ):
            raise AssessmentReviewAccessDenied()

    @staticmethod
    def _replay(
        tx: ContinuityTransaction, scope: str, key: str, digest: str
    ) -> CommandOutcome | None:
        existing = tx.get_idempotency(scope, key)
        if existing is None:
            return None
        if existing.digest != digest:
            raise AssessmentReviewConflict("IDEMPOTENCY KEY REUSE CONFLICT")
        return existing.outcome

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
        actor_id: RecordId,
        contract_key: str,
        context_digest: str,
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
                str(actor_id),
            )
        )
        tx.insert_projection(
            "record_version_semantics",
            {
                "version_id": str(version_id),
                "contract_key": contract_key,
                "context_digest": context_digest,
                "consumer_id": "gate8-slice-c",
                "adapter_key": None,
            },
        )

    @staticmethod
    def _ensure_contract_context(
        tx: ContinuityTransaction,
        contract: SemanticContractRef,
        context: ExactContextSet,
        recorded_at: datetime,
    ) -> None:
        key = contract.key
        if not tx.projection_rows("semantic_contracts", contract_key=key):
            tx.insert_projection(
                "semantic_contracts",
                {
                    "contract_key": key,
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
            "prospective-assessment",
            "assessment-readiness",
            "assessment-adequacy",
            "assessment-reliance",
        ):
            if not tx.projection_rows(
                "semantic_contract_families", contract_key=key, record_family=family
            ):
                tx.insert_projection(
                    "semantic_contract_families", {"contract_key": key, "record_family": family}
                )

    @staticmethod
    def _successor_history(
        tx: ContinuityTransaction,
        expected: RecordVersionId | None,
        successor: RecordVersionId,
        effective_at: datetime,
        recorded_at: datetime,
        actor_id: RecordId,
        contract_key: str,
        context_digest: str,
    ) -> tuple[tuple[RelationshipId, ...], tuple[EventId, ...]]:
        if expected is None:
            return (), ()
        relationship = VersionRelationship(
            RelationshipId.new(),
            expected,
            successor,
            RelationshipType.SUPERSESSION,
            recorded_at,
            "material assessment correction",
        )
        status = StatusEvent(
            EventId.new(),
            expected,
            "CURRENT",
            "SUPERSEDED",
            recorded_at,
            effective_at,
            str(actor_id),
            "material assessment correction",
        )
        tx.add_relationship(relationship)
        tx.add_status_event(status)
        tx.insert_projection(
            "version_relationship_semantics",
            {
                "relationship_id": str(relationship.relationship_id),
                "contract_key": contract_key,
                "context_digest": context_digest,
            },
        )
        tx.insert_projection(
            "status_event_semantics",
            {
                "event_id": str(status.event_id),
                "contract_key": contract_key,
                "context_digest": context_digest,
            },
        )
        return (relationship.relationship_id,), (status.event_id,)

    @staticmethod
    def _finish_commit(
        tx: ContinuityTransaction,
        identity: CommandIdentity,
        digest: str,
        record_id: RecordId,
        versions: tuple[RecordVersionId, ...],
        statuses: tuple[EventId, ...],
        relationships: tuple[RelationshipId, ...],
        context_digest: str,
        effective_at: datetime,
        recorded_at: datetime,
        action: str,
    ) -> CommandOutcome:
        audit = AuditFact(
            AuditId.new(),
            identity.principal_id,
            str(identity.actor_id),
            ActorResolution.PROVIDED,
            action,
            "COMMITTED",
            identity.command_id,
            identity.idempotency_scope,
            identity.idempotency_key,
            None,
            None,
            record_id,
            versions,
            "EXACT_CONTEXT",
            context_digest,
            effective_at,
            recorded_at,
            ("SEMANTIC_CONTRACT_BOUND", "VALUE_RISK_LANES_INDEPENDENT"),
            digest,
        )
        tx.add_audit(audit)
        outcome = CommandOutcome(
            str(identity.command_id),
            str(record_id),
            tuple(str(value) for value in versions),
            tuple(str(value) for value in statuses),
            tuple(str(value) for value in relationships),
            str(audit.audit_id),
        )
        tx.add_idempotency(
            IdempotencyFact(
                identity.idempotency_scope,
                identity.idempotency_key,
                digest,
                str(identity.command_id),
                outcome,
                recorded_at,
            )
        )
        return outcome

    @staticmethod
    def _candidate_scope(lane: AssessmentLane, case_id: RecordId) -> str:
        return f"assessment:{lane.value}:case:{case_id}"

    @staticmethod
    def _review_scope(
        lane: AssessmentLane,
        case_id: RecordId,
        configuration_version_id: RecordVersionId,
        decision_use: str,
    ) -> str:
        digest = canonical_command_digest({"decision_use": decision_use})
        return (
            f"assessment-review:{lane.value}:case:{case_id}:"
            f"configuration:{configuration_version_id}:use:{digest}"
        )

    @classmethod
    def _readiness_scope(
        cls,
        lane: AssessmentLane,
        case_id: RecordId,
        configuration_version_id: RecordVersionId,
        decision_use: str,
        assessment_version_id: RecordVersionId,
    ) -> str:
        base = cls._review_scope(lane, case_id, configuration_version_id, decision_use)
        return f"{base}:assessment:{assessment_version_id}"

    @classmethod
    def _adequacy_scope(
        cls,
        lane: AssessmentLane,
        case_id: RecordId,
        configuration_version_id: RecordVersionId,
        decision_use: str,
        assessment_version_id: RecordVersionId,
    ) -> str:
        base = cls._review_scope(lane, case_id, configuration_version_id, decision_use)
        return f"{base}:assessment:{assessment_version_id}"

    @staticmethod
    def _ids(values: tuple[RecordVersionId, ...]) -> list[str]:
        return [str(value) for value in values]

    @staticmethod
    def _optional(value: RecordVersionId | None) -> str | None:
        return str(value) if value else None

    @staticmethod
    def _finish_payload(command: FinishAssessmentCommand) -> dict[str, object]:
        return {
            "kind": "finish",
            "lane": command.lane.value,
            "case": str(command.case_id),
            "configuration": str(command.configuration_version_id),
            "assessment_record": str(command.facts.assessment_record_id),
            "assessment_version": str(command.facts.assessment_version_id),
            "readiness_record": str(command.facts.readiness_record_id),
            "readiness_version": str(command.facts.readiness_version_id),
            "content": command.content.as_dict(),
            "decision_use": command.decision_use,
            "scope": command.assessed_scope,
            "basis": AssessmentReviewService._ids(command.information_basis_version_ids),
            "responsibility": str(command.responsibility_version_id),
            "assignment": str(command.assignment_version_id),
            "expected": AssessmentReviewService._optional(command.expected_assessment_version_id),
            "rationale": command.rationale,
            "limitations": list(command.limitations),
            "context": command.context.digest,
            "effective_at": command.effective_at.isoformat(),
            "knowledge_cutoff": command.knowledge_cutoff.isoformat(),
            "principal": command.identity.principal_id,
            "actor": str(command.identity.actor_id),
        }

    @staticmethod
    def _adequacy_payload(command: DetermineAdequacyCommand) -> dict[str, object]:
        return {
            "kind": "adequacy",
            "lane": command.lane.value,
            "case": str(command.case_id),
            "configuration": str(command.configuration_version_id),
            "assessment": str(command.assessment_version_id),
            "readiness": str(command.readiness_version_id),
            "record": str(command.facts.record_id),
            "version": str(command.facts.version_id),
            "outcome": command.outcome.value,
            "reasons": list(command.material_reasons),
            "rationale": command.rationale,
            "limitations": list(command.limitations),
            "uncertainty": command.uncertainty,
            "basis": AssessmentReviewService._ids(command.information_basis_version_ids),
            "responsibility": str(command.responsibility_version_id),
            "assignment": str(command.assignment_version_id),
            "expected": AssessmentReviewService._optional(command.expected_adequacy_version_id),
            "context": command.context.digest,
            "use": command.decision_use,
            "scope": command.assessed_scope,
            "effective_at": command.effective_at.isoformat(),
            "knowledge_cutoff": command.knowledge_cutoff.isoformat(),
            "principal": command.identity.principal_id,
            "actor": str(command.identity.actor_id),
        }

    @staticmethod
    def _reliance_payload(command: DesignateRelianceCommand) -> dict[str, object]:
        return {
            "kind": "reliance",
            "lane": command.lane.value,
            "case": str(command.case_id),
            "configuration": str(command.configuration_version_id),
            "assessment": str(command.assessment_version_id),
            "readiness": str(command.readiness_version_id),
            "adequacy": str(command.adequacy_version_id),
            "record": str(command.facts.record_id),
            "version": str(command.facts.version_id),
            "dispositions": [
                {
                    "assessment": str(value.assessment_version_id),
                    "disposition": value.disposition,
                    "rationale": value.rationale,
                }
                for value in command.candidate_dispositions
            ],
            "rationale": command.rationale,
            "basis": AssessmentReviewService._ids(command.information_basis_version_ids),
            "responsibility": str(command.responsibility_version_id),
            "assignment": str(command.assignment_version_id),
            "expected": AssessmentReviewService._optional(command.expected_reliance_version_id),
            "context": command.context.digest,
            "use": command.decision_use,
            "scope": command.assessed_scope,
            "effective_at": command.effective_at.isoformat(),
            "knowledge_cutoff": command.knowledge_cutoff.isoformat(),
            "principal": command.identity.principal_id,
            "actor": str(command.identity.actor_id),
        }
