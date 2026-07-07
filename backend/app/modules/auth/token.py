from __future__ import annotations

import base64
import json
import hmac
import hashlib
import time
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from app.core.config import Settings
from app.modules.auth.exceptions import AuthConfigurationError, InvalidTokenError


def create_access_token(
    settings: Settings,
    *,
    user_id: UUID,
    session_id: UUID,
    now: datetime | None = None,
) -> tuple[str, datetime]:
    issued_at = now or datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "sid": str(session_id),
        "typ": "access",
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    return encode_jwt(settings, payload), expires_at


def decode_access_token(settings: Settings, token: str) -> dict[str, Any]:
    payload = decode_jwt(settings, token)
    if payload.get("typ") != "access":
        raise InvalidTokenError("invalid token")
    try:
        UUID(str(payload["sub"]))
        UUID(str(payload["sid"]))
    except (KeyError, ValueError) as exc:
        raise InvalidTokenError("invalid token") from exc
    return payload


def encode_jwt(settings: Settings, payload: dict[str, Any]) -> str:
    secret = _jwt_secret(settings)
    header = {"alg": settings.JWT_ALGORITHM, "typ": "JWT"}
    if settings.JWT_ALGORITHM != "HS256":
        raise AuthConfigurationError("unsupported jwt algorithm")
    segments = [_json_b64(header), _json_b64(payload)]
    signing_input = ".".join(segments).encode("ascii")
    signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    segments.append(_b64encode(signature))
    return ".".join(segments)


def decode_jwt(settings: Settings, token: str) -> dict[str, Any]:
    secret = _jwt_secret(settings)
    try:
        header_segment, payload_segment, signature_segment = token.split(".")
        signing_input = f"{header_segment}.{payload_segment}".encode("ascii")
        expected = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
        actual = _b64decode(signature_segment)
        if not hmac.compare_digest(actual, expected):
            raise InvalidTokenError("invalid token")
        header = json.loads(_b64decode(header_segment))
        payload = json.loads(_b64decode(payload_segment))
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise InvalidTokenError("invalid token") from exc
    if header.get("alg") != settings.JWT_ALGORITHM:
        raise InvalidTokenError("invalid token")
    exp = payload.get("exp")
    if not isinstance(exp, int) or exp < int(time.time()):
        raise InvalidTokenError("invalid token")
    return payload


def _jwt_secret(settings: Settings) -> str:
    secret = settings.JWT_SECRET_KEY or settings.SECRET_KEY
    if not secret:
        raise AuthConfigurationError("jwt secret is not configured")
    return secret


def _json_b64(value: dict[str, Any]) -> str:
    data = json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return _b64encode(data)


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))
