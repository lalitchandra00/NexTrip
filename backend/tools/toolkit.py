# Combined toolkit for all tools
from typing import List

from tools.transportation.train import search_trains
from tools.transportation.flight import search_flights
from tools.transportation.bus import search_buses
from tools.hotels.hotel import search_hotels
from tools.rentals.car import search_rentals
from tools.weather.weather import get_weather


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
