"""Gate 8 Slice-H practitioner routes over the accepted prospective services."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, Response

from paim.assessment_review import AssessmentLane
from paim.case_continuity import CaseContinuityAccessDenied, CaseContinuityConflict
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
    non_effect: str
    button: str


@dataclass(frozen=True, slots=True)
class SliceHActionPresentation:
    title: str
    introduction: str
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
    if action == "assessment.finish.value":
        return (
            {
                "name": "finding",
                "label": "What improvement or benefit are we expecting?",
                "type": "textarea",
                "help": "Describe the practical result that matters to this management decision.",
            },
            {
                "name": "boundary",
                "label": "How is this AI use expected to contribute, and where might it not?",
                "type": "textarea",
                "help": (
                    "State the substantive limits of the expectation; PAIM already carries "
                    "the Case and setup."
                ),
            },
            {
                "name": "provenance",
                "label": "What information supports or limits that expectation?",
                "type": "textarea",
            },
            {
                "name": "uncertainty",
                "label": "What important uncertainty should the decision maker understand?",
                "type": "textarea",
            },
            {
                "name": "implication",
                "label": "What does this imply for the management decision?",
                "type": "textarea",
            },
            {
                "name": "rationale",
                "label": "Why is this Value assessment ready for independent review?",
                "type": "textarea",
            },
            {
                "name": "limitations",
                "label": "Other important limitations (one per line)",
                "type": "textarea",
                "required": False,
            },
        )
    if action == "assessment.finish.risk":
        return (
            {
                "name": "finding",
                "label": "What could go wrong or require attention?",
                "type": "textarea",
                "help": "Describe the concern without turning it into a score or ranking.",
            },
            {
                "name": "boundary",
                "label": "Under what conditions or circumstances does it matter?",
                "type": "textarea",
                "help": (
                    "State the substantive conditions; PAIM already carries the Case and setup."
                ),
            },
            {
                "name": "rationale",
                "label": "What safeguards or controls reduce or manage the concern?",
                "type": "textarea",
            },
            {
                "name": "provenance",
                "label": "What information supports or limits this assessment?",
                "type": "textarea",
            },
            {
                "name": "uncertainty",
                "label": (
                    "What uncertainty or residual concern should the decision maker understand?"
                ),
                "type": "textarea",
            },
            {
                "name": "implication",
                "label": "What does this imply for the management decision?",
                "type": "textarea",
            },
            {
                "name": "limitations",
                "label": "Other important limitations (one per line)",
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
                "name": "authority_limits",
                "label": "What limits apply to this authorization? (one per line)",
                "type": "textarea",
                "required": False,
            },
            {
                "name": "conditions",
                "label": "What conditions apply? (one per line)",
                "type": "textarea",
                "required": False,
            },
            {
                "name": "dissent",
                "label": "Is there any dissent to record? (one per line)",
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


def _action_presentation(action: str) -> SliceHActionPresentation:
    presentations = {
        "assessment.finish.value": SliceHActionPresentation(
            "Finish the Value assessment",
            (
                "Describe the expected benefit, its support, and what the decision maker "
                "should understand."
            ),
            "Review the Value assessment",
        ),
        "assessment.finish.risk": SliceHActionPresentation(
            "Finish the Risk assessment",
            (
                "Describe the concerns, safeguards, evidence, and residual uncertainty "
                "for this AI use."
            ),
            "Review the Risk assessment",
        ),
        "assessment.adequacy.value": SliceHActionPresentation(
            "Review whether the Value assessment is suitable",
            (
                "Decide whether this assessment is suitable for the management decision "
                "in front of you."
            ),
            "Review the adequacy judgment",
        ),
        "assessment.adequacy.risk": SliceHActionPresentation(
            "Review whether the Risk assessment is suitable",
            (
                "Decide whether this assessment is suitable for the management decision "
                "in front of you."
            ),
            "Review the adequacy judgment",
        ),
        "assessment.reliance.value": SliceHActionPresentation(
            "Choose the Value assessment to use",
            "Make the accountable choice only when more than one suitable assessment is available.",
            "Review the Value choice",
        ),
        "assessment.reliance.risk": SliceHActionPresentation(
            "Choose the Risk assessment to use",
            "Make the accountable choice only when more than one suitable assessment is available.",
            "Review the Risk choice",
        ),
        "integration.complete": SliceHActionPresentation(
            "Consider Value and Risk together",
            (
                "Relate the independent Value and Risk positions in preparation for a "
                "management decision."
            ),
            "Review this consideration",
        ),
        "decision.propose": SliceHActionPresentation(
            "Propose a management decision",
            "State the proposed action, operating position, reasons, and any conditions.",
            "Review the proposal",
        ),
        "decision.authorize": SliceHActionPresentation(
            "Authorize the proposed decision",
            (
                "Record the limits, conditions, or dissent that belong with this separate "
                "authorization."
            ),
            "Review the authorization",
        ),
        "decision.confirm": SliceHActionPresentation(
            "Confirm the current decision",
            "Explain why the current decision remains appropriate after review.",
            "Review the confirmation",
        ),
        "review.plan": SliceHActionPresentation(
            "Plan the next review",
            "Choose a proportionate time to revisit this Case and explain why.",
            "Review the plan",
        ),
        "review.episode.begin": SliceHActionPresentation(
            "Begin a focused review",
            (
                "Open only the review needed for the visible change; no substantive "
                "conclusion is assumed."
            ),
            "Review this step",
        ),
        "review.episode.complete": SliceHActionPresentation(
            "Complete the focused review",
            "Explain why the focused review is complete with the current decision unchanged.",
            "Review the completion",
        ),
    }
    return presentations[action]


def _action_confirmation(action: str, payload: dict[str, str]) -> SliceHConfirmation:
    labels: dict[str, dict[str, str]] = {
        "assessment.finish.value": {
            "finding": "Expected improvement or benefit",
            "implication": "Implication for the decision",
            "uncertainty": "Important uncertainty",
        },
        "assessment.finish.risk": {
            "finding": "Concern requiring attention",
            "implication": "Implication for the decision",
            "uncertainty": "Residual uncertainty",
        },
        "assessment.adequacy.value": {"outcome": "Suitability", "rationale": "Why"},
        "assessment.adequacy.risk": {"outcome": "Suitability", "rationale": "Why"},
        "assessment.reliance.value": {
            "candidate_choice": "Assessment choice",
            "rationale": "Why",
        },
        "assessment.reliance.risk": {
            "candidate_choice": "Assessment choice",
            "rationale": "Why",
        },
        "integration.complete": {
            "rationale": "How Value and Risk were considered",
            "uncertainty": "Remaining uncertainty",
        },
        "decision.propose": {
            "proposed_action": "Proposed action",
            "rationale": "Why",
            "conditions": "Conditions and limits",
        },
        "decision.authorize": {
            "authority_limits": "Authorization limits",
            "conditions": "Conditions",
            "dissent": "Dissent",
        },
        "decision.confirm": {"rationale": "Why the decision remains unchanged"},
        "review.plan": {"review_at": "Next review", "rationale": "Why"},
        "review.episode.begin": {"acknowledgment": "Focused review"},
        "review.episode.complete": {"rationale": "Why the review is complete"},
    }
    copy = {
        "assessment.finish.value": (
            "Record this Value assessment?",
            "Check the expected benefit and the implication for the decision.",
            "The Value assessment becomes ready for a separate suitability review.",
            "Risk, suitability, reliance, and the management decision are not changed.",
            "Record Value assessment",
        ),
        "assessment.finish.risk": (
            "Record this Risk assessment?",
            "Check the concern and the implication for the decision.",
            "The Risk assessment becomes ready for a separate suitability review.",
            "Value, suitability, reliance, and the management decision are not changed.",
            "Record Risk assessment",
        ),
        "assessment.adequacy.value": (
            "Record the Value suitability judgment?",
            "Check whether the Value assessment is suitable for this decision.",
            "This records a separate suitability judgment for the Value assessment.",
            "It does not endorse the Case or alter the assessment or Risk position.",
            "Record Value suitability",
        ),
        "assessment.adequacy.risk": (
            "Record the Risk suitability judgment?",
            "Check whether the Risk assessment is suitable for this decision.",
            "This records a separate suitability judgment for the Risk assessment.",
            "It does not endorse the Case or alter the assessment or Value position.",
            "Record Risk suitability",
        ),
        "assessment.reliance.value": (
            "Use this Value assessment?",
            "Check the accountable assessment choice and its reason.",
            "The chosen Value assessment will be used for this decision purpose.",
            "The assessment itself and the Risk position are not changed.",
            "Record Value choice",
        ),
        "assessment.reliance.risk": (
            "Use this Risk assessment?",
            "Check the accountable assessment choice and its reason.",
            "The chosen Risk assessment will be used for this decision purpose.",
            "The assessment itself and the Value position are not changed.",
            "Record Risk choice",
        ),
        "integration.complete": (
            "Record how Value and Risk were considered?",
            "Check the management judgment that relates the independent positions.",
            "This prepares the Value and Risk basis for a separate decision proposal.",
            "It does not combine the assessments or authorize a decision.",
            "Record consideration",
        ),
        "decision.propose": (
            "Record this decision proposal?",
            "Check the proposed action, reasons, and important conditions.",
            "This creates a proposal for separate authorization.",
            "It does not authorize the proposal or change the Value and Risk assessments.",
            "Record proposal",
        ),
        "decision.authorize": (
            "Authorize this proposed decision?",
            (
                "Check the limits, conditions, and any dissent. PAIM will use the established "
                "authority source."
            ),
            "This records a separate authorization of the current proposal.",
            "It does not change the proposal, Value, Risk, or the source of authority.",
            "Authorize decision",
        ),
        "decision.confirm": (
            "Confirm the current decision?",
            "Check why the decision remains unchanged after review.",
            "This records the accountable unchanged-decision confirmation.",
            "It does not create a replacement decision.",
            "Confirm decision",
        ),
        "review.plan": (
            "Record this review plan?",
            "Check the next review time and why it is proportionate.",
            "This establishes the next planned review point.",
            "It does not create a review conclusion or change the decision.",
            "Record review plan",
        ),
        "review.episode.begin": (
            "Begin this focused review?",
            "Check that the visible change calls for this focused review.",
            "This opens a review limited to the stated focus.",
            "It does not assert a finding or change the decision.",
            "Begin focused review",
        ),
        "review.episode.complete": (
            "Complete this focused review?",
            "Check why the focused review is complete.",
            "This closes the focused review with the current decision unchanged.",
            "It does not create a new decision or a full reassessment.",
            "Complete focused review",
        ),
    }
    title, introduction, consequence, non_effect, button = copy[action]
    shown = tuple(
        (label, payload[name]) for name, label in labels[action].items() if payload.get(name)
    )
    return SliceHConfirmation(title, introduction, shown, consequence, non_effect, button)


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
        assert session.authentication is not None
        if not same_origin(request):
            return error(
                request,
                session,
                title="Request rejected",
                message="The request origin could not be verified.",
                return_path="/cases/new",
                status=403,
            )
        if not gateway.slice_h_case_initiation_available(session.authentication):
            return error(
                request,
                session,
                title="Case start is not available",
                message=(
                    "Your current account does not have an active Case-start mandate. "
                    "Ask a PAIM administrator to establish it before entering Case details."
                ),
                return_path="/cases",
                status=403,
            )
        form = await request.form(max_fields=30, max_files=0, max_part_size=4_096)
        if not registry.verify_csrf(session, str(form.get("csrf_token", ""))):
            return error(
                request,
                session,
                title="Request rejected",
                message="The form token was missing or invalid.",
                return_path="/cases/new",
                status=403,
            )
        limits = {
            "title": 300,
            "ai_name": 300,
            "ai_description": 600,
            "provider_source_type": 300,
            "capabilities": 600,
            "bounded_use": 1_200,
            "management_question": 1_200,
            "setup_description": 2_000,
            "version_model_release": 300,
            "development_context": 400,
            "operating_characteristics": 400,
            "known_strengths_limitations": 500,
            "organizational_experience": 400,
            "other_identifying_information": 400,
            "effective_at": 80,
        }
        payload: dict[str, str] = {}
        for name, limit in limits.items():
            value = str(form.get(name, "")).strip()
            if len(value) > limit:
                return error(
                    request,
                    session,
                    title="One entry is too long",
                    message="Shorten the marked Case information and review it again.",
                    return_path="/cases/new",
                    status=400,
                )
            payload[name] = value
        required = (
            "title",
            "ai_name",
            "ai_description",
            "provider_source_type",
            "capabilities",
            "bounded_use",
            "management_question",
            "setup_description",
            "effective_at",
        )
        missing = tuple(name for name in required if not payload[name])
        if missing:
            return error(
                request,
                session,
                title="Required information is missing",
                message=(
                    "Complete the Case name, AI details, AI use, management question, "
                    "and starting operating context."
                ),
                return_path="/cases/new",
                status=400,
            )
        try:
            effective_at = _timestamp(payload["effective_at"])
        except ValueError as exc:
            return error(
                request,
                session,
                title="The start time is invalid",
                message=str(exc),
                return_path="/cases/new",
                status=400,
            )
        if not gateway.slice_h_case_initiation_available(
            session.authentication,
            bounded_use=payload["bounded_use"],
            effective_at=effective_at,
        ):
            return error(
                request,
                session,
                title="This AI use is outside your Case-start mandate",
                message=(
                    "No Case was created. Ask a PAIM administrator to confirm the current "
                    "organizational mandate for this AI use."
                ),
                return_path="/cases/new",
                status=403,
            )
        dependencies: list[dict[str, str]] = []
        for index in (1, 2):
            name = str(form.get(f"dependency_{index}_name", "")).strip()
            relationship = str(form.get(f"dependency_{index}_type", "")).strip()
            why = str(form.get(f"dependency_{index}_why", "")).strip()
            if any((name, relationship, why)):
                if (
                    not all((name, relationship, why))
                    or relationship not in {"INTERNAL", "EXTERNAL", "MIXED"}
                    or len(name) > 300
                    or len(why) > 500
                ):
                    return error(
                        request,
                        session,
                        title="Dependency information is incomplete",
                        message="Give each dependency a name, relationship, and why it matters.",
                        return_path="/cases/new",
                        status=400,
                    )
                dependencies.append(
                    {"name": name, "relationship_type": relationship, "why_it_matters": why}
                )
        payload["dependencies_json"] = json.dumps(
            dependencies, sort_keys=True, separators=(",", ":")
        )
        prior_intent_id = str(form.get("intent_id", "")).strip()
        intent = registry.create_intent(
            identifier,
            action="case.create_open",
            payload=payload,
            expected_version_ids=(),
        )
        if prior_intent_id:
            registry.discard_intent(identifier, prior_intent_id)
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
        return render(
            request,
            "case_start_review.html",
            {
                "view": None,
                "csrf_token": session.csrf_secret,
                "intent": intent,
                "commit_path": f"/cases/start/commit/{intent_id}",
                "edit_path": f"/cases/start/edit/{intent_id}",
                "cancel_path": f"/cases/start/cancel/{intent_id}",
                "dependencies": json.loads(intent.payload["dependencies_json"]),
                "authenticated": True,
            },
            200,
        )

    @app.get("/cases/start/edit/{intent_id}")
    def edit_case_start(request: Request, intent_id: str) -> Response:
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
                message="Return to Cases and enter the Case information again.",
                return_path="/cases/new",
                status=409,
            )
        assert session.authentication is not None
        return render(
            request,
            "case_new.html",
            {
                "view": gateway.practitioner_cases(session.authentication),
                "csrf_token": session.csrf_secret,
                "effective_at": intent.payload["effective_at"],
                "initiation_available": gateway.slice_h_case_initiation_available(
                    session.authentication
                ),
                "form_values": intent.payload,
                "dependencies": json.loads(intent.payload["dependencies_json"]),
                "intent_id": intent_id,
            },
            200,
        )

    @app.post("/cases/start/cancel/{intent_id}")
    async def cancel_case_start(request: Request, intent_id: str) -> Response:
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
                return_path="/cases",
                status=403,
            )
        form = await request.form(max_fields=1, max_files=0, max_part_size=1_024)
        if not registry.verify_csrf(session, str(form.get("csrf_token", ""))):
            return error(
                request,
                session,
                title="Request rejected",
                message="The form token was missing or invalid.",
                return_path="/cases",
                status=403,
            )
        registry.discard_intent(identifier, intent_id)
        return RedirectResponse("/cases", status_code=303)

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
                management_question=intent.payload["management_question"],
                setup_description=intent.payload["setup_description"],
                effective_at=effective_at,
                ai_profile={
                    "name": intent.payload["ai_name"],
                    "description": intent.payload["ai_description"],
                    "provider_source_type": intent.payload["provider_source_type"],
                    "capabilities": intent.payload["capabilities"],
                    **{
                        name: value
                        for name in (
                            "version_model_release",
                            "development_context",
                            "operating_characteristics",
                            "known_strengths_limitations",
                            "organizational_experience",
                            "other_identifying_information",
                        )
                        if (value := intent.payload[name])
                    },
                },
                dependencies=tuple(json.loads(intent.payload["dependencies_json"])),
            )
            gateway.slice_h_establish_creator_visibility(
                session.authentication, outcome, effective_at=effective_at
            )
        except AccessDenied:
            return error(
                request,
                session,
                title="Case start is no longer available",
                message=(
                    "Your Case-start mandate changed before the Case was started. "
                    "No Case was created; ask a PAIM administrator to confirm your current mandate."
                ),
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
        except (AccessDenied, CaseContinuityAccessDenied, ValueError):
            return error(
                request,
                session,
                title="This task is no longer available",
                message="Return to the Case to reconstruct current work. PAIM did not retarget it.",
                return_path=f"/cases/{case_id}",
                status=409,
            )
        try:
            action_context = gateway.slice_h_action_context(
                session.authentication,
                RecordId.parse(case_id),
                view.responsibility_version_id,
            )
            action_path = (
                f"/cases/{case_id}/actions/{view.responsibility_version_id}"
                if action_context.obligation in _OBLIGATION_ACTION
                else None
            )
        except AccessDenied:
            action_path = None
        return render(
            request,
            "slice_h_task.html",
            {
                "view": view,
                "case_view": case_view,
                "action_path": action_path,
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
                "presentation": _action_presentation(action),
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
        confirmation = _action_confirmation(intent.action, intent.payload)
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
        if intent.action in {"assessment.adequacy.value", "assessment.adequacy.risk"}:
            lane = AssessmentLane.VALUE if intent.action.endswith("value") else AssessmentLane.RISK
            try:
                carried = gateway.slice_h_carry_single_reliance(
                    session.authentication,
                    case_id=RecordId.parse(case_id),
                    lane=lane,
                    effective_at=effective_at,
                    idempotency_key=f"{intent.idempotency_key}-single-reliance",
                )
                if carried is not None:
                    gateway.slice_h_establish_result_visibility(
                        session.authentication,
                        carried,
                        case_id=RecordId.parse(case_id),
                        effective_at=effective_at,
                    )
            except (AccessDenied, KeyError, RuntimeError, ValueError) as exc:
                return render(
                    request,
                    "action_error.html",
                    {
                        "view": None,
                        "csrf_token": session.csrf_secret,
                        "title": "Assessment recorded; next basis was not carried",
                        "message": str(exc),
                        "details": (
                            "The adequacy judgment remains recorded.",
                            "No assessment basis was inferred or partially substituted.",
                        ),
                        "return_path": f"/cases/{case_id}",
                    },
                    409,
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
