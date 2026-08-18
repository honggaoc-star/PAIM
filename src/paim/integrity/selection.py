"""Pure deterministic current-selection semantics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from paim.integrity.ids import RecordId, RecordVersionId
from paim.integrity.records import StatusEvent
from paim.integrity.time import EffectiveInterval, require_utc

_ENDING_STATUSES = frozenset({"superseded", "withdrawn"})


@dataclass(frozen=True, slots=True)
class SelectionQuery:
    family: str
    scope: str
    effective_at: datetime
    known_at: datetime | None = None
    record_id: RecordId | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "effective_at", require_utc(self.effective_at))
        if self.known_at is not None:
            object.__setattr__(self, "known_at", require_utc(self.known_at))


@dataclass(frozen=True, slots=True)
class SelectionCandidate:
    record_id: RecordId
    version_id: RecordVersionId
    family: str
    scope: str
    recorded_at: datetime
    effective: EffectiveInterval
    finalized: bool = True
    status_events: frozenset[StatusEvent] = frozenset()
    explicit_ineligibility_reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "recorded_at", require_utc(self.recorded_at))


@dataclass(frozen=True, slots=True)
class SelectionAbsent:
    reason: str = "NOT ESTABLISHED"


@dataclass(frozen=True, slots=True)
class SelectionFound:
    candidate: SelectionCandidate


@dataclass(frozen=True, slots=True)
class SelectionConflict:
    candidates: frozenset[SelectionCandidate]
    reasons: tuple[str, ...] = ("CURRENT RECORD CONFLICT — UNRESOLVED",)


type CurrentSelection = SelectionAbsent | SelectionFound | SelectionConflict


def _is_eligible(candidate: SelectionCandidate, query: SelectionQuery) -> bool:
    if candidate.family != query.family or candidate.scope != query.scope:
        return False
    if query.record_id is not None and candidate.record_id != query.record_id:
        return False
    if not candidate.finalized or candidate.explicit_ineligibility_reasons:
        return False
    if not candidate.effective.contains(query.effective_at):
        return False
    if query.known_at is not None and candidate.recorded_at > query.known_at:
        return False
    for event in candidate.status_events:
        event_known = query.known_at is None or event.recorded_at <= query.known_at
        if (
            event_known
            and event.effective_at <= query.effective_at
            and event.new_status.casefold() in _ENDING_STATUSES
        ):
            return False
    return True


def select_current(
    query: SelectionQuery, candidates: tuple[SelectionCandidate, ...]
) -> CurrentSelection:
    """Return one, explicit absence, or all incompatible eligible candidates.

    Candidate ordering and identifier ordering never select a winner. A frozenset
    makes the conflict result invariant to input permutation without assigning
    semantic order to UUID values.
    """
    eligible = frozenset(candidate for candidate in candidates if _is_eligible(candidate, query))
    if not eligible:
        return SelectionAbsent()
    if len(eligible) == 1:
        return SelectionFound(next(iter(eligible)))
    return SelectionConflict(candidates=eligible)
