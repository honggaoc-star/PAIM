"""Access-first Home, Case, and Task composition over prospective sources."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import cast

from paim.case_continuity.models import ContinuitySelectionKind
from paim.case_continuity.service import (
    CaseContinuityAccessDenied,
    CaseContinuityService,
    ContinuityAccessPolicy,
    ContinuityStore,
    ContinuityTransaction,
)
from paim.integrity.ids import RecordId, RecordVersionId
from paim.integrity.selection import SelectionFound, SelectionQuery
from paim.practitioner_queries.models import (
    AIProfile,
    AttentionItem,
    CaseView,
    ContinuingReviewPosition,
    DependencyFact,
    GovernedPosition,
    HomeView,
    LanePosition,
    SourceManifest,
    TaskView,
)


@dataclass(frozen=True, slots=True)
class _SliceCLaneRows:
    assessment: tuple[dict[str, object], ...]
    readiness: tuple[dict[str, object], ...]
    adequacy: tuple[dict[str, object], ...]
    reliance: tuple[dict[str, object], ...]
    unavailable: frozenset[str]


class PractitionerQueryService:
    """Compose visible exact facts; never persist a presentation result."""

    def __init__(
        self,
        store: ContinuityStore,
        continuity: CaseContinuityService,
        access_policy: ContinuityAccessPolicy,
    ) -> None:
        self._store = store
        self._continuity = continuity
        self._access = access_policy

    def home(
        self,
        *,
        principal_id: str,
        actor_id: RecordId,
        candidate_case_ids: tuple[RecordId, ...],
        effective_at: datetime,
        known_at: datetime,
    ) -> HomeView:
        # Filter the population before opening the composition read. Hidden Cases
        # cannot change counts, conflicts, order, or manifest shape.
        visible = tuple(
            sorted(
                (
                    case_id
                    for case_id in candidate_case_ids
                    if self._allowed(principal_id, actor_id, case_id, "home.read")
                ),
                key=str,
            )
        )
        items: list[AttentionItem] = []
        with self._store.read_transaction() as tx:
            for case_id in visible:
                if not self._allowed(principal_id, actor_id, case_id, "home.read"):
                    continue
                items.extend(
                    self._case_attention(
                        tx,
                        principal_id,
                        actor_id,
                        case_id,
                        effective_at,
                        known_at,
                    )
                )
        return HomeView("What needs me?", tuple(items), visible)

    def case(
        self,
        *,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        effective_at: datetime,
        known_at: datetime,
    ) -> CaseView:
        if not self._allowed(principal_id, actor_id, case_id, "case.compose"):
            raise CaseContinuityAccessDenied()
        continuity = self._continuity.select_status(
            principal_id=principal_id,
            actor_id=actor_id,
            case_id=case_id,
            effective_at=effective_at,
            known_at=known_at,
        )
        with self._store.read_transaction() as tx:
            if not self._allowed(principal_id, actor_id, case_id, "case.compose"):
                raise CaseContinuityAccessDenied()
            case_versions = self._current_family(
                tx, "prospective-case", f"case:{case_id}", effective_at, known_at
            )
            title = "Bounded PAIM Case"
            bounded_use: str | None = None
            management_question: str | None = None
            case_number: str | None = None
            ai_profile: AIProfile | None = None
            dependencies: tuple[DependencyFact, ...] = ()
            manifest: set[RecordVersionId] = set()
            continuity_visible = all(
                self._source_visible(
                    tx, principal_id, actor_id, case_id, value, effective_at, known_at
                )
                for value in continuity.version_ids
            )
            continuity_kind = (
                continuity.kind
                if continuity_visible
                else ContinuitySelectionKind.NOT_SAFELY_AVAILABLE
            )
            continuity_status = continuity.status if continuity_visible else None
            if continuity_visible:
                manifest.update(continuity.version_ids)
            if len(case_versions) == 1:
                source = tx.get_version(case_versions[0])
                if source is not None and self._source_visible(
                    tx,
                    principal_id,
                    actor_id,
                    case_id,
                    source.version_id,
                    effective_at,
                    known_at,
                ):
                    title = cast(str, source.content.get("title", title))
                    bounded_use_value = source.content.get("bounded_use")
                    question_value = source.content.get("management_question")
                    bounded_use = bounded_use_value if isinstance(bounded_use_value, str) else None
                    management_question = (
                        question_value if isinstance(question_value, str) else None
                    )
                    number_rows = tx.projection_rows(
                        "case_number_allocations", case_id=str(case_id)
                    )
                    if len(number_rows) == 1:
                        number_value = number_rows[0].get("case_number")
                        case_number = number_value if isinstance(number_value, str) else None
                    raw_profile = source.content.get("ai_profile")
                    if isinstance(raw_profile, dict):
                        name = raw_profile.get("name")
                        if isinstance(name, str) and name.strip():
                            ai_profile = AIProfile(
                                name=name,
                                description=self._optional_text(raw_profile.get("description")),
                                provider_source_type=self._optional_text(
                                    raw_profile.get("provider_source_type")
                                ),
                                provider_source_other=self._optional_text(
                                    raw_profile.get("provider_source_other")
                                ),
                                capabilities=self._optional_text(raw_profile.get("capabilities")),
                                version_model_release=self._optional_text(
                                    raw_profile.get("version_model_release")
                                ),
                                development_context=self._optional_text(
                                    raw_profile.get("development_context")
                                ),
                                operating_characteristics=self._optional_text(
                                    raw_profile.get("operating_characteristics")
                                ),
                                known_strengths_limitations=self._optional_text(
                                    raw_profile.get("known_strengths_limitations")
                                ),
                                organizational_experience=self._optional_text(
                                    raw_profile.get("organizational_experience")
                                ),
                                other_identifying_information=self._optional_text(
                                    raw_profile.get("other_identifying_information")
                                ),
                            )
                    raw_dependencies = source.content.get("dependencies")
                    if isinstance(raw_dependencies, list):
                        parsed_dependencies: list[DependencyFact] = []
                        for item in raw_dependencies:
                            if not isinstance(item, dict):
                                continue
                            name = item.get("name")
                            why = item.get("why_it_matters")
                            relationship_type = item.get("relationship_type")
                            if isinstance(name, str) and isinstance(why, str):
                                parsed_dependencies.append(
                                    DependencyFact(
                                        name,
                                        why,
                                        (
                                            relationship_type
                                            if isinstance(relationship_type, str)
                                            else None
                                        ),
                                    )
                                )
                        dependencies = tuple(parsed_dependencies)
                    manifest.add(source.version_id)
            governing = self._current_family(
                tx, "governing-configuration", f"case:{case_id}", effective_at, known_at
            )
            governing_id: RecordVersionId | None = None
            governing_state = "GOVERNING CONFIGURATION NOT ESTABLISHED"
            if len(governing) == 1:
                rows = tx.projection_rows(
                    "governing_configuration_designations", version_id=str(governing[0])
                )
                if len(rows) == 1:
                    candidate_id = RecordVersionId.parse(str(rows[0]["configuration_version_id"]))
                    if all(
                        self._source_visible(
                            tx, principal_id, actor_id, case_id, value, effective_at, known_at
                        )
                        for value in (governing[0], candidate_id)
                    ):
                        governing_id = candidate_id
                        governing_state = "ONE"
                        manifest.update((governing[0], governing_id))
                    else:
                        governing_state = "GOVERNING CONFIGURATION STATUS NOT SAFELY AVAILABLE"
            elif len(governing) > 1:
                if all(
                    self._source_visible(
                        tx, principal_id, actor_id, case_id, value, effective_at, known_at
                    )
                    for value in governing
                ):
                    governing_state = "GOVERNING CONFIGURATION CONFLICT — UNRESOLVED"
                    manifest.update(governing)
                else:
                    governing_state = "GOVERNING CONFIGURATION STATUS NOT SAFELY AVAILABLE"
            all_responsibilities = self._latest_rows(
                tx,
                tx.projection_rows("responsibility_versions", owning_case_id=str(case_id)),
                effective_at,
                known_at,
            )
            all_work = self._latest_rows(
                tx,
                tx.projection_rows("case_work_versions", owning_case_id=str(case_id)),
                effective_at,
                known_at,
            )
            responsibilities = self._current_responsibilities(
                tx, principal_id, actor_id, case_id, effective_at, known_at
            )
            work = self._current_work(tx, principal_id, actor_id, case_id, effective_at, known_at)
            responsibility_hidden = len(responsibilities) != len(all_responsibilities)
            work_hidden = len(work) != len(all_work)
            value_position = self._lane_position(
                tx,
                principal_id,
                actor_id,
                "VALUE",
                case_id,
                governing_id,
                effective_at,
                known_at,
            )
            risk_position = self._lane_position(
                tx,
                principal_id,
                actor_id,
                "RISK",
                case_id,
                governing_id,
                effective_at,
                known_at,
            )
            integration_position, decision_position = self._slice_d_positions(
                tx,
                principal_id,
                actor_id,
                case_id,
                governing_id,
                effective_at,
                known_at,
            )
            review_position = self._continuing_review_position(
                tx,
                principal_id,
                actor_id,
                case_id,
                governing_id,
                effective_at,
                known_at,
            )
            manifest.update(
                RecordVersionId.parse(str(row["version_id"])) for row in responsibilities
            )
            manifest.update(RecordVersionId.parse(str(row["version_id"])) for row in work)
            for lane_position in (value_position, risk_position):
                if lane_position is not None:
                    manifest.update(lane_position.source_version_ids)
            for governed_position in (integration_position, decision_position):
                if governed_position is not None:
                    manifest.update(governed_position.source_version_ids)
            if review_position is not None:
                manifest.update(review_position.source_version_ids)
            position = (
                "Case continuity: "
                f"{continuity_status.value if continuity_status else continuity_kind.value}",
                f"Governing configuration: {governing_state}",
                (
                    "Responsibilities: status not safely available"
                    if responsibility_hidden
                    else f"Responsibilities: {len(responsibilities)} visible exact source(s)"
                ),
                (
                    "Durable work: status not safely available"
                    if work_hidden
                    else f"Durable work: {len(work)} visible exact source(s)"
                ),
            )
            return CaseView(
                case_id,
                title,
                continuity_kind,
                continuity_status,
                governing_id,
                governing_state,
                (
                    "RESPONSIBILITY STATUS NOT SAFELY AVAILABLE"
                    if responsibility_hidden
                    else self._responsibility_summary(
                        tx,
                        principal_id,
                        actor_id,
                        case_id,
                        responsibilities,
                        effective_at,
                        known_at,
                    )
                ),
                "WORK STATUS NOT SAFELY AVAILABLE" if work_hidden else self._work_state(work),
                position,
                SourceManifest(tuple(sorted(manifest, key=str)), effective_at, known_at),
                value_position=value_position,
                risk_position=risk_position,
                integration_position=integration_position,
                decision_position=decision_position,
                continuing_review_position=review_position,
                bounded_use=bounded_use,
                management_question=management_question,
                case_number=case_number,
                ai_profile=ai_profile,
                dependencies=dependencies,
            )

    @staticmethod
    def _optional_text(value: object) -> str | None:
        return value if isinstance(value, str) and value.strip() else None

    def task(
        self,
        *,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        work_version_id: RecordVersionId,
        effective_at: datetime,
        known_at: datetime,
    ) -> TaskView:
        if not self._allowed(principal_id, actor_id, case_id, "task.read"):
            raise CaseContinuityAccessDenied()
        with self._store.read_transaction() as tx:
            if not self._allowed(principal_id, actor_id, case_id, "task.read"):
                raise CaseContinuityAccessDenied()
            rows = tx.projection_rows("case_work_versions", version_id=str(work_version_id))
            if len(rows) != 1 or rows[0]["owning_case_id"] != str(case_id):
                raise CaseContinuityAccessDenied()
            row = rows[0]
            exact = tx.get_version(work_version_id)
            if exact is None or not self._source_visible(
                tx,
                principal_id,
                actor_id,
                case_id,
                work_version_id,
                effective_at,
                known_at,
            ):
                raise CaseContinuityAccessDenied()
            selected = tx.select_current(
                SelectionQuery(exact.family, exact.scope, effective_at, known_at, exact.record_id)
            )
            if (
                not isinstance(selected, SelectionFound)
                or selected.candidate.version_id != work_version_id
            ):
                raise ValueError("requested Work is not exact current Work")
            responsibility_id = RecordVersionId.parse(str(row["responsibility_version_id"]))
            responsibility = tx.get_version(responsibility_id)
            if responsibility is None or not self._source_visible(
                tx,
                principal_id,
                actor_id,
                case_id,
                responsibility_id,
                effective_at,
                known_at,
            ):
                raise CaseContinuityAccessDenied()
            content = exact.content
            return TaskView(
                case_id,
                work_version_id,
                responsibility_id,
                cast(
                    str, content.get("question", "What result is required for this bounded work?")
                ),
                cast(str, content.get("instruction", row["reason"])),
                cast(
                    str,
                    content.get(
                        "consequence",
                        "The Case remains open until the owning obligation is resolved.",
                    ),
                ),
                cast(
                    str,
                    content.get(
                        "return_path", row.get("return_context_digest") or "Return to the Case."
                    ),
                ),
                cast(
                    str,
                    content.get("permitted_action", "Commit only the named owning-domain result."),
                ),
                "Software access permits an attempt; Responsibility and substantive "
                "authority are validated separately at commit.",
                SourceManifest(
                    tuple(sorted((work_version_id, responsibility_id), key=str)),
                    effective_at,
                    known_at,
                ),
            )

    def _case_attention(
        self,
        tx: ContinuityTransaction,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        effective_at: datetime,
        known_at: datetime,
    ) -> tuple[AttentionItem, ...]:
        responsibilities = self._current_responsibilities(
            tx, principal_id, actor_id, case_id, effective_at, known_at
        )
        work = self._current_work(tx, principal_id, actor_id, case_id, effective_at, known_at)
        result: list[AttentionItem] = []
        governing = self._current_family(
            tx, "governing-configuration", f"case:{case_id}", effective_at, known_at
        )
        governing_id: RecordVersionId | None = None
        if len(governing) == 1:
            rows = tx.projection_rows(
                "governing_configuration_designations", version_id=str(governing[0])
            )
            if len(rows) == 1:
                governing_id = RecordVersionId.parse(str(rows[0]["configuration_version_id"]))
        review = self._continuing_review_position(
            tx,
            principal_id,
            actor_id,
            case_id,
            governing_id,
            effective_at,
            known_at,
        )
        setup_attention = self._initial_assessment_setup_attention(
            tx,
            principal_id,
            actor_id,
            case_id,
            responsibilities,
            governing,
            governing_id,
            effective_at,
            known_at,
        )
        if setup_attention is not None:
            result.append(setup_attention)
        if review is not None and review.attention_reasons:
            review_obligation: str | None = "BEGIN_CONTINUING_REVIEW"
            if review.current_review_state == "FOCUSED REVIEW OPEN":
                confirmation_raw = self._current_projection_rows(
                    tx,
                    tx.projection_rows(
                        "prospective_decision_confirmation_versions",
                        case_id=str(case_id),
                        configuration_version_id=str(governing_id),
                    ),
                    effective_at,
                    known_at,
                )
                confirmation_rows, confirmation_hidden = self._visible_review_rows(
                    tx,
                    principal_id,
                    actor_id,
                    case_id,
                    effective_at,
                    known_at,
                    confirmation_raw,
                    (
                        "decision_version_id",
                        "integration_version_id",
                        "configuration_version_id",
                        "responsibility_version_id",
                        "assignment_version_id",
                        "authority_source_version_id",
                    ),
                    (),
                )
                review_obligation = (
                    None
                    if confirmation_hidden
                    else "COMPLETE_CONTINUING_REVIEW"
                    if confirmation_rows
                    else "CONFIRM_MANAGEMENT_DECISION"
                )
            review_responsibility: RecordVersionId | None = None
            for responsibility in responsibilities:
                if review_obligation is None or (
                    responsibility["obligation_kind"] != review_obligation
                ):
                    continue
                if (
                    self._one_responsibility_state(
                        tx,
                        principal_id,
                        actor_id,
                        case_id,
                        responsibility,
                        effective_at,
                        known_at,
                    )
                    != "ONE"
                ):
                    continue
                assignments = self._eligible_assignments(
                    tx,
                    principal_id,
                    actor_id,
                    case_id,
                    responsibility,
                    effective_at,
                    known_at,
                )
                if assignments and assignments[0]["actor_id"] == str(actor_id):
                    review_responsibility = RecordVersionId.parse(str(responsibility["version_id"]))
                    break
            result.append(
                AttentionItem(
                    case_id,
                    "CONTINUING_REVIEW",
                    "What specifically needs review for this continuing Case?",
                    "; ".join(review.attention_reasons),
                    review_responsibility,
                    None,
                    SourceManifest(review.source_version_ids, effective_at, known_at),
                )
            )
        for row in work:
            if row["assignee_actor_id"] != str(actor_id) or row["state"] not in {
                "READY",
                "WAITING",
            }:
                continue
            work_id = RecordVersionId.parse(str(row["version_id"]))
            responsibility_id = RecordVersionId.parse(str(row["responsibility_version_id"]))
            result.append(
                AttentionItem(
                    case_id,
                    "DURABLE_WORK",
                    str(row["reason"]),
                    "The owning obligation remains unresolved.",
                    responsibility_id,
                    work_id,
                    SourceManifest((responsibility_id, work_id), effective_at, known_at),
                )
            )
        # Responsibilities with vacancy/conflict are visible attention but are not
        # assigned to an Actor and never become inferred priority.
        for row in responsibilities:
            state = self._one_responsibility_state(
                tx,
                principal_id,
                actor_id,
                case_id,
                row,
                effective_at,
                known_at,
            )
            if state == "ONE":
                assignments = self._eligible_assignments(
                    tx,
                    principal_id,
                    actor_id,
                    case_id,
                    row,
                    effective_at,
                    known_at,
                )
                if assignments[0]["actor_id"] != str(actor_id):
                    continue
            responsibility_id = RecordVersionId.parse(str(row["version_id"]))
            obligation = str(row["obligation_kind"])
            lane_question = {
                "FINISH_VALUE_ASSESSMENT": (
                    "VALUE_ASSESSMENT",
                    "Finish the Value assessment for independent review.",
                ),
                "FINISH_RISK_ASSESSMENT": (
                    "RISK_ASSESSMENT",
                    "Finish the Risk assessment for independent review.",
                ),
                "REVIEW_VALUE_ASSESSMENT_ADEQUACY": (
                    "VALUE_REVIEW",
                    "Is the Value assessment adequate for this bounded decision use?",
                ),
                "REVIEW_RISK_ASSESSMENT_ADEQUACY": (
                    "RISK_REVIEW",
                    "Is the Risk assessment adequate for this bounded decision use?",
                ),
                "DESIGNATE_VALUE_ASSESSMENT_RELIANCE": (
                    "VALUE_RELIANCE",
                    "Which adequate Value assessment should this Case actually use?",
                ),
                "DESIGNATE_RISK_ASSESSMENT_RELIANCE": (
                    "RISK_RELIANCE",
                    "Which adequate Risk assessment should this Case actually use?",
                ),
                "COMPLETE_VALUE_RISK_INTEGRATION": (
                    "VALUE_RISK_INTEGRATION",
                    "How should the exact relied Value and Risk positions be integrated?",
                ),
                "PROPOSE_MANAGEMENT_DECISION": (
                    "DECISION_PROPOSAL",
                    "What bounded management action should be proposed from this Integration?",
                ),
                "AUTHORIZE_MANAGEMENT_DECISION": (
                    "DECISION_AUTHORIZATION",
                    "Should this exact proposed Decision be authorized within its authority basis?",
                ),
                "CONFIRM_MANAGEMENT_DECISION": (
                    "DECISION_CONFIRMATION",
                    "Does the exact authorized Decision remain unchanged?",
                ),
            }.get(obligation)
            if lane_question is None and state == "ONE":
                continue
            if lane_question:
                slice_d_obligations = {
                    "COMPLETE_VALUE_RISK_INTEGRATION",
                    "PROPOSE_MANAGEMENT_DECISION",
                    "AUTHORIZE_MANAGEMENT_DECISION",
                    "CONFIRM_MANAGEMENT_DECISION",
                }
                required = (
                    self._slice_d_attention_required(
                        tx,
                        principal_id,
                        actor_id,
                        obligation,
                        case_id,
                        effective_at,
                        known_at,
                    )
                    if obligation in slice_d_obligations
                    else self._lane_attention_required(
                        tx,
                        principal_id,
                        actor_id,
                        obligation,
                        case_id,
                        effective_at,
                        known_at,
                    )
                )
                if not required:
                    continue
            result.append(
                AttentionItem(
                    case_id,
                    lane_question[0] if lane_question and state == "ONE" else state,
                    lane_question[1]
                    if lane_question
                    else f"Who will carry {obligation} for this exact Case context?",
                    (
                        "This assessment is assigned to you and has not yet been completed."
                        if lane_question and state == "ONE"
                        else (
                            "A responsible person must be clearly assigned before this "
                            "work can continue."
                        )
                    ),
                    responsibility_id,
                    None,
                    SourceManifest((responsibility_id,), effective_at, known_at),
                )
            )
        return tuple(
            sorted(
                result,
                key=lambda value: (
                    str(value.case_id),
                    value.kind,
                    str(value.work_version_id or ""),
                ),
            )
        )

    def _continuing_review_position(
        self,
        tx: ContinuityTransaction,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        configuration_version_id: RecordVersionId | None,
        effective_at: datetime,
        known_at: datetime,
    ) -> ContinuingReviewPosition | None:
        if configuration_version_id is None:
            return None
        decision_rows = self._current_projection_rows(
            tx,
            tx.projection_rows(
                "prospective_decision_versions",
                case_id=str(case_id),
                configuration_version_id=str(configuration_version_id),
            ),
            effective_at,
            known_at,
        )
        visible_decisions = self._visible_slice_d_rows(
            tx,
            principal_id,
            actor_id,
            case_id,
            decision_rows,
            "decision",
            effective_at,
            known_at,
        )
        authorized = tuple(row for row in visible_decisions if row.get("status") == "AUTHORIZED")
        if len(authorized) != 1:
            return None
        decision = authorized[0]
        decision_id = str(decision["version_id"])
        context_digest = str(decision["context_digest"])
        common = {
            "case_id": str(case_id),
            "configuration_version_id": str(configuration_version_id),
            "context_digest": context_digest,
        }

        plan_raw = tuple(
            row
            for row in self._current_projection_rows(
                tx,
                tx.projection_rows("planned_review_point_versions", **common),
                effective_at,
                known_at,
            )
            if row.get("decision_version_id") == decision_id
        )
        plans, plan_hidden = self._visible_review_rows(
            tx,
            principal_id,
            actor_id,
            case_id,
            effective_at,
            known_at,
            plan_raw,
            (
                "configuration_version_id",
                "decision_version_id",
                "responsibility_version_id",
                "assignment_version_id",
                "planning_authority_source_version_id",
            ),
            ("source_basis_version_ids_json",),
        )
        planned_at: datetime | None = None
        if plan_hidden:
            planned_state = "STATUS NOT SAFELY AVAILABLE"
        elif not plans:
            planned_state = "NEXT REVIEW NOT PLANNED"
        elif len(plans) > 1:
            planned_state = "PLANNED REVIEW CONFLICT — UNRESOLVED"
        else:
            planned_state = "PLANNED"
            planned_at = self._from_epoch_us(cast(int, plans[0]["review_at_us"]))

        constraint_raw = tuple(
            row
            for row in self._current_projection_rows(
                tx,
                tx.projection_rows("required_review_constraint_versions", state="ACTIVE", **common),
                effective_at,
                known_at,
            )
            if row.get("decision_version_id") == decision_id
        )
        constraints, constraint_hidden = self._visible_review_rows(
            tx,
            principal_id,
            actor_id,
            case_id,
            effective_at,
            known_at,
            constraint_raw,
            (
                "configuration_version_id",
                "decision_version_id",
                "source_version_id",
                "source_authority_version_id",
                "applicability_version_id",
                "responsibility_version_id",
                "assignment_version_id",
            ),
            (),
        )
        required_start: datetime | None = None
        required_end: datetime | None = None
        if constraint_hidden:
            required_state = "STATUS NOT SAFELY AVAILABLE"
        elif not constraints:
            required_state = "REQUIRED REVIEW NOT ESTABLISHED"
        else:
            starts = [
                cast(int, row["window_start_us"])
                for row in constraints
                if row.get("window_start_us") is not None
            ]
            ends = [
                cast(int, row["window_end_us"])
                for row in constraints
                if row.get("window_end_us") is not None
            ]
            required_start = self._from_epoch_us(max(starts)) if starts else None
            required_end = self._from_epoch_us(min(ends)) if ends else None
            required_state = (
                "REQUIRED REVIEW TIMING CONFLICT — UNRESOLVED"
                if required_start is not None
                and required_end is not None
                and required_start > required_end
                else "EXACT MECHANICAL CONSTRAINT INTERSECTION"
            )

        episode_raw = self._current_projection_rows(
            tx,
            tx.projection_rows("review_episode_versions", **common),
            effective_at,
            known_at,
        )
        episodes, episode_hidden = self._visible_review_rows(
            tx,
            principal_id,
            actor_id,
            case_id,
            effective_at,
            known_at,
            episode_raw,
            (
                "configuration_version_id",
                "prior_decision_version_id",
                "prior_integration_version_id",
                "prior_value_reliance_version_id",
                "prior_risk_reliance_version_id",
                "continued_value_reliance_version_id",
                "continued_risk_reliance_version_id",
                "decision_confirmation_version_id",
                "successor_decision_version_id",
                "responsibility_version_id",
                "assignment_version_id",
            ),
            ("origin_version_ids_json", "refreshed_result_version_ids_json"),
        )
        open_episodes = tuple(row for row in episodes if row.get("status") == "OPEN")
        if episode_hidden:
            current_review = "STATUS NOT SAFELY AVAILABLE"
        elif not open_episodes:
            current_review = "NO OPEN REVIEW"
        elif len(open_episodes) == 1:
            current_review = "FOCUSED REVIEW OPEN"
        else:
            current_review = "REVIEW EPISODE CONFLICT — UNRESOLVED"
        completed_at: datetime | None = None
        completed_versions = [
            tx.get_version(RecordVersionId.parse(str(row["version_id"])))
            for row in episodes
            if row.get("status") == "COMPLETED"
        ]
        known_completed = [value for value in completed_versions if value is not None]
        if known_completed:
            completed_at = max(value.effective.start for value in known_completed)

        addressed_event_ids = {
            str(link["result_version_id"])
            for row in episodes
            if row.get("status") == "COMPLETED"
            for link in tx.projection_rows(
                "review_episode_result_links",
                episode_version_id=str(row["version_id"]),
                link_role="ADDRESSED_EVENT_ORIGIN",
            )
        }
        event_raw = tuple(
            row
            for row in self._current_projection_rows(
                tx,
                tx.projection_rows("review_attention_event_versions", **common),
                effective_at,
                known_at,
            )
            if row.get("decision_version_id") == decision_id
            and str(row["version_id"]) not in addressed_event_ids
        )
        events, _event_hidden = self._visible_review_rows(
            tx,
            principal_id,
            actor_id,
            case_id,
            effective_at,
            known_at,
            event_raw,
            (
                "configuration_version_id",
                "decision_version_id",
                "event_source_version_id",
                "responsibility_version_id",
                "assignment_version_id",
            ),
            (),
        )
        reasons: list[str] = []
        source_ids: set[RecordVersionId] = set()
        if planned_at is not None and planned_at <= effective_at:
            reasons.append("The visible planned review point is due.")
            source_ids.add(RecordVersionId.parse(str(plans[0]["version_id"])))
        if required_state == "REQUIRED REVIEW TIMING CONFLICT — UNRESOLVED":
            reasons.append("Visible required review timing is unresolved.")
            source_ids.update(RecordVersionId.parse(str(row["version_id"])) for row in constraints)
        elif required_end is not None and required_end <= effective_at:
            reasons.append("A visible governing review requirement is due.")
            source_ids.update(RecordVersionId.parse(str(row["version_id"])) for row in constraints)
        if events:
            reasons.append("An explicit visible governed event calls for review attention.")
            source_ids.update(RecordVersionId.parse(str(row["version_id"])) for row in events)
        for rows in (plans, constraints, episodes):
            source_ids.update(RecordVersionId.parse(str(row["version_id"])) for row in rows)
        if not (plan_raw or constraint_raw or episode_raw or event_raw):
            return None
        return ContinuingReviewPosition(
            planned_at,
            planned_state,
            required_start,
            required_end,
            required_state,
            current_review,
            completed_at,
            tuple(reasons),
            tuple(sorted(source_ids, key=str)),
        )

    def _visible_review_rows(
        self,
        tx: ContinuityTransaction,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        effective_at: datetime,
        known_at: datetime,
        rows: tuple[dict[str, object], ...],
        scalar_fields: tuple[str, ...],
        json_fields: tuple[str, ...],
    ) -> tuple[tuple[dict[str, object], ...], bool]:
        visible: list[dict[str, object]] = []
        for row in rows:
            required = self._review_required_versions(tx, row, scalar_fields, json_fields)
            if required is not None and all(
                self._source_visible(
                    tx,
                    principal_id,
                    actor_id,
                    case_id,
                    version_id,
                    effective_at,
                    known_at,
                )
                for version_id in required
            ):
                visible.append(row)
        return tuple(visible), len(visible) != len(rows)

    @staticmethod
    def _review_required_versions(
        tx: ContinuityTransaction,
        row: dict[str, object],
        scalar_fields: tuple[str, ...],
        json_fields: tuple[str, ...],
    ) -> set[RecordVersionId] | None:
        try:
            required = {RecordVersionId.parse(str(row["version_id"]))}
            for field in scalar_fields:
                if row.get(field):
                    required.add(RecordVersionId.parse(str(row[field])))
            for field in json_fields:
                encoded = row.get(field)
                if encoded:
                    values = json.loads(cast(str, encoded))
                    if not isinstance(values, list) or not all(
                        isinstance(value, str) for value in values
                    ):
                        return None
                    required.update(RecordVersionId.parse(value) for value in values)
            assignment = row.get("assignment_version_id")
            if assignment:
                assignment_rows = tx.projection_rows(
                    "responsibility_assignment_versions", version_id=str(assignment)
                )
                if len(assignment_rows) != 1:
                    return None
                basis_id = RecordVersionId.parse(
                    str(assignment_rows[0]["assignment_basis_version_id"])
                )
                required.add(basis_id)
                basis_rows = tx.projection_rows(
                    "assignment_basis_versions", version_id=str(basis_id)
                )
                if len(basis_rows) != 1:
                    return None
                required.add(RecordVersionId.parse(str(basis_rows[0]["basis_source_version_id"])))
            return required
        except (KeyError, TypeError, ValueError):
            return None

    @staticmethod
    def _from_epoch_us(value: int) -> datetime:
        return datetime.fromtimestamp(value / 1_000_000, tz=UTC)

    def _lane_attention_required(
        self,
        tx: ContinuityTransaction,
        principal_id: str,
        actor_id: RecordId,
        obligation: str,
        case_id: RecordId,
        effective_at: datetime,
        known_at: datetime,
    ) -> bool:
        lane = "VALUE" if "VALUE" in obligation else "RISK"
        lane_rows = self._slice_c_lane_rows(
            tx,
            principal_id,
            actor_id,
            lane,
            case_id,
            None,
            effective_at,
            known_at,
        )
        assessment = lane_rows.assessment
        readiness = lane_rows.readiness
        adequacy = lane_rows.adequacy
        reliance = lane_rows.reliance
        if obligation.startswith("FINISH_"):
            return not assessment and "assessment" not in lane_rows.unavailable
        if obligation.startswith("REVIEW_"):
            return bool(readiness) and not adequacy and "adequacy" not in lane_rows.unavailable
        if obligation.startswith("DESIGNATE_"):
            return (
                any(row.get("outcome") == "ADEQUATE" for row in adequacy)
                and not reliance
                and "reliance" not in lane_rows.unavailable
            )
        return True

    def _slice_d_attention_required(
        self,
        tx: ContinuityTransaction,
        principal_id: str,
        actor_id: RecordId,
        obligation: str,
        case_id: RecordId,
        effective_at: datetime,
        known_at: datetime,
    ) -> bool:
        governing = self._current_family(
            tx,
            "governing-configuration",
            f"case:{case_id}",
            effective_at,
            known_at,
        )
        if len(governing) != 1:
            return False
        rows = tx.projection_rows(
            "governing_configuration_designations", version_id=str(governing[0])
        )
        if len(rows) != 1:
            return False
        configuration_version_id = RecordVersionId.parse(str(rows[0]["configuration_version_id"]))
        integration, decision = self._slice_d_positions(
            tx,
            principal_id,
            actor_id,
            case_id,
            configuration_version_id,
            effective_at,
            known_at,
        )
        if obligation == "COMPLETE_VALUE_RISK_INTEGRATION":
            lanes = tuple(
                self._lane_position(
                    tx,
                    principal_id,
                    actor_id,
                    lane,
                    case_id,
                    configuration_version_id,
                    effective_at,
                    known_at,
                )
                for lane in ("VALUE", "RISK")
            )
            return integration is None and all(
                lane is not None and lane.reliance == "RELIED" for lane in lanes
            )
        if obligation == "PROPOSE_MANAGEMENT_DECISION":
            return bool(
                integration is not None and integration.state == "COMPLETED" and decision is None
            )
        if obligation == "AUTHORIZE_MANAGEMENT_DECISION":
            return decision is not None and decision.state == "PROPOSED"
        # Confirmation requires an explicit owning review/Work source; the mere
        # existence of an authorized Decision is not inferred as attention.
        return False

    def _lane_position(
        self,
        tx: ContinuityTransaction,
        principal_id: str,
        actor_id: RecordId,
        lane: str,
        case_id: RecordId,
        configuration_version_id: RecordVersionId | None,
        effective_at: datetime,
        known_at: datetime,
    ) -> LanePosition | None:
        if configuration_version_id is None:
            return None
        lane_rows = self._slice_c_lane_rows(
            tx,
            principal_id,
            actor_id,
            lane,
            case_id,
            configuration_version_id,
            effective_at,
            known_at,
        )
        definitions = (
            ("assessment", "PRESENT"),
            ("readiness", "READY FOR INDEPENDENT REVIEW"),
            ("adequacy", None),
            ("reliance", "RELIED"),
        )
        values = {
            "assessment": "NOT ESTABLISHED",
            "readiness": "NOT ESTABLISHED",
            "adequacy": "NOT ESTABLISHED",
            "reliance": "NOT ESTABLISHED",
        }
        manifest: set[RecordVersionId] = set()
        for field, established in definitions:
            current = cast(tuple[dict[str, object], ...], getattr(lane_rows, field))
            if field in lane_rows.unavailable:
                values[field] = (
                    "REVIEW STATUS NOT AVAILABLE"
                    if field in {"adequacy", "reliance"}
                    else "STATUS NOT AVAILABLE"
                )
                continue
            if len(current) > 1:
                values[field] = "CONFLICT — UNRESOLVED"
            elif len(current) == 1:
                values[field] = str(current[0].get("outcome") or established)
                manifest.update(
                    RecordVersionId.parse(value)
                    for value in cast(tuple[str, ...], current[0]["_visible_source_version_ids"])
                )
        if not manifest and not lane_rows.unavailable:
            return None
        return LanePosition(
            lane,
            values["assessment"],
            values["readiness"],
            values["adequacy"],
            values["reliance"],
            tuple(sorted(manifest, key=str)),
        )

    def _slice_c_lane_rows(
        self,
        tx: ContinuityTransaction,
        principal_id: str,
        actor_id: RecordId,
        lane: str,
        case_id: RecordId,
        configuration_version_id: RecordVersionId | None,
        effective_at: datetime,
        known_at: datetime,
    ) -> _SliceCLaneRows:
        filters: dict[str, object] = {"lane": lane, "case_id": str(case_id)}
        if configuration_version_id is not None:
            filters["configuration_version_id"] = str(configuration_version_id)
        unavailable: set[str] = set()
        raw_assessment = PractitionerQueryService._current_projection_rows(
            tx,
            tx.projection_rows("assessment_candidate_versions", **filters),
            effective_at,
            known_at,
        )
        assessment = self._visible_slice_c_rows(
            tx,
            principal_id,
            actor_id,
            case_id,
            effective_at,
            known_at,
            raw_assessment,
        )
        if len(raw_assessment) != len(assessment):
            unavailable.update(("assessment", "readiness", "adequacy", "reliance"))
        assessment_ids = {str(row["version_id"]) for row in assessment}
        raw_readiness = tuple(
            row
            for row in PractitionerQueryService._current_projection_rows(
                tx,
                tx.projection_rows("assessment_readiness_versions", **filters),
                effective_at,
                known_at,
            )
            if str(row["assessment_version_id"]) in assessment_ids
        )
        readiness = self._visible_slice_c_rows(
            tx, principal_id, actor_id, case_id, effective_at, known_at, raw_readiness
        )
        if len(raw_readiness) != len(readiness):
            unavailable.update(("readiness", "adequacy", "reliance"))
        readiness_ids = {str(row["version_id"]) for row in readiness}
        raw_adequacy = tuple(
            row
            for row in PractitionerQueryService._current_projection_rows(
                tx,
                tx.projection_rows("assessment_adequacy_versions", **filters),
                effective_at,
                known_at,
            )
            if str(row["assessment_version_id"]) in assessment_ids
            and str(row["readiness_version_id"]) in readiness_ids
        )
        adequacy = self._visible_slice_c_rows(
            tx, principal_id, actor_id, case_id, effective_at, known_at, raw_adequacy
        )
        if len(raw_adequacy) != len(adequacy):
            unavailable.update(("adequacy", "reliance"))
        adequate_ids = {
            str(row["version_id"]) for row in adequacy if row.get("outcome") == "ADEQUATE"
        }
        raw_reliance = tuple(
            row
            for row in PractitionerQueryService._current_projection_rows(
                tx,
                tx.projection_rows("assessment_reliance_versions", **filters),
                effective_at,
                known_at,
            )
            if str(row["assessment_version_id"]) in assessment_ids
            and str(row["readiness_version_id"]) in readiness_ids
            and str(row["adequacy_version_id"]) in adequate_ids
        )
        reliance = self._visible_slice_c_rows(
            tx, principal_id, actor_id, case_id, effective_at, known_at, raw_reliance
        )
        if len(raw_reliance) != len(reliance):
            unavailable.add("reliance")
        return _SliceCLaneRows(
            assessment,
            readiness,
            adequacy,
            reliance,
            frozenset(unavailable),
        )

    def _visible_slice_c_rows(
        self,
        tx: ContinuityTransaction,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        effective_at: datetime,
        known_at: datetime,
        rows: tuple[dict[str, object], ...],
    ) -> tuple[dict[str, object], ...]:
        visible: list[dict[str, object]] = []
        for row in rows:
            required = self._slice_c_required_versions(tx, row)
            if required is None or not all(
                self._source_visible(
                    tx,
                    principal_id,
                    actor_id,
                    case_id,
                    version_id,
                    effective_at,
                    known_at,
                )
                for version_id in required
            ):
                continue
            enriched = dict(row)
            enriched["_visible_source_version_ids"] = tuple(
                sorted(str(value) for value in required)
            )
            visible.append(enriched)
        return tuple(visible)

    @staticmethod
    def _slice_c_required_versions(
        tx: ContinuityTransaction, row: dict[str, object]
    ) -> set[RecordVersionId] | None:
        try:
            required = {RecordVersionId.parse(str(row["version_id"]))}
            for field in (
                "configuration_version_id",
                "assessment_version_id",
                "readiness_version_id",
                "adequacy_version_id",
                "responsibility_version_id",
                "assignment_version_id",
                "assignment_basis_version_id",
            ):
                value = row.get(field)
                if value:
                    required.add(RecordVersionId.parse(str(value)))
            encoded_basis = row.get("information_basis_version_ids_json")
            if encoded_basis:
                basis = json.loads(cast(str, encoded_basis))
                if not isinstance(basis, list) or not all(
                    isinstance(value, str) for value in basis
                ):
                    return None
                required.update(RecordVersionId.parse(value) for value in basis)
            assignment_id = row.get("assignment_version_id")
            basis_id: RecordVersionId | None = None
            if assignment_id:
                assignments = tx.projection_rows(
                    "responsibility_assignment_versions", version_id=str(assignment_id)
                )
                if len(assignments) != 1:
                    return None
                basis_id = RecordVersionId.parse(str(assignments[0]["assignment_basis_version_id"]))
                required.add(basis_id)
            elif row.get("assignment_basis_version_id"):
                basis_id = RecordVersionId.parse(str(row["assignment_basis_version_id"]))
            if basis_id is not None:
                bases = tx.projection_rows("assignment_basis_versions", version_id=str(basis_id))
                if len(bases) != 1:
                    return None
                required.add(RecordVersionId.parse(str(bases[0]["basis_source_version_id"])))
            return required
        except (KeyError, TypeError, ValueError):
            return None

    def _slice_d_positions(
        self,
        tx: ContinuityTransaction,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        configuration_version_id: RecordVersionId | None,
        effective_at: datetime,
        known_at: datetime,
    ) -> tuple[GovernedPosition | None, GovernedPosition | None]:
        if configuration_version_id is None:
            return None, None
        integration_rows = self._current_projection_rows(
            tx,
            tx.projection_rows(
                "prospective_integration_versions",
                case_id=str(case_id),
                configuration_version_id=str(configuration_version_id),
            ),
            effective_at,
            known_at,
        )
        visible_integrations = self._visible_slice_d_rows(
            tx,
            principal_id,
            actor_id,
            case_id,
            integration_rows,
            "integration",
            effective_at,
            known_at,
        )
        integration_position = self._governed_position(
            visible_integrations,
            hidden=self._slice_d_has_hidden_sources(
                tx,
                principal_id,
                actor_id,
                case_id,
                integration_rows,
                "integration",
                effective_at,
                known_at,
            ),
            established="COMPLETED",
        )
        visible_integration_ids = {str(row["version_id"]) for row in visible_integrations}
        decision_rows = tuple(
            row
            for row in self._current_projection_rows(
                tx,
                tx.projection_rows(
                    "prospective_decision_versions",
                    case_id=str(case_id),
                    configuration_version_id=str(configuration_version_id),
                ),
                effective_at,
                known_at,
            )
            if str(row["integration_version_id"]) in visible_integration_ids
        )
        visible_decisions = self._visible_slice_d_rows(
            tx,
            principal_id,
            actor_id,
            case_id,
            decision_rows,
            "decision",
            effective_at,
            known_at,
        )
        decision_position = self._governed_position(
            visible_decisions,
            hidden=self._slice_d_has_hidden_sources(
                tx,
                principal_id,
                actor_id,
                case_id,
                decision_rows,
                "decision",
                effective_at,
                known_at,
            ),
            established=None,
        )
        if decision_position is not None and len(visible_decisions) == 1:
            decision_source = tx.get_version(
                RecordVersionId.parse(str(visible_decisions[0]["version_id"]))
            )
            if decision_source is not None:
                action = decision_source.content.get("proposed_action")
                rationale = decision_source.content.get("rationale")
                raw_conditions = decision_source.content.get("authorization_conditions")
                if raw_conditions is None:
                    raw_conditions = decision_source.content.get("conditions_and_limits")
                conditions = (
                    tuple(value for value in raw_conditions if isinstance(value, str))
                    if isinstance(raw_conditions, list)
                    else ()
                )
                decision_position = GovernedPosition(
                    decision_position.state,
                    decision_position.source_version_ids,
                    action if isinstance(action, str) else None,
                    rationale if isinstance(rationale, str) else None,
                    conditions,
                )
        return integration_position, decision_position

    @staticmethod
    def _governed_position(
        rows: tuple[dict[str, object], ...],
        *,
        hidden: bool,
        established: str | None,
    ) -> GovernedPosition | None:
        if hidden:
            return GovernedPosition("STATUS NOT AVAILABLE", ())
        if not rows:
            return None
        if len(rows) > 1:
            return GovernedPosition("CONFLICT — UNRESOLVED", ())
        row = rows[0]
        return GovernedPosition(
            str(row.get("status") or established),
            tuple(
                RecordVersionId.parse(value)
                for value in cast(tuple[str, ...], row["_visible_source_version_ids"])
            ),
        )

    def _visible_slice_d_rows(
        self,
        tx: ContinuityTransaction,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        rows: tuple[dict[str, object], ...],
        kind: str,
        effective_at: datetime,
        known_at: datetime,
    ) -> tuple[dict[str, object], ...]:
        visible: list[dict[str, object]] = []
        for row in rows:
            required = self._slice_d_required_versions(tx, row, kind)
            if required is None or not all(
                self._source_visible(
                    tx,
                    principal_id,
                    actor_id,
                    case_id,
                    version_id,
                    effective_at,
                    known_at,
                )
                for version_id in required
            ):
                continue
            basis_row = row
            if kind == "decision":
                integration_rows = tx.projection_rows(
                    "prospective_integration_versions",
                    version_id=str(row["integration_version_id"]),
                )
                if len(integration_rows) != 1:
                    continue
                basis_row = integration_rows[0]
            if not self._slice_d_basis_current(tx, basis_row, effective_at, known_at):
                continue
            enriched = dict(row)
            enriched["_visible_source_version_ids"] = tuple(
                sorted(str(value) for value in required)
            )
            visible.append(enriched)
        return tuple(visible)

    def _slice_d_has_hidden_sources(
        self,
        tx: ContinuityTransaction,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        rows: tuple[dict[str, object], ...],
        kind: str,
        effective_at: datetime,
        known_at: datetime,
    ) -> bool:
        for row in rows:
            required = self._slice_d_required_versions(tx, row, kind)
            if required is None or not all(
                self._source_visible(
                    tx,
                    principal_id,
                    actor_id,
                    case_id,
                    version_id,
                    effective_at,
                    known_at,
                )
                for version_id in required
            ):
                return True
        return False

    @staticmethod
    def _slice_d_basis_current(
        tx: ContinuityTransaction,
        row: dict[str, object],
        effective_at: datetime,
        known_at: datetime,
    ) -> bool:
        try:
            for lane in ("value", "risk"):
                for component in ("assessment", "readiness", "adequacy", "reliance"):
                    version_id = RecordVersionId.parse(str(row[f"{lane}_{component}_version_id"]))
                    version = tx.get_version(version_id)
                    if version is None:
                        return False
                    selected = tx.select_current(
                        SelectionQuery(
                            version.family,
                            version.scope,
                            effective_at,
                            known_at,
                            version.record_id if component != "reliance" else None,
                        )
                    )
                    if not (
                        isinstance(selected, SelectionFound)
                        and selected.candidate.version_id == version_id
                    ):
                        return False
            return True
        except (KeyError, TypeError, ValueError):
            return False

    @staticmethod
    def _slice_d_required_versions(
        tx: ContinuityTransaction,
        row: dict[str, object],
        kind: str,
    ) -> set[RecordVersionId] | None:
        try:
            required = {
                RecordVersionId.parse(str(row[field]))
                for field in (
                    "version_id",
                    "configuration_version_id",
                    "integration_version_id",
                    "responsibility_version_id",
                    "assignment_version_id",
                    "authority_source_version_id",
                    "proposal_version_id",
                )
                if row.get(field)
            }
            integration = row
            if kind == "decision":
                integration_rows = tx.projection_rows(
                    "prospective_integration_versions",
                    version_id=str(row["integration_version_id"]),
                )
                if len(integration_rows) != 1:
                    return None
                integration = integration_rows[0]
            required.add(RecordVersionId.parse(str(integration["version_id"])))
            for lane in ("value", "risk"):
                for family, table in (
                    ("assessment", "assessment_candidate_versions"),
                    ("readiness", "assessment_readiness_versions"),
                    ("adequacy", "assessment_adequacy_versions"),
                    ("reliance", "assessment_reliance_versions"),
                ):
                    version_id = RecordVersionId.parse(
                        str(integration[f"{lane}_{family}_version_id"])
                    )
                    rows = tx.projection_rows(table, version_id=str(version_id))
                    if len(rows) != 1:
                        return None
                    source_set = PractitionerQueryService._slice_c_required_versions(tx, rows[0])
                    if source_set is None:
                        return None
                    required.update(source_set)
            for field in (
                "value_information_basis_json",
                "risk_information_basis_json",
            ):
                encoded = integration.get(field)
                if not isinstance(encoded, str):
                    return None
                values = json.loads(encoded)
                if not isinstance(values, list) or not all(
                    isinstance(value, str) for value in values
                ):
                    return None
                required.update(RecordVersionId.parse(value) for value in values)
            assignment_ids = {
                str(value)
                for value in (
                    integration.get("assignment_version_id"),
                    row.get("assignment_version_id"),
                )
                if value
            }
            for assignment_id in assignment_ids:
                assignments = tx.projection_rows(
                    "responsibility_assignment_versions", version_id=str(assignment_id)
                )
                if len(assignments) != 1:
                    return None
                basis_id = RecordVersionId.parse(str(assignments[0]["assignment_basis_version_id"]))
                required.add(basis_id)
                bases = tx.projection_rows("assignment_basis_versions", version_id=str(basis_id))
                if len(bases) != 1:
                    return None
                required.add(RecordVersionId.parse(str(bases[0]["basis_source_version_id"])))
            return required
        except (KeyError, TypeError, ValueError):
            return None

    @staticmethod
    def _current_projection_rows(
        tx: ContinuityTransaction,
        rows: tuple[dict[str, object], ...],
        effective_at: datetime,
        known_at: datetime,
    ) -> tuple[dict[str, object], ...]:
        by_record: dict[str, dict[str, dict[str, object]]] = {}
        for row in rows:
            by_record.setdefault(str(row["record_id"]), {})[str(row["version_id"])] = row
        current: list[dict[str, object]] = []
        for _record_id, versions in by_record.items():
            sample = tx.get_version(RecordVersionId.parse(next(iter(versions))))
            if sample is None:
                continue
            selected = tx.select_current(
                SelectionQuery(
                    sample.family,
                    sample.scope,
                    effective_at,
                    known_at,
                    sample.record_id,
                )
            )
            candidates = (
                (selected.candidate,)
                if isinstance(selected, SelectionFound)
                else getattr(selected, "candidates", ())
            )
            current.extend(
                versions[str(candidate.version_id)]
                for candidate in candidates
                if str(candidate.version_id) in versions
            )
        return tuple(sorted(current, key=lambda row: str(row["version_id"])))

    @staticmethod
    def _current_family(
        tx: ContinuityTransaction,
        family: str,
        scope: str,
        effective_at: datetime,
        known_at: datetime,
    ) -> tuple[RecordVersionId, ...]:
        selected = tx.select_current(SelectionQuery(family, scope, effective_at, known_at))
        if isinstance(selected, SelectionFound):
            return (selected.candidate.version_id,)
        candidates = getattr(selected, "candidates", ())
        return tuple(sorted((item.version_id for item in candidates), key=str))

    def _current_responsibilities(
        self,
        tx: ContinuityTransaction,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        effective_at: datetime,
        known_at: datetime,
    ) -> tuple[dict[str, object], ...]:
        rows = tx.projection_rows("responsibility_versions", owning_case_id=str(case_id))
        return tuple(
            row
            for row in PractitionerQueryService._latest_rows(tx, rows, effective_at, known_at)
            if self._source_visible(
                tx,
                principal_id,
                actor_id,
                case_id,
                RecordVersionId.parse(str(row["version_id"])),
                effective_at,
                known_at,
            )
        )

    def _current_work(
        self,
        tx: ContinuityTransaction,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        effective_at: datetime,
        known_at: datetime,
    ) -> tuple[dict[str, object], ...]:
        rows = tx.projection_rows("case_work_versions", owning_case_id=str(case_id))
        visible: list[dict[str, object]] = []
        for row in PractitionerQueryService._latest_rows(tx, rows, effective_at, known_at):
            required = self._slice_c_required_versions(tx, row)
            if required is not None and all(
                self._source_visible(
                    tx,
                    principal_id,
                    actor_id,
                    case_id,
                    version_id,
                    effective_at,
                    known_at,
                )
                for version_id in required
            ):
                visible.append(row)
        return tuple(visible)

    @staticmethod
    def _latest_rows(
        tx: ContinuityTransaction,
        rows: tuple[dict[str, object], ...],
        effective_at: datetime,
        known_at: datetime,
    ) -> tuple[dict[str, object], ...]:
        current: dict[str, tuple[datetime, dict[str, object]]] = {}
        for row in rows:
            version = tx.get_version(RecordVersionId.parse(str(row["version_id"])))
            if (
                version is None
                or version.recorded_at > known_at
                or not version.effective.contains(effective_at)
            ):
                continue
            prior = current.get(str(row["record_id"]))
            if prior is None or version.recorded_at > prior[0]:
                current[str(row["record_id"])] = (version.recorded_at, row)
        return tuple(
            value[1]
            for value in sorted(current.values(), key=lambda value: str(value[1]["version_id"]))
        )

    def _eligible_assignments(
        self,
        tx: ContinuityTransaction,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        responsibility: dict[str, object],
        effective_at: datetime,
        known_at: datetime,
    ) -> tuple[dict[str, object], ...]:
        rows = tx.projection_rows(
            "responsibility_assignment_versions",
            signature_digest=str(responsibility["signature_digest"]),
        )
        latest = PractitionerQueryService._latest_rows(tx, rows, effective_at, known_at)
        visible: list[dict[str, object]] = []
        for row in latest:
            required = self._slice_c_required_versions(tx, row)
            if (
                row["state"] == "ASSIGNED"
                and required is not None
                and all(
                    self._source_visible(
                        tx,
                        principal_id,
                        actor_id,
                        case_id,
                        version_id,
                        effective_at,
                        known_at,
                    )
                    for version_id in required
                )
            ):
                visible.append(row)
        return tuple(visible)

    def _one_responsibility_state(
        self,
        tx: ContinuityTransaction,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        responsibility: dict[str, object],
        effective_at: datetime,
        known_at: datetime,
    ) -> str:
        assignments = self._eligible_assignments(
            tx,
            principal_id,
            actor_id,
            case_id,
            responsibility,
            effective_at,
            known_at,
        )
        if not assignments:
            return "RESPONSIBILITY NOT ESTABLISHED"
        if len(assignments) != 1:
            return "RESPONSIBILITY CONFLICT — UNRESOLVED"
        return "ONE"

    def _responsibility_state(
        self,
        tx: ContinuityTransaction,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        rows: tuple[dict[str, object], ...],
        effective_at: datetime,
        known_at: datetime,
    ) -> str:
        states = {
            self._one_responsibility_state(
                tx,
                principal_id,
                actor_id,
                case_id,
                row,
                effective_at,
                known_at,
            )
            for row in rows
        }
        if "RESPONSIBILITY CONFLICT — UNRESOLVED" in states:
            return "RESPONSIBILITY CONFLICT — UNRESOLVED"
        if "RESPONSIBILITY NOT ESTABLISHED" in states:
            return "RESPONSIBILITY NOT ESTABLISHED"
        return "ONE" if states else "NO PROSPECTIVE RESPONSIBILITY SOURCE"

    @staticmethod
    def _work_state(rows: tuple[dict[str, object], ...]) -> str:
        states = sorted({str(row["state"]) for row in rows})
        return ", ".join(states) if states else "NO DURABLE WORK SOURCE"

    def _allowed(
        self,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        action: str,
        source_version_id: RecordVersionId | None = None,
        source_family: str | None = None,
        effective_at: datetime | None = None,
        known_at: datetime | None = None,
        *,
        write: bool = False,
    ) -> bool:
        return self._access.authorize(
            principal_id=principal_id,
            actor_id=str(actor_id),
            action=action,
            case_id=case_id,
            write=write,
            source_version_id=source_version_id,
            source_family=source_family,
            effective_at=effective_at,
            known_at=known_at,
        )

    def _initial_assessment_setup_attention(
        self,
        tx: ContinuityTransaction,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        responsibilities: tuple[dict[str, object], ...],
        governing: tuple[RecordVersionId, ...],
        governing_id: RecordVersionId | None,
        effective_at: datetime,
        known_at: datetime,
    ) -> AttentionItem | None:
        """Expose the exact missing setup step without inferring authority."""

        lane_obligations = {
            "FINISH_VALUE_ASSESSMENT",
            "FINISH_RISK_ASSESSMENT",
        }
        if any(str(row["obligation_kind"]) in lane_obligations for row in responsibilities):
            return None
        all_responsibilities = self._latest_rows(
            tx,
            tx.projection_rows("responsibility_versions", owning_case_id=str(case_id)),
            effective_at,
            known_at,
        )
        if len(all_responsibilities) != len(responsibilities):
            return None
        continuity = tuple(
            row for row in responsibilities if row["obligation_kind"] == "DETERMINE_CASE_CONTINUITY"
        )
        if len(continuity) != 1 or len(governing) != 1 or governing_id is None:
            return None
        if (
            self._one_responsibility_state(
                tx,
                principal_id,
                actor_id,
                case_id,
                continuity[0],
                effective_at,
                known_at,
            )
            != "ONE"
        ):
            return None
        assignments = self._eligible_assignments(
            tx,
            principal_id,
            actor_id,
            case_id,
            continuity[0],
            effective_at,
            known_at,
        )
        if len(assignments) != 1 or assignments[0]["actor_id"] != str(actor_id):
            return None
        responsibility_id = RecordVersionId.parse(str(continuity[0]["version_id"]))
        assignment_id = RecordVersionId.parse(str(assignments[0]["version_id"]))
        basis_id = RecordVersionId.parse(str(assignments[0]["assignment_basis_version_id"]))
        basis_rows = tx.projection_rows("assignment_basis_versions", version_id=str(basis_id))
        if len(basis_rows) != 1:
            return None
        authority_id = RecordVersionId.parse(str(basis_rows[0]["basis_source_version_id"]))
        case_versions = self._current_family(
            tx, "prospective-case", f"case:{case_id}", effective_at, known_at
        )
        status_versions = self._current_family(
            tx, "case-continuity-status", f"case:{case_id}", effective_at, known_at
        )
        sources = tuple(
            sorted(
                {
                    *case_versions,
                    *status_versions,
                    governing[0],
                    governing_id,
                    responsibility_id,
                    assignment_id,
                    basis_id,
                    authority_id,
                },
                key=str,
            )
        )
        if not sources or not all(
            self._source_visible(
                tx,
                principal_id,
                actor_id,
                case_id,
                source,
                effective_at,
                known_at,
            )
            for source in sources
        ):
            return None
        can_setup = self._allowed(
            principal_id,
            actor_id,
            case_id,
            "case.initial-assessment.setup",
            write=True,
        )
        return AttentionItem(
            case_id,
            "INITIAL_ASSESSMENT_SETUP",
            "Set up responsibility for Value and Risk assessments.",
            (
                "Record the authority source and confirm who will carry each independent "
                "assessment before assessment work begins."
                if can_setup
                else (
                    "An authorized practitioner must establish the two independent "
                    "responsibilities."
                )
            ),
            None,
            None,
            SourceManifest(sources, effective_at, known_at),
            f"/cases/{case_id}/setup/initial-assessments" if can_setup else None,
        )

    def _responsibility_summary(
        self,
        tx: ContinuityTransaction,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        rows: tuple[dict[str, object], ...],
        effective_at: datetime,
        known_at: datetime,
    ) -> str:
        labels = {
            "DETERMINE_CASE_CONTINUITY": "Case continuity",
            "FINISH_VALUE_ASSESSMENT": "Value assessment",
            "FINISH_RISK_ASSESSMENT": "Risk assessment",
        }
        summaries: list[str] = []
        for row in rows:
            label = labels.get(
                str(row["obligation_kind"]),
                str(row["obligation_kind"]).replace("_", " ").title(),
            )
            state = self._one_responsibility_state(
                tx, principal_id, actor_id, case_id, row, effective_at, known_at
            )
            if state == "ONE":
                assignments = self._eligible_assignments(
                    tx,
                    principal_id,
                    actor_id,
                    case_id,
                    row,
                    effective_at,
                    known_at,
                )
                ownership = (
                    "assigned to you"
                    if assignments and assignments[0]["actor_id"] == str(actor_id)
                    else "assigned to another practitioner"
                )
            elif "CONFLICT" in state:
                ownership = "assignment conflict"
            else:
                ownership = "assignment not established"
            summaries.append(f"{label} — {ownership}")
        return "; ".join(summaries) if summaries else "No visible responsibility"

    def _source_visible(
        self,
        tx: ContinuityTransaction,
        principal_id: str,
        actor_id: RecordId,
        case_id: RecordId,
        version_id: RecordVersionId,
        effective_at: datetime,
        known_at: datetime,
    ) -> bool:
        source = tx.get_version(version_id)
        return bool(
            source is not None
            and self._allowed(
                principal_id,
                actor_id,
                case_id,
                "source.read",
                version_id,
                source.family,
                effective_at,
                known_at,
            )
        )
