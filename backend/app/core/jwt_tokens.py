"""Minimal HS256 JWT support for the app's fixed symmetric token format."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from datetime import datetime, timezone
from typing import Any


class TokenDecodeError(ValueError):
    pass


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    try:
        encoded = value.encode("ascii")
        return base64.b64decode(
            encoded + b"=" * (-len(encoded) % 4), altchars=b"-_", validate=True
        )
    except (UnicodeEncodeError, ValueError) as exc:
        raise TokenDecodeError("Malformed token encoding") from exc


def encode_hs256(claims: dict[str, Any], secret: str) -> str:
    header = _b64url_encode(json.dumps(
        {"alg": "HS256", "typ": "JWT"}, separators=(",", ":")
    ).encode("utf-8"))
    payload = dict(claims)
    exp = payload.get("exp")
    if isinstance(exp, datetime):
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        payload["exp"] = int(exp.timestamp())
    body = _b64url_encode(json.dumps(
        payload, separators=(",", ":"), default=str
    ).encode("utf-8"))
    signing_input = f"{header}.{body}".encode("ascii")
    signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{header}.{body}.{_b64url_encode(signature)}"


def decode_hs256(token: str, secrets: list[str]) -> dict[str, Any]:
    if not isinstance(token, str) or len(token) > 8192:
        raise TokenDecodeError("Invalid token")
    parts = token.split(".")
    if len(parts) != 3 or not all(parts):
        raise TokenDecodeError("Malformed token")
    header_bytes = _b64url_decode(parts[0])
    payload_bytes = _b64url_decode(parts[1])
    supplied_signature = _b64url_decode(parts[2])
    try:
        header = json.loads(header_bytes)
        payload = json.loads(payload_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TokenDecodeError("Malformed token JSON") from exc
    if not isinstance(header, dict) or header.get("alg") != "HS256":
        raise TokenDecodeError("Unsupported token algorithm")
    if header.get("crit") or header.get("b64") is False:
        raise TokenDecodeError("Unsupported token header")
    if not isinstance(payload, dict):
        raise TokenDecodeError("Malformed token claims")

    signing_input = f"{parts[0]}.{parts[1]}".encode("ascii")
    valid_signature = any(
        hmac.compare_digest(
            supplied_signature,
            hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest(),
        )
        for secret in secrets
        if secret
    )
    if not valid_signature:
        raise TokenDecodeError("Invalid token signature")

    exp = payload.get("exp")
    if isinstance(exp, bool) or not isinstance(exp, (int, float)) or exp <= time.time():
        raise TokenDecodeError("Token expired or has no expiry")
    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise TokenDecodeError("Token subject is required")
    return payload
