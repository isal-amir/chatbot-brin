import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys
import os

# Add backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app, JWT_SECRET
from core.database import Base, get_db
from models.user import User
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
from core.config import settings

# Setup in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@pytest.fixture(scope="session")
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(setup_db):
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Clean up data between tests
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def test_password():
    return "securepassword123"

@pytest.fixture
def student_user(db_session, test_password):
    hashed_pwd = pwd_context.hash(test_password)
    user = User(username="test_student", hashed_password=hashed_pwd, is_admin=False)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def admin_user(db_session, test_password):
    hashed_pwd = pwd_context.hash(test_password)
    user = User(username="test_admin", hashed_password=hashed_pwd, is_admin=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def student_token(student_user):
    expire = datetime.utcnow() + timedelta(days=1)
    return jwt.encode(
        {"sub": student_user.username, "exp": expire, "is_admin": student_user.is_admin},
        JWT_SECRET,
        algorithm="HS256"
    )

@pytest.fixture
def admin_token(admin_user):
    expire = datetime.utcnow() + timedelta(days=1)
    return jwt.encode(
        {"sub": admin_user.username, "exp": expire, "is_admin": admin_user.is_admin},
        JWT_SECRET,
        algorithm="HS256"
    )
