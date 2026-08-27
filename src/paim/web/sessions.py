"""Opaque, process-local browser sessions for the one-worker M1 topology."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta

from paim.operational.models import AuthenticatedSession

_SESSION_BYTES = 32


@dataclass(frozen=True, slots=True)
class BrowserSession:
    digest: str
    csrf_secret: str
    created_at: datetime
    last_active_at: datetime
    expires_at: datetime
    authentication: AuthenticatedSession | None = None

    @property
    def authenticated(self) -> bool:
        return self.authentication is not None


@dataclass(frozen=True, slots=True)
class ActionIntent:
    intent_id: str
    action: str
    payload: dict[str, str]
    expected_version_ids: tuple[str, ...]
    idempotency_key: str
    created_at: datetime
    expires_at: datetime
    outcome_path: str | None = None


class SessionRegistry:
    """Store only a digest of each opaque browser session identifier."""

    def __init__(
        self,
        *,
        now: Callable[[], datetime] | None = None,
        inactivity_timeout: timedelta = timedelta(minutes=30),
        absolute_timeout: timedelta = timedelta(hours=8),
        anonymous_timeout: timedelta = timedelta(minutes=10),
        maximum_sessions: int = 256,
    ) -> None:
        self._now = now or (lambda: datetime.now(UTC))
        self._inactivity_timeout = inactivity_timeout
        self._absolute_timeout = absolute_timeout
        self._anonymous_timeout = anonymous_timeout
        self._maximum_sessions = maximum_sessions
        self._sessions: dict[str, BrowserSession] = {}
        self._intents: dict[tuple[str, str], ActionIntent] = {}

    @staticmethod
    def _digest(identifier: str) -> str:
        return hashlib.sha256(identifier.encode("ascii")).hexdigest()

    def create_anonymous(self) -> tuple[str, BrowserSession]:
        return self._create(None)

    def rotate_authenticated(
        self, identifier: str, authentication: AuthenticatedSession
    ) -> tuple[str, BrowserSession]:
        self.invalidate(identifier)
        return self._create(authentication)

    def get(self, identifier: str | None, *, touch: bool = True) -> BrowserSession | None:
        if not identifier:
            return None
        now = self._now()
        digest = self._digest(identifier)
        session = self._sessions.get(digest)
        if session is None:
            return None
        inactivity_expiry = session.last_active_at + self._inactivity_timeout
        if now >= session.expires_at or now >= inactivity_expiry:
            self._sessions.pop(digest, None)
            return None
        if touch:
            session = replace(session, last_active_at=now)
            self._sessions[digest] = session
        return session

    def invalidate(self, identifier: str | None) -> None:
        if identifier:
            digest = self._digest(identifier)
            self._sessions.pop(digest, None)
            for key in tuple(self._intents):
                if key[0] == digest:
                    self._intents.pop(key, None)

    def create_intent(
        self,
        identifier: str,
        *,
        action: str,
        payload: dict[str, str],
        expected_version_ids: tuple[str, ...],
        lifetime: timedelta = timedelta(minutes=15),
    ) -> ActionIntent:
        session = self.get(identifier, touch=False)
        if session is None or not session.authenticated:
            raise ValueError("authenticated browser session required")
        now = self._now()
        intent = ActionIntent(
            intent_id=secrets.token_urlsafe(24),
            action=action,
            payload=dict(payload),
            expected_version_ids=expected_version_ids,
            idempotency_key=secrets.token_urlsafe(32),
            created_at=now,
            expires_at=now + lifetime,
        )
        self._intents[(session.digest, intent.intent_id)] = intent
        return intent

    def intent(self, identifier: str, intent_id: str, *, action: str) -> ActionIntent | None:
        session = self.get(identifier, touch=False)
        if session is None:
            return None
        key = (session.digest, intent_id)
        intent = self._intents.get(key)
        if intent is None or intent.action != action or self._now() >= intent.expires_at:
            self._intents.pop(key, None)
            return None
        return intent

    def intent_for_actions(
        self, identifier: str, intent_id: str, *, actions: frozenset[str]
    ) -> ActionIntent | None:
        """Resolve one intent only when its action belongs to a closed route allowlist."""

        session = self.get(identifier, touch=False)
        if session is None:
            return None
        key = (session.digest, intent_id)
        intent = self._intents.get(key)
        if intent is None or intent.action not in actions or self._now() >= intent.expires_at:
            self._intents.pop(key, None)
            return None
        return intent

    def record_intent_outcome(
        self, identifier: str, intent_id: str, *, outcome_path: str
    ) -> ActionIntent:
        session = self.get(identifier, touch=False)
        if session is None:
            raise ValueError("browser session unavailable")
        key = (session.digest, intent_id)
        intent = self._intents[key]
        completed = replace(intent, outcome_path=outcome_path)
        self._intents[key] = completed
        return completed

    def discard_intent(self, identifier: str, intent_id: str) -> None:
        session = self.get(identifier, touch=False)
        if session is not None:
            self._intents.pop((session.digest, intent_id), None)

    def verify_csrf(self, session: BrowserSession, supplied: str) -> bool:
        return hmac.compare_digest(session.csrf_secret, supplied)

    @property
    def count(self) -> int:
        self.cleanup()
        return len(self._sessions)

    def cleanup(self) -> None:
        for digest, session in tuple(self._sessions.items()):
            now = self._now()
            if now >= session.expires_at or now >= (
                session.last_active_at + self._inactivity_timeout
            ):
                self._sessions.pop(digest, None)
        for key, intent in tuple(self._intents.items()):
            if intent.expires_at <= self._now() or key[0] not in self._sessions:
                self._intents.pop(key, None)

    def _create(self, authentication: AuthenticatedSession | None) -> tuple[str, BrowserSession]:
        self.cleanup()
        if len(self._sessions) >= self._maximum_sessions:
            oldest = min(self._sessions.values(), key=lambda item: item.last_active_at)
            self._sessions.pop(oldest.digest, None)
        identifier = secrets.token_urlsafe(_SESSION_BYTES)
        digest = self._digest(identifier)
        now = self._now()
        timeout = self._absolute_timeout if authentication else self._anonymous_timeout
        session = BrowserSession(
            digest=digest,
            csrf_secret=secrets.token_urlsafe(_SESSION_BYTES),
            created_at=now,
            last_active_at=now,
            expires_at=now + timeout,
            authentication=authentication,
        )
        self._sessions[digest] = session
        return identifier, session
