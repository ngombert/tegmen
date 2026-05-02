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
        Search for recipes based on multiple filters and pagination.
        
        Args:
            request: Search parameters and filters
            
        Returns:
            Paginated search results matching all criteria
        """
        matches: list[RecipeBase] = []
        query = request.query.lower().strip()
        
        # Normalize filter inputs
        tags_inc = [t.lower() for t in request.tags_include] if request.tags_include else []
        if request.tag: # Backward compatibility
            tags_inc.append(request.tag.lower())
            
        tags_exc = [t.lower() for t in request.tags_exclude] if request.tags_exclude else []
        ing_exc = [i.lower() for i in request.ingredients_exclude] if request.ingredients_exclude else []

        for recipe in RECIPES_DB:
            # 1. Filter by prep time
            if request.max_prep_time and recipe.prep_time > request.max_prep_time:
                continue
                
            # 2. Filter by tags_include (ALL must be present)
            if tags_inc:
                recipe_tags = [t.lower() for t in recipe.tags]
                if not all(t in recipe_tags for t in tags_inc):
                    continue
            
            # 3. Filter by tags_exclude (NONE must be present)
            if tags_exc:
                recipe_tags = [t.lower() for t in recipe.tags]
                if any(t in recipe_tags for t in tags_exc):
                    continue
            
            # 4. Filter by ingredients_exclude
            if ing_exc:
                recipe_ing_names = [i.name.lower() for i in recipe.ingredients]
                excluded_found = False
                for excluded_ing in ing_exc:
                    if any(excluded_ing in ri for ri in recipe_ing_names):
                        excluded_found = True
                        break
                if excluded_found:
                    continue
            
            # 5. Filter by query (matches name OR any ingredient)
            if query:
                match_found = query in recipe.name.lower()
                if not match_found:
                    for ing in recipe.ingredients:
                        if query in ing.name.lower():
                            match_found = True
                            break
                if not match_found:
                    continue
            
            # If we reached here, the recipe matches all criteria
            matches.append(RecipeBase(**recipe.model_dump()))

        total_count = len(matches)
        
        # Apply pagination
        results = matches[request.offset : request.offset + request.limit]
        
        return SearchResponse(results=results, total_count=total_count)

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
