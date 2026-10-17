"""Fixtures compartidas para todos los archivos de test.

Usan una base SQLite en memoria (no la Postgres real) con StaticPool: FastAPI
corre los endpoints síncronos en un hilo aparte, y sin StaticPool cada hilo
vería una base en memoria distinta y vacía.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, get_db
from app.models import Question


@pytest.fixture()
def db_session():
    """Motor SQLite en memoria, limpio en cada test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(db_session):
    """TestClient con la base de prueba ya conectada (sin datos)."""
    return TestClient(app)


@pytest.fixture()
def seeded_client(client, db_session):
    """TestClient con 2 preguntas de ejemplo ya cargadas."""
    db_session.add_all([
        Question(
            id=1,
            question="¿Cuál es la capital de Francia?",
            answer="París",
            category="geografía",
        ),
        Question(
            id=2,
            question="¿Quién escribió el Quijote?",
            answer="Miguel de Cervantes",
            category="literatura",
        ),
    ])
    db_session.commit()
    return client
