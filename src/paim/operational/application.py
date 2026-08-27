"""Authenticated gateway over the existing PAIM Increment 1-7 services."""

from __future__ import annotations

import csv
import hashlib
import hmac
import json
import secrets
from collections.abc import Callable, Mapping
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import NoReturn, TypeVar, cast

from sqlalchemy.exc import SQLAlchemyError

from paim.application import (
    DomainPreconditionFailed,
    DomainRuleViolation,
    Increment7ApplicationService,
    StalePrecondition,
)
from paim.application.practitioner import (
    ActorContext,
    CaseListView,
    CaseOrientationView,
    CaseSummary,
    CaseWorkspaceView,
    HomeView,
    PractitionerQueryService,
)
from paim.assessment_review import (
    AdequacyFacts,
    AdequacyOutcome,
    AssessmentContent,
    AssessmentLane,
    AssessmentReviewService,
    CandidateDisposition,
    DesignateRelianceCommand,
    DetermineAdequacyCommand,
    FinishAssessmentCommand,
    FinishFacts,
    RelianceFacts,
)
from paim.assessment_review import (
    CommandIdentity as AssessmentCommandIdentity,
)
from paim.audit import ActorResolution
from paim.case_continuity import (
    CaseContinuityService,
    CaseInitiationAuthorityCommand,
    CaseInitiationAuthorityState,
    MinimalOpenCaseCommand,
)
from paim.case_continuity import (
    CommandIdentity as ContinuityCommandIdentity,
)
from paim.continuing_review import (
    BeginReviewEpisodeCommand,
    CompleteReviewEpisodeCommand,
    ContinuingReviewService,
    EstablishPlannedReviewPointCommand,
    PlannedReviewPointSpec,
    ReviewFocus,
    ReviewOrigin,
    ReviewOutcome,
    ReviewRecordFacts,
)
from paim.domain import (
    AccountabilityConflict,
    AccountabilityFound,
    CommandMeta,
    ProjectionConsistency,
    RegisterAction,
    RegisterActionLaunch,
    RegisterConcernEntry,
    RegisterLifecycle,
    RegisterManifest,
    RegisterQuery,
    RegisterView,
    RoleTargetType,
)
from paim.integrity import (
    Clock,
    CommandId,
    RecordId,
    RecordVersionId,
    SystemClock,
    to_epoch_microseconds,
)
from paim.integrity.records import JsonValue
from paim.integrity.selection import SelectionFound, SelectionQuery
from paim.integrity.semantics import (
    ContextMemberKind,
    ExactContextMember,
    ExactContextSet,
    SemanticContractRef,
)
from paim.operational.models import (
    UNSUPPORTED_CAPABILITIES,
    AccessDenied,
    AccessEffect,
    AccessGrantInput,
    AccountabilityCheck,
    AccountableAssignmentView,
    AdapterType,
    AuthenticatedSession,
    AuthenticationFailed,
    BackupManifest,
    DeliveryResult,
    DeliveryStatus,
    HealthReport,
    IntakeEnvelope,
    IntakeResult,
    IntakeStatus,
    LocalConfiguration,
    Permission,
    PrincipalStatus,
    ScopeType,
    SourceAccessGrantInput,
    UnsupportedCapability,
)
from paim.operational.recovery import create_backup, health_report, restore_backup
from paim.operational.store import OperationalStore
from paim.persistence.ports import CommandOutcome, WriterContention
from paim.persistence.sqlite import SQLiteIntegrityStore
from paim.practitioner_queries import (
    CaseView as ProspectiveCaseView,
)
from paim.practitioner_queries import (
    HomeView as ProspectiveHomeView,
)
from paim.practitioner_queries import (
    PractitionerQueryService as ProspectivePractitionerQueryService,
)
from paim.practitioner_queries import (
    TaskView as ProspectiveTaskView,
)
from paim.prospective_decision import (
    AuthorizationFacts,
    AuthorizeDecisionCommand,
    ConfirmationFacts,
    ConfirmDecisionCommand,
    DecisionFacts,
    IntegrateValueRiskCommand,
    IntegrationFacts,
    ProposeDecisionCommand,
    ProspectiveDecisionService,
    ReliedLaneBasis,
)
from paim.reconstruction import CaseTimeline, ReconstructionService, ThenNowComparison
from paim.responsibility.models import ObligationKind
from paim.responsibility.service import OperationalSliceAAccessPolicy
from paim.slice_h_actions import (
    SliceHActionContext,
    SliceHActionContextResolver,
    json_version_ids,
)

T = TypeVar("T")
_ITERATIONS = 600_000
_MAX_INTAKE_BYTES = 1_048_576
_ACTOR_BOUND_ACTIONS = frozenset(
    {
        "decision.authorize",
        "completion.accept",
        "activation.authorize",
        "reassessment.confirm",
        "reassessment.successor",
        "shared-dependency.determine",
    }
)


class OperationalApplication:
    """One local, authenticated, access-controlled PAIM application boundary."""

    def __init__(self, config: LocalConfiguration, clock: Clock | None = None) -> None:
        self.config = config
        self.clock = clock or SystemClock()
        self.domain_store = SQLiteIntegrityStore(config.database_url)
        self.operational_store = OperationalStore(config.database_url, config.event_log_path)
        self._service = Increment7ApplicationService(self.domain_store, self.clock)
        self._practitioner_queries = PractitionerQueryService(self.domain_store)
        self._prospective_access = OperationalSliceAAccessPolicy(self.operational_store)
        self._case_continuity = CaseContinuityService(
            self.domain_store, self.clock, self._prospective_access
        )
        self._assessment_review = AssessmentReviewService(
            self.domain_store, self.clock, self._prospective_access
        )
        self._prospective_decision = ProspectiveDecisionService(
            self.domain_store, self.clock, self._prospective_access
        )
        self._continuing_review = ContinuingReviewService(
            self.domain_store, self.clock, self._prospective_access
        )
        self._slice_h_actions = SliceHActionContextResolver(
            self.domain_store, self._prospective_access
        )
        self._prospective_queries = ProspectivePractitionerQueryService(
            self.domain_store, self._case_continuity, self._prospective_access
        )
        self._reconstruction = ReconstructionService(self.domain_store, self._prospective_access)
        self._register_queries: dict[str, RegisterQuery] = {}

    def close(self) -> None:
        self.domain_store.dispose()
        self.operational_store.dispose()

    def __enter__(self) -> OperationalApplication:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    @staticmethod
    def _credential(token: str, salt_hex: str, iterations: int) -> str:
        return hashlib.pbkdf2_hmac(
            "sha256", token.encode("utf-8"), bytes.fromhex(salt_hex), iterations
        ).hex()

    def bootstrap_principal(
        self,
        *,
        principal_id: str,
        token: str,
        actor_id: RecordId | None,
        grants: tuple[AccessGrantInput, ...],
    ) -> None:
        """Create the first explicit principal; there is no default identity."""
        if not principal_id.strip() or len(token) < 20:
            raise ValueError(
                "explicit principal and a credential of at least 20 characters required"
            )
        with self.operational_store.read() as connection:
            count = int(
                connection.exec_driver_sql("SELECT COUNT(*) FROM operational_principals").scalar()
                or 0
            )
        if count:
            raise AccessDenied("initial bootstrap is closed after the first principal")
        now = self.clock.now()
        salt = secrets.token_hex(16)
        self.operational_store.add_principal_version(
            version_id=str(RecordId.new()),
            principal_id=principal_id,
            actor_id=actor_id,
            status=PrincipalStatus.ENABLED,
            credential_salt=salt,
            credential_verifier=self._credential(token, salt, _ITERATIONS),
            credential_iterations=_ITERATIONS,
            recorded_at=now,
            recorded_by=principal_id,
        )
        for grant in grants:
            self.operational_store.add_access_grant(
                grant_id=str(RecordId.new()),
                principal_id=principal_id,
                value=grant,
                recorded_at=now,
                recorded_by=principal_id,
            )
        self._audit(
            category="CONFIGURATION",
            outcome="SUCCESS",
            principal_id=principal_id,
            actor_id=actor_id,
            action="bootstrap-principal",
            reason="EXPLICIT_INITIAL_BOOTSTRAP",
            details={"grant_count": len(grants), "actor_mapping": actor_id is not None},
        )

    def provision_principal(
        self,
        session: AuthenticatedSession,
        *,
        principal_id: str,
        token: str,
        actor_id: RecordId | None,
        status: PrincipalStatus,
    ) -> None:
        self._require(session, Permission.OPERATIONAL_ADMIN, "principal.manage")
        if len(token) < 20:
            raise ValueError("credential must contain at least 20 characters")
        salt = secrets.token_hex(16)
        self.operational_store.add_principal_version(
            version_id=str(RecordId.new()),
            principal_id=principal_id,
            actor_id=actor_id,
            status=status,
            credential_salt=salt,
            credential_verifier=self._credential(token, salt, _ITERATIONS),
            credential_iterations=_ITERATIONS,
            recorded_at=self.clock.now(),
            recorded_by=session.principal_id,
        )
        self._audit_session(
            session,
            category="ADMIN",
            outcome="SUCCESS",
            action="principal.manage",
            reason="PRINCIPAL_VERSION_APPENDED",
            details={"subject_principal": principal_id, "status": status.value},
        )

    def grant_access(
        self,
        session: AuthenticatedSession,
        *,
        principal_id: str,
        grant: AccessGrantInput,
    ) -> None:
        self._require(session, Permission.OPERATIONAL_ADMIN, "access.manage")
        if not self.operational_store.principal_exists(principal_id):
            raise ValueError("access subject principal is not established")
        if grant.scope_type is ScopeType.GLOBAL and grant.scope_id is not None:
            raise ValueError("global access cannot carry a scope ID")
        if grant.scope_type is not ScopeType.GLOBAL and grant.scope_id is None:
            raise ValueError("scoped access requires an exact scope ID")
        self.operational_store.add_access_grant(
            grant_id=str(RecordId.new()),
            principal_id=principal_id,
            value=grant,
            recorded_at=self.clock.now(),
            recorded_by=session.principal_id,
        )
        self._audit_session(
            session,
            category="ADMIN",
            outcome="SUCCESS",
            action="access.manage",
            reason="SOFTWARE_ACCESS_FACT_APPENDED",
            details={
                "subject_principal": principal_id,
                "permission": grant.permission.value,
                "action": grant.action,
                "scope_type": grant.scope_type.value,
                "scope_id": str(grant.scope_id) if grant.scope_id else None,
                "effect": grant.effect.value,
            },
        )

    def grant_source_access(
        self,
        session: AuthenticatedSession,
        *,
        principal_id: str,
        grant: SourceAccessGrantInput,
    ) -> None:
        """Append exact-source visibility without conferring substantive authority."""

        self._require(session, Permission.OPERATIONAL_ADMIN, "source-access.manage")
        if not self.operational_store.principal_exists(principal_id):
            raise ValueError("access subject principal is not established")
        with self.domain_store.read_transaction() as transaction:
            source = transaction.get_version(grant.source_version_id)
        if source is None or source.family != grant.source_family:
            raise ValueError("exact source context is not established")
        if grant.case_id not in self.operational_store.all_case_ids():
            raise ValueError("source-access Case is not established")
        if grant.configuration_id is not None and (
            self.operational_store.configuration_case(grant.configuration_id) != grant.case_id
        ):
            raise ValueError("source-access Configuration is not in the exact Case")
        self.operational_store.add_source_access_grant(
            grant_id=str(RecordId.new()),
            principal_id=principal_id,
            value=grant,
            recorded_at=self.clock.now(),
            recorded_by=session.principal_id,
        )
        self._audit_session(
            session,
            category="ADMIN",
            outcome="SUCCESS",
            action="source-access.manage",
            reason="SOURCE_ACCESS_FACT_APPENDED",
            details={
                "subject_principal": principal_id,
                "action": grant.action,
                "case_id": str(grant.case_id),
                "configuration_id": (
                    str(grant.configuration_id) if grant.configuration_id else None
                ),
                "source_version_id": str(grant.source_version_id),
                "source_family": grant.source_family,
                "effect": grant.effect.value,
            },
            case_id=grant.case_id,
            configuration_id=grant.configuration_id,
        )

    def authenticate(
        self, principal_id: str, token: str, *, correlation_id: str | None = None
    ) -> AuthenticatedSession:
        now = self.clock.now()
        correlation = correlation_id or str(RecordId.new())
        principal = self.operational_store.current_principal(principal_id)
        verified = False
        if principal is not None:
            supplied = self._credential(
                token, principal.credential_salt, principal.credential_iterations
            )
            verified = hmac.compare_digest(supplied, principal.credential_verifier)
        if principal is None or not verified or principal.status is not PrincipalStatus.ENABLED:
            self._audit(
                category="AUTHENTICATION",
                outcome="FAILURE",
                principal_id=principal_id,
                actor_id=None,
                action="login",
                reason=(
                    "PRINCIPAL_NOT_ENABLED"
                    if principal is not None and principal.status is not PrincipalStatus.ENABLED
                    else "CREDENTIAL_NOT_ESTABLISHED"
                ),
                details={"authenticated": False},
                correlation_id=correlation,
            )
            raise AuthenticationFailed("authentication not established")
        if not self.operational_store.permission_allowed(principal_id, Permission.LOGIN, "use"):
            self._audit(
                category="ACCESS",
                outcome="DENIED",
                principal_id=principal_id,
                actor_id=principal.actor_id,
                action="login",
                reason="LOGIN_PERMISSION_NOT_ESTABLISHED",
                details={"authenticated": True},
                correlation_id=correlation,
            )
            raise AccessDenied("application login permission not established")
        session = AuthenticatedSession(principal_id, principal.actor_id, correlation, now)
        self._audit_session(
            session,
            category="AUTHENTICATION",
            outcome="SUCCESS",
            action="login",
            reason="CREDENTIAL_VERIFIED",
            details={"authenticated": True},
        )
        self._audit_session(
            session,
            category="ACTOR_RESOLUTION",
            outcome="SUCCESS" if principal.actor_id else "FAILURE",
            action="principal.resolve",
            reason=("ACTOR_RESOLVED" if principal.actor_id else "ACTOR_NOT_ESTABLISHED"),
            details={"resolved": principal.actor_id is not None},
        )
        return session

    def revalidate_session(self, session: AuthenticatedSession) -> None:
        """Fail closed when current principal status or Actor mapping has changed."""
        self._validate_session(session, "browser.session")

    def slice_h_home(
        self,
        session: AuthenticatedSession,
        *,
        effective_at: datetime | None = None,
        known_at: datetime | None = None,
    ) -> ProspectiveHomeView:
        """Compose the Slice-H Home surface from exact prospective sources."""

        actor_id, effective, known = self._slice_h_context(
            session, effective_at=effective_at, known_at=known_at
        )
        return self._prospective_queries.home(
            principal_id=session.principal_id,
            actor_id=actor_id,
            candidate_case_ids=self._prospective_case_ids(session),
            effective_at=effective,
            known_at=known,
        )

    def slice_h_case(
        self,
        session: AuthenticatedSession,
        case_id: RecordId,
        *,
        effective_at: datetime | None = None,
        known_at: datetime | None = None,
    ) -> ProspectiveCaseView:
        """Compose one continuing Case without a persisted master status."""

        actor_id, effective, known = self._slice_h_context(
            session, effective_at=effective_at, known_at=known_at
        )
        if case_id not in self._prospective_case_ids(session):
            raise AccessDenied("prospective Case is not visible")
        return self._prospective_queries.case(
            principal_id=session.principal_id,
            actor_id=actor_id,
            case_id=case_id,
            effective_at=effective,
            known_at=known,
        )

    def slice_h_task(
        self,
        session: AuthenticatedSession,
        case_id: RecordId,
        work_version_id: RecordVersionId,
        *,
        effective_at: datetime | None = None,
        known_at: datetime | None = None,
    ) -> ProspectiveTaskView:
        """Reconstruct durable Work context; browser state is never continuity authority."""

        actor_id, effective, known = self._slice_h_context(
            session, effective_at=effective_at, known_at=known_at
        )
        return self._prospective_queries.task(
            principal_id=session.principal_id,
            actor_id=actor_id,
            case_id=case_id,
            work_version_id=work_version_id,
            effective_at=effective,
            known_at=known,
        )

    def slice_h_action_context(
        self,
        session: AuthenticatedSession,
        case_id: RecordId,
        responsibility_version_id: RecordVersionId,
        *,
        effective_at: datetime | None = None,
        known_at: datetime | None = None,
    ) -> SliceHActionContext:
        """Reconstruct exact action context from durable governed facts only."""

        actor_id, effective, known = self._slice_h_context(
            session, effective_at=effective_at, known_at=known_at
        )
        if case_id not in self._prospective_case_ids(session):
            raise AccessDenied("prospective Case is not visible")
        try:
            return self._slice_h_actions.resolve(
                principal_id=session.principal_id,
                actor_id=actor_id,
                case_id=case_id,
                responsibility_version_id=responsibility_version_id,
                effective_at=effective,
                known_at=known,
            )
        except ValueError as exc:
            raise AccessDenied(str(exc)) from exc

    def slice_h_commit_action(
        self,
        session: AuthenticatedSession,
        *,
        case_id: RecordId,
        responsibility_version_id: RecordVersionId,
        expected_source_version_ids: tuple[RecordVersionId, ...],
        action: str,
        payload: Mapping[str, str],
        idempotency_key: str,
        effective_at: datetime,
    ) -> CommandOutcome:
        """Commit one ordinary judgment through its accepted production service.

        The exact context is reconstructed again at commit. A browser-supplied
        identity can select only the previously reviewed Responsibility; it can
        never retarget any downstream source.
        """

        self._require(session, Permission.COMMAND, action, ScopeType.CASE, case_id)
        context = self.slice_h_action_context(
            session,
            case_id,
            responsibility_version_id,
            effective_at=effective_at,
            known_at=self.clock.now(),
        )
        if context.source_version_ids != expected_source_version_ids:
            raise AccessDenied("the reviewed exact context changed; no retarget permitted")
        if session.actor_id is None:
            raise AccessDenied("current Actor mapping is not established")
        identity = AssessmentCommandIdentity(
            CommandId.new(),
            "slice-h-practitioner-action",
            idempotency_key,
            session.principal_id,
            session.actor_id,
        )
        now = self.clock.now()

        def lines(name: str) -> tuple[str, ...]:
            return tuple(
                value.strip() for value in payload.get(name, "").splitlines() if value.strip()
            )

        if action in {"assessment.finish.value", "assessment.finish.risk"}:
            lane = AssessmentLane.VALUE if action.endswith("value") else AssessmentLane.RISK
            if context.lane is not lane:
                raise AccessDenied("task lane does not match the exact Responsibility")
            return self._assessment_review.finish_assessment(
                FinishAssessmentCommand(
                    identity,
                    FinishFacts.new(),
                    SemanticContractRef("paim.assessment-review", "1.0"),
                    context.context,
                    lane,
                    case_id,
                    context.configuration_version_id,
                    AssessmentContent(
                        payload["finding"],
                        payload["boundary"],
                        payload["uncertainty"],
                        payload["implication"],
                        payload["provenance"],
                    ),
                    context.decision_use,
                    context.bounded_scope,
                    context.information_basis_version_ids,
                    context.responsibility_version_id,
                    context.assignment_version_id,
                    context.current_assessment_version_id,
                    payload["rationale"],
                    lines("limitations"),
                    effective_at,
                    now,
                )
            )
        if action in {"assessment.adequacy.value", "assessment.adequacy.risk"}:
            lane = AssessmentLane.VALUE if action.endswith("value") else AssessmentLane.RISK
            if (
                context.lane is not lane
                or context.current_assessment_version_id is None
                or context.current_readiness_version_id is None
            ):
                raise AccessDenied("the exact assessment is not ready for this review")
            outcome = AdequacyOutcome(payload["outcome"])
            reasons = lines("material_reasons")
            return self._assessment_review.determine_adequacy(
                DetermineAdequacyCommand(
                    identity,
                    AdequacyFacts.new(),
                    SemanticContractRef("paim.assessment-review", "1.0"),
                    context.context,
                    lane,
                    case_id,
                    context.configuration_version_id,
                    context.current_assessment_version_id,
                    context.current_readiness_version_id,
                    context.decision_use,
                    context.bounded_scope,
                    context.information_basis_version_ids,
                    outcome,
                    reasons,
                    payload["rationale"],
                    lines("limitations"),
                    payload["uncertainty"],
                    context.responsibility_version_id,
                    context.assignment_version_id,
                    context.current_adequacy_version_id,
                    effective_at,
                    now,
                )
            )
        if action in {"assessment.reliance.value", "assessment.reliance.risk"}:
            lane = AssessmentLane.VALUE if action.endswith("value") else AssessmentLane.RISK
            if context.lane is not lane or not context.reliance_candidate_version_ids:
                raise AccessDenied("one exact adequate assessment is not available")
            choice = payload.get("candidate_choice", "candidate-1")
            try:
                choice_index = int(choice.removeprefix("candidate-")) - 1
                assessment_id = context.reliance_candidate_version_ids[choice_index]
            except (IndexError, ValueError) as exc:
                raise AccessDenied("the selected adequate assessment is unavailable") from exc
            with self.domain_store.read_transaction() as transaction:
                readiness_rows = transaction.projection_rows(
                    "assessment_readiness_versions",
                    assessment_version_id=str(assessment_id),
                )
                adequacy_rows = transaction.projection_rows(
                    "assessment_adequacy_versions",
                    assessment_version_id=str(assessment_id),
                    outcome="ADEQUATE",
                )
            if len(readiness_rows) != 1 or len(adequacy_rows) != 1:
                raise AccessDenied("the selected adequate assessment is unavailable")
            readiness_id = RecordVersionId.parse(str(readiness_rows[0]["version_id"]))
            adequacy_id = RecordVersionId.parse(str(adequacy_rows[0]["version_id"]))
            information_basis = context.reliance_candidate_information_basis[choice_index]
            dispositions = tuple(
                CandidateDisposition(
                    candidate_id,
                    "NOT_SELECTED_FOR_THIS_USE",
                    payload["rationale"],
                )
                for candidate_id in context.reliance_candidate_version_ids
                if candidate_id != assessment_id
            )
            return self._assessment_review.designate_reliance(
                DesignateRelianceCommand(
                    identity,
                    RelianceFacts.new(),
                    SemanticContractRef("paim.assessment-review", "1.0"),
                    context.context,
                    lane,
                    case_id,
                    context.configuration_version_id,
                    assessment_id,
                    readiness_id,
                    adequacy_id,
                    context.decision_use,
                    context.bounded_scope,
                    information_basis,
                    dispositions,
                    payload["rationale"],
                    context.responsibility_version_id,
                    context.assignment_version_id,
                    context.current_reliance_version_id,
                    effective_at,
                    now,
                )
            )
        if action == "integration.complete":
            value = self._slice_h_relied_basis(context, AssessmentLane.VALUE)
            risk = self._slice_h_relied_basis(context, AssessmentLane.RISK)
            return self._prospective_decision.integrate_value_risk(
                IntegrateValueRiskCommand(
                    identity,
                    IntegrationFacts.new(),
                    SemanticContractRef("paim.prospective-integration-decision", "1.0"),
                    context.context,
                    case_id,
                    context.configuration_version_id,
                    context.decision_use,
                    context.bounded_scope,
                    value,
                    risk,
                    payload["rationale"],
                    lines("material_tensions"),
                    lines("limitations"),
                    payload["uncertainty"],
                    lines("unresolved_conditions"),
                    context.responsibility_version_id,
                    context.assignment_version_id,
                    context.authority_source_version_id,
                    context.current_integration_version_id,
                    effective_at,
                    now,
                )
            )
        if action == "decision.propose":
            if context.current_integration_version_id is None:
                raise AccessDenied("one exact current Value/Risk consideration is required")
            return self._prospective_decision.propose_decision(
                ProposeDecisionCommand(
                    identity,
                    DecisionFacts.new(),
                    SemanticContractRef("paim.prospective-integration-decision", "1.0"),
                    context.context,
                    case_id,
                    context.configuration_version_id,
                    context.current_integration_version_id,
                    context.decision_use,
                    context.bounded_scope,
                    payload["proposed_action"],
                    payload["operating_state"],
                    payload["rationale"],
                    lines("conditions"),
                    lines("alternatives"),
                    context.responsibility_version_id,
                    context.assignment_version_id,
                    context.current_decision_version_id,
                    context.current_decision_version_id,
                    effective_at,
                    now,
                )
            )
        if action == "decision.authorize":
            if (
                context.current_decision_version_id is None
                or context.current_decision_status != "PROPOSED"
                or context.current_integration_version_id is None
                or context.authority_identity is None
            ):
                raise AccessDenied("one exact current proposal is required")
            return self._prospective_decision.authorize_decision(
                AuthorizeDecisionCommand(
                    identity,
                    AuthorizationFacts.new(),
                    SemanticContractRef("paim.prospective-integration-decision", "1.0"),
                    context.context,
                    case_id,
                    context.configuration_version_id,
                    context.current_decision_version_id,
                    context.current_integration_version_id,
                    context.decision_use,
                    context.bounded_scope,
                    context.responsibility_version_id,
                    context.assignment_version_id,
                    context.authority_source_version_id,
                    context.authority_identity,
                    context.bounded_scope,
                    lines("authority_limits"),
                    lines("conditions"),
                    lines("dissent"),
                    effective_at,
                    now,
                )
            )
        if action == "decision.confirm":
            if (
                context.current_decision_version_id is None
                or context.current_decision_status != "AUTHORIZED"
                or context.current_integration_version_id is None
            ):
                raise AccessDenied("one exact authorized Decision is required")
            return self._prospective_decision.confirm_decision(
                ConfirmDecisionCommand(
                    identity,
                    ConfirmationFacts.new(),
                    SemanticContractRef("paim.prospective-integration-decision", "1.0"),
                    context.context,
                    case_id,
                    context.configuration_version_id,
                    context.current_decision_version_id,
                    context.current_integration_version_id,
                    context.decision_use,
                    context.bounded_scope,
                    payload["rationale"],
                    context.responsibility_version_id,
                    context.assignment_version_id,
                    context.authority_source_version_id,
                    effective_at,
                    now,
                )
            )
        if action == "review.plan":
            if context.current_decision_version_id is None:
                raise AccessDenied("one exact current Decision is required")
            review_at = datetime.fromisoformat(payload["review_at"].replace("Z", "+00:00"))
            return self._continuing_review.establish_planned_review_point(
                EstablishPlannedReviewPointCommand(
                    identity,
                    SemanticContractRef("paim.continuing-review", "1.0"),
                    context.context,
                    case_id,
                    context.configuration_version_id,
                    context.current_decision_version_id,
                    "continuing management review",
                    context.bounded_scope,
                    PlannedReviewPointSpec(
                        ReviewRecordFacts.new(),
                        review_at,
                        payload["rationale"],
                        (context.current_decision_version_id,),
                    ),
                    context.responsibility_version_id,
                    context.assignment_version_id,
                    None,
                    False,
                    effective_at,
                    now,
                )
            )
        if action == "review.episode.begin":
            if (
                context.current_decision_version_id is None
                or context.current_integration_version_id is None
                or not context.review_origin_version_ids
                or not context.review_focus
            ):
                raise AccessDenied("one exact visible focused-review origin is required")
            value = self._slice_h_relied_basis(context, AssessmentLane.VALUE)
            risk = self._slice_h_relied_basis(context, AssessmentLane.RISK)
            return self._continuing_review.begin_review_episode(
                BeginReviewEpisodeCommand(
                    identity,
                    ReviewRecordFacts.new(),
                    SemanticContractRef("paim.continuing-review", "1.0"),
                    context.context,
                    case_id,
                    context.configuration_version_id,
                    context.current_decision_version_id,
                    context.current_integration_version_id,
                    ReviewOrigin.EVENT_TRIGGER,
                    context.review_origin_version_ids,
                    tuple(ReviewFocus(value) for value in context.review_focus),
                    value.reliance_version_id,
                    risk.reliance_version_id,
                    context.responsibility_version_id,
                    context.assignment_version_id,
                    None,
                    effective_at,
                    now,
                )
            )
        if action == "review.episode.complete":
            if (
                context.current_review_episode_version_id is None
                or context.current_confirmation_version_id is None
            ):
                raise AccessDenied(
                    "an exact focused review and unchanged-Decision confirmation are required"
                )
            value = self._slice_h_relied_basis(context, AssessmentLane.VALUE)
            risk = self._slice_h_relied_basis(context, AssessmentLane.RISK)
            with self.domain_store.read_transaction() as transaction:
                episode = transaction.get_version(context.current_review_episode_version_id)
            if episode is None:
                raise AccessDenied("the exact focused review is unavailable")
            return self._continuing_review.complete_review_episode(
                CompleteReviewEpisodeCommand(
                    identity,
                    ReviewRecordFacts(episode.record_id, RecordVersionId.new()),
                    SemanticContractRef("paim.continuing-review", "1.0"),
                    context.context,
                    case_id,
                    context.configuration_version_id,
                    context.current_review_episode_version_id,
                    ReviewOutcome.UNCHANGED_DECISION_CONFIRMED,
                    (),
                    value.reliance_version_id,
                    risk.reliance_version_id,
                    context.current_confirmation_version_id,
                    None,
                    payload["rationale"],
                    context.responsibility_version_id,
                    context.assignment_version_id,
                    None,
                    None,
                    None,
                    effective_at,
                    now,
                )
            )
        raise ValueError("unsupported contextual Slice-H action")

    def slice_h_carry_single_reliance(
        self,
        session: AuthenticatedSession,
        *,
        case_id: RecordId,
        lane: AssessmentLane,
        effective_at: datetime,
        idempotency_key: str,
    ) -> CommandOutcome | None:
        """Carry one deterministic eligible assessment without a Level-1 choice.

        Reliance remains its own authoritative command and audit outcome. Carriage
        occurs only when the signed-in Actor is the one exact accountable assignee,
        has the exact command permission and source visibility, and one (not zero or
        multiple) eligible adequate assessment exists. Otherwise no fact is written
        and the owning-domain state remains available for explicit resolution.
        """

        action = f"assessment.reliance.{lane.value.lower()}"
        if not self.operational_store.permission_allowed(
            session.principal_id,
            Permission.COMMAND,
            action,
            ScopeType.CASE,
            case_id,
        ):
            return None
        obligation = (
            ObligationKind.DESIGNATE_VALUE_ASSESSMENT_RELIANCE
            if lane is AssessmentLane.VALUE
            else ObligationKind.DESIGNATE_RISK_ASSESSMENT_RELIANCE
        )
        with self.domain_store.read_transaction() as transaction:
            rows = transaction.projection_rows(
                "responsibility_versions",
                owning_case_id=str(case_id),
                obligation_kind=obligation.value,
            )
            current_ids: list[RecordVersionId] = []
            for row in rows:
                version_id = RecordVersionId.parse(str(row["version_id"]))
                source = transaction.get_version(version_id)
                if source is None:
                    continue
                selected = transaction.select_current(
                    SelectionQuery(
                        source.family,
                        source.scope,
                        effective_at,
                        self.clock.now(),
                        source.record_id,
                    )
                )
                if (
                    isinstance(selected, SelectionFound)
                    and selected.candidate.version_id == version_id
                ):
                    current_ids.append(version_id)
        contexts: list[SliceHActionContext] = []
        for responsibility_id in current_ids:
            try:
                context = self.slice_h_action_context(
                    session,
                    case_id,
                    responsibility_id,
                    effective_at=effective_at,
                    known_at=self.clock.now(),
                )
            except AccessDenied:
                continue
            if (
                context.lane is lane
                and context.current_reliance_version_id is None
                and len(context.reliance_candidate_version_ids) == 1
            ):
                contexts.append(context)
        if len(contexts) != 1:
            return None
        context = contexts[0]
        return self.slice_h_commit_action(
            session,
            case_id=case_id,
            responsibility_version_id=context.responsibility_version_id,
            expected_source_version_ids=context.source_version_ids,
            action=action,
            payload={
                "rationale": (
                    "Carried deterministically because exactly one eligible adequate "
                    f"{lane.value.title()} assessment is established for this decision use."
                )
            },
            idempotency_key=idempotency_key,
            effective_at=effective_at,
        )

    def _slice_h_relied_basis(
        self, context: SliceHActionContext, lane: AssessmentLane
    ) -> ReliedLaneBasis:
        rows: tuple[dict[str, object], ...]
        with self.domain_store.read_transaction() as transaction:
            rows = transaction.projection_rows(
                "assessment_reliance_versions",
                lane=lane.value,
                case_id=str(context.case_id),
                configuration_version_id=str(context.configuration_version_id),
                context_digest=context.context.digest,
                decision_use=context.decision_use,
            )
            current: list[dict[str, object]] = []
            for row in rows:
                version_id = RecordVersionId.parse(str(row["version_id"]))
                source = transaction.get_version(version_id)
                if source is None:
                    continue
                selected = transaction.select_current(
                    SelectionQuery(
                        source.family,
                        source.scope,
                        self.clock.now(),
                        self.clock.now(),
                        source.record_id,
                    )
                )
                if (
                    isinstance(selected, SelectionFound)
                    and selected.candidate.version_id == version_id
                ):
                    current.append(row)
        if len(current) != 1:
            raise AccessDenied(f"one exact current {lane.value.title()} reliance is required")
        row = current[0]
        return ReliedLaneBasis(
            lane,
            RecordVersionId.parse(str(row["assessment_version_id"])),
            RecordVersionId.parse(str(row["readiness_version_id"])),
            RecordVersionId.parse(str(row["adequacy_version_id"])),
            RecordVersionId.parse(str(row["version_id"])),
            json_version_ids(row["information_basis_version_ids_json"]),
        )

    def slice_h_timeline(
        self,
        session: AuthenticatedSession,
        case_id: RecordId,
        *,
        effective_at: datetime | None = None,
        known_at: datetime | None = None,
    ) -> CaseTimeline:
        """Return access-filtered dual-time organizational memory for one Case."""

        actor_id, effective, known = self._slice_h_context(
            session, effective_at=effective_at, known_at=known_at
        )
        return self._reconstruction.timeline(
            principal_id=session.principal_id,
            actor_id=actor_id,
            case_id=case_id,
            effective_at=effective,
            known_at=known,
        )

    def slice_h_comparison(
        self,
        session: AuthenticatedSession,
        case_id: RecordId,
        *,
        prior_effective_at: datetime,
        prior_known_at: datetime,
        current_effective_at: datetime | None = None,
        current_known_at: datetime | None = None,
    ) -> ThenNowComparison:
        """Compare two access-safe exact positions without projecting later knowledge back."""

        actor_id, current_effective, current_known = self._slice_h_context(
            session,
            effective_at=current_effective_at,
            known_at=current_known_at,
        )
        prior = self._reconstruction.current_position(
            principal_id=session.principal_id,
            actor_id=actor_id,
            case_id=case_id,
            effective_at=prior_effective_at,
            known_at=prior_known_at,
        )
        current = self._reconstruction.current_position(
            principal_id=session.principal_id,
            actor_id=actor_id,
            case_id=case_id,
            effective_at=current_effective,
            known_at=current_known,
        )
        return self._reconstruction.compare(prior, current)

    def slice_h_initiate_case(
        self,
        session: AuthenticatedSession,
        *,
        idempotency_key: str,
        title: str,
        bounded_use: str,
        management_question: str,
        setup_description: str,
        effective_at: datetime,
        ai_profile: dict[str, JsonValue] | None = None,
        dependencies: tuple[dict[str, JsonValue], ...] = (),
    ) -> CommandOutcome:
        """Use the H0 natural command; no PAIM identity is supplied by the practitioner."""

        self._validate_session(session, "case.create_open")
        if session.actor_id is None:
            raise AccessDenied("current Actor mapping is not established")
        organization_scope = self._case_initiation_scope(
            actor_id=session.actor_id,
            bounded_use=bounded_use,
            effective_at=effective_at,
        )
        return self._case_continuity.initiate_case(
            MinimalOpenCaseCommand(
                ContinuityCommandIdentity(
                    CommandId.new(),
                    "slice-h-case-initiation",
                    idempotency_key,
                    session.principal_id,
                    session.actor_id,
                ),
                SemanticContractRef("paim.case-continuity", "1.0"),
                organization_scope,
                title,
                bounded_use,
                management_question,
                {
                    "system": title,
                    "intended_use": bounded_use,
                    "scope": setup_description,
                },
                "finalized",
                "candidate",
                effective_at,
                self.clock.now(),
                ai_profile,
                dependencies,
            )
        )

    def slice_h_case_initiation_available(
        self,
        session: AuthenticatedSession,
        *,
        bounded_use: str | None = None,
        effective_at: datetime | None = None,
    ) -> bool:
        """Disclose only whether a usable pre-Case mandate exists for this Actor."""

        self._validate_session(session, "case.create_open")
        if session.actor_id is None:
            return False
        if not self.operational_store.permission_allowed(
            session.principal_id, Permission.COMMAND, "case.create_open"
        ):
            return False
        effective = effective_at or self.clock.now()
        if bounded_use is not None:
            try:
                self._case_initiation_scope(
                    actor_id=session.actor_id,
                    bounded_use=bounded_use,
                    effective_at=effective,
                )
            except AccessDenied:
                return False
            return True
        known_at = self.clock.now()
        scopes: set[str] = set()
        with self.domain_store.read_transaction() as transaction:
            for row in transaction.projection_rows(
                "case_initiation_authority_versions",
                authorized_actor_id=str(session.actor_id),
                state="ACTIVE",
            ):
                version_id = RecordVersionId.parse(str(row["version_id"]))
                version = transaction.get_version(version_id)
                if version is None:
                    continue
                selected = transaction.select_current(
                    SelectionQuery(
                        version.family,
                        version.scope,
                        effective,
                        known_at,
                        version.record_id,
                    )
                )
                if (
                    isinstance(selected, SelectionFound)
                    and selected.candidate.version_id == version_id
                ):
                    scopes.add(str(row["organization_scope"]))
        return len(scopes) == 1

    def record_case_initiation_authority(
        self,
        session: AuthenticatedSession,
        *,
        authorized_actor_id: RecordId,
        organization_scope: str,
        allowed_use_prefixes: tuple[str, ...],
        authoritative_source: str,
        source_version: str,
        effective_at: datetime,
        idempotency_key: str,
    ) -> CommandOutcome:
        """Production administrator path for an externally grounded pre-Case mandate."""

        self._validate_session(session, "case.initiation-authority.record")
        if session.actor_id is None:
            raise AccessDenied("current Actor mapping is not established")
        context = ExactContextSet.create(
            (
                ExactContextMember(
                    "authorized_actor", ContextMemberKind.RECORD, str(authorized_actor_id)
                ),
                ExactContextMember(
                    "organization_scope", ContextMemberKind.LITERAL, organization_scope
                ),
            )
        )
        return self._case_continuity.record_case_initiation_authority(
            CaseInitiationAuthorityCommand(
                ContinuityCommandIdentity(
                    CommandId.new(),
                    "operational-case-initiation-authority",
                    idempotency_key,
                    session.principal_id,
                    session.actor_id,
                ),
                RecordId.new(),
                RecordVersionId.new(),
                authorized_actor_id,
                organization_scope,
                allowed_use_prefixes,
                {
                    "authoritative_source": authoritative_source,
                    "source_version": source_version,
                    "scope": organization_scope,
                },
                CaseInitiationAuthorityState.ACTIVE,
                effective_at,
                SemanticContractRef("paim.case-continuity", "1.0"),
                context,
            )
        )

    def slice_h_establish_creator_visibility(
        self,
        session: AuthenticatedSession,
        outcome: CommandOutcome,
        *,
        effective_at: datetime,
    ) -> None:
        """Apply separately authorized software visibility to a newly created Case.

        This operation is deliberately separate from Case semantics. It runs only
        when the signed-in principal already holds both exact operational-admin
        permissions; it creates no Responsibility or substantive authority.
        """

        if not (
            self.operational_store.permission_allowed(
                session.principal_id, Permission.OPERATIONAL_ADMIN, "access.manage"
            )
            and self.operational_store.permission_allowed(
                session.principal_id,
                Permission.OPERATIONAL_ADMIN,
                "source-access.manage",
            )
        ):
            return
        case_id = RecordId.parse(outcome.record_id)
        if not self.operational_store.permission_allowed(
            session.principal_id,
            Permission.CASE_READ,
            "read",
            ScopeType.CASE,
            case_id,
        ):
            self.grant_access(
                session,
                principal_id=session.principal_id,
                grant=AccessGrantInput(
                    Permission.CASE_READ,
                    "read",
                    ScopeType.CASE,
                    case_id,
                    AccessEffect.ALLOW,
                ),
            )
        source_ids = {RecordVersionId.parse(value) for value in outcome.version_ids}
        with self.domain_store.read_transaction() as transaction:
            for basis in transaction.projection_rows("assignment_basis_versions"):
                if RecordVersionId.parse(str(basis["version_id"])) in source_ids:
                    source_ids.add(RecordVersionId.parse(str(basis["basis_source_version_id"])))
            sources = tuple(transaction.get_version(value) for value in source_ids)
        if any(source is None for source in sources):
            raise RuntimeError("new Case source manifest is unavailable")
        for source in sources:
            assert source is not None
            self.grant_source_access(
                session,
                principal_id=session.principal_id,
                grant=SourceAccessGrantInput(
                    "source.read",
                    case_id,
                    source.version_id,
                    source.family,
                    AccessEffect.ALLOW,
                    effective_at,
                ),
            )

    def slice_h_establish_result_visibility(
        self,
        session: AuthenticatedSession,
        outcome: CommandOutcome,
        *,
        case_id: RecordId,
        effective_at: datetime,
    ) -> None:
        """Apply only separately authorized source visibility to a committed result."""

        if not self.operational_store.permission_allowed(
            session.principal_id,
            Permission.OPERATIONAL_ADMIN,
            "source-access.manage",
        ):
            return
        source_ids = tuple(RecordVersionId.parse(value) for value in outcome.version_ids)
        with self.domain_store.read_transaction() as transaction:
            sources = tuple(transaction.get_version(value) for value in source_ids)
        if any(source is None for source in sources):
            raise RuntimeError("committed result source manifest is unavailable")
        for source in sources:
            assert source is not None
            self.grant_source_access(
                session,
                principal_id=session.principal_id,
                grant=SourceAccessGrantInput(
                    "source.read",
                    case_id,
                    source.version_id,
                    source.family,
                    AccessEffect.ALLOW,
                    effective_at,
                ),
            )

    def _slice_h_context(
        self,
        session: AuthenticatedSession,
        *,
        effective_at: datetime | None,
        known_at: datetime | None,
    ) -> tuple[RecordId, datetime, datetime]:
        self._validate_session(session, "practitioner.read")
        if session.actor_id is None:
            raise AccessDenied("current Actor mapping is not established")
        effective = effective_at or self.clock.now()
        known = known_at or self.clock.now()
        return session.actor_id, effective, known

    def _prospective_case_ids(self, session: AuthenticatedSession) -> tuple[RecordId, ...]:
        accessible = self.operational_store.accessible_case_ids(session.principal_id)
        with self.domain_store.read_transaction() as transaction:
            prospective = {
                RecordId.parse(str(row["case_id"]))
                for row in transaction.projection_rows("case_continuity_status_records")
            }
        return tuple(sorted(accessible.intersection(prospective), key=str))

    def _case_initiation_scope(
        self,
        *,
        actor_id: RecordId,
        bounded_use: str,
        effective_at: datetime,
    ) -> str:
        known_at = self.clock.now()
        scopes: set[str] = set()
        with self.domain_store.read_transaction() as transaction:
            rows = transaction.projection_rows(
                "case_initiation_authority_versions",
                authorized_actor_id=str(actor_id),
                state="ACTIVE",
            )
            for row in rows:
                version_id = RecordVersionId.parse(str(row["version_id"]))
                version = transaction.get_version(version_id)
                if version is None:
                    continue
                selected = transaction.select_current(
                    SelectionQuery(
                        version.family,
                        version.scope,
                        effective_at,
                        known_at,
                        version.record_id,
                    )
                )
                prefixes = json.loads(cast(str, row["allowed_use_prefixes_json"]))
                if (
                    isinstance(selected, SelectionFound)
                    and selected.candidate.version_id == version_id
                    and isinstance(prefixes, list)
                    and all(isinstance(value, str) for value in prefixes)
                    and (not prefixes or any(bounded_use.startswith(value) for value in prefixes))
                ):
                    scopes.add(str(row["organization_scope"]))
        if len(scopes) != 1:
            raise AccessDenied("one exact Case-initiation mandate is not established")
        return scopes.pop()

    def practitioner_home(self, session: AuthenticatedSession) -> HomeView:
        actor, cases, effective_at, known_at = self._practitioner_context(session)
        health = self.health()
        return self._practitioner_queries.home(
            actor=actor,
            cases=cases,
            health_state=health.state.value,
            health_reasons=health.reasons,
            effective_at=effective_at,
            known_at=known_at,
        )

    def practitioner_cases(
        self, session: AuthenticatedSession, *, search_text: str = ""
    ) -> CaseListView:
        actor, cases, effective_at, known_at = self._practitioner_context(session)
        return self._practitioner_queries.case_list(
            actor=actor,
            cases=cases,
            search_text=search_text,
            effective_at=effective_at,
            known_at=known_at,
        )

    def practitioner_case(
        self, session: AuthenticatedSession, case_id: RecordId
    ) -> CaseOrientationView | None:
        actor, cases, effective_at, known_at = self._practitioner_context(session)
        return self._practitioner_queries.orientation(
            actor=actor,
            cases=cases,
            case_id=case_id,
            effective_at=effective_at,
            known_at=known_at,
        )

    def practitioner_workspace(
        self, session: AuthenticatedSession, case_id: RecordId
    ) -> CaseWorkspaceView | None:
        actor, cases, effective_at, known_at = self._practitioner_context(session)
        if not any(item.case_id == str(case_id) for item in cases):
            return None
        visible_configurations = self.operational_store.accessible_configuration_ids(
            session.principal_id, frozenset({case_id})
        )
        governing = self._service.select_governing_configuration(
            case_id=case_id,
            effective_at=effective_at,
            known_at=known_at,
        )
        actions = (
            "configuration.create",
            "configuration.designate",
            "evidence.create",
            "authority.create",
            "authority-gap.create",
            "evidence.applicability",
            "value-input.create",
            "risk-input.create",
            "value-input.ready",
            "risk-input.ready",
            "value-fitness.create",
            "risk-fitness.create",
            "value-input.select",
            "risk-input.select",
            "case.lifecycle.advance",
            "integration.create",
            "boundary.create",
            "decision.propose",
            "decision.authorize",
        )
        access = {
            action: self.operational_store.permission_allowed(
                session.principal_id,
                Permission.COMMAND,
                action,
                ScopeType.CASE,
                case_id,
            )
            for action in actions
        }
        return self._practitioner_queries.workspace(
            actor=actor,
            cases=cases,
            case_id=case_id,
            visible_configuration_ids=visible_configurations,
            governing=governing,
            lifecycle_state=self._service.current_lifecycle_state(
                case_id=case_id, effective_at=effective_at
            ).value,
            action_access=access,
            effective_at=effective_at,
            known_at=known_at,
        )

    def resolve_judgment_accountability(
        self,
        session: AuthenticatedSession,
        *,
        case_id: RecordId,
        configuration_id: RecordId,
        eligible_functions: tuple[str, ...],
        effective_at: datetime,
    ) -> AccountabilityCheck:
        """Resolve exact current Role Assignment accountability for one browser judgment.

        The caller supplies a closed, action-specific function set. Resolution uses the
        production Role Assignment selector for the exact Configuration and its owning Case.
        Results across functions are combined without specificity, recency, role, actor, or
        display-order precedence.
        """
        self._validate_session(session, "judgment.accountability.resolve")
        self._require(session, Permission.CASE_READ, "read", ScopeType.CASE, case_id)
        owning_case = self.operational_store.configuration_case(configuration_id)
        if owning_case != case_id:
            self._deny(
                session,
                "judgment.accountability.resolve",
                "CONFIGURATION_SCOPE_NOT_ESTABLISHED",
                case_id,
            )
        self._require(
            session,
            Permission.CONFIGURATION_READ,
            "read",
            ScopeType.CONFIGURATION,
            configuration_id,
        )
        known_at = self.clock.now()
        assignment_ids: set[RecordVersionId] = set()
        conflict = False
        for function in eligible_functions:
            result = self._service.resolve_accountability(
                role=function,
                target_type=RoleTargetType.CONFIGURATION,
                target_id=str(configuration_id),
                effective_at=effective_at,
                known_at=known_at,
            )
            if isinstance(result, AccountabilityFound):
                if result.assignment_version_id is not None:
                    assignment_ids.add(result.assignment_version_id)
            elif isinstance(result, AccountabilityConflict):
                conflict = True
                assignment_ids.update(result.assignment_version_ids)

        assignments: list[AccountableAssignmentView] = []
        for version_id in sorted(assignment_ids, key=str):
            version = self.domain_store.get_version(version_id)
            actor_value = version.content.get("paim_actor_id") if version is not None else None
            function_value = version.content.get("role") if version is not None else None
            if not isinstance(actor_value, str) or not isinstance(function_value, str):
                raise RuntimeError("accountable Role Assignment detail is unavailable")
            actor = self._practitioner_queries.actor_context(
                principal_id=session.principal_id,
                actor_id=RecordId.parse(actor_value),
                effective_at=effective_at,
                known_at=known_at,
            )
            assignments.append(
                AccountableAssignmentView(str(version_id), actor.display_name, function_value)
            )
        if conflict or len(assignments) > 1:
            state = "CONFLICT"
        elif assignments:
            state = "ESTABLISHED"
        else:
            state = "NOT_ESTABLISHED"
        return AccountabilityCheck(state, tuple(assignments))

    def _practitioner_context(
        self, session: AuthenticatedSession
    ) -> tuple[ActorContext, tuple[CaseSummary, ...], datetime, datetime]:
        self._validate_session(session, "practitioner.read")
        if session.actor_id is None:
            raise AccessDenied("current Actor mapping is not established")
        now = self.clock.now()
        visible_cases = self.operational_store.accessible_case_ids(session.principal_id)
        visible_configurations = self.operational_store.accessible_configuration_ids(
            session.principal_id, visible_cases
        )
        configuration_counts = {case_id: 0 for case_id in visible_cases}
        for configuration_id in visible_configurations:
            owning_case_id = self.operational_store.configuration_case(configuration_id)
            if owning_case_id in visible_cases:
                configuration_counts[owning_case_id] += 1
        actor = self._practitioner_queries.actor_context(
            principal_id=session.principal_id,
            actor_id=session.actor_id,
            effective_at=now,
            known_at=now,
        )
        cases = self._practitioner_queries.cases(
            visible_case_ids=visible_cases,
            visible_configuration_counts=configuration_counts,
            effective_at=now,
            known_at=now,
        )
        return actor, cases, now, now

    def run_command(
        self,
        session: AuthenticatedSession,
        *,
        action: str,
        idempotency_key: str,
        operation: Callable[[Increment7ApplicationService, CommandMeta], T],
        case_id: RecordId | None = None,
        configuration_id: RecordId | None = None,
        claimed_actor_id: RecordId | None = None,
        causation_id: str | None = None,
    ) -> T:
        """Invoke an existing typed domain command after software access checks.

        The operation receives the established Increment 7 service and an exact
        ``CommandMeta``. Domain authority and all semantic guards remain inside
        that existing service.
        """
        unresolved_actor_allowed = action == "actor.create"
        if session.actor_id is None and not unresolved_actor_allowed:
            self._deny(session, action, "PAIM_ACTOR_MAPPING_NOT_ESTABLISHED", case_id)
        if action in _ACTOR_BOUND_ACTIONS and claimed_actor_id is None:
            self._deny(session, action, "SUBSTANTIVE_ACTOR_CLAIM_REQUIRED", case_id)
        if claimed_actor_id is not None and claimed_actor_id != session.actor_id:
            self._deny(session, action, "SUBSTANTIVE_ACTOR_CLAIM_MISMATCH", case_id)
        self._require(
            session,
            Permission.COMMAND,
            action,
            ScopeType.CASE if case_id else ScopeType.GLOBAL,
            case_id,
        )
        if case_id is not None:
            self._require(session, Permission.CASE_READ, "read", ScopeType.CASE, case_id)
        if configuration_id is not None:
            owning_case = self.operational_store.configuration_case(configuration_id)
            if owning_case is None or (case_id is not None and owning_case != case_id):
                self._deny(session, action, "CONFIGURATION_SCOPE_NOT_ESTABLISHED", case_id)
            self._require(
                session,
                Permission.CONFIGURATION_READ,
                "read",
                ScopeType.CONFIGURATION,
                configuration_id,
            )
        meta = CommandMeta(
            command_id=CommandId.new(),
            idempotency_scope=f"operational:{action}",
            idempotency_key=idempotency_key,
            principal_id=session.principal_id,
            actor_id=str(session.actor_id) if session.actor_id else None,
            actor_resolution=(
                ActorResolution.PROVIDED
                if session.actor_id is not None
                else ActorResolution.UNRESOLVED
            ),
            correlation_id=session.correlation_id,
            causation_id=causation_id,
        )
        self._audit_session(
            session,
            category="ACCESS",
            outcome="ALLOWED",
            action=action,
            reason="SOFTWARE_ACCESS_ESTABLISHED",
            details={"command_id": str(meta.command_id)},
            case_id=case_id,
            configuration_id=configuration_id,
            causation_id=causation_id,
        )
        try:
            result = operation(self._service, meta)
        except (
            DomainRuleViolation,
            DomainPreconditionFailed,
            StalePrecondition,
            WriterContention,
            SQLAlchemyError,
        ) as error:
            self._audit_session(
                session,
                category="COMMAND",
                outcome="FAILURE",
                action=action,
                reason=type(error).__name__.upper(),
                details={"command_id": str(meta.command_id), "blocked": True},
                case_id=case_id,
                configuration_id=configuration_id,
                causation_id=causation_id,
            )
            raise
        self._audit_session(
            session,
            category="COMMAND",
            outcome="SUCCESS",
            action=action,
            reason="EXISTING_DOMAIN_COMMAND_COMMITTED",
            details={"command_id": str(meta.command_id)},
            case_id=case_id,
            configuration_id=configuration_id,
            causation_id=causation_id,
        )
        return result

    def intake(self, session: AuthenticatedSession, envelope: IntakeEnvelope) -> IntakeResult:
        self._require(session, Permission.COMMAND, f"intake.{envelope.adapter_type.value.lower()}")
        if envelope.target_case_id is not None:
            self._require(
                session,
                Permission.CASE_READ,
                "read",
                ScopeType.CASE,
                envelope.target_case_id,
            )
        if envelope.target_configuration_id is not None:
            self._require(
                session,
                Permission.CONFIGURATION_READ,
                "read",
                ScopeType.CONFIGURATION,
                envelope.target_configuration_id,
            )
        payload_json = json.dumps(
            envelope.payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )
        payload_bytes = payload_json.encode("utf-8")
        checksum = hashlib.sha256(payload_bytes).hexdigest()
        now = self.clock.now()
        reason = self._intake_quarantine_reason(envelope, len(payload_bytes))
        prior_replays = self.operational_store.intake_replays(
            envelope.adapter_type, envelope.source_system, envelope.replay_id
        )
        for prior in prior_replays:
            if prior["payload_checksum"] == checksum:
                result = IntakeResult(
                    cast("str", prior["intake_id"]),
                    IntakeStatus(cast("str", prior["status"])),
                    checksum,
                    True,
                    cast("str | None", prior["quarantine_reason"]),
                    cast("str | None", prior["supersedes_intake_id"]),
                )
                self._adapter_audit(session, envelope, "REPLAYED", "EXACT_REPLAY", result)
                return result
        if prior_replays:
            reason = "REPLAY_ID_PAYLOAD_MISMATCH"
        latest = self.operational_store.latest_source_intake(
            envelope.adapter_type, envelope.source_system, envelope.source_object_id
        )
        if (
            reason is None
            and latest is not None
            and latest["source_version"] == envelope.source_version
            and latest["payload_checksum"] != checksum
        ):
            reason = "SOURCE_VERSION_PAYLOAD_MISMATCH"
        status = IntakeStatus.QUARANTINED if reason else IntakeStatus.PROPOSED
        intake_id = str(RecordId.new())
        supersedes = (
            cast("str", latest["intake_id"])
            if latest is not None and latest["source_version"] != envelope.source_version
            else None
        )
        self.operational_store.add_intake(
            {
                "intake_id": intake_id,
                "adapter_type": envelope.adapter_type.value,
                "source_system": envelope.source_system,
                "source_object_id": envelope.source_object_id,
                "source_version": envelope.source_version,
                "source_effective_at_us": to_epoch_microseconds(envelope.source_effective_at),
                "ingested_at_us": to_epoch_microseconds(now),
                "payload_checksum": checksum,
                "target_case_id": str(envelope.target_case_id) if envelope.target_case_id else None,
                "target_configuration_id": (
                    str(envelope.target_configuration_id)
                    if envelope.target_configuration_id
                    else None
                ),
                "management_context": envelope.management_context,
                "replay_id": envelope.replay_id,
                "mapper_rule_id": envelope.mapper_rule_id,
                "mapper_rule_version": envelope.mapper_rule_version,
                "payload_reference": envelope.payload_reference,
                "payload_json": payload_json,
                "unmapped_material_json": json.dumps(
                    envelope.unmapped_material or {}, sort_keys=True, separators=(",", ":")
                ),
                "status": status.value,
                "quarantine_reason": reason,
                "supersedes_intake_id": supersedes,
            }
        )
        result = IntakeResult(intake_id, status, checksum, False, reason, supersedes)
        self._adapter_audit(
            session,
            envelope,
            "QUARANTINED" if reason else "ACCEPTED",
            reason or "NON_AUTHORITATIVE_PROPOSAL_RETAINED",
            result,
        )
        return result

    def promote_intake(
        self,
        session: AuthenticatedSession,
        *,
        intake_id: str,
        action: str,
        idempotency_key: str,
        operation: Callable[[Increment7ApplicationService, CommandMeta], T],
    ) -> T:
        row = self.operational_store.intake(intake_id)
        if row is None or row["status"] != IntakeStatus.PROPOSED.value:
            raise DomainRuleViolation("intake is not an eligible proposed source")
        case_text = cast("str | None", row["target_case_id"])
        configuration_text = cast("str | None", row["target_configuration_id"])
        return self.run_command(
            session,
            action=action,
            idempotency_key=idempotency_key,
            operation=operation,
            case_id=RecordId.parse(case_text) if case_text else None,
            configuration_id=(RecordId.parse(configuration_text) if configuration_text else None),
            causation_id=intake_id,
        )

    def derive_register(
        self,
        session: AuthenticatedSession,
        *,
        requested_case_ids: frozenset[RecordId],
        requested_configuration_ids: frozenset[RecordId],
        effective_at: datetime,
        known_at: datetime,
        rule_id: str,
        rule_version: str,
        lifecycle_filter: frozenset[RegisterLifecycle] = frozenset(),
        order_by: tuple[str, ...] = ("stable_identity",),
        processed_watermark: datetime | None = None,
    ) -> RegisterView:
        self._validate_session(session, "register.derive")
        accessible_cases = self.operational_store.accessible_case_ids(session.principal_id)
        population_cases = requested_case_ids or self.operational_store.all_case_ids()
        visible_cases = population_cases & accessible_cases
        population_configurations = (
            requested_configuration_ids or self.operational_store.all_configuration_ids()
        )
        accessible_configurations = self.operational_store.accessible_configuration_ids(
            session.principal_id, visible_cases
        )
        # The current Register contract has a Case-level visibility seam. Fail
        # closed at that seam when a visible Case contains any requested
        # Configuration not granted to the principal; this avoids leaking a
        # same-Case hidden Configuration through entries or group counts.
        visible_cases = frozenset(
            case_id
            for case_id in visible_cases
            if all(
                configuration_id in accessible_configurations
                for configuration_id in population_configurations
                if self.operational_store.configuration_case(configuration_id) == case_id
            )
        )
        query = RegisterQuery(
            case_ids=population_cases,
            configuration_ids=population_configurations,
            effective_at=effective_at,
            known_at=known_at,
            rule_id=rule_id,
            rule_version=rule_version,
            access_context=self._access_context(session),
            accessible_case_ids=visible_cases,
            lifecycle_filter=lifecycle_filter,
            order_by=order_by,
            processed_watermark=processed_watermark,
        )
        view = self._service.derive_management_register(query)
        view = replace(
            view,
            filters=(
                "case_ids:ACCESS_SCOPED",
                "configuration_ids:ACCESS_SCOPED",
                "lifecycle:" + ",".join(sorted(item.value for item in lifecycle_filter)),
                f"access_context:{self._access_context(session)}",
            ),
        )
        self._register_queries[self._view_key(view)] = query
        self._audit_session(
            session,
            category="PROJECTION",
            outcome="SUCCESS" if view.consistency is ProjectionConsistency.CURRENT else "DEGRADED",
            action="register.derive",
            reason=f"REGISTER_{view.consistency.value}",
            details={
                "visible_entry_count": len(view.entries),
                "visible_group_count": len(view.groups),
                "access_filtered": any(group.access_filtered for group in view.groups),
            },
        )
        return view

    def persist_register_output(
        self, session: AuthenticatedSession, view: RegisterView, *, output_kind: str
    ) -> RegisterManifest:
        if view.access_context != self._access_context(session):
            raise AccessDenied(
                "Register view access context does not match authenticated principal"
            )
        self._require(session, Permission.EXPORT, "register.output")
        query = self._register_queries.get(self._view_key(view))
        if query is None:
            raise DomainRuleViolation("Register output requires trusted operational query basis")
        manifest = self._service.persist_register_output(view, output_kind=output_kind)
        query_json = self._query_json(query)
        self.operational_store.add_register_rebuild_basis(
            manifest_id=manifest.manifest_id,
            query_json=query_json,
            query_checksum=hashlib.sha256(query_json.encode("utf-8")).hexdigest(),
            recorded_at=self.clock.now(),
        )
        return manifest

    def launch_register_action(
        self,
        session: AuthenticatedSession,
        view: RegisterView,
        action: RegisterAction,
        entry: RegisterConcernEntry,
    ) -> RegisterActionLaunch:
        if view.access_context != self._access_context(session):
            raise AccessDenied(
                "Register view access context does not match authenticated principal"
            )
        if view.consistency is not ProjectionConsistency.CURRENT:
            raise DomainRuleViolation("stale or inconsistent Register cannot authorize action")
        self._require(session, Permission.COMMAND, f"register.{action.value.lower()}")
        return self._service.launch_action(
            action,
            entry,
            launch_context=f"{self._access_context(session)}|correlation:{session.correlation_id}",
        )

    def export_manifest(
        self, session: AuthenticatedSession, manifest_id: str, *, output_format: str
    ) -> Path:
        self._require(session, Permission.EXPORT, "register.export")
        manifest = self._service.get_register_manifest(manifest_id)
        if manifest is None:
            raise DomainRuleViolation("Register manifest is not established")
        content = cast("dict[str, JsonValue]", json.loads(manifest.content_json))
        self._validate_manifest_access(session, content)
        if hashlib.sha256(manifest.content_json.encode("utf-8")).hexdigest() != manifest.checksum:
            raise DomainRuleViolation("Register manifest checksum is inconsistent")
        if output_format not in {"json", "csv"}:
            raise ValueError("export format must be json or csv")
        target = self.config.export_directory / f"{manifest_id}.{output_format}"
        if output_format == "json":
            wrapper = {
                "manifest_id": manifest.manifest_id,
                "manifest_checksum": manifest.checksum,
                "access_context": content["access_context"],
                "effective_at": content["effective_at"],
                "known_at": content["known_at"],
                "rule_id": content["rule_id"],
                "rule_version": content["rule_version"],
                "source_high_water": content["source_high_water"],
                "processed_watermark": content["processed_watermark"],
                "consistency": content["consistency"],
                "content": content,
            }
            target.write_text(
                json.dumps(wrapper, sort_keys=True, separators=(",", ":")), encoding="utf-8"
            )
        else:
            self._write_csv_export(target, manifest, content)
        self._audit_session(
            session,
            category="EXPORT",
            outcome="SUCCESS",
            action="register.export",
            reason="EXACT_MANIFEST_EXPORTED",
            details={
                "manifest_id": manifest_id,
                "manifest_checksum": manifest.checksum,
                "format": output_format,
            },
        )
        return target

    def deliver_notification(
        self,
        session: AuthenticatedSession,
        *,
        intent_id: str,
        attempt_id: str,
        simulate_failure: bool = False,
    ) -> DeliveryResult:
        self._require(session, Permission.DELIVERY, "notification.deliver")
        existing = self.operational_store.delivery_attempt(attempt_id)
        if existing:
            last = existing[-1]
            if last["intent_id"] != intent_id:
                raise DomainRuleViolation("delivery attempt identity was reused for another intent")
            return DeliveryResult(
                intent_id,
                attempt_id,
                DeliveryStatus(cast("str", last["status"])),
                cast("str | None", last["spool_reference"]),
                True,
            )
        delivered = self.operational_store.delivered_intent(intent_id)
        if delivered is not None:
            return DeliveryResult(
                intent_id,
                cast("str", delivered["attempt_id"]),
                DeliveryStatus.DELIVERED,
                cast("str | None", delivered["spool_reference"]),
                True,
            )
        intent = self.operational_store.notification_intent(intent_id)
        if intent is None:
            raise DomainRuleViolation("notification intent is not established")
        manifest = self._service.get_register_manifest(cast("str", intent["manifest_id"]))
        if manifest is None:
            raise DomainRuleViolation("notification manifest is not established")
        content = cast("dict[str, JsonValue]", json.loads(manifest.content_json))
        self._validate_manifest_access(session, content)
        now = self.clock.now()
        self.operational_store.add_delivery_event(
            event_id=str(RecordId.new()),
            intent_id=intent_id,
            attempt_id=attempt_id,
            status=DeliveryStatus.PENDING.value,
            recorded_at=now,
        )
        spool_name = hashlib.sha256(f"{intent_id}|{attempt_id}".encode()).hexdigest() + ".json"
        target = self.config.spool_directory / spool_name
        try:
            if simulate_failure:
                raise OSError("simulated local delivery failure")
            body = json.dumps(
                {
                    "intent_id": intent_id,
                    "manifest_id": manifest.manifest_id,
                    "manifest_checksum": manifest.checksum,
                    "concern_key": intent["concern_key"],
                    "concern_lifecycle": intent["concern_lifecycle"],
                    "channel": intent["channel"],
                    "recipient_scope": intent["recipient_scope"],
                },
                sort_keys=True,
                separators=(",", ":"),
            )
            if target.exists() and target.read_text(encoding="utf-8") != body:
                raise OSError("delivery spool identity conflict")
            if not target.exists():
                target.write_text(body, encoding="utf-8")
        except OSError:
            self.operational_store.add_delivery_event(
                event_id=str(RecordId.new()),
                intent_id=intent_id,
                attempt_id=attempt_id,
                status=DeliveryStatus.FAILED.value,
                recorded_at=self.clock.now(),
                reason="LOCAL_SPOOL_WRITE_FAILED",
            )
            self._audit_session(
                session,
                category="DELIVERY",
                outcome="FAILURE",
                action="notification.deliver",
                reason="LOCAL_SPOOL_WRITE_FAILED",
                details={"intent_id": intent_id, "attempt_id": attempt_id},
            )
            return DeliveryResult(intent_id, attempt_id, DeliveryStatus.FAILED, None, False)
        self.operational_store.add_delivery_event(
            event_id=str(RecordId.new()),
            intent_id=intent_id,
            attempt_id=attempt_id,
            status=DeliveryStatus.DELIVERED.value,
            recorded_at=self.clock.now(),
            spool_reference=target.name,
        )
        self._audit_session(
            session,
            category="DELIVERY",
            outcome="DELIVERED",
            action="notification.deliver",
            reason="LOCAL_SPOOL_DELIVERY_COMPLETE",
            details={"intent_id": intent_id, "attempt_id": attempt_id},
        )
        return DeliveryResult(intent_id, attempt_id, DeliveryStatus.DELIVERED, target.name, False)

    def backup(
        self, session: AuthenticatedSession, *, label: str
    ) -> tuple[Path, Path, BackupManifest]:
        self._require(session, Permission.OPERATIONAL_ADMIN, "backup.create")
        return create_backup(self, session, label=label)

    def restore(
        self,
        session: AuthenticatedSession,
        *,
        backup_path: Path,
        manifest_path: Path,
        target_path: Path,
    ) -> BackupManifest:
        self._require(session, Permission.OPERATIONAL_ADMIN, "restore.verify")
        return restore_backup(
            self,
            session,
            backup_path=backup_path,
            manifest_path=manifest_path,
            target_path=target_path,
        )

    def health(self) -> HealthReport:
        return health_report(self)

    def counters(self, session: AuthenticatedSession) -> dict[str, int]:
        self._require(session, Permission.OPERATIONAL_ADMIN, "observability.read")
        return self.operational_store.operational_counts()

    def require_supported(self, capability: str) -> None:
        normalized = capability.strip().upper()
        if normalized in UNSUPPORTED_CAPABILITIES:
            raise UnsupportedCapability(f"{normalized} is explicitly unsupported in PAIM v0.1")

    def _intake_quarantine_reason(self, envelope: IntakeEnvelope, payload_size: int) -> str | None:
        if not all(
            item.strip()
            for item in (
                envelope.source_system,
                envelope.source_object_id,
                envelope.replay_id,
                envelope.mapper_rule_id,
                envelope.mapper_rule_version,
            )
        ):
            return "REQUIRED_PROVENANCE_NOT_ESTABLISHED"
        if payload_size > _MAX_INTAKE_BYTES:
            return "BOUNDED_PAYLOAD_LIMIT_EXCEEDED"
        if envelope.adapter_type is AdapterType.EXTERNAL_TRIGGER:
            if envelope.target_case_id is None or not (envelope.management_context or "").strip():
                return "EXACT_TRIGGER_CASE_AND_MANAGEMENT_CONTEXT_REQUIRED"
        elif envelope.target_case_id is None or envelope.target_configuration_id is None:
            return "EXACT_CASE_AND_CONFIGURATION_TARGET_REQUIRED"
        if envelope.target_configuration_id is not None:
            owner = self.operational_store.configuration_case(envelope.target_configuration_id)
            if owner is None or owner != envelope.target_case_id:
                return "TARGET_CONFIGURATION_CONTEXT_MISMATCH"
        return None

    def _adapter_audit(
        self,
        session: AuthenticatedSession,
        envelope: IntakeEnvelope,
        outcome: str,
        reason: str,
        result: IntakeResult,
    ) -> None:
        self._audit_session(
            session,
            category="ADAPTER",
            outcome=outcome,
            action=f"intake.{envelope.adapter_type.value.lower()}",
            reason=reason,
            details={
                "intake_id": result.intake_id,
                "adapter_type": envelope.adapter_type.value,
                "source_system": envelope.source_system,
                "source_object_id": envelope.source_object_id,
                "source_version": envelope.source_version,
                "checksum": result.payload_checksum,
                "replayed": result.replayed,
            },
            case_id=envelope.target_case_id,
            configuration_id=envelope.target_configuration_id,
        )

    def _require(
        self,
        session: AuthenticatedSession,
        permission: Permission,
        action: str,
        scope_type: ScopeType = ScopeType.GLOBAL,
        scope_id: RecordId | None = None,
    ) -> None:
        self._validate_session(session, action, scope_id)
        if not self.operational_store.permission_allowed(
            session.principal_id, permission, action, scope_type, scope_id
        ):
            self._deny(session, action, f"{permission.value}_NOT_ESTABLISHED", scope_id)

    def _validate_session(
        self,
        session: AuthenticatedSession,
        action: str,
        scope_id: RecordId | None = None,
    ) -> None:
        """Require the session's principal status and actor resolution to remain current."""
        current = self.operational_store.current_principal(session.principal_id)
        if current is None or current.status is not PrincipalStatus.ENABLED:
            self._deny(session, action, "AUTHENTICATION_STATE_UNAVAILABLE", scope_id)
        bootstrap_actor_creation = (
            action == "actor.create" and session.actor_id is None and current.actor_id is None
        )
        if current.actor_id != session.actor_id and not bootstrap_actor_creation:
            self._deny(session, action, "PRINCIPAL_ACTOR_MAPPING_NOT_CURRENT", scope_id)

    def _deny(
        self,
        session: AuthenticatedSession,
        action: str,
        reason: str,
        case_id: RecordId | None,
    ) -> NoReturn:
        self._audit_session(
            session,
            category="ACCESS",
            outcome="DENIED",
            action=action,
            reason=reason,
            details={"allowed": False},
            case_id=case_id,
        )
        raise AccessDenied("software access not established")

    @staticmethod
    def _access_context(session: AuthenticatedSession) -> str:
        return f"principal:{session.principal_id}"

    @staticmethod
    def _view_key(view: RegisterView) -> str:
        content = Increment7ApplicationService._view_content(view)
        represented = json.dumps(content, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(represented.encode("utf-8")).hexdigest()

    @staticmethod
    def _query_json(query: RegisterQuery) -> str:
        value = {
            "case_ids": sorted(str(item) for item in query.case_ids),
            "configuration_ids": sorted(str(item) for item in query.configuration_ids),
            "effective_at": query.effective_at.isoformat(),
            "known_at": query.known_at.isoformat() if query.known_at else None,
            "rule_id": query.rule_id,
            "rule_version": query.rule_version,
            "access_context": query.access_context,
            "accessible_case_ids": sorted(str(item) for item in query.accessible_case_ids),
            "lifecycle_filter": sorted(item.value for item in query.lifecycle_filter),
            "order_by": list(query.order_by),
            "processed_watermark": (
                query.processed_watermark.isoformat() if query.processed_watermark else None
            ),
        }
        return json.dumps(value, sort_keys=True, separators=(",", ":"))

    def _validate_manifest_access(
        self, session: AuthenticatedSession, content: Mapping[str, JsonValue]
    ) -> None:
        if content.get("access_context") != self._access_context(session):
            raise AccessDenied("manifest access context does not match authenticated principal")
        accessible = {
            str(item) for item in self.operational_store.accessible_case_ids(session.principal_id)
        }
        visible: set[str] = set()
        entries = content.get("entries", [])
        if isinstance(entries, list):
            for item in entries:
                if isinstance(item, dict) and isinstance(item.get("key"), str):
                    key = cast("str", item["key"])
                    first = key.split("|", 1)[0]
                    if first.startswith("case:"):
                        visible.add(first.removeprefix("case:"))
        if not visible <= accessible:
            raise AccessDenied("manifest includes inaccessible Case scope")

    @staticmethod
    def _write_csv_export(
        target: Path, manifest: RegisterManifest, content: Mapping[str, JsonValue]
    ) -> None:
        fields = (
            "row_type",
            "manifest_id",
            "manifest_checksum",
            "access_context",
            "effective_at",
            "known_at",
            "rule_version",
            "source_high_water",
            "processed_watermark",
            "consistency",
            "identity",
            "lifecycle",
            "basis_json",
            "access_filtered",
        )
        with target.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            common = {
                "manifest_id": manifest.manifest_id,
                "manifest_checksum": manifest.checksum,
                "access_context": content["access_context"],
                "effective_at": content["effective_at"],
                "known_at": content["known_at"],
                "rule_version": content["rule_version"],
                "source_high_water": content["source_high_water"],
                "processed_watermark": content["processed_watermark"],
                "consistency": content["consistency"],
            }
            entries = content.get("entries", [])
            if isinstance(entries, list):
                for item in entries:
                    if not isinstance(item, dict):
                        continue
                    writer.writerow(
                        {
                            **common,
                            "row_type": "ENTRY",
                            "identity": item.get("key"),
                            "lifecycle": item.get("lifecycle"),
                            "basis_json": json.dumps(item, sort_keys=True, separators=(",", ":")),
                            "access_filtered": "",
                        }
                    )
            groups = content.get("groups", [])
            if isinstance(groups, list):
                for item in groups:
                    if not isinstance(item, dict):
                        continue
                    writer.writerow(
                        {
                            **common,
                            "row_type": "GROUP",
                            "identity": item.get("dependency_record_id"),
                            "lifecycle": "",
                            "basis_json": json.dumps(item, sort_keys=True, separators=(",", ":")),
                            "access_filtered": item.get("access_filtered"),
                        }
                    )

    def _audit_session(
        self,
        session: AuthenticatedSession,
        *,
        category: str,
        outcome: str,
        action: str,
        reason: str,
        details: Mapping[str, JsonValue],
        case_id: RecordId | None = None,
        configuration_id: RecordId | None = None,
        causation_id: str | None = None,
    ) -> str:
        return self._audit(
            category=category,
            outcome=outcome,
            principal_id=session.principal_id,
            actor_id=session.actor_id,
            action=action,
            reason=reason,
            details=details,
            case_id=case_id,
            configuration_id=configuration_id,
            correlation_id=session.correlation_id,
            causation_id=causation_id,
        )

    def _audit(
        self,
        *,
        category: str,
        outcome: str,
        principal_id: str | None,
        actor_id: RecordId | None,
        action: str,
        reason: str,
        details: Mapping[str, JsonValue],
        case_id: RecordId | None = None,
        configuration_id: RecordId | None = None,
        correlation_id: str | None = None,
        causation_id: str | None = None,
    ) -> str:
        return self.operational_store.audit(
            event_id=str(RecordId.new()),
            category=category,
            outcome=outcome,
            principal_id=principal_id,
            actor_id=actor_id,
            action=action,
            recorded_at=self.clock.now(),
            reason_category=reason,
            details=details,
            case_id=case_id,
            configuration_id=configuration_id,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )
