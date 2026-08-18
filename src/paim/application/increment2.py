"""Increment 2 semantic commands composed on the common integrity kernel."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import cast

from paim.audit import AuditFact
from paim.domain.models import (
    AccountabilityConflict,
    AccountabilityFound,
    AccountabilityResolution,
    AccountabilityVacant,
    ActorVersionInput,
    CaseLifecycleState,
    CaseLinkInput,
    CaseVersionInput,
    CommandMeta,
    ConfigurationDeterminationInput,
    ConfigurationVersionInput,
    DelegationEffect,
    DeterminationKind,
    DeterminationOutcome,
    GoverningConfigurationAbsent,
    GoverningConfigurationConflict,
    GoverningConfigurationFound,
    GoverningConfigurationSelection,
    GoverningDesignationInput,
    LifecycleTransitionResult,
    RoleAssignmentVersionInput,
    RoleTargetType,
)
from paim.domain.ports import Increment2Store, Increment2Transaction
from paim.integrity import (
    AuditId,
    EventId,
    RecordId,
    RecordVersionId,
    RelationshipId,
    RelationshipType,
    SelectionAbsent,
    SelectionConflict,
    SelectionFound,
    SelectionQuery,
    StatusEvent,
    VersionRelationship,
)
from paim.integrity.commands import canonical_command_digest
from paim.integrity.records import FinalizedRecordVersion, JsonValue, canonical_json
from paim.integrity.time import Clock, EffectiveInterval, require_utc, to_epoch_microseconds
from paim.persistence.ports import CommandOutcome, IdempotencyFact


class DomainPreconditionFailed(RuntimeError):
    """A domain write observed authoritative state different from its precondition."""


class DomainRuleViolation(RuntimeError):
    """A command would violate an accepted Increment 2 semantic rule."""


def _selection_text(selection: SelectionAbsent | SelectionFound | SelectionConflict) -> str:
    if isinstance(selection, SelectionAbsent):
        return "ABSENT"
    if isinstance(selection, SelectionFound):
        return str(selection.candidate.version_id)
    return "CONFLICT:" + ",".join(
        sorted(str(candidate.version_id) for candidate in selection.candidates)
    )


def _accountability_pair_valid(
    assignment_version_id: RecordVersionId | None, mechanism: str | None
) -> bool:
    return (assignment_version_id is not None) != bool(mechanism)


class Increment2ApplicationService:
    """Bounded synchronous application boundary for Increment 2 domain behavior."""

    def __init__(self, store: Increment2Store, clock: Clock) -> None:
        self._store = store
        self._clock = clock

    def _commit_version(
        self,
        *,
        meta: CommandMeta,
        record_id: RecordId,
        version_id: RecordVersionId,
        family: str,
        scope: str,
        content: dict[str, JsonValue],
        effective: EffectiveInterval,
        expected_version_id: RecordVersionId | None,
        relationship_reason: str | None,
        project: Callable[[Increment2Transaction], None],
        reason_outcome: str,
        after_version: Callable[
            [Increment2Transaction, datetime],
            tuple[tuple[EventId, ...], tuple[RecordVersionId, ...]],
        ]
        | None = None,
    ) -> CommandOutcome:
        payload: dict[str, JsonValue] = {
            "record_id": str(record_id),
            "version_id": str(version_id),
            "family": family,
            "scope": scope,
            "content": content,
            "effective_from": effective.start.isoformat(),
            "effective_to": effective.end.isoformat() if effective.end else None,
            "expected_version_id": str(expected_version_id) if expected_version_id else None,
            "relationship_reason": relationship_reason,
            "principal_id": meta.principal_id,
            "actor_id": meta.actor_id,
        }
        digest = canonical_command_digest(payload)
        recorded_at = self._clock.now()
        query = SelectionQuery(
            family=family,
            scope=scope,
            effective_at=effective.start,
            known_at=recorded_at,
            record_id=record_id,
        )
        with self._store.semantic_transaction() as transaction:
            replay = transaction.get_idempotency(meta.idempotency_scope, meta.idempotency_key)
            if replay is not None:
                if replay.digest != digest:
                    raise DomainPreconditionFailed("IDEMPOTENCY KEY REUSE CONFLICT")
                return replay.outcome

            observed = transaction.select_current(query)
            matches = (
                isinstance(observed, SelectionAbsent)
                if expected_version_id is None
                else isinstance(observed, SelectionFound)
                and observed.candidate.version_id == expected_version_id
            )
            if not matches:
                observed_text = _selection_text(observed)
                raise DomainPreconditionFailed(
                    f"expected {expected_version_id or 'ABSENT'}; observed {observed_text}"
                )
            if expected_version_id is not None and not relationship_reason:
                raise DomainRuleViolation("successor requires an explicit relationship reason")

            version = FinalizedRecordVersion(
                record_id=record_id,
                version_id=version_id,
                family=family,
                scope=scope,
                content_json=canonical_json(content),
                recorded_at=recorded_at,
                effective=effective,
                creator=meta.actor_id or meta.principal_id,
            )
            transaction.add_version(version)
            project(transaction)

            relationship_ids: tuple[RelationshipId, ...] = ()
            status_ids: tuple[EventId, ...] = ()
            if expected_version_id is not None:
                relationship = VersionRelationship(
                    relationship_id=RelationshipId.new(),
                    source_version_id=expected_version_id,
                    target_version_id=version_id,
                    relationship_type=RelationshipType.SUPERSESSION,
                    recorded_at=recorded_at,
                    reason=cast("str", relationship_reason),
                )
                transaction.add_relationship(relationship)
                status = StatusEvent(
                    event_id=EventId.new(),
                    target_version_id=expected_version_id,
                    prior_status="finalized",
                    new_status="superseded",
                    recorded_at=recorded_at,
                    effective_at=effective.start,
                    actor=meta.actor_id or meta.actor_resolution.value,
                    basis=cast("str", relationship_reason),
                )
                transaction.add_status_event(status)
                relationship_ids = (relationship.relationship_id,)
                status_ids = (status.event_id,)
            extra_affected: tuple[RecordVersionId, ...] = ()
            if after_version is not None:
                extra_status_ids, extra_affected = after_version(transaction, recorded_at)
                status_ids += extra_status_ids

            affected_versions: tuple[RecordVersionId, ...] = (version_id,)
            if expected_version_id is not None:
                affected_versions = (expected_version_id, version_id)
            affected_versions += extra_affected

            audit = AuditFact(
                audit_id=AuditId.new(),
                principal_id=meta.principal_id,
                actor_id=meta.actor_id,
                actor_resolution=meta.actor_resolution,
                operation=f"FINALIZE_{family.upper().replace('-', '_')}",
                result="COMMITTED",
                command_id=meta.command_id,
                idempotency_scope=meta.idempotency_scope,
                idempotency_key=meta.idempotency_key,
                correlation_id=meta.correlation_id,
                causation_id=meta.causation_id,
                target_record_id=record_id,
                affected_version_ids=affected_versions,
                expected_precondition=str(expected_version_id) if expected_version_id else "ABSENT",
                observed_precondition=_selection_text(observed),
                effective_at=effective.start,
                recorded_at=recorded_at,
                reason_outcomes=(reason_outcome,),
                request_digest=digest,
            )
            transaction.add_audit(audit)
            outcome = CommandOutcome(
                command_id=str(meta.command_id),
                record_id=str(record_id),
                version_ids=(str(version_id),),
                status_event_ids=tuple(str(value) for value in status_ids),
                relationship_ids=tuple(str(value) for value in relationship_ids),
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
            return outcome

    def commit_case(self, meta: CommandMeta, value: CaseVersionInput) -> CommandOutcome:
        if not value.title.strip():
            raise DomainRuleViolation("Case title is required")
        content: dict[str, JsonValue] = {
            "title": value.title,
            "initial_lifecycle_state": CaseLifecycleState.OPEN.value,
        }
        return self._commit_version(
            meta=meta,
            record_id=value.case_id,
            version_id=value.version_id,
            family="case",
            scope=f"case:{value.case_id}",
            content=content,
            effective=value.effective,
            expected_version_id=value.expected_version_id,
            relationship_reason=value.relationship_reason,
            project=lambda transaction: transaction.add_case(value.case_id, value.version_id),
            reason_outcome="INCREMENT_2_CASE_VALID",
        )

    def commit_configuration(
        self, meta: CommandMeta, value: ConfigurationVersionInput
    ) -> CommandOutcome:
        if value.maturity.value != "finalized":
            raise DomainRuleViolation(
                "only finalized authoritative Configuration versions may commit"
            )

        def project(transaction: Increment2Transaction) -> None:
            if not transaction.case_exists(value.owning_case_id):
                raise DomainRuleViolation("Configuration requires exactly one existing owning Case")
            transaction.add_configuration(
                configuration_id=value.configuration_id,
                version_id=value.version_id,
                owning_case_id=value.owning_case_id,
                maturity=value.maturity.value,
                purpose=value.purpose.value,
            )

        content = dict(value.content)
        content.update(
            {
                "owning_case_id": str(value.owning_case_id),
                "maturity": value.maturity.value,
                "purpose": value.purpose.value,
            }
        )
        return self._commit_version(
            meta=meta,
            record_id=value.configuration_id,
            version_id=value.version_id,
            family="managed-configuration",
            scope=f"case:{value.owning_case_id}",
            content=content,
            effective=value.effective,
            expected_version_id=value.expected_version_id,
            relationship_reason=value.relationship_reason,
            project=project,
            reason_outcome="INCREMENT_2_CONFIGURATION_VALID",
        )

    def commit_actor(self, meta: CommandMeta, value: ActorVersionInput) -> CommandOutcome:
        if not value.display_name.strip():
            raise DomainRuleViolation("PAIM actor display name is required")
        return self._commit_version(
            meta=meta,
            record_id=value.actor_id,
            version_id=value.version_id,
            family="paim-actor",
            scope=f"actor:{value.actor_id}",
            content={"display_name": value.display_name},
            effective=value.effective,
            expected_version_id=value.expected_version_id,
            relationship_reason=value.relationship_reason,
            project=lambda transaction: transaction.add_actor(value.actor_id, value.version_id),
            reason_outcome="INCREMENT_2_ACTOR_VALID",
        )

    def _validate_role_scope(
        self, transaction: Increment2Transaction, value: RoleAssignmentVersionInput
    ) -> None:
        if not transaction.actor_exists(value.paim_actor_id):
            raise DomainRuleViolation("Role Assignment requires an existing PAIM actor")
        if value.target_type in {RoleTargetType.ORGANIZATION, RoleTargetType.BUSINESS_UNIT}:
            if value.case_context_id is not None:
                raise DomainRuleViolation(
                    "organization/business-unit assignment cannot invent Case ID"
                )
        elif value.target_type is RoleTargetType.CASE:
            if value.case_context_id is None or value.target_id != str(value.case_context_id):
                raise DomainRuleViolation("Case assignment requires its exact Case context")
            if not transaction.case_exists(value.case_context_id):
                raise DomainRuleViolation("Case target does not exist")
        elif value.target_type is RoleTargetType.CONFIGURATION:
            try:
                configuration_id = RecordId.parse(value.target_id)
            except ValueError as error:
                raise DomainRuleViolation(
                    "Configuration target must be a Configuration identity"
                ) from error
            owner = transaction.configuration_owning_case(configuration_id)
            if owner is None or owner != value.case_context_id:
                raise DomainRuleViolation(
                    "Configuration assignment requires exact owning-Case context "
                    "without broadening scope"
                )
        if value.delegation_effect is DelegationEffect.NONE:
            if value.delegated_from_version_id is not None:
                raise DomainRuleViolation(
                    "non-delegated assignment cannot name a delegation source"
                )
        elif value.delegated_from_version_id is None:
            raise DomainRuleViolation(
                "delegation effect requires an exact source assignment version"
            )

    def commit_role_assignment(
        self, meta: CommandMeta, value: RoleAssignmentVersionInput
    ) -> CommandOutcome:
        if (
            not value.role.strip()
            or not value.target_id.strip()
            or not value.compatibility_key.strip()
        ):
            raise DomainRuleViolation("role, typed target, and compatibility key are required")

        def project(transaction: Increment2Transaction) -> None:
            self._validate_role_scope(transaction, value)
            transaction.add_role_assignment(
                assignment_id=value.assignment_id,
                version_id=value.version_id,
                actor_id=value.paim_actor_id,
                role=value.role,
                target_type=value.target_type.value,
                target_id=value.target_id,
                case_context_id=value.case_context_id,
                accountable=value.accountable,
                compatibility_key=value.compatibility_key,
                delegation_effect=value.delegation_effect.value,
                delegated_from_version_id=value.delegated_from_version_id,
            )

        def after_version(
            transaction: Increment2Transaction, recorded_at: datetime
        ) -> tuple[tuple[EventId, ...], tuple[RecordVersionId, ...]]:
            if value.delegation_effect is not DelegationEffect.TRANSFER:
                return (), ()
            assert value.delegated_from_version_id is not None
            source = transaction.get_version(value.delegated_from_version_id)
            if source is None or source.family != "role-assignment":
                raise DomainRuleViolation(
                    "delegation source must be an exact Role Assignment version"
                )
            status = StatusEvent(
                event_id=EventId.new(),
                target_version_id=value.delegated_from_version_id,
                prior_status="finalized",
                new_status="superseded",
                recorded_at=recorded_at,
                effective_at=value.effective.start,
                actor=meta.actor_id or meta.actor_resolution.value,
                basis="explicit accountability transfer",
            )
            transaction.add_status_event(status)
            return (status.event_id,), (value.delegated_from_version_id,)

        content: dict[str, JsonValue] = {
            "paim_actor_id": str(value.paim_actor_id),
            "role": value.role,
            "target_type": value.target_type.value,
            "target_id": value.target_id,
            "case_context_id": str(value.case_context_id) if value.case_context_id else None,
            "accountable": value.accountable,
            "compatibility_key": value.compatibility_key,
            "delegation_effect": value.delegation_effect.value,
            "delegated_from_version_id": (
                str(value.delegated_from_version_id)
                if value.delegated_from_version_id is not None
                else None
            ),
        }
        return self._commit_version(
            meta=meta,
            record_id=value.assignment_id,
            version_id=value.version_id,
            family="role-assignment",
            scope=f"{value.target_type.value}:{value.target_id}:{value.role}",
            content=content,
            effective=value.effective,
            expected_version_id=value.expected_version_id,
            relationship_reason=value.relationship_reason,
            project=project,
            reason_outcome="INCREMENT_2_ROLE_ASSIGNMENT_VALID",
            after_version=after_version,
        )

    def _targets_with_case_context(
        self,
        transaction: Increment2Transaction,
        target_type: RoleTargetType,
        target_id: str,
    ) -> tuple[tuple[str, str], ...]:
        targets: list[tuple[str, str]] = [(target_type.value, target_id)]
        if target_type is RoleTargetType.CONFIGURATION:
            owner = transaction.configuration_owning_case(RecordId.parse(target_id))
            if owner is None:
                return tuple(targets)
            targets.append((RoleTargetType.CASE.value, str(owner)))
        return tuple(targets)

    def _current_role_versions(
        self,
        transaction: Increment2Transaction,
        *,
        role: str,
        target_type: RoleTargetType,
        target_id: str,
        effective_at: datetime,
        known_at: datetime,
    ) -> tuple[RecordVersionId, ...]:
        targets = self._targets_with_case_context(transaction, target_type, target_id)
        assignment_ids = transaction.role_assignment_records(role=role, targets=targets)
        versions: list[RecordVersionId] = []
        for assignment_id in assignment_ids:
            history = transaction.get_history(assignment_id)
            if not history.versions:
                continue
            exemplar = next(iter(history.versions))
            result = transaction.select_current(
                SelectionQuery(
                    family="role-assignment",
                    scope=exemplar.scope,
                    effective_at=effective_at,
                    known_at=known_at,
                    record_id=assignment_id,
                )
            )
            if isinstance(result, SelectionFound):
                versions.append(result.candidate.version_id)
            elif isinstance(result, SelectionConflict):
                versions.extend(candidate.version_id for candidate in result.candidates)
        return tuple(versions)

    def resolve_role_performers(
        self,
        *,
        role: str,
        target_type: RoleTargetType,
        target_id: str,
        effective_at: datetime,
        known_at: datetime | None = None,
    ) -> tuple[RecordVersionId, ...]:
        effective_at = require_utc(effective_at)
        knowledge_time = require_utc(known_at or self._clock.now())
        with self._store.read_transaction() as transaction:
            return self._current_role_versions(
                transaction,
                role=role,
                target_type=target_type,
                target_id=target_id,
                effective_at=effective_at,
                known_at=knowledge_time,
            )

    def _resolve_accountability(
        self,
        transaction: Increment2Transaction,
        *,
        role: str,
        target_type: RoleTargetType,
        target_id: str,
        effective_at: datetime,
        known_at: datetime,
        mechanism: str | None = None,
    ) -> AccountabilityResolution:
        versions = self._current_role_versions(
            transaction,
            role=role,
            target_type=target_type,
            target_id=target_id,
            effective_at=effective_at,
            known_at=known_at,
        )
        accountable_values: list[RecordVersionId] = []
        for version_id in versions:
            detail = transaction.role_assignment_detail(version_id)
            if detail is not None and detail.accountable:
                accountable_values.append(version_id)
        accountable = tuple(accountable_values)
        if mechanism:
            if accountable:
                return AccountabilityConflict(frozenset(accountable))
            return AccountabilityFound(assignment_version_id=None, mechanism=mechanism)
        if not accountable:
            return AccountabilityVacant()
        if len(accountable) == 1:
            return AccountabilityFound(assignment_version_id=accountable[0], mechanism=None)
        return AccountabilityConflict(frozenset(accountable))

    def resolve_accountability(
        self,
        *,
        role: str,
        target_type: RoleTargetType,
        target_id: str,
        effective_at: datetime,
        known_at: datetime | None = None,
        mechanism: str | None = None,
    ) -> AccountabilityResolution:
        effective_at = require_utc(effective_at)
        knowledge_time = require_utc(known_at or self._clock.now())
        with self._store.read_transaction() as transaction:
            return self._resolve_accountability(
                transaction,
                role=role,
                target_type=target_type,
                target_id=target_id,
                effective_at=effective_at,
                known_at=knowledge_time,
                mechanism=mechanism,
            )

    def _validate_accountable_provenance(
        self,
        transaction: Increment2Transaction,
        *,
        assignment_version_id: RecordVersionId | None,
        mechanism: str | None,
        effective_at: datetime,
        known_at: datetime,
    ) -> None:
        if not _accountability_pair_valid(assignment_version_id, mechanism):
            raise DomainRuleViolation("exactly one accountable assignment or mechanism is required")
        if mechanism:
            return
        assert assignment_version_id is not None
        detail = transaction.role_assignment_detail(assignment_version_id)
        if detail is None or not detail.accountable:
            raise DomainRuleViolation(
                "accountable provenance must reference an accountable assignment"
            )
        result = self._resolve_accountability(
            transaction,
            role=detail.role,
            target_type=detail.target_type,
            target_id=detail.target_id,
            effective_at=effective_at,
            known_at=known_at,
        )
        if (
            not isinstance(result, AccountabilityFound)
            or result.assignment_version_id != assignment_version_id
        ):
            raise DomainRuleViolation(
                "vacant or conflicting accountability blocks authoritative use"
            )

    def commit_governing_designation(
        self, meta: CommandMeta, value: GoverningDesignationInput
    ) -> CommandOutcome:
        recorded_at = self._clock.now()

        def project(transaction: Increment2Transaction) -> None:
            context = transaction.configuration_version_context(value.configuration_version_id)
            if context is None:
                raise DomainRuleViolation(
                    "governing designation requires an exact Configuration version"
                )
            if context.owning_case_id != value.case_id or context.maturity != "finalized":
                raise DomainRuleViolation(
                    "governing Configuration must be finalized and owned by the designated Case"
                )
            self._validate_accountable_provenance(
                transaction,
                assignment_version_id=value.accountable_assignment_version_id,
                mechanism=value.accountable_mechanism,
                effective_at=value.effective.start,
                known_at=recorded_at,
            )
            transaction.add_governing_designation(
                version_id=value.version_id,
                case_id=value.case_id,
                configuration_version_id=value.configuration_version_id,
                accountable_assignment_version_id=value.accountable_assignment_version_id,
                accountable_mechanism=value.accountable_mechanism,
            )

        content: dict[str, JsonValue] = {
            "case_id": str(value.case_id),
            "configuration_version_id": str(value.configuration_version_id),
            "accountable_assignment_version_id": (
                str(value.accountable_assignment_version_id)
                if value.accountable_assignment_version_id
                else None
            ),
            "accountable_mechanism": value.accountable_mechanism,
        }
        return self._commit_version(
            meta=meta,
            record_id=value.designation_id,
            version_id=value.version_id,
            family="governing-configuration-designation",
            scope=f"case:{value.case_id}",
            content=content,
            effective=value.effective,
            expected_version_id=value.expected_version_id,
            relationship_reason=value.relationship_reason,
            project=project,
            reason_outcome="INCREMENT_2_GOVERNING_DESIGNATION_VALID",
        )

    def _select_governing(
        self,
        transaction: Increment2Transaction,
        *,
        case_id: RecordId,
        effective_at: datetime,
        known_at: datetime,
    ) -> GoverningConfigurationSelection:
        result = transaction.select_current(
            SelectionQuery(
                family="governing-configuration-designation",
                scope=f"case:{case_id}",
                effective_at=effective_at,
                known_at=known_at,
            )
        )
        if isinstance(result, SelectionAbsent):
            return GoverningConfigurationAbsent()
        if isinstance(result, SelectionFound):
            row = transaction.governing_designation_detail(result.candidate.version_id)
            assert row is not None
            return GoverningConfigurationFound(
                designation_version_id=result.candidate.version_id,
                configuration_version_id=row.configuration_version_id,
            )
        designation_ids = frozenset(candidate.version_id for candidate in result.candidates)
        configuration_values: set[RecordVersionId] = set()
        for candidate in result.candidates:
            detail = transaction.governing_designation_detail(candidate.version_id)
            assert detail is not None
            configuration_values.add(detail.configuration_version_id)
        configuration_ids = frozenset(configuration_values)
        return GoverningConfigurationConflict(designation_ids, configuration_ids)

    def select_governing_configuration(
        self,
        *,
        case_id: RecordId,
        effective_at: datetime,
        known_at: datetime | None = None,
    ) -> GoverningConfigurationSelection:
        effective_at = require_utc(effective_at)
        knowledge_time = require_utc(known_at or self._clock.now())
        with self._store.read_transaction() as transaction:
            return self._select_governing(
                transaction,
                case_id=case_id,
                effective_at=effective_at,
                known_at=knowledge_time,
            )

    def commit_determination(
        self, meta: CommandMeta, value: ConfigurationDeterminationInput
    ) -> CommandOutcome:
        allowed = {
            DeterminationKind.MATERIALITY: {
                DeterminationOutcome.MATERIAL,
                DeterminationOutcome.NON_MATERIAL,
            },
            DeterminationKind.IDENTITY_CONTINUITY: {
                DeterminationOutcome.SAME_IDENTITY,
                DeterminationOutcome.NEW_IDENTITY,
            },
        }
        if value.outcome not in allowed[value.kind] or not value.rationale.strip():
            raise DomainRuleViolation("determination outcome/rationale is incomplete or mismatched")
        recorded_at = self._clock.now()

        def project(transaction: Increment2Transaction) -> None:
            if transaction.configuration_version_context(value.configuration_version_id) is None:
                raise DomainRuleViolation("determination requires an exact Configuration version")
            self._validate_accountable_provenance(
                transaction,
                assignment_version_id=value.accountable_assignment_version_id,
                mechanism=value.accountable_mechanism,
                effective_at=value.effective.start,
                known_at=recorded_at,
            )
            transaction.add_configuration_determination(
                version_id=value.version_id,
                configuration_version_id=value.configuration_version_id,
                determination_kind=value.kind.value,
                outcome=value.outcome.value,
                rationale=value.rationale,
                accountable_assignment_version_id=value.accountable_assignment_version_id,
                accountable_mechanism=value.accountable_mechanism,
            )

        content: dict[str, JsonValue] = {
            "configuration_version_id": str(value.configuration_version_id),
            "determination_kind": value.kind.value,
            "outcome": value.outcome.value,
            "rationale": value.rationale,
            "accountable_assignment_version_id": (
                str(value.accountable_assignment_version_id)
                if value.accountable_assignment_version_id
                else None
            ),
            "accountable_mechanism": value.accountable_mechanism,
        }
        return self._commit_version(
            meta=meta,
            record_id=value.determination_id,
            version_id=value.version_id,
            family="configuration-determination",
            scope=f"configuration-version:{value.configuration_version_id}:{value.kind.value}",
            content=content,
            effective=value.effective,
            expected_version_id=value.expected_version_id,
            relationship_reason=value.relationship_reason,
            project=project,
            reason_outcome="INCREMENT_2_ACCOUNTABLE_DETERMINATION_VALID",
        )

    def current_lifecycle_state(
        self, *, case_id: RecordId, effective_at: datetime, known_at: datetime | None = None
    ) -> CaseLifecycleState:
        effective_at = require_utc(effective_at)
        knowledge_time = require_utc(known_at or self._clock.now())
        with self._store.read_transaction() as transaction:
            selection = transaction.select_current(
                SelectionQuery(
                    family="case",
                    scope=f"case:{case_id}",
                    effective_at=effective_at,
                    known_at=knowledge_time,
                    record_id=case_id,
                )
            )
            if not isinstance(selection, SelectionFound):
                raise DomainRuleViolation("Case is absent or has conflicting current versions")
            history = transaction.get_history(case_id)
            events = sorted(
                (
                    event
                    for event in history.status_events
                    if event.effective_at <= effective_at
                    and event.recorded_at <= knowledge_time
                    and event.new_status in {state.value for state in CaseLifecycleState}
                ),
                key=lambda event: (event.effective_at, event.recorded_at, str(event.event_id)),
            )
            return CaseLifecycleState(events[-1].new_status) if events else CaseLifecycleState.OPEN

    def transition_case(
        self,
        meta: CommandMeta,
        *,
        case_id: RecordId,
        target_state: CaseLifecycleState,
        effective_at: datetime,
    ) -> LifecycleTransitionResult:
        effective_at = require_utc(effective_at)
        recorded_at = self._clock.now()
        if target_state is not CaseLifecycleState.CONFIGURATION_DEFINED:
            return LifecycleTransitionResult(
                accepted=False,
                state=self.current_lifecycle_state(case_id=case_id, effective_at=effective_at),
                reason="LATER VALUE/RISK/EVIDENCE PREREQUISITES UNAVAILABLE",
            )
        with self._store.semantic_transaction() as transaction:
            case_selection = transaction.select_current(
                SelectionQuery(
                    family="case",
                    scope=f"case:{case_id}",
                    effective_at=effective_at,
                    known_at=recorded_at,
                    record_id=case_id,
                )
            )
            if not isinstance(case_selection, SelectionFound):
                raise DomainRuleViolation("Case is absent or conflicting")
            history = transaction.get_history(case_id)
            lifecycle_events = [
                event
                for event in history.status_events
                if event.effective_at <= effective_at
                and event.recorded_at <= recorded_at
                and event.new_status in {state.value for state in CaseLifecycleState}
            ]
            lifecycle_events.sort(
                key=lambda event: (event.effective_at, event.recorded_at, str(event.event_id))
            )
            current_state = (
                CaseLifecycleState(lifecycle_events[-1].new_status)
                if lifecycle_events
                else CaseLifecycleState.OPEN
            )
            payload: dict[str, JsonValue] = {
                "case_id": str(case_id),
                "target_state": target_state.value,
                "effective_at": effective_at.isoformat(),
                "principal_id": meta.principal_id,
                "actor_id": meta.actor_id,
            }
            digest = canonical_command_digest(payload)
            replay = transaction.get_idempotency(meta.idempotency_scope, meta.idempotency_key)
            if replay is not None:
                if replay.digest != digest:
                    raise DomainPreconditionFailed("IDEMPOTENCY KEY REUSE CONFLICT")
                return LifecycleTransitionResult(
                    True,
                    target_state,
                    "TRANSITION COMMITTED",
                    replay.outcome.status_event_ids[0],
                )
            if current_state is not CaseLifecycleState.OPEN:
                raise DomainRuleViolation("invalid or duplicate lifecycle transition")
            governing = self._select_governing(
                transaction,
                case_id=case_id,
                effective_at=effective_at,
                known_at=recorded_at,
            )
            if isinstance(governing, GoverningConfigurationAbsent):
                return LifecycleTransitionResult(False, current_state, governing.reason)
            if isinstance(governing, GoverningConfigurationConflict):
                return LifecycleTransitionResult(False, current_state, governing.reason)
            event = StatusEvent(
                event_id=EventId.new(),
                target_version_id=case_selection.candidate.version_id,
                prior_status=current_state.value,
                new_status=target_state.value,
                recorded_at=recorded_at,
                effective_at=effective_at,
                actor=meta.actor_id or meta.actor_resolution.value,
                basis=f"governing designation {governing.designation_version_id}",
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
                affected_version_ids=(case_selection.candidate.version_id,),
                expected_precondition=current_state.value,
                observed_precondition=current_state.value,
                effective_at=effective_at,
                recorded_at=recorded_at,
                reason_outcomes=("GOVERNING_CONFIGURATION_GUARD_SATISFIED",),
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

    def link_cases(self, meta: CommandMeta, value: CaseLinkInput) -> CommandOutcome:
        recorded_at = self._clock.now()
        effective_at = require_utc(value.effective_at)
        payload: dict[str, JsonValue] = {
            "link_id": value.link_id,
            "source_case_id": str(value.source_case_id),
            "target_case_id": str(value.target_case_id),
            "relationship_type": value.relationship_type,
            "effective_at": effective_at.isoformat(),
            "reason": value.reason,
            "principal_id": meta.principal_id,
            "actor_id": meta.actor_id,
        }
        digest = canonical_command_digest(payload)
        with self._store.semantic_transaction() as transaction:
            replay = transaction.get_idempotency(meta.idempotency_scope, meta.idempotency_key)
            if replay is not None:
                if replay.digest != digest:
                    raise DomainPreconditionFailed("IDEMPOTENCY KEY REUSE CONFLICT")
                return replay.outcome
            if not transaction.case_exists(value.source_case_id) or not transaction.case_exists(
                value.target_case_id
            ):
                raise DomainRuleViolation("linked Cases must both exist")
            transaction.add_case_link(
                link_id=value.link_id,
                source_case_id=value.source_case_id,
                target_case_id=value.target_case_id,
                relationship_type=value.relationship_type,
                recorded_at_us=to_epoch_microseconds(recorded_at),
                effective_at_us=to_epoch_microseconds(effective_at),
                actor_id=meta.actor_id or meta.actor_resolution.value,
                reason=value.reason,
            )
            audit = AuditFact(
                audit_id=AuditId.new(),
                principal_id=meta.principal_id,
                actor_id=meta.actor_id,
                actor_resolution=meta.actor_resolution,
                operation="LINK_CASES",
                result="COMMITTED",
                command_id=meta.command_id,
                idempotency_scope=meta.idempotency_scope,
                idempotency_key=meta.idempotency_key,
                correlation_id=meta.correlation_id,
                causation_id=meta.causation_id,
                target_record_id=value.source_case_id,
                affected_version_ids=(),
                expected_precondition="BOTH CASES EXIST",
                observed_precondition="BOTH CASES EXIST",
                effective_at=effective_at,
                recorded_at=recorded_at,
                reason_outcomes=("INCREMENT_2_LINKED_CASE_RELATIONSHIP",),
                request_digest=digest,
            )
            transaction.add_audit(audit)
            outcome = CommandOutcome(
                command_id=str(meta.command_id),
                record_id=str(value.source_case_id),
                version_ids=(),
                status_event_ids=(),
                relationship_ids=(value.link_id,),
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
            return outcome
