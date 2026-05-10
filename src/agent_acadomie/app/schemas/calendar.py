from pydantic import BaseModel, ConfigDict

class CalendarEvent(BaseModel):
    """Basic calendar event information."""
    model_config = ConfigDict(strict=True, extra="ignore")
    
    id: str
    date: str
    event: str
