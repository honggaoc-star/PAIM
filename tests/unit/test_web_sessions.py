from __future__ import annotations

from datetime import timedelta

from paim.integrity import RecordId
from paim.operational import AuthenticatedSession
from paim.web.app import AttemptLimiter
from paim.web.sessions import SessionRegistry
from tests.web_support import NOW, MutableNow


def authenticated() -> AuthenticatedSession:
    return AuthenticatedSession(
        "principal:test",
        RecordId.new(),
        "correlation:test",
        NOW,
    )


def test_opaque_identifier_digest_rotation_and_invalidation() -> None:
    clock = MutableNow()
    registry = SessionRegistry(now=clock)
    anonymous_id, anonymous = registry.create_anonymous()

    assert len(anonymous_id) >= 43
    assert anonymous_id not in repr(anonymous)
    assert registry.get(anonymous_id, touch=False) == anonymous

    authenticated_id, browser_session = registry.rotate_authenticated(anonymous_id, authenticated())
    assert authenticated_id != anonymous_id
    assert registry.get(anonymous_id) is None
    assert registry.get(authenticated_id) == browser_session
    registry.invalidate(authenticated_id)
    assert registry.get(authenticated_id) is None


def test_inactivity_absolute_expiry_and_bounded_count() -> None:
    clock = MutableNow()
    registry = SessionRegistry(now=clock, maximum_sessions=2)
    first, _ = registry.create_anonymous()
    clock.advance(timedelta(seconds=1))
    second, _ = registry.create_anonymous()
    clock.advance(timedelta(seconds=1))
    third, _ = registry.create_anonymous()
    assert registry.count == 2
    assert registry.get(first) is None
    assert registry.get(second) is not None
    assert registry.get(third) is not None

    authenticated_id, _ = registry.rotate_authenticated(third, authenticated())
    clock.advance(timedelta(minutes=31))
    assert registry.get(authenticated_id) is None

    absolute_registry = SessionRegistry(now=clock)
    anonymous_id, _ = absolute_registry.create_anonymous()
    session_id, _ = absolute_registry.rotate_authenticated(anonymous_id, authenticated())
    for _ in range(23):
        clock.advance(timedelta(minutes=20))
        assert absolute_registry.get(session_id) is not None
    clock.advance(timedelta(minutes=20))
    assert absolute_registry.get(session_id) is None


def test_csrf_comparison_is_bound_to_exact_session() -> None:
    registry = SessionRegistry(now=MutableNow())
    first_id, first = registry.create_anonymous()
    _second_id, second = registry.create_anonymous()
    assert registry.verify_csrf(first, first.csrf_secret)
    assert not registry.verify_csrf(first, second.csrf_secret)
    registry.invalidate(first_id)


def test_attempt_limiter_is_bounded_and_recovers_after_window() -> None:
    clock = MutableNow()
    limiter = AttemptLimiter(now=clock, maximum_attempts=2, maximum_keys=2)
    limiter.record_failure("principal:a")
    limiter.record_failure("principal:a")
    assert not limiter.allowed("principal:a")
    limiter.record_failure("principal:b")
    limiter.record_failure("principal:c")
    assert limiter.key_count == 2
    assert limiter.allowed("principal:a")
    clock.advance(timedelta(minutes=1))
    assert limiter.allowed("principal:b")
