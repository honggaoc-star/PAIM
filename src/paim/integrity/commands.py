"""Versioned canonical semantic-command digest."""

from __future__ import annotations

import hashlib
import json

from paim.integrity.records import JsonValue

CANONICAL_COMMAND_VERSION = 1


def canonical_command_digest(payload: dict[str, JsonValue]) -> str:
    envelope: dict[str, JsonValue] = {
        "canonical_command_version": CANONICAL_COMMAND_VERSION,
        "payload": payload,
    }
    encoded = json.dumps(
        envelope,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()
