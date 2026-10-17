"""Tests de integración: la API + la base de datos (de prueba) funcionando juntas."""


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Questions API funcionando",
        "endpoints": ["/questions", "/questions/{id}"]
    }


def test_list_questions_default_pagination(seeded_client):
    response = seeded_client.get("/questions")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["question"] == "¿Cuál es la capital de Francia?"


def test_list_questions_respects_skip_and_limit(seeded_client):
    response = seeded_client.get("/questions?skip=1&limit=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == 2


def test_get_question_found(seeded_client):
    response = seeded_client.get("/questions/1")
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "París"
    assert data["category"] == "geografía"


def test_get_question_not_found(seeded_client):
    response = seeded_client.get("/questions/999")
    # Nota: la API actual devuelve 200 con un JSON de error en vez de un 404.
    # Es una decisión de la guía del profesor, no un bug de este test.
    assert response.status_code == 200
    assert response.json() == {"error": "Pregunta no encontrada"}
