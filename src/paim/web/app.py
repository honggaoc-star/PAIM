"""FastAPI/Jinja local browser shell over the authenticated PAIM gateway."""

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.templating import Jinja2Templates

from paim.integrity import RecordId
from paim.operational import OperationalApplication
from paim.operational.models import AccessDenied, AuthenticationFailed, LocalConfiguration
from paim.web.m1b import register_m1b_routes
from paim.web.sessions import BrowserSession, SessionRegistry

COOKIE_NAME = "paim_session"
MAX_REQUEST_BODY = 8_192
GENERIC_AUTHENTICATION_ERROR = (
    "Authentication was not established. Check the details and try again."
)
_CSP = (
    "default-src 'self'; frame-ancestors 'none'; form-action 'self'; "
    "base-uri 'none'; object-src 'none'"
)


@dataclass(frozen=True, slots=True)
class WebRuntime:
    operational: OperationalApplication
    sessions: SessionRegistry
    expected_origin: str
    owns_operational: bool = False


class AttemptLimiter:
    def __init__(
        self,
        *,
        now: Callable[[], datetime],
        maximum_attempts: int = 5,
        maximum_keys: int = 256,
        window: timedelta = timedelta(minutes=1),
    ) -> None:
        self._now = now
        self._maximum = maximum_attempts
        self._maximum_keys = maximum_keys
        self._window = window
        self._attempts: dict[str, deque[datetime]] = defaultdict(deque)

    def allowed(self, key: str) -> bool:
        now = self._now()
        attempts = self._attempts.get(key)
        if attempts is None:
            return True
        while attempts and now - attempts[0] >= self._window:
            attempts.popleft()
        if not attempts:
            self._attempts.pop(key, None)
            return True
        return len(attempts) < self._maximum

    def record_failure(self, key: str) -> None:
        if key not in self._attempts and len(self._attempts) >= self._maximum_keys:
            self._attempts.pop(next(iter(self._attempts)))
        self._attempts[key].append(self._now())

    def clear(self, key: str) -> None:
        self._attempts.pop(key, None)

    @property
    def key_count(self) -> int:
        return len(self._attempts)


def create_web_application(
    config: LocalConfiguration,
    *,
    operational: OperationalApplication | None = None,
    sessions: SessionRegistry | None = None,
    expected_origin: str = "http://127.0.0.1:8841",
    now: Callable[[], datetime] | None = None,
    startup_announcement: str | None = None,
) -> FastAPI:
    """Build the replaceable M1A browser adapter with injected test seams."""
    package_root = Path(__file__).resolve().parent
    template_root = package_root / "templates"
    static_root = package_root / "static"
    if not template_root.is_dir() or not static_root.is_dir():
        raise RuntimeError("required PAIM web package resources are unavailable")

    clock = now or (lambda: datetime.now(UTC))
    gateway = operational or OperationalApplication(config)
    registry = sessions or SessionRegistry(now=clock)
    runtime = WebRuntime(gateway, registry, expected_origin, operational is None)
    limiter = AttemptLimiter(now=clock)
    environment = Environment(
        loader=FileSystemLoader(template_root),
        autoescape=select_autoescape(("html", "xml")),
        undefined=StrictUndefined,
    )
    templates = Jinja2Templates(env=environment)

    @asynccontextmanager
    async def lifespan(_application: FastAPI) -> AsyncIterator[None]:
        if startup_announcement:
            print(startup_announcement, flush=True)
        try:
            yield
        finally:
            if runtime.owns_operational:
                runtime.operational.close()

    app = FastAPI(
        title="PAIM practitioner foundation",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        lifespan=lifespan,
    )
    app.state.runtime = runtime
    app.state.templates = templates
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1"])
    app.mount("/static", StaticFiles(directory=static_root), name="static")

    @app.exception_handler(AccessDenied)
    async def access_denied(request: Request, _error: AccessDenied) -> Response:
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={
                "request": request,
                "title": "Software access denied",
                "message": (
                    "The requested operation is not available in your current visible scope."
                ),
            },
            status_code=403,
        )

    @app.exception_handler(Exception)
    async def unexpected_failure(request: Request, _error: Exception) -> Response:
        current = registry.get(request.cookies.get(COOKIE_NAME), touch=False)
        reference = (
            current.authentication.correlation_id
            if current is not None and current.authentication is not None
            else None
        )
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={
                "request": request,
                "title": "PAIM could not complete the request",
                "message": "No governed record was changed. Return to Home or sign in again.",
                "reference": reference,
            },
            status_code=500,
        )

    @app.middleware("http")
    async def request_policy(request: Request, call_next: Callable[[Request], Any]) -> Response:
        if request.method == "POST":
            content_length = request.headers.get("content-length")
            if content_length is None or not content_length.isdecimal():
                response = Response("Request body length is required.", status_code=411)
            elif int(content_length) > MAX_REQUEST_BODY:
                response = Response("Request body is too large.", status_code=413)
            else:
                body = await request.body()
                if len(body) > MAX_REQUEST_BODY:
                    response = Response("Request body is too large.", status_code=413)
                else:
                    response = await call_next(request)
        else:
            response = await call_next(request)
        response.headers["Content-Security-Policy"] = _CSP
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        return response

    def render(
        request: Request, name: str, context: dict[str, object], status: int = 200
    ) -> Response:
        return templates.TemplateResponse(
            request=request,
            name=name,
            context={"request": request, **context},
            status_code=status,
        )

    def set_session_cookie(response: Response, identifier: str) -> None:
        response.set_cookie(
            COOKIE_NAME,
            identifier,
            httponly=True,
            secure=False,
            samesite="strict",
            path="/",
            max_age=8 * 60 * 60,
        )

    def clear_session_cookie(response: Response) -> None:
        response.delete_cookie(COOKIE_NAME, path="/", httponly=True, samesite="strict")

    def same_origin(request: Request) -> bool:
        origin = request.headers.get("origin")
        if origin is not None:
            # Referrer-Policy: no-referrer requires browsers to serialize the
            # Origin of a basic HTML form POST as ``null``. In that exact case,
            # trusted Host middleware plus browser Fetch Metadata and the
            # synchronizer token form the same-origin proof. Other null-origin
            # requests remain denied.
            if origin == "null":
                return (
                    request.headers.get("sec-fetch-site") == "same-origin"
                    and request.headers.get("sec-fetch-mode") == "navigate"
                )
            return origin == runtime.expected_origin
        referer = request.headers.get("referer")
        if referer is None:
            return False
        parsed = urlsplit(referer)
        return f"{parsed.scheme}://{parsed.netloc}" == runtime.expected_origin

    def authenticated(request: Request) -> tuple[str, BrowserSession] | None:
        identifier = request.cookies.get(COOKIE_NAME)
        session = registry.get(identifier)
        if session is None or session.authentication is None:
            return None
        try:
            gateway.revalidate_session(session.authentication)
        except AccessDenied:
            registry.invalidate(identifier)
            return None
        return identifier or "", session

    @app.get("/", response_class=HTMLResponse)
    def root() -> Response:
        return RedirectResponse("/home", status_code=303)

    @app.get("/healthz")
    def healthz() -> dict[str, object]:
        report = gateway.health()
        return {"state": report.state.value, "reasons": report.reasons}

    @app.get("/login", response_class=HTMLResponse)
    def login(request: Request) -> Response:
        current = registry.get(request.cookies.get(COOKIE_NAME), touch=False)
        if current is not None and current.authenticated:
            return RedirectResponse("/home", status_code=303)
        if current is None:
            identifier, anonymous = registry.create_anonymous()
        else:
            identifier = request.cookies[COOKIE_NAME]
            anonymous = current
        response = render(
            request,
            "login.html",
            {"csrf_token": anonymous.csrf_secret, "error": None},
        )
        set_session_cookie(response, identifier)
        return response

    @app.post("/session", response_class=HTMLResponse)
    async def create_session(request: Request) -> Response:
        if not same_origin(request):
            return render(
                request,
                "error.html",
                {
                    "title": "Request rejected",
                    "message": "The request origin could not be verified.",
                },
                403,
            )
        identifier = request.cookies.get(COOKIE_NAME)
        anonymous = registry.get(identifier, touch=False)
        if anonymous is None or anonymous.authenticated:
            return RedirectResponse("/login", status_code=303)
        form = await request.form(max_fields=4, max_files=0, max_part_size=4_096)
        principal_id = str(form.get("principal_id", "")).strip()
        credential = str(form.get("credential", ""))
        csrf_token = str(form.get("csrf_token", ""))
        if not registry.verify_csrf(anonymous, csrf_token):
            return render(
                request,
                "error.html",
                {"title": "Request rejected", "message": "The form token was missing or invalid."},
                403,
            )
        if not principal_id or len(principal_id) > 200 or not credential or len(credential) > 4_096:
            return render(
                request,
                "login.html",
                {"csrf_token": anonymous.csrf_secret, "error": GENERIC_AUTHENTICATION_ERROR},
                400,
            )
        throttle_key = (
            f"{request.client.host if request.client else 'local'}:{principal_id.casefold()}"
        )
        if not limiter.allowed(throttle_key):
            return render(
                request,
                "login.html",
                {"csrf_token": anonymous.csrf_secret, "error": GENERIC_AUTHENTICATION_ERROR},
                429,
            )
        try:
            authentication = gateway.authenticate(principal_id, credential)
            if authentication.actor_id is None:
                raise AuthenticationFailed("current Actor mapping is not established")
        except (AuthenticationFailed, AccessDenied):
            limiter.record_failure(throttle_key)
            return render(
                request,
                "login.html",
                {"csrf_token": anonymous.csrf_secret, "error": GENERIC_AUTHENTICATION_ERROR},
                401,
            )
        limiter.clear(throttle_key)
        new_identifier, _authenticated = registry.rotate_authenticated(
            identifier or "", authentication
        )
        response = RedirectResponse("/home", status_code=303)
        set_session_cookie(response, new_identifier)
        return response

    @app.post("/logout", response_class=HTMLResponse)
    async def logout(request: Request) -> Response:
        current = authenticated(request)
        if current is None:
            response = RedirectResponse("/login", status_code=303)
            clear_session_cookie(response)
            return response
        identifier, session = current
        if not same_origin(request):
            return render(
                request,
                "error.html",
                {
                    "title": "Request rejected",
                    "message": "The request origin could not be verified.",
                },
                403,
            )
        form = await request.form(max_fields=1, max_files=0, max_part_size=512)
        if not registry.verify_csrf(session, str(form.get("csrf_token", ""))):
            return render(
                request,
                "error.html",
                {"title": "Request rejected", "message": "The form token was missing or invalid."},
                403,
            )
        registry.invalidate(identifier)
        response = RedirectResponse("/login", status_code=303)
        clear_session_cookie(response)
        return response

    def require_session(request: Request) -> BrowserSession | Response:
        current = authenticated(request)
        if current is None:
            response = RedirectResponse("/login?reason=session", status_code=303)
            clear_session_cookie(response)
            return response
        return current[1]

    @app.get("/home", response_class=HTMLResponse)
    def home(request: Request) -> Response:
        browser_session = require_session(request)
        if isinstance(browser_session, Response):
            return browser_session
        assert browser_session.authentication is not None
        try:
            view = gateway.practitioner_home(browser_session.authentication)
        except AccessDenied:
            registry.invalidate(request.cookies.get(COOKIE_NAME))
            return RedirectResponse("/login?reason=session", status_code=303)
        return render(
            request, "home.html", {"view": view, "csrf_token": browser_session.csrf_secret}
        )

    @app.get("/cases", response_class=HTMLResponse)
    def cases(request: Request, q: str = "") -> Response:
        browser_session = require_session(request)
        if isinstance(browser_session, Response):
            return browser_session
        assert browser_session.authentication is not None
        view = gateway.practitioner_cases(browser_session.authentication, search_text=q[:200])
        return render(
            request, "cases.html", {"view": view, "csrf_token": browser_session.csrf_secret}
        )

    @app.get("/cases/new", response_class=HTMLResponse)
    def new_case(request: Request) -> Response:
        browser_session = require_session(request)
        if isinstance(browser_session, Response):
            return browser_session
        assert browser_session.authentication is not None
        view = gateway.practitioner_cases(browser_session.authentication)
        return render(
            request,
            "case_new.html",
            {
                "view": view,
                "csrf_token": browser_session.csrf_secret,
                "effective_at": clock().astimezone(UTC).isoformat(),
            },
        )

    def render_case_area(request: Request, case_id: str, area: str) -> Response:
        browser_session = require_session(request)
        if isinstance(browser_session, Response):
            return browser_session
        assert browser_session.authentication is not None
        try:
            identity = RecordId.parse(case_id)
        except ValueError:
            return render(
                request, "not_found.html", {"csrf_token": browser_session.csrf_secret}, 404
            )
        view = gateway.practitioner_workspace(browser_session.authentication, identity)
        if view is None:
            return render(
                request, "not_found.html", {"csrf_token": browser_session.csrf_secret}, 404
            )
        templates_by_area = {
            "overview": "case.html",
            "configuration": "case_configuration.html",
            "evidence": "case_evidence.html",
            "assessment": "case_assessment.html",
            "history": "case_history.html",
        }
        template = templates_by_area.get(area)
        if template is None:
            return render(
                request, "not_found.html", {"csrf_token": browser_session.csrf_secret}, 404
            )
        return render(
            request,
            template,
            {
                "view": view,
                "active_area": area,
                "csrf_token": browser_session.csrf_secret,
            },
        )

    @app.get("/cases/{case_id}", response_class=HTMLResponse)
    def case_overview(request: Request, case_id: str) -> Response:
        return render_case_area(request, case_id, "overview")

    @app.get("/cases/{case_id}/{area}", response_class=HTMLResponse)
    def case_work_area(request: Request, case_id: str, area: str) -> Response:
        return render_case_area(request, case_id, area)

    @app.get("/administration", response_class=HTMLResponse)
    def administration(request: Request) -> Response:
        browser_session = require_session(request)
        if isinstance(browser_session, Response):
            return browser_session
        assert browser_session.authentication is not None
        view = gateway.practitioner_home(browser_session.authentication)
        return render(
            request,
            "administration.html",
            {"view": view, "csrf_token": browser_session.csrf_secret},
        )

    register_m1b_routes(
        app,
        gateway=gateway,
        registry=registry,
        render=render,
        require_session=require_session,
        same_origin=same_origin,
        now=clock,
    )

    return app
