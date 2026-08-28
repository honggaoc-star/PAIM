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
CASE_START_RECOVERY_COOKIE = "paim_case_start_recovery"


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


@dataclass(frozen=True, slots=True)
class ExpiredBrowserSession:
    session: BrowserSession
    recoverable_until: datetime


@dataclass(frozen=True, slots=True)
class CaseStartRecovery:
    digest: str
    principal_id: str
    payload: dict[str, str]
    created_at: datetime
    expires_at: datetime


class SessionRegistry:
    """Store only a digest of each opaque browser session identifier."""

    def __init__(
        self,
        *,
        now: Callable[[], datetime] | None = None,
        inactivity_timeout: timedelta = timedelta(minutes=30),
        absolute_timeout: timedelta = timedelta(hours=8),
        anonymous_timeout: timedelta = timedelta(minutes=10),
        recovery_timeout: timedelta = timedelta(minutes=30),
        maximum_sessions: int = 256,
        maximum_recoveries: int = 64,
    ) -> None:
        self._now = now or (lambda: datetime.now(UTC))
        self._inactivity_timeout = inactivity_timeout
        self._absolute_timeout = absolute_timeout
        self._anonymous_timeout = anonymous_timeout
        self._recovery_timeout = recovery_timeout
        self._maximum_sessions = maximum_sessions
        self._maximum_recoveries = maximum_recoveries
        self._sessions: dict[str, BrowserSession] = {}
        self._intents: dict[tuple[str, str], ActionIntent] = {}
        self._expired_sessions: dict[str, ExpiredBrowserSession] = {}
        self._case_start_recoveries: dict[str, CaseStartRecovery] = {}

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
            self._preserve_expired(digest, session, now)
            return None
        if touch:
            session = replace(session, last_active_at=now)
            self._sessions[digest] = session
        return session

    def recoverable_session(self, identifier: str | None) -> BrowserSession | None:
        """Return a short-lived expired session only for exact re-authentication recovery."""

        if not identifier:
            return None
        self.cleanup()
        expired = self._expired_sessions.get(self._digest(identifier))
        return expired.session if expired is not None else None

    def invalidate(self, identifier: str | None) -> None:
        if identifier:
            digest = self._digest(identifier)
            self._sessions.pop(digest, None)
            self._expired_sessions.pop(digest, None)
            for key in tuple(self._intents):
                if key[0] == digest:
                    self._intents.pop(key, None)

    def create_case_start_recovery(
        self,
        identifier: str,
        *,
        payload: dict[str, str],
    ) -> str:
        """Preserve an uncommitted Case-start form across exact-principal reauthentication."""

        expired = self.recoverable_session(identifier)
        if expired is None or expired.authentication is None:
            raise ValueError("recoverable authenticated browser session required")
        self._bound_recovery_capacity()
        token = secrets.token_urlsafe(_SESSION_BYTES)
        digest = self._digest(token)
        now = self._now()
        self._case_start_recoveries[digest] = CaseStartRecovery(
            digest=digest,
            principal_id=expired.authentication.principal_id,
            payload=dict(payload),
            created_at=now,
            expires_at=now + self._recovery_timeout,
        )
        self._expired_sessions.pop(self._digest(identifier), None)
        return token

    def claim_case_start_recovery(
        self,
        token: str | None,
        *,
        identifier: str,
        principal_id: str,
    ) -> ActionIntent | None:
        """Consume one recovery only for the same freshly authenticated principal."""

        if not token:
            return None
        self.cleanup()
        digest = self._digest(token)
        recovery = self._case_start_recoveries.get(digest)
        if recovery is None or not hmac.compare_digest(recovery.principal_id, principal_id):
            return None
        intent = self.create_intent(
            identifier,
            action="case.create_open",
            payload=recovery.payload,
            expected_version_ids=(),
            lifetime=self._recovery_timeout,
        )
        self._case_start_recoveries.pop(digest, None)
        return intent

    def discard_case_start_recovery(self, token: str | None) -> None:
        if token:
            self._case_start_recoveries.pop(self._digest(token), None)

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
        now = self._now()
        for digest, session in tuple(self._sessions.items()):
            if now >= session.expires_at or now >= (
                session.last_active_at + self._inactivity_timeout
            ):
                self._preserve_expired(digest, session, now)
        for key, intent in tuple(self._intents.items()):
            if intent.expires_at <= now or key[0] not in self._sessions:
                self._intents.pop(key, None)
        for digest, expired in tuple(self._expired_sessions.items()):
            if expired.recoverable_until <= now:
                self._expired_sessions.pop(digest, None)
        for digest, recovery in tuple(self._case_start_recoveries.items()):
            if recovery.expires_at <= now:
                self._case_start_recoveries.pop(digest, None)

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

    def _preserve_expired(self, digest: str, session: BrowserSession, now: datetime) -> None:
        self._sessions.pop(digest, None)
        for key in tuple(self._intents):
            if key[0] == digest:
                self._intents.pop(key, None)
        if session.authentication is not None:
            self._expired_sessions[digest] = ExpiredBrowserSession(
                session=session,
                recoverable_until=now + self._recovery_timeout,
            )
            if len(self._expired_sessions) > self._maximum_sessions:
                oldest_digest = min(
                    self._expired_sessions,
                    key=lambda item: self._expired_sessions[item].recoverable_until,
                )
                self._expired_sessions.pop(oldest_digest, None)

    def _bound_recovery_capacity(self) -> None:
        self.cleanup()
        if len(self._case_start_recoveries) >= self._maximum_recoveries:
            oldest = min(self._case_start_recoveries.values(), key=lambda item: item.created_at)
            self._case_start_recoveries.pop(oldest.digest, None)

    @property
    def recovery_count(self) -> int:
        self.cleanup()
        return len(self._case_start_recoveries)
