import pandas as pd
import requests
import tempfile
import os
import json
from app.database import SessionLocal, engine
from app.models import Base, Question

DATASET_URL = "https://huggingface.co/datasets/kth8/OpenTriviaQA/resolve/main/data/train-00000-of-00001.parquet"


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


def download_parquet(url: str) -> str:
    print(f"Descargando {url}...")
    r = requests.get(url, stream=True)
    r.raise_for_status()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".parquet")
    tmp.write(r.content)
    tmp.close()
    return tmp.name


def load_questions():
    Base.metadata.create_all(bind=engine)

    parquet_path = download_parquet(DATASET_URL)
    df = pd.read_parquet(parquet_path)
    os.unlink(parquet_path)

    print(f"Columnas disponibles: {list(df.columns)}")
    print(f"Filas: {len(df)}")
    print(df.head(3))

    session = SessionLocal()
    try:
        seen_questions = set()
        inserted = 0
        descartadas_duplicadas = 0
        descartadas_formato = 0

        for _, row in df.iterrows():
            question_text = row.get("question", "")
            if question_text in seen_questions:
                descartadas_duplicadas += 1
                continue

            choices = row.get("choices")
            if choices is None:
                descartadas_formato += 1
                continue

            opciones = [str(c).strip() for c in choices]
            respuesta = resolve_answer(row).strip()

            # Solo nos quedamos con preguntas de opción múltiple con
            # exactamente 4 alternativas, donde la respuesta correcta
            # esté efectivamente entre ellas.
            if len(opciones) != 4 or respuesta not in opciones:
                descartadas_formato += 1
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
            f"(de {len(df)} filas; se omitieron {descartadas_duplicadas} duplicadas "
            f"y {descartadas_formato} que no tenían exactamente 4 opciones válidas)."
        )
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    load_questions()