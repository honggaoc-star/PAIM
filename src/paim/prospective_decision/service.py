"""Atomic prospective Integration and Decision service for Gate 8 Slice D."""

from __future__ import annotations

import json
from contextlib import AbstractContextManager
from datetime import datetime
from typing import Protocol, cast

from paim.assessment_review.models import AdequacyOutcome, AssessmentLane, CommandIdentity
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
from paim.prospective_decision.models import (
    AuthorizeDecisionCommand,
    ConfirmDecisionCommand,
    IntegrateValueRiskCommand,
    ProposeDecisionCommand,
    ProspectiveDecisionStatus,
    ProspectiveSelection,
    ProspectiveSelectionKind,
    ReliedLaneBasis,
)
from paim.responsibility.models import ObligationKind


class ProspectiveDecisionStore(Protocol):
    def semantic_transaction(self) -> AbstractContextManager[ContinuityTransaction]: ...
    def read_transaction(self) -> AbstractContextManager[ContinuityTransaction]: ...


class ProspectiveDecisionConflict(RuntimeError):
    pass


class ProspectiveDecisionAccessDenied(RuntimeError):
    def __init__(self) -> None:
        super().__init__("software access not established")


class ProspectiveDecisionService:
    """Consumes exact prospective relied lanes without legacy fallback or scoring."""

    def __init__(
        self,
        store: ProspectiveDecisionStore,
        clock: Clock,
        access: ContinuityAccessPolicy,
    ) -> None:
        self._store = store
        self._clock = clock
        self._access = access

    def integrate_value_risk(self, command: IntegrateValueRiskCommand) -> CommandOutcome:
        action = "integration.complete"
        digest = canonical_command_digest(
            cast("dict[str, JsonValue]", self._integration_payload(command))
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
            self._validate_relied_basis(tx, command, command.value_basis, recorded_at)
            self._validate_relied_basis(tx, command, command.risk_basis, recorded_at)
            all_sources = set(command.value_basis.version_ids + command.risk_basis.version_ids)
            all_sources.update(
                {
                    command.configuration_version_id,
                    command.responsibility_version_id,
                    command.assignment_version_id,
                    command.authority_source_version_id,
                }
            )
            self._expand_assignment_sources(tx, all_sources)
            self._validate_source_access(command, all_sources)
            self._validate_accountability(
                tx,
                command.case_id,
                command.context.digest,
                command.identity.actor_id,
                command.responsibility_version_id,
                command.assignment_version_id,
                ObligationKind.COMPLETE_VALUE_RISK_INTEGRATION,
                command.effective_at,
                recorded_at,
            )
            self._validate_authority(
                tx,
                command.authority_source_version_id,
                command.identity.actor_id,
                "INTEGRATE_VALUE_RISK",
                command.case_id,
                command.context.digest,
                command.decision_use,
                command.bounded_scope,
                command.effective_at,
                recorded_at,
            )
            self._ensure_contract_context(tx, command.contract, command.context, recorded_at)
            scope = self._integration_scope(
                command.case_id,
                command.configuration_version_id,
                command.context.digest,
                command.decision_use,
                command.bounded_scope,
            )
            observed = tx.select_current(
                SelectionQuery(
                    "prospective-integration",
                    scope,
                    command.effective_at,
                    recorded_at,
                    command.facts.record_id,
                )
            )
            self._expect(observed, command.expected_integration_version_id)
            content = cast(
                "dict[str, JsonValue]",
                {
                    "case_id": str(command.case_id),
                    "configuration_version_id": str(command.configuration_version_id),
                    "context_digest": command.context.digest,
                    "decision_use": command.decision_use,
                    "bounded_scope": command.bounded_scope,
                    "value_basis": self._basis_payload(command.value_basis),
                    "risk_basis": self._basis_payload(command.risk_basis),
                    "integration_rationale": command.integration_rationale,
                    "material_tensions": list(command.material_tensions),
                    "limitations": list(command.limitations),
                    "uncertainty": command.uncertainty,
                    "unresolved_conditions": list(command.unresolved_conditions),
                    "responsibility_version_id": str(command.responsibility_version_id),
                    "assignment_version_id": str(command.assignment_version_id),
                    "authority_source_version_id": str(command.authority_source_version_id),
                    "status": "COMPLETED",
                },
            )
            self._add_version(
                tx,
                command.facts.record_id,
                command.facts.version_id,
                "prospective-integration",
                scope,
                content,
                command.effective_at,
                recorded_at,
                command.identity.actor_id,
                command.contract.key,
                command.context.digest,
            )
            if command.expected_integration_version_id is None:
                tx.insert_projection(
                    "prospective_integration_records",
                    {"record_id": str(command.facts.record_id)},
                )
            tx.insert_projection(
                "prospective_integration_versions",
                {
                    "version_id": str(command.facts.version_id),
                    "record_id": str(command.facts.record_id),
                    "case_id": str(command.case_id),
                    "configuration_version_id": str(command.configuration_version_id),
                    "context_digest": command.context.digest,
                    "decision_use": command.decision_use,
                    "bounded_scope": command.bounded_scope,
                    "value_assessment_version_id": str(command.value_basis.assessment_version_id),
                    "value_readiness_version_id": str(command.value_basis.readiness_version_id),
                    "value_adequacy_version_id": str(command.value_basis.adequacy_version_id),
                    "value_reliance_version_id": str(command.value_basis.reliance_version_id),
                    "risk_assessment_version_id": str(command.risk_basis.assessment_version_id),
                    "risk_readiness_version_id": str(command.risk_basis.readiness_version_id),
                    "risk_adequacy_version_id": str(command.risk_basis.adequacy_version_id),
                    "risk_reliance_version_id": str(command.risk_basis.reliance_version_id),
                    "value_information_basis_json": json.dumps(
                        self._ids(command.value_basis.information_basis_version_ids)
                    ),
                    "risk_information_basis_json": json.dumps(
                        self._ids(command.risk_basis.information_basis_version_ids)
                    ),
                    "responsibility_version_id": str(command.responsibility_version_id),
                    "assignment_version_id": str(command.assignment_version_id),
                    "authority_source_version_id": str(command.authority_source_version_id),
                    "knowledge_cutoff_us": to_epoch_microseconds(command.knowledge_cutoff),
                    "predecessor_version_id": self._optional(
                        command.expected_integration_version_id
                    ),
                },
            )
            relationships, statuses = self._successor_history(
                tx,
                command.expected_integration_version_id,
                command.facts.version_id,
                "material prospective Integration successor",
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
                command.facts.record_id,
                (command.facts.version_id,),
                statuses,
                relationships,
                command.context.digest,
                command.effective_at,
                recorded_at,
                "PROSPECTIVE_INTEGRATION_COMMITTED",
                ("EXACT_VALUE_RISK_RELIED_BASIS", "NO_NETTING_OR_WINNER"),
            )

    def propose_decision(self, command: ProposeDecisionCommand) -> CommandOutcome:
        action = "decision.propose"
        digest = canonical_command_digest(
            cast("dict[str, JsonValue]", self._proposal_payload(command))
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
            integration = self._validate_integration_current(tx, command, recorded_at)
            self._validate_source_access(
                command, self._integration_required_versions(tx, integration)
            )
            self._validate_accountability(
                tx,
                command.case_id,
                command.context.digest,
                command.identity.actor_id,
                command.responsibility_version_id,
                command.assignment_version_id,
                ObligationKind.PROPOSE_MANAGEMENT_DECISION,
                command.effective_at,
                recorded_at,
            )
            self._ensure_contract_context(tx, command.contract, command.context, recorded_at)
            scope = self._decision_scope(
                command.case_id,
                command.configuration_version_id,
                command.context.digest,
                command.decision_use,
                command.bounded_scope,
            )
            current = tx.select_current(
                SelectionQuery("prospective-decision", scope, command.effective_at, recorded_at)
            )
            self._expect_global(current, command.expected_current_decision_version_id)
            if (
                command.predecessor_decision_version_id
                != command.expected_current_decision_version_id
            ):
                raise ProspectiveDecisionConflict(
                    "Decision predecessor must be the exact expected current Decision"
                )
            content = cast(
                "dict[str, JsonValue]",
                {
                    "case_id": str(command.case_id),
                    "configuration_version_id": str(command.configuration_version_id),
                    "integration_version_id": str(command.integration_version_id),
                    "context_digest": command.context.digest,
                    "decision_use": command.decision_use,
                    "bounded_scope": command.bounded_scope,
                    "proposed_action": command.proposed_action,
                    "operating_state": command.operating_state,
                    "rationale": command.rationale,
                    "conditions_and_limits": list(command.conditions_and_limits),
                    "alternatives_considered": list(command.alternatives_considered),
                    "responsibility_version_id": str(command.responsibility_version_id),
                    "assignment_version_id": str(command.assignment_version_id),
                    "status": ProspectiveDecisionStatus.PROPOSED.value,
                },
            )
            self._add_version(
                tx,
                command.facts.record_id,
                command.facts.version_id,
                "prospective-decision",
                scope,
                content,
                command.effective_at,
                recorded_at,
                command.identity.actor_id,
                command.contract.key,
                command.context.digest,
            )
            tx.insert_projection(
                "prospective_decision_records", {"record_id": str(command.facts.record_id)}
            )
            relationships, statuses = self._insert_decision_projection(
                tx,
                version_id=command.facts.version_id,
                record_id=command.facts.record_id,
                command=command,
                status=ProspectiveDecisionStatus.PROPOSED,
                integration=integration,
                responsibility_version_id=command.responsibility_version_id,
                assignment_version_id=command.assignment_version_id,
                authority_source_version_id=None,
                proposal_version_id=None,
                predecessor_version_id=command.predecessor_decision_version_id,
                knowledge_cutoff=command.knowledge_cutoff,
                effective_at=command.effective_at,
                recorded_at=recorded_at,
                actor_id=command.identity.actor_id,
                contract_key=command.contract.key,
                context_digest=command.context.digest,
                succession_reason="explicit prospective successor Decision proposal",
            )
            return self._finish_commit(
                tx,
                command.identity,
                digest,
                command.facts.record_id,
                (command.facts.version_id,),
                statuses,
                relationships,
                command.context.digest,
                command.effective_at,
                recorded_at,
                "PROSPECTIVE_DECISION_PROPOSED",
                ("PROPOSAL_NOT_AUTHORIZATION",),
            )

    def authorize_decision(self, command: AuthorizeDecisionCommand) -> CommandOutcome:
        action = "decision.authorize"
        digest = canonical_command_digest(
            cast("dict[str, JsonValue]", self._authorization_payload(command))
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
            proposal, integration = self._validate_proposal_current(tx, command, recorded_at)
            self._validate_source_access(
                command,
                self._decision_required_versions(tx, proposal)
                | self._integration_required_versions(tx, integration),
            )
            self._validate_accountability(
                tx,
                command.case_id,
                command.context.digest,
                command.identity.actor_id,
                command.responsibility_version_id,
                command.assignment_version_id,
                ObligationKind.AUTHORIZE_MANAGEMENT_DECISION,
                command.effective_at,
                recorded_at,
            )
            self._validate_authority(
                tx,
                command.authority_source_version_id,
                command.identity.actor_id,
                "AUTHORIZE_DECISION",
                command.case_id,
                command.context.digest,
                command.decision_use,
                command.authorized_scope,
                command.effective_at,
                recorded_at,
            )
            proposal_version = tx.get_version(command.proposal_version_id)
            assert proposal_version is not None
            content = dict(proposal_version.content)
            content.update(
                {
                    "status": ProspectiveDecisionStatus.AUTHORIZED.value,
                    "authority_source_version_id": str(command.authority_source_version_id),
                    "authority_identity": command.authority_identity,
                    "authorized_scope": command.authorized_scope,
                    "authority_limits": list(command.authority_limits),
                    "authorization_conditions": list(command.conditions),
                    "dissent": list(command.dissent),
                    "responsibility_version_id": str(command.responsibility_version_id),
                    "assignment_version_id": str(command.assignment_version_id),
                }
            )
            self._add_version(
                tx,
                proposal_version.record_id,
                command.facts.decision_version_id,
                "prospective-decision",
                proposal_version.scope,
                content,
                command.effective_at,
                recorded_at,
                command.identity.actor_id,
                command.contract.key,
                command.context.digest,
            )
            relationships, statuses = self._insert_decision_projection(
                tx,
                version_id=command.facts.decision_version_id,
                record_id=proposal_version.record_id,
                command=command,
                status=ProspectiveDecisionStatus.AUTHORIZED,
                integration=integration,
                responsibility_version_id=command.responsibility_version_id,
                assignment_version_id=command.assignment_version_id,
                authority_source_version_id=command.authority_source_version_id,
                proposal_version_id=command.proposal_version_id,
                predecessor_version_id=command.proposal_version_id,
                knowledge_cutoff=command.knowledge_cutoff,
                effective_at=command.effective_at,
                recorded_at=recorded_at,
                actor_id=command.identity.actor_id,
                contract_key=command.contract.key,
                context_digest=command.context.digest,
                succession_reason="separate Decision authorization",
            )
            self._add_version(
                tx,
                command.facts.authorization_record_id,
                command.facts.authorization_version_id,
                "prospective-decision-authorization",
                f"decision-version:{command.facts.decision_version_id}",
                cast(
                    "dict[str, JsonValue]",
                    {
                        "decision_version_id": str(command.facts.decision_version_id),
                        "proposal_version_id": str(command.proposal_version_id),
                        "integration_version_id": str(command.integration_version_id),
                        "authority_source_version_id": str(command.authority_source_version_id),
                        "authority_identity": command.authority_identity,
                        "authorized_scope": command.authorized_scope,
                        "authority_limits": list(command.authority_limits),
                        "conditions": list(command.conditions),
                        "dissent": list(command.dissent),
                    },
                ),
                command.effective_at,
                recorded_at,
                command.identity.actor_id,
                command.contract.key,
                command.context.digest,
            )
            tx.insert_projection(
                "prospective_decision_authorization_records",
                {"record_id": str(command.facts.authorization_record_id)},
            )
            tx.insert_projection(
                "prospective_decision_authorization_versions",
                {
                    "version_id": str(command.facts.authorization_version_id),
                    "record_id": str(command.facts.authorization_record_id),
                    "decision_version_id": str(command.facts.decision_version_id),
                    "proposal_version_id": str(command.proposal_version_id),
                    "integration_version_id": str(command.integration_version_id),
                    "case_id": str(command.case_id),
                    "configuration_version_id": str(command.configuration_version_id),
                    "context_digest": command.context.digest,
                    "authority_source_version_id": str(command.authority_source_version_id),
                    "responsibility_version_id": str(command.responsibility_version_id),
                    "assignment_version_id": str(command.assignment_version_id),
                },
            )
            return self._finish_commit(
                tx,
                command.identity,
                digest,
                proposal_version.record_id,
                (command.facts.decision_version_id, command.facts.authorization_version_id),
                statuses,
                relationships,
                command.context.digest,
                command.effective_at,
                recorded_at,
                "PROSPECTIVE_DECISION_AUTHORIZED",
                ("EXACT_DECISION_AUTHORITY", "AUTHORIZATION_SEPARATE_FROM_PROPOSAL"),
            )

    def confirm_decision(self, command: ConfirmDecisionCommand) -> CommandOutcome:
        action = "decision.confirm"
        digest = canonical_command_digest(
            cast("dict[str, JsonValue]", self._confirmation_payload(command))
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
            decision, integration = self._validate_authorized_current(tx, command, recorded_at)
            self._validate_source_access(
                command,
                self._decision_required_versions(tx, decision)
                | self._integration_required_versions(tx, integration),
            )
            self._validate_accountability(
                tx,
                command.case_id,
                command.context.digest,
                command.identity.actor_id,
                command.responsibility_version_id,
                command.assignment_version_id,
                ObligationKind.CONFIRM_MANAGEMENT_DECISION,
                command.effective_at,
                recorded_at,
            )
            self._validate_authority(
                tx,
                command.authority_source_version_id,
                command.identity.actor_id,
                "CONFIRM_DECISION",
                command.case_id,
                command.context.digest,
                command.decision_use,
                command.bounded_scope,
                command.effective_at,
                recorded_at,
            )
            self._add_version(
                tx,
                command.facts.record_id,
                command.facts.version_id,
                "prospective-decision-confirmation",
                f"decision-version:{command.decision_version_id}",
                cast(
                    "dict[str, JsonValue]",
                    {
                        "decision_version_id": str(command.decision_version_id),
                        "integration_version_id": str(command.integration_version_id),
                        "configuration_version_id": str(command.configuration_version_id),
                        "rationale": command.rationale,
                        "responsibility_version_id": str(command.responsibility_version_id),
                        "assignment_version_id": str(command.assignment_version_id),
                        "authority_source_version_id": str(command.authority_source_version_id),
                        "outcome": "UNCHANGED_DECISION_CONFIRMED",
                    },
                ),
                command.effective_at,
                recorded_at,
                command.identity.actor_id,
                command.contract.key,
                command.context.digest,
            )
            tx.insert_projection(
                "prospective_decision_confirmation_records",
                {"record_id": str(command.facts.record_id)},
            )
            tx.insert_projection(
                "prospective_decision_confirmation_versions",
                {
                    "version_id": str(command.facts.version_id),
                    "record_id": str(command.facts.record_id),
                    "decision_version_id": str(command.decision_version_id),
                    "integration_version_id": str(command.integration_version_id),
                    "case_id": str(command.case_id),
                    "configuration_version_id": str(command.configuration_version_id),
                    "context_digest": command.context.digest,
                    "responsibility_version_id": str(command.responsibility_version_id),
                    "assignment_version_id": str(command.assignment_version_id),
                    "authority_source_version_id": str(command.authority_source_version_id),
                },
            )
            return self._finish_commit(
                tx,
                command.identity,
                digest,
                command.facts.record_id,
                (command.facts.version_id,),
                (),
                (),
                command.context.digest,
                command.effective_at,
                recorded_at,
                "PROSPECTIVE_DECISION_CONFIRMED",
                ("UNCHANGED_DECISION_ONLY",),
            )

    def select_integration(
        self,
        *,
        case_id: RecordId,
        configuration_version_id: RecordVersionId,
        context: ExactContextSet,
        decision_use: str,
        bounded_scope: str,
        effective_at: datetime,
        known_at: datetime,
    ) -> ProspectiveSelection:
        return self._select(
            "prospective-integration",
            self._integration_scope(
                case_id, configuration_version_id, context.digest, decision_use, bounded_scope
            ),
            effective_at,
            known_at,
        )

    def select_decision(
        self,
        *,
        case_id: RecordId,
        configuration_version_id: RecordVersionId,
        context: ExactContextSet,
        decision_use: str,
        bounded_scope: str,
        effective_at: datetime,
        known_at: datetime,
    ) -> ProspectiveSelection:
        return self._select(
            "prospective-decision",
            self._decision_scope(
                case_id, configuration_version_id, context.digest, decision_use, bounded_scope
            ),
            effective_at,
            known_at,
        )

    def _select(
        self, family: str, scope: str, effective_at: datetime, known_at: datetime
    ) -> ProspectiveSelection:
        require_utc(effective_at)
        require_utc(known_at)
        with self._store.read_transaction() as tx:
            selected = tx.select_current(SelectionQuery(family, scope, effective_at, known_at))
            if isinstance(selected, SelectionAbsent):
                return ProspectiveSelection(ProspectiveSelectionKind.ABSENT, ())
            candidates = (
                selected.candidates
                if isinstance(selected, SelectionConflict)
                else (cast(SelectionFound, selected).candidate,)
            )
            eligible = tuple(
                candidate
                for candidate in candidates
                if self._prospective_candidate_eligible(
                    tx, family, candidate.version_id, effective_at, known_at
                )
            )
            ids = tuple(sorted((candidate.version_id for candidate in eligible), key=str))
            if not ids:
                return ProspectiveSelection(ProspectiveSelectionKind.ABSENT, ())
            if len(ids) != 1:
                return ProspectiveSelection(ProspectiveSelectionKind.CONFLICT, ids)
            version = tx.get_version(ids[0])
            return ProspectiveSelection(
                ProspectiveSelectionKind.ONE,
                ids,
                str(version.content.get("status")) if version else None,
            )

    def _prospective_candidate_eligible(
        self,
        tx: ContinuityTransaction,
        family: str,
        version_id: RecordVersionId,
        effective_at: datetime,
        known_at: datetime,
    ) -> bool:
        table = {
            "prospective-integration": "prospective_integration_versions",
            "prospective-decision": "prospective_decision_versions",
        }[family]
        rows = tx.projection_rows(table, version_id=str(version_id))
        if len(rows) != 1:
            return False
        row = rows[0]
        if family == "prospective-decision":
            integrations = tx.projection_rows(
                "prospective_integration_versions",
                version_id=str(row["integration_version_id"]),
            )
            if len(integrations) != 1 or not self._integration_basis_current(
                tx, integrations[0], effective_at, known_at
            ):
                return False
        return (
            self._integration_basis_current(tx, row, effective_at, known_at)
            if family == "prospective-integration"
            else True
        )

    @staticmethod
    def _integration_basis_current(
        tx: ContinuityTransaction,
        row: dict[str, object],
        effective_at: datetime,
        known_at: datetime,
    ) -> bool:
        try:
            for lane in ("value", "risk"):
                for component in ("assessment", "readiness", "adequacy", "reliance"):
                    version_id = RecordVersionId.parse(str(row[f"{lane}_{component}_version_id"]))
                    version = tx.get_version(version_id)
                    if version is None:
                        return False
                    selected = tx.select_current(
                        SelectionQuery(
                            version.family,
                            version.scope,
                            effective_at,
                            known_at,
                            version.record_id if component != "reliance" else None,
                        )
                    )
                    if not (
                        isinstance(selected, SelectionFound)
                        and selected.candidate.version_id == version_id
                    ):
                        return False
                encoded = row[f"{lane}_information_basis_json"]
                if not isinstance(encoded, str):
                    return False
                for value in cast(list[str], json.loads(encoded)):
                    version_id = RecordVersionId.parse(value)
                    version = tx.get_version(version_id)
                    if version is None:
                        return False
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
                    ):
                        return False
            return True
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            return False

    def _validate_relied_basis(
        self,
        tx: ContinuityTransaction,
        command: IntegrateValueRiskCommand,
        basis: ReliedLaneBasis,
        known_at: datetime,
    ) -> None:
        rows = tx.projection_rows(
            "assessment_reliance_versions", version_id=str(basis.reliance_version_id)
        )
        if len(rows) != 1:
            raise ProspectiveDecisionConflict(f"{basis.lane.value} reliance is not established")
        row = rows[0]
        expected = {
            "lane": basis.lane.value,
            "assessment_version_id": str(basis.assessment_version_id),
            "readiness_version_id": str(basis.readiness_version_id),
            "adequacy_version_id": str(basis.adequacy_version_id),
            "case_id": str(command.case_id),
            "configuration_version_id": str(command.configuration_version_id),
            "context_digest": command.context.digest,
            "decision_use": command.decision_use,
            "assessed_scope": command.bounded_scope,
        }
        if any(row.get(key) != value for key, value in expected.items()) or json.loads(
            cast(str, row["information_basis_version_ids_json"])
        ) != self._ids(basis.information_basis_version_ids):
            raise ProspectiveDecisionConflict(
                f"{basis.lane.value} relied chain does not match exact Integration context"
            )
        adequacy = tx.projection_rows(
            "assessment_adequacy_versions", version_id=str(basis.adequacy_version_id)
        )
        if len(adequacy) != 1 or adequacy[0]["outcome"] != AdequacyOutcome.ADEQUATE.value:
            raise ProspectiveDecisionConflict(
                "Adequacy alone is not Reliance and relied adequacy must be ADEQUATE"
            )
        for version_id in basis.version_ids:
            self._require_current_version(
                tx,
                version_id,
                command.effective_at,
                known_at,
                f"{basis.lane.value} relied chain is stale",
            )
        reliance_version = tx.get_version(basis.reliance_version_id)
        if reliance_version is None or reliance_version.family != "assessment-reliance":
            raise ProspectiveDecisionConflict(
                f"{basis.lane.value} reliance is not a prospective Reliance Version"
            )
        selected = tx.select_current(
            SelectionQuery(
                "assessment-reliance",
                reliance_version.scope,
                command.effective_at,
                known_at,
            )
        )
        if (
            not isinstance(selected, SelectionFound)
            or selected.candidate.version_id != basis.reliance_version_id
        ):
            raise ProspectiveDecisionConflict(
                f"{basis.lane.value} reliance is absent or conflicting; no implicit winner"
            )

    def _validate_integration_current(
        self,
        tx: ContinuityTransaction,
        command: ProposeDecisionCommand | AuthorizeDecisionCommand | ConfirmDecisionCommand,
        known_at: datetime,
    ) -> dict[str, object]:
        self._validate_case_context(
            tx,
            command.case_id,
            command.configuration_version_id,
            command.context.digest,
            command.effective_at,
            known_at,
        )
        rows = tx.projection_rows(
            "prospective_integration_versions", version_id=str(command.integration_version_id)
        )
        if len(rows) != 1:
            raise ProspectiveDecisionConflict("exact prospective Integration is not established")
        row = rows[0]
        if any(
            row.get(key) != value
            for key, value in {
                "case_id": str(command.case_id),
                "configuration_version_id": str(command.configuration_version_id),
                "context_digest": command.context.digest,
                "decision_use": command.decision_use,
                "bounded_scope": command.bounded_scope,
            }.items()
        ):
            raise ProspectiveDecisionConflict("Integration does not bind exact Decision context")
        self._require_current_version(
            tx,
            command.integration_version_id,
            command.effective_at,
            known_at,
            "Integration is stale",
        )
        for lane in ("value", "risk"):
            basis = ReliedLaneBasis(
                AssessmentLane(lane.upper()),
                RecordVersionId.parse(str(row[f"{lane}_assessment_version_id"])),
                RecordVersionId.parse(str(row[f"{lane}_readiness_version_id"])),
                RecordVersionId.parse(str(row[f"{lane}_adequacy_version_id"])),
                RecordVersionId.parse(str(row[f"{lane}_reliance_version_id"])),
                tuple(
                    RecordVersionId.parse(value)
                    for value in json.loads(cast(str, row[f"{lane}_information_basis_json"]))
                ),
            )
            proxy = cast(IntegrateValueRiskCommand, command)
            # The validation uses only the shared exact context fields.
            self._validate_relied_basis(tx, proxy, basis, known_at)
        return row

    def _validate_proposal_current(
        self, tx: ContinuityTransaction, command: AuthorizeDecisionCommand, known_at: datetime
    ) -> tuple[dict[str, object], dict[str, object]]:
        integration = self._validate_integration_current(tx, command, known_at)
        rows = tx.projection_rows(
            "prospective_decision_versions", version_id=str(command.proposal_version_id)
        )
        if (
            len(rows) != 1
            or rows[0]["status"] != ProspectiveDecisionStatus.PROPOSED.value
            or rows[0]["integration_version_id"] != str(command.integration_version_id)
        ):
            raise ProspectiveDecisionConflict(
                "exact Decision proposal/Integration chain is not established"
            )
        self._require_current_version(
            tx,
            command.proposal_version_id,
            command.effective_at,
            known_at,
            "Decision proposal is stale",
        )
        return rows[0], integration

    def _validate_authorized_current(
        self, tx: ContinuityTransaction, command: ConfirmDecisionCommand, known_at: datetime
    ) -> tuple[dict[str, object], dict[str, object]]:
        integration = self._validate_integration_current(tx, command, known_at)
        rows = tx.projection_rows(
            "prospective_decision_versions", version_id=str(command.decision_version_id)
        )
        if (
            len(rows) != 1
            or rows[0]["status"] != ProspectiveDecisionStatus.AUTHORIZED.value
            or rows[0]["integration_version_id"] != str(command.integration_version_id)
        ):
            raise ProspectiveDecisionConflict("exact authorized Decision is not established")
        self._require_current_version(
            tx,
            command.decision_version_id,
            command.effective_at,
            known_at,
            "authorized Decision is stale",
        )
        return rows[0], integration

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
            raise ProspectiveDecisionConflict("exact prospective OPEN Case is not established")
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
            raise ProspectiveDecisionConflict("Case continuity is absent or conflicting")
        statuses = tx.projection_rows(
            "case_continuity_status_versions", version_id=str(selected.candidate.version_id)
        )
        if len(statuses) != 1 or statuses[0]["status"] != "OPEN":
            raise ProspectiveDecisionConflict("prospective Case is not OPEN")
        governing = tx.select_current(
            SelectionQuery("governing-configuration", f"case:{case_id}", effective_at, known_at)
        )
        if not isinstance(governing, SelectionFound):
            raise ProspectiveDecisionConflict("governing Configuration is absent or conflicting")
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
            raise ProspectiveDecisionConflict("exact governing Configuration/context mismatch")

    def _validate_accountability(
        self,
        tx: ContinuityTransaction,
        case_id: RecordId,
        context_digest: str,
        actor_id: RecordId,
        responsibility_version_id: RecordVersionId,
        assignment_version_id: RecordVersionId,
        obligation: ObligationKind,
        effective_at: datetime,
        known_at: datetime,
    ) -> None:
        responsibilities = tx.projection_rows(
            "responsibility_versions", version_id=str(responsibility_version_id)
        )
        assignments = tx.projection_rows(
            "responsibility_assignment_versions", version_id=str(assignment_version_id)
        )
        if len(responsibilities) != 1 or len(assignments) != 1:
            raise ProspectiveDecisionConflict("exact Responsibility/assignment is not established")
        responsibility, assignment = responsibilities[0], assignments[0]
        if (
            responsibility["obligation_kind"] != obligation.value
            or responsibility["owning_case_id"] != str(case_id)
            or responsibility["context_digest"] != context_digest
            or assignment["responsibility_version_id"] != str(responsibility_version_id)
            or assignment["actor_id"] != str(actor_id)
            or assignment["state"] != "ASSIGNED"
        ):
            raise ProspectiveDecisionConflict("accountability does not match exact governed act")
        self._require_current_version(
            tx, responsibility_version_id, effective_at, known_at, "Responsibility is stale"
        )
        self._require_current_version(
            tx, assignment_version_id, effective_at, known_at, "assignment is stale"
        )
        eligible: list[dict[str, object]] = []
        for row in tx.projection_rows(
            "responsibility_assignment_versions",
            signature_digest=str(responsibility["signature_digest"]),
        ):
            try:
                self._require_current_version(
                    tx, RecordVersionId.parse(str(row["version_id"])), effective_at, known_at, ""
                )
            except ProspectiveDecisionConflict:
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
            raise ProspectiveDecisionConflict("Responsibility vacancy or conflict")
        basis = tx.projection_rows(
            "assignment_basis_versions", version_id=str(assignment["assignment_basis_version_id"])
        )
        if len(basis) != 1 or basis[0]["state"] != "ACTIVE":
            raise ProspectiveDecisionConflict("exact Assignment Basis is not active")
        basis_row = basis[0]
        basis_id = RecordVersionId.parse(str(basis_row["version_id"]))
        source_id = RecordVersionId.parse(str(basis_row["basis_source_version_id"]))
        self._require_current_version(
            tx, basis_id, effective_at, known_at, "Assignment Basis is stale"
        )
        self._require_current_version(
            tx, source_id, effective_at, known_at, "assignment authority source is stale"
        )
        source = tx.get_version(source_id)
        authority = source.content.get("assignment_authority") if source else None
        if (
            not isinstance(authority, dict)
            or obligation.value
            not in cast(list[str], authority.get("allowed_obligation_kinds", []))
            or str(case_id) not in cast(list[str], authority.get("allowed_case_ids", []))
            or str(responsibility["signature_digest"])
            not in cast(list[str], authority.get("allowed_signature_digests", []))
            or authority.get("context_digest") != context_digest
        ):
            raise ProspectiveDecisionConflict(
                "Assignment Basis does not authorize exact governed act"
            )

    def _validate_authority(
        self,
        tx: ContinuityTransaction,
        version_id: RecordVersionId,
        actor_id: RecordId,
        action: str,
        case_id: RecordId,
        context_digest: str,
        decision_use: str,
        bounded_scope: str,
        effective_at: datetime,
        known_at: datetime,
    ) -> None:
        self._require_current_version(
            tx, version_id, effective_at, known_at, "substantive authority source is stale"
        )
        source = tx.get_version(version_id)
        authority = (
            source.content.get("prospective_substantive_authority")
            if source and source.family == "authority-record"
            else None
        )
        if (
            not isinstance(authority, dict)
            or authority.get("actor_id") != str(actor_id)
            or action not in cast(list[str], authority.get("allowed_actions", []))
            or str(case_id) not in cast(list[str], authority.get("allowed_case_ids", []))
            or authority.get("context_digest") != context_digest
            or decision_use not in cast(list[str], authority.get("allowed_decision_uses", []))
            or bounded_scope not in cast(list[str], authority.get("allowed_scopes", []))
        ):
            raise ProspectiveDecisionConflict("exact substantive authority is not established")

    def _validate_source_access(
        self,
        command: IntegrateValueRiskCommand
        | ProposeDecisionCommand
        | AuthorizeDecisionCommand
        | ConfirmDecisionCommand,
        version_ids: set[RecordVersionId],
    ) -> None:
        identity = command.identity
        case_id = command.case_id
        for version_id in version_ids:
            if not self._access.authorize(
                principal_id=str(identity.principal_id),
                actor_id=str(identity.actor_id),
                action="source.read",
                case_id=case_id,
                write=False,
                source_version_id=version_id,
                source_family=None,
                effective_at=command.effective_at,
                known_at=command.knowledge_cutoff,
            ):
                raise ProspectiveDecisionAccessDenied()

    def _require_access(
        self,
        command: IntegrateValueRiskCommand
        | ProposeDecisionCommand
        | AuthorizeDecisionCommand
        | ConfirmDecisionCommand,
        action: str,
    ) -> None:
        identity = command.identity
        if not self._access.authorize(
            principal_id=str(identity.principal_id),
            actor_id=str(identity.actor_id),
            action=action,
            case_id=command.case_id,
            write=True,
        ):
            raise ProspectiveDecisionAccessDenied()

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
            raise ProspectiveDecisionConflict(reason or "exact Version unavailable")
        selected = tx.select_current(
            SelectionQuery(version.family, version.scope, effective_at, known_at, version.record_id)
        )
        if not isinstance(selected, SelectionFound) or selected.candidate.version_id != version_id:
            raise ProspectiveDecisionConflict(reason or "exact Version is not current")

    @staticmethod
    def _expect(selected: object, expected: RecordVersionId | None) -> None:
        if expected is None and not isinstance(selected, SelectionAbsent):
            raise ProspectiveDecisionConflict("expected absent prospective record")
        if expected is not None and not (
            isinstance(selected, SelectionFound) and selected.candidate.version_id == expected
        ):
            raise ProspectiveDecisionConflict("stale exact predecessor; no retarget permitted")

    @staticmethod
    def _expect_global(selected: object, expected: RecordVersionId | None) -> None:
        ProspectiveDecisionService._expect(selected, expected)

    @staticmethod
    def _replay(
        tx: ContinuityTransaction, scope: str, key: str, digest: str
    ) -> CommandOutcome | None:
        fact = tx.get_idempotency(scope, key)
        if fact is None:
            return None
        if fact.digest != digest:
            raise ProspectiveDecisionConflict("IDEMPOTENCY KEY REUSE CONFLICT")
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
                "consumer_id": "gate8-slice-d",
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
            "prospective-integration",
            "prospective-decision",
            "prospective-decision-authorization",
            "prospective-decision-confirmation",
        ):
            if not tx.projection_rows(
                "semantic_contract_families", contract_key=contract.key, record_family=family
            ):
                tx.insert_projection(
                    "semantic_contract_families",
                    {"contract_key": contract.key, "record_family": family},
                )

    @staticmethod
    def _successor_history(
        tx: ContinuityTransaction,
        predecessor: RecordVersionId | None,
        successor: RecordVersionId,
        reason: str,
        effective_at: datetime,
        recorded_at: datetime,
        actor_id: RecordId,
        contract_key: str,
        context_digest: str,
    ) -> tuple[tuple[RelationshipId, ...], tuple[EventId, ...]]:
        if predecessor is None:
            return (), ()
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
            effective_at,
            str(actor_id),
            reason,
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
        reasons: tuple[str, ...],
    ) -> CommandOutcome:
        audit = AuditFact(
            AuditId.new(),
            str(identity.principal_id),
            str(identity.actor_id),
            ActorResolution.PROVIDED,
            action,
            "COMMITTED",
            identity.command_id,
            str(identity.idempotency_scope),
            str(identity.idempotency_key),
            None,
            None,
            record_id,
            versions,
            "EXACT_CONTEXT_AND_EXPECTED_BASIS",
            context_digest,
            effective_at,
            recorded_at,
            reasons,
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
                str(identity.idempotency_scope),
                str(identity.idempotency_key),
                digest,
                str(identity.command_id),
                outcome,
                recorded_at,
            )
        )
        return outcome

    @staticmethod
    def _insert_decision_projection(
        tx: ContinuityTransaction,
        *,
        version_id: RecordVersionId,
        record_id: RecordId,
        command: ProposeDecisionCommand | AuthorizeDecisionCommand,
        status: ProspectiveDecisionStatus,
        integration: dict[str, object],
        responsibility_version_id: RecordVersionId,
        assignment_version_id: RecordVersionId,
        authority_source_version_id: RecordVersionId | None,
        proposal_version_id: RecordVersionId | None,
        predecessor_version_id: RecordVersionId | None,
        knowledge_cutoff: datetime,
        effective_at: datetime,
        recorded_at: datetime,
        actor_id: RecordId,
        contract_key: str,
        context_digest: str,
        succession_reason: str,
    ) -> tuple[tuple[RelationshipId, ...], tuple[EventId, ...]]:
        """Persist one Decision projection and its canonical succession facts.

        The projection predecessor is not an independent currentness hint.  When
        present, it is always materialized by this same operation as the kernel
        supersession relationship and predecessor status event consumed by
        ``select_current``.  Keeping the three representations behind one helper
        prevents a Decision successor from becoming co-current with its predecessor.
        """
        if predecessor_version_id is not None:
            predecessor = tx.get_version(predecessor_version_id)
            successor = tx.get_version(version_id)
            if predecessor is None or successor is None:
                raise ProspectiveDecisionConflict(
                    "Decision succession requires exact persisted predecessor "
                    "and successor Versions"
                )
            if (
                predecessor.family != "prospective-decision"
                or successor.family != "prospective-decision"
                or predecessor.scope != successor.scope
            ):
                raise ProspectiveDecisionConflict(
                    "Decision succession requires one exact Decision family and scope"
                )
        tx.insert_projection(
            "prospective_decision_versions",
            {
                "version_id": str(version_id),
                "record_id": str(record_id),
                "case_id": str(command.case_id),
                "configuration_version_id": str(command.configuration_version_id),
                "context_digest": command.context.digest,
                "integration_version_id": str(command.integration_version_id),
                "decision_use": command.decision_use,
                "bounded_scope": command.bounded_scope,
                "status": status.value,
                "value_assessment_version_id": str(integration["value_assessment_version_id"]),
                "value_readiness_version_id": str(integration["value_readiness_version_id"]),
                "value_adequacy_version_id": str(integration["value_adequacy_version_id"]),
                "value_reliance_version_id": str(integration["value_reliance_version_id"]),
                "risk_assessment_version_id": str(integration["risk_assessment_version_id"]),
                "risk_readiness_version_id": str(integration["risk_readiness_version_id"]),
                "risk_adequacy_version_id": str(integration["risk_adequacy_version_id"]),
                "risk_reliance_version_id": str(integration["risk_reliance_version_id"]),
                "responsibility_version_id": str(responsibility_version_id),
                "assignment_version_id": str(assignment_version_id),
                "authority_source_version_id": ProspectiveDecisionService._optional(
                    authority_source_version_id
                ),
                "proposal_version_id": ProspectiveDecisionService._optional(proposal_version_id),
                "predecessor_version_id": ProspectiveDecisionService._optional(
                    predecessor_version_id
                ),
                "knowledge_cutoff_us": to_epoch_microseconds(knowledge_cutoff),
            },
        )
        return ProspectiveDecisionService._successor_history(
            tx,
            predecessor_version_id,
            version_id,
            succession_reason,
            effective_at,
            recorded_at,
            actor_id,
            contract_key,
            context_digest,
        )

    @staticmethod
    def _integration_required_versions(
        tx: ContinuityTransaction, row: dict[str, object]
    ) -> set[RecordVersionId]:
        required = {
            RecordVersionId.parse(str(row[field]))
            for field in (
                "version_id",
                "configuration_version_id",
                "value_assessment_version_id",
                "value_readiness_version_id",
                "value_adequacy_version_id",
                "value_reliance_version_id",
                "risk_assessment_version_id",
                "risk_readiness_version_id",
                "risk_adequacy_version_id",
                "risk_reliance_version_id",
                "responsibility_version_id",
                "assignment_version_id",
                "authority_source_version_id",
            )
        }
        for field in ("value_information_basis_json", "risk_information_basis_json"):
            required.update(
                RecordVersionId.parse(value) for value in json.loads(cast(str, row[field]))
            )
        ProspectiveDecisionService._expand_assignment_sources(tx, required)
        return required

    @staticmethod
    def _decision_required_versions(
        tx: ContinuityTransaction, row: dict[str, object]
    ) -> set[RecordVersionId]:
        result = {
            RecordVersionId.parse(str(row[field]))
            for field in (
                "version_id",
                "configuration_version_id",
                "integration_version_id",
                "responsibility_version_id",
                "assignment_version_id",
            )
        }
        for field in ("authority_source_version_id", "proposal_version_id"):
            if row.get(field):
                result.add(RecordVersionId.parse(str(row[field])))
        ProspectiveDecisionService._expand_assignment_sources(tx, result)
        return result

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
    def _integration_scope(
        case_id: RecordId,
        configuration_version_id: RecordVersionId,
        context_digest: str,
        decision_use: str,
        bounded_scope: str,
    ) -> str:
        return (
            f"prospective-integration:case:{case_id}:"
            f"configuration-version:{configuration_version_id}:context:{context_digest}:"
            f"use:{decision_use}:scope:{bounded_scope}"
        )

    @staticmethod
    def _decision_scope(
        case_id: RecordId,
        configuration_version_id: RecordVersionId,
        context_digest: str,
        decision_use: str,
        bounded_scope: str,
    ) -> str:
        return (
            f"prospective-decision:case:{case_id}:"
            f"configuration-version:{configuration_version_id}:context:{context_digest}:"
            f"use:{decision_use}:scope:{bounded_scope}"
        )

    @staticmethod
    def _basis_payload(basis: ReliedLaneBasis) -> dict[str, JsonValue]:
        return {
            "lane": basis.lane.value,
            "assessment_version_id": str(basis.assessment_version_id),
            "readiness_version_id": str(basis.readiness_version_id),
            "adequacy_version_id": str(basis.adequacy_version_id),
            "reliance_version_id": str(basis.reliance_version_id),
            "information_basis_version_ids": cast(
                "list[JsonValue]",
                ProspectiveDecisionService._ids(basis.information_basis_version_ids),
            ),
        }

    @staticmethod
    def _ids(values: tuple[RecordVersionId, ...]) -> list[str]:
        return [str(value) for value in values]

    @staticmethod
    def _optional(value: RecordVersionId | None) -> str | None:
        return str(value) if value is not None else None

    @staticmethod
    def _integration_payload(command: IntegrateValueRiskCommand) -> dict[str, object]:
        return {
            "contract": command.contract.key,
            "context": command.context.digest,
            "case_id": str(command.case_id),
            "configuration_version_id": str(command.configuration_version_id),
            "decision_use": command.decision_use,
            "bounded_scope": command.bounded_scope,
            "facts": [str(command.facts.record_id), str(command.facts.version_id)],
            "value_basis": ProspectiveDecisionService._basis_payload(command.value_basis),
            "risk_basis": ProspectiveDecisionService._basis_payload(command.risk_basis),
            "rationale": command.integration_rationale,
            "material_tensions": list(command.material_tensions),
            "limitations": list(command.limitations),
            "uncertainty": command.uncertainty,
            "unresolved_conditions": list(command.unresolved_conditions),
            "responsibility_version_id": str(command.responsibility_version_id),
            "assignment_version_id": str(command.assignment_version_id),
            "authority_source_version_id": str(command.authority_source_version_id),
            "expected": ProspectiveDecisionService._optional(
                command.expected_integration_version_id
            ),
            "effective_at": command.effective_at.isoformat(),
            "knowledge_cutoff": command.knowledge_cutoff.isoformat(),
        }

    @staticmethod
    def _proposal_payload(command: ProposeDecisionCommand) -> dict[str, object]:
        return {
            "contract": command.contract.key,
            "context": command.context.digest,
            "case_id": str(command.case_id),
            "configuration_version_id": str(command.configuration_version_id),
            "integration_version_id": str(command.integration_version_id),
            "decision_use": command.decision_use,
            "bounded_scope": command.bounded_scope,
            "facts": [str(command.facts.record_id), str(command.facts.version_id)],
            "proposed_action": command.proposed_action,
            "operating_state": command.operating_state,
            "rationale": command.rationale,
            "conditions": list(command.conditions_and_limits),
            "alternatives": list(command.alternatives_considered),
            "responsibility_version_id": str(command.responsibility_version_id),
            "assignment_version_id": str(command.assignment_version_id),
            "predecessor": ProspectiveDecisionService._optional(
                command.predecessor_decision_version_id
            ),
            "expected": ProspectiveDecisionService._optional(
                command.expected_current_decision_version_id
            ),
            "effective_at": command.effective_at.isoformat(),
            "knowledge_cutoff": command.knowledge_cutoff.isoformat(),
        }

    @staticmethod
    def _authorization_payload(command: AuthorizeDecisionCommand) -> dict[str, object]:
        return {
            "contract": command.contract.key,
            "context": command.context.digest,
            "case_id": str(command.case_id),
            "configuration_version_id": str(command.configuration_version_id),
            "proposal_version_id": str(command.proposal_version_id),
            "integration_version_id": str(command.integration_version_id),
            "decision_use": command.decision_use,
            "bounded_scope": command.bounded_scope,
            "facts": [
                str(command.facts.decision_version_id),
                str(command.facts.authorization_record_id),
                str(command.facts.authorization_version_id),
            ],
            "responsibility_version_id": str(command.responsibility_version_id),
            "assignment_version_id": str(command.assignment_version_id),
            "authority_source_version_id": str(command.authority_source_version_id),
            "authority_identity": command.authority_identity,
            "authorized_scope": command.authorized_scope,
            "authority_limits": list(command.authority_limits),
            "conditions": list(command.conditions),
            "dissent": list(command.dissent),
            "effective_at": command.effective_at.isoformat(),
            "knowledge_cutoff": command.knowledge_cutoff.isoformat(),
        }

    @staticmethod
    def _confirmation_payload(command: ConfirmDecisionCommand) -> dict[str, object]:
        return {
            "contract": command.contract.key,
            "context": command.context.digest,
            "case_id": str(command.case_id),
            "configuration_version_id": str(command.configuration_version_id),
            "decision_version_id": str(command.decision_version_id),
            "integration_version_id": str(command.integration_version_id),
            "decision_use": command.decision_use,
            "bounded_scope": command.bounded_scope,
            "facts": [str(command.facts.record_id), str(command.facts.version_id)],
            "rationale": command.rationale,
            "responsibility_version_id": str(command.responsibility_version_id),
            "assignment_version_id": str(command.assignment_version_id),
            "authority_source_version_id": str(command.authority_source_version_id),
            "effective_at": command.effective_at.isoformat(),
            "knowledge_cutoff": command.knowledge_cutoff.isoformat(),
        }
