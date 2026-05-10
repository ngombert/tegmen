from pydantic import BaseModel, ConfigDict, Field

class HomeworkBase(BaseModel):
    """Basic homework information."""
    model_config = ConfigDict(strict=True, extra="ignore")
    
    id: str
    subject: str
    task: str
    due_date: str
