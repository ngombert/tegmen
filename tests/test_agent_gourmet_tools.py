from src.agent_gourmet.tools import search_recipes, get_recipe_details


def test_search_recipes_all():
    """Test searching with no query returns all results (subject to tag filter if any, or just first few if implied by logic)."""
    # implementation: if not query -> results.append(recipe) unless tag mismatch
    results = search_recipes()
    # Based on RECIPES_DB in tools.py, there are 4 recipes
    assert len(results) == 4


def test_search_recipes_query_match():
    """Test searching by name."""
    results = search_recipes("carbonara")
    assert len(results) == 1
    assert results[0]["name"] == "Pâtes Carbonara"


def test_search_recipes_ingredient_match():
    """Test searching by ingredient."""
    # "pommes de terre" is in Poulet Rôti
    results = search_recipes("pommes de terre")
    assert len(results) == 1
    assert results[0]["name"] == "Poulet Rôti"


def test_search_recipes_tag_filter():
    """Test filtering by tag."""
    results = search_recipes(tag="végétarien")
    # Ratatouille has tag 'végétarien'
    assert len(results) == 1
    assert results[0]["name"] == "Ratatouille"


def test_search_recipes_query_and_tag():
    """Test query and tag combination."""
    # 'légumes' tag + 'courgette' ingredient -> Ratatouille
    results = search_recipes("courgette", tag="légumes")
    assert len(results) == 1
    assert results[0]["name"] == "Ratatouille"


def test_search_recipes_no_results():
    """Test search with no matches."""
    results = search_recipes("pizza")
    assert len(results) == 0


def test_get_recipe_details_found():
    """Test getting existing recipe details."""
    details = get_recipe_details("1")
    assert details["name"] == "Pâtes Carbonara"
    assert "ingredients" in details


def test_get_recipe_details_not_found():
    """Test getting non-existent recipe."""
    details = get_recipe_details("999")
    assert "error" in details
    assert details["error"] == "Recette non trouvée"
