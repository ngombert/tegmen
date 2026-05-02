from pydantic import BaseModel, ConfigDict, Field

class RecipeBase(BaseModel):
    """Basic recipe information for search results."""
    model_config = ConfigDict(strict=True)
    
    id: str
    name: str
    tags: list[str] = Field(default_factory=list)
    prep_time: int # in minutes

class Ingredient(BaseModel):
    """Structured ingredient information."""
    model_config = ConfigDict(strict=True)
    
    name: str
    quantity: str | None = None
    unit: str | None = None

class RecipeDetail(RecipeBase):
    """Full recipe details."""
    model_config = ConfigDict(strict=True)
    
    ingredients: list[Ingredient]
    steps: list[str]
    servings: int | None = None
    difficulty: str | None = None

class SearchRequest(BaseModel):
    """Request schema for recipe search."""
    model_config = ConfigDict(strict=True)
    
    query: str = ""
    tag: str | None = None

class SearchResponse(BaseModel):
    """Response schema for recipe search."""
    model_config = ConfigDict(strict=True)
    
    results: list[RecipeBase]
    total_count: int
