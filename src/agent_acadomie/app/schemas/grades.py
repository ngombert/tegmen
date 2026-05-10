from pydantic import BaseModel, ConfigDict

class GradeResponse(BaseModel):
    """Basic grade information."""
    model_config = ConfigDict(strict=True, extra="ignore")
    
    student_name: str
    subject: str
    grades: list[float]
