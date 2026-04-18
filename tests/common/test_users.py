import pytest
from common.users import get_user_profile

def test_get_parent_profile():
    profile = get_user_profile("user-parent-1", "test-family")
    assert profile is not None
    assert profile.role == "parent"
    assert profile.name == "Jean (Parent)"

def test_get_child_profile():
    profile = get_user_profile("user-child-1", "test-family")
    assert profile is not None
    assert profile.role == "child"
    assert "agent_explorer" in profile.restrictions

def test_get_non_existent_profile():
    profile = get_user_profile("ghost", "test-family")
    assert profile is None

def test_get_profile_wrong_family():
    profile = get_user_profile("user-parent-1", "wrong-family")
    assert profile is None
