# Weather API utilities with LangChain tools
import os
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv()


class WeatherAPI:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("WEATHER_STACK_API")
        self.base_url = "http://api.weatherstack.com/current"

    def get_current_weather(self, query: str, units: str = "m", language: str = "en") -> Dict[str, Any]:
        """Get current weather for a location."""
        params = {
            "access_key": self.api_key,
            "query": query,
            "units": units,
            "language": language
        }
        response = requests.get(self.base_url, params=params)
        response.raise_for_status()
        return response.json()


def get_weather_tool(query: str, units: str = "m") -> Dict[str, Any]:
    """Tool to get current weather."""
    weather_api = WeatherAPI()
    return weather_api.get_current_weather(query, units=units)


@tool
def get_weather(query: str, units: str = "m") -> Dict[str, Any]:
    """Get current weather for a location."""
    return get_weather_tool(query, units=units)
