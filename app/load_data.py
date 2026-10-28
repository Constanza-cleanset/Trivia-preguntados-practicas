import argparse
import json
import os
import tempfile

import pandas as pd
import requests
from ftfy import fix_text

from app.database import SessionLocal, engine
from app.models import Base, Categorization, Question

DATASET_URL = "https://huggingface.co/datasets/kth8/OpenTriviaQA/resolve/main/data/train-00000-of-00001.parquet"
DOWNLOAD_TIMEOUT = 60  # segundos


def resolve_answer(row) -> str:
    """Devuelve el texto de la respuesta. Soporta tanto un string directo
    como un dict estilo TriviaQA ({'value': ..., 'aliases': [...]})."""
    answer = row.get("answer", "")
    if isinstance(answer, dict):
        value = answer.get("value", "")
        if value:
            return value
        aliases = answer.get("aliases") or answer.get("normalized_aliases")
        if aliases:
            return aliases[0]
        return ""
    return answer or row.get("answer_alias", "") or ""


def is_disguised_true_false(opciones: list) -> bool:
    """Detecta preguntas de Verdadero/Falso que vienen disfrazadas de opción
    múltiple: alguna de sus 4 opciones es, literalmente, "True" o "False"."""
    normalizadas = {o.strip().lower() for o in opciones}
    return "true" in normalizadas or "false" in normalizadas


def download_parquet(url: str) -> str:
    print(f"Descargando {url}...")
    try:
        r = requests.get(url, stream=True, timeout=DOWNLOAD_TIMEOUT)
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise SystemExit(f"No se pudo descargar el dataset: {e}")
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".parquet")
    tmp.write(r.content)
    tmp.close()
    return tmp.name


def reset_database(session):
    """Borra todo lo cargado previamente (categorizaciones primero, por la
    foreign key, y después las preguntas) para poder recargar desde cero."""
    borradas_cat = session.query(Categorization).delete()
    borradas_q = session.query(Question).delete()
    session.commit()
    print(f"Se borraron {borradas_q} preguntas y {borradas_cat} categorizaciones existentes.")


def load_questions(reset: bool = False):
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()

    existing_count = session.query(Question).count()
    if existing_count > 0 and not reset:
        print(
            f"Ya hay {existing_count} preguntas cargadas. No se vuelve a cargar nada "
            "para no duplicar. Si querés recargar desde cero, corré con --reset."
        )
        session.close()
        return

    if existing_count > 0 and reset:
        reset_database(session)

    parquet_path = download_parquet(DATASET_URL)
    df = pd.read_parquet(parquet_path)
    os.unlink(parquet_path)

    print(f"Columnas disponibles: {list(df.columns)}")
    print(f"Filas: {len(df)}")
    print(df.head(3))

    try:
        seen_questions = set()
        inserted = 0
        descartadas_duplicadas = 0
        descartadas_formato = 0
        descartadas_vf = 0

        for _, row in df.iterrows():
            question_text = fix_text(row.get("question", "") or "")
            if question_text in seen_questions:
                descartadas_duplicadas += 1
                continue

            choices = row.get("choices")
            if choices is None:
                descartadas_formato += 1
                continue

            opciones = [fix_text(str(c).strip()) for c in choices]
            respuesta = fix_text(resolve_answer(row).strip())

            # Solo nos quedamos con preguntas de opción múltiple con
            # exactamente 4 alternativas, donde la respuesta correcta
            # esté efectivamente entre ellas.
            if len(opciones) != 4 or respuesta not in opciones:
                descartadas_formato += 1
                continue

            # Descartamos las de Verdadero/Falso disfrazadas de opción
            # múltiple (alguna opción es literalmente "True" o "False").
            if is_disguised_true_false(opciones):
                descartadas_vf += 1
                continue

            seen_questions.add(question_text)

            question = Question(
                question=question_text,
                answer=respuesta,
                category=None,
                source="OpenTriviaQA",
                options=json.dumps(opciones),
            )
            session.add(question)
            inserted += 1

        session.commit()
        print(
            f"Se insertaron {inserted} preguntas correctamente "
            f"(de {len(df)} filas; se omitieron {descartadas_duplicadas} duplicadas, "
            f"{descartadas_formato} sin 4 opciones válidas y {descartadas_vf} de "
            "Verdadero/Falso disfrazadas)."
        )
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
    finally:
        session.close()


def parse_args():
    parser = argparse.ArgumentParser(description="Carga las preguntas de OpenTriviaQA en la base de datos.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Borra las preguntas y categorizaciones existentes antes de recargar (si no se pasa y ya hay datos, no hace nada).",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    load_questions(reset=args.reset)
