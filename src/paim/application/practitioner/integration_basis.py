"""Exact browser-read oracle for a current Integration analytical basis."""

from __future__ import annotations

from dataclasses import dataclass

from paim.application.practitioner.models import (
    AnalyticalLaneView,
    GovernedRecordView,
    ReadState,
)


@dataclass(frozen=True, slots=True)
class ExactCurrentIntegrationBasis:
    """The exact current Value/Risk records bound by one Integration."""

    integration: GovernedRecordView
    value_input: GovernedRecordView
    value_selection: GovernedRecordView
    value_fitness: GovernedRecordView
    risk_input: GovernedRecordView
    risk_selection: GovernedRecordView
    risk_fitness: GovernedRecordView
    use_context: str
    purpose: str


def exact_current_integration_basis(
    integration: GovernedRecordView,
    *,
    value: AnalyticalLaneView,
    risk: AnalyticalLaneView,
) -> ExactCurrentIntegrationBasis | None:
    """Return the exact current analytical basis, or ``None`` without substitution."""

    def lane_basis(
        lane: AnalyticalLaneView,
    ) -> tuple[GovernedRecordView, GovernedRecordView, GovernedRecordView] | None:
        if lane.selection_state is not ReadState.ESTABLISHED or len(lane.selections) != 1:
            return None
        selection = lane.selections[0]
        inputs = tuple(
            item
            for item in lane.candidates
            if item.record_id == selection.content.get("input_id")
            and item.version_id == selection.content.get("input_version_id")
        )
        fitness = tuple(
            item
            for item in lane.fitness
            if item.version_id == selection.content.get("fitness_version_id")
        )
        if len(inputs) != 1 or len(fitness) != 1:
            return None
        selected_input, selected_fitness = inputs[0], fitness[0]
        shared = (
            "configuration_version_id",
            "use_context",
            "purpose",
        )
        if (
            selection.content.get("lane") != lane.lane
            or selection.content.get("outcome") != "SELECTED"
            or selected_fitness.content.get("lane") != lane.lane
            or selected_fitness.content.get("input_version_id") != selected_input.version_id
            or selected_fitness.state != "SUPPORTABLE"
            or any(
                selection.content.get(field) != selected_fitness.content.get(field)
                for field in shared
            )
        ):
            return None
        configuration_id = selection.content.get("configuration_id")
        if configuration_id is not None and (
            selected_input.content.get("configuration_id") != configuration_id
        ):
            return None
        if selected_input.content.get("configuration_version_id") != selection.content.get(
            "configuration_version_id"
        ):
            return None
        return selected_input, selection, selected_fitness

    value_basis = lane_basis(value)
    risk_basis = lane_basis(risk)
    if value_basis is None or risk_basis is None or integration.family != "integration":
        return None
    value_input, value_selection, value_fitness = value_basis
    risk_input, risk_selection, risk_fitness = risk_basis
    use_context = value_selection.content.get("use_context")
    purpose = value_selection.content.get("purpose")
    configuration_id = value_selection.content.get("configuration_id")
    configuration_version_id = value_selection.content.get("configuration_version_id")
    if (
        not isinstance(use_context, str)
        or not isinstance(purpose, str)
        or risk_selection.content.get("use_context") != use_context
        or risk_selection.content.get("purpose") != purpose
        or risk_selection.content.get("configuration_id") != configuration_id
        or risk_selection.content.get("configuration_version_id") != configuration_version_id
    ):
        return None
    expected = {
        "configuration_id": configuration_id,
        "configuration_version_id": configuration_version_id,
        "use_context": use_context,
        "purpose": purpose,
        "value_input_version_id": value_input.version_id,
        "value_acceptance_version_id": value_selection.version_id,
        "value_fitness_version_id": value_fitness.version_id,
        "risk_input_version_id": risk_input.version_id,
        "risk_acceptance_version_id": risk_selection.version_id,
        "risk_fitness_version_id": risk_fitness.version_id,
    }
    if any(
        integration.content.get(field) != expected_value
        for field, expected_value in expected.items()
    ):
        return None
    return ExactCurrentIntegrationBasis(
        integration,
        value_input,
        value_selection,
        value_fitness,
        risk_input,
        risk_selection,
        risk_fitness,
        use_context,
        purpose,
    )
