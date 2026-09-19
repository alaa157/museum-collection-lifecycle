from fastapi import HTTPException, status
from app.core.config import get_settings
import jwt
from jwt import InvalidTokenError
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


security = HTTPBearer(auto_error=False)
settings = get_settings()

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

def require_role(*roles: str):
    allowed = {role.upper() for role in roles}

    def dependency(
        credentials: HTTPAuthorizationCredentials | None = Depends(security),
    ) -> int:
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
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token.")
        except InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid access token.",
            )

        user_roles = {str(role).upper() for role in payload.get("roles", [])}

        if not user_roles.intersection(allowed):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )

        try:
            return int(payload["sub"])
        except (KeyError, TypeError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid access token.",
            )

    return dependency
