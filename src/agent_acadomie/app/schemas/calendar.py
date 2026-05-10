from pydantic import BaseModel, ConfigDict, Field
from typing import List
import uuid

class CalendarEvent(BaseModel):
    """Detailed calendar event information."""
    model_config = ConfigDict(strict=True, extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    date: str
    description: str
    family_id: str

class CalendarRequest(BaseModel):
    """Request to retrieve calendar events."""
    model_config = ConfigDict(strict=True, extra="ignore")
    
    family_id: str
    # Possible filters could be added here (e.g., start_date, end_date)

class CalendarResponse(BaseModel):
    """Response containing a list of calendar events."""
    model_config = ConfigDict(strict=True, extra="ignore")
    
    events: List[CalendarEvent]
    total_count: int
