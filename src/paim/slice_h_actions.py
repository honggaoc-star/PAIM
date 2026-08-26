"""Bounded production adapter for Slice-H contextual practitioner actions.

The adapter reconstructs command identity and exact governed context from persisted
prospective facts.  Browser fields contain only the practitioner's substantive
judgment; PAIM identities never come from an ordinary form.
"""

from __future__ import annotations

import json
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, cast

from paim.assessment_review import AssessmentLane
from paim.case_continuity.service import ContinuityAccessPolicy, ContinuityTransaction
from paim.integrity import RecordId, RecordVersionId
from paim.integrity.records import FinalizedRecordVersion
from paim.integrity.selection import SelectionFound, SelectionQuery
from paim.integrity.semantics import (
    ContextMemberKind,
    ExactContextMember,
    ExactContextSet,
)
from paim.responsibility.models import ObligationKind


class SliceHActionStore(Protocol):
    def read_transaction(self) -> AbstractContextManager[ContinuityTransaction]: ...

    def m1b_versions(
        self,
        *,
        case_id: RecordId,
        visible_configuration_ids: frozenset[RecordId],
    ) -> tuple[FinalizedRecordVersion, ...]: ...


@dataclass(frozen=True, slots=True)
class SliceHActionContext:
    """Access-safe exact inputs for one current Responsibility action."""

    case_id: RecordId
    configuration_version_id: RecordVersionId
    context: ExactContextSet
    obligation: ObligationKind
    responsibility_version_id: RecordVersionId
    assignment_version_id: RecordVersionId
    authority_source_version_id: RecordVersionId
    authority_identity: str | None
    decision_use: str
    bounded_scope: str
    information_basis_version_ids: tuple[RecordVersionId, ...]
    current_assessment_version_id: RecordVersionId | None
    current_readiness_version_id: RecordVersionId | None
    current_adequacy_version_id: RecordVersionId | None
    current_reliance_version_id: RecordVersionId | None
    reliance_candidate_version_ids: tuple[RecordVersionId, ...]
    reliance_candidate_labels: tuple[str, ...]
    reliance_candidate_information_basis: tuple[tuple[RecordVersionId, ...], ...]
    current_integration_version_id: RecordVersionId | None
    current_decision_version_id: RecordVersionId | None
    current_decision_status: str | None
    review_origin_version_ids: tuple[RecordVersionId, ...]
    review_focus: tuple[str, ...]
    current_review_episode_version_id: RecordVersionId | None
    current_confirmation_version_id: RecordVersionId | None
    source_version_ids: tuple[RecordVersionId, ...]

    @property
    def lane(self) -> AssessmentLane | None:
        if "VALUE" in self.obligation.value:
            return AssessmentLane.VALUE
        if "RISK" in self.obligation.value:
            return AssessmentLane.RISK
        return None


class SliceHActionContextResolver:
    """Resolve one exact action without composing before source authorization."""

    def __init__(self, store: SliceHActionStore, access: ContinuityAccessPolicy) -> None:
        self._store = store
        self._access = access

    def resolve(
        self,
        *,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        responsibility_version_id: RecordVersionId,
        effective_at: datetime,
        known_at: datetime,
    ) -> SliceHActionContext:
        with self._store.read_transaction() as tx:
            responsibility = self._exact_current_row(
                tx,
                "responsibility_versions",
                responsibility_version_id,
                effective_at,
                known_at,
            )
            if responsibility["owning_case_id"] != str(case_id):
                raise ValueError("Responsibility does not belong to the requested Case")
            responsibility_source = tx.get_version(responsibility_version_id)
            if responsibility_source is None:
                raise ValueError("Responsibility source is unavailable")
            context = self._context(tx, str(responsibility["context_digest"]))
            configuration_version_id = RecordVersionId.parse(
                next(
                    member.identity
                    for member in context.members
                    if member.slot == "configuration_version"
                    and member.kind is ContextMemberKind.VERSION
                )
            )
            obligation = ObligationKind(str(responsibility["obligation_kind"]))
            assignments = self._current_assignments(
                tx,
                responsibility,
                actor_id,
                effective_at,
                known_at,
            )
            if len(assignments) != 1:
                raise ValueError("one exact accountable assignment is not established")
            assignment = assignments[0]
            assignment_version_id = RecordVersionId.parse(str(assignment["version_id"]))
            basis_id = RecordVersionId.parse(str(assignment["assignment_basis_version_id"]))
            basis = self._exact_current_row(
                tx, "assignment_basis_versions", basis_id, effective_at, known_at
            )
            authority_id = RecordVersionId.parse(str(basis["basis_source_version_id"]))
            authority_identity: str | None = None
            required_authority_action = {
                ObligationKind.COMPLETE_VALUE_RISK_INTEGRATION: "INTEGRATE_VALUE_RISK",
                ObligationKind.AUTHORIZE_MANAGEMENT_DECISION: "AUTHORIZE_DECISION",
                ObligationKind.CONFIRM_MANAGEMENT_DECISION: "CONFIRM_DECISION",
            }.get(obligation)
            if required_authority_action is not None:
                applicability_rows = tx.projection_rows(
                    "evidence_applicability_versions",
                    configuration_version_id=str(configuration_version_id),
                )
                configuration_ids = {
                    RecordId.parse(str(row["configuration_id"])) for row in applicability_rows
                }
                if len(configuration_ids) != 1:
                    raise ValueError("governing Configuration context is unavailable")
                authorities = self._store.m1b_versions(
                    case_id=case_id,
                    visible_configuration_ids=frozenset(configuration_ids),
                )
                candidates: list[RecordVersionId] = []
                for source in authorities:
                    if source.family != "authority-record":
                        continue
                    authority = source.content.get("prospective_substantive_authority")
                    if not isinstance(authority, dict):
                        continue
                    actions = authority.get("allowed_actions")
                    cases = authority.get("allowed_case_ids")
                    contexts = authority.get("context_digest")
                    if (
                        authority.get("actor_id") == str(actor_id)
                        and isinstance(actions, list)
                        and required_authority_action in actions
                        and isinstance(cases, list)
                        and str(case_id) in cases
                        and contexts == context.digest
                    ):
                        selected = tx.select_current(
                            SelectionQuery(
                                source.family,
                                source.scope,
                                effective_at,
                                known_at,
                                source.record_id,
                            )
                        )
                        if (
                            isinstance(selected, SelectionFound)
                            and selected.candidate.version_id == source.version_id
                        ):
                            candidates.append(source.version_id)
                if len(candidates) != 1:
                    raise ValueError("one exact substantive authority source is not established")
                authority_id = candidates[0]
                if obligation is ObligationKind.AUTHORIZE_MANAGEMENT_DECISION:
                    authority_source = tx.get_version(authority_id)
                    authority = (
                        authority_source.content.get("prospective_substantive_authority")
                        if authority_source is not None
                        else None
                    )
                    source_actor = (
                        authority.get("actor_id") if isinstance(authority, dict) else None
                    )
                    if not isinstance(source_actor, str) or not source_actor.strip():
                        raise ValueError(
                            "the authoritative Decision authority identity is unavailable"
                        )
                    authority_identity = source_actor
            content = responsibility_source.content
            decision_use = str(
                content.get("use_discriminator")
                or self._literal(context, "bounded_use")
                or "bounded Case decision"
            )
            bounded_scope = str(
                content.get("scope_discriminator")
                or self._literal(context, "bounded_use")
                or "exact bounded Case scope"
            )
            source_ids: set[RecordVersionId] = {
                responsibility_version_id,
                assignment_version_id,
                basis_id,
                authority_id,
                configuration_version_id,
                *(
                    RecordVersionId.parse(member.identity)
                    for member in context.members
                    if member.kind is ContextMemberKind.VERSION
                ),
            }
            information = self._information_basis(
                tx,
                principal_id,
                actor_id,
                case_id,
                configuration_version_id,
                effective_at,
                known_at,
            )
            source_ids.update(information)
            lane = (
                AssessmentLane.VALUE
                if "VALUE" in obligation.value
                else AssessmentLane.RISK
                if "RISK" in obligation.value
                else None
            )
            assessment = readiness = adequacy = reliance = None
            reliance_candidates: tuple[RecordVersionId, ...] = ()
            reliance_labels: tuple[str, ...] = ()
            reliance_information: tuple[tuple[RecordVersionId, ...], ...] = ()
            if lane is not None:
                if obligation in {
                    ObligationKind.DESIGNATE_VALUE_ASSESSMENT_RELIANCE,
                    ObligationKind.DESIGNATE_RISK_ASSESSMENT_RELIANCE,
                }:
                    candidate_rows = self._context_current_rows(
                        tx,
                        tx.projection_rows(
                            "assessment_candidate_versions",
                            case_id=str(case_id),
                            configuration_version_id=str(configuration_version_id),
                            lane=lane.value,
                            decision_use=decision_use,
                        ),
                        effective_at,
                        known_at,
                    )
                    candidate_details: list[
                        tuple[
                            RecordVersionId,
                            RecordVersionId,
                            RecordVersionId,
                            str,
                            tuple[RecordVersionId, ...],
                        ]
                    ] = []
                    for candidate_row in candidate_rows:
                        candidate_id = RecordVersionId.parse(str(candidate_row["version_id"]))
                        readiness_rows = self._context_current_rows(
                            tx,
                            tx.projection_rows(
                                "assessment_readiness_versions",
                                assessment_version_id=str(candidate_id),
                            ),
                            effective_at,
                            known_at,
                        )
                        adequacy_rows = self._context_current_rows(
                            tx,
                            tx.projection_rows(
                                "assessment_adequacy_versions",
                                assessment_version_id=str(candidate_id),
                                outcome="ADEQUATE",
                            ),
                            effective_at,
                            known_at,
                        )
                        if len(readiness_rows) != 1 or len(adequacy_rows) != 1:
                            continue
                        candidate_source = tx.get_version(candidate_id)
                        if candidate_source is None:
                            continue
                        label = str(
                            candidate_source.content.get("finding", "Bounded assessment candidate")
                        )
                        candidate_details.append(
                            (
                                candidate_id,
                                RecordVersionId.parse(str(readiness_rows[0]["version_id"])),
                                RecordVersionId.parse(str(adequacy_rows[0]["version_id"])),
                                label,
                                json_version_ids(
                                    candidate_row["information_basis_version_ids_json"]
                                ),
                            )
                        )
                    candidate_details.sort(key=lambda value: str(value[0]))
                    reliance_candidates = tuple(value[0] for value in candidate_details)
                    reliance_labels = tuple(value[3] for value in candidate_details)
                    reliance_information = tuple(value[4] for value in candidate_details)
                    for (
                        candidate_id,
                        readiness_id,
                        adequacy_id,
                        _label,
                        candidate_information,
                    ) in candidate_details:
                        source_ids.update(
                            (candidate_id, readiness_id, adequacy_id, *candidate_information)
                        )
                    if len(candidate_details) == 1:
                        assessment, readiness, adequacy, _label, _candidate_information = (
                            candidate_details[0]
                        )
                else:
                    assessment = self._one_current_version(
                        tx,
                        "assessment_candidate_versions",
                        case_id,
                        configuration_version_id,
                        effective_at,
                        known_at,
                        lane=lane.value,
                        decision_use=decision_use,
                    )
                    readiness = self._one_current_version(
                        tx,
                        "assessment_readiness_versions",
                        case_id,
                        configuration_version_id,
                        effective_at,
                        known_at,
                        lane=lane.value,
                        decision_use=decision_use,
                    )
                    adequacy = self._one_current_version(
                        tx,
                        "assessment_adequacy_versions",
                        case_id,
                        configuration_version_id,
                        effective_at,
                        known_at,
                        lane=lane.value,
                        decision_use=decision_use,
                    )
                reliance = self._one_current_version(
                    tx,
                    "assessment_reliance_versions",
                    case_id,
                    configuration_version_id,
                    effective_at,
                    known_at,
                    lane=lane.value,
                    decision_use=decision_use,
                )
                source_ids.update(
                    value for value in (assessment, readiness, adequacy, reliance) if value
                )
            integration = self._one_current_version(
                tx,
                "prospective_integration_versions",
                case_id,
                configuration_version_id,
                effective_at,
                known_at,
                decision_use=decision_use,
            )
            decision = self._one_current_version(
                tx,
                "prospective_decision_versions",
                case_id,
                configuration_version_id,
                effective_at,
                known_at,
                decision_use=decision_use,
            )
            decision_status = None
            if decision is not None:
                rows = tx.projection_rows("prospective_decision_versions", version_id=str(decision))
                decision_status = str(rows[0]["status"]) if len(rows) == 1 else None
            source_ids.update(value for value in (integration, decision) if value)
            if obligation in {
                ObligationKind.COMPLETE_VALUE_RISK_INTEGRATION,
                ObligationKind.PROPOSE_MANAGEMENT_DECISION,
                ObligationKind.AUTHORIZE_MANAGEMENT_DECISION,
                ObligationKind.CONFIRM_MANAGEMENT_DECISION,
                ObligationKind.PLAN_NEXT_REVIEW,
                ObligationKind.BEGIN_CONTINUING_REVIEW,
                ObligationKind.COMPLETE_CONTINUING_REVIEW,
            }:
                for analytical_lane in (AssessmentLane.VALUE, AssessmentLane.RISK):
                    for table in (
                        "assessment_candidate_versions",
                        "assessment_readiness_versions",
                        "assessment_adequacy_versions",
                        "assessment_reliance_versions",
                    ):
                        lane_source_id = self._one_current_version(
                            tx,
                            table,
                            case_id,
                            configuration_version_id,
                            effective_at,
                            known_at,
                            lane=analytical_lane.value,
                            decision_use=decision_use,
                        )
                        if lane_source_id is not None:
                            source_ids.add(lane_source_id)
            if integration is not None:
                integration_rows = tx.projection_rows(
                    "prospective_integration_versions", version_id=str(integration)
                )
                if len(integration_rows) != 1:
                    raise ValueError("exact Integration basis is unavailable")
                integration_row = integration_rows[0]
                for field in (
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
                ):
                    if integration_row.get(field):
                        source_ids.add(RecordVersionId.parse(str(integration_row[field])))
                source_ids.update(json_version_ids(integration_row["value_information_basis_json"]))
                source_ids.update(json_version_ids(integration_row["risk_information_basis_json"]))
            if decision is not None:
                decision_rows = tx.projection_rows(
                    "prospective_decision_versions", version_id=str(decision)
                )
                if len(decision_rows) != 1:
                    raise ValueError("exact Decision basis is unavailable")
                for field in (
                    "integration_version_id",
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
                    "proposal_version_id",
                    "predecessor_version_id",
                ):
                    if decision_rows[0].get(field):
                        source_ids.add(RecordVersionId.parse(str(decision_rows[0][field])))
            review_origins: tuple[RecordVersionId, ...] = ()
            review_focus: tuple[str, ...] = ()
            episode = None
            confirmation = None
            if obligation is ObligationKind.BEGIN_CONTINUING_REVIEW:
                events = self._context_current_rows(
                    tx,
                    tx.projection_rows(
                        "review_attention_event_versions",
                        case_id=str(case_id),
                        configuration_version_id=str(configuration_version_id),
                        context_digest=context.digest,
                    ),
                    effective_at,
                    known_at,
                )
                addressed = {
                    str(link["result_version_id"])
                    for completed in tx.projection_rows(
                        "review_episode_versions",
                        case_id=str(case_id),
                        configuration_version_id=str(configuration_version_id),
                        context_digest=context.digest,
                        status="COMPLETED",
                    )
                    for link in tx.projection_rows(
                        "review_episode_result_links",
                        episode_version_id=str(completed["version_id"]),
                        link_role="ADDRESSED_EVENT_ORIGIN",
                    )
                }
                events = tuple(row for row in events if str(row["version_id"]) not in addressed)
                if len(events) != 1:
                    raise ValueError("one exact visible review origin is not established")
                event = events[0]
                review_origins = (RecordVersionId.parse(str(event["version_id"])),)
                review_focus = tuple(json.loads(cast(str, event["affected_focus_json"])))
                source_ids.update(review_origins)
                source_ids.add(RecordVersionId.parse(str(event["event_source_version_id"])))
            if obligation is ObligationKind.COMPLETE_CONTINUING_REVIEW:
                episodes = self._context_current_rows(
                    tx,
                    tx.projection_rows(
                        "review_episode_versions",
                        case_id=str(case_id),
                        configuration_version_id=str(configuration_version_id),
                        context_digest=context.digest,
                        status="OPEN",
                    ),
                    effective_at,
                    known_at,
                )
                if len(episodes) != 1:
                    raise ValueError("one exact open focused review is not established")
                episode_row = episodes[0]
                episode = RecordVersionId.parse(str(episode_row["version_id"]))
                review_origins = json_version_ids(episode_row["origin_version_ids_json"])
                review_focus = tuple(json.loads(cast(str, episode_row["focused_scope_json"])))
                source_ids.update(
                    {
                        episode,
                        *review_origins,
                        RecordVersionId.parse(str(episode_row["prior_decision_version_id"])),
                        RecordVersionId.parse(str(episode_row["prior_integration_version_id"])),
                        RecordVersionId.parse(str(episode_row["prior_value_reliance_version_id"])),
                        RecordVersionId.parse(str(episode_row["prior_risk_reliance_version_id"])),
                    }
                )
                confirmations = self._context_current_rows(
                    tx,
                    tx.projection_rows(
                        "prospective_decision_confirmation_versions",
                        case_id=str(case_id),
                        configuration_version_id=str(configuration_version_id),
                        decision_version_id=str(decision),
                    ),
                    effective_at,
                    known_at,
                )
                if len(confirmations) != 1:
                    raise ValueError("one exact unchanged-Decision confirmation is not established")
                confirmation = RecordVersionId.parse(str(confirmations[0]["version_id"]))
                source_ids.add(confirmation)
            for source_id in tuple(source_ids):
                assignment_rows = tx.projection_rows(
                    "responsibility_assignment_versions", version_id=str(source_id)
                )
                if len(assignment_rows) == 1:
                    assignment_basis = RecordVersionId.parse(
                        str(assignment_rows[0]["assignment_basis_version_id"])
                    )
                    source_ids.add(assignment_basis)
                    basis_rows = tx.projection_rows(
                        "assignment_basis_versions", version_id=str(assignment_basis)
                    )
                    if len(basis_rows) != 1:
                        raise ValueError("exact Assignment Basis is unavailable")
                    source_ids.add(
                        RecordVersionId.parse(str(basis_rows[0]["basis_source_version_id"]))
                    )
            hidden = tuple(
                source_id
                for source_id in source_ids
                if not self._visible(
                    tx,
                    principal_id,
                    actor_id,
                    case_id,
                    source_id,
                    effective_at,
                    known_at,
                )
            )
            if hidden:
                raise ValueError("exact governed context is not safely available")
            return SliceHActionContext(
                case_id,
                configuration_version_id,
                context,
                obligation,
                responsibility_version_id,
                assignment_version_id,
                authority_id,
                authority_identity,
                decision_use,
                bounded_scope,
                information,
                assessment,
                readiness,
                adequacy,
                reliance,
                reliance_candidates,
                reliance_labels,
                reliance_information,
                integration,
                decision,
                decision_status,
                review_origins,
                review_focus,
                episode,
                confirmation,
                tuple(sorted(source_ids, key=str)),
            )

    @staticmethod
    def _literal(context: ExactContextSet, slot: str) -> str | None:
        return next(
            (
                member.identity
                for member in context.members
                if member.slot == slot and member.kind is ContextMemberKind.LITERAL
            ),
            None,
        )

    @staticmethod
    def _context(tx: ContinuityTransaction, digest: str) -> ExactContextSet:
        rows = tx.projection_rows("exact_context_members", context_digest=digest)
        context = ExactContextSet.create(
            tuple(
                ExactContextMember(
                    str(row["slot"]),
                    ContextMemberKind(str(row["member_kind"])),
                    str(row["identity"]),
                )
                for row in rows
            )
        )
        if context.digest != digest:
            raise ValueError("persisted exact context digest mismatch")
        return context

    @staticmethod
    def _exact_current_row(
        tx: ContinuityTransaction,
        table: str,
        version_id: RecordVersionId,
        effective_at: datetime,
        known_at: datetime,
    ) -> dict[str, object]:
        rows = tx.projection_rows(table, version_id=str(version_id))
        source = tx.get_version(version_id)
        if len(rows) != 1 or source is None:
            raise ValueError("exact governed source is unavailable")
        selected = tx.select_current(
            SelectionQuery(
                source.family,
                source.scope,
                effective_at,
                known_at,
                source.record_id,
            )
        )
        if not isinstance(selected, SelectionFound) or selected.candidate.version_id != version_id:
            raise ValueError("exact governed source is stale; no retarget permitted")
        return rows[0]

    @staticmethod
    def _context_current_rows(
        tx: ContinuityTransaction,
        rows: tuple[dict[str, object], ...],
        effective_at: datetime,
        known_at: datetime,
    ) -> tuple[dict[str, object], ...]:
        result: list[dict[str, object]] = []
        for row in rows:
            version_id = RecordVersionId.parse(str(row["version_id"]))
            source = tx.get_version(version_id)
            if source is None:
                continue
            selected = tx.select_current(
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

    def _current_assignments(
        self,
        tx: ContinuityTransaction,
        responsibility: dict[str, object],
        actor_id: RecordId,
        effective_at: datetime,
        known_at: datetime,
    ) -> tuple[dict[str, object], ...]:
        rows = tx.projection_rows(
            "responsibility_assignment_versions",
            signature_digest=str(responsibility["signature_digest"]),
            actor_id=str(actor_id),
            state="ASSIGNED",
        )
        return self._context_current_rows(tx, rows, effective_at, known_at)

    def _information_basis(
        self,
        tx: ContinuityTransaction,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        configuration_version_id: RecordVersionId,
        effective_at: datetime,
        known_at: datetime,
    ) -> tuple[RecordVersionId, ...]:
        rows = tx.projection_rows(
            "evidence_applicability_versions",
            configuration_version_id=str(configuration_version_id),
            outcome="APPLICABLE",
        )
        current = self._context_current_rows(tx, rows, effective_at, known_at)
        result: set[RecordVersionId] = set()
        for row in current:
            applicability = RecordVersionId.parse(str(row["version_id"]))
            evidence = RecordVersionId.parse(str(row["evidence_version_id"]))
            if all(
                self._visible(
                    tx,
                    principal_id,
                    actor_id,
                    case_id,
                    source,
                    effective_at,
                    known_at,
                )
                for source in (applicability, evidence)
            ):
                result.update((applicability, evidence))
        return tuple(sorted(result, key=str))

    def _one_current_version(
        self,
        tx: ContinuityTransaction,
        table: str,
        case_id: RecordId,
        configuration_version_id: RecordVersionId,
        effective_at: datetime,
        known_at: datetime,
        **equals: object,
    ) -> RecordVersionId | None:
        rows = tx.projection_rows(
            table,
            case_id=str(case_id),
            configuration_version_id=str(configuration_version_id),
            **equals,
        )
        current = self._context_current_rows(tx, rows, effective_at, known_at)
        if not current:
            return None
        if len(current) != 1:
            raise ValueError("current governed context is conflicting")
        return RecordVersionId.parse(str(current[0]["version_id"]))

    def _visible(
        self,
        tx: ContinuityTransaction,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        source_id: RecordVersionId,
        effective_at: datetime,
        known_at: datetime,
    ) -> bool:
        source = tx.get_version(source_id)
        return source is not None and self._access.authorize(
            principal_id=principal_id,
            actor_id=str(actor_id),
            action="source.read",
            case_id=case_id,
            source_version_id=source_id,
            source_family=source.family,
            effective_at=effective_at,
            known_at=known_at,
            write=False,
        )


def json_version_ids(value: object) -> tuple[RecordVersionId, ...]:
    """Parse a persisted exact-ID array without broad semantic substitution."""

    parsed = json.loads(cast(str, value))
    if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
        raise ValueError("persisted exact Version array is invalid")
    return tuple(RecordVersionId.parse(item) for item in parsed)


__all__ = ["SliceHActionContext", "SliceHActionContextResolver", "json_version_ids"]
