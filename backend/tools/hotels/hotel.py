# Hotels API utilities with LangChain tools
import os
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv()


class HotelAPI:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("RAPID_API_KEY") or os.getenv("RAPIDAPI_KEY")
        self.base_url = "https://booking-com15.p.rapidapi.com/api/v1"
        self.headers = {
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": "booking-com15.p.rapidapi.com"
        }

    def search_destination(self, query: str) -> Dict[str, Any]:
        """Search hotel destination by name."""
        url = f"{self.base_url}/hotels/searchDestination"
        querystring = {"query": query}
        response = requests.get(url, headers=self.headers, params=querystring)
        response.raise_for_status()
        return response.json()

    def search_hotels(self, dest_id: str, search_type: str = "CITY",
                      adults: int = 1, children_age: str = "0,17",
                      room_qty: int = 1, page_number: int = 1,
                      units: str = "metric", temperature_unit: str = "c",
                      languagecode: str = "en-us", currency_code: str = "INR",
                      location: str = "US", arrival_date: Optional[str] = None,
                      departure_date: Optional[str] = None) -> Dict[str, Any]:
        """Search hotels using destination id."""
        url = f"{self.base_url}/hotels/searchHotels"
        querystring = {
            "dest_id": dest_id,
            "search_type": search_type,
            "adults": str(adults),
            "children_age": children_age,
            "room_qty": str(room_qty),
            "page_number": str(page_number),
            "units": units,
            "temperature_unit": temperature_unit,
            "languagecode": languagecode,
            "currency_code": currency_code,
            "location": location
        }
        if arrival_date:
            querystring["arrival_date"] = arrival_date
        if departure_date:
            querystring["departure_date"] = departure_date
        response = requests.get(url, headers=self.headers, params=querystring)
        response.raise_for_status()
        return response.json()


def search_hotels_tool(destination: str, arrival_date: Optional[str] = None,
                       departure_date: Optional[str] = None,
                       search_type: str = "CITY", adults: int = 1,
                       currency_code: str = "INR") -> Dict[str, Any]:
    """Tool to search hotels at destination."""
    hotel_api = HotelAPI()
    dest_result = hotel_api.search_destination(destination)
    if not dest_result.get("data"):
        return {"error": "Could not find destination", "raw": dest_result}

    dest = dest_result["data"][0]
    dest_id = dest.get("dest_id")
    hotels = hotel_api.search_hotels(dest_id, search_type=search_type,
                                     adults=adults, currency_code=currency_code,
                                     arrival_date=arrival_date,
                                     departure_date=departure_date)
    return {
        "destination_info": dest,
        "all_destinations": dest_result.get("data", []),
        "hotels": hotels
    }


@tool
def search_hotels(destination: str, arrival_date: Optional[str] = None,
                  departure_date: Optional[str] = None,
                  search_type: str = "CITY", adults: int = 1,
                  currency_code: str = "INR") -> Dict[str, Any]:
    """Search hotels at destination."""
    return search_hotels_tool(destination, arrival_date, departure_date,
                              search_type, adults, currency_code)
