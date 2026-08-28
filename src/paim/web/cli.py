"""Loopback-only launcher for the PAIM M1A browser foundation."""

from __future__ import annotations

import argparse
import secrets
import threading
from pathlib import Path

import uvicorn

from paim.operational import OperationalApplication, ReadinessState, load_configuration
from paim.persistence.sqlite import upgrade_database
from paim.web.app import create_web_application
from paim.web.lifecycle import LifecycleCoordinator, configuration_fingerprint

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8841


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="paim-web")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.host != DEFAULT_HOST:
        raise SystemExit("M1A permits binding only to 127.0.0.1")
    if not 1_024 <= args.port <= 65_535:
        raise SystemExit("port must be between 1024 and 65535")
    if len(secrets.token_bytes(32)) != 32:
        raise SystemExit("secure randomness is unavailable")
    config = load_configuration(args.config)
    upgrade_database(config.database_url)
    operational = OperationalApplication(config)
    health = operational.health()
    if health.state is not ReadinessState.READY:
        operational.close()
        raise SystemExit("PAIM required startup health checks did not pass")
    local_url = f"http://{DEFAULT_HOST}:{args.port}"
    lifecycle = LifecycleCoordinator()
    app = create_web_application(
        config,
        operational=operational,
        expected_origin=local_url,
        startup_announcement=f"PAIM local URL: {local_url}",
        lifecycle=lifecycle,
        instance_fingerprint=configuration_fingerprint(args.config),
    )
    server = uvicorn.Server(
        uvicorn.Config(
            app,
            host=DEFAULT_HOST,
            port=args.port,
            workers=1,
            reload=False,
            access_log=True,
        )
    )

    def request_server_exit() -> None:
        lifecycle.wait_for_stop()
        server.should_exit = True

    monitor = threading.Thread(
        target=request_server_exit,
        name="paim-lifecycle-monitor",
        daemon=True,
    )
    monitor.start()
    try:
        server.run()
    finally:
        operational.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
