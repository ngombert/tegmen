"""Tools for Agent Gourmet."""

from typing import List, Optional

# Mock database of recipes for development
RECIPES_DB = [
    {
        "id": "1",
        "name": "Pâtes Carbonara",
        "ingredients": ["pâtes", "oeufs", "pecorino", "guanciale", "poivre"],
        "steps": [
            "Cuire les pâtes",
            "Mélanger oeufs et fromage",
            "Cuire guanciale",
            "Mélanger tout hors du feu",
        ],
        "tags": ["italien", "rapide", "pâtes"],
        "time_minutes": 20,
    },
    {
        "id": "2",
        "name": "Poulet Rôti",
        "ingredients": ["poulet", "beurre", "herbes", "pommes de terre"],
        "steps": ["Préchauffer four", "Beurrer poulet", "Rôtir 1h30"],
        "tags": ["familial", "dimanche", "poulet"],
        "time_minutes": 90,
    },
    {
        "id": "3",
        "name": "Salade César",
        "ingredients": ["laitue", "poulet", "croûtons", "parmesan", "sauce césar"],
        "steps": ["Laver salade", "Cuire poulet", "Assembler"],
        "tags": ["frais", "salade", "entrée"],
        "time_minutes": 15,
    },
    {
        "id": "4",
        "name": "Ratatouille",
        "ingredients": ["aubergine", "courgette", "poivron", "tomate", "oignon"],
        "steps": ["Couper légumes", "Mijoter doucement"],
        "tags": ["légumes", "végétarien", "été"],
        "time_minutes": 60,
    },
]


def search_recipes(query: str = "", tag: Optional[str] = None) -> List[dict]:
    """
    Rechercher des recettes par nom ou tag.

    Args:
        query: Terme de recherche (nom de recette ou ingrédient) - Optionnel
        tag: Filtrer par tag (ex: 'végétarien', 'italien') - Optionnel

    Returns:
        Liste de recettes correspondantes
    """
    results = []
    query = query.lower().strip()
    tag = tag.lower() if tag else None

    for recipe in RECIPES_DB:
        # Check tag matches if provided
        if tag and tag not in recipe["tags"]:
            continue

        # Check query matches name or ingredients
        # If query is empty, and we passed tag check, it's a match
        if not query:
            results.append(recipe)
            continue

        if query in recipe["name"].lower() or any(
            query in ing for ing in recipe["ingredients"]
        ):
            results.append(recipe)

    return results


def get_recipe_details(recipe_id: str) -> dict:
    """
    Obtenir les détails d'une recette par son ID.

    Args:
        recipe_id: Identifiant de la recette

    Returns:
        Détails complets de la recette ou message d'erreur
    """
    for recipe in RECIPES_DB:
        if recipe["id"] == recipe_id:
            return recipe
    return {"error": "Recette non trouvée"}
