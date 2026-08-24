"""UX-3B authoritative accountability resolution for governed judgments."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from paim.domain import ApplicabilityTargetType
from paim.integrity import RecordId, RecordVersionId
from paim.operational import AccountabilityCheck, AuthenticatedSession, OperationalApplication


@dataclass(frozen=True, slots=True)
class AccountabilityUnavailable(ValueError):
    """A finalization attempt encountered explicit vacancy or conflict."""

    state: str
    message: str

    def __str__(self) -> str:
        return self.message


_COVERED_ACTIONS = frozenset(
    {
        "evidence.applicability",
        "value-fitness.create",
        "risk-fitness.create",
        "value-input.select",
        "risk-input.select",
    }
)


def covered_accountability_action(action: str) -> bool:
    return action in _COVERED_ACTIONS


def _eligible_functions(action: str, payload: dict[str, str]) -> tuple[str, ...]:
    if action == "evidence.applicability":
        ApplicabilityTargetType(payload["target_type"])
        # The current Role Assignment model has no obligation/purpose/scope discriminator.
        # Only the explicitly named Applicability function can therefore be selected safely;
        # ownership and evaluator labels alone cannot make another assignment eligible.
        return ("Applicability Owner",)
    return ("Value Evaluator",) if action.startswith("value") else ("Risk Evaluator",)


def resolve_payload_accountability(
    gateway: OperationalApplication,
    authentication: AuthenticatedSession,
    *,
    action: str,
    case_id: RecordId,
    payload: dict[str, str],
    effective_at: datetime,
    expected_assignment_version_id: str | None = None,
) -> AccountabilityCheck:
    """Resolve, bind, and optionally revalidate one exact accountability basis."""
    if action not in _COVERED_ACTIONS:
        raise ValueError("action does not use UX-3B accountability resolution")
    payload.pop("accountable_mechanism", None)
    payload.pop("accountable_assignment_version_id", None)
    configuration_id = RecordId.parse(payload["configuration_id"])
    check = gateway.resolve_judgment_accountability(
        authentication,
        case_id=case_id,
        configuration_id=configuration_id,
        eligible_functions=_eligible_functions(action, payload),
        effective_at=effective_at,
    )
    if check.state == "NOT_ESTABLISHED":
        raise AccountabilityUnavailable(
            check.state,
            "Accountability for this judgment has not been established.",
        )
    if check.state == "CONFLICT":
        raise AccountabilityUnavailable(
            check.state,
            "More than one accountability assignment applies and the conflict must be resolved.",
        )
    assignment = check.assignments[0]
    if expected_assignment_version_id is not None and (
        assignment.assignment_version_id != expected_assignment_version_id
    ):
        raise AccountabilityUnavailable(
            "CHANGED",
            "The established accountability for this judgment changed before confirmation.",
        )
    RecordVersionId.parse(assignment.assignment_version_id)
    payload["accountable_assignment_version_id"] = assignment.assignment_version_id
    payload["accountability_label"] = assignment.practitioner_label
    return check
