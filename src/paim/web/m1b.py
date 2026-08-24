"""Bounded M1B browser command adapters over released PAIM capabilities."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from urllib.parse import urlencode

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, Response

from paim.application import DomainPreconditionFailed, DomainRuleViolation, StalePrecondition
from paim.application.practitioner import CaseWorkspaceView, GovernedRecordView
from paim.domain import (
    AcceptanceSelectionVersionInput,
    AnalyticalInputVersionInput,
    AnalyticalLane,
    ApplicabilityOutcome,
    ApplicabilityTargetType,
    AuthorityGapVersionInput,
    AuthorityVersionInput,
    CaseVersionInput,
    ConfigurationMaturity,
    ConfigurationPurpose,
    ConfigurationVersionInput,
    EvidenceApplicabilityVersionInput,
    EvidenceAttention,
    EvidenceClassification,
    EvidenceVersionInput,
    FitnessOutcome,
    GoverningDesignationInput,
    LaneFitnessVersionInput,
    MaterialEvidenceBasisInput,
)
from paim.integrity import EffectiveInterval, RecordId, RecordVersionId
from paim.operational import OperationalApplication
from paim.operational.models import AccessDenied
from paim.web.sessions import ActionIntent, BrowserSession, SessionRegistry
from paim.web.ux3a import applicability_task_context, confirmation_presentation

Render = Callable[[Request, str, dict[str, object], int], Response]
RequireSession = Callable[[Request], BrowserSession | Response]
SameOrigin = Callable[[Request], bool]


def _timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("an explicit UTC offset is required")
    return parsed.astimezone(UTC)


def _lines(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.splitlines() if item.strip())


def _version_ids(value: str) -> tuple[RecordVersionId, ...]:
    return tuple(RecordVersionId.parse(item) for item in _lines(value.replace(",", "\n")))


def _boolean(value: str) -> bool:
    if value == "TRUE":
        return True
    if value == "FALSE":
        return False
    raise ValueError("boolean value must be exactly TRUE or FALSE")


def _required(payload: dict[str, str], names: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(name for name in names if not payload.get(name, "").strip())


_MULTI_FIELDS = frozenset({"evidence_version_ids", "material_applicability_version_ids"})


def _form_payload(form: object) -> dict[str, str]:
    payload: dict[str, str] = {}
    for key, value in form.multi_items():  # type: ignore[attr-defined]
        name = str(key)
        if name not in _MULTI_FIELDS:
            payload[name] = str(value).strip()
    for name in _MULTI_FIELDS:
        values = tuple(
            str(value).strip()
            for value in form.getlist(name)  # type: ignore[attr-defined]
            if str(value).strip()
        )
        if values:
            payload[name] = "\n".join(values)
    return payload


def _record_by_version(
    values: tuple[GovernedRecordView, ...], version_id: str, description: str
) -> GovernedRecordView:
    matches = tuple(item for item in values if item.version_id == version_id)
    if len(matches) != 1:
        raise ValueError(f"selected {description} is no longer one exact visible Version")
    return matches[0]


def _bind_visible_choices(action: str, payload: dict[str, str], view: CaseWorkspaceView) -> None:
    configuration_choice = payload.get("configuration_choice")
    if action == "configuration.create" and configuration_choice:
        configuration_matches = tuple(
            item for item in view.configurations if item.version_id == configuration_choice
        )
        if len(configuration_matches) != 1:
            raise ValueError("selected Configuration is no longer one exact visible Version")
        selected_configuration = configuration_matches[0]
        payload["configuration_id"] = selected_configuration.configuration_id
        payload["expected_version_id"] = selected_configuration.version_id
        payload["configuration_label"] = str(
            selected_configuration.content.get("system", "Managed Configuration")
        )

    if payload.get("configuration_version_id"):
        bound_configurations = tuple(
            item
            for item in view.configurations
            if item.version_id == payload["configuration_version_id"]
            and item.configuration_id == payload.get("configuration_id")
        )
        if len(bound_configurations) != 1:
            raise ValueError("bound Configuration is no longer one exact visible Version")

    evidence_versions = _lines(payload.get("evidence_version_ids", ""))
    if evidence_versions:
        supporting_evidence = tuple(
            _record_by_version(view.evidence, version_id, "Evidence")
            for version_id in evidence_versions
        )
        payload["evidence_labels"] = "; ".join(item.label for item in supporting_evidence)

    if action == "evidence.applicability":
        if payload.get("task_origin") == "assessment-support":
            context = applicability_task_context(
                view,
                lane=payload.get("origin_lane", ""),
                input_version_id=payload.get("origin_input_version_id", ""),
                evidence_version_id=payload.get("origin_evidence_version_id", ""),
            )
            assert context.selected_item is not None
            expected_evidence = context.selected_item.evidence.version_id
            expected_target = context.assessment.input.version_id
            if (
                payload.get("evidence_choice") != expected_evidence
                or payload.get("target_choice") != expected_target
            ):
                raise ValueError("the carried information-review context was changed")
            payload["origin_lane"] = context.lane
            payload["evidence_choice"] = expected_evidence
            payload["target_choice"] = expected_target
            payload["configuration_id"] = context.configuration.configuration_id
            payload["configuration_version_id"] = context.configuration.version_id
            payload["purpose"] = str(context.assessment.input.content.get("purpose", ""))
        selected_evidence = _record_by_version(
            view.evidence, payload.get("evidence_choice", ""), "Evidence"
        )
        payload["evidence_id"] = selected_evidence.record_id
        payload["evidence_version_id"] = selected_evidence.version_id
        payload["evidence_label"] = selected_evidence.label
        target_version_id = payload.get("target_choice", "")
        configurations = tuple(
            item for item in view.configurations if item.version_id == target_version_id
        )
        candidates = view.value.candidates + view.risk.candidates + view.authority
        targets = tuple(item for item in candidates if item.version_id == target_version_id)
        if len(configurations) + len(targets) != 1:
            raise ValueError("selected governed target is no longer one exact visible Version")
        if configurations:
            target = configurations[0]
            payload["target_type"] = ApplicabilityTargetType.MANAGED_CONFIGURATION_VERSION.value
            payload["target_id"] = target.configuration_id
            payload["target_version_id"] = target.version_id
            payload["target_label"] = str(target.content.get("system", "Managed Configuration"))
        else:
            target_record = targets[0]
            target_types = {
                "value-input": ApplicabilityTargetType.VALUE_INPUT_VERSION,
                "risk-input": ApplicabilityTargetType.RISK_INPUT_VERSION,
                "authority-record": ApplicabilityTargetType.AUTHORITY_RECORD_VERSION,
            }
            target_type = target_types.get(target_record.family)
            if target_type is None:
                raise ValueError("selected governed target type is unsupported")
            payload["target_type"] = target_type.value
            payload["target_id"] = target_record.record_id
            payload["target_version_id"] = target_record.version_id
            payload["target_label"] = target_record.label

    if action.endswith("input.ready"):
        lane = view.value if action.startswith("value") else view.risk
        ready_input = _record_by_version(
            lane.candidates, payload.get("input_version_id", ""), "analytical Input"
        )
        payload["input_label"] = ready_input.label

    if action.endswith("fitness.create"):
        lane = view.value if action.startswith("value") else view.risk
        selected_input = _record_by_version(
            lane.candidates, payload.get("input_version_id", ""), "analytical Input"
        )
        fitness_evidence = _record_by_version(
            view.evidence, payload.get("evidence_version_id", ""), "Evidence"
        )
        fitness_applicability = _record_by_version(
            view.applicability,
            payload.get("applicability_version_id", ""),
            "Applicability determination",
        )
        expected_target_type = (
            ApplicabilityTargetType.VALUE_INPUT_VERSION.value
            if action.startswith("value")
            else ApplicabilityTargetType.RISK_INPUT_VERSION.value
        )
        if (
            fitness_applicability.content.get("evidence_version_id") != fitness_evidence.version_id
            or fitness_applicability.content.get("target_type") != expected_target_type
            or fitness_applicability.content.get("target_id") != selected_input.record_id
            or fitness_applicability.content.get("target_version_id") != selected_input.version_id
        ):
            raise ValueError(
                "selected Applicability does not bind the chosen information to this assessment"
            )
        payload["input_label"] = selected_input.label
        payload["evidence_label"] = fitness_evidence.label
        payload["applicability_label"] = fitness_applicability.label

    if action.endswith("input.select"):
        lane = view.value if action.startswith("value") else view.risk
        selected_input = _record_by_version(
            lane.candidates, payload.get("input_version_id", ""), "analytical Input"
        )
        fitness = _record_by_version(
            lane.fitness, payload.get("fitness_version_id", ""), "fitness determination"
        )
        if fitness.state != FitnessOutcome.SUPPORTABLE.value:
            raise ValueError("selected fitness determination is not SUPPORTABLE")
        if (
            fitness.content.get("input_version_id") != selected_input.version_id
            or fitness.content.get("configuration_version_id")
            != payload.get("configuration_version_id")
            or fitness.content.get("use_context") != payload.get("use_context")
            or fitness.content.get("purpose") != payload.get("purpose")
            or bool(fitness.content.get("decision_limiting"))
        ):
            raise ValueError(
                "selected support review no longer binds this assessment and intended use"
            )
        applicability_ids = _lines(payload.get("material_applicability_version_ids", ""))
        selected_applicability = tuple(
            _record_by_version(view.applicability, value, "Applicability determination")
            for value in applicability_ids
        )
        expected_applicability_ids = {
            str(item.get("applicability_version_id"))
            for item in fitness.content.get("material_evidence", ())
            if isinstance(item, dict) and item.get("applicability_version_id")
        }
        if set(applicability_ids) != expected_applicability_ids:
            raise ValueError(
                "selected assessment must retain the support review's exact Applicability basis"
            )
        payload["input_id"] = selected_input.record_id
        payload["input_label"] = selected_input.label
        payload["fitness_label"] = f"{fitness.state}: {fitness.label}"
        payload["material_applicability_labels"] = "; ".join(
            item.label for item in selected_applicability
        )


def _expected_versions(payload: dict[str, str]) -> tuple[str, ...]:
    values: list[str] = []
    for name, value in payload.items():
        if name == "version_id" or not value:
            continue
        if name.endswith("version_id"):
            values.append(value)
        elif name.endswith("version_ids"):
            values.extend(_lines(value))
    return tuple(sorted(set(values)))


def _return_path(action: str, case_id: RecordId) -> str:
    if action.startswith("configuration"):
        return f"/cases/{case_id}/configuration"
    if action.startswith(("evidence", "authority")):
        return f"/cases/{case_id}/evidence"
    if action.startswith(("value", "risk")):
        return f"/cases/{case_id}/assessment"
    return f"/cases/{case_id}"


def _task_path(case_id: RecordId, payload: dict[str, str]) -> str:
    query = urlencode(
        {
            "task": "assessment-support",
            "lane": payload["origin_lane"],
            "input_version_id": payload["origin_input_version_id"],
            "evidence_version_id": payload["origin_evidence_version_id"],
        }
    )
    return f"/cases/{case_id}/evidence?{query}"


def _intent_return_path(action: str, case_id: RecordId, payload: dict[str, str]) -> str:
    if action == "evidence.applicability" and payload.get("task_origin") == "assessment-support":
        return _task_path(case_id, payload)
    return _return_path(action, case_id)


_REQUIRED: dict[str, tuple[str, ...]] = {
    "case.create": ("title", "effective_at"),
    "configuration.create": ("purpose", "system", "intended_use", "effective_at"),
    "configuration.designate": (
        "configuration_id",
        "configuration_version_id",
        "accountable_mechanism",
        "effective_at",
    ),
    "evidence.create": (
        "configuration_id",
        "configuration_version_id",
        "classification",
        "source",
        "provenance",
        "statement",
        "effective_at",
    ),
    "authority.create": (
        "configuration_id",
        "configuration_version_id",
        "category",
        "source",
        "scope",
        "requirement",
        "provenance",
        "effective_at",
    ),
    "authority-gap.create": (
        "configuration_id",
        "configuration_version_id",
        "question_id",
        "question",
        "scope",
        "rationale",
        "provenance",
        "effective_at",
    ),
    "evidence.applicability": (
        "configuration_id",
        "configuration_version_id",
        "evidence_id",
        "evidence_version_id",
        "target_type",
        "target_id",
        "target_version_id",
        "purpose",
        "assessed_scope",
        "outcome",
        "rationale",
        "accountable_mechanism",
        "effective_at",
    ),
    "value-input.create": (
        "configuration_id",
        "configuration_version_id",
        "purpose",
        "finding",
        "boundary",
        "implication",
        "provenance",
        "effective_at",
    ),
    "risk-input.create": (
        "configuration_id",
        "configuration_version_id",
        "purpose",
        "finding",
        "boundary",
        "implication",
        "provenance",
        "effective_at",
    ),
    "value-input.ready": ("input_version_id", "rationale", "effective_at"),
    "risk-input.ready": ("input_version_id", "rationale", "effective_at"),
    "value-fitness.create": (
        "configuration_id",
        "configuration_version_id",
        "input_version_id",
        "use_context",
        "purpose",
        "outcome",
        "decision_limiting",
        "rationale",
        "accountable_mechanism",
        "evidence_version_id",
        "applicability_version_id",
        "evidence_role",
        "required_support",
        "claimed_scope",
        "effective_at",
    ),
    "risk-fitness.create": (
        "configuration_id",
        "configuration_version_id",
        "input_version_id",
        "use_context",
        "purpose",
        "outcome",
        "decision_limiting",
        "rationale",
        "accountable_mechanism",
        "evidence_version_id",
        "applicability_version_id",
        "evidence_role",
        "required_support",
        "claimed_scope",
        "effective_at",
    ),
    "value-input.select": (
        "configuration_id",
        "configuration_version_id",
        "input_id",
        "input_version_id",
        "fitness_version_id",
        "use_context",
        "purpose",
        "rationale",
        "accountable_mechanism",
        "material_applicability_version_ids",
        "effective_at",
    ),
    "risk-input.select": (
        "configuration_id",
        "configuration_version_id",
        "input_id",
        "input_version_id",
        "fitness_version_id",
        "use_context",
        "purpose",
        "rationale",
        "accountable_mechanism",
        "material_applicability_version_ids",
        "effective_at",
    ),
}


def _new_identities(action: str, payload: dict[str, str]) -> None:
    if action == "case.create":
        payload["case_id"] = str(RecordId.new())
        payload["version_id"] = str(RecordVersionId.new())
    elif action != "value-input.ready" and action != "risk-input.ready":
        if action == "configuration.create" and payload.get("configuration_id"):
            pass
        else:
            payload.setdefault("record_id", str(RecordId.new()))
        payload["version_id"] = str(RecordVersionId.new())


def _lane(action: str) -> AnalyticalLane:
    return AnalyticalLane.VALUE if action.startswith("value") else AnalyticalLane.RISK


def _execute(
    gateway: OperationalApplication,
    session: BrowserSession,
    intent: ActionIntent,
    case_id: RecordId | None,
) -> str:
    assert session.authentication is not None
    authentication = session.authentication
    assert authentication.actor_id is not None
    actor_id = authentication.actor_id
    data = intent.payload
    effective_at = _timestamp(data["effective_at"])
    effective = EffectiveInterval(effective_at)
    configuration_id = (
        RecordId.parse(data["configuration_id"]) if data.get("configuration_id") else None
    )

    if intent.action == "case.create":
        identity = RecordId.parse(data["case_id"])
        gateway.run_command(
            authentication,
            action=intent.action,
            idempotency_key=intent.idempotency_key,
            operation=lambda service, meta: service.commit_case(
                meta,
                CaseVersionInput(
                    identity,
                    RecordVersionId.parse(data["version_id"]),
                    data["title"],
                    effective,
                ),
            ),
        )
        return f"/cases/{identity}"

    assert case_id is not None
    if intent.action == "configuration.create":
        identity = (
            RecordId.parse(data["configuration_id"])
            if data.get("configuration_id")
            else RecordId.parse(data["record_id"])
        )
        expected = (
            RecordVersionId.parse(data["expected_version_id"])
            if data.get("expected_version_id")
            else None
        )
        gateway.run_command(
            authentication,
            action=intent.action,
            idempotency_key=intent.idempotency_key,
            case_id=case_id,
            operation=lambda service, meta: service.commit_configuration(
                meta,
                ConfigurationVersionInput(
                    identity,
                    RecordVersionId.parse(data["version_id"]),
                    case_id,
                    ConfigurationMaturity.FINALIZED,
                    ConfigurationPurpose(data["purpose"]),
                    {
                        "system": data["system"],
                        "intended_use": data["intended_use"],
                        "users": data.get("users", ""),
                        "workflow": data.get("workflow", ""),
                        "conditions": data.get("conditions", ""),
                        "exclusions": data.get("exclusions", ""),
                    },
                    effective,
                    expected,
                    data.get("relationship_reason") or None,
                ),
            ),
        )
        return _return_path(intent.action, case_id)

    if intent.action.endswith("input.ready"):
        gateway.run_command(
            authentication,
            action=intent.action,
            idempotency_key=intent.idempotency_key,
            case_id=case_id,
            operation=lambda service, meta: service.mark_input_ready(
                meta,
                input_version_id=RecordVersionId.parse(data["input_version_id"]),
                effective_at=effective_at,
                rationale=data["rationale"],
            ),
        )
        return _return_path(intent.action, case_id)

    assert configuration_id is not None
    configuration_version_id = RecordVersionId.parse(data["configuration_version_id"])
    if intent.action == "configuration.designate":
        gateway.run_command(
            authentication,
            action=intent.action,
            idempotency_key=intent.idempotency_key,
            case_id=case_id,
            configuration_id=configuration_id,
            operation=lambda service, meta: service.commit_governing_designation(
                meta,
                GoverningDesignationInput(
                    RecordId.parse(data["record_id"]),
                    RecordVersionId.parse(data["version_id"]),
                    case_id,
                    configuration_version_id,
                    effective,
                    None,
                    data["accountable_mechanism"],
                ),
            ),
        )
    elif intent.action == "evidence.create":
        observed = _timestamp(data["observed_as_of"]) if data.get("observed_as_of") else None
        gateway.run_command(
            authentication,
            action=intent.action,
            idempotency_key=intent.idempotency_key,
            case_id=case_id,
            configuration_id=configuration_id,
            operation=lambda service, meta: service.commit_evidence(
                meta,
                EvidenceVersionInput(
                    RecordId.parse(data["record_id"]),
                    RecordVersionId.parse(data["version_id"]),
                    case_id,
                    configuration_id,
                    configuration_version_id,
                    EvidenceClassification(data["classification"]),
                    data["source"],
                    {"source": data["provenance"]},
                    {"statement": data["statement"]},
                    observed,
                    effective,
                    EvidenceAttention(data.get("attention", "current")),
                ),
            ),
        )
    elif intent.action == "authority.create":
        gateway.run_command(
            authentication,
            action=intent.action,
            idempotency_key=intent.idempotency_key,
            case_id=case_id,
            configuration_id=configuration_id,
            operation=lambda service, meta: service.commit_authority_record(
                meta,
                AuthorityVersionInput(
                    RecordId.parse(data["record_id"]),
                    RecordVersionId.parse(data["version_id"]),
                    case_id,
                    configuration_id,
                    configuration_version_id,
                    data["category"],
                    data["source"],
                    {"source": data["provenance"]},
                    data["scope"],
                    data["requirement"],
                    {"notes": data.get("notes", "")},
                    effective,
                    _version_ids(data.get("evidence_version_ids", "")),
                ),
            ),
        )
    elif intent.action == "authority-gap.create":
        gateway.run_command(
            authentication,
            action=intent.action,
            idempotency_key=intent.idempotency_key,
            case_id=case_id,
            configuration_id=configuration_id,
            operation=lambda service, meta: service.commit_authority_gap(
                meta,
                AuthorityGapVersionInput(
                    RecordId.parse(data["record_id"]),
                    RecordVersionId.parse(data["version_id"]),
                    case_id,
                    configuration_id,
                    configuration_version_id,
                    data["question_id"],
                    data["question"],
                    data["scope"],
                    data["rationale"],
                    {"source": data["provenance"]},
                    effective,
                    _version_ids(data.get("evidence_version_ids", "")),
                ),
            ),
        )
    elif intent.action == "evidence.applicability":
        gateway.run_command(
            authentication,
            action=intent.action,
            idempotency_key=intent.idempotency_key,
            case_id=case_id,
            configuration_id=configuration_id,
            operation=lambda service, meta: service.commit_evidence_applicability(
                meta,
                EvidenceApplicabilityVersionInput(
                    RecordId.parse(data["record_id"]),
                    RecordVersionId.parse(data["version_id"]),
                    RecordId.parse(data["evidence_id"]),
                    RecordVersionId.parse(data["evidence_version_id"]),
                    ApplicabilityTargetType(data["target_type"]),
                    data["target_id"],
                    RecordVersionId.parse(data["target_version_id"]),
                    data["purpose"],
                    data["assessed_scope"],
                    case_id,
                    configuration_id,
                    configuration_version_id,
                    ApplicabilityOutcome(data["outcome"]),
                    _lines(data.get("conditions", "")),
                    _lines(data.get("limitations", "")),
                    data["rationale"],
                    actor_id,
                    None,
                    data["accountable_mechanism"],
                    effective,
                ),
            ),
        )
    elif intent.action.endswith("input.create"):
        lane = _lane(intent.action)
        gateway.run_command(
            authentication,
            action=intent.action,
            idempotency_key=intent.idempotency_key,
            case_id=case_id,
            configuration_id=configuration_id,
            operation=lambda service, meta: service.commit_analytical_input(
                meta,
                AnalyticalInputVersionInput(
                    RecordId.parse(data["record_id"]),
                    RecordVersionId.parse(data["version_id"]),
                    lane,
                    case_id,
                    configuration_id,
                    configuration_version_id,
                    data["purpose"],
                    data["finding"],
                    data["boundary"],
                    _lines(data.get("uncertainties", "")),
                    data["implication"],
                    {"source": data["provenance"]},
                    _version_ids(data.get("evidence_version_ids", "")),
                    effective,
                ),
            ),
        )
    elif intent.action.endswith("fitness.create"):
        lane = _lane(intent.action)
        basis = MaterialEvidenceBasisInput(
            RecordVersionId.parse(data["evidence_version_id"]),
            RecordVersionId.parse(data["applicability_version_id"]),
            data["evidence_role"],
            _boolean(data["required_support"]),
            data["claimed_scope"],
        )
        gateway.run_command(
            authentication,
            action=intent.action,
            idempotency_key=intent.idempotency_key,
            case_id=case_id,
            configuration_id=configuration_id,
            operation=lambda service, meta: service.commit_lane_fitness(
                meta,
                LaneFitnessVersionInput(
                    RecordId.parse(data["record_id"]),
                    RecordVersionId.parse(data["version_id"]),
                    lane,
                    RecordVersionId.parse(data["input_version_id"]),
                    case_id,
                    configuration_id,
                    configuration_version_id,
                    data["use_context"],
                    data["purpose"],
                    FitnessOutcome(data["outcome"]),
                    data["rationale"],
                    data.get("indeterminate_treatment") or None,
                    _boolean(data["decision_limiting"]),
                    None,
                    data["accountable_mechanism"],
                    (basis,),
                    effective,
                ),
            ),
        )
    elif intent.action.endswith("input.select"):
        lane = _lane(intent.action)
        gateway.run_command(
            authentication,
            action=intent.action,
            idempotency_key=intent.idempotency_key,
            case_id=case_id,
            configuration_id=configuration_id,
            operation=lambda service, meta: service.commit_acceptance_selection(
                meta,
                AcceptanceSelectionVersionInput(
                    RecordId.parse(data["record_id"]),
                    RecordVersionId.parse(data["version_id"]),
                    lane,
                    RecordId.parse(data["input_id"]),
                    RecordVersionId.parse(data["input_version_id"]),
                    case_id,
                    configuration_id,
                    configuration_version_id,
                    data["use_context"],
                    data["purpose"],
                    data["rationale"],
                    None,
                    data["accountable_mechanism"],
                    RecordVersionId.parse(data["fitness_version_id"]),
                    _version_ids(data["material_applicability_version_ids"]),
                    effective,
                ),
            ),
        )
    else:
        raise ValueError("unsupported M1B action")
    if (
        intent.action == "evidence.applicability"
        and data.get("task_origin") == "assessment-support"
    ):
        current_view = gateway.practitioner_workspace(authentication, case_id)
        if current_view is None:
            raise AccessDenied("Case workspace is no longer visible")
        context = applicability_task_context(
            current_view,
            lane=data["origin_lane"],
            input_version_id=data["origin_input_version_id"],
        )
        if context.unresolved:
            next_payload = {
                **data,
                "origin_evidence_version_id": context.unresolved[0].evidence.version_id,
            }
            return _task_path(case_id, next_payload)
        return f"/cases/{case_id}/assessment#{context.lane.casefold()}-work"
    return _return_path(intent.action, case_id)


def register_m1b_routes(
    app: FastAPI,
    *,
    gateway: OperationalApplication,
    registry: SessionRegistry,
    render: Render,
    require_session: RequireSession,
    same_origin: SameOrigin,
    now: Callable[[], datetime],
) -> None:
    """Register explicit resource/action routes; there is no generic mutation endpoint."""

    def current(request: Request) -> tuple[str, BrowserSession] | Response:
        session = require_session(request)
        if isinstance(session, Response):
            return session
        identifier = request.cookies.get("paim_session")
        if not identifier:
            return RedirectResponse("/login", status_code=303)
        return identifier, session

    def action_return_path(action: str, case_id_text: str | None) -> str:
        if case_id_text is None:
            return "/cases/new"
        try:
            return _return_path(action, RecordId.parse(case_id_text))
        except ValueError:
            return "/cases"

    async def review(request: Request, action: str, case_id_text: str | None) -> Response:
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
        form = await request.form(max_fields=40, max_files=0, max_part_size=8_192)
        if not registry.verify_csrf(session, str(form.get("csrf_token", ""))):
            return render(
                request,
                "error.html",
                {"title": "Request rejected", "message": "The form token was invalid."},
                403,
            )
        payload = _form_payload(form)
        payload.pop("csrf_token", None)
        payload.setdefault("effective_at", now().astimezone(UTC).isoformat())
        if case_id_text is not None:
            assert session.authentication is not None
            try:
                case_id = RecordId.parse(case_id_text)
                view = gateway.practitioner_workspace(session.authentication, case_id)
                if view is None:
                    raise ValueError("Case workspace is no longer visible")
                _bind_visible_choices(action, payload, view)
            except (AccessDenied, ValueError) as error:
                return render(
                    request,
                    "action_error.html",
                    {
                        "view": None,
                        "csrf_token": session.csrf_secret,
                        "title": "Selected source is unavailable",
                        "message": "No governed record was changed.",
                        "details": (str(error),),
                        "return_path": action_return_path(action, case_id_text),
                    },
                    409,
                )
        missing = _required(payload, _REQUIRED[action])
        if missing:
            return render(
                request,
                "action_error.html",
                {
                    "view": None,
                    "csrf_token": session.csrf_secret,
                    "title": "Required exact inputs are missing",
                    "message": "No governed record was changed.",
                    "details": tuple(f"{name} is required" for name in missing),
                    "return_path": action_return_path(action, case_id_text),
                },
                400,
            )
        _new_identities(action, payload)
        intent = registry.create_intent(
            identifier,
            action=action,
            payload=payload,
            expected_version_ids=_expected_versions(payload),
        )
        prefix = f"/cases/{case_id_text}" if case_id_text else "/cases"
        return RedirectResponse(
            f"{prefix}/{action.replace('.', '-')}/confirm/{intent.intent_id}", status_code=303
        )

    def confirm(
        request: Request, action: str, intent_id: str, case_id_text: str | None
    ) -> Response:
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
                    "message": "Reconstruct the authoritative workspace before trying again.",
                    "details": (),
                    "return_path": action_return_path(action, case_id_text),
                },
                409,
            )
        prefix = f"/cases/{case_id_text}" if case_id_text else "/cases"
        case_identity = RecordId.parse(case_id_text) if case_id_text else None
        return_path = (
            _intent_return_path(action, case_identity, intent.payload)
            if case_identity is not None
            else action_return_path(action, case_id_text)
        )
        return render(
            request,
            "confirm.html",
            {
                "view": None,
                "csrf_token": session.csrf_secret,
                "intent": intent,
                "confirmation": confirmation_presentation(action, intent.payload),
                "commit_path": (f"{prefix}/{action.replace('.', '-')}/commit/{intent.intent_id}"),
                "return_path": return_path,
            },
            200,
        )

    async def commit(
        request: Request, action: str, intent_id: str, case_id_text: str | None
    ) -> Response:
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
            return confirm(request, action, intent_id, case_id_text)
        if intent.outcome_path:
            return RedirectResponse(intent.outcome_path, status_code=303)
        try:
            case_id = RecordId.parse(case_id_text) if case_id_text else None
            if case_id is not None:
                assert session.authentication is not None
                view = gateway.practitioner_workspace(session.authentication, case_id)
                if view is None:
                    raise AccessDenied("Case workspace is no longer visible")
                try:
                    _bind_visible_choices(action, intent.payload, view)
                except ValueError as error:
                    raise StalePrecondition(str(error)) from error
            outcome = _execute(gateway, session, intent, case_id)
        except AccessDenied:
            title, status = "Software access or exact visibility denied", 403
            message = (
                "Software permission and governed-context visibility are separate prerequisites; "
                "neither establishes accountability or substantive authority."
            )
        except (DomainPreconditionFailed, StalePrecondition) as error:
            title, status = "Exact Version changed", 409
            message = (
                f"The expected exact Version no longer matches authoritative current state. {error}"
            )
        except DomainRuleViolation as error:
            reason = str(error)
            if "already ready" in reason.casefold() or "already frozen" in reason.casefold():
                title = "Exact analytical state changed"
            elif "accountab" in reason.casefold():
                title = "Accountability vacancy or conflict"
            elif "authority" in reason.casefold():
                title = "Authority is not established"
            elif "conflict" in reason.casefold():
                title = "Explicit governed-state conflict"
            else:
                title = "Owning PAIM capability rejected the action"
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
                "details": (
                    "Why: the authoritative command revalidated the exact submitted basis.",
                    "What can legitimately change it: use the named owning-domain action after "
                    "the missing prerequisite is established.",
                ),
                "return_path": (
                    _intent_return_path(action, case_id, intent.payload)
                    if case_id is not None
                    else action_return_path(action, case_id_text)
                ),
            },
            status,
        )

    def register(action: str, slug: str) -> None:
        async def review_case(request: Request, case_id: str) -> Response:
            return await review(request, action, case_id)

        def confirm_case(request: Request, case_id: str, intent_id: str) -> Response:
            return confirm(request, action, intent_id, case_id)

        async def commit_case(request: Request, case_id: str, intent_id: str) -> Response:
            return await commit(request, action, intent_id, case_id)

        app.add_api_route(
            f"/cases/{{case_id}}/{slug}/review",
            review_case,
            methods=["POST"],
            name=f"m1b_{slug.replace('/', '_')}_review",
        )
        app.add_api_route(
            f"/cases/{{case_id}}/{action.replace('.', '-')}/confirm/{{intent_id}}",
            confirm_case,
            methods=["GET"],
            name=f"m1b_{slug.replace('/', '_')}_confirm",
        )
        app.add_api_route(
            f"/cases/{{case_id}}/{action.replace('.', '-')}/commit/{{intent_id}}",
            commit_case,
            methods=["POST"],
            name=f"m1b_{slug.replace('/', '_')}_commit",
        )

    async def review_new_case(request: Request) -> Response:
        return await review(request, "case.create", None)

    def confirm_new_case(request: Request, intent_id: str) -> Response:
        return confirm(request, "case.create", intent_id, None)

    async def commit_new_case(request: Request, intent_id: str) -> Response:
        return await commit(request, "case.create", intent_id, None)

    app.add_api_route("/cases/new/review", review_new_case, methods=["POST"])
    app.add_api_route("/cases/case-create/confirm/{intent_id}", confirm_new_case, methods=["GET"])
    app.add_api_route("/cases/case-create/commit/{intent_id}", commit_new_case, methods=["POST"])
    for action, slug in (
        ("configuration.create", "configuration"),
        ("configuration.designate", "configuration/designation"),
        ("evidence.create", "evidence"),
        ("authority.create", "authority"),
        ("authority-gap.create", "authority-gap"),
        ("evidence.applicability", "applicability"),
        ("value-input.create", "value/input"),
        ("value-input.ready", "value/readiness"),
        ("value-fitness.create", "value/fitness"),
        ("value-input.select", "value/selection"),
        ("risk-input.create", "risk/input"),
        ("risk-input.ready", "risk/readiness"),
        ("risk-fitness.create", "risk/fitness"),
        ("risk-input.select", "risk/selection"),
    ):
        register(action, slug)
