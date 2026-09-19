from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.role import Role
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    CreateUserRequest,
    RoleResponse,
    UpdateUserStatusRequest,
    UserResponse,
)
from app.security.authorization import require_permissions
from app.services.user_service import user_service


router = APIRouter(prefix="/auth", tags=["users"])
repository = UserRepository()


@router.get(
    "/users",
    response_model=list[UserResponse],
)
def list_users(
    _current_user: User = Depends(
        require_permissions("users:read")
    ),
    db: Session = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    return repository.list(
        db,
        offset=offset,
        limit=limit,
    )


@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    payload: CreateUserRequest,
    _current_user: User = Depends(
        require_permissions("users:create")
    ),
    db: Session = Depends(get_db),
):
    try:
        user = user_service.create_user(
            db,
            email=str(payload.email),
            password=payload.password,
            first_name=payload.first_name,
            last_name=payload.last_name,
            role_names=payload.role_names,
        )

        db.commit()
        db.refresh(user)

        return user

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    _current_user: User = Depends(
        require_permissions("users:read")
    ),
    db: Session = Depends(get_db),
):
    user = repository.get_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    return user


@router.patch(
    "/users/{user_id}/status",
    response_model=UserResponse,
)
def update_status(
    user_id: int,
    payload: UpdateUserStatusRequest,
    current_user: User = Depends(
        require_permissions("users:update")
    ),
    db: Session = Depends(get_db),
):
    user = repository.get_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    if user.id == current_user.id and not payload.is_active:
        raise HTTPException(
            status_code=400,
            detail="You cannot deactivate your own account.",
        )

    user.is_active = payload.is_active

    db.commit()
    db.refresh(user)

    return user


@router.get(
    "/roles",
    response_model=list[RoleResponse],
)
def list_roles(
    _current_user: User = Depends(
        require_permissions("roles:read")
    ),
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(Role).order_by(Role.name)
    ).unique().all()


@router.patch(
    "/users/{user_id}/roles",
    response_model=UserResponse,
)
def update_user_roles(
    user_id: int,
    role_names: list[str],
    _current_user: User = Depends(
        require_permissions("roles:update")
    ),
    db: Session = Depends(get_db),
):
    user = repository.get_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    normalized_names = {
        role.upper().strip()
        for role in role_names
        if role.strip()
    }

    roles = list(
        db.scalars(
            select(Role).where(Role.name.in_(normalized_names))
        ).all()
    )

    found_names = {role.name for role in roles}

    if found_names != normalized_names:
        missing = normalized_names - found_names

        raise HTTPException(
            status_code=400,
            detail=f"Unknown roles: {', '.join(sorted(missing))}",
        )

    user.roles = roles

    db.commit()
    db.refresh(user)

    return user
