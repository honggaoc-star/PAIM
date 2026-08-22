"""Access-bounded composition over authoritative PAIM integrity reads."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from datetime import datetime

from paim.application.practitioner.models import (
    ActorContext,
    AnalyticalLaneView,
    AttentionItemView,
    CaseListView,
    CaseOrientationView,
    CaseSummary,
    CaseWorkspaceView,
    ConfigurationView,
    ExplanationView,
    GovernedRecordView,
    HomeView,
    ReadState,
    SourceBasis,
)
from paim.domain import (
    GoverningConfigurationAbsent,
    GoverningConfigurationConflict,
    GoverningConfigurationFound,
    GoverningConfigurationSelection,
)
from paim.integrity import (
    FinalizedRecordVersion,
    RecordId,
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
        source_versions = self._store.m1b_versions(
            case_id=case_id,
            visible_configuration_ids=visible_configuration_ids,
        )
        current = self._current_versions(source_versions, effective_at, known_at)
        visible_versions = self._exact_visible_version_index(current)
        by_family: dict[str, list[FinalizedRecordVersion]] = {}
        for version in current:
            by_family.setdefault(version.family, []).append(version)

        governing_ids: tuple[str, ...]
        governing_basis: tuple[str, ...]
        if isinstance(governing, GoverningConfigurationFound):
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
            ConfigurationView(
                configuration_id=str(version.record_id),
                version_id=str(version.version_id),
                maturity=str(version.content.get("maturity", "unknown")),
                purpose=str(version.content.get("purpose", "unknown")),
                content=dict(version.content),
                is_governing=str(version.version_id) in governing_ids,
                basis=self._basis(version, effective_at, known_at),
            )
            for version in sorted(
                by_family.get("managed-configuration", []),
                key=lambda item: (item.recorded_at, str(item.version_id)),
            )
        )

        evidence = self._record_views(
            by_family.get("evidence", []), effective_at, known_at, visible_versions
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
            "VALUE", by_family, action_access, effective_at, known_at, visible_versions
        )
        risk = self._lane_view(
            "RISK", by_family, action_access, effective_at, known_at, visible_versions
        )
        attention = self._attention(
            case_id=case_id,
            governing_state=governing_state,
            governing_explanation=ExplanationView(
                governing_state,
                governing_reason,
                "Designate a finalized candidate Configuration",
                True,
                action_access.get("configuration.designate", False),
                True,
                "Required by the governing designation command",
                "Established only by the owning PAIM capability",
                governing_basis,
            ),
            evidence=evidence,
            authority_gaps=gaps,
            applicability=applicability,
            value=value,
            risk=risk,
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
            evidence=evidence,
            authority=authority,
            authority_gaps=gaps,
            applicability=applicability,
            value=value,
            risk=risk,
            attention=attention,
            effective_at=effective_at,
            known_at=known_at,
        )

    @staticmethod
    def _attention(
        *,
        case_id: RecordId,
        governing_state: ReadState,
        governing_explanation: ExplanationView,
        evidence: tuple[GovernedRecordView, ...],
        authority_gaps: tuple[GovernedRecordView, ...],
        applicability: tuple[GovernedRecordView, ...],
        value: AnalyticalLaneView,
        risk: AnalyticalLaneView,
        action_access: Mapping[str, bool],
    ) -> tuple[AttentionItemView, ...]:
        base = f"/cases/{case_id}"
        items: list[AttentionItemView] = []
        if governing_state is not ReadState.ESTABLISHED:
            label = (
                "Governing Configuration conflict"
                if governing_state is ReadState.CONFLICT
                else "Governing Configuration not yet established"
            )
            items.append(
                AttentionItemView(
                    "governing-configuration",
                    label,
                    governing_explanation.reason,
                    f"{base}/configuration",
                    governing_explanation,
                )
            )
        unresolved = tuple(item for item in authority_gaps if item.state == "UNRESOLVED")
        if unresolved:
            items.append(
                AttentionItemView(
                    "authority-gap",
                    "Unresolved authority question",
                    f"{len(unresolved)} visible authority question(s) remain unresolved.",
                    f"{base}/evidence",
                    ExplanationView(
                        ReadState.ABSENT,
                        "The recorded Authority Gap remains unresolved; PAIM does not infer "
                        "authority from software access or surrounding evidence.",
                        "Work through the owning Authority Gap pathway",
                        True,
                        False,
                        True,
                        "The applicable accountable assignment or mechanism must remain explicit",
                        "Only the owning authority capability may establish or change "
                        "substantive authority",
                        tuple(item.version_id for item in unresolved),
                    ),
                )
            )
        if evidence and not applicability:
            items.append(
                AttentionItemView(
                    "applicability",
                    "Evidence Applicability not yet established",
                    "Evidence exists, but no visible exact Applicability determination is "
                    "established.",
                    f"{base}/evidence",
                    ExplanationView(
                        ReadState.ABSENT,
                        "Evidence existence does not establish Applicability to a Configuration "
                        "or analytical Input.",
                        "Assess Evidence Applicability for an exact visible target",
                        True,
                        action_access.get("evidence.applicability", False),
                        True,
                        "Applicability requires an explicit accountable basis",
                        "Applicability does not create substantive authority",
                    ),
                )
            )
        for lane in (value, risk):
            if lane.selection_state is not ReadState.ESTABLISHED:
                label = (
                    f"{lane.lane.title()} assessment selection conflict"
                    if lane.selection_state is ReadState.CONFLICT
                    else f"{lane.lane.title()} assessment not yet selected"
                )
                items.append(
                    AttentionItemView(
                        f"{lane.lane.casefold()}-selection",
                        label,
                        lane.explanation.reason,
                        f"{base}/assessment#{lane.lane.casefold()}",
                        ExplanationView(
                            lane.selection_state,
                            lane.explanation.reason,
                            f"Select one exact {lane.lane.title()} analysis for the stated use",
                            True,
                            action_access.get(f"{lane.lane.casefold()}-input.select", False),
                            True,
                            lane.explanation.accountability,
                            lane.explanation.substantive_authority,
                            lane.explanation.basis_version_ids,
                        ),
                    )
                )
        return tuple(items)

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

        return default

    def _lane_view(
        self,
        lane: str,
        by_family: Mapping[str, list[FinalizedRecordVersion]],
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
        state = (
            ReadState.ABSENT
            if not selections
            else ReadState.ESTABLISHED
            if len(selections) == 1
            else ReadState.CONFLICT
        )
        reason = (
            f"{lane.title()} Input selection is not established."
            if state is ReadState.ABSENT
            else f"One exact {lane.title()} Input selection is established."
            if state is ReadState.ESTABLISHED
            else f"Multiple incompatible {lane.title()} selections remain explicit."
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
                tuple(item.version_id for item in selections),
            ),
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
