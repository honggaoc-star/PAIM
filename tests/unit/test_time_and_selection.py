from datetime import UTC, datetime, timedelta, timezone
from itertools import permutations

import pytest

from paim.integrity import (
    EffectiveInterval,
    EventId,
    FixedClock,
    RecordId,
    RecordVersionId,
    SelectionAbsent,
    SelectionCandidate,
    SelectionConflict,
    SelectionFound,
    SelectionQuery,
    StatusEvent,
    from_epoch_microseconds,
    require_utc,
    select_current,
    to_epoch_microseconds,
)
from tests.helpers import utc


def candidate(
    *,
    recorded_at: datetime,
    effective_from: datetime,
    events: frozenset[StatusEvent] = frozenset(),
) -> SelectionCandidate:
    version_id = RecordVersionId.new()
    return SelectionCandidate(
        record_id=RecordId.new(),
        version_id=version_id,
        family="opaque",
        scope="scope",
        recorded_at=recorded_at,
        effective=EffectiveInterval(effective_from),
        status_events=events,
    )


def test_utc_aware_only_and_exact_microsecond_round_trip() -> None:
    value = utc(2026, 1, 2, 3, 456789)
    assert from_epoch_microseconds(to_epoch_microseconds(value)) == value
    with pytest.raises(ValueError, match="timezone-aware"):
        require_utc(datetime(2026, 1, 1))
    with pytest.raises(ValueError, match="normalized to UTC"):
        require_utc(datetime(2026, 1, 1, tzinfo=timezone(timedelta(hours=1))))


def test_half_open_interval_boundaries_and_controlled_clock() -> None:
    start = utc(2026, 1, 1)
    end = utc(2026, 2, 1)
    interval = EffectiveInterval(start, end)

    assert interval.contains(start)
    assert interval.contains(end - timedelta(microseconds=1))
    assert not interval.contains(end)
    assert FixedClock(start).now() == start


def test_selection_returns_explicit_absence_and_exact_single_version() -> None:
    query = SelectionQuery("opaque", "scope", utc(2026, 1, 5))
    selected = candidate(recorded_at=utc(2026, 1, 2), effective_from=utc(2026, 1, 1))

    assert isinstance(select_current(query, ()), SelectionAbsent)
    result = select_current(query, (selected,))
    assert isinstance(result, SelectionFound)
    assert result.candidate.version_id == selected.version_id


def test_conflict_contains_every_candidate_and_is_permutation_invariant() -> None:
    same_time = utc(2026, 1, 2)
    candidates = tuple(
        candidate(recorded_at=same_time, effective_from=utc(2026, 1, 1)) for _ in range(3)
    )
    query = SelectionQuery("opaque", "scope", utc(2026, 1, 5))
    results = [select_current(query, tuple(order)) for order in permutations(candidates)]

    assert all(isinstance(result, SelectionConflict) for result in results)
    assert all(result == results[0] for result in results)
    conflict = results[0]
    assert isinstance(conflict, SelectionConflict)
    assert conflict.candidates == frozenset(candidates)


def test_known_at_excludes_later_recorded_backdated_version_and_status() -> None:
    first = candidate(recorded_at=utc(2026, 1, 2), effective_from=utc(2026, 1, 1))
    ending = StatusEvent(
        EventId.new(),
        first.version_id,
        "finalized",
        "superseded",
        utc(2026, 2, 1),
        utc(2026, 1, 10),
        "actor",
        "correction",
    )
    first_with_status = SelectionCandidate(
        record_id=first.record_id,
        version_id=first.version_id,
        family=first.family,
        scope=first.scope,
        recorded_at=first.recorded_at,
        effective=first.effective,
        status_events=frozenset({ending}),
    )
    backdated = candidate(recorded_at=utc(2026, 2, 1), effective_from=utc(2026, 1, 10))

    prior = select_current(
        SelectionQuery("opaque", "scope", utc(2026, 1, 20), utc(2026, 1, 20)),
        (first_with_status, backdated),
    )
    current = select_current(
        SelectionQuery("opaque", "scope", utc(2026, 1, 20)),
        (first_with_status, backdated),
    )

    assert isinstance(prior, SelectionFound)
    assert prior.candidate.version_id == first.version_id
    assert isinstance(current, SelectionFound)
    assert current.candidate.version_id == backdated.version_id


def test_uuid_and_equal_timestamps_never_break_a_conflict() -> None:
    instant = datetime(2026, 1, 1, tzinfo=UTC)
    left = candidate(recorded_at=instant, effective_from=instant)
    right = candidate(recorded_at=instant, effective_from=instant)

    result = select_current(SelectionQuery("opaque", "scope", instant), (right, left))
    assert isinstance(result, SelectionConflict)
    assert result.candidates == frozenset({left, right})


def test_explicit_management_subject_identity_filters_same_scope_candidates() -> None:
    instant = utc(2026, 1, 1)
    selected = candidate(recorded_at=instant, effective_from=instant)
    other_subject = candidate(recorded_at=instant, effective_from=instant)

    result = select_current(
        SelectionQuery("opaque", "scope", instant, record_id=selected.record_id),
        (other_subject, selected),
    )

    assert isinstance(result, SelectionFound)
    assert result.candidate.version_id == selected.version_id
