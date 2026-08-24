from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from paim.domain import (
    ActorVersionInput,
    CaseVersionInput,
    ConfigurationMaturity,
    ConfigurationPurpose,
    ConfigurationVersionInput,
    DelegationEffect,
    RoleAssignmentVersionInput,
    RoleTargetType,
)
from paim.integrity import EffectiveInterval, FixedClock, RecordId, RecordVersionId
from paim.operational import (
    AccessEffect,
    AccessGrantInput,
    AuthenticatedSession,
    LocalConfiguration,
    OperationalApplication,
    Permission,
    PrincipalStatus,
    ScopeType,
)
from paim.persistence.sqlite import upgrade_database
from paim.web import create_web_application
from paim.web.sessions import SessionRegistry
from tests.helpers import utc

NOW = utc(2026, 8, 21)
EFFECTIVE = EffectiveInterval(utc(2026, 1, 1))
TOKEN = "m1a-protected-test-token-00000001"
ORIGIN = "http://127.0.0.1:8841"


@dataclass
class MutableNow:
    value: datetime = NOW

    def __call__(self) -> datetime:
        return self.value

    def advance(self, delta: timedelta) -> None:
        self.value = self.value + delta


@dataclass
class WebFixture:
    config: LocalConfiguration
    operational: OperationalApplication
    admin_session: AuthenticatedSession
    actor_id: RecordId
    visible_case_id: RecordId
    visible_configuration_id: RecordId
    hidden_case_id: RecordId
    sessions: SessionRegistry
    client: TestClient
    now: MutableNow


def allow(
    permission: Permission,
    action: str,
    scope_type: ScopeType = ScopeType.GLOBAL,
    scope_id: RecordId | None = None,
    effect: AccessEffect = AccessEffect.ALLOW,
) -> AccessGrantInput:
    return AccessGrantInput(permission, action, scope_type, scope_id, effect)


def grant(
    fixture: WebFixture,
    permission: Permission,
    action: str,
    scope_type: ScopeType = ScopeType.GLOBAL,
    scope_id: RecordId | None = None,
    effect: AccessEffect = AccessEffect.ALLOW,
) -> None:
    fixture.operational.grant_access(
        fixture.admin_session,
        principal_id="principal:web-practitioner",
        grant=allow(permission, action, scope_type, scope_id, effect),
    )


def establish_m1b_accountability(fixture: WebFixture) -> None:
    """Establish separate exact functions used by browser judgment oracles."""
    grant(
        fixture,
        Permission.COMMAND,
        "role-assignment.create",
        ScopeType.CASE,
        fixture.visible_case_id,
    )
    for role, key in (
        ("Applicability Owner", "evidence-applicability"),
        ("Value Evaluator", "value-governed-judgments"),
        ("Risk Evaluator", "risk-governed-judgments"),
    ):
        fixture.operational.run_command(
            fixture.admin_session,
            action="role-assignment.create",
            idempotency_key=f"web-{key}",
            case_id=fixture.visible_case_id,
            configuration_id=fixture.visible_configuration_id,
            operation=lambda service, meta, function=role, compatibility=key: (
                service.commit_role_assignment(
                    meta,
                    RoleAssignmentVersionInput(
                        RecordId.new(),
                        RecordVersionId.new(),
                        fixture.actor_id,
                        function,
                        RoleTargetType.CONFIGURATION,
                        str(fixture.visible_configuration_id),
                        fixture.visible_case_id,
                        True,
                        compatibility,
                        DelegationEffect.NONE,
                        None,
                        EFFECTIVE,
                    ),
                )
            ),
        )


def csrf_from(response_text: str) -> str:
    match = re.search(r'name="csrf_token" value="([^"]+)"', response_text)
    assert match is not None
    return match.group(1)


def login(client: TestClient, *, token: str = TOKEN) -> tuple[str, object]:
    login_page = client.get("/login")
    before = client.cookies.get("paim_session")
    assert before
    response = client.post(
        "/session",
        data={
            "principal_id": "principal:web-practitioner",
            "credential": token,
            "csrf_token": csrf_from(login_page.text),
        },
        headers={"Origin": ORIGIN},
        follow_redirects=False,
    )
    return before, response


@pytest.fixture
def web_fixture(tmp_path: Path) -> Iterator[WebFixture]:
    config = LocalConfiguration(
        database_path=tmp_path / "paim.sqlite3",
        credential_env="PAIM_WEB_TEST_TOKEN",
        intake_directory=tmp_path / "intake",
        spool_directory=tmp_path / "spool",
        export_directory=tmp_path / "export",
        backup_directory=tmp_path / "backup",
        event_log_path=tmp_path / "events" / "operational.jsonl",
    )
    for directory in (
        config.intake_directory,
        config.spool_directory,
        config.export_directory,
        config.backup_directory,
        config.event_log_path.parent,
    ):
        directory.mkdir(parents=True)
    upgrade_database(config.database_url)
    operational = OperationalApplication(config, FixedClock(NOW))
    operational.bootstrap_principal(
        principal_id="principal:web-practitioner",
        token=TOKEN,
        actor_id=None,
        grants=(
            allow(Permission.LOGIN, "use"),
            allow(Permission.COMMAND, "actor.create"),
            allow(Permission.COMMAND, "case.create"),
            allow(Permission.OPERATIONAL_ADMIN, "principal.manage"),
            allow(Permission.OPERATIONAL_ADMIN, "access.manage"),
        ),
    )
    unresolved = operational.authenticate("principal:web-practitioner", TOKEN)
    actor_id = RecordId.new()
    operational.run_command(
        unresolved,
        action="actor.create",
        idempotency_key="web-actor",
        operation=lambda service, meta: service.commit_actor(
            meta,
            ActorVersionInput(
                actor_id,
                RecordVersionId.new(),
                "M1A Practitioner",
                EFFECTIVE,
            ),
        ),
    )
    operational.provision_principal(
        unresolved,
        principal_id="principal:web-practitioner",
        token=TOKEN,
        actor_id=actor_id,
        status=PrincipalStatus.ENABLED,
    )
    session = operational.authenticate("principal:web-practitioner", TOKEN)
    visible_case_id = RecordId.new()
    hidden_case_id = RecordId.new()
    for case_id, title, key in (
        (visible_case_id, "Visible governed service", "visible"),
        (hidden_case_id, "Protected hidden service", "hidden"),
    ):
        operational.run_command(
            session,
            action="case.create",
            idempotency_key=f"web-case-{key}",
            operation=lambda service, meta, identity=case_id, label=title: service.commit_case(
                meta,
                CaseVersionInput(identity, RecordVersionId.new(), label, EFFECTIVE),
            ),
        )
    operational.grant_access(
        session,
        principal_id="principal:web-practitioner",
        grant=allow(Permission.CASE_READ, "read", ScopeType.CASE, visible_case_id),
    )
    operational.grant_access(
        session,
        principal_id="principal:web-practitioner",
        grant=allow(
            Permission.COMMAND,
            "configuration.create",
            ScopeType.CASE,
            visible_case_id,
        ),
    )
    configuration_id = RecordId.new()
    operational.run_command(
        session,
        action="configuration.create",
        idempotency_key="web-visible-configuration",
        case_id=visible_case_id,
        operation=lambda service, meta: service.commit_configuration(
            meta,
            ConfigurationVersionInput(
                configuration_id,
                RecordVersionId.new(),
                visible_case_id,
                ConfigurationMaturity.FINALIZED,
                ConfigurationPurpose.CANDIDATE,
                {"system": "visible"},
                EFFECTIVE,
            ),
        ),
    )
    operational.grant_access(
        session,
        principal_id="principal:web-practitioner",
        grant=allow(
            Permission.CONFIGURATION_READ,
            "read",
            ScopeType.CONFIGURATION,
            configuration_id,
        ),
    )
    mutable_now = MutableNow()
    sessions = SessionRegistry(now=mutable_now)
    app = create_web_application(
        config,
        operational=operational,
        sessions=sessions,
        expected_origin=ORIGIN,
        now=mutable_now,
    )
    with TestClient(app, base_url=ORIGIN) as client:
        yield WebFixture(
            config,
            operational,
            session,
            actor_id,
            visible_case_id,
            configuration_id,
            hidden_case_id,
            sessions,
            client,
            mutable_now,
        )
    operational.close()
