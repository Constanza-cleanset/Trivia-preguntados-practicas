"""Tests de validación: la API debe rechazar entradas inválidas o raras,
y responder algo razonable ante entradas en el límite (edge cases)."""


def test_list_questions_rejects_negative_skip(seeded_client):
    response = seeded_client.get("/questions?skip=-1")
    assert response.status_code == 422


def test_list_questions_rejects_invalid_limit(seeded_client):
    response = seeded_client.get("/questions?limit=0")
    assert response.status_code == 422

    response = seeded_client.get("/questions?limit=500")
    assert response.status_code == 422


def test_get_question_rejects_non_numeric_id(seeded_client):
    response = seeded_client.get("/questions/abc")
    assert response.status_code == 422


def test_get_question_accepts_negative_id_but_not_found(seeded_client):
    # FastAPI no limita el rango de un int en el path por defecto;
    # este test documenta que un id negativo no rompe la API, solo no encuentra nada.
    response = seeded_client.get("/questions/-1")
    assert response.status_code == 200
    assert response.json() == {"error": "Pregunta no encontrada"}


def test_get_question_very_large_id_does_not_crash(seeded_client):
    response = seeded_client.get("/questions/999999999")
    assert response.status_code == 200
    assert response.json() == {"error": "Pregunta no encontrada"}
