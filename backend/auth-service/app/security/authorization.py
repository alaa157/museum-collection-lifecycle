from collections.abc import Callable
from fastapi import Depends, HTTPException, status
from app.api.dependencies import get_current_user
from app.models.user import User


def require_roles(*required_roles: str) -> Callable:
    required = {role.upper() for role in required_roles}

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        user_roles = {role.name.upper() for role in current_user.roles}
        if not required.intersection(user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role permissions.",
            )
        return current_user

    return dependency


def require_permissions(*permissions: str) -> Callable:
    required = set(permissions)

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        available: set[str] = set()

        for role in current_user.roles:
            available.update(permission.code for permission in role.permissions)

        if not required.issubset(available):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )

        return current_user

    return dependency
