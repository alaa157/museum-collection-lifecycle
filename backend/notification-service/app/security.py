import jwt
from jwt import InvalidTokenError
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.db import settings


security = HTTPBearer(auto_error=False)


def current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
):
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required.")

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid access token.")
        return int(payload["sub"])
    except (InvalidTokenError, KeyError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid access token.")
