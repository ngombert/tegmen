"""Semantic Router for intent classification."""

from semantic_router import Route
from semantic_router.routers import SemanticRouter
from semantic_router.encoders import HuggingFaceEncoder

from src.common.config import config

# Initialize encoder with local model
encoder = HuggingFaceEncoder(name=config.EMBEDDING_MODEL)

# Define routes with training utterances
gourmet_route = Route(
    name="gourmet",
    utterances=[
        "Qu'est-ce qu'on mange ce soir ?",
        "Donne-moi une idée de recette",
        "Je cherche une recette de poulet",
        "Qu'est-ce qu'on peut cuisiner avec des légumes ?",
        "Propose-moi un menu pour la semaine",
        "Recette facile pour le dîner",
        "Idée de repas rapide",
        "Qu'est-ce qu'on prépare pour le déjeuner ?",
        "Menu équilibré pour enfants",
        "Dessert facile à faire",
        "Recette végétarienne",
        "Que faire avec du saumon ?",
        "Idée de goûter pour les enfants",
        "Recette sans gluten",
        "Plat familial",
        "Faire une liste de courses",
        "ingrédients pour les crêpes",
        "cuisine italienne",
        "repas de noël",
    ],
)

acadomie_route = Route(
    name="acadomie",
    utterances=[
        "Aide-moi avec mes devoirs",
        "Quand est la rentrée des classes ?",
        "Calendrier scolaire",
        "Exercice de mathématiques",
        "Révisions pour l'examen",
        "Aide aux devoirs de français",
        "Emploi du temps de l'école",
        "Dates des vacances scolaires",
        "Réunion parents-professeurs",
        "Sortie scolaire",
        "Note de contrôle",
        "Inscription à l'école",
        "Cours particuliers",
        "Aide pour un exposé",
        "Exercice de grammaire",
        "Prochaines vacances scolaires",
        "vacances de Pâques",
        "devoir de géographie",
    ],
)

explorer_route = Route(
    name="explorer",
    utterances=[
        "Où partir en vacances ?",
        "Idée de sortie ce week-end",
        "Destination voyage famille",
        "Activités à faire avec les enfants",
        "Parc d'attractions proche",
        "Randonnée familiale",
        "Voyage pas cher",
        "Hôtel famille",
        "Camping avec enfants",
        "Musée à visiter",
        "Zoo le plus proche",
        "Plage accessible en voiture",
        "Week-end en famille",
        "Activité plein air",
        "Réservation vacances",
        "Prix des billets d'avion",
        "vol pour le Japon",
        "réserver un hôtel à Nice",
        "partir à la mer",
        "Choix d'un hotel",
    ],
)

chitchat_route = Route(
    name="chitchat",
    utterances=[
        "Bonjour",
        "Salut",
        "Comment ça va ?",
        "Raconte-moi une blague",
        "Quelle est la météo ?",
        "Qui es-tu ?",
        "Tu t'appelles comment ?",
        "Merci",
        "Au revoir",
        "Quelle est la capitale de la France ?",
        "Parle-moi de toi",
        "Bonne nuit",
    ],
)

# Create semantic router with auto sync
routes = [gourmet_route, acadomie_route, explorer_route, chitchat_route]
router = SemanticRouter(encoder=encoder, routes=routes, auto_sync="local")


def classify_intent(message: str) -> str:
    """
    Classify user intent using semantic similarity.

    Args:
        message: User message to classify

    Returns:
        Route name: 'gourmet', 'acadomie', 'explorer', or 'unknown'
    """
    result = router(message)
    if result.name is None:
        return "unknown"
    return result.name


# Warm up the router (load model) at import time
def warmup() -> None:
    """Pre-load the embedding model to avoid cold start latency."""
    _ = classify_intent("test")
