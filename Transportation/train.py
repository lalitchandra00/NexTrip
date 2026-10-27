# Train API utilities

import os
import requests
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

load_dotenv()


class TrainAPI:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("RAPID_API_KEY") or os.getenv("RAPIDAPI_KEY")
        self.base_url = "https://rail-info-api-india1.p.rapidapi.com/v1"
        self.headers = {
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": "rail-info-api-india1.p.rapidapi.com"
        }

    def search_stations(self, query: str) -> Dict[str, Any]:
        """Search for railway stations by name (only q needed)."""
        url = f"{self.base_url}/stations/search"
        querystring = {"q": query}
        response = requests.get(url, headers=self.headers, params=querystring)
        response.raise_for_status()
        return response.json()

    def get_trains_between_stations(self, from_station: str, to_station: str,
                                   via: Optional[str] = None) -> Dict[str, Any]:
        """Get trains between two station codes. Only from, to, via needed."""
        url = f"{self.base_url}/trains/between"
        querystring = {
            "from": from_station,
            "to": to_station
        }
        if via:
            querystring["via"] = via
        response = requests.get(url, headers=self.headers, params=querystring)
        response.raise_for_status()
        return response.json()

    def find_closest_stations(self, query: str, lat: Optional[float] = None, 
                            lon: Optional[float] = None) -> List[Dict[str, Any]]:
        """Find stations matching query, optionally using location to find closest."""
        result = self.search_stations(query, lat=lat, lon=lon)
        return result.get("data", [])


def search_trains_tool(from_location: str, to_location: str, 
                     from_lat: Optional[float] = None, from_lon: Optional[float] = None,
                     to_lat: Optional[float] = None, to_lon: Optional[float] = None) -> Dict[str, Any]:
    """
    Tool to search for trains between locations.
    LLM converts location names to station codes; this tool handles the API calls.
    """
    train_api = TrainAPI()
    
    # Find station codes for both locations
    from_stations = train_api.find_closest_stations(from_location, from_lat, from_lon)
    to_stations = train_api.find_closest_stations(to_location, to_lat, to_lon)
    
    if not from_stations or not to_stations:
        return {"error": "Could not find stations for one or both locations"}
    
    # Use first/closest station codes
    from_code = from_stations[0].get("station_code")
    to_code = to_stations[0].get("station_code")
    
    # Get trains
    trains = train_api.get_trains_between_stations(from_code, to_code)
    
    return {
        "from_stations": from_stations,
        "to_stations": to_stations,
        "trains": trains
    }


