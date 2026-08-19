"""Small local CLI for the bounded PAIM v0.1 operational application."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import cast

from paim.domain import (
    ActorVersionInput,
    CaseVersionInput,
    ConfigurationMaturity,
    ConfigurationPurpose,
    ConfigurationVersionInput,
)
from paim.integrity import EffectiveInterval, RecordId, RecordVersionId
from paim.integrity.records import JsonValue
from paim.operational.application import OperationalApplication
from paim.operational.configuration import credential_from_environment, load_configuration
from paim.operational.models import (
    AccessEffect,
    AccessGrantInput,
    AdapterType,
    IntakeEnvelope,
    Permission,
    PrincipalStatus,
    ScopeType,
)
from paim.persistence.sqlite import upgrade_database


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="paim-local")
    parser.add_argument("--config", type=Path, required=True)
    commands = parser.add_subparsers(dest="command", required=True)

    bootstrap = commands.add_parser("bootstrap")
    bootstrap.add_argument("--principal", required=True)
    bootstrap.add_argument("--actor-id")
    bootstrap.add_argument("--admin", action="store_true")
    bootstrap.add_argument("--case-read", action="append", default=[])
    bootstrap.add_argument("--configuration-read", action="append", default=[])
    bootstrap.add_argument("--allow-command", action="append", default=[])
    bootstrap.add_argument("--allow-export", action="store_true")
    bootstrap.add_argument("--allow-delivery", action="store_true")

    login_parent = argparse.ArgumentParser(add_help=False)
    login_parent.add_argument("--principal", required=True)

    commands.add_parser("health", parents=[login_parent])
    commands.add_parser("counters", parents=[login_parent])

    actor = commands.add_parser("actor-create", parents=[login_parent])
    actor.add_argument("--display-name", required=True)
    actor.add_argument("--effective-at", required=True)

    principal = commands.add_parser("principal-update", parents=[login_parent])
    principal.add_argument("--subject-principal", required=True)
    principal.add_argument("--subject-token-env", required=True)
    principal.add_argument("--actor-id")
    principal.add_argument(
        "--status", choices=[item.value for item in PrincipalStatus], required=True
    )

    access = commands.add_parser("access-grant", parents=[login_parent])
    access.add_argument("--subject-principal", required=True)
    access.add_argument("--permission", choices=[item.value for item in Permission], required=True)
    access.add_argument("--action", required=True)
    access.add_argument("--scope-type", choices=[item.value for item in ScopeType], required=True)
    access.add_argument("--scope-id")
    access.add_argument("--effect", choices=[item.value for item in AccessEffect], required=True)

    case = commands.add_parser("case-create", parents=[login_parent])
    case.add_argument("--title", required=True)
    case.add_argument("--effective-at", required=True)

    configuration = commands.add_parser("configuration-create", parents=[login_parent])
    configuration.add_argument("--case-id", required=True)
    configuration.add_argument(
        "--maturity", choices=[item.value for item in ConfigurationMaturity], required=True
    )
    configuration.add_argument(
        "--purpose", choices=[item.value for item in ConfigurationPurpose], required=True
    )
    configuration.add_argument("--effective-at", required=True)
    configuration.add_argument("--content-file", type=Path, required=True)

    intake = commands.add_parser("intake", parents=[login_parent])
    intake.add_argument("--type", choices=[item.value for item in AdapterType], required=True)
    intake.add_argument("--source-system", required=True)
    intake.add_argument("--source-object-id", required=True)
    intake.add_argument("--source-version")
    intake.add_argument("--source-effective-at", required=True)
    intake.add_argument("--replay-id", required=True)
    intake.add_argument("--mapper-rule-id", required=True)
    intake.add_argument("--mapper-rule-version", required=True)
    intake.add_argument("--case-id")
    intake.add_argument("--configuration-id")
    intake.add_argument("--management-context")
    intake.add_argument("--file", type=Path, required=True)

    export = commands.add_parser("export", parents=[login_parent])
    export.add_argument("--manifest-id", required=True)
    export.add_argument("--format", choices=("json", "csv"), required=True)

    delivery = commands.add_parser("deliver", parents=[login_parent])
    delivery.add_argument("--intent-id", required=True)
    delivery.add_argument("--attempt-id", required=True)

    backup = commands.add_parser("backup", parents=[login_parent])
    backup.add_argument("--label", required=True)

    restore = commands.add_parser("restore", parents=[login_parent])
    restore.add_argument("--backup", type=Path, required=True)
    restore.add_argument("--manifest", type=Path, required=True)
    restore.add_argument("--target", type=Path, required=True)

    unsupported = commands.add_parser("unsupported", parents=[login_parent])
    unsupported.add_argument("capability")
    return parser


def _grant(
    permission: Permission,
    action: str,
    scope_type: ScopeType = ScopeType.GLOBAL,
    scope_id: str | None = None,
) -> AccessGrantInput:
    return AccessGrantInput(
        permission,
        action,
        scope_type,
        RecordId.parse(scope_id) if scope_id else None,
        AccessEffect.ALLOW,
    )


def _bootstrap_grants(args: argparse.Namespace) -> tuple[AccessGrantInput, ...]:
    grants = [_grant(Permission.LOGIN, "use")]
    grants.extend(
        _grant(Permission.CASE_READ, "read", ScopeType.CASE, item) for item in args.case_read
    )
    grants.extend(
        _grant(Permission.CONFIGURATION_READ, "read", ScopeType.CONFIGURATION, item)
        for item in args.configuration_read
    )
    grants.extend(_grant(Permission.COMMAND, item) for item in args.allow_command)
    if args.allow_export:
        grants.extend(
            (
                _grant(Permission.EXPORT, "register.output"),
                _grant(Permission.EXPORT, "register.export"),
            )
        )
    if args.allow_delivery:
        grants.append(_grant(Permission.DELIVERY, "notification.deliver"))
    if args.admin:
        for action in (
            "principal.manage",
            "access.manage",
            "backup.create",
            "restore.verify",
            "observability.read",
        ):
            grants.append(_grant(Permission.OPERATIONAL_ADMIN, action))
    return tuple(grants)


def _json(value: object) -> None:
    def default(item: object) -> str:
        if isinstance(item, (datetime, Path, RecordId)):
            return str(item)
        raise TypeError(f"cannot encode {type(item).__name__}")

    print(json.dumps(value, default=default, sort_keys=True, separators=(",", ":")))


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    config = load_configuration(args.config)
    token = credential_from_environment(config)
    upgrade_database(config.database_url)
    with OperationalApplication(config) as app:
        if args.command == "bootstrap":
            app.bootstrap_principal(
                principal_id=args.principal,
                token=token,
                actor_id=RecordId.parse(args.actor_id) if args.actor_id else None,
                grants=_bootstrap_grants(args),
            )
            _json({"status": "BOOTSTRAPPED", "principal_id": args.principal})
            return 0
        session = app.authenticate(args.principal, token)
        if args.command == "health":
            _json(asdict(app.health()))
        elif args.command == "counters":
            _json(app.counters(session))
        elif args.command == "actor-create":
            actor_id = RecordId.new()
            actor_outcome = app.run_command(
                session,
                action="actor.create",
                idempotency_key=f"cli-actor-{actor_id}",
                operation=lambda service, meta: service.commit_actor(
                    meta,
                    ActorVersionInput(
                        actor_id,
                        RecordVersionId.new(),
                        args.display_name,
                        EffectiveInterval(datetime.fromisoformat(args.effective_at)),
                    ),
                ),
            )
            _json({"actor_id": actor_id, "outcome": asdict(actor_outcome)})
        elif args.command == "principal-update":
            subject_token = os.environ.get(args.subject_token_env)
            if not subject_token:
                raise ValueError("subject credential environment source is unavailable")
            app.provision_principal(
                session,
                principal_id=args.subject_principal,
                token=subject_token,
                actor_id=RecordId.parse(args.actor_id) if args.actor_id else None,
                status=PrincipalStatus(args.status),
            )
            _json({"status": "PRINCIPAL_VERSION_APPENDED"})
        elif args.command == "access-grant":
            scope_type = ScopeType(args.scope_type)
            scope_id = RecordId.parse(args.scope_id) if args.scope_id else None
            app.grant_access(
                session,
                principal_id=args.subject_principal,
                grant=AccessGrantInput(
                    Permission(args.permission),
                    args.action,
                    scope_type,
                    scope_id,
                    AccessEffect(args.effect),
                ),
            )
            _json({"status": "SOFTWARE_ACCESS_FACT_APPENDED"})
        elif args.command == "case-create":
            case_id = RecordId.new()
            case_outcome = app.run_command(
                session,
                action="case.create",
                idempotency_key=f"cli-case-{case_id}",
                operation=lambda service, meta: service.commit_case(
                    meta,
                    CaseVersionInput(
                        case_id,
                        RecordVersionId.new(),
                        args.title,
                        EffectiveInterval(datetime.fromisoformat(args.effective_at)),
                    ),
                ),
            )
            _json({"case_id": case_id, "outcome": asdict(case_outcome)})
        elif args.command == "configuration-create":
            content = cast(
                "dict[str, JsonValue]",
                json.loads(args.content_file.read_text(encoding="utf-8")),
            )
            case_id = RecordId.parse(args.case_id)
            configuration_id = RecordId.new()
            configuration_outcome = app.run_command(
                session,
                action="configuration.create",
                idempotency_key=f"cli-configuration-{configuration_id}",
                case_id=case_id,
                operation=lambda service, meta: service.commit_configuration(
                    meta,
                    ConfigurationVersionInput(
                        configuration_id,
                        RecordVersionId.new(),
                        case_id,
                        ConfigurationMaturity(args.maturity),
                        ConfigurationPurpose(args.purpose),
                        content,
                        EffectiveInterval(datetime.fromisoformat(args.effective_at)),
                    ),
                ),
            )
            _json(
                {
                    "configuration_id": configuration_id,
                    "outcome": asdict(configuration_outcome),
                }
            )
        elif args.command == "intake":
            try:
                payload = cast(
                    "dict[str, JsonValue]", json.loads(args.file.read_text(encoding="utf-8"))
                )
            except (OSError, ValueError, TypeError) as error:
                raise ValueError("intake file must contain one JSON object") from error
            intake_result = app.intake(
                session,
                IntakeEnvelope(
                    adapter_type=AdapterType(args.type),
                    source_system=args.source_system,
                    source_object_id=args.source_object_id,
                    source_version=args.source_version,
                    source_effective_at=datetime.fromisoformat(args.source_effective_at),
                    payload=payload,
                    replay_id=args.replay_id,
                    mapper_rule_id=args.mapper_rule_id,
                    mapper_rule_version=args.mapper_rule_version,
                    target_case_id=RecordId.parse(args.case_id) if args.case_id else None,
                    target_configuration_id=(
                        RecordId.parse(args.configuration_id) if args.configuration_id else None
                    ),
                    management_context=args.management_context,
                    payload_reference=args.file.name,
                ),
            )
            _json(asdict(intake_result))
        elif args.command == "export":
            _json(
                {"path": app.export_manifest(session, args.manifest_id, output_format=args.format)}
            )
        elif args.command == "deliver":
            _json(
                asdict(
                    app.deliver_notification(
                        session, intent_id=args.intent_id, attempt_id=args.attempt_id
                    )
                )
            )
        elif args.command == "backup":
            backup, manifest, value = app.backup(session, label=args.label)
            _json({"backup": backup, "manifest": manifest, "basis": asdict(value)})
        elif args.command == "restore":
            _json(
                asdict(
                    app.restore(
                        session,
                        backup_path=args.backup,
                        manifest_path=args.manifest,
                        target_path=args.target,
                    )
                )
            )
        elif args.command == "unsupported":
            app.require_supported(args.capability)
        else:
            raise AssertionError("unreachable CLI command")
    return 0
