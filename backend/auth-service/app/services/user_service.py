from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.role import Role
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.security.passwords import hash_password


class UserService:
    def __init__(self, users: UserRepository):
        self.users = users

    def create_user(
        self,
        db: Session,
        *,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        role_names: list[str],
    ) -> User:
        normalized_email = email.lower().strip()

        if self.users.get_by_email(db, normalized_email):
            raise ValueError("A user with this email already exists.")

        roles: list[Role] = []
        for role_name in role_names:
            role = db.scalar(
                select(Role).where(Role.name == role_name.upper())
            )
            if not role:
                raise ValueError(f"Unknown role: {role_name}")
            roles.append(role)

        user = User(
            email=normalized_email,
            password_hash=hash_password(password),
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            roles=roles,
        )
        self.users.add(db, user)
        return user


user_service = UserService(UserRepository())
