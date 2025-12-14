"""Unit tests for Agent Explorer."""

import pytest
import json
from src.agent_explorer.tools import (
    search_destinations,
    get_activities,
    get_weather_forecast,
)
from src.agent_explorer.agent import agent


def test_search_destinations_all():
    result = search_destinations(criteria="sea", budget="medium")
    data = json.loads(result)
    assert data["criteria"] == "sea"
    assert len(data["suggestions"]) > 0
    assert any("Nice" in d["name"] for d in data["suggestions"])


def test_get_activities_found():
    result = get_activities("Nice", type="family")
    data = json.loads(result)
    assert "Nice" in data["location"]
    assert len(data["activities"]) > 0


def test_get_activities_default():
    result = get_activities("Nowhere")
    data = json.loads(result)
    assert len(data["activities"]) > 0


def test_get_weather():
    result = get_weather_forecast("Paris")
    data = json.loads(result)
    assert data["location"] == "Paris"
    assert "condition" in data
    assert "temperature" in data


@pytest.mark.asyncio
async def test_agent_tool_registration():
    # Verify tools are registered
    assert len(agent.tools) == 3
    tool_names = [t.__name__ for t in agent.tools]
    assert "search_destinations" in tool_names
    assert "get_activities" in tool_names
    assert "get_weather_forecast" in tool_names
