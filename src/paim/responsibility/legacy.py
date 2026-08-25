"""Explicit read-only adapter for bounded legacy Role Assignment consumers.

The adapter never writes prospective facts and never runs as fallback after a
prospective Responsibility read has failed.
"""

from __future__ import annotations

from dataclasses import dataclass

from paim.domain.models import RoleAssignmentDetail, RoleTargetType
from paim.integrity.ids import RecordId
from paim.responsibility.models import ObligationKind


@dataclass(frozen=True, slots=True)
class LegacyResponsibilityCandidate:
    actor_id: RecordId
    source_assignment_version_id: str
    obligation_kind: ObligationKind
    adapter_key: str = "legacy-role-responsibility-adapter@1"
    source_label: str = "LEGACY_ROLE_ASSIGNMENT_READ_ONLY"


class LegacyRoleResponsibilityAdapter:
    """Named/versioned, exact-target, read-only compatibility adapter."""

    @staticmethod
    def adapt(
        assignment: RoleAssignmentDetail,
        *,
        obligation_kind: ObligationKind,
        owning_case_id: RecordId,
    ) -> LegacyResponsibilityCandidate | None:
        if (
            not assignment.accountable
            or assignment.target_type is not RoleTargetType.CASE
            or assignment.target_id != str(owning_case_id)
            or assignment.case_context_id not in {None, owning_case_id}
        ):
            return None
        return LegacyResponsibilityCandidate(
            actor_id=assignment.actor_id,
            source_assignment_version_id=str(assignment.version_id),
            obligation_kind=obligation_kind,
        )
