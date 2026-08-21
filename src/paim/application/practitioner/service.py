"""Access-bounded composition over authoritative PAIM integrity reads."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime

from paim.application.practitioner.models import (
    ActorContext,
    CaseListView,
    CaseOrientationView,
    CaseSummary,
    HomeView,
    ReadState,
    SourceBasis,
)
from paim.integrity import (
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
