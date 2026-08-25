from __future__ import annotations

import pytest

from paim.domain.models import DelegationEffect, RoleAssignmentDetail, RoleTargetType
from paim.integrity import RecordId, RecordVersionId
from paim.integrity.semantics import (
    ContextMemberKind,
    ExactContextMember,
    ExactContextSet,
)
from paim.responsibility.legacy import LegacyRoleResponsibilityAdapter
from paim.responsibility.models import ObligationKind


def test_exact_context_is_order_independent_and_preserves_identity_kinds() -> None:
    record_id = RecordId.new()
    version_id = RecordVersionId.new()
    members = (
        ExactContextMember("case", ContextMemberKind.RECORD, str(record_id)),
        ExactContextMember("configuration", ContextMemberKind.VERSION, str(version_id)),
        ExactContextMember("purpose", ContextMemberKind.LITERAL, "bounded-use"),
    )
    forward = ExactContextSet.create(members)
    reverse = ExactContextSet.create(tuple(reversed(members)))

    assert forward.digest == reverse.digest
    assert forward.canonical_json == reverse.canonical_json
    assert '"kind":"RECORD"' in forward.canonical_json
    assert '"kind":"VERSION"' in forward.canonical_json


def test_exact_context_rejects_duplicate_slots_and_noncanonical_members() -> None:
    record_id = str(RecordId.new())
    with pytest.raises(ValueError, match="slots must be unique"):
        ExactContextSet.create(
            (
                ExactContextMember("case", ContextMemberKind.RECORD, record_id),
                ExactContextMember("case", ContextMemberKind.LITERAL, "other"),
            )
        )
    with pytest.raises(ValueError, match="canonical"):
        ExactContextMember(" case", ContextMemberKind.LITERAL, "value")


def test_legacy_role_adapter_is_explicit_read_only_and_exact_case_bounded() -> None:
    case_id, actor_id = RecordId.new(), RecordId.new()
    assignment = RoleAssignmentDetail(
        RecordVersionId.new(),
        RecordId.new(),
        actor_id,
        "case reviewer",
        RoleTargetType.CASE,
        str(case_id),
        case_id,
        True,
        "compatible",
        DelegationEffect.NONE,
        None,
    )
    adapted = LegacyRoleResponsibilityAdapter.adapt(
        assignment,
        obligation_kind=ObligationKind.COMPLETE_CONTINUING_REVIEW,
        owning_case_id=case_id,
    )
    assert adapted is not None
    assert adapted.actor_id == actor_id
    assert adapted.source_label == "LEGACY_ROLE_ASSIGNMENT_READ_ONLY"
    assert (
        LegacyRoleResponsibilityAdapter.adapt(
            assignment,
            obligation_kind=ObligationKind.COMPLETE_CONTINUING_REVIEW,
            owning_case_id=RecordId.new(),
        )
        is None
    )
