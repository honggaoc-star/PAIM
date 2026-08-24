"""UX-3A transient task context and practitioner confirmation presentation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from paim.application.practitioner import (
    AnalyticalAssessmentView,
    CaseWorkspaceView,
    ConfigurationView,
    GovernedRecordView,
)
from paim.domain import ApplicabilityTargetType


@dataclass(frozen=True, slots=True)
class ApplicabilityTaskItem:
    """One exact Evidence-to-Input prerequisite; never a combined judgment."""

    evidence: GovernedRecordView
    applicability: tuple[GovernedRecordView, ...]

    @property
    def resolved(self) -> bool:
        return bool(self.applicability)


@dataclass(frozen=True, slots=True)
class ApplicabilityTaskContext:
    """Read-side-only context reconstructed from current authoritative relations."""

    lane: str
    assessment: AnalyticalAssessmentView
    configuration: ConfigurationView
    items: tuple[ApplicabilityTaskItem, ...]
    selected_item: ApplicabilityTaskItem | None = None

    @property
    def unresolved(self) -> tuple[ApplicabilityTaskItem, ...]:
        return tuple(item for item in self.items if not item.resolved)

    @property
    def resolved_applicability(self) -> tuple[GovernedRecordView, ...]:
        return tuple(applicability for item in self.items for applicability in item.applicability)

    @property
    def reviewed_count(self) -> int:
        return len(self.items) - len(self.unresolved)


def applicability_task_context(
    view: CaseWorkspaceView,
    *,
    lane: str,
    input_version_id: str,
    evidence_version_id: str | None = None,
) -> ApplicabilityTaskContext:
    """Resolve an assessment prerequisite only from exact current visible relations."""
    normalized_lane = lane.upper()
    if normalized_lane not in {"VALUE", "RISK"}:
        raise ValueError("the originating assessment lane is unavailable")
    lane_view = view.value if normalized_lane == "VALUE" else view.risk
    assessments = tuple(
        item
        for item in lane_view.assessments
        if item.input.version_id == input_version_id and item.ready and item.actionable
    )
    if len(assessments) != 1:
        raise ValueError("the assessment waiting for support review is no longer current")
    assessment = assessments[0]
    configuration_version_id = str(assessment.input.content.get("configuration_version_id", ""))
    configurations = tuple(
        item
        for item in view.configurations
        if item.is_governing and item.version_id == configuration_version_id
    )
    if len(configurations) != 1:
        raise ValueError("the setup used for this assessment is no longer current and visible")

    linked_ids = tuple(
        str(value) for value in assessment.input.content.get("evidence_version_ids", ())
    )
    if len(set(linked_ids)) != len(linked_ids):
        raise ValueError("the assessment's information linkage is not one exact set")
    visible_by_version = {item.version_id: item for item in view.evidence}
    if any(version_id not in visible_by_version for version_id in linked_ids):
        raise ValueError("information linked to this assessment is no longer current and visible")

    target_type = (
        ApplicabilityTargetType.VALUE_INPUT_VERSION.value
        if normalized_lane == "VALUE"
        else ApplicabilityTargetType.RISK_INPUT_VERSION.value
    )
    items = tuple(
        ApplicabilityTaskItem(
            visible_by_version[version_id],
            tuple(
                item
                for item in assessment.applicability
                if item.content.get("evidence_version_id") == version_id
                and item.content.get("target_type") == target_type
                and item.content.get("target_id") == assessment.input.record_id
                and item.content.get("target_version_id") == assessment.input.version_id
            ),
        )
        for version_id in linked_ids
    )
    selected_item = None
    if evidence_version_id is not None:
        matches = tuple(
            item
            for item in items
            if item.evidence.version_id == evidence_version_id and not item.resolved
        )
        if len(matches) != 1:
            raise ValueError("the selected information review is no longer unresolved")
        selected_item = matches[0]
    return ApplicabilityTaskContext(
        normalized_lane,
        assessment,
        configurations[0],
        items,
        selected_item,
    )


def assessment_task_contexts(
    view: CaseWorkspaceView,
) -> Mapping[str, ApplicabilityTaskContext]:
    """Build exact contexts for current ready assessments; omit unavailable contexts."""
    contexts: dict[str, ApplicabilityTaskContext] = {}
    for lane_view in (view.value, view.risk):
        for assessment in lane_view.assessments:
            if not assessment.ready or not assessment.actionable:
                continue
            try:
                context = applicability_task_context(
                    view,
                    lane=lane_view.lane,
                    input_version_id=assessment.input.version_id,
                )
            except ValueError:
                continue
            contexts[assessment.input.version_id] = context
    return contexts


@dataclass(frozen=True, slots=True)
class ConfirmationField:
    label: str
    value: str


@dataclass(frozen=True, slots=True)
class ConfirmationPresentation:
    title: str
    introduction: str
    consequence: str
    button: str
    fields: tuple[ConfirmationField, ...]


def _field(payload: Mapping[str, str], key: str, label: str) -> ConfirmationField | None:
    value = payload.get(key, "").strip()
    value = {
        "TRUE": "Yes",
        "FALSE": "No",
        "SUPPORTABLE": "Sufficiently supported for this use",
        "BLOCKED": "Not sufficiently supported for this use",
        "APPLICABLE": "Applies",
        "CONDITIONALLY_APPLICABLE": "Applies under conditions",
        "PARTIALLY_APPLICABLE": "Applies in part",
        "NOT_APPLICABLE": "Does not apply",
        "INDETERMINATE": "Cannot yet determine",
    }.get(value, value)
    return ConfirmationField(label, value) if value else None


def _fields(
    payload: Mapping[str, str], definitions: tuple[tuple[str, str], ...]
) -> tuple[ConfirmationField, ...]:
    return tuple(
        field for key, label in definitions if (field := _field(payload, key, label)) is not None
    )


def confirmation_presentation(action: str, payload: Mapping[str, str]) -> ConfirmationPresentation:
    """Translate an action intent without changing its command or security basis."""
    lane = "Value" if action.startswith("value") else "Risk"
    if action in {"value-input.create", "risk-input.create"}:
        return ConfirmationPresentation(
            f"Review and record {lane} assessment",
            "Review the assessment below before recording it.",
            (
                "This records one independent assessment. It does not determine whether the "
                "assessment is sufficiently supported or choose it for management use."
            ),
            f"Record {lane} assessment",
            _fields(
                payload,
                (
                    ("purpose", "Purpose of this assessment"),
                    ("finding", "Potential Value" if lane == "Value" else "Potential Risk"),
                    ("boundary", f"Where this {lane} applies"),
                    ("uncertainties", "What remains uncertain"),
                    ("implication", f"What this {lane} assessment alone supports"),
                    ("evidence_labels", "Information used"),
                    ("provenance", "How this assessment was produced"),
                ),
            ),
        )
    if action in {"value-input.ready", "risk-input.ready"}:
        return ConfirmationPresentation(
            f"Confirm {lane} assessment is ready for review",
            "Review why this assessment is complete enough for support review.",
            (
                "This marks the assessment ready for support review. It does not determine "
                "whether it is sufficiently supported or choose it for management use."
            ),
            "Mark ready for review",
            _fields(payload, (("input_label", "Assessment"), ("rationale", "Why it is ready"))),
        )
    if action == "evidence.applicability":
        return ConfirmationPresentation(
            "Confirm how this information applies",
            "Review the information-to-assessment judgment before recording it.",
            (
                "This records how this information applies to the assessment. It does not "
                "determine whether the assessment is sufficiently supported."
            ),
            "Record information review",
            _fields(
                payload,
                (
                    ("evidence_label", "Information"),
                    ("target_label", "Assessment"),
                    ("purpose", "Purpose for this review"),
                    ("assessed_scope", "Scope of this judgment"),
                    ("outcome", "Judgment"),
                    ("conditions", "Conditions"),
                    ("limitations", "Limitations"),
                    ("rationale", "Why"),
                    ("accountability_label", "Responsible for this judgment"),
                ),
            ),
        )
    if action in {"value-fitness.create", "risk-fitness.create"}:
        return ConfirmationPresentation(
            f"Confirm whether the {lane} assessment is sufficiently supported",
            "Review the support judgment for the stated use.",
            "This records support for the stated use. It does not choose the assessment.",
            "Record support judgment",
            _fields(
                payload,
                (
                    ("input_label", "Assessment"),
                    ("use_context", "Proposed use"),
                    ("purpose", "Purpose"),
                    ("outcome", "Support judgment"),
                    ("evidence_label", "Information reviewed"),
                    ("applicability_label", "How the information applies"),
                    ("evidence_role", "Role this information plays"),
                    ("required_support", "Is this information required support?"),
                    ("claimed_scope", "Scope supported by this judgment"),
                    ("decision_limiting", "Does this limit a later management decision?"),
                    ("indeterminate_treatment", "Treatment of an indeterminate matter"),
                    ("rationale", "Rationale"),
                    ("accountability_label", "Responsible for this judgment"),
                ),
            ),
        )
    if action in {"value-input.select", "risk-input.select"}:
        return ConfirmationPresentation(
            f"Confirm use of this {lane} assessment",
            "Review the assessment being chosen for the stated use.",
            (
                "This accepts this specific assessment for the stated use and may finalize the "
                "retained assessment. It does not authorize a Decision or operation."
            ),
            f"Choose {lane} assessment",
            _fields(
                payload,
                (
                    ("input_label", "Assessment"),
                    ("use_context", "Proposed use"),
                    ("purpose", "Purpose"),
                    ("fitness_label", "Recorded support judgment"),
                    ("material_applicability_labels", "Information-review basis"),
                    ("rationale", "Why management should use this assessment"),
                    ("accountability_label", "Responsible for this judgment"),
                ),
            ),
        )
    return ConfirmationPresentation(
        "Review and confirm this action",
        "Review what will be recorded before continuing.",
        "PAIM will check the current governed context before recording this action.",
        "Confirm action",
        tuple(
            ConfirmationField(key.replace("_", " ").title(), value)
            for key, value in payload.items()
            if value
            and not key.endswith("_id")
            and not key.endswith("_ids")
            and key
            not in {
                "effective_at",
                "configuration_choice",
                "target_choice",
                "evidence_choice",
            }
        ),
    )
