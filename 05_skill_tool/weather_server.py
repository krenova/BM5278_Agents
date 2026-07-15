"""Local stdio MCP weather server backed by Open-Meteo."""

from __future__ import annotations

import json
import sys
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen


def parse_weather(geocoding: dict[str, Any], forecast: dict[str, Any]) -> str:
    """Convert canned or live API responses into a concise weather report."""
    if not geocoding.get("results"):
        return "I could not find that city."

    place = geocoding["results"][0]
    current = forecast.get("current", {})
    return (
        f"{place['name']}, {place.get('country', '')}: "
        f"{current.get('temperature_2m')}°C, "
        f"wind {current.get('wind_speed_10m')} km/h (current conditions)."
    )


def get_json(url: str) -> dict[str, Any]:
    """Fetch and decode a JSON response from Open-Meteo."""
    with urlopen(url, timeout=15) as response:
        return json.load(response)


def get_weather(city: str) -> str:
    """Get current temperature and wind for a city."""
    print(f"weather lookup: {city}", file=sys.stderr)
    geocoding = get_json(
        "https://geocoding-api.open-meteo.com/v1/search?" + urlencode({"name": city, "count": 1})
    )
    if not geocoding.get("results"):
        return "I could not find that city."

    place = geocoding["results"][0]
    forecast = get_json(
        "https://api.open-meteo.com/v1/forecast?"
        + urlencode(
            {
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "current": "temperature_2m,wind_speed_10m",
            }
        )
    )
    return parse_weather(geocoding, forecast)


if __name__ == "__main__":
    from mcp.server.fastmcp import FastMCP

    server = FastMCP("Local Weather")
    server.tool()(get_weather)
    server.run(transport="stdio")
