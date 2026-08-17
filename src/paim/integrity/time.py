"""UTC, microsecond, interval, and injected-clock conventions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol

_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
_MIN_I64 = -(2**63)
_MAX_I64 = 2**63 - 1


def require_utc(value: datetime) -> datetime:
    """Require a timezone-aware value already normalized to UTC."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("datetime must be timezone-aware UTC")
    if value.utcoffset() != timedelta(0):
        raise ValueError("datetime must be normalized to UTC")
    return value.astimezone(UTC)


def to_epoch_microseconds(value: datetime) -> int:
    """Convert aware UTC time to exact signed integer epoch microseconds."""
    delta = require_utc(value) - _EPOCH
    result = (delta.days * 86_400 + delta.seconds) * 1_000_000 + delta.microseconds
    if not _MIN_I64 <= result <= _MAX_I64:
        raise OverflowError("timestamp exceeds signed 64-bit microseconds")
    return result


def from_epoch_microseconds(value: int) -> datetime:
    """Convert signed integer epoch microseconds to aware UTC time."""
    if not _MIN_I64 <= value <= _MAX_I64:
        raise OverflowError("timestamp exceeds signed 64-bit microseconds")
    return _EPOCH + timedelta(microseconds=value)


@dataclass(frozen=True, slots=True)
class EffectiveInterval:
    """Half-open effective interval ``[start, end)``."""

    start: datetime
    end: datetime | None = None

    def __post_init__(self) -> None:
        start = require_utc(self.start)
        end = require_utc(self.end) if self.end is not None else None
        if end is not None and end <= start:
            raise ValueError("effective interval end must be after start")
        object.__setattr__(self, "start", start)
        object.__setattr__(self, "end", end)

    def contains(self, instant: datetime) -> bool:
        checked = require_utc(instant)
        return self.start <= checked and (self.end is None or checked < self.end)


class Clock(Protocol):
    """Source of recorded time supplied to application services."""

    def now(self) -> datetime: ...


@dataclass(frozen=True, slots=True)
class FixedClock:
    """Deterministic clock for tests and controlled imports."""

    value: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", require_utc(self.value))

    def now(self) -> datetime:
        return self.value


@dataclass(frozen=True, slots=True)
class SystemClock:
    """UTC wall clock isolated behind the application boundary."""

    def now(self) -> datetime:
        return datetime.now(UTC)
