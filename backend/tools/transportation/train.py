# Train API utilities with LangChain tools
import os
import requests
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv()

REQUEST_TIMEOUT = 20


class TrainAPI:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("RAPID_API_KEY") or os.getenv("RAPIDAPI_KEY")
        self.base_url = "https://rail-info-api-india1.p.rapidapi.com/v1"
        self.headers = {
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": "rail-info-api-india1.p.rapidapi.com"
        }

    def search_stations(self, query: str, lat: Optional[float] = None,
                         lon: Optional[float] = None) -> Dict[str, Any]:
        """Search for railway stations by name (only q needed)."""
        url = f"{self.base_url}/stations/search"
        querystring = {"q": query}
        response = requests.get(url, headers=self.headers, params=querystring, timeout=REQUEST_TIMEOUT)
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
        response = requests.get(url, headers=self.headers, params=querystring, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()

    def find_closest_stations(self, query: str, lat: Optional[float] = None,
                              lon: Optional[float] = None) -> List[Dict[str, Any]]:
        """Find stations matching query, optionally using location to find closest."""
        result = self.search_stations(query, lat=lat, lon=lon)
        return result.get("data", [])


def _rank_stations(stations: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
    """Prefer major, well-named stations over obscure nearby halts."""
    needle = (query or "").strip().lower()

    def score(station: Dict[str, Any]) -> float:
        name = (station.get("display_name_en") or "").lower()
        value = 0.0
        if needle and name == needle:
            value += 100
        if needle and (name.startswith(needle) or name.endswith(needle)):
            value += 20
        if needle and needle in name:
            value += 10
        for keyword, weight in (
            ("junction", 8),
            ("jn", 8),
            ("central", 6),
            ("terminus", 6),
            ("isbt", 6),
            ("new ", 3),
        ):
            if keyword in name:
                value += weight
        for keyword in ("airport", "metro", "halt", "cabinet", "secretariat"):
            if keyword in name:
                value -= 20
        return value

    return sorted(stations, key=score, reverse=True)


def _station_code(station: Dict[str, Any]) -> Optional[str]:
    return (
        station.get("code_current")
        or station.get("station_code")
        or station.get("code")
    )


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

    from_stations = _rank_stations(from_stations, from_location)
    to_stations = _rank_stations(to_stations, to_location)

    # Try the best-looking station pairs until one returns trains.
    trains: Dict[str, Any] = {}
    used_from = from_stations[0]
    used_to = to_stations[0]
    for from_station in from_stations[:2]:
        from_code = _station_code(from_station)
        if not from_code:
            continue
        for to_station in to_stations[:2]:
            to_code = _station_code(to_station)
            if not to_code:
                continue
            candidate = train_api.get_trains_between_stations(from_code, to_code)
            if candidate.get("data"):
                trains = candidate
                used_from = from_station
                used_to = to_station
                break
            if not trains:
                trains = candidate
        if trains.get("data"):
            break

    return {
        "from_stations": [used_from],
        "to_stations": [used_to],
        "trains": trains or {"data": []}
    }


@tool
def search_trains(from_location: str, to_location: str,
                  from_lat: Optional[float] = None, from_lon: Optional[float] = None,
                  to_lat: Optional[float] = None, to_lon: Optional[float] = None) -> Dict[str, Any]:
    """Search for trains between locations. Find stations and get trains."""
    try:
        return search_trains_tool(from_location, to_location, from_lat, from_lon, to_lat, to_lon)
    except Exception as e:
        return {"error": f"Train search failed: {e}"}
