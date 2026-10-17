from datetime import datetime, timezone

from app.database import SessionLocal, engine
from app.models import Base, Question, Categorization
from app.classifier import AIClassifier
from app.human_review import display_question_context, ask_human_for_category, confirm_ai_suggestion

CONFIDENCE_THRESHOLD = 0.70


def get_uncategorized_questions(db):
    """Devuelve las preguntas que todavía no tienen una fila en categorizations."""
    categorized_ids = db.query(Categorization.question_id).subquery()
    return db.query(Question).filter(Question.id.notin_(categorized_ids)).all()


def save_categorization(db, question_id: int, category_name: str, confidence_score: float, is_automatic: bool):
    categorization = Categorization(
        question_id=question_id,
        category_name=category_name,
        confidence_score=confidence_score,
        is_automatic=is_automatic,
        created_at=datetime.now(timezone.utc),
    )
    db.add(categorization)
    db.commit()


def categorize_all():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    classifier = AIClassifier()

    total = 0
    automatic = 0
    manual = 0
    skipped = 0

    try:
        questions = get_uncategorized_questions(db)
        print(f"Preguntas sin categorizar: {len(questions)}")

        for question in questions:
            total += 1
            result = classifier.classify(question.question)

            if result.confidence_score >= CONFIDENCE_THRESHOLD:
                save_categorization(db, question.id, result.category_name, result.confidence_score, is_automatic=True)
                automatic += 1
                continue

            display_question_context(question.question, question.answer, result)

            if confirm_ai_suggestion(result.category_name):
                save_categorization(db, question.id, result.category_name, result.confidence_score, is_automatic=False)
                manual += 1
                continue

            chosen_name = ask_human_for_category()
            if chosen_name is None:
                skipped += 1
                continue

            save_categorization(db, question.id, chosen_name, result.confidence_score, is_automatic=False)
            manual += 1

    finally:
        db.close()

    print("\n" + "=" * 60)
    print("Resumen de categorización:")
    print(f"  Total procesadas: {total}")
    print(f"  Automáticas: {automatic}")
    print(f"  Manuales: {manual}")
    print(f"  Omitidas: {skipped}")
    print("=" * 60)


if __name__ == "__main__":
    categorize_all()