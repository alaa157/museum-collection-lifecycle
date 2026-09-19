from collections.abc import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.role import Permission, Role
from app.models.user import User
from app.security.passwords import hash_password


TEST_DATABASE_URL = "sqlite:///./test_auth.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db() -> Generator[Session, None, None]:
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture()
def client(db: Session):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture()
def admin_user(db: Session):
    permission = Permission(
        code="users:read",
        description="Read users",
    )
    role = Role(
        name="ADMIN_TEST",
        description="Test administrator",
        permissions=[permission],
    )
    user = User(
        email="admin@test.local",
        password_hash=hash_password("AdminPassword123!"),
        first_name="Test",
        last_name="Admin",
        is_active=True,
        roles=[role],
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
