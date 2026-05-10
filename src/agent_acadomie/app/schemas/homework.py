from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
import uuid
from datetime import datetime

class HomeworkItem(BaseModel):
    """Detailed homework information."""
    model_config = ConfigDict(strict=True, extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    subject: str
    task: str
    due_date: str  # ISO format string or just descriptive
    completed: bool = False
    family_id: str

class HomeworkListRequest(BaseModel):
    """Request to list homework."""
    model_config = ConfigDict(strict=True, extra="ignore")
    
    family_id: str
    include_completed: bool = False

class HomeworkListResponse(BaseModel):
    """Response containing a list of homework."""
    model_config = ConfigDict(strict=True, extra="ignore")
    
    homeworks: List[HomeworkItem]
    total_count: int

class HomeworkAddRequest(BaseModel):
    """Request to add a new homework."""
    model_config = ConfigDict(strict=True, extra="ignore")
    
    family_id: str
    subject: str
    task: str
    due_date: str
