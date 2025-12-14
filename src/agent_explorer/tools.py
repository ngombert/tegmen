"""Tools for Agent Explorer."""

import json
import random


def search_destinations(criteria: str, budget: str = "medium") -> str:
    """Search for travel destinations based on criteria.

    Args:
        criteria: Search criteria (e.g., "sea", "mountains", "warm").
        budget: Budget level ("low", "medium", "high").

    Returns:
        A list of suggested destinations.
    """
    # Mock data
    destinations = [
        {"name": "Nice, France", "type": "sea", "weather": "sunny", "budget": "medium"},
        {
            "name": "Chamonix, France",
            "type": "mountains",
            "weather": "snowy",
            "budget": "high",
        },
        {
            "name": "Lisbonne, Portugal",
            "type": "city",
            "weather": "sunny",
            "budget": "medium",
        },
        {
            "name": "Bali, Indonésie",
            "type": "exotic",
            "weather": "humid",
            "budget": "low",
        },  # Relative to life cost there
        {
            "name": "Bretagne, France",
            "type": "nature",
            "weather": "cloudy",
            "budget": "medium",
        },
    ]

    results = []
    for dest in destinations:
        if criteria.lower() in dest["type"] or criteria.lower() in dest["name"].lower():
            if budget == "all" or dest["budget"] == budget:
                results.append(dest)

    # Fallback if empty
    if not results:
        results = [destinations[0], destinations[2]]

    return json.dumps(
        {"criteria": criteria, "budget": budget, "suggestions": results},
        ensure_ascii=False,
    )


def get_activities(location: str, type: str = "family") -> str:
    """Find activities in a specific location.

    Args:
        location: The location to search in.
        type: Type of activity ("family", "couple", "adventure").

    Returns:
        A list of suggested activities.
    """
    # Mock data
    activities_db = {
        "Nice": [
            "Promenade des Anglais",
            "Musée Matisse",
            "Parc de la Colline du Château",
        ],
        "Chamonix": ["Ski", "Randonnée", "Aiguille du Midi"],
        "Lisbonne": ["Tour de Belém", "Tram 28", "Océanarium"],
    }

    # Fuzzy match location
    found_activities = []
    found_location = location

    for key, acts in activities_db.items():
        if key.lower() in location.lower():
            found_activities = acts
            found_location = key
            break

    if not found_activities:
        found_activities = [
            "Visite du centre-ville",
            "Découverte culinaire",
            "Balade au parc",
        ]

    return json.dumps(
        {"location": found_location, "type": type, "activities": found_activities},
        ensure_ascii=False,
    )


def get_weather_forecast(location: str) -> str:
    """Get weather forecast for a location.

    Args:
        location: The location to check.

    Returns:
        Weather forecast.
    """
    # Mock data
    weathers = ["Ensoleillé", "Nuageux", "Pluvieux", "Orageux", "Neige"]
    temps = random.randint(10, 30)

    forecast = {
        "location": location,
        "condition": random.choice(weathers),
        "temperature": f"{temps}°C",
    }
    return json.dumps(forecast, ensure_ascii=False)
