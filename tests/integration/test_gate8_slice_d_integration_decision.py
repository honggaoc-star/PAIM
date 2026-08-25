from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import timedelta

import pytest
from alembic import command as alembic_command

from paim.application import Increment3ApplicationService
from paim.assessment_review import AssessmentLane
from paim.audit import ActorResolution
from paim.case_continuity import CaseContinuityService
from paim.domain import AuthorityVersionInput, CommandMeta
from paim.integrity import CommandId, EffectiveInterval, FixedClock, RecordId, RecordVersionId
from paim.integrity.semantics import SemanticContractRef
from paim.practitioner_queries import PractitionerQueryService
from paim.prospective_decision import (
    AuthorizationFacts,
    AuthorizeDecisionCommand,
    ConfirmationFacts,
    ConfirmDecisionCommand,
    DecisionFacts,
    IntegrateValueRiskCommand,
    IntegrationFacts,
    ProposeDecisionCommand,
    ProspectiveDecisionConflict,
    ProspectiveDecisionService,
    ProspectiveDecisionStatus,
    ProspectiveSelectionKind,
    ReliedLaneBasis,
)
from paim.responsibility.models import ObligationKind
from tests.integration.test_gate8_slice_b_case_continuity import NOW, RECORDED
from tests.integration.test_gate8_slice_c_assessment_review import (
    ASSESSED_SCOPE,
    DECISION_USE,
    KNOWLEDGE,
    Fixture,
    ResponsibilityBasis,
    SelectiveSourceAccess,
    adequacy_command,
    establish_responsibility,
    finish_command,
    fixture,
    identity,
    reliance_command,
)
from tests.integration.test_migration_and_schema import alembic_config

CONTRACT = SemanticContractRef("paim.prospective-integration-decision", "1.0")


@dataclass(frozen=True)
class SliceDFixture:
    source: Fixture
    service: ProspectiveDecisionService
    value: ReliedLaneBasis
    risk: ReliedLaneBasis
    responsibilities: dict[ObligationKind, ResponsibilityBasis]
    integration_authority: RecordVersionId
    decision_authority: RecordVersionId


def substantive_authority(
    store: object,
    fx: Fixture,
    *,
    actor_id: RecordId,
    actions: tuple[str, ...],
    key: str,
) -> RecordVersionId:
    record_id, version_id = RecordId.new(), RecordVersionId.new()
    Increment3ApplicationService(
        store,  # type: ignore[arg-type]
        FixedClock(RECORDED + timedelta(seconds=3)),
    ).commit_authority_record(
        CommandMeta(
            CommandId.new(),
            "gate8-slice-d",
            key,
            "principal:slice-c",
            str(actor_id),
            ActorResolution.PROVIDED,
        ),
        AuthorityVersionInput(
            record_id,
            version_id,
            fx.opened.facts.case_id,  # type: ignore[attr-defined]
            fx.opened.facts.configuration_id,  # type: ignore[attr-defined]
            fx.opened.facts.configuration_version_id,  # type: ignore[attr-defined]
            "prospective-substantive-authority",
            "bounded-governance-charter",
            {"source": "fresh Slice-D vertical proof"},
            ASSESSED_SCOPE,
            "exact separately established substantive authority",
            {
                "prospective_substantive_authority": {
                    "actor_id": str(actor_id),
                    "allowed_actions": list(actions),
                    "allowed_case_ids": [str(fx.opened.facts.case_id)],  # type: ignore[attr-defined]
                    "context_digest": fx.opened.context.digest,  # type: ignore[attr-defined]
                    "allowed_decision_uses": [DECISION_USE],
                    "allowed_scopes": [ASSESSED_SCOPE],
                }
            },
            EffectiveInterval(NOW),
        ),
    )
    return version_id


def slice_d_fixture(store: object, key: str = "vertical") -> SliceDFixture:
    fx = fixture(store, key)
    relied: dict[AssessmentLane, ReliedLaneBasis] = {}
    for lane, actor in ((AssessmentLane.VALUE, fx.actor_a), (AssessmentLane.RISK, fx.actor_b)):
        finish = finish_command(fx, lane, f"{key}-{lane.value}-finish")
        adequacy = adequacy_command(fx, finish, f"{key}-{lane.value}-adequacy")
        reliance = reliance_command(
            fx,
            finish,
            adequacy,
            f"{key}-{lane.value}-reliance",
            actor,
        )
        fx.service.finish_assessment(finish)
        fx.service.determine_adequacy(adequacy)
        fx.service.designate_reliance(reliance)
        relied[lane] = ReliedLaneBasis(
            lane,
            finish.facts.assessment_version_id,
            finish.facts.readiness_version_id,
            adequacy.facts.version_id,
            reliance.facts.version_id,
            fx.information_basis,
        )
    obligations = (
        ObligationKind.COMPLETE_VALUE_RISK_INTEGRATION,
        ObligationKind.PROPOSE_MANAGEMENT_DECISION,
        ObligationKind.AUTHORIZE_MANAGEMENT_DECISION,
        ObligationKind.CONFIRM_MANAGEMENT_DECISION,
    )
    responsibilities = {
        obligation: establish_responsibility(
            store,
            case_id=fx.opened.facts.case_id,  # type: ignore[attr-defined]
            actor_id=fx.actor_a,
            assigned_actor_id=fx.actor_a,
            context=fx.opened.context,
            obligation=obligation,
            key=f"{key}-{obligation.value}",
        )
        for obligation in obligations
    }
    return SliceDFixture(
        fx,
        ProspectiveDecisionService(
            store,  # type: ignore[arg-type]
            FixedClock(RECORDED + timedelta(seconds=4)),
            fx.access,
        ),
        relied[AssessmentLane.VALUE],
        relied[AssessmentLane.RISK],
        responsibilities,
        substantive_authority(
            store,
            fx,
            actor_id=fx.actor_a,
            actions=("INTEGRATE_VALUE_RISK",),
            key=f"{key}-integration-authority",
        ),
        substantive_authority(
            store,
            fx,
            actor_id=fx.actor_a,
            actions=("AUTHORIZE_DECISION", "CONFIRM_DECISION"),
            key=f"{key}-decision-authority",
        ),
    )


def integration_command(fx: SliceDFixture, key: str) -> IntegrateValueRiskCommand:
    accountability = fx.responsibilities[ObligationKind.COMPLETE_VALUE_RISK_INTEGRATION]
    source = fx.source
    return IntegrateValueRiskCommand(
        identity(source.actor_a, key),
        IntegrationFacts.new(),
        CONTRACT,
        source.opened.context,  # type: ignore[attr-defined]
        source.opened.facts.case_id,  # type: ignore[attr-defined]
        source.opened.facts.configuration_version_id,  # type: ignore[attr-defined]
        DECISION_USE,
        ASSESSED_SCOPE,
        fx.value,
        fx.risk,
        "preserve independent Value and Risk conclusions while synthesizing tensions",
        ("Value opportunity and Risk limitation remain separate",),
        ("bounded use only",),
        "material uncertainty remains visible",
        (),
        accountability.responsibility_version_id,
        accountability.assignment_version_id,
        fx.integration_authority,
        None,
        NOW,
        KNOWLEDGE,
    )


def proposal_command(
    fx: SliceDFixture,
    integration: IntegrateValueRiskCommand,
    key: str,
) -> ProposeDecisionCommand:
    accountability = fx.responsibilities[ObligationKind.PROPOSE_MANAGEMENT_DECISION]
    source = fx.source
    return ProposeDecisionCommand(
        identity(source.actor_a, key),
        DecisionFacts.new(),
        CONTRACT,
        source.opened.context,  # type: ignore[attr-defined]
        source.opened.facts.case_id,  # type: ignore[attr-defined]
        source.opened.facts.configuration_version_id,  # type: ignore[attr-defined]
        integration.facts.version_id,
        DECISION_USE,
        ASSESSED_SCOPE,
        "proceed within the exact bounded scope",
        "bounded continuation",
        "management judgment based on exact independent relied lanes",
        ("remain inside exact scope",),
        ("do not proceed",),
        accountability.responsibility_version_id,
        accountability.assignment_version_id,
        None,
        None,
        NOW,
        KNOWLEDGE,
    )


def test_vertical_proof_binds_exact_lanes_and_separates_authorization(
    sqlite_store: object,
) -> None:
    store = sqlite_store
    fx = slice_d_fixture(store)
    integration = integration_command(fx, "integrate")
    integrated = fx.service.integrate_value_risk(integration)
    assert fx.service.integrate_value_risk(integration) == integrated
    with pytest.raises(ProspectiveDecisionConflict, match="IDEMPOTENCY"):
        fx.service.integrate_value_risk(
            replace(integration, integration_rationale="changed replay payload")
        )
    selected_integration = fx.service.select_integration(
        case_id=integration.case_id,
        configuration_version_id=integration.configuration_version_id,
        context=integration.context,
        decision_use=integration.decision_use,
        bounded_scope=integration.bounded_scope,
        effective_at=NOW,
        known_at=RECORDED + timedelta(seconds=5),
    )
    assert selected_integration.kind is ProspectiveSelectionKind.ONE

    proposal = proposal_command(fx, integration, "propose")
    fx.service.propose_decision(proposal)
    proposed = fx.service.select_decision(
        case_id=proposal.case_id,
        configuration_version_id=proposal.configuration_version_id,
        context=proposal.context,
        decision_use=proposal.decision_use,
        bounded_scope=proposal.bounded_scope,
        effective_at=NOW,
        known_at=RECORDED + timedelta(seconds=5),
    )
    assert proposed.status == ProspectiveDecisionStatus.PROPOSED.value

    authority = fx.responsibilities[ObligationKind.AUTHORIZE_MANAGEMENT_DECISION]
    authorize = AuthorizeDecisionCommand(
        identity(fx.source.actor_a, "authorize"),
        AuthorizationFacts.new(),
        CONTRACT,
        proposal.context,
        proposal.case_id,
        proposal.configuration_version_id,
        proposal.facts.version_id,
        integration.facts.version_id,
        DECISION_USE,
        ASSESSED_SCOPE,
        authority.responsibility_version_id,
        authority.assignment_version_id,
        fx.decision_authority,
        "bounded Decision Authority",
        ASSESSED_SCOPE,
        ("no broader use",),
        ("remain inside exact boundary",),
        (),
        NOW,
        KNOWLEDGE,
    )
    outcome = fx.service.authorize_decision(authorize)
    assert fx.service.authorize_decision(authorize) == outcome
    current = fx.service.select_decision(
        case_id=proposal.case_id,
        configuration_version_id=proposal.configuration_version_id,
        context=proposal.context,
        decision_use=proposal.decision_use,
        bounded_scope=proposal.bounded_scope,
        effective_at=NOW,
        known_at=RECORDED + timedelta(seconds=5),
    )
    assert current.status == ProspectiveDecisionStatus.AUTHORIZED.value

    confirmation = fx.responsibilities[ObligationKind.CONFIRM_MANAGEMENT_DECISION]
    fx.service.confirm_decision(
        ConfirmDecisionCommand(
            identity(fx.source.actor_a, "confirm"),
            ConfirmationFacts.new(),
            CONTRACT,
            proposal.context,
            proposal.case_id,
            proposal.configuration_version_id,
            authorize.facts.decision_version_id,
            integration.facts.version_id,
            DECISION_USE,
            ASSESSED_SCOPE,
            "the exact authorized Decision remains unchanged",
            confirmation.responsibility_version_id,
            confirmation.assignment_version_id,
            fx.decision_authority,
            NOW,
            KNOWLEDGE,
        )
    )
    with store.read_transaction() as tx:  # type: ignore[attr-defined]
        row = tx.projection_rows(
            "prospective_decision_versions",
            version_id=str(authorize.facts.decision_version_id),
        )[0]
        assert row["value_reliance_version_id"] == str(fx.value.reliance_version_id)
        assert row["risk_reliance_version_id"] == str(fx.risk.reliance_version_id)
        assert tx.count_rows("prospective_decision_confirmation_versions") == 1


def test_lane_successor_invalidates_old_chain_without_retarget_or_mutation(
    sqlite_store: object,
) -> None:
    store = sqlite_store
    fx = slice_d_fixture(store, "stale")
    integration = integration_command(fx, "stale-integrate")
    fx.service.integrate_value_risk(integration)
    proposal = proposal_command(fx, integration, "stale-propose")

    # Build the successor from the exact predecessor Record rather than retargeting the command.
    with store.read_transaction() as tx:  # type: ignore[attr-defined]
        prior = tx.get_version(fx.value.assessment_version_id)
        assert prior is not None
    successor = replace(
        finish_command(fx.source, AssessmentLane.VALUE, "value-correction-exact"),
        facts=replace(
            finish_command(fx.source, AssessmentLane.VALUE, "unused-2").facts,
            assessment_record_id=prior.record_id,
        ),
        expected_assessment_version_id=fx.value.assessment_version_id,
    )
    fx.source.service.finish_assessment(successor)
    assert (
        fx.service.select_integration(
            case_id=integration.case_id,
            configuration_version_id=integration.configuration_version_id,
            context=integration.context,
            decision_use=integration.decision_use,
            bounded_scope=integration.bounded_scope,
            effective_at=NOW,
            known_at=RECORDED + timedelta(seconds=5),
        ).kind
        is ProspectiveSelectionKind.ABSENT
    )
    with store.read_transaction() as tx:  # type: ignore[attr-defined]
        before = tx.count_rows("prospective_decision_versions")
    with pytest.raises(ProspectiveDecisionConflict, match="stale"):
        fx.service.propose_decision(proposal)
    with store.read_transaction() as tx:  # type: ignore[attr-defined]
        assert tx.count_rows("prospective_decision_versions") == before == 0
        assert tx.get_version(integration.facts.version_id) is not None
        assert tx.get_version(fx.value.assessment_version_id) is not None


def test_integration_requires_separate_authority_and_never_uses_legacy_fallback(
    sqlite_store: object,
) -> None:
    store = sqlite_store
    fx = slice_d_fixture(store, "authority")
    command = integration_command(fx, "wrong-authority")
    before: tuple[int, int]
    with store.read_transaction() as tx:  # type: ignore[attr-defined]
        before = (
            tx.count_rows("prospective_integration_versions"),
            tx.count_rows("integration_versions"),
        )
    with pytest.raises(ProspectiveDecisionConflict, match="substantive authority"):
        fx.service.integrate_value_risk(
            replace(command, authority_source_version_id=fx.decision_authority)
        )
    with store.read_transaction() as tx:  # type: ignore[attr-defined]
        assert (
            tx.count_rows("prospective_integration_versions"),
            tx.count_rows("integration_versions"),
        ) == before

    valid = replace(command, identity=identity(fx.source.actor_a, "valid-integration"))
    fx.service.integrate_value_risk(valid)
    proposal = proposal_command(fx, valid, "authority-proposal")
    fx.service.propose_decision(proposal)
    accountability = fx.responsibilities[ObligationKind.AUTHORIZE_MANAGEMENT_DECISION]
    wrong_authorization = AuthorizeDecisionCommand(
        identity(fx.source.actor_a, "wrong-decision-authority"),
        AuthorizationFacts.new(),
        CONTRACT,
        proposal.context,
        proposal.case_id,
        proposal.configuration_version_id,
        proposal.facts.version_id,
        valid.facts.version_id,
        DECISION_USE,
        ASSESSED_SCOPE,
        accountability.responsibility_version_id,
        accountability.assignment_version_id,
        fx.integration_authority,
        "Integration Authority is not Decision Authority",
        ASSESSED_SCOPE,
        (),
        (),
        (),
        NOW,
        KNOWLEDGE,
    )
    with store.read_transaction() as tx:  # type: ignore[attr-defined]
        decision_count = tx.count_rows("prospective_decision_versions")
    with pytest.raises(ProspectiveDecisionConflict, match="substantive authority"):
        fx.service.authorize_decision(wrong_authorization)
    with store.read_transaction() as tx:  # type: ignore[attr-defined]
        assert tx.count_rows("prospective_decision_versions") == decision_count


def test_practitioner_composition_filters_exact_sources_before_slice_d_state(
    sqlite_store: object,
) -> None:
    store = sqlite_store
    fx = slice_d_fixture(store, "non-disclosure")
    integration = integration_command(fx, "visible-integration")
    fx.service.integrate_value_risk(integration)
    proposal = proposal_command(fx, integration, "visible-proposal")
    fx.service.propose_decision(proposal)

    def view(hidden: frozenset[RecordVersionId]) -> object:
        access = SelectiveSourceAccess(hidden)
        queries = PractitionerQueryService(
            store,  # type: ignore[arg-type]
            CaseContinuityService(
                store,  # type: ignore[arg-type]
                FixedClock(RECORDED + timedelta(seconds=5)),
                access,
            ),
            access,
        )
        return queries.case(
            principal_id="principal:slice-c",
            actor_id=fx.source.actor_a,
            case_id=integration.case_id,
            effective_at=NOW,
            known_at=RECORDED + timedelta(seconds=5),
        )

    visible = view(frozenset())
    assert visible.integration_position is not None  # type: ignore[attr-defined]
    assert visible.integration_position.state == "COMPLETED"  # type: ignore[attr-defined]
    assert visible.decision_position is not None  # type: ignore[attr-defined]
    assert visible.decision_position.state == "PROPOSED"  # type: ignore[attr-defined]

    hidden_lane = view(frozenset({fx.value.reliance_version_id}))
    assert hidden_lane.integration_position is not None  # type: ignore[attr-defined]
    assert hidden_lane.integration_position.state == "STATUS NOT AVAILABLE"  # type: ignore[attr-defined]
    assert hidden_lane.integration_position.source_version_ids == ()  # type: ignore[attr-defined]
    assert hidden_lane.decision_position is None  # type: ignore[attr-defined]

    hidden_integration = view(frozenset({integration.facts.version_id}))
    assert hidden_integration.integration_position is not None  # type: ignore[attr-defined]
    assert hidden_integration.integration_position.state == "STATUS NOT AVAILABLE"  # type: ignore[attr-defined]
    assert hidden_integration.decision_position is None  # type: ignore[attr-defined]


def test_slice_d_facts_prohibit_destructive_migration_downgrade(
    sqlite_store: object,
) -> None:
    fx = slice_d_fixture(sqlite_store, "downgrade")
    fx.service.integrate_value_risk(integration_command(fx, "downgrade-integration"))
    config = alembic_config(str(sqlite_store.engine.url))  # type: ignore[attr-defined]
    with pytest.raises(RuntimeError, match="destructive rollback is prohibited"):
        alembic_command.downgrade(config, "0012_gate8_assessment_review")
    with sqlite_store.engine.connect() as connection:  # type: ignore[attr-defined]
        assert connection.exec_driver_sql(
            "SELECT version_num FROM alembic_version"
        ).scalar_one() == ("0013_gate8_integration_decision_basis")
