"""Access-first Home, Case, and Task composition over prospective sources."""

from __future__ import annotations

from datetime import datetime
from typing import cast

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
    AttentionItem,
    CaseView,
    HomeView,
    LanePosition,
    SourceManifest,
    TaskView,
)


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
                items.extend(self._case_attention(tx, actor_id, case_id, effective_at, known_at))
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
            manifest: set[RecordVersionId] = set(continuity.version_ids)
            if len(case_versions) == 1:
                source = tx.get_version(case_versions[0])
                if source is not None:
                    title = cast(str, source.content.get("title", title))
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
                    governing_id = RecordVersionId.parse(str(rows[0]["configuration_version_id"]))
                    governing_state = "ONE"
                    manifest.update((governing[0], governing_id))
            elif len(governing) > 1:
                governing_state = "GOVERNING CONFIGURATION CONFLICT — UNRESOLVED"
                manifest.update(governing)
            responsibilities = self._current_responsibilities(tx, case_id, effective_at, known_at)
            work = self._current_work(tx, case_id, effective_at, known_at)
            value_position = self._lane_position(
                tx, "VALUE", case_id, governing_id, effective_at, known_at
            )
            risk_position = self._lane_position(
                tx, "RISK", case_id, governing_id, effective_at, known_at
            )
            manifest.update(
                RecordVersionId.parse(str(row["version_id"])) for row in responsibilities
            )
            manifest.update(RecordVersionId.parse(str(row["version_id"])) for row in work)
            for lane_position in (value_position, risk_position):
                if lane_position is not None:
                    manifest.update(lane_position.source_version_ids)
            position = (
                "Case continuity: "
                f"{continuity.status.value if continuity.status else continuity.kind.value}",
                f"Governing configuration: {governing_state}",
                f"Responsibilities: {len(responsibilities)} visible exact source(s)",
                f"Durable work: {len(work)} visible exact source(s)",
            )
            return CaseView(
                case_id,
                title,
                continuity.kind,
                continuity.status,
                governing_id,
                governing_state,
                self._responsibility_state(tx, responsibilities, effective_at, known_at),
                self._work_state(work),
                position,
                SourceManifest(tuple(sorted(manifest, key=str)), effective_at, known_at),
                value_position=value_position,
                risk_position=risk_position,
            )

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
            if exact is None:
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
            if responsibility is None:
                raise ValueError("owning Responsibility is not established")
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
        actor_id: RecordId,
        case_id: RecordId,
        effective_at: datetime,
        known_at: datetime,
    ) -> tuple[AttentionItem, ...]:
        responsibilities = self._current_responsibilities(tx, case_id, effective_at, known_at)
        work = self._current_work(tx, case_id, effective_at, known_at)
        result: list[AttentionItem] = []
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
            state = self._one_responsibility_state(tx, row, effective_at, known_at)
            if state == "ONE":
                assignments = self._eligible_assignments(tx, row, effective_at, known_at)
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
            }.get(obligation)
            if lane_question and not self._lane_attention_required(
                tx, obligation, case_id, effective_at, known_at
            ):
                continue
            result.append(
                AttentionItem(
                    case_id,
                    lane_question[0] if lane_question and state == "ONE" else state,
                    lane_question[1]
                    if lane_question
                    else f"Who will carry {obligation} for this exact Case context?",
                    "The governed act cannot proceed until accountability is exact.",
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

    @staticmethod
    def _lane_attention_required(
        tx: ContinuityTransaction,
        obligation: str,
        case_id: RecordId,
        effective_at: datetime,
        known_at: datetime,
    ) -> bool:
        lane = "VALUE" if "VALUE" in obligation else "RISK"
        lane_rows = PractitionerQueryService._slice_c_lane_rows(
            tx, lane, case_id, None, effective_at, known_at
        )
        readiness = lane_rows["readiness"]
        adequacy = lane_rows["adequacy"]
        reliance = lane_rows["reliance"]
        if obligation.startswith("FINISH_"):
            return not readiness
        if obligation.startswith("REVIEW_"):
            return bool(readiness) and not adequacy
        if obligation.startswith("DESIGNATE_"):
            return any(row.get("outcome") == "ADEQUATE" for row in adequacy) and not reliance
        return True

    @staticmethod
    def _lane_position(
        tx: ContinuityTransaction,
        lane: str,
        case_id: RecordId,
        configuration_version_id: RecordVersionId | None,
        effective_at: datetime,
        known_at: datetime,
    ) -> LanePosition | None:
        if configuration_version_id is None:
            return None
        lane_rows = PractitionerQueryService._slice_c_lane_rows(
            tx,
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
            current = lane_rows[field]
            if len(current) > 1:
                values[field] = "CONFLICT — UNRESOLVED"
            elif len(current) == 1:
                values[field] = str(current[0].get("outcome") or established)
                manifest.add(RecordVersionId.parse(str(current[0]["version_id"])))
                assessment_id = current[0].get("assessment_version_id")
                if assessment_id:
                    manifest.add(RecordVersionId.parse(str(assessment_id)))
        if not manifest:
            return None
        return LanePosition(
            lane,
            values["assessment"],
            values["readiness"],
            values["adequacy"],
            values["reliance"],
            tuple(sorted(manifest, key=str)),
        )

    @staticmethod
    def _slice_c_lane_rows(
        tx: ContinuityTransaction,
        lane: str,
        case_id: RecordId,
        configuration_version_id: RecordVersionId | None,
        effective_at: datetime,
        known_at: datetime,
    ) -> dict[str, tuple[dict[str, object], ...]]:
        filters: dict[str, object] = {"lane": lane, "case_id": str(case_id)}
        if configuration_version_id is not None:
            filters["configuration_version_id"] = str(configuration_version_id)
        assessment = PractitionerQueryService._current_projection_rows(
            tx,
            tx.projection_rows("assessment_candidate_versions", **filters),
            effective_at,
            known_at,
        )
        assessment_ids = {str(row["version_id"]) for row in assessment}
        readiness = tuple(
            row
            for row in PractitionerQueryService._current_projection_rows(
                tx,
                tx.projection_rows("assessment_readiness_versions", **filters),
                effective_at,
                known_at,
            )
            if str(row["assessment_version_id"]) in assessment_ids
        )
        readiness_ids = {str(row["version_id"]) for row in readiness}
        adequacy = tuple(
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
        adequate_ids = {
            str(row["version_id"]) for row in adequacy if row.get("outcome") == "ADEQUATE"
        }
        reliance = tuple(
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
        return {
            "assessment": assessment,
            "readiness": readiness,
            "adequacy": adequacy,
            "reliance": reliance,
        }

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

    @staticmethod
    def _current_responsibilities(
        tx: ContinuityTransaction, case_id: RecordId, effective_at: datetime, known_at: datetime
    ) -> tuple[dict[str, object], ...]:
        rows = tx.projection_rows("responsibility_versions", owning_case_id=str(case_id))
        return PractitionerQueryService._latest_rows(tx, rows, effective_at, known_at)

    @staticmethod
    def _current_work(
        tx: ContinuityTransaction, case_id: RecordId, effective_at: datetime, known_at: datetime
    ) -> tuple[dict[str, object], ...]:
        rows = tx.projection_rows("case_work_versions", owning_case_id=str(case_id))
        return PractitionerQueryService._latest_rows(tx, rows, effective_at, known_at)

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

    @staticmethod
    def _eligible_assignments(
        tx: ContinuityTransaction,
        responsibility: dict[str, object],
        effective_at: datetime,
        known_at: datetime,
    ) -> tuple[dict[str, object], ...]:
        rows = tx.projection_rows(
            "responsibility_assignment_versions",
            signature_digest=str(responsibility["signature_digest"]),
        )
        latest = PractitionerQueryService._latest_rows(tx, rows, effective_at, known_at)
        return tuple(row for row in latest if row["state"] == "ASSIGNED")

    @staticmethod
    def _one_responsibility_state(
        tx: ContinuityTransaction,
        responsibility: dict[str, object],
        effective_at: datetime,
        known_at: datetime,
    ) -> str:
        assignments = PractitionerQueryService._eligible_assignments(
            tx, responsibility, effective_at, known_at
        )
        if not assignments:
            return "RESPONSIBILITY NOT ESTABLISHED"
        if len(assignments) != 1:
            return "RESPONSIBILITY CONFLICT — UNRESOLVED"
        return "ONE"

    @staticmethod
    def _responsibility_state(
        tx: ContinuityTransaction,
        rows: tuple[dict[str, object], ...],
        effective_at: datetime,
        known_at: datetime,
    ) -> str:
        states = {
            PractitionerQueryService._one_responsibility_state(tx, row, effective_at, known_at)
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
        self, principal_id: str, actor_id: RecordId, case_id: RecordId, action: str
    ) -> bool:
        return self._access.authorize(
            principal_id=principal_id,
            actor_id=str(actor_id),
            action=action,
            case_id=case_id,
            write=False,
        )
