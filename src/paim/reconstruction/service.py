"""Access-first, dual-time Slice-G reconstruction over exact authoritative facts."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from typing import cast

from paim.case_continuity.service import (
    ContinuityAccessPolicy,
    ContinuityStore,
    ContinuityTransaction,
)
from paim.integrity.ids import RecordId, RecordVersionId
from paim.integrity.records import FinalizedRecordVersion
from paim.integrity.selection import SelectionConflict, SelectionFound, SelectionQuery
from paim.integrity.time import FixedClock, require_utc
from paim.quantitative_claims import (
    ComparisonState,
    QuantitativeClaimAccessDenied,
    QuantitativeClaimConflict,
    QuantitativeClaimService,
)
from paim.reconstruction.models import (
    CaseHistoryView,
    CaseTimeline,
    DecisionAuditNarrative,
    LanePosition,
    ManagementPosition,
    PositionChange,
    PositionComponent,
    QuantitativePairChange,
    ReconstructionState,
    SourceManifest,
    SourceReference,
    ThenNowComparison,
    TimelineItem,
)


class ReconstructionAccessDenied(RuntimeError):
    def __init__(self) -> None:
        super().__init__("software access not established")


_FAMILY_TABLES = {
    "case-continuity-status": "case_continuity_status_versions",
    "governing-configuration": "governing_configuration_designations",
    "assessment-candidate": "assessment_candidate_versions",
    "assessment-readiness": "assessment_readiness_versions",
    "assessment-adequacy": "assessment_adequacy_versions",
    "assessment-reliance": "assessment_reliance_versions",
    "prospective-integration": "prospective_integration_versions",
    "prospective-decision": "prospective_decision_versions",
    "prospective-decision-authorization": "prospective_decision_authorization_versions",
    "prospective-decision-confirmation": "prospective_decision_confirmation_versions",
    "planned-review-point": "planned_review_point_versions",
    "required-review-constraint": "required_review_constraint_versions",
    "review-attention-event": "review_attention_event_versions",
    "review-episode": "review_episode_versions",
    "quantitative-claim": "quantitative_claim_versions",
    "quantitative-comparability": "quantitative_comparability_versions",
    "responsibility": "responsibility_versions",
    "responsibility-assignment": "responsibility_assignment_versions",
    "assignment-basis": "assignment_basis_versions",
    "case-work": "case_work_versions",
}

_TIMELINE_TABLES = (
    ("case-continuity-status", "case_continuity_status_versions"),
    ("governing-configuration", "governing_configuration_designations"),
    ("assessment-candidate", "assessment_candidate_versions"),
    ("assessment-adequacy", "assessment_adequacy_versions"),
    ("assessment-reliance", "assessment_reliance_versions"),
    ("prospective-integration", "prospective_integration_versions"),
    ("prospective-decision", "prospective_decision_versions"),
    ("planned-review-point", "planned_review_point_versions"),
    ("required-review-constraint", "required_review_constraint_versions"),
    ("review-attention-event", "review_attention_event_versions"),
    ("review-episode", "review_episode_versions"),
    ("quantitative-claim", "quantitative_claim_versions"),
    ("quantitative-comparability", "quantitative_comparability_versions"),
)


class ReconstructionService:
    """Rebuild management positions; never persist a presentation or snapshot truth."""

    def __init__(self, store: ContinuityStore, access_policy: ContinuityAccessPolicy) -> None:
        self._store = store
        self._access = access_policy

    def decision_time_position(
        self,
        *,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        decision_version_id: RecordVersionId,
        effective_at: datetime,
        known_at: datetime,
    ) -> ManagementPosition:
        """Reconstruct the exact basis bound to one exact authorized Decision Version."""

        self._validate_cutoffs(effective_at, known_at)
        self._require_case_access(principal_id, actor_id, case_id)
        with self._store.read_transaction() as tx:
            row = self._one_row(tx, "prospective_decision_versions", decision_version_id)
            version = tx.get_version(decision_version_id)
            if (
                row is None
                or version is None
                or row.get("case_id") != str(case_id)
                or row.get("status") != "AUTHORIZED"
                or version.recorded_at > known_at
                or not version.effective.contains(effective_at)
            ):
                return self._empty_position(
                    ReconstructionState.ABSENT, case_id, effective_at, known_at
                )
            if not self._source_visible(
                tx,
                principal_id,
                actor_id,
                case_id,
                decision_version_id,
                effective_at,
                known_at,
            ):
                return self._empty_position(
                    ReconstructionState.NOT_SAFELY_AVAILABLE,
                    case_id,
                    effective_at,
                    known_at,
                )
            closure = self._source_closure(tx, decision_version_id)
            if closure is None:
                visible = self._manifest(tx, {decision_version_id}, effective_at, known_at)
                return ManagementPosition(
                    ReconstructionState.MALFORMED,
                    case_id,
                    effective_at,
                    known_at,
                    ReconstructionState.MALFORMED,
                    ReconstructionState.MALFORMED,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    visible,
                )
            if not self._closure_knowable(tx, closure, known_at):
                return ManagementPosition(
                    ReconstructionState.MALFORMED,
                    case_id,
                    effective_at,
                    known_at,
                    ReconstructionState.MALFORMED,
                    ReconstructionState.MALFORMED,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    self._manifest(tx, {decision_version_id}, effective_at, known_at),
                )
            if not self._closure_visible(
                tx, principal_id, actor_id, case_id, closure, effective_at, known_at
            ):
                return self._empty_position(
                    ReconstructionState.NOT_SAFELY_AVAILABLE,
                    case_id,
                    effective_at,
                    known_at,
                )
            return self._compose_bound_position(
                tx,
                principal_id,
                actor_id,
                case_id,
                row,
                closure,
                effective_at,
                known_at,
            )

    def current_position(
        self,
        *,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        effective_at: datetime,
        known_at: datetime,
    ) -> ManagementPosition:
        """Compose current visible facts using canonical record/scope selectors."""

        self._validate_cutoffs(effective_at, known_at)
        self._require_case_access(principal_id, actor_id, case_id)
        with self._store.read_transaction() as tx:
            continuity = self._current_component(
                tx,
                principal_id,
                actor_id,
                case_id,
                "case-continuity-status",
                tx.projection_rows("case_continuity_status_versions", case_id=str(case_id)),
                effective_at,
                known_at,
            )
            governing = self._current_component(
                tx,
                principal_id,
                actor_id,
                case_id,
                "governing-configuration",
                tx.projection_rows("governing_configuration_designations", case_id=str(case_id)),
                effective_at,
                known_at,
            )
            if self._unsafe(continuity, governing):
                return self._empty_position(
                    ReconstructionState.NOT_SAFELY_AVAILABLE,
                    case_id,
                    effective_at,
                    known_at,
                )
            configuration_id = (
                governing.version_ids[0]
                if governing.state is ReconstructionState.AVAILABLE and governing.version_ids
                else None
            )
            configuration_version_id: RecordVersionId | None = None
            if configuration_id is not None:
                designation = self._one_row(
                    tx, "governing_configuration_designations", configuration_id
                )
                if designation is not None:
                    configuration_version_id = RecordVersionId.parse(
                        str(designation["configuration_version_id"])
                    )
                    governing = PositionComponent(
                        governing.state,
                        (configuration_version_id,),
                        governing.source_manifest,
                    )
            lane_seed = self._empty_component(ReconstructionState.ABSENT, effective_at, known_at)
            value_resolution, risk_resolution = self._current_lanes(
                tx,
                principal_id,
                actor_id,
                case_id,
                configuration_version_id,
                lane_seed,
                effective_at,
                known_at,
            )
            value_state = (
                ReconstructionState.AVAILABLE
                if isinstance(value_resolution, LanePosition)
                else value_resolution.state
            )
            risk_state = (
                ReconstructionState.AVAILABLE
                if isinstance(risk_resolution, LanePosition)
                else risk_resolution.state
            )
            if value_state in {
                ReconstructionState.NOT_SAFELY_AVAILABLE,
                ReconstructionState.MALFORMED,
            } or risk_state in {
                ReconstructionState.NOT_SAFELY_AVAILABLE,
                ReconstructionState.MALFORMED,
            }:
                return self._empty_position(
                    ReconstructionState.NOT_SAFELY_AVAILABLE,
                    case_id,
                    effective_at,
                    known_at,
                )
            integration = self._current_integration_component(
                tx,
                principal_id,
                actor_id,
                case_id,
                configuration_version_id,
                value_resolution if isinstance(value_resolution, LanePosition) else None,
                risk_resolution if isinstance(risk_resolution, LanePosition) else None,
                effective_at,
                known_at,
            )
            decision = self._current_decision_component(
                tx,
                principal_id,
                actor_id,
                case_id,
                configuration_version_id,
                integration,
                effective_at,
                known_at,
            )
            review = self._review_component(
                tx,
                principal_id,
                actor_id,
                case_id,
                configuration_version_id,
                effective_at,
                known_at,
            )
            quantitative = self._quantitative_component(
                tx,
                principal_id,
                actor_id,
                case_id,
                configuration_version_id,
                effective_at,
                known_at,
            )
            basis_components = (
                continuity,
                governing,
                integration,
                decision,
                review,
                quantitative,
            )
            if any(
                item.state is ReconstructionState.NOT_SAFELY_AVAILABLE for item in basis_components
            ):
                return self._empty_position(
                    ReconstructionState.NOT_SAFELY_AVAILABLE,
                    case_id,
                    effective_at,
                    known_at,
                )
            linked_ids = {
                version_id
                for component in basis_components
                for version_id in component.source_manifest.version_ids
            }
            responsibility_work = self._linked_responsibility_work_component(
                tx, linked_ids, effective_at, known_at
            )
            components = (*basis_components, responsibility_work)
            manifest_ids: set[RecordVersionId] = set()
            for component in components:
                manifest_ids.update(component.source_manifest.version_ids)
            for lane in (value_resolution, risk_resolution):
                manifest_ids.update(lane.source_manifest.version_ids)
            state = (
                ReconstructionState.CONFLICT
                if any(item.state is ReconstructionState.CONFLICT for item in components)
                or value_state is ReconstructionState.CONFLICT
                or risk_state is ReconstructionState.CONFLICT
                else ReconstructionState.AVAILABLE
            )
            return ManagementPosition(
                state,
                case_id,
                effective_at,
                known_at,
                value_state,
                risk_state,
                continuity,
                governing,
                value_resolution if isinstance(value_resolution, LanePosition) else None,
                risk_resolution if isinstance(risk_resolution, LanePosition) else None,
                integration,
                decision,
                review,
                quantitative,
                responsibility_work,
                self._manifest(tx, manifest_ids, effective_at, known_at),
                reader_principal_id=principal_id,
                reader_actor_id=actor_id,
            )

    def compare(self, prior: ManagementPosition, current: ManagementPosition) -> ThenNowComparison:
        """Mechanically compare exact identities; never infer quality, cause, or required action."""

        if prior.case_id != current.case_id:
            raise ValueError("then-versus-now positions must belong to the same Case")
        same_reader = (
            bool(prior.reader_principal_id)
            and prior.reader_principal_id == current.reader_principal_id
            and prior.reader_actor_id is not None
            and prior.reader_actor_id == current.reader_actor_id
        )
        if not same_reader:
            state = ReconstructionState.NOT_SAFELY_AVAILABLE
        elif prior.state is ReconstructionState.MALFORMED:
            state = ReconstructionState.MALFORMED
        elif (
            prior.state is not ReconstructionState.AVAILABLE
            or current.state is not ReconstructionState.AVAILABLE
        ):
            state = ReconstructionState.NOT_SAFELY_AVAILABLE
        else:
            state = ReconstructionState.AVAILABLE
        if state is not ReconstructionState.AVAILABLE:
            return ThenNowComparison(
                state,
                None,
                None,
                (),
                self._blank_manifest(prior.effective_at, prior.known_at),
                self._blank_manifest(current.effective_at, current.known_at),
            )
        changes: list[PositionChange] = []
        for name in (
            "governing_configuration",
            "value",
            "risk",
            "integration",
            "decision",
            "review",
            "quantitative_claims",
            "responsibility_work",
        ):
            prior_ids = self._component_ids(prior, name)
            current_ids = self._component_ids(current, name)
            if name == "quantitative_claims":
                pair_changes = self._quantitative_pair_changes(prior, current)
                source_set_changed = prior_ids != current_ids
                changes.append(
                    PositionChange(
                        name,
                        prior_ids,
                        current_ids,
                        source_set_changed and bool(pair_changes),
                        source_set_changed=source_set_changed,
                        quantitative_comparison_established=bool(pair_changes),
                        quantitative_pair_changes=pair_changes,
                    )
                )
            else:
                changes.append(self._change(name, prior_ids, current_ids))
        return ThenNowComparison(
            state,
            prior,
            current,
            tuple(changes),
            prior.source_manifest,
            current.source_manifest,
        )

    def _quantitative_pair_changes(
        self, prior: ManagementPosition, current: ManagementPosition
    ) -> tuple[QuantitativePairChange, ...]:
        """Reuse Slice-F exact pair comparison at the current side's explicit cutoff."""

        principal_id = current.reader_principal_id
        actor_id = current.reader_actor_id
        if not principal_id or actor_id is None:
            return ()
        prior_ids = self._quantitative_claim_ids(prior)
        current_ids = self._quantitative_claim_ids(current)
        if not prior_ids or not current_ids:
            return ()
        quantitative = QuantitativeClaimService(
            self._store,
            FixedClock(current.known_at),
            self._access,
        )
        results: list[QuantitativePairChange] = []
        for left_id in prior_ids:
            for right_id in current_ids:
                if left_id == right_id:
                    continue
                try:
                    comparison = quantitative.compare(
                        principal_id=principal_id,
                        actor_id=actor_id,
                        case_id=current.case_id,
                        left_claim_version_id=left_id,
                        right_claim_version_id=right_id,
                        effective_at=current.effective_at,
                        known_at=current.known_at,
                    )
                except (QuantitativeClaimAccessDenied, QuantitativeClaimConflict):
                    continue
                if (
                    comparison.state is not ComparisonState.COMPARABLE
                    or comparison.comparability_version_id is None
                ):
                    continue
                with self._store.read_transaction() as tx:
                    closure = self._source_closure(tx, comparison.comparability_version_id)
                    if closure is None or not self._closure_knowable(tx, closure, current.known_at):
                        continue
                    if not self._closure_visible(
                        tx,
                        principal_id,
                        actor_id,
                        current.case_id,
                        closure,
                        current.effective_at,
                        current.known_at,
                    ):
                        continue
                    manifest = self._manifest(tx, closure, current.effective_at, current.known_at)
                results.append(
                    QuantitativePairChange(
                        left_id,
                        right_id,
                        comparison.comparability_version_id,
                        comparison.difference,
                        comparison.ratio,
                        comparison.percentage_change,
                        manifest,
                    )
                )
        return tuple(
            sorted(
                results,
                key=lambda result: (
                    str(result.left_claim_version_id),
                    str(result.right_claim_version_id),
                    str(result.comparability_version_id),
                ),
            )
        )

    @staticmethod
    def _quantitative_claim_ids(position: ManagementPosition) -> tuple[RecordVersionId, ...]:
        if position.quantitative_claims is None:
            return ()
        claim_ids = {
            source.version_id
            for source in position.quantitative_claims.source_manifest.sources
            if source.family == "quantitative-claim"
            and source.version_id in position.quantitative_claims.version_ids
        }
        return tuple(sorted(claim_ids, key=str))

    def decision_audit(
        self,
        *,
        principal_id: str,
        actor_id: RecordId,
        prior: ManagementPosition,
        current: ManagementPosition,
    ) -> DecisionAuditNarrative:
        """Explain one visible Decision from recorded facts without a new governed conclusion."""

        comparison = self.compare(prior, current)
        if (
            comparison.state is not ReconstructionState.AVAILABLE
            or prior.decision is None
            or len(prior.decision.version_ids) != 1
        ):
            return DecisionAuditNarrative(
                state=comparison.state,
                decision_version_id=None,
                decision_effective_at=None,
                decision_recorded_at=None,
                action=None,
                rationale=None,
                conditions=(),
                accountable_actor_id=None,
                responsibility_version_id=None,
                assignment_version_id=None,
                assignment_basis_version_id=None,
                authority_source_version_id=None,
                integration_version_id=None,
                value_reliance_version_id=None,
                risk_reliance_version_id=None,
                successor_decision_version_ids=(),
                continuing_review_version_ids=(),
                subsequent_visible_changes=(),
                source_manifest=self._blank_manifest(prior.effective_at, prior.known_at),
            )
        decision_id = prior.decision.version_ids[0]
        with self._store.read_transaction() as tx:
            row = self._one_row(tx, "prospective_decision_versions", decision_id)
            version = tx.get_version(decision_id)
            if row is None or version is None:
                return self._malformed_audit(prior)
            assignment_id = RecordVersionId.parse(str(row["assignment_version_id"]))
            assignments = tx.projection_rows(
                "responsibility_assignment_versions", version_id=str(assignment_id)
            )
            if len(assignments) != 1:
                return self._malformed_audit(prior)
            actor = RecordId.parse(str(assignments[0]["actor_id"]))
            assignment_basis = RecordVersionId.parse(
                str(assignments[0]["assignment_basis_version_id"])
            )
            successors: list[RecordVersionId] = []
            successor_source_ids: set[RecordVersionId] = set()
            for candidate in tx.projection_rows(
                "prospective_decision_versions", case_id=str(prior.case_id)
            ):
                if candidate.get("predecessor_version_id") != str(decision_id):
                    continue
                candidate_id = RecordVersionId.parse(str(candidate["version_id"]))
                candidate_version = tx.get_version(candidate_id)
                closure = self._source_closure(tx, candidate_id)
                if (
                    candidate_version is None
                    or not self._has_prospective_semantics(tx, candidate_id)
                    or not candidate_version.effective.contains(current.effective_at)
                    or closure is None
                    or not self._closure_knowable(tx, closure, current.known_at)
                    or not self._closure_visible(
                        tx,
                        principal_id,
                        actor_id,
                        prior.case_id,
                        closure,
                        current.effective_at,
                        current.known_at,
                    )
                ):
                    continue
                successors.append(candidate_id)
                successor_source_ids.update(closure)
            content = version.content
            conditions = content.get("conditions") or content.get("conditions_and_limits") or []
            return DecisionAuditNarrative(
                state=ReconstructionState.AVAILABLE,
                decision_version_id=decision_id,
                decision_effective_at=version.effective.start,
                decision_recorded_at=version.recorded_at,
                action=self._optional_text(content.get("proposed_action")),
                rationale=self._optional_text(content.get("rationale")),
                conditions=(
                    tuple(str(value) for value in conditions)
                    if isinstance(conditions, list)
                    else ()
                ),
                accountable_actor_id=actor,
                responsibility_version_id=RecordVersionId.parse(
                    str(row["responsibility_version_id"])
                ),
                assignment_version_id=assignment_id,
                assignment_basis_version_id=assignment_basis,
                authority_source_version_id=RecordVersionId.parse(
                    str(row["authority_source_version_id"])
                ),
                integration_version_id=RecordVersionId.parse(str(row["integration_version_id"])),
                value_reliance_version_id=RecordVersionId.parse(
                    str(row["value_reliance_version_id"])
                ),
                risk_reliance_version_id=RecordVersionId.parse(
                    str(row["risk_reliance_version_id"])
                ),
                successor_decision_version_ids=tuple(sorted(successors, key=str)),
                continuing_review_version_ids=(
                    current.review.version_ids if current.review is not None else ()
                ),
                subsequent_visible_changes=tuple(
                    change for change in comparison.changes if change.changed
                ),
                source_manifest=self._merge_manifests(
                    self._merge_manifests(prior.source_manifest, current.source_manifest),
                    self._manifest(
                        tx,
                        successor_source_ids,
                        current.effective_at,
                        current.known_at,
                    ),
                ),
            )

    def timeline(
        self,
        *,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        effective_at: datetime,
        known_at: datetime,
    ) -> CaseTimeline:
        """Return fully visible history; hidden items leave no count or placeholder."""

        self._validate_cutoffs(effective_at, known_at)
        self._require_case_access(principal_id, actor_id, case_id)
        items: list[TimelineItem] = []
        manifest_ids: set[RecordVersionId] = set()
        with self._store.read_transaction() as tx:
            for family, table in _TIMELINE_TABLES:
                for row in tx.projection_rows(table, case_id=str(case_id)):
                    version_id = RecordVersionId.parse(str(row["version_id"]))
                    version = tx.get_version(version_id)
                    if (
                        version is None
                        or version.recorded_at > known_at
                        or version.effective.start > effective_at
                        or not self._has_prospective_semantics(tx, version_id)
                    ):
                        continue
                    closure = self._source_closure(tx, version_id)
                    if closure is None or not self._closure_visible(
                        tx,
                        principal_id,
                        actor_id,
                        case_id,
                        closure,
                        effective_at,
                        known_at,
                    ):
                        continue
                    item_manifest = self._manifest(tx, closure, effective_at, known_at)
                    manifest_ids.update(closure)
                    action, rationale, conditions = self._timeline_management_detail(
                        family, version
                    )
                    items.append(
                        TimelineItem(
                            family,
                            version.record_id,
                            version.version_id,
                            version.effective.start,
                            version.recorded_at,
                            self._timeline_description(family, version),
                            item_manifest,
                            action,
                            rationale,
                            conditions,
                        )
                    )
            items.sort(key=lambda item: (item.effective_at, item.recorded_at, str(item.version_id)))
            return CaseTimeline(
                ReconstructionState.AVAILABLE,
                case_id,
                effective_at,
                known_at,
                tuple(items),
                self._manifest(tx, manifest_ids, effective_at, known_at),
            )

    def case_history(
        self,
        *,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        decision_version_id: RecordVersionId,
        prior_effective_at: datetime,
        prior_known_at: datetime,
        current_effective_at: datetime,
        current_known_at: datetime,
    ) -> CaseHistoryView:
        prior = self.decision_time_position(
            principal_id=principal_id,
            actor_id=actor_id,
            case_id=case_id,
            decision_version_id=decision_version_id,
            effective_at=prior_effective_at,
            known_at=prior_known_at,
        )
        current = self.current_position(
            principal_id=principal_id,
            actor_id=actor_id,
            case_id=case_id,
            effective_at=current_effective_at,
            known_at=current_known_at,
        )
        comparison = self.compare(prior, current)
        audit = self.decision_audit(
            principal_id=principal_id,
            actor_id=actor_id,
            prior=prior,
            current=current,
        )
        timeline = self.timeline(
            principal_id=principal_id,
            actor_id=actor_id,
            case_id=case_id,
            effective_at=current_effective_at,
            known_at=current_known_at,
        )
        return CaseHistoryView(current, prior, comparison, audit, timeline)

    def _compose_bound_position(
        self,
        tx: ContinuityTransaction,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        decision: dict[str, object],
        decision_closure: set[RecordVersionId],
        effective_at: datetime,
        known_at: datetime,
    ) -> ManagementPosition:
        configuration_id = RecordVersionId.parse(str(decision["configuration_version_id"]))
        integration_id = RecordVersionId.parse(str(decision["integration_version_id"]))
        integration_closure = self._source_closure(tx, integration_id)
        if integration_closure is None:
            return self._empty_position(
                ReconstructionState.MALFORMED, case_id, effective_at, known_at
            )
        integration_row = self._one_row(tx, "prospective_integration_versions", integration_id)
        if integration_row is None:
            return self._empty_position(
                ReconstructionState.MALFORMED, case_id, effective_at, known_at
            )
        value = self._lane_from_row(tx, integration_row, "value", effective_at, known_at)
        risk = self._lane_from_row(tx, integration_row, "risk", effective_at, known_at)
        if value is None or risk is None:
            return self._empty_position(
                ReconstructionState.MALFORMED, case_id, effective_at, known_at
            )
        continuity = self._current_component(
            tx,
            principal_id,
            actor_id,
            case_id,
            "case-continuity-status",
            tx.projection_rows("case_continuity_status_versions", case_id=str(case_id)),
            effective_at,
            known_at,
        )
        governing = self._component_from_exact(
            tx,
            principal_id,
            actor_id,
            case_id,
            (configuration_id,),
            effective_at,
            known_at,
        )
        review = self._review_component(
            tx,
            principal_id,
            actor_id,
            case_id,
            configuration_id,
            effective_at,
            known_at,
        )
        quantitative = self._quantitative_component(
            tx,
            principal_id,
            actor_id,
            case_id,
            configuration_id,
            effective_at,
            known_at,
        )
        linked_ids = set(decision_closure)
        linked_ids.update(review.source_manifest.version_ids)
        linked_ids.update(quantitative.source_manifest.version_ids)
        responsibility_work = self._linked_responsibility_work_component(
            tx, linked_ids, effective_at, known_at
        )
        for component in (continuity, governing, review, quantitative, responsibility_work):
            if component.state is ReconstructionState.NOT_SAFELY_AVAILABLE:
                return self._empty_position(
                    ReconstructionState.NOT_SAFELY_AVAILABLE, case_id, effective_at, known_at
                )
        manifest_ids = set(decision_closure)
        manifest_ids.update(continuity.source_manifest.version_ids)
        manifest_ids.update(review.source_manifest.version_ids)
        manifest_ids.update(quantitative.source_manifest.version_ids)
        manifest_ids.update(responsibility_work.source_manifest.version_ids)
        decision_id = RecordVersionId.parse(str(decision["version_id"]))
        return ManagementPosition(
            ReconstructionState.AVAILABLE,
            case_id,
            effective_at,
            known_at,
            ReconstructionState.AVAILABLE,
            ReconstructionState.AVAILABLE,
            continuity,
            governing,
            value,
            risk,
            self._component_from_closure(
                tx, (integration_id,), integration_closure, effective_at, known_at
            ),
            self._component_from_closure(
                tx, (decision_id,), decision_closure, effective_at, known_at
            ),
            review,
            quantitative,
            responsibility_work,
            self._manifest(tx, manifest_ids, effective_at, known_at),
            reader_principal_id=principal_id,
            reader_actor_id=actor_id,
        )

    def _current_component(
        self,
        tx: ContinuityTransaction,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        family: str,
        rows: tuple[dict[str, object], ...],
        effective_at: datetime,
        known_at: datetime,
    ) -> PositionComponent:
        selected, conflict = self._selected_version_ids(tx, family, rows, effective_at, known_at)
        if not selected:
            return self._empty_component(ReconstructionState.ABSENT, effective_at, known_at)
        return self._authorized_component(
            tx,
            principal_id,
            actor_id,
            case_id,
            selected,
            effective_at,
            known_at,
            conflict,
        )

    def _case_current_component(
        self,
        tx: ContinuityTransaction,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        family: str,
        table: str,
        configuration_version_id: RecordVersionId | None,
        effective_at: datetime,
        known_at: datetime,
        required_status: str | None = None,
        select_per_record: bool = False,
    ) -> PositionComponent:
        filters: dict[str, object] = {"case_id": str(case_id)}
        if configuration_version_id is not None:
            filters["configuration_version_id"] = str(configuration_version_id)
        rows = tuple(
            row
            for row in tx.projection_rows(table, **filters)
            if required_status is None or row.get("status") == required_status
        )
        if select_per_record:
            selected, conflict = self._selected_record_version_ids(
                tx, family, rows, effective_at, known_at
            )
            if not selected:
                return self._empty_component(ReconstructionState.ABSENT, effective_at, known_at)
            return self._authorized_component(
                tx,
                principal_id,
                actor_id,
                case_id,
                selected,
                effective_at,
                known_at,
                conflict,
            )
        return self._current_component(
            tx, principal_id, actor_id, case_id, family, rows, effective_at, known_at
        )

    def _current_integration_component(
        self,
        tx: ContinuityTransaction,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        configuration_version_id: RecordVersionId | None,
        value: LanePosition | None,
        risk: LanePosition | None,
        effective_at: datetime,
        known_at: datetime,
    ) -> PositionComponent:
        """Select only Integrations bound to both exact current relied lane bases."""

        if configuration_version_id is None or value is None or risk is None:
            return self._empty_component(ReconstructionState.ABSENT, effective_at, known_at)
        rows = tuple(
            row
            for row in tx.projection_rows(
                "prospective_integration_versions",
                case_id=str(case_id),
                configuration_version_id=str(configuration_version_id),
            )
            if self._integration_matches_lanes(row, value, risk)
        )
        return self._current_component(
            tx,
            principal_id,
            actor_id,
            case_id,
            "prospective-integration",
            rows,
            effective_at,
            known_at,
        )

    def _current_decision_component(
        self,
        tx: ContinuityTransaction,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        configuration_version_id: RecordVersionId | None,
        integration: PositionComponent,
        effective_at: datetime,
        known_at: datetime,
    ) -> PositionComponent:
        """Select authorized Decisions bound to the exact current Integration only."""

        if (
            configuration_version_id is None
            or integration.state is not ReconstructionState.AVAILABLE
            or len(integration.version_ids) != 1
        ):
            return self._empty_component(ReconstructionState.ABSENT, effective_at, known_at)
        rows = tuple(
            row
            for row in tx.projection_rows(
                "prospective_decision_versions",
                case_id=str(case_id),
                configuration_version_id=str(configuration_version_id),
            )
            if row.get("status") == "AUTHORIZED"
            and row.get("integration_version_id") == str(integration.version_ids[0])
        )
        return self._current_component(
            tx,
            principal_id,
            actor_id,
            case_id,
            "prospective-decision",
            rows,
            effective_at,
            known_at,
        )

    @staticmethod
    def _integration_matches_lanes(
        row: dict[str, object], value: LanePosition, risk: LanePosition
    ) -> bool:
        for prefix, lane in (("value", value), ("risk", risk)):
            for field, expected in (
                ("assessment", lane.assessment_version_id),
                ("readiness", lane.readiness_version_id),
                ("adequacy", lane.adequacy_version_id),
                ("reliance", lane.reliance_version_id),
            ):
                if row.get(f"{prefix}_{field}_version_id") != str(expected):
                    return False
            try:
                information = tuple(
                    RecordVersionId.parse(value)
                    for value in cast(
                        list[str], json.loads(str(row[f"{prefix}_information_basis_json"]))
                    )
                )
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                return False
            if information != lane.information_basis_version_ids:
                return False
        return True

    def _review_component(
        self,
        tx: ContinuityTransaction,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        configuration_version_id: RecordVersionId | None,
        effective_at: datetime,
        known_at: datetime,
    ) -> PositionComponent:
        ids: set[RecordVersionId] = set()
        conflict = False
        for family, table in (
            ("planned-review-point", "planned_review_point_versions"),
            ("required-review-constraint", "required_review_constraint_versions"),
            ("review-attention-event", "review_attention_event_versions"),
            ("review-episode", "review_episode_versions"),
        ):
            filters: dict[str, object] = {"case_id": str(case_id)}
            if configuration_version_id is not None:
                filters["configuration_version_id"] = str(configuration_version_id)
            selected, selected_conflict = self._selected_record_version_ids(
                tx, family, tx.projection_rows(table, **filters), effective_at, known_at
            )
            ids.update(selected)
            conflict = conflict or selected_conflict
        if not ids:
            return self._empty_component(ReconstructionState.ABSENT, effective_at, known_at)
        return self._authorized_component(
            tx,
            principal_id,
            actor_id,
            case_id,
            tuple(sorted(ids, key=str)),
            effective_at,
            known_at,
            conflict,
        )

    def _quantitative_component(
        self,
        tx: ContinuityTransaction,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        configuration_version_id: RecordVersionId | None,
        effective_at: datetime,
        known_at: datetime,
    ) -> PositionComponent:
        ids: set[RecordVersionId] = set()
        conflict = False
        for family, table in (("quantitative-claim", "quantitative_claim_versions"),):
            filters: dict[str, object] = {"case_id": str(case_id)}
            if configuration_version_id is not None:
                filters["configuration_version_id"] = str(configuration_version_id)
            selected, selected_conflict = self._selected_record_version_ids(
                tx,
                family,
                tx.projection_rows(table, **filters),
                effective_at,
                known_at,
            )
            ids.update(selected)
            conflict = conflict or selected_conflict
        if not ids:
            return self._empty_component(ReconstructionState.ABSENT, effective_at, known_at)
        return self._authorized_component(
            tx,
            principal_id,
            actor_id,
            case_id,
            tuple(sorted(ids, key=str)),
            effective_at,
            known_at,
            conflict,
        )

    @staticmethod
    def _linked_responsibility_work_component(
        tx: ContinuityTransaction,
        linked_ids: set[RecordVersionId],
        effective_at: datetime,
        known_at: datetime,
    ) -> PositionComponent:
        ids = tuple(
            sorted(
                (
                    version_id
                    for version_id in linked_ids
                    if (source := tx.get_version(version_id)) is not None
                    and source.family
                    in {"responsibility", "responsibility-assignment", "case-work"}
                ),
                key=str,
            )
        )
        if not ids:
            return ReconstructionService._empty_component(
                ReconstructionState.ABSENT, effective_at, known_at
            )
        return PositionComponent(
            ReconstructionState.AVAILABLE,
            ids,
            ReconstructionService._manifest(tx, set(ids), effective_at, known_at),
        )

    def _current_lanes(
        self,
        tx: ContinuityTransaction,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        configuration_version_id: RecordVersionId | None,
        integration: PositionComponent,
        effective_at: datetime,
        known_at: datetime,
    ) -> tuple[LanePosition | PositionComponent, LanePosition | PositionComponent]:
        if integration.state is ReconstructionState.AVAILABLE and len(integration.version_ids) == 1:
            row = self._one_row(tx, "prospective_integration_versions", integration.version_ids[0])
            if row is not None:
                value = self._lane_from_row(tx, row, "value", effective_at, known_at)
                risk = self._lane_from_row(tx, row, "risk", effective_at, known_at)
                return (
                    value
                    or self._empty_component(ReconstructionState.MALFORMED, effective_at, known_at),
                    risk
                    or self._empty_component(ReconstructionState.MALFORMED, effective_at, known_at),
                )
        result: list[LanePosition | PositionComponent] = []
        for lane in ("VALUE", "RISK"):
            filters: dict[str, object] = {"case_id": str(case_id), "lane": lane}
            if configuration_version_id is not None:
                filters["configuration_version_id"] = str(configuration_version_id)
            selected, conflict = self._selected_version_ids(
                tx,
                "assessment-reliance",
                tx.projection_rows("assessment_reliance_versions", **filters),
                effective_at,
                known_at,
            )
            if conflict or len(selected) > 1:
                result.append(
                    self._authorized_component(
                        tx,
                        principal_id,
                        actor_id,
                        case_id,
                        selected,
                        effective_at,
                        known_at,
                        True,
                    )
                )
                continue
            if not selected:
                result.append(
                    self._empty_component(ReconstructionState.ABSENT, effective_at, known_at)
                )
                continue
            row = self._one_row(tx, "assessment_reliance_versions", selected[0])
            if row is None:
                result.append(
                    self._empty_component(ReconstructionState.MALFORMED, effective_at, known_at)
                )
                continue
            lane_position = self._lane_from_reliance(tx, row, effective_at, known_at)
            if lane_position is None or not self._closure_visible(
                tx,
                principal_id,
                actor_id,
                case_id,
                set(lane_position.source_manifest.version_ids),
                effective_at,
                known_at,
            ):
                result.append(
                    self._empty_component(
                        ReconstructionState.NOT_SAFELY_AVAILABLE, effective_at, known_at
                    )
                )
            else:
                result.append(lane_position)
        return result[0], result[1]

    def _lane_from_row(
        self,
        tx: ContinuityTransaction,
        row: dict[str, object],
        prefix: str,
        effective_at: datetime,
        known_at: datetime,
    ) -> LanePosition | None:
        try:
            ids = {
                name: RecordVersionId.parse(str(row[f"{prefix}_{name}_version_id"]))
                for name in ("assessment", "readiness", "adequacy", "reliance")
            }
            information = tuple(
                RecordVersionId.parse(value)
                for value in cast(
                    list[str], json.loads(str(row[f"{prefix}_information_basis_json"]))
                )
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            return None
        closure: set[RecordVersionId] = set(information)
        for version_id in ids.values():
            source_closure = self._source_closure(tx, version_id)
            if source_closure is None:
                return None
            closure.update(source_closure)
        return LanePosition(
            prefix.upper(),
            ids["assessment"],
            ids["readiness"],
            ids["adequacy"],
            ids["reliance"],
            information,
            self._manifest(tx, closure, effective_at, known_at),
        )

    def _lane_from_reliance(
        self,
        tx: ContinuityTransaction,
        row: dict[str, object],
        effective_at: datetime,
        known_at: datetime,
    ) -> LanePosition | None:
        try:
            ids = {
                name: RecordVersionId.parse(str(row[f"{name}_version_id"]))
                for name in ("assessment", "readiness", "adequacy")
            }
            reliance_id = RecordVersionId.parse(str(row["version_id"]))
            information = tuple(
                RecordVersionId.parse(value)
                for value in cast(
                    list[str], json.loads(str(row["information_basis_version_ids_json"]))
                )
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            return None
        closure = self._source_closure(tx, reliance_id)
        if closure is None:
            return None
        return LanePosition(
            str(row["lane"]),
            ids["assessment"],
            ids["readiness"],
            ids["adequacy"],
            reliance_id,
            information,
            self._manifest(tx, closure, effective_at, known_at),
        )

    def _authorized_component(
        self,
        tx: ContinuityTransaction,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        version_ids: tuple[RecordVersionId, ...],
        effective_at: datetime,
        known_at: datetime,
        conflict: bool,
    ) -> PositionComponent:
        closure: set[RecordVersionId] = set()
        for version_id in version_ids:
            source_closure = self._source_closure(tx, version_id)
            if source_closure is None:
                return self._empty_component(ReconstructionState.MALFORMED, effective_at, known_at)
            closure.update(source_closure)
        if not self._closure_visible(
            tx, principal_id, actor_id, case_id, closure, effective_at, known_at
        ):
            return self._empty_component(
                ReconstructionState.NOT_SAFELY_AVAILABLE, effective_at, known_at
            )
        return self._component_from_closure(
            tx,
            version_ids,
            closure,
            effective_at,
            known_at,
            ReconstructionState.CONFLICT if conflict else ReconstructionState.AVAILABLE,
        )

    def _component_from_exact(
        self,
        tx: ContinuityTransaction,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        version_ids: tuple[RecordVersionId, ...],
        effective_at: datetime,
        known_at: datetime,
    ) -> PositionComponent:
        return self._authorized_component(
            tx,
            principal_id,
            actor_id,
            case_id,
            version_ids,
            effective_at,
            known_at,
            False,
        )

    def _component_from_closure(
        self,
        tx: ContinuityTransaction,
        version_ids: tuple[RecordVersionId, ...],
        closure: set[RecordVersionId],
        effective_at: datetime,
        known_at: datetime,
        state: ReconstructionState = ReconstructionState.AVAILABLE,
    ) -> PositionComponent:
        return PositionComponent(
            state,
            tuple(sorted(version_ids, key=str)),
            self._manifest(tx, closure, effective_at, known_at),
        )

    @staticmethod
    def _selected_version_ids(
        tx: ContinuityTransaction,
        family: str,
        rows: tuple[dict[str, object], ...],
        effective_at: datetime,
        known_at: datetime,
    ) -> tuple[tuple[RecordVersionId, ...], bool]:
        by_scope: dict[str, dict[str, RecordVersionId]] = defaultdict(dict)
        for row in rows:
            version_id = RecordVersionId.parse(str(row["version_id"]))
            version = tx.get_version(version_id)
            if version is not None and ReconstructionService._has_prospective_semantics(
                tx, version_id
            ):
                by_scope[version.scope][str(version_id)] = version_id
        selected_ids: set[RecordVersionId] = set()
        conflict = False
        for scope, available in by_scope.items():
            selected = tx.select_current(SelectionQuery(family, scope, effective_at, known_at))
            if isinstance(selected, SelectionFound):
                if str(selected.candidate.version_id) in available:
                    selected_ids.add(selected.candidate.version_id)
            elif isinstance(selected, SelectionConflict):
                visible_candidates = tuple(
                    candidate.version_id
                    for candidate in selected.candidates
                    if str(candidate.version_id) in available
                )
                if len(visible_candidates) == 1:
                    selected_ids.add(visible_candidates[0])
                elif visible_candidates:
                    selected_ids.update(visible_candidates)
                    conflict = True
        return tuple(sorted(selected_ids, key=str)), conflict

    @staticmethod
    def _selected_record_version_ids(
        tx: ContinuityTransaction,
        family: str,
        rows: tuple[dict[str, object], ...],
        effective_at: datetime,
        known_at: datetime,
    ) -> tuple[tuple[RecordVersionId, ...], bool]:
        records: dict[RecordId, FinalizedRecordVersion] = {}
        for row in rows:
            version = tx.get_version(RecordVersionId.parse(str(row["version_id"])))
            if version is not None and ReconstructionService._has_prospective_semantics(
                tx, version.version_id
            ):
                records[version.record_id] = version
        selected_ids: set[RecordVersionId] = set()
        conflict = False
        for record_id, sample in records.items():
            selected = tx.select_current(
                SelectionQuery(family, sample.scope, effective_at, known_at, record_id)
            )
            if isinstance(selected, SelectionFound):
                selected_ids.add(selected.candidate.version_id)
            elif isinstance(selected, SelectionConflict):
                selected_ids.update(candidate.version_id for candidate in selected.candidates)
                conflict = True
        return tuple(sorted(selected_ids, key=str)), conflict

    @staticmethod
    def _has_prospective_semantics(tx: ContinuityTransaction, version_id: RecordVersionId) -> bool:
        return len(tx.projection_rows("record_version_semantics", version_id=str(version_id))) == 1

    def _source_closure(
        self,
        tx: ContinuityTransaction,
        version_id: RecordVersionId,
        seen: set[RecordVersionId] | None = None,
    ) -> set[RecordVersionId] | None:
        visited = set() if seen is None else seen
        if version_id in visited:
            return set()
        version = tx.get_version(version_id)
        if version is None:
            return None
        visited.add(version_id)
        closure = {version_id}
        table = _FAMILY_TABLES.get(version.family)
        if table is None:
            return closure
        row = self._one_row(tx, table, version_id)
        if row is None:
            return None
        try:
            direct = self._direct_source_ids(tx, version.family, row)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            return None
        for source_id in direct:
            nested = self._source_closure(tx, source_id, visited)
            if nested is None:
                return None
            closure.update(nested)
        context_digest = row.get("context_digest")
        if context_digest:
            members = tx.projection_rows(
                "exact_context_members", context_digest=str(context_digest)
            )
            if not members:
                return None
            for member in members:
                if member.get("member_kind") == "VERSION":
                    source_id = RecordVersionId.parse(str(member["identity"]))
                    nested = self._source_closure(tx, source_id, visited)
                    if nested is None:
                        return None
                    closure.update(nested)
        return closure

    def _direct_source_ids(
        self,
        tx: ContinuityTransaction,
        family: str,
        row: dict[str, object],
    ) -> set[RecordVersionId]:
        ignored = {"version_id", "predecessor_version_id"}
        ids: set[RecordVersionId] = set()
        for key, value in row.items():
            if value is None or key in ignored:
                continue
            if key.endswith("_version_id"):
                ids.add(RecordVersionId.parse(str(value)))
            elif key.endswith("_version_ids_json") or key.endswith("_basis_json"):
                decoded = json.loads(str(value))
                if isinstance(decoded, list):
                    ids.update(RecordVersionId.parse(str(item)) for item in decoded)
        if family == "quantitative-claim":
            links = tx.projection_rows(
                "quantitative_claim_basis_links", claim_version_id=str(row["version_id"])
            )
            if not {"SOURCE", "APPLICABILITY"} <= {str(link["link_role"]) for link in links}:
                raise ValueError("quantitative claim basis is incomplete")
            ids.update(RecordVersionId.parse(str(link["source_version_id"])) for link in links)
        if family == "responsibility-assignment":
            ids.add(RecordVersionId.parse(str(row["assignment_basis_version_id"])))
        if family == "assignment-basis":
            ids.add(RecordVersionId.parse(str(row["basis_source_version_id"])))
        if family == "prospective-decision" and row.get("status") == "AUTHORIZED":
            authorization = tx.projection_rows(
                "prospective_decision_authorization_versions",
                decision_version_id=str(row["version_id"]),
            )
            if len(authorization) != 1:
                raise ValueError("authorized Decision has no exact authorization fact")
            ids.add(RecordVersionId.parse(str(authorization[0]["version_id"])))
        return ids

    def _closure_visible(
        self,
        tx: ContinuityTransaction,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        closure: set[RecordVersionId],
        effective_at: datetime,
        known_at: datetime,
    ) -> bool:
        return all(
            self._source_visible(
                tx,
                principal_id,
                actor_id,
                case_id,
                source_id,
                effective_at,
                known_at,
            )
            for source_id in closure
        )

    @staticmethod
    def _closure_knowable(
        tx: ContinuityTransaction, closure: set[RecordVersionId], known_at: datetime
    ) -> bool:
        return all(
            (source := tx.get_version(source_id)) is not None and source.recorded_at <= known_at
            for source_id in closure
        )

    def _source_visible(
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
        return bool(
            source is not None
            and self._access.authorize(
                principal_id=principal_id,
                actor_id=str(actor_id),
                action="source.read",
                case_id=case_id,
                write=False,
                source_version_id=source_id,
                source_family=source.family,
                effective_at=effective_at,
                known_at=known_at,
            )
        )

    def _require_case_access(
        self, principal_id: str, actor_id: RecordId, case_id: RecordId
    ) -> None:
        if not self._access.authorize(
            principal_id=principal_id,
            actor_id=str(actor_id),
            action="history.read",
            case_id=case_id,
            write=False,
            source_version_id=None,
            source_family=None,
        ):
            raise ReconstructionAccessDenied()

    @staticmethod
    def _one_row(
        tx: ContinuityTransaction, table: str, version_id: RecordVersionId
    ) -> dict[str, object] | None:
        rows = tx.projection_rows(table, version_id=str(version_id))
        return rows[0] if len(rows) == 1 else None

    @staticmethod
    def _manifest(
        tx: ContinuityTransaction,
        ids: set[RecordVersionId],
        effective_at: datetime,
        known_at: datetime,
    ) -> SourceManifest:
        sources: list[SourceReference] = []
        for version_id in sorted(ids, key=str):
            version = tx.get_version(version_id)
            if version is None:
                continue
            sources.append(
                SourceReference(
                    version.record_id,
                    version.version_id,
                    version.family,
                    version.effective.start,
                    version.effective.end,
                    version.recorded_at,
                )
            )
        return SourceManifest(tuple(sources), effective_at, known_at)

    @staticmethod
    def _blank_manifest(effective_at: datetime, known_at: datetime) -> SourceManifest:
        return SourceManifest((), effective_at, known_at)

    @classmethod
    def _empty_component(
        cls, state: ReconstructionState, effective_at: datetime, known_at: datetime
    ) -> PositionComponent:
        return PositionComponent(state, (), cls._blank_manifest(effective_at, known_at))

    @classmethod
    def _empty_position(
        cls,
        state: ReconstructionState,
        case_id: RecordId,
        effective_at: datetime,
        known_at: datetime,
    ) -> ManagementPosition:
        return ManagementPosition(
            state,
            case_id,
            effective_at,
            known_at,
            state,
            state,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            cls._blank_manifest(effective_at, known_at),
        )

    @staticmethod
    def _unsafe(*components: PositionComponent) -> bool:
        return any(
            component.state
            in (ReconstructionState.NOT_SAFELY_AVAILABLE, ReconstructionState.MALFORMED)
            for component in components
        )

    @staticmethod
    def _validate_cutoffs(effective_at: datetime, known_at: datetime) -> None:
        require_utc(effective_at)
        require_utc(known_at)

    @staticmethod
    def _change(
        name: str,
        prior: tuple[RecordVersionId, ...],
        current: tuple[RecordVersionId, ...],
    ) -> PositionChange:
        return PositionChange(name, prior, current, prior != current, prior != current)

    @staticmethod
    def _component_ids(position: ManagementPosition, name: str) -> tuple[RecordVersionId, ...]:
        value = getattr(position, name)
        if isinstance(value, PositionComponent):
            return value.version_ids
        if isinstance(value, LanePosition):
            return (
                value.assessment_version_id,
                value.readiness_version_id,
                value.adequacy_version_id,
                value.reliance_version_id,
                *value.information_basis_version_ids,
            )
        return ()

    @staticmethod
    def _timeline_description(family: str, version: FinalizedRecordVersion) -> str:
        content = version.content
        label = {
            "case-continuity-status": "Case position recorded",
            "governing-configuration": "Case setup recorded",
            "assessment-candidate": "Assessment completed",
            "assessment-adequacy": "Assessment suitability reviewed",
            "assessment-reliance": "Assessment selected for this decision",
            "prospective-integration": "Value and Risk considered together",
            "prospective-decision": "Decision recorded",
            "planned-review-point": "Next review planned",
            "required-review-constraint": "Review requirement recorded",
            "review-attention-event": "A change needs review",
            "review-episode": "Focused review recorded",
            "quantitative-claim": "Quantitative claim recorded",
            "quantitative-comparability": "Comparability recorded",
        }[family]
        state = content.get("status") or content.get("outcome")
        return f"{label}: {state}" if isinstance(state, str) else label

    @staticmethod
    def _timeline_management_detail(
        family: str, version: FinalizedRecordVersion
    ) -> tuple[str | None, str | None, tuple[str, ...]]:
        if family != "prospective-decision":
            return None, None, ()
        content = version.content
        action = content.get("proposed_action")
        rationale = content.get("rationale")
        raw_conditions = (
            content.get("authorization_conditions")
            if content.get("authorization_conditions")
            else content.get("conditions_and_limits")
        )
        conditions = (
            tuple(value for value in raw_conditions if isinstance(value, str))
            if isinstance(raw_conditions, list)
            else ()
        )
        return (
            action if isinstance(action, str) else None,
            rationale if isinstance(rationale, str) else None,
            conditions,
        )

    @staticmethod
    def _optional_text(value: object) -> str | None:
        return value if isinstance(value, str) else None

    @classmethod
    def _malformed_audit(cls, prior: ManagementPosition) -> DecisionAuditNarrative:
        return DecisionAuditNarrative(
            state=ReconstructionState.MALFORMED,
            decision_version_id=None,
            decision_effective_at=None,
            decision_recorded_at=None,
            action=None,
            rationale=None,
            conditions=(),
            accountable_actor_id=None,
            responsibility_version_id=None,
            assignment_version_id=None,
            assignment_basis_version_id=None,
            authority_source_version_id=None,
            integration_version_id=None,
            value_reliance_version_id=None,
            risk_reliance_version_id=None,
            successor_decision_version_ids=(),
            continuing_review_version_ids=(),
            subsequent_visible_changes=(),
            source_manifest=cls._blank_manifest(prior.effective_at, prior.known_at),
        )

    @staticmethod
    def _merge_manifests(prior: SourceManifest, current: SourceManifest) -> SourceManifest:
        sources = {source.version_id: source for source in prior.sources}
        sources.update({source.version_id: source for source in current.sources})
        return SourceManifest(
            tuple(sorted(sources.values(), key=lambda source: str(source.version_id))),
            current.effective_at,
            current.known_at,
        )
