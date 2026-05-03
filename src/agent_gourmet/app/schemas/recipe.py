from pydantic import BaseModel, ConfigDict, Field

class RecipeBase(BaseModel):
    """Basic recipe information for search results."""
    model_config = ConfigDict(strict=True, extra="ignore")
    
    id: str
    name: str
    tags: list[str] = Field(default_factory=list)
    prep_time: int # in minutes

class Ingredient(BaseModel):
    """Structured ingredient information."""
    model_config = ConfigDict(strict=True, extra="ignore")
    
    name: str
    quantity: str | None = None
    unit: str | None = None

class RecipeDetail(RecipeBase):
    """Full recipe details."""
    model_config = ConfigDict(strict=True, extra="ignore")
    
    ingredients: list[Ingredient]
    steps: list[str]
    servings: int | None = None
    difficulty: str | None = None

class SearchRequest(BaseModel):
    """Request schema for recipe search."""
    model_config = ConfigDict(strict=True, extra="ignore")
    
    query: str = ""
    tag: str | None = None # legacy, tags_include preferred
    tags_include: list[str] | None = None
    tags_exclude: list[str] | None = None
    ingredients_exclude: list[str] | None = None
    max_prep_time: int | None = None
    limit: int = 10
    offset: int = 0

class SearchResponse(BaseModel):
    """Response schema for recipe search."""
    model_config = ConfigDict(strict=True, extra="ignore")
    
    results: list[RecipeBase]
    total_count: int

class RecipeDetailRequest(BaseModel):
    """
    Request schema to retrieve full details of a single recipe.
    
    Attributes:
        recipe_id: The unique string identifier of the recipe to retrieve.
    """
    model_config = ConfigDict(strict=True, extra="ignore")
    
    recipe_id: str

class RecipeDetailResponse(BaseModel):
    """
    Response schema containing the complete details of the requested recipe.
    
    Attributes:
        recipe: The full RecipeDetail object containing ingredients, steps, and metadata.
    """
    model_config = ConfigDict(strict=True, extra="ignore")
    
    recipe: RecipeDetail
