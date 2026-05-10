from pydantic import BaseModel, ConfigDict
from typing import Optional

class OrganizationRequest(BaseModel):
    """Request to generate organizational advice."""
    model_config = ConfigDict(strict=True, extra="ignore")
    
    family_id: str
    student_id: str
    question: Optional[str] = None

class OrganizationResponse(BaseModel):
    """Response containing organizational advice."""
    model_config = ConfigDict(strict=True, extra="ignore")
    
    advice: str
