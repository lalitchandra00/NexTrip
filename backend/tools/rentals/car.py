# Car rental API utilities with LangChain tools
import os
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv()


class RentalAPI:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("RAPID_API_KEY") or os.getenv("RAPIDAPI_KEY")
        self.base_url = "https://booking-com15.p.rapidapi.com/api/v2"
        self.headers = {
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": "booking-com15.p.rapidapi.com"
        }

    def search_destination(self, term: str, country_of_residence: str = "us") -> Dict[str, Any]:
        """Get location details for car pickup."""
        url = f"{self.base_url}/cars/searchDestination"
        querystring = {"term": term, "countryOfResidence": country_of_residence}
        response = requests.get(url, headers=self.headers, params=querystring)
        response.raise_for_status()
        return response.json()

    def search_car_rentals(self, pick_up_latitude: str, pick_up_longitude: str,
                           pick_up_date: str, pick_up_time: str,
                           drop_off_date: str, drop_off_time: str,
                           country_of_residence: str = "us") -> Dict[str, Any]:
        """Search car rentals."""
        url = f"{self.base_url}/cars/searchCarRentals"
        querystring = {
            "pick_up_latitude": pick_up_latitude,
            "pick_up_longitude": pick_up_longitude,
            "pick_up_date": pick_up_date,
            "pick_up_time": pick_up_time,
            "drop_off_date": drop_off_date,
            "drop_off_time": drop_off_time,
            "countryOfResidence": country_of_residence
        }
        response = requests.get(url, headers=self.headers, params=querystring)
        response.raise_for_status()
        return response.json()


def search_rentals_tool(location_term: str, pick_up_date: str, pick_up_time: str,
                        drop_off_date: str, drop_off_time: str,
                        country_of_residence: str = "us") -> Dict[str, Any]:
    """Tool to search car rentals. Get lat/lon for location first."""
    rental_api = RentalAPI()
    dest = rental_api.search_destination(location_term, country_of_residence)
    if not dest.get("data"):
        return {"error": "Could not find location", "raw": dest}

    loc = dest["data"][0]
    lat = loc.get("latitude") or loc.get("lat")
    lon = loc.get("longitude") or loc.get("lng") or loc.get("lon")
    if lat is None or lon is None:
        return {"error": "Could not extract coordinates", "location": loc}

    rentals = rental_api.search_car_rentals(str(lat), str(lon), pick_up_date,
                                            pick_up_time, drop_off_date,
                                            drop_off_time, country_of_residence)
    return {
        "pickup_location": loc,
        "rentals": rentals
    }


@tool
def search_rentals(location_term: str, pick_up_date: str, pick_up_time: str,
                   drop_off_date: str, drop_off_time: str,
                   country_of_residence: str = "us") -> Dict[str, Any]:
    """Search car rentals at location."""
    return search_rentals_tool(location_term, pick_up_date, pick_up_time,
                               drop_off_date, drop_off_time,
                               country_of_residence)
