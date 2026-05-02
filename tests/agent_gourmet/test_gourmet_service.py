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

@pytest.mark.asyncio
async def test_search_recipes_by_ingredient(service):
    request = SearchRequest(query="pecorino")
    response = await service.search_recipes(request)
    assert response.total_count >= 1
    assert any("carbonara" in r.name.lower() for r in response.results)

@pytest.mark.asyncio
async def test_search_recipes_empty_result(service):
    request = SearchRequest(query="xyzzy")
    response = await service.search_recipes(request)
    assert response.total_count == 0
    assert response.results == []

@pytest.mark.asyncio
async def test_search_recipes_combined(service):
    # 'poulet' is in 'Poulet Rôti' (tags: familial, dimanche, poulet) 
    # and 'Salade César' (tags: frais, salade, entrée)
    request = SearchRequest(query="poulet", tag="dimanche")
    response = await service.search_recipes(request)
    assert response.total_count == 1
    assert response.results[0].name == "Poulet Rôti"

@pytest.mark.asyncio
async def test_search_filters_tags(service):
    # Multiple tags (AND logic)
    request = SearchRequest(tags_include=["italien", "pâtes"])
    response = await service.search_recipes(request)
    assert response.total_count == 1
    assert response.results[0].name == "Pâtes Carbonara"

@pytest.mark.asyncio
async def test_search_filters_exclusions(service):
    # Exclude tags
    request = SearchRequest(query="poulet", tags_exclude=["familial"])
    response = await service.search_recipes(request)
    assert response.total_count == 1
    assert response.results[0].name == "Salade César"

    # Exclude ingredients
    # 'pâtes' is in Carbonara. 
    # Let's search all recipes but exclude those with 'pecorino' (Carbonara)
    request = SearchRequest(ingredients_exclude=["pecorino"])
    response = await service.search_recipes(request)
    assert response.total_count == 3 # All except Carbonara
    assert not any(r.name == "Pâtes Carbonara" for r in response.results)

@pytest.mark.asyncio
async def test_search_filters_prep_time(service):
    # Max prep time 20 mins
    request = SearchRequest(max_prep_time=20)
    response = await service.search_recipes(request)
    assert response.total_count == 2 # Carbonara (20) and Salade César (15)
    
@pytest.mark.asyncio
async def test_search_pagination(service):
    # Request all recipes but limit to 2
    request = SearchRequest(limit=2)
    response = await service.search_recipes(request)
    assert response.total_count == 4 # Total available matches
    assert len(response.results) == 2 # Paginated results
    
    # Check offset
    request = SearchRequest(limit=2, offset=2)
    response = await service.search_recipes(request)
    assert response.total_count == 4
    assert len(response.results) == 2
    # Carbonara(0), Poulet(1), César(2), Ratatouille(3)
    assert response.results[0].name == "Salade César"
