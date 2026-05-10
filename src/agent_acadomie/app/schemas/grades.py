from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
import uuid

class GradeItem(BaseModel):
    """Detailed grade information."""
    model_config = ConfigDict(strict=True, extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    subject: str
    grade: float
    max_grade: float = 20.0
    evaluation_name: str
    date: str
    student_id: str
    family_id: str

class UserIdentity(BaseModel):
    """User identity provided by Maestro."""
    model_config = ConfigDict(strict=True, extra="ignore")
    
    id: str
    role: str

class GradeRequest(BaseModel):
    """Request to retrieve grades."""
    model_config = ConfigDict(strict=True, extra="ignore")
    
    family_id: str
    student_id: str

class GradeResponse(BaseModel):
    """Response containing a list of grades."""
    model_config = ConfigDict(strict=True, extra="ignore")
    
    grades: List[GradeItem]
    average: Optional[float] = None
