# Bus API utilities with LangChain tools (Flixbus)
import os
import requests
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv()

REQUEST_TIMEOUT = 20


class BusAPI:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("RAPID_API_KEY") or os.getenv("RAPIDAPI_KEY")
        self.base_url = "https://flixbus2.p.rapidapi.com"
        self.headers = {
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": "flixbus2.p.rapidapi.com"
        }

    def autocomplete_stations(self, query: str, locale: str = "en") -> Dict[str, Any]:
        """Get bus stations/autocomplete for location."""
        url = f"{self.base_url}/autocomplete"
        querystring = {"query": query, "locale": locale}
        response = requests.get(url, headers=self.headers, params=querystring, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()

    def search_trips(self, from_id: str, to_id: str, date: str, adult: int = 1) -> Dict[str, Any]:
        """Search bus trips. Need from_id, to_id, adult, date."""
        url = f"{self.base_url}/trips"
        querystring = {
            "from_id": from_id,
            "to_id": to_id,
            "date": date,
            "adult": str(adult)
        }
        response = requests.get(url, headers=self.headers, params=querystring, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()


def _to_bus_date(value: str) -> str:
    try:
        year, month, day = value.split("-")
        return f"{day}.{month}.{year}"
    except (ValueError, AttributeError):
        return value


def _first_station(result: Any) -> Dict[str, Any]:
    if isinstance(result, list):
        return result[0] if result else {}
    if isinstance(result, dict):
        for key in ("data", "stations", "results", "cities"):
            value = result.get(key)
            if isinstance(value, list) and value:
                return value[0]
            if isinstance(value, dict):
                return value
        return result
    return {}


def search_buses_tool(from_location: str, to_location: str, travel_date: str, adult: int = 1) -> Dict[str, Any]:
    """Tool to search buses between locations."""
    bus_api = BusAPI()
    from_station = _first_station(bus_api.autocomplete_stations(from_location))
    to_station = _first_station(bus_api.autocomplete_stations(to_location))

    if not from_station or not to_station:
        return {"error": "Could not find bus stations"}

    from_id = from_station.get("id") or from_station.get("station_id") or from_station.get("uid") or from_station.get("legacy_id")
    to_id = to_station.get("id") or to_station.get("station_id") or to_station.get("uid") or to_station.get("legacy_id")

    if not from_id or not to_id:
        return {"error": "Could not extract bus station IDs", "from_stations": from_station, "to_stations": to_station}

    trips = bus_api.search_trips(str(from_id), str(to_id), _to_bus_date(travel_date), adult)
    return {
        "from_stations": from_station,
        "to_stations": to_station,
        "buses": trips
    }


@tool
def search_buses(from_location: str, to_location: str, travel_date: str, adult: int = 1) -> Dict[str, Any]:
    """Search for bus trips between locations."""
    try:
        return search_buses_tool(from_location, to_location, travel_date, adult)
    except Exception as e:
        return {"error": f"Bus search failed: {e}"}
