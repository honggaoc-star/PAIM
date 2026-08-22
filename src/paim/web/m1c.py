"""M1C browser adapters for explicit Integration, Boundary, and Decision work."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, Response

from paim.application import DomainPreconditionFailed, DomainRuleViolation, StalePrecondition
from paim.application.practitioner import CaseWorkspaceView, GovernedRecordView, ReadState
from paim.domain import (
    BoundaryClauseEffect,
    BoundaryClauseInput,
    BoundarySnapshotVersionInput,
    BoundaryVerificationMode,
    CaseLifecycleState,
    DecisionAuthorizationBasisVersionInput,
    DecisionStatus,
    DecisionVersionInput,
    IntegrationStatus,
    IntegrationVersionInput,
)
from paim.integrity import EffectiveInterval, EventId, RecordId, RecordVersionId
from paim.operational import OperationalApplication
from paim.operational.models import AccessDenied
from paim.web.sessions import ActionIntent, BrowserSession, SessionRegistry

Render = Callable[[Request, str, dict[str, object], int], Response]
RequireSession = Callable[[Request], BrowserSession | Response]
SameOrigin = Callable[[Request], bool]

_ACTIONS = {
    "case.lifecycle.advance",
    "integration.create",
    "boundary.create",
    "decision.propose",
    "decision.authorize",
}

_REQUIRED = {
    "case.lifecycle.advance": ("target_state", "effective_at"),
    "integration.create": (
        "status",
        "reinforcing_effects",
        "conflicts",
        "tradeoffs",
        "remaining_uncertainty",
        "proposed_judgment",
        "accountable_mechanism",
        "rationale",
        "effective_at",
    ),
    "boundary.create": (
        "integration_version_id",
        "status",
        "clause_type",
        "effect",
        "narrative",
        "clause_rationale",
        "provenance",
        "verification_mode",
        "narrative_rationale",
        "effective_at",
    ),
    "decision.propose": (
        "integration_version_id",
        "boundary_snapshot_version_id",
        "status",
        "proposed_action",
        "operating_state",
        "rationale",
        "effective_at",
    ),
    "decision.authorize": (
        "decision_version_id",
        "authority_assignment_version_id",
        "authority_record_version_id",
        "authorized_scope",
        "decision_type",
        "effective_at",
    ),
}
_MULTI_FIELDS = frozenset({"authority_record_version_ids", "authority_gap_version_ids"})


def _timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("an explicit UTC offset is required")
    return parsed.astimezone(UTC)


def _lines(value: str) -> tuple[str, ...]:
    return tuple(line.strip() for line in value.splitlines() if line.strip())


def _version_ids(value: str) -> tuple[RecordVersionId, ...]:
    return tuple(RecordVersionId.parse(item) for item in _lines(value.replace(",", "\n")))


def _record(
    values: tuple[GovernedRecordView, ...], version_id: str, label: str
) -> GovernedRecordView:
    matches = tuple(item for item in values if item.version_id == version_id)
    if len(matches) != 1:
        raise ValueError(f"selected {label} is no longer one exact visible Version")
    return matches[0]


def _governing(view: CaseWorkspaceView) -> tuple[str, str]:
    matches = tuple(item for item in view.configurations if item.is_governing)
    if view.governing_state is not ReadState.ESTABLISHED or len(matches) != 1:
        raise ValueError("one exact governing Configuration is required")
    return matches[0].configuration_id, matches[0].version_id


def _selected_lane(
    view: CaseWorkspaceView, lane_name: str
) -> tuple[GovernedRecordView, GovernedRecordView]:
    lane = view.value if lane_name == "VALUE" else view.risk
    if lane.selection_state is not ReadState.ESTABLISHED or len(lane.selections) != 1:
        raise ValueError(f"one exact {lane_name.title()} selection is required")
    selection = lane.selections[0]
    selected = _record(
        lane.candidates, str(selection.content.get("input_version_id", "")), f"{lane_name} Input"
    )
    if selected.record_id != selection.content.get("input_id"):
        raise ValueError(f"exact {lane_name.title()} Input identity no longer matches selection")
    return selected, selection


def _form_payload(form: object) -> dict[str, str]:
    payload = {
        str(key): str(value).strip()
        for key, value in form.multi_items()  # type: ignore[attr-defined]
        if str(key) != "csrf_token" and str(key) not in _MULTI_FIELDS
    }
    for name in _MULTI_FIELDS:
        values = tuple(
            str(value).strip()
            for value in form.getlist(name)  # type: ignore[attr-defined]
            if str(value).strip()
        )
        if values:
            payload[name] = "\n".join(values)
    return payload


def _expected(payload: dict[str, str]) -> tuple[str, ...]:
    values: list[str] = []
    for name, value in payload.items():
        if name == "new_version_id" or not value:
            continue
        if name.endswith("version_id"):
            values.append(value)
        elif name.endswith("version_ids"):
            values.extend(_lines(value.replace(",", "\n")))
    return tuple(sorted(set(values)))


def _bind(action: str, payload: dict[str, str], view: CaseWorkspaceView) -> None:
    configuration_id, configuration_version_id = _governing(view)
    payload["configuration_id"] = configuration_id
    payload["configuration_version_id"] = configuration_version_id
    if action == "case.lifecycle.advance":
        successors = {
            "open": "configuration_defined",
            "configuration_defined": "evidence_analysis",
            "evidence_analysis": "ready_for_integration",
            "ready_for_integration": "decision_pending",
        }
        target = successors.get(view.lifecycle_state)
        if target is None or payload.get("target_state") != target:
            raise ValueError("submitted lifecycle successor is not the exact permitted next state")
        if target == "ready_for_integration":
            _, value_selection = _selected_lane(view, "VALUE")
            _, risk_selection = _selected_lane(view, "RISK")
            if value_selection.content.get("use_context") != risk_selection.content.get(
                "use_context"
            ) or value_selection.content.get("purpose") != risk_selection.content.get("purpose"):
                raise ValueError("selected Value and Risk use/purpose bindings differ")
            payload["use_context"] = str(value_selection.content["use_context"])
            payload["purpose"] = str(value_selection.content["purpose"])

    elif action == "integration.create":
        value_input, value_selection = _selected_lane(view, "VALUE")
        risk_input, risk_selection = _selected_lane(view, "RISK")
        if value_selection.content.get("use_context") != risk_selection.content.get(
            "use_context"
        ) or value_selection.content.get("purpose") != risk_selection.content.get("purpose"):
            raise ValueError("selected Value and Risk use/purpose bindings differ")
        payload.update(
            value_input_version_id=value_input.version_id,
            value_input_label=value_input.label,
            value_acceptance_version_id=value_selection.version_id,
            value_fitness_version_id=str(value_selection.content["fitness_version_id"]),
            risk_input_version_id=risk_input.version_id,
            risk_input_label=risk_input.label,
            risk_acceptance_version_id=risk_selection.version_id,
            risk_fitness_version_id=str(risk_selection.content["fitness_version_id"]),
            use_context=str(value_selection.content["use_context"]),
            purpose=str(value_selection.content["purpose"]),
        )
        applicability = {
            str(value)
            for selection in (value_selection, risk_selection)
            for value in selection.content.get("material_applicability_version_ids", [])
        }
        for version_id in applicability:
            _record(view.applicability, version_id, "material Applicability")
        payload["material_applicability_version_ids"] = "\n".join(sorted(applicability))
        authority_ids = _lines(payload.get("authority_record_version_ids", ""))
        gap_ids = _lines(payload.get("authority_gap_version_ids", ""))
        for version_id in authority_ids:
            _record(view.authority, version_id, "Authority Record")
        for version_id in gap_ids:
            _record(view.authority_gaps, version_id, "Authority Gap")

    elif action == "boundary.create":
        integration = _record(
            view.decision.integrations, payload.get("integration_version_id", ""), "Integration"
        )
        if integration.state != IntegrationStatus.COMPLETED.value:
            raise ValueError("exact completed Integration is required")
        payload["integration_id"] = integration.record_id

    elif action == "decision.propose":
        integration = _record(
            view.decision.integrations, payload.get("integration_version_id", ""), "Integration"
        )
        boundary = _record(
            view.decision.boundaries, payload.get("boundary_snapshot_version_id", ""), "Boundary"
        )
        if integration.state != IntegrationStatus.COMPLETED.value or boundary.state != "finalized":
            raise ValueError("exact completed Integration and finalized Boundary are required")
        if boundary.content.get("integration_version_id") != integration.version_id:
            raise ValueError("Boundary does not bind the exact selected Integration")
        payload["integration_id"] = integration.record_id
        payload["boundary_snapshot_id"] = boundary.record_id
        for version_id in _lines(payload.get("authority_record_version_ids", "")):
            _record(view.authority, version_id, "Authority Record")
        for version_id in _lines(payload.get("authority_gap_version_ids", "")):
            _record(view.authority_gaps, version_id, "Authority Gap")

    elif action == "decision.authorize":
        decision = _record(
            view.decision.decisions, payload.get("decision_version_id", ""), "Decision proposal"
        )
        if decision.state not in {
            DecisionStatus.PROPOSED.value,
            DecisionStatus.PENDING_AUTHORIZATION.value,
        }:
            raise ValueError("exact current proposed Decision is required")
        assignment = _record(
            view.decision.authority_assignments,
            payload.get("authority_assignment_version_id", ""),
            "Decision Authority assignment",
        )
        authority = _record(
            view.authority, payload.get("authority_record_version_id", ""), "Authority Record"
        )
        if assignment.content.get("paim_actor_id") != view.actor.actor_id:
            raise ValueError("Decision Authority assignment does not name the authenticated Actor")
        payload.update(
            decision_id=decision.record_id,
            decision_authority_identity=view.actor.actor_id,
            integration_version_id=str(decision.content["integration_version_id"]),
            boundary_snapshot_version_id=str(decision.content["boundary_snapshot_version_id"]),
            operating_state=str(decision.content["operating_state"]),
            authority_record_id=authority.record_id,
        )


def _execute(
    gateway: OperationalApplication,
    session: BrowserSession,
    intent: ActionIntent,
    case_id: RecordId,
) -> str:
    assert session.authentication is not None
    auth = session.authentication
    actor_id = auth.actor_id
    assert actor_id is not None
    data = intent.payload
    effective_at = _timestamp(data["effective_at"])
    effective = EffectiveInterval(effective_at)
    configuration_id = RecordId.parse(data["configuration_id"])
    configuration_version_id = RecordVersionId.parse(data["configuration_version_id"])

    if intent.action == "case.lifecycle.advance":
        outcome = gateway.run_command(
            auth,
            action=intent.action,
            idempotency_key=intent.idempotency_key,
            case_id=case_id,
            operation=lambda service, meta: service.transition_case(
                meta,
                case_id=case_id,
                target_state=CaseLifecycleState(data["target_state"]),
                effective_at=effective_at,
                use_context=data.get("use_context") or None,
                purpose=data.get("purpose") or None,
            ),
        )
        if not outcome.accepted:
            raise DomainRuleViolation(outcome.reason)
        return f"/cases/{case_id}/decision"

    if intent.action == "integration.create":
        gateway.run_command(
            auth,
            action=intent.action,
            idempotency_key=intent.idempotency_key,
            case_id=case_id,
            configuration_id=configuration_id,
            operation=lambda service, meta: service.commit_integration(
                meta,
                IntegrationVersionInput(
                    RecordId.parse(data["record_id"]),
                    RecordVersionId.parse(data["new_version_id"]),
                    case_id,
                    configuration_id,
                    configuration_version_id,
                    data["use_context"],
                    data["purpose"],
                    RecordVersionId.parse(data["value_input_version_id"]),
                    RecordVersionId.parse(data["value_acceptance_version_id"]),
                    RecordVersionId.parse(data["value_fitness_version_id"]),
                    RecordVersionId.parse(data["risk_input_version_id"]),
                    RecordVersionId.parse(data["risk_acceptance_version_id"]),
                    RecordVersionId.parse(data["risk_fitness_version_id"]),
                    _version_ids(data["material_applicability_version_ids"]),
                    _lines(data.get("constraint_references", "")),
                    _version_ids(data.get("authority_record_version_ids", "")),
                    _version_ids(data.get("authority_gap_version_ids", "")),
                    actor_id,
                    None,
                    data["accountable_mechanism"],
                    IntegrationStatus(data["status"]),
                    {
                        "reinforcing_effects": data["reinforcing_effects"],
                        "conflicts": data["conflicts"],
                        "tradeoffs": data["tradeoffs"],
                        "remaining_uncertainty": data["remaining_uncertainty"],
                    },
                    tuple({"alternative": line} for line in _lines(data.get("alternatives", ""))),
                    {"judgment": data["proposed_judgment"]},
                    data["rationale"],
                    effective,
                ),
            ),
        )
    elif intent.action == "boundary.create":
        gateway.run_command(
            auth,
            action=intent.action,
            idempotency_key=intent.idempotency_key,
            case_id=case_id,
            configuration_id=configuration_id,
            operation=lambda service, meta: service.commit_boundary_snapshot(
                meta,
                BoundarySnapshotVersionInput(
                    RecordId.parse(data["record_id"]),
                    RecordVersionId.parse(data["new_version_id"]),
                    case_id,
                    configuration_id,
                    configuration_version_id,
                    RecordId.parse(data["integration_id"]),
                    RecordVersionId.parse(data["integration_version_id"]),
                    actor_id,
                    data["status"],
                    (
                        BoundaryClauseInput(
                            RecordId.parse(data["clause_id"]),
                            RecordVersionId.parse(data["clause_version_id"]),
                            data["clause_type"],
                            BoundaryClauseEffect(data["effect"]),
                            data.get("target_reference") or None,
                            data.get("structured_reference") or None,
                            data.get("operator") or None,
                            data.get("structured_value") or None,
                            data.get("unit") or None,
                            data["narrative"],
                            data["clause_rationale"],
                            _lines(data["provenance"]),
                            BoundaryVerificationMode(data["verification_mode"]),
                            data.get("breach_consequence") or None,
                        ),
                    ),
                    data["narrative_rationale"],
                    _lines(data.get("unresolved_items", "")),
                    effective,
                ),
            ),
        )
    elif intent.action == "decision.propose":
        gateway.run_command(
            auth,
            action=intent.action,
            idempotency_key=intent.idempotency_key,
            case_id=case_id,
            configuration_id=configuration_id,
            operation=lambda service, meta: service.commit_decision_proposal(
                meta,
                DecisionVersionInput(
                    RecordId.parse(data["record_id"]),
                    RecordVersionId.parse(data["new_version_id"]),
                    case_id,
                    configuration_id,
                    configuration_version_id,
                    RecordId.parse(data["integration_id"]),
                    RecordVersionId.parse(data["integration_version_id"]),
                    RecordId.parse(data["boundary_snapshot_id"]),
                    RecordVersionId.parse(data["boundary_snapshot_version_id"]),
                    data["proposed_action"],
                    data["operating_state"],
                    data["rationale"],
                    _lines(data.get("conditions_and_limits", "")),
                    (),
                    (),
                    _lines(data.get("alternatives_considered", "")),
                    _lines(data.get("constraint_references", "")),
                    _version_ids(data.get("authority_record_version_ids", "")),
                    _version_ids(data.get("authority_gap_version_ids", "")),
                    _lines(data.get("intervention_declarations", "")),
                    _lines(data.get("learning_declarations", "")),
                    _lines(data.get("reassessment_declarations", "")),
                    DecisionStatus(data["status"]),
                    effective,
                ),
            ),
        )
    elif intent.action == "decision.authorize":
        gateway.run_command(
            auth,
            action=intent.action,
            idempotency_key=intent.idempotency_key,
            case_id=case_id,
            configuration_id=configuration_id,
            claimed_actor_id=actor_id,
            operation=lambda service, meta: service.authorize_decision(
                meta,
                DecisionAuthorizationBasisVersionInput(
                    RecordId.parse(data["record_id"]),
                    RecordVersionId.parse(data["new_version_id"]),
                    RecordId.parse(data["decision_id"]),
                    RecordVersionId.parse(data["decision_version_id"]),
                    data["decision_authority_identity"],
                    RecordVersionId.parse(data["authority_assignment_version_id"]),
                    None,
                    RecordVersionId.parse(data["authority_record_version_id"]),
                    (),
                    data["authorized_scope"],
                    _lines(data.get("limits", "")),
                    configuration_id,
                    configuration_version_id,
                    (data["operating_state"],),
                    data["decision_type"],
                    data.get("organizational_unit") or None,
                    data["authorization_event_id"],
                    actor_id,
                    effective_at,
                    _lines(data.get("conditions", "")),
                    _lines(data.get("dissent", "")),
                    data.get("exception") or None,
                    (),
                    None,
                    effective,
                ),
            ),
        )
    else:
        raise ValueError("unsupported M1C action")
    return f"/cases/{case_id}/decision"


def register_m1c_routes(
    app: FastAPI,
    *,
    gateway: OperationalApplication,
    registry: SessionRegistry,
    render: Render,
    require_session: RequireSession,
    same_origin: SameOrigin,
    now: Callable[[], datetime],
) -> None:
    """Register explicit review/confirm/commit routes for the M1C workspace."""

    def current(request: Request) -> tuple[str, BrowserSession] | Response:
        session = require_session(request)
        if isinstance(session, Response):
            return session
        identifier = request.cookies.get("paim_session")
        return (identifier, session) if identifier else RedirectResponse("/login", status_code=303)

    async def review(request: Request, case_id: str, action: str) -> Response:
        state = current(request)
        if isinstance(state, Response):
            return state
        identifier, session = state
        if not same_origin(request):
            return render(
                request,
                "error.html",
                {"title": "Request rejected", "message": "The request origin was not verified."},
                403,
            )
        form = await request.form(max_fields=50, max_files=0, max_part_size=8_192)
        if not registry.verify_csrf(session, str(form.get("csrf_token", ""))):
            return render(
                request,
                "error.html",
                {"title": "Request rejected", "message": "The form token was invalid."},
                403,
            )
        try:
            identity = RecordId.parse(case_id)
            assert session.authentication is not None
            view = gateway.practitioner_workspace(session.authentication, identity)
            if view is None:
                raise AccessDenied("Case workspace is no longer visible")
            payload = _form_payload(form)
            payload.setdefault("effective_at", now().astimezone(UTC).isoformat())
            missing = tuple(name for name in _REQUIRED[action] if not payload.get(name))
            if missing:
                raise ValueError("required exact input missing: " + ", ".join(missing))
            _bind(action, payload, view)
            payload["record_id"] = str(RecordId.new())
            payload["new_version_id"] = str(RecordVersionId.new())
            if action == "boundary.create":
                payload["clause_id"] = str(RecordId.new())
                payload["clause_version_id"] = str(RecordVersionId.new())
            if action == "decision.authorize":
                payload["authorization_event_id"] = str(EventId.new())
            intent = registry.create_intent(
                identifier, action=action, payload=payload, expected_version_ids=_expected(payload)
            )
        except (AccessDenied, ValueError, KeyError) as error:
            return render(
                request,
                "action_error.html",
                {
                    "view": None,
                    "csrf_token": session.csrf_secret,
                    "title": "Selected exact basis is unavailable",
                    "message": "No governed record was changed.",
                    "details": (str(error),),
                    "return_path": f"/cases/{case_id}/decision",
                },
                409,
            )
        return RedirectResponse(
            f"/cases/{case_id}/{action.replace('.', '-')}/confirm/{intent.intent_id}",
            status_code=303,
        )

    def confirm(request: Request, case_id: str, intent_id: str, action: str) -> Response:
        state = current(request)
        if isinstance(state, Response):
            return state
        identifier, session = state
        intent = registry.intent(identifier, intent_id, action=action)
        if intent is None:
            return render(
                request,
                "action_error.html",
                {
                    "view": None,
                    "csrf_token": session.csrf_secret,
                    "title": "Action intent expired",
                    "message": "Reconstruct the exact Decision workspace before trying again.",
                    "details": (),
                    "return_path": f"/cases/{case_id}/decision",
                },
                409,
            )
        return render(
            request,
            "confirm.html",
            {
                "view": None,
                "csrf_token": session.csrf_secret,
                "intent": intent,
                "commit_path": f"/cases/{case_id}/{action.replace('.', '-')}/commit/{intent_id}",
                "return_path": f"/cases/{case_id}/decision",
            },
            200,
        )

    async def commit(request: Request, case_id: str, intent_id: str, action: str) -> Response:
        state = current(request)
        if isinstance(state, Response):
            return state
        identifier, session = state
        if not same_origin(request):
            return render(
                request,
                "error.html",
                {"title": "Request rejected", "message": "The request origin was not verified."},
                403,
            )
        form = await request.form(max_fields=2, max_files=0, max_part_size=1_024)
        if not registry.verify_csrf(session, str(form.get("csrf_token", ""))):
            return render(
                request,
                "error.html",
                {"title": "Request rejected", "message": "The form token was invalid."},
                403,
            )
        intent = registry.intent(identifier, intent_id, action=action)
        if intent is None:
            return confirm(request, case_id, intent_id, action)
        if intent.outcome_path:
            return RedirectResponse(intent.outcome_path, status_code=303)
        try:
            identity = RecordId.parse(case_id)
            assert session.authentication is not None
            view = gateway.practitioner_workspace(session.authentication, identity)
            if view is None:
                raise AccessDenied("Case workspace is no longer visible")
            rebound = dict(intent.payload)
            _bind(action, rebound, view)
            if _expected(rebound) != intent.expected_version_ids:
                raise StalePrecondition(
                    "the exact authoritative M1C basis changed after confirmation"
                )
            outcome = _execute(gateway, session, replace(intent, payload=rebound), identity)
        except AccessDenied:
            title, status, message = (
                "Software access or exact visibility denied",
                403,
                "Software access and exact governed-context visibility are separate "
                "prerequisites; neither establishes accountability or substantive authority.",
            )
        except (DomainPreconditionFailed, StalePrecondition) as error:
            title, status, message = "Exact Version changed", 409, str(error)
        except DomainRuleViolation as error:
            reason = str(error)
            title = (
                "Accountability or authority is not established"
                if any(word in reason.casefold() for word in ("accountab", "authority"))
                else "Owning PAIM capability rejected the action"
            )
            status, message = 409, reason
        except (ValueError, KeyError) as error:
            title, status, message = "Exact submitted identity is invalid", 400, str(error)
        else:
            registry.record_intent_outcome(identifier, intent_id, outcome_path=outcome)
            return RedirectResponse(outcome, status_code=303)
        return render(
            request,
            "action_error.html",
            {
                "view": None,
                "csrf_token": session.csrf_secret,
                "title": title,
                "message": message,
                "details": ("The production command revalidated the exact submitted basis.",),
                "return_path": f"/cases/{case_id}/decision",
            },
            status,
        )

    def register(action: str) -> None:
        slug = action.replace(".", "-")

        async def review_route(request: Request, case_id: str) -> Response:
            return await review(request, case_id, action)

        def confirm_route(request: Request, case_id: str, intent_id: str) -> Response:
            return confirm(request, case_id, intent_id, action)

        async def commit_route(request: Request, case_id: str, intent_id: str) -> Response:
            return await commit(request, case_id, intent_id, action)

        app.add_api_route(f"/cases/{{case_id}}/{slug}/review", review_route, methods=["POST"])
        app.add_api_route(
            f"/cases/{{case_id}}/{slug}/confirm/{{intent_id}}", confirm_route, methods=["GET"]
        )
        app.add_api_route(
            f"/cases/{{case_id}}/{slug}/commit/{{intent_id}}", commit_route, methods=["POST"]
        )

    for action in sorted(_ACTIONS):
        register(action)
