# Transportation Tools - unified interface and toolkit
from .train import search_trains_tool, TrainAPI, search_trains
from .flight import search_flights_tool, FlightAPI, search_flights
from .bus import search_buses_tool, BusAPI, search_buses
from typing import Dict, Any, Optional, List


class TransportationTool:
    """Unified tool for searching trains, flights, and buses."""

    def __init__(self):
        self.train_api = TrainAPI()
        self.flight_api = FlightAPI()
        self.bus_api = BusAPI()

    def search_transportation(self, from_location: str, to_location: str,
                             travel_date: Optional[str] = None,
                             mode: str = "both",
                             cabin_class: str = "economy",
                             adults: int = 1,
                             currency: str = "INR",
                             **kwargs) -> Dict[str, Any]:
        """Search for transportation options (trains/flights/buses)."""
        result = {}

        if mode in ["train", "both"]:
            try:
                result["trains"] = search_trains_tool(from_location, to_location)
            except Exception as e:
                result["trains_error"] = str(e)

        if mode in ["flight", "both"]:
            if not travel_date:
                result["flights_error"] = "travel_date required for flight search"
            else:
                try:
                    result["flights"] = search_flights_tool(from_location, to_location, travel_date, cabin_class, adults)
                except Exception as e:
                    result["flights_error"] = str(e)

        if mode in ["bus", "both"]:
            if not travel_date:
                result["buses_error"] = "travel_date required for bus search"
            else:
                try:
                    result["buses"] = search_buses_tool(from_location, to_location, travel_date, adults)
                except Exception as e:
                    result["buses_error"] = str(e)

        return result

    def search_trains(self, from_location: str, to_location: str) -> Dict[str, Any]:
        return search_trains_tool(from_location, to_location)

    def search_flights(self, from_location: str, to_location: str, travel_date: str,
                       cabin_class: str = "economy", adults: int = 1) -> Dict[str, Any]:
        return search_flights_tool(from_location, to_location, travel_date, cabin_class, adults)

    def search_buses(self, from_location: str, to_location: str, travel_date: str, adult: int = 1) -> Dict[str, Any]:
        return search_buses_tool(from_location, to_location, travel_date, adult)


class TransportationToolkit:
    """Toolkit containing all transportation tools for LangChain agent."""

    @staticmethod
    def get_tools():
        return [
            search_trains,
            search_flights,
            search_buses,
        ]


# Convenience function
def transportation_search_tool(**kwargs) -> Dict[str, Any]:
    """Main tool function for transportation search."""
    tool = TransportationTool()
    return tool.search_transportation(**kwargs)


def get_transportation_tools():
    """Get all transportation tools as a list."""
    return TransportationToolkit.get_tools()
