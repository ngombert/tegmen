from common.exceptions import A2ARPCError
from agent_gourmet.app.schemas.recipe import (
    RecipeBase,
    RecipeDetail,
    Ingredient,
    SearchRequest,
    SearchResponse,
)

# Mock database enriched for Pydantic strictness and domain requirements
RECIPES_DB: list[RecipeDetail] = [
    RecipeDetail(
        id="1",
        name="Pâtes Carbonara",
        ingredients=[
            Ingredient(name="pâtes", quantity="400", unit="g"),
            Ingredient(name="oeufs", quantity="4"),
            Ingredient(name="pecorino", quantity="100", unit="g"),
            Ingredient(name="guanciale", quantity="150", unit="g"),
            Ingredient(name="poivre", quantity="1", unit="c.à.s."),
        ],
        steps=[
            "Cuire les pâtes",
            "Mélanger oeufs et fromage",
            "Cuire guanciale",
            "Mélanger tout hors du feu",
        ],
        tags=["italien", "rapide", "pâtes"],
        prep_time=20,
        servings=4,
        difficulty="facile",
    ),
    RecipeDetail(
        id="2",
        name="Poulet Rôti",
        ingredients=[
            Ingredient(name="poulet", quantity="1.5", unit="kg"),
            Ingredient(name="beurre", quantity="50", unit="g"),
            Ingredient(name="herbes", quantity="1", unit="bouquet"),
            Ingredient(name="pommes de terre", quantity="1", unit="kg"),
        ],
        steps=["Préchauffer four", "Beurrer poulet", "Rôtir 1h30"],
        tags=["familial", "dimanche", "poulet"],
        prep_time=90,
        servings=6,
        difficulty="moyen",
    ),
    RecipeDetail(
        id="3",
        name="Salade César",
        ingredients=[
            Ingredient(name="laitue", quantity="1", unit="pièce"),
            Ingredient(name="poulet", quantity="200", unit="g"),
            Ingredient(name="croûtons", quantity="50", unit="g"),
            Ingredient(name="parmesan", quantity="30", unit="g"),
            Ingredient(name="sauce césar", quantity="4", unit="c.à.s."),
        ],
        steps=["Laver salade", "Cuire poulet", "Assembler"],
        tags=["frais", "salade", "entrée"],
        prep_time=15,
        servings=2,
        difficulty="facile",
    ),
    RecipeDetail(
        id="4",
        name="Ratatouille",
        ingredients=[
            Ingredient(name="aubergine", quantity="2"),
            Ingredient(name="courgette", quantity="3"),
            Ingredient(name="poivron", quantity="2"),
            Ingredient(name="tomate", quantity="5"),
            Ingredient(name="oignon", quantity="2"),
        ],
        steps=["Couper légumes", "Mijoter doucement"],
        tags=["légumes", "végétarien", "été"],
        prep_time=60,
        servings=4,
        difficulty="moyen",
    ),
]

class RecipeService:
    """Service handling recipe business logic."""

    async def search_recipes(self, request: SearchRequest) -> SearchResponse:
        """
        Search for recipes based on query and/or tag.
        
        Args:
            request: Search parameters
            
        Returns:
            Search results matching criteria
        """
        results: list[RecipeBase] = []
        query = request.query.lower().strip()
        tag = request.tag.lower().strip() if request.tag else None

        for recipe in RECIPES_DB:
            # Check tag filter
            if tag and tag not in [t.lower() for t in recipe.tags]:
                continue
            
            # Check query matches name or ingredients
            if not query:
                results.append(RecipeBase(**recipe.model_dump()))
                continue
            
            match_found = False
            if query in recipe.name.lower():
                match_found = True
            else:
                for ing in recipe.ingredients:
                    if query in ing.name.lower():
                        match_found = True
                        break
            
            if match_found:
                results.append(RecipeBase(**recipe.model_dump()))

        return SearchResponse(results=results, total_count=len(results))

    async def get_recipe_details(self, recipe_id: str) -> RecipeDetail:
        """
        Retrieve full details for a specific recipe.
        
        Args:
            recipe_id: Unique identifier of the recipe
            
        Returns:
            Complete recipe details
            
        Raises:
            A2ARPCError: If recipe is not found
        """
        for recipe in RECIPES_DB:
            if recipe.id == recipe_id:
                return recipe
        
        raise A2ARPCError(
            code=A2ARPCError.RECIPE_NOT_FOUND,
            message="Recette non trouvée",
            data={"recipe_id": recipe_id}
        )
