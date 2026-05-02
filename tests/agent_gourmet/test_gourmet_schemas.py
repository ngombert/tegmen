import pytest
from pydantic import ValidationError
from agent_gourmet.app.schemas.recipe import RecipeBase, Ingredient, RecipeDetail, SearchRequest, SearchResponse

def test_recipe_base_valid():
    data = {
        "id": "1",
        "name": "Test Recipe",
        "tags": ["test"],
        "prep_time": 30
    }
    recipe = RecipeBase(**data)
    assert recipe.id == "1"
    assert recipe.name == "Test Recipe"

def test_recipe_base_strict():
    data = {
        "id": 1, # Should fail if strict=True because id is str
        "name": "Test Recipe",
        "tags": ["test"],
        "prep_time": "30" # Should fail if strict=True because prep_time is int
    }
    with pytest.raises(ValidationError):
        RecipeBase(**data)

def test_ingredient_valid():
    ing = Ingredient(name="salt", quantity="1", unit="pinch")
    assert ing.name == "salt"
    assert ing.quantity == "1"

def test_recipe_detail_valid():
    data = {
        "id": "1",
        "name": "Test Recipe",
        "tags": ["test"],
        "prep_time": 30,
        "ingredients": [{"name": "salt"}],
        "steps": ["step 1"],
        "servings": 4,
        "difficulty": "easy"
    }
    detail = RecipeDetail(**data)
    assert len(detail.ingredients) == 1
    assert detail.ingredients[0].name == "salt"

def test_search_request_defaults():
    req = SearchRequest()
    assert req.query == ""
    assert req.tag is None

def test_search_response_valid():
    recipe = {
        "id": "1",
        "name": "Test Recipe",
        "tags": ["test"],
        "prep_time": 30
    }
    resp = SearchResponse(results=[recipe], total_count=1)
    assert resp.total_count == 1
    assert len(resp.results) == 1

def test_recipe_detail_request_valid():
    from agent_gourmet.app.schemas.recipe import RecipeDetailRequest
    req = RecipeDetailRequest(recipe_id="123")
    assert req.recipe_id == "123"

def test_recipe_detail_request_strict():
    from agent_gourmet.app.schemas.recipe import RecipeDetailRequest
    with pytest.raises(ValidationError):
        RecipeDetailRequest(recipe_id=123) # Should fail (strict str)

def test_recipe_detail_response_valid():
    from agent_gourmet.app.schemas.recipe import RecipeDetailResponse, RecipeDetail, Ingredient
    detail = RecipeDetail(
        id="1",
        name="Test",
        tags=["a"],
        prep_time=10,
        ingredients=[Ingredient(name="i")],
        steps=["s"]
    )
    resp = RecipeDetailResponse(recipe=detail)
    assert resp.recipe.id == "1"
