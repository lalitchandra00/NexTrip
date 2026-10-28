# Combined toolkit for all tools
from typing import List

from Transportation.train import search_trains
from Transportation.flight import search_flights
from Transportation.bus import search_buses
from Stay.hotel import search_hotels
from Rentals.car import search_rentals
from Weather.weather import get_weather


class NexTripToolkit:
    """Combined toolkit for all NexTrip tools."""

    @staticmethod
    def get_transportation_tools() -> List:
        return [
            search_trains,
            search_flights,
            search_buses,
        ]

    @staticmethod
    def get_hotel_tools() -> List:
        return [
            search_hotels,
        ]

    @staticmethod
    def get_rental_tools() -> List:
        return [
            search_rentals,
        ]

    @staticmethod
    def get_weather_tools() -> List:
        return [
            get_weather,
        ]

    @staticmethod
    def get_all_tools() -> List:
        tools = []
        tools.extend(NexTripToolkit.get_transportation_tools())
        tools.extend(NexTripToolkit.get_hotel_tools())
        tools.extend(NexTripToolkit.get_rental_tools())
        tools.extend(NexTripToolkit.get_weather_tools())
        return tools


def get_all_tools():
    return NexTripToolkit.get_all_tools()


def get_transportation_tools():
    return NexTripToolkit.get_transportation_tools()
