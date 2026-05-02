import pytest
from agent_gourmet.app.services.recipe_service import RecipeService
from agent_gourmet.app.schemas.recipe import SearchRequest, SearchResponse, RecipeDetail
from common.exceptions import A2ARPCError

@pytest.fixture
def service():
    return RecipeService()

@pytest.mark.asyncio
async def test_search_recipes_all(service):
    request = SearchRequest(query="")
    response = await service.search_recipes(request)
    assert isinstance(response, SearchResponse)
    assert response.total_count == 4
    assert len(response.results) == 4

@pytest.mark.asyncio
async def test_search_recipes_query(service):
    request = SearchRequest(query="carbonara")
    response = await service.search_recipes(request)
    assert response.total_count == 1
    assert response.results[0].name == "Pâtes Carbonara"

@pytest.mark.asyncio
async def test_search_recipes_tag(service):
    request = SearchRequest(tag="végétarien")
    response = await service.search_recipes(request)
    assert response.total_count == 1
    assert response.results[0].name == "Ratatouille"

@pytest.mark.asyncio
async def test_get_recipe_details_success(service):
    detail = await service.get_recipe_details("1")
    assert isinstance(detail, RecipeDetail)
    assert detail.name == "Pâtes Carbonara"
    assert len(detail.ingredients) > 0
    assert detail.difficulty == "facile"

@pytest.mark.asyncio
async def test_get_recipe_details_not_found(service):
    with pytest.raises(A2ARPCError) as excinfo:
        await service.get_recipe_details("999")
    assert excinfo.value.code == A2ARPCError.RECIPE_NOT_FOUND
