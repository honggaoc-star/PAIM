"""Increment 3 semantic commands composed on the accepted PAIM integrity kernel."""

from __future__ import annotations

import json
from datetime import datetime
from typing import cast

from paim.application.increment2 import DomainRuleViolation, Increment2ApplicationService
from paim.application.service import CommitStatusCommand, IntegrityApplicationService
from paim.domain.increment3 import (
    AcceptanceSelectionDetail,
    AcceptanceSelectionVersionInput,
    AnalyticalHandoffReadiness,
    AnalyticalInputVersionInput,
    AnalyticalLane,
    ApplicabilityConflict,
    ApplicabilityFound,
    ApplicabilityNotEstablished,
    ApplicabilitySelection,
    ApplicabilityTargetType,
    AuthorityGapVersionInput,
    AuthorityVersionInput,
    CandidateDispositionVersionInput,
    EvidenceApplicabilityVersionInput,
    EvidenceAttention,
    EvidenceVersionInput,
    FitnessOutcome,
    InputSelection,
    InputSelectionConflict,
    InputSelectionFound,
    InputSelectionNotEstablished,
    LaneFitnessVersionInput,
)
from paim.domain.increment3_ports import Increment3Store, Increment3Transaction
from paim.domain.models import (
    CommandMeta,
    GoverningConfigurationConflict,
    GoverningConfigurationFound,
    RoleTargetType,
)
from paim.integrity import (
    EventId,
    RecordId,
    RecordVersionId,
    RelationshipId,
    RelationshipType,
    SelectionAbsent,
    SelectionCandidate,
    SelectionFound,
    SelectionQuery,
    StatusEvent,
    VersionRelationship,
)
from paim.integrity.records import JsonValue
from paim.integrity.time import Clock, require_utc, to_epoch_microseconds
from paim.persistence.ports import CommandOutcome, IntegrityStore


def _accountability_present(
    assignment_version_id: RecordVersionId | None, mechanism: str | None
) -> bool:
    return (assignment_version_id is not None) != bool(mechanism)


def _applicability_scope(value: EvidenceApplicabilityVersionInput) -> str:
    target_version = str(value.target_version_id) if value.target_version_id else "question"
    question_context = (
        f":case:{value.case_id}:configuration-version:{value.configuration_version_id}"
        if value.target_version_id is None
        else ""
    )
    return (
        f"evidence-version:{value.evidence_version_id}:target:{value.target_type.value}:"
        f"{value.target_id}:{target_version}{question_context}:"
        f"purpose:{value.purpose}:scope:{value.assessed_scope}"
    )


def _selection_scope(
    *,
    lane: AnalyticalLane,
    configuration_version_id: RecordVersionId,
    use_context: str,
    purpose: str,
) -> str:
    return (
        f"lane:{lane.value}:configuration-version:{configuration_version_id}:"
        f"use:{use_context}:purpose:{purpose}"
    )


class Increment3ApplicationService(Increment2ApplicationService):
    """Bounded synchronous application boundary for Increment 3 behavior."""

    def __init__(self, store: Increment3Store, clock: Clock) -> None:
        super().__init__(store, clock)
        self._increment3_store = store

    def _configuration_context(
        self,
        transaction: Increment3Transaction,
        *,
        case_id: RecordId,
        configuration_id: RecordId,
        configuration_version_id: RecordVersionId,
    ) -> None:
        context = transaction.configuration_version_context(configuration_version_id)
        if (
            context is None
            or context.configuration_id != configuration_id
            or context.owning_case_id != case_id
            or context.maturity != "finalized"
        ):
            raise DomainRuleViolation(
                "exact finalized Configuration Version and owning Case context are required"
            )

    def _governing_context(
        self,
        transaction: Increment3Transaction,
        *,
        case_id: RecordId,
        configuration_version_id: RecordVersionId,
        effective_at: datetime,
        known_at: datetime,
    ) -> None:
        governing = self._select_governing(
            transaction,
            case_id=case_id,
            effective_at=effective_at,
            known_at=known_at,
        )
        if not isinstance(governing, GoverningConfigurationFound):
            reason = (
                governing.reason
                if isinstance(governing, GoverningConfigurationConflict)
                else "GOVERNING CONFIGURATION NOT ESTABLISHED"
            )
            raise DomainRuleViolation(reason)
        if governing.configuration_version_id != configuration_version_id:
            raise DomainRuleViolation(
                "record is not bound to the exact governing Configuration Version"
            )

    def _validate_accountability(
        self,
        transaction: Increment3Transaction,
        *,
        assignment_version_id: RecordVersionId | None,
        mechanism: str | None,
        configuration_id: RecordId | None,
        effective_at: datetime,
        known_at: datetime,
    ) -> None:
        if not _accountability_present(assignment_version_id, mechanism):
            raise DomainRuleViolation("exactly one accountable assignment or mechanism is required")
        if mechanism:
            return
        if configuration_id is None:
            raise DomainRuleViolation(
                "assignment-based accountability requires exact Configuration context"
            )
        self._validate_accountable_provenance(
            transaction,
            assignment_version_id=assignment_version_id,
            mechanism=None,
            configuration_id=configuration_id,
            effective_at=effective_at,
            known_at=known_at,
        )

    def _validate_applicability_accountability(
        self,
        transaction: Increment3Transaction,
        *,
        value: EvidenceApplicabilityVersionInput,
        effective_at: datetime,
        known_at: datetime,
    ) -> None:
        if not _accountability_present(
            value.accountable_assignment_version_id, value.accountable_mechanism
        ):
            raise DomainRuleViolation("exactly one accountable assignment or mechanism is required")
        if value.accountable_mechanism:
            return
        assert value.accountable_assignment_version_id is not None
        assignment = transaction.role_assignment_detail(value.accountable_assignment_version_id)
        if assignment is None or not assignment.accountable:
            raise DomainRuleViolation(
                "accountable provenance must reference an accountable assignment"
            )

        targets: tuple[tuple[RoleTargetType, str], ...]
        if value.target_type in {
            ApplicabilityTargetType.MANAGED_CONFIGURATION_VERSION,
            ApplicabilityTargetType.VALUE_INPUT_VERSION,
            ApplicabilityTargetType.RISK_INPUT_VERSION,
        }:
            if value.configuration_id is None:
                raise DomainRuleViolation(
                    "Configuration target Applicability requires exact Configuration context"
                )
            targets = ((RoleTargetType.CONFIGURATION, str(value.configuration_id)),)
        else:
            authority = transaction.authority_applicability_context(
                target_type=value.target_type,
                target_id=value.target_id,
                target_version_id=value.target_version_id,
                case_id=value.case_id,
                configuration_version_id=value.configuration_version_id,
            )
            if authority is None:
                raise DomainRuleViolation("exact Authority target context is not established")
            if authority.configuration_id is not None:
                targets = ((RoleTargetType.CONFIGURATION, str(authority.configuration_id)),)
            elif authority.case_id is not None:
                targets = ((RoleTargetType.CASE, str(authority.case_id)),)
            else:
                targets = ((RoleTargetType.AUTHORITY_DOMAIN, authority.authority_scope),)

        accountable: set[RecordVersionId] = set()
        for target_type, target_id in targets:
            for version_id in self._current_role_versions(
                transaction,
                role=assignment.role,
                target_type=target_type,
                target_id=target_id,
                effective_at=effective_at,
                known_at=known_at,
            ):
                detail = transaction.role_assignment_detail(version_id)
                if detail is not None and detail.accountable:
                    accountable.add(version_id)
        if accountable != {value.accountable_assignment_version_id}:
            raise DomainRuleViolation(
                "vacant or conflicting target-context accountability blocks Applicability"
            )

    def commit_evidence(self, meta: CommandMeta, value: EvidenceVersionInput) -> CommandOutcome:
        if not value.source.strip() or not value.provenance or not value.content:
            raise DomainRuleViolation("Evidence source, provenance, and content are required")
        if (value.configuration_id is None) != (value.configuration_version_id is None):
            raise DomainRuleViolation(
                "Evidence Configuration identity/version must be supplied together"
            )
        if value.configuration_version_id is not None and (
            value.case_id is None or value.configuration_id is None
        ):
            raise DomainRuleViolation("Configuration-bound Evidence requires Case context")

        def project(base: object) -> None:
            transaction = cast("Increment3Transaction", base)
            if value.configuration_version_id and value.configuration_id and value.case_id:
                self._configuration_context(
                    transaction,
                    case_id=value.case_id,
                    configuration_id=value.configuration_id,
                    configuration_version_id=value.configuration_version_id,
                )
            transaction.add_evidence(
                evidence_id=value.evidence_id,
                version_id=value.version_id,
                case_id=value.case_id,
                configuration_id=value.configuration_id,
                configuration_version_id=value.configuration_version_id,
                classification=value.classification.value,
                source=value.source,
                provenance_json=json.dumps(value.provenance, sort_keys=True, separators=(",", ":")),
                observed_at_us=(
                    to_epoch_microseconds(require_utc(value.observed_as_of))
                    if value.observed_as_of
                    else None
                ),
                attention=value.attention.value,
            )
            for use_reference in value.affected_use_references:
                transaction.add_affected_use_reference(
                    source_version_id=value.version_id, use_reference=use_reference
                )

        content = dict(value.content)
        content.update(
            {
                "classification": value.classification.value,
                "source": value.source,
                "provenance": value.provenance,
                "case_id": str(value.case_id) if value.case_id else None,
                "configuration_id": str(value.configuration_id) if value.configuration_id else None,
                "configuration_version_id": (
                    str(value.configuration_version_id) if value.configuration_version_id else None
                ),
                "observed_as_of": value.observed_as_of.isoformat()
                if value.observed_as_of
                else None,
                "attention": value.attention.value,
                "affected_use_references": list(value.affected_use_references),
            }
        )
        return self._commit_version(
            meta=meta,
            record_id=value.evidence_id,
            version_id=value.version_id,
            family="evidence",
            scope=f"evidence:{value.evidence_id}",
            content=content,
            effective=value.effective,
            expected_version_id=value.expected_version_id,
            relationship_reason=value.relationship_reason,
            relationship_type=value.relationship_type,
            project=project,
            reason_outcome="INCREMENT_3_EVIDENCE_VALID",
        )

    def commit_authority_record(
        self, meta: CommandMeta, value: AuthorityVersionInput
    ) -> CommandOutcome:
        if (
            not all(
                item.strip()
                for item in (value.category, value.source, value.scope, value.requirement)
            )
            or not value.provenance
        ):
            raise DomainRuleViolation(
                "Authority category, source, scope, requirement, and provenance are required"
            )
        context_fields = (
            value.case_id,
            value.configuration_id,
            value.configuration_version_id,
        )
        if any(item is not None for item in context_fields) and not all(
            item is not None for item in context_fields
        ):
            raise DomainRuleViolation(
                "Authority Configuration context must supply exact Case, identity, and Version"
            )

        def project(base: object) -> None:
            transaction = cast("Increment3Transaction", base)
            if value.configuration_version_id and value.configuration_id and value.case_id:
                self._configuration_context(
                    transaction,
                    case_id=value.case_id,
                    configuration_id=value.configuration_id,
                    configuration_version_id=value.configuration_version_id,
                )
            for evidence_version_id in value.evidence_version_ids:
                evidence = transaction.get_version(evidence_version_id)
                if evidence is None or evidence.family != "evidence":
                    raise DomainRuleViolation(
                        "Authority Evidence links require exact Evidence Versions"
                    )
            transaction.add_authority_record(
                authority_id=value.authority_id,
                version_id=value.version_id,
                case_id=value.case_id,
                configuration_id=value.configuration_id,
                configuration_version_id=value.configuration_version_id,
                category=value.category,
                source=value.source,
                provenance_json=json.dumps(value.provenance, sort_keys=True, separators=(",", ":")),
                authority_scope=value.scope,
                requirement=value.requirement,
            )
            for evidence_version_id in value.evidence_version_ids:
                transaction.add_exact_evidence_link(
                    source_version_id=value.version_id,
                    evidence_version_id=evidence_version_id,
                    link_role="authority_basis",
                )

        content = dict(value.content)
        content.update(
            {
                "category": value.category,
                "source": value.source,
                "scope": value.scope,
                "requirement": value.requirement,
                "provenance": value.provenance,
                "case_id": str(value.case_id) if value.case_id else None,
                "configuration_id": str(value.configuration_id) if value.configuration_id else None,
                "configuration_version_id": (
                    str(value.configuration_version_id) if value.configuration_version_id else None
                ),
                "evidence_version_ids": [str(item) for item in value.evidence_version_ids],
            }
        )
        return self._commit_version(
            meta=meta,
            record_id=value.authority_id,
            version_id=value.version_id,
            family="authority-record",
            scope=f"authority:{value.authority_id}",
            content=content,
            effective=value.effective,
            expected_version_id=value.expected_version_id,
            relationship_reason=value.relationship_reason,
            relationship_type=value.relationship_type,
            project=project,
            reason_outcome="INCREMENT_3_AUTHORITY_RECORD_VALID",
        )

    def commit_authority_gap(
        self, meta: CommandMeta, value: AuthorityGapVersionInput
    ) -> CommandOutcome:
        if not all(
            item.strip()
            for item in (value.question_id, value.question, value.scope, value.rationale)
        ):
            raise DomainRuleViolation("Authority Gap question, scope, and rationale are required")
        if not value.provenance:
            raise DomainRuleViolation("Authority Gap provenance is required")

        def project(base: object) -> None:
            transaction = cast("Increment3Transaction", base)
            self._configuration_context(
                transaction,
                case_id=value.case_id,
                configuration_id=value.configuration_id,
                configuration_version_id=value.configuration_version_id,
            )
            for evidence_version_id in value.evidence_version_ids:
                evidence = transaction.get_version(evidence_version_id)
                if evidence is None or evidence.family != "evidence":
                    raise DomainRuleViolation("Authority Gap links require exact Evidence Versions")
            transaction.add_authority_gap(
                gap_id=value.gap_id,
                version_id=value.version_id,
                case_id=value.case_id,
                configuration_id=value.configuration_id,
                configuration_version_id=value.configuration_version_id,
                question_id=value.question_id,
                question=value.question,
                authority_scope=value.scope,
                rationale=value.rationale,
                provenance_json=json.dumps(value.provenance, sort_keys=True, separators=(",", ":")),
            )
            for evidence_version_id in value.evidence_version_ids:
                transaction.add_exact_evidence_link(
                    source_version_id=value.version_id,
                    evidence_version_id=evidence_version_id,
                    link_role="authority_gap_basis",
                )

        content: dict[str, JsonValue] = {
            "question_id": value.question_id,
            "question": value.question,
            "scope": value.scope,
            "rationale": value.rationale,
            "provenance": value.provenance,
            "case_id": str(value.case_id),
            "configuration_id": str(value.configuration_id),
            "configuration_version_id": str(value.configuration_version_id),
            "evidence_version_ids": [str(item) for item in value.evidence_version_ids],
        }
        return self._commit_version(
            meta=meta,
            record_id=value.gap_id,
            version_id=value.version_id,
            family="authority-gap",
            scope=f"case:{value.case_id}:authority-gap:{value.question_id}",
            content=content,
            effective=value.effective,
            expected_version_id=value.expected_version_id,
            relationship_reason=value.relationship_reason,
            relationship_type=value.relationship_type,
            project=project,
            reason_outcome="INCREMENT_3_AUTHORITY_GAP_VALID",
        )

    def commit_evidence_applicability(
        self, meta: CommandMeta, value: EvidenceApplicabilityVersionInput
    ) -> CommandOutcome:
        if not all(
            item.strip()
            for item in (value.target_id, value.purpose, value.assessed_scope, value.rationale)
        ):
            raise DomainRuleViolation(
                "Applicability target, purpose, scope, and rationale are required"
            )
        if (
            value.target_version_id is None
            and value.target_type is not ApplicabilityTargetType.AUTHORITY_GAP
        ):
            raise DomainRuleViolation(
                "versioned Increment 3 Applicability target requires an exact target Version"
            )
        context_fields = (
            value.case_id,
            value.configuration_id,
            value.configuration_version_id,
        )
        if any(item is not None for item in context_fields) and not all(
            item is not None for item in context_fields
        ):
            raise DomainRuleViolation(
                "Applicability Configuration context must supply exact Case, identity, and Version"
            )
        if value.outcome.value == "REFRESH_REQUIRED":
            raise DomainRuleViolation("REFRESH REQUIRED is not an Applicability outcome")
        if value.outcome.value in {"CONDITIONALLY_APPLICABLE", "PARTIALLY_APPLICABLE"} and (
            not value.conditions or not value.limitations
        ):
            raise DomainRuleViolation(
                "conditional/partial Applicability requires conditions and limitations"
            )

        recorded_at = self._clock.now()

        def project(base: object) -> None:
            transaction = cast("Increment3Transaction", base)
            evidence = transaction.get_version(value.evidence_version_id)
            if (
                evidence is None
                or evidence.family != "evidence"
                or evidence.record_id != value.evidence_id
            ):
                raise DomainRuleViolation(
                    "Applicability requires the exact Evidence identity/version"
                )
            if not transaction.actor_exists(value.assessor_actor_id):
                raise DomainRuleViolation("Applicability assessor must be an existing PAIM actor")
            if not transaction.exact_target_exists(
                target_type=value.target_type,
                target_id=value.target_id,
                target_version_id=value.target_version_id,
                case_id=value.case_id,
                configuration_version_id=value.configuration_version_id,
            ):
                raise DomainRuleViolation(
                    "Applicability target identity/version is not established"
                )
            if value.case_id and value.configuration_id and value.configuration_version_id:
                self._configuration_context(
                    transaction,
                    case_id=value.case_id,
                    configuration_id=value.configuration_id,
                    configuration_version_id=value.configuration_version_id,
                )
                target_input = transaction.analytical_input_detail(
                    cast("RecordVersionId", value.target_version_id)
                )
                if target_input is not None and (
                    target_input.case_id != value.case_id
                    or target_input.configuration_id != value.configuration_id
                    or target_input.configuration_version_id != value.configuration_version_id
                ):
                    raise DomainRuleViolation(
                        "Applicability context does not match the exact target Input Version"
                    )
                if value.target_type is ApplicabilityTargetType.MANAGED_CONFIGURATION_VERSION and (
                    str(value.configuration_id) != value.target_id
                    or value.configuration_version_id != value.target_version_id
                ):
                    raise DomainRuleViolation(
                        "Applicability context does not match the exact target "
                        "Configuration Version"
                    )
            self._validate_applicability_accountability(
                transaction,
                value=value,
                effective_at=value.effective.start,
                known_at=recorded_at,
            )
            for displaced in value.displaced_applicability_version_ids:
                displaced_detail = transaction.evidence_applicability_detail(displaced)
                if (
                    displaced_detail is None
                    or displaced_detail.evidence_version_id != value.evidence_version_id
                    or displaced_detail.target_type is not value.target_type
                    or displaced_detail.target_id != value.target_id
                    or displaced_detail.target_version_id != value.target_version_id
                    or displaced_detail.case_id != value.case_id
                    or displaced_detail.configuration_version_id != value.configuration_version_id
                    or displaced_detail.purpose != value.purpose
                    or displaced_detail.assessed_scope != value.assessed_scope
                ):
                    raise DomainRuleViolation(
                        "displaced Applicability is outside this exact assessment context"
                    )
            transaction.add_evidence_applicability(
                applicability_id=value.applicability_id,
                version_id=value.version_id,
                evidence_version_id=value.evidence_version_id,
                target_type=value.target_type.value,
                target_id=value.target_id,
                target_version_id=value.target_version_id,
                purpose=value.purpose,
                assessed_scope=value.assessed_scope,
                case_id=value.case_id,
                configuration_id=value.configuration_id,
                configuration_version_id=value.configuration_version_id,
                outcome=value.outcome.value,
                conditions_json=json.dumps(value.conditions, separators=(",", ":")),
                limitations_json=json.dumps(value.limitations, separators=(",", ":")),
                rationale=value.rationale,
                assessor_actor_id=value.assessor_actor_id,
                accountable_assignment_version_id=value.accountable_assignment_version_id,
                accountable_mechanism=value.accountable_mechanism,
            )
            for use_reference in value.affected_use_references:
                transaction.add_affected_use_reference(
                    source_version_id=value.version_id, use_reference=use_reference
                )

        def after_version(
            base: object, committed_at: datetime
        ) -> tuple[tuple[EventId, ...], tuple[RecordVersionId, ...]]:
            transaction = cast("Increment3Transaction", base)
            status_ids: list[EventId] = []
            for displaced in value.displaced_applicability_version_ids:
                status = StatusEvent(
                    event_id=EventId.new(),
                    target_version_id=displaced,
                    prior_status="finalized",
                    new_status="superseded",
                    recorded_at=committed_at,
                    effective_at=value.effective.start,
                    actor=meta.actor_id or meta.actor_resolution.value,
                    basis=value.rationale,
                )
                transaction.add_status_event(status)
                transaction.add_relationship(
                    VersionRelationship(
                        relationship_id=RelationshipId.new(),
                        source_version_id=displaced,
                        target_version_id=value.version_id,
                        relationship_type=RelationshipType.SUPERSESSION,
                        recorded_at=committed_at,
                        reason=value.rationale,
                    )
                )
                status_ids.append(status.event_id)
            return tuple(status_ids), value.displaced_applicability_version_ids

        content: dict[str, JsonValue] = {
            "evidence_id": str(value.evidence_id),
            "evidence_version_id": str(value.evidence_version_id),
            "target_type": value.target_type.value,
            "target_id": value.target_id,
            "target_version_id": str(value.target_version_id),
            "purpose": value.purpose,
            "assessed_scope": value.assessed_scope,
            "outcome": value.outcome.value,
            "conditions": list(value.conditions),
            "limitations": list(value.limitations),
            "rationale": value.rationale,
            "assessor_actor_id": str(value.assessor_actor_id),
            "accountable_assignment_version_id": (
                str(value.accountable_assignment_version_id)
                if value.accountable_assignment_version_id
                else None
            ),
            "accountable_mechanism": value.accountable_mechanism,
            "affected_use_references": list(value.affected_use_references),
            "displaced_applicability_version_ids": [
                str(item) for item in value.displaced_applicability_version_ids
            ],
        }
        return self._commit_version(
            meta=meta,
            record_id=value.applicability_id,
            version_id=value.version_id,
            family="evidence-applicability",
            scope=_applicability_scope(value),
            content=content,
            effective=value.effective,
            expected_version_id=value.expected_version_id,
            relationship_reason=value.relationship_reason,
            relationship_type=value.relationship_type,
            project=project,
            after_version=after_version,
            reason_outcome="INCREMENT_3_EVIDENCE_APPLICABILITY_VALID",
        )

    def _select_applicability(
        self,
        transaction: Increment3Transaction,
        *,
        evidence_version_id: RecordVersionId,
        target_type: ApplicabilityTargetType,
        target_id: str,
        target_version_id: RecordVersionId | None,
        purpose: str,
        assessed_scope: str,
        effective_at: datetime,
        known_at: datetime,
        case_id: RecordId | None = None,
        configuration_version_id: RecordVersionId | None = None,
    ) -> ApplicabilitySelection:
        if (
            target_type is ApplicabilityTargetType.AUTHORITY_GAP
            and target_version_id is None
            and (case_id is None or configuration_version_id is None)
        ):
            return ApplicabilityNotEstablished("AUTHORITY GAP QUESTION CONTEXT NOT ESTABLISHED")
        target_version = str(target_version_id) if target_version_id else "question"
        question_context = (
            f":case:{case_id}:configuration-version:{configuration_version_id}"
            if target_version_id is None
            else ""
        )
        scope = (
            f"evidence-version:{evidence_version_id}:target:{target_type.value}:{target_id}:"
            f"{target_version}{question_context}:purpose:{purpose}:scope:{assessed_scope}"
        )
        result = transaction.select_current(
            SelectionQuery(
                family="evidence-applicability",
                scope=scope,
                effective_at=effective_at,
                known_at=known_at,
            )
        )
        if isinstance(result, SelectionAbsent):
            return ApplicabilityNotEstablished()
        if isinstance(result, SelectionFound):
            return ApplicabilityFound(result.candidate.version_id)
        return ApplicabilityConflict(
            frozenset(candidate.version_id for candidate in result.candidates)
        )

    def select_evidence_applicability(
        self,
        *,
        evidence_version_id: RecordVersionId,
        target_type: ApplicabilityTargetType,
        target_id: str,
        target_version_id: RecordVersionId | None,
        purpose: str,
        assessed_scope: str,
        effective_at: datetime,
        known_at: datetime | None = None,
        case_id: RecordId | None = None,
        configuration_version_id: RecordVersionId | None = None,
    ) -> ApplicabilitySelection:
        effective_at = require_utc(effective_at)
        knowledge_time = require_utc(known_at or self._clock.now())
        with self._increment3_store.read_transaction() as transaction:
            return self._select_applicability(
                transaction,
                evidence_version_id=evidence_version_id,
                target_type=target_type,
                target_id=target_id,
                target_version_id=target_version_id,
                purpose=purpose,
                assessed_scope=assessed_scope,
                effective_at=effective_at,
                known_at=knowledge_time,
                case_id=case_id,
                configuration_version_id=configuration_version_id,
            )

    def commit_analytical_input(
        self, meta: CommandMeta, value: AnalyticalInputVersionInput
    ) -> CommandOutcome:
        if (
            not all(
                item.strip()
                for item in (value.purpose, value.finding, value.boundary, value.implication)
            )
            or not value.provenance
        ):
            raise DomainRuleViolation("Input five-part content and provenance are required")

        def project(base: object) -> None:
            transaction = cast("Increment3Transaction", base)
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
            for evidence_version_id in value.evidence_version_ids:
                evidence = transaction.get_version(evidence_version_id)
                if evidence is None or evidence.family != "evidence":
                    raise DomainRuleViolation("Input provenance requires exact Evidence Versions")
            transaction.add_analytical_input(
                input_id=value.input_id,
                version_id=value.version_id,
                lane=value.lane.value,
                case_id=value.case_id,
                configuration_id=value.configuration_id,
                configuration_version_id=value.configuration_version_id,
                purpose=value.purpose,
                finding=value.finding,
                boundary=value.boundary,
                uncertainties_json=json.dumps(value.uncertainties, separators=(",", ":")),
                implication=value.implication,
                provenance_json=json.dumps(value.provenance, sort_keys=True, separators=(",", ":")),
            )
            for evidence_version_id in value.evidence_version_ids:
                transaction.add_exact_evidence_link(
                    source_version_id=value.version_id,
                    evidence_version_id=evidence_version_id,
                    link_role="input_material_basis",
                )

        content: dict[str, JsonValue] = {
            "lane": value.lane.value,
            "case_id": str(value.case_id),
            "configuration_id": str(value.configuration_id),
            "configuration_version_id": str(value.configuration_version_id),
            "purpose": value.purpose,
            "finding": value.finding,
            "boundary": value.boundary,
            "uncertainties": list(value.uncertainties),
            "implication": value.implication,
            "provenance": value.provenance,
            "evidence_version_ids": [str(item) for item in value.evidence_version_ids],
        }
        return self._commit_version(
            meta=meta,
            record_id=value.input_id,
            version_id=value.version_id,
            family=f"{value.lane.value.casefold()}-input",
            scope=f"input:{value.input_id}",
            content=content,
            effective=value.effective,
            expected_version_id=value.expected_version_id,
            relationship_reason=value.relationship_reason,
            relationship_type=value.relationship_type,
            project=project,
            reason_outcome=f"INCREMENT_3_{value.lane.value}_INPUT_VALID",
        )

    def _commit_status(
        self,
        meta: CommandMeta,
        *,
        record_id: RecordId,
        version_id: RecordVersionId,
        family: str,
        scope: str,
        prior_status: str,
        new_status: str,
        effective_at: datetime,
        basis: str,
        reason: str,
    ) -> CommandOutcome:
        integrity_store = cast("IntegrityStore", self._increment3_store)
        return IntegrityApplicationService(integrity_store, self._clock).commit_status(
            CommitStatusCommand(
                command_id=meta.command_id,
                idempotency_scope=meta.idempotency_scope,
                idempotency_key=meta.idempotency_key,
                record_id=record_id,
                target_version_id=version_id,
                family=family,
                scope=scope,
                precondition_at=effective_at,
                prior_status=prior_status,
                new_status=new_status,
                effective_at=effective_at,
                basis=basis,
                principal_id=meta.principal_id,
                actor_id=meta.actor_id,
                actor_resolution=meta.actor_resolution,
                correlation_id=meta.correlation_id,
                causation_id=meta.causation_id,
                reason_outcomes=(reason,),
            )
        )

    def mark_input_ready(
        self,
        meta: CommandMeta,
        *,
        input_version_id: RecordVersionId,
        effective_at: datetime,
        rationale: str,
    ) -> CommandOutcome:
        with self._increment3_store.read_transaction() as transaction:
            detail = transaction.analytical_input_detail(input_version_id)
            if detail is None:
                raise DomainRuleViolation("ready event requires an exact Input Version")
            statuses = transaction.version_statuses(
                version_id=input_version_id,
                effective_at=effective_at,
                known_at=self._clock.now(),
            )
            if "ready" in statuses or "frozen" in statuses:
                raise DomainRuleViolation("Input is already ready or frozen")
        return self._commit_status(
            meta,
            record_id=detail.input_id,
            version_id=input_version_id,
            family=f"{detail.lane.value.casefold()}-input",
            scope=f"input:{detail.input_id}",
            prior_status="candidate",
            new_status="ready",
            effective_at=require_utc(effective_at),
            basis=rationale,
            reason="ANALYTICAL_READINESS_RECORDED",
        )

    def mark_evidence_attention(
        self,
        meta: CommandMeta,
        *,
        evidence_id: RecordId,
        evidence_version_id: RecordVersionId,
        attention: EvidenceAttention,
        effective_at: datetime,
        rationale: str,
    ) -> CommandOutcome:
        if attention is EvidenceAttention.CURRENT:
            raise DomainRuleViolation("attention command must record refresh-required or stale")
        return self._commit_status(
            meta,
            record_id=evidence_id,
            version_id=evidence_version_id,
            family="evidence",
            scope=f"evidence:{evidence_id}",
            prior_status="current",
            new_status=attention.value,
            effective_at=require_utc(effective_at),
            basis=rationale,
            reason="EVIDENCE_ATTENTION_RECORDED",
        )

    def commit_candidate_disposition(
        self, meta: CommandMeta, value: CandidateDispositionVersionInput
    ) -> CommandOutcome:
        if not value.rationale.strip():
            raise DomainRuleViolation("candidate disposition rationale is required")
        recorded_at = self._clock.now()

        def project(base: object) -> None:
            transaction = cast("Increment3Transaction", base)
            detail = transaction.analytical_input_detail(value.input_version_id)
            if (
                detail is None
                or detail.lane is not value.lane
                or detail.configuration_version_id != value.configuration_version_id
            ):
                raise DomainRuleViolation("disposition must bind the exact lane Input context")
            if _accountability_present(
                value.accountable_assignment_version_id, value.accountable_mechanism
            ):
                self._validate_accountability(
                    transaction,
                    assignment_version_id=value.accountable_assignment_version_id,
                    mechanism=value.accountable_mechanism,
                    configuration_id=detail.configuration_id,
                    effective_at=value.effective.start,
                    known_at=recorded_at,
                )
            transaction.add_candidate_disposition(
                disposition_id=value.disposition_id,
                version_id=value.version_id,
                input_version_id=value.input_version_id,
                lane=value.lane.value,
                configuration_version_id=value.configuration_version_id,
                use_context=value.use_context,
                purpose=value.purpose,
                disposition=value.disposition.value,
                rationale=value.rationale,
                accountable_assignment_version_id=value.accountable_assignment_version_id,
                accountable_mechanism=value.accountable_mechanism,
            )

        content: dict[str, JsonValue] = {
            "input_version_id": str(value.input_version_id),
            "lane": value.lane.value,
            "configuration_version_id": str(value.configuration_version_id),
            "use_context": value.use_context,
            "purpose": value.purpose,
            "disposition": value.disposition.value,
            "rationale": value.rationale,
        }
        return self._commit_version(
            meta=meta,
            record_id=value.disposition_id,
            version_id=value.version_id,
            family="candidate-disposition",
            scope=(
                f"input-version:{value.input_version_id}:use:{value.use_context}:"
                f"purpose:{value.purpose}"
            ),
            content=content,
            effective=value.effective,
            expected_version_id=value.expected_version_id,
            relationship_reason=value.relationship_reason,
            project=project,
            reason_outcome="INCREMENT_3_CANDIDATE_DISPOSITION_VALID",
        )

    def commit_lane_fitness(
        self, meta: CommandMeta, value: LaneFitnessVersionInput
    ) -> CommandOutcome:
        if not value.rationale.strip():
            raise DomainRuleViolation("lane fitness rationale is required")
        recorded_at = self._clock.now()

        def project(base: object) -> None:
            transaction = cast("Increment3Transaction", base)
            detail = transaction.analytical_input_detail(value.input_version_id)
            if (
                detail is None
                or detail.lane is not value.lane
                or detail.case_id != value.case_id
                or detail.configuration_id != value.configuration_id
                or detail.configuration_version_id != value.configuration_version_id
            ):
                raise DomainRuleViolation(
                    "fitness must bind the exact lane Input and Configuration"
                )
            self._validate_accountability(
                transaction,
                assignment_version_id=value.accountable_assignment_version_id,
                mechanism=value.accountable_mechanism,
                configuration_id=value.configuration_id,
                effective_at=value.effective.start,
                known_at=recorded_at,
            )
            blockers: list[str] = []
            for basis in value.material_evidence:
                applicability = transaction.evidence_applicability_detail(
                    basis.applicability_version_id
                )
                expected_target = (
                    ApplicabilityTargetType.VALUE_INPUT_VERSION
                    if value.lane is AnalyticalLane.VALUE
                    else ApplicabilityTargetType.RISK_INPUT_VERSION
                )
                if (
                    applicability is None
                    or applicability.evidence_version_id != basis.evidence_version_id
                    or applicability.target_type is not expected_target
                    or applicability.target_version_id != value.input_version_id
                    or applicability.target_id != str(detail.input_id)
                    or applicability.purpose != value.purpose
                ):
                    blockers.append("MATERIAL EVIDENCE APPLICABILITY NOT ESTABLISHED")
                    continue
                selected = self._select_applicability(
                    transaction,
                    evidence_version_id=basis.evidence_version_id,
                    target_type=applicability.target_type,
                    target_id=applicability.target_id,
                    target_version_id=value.input_version_id,
                    purpose=value.purpose,
                    assessed_scope=applicability.assessed_scope,
                    effective_at=value.effective.start,
                    known_at=recorded_at,
                )
                if not isinstance(selected, ApplicabilityFound) or (
                    selected.applicability_version_id != basis.applicability_version_id
                ):
                    blockers.append("MATERIAL EVIDENCE APPLICABILITY ABSENT OR CONFLICTING")
                    continue
                statuses = transaction.version_statuses(
                    version_id=basis.evidence_version_id,
                    effective_at=value.effective.start,
                    known_at=recorded_at,
                )
                initial_attention = transaction.evidence_attention(basis.evidence_version_id)
                if (
                    basis.required_support
                    and any(status in {"refresh_required", "stale"} for status in statuses)
                ) or (
                    basis.required_support and initial_attention in {"refresh_required", "stale"}
                ):
                    blockers.append("MATERIAL EVIDENCE REFRESH REQUIRED")
                if basis.required_support and applicability.outcome.value == "NOT_APPLICABLE":
                    blockers.append("MATERIAL EVIDENCE NOT APPLICABLE")
                if (
                    applicability.outcome.value
                    in {
                        "CONDITIONALLY_APPLICABLE",
                        "PARTIALLY_APPLICABLE",
                    }
                    and basis.claimed_scope != applicability.assessed_scope
                ):
                    blockers.append("MATERIAL EVIDENCE CLAIM EXCEEDS ASSESSED SCOPE")
                if applicability.outcome.value == "INDETERMINATE" and (
                    not value.indeterminate_treatment or value.decision_limiting
                ):
                    blockers.append("INDETERMINATE MATERIAL EVIDENCE NOT SUPPORTABLE")
            if blockers and value.outcome is FitnessOutcome.SUPPORTABLE:
                raise DomainRuleViolation("; ".join(sorted(set(blockers))))
            if value.outcome is FitnessOutcome.SUPPORTABLE and value.decision_limiting:
                raise DomainRuleViolation(
                    "decision-limiting lane uncertainty blocks supportability"
                )
            transaction.add_lane_fitness(
                fitness_id=value.fitness_id,
                version_id=value.version_id,
                lane=value.lane.value,
                input_version_id=value.input_version_id,
                case_id=value.case_id,
                configuration_id=value.configuration_id,
                configuration_version_id=value.configuration_version_id,
                use_context=value.use_context,
                purpose=value.purpose,
                outcome=value.outcome.value,
                rationale=value.rationale,
                indeterminate_treatment=value.indeterminate_treatment,
                decision_limiting=value.decision_limiting,
                accountable_assignment_version_id=value.accountable_assignment_version_id,
                accountable_mechanism=value.accountable_mechanism,
                material_evidence=value.material_evidence,
            )

        content: dict[str, JsonValue] = {
            "lane": value.lane.value,
            "input_version_id": str(value.input_version_id),
            "configuration_version_id": str(value.configuration_version_id),
            "use_context": value.use_context,
            "purpose": value.purpose,
            "outcome": value.outcome.value,
            "rationale": value.rationale,
            "indeterminate_treatment": value.indeterminate_treatment,
            "decision_limiting": value.decision_limiting,
            "material_evidence": [
                {
                    "evidence_version_id": str(item.evidence_version_id),
                    "applicability_version_id": str(item.applicability_version_id),
                    "role": item.role,
                    "required_support": item.required_support,
                    "claimed_scope": item.claimed_scope,
                }
                for item in value.material_evidence
            ],
        }
        return self._commit_version(
            meta=meta,
            record_id=value.fitness_id,
            version_id=value.version_id,
            family="lane-evidence-fitness",
            scope=(
                f"lane:{value.lane.value}:input-version:{value.input_version_id}:"
                f"use:{value.use_context}:purpose:{value.purpose}"
            ),
            content=content,
            effective=value.effective,
            expected_version_id=value.expected_version_id,
            relationship_reason=value.relationship_reason,
            project=project,
            reason_outcome="INCREMENT_3_LANE_EVIDENCE_FITNESS_VALID",
        )

    def commit_acceptance_selection(
        self, meta: CommandMeta, value: AcceptanceSelectionVersionInput
    ) -> CommandOutcome:
        if (
            not value.rationale.strip()
            or not value.use_context.strip()
            or not value.purpose.strip()
        ):
            raise DomainRuleViolation("Acceptance use, purpose, and rationale are required")
        recorded_at = self._clock.now()

        def project(base: object) -> None:
            transaction = cast("Increment3Transaction", base)
            input_detail = transaction.analytical_input_detail(value.input_version_id)
            if (
                input_detail is None
                or input_detail.input_id != value.input_id
                or input_detail.lane is not value.lane
                or input_detail.case_id != value.case_id
                or input_detail.configuration_id != value.configuration_id
                or input_detail.configuration_version_id != value.configuration_version_id
            ):
                raise DomainRuleViolation("Acceptance must bind the exact lane Input context")
            self._governing_context(
                transaction,
                case_id=value.case_id,
                configuration_version_id=value.configuration_version_id,
                effective_at=value.effective.start,
                known_at=recorded_at,
            )
            self._validate_accountability(
                transaction,
                assignment_version_id=value.accountable_assignment_version_id,
                mechanism=value.accountable_mechanism,
                configuration_id=value.configuration_id,
                effective_at=value.effective.start,
                known_at=recorded_at,
            )
            fitness = transaction.lane_fitness_detail(value.fitness_version_id)
            if (
                fitness is None
                or fitness.lane is not value.lane
                or fitness.input_version_id != value.input_version_id
                or fitness.configuration_version_id != value.configuration_version_id
                or fitness.use_context != value.use_context
                or fitness.purpose != value.purpose
                or fitness.outcome is not FitnessOutcome.SUPPORTABLE
                or fitness.decision_limiting
            ):
                raise DomainRuleViolation("exact supportable lane fitness is required")
            material_ids = frozenset(
                item.applicability_version_id
                for item in transaction.material_evidence_basis(value.fitness_version_id)
            )
            if material_ids != frozenset(value.material_applicability_version_ids):
                raise DomainRuleViolation(
                    "Acceptance must retain the exact material Applicability basis"
                )
            statuses = transaction.version_statuses(
                version_id=value.input_version_id,
                effective_at=value.effective.start,
                known_at=recorded_at,
            )
            if "frozen" not in statuses and "ready" not in statuses:
                raise DomainRuleViolation(
                    "analytical readiness is required before first acceptance"
                )
            if any(
                status in {"withdrawn", "superseded", "refresh_required"} for status in statuses
            ):
                raise DomainRuleViolation(
                    "withdrawn, superseded, or refresh-required Input is ineligible"
                )
            for candidate_version_id in transaction.analytical_input_versions(
                lane=value.lane.value,
                configuration_version_id=value.configuration_version_id,
                purpose=input_detail.purpose,
            ):
                if candidate_version_id == value.input_version_id:
                    continue
                candidate_statuses = transaction.version_statuses(
                    version_id=candidate_version_id,
                    effective_at=value.effective.start,
                    known_at=recorded_at,
                )
                if "ready" in candidate_statuses and not transaction.candidate_has_disposition(
                    input_version_id=candidate_version_id,
                    lane=value.lane.value,
                    configuration_version_id=value.configuration_version_id,
                    use_context=value.use_context,
                    purpose=value.purpose,
                    effective_at=value.effective.start,
                    known_at=recorded_at,
                ):
                    raise DomainRuleViolation(
                        "material ready competitors require explicit use-specific dispositions"
                    )
            for displaced in value.displaced_acceptance_version_ids:
                detail = transaction.acceptance_selection_detail(displaced)
                if (
                    detail is None
                    or detail.lane is not value.lane
                    or detail.configuration_version_id != value.configuration_version_id
                    or detail.use_context != value.use_context
                    or detail.purpose != value.purpose
                ):
                    raise DomainRuleViolation(
                        "displaced acceptance is outside this selection context"
                    )
            transaction.add_acceptance_selection(
                acceptance_id=value.acceptance_id,
                version_id=value.version_id,
                lane=value.lane.value,
                input_version_id=value.input_version_id,
                case_id=value.case_id,
                configuration_id=value.configuration_id,
                configuration_version_id=value.configuration_version_id,
                use_context=value.use_context,
                purpose=value.purpose,
                rationale=value.rationale,
                accountable_assignment_version_id=value.accountable_assignment_version_id,
                accountable_mechanism=value.accountable_mechanism,
                fitness_version_id=value.fitness_version_id,
            )

        def after_version(
            base: object, committed_at: datetime
        ) -> tuple[tuple[EventId, ...], tuple[RecordVersionId, ...]]:
            transaction = cast("Increment3Transaction", base)
            status_ids: list[EventId] = []
            affected: list[RecordVersionId] = []
            input_statuses = transaction.version_statuses(
                version_id=value.input_version_id,
                effective_at=value.effective.start,
                known_at=committed_at,
            )
            if "frozen" not in input_statuses:
                freeze = StatusEvent(
                    event_id=EventId.new(),
                    target_version_id=value.input_version_id,
                    prior_status="ready",
                    new_status="frozen",
                    recorded_at=committed_at,
                    effective_at=value.effective.start,
                    actor=meta.actor_id or meta.actor_resolution.value,
                    basis=f"atomic first acceptance {value.version_id}",
                )
                transaction.add_status_event(freeze)
                status_ids.append(freeze.event_id)
                affected.append(value.input_version_id)
            for displaced in value.displaced_acceptance_version_ids:
                status = StatusEvent(
                    event_id=EventId.new(),
                    target_version_id=displaced,
                    prior_status="selected",
                    new_status="superseded",
                    recorded_at=committed_at,
                    effective_at=value.effective.start,
                    actor=meta.actor_id or meta.actor_resolution.value,
                    basis=value.rationale,
                )
                transaction.add_status_event(status)
                transaction.add_relationship(
                    VersionRelationship(
                        relationship_id=RelationshipId.new(),
                        source_version_id=displaced,
                        target_version_id=value.version_id,
                        relationship_type=RelationshipType.SUPERSESSION,
                        recorded_at=committed_at,
                        reason=value.rationale,
                    )
                )
                status_ids.append(status.event_id)
                affected.append(displaced)
            return tuple(status_ids), tuple(affected)

        content: dict[str, JsonValue] = {
            "lane": value.lane.value,
            "input_id": str(value.input_id),
            "input_version_id": str(value.input_version_id),
            "case_id": str(value.case_id),
            "configuration_id": str(value.configuration_id),
            "configuration_version_id": str(value.configuration_version_id),
            "use_context": value.use_context,
            "purpose": value.purpose,
            "outcome": "SELECTED",
            "rationale": value.rationale,
            "fitness_version_id": str(value.fitness_version_id),
            "material_applicability_version_ids": [
                str(item) for item in value.material_applicability_version_ids
            ],
            "displaced_acceptance_version_ids": [
                str(item) for item in value.displaced_acceptance_version_ids
            ],
        }
        return self._commit_version(
            meta=meta,
            record_id=value.acceptance_id,
            version_id=value.version_id,
            family="input-acceptance-selection",
            scope=_selection_scope(
                lane=value.lane,
                configuration_version_id=value.configuration_version_id,
                use_context=value.use_context,
                purpose=value.purpose,
            ),
            content=content,
            effective=value.effective,
            expected_version_id=value.expected_version_id,
            relationship_reason=value.relationship_reason,
            project=project,
            after_version=after_version,
            reason_outcome="INCREMENT_3_INPUT_ACCEPTANCE_SELECTION_VALID",
        )

    def _eligible_acceptance_candidates(
        self,
        transaction: Increment3Transaction,
        *,
        lane: AnalyticalLane,
        configuration_version_id: RecordVersionId,
        use_context: str,
        purpose: str,
        effective_at: datetime,
        known_at: datetime,
    ) -> tuple[tuple[SelectionCandidate, AcceptanceSelectionDetail], ...]:
        result = transaction.select_current(
            SelectionQuery(
                family="input-acceptance-selection",
                scope=_selection_scope(
                    lane=lane,
                    configuration_version_id=configuration_version_id,
                    use_context=use_context,
                    purpose=purpose,
                ),
                effective_at=effective_at,
                known_at=known_at,
            )
        )
        candidates: tuple[SelectionCandidate, ...]
        if isinstance(result, SelectionAbsent):
            candidates = ()
        elif isinstance(result, SelectionFound):
            candidates = (result.candidate,)
        else:
            candidates = tuple(result.candidates)
        eligible: list[tuple[SelectionCandidate, AcceptanceSelectionDetail]] = []
        for candidate in candidates:
            detail = transaction.acceptance_selection_detail(candidate.version_id)
            if detail is None:
                continue
            acceptance_statuses = transaction.version_statuses(
                version_id=candidate.version_id,
                effective_at=effective_at,
                known_at=known_at,
            )
            input_statuses = transaction.version_statuses(
                version_id=detail.input_version_id,
                effective_at=effective_at,
                known_at=known_at,
            )
            if any(
                status in {"withdrawn", "rejected_for_use", "superseded"}
                for status in acceptance_statuses
            ) or any(
                status in {"withdrawn", "superseded", "refresh_required"}
                for status in input_statuses
            ):
                continue
            if "frozen" not in input_statuses:
                continue
            fitness = transaction.lane_fitness_detail(detail.fitness_version_id)
            if (
                fitness is None
                or fitness.outcome is not FitnessOutcome.SUPPORTABLE
                or fitness.decision_limiting
            ):
                continue
            prospective_basis_valid = True
            for basis in transaction.material_evidence_basis(detail.fitness_version_id):
                applicability = transaction.evidence_applicability_detail(
                    basis.applicability_version_id
                )
                if (
                    applicability is None
                    or applicability.target_version_id != detail.input_version_id
                ):
                    prospective_basis_valid = False
                    break
                current = self._select_applicability(
                    transaction,
                    evidence_version_id=basis.evidence_version_id,
                    target_type=applicability.target_type,
                    target_id=applicability.target_id,
                    target_version_id=detail.input_version_id,
                    purpose=applicability.purpose,
                    assessed_scope=applicability.assessed_scope,
                    effective_at=effective_at,
                    known_at=known_at,
                )
                evidence_statuses = transaction.version_statuses(
                    version_id=basis.evidence_version_id,
                    effective_at=effective_at,
                    known_at=known_at,
                )
                if (
                    not isinstance(current, ApplicabilityFound)
                    or current.applicability_version_id != basis.applicability_version_id
                    or (
                        basis.required_support
                        and (
                            transaction.evidence_attention(basis.evidence_version_id)
                            in {"refresh_required", "stale"}
                            or any(
                                status in {"refresh_required", "stale"}
                                for status in evidence_statuses
                            )
                        )
                    )
                ):
                    prospective_basis_valid = False
                    break
            if not prospective_basis_valid:
                continue
            eligible.append((candidate, detail))
        return tuple(eligible)

    def _select_input(
        self,
        transaction: Increment3Transaction,
        *,
        lane: AnalyticalLane,
        configuration_version_id: RecordVersionId,
        use_context: str,
        purpose: str,
        effective_at: datetime,
        known_at: datetime,
    ) -> InputSelection:
        eligible = self._eligible_acceptance_candidates(
            transaction,
            lane=lane,
            configuration_version_id=configuration_version_id,
            use_context=use_context,
            purpose=purpose,
            effective_at=effective_at,
            known_at=known_at,
        )
        if not eligible:
            return InputSelectionNotEstablished()
        if len(eligible) == 1:
            candidate, detail = eligible[0]
            return InputSelectionFound(detail.input_version_id, candidate.version_id)
        return InputSelectionConflict(
            acceptance_version_ids=frozenset(candidate.version_id for candidate, _ in eligible),
            input_version_ids=frozenset(detail.input_version_id for _, detail in eligible),
        )

    def select_input(
        self,
        *,
        lane: AnalyticalLane,
        configuration_version_id: RecordVersionId,
        use_context: str,
        purpose: str,
        effective_at: datetime,
        known_at: datetime | None = None,
    ) -> InputSelection:
        effective_at = require_utc(effective_at)
        knowledge_time = require_utc(known_at or self._clock.now())
        with self._increment3_store.read_transaction() as transaction:
            return self._select_input(
                transaction,
                lane=lane,
                configuration_version_id=configuration_version_id,
                use_context=use_context,
                purpose=purpose,
                effective_at=effective_at,
                known_at=knowledge_time,
            )

    def change_input_eligibility(
        self,
        meta: CommandMeta,
        *,
        input_version_id: RecordVersionId,
        new_status: str,
        effective_at: datetime,
        rationale: str,
    ) -> CommandOutcome:
        if new_status not in {"withdrawn", "superseded", "refresh_required"}:
            raise DomainRuleViolation("unsupported prospective Input status")
        with self._increment3_store.read_transaction() as transaction:
            detail = transaction.analytical_input_detail(input_version_id)
            if detail is None:
                raise DomainRuleViolation("Input Version is not established")
        return self._commit_status(
            meta,
            record_id=detail.input_id,
            version_id=input_version_id,
            family=f"{detail.lane.value.casefold()}-input",
            scope=f"input:{detail.input_id}",
            prior_status="frozen",
            new_status=new_status,
            effective_at=require_utc(effective_at),
            basis=rationale,
            reason="INPUT_PROSPECTIVE_ELIGIBILITY_CHANGED",
        )

    def change_acceptance_eligibility(
        self,
        meta: CommandMeta,
        *,
        acceptance_version_id: RecordVersionId,
        new_status: str,
        effective_at: datetime,
        rationale: str,
    ) -> CommandOutcome:
        if new_status not in {"withdrawn", "rejected_for_use", "superseded"}:
            raise DomainRuleViolation("unsupported Acceptance disposition status")
        with self._increment3_store.read_transaction() as transaction:
            detail = transaction.acceptance_selection_detail(acceptance_version_id)
            if detail is None:
                raise DomainRuleViolation("Acceptance/Selection Version is not established")
        return self._commit_status(
            meta,
            record_id=detail.acceptance_id,
            version_id=acceptance_version_id,
            family="input-acceptance-selection",
            scope=_selection_scope(
                lane=detail.lane,
                configuration_version_id=detail.configuration_version_id,
                use_context=detail.use_context,
                purpose=detail.purpose,
            ),
            prior_status="selected",
            new_status=new_status,
            effective_at=require_utc(effective_at),
            basis=rationale,
            reason="ACCEPTANCE_PROSPECTIVE_ELIGIBILITY_CHANGED",
        )

    def analytical_handoff_readiness(
        self,
        *,
        case_id: RecordId,
        use_context: str,
        purpose: str,
        effective_at: datetime,
        known_at: datetime | None = None,
    ) -> AnalyticalHandoffReadiness:
        effective_at = require_utc(effective_at)
        knowledge_time = require_utc(known_at or self._clock.now())
        diagnostics: list[str] = []
        with self._increment3_store.read_transaction() as transaction:
            governing = self._select_governing(
                transaction,
                case_id=case_id,
                effective_at=effective_at,
                known_at=knowledge_time,
            )
            if not isinstance(governing, GoverningConfigurationFound):
                diagnostics.append(
                    getattr(governing, "reason", "GOVERNING CONFIGURATION NOT ESTABLISHED")
                )
                absent = InputSelectionNotEstablished()
                return AnalyticalHandoffReadiness(
                    False, None, absent, absent, tuple(diagnostics), ()
                )
            value = self._select_input(
                transaction,
                lane=AnalyticalLane.VALUE,
                configuration_version_id=governing.configuration_version_id,
                use_context=use_context,
                purpose=purpose,
                effective_at=effective_at,
                known_at=knowledge_time,
            )
            risk = self._select_input(
                transaction,
                lane=AnalyticalLane.RISK,
                configuration_version_id=governing.configuration_version_id,
                use_context=use_context,
                purpose=purpose,
                effective_at=effective_at,
                known_at=knowledge_time,
            )
            if not isinstance(value, InputSelectionFound):
                diagnostics.append(value.reason)
            if not isinstance(risk, InputSelectionFound):
                diagnostics.append(risk.reason)
            gaps = transaction.current_authority_gap_versions(
                case_id=case_id,
                configuration_version_id=governing.configuration_version_id,
                effective_at=effective_at,
                known_at=knowledge_time,
            )
            if gaps:
                diagnostics.append("AUTHORITY GAPS PRESERVED FOR FUTURE INTEGRATION")
            return AnalyticalHandoffReadiness(
                eligible=isinstance(value, InputSelectionFound)
                and isinstance(risk, InputSelectionFound),
                configuration_version_id=governing.configuration_version_id,
                value_selection=value,
                risk_selection=risk,
                diagnostics=tuple(diagnostics),
                authority_gap_version_ids=gaps,
            )
