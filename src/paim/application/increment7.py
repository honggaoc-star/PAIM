"""Increment 7 Shared Dependency and derived Management Register service."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime
from typing import cast

from paim.application.increment2 import DomainRuleViolation
from paim.application.increment6 import Increment6ApplicationService
from paim.domain.increment7 import (
    DependencyCandidateSetVersionInput,
    EquivalenceDeterminationConflict,
    EquivalenceDeterminationFound,
    EquivalenceDeterminationNotEstablished,
    EquivalenceDeterminationSelection,
    EquivalenceDeterminationVersionInput,
    EquivalenceOutcome,
    NotificationIntent,
    ProjectionConsistency,
    RegisterAction,
    RegisterActionLaunch,
    RegisterConcernEntry,
    RegisterConcernKey,
    RegisterLifecycle,
    RegisterManifest,
    RegisterQuery,
    RegisterSourceSelection,
    RegisterView,
    SharedDependencyAccountability,
    SharedDependencyAccountabilityConflict,
    SharedDependencyAccountabilityFound,
    SharedDependencyAccountabilityNotEstablished,
    SharedDependencyGroup,
    SharedDependencyMechanismVersionInput,
    SharedDependencyVersionInput,
    SourceDisposition,
)
from paim.domain.increment7_ports import Increment7Store, Increment7Transaction
from paim.domain.models import (
    CommandMeta,
    DelegationEffect,
    RoleAssignmentDetail,
    RoleTargetType,
)
from paim.integrity import (
    RecordId,
    RecordVersionId,
    SelectionConflict,
    SelectionFound,
    SelectionQuery,
)
from paim.integrity.records import JsonValue, canonical_json
from paim.integrity.time import Clock, from_epoch_microseconds, require_utc, to_epoch_microseconds
from paim.persistence.ports import CommandOutcome

_DETERMINER = "Shared Dependency Determiner"
_ALLOWED_SOURCE_FAMILIES = frozenset(
    {
        "governing-configuration-designation",
        "managed-configuration",
        "configuration-determination",
        "authority-gap",
        "evidence",
        "evidence-applicability",
        "lane-evidence-fitness",
        "input-acceptance-selection",
        "integration",
        "uncertainty-classification",
        "boundary-snapshot",
        "boundary-determination",
        "management-decision",
        "decision-authorization-basis",
        "bounded-proceed-determination",
        "intervention",
        "intervention-obligation-set",
        "intervention-obligation",
        "intervention-completion-result",
        "intervention-completion-acceptance",
        "learning-item",
        "reassessment-trigger",
        "trigger-determination",
        "reassessment",
        "interim-operating-disposition",
        "role-assignment",
    }
)
_SAFE_ORDERING = frozenset(
    {
        "stable_identity",
        "due_at",
        "recorded_at",
        "effective_at",
        "lifecycle",
        "source_label",
    }
)
_AUTO_POPULATION_FAMILIES = tuple(
    sorted(
        _ALLOWED_SOURCE_FAMILIES
        - {
            # Configuration inclusion needs either an exact governing
            # designation or an accepted linked-work obligation; the raw
            # Configuration family alone cannot establish either condition.
            "managed-configuration",
            # Role vacancy/conflict is populated only for an identified
            # obligation and is therefore supplied by that owning adapter.
            "role-assignment",
        }
    )
)
_ACTION_CONTRACTS: dict[RegisterAction, tuple[bool, str]] = {
    RegisterAction.ASSIGN_OWNER: (True, "commit_role_assignment"),
    RegisterAction.ACKNOWLEDGE: (False, "record_personal_register_preference"),
    RegisterAction.READ: (False, "record_personal_register_preference"),
    RegisterAction.SNOOZE: (False, "record_personal_register_preference"),
    RegisterAction.DEFER: (True, "invoke_owning_family_deferral_if_supported"),
    RegisterAction.ACCEPT_RESIDUAL_CONCERN: (
        True,
        "commit_exact_decision_uncertainty_or_authority",
    ),
    RegisterAction.LINK_SHARED_DEPENDENCY: (
        True,
        "commit_dependency_candidate_set_and_equivalence",
    ),
    RegisterAction.LINK_DUPLICATE: (True, "invoke_owning_family_duplicate_determination"),
    RegisterAction.CREATE_TRIGGER: (True, "commit_trigger"),
    RegisterAction.CREATE_REASSESSMENT: (True, "commit_reassessment"),
    RegisterAction.CREATE_OR_MODIFY_DECISION: (True, "commit_decision"),
    RegisterAction.CREATE_OR_MODIFY_INTERVENTION: (True, "commit_intervention"),
}


class Increment7ApplicationService(Increment6ApplicationService):
    """Specification-bounded synchronous Increment 7 application boundary."""

    def __init__(self, store: Increment7Store, clock: Clock) -> None:
        super().__init__(store, clock)
        self._increment7_store = store

    @staticmethod
    def _required(*values: str) -> bool:
        return all(value.strip() for value in values)

    @staticmethod
    def _canonical_members(value: DependencyCandidateSetVersionInput) -> list[dict[str, str]]:
        return sorted(
            (
                {
                    "source_family": member.source_family,
                    "source_record_id": str(member.source_record_id),
                    "source_version_id": str(member.source_version_id),
                    "dependency_kind": member.dependency_kind,
                }
                for member in value.members
            ),
            key=lambda item: (
                item["source_family"],
                item["source_record_id"],
                item["source_version_id"],
                item["dependency_kind"],
            ),
        )

    def commit_shared_dependency(
        self, meta: CommandMeta, value: SharedDependencyVersionInput
    ) -> CommandOutcome:
        if (
            not self._required(
                value.dependency_kind, value.purpose, value.declared_scope, value.rationale
            )
            or not value.provenance
        ):
            raise DomainRuleViolation(
                "Shared Dependency kind, purpose, scope, provenance, and rationale are required"
            )

        def project(base: object) -> None:
            transaction = cast("Increment7Transaction", base)
            transaction.add_shared_dependency(
                dependency_id=value.dependency_id,
                version_id=value.version_id,
                dependency_kind=value.dependency_kind,
                purpose=value.purpose,
                declared_scope=value.declared_scope,
                organizational_context=value.organizational_context,
                provenance_json=json.dumps(value.provenance, sort_keys=True, separators=(",", ":")),
                withdrawn=value.withdrawn,
            )

        content: dict[str, JsonValue] = {
            "dependency_kind": value.dependency_kind,
            "purpose": value.purpose,
            "declared_scope": value.declared_scope,
            "organizational_context": value.organizational_context,
            "provenance": value.provenance,
            "rationale": value.rationale,
            "withdrawn": value.withdrawn,
        }
        return self._commit_version(
            meta=meta,
            record_id=value.dependency_id,
            version_id=value.version_id,
            family="shared-dependency",
            scope=f"shared-dependency:{value.dependency_id}",
            content=content,
            effective=value.effective,
            expected_version_id=value.expected_version_id,
            relationship_reason=value.relationship_reason,
            relationship_type=value.relationship_type,
            project=project,
            reason_outcome="INCREMENT_7_SHARED_DEPENDENCY_VALID",
        )

    def commit_dependency_candidate_set(
        self, meta: CommandMeta, value: DependencyCandidateSetVersionInput
    ) -> CommandOutcome:
        if not value.members:
            raise DomainRuleViolation("Dependency Candidate Set requires exact typed membership")
        if (
            not self._required(
                value.dependency_kind,
                value.equivalence_scope,
                value.purpose,
                value.rationale,
            )
            or not value.provenance
        ):
            raise DomainRuleViolation(
                "Candidate Set kind, scope, purpose, provenance, and rationale are required"
            )
        members = self._canonical_members(value)
        identities = {
            (item["source_family"], item["source_record_id"], item["source_version_id"])
            for item in members
        }
        if len(identities) != len(members):
            raise DomainRuleViolation("Candidate Set cannot contain duplicate exact members")
        if any(item["dependency_kind"] != value.dependency_kind for item in members):
            raise DomainRuleViolation("Candidate Set member dependency kind must be exact")
        membership_json = canonical_json(cast("dict[str, JsonValue]", {"members": members}))
        checksum = hashlib.sha256(membership_json.encode("utf-8")).hexdigest()

        def project(base: object) -> None:
            transaction = cast("Increment7Transaction", base)
            for member in value.members:
                source = transaction.get_version(member.source_version_id)
                if (
                    source is None
                    or source.record_id != member.source_record_id
                    or source.family != member.source_family
                ):
                    raise DomainRuleViolation(
                        "Candidate Set membership requires exact typed source Record/Version"
                    )
            transaction.add_dependency_candidate_set(
                candidate_set_id=value.candidate_set_id,
                version_id=value.version_id,
                dependency_kind=value.dependency_kind,
                equivalence_scope=value.equivalence_scope,
                purpose=value.purpose,
                organizational_context=value.organizational_context,
                provenance_json=json.dumps(value.provenance, sort_keys=True, separators=(",", ":")),
                membership_checksum=checksum,
                withdrawn=value.withdrawn,
                members=members,
            )

        content: dict[str, JsonValue] = {
            "dependency_kind": value.dependency_kind,
            "equivalence_scope": value.equivalence_scope,
            "purpose": value.purpose,
            "organizational_context": value.organizational_context,
            "provenance": value.provenance,
            "rationale": value.rationale,
            "members": cast("list[JsonValue]", members),
            "membership_checksum": checksum,
            "withdrawn": value.withdrawn,
        }
        return self._commit_version(
            meta=meta,
            record_id=value.candidate_set_id,
            version_id=value.version_id,
            family="dependency-candidate-set",
            scope=f"dependency-candidate-set:{value.candidate_set_id}",
            content=content,
            effective=value.effective,
            expected_version_id=value.expected_version_id,
            relationship_reason=value.relationship_reason,
            relationship_type=value.relationship_type,
            project=project,
            reason_outcome="INCREMENT_7_IMMUTABLE_CANDIDATE_SET_VALID",
        )

    def _target_family(self, target_type: str) -> str:
        if target_type == RoleTargetType.DEPENDENCY_CANDIDATE_SET.value:
            return "dependency-candidate-set"
        if target_type == RoleTargetType.SHARED_DEPENDENCY.value:
            return "shared-dependency"
        raise DomainRuleViolation("Shared Dependency accountability target type is invalid")

    def commit_shared_dependency_mechanism(
        self, meta: CommandMeta, value: SharedDependencyMechanismVersionInput
    ) -> CommandOutcome:
        if not self._required(
            value.target_id,
            value.rule_id,
            value.rule_version,
            value.authority_source,
        ):
            raise DomainRuleViolation(
                "governed mechanism requires exact target, rule/version, and authority source"
            )
        target_family = self._target_family(value.target_type)

        def project(base: object) -> None:
            transaction = cast("Increment7Transaction", base)
            if not transaction.actor_exists(value.accountable_actor_id):
                raise DomainRuleViolation("mechanism accountable actor is not established")
            try:
                target_version_id = RecordVersionId.parse(value.target_id)
            except ValueError as error:
                raise DomainRuleViolation("mechanism target requires an exact Version") from error
            target = transaction.get_version(target_version_id)
            if target is None or target.family != target_family:
                raise DomainRuleViolation("governed mechanism exact target is not established")
            transaction.add_shared_dependency_mechanism(
                mechanism_id=value.mechanism_id,
                version_id=value.version_id,
                target_type=value.target_type,
                target_id=value.target_id,
                accountable_actor_id=value.accountable_actor_id,
                rule_id=value.rule_id,
                rule_version=value.rule_version,
                authority_source=value.authority_source,
                limits_json=json.dumps(value.limits, separators=(",", ":")),
            )

        content: dict[str, JsonValue] = {
            "function": _DETERMINER,
            "target_type": value.target_type,
            "target_id": value.target_id,
            "accountable_actor_id": str(value.accountable_actor_id),
            "rule_id": value.rule_id,
            "rule_version": value.rule_version,
            "authority_source": value.authority_source,
            "limits": list(value.limits),
        }
        return self._commit_version(
            meta=meta,
            record_id=value.mechanism_id,
            version_id=value.version_id,
            family="shared-dependency-accountability-mechanism",
            scope=f"dependency-target:{value.target_type}:{value.target_id}",
            content=content,
            effective=value.effective,
            expected_version_id=value.expected_version_id,
            relationship_reason=value.relationship_reason,
            relationship_type=value.relationship_type,
            project=project,
            reason_outcome="INCREMENT_7_GENUINE_GOVERNED_MECHANISM_VALID",
        )

    def _current_assignments(
        self,
        transaction: Increment7Transaction,
        *,
        target_type: str,
        target_id: str,
        effective_at: datetime,
        known_at: datetime,
    ) -> tuple[RecordVersionId, ...]:
        assignment_ids = transaction.role_assignment_records(
            role=_DETERMINER, targets=((target_type, target_id),)
        )
        versions: list[RecordVersionId] = []
        for assignment_id in assignment_ids:
            history = transaction.get_history(assignment_id)
            if not history.versions:
                continue
            scope = next(iter(history.versions)).scope
            selected = transaction.select_current(
                SelectionQuery(
                    family="role-assignment",
                    scope=scope,
                    effective_at=effective_at,
                    known_at=known_at,
                    record_id=assignment_id,
                )
            )
            if isinstance(selected, SelectionFound):
                versions.append(selected.candidate.version_id)
            elif isinstance(selected, SelectionConflict):
                versions.extend(candidate.version_id for candidate in selected.candidates)
        return tuple(versions)

    def _dependency_accountability_in_transaction(
        self,
        transaction: Increment7Transaction,
        *,
        target_type: str,
        target_id: str,
        effective_at: datetime,
        known_at: datetime,
    ) -> SharedDependencyAccountability:
        candidates: list[SharedDependencyAccountabilityFound] = []
        candidate_ids: list[RecordVersionId] = []
        assignment_candidates: dict[RecordVersionId, RoleAssignmentDetail] = {}
        for version_id in self._current_assignments(
            transaction,
            target_type=target_type,
            target_id=target_id,
            effective_at=effective_at,
            known_at=known_at,
        ):
            detail = transaction.role_assignment_detail(version_id)
            if detail is not None and detail.accountable and detail.role == _DETERMINER:
                assignment_candidates[version_id] = detail
                candidate_ids.append(version_id)
        if assignment_candidates:
            delegated_sources = {
                detail.delegated_from_version_id
                for detail in assignment_candidates.values()
                if detail.delegated_from_version_id is not None
            }
            leaves = set(assignment_candidates) - delegated_sources
            if len(leaves) == 1:
                leaf_version_id = next(iter(leaves))
                lineage: set[RecordVersionId] = set()
                cursor: RecordVersionId | None = leaf_version_id
                while cursor is not None and cursor not in lineage:
                    lineage.add(cursor)
                    detail = assignment_candidates.get(cursor)
                    cursor = detail.delegated_from_version_id if detail is not None else None
                if lineage == set(assignment_candidates) and cursor is None:
                    leaf = assignment_candidates[leaf_version_id]
                    candidates.append(
                        SharedDependencyAccountabilityFound(
                            assignment_version_id=leaf_version_id,
                            mechanism_version_id=None,
                            actor_id=leaf.actor_id,
                        )
                    )
        for version_id in transaction.shared_dependency_mechanism_versions(
            target_type=target_type, target_id=target_id
        ):
            version = transaction.get_version(version_id)
            mechanism_detail = transaction.shared_dependency_mechanism_detail(version_id)
            if version is None or mechanism_detail is None:
                continue
            selected = transaction.select_current(
                SelectionQuery(
                    family="shared-dependency-accountability-mechanism",
                    scope=version.scope,
                    effective_at=effective_at,
                    known_at=known_at,
                    record_id=version.record_id,
                )
            )
            if isinstance(selected, SelectionFound) and selected.candidate.version_id == version_id:
                candidates.append(
                    SharedDependencyAccountabilityFound(
                        assignment_version_id=None,
                        mechanism_version_id=version_id,
                        actor_id=RecordId.parse(
                            cast("str", mechanism_detail["accountable_actor_id"])
                        ),
                    )
                )
                candidate_ids.append(version_id)
        if not candidates and candidate_ids:
            return SharedDependencyAccountabilityConflict(frozenset(candidate_ids))
        if not candidates:
            return SharedDependencyAccountabilityNotEstablished()
        if len(candidates) == 1:
            return candidates[0]
        return SharedDependencyAccountabilityConflict(frozenset(candidate_ids))

    def resolve_shared_dependency_accountability(
        self,
        *,
        target_type: RoleTargetType,
        target_version_id: RecordVersionId,
        effective_at: datetime,
        known_at: datetime | None = None,
    ) -> SharedDependencyAccountability:
        if target_type not in {
            RoleTargetType.DEPENDENCY_CANDIDATE_SET,
            RoleTargetType.SHARED_DEPENDENCY,
        }:
            raise DomainRuleViolation(
                "Shared Dependency accountability requires exact typed target"
            )
        effective = require_utc(effective_at)
        knowledge = require_utc(known_at or self._clock.now())
        with self._increment7_store.read_transaction() as transaction:
            return self._dependency_accountability_in_transaction(
                transaction,
                target_type=target_type.value,
                target_id=str(target_version_id),
                effective_at=effective,
                known_at=knowledge,
            )

    def _validate_delegation_chain(
        self,
        transaction: Increment7Transaction,
        assignment_version_id: RecordVersionId,
        chain: tuple[RecordVersionId, ...],
        *,
        target_version_id: RecordVersionId,
        effective_at: datetime,
        known_at: datetime,
    ) -> None:
        def eligible_detail(version_id: RecordVersionId) -> RoleAssignmentDetail:
            version = transaction.get_version(version_id)
            detail = transaction.role_assignment_detail(version_id)
            if version is None or version.family != "role-assignment" or detail is None:
                raise DomainRuleViolation("delegation chain Role Assignment is not established")
            selected = transaction.select_current(
                SelectionQuery(
                    family="role-assignment",
                    scope=version.scope,
                    effective_at=effective_at,
                    known_at=known_at,
                    record_id=version.record_id,
                )
            )
            if (
                not isinstance(selected, SelectionFound)
                or selected.candidate.version_id != version_id
            ):
                raise DomainRuleViolation(
                    "delegation chain contains a prospectively ineligible Role Assignment"
                )
            if (
                not detail.accountable
                or detail.role != _DETERMINER
                or detail.target_type is not RoleTargetType.DEPENDENCY_CANDIDATE_SET
                or detail.target_id != str(target_version_id)
            ):
                raise DomainRuleViolation(
                    "delegation chain Role Assignment has an ineligible role or exact target"
                )
            return detail

        detail = eligible_detail(assignment_version_id)
        expected = detail.delegated_from_version_id
        if expected is None and chain:
            raise DomainRuleViolation("non-delegated assignment cannot cite a delegation chain")
        child = detail
        for version_id in chain:
            if expected != version_id:
                raise DomainRuleViolation("delegation chain is incomplete or out of order")
            if child.delegation_effect is DelegationEffect.NONE:
                raise DomainRuleViolation("delegation chain contains an invalid delegation effect")
            parent = eligible_detail(version_id)
            expected = parent.delegated_from_version_id
            child = parent
        if expected is not None:
            raise DomainRuleViolation("delegation chain is incomplete")
        if child.delegation_effect is not DelegationEffect.NONE:
            raise DomainRuleViolation("delegation chain root has an invalid delegation effect")

    def commit_equivalence_determination(
        self, meta: CommandMeta, value: EquivalenceDeterminationVersionInput
    ) -> CommandOutcome:
        if not self._required(value.dependency_kind, value.equivalence_scope, value.rationale):
            raise DomainRuleViolation("Equivalence kind, scope, and rationale are required")
        if (value.outcome is EquivalenceOutcome.EQUIVALENT) != (
            value.shared_dependency_version_id is not None
        ):
            raise DomainRuleViolation(
                "only EQUIVALENT outcome requires an exact Shared Dependency Version"
            )
        if (value.accountable_assignment_version_id is not None) == (
            value.accountable_mechanism_version_id is not None
        ):
            raise DomainRuleViolation(
                "exactly one accountable assignment or genuine mechanism is required"
            )
        recorded_at = self._clock.now()

        def project(base: object) -> None:
            transaction = cast("Increment7Transaction", base)
            candidate_set = transaction.candidate_set_detail(value.candidate_set_version_id)
            candidate_record = transaction.get_version(value.candidate_set_version_id)
            if (
                candidate_set is None
                or candidate_record is None
                or candidate_record.family != "dependency-candidate-set"
                or candidate_set["dependency_kind"] != value.dependency_kind
                or candidate_set["equivalence_scope"] != value.equivalence_scope
                or bool(candidate_set["withdrawn"])
            ):
                raise DomainRuleViolation("exact eligible Candidate Set Version is not established")
            if value.shared_dependency_version_id is not None:
                dependency = transaction.shared_dependency_detail(
                    value.shared_dependency_version_id
                )
                if (
                    dependency is None
                    or dependency["dependency_kind"] != value.dependency_kind
                    or bool(dependency["withdrawn"])
                ):
                    raise DomainRuleViolation(
                        "exact eligible Shared Dependency Version is not established"
                    )
            if value.accountable_assignment_version_id is not None:
                self._validate_delegation_chain(
                    transaction,
                    value.accountable_assignment_version_id,
                    value.delegation_chain_version_ids,
                    target_version_id=value.candidate_set_version_id,
                    effective_at=value.effective.start,
                    known_at=recorded_at,
                )
            elif value.delegation_chain_version_ids:
                raise DomainRuleViolation("governed mechanism cannot cite a Role delegation chain")
            accountability = self._dependency_accountability_in_transaction(
                transaction,
                target_type=RoleTargetType.DEPENDENCY_CANDIDATE_SET.value,
                target_id=str(value.candidate_set_version_id),
                effective_at=value.effective.start,
                known_at=recorded_at,
            )
            if not isinstance(accountability, SharedDependencyAccountabilityFound):
                raise DomainRuleViolation(accountability.reason)
            if (
                accountability.assignment_version_id != value.accountable_assignment_version_id
                or accountability.mechanism_version_id != value.accountable_mechanism_version_id
                or accountability.actor_id != value.actor_id
            ):
                raise DomainRuleViolation(
                    "Equivalence accountability basis is not the one eligible basis"
                )
            transaction.add_equivalence_determination(
                determination_id=value.determination_id,
                version_id=value.version_id,
                candidate_set_version_id=value.candidate_set_version_id,
                shared_dependency_version_id=value.shared_dependency_version_id,
                dependency_kind=value.dependency_kind,
                equivalence_scope=value.equivalence_scope,
                outcome=value.outcome.value,
                actor_id=value.actor_id,
                assignment_version_id=value.accountable_assignment_version_id,
                mechanism_version_id=value.accountable_mechanism_version_id,
                delegation_chain_version_ids=value.delegation_chain_version_ids,
            )

        content: dict[str, JsonValue] = {
            "candidate_set_version_id": str(value.candidate_set_version_id),
            "shared_dependency_version_id": (
                str(value.shared_dependency_version_id)
                if value.shared_dependency_version_id
                else None
            ),
            "dependency_kind": value.dependency_kind,
            "equivalence_scope": value.equivalence_scope,
            "outcome": value.outcome.value,
            "rationale": value.rationale,
            "actor_id": str(value.actor_id),
            "assignment_version_id": (
                str(value.accountable_assignment_version_id)
                if value.accountable_assignment_version_id
                else None
            ),
            "mechanism_version_id": (
                str(value.accountable_mechanism_version_id)
                if value.accountable_mechanism_version_id
                else None
            ),
            "delegation_chain_version_ids": [
                str(item) for item in value.delegation_chain_version_ids
            ],
        }
        return self._commit_version(
            meta=meta,
            record_id=value.determination_id,
            version_id=value.version_id,
            family="shared-dependency-equivalence",
            scope=(
                f"candidate-set-version:{value.candidate_set_version_id}:"
                f"kind:{value.dependency_kind}:scope:{value.equivalence_scope}"
            ),
            content=content,
            effective=value.effective,
            expected_version_id=value.expected_version_id,
            relationship_reason=value.relationship_reason,
            relationship_type=value.relationship_type,
            project=project,
            reason_outcome="INCREMENT_7_ACCOUNTABLE_EQUIVALENCE_VALID",
        )

    def _current_equivalence_in_transaction(
        self,
        transaction: Increment7Transaction,
        *,
        candidate_set_version_id: RecordVersionId,
        dependency_kind: str,
        equivalence_scope: str,
        effective_at: datetime,
        known_at: datetime,
    ) -> EquivalenceDeterminationSelection:
        found: list[EquivalenceDeterminationFound] = []
        for row in transaction.equivalence_determination_rows(
            candidate_set_version_id=candidate_set_version_id,
            dependency_kind=dependency_kind,
            equivalence_scope=equivalence_scope,
        ):
            version_id = RecordVersionId.parse(cast("str", row["version_id"]))
            record = transaction.get_version(version_id)
            if record is None:
                continue
            selected = transaction.select_current(
                SelectionQuery(
                    family="shared-dependency-equivalence",
                    scope=record.scope,
                    effective_at=effective_at,
                    known_at=known_at,
                    record_id=record.record_id,
                )
            )
            if isinstance(selected, SelectionFound) and selected.candidate.version_id == version_id:
                dependency = cast("str | None", row["shared_dependency_version_id"])
                found.append(
                    EquivalenceDeterminationFound(
                        version_id=version_id,
                        outcome=EquivalenceOutcome(cast("str", row["outcome"])),
                        shared_dependency_version_id=(
                            RecordVersionId.parse(dependency) if dependency else None
                        ),
                    )
                )
        if not found:
            return EquivalenceDeterminationNotEstablished()
        if len(found) == 1:
            return found[0]
        return EquivalenceDeterminationConflict(frozenset(item.version_id for item in found))

    def current_equivalence_determination(
        self,
        *,
        candidate_set_version_id: RecordVersionId,
        dependency_kind: str,
        equivalence_scope: str,
        effective_at: datetime,
        known_at: datetime | None = None,
    ) -> EquivalenceDeterminationSelection:
        effective = require_utc(effective_at)
        knowledge = require_utc(known_at or self._clock.now())
        with self._increment7_store.read_transaction() as transaction:
            return self._current_equivalence_in_transaction(
                transaction,
                candidate_set_version_id=candidate_set_version_id,
                dependency_kind=dependency_kind,
                equivalence_scope=equivalence_scope,
                effective_at=effective,
                known_at=knowledge,
            )

    @staticmethod
    def _lifecycle(
        selection: RegisterSourceSelection, consistency: ProjectionConsistency
    ) -> RegisterLifecycle:
        if consistency is not ProjectionConsistency.CURRENT:
            return RegisterLifecycle.PROJECTION_STALE_OR_INCONSISTENT
        if len(selection.selected_source_version_ids) > 1:
            return RegisterLifecycle.CURRENT_CONFLICT
        return {
            SourceDisposition.ATTENTION: RegisterLifecycle.CURRENT_ATTENTION,
            SourceDisposition.INFORMATIONAL: RegisterLifecycle.CURRENT_INFORMATIONAL,
            SourceDisposition.RESOLVED: RegisterLifecycle.RESOLVED_HISTORICAL,
            SourceDisposition.SUPERSEDED: RegisterLifecycle.SUPERSEDED_HISTORICAL,
            SourceDisposition.WITHDRAWN_OR_INELIGIBLE: (
                RegisterLifecycle.WITHDRAWN_OR_INELIGIBLE_HISTORICAL
            ),
        }[selection.disposition]

    @staticmethod
    def _exact_value(
        family: str,
        content: dict[str, object],
        field: str,
        mapping: dict[str, SourceDisposition],
    ) -> SourceDisposition:
        value = content.get(field)
        if not isinstance(value, str) or value not in mapping:
            raise DomainRuleViolation(
                f"{family} selected source has no accepted {field} population meaning"
            )
        return mapping[value]

    @classmethod
    def _source_disposition(
        cls,
        family: str,
        content: dict[str, object],
        version_statuses: tuple[str, ...] = (),
        *,
        effective_at: datetime | None = None,
    ) -> SourceDisposition:
        """Apply the exact owning-family population contract.

        This deliberately has no generic status/outcome fallback. A family is
        admitted only through an explicit adapter and malformed or unknown
        persisted meanings fail closed instead of becoming guessed attention.
        """

        statuses = {value.casefold() for value in version_statuses}
        if "withdrawn" in statuses or bool(content.get("withdrawn")):
            return SourceDisposition.WITHDRAWN_OR_INELIGIBLE
        if "superseded" in statuses:
            return SourceDisposition.SUPERSEDED

        if family == "governing-configuration-designation":
            return SourceDisposition.INFORMATIONAL
        if family == "configuration-determination":
            return cls._exact_value(
                family,
                content,
                "outcome",
                {
                    "material": SourceDisposition.INFORMATIONAL,
                    "non_material": SourceDisposition.INFORMATIONAL,
                    "same_identity": SourceDisposition.INFORMATIONAL,
                    "new_identity": SourceDisposition.INFORMATIONAL,
                },
            )
        if family == "authority-gap":
            return cls._exact_value(
                family,
                {**content, "outcome": content.get("outcome", "UNRESOLVED")},
                "outcome",
                {
                    "UNRESOLVED": SourceDisposition.ATTENTION,
                    "REQUIREMENT_ESTABLISHED": SourceDisposition.RESOLVED,
                    "PROHIBITION_ESTABLISHED": SourceDisposition.RESOLVED,
                    "PERMISSION_OR_AUTHORITY_ESTABLISHED": SourceDisposition.RESOLVED,
                    "NOT_APPLICABLE_TO_BOUNDED_DECISION": SourceDisposition.RESOLVED,
                    "AUTHORIZED_REFRAMING_NO_LONGER_MATERIAL": SourceDisposition.RESOLVED,
                },
            )
        if family == "evidence":
            return cls._exact_value(
                family,
                content,
                "attention",
                {
                    "current": SourceDisposition.INFORMATIONAL,
                    "refresh_required": SourceDisposition.ATTENTION,
                    "stale": SourceDisposition.ATTENTION,
                },
            )
        if family == "evidence-applicability":
            return cls._exact_value(
                family,
                content,
                "outcome",
                {
                    "APPLICABLE": SourceDisposition.INFORMATIONAL,
                    "CONDITIONALLY_APPLICABLE": SourceDisposition.INFORMATIONAL,
                    "PARTIALLY_APPLICABLE": SourceDisposition.INFORMATIONAL,
                    "NOT_APPLICABLE": SourceDisposition.ATTENTION,
                    "INDETERMINATE": SourceDisposition.ATTENTION,
                },
            )
        if family == "lane-evidence-fitness":
            return cls._exact_value(
                family,
                content,
                "outcome",
                {
                    "SUPPORTABLE": SourceDisposition.INFORMATIONAL,
                    "BLOCKED": SourceDisposition.ATTENTION,
                },
            )
        if family == "input-acceptance-selection":
            if statuses & {"rejected_for_use", "withdrawn"}:
                return SourceDisposition.WITHDRAWN_OR_INELIGIBLE
            return cls._exact_value(
                family, content, "outcome", {"SELECTED": SourceDisposition.INFORMATIONAL}
            )
        if family == "integration":
            return cls._exact_value(
                family,
                content,
                "status",
                {
                    "draft": SourceDisposition.ATTENTION,
                    "ready": SourceDisposition.ATTENTION,
                    "in_progress": SourceDisposition.ATTENTION,
                    "completed": SourceDisposition.INFORMATIONAL,
                    "decision_pending": SourceDisposition.ATTENTION,
                    "superseded": SourceDisposition.SUPERSEDED,
                    "withdrawn": SourceDisposition.WITHDRAWN_OR_INELIGIBLE,
                },
            )
        if family == "uncertainty-classification":
            return cls._exact_value(
                family,
                content,
                "classification",
                {
                    "ACCEPTED_UNCERTAINTY": SourceDisposition.INFORMATIONAL,
                    "DECISION_LIMITING_UNCERTAINTY": SourceDisposition.ATTENTION,
                },
            )
        if family == "boundary-snapshot":
            return cls._exact_value(
                family,
                content,
                "status",
                {
                    "draft": SourceDisposition.ATTENTION,
                    "finalized": SourceDisposition.INFORMATIONAL,
                    "current": SourceDisposition.INFORMATIONAL,
                    "superseded": SourceDisposition.SUPERSEDED,
                    "withdrawn": SourceDisposition.WITHDRAWN_OR_INELIGIBLE,
                },
            )
        if family == "boundary-determination":
            return cls._exact_value(
                family,
                content,
                "outcome",
                {
                    "PASS": SourceDisposition.INFORMATIONAL,
                    "BREACH": SourceDisposition.ATTENTION,
                    "INDETERMINATE": SourceDisposition.ATTENTION,
                },
            )
        if family == "management-decision":
            return cls._exact_value(
                family,
                content,
                "status",
                {
                    "proposed": SourceDisposition.ATTENTION,
                    "pending_authorization": SourceDisposition.ATTENTION,
                    "authorized": SourceDisposition.INFORMATIONAL,
                    "expired": SourceDisposition.ATTENTION,
                    "superseded": SourceDisposition.SUPERSEDED,
                    "withdrawn": SourceDisposition.WITHDRAWN_OR_INELIGIBLE,
                },
            )
        if family in {
            "decision-authorization-basis",
            "bounded-proceed-determination",
            "reassessment-trigger",
        }:
            return SourceDisposition.INFORMATIONAL
        if family == "intervention-obligation-set":
            raise DomainRuleViolation(
                "Intervention Obligation Set requires its authoritative aggregate adapter"
            )
        if family == "intervention":
            return cls._exact_value(
                family,
                content,
                "status",
                {
                    "PROPOSED": SourceDisposition.ATTENTION,
                    "PLANNED": SourceDisposition.ATTENTION,
                    "IN_PROGRESS": SourceDisposition.ATTENTION,
                    "BLOCKED": SourceDisposition.ATTENTION,
                    "PARTIALLY_COMPLETED": SourceDisposition.ATTENTION,
                    "COMPLETED": SourceDisposition.INFORMATIONAL,
                    "FAILED": SourceDisposition.ATTENTION,
                    "CANCELLED": SourceDisposition.WITHDRAWN_OR_INELIGIBLE,
                    "SUPERSEDED": SourceDisposition.SUPERSEDED,
                },
            )
        if family == "intervention-obligation":
            return cls._exact_value(
                family,
                content,
                "requirement_type",
                {
                    "REQUIRED_BEFORE_OPERATION": SourceDisposition.ATTENTION,
                    "REQUIRED_AFTER_OPERATION": SourceDisposition.ATTENTION,
                    "OPTIONAL": SourceDisposition.INFORMATIONAL,
                },
            )
        if family == "intervention-completion-result":
            # A Result never satisfies an obligation without eligible Acceptance.
            return SourceDisposition.ATTENTION
        if family == "intervention-completion-acceptance":
            if content.get("status") == "WITHDRAWN":
                return SourceDisposition.WITHDRAWN_OR_INELIGIBLE
            if content.get("status") == "SUPERSEDED":
                return SourceDisposition.SUPERSEDED
            return cls._exact_value(
                family,
                content,
                "outcome",
                {
                    "ACCEPTED": SourceDisposition.RESOLVED,
                    "REJECTED": SourceDisposition.ATTENTION,
                },
            )
        if family == "learning-item":
            return cls._exact_value(
                family,
                content,
                "status",
                {
                    "PROPOSED": SourceDisposition.ATTENTION,
                    "ACTIVE": SourceDisposition.ATTENTION,
                    "AWAITING_EVIDENCE": SourceDisposition.ATTENTION,
                    "COMPLETED": SourceDisposition.RESOLVED,
                    "INCONCLUSIVE": SourceDisposition.ATTENTION,
                    "CANCELLED": SourceDisposition.WITHDRAWN_OR_INELIGIBLE,
                    "SUPERSEDED": SourceDisposition.SUPERSEDED,
                },
            )
        if family == "trigger-determination":
            return cls._exact_value(
                family,
                content,
                "outcome",
                {
                    "INFORMATIONAL": SourceDisposition.INFORMATIONAL,
                    "MONITOR": SourceDisposition.INFORMATIONAL,
                    "ANALYTICAL_REFRESH": SourceDisposition.ATTENTION,
                    "REASSESSMENT_REQUIRED": SourceDisposition.ATTENTION,
                    "IMMEDIATE_DISPOSITION_AND_REASSESSMENT": SourceDisposition.ATTENTION,
                },
            )
        if family == "reassessment":
            return cls._exact_value(
                family,
                content,
                "status",
                {
                    "PROPOSED": SourceDisposition.ATTENTION,
                    "OPEN": SourceDisposition.ATTENTION,
                    "ANALYSIS_IN_PROGRESS": SourceDisposition.ATTENTION,
                    "AWAITING_DECISION_AUTHORITY": SourceDisposition.ATTENTION,
                    "BLOCKED_CONFLICT": SourceDisposition.ATTENTION,
                    "COMPLETED_CONFIRMED": SourceDisposition.RESOLVED,
                    "COMPLETED_SUCCESSOR_DECISION": SourceDisposition.RESOLVED,
                    "CANCELLED": SourceDisposition.WITHDRAWN_OR_INELIGIBLE,
                    "SUPERSEDED": SourceDisposition.SUPERSEDED,
                },
            )
        if family == "interim-operating-disposition":
            expiry = content.get("expiry_at")
            if (
                isinstance(expiry, str)
                and effective_at is not None
                and require_utc(datetime.fromisoformat(expiry)) <= effective_at
            ):
                return SourceDisposition.ATTENTION
            return (
                SourceDisposition.ATTENTION
                if content.get("suspend_scope")
                else SourceDisposition.INFORMATIONAL
            )
        raise DomainRuleViolation(f"{family} has no accepted Management Register adapter")

    @staticmethod
    def _source_context(
        transaction: Increment7Transaction,
        *,
        family: str,
        record_id: RecordId,
        content: dict[str, object],
    ) -> tuple[RecordId, RecordId | None] | None:
        case_text = content.get("case_id") or content.get("owning_case_id")
        configuration_text = content.get("configuration_id")
        configuration_version_text = content.get("configuration_version_id")
        if family == "managed-configuration":
            configuration_text = str(record_id)
        if not case_text or not configuration_version_text:
            for link_field in (
                "integration_version_id",
                "snapshot_version_id",
                "decision_version_id",
                "intervention_version_id",
                "obligation_version_id",
                "reassessment_version_id",
            ):
                linked_text = content.get(link_field)
                if not linked_text:
                    continue
                try:
                    linked = transaction.get_version(RecordVersionId.parse(str(linked_text)))
                except ValueError:
                    linked = None
                if linked is None:
                    continue
                linked_content = cast("dict[str, object]", json.loads(linked.content_json))
                case_text = case_text or linked_content.get("case_id")
                configuration_text = configuration_text or linked_content.get("configuration_id")
                configuration_version_text = configuration_version_text or linked_content.get(
                    "configuration_version_id"
                )
                if case_text and configuration_version_text:
                    break
        if configuration_version_text and (not case_text or not configuration_text):
            try:
                context = transaction.configuration_version_context(
                    RecordVersionId.parse(str(configuration_version_text))
                )
            except ValueError:
                context = None
            if context is not None:
                case_text = case_text or str(context.owning_case_id)
                configuration_text = configuration_text or str(context.configuration_id)
        if not case_text:
            return None
        try:
            case_id = RecordId.parse(str(case_text))
            configuration_id = (
                RecordId.parse(str(configuration_text)) if configuration_text else None
            )
        except ValueError:
            return None
        return case_id, configuration_id

    def _resolved_dependency_for_sources(
        self,
        transaction: Increment7Transaction,
        *,
        family: str,
        record_id: RecordId,
        source_version_ids: tuple[RecordVersionId, ...],
        effective_at: datetime,
        known_at: datetime,
    ) -> tuple[RecordId, RecordVersionId] | None:
        """Resolve exact source Versions through accepted equivalence determinations."""

        resolved_by_source: dict[RecordVersionId, set[tuple[RecordId, RecordVersionId]]] = {
            version_id: set() for version_id in source_version_ids
        }
        for identity in transaction.register_record_identities(("dependency-candidate-set",)):
            candidate_set_id = RecordId.parse(identity["record_id"])
            selected = transaction.select_current(
                SelectionQuery(
                    family="dependency-candidate-set",
                    scope=identity["scope"],
                    effective_at=effective_at,
                    known_at=known_at,
                    record_id=candidate_set_id,
                )
            )
            if not isinstance(selected, SelectionFound):
                continue
            candidate_version_id = selected.candidate.version_id
            detail = transaction.candidate_set_detail(candidate_version_id)
            if detail is None or bool(detail["withdrawn"]):
                continue
            matching_versions = {
                RecordVersionId.parse(cast("str", member["source_version_id"]))
                for member in transaction.candidate_set_members(candidate_version_id)
                if member["source_family"] == family
                and member["source_record_id"] == str(record_id)
                and RecordVersionId.parse(cast("str", member["source_version_id"]))
                in resolved_by_source
            }
            if not matching_versions:
                continue
            equivalence = self._current_equivalence_in_transaction(
                transaction,
                candidate_set_version_id=candidate_version_id,
                dependency_kind=cast("str", detail["dependency_kind"]),
                equivalence_scope=cast("str", detail["equivalence_scope"]),
                effective_at=effective_at,
                known_at=known_at,
            )
            if (
                not isinstance(equivalence, EquivalenceDeterminationFound)
                or equivalence.outcome is not EquivalenceOutcome.EQUIVALENT
                or equivalence.shared_dependency_version_id is None
            ):
                continue
            dependency_version_id = equivalence.shared_dependency_version_id
            dependency = transaction.get_version(dependency_version_id)
            if dependency is None or dependency.family != "shared-dependency":
                continue
            current_dependency = transaction.select_current(
                SelectionQuery(
                    family=dependency.family,
                    scope=dependency.scope,
                    effective_at=effective_at,
                    known_at=known_at,
                    record_id=dependency.record_id,
                )
            )
            if (
                not isinstance(current_dependency, SelectionFound)
                or current_dependency.candidate.version_id != dependency_version_id
            ):
                continue
            for source_version_id in matching_versions:
                resolved_by_source[source_version_id].add(
                    (dependency.record_id, dependency_version_id)
                )
        resolutions = {
            next(iter(values)) for values in resolved_by_source.values() if len(values) == 1
        }
        if (
            all(len(values) == 1 for values in resolved_by_source.values())
            and len(resolutions) == 1
        ):
            return next(iter(resolutions))
        return None

    def derive_management_register(self, query: RegisterQuery) -> RegisterView:
        """Derive the Register directly from accepted authoritative families.

        Owning domain adapters remain responsible for domain-specific absent
        obligations (for example a vacancy with no source record). Existing
        authoritative records are selected here with the common dual-time
        kernel; raw telemetry and unknown families never enter the population.
        """

        effective_at = require_utc(query.effective_at)
        known_at = require_utc(query.known_at or self._clock.now())
        selections: list[RegisterSourceSelection] = []
        with self._increment7_store.read_transaction() as transaction:
            for identity in transaction.register_record_identities(_AUTO_POPULATION_FAMILIES):
                record_id = RecordId.parse(identity["record_id"])
                family = identity["family"]
                selected = transaction.select_current(
                    SelectionQuery(
                        family=family,
                        scope=identity["scope"],
                        effective_at=effective_at,
                        known_at=known_at,
                        record_id=record_id,
                    )
                )
                candidates: tuple[RecordVersionId, ...]
                if isinstance(selected, SelectionFound):
                    candidates = (selected.candidate.version_id,)
                elif isinstance(selected, SelectionConflict):
                    candidates = tuple(
                        candidate.version_id
                        for candidate in sorted(
                            selected.candidates, key=lambda item: str(item.version_id)
                        )
                    )
                else:
                    continue
                versions = [transaction.get_version(version_id) for version_id in candidates]
                contents: list[dict[str, object]] = []
                for version in versions:
                    if version is None:
                        raise DomainRuleViolation(
                            "selected Register source cannot be reconstructed"
                        )
                    contents.append(cast("dict[str, object]", json.loads(version.content_json)))
                contexts = {
                    context
                    for context in (
                        self._source_context(
                            transaction,
                            family=family,
                            record_id=record_id,
                            content=content,
                        )
                        for content in contents
                    )
                    if context is not None
                }
                if len(contexts) != 1:
                    # Unbound records are not silently assigned to a Case;
                    # incompatible contexts remain outside a fabricated entry.
                    continue
                case_id, configuration_id = next(iter(contexts))
                if family == "intervention-obligation-set" and len(contents) == 1:
                    aggregate = self._evaluate_prerequisites_in_transaction(
                        transaction,
                        decision_version_id=RecordVersionId.parse(
                            str(contents[0]["decision_version_id"])
                        ),
                        configuration_version_id=RecordVersionId.parse(
                            str(contents[0]["configuration_version_id"])
                        ),
                        effective_at=effective_at,
                        known_at=known_at,
                    )
                    dispositions = {
                        {
                            "SATISFIED": SourceDisposition.RESOLVED,
                            "NOT_REQUIRED": SourceDisposition.RESOLVED,
                            "NOT_ESTABLISHED": SourceDisposition.ATTENTION,
                            "INCOMPLETE": SourceDisposition.ATTENTION,
                            "BLOCKED": SourceDisposition.ATTENTION,
                            "CONFLICT": SourceDisposition.ATTENTION,
                        }[aggregate.result.value]
                    }
                elif family == "trigger-determination" and len(contents) == 1:
                    trigger_outcome = str(contents[0].get("outcome"))
                    if trigger_outcome in {
                        "REASSESSMENT_REQUIRED",
                        "IMMEDIATE_DISPOSITION_AND_REASSESSMENT",
                    }:
                        coverage = self._trigger_coverage_in_transaction(
                            transaction,
                            trigger_version_id=RecordVersionId.parse(
                                str(contents[0]["trigger_version_id"])
                            ),
                            effective_at=effective_at,
                            known_at=known_at,
                        )
                        if coverage.state is None:
                            dispositions = {SourceDisposition.WITHDRAWN_OR_INELIGIBLE}
                        else:
                            dispositions = {
                                {
                                    "REASSESSMENT_REQUIRED_UNASSIGNED": (
                                        SourceDisposition.ATTENTION
                                    ),
                                    "LINKED_ACTIVE": SourceDisposition.INFORMATIONAL,
                                    "BLOCKED_CONFLICT": SourceDisposition.ATTENTION,
                                    "SATISFIED_BY_COMPLETED_REASSESSMENT": (
                                        SourceDisposition.RESOLVED
                                    ),
                                    "DUPLICATE_DISPOSITIONED": SourceDisposition.RESOLVED,
                                }[coverage.state.value]
                            }
                    else:
                        dispositions = {
                            self._source_disposition(
                                family,
                                contents[0],
                                transaction.version_statuses(
                                    version_id=candidates[0],
                                    effective_at=effective_at,
                                    known_at=known_at,
                                ),
                                effective_at=effective_at,
                            )
                        }
                else:
                    dispositions = {
                        self._source_disposition(
                            family,
                            content,
                            transaction.version_statuses(
                                version_id=version_id,
                                effective_at=effective_at,
                                known_at=known_at,
                            ),
                            effective_at=effective_at,
                        )
                        for content, version_id in zip(contents, candidates, strict=True)
                    }
                disposition = (
                    next(iter(dispositions))
                    if len(dispositions) == 1
                    else SourceDisposition.ATTENTION
                )
                dependency_record_id: RecordId | None = None
                dependency_version_id: RecordVersionId | None = None
                dependency_versions = {
                    str(content.get("shared_dependency_version_id"))
                    for content in contents
                    if content.get("shared_dependency_version_id")
                }
                if len(dependency_versions) == 1:
                    dependency_version_id = RecordVersionId.parse(next(iter(dependency_versions)))
                    dependency = transaction.get_version(dependency_version_id)
                    if dependency is not None and dependency.family == "shared-dependency":
                        dependency_record_id = dependency.record_id
                    else:
                        dependency_version_id = None
                if dependency_version_id is None:
                    resolved_dependency = self._resolved_dependency_for_sources(
                        transaction,
                        family=family,
                        record_id=record_id,
                        source_version_ids=candidates,
                        effective_at=effective_at,
                        known_at=known_at,
                    )
                    if resolved_dependency is not None:
                        dependency_record_id, dependency_version_id = resolved_dependency
                selections.append(
                    RegisterSourceSelection(
                        key=RegisterConcernKey(
                            case_id,
                            configuration_id,
                            family.replace("-", "_").upper(),
                            family,
                            record_id,
                        ),
                        selected_source_version_ids=candidates,
                        disposition=disposition,
                        source_labels=tuple(
                            sorted(
                                {
                                    str(content[key])
                                    for content in contents
                                    for key in ("materiality", "priority", "status")
                                    if content.get(key) is not None
                                }
                            )
                        ),
                        blocker_present=any(
                            bool(content.get("blocker_present"))
                            or str(content.get("status", "")).upper()
                            in {"BLOCKED", "BLOCKED_CONFLICT"}
                            for content in contents
                        ),
                        dependency_record_id=dependency_record_id,
                        dependency_version_id=dependency_version_id,
                    )
                )
        return self.derive_register_view(query, tuple(selections))

    def derive_register_view(
        self,
        query: RegisterQuery,
        sources: tuple[RegisterSourceSelection, ...],
    ) -> RegisterView:
        effective_at = require_utc(query.effective_at)
        known_at = require_utc(query.known_at or self._clock.now())
        if not self._required(query.rule_id, query.rule_version, query.access_context):
            raise DomainRuleViolation(
                "Register query requires exact rule/version and access context"
            )
        if not query.order_by or any(item not in _SAFE_ORDERING for item in query.order_by):
            raise DomainRuleViolation(
                "Register ordering must use exact non-substantive source facts"
            )
        all_version_ids = tuple(
            version_id for source in sources for version_id in source.selected_source_version_ids
        )
        if len(set(all_version_ids)) != len(all_version_ids):
            # One source Version may support multiple concerns, but each supplied
            # selection must be individually reconstructed. Query it only once.
            unique_version_ids = tuple(dict.fromkeys(all_version_ids))
        else:
            unique_version_ids = all_version_ids

        with self._increment7_store.read_transaction() as transaction:
            rows = transaction.record_versions_for_register(unique_version_ids)
            by_version = {cast("str", row["version_id"]): row for row in rows}
            if len(by_version) != len(unique_version_ids):
                raise DomainRuleViolation("Register source Version is not established")
            for source in sources:
                if not source.selected_source_version_ids:
                    raise DomainRuleViolation(
                        "Register concern requires exact source Version basis"
                    )
                if source.key.source_family not in _ALLOWED_SOURCE_FAMILIES:
                    raise DomainRuleViolation(
                        "source family is not accepted by the population matrix"
                    )
                for version_id in source.selected_source_version_ids:
                    row = by_version[str(version_id)]
                    if (
                        row["record_id"] != str(source.key.source_record_id)
                        or row["family"] != source.key.source_family
                    ):
                        raise DomainRuleViolation(
                            "Register concern source identity/version mismatch"
                        )
                    if from_epoch_microseconds(cast("int", row["recorded_at_us"])) > known_at:
                        raise DomainRuleViolation("Register source exceeds the knowledge cutoff")
                    start = from_epoch_microseconds(cast("int", row["effective_from_us"]))
                    end_value = cast("int | None", row["effective_to_us"])
                    end = from_epoch_microseconds(end_value) if end_value is not None else None
                    if source.disposition in {
                        SourceDisposition.ATTENTION,
                        SourceDisposition.INFORMATIONAL,
                    } and not (start <= effective_at and (end is None or effective_at < end)):
                        raise DomainRuleViolation(
                            "current Register source is outside effective context"
                        )
                if source.dependency_version_id is not None:
                    if source.dependency_record_id is None:
                        raise DomainRuleViolation(
                            "dependency Version requires stable dependency identity"
                        )
                    dependency = transaction.get_version(source.dependency_version_id)
                    if (
                        dependency is None
                        or dependency.family != "shared-dependency"
                        or dependency.record_id != source.dependency_record_id
                    ):
                        raise DomainRuleViolation("Register grouping dependency is not exact")

        high_water = max(
            (
                from_epoch_microseconds(cast("int", by_version[str(version)]["recorded_at_us"]))
                for version in unique_version_ids
            ),
            default=None,
        )
        watermark = query.processed_watermark or high_water
        if high_water is not None and (watermark is None or watermark < high_water):
            consistency = ProjectionConsistency.STALE
        else:
            consistency = ProjectionConsistency.CURRENT

        unfiltered: list[RegisterConcernEntry] = []
        keys: set[str] = set()
        for source in sources:
            key = source.key.canonical()
            if key in keys:
                raise DomainRuleViolation("Register concern key must be unique per derived view")
            keys.add(key)
            if query.case_ids and source.key.case_id not in query.case_ids:
                continue
            if (
                query.configuration_ids
                and source.key.configuration_id not in query.configuration_ids
            ):
                continue
            lifecycle = self._lifecycle(source, consistency)
            if query.lifecycle_filter and lifecycle not in query.lifecycle_filter:
                continue
            unfiltered.append(
                RegisterConcernEntry(
                    key=source.key,
                    lifecycle=lifecycle,
                    selected_source_version_ids=source.selected_source_version_ids,
                    source_labels=source.source_labels,
                    due_at=source.due_at,
                    blocker_present=source.blocker_present,
                    dependency_record_id=source.dependency_record_id,
                    dependency_version_id=source.dependency_version_id,
                )
            )

        visible = [entry for entry in unfiltered if entry.key.case_id in query.accessible_case_ids]
        visible.sort(key=lambda entry: self._entry_order_key(entry, query.order_by))
        groups = self._groups(unfiltered, visible)
        filters = (
            f"case_ids:{','.join(sorted(str(item) for item in query.case_ids))}",
            f"configuration_ids:{','.join(sorted(str(item) for item in query.configuration_ids))}",
            "lifecycle:" + ",".join(sorted(item.value for item in query.lifecycle_filter)),
            f"access_context:{query.access_context}",
        )
        return RegisterView(
            entries=tuple(visible),
            groups=groups,
            generated_at=self._clock.now(),
            effective_at=effective_at,
            known_at=known_at,
            rule_id=query.rule_id,
            rule_version=query.rule_version,
            source_high_water=high_water,
            processed_watermark=watermark,
            consistency=consistency,
            access_context=query.access_context,
            filters=filters,
            ordering=query.order_by,
        )

    @staticmethod
    def _entry_order_key(entry: RegisterConcernEntry, order_by: tuple[str, ...]) -> tuple[str, ...]:
        values: list[str] = []
        for field in order_by:
            if field == "due_at":
                values.append(entry.due_at.isoformat() if entry.due_at else "9999-12-31")
            elif field == "lifecycle":
                values.append(entry.lifecycle.value)
            elif field == "source_label":
                values.append(entry.source_labels[0] if entry.source_labels else "")
            else:
                values.append(entry.key.canonical())
        values.append(entry.key.canonical())
        return tuple(values)

    @staticmethod
    def _groups(
        global_entries: list[RegisterConcernEntry],
        visible_entries: list[RegisterConcernEntry],
    ) -> tuple[SharedDependencyGroup, ...]:
        global_by_dependency: dict[RecordId, list[RegisterConcernEntry]] = defaultdict(list)
        visible_by_dependency: dict[RecordId, list[RegisterConcernEntry]] = defaultdict(list)
        for entry in global_entries:
            if entry.dependency_record_id is not None:
                global_by_dependency[entry.dependency_record_id].append(entry)
        for entry in visible_entries:
            if entry.dependency_record_id is not None:
                visible_by_dependency[entry.dependency_record_id].append(entry)
        groups: list[SharedDependencyGroup] = []
        for dependency_id, visible in visible_by_dependency.items():
            global_constituents = global_by_dependency[dependency_id]
            access_filtered = len(visible) != len(global_constituents)
            concern_counts = Counter(entry.key.concern_kind for entry in visible)
            lifecycle_counts = Counter(entry.lifecycle for entry in visible)
            groups.append(
                SharedDependencyGroup(
                    dependency_record_id=dependency_id,
                    dependency_version_ids=frozenset(
                        entry.dependency_version_id
                        for entry in visible
                        if entry.dependency_version_id is not None
                    ),
                    constituent_keys=tuple(
                        sorted((entry.key for entry in visible), key=lambda key: key.canonical())
                    ),
                    visible_case_ids=frozenset(entry.key.case_id for entry in visible),
                    visible_configuration_ids=frozenset(
                        entry.key.configuration_id
                        for entry in visible
                        if entry.key.configuration_id is not None
                    ),
                    concern_counts=tuple(sorted(concern_counts.items())),
                    lifecycle_counts=tuple(
                        sorted(lifecycle_counts.items(), key=lambda item: item[0].value)
                    ),
                    unresolved_count=sum(
                        entry.lifecycle
                        in {RegisterLifecycle.CURRENT_ATTENTION, RegisterLifecycle.CURRENT_CONFLICT}
                        for entry in visible
                    ),
                    conflict_count=sum(
                        entry.lifecycle is RegisterLifecycle.CURRENT_CONFLICT for entry in visible
                    ),
                    blocker_present=any(entry.blocker_present for entry in visible),
                    visible_constituent_count=len(visible),
                    global_constituent_count=(
                        None if access_filtered else len(global_constituents)
                    ),
                    access_filtered=access_filtered,
                )
            )
        return tuple(sorted(groups, key=lambda group: str(group.dependency_record_id)))

    def persist_register_output(
        self,
        view: RegisterView,
        *,
        output_kind: str,
        manifest_id: str | None = None,
    ) -> RegisterManifest:
        if output_kind not in {"VIEW", "REPORT", "EXPORT"}:
            raise DomainRuleViolation("Register output kind must be VIEW, REPORT, or EXPORT")
        identifier = manifest_id or str(RecordId.new())
        content = self._view_content(view)
        content_json = json.dumps(content, sort_keys=True, separators=(",", ":"))
        checksum = hashlib.sha256(content_json.encode("utf-8")).hexdigest()
        with self._increment7_store.semantic_transaction() as transaction:
            transaction.add_register_manifest(
                manifest_id=identifier,
                output_kind=output_kind,
                content_json=content_json,
                checksum=checksum,
                generated_at_us=to_epoch_microseconds(view.generated_at),
                effective_at_us=to_epoch_microseconds(view.effective_at),
                known_at_us=to_epoch_microseconds(view.known_at),
                rule_id=view.rule_id,
                rule_version=view.rule_version,
                source_high_water_us=(
                    to_epoch_microseconds(view.source_high_water)
                    if view.source_high_water
                    else None
                ),
                processed_watermark_us=(
                    to_epoch_microseconds(view.processed_watermark)
                    if view.processed_watermark
                    else None
                ),
                consistency=view.consistency.value,
                access_context=view.access_context,
            )
        return RegisterManifest(identifier, output_kind, content_json, checksum, view.generated_at)

    @staticmethod
    def _view_content(view: RegisterView) -> dict[str, object]:
        return {
            "generated_at": view.generated_at.isoformat(),
            "effective_at": view.effective_at.isoformat(),
            "known_at": view.known_at.isoformat(),
            "rule_id": view.rule_id,
            "rule_version": view.rule_version,
            "source_high_water": (
                view.source_high_water.isoformat() if view.source_high_water else None
            ),
            "processed_watermark": (
                view.processed_watermark.isoformat() if view.processed_watermark else None
            ),
            "consistency": view.consistency.value,
            "access_context": view.access_context,
            "filters": list(view.filters),
            "ordering": list(view.ordering),
            "entries": [
                {
                    "key": entry.key.canonical(),
                    "lifecycle": entry.lifecycle.value,
                    "source_versions": [str(item) for item in entry.selected_source_version_ids],
                    "source_labels": list(entry.source_labels),
                    "due_at": entry.due_at.isoformat() if entry.due_at else None,
                    "blocker_present": entry.blocker_present,
                    "dependency_record_id": (
                        str(entry.dependency_record_id) if entry.dependency_record_id else None
                    ),
                    "dependency_version_id": (
                        str(entry.dependency_version_id) if entry.dependency_version_id else None
                    ),
                }
                for entry in view.entries
            ],
            "groups": [
                {
                    "dependency_record_id": str(group.dependency_record_id),
                    "dependency_version_ids": sorted(
                        str(item) for item in group.dependency_version_ids
                    ),
                    "constituent_keys": [key.canonical() for key in group.constituent_keys],
                    "visible_case_ids": sorted(str(item) for item in group.visible_case_ids),
                    "visible_configuration_ids": sorted(
                        str(item) for item in group.visible_configuration_ids
                    ),
                    "concern_counts": list(group.concern_counts),
                    "lifecycle_counts": [
                        (lifecycle.value, count) for lifecycle, count in group.lifecycle_counts
                    ],
                    "unresolved_count": group.unresolved_count,
                    "conflict_count": group.conflict_count,
                    "blocker_present": group.blocker_present,
                    "visible_constituent_count": group.visible_constituent_count,
                    "global_constituent_count": group.global_constituent_count,
                    "access_filtered": group.access_filtered,
                }
                for group in view.groups
            ],
        }

    def generate_notification_intents(
        self,
        manifest: RegisterManifest,
        view: RegisterView,
        *,
        channel: str,
        recipient_scope: str,
    ) -> tuple[NotificationIntent, ...]:
        if not self._required(channel, recipient_scope):
            raise DomainRuleViolation("notification channel and recipient scope are required")
        represented = json.dumps(self._view_content(view), sort_keys=True, separators=(",", ":"))
        if represented != manifest.content_json:
            raise DomainRuleViolation(
                "notification view must match the exact retained manifest basis"
            )
        now = self._clock.now()
        intents: list[NotificationIntent] = []
        with self._increment7_store.semantic_transaction() as transaction:
            if transaction.register_manifest(manifest.manifest_id) is None:
                raise DomainRuleViolation("notification requires an exact retained manifest")
            for entry in view.entries:
                if entry.lifecycle not in {
                    RegisterLifecycle.CURRENT_ATTENTION,
                    RegisterLifecycle.CURRENT_CONFLICT,
                }:
                    continue
                intent = NotificationIntent(
                    intent_id=str(RecordId.new()),
                    manifest_id=manifest.manifest_id,
                    concern_key=entry.key.canonical(),
                    concern_lifecycle=entry.lifecycle,
                    channel=channel,
                    recipient_scope=recipient_scope,
                    created_at=now,
                )
                transaction.add_notification_intent(
                    intent_id=intent.intent_id,
                    manifest_id=intent.manifest_id,
                    concern_key=intent.concern_key,
                    concern_lifecycle=intent.concern_lifecycle.value,
                    channel=intent.channel,
                    recipient_scope=intent.recipient_scope,
                    created_at_us=to_epoch_microseconds(intent.created_at),
                )
                intents.append(intent)
        return tuple(intents)

    def get_register_manifest(self, manifest_id: str) -> RegisterManifest | None:
        with self._increment7_store.read_transaction() as transaction:
            row = transaction.register_manifest(manifest_id)
        if row is None:
            return None
        return RegisterManifest(
            manifest_id=cast("str", row["manifest_id"]),
            output_kind=cast("str", row["output_kind"]),
            content_json=cast("str", row["content_json"]),
            checksum=cast("str", row["checksum"]),
            generated_at=from_epoch_microseconds(cast("int", row["generated_at_us"])),
        )

    def launch_action(
        self,
        action: RegisterAction,
        entry: RegisterConcernEntry,
        *,
        launch_context: str,
    ) -> RegisterActionLaunch:
        if action is RegisterAction.MARK_RESOLVED:
            raise DomainRuleViolation("generic Register mark resolved is unavailable")
        if not launch_context.strip():
            raise DomainRuleViolation("Register action requires retained launch-context provenance")
        authoritative, command = _ACTION_CONTRACTS[action]
        return RegisterActionLaunch(
            action=action,
            authoritative=authoritative,
            owning_family=entry.key.source_family,
            command_contract=command,
            source_version_ids=entry.selected_source_version_ids,
            launch_context=launch_context,
        )
