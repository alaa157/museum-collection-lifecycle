from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.user import User


class UserRepository:
    def get_by_id(self, db: Session, user_id: int) -> User | None:
        return db.get(User, user_id)

    def get_by_email(self, db: Session, email: str) -> User | None:
        statement = select(User).where(User.email == email.lower())
        return db.scalar(statement)

    def list(self, db: Session, offset: int = 0, limit: int = 100) -> list[User]:
        statement = (
            select(User)
            .order_by(User.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(db.scalars(statement).unique().all())

    def add(self, db: Session, user: User) -> User:
        db.add(user)
        db.flush()
        return user
