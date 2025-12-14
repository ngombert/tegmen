"""Unit tests for Agent Acadomie."""

import pytest
from src.agent_acadomie.tools import (
    get_school_calendar,
    get_student_grades,
    get_homework,
)
from src.agent_acadomie.agent import agent
import json


def test_get_school_calendar():
    result = get_school_calendar("Alice")
    data = json.loads(result)
    assert data["student"] == "Alice"
    assert "upcoming_events" in data
    assert len(data["upcoming_events"]) > 0


def test_get_student_grades_all():
    result = get_student_grades("Bob")
    data = json.loads(result)
    assert data["student"] == "Bob"
    assert "grades" in data
    assert "Mathématiques" in data["grades"]


def test_get_student_grades_specific():
    result = get_student_grades("Charlie", subject="Math")
    data = json.loads(result)
    assert "grades" in data
    assert "Mathématiques" in data["grades"]
    assert "Français" not in data["grades"]


def test_get_homework():
    result = get_homework("David")
    data = json.loads(result)
    assert data["student"] == "David"
    assert "homework" in data
    assert len(data["homework"]) > 0


@pytest.mark.asyncio
async def test_agent_tool_registration():
    # Verify tools are registered
    assert len(agent.tools) == 3
    tool_names = [t.__name__ for t in agent.tools]
    assert "get_school_calendar" in tool_names
    assert "get_student_grades" in tool_names
    assert "get_homework" in tool_names
