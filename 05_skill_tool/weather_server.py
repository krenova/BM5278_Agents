import json,sys
from urllib.parse import urlencode
from urllib.request import urlopen
def parse_weather(geo,forecast):
 if not geo.get('results'):return 'I could not find that city.'
 p=geo['results'][0];c=forecast.get('current',{});return f"{p['name']}, {p.get('country','')}: {c.get('temperature_2m')}°C, wind {c.get('wind_speed_10m')} km/h (current conditions)."
def get_json(url):
 with urlopen(url,timeout=15) as r:return json.load(r)
def get_weather(city:str)->str:
 '''Get current temperature and wind for a city.'''
 print(f'weather lookup: {city}',file=sys.stderr);g=get_json('https://geocoding-api.open-meteo.com/v1/search?'+urlencode({'name':city,'count':1}))
 if not g.get('results'):return 'I could not find that city.'
 p=g['results'][0];f=get_json('https://api.open-meteo.com/v1/forecast?'+urlencode({'latitude':p['latitude'],'longitude':p['longitude'],'current':'temperature_2m,wind_speed_10m'}));return parse_weather(g,f)
if __name__=='__main__':
 from mcp.server.fastmcp import FastMCP
 mcp=FastMCP('Local Weather');mcp.tool()(get_weather);mcp.run(transport='stdio')
