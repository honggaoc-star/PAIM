"""Increment 5 Intervention, Completion Acceptance, activation, and Learning semantics."""

from __future__ import annotations

import json
from datetime import datetime
from typing import cast

from paim.application.increment2 import DomainRuleViolation
from paim.application.increment4 import Increment4ApplicationService
from paim.audit import AuditFact
from paim.domain.increment4 import AuthorizedDecisionFound, DecisionStatus
from paim.domain.increment5 import (
    ActivationAuthorityKind,
    ActivationRequest,
    ActivationResult,
    AggregatePrerequisiteResult,
    CompletionAcceptanceConflict,
    CompletionAcceptanceFound,
    CompletionAcceptanceNotEstablished,
    CompletionAcceptanceOutcome,
    CompletionAcceptanceSelection,
    CompletionAcceptanceStatus,
    CompletionAcceptanceVersionInput,
    CompletionAcceptorMechanismVersionInput,
    CompletionAccountabilityConflict,
    CompletionAccountabilityFound,
    CompletionAccountabilityNotEstablished,
    CompletionAccountabilityResolution,
    CompletionResultVersionInput,
    ContinuedValidityAccountabilityConflict,
    ContinuedValidityAccountabilityFound,
    ContinuedValidityAccountabilityNotEstablished,
    ContinuedValidityAccountabilityResolution,
    ContinuedValidityMechanismVersionInput,
    InterventionStatus,
    InterventionVersionInput,
    LearningItemVersionInput,
    ObligationDetail,
    ObligationEvaluation,
    ObligationResult,
    ObligationSetConflict,
    ObligationSetFound,
    ObligationSetNotEstablished,
    ObligationSetSelection,
    ObligationSetVersionInput,
    PrerequisiteEvaluation,
    ReplacementVersionInput,
    RequirementType,
    ReuseDeterminationVersionInput,
)
from paim.domain.increment5_ports import Increment5Store, Increment5Transaction
from paim.domain.models import CaseLifecycleState, CommandMeta, LifecycleTransitionResult
from paim.integrity import (
    AuditId,
    EffectiveInterval,
    EventId,
    RecordId,
    RecordVersionId,
    RelationshipId,
    SelectionFound,
    SelectionQuery,
    StatusEvent,
)
from paim.integrity.commands import canonical_command_digest
from paim.integrity.records import (
    FinalizedRecordVersion,
    JsonValue,
    VersionRelationship,
    canonical_json,
)
from paim.integrity.time import Clock, from_epoch_microseconds, require_utc
from paim.persistence.ports import CommandOutcome, IdempotencyFact

_COMPLETION_ACCEPTOR_ROLE = "Intervention Completion Acceptor"
_CONTINUED_VALIDITY_ACCEPTOR_ROLE = "Continued Validity Acceptor"


def _exactly_one(value: RecordVersionId | None, mechanism: str | RecordVersionId | None) -> bool:
    return (value is not None) != bool(mechanism)


class Increment5ApplicationService(Increment4ApplicationService):
    """Synchronous bounded Increment 5 application boundary."""

    def __init__(self, store: Increment5Store, clock: Clock) -> None:
        super().__init__(store, clock)
        self._increment5_store = store

    @staticmethod
    def _is_current(
        transaction: Increment5Transaction,
        version_id: RecordVersionId,
        *,
        effective_at: datetime,
        known_at: datetime,
    ) -> bool:
        version = transaction.get_version(version_id)
        if version is None:
            return False
        selection = transaction.select_current(
            SelectionQuery(
                family=version.family,
                scope=version.scope,
                effective_at=effective_at,
                known_at=known_at,
                record_id=version.record_id,
            )
        )
        return (
            isinstance(selection, SelectionFound) and selection.candidate.version_id == version_id
        )

    @staticmethod
    def _version_content(
        transaction: Increment5Transaction, version_id: RecordVersionId
    ) -> dict[str, JsonValue]:
        version = transaction.get_version(version_id)
        if version is None:
            raise DomainRuleViolation(f"required version {version_id} is not established")
        return version.content

    def commit_intervention(
        self, meta: CommandMeta, value: InterventionVersionInput
    ) -> CommandOutcome:
        if not _exactly_one(value.owner_assignment_version_id, value.accountable_mechanism):
            raise DomainRuleViolation("Intervention requires exactly one accountable owner")
        if not value.title.strip() or not value.scope.strip() or not value.completion_criteria:
            raise DomainRuleViolation("Intervention scope and completion criteria are required")
        content: dict[str, JsonValue] = {
            "case_id": str(value.case_id),
            "decision_version_id": str(value.decision_version_id),
            "configuration_id": str(value.configuration_id),
            "configuration_version_id": str(value.configuration_version_id),
            "owner_actor_id": str(value.owner_actor_id),
            "owner_assignment_version_id": (
                str(value.owner_assignment_version_id)
                if value.owner_assignment_version_id
                else None
            ),
            "accountable_mechanism": value.accountable_mechanism,
            "status": value.status.value,
            "title": value.title,
            "scope": value.scope,
            "implementation_provenance": value.implementation_provenance,
            "completion_criteria": list(value.completion_criteria),
            "fallback_and_remediation": value.fallback_and_remediation,
        }

        def project(base: object) -> None:
            transaction = cast("Increment5Transaction", base)
            decision = transaction.decision_detail(value.decision_version_id)
            context = transaction.configuration_version_context(value.configuration_version_id)
            if (
                decision is None
                or decision.case_id != value.case_id
                or decision.configuration_id != value.configuration_id
                or decision.configuration_version_id != value.configuration_version_id
                or context is None
                or context.owning_case_id != value.case_id
                or not transaction.actor_exists(value.owner_actor_id)
            ):
                raise DomainRuleViolation(
                    "Intervention exact Decision/Configuration/owner mismatch"
                )
            if value.owner_assignment_version_id is not None:
                assignment = transaction.role_assignment_detail(value.owner_assignment_version_id)
                if (
                    assignment is None
                    or assignment.actor_id != value.owner_actor_id
                    or not assignment.accountable
                    or not self._assignment_current(
                        transaction,
                        value.owner_assignment_version_id,
                        effective_at=value.effective.start,
                        known_at=self._clock.now(),
                    )
                ):
                    raise DomainRuleViolation("Intervention owner assignment is ineligible")
            transaction.add_intervention(
                intervention_id=value.intervention_id,
                version_id=value.version_id,
                case_id=value.case_id,
                decision_version_id=value.decision_version_id,
                configuration_id=value.configuration_id,
                configuration_version_id=value.configuration_version_id,
                owner_actor_id=value.owner_actor_id,
                owner_assignment_version_id=value.owner_assignment_version_id,
                accountable_mechanism=value.accountable_mechanism,
                status=value.status.value,
            )

        return self._commit_version(
            meta=meta,
            record_id=value.intervention_id,
            version_id=value.version_id,
            family="intervention",
            scope=f"intervention:{value.intervention_id}",
            content=content,
            effective=value.effective,
            expected_version_id=value.expected_version_id,
            relationship_reason=value.relationship_reason,
            relationship_type=value.relationship_type,
            project=project,
            reason_outcome="INTERVENTION_EXACT_HISTORY_RECORDED_STATUS_NOT_ACCEPTANCE",
        )

    def commit_obligation_set(
        self, meta: CommandMeta, value: ObligationSetVersionInput
    ) -> CommandOutcome:
        if not value.rationale.strip():
            raise DomainRuleViolation("Obligation Set rationale is required")
        if len({item.obligation_id for item in value.obligations}) != len(value.obligations):
            raise DomainRuleViolation("Obligation Set cannot repeat an Obligation identity")
        recorded_at = self._clock.now()
        content: dict[str, JsonValue] = {
            "decision_id": str(value.decision_id),
            "decision_version_id": str(value.decision_version_id),
            "case_id": str(value.case_id),
            "configuration_id": str(value.configuration_id),
            "configuration_version_id": str(value.configuration_version_id),
            "obligation_version_ids": [str(item.version_id) for item in value.obligations],
            "rationale": value.rationale,
        }

        def project(base: object) -> None:
            transaction = cast("Increment5Transaction", base)
            decision = transaction.decision_detail(value.decision_version_id)
            decision_record = transaction.get_version(value.decision_version_id)
            if (
                decision is None
                or decision_record is None
                or decision.decision_id != value.decision_id
                or decision.case_id != value.case_id
                or decision.configuration_id != value.configuration_id
                or decision.configuration_version_id != value.configuration_version_id
            ):
                raise DomainRuleViolation("Obligation Set exact Decision/Configuration mismatch")
            authorized = any(
                event.target_version_id == value.decision_version_id
                and event.new_status == DecisionStatus.AUTHORIZED.value
                for event in transaction.get_history(value.decision_id).status_events
            )
            if not authorized:
                raise DomainRuleViolation("Obligation Set requires an authorized Decision Version")
            transaction.add_obligation_set(
                obligation_set_id=value.obligation_set_id,
                version_id=value.version_id,
                decision_id=value.decision_id,
                decision_version_id=value.decision_version_id,
                case_id=value.case_id,
                configuration_id=value.configuration_id,
                configuration_version_id=value.configuration_version_id,
            )
            for item in value.obligations:
                intervention = transaction.intervention_detail(item.intervention_version_id)
                if (
                    intervention is None
                    or intervention.intervention_id != item.intervention_id
                    or intervention.decision_version_id != value.decision_version_id
                    or intervention.configuration_version_id != value.configuration_version_id
                ):
                    raise DomainRuleViolation("Obligation exact Intervention binding mismatch")
                if item.requirement_type is RequirementType.REQUIRED_AFTER_OPERATION and (
                    not item.post_operation_permitted or not item.post_operation_timing_conditions
                ):
                    raise DomainRuleViolation(
                        "required-after obligation needs exact Decision permission and conditions"
                    )
                if item.requirement_type is not RequirementType.REQUIRED_AFTER_OPERATION and (
                    item.post_operation_permitted or item.post_operation_timing_conditions
                ):
                    raise DomainRuleViolation(
                        "post-operation permission belongs only to required-after obligations"
                    )
                if not item.completion_criteria or not item.rationale.strip():
                    raise DomainRuleViolation("Obligation criteria and rationale are required")
                current = transaction.select_current(
                    SelectionQuery(
                        family="intervention-obligation",
                        scope=f"obligation:{item.obligation_id}",
                        effective_at=value.effective.start,
                        known_at=recorded_at,
                        record_id=item.obligation_id,
                    )
                )
                if item.expected_version_id is None:
                    if isinstance(current, SelectionFound):
                        raise DomainRuleViolation(
                            "Obligation identity already has a current Version"
                        )
                elif not isinstance(current, SelectionFound) or (
                    current.candidate.version_id != item.expected_version_id
                ):
                    raise DomainRuleViolation("Obligation successor precondition is stale")
                elif not item.relationship_reason:
                    raise DomainRuleViolation(
                        "Obligation successor requires an explicit relationship reason"
                    )
                item_content: dict[str, JsonValue] = {
                    "obligation_set_version_id": str(value.version_id),
                    "decision_version_id": str(value.decision_version_id),
                    "configuration_version_id": str(value.configuration_version_id),
                    "intervention_id": str(item.intervention_id),
                    "intervention_version_id": str(item.intervention_version_id),
                    "requirement_type": item.requirement_type.value,
                    "completion_criteria": list(item.completion_criteria),
                    "boundary_clause_version_ids": [
                        str(entry) for entry in item.boundary_clause_version_ids
                    ],
                    "decision_conditions": list(item.decision_conditions),
                    "control_references": list(item.control_references),
                    "prohibitions": list(item.prohibitions),
                    "rationale": item.rationale,
                    "provenance": item.provenance,
                    "post_operation_permitted": item.post_operation_permitted,
                    "post_operation_timing_conditions": list(item.post_operation_timing_conditions),
                }
                transaction.add_version(
                    FinalizedRecordVersion(
                        item.obligation_id,
                        item.version_id,
                        "intervention-obligation",
                        f"obligation:{item.obligation_id}",
                        canonical_json(item_content),
                        recorded_at,
                        value.effective,
                        meta.actor_id or meta.principal_id,
                    )
                )
                if item.expected_version_id is not None:
                    relationship_reason = cast("str", item.relationship_reason)
                    transaction.add_relationship(
                        VersionRelationship(
                            RelationshipId.new(),
                            item.expected_version_id,
                            item.version_id,
                            item.relationship_type,
                            recorded_at,
                            relationship_reason,
                        )
                    )
                    transaction.add_status_event(
                        StatusEvent(
                            EventId.new(),
                            item.expected_version_id,
                            "finalized",
                            item.relationship_type.value,
                            recorded_at,
                            value.effective.start,
                            meta.actor_id or meta.principal_id,
                            relationship_reason,
                        )
                    )
                transaction.add_obligation(
                    obligation_id=item.obligation_id,
                    version_id=item.version_id,
                    obligation_set_version_id=value.version_id,
                    decision_version_id=value.decision_version_id,
                    configuration_version_id=value.configuration_version_id,
                    intervention_id=item.intervention_id,
                    intervention_version_id=item.intervention_version_id,
                    requirement_type=item.requirement_type.value,
                    post_operation_permitted=item.post_operation_permitted,
                    post_operation_timing_conditions=(item.post_operation_timing_conditions),
                )

        def after_version(
            _transaction: object, _recorded_at: datetime
        ) -> tuple[tuple[EventId, ...], tuple[RecordVersionId, ...]]:
            return (), tuple(item.version_id for item in value.obligations)

        return self._commit_version(
            meta=meta,
            record_id=value.obligation_set_id,
            version_id=value.version_id,
            family="intervention-obligation-set",
            scope=(
                f"decision-version:{value.decision_version_id}:"
                f"configuration-version:{value.configuration_version_id}"
            ),
            content=content,
            effective=value.effective,
            expected_version_id=value.expected_version_id,
            relationship_reason=value.relationship_reason,
            relationship_type=value.relationship_type,
            project=project,
            after_version=after_version,
            reason_outcome="EXACT_DECISION_INTERVENTION_OBLIGATION_SET_RECORDED_ATOMICALLY",
        )

    def commit_completion_result(
        self, meta: CommandMeta, value: CompletionResultVersionInput
    ) -> CommandOutcome:
        if (
            not value.criteria
            or any(not item.criterion.strip() for item in value.criteria)
            or not value.evidence_version_ids
        ):
            raise DomainRuleViolation(
                "Completion Result requires criterion-by-criterion outcomes and Evidence"
            )
        content: dict[str, JsonValue] = {
            "obligation_version_id": str(value.obligation_version_id),
            "intervention_version_id": str(value.intervention_version_id),
            "decision_version_id": str(value.decision_version_id),
            "configuration_version_id": str(value.configuration_version_id),
            "criteria": [
                {
                    "criterion": item.criterion,
                    "outcome": item.outcome.value,
                    "rationale": item.rationale,
                }
                for item in value.criteria
            ],
            "evidence_version_ids": [str(item) for item in value.evidence_version_ids],
            "evidence_provenance": value.evidence_provenance,
            "performer_actor_id": str(value.performer_actor_id),
            "limitations": list(value.limitations),
            "residual_exposure": value.residual_exposure,
            "fallback_remediation_state": value.fallback_remediation_state,
        }

        def project(base: object) -> None:
            transaction = cast("Increment5Transaction", base)
            obligation = transaction.obligation_detail(value.obligation_version_id)
            intervention = transaction.intervention_detail(value.intervention_version_id)
            allowed_intervention = False
            if obligation is not None:
                if obligation.intervention_version_id == value.intervention_version_id:
                    allowed_intervention = True
                else:
                    replacements = self._current_record_versions(
                        transaction,
                        transaction.replacement_versions(
                            obligation_version_id=value.obligation_version_id
                        ),
                        effective_at=value.effective.start,
                        known_at=self._clock.now(),
                    )
                    if len(replacements) == 1:
                        replacement = transaction.replacement_detail(replacements[0])
                        allowed_intervention = bool(
                            replacement is not None
                            and not replacement["substantive_change"]
                            and replacement["replacement_intervention_version_id"]
                            == str(value.intervention_version_id)
                        )
            if (
                obligation is None
                or intervention is None
                or not allowed_intervention
                or obligation.decision_version_id != value.decision_version_id
                or obligation.configuration_version_id != value.configuration_version_id
                or intervention.decision_version_id != value.decision_version_id
                or intervention.configuration_version_id != value.configuration_version_id
                or not transaction.actor_exists(value.performer_actor_id)
            ):
                raise DomainRuleViolation("Completion Result exact binding is ineligible")
            for evidence_id in value.evidence_version_ids:
                evidence = transaction.get_version(evidence_id)
                if evidence is None or evidence.family != "evidence":
                    raise DomainRuleViolation(
                        "Completion Result Evidence Version is not established"
                    )
            transaction.add_completion_result(
                result_id=value.result_id,
                version_id=value.version_id,
                obligation_version_id=value.obligation_version_id,
                intervention_version_id=value.intervention_version_id,
                decision_version_id=value.decision_version_id,
                configuration_version_id=value.configuration_version_id,
                criteria=value.criteria,
                evidence_version_ids=value.evidence_version_ids,
                performer_actor_id=value.performer_actor_id,
            )

        return self._commit_version(
            meta=meta,
            record_id=value.result_id,
            version_id=value.version_id,
            family="intervention-completion-result",
            scope=f"obligation-version:{value.obligation_version_id}",
            content=content,
            effective=value.effective,
            expected_version_id=value.expected_version_id,
            relationship_reason=value.relationship_reason,
            relationship_type=value.relationship_type,
            project=project,
            reason_outcome="COMPLETION_RESULT_RECORDED_WITHOUT_INFERRED_ACCEPTANCE",
        )

    def commit_completion_acceptor_mechanism(
        self, meta: CommandMeta, value: CompletionAcceptorMechanismVersionInput
    ) -> CommandOutcome:
        if (
            not value.rule_version.strip()
            or not value.authority_scope.strip()
            or not value.authority_source.strip()
        ):
            raise DomainRuleViolation(
                "Completion Acceptor mechanism requires retained rule, scope, and authority source"
            )
        content: dict[str, JsonValue] = {
            "case_id": str(value.case_id),
            "intervention_id": str(value.intervention_id),
            "intervention_version_id": str(value.intervention_version_id),
            "decision_version_id": str(value.decision_version_id),
            "configuration_id": str(value.configuration_id),
            "configuration_version_id": str(value.configuration_version_id),
            "accountable_actor_id": str(value.accountable_actor_id),
            "rule_version": value.rule_version,
            "authority_scope": value.authority_scope,
            "authority_source": value.authority_source,
        }

        def project(base: object) -> None:
            transaction = cast("Increment5Transaction", base)
            intervention = transaction.intervention_detail(value.intervention_version_id)
            decision = transaction.decision_detail(value.decision_version_id)
            context = transaction.configuration_version_context(value.configuration_version_id)
            if (
                intervention is None
                or intervention.intervention_id != value.intervention_id
                or intervention.case_id != value.case_id
                or intervention.decision_version_id != value.decision_version_id
                or intervention.configuration_id != value.configuration_id
                or intervention.configuration_version_id != value.configuration_version_id
                or decision is None
                or decision.case_id != value.case_id
                or decision.configuration_id != value.configuration_id
                or decision.configuration_version_id != value.configuration_version_id
                or context is None
                or context.configuration_id != value.configuration_id
                or context.owning_case_id != value.case_id
                or not transaction.actor_exists(value.accountable_actor_id)
            ):
                raise DomainRuleViolation(
                    "Completion Acceptor mechanism exact governed context is ineligible"
                )
            transaction.add_completion_acceptor_mechanism(
                mechanism_id=value.mechanism_id,
                version_id=value.version_id,
                case_id=value.case_id,
                intervention_id=value.intervention_id,
                intervention_version_id=value.intervention_version_id,
                decision_version_id=value.decision_version_id,
                configuration_id=value.configuration_id,
                configuration_version_id=value.configuration_version_id,
                accountable_actor_id=value.accountable_actor_id,
                rule_version=value.rule_version,
                authority_scope=value.authority_scope,
                authority_source=value.authority_source,
            )

        return self._commit_version(
            meta=meta,
            record_id=value.mechanism_id,
            version_id=value.version_id,
            family="completion-acceptor-mechanism",
            scope=(
                f"case:{value.case_id}:intervention:{value.intervention_id}:"
                f"decision-version:{value.decision_version_id}:"
                f"configuration-version:{value.configuration_version_id}:"
                f"mechanism:{value.mechanism_id}"
            ),
            content=content,
            effective=value.effective,
            expected_version_id=value.expected_version_id,
            relationship_reason=value.relationship_reason,
            relationship_type=value.relationship_type,
            project=project,
            reason_outcome="GOVERNED_COMPLETION_ACCEPTOR_MECHANISM_RECORDED",
        )

    def _completion_accountability_in_transaction(
        self,
        transaction: Increment5Transaction,
        *,
        obligation: ObligationDetail,
        effective_at: datetime,
        known_at: datetime,
    ) -> CompletionAccountabilityResolution:
        intervention = transaction.intervention_detail(obligation.intervention_version_id)
        decision = transaction.decision_detail(obligation.decision_version_id)
        context = transaction.configuration_version_context(obligation.configuration_version_id)
        if intervention is None or decision is None or context is None:
            return CompletionAccountabilityNotEstablished()
        targets = (
            ("intervention", str(obligation.intervention_id)),
            ("decision", str(decision.decision_id)),
            ("configuration", str(context.configuration_id)),
            ("case", str(context.owning_case_id)),
        )
        assignment_candidates: set[RecordVersionId] = set()
        for record_id in transaction.role_assignment_records(
            role=_COMPLETION_ACCEPTOR_ROLE, targets=targets
        ):
            for candidate in transaction.get_history(record_id).versions:
                detail = transaction.role_assignment_detail(candidate.version_id)
                if (
                    detail is not None
                    and detail.accountable
                    and (detail.target_type.value, detail.target_id) in targets
                    and self._assignment_current(
                        transaction,
                        candidate.version_id,
                        effective_at=effective_at,
                        known_at=known_at,
                    )
                ):
                    assignment_candidates.add(candidate.version_id)
        mechanism_candidates = {
            version_id
            for version_id in transaction.completion_acceptor_mechanism_versions(
                case_id=context.owning_case_id,
                intervention_id=obligation.intervention_id,
                decision_version_id=obligation.decision_version_id,
                configuration_id=context.configuration_id,
                configuration_version_id=obligation.configuration_version_id,
            )
            if (
                (mechanism_detail := transaction.completion_acceptor_mechanism_detail(version_id))
                is not None
                and mechanism_detail["intervention_version_id"]
                == str(obligation.intervention_version_id)
                and self._is_current(
                    transaction,
                    version_id,
                    effective_at=effective_at,
                    known_at=known_at,
                )
            )
        }
        candidates = assignment_candidates | mechanism_candidates
        if not candidates:
            return CompletionAccountabilityNotEstablished()
        if len(candidates) > 1:
            return CompletionAccountabilityConflict(frozenset(candidates))
        selected = next(iter(candidates))
        if selected in assignment_candidates:
            return CompletionAccountabilityFound(selected, None)
        return CompletionAccountabilityFound(None, selected)

    def completion_acceptor_accountability(
        self,
        *,
        obligation_version_id: RecordVersionId,
        effective_at: datetime,
        known_at: datetime | None = None,
    ) -> CompletionAccountabilityResolution:
        effective_at = require_utc(effective_at)
        knowledge_time = require_utc(known_at or self._clock.now())
        with self._increment5_store.read_transaction() as transaction:
            obligation = transaction.obligation_detail(obligation_version_id)
            if obligation is None:
                return CompletionAccountabilityNotEstablished()
            return self._completion_accountability_in_transaction(
                transaction,
                obligation=obligation,
                effective_at=effective_at,
                known_at=knowledge_time,
            )

    def _validate_completion_acceptor(
        self,
        transaction: Increment5Transaction,
        *,
        obligation: ObligationDetail,
        actor_id: RecordId,
        assignment_version_id: RecordVersionId | None,
        mechanism_version_id: RecordVersionId | None,
        delegation_chain_version_ids: tuple[RecordVersionId, ...],
        effective_at: datetime,
        known_at: datetime,
    ) -> None:
        if not _exactly_one(assignment_version_id, mechanism_version_id):
            raise DomainRuleViolation("Completion Acceptance needs exactly one accountability path")
        resolution = self._completion_accountability_in_transaction(
            transaction,
            obligation=obligation,
            effective_at=effective_at,
            known_at=known_at,
        )
        if isinstance(resolution, CompletionAccountabilityConflict):
            raise DomainRuleViolation(resolution.reason)
        if mechanism_version_id is not None:
            if delegation_chain_version_ids:
                raise DomainRuleViolation("governed mechanism cannot cite a Role delegation chain")
            if not isinstance(resolution, CompletionAccountabilityFound) or (
                resolution.mechanism_version_id != mechanism_version_id
                or resolution.assignment_version_id is not None
            ):
                raise DomainRuleViolation("COMPLETION ACCEPTANCE ACCOUNTABILITY NOT ESTABLISHED")
            mechanism = transaction.completion_acceptor_mechanism_detail(mechanism_version_id)
            if mechanism is None or mechanism["accountable_actor_id"] != str(actor_id):
                raise DomainRuleViolation("Completion Acceptor actor/mechanism mismatch")
            return
        assert assignment_version_id is not None
        if not isinstance(resolution, CompletionAccountabilityFound) or (
            resolution.assignment_version_id != assignment_version_id
            or resolution.mechanism_version_id is not None
        ):
            raise DomainRuleViolation("COMPLETION ACCEPTANCE ACCOUNTABILITY NOT ESTABLISHED")
        assignment = transaction.role_assignment_detail(assignment_version_id)
        if assignment is None or assignment.actor_id != actor_id:
            raise DomainRuleViolation("Completion Acceptor actor/assignment mismatch")
        if assignment.delegated_from_version_id is not None and not delegation_chain_version_ids:
            raise DomainRuleViolation("delegated Completion Acceptance requires exact chain")
        if delegation_chain_version_ids:
            if delegation_chain_version_ids[-1] != assignment_version_id:
                raise DomainRuleViolation("delegation chain must terminate at Completion Acceptor")
            previous: RecordVersionId | None = None
            for link_id in delegation_chain_version_ids:
                link = transaction.role_assignment_detail(link_id)
                if (
                    link is None
                    or not link.accountable
                    or link.role != _COMPLETION_ACCEPTOR_ROLE
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
                        "invalid, expired, superseded, unrelated, or incomplete delegation"
                    )
                previous = link_id

    def commit_completion_acceptance(
        self, meta: CommandMeta, value: CompletionAcceptanceVersionInput
    ) -> CommandOutcome:
        if not value.rationale.strip():
            raise DomainRuleViolation("Completion Acceptance rationale is required")
        content: dict[str, JsonValue] = {
            "obligation_version_id": str(value.obligation_version_id),
            "intervention_version_id": str(value.intervention_version_id),
            "completion_result_version_id": str(value.completion_result_version_id),
            "decision_version_id": str(value.decision_version_id),
            "configuration_version_id": str(value.configuration_version_id),
            "boundary_condition_references": list(value.boundary_condition_references),
            "outcome": value.outcome.value,
            "status": value.status.value,
            "rationale": value.rationale,
            "exceptions": list(value.exceptions),
            "limitations": list(value.limitations),
            "accountable_actor_id": str(value.accountable_actor_id),
            "accountable_assignment_version_id": (
                str(value.accountable_assignment_version_id)
                if value.accountable_assignment_version_id
                else None
            ),
            "accountable_mechanism_version_id": (
                str(value.accountable_mechanism_version_id)
                if value.accountable_mechanism_version_id
                else None
            ),
            "delegation_chain_version_ids": [
                str(item) for item in value.delegation_chain_version_ids
            ],
        }

        def project(base: object) -> None:
            transaction = cast("Increment5Transaction", base)
            obligation = transaction.obligation_detail(value.obligation_version_id)
            result = transaction.completion_result_detail(value.completion_result_version_id)
            if (
                obligation is None
                or result is None
                or result.obligation_version_id != value.obligation_version_id
                or result.intervention_version_id != value.intervention_version_id
                or result.decision_version_id != value.decision_version_id
                or result.configuration_version_id != value.configuration_version_id
                or obligation.intervention_version_id != value.intervention_version_id
                or obligation.decision_version_id != value.decision_version_id
                or obligation.configuration_version_id != value.configuration_version_id
            ):
                raise DomainRuleViolation("Completion Acceptance exact binding is ineligible")
            if not result.all_met:
                raise DomainRuleViolation("Completion Result is not mechanically eligible")
            self._validate_completion_acceptor(
                transaction,
                obligation=obligation,
                actor_id=value.accountable_actor_id,
                assignment_version_id=value.accountable_assignment_version_id,
                mechanism_version_id=value.accountable_mechanism_version_id,
                delegation_chain_version_ids=value.delegation_chain_version_ids,
                effective_at=value.effective.start,
                known_at=self._clock.now(),
            )
            transaction.add_completion_acceptance(
                acceptance_id=value.acceptance_id,
                version_id=value.version_id,
                obligation_version_id=value.obligation_version_id,
                intervention_version_id=value.intervention_version_id,
                completion_result_version_id=value.completion_result_version_id,
                decision_version_id=value.decision_version_id,
                configuration_version_id=value.configuration_version_id,
                outcome=value.outcome.value,
                status=value.status.value,
                accountable_actor_id=value.accountable_actor_id,
                accountable_assignment_version_id=(value.accountable_assignment_version_id),
                accountable_mechanism_version_id=(value.accountable_mechanism_version_id),
                delegation_chain_version_ids=value.delegation_chain_version_ids,
            )

        return self._commit_version(
            meta=meta,
            record_id=value.acceptance_id,
            version_id=value.version_id,
            family="intervention-completion-acceptance",
            scope=f"obligation-version:{value.obligation_version_id}",
            content=content,
            effective=value.effective,
            expected_version_id=value.expected_version_id,
            relationship_reason=value.relationship_reason,
            relationship_type=value.relationship_type,
            project=project,
            reason_outcome="ACCOUNTABLE_COMPLETION_ACCEPTANCE_RECORDED_SEPARATELY",
        )

    def commit_replacement(
        self, meta: CommandMeta, value: ReplacementVersionInput
    ) -> CommandOutcome:
        if not value.rationale.strip():
            raise DomainRuleViolation("replacement rationale is required")
        if value.substantive_change and value.successor_decision_version_id is None:
            raise DomainRuleViolation("substantive replacement requires successor Decision")
        content: dict[str, JsonValue] = {
            "obligation_version_id": str(value.obligation_version_id),
            "predecessor_intervention_version_id": str(value.predecessor_intervention_version_id),
            "replacement_intervention_version_id": str(value.replacement_intervention_version_id),
            "substantive_change": value.substantive_change,
            "successor_decision_version_id": (
                str(value.successor_decision_version_id)
                if value.successor_decision_version_id
                else None
            ),
            "rationale": value.rationale,
        }

        def project(base: object) -> None:
            transaction = cast("Increment5Transaction", base)
            obligation = transaction.obligation_detail(value.obligation_version_id)
            predecessor = transaction.intervention_detail(value.predecessor_intervention_version_id)
            replacement = transaction.intervention_detail(value.replacement_intervention_version_id)
            if (
                obligation is None
                or predecessor is None
                or replacement is None
                or obligation.intervention_version_id != value.predecessor_intervention_version_id
                or replacement.case_id != predecessor.case_id
            ):
                raise DomainRuleViolation("replacement exact relationship is invalid")
            if not value.substantive_change and (
                replacement.decision_version_id != obligation.decision_version_id
                or replacement.configuration_version_id != obligation.configuration_version_id
            ):
                raise DomainRuleViolation("replacement crosses Decision/Configuration boundary")
            if value.successor_decision_version_id is not None and (
                transaction.decision_detail(value.successor_decision_version_id) is None
            ):
                raise DomainRuleViolation("successor Decision is not established")
            transaction.add_replacement(
                replacement_id=value.replacement_id,
                version_id=value.version_id,
                obligation_version_id=value.obligation_version_id,
                predecessor_intervention_version_id=(value.predecessor_intervention_version_id),
                replacement_intervention_version_id=(value.replacement_intervention_version_id),
                substantive_change=value.substantive_change,
                successor_decision_version_id=value.successor_decision_version_id,
            )

        return self._commit_version(
            meta=meta,
            record_id=value.replacement_id,
            version_id=value.version_id,
            family="intervention-replacement",
            scope=f"obligation-version:{value.obligation_version_id}",
            content=content,
            effective=value.effective,
            expected_version_id=value.expected_version_id,
            relationship_reason=value.relationship_reason,
            relationship_type=value.relationship_type,
            project=project,
            reason_outcome="EXACT_INTERVENTION_REPLACEMENT_PRESERVES_PREDECESSOR",
        )

    def commit_continued_validity_mechanism(
        self, meta: CommandMeta, value: ContinuedValidityMechanismVersionInput
    ) -> CommandOutcome:
        if (
            not value.rule_version.strip()
            or not value.authority_scope.strip()
            or not value.authority_source.strip()
        ):
            raise DomainRuleViolation(
                "Continued Validity mechanism requires retained rule, scope, and authority source"
            )
        content: dict[str, JsonValue] = {
            "successor_obligation_version_id": str(value.successor_obligation_version_id),
            "case_id": str(value.case_id),
            "intervention_id": str(value.intervention_id),
            "intervention_version_id": str(value.intervention_version_id),
            "decision_version_id": str(value.decision_version_id),
            "configuration_id": str(value.configuration_id),
            "configuration_version_id": str(value.configuration_version_id),
            "accountable_actor_id": str(value.accountable_actor_id),
            "rule_version": value.rule_version,
            "authority_scope": value.authority_scope,
            "authority_source": value.authority_source,
        }

        def project(base: object) -> None:
            transaction = cast("Increment5Transaction", base)
            obligation = transaction.obligation_detail(value.successor_obligation_version_id)
            intervention = transaction.intervention_detail(value.intervention_version_id)
            decision = transaction.decision_detail(value.decision_version_id)
            context = transaction.configuration_version_context(value.configuration_version_id)
            if (
                obligation is None
                or obligation.intervention_id != value.intervention_id
                or obligation.intervention_version_id != value.intervention_version_id
                or obligation.decision_version_id != value.decision_version_id
                or obligation.configuration_version_id != value.configuration_version_id
                or intervention is None
                or intervention.case_id != value.case_id
                or intervention.configuration_id != value.configuration_id
                or decision is None
                or decision.case_id != value.case_id
                or decision.configuration_id != value.configuration_id
                or decision.configuration_version_id != value.configuration_version_id
                or context is None
                or context.configuration_id != value.configuration_id
                or context.owning_case_id != value.case_id
                or not transaction.actor_exists(value.accountable_actor_id)
            ):
                raise DomainRuleViolation(
                    "Continued Validity mechanism exact governed context is ineligible"
                )
            transaction.add_continued_validity_mechanism(
                mechanism_id=value.mechanism_id,
                version_id=value.version_id,
                successor_obligation_version_id=value.successor_obligation_version_id,
                case_id=value.case_id,
                intervention_id=value.intervention_id,
                intervention_version_id=value.intervention_version_id,
                decision_version_id=value.decision_version_id,
                configuration_id=value.configuration_id,
                configuration_version_id=value.configuration_version_id,
                accountable_actor_id=value.accountable_actor_id,
                rule_version=value.rule_version,
                authority_scope=value.authority_scope,
                authority_source=value.authority_source,
            )

        return self._commit_version(
            meta=meta,
            record_id=value.mechanism_id,
            version_id=value.version_id,
            family="continued-validity-mechanism",
            scope=(
                f"successor-obligation-version:{value.successor_obligation_version_id}:"
                f"mechanism:{value.mechanism_id}"
            ),
            content=content,
            effective=value.effective,
            expected_version_id=value.expected_version_id,
            relationship_reason=value.relationship_reason,
            relationship_type=value.relationship_type,
            project=project,
            reason_outcome="GOVERNED_CONTINUED_VALIDITY_MECHANISM_RECORDED",
        )

    def _continued_validity_accountability_in_transaction(
        self,
        transaction: Increment5Transaction,
        *,
        obligation: ObligationDetail,
        effective_at: datetime,
        known_at: datetime,
    ) -> ContinuedValidityAccountabilityResolution:
        intervention = transaction.intervention_detail(obligation.intervention_version_id)
        decision = transaction.decision_detail(obligation.decision_version_id)
        context = transaction.configuration_version_context(obligation.configuration_version_id)
        if intervention is None or decision is None or context is None:
            return ContinuedValidityAccountabilityNotEstablished()
        targets = (
            ("intervention", str(obligation.intervention_id)),
            ("decision", str(decision.decision_id)),
            ("configuration", str(context.configuration_id)),
            ("case", str(context.owning_case_id)),
        )
        assignment_candidates: set[RecordVersionId] = set()
        for record_id in transaction.role_assignment_records(
            role=_CONTINUED_VALIDITY_ACCEPTOR_ROLE, targets=targets
        ):
            for candidate in transaction.get_history(record_id).versions:
                detail = transaction.role_assignment_detail(candidate.version_id)
                if (
                    detail is not None
                    and detail.accountable
                    and (detail.target_type.value, detail.target_id) in targets
                    and self._assignment_current(
                        transaction,
                        candidate.version_id,
                        effective_at=effective_at,
                        known_at=known_at,
                    )
                ):
                    assignment_candidates.add(candidate.version_id)
        mechanism_candidates = {
            version_id
            for version_id in transaction.continued_validity_mechanism_versions(
                successor_obligation_version_id=obligation.version_id
            )
            if (
                (mechanism_detail := transaction.continued_validity_mechanism_detail(version_id))
                is not None
                and mechanism_detail["case_id"] == str(context.owning_case_id)
                and mechanism_detail["intervention_id"] == str(obligation.intervention_id)
                and mechanism_detail["intervention_version_id"]
                == str(obligation.intervention_version_id)
                and mechanism_detail["decision_version_id"] == str(obligation.decision_version_id)
                and mechanism_detail["configuration_id"] == str(context.configuration_id)
                and mechanism_detail["configuration_version_id"]
                == str(obligation.configuration_version_id)
                and self._is_current(
                    transaction,
                    version_id,
                    effective_at=effective_at,
                    known_at=known_at,
                )
            )
        }
        candidates = assignment_candidates | mechanism_candidates
        if not candidates:
            return ContinuedValidityAccountabilityNotEstablished()
        if len(candidates) > 1:
            return ContinuedValidityAccountabilityConflict(frozenset(candidates))
        selected = next(iter(candidates))
        if selected in assignment_candidates:
            return ContinuedValidityAccountabilityFound(selected, None)
        return ContinuedValidityAccountabilityFound(None, selected)

    def _validate_continued_validity_accountability(
        self,
        transaction: Increment5Transaction,
        *,
        obligation: ObligationDetail,
        actor_id: RecordId,
        assignment_version_id: RecordVersionId | None,
        mechanism_version_id: RecordVersionId | None,
        delegation_chain_version_ids: tuple[RecordVersionId, ...],
        effective_at: datetime,
        known_at: datetime,
    ) -> None:
        if not _exactly_one(assignment_version_id, mechanism_version_id):
            raise DomainRuleViolation("continued-validity requires exactly one accountability path")
        resolution = self._continued_validity_accountability_in_transaction(
            transaction,
            obligation=obligation,
            effective_at=effective_at,
            known_at=known_at,
        )
        if isinstance(resolution, ContinuedValidityAccountabilityConflict):
            raise DomainRuleViolation(resolution.reason)
        if mechanism_version_id is not None:
            if delegation_chain_version_ids:
                raise DomainRuleViolation(
                    "governed continued-validity mechanism cannot cite a Role delegation chain"
                )
            if not isinstance(resolution, ContinuedValidityAccountabilityFound) or (
                resolution.mechanism_version_id != mechanism_version_id
                or resolution.assignment_version_id is not None
            ):
                raise DomainRuleViolation("CONTINUED VALIDITY ACCOUNTABILITY NOT ESTABLISHED")
            mechanism = transaction.continued_validity_mechanism_detail(mechanism_version_id)
            if mechanism is None or mechanism["accountable_actor_id"] != str(actor_id):
                raise DomainRuleViolation("Continued Validity actor/mechanism mismatch")
            return
        assert assignment_version_id is not None
        if not isinstance(resolution, ContinuedValidityAccountabilityFound) or (
            resolution.assignment_version_id != assignment_version_id
            or resolution.mechanism_version_id is not None
        ):
            raise DomainRuleViolation("CONTINUED VALIDITY ACCOUNTABILITY NOT ESTABLISHED")
        assignment = transaction.role_assignment_detail(assignment_version_id)
        if assignment is None or assignment.actor_id != actor_id:
            raise DomainRuleViolation("Continued Validity actor/assignment mismatch")
        if assignment.delegated_from_version_id is not None and not delegation_chain_version_ids:
            raise DomainRuleViolation("delegated continued-validity requires exact chain")
        if delegation_chain_version_ids:
            if delegation_chain_version_ids[-1] != assignment_version_id:
                raise DomainRuleViolation(
                    "delegation chain must terminate at Continued Validity Acceptor"
                )
            previous: RecordVersionId | None = None
            for link_id in delegation_chain_version_ids:
                link = transaction.role_assignment_detail(link_id)
                if (
                    link is None
                    or not link.accountable
                    or link.role != _CONTINUED_VALIDITY_ACCEPTOR_ROLE
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
                        "invalid, expired, superseded, unrelated, or incomplete delegation"
                    )
                previous = link_id

    def commit_reuse_determination(
        self, meta: CommandMeta, value: ReuseDeterminationVersionInput
    ) -> CommandOutcome:
        if not _exactly_one(
            value.accountable_assignment_version_id,
            value.accountable_mechanism_version_id,
        ):
            raise DomainRuleViolation("continued-validity requires exactly one accountability path")
        coverage = (
            value.unchanged_configuration_content,
            value.boundary_conditions_covered,
            value.completion_criteria_covered,
            value.evidence_applicability_covered,
            value.acceptance_scope_covered,
            value.changed_configuration_version_covered,
        )
        content: dict[str, JsonValue] = {
            "successor_obligation_version_id": str(value.successor_obligation_version_id),
            "prior_completion_result_version_id": str(value.prior_completion_result_version_id),
            "prior_acceptance_version_id": str(value.prior_acceptance_version_id),
            "accountable_actor_id": str(value.accountable_actor_id),
            "accountable_assignment_version_id": (
                str(value.accountable_assignment_version_id)
                if value.accountable_assignment_version_id
                else None
            ),
            "accountable_mechanism_version_id": (
                str(value.accountable_mechanism_version_id)
                if value.accountable_mechanism_version_id
                else None
            ),
            "delegation_chain_version_ids": [
                str(version_id) for version_id in value.delegation_chain_version_ids
            ],
            "unchanged_configuration_content": value.unchanged_configuration_content,
            "boundary_conditions_covered": value.boundary_conditions_covered,
            "completion_criteria_covered": value.completion_criteria_covered,
            "evidence_applicability_covered": value.evidence_applicability_covered,
            "acceptance_scope_covered": value.acceptance_scope_covered,
            "changed_configuration_version_covered": (value.changed_configuration_version_covered),
            "rationale": value.rationale,
        }

        def project(base: object) -> None:
            transaction = cast("Increment5Transaction", base)
            obligation = transaction.obligation_detail(value.successor_obligation_version_id)
            result = transaction.completion_result_detail(value.prior_completion_result_version_id)
            acceptance = transaction.completion_acceptance_detail(value.prior_acceptance_version_id)
            acceptance_selection = (
                self._select_acceptance_in_transaction(
                    transaction,
                    obligation_version_id=acceptance.obligation_version_id,
                    effective_at=value.effective.start,
                    known_at=self._clock.now(),
                )
                if acceptance is not None
                else CompletionAcceptanceNotEstablished()
            )
            if (
                obligation is None
                or result is None
                or acceptance is None
                or acceptance.completion_result_version_id
                != value.prior_completion_result_version_id
                or acceptance.outcome is not CompletionAcceptanceOutcome.ACCEPTED
                or not isinstance(acceptance_selection, CompletionAcceptanceFound)
                or acceptance_selection.acceptance_version_id != value.prior_acceptance_version_id
                or not result.all_met
                or not transaction.actor_exists(value.accountable_actor_id)
            ):
                raise DomainRuleViolation("continued-validity exact prior basis is ineligible")
            self._validate_continued_validity_accountability(
                transaction,
                obligation=obligation,
                actor_id=value.accountable_actor_id,
                assignment_version_id=value.accountable_assignment_version_id,
                mechanism_version_id=value.accountable_mechanism_version_id,
                delegation_chain_version_ids=value.delegation_chain_version_ids,
                effective_at=value.effective.start,
                known_at=self._clock.now(),
            )
            transaction.add_reuse_determination(
                determination_id=value.determination_id,
                version_id=value.version_id,
                successor_obligation_version_id=(value.successor_obligation_version_id),
                prior_completion_result_version_id=(value.prior_completion_result_version_id),
                prior_acceptance_version_id=value.prior_acceptance_version_id,
                accountable_actor_id=value.accountable_actor_id,
                accountable_assignment_version_id=(value.accountable_assignment_version_id),
                accountable_mechanism_version_id=(value.accountable_mechanism_version_id),
                delegation_chain_version_ids=value.delegation_chain_version_ids,
                all_coverage_established=all(coverage),
            )

        return self._commit_version(
            meta=meta,
            record_id=value.determination_id,
            version_id=value.version_id,
            family="intervention-continued-validity",
            scope=f"obligation-version:{value.successor_obligation_version_id}",
            content=content,
            effective=value.effective,
            expected_version_id=value.expected_version_id,
            relationship_reason=value.relationship_reason,
            relationship_type=value.relationship_type,
            project=project,
            reason_outcome="ACCOUNTABLE_CONTINUED_VALIDITY_RECORDED_PROSPECTIVELY",
        )

    def _select_obligation_set_in_transaction(
        self,
        transaction: Increment5Transaction,
        *,
        decision_version_id: RecordVersionId,
        configuration_version_id: RecordVersionId,
        effective_at: datetime,
        known_at: datetime,
    ) -> ObligationSetSelection:
        candidates = {
            version_id
            for version_id in transaction.obligation_set_versions(
                decision_version_id=decision_version_id,
                configuration_version_id=configuration_version_id,
            )
            if self._is_current(
                transaction,
                version_id,
                effective_at=effective_at,
                known_at=known_at,
            )
        }
        if not candidates:
            return ObligationSetNotEstablished()
        if len(candidates) > 1:
            return ObligationSetConflict(frozenset(candidates))
        return ObligationSetFound(next(iter(candidates)))

    def current_obligation_set(
        self,
        *,
        decision_version_id: RecordVersionId,
        configuration_version_id: RecordVersionId,
        effective_at: datetime,
        known_at: datetime | None = None,
    ) -> ObligationSetSelection:
        effective_at = require_utc(effective_at)
        knowledge_time = require_utc(known_at or self._clock.now())
        with self._increment5_store.read_transaction() as transaction:
            return self._select_obligation_set_in_transaction(
                transaction,
                decision_version_id=decision_version_id,
                configuration_version_id=configuration_version_id,
                effective_at=effective_at,
                known_at=knowledge_time,
            )

    def _select_acceptance_in_transaction(
        self,
        transaction: Increment5Transaction,
        *,
        obligation_version_id: RecordVersionId,
        effective_at: datetime,
        known_at: datetime,
        intervention_version_id: RecordVersionId | None = None,
        completion_result_version_id: RecordVersionId | None = None,
    ) -> CompletionAcceptanceSelection:
        found: list[tuple[RecordVersionId, CompletionAcceptanceOutcome]] = []
        for version_id in transaction.completion_acceptance_versions(
            obligation_version_id=obligation_version_id
        ):
            detail = transaction.completion_acceptance_detail(version_id)
            if (
                detail is None
                or detail.status is not CompletionAcceptanceStatus.CURRENT
                or (
                    intervention_version_id is not None
                    and detail.intervention_version_id != intervention_version_id
                )
                or (
                    completion_result_version_id is not None
                    and detail.completion_result_version_id != completion_result_version_id
                )
                or not self._is_current(
                    transaction,
                    version_id,
                    effective_at=effective_at,
                    known_at=known_at,
                )
            ):
                continue
            found.append((version_id, detail.outcome))
        if not found:
            return CompletionAcceptanceNotEstablished()
        if len(found) > 1:
            return CompletionAcceptanceConflict(frozenset(item[0] for item in found))
        return CompletionAcceptanceFound(*found[0])

    def current_completion_acceptance(
        self,
        *,
        obligation_version_id: RecordVersionId,
        effective_at: datetime,
        known_at: datetime | None = None,
    ) -> CompletionAcceptanceSelection:
        effective_at = require_utc(effective_at)
        knowledge_time = require_utc(known_at or self._clock.now())
        with self._increment5_store.read_transaction() as transaction:
            return self._select_acceptance_in_transaction(
                transaction,
                obligation_version_id=obligation_version_id,
                effective_at=effective_at,
                known_at=knowledge_time,
            )

    def _current_record_versions(
        self,
        transaction: Increment5Transaction,
        version_ids: tuple[RecordVersionId, ...],
        *,
        effective_at: datetime,
        known_at: datetime,
    ) -> tuple[RecordVersionId, ...]:
        return tuple(
            item
            for item in version_ids
            if self._is_current(
                transaction,
                item,
                effective_at=effective_at,
                known_at=known_at,
            )
        )

    def _evaluate_obligation_in_transaction(
        self,
        transaction: Increment5Transaction,
        *,
        obligation: ObligationDetail,
        effective_at: datetime,
        known_at: datetime,
    ) -> ObligationEvaluation:
        diagnostics: list[str] = []
        replacements = self._current_record_versions(
            transaction,
            transaction.replacement_versions(obligation_version_id=obligation.version_id),
            effective_at=effective_at,
            known_at=known_at,
        )
        if len(replacements) > 1:
            return ObligationEvaluation(
                obligation.version_id,
                ObligationResult.CONFLICT,
                obligation.intervention_version_id,
                None,
                None,
                None,
                None,
                ("incompatible current replacements",),
            )
        replacement_version_id = replacements[0] if replacements else None
        intervention_version_id = obligation.intervention_version_id
        if replacement_version_id is not None:
            replacement = transaction.replacement_detail(replacement_version_id)
            assert replacement is not None
            if bool(replacement["substantive_change"]):
                return ObligationEvaluation(
                    obligation.version_id,
                    ObligationResult.BLOCKED,
                    intervention_version_id,
                    None,
                    None,
                    replacement_version_id,
                    None,
                    ("substantive replacement requires successor Decision obligation set",),
                )
            intervention_version_id = RecordVersionId.parse(
                cast("str", replacement["replacement_intervention_version_id"])
            )
            diagnostics.append(f"replacement {replacement_version_id} applies prospectively")

        reuse_versions = self._current_record_versions(
            transaction,
            transaction.reuse_determination_versions(
                successor_obligation_version_id=obligation.version_id
            ),
            effective_at=effective_at,
            known_at=known_at,
        )
        if len(reuse_versions) > 1:
            return ObligationEvaluation(
                obligation.version_id,
                ObligationResult.CONFLICT,
                intervention_version_id,
                None,
                None,
                replacement_version_id,
                None,
                ("incompatible continued-validity determinations",),
            )
        reuse_version_id = reuse_versions[0] if reuse_versions else None
        if reuse_version_id is not None:
            reuse = transaction.reuse_determination_detail(reuse_version_id)
            assert reuse is not None
            result_id = RecordVersionId.parse(
                cast("str", reuse["prior_completion_result_version_id"])
            )
            acceptance_id = RecordVersionId.parse(cast("str", reuse["prior_acceptance_version_id"]))
            reused_result = transaction.completion_result_detail(result_id)
            reused_acceptance = transaction.completion_acceptance_detail(acceptance_id)
            prospective_acceptance = (
                self._select_acceptance_in_transaction(
                    transaction,
                    obligation_version_id=reused_acceptance.obligation_version_id,
                    effective_at=effective_at,
                    known_at=known_at,
                )
                if reused_acceptance is not None
                else CompletionAcceptanceNotEstablished()
            )
            if isinstance(prospective_acceptance, CompletionAcceptanceConflict):
                return ObligationEvaluation(
                    obligation.version_id,
                    ObligationResult.CONFLICT,
                    intervention_version_id,
                    result_id,
                    None,
                    replacement_version_id,
                    reuse_version_id,
                    tuple(
                        [
                            *diagnostics,
                            "prior Completion Acceptance is prospectively conflicting",
                        ]
                    ),
                )
            if (
                bool(reuse["all_coverage_established"])
                and reused_result is not None
                and reused_result.all_met
                and reused_acceptance is not None
                and reused_acceptance.completion_result_version_id == result_id
                and reused_acceptance.outcome is CompletionAcceptanceOutcome.ACCEPTED
                and isinstance(prospective_acceptance, CompletionAcceptanceFound)
                and prospective_acceptance.acceptance_version_id == acceptance_id
            ):
                return ObligationEvaluation(
                    obligation.version_id,
                    ObligationResult.SATISFIED,
                    intervention_version_id,
                    result_id,
                    acceptance_id,
                    replacement_version_id,
                    reuse_version_id,
                    tuple([*diagnostics, "exact continued-validity basis accepted"]),
                )
            return ObligationEvaluation(
                obligation.version_id,
                ObligationResult.NOT_ESTABLISHED,
                intervention_version_id,
                result_id,
                acceptance_id,
                replacement_version_id,
                reuse_version_id,
                tuple(
                    [
                        *diagnostics,
                        "continued-validity coverage or prospective Acceptance eligibility "
                        "not established",
                    ]
                ),
            )

        intervention = transaction.intervention_detail(intervention_version_id)
        if intervention is None:
            return ObligationEvaluation(
                obligation.version_id,
                ObligationResult.NOT_ESTABLISHED,
                intervention_version_id,
                None,
                None,
                replacement_version_id,
                None,
                tuple([*diagnostics, "required Intervention Version absent"]),
            )
        result_versions = tuple(
            item
            for item in self._current_record_versions(
                transaction,
                transaction.completion_result_versions(obligation_version_id=obligation.version_id),
                effective_at=effective_at,
                known_at=known_at,
            )
            if (
                (detail := transaction.completion_result_detail(item)) is not None
                and detail.intervention_version_id == intervention_version_id
            )
        )
        if len(result_versions) > 1:
            return ObligationEvaluation(
                obligation.version_id,
                ObligationResult.CONFLICT,
                intervention_version_id,
                None,
                None,
                replacement_version_id,
                None,
                tuple([*diagnostics, "incompatible current Completion Results"]),
            )
        result_version_id = result_versions[0] if result_versions else None
        acceptance_selection = self._select_acceptance_in_transaction(
            transaction,
            obligation_version_id=obligation.version_id,
            intervention_version_id=intervention_version_id,
            completion_result_version_id=result_version_id,
            effective_at=effective_at,
            known_at=known_at,
        )
        if isinstance(acceptance_selection, CompletionAcceptanceConflict):
            return ObligationEvaluation(
                obligation.version_id,
                ObligationResult.CONFLICT,
                intervention_version_id,
                result_version_id,
                None,
                replacement_version_id,
                None,
                tuple([*diagnostics, acceptance_selection.reason]),
            )
        incomplete = {
            InterventionStatus.PROPOSED,
            InterventionStatus.PLANNED,
            InterventionStatus.IN_PROGRESS,
            InterventionStatus.PARTIALLY_COMPLETED,
        }
        terminal = {
            InterventionStatus.BLOCKED,
            InterventionStatus.FAILED,
            InterventionStatus.CANCELLED,
        }
        if intervention.status in incomplete:
            result_state = ObligationResult.INCOMPLETE
        elif intervention.status in terminal:
            result_state = ObligationResult.BLOCKED
        elif intervention.status is InterventionStatus.SUPERSEDED or result_version_id is None:
            result_state = ObligationResult.NOT_ESTABLISHED
        else:
            completion_result = transaction.completion_result_detail(result_version_id)
            if (
                completion_result is None
                or not completion_result.all_met
                or isinstance(acceptance_selection, CompletionAcceptanceNotEstablished)
            ):
                result_state = ObligationResult.NOT_ESTABLISHED
            elif acceptance_selection.outcome is CompletionAcceptanceOutcome.REJECTED:
                result_state = ObligationResult.BLOCKED
            else:
                result_state = ObligationResult.SATISFIED
        acceptance_version_id = (
            acceptance_selection.acceptance_version_id
            if isinstance(acceptance_selection, CompletionAcceptanceFound)
            else None
        )
        diagnostics.append(
            f"Intervention {intervention_version_id} status {intervention.status.value}"
        )
        return ObligationEvaluation(
            obligation.version_id,
            result_state,
            intervention_version_id,
            result_version_id,
            acceptance_version_id,
            replacement_version_id,
            None,
            tuple(diagnostics),
        )

    def _evaluate_prerequisites_in_transaction(
        self,
        transaction: Increment5Transaction,
        *,
        decision_version_id: RecordVersionId,
        configuration_version_id: RecordVersionId,
        effective_at: datetime,
        known_at: datetime,
    ) -> PrerequisiteEvaluation:
        selected = self._select_obligation_set_in_transaction(
            transaction,
            decision_version_id=decision_version_id,
            configuration_version_id=configuration_version_id,
            effective_at=effective_at,
            known_at=known_at,
        )
        if isinstance(selected, ObligationSetConflict):
            return PrerequisiteEvaluation(
                decision_version_id,
                configuration_version_id,
                None,
                AggregatePrerequisiteResult.CONFLICT,
                (),
                (selected.reason,),
                effective_at,
                known_at,
            )
        if isinstance(selected, ObligationSetNotEstablished):
            return PrerequisiteEvaluation(
                decision_version_id,
                configuration_version_id,
                None,
                AggregatePrerequisiteResult.NOT_ESTABLISHED,
                (),
                (selected.reason,),
                effective_at,
                known_at,
            )
        detail = transaction.obligation_set_detail(selected.obligation_set_version_id)
        if detail is None:
            raise DomainRuleViolation("selected Obligation Set detail is absent")
        required: list[ObligationDetail] = []
        diagnostics: list[str] = []
        for version_id in detail.obligation_version_ids:
            obligation = transaction.obligation_detail(version_id)
            if obligation is None:
                return PrerequisiteEvaluation(
                    decision_version_id,
                    configuration_version_id,
                    detail.version_id,
                    AggregatePrerequisiteResult.NOT_ESTABLISHED,
                    (),
                    (f"Obligation {version_id} detail absent",),
                    effective_at,
                    known_at,
                )
            if obligation.requirement_type is RequirementType.REQUIRED_AFTER_OPERATION:
                if (
                    not obligation.post_operation_permitted
                    or not obligation.post_operation_timing_conditions
                ):
                    return PrerequisiteEvaluation(
                        decision_version_id,
                        configuration_version_id,
                        detail.version_id,
                        AggregatePrerequisiteResult.NOT_ESTABLISHED,
                        (),
                        ("required-after permission or timing conditions absent",),
                        effective_at,
                        known_at,
                    )
                diagnostics.append(f"required-after commitment {version_id} retained")
            elif obligation.requirement_type is RequirementType.OPTIONAL:
                diagnostics.append(f"optional commitment {version_id} does not block")
            else:
                required.append(obligation)
        if not required:
            return PrerequisiteEvaluation(
                decision_version_id,
                configuration_version_id,
                detail.version_id,
                AggregatePrerequisiteResult.NOT_REQUIRED,
                (),
                tuple(diagnostics),
                effective_at,
                known_at,
            )
        evaluations = tuple(
            self._evaluate_obligation_in_transaction(
                transaction,
                obligation=item,
                effective_at=effective_at,
                known_at=known_at,
            )
            for item in required
        )
        results = {item.result for item in evaluations}
        if ObligationResult.CONFLICT in results:
            aggregate = AggregatePrerequisiteResult.CONFLICT
        elif ObligationResult.NOT_ESTABLISHED in results:
            aggregate = AggregatePrerequisiteResult.NOT_ESTABLISHED
        elif ObligationResult.BLOCKED in results:
            aggregate = AggregatePrerequisiteResult.BLOCKED
        elif ObligationResult.INCOMPLETE in results:
            aggregate = AggregatePrerequisiteResult.INCOMPLETE
        else:
            aggregate = AggregatePrerequisiteResult.SATISFIED
        return PrerequisiteEvaluation(
            decision_version_id,
            configuration_version_id,
            detail.version_id,
            aggregate,
            evaluations,
            tuple(diagnostics),
            effective_at,
            known_at,
        )

    def evaluate_prerequisites(
        self,
        *,
        decision_version_id: RecordVersionId,
        configuration_version_id: RecordVersionId,
        effective_at: datetime,
        known_at: datetime | None = None,
    ) -> PrerequisiteEvaluation:
        effective_at = require_utc(effective_at)
        knowledge_time = require_utc(known_at or self._clock.now())
        with self._increment5_store.read_transaction() as transaction:
            return self._evaluate_prerequisites_in_transaction(
                transaction,
                decision_version_id=decision_version_id,
                configuration_version_id=configuration_version_id,
                effective_at=effective_at,
                known_at=knowledge_time,
            )

    def commit_learning_item(
        self, meta: CommandMeta, value: LearningItemVersionInput
    ) -> CommandOutcome:
        if not _exactly_one(value.owner_assignment_version_id, value.accountable_mechanism):
            raise DomainRuleViolation("Learning Item requires exactly one accountable owner")
        if (
            not value.question_or_hypothesis.strip()
            or not value.purpose.strip()
            or not value.expected_knowledge_gain.strip()
            or not value.method_activity.strip()
        ):
            raise DomainRuleViolation("Learning question, purpose, gain, and method are required")
        content: dict[str, JsonValue] = {
            "case_id": str(value.case_id),
            "decision_version_id": str(value.decision_version_id),
            "configuration_id": str(value.configuration_id),
            "configuration_version_id": str(value.configuration_version_id),
            "uncertainty_version_id": str(value.uncertainty_version_id),
            "question_or_hypothesis": value.question_or_hypothesis,
            "purpose": value.purpose,
            "expected_knowledge_gain": value.expected_knowledge_gain,
            "owner_actor_id": str(value.owner_actor_id),
            "owner_assignment_version_id": (
                str(value.owner_assignment_version_id)
                if value.owner_assignment_version_id
                else None
            ),
            "accountable_mechanism": value.accountable_mechanism,
            "method_activity": value.method_activity,
            "status": value.status.value,
            "result": value.result,
            "limitations": list(value.limitations),
            "evidence_version_ids": [str(item) for item in value.evidence_version_ids],
            "successor_decision_version_id": (
                str(value.successor_decision_version_id)
                if value.successor_decision_version_id
                else None
            ),
            "reassessment_extension_reference": value.reassessment_extension_reference,
            "provenance": value.provenance,
        }

        def project(base: object) -> None:
            transaction = cast("Increment5Transaction", base)
            decision = transaction.decision_detail(value.decision_version_id)
            uncertainty = transaction.get_version(value.uncertainty_version_id)
            if (
                decision is None
                or decision.case_id != value.case_id
                or decision.configuration_id != value.configuration_id
                or decision.configuration_version_id != value.configuration_version_id
                or uncertainty is None
                or uncertainty.family != "uncertainty-classification"
                or uncertainty.content.get("classification") != "DECISION_LIMITING_UNCERTAINTY"
                or not transaction.actor_exists(value.owner_actor_id)
            ):
                raise DomainRuleViolation(
                    "Learning Item exact Decision/uncertainty binding mismatch"
                )
            if value.owner_assignment_version_id is not None:
                assignment = transaction.role_assignment_detail(value.owner_assignment_version_id)
                if (
                    assignment is None
                    or assignment.actor_id != value.owner_actor_id
                    or not assignment.accountable
                    or not self._assignment_current(
                        transaction,
                        value.owner_assignment_version_id,
                        effective_at=value.effective.start,
                        known_at=self._clock.now(),
                    )
                ):
                    raise DomainRuleViolation("Learning owner assignment is ineligible")
            for evidence_id in value.evidence_version_ids:
                evidence = transaction.get_version(evidence_id)
                if evidence is None or evidence.family != "evidence":
                    raise DomainRuleViolation("Learning output must link exact Evidence Version")
            if value.successor_decision_version_id is not None and (
                transaction.decision_detail(value.successor_decision_version_id) is None
            ):
                raise DomainRuleViolation("Learning successor Decision seam is invalid")
            transaction.add_learning_item(
                learning_item_id=value.learning_item_id,
                version_id=value.version_id,
                case_id=value.case_id,
                decision_version_id=value.decision_version_id,
                configuration_id=value.configuration_id,
                configuration_version_id=value.configuration_version_id,
                uncertainty_version_id=value.uncertainty_version_id,
                owner_actor_id=value.owner_actor_id,
                owner_assignment_version_id=value.owner_assignment_version_id,
                accountable_mechanism=value.accountable_mechanism,
                status=value.status.value,
                evidence_version_ids=value.evidence_version_ids,
                successor_decision_version_id=value.successor_decision_version_id,
            )

        return self._commit_version(
            meta=meta,
            record_id=value.learning_item_id,
            version_id=value.version_id,
            family="learning-item",
            scope=(
                f"case:{value.case_id}:decision-version:{value.decision_version_id}:"
                f"learning-item:{value.learning_item_id}"
            ),
            content=content,
            effective=value.effective,
            expected_version_id=value.expected_version_id,
            relationship_reason=value.relationship_reason,
            relationship_type=value.relationship_type,
            project=project,
            reason_outcome="DECISION_SPECIFIC_LEARNING_RECORDED_NO_AUTOMATIC_DECISION_EFFECT",
        )

    def _begin_intervention(
        self,
        meta: CommandMeta,
        *,
        case_id: RecordId,
        effective_at: datetime,
    ) -> LifecycleTransitionResult:
        recorded_at = self._clock.now()
        payload: dict[str, JsonValue] = {
            "case_id": str(case_id),
            "target_state": CaseLifecycleState.INTERVENTION_IN_PROGRESS.value,
            "effective_at": effective_at.isoformat(),
            "principal_id": meta.principal_id,
            "actor_id": meta.actor_id,
        }
        digest = canonical_command_digest(payload)
        with self._increment5_store.semantic_transaction() as transaction:
            replay = transaction.get_idempotency(meta.idempotency_scope, meta.idempotency_key)
            if replay is not None:
                if replay.digest != digest:
                    raise DomainRuleViolation("IDEMPOTENCY KEY REUSE CONFLICT")
                return LifecycleTransitionResult(
                    True,
                    CaseLifecycleState.INTERVENTION_IN_PROGRESS,
                    "TRANSITION COMMITTED",
                    replay.outcome.status_event_ids[0],
                )
            current, case_version_id = self._case_state_in_transaction(
                transaction,
                case_id=case_id,
                effective_at=effective_at,
                known_at=recorded_at,
            )
            if current is not CaseLifecycleState.DECIDED:
                return LifecycleTransitionResult(
                    False, current, "Intervention may begin only from DECIDED"
                )
            event = StatusEvent(
                EventId.new(),
                case_version_id,
                current.value,
                CaseLifecycleState.INTERVENTION_IN_PROGRESS.value,
                recorded_at,
                effective_at,
                meta.actor_id or meta.actor_resolution.value,
                "authorized Decision identifies material Intervention work",
            )
            transaction.add_status_event(event)
            audit = AuditFact(
                AuditId.new(),
                meta.principal_id,
                meta.actor_id,
                meta.actor_resolution,
                "BEGIN_INCREMENT_5_INTERVENTION",
                "COMMITTED",
                meta.command_id,
                meta.idempotency_scope,
                meta.idempotency_key,
                meta.correlation_id,
                meta.causation_id,
                case_id,
                (case_version_id,),
                current.value,
                current.value,
                effective_at,
                recorded_at,
                ("Intervention workflow started; target operation remains unauthorized",),
                digest,
            )
            transaction.add_audit(audit)
            outcome = CommandOutcome(
                str(meta.command_id),
                str(case_id),
                (),
                (str(event.event_id),),
                (),
                str(audit.audit_id),
            )
            transaction.add_idempotency(
                IdempotencyFact(
                    meta.idempotency_scope,
                    meta.idempotency_key,
                    digest,
                    str(meta.command_id),
                    outcome,
                    recorded_at,
                )
            )
            return LifecycleTransitionResult(
                True,
                CaseLifecycleState.INTERVENTION_IN_PROGRESS,
                "TRANSITION COMMITTED",
                str(event.event_id),
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
        if target_state is CaseLifecycleState.INTERVENTION_IN_PROGRESS:
            return self._begin_intervention(meta, case_id=case_id, effective_at=effective_at)
        if target_state is CaseLifecycleState.OPERATING_OBSERVING:
            return LifecycleTransitionResult(
                False,
                self.current_lifecycle_state(case_id=case_id, effective_at=effective_at),
                "OPERATING_OBSERVING requires atomic Increment 5 activation",
            )
        return super().transition_case(
            meta,
            case_id=case_id,
            target_state=target_state,
            effective_at=effective_at,
            use_context=use_context,
            purpose=purpose,
        )

    def _authorized_decisions_in_transaction(
        self,
        transaction: Increment5Transaction,
        *,
        case_id: RecordId,
        configuration_version_id: RecordVersionId,
        effective_at: datetime,
        known_at: datetime,
    ) -> tuple[AuthorizedDecisionFound, ...]:
        found: list[AuthorizedDecisionFound] = []
        for decision_version_id in transaction.decision_versions(
            case_id=case_id, configuration_version_id=configuration_version_id
        ):
            decision = transaction.decision_detail(decision_version_id)
            if decision is None or not self._is_current(
                transaction,
                decision_version_id,
                effective_at=effective_at,
                known_at=known_at,
            ):
                continue
            authorized = any(
                event.target_version_id == decision_version_id
                and event.new_status == DecisionStatus.AUTHORIZED.value
                and event.effective_at <= effective_at
                and event.recorded_at <= known_at
                for event in transaction.get_history(decision.decision_id).status_events
            )
            if not authorized:
                continue
            bases = tuple(
                item
                for item in transaction.authorization_basis_versions(
                    decision_version_id=decision_version_id
                )
                if self._is_current(
                    transaction,
                    item,
                    effective_at=effective_at,
                    known_at=known_at,
                )
            )
            if len(bases) == 1:
                found.append(
                    AuthorizedDecisionFound(
                        decision_version_id,
                        decision.boundary_snapshot_version_id,
                        bases[0],
                    )
                )
            elif len(bases) > 1:
                found.extend(
                    AuthorizedDecisionFound(
                        decision_version_id,
                        decision.boundary_snapshot_version_id,
                        basis,
                    )
                    for basis in bases
                )
        return tuple(found)

    def _validate_activation_authority(
        self,
        transaction: Increment5Transaction,
        *,
        request: ActivationRequest,
        known_at: datetime,
    ) -> None:
        decision = transaction.decision_detail(request.decision_version_id)
        basis = transaction.authorization_basis_detail(
            request.decision_authorization_basis_version_id
        )
        if decision is None or basis is None:
            raise DomainRuleViolation("exact Decision Authorization Basis is absent")
        if (
            basis.decision_version_id != request.decision_version_id
            or basis.configuration_version_id != request.configuration_version_id
            or basis.authorized_scope != request.authority_scope
            or request.operating_state not in basis.operating_state_coverage
        ):
            raise DomainRuleViolation("activation authority does not cover exact target")
        if not request.authority_effective.contains(request.effective_at):
            raise DomainRuleViolation("activation authority is not effective")
        if request.authority_kind is ActivationAuthorityKind.DECISION_AUTHORITY:
            if (
                request.authority_actor_id is None
                or request.authority_assignment_version_id is None
                or request.preauthorized_mechanism_version_id is not None
            ):
                raise DomainRuleViolation("Decision Authority activation path is incomplete")
            self._validate_exact_decision_authority(
                transaction,
                decision=decision,
                actor_id=request.authority_actor_id,
                authority_assignment_version_id=(request.authority_assignment_version_id),
                authority_mechanism=None,
                authority_record_version_id=basis.authority_record_version_id,
                delegation_chain_version_ids=request.delegation_chain_version_ids,
                authorized_scope=request.authority_scope,
                configuration_id=request.configuration_id,
                configuration_version_id=request.configuration_version_id,
                operating_state_coverage=(request.operating_state,),
                effective_at=request.effective_at,
                known_at=known_at,
            )
            return
        if (
            request.authority_actor_id is not None
            or request.authority_assignment_version_id is not None
            or request.preauthorized_mechanism_version_id is None
            or request.delegation_chain_version_ids
        ):
            raise DomainRuleViolation("organizational activation mechanism path is incomplete")
        mechanism = transaction.preauthorized_activation_mechanism(
            basis_version_id=request.decision_authorization_basis_version_id,
            mechanism_version_id=request.preauthorized_mechanism_version_id,
        )
        if mechanism is None:
            raise DomainRuleViolation("pre-authorized organizational mechanism is absent")
        effective_from = from_epoch_microseconds(cast("int", mechanism["effective_from_us"]))
        effective_to_value = cast("int | None", mechanism["effective_to_us"])
        effective_to = (
            from_epoch_microseconds(effective_to_value) if effective_to_value is not None else None
        )
        if not EffectiveInterval(effective_from, effective_to).contains(request.effective_at):
            raise DomainRuleViolation("pre-authorized organizational mechanism is not effective")
        if (
            cast("str", mechanism["scope"]) != request.authority_scope
            or tuple(
                cast(
                    "list[str]",
                    json.loads(cast("str", mechanism["limits_json"])),
                )
            )
            != request.authority_limits
            or not cast("str", mechanism["rule_version"]).strip()
            or not cast("str", mechanism["authority_source"]).strip()
        ):
            raise DomainRuleViolation(
                "pre-authorized mechanism rule/version/scope/authority provenance mismatch"
            )

    def activate_target(self, meta: CommandMeta, request: ActivationRequest) -> ActivationResult:
        effective_at = require_utc(request.effective_at)
        recorded_at = self._clock.now()
        knowledge_time = require_utc(request.known_at or recorded_at)
        if knowledge_time > recorded_at:
            raise DomainRuleViolation("activation knowledge cutoff cannot be in the future")
        if not request.operating_state.strip() or not request.rationale.strip():
            raise DomainRuleViolation("activation operating state and rationale are required")
        payload: dict[str, JsonValue] = {
            "basis_id": str(request.basis_id),
            "basis_version_id": str(request.basis_version_id),
            "authorization_id": str(request.authorization_id),
            "authorization_version_id": str(request.authorization_version_id),
            "activation_event_id": request.activation_event_id,
            "case_id": str(request.case_id),
            "decision_version_id": str(request.decision_version_id),
            "configuration_id": str(request.configuration_id),
            "configuration_version_id": str(request.configuration_version_id),
            "boundary_snapshot_version_id": str(request.boundary_snapshot_version_id),
            "operating_state": request.operating_state,
            "authority_kind": request.authority_kind.value,
            "authority_actor_id": (
                str(request.authority_actor_id) if request.authority_actor_id else None
            ),
            "authority_assignment_version_id": (
                str(request.authority_assignment_version_id)
                if request.authority_assignment_version_id
                else None
            ),
            "preauthorized_mechanism_version_id": (
                str(request.preauthorized_mechanism_version_id)
                if request.preauthorized_mechanism_version_id
                else None
            ),
            "decision_authorization_basis_version_id": str(
                request.decision_authorization_basis_version_id
            ),
            "authority_scope": request.authority_scope,
            "authority_limits": list(request.authority_limits),
            "delegation_chain_version_ids": [
                str(item) for item in request.delegation_chain_version_ids
            ],
            "rationale": request.rationale,
            "effective_at": effective_at.isoformat(),
            "knowledge_cutoff": knowledge_time.isoformat(),
            "principal_id": meta.principal_id,
            "actor_id": meta.actor_id,
        }
        digest = canonical_command_digest(payload)
        with self._increment5_store.semantic_transaction() as transaction:
            replay = transaction.get_idempotency(meta.idempotency_scope, meta.idempotency_key)
            if replay is not None:
                if replay.digest != digest:
                    raise DomainRuleViolation("IDEMPOTENCY KEY REUSE CONFLICT")
                return ActivationResult(
                    True,
                    "TARGET ACTIVATION COMMITTED",
                    RecordVersionId.parse(replay.outcome.version_ids[0]),
                    RecordVersionId.parse(replay.outcome.version_ids[1]),
                    replay.outcome.status_event_ids[0],
                )
            current_state, case_version_id = self._case_state_in_transaction(
                transaction,
                case_id=request.case_id,
                effective_at=effective_at,
                known_at=knowledge_time,
            )
            if current_state not in {
                CaseLifecycleState.DECIDED,
                CaseLifecycleState.INTERVENTION_IN_PROGRESS,
            }:
                raise DomainRuleViolation("target activation lifecycle source is ineligible")
            authorized = self._authorized_decisions_in_transaction(
                transaction,
                case_id=request.case_id,
                configuration_version_id=request.configuration_version_id,
                effective_at=effective_at,
                known_at=knowledge_time,
            )
            if len(authorized) != 1:
                reason = (
                    "AUTHORIZED DECISION NOT ESTABLISHED"
                    if not authorized
                    else "AUTHORIZED DECISION CONFLICT — UNRESOLVED"
                )
                raise DomainRuleViolation(reason)
            selected_decision = authorized[0]
            if (
                selected_decision.decision_version_id != request.decision_version_id
                or selected_decision.boundary_snapshot_version_id
                != request.boundary_snapshot_version_id
                or selected_decision.authorization_basis_version_id
                != request.decision_authorization_basis_version_id
            ):
                raise DomainRuleViolation("activation exact authorized Decision basis mismatch")
            decision = transaction.decision_detail(request.decision_version_id)
            boundary = transaction.boundary_snapshot_detail(request.boundary_snapshot_version_id)
            context = transaction.configuration_version_context(request.configuration_version_id)
            if (
                decision is None
                or boundary is None
                or context is None
                or decision.case_id != request.case_id
                or decision.configuration_id != request.configuration_id
                or decision.configuration_version_id != request.configuration_version_id
                or decision.boundary_snapshot_version_id != request.boundary_snapshot_version_id
                or decision.operating_state != request.operating_state
                or boundary.status != "finalized"
                or boundary.configuration_version_id != request.configuration_version_id
                or context.owning_case_id != request.case_id
                or not self._is_current(
                    transaction,
                    request.boundary_snapshot_version_id,
                    effective_at=effective_at,
                    known_at=knowledge_time,
                )
            ):
                raise DomainRuleViolation("target Configuration/Boundary alignment failed")
            evaluation = self._evaluate_prerequisites_in_transaction(
                transaction,
                decision_version_id=request.decision_version_id,
                configuration_version_id=request.configuration_version_id,
                effective_at=effective_at,
                known_at=knowledge_time,
            )
            if (
                evaluation.result
                not in {
                    AggregatePrerequisiteResult.SATISFIED,
                    AggregatePrerequisiteResult.NOT_REQUIRED,
                }
                or evaluation.obligation_set_version_id is None
            ):
                raise DomainRuleViolation(
                    f"target prerequisites block activation: {evaluation.result.value}"
                )
            self._validate_activation_authority(
                transaction, request=request, known_at=knowledge_time
            )
            interval = EffectiveInterval(effective_at)
            basis_content: dict[str, JsonValue] = {
                "decision_version_id": str(request.decision_version_id),
                "configuration_version_id": str(request.configuration_version_id),
                "boundary_snapshot_version_id": str(request.boundary_snapshot_version_id),
                "obligation_set_version_id": str(evaluation.obligation_set_version_id),
                "aggregate_result": evaluation.result.value,
                "obligations": [
                    {
                        "obligation_version_id": str(item.obligation_version_id),
                        "result": item.result.value,
                        "intervention_version_id": (
                            str(item.intervention_version_id)
                            if item.intervention_version_id
                            else None
                        ),
                        "completion_result_version_id": (
                            str(item.completion_result_version_id)
                            if item.completion_result_version_id
                            else None
                        ),
                        "completion_acceptance_version_id": (
                            str(item.completion_acceptance_version_id)
                            if item.completion_acceptance_version_id
                            else None
                        ),
                        "replacement_version_id": (
                            str(item.replacement_version_id)
                            if item.replacement_version_id
                            else None
                        ),
                        "reuse_determination_version_id": (
                            str(item.reuse_determination_version_id)
                            if item.reuse_determination_version_id
                            else None
                        ),
                        "diagnostics": list(item.diagnostics),
                    }
                    for item in evaluation.obligations
                ],
                "effective_at": effective_at.isoformat(),
                "recorded_at": recorded_at.isoformat(),
                "knowledge_cutoff": knowledge_time.isoformat(),
                "diagnostics": list(evaluation.diagnostics),
            }
            authorization_content: dict[str, JsonValue] = {
                "decision_version_id": str(request.decision_version_id),
                "configuration_version_id": str(request.configuration_version_id),
                "operating_state": request.operating_state,
                "boundary_snapshot_version_id": str(request.boundary_snapshot_version_id),
                "prerequisite_basis_version_id": str(request.basis_version_id),
                "authority_kind": request.authority_kind.value,
                "authority_actor_id": (
                    str(request.authority_actor_id) if request.authority_actor_id else None
                ),
                "authority_assignment_version_id": (
                    str(request.authority_assignment_version_id)
                    if request.authority_assignment_version_id
                    else None
                ),
                "mechanism_version_id": (
                    str(request.preauthorized_mechanism_version_id)
                    if request.preauthorized_mechanism_version_id
                    else None
                ),
                "decision_authorization_basis_version_id": str(
                    request.decision_authorization_basis_version_id
                ),
                "authority_scope": request.authority_scope,
                "authority_limits": list(request.authority_limits),
                "authority_effective_from": request.authority_effective.start.isoformat(),
                "authority_effective_to": (
                    request.authority_effective.end.isoformat()
                    if request.authority_effective.end
                    else None
                ),
                "rationale": request.rationale,
            }
            transaction.add_version(
                FinalizedRecordVersion(
                    request.basis_id,
                    request.basis_version_id,
                    "prerequisite-evaluation-basis",
                    (
                        f"decision-version:{request.decision_version_id}:"
                        f"configuration-version:{request.configuration_version_id}"
                    ),
                    canonical_json(basis_content),
                    recorded_at,
                    interval,
                    meta.actor_id or meta.principal_id,
                )
            )
            transaction.add_prerequisite_evaluation_basis(
                basis_id=request.basis_id,
                version_id=request.basis_version_id,
                decision_version_id=request.decision_version_id,
                configuration_version_id=request.configuration_version_id,
                boundary_snapshot_version_id=request.boundary_snapshot_version_id,
                obligation_set_version_id=evaluation.obligation_set_version_id,
                aggregate_result=evaluation.result.value,
                effective_at=effective_at,
                knowledge_cutoff=knowledge_time,
            )
            for ordinal, item in enumerate(evaluation.obligations):
                transaction.add_prerequisite_basis_item(
                    basis_version_id=request.basis_version_id,
                    ordinal=ordinal,
                    obligation_version_id=item.obligation_version_id,
                    intervention_version_id=item.intervention_version_id,
                    completion_result_version_id=item.completion_result_version_id,
                    completion_acceptance_version_id=(item.completion_acceptance_version_id),
                    replacement_version_id=item.replacement_version_id,
                    reuse_determination_version_id=(item.reuse_determination_version_id),
                    result=item.result.value,
                    diagnostics=item.diagnostics,
                )
            transaction.add_version(
                FinalizedRecordVersion(
                    request.authorization_id,
                    request.authorization_version_id,
                    "activation-authorization",
                    (
                        f"decision-version:{request.decision_version_id}:"
                        f"configuration-version:{request.configuration_version_id}"
                    ),
                    canonical_json(authorization_content),
                    recorded_at,
                    interval,
                    meta.actor_id or meta.principal_id,
                )
            )
            transaction.add_activation_authorization(
                authorization_id=request.authorization_id,
                version_id=request.authorization_version_id,
                decision_version_id=request.decision_version_id,
                configuration_version_id=request.configuration_version_id,
                operating_state=request.operating_state,
                boundary_snapshot_version_id=request.boundary_snapshot_version_id,
                prerequisite_basis_version_id=request.basis_version_id,
                authority_kind=request.authority_kind.value,
                authority_actor_id=request.authority_actor_id,
                authority_assignment_version_id=(request.authority_assignment_version_id),
                mechanism_version_id=request.preauthorized_mechanism_version_id,
                decision_authorization_basis_version_id=(
                    request.decision_authorization_basis_version_id
                ),
                authority_scope=request.authority_scope,
                authority_limits=request.authority_limits,
                authority_effective_from=request.authority_effective.start,
                authority_effective_to=request.authority_effective.end,
                delegation_chain_version_ids=request.delegation_chain_version_ids,
                activation_effective_at=effective_at,
            )
            lifecycle_event = StatusEvent(
                EventId.new(),
                case_version_id,
                current_state.value,
                CaseLifecycleState.OPERATING_OBSERVING.value,
                recorded_at,
                effective_at,
                meta.actor_id or meta.actor_resolution.value,
                (
                    f"Activation Authorization {request.authorization_version_id}; "
                    f"Prerequisite Evaluation Basis {request.basis_version_id}"
                ),
            )
            transaction.add_status_event(lifecycle_event)
            transaction.add_target_activation_event(
                event_id=request.activation_event_id,
                case_id=request.case_id,
                decision_version_id=request.decision_version_id,
                configuration_version_id=request.configuration_version_id,
                boundary_snapshot_version_id=request.boundary_snapshot_version_id,
                prerequisite_basis_version_id=request.basis_version_id,
                activation_authorization_version_id=request.authorization_version_id,
                operating_state=request.operating_state,
                lifecycle_event_id=str(lifecycle_event.event_id),
                effective_at=effective_at,
                recorded_at=recorded_at,
                knowledge_cutoff=knowledge_time,
            )
            audit = AuditFact(
                AuditId.new(),
                meta.principal_id,
                meta.actor_id,
                meta.actor_resolution,
                "ACTIVATE_TARGET_CONFIGURATION",
                "COMMITTED",
                meta.command_id,
                meta.idempotency_scope,
                meta.idempotency_key,
                meta.correlation_id,
                meta.causation_id,
                request.case_id,
                (
                    case_version_id,
                    request.basis_version_id,
                    request.authorization_version_id,
                ),
                current_state.value,
                current_state.value,
                effective_at,
                recorded_at,
                (
                    evaluation.result.value,
                    request.authority_kind.value,
                    "ACTIVATION_GUARD_BASIS_AUTHORIZATION_EVENT_TRANSITION_ATOMIC",
                ),
                digest,
            )
            transaction.add_audit(audit)
            outcome = CommandOutcome(
                str(meta.command_id),
                str(request.case_id),
                (str(request.basis_version_id), str(request.authorization_version_id)),
                (str(lifecycle_event.event_id),),
                (),
                str(audit.audit_id),
            )
            transaction.add_idempotency(
                IdempotencyFact(
                    meta.idempotency_scope,
                    meta.idempotency_key,
                    digest,
                    str(meta.command_id),
                    outcome,
                    recorded_at,
                )
            )
            return ActivationResult(
                True,
                "TARGET ACTIVATION COMMITTED",
                request.basis_version_id,
                request.authorization_version_id,
                str(lifecycle_event.event_id),
            )
