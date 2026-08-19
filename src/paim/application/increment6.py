"""Increment 6 Trigger, Reassessment, and Interim Disposition commands."""

from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import datetime
from typing import cast

from paim.application.increment2 import DomainPreconditionFailed, DomainRuleViolation
from paim.application.increment5 import Increment5ApplicationService
from paim.audit import AuditFact
from paim.domain.increment4 import BoundaryVerificationMode, DecisionStatus
from paim.domain.increment6 import (
    AccountabilityFunction,
    DecisionConfirmationVersionInput,
    EffectiveOperatingDisposition,
    InterimOperatingDispositionVersionInput,
    ReassessmentCompletionResult,
    ReassessmentDeterminationConflict,
    ReassessmentDeterminationFound,
    ReassessmentDeterminationKind,
    ReassessmentDeterminationNotEstablished,
    ReassessmentDeterminationOutcome,
    ReassessmentDeterminationSelection,
    ReassessmentDeterminationVersionInput,
    ReassessmentMechanismVersionInput,
    ReassessmentOverlap,
    ReassessmentStatus,
    ReassessmentTerminationRequest,
    ReassessmentVersionInput,
    SuccessorDecisionCompletionRequest,
    TriggerCoverage,
    TriggerCoverageState,
    TriggerDeterminationConflict,
    TriggerDeterminationFound,
    TriggerDeterminationNotEstablished,
    TriggerDeterminationOutcome,
    TriggerDeterminationSelection,
    TriggerDeterminationVersionInput,
    TriggerSourceKind,
    TriggerVersionInput,
)
from paim.domain.increment6_ports import Increment6Store, Increment6Transaction
from paim.domain.models import CommandMeta, RoleTargetType
from paim.integrity import (
    AuditId,
    EventId,
    RecordId,
    RecordVersionId,
    RelationshipId,
    RelationshipType,
    SelectionConflict,
    SelectionFound,
    SelectionQuery,
    StatusEvent,
    VersionRelationship,
)
from paim.integrity.commands import canonical_command_digest
from paim.integrity.records import FinalizedRecordVersion, JsonValue, canonical_json
from paim.integrity.time import Clock, EffectiveInterval, from_epoch_microseconds, require_utc
from paim.persistence.ports import CommandOutcome, IdempotencyFact

_ACTIVE_REASSESSMENT_STATUSES = frozenset(
    {
        ReassessmentStatus.OPEN.value,
        ReassessmentStatus.ANALYSIS_IN_PROGRESS.value,
        ReassessmentStatus.AWAITING_DECISION_AUTHORITY.value,
        ReassessmentStatus.BLOCKED_CONFLICT.value,
    }
)
_REQUIRING_OUTCOMES = frozenset(
    {
        TriggerDeterminationOutcome.REASSESSMENT_REQUIRED,
        TriggerDeterminationOutcome.IMMEDIATE_DISPOSITION_AND_REASSESSMENT,
    }
)


class Increment6ApplicationService(Increment5ApplicationService):
    """Specification-bounded synchronous Increment 6 application boundary."""

    def __init__(self, store: Increment6Store, clock: Clock) -> None:
        super().__init__(store, clock)
        self._increment6_store = store

    @staticmethod
    def _exactly_one(
        assignment_version_id: RecordVersionId | None,
        mechanism_version_id: RecordVersionId | None,
    ) -> bool:
        return (assignment_version_id is not None) != (mechanism_version_id is not None)

    @staticmethod
    def _json_tuple(row: dict[str, object], key: str) -> tuple[str, ...]:
        return tuple(cast("list[str]", json.loads(cast("str", row[key]))))

    @staticmethod
    def _json_text(values: Iterable[str]) -> list[JsonValue]:
        return [cast("JsonValue", item) for item in values]

    def _current_version_for_record(
        self,
        transaction: Increment6Transaction,
        *,
        record_id: RecordId,
        family: str,
        scope: str,
        effective_at: datetime,
        known_at: datetime,
    ) -> RecordVersionId | None:
        result = transaction.select_current(
            SelectionQuery(
                family=family,
                scope=scope,
                effective_at=effective_at,
                known_at=known_at,
                record_id=record_id,
            )
        )
        return result.candidate.version_id if isinstance(result, SelectionFound) else None

    def _validate_context(
        self,
        transaction: Increment6Transaction,
        *,
        case_id: RecordId,
        decision_version_id: RecordVersionId,
        configuration_version_id: RecordVersionId,
    ) -> None:
        decision = transaction.decision_detail(decision_version_id)
        configuration = transaction.configuration_version_context(configuration_version_id)
        if (
            decision is None
            or configuration is None
            or decision.case_id != case_id
            or decision.configuration_version_id != configuration_version_id
            or configuration.owning_case_id != case_id
        ):
            raise DomainRuleViolation("exact Case/Decision/Configuration context mismatch")

    def _applicable_targets(
        self,
        transaction: Increment6Transaction,
        *,
        case_id: RecordId,
        decision_version_id: RecordVersionId,
        configuration_version_id: RecordVersionId,
        intervention_version_id: RecordVersionId | None = None,
    ) -> tuple[tuple[str, str], ...]:
        decision = transaction.decision_detail(decision_version_id)
        configuration = transaction.configuration_version_context(configuration_version_id)
        if decision is None or configuration is None:
            return ()
        targets = [
            (RoleTargetType.DECISION.value, str(decision.decision_id)),
            (RoleTargetType.CONFIGURATION.value, str(configuration.configuration_id)),
            (RoleTargetType.CASE.value, str(case_id)),
        ]
        if intervention_version_id is not None:
            intervention = transaction.intervention_detail(intervention_version_id)
            if intervention is None:
                raise DomainRuleViolation("exact source Intervention Version does not exist")
            targets.append((RoleTargetType.INTERVENTION.value, str(intervention.intervention_id)))
        return tuple(targets)

    def _eligible_assignments(
        self,
        transaction: Increment6Transaction,
        *,
        function: AccountabilityFunction,
        targets: tuple[tuple[str, str], ...],
        effective_at: datetime,
        known_at: datetime,
    ) -> tuple[RecordVersionId, ...]:
        assignment_ids = transaction.role_assignment_records(role=function.value, targets=targets)
        found: list[RecordVersionId] = []
        for assignment_id in assignment_ids:
            history = transaction.get_history(assignment_id)
            if not history.versions:
                continue
            exemplar = next(iter(history.versions))
            current = transaction.select_current(
                SelectionQuery(
                    family="role-assignment",
                    scope=exemplar.scope,
                    effective_at=effective_at,
                    known_at=known_at,
                    record_id=assignment_id,
                )
            )
            candidates = (
                (current.candidate,)
                if isinstance(current, SelectionFound)
                else tuple(current.candidates)
                if isinstance(current, SelectionConflict)
                else ()
            )
            for candidate in candidates:
                detail = transaction.role_assignment_detail(candidate.version_id)
                if detail is not None and detail.accountable:
                    found.append(candidate.version_id)
        return tuple(found)

    def _validate_function_accountability(
        self,
        transaction: Increment6Transaction,
        *,
        function: AccountabilityFunction,
        case_id: RecordId,
        decision_version_id: RecordVersionId,
        configuration_version_id: RecordVersionId,
        actor_id: RecordId,
        assignment_version_id: RecordVersionId | None,
        mechanism_version_id: RecordVersionId | None,
        delegation_chain_version_ids: tuple[RecordVersionId, ...],
        effective_at: datetime,
        known_at: datetime,
        intervention_version_id: RecordVersionId | None = None,
    ) -> None:
        if not self._exactly_one(assignment_version_id, mechanism_version_id):
            raise DomainRuleViolation(f"{function.value.upper()} ACCOUNTABILITY NOT ESTABLISHED")
        targets = self._applicable_targets(
            transaction,
            case_id=case_id,
            decision_version_id=decision_version_id,
            configuration_version_id=configuration_version_id,
            intervention_version_id=intervention_version_id,
        )
        eligible = self._eligible_assignments(
            transaction,
            function=function,
            targets=targets,
            effective_at=effective_at,
            known_at=known_at,
        )
        if mechanism_version_id is not None:
            mechanism = transaction.reassessment_mechanism_detail(mechanism_version_id)
            if mechanism is None:
                raise DomainRuleViolation("GOVERNED MECHANISM NOT ESTABLISHED")
            mechanism_record = transaction.get_version(mechanism_version_id)
            if mechanism_record is None:
                raise DomainRuleViolation("GOVERNED MECHANISM NOT ESTABLISHED")
            current = self._current_version_for_record(
                transaction,
                record_id=mechanism_record.record_id,
                family="reassessment-accountability-mechanism",
                scope=mechanism_record.scope,
                effective_at=effective_at,
                known_at=known_at,
            )
            exact = (
                current == mechanism_version_id
                and mechanism["function"] == function.value
                and mechanism["case_id"] == str(case_id)
                and mechanism["decision_version_id"] == str(decision_version_id)
                and mechanism["configuration_version_id"] == str(configuration_version_id)
                and mechanism["accountable_actor_id"] == str(actor_id)
                and bool(cast("str", mechanism["rule_version"]).strip())
                and bool(cast("str", mechanism["authority_scope"]).strip())
                and bool(cast("str", mechanism["authority_source"]).strip())
            )
            if intervention_version_id is not None:
                exact = exact and mechanism["intervention_version_id"] == str(
                    intervention_version_id
                )
            if not exact:
                raise DomainRuleViolation("GOVERNED MECHANISM SCOPE OR VERSION MISMATCH")
            if eligible:
                raise DomainRuleViolation(
                    f"{function.value.upper()} ACCOUNTABILITY CONFLICT — UNRESOLVED"
                )
            if delegation_chain_version_ids:
                raise DomainRuleViolation("mechanism path cannot carry assignment delegation")
            return
        assert assignment_version_id is not None
        expected_assignments = set(delegation_chain_version_ids or (assignment_version_id,))
        if not eligible or set(eligible) != expected_assignments:
            reason = (
                f"{function.value.upper()} ACCOUNTABILITY NOT ESTABLISHED"
                if not eligible
                else f"{function.value.upper()} ACCOUNTABILITY CONFLICT — UNRESOLVED"
            )
            raise DomainRuleViolation(reason)
        detail = transaction.role_assignment_detail(assignment_version_id)
        if detail is None or detail.actor_id != actor_id or detail.role != function.value:
            raise DomainRuleViolation("accountable actor/function mismatch")
        if detail.delegated_from_version_id is not None and not delegation_chain_version_ids:
            raise DomainRuleViolation("delegated accountability requires exact delegation chain")
        if delegation_chain_version_ids:
            if delegation_chain_version_ids[-1] != assignment_version_id:
                raise DomainRuleViolation("delegation chain must terminate at accountable assignee")
            previous: RecordVersionId | None = None
            for link_id in delegation_chain_version_ids:
                link = transaction.role_assignment_detail(link_id)
                if (
                    link is None
                    or not link.accountable
                    or link.role != function.value
                    or (link.target_type.value, link.target_id) not in targets
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

    def commit_reassessment_mechanism(
        self, meta: CommandMeta, value: ReassessmentMechanismVersionInput
    ) -> CommandOutcome:
        if not all(
            item.strip()
            for item in (value.rule_version, value.authority_scope, value.authority_source)
        ):
            raise DomainRuleViolation("genuine mechanism requires rule/version/scope/authority")

        def project(base: object) -> None:
            transaction = cast("Increment6Transaction", base)
            self._validate_context(
                transaction,
                case_id=value.case_id,
                decision_version_id=value.decision_version_id,
                configuration_version_id=value.configuration_version_id,
            )
            if value.intervention_version_id is not None:
                intervention = transaction.intervention_detail(value.intervention_version_id)
                if (
                    intervention is None
                    or intervention.case_id != value.case_id
                    or intervention.decision_version_id != value.decision_version_id
                    or intervention.configuration_version_id != value.configuration_version_id
                ):
                    raise DomainRuleViolation(
                        "governed mechanism source Intervention context mismatch"
                    )
            if not transaction.actor_exists(value.accountable_actor_id):
                raise DomainRuleViolation("mechanism accountable PAIM actor does not exist")
            transaction.add_reassessment_mechanism(
                mechanism_id=value.mechanism_id,
                version_id=value.version_id,
                function=value.function.value,
                case_id=value.case_id,
                decision_version_id=value.decision_version_id,
                configuration_version_id=value.configuration_version_id,
                intervention_version_id=value.intervention_version_id,
                accountable_actor_id=value.accountable_actor_id,
                rule_version=value.rule_version,
                authority_scope=value.authority_scope,
                authority_source=value.authority_source,
                limits=value.limits,
            )

        content: dict[str, JsonValue] = {
            "function": value.function.value,
            "case_id": str(value.case_id),
            "decision_version_id": str(value.decision_version_id),
            "configuration_version_id": str(value.configuration_version_id),
            "intervention_version_id": (
                str(value.intervention_version_id) if value.intervention_version_id else None
            ),
            "accountable_actor_id": str(value.accountable_actor_id),
            "rule_version": value.rule_version,
            "authority_scope": value.authority_scope,
            "authority_source": value.authority_source,
            "limits": self._json_text(value.limits),
        }
        return self._commit_version(
            meta=meta,
            record_id=value.mechanism_id,
            version_id=value.version_id,
            family="reassessment-accountability-mechanism",
            scope=(
                f"function:{value.function.value}:case:{value.case_id}:"
                f"decision-version:{value.decision_version_id}:"
                f"configuration-version:{value.configuration_version_id}"
            ),
            content=content,
            effective=value.effective,
            expected_version_id=value.expected_version_id,
            relationship_reason=value.relationship_reason,
            relationship_type=value.relationship_type,
            project=project,
            reason_outcome="INCREMENT_6_GENUINE_GOVERNED_MECHANISM",
        )

    def commit_trigger(self, meta: CommandMeta, value: TriggerVersionInput) -> CommandOutcome:
        require_utc(value.source_knowledge_at)
        if not (
            value.trigger_type.strip()
            and value.management_question.strip()
            and value.source_family.strip()
            and value.source_record_id.strip()
            and value.source_version_id.strip()
            and value.source_event_id.strip()
            and value.description.strip()
            and value.rationale.strip()
        ):
            raise DomainRuleViolation(
                "Trigger identity, source, question, and rationale are required"
            )
        if value.source_knowledge_at > self._clock.now():
            raise DomainRuleViolation("Trigger source knowledge cutoff cannot be in the future")
        if value.source_kind is TriggerSourceKind.HUMAN_EXTERNAL and not (
            value.source_system and value.source_actor
        ):
            raise DomainRuleViolation(
                "external Trigger requires source system and actor provenance"
            )

        def project(base: object) -> None:
            transaction = cast("Increment6Transaction", base)
            self._validate_context(
                transaction,
                case_id=value.case_id,
                decision_version_id=value.decision_version_id,
                configuration_version_id=value.configuration_version_id,
            )
            if value.source_kind is TriggerSourceKind.PAIM_RECORD:
                try:
                    source_record_id = RecordId.parse(value.source_record_id)
                    source_version_id = RecordVersionId.parse(value.source_version_id)
                except ValueError as error:
                    raise DomainRuleViolation(
                        "PAIM Trigger source requires exact stable and Version identifiers"
                    ) from error
                source = transaction.get_version(source_version_id)
                if (
                    source is None
                    or source.record_id != source_record_id
                    or source.family != value.source_family
                    or source.recorded_at > value.source_knowledge_at
                ):
                    raise DomainRuleViolation("exact PAIM Trigger source is not established")
            if value.expected_version_id is not None:
                predecessor = transaction.trigger_detail(value.expected_version_id)
                if predecessor is None or any(
                    predecessor[key] != expected
                    for key, expected in (
                        ("trigger_id", str(value.trigger_id)),
                        ("case_id", str(value.case_id)),
                        ("source_event_id", value.source_event_id),
                        ("management_question", value.management_question),
                    )
                ):
                    raise DomainRuleViolation(
                        "Trigger successor must retain occurrence, Case, and management question"
                    )
                if predecessor["source_version_id"] == value.source_version_id:
                    raise DomainRuleViolation(
                        "Trigger successor requires a material source Version change"
                    )
            transaction.add_trigger(
                trigger_id=value.trigger_id,
                version_id=value.version_id,
                case_id=value.case_id,
                decision_version_id=value.decision_version_id,
                configuration_version_id=value.configuration_version_id,
                trigger_type=value.trigger_type,
                management_question=value.management_question,
                affected_scope=sorted(value.affected_scope),
                source_kind=value.source_kind.value,
                source_family=value.source_family,
                source_record_id=value.source_record_id,
                source_version_id=value.source_version_id,
                source_system=value.source_system,
                source_actor=value.source_actor,
                source_event_id=value.source_event_id,
                source_knowledge_at=value.source_knowledge_at,
                withdrawn=value.withdrawn,
            )

        content: dict[str, JsonValue] = {
            "case_id": str(value.case_id),
            "decision_version_id": str(value.decision_version_id),
            "configuration_version_id": str(value.configuration_version_id),
            "trigger_type": value.trigger_type,
            "management_question": value.management_question,
            "affected_scope": self._json_text(sorted(value.affected_scope)),
            "source_kind": value.source_kind.value,
            "source_family": value.source_family,
            "source_record_id": value.source_record_id,
            "source_version_id": value.source_version_id,
            "source_system": value.source_system,
            "source_actor": value.source_actor,
            "source_event_id": value.source_event_id,
            "source_knowledge_at": value.source_knowledge_at.isoformat(),
            "description": value.description,
            "rationale": value.rationale,
            "affected_references": self._json_text(value.affected_references),
            "provenance": value.provenance,
            "withdrawn": value.withdrawn,
        }
        return self._commit_version(
            meta=meta,
            record_id=value.trigger_id,
            version_id=value.version_id,
            family="reassessment-trigger",
            scope=f"case:{value.case_id}:trigger:{value.trigger_id}",
            content=content,
            effective=value.effective,
            expected_version_id=value.expected_version_id,
            relationship_reason=value.relationship_reason,
            relationship_type=value.relationship_type,
            project=project,
            reason_outcome="INCREMENT_6_CASE_SCOPED_TRIGGER_VALID",
        )

    def commit_trigger_determination(
        self, meta: CommandMeta, value: TriggerDeterminationVersionInput
    ) -> CommandOutcome:
        if not value.rationale.strip():
            raise DomainRuleViolation("Trigger Determination rationale is required")
        recorded_at = self._clock.now()

        def project(base: object) -> None:
            transaction = cast("Increment6Transaction", base)
            trigger = transaction.trigger_detail(value.trigger_version_id)
            if trigger is None or any(
                trigger[key] != expected
                for key, expected in (
                    ("case_id", str(value.case_id)),
                    ("decision_version_id", str(value.decision_version_id)),
                    ("configuration_version_id", str(value.configuration_version_id)),
                )
            ):
                raise DomainRuleViolation("Trigger Determination exact context mismatch")
            source_intervention_version_id = (
                RecordVersionId.parse(cast("str", trigger["source_version_id"]))
                if trigger["source_kind"] == TriggerSourceKind.PAIM_RECORD.value
                and trigger["source_family"] == "intervention"
                else None
            )
            self._validate_function_accountability(
                transaction,
                function=AccountabilityFunction.TRIGGER_DETERMINER,
                case_id=value.case_id,
                decision_version_id=value.decision_version_id,
                configuration_version_id=value.configuration_version_id,
                actor_id=value.actor_id,
                assignment_version_id=value.accountable_assignment_version_id,
                mechanism_version_id=value.accountable_mechanism_version_id,
                delegation_chain_version_ids=value.delegation_chain_version_ids,
                effective_at=value.effective.start,
                known_at=recorded_at,
                intervention_version_id=source_intervention_version_id,
            )
            transaction.add_trigger_determination(
                determination_id=value.determination_id,
                version_id=value.version_id,
                trigger_version_id=value.trigger_version_id,
                case_id=value.case_id,
                decision_version_id=value.decision_version_id,
                configuration_version_id=value.configuration_version_id,
                outcome=value.outcome.value,
                actor_id=value.actor_id,
                assignment_version_id=value.accountable_assignment_version_id,
                mechanism_version_id=value.accountable_mechanism_version_id,
            )

        content: dict[str, JsonValue] = {
            "trigger_version_id": str(value.trigger_version_id),
            "case_id": str(value.case_id),
            "decision_version_id": str(value.decision_version_id),
            "configuration_version_id": str(value.configuration_version_id),
            "outcome": value.outcome.value,
            "rationale": value.rationale,
            "actor_id": str(value.actor_id),
            "assignment_version_id": (
                str(value.accountable_assignment_version_id)
                if value.accountable_assignment_version_id
                else None
            ),
            "mechanism_version_id": (
                str(value.accountable_mechanism_version_id)
                if value.accountable_mechanism_version_id
                else None
            ),
            "delegation_chain_version_ids": self._json_text(
                str(item) for item in value.delegation_chain_version_ids
            ),
        }
        return self._commit_version(
            meta=meta,
            record_id=value.determination_id,
            version_id=value.version_id,
            family="trigger-determination",
            scope=f"trigger-version:{value.trigger_version_id}",
            content=content,
            effective=value.effective,
            expected_version_id=value.expected_version_id,
            relationship_reason=value.relationship_reason,
            relationship_type=value.relationship_type,
            project=project,
            reason_outcome="INCREMENT_6_TRIGGER_DETERMINATION_VALID",
        )

    def _trigger_determination_in_transaction(
        self,
        transaction: Increment6Transaction,
        *,
        trigger_version_id: RecordVersionId,
        effective_at: datetime,
        known_at: datetime,
    ) -> TriggerDeterminationSelection:
        found: list[tuple[RecordVersionId, TriggerDeterminationOutcome]] = []
        for row in transaction.trigger_determination_rows(trigger_version_id):
            determination_id = RecordId.parse(cast("str", row["determination_id"]))
            version_id = RecordVersionId.parse(cast("str", row["version_id"]))
            current = transaction.select_current(
                SelectionQuery(
                    family="trigger-determination",
                    scope=f"trigger-version:{trigger_version_id}",
                    effective_at=effective_at,
                    known_at=known_at,
                    record_id=determination_id,
                )
            )
            if isinstance(current, SelectionFound) and current.candidate.version_id == version_id:
                found.append((version_id, TriggerDeterminationOutcome(cast("str", row["outcome"]))))
        if not found:
            return TriggerDeterminationNotEstablished()
        if len(found) == 1:
            return TriggerDeterminationFound(*found[0])
        return TriggerDeterminationConflict(frozenset(item[0] for item in found))

    def current_trigger_determination(
        self,
        *,
        trigger_version_id: RecordVersionId,
        effective_at: datetime,
        known_at: datetime | None = None,
    ) -> TriggerDeterminationSelection:
        effective_at = require_utc(effective_at)
        known = require_utc(known_at or self._clock.now())
        with self._increment6_store.read_transaction() as transaction:
            return self._trigger_determination_in_transaction(
                transaction,
                trigger_version_id=trigger_version_id,
                effective_at=effective_at,
                known_at=known,
            )

    def commit_reassessment_determination(
        self, meta: CommandMeta, value: ReassessmentDeterminationVersionInput
    ) -> CommandOutcome:
        if not value.rationale.strip():
            raise DomainRuleViolation("coordination determination rationale is required")
        allowed_outcomes = {
            ReassessmentDeterminationKind.GROUPING: {
                ReassessmentDeterminationOutcome.COMPATIBLE,
                ReassessmentDeterminationOutcome.INCOMPATIBLE,
            },
            ReassessmentDeterminationKind.DUPLICATE: {ReassessmentDeterminationOutcome.DUPLICATE},
            ReassessmentDeterminationKind.COEXISTENCE: {
                ReassessmentDeterminationOutcome.COEXISTENCE_AUTHORIZED
            },
            ReassessmentDeterminationKind.CANCELLATION: {
                ReassessmentDeterminationOutcome.CANCELLATION_AUTHORIZED
            },
            ReassessmentDeterminationKind.SUPERSESSION: {
                ReassessmentDeterminationOutcome.SUPERSESSION_AUTHORIZED
            },
        }
        if value.outcome not in allowed_outcomes[value.kind]:
            raise DomainRuleViolation("coordination determination kind/outcome mismatch")
        if value.kind is ReassessmentDeterminationKind.DUPLICATE and (
            value.outcome is not ReassessmentDeterminationOutcome.DUPLICATE
            or len(set(value.trigger_version_ids)) != 2
            or value.canonical_trigger_version_id not in value.trigger_version_ids
        ):
            raise DomainRuleViolation("identity-level duplicate disposition is incomplete")
        if value.kind is ReassessmentDeterminationKind.GROUPING and (
            len(set(value.trigger_version_ids)) < 2
        ):
            raise DomainRuleViolation("grouping determination requires exact Trigger set")
        if value.kind is ReassessmentDeterminationKind.COEXISTENCE and (
            len(set(value.reassessment_version_ids)) != 2
        ):
            raise DomainRuleViolation(
                "coexistence determination requires exactly two Reassessments"
            )
        if value.kind in {
            ReassessmentDeterminationKind.CANCELLATION,
            ReassessmentDeterminationKind.SUPERSESSION,
        } and (
            len(value.reassessment_version_ids) != 1
            or value.target_reassessment_version_id != value.reassessment_version_ids[0]
        ):
            raise DomainRuleViolation(
                "termination determination requires one exact target Reassessment"
            )

        recorded_at = self._clock.now()

        def project(base: object) -> None:
            transaction = cast("Increment6Transaction", base)
            self._validate_context(
                transaction,
                case_id=value.case_id,
                decision_version_id=value.decision_version_id,
                configuration_version_id=value.configuration_version_id,
            )
            for trigger_version_id in value.trigger_version_ids:
                trigger = transaction.trigger_detail(trigger_version_id)
                if trigger is None or trigger["case_id"] != str(value.case_id):
                    raise DomainRuleViolation("determination Trigger context mismatch")
            for reassessment_version_id in value.reassessment_version_ids:
                reassessment = transaction.reassessment_detail(reassessment_version_id)
                if reassessment is None or reassessment["case_id"] != str(value.case_id):
                    raise DomainRuleViolation("determination Reassessment context mismatch")
            self._validate_function_accountability(
                transaction,
                function=AccountabilityFunction.REASSESSMENT_COORDINATION_AUTHORITY,
                case_id=value.case_id,
                decision_version_id=value.decision_version_id,
                configuration_version_id=value.configuration_version_id,
                actor_id=value.actor_id,
                assignment_version_id=value.accountable_assignment_version_id,
                mechanism_version_id=value.accountable_mechanism_version_id,
                delegation_chain_version_ids=value.delegation_chain_version_ids,
                effective_at=value.effective.start,
                known_at=recorded_at,
            )
            transaction.add_reassessment_determination(
                determination_id=value.determination_id,
                version_id=value.version_id,
                kind=value.kind.value,
                outcome=value.outcome.value,
                target_reassessment_version_id=value.target_reassessment_version_id,
                canonical_trigger_version_id=value.canonical_trigger_version_id,
                case_id=value.case_id,
                decision_version_id=value.decision_version_id,
                configuration_version_id=value.configuration_version_id,
                affected_scope=sorted(value.affected_scope),
                actor_id=value.actor_id,
                assignment_version_id=value.accountable_assignment_version_id,
                mechanism_version_id=value.accountable_mechanism_version_id,
                trigger_version_ids=value.trigger_version_ids,
                reassessment_version_ids=value.reassessment_version_ids,
            )

        content: dict[str, JsonValue] = {
            "kind": value.kind.value,
            "outcome": value.outcome.value,
            "case_id": str(value.case_id),
            "decision_version_id": str(value.decision_version_id),
            "configuration_version_id": str(value.configuration_version_id),
            "affected_scope": self._json_text(sorted(value.affected_scope)),
            "trigger_version_ids": self._json_text(str(item) for item in value.trigger_version_ids),
            "reassessment_version_ids": self._json_text(
                str(item) for item in value.reassessment_version_ids
            ),
            "target_reassessment_version_id": (
                str(value.target_reassessment_version_id)
                if value.target_reassessment_version_id
                else None
            ),
            "canonical_trigger_version_id": (
                str(value.canonical_trigger_version_id)
                if value.canonical_trigger_version_id
                else None
            ),
            "actor_id": str(value.actor_id),
            "assignment_version_id": (
                str(value.accountable_assignment_version_id)
                if value.accountable_assignment_version_id
                else None
            ),
            "mechanism_version_id": (
                str(value.accountable_mechanism_version_id)
                if value.accountable_mechanism_version_id
                else None
            ),
            "delegation_chain_version_ids": self._json_text(
                str(item) for item in value.delegation_chain_version_ids
            ),
            "rationale": value.rationale,
        }
        return self._commit_version(
            meta=meta,
            record_id=value.determination_id,
            version_id=value.version_id,
            family="reassessment-determination",
            scope=(
                f"case:{value.case_id}:kind:{value.kind.value}:"
                f"determination:{value.determination_id}"
            ),
            content=content,
            effective=value.effective,
            expected_version_id=value.expected_version_id,
            relationship_reason=value.relationship_reason,
            relationship_type=value.relationship_type,
            project=project,
            reason_outcome="INCREMENT_6_ACCOUNTABLE_COORDINATION_DETERMINATION",
        )

    def _eligible_reassessment_determinations(
        self,
        transaction: Increment6Transaction,
        *,
        kind: ReassessmentDeterminationKind,
        effective_at: datetime,
        known_at: datetime,
        trigger_version_id: RecordVersionId | None = None,
        reassessment_version_ids: tuple[RecordVersionId, ...] = (),
    ) -> tuple[dict[str, object], ...]:
        found: list[dict[str, object]] = []
        for row in transaction.reassessment_determination_rows(
            kind=kind.value,
            trigger_version_id=trigger_version_id,
            reassessment_version_ids=reassessment_version_ids,
        ):
            version = transaction.get_version(RecordVersionId.parse(cast("str", row["version_id"])))
            if version is None:
                continue
            current = transaction.select_current(
                SelectionQuery(
                    family="reassessment-determination",
                    scope=version.scope,
                    effective_at=effective_at,
                    known_at=known_at,
                    record_id=version.record_id,
                )
            )
            if (
                isinstance(current, SelectionFound)
                and current.candidate.version_id == version.version_id
            ):
                chain = tuple(
                    RecordVersionId.parse(item)
                    for item in cast("list[str]", version.content["delegation_chain_version_ids"])
                )
                try:
                    self._validate_function_accountability(
                        transaction,
                        function=AccountabilityFunction.REASSESSMENT_COORDINATION_AUTHORITY,
                        case_id=RecordId.parse(cast("str", row["case_id"])),
                        decision_version_id=RecordVersionId.parse(
                            cast("str", row["decision_version_id"])
                        ),
                        configuration_version_id=RecordVersionId.parse(
                            cast("str", row["configuration_version_id"])
                        ),
                        actor_id=RecordId.parse(cast("str", row["actor_id"])),
                        assignment_version_id=(
                            RecordVersionId.parse(cast("str", row["assignment_version_id"]))
                            if row["assignment_version_id"]
                            else None
                        ),
                        mechanism_version_id=(
                            RecordVersionId.parse(cast("str", row["mechanism_version_id"]))
                            if row["mechanism_version_id"]
                            else None
                        ),
                        delegation_chain_version_ids=chain,
                        effective_at=effective_at,
                        known_at=known_at,
                    )
                except DomainRuleViolation:
                    continue
                found.append(row)
        return tuple(found)

    def _grouping_established(
        self,
        transaction: Increment6Transaction,
        *,
        trigger_version_ids: tuple[RecordVersionId, ...],
        effective_at: datetime,
        known_at: datetime,
    ) -> bool:
        selected = self._coordination_determination_in_transaction(
            transaction,
            kind=ReassessmentDeterminationKind.GROUPING,
            trigger_version_ids=trigger_version_ids,
            reassessment_version_ids=(),
            effective_at=effective_at,
            known_at=known_at,
        )
        return isinstance(selected, ReassessmentDeterminationFound) and (
            selected.outcome is ReassessmentDeterminationOutcome.COMPATIBLE
        )

    def _coordination_determination_in_transaction(
        self,
        transaction: Increment6Transaction,
        *,
        kind: ReassessmentDeterminationKind,
        trigger_version_ids: tuple[RecordVersionId, ...],
        reassessment_version_ids: tuple[RecordVersionId, ...],
        effective_at: datetime,
        known_at: datetime,
    ) -> ReassessmentDeterminationSelection:
        expected_triggers = {str(item) for item in trigger_version_ids}
        expected_reassessments = {str(item) for item in reassessment_version_ids}
        exact: list[tuple[RecordVersionId, ReassessmentDeterminationOutcome]] = []
        for candidate in self._eligible_reassessment_determinations(
            transaction,
            kind=kind,
            effective_at=effective_at,
            known_at=known_at,
        ):
            version_id = RecordVersionId.parse(cast("str", candidate["version_id"]))
            record = transaction.get_version(version_id)
            if record is None:
                continue
            if (
                set(cast("list[str]", record.content["trigger_version_ids"])) == expected_triggers
                and set(cast("list[str]", record.content["reassessment_version_ids"]))
                == expected_reassessments
            ):
                exact.append(
                    (
                        version_id,
                        ReassessmentDeterminationOutcome(cast("str", candidate["outcome"])),
                    )
                )
        not_established = {
            ReassessmentDeterminationKind.GROUPING: "TRIGGER GROUPING NOT ESTABLISHED",
            ReassessmentDeterminationKind.DUPLICATE: "DUPLICATE DISPOSITION NOT ESTABLISHED",
        }.get(kind, "REASSESSMENT COORDINATION NOT ESTABLISHED")
        conflict = {
            ReassessmentDeterminationKind.GROUPING: "TRIGGER GROUPING CONFLICT — UNRESOLVED",
            ReassessmentDeterminationKind.DUPLICATE: (
                "DUPLICATE DISPOSITION CONFLICT — UNRESOLVED"
            ),
        }.get(kind, "REASSESSMENT COORDINATION CONFLICT — UNRESOLVED")
        if not exact:
            return ReassessmentDeterminationNotEstablished(not_established)
        if len(exact) == 1:
            return ReassessmentDeterminationFound(*exact[0])
        return ReassessmentDeterminationConflict(frozenset(item[0] for item in exact), conflict)

    def current_coordination_determination(
        self,
        *,
        kind: ReassessmentDeterminationKind,
        trigger_version_ids: tuple[RecordVersionId, ...] = (),
        reassessment_version_ids: tuple[RecordVersionId, ...] = (),
        effective_at: datetime,
        known_at: datetime | None = None,
    ) -> ReassessmentDeterminationSelection:
        effective_at = require_utc(effective_at)
        known = require_utc(known_at or self._clock.now())
        with self._increment6_store.read_transaction() as transaction:
            return self._coordination_determination_in_transaction(
                transaction,
                kind=kind,
                trigger_version_ids=trigger_version_ids,
                reassessment_version_ids=reassessment_version_ids,
                effective_at=effective_at,
                known_at=known,
            )

    def commit_reassessment(
        self, meta: CommandMeta, value: ReassessmentVersionInput
    ) -> CommandOutcome:
        if not value.purpose.strip() or not value.rationale.strip():
            raise DomainRuleViolation("Reassessment purpose and rationale are required")
        if value.status in {
            ReassessmentStatus.COMPLETED_CONFIRMED,
            ReassessmentStatus.COMPLETED_SUCCESSOR_DECISION,
            ReassessmentStatus.CANCELLED,
            ReassessmentStatus.SUPERSEDED,
        }:
            raise DomainRuleViolation("terminal Reassessment status requires its semantic command")
        if value.status is not ReassessmentStatus.PROPOSED and not value.memberships:
            raise DomainRuleViolation("active Reassessment requires an exact Trigger Set")
        trigger_ids = tuple(item.trigger_version_id for item in value.memberships)
        if len(trigger_ids) != len(set(trigger_ids)):
            raise DomainRuleViolation(
                "Reassessment Trigger Set contains a duplicate Trigger Version"
            )
        recorded_at = self._clock.now()

        def project(base: object) -> None:
            transaction = cast("Increment6Transaction", base)
            self._validate_context(
                transaction,
                case_id=value.case_id,
                decision_version_id=value.decision_version_id,
                configuration_version_id=value.configuration_version_id,
            )
            predecessor_status: ReassessmentStatus | None = None
            if value.expected_version_id is not None:
                predecessor = transaction.reassessment_detail(value.expected_version_id)
                if predecessor is None or any(
                    predecessor[key] != expected
                    for key, expected in (
                        ("reassessment_id", str(value.reassessment_id)),
                        ("case_id", str(value.case_id)),
                        ("decision_version_id", str(value.decision_version_id)),
                        ("configuration_version_id", str(value.configuration_version_id)),
                        ("purpose", value.purpose),
                        ("affected_scope_json", json.dumps(sorted(value.affected_scope))),
                    )
                ):
                    raise DomainRuleViolation(
                        "Case/Decision/Configuration/substantive scope change requires new identity"
                    )
                predecessor_status = ReassessmentStatus(
                    transaction.current_reassessment_status(
                        reassessment_version_id=value.expected_version_id,
                        effective_at=value.effective.start,
                        known_at=recorded_at,
                    )
                )
            allowed_progress = {
                ReassessmentStatus.PROPOSED: {ReassessmentStatus.PROPOSED, ReassessmentStatus.OPEN},
                ReassessmentStatus.OPEN: {
                    ReassessmentStatus.OPEN,
                    ReassessmentStatus.ANALYSIS_IN_PROGRESS,
                    ReassessmentStatus.BLOCKED_CONFLICT,
                },
                ReassessmentStatus.ANALYSIS_IN_PROGRESS: {
                    ReassessmentStatus.ANALYSIS_IN_PROGRESS,
                    ReassessmentStatus.AWAITING_DECISION_AUTHORITY,
                    ReassessmentStatus.BLOCKED_CONFLICT,
                },
                ReassessmentStatus.AWAITING_DECISION_AUTHORITY: {
                    ReassessmentStatus.AWAITING_DECISION_AUTHORITY,
                    ReassessmentStatus.BLOCKED_CONFLICT,
                },
                ReassessmentStatus.BLOCKED_CONFLICT: {
                    ReassessmentStatus.BLOCKED_CONFLICT,
                    ReassessmentStatus.OPEN,
                    ReassessmentStatus.ANALYSIS_IN_PROGRESS,
                    ReassessmentStatus.AWAITING_DECISION_AUTHORITY,
                },
            }
            if predecessor_status is None:
                if value.status not in {ReassessmentStatus.PROPOSED, ReassessmentStatus.OPEN}:
                    raise DomainRuleViolation("new Reassessment must begin PROPOSED or OPEN")
            elif value.status not in allowed_progress.get(predecessor_status, set()):
                raise DomainRuleViolation("invalid Reassessment status progression")
            owner_vacant_proposal = (
                value.status is ReassessmentStatus.PROPOSED
                and value.owner_assignment_version_id is None
                and value.owner_mechanism_version_id is None
            )
            if owner_vacant_proposal:
                if not transaction.actor_exists(value.owner_actor_id):
                    raise DomainRuleViolation("proposed Reassessment actor does not exist")
            else:
                self._validate_function_accountability(
                    transaction,
                    function=AccountabilityFunction.REASSESSMENT_OWNER,
                    case_id=value.case_id,
                    decision_version_id=value.decision_version_id,
                    configuration_version_id=value.configuration_version_id,
                    actor_id=value.owner_actor_id,
                    assignment_version_id=value.owner_assignment_version_id,
                    mechanism_version_id=value.owner_mechanism_version_id,
                    delegation_chain_version_ids=(),
                    effective_at=value.effective.start,
                    known_at=recorded_at,
                )
            for trigger_version_id in trigger_ids:
                trigger = transaction.trigger_detail(trigger_version_id)
                if trigger is None or any(
                    trigger[key] != expected
                    for key, expected in (
                        ("case_id", str(value.case_id)),
                        ("decision_version_id", str(value.decision_version_id)),
                        ("configuration_version_id", str(value.configuration_version_id)),
                    )
                ):
                    raise DomainRuleViolation("Trigger Set exact context mismatch")
                determination = self._trigger_determination_in_transaction(
                    transaction,
                    trigger_version_id=trigger_version_id,
                    effective_at=value.effective.start,
                    known_at=recorded_at,
                )
                if not (
                    isinstance(determination, TriggerDeterminationFound)
                    and determination.outcome in _REQUIRING_OUTCOMES
                ):
                    raise DomainRuleViolation("Trigger Determination does not require Reassessment")
            if len(trigger_ids) > 1 and not self._grouping_established(
                transaction,
                trigger_version_ids=trigger_ids,
                effective_at=value.effective.start,
                known_at=recorded_at,
            ):
                raise DomainRuleViolation("TRIGGER GROUPING NOT ESTABLISHED")
            for membership in value.memberships:
                transaction.add_version(
                    FinalizedRecordVersion(
                        membership.membership_id,
                        membership.version_id,
                        "trigger-reassessment-membership",
                        (
                            f"trigger-version:{membership.trigger_version_id}:"
                            f"reassessment-version:{value.version_id}"
                        ),
                        canonical_json(
                            {
                                "trigger_version_id": str(membership.trigger_version_id),
                                "reassessment_version_id": str(value.version_id),
                                "membership_scope": membership.membership_scope,
                                "active": membership.active,
                            }
                        ),
                        recorded_at,
                        value.effective,
                        meta.actor_id or meta.principal_id,
                    )
                )
            transaction.add_reassessment(
                reassessment_id=value.reassessment_id,
                version_id=value.version_id,
                case_id=value.case_id,
                decision_version_id=value.decision_version_id,
                configuration_version_id=value.configuration_version_id,
                purpose=value.purpose,
                affected_scope=sorted(value.affected_scope),
                owner_actor_id=value.owner_actor_id,
                owner_assignment_version_id=value.owner_assignment_version_id,
                owner_mechanism_version_id=value.owner_mechanism_version_id,
                status=value.status.value,
                memberships=tuple(
                    {
                        "membership_id": item.membership_id,
                        "version_id": item.version_id,
                        "trigger_version_id": item.trigger_version_id,
                        "membership_scope": item.membership_scope,
                        "active": item.active,
                    }
                    for item in value.memberships
                ),
            )

        content: dict[str, JsonValue] = {
            "case_id": str(value.case_id),
            "decision_version_id": str(value.decision_version_id),
            "configuration_version_id": str(value.configuration_version_id),
            "purpose": value.purpose,
            "affected_scope": self._json_text(sorted(value.affected_scope)),
            "owner_actor_id": str(value.owner_actor_id),
            "owner_assignment_version_id": (
                str(value.owner_assignment_version_id)
                if value.owner_assignment_version_id
                else None
            ),
            "owner_mechanism_version_id": (
                str(value.owner_mechanism_version_id) if value.owner_mechanism_version_id else None
            ),
            "status": value.status.value,
            "trigger_set": [
                {
                    "trigger_version_id": str(item.trigger_version_id),
                    "membership_version_id": str(item.version_id),
                    "membership_scope": item.membership_scope,
                }
                for item in value.memberships
            ],
            "reviewed_basis_version_ids": self._json_text(
                str(item) for item in value.reviewed_basis_version_ids
            ),
            "rationale": value.rationale,
        }
        return self._commit_version(
            meta=meta,
            record_id=value.reassessment_id,
            version_id=value.version_id,
            family="reassessment",
            scope=f"case:{value.case_id}:reassessment:{value.reassessment_id}",
            content=content,
            effective=value.effective,
            expected_version_id=value.expected_version_id,
            relationship_reason=value.relationship_reason,
            relationship_type=value.relationship_type,
            project=project,
            reason_outcome="INCREMENT_6_IMMUTABLE_TRIGGER_SET",
        )

    def _reassessment_overlap_in_transaction(
        self,
        transaction: Increment6Transaction,
        *,
        first_version_id: RecordVersionId,
        second_version_id: RecordVersionId,
        effective_at: datetime,
        known_at: datetime,
    ) -> ReassessmentOverlap:
        first = transaction.reassessment_detail(first_version_id)
        second = transaction.reassessment_detail(second_version_id)
        if first is None or second is None:
            raise DomainRuleViolation("Reassessment Version not established")
        if first["case_id"] != second["case_id"]:
            return ReassessmentOverlap(True, "DIFFERENT CASES — INDEPENDENT")
        first_scope = frozenset(self._json_tuple(first, "affected_scope_json"))
        second_scope = frozenset(self._json_tuple(second, "affected_scope_json"))
        shared_trigger = bool(
            {item[0] for item in transaction.trigger_set(first_version_id)}
            & {item[0] for item in transaction.trigger_set(second_version_id)}
        )
        if (
            first_scope
            and second_scope
            and first_scope.isdisjoint(second_scope)
            and not shared_trigger
        ):
            return ReassessmentOverlap(True, "MECHANICALLY DISJOINT STRUCTURED SCOPE")
        candidates = self._eligible_reassessment_determinations(
            transaction,
            kind=ReassessmentDeterminationKind.COEXISTENCE,
            effective_at=effective_at,
            known_at=known_at,
            reassessment_version_ids=(first_version_id, second_version_id),
        )
        exact = []
        expected = {str(first_version_id), str(second_version_id)}
        for candidate in candidates:
            record = transaction.get_version(
                RecordVersionId.parse(cast("str", candidate["version_id"]))
            )
            if (
                record is not None
                and candidate["outcome"]
                == ReassessmentDeterminationOutcome.COEXISTENCE_AUTHORIZED.value
                and set(cast("list[str]", record.content["reassessment_version_ids"])) == expected
            ):
                exact.append(record.version_id)
        if len(exact) == 1:
            return ReassessmentOverlap(True, "ACCOUNTABLE COEXISTENCE", exact[0])
        return ReassessmentOverlap(False, "REASSESSMENT OVERLAP CONFLICT — UNRESOLVED")

    def reassessment_overlap(
        self,
        *,
        first_version_id: RecordVersionId,
        second_version_id: RecordVersionId,
        effective_at: datetime,
        known_at: datetime | None = None,
    ) -> ReassessmentOverlap:
        effective_at = require_utc(effective_at)
        known = require_utc(known_at or self._clock.now())
        with self._increment6_store.read_transaction() as transaction:
            return self._reassessment_overlap_in_transaction(
                transaction,
                first_version_id=first_version_id,
                second_version_id=second_version_id,
                effective_at=effective_at,
                known_at=known,
            )

    def reject_merge(self, *_: object, **__: object) -> None:
        raise DomainRuleViolation("REASSESSMENT MERGE UNSUPPORTED IN V0.1")

    def _trigger_coverage_in_transaction(
        self,
        transaction: Increment6Transaction,
        *,
        trigger_version_id: RecordVersionId,
        effective_at: datetime,
        known_at: datetime,
        exclude_reassessment_version_id: RecordVersionId | None = None,
    ) -> TriggerCoverage:
        trigger = transaction.trigger_detail(trigger_version_id)
        if trigger is None:
            raise DomainRuleViolation("Trigger Version not established")
        version = transaction.get_version(trigger_version_id)
        if version is None or cast("bool", trigger["withdrawn"]):
            return TriggerCoverage(
                trigger_version_id, None, frozenset(), "TRIGGER PROSPECTIVELY INELIGIBLE"
            )
        current_trigger = transaction.select_current(
            SelectionQuery(
                family="reassessment-trigger",
                scope=version.scope,
                effective_at=effective_at,
                known_at=known_at,
                record_id=version.record_id,
            )
        )
        if (
            not isinstance(current_trigger, SelectionFound)
            or current_trigger.candidate.version_id != trigger_version_id
        ):
            return TriggerCoverage(
                trigger_version_id, None, frozenset(), "TRIGGER PROSPECTIVELY INELIGIBLE"
            )
        determination = self._trigger_determination_in_transaction(
            transaction,
            trigger_version_id=trigger_version_id,
            effective_at=effective_at,
            known_at=known_at,
        )
        if isinstance(determination, TriggerDeterminationConflict):
            return TriggerCoverage(
                trigger_version_id,
                TriggerCoverageState.BLOCKED_CONFLICT,
                determination.version_ids,
                determination.reason,
            )
        if not isinstance(determination, TriggerDeterminationFound):
            return TriggerCoverage(
                trigger_version_id,
                TriggerCoverageState.BLOCKED_CONFLICT,
                frozenset(),
                determination.reason,
            )
        if determination.outcome not in _REQUIRING_OUTCOMES:
            return TriggerCoverage(
                trigger_version_id, None, frozenset(), "REASSESSMENT NOT REQUIRED"
            )

        duplicate = self._eligible_reassessment_determinations(
            transaction,
            kind=ReassessmentDeterminationKind.DUPLICATE,
            effective_at=effective_at,
            known_at=known_at,
            trigger_version_id=trigger_version_id,
        )
        duplicate_ids = frozenset(
            RecordVersionId.parse(cast("str", item["version_id"]))
            for item in duplicate
            if item["outcome"] == ReassessmentDeterminationOutcome.DUPLICATE.value
            and item["canonical_trigger_version_id"] != str(trigger_version_id)
        )
        active: set[RecordVersionId] = set()
        completed: set[RecordVersionId] = set()
        for membership in transaction.membership_rows_for_trigger(trigger_version_id):
            reassessment_version_id = RecordVersionId.parse(
                cast("str", membership["reassessment_version_id"])
            )
            if reassessment_version_id == exclude_reassessment_version_id:
                continue
            reassessment_version = transaction.get_version(reassessment_version_id)
            if reassessment_version is None:
                continue
            current_reassessment = transaction.select_current(
                SelectionQuery(
                    "reassessment",
                    reassessment_version.scope,
                    effective_at,
                    known_at,
                    reassessment_version.record_id,
                )
            )
            if (
                not isinstance(current_reassessment, SelectionFound)
                or current_reassessment.candidate.version_id != reassessment_version_id
            ):
                continue
            status = transaction.current_reassessment_status(
                reassessment_version_id=reassessment_version_id,
                effective_at=effective_at,
                known_at=known_at,
            )
            if status in _ACTIVE_REASSESSMENT_STATUSES:
                active.add(reassessment_version_id)
            elif transaction.reassessment_completion(reassessment_version_id) is not None:
                completed.add(reassessment_version_id)
        reassessment_coverage = active | completed
        compatible_coverage = True
        coverage_list = sorted(reassessment_coverage, key=str)
        for index, first in enumerate(coverage_list):
            for second in coverage_list[index + 1 :]:
                if not self._reassessment_overlap_in_transaction(
                    transaction,
                    first_version_id=first,
                    second_version_id=second,
                    effective_at=effective_at,
                    known_at=known_at,
                ).compatible:
                    compatible_coverage = False
        states = sum(bool(value) for value in (duplicate_ids, reassessment_coverage))
        supporting = duplicate_ids | frozenset(active) | frozenset(completed)
        if states > 1 or not compatible_coverage:
            return TriggerCoverage(
                trigger_version_id,
                TriggerCoverageState.BLOCKED_CONFLICT,
                supporting,
                "TRIGGER COVERAGE CONFLICT — UNRESOLVED",
            )
        if duplicate_ids:
            if len(duplicate_ids) > 1:
                return TriggerCoverage(
                    trigger_version_id,
                    TriggerCoverageState.BLOCKED_CONFLICT,
                    duplicate_ids,
                    "TRIGGER COVERAGE CONFLICT — UNRESOLVED",
                )
            return TriggerCoverage(
                trigger_version_id,
                TriggerCoverageState.DUPLICATE_DISPOSITIONED,
                duplicate_ids,
                "IDENTITY-LEVEL DUPLICATE DISPOSITION",
            )
        if active:
            return TriggerCoverage(
                trigger_version_id,
                TriggerCoverageState.LINKED_ACTIVE,
                frozenset(active),
                "ACTIVE REASSESSMENT MEMBERSHIP",
            )
        if completed:
            return TriggerCoverage(
                trigger_version_id,
                TriggerCoverageState.SATISFIED_BY_COMPLETED_REASSESSMENT,
                frozenset(completed),
                "EXACT COMPLETED REASSESSMENT OUTCOME",
            )
        return TriggerCoverage(
            trigger_version_id,
            TriggerCoverageState.REASSESSMENT_REQUIRED_UNASSIGNED,
            frozenset(),
            "REASSESSMENT_REQUIRED_UNASSIGNED",
        )

    def trigger_coverage(
        self,
        *,
        trigger_version_id: RecordVersionId,
        effective_at: datetime,
        known_at: datetime | None = None,
    ) -> TriggerCoverage:
        effective_at = require_utc(effective_at)
        known = require_utc(known_at or self._clock.now())
        with self._increment6_store.read_transaction() as transaction:
            return self._trigger_coverage_in_transaction(
                transaction,
                trigger_version_id=trigger_version_id,
                effective_at=effective_at,
                known_at=known,
            )

    def terminate_reassessment(
        self,
        meta: CommandMeta,
        request: ReassessmentTerminationRequest,
        *,
        supersede: bool,
    ) -> CommandOutcome:
        effective_at = require_utc(request.effective_at)
        recorded_at = self._clock.now()
        target_status = ReassessmentStatus.SUPERSEDED if supersede else ReassessmentStatus.CANCELLED
        expected_kind = (
            ReassessmentDeterminationKind.SUPERSESSION
            if supersede
            else ReassessmentDeterminationKind.CANCELLATION
        )
        expected_outcome = (
            ReassessmentDeterminationOutcome.SUPERSESSION_AUTHORIZED
            if supersede
            else ReassessmentDeterminationOutcome.CANCELLATION_AUTHORIZED
        )
        if supersede != (request.successor_reassessment_version_id is not None):
            raise DomainRuleViolation(
                "supersession names exactly one successor; cancellation names none"
            )
        payload: dict[str, JsonValue] = {
            "reassessment_id": str(request.reassessment_id),
            "expected_reassessment_version_id": str(request.expected_reassessment_version_id),
            "determination_version_id": str(request.determination_version_id),
            "successor_reassessment_version_id": (
                str(request.successor_reassessment_version_id)
                if request.successor_reassessment_version_id
                else None
            ),
            "target_status": target_status.value,
            "effective_at": effective_at.isoformat(),
            "principal_id": meta.principal_id,
            "actor_id": meta.actor_id,
        }
        digest = canonical_command_digest(payload)
        with self._increment6_store.semantic_transaction() as transaction:
            replay = transaction.get_idempotency(meta.idempotency_scope, meta.idempotency_key)
            if replay is not None:
                if replay.digest != digest:
                    raise DomainPreconditionFailed("IDEMPOTENCY KEY REUSE CONFLICT")
                return replay.outcome
            reassessment = transaction.reassessment_detail(request.expected_reassessment_version_id)
            version = transaction.get_version(request.expected_reassessment_version_id)
            if (
                reassessment is None
                or version is None
                or reassessment["reassessment_id"] != str(request.reassessment_id)
            ):
                raise DomainPreconditionFailed("stale Reassessment Version precondition")
            current = transaction.select_current(
                SelectionQuery(
                    "reassessment",
                    version.scope,
                    effective_at,
                    recorded_at,
                    request.reassessment_id,
                )
            )
            if (
                not isinstance(current, SelectionFound)
                or current.candidate.version_id != request.expected_reassessment_version_id
            ):
                raise DomainPreconditionFailed("stale Reassessment Version precondition")
            determination = transaction.reassessment_determination_detail(
                request.determination_version_id
            )
            determination_record = transaction.get_version(request.determination_version_id)
            eligible_determination_ids = {
                RecordVersionId.parse(cast("str", item["version_id"]))
                for item in self._eligible_reassessment_determinations(
                    transaction,
                    kind=expected_kind,
                    effective_at=effective_at,
                    known_at=recorded_at,
                    reassessment_version_ids=(request.expected_reassessment_version_id,),
                )
            }
            if (
                determination is None
                or determination_record is None
                or request.determination_version_id not in eligible_determination_ids
                or determination["kind"] != expected_kind.value
                or determination["outcome"] != expected_outcome.value
                or determination["target_reassessment_version_id"]
                != str(request.expected_reassessment_version_id)
                or cast(
                    "list[str]",
                    determination_record.content["reassessment_version_ids"],
                )
                != [str(request.expected_reassessment_version_id)]
            ):
                raise DomainRuleViolation("accountable termination determination not established")
            if request.successor_reassessment_version_id is not None:
                successor = transaction.reassessment_detail(
                    request.successor_reassessment_version_id
                )
                if successor is None or successor["case_id"] != reassessment["case_id"]:
                    raise DomainRuleViolation("exact successor Reassessment is invalid")
            for trigger_version_id, _ in transaction.trigger_set(
                request.expected_reassessment_version_id
            ):
                coverage = self._trigger_coverage_in_transaction(
                    transaction,
                    trigger_version_id=trigger_version_id,
                    effective_at=effective_at,
                    known_at=recorded_at,
                    exclude_reassessment_version_id=request.expected_reassessment_version_id,
                )
                if coverage.state not in {
                    TriggerCoverageState.LINKED_ACTIVE,
                    TriggerCoverageState.SATISFIED_BY_COMPLETED_REASSESSMENT,
                    TriggerCoverageState.DUPLICATE_DISPOSITIONED,
                }:
                    raise DomainRuleViolation(
                        "termination would violate no-lost-trigger coverage invariant"
                    )
            status = StatusEvent(
                EventId.new(),
                request.expected_reassessment_version_id,
                transaction.current_reassessment_status(
                    reassessment_version_id=request.expected_reassessment_version_id,
                    effective_at=effective_at,
                    known_at=recorded_at,
                ),
                target_status.value,
                recorded_at,
                effective_at,
                meta.actor_id or meta.actor_resolution.value,
                f"accountable {expected_kind.value} {request.determination_version_id}",
            )
            transaction.add_status_event(status)
            relationship_ids: tuple[str, ...] = ()
            affected: tuple[RecordVersionId, ...] = (request.expected_reassessment_version_id,)
            if request.successor_reassessment_version_id is not None:
                relationship = VersionRelationship(
                    RelationshipId.new(),
                    request.expected_reassessment_version_id,
                    request.successor_reassessment_version_id,
                    RelationshipType.SUPERSESSION,
                    recorded_at,
                    "accountable history-preserving Reassessment supersession",
                )
                transaction.add_relationship(relationship)
                relationship_ids = (str(relationship.relationship_id),)
                affected += (request.successor_reassessment_version_id,)
            audit = AuditFact(
                AuditId.new(),
                meta.principal_id,
                meta.actor_id,
                meta.actor_resolution,
                f"{target_status.value}_REASSESSMENT",
                "COMMITTED",
                meta.command_id,
                meta.idempotency_scope,
                meta.idempotency_key,
                meta.correlation_id,
                meta.causation_id,
                request.reassessment_id,
                affected,
                str(request.expected_reassessment_version_id),
                str(request.expected_reassessment_version_id),
                effective_at,
                recorded_at,
                ("NO_LOST_TRIGGER_ATOMIC_COVERAGE",),
                digest,
            )
            transaction.add_audit(audit)
            outcome = CommandOutcome(
                str(meta.command_id),
                str(request.reassessment_id),
                (),
                (str(status.event_id),),
                relationship_ids,
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
            return outcome

    def commit_interim_disposition(
        self, meta: CommandMeta, value: InterimOperatingDispositionVersionInput
    ) -> CommandOutcome:
        require_utc(value.knowledge_cutoff)
        if value.knowledge_cutoff > self._clock.now():
            raise DomainRuleViolation(
                "Interim Disposition knowledge cutoff cannot be in the future"
            )
        if value.expiry_at is not None:
            require_utc(value.expiry_at)
            if value.expiry_at <= value.effective.start:
                raise DomainRuleViolation("Interim Disposition expiry must be prospective")
        if not value.rationale.strip() or not (
            value.required_controls
            or value.prohibitions
            or value.conditions
            or value.suspend_scope
            or value.allowed_actions
        ):
            raise DomainRuleViolation("Interim Disposition must state an exact restrictive effect")

        def project(base: object) -> None:
            transaction = cast("Increment6Transaction", base)
            reassessment = transaction.reassessment_detail(value.reassessment_version_id)
            decision = transaction.decision_detail(value.decision_version_id)
            boundary = transaction.boundary_snapshot_detail(value.boundary_snapshot_version_id)
            basis = transaction.authorization_basis_detail(value.authority_basis_version_id)
            basis_record = transaction.get_version(value.authority_basis_version_id)
            if (
                reassessment is None
                or decision is None
                or boundary is None
                or basis is None
                or basis_record is None
                or reassessment["case_id"] != str(value.case_id)
                or reassessment["decision_version_id"] != str(value.decision_version_id)
                or reassessment["configuration_version_id"] != str(value.configuration_version_id)
                or decision.boundary_snapshot_version_id != value.boundary_snapshot_version_id
                or basis.decision_version_id != value.decision_version_id
                or basis.configuration_version_id != value.configuration_version_id
                or basis_record.content.get("authorization_actor_id")
                != str(value.authority_actor_id)
            ):
                raise DomainRuleViolation("Interim Disposition exact governance basis mismatch")
            status = transaction.current_reassessment_status(
                reassessment_version_id=value.reassessment_version_id,
                effective_at=value.effective.start,
                known_at=value.knowledge_cutoff,
            )
            if status not in _ACTIVE_REASSESSMENT_STATUSES:
                raise DomainRuleViolation("Interim Disposition requires active Reassessment")
            for other_version_id in transaction.reassessment_versions_for_case(value.case_id):
                if other_version_id == value.reassessment_version_id:
                    continue
                other = transaction.get_version(other_version_id)
                if other is None:
                    continue
                selected = transaction.select_current(
                    SelectionQuery(
                        "reassessment",
                        other.scope,
                        value.effective.start,
                        value.knowledge_cutoff,
                        other.record_id,
                    )
                )
                if (
                    isinstance(selected, SelectionFound)
                    and selected.candidate.version_id == other_version_id
                    and transaction.current_reassessment_status(
                        reassessment_version_id=other_version_id,
                        effective_at=value.effective.start,
                        known_at=value.knowledge_cutoff,
                    )
                    in _ACTIVE_REASSESSMENT_STATUSES
                    and not self._reassessment_overlap_in_transaction(
                        transaction,
                        first_version_id=value.reassessment_version_id,
                        second_version_id=other_version_id,
                        effective_at=value.effective.start,
                        known_at=value.knowledge_cutoff,
                    ).compatible
                ):
                    raise DomainRuleViolation(
                        "Reassessment overlap conflict blocks Interim Disposition"
                    )
            authorized = self._authorized_decisions_in_transaction(
                transaction,
                case_id=value.case_id,
                configuration_version_id=value.configuration_version_id,
                effective_at=value.effective.start,
                known_at=value.knowledge_cutoff,
            )
            if (
                len(authorized) != 1
                or authorized[0].decision_version_id != value.decision_version_id
            ):
                raise DomainRuleViolation("Interim Disposition Decision Authority not established")
            transaction.add_interim_disposition(
                disposition_id=value.disposition_id,
                version_id=value.version_id,
                reassessment_version_id=value.reassessment_version_id,
                case_id=value.case_id,
                decision_version_id=value.decision_version_id,
                configuration_version_id=value.configuration_version_id,
                boundary_snapshot_version_id=value.boundary_snapshot_version_id,
                affected_scope=sorted(value.affected_scope),
                operating_state=value.operating_state,
                allowed_actions=sorted(value.allowed_actions),
                required_controls=sorted(value.required_controls),
                prohibitions=sorted(value.prohibitions),
                conditions=sorted(value.conditions),
                suspend_scope=value.suspend_scope,
                authority_basis_version_id=value.authority_basis_version_id,
                authority_actor_id=value.authority_actor_id,
                expiry_at=value.expiry_at,
            )

        content: dict[str, JsonValue] = {
            "reassessment_version_id": str(value.reassessment_version_id),
            "case_id": str(value.case_id),
            "decision_version_id": str(value.decision_version_id),
            "configuration_version_id": str(value.configuration_version_id),
            "boundary_snapshot_version_id": str(value.boundary_snapshot_version_id),
            "affected_scope": self._json_text(sorted(value.affected_scope)),
            "operating_state": value.operating_state,
            "allowed_actions": self._json_text(sorted(value.allowed_actions)),
            "required_controls": self._json_text(sorted(value.required_controls)),
            "prohibitions": self._json_text(sorted(value.prohibitions)),
            "conditions": self._json_text(sorted(value.conditions)),
            "suspend_scope": value.suspend_scope,
            "rationale": value.rationale,
            "authority_basis_version_id": str(value.authority_basis_version_id),
            "authority_actor_id": str(value.authority_actor_id),
            "expiry_at": value.expiry_at.isoformat() if value.expiry_at else None,
            "knowledge_cutoff": value.knowledge_cutoff.isoformat(),
        }
        return self._commit_version(
            meta=meta,
            record_id=value.disposition_id,
            version_id=value.version_id,
            family="interim-operating-disposition",
            scope=(
                f"case:{value.case_id}:decision-version:{value.decision_version_id}:"
                f"configuration-version:{value.configuration_version_id}"
            ),
            content=content,
            effective=value.effective,
            expected_version_id=value.expected_version_id,
            relationship_reason=value.relationship_reason,
            relationship_type=value.relationship_type,
            project=project,
            reason_outcome="INCREMENT_6_RESTRICTIVE_INTERIM_DISPOSITION",
        )

    def effective_operating_disposition(
        self,
        *,
        case_id: RecordId,
        decision_version_id: RecordVersionId,
        configuration_version_id: RecordVersionId,
        effective_at: datetime,
        known_at: datetime | None = None,
    ) -> EffectiveOperatingDisposition:
        effective_at = require_utc(effective_at)
        known = require_utc(known_at or self._clock.now())
        with self._increment6_store.read_transaction() as transaction:
            selected: list[tuple[RecordVersionId, dict[str, object]]] = []
            for row in transaction.interim_disposition_rows(
                case_id=case_id,
                decision_version_id=decision_version_id,
                configuration_version_id=configuration_version_id,
            ):
                reassessment_version_id = RecordVersionId.parse(
                    cast("str", row["reassessment_version_id"])
                )
                reassessment_version = transaction.get_version(reassessment_version_id)
                current_reassessment = (
                    transaction.select_current(
                        SelectionQuery(
                            "reassessment",
                            reassessment_version.scope,
                            effective_at,
                            known,
                            reassessment_version.record_id,
                        )
                    )
                    if reassessment_version is not None
                    else None
                )
                if (
                    not isinstance(current_reassessment, SelectionFound)
                    or current_reassessment.candidate.version_id != reassessment_version_id
                    or transaction.current_reassessment_status(
                        reassessment_version_id=reassessment_version_id,
                        effective_at=effective_at,
                        known_at=known,
                    )
                    not in _ACTIVE_REASSESSMENT_STATUSES
                ):
                    continue
                version_id = RecordVersionId.parse(cast("str", row["version_id"]))
                version = transaction.get_version(version_id)
                if version is None:
                    continue
                current = transaction.select_current(
                    SelectionQuery(
                        "interim-operating-disposition",
                        version.scope,
                        effective_at,
                        known,
                        version.record_id,
                    )
                )
                expiry = cast("int | None", row["expiry_at_us"])
                if (
                    isinstance(current, SelectionFound)
                    and current.candidate.version_id == version_id
                    and (expiry is None or effective_at < from_epoch_microseconds(expiry))
                ):
                    selected.append((version_id, row))
            if not selected:
                return EffectiveOperatingDisposition(
                    False,
                    frozenset(),
                    frozenset(),
                    frozenset(),
                    frozenset(),
                    frozenset(),
                    frozenset(),
                    frozenset(),
                    "NO CURRENT INTERIM OPERATING DISPOSITION",
                )
            scopes = [
                frozenset(self._json_tuple(row, "affected_scope_json")) for _, row in selected
            ]
            allowed_sets = [
                frozenset(self._json_tuple(row, "allowed_actions_json")) for _, row in selected
            ]
            allowed = allowed_sets[0]
            for item in allowed_sets[1:]:
                allowed &= item
            states = frozenset(
                cast("str", row["operating_state"])
                for _, row in selected
                if row["operating_state"] is not None
            )
            required = frozenset().union(
                *(frozenset(self._json_tuple(row, "required_controls_json")) for _, row in selected)
            )
            prohibited = frozenset().union(
                *(frozenset(self._json_tuple(row, "prohibitions_json")) for _, row in selected)
            )
            conditions = frozenset().union(
                *(frozenset(self._json_tuple(row, "conditions_json")) for _, row in selected)
            )
            indeterminate = (
                any(not scope for scope in scopes)
                or len(states) > 1
                or bool(allowed & prohibited)
                or any(cast("bool", row["suspend_scope"]) for _, row in selected)
            )
            return EffectiveOperatingDisposition(
                indeterminate,
                frozenset().union(*scopes),
                states,
                allowed,
                required,
                prohibited,
                conditions,
                frozenset(item[0] for item in selected),
                (
                    "INDETERMINATE INTERSECTION — AFFECTED SCOPE SUSPENDED"
                    if indeterminate
                    else "EXACT RESTRICTIVE INTERSECTION"
                ),
            )

    def _validate_completion_basis(
        self,
        transaction: Increment6Transaction,
        *,
        reassessment_version_id: RecordVersionId,
        decision_version_id: RecordVersionId,
        configuration_version_id: RecordVersionId,
        effective_at: datetime,
        known_at: datetime,
    ) -> dict[str, object]:
        reassessment = transaction.reassessment_detail(reassessment_version_id)
        version = transaction.get_version(reassessment_version_id)
        if reassessment is None or version is None:
            raise DomainPreconditionFailed("Reassessment Version not established")
        current = transaction.select_current(
            SelectionQuery(
                "reassessment",
                version.scope,
                effective_at,
                known_at,
                version.record_id,
            )
        )
        if (
            not isinstance(current, SelectionFound)
            or current.candidate.version_id != reassessment_version_id
        ):
            raise DomainPreconditionFailed("stale expected Reassessment Version")
        if reassessment["decision_version_id"] != str(decision_version_id) or reassessment[
            "configuration_version_id"
        ] != str(configuration_version_id):
            raise DomainRuleViolation("completion current-governance context mismatch")
        status = transaction.current_reassessment_status(
            reassessment_version_id=reassessment_version_id,
            effective_at=effective_at,
            known_at=known_at,
        )
        if status != ReassessmentStatus.AWAITING_DECISION_AUTHORITY.value:
            raise DomainRuleViolation(
                "Reassessment must be AWAITING_DECISION_AUTHORITY to complete"
            )
        authorized = self._authorized_decisions_in_transaction(
            transaction,
            case_id=RecordId.parse(cast("str", reassessment["case_id"])),
            configuration_version_id=configuration_version_id,
            effective_at=effective_at,
            known_at=known_at,
        )
        if len(authorized) != 1 or authorized[0].decision_version_id != decision_version_id:
            raise DomainRuleViolation("current authorized Decision not established")
        case_id = RecordId.parse(cast("str", reassessment["case_id"]))
        for other_version_id in transaction.reassessment_versions_for_case(case_id):
            if other_version_id == reassessment_version_id:
                continue
            other_version = transaction.get_version(other_version_id)
            if other_version is None:
                continue
            selected = transaction.select_current(
                SelectionQuery(
                    "reassessment",
                    other_version.scope,
                    effective_at,
                    known_at,
                    other_version.record_id,
                )
            )
            if (
                not isinstance(selected, SelectionFound)
                or selected.candidate.version_id != other_version_id
                or transaction.current_reassessment_status(
                    reassessment_version_id=other_version_id,
                    effective_at=effective_at,
                    known_at=known_at,
                )
                not in _ACTIVE_REASSESSMENT_STATUSES
            ):
                continue
            if not self._reassessment_overlap_in_transaction(
                transaction,
                first_version_id=reassessment_version_id,
                second_version_id=other_version_id,
                effective_at=effective_at,
                known_at=known_at,
            ).compatible:
                raise DomainRuleViolation("Reassessment overlap conflict blocks completion")
        for trigger_version_id, _ in transaction.trigger_set(reassessment_version_id):
            coverage = self._trigger_coverage_in_transaction(
                transaction,
                trigger_version_id=trigger_version_id,
                effective_at=effective_at,
                known_at=known_at,
            )
            if coverage.state is not TriggerCoverageState.LINKED_ACTIVE or (
                reassessment_version_id not in coverage.supporting_version_ids
            ):
                raise DomainRuleViolation("Trigger coverage conflict blocks completion")
        owner_assignment = (
            RecordVersionId.parse(cast("str", reassessment["owner_assignment_version_id"]))
            if reassessment["owner_assignment_version_id"]
            else None
        )
        owner_mechanism = (
            RecordVersionId.parse(cast("str", reassessment["owner_mechanism_version_id"]))
            if reassessment["owner_mechanism_version_id"]
            else None
        )
        self._validate_function_accountability(
            transaction,
            function=AccountabilityFunction.REASSESSMENT_OWNER,
            case_id=RecordId.parse(cast("str", reassessment["case_id"])),
            decision_version_id=decision_version_id,
            configuration_version_id=configuration_version_id,
            actor_id=RecordId.parse(cast("str", reassessment["owner_actor_id"])),
            assignment_version_id=owner_assignment,
            mechanism_version_id=owner_mechanism,
            delegation_chain_version_ids=(),
            effective_at=effective_at,
            known_at=known_at,
        )
        return reassessment

    def complete_confirmed(
        self, meta: CommandMeta, value: DecisionConfirmationVersionInput
    ) -> ReassessmentCompletionResult:
        effective_at = require_utc(value.effective_at)
        known_at = require_utc(value.knowledge_cutoff)
        recorded_at = self._clock.now()
        required_review_domains = {
            "evidence",
            "authority",
            "configuration",
            "value",
            "risk",
            "control",
            "uncertainty",
            "boundary",
        }
        if (
            known_at > recorded_at
            or not value.rationale.strip()
            or set(value.reviewed_domains) != required_review_domains
            or any(not references for references in value.reviewed_domains.values())
            or not value.next_trigger_learning_references
        ):
            raise DomainRuleViolation("confirmation knowledge/rationale is invalid")
        payload: dict[str, JsonValue] = {
            "confirmation_id": str(value.confirmation_id),
            "version_id": str(value.version_id),
            "reassessment_version_id": str(value.reassessment_version_id),
            "decision_version_id": str(value.decision_version_id),
            "configuration_version_id": str(value.configuration_version_id),
            "boundary_snapshot_version_id": str(value.boundary_snapshot_version_id),
            "authority_basis_version_id": str(value.authority_basis_version_id),
            "confirmer_actor_id": str(value.confirmer_actor_id),
            "trigger_version_ids": self._json_text(str(item) for item in value.trigger_version_ids),
            "reviewed_basis_version_ids": self._json_text(
                str(item) for item in value.reviewed_basis_version_ids
            ),
            "reviewed_domains": {
                key: list(references) for key, references in value.reviewed_domains.items()
            },
            "next_trigger_learning_references": self._json_text(
                value.next_trigger_learning_references
            ),
            "rationale": value.rationale,
            "effective_at": effective_at.isoformat(),
            "knowledge_cutoff": known_at.isoformat(),
            "principal_id": meta.principal_id,
            "actor_id": meta.actor_id,
        }
        digest = canonical_command_digest(payload)
        with self._increment6_store.semantic_transaction() as transaction:
            replay = transaction.get_idempotency(meta.idempotency_scope, meta.idempotency_key)
            if replay is not None:
                if replay.digest != digest:
                    raise DomainPreconditionFailed("IDEMPOTENCY KEY REUSE CONFLICT")
                return ReassessmentCompletionResult(
                    True,
                    ReassessmentStatus.COMPLETED_CONFIRMED,
                    RecordVersionId.parse(replay.outcome.version_ids[0]),
                    "REASSESSMENT CONFIRMATION COMMITTED",
                )
            reassessment = self._validate_completion_basis(
                transaction,
                reassessment_version_id=value.reassessment_version_id,
                decision_version_id=value.decision_version_id,
                configuration_version_id=value.configuration_version_id,
                effective_at=effective_at,
                known_at=known_at,
            )
            decision = transaction.decision_detail(value.decision_version_id)
            basis = transaction.authorization_basis_detail(value.authority_basis_version_id)
            actual_triggers = tuple(
                item[0] for item in transaction.trigger_set(value.reassessment_version_id)
            )
            current_authorized = self._authorized_decisions_in_transaction(
                transaction,
                case_id=RecordId.parse(cast("str", reassessment["case_id"])),
                configuration_version_id=value.configuration_version_id,
                effective_at=effective_at,
                known_at=known_at,
            )
            exact_reviewed_versions = set(value.reviewed_basis_version_ids)
            for references in value.reviewed_domains.values():
                for reference in references:
                    try:
                        reviewed_version_id = RecordVersionId.parse(reference)
                    except ValueError:
                        continue
                    if transaction.get_version(reviewed_version_id) is None:
                        raise DomainRuleViolation(
                            "Decision Confirmation reviewed exact Version is not established"
                        )
                    exact_reviewed_versions.add(reviewed_version_id)
            if (
                decision is None
                or basis is None
                or len(current_authorized) != 1
                or current_authorized[0].authorization_basis_version_id
                != value.authority_basis_version_id
                or decision.boundary_snapshot_version_id != value.boundary_snapshot_version_id
                or basis.decision_version_id != value.decision_version_id
                or tuple(value.trigger_version_ids) != actual_triggers
                or value.confirmer_actor_id
                != RecordId.parse(cast("str", reassessment["owner_actor_id"]))
                or value.configuration_version_id not in exact_reviewed_versions
                or value.boundary_snapshot_version_id not in exact_reviewed_versions
                or value.decision_version_id not in exact_reviewed_versions
            ):
                raise DomainRuleViolation("immutable Decision Confirmation exact basis mismatch")
            confirmation_content: dict[str, JsonValue] = {
                "reassessment_version_id": str(value.reassessment_version_id),
                "decision_version_id": str(value.decision_version_id),
                "configuration_version_id": str(value.configuration_version_id),
                "boundary_snapshot_version_id": str(value.boundary_snapshot_version_id),
                "authority_basis_version_id": str(value.authority_basis_version_id),
                "confirmer_actor_id": str(value.confirmer_actor_id),
                "trigger_version_ids": self._json_text(
                    str(item) for item in value.trigger_version_ids
                ),
                "reviewed_basis_version_ids": self._json_text(
                    str(item) for item in value.reviewed_basis_version_ids
                ),
                "reviewed_domains": {
                    key: list(references) for key, references in value.reviewed_domains.items()
                },
                "next_trigger_learning_references": self._json_text(
                    value.next_trigger_learning_references
                ),
                "rationale": value.rationale,
                "effective_at": effective_at.isoformat(),
                "knowledge_cutoff": known_at.isoformat(),
            }
            transaction.add_version(
                FinalizedRecordVersion(
                    value.confirmation_id,
                    value.version_id,
                    "decision-confirmation",
                    f"reassessment-version:{value.reassessment_version_id}",
                    canonical_json(confirmation_content),
                    recorded_at,
                    EffectiveInterval(effective_at),
                    meta.actor_id or meta.principal_id,
                )
            )
            transaction.add_decision_confirmation(
                confirmation_id=value.confirmation_id,
                version_id=value.version_id,
                reassessment_version_id=value.reassessment_version_id,
                decision_version_id=value.decision_version_id,
                configuration_version_id=value.configuration_version_id,
                boundary_snapshot_version_id=value.boundary_snapshot_version_id,
                authority_basis_version_id=value.authority_basis_version_id,
                confirmer_actor_id=value.confirmer_actor_id,
            )
            status = StatusEvent(
                EventId.new(),
                value.reassessment_version_id,
                transaction.current_reassessment_status(
                    reassessment_version_id=value.reassessment_version_id,
                    effective_at=effective_at,
                    known_at=known_at,
                ),
                ReassessmentStatus.COMPLETED_CONFIRMED.value,
                recorded_at,
                effective_at,
                meta.actor_id or meta.actor_resolution.value,
                f"immutable Decision Confirmation {value.version_id}",
            )
            transaction.add_status_event(status)
            transaction.add_reassessment_completion(
                reassessment_version_id=value.reassessment_version_id,
                path="CONFIRMED",
                confirmation_version_id=value.version_id,
                successor_decision_version_id=None,
                completed_at=effective_at,
            )
            audit = AuditFact(
                AuditId.new(),
                meta.principal_id,
                meta.actor_id,
                meta.actor_resolution,
                "COMPLETE_REASSESSMENT_CONFIRMED",
                "COMMITTED",
                meta.command_id,
                meta.idempotency_scope,
                meta.idempotency_key,
                meta.correlation_id,
                meta.causation_id,
                RecordId.parse(cast("str", reassessment["reassessment_id"])),
                (value.reassessment_version_id, value.version_id),
                str(value.reassessment_version_id),
                str(value.reassessment_version_id),
                effective_at,
                recorded_at,
                ("EXACTLY_ONE_COMPLETION_PATH", "CURRENT_GOVERNANCE_REVALIDATED"),
                digest,
            )
            transaction.add_audit(audit)
            outcome = CommandOutcome(
                str(meta.command_id),
                str(value.confirmation_id),
                (str(value.version_id),),
                (str(status.event_id),),
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
            return ReassessmentCompletionResult(
                True,
                ReassessmentStatus.COMPLETED_CONFIRMED,
                value.version_id,
                "REASSESSMENT CONFIRMATION COMMITTED",
            )

    def complete_with_successor(
        self, meta: CommandMeta, request: SuccessorDecisionCompletionRequest
    ) -> ReassessmentCompletionResult:
        """Atomically commit the existing Increment 4 successor bundle and completion."""
        effective_at = require_utc(request.effective_at)
        known_at = require_utc(request.knowledge_cutoff)
        recorded_at = self._clock.now()
        boundary = request.successor_boundary
        decision = request.successor_decision
        authorization = request.authorization_basis
        clause_ids = {item.clause_id for item in boundary.clauses}
        clause_versions = {item.clause_version_id for item in boundary.clauses}
        if known_at > recorded_at or authorization.authorization_effective_at != effective_at:
            raise DomainRuleViolation("successor completion time/knowledge basis is invalid")
        if (
            boundary.effective.start != effective_at
            or decision.effective.start != effective_at
            or authorization.effective.start != effective_at
            or boundary.status != "finalized"
            or not boundary.clauses
            or not boundary.narrative_rationale.strip()
            or len(clause_ids) != len(boundary.clauses)
            or len(clause_versions) != len(boundary.clauses)
            or any(
                not clause.narrative.strip()
                or not clause.provenance
                or (
                    clause.verification_mode is BoundaryVerificationMode.MECHANICAL
                    and (clause.operator is None or clause.value is None)
                )
                for clause in boundary.clauses
            )
            or decision.status is not DecisionStatus.PROPOSED
            or not decision.proposed_action.strip()
            or not decision.operating_state.strip()
            or not decision.rationale.strip()
            or decision.expected_version_id != request.predecessor_decision_version_id
            or boundary.expected_version_id is None
            or authorization.decision_id != decision.decision_id
            or authorization.decision_version_id != decision.version_id
            or authorization.configuration_id != decision.configuration_id
            or authorization.configuration_version_id != decision.configuration_version_id
            or decision.boundary_snapshot_id != boundary.snapshot_id
            or decision.boundary_snapshot_version_id != boundary.version_id
            or boundary.case_id != decision.case_id
            or boundary.configuration_id != decision.configuration_id
            or boundary.configuration_version_id != decision.configuration_version_id
            or boundary.integration_id != decision.integration_id
            or boundary.integration_version_id != decision.integration_version_id
            or any(
                clause.verification_mode
                in {
                    BoundaryVerificationMode.HUMAN,
                    BoundaryVerificationMode.EXTERNAL,
                    BoundaryVerificationMode.INDETERMINATE,
                }
                for clause in boundary.clauses
            )
        ):
            raise DomainRuleViolation(
                "atomic successor Decision/Boundary/Authorization bundle mismatch"
            )
        payload: dict[str, JsonValue] = {
            "reassessment_version_id": str(request.reassessment_version_id),
            "predecessor_decision_version_id": str(request.predecessor_decision_version_id),
            "successor_boundary_version_id": str(boundary.version_id),
            "successor_decision_version_id": str(decision.version_id),
            "authorization_basis_version_id": str(authorization.version_id),
            "effective_at": effective_at.isoformat(),
            "knowledge_cutoff": known_at.isoformat(),
            "principal_id": meta.principal_id,
            "actor_id": meta.actor_id,
        }
        digest = canonical_command_digest(payload)
        with self._increment6_store.semantic_transaction() as transaction:
            replay = transaction.get_idempotency(meta.idempotency_scope, meta.idempotency_key)
            if replay is not None:
                if replay.digest != digest:
                    raise DomainPreconditionFailed("IDEMPOTENCY KEY REUSE CONFLICT")
                return ReassessmentCompletionResult(
                    True,
                    ReassessmentStatus.COMPLETED_SUCCESSOR_DECISION,
                    RecordVersionId.parse(replay.outcome.version_ids[0]),
                    "REASSESSMENT SUCCESSOR DECISION COMMITTED",
                )
            reassessment = self._validate_completion_basis(
                transaction,
                reassessment_version_id=request.reassessment_version_id,
                decision_version_id=request.predecessor_decision_version_id,
                configuration_version_id=decision.configuration_version_id,
                effective_at=effective_at,
                known_at=known_at,
            )
            predecessor = transaction.decision_detail(request.predecessor_decision_version_id)
            predecessor_version = transaction.get_version(request.predecessor_decision_version_id)
            predecessor_boundary = (
                transaction.boundary_snapshot_detail(predecessor.boundary_snapshot_version_id)
                if predecessor is not None
                else None
            )
            predecessor_boundary_version = (
                transaction.get_version(predecessor.boundary_snapshot_version_id)
                if predecessor is not None
                else None
            )
            integration = transaction.integration_detail(decision.integration_version_id)
            if (
                predecessor is None
                or predecessor_version is None
                or predecessor_boundary is None
                or predecessor_boundary_version is None
                or boundary.expected_version_id != predecessor.boundary_snapshot_version_id
                or predecessor.decision_id != decision.decision_id
                or predecessor.case_id != decision.case_id
                or predecessor.configuration_version_id != decision.configuration_version_id
                or integration is None
                or integration.status.value != "completed"
            ):
                raise DomainRuleViolation(
                    "successor predecessor/current Integration basis mismatch"
                )
            for classification_id, expected in (
                *(
                    (item, "ACCEPTED_UNCERTAINTY")
                    for item in decision.accepted_uncertainty_version_ids
                ),
                *(
                    (item, "DECISION_LIMITING_UNCERTAINTY")
                    for item in decision.decision_limiting_uncertainty_version_ids
                ),
            ):
                classification = transaction.get_version(classification_id)
                if (
                    classification is None
                    or classification.family != "uncertainty-classification"
                    or classification.content.get("classification") != expected
                    or classification.content.get("integration_version_id")
                    != str(decision.integration_version_id)
                    or classification.content.get("proposed_operating_state")
                    != decision.operating_state
                ):
                    raise DomainRuleViolation(
                        "successor Decision uncertainty basis must match "
                        "Integration, class, and state"
                    )

            boundary_content: dict[str, JsonValue] = {
                "case_id": str(boundary.case_id),
                "configuration_id": str(boundary.configuration_id),
                "configuration_version_id": str(boundary.configuration_version_id),
                "integration_id": str(boundary.integration_id),
                "integration_version_id": str(boundary.integration_version_id),
                "owner_actor_id": str(boundary.owner_actor_id),
                "status": boundary.status,
                "clauses": [
                    {
                        "clause_id": str(clause.clause_id),
                        "clause_version_id": str(clause.clause_version_id),
                        "clause_type": clause.clause_type,
                        "effect": clause.effect.value,
                        "target_reference": clause.target_reference,
                        "structured_reference": clause.structured_reference,
                        "operator": clause.operator,
                        "value": clause.value,
                        "unit": clause.unit,
                        "narrative": clause.narrative,
                        "verification_mode": clause.verification_mode.value,
                    }
                    for clause in boundary.clauses
                ],
                "narrative_rationale": boundary.narrative_rationale,
                "unresolved_items": self._json_text(boundary.unresolved_items),
            }
            transaction.add_version(
                FinalizedRecordVersion(
                    boundary.snapshot_id,
                    boundary.version_id,
                    "boundary-snapshot",
                    f"case:{boundary.case_id}:configuration-version:{boundary.configuration_version_id}",
                    canonical_json(boundary_content),
                    recorded_at,
                    boundary.effective,
                    meta.actor_id or meta.principal_id,
                )
            )
            transaction.add_boundary_snapshot(
                snapshot_id=boundary.snapshot_id,
                version_id=boundary.version_id,
                case_id=boundary.case_id,
                configuration_id=boundary.configuration_id,
                configuration_version_id=boundary.configuration_version_id,
                integration_id=boundary.integration_id,
                integration_version_id=boundary.integration_version_id,
                owner_actor_id=boundary.owner_actor_id,
                status=boundary.status,
                clauses=boundary.clauses,
                recorded_at=recorded_at,
                effective_at=effective_at,
            )

            decision_content: dict[str, JsonValue] = {
                "case_id": str(decision.case_id),
                "configuration_id": str(decision.configuration_id),
                "configuration_version_id": str(decision.configuration_version_id),
                "integration_id": str(decision.integration_id),
                "integration_version_id": str(decision.integration_version_id),
                "boundary_snapshot_id": str(decision.boundary_snapshot_id),
                "boundary_snapshot_version_id": str(decision.boundary_snapshot_version_id),
                "proposed_action": decision.proposed_action,
                "operating_state": decision.operating_state,
                "rationale": decision.rationale,
                "conditions_and_limits": self._json_text(decision.conditions_and_limits),
                "accepted_uncertainty_version_ids": self._json_text(
                    str(item) for item in decision.accepted_uncertainty_version_ids
                ),
                "decision_limiting_uncertainty_version_ids": self._json_text(
                    str(item) for item in decision.decision_limiting_uncertainty_version_ids
                ),
                "authority_record_version_ids": self._json_text(
                    str(item) for item in decision.authority_record_version_ids
                ),
                "authority_gap_version_ids": self._json_text(
                    str(item) for item in decision.authority_gap_version_ids
                ),
                "status": decision.status.value,
            }
            transaction.add_version(
                FinalizedRecordVersion(
                    decision.decision_id,
                    decision.version_id,
                    "management-decision",
                    f"case:{decision.case_id}:configuration-version:{decision.configuration_version_id}",
                    canonical_json(decision_content),
                    recorded_at,
                    decision.effective,
                    meta.actor_id or meta.principal_id,
                )
            )
            transaction.add_decision(
                decision_id=decision.decision_id,
                version_id=decision.version_id,
                case_id=decision.case_id,
                configuration_id=decision.configuration_id,
                configuration_version_id=decision.configuration_version_id,
                integration_id=decision.integration_id,
                integration_version_id=decision.integration_version_id,
                boundary_snapshot_id=decision.boundary_snapshot_id,
                boundary_snapshot_version_id=decision.boundary_snapshot_version_id,
                proposed_action=decision.proposed_action,
                operating_state=decision.operating_state,
                status=decision.status.value,
                accepted_uncertainty_version_ids=decision.accepted_uncertainty_version_ids,
                decision_limiting_uncertainty_version_ids=(
                    decision.decision_limiting_uncertainty_version_ids
                ),
                authority_record_version_ids=decision.authority_record_version_ids,
                authority_gap_version_ids=decision.authority_gap_version_ids,
            )
            successor_detail = transaction.decision_detail(decision.version_id)
            if successor_detail is None:
                raise DomainRuleViolation("successor Decision projection failed")
            self._validate_decision_authority(
                transaction,
                value=authorization,
                decision=successor_detail,
                effective_at=effective_at,
                known_at=known_at,
            )
            authorization_content: dict[str, JsonValue] = {
                "decision_id": str(authorization.decision_id),
                "decision_version_id": str(authorization.decision_version_id),
                "decision_authority_identity": authorization.decision_authority_identity,
                "authority_assignment_version_id": (
                    str(authorization.authority_assignment_version_id)
                    if authorization.authority_assignment_version_id
                    else None
                ),
                "authority_mechanism": authorization.authority_mechanism,
                "authority_record_version_id": (
                    str(authorization.authority_record_version_id)
                    if authorization.authority_record_version_id
                    else None
                ),
                "delegation_chain_version_ids": self._json_text(
                    str(item) for item in authorization.delegation_chain_version_ids
                ),
                "authorized_scope": authorization.authorized_scope,
                "limits": self._json_text(authorization.limits),
                "configuration_id": str(authorization.configuration_id),
                "configuration_version_id": str(authorization.configuration_version_id),
                "operating_state_coverage": self._json_text(authorization.operating_state_coverage),
                "authorization_event_id": authorization.authorization_event_id,
                "authorization_actor_id": str(authorization.authorization_actor_id),
                "authorization_effective_at": effective_at.isoformat(),
            }
            transaction.add_version(
                FinalizedRecordVersion(
                    authorization.basis_id,
                    authorization.version_id,
                    "decision-authorization-basis",
                    f"decision-version:{decision.version_id}",
                    canonical_json(authorization_content),
                    recorded_at,
                    authorization.effective,
                    meta.actor_id or meta.principal_id,
                )
            )
            transaction.add_authorization_basis(
                basis_id=authorization.basis_id,
                version_id=authorization.version_id,
                decision_version_id=authorization.decision_version_id,
                decision_authority_identity=authorization.decision_authority_identity,
                authority_assignment_version_id=authorization.authority_assignment_version_id,
                authority_mechanism=authorization.authority_mechanism,
                authority_record_version_id=authorization.authority_record_version_id,
                delegation_chain_version_ids=authorization.delegation_chain_version_ids,
                authorized_scope=authorization.authorized_scope,
                configuration_id=authorization.configuration_id,
                configuration_version_id=authorization.configuration_version_id,
                operating_state_coverage=authorization.operating_state_coverage,
                decision_type=authorization.decision_type,
                organizational_unit=authorization.organizational_unit,
                authorization_event_id=authorization.authorization_event_id,
                authorization_actor_id=authorization.authorization_actor_id,
                authorization_effective_at=effective_at,
                authority_gap_version_ids=authorization.authority_gap_version_ids,
                bounded_proceed_version_id=authorization.bounded_proceed_version_id,
                preauthorized_activation_mechanisms=(
                    authorization.preauthorized_activation_mechanisms
                ),
            )
            relationships = (
                VersionRelationship(
                    RelationshipId.new(),
                    request.predecessor_decision_version_id,
                    decision.version_id,
                    decision.relationship_type,
                    recorded_at,
                    decision.relationship_reason or "Reassessment successor Decision",
                ),
                VersionRelationship(
                    RelationshipId.new(),
                    predecessor.boundary_snapshot_version_id,
                    boundary.version_id,
                    boundary.relationship_type,
                    recorded_at,
                    boundary.relationship_reason or "Reassessment successor Boundary",
                ),
            )
            for relationship in relationships:
                transaction.add_relationship(relationship)
            decision_status = StatusEvent(
                EventId.new(),
                decision.version_id,
                DecisionStatus.PROPOSED.value,
                DecisionStatus.AUTHORIZED.value,
                recorded_at,
                effective_at,
                str(authorization.authorization_actor_id),
                f"Decision Authorization Basis {authorization.version_id}",
            )
            predecessor_decision_status = StatusEvent(
                EventId.new(),
                request.predecessor_decision_version_id,
                DecisionStatus.AUTHORIZED.value,
                DecisionStatus.SUPERSEDED.value,
                recorded_at,
                effective_at,
                str(authorization.authorization_actor_id),
                f"successor Decision {decision.version_id}",
            )
            predecessor_boundary_status = StatusEvent(
                EventId.new(),
                predecessor.boundary_snapshot_version_id,
                "finalized",
                "superseded",
                recorded_at,
                effective_at,
                str(authorization.authorization_actor_id),
                f"successor Boundary {boundary.version_id}",
            )
            completion_status = StatusEvent(
                EventId.new(),
                request.reassessment_version_id,
                transaction.current_reassessment_status(
                    reassessment_version_id=request.reassessment_version_id,
                    effective_at=effective_at,
                    known_at=known_at,
                ),
                ReassessmentStatus.COMPLETED_SUCCESSOR_DECISION.value,
                recorded_at,
                effective_at,
                meta.actor_id or meta.actor_resolution.value,
                f"authorized successor Decision {decision.version_id}",
            )
            for status in (
                decision_status,
                predecessor_decision_status,
                predecessor_boundary_status,
                completion_status,
            ):
                transaction.add_status_event(status)
            transaction.add_reassessment_completion(
                reassessment_version_id=request.reassessment_version_id,
                path="SUCCESSOR_DECISION",
                confirmation_version_id=None,
                successor_decision_version_id=decision.version_id,
                completed_at=effective_at,
            )
            audit = AuditFact(
                AuditId.new(),
                meta.principal_id,
                meta.actor_id,
                meta.actor_resolution,
                "COMPLETE_REASSESSMENT_SUCCESSOR_DECISION",
                "COMMITTED",
                meta.command_id,
                meta.idempotency_scope,
                meta.idempotency_key,
                meta.correlation_id,
                meta.causation_id,
                RecordId.parse(cast("str", reassessment["reassessment_id"])),
                (
                    request.reassessment_version_id,
                    boundary.version_id,
                    decision.version_id,
                    authorization.version_id,
                ),
                str(request.reassessment_version_id),
                str(request.reassessment_version_id),
                effective_at,
                recorded_at,
                ("EXACTLY_ONE_COMPLETION_PATH", "ATOMIC_SUCCESSOR_DECISION_BUNDLE"),
                digest,
            )
            transaction.add_audit(audit)
            outcome = CommandOutcome(
                str(meta.command_id),
                str(decision.decision_id),
                (str(decision.version_id), str(boundary.version_id), str(authorization.version_id)),
                tuple(
                    str(item.event_id)
                    for item in (
                        decision_status,
                        predecessor_decision_status,
                        predecessor_boundary_status,
                        completion_status,
                    )
                ),
                tuple(str(item.relationship_id) for item in relationships),
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
            return ReassessmentCompletionResult(
                True,
                ReassessmentStatus.COMPLETED_SUCCESSOR_DECISION,
                decision.version_id,
                "REASSESSMENT SUCCESSOR DECISION COMMITTED",
            )
