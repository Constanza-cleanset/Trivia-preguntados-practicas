from dataclasses import dataclass
from typing import List, Dict

from transformers import pipeline

from app.categories import get_category_names, get_category_descriptions


@dataclass
class ClassificationResult:
    category_name: str
    confidence_score: float
    all_scores: Dict[str, float]


class AIClassifier:
    def __init__(self, model_name: str = "facebook/bart-large-mnli"):
        self._pipeline = pipeline("zero-shot-classification", model=model_name)
        self._names = get_category_names()
        self._descriptions = get_category_descriptions()
        self._description_to_name = dict(zip(self._descriptions, self._names))

    def _build_result(self, raw_result: dict) -> ClassificationResult:
        all_scores = {
            self._description_to_name[label]: score
            for label, score in zip(raw_result["labels"], raw_result["scores"])
        }
        best_label = raw_result["labels"][0]
        best_score = raw_result["scores"][0]
        return ClassificationResult(
            category_name=self._description_to_name[best_label],
            confidence_score=best_score,
            all_scores=all_scores,
        )

    def classify(self, question_text: str) -> ClassificationResult:
        """Clasifica una sola pregunta."""
        raw_result = self._pipeline(question_text, candidate_labels=self._descriptions)
        return self._build_result(raw_result)

    def classify_batch(self, question_texts: List[str]) -> List[ClassificationResult]:
        """Clasifica varias preguntas de una vez (más eficiente que llamar classify() en un loop)."""
        raw_results = self._pipeline(question_texts, candidate_labels=self._descriptions)
        if isinstance(raw_results, dict):
            raw_results = [raw_results]
        return [self._build_result(r) for r in raw_results]