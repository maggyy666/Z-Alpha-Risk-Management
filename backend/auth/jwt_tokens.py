"""JWT issue/verify helpers shared by user-api and backend.

HS256 symmetric signing with AUTH_SECRET -- same secret is mounted into both
services so they agree on token validity. Tokens carry `sub` (username) and
`exp` claims; issue() returns the encoded string, decode() returns the claims
dict or raises on invalid/expired tokens.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import jwt

_ALGO = "HS256"
_DEFAULT_TTL_HOURS = 24


def _secret() -> str:
    secret = os.environ.get("AUTH_SECRET")
    if not secret:
        raise RuntimeError("AUTH_SECRET is not set")
    return secret


def issue(username: str, ttl_hours: int | None = None) -> str:
    ttl = ttl_hours if ttl_hours is not None else _DEFAULT_TTL_HOURS
    now = datetime.now(timezone.utc)
    payload = {
        "sub": username,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=ttl)).timestamp()),
    }
    return jwt.encode(payload, _secret(), algorithm=_ALGO)


def decode(token: str) -> Dict[str, Any]:
    """Return claims dict. Raises jwt.InvalidTokenError / jwt.ExpiredSignatureError."""
    return jwt.decode(token, _secret(), algorithms=[_ALGO])
