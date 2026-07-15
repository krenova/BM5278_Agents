"""A stdio MCP server. Never print diagnostics to stdout: it carries JSON-RPC."""
from __future__ import annotations
import json, sys
from urllib.parse import urlencode
from urllib.request import urlopen

def parse_weather(geocoding: dict, forecast: dict) -> str:
    if not geocoding.get('results'): return 'I could not find that city.'
    place=geocoding['results'][0]; current=forecast.get('current', {})
    return f"{place['name']}, {place.get('country', '')}: {current.get('temperature_2m')}°C, wind {current.get('wind_speed_10m')} km/h (current conditions)."

def get_json(url: str) -> dict:
    with urlopen(url, timeout=15) as response:
        return json.load(response)

def get_weather(city: str) -> str:
    """Get current temperature and wind for a city."""
    print(f'weather lookup: {city}', file=sys.stderr)
    geo=get_json('https://geocoding-api.open-meteo.com/v1/search?'+urlencode({'name':city,'count':1}))
    if not geo.get('results'): return 'I could not find that city.'
    place=geo['results'][0]
    forecast=get_json('https://api.open-meteo.com/v1/forecast?'+urlencode({'latitude':place['latitude'],'longitude':place['longitude'],'current':'temperature_2m,wind_speed_10m'}))
    return parse_weather(geo, forecast)

if __name__ == '__main__':
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP('Local Weather')
    mcp.tool()(get_weather)
    mcp.run(transport='stdio')
