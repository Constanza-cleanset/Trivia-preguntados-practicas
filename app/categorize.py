import argparse
from datetime import datetime, timezone

from tqdm import tqdm

from app.database import SessionLocal, engine
from app.models import Base, Question, Categorization
from app.classifier import AIClassifier
from app.human_review import display_question_context, ask_human_for_category, confirm_ai_suggestion

CONFIDENCE_THRESHOLD = 0.70
DEFAULT_BATCH_SIZE = 16


def get_uncategorized_questions(db):
    """Devuelve las preguntas que todavía no tienen una fila en categorizations."""
    categorized_ids = db.query(Categorization.question_id).subquery()
    return db.query(Question).filter(Question.id.notin_(categorized_ids)).all()


def chunked(items, size):
    """Parte una lista en tandas de a `size` elementos."""
    for i in range(0, len(items), size):
        yield items[i:i + size]


def save_categorization(db, question_id: int, category_name: str, confidence_score: float, is_automatic: bool, commit: bool = True):
    categorization = Categorization(
        question_id=question_id,
        category_name=category_name,
        confidence_score=confidence_score,
        is_automatic=is_automatic,
        created_at=datetime.now(timezone.utc),
    )
    db.add(categorization)
    if commit:
        db.commit()


def categorize_all(auto_only: bool = False, batch_size: int = DEFAULT_BATCH_SIZE):
    """Categoriza las preguntas pendientes, mandándolas al clasificador en
    tandas de `batch_size` (en vez de una por una) para acelerar el proceso.

    Si auto_only=True, solo guarda las categorizaciones automáticas (confianza
    >= CONFIDENCE_THRESHOLD) y deja sin tocar las que quedan por debajo del
    umbral, para revisarlas a mano más adelante (no se muestra ningún prompt
    interactivo)."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    classifier = AIClassifier()

    total = 0
    automatic = 0
    manual = 0
    skipped = 0
    pendientes = 0

    try:
        questions = get_uncategorized_questions(db)
        print(f"Preguntas sin categorizar: {len(questions)}")
        print(f"Procesando en tandas de {batch_size} preguntas...")

        tandas = list(chunked(questions, batch_size))
        for tanda in tqdm(tandas, unit="tanda"):
            resultados = classifier.classify_batch([q.question for q in tanda])

            for question, result in zip(tanda, resultados):
                total += 1

                if result.confidence_score >= CONFIDENCE_THRESHOLD:
                    save_categorization(
                        db, question.id, result.category_name, result.confidence_score,
                        is_automatic=True, commit=False,
                    )
                    automatic += 1
                    continue

                if auto_only:
                    # Queda sin categorizar: se revisa a mano en otra corrida.
                    pendientes += 1
                    continue

                display_question_context(question.question, question.answer, result)

                if confirm_ai_suggestion(result.category_name):
                    save_categorization(
                        db, question.id, result.category_name, result.confidence_score,
                        is_automatic=False, commit=False,
                    )
                    manual += 1
                    continue

                chosen_name = ask_human_for_category()
                if chosen_name is None:
                    skipped += 1
                    continue

                save_categorization(
                    db, question.id, chosen_name, result.confidence_score,
                    is_automatic=False, commit=False,
                )
                manual += 1

            db.commit()  # Un solo commit por tanda, en vez de uno por pregunta.

    finally:
        db.close()

    print("\n" + "=" * 60)
    print("Resumen de categorización:")
    print(f"  Total procesadas: {total}")
    print(f"  Automáticas: {automatic}")
    print(f"  Manuales: {manual}")
    print(f"  Omitidas: {skipped}")
    if auto_only:
        print(f"  Pendientes (< {CONFIDENCE_THRESHOLD:.0%}, para después): {pendientes}")
    print("=" * 60)


def parse_args():
    parser = argparse.ArgumentParser(description="Categoriza las preguntas con IA (zero-shot) + revisión humana.")
    parser.add_argument(
        "--auto-only",
        action="store_true",
        help=(
            f"Solo guarda las categorizaciones automáticas (confianza >= {CONFIDENCE_THRESHOLD:.0%}) "
            "y deja las de baja confianza sin categorizar, para revisarlas después. "
            "No muestra prompts interactivos."
        ),
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Cantidad de preguntas por tanda enviadas al clasificador (default: {DEFAULT_BATCH_SIZE}).",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    categorize_all(auto_only=args.auto_only, batch_size=args.batch_size)