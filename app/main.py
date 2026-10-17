from fastapi import FastAPI, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.database import get_db, engine
from app.models import Base, Question, Categorization
from app.categories import CATEGORIES

app = FastAPI(title="Questions API", version="1.0.0")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"message": "Questions API funcionando", "endpoints": ["/questions", "/questions/{id}"]}


@app.get("/questions")
def list_questions(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    questions = db.query(Question).offset(skip).limit(limit).all()
    return questions


@app.get("/questions/{question_id}")
def get_question(question_id: int, db: Session = Depends(get_db)):
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        return {"error": "Pregunta no encontrada"}
    return question


@app.get("/questions/category/{category_name}")
def list_questions_by_category(
    category_name: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    results = (
        db.query(Question, Categorization)
        .join(Categorization, Categorization.question_id == Question.id)
        .filter(Categorization.category_name == category_name)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [
        {
            "id": question.id,
            "question": question.question,
            "answer": question.answer,
            "options": question.options,
            "source": question.source,
            "category_name": categorization.category_name,
            "confidence_score": categorization.confidence_score,
            "is_automatic": categorization.is_automatic,
        }
        for question, categorization in results
    ]


@app.get("/categories")
def list_categories():
    return CATEGORIES


@app.get("/categories/stats")
def category_stats(db: Session = Depends(get_db)):
    total_questions = db.query(Question).count()
    categorized = db.query(Categorization.question_id).distinct().count()
    uncategorized = total_questions - categorized
    automatic = db.query(Categorization).filter(Categorization.is_automatic == True).count()
    manual = db.query(Categorization).filter(Categorization.is_automatic == False).count()

    by_category = {}
    rows = (
        db.query(Categorization.category_name, func.count(Categorization.id))
        .group_by(Categorization.category_name)
        .all()
    )
    for name, count in rows:
        by_category[name] = count

    return {
        "total_questions": total_questions,
        "categorized": categorized,
        "uncategorized": uncategorized,
        "automatic": automatic,
        "manual": manual,
        "by_category": by_category,
    }