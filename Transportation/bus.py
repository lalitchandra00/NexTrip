# Bus API utilities (Flixbus)

import os
import requests
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

load_dotenv()


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
        response = requests.get(url, headers=self.headers, params=querystring)
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
        response = requests.get(url, headers=self.headers, params=querystring)
        response.raise_for_status()
        return response.json()


def search_buses_tool(from_location: str, to_location: str, travel_date: str, adult: int = 1) -> Dict[str, Any]:
    """Tool to search buses between locations."""
    bus_api = BusAPI()
    from_stations = bus_api.autocomplete_stations(from_location)
    to_stations = bus_api.autocomplete_stations(to_location)
    
    if not from_stations or not to_stations:
        return {"error": "Could not find bus stations"}
    
    from_id = from_stations[0].get("id") or from_stations[0].get("station_id") or from_stations[0].get("uid")
    to_id = to_stations[0].get("id") or to_stations[0].get("station_id") or to_stations[0].get("uid")
    
    if not from_id or not to_id:
        return {"error": "Could not extract bus station IDs", "from_stations": from_stations, "to_stations": to_stations}
    
    trips = bus_api.search_trips(str(from_id), str(to_id), travel_date, adult)
    return {
        "from_stations": from_stations,
        "to_stations": to_stations,
        "buses": trips
    }
