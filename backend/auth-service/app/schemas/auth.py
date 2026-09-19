from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=128,
    )


class RefreshRequest(BaseModel):
    refresh_token: str | None = Field(
        default=None,
        min_length=20,
    )


class LogoutRequest(BaseModel):
    refresh_token: str | None = Field(
        default=None,
        min_length=20,
    )


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class PermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    description: str | None = None


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    description: str | None = None
    permissions: list[PermissionResponse]


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    first_name: str
    last_name: str
    is_active: bool
    is_verified: bool
    roles: list[RoleResponse]


class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(
        min_length=12,
        max_length=128,
    )
    first_name: str = Field(
        min_length=1,
        max_length=100,
    )
    last_name: str = Field(
        min_length=1,
        max_length=100,
    )
    role_names: list[str] = Field(
        default_factory=list
    )


class UpdateUserStatusRequest(BaseModel):
    is_active: bool