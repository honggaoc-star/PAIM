"""Controlled Responsibility and Work vocabulary for Gate 8 Slice A."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum

from paim.integrity.ids import RecordId
from paim.integrity.semantics import ExactContextSet, SemanticContractRef


class PracticalRole(StrEnum):
    CASE_COORDINATOR = "CASE_COORDINATOR"
    ASSESSOR = "ASSESSOR"
    REVIEWER = "REVIEWER"


class ObligationKind(StrEnum):
    COORDINATE_CASE = "COORDINATE_CASE"
    DETERMINE_CASE_CONTINUITY = "DETERMINE_CASE_CONTINUITY"
    MAINTAIN_CONFIGURATION_CONTEXT = "MAINTAIN_CONFIGURATION_CONTEXT"
    PRODUCE_VALUE_INPUT = "PRODUCE_VALUE_INPUT"
    PRODUCE_RISK_INPUT = "PRODUCE_RISK_INPUT"
    FINISH_VALUE_ASSESSMENT = "FINISH_VALUE_ASSESSMENT"
    FINISH_RISK_ASSESSMENT = "FINISH_RISK_ASSESSMENT"
    REVIEW_VALUE_ASSESSMENT_ADEQUACY = "REVIEW_VALUE_ASSESSMENT_ADEQUACY"
    REVIEW_RISK_ASSESSMENT_ADEQUACY = "REVIEW_RISK_ASSESSMENT_ADEQUACY"
    DESIGNATE_VALUE_ASSESSMENT_RELIANCE = "DESIGNATE_VALUE_ASSESSMENT_RELIANCE"
    DESIGNATE_RISK_ASSESSMENT_RELIANCE = "DESIGNATE_RISK_ASSESSMENT_RELIANCE"
    JUDGE_EVIDENCE_APPLICABILITY = "JUDGE_EVIDENCE_APPLICABILITY"
    ACCEPT_VALUE_INPUT_FOR_USE = "ACCEPT_VALUE_INPUT_FOR_USE"
    ACCEPT_RISK_INPUT_FOR_USE = "ACCEPT_RISK_INPUT_FOR_USE"
    COMPLETE_VALUE_RISK_INTEGRATION = "COMPLETE_VALUE_RISK_INTEGRATION"
    RESOLVE_AUTHORITY_QUESTION = "RESOLVE_AUTHORITY_QUESTION"
    DETERMINE_TRIGGER = "DETERMINE_TRIGGER"
    LEAD_REASSESSMENT = "LEAD_REASSESSMENT"
    COORDINATE_REASSESSMENT = "COORDINATE_REASSESSMENT"
    PLAN_NEXT_REVIEW = "PLAN_NEXT_REVIEW"
    NORMALIZE_REQUIRED_REVIEW_CONSTRAINT = "NORMALIZE_REQUIRED_REVIEW_CONSTRAINT"
    COMPLETE_CONTINUING_REVIEW = "COMPLETE_CONTINUING_REVIEW"
    PERFORM_INTERVENTION = "PERFORM_INTERVENTION"
    ACCEPT_INTERVENTION_COMPLETION = "ACCEPT_INTERVENTION_COMPLETION"
    OBTAIN_LEARNING_EVIDENCE = "OBTAIN_LEARNING_EVIDENCE"
    DETERMINE_SHARED_DEPENDENCY_EQUIVALENCE = "DETERMINE_SHARED_DEPENDENCY_EQUIVALENCE"


class AssignmentState(StrEnum):
    ASSIGNED = "ASSIGNED"
    WITHDRAWN = "WITHDRAWN"
    SUPERSEDED = "SUPERSEDED"


class WorkState(StrEnum):
    READY = "READY"
    WAITING = "WAITING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    SUPERSEDED = "SUPERSEDED"


class ResponsibilityResolutionKind(StrEnum):
    ONE = "ONE"
    VACANCY = "RESPONSIBILITY NOT ESTABLISHED"
    CONFLICT = "RESPONSIBILITY CONFLICT — UNRESOLVED"


def responsibility_signature(
    *,
    contract: SemanticContractRef,
    obligation_kind: ObligationKind,
    owning_case_id: RecordId,
    context: ExactContextSet,
    purpose: str,
    use: str,
    scope: str,
) -> str:
    """Canonical obligation signature; Actor, access, labels, and time are excluded."""
    values = {
        "contract": contract.key,
        "obligation_kind": obligation_kind.value,
        "owning_case_id": str(owning_case_id),
        "context_digest": context.digest,
        "purpose": purpose,
        "use": use,
        "scope": scope,
    }
    canonical = json.dumps(values, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ResponsibilityResolution:
    kind: ResponsibilityResolutionKind
    assignment_version_ids: tuple[str, ...]
    actor_id: str | None = None
