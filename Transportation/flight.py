# Flight API utilities

import os
import requests
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

load_dotenv()


class FlightAPI:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("RAPID_API_KEY") or os.getenv("RAPIDAPI_KEY")
        self.base_url = "https://sky-scrapper.p.rapidapi.com/api"
        self.headers = {
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": "sky-scrapper.p.rapidapi.com"
        }

    def search_airports(self, query: str, locale: str = "en-US") -> Dict[str, Any]:
        """Search for airports/cities by name. Send only query as needed."""
        url = f"{self.base_url}/v1/flights/searchAirport"
        querystring = {"query": query, "locale": locale}
        response = requests.get(url, headers=self.headers, params=querystring)
        response.raise_for_status()
        return response.json()

    def search_flights(self, origin_sky_id: str, destination_sky_id: str,
                       origin_entity_id: str, destination_entity_id: str,
                       date: str, cabin_class: str = "economy",
                       adults: int = 1, sort_by: str = "best",
                       currency: str = "INR", market: str = "en-US",
                       country_code: str = "US") -> Dict[str, Any]:
        """Search for flights. Need origin/dest skyId, entityId, date, cabinClass, currency etc."""
        url = f"{self.base_url}/v2/flights/searchFlights"
        querystring = {
            "originSkyId": origin_sky_id,
            "destinationSkyId": destination_sky_id,
            "originEntityId": origin_entity_id,
            "destinationEntityId": destination_entity_id,
            "date": date,
            "cabinClass": cabin_class,
            "adults": str(adults),
            "sortBy": sort_by,
            "currency": currency,
            "market": market,
            "countryCode": country_code
        }
        response = requests.get(url, headers=self.headers, params=querystring)
        response.raise_for_status()
        return response.json()

    def get_nearby_airports(self, query: str) -> List[Dict[str, Any]]:
        """Get nearby airports for a location."""
        result = self.search_airports(query)
        return result.get("data", [])


def search_flights_tool(from_location: str, to_location: str, travel_date: str,
                       cabin_class: str = "economy", adults: int = 1) -> Dict[str, Any]:
    """
    Tool to search for flights between locations.
    Finds airports for both locations and searches flights.
    """
    flight_api = FlightAPI()
    
    # Find airports for both locations
    from_airports = flight_api.get_nearby_airports(from_location)
    to_airports = flight_api.get_nearby_airports(to_location)
    
    if not from_airports or not to_airports:
        return {"error": "Could not find airports for one or both locations"}
    
    # Extract relevant params
    from_airport = from_airports[0]
    to_airport = to_airports[0]
    
    origin_sky_id = from_airport.get("navigation", {}).get("relevantFlightParams", {}).get("skyId")
    origin_entity_id = from_airport.get("navigation", {}).get("relevantFlightParams", {}).get("entityId")
    dest_sky_id = to_airport.get("navigation", {}).get("relevantFlightParams", {}).get("skyId")
    dest_entity_id = to_airport.get("navigation", {}).get("relevantFlightParams", {}).get("entityId")
    
    if not all([origin_sky_id, origin_entity_id, dest_sky_id, dest_entity_id]):
        return {"error": "Could not extract airport parameters"}
    
    # Search flights
    flights = flight_api.search_flights(
        origin_sky_id=origin_sky_id,
        destination_sky_id=dest_sky_id,
        origin_entity_id=origin_entity_id,
        destination_entity_id=dest_entity_id,
        date=travel_date,
        cabin_class=cabin_class,
        adults=adults
    )
    
    return {
        "from_airports": from_airports,
        "to_airports": to_airports,
        "flights": flights
    }
