"""Tests de calidad de datos: corren contra la base real (Postgres).
Necesitan Docker levantado y datos ya cargados (docker compose up -d +
poetry run python app/load_data.py)."""
import pytest
from sqlalchemy import func

from app.database import SessionLocal
from app.models import Question


@pytest.fixture(scope="module")
def real_db():
    db = SessionLocal()
    yield db
    db.close()


def test_there_are_questions_loaded(real_db):
    count = real_db.query(Question).count()
    assert count > 0, "No hay preguntas cargadas. ¿Corriste load_data.py?"


def test_no_questions_with_empty_text(real_db):
    empty = real_db.query(Question).filter(
        (Question.question == None) | (Question.question == "")
    ).count()
    assert empty == 0


def test_no_answers_with_empty_text(real_db):
    empty = real_db.query(Question).filter(
        (Question.answer == None) | (Question.answer == "")
    ).count()
    assert empty == 0


def test_no_duplicate_questions(real_db):
    duplicates = (
        real_db.query(Question.question, func.count(Question.id))
        .group_by(Question.question)
        .having(func.count(Question.id) > 1)
        .all()
    )
    assert len(duplicates) == 0, f"Hay {len(duplicates)} preguntas duplicadas"


def test_category_values_are_not_blank(real_db):
    categories = real_db.query(Question.category).distinct().all()
    for (cat,) in categories:
        if cat is not None:
            assert cat.strip() != "", "Hay una categoría que son solo espacios en blanco"
