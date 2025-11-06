import requests
from google import genai

from config import base, weather, gemini
from prompts.gemini_prompts import system_prompt


def _get_location_coordinates(city_name):
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": city_name, "count": 1, "language": "en", "format": "json"}
    response = requests.get(url, params=params)
    data = response.json()

    if "results" in data and len(data["results"]) > 0:
        result = data["results"][0]
        return result["latitude"], result["longitude"]
    else:
        raise ValueError("City not found")

lat, lon = _get_location_coordinates("Tampa")
print(f"Tampa: lat={lat}, lon={lon}")

def get_weather_info(location: str, date: str) -> dict[str, any]:
    url = f"https://api.weatherapi.com/v1/forecast.json"
    params = {
        "key": weather.WEATHER_API_SECRET,
        "q": location,
        "days": 1,
        "aqi": "no",
        "alerts": "no"
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": "Unable to fetch weather information"}
