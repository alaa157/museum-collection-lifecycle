from datetime import datetime, timedelta, timezone
from uuid import uuid4
import jwt
from jwt import InvalidTokenError
from app.core.config import get_settings

settings = get_settings()

class TokenError(Exception):
    pass

def _create_token(
    subject: str,
    token_type: str,
    expires_delta: timedelta,
    extra_claims: dict | None = None,
) -> tuple[str, str, datetime]:
    now = datetime.now(timezone.utc)
    expires_at = now + expires_delta
    jti = uuid4().hex

    payload = {
        "sub": subject,
        "type": token_type,
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }

    if extra_claims:
        payload.update(extra_claims)

    token = jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    return token, jti, expires_at


def create_access_token(user_id: int, roles: list[str]) -> str:
    token, _, _ = _create_token(
        subject=str(user_id),
        token_type="access",
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        extra_claims={"roles": roles},
    )
    return token


def create_refresh_token(user_id: int) -> tuple[str, str, datetime]:
    return _create_token(
        subject=str(user_id),
        token_type="refresh",
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
    )


def decode_token(token: str, expected_type: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except InvalidTokenError as exc:
        raise TokenError("Invalid or expired token.") from exc

    if payload.get("type") != expected_type:
        raise TokenError("Invalid token type.")

    if not payload.get("sub"):
        raise TokenError("Token subject is missing.")

    return payload
