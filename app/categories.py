CATEGORIES = [
    {
        "name": "artes",
        "label": "Artes",
        "description": "Preguntas sobre pintura, escultura, literatura, poesía, arquitectura, teatro clásico, artistas y escritores.",
    },
    {
        "name": "ciencia",
        "label": "Ciencia",
        "description": "Preguntas sobre biología, física, química, matemáticas, astronomía, medicina, naturaleza, animales, inventos y descubrimientos científicos.",
    },
    {
        "name": "deportes",
        "label": "Deportes",
        "description": "Preguntas sobre fútbol, básquet, tenis, olimpiadas, atletas, equipos deportivos, reglas de juego y competencias.",
    },
    {
        "name": "entretenimiento",
        "label": "Entretenimiento",
        "description": "Preguntas sobre películas, series de televisión, música popular, actores, cantantes, celebridades, videojuegos y cultura pop.",
    },
    {
        "name": "geografia",
        "label": "Geografía",
        "description": "Preguntas sobre países, capitales, ríos, montañas, continentes, mapas y ubicaciones geográficas.",
    },
    {
        "name": "historia",
        "label": "Historia",
        "description": "Preguntas sobre hechos históricos, guerras, civilizaciones antiguas, personajes históricos, fechas importantes y eventos políticos del pasado.",
    },
]


def get_category_names():
    return [c["name"] for c in CATEGORIES]


def get_category_labels():
    return [c["label"] for c in CATEGORIES]


def get_category_descriptions():
    return [c["description"] for c in CATEGORIES]


def find_category_by_name(name):
    for c in CATEGORIES:
        if c["name"] == name:
            return c
    return None