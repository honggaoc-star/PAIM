"""Atomic prospective continuing-Case commands and selectors."""

from __future__ import annotations

import json
from contextlib import AbstractContextManager
from datetime import datetime
from typing import Protocol, cast

from paim.audit.models import ActorResolution, AuditFact
from paim.case_continuity.models import (
    CaseInitiationAuthorityCommand,
    CaseInitiationAuthorityState,
    CommandIdentity,
    ConfigurationSuccessorCommand,
    ContinuitySelection,
    ContinuitySelectionKind,
    ContinuityStatus,
    DeterminationKind,
    DeterminationOutcome,
    LegacyLifecycleView,
    MinimalOpenCaseCommand,
    OpenCaseCommand,
    OpeningFacts,
    TransitionCaseCommand,
    TransitionFacts,
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
from paim.integrity.semantics import (
    ContextMemberKind,
    ExactContextMember,
    ExactContextSet,
    SemanticContractRef,
)
from paim.integrity.time import Clock, EffectiveInterval, to_epoch_microseconds
from paim.persistence.ports import CommandOutcome, IdempotencyFact, RecordHistory
from paim.responsibility.models import ObligationKind, responsibility_signature
from paim.responsibility.service import ProjectionFact, ResponsibilityWorkService, SliceACommand


class ContinuityTransaction(Protocol):
    def get_idempotency(self, scope: str, key: str) -> IdempotencyFact | None: ...
    def add_idempotency(self, fact: IdempotencyFact) -> None: ...
    def add_version(self, version: FinalizedRecordVersion) -> None: ...
    def add_audit(self, fact: AuditFact) -> None: ...
    def add_relationship(self, relationship: VersionRelationship) -> None: ...
    def add_status_event(self, event: StatusEvent) -> None: ...
    def get_version(self, version_id: RecordVersionId) -> FinalizedRecordVersion | None: ...
    def get_history(self, record_id: RecordId) -> RecordHistory: ...
    def select_current(self, query: SelectionQuery) -> object: ...
    def case_exists(self, case_id: RecordId) -> bool: ...
    def add_case(self, case_id: RecordId, version_id: RecordVersionId) -> None: ...
    def add_configuration(
        self,
        *,
        configuration_id: RecordId,
        version_id: RecordVersionId,
        owning_case_id: RecordId,
        maturity: str,
        purpose: str,
    ) -> None: ...
    def configuration_owning_case(self, configuration_id: RecordId) -> RecordId | None: ...
    def add_governing_designation(
        self,
        *,
        version_id: RecordVersionId,
        case_id: RecordId,
        configuration_version_id: RecordVersionId,
        accountable_assignment_version_id: RecordVersionId | None,
        accountable_mechanism: str | None,
    ) -> None: ...
    def insert_projection(self, table_name: str, values: dict[str, object]) -> None: ...
    def projection_rows(
        self, table_name: str, **equals: object
    ) -> tuple[dict[str, object], ...]: ...


class ContinuityStore(Protocol):
    def semantic_transaction(self) -> AbstractContextManager[ContinuityTransaction]: ...
    def read_transaction(self) -> AbstractContextManager[ContinuityTransaction]: ...


class ContinuityAccessPolicy(Protocol):
    def authorize(
        self,
        *,
        principal_id: str,
        actor_id: str,
        action: str,
        case_id: RecordId,
        write: bool,
        source_version_id: RecordVersionId | None = None,
        source_family: str | None = None,
        effective_at: datetime | None = None,
        known_at: datetime | None = None,
        configuration_id: RecordId | None = None,
    ) -> bool: ...


class CaseContinuityConflict(RuntimeError):
    pass


class CaseContinuityAccessDenied(RuntimeError):
    def __init__(self) -> None:
        super().__init__("software access not established")


_ALLOWED_TRANSITIONS = {
    (
        ContinuityStatus.OPEN,
        DeterminationKind.CASE_CLOSURE,
        DeterminationOutcome.CLOSE,
    ): ContinuityStatus.CLOSED,
    (
        ContinuityStatus.CLOSED,
        DeterminationKind.CASE_REOPENING,
        DeterminationOutcome.REOPEN_SAME_CASE,
    ): ContinuityStatus.OPEN,
    (
        ContinuityStatus.OPEN,
        DeterminationKind.CASE_SUPERSESSION,
        DeterminationOutcome.SUPERSEDE_WITH_SUCCESSOR,
    ): ContinuityStatus.SUPERSEDED,
    (
        ContinuityStatus.CLOSED,
        DeterminationKind.CASE_SUPERSESSION,
        DeterminationOutcome.SUPERSEDE_WITH_SUCCESSOR,
    ): ContinuityStatus.SUPERSEDED,
}


class CaseContinuityService:
    """Natural prospective Case commands over one outer semantic transaction."""

    def __init__(
        self, store: ContinuityStore, clock: Clock, access_policy: ContinuityAccessPolicy
    ) -> None:
        self._store = store
        self._clock = clock
        self._access = access_policy

    def record_case_initiation_authority(
        self, command: CaseInitiationAuthorityCommand
    ) -> CommandOutcome:
        """Record an externally grounded pre-Case organizational mandate."""

        action = "case.initiation-authority.record"
        digest = canonical_command_digest(
            {
                "action": action,
                "record_id": str(command.record_id),
                "version_id": str(command.version_id),
                "authorized_actor_id": str(command.authorized_actor_id),
                "organization_scope": command.organization_scope,
                "allowed_use_prefixes": list(command.allowed_use_prefixes),
                "provenance": command.provenance,
                "state": command.state.value,
                "expected_version_id": (
                    str(command.expected_version_id) if command.expected_version_id else None
                ),
                "effective_at": command.effective_at.isoformat(),
                "contract": command.contract.key,
                "context": command.context.digest,
            }
        )
        self._require_access(
            command.identity.principal_id,
            command.identity.actor_id,
            action,
            command.record_id,
            True,
        )
        recorded_at = self._clock.now()
        with self._store.semantic_transaction() as tx:
            replay = self._replay(
                tx, command.identity.idempotency_scope, command.identity.idempotency_key, digest
            )
            if replay is not None:
                return replay
            self._require_access(
                command.identity.principal_id,
                command.identity.actor_id,
                action,
                command.record_id,
                True,
            )
            relationships: tuple[RelationshipId, ...] = ()
            relationship: VersionRelationship | None = None
            if command.expected_version_id is None:
                observed = tx.select_current(
                    SelectionQuery(
                        "case-initiation-authority",
                        f"organization:{command.organization_scope}",
                        command.effective_at,
                        recorded_at,
                        command.record_id,
                    )
                )
                if not isinstance(observed, SelectionAbsent):
                    raise CaseContinuityConflict("expected absent Case-initiation authority")
            else:
                predecessor = tx.get_version(command.expected_version_id)
                selected = tx.select_current(
                    SelectionQuery(
                        "case-initiation-authority",
                        f"organization:{command.organization_scope}",
                        command.effective_at,
                        recorded_at,
                        command.record_id,
                    )
                )
                if (
                    predecessor is None
                    or not isinstance(selected, SelectionFound)
                    or selected.candidate.version_id != command.expected_version_id
                ):
                    raise CaseContinuityConflict("stale Case-initiation authority predecessor")
                relationship = VersionRelationship(
                    RelationshipId.new(),
                    command.expected_version_id,
                    command.version_id,
                    RelationshipType.SUPERSESSION,
                    recorded_at,
                    "Case-initiation authority succession",
                )
                relationships = (relationship.relationship_id,)
            self._ensure_contract_context(tx, command.contract, command.context, recorded_at)
            self._add_version(
                tx,
                command.record_id,
                command.version_id,
                "case-initiation-authority",
                f"organization:{command.organization_scope}",
                {
                    "case_initiation_authority": {
                        "authorized_actor_id": str(command.authorized_actor_id),
                        "organization_scope": command.organization_scope,
                        "permitted_acts": ["CREATE_OPEN_CASE"],
                        "allowed_use_prefixes": list(command.allowed_use_prefixes),
                        "initial_responsibility": "DETERMINE_CASE_CONTINUITY",
                        "initial_assignment_limits": {
                            "continuity_actions": [value.value for value in DeterminationKind]
                        },
                        "initial_assignment_max_active": 1,
                        "downstream_authority_granted": False,
                    },
                    "provenance": command.provenance,
                    "state": command.state.value,
                },
                command.effective_at,
                recorded_at,
                command.identity.actor_id,
                command.contract,
                command.context,
            )
            if relationship is not None:
                tx.add_relationship(relationship)
            tx.insert_projection(
                "case_initiation_authority_versions",
                {
                    "version_id": str(command.version_id),
                    "record_id": str(command.record_id),
                    "authorized_actor_id": str(command.authorized_actor_id),
                    "organization_scope": command.organization_scope,
                    "allowed_use_prefixes_json": json.dumps(list(command.allowed_use_prefixes)),
                    "provenance_json": json.dumps(
                        command.provenance, sort_keys=True, separators=(",", ":")
                    ),
                    "state": command.state.value,
                    "predecessor_version_id": (
                        str(command.expected_version_id) if command.expected_version_id else None
                    ),
                    "recorded_at_us": to_epoch_microseconds(recorded_at),
                },
            )
            return self._finish(
                tx,
                command.identity,
                digest,
                command.record_id,
                (command.version_id,),
                (),
                relationships,
                command.effective_at,
                recorded_at,
                command.context,
                ("PRE_CASE_INITIATION_AUTHORITY_RECORDED", command.state.value),
            )

    def initiate_case(self, request: MinimalOpenCaseCommand) -> CommandOutcome:
        """Open one Case without exposing generated semantic identities to the caller."""

        digest = canonical_command_digest(
            {
                "action": "CREATE_OPEN_CASE",
                "organization_scope": request.organization_scope,
                "contract": request.contract.key,
                "title": request.title,
                "bounded_use": request.bounded_use,
                "management_question": request.management_question,
                "configuration": request.configuration_content,
                "configuration_maturity": request.configuration_maturity,
                "configuration_purpose": request.configuration_purpose,
                "effective_at": request.effective_at.isoformat(),
                "knowledge_cutoff": request.knowledge_cutoff.isoformat(),
                "actor": str(request.identity.actor_id),
                "principal": request.identity.principal_id,
            }
        )
        with self._store.read_transaction() as tx:
            replay = self._replay(
                tx,
                request.identity.idempotency_scope,
                request.identity.idempotency_key,
                digest,
            )
        if replay is not None:
            self._require_access(
                request.identity.principal_id,
                request.identity.actor_id,
                "case.create_open",
                RecordId.parse(replay.record_id),
                True,
            )
            return replay
        facts = OpeningFacts.new()
        context = ExactContextSet.create(
            (
                ExactContextMember("case", ContextMemberKind.RECORD, str(facts.case_id)),
                ExactContextMember(
                    "configuration_version",
                    ContextMemberKind.VERSION,
                    str(facts.configuration_version_id),
                ),
                ExactContextMember("bounded_use", ContextMemberKind.LITERAL, request.bounded_use),
            )
        )
        authority_id = self._select_case_initiation_authority(
            actor_id=request.identity.actor_id,
            organization_scope=request.organization_scope,
            bounded_use=request.bounded_use,
            effective_at=request.effective_at,
        )
        command = OpenCaseCommand(
            request.identity,
            facts,
            request.contract,
            context,
            request.title,
            request.bounded_use,
            request.management_question,
            request.configuration_content,
            request.configuration_maturity,
            request.configuration_purpose,
            authority_id,
            authority_id,
            request.effective_at,
            request.knowledge_cutoff,
            request.organization_scope,
        )
        return self._open_case(command, digest)

    def open_case(self, command: OpenCaseCommand) -> CommandOutcome:
        return self._open_case(command, canonical_command_digest(self._open_payload(command)))

    def _open_case(self, command: OpenCaseCommand, digest: str) -> CommandOutcome:
        action = "case.create_open"
        self._require_access(
            command.identity.principal_id,
            command.identity.actor_id,
            action,
            command.facts.case_id,
            True,
        )
        recorded_at = self._clock.now()
        with self._store.semantic_transaction() as tx:
            replay = self._replay(
                tx, command.identity.idempotency_scope, command.identity.idempotency_key, digest
            )
            if replay is not None:
                return replay
            self._require_access(
                command.identity.principal_id,
                command.identity.actor_id,
                action,
                command.facts.case_id,
                True,
            )
            if tx.case_exists(command.facts.case_id):
                raise CaseContinuityConflict("prospective Case identity already exists")
            if command.initiation_scope is not None:
                self._require_case_initiation_authority(
                    tx,
                    version_id=command.authority_source_version_id,
                    actor_id=command.identity.actor_id,
                    organization_scope=command.initiation_scope,
                    bounded_use=command.bounded_use,
                    effective_at=command.effective_at,
                    known_at=recorded_at,
                )
            else:
                self._require_authority_source(
                    tx,
                    version_id=command.authority_source_version_id,
                    actor_id=command.identity.actor_id,
                    case_id=command.facts.case_id,
                    action="CREATE_OPEN_CASE",
                    context=command.context,
                    effective_at=command.effective_at,
                    known_at=recorded_at,
                )
            self._ensure_contract_context(tx, command.contract, command.context, recorded_at)
            f = command.facts
            versions: list[RecordVersionId] = []
            case_content: dict[str, JsonValue] = {
                "title": command.title,
                "bounded_use": command.bounded_use,
                "management_question": command.management_question,
            }
            if command.initiation_scope is not None:
                case_content["case_initiation"] = {
                    "authority_source_version_id": str(command.authority_source_version_id),
                    "responsibility_version_id": str(f.responsibility_version_id),
                    "assignment_basis_version_id": str(f.assignment_basis_version_id),
                    "assignment_version_id": str(f.assignment_version_id),
                }
            self._add_version(
                tx,
                f.case_id,
                f.case_version_id,
                "prospective-case",
                f"case:{f.case_id}",
                case_content,
                command.effective_at,
                recorded_at,
                command.identity.actor_id,
                command.contract,
                command.context,
            )
            tx.add_case(f.case_id, f.case_version_id)
            versions.append(f.case_version_id)
            self._add_version(
                tx,
                f.configuration_id,
                f.configuration_version_id,
                "managed-configuration",
                f"case:{f.case_id}",
                command.configuration_content,
                command.effective_at,
                recorded_at,
                command.identity.actor_id,
                command.contract,
                command.context,
            )
            tx.add_configuration(
                configuration_id=f.configuration_id,
                version_id=f.configuration_version_id,
                owning_case_id=f.case_id,
                maturity=command.configuration_maturity,
                purpose=command.configuration_purpose,
            )
            versions.append(f.configuration_version_id)
            signature = self._opening_responsibility(tx, command, recorded_at)
            versions.extend(
                (
                    f.responsibility_version_id,
                    f.assignment_basis_version_id,
                    f.assignment_version_id,
                )
            )
            self._add_version(
                tx,
                f.designation_record_id,
                f.designation_version_id,
                "governing-configuration",
                f"case:{f.case_id}",
                {"configuration_version_id": str(f.configuration_version_id)},
                command.effective_at,
                recorded_at,
                command.identity.actor_id,
                command.contract,
                command.context,
            )
            tx.add_governing_designation(
                version_id=f.designation_version_id,
                case_id=f.case_id,
                configuration_version_id=f.configuration_version_id,
                accountable_assignment_version_id=None,
                accountable_mechanism=(
                    f"prospective Responsibility {f.responsibility_version_id}; "
                    f"assignment {f.assignment_version_id}"
                ),
            )
            versions.append(f.designation_version_id)
            self._add_version(
                tx,
                f.status_record_id,
                f.status_version_id,
                "case-continuity-status",
                f"case:{f.case_id}",
                {
                    "status": ContinuityStatus.OPEN.value,
                    "prior_status": None,
                    "rationale": "bounded Case opened",
                },
                command.effective_at,
                recorded_at,
                command.identity.actor_id,
                command.contract,
                command.context,
            )
            tx.insert_projection(
                "case_continuity_status_records",
                {"record_id": str(f.status_record_id), "case_id": str(f.case_id)},
            )
            tx.insert_projection(
                "case_continuity_status_versions",
                {
                    "version_id": str(f.status_version_id),
                    "record_id": str(f.status_record_id),
                    "case_id": str(f.case_id),
                    "status": "OPEN",
                    "prior_status": None,
                    "determination_version_id": None,
                    "responsibility_version_id": str(f.responsibility_version_id),
                    "assignment_version_id": str(f.assignment_version_id),
                    "authority_basis_version_id": str(command.authority_source_version_id),
                    "knowledge_cutoff_us": to_epoch_microseconds(command.knowledge_cutoff),
                    "rationale": "bounded Case opened",
                    "effective_at_us": to_epoch_microseconds(command.effective_at),
                    "recorded_at_us": to_epoch_microseconds(recorded_at),
                    "predecessor_version_id": None,
                    "successor_case_id": None,
                },
            )
            versions.append(f.status_version_id)
            return self._finish(
                tx,
                command.identity,
                digest,
                f.case_id,
                tuple(versions),
                (),
                (),
                command.effective_at,
                recorded_at,
                command.context,
                ("PROSPECTIVE_CASE_OPENED", "EXACT_GOVERNING_CONFIGURATION", signature),
            )

    def transition_case(self, command: TransitionCaseCommand) -> CommandOutcome:
        action = f"case.continuity.{command.kind.value.casefold()}"
        digest = canonical_command_digest(self._transition_payload(command))
        self._require_access(
            command.identity.principal_id, command.identity.actor_id, action, command.case_id, True
        )
        recorded_at = self._clock.now()
        with self._store.semantic_transaction() as tx:
            replay = self._replay(
                tx, command.identity.idempotency_scope, command.identity.idempotency_key, digest
            )
            if replay is not None:
                return replay
            self._require_access(
                command.identity.principal_id,
                command.identity.actor_id,
                action,
                command.case_id,
                True,
            )
            selected = self._select_status_tx(
                tx, command.case_id, command.effective_at, recorded_at
            )
            if (
                selected.kind is not ContinuitySelectionKind.ONE
                or selected.version_ids != (command.expected_status_version_id,)
                or selected.status is not command.expected_status
            ):
                raise CaseContinuityConflict("stale or conflicting exact Case continuity status")
            target = _ALLOWED_TRANSITIONS.get(
                (command.expected_status, command.kind, command.outcome)
            )
            if target is None:
                raise CaseContinuityConflict(
                    "requested determination does not permit a status transition"
                )
            if command.expected_status is ContinuityStatus.SUPERSEDED:
                raise CaseContinuityConflict("SUPERSEDED Case is terminal")
            if target is ContinuityStatus.SUPERSEDED and command.successor_case_id is None:
                raise CaseContinuityConflict("supersession requires one named successor Case")
            if command.successor_case_id is not None and not tx.case_exists(
                command.successor_case_id
            ):
                raise CaseContinuityConflict("named successor Case is not established")
            self._validate_accountability(tx, command, recorded_at)
            if command.kind is DeterminationKind.CASE_CLOSURE:
                self._validate_closure(tx, command, recorded_at)
            self._ensure_contract_context(tx, command.contract, command.context, recorded_at)
            self._add_determination(tx, command, recorded_at)
            self._add_version(
                tx,
                command.status_record_id,
                command.facts.status_version_id,
                "case-continuity-status",
                f"case:{command.case_id}",
                {
                    "status": target.value,
                    "prior_status": command.expected_status.value,
                    "determination_version_id": str(command.facts.determination_version_id),
                    "rationale": command.rationale,
                },
                command.effective_at,
                recorded_at,
                command.identity.actor_id,
                command.contract,
                command.context,
            )
            tx.insert_projection(
                "case_continuity_status_versions",
                {
                    "version_id": str(command.facts.status_version_id),
                    "record_id": str(command.status_record_id),
                    "case_id": str(command.case_id),
                    "status": target.value,
                    "prior_status": command.expected_status.value,
                    "determination_version_id": str(command.facts.determination_version_id),
                    "responsibility_version_id": str(command.responsibility_version_id),
                    "assignment_version_id": str(command.assignment_version_id),
                    "authority_basis_version_id": str(command.authority_basis_version_id),
                    "knowledge_cutoff_us": to_epoch_microseconds(command.knowledge_cutoff),
                    "rationale": command.rationale,
                    "effective_at_us": to_epoch_microseconds(command.effective_at),
                    "recorded_at_us": to_epoch_microseconds(recorded_at),
                    "predecessor_version_id": str(command.expected_status_version_id),
                    "successor_case_id": str(command.successor_case_id)
                    if command.successor_case_id
                    else None,
                },
            )
            relationship = VersionRelationship(
                RelationshipId.new(),
                command.expected_status_version_id,
                command.facts.status_version_id,
                RelationshipType.SUPERSESSION,
                recorded_at,
                "exact prospective continuity transition",
            )
            tx.add_relationship(relationship)
            tx.insert_projection(
                "version_relationship_semantics",
                {
                    "relationship_id": str(relationship.relationship_id),
                    "contract_key": command.contract.key,
                    "context_digest": command.context.digest,
                },
            )
            event = StatusEvent(
                EventId.new(),
                command.expected_status_version_id,
                "CURRENT",
                "SUPERSEDED",
                recorded_at,
                command.effective_at,
                str(command.identity.actor_id),
                command.rationale,
            )
            tx.add_status_event(event)
            tx.insert_projection(
                "status_event_semantics",
                {
                    "event_id": str(event.event_id),
                    "contract_key": command.contract.key,
                    "context_digest": command.context.digest,
                },
            )
            if target is ContinuityStatus.SUPERSEDED:
                assert command.successor_case_id is not None
                tx.insert_projection(
                    "case_continuity_relationships",
                    {
                        "relationship_id": str(RelationshipId.new()),
                        "source_case_id": str(command.case_id),
                        "target_case_id": str(command.successor_case_id),
                        "relationship_kind": "SUPERSEDED_BY",
                        "determination_version_id": str(command.facts.determination_version_id),
                        "effective_at_us": to_epoch_microseconds(command.effective_at),
                        "recorded_at_us": to_epoch_microseconds(recorded_at),
                    },
                )
            return self._finish(
                tx,
                command.identity,
                digest,
                command.case_id,
                (command.facts.determination_version_id, command.facts.status_version_id),
                (event.event_id,),
                (relationship.relationship_id,),
                command.effective_at,
                recorded_at,
                command.context,
                (f"CASE_{target.value}", "ACCOUNTABLE_CONTINUITY_DETERMINATION"),
            )

    def continue_configuration(self, command: ConfigurationSuccessorCommand) -> CommandOutcome:
        """Append a same-Case Configuration successor without retargeting old facts."""
        action = "case.continuity.same_or_new_case"
        digest = canonical_command_digest(self._configuration_payload(command))
        self._require_access(
            command.identity.principal_id, command.identity.actor_id, action, command.case_id, True
        )
        recorded_at = self._clock.now()
        with self._store.semantic_transaction() as tx:
            replay = self._replay(
                tx, command.identity.idempotency_scope, command.identity.idempotency_key, digest
            )
            if replay is not None:
                return replay
            self._require_access(
                command.identity.principal_id,
                command.identity.actor_id,
                action,
                command.case_id,
                True,
            )
            status = self._select_status_tx(tx, command.case_id, command.effective_at, recorded_at)
            if status.status is not ContinuityStatus.OPEN or status.version_ids != (
                command.expected_status_version_id,
            ):
                raise CaseContinuityConflict(
                    "only exact current OPEN Case accepts Configuration continuity"
                )
            prior = tx.get_version(command.predecessor_configuration_version_id)
            if (
                prior is None
                or tx.configuration_owning_case(command.predecessor_configuration_id)
                != command.case_id
            ):
                raise CaseContinuityConflict(
                    "exact predecessor Configuration is not established in Case"
                )
            self._require_exact_current(
                tx, prior, command.effective_at, recorded_at, "stale predecessor Configuration"
            )
            designation = tx.get_version(command.expected_designation_version_id)
            if designation is None or designation.record_id != command.designation_record_id:
                raise CaseContinuityConflict(
                    "exact governing Configuration designation is not established"
                )
            governing = tx.select_current(
                SelectionQuery(
                    designation.family,
                    designation.scope,
                    command.effective_at,
                    recorded_at,
                )
            )
            if not (
                isinstance(governing, SelectionFound)
                and governing.candidate.version_id == designation.version_id
            ):
                raise CaseContinuityConflict("governing Configuration absence or conflict")
            shim = TransitionCaseCommand(
                command.identity,
                # status_version_id is unused by the determination writer
                TransitionFacts(
                    command.facts.determination_record_id,
                    command.facts.determination_version_id,
                    RecordVersionId.new(),
                ),
                command.contract,
                command.context,
                command.case_id,
                command.status_record_id,
                command.expected_status_version_id,
                ContinuityStatus.OPEN,
                DeterminationKind.SAME_OR_NEW_CASE,
                DeterminationOutcome.SAME_CASE,
                command.responsibility_version_id,
                command.assignment_version_id,
                command.authority_basis_version_id,
                command.rationale,
                command.factors,
                command.effective_at,
                command.knowledge_cutoff,
            )
            self._validate_accountability(tx, shim, recorded_at)
            self._ensure_contract_context(tx, command.contract, command.context, recorded_at)
            self._add_version(
                tx,
                command.facts.configuration_id,
                command.facts.configuration_version_id,
                "managed-configuration",
                f"case:{command.case_id}",
                command.configuration_content,
                command.effective_at,
                recorded_at,
                command.identity.actor_id,
                command.contract,
                command.context,
            )
            tx.add_configuration(
                configuration_id=command.facts.configuration_id,
                version_id=command.facts.configuration_version_id,
                owning_case_id=command.case_id,
                maturity=command.configuration_maturity,
                purpose=command.configuration_purpose,
            )
            self._add_determination(
                tx,
                shim,
                recorded_at,
                prior_configuration_version_id=command.predecessor_configuration_version_id,
                candidate_configuration_version_id=command.facts.configuration_version_id,
            )
            self._add_version(
                tx,
                command.designation_record_id,
                command.facts.designation_version_id,
                "governing-configuration",
                f"case:{command.case_id}",
                {"configuration_version_id": str(command.facts.configuration_version_id)},
                command.effective_at,
                recorded_at,
                command.identity.actor_id,
                command.contract,
                command.context,
            )
            tx.add_governing_designation(
                version_id=command.facts.designation_version_id,
                case_id=command.case_id,
                configuration_version_id=command.facts.configuration_version_id,
                accountable_assignment_version_id=None,
                accountable_mechanism=(
                    f"prospective Responsibility {command.responsibility_version_id}; "
                    f"assignment {command.assignment_version_id}"
                ),
            )
            rels: list[RelationshipId] = []
            events: list[EventId] = []
            for source, target, reason in (
                (
                    command.predecessor_configuration_version_id,
                    command.facts.configuration_version_id,
                    "same-Case Configuration successor",
                ),
                (
                    command.expected_designation_version_id,
                    command.facts.designation_version_id,
                    "new exact governing designation",
                ),
            ):
                rel = VersionRelationship(
                    RelationshipId.new(),
                    source,
                    target,
                    RelationshipType.SUPERSESSION,
                    recorded_at,
                    reason,
                )
                tx.add_relationship(rel)
                tx.insert_projection(
                    "version_relationship_semantics",
                    {
                        "relationship_id": str(rel.relationship_id),
                        "contract_key": command.contract.key,
                        "context_digest": command.context.digest,
                    },
                )
                rels.append(rel.relationship_id)
                event = StatusEvent(
                    EventId.new(),
                    source,
                    "CURRENT",
                    "SUPERSEDED",
                    recorded_at,
                    command.effective_at,
                    str(command.identity.actor_id),
                    reason,
                )
                tx.add_status_event(event)
                tx.insert_projection(
                    "status_event_semantics",
                    {
                        "event_id": str(event.event_id),
                        "contract_key": command.contract.key,
                        "context_digest": command.context.digest,
                    },
                )
                events.append(event.event_id)
            tx.insert_projection(
                "configuration_continuity_links",
                {
                    "relationship_id": command.facts.relationship_id,
                    "case_id": str(command.case_id),
                    "predecessor_configuration_version_id": str(
                        command.predecessor_configuration_version_id
                    ),
                    "successor_configuration_version_id": str(
                        command.facts.configuration_version_id
                    ),
                    "determination_version_id": str(command.facts.determination_version_id),
                    "recorded_at_us": to_epoch_microseconds(recorded_at),
                },
            )
            return self._finish(
                tx,
                command.identity,
                digest,
                command.case_id,
                (
                    command.facts.determination_version_id,
                    command.facts.configuration_version_id,
                    command.facts.designation_version_id,
                ),
                tuple(events),
                tuple(rels),
                command.effective_at,
                recorded_at,
                command.context,
                ("SAME_CASE_CONFIGURATION_SUCCESSOR", "NO_HISTORICAL_RETARGET"),
            )

    def relate_new_case(self, command: TransitionCaseCommand) -> CommandOutcome:
        """Record an accountable NEW_CASE_REQUIRED result without moving source status."""
        if (
            command.kind is not DeterminationKind.SAME_OR_NEW_CASE
            or command.outcome is not DeterminationOutcome.NEW_CASE_REQUIRED
            or command.successor_case_id is None
        ):
            raise CaseContinuityConflict("new-Case routing requires exact accountable outcome")
        action = "case.continuity.same_or_new_case"
        digest = canonical_command_digest(self._transition_payload(command))
        self._require_access(
            command.identity.principal_id,
            command.identity.actor_id,
            action,
            command.case_id,
            True,
        )
        recorded_at = self._clock.now()
        with self._store.semantic_transaction() as tx:
            replay = self._replay(
                tx,
                command.identity.idempotency_scope,
                command.identity.idempotency_key,
                digest,
            )
            if replay is not None:
                return replay
            self._require_access(
                command.identity.principal_id,
                command.identity.actor_id,
                action,
                command.case_id,
                True,
            )
            selected = self._select_status_tx(
                tx, command.case_id, command.effective_at, recorded_at
            )
            if (
                selected.kind is not ContinuitySelectionKind.ONE
                or selected.version_ids != (command.expected_status_version_id,)
                or selected.status is not command.expected_status
            ):
                raise CaseContinuityConflict("stale or conflicting exact Case continuity status")
            if not tx.case_exists(command.successor_case_id):
                raise CaseContinuityConflict("named new Case is not established")
            self._validate_accountability(tx, command, recorded_at)
            self._ensure_contract_context(tx, command.contract, command.context, recorded_at)
            self._add_determination(tx, command, recorded_at)
            relationship_id = str(RelationshipId.new())
            tx.insert_projection(
                "case_continuity_relationships",
                {
                    "relationship_id": relationship_id,
                    "source_case_id": str(command.case_id),
                    "target_case_id": str(command.successor_case_id),
                    "relationship_kind": "RELATED_NEW_CASE",
                    "determination_version_id": str(command.facts.determination_version_id),
                    "effective_at_us": to_epoch_microseconds(command.effective_at),
                    "recorded_at_us": to_epoch_microseconds(recorded_at),
                },
            )
            return self._finish(
                tx,
                command.identity,
                digest,
                command.case_id,
                (command.facts.determination_version_id,),
                (),
                (),
                command.effective_at,
                recorded_at,
                command.context,
                ("NEW_CASE_REQUIRED", "NO_AUTHORITY_OR_HISTORY_TRANSFER"),
            )

    def select_status(
        self,
        *,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        effective_at: datetime,
        known_at: datetime,
    ) -> ContinuitySelection:
        self._require_access(principal_id, actor_id, "case.continuity.read", case_id, False)
        with self._store.read_transaction() as tx:
            self._require_access(principal_id, actor_id, "case.continuity.read", case_id, False)
            return self._select_status_tx(tx, case_id, effective_at, known_at)

    def legacy_lifecycle(
        self, *, principal_id: str, actor_id: RecordId, case_id: RecordId
    ) -> LegacyLifecycleView:
        """Bounded read adapter: retain phase labels and explicitly refuse status mapping."""
        self._require_access(principal_id, actor_id, "case.legacy.read", case_id, False)
        with self._store.read_transaction() as tx:
            self._require_access(principal_id, actor_id, "case.legacy.read", case_id, False)
            rows = tx.projection_rows("case_continuity_status_records", case_id=str(case_id))
            if rows:
                return LegacyLifecycleView((), ())
            # The common Case identity Version is source provenance; legacy phase
            # labels remain exact status-event content and are never translated.
            history = tx.get_history(case_id)
            return LegacyLifecycleView(
                tuple(sorted((value.version_id for value in history.versions), key=str)),
                tuple(sorted({value.new_status for value in history.status_events})),
            )

    def _select_status_tx(
        self,
        tx: ContinuityTransaction,
        case_id: RecordId,
        effective_at: datetime,
        known_at: datetime,
    ) -> ContinuitySelection:
        records = tx.projection_rows("case_continuity_status_records", case_id=str(case_id))
        if not records:
            return ContinuitySelection(ContinuitySelectionKind.ABSENT, ())
        if len(records) != 1:
            return ContinuitySelection(ContinuitySelectionKind.CONFLICT, ())
        record_id = RecordId.parse(str(records[0]["record_id"]))
        selected = tx.select_current(
            SelectionQuery(
                "case-continuity-status", f"case:{case_id}", effective_at, known_at, record_id
            )
        )
        if isinstance(selected, SelectionAbsent):
            return ContinuitySelection(ContinuitySelectionKind.ABSENT, ())
        if isinstance(selected, SelectionConflict):
            return ContinuitySelection(
                ContinuitySelectionKind.CONFLICT,
                tuple(sorted((c.version_id for c in selected.candidates), key=str)),
            )
        assert isinstance(selected, SelectionFound)
        rows = tx.projection_rows(
            "case_continuity_status_versions", version_id=str(selected.candidate.version_id)
        )
        if len(rows) != 1:
            return ContinuitySelection(
                ContinuitySelectionKind.CONFLICT, (selected.candidate.version_id,)
            )
        return ContinuitySelection(
            ContinuitySelectionKind.ONE,
            (selected.candidate.version_id,),
            ContinuityStatus(str(rows[0]["status"])),
        )

    def _opening_responsibility(
        self, tx: ContinuityTransaction, command: OpenCaseCommand, recorded_at: datetime
    ) -> str:
        f = command.facts
        signature = responsibility_signature(
            contract=command.contract,
            obligation_kind=ObligationKind.DETERMINE_CASE_CONTINUITY,
            owning_case_id=f.case_id,
            context=command.context,
            purpose="continuing-case",
            use=command.bounded_use,
            scope=command.management_question,
        )
        basis_limits = {"continuity_actions": [value.value for value in DeterminationKind]}
        basis_row: dict[str, object] = {
            "version_id": str(f.assignment_basis_version_id),
            "record_id": str(f.assignment_basis_record_id),
            "assigning_actor_id": str(command.identity.actor_id),
            "basis_source_version_id": str(command.assignment_authority_source_version_id),
            "owning_case_id": str(f.case_id),
            "context_digest": command.context.digest,
            "allowed_obligation_kinds_json": json.dumps(
                [ObligationKind.DETERMINE_CASE_CONTINUITY.value]
            ),
            "allowed_case_ids_json": json.dumps([str(f.case_id)]),
            "allowed_signature_digests_json": json.dumps([signature]),
            "limits_json": json.dumps(basis_limits),
            "max_active_assignments": 1,
            "state": "ACTIVE",
            "effective_from_us": to_epoch_microseconds(command.effective_at),
            "effective_to_us": None,
            "recorded_at_us": to_epoch_microseconds(recorded_at),
            "predecessor_version_id": None,
        }
        basis_validation = SliceACommand(
            command.identity.command_id,
            command.identity.idempotency_scope,
            command.identity.idempotency_key,
            command.identity.principal_id,
            str(command.identity.actor_id),
            f.assignment_basis_record_id,
            f.assignment_basis_version_id,
            "assignment-basis",
            f"case:{f.case_id}",
            {
                "authority_source_version_id": str(command.assignment_authority_source_version_id),
                "responsibility_signature": signature,
                "responsibility_version_id": str(f.responsibility_version_id),
            },
            command.effective_at,
            command.contract,
            command.context,
            f.case_id,
            "responsibility.assignment-basis.create",
            (ProjectionFact("assignment_basis_versions", basis_row),),
        )
        ResponsibilityWorkService.validate_assignment_basis(
            tx, basis_validation, basis_row, recorded_at
        )
        self._add_version(
            tx,
            f.responsibility_record_id,
            f.responsibility_version_id,
            "responsibility",
            f"case:{f.case_id}",
            {
                "purpose_discriminator": "continuing-case",
                "use_discriminator": command.bounded_use,
                "scope_discriminator": command.management_question,
            },
            command.effective_at,
            recorded_at,
            command.identity.actor_id,
            command.contract,
            command.context,
        )
        tx.insert_projection(
            "responsibility_records", {"record_id": str(f.responsibility_record_id)}
        )
        tx.insert_projection(
            "responsibility_versions",
            {
                "version_id": str(f.responsibility_version_id),
                "record_id": str(f.responsibility_record_id),
                "obligation_kind": ObligationKind.DETERMINE_CASE_CONTINUITY.value,
                "owning_case_id": str(f.case_id),
                "context_digest": command.context.digest,
                "signature_digest": signature,
            },
        )
        self._add_version(
            tx,
            f.assignment_basis_record_id,
            f.assignment_basis_version_id,
            "assignment-basis",
            f"case:{f.case_id}",
            {"authority_source_version_id": str(command.assignment_authority_source_version_id)},
            command.effective_at,
            recorded_at,
            command.identity.actor_id,
            command.contract,
            command.context,
        )
        tx.insert_projection(
            "assignment_basis_records", {"record_id": str(f.assignment_basis_record_id)}
        )
        tx.insert_projection("assignment_basis_versions", basis_row)
        assignment_row: dict[str, object] = {
            "version_id": str(f.assignment_version_id),
            "record_id": str(f.assignment_record_id),
            "responsibility_version_id": str(f.responsibility_version_id),
            "signature_digest": signature,
            "actor_id": str(command.identity.actor_id),
            "assignment_basis_version_id": str(f.assignment_basis_version_id),
            "state": "ASSIGNED",
            "effective_from_us": to_epoch_microseconds(command.effective_at),
            "effective_to_us": None,
            "recorded_at_us": to_epoch_microseconds(recorded_at),
            "predecessor_version_id": None,
        }
        assignment_validation = SliceACommand(
            command.identity.command_id,
            command.identity.idempotency_scope,
            command.identity.idempotency_key,
            command.identity.principal_id,
            str(command.identity.actor_id),
            f.assignment_record_id,
            f.assignment_version_id,
            "responsibility-assignment",
            f"case:{f.case_id}",
            {
                "responsibility_version_id": str(f.responsibility_version_id),
                "actor_id": str(command.identity.actor_id),
                "responsibility_signature": signature,
                "assignment_basis_version_id": str(f.assignment_basis_version_id),
            },
            command.effective_at,
            command.contract,
            command.context,
            f.case_id,
            "responsibility.assignment.create",
            (ProjectionFact("responsibility_assignment_versions", assignment_row),),
        )
        ResponsibilityWorkService.validate_responsibility_assignment(
            tx, assignment_validation, assignment_row, recorded_at
        )
        self._add_version(
            tx,
            f.assignment_record_id,
            f.assignment_version_id,
            "responsibility-assignment",
            f"case:{f.case_id}",
            {
                "responsibility_version_id": str(f.responsibility_version_id),
                "actor_id": str(command.identity.actor_id),
            },
            command.effective_at,
            recorded_at,
            command.identity.actor_id,
            command.contract,
            command.context,
        )
        tx.insert_projection(
            "responsibility_assignment_records", {"record_id": str(f.assignment_record_id)}
        )
        tx.insert_projection("responsibility_assignment_versions", assignment_row)
        return signature

    def _validate_accountability(
        self, tx: ContinuityTransaction, command: TransitionCaseCommand, recorded_at: datetime
    ) -> None:
        resp = tx.projection_rows(
            "responsibility_versions", version_id=str(command.responsibility_version_id)
        )
        assignment = tx.projection_rows(
            "responsibility_assignment_versions", version_id=str(command.assignment_version_id)
        )
        if len(resp) != 1 or len(assignment) != 1:
            raise CaseContinuityConflict(
                "exact continuity Responsibility/assignment not established"
            )
        r, a = resp[0], assignment[0]
        if (
            r["obligation_kind"] != ObligationKind.DETERMINE_CASE_CONTINUITY.value
            or r["owning_case_id"] != str(command.case_id)
            or r["context_digest"] != command.context.digest
            or a["responsibility_version_id"] != str(command.responsibility_version_id)
            or a["actor_id"] != str(command.identity.actor_id)
            or a["state"] != "ASSIGNED"
        ):
            raise CaseContinuityConflict("continuity accountability does not match exact context")
        basis = tx.projection_rows(
            "assignment_basis_versions", version_id=str(a["assignment_basis_version_id"])
        )
        if len(basis) != 1 or basis[0]["basis_source_version_id"] != str(
            command.authority_basis_version_id
        ):
            raise CaseContinuityConflict(
                "substantive authority basis is not the exact assignment source"
            )
        # No implicit winner: exactly one eligible current assignment for signature.
        effective_us, known_us = (
            to_epoch_microseconds(command.effective_at),
            to_epoch_microseconds(recorded_at),
        )
        eligible: list[dict[str, object]] = []
        for row in tx.projection_rows(
            "responsibility_assignment_versions", signature_digest=str(r["signature_digest"])
        ):
            if (
                row["state"] != "ASSIGNED"
                or cast(int, row["effective_from_us"]) > effective_us
                or (
                    row["effective_to_us"] is not None
                    and effective_us >= cast(int, row["effective_to_us"])
                )
                or cast(int, row["recorded_at_us"]) > known_us
            ):
                continue
            version = tx.get_version(RecordVersionId.parse(str(row["version_id"])))
            if version is None:
                continue
            selected = tx.select_current(
                SelectionQuery(
                    version.family,
                    version.scope,
                    command.effective_at,
                    recorded_at,
                    version.record_id,
                )
            )
            if (
                isinstance(selected, SelectionFound)
                and selected.candidate.version_id == version.version_id
            ):
                eligible.append(row)
        if len(eligible) != 1 or eligible[0]["version_id"] != str(command.assignment_version_id):
            raise CaseContinuityConflict("continuity Responsibility vacancy or conflict")
        self._require_authority_source(
            tx,
            command.authority_basis_version_id,
            command.identity.actor_id,
            command.case_id,
            command.kind.value,
            command.context,
            command.effective_at,
            recorded_at,
        )

    def _validate_closure(
        self, tx: ContinuityTransaction, command: TransitionCaseCommand, recorded_at: datetime
    ) -> None:
        manifest = command.closure_manifest
        if manifest is None:
            raise CaseContinuityConflict("exact closure guard manifest is required")
        if manifest.operation_continues:
            raise CaseContinuityConflict("current operation continues; Case remains OPEN")
        work_rows = tx.projection_rows("case_work_versions", owning_case_id=str(command.case_id))
        current: dict[str, tuple[datetime, dict[str, object]]] = {}
        for row in work_rows:
            version = tx.get_version(RecordVersionId.parse(str(row["version_id"])))
            if (
                version is None
                or version.recorded_at > recorded_at
                or not version.effective.contains(command.effective_at)
            ):
                continue
            prior = current.get(str(row["record_id"]))
            if prior is None or version.recorded_at > prior[0]:
                current[str(row["record_id"])] = (version.recorded_at, row)
        if any(row["state"] in {"READY", "WAITING"} for _, row in current.values()):
            raise CaseContinuityConflict(
                "required durable Work remains unresolved; Case remains OPEN"
            )
        for responsibility in tx.projection_rows(
            "responsibility_versions", owning_case_id=str(command.case_id)
        ):
            exact = tx.get_version(RecordVersionId.parse(str(responsibility["version_id"])))
            if exact is None:
                continue
            selected = tx.select_current(
                SelectionQuery(
                    exact.family,
                    exact.scope,
                    command.effective_at,
                    recorded_at,
                    exact.record_id,
                )
            )
            if not (
                isinstance(selected, SelectionFound)
                and selected.candidate.version_id == exact.version_id
            ):
                continue
            assignment_rows = tx.projection_rows(
                "responsibility_assignment_versions",
                signature_digest=str(responsibility["signature_digest"]),
            )
            eligible_by_record: dict[str, tuple[datetime, dict[str, object]]] = {}
            for assignment in assignment_rows:
                assignment_version = tx.get_version(
                    RecordVersionId.parse(str(assignment["version_id"]))
                )
                if (
                    assignment_version is None
                    or assignment_version.recorded_at > recorded_at
                    or not assignment_version.effective.contains(command.effective_at)
                ):
                    continue
                prior = eligible_by_record.get(str(assignment["record_id"]))
                if prior is None or assignment_version.recorded_at > prior[0]:
                    eligible_by_record[str(assignment["record_id"])] = (
                        assignment_version.recorded_at,
                        assignment,
                    )
            eligible = [
                assignment
                for _, assignment in eligible_by_record.values()
                if assignment["state"] == "ASSIGNED"
            ]
            if len(eligible) != 1:
                raise CaseContinuityConflict(
                    "required Responsibility vacancy or conflict remains; Case remains OPEN"
                )
        if not manifest.required_version_ids:
            raise CaseContinuityConflict("closure guard basis is not established")
        if any(tx.get_version(value) is None for value in manifest.required_version_ids):
            raise CaseContinuityConflict("closure guard cites an unavailable exact Version")

    def _add_determination(
        self,
        tx: ContinuityTransaction,
        command: TransitionCaseCommand,
        recorded_at: datetime,
        *,
        prior_configuration_version_id: RecordVersionId | None = None,
        candidate_configuration_version_id: RecordVersionId | None = None,
    ) -> None:
        self._add_version(
            tx,
            command.facts.determination_record_id,
            command.facts.determination_version_id,
            "case-continuity-determination",
            f"case:{command.case_id}",
            {
                "kind": command.kind.value,
                "outcome": command.outcome.value,
                "rationale": command.rationale,
                "factors": list(command.factors),
            },
            command.effective_at,
            recorded_at,
            command.identity.actor_id,
            command.contract,
            command.context,
        )
        tx.insert_projection(
            "case_continuity_determination_records",
            {"record_id": str(command.facts.determination_record_id)},
        )
        tx.insert_projection(
            "case_continuity_determination_versions",
            {
                "version_id": str(command.facts.determination_version_id),
                "record_id": str(command.facts.determination_record_id),
                "kind": command.kind.value,
                "outcome": command.outcome.value,
                "source_case_id": str(command.case_id),
                "source_status_version_id": str(command.expected_status_version_id),
                "prior_configuration_version_id": str(prior_configuration_version_id)
                if prior_configuration_version_id
                else None,
                "candidate_configuration_version_id": str(candidate_configuration_version_id)
                if candidate_configuration_version_id
                else None,
                "successor_case_id": str(command.successor_case_id)
                if command.successor_case_id
                else None,
                "changed_basis_context_digest": command.context.digest,
                "guard_manifest_json": json.dumps(self._manifest(command), sort_keys=True),
                "rationale": command.rationale,
                "factors_json": json.dumps(command.factors),
                "responsibility_version_id": str(command.responsibility_version_id),
                "assignment_version_id": str(command.assignment_version_id),
                "authority_basis_version_id": str(command.authority_basis_version_id),
                "effective_at_us": to_epoch_microseconds(command.effective_at),
                "knowledge_cutoff_us": to_epoch_microseconds(command.knowledge_cutoff),
                "recorded_at_us": to_epoch_microseconds(recorded_at),
            },
        )

    @staticmethod
    def _manifest(command: TransitionCaseCommand) -> dict[str, JsonValue]:
        value = command.closure_manifest
        return (
            {}
            if value is None
            else {
                "operation_continues": value.operation_continues,
                "required_version_ids": [str(v) for v in value.required_version_ids],
                "unresolved_item_treatment": value.unresolved_item_treatment,
                "retention_basis": value.retention_basis,
            }
        )

    def _select_case_initiation_authority(
        self,
        *,
        actor_id: RecordId,
        organization_scope: str,
        bounded_use: str,
        effective_at: datetime,
    ) -> RecordVersionId:
        known_at = self._clock.now()
        matches: list[RecordVersionId] = []
        with self._store.read_transaction() as tx:
            rows = tx.projection_rows(
                "case_initiation_authority_versions",
                authorized_actor_id=str(actor_id),
                organization_scope=organization_scope,
            )
            for row in rows:
                if row["state"] != CaseInitiationAuthorityState.ACTIVE.value:
                    continue
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
                prefixes = cast(
                    "list[str]", json.loads(cast(str, row["allowed_use_prefixes_json"]))
                )
                if (
                    isinstance(selected, SelectionFound)
                    and selected.candidate.version_id == version_id
                    and (not prefixes or any(bounded_use.startswith(value) for value in prefixes))
                ):
                    matches.append(version_id)
        if len(matches) != 1:
            raise CaseContinuityConflict(
                "exact current pre-Case initiation authority not established"
            )
        return matches[0]

    @staticmethod
    def _require_case_initiation_authority(
        tx: ContinuityTransaction,
        *,
        version_id: RecordVersionId,
        actor_id: RecordId,
        organization_scope: str,
        bounded_use: str,
        effective_at: datetime,
        known_at: datetime,
    ) -> None:
        source = tx.get_version(version_id)
        rows = tx.projection_rows("case_initiation_authority_versions", version_id=str(version_id))
        if source is None or source.family != "case-initiation-authority" or len(rows) != 1:
            raise CaseContinuityConflict("pre-Case initiation authority is not established")
        row = rows[0]
        selected = tx.select_current(
            SelectionQuery(source.family, source.scope, effective_at, known_at, source.record_id)
        )
        prefixes = cast("list[str]", json.loads(cast(str, row["allowed_use_prefixes_json"])))
        if (
            not isinstance(selected, SelectionFound)
            or selected.candidate.version_id != version_id
            or row["state"] != CaseInitiationAuthorityState.ACTIVE.value
            or row["authorized_actor_id"] != str(actor_id)
            or row["organization_scope"] != organization_scope
            or (prefixes and not any(bounded_use.startswith(value) for value in prefixes))
        ):
            raise CaseContinuityConflict(
                "pre-Case initiation authority is stale, withdrawn, or out of scope"
            )

    def _require_authority_source(
        self,
        tx: ContinuityTransaction,
        version_id: RecordVersionId,
        actor_id: RecordId,
        case_id: RecordId,
        action: str,
        context: ExactContextSet,
        effective_at: datetime,
        known_at: datetime,
    ) -> None:
        version = tx.get_version(version_id)
        if version is not None and version.family == "case-initiation-authority":
            raise CaseContinuityConflict(
                "pre-Case initiation authority grants no post-Case substantive authority"
            )
        if version is None or version.family not in {
            "authority-record",
            "decision-authorization-basis",
        }:
            raise CaseContinuityConflict("substantive continuity authority is not established")
        self._require_exact_current(
            tx, version, effective_at, known_at, "substantive continuity authority is stale"
        )
        authority = version.content.get("case_continuity_authority")
        if (
            not isinstance(authority, dict)
            or authority.get("actor_id") != str(actor_id)
            or str(case_id) not in cast(list[str], authority.get("allowed_case_ids", []))
            or action not in cast(list[str], authority.get("allowed_actions", []))
            or authority.get("context_digest") != context.digest
        ):
            raise CaseContinuityConflict(
                "substantive continuity authority does not cover exact act/context"
            )

    @staticmethod
    def _require_exact_current(
        tx: ContinuityTransaction,
        version: FinalizedRecordVersion,
        effective_at: datetime,
        known_at: datetime,
        reason: str,
    ) -> None:
        selected = tx.select_current(
            SelectionQuery(version.family, version.scope, effective_at, known_at, version.record_id)
        )
        if (
            not isinstance(selected, SelectionFound)
            or selected.candidate.version_id != version.version_id
        ):
            raise CaseContinuityConflict(reason)

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
                    "interpretation_source": (
                        "docs/system/specifications/PAIM_CASE_LIFECYCLE_SPEC_v0.1.md"
                    ),
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
        contract: SemanticContractRef,
        context: ExactContextSet,
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
        if not tx.projection_rows(
            "semantic_contract_families", contract_key=contract.key, record_family=family
        ):
            tx.insert_projection(
                "semantic_contract_families",
                {"contract_key": contract.key, "record_family": family},
            )
        tx.insert_projection(
            "record_version_semantics",
            {
                "version_id": str(version_id),
                "contract_key": contract.key,
                "context_digest": context.digest,
                "consumer_id": "gate8-slice-b",
                "adapter_key": None,
            },
        )

    def _require_access(
        self, principal_id: str, actor_id: RecordId, action: str, case_id: RecordId, write: bool
    ) -> None:
        if not self._access.authorize(
            principal_id=principal_id,
            actor_id=str(actor_id),
            action=action,
            case_id=case_id,
            write=write,
        ):
            raise CaseContinuityAccessDenied()

    @staticmethod
    def _replay(
        tx: ContinuityTransaction, scope: str, key: str, digest: str
    ) -> CommandOutcome | None:
        fact = tx.get_idempotency(scope, key)
        if fact is None:
            return None
        if fact.digest != digest:
            raise CaseContinuityConflict("IDEMPOTENCY KEY REUSE CONFLICT")
        return fact.outcome

    @staticmethod
    def _finish(
        tx: ContinuityTransaction,
        identity: CommandIdentity,
        digest: str,
        record_id: RecordId,
        versions: tuple[RecordVersionId, ...],
        events: tuple[EventId, ...],
        relationships: tuple[RelationshipId, ...],
        effective_at: datetime,
        recorded_at: datetime,
        context: ExactContextSet,
        reasons: tuple[str, ...],
    ) -> CommandOutcome:
        command_id = identity.command_id
        audit = AuditFact(
            AuditId.new(),
            identity.principal_id,
            str(identity.actor_id),
            ActorResolution.PROVIDED,
            "SLICE_B_CASE_CONTINUITY_COMMIT",
            "COMMITTED",
            command_id,
            identity.idempotency_scope,
            identity.idempotency_key,
            None,
            None,
            record_id,
            versions,
            "EXACT_CONTEXT",
            context.digest,
            effective_at,
            recorded_at,
            reasons,
            digest,
        )
        tx.add_audit(audit)
        outcome = CommandOutcome(
            str(command_id),
            str(record_id),
            tuple(map(str, versions)),
            tuple(map(str, events)),
            tuple(map(str, relationships)),
            str(audit.audit_id),
        )
        tx.add_idempotency(
            IdempotencyFact(
                identity.idempotency_scope,
                identity.idempotency_key,
                digest,
                str(command_id),
                outcome,
                recorded_at,
            )
        )
        return outcome

    @staticmethod
    def _open_payload(command: OpenCaseCommand) -> dict[str, JsonValue]:
        return {
            "action": "CREATE_OPEN_CASE",
            "case_id": str(command.facts.case_id),
            "facts": [str(v) for v in command.facts.__dict__.values()]
            if hasattr(command.facts, "__dict__")
            else repr(command.facts),
            "contract": command.contract.key,
            "context": command.context.digest,
            "title": command.title,
            "bounded_use": command.bounded_use,
            "management_question": command.management_question,
            "configuration": command.configuration_content,
            "continuity_authority": str(command.authority_source_version_id),
            "assignment_authority": str(command.assignment_authority_source_version_id),
            "effective_at": command.effective_at.isoformat(),
            "knowledge_cutoff": command.knowledge_cutoff.isoformat(),
            "actor": str(command.identity.actor_id),
            "principal": command.identity.principal_id,
        }

    @staticmethod
    def _transition_payload(command: TransitionCaseCommand) -> dict[str, JsonValue]:
        return {
            "action": command.kind.value,
            "outcome": command.outcome.value,
            "case_id": str(command.case_id),
            "expected_status_version_id": str(command.expected_status_version_id),
            "facts": repr(command.facts),
            "contract": command.contract.key,
            "context": command.context.digest,
            "responsibility": str(command.responsibility_version_id),
            "assignment": str(command.assignment_version_id),
            "authority": str(command.authority_basis_version_id),
            "rationale": command.rationale,
            "factors": list(command.factors),
            "manifest": CaseContinuityService._manifest(command),
            "successor_case_id": str(command.successor_case_id)
            if command.successor_case_id
            else None,
            "effective_at": command.effective_at.isoformat(),
            "knowledge_cutoff": command.knowledge_cutoff.isoformat(),
            "actor": str(command.identity.actor_id),
            "principal": command.identity.principal_id,
        }

    @staticmethod
    def _configuration_payload(command: ConfigurationSuccessorCommand) -> dict[str, JsonValue]:
        return {
            "action": "SAME_CASE_CONFIGURATION_SUCCESSOR",
            "case_id": str(command.case_id),
            "facts": repr(command.facts),
            "expected_status": str(command.expected_status_version_id),
            "predecessor_configuration": str(command.predecessor_configuration_version_id),
            "expected_designation": str(command.expected_designation_version_id),
            "configuration": command.configuration_content,
            "contract": command.contract.key,
            "context": command.context.digest,
            "responsibility": str(command.responsibility_version_id),
            "assignment": str(command.assignment_version_id),
            "authority": str(command.authority_basis_version_id),
            "rationale": command.rationale,
            "factors": list(command.factors),
            "effective_at": command.effective_at.isoformat(),
            "knowledge_cutoff": command.knowledge_cutoff.isoformat(),
            "actor": str(command.identity.actor_id),
            "principal": command.identity.principal_id,
        }
