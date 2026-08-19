"""SQLite + SQLAlchemy Core implementation of the integrity persistence ports."""

from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime
from typing import Any, cast

from sqlalchemy import Connection, Engine, create_engine, event, func, insert, or_, select
from sqlalchemy.engine import RowMapping
from sqlalchemy.exc import OperationalError

from paim.audit.models import ActorResolution, AuditFact
from paim.domain.increment3 import (
    AcceptanceSelectionDetail,
    AnalyticalInputDetail,
    AnalyticalLane,
    ApplicabilityOutcome,
    ApplicabilityTargetType,
    AuthorityApplicabilityContext,
    EvidenceApplicabilityDetail,
    FitnessOutcome,
    LaneFitnessDetail,
    MaterialEvidenceBasisInput,
)
from paim.domain.increment4 import (
    AuthorizationBasisDetail,
    BoundaryClauseDetail,
    BoundaryClauseEffect,
    BoundaryClauseInput,
    BoundarySnapshotDetail,
    BoundaryVerificationMode,
    DecisionDetail,
    DecisionStatus,
    IntegrationDetail,
    IntegrationStatus,
    PreauthorizedActivationMechanismInput,
)
from paim.domain.increment5 import (
    CompletionAcceptanceDetail,
    CompletionAcceptanceOutcome,
    CompletionAcceptanceStatus,
    CompletionCriterionResult,
    CompletionResultDetail,
    CriterionOutcome,
    InterventionDetail,
    InterventionStatus,
    ObligationDetail,
    ObligationSetDetail,
    RequirementType,
)
from paim.domain.models import (
    ConfigurationVersionContext,
    DelegationEffect,
    GoverningDesignationDetail,
    RoleAssignmentDetail,
    RoleTargetType,
)
from paim.integrity.ids import (
    AuditId,
    CommandId,
    EventId,
    RecordId,
    RecordVersionId,
    RelationshipId,
)
from paim.integrity.records import (
    FinalizedRecordVersion,
    RelationshipType,
    StatusEvent,
    VersionRelationship,
)
from paim.integrity.selection import (
    CurrentSelection,
    SelectionCandidate,
    SelectionConflict,
    SelectionFound,
    SelectionQuery,
    select_current,
)
from paim.integrity.time import EffectiveInterval, from_epoch_microseconds, to_epoch_microseconds
from paim.persistence.ports import (
    CommandOutcome,
    IdempotencyFact,
    NestedSemanticCommit,
    RecordHistory,
    WriterContention,
)
from paim.persistence.sqlite.schema import (
    activation_authorization_delegations,
    activation_authorization_records,
    activation_authorization_versions,
    affected_use_references,
    analytical_input_versions,
    analytical_inputs,
    audit_facts,
    authority_gap_versions,
    authority_gaps,
    authority_record_versions,
    authority_records,
    boundary_clause_records,
    boundary_clause_versions,
    boundary_determination_evidence,
    boundary_determination_records,
    boundary_determination_versions,
    boundary_snapshot_records,
    boundary_snapshot_versions,
    bounded_proceed_boundary_clauses,
    bounded_proceed_delegations,
    bounded_proceed_records,
    bounded_proceed_versions,
    candidate_disposition_versions,
    candidate_dispositions,
    completion_acceptance_delegations,
    completion_acceptance_records,
    completion_acceptance_versions,
    completion_acceptor_mechanism_records,
    completion_acceptor_mechanism_versions,
    completion_result_criteria,
    completion_result_evidence,
    completion_result_records,
    completion_result_versions,
    configuration_determinations,
    continued_validity_delegations,
    continued_validity_mechanism_records,
    continued_validity_mechanism_versions,
    continued_validity_records,
    continued_validity_versions,
    decision_authority_gaps,
    decision_authority_records,
    decision_authorization_basis_records,
    decision_authorization_basis_versions,
    decision_authorization_delegations,
    decision_authorization_gaps,
    decision_confirmation_records,
    decision_confirmation_versions,
    decision_preauthorized_activation_mechanisms,
    decision_records,
    decision_uncertainty_links,
    decision_versions,
    dependency_candidate_set_members,
    dependency_candidate_set_records,
    dependency_candidate_set_versions,
    evidence_applicability_records,
    evidence_applicability_versions,
    evidence_records,
    evidence_versions,
    exact_evidence_links,
    governing_configuration_designations,
    idempotency_facts,
    input_acceptance_records,
    input_acceptance_versions,
    integration_authority_gaps,
    integration_authority_records,
    integration_material_applicability,
    integration_records,
    integration_versions,
    interim_disposition_records,
    interim_disposition_versions,
    intervention_records,
    intervention_replacement_records,
    intervention_replacement_versions,
    intervention_versions,
    lane_fitness_records,
    lane_fitness_versions,
    learning_item_evidence,
    learning_item_records,
    learning_item_versions,
    managed_configuration_versions,
    managed_configurations,
    material_evidence_basis,
    metadata,
    obligation_records,
    obligation_set_records,
    obligation_set_versions,
    obligation_versions,
    paim_actor_versions,
    paim_actors,
    paim_case_links,
    paim_case_versions,
    paim_cases,
    prerequisite_evaluation_basis_items,
    prerequisite_evaluation_basis_records,
    prerequisite_evaluation_basis_versions,
    reassessment_completion_outcomes,
    reassessment_determination_reassessments,
    reassessment_determination_records,
    reassessment_determination_triggers,
    reassessment_determination_versions,
    reassessment_mechanism_records,
    reassessment_mechanism_versions,
    reassessment_records,
    reassessment_versions,
    record_versions,
    records,
    register_notification_intents,
    register_output_manifests,
    role_assignment_versions,
    role_assignments,
    shared_dependency_equivalence_delegations,
    shared_dependency_equivalence_records,
    shared_dependency_equivalence_versions,
    shared_dependency_mechanism_records,
    shared_dependency_mechanism_versions,
    shared_dependency_records,
    shared_dependency_versions,
    status_events,
    target_activation_events,
    trigger_determination_records,
    trigger_determination_versions,
    trigger_membership_records,
    trigger_membership_versions,
    trigger_records,
    trigger_set_members,
    trigger_versions,
    uncertainty_classification_records,
    uncertainty_classification_versions,
    version_relationships,
)

_semantic_active: ContextVar[bool] = ContextVar("paim_semantic_transaction_active", default=False)


def _enable_foreign_keys(dbapi_connection: Any, _connection_record: Any) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def _outcome_json(outcome: CommandOutcome) -> str:
    return json.dumps(
        {
            "command_id": outcome.command_id,
            "record_id": outcome.record_id,
            "version_ids": list(outcome.version_ids),
            "status_event_ids": list(outcome.status_event_ids),
            "relationship_ids": list(outcome.relationship_ids),
            "audit_id": outcome.audit_id,
            "result": outcome.result,
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def _parse_outcome(value: str) -> CommandOutcome:
    data = cast("dict[str, Any]", json.loads(value))
    return CommandOutcome(
        command_id=cast("str", data["command_id"]),
        record_id=cast("str", data["record_id"]),
        version_ids=tuple(cast("list[str]", data["version_ids"])),
        status_event_ids=tuple(cast("list[str]", data["status_event_ids"])),
        relationship_ids=tuple(cast("list[str]", data["relationship_ids"])),
        audit_id=cast("str", data["audit_id"]),
        result=cast("str", data["result"]),
    )


def _version_from_row(row: RowMapping) -> FinalizedRecordVersion:
    end_us = cast("int | None", row["effective_to_us"])
    return FinalizedRecordVersion(
        record_id=RecordId.parse(cast("str", row["record_id"])),
        version_id=RecordVersionId.parse(cast("str", row["version_id"])),
        family=cast("str", row["family"]),
        scope=cast("str", row["scope"]),
        content_json=cast("str", row["content_json"]),
        recorded_at=from_epoch_microseconds(cast("int", row["recorded_at_us"])),
        effective=EffectiveInterval(
            from_epoch_microseconds(cast("int", row["effective_from_us"])),
            from_epoch_microseconds(end_us) if end_us is not None else None,
        ),
        creator=cast("str", row["creator"]),
    )


def _event_from_row(row: RowMapping) -> StatusEvent:
    return StatusEvent(
        event_id=EventId.parse(cast("str", row["event_id"])),
        target_version_id=RecordVersionId.parse(cast("str", row["target_version_id"])),
        prior_status=cast("str", row["prior_status"]),
        new_status=cast("str", row["new_status"]),
        recorded_at=from_epoch_microseconds(cast("int", row["recorded_at_us"])),
        effective_at=from_epoch_microseconds(cast("int", row["effective_at_us"])),
        actor=cast("str", row["actor"]),
        basis=cast("str", row["basis"]),
    )


def _relationship_from_row(row: RowMapping) -> VersionRelationship:
    return VersionRelationship(
        relationship_id=RelationshipId.parse(cast("str", row["relationship_id"])),
        source_version_id=RecordVersionId.parse(cast("str", row["source_version_id"])),
        target_version_id=RecordVersionId.parse(cast("str", row["target_version_id"])),
        relationship_type=RelationshipType(cast("str", row["relationship_type"])),
        recorded_at=from_epoch_microseconds(cast("int", row["recorded_at_us"])),
        reason=cast("str", row["reason"]),
    )


def _audit_from_row(row: RowMapping) -> AuditFact:
    return AuditFact(
        audit_id=AuditId.parse(cast("str", row["audit_id"])),
        principal_id=cast("str", row["principal_id"]),
        actor_id=cast("str | None", row["actor_id"]),
        actor_resolution=ActorResolution(cast("str", row["actor_resolution"])),
        operation=cast("str", row["operation"]),
        result=cast("str", row["result"]),
        command_id=CommandId.parse(cast("str", row["command_id"])),
        idempotency_scope=cast("str", row["idempotency_scope"]),
        idempotency_key=cast("str", row["idempotency_key"]),
        correlation_id=cast("str | None", row["correlation_id"]),
        causation_id=cast("str | None", row["causation_id"]),
        target_record_id=RecordId.parse(cast("str", row["target_record_id"])),
        affected_version_ids=tuple(
            RecordVersionId.parse(value)
            for value in cast(
                "list[str]", json.loads(cast("str", row["affected_version_ids_json"]))
            )
        ),
        expected_precondition=cast("str", row["expected_precondition"]),
        observed_precondition=cast("str", row["observed_precondition"]),
        effective_at=from_epoch_microseconds(cast("int", row["effective_at_us"])),
        recorded_at=from_epoch_microseconds(cast("int", row["recorded_at_us"])),
        reason_outcomes=tuple(
            cast("list[str]", json.loads(cast("str", row["reason_outcomes_json"])))
        ),
        request_digest=cast("str", row["request_digest"]),
    )


class SQLiteIntegrityTransaction:
    """Operations bound to one explicit database transaction."""

    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    @property
    def connection(self) -> Connection:
        """Expose the transaction connection to normalized domain projections."""
        return self._connection

    def get_idempotency(self, scope: str, key: str) -> IdempotencyFact | None:
        row = (
            self._connection.execute(
                select(idempotency_facts).where(
                    idempotency_facts.c.scope == scope,
                    idempotency_facts.c.idempotency_key == key,
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return None
        return IdempotencyFact(
            scope=cast("str", row["scope"]),
            key=cast("str", row["idempotency_key"]),
            digest=cast("str", row["digest"]),
            command_id=cast("str", row["command_id"]),
            outcome=_parse_outcome(cast("str", row["outcome_json"])),
            recorded_at=from_epoch_microseconds(cast("int", row["recorded_at_us"])),
        )

    def add_idempotency(self, fact: IdempotencyFact) -> None:
        self._connection.execute(
            insert(idempotency_facts).values(
                scope=fact.scope,
                idempotency_key=fact.key,
                digest=fact.digest,
                command_id=fact.command_id,
                outcome_json=_outcome_json(fact.outcome),
                recorded_at_us=to_epoch_microseconds(fact.recorded_at),
            )
        )

    def add_version(self, version: FinalizedRecordVersion) -> None:
        existing = (
            self._connection.execute(
                select(records).where(records.c.record_id == str(version.record_id))
            )
            .mappings()
            .one_or_none()
        )
        if existing is None:
            self._connection.execute(
                insert(records).values(
                    record_id=str(version.record_id), family=version.family, scope=version.scope
                )
            )
        elif existing["family"] != version.family or existing["scope"] != version.scope:
            raise ValueError("Record ID cannot be reused for another family or scope")
        self._connection.execute(
            insert(record_versions).values(
                version_id=str(version.version_id),
                record_id=str(version.record_id),
                content_json=version.content_json,
                finalized=True,
                recorded_at_us=to_epoch_microseconds(version.recorded_at),
                effective_from_us=to_epoch_microseconds(version.effective.start),
                effective_to_us=(
                    to_epoch_microseconds(version.effective.end)
                    if version.effective.end is not None
                    else None
                ),
                creator=version.creator,
            )
        )

    def case_exists(self, case_id: RecordId) -> bool:
        return (
            self._connection.scalar(
                select(func.count())
                .select_from(paim_cases)
                .where(paim_cases.c.case_id == str(case_id))
            )
            == 1
        )

    def add_case(self, case_id: RecordId, version_id: RecordVersionId) -> None:
        if not self.case_exists(case_id):
            self._connection.execute(insert(paim_cases).values(case_id=str(case_id)))
        self._connection.execute(
            insert(paim_case_versions).values(
                version_id=str(version_id),
                case_id=str(case_id),
                initial_lifecycle_state="open",
            )
        )

    def add_case_link(
        self,
        *,
        link_id: str,
        source_case_id: RecordId,
        target_case_id: RecordId,
        relationship_type: str,
        recorded_at_us: int,
        effective_at_us: int,
        actor_id: str,
        reason: str,
    ) -> None:
        self._connection.execute(
            insert(paim_case_links).values(
                link_id=link_id,
                source_case_id=str(source_case_id),
                target_case_id=str(target_case_id),
                relationship_type=relationship_type,
                recorded_at_us=recorded_at_us,
                effective_at_us=effective_at_us,
                actor_id=actor_id,
                reason=reason,
            )
        )

    def configuration_owning_case(self, configuration_id: RecordId) -> RecordId | None:
        value = self._connection.scalar(
            select(managed_configurations.c.owning_case_id).where(
                managed_configurations.c.configuration_id == str(configuration_id)
            )
        )
        return RecordId.parse(cast("str", value)) if value is not None else None

    def add_configuration(
        self,
        *,
        configuration_id: RecordId,
        version_id: RecordVersionId,
        owning_case_id: RecordId,
        maturity: str,
        purpose: str,
    ) -> None:
        existing_owner = self.configuration_owning_case(configuration_id)
        if existing_owner is None:
            self._connection.execute(
                insert(managed_configurations).values(
                    configuration_id=str(configuration_id), owning_case_id=str(owning_case_id)
                )
            )
        elif existing_owner != owning_case_id:
            raise ValueError("Configuration identity cannot change its owning Case")
        self._connection.execute(
            insert(managed_configuration_versions).values(
                version_id=str(version_id),
                configuration_id=str(configuration_id),
                maturity=maturity,
                purpose=purpose,
            )
        )

    def configuration_version_context(
        self, version_id: RecordVersionId
    ) -> ConfigurationVersionContext | None:
        row = (
            self._connection.execute(
                select(
                    managed_configuration_versions.c.configuration_id,
                    managed_configurations.c.owning_case_id,
                    managed_configuration_versions.c.maturity,
                    managed_configuration_versions.c.purpose,
                )
                .join(
                    managed_configurations,
                    managed_configurations.c.configuration_id
                    == managed_configuration_versions.c.configuration_id,
                )
                .where(managed_configuration_versions.c.version_id == str(version_id))
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return None
        return ConfigurationVersionContext(
            configuration_id=RecordId.parse(cast("str", row["configuration_id"])),
            owning_case_id=RecordId.parse(cast("str", row["owning_case_id"])),
            maturity=cast("str", row["maturity"]),
            purpose=cast("str", row["purpose"]),
        )

    def actor_exists(self, actor_id: RecordId) -> bool:
        return (
            self._connection.scalar(
                select(func.count())
                .select_from(paim_actors)
                .where(paim_actors.c.actor_id == str(actor_id))
            )
            == 1
        )

    def add_actor(self, actor_id: RecordId, version_id: RecordVersionId) -> None:
        if not self.actor_exists(actor_id):
            self._connection.execute(insert(paim_actors).values(actor_id=str(actor_id)))
        self._connection.execute(
            insert(paim_actor_versions).values(version_id=str(version_id), actor_id=str(actor_id))
        )

    def add_role_assignment(
        self,
        *,
        assignment_id: RecordId,
        version_id: RecordVersionId,
        actor_id: RecordId,
        role: str,
        target_type: str,
        target_id: str,
        case_context_id: RecordId | None,
        accountable: bool,
        compatibility_key: str,
        delegation_effect: str,
        delegated_from_version_id: RecordVersionId | None,
    ) -> None:
        exists = self._connection.scalar(
            select(func.count())
            .select_from(role_assignments)
            .where(role_assignments.c.assignment_id == str(assignment_id))
        )
        if exists != 1:
            self._connection.execute(
                insert(role_assignments).values(assignment_id=str(assignment_id))
            )
        self._connection.execute(
            insert(role_assignment_versions).values(
                version_id=str(version_id),
                assignment_id=str(assignment_id),
                actor_id=str(actor_id),
                role=role,
                target_type=target_type,
                target_id=target_id,
                case_context_id=str(case_context_id) if case_context_id is not None else None,
                accountable=accountable,
                compatibility_key=compatibility_key,
                delegation_effect=delegation_effect,
                delegated_from_version_id=(
                    str(delegated_from_version_id)
                    if delegated_from_version_id is not None
                    else None
                ),
            )
        )

    def role_assignment_records(
        self, *, role: str, targets: tuple[tuple[str, str], ...]
    ) -> tuple[RecordId, ...]:
        if not targets:
            return ()
        predicates = tuple(
            (role_assignment_versions.c.target_type == target_type)
            & (role_assignment_versions.c.target_id == target_id)
            for target_type, target_id in targets
        )
        values = self._connection.execute(
            select(role_assignment_versions.c.assignment_id)
            .where(role_assignment_versions.c.role == role, or_(*predicates))
            .distinct()
        ).scalars()
        return tuple(RecordId.parse(cast("str", value)) for value in values)

    def role_assignment_detail(self, version_id: RecordVersionId) -> RoleAssignmentDetail | None:
        row = (
            self._connection.execute(
                select(role_assignment_versions).where(
                    role_assignment_versions.c.version_id == str(version_id)
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return None
        case_context = cast("str | None", row["case_context_id"])
        delegated_from = cast("str | None", row["delegated_from_version_id"])
        return RoleAssignmentDetail(
            version_id=RecordVersionId.parse(cast("str", row["version_id"])),
            assignment_id=RecordId.parse(cast("str", row["assignment_id"])),
            actor_id=RecordId.parse(cast("str", row["actor_id"])),
            role=cast("str", row["role"]),
            target_type=RoleTargetType(cast("str", row["target_type"])),
            target_id=cast("str", row["target_id"]),
            case_context_id=RecordId.parse(case_context) if case_context is not None else None,
            accountable=cast("bool", row["accountable"]),
            compatibility_key=cast("str", row["compatibility_key"]),
            delegation_effect=DelegationEffect(cast("str", row["delegation_effect"])),
            delegated_from_version_id=(
                RecordVersionId.parse(delegated_from) if delegated_from is not None else None
            ),
        )

    def add_governing_designation(
        self,
        *,
        version_id: RecordVersionId,
        case_id: RecordId,
        configuration_version_id: RecordVersionId,
        accountable_assignment_version_id: RecordVersionId | None,
        accountable_mechanism: str | None,
    ) -> None:
        self._connection.execute(
            insert(governing_configuration_designations).values(
                version_id=str(version_id),
                case_id=str(case_id),
                configuration_version_id=str(configuration_version_id),
                accountable_assignment_version_id=(
                    str(accountable_assignment_version_id)
                    if accountable_assignment_version_id is not None
                    else None
                ),
                accountable_mechanism=accountable_mechanism,
            )
        )

    def governing_designation_detail(
        self, version_id: RecordVersionId
    ) -> GoverningDesignationDetail | None:
        row = (
            self._connection.execute(
                select(governing_configuration_designations).where(
                    governing_configuration_designations.c.version_id == str(version_id)
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return None
        return GoverningDesignationDetail(
            version_id=RecordVersionId.parse(cast("str", row["version_id"])),
            case_id=RecordId.parse(cast("str", row["case_id"])),
            configuration_version_id=RecordVersionId.parse(
                cast("str", row["configuration_version_id"])
            ),
        )

    def add_configuration_determination(
        self,
        *,
        version_id: RecordVersionId,
        configuration_version_id: RecordVersionId,
        determination_kind: str,
        outcome: str,
        rationale: str,
        accountable_assignment_version_id: RecordVersionId | None,
        accountable_mechanism: str | None,
    ) -> None:
        self._connection.execute(
            insert(configuration_determinations).values(
                version_id=str(version_id),
                configuration_version_id=str(configuration_version_id),
                determination_kind=determination_kind,
                outcome=outcome,
                rationale=rationale,
                accountable_assignment_version_id=(
                    str(accountable_assignment_version_id)
                    if accountable_assignment_version_id is not None
                    else None
                ),
                accountable_mechanism=accountable_mechanism,
            )
        )

    def _identity_exists(self, table: Any, column: Any, value: str) -> bool:
        return (
            self._connection.scalar(select(func.count()).select_from(table).where(column == value))
            == 1
        )

    def add_evidence(
        self,
        *,
        evidence_id: RecordId,
        version_id: RecordVersionId,
        case_id: RecordId | None,
        configuration_id: RecordId | None,
        configuration_version_id: RecordVersionId | None,
        classification: str,
        source: str,
        provenance_json: str,
        observed_at_us: int | None,
        attention: str,
    ) -> None:
        if not self._identity_exists(
            evidence_records, evidence_records.c.evidence_id, str(evidence_id)
        ):
            self._connection.execute(insert(evidence_records).values(evidence_id=str(evidence_id)))
        self._connection.execute(
            insert(evidence_versions).values(
                version_id=str(version_id),
                evidence_id=str(evidence_id),
                case_id=str(case_id) if case_id else None,
                configuration_id=str(configuration_id) if configuration_id else None,
                configuration_version_id=(
                    str(configuration_version_id) if configuration_version_id else None
                ),
                classification=classification,
                source=source,
                provenance_json=provenance_json,
                observed_at_us=observed_at_us,
                attention=attention,
            )
        )

    def add_authority_record(
        self,
        *,
        authority_id: RecordId,
        version_id: RecordVersionId,
        case_id: RecordId | None,
        configuration_id: RecordId | None,
        configuration_version_id: RecordVersionId | None,
        category: str,
        source: str,
        provenance_json: str,
        authority_scope: str,
        requirement: str,
    ) -> None:
        if not self._identity_exists(
            authority_records, authority_records.c.authority_id, str(authority_id)
        ):
            self._connection.execute(
                insert(authority_records).values(authority_id=str(authority_id))
            )
        self._connection.execute(
            insert(authority_record_versions).values(
                version_id=str(version_id),
                authority_id=str(authority_id),
                case_id=str(case_id) if case_id else None,
                configuration_id=str(configuration_id) if configuration_id else None,
                configuration_version_id=(
                    str(configuration_version_id) if configuration_version_id else None
                ),
                category=category,
                source=source,
                provenance_json=provenance_json,
                authority_scope=authority_scope,
                requirement=requirement,
            )
        )

    def add_authority_gap(
        self,
        *,
        gap_id: RecordId,
        version_id: RecordVersionId,
        case_id: RecordId,
        configuration_id: RecordId,
        configuration_version_id: RecordVersionId,
        question_id: str,
        question: str,
        authority_scope: str,
        rationale: str,
        provenance_json: str,
    ) -> None:
        if not self._identity_exists(authority_gaps, authority_gaps.c.gap_id, str(gap_id)):
            self._connection.execute(insert(authority_gaps).values(gap_id=str(gap_id)))
        self._connection.execute(
            insert(authority_gap_versions).values(
                version_id=str(version_id),
                gap_id=str(gap_id),
                case_id=str(case_id),
                configuration_id=str(configuration_id),
                configuration_version_id=str(configuration_version_id),
                question_id=question_id,
                question=question,
                authority_scope=authority_scope,
                rationale=rationale,
                provenance_json=provenance_json,
            )
        )

    def add_exact_evidence_link(
        self,
        *,
        source_version_id: RecordVersionId,
        evidence_version_id: RecordVersionId,
        link_role: str,
    ) -> None:
        self._connection.execute(
            insert(exact_evidence_links).values(
                source_version_id=str(source_version_id),
                evidence_version_id=str(evidence_version_id),
                link_role=link_role,
            )
        )

    def add_affected_use_reference(
        self, *, source_version_id: RecordVersionId, use_reference: str
    ) -> None:
        self._connection.execute(
            insert(affected_use_references).values(
                source_version_id=str(source_version_id), use_reference=use_reference
            )
        )

    def add_evidence_applicability(
        self,
        *,
        applicability_id: RecordId,
        version_id: RecordVersionId,
        evidence_version_id: RecordVersionId,
        target_type: str,
        target_id: str,
        target_version_id: RecordVersionId | None,
        purpose: str,
        assessed_scope: str,
        case_id: RecordId | None,
        configuration_id: RecordId | None,
        configuration_version_id: RecordVersionId | None,
        outcome: str,
        conditions_json: str,
        limitations_json: str,
        rationale: str,
        assessor_actor_id: RecordId,
        accountable_assignment_version_id: RecordVersionId | None,
        accountable_mechanism: str | None,
    ) -> None:
        if not self._identity_exists(
            evidence_applicability_records,
            evidence_applicability_records.c.applicability_id,
            str(applicability_id),
        ):
            self._connection.execute(
                insert(evidence_applicability_records).values(
                    applicability_id=str(applicability_id)
                )
            )
        self._connection.execute(
            insert(evidence_applicability_versions).values(
                version_id=str(version_id),
                applicability_id=str(applicability_id),
                evidence_version_id=str(evidence_version_id),
                target_type=target_type,
                target_id=target_id,
                target_version_id=str(target_version_id) if target_version_id else None,
                purpose=purpose,
                assessed_scope=assessed_scope,
                case_id=str(case_id) if case_id else None,
                configuration_id=str(configuration_id) if configuration_id else None,
                configuration_version_id=(
                    str(configuration_version_id) if configuration_version_id else None
                ),
                outcome=outcome,
                conditions_json=conditions_json,
                limitations_json=limitations_json,
                rationale=rationale,
                assessor_actor_id=str(assessor_actor_id),
                accountable_assignment_version_id=(
                    str(accountable_assignment_version_id)
                    if accountable_assignment_version_id
                    else None
                ),
                accountable_mechanism=accountable_mechanism,
            )
        )

    def evidence_applicability_detail(
        self, version_id: RecordVersionId
    ) -> EvidenceApplicabilityDetail | None:
        row = (
            self._connection.execute(
                select(evidence_applicability_versions).where(
                    evidence_applicability_versions.c.version_id == str(version_id)
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return None
        target_version = cast("str | None", row["target_version_id"])
        assignment = cast("str | None", row["accountable_assignment_version_id"])
        return EvidenceApplicabilityDetail(
            version_id=version_id,
            applicability_id=RecordId.parse(cast("str", row["applicability_id"])),
            evidence_version_id=RecordVersionId.parse(cast("str", row["evidence_version_id"])),
            target_type=ApplicabilityTargetType(cast("str", row["target_type"])),
            target_id=cast("str", row["target_id"]),
            target_version_id=(RecordVersionId.parse(target_version) if target_version else None),
            case_id=(RecordId.parse(cast("str", row["case_id"])) if row["case_id"] else None),
            configuration_version_id=(
                RecordVersionId.parse(cast("str", row["configuration_version_id"]))
                if row["configuration_version_id"]
                else None
            ),
            purpose=cast("str", row["purpose"]),
            assessed_scope=cast("str", row["assessed_scope"]),
            outcome=ApplicabilityOutcome(cast("str", row["outcome"])),
            accountable_assignment_version_id=(
                RecordVersionId.parse(assignment) if assignment else None
            ),
            accountable_mechanism=cast("str | None", row["accountable_mechanism"]),
        )

    def add_analytical_input(
        self,
        *,
        input_id: RecordId,
        version_id: RecordVersionId,
        lane: str,
        case_id: RecordId,
        configuration_id: RecordId,
        configuration_version_id: RecordVersionId,
        purpose: str,
        finding: str,
        boundary: str,
        uncertainties_json: str,
        implication: str,
        provenance_json: str,
    ) -> None:
        existing_lane = self._connection.scalar(
            select(analytical_inputs.c.lane).where(analytical_inputs.c.input_id == str(input_id))
        )
        if existing_lane is None:
            self._connection.execute(
                insert(analytical_inputs).values(input_id=str(input_id), lane=lane)
            )
        elif existing_lane != lane:
            raise ValueError("analytical Input identity cannot change Value/Risk lane")
        self._connection.execute(
            insert(analytical_input_versions).values(
                version_id=str(version_id),
                input_id=str(input_id),
                lane=lane,
                case_id=str(case_id),
                configuration_id=str(configuration_id),
                configuration_version_id=str(configuration_version_id),
                purpose=purpose,
                finding=finding,
                boundary=boundary,
                uncertainties_json=uncertainties_json,
                implication=implication,
                provenance_json=provenance_json,
            )
        )

    def analytical_input_detail(self, version_id: RecordVersionId) -> AnalyticalInputDetail | None:
        row = (
            self._connection.execute(
                select(analytical_input_versions).where(
                    analytical_input_versions.c.version_id == str(version_id)
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return None
        return AnalyticalInputDetail(
            version_id=version_id,
            input_id=RecordId.parse(cast("str", row["input_id"])),
            lane=AnalyticalLane(cast("str", row["lane"])),
            case_id=RecordId.parse(cast("str", row["case_id"])),
            configuration_id=RecordId.parse(cast("str", row["configuration_id"])),
            configuration_version_id=RecordVersionId.parse(
                cast("str", row["configuration_version_id"])
            ),
            purpose=cast("str", row["purpose"]),
            implication=cast("str", row["implication"]),
        )

    def analytical_input_versions(
        self,
        *,
        lane: str,
        configuration_version_id: RecordVersionId,
        purpose: str,
    ) -> tuple[RecordVersionId, ...]:
        values = self._connection.execute(
            select(analytical_input_versions.c.version_id).where(
                analytical_input_versions.c.lane == lane,
                analytical_input_versions.c.configuration_version_id
                == str(configuration_version_id),
                analytical_input_versions.c.purpose == purpose,
            )
        ).scalars()
        return tuple(RecordVersionId.parse(cast("str", value)) for value in values)

    def add_candidate_disposition(
        self,
        *,
        disposition_id: RecordId,
        version_id: RecordVersionId,
        input_version_id: RecordVersionId,
        lane: str,
        configuration_version_id: RecordVersionId,
        use_context: str,
        purpose: str,
        disposition: str,
        rationale: str,
        accountable_assignment_version_id: RecordVersionId | None,
        accountable_mechanism: str | None,
    ) -> None:
        if not self._identity_exists(
            candidate_dispositions, candidate_dispositions.c.disposition_id, str(disposition_id)
        ):
            self._connection.execute(
                insert(candidate_dispositions).values(disposition_id=str(disposition_id))
            )
        self._connection.execute(
            insert(candidate_disposition_versions).values(
                version_id=str(version_id),
                disposition_id=str(disposition_id),
                input_version_id=str(input_version_id),
                lane=lane,
                configuration_version_id=str(configuration_version_id),
                use_context=use_context,
                purpose=purpose,
                disposition=disposition,
                rationale=rationale,
                accountable_assignment_version_id=(
                    str(accountable_assignment_version_id)
                    if accountable_assignment_version_id
                    else None
                ),
                accountable_mechanism=accountable_mechanism,
            )
        )

    def candidate_has_disposition(
        self,
        *,
        input_version_id: RecordVersionId,
        lane: str,
        configuration_version_id: RecordVersionId,
        use_context: str,
        purpose: str,
        effective_at: datetime,
        known_at: datetime,
    ) -> bool:
        rows = self._connection.execute(
            select(
                candidate_disposition_versions.c.disposition_id,
                records.c.scope,
            )
            .join(
                record_versions,
                record_versions.c.version_id == candidate_disposition_versions.c.version_id,
            )
            .join(records, records.c.record_id == record_versions.c.record_id)
            .where(
                candidate_disposition_versions.c.input_version_id == str(input_version_id),
                candidate_disposition_versions.c.lane == lane,
                candidate_disposition_versions.c.configuration_version_id
                == str(configuration_version_id),
                candidate_disposition_versions.c.use_context == use_context,
                candidate_disposition_versions.c.purpose == purpose,
            )
        ).mappings()
        for row in rows:
            selection = self.select_current(
                SelectionQuery(
                    family="candidate-disposition",
                    scope=cast("str", row["scope"]),
                    effective_at=effective_at,
                    known_at=known_at,
                    record_id=RecordId.parse(cast("str", row["disposition_id"])),
                )
            )
            if isinstance(selection, SelectionFound):
                return True
        return False

    def add_lane_fitness(
        self,
        *,
        fitness_id: RecordId,
        version_id: RecordVersionId,
        lane: str,
        input_version_id: RecordVersionId,
        case_id: RecordId,
        configuration_id: RecordId,
        configuration_version_id: RecordVersionId,
        use_context: str,
        purpose: str,
        outcome: str,
        rationale: str,
        indeterminate_treatment: str | None,
        decision_limiting: bool,
        accountable_assignment_version_id: RecordVersionId | None,
        accountable_mechanism: str | None,
        material_evidence: tuple[MaterialEvidenceBasisInput, ...],
    ) -> None:
        if not self._identity_exists(
            lane_fitness_records, lane_fitness_records.c.fitness_id, str(fitness_id)
        ):
            self._connection.execute(
                insert(lane_fitness_records).values(fitness_id=str(fitness_id))
            )
        self._connection.execute(
            insert(lane_fitness_versions).values(
                version_id=str(version_id),
                fitness_id=str(fitness_id),
                lane=lane,
                input_version_id=str(input_version_id),
                case_id=str(case_id),
                configuration_id=str(configuration_id),
                configuration_version_id=str(configuration_version_id),
                use_context=use_context,
                purpose=purpose,
                outcome=outcome,
                rationale=rationale,
                indeterminate_treatment=indeterminate_treatment,
                decision_limiting=decision_limiting,
                accountable_assignment_version_id=(
                    str(accountable_assignment_version_id)
                    if accountable_assignment_version_id
                    else None
                ),
                accountable_mechanism=accountable_mechanism,
            )
        )
        for basis in material_evidence:
            self._connection.execute(
                insert(material_evidence_basis).values(
                    fitness_version_id=str(version_id),
                    evidence_version_id=str(basis.evidence_version_id),
                    applicability_version_id=str(basis.applicability_version_id),
                    role=basis.role,
                    required_support=basis.required_support,
                    claimed_scope=basis.claimed_scope,
                )
            )

    def lane_fitness_detail(self, version_id: RecordVersionId) -> LaneFitnessDetail | None:
        row = (
            self._connection.execute(
                select(lane_fitness_versions).where(
                    lane_fitness_versions.c.version_id == str(version_id)
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return None
        return LaneFitnessDetail(
            version_id=version_id,
            lane=AnalyticalLane(cast("str", row["lane"])),
            input_version_id=RecordVersionId.parse(cast("str", row["input_version_id"])),
            configuration_version_id=RecordVersionId.parse(
                cast("str", row["configuration_version_id"])
            ),
            use_context=cast("str", row["use_context"]),
            purpose=cast("str", row["purpose"]),
            outcome=FitnessOutcome(cast("str", row["outcome"])),
            rationale=cast("str", row["rationale"]),
            indeterminate_treatment=cast("str | None", row["indeterminate_treatment"]),
            decision_limiting=cast("bool", row["decision_limiting"]),
        )

    def material_evidence_basis(
        self, fitness_version_id: RecordVersionId
    ) -> tuple[MaterialEvidenceBasisInput, ...]:
        rows = self._connection.execute(
            select(material_evidence_basis).where(
                material_evidence_basis.c.fitness_version_id == str(fitness_version_id)
            )
        ).mappings()
        return tuple(
            MaterialEvidenceBasisInput(
                evidence_version_id=RecordVersionId.parse(cast("str", row["evidence_version_id"])),
                applicability_version_id=RecordVersionId.parse(
                    cast("str", row["applicability_version_id"])
                ),
                role=cast("str", row["role"]),
                required_support=cast("bool", row["required_support"]),
                claimed_scope=cast("str", row["claimed_scope"]),
            )
            for row in rows
        )

    def add_acceptance_selection(
        self,
        *,
        acceptance_id: RecordId,
        version_id: RecordVersionId,
        lane: str,
        input_version_id: RecordVersionId,
        case_id: RecordId,
        configuration_id: RecordId,
        configuration_version_id: RecordVersionId,
        use_context: str,
        purpose: str,
        rationale: str,
        accountable_assignment_version_id: RecordVersionId | None,
        accountable_mechanism: str | None,
        fitness_version_id: RecordVersionId,
    ) -> None:
        if not self._identity_exists(
            input_acceptance_records, input_acceptance_records.c.acceptance_id, str(acceptance_id)
        ):
            self._connection.execute(
                insert(input_acceptance_records).values(acceptance_id=str(acceptance_id))
            )
        self._connection.execute(
            insert(input_acceptance_versions).values(
                version_id=str(version_id),
                acceptance_id=str(acceptance_id),
                lane=lane,
                input_version_id=str(input_version_id),
                case_id=str(case_id),
                configuration_id=str(configuration_id),
                configuration_version_id=str(configuration_version_id),
                use_context=use_context,
                purpose=purpose,
                rationale=rationale,
                accountable_assignment_version_id=(
                    str(accountable_assignment_version_id)
                    if accountable_assignment_version_id
                    else None
                ),
                accountable_mechanism=accountable_mechanism,
                fitness_version_id=str(fitness_version_id),
            )
        )

    def acceptance_selection_detail(
        self, version_id: RecordVersionId
    ) -> AcceptanceSelectionDetail | None:
        row = (
            self._connection.execute(
                select(input_acceptance_versions).where(
                    input_acceptance_versions.c.version_id == str(version_id)
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return None
        return AcceptanceSelectionDetail(
            version_id=version_id,
            acceptance_id=RecordId.parse(cast("str", row["acceptance_id"])),
            lane=AnalyticalLane(cast("str", row["lane"])),
            input_version_id=RecordVersionId.parse(cast("str", row["input_version_id"])),
            case_id=RecordId.parse(cast("str", row["case_id"])),
            configuration_id=RecordId.parse(cast("str", row["configuration_id"])),
            configuration_version_id=RecordVersionId.parse(
                cast("str", row["configuration_version_id"])
            ),
            use_context=cast("str", row["use_context"]),
            purpose=cast("str", row["purpose"]),
            fitness_version_id=RecordVersionId.parse(cast("str", row["fitness_version_id"])),
        )

    def version_statuses(
        self,
        *,
        version_id: RecordVersionId,
        effective_at: datetime,
        known_at: datetime,
    ) -> tuple[str, ...]:
        values = self._connection.execute(
            select(status_events.c.new_status).where(
                status_events.c.target_version_id == str(version_id),
                status_events.c.effective_at_us <= to_epoch_microseconds(effective_at),
                status_events.c.recorded_at_us <= to_epoch_microseconds(known_at),
            )
        ).scalars()
        return tuple(cast("str", value) for value in values)

    def evidence_attention(self, version_id: RecordVersionId) -> str | None:
        value = self._connection.execute(
            select(evidence_versions.c.attention).where(
                evidence_versions.c.version_id == str(version_id)
            )
        ).scalar_one_or_none()
        return cast("str | None", value)

    def current_authority_gap_versions(
        self,
        *,
        case_id: RecordId,
        configuration_version_id: RecordVersionId,
        effective_at: datetime,
        known_at: datetime,
    ) -> tuple[RecordVersionId, ...]:
        rows = self._connection.execute(
            select(authority_gap_versions.c.gap_id, records.c.scope)
            .join(
                record_versions, record_versions.c.version_id == authority_gap_versions.c.version_id
            )
            .join(records, records.c.record_id == record_versions.c.record_id)
            .where(
                authority_gap_versions.c.case_id == str(case_id),
                authority_gap_versions.c.configuration_version_id == str(configuration_version_id),
            )
            .distinct()
        ).mappings()
        current: list[RecordVersionId] = []
        for row in rows:
            result = self.select_current(
                SelectionQuery(
                    family="authority-gap",
                    scope=cast("str", row["scope"]),
                    effective_at=effective_at,
                    known_at=known_at,
                    record_id=RecordId.parse(cast("str", row["gap_id"])),
                )
            )
            if isinstance(result, SelectionFound):
                current.append(result.candidate.version_id)
            elif isinstance(result, SelectionConflict):
                current.extend(candidate.version_id for candidate in result.candidates)
        return tuple(current)

    def exact_target_exists(
        self,
        *,
        target_type: ApplicabilityTargetType,
        target_id: str,
        target_version_id: RecordVersionId | None,
        case_id: RecordId | None,
        configuration_version_id: RecordVersionId | None,
    ) -> bool:
        if target_type is ApplicabilityTargetType.MANAGED_CONFIGURATION_VERSION:
            if target_version_id is None:
                return False
            context = self.configuration_version_context(target_version_id)
            return context is not None and str(context.configuration_id) == target_id
        if target_type in {
            ApplicabilityTargetType.VALUE_INPUT_VERSION,
            ApplicabilityTargetType.RISK_INPUT_VERSION,
        }:
            if target_version_id is None:
                return False
            detail = self.analytical_input_detail(target_version_id)
            expected_lane = (
                AnalyticalLane.VALUE
                if target_type is ApplicabilityTargetType.VALUE_INPUT_VERSION
                else AnalyticalLane.RISK
            )
            return (
                detail is not None
                and detail.lane is expected_lane
                and str(detail.input_id) == target_id
            )
        return (
            self.authority_applicability_context(
                target_type=target_type,
                target_id=target_id,
                target_version_id=target_version_id,
                case_id=case_id,
                configuration_version_id=configuration_version_id,
            )
            is not None
        )

    def authority_applicability_context(
        self,
        *,
        target_type: ApplicabilityTargetType,
        target_id: str,
        target_version_id: RecordVersionId | None,
        case_id: RecordId | None,
        configuration_version_id: RecordVersionId | None,
    ) -> AuthorityApplicabilityContext | None:
        if target_type is ApplicabilityTargetType.AUTHORITY_RECORD_VERSION:
            if target_version_id is None:
                return None
            row = (
                self._connection.execute(
                    select(authority_record_versions).where(
                        authority_record_versions.c.version_id == str(target_version_id),
                        authority_record_versions.c.authority_id == target_id,
                    )
                )
                .mappings()
                .one_or_none()
            )
        elif target_type is ApplicabilityTargetType.AUTHORITY_GAP:
            query = select(authority_gap_versions)
            if target_version_id is not None:
                query = query.where(
                    authority_gap_versions.c.version_id == str(target_version_id),
                    or_(
                        authority_gap_versions.c.gap_id == target_id,
                        authority_gap_versions.c.question_id == target_id,
                    ),
                )
            else:
                query = query.where(authority_gap_versions.c.question_id == target_id)
                if case_id is not None:
                    query = query.where(authority_gap_versions.c.case_id == str(case_id))
                if configuration_version_id is not None:
                    query = query.where(
                        authority_gap_versions.c.configuration_version_id
                        == str(configuration_version_id)
                    )
            rows = self._connection.execute(query).mappings().all()
            contexts = {
                (
                    cast("str", item["gap_id"]),
                    cast("str", item["case_id"]),
                    cast("str", item["configuration_id"]),
                    cast("str", item["configuration_version_id"]),
                    cast("str", item["authority_scope"]),
                )
                for item in rows
            }
            if len(contexts) != 1:
                return None
            row = rows[0]
        else:
            return None
        if row is None:
            return None
        row_case = cast("str | None", row["case_id"])
        row_configuration = cast("str | None", row["configuration_id"])
        row_configuration_version = cast("str | None", row["configuration_version_id"])
        return AuthorityApplicabilityContext(
            case_id=RecordId.parse(row_case) if row_case else None,
            configuration_id=(RecordId.parse(row_configuration) if row_configuration else None),
            configuration_version_id=(
                RecordVersionId.parse(row_configuration_version)
                if row_configuration_version
                else None
            ),
            authority_scope=cast("str", row["authority_scope"]),
        )

    def add_integration(
        self,
        *,
        integration_id: RecordId,
        version_id: RecordVersionId,
        case_id: RecordId,
        configuration_id: RecordId,
        configuration_version_id: RecordVersionId,
        use_context: str,
        purpose: str,
        value_input_version_id: RecordVersionId,
        value_acceptance_version_id: RecordVersionId,
        value_fitness_version_id: RecordVersionId,
        risk_input_version_id: RecordVersionId,
        risk_acceptance_version_id: RecordVersionId,
        risk_fitness_version_id: RecordVersionId,
        integrator_actor_id: RecordId,
        owner_assignment_version_id: RecordVersionId | None,
        accountable_mechanism: str | None,
        status: str,
        material_applicability_version_ids: tuple[RecordVersionId, ...],
        authority_record_version_ids: tuple[RecordVersionId, ...],
        authority_gap_version_ids: tuple[RecordVersionId, ...],
    ) -> None:
        if not self._identity_exists(
            integration_records, integration_records.c.integration_id, str(integration_id)
        ):
            self.connection.execute(
                insert(integration_records).values(integration_id=str(integration_id))
            )
        self.connection.execute(
            insert(integration_versions).values(
                version_id=str(version_id),
                integration_id=str(integration_id),
                case_id=str(case_id),
                configuration_id=str(configuration_id),
                configuration_version_id=str(configuration_version_id),
                use_context=use_context,
                purpose=purpose,
                value_input_version_id=str(value_input_version_id),
                value_acceptance_version_id=str(value_acceptance_version_id),
                value_fitness_version_id=str(value_fitness_version_id),
                risk_input_version_id=str(risk_input_version_id),
                risk_acceptance_version_id=str(risk_acceptance_version_id),
                risk_fitness_version_id=str(risk_fitness_version_id),
                integrator_actor_id=str(integrator_actor_id),
                owner_assignment_version_id=(
                    str(owner_assignment_version_id) if owner_assignment_version_id else None
                ),
                accountable_mechanism=accountable_mechanism,
                status=status,
            )
        )
        for item in material_applicability_version_ids:
            self.connection.execute(
                insert(integration_material_applicability).values(
                    integration_version_id=str(version_id), applicability_version_id=str(item)
                )
            )
        for item in authority_record_version_ids:
            self.connection.execute(
                insert(integration_authority_records).values(
                    integration_version_id=str(version_id), authority_version_id=str(item)
                )
            )
        for item in authority_gap_version_ids:
            self.connection.execute(
                insert(integration_authority_gaps).values(
                    integration_version_id=str(version_id), gap_version_id=str(item)
                )
            )

    def integration_detail(self, version_id: RecordVersionId) -> IntegrationDetail | None:
        row = (
            self.connection.execute(
                select(integration_versions).where(
                    integration_versions.c.version_id == str(version_id)
                )
            )
            .mappings()
            .first()
        )
        if row is None:
            return None
        return IntegrationDetail(
            RecordId.parse(cast("str", row["integration_id"])),
            version_id,
            RecordId.parse(cast("str", row["case_id"])),
            RecordId.parse(cast("str", row["configuration_id"])),
            RecordVersionId.parse(cast("str", row["configuration_version_id"])),
            cast("str", row["use_context"]),
            cast("str", row["purpose"]),
            RecordVersionId.parse(cast("str", row["value_input_version_id"])),
            RecordVersionId.parse(cast("str", row["value_acceptance_version_id"])),
            RecordVersionId.parse(cast("str", row["value_fitness_version_id"])),
            RecordVersionId.parse(cast("str", row["risk_input_version_id"])),
            RecordVersionId.parse(cast("str", row["risk_acceptance_version_id"])),
            RecordVersionId.parse(cast("str", row["risk_fitness_version_id"])),
            IntegrationStatus(cast("str", row["status"])),
        )

    def integration_versions_for_context(
        self, *, case_id: RecordId, configuration_version_id: RecordVersionId
    ) -> tuple[RecordVersionId, ...]:
        rows = (
            self.connection.execute(
                select(integration_versions.c.version_id).where(
                    integration_versions.c.case_id == str(case_id),
                    integration_versions.c.configuration_version_id
                    == str(configuration_version_id),
                )
            )
            .scalars()
            .all()
        )
        return tuple(RecordVersionId.parse(cast("str", item)) for item in rows)

    def add_uncertainty_classification(
        self,
        *,
        classification_id: RecordId,
        version_id: RecordVersionId,
        integration_version_id: RecordVersionId,
        proposed_decision_context: str,
        proposed_operating_state: str,
        source_reference: str,
        source_input_version_id: RecordVersionId | None,
        source_evidence_version_id: RecordVersionId | None,
        classification: str,
        accountable_assignment_version_id: RecordVersionId | None,
        accountable_mechanism: str | None,
    ) -> None:
        if not self._identity_exists(
            uncertainty_classification_records,
            uncertainty_classification_records.c.classification_id,
            str(classification_id),
        ):
            self.connection.execute(
                insert(uncertainty_classification_records).values(
                    classification_id=str(classification_id)
                )
            )
        self.connection.execute(
            insert(uncertainty_classification_versions).values(
                version_id=str(version_id),
                classification_id=str(classification_id),
                integration_version_id=str(integration_version_id),
                proposed_decision_context=proposed_decision_context,
                proposed_operating_state=proposed_operating_state,
                source_reference=source_reference,
                source_input_version_id=(
                    str(source_input_version_id) if source_input_version_id else None
                ),
                source_evidence_version_id=(
                    str(source_evidence_version_id) if source_evidence_version_id else None
                ),
                classification=classification,
                accountable_assignment_version_id=(
                    str(accountable_assignment_version_id)
                    if accountable_assignment_version_id
                    else None
                ),
                accountable_mechanism=accountable_mechanism,
            )
        )

    def add_boundary_snapshot(
        self,
        *,
        snapshot_id: RecordId,
        version_id: RecordVersionId,
        case_id: RecordId,
        configuration_id: RecordId,
        configuration_version_id: RecordVersionId,
        integration_id: RecordId,
        integration_version_id: RecordVersionId,
        owner_actor_id: RecordId,
        status: str,
        clauses: tuple[BoundaryClauseInput, ...],
        recorded_at: datetime,
        effective_at: datetime,
    ) -> None:
        if not self._identity_exists(
            boundary_snapshot_records, boundary_snapshot_records.c.snapshot_id, str(snapshot_id)
        ):
            self.connection.execute(
                insert(boundary_snapshot_records).values(snapshot_id=str(snapshot_id))
            )
        self.connection.execute(
            insert(boundary_snapshot_versions).values(
                version_id=str(version_id),
                snapshot_id=str(snapshot_id),
                case_id=str(case_id),
                configuration_id=str(configuration_id),
                configuration_version_id=str(configuration_version_id),
                integration_id=str(integration_id),
                integration_version_id=str(integration_version_id),
                owner_actor_id=str(owner_actor_id),
                status=status,
            )
        )
        for clause in clauses:
            clause_scope = f"boundary-snapshot-version:{version_id}:clause:{clause.clause_id}"
            clause_version = FinalizedRecordVersion(
                record_id=clause.clause_id,
                version_id=clause.clause_version_id,
                family="boundary-clause",
                scope=clause_scope,
                content_json=json.dumps(
                    {
                        "clause_type": clause.clause_type,
                        "effect": clause.effect.value,
                        "target_reference": clause.target_reference,
                        "structured_reference": clause.structured_reference,
                        "operator": clause.operator,
                        "value": clause.value,
                        "unit": clause.unit,
                        "narrative": clause.narrative,
                        "rationale": clause.rationale,
                        "provenance": clause.provenance,
                        "verification_mode": clause.verification_mode.value,
                        "breach_consequence": clause.breach_consequence,
                    }
                ),
                recorded_at=recorded_at,
                effective=EffectiveInterval(effective_at),
                creator=str(owner_actor_id),
            )
            self.add_version(clause_version)
            if not self._identity_exists(
                boundary_clause_records, boundary_clause_records.c.clause_id, str(clause.clause_id)
            ):
                self.connection.execute(
                    insert(boundary_clause_records).values(clause_id=str(clause.clause_id))
                )
            self.connection.execute(
                insert(boundary_clause_versions).values(
                    clause_version_id=str(clause.clause_version_id),
                    clause_id=str(clause.clause_id),
                    snapshot_version_id=str(version_id),
                    clause_type=clause.clause_type,
                    effect=clause.effect.value,
                    target_reference=clause.target_reference,
                    structured_reference=clause.structured_reference,
                    operator=clause.operator,
                    structured_value=clause.value,
                    unit=clause.unit,
                    narrative=clause.narrative,
                    verification_mode=clause.verification_mode.value,
                )
            )
            if clause.predecessor_clause_version_id is not None:
                relationship = VersionRelationship(
                    RelationshipId.new(),
                    clause.predecessor_clause_version_id,
                    clause.clause_version_id,
                    RelationshipType.AMENDMENT,
                    recorded_at,
                    clause.relationship_reason or "Boundary clause successor",
                )
                self.add_relationship(relationship)
                self.add_status_event(
                    StatusEvent(
                        EventId.new(),
                        clause.predecessor_clause_version_id,
                        "finalized",
                        "superseded",
                        recorded_at,
                        effective_at,
                        str(owner_actor_id),
                        relationship.reason,
                    )
                )

    def boundary_snapshot_detail(
        self, version_id: RecordVersionId
    ) -> BoundarySnapshotDetail | None:
        row = (
            self.connection.execute(
                select(boundary_snapshot_versions).where(
                    boundary_snapshot_versions.c.version_id == str(version_id)
                )
            )
            .mappings()
            .first()
        )
        if row is None:
            return None
        clause_rows = (
            self.connection.execute(
                select(boundary_clause_versions).where(
                    boundary_clause_versions.c.snapshot_version_id == str(version_id)
                )
            )
            .mappings()
            .all()
        )
        clauses = tuple(
            BoundaryClauseDetail(
                RecordId.parse(cast("str", item["clause_id"])),
                RecordVersionId.parse(cast("str", item["clause_version_id"])),
                cast("str", item["clause_type"]),
                BoundaryClauseEffect(cast("str", item["effect"])),
                cast("str | None", item["target_reference"]),
                cast("str | None", item["structured_reference"]),
                cast("str | None", item["operator"]),
                cast("str | None", item["structured_value"]),
                cast("str | None", item["unit"]),
                cast("str", item["narrative"]),
                BoundaryVerificationMode(cast("str", item["verification_mode"])),
            )
            for item in clause_rows
        )
        return BoundarySnapshotDetail(
            RecordId.parse(cast("str", row["snapshot_id"])),
            version_id,
            RecordId.parse(cast("str", row["case_id"])),
            RecordId.parse(cast("str", row["configuration_id"])),
            RecordVersionId.parse(cast("str", row["configuration_version_id"])),
            RecordId.parse(cast("str", row["integration_id"])),
            RecordVersionId.parse(cast("str", row["integration_version_id"])),
            cast("str", row["status"]),
            clauses,
        )

    def add_boundary_determination(
        self,
        *,
        determination_id: RecordId,
        version_id: RecordVersionId,
        snapshot_version_id: RecordVersionId,
        clause_id: RecordId,
        clause_version_id: RecordVersionId,
        outcome: str,
        actor_id: RecordId,
        accountable_assignment_version_id: RecordVersionId | None,
        accountable_mechanism: str | None,
        evidence_version_ids: tuple[RecordVersionId, ...],
    ) -> None:
        if not self._identity_exists(
            boundary_determination_records,
            boundary_determination_records.c.determination_id,
            str(determination_id),
        ):
            self.connection.execute(
                insert(boundary_determination_records).values(
                    determination_id=str(determination_id)
                )
            )
        self.connection.execute(
            insert(boundary_determination_versions).values(
                version_id=str(version_id),
                determination_id=str(determination_id),
                snapshot_version_id=str(snapshot_version_id),
                clause_id=str(clause_id),
                clause_version_id=str(clause_version_id),
                outcome=outcome,
                actor_id=str(actor_id),
                accountable_assignment_version_id=(
                    str(accountable_assignment_version_id)
                    if accountable_assignment_version_id
                    else None
                ),
                accountable_mechanism=accountable_mechanism,
            )
        )
        for evidence_id in evidence_version_ids:
            self.connection.execute(
                insert(boundary_determination_evidence).values(
                    determination_version_id=str(version_id), evidence_version_id=str(evidence_id)
                )
            )

    def current_boundary_determination(
        self,
        *,
        snapshot_version_id: RecordVersionId,
        clause_version_id: RecordVersionId,
        effective_at: datetime,
        known_at: datetime,
    ) -> tuple[RecordVersionId, str] | None:
        rows = (
            self.connection.execute(
                select(
                    boundary_determination_versions.c.version_id,
                    boundary_determination_versions.c.determination_id,
                    boundary_determination_versions.c.outcome,
                ).where(
                    boundary_determination_versions.c.snapshot_version_id
                    == str(snapshot_version_id),
                    boundary_determination_versions.c.clause_version_id == str(clause_version_id),
                )
            )
            .mappings()
            .all()
        )
        found: list[tuple[RecordVersionId, str]] = []
        for row in rows:
            record_id = RecordId.parse(cast("str", row["determination_id"]))
            history = self.get_history(record_id)
            if not history.versions:
                continue
            exemplar = next(iter(history.versions))
            current = self.select_current(
                SelectionQuery(
                    family="boundary-determination",
                    scope=exemplar.scope,
                    effective_at=effective_at,
                    known_at=known_at,
                    record_id=record_id,
                )
            )
            candidate_id = RecordVersionId.parse(cast("str", row["version_id"]))
            if isinstance(current, SelectionFound) and current.candidate.version_id == candidate_id:
                found.append((candidate_id, cast("str", row["outcome"])))
        return found[0] if len(found) == 1 else None

    def add_decision(
        self,
        *,
        decision_id: RecordId,
        version_id: RecordVersionId,
        case_id: RecordId,
        configuration_id: RecordId,
        configuration_version_id: RecordVersionId,
        integration_id: RecordId,
        integration_version_id: RecordVersionId,
        boundary_snapshot_id: RecordId,
        boundary_snapshot_version_id: RecordVersionId,
        proposed_action: str,
        operating_state: str,
        status: str,
        accepted_uncertainty_version_ids: tuple[RecordVersionId, ...],
        decision_limiting_uncertainty_version_ids: tuple[RecordVersionId, ...],
        authority_record_version_ids: tuple[RecordVersionId, ...],
        authority_gap_version_ids: tuple[RecordVersionId, ...],
    ) -> None:
        if not self._identity_exists(
            decision_records, decision_records.c.decision_id, str(decision_id)
        ):
            self.connection.execute(insert(decision_records).values(decision_id=str(decision_id)))
        self.connection.execute(
            insert(decision_versions).values(
                version_id=str(version_id),
                decision_id=str(decision_id),
                case_id=str(case_id),
                configuration_id=str(configuration_id),
                configuration_version_id=str(configuration_version_id),
                integration_id=str(integration_id),
                integration_version_id=str(integration_version_id),
                boundary_snapshot_id=str(boundary_snapshot_id),
                boundary_snapshot_version_id=str(boundary_snapshot_version_id),
                proposed_action=proposed_action,
                operating_state=operating_state,
                status=status,
            )
        )
        for classification_id in accepted_uncertainty_version_ids:
            self.connection.execute(
                insert(decision_uncertainty_links).values(
                    decision_version_id=str(version_id),
                    classification_version_id=str(classification_id),
                    classification="ACCEPTED_UNCERTAINTY",
                )
            )
        for classification_id in decision_limiting_uncertainty_version_ids:
            self.connection.execute(
                insert(decision_uncertainty_links).values(
                    decision_version_id=str(version_id),
                    classification_version_id=str(classification_id),
                    classification="DECISION_LIMITING_UNCERTAINTY",
                )
            )
        for authority_id in authority_record_version_ids:
            self.connection.execute(
                insert(decision_authority_records).values(
                    decision_version_id=str(version_id), authority_version_id=str(authority_id)
                )
            )
        for gap_id in authority_gap_version_ids:
            self.connection.execute(
                insert(decision_authority_gaps).values(
                    decision_version_id=str(version_id), gap_version_id=str(gap_id)
                )
            )

    def decision_detail(self, version_id: RecordVersionId) -> DecisionDetail | None:
        row = (
            self.connection.execute(
                select(decision_versions).where(decision_versions.c.version_id == str(version_id))
            )
            .mappings()
            .first()
        )
        if row is None:
            return None
        return DecisionDetail(
            RecordId.parse(cast("str", row["decision_id"])),
            version_id,
            RecordId.parse(cast("str", row["case_id"])),
            RecordId.parse(cast("str", row["configuration_id"])),
            RecordVersionId.parse(cast("str", row["configuration_version_id"])),
            RecordId.parse(cast("str", row["integration_id"])),
            RecordVersionId.parse(cast("str", row["integration_version_id"])),
            RecordId.parse(cast("str", row["boundary_snapshot_id"])),
            RecordVersionId.parse(cast("str", row["boundary_snapshot_version_id"])),
            cast("str", row["proposed_action"]),
            cast("str", row["operating_state"]),
            DecisionStatus(cast("str", row["status"])),
        )

    def decision_versions(
        self, *, case_id: RecordId, configuration_version_id: RecordVersionId
    ) -> tuple[RecordVersionId, ...]:
        rows = (
            self.connection.execute(
                select(decision_versions.c.version_id).where(
                    decision_versions.c.case_id == str(case_id),
                    decision_versions.c.configuration_version_id == str(configuration_version_id),
                )
            )
            .scalars()
            .all()
        )
        return tuple(RecordVersionId.parse(cast("str", row)) for row in rows)

    def add_bounded_proceed(
        self,
        *,
        determination_id: RecordId,
        version_id: RecordVersionId,
        decision_version_id: RecordVersionId,
        unresolved_gap_version_id: RecordVersionId,
        blocked_broader_decision: str,
        narrower_scope: str,
        boundary_clause_version_ids: tuple[RecordVersionId, ...],
        operating_state: str,
        actor_id: RecordId,
        authority_assignment_version_id: RecordVersionId | None,
        authority_mechanism: str | None,
        authority_record_version_id: RecordVersionId | None,
        delegation_chain_version_ids: tuple[RecordVersionId, ...],
    ) -> None:
        if not self._identity_exists(
            bounded_proceed_records,
            bounded_proceed_records.c.determination_id,
            str(determination_id),
        ):
            self.connection.execute(
                insert(bounded_proceed_records).values(determination_id=str(determination_id))
            )
        self.connection.execute(
            insert(bounded_proceed_versions).values(
                version_id=str(version_id),
                determination_id=str(determination_id),
                decision_version_id=str(decision_version_id),
                unresolved_gap_version_id=str(unresolved_gap_version_id),
                blocked_broader_decision=blocked_broader_decision,
                narrower_scope=narrower_scope,
                operating_state=operating_state,
                actor_id=str(actor_id),
                authority_assignment_version_id=(
                    str(authority_assignment_version_id)
                    if authority_assignment_version_id
                    else None
                ),
                authority_mechanism=authority_mechanism,
                authority_record_version_id=(
                    str(authority_record_version_id) if authority_record_version_id else None
                ),
            )
        )
        for ordinal, assignment_id in enumerate(delegation_chain_version_ids):
            self.connection.execute(
                insert(bounded_proceed_delegations).values(
                    bounded_proceed_version_id=str(version_id),
                    ordinal=ordinal,
                    assignment_version_id=str(assignment_id),
                )
            )
        for clause_id in boundary_clause_version_ids:
            self.connection.execute(
                insert(bounded_proceed_boundary_clauses).values(
                    bounded_proceed_version_id=str(version_id), clause_version_id=str(clause_id)
                )
            )

    def bounded_proceed_detail(self, version_id: RecordVersionId) -> dict[str, str] | None:
        row = (
            self.connection.execute(
                select(bounded_proceed_versions).where(
                    bounded_proceed_versions.c.version_id == str(version_id)
                )
            )
            .mappings()
            .first()
        )
        if row is None:
            return None
        return {
            key: cast("str", row[key])
            for key in (
                "decision_version_id",
                "unresolved_gap_version_id",
                "narrower_scope",
                "operating_state",
                "actor_id",
            )
        }

    def add_authorization_basis(
        self,
        *,
        basis_id: RecordId,
        version_id: RecordVersionId,
        decision_version_id: RecordVersionId,
        decision_authority_identity: str,
        authority_assignment_version_id: RecordVersionId | None,
        authority_mechanism: str | None,
        authority_record_version_id: RecordVersionId | None,
        delegation_chain_version_ids: tuple[RecordVersionId, ...],
        authorized_scope: str,
        configuration_id: RecordId,
        configuration_version_id: RecordVersionId,
        operating_state_coverage: tuple[str, ...],
        decision_type: str,
        organizational_unit: str | None,
        authorization_event_id: str,
        authorization_actor_id: RecordId,
        authorization_effective_at: datetime,
        authority_gap_version_ids: tuple[RecordVersionId, ...],
        bounded_proceed_version_id: RecordVersionId | None,
        preauthorized_activation_mechanisms: tuple[PreauthorizedActivationMechanismInput, ...],
    ) -> None:
        if not self._identity_exists(
            decision_authorization_basis_records,
            decision_authorization_basis_records.c.basis_id,
            str(basis_id),
        ):
            self.connection.execute(
                insert(decision_authorization_basis_records).values(basis_id=str(basis_id))
            )
        self.connection.execute(
            insert(decision_authorization_basis_versions).values(
                version_id=str(version_id),
                basis_id=str(basis_id),
                decision_version_id=str(decision_version_id),
                decision_authority_identity=decision_authority_identity,
                authority_assignment_version_id=(
                    str(authority_assignment_version_id)
                    if authority_assignment_version_id
                    else None
                ),
                authority_mechanism=authority_mechanism,
                authority_record_version_id=(
                    str(authority_record_version_id) if authority_record_version_id else None
                ),
                authorized_scope=authorized_scope,
                configuration_id=str(configuration_id),
                configuration_version_id=str(configuration_version_id),
                operating_state_coverage_json=json.dumps(operating_state_coverage),
                decision_type=decision_type,
                organizational_unit=organizational_unit,
                authorization_event_id=authorization_event_id,
                authorization_actor_id=str(authorization_actor_id),
                authorization_effective_at_us=to_epoch_microseconds(authorization_effective_at),
                bounded_proceed_version_id=(
                    str(bounded_proceed_version_id) if bounded_proceed_version_id else None
                ),
            )
        )
        for ordinal, assignment_id in enumerate(delegation_chain_version_ids):
            self.connection.execute(
                insert(decision_authorization_delegations).values(
                    basis_version_id=str(version_id),
                    ordinal=ordinal,
                    assignment_version_id=str(assignment_id),
                )
            )
        for gap_id in authority_gap_version_ids:
            self.connection.execute(
                insert(decision_authorization_gaps).values(
                    basis_version_id=str(version_id), gap_version_id=str(gap_id)
                )
            )
        self.add_preauthorized_activation_mechanisms(
            basis_version_id=version_id,
            mechanisms=preauthorized_activation_mechanisms,
        )

    def add_preauthorized_activation_mechanisms(
        self,
        *,
        basis_version_id: RecordVersionId,
        mechanisms: tuple[PreauthorizedActivationMechanismInput, ...],
    ) -> None:
        for mechanism in mechanisms:
            self.connection.execute(
                insert(decision_preauthorized_activation_mechanisms).values(
                    mechanism_id=str(mechanism.mechanism_id),
                    mechanism_version_id=str(mechanism.mechanism_version_id),
                    basis_version_id=str(basis_version_id),
                    rule_version=mechanism.rule_version,
                    scope=mechanism.scope,
                    authority_source=mechanism.authority_source,
                    limits_json=json.dumps(mechanism.limits),
                    effective_from_us=to_epoch_microseconds(mechanism.effective.start),
                    effective_to_us=(
                        to_epoch_microseconds(mechanism.effective.end)
                        if mechanism.effective.end
                        else None
                    ),
                )
            )

    def preauthorized_activation_mechanism(
        self,
        *,
        basis_version_id: RecordVersionId,
        mechanism_version_id: RecordVersionId,
    ) -> dict[str, object] | None:
        row = (
            self.connection.execute(
                select(decision_preauthorized_activation_mechanisms).where(
                    decision_preauthorized_activation_mechanisms.c.basis_version_id
                    == str(basis_version_id),
                    decision_preauthorized_activation_mechanisms.c.mechanism_version_id
                    == str(mechanism_version_id),
                )
            )
            .mappings()
            .first()
        )
        return dict(row) if row is not None else None

    def authorization_basis_detail(
        self, version_id: RecordVersionId
    ) -> AuthorizationBasisDetail | None:
        row = (
            self.connection.execute(
                select(decision_authorization_basis_versions).where(
                    decision_authorization_basis_versions.c.version_id == str(version_id)
                )
            )
            .mappings()
            .first()
        )
        if row is None:
            return None
        return AuthorizationBasisDetail(
            RecordId.parse(cast("str", row["basis_id"])),
            version_id,
            RecordVersionId.parse(cast("str", row["decision_version_id"])),
            (
                RecordVersionId.parse(cast("str", row["authority_assignment_version_id"]))
                if row["authority_assignment_version_id"]
                else None
            ),
            cast("str | None", row["authority_mechanism"]),
            (
                RecordVersionId.parse(cast("str", row["authority_record_version_id"]))
                if row["authority_record_version_id"]
                else None
            ),
            cast("str", row["authorized_scope"]),
            RecordId.parse(cast("str", row["configuration_id"])),
            RecordVersionId.parse(cast("str", row["configuration_version_id"])),
            tuple(cast("list[str]", json.loads(cast("str", row["operating_state_coverage_json"])))),
            (
                RecordVersionId.parse(cast("str", row["bounded_proceed_version_id"]))
                if row["bounded_proceed_version_id"]
                else None
            ),
        )

    def authorization_basis_versions(
        self, *, decision_version_id: RecordVersionId
    ) -> tuple[RecordVersionId, ...]:
        rows = (
            self.connection.execute(
                select(decision_authorization_basis_versions.c.version_id).where(
                    decision_authorization_basis_versions.c.decision_version_id
                    == str(decision_version_id)
                )
            )
            .scalars()
            .all()
        )
        return tuple(RecordVersionId.parse(cast("str", row)) for row in rows)

    def authority_record_scope(self, version_id: RecordVersionId) -> str | None:
        row = self.connection.execute(
            select(authority_record_versions.c.authority_scope).where(
                authority_record_versions.c.version_id == str(version_id)
            )
        ).scalar_one_or_none()
        return cast("str | None", row)

    def add_intervention(
        self,
        *,
        intervention_id: RecordId,
        version_id: RecordVersionId,
        case_id: RecordId,
        decision_version_id: RecordVersionId,
        configuration_id: RecordId,
        configuration_version_id: RecordVersionId,
        owner_actor_id: RecordId,
        owner_assignment_version_id: RecordVersionId | None,
        accountable_mechanism: str | None,
        status: str,
    ) -> None:
        if not self._identity_exists(
            intervention_records, intervention_records.c.intervention_id, str(intervention_id)
        ):
            self.connection.execute(
                insert(intervention_records).values(intervention_id=str(intervention_id))
            )
        self.connection.execute(
            insert(intervention_versions).values(
                version_id=str(version_id),
                intervention_id=str(intervention_id),
                case_id=str(case_id),
                decision_version_id=str(decision_version_id),
                configuration_id=str(configuration_id),
                configuration_version_id=str(configuration_version_id),
                owner_actor_id=str(owner_actor_id),
                owner_assignment_version_id=(
                    str(owner_assignment_version_id) if owner_assignment_version_id else None
                ),
                accountable_mechanism=accountable_mechanism,
                status=status,
            )
        )

    def intervention_detail(self, version_id: RecordVersionId) -> InterventionDetail | None:
        row = (
            self.connection.execute(
                select(intervention_versions).where(
                    intervention_versions.c.version_id == str(version_id)
                )
            )
            .mappings()
            .first()
        )
        if row is None:
            return None
        return InterventionDetail(
            RecordId.parse(cast("str", row["intervention_id"])),
            version_id,
            RecordId.parse(cast("str", row["case_id"])),
            RecordVersionId.parse(cast("str", row["decision_version_id"])),
            RecordId.parse(cast("str", row["configuration_id"])),
            RecordVersionId.parse(cast("str", row["configuration_version_id"])),
            RecordId.parse(cast("str", row["owner_actor_id"])),
            InterventionStatus(cast("str", row["status"])),
        )

    def add_obligation_set(
        self,
        *,
        obligation_set_id: RecordId,
        version_id: RecordVersionId,
        decision_id: RecordId,
        decision_version_id: RecordVersionId,
        case_id: RecordId,
        configuration_id: RecordId,
        configuration_version_id: RecordVersionId,
    ) -> None:
        if not self._identity_exists(
            obligation_set_records,
            obligation_set_records.c.obligation_set_id,
            str(obligation_set_id),
        ):
            self.connection.execute(
                insert(obligation_set_records).values(obligation_set_id=str(obligation_set_id))
            )
        self.connection.execute(
            insert(obligation_set_versions).values(
                version_id=str(version_id),
                obligation_set_id=str(obligation_set_id),
                decision_id=str(decision_id),
                decision_version_id=str(decision_version_id),
                case_id=str(case_id),
                configuration_id=str(configuration_id),
                configuration_version_id=str(configuration_version_id),
            )
        )

    def add_obligation(
        self,
        *,
        obligation_id: RecordId,
        version_id: RecordVersionId,
        obligation_set_version_id: RecordVersionId,
        decision_version_id: RecordVersionId,
        configuration_version_id: RecordVersionId,
        intervention_id: RecordId,
        intervention_version_id: RecordVersionId,
        requirement_type: str,
        post_operation_permitted: bool,
        post_operation_timing_conditions: tuple[str, ...],
    ) -> None:
        if not self._identity_exists(
            obligation_records, obligation_records.c.obligation_id, str(obligation_id)
        ):
            self.connection.execute(
                insert(obligation_records).values(obligation_id=str(obligation_id))
            )
        self.connection.execute(
            insert(obligation_versions).values(
                version_id=str(version_id),
                obligation_id=str(obligation_id),
                obligation_set_version_id=str(obligation_set_version_id),
                decision_version_id=str(decision_version_id),
                configuration_version_id=str(configuration_version_id),
                intervention_id=str(intervention_id),
                intervention_version_id=str(intervention_version_id),
                requirement_type=requirement_type,
                post_operation_permitted=post_operation_permitted,
                post_operation_timing_conditions_json=json.dumps(post_operation_timing_conditions),
            )
        )

    def obligation_set_detail(self, version_id: RecordVersionId) -> ObligationSetDetail | None:
        row = (
            self.connection.execute(
                select(obligation_set_versions).where(
                    obligation_set_versions.c.version_id == str(version_id)
                )
            )
            .mappings()
            .first()
        )
        if row is None:
            return None
        obligations = self.connection.execute(
            select(obligation_versions.c.version_id).where(
                obligation_versions.c.obligation_set_version_id == str(version_id)
            )
        ).scalars()
        return ObligationSetDetail(
            RecordId.parse(cast("str", row["obligation_set_id"])),
            version_id,
            RecordId.parse(cast("str", row["decision_id"])),
            RecordVersionId.parse(cast("str", row["decision_version_id"])),
            RecordId.parse(cast("str", row["case_id"])),
            RecordId.parse(cast("str", row["configuration_id"])),
            RecordVersionId.parse(cast("str", row["configuration_version_id"])),
            tuple(RecordVersionId.parse(cast("str", item)) for item in obligations),
        )

    def obligation_set_versions(
        self,
        *,
        decision_version_id: RecordVersionId,
        configuration_version_id: RecordVersionId,
    ) -> tuple[RecordVersionId, ...]:
        rows = self.connection.execute(
            select(obligation_set_versions.c.version_id).where(
                obligation_set_versions.c.decision_version_id == str(decision_version_id),
                obligation_set_versions.c.configuration_version_id == str(configuration_version_id),
            )
        ).scalars()
        return tuple(RecordVersionId.parse(cast("str", item)) for item in rows)

    def obligation_detail(self, version_id: RecordVersionId) -> ObligationDetail | None:
        row = (
            self.connection.execute(
                select(obligation_versions).where(
                    obligation_versions.c.version_id == str(version_id)
                )
            )
            .mappings()
            .first()
        )
        if row is None:
            return None
        return ObligationDetail(
            RecordId.parse(cast("str", row["obligation_id"])),
            version_id,
            RecordVersionId.parse(cast("str", row["obligation_set_version_id"])),
            RecordVersionId.parse(cast("str", row["decision_version_id"])),
            RecordVersionId.parse(cast("str", row["configuration_version_id"])),
            RecordId.parse(cast("str", row["intervention_id"])),
            RecordVersionId.parse(cast("str", row["intervention_version_id"])),
            RequirementType(cast("str", row["requirement_type"])),
            bool(row["post_operation_permitted"]),
            tuple(
                cast(
                    "list[str]",
                    json.loads(cast("str", row["post_operation_timing_conditions_json"])),
                )
            ),
        )

    def add_completion_result(
        self,
        *,
        result_id: RecordId,
        version_id: RecordVersionId,
        obligation_version_id: RecordVersionId,
        intervention_version_id: RecordVersionId,
        decision_version_id: RecordVersionId,
        configuration_version_id: RecordVersionId,
        criteria: tuple[CompletionCriterionResult, ...],
        evidence_version_ids: tuple[RecordVersionId, ...],
        performer_actor_id: RecordId,
    ) -> None:
        if not self._identity_exists(
            completion_result_records, completion_result_records.c.result_id, str(result_id)
        ):
            self.connection.execute(
                insert(completion_result_records).values(result_id=str(result_id))
            )
        self.connection.execute(
            insert(completion_result_versions).values(
                version_id=str(version_id),
                result_id=str(result_id),
                obligation_version_id=str(obligation_version_id),
                intervention_version_id=str(intervention_version_id),
                decision_version_id=str(decision_version_id),
                configuration_version_id=str(configuration_version_id),
                performer_actor_id=str(performer_actor_id),
            )
        )
        for ordinal, criterion in enumerate(criteria):
            self.connection.execute(
                insert(completion_result_criteria).values(
                    result_version_id=str(version_id),
                    ordinal=ordinal,
                    criterion=criterion.criterion,
                    outcome=criterion.outcome.value,
                    rationale=criterion.rationale,
                )
            )
        for evidence_id in evidence_version_ids:
            self.connection.execute(
                insert(completion_result_evidence).values(
                    result_version_id=str(version_id), evidence_version_id=str(evidence_id)
                )
            )

    def completion_result_detail(
        self, version_id: RecordVersionId
    ) -> CompletionResultDetail | None:
        row = (
            self.connection.execute(
                select(completion_result_versions).where(
                    completion_result_versions.c.version_id == str(version_id)
                )
            )
            .mappings()
            .first()
        )
        if row is None:
            return None
        criteria_rows = (
            self.connection.execute(
                select(completion_result_criteria)
                .where(completion_result_criteria.c.result_version_id == str(version_id))
                .order_by(completion_result_criteria.c.ordinal)
            )
            .mappings()
            .all()
        )
        evidence_rows = self.connection.execute(
            select(completion_result_evidence.c.evidence_version_id).where(
                completion_result_evidence.c.result_version_id == str(version_id)
            )
        ).scalars()
        return CompletionResultDetail(
            RecordId.parse(cast("str", row["result_id"])),
            version_id,
            RecordVersionId.parse(cast("str", row["obligation_version_id"])),
            RecordVersionId.parse(cast("str", row["intervention_version_id"])),
            RecordVersionId.parse(cast("str", row["decision_version_id"])),
            RecordVersionId.parse(cast("str", row["configuration_version_id"])),
            tuple(
                CompletionCriterionResult(
                    cast("str", item["criterion"]),
                    CriterionOutcome(cast("str", item["outcome"])),
                    cast("str", item["rationale"]),
                )
                for item in criteria_rows
            ),
            tuple(RecordVersionId.parse(cast("str", item)) for item in evidence_rows),
        )

    def completion_result_versions(
        self, *, obligation_version_id: RecordVersionId
    ) -> tuple[RecordVersionId, ...]:
        rows = self.connection.execute(
            select(completion_result_versions.c.version_id).where(
                completion_result_versions.c.obligation_version_id == str(obligation_version_id)
            )
        ).scalars()
        return tuple(RecordVersionId.parse(cast("str", item)) for item in rows)

    def add_completion_acceptor_mechanism(
        self,
        *,
        mechanism_id: RecordId,
        version_id: RecordVersionId,
        case_id: RecordId,
        intervention_id: RecordId,
        intervention_version_id: RecordVersionId,
        decision_version_id: RecordVersionId,
        configuration_id: RecordId,
        configuration_version_id: RecordVersionId,
        accountable_actor_id: RecordId,
        rule_version: str,
        authority_scope: str,
        authority_source: str,
    ) -> None:
        if not self._identity_exists(
            completion_acceptor_mechanism_records,
            completion_acceptor_mechanism_records.c.mechanism_id,
            str(mechanism_id),
        ):
            self.connection.execute(
                insert(completion_acceptor_mechanism_records).values(mechanism_id=str(mechanism_id))
            )
        self.connection.execute(
            insert(completion_acceptor_mechanism_versions).values(
                version_id=str(version_id),
                mechanism_id=str(mechanism_id),
                case_id=str(case_id),
                intervention_id=str(intervention_id),
                intervention_version_id=str(intervention_version_id),
                decision_version_id=str(decision_version_id),
                configuration_id=str(configuration_id),
                configuration_version_id=str(configuration_version_id),
                accountable_actor_id=str(accountable_actor_id),
                rule_version=rule_version,
                authority_scope=authority_scope,
                authority_source=authority_source,
            )
        )

    def completion_acceptor_mechanism_detail(
        self, version_id: RecordVersionId
    ) -> dict[str, object] | None:
        row = (
            self.connection.execute(
                select(completion_acceptor_mechanism_versions).where(
                    completion_acceptor_mechanism_versions.c.version_id == str(version_id)
                )
            )
            .mappings()
            .first()
        )
        return dict(row) if row is not None else None

    def completion_acceptor_mechanism_versions(
        self,
        *,
        case_id: RecordId,
        intervention_id: RecordId,
        decision_version_id: RecordVersionId,
        configuration_id: RecordId,
        configuration_version_id: RecordVersionId,
    ) -> tuple[RecordVersionId, ...]:
        rows = self.connection.execute(
            select(completion_acceptor_mechanism_versions.c.version_id).where(
                completion_acceptor_mechanism_versions.c.case_id == str(case_id),
                completion_acceptor_mechanism_versions.c.intervention_id == str(intervention_id),
                completion_acceptor_mechanism_versions.c.decision_version_id
                == str(decision_version_id),
                completion_acceptor_mechanism_versions.c.configuration_id == str(configuration_id),
                completion_acceptor_mechanism_versions.c.configuration_version_id
                == str(configuration_version_id),
            )
        ).scalars()
        return tuple(RecordVersionId.parse(cast("str", item)) for item in rows)

    def add_completion_acceptance(
        self,
        *,
        acceptance_id: RecordId,
        version_id: RecordVersionId,
        obligation_version_id: RecordVersionId,
        intervention_version_id: RecordVersionId,
        completion_result_version_id: RecordVersionId,
        decision_version_id: RecordVersionId,
        configuration_version_id: RecordVersionId,
        outcome: str,
        status: str,
        accountable_actor_id: RecordId,
        accountable_assignment_version_id: RecordVersionId | None,
        accountable_mechanism_version_id: RecordVersionId | None,
        delegation_chain_version_ids: tuple[RecordVersionId, ...],
    ) -> None:
        if not self._identity_exists(
            completion_acceptance_records,
            completion_acceptance_records.c.acceptance_id,
            str(acceptance_id),
        ):
            self.connection.execute(
                insert(completion_acceptance_records).values(acceptance_id=str(acceptance_id))
            )
        self.connection.execute(
            insert(completion_acceptance_versions).values(
                version_id=str(version_id),
                acceptance_id=str(acceptance_id),
                obligation_version_id=str(obligation_version_id),
                intervention_version_id=str(intervention_version_id),
                completion_result_version_id=str(completion_result_version_id),
                decision_version_id=str(decision_version_id),
                configuration_version_id=str(configuration_version_id),
                outcome=outcome,
                status=status,
                accountable_actor_id=str(accountable_actor_id),
                accountable_assignment_version_id=(
                    str(accountable_assignment_version_id)
                    if accountable_assignment_version_id
                    else None
                ),
                accountable_mechanism_version_id=(
                    str(accountable_mechanism_version_id)
                    if accountable_mechanism_version_id
                    else None
                ),
            )
        )
        for ordinal, assignment_id in enumerate(delegation_chain_version_ids):
            self.connection.execute(
                insert(completion_acceptance_delegations).values(
                    acceptance_version_id=str(version_id),
                    ordinal=ordinal,
                    assignment_version_id=str(assignment_id),
                )
            )

    def completion_acceptance_detail(
        self, version_id: RecordVersionId
    ) -> CompletionAcceptanceDetail | None:
        row = (
            self.connection.execute(
                select(completion_acceptance_versions).where(
                    completion_acceptance_versions.c.version_id == str(version_id)
                )
            )
            .mappings()
            .first()
        )
        if row is None:
            return None
        return CompletionAcceptanceDetail(
            RecordId.parse(cast("str", row["acceptance_id"])),
            version_id,
            RecordVersionId.parse(cast("str", row["obligation_version_id"])),
            RecordVersionId.parse(cast("str", row["intervention_version_id"])),
            RecordVersionId.parse(cast("str", row["completion_result_version_id"])),
            RecordVersionId.parse(cast("str", row["decision_version_id"])),
            RecordVersionId.parse(cast("str", row["configuration_version_id"])),
            CompletionAcceptanceOutcome(cast("str", row["outcome"])),
            RecordId.parse(cast("str", row["accountable_actor_id"])),
            (
                RecordVersionId.parse(cast("str", row["accountable_assignment_version_id"]))
                if row["accountable_assignment_version_id"]
                else None
            ),
            (
                RecordVersionId.parse(cast("str", row["accountable_mechanism_version_id"]))
                if row["accountable_mechanism_version_id"]
                else None
            ),
            CompletionAcceptanceStatus(cast("str", row["status"])),
        )

    def completion_acceptance_versions(
        self, *, obligation_version_id: RecordVersionId
    ) -> tuple[RecordVersionId, ...]:
        rows = self.connection.execute(
            select(completion_acceptance_versions.c.version_id).where(
                completion_acceptance_versions.c.obligation_version_id == str(obligation_version_id)
            )
        ).scalars()
        return tuple(RecordVersionId.parse(cast("str", item)) for item in rows)

    def add_replacement(
        self,
        *,
        replacement_id: RecordId,
        version_id: RecordVersionId,
        obligation_version_id: RecordVersionId,
        predecessor_intervention_version_id: RecordVersionId,
        replacement_intervention_version_id: RecordVersionId,
        substantive_change: bool,
        successor_decision_version_id: RecordVersionId | None,
    ) -> None:
        if not self._identity_exists(
            intervention_replacement_records,
            intervention_replacement_records.c.replacement_id,
            str(replacement_id),
        ):
            self.connection.execute(
                insert(intervention_replacement_records).values(replacement_id=str(replacement_id))
            )
        self.connection.execute(
            insert(intervention_replacement_versions).values(
                version_id=str(version_id),
                replacement_id=str(replacement_id),
                obligation_version_id=str(obligation_version_id),
                predecessor_intervention_version_id=str(predecessor_intervention_version_id),
                replacement_intervention_version_id=str(replacement_intervention_version_id),
                substantive_change=substantive_change,
                successor_decision_version_id=(
                    str(successor_decision_version_id) if successor_decision_version_id else None
                ),
            )
        )

    def replacement_versions(
        self, *, obligation_version_id: RecordVersionId
    ) -> tuple[RecordVersionId, ...]:
        rows = self.connection.execute(
            select(intervention_replacement_versions.c.version_id).where(
                intervention_replacement_versions.c.obligation_version_id
                == str(obligation_version_id)
            )
        ).scalars()
        return tuple(RecordVersionId.parse(cast("str", item)) for item in rows)

    def replacement_detail(self, version_id: RecordVersionId) -> dict[str, object] | None:
        row = (
            self.connection.execute(
                select(intervention_replacement_versions).where(
                    intervention_replacement_versions.c.version_id == str(version_id)
                )
            )
            .mappings()
            .first()
        )
        return dict(row) if row is not None else None

    def add_continued_validity_mechanism(
        self,
        *,
        mechanism_id: RecordId,
        version_id: RecordVersionId,
        successor_obligation_version_id: RecordVersionId,
        case_id: RecordId,
        intervention_id: RecordId,
        intervention_version_id: RecordVersionId,
        decision_version_id: RecordVersionId,
        configuration_id: RecordId,
        configuration_version_id: RecordVersionId,
        accountable_actor_id: RecordId,
        rule_version: str,
        authority_scope: str,
        authority_source: str,
    ) -> None:
        if not self._identity_exists(
            continued_validity_mechanism_records,
            continued_validity_mechanism_records.c.mechanism_id,
            str(mechanism_id),
        ):
            self.connection.execute(
                insert(continued_validity_mechanism_records).values(mechanism_id=str(mechanism_id))
            )
        self.connection.execute(
            insert(continued_validity_mechanism_versions).values(
                version_id=str(version_id),
                mechanism_id=str(mechanism_id),
                successor_obligation_version_id=str(successor_obligation_version_id),
                case_id=str(case_id),
                intervention_id=str(intervention_id),
                intervention_version_id=str(intervention_version_id),
                decision_version_id=str(decision_version_id),
                configuration_id=str(configuration_id),
                configuration_version_id=str(configuration_version_id),
                accountable_actor_id=str(accountable_actor_id),
                rule_version=rule_version,
                authority_scope=authority_scope,
                authority_source=authority_source,
            )
        )

    def continued_validity_mechanism_detail(
        self, version_id: RecordVersionId
    ) -> dict[str, object] | None:
        row = (
            self.connection.execute(
                select(continued_validity_mechanism_versions).where(
                    continued_validity_mechanism_versions.c.version_id == str(version_id)
                )
            )
            .mappings()
            .first()
        )
        return dict(row) if row is not None else None

    def continued_validity_mechanism_versions(
        self, *, successor_obligation_version_id: RecordVersionId
    ) -> tuple[RecordVersionId, ...]:
        rows = self.connection.execute(
            select(continued_validity_mechanism_versions.c.version_id).where(
                continued_validity_mechanism_versions.c.successor_obligation_version_id
                == str(successor_obligation_version_id)
            )
        ).scalars()
        return tuple(RecordVersionId.parse(cast("str", item)) for item in rows)

    def add_reuse_determination(
        self,
        *,
        determination_id: RecordId,
        version_id: RecordVersionId,
        successor_obligation_version_id: RecordVersionId,
        prior_completion_result_version_id: RecordVersionId,
        prior_acceptance_version_id: RecordVersionId,
        accountable_actor_id: RecordId,
        accountable_assignment_version_id: RecordVersionId | None,
        accountable_mechanism_version_id: RecordVersionId | None,
        delegation_chain_version_ids: tuple[RecordVersionId, ...],
        all_coverage_established: bool,
    ) -> None:
        if not self._identity_exists(
            continued_validity_records,
            continued_validity_records.c.determination_id,
            str(determination_id),
        ):
            self.connection.execute(
                insert(continued_validity_records).values(determination_id=str(determination_id))
            )
        self.connection.execute(
            insert(continued_validity_versions).values(
                version_id=str(version_id),
                determination_id=str(determination_id),
                successor_obligation_version_id=str(successor_obligation_version_id),
                prior_completion_result_version_id=str(prior_completion_result_version_id),
                prior_acceptance_version_id=str(prior_acceptance_version_id),
                accountable_actor_id=str(accountable_actor_id),
                accountable_assignment_version_id=(
                    str(accountable_assignment_version_id)
                    if accountable_assignment_version_id
                    else None
                ),
                accountable_mechanism_version_id=(
                    str(accountable_mechanism_version_id)
                    if accountable_mechanism_version_id
                    else None
                ),
                all_coverage_established=all_coverage_established,
            )
        )
        for ordinal, assignment_id in enumerate(delegation_chain_version_ids):
            self.connection.execute(
                insert(continued_validity_delegations).values(
                    determination_version_id=str(version_id),
                    ordinal=ordinal,
                    assignment_version_id=str(assignment_id),
                )
            )

    def reuse_determination_versions(
        self, *, successor_obligation_version_id: RecordVersionId
    ) -> tuple[RecordVersionId, ...]:
        rows = self.connection.execute(
            select(continued_validity_versions.c.version_id).where(
                continued_validity_versions.c.successor_obligation_version_id
                == str(successor_obligation_version_id)
            )
        ).scalars()
        return tuple(RecordVersionId.parse(cast("str", item)) for item in rows)

    def reuse_determination_detail(self, version_id: RecordVersionId) -> dict[str, object] | None:
        row = (
            self.connection.execute(
                select(continued_validity_versions).where(
                    continued_validity_versions.c.version_id == str(version_id)
                )
            )
            .mappings()
            .first()
        )
        return dict(row) if row is not None else None

    def add_prerequisite_evaluation_basis(
        self,
        *,
        basis_id: RecordId,
        version_id: RecordVersionId,
        decision_version_id: RecordVersionId,
        configuration_version_id: RecordVersionId,
        boundary_snapshot_version_id: RecordVersionId,
        obligation_set_version_id: RecordVersionId,
        aggregate_result: str,
        effective_at: datetime,
        knowledge_cutoff: datetime,
    ) -> None:
        if not self._identity_exists(
            prerequisite_evaluation_basis_records,
            prerequisite_evaluation_basis_records.c.basis_id,
            str(basis_id),
        ):
            self.connection.execute(
                insert(prerequisite_evaluation_basis_records).values(basis_id=str(basis_id))
            )
        self.connection.execute(
            insert(prerequisite_evaluation_basis_versions).values(
                version_id=str(version_id),
                basis_id=str(basis_id),
                decision_version_id=str(decision_version_id),
                configuration_version_id=str(configuration_version_id),
                boundary_snapshot_version_id=str(boundary_snapshot_version_id),
                obligation_set_version_id=str(obligation_set_version_id),
                aggregate_result=aggregate_result,
                effective_at_us=to_epoch_microseconds(effective_at),
                knowledge_cutoff_us=to_epoch_microseconds(knowledge_cutoff),
            )
        )

    def add_prerequisite_basis_item(
        self,
        *,
        basis_version_id: RecordVersionId,
        ordinal: int,
        obligation_version_id: RecordVersionId,
        intervention_version_id: RecordVersionId | None,
        completion_result_version_id: RecordVersionId | None,
        completion_acceptance_version_id: RecordVersionId | None,
        replacement_version_id: RecordVersionId | None,
        reuse_determination_version_id: RecordVersionId | None,
        result: str,
        diagnostics: tuple[str, ...],
    ) -> None:
        self.connection.execute(
            insert(prerequisite_evaluation_basis_items).values(
                basis_version_id=str(basis_version_id),
                ordinal=ordinal,
                obligation_version_id=str(obligation_version_id),
                intervention_version_id=(
                    str(intervention_version_id) if intervention_version_id else None
                ),
                completion_result_version_id=(
                    str(completion_result_version_id) if completion_result_version_id else None
                ),
                completion_acceptance_version_id=(
                    str(completion_acceptance_version_id)
                    if completion_acceptance_version_id
                    else None
                ),
                replacement_version_id=(
                    str(replacement_version_id) if replacement_version_id else None
                ),
                reuse_determination_version_id=(
                    str(reuse_determination_version_id) if reuse_determination_version_id else None
                ),
                result=result,
                diagnostics_json=json.dumps(diagnostics),
            )
        )

    def add_activation_authorization(
        self,
        *,
        authorization_id: RecordId,
        version_id: RecordVersionId,
        decision_version_id: RecordVersionId,
        configuration_version_id: RecordVersionId,
        operating_state: str,
        boundary_snapshot_version_id: RecordVersionId,
        prerequisite_basis_version_id: RecordVersionId,
        authority_kind: str,
        authority_actor_id: RecordId | None,
        authority_assignment_version_id: RecordVersionId | None,
        mechanism_version_id: RecordVersionId | None,
        decision_authorization_basis_version_id: RecordVersionId,
        authority_scope: str,
        authority_limits: tuple[str, ...],
        authority_effective_from: datetime,
        authority_effective_to: datetime | None,
        delegation_chain_version_ids: tuple[RecordVersionId, ...],
        activation_effective_at: datetime,
    ) -> None:
        if not self._identity_exists(
            activation_authorization_records,
            activation_authorization_records.c.authorization_id,
            str(authorization_id),
        ):
            self.connection.execute(
                insert(activation_authorization_records).values(
                    authorization_id=str(authorization_id)
                )
            )
        self.connection.execute(
            insert(activation_authorization_versions).values(
                version_id=str(version_id),
                authorization_id=str(authorization_id),
                decision_version_id=str(decision_version_id),
                configuration_version_id=str(configuration_version_id),
                operating_state=operating_state,
                boundary_snapshot_version_id=str(boundary_snapshot_version_id),
                prerequisite_basis_version_id=str(prerequisite_basis_version_id),
                authority_kind=authority_kind,
                authority_actor_id=str(authority_actor_id) if authority_actor_id else None,
                authority_assignment_version_id=(
                    str(authority_assignment_version_id)
                    if authority_assignment_version_id
                    else None
                ),
                mechanism_version_id=(str(mechanism_version_id) if mechanism_version_id else None),
                decision_authorization_basis_version_id=str(
                    decision_authorization_basis_version_id
                ),
                authority_scope=authority_scope,
                authority_limits_json=json.dumps(authority_limits),
                authority_effective_from_us=to_epoch_microseconds(authority_effective_from),
                authority_effective_to_us=(
                    to_epoch_microseconds(authority_effective_to)
                    if authority_effective_to
                    else None
                ),
                activation_effective_at_us=to_epoch_microseconds(activation_effective_at),
            )
        )
        for ordinal, assignment_id in enumerate(delegation_chain_version_ids):
            self.connection.execute(
                insert(activation_authorization_delegations).values(
                    authorization_version_id=str(version_id),
                    ordinal=ordinal,
                    assignment_version_id=str(assignment_id),
                )
            )

    def add_target_activation_event(
        self,
        *,
        event_id: str,
        case_id: RecordId,
        decision_version_id: RecordVersionId,
        configuration_version_id: RecordVersionId,
        boundary_snapshot_version_id: RecordVersionId,
        prerequisite_basis_version_id: RecordVersionId,
        activation_authorization_version_id: RecordVersionId,
        operating_state: str,
        lifecycle_event_id: str,
        effective_at: datetime,
        recorded_at: datetime,
        knowledge_cutoff: datetime,
    ) -> None:
        self.connection.execute(
            insert(target_activation_events).values(
                event_id=event_id,
                case_id=str(case_id),
                decision_version_id=str(decision_version_id),
                configuration_version_id=str(configuration_version_id),
                boundary_snapshot_version_id=str(boundary_snapshot_version_id),
                prerequisite_basis_version_id=str(prerequisite_basis_version_id),
                activation_authorization_version_id=str(activation_authorization_version_id),
                operating_state=operating_state,
                lifecycle_event_id=lifecycle_event_id,
                effective_at_us=to_epoch_microseconds(effective_at),
                recorded_at_us=to_epoch_microseconds(recorded_at),
                knowledge_cutoff_us=to_epoch_microseconds(knowledge_cutoff),
            )
        )

    def add_learning_item(
        self,
        *,
        learning_item_id: RecordId,
        version_id: RecordVersionId,
        case_id: RecordId,
        decision_version_id: RecordVersionId,
        configuration_id: RecordId,
        configuration_version_id: RecordVersionId,
        uncertainty_version_id: RecordVersionId,
        owner_actor_id: RecordId,
        owner_assignment_version_id: RecordVersionId | None,
        accountable_mechanism: str | None,
        status: str,
        evidence_version_ids: tuple[RecordVersionId, ...],
        successor_decision_version_id: RecordVersionId | None,
    ) -> None:
        if not self._identity_exists(
            learning_item_records,
            learning_item_records.c.learning_item_id,
            str(learning_item_id),
        ):
            self.connection.execute(
                insert(learning_item_records).values(learning_item_id=str(learning_item_id))
            )
        self.connection.execute(
            insert(learning_item_versions).values(
                version_id=str(version_id),
                learning_item_id=str(learning_item_id),
                case_id=str(case_id),
                decision_version_id=str(decision_version_id),
                configuration_id=str(configuration_id),
                configuration_version_id=str(configuration_version_id),
                uncertainty_version_id=str(uncertainty_version_id),
                owner_actor_id=str(owner_actor_id),
                owner_assignment_version_id=(
                    str(owner_assignment_version_id) if owner_assignment_version_id else None
                ),
                accountable_mechanism=accountable_mechanism,
                status=status,
                successor_decision_version_id=(
                    str(successor_decision_version_id) if successor_decision_version_id else None
                ),
            )
        )
        for evidence_id in evidence_version_ids:
            self.connection.execute(
                insert(learning_item_evidence).values(
                    learning_item_version_id=str(version_id),
                    evidence_version_id=str(evidence_id),
                )
            )

    # Increment 6 projections. The common record/version/status tables remain
    # authoritative; these normalized tables enforce exact foreign-key binding.
    def add_reassessment_mechanism(self, **values: object) -> None:
        mechanism_id = cast("RecordId", values["mechanism_id"])
        if not self._identity_exists(
            reassessment_mechanism_records,
            reassessment_mechanism_records.c.mechanism_id,
            str(mechanism_id),
        ):
            self.connection.execute(
                insert(reassessment_mechanism_records).values(mechanism_id=str(mechanism_id))
            )
        self.connection.execute(
            insert(reassessment_mechanism_versions).values(
                version_id=str(values["version_id"]),
                mechanism_id=str(mechanism_id),
                function=values["function"],
                case_id=str(values["case_id"]),
                decision_version_id=str(values["decision_version_id"]),
                configuration_version_id=str(values["configuration_version_id"]),
                intervention_version_id=(
                    str(values["intervention_version_id"])
                    if values.get("intervention_version_id") is not None
                    else None
                ),
                accountable_actor_id=str(values["accountable_actor_id"]),
                rule_version=values["rule_version"],
                authority_scope=values["authority_scope"],
                authority_source=values["authority_source"],
                limits_json=json.dumps(values["limits"]),
            )
        )

    def reassessment_mechanism_detail(
        self, version_id: RecordVersionId
    ) -> dict[str, object] | None:
        row = (
            self.connection.execute(
                select(reassessment_mechanism_versions).where(
                    reassessment_mechanism_versions.c.version_id == str(version_id)
                )
            )
            .mappings()
            .one_or_none()
        )
        return dict(row) if row is not None else None

    def add_trigger(self, **values: object) -> None:
        trigger_id = cast("RecordId", values["trigger_id"])
        if not self._identity_exists(
            trigger_records, trigger_records.c.trigger_id, str(trigger_id)
        ):
            self.connection.execute(insert(trigger_records).values(trigger_id=str(trigger_id)))
        self.connection.execute(
            insert(trigger_versions).values(
                version_id=str(values["version_id"]),
                trigger_id=str(trigger_id),
                case_id=str(values["case_id"]),
                decision_version_id=str(values["decision_version_id"]),
                configuration_version_id=str(values["configuration_version_id"]),
                trigger_type=values["trigger_type"],
                management_question=values["management_question"],
                affected_scope_json=json.dumps(values["affected_scope"]),
                source_kind=values["source_kind"],
                source_family=values["source_family"],
                source_record_id=values["source_record_id"],
                source_version_id=values["source_version_id"],
                source_system=values.get("source_system"),
                source_actor=values.get("source_actor"),
                source_event_id=values["source_event_id"],
                source_knowledge_at_us=to_epoch_microseconds(
                    cast("datetime", values["source_knowledge_at"])
                ),
                withdrawn=values["withdrawn"],
            )
        )

    def trigger_detail(self, version_id: RecordVersionId) -> dict[str, object] | None:
        row = (
            self.connection.execute(
                select(trigger_versions).where(trigger_versions.c.version_id == str(version_id))
            )
            .mappings()
            .one_or_none()
        )
        return dict(row) if row is not None else None

    def trigger_versions_for_identity(self, trigger_id: RecordId) -> tuple[RecordVersionId, ...]:
        rows = self.connection.execute(
            select(trigger_versions.c.version_id).where(
                trigger_versions.c.trigger_id == str(trigger_id)
            )
        ).scalars()
        return tuple(RecordVersionId.parse(cast("str", value)) for value in rows)

    def add_trigger_determination(self, **values: object) -> None:
        determination_id = cast("RecordId", values["determination_id"])
        if not self._identity_exists(
            trigger_determination_records,
            trigger_determination_records.c.determination_id,
            str(determination_id),
        ):
            self.connection.execute(
                insert(trigger_determination_records).values(determination_id=str(determination_id))
            )
        self.connection.execute(
            insert(trigger_determination_versions).values(
                version_id=str(values["version_id"]),
                determination_id=str(determination_id),
                trigger_version_id=str(values["trigger_version_id"]),
                case_id=str(values["case_id"]),
                decision_version_id=str(values["decision_version_id"]),
                configuration_version_id=str(values["configuration_version_id"]),
                outcome=values["outcome"],
                actor_id=str(values["actor_id"]),
                assignment_version_id=(
                    str(values["assignment_version_id"])
                    if values.get("assignment_version_id") is not None
                    else None
                ),
                mechanism_version_id=(
                    str(values["mechanism_version_id"])
                    if values.get("mechanism_version_id") is not None
                    else None
                ),
            )
        )

    def trigger_determination_rows(
        self, trigger_version_id: RecordVersionId
    ) -> tuple[dict[str, object], ...]:
        rows = self.connection.execute(
            select(trigger_determination_versions).where(
                trigger_determination_versions.c.trigger_version_id == str(trigger_version_id)
            )
        ).mappings()
        return tuple(dict(row) for row in rows)

    def add_reassessment(self, **values: object) -> None:
        reassessment_id = cast("RecordId", values["reassessment_id"])
        if not self._identity_exists(
            reassessment_records, reassessment_records.c.reassessment_id, str(reassessment_id)
        ):
            self.connection.execute(
                insert(reassessment_records).values(reassessment_id=str(reassessment_id))
            )
        self.connection.execute(
            insert(reassessment_versions).values(
                version_id=str(values["version_id"]),
                reassessment_id=str(reassessment_id),
                case_id=str(values["case_id"]),
                decision_version_id=str(values["decision_version_id"]),
                configuration_version_id=str(values["configuration_version_id"]),
                purpose=values["purpose"],
                affected_scope_json=json.dumps(values["affected_scope"]),
                owner_actor_id=str(values["owner_actor_id"]),
                owner_assignment_version_id=(
                    str(values["owner_assignment_version_id"])
                    if values.get("owner_assignment_version_id") is not None
                    else None
                ),
                owner_mechanism_version_id=(
                    str(values["owner_mechanism_version_id"])
                    if values.get("owner_mechanism_version_id") is not None
                    else None
                ),
                initial_status=values["status"],
            )
        )
        memberships = cast("tuple[dict[str, object], ...]", values["memberships"])
        for ordinal, membership in enumerate(memberships):
            membership_id = cast("RecordId", membership["membership_id"])
            if not self._identity_exists(
                trigger_membership_records,
                trigger_membership_records.c.membership_id,
                str(membership_id),
            ):
                self.connection.execute(
                    insert(trigger_membership_records).values(membership_id=str(membership_id))
                )
            self.connection.execute(
                insert(trigger_membership_versions).values(
                    version_id=str(membership["version_id"]),
                    membership_id=str(membership_id),
                    trigger_version_id=str(membership["trigger_version_id"]),
                    reassessment_version_id=str(values["version_id"]),
                    membership_scope=membership["membership_scope"],
                    active=membership["active"],
                )
            )
            self.connection.execute(
                insert(trigger_set_members).values(
                    reassessment_version_id=str(values["version_id"]),
                    ordinal=ordinal,
                    trigger_version_id=str(membership["trigger_version_id"]),
                    membership_version_id=str(membership["version_id"]),
                )
            )

    def reassessment_detail(self, version_id: RecordVersionId) -> dict[str, object] | None:
        row = (
            self.connection.execute(
                select(reassessment_versions).where(
                    reassessment_versions.c.version_id == str(version_id)
                )
            )
            .mappings()
            .one_or_none()
        )
        return dict(row) if row is not None else None

    def reassessment_versions_for_case(self, case_id: RecordId) -> tuple[RecordVersionId, ...]:
        rows = self.connection.execute(
            select(reassessment_versions.c.version_id).where(
                reassessment_versions.c.case_id == str(case_id)
            )
        ).scalars()
        return tuple(RecordVersionId.parse(cast("str", value)) for value in rows)

    def trigger_set(
        self, reassessment_version_id: RecordVersionId
    ) -> tuple[tuple[RecordVersionId, RecordVersionId], ...]:
        rows = self.connection.execute(
            select(
                trigger_set_members.c.trigger_version_id,
                trigger_set_members.c.membership_version_id,
            )
            .where(trigger_set_members.c.reassessment_version_id == str(reassessment_version_id))
            .order_by(trigger_set_members.c.ordinal)
        ).all()
        return tuple(
            (RecordVersionId.parse(cast("str", row[0])), RecordVersionId.parse(cast("str", row[1])))
            for row in rows
        )

    def membership_rows_for_trigger(
        self, trigger_version_id: RecordVersionId
    ) -> tuple[dict[str, object], ...]:
        rows = self.connection.execute(
            select(trigger_membership_versions).where(
                trigger_membership_versions.c.trigger_version_id == str(trigger_version_id),
                trigger_membership_versions.c.active.is_(True),
            )
        ).mappings()
        return tuple(dict(row) for row in rows)

    def add_reassessment_determination(self, **values: object) -> None:
        determination_id = cast("RecordId", values["determination_id"])
        if not self._identity_exists(
            reassessment_determination_records,
            reassessment_determination_records.c.determination_id,
            str(determination_id),
        ):
            self.connection.execute(
                insert(reassessment_determination_records).values(
                    determination_id=str(determination_id)
                )
            )
        self.connection.execute(
            insert(reassessment_determination_versions).values(
                version_id=str(values["version_id"]),
                determination_id=str(determination_id),
                kind=values["kind"],
                outcome=values["outcome"],
                target_reassessment_version_id=(
                    str(values["target_reassessment_version_id"])
                    if values.get("target_reassessment_version_id") is not None
                    else None
                ),
                canonical_trigger_version_id=(
                    str(values["canonical_trigger_version_id"])
                    if values.get("canonical_trigger_version_id") is not None
                    else None
                ),
                case_id=str(values["case_id"]),
                decision_version_id=str(values["decision_version_id"]),
                configuration_version_id=str(values["configuration_version_id"]),
                affected_scope_json=json.dumps(values["affected_scope"]),
                actor_id=str(values["actor_id"]),
                assignment_version_id=(
                    str(values["assignment_version_id"])
                    if values.get("assignment_version_id") is not None
                    else None
                ),
                mechanism_version_id=(
                    str(values["mechanism_version_id"])
                    if values.get("mechanism_version_id") is not None
                    else None
                ),
            )
        )
        for trigger_version_id in cast(
            "tuple[RecordVersionId, ...]", values["trigger_version_ids"]
        ):
            self.connection.execute(
                insert(reassessment_determination_triggers).values(
                    determination_version_id=str(values["version_id"]),
                    trigger_version_id=str(trigger_version_id),
                )
            )
        for reassessment_version_id in cast(
            "tuple[RecordVersionId, ...]", values["reassessment_version_ids"]
        ):
            self.connection.execute(
                insert(reassessment_determination_reassessments).values(
                    determination_version_id=str(values["version_id"]),
                    reassessment_version_id=str(reassessment_version_id),
                )
            )

    def reassessment_determination_detail(
        self, version_id: RecordVersionId
    ) -> dict[str, object] | None:
        row = (
            self.connection.execute(
                select(reassessment_determination_versions).where(
                    reassessment_determination_versions.c.version_id == str(version_id)
                )
            )
            .mappings()
            .one_or_none()
        )
        return dict(row) if row is not None else None

    def reassessment_determination_rows(
        self,
        *,
        kind: str,
        trigger_version_id: RecordVersionId | None = None,
        reassessment_version_ids: tuple[RecordVersionId, ...] = (),
    ) -> tuple[dict[str, object], ...]:
        query = select(reassessment_determination_versions).where(
            reassessment_determination_versions.c.kind == kind
        )
        if trigger_version_id is not None:
            query = query.join(
                reassessment_determination_triggers,
                reassessment_determination_triggers.c.determination_version_id
                == reassessment_determination_versions.c.version_id,
            ).where(
                reassessment_determination_triggers.c.trigger_version_id == str(trigger_version_id)
            )
        if reassessment_version_ids:
            query = query.join(
                reassessment_determination_reassessments,
                reassessment_determination_reassessments.c.determination_version_id
                == reassessment_determination_versions.c.version_id,
            ).where(
                reassessment_determination_reassessments.c.reassessment_version_id.in_(
                    tuple(str(value) for value in reassessment_version_ids)
                )
            )
        rows = self.connection.execute(query.distinct()).mappings()
        return tuple(dict(row) for row in rows)

    def add_interim_disposition(self, **values: object) -> None:
        disposition_id = cast("RecordId", values["disposition_id"])
        if not self._identity_exists(
            interim_disposition_records,
            interim_disposition_records.c.disposition_id,
            str(disposition_id),
        ):
            self.connection.execute(
                insert(interim_disposition_records).values(disposition_id=str(disposition_id))
            )
        expiry_at = cast("datetime | None", values.get("expiry_at"))
        self.connection.execute(
            insert(interim_disposition_versions).values(
                version_id=str(values["version_id"]),
                disposition_id=str(disposition_id),
                reassessment_version_id=str(values["reassessment_version_id"]),
                case_id=str(values["case_id"]),
                decision_version_id=str(values["decision_version_id"]),
                configuration_version_id=str(values["configuration_version_id"]),
                boundary_snapshot_version_id=str(values["boundary_snapshot_version_id"]),
                affected_scope_json=json.dumps(values["affected_scope"]),
                operating_state=values.get("operating_state"),
                allowed_actions_json=json.dumps(values["allowed_actions"]),
                required_controls_json=json.dumps(values["required_controls"]),
                prohibitions_json=json.dumps(values["prohibitions"]),
                conditions_json=json.dumps(values["conditions"]),
                suspend_scope=values["suspend_scope"],
                authority_basis_version_id=str(values["authority_basis_version_id"]),
                authority_actor_id=str(values["authority_actor_id"]),
                expiry_at_us=to_epoch_microseconds(expiry_at) if expiry_at is not None else None,
            )
        )

    def interim_disposition_rows(
        self,
        *,
        case_id: RecordId,
        decision_version_id: RecordVersionId,
        configuration_version_id: RecordVersionId,
    ) -> tuple[dict[str, object], ...]:
        rows = self.connection.execute(
            select(interim_disposition_versions).where(
                interim_disposition_versions.c.case_id == str(case_id),
                interim_disposition_versions.c.decision_version_id == str(decision_version_id),
                interim_disposition_versions.c.configuration_version_id
                == str(configuration_version_id),
            )
        ).mappings()
        return tuple(dict(row) for row in rows)

    def add_decision_confirmation(self, **values: object) -> None:
        confirmation_id = cast("RecordId", values["confirmation_id"])
        if not self._identity_exists(
            decision_confirmation_records,
            decision_confirmation_records.c.confirmation_id,
            str(confirmation_id),
        ):
            self.connection.execute(
                insert(decision_confirmation_records).values(confirmation_id=str(confirmation_id))
            )
        self.connection.execute(
            insert(decision_confirmation_versions).values(
                version_id=str(values["version_id"]),
                confirmation_id=str(confirmation_id),
                reassessment_version_id=str(values["reassessment_version_id"]),
                decision_version_id=str(values["decision_version_id"]),
                configuration_version_id=str(values["configuration_version_id"]),
                boundary_snapshot_version_id=str(values["boundary_snapshot_version_id"]),
                authority_basis_version_id=str(values["authority_basis_version_id"]),
                confirmer_actor_id=str(values["confirmer_actor_id"]),
            )
        )

    def add_reassessment_completion(self, **values: object) -> None:
        self.connection.execute(
            insert(reassessment_completion_outcomes).values(
                reassessment_version_id=str(values["reassessment_version_id"]),
                path=values["path"],
                confirmation_version_id=(
                    str(values["confirmation_version_id"])
                    if values.get("confirmation_version_id") is not None
                    else None
                ),
                successor_decision_version_id=(
                    str(values["successor_decision_version_id"])
                    if values.get("successor_decision_version_id") is not None
                    else None
                ),
                completed_at_us=to_epoch_microseconds(cast("datetime", values["completed_at"])),
            )
        )

    def reassessment_completion(
        self, reassessment_version_id: RecordVersionId
    ) -> dict[str, object] | None:
        row = (
            self.connection.execute(
                select(reassessment_completion_outcomes).where(
                    reassessment_completion_outcomes.c.reassessment_version_id
                    == str(reassessment_version_id)
                )
            )
            .mappings()
            .one_or_none()
        )
        return dict(row) if row is not None else None

    def current_reassessment_status(
        self,
        *,
        reassessment_version_id: RecordVersionId,
        effective_at: datetime,
        known_at: datetime,
    ) -> str:
        detail = self.reassessment_detail(reassessment_version_id)
        if detail is None:
            raise ValueError("Reassessment Version does not exist")
        record_id = RecordId.parse(cast("str", detail["reassessment_id"]))
        history = self.get_history(record_id)
        events = sorted(
            (
                event
                for event in history.status_events
                if event.target_version_id == reassessment_version_id
                and event.effective_at <= effective_at
                and event.recorded_at <= known_at
                and event.new_status
                in {
                    "PROPOSED",
                    "OPEN",
                    "ANALYSIS_IN_PROGRESS",
                    "AWAITING_DECISION_AUTHORITY",
                    "BLOCKED_CONFLICT",
                    "COMPLETED_CONFIRMED",
                    "COMPLETED_SUCCESSOR_DECISION",
                    "CANCELLED",
                    "SUPERSEDED",
                }
            ),
            key=lambda event: (event.effective_at, event.recorded_at, str(event.event_id)),
        )
        return events[-1].new_status if events else cast("str", detail["initial_status"])

    def add_shared_dependency(self, **values: object) -> None:
        dependency_id = cast("RecordId", values["dependency_id"])
        if not self._identity_exists(
            shared_dependency_records,
            shared_dependency_records.c.dependency_id,
            str(dependency_id),
        ):
            self.connection.execute(
                insert(shared_dependency_records).values(dependency_id=str(dependency_id))
            )
        self.connection.execute(
            insert(shared_dependency_versions).values(
                version_id=str(values["version_id"]),
                dependency_id=str(dependency_id),
                dependency_kind=values["dependency_kind"],
                purpose=values["purpose"],
                declared_scope=values["declared_scope"],
                organizational_context=values.get("organizational_context"),
                provenance_json=values["provenance_json"],
                withdrawn=values["withdrawn"],
            )
        )

    def shared_dependency_detail(self, version_id: RecordVersionId) -> dict[str, object] | None:
        row = (
            self.connection.execute(
                select(shared_dependency_versions).where(
                    shared_dependency_versions.c.version_id == str(version_id)
                )
            )
            .mappings()
            .one_or_none()
        )
        return dict(row) if row is not None else None

    def add_dependency_candidate_set(self, **values: object) -> None:
        candidate_set_id = cast("RecordId", values["candidate_set_id"])
        if not self._identity_exists(
            dependency_candidate_set_records,
            dependency_candidate_set_records.c.candidate_set_id,
            str(candidate_set_id),
        ):
            self.connection.execute(
                insert(dependency_candidate_set_records).values(
                    candidate_set_id=str(candidate_set_id)
                )
            )
        version_id = str(values["version_id"])
        self.connection.execute(
            insert(dependency_candidate_set_versions).values(
                version_id=version_id,
                candidate_set_id=str(candidate_set_id),
                dependency_kind=values["dependency_kind"],
                equivalence_scope=values["equivalence_scope"],
                purpose=values["purpose"],
                organizational_context=values.get("organizational_context"),
                provenance_json=values["provenance_json"],
                membership_checksum=values["membership_checksum"],
                withdrawn=values["withdrawn"],
            )
        )
        for ordinal, member in enumerate(cast("list[dict[str, str]]", values["members"])):
            self.connection.execute(
                insert(dependency_candidate_set_members).values(
                    candidate_set_version_id=version_id,
                    ordinal=ordinal,
                    source_family=member["source_family"],
                    source_record_id=member["source_record_id"],
                    source_version_id=member["source_version_id"],
                    dependency_kind=member["dependency_kind"],
                )
            )

    def candidate_set_detail(self, version_id: RecordVersionId) -> dict[str, object] | None:
        row = (
            self.connection.execute(
                select(dependency_candidate_set_versions).where(
                    dependency_candidate_set_versions.c.version_id == str(version_id)
                )
            )
            .mappings()
            .one_or_none()
        )
        return dict(row) if row is not None else None

    def candidate_set_members(self, version_id: RecordVersionId) -> tuple[dict[str, object], ...]:
        rows = (
            self.connection.execute(
                select(dependency_candidate_set_members)
                .where(
                    dependency_candidate_set_members.c.candidate_set_version_id == str(version_id)
                )
                .order_by(dependency_candidate_set_members.c.ordinal)
            )
            .mappings()
            .all()
        )
        return tuple(dict(row) for row in rows)

    def add_shared_dependency_mechanism(self, **values: object) -> None:
        mechanism_id = cast("RecordId", values["mechanism_id"])
        if not self._identity_exists(
            shared_dependency_mechanism_records,
            shared_dependency_mechanism_records.c.mechanism_id,
            str(mechanism_id),
        ):
            self.connection.execute(
                insert(shared_dependency_mechanism_records).values(mechanism_id=str(mechanism_id))
            )
        self.connection.execute(
            insert(shared_dependency_mechanism_versions).values(
                version_id=str(values["version_id"]),
                mechanism_id=str(mechanism_id),
                target_type=values["target_type"],
                target_id=values["target_id"],
                accountable_actor_id=str(values["accountable_actor_id"]),
                rule_id=values["rule_id"],
                rule_version=values["rule_version"],
                authority_source=values["authority_source"],
                limits_json=values["limits_json"],
            )
        )

    def shared_dependency_mechanism_detail(
        self, version_id: RecordVersionId
    ) -> dict[str, object] | None:
        row = (
            self.connection.execute(
                select(shared_dependency_mechanism_versions).where(
                    shared_dependency_mechanism_versions.c.version_id == str(version_id)
                )
            )
            .mappings()
            .one_or_none()
        )
        return dict(row) if row is not None else None

    def shared_dependency_mechanism_versions(
        self, *, target_type: str, target_id: str
    ) -> tuple[RecordVersionId, ...]:
        rows = self.connection.execute(
            select(shared_dependency_mechanism_versions.c.version_id).where(
                shared_dependency_mechanism_versions.c.target_type == target_type,
                shared_dependency_mechanism_versions.c.target_id == target_id,
            )
        ).all()
        return tuple(RecordVersionId.parse(cast("str", row[0])) for row in rows)

    def add_equivalence_determination(self, **values: object) -> None:
        determination_id = cast("RecordId", values["determination_id"])
        if not self._identity_exists(
            shared_dependency_equivalence_records,
            shared_dependency_equivalence_records.c.determination_id,
            str(determination_id),
        ):
            self.connection.execute(
                insert(shared_dependency_equivalence_records).values(
                    determination_id=str(determination_id)
                )
            )
        version_id = str(values["version_id"])
        self.connection.execute(
            insert(shared_dependency_equivalence_versions).values(
                version_id=version_id,
                determination_id=str(determination_id),
                candidate_set_version_id=str(values["candidate_set_version_id"]),
                shared_dependency_version_id=(
                    str(values["shared_dependency_version_id"])
                    if values.get("shared_dependency_version_id") is not None
                    else None
                ),
                dependency_kind=values["dependency_kind"],
                equivalence_scope=values["equivalence_scope"],
                outcome=values["outcome"],
                actor_id=str(values["actor_id"]),
                assignment_version_id=(
                    str(values["assignment_version_id"])
                    if values.get("assignment_version_id") is not None
                    else None
                ),
                mechanism_version_id=(
                    str(values["mechanism_version_id"])
                    if values.get("mechanism_version_id") is not None
                    else None
                ),
            )
        )
        for ordinal, assignment_id in enumerate(
            cast("tuple[RecordVersionId, ...]", values["delegation_chain_version_ids"])
        ):
            self.connection.execute(
                insert(shared_dependency_equivalence_delegations).values(
                    determination_version_id=version_id,
                    ordinal=ordinal,
                    assignment_version_id=str(assignment_id),
                )
            )

    def equivalence_determination_rows(
        self,
        *,
        candidate_set_version_id: RecordVersionId,
        dependency_kind: str,
        equivalence_scope: str,
    ) -> tuple[dict[str, object], ...]:
        rows = (
            self.connection.execute(
                select(shared_dependency_equivalence_versions).where(
                    shared_dependency_equivalence_versions.c.candidate_set_version_id
                    == str(candidate_set_version_id),
                    shared_dependency_equivalence_versions.c.dependency_kind == dependency_kind,
                    shared_dependency_equivalence_versions.c.equivalence_scope == equivalence_scope,
                )
            )
            .mappings()
            .all()
        )
        return tuple(dict(row) for row in rows)

    def add_register_manifest(self, **values: object) -> None:
        self.connection.execute(insert(register_output_manifests).values(**values))

    def register_manifest(self, manifest_id: str) -> dict[str, object] | None:
        row = (
            self.connection.execute(
                select(register_output_manifests).where(
                    register_output_manifests.c.manifest_id == manifest_id
                )
            )
            .mappings()
            .one_or_none()
        )
        return dict(row) if row is not None else None

    def add_notification_intent(self, **values: object) -> None:
        self.connection.execute(insert(register_notification_intents).values(**values))

    def notification_intents(self, manifest_id: str) -> tuple[dict[str, object], ...]:
        rows = (
            self.connection.execute(
                select(register_notification_intents)
                .where(register_notification_intents.c.manifest_id == manifest_id)
                .order_by(register_notification_intents.c.intent_id)
            )
            .mappings()
            .all()
        )
        return tuple(dict(row) for row in rows)

    def record_versions_for_register(
        self, version_ids: tuple[RecordVersionId, ...]
    ) -> tuple[dict[str, object], ...]:
        if not version_ids:
            return ()
        rows = (
            self.connection.execute(
                select(
                    record_versions.c.version_id,
                    record_versions.c.record_id,
                    records.c.family,
                    records.c.scope,
                    record_versions.c.content_json,
                    record_versions.c.recorded_at_us,
                    record_versions.c.effective_from_us,
                    record_versions.c.effective_to_us,
                )
                .join(records, records.c.record_id == record_versions.c.record_id)
                .where(record_versions.c.version_id.in_(tuple(str(value) for value in version_ids)))
            )
            .mappings()
            .all()
        )
        return tuple(dict(row) for row in rows)

    def register_record_identities(self, families: tuple[str, ...]) -> tuple[dict[str, str], ...]:
        rows = (
            self.connection.execute(
                select(records.c.record_id, records.c.family, records.c.scope)
                .where(records.c.family.in_(families))
                .order_by(records.c.family, records.c.scope, records.c.record_id)
            )
            .mappings()
            .all()
        )
        return tuple(
            {
                "record_id": cast("str", row["record_id"]),
                "family": cast("str", row["family"]),
                "scope": cast("str", row["scope"]),
            }
            for row in rows
        )

    def add_status_event(self, status: StatusEvent) -> None:
        self._connection.execute(
            insert(status_events).values(
                event_id=str(status.event_id),
                target_version_id=str(status.target_version_id),
                prior_status=status.prior_status,
                new_status=status.new_status,
                recorded_at_us=to_epoch_microseconds(status.recorded_at),
                effective_at_us=to_epoch_microseconds(status.effective_at),
                actor=status.actor,
                basis=status.basis,
            )
        )

    def add_relationship(self, relationship: VersionRelationship) -> None:
        self._connection.execute(
            insert(version_relationships).values(
                relationship_id=str(relationship.relationship_id),
                source_version_id=str(relationship.source_version_id),
                target_version_id=str(relationship.target_version_id),
                relationship_type=relationship.relationship_type.value,
                recorded_at_us=to_epoch_microseconds(relationship.recorded_at),
                reason=relationship.reason,
            )
        )

    def add_audit(self, fact: AuditFact) -> None:
        self._connection.execute(
            insert(audit_facts).values(
                audit_id=str(fact.audit_id),
                principal_id=fact.principal_id,
                actor_id=fact.actor_id,
                actor_resolution=fact.actor_resolution.value,
                operation=fact.operation,
                result=fact.result,
                command_id=str(fact.command_id),
                idempotency_scope=fact.idempotency_scope,
                idempotency_key=fact.idempotency_key,
                correlation_id=fact.correlation_id,
                causation_id=fact.causation_id,
                target_record_id=str(fact.target_record_id),
                affected_version_ids_json=json.dumps(
                    [str(value) for value in fact.affected_version_ids], separators=(",", ":")
                ),
                expected_precondition=fact.expected_precondition,
                observed_precondition=fact.observed_precondition,
                effective_at_us=to_epoch_microseconds(fact.effective_at),
                recorded_at_us=to_epoch_microseconds(fact.recorded_at),
                reason_outcomes_json=json.dumps(fact.reason_outcomes, separators=(",", ":")),
                request_digest=fact.request_digest,
            )
        )

    def get_version(self, version_id: RecordVersionId) -> FinalizedRecordVersion | None:
        statement = (
            select(
                record_versions,
                records.c.family,
                records.c.scope,
            )
            .join(records, records.c.record_id == record_versions.c.record_id)
            .where(record_versions.c.version_id == str(version_id))
        )
        row = self._connection.execute(statement).mappings().one_or_none()
        return _version_from_row(row) if row is not None else None

    def get_history(self, record_id: RecordId) -> RecordHistory:
        version_rows = (
            self._connection.execute(
                select(record_versions, records.c.family, records.c.scope)
                .join(records, records.c.record_id == record_versions.c.record_id)
                .where(record_versions.c.record_id == str(record_id))
            )
            .mappings()
            .all()
        )
        versions = tuple(_version_from_row(row) for row in version_rows)
        version_ids = tuple(str(version.version_id) for version in versions)
        if not version_ids:
            return RecordHistory(
                versions=frozenset(), status_events=frozenset(), relationships=frozenset()
            )
        event_rows = (
            self._connection.execute(
                select(status_events).where(status_events.c.target_version_id.in_(version_ids))
            )
            .mappings()
            .all()
        )
        relationship_rows = (
            self._connection.execute(
                select(version_relationships).where(
                    or_(
                        version_relationships.c.source_version_id.in_(version_ids),
                        version_relationships.c.target_version_id.in_(version_ids),
                    )
                )
            )
            .mappings()
            .all()
        )
        return RecordHistory(
            versions=frozenset(versions),
            status_events=frozenset(_event_from_row(row) for row in event_rows),
            relationships=frozenset(_relationship_from_row(row) for row in relationship_rows),
        )

    def select_current(self, query: SelectionQuery) -> CurrentSelection:
        statement = (
            select(record_versions, records.c.family, records.c.scope)
            .join(records, records.c.record_id == record_versions.c.record_id)
            .where(records.c.family == query.family, records.c.scope == query.scope)
        )
        if query.record_id is not None:
            statement = statement.where(records.c.record_id == str(query.record_id))
        version_rows = self._connection.execute(statement).mappings().all()
        candidates: list[SelectionCandidate] = []
        for row in version_rows:
            version = _version_from_row(row)
            event_rows = (
                self._connection.execute(
                    select(status_events).where(
                        status_events.c.target_version_id == str(version.version_id)
                    )
                )
                .mappings()
                .all()
            )
            candidates.append(
                SelectionCandidate(
                    record_id=version.record_id,
                    version_id=version.version_id,
                    family=version.family,
                    scope=version.scope,
                    recorded_at=version.recorded_at,
                    effective=version.effective,
                    finalized=cast("bool", row["finalized"]),
                    status_events=frozenset(_event_from_row(event) for event in event_rows),
                )
            )
        return select_current(query, tuple(candidates))

    def count_rows(self, table_name: str) -> int:
        table = metadata.tables.get(table_name)
        if table is None:
            raise ValueError(f"unknown table: {table_name}")
        return int(self._connection.scalar(select(func.count()).select_from(table)) or 0)


class SQLiteIntegrityStore:
    """Synchronous local adapter with one explicit writer per semantic commit."""

    def __init__(self, database_url: str, *, timeout_seconds: float = 0.25) -> None:
        self.engine: Engine = create_engine(
            database_url,
            connect_args={"timeout": timeout_seconds},
        )
        event.listen(self.engine, "connect", _enable_foreign_keys)

    @contextmanager
    def read_transaction(self) -> Iterator[SQLiteIntegrityTransaction]:
        """Use one consistent read connection without acquiring the writer boundary."""
        with self.engine.connect() as connection:
            yield SQLiteIntegrityTransaction(connection)

    @contextmanager
    def semantic_transaction(self) -> Iterator[SQLiteIntegrityTransaction]:
        if _semantic_active.get():
            raise NestedSemanticCommit("nested independent semantic commits are prohibited")
        token = _semantic_active.set(True)
        try:
            with self.engine.connect() as connection:
                try:
                    connection.exec_driver_sql("BEGIN IMMEDIATE")
                except OperationalError as error:
                    if "locked" in str(error).casefold() or "busy" in str(error).casefold():
                        raise WriterContention("SQLITE WRITER CONTENTION") from error
                    raise
                transaction = SQLiteIntegrityTransaction(connection)
                try:
                    yield transaction
                    connection.commit()
                except BaseException:
                    connection.rollback()
                    raise
        finally:
            _semantic_active.reset(token)

    def get_version(self, version_id: RecordVersionId) -> FinalizedRecordVersion | None:
        with self.engine.connect() as connection:
            return SQLiteIntegrityTransaction(connection).get_version(version_id)

    def get_history(self, record_id: RecordId) -> RecordHistory:
        with self.engine.connect() as connection:
            return SQLiteIntegrityTransaction(connection).get_history(record_id)

    def select_current(self, query: SelectionQuery) -> CurrentSelection:
        with self.engine.connect() as connection:
            return SQLiteIntegrityTransaction(connection).select_current(query)

    def get_audit(self, audit_id: AuditId) -> AuditFact | None:
        with self.engine.connect() as connection:
            row = (
                connection.execute(
                    select(audit_facts).where(audit_facts.c.audit_id == str(audit_id))
                )
                .mappings()
                .one_or_none()
            )
            return _audit_from_row(row) if row is not None else None

    def count_rows(self, table_name: str) -> int:
        with self.engine.connect() as connection:
            return SQLiteIntegrityTransaction(connection).count_rows(table_name)

    def dispose(self) -> None:
        self.engine.dispose()
