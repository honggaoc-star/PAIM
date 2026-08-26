"""Gate 8 Slice-H practitioner routes over the accepted prospective services."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, Response

from paim.case_continuity import CaseContinuityConflict
from paim.integrity import RecordId, RecordVersionId
from paim.operational import OperationalApplication
from paim.operational.models import AccessDenied
from paim.reconstruction import ReconstructionAccessDenied
from paim.responsibility.models import ObligationKind
from paim.slice_h_actions import SliceHActionContext
from paim.web.sessions import BrowserSession, SessionRegistry

Render = Callable[[Request, str, dict[str, object], int], Response]
RequireSession = Callable[[Request], BrowserSession | Response]
SameOrigin = Callable[[Request], bool]


@dataclass(frozen=True, slots=True)
class SliceHConfirmation:
    title: str
    introduction: str
    fields: tuple[tuple[str, str], ...]
    consequence: str
    button: str


_OBLIGATION_ACTION = {
    ObligationKind.FINISH_VALUE_ASSESSMENT: "assessment.finish.value",
    ObligationKind.FINISH_RISK_ASSESSMENT: "assessment.finish.risk",
    ObligationKind.REVIEW_VALUE_ASSESSMENT_ADEQUACY: "assessment.adequacy.value",
    ObligationKind.REVIEW_RISK_ASSESSMENT_ADEQUACY: "assessment.adequacy.risk",
    ObligationKind.DESIGNATE_VALUE_ASSESSMENT_RELIANCE: "assessment.reliance.value",
    ObligationKind.DESIGNATE_RISK_ASSESSMENT_RELIANCE: "assessment.reliance.risk",
    ObligationKind.COMPLETE_VALUE_RISK_INTEGRATION: "integration.complete",
    ObligationKind.PROPOSE_MANAGEMENT_DECISION: "decision.propose",
    ObligationKind.AUTHORIZE_MANAGEMENT_DECISION: "decision.authorize",
    ObligationKind.CONFIRM_MANAGEMENT_DECISION: "decision.confirm",
    ObligationKind.PLAN_NEXT_REVIEW: "review.plan",
    ObligationKind.BEGIN_CONTINUING_REVIEW: "review.episode.begin",
    ObligationKind.COMPLETE_CONTINUING_REVIEW: "review.episode.complete",
}


def _action_fields(
    action: str, context: SliceHActionContext | None = None
) -> tuple[dict[str, object], ...]:
    if action.startswith("assessment.finish"):
        return (
            {
                "name": "finding",
                "label": "What is the assessment's main finding?",
                "type": "textarea",
            },
            {
                "name": "boundary",
                "label": "What exact use and boundary does it cover?",
                "type": "textarea",
            },
            {"name": "uncertainty", "label": "What remains uncertain?", "type": "textarea"},
            {
                "name": "implication",
                "label": "What does this mean for this bounded decision?",
                "type": "textarea",
            },
            {
                "name": "provenance",
                "label": "What information supports or limits it?",
                "type": "textarea",
            },
            {
                "name": "rationale",
                "label": "Why is it ready for independent review?",
                "type": "textarea",
            },
            {
                "name": "limitations",
                "label": "Limitations (one per line)",
                "type": "textarea",
                "required": False,
            },
        )
    if action.startswith("assessment.adequacy"):
        return (
            {
                "name": "outcome",
                "label": "Is this assessment adequate for the decision being made?",
                "type": "select",
                "options": (
                    ("ADEQUATE", "Yes"),
                    ("NOT_ADEQUATE", "No"),
                    ("INDETERMINATE", "Needs revision"),
                ),
            },
            {"name": "rationale", "label": "Why?", "type": "textarea"},
            {
                "name": "material_reasons",
                "label": "Material reasons if No or Needs revision (one per line)",
                "type": "textarea",
                "required": False,
            },
            {
                "name": "uncertainty",
                "label": "What uncertainty did you consider?",
                "type": "textarea",
            },
            {
                "name": "limitations",
                "label": "Limitations (one per line)",
                "type": "textarea",
                "required": False,
            },
        )
    if action.startswith("assessment.reliance"):
        choice: tuple[dict[str, object], ...] = ()
        if context is not None and len(context.reliance_candidate_version_ids) > 1:
            choice = (
                {
                    "name": "candidate_choice",
                    "label": "Which assessment should be used for this decision?",
                    "type": "select",
                    "options": tuple(
                        (f"candidate-{index}", label)
                        for index, label in enumerate(context.reliance_candidate_labels, start=1)
                    ),
                },
            )
        return (
            *choice,
            {
                "name": "rationale",
                "label": "Why should this exact adequate assessment be used for this decision?",
                "type": "textarea",
            },
        )
    if action == "integration.complete":
        return (
            {
                "name": "rationale",
                "label": (
                    "How should the independent Value and Risk positions be considered together?"
                ),
                "type": "textarea",
            },
            {
                "name": "material_tensions",
                "label": "Material tensions (one per line)",
                "type": "textarea",
                "required": False,
            },
            {
                "name": "limitations",
                "label": "Conditions or limitations (one per line)",
                "type": "textarea",
                "required": False,
            },
            {"name": "uncertainty", "label": "What uncertainty remains?", "type": "textarea"},
            {
                "name": "unresolved_conditions",
                "label": "Unresolved conditions (one per line)",
                "type": "textarea",
                "required": False,
            },
        )
    if action == "decision.propose":
        return (
            {
                "name": "proposed_action",
                "label": "What bounded management action do you propose?",
                "type": "textarea",
            },
            {
                "name": "operating_state",
                "label": "What operating position should apply?",
                "type": "text",
            },
            {"name": "rationale", "label": "Why?", "type": "textarea"},
            {
                "name": "conditions",
                "label": "Conditions and limits (one per line)",
                "type": "textarea",
                "required": False,
            },
            {
                "name": "alternatives",
                "label": "Alternatives considered (one per line)",
                "type": "textarea",
                "required": False,
            },
        )
    if action == "decision.authorize":
        return (
            {
                "name": "authority_identity",
                "label": "What exact authority are you exercising?",
                "type": "text",
            },
            {
                "name": "authority_limits",
                "label": "Authority limits (one per line)",
                "type": "textarea",
                "required": False,
            },
            {
                "name": "conditions",
                "label": "Authorization conditions (one per line)",
                "type": "textarea",
                "required": False,
            },
            {
                "name": "dissent",
                "label": "Recorded dissent (one per line)",
                "type": "textarea",
                "required": False,
            },
        )
    if action == "decision.confirm":
        return (
            {
                "name": "rationale",
                "label": "Why does the exact current Decision remain unchanged?",
                "type": "textarea",
            },
        )
    if action == "review.plan":
        return (
            {
                "name": "review_at",
                "label": "When should this Case next be reviewed?",
                "type": "datetime-local",
            },
            {"name": "rationale", "label": "Why is that timing appropriate?", "type": "textarea"},
        )
    if action == "review.episode.begin":
        return (
            {
                "name": "acknowledgment",
                "label": (
                    "Begin this focused review using the visible reason and exact current basis?"
                ),
                "type": "select",
                "options": (("BEGIN", "Begin focused review"),),
            },
        )
    if action == "review.episode.complete":
        return (
            {
                "name": "rationale",
                "label": "Why is this focused review complete with the current Decision unchanged?",
                "type": "textarea",
            },
        )
    raise ValueError("unsupported contextual action")


def _timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("an explicit UTC offset is required")
    return parsed.astimezone(UTC)


def register_slice_h_routes(
    app: FastAPI,
    *,
    gateway: OperationalApplication,
    registry: SessionRegistry,
    render: Render,
    require_session: RequireSession,
    same_origin: SameOrigin,
    now: Callable[[], datetime],
) -> None:
    """Register only the contextual Slice-H routes; there is no domain navigation."""

    def current(request: Request) -> tuple[str, BrowserSession] | Response:
        session = require_session(request)
        if isinstance(session, Response):
            return session
        identifier = request.cookies.get("paim_session")
        if not identifier:
            return RedirectResponse("/login", status_code=303)
        return identifier, session

    def error(
        request: Request,
        session: BrowserSession,
        *,
        title: str,
        message: str,
        return_path: str,
        status: int,
    ) -> Response:
        return render(
            request,
            "action_error.html",
            {
                "view": None,
                "csrf_token": session.csrf_secret,
                "title": title,
                "message": message,
                "details": ("No governed record was changed by this attempt.",),
                "return_path": return_path,
            },
            status,
        )

    @app.post("/cases/start/review")
    async def review_case_start(request: Request) -> Response:
        state = current(request)
        if isinstance(state, Response):
            return state
        identifier, session = state
        if not same_origin(request):
            return error(
                request,
                session,
                title="Request rejected",
                message="The request origin could not be verified.",
                return_path="/cases/new",
                status=403,
            )
        form = await request.form(max_fields=6, max_files=0, max_part_size=4_096)
        if not registry.verify_csrf(session, str(form.get("csrf_token", ""))):
            return error(
                request,
                session,
                title="Request rejected",
                message="The form token was missing or invalid.",
                return_path="/cases/new",
                status=403,
            )
        payload = {
            name: str(form.get(name, "")).strip()
            for name in ("title", "bounded_use", "setup_description", "effective_at")
        }
        missing = tuple(name for name, value in payload.items() if not value)
        if missing:
            return error(
                request,
                session,
                title="Required information is missing",
                message="Complete the bounded Case description before reviewing it.",
                return_path="/cases/new",
                status=400,
            )
        try:
            _timestamp(payload["effective_at"])
        except ValueError as exc:
            return error(
                request,
                session,
                title="The start time is invalid",
                message=str(exc),
                return_path="/cases/new",
                status=400,
            )
        intent = registry.create_intent(
            identifier,
            action="case.create_open",
            payload=payload,
            expected_version_ids=(),
        )
        return RedirectResponse(f"/cases/start/confirm/{intent.intent_id}", status_code=303)

    @app.get("/cases/start/confirm/{intent_id}")
    def confirm_case_start(request: Request, intent_id: str) -> Response:
        state = current(request)
        if isinstance(state, Response):
            return state
        identifier, session = state
        intent = registry.intent(identifier, intent_id, action="case.create_open")
        if intent is None:
            return error(
                request,
                session,
                title="Case-start review expired",
                message="Return to Cases and reconstruct the request.",
                return_path="/cases/new",
                status=409,
            )
        confirmation = SliceHConfirmation(
            "Start this Case?",
            "Review the bounded AI use. PAIM will create the exact Case context and initial "
            "continuity responsibility through the accepted production command.",
            (
                ("Case", intent.payload["title"]),
                ("AI use", intent.payload["bounded_use"]),
                ("Starting setup or scope", intent.payload["setup_description"]),
            ),
            "This opens one continuing Case and its first governing setup. It does not grant "
            "Value, Risk, Decision, or later operating authority.",
            "Start Case",
        )
        return render(
            request,
            "slice_h_confirm.html",
            {
                "view": None,
                "csrf_token": session.csrf_secret,
                "intent": intent,
                "confirmation": confirmation,
                "commit_path": f"/cases/start/commit/{intent_id}",
                "return_path": "/cases/new",
                "authenticated": True,
            },
            200,
        )

    @app.post("/cases/start/commit/{intent_id}")
    async def commit_case_start(request: Request, intent_id: str) -> Response:
        state = current(request)
        if isinstance(state, Response):
            return state
        identifier, session = state
        if not same_origin(request):
            return error(
                request,
                session,
                title="Request rejected",
                message="The request origin could not be verified.",
                return_path="/cases/new",
                status=403,
            )
        form = await request.form(max_fields=1, max_files=0, max_part_size=1_024)
        if not registry.verify_csrf(session, str(form.get("csrf_token", ""))):
            return error(
                request,
                session,
                title="Request rejected",
                message="The form token was missing or invalid.",
                return_path="/cases/new",
                status=403,
            )
        intent = registry.intent(identifier, intent_id, action="case.create_open")
        if intent is None:
            return confirm_case_start(request, intent_id)
        if intent.outcome_path:
            return RedirectResponse(intent.outcome_path, status_code=303)
        assert session.authentication is not None
        try:
            effective_at = _timestamp(intent.payload["effective_at"])
            outcome = gateway.slice_h_initiate_case(
                session.authentication,
                idempotency_key=intent.idempotency_key,
                title=intent.payload["title"],
                bounded_use=intent.payload["bounded_use"],
                management_question=(
                    "What continuing management attention does this bounded AI use require?"
                ),
                setup_description=intent.payload["setup_description"],
                effective_at=effective_at,
            )
            gateway.slice_h_establish_creator_visibility(
                session.authentication, outcome, effective_at=effective_at
            )
        except AccessDenied as exc:
            return error(
                request,
                session,
                title="Case initiation authority is not established",
                message=str(exc),
                return_path="/cases/new",
                status=403,
            )
        except (CaseContinuityConflict, ValueError) as exc:
            return error(
                request,
                session,
                title="The exact Case-start context changed",
                message=str(exc),
                return_path="/cases/new",
                status=409,
            )
        outcome_path = f"/cases/{outcome.record_id}"
        registry.record_intent_outcome(identifier, intent_id, outcome_path=outcome_path)
        return RedirectResponse(outcome_path, status_code=303)

    @app.get("/cases/{case_id}/tasks/{work_version_id}")
    def contextual_task(request: Request, case_id: str, work_version_id: str) -> Response:
        state = current(request)
        if isinstance(state, Response):
            return state
        _identifier, session = state
        assert session.authentication is not None
        try:
            view = gateway.slice_h_task(
                session.authentication,
                RecordId.parse(case_id),
                RecordVersionId.parse(work_version_id),
            )
            case_view = gateway.slice_h_case(session.authentication, RecordId.parse(case_id))
        except (AccessDenied, ValueError):
            return error(
                request,
                session,
                title="This task is no longer available",
                message="Return to the Case to reconstruct current work. PAIM did not retarget it.",
                return_path=f"/cases/{case_id}",
                status=409,
            )
        return render(
            request,
            "slice_h_task.html",
            {
                "view": view,
                "case_view": case_view,
                "csrf_token": session.csrf_secret,
                "authenticated": True,
            },
            200,
        )

    def action_context(
        request: Request, case_id: str, responsibility_version_id: str
    ) -> tuple[str, BrowserSession, SliceHActionContext, str] | Response:
        state = current(request)
        if isinstance(state, Response):
            return state
        identifier, session = state
        assert session.authentication is not None
        try:
            context = gateway.slice_h_action_context(
                session.authentication,
                RecordId.parse(case_id),
                RecordVersionId.parse(responsibility_version_id),
            )
            action = _OBLIGATION_ACTION[context.obligation]
        except (AccessDenied, KeyError, ValueError):
            return error(
                request,
                session,
                title="This work is no longer available",
                message="Return to the Case to reconstruct the exact current action.",
                return_path=f"/cases/{case_id}",
                status=409,
            )
        return identifier, session, context, action

    @app.get("/cases/{case_id}/actions/{responsibility_version_id}")
    def practitioner_action(
        request: Request, case_id: str, responsibility_version_id: str
    ) -> Response:
        resolved = action_context(request, case_id, responsibility_version_id)
        if isinstance(resolved, Response):
            return resolved
        _identifier, session, context, action = resolved
        assert session.authentication is not None
        case_view = gateway.slice_h_case(session.authentication, RecordId.parse(case_id))
        return render(
            request,
            "slice_h_action.html",
            {
                "view": case_view,
                "context": context,
                "action": action,
                "fields": _action_fields(action, context),
                "csrf_token": session.csrf_secret,
                "review_path": (f"/cases/{case_id}/actions/{responsibility_version_id}/review"),
                "authenticated": True,
            },
            200,
        )

    @app.post("/cases/{case_id}/actions/{responsibility_version_id}/review")
    async def review_practitioner_action(
        request: Request, case_id: str, responsibility_version_id: str
    ) -> Response:
        resolved = action_context(request, case_id, responsibility_version_id)
        if isinstance(resolved, Response):
            return resolved
        identifier, session, context, action = resolved
        if not same_origin(request):
            return error(
                request,
                session,
                title="Request rejected",
                message="The request origin could not be verified.",
                return_path=f"/cases/{case_id}/actions/{responsibility_version_id}",
                status=403,
            )
        fields = _action_fields(action, context)
        form = await request.form(max_fields=16, max_files=0, max_part_size=8_192)
        if not registry.verify_csrf(session, str(form.get("csrf_token", ""))):
            return error(
                request,
                session,
                title="Request rejected",
                message="The form token was missing or invalid.",
                return_path=f"/cases/{case_id}/actions/{responsibility_version_id}",
                status=403,
            )
        payload = {
            str(field["name"]): str(form.get(str(field["name"]), "")).strip() for field in fields
        }
        missing = tuple(
            str(field["label"])
            for field in fields
            if field.get("required", True) and not payload[str(field["name"])]
        )
        if missing:
            return error(
                request,
                session,
                title="Required judgment is incomplete",
                message="Complete: " + "; ".join(missing),
                return_path=f"/cases/{case_id}/actions/{responsibility_version_id}",
                status=400,
            )
        payload.update(
            {
                "case_id": case_id,
                "responsibility_version_id": responsibility_version_id,
                "effective_at": now().astimezone(UTC).isoformat(),
            }
        )
        intent = registry.create_intent(
            identifier,
            action=action,
            payload=payload,
            expected_version_ids=tuple(str(value) for value in context.source_version_ids),
        )
        return RedirectResponse(
            f"/cases/{case_id}/actions/confirm/{intent.intent_id}", status_code=303
        )

    @app.get("/cases/{case_id}/actions/confirm/{intent_id}")
    def confirm_practitioner_action(request: Request, case_id: str, intent_id: str) -> Response:
        state = current(request)
        if isinstance(state, Response):
            return state
        identifier, session = state
        intent = registry.intent_for_actions(
            identifier,
            intent_id,
            actions=frozenset(_OBLIGATION_ACTION.values()),
        )
        if intent is None or intent.payload.get("case_id") != case_id:
            return error(
                request,
                session,
                title="Action review expired",
                message="Return to the Case and reconstruct the current action.",
                return_path=f"/cases/{case_id}",
                status=409,
            )
        shown = tuple(
            (key.replace("_", " ").title(), value)
            for key, value in intent.payload.items()
            if key not in {"case_id", "responsibility_version_id", "effective_at"} and value
        )
        confirmation = SliceHConfirmation(
            "Record this judgment?",
            "Review the practitioner judgment before PAIM revalidates the exact governed context.",
            shown,
            "Only the named governed act is recorded. Related Value, Risk, responsibility, "
            "access, authority, and history facts remain separate.",
            "Record judgment",
        )
        return render(
            request,
            "slice_h_confirm.html",
            {
                "view": None,
                "csrf_token": session.csrf_secret,
                "intent": intent,
                "confirmation": confirmation,
                "commit_path": f"/cases/{case_id}/actions/commit/{intent_id}",
                "return_path": f"/cases/{case_id}",
                "authenticated": True,
            },
            200,
        )

    @app.post("/cases/{case_id}/actions/commit/{intent_id}")
    async def commit_practitioner_action(
        request: Request, case_id: str, intent_id: str
    ) -> Response:
        state = current(request)
        if isinstance(state, Response):
            return state
        identifier, session = state
        if not same_origin(request):
            return error(
                request,
                session,
                title="Request rejected",
                message="The request origin could not be verified.",
                return_path=f"/cases/{case_id}",
                status=403,
            )
        form = await request.form(max_fields=1, max_files=0, max_part_size=1_024)
        if not registry.verify_csrf(session, str(form.get("csrf_token", ""))):
            return error(
                request,
                session,
                title="Request rejected",
                message="The form token was missing or invalid.",
                return_path=f"/cases/{case_id}",
                status=403,
            )
        intent = registry.intent_for_actions(
            identifier,
            intent_id,
            actions=frozenset(_OBLIGATION_ACTION.values()),
        )
        if intent is None or intent.payload.get("case_id") != case_id:
            return confirm_practitioner_action(request, case_id, intent_id)
        if intent.outcome_path:
            return RedirectResponse(intent.outcome_path, status_code=303)
        assert session.authentication is not None
        try:
            effective_at = _timestamp(intent.payload["effective_at"])
            outcome = gateway.slice_h_commit_action(
                session.authentication,
                case_id=RecordId.parse(case_id),
                responsibility_version_id=RecordVersionId.parse(
                    intent.payload["responsibility_version_id"]
                ),
                expected_source_version_ids=tuple(
                    RecordVersionId.parse(value) for value in intent.expected_version_ids
                ),
                action=intent.action,
                payload=intent.payload,
                idempotency_key=intent.idempotency_key,
                effective_at=effective_at,
            )
            gateway.slice_h_establish_result_visibility(
                session.authentication,
                outcome,
                case_id=RecordId.parse(case_id),
                effective_at=effective_at,
            )
        except (AccessDenied, KeyError, RuntimeError, ValueError) as exc:
            return error(
                request,
                session,
                title="The judgment could not be recorded",
                message=str(exc),
                return_path=f"/cases/{case_id}",
                status=409,
            )
        outcome_path = f"/cases/{case_id}"
        registry.record_intent_outcome(identifier, intent_id, outcome_path=outcome_path)
        return RedirectResponse(outcome_path, status_code=303)

    @app.get("/cases/{case_id}/history-decisions")
    def history_decisions(
        request: Request,
        case_id: str,
        effective_at: str = "",
        known_at: str = "",
    ) -> Response:
        state = current(request)
        if isinstance(state, Response):
            return state
        _identifier, session = state
        assert session.authentication is not None
        try:
            current_time = now().astimezone(UTC)
            effective = _timestamp(effective_at) if effective_at else current_time
            known = _timestamp(known_at) if known_at else current_time
            identity = RecordId.parse(case_id)
            timeline = gateway.slice_h_timeline(
                session.authentication,
                identity,
                effective_at=effective,
                known_at=known,
            )
            case_view = gateway.slice_h_case(
                session.authentication,
                identity,
                effective_at=effective,
                known_at=known,
            )
            comparison = (
                gateway.slice_h_comparison(
                    session.authentication,
                    identity,
                    prior_effective_at=effective,
                    prior_known_at=known,
                    current_effective_at=current_time,
                    current_known_at=current_time,
                )
                if effective_at or known_at
                else None
            )
        except (AccessDenied, ReconstructionAccessDenied, ValueError):
            return error(
                request,
                session,
                title="History is not safely available",
                message="The exact requested Case and time context could not be reconstructed.",
                return_path="/cases",
                status=404,
            )
        return render(
            request,
            "slice_h_history.html",
            {
                "view": case_view,
                "timeline": timeline,
                "comparison": comparison,
                "csrf_token": session.csrf_secret,
                "authenticated": True,
            },
            200,
        )


__all__ = ["register_slice_h_routes"]
