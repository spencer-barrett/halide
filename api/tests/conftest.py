import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from halide_api.config import settings
from fastapi.testclient import TestClient
from halide_api.db import get_db
from halide_api.main import app

assert settings.database_test != settings.database_url_pooled
engine = create_engine(settings.database_test, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)

@pytest.fixture
def session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.execute(text("TRUNCATE assets, batches CASCADE"))
        db.commit()
        db.close()
        
@pytest.fixture
def client(session: Session):
    app.dependency_overrides[get_db] = lambda: session
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()