"""Access-bounded composition over authoritative PAIM integrity reads."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from datetime import datetime

from paim.application.practitioner.integration_basis import exact_current_integration_basis
from paim.application.practitioner.models import (
    ActorContext,
    AnalyticalAssessmentView,
    AnalyticalLaneView,
    CaseListView,
    CaseOrientationView,
    CaseSummary,
    CaseWorkspaceView,
    ConfigurationView,
    DecisionWorkspaceView,
    ExplanationView,
    GovernedRecordView,
    HomeView,
    OrientationItemView,
    PractitionerExceptionView,
    ReadState,
    SourceBasis,
)
from paim.domain import (
    EvidenceClassification,
    GoverningConfigurationAbsent,
    GoverningConfigurationConflict,
    GoverningConfigurationFound,
    GoverningConfigurationSelection,
)
from paim.integrity import (
    FinalizedRecordVersion,
    RecordId,
    RecordVersionId,
    SelectionAbsent,
    SelectionConflict,
    SelectionFound,
    SelectionQuery,
)
from paim.persistence.ports import IntegrityStore


class PractitionerQueryService:
    """Compose immutable views only after trusted access scope is established."""

    def __init__(self, store: IntegrityStore) -> None:
        self._store = store

    def actor_context(
        self,
        *,
        principal_id: str,
        actor_id: RecordId,
        effective_at: datetime,
        known_at: datetime,
    ) -> ActorContext:
        selection = self._store.select_current(
            SelectionQuery(
                family="paim-actor",
                scope=f"actor:{actor_id}",
                record_id=actor_id,
                effective_at=effective_at,
                known_at=known_at,
            )
        )
        if not isinstance(selection, SelectionFound):
            raise RuntimeError("current authenticated Actor read is not established")
        version = self._store.get_version(selection.candidate.version_id)
        if version is None:
            raise RuntimeError("authenticated Actor Version is unavailable")
        display_name = version.content.get("display_name")
        if not isinstance(display_name, str) or not display_name.strip():
            raise RuntimeError("authenticated Actor display name is unavailable")
        return ActorContext(
            principal_id=principal_id,
            actor_id=str(actor_id),
            display_name=display_name,
            basis=SourceBasis(
                record_id=str(actor_id),
                version_ids=(str(version.version_id),),
                effective_at=effective_at,
                known_at=known_at,
            ),
        )

    def cases(
        self,
        *,
        visible_case_ids: frozenset[RecordId],
        visible_configuration_counts: Mapping[RecordId, int],
        effective_at: datetime,
        known_at: datetime,
    ) -> tuple[CaseSummary, ...]:
        # The caller supplies only the trusted access-filtered population. No global
        # population is queried here, so hidden identities cannot enter aggregation.
        summaries = tuple(
            self._case_summary(
                case_id=case_id,
                visible_configuration_count=visible_configuration_counts.get(case_id, 0),
                effective_at=effective_at,
                known_at=known_at,
            )
            for case_id in visible_case_ids
        )
        return tuple(sorted(summaries, key=lambda item: (item.title.casefold(), item.case_id)))

    def home(
        self,
        *,
        actor: ActorContext,
        cases: tuple[CaseSummary, ...],
        health_state: str,
        health_reasons: tuple[str, ...],
        effective_at: datetime,
        known_at: datetime,
    ) -> HomeView:
        return HomeView(
            actor=actor,
            health=health_state,
            health_reasons=health_reasons,
            visible_case_count=len(cases),
            cases=cases,
            effective_at=effective_at,
            known_at=known_at,
        )

    def case_list(
        self,
        *,
        actor: ActorContext,
        cases: tuple[CaseSummary, ...],
        search_text: str,
        effective_at: datetime,
        known_at: datetime,
    ) -> CaseListView:
        normalized = search_text.strip().casefold()
        filtered = (
            tuple(
                item
                for item in cases
                if normalized in item.title.casefold() or normalized in item.case_id.casefold()
            )
            if normalized
            else cases
        )
        return CaseListView(
            actor=actor,
            cases=filtered,
            visible_case_count=len(filtered),
            search_text=search_text.strip(),
            effective_at=effective_at,
            known_at=known_at,
        )

    @staticmethod
    def orientation(
        *,
        actor: ActorContext,
        cases: tuple[CaseSummary, ...],
        case_id: RecordId,
        effective_at: datetime,
        known_at: datetime,
    ) -> CaseOrientationView | None:
        selected = next((item for item in cases if item.case_id == str(case_id)), None)
        if selected is None:
            return None
        return CaseOrientationView(actor, selected, effective_at, known_at)

    def workspace(
        self,
        *,
        actor: ActorContext,
        cases: tuple[CaseSummary, ...],
        case_id: RecordId,
        visible_configuration_ids: frozenset[RecordId],
        governing: GoverningConfigurationSelection,
        lifecycle_state: str,
        action_access: Mapping[str, bool],
        effective_at: datetime,
        known_at: datetime,
    ) -> CaseWorkspaceView | None:
        selected_case = next((item for item in cases if item.case_id == str(case_id)), None)
        if selected_case is None:
            return None
        source_versions = self._store.m1c_versions(
            case_id=case_id,
            visible_configuration_ids=visible_configuration_ids,
        )
        current = self._current_versions(source_versions, effective_at, known_at)
        visible_versions = self._exact_visible_version_index(source_versions)
        all_by_family: dict[str, list[FinalizedRecordVersion]] = {}
        for version in source_versions:
            all_by_family.setdefault(version.family, []).append(version)
        by_family: dict[str, list[FinalizedRecordVersion]] = {}
        for version in current:
            by_family.setdefault(version.family, []).append(version)

        visible_configuration_version_ids = frozenset(
            str(version.version_id)
            for version in source_versions
            if version.family == "managed-configuration"
        )

        governing_ids: tuple[str, ...]
        governing_basis: tuple[str, ...]
        if (
            isinstance(governing, GoverningConfigurationFound)
            and str(governing.configuration_version_id) not in visible_configuration_version_ids
        ):
            governing_state = ReadState.INACCESSIBLE
            governing_ids = ()
            governing_reason = (
                "The setup used for this Case cannot be shown in the current visible context."
            )
            governing_basis = ()
        elif (
            isinstance(governing, GoverningConfigurationConflict)
            and not {str(value) for value in governing.configuration_version_ids}
            <= visible_configuration_version_ids
        ):
            governing_state = ReadState.INACCESSIBLE
            governing_ids = ()
            governing_reason = (
                "The setup used for this Case cannot be resolved in the current visible context."
            )
            governing_basis = ()
        elif isinstance(governing, GoverningConfigurationFound):
            governing_state = ReadState.ESTABLISHED
            governing_ids = (str(governing.configuration_version_id),)
            governing_reason = "One exact governing Configuration is established."
            governing_basis = (str(governing.designation_version_id),)
        elif isinstance(governing, GoverningConfigurationConflict):
            governing_state = ReadState.CONFLICT
            governing_ids = tuple(
                sorted(str(value) for value in governing.configuration_version_ids)
            )
            governing_reason = governing.reason
            governing_basis = tuple(
                sorted(str(value) for value in governing.designation_version_ids)
            )
        else:
            assert isinstance(governing, GoverningConfigurationAbsent)
            governing_state = ReadState.ABSENT
            governing_ids = ()
            governing_reason = governing.reason
            governing_basis = ()

        configuration_views = tuple(
            self._configuration_view(
                version,
                is_governing=str(version.version_id) in governing_ids,
                effective_at=effective_at,
                known_at=known_at,
            )
            for version in sorted(
                by_family.get("managed-configuration", []),
                key=lambda item: (item.recorded_at, str(item.version_id)),
            )
        )

        evidence = self._record_views(
            by_family.get("evidence", []), effective_at, known_at, visible_versions
        )
        available_information, explicitly_unavailable_information = self._information_groups(
            evidence
        )
        authority = self._record_views(
            by_family.get("authority-record", []), effective_at, known_at, visible_versions
        )
        gaps = self._record_views(
            by_family.get("authority-gap", []), effective_at, known_at, visible_versions
        )
        applicability = self._record_views(
            by_family.get("evidence-applicability", []),
            effective_at,
            known_at,
            visible_versions,
        )
        value = self._lane_view(
            "VALUE",
            by_family,
            applicability,
            governing_ids,
            action_access,
            effective_at,
            known_at,
            visible_versions,
        )
        risk = self._lane_view(
            "RISK",
            by_family,
            applicability,
            governing_ids,
            action_access,
            effective_at,
            known_at,
            visible_versions,
        )
        decision = self._decision_workspace(
            by_family=by_family,
            all_by_family=all_by_family,
            value=value,
            risk=risk,
            action_access=action_access,
            effective_at=effective_at,
            known_at=known_at,
            visible_versions=visible_versions,
        )
        authorized_configuration_versions = {
            str(item.content.get("configuration_version_id", ""))
            for item in decision.authorizations
        }
        configuration_views = tuple(
            replace(
                item,
                practitioner_label="Authorized setup",
                context_summary=(
                    "A Decision authorizes this setup under recorded limits. Authorization "
                    "does not by itself establish operation."
                ),
            )
            if item.version_id in authorized_configuration_versions
            else item
            for item in configuration_views
        )
        available_work, required_prerequisite, unresolved_conditions = self._orientation_items(
            case_id=case_id,
            governing_state=governing_state,
            evidence=evidence,
            authority_gaps=gaps,
            applicability=applicability,
            value=value,
            risk=risk,
            decision=decision,
            action_access=action_access,
        )
        return CaseWorkspaceView(
            actor=actor,
            case=selected_case,
            lifecycle_state=lifecycle_state,
            configurations=configuration_views,
            governing_state=governing_state,
            governing_configuration_version_ids=governing_ids,
            governing_explanation=ExplanationView(
                governing_state,
                governing_reason,
                "Designate an exact finalized candidate Configuration",
                True,
                action_access.get("configuration.designate", False),
                True,
                "Required by the governing designation command",
                "Established only by the owning PAIM capability",
                governing_basis,
            ),
            current_position=self._current_position(lifecycle_state, governing_state),
            evidence=evidence,
            available_information=available_information,
            explicitly_unavailable_information=explicitly_unavailable_information,
            information_action_access={
                action: action_access.get(action, False)
                for action in (
                    "evidence.create",
                    "authority.create",
                    "authority-gap.create",
                    "evidence.applicability",
                )
            },
            authority=authority,
            authority_gaps=gaps,
            applicability=applicability,
            value=value,
            risk=risk,
            decision=decision,
            available_work=available_work,
            required_prerequisite=required_prerequisite,
            unresolved_conditions=unresolved_conditions,
            effective_at=effective_at,
            known_at=known_at,
        )

    @staticmethod
    def _information_groups(
        evidence: tuple[GovernedRecordView, ...],
    ) -> tuple[tuple[GovernedRecordView, ...], tuple[GovernedRecordView, ...]]:
        """Split only explicitly governed unavailable information from neutral information."""

        unavailable = tuple(
            item
            for item in evidence
            if item.content.get("classification") == EvidenceClassification.UNKNOWN.value
            and item.content.get("unknown") is True
            and item.content.get("not_a_positive_finding") is True
        )
        unavailable_versions = {item.version_id for item in unavailable}
        available = tuple(item for item in evidence if item.version_id not in unavailable_versions)
        return available, unavailable

    @staticmethod
    def _orientation_items(
        *,
        case_id: RecordId,
        governing_state: ReadState,
        evidence: tuple[GovernedRecordView, ...],
        authority_gaps: tuple[GovernedRecordView, ...],
        applicability: tuple[GovernedRecordView, ...],
        value: AnalyticalLaneView,
        risk: AnalyticalLaneView,
        decision: DecisionWorkspaceView,
        action_access: Mapping[str, bool],
    ) -> tuple[
        tuple[OrientationItemView, ...],
        OrientationItemView | None,
        tuple[OrientationItemView, ...],
    ]:
        base = f"/cases/{case_id}"
        available: list[OrientationItemView] = []
        unresolved: list[OrientationItemView] = []
        # This read is passive orientation; no downstream action intent is established.
        required: OrientationItemView | None = None

        if governing_state is not ReadState.ESTABLISHED:
            condition = (
                "More than one setup claims to be the current assessment basis."
                if governing_state is ReadState.CONFLICT
                else "The assessment setup is not visible in this session."
                if governing_state is ReadState.INACCESSIBLE
                else "No single setup is established as the current assessment basis."
            )
            resolution = (
                "Review the competing setup designations and use the governed Configuration "
                "process to preserve one valid assessment basis."
                if governing_state is ReadState.CONFLICT
                else "Ask an administrator to restore access to the Case's setup."
                if governing_state is ReadState.INACCESSIBLE
                else "Use the proposal setup page to establish one finalized setup for assessment."
            )
            exception = PractitionerExceptionView(
                "Begin evidence or independent assessment work",
                condition,
                (
                    "PAIM cannot choose a setup by recency, specificity, role, or presentation "
                    "order."
                    if governing_state is ReadState.CONFLICT
                    else "Evidence and assessments must remain bound to one visible "
                    "Configuration Version."
                ),
                resolution,
            )
            if action_access.get("configuration.create", False) or action_access.get(
                "configuration.designate", False
            ):
                available.append(
                    OrientationItemView(
                        "assessment-setup",
                        "Establish one setup for assessment",
                        "Review visible setups or record the setup that assessment work will use.",
                        f"{base}/configuration",
                    )
                )
            unresolved.append(
                OrientationItemView(
                    "assessment-setup-condition",
                    "Assessment setup unresolved",
                    condition,
                    f"{base}/configuration",
                    exception,
                )
            )

        unresolved_gaps = tuple(item for item in authority_gaps if item.state == "UNRESOLVED")
        if unresolved_gaps:
            unresolved_condition = PractitionerExceptionView(
                "Use the unresolved requirement or authority as a Decision basis",
                "A recorded authority question remains unresolved.",
                "PAIM does not infer governing authority from access, nearby evidence, "
                "or role labels.",
                "Review the question and route it to the responsible authority role or "
                "governance process.",
            )
            unresolved.append(
                OrientationItemView(
                    "authority-gap",
                    "Unresolved authority question",
                    "A visible requirement or authority question still needs an explicit "
                    "resolution.",
                    f"{base}/evidence",
                    unresolved_condition,
                )
            )

        if evidence and not applicability:
            unresolved.append(
                OrientationItemView(
                    "applicability",
                    "How the available information applies is unresolved",
                    "Information is recorded, but its relevance to this setup has not been "
                    "decided.",
                    f"{base}/evidence",
                    PractitionerExceptionView(
                        "Use recorded information in an assessment",
                        "No visible Applicability determination is established.",
                        "Recorded information does not automatically bear on a setup or analysis.",
                        "Decide what the information bears on, under what limits, and why.",
                    ),
                )
            )

        if governing_state is ReadState.ESTABLISHED:
            available.append(
                OrientationItemView(
                    "review-known",
                    "Review what is known and unresolved",
                    "Review visible information, limitations, requirements, and authority "
                    "questions.",
                    f"{base}/evidence",
                )
            )

        incomplete_lanes = tuple(
            lane for lane in (value, risk) if lane.selection_state is not ReadState.ESTABLISHED
        )
        for lane in (value, risk):
            if lane.selection_state is ReadState.CONFLICT:
                unresolved.append(
                    OrientationItemView(
                        f"{lane.lane.casefold()}-selection-conflict",
                        f"{lane.lane.title()} assessment choice is conflicted",
                        f"More than one incompatible {lane.lane.title()} assessment choice "
                        "remains visible.",
                        f"{base}/assessment#{lane.lane.casefold()}",
                        PractitionerExceptionView(
                            "Use the lane in a management judgment",
                            f"The {lane.lane.title()} assessment choice is conflicted.",
                            "PAIM cannot choose among incompatible lane selections.",
                            f"Resolve the {lane.lane.title()} selection through its governed "
                            "lane process.",
                        ),
                    )
                )
            elif (
                governing_state is ReadState.ESTABLISHED
                and lane.selection_state is ReadState.ABSENT
            ):
                action_prefix = lane.lane.casefold()
                if action_access.get(f"{action_prefix}-input.create", False) or action_access.get(
                    f"{action_prefix}-input.select", False
                ):
                    available.append(
                        OrientationItemView(
                            f"{action_prefix}-assessment",
                            f"Assess {lane.lane.title()}",
                            f"Develop and explicitly choose the {lane.lane.title()} assessment "
                            "management will use.",
                            f"{base}/assessment#{action_prefix}",
                        )
                    )
                else:
                    unresolved.append(
                        OrientationItemView(
                            f"{action_prefix}-software-access",
                            f"{lane.lane.title()} work cannot be recorded in this session",
                            "The required software permission is not available.",
                            f"{base}/assessment#{action_prefix}",
                            PractitionerExceptionView(
                                f"Record or choose a {lane.lane.title()} assessment",
                                "This session lacks the required command access.",
                                "Software access permits an attempt but does not establish "
                                "accountability or authority.",
                                "Ask a software administrator for the required access; the "
                                "lane's accountability remains separate.",
                            ),
                        )
                    )

        if governing_state is ReadState.ESTABLISHED and not incomplete_lanes:
            downstream = (
                (
                    "management-judgment",
                    "Record the management judgment",
                    "Relate the independent Value and Risk assessments without combining them.",
                    "integration.create",
                )
                if decision.integration_state is not ReadState.ESTABLISHED
                else (
                    "operating-limits",
                    "Define operating limits and conditions",
                    "State the permitted scope, controls, conditions, and exclusions.",
                    "boundary.create",
                )
                if decision.boundary_state is not ReadState.ESTABLISHED
                else (
                    "proposal",
                    "Propose an action",
                    "Prepare an action for separate authorization.",
                    "decision.propose",
                )
                if decision.decision_state is not ReadState.ESTABLISHED
                else (
                    "authorization",
                    "Review the proposal for authorization",
                    "Authorization remains a separate governed act.",
                    "decision.authorize",
                )
                if decision.authorization_state is not ReadState.ESTABLISHED
                else None
            )
            if downstream is not None:
                key, label, summary, action = downstream
                if action_access.get(action, False):
                    available.append(OrientationItemView(key, label, summary, f"{base}/decision"))

        return tuple(available), required, tuple(unresolved)

    @staticmethod
    def _current_position(lifecycle_state: str, governing_state: ReadState) -> str:
        if governing_state is ReadState.CONFLICT:
            return "Work is paused because the setup for assessment is conflicted."
        if governing_state is ReadState.INACCESSIBLE:
            return "The Case is visible, but its assessment setup is not visible in this session."
        if governing_state is ReadState.ABSENT:
            return "The Case is open, but no single setup is established for assessment."
        positions = {
            "OPEN": "A setup is established for assessment; the management concern remains open.",
            "CONFIGURATION_DEFINED": (
                "The setup for assessment is established; evidence and independent "
                "assessment work can proceed."
            ),
            "EVIDENCE_ANALYSIS": (
                "Information and independent Value and Risk assessments are being developed."
            ),
            "READY_FOR_INTEGRATION": (
                "Independent Value and Risk bases are ready for management judgment."
            ),
            "DECISION_PENDING": "A proposed action is awaiting a separate authorization decision.",
            "DECIDED": (
                "An authorized management Decision is established; operation remains "
                "separately governed."
            ),
        }
        return positions.get(lifecycle_state, "Management work is in progress for this Case.")

    @staticmethod
    def _configuration_view(
        version: FinalizedRecordVersion,
        *,
        is_governing: bool,
        effective_at: datetime,
        known_at: datetime,
    ) -> ConfigurationView:
        purpose = str(version.content.get("purpose", "unknown"))
        maturity = str(version.content.get("maturity", "unknown"))
        if (is_governing and purpose == "candidate") or purpose in {
            "proposed",
            "experimental",
        }:
            practitioner_label = "Proposed setup under review"
        elif purpose in {"alternative", "fallback"}:
            practitioner_label = "Comparison option"
        elif is_governing:
            practitioner_label = "Setup used for this assessment"
        else:
            practitioner_label = "Other visible setup"
        context_summary = (
            "This is the Case's current assessment basis. That fact does not authorize or "
            "start operation."
            if is_governing
            else "This setup is visible for comparison and is not the current assessment basis."
        )
        return ConfigurationView(
            configuration_id=str(version.record_id),
            version_id=str(version.version_id),
            maturity=maturity,
            purpose=purpose,
            content=dict(version.content),
            is_governing=is_governing,
            practitioner_label=practitioner_label,
            context_summary=context_summary,
            basis=PractitionerQueryService._basis(version, effective_at, known_at),
        )

    def _decision_workspace(
        self,
        *,
        by_family: Mapping[str, list[FinalizedRecordVersion]],
        all_by_family: Mapping[str, list[FinalizedRecordVersion]],
        value: AnalyticalLaneView,
        risk: AnalyticalLaneView,
        action_access: Mapping[str, bool],
        effective_at: datetime,
        known_at: datetime,
        visible_versions: Mapping[str, FinalizedRecordVersion | None],
    ) -> DecisionWorkspaceView:
        def selected(lane: AnalyticalLaneView) -> GovernedRecordView | None:
            if lane.selection_state is not ReadState.ESTABLISHED:
                return None
            selection = lane.selections[0]
            matches = tuple(
                item
                for item in lane.candidates
                if item.version_id == selection.content.get("input_version_id")
                and item.record_id == selection.content.get("input_id")
            )
            return matches[0] if len(matches) == 1 else None

        selected_value = selected(value)
        selected_risk = selected(risk)
        all_integrations = self._record_views(
            by_family.get("integration", []), effective_at, known_at, visible_versions
        )
        integrations = tuple(
            item
            for item in all_integrations
            if exact_current_integration_basis(item, value=value, risk=risk) is not None
        )
        integration_versions = {item.version_id: item for item in integrations}
        all_boundaries = self._record_views(
            by_family.get("boundary-snapshot", []), effective_at, known_at, visible_versions
        )
        boundaries = tuple(
            item
            for item in all_boundaries
            if (
                integration := integration_versions.get(
                    str(item.content.get("integration_version_id", ""))
                )
            )
            is not None
            and item.content.get("integration_id") == integration.record_id
            and item.content.get("configuration_id") == integration.content.get("configuration_id")
            and item.content.get("configuration_version_id")
            == integration.content.get("configuration_version_id")
        )
        boundary_versions = {item.version_id: item for item in boundaries}
        all_decisions = self._record_views(
            by_family.get("management-decision", []), effective_at, known_at, visible_versions
        )
        decisions = tuple(
            item
            for item in all_decisions
            if (
                integration := integration_versions.get(
                    str(item.content.get("integration_version_id", ""))
                )
            )
            is not None
            and (
                boundary := boundary_versions.get(
                    str(item.content.get("boundary_snapshot_version_id", ""))
                )
            )
            is not None
            and item.content.get("integration_id") == integration.record_id
            and item.content.get("boundary_snapshot_id") == boundary.record_id
            and boundary.content.get("integration_version_id") == integration.version_id
            and item.content.get("configuration_id") == integration.content.get("configuration_id")
            and item.content.get("configuration_version_id")
            == integration.content.get("configuration_version_id")
        )
        decision_versions = {item.version_id: item for item in decisions}
        all_authorizations = self._record_views(
            by_family.get("decision-authorization-basis", []),
            effective_at,
            known_at,
            visible_versions,
        )
        authorizations = tuple(
            item
            for item in all_authorizations
            if (decision := decision_versions.get(str(item.content.get("decision_version_id", ""))))
            is not None
            and item.content.get("decision_id") == decision.record_id
            and item.content.get("configuration_id") == decision.content.get("configuration_id")
            and item.content.get("configuration_version_id")
            == decision.content.get("configuration_version_id")
        )
        assignments = tuple(
            item
            for item in self._record_views(
                by_family.get("role-assignment", []),
                effective_at,
                known_at,
                visible_versions,
            )
            if item.content.get("role") == "Decision Authority"
            and item.content.get("accountable") is True
        )
        history_versions = tuple(
            version
            for family in (
                "integration",
                "uncertainty-classification",
                "boundary-snapshot",
                "boundary-determination",
                "management-decision",
                "decision-authorization-basis",
            )
            for version in all_by_family.get(family, [])
        )
        history = self._record_views(
            list(history_versions), effective_at, known_at, visible_versions
        )

        def state(values: tuple[GovernedRecordView, ...]) -> ReadState:
            return (
                ReadState.ABSENT
                if not values
                else ReadState.ESTABLISHED
                if len(values) == 1
                else ReadState.CONFLICT
            )

        integration_state = state(integrations)
        boundary_state = state(tuple(item for item in boundaries if item.state == "finalized"))
        decision_state = state(
            tuple(item for item in decisions if item.state in {"proposed", "pending_authorization"})
        )
        authorization_state = state(authorizations)

        def explanation(
            stage_state: ReadState,
            established: str,
            absent: str,
            action: str,
            access_action: str,
            basis: tuple[GovernedRecordView, ...],
            accountability: str,
            authority: str,
        ) -> ExplanationView:
            reason = (
                established
                if stage_state is ReadState.ESTABLISHED
                else f"Multiple incompatible current {absent} records remain explicit."
                if stage_state is ReadState.CONFLICT
                else f"No exact current {absent} is established."
            )
            return ExplanationView(
                stage_state,
                reason,
                action,
                True,
                action_access.get(access_action, False),
                True,
                accountability,
                authority,
                tuple(item.version_id for item in basis),
            )

        return DecisionWorkspaceView(
            selected_value,
            selected_risk,
            integrations,
            boundaries,
            decisions,
            authorizations,
            assignments,
            history,
            integration_state,
            boundary_state,
            decision_state,
            authorization_state,
            explanation(
                integration_state,
                "One exact Integration remains valid for the current selected "
                "Value and Risk basis.",
                "Integration",
                "Integrate the exact selected Value and Risk analyses",
                "integration.create",
                integrations,
                "The Integration must retain an explicit accountable basis.",
                "Integration does not authorize a Decision.",
            ),
            explanation(
                boundary_state,
                "One exact finalized operating Boundary is established.",
                "finalized Boundary",
                "Establish explicit Boundary clauses for the exact Integration",
                "boundary.create",
                boundaries,
                "The Boundary owner remains explicit.",
                "A Boundary limits a Decision; it does not authorize one.",
            ),
            explanation(
                decision_state,
                "One exact current Decision proposal is established.",
                "Decision proposal",
                "Propose a Decision bound to the exact Integration and Boundary",
                "decision.propose",
                decisions,
                "Proposal authorship is not Decision authority.",
                "A proposal is not an authorization.",
            ),
            explanation(
                authorization_state,
                "One exact Decision Authorization Basis is established.",
                "Decision Authorization Basis",
                "Authorize through the owning Decision authority capability",
                "decision.authorize",
                authorizations,
                "Exactly one eligible accountable Decision Authority assignment is required.",
                "Substantive authority must be established by exact assignment and authority "
                "source; software access is insufficient.",
            ),
        )

    def _current_versions(
        self,
        versions: tuple[FinalizedRecordVersion, ...],
        effective_at: datetime,
        known_at: datetime,
    ) -> tuple[FinalizedRecordVersion, ...]:
        record_ids = sorted({version.record_id for version in versions}, key=str)
        selected: list[FinalizedRecordVersion] = []
        exemplars = {version.record_id: version for version in versions}
        for record_id in record_ids:
            exemplar = exemplars[record_id]
            result = self._store.select_current(
                SelectionQuery(
                    family=exemplar.family,
                    scope=exemplar.scope,
                    record_id=record_id,
                    effective_at=effective_at,
                    known_at=known_at,
                )
            )
            candidates = (
                (result.candidate,)
                if isinstance(result, SelectionFound)
                else tuple(result.candidates)
                if isinstance(result, SelectionConflict)
                else ()
            )
            for candidate in candidates:
                version = self._store.get_version(candidate.version_id)
                if version is not None:
                    selected.append(version)
        return tuple(selected)

    @staticmethod
    def _basis(
        version: FinalizedRecordVersion, effective_at: datetime, known_at: datetime
    ) -> SourceBasis:
        return SourceBasis(
            str(version.record_id), (str(version.version_id),), effective_at, known_at
        )

    def _record_views(
        self,
        versions: list[FinalizedRecordVersion],
        effective_at: datetime,
        known_at: datetime,
        visible_versions: Mapping[str, FinalizedRecordVersion | None],
    ) -> tuple[GovernedRecordView, ...]:
        values = []
        for version in versions:
            content = dict(version.content)
            label = next(
                (
                    str(content[key])
                    for key in ("question", "source", "finding", "purpose", "category")
                    if content.get(key)
                ),
                version.family.replace("-", " ").title(),
            )
            state = str(
                content.get("outcome")
                or content.get("attention")
                or content.get("maturity")
                or content.get("status")
                or "ESTABLISHED"
            )
            view = GovernedRecordView(
                str(version.record_id),
                str(version.version_id),
                version.family,
                label,
                state,
                content,
                self._basis(version, effective_at, known_at),
            )
            values.append(
                replace(view, label=self._contextual_label(version, visible_versions, label))
            )
        return tuple(sorted(values, key=lambda item: (item.label.casefold(), item.version_id)))

    @staticmethod
    def _exact_visible_version_index(
        versions: tuple[FinalizedRecordVersion, ...],
    ) -> dict[str, FinalizedRecordVersion | None]:
        """Index only unambiguous exact Versions from the access-filtered current population."""

        indexed: dict[str, FinalizedRecordVersion | None] = {}
        for version in versions:
            key = str(version.version_id)
            indexed[key] = version if key not in indexed else None
        return indexed

    @staticmethod
    def _contextual_label(
        version: FinalizedRecordVersion,
        visible_versions: Mapping[str, FinalizedRecordVersion | None],
        default: str,
    ) -> str:
        """Derive display text only from exact, visible, authoritative relations."""

        content = version.content

        def exact(version_id: object) -> FinalizedRecordVersion | None:
            if not isinstance(version_id, str) or not version_id:
                return None
            return visible_versions.get(version_id)

        def text(source: FinalizedRecordVersion, key: str) -> str | None:
            value = source.content.get(key)
            return value.strip() if isinstance(value, str) and value.strip() else None

        def exact_target(
            *, version_id: object, record_id: object, family: str
        ) -> FinalizedRecordVersion | None:
            target = exact(version_id)
            if (
                target is None
                or target.family != family
                or not isinstance(record_id, str)
                or str(target.record_id) != record_id
            ):
                return None
            return target

        if version.family == "evidence-applicability":
            evidence = exact_target(
                version_id=content.get("evidence_version_id"),
                record_id=content.get("evidence_id"),
                family="evidence",
            )
            target_type = content.get("target_type")
            target_family = (
                {
                    "managed_configuration_version": "managed-configuration",
                    "value_input_version": "value-input",
                    "risk_input_version": "risk-input",
                    "authority_record_version": "authority-record",
                    "authority_gap": "authority-gap",
                }.get(target_type)
                if isinstance(target_type, str)
                else None
            )
            target = (
                exact_target(
                    version_id=content.get("target_version_id"),
                    record_id=content.get("target_id"),
                    family=target_family,
                )
                if target_family is not None
                else None
            )
            source_label = text(evidence, "source") if evidence is not None else None
            target_label: str | None = None
            if target is not None:
                if target.family == "managed-configuration":
                    target_label = text(target, "system")
                elif target.family == "value-input":
                    finding = text(target, "finding")
                    target_label = f"Value analysis: {finding}" if finding else None
                elif target.family == "risk-input":
                    finding = text(target, "finding")
                    target_label = f"Risk analysis: {finding}" if finding else None
                elif target.family == "authority-record":
                    source = text(target, "source")
                    target_label = f"Authority source: {source}" if source else None
                elif target.family == "authority-gap":
                    question = text(target, "question")
                    target_label = f"Authority question: {question}" if question else None
            outcome = content.get("outcome")
            if source_label and target_label and isinstance(outcome, str) and outcome:
                return f"{outcome.replace('_', ' ').title()} — {source_label} → {target_label}"
            return "Applicability — exact related records unavailable"

        if version.family == "lane-evidence-fitness":
            lane_value = content.get("lane")
            lane = lane_value if isinstance(lane_value, str) else None
            expected_family = (
                {"VALUE": "value-input", "RISK": "risk-input"}.get(lane)
                if lane is not None
                else None
            )
            analytical_input = exact(content.get("input_version_id"))
            finding = (
                text(analytical_input, "finding")
                if analytical_input is not None and analytical_input.family == expected_family
                else None
            )
            outcome = content.get("outcome")
            if isinstance(lane, str) and finding and isinstance(outcome, str) and outcome:
                return f"{lane.title()} fitness — {outcome.replace('_', ' ').title()} — {finding}"
            lane_label = lane.title() if isinstance(lane, str) and lane else "Lane"
            return f"{lane_label} fitness — exact analysis unavailable"

        if version.family == "input-acceptance-selection":
            lane_value = content.get("lane")
            lane = lane_value if isinstance(lane_value, str) else None
            expected_family = (
                {"VALUE": "value-input", "RISK": "risk-input"}.get(lane)
                if lane is not None
                else None
            )
            analytical_input = exact_target(
                version_id=content.get("input_version_id"),
                record_id=content.get("input_id"),
                family=expected_family or "",
            )
            fitness = exact(content.get("fitness_version_id"))
            exact_fitness = (
                fitness is not None
                and fitness.family == "lane-evidence-fitness"
                and fitness.content.get("lane") == lane
                and fitness.content.get("input_version_id") == content.get("input_version_id")
                and fitness.content.get("outcome") == "SUPPORTABLE"
            )
            finding = text(analytical_input, "finding") if analytical_input is not None else None
            if isinstance(lane, str) and finding and exact_fitness:
                return f"{lane.title()} assessment selected — {finding}"
            lane_label = lane.title() if isinstance(lane, str) and lane else "Lane"
            return f"{lane_label} assessment selection — exact analysis unavailable"

        if version.family == "integration":
            value_input = exact(content.get("value_input_version_id"))
            risk_input = exact(content.get("risk_input_version_id"))
            value_finding = (
                text(value_input, "finding")
                if value_input is not None and value_input.family == "value-input"
                else None
            )
            risk_finding = (
                text(risk_input, "finding")
                if risk_input is not None and risk_input.family == "risk-input"
                else None
            )
            if value_finding and risk_finding:
                return f"Integration — Value: {value_finding} | Risk: {risk_finding}"
            return "Integration — exact selected Value/Risk basis unavailable"

        if version.family == "boundary-snapshot":
            integration = exact(content.get("integration_version_id"))
            rationale = text(version, "narrative_rationale")
            if integration is not None and integration.family == "integration" and rationale:
                return f"Boundary — {rationale}"
            return "Boundary — exact Integration relation unavailable"

        if version.family == "management-decision":
            integration = exact(content.get("integration_version_id"))
            boundary = exact(content.get("boundary_snapshot_version_id"))
            proposed_action = text(version, "proposed_action")
            if (
                integration is not None
                and integration.family == "integration"
                and boundary is not None
                and boundary.family == "boundary-snapshot"
                and proposed_action
            ):
                return f"Proposed Decision — {proposed_action}"
            return "Decision proposal — exact Integration/Boundary basis unavailable"

        if version.family == "decision-authorization-basis":
            decision = exact(content.get("decision_version_id"))
            scope = text(version, "authorized_scope")
            proposed_action = text(decision, "proposed_action") if decision is not None else None
            if decision is not None and decision.family == "management-decision" and scope:
                return f"Authorized Decision — {proposed_action or 'exact proposal'} — {scope}"
            return "Decision authorization — exact proposal relation unavailable"

        if version.family == "role-assignment" and content.get("role") == "Decision Authority":
            target_type = content.get("target_type")
            if isinstance(target_type, str):
                return f"Decision Authority — {target_type.replace('_', ' ').title()} scope"
            return "Decision Authority assignment — exact target unavailable"

        return default

    def _lane_view(
        self,
        lane: str,
        by_family: Mapping[str, list[FinalizedRecordVersion]],
        applicability: tuple[GovernedRecordView, ...],
        governing_configuration_version_ids: tuple[str, ...],
        action_access: Mapping[str, bool],
        effective_at: datetime,
        known_at: datetime,
        visible_versions: Mapping[str, FinalizedRecordVersion | None],
    ) -> AnalyticalLaneView:
        candidates = self._record_views(
            by_family.get(f"{lane.casefold()}-input", []),
            effective_at,
            known_at,
            visible_versions,
        )
        fitness = tuple(
            item
            for item in self._record_views(
                by_family.get("lane-evidence-fitness", []),
                effective_at,
                known_at,
                visible_versions,
            )
            if item.content.get("lane") == lane
        )
        selections = tuple(
            item
            for item in self._record_views(
                by_family.get("input-acceptance-selection", []),
                effective_at,
                known_at,
                visible_versions,
            )
            if item.content.get("lane") == lane
        )
        ineligible_selection_statuses = {"withdrawn", "rejected_for_use", "superseded"}
        eligible_selections = tuple(
            item
            for item in selections
            if not ineligible_selection_statuses.intersection(
                self._store.version_statuses(
                    version_id=RecordVersionId.parse(item.version_id),
                    effective_at=effective_at,
                    known_at=known_at,
                )
            )
        )
        current_context_selections = tuple(
            item
            for item in eligible_selections
            if len(governing_configuration_version_ids) != 1
            or item.content.get("configuration_version_id")
            == governing_configuration_version_ids[0]
        )
        expected_target_type = f"{lane.casefold()}_input_version"
        ineligible_input_statuses = {"withdrawn", "superseded", "refresh_required"}
        assessments: list[AnalyticalAssessmentView] = []
        for candidate in candidates:
            if (
                len(governing_configuration_version_ids) == 1
                and candidate.content.get("configuration_version_id")
                != governing_configuration_version_ids[0]
            ):
                continue
            candidate_statuses = self._store.version_statuses(
                version_id=RecordVersionId.parse(candidate.version_id),
                effective_at=effective_at,
                known_at=known_at,
            )
            related_applicability = tuple(
                item
                for item in applicability
                if item.content.get("target_type") == expected_target_type
                and item.content.get("target_id") == candidate.record_id
                and item.content.get("target_version_id") == candidate.version_id
            )
            related_fitness = tuple(
                item
                for item in fitness
                if item.content.get("input_version_id") == candidate.version_id
                and item.content.get("configuration_version_id")
                == candidate.content.get("configuration_version_id")
                and not ineligible_input_statuses.intersection(candidate_statuses)
            )
            related_selections = tuple(
                item
                for item in current_context_selections
                if item.content.get("input_id") == candidate.record_id
                and item.content.get("input_version_id") == candidate.version_id
                and item.content.get("configuration_version_id")
                == candidate.content.get("configuration_version_id")
                and not ineligible_input_statuses.intersection(candidate_statuses)
            )
            assessments.append(
                AnalyticalAssessmentView(
                    candidate,
                    candidate_statuses,
                    related_applicability,
                    related_fitness,
                    related_selections,
                )
            )
        visible_context_selections = tuple(
            selection for assessment in assessments for selection in assessment.selections
        )
        selection_contexts: dict[tuple[object, object, object], int] = {}
        for item in visible_context_selections:
            context = (
                item.content.get("configuration_version_id"),
                item.content.get("use_context"),
                item.content.get("purpose"),
            )
            selection_contexts[context] = selection_contexts.get(context, 0) + 1
        state = (
            ReadState.CONFLICT
            if any(count > 1 for count in selection_contexts.values())
            else ReadState.ESTABLISHED
            if visible_context_selections
            else ReadState.ABSENT
        )
        reason = (
            f"{lane.title()} Input selection is not established."
            if state is ReadState.ABSENT
            else f"An explicit {lane.title()} Input selection is established for each recorded use."
            if state is ReadState.ESTABLISHED
            else f"Multiple incompatible {lane.title()} selections remain explicit."
        )
        supportable = any(
            item.state == "SUPPORTABLE" and not bool(item.content.get("decision_limiting"))
            for assessment in assessments
            for item in assessment.fitness
        )
        task_stage = (
            "SELECTION_CONFLICT"
            if state is ReadState.CONFLICT
            else "SELECTED"
            if state is ReadState.ESTABLISHED
            else "CHOOSE_FOR_USE"
            if supportable
            else "REVIEW_SUPPORT"
            if any(item.ready and item.actionable for item in assessments)
            else "READY_FOR_REVIEW"
            if any(item.actionable for item in assessments)
            else "DEVELOP"
        )
        return AnalyticalLaneView(
            lane,
            candidates,
            fitness,
            selections,
            state,
            ExplanationView(
                state,
                reason,
                f"Complete the exact {lane.title()} lane acceptance pathway",
                True,
                action_access.get(f"{lane.casefold()}-input.create", False),
                True,
                "Lane-specific accountability must be established",
                "Software permission does not establish substantive authority",
                tuple(item.version_id for item in visible_context_selections),
            ),
            tuple(assessments),
            task_stage,
            {
                action: action_access.get(action, False)
                for action in (
                    f"{lane.casefold()}-input.create",
                    f"{lane.casefold()}-input.ready",
                    f"{lane.casefold()}-fitness.create",
                    f"{lane.casefold()}-input.select",
                )
            },
        )

    def _case_summary(
        self,
        *,
        case_id: RecordId,
        visible_configuration_count: int,
        effective_at: datetime,
        known_at: datetime,
    ) -> CaseSummary:
        selection = self._store.select_current(
            SelectionQuery(
                family="case",
                scope=f"case:{case_id}",
                record_id=case_id,
                effective_at=effective_at,
                known_at=known_at,
            )
        )
        if isinstance(selection, SelectionFound):
            version = self._store.get_version(selection.candidate.version_id)
            title = version.content.get("title") if version is not None else None
            if not isinstance(title, str) or not title.strip():
                return CaseSummary(
                    str(case_id),
                    "Case title unavailable",
                    ReadState.INDETERMINATE,
                    "The exact current Case Version could not be reconstructed.",
                    visible_configuration_count,
                    SourceBasis(
                        str(case_id),
                        (str(selection.candidate.version_id),),
                        effective_at,
                        known_at,
                    ),
                )
            return CaseSummary(
                str(case_id),
                title,
                ReadState.ESTABLISHED,
                "One exact current Case Version is established.",
                visible_configuration_count,
                SourceBasis(
                    str(case_id),
                    (str(selection.candidate.version_id),),
                    effective_at,
                    known_at,
                ),
            )
        if isinstance(selection, SelectionConflict):
            version_ids = tuple(
                sorted(str(candidate.version_id) for candidate in selection.candidates)
            )
            return CaseSummary(
                str(case_id),
                "Case title unresolved",
                ReadState.CONFLICT,
                "Multiple incompatible current Case Versions remain explicit.",
                visible_configuration_count,
                SourceBasis(str(case_id), version_ids, effective_at, known_at),
            )
        if isinstance(selection, SelectionAbsent):
            return CaseSummary(
                str(case_id),
                "Case version not established",
                ReadState.ABSENT,
                selection.reason,
                visible_configuration_count,
                SourceBasis(str(case_id), (), effective_at, known_at),
            )
        raise AssertionError("unreachable current-selection result")
