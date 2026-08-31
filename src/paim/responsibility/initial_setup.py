"""Explicit initial Value/Risk Responsibility setup for a newly opened Case."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from paim.audit.models import ActorResolution, AuditFact
from paim.integrity.commands import canonical_command_digest
from paim.integrity.ids import AuditId, CommandId, RecordId, RecordVersionId
from paim.integrity.records import FinalizedRecordVersion, JsonValue, canonical_json
from paim.integrity.selection import SelectionFound, SelectionQuery
from paim.integrity.semantics import (
    ContextMemberKind,
    ExactContextMember,
    ExactContextSet,
    SemanticContractRef,
)
from paim.integrity.time import Clock, EffectiveInterval, to_epoch_microseconds
from paim.persistence.ports import CommandOutcome, IdempotencyFact
from paim.responsibility.models import ObligationKind, PracticalRole, responsibility_signature
from paim.responsibility.service import (
    ProjectionFact,
    ResponsibilityWorkService,
    SliceAAccessDenied,
    SliceAAccessPolicy,
    SliceACommand,
    SliceAConflict,
    SliceAStore,
    SliceATransaction,
)

_CONTRACT = SemanticContractRef("paim-gate8-slice-a", "1")
_ACTION = "case.initial-assessment.setup"
_OBLIGATIONS = (
    ObligationKind.FINISH_VALUE_ASSESSMENT,
    ObligationKind.FINISH_RISK_ASSESSMENT,
)


@dataclass(frozen=True, slots=True)
class InitialAssessmentSetupContext:
    case_id: RecordId
    configuration_id: RecordId
    configuration_version_id: RecordVersionId
    bounded_use: str
    management_question: str
    context: ExactContextSet
    source_version_ids: tuple[RecordVersionId, ...]


@dataclass(frozen=True, slots=True)
class _LaneFacts:
    responsibility_record_id: RecordId
    responsibility_version_id: RecordVersionId
    assignment_record_id: RecordId
    assignment_version_id: RecordVersionId

    @classmethod
    def new(cls) -> _LaneFacts:
        return cls(RecordId.new(), RecordVersionId.new(), RecordId.new(), RecordVersionId.new())


@dataclass(frozen=True, slots=True)
class InitialAssessmentSetupFacts:
    authority_record_id: RecordId
    authority_version_id: RecordVersionId
    basis_record_id: RecordId
    basis_version_id: RecordVersionId
    value: _LaneFacts
    risk: _LaneFacts

    @classmethod
    def new(cls) -> InitialAssessmentSetupFacts:
        return cls(
            RecordId.new(),
            RecordVersionId.new(),
            RecordId.new(),
            RecordVersionId.new(),
            _LaneFacts.new(),
            _LaneFacts.new(),
        )


@dataclass(frozen=True, slots=True)
class InitialAssessmentSetupCommand:
    command_id: CommandId
    idempotency_scope: str
    idempotency_key: str
    principal_id: str
    actor_id: RecordId
    case_id: RecordId
    authority_source: str
    authority_provenance: str
    authority_scope: str
    authority_requirement: str
    effective_at: datetime
    expected_source_version_ids: tuple[RecordVersionId, ...]
    facts: InitialAssessmentSetupFacts

    def digest(self) -> str:
        return canonical_command_digest(
            {
                "principal_id": self.principal_id,
                "actor_id": str(self.actor_id),
                "case_id": str(self.case_id),
                "authority_source": self.authority_source,
                "authority_provenance": self.authority_provenance,
                "authority_scope": self.authority_scope,
                "authority_requirement": self.authority_requirement,
                "effective_at": self.effective_at.isoformat(),
                "expected_source_version_ids": [
                    str(value) for value in self.expected_source_version_ids
                ],
                "authority_record_id": str(self.facts.authority_record_id),
                "authority_version_id": str(self.facts.authority_version_id),
                "basis_record_id": str(self.facts.basis_record_id),
                "basis_version_id": str(self.facts.basis_version_id),
                "value_responsibility_version_id": str(self.facts.value.responsibility_version_id),
                "value_assignment_version_id": str(self.facts.value.assignment_version_id),
                "risk_responsibility_version_id": str(self.facts.risk.responsibility_version_id),
                "risk_assignment_version_id": str(self.facts.risk.assignment_version_id),
            }
        )


SetupCommitHook = Callable[
    [SliceATransaction, CommandOutcome, InitialAssessmentSetupContext, datetime], None
]


class InitialAssessmentSetupService:
    """Establish explicit assessment assignment authority and two independent Responsibilities."""

    def __init__(self, store: SliceAStore, clock: Clock, access: SliceAAccessPolicy) -> None:
        self._store = store
        self._clock = clock
        self._access = access

    def resolve(
        self,
        *,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        effective_at: datetime,
        known_at: datetime,
    ) -> InitialAssessmentSetupContext:
        with self._store.read_transaction() as transaction:
            return self._resolve(
                transaction,
                principal_id=principal_id,
                actor_id=actor_id,
                case_id=case_id,
                effective_at=effective_at,
                known_at=known_at,
            )

    def commit(
        self,
        command: InitialAssessmentSetupCommand,
        *,
        commit_hook: SetupCommitHook | None = None,
    ) -> CommandOutcome:
        for value in (
            command.authority_source,
            command.authority_provenance,
            command.authority_scope,
            command.authority_requirement,
        ):
            if not value.strip():
                raise ValueError(
                    "assignment authority source, reference, scope, and requirement are required"
                )
        digest = command.digest()
        recorded_at = self._clock.now()
        self._require_access(command)
        with self._store.semantic_transaction() as transaction:
            replay = transaction.get_idempotency(command.idempotency_scope, command.idempotency_key)
            if replay is not None:
                if replay.digest != digest:
                    raise SliceAConflict("IDEMPOTENCY KEY REUSE CONFLICT")
                return replay.outcome
            self._require_access(command)
            context = self._resolve(
                transaction,
                principal_id=command.principal_id,
                actor_id=command.actor_id,
                case_id=command.case_id,
                effective_at=command.effective_at,
                known_at=recorded_at,
            )
            if context.source_version_ids != command.expected_source_version_ids:
                raise SliceAConflict("initial assessment setup context changed")
            outcome = self._write_setup(transaction, command, context, recorded_at, digest)
            if commit_hook is not None:
                commit_hook(transaction, outcome, context, recorded_at)
            return outcome

    def _require_access(self, command: InitialAssessmentSetupCommand) -> None:
        if not self._access.authorize(
            principal_id=command.principal_id,
            actor_id=str(command.actor_id),
            action=_ACTION,
            case_id=command.case_id,
            write=True,
        ):
            raise SliceAAccessDenied()

    def _resolve(
        self,
        transaction: SliceATransaction,
        *,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        effective_at: datetime,
        known_at: datetime,
    ) -> InitialAssessmentSetupContext:
        if not self._access.authorize(
            principal_id=principal_id,
            actor_id=str(actor_id),
            action=_ACTION,
            case_id=case_id,
            write=True,
        ):
            raise SliceAAccessDenied()
        case_versions = self._current_family(
            transaction, "prospective-case", f"case:{case_id}", effective_at, known_at
        )
        if len(case_versions) != 1 or case_versions[0].creator != str(actor_id):
            raise SliceAConflict(
                "only the exact initiating Actor may set up initial assessment work"
            )
        status_rows = self._current_rows(
            transaction,
            transaction.projection_rows("case_continuity_status_versions", case_id=str(case_id)),
            effective_at,
            known_at,
        )
        if len(status_rows) != 1 or status_rows[0]["status"] != "OPEN":
            raise SliceAConflict("prospective Case is not OPEN")
        governing_rows = self._current_rows(
            transaction,
            transaction.projection_rows(
                "governing_configuration_designations", case_id=str(case_id)
            ),
            effective_at,
            known_at,
        )
        if len(governing_rows) != 1:
            raise SliceAConflict("one exact governing Configuration is not established")
        configuration_version_id = RecordVersionId.parse(
            str(governing_rows[0]["configuration_version_id"])
        )
        configuration = transaction.get_version(configuration_version_id)
        if configuration is None:
            raise SliceAConflict("governing Configuration Version is unavailable")
        continuity_responsibilities = self._current_rows(
            transaction,
            transaction.projection_rows(
                "responsibility_versions",
                owning_case_id=str(case_id),
                obligation_kind=ObligationKind.DETERMINE_CASE_CONTINUITY.value,
            ),
            effective_at,
            known_at,
        )
        if len(continuity_responsibilities) != 1:
            raise SliceAConflict("one exact Case-continuity Responsibility is not established")
        continuity = continuity_responsibilities[0]
        context = self._context(transaction, str(continuity["context_digest"]))
        assignments = self._current_rows(
            transaction,
            transaction.projection_rows(
                "responsibility_assignment_versions",
                signature_digest=str(continuity["signature_digest"]),
            ),
            effective_at,
            known_at,
        )
        assignments = tuple(
            row
            for row in assignments
            if row["state"] == "ASSIGNED" and row["actor_id"] == str(actor_id)
        )
        if len(assignments) != 1:
            raise SliceAConflict("initial Case-continuity accountability is not exact")
        basis_id = RecordVersionId.parse(str(assignments[0]["assignment_basis_version_id"]))
        basis = self._exact_current_row(
            transaction, "assignment_basis_versions", basis_id, effective_at, known_at
        )
        authority_id = RecordVersionId.parse(str(basis["basis_source_version_id"]))
        existing = tuple(
            row
            for row in self._current_rows(
                transaction,
                transaction.projection_rows("responsibility_versions", owning_case_id=str(case_id)),
                effective_at,
                known_at,
            )
            if row["obligation_kind"] in {value.value for value in _OBLIGATIONS}
        )
        if existing:
            raise SliceAConflict("initial assessment Responsibilities are already established")
        source_ids = {
            case_versions[0].version_id,
            RecordVersionId.parse(str(status_rows[0]["version_id"])),
            RecordVersionId.parse(str(governing_rows[0]["version_id"])),
            configuration_version_id,
            RecordVersionId.parse(str(continuity["version_id"])),
            RecordVersionId.parse(str(assignments[0]["version_id"])),
            basis_id,
            authority_id,
        }
        for version_id in source_ids:
            source = transaction.get_version(version_id)
            if source is None or not self._access.authorize(
                principal_id=principal_id,
                actor_id=str(actor_id),
                action="source.read",
                case_id=case_id,
                write=False,
                source_version_id=version_id,
                source_family=source.family,
                effective_at=effective_at,
                known_at=known_at,
            ):
                raise SliceAAccessDenied()
        continuity_source = transaction.get_version(
            RecordVersionId.parse(str(continuity["version_id"]))
        )
        if continuity_source is None:
            raise SliceAConflict("initial Case-continuity source is unavailable")
        bounded_use = str(continuity_source.content.get("use_discriminator", "")).strip()
        management_question = str(continuity_source.content.get("scope_discriminator", "")).strip()
        if not bounded_use or not management_question:
            raise SliceAConflict("initial Case management context is unavailable")
        return InitialAssessmentSetupContext(
            case_id,
            configuration.record_id,
            configuration_version_id,
            bounded_use,
            management_question,
            context,
            tuple(sorted(source_ids, key=str)),
        )

    def _write_setup(
        self,
        transaction: SliceATransaction,
        command: InitialAssessmentSetupCommand,
        context: InitialAssessmentSetupContext,
        recorded_at: datetime,
        digest: str,
    ) -> CommandOutcome:
        bounded_use = context.bounded_use
        management_question = context.management_question
        self._ensure_semantics(transaction, recorded_at)
        facts_by_obligation = {
            ObligationKind.FINISH_VALUE_ASSESSMENT: command.facts.value,
            ObligationKind.FINISH_RISK_ASSESSMENT: command.facts.risk,
        }
        signatures = {
            obligation: responsibility_signature(
                contract=_CONTRACT,
                obligation_kind=obligation,
                owning_case_id=command.case_id,
                context=context.context,
                purpose="initial-assessment",
                use=bounded_use,
                scope=management_question,
            )
            for obligation in _OBLIGATIONS
        }
        limits: dict[str, JsonValue] = {
            "assessment_lanes": ["VALUE", "RISK"],
            "purpose": "initial-assessment",
        }
        authority_content: dict[str, JsonValue] = {
            "category": "assignment-authority",
            "source": command.authority_source,
            "scope": command.authority_scope,
            "requirement": command.authority_requirement,
            "provenance": {"reference": command.authority_provenance},
            "case_id": str(command.case_id),
            "configuration_id": str(context.configuration_id),
            "configuration_version_id": str(context.configuration_version_id),
            "assignment_authority": {
                "assigning_actor_id": str(command.actor_id),
                "allowed_case_ids": [str(command.case_id)],
                "allowed_obligation_kinds": [value.value for value in _OBLIGATIONS],
                "allowed_signature_digests": [signatures[value] for value in _OBLIGATIONS],
                "context_digest": context.context.digest,
                "max_active_assignments": 2,
                "limits": limits,
            },
        }
        self._add_version(
            transaction,
            command.facts.authority_record_id,
            command.facts.authority_version_id,
            "authority-record",
            f"authority:{command.facts.authority_record_id}",
            authority_content,
            command.effective_at,
            recorded_at,
            command.actor_id,
            None,
        )
        for obligation, lane_facts in facts_by_obligation.items():
            self._add_version(
                transaction,
                lane_facts.responsibility_record_id,
                lane_facts.responsibility_version_id,
                "responsibility",
                f"case:{command.case_id}",
                {
                    "purpose_discriminator": "initial-assessment",
                    "use_discriminator": bounded_use,
                    "scope_discriminator": management_question,
                },
                command.effective_at,
                recorded_at,
                command.actor_id,
                _CONTRACT,
                context.context.digest,
            )
            transaction.insert_projection(
                "responsibility_records", {"record_id": str(lane_facts.responsibility_record_id)}
            )
            transaction.insert_projection(
                "responsibility_versions",
                {
                    "version_id": str(lane_facts.responsibility_version_id),
                    "record_id": str(lane_facts.responsibility_record_id),
                    "obligation_kind": obligation.value,
                    "owning_case_id": str(command.case_id),
                    "context_digest": context.context.digest,
                    "signature_digest": signatures[obligation],
                },
            )
            transaction.insert_projection(
                "responsibility_practical_roles",
                {
                    "responsibility_version_id": str(lane_facts.responsibility_version_id),
                    "role_code": PracticalRole.ASSESSOR.value,
                },
            )
        basis_row: dict[str, object] = {
            "version_id": str(command.facts.basis_version_id),
            "record_id": str(command.facts.basis_record_id),
            "assigning_actor_id": str(command.actor_id),
            "basis_source_version_id": str(command.facts.authority_version_id),
            "owning_case_id": str(command.case_id),
            "context_digest": context.context.digest,
            "allowed_obligation_kinds_json": json.dumps([value.value for value in _OBLIGATIONS]),
            "allowed_case_ids_json": json.dumps([str(command.case_id)]),
            "allowed_signature_digests_json": json.dumps(
                [signatures[value] for value in _OBLIGATIONS]
            ),
            "limits_json": json.dumps(limits, sort_keys=True, separators=(",", ":")),
            "max_active_assignments": 2,
            "state": "ACTIVE",
            "effective_from_us": to_epoch_microseconds(command.effective_at),
            "effective_to_us": None,
            "recorded_at_us": to_epoch_microseconds(recorded_at),
            "predecessor_version_id": None,
        }
        basis_command = self._validation_command(
            command,
            context,
            command.facts.basis_record_id,
            command.facts.basis_version_id,
            "assignment-basis",
            "responsibility.assignment-basis.create",
            {
                "authority_source_version_id": str(command.facts.authority_version_id),
                "responsibility_signature": signatures[_OBLIGATIONS[0]],
                "responsibility_version_id": str(command.facts.value.responsibility_version_id),
            },
            ProjectionFact("assignment_basis_versions", basis_row),
        )
        ResponsibilityWorkService.validate_assignment_basis(
            transaction, basis_command, basis_row, recorded_at
        )
        self._add_version(
            transaction,
            command.facts.basis_record_id,
            command.facts.basis_version_id,
            "assignment-basis",
            f"case:{command.case_id}",
            {"authority_source_version_id": str(command.facts.authority_version_id)},
            command.effective_at,
            recorded_at,
            command.actor_id,
            _CONTRACT,
            context.context.digest,
        )
        transaction.insert_projection(
            "assignment_basis_records", {"record_id": str(command.facts.basis_record_id)}
        )
        transaction.insert_projection("assignment_basis_versions", basis_row)
        for obligation, lane_facts in facts_by_obligation.items():
            assignment_row: dict[str, object] = {
                "version_id": str(lane_facts.assignment_version_id),
                "record_id": str(lane_facts.assignment_record_id),
                "responsibility_version_id": str(lane_facts.responsibility_version_id),
                "signature_digest": signatures[obligation],
                "actor_id": str(command.actor_id),
                "assignment_basis_version_id": str(command.facts.basis_version_id),
                "state": "ASSIGNED",
                "effective_from_us": to_epoch_microseconds(command.effective_at),
                "effective_to_us": None,
                "recorded_at_us": to_epoch_microseconds(recorded_at),
                "predecessor_version_id": None,
            }
            assignment_command = self._validation_command(
                command,
                context,
                lane_facts.assignment_record_id,
                lane_facts.assignment_version_id,
                "responsibility-assignment",
                "responsibility.assignment.create",
                {
                    "responsibility_version_id": str(lane_facts.responsibility_version_id),
                    "actor_id": str(command.actor_id),
                    "responsibility_signature": signatures[obligation],
                    "assignment_basis_version_id": str(command.facts.basis_version_id),
                },
                ProjectionFact("responsibility_assignment_versions", assignment_row),
            )
            ResponsibilityWorkService.validate_responsibility_assignment(
                transaction, assignment_command, assignment_row, recorded_at
            )
            self._add_version(
                transaction,
                lane_facts.assignment_record_id,
                lane_facts.assignment_version_id,
                "responsibility-assignment",
                f"case:{command.case_id}",
                {
                    "responsibility_version_id": str(lane_facts.responsibility_version_id),
                    "actor_id": str(command.actor_id),
                },
                command.effective_at,
                recorded_at,
                command.actor_id,
                _CONTRACT,
                context.context.digest,
            )
            transaction.insert_projection(
                "responsibility_assignment_records",
                {"record_id": str(lane_facts.assignment_record_id)},
            )
            transaction.insert_projection("responsibility_assignment_versions", assignment_row)
        version_ids = (
            command.facts.authority_version_id,
            command.facts.value.responsibility_version_id,
            command.facts.risk.responsibility_version_id,
            command.facts.basis_version_id,
            command.facts.value.assignment_version_id,
            command.facts.risk.assignment_version_id,
        )
        audit = AuditFact(
            AuditId.new(),
            command.principal_id,
            str(command.actor_id),
            ActorResolution.PROVIDED,
            "INITIAL_ASSESSMENT_RESPONSIBILITY_SETUP",
            "COMMITTED",
            command.command_id,
            command.idempotency_scope,
            command.idempotency_key,
            None,
            None,
            command.case_id,
            version_ids,
            "EXACT_CONTEXT",
            context.context.digest,
            command.effective_at,
            recorded_at,
            (
                "ASSIGNMENT_AUTHORITY_EXPLICIT",
                "VALUE_RISK_RESPONSIBILITIES_INDEPENDENT",
            ),
            digest,
        )
        transaction.add_audit(audit)
        outcome = CommandOutcome(
            str(command.command_id),
            str(command.case_id),
            tuple(str(value) for value in version_ids),
            (),
            (),
            str(audit.audit_id),
        )
        transaction.add_idempotency(
            IdempotencyFact(
                command.idempotency_scope,
                command.idempotency_key,
                digest,
                str(command.command_id),
                outcome,
                recorded_at,
            )
        )
        return outcome

    @staticmethod
    def _ensure_semantics(transaction: SliceATransaction, recorded_at: datetime) -> None:
        if not transaction.projection_rows("semantic_contracts", contract_key=_CONTRACT.key):
            transaction.insert_projection(
                "semantic_contracts",
                {
                    "contract_key": _CONTRACT.key,
                    "contract_id": _CONTRACT.contract_id,
                    "contract_version": _CONTRACT.version,
                    "owner": "PAIM",
                    "interpretation_source": "docs/system/specifications",
                    "recorded_at_us": to_epoch_microseconds(recorded_at),
                },
            )
        for family in (
            "responsibility",
            "assignment-basis",
            "responsibility-assignment",
        ):
            if not transaction.projection_rows(
                "semantic_contract_families",
                contract_key=_CONTRACT.key,
                record_family=family,
            ):
                transaction.insert_projection(
                    "semantic_contract_families",
                    {"contract_key": _CONTRACT.key, "record_family": family},
                )

    @staticmethod
    def _validation_command(
        command: InitialAssessmentSetupCommand,
        context: InitialAssessmentSetupContext,
        record_id: RecordId,
        version_id: RecordVersionId,
        family: str,
        action: str,
        content: dict[str, JsonValue],
        projection: ProjectionFact,
    ) -> SliceACommand:
        return SliceACommand(
            command.command_id,
            command.idempotency_scope,
            command.idempotency_key,
            command.principal_id,
            str(command.actor_id),
            record_id,
            version_id,
            family,
            f"case:{command.case_id}",
            content,
            command.effective_at,
            _CONTRACT,
            context.context,
            command.case_id,
            action,
            (projection,),
        )

    @staticmethod
    def _add_version(
        transaction: SliceATransaction,
        record_id: RecordId,
        version_id: RecordVersionId,
        family: str,
        scope: str,
        content: dict[str, JsonValue],
        effective_at: datetime,
        recorded_at: datetime,
        actor_id: RecordId,
        contract: SemanticContractRef | None,
        context_digest: str | None = None,
    ) -> None:
        transaction.add_version(
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
        if contract is not None:
            transaction.insert_projection(
                "record_version_semantics",
                {
                    "version_id": str(version_id),
                    "contract_key": contract.key,
                    "context_digest": context_digest,
                    "consumer_id": "gate8-slice-a",
                    "adapter_key": None,
                },
            )

    @staticmethod
    def _literal(context: ExactContextSet, slot: str) -> str:
        return next(
            member.identity
            for member in context.members
            if member.slot == slot and member.kind is ContextMemberKind.LITERAL
        )

    @staticmethod
    def _context(transaction: SliceATransaction, digest: str) -> ExactContextSet:
        rows = transaction.projection_rows("exact_context_members", context_digest=digest)
        if not rows:
            raise SliceAConflict("exact Case context is unavailable")
        return ExactContextSet.create(
            tuple(
                ExactContextMember(
                    str(row["slot"]),
                    ContextMemberKind(str(row["member_kind"])),
                    str(row["identity"]),
                )
                for row in sorted(rows, key=lambda value: str(value["slot"]))
            )
        )

    @staticmethod
    def _current_family(
        transaction: SliceATransaction,
        family: str,
        scope: str,
        effective_at: datetime,
        known_at: datetime,
    ) -> tuple[FinalizedRecordVersion, ...]:
        selected = transaction.select_current(SelectionQuery(family, scope, effective_at, known_at))
        if isinstance(selected, SelectionFound):
            source = transaction.get_version(selected.candidate.version_id)
            return (source,) if source is not None else ()
        return ()

    @staticmethod
    def _current_rows(
        transaction: SliceATransaction,
        rows: tuple[dict[str, object], ...],
        effective_at: datetime,
        known_at: datetime,
    ) -> tuple[dict[str, object], ...]:
        result: list[dict[str, object]] = []
        for row in rows:
            version_id = RecordVersionId.parse(str(row["version_id"]))
            source = transaction.get_version(version_id)
            if source is None:
                continue
            selected = transaction.select_current(
                SelectionQuery(
                    source.family,
                    source.scope,
                    effective_at,
                    known_at,
                    source.record_id,
                )
            )
            if isinstance(selected, SelectionFound) and selected.candidate.version_id == version_id:
                result.append(row)
        return tuple(result)

    @classmethod
    def _exact_current_row(
        cls,
        transaction: SliceATransaction,
        table: str,
        version_id: RecordVersionId,
        effective_at: datetime,
        known_at: datetime,
    ) -> dict[str, object]:
        rows = cls._current_rows(
            transaction,
            transaction.projection_rows(table, version_id=str(version_id)),
            effective_at,
            known_at,
        )
        if len(rows) != 1:
            raise SliceAConflict(f"exact current {table} source is unavailable")
        return rows[0]
