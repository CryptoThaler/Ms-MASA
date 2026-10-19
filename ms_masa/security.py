"""
Shared hardening helpers for Ms-MASA's network-facing servers.

Policy:
- Servers bind to 127.0.0.1 by default.
- Binding to a non-loopback address requires a bearer token
  (MS_MASA_AUTH_TOKEN), checked in constant time on every request.
- Callers never see internal exception text; details go to the server log.
"""

from __future__ import annotations

import hmac
import ipaddress
import logging
import os
import uuid

logger = logging.getLogger("ms_masa.security")

DEFAULT_HOST = "127.0.0.1"
AUTH_TOKEN_ENV = "MS_MASA_AUTH_TOKEN"
MIN_TOKEN_LENGTH = 16


def is_loopback(host: str) -> bool:
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def load_auth_token() -> str | None:
    token = os.getenv(AUTH_TOKEN_ENV, "").strip()
    if not token:
        return None
    if len(token) < MIN_TOKEN_LENGTH:
        raise SystemExit(
            f"{AUTH_TOKEN_ENV} must be at least {MIN_TOKEN_LENGTH} characters. "
            "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
        )
    return token


def enforce_bind_policy(host: str, token: str | None) -> None:
    """Refuse to expose an unauthenticated server beyond loopback."""
    if not is_loopback(host) and token is None:
        raise SystemExit(
            f"Refusing to bind {host} without authentication. "
            f"Set {AUTH_TOKEN_ENV} to require a bearer token, or bind {DEFAULT_HOST}."
        )


def bearer_matches(authorization: str | None, token: str | None) -> bool:
    """True if no token is configured, or the Authorization header carries it."""
    if token is None:
        return True
    if not authorization or not authorization.startswith("Bearer "):
        return False
    return hmac.compare_digest(authorization[len("Bearer "):].encode(), token.encode())


def public_error(exc: BaseException, context: str = "request") -> str:
    """Log the real error server-side and return an opaque message for callers."""
    error_id = uuid.uuid4().hex[:12]
    logger.error("%s failed [%s]", context, error_id, exc_info=exc)
    return f"Internal error ({type(exc).__name__}); reference {error_id}"


class BearerAuthASGI:
    """Minimal ASGI middleware enforcing a bearer token on HTTP requests."""

    def __init__(self, app, token: str):
        self.app = app
        self.token = token

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = {k.decode("latin-1").lower(): v.decode("latin-1") for k, v in scope.get("headers", [])}
        if bearer_matches(headers.get("authorization"), self.token):
            return await self.app(scope, receive, send)
        body = b'{"error":"unauthorized"}'
        await send({
            "type": "http.response.start",
            "status": 401,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode()),
                (b"www-authenticate", b"Bearer"),
            ],
        })
        await send({"type": "http.response.body", "body": body})
