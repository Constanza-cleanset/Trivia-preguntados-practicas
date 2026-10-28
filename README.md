# Trivia Preguntados — Práctica

API de preguntas de trivia construida con **FastAPI**, **SQLAlchemy** y **PostgreSQL**, con categorización automática de preguntas usando IA (*zero-shot classification*) y revisión humana (*Human-in-the-Loop*) para los casos de baja confianza.

Proyecto de Práctica Profesional II — CDIA.

## Requisitos

- Python 3.11+
- [Poetry](https://python-poetry.org/)
- Docker y Docker Compose

## Puesta en marcha

1. Clonar el repo e instalar las dependencias:

   ```bash
   poetry install
   ```

2. Copiar el archivo de variables de entorno de ejemplo:

   ```bash
   cp .env.example .env
   ```

   Por defecto apunta a la base de datos local que levanta `docker-compose.yml`. No hace falta tocar nada salvo que quieras usar otra configuración.

3. Levantar la base de datos (PostgreSQL):

   ```bash
   docker compose up -d
   ```

## Cargar las preguntas

Descarga el dataset de Hugging Face (OpenTriviaQA) y lo carga en la base:

```bash
poetry run python app/load_data.py
```

## Categorizar las preguntas con IA

Clasifica cada pregunta en una de las 6 categorías definidas en `app/categories.py`, usando un modelo de zero-shot classification (`facebook/bart-large-mnli`). Las preguntas con confianza ≥ 70% se categorizan automáticamente; por debajo de ese umbral, el script pide confirmación por consola.

```bash
poetry run python -m app.categorize
```

Para correrlo sin intervención humana (solo guarda las automáticas y deja las de baja confianza sin categorizar, para revisarlas después):

```bash
poetry run python -m app.categorize --auto-only
```

Por defecto procesa las preguntas en tandas de 16 para aprovechar mejor la GPU/CPU. Se puede ajustar con `--batch-size`:

```bash
poetry run python -m app.categorize --auto-only --batch-size 32
```

> Si alguien del equipo ya tiene un dump de la base con las preguntas categorizadas (por ejemplo para no esperar a que corra todo el proceso de nuevo), se puede restaurar con:
>
> ```bash
> docker compose cp archivo.dump db:/tmp/archivo.dump
> docker compose exec db pg_restore -U admin -d questions_db --clean --if-exists --no-owner -v /tmp/archivo.dump
> ```

## Levantar la API

```bash
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Documentación interactiva (Swagger UI): http://localhost:8000/docs

### Endpoints disponibles

| Endpoint | Descripción |
|---|---|
| `GET /` | Mensaje de bienvenida |
| `GET /questions` | Lista de preguntas (`skip`, `limit`) |
| `GET /questions/{id}` | Una pregunta por ID |
| `GET /questions/category/{category_name}` | Preguntas filtradas por categoría |
| `GET /categories` | Lista de categorías disponibles |
| `GET /categories/stats` | Estadísticas de categorización (total, automáticas, manuales, por categoría) |

## Tests

```bash
poetry run pytest
```

`tests/test_data_quality.py` corre contra la base real (necesita Docker levantado y datos ya cargados); el resto usa una base SQLite en memoria.
