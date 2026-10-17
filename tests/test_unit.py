"""Tests unitarios: funciones aisladas, sin red ni base de datos real (todo con mocks)."""
from unittest.mock import patch, MagicMock
import os
import pytest

from app.models import Question
from app.database import get_db
from app.load_data import download_parquet, resolve_answer


def test_question_model_stores_fields_in_memory():
    q = Question(question="¿Capital de Italia?", answer="Roma", category="geografía", source="test")
    assert q.question == "¿Capital de Italia?"
    assert q.answer == "Roma"
    assert q.category == "geografía"


def test_resolve_answer_prefers_answer_field():
    assert resolve_answer({"answer": "París", "answer_alias": "Paris, Francia"}) == "París"


def test_resolve_answer_falls_back_to_alias_when_answer_empty():
    assert resolve_answer({"answer": "", "answer_alias": "Paris, Francia"}) == "Paris, Francia"


def test_resolve_answer_returns_empty_string_when_both_missing():
    assert resolve_answer({}) == ""


@patch("app.load_data.requests.get")
def test_download_parquet_writes_response_content_to_temp_file(mock_get):
    mock_response = MagicMock()
    mock_response.content = b"contenido-parquet-falso"
    mock_get.return_value = mock_response

    path = download_parquet("https://ejemplo.com/data.parquet")

    mock_get.assert_called_once_with("https://ejemplo.com/data.parquet", stream=True)
    with open(path, "rb") as f:
        assert f.read() == b"contenido-parquet-falso"
    os.unlink(path)


@patch("app.load_data.requests.get")
def test_download_parquet_raises_on_http_error(mock_get):
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = Exception("HTTP 404")
    mock_get.return_value = mock_response

    with pytest.raises(Exception, match="404"):
        download_parquet("https://ejemplo.com/no-existe.parquet")


@patch("app.database.SessionLocal")
def test_get_db_closes_session_after_use(mock_session_local):
    mock_session = MagicMock()
    mock_session_local.return_value = mock_session

    gen = get_db()
    db = next(gen)
    assert db is mock_session
    mock_session.close.assert_not_called()

    with pytest.raises(StopIteration):
        next(gen)
    mock_session.close.assert_called_once()
