import jwt
from jwt import InvalidTokenError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.db import settings


security = HTTPBearer(auto_error=False)

ROLE_PERMISSIONS = {
    "ADMIN": [
        "collection:read", "collection:create", "collection:update", "collection:delete", "collection:move",
        "conservation:read", "conservation:write", "conservation:update",
        "loans:read", "loans:write", "audit:read", "settings:manage",
    ],
    "CURATOR": ["collection:read", "collection:create", "collection:update", "collection:move", "conservation:read", "loans:read"],
    "CONSERVATOR": ["collection:read", "conservation:read", "conservation:write", "conservation:update"],
    "REGISTRAR": ["collection:read", "collection:create", "collection:update", "collection:move", "loans:read", "loans:write"],
    "RESEARCHER": ["collection:read", "conservation:read", "loans:read"],
    "VIEWER": ["collection:read"],
}

def resolve_permissions(roles: list[str]) -> set[str]:
    permissions = set()
    for role in roles:
        permissions.update(ROLE_PERMISSIONS.get(role.upper(), []))
    return permissions

def _decode_access_token(credentials: HTTPAuthorizationCredentials | None) -> dict:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type.")
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token.")

def require_permission(permission: str):
    def dependency(credentials: HTTPAuthorizationCredentials | None = Depends(security)) -> int:
        payload = _decode_access_token(credentials)
        user_roles = payload.get("roles", [])
        user_permissions = resolve_permissions(user_roles)
        
        if permission not in user_permissions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")
            
        return int(payload["sub"])
    return dependency

def get_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
):
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid access token.",
            )

        return (
            int(payload["sub"]),
            {str(role).upper() for role in payload.get("roles", [])},
        )
    except (InvalidTokenError, ValueError, KeyError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token.",
        )


def require_roles(*roles: str):
    accepted = {role.upper() for role in roles}

    def dependency(user=Depends(get_user)):
        user_id, user_roles = user

        if not accepted.intersection(user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )

        return user_id

    return dependency
