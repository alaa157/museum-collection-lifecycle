import hashlib
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.models.role import Role
from app.repositories.user_repository import UserRepository
from app.security.jwt import (
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.security.passwords import verify_password


class AuthenticationService:
    def __init__(self, users: UserRepository):
        self.users = users

    @staticmethod
    def _hash_refresh_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @staticmethod
    def _roles(user: User) -> list[str]:
        return [role.name for role in user.roles]

    def authenticate(self, db: Session, email: str, password: str) -> User:
        user = self.users.get_by_email(db, email)
        if not user or not verify_password(password, user.password_hash):
            raise ValueError("Invalid email or password.")

        if not user.is_active:
            raise ValueError("User account is inactive.")

        return user

    def issue_tokens(self, db: Session, user: User) -> tuple[str, str, int]:
        access_token = create_access_token(user.id, self._roles(user))
        refresh_token, jti, expires_at = create_refresh_token(user.id)

        db.add(
            RefreshToken(
                user_id=user.id,
                token_jti=jti,
                token_hash=self._hash_refresh_token(refresh_token),
                expires_at=expires_at,
            )
        )
        db.flush()

        expires_in = int((expires_at - datetime.now(timezone.utc)).total_seconds())
        return access_token, refresh_token, max(expires_in, 1)

    def rotate_refresh_token(self, db: Session, token: str) -> tuple[str, str, int]:
        try:
            payload = decode_token(token, "refresh")
            user_id = int(payload["sub"])
            jti = payload["jti"]
        except (TokenError, ValueError, TypeError, KeyError) as exc:
            raise ValueError("Invalid refresh token.") from exc

        stored = db.scalar(
            select(RefreshToken)
            .where(RefreshToken.token_jti == jti)
            .with_for_update()
        )

        if not stored or stored.is_revoked:
            raise ValueError("Refresh token has been revoked.")

        if stored.token_hash != self._hash_refresh_token(token):
            raise ValueError("Refresh token mismatch.")

        if stored.expires_at <= datetime.now(timezone.utc):
            stored.is_revoked = True
            stored.revoked_at = datetime.now(timezone.utc)
            db.flush()
            raise ValueError("Refresh token has expired.")

        user = self.users.get_by_id(db, user_id)
        if not user or not user.is_active:
            raise ValueError("User is inactive or does not exist.")

        stored.is_revoked = True
        stored.revoked_at = datetime.now(timezone.utc)

        access_token, new_refresh, new_exp = self.issue_tokens(db, user)
        return access_token, new_refresh, new_exp

    def revoke_refresh_token(self, db: Session, token: str) -> None:
        try:
            payload = decode_token(token, "refresh")
            jti = payload["jti"]
        except (TokenError, KeyError):
            return

        stored = db.scalar(
            select(RefreshToken).where(RefreshToken.token_jti == jti)
        )

        if stored and not stored.is_revoked:
            stored.is_revoked = True
            stored.revoked_at = datetime.now(timezone.utc)
            db.flush()


auth_service = AuthenticationService(UserRepository())
