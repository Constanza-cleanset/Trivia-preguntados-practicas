from app.categories import CATEGORIES


def display_question_context(question_text: str, answer: str, result) -> None:
    """Muestra la pregunta, la respuesta correcta y la sugerencia de la IA con todos los puntajes."""
    print("\n" + "=" * 60)
    print(f"Pregunta: {question_text}")
    print(f"Respuesta: {answer}")
    print("-" * 60)
    print(f"Sugerencia de la IA: {result.category_name} (confianza: {result.confidence_score:.2%})")
    print("Todos los puntajes:")
    for name, score in sorted(result.all_scores.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {name}: {score:.2%}")
    print("=" * 60)


def confirm_ai_suggestion(category_name: str) -> bool:
    """Pregunta si se acepta la sugerencia de la IA. Devuelve True/False."""
    respuesta = input(f"¿Aceptás la categoría sugerida '{category_name}'? (s/n): ").strip().lower()
    return respuesta in ("s", "si", "sí", "y", "yes")


def ask_human_for_category():
    """Muestra la lista numerada de categorías y deja elegir una, o 0 para omitir.
    Devuelve el nombre (name) de la categoría elegida, o None si se omite."""
    print("\nElegí la categoría correcta:")
    for i, cat in enumerate(CATEGORIES, start=1):
        print(f"  {i}. {cat['label']}")
    print("  0. Omitir esta pregunta")

    while True:
        choice = input("Opción: ").strip()
        if choice == "0":
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(CATEGORIES):
            return CATEGORIES[int(choice) - 1]["name"]
        print("Opción inválida, intentá de nuevo.")