"""Increment 4 Integration, Boundary, Decision, and authorization semantics."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import cast

from paim.application.increment2 import DomainRuleViolation
from paim.application.increment3 import Increment3ApplicationService
from paim.audit import AuditFact
from paim.domain.increment3 import InputSelectionFound
from paim.domain.increment4 import (
    AuthorizedDecisionConflict,
    AuthorizedDecisionFound,
    AuthorizedDecisionNotEstablished,
    AuthorizedDecisionSelection,
    BoundaryClauseDetail,
    BoundaryClauseEffect,
    BoundaryComparisonOutcome,
    BoundaryDeterminationVersionInput,
    BoundaryEvaluation,
    BoundaryEvaluationOutcome,
    BoundarySnapshotVersionInput,
    BoundaryVerificationMode,
    BoundedProceedVersionInput,
    DecisionAuthorizationBasisVersionInput,
    DecisionDetail,
    DecisionStatus,
    DecisionVersionInput,
    IntegrationStatus,
    IntegrationVersionInput,
    UncertaintyClassificationVersionInput,
)
from paim.domain.increment4_ports import Increment4Store, Increment4Transaction
from paim.domain.models import (
    CaseLifecycleState,
    CommandMeta,
    GoverningConfigurationFound,
    LifecycleTransitionResult,
    RoleTargetType,
)
from paim.integrity import (
    AuditId,
    EventId,
    RecordId,
    RecordVersionId,
    SelectionFound,
    SelectionQuery,
    StatusEvent,
)
from paim.integrity.commands import canonical_command_digest
from paim.integrity.records import JsonValue
from paim.integrity.time import Clock, require_utc
from paim.persistence.ports import CommandOutcome, IdempotencyFact


def _one_authority(assignment_version_id: RecordVersionId | None, mechanism: str | None) -> bool:
    return (assignment_version_id is not None) != bool(mechanism)


def _decision_scope(case_id: RecordId, configuration_version_id: RecordVersionId) -> str:
    return f"case:{case_id}:configuration-version:{configuration_version_id}"


class Increment4ApplicationService(Increment3ApplicationService):
    """Synchronous bounded Increment 4 application boundary."""

    def __init__(self, store: Increment4Store, clock: Clock) -> None:
        super().__init__(store, clock)
        self._increment4_store = store

    def commit_integration(
        self, meta: CommandMeta, value: IntegrationVersionInput
    ) -> CommandOutcome:
        if not value.rationale.strip() or not value.interaction_analysis:
            raise DomainRuleViolation("Integration interaction analysis and rationale are required")
        if not _one_authority(value.owner_assignment_version_id, value.accountable_mechanism):
            raise DomainRuleViolation("Integration requires exactly one accountable owner")
        if value.status is IntegrationStatus.COMPLETED and not value.proposed_judgment:
            raise DomainRuleViolation("completed Integration requires proposed judgment")
        content: dict[str, JsonValue] = {
            "case_id": str(value.case_id),
            "configuration_id": str(value.configuration_id),
            "configuration_version_id": str(value.configuration_version_id),
            "use_context": value.use_context,
            "purpose": value.purpose,
            "value_input_version_id": str(value.value_input_version_id),
            "value_acceptance_version_id": str(value.value_acceptance_version_id),
            "value_fitness_version_id": str(value.value_fitness_version_id),
            "risk_input_version_id": str(value.risk_input_version_id),
            "risk_acceptance_version_id": str(value.risk_acceptance_version_id),
            "risk_fitness_version_id": str(value.risk_fitness_version_id),
            "material_applicability_version_ids": [
                str(item) for item in value.material_applicability_version_ids
            ],
            "constraint_references": list(value.constraint_references),
            "authority_record_version_ids": [
                str(item) for item in value.authority_record_version_ids
            ],
            "authority_gap_version_ids": [str(item) for item in value.authority_gap_version_ids],
            "integrator_actor_id": str(value.integrator_actor_id),
            "owner_assignment_version_id": (
                str(value.owner_assignment_version_id)
                if value.owner_assignment_version_id
                else None
            ),
            "accountable_mechanism": value.accountable_mechanism,
            "status": value.status.value,
            "interaction_analysis": value.interaction_analysis,
            "alternatives": list(value.alternatives),
            "proposed_judgment": value.proposed_judgment,
            "rationale": value.rationale,
        }

        def project(base: object) -> None:
            transaction = cast("Increment4Transaction", base)
            self._configuration_context(
                transaction,
                case_id=value.case_id,
                configuration_id=value.configuration_id,
                configuration_version_id=value.configuration_version_id,
            )
            self._governing_context(
                transaction,
                case_id=value.case_id,
                configuration_version_id=value.configuration_version_id,
                effective_at=value.effective.start,
                known_at=self._clock.now(),
            )
            readiness = self.analytical_handoff_readiness(
                case_id=value.case_id,
                use_context=value.use_context,
                purpose=value.purpose,
                effective_at=value.effective.start,
                known_at=self._clock.now(),
            )
            if not readiness.eligible:
                raise DomainRuleViolation("; ".join(readiness.diagnostics))
            if not isinstance(readiness.value_selection, InputSelectionFound) or not isinstance(
                readiness.risk_selection, InputSelectionFound
            ):
                raise DomainRuleViolation("exact Value and Risk selections are required")
            if (
                readiness.configuration_version_id != value.configuration_version_id
                or readiness.value_selection.input_version_id != value.value_input_version_id
                or readiness.value_selection.acceptance_version_id
                != value.value_acceptance_version_id
                or readiness.risk_selection.input_version_id != value.risk_input_version_id
                or readiness.risk_selection.acceptance_version_id
                != value.risk_acceptance_version_id
            ):
                raise DomainRuleViolation("Integration analytical basis does not match handoff")
            value_acceptance = transaction.acceptance_selection_detail(
                value.value_acceptance_version_id
            )
            risk_acceptance = transaction.acceptance_selection_detail(
                value.risk_acceptance_version_id
            )
            if (
                value_acceptance is None
                or risk_acceptance is None
                or value_acceptance.fitness_version_id != value.value_fitness_version_id
                or risk_acceptance.fitness_version_id != value.risk_fitness_version_id
            ):
                raise DomainRuleViolation("Integration fitness basis does not match selection")
            exact_applicability = {
                item.applicability_version_id
                for fitness_id in (
                    value.value_fitness_version_id,
                    value.risk_fitness_version_id,
                )
                for item in transaction.material_evidence_basis(fitness_id)
            }
            if exact_applicability != set(value.material_applicability_version_ids):
                raise DomainRuleViolation(
                    "Integration must bind the exact material Applicability basis"
                )
            self._validate_accountability(
                transaction,
                assignment_version_id=value.owner_assignment_version_id,
                mechanism=value.accountable_mechanism,
                configuration_id=value.configuration_id,
                effective_at=value.effective.start,
                known_at=self._clock.now(),
            )
            transaction.add_integration(
                integration_id=value.integration_id,
                version_id=value.version_id,
                case_id=value.case_id,
                configuration_id=value.configuration_id,
                configuration_version_id=value.configuration_version_id,
                use_context=value.use_context,
                purpose=value.purpose,
                value_input_version_id=value.value_input_version_id,
                value_acceptance_version_id=value.value_acceptance_version_id,
                value_fitness_version_id=value.value_fitness_version_id,
                risk_input_version_id=value.risk_input_version_id,
                risk_acceptance_version_id=value.risk_acceptance_version_id,
                risk_fitness_version_id=value.risk_fitness_version_id,
                integrator_actor_id=value.integrator_actor_id,
                owner_assignment_version_id=value.owner_assignment_version_id,
                accountable_mechanism=value.accountable_mechanism,
                status=value.status.value,
                material_applicability_version_ids=value.material_applicability_version_ids,
                authority_record_version_ids=value.authority_record_version_ids,
                authority_gap_version_ids=value.authority_gap_version_ids,
            )

        return self._commit_version(
            meta=meta,
            record_id=value.integration_id,
            version_id=value.version_id,
            family="integration",
            scope=(
                f"{_decision_scope(value.case_id, value.configuration_version_id)}:"
                f"use:{value.use_context}:purpose:{value.purpose}"
            ),
            content=content,
            effective=value.effective,
            expected_version_id=value.expected_version_id,
            relationship_reason=value.relationship_reason,
            relationship_type=value.relationship_type,
            project=project,
            reason_outcome="INCREMENT_4_EXACT_ANALYTICAL_BASIS_VALID",
        )

    def commit_uncertainty_classification(
        self, meta: CommandMeta, value: UncertaintyClassificationVersionInput
    ) -> CommandOutcome:
        if not value.source_reference.strip() or not value.rationale.strip():
            raise DomainRuleViolation("uncertainty source and accountable rationale are required")
        if not value.proposed_operating_state.strip():
            raise DomainRuleViolation("proposed operating state must be explicit")
        if not _one_authority(value.accountable_assignment_version_id, value.accountable_mechanism):
            raise DomainRuleViolation("uncertainty classification requires accountability")
        content: dict[str, JsonValue] = {
            "integration_version_id": str(value.integration_version_id),
            "proposed_decision_context": value.proposed_decision_context,
            "proposed_operating_state": value.proposed_operating_state,
            "source_reference": value.source_reference,
            "source_input_version_id": (
                str(value.source_input_version_id) if value.source_input_version_id else None
            ),
            "source_evidence_version_id": (
                str(value.source_evidence_version_id) if value.source_evidence_version_id else None
            ),
            "classification": value.classification.value,
            "rationale": value.rationale,
            "observation_or_requirement": value.observation_or_requirement,
            "accountable_assignment_version_id": (
                str(value.accountable_assignment_version_id)
                if value.accountable_assignment_version_id
                else None
            ),
            "accountable_mechanism": value.accountable_mechanism,
        }

        def project(base: object) -> None:
            transaction = cast("Increment4Transaction", base)
            integration = transaction.integration_detail(value.integration_version_id)
            if integration is None:
                raise DomainRuleViolation("exact Integration Version is not established")
            self._validate_accountability(
                transaction,
                assignment_version_id=value.accountable_assignment_version_id,
                mechanism=value.accountable_mechanism,
                configuration_id=integration.configuration_id,
                effective_at=value.effective.start,
                known_at=self._clock.now(),
            )
            transaction.add_uncertainty_classification(
                classification_id=value.classification_id,
                version_id=value.version_id,
                integration_version_id=value.integration_version_id,
                proposed_decision_context=value.proposed_decision_context,
                proposed_operating_state=value.proposed_operating_state,
                source_reference=value.source_reference,
                source_input_version_id=value.source_input_version_id,
                source_evidence_version_id=value.source_evidence_version_id,
                classification=value.classification.value,
                accountable_assignment_version_id=value.accountable_assignment_version_id,
                accountable_mechanism=value.accountable_mechanism,
            )

        return self._commit_version(
            meta=meta,
            record_id=value.classification_id,
            version_id=value.version_id,
            family="uncertainty-classification",
            scope=(
                f"integration-version:{value.integration_version_id}:decision-context:"
                f"{value.proposed_decision_context}:source:{value.source_reference}"
            ),
            content=content,
            effective=value.effective,
            expected_version_id=value.expected_version_id,
            relationship_reason=value.relationship_reason,
            relationship_type=value.relationship_type,
            project=project,
            reason_outcome="ACCOUNTABLE_DECISION_RELATIVE_UNCERTAINTY_RECORDED",
        )

    def commit_boundary_snapshot(
        self, meta: CommandMeta, value: BoundarySnapshotVersionInput
    ) -> CommandOutcome:
        if value.status not in {"draft", "finalized"}:
            raise DomainRuleViolation("Boundary Snapshot status must be draft or finalized")
        if not value.clauses or not value.narrative_rationale.strip():
            raise DomainRuleViolation("Boundary Snapshot requires clauses and rationale")
        clause_ids = {item.clause_id for item in value.clauses}
        clause_versions = {item.clause_version_id for item in value.clauses}
        if len(clause_ids) != len(value.clauses) or len(clause_versions) != len(value.clauses):
            raise DomainRuleViolation("Boundary clause identities and Versions must be unique")
        for clause in value.clauses:
            if not clause.narrative.strip() or not clause.provenance:
                raise DomainRuleViolation("each Boundary clause requires meaning and provenance")
            mechanical = clause.verification_mode is BoundaryVerificationMode.MECHANICAL
            if mechanical and (clause.operator is None or clause.value is None):
                raise DomainRuleViolation("mechanical Boundary clauses require operator and value")
        content: dict[str, JsonValue] = {
            "case_id": str(value.case_id),
            "configuration_id": str(value.configuration_id),
            "configuration_version_id": str(value.configuration_version_id),
            "integration_id": str(value.integration_id),
            "integration_version_id": str(value.integration_version_id),
            "owner_actor_id": str(value.owner_actor_id),
            "status": value.status,
            "clause_version_ids": [str(item.clause_version_id) for item in value.clauses],
            "narrative_rationale": value.narrative_rationale,
            "unresolved_items": list(value.unresolved_items),
        }

        def project(base: object) -> None:
            transaction = cast("Increment4Transaction", base)
            integration = transaction.integration_detail(value.integration_version_id)
            if (
                integration is None
                or integration.integration_id != value.integration_id
                or integration.case_id != value.case_id
                or integration.configuration_id != value.configuration_id
                or integration.configuration_version_id != value.configuration_version_id
                or integration.status is not IntegrationStatus.COMPLETED
            ):
                raise DomainRuleViolation(
                    "Boundary Snapshot requires the exact completed Integration context"
                )
            transaction.add_boundary_snapshot(
                snapshot_id=value.snapshot_id,
                version_id=value.version_id,
                case_id=value.case_id,
                configuration_id=value.configuration_id,
                configuration_version_id=value.configuration_version_id,
                integration_id=value.integration_id,
                integration_version_id=value.integration_version_id,
                owner_actor_id=value.owner_actor_id,
                status=value.status,
                clauses=value.clauses,
                recorded_at=self._clock.now(),
                effective_at=value.effective.start,
            )

        return self._commit_version(
            meta=meta,
            record_id=value.snapshot_id,
            version_id=value.version_id,
            family="boundary-snapshot",
            scope=_decision_scope(value.case_id, value.configuration_version_id),
            content=content,
            effective=value.effective,
            expected_version_id=value.expected_version_id,
            relationship_reason=value.relationship_reason,
            relationship_type=value.relationship_type,
            project=project,
            reason_outcome="EXACT_IMMUTABLE_BOUNDARY_SNAPSHOT_RECORDED",
        )

    def commit_boundary_determination(
        self, meta: CommandMeta, value: BoundaryDeterminationVersionInput
    ) -> CommandOutcome:
        if not value.rationale.strip() or not _one_authority(
            value.accountable_assignment_version_id, value.accountable_mechanism
        ):
            raise DomainRuleViolation(
                "Boundary determination requires rationale and accountability"
            )
        content: dict[str, JsonValue] = {
            "snapshot_version_id": str(value.snapshot_version_id),
            "clause_id": str(value.clause_id),
            "clause_version_id": str(value.clause_version_id),
            "outcome": value.outcome.value,
            "actor_id": str(value.actor_id),
            "accountable_assignment_version_id": (
                str(value.accountable_assignment_version_id)
                if value.accountable_assignment_version_id
                else None
            ),
            "accountable_mechanism": value.accountable_mechanism,
            "evidence_version_ids": [str(item) for item in value.evidence_version_ids],
            "rationale": value.rationale,
            "review_condition": value.review_condition,
        }

        def project(base: object) -> None:
            transaction = cast("Increment4Transaction", base)
            snapshot = transaction.boundary_snapshot_detail(value.snapshot_version_id)
            if snapshot is None or not any(
                clause.clause_id == value.clause_id
                and clause.clause_version_id == value.clause_version_id
                and clause.verification_mode
                in {BoundaryVerificationMode.HUMAN, BoundaryVerificationMode.EXTERNAL}
                for clause in snapshot.clauses
            ):
                raise DomainRuleViolation(
                    "determination must bind an exact human/external Boundary clause"
                )
            self._validate_accountability(
                transaction,
                assignment_version_id=value.accountable_assignment_version_id,
                mechanism=value.accountable_mechanism,
                configuration_id=snapshot.configuration_id,
                effective_at=value.effective.start,
                known_at=self._clock.now(),
            )
            transaction.add_boundary_determination(
                determination_id=value.determination_id,
                version_id=value.version_id,
                snapshot_version_id=value.snapshot_version_id,
                clause_id=value.clause_id,
                clause_version_id=value.clause_version_id,
                outcome=value.outcome.value,
                actor_id=value.actor_id,
                accountable_assignment_version_id=value.accountable_assignment_version_id,
                accountable_mechanism=value.accountable_mechanism,
                evidence_version_ids=value.evidence_version_ids,
            )

        return self._commit_version(
            meta=meta,
            record_id=value.determination_id,
            version_id=value.version_id,
            family="boundary-determination",
            scope=(
                f"boundary-snapshot-version:{value.snapshot_version_id}:"
                f"clause-version:{value.clause_version_id}"
            ),
            content=content,
            effective=value.effective,
            expected_version_id=value.expected_version_id,
            relationship_reason=value.relationship_reason,
            relationship_type=value.relationship_type,
            project=project,
            reason_outcome="ACCOUNTABLE_BOUNDARY_DETERMINATION_RECORDED",
        )

    def commit_decision_proposal(
        self, meta: CommandMeta, value: DecisionVersionInput
    ) -> CommandOutcome:
        if value.status not in {
            DecisionStatus.PROPOSED,
            DecisionStatus.PENDING_AUTHORIZATION,
        }:
            raise DomainRuleViolation("a Decision proposal cannot self-authorize")
        if not value.proposed_action.strip() or not value.operating_state.strip():
            raise DomainRuleViolation("Decision action and operating state must be explicit")
        if not value.rationale.strip():
            raise DomainRuleViolation("Decision rationale is required")
        content: dict[str, JsonValue] = {
            "case_id": str(value.case_id),
            "configuration_id": str(value.configuration_id),
            "configuration_version_id": str(value.configuration_version_id),
            "integration_id": str(value.integration_id),
            "integration_version_id": str(value.integration_version_id),
            "boundary_snapshot_id": str(value.boundary_snapshot_id),
            "boundary_snapshot_version_id": str(value.boundary_snapshot_version_id),
            "proposed_action": value.proposed_action,
            "operating_state": value.operating_state,
            "rationale": value.rationale,
            "conditions_and_limits": list(value.conditions_and_limits),
            "accepted_uncertainty_version_ids": [
                str(item) for item in value.accepted_uncertainty_version_ids
            ],
            "decision_limiting_uncertainty_version_ids": [
                str(item) for item in value.decision_limiting_uncertainty_version_ids
            ],
            "alternatives_considered": list(value.alternatives_considered),
            "constraint_references": list(value.constraint_references),
            "authority_record_version_ids": [
                str(item) for item in value.authority_record_version_ids
            ],
            "authority_gap_version_ids": [str(item) for item in value.authority_gap_version_ids],
            "intervention_declarations": list(value.intervention_declarations),
            "learning_declarations": list(value.learning_declarations),
            "reassessment_declarations": list(value.reassessment_declarations),
            "status": value.status.value,
        }

        def project(base: object) -> None:
            transaction = cast("Increment4Transaction", base)
            integration = transaction.integration_detail(value.integration_version_id)
            snapshot = transaction.boundary_snapshot_detail(value.boundary_snapshot_version_id)
            if (
                integration is None
                or integration.integration_id != value.integration_id
                or integration.status is not IntegrationStatus.COMPLETED
                or integration.case_id != value.case_id
                or integration.configuration_version_id != value.configuration_version_id
            ):
                raise DomainRuleViolation("Decision requires the exact completed Integration")
            if (
                snapshot is None
                or snapshot.snapshot_id != value.boundary_snapshot_id
                or snapshot.status != "finalized"
                or snapshot.integration_version_id != value.integration_version_id
                or snapshot.configuration_version_id != value.configuration_version_id
            ):
                raise DomainRuleViolation("Decision requires the exact finalized Boundary Snapshot")
            for classification_id, expected in (
                *(
                    (item, "ACCEPTED_UNCERTAINTY")
                    for item in value.accepted_uncertainty_version_ids
                ),
                *(
                    (item, "DECISION_LIMITING_UNCERTAINTY")
                    for item in value.decision_limiting_uncertainty_version_ids
                ),
            ):
                classification = transaction.get_version(classification_id)
                if (
                    classification is None
                    or classification.family != "uncertainty-classification"
                    or classification.content.get("classification") != expected
                    or classification.content.get("integration_version_id")
                    != str(value.integration_version_id)
                    or classification.content.get("proposed_operating_state")
                    != value.operating_state
                ):
                    raise DomainRuleViolation(
                        "Decision uncertainty basis must match Integration, class, and state"
                    )
            transaction.add_decision(
                decision_id=value.decision_id,
                version_id=value.version_id,
                case_id=value.case_id,
                configuration_id=value.configuration_id,
                configuration_version_id=value.configuration_version_id,
                integration_id=value.integration_id,
                integration_version_id=value.integration_version_id,
                boundary_snapshot_id=value.boundary_snapshot_id,
                boundary_snapshot_version_id=value.boundary_snapshot_version_id,
                proposed_action=value.proposed_action,
                operating_state=value.operating_state,
                status=value.status.value,
                accepted_uncertainty_version_ids=value.accepted_uncertainty_version_ids,
                decision_limiting_uncertainty_version_ids=(
                    value.decision_limiting_uncertainty_version_ids
                ),
                authority_record_version_ids=value.authority_record_version_ids,
                authority_gap_version_ids=value.authority_gap_version_ids,
            )

        return self._commit_version(
            meta=meta,
            record_id=value.decision_id,
            version_id=value.version_id,
            family="management-decision",
            scope=_decision_scope(value.case_id, value.configuration_version_id),
            content=content,
            effective=value.effective,
            expected_version_id=value.expected_version_id,
            relationship_reason=value.relationship_reason,
            relationship_type=value.relationship_type,
            project=project,
            reason_outcome="PROPOSED_DECISION_EXACT_BASIS_RECORDED_NOT_AUTHORIZED",
        )

    def _assignment_current(
        self,
        transaction: Increment4Transaction,
        version_id: RecordVersionId,
        *,
        effective_at: datetime,
        known_at: datetime,
    ) -> bool:
        detail = transaction.role_assignment_detail(version_id)
        if detail is None:
            return False
        history = transaction.get_history(detail.assignment_id)
        if not history.versions:
            return False
        exemplar = next(iter(history.versions))
        current = transaction.select_current(
            SelectionQuery(
                family="role-assignment",
                scope=exemplar.scope,
                effective_at=effective_at,
                known_at=known_at,
                record_id=detail.assignment_id,
            )
        )
        return isinstance(current, SelectionFound) and current.candidate.version_id == version_id

    def _validate_exact_decision_authority(
        self,
        transaction: Increment4Transaction,
        *,
        decision: DecisionDetail,
        actor_id: RecordId,
        authority_assignment_version_id: RecordVersionId | None,
        authority_mechanism: str | None,
        authority_record_version_id: RecordVersionId | None,
        delegation_chain_version_ids: tuple[RecordVersionId, ...],
        authorized_scope: str,
        configuration_id: RecordId,
        configuration_version_id: RecordVersionId,
        operating_state_coverage: tuple[str, ...],
        effective_at: datetime,
        known_at: datetime,
    ) -> None:
        if not _one_authority(authority_assignment_version_id, authority_mechanism):
            raise DomainRuleViolation(
                "missing authority: exactly one authority assignment or mechanism is required"
            )
        if configuration_id != decision.configuration_id or (
            configuration_version_id != decision.configuration_version_id
        ):
            raise DomainRuleViolation("Decision authority Configuration coverage mismatch")
        if decision.operating_state not in operating_state_coverage:
            raise DomainRuleViolation("Decision authority operating-state coverage mismatch")
        if authority_record_version_id is not None:
            authority = transaction.get_version(authority_record_version_id)
            if authority is None or authority.family != "authority-record":
                raise DomainRuleViolation("required Authority Record is not established")
            current = transaction.select_current(
                SelectionQuery(
                    family=authority.family,
                    scope=authority.scope,
                    effective_at=effective_at,
                    known_at=known_at,
                    record_id=authority.record_id,
                )
            )
            if not isinstance(current, SelectionFound) or (
                current.candidate.version_id != authority_record_version_id
            ):
                raise DomainRuleViolation("Authority Record is expired, withdrawn, or superseded")
            if transaction.authority_record_scope(authority_record_version_id) != authorized_scope:
                raise DomainRuleViolation("Authority Record scope does not cover exact Decision")
        elif not authority_mechanism:
            raise DomainRuleViolation("missing required Authority Record or mechanism")

        if authority_mechanism:
            if delegation_chain_version_ids:
                raise DomainRuleViolation(
                    "organizational mechanism cannot fabricate a Role Assignment delegation chain"
                )
            return

        assert authority_assignment_version_id is not None
        assignment = transaction.role_assignment_detail(authority_assignment_version_id)
        if (
            assignment is None
            or not assignment.accountable
            or assignment.role.casefold().replace(" ", "_") != "decision_authority"
            or assignment.actor_id != actor_id
            or not self._assignment_current(
                transaction,
                authority_assignment_version_id,
                effective_at=effective_at,
                known_at=known_at,
            )
        ):
            raise DomainRuleViolation(
                "authority vacancy or invalid Decision Authority assignment blocks authorization"
            )
        applicable_targets = (
            (RoleTargetType.DECISION.value, str(decision.decision_id)),
            (RoleTargetType.CONFIGURATION.value, str(decision.configuration_id)),
            (RoleTargetType.CASE.value, str(decision.case_id)),
        )
        if (assignment.target_type.value, assignment.target_id) not in applicable_targets:
            raise DomainRuleViolation("unrelated-scope Decision Authority is ineligible")

        chain = delegation_chain_version_ids
        if assignment.delegated_from_version_id is not None and not chain:
            raise DomainRuleViolation(
                "delegated Decision Authority requires exact delegation chain"
            )
        if chain:
            if chain[-1] != authority_assignment_version_id:
                raise DomainRuleViolation("delegation chain must terminate at Decision Authority")
            previous: RecordVersionId | None = None
            for link_id in chain:
                link = transaction.role_assignment_detail(link_id)
                if (
                    link is None
                    or not link.accountable
                    or link.role.casefold().replace(" ", "_") != "decision_authority"
                    or (link.target_type.value, link.target_id) not in applicable_targets
                    or not self._assignment_current(
                        transaction,
                        link_id,
                        effective_at=effective_at,
                        known_at=known_at,
                    )
                    or (previous is None and link.delegated_from_version_id is not None)
                    or (previous is not None and link.delegated_from_version_id != previous)
                ):
                    raise DomainRuleViolation(
                        "invalid, expired, revoked, or out-of-scope delegation"
                    )
                previous = link_id

        record_ids = transaction.role_assignment_records(
            role=assignment.role, targets=applicable_targets
        )
        applicable: set[RecordVersionId] = set()
        for record_id in record_ids:
            history = transaction.get_history(record_id)
            for candidate in history.versions:
                if self._assignment_current(
                    transaction,
                    candidate.version_id,
                    effective_at=effective_at,
                    known_at=known_at,
                ):
                    detail = transaction.role_assignment_detail(candidate.version_id)
                    if detail is not None and detail.accountable:
                        applicable.add(candidate.version_id)
        established_chain = set(chain) if chain else {authority_assignment_version_id}
        if applicable != established_chain:
            raise DomainRuleViolation(
                "incompatible applicable Decision Authority assignments — explicit conflict"
            )

    def _validate_decision_authority(
        self,
        transaction: Increment4Transaction,
        *,
        value: DecisionAuthorizationBasisVersionInput,
        decision: DecisionDetail,
        effective_at: datetime,
        known_at: datetime,
    ) -> None:
        if (
            value.authority_assignment_version_id is not None
            and str(value.authorization_actor_id) != value.decision_authority_identity
        ):
            raise DomainRuleViolation(
                "Decision Authority identity must match the attributable authorization actor"
            )
        self._validate_exact_decision_authority(
            transaction,
            decision=decision,
            actor_id=value.authorization_actor_id,
            authority_assignment_version_id=value.authority_assignment_version_id,
            authority_mechanism=value.authority_mechanism,
            authority_record_version_id=value.authority_record_version_id,
            delegation_chain_version_ids=value.delegation_chain_version_ids,
            authorized_scope=value.authorized_scope,
            configuration_id=value.configuration_id,
            configuration_version_id=value.configuration_version_id,
            operating_state_coverage=value.operating_state_coverage,
            effective_at=effective_at,
            known_at=known_at,
        )

    def commit_bounded_proceed(
        self, meta: CommandMeta, value: BoundedProceedVersionInput
    ) -> CommandOutcome:
        if not _one_authority(value.authority_assignment_version_id, value.authority_mechanism):
            raise DomainRuleViolation("bounded proceed requires exact Decision Authority")
        if (
            not value.narrower_scope.strip()
            or not value.rationale.strip()
            or not value.review_trigger.strip()
        ):
            raise DomainRuleViolation(
                "bounded proceed scope, rationale, and review trigger are required"
            )
        content: dict[str, JsonValue] = {
            "decision_version_id": str(value.decision_version_id),
            "unresolved_gap_version_id": str(value.unresolved_gap_version_id),
            "blocked_broader_decision": value.blocked_broader_decision,
            "narrower_scope": value.narrower_scope,
            "boundary_clause_version_ids": [
                str(item) for item in value.boundary_clause_version_ids
            ],
            "operating_state": value.operating_state,
            "rationale": value.rationale,
            "conditions": list(value.conditions),
            "review_trigger": value.review_trigger,
            "actor_id": str(value.actor_id),
            "authority_assignment_version_id": (
                str(value.authority_assignment_version_id)
                if value.authority_assignment_version_id
                else None
            ),
            "authority_mechanism": value.authority_mechanism,
            "authority_record_version_id": (
                str(value.authority_record_version_id)
                if value.authority_record_version_id
                else None
            ),
            "delegation_chain_version_ids": [
                str(item) for item in value.delegation_chain_version_ids
            ],
        }

        def project(base: object) -> None:
            transaction = cast("Increment4Transaction", base)
            decision = transaction.decision_detail(value.decision_version_id)
            gap = transaction.get_version(value.unresolved_gap_version_id)
            if decision is None or gap is None or gap.family != "authority-gap":
                raise DomainRuleViolation(
                    "exact proposed Decision and unresolved Authority Gap required"
                )
            if decision.operating_state != value.operating_state:
                raise DomainRuleViolation(
                    "bounded proceed operating state must match exact Decision"
                )
            snapshot = transaction.boundary_snapshot_detail(decision.boundary_snapshot_version_id)
            if snapshot is None or set(value.boundary_clause_version_ids) - {
                clause.clause_version_id for clause in snapshot.clauses
            }:
                raise DomainRuleViolation(
                    "bounded proceed must bind exact Decision Boundary clauses"
                )
            self._validate_exact_decision_authority(
                transaction,
                decision=decision,
                actor_id=value.actor_id,
                authority_assignment_version_id=value.authority_assignment_version_id,
                authority_mechanism=value.authority_mechanism,
                authority_record_version_id=value.authority_record_version_id,
                delegation_chain_version_ids=value.delegation_chain_version_ids,
                authorized_scope=value.narrower_scope,
                configuration_id=decision.configuration_id,
                configuration_version_id=decision.configuration_version_id,
                operating_state_coverage=(value.operating_state,),
                effective_at=value.effective.start,
                known_at=self._clock.now(),
            )
            transaction.add_bounded_proceed(
                determination_id=value.determination_id,
                version_id=value.version_id,
                decision_version_id=value.decision_version_id,
                unresolved_gap_version_id=value.unresolved_gap_version_id,
                blocked_broader_decision=value.blocked_broader_decision,
                narrower_scope=value.narrower_scope,
                boundary_clause_version_ids=value.boundary_clause_version_ids,
                operating_state=value.operating_state,
                actor_id=value.actor_id,
                authority_assignment_version_id=value.authority_assignment_version_id,
                authority_mechanism=value.authority_mechanism,
                authority_record_version_id=value.authority_record_version_id,
                delegation_chain_version_ids=value.delegation_chain_version_ids,
            )

        return self._commit_version(
            meta=meta,
            record_id=value.determination_id,
            version_id=value.version_id,
            family="bounded-proceed-determination",
            scope=(
                f"decision-version:{value.decision_version_id}:"
                f"authority-gap-version:{value.unresolved_gap_version_id}"
            ),
            content=content,
            effective=value.effective,
            expected_version_id=value.expected_version_id,
            relationship_reason=value.relationship_reason,
            relationship_type=value.relationship_type,
            project=project,
            reason_outcome="BOUNDED_PROCEED_PRESERVES_UNRESOLVED_AUTHORITY_GAP",
        )

    def _case_state_in_transaction(
        self,
        transaction: Increment4Transaction,
        *,
        case_id: RecordId,
        effective_at: datetime,
        known_at: datetime,
    ) -> tuple[CaseLifecycleState, RecordVersionId]:
        selected = transaction.select_current(
            SelectionQuery(
                family="case",
                scope=f"case:{case_id}",
                effective_at=effective_at,
                known_at=known_at,
                record_id=case_id,
            )
        )
        if not isinstance(selected, SelectionFound):
            raise DomainRuleViolation("Case is absent or conflicting")
        events = [
            event
            for event in transaction.get_history(case_id).status_events
            if event.effective_at <= effective_at
            and event.recorded_at <= known_at
            and event.new_status in {state.value for state in CaseLifecycleState}
        ]
        events.sort(key=lambda item: (item.effective_at, item.recorded_at, str(item.event_id)))
        state = CaseLifecycleState(events[-1].new_status) if events else CaseLifecycleState.OPEN
        return state, selected.candidate.version_id

    def authorize_decision(
        self, meta: CommandMeta, value: DecisionAuthorizationBasisVersionInput
    ) -> CommandOutcome:
        value_effective = require_utc(value.authorization_effective_at)
        if value_effective != value.effective.start:
            raise DomainRuleViolation(
                "authorization event and Authorization Basis effective time must match"
            )
        if (
            not value.decision_authority_identity.strip()
            or not value.authorized_scope.strip()
            or not value.authorization_event_id.strip()
            or not value.operating_state_coverage
        ):
            raise DomainRuleViolation("complete Decision Authorization Basis is required")
        content: dict[str, JsonValue] = {
            "decision_id": str(value.decision_id),
            "decision_version_id": str(value.decision_version_id),
            "decision_authority_identity": value.decision_authority_identity,
            "authority_assignment_version_id": (
                str(value.authority_assignment_version_id)
                if value.authority_assignment_version_id
                else None
            ),
            "authority_mechanism": value.authority_mechanism,
            "authority_record_version_id": (
                str(value.authority_record_version_id)
                if value.authority_record_version_id
                else None
            ),
            "delegation_chain_version_ids": [
                str(item) for item in value.delegation_chain_version_ids
            ],
            "authorized_scope": value.authorized_scope,
            "limits": list(value.limits),
            "configuration_id": str(value.configuration_id),
            "configuration_version_id": str(value.configuration_version_id),
            "operating_state_coverage": list(value.operating_state_coverage),
            "decision_type": value.decision_type,
            "organizational_unit": value.organizational_unit,
            "authorization_event_id": value.authorization_event_id,
            "authorization_actor_id": str(value.authorization_actor_id),
            "authorization_effective_at": value_effective.isoformat(),
            "conditions": list(value.conditions),
            "dissent": list(value.dissent),
            "exception": value.exception,
            "authority_gap_version_ids": [str(item) for item in value.authority_gap_version_ids],
            "bounded_proceed_version_id": (
                str(value.bounded_proceed_version_id) if value.bounded_proceed_version_id else None
            ),
        }

        def project(base: object) -> None:
            transaction = cast("Increment4Transaction", base)
            now = self._clock.now()
            decision = transaction.decision_detail(value.decision_version_id)
            if decision is None or decision.decision_id != value.decision_id:
                raise DomainRuleViolation("exact proposed Decision Version is not established")
            decision_record = transaction.get_version(value.decision_version_id)
            if decision_record is None:
                raise DomainRuleViolation("exact Decision history is not established")
            current_decision = transaction.select_current(
                SelectionQuery(
                    family="management-decision",
                    scope=decision_record.scope,
                    effective_at=value_effective,
                    known_at=now,
                    record_id=value.decision_id,
                )
            )
            if not isinstance(current_decision, SelectionFound) or (
                current_decision.candidate.version_id != value.decision_version_id
            ):
                raise DomainRuleViolation("Decision Version is stale, withdrawn, or conflicting")
            if transaction.authorization_basis_versions(
                decision_version_id=value.decision_version_id
            ):
                raise DomainRuleViolation("Decision already has an Authorization Basis")
            integration = transaction.integration_detail(decision.integration_version_id)
            snapshot = transaction.boundary_snapshot_detail(decision.boundary_snapshot_version_id)
            if integration is None or integration.status is not IntegrationStatus.COMPLETED:
                raise DomainRuleViolation("completed exact Integration is required")
            if snapshot is None or snapshot.status != "finalized":
                raise DomainRuleViolation("finalized exact Boundary Snapshot is required")
            if (
                integration.configuration_version_id != decision.configuration_version_id
                or snapshot.configuration_version_id != decision.configuration_version_id
                or snapshot.integration_version_id != decision.integration_version_id
            ):
                raise DomainRuleViolation(
                    "Decision, Integration, and Boundary exact basis mismatch"
                )
            for clause in snapshot.clauses:
                if clause.verification_mode in {
                    BoundaryVerificationMode.HUMAN,
                    BoundaryVerificationMode.EXTERNAL,
                }:
                    determination = transaction.current_boundary_determination(
                        snapshot_version_id=snapshot.version_id,
                        clause_version_id=clause.clause_version_id,
                        effective_at=value_effective,
                        known_at=now,
                    )
                    if determination is None or determination[1] != BoundaryEvaluationOutcome.PASS:
                        raise DomainRuleViolation(
                            "required human/external Boundary determination absent or unsatisfied"
                        )
                elif clause.verification_mode is BoundaryVerificationMode.INDETERMINATE:
                    raise DomainRuleViolation("indeterminate Boundary clause blocks authorization")
            self._validate_decision_authority(
                transaction,
                value=value,
                decision=decision,
                effective_at=value_effective,
                known_at=now,
            )
            decision_gaps = {
                RecordVersionId.parse(item)
                for item in cast(
                    "list[str]", decision_record.content.get("authority_gap_version_ids", [])
                )
            }
            if not set(value.authority_gap_version_ids).issubset(decision_gaps):
                raise DomainRuleViolation("Authorization Basis cites unrelated Authority Gap")
            if value.authority_gap_version_ids:
                if value.bounded_proceed_version_id is None:
                    raise DomainRuleViolation(
                        "unresolved Authority Gap requires explicit bounded-proceed determination"
                    )
                bounded = transaction.get_version(value.bounded_proceed_version_id)
                bounded_detail = transaction.bounded_proceed_detail(
                    value.bounded_proceed_version_id
                )
                if (
                    bounded is None
                    or bounded.family != "bounded-proceed-determination"
                    or bounded_detail is None
                    or bounded_detail["decision_version_id"] != str(value.decision_version_id)
                    or RecordVersionId.parse(bounded_detail["unresolved_gap_version_id"])
                    not in value.authority_gap_version_ids
                    or bounded_detail["narrower_scope"] != value.authorized_scope
                    or bounded_detail["operating_state"] != decision.operating_state
                ):
                    raise DomainRuleViolation(
                        "bounded proceed does not cover exact narrower Decision"
                    )
                current_bounded = transaction.select_current(
                    SelectionQuery(
                        family=bounded.family,
                        scope=bounded.scope,
                        effective_at=value_effective,
                        known_at=now,
                        record_id=bounded.record_id,
                    )
                )
                if not isinstance(current_bounded, SelectionFound) or (
                    current_bounded.candidate.version_id != value.bounded_proceed_version_id
                ):
                    raise DomainRuleViolation("bounded-proceed determination is not current")
                bounded_assignment = bounded.content.get("authority_assignment_version_id")
                bounded_mechanism = bounded.content.get("authority_mechanism")
                bounded_authority_record = bounded.content.get("authority_record_version_id")
                bounded_delegation_chain = bounded.content.get("delegation_chain_version_ids")
                if (
                    bounded_assignment
                    != (
                        str(value.authority_assignment_version_id)
                        if value.authority_assignment_version_id
                        else None
                    )
                    or bounded_mechanism != value.authority_mechanism
                    or bounded_authority_record
                    != (
                        str(value.authority_record_version_id)
                        if value.authority_record_version_id
                        else None
                    )
                    or bounded_delegation_chain
                    != [str(item) for item in value.delegation_chain_version_ids]
                ):
                    raise DomainRuleViolation(
                        "bounded proceed was not made by the exact Decision Authority"
                    )
            elif value.bounded_proceed_version_id is not None:
                raise DomainRuleViolation("bounded proceed cannot be detached from a cited Gap")
            state, _ = self._case_state_in_transaction(
                transaction,
                case_id=decision.case_id,
                effective_at=value_effective,
                known_at=now,
            )
            if state is CaseLifecycleState.DECIDED:
                history = transaction.get_history(decision.decision_id)
                if not any(
                    relationship.target_version_id == value.decision_version_id
                    for relationship in history.relationships
                ):
                    raise DomainRuleViolation(
                        "DECIDED Case requires an explicit successor/amendment Decision"
                    )
            elif state is not CaseLifecycleState.DECISION_PENDING:
                raise DomainRuleViolation(
                    "Case must be DECISION_PENDING before initial authorization"
                )
            transaction.add_authorization_basis(
                basis_id=value.basis_id,
                version_id=value.version_id,
                decision_version_id=value.decision_version_id,
                decision_authority_identity=value.decision_authority_identity,
                authority_assignment_version_id=value.authority_assignment_version_id,
                authority_mechanism=value.authority_mechanism,
                authority_record_version_id=value.authority_record_version_id,
                delegation_chain_version_ids=value.delegation_chain_version_ids,
                authorized_scope=value.authorized_scope,
                configuration_id=value.configuration_id,
                configuration_version_id=value.configuration_version_id,
                operating_state_coverage=value.operating_state_coverage,
                decision_type=value.decision_type,
                organizational_unit=value.organizational_unit,
                authorization_event_id=value.authorization_event_id,
                authorization_actor_id=value.authorization_actor_id,
                authorization_effective_at=value_effective,
                authority_gap_version_ids=value.authority_gap_version_ids,
                bounded_proceed_version_id=value.bounded_proceed_version_id,
                preauthorized_activation_mechanisms=(value.preauthorized_activation_mechanisms),
            )

        def after_version(
            base: object, recorded_at: datetime
        ) -> tuple[tuple[EventId, ...], tuple[RecordVersionId, ...]]:
            transaction = cast("Increment4Transaction", base)
            decision = transaction.decision_detail(value.decision_version_id)
            assert decision is not None
            state, case_version_id = self._case_state_in_transaction(
                transaction,
                case_id=decision.case_id,
                effective_at=value_effective,
                known_at=recorded_at,
            )
            if state not in {
                CaseLifecycleState.DECISION_PENDING,
                CaseLifecycleState.DECIDED,
            }:
                raise DomainRuleViolation("stale lifecycle precondition blocks authorization")
            decision_event = StatusEvent(
                EventId.new(),
                value.decision_version_id,
                decision.status.value,
                DecisionStatus.AUTHORIZED.value,
                recorded_at,
                value_effective,
                str(value.authorization_actor_id),
                f"Decision Authorization Basis {value.version_id}",
            )
            transaction.add_status_event(decision_event)
            if state is CaseLifecycleState.DECIDED:
                return ((decision_event.event_id,), (value.decision_version_id,))
            lifecycle_event = StatusEvent(
                EventId.new(),
                case_version_id,
                state.value,
                CaseLifecycleState.DECIDED.value,
                recorded_at,
                value_effective,
                str(value.authorization_actor_id),
                f"Authorized Decision {value.decision_version_id} and Basis {value.version_id}",
            )
            transaction.add_status_event(lifecycle_event)
            return (
                (decision_event.event_id, lifecycle_event.event_id),
                (value.decision_version_id, case_version_id),
            )

        return self._commit_version(
            meta=meta,
            record_id=value.basis_id,
            version_id=value.version_id,
            family="decision-authorization-basis",
            scope=f"decision-version:{value.decision_version_id}",
            content=content,
            effective=value.effective,
            expected_version_id=value.expected_version_id,
            relationship_reason=value.relationship_reason,
            relationship_type=value.relationship_type,
            project=project,
            after_version=after_version,
            reason_outcome="DECISION_BOUNDARY_AUTHORIZATION_LIFECYCLE_ATOMIC_COMMIT",
        )

    def transition_case(
        self,
        meta: CommandMeta,
        *,
        case_id: RecordId,
        target_state: CaseLifecycleState,
        effective_at: datetime,
        use_context: str | None = None,
        purpose: str | None = None,
    ) -> LifecycleTransitionResult:
        effective_at = require_utc(effective_at)
        if target_state is CaseLifecycleState.CONFIGURATION_DEFINED:
            return super().transition_case(
                meta,
                case_id=case_id,
                target_state=target_state,
                effective_at=effective_at,
            )
        if target_state is CaseLifecycleState.DECIDED:
            return LifecycleTransitionResult(
                False,
                self.current_lifecycle_state(case_id=case_id, effective_at=effective_at),
                "DECIDED requires the atomic Decision Authorization semantic commit",
            )
        recorded_at = self._clock.now()
        readiness = None
        if target_state is CaseLifecycleState.READY_FOR_INTEGRATION:
            if not use_context or not purpose:
                return LifecycleTransitionResult(
                    False,
                    self.current_lifecycle_state(case_id=case_id, effective_at=effective_at),
                    "bounded Integration use and purpose are required",
                )
            readiness = self.analytical_handoff_readiness(
                case_id=case_id,
                use_context=use_context,
                purpose=purpose,
                effective_at=effective_at,
                known_at=recorded_at,
            )
            if not readiness.eligible:
                return LifecycleTransitionResult(
                    False,
                    self.current_lifecycle_state(case_id=case_id, effective_at=effective_at),
                    "; ".join(readiness.diagnostics),
                )
        payload: dict[str, JsonValue] = {
            "case_id": str(case_id),
            "target_state": target_state.value,
            "effective_at": effective_at.isoformat(),
            "use_context": use_context,
            "purpose": purpose,
            "principal_id": meta.principal_id,
            "actor_id": meta.actor_id,
        }
        digest = canonical_command_digest(payload)
        with self._increment4_store.semantic_transaction() as transaction:
            replay = transaction.get_idempotency(meta.idempotency_scope, meta.idempotency_key)
            if replay is not None:
                if replay.digest != digest:
                    raise DomainRuleViolation("IDEMPOTENCY KEY REUSE CONFLICT")
                state = self._case_state_in_transaction(
                    transaction,
                    case_id=case_id,
                    effective_at=effective_at,
                    known_at=recorded_at,
                )[0]
                return LifecycleTransitionResult(
                    True, state, "TRANSITION COMMITTED", replay.outcome.status_event_ids[0]
                )
            current, case_version_id = self._case_state_in_transaction(
                transaction,
                case_id=case_id,
                effective_at=effective_at,
                known_at=recorded_at,
            )
            allowed = {
                CaseLifecycleState.CONFIGURATION_DEFINED: CaseLifecycleState.EVIDENCE_ANALYSIS,
                CaseLifecycleState.EVIDENCE_ANALYSIS: CaseLifecycleState.READY_FOR_INTEGRATION,
                CaseLifecycleState.READY_FOR_INTEGRATION: CaseLifecycleState.DECISION_PENDING,
            }
            if allowed.get(current) is not target_state:
                return LifecycleTransitionResult(
                    False, current, "transition is outside the bounded Increment 4 lifecycle path"
                )
            basis = ""
            if target_state is CaseLifecycleState.EVIDENCE_ANALYSIS:
                governing = self._select_governing(
                    transaction,
                    case_id=case_id,
                    effective_at=effective_at,
                    known_at=recorded_at,
                )
                if not isinstance(governing, GoverningConfigurationFound):
                    return LifecycleTransitionResult(
                        False, current, "GOVERNING CONFIGURATION NOT ESTABLISHED"
                    )
                basis = f"governing Configuration {governing.configuration_version_id}"
            elif target_state is CaseLifecycleState.READY_FOR_INTEGRATION:
                assert readiness is not None and readiness.configuration_version_id is not None
                basis = (
                    f"eligible exact Value/Risk handoff for {readiness.configuration_version_id}"
                )
            else:
                governing = self._select_governing(
                    transaction,
                    case_id=case_id,
                    effective_at=effective_at,
                    known_at=recorded_at,
                )
                if not isinstance(governing, GoverningConfigurationFound):
                    return LifecycleTransitionResult(
                        False, current, "GOVERNING CONFIGURATION NOT ESTABLISHED"
                    )
                integration_ids = transaction.integration_versions_for_context(
                    case_id=case_id,
                    configuration_version_id=governing.configuration_version_id,
                )
                eligible: list[RecordVersionId] = []
                for version_id in integration_ids:
                    detail = transaction.integration_detail(version_id)
                    version = transaction.get_version(version_id)
                    if (
                        detail is None
                        or version is None
                        or detail.status
                        not in {
                            IntegrationStatus.IN_PROGRESS,
                            IntegrationStatus.COMPLETED,
                            IntegrationStatus.DECISION_PENDING,
                        }
                    ):
                        continue
                    current_integration = transaction.select_current(
                        SelectionQuery(
                            family=version.family,
                            scope=version.scope,
                            effective_at=effective_at,
                            known_at=recorded_at,
                            record_id=version.record_id,
                        )
                    )
                    if isinstance(current_integration, SelectionFound) and (
                        current_integration.candidate.version_id == version_id
                    ):
                        eligible.append(version_id)
                if len(eligible) != 1:
                    reason = (
                        "INTEGRATION NOT ESTABLISHED"
                        if not eligible
                        else "INTEGRATION CONFLICT — UNRESOLVED"
                    )
                    return LifecycleTransitionResult(False, current, reason)
                basis = f"Integration begun {eligible[0]}"
            event = StatusEvent(
                EventId.new(),
                case_version_id,
                current.value,
                target_state.value,
                recorded_at,
                effective_at,
                meta.actor_id or meta.actor_resolution.value,
                basis,
            )
            transaction.add_status_event(event)
            audit = AuditFact(
                audit_id=AuditId.new(),
                principal_id=meta.principal_id,
                actor_id=meta.actor_id,
                actor_resolution=meta.actor_resolution,
                operation="TRANSITION_CASE_LIFECYCLE",
                result="COMMITTED",
                command_id=meta.command_id,
                idempotency_scope=meta.idempotency_scope,
                idempotency_key=meta.idempotency_key,
                correlation_id=meta.correlation_id,
                causation_id=meta.causation_id,
                target_record_id=case_id,
                affected_version_ids=(case_version_id,),
                expected_precondition=current.value,
                observed_precondition=current.value,
                effective_at=effective_at,
                recorded_at=recorded_at,
                reason_outcomes=(basis,),
                request_digest=digest,
            )
            transaction.add_audit(audit)
            outcome = CommandOutcome(
                command_id=str(meta.command_id),
                record_id=str(case_id),
                version_ids=(),
                status_event_ids=(str(event.event_id),),
                relationship_ids=(),
                audit_id=str(audit.audit_id),
            )
            transaction.add_idempotency(
                IdempotencyFact(
                    scope=meta.idempotency_scope,
                    key=meta.idempotency_key,
                    digest=digest,
                    command_id=str(meta.command_id),
                    outcome=outcome,
                    recorded_at=recorded_at,
                )
            )
            return LifecycleTransitionResult(
                True, target_state, "TRANSITION COMMITTED", str(event.event_id)
            )

    def evaluate_boundary_clause(
        self,
        *,
        snapshot_version_id: RecordVersionId,
        clause_version_id: RecordVersionId,
        observed_value: str | None,
        observed_unit: str | None,
        effective_at: datetime,
        known_at: datetime | None = None,
    ) -> BoundaryEvaluation:
        effective_at = require_utc(effective_at)
        knowledge_time = require_utc(known_at or self._clock.now())
        with self._increment4_store.read_transaction() as transaction:
            snapshot = transaction.boundary_snapshot_detail(snapshot_version_id)
            if snapshot is None:
                raise DomainRuleViolation("Boundary Snapshot is not established")
            matches = [
                clause
                for clause in snapshot.clauses
                if clause.clause_version_id == clause_version_id
            ]
            if len(matches) != 1:
                raise DomainRuleViolation("exact Boundary Clause Version is not established")
            clause = matches[0]
            if clause.verification_mode in {
                BoundaryVerificationMode.HUMAN,
                BoundaryVerificationMode.EXTERNAL,
            }:
                determination = transaction.current_boundary_determination(
                    snapshot_version_id=snapshot_version_id,
                    clause_version_id=clause_version_id,
                    effective_at=effective_at,
                    known_at=knowledge_time,
                )
                if determination is None:
                    return BoundaryEvaluation(
                        clause_version_id,
                        BoundaryEvaluationOutcome.INDETERMINATE,
                        "REQUIRED DETERMINATION NOT ESTABLISHED",
                    )
                return BoundaryEvaluation(
                    clause_version_id,
                    BoundaryEvaluationOutcome(determination[1]),
                    f"determination {determination[0]}",
                )
            if clause.verification_mode is BoundaryVerificationMode.INDETERMINATE:
                return BoundaryEvaluation(
                    clause_version_id,
                    BoundaryEvaluationOutcome.INDETERMINATE,
                    "CLAUSE VERIFICATION MODE IS INDETERMINATE",
                )
            return self._mechanical_clause(clause, observed_value, observed_unit)

    @staticmethod
    def _mechanical_clause(
        clause: BoundaryClauseDetail,
        observed_value: str | None,
        observed_unit: str | None,
    ) -> BoundaryEvaluation:
        if observed_value is None or (clause.unit is not None and clause.unit != observed_unit):
            return BoundaryEvaluation(
                clause.clause_version_id,
                BoundaryEvaluationOutcome.INDETERMINATE,
                "OBSERVATION OR EXACT UNIT NOT ESTABLISHED",
            )
        operator = (clause.operator or "").upper()
        expected = clause.value or ""
        try:
            left, right = Decimal(observed_value), Decimal(expected)
            result = {
                "EQ": left == right,
                "NE": left != right,
                "LT": left < right,
                "LTE": left <= right,
                "GT": left > right,
                "GTE": left >= right,
            }.get(operator)
        except InvalidOperation:
            result = {
                "EQ": observed_value == expected,
                "NE": observed_value != expected,
                "IN": observed_value in {item.strip() for item in expected.split(",")},
                "NOT_IN": observed_value not in {item.strip() for item in expected.split(",")},
            }.get(operator)
        if result is None:
            return BoundaryEvaluation(
                clause.clause_version_id,
                BoundaryEvaluationOutcome.INDETERMINATE,
                "OPERATOR DOES NOT SUPPORT DETERMINISTIC COMPARISON",
            )
        return BoundaryEvaluation(
            clause.clause_version_id,
            BoundaryEvaluationOutcome.PASS if result else BoundaryEvaluationOutcome.BREACH,
            "MECHANICAL CLAUSE SATISFIED" if result else "MECHANICAL CLAUSE BREACHED",
        )

    def compare_boundaries(
        self,
        *,
        predecessor_version_id: RecordVersionId,
        successor_version_id: RecordVersionId,
    ) -> BoundaryComparisonOutcome:
        with self._increment4_store.read_transaction() as transaction:
            predecessor = transaction.boundary_snapshot_detail(predecessor_version_id)
            successor = transaction.boundary_snapshot_detail(successor_version_id)
        if predecessor is None or successor is None:
            raise DomainRuleViolation("both exact Boundary Snapshot Versions are required")
        old = {
            (item.clause_type, item.target_reference, item.structured_reference): item
            for item in predecessor.clauses
        }
        new = {
            (item.clause_type, item.target_reference, item.structured_reference): item
            for item in successor.clauses
        }
        narrowed = False
        broadened = False
        for key in old.keys() | new.keys():
            before, after = old.get(key), new.get(key)
            if before is None:
                assert after is not None
                if after.effect is BoundaryClauseEffect.PERMITTED:
                    broadened = True
                elif after.effect is BoundaryClauseEffect.INDETERMINATE:
                    return BoundaryComparisonOutcome.INDETERMINATE
                else:
                    narrowed = True
                continue
            if after is None:
                if before.effect is BoundaryClauseEffect.PERMITTED:
                    narrowed = True
                elif before.effect is BoundaryClauseEffect.INDETERMINATE:
                    return BoundaryComparisonOutcome.INDETERMINATE
                else:
                    broadened = True
                continue
            before_signature = (
                before.effect,
                before.operator,
                before.value,
                before.unit,
                before.narrative,
                before.verification_mode,
            )
            after_signature = (
                after.effect,
                after.operator,
                after.value,
                after.unit,
                after.narrative,
                after.verification_mode,
            )
            if before_signature == after_signature:
                continue
            direction = self._clause_change_direction(before, after)
            if direction is BoundaryComparisonOutcome.INDETERMINATE:
                return direction
            narrowed |= direction is BoundaryComparisonOutcome.NARROWED
            broadened |= direction is BoundaryComparisonOutcome.BROADENED
        if narrowed and broadened:
            return BoundaryComparisonOutcome.MIXED
        if narrowed:
            return BoundaryComparisonOutcome.NARROWED
        if broadened:
            return BoundaryComparisonOutcome.BROADENED
        return BoundaryComparisonOutcome.UNCHANGED

    @staticmethod
    def _clause_change_direction(
        before: BoundaryClauseDetail, after: BoundaryClauseDetail
    ) -> BoundaryComparisonOutcome:
        if (
            before.effect is BoundaryClauseEffect.INDETERMINATE
            or after.effect is BoundaryClauseEffect.INDETERMINATE
            or before.operator != after.operator
            or before.unit != after.unit
        ):
            return BoundaryComparisonOutcome.INDETERMINATE
        if before.effect != after.effect:
            restrictive = {
                BoundaryClauseEffect.EXCLUDED,
                BoundaryClauseEffect.REQUIRED,
                BoundaryClauseEffect.LIMITED,
                BoundaryClauseEffect.CONDITIONAL,
            }
            if before.effect is BoundaryClauseEffect.PERMITTED and after.effect in restrictive:
                return BoundaryComparisonOutcome.NARROWED
            if after.effect is BoundaryClauseEffect.PERMITTED and before.effect in restrictive:
                return BoundaryComparisonOutcome.BROADENED
            return BoundaryComparisonOutcome.INDETERMINATE
        try:
            old_value = Decimal(before.value or "")
            new_value = Decimal(after.value or "")
        except InvalidOperation:
            if before.operator in {"IN", "NOT_IN"}:
                old_set = {item.strip() for item in (before.value or "").split(",")}
                new_set = {item.strip() for item in (after.value or "").split(",")}
                if old_set == new_set:
                    return BoundaryComparisonOutcome.UNCHANGED
                permission = before.operator == "IN"
                if new_set < old_set:
                    return (
                        BoundaryComparisonOutcome.NARROWED
                        if permission
                        else BoundaryComparisonOutcome.BROADENED
                    )
                if new_set > old_set:
                    return (
                        BoundaryComparisonOutcome.BROADENED
                        if permission
                        else BoundaryComparisonOutcome.NARROWED
                    )
            return BoundaryComparisonOutcome.INDETERMINATE
        if new_value == old_value:
            return BoundaryComparisonOutcome.UNCHANGED
        if before.operator in {"LTE", "LT"}:
            return (
                BoundaryComparisonOutcome.NARROWED
                if new_value < old_value
                else BoundaryComparisonOutcome.BROADENED
            )
        if before.operator in {"GTE", "GT"}:
            return (
                BoundaryComparisonOutcome.NARROWED
                if new_value > old_value
                else BoundaryComparisonOutcome.BROADENED
            )
        return BoundaryComparisonOutcome.INDETERMINATE

    def current_authorized_decision(
        self,
        *,
        case_id: RecordId,
        configuration_version_id: RecordVersionId,
        effective_at: datetime,
        known_at: datetime | None = None,
    ) -> AuthorizedDecisionSelection:
        effective_at = require_utc(effective_at)
        knowledge_time = require_utc(known_at or self._clock.now())
        found: list[AuthorizedDecisionFound] = []
        with self._increment4_store.read_transaction() as transaction:
            for decision_version_id in transaction.decision_versions(
                case_id=case_id, configuration_version_id=configuration_version_id
            ):
                detail = transaction.decision_detail(decision_version_id)
                version = transaction.get_version(decision_version_id)
                if detail is None or version is None:
                    continue
                current = transaction.select_current(
                    SelectionQuery(
                        family=version.family,
                        scope=version.scope,
                        effective_at=effective_at,
                        known_at=knowledge_time,
                        record_id=version.record_id,
                    )
                )
                if not isinstance(current, SelectionFound) or (
                    current.candidate.version_id != decision_version_id
                ):
                    continue
                authorized_events = [
                    event
                    for event in transaction.get_history(detail.decision_id).status_events
                    if event.target_version_id == decision_version_id
                    and event.new_status == DecisionStatus.AUTHORIZED.value
                    and event.effective_at <= effective_at
                    and event.recorded_at <= knowledge_time
                ]
                if not authorized_events:
                    continue
                basis_candidates: list[RecordVersionId] = []
                for basis_version_id in transaction.authorization_basis_versions(
                    decision_version_id=decision_version_id
                ):
                    basis = transaction.authorization_basis_detail(basis_version_id)
                    basis_version = transaction.get_version(basis_version_id)
                    if basis is None or basis_version is None:
                        continue
                    basis_current = transaction.select_current(
                        SelectionQuery(
                            family=basis_version.family,
                            scope=basis_version.scope,
                            effective_at=effective_at,
                            known_at=knowledge_time,
                            record_id=basis_version.record_id,
                        )
                    )
                    if isinstance(basis_current, SelectionFound) and (
                        basis_current.candidate.version_id == basis_version_id
                    ):
                        basis_candidates.append(basis_version_id)
                if len(basis_candidates) == 1:
                    found.append(
                        AuthorizedDecisionFound(
                            decision_version_id,
                            detail.boundary_snapshot_version_id,
                            basis_candidates[0],
                        )
                    )
                elif len(basis_candidates) > 1:
                    return AuthorizedDecisionConflict(
                        frozenset({decision_version_id}), frozenset(basis_candidates)
                    )
        if not found:
            return AuthorizedDecisionNotEstablished()
        if len(found) == 1:
            return found[0]
        return AuthorizedDecisionConflict(
            frozenset(item.decision_version_id for item in found),
            frozenset(item.authorization_basis_version_id for item in found),
        )
