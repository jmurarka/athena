import pytest
import os
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

# Force SQLite in-memory test database and test settings
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["DEV_MODE"] = "True"
os.environ["LLM_MODE"] = "mock"

from app.core.db import Base, engine, SessionLocal
from app.models.user import User
from app.main import app
from starlette.testclient import TestClient

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    test_uuid = "99999999-9999-9999-9999-999999999999"
    test_user = db.query(User).filter(User.id == test_uuid).first()
    if not test_user:
        test_user = User(
            id=test_uuid,
            email="testrunner@athena.local",
            name="TestRunner",
            auth_provider="supabase"
        )
        db.add(test_user)
        db.commit()
    db.close()
    yield

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
