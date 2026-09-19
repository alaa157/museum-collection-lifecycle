from fastapi import (
    APIRouter,
    Cookie,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)

from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.config import get_settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import auth_service


router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)

settings = get_settings()

REFRESH_COOKIE_NAME = "museum_refresh_token"


def _set_refresh_cookie(
    response: Response,
    refresh_token: str,
) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=getattr(
            settings,
            "auth_cookie_secure",
            False,
        ),
        samesite="lax",
        path="/api/v1/auth",
        max_age=30 * 24 * 60 * 60,
    )


def _clear_refresh_cookie(
    response: Response,
) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path="/api/v1/auth",
    )


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    payload: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    try:
        user = auth_service.authenticate(
            db,
            payload.email,
            payload.password,
        )

        access_token, refresh_token, expires_in = (
            auth_service.issue_tokens(db, user)
        )

        db.commit()

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )

    _set_refresh_cookie(
        response,
        refresh_token,
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
)
def refresh(
    response: Response,
    payload: RefreshRequest | None = None,
    museum_refresh_token: str | None = Cookie(
        default=None,
        alias=REFRESH_COOKIE_NAME,
    ),
    db: Session = Depends(get_db),
):
    token = (
        museum_refresh_token
        or (payload.refresh_token if payload else None)
    )

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is required.",
        )

    try:
        access_token, refresh_token, expires_in = (
            auth_service.rotate_refresh_token(
                db,
                token,
            )
        )

        db.commit()

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )

    _set_refresh_cookie(
        response,
        refresh_token,
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
def logout(
    response: Response,
    payload: LogoutRequest | None = None,
    museum_refresh_token: str | None = Cookie(
        default=None,
        alias=REFRESH_COOKIE_NAME,
    ),
    db: Session = Depends(get_db),
):
    token = (
        museum_refresh_token
        or (payload.refresh_token if payload else None)
    )

    if token:
        auth_service.revoke_refresh_token(
            db,
            token,
        )
        db.commit()

    _clear_refresh_cookie(response)

    return None


@router.get(
    "/me",
    response_model=UserResponse,
)
def me(
    current_user: User = Depends(get_current_user),
):
    return current_user