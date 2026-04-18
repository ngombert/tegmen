from typing import Dict, List, Optional
from pydantic import BaseModel

class UserProfile(BaseModel):
    user_id: str
    family_id: str
    name: str
    role: str # 'parent' or 'child'
    restrictions: List[str] = []
    preferences: Dict = {}

# Mock Database of user profiles
MOCK_PROFILES = {
    "user-parent-1": UserProfile(
        user_id="user-parent-1",
        family_id="test-family",
        name="Jean (Parent)",
        role="parent",
    ),
    "user-child-1": UserProfile(
        user_id="user-child-1",
        family_id="test-family",
        name="Léo (Enfant)",
        role="child",
        restrictions=["agent_explorer"] # Block travel agent
    )
}

def get_user_profile(user_id: str, family_id: str) -> Optional[UserProfile]:
    """
    Retrieve a user profile from the mock database.
    In a real app, this would query Postgres.
    """
    profile = MOCK_PROFILES.get(user_id)
    if profile and profile.family_id == family_id:
        return profile
    return None
