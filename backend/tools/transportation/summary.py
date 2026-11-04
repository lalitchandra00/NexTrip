# Normalized transportation results for the trip response
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from tools.rentals.car import search_rentals_tool
from tools.transportation.bus import search_buses_tool
from tools.transportation.flight import search_flights_tool
from tools.transportation.train import search_trains_tool


def _clock(value: Optional[str]) -> Optional[str]:
    if not value or not isinstance(value, str):
        return value
    parts = value.split(":")
    if len(parts) >= 2:
        return f"{parts[0].zfill(2)}:{parts[1].zfill(2)}"
    return value


def _iso_time(value: Optional[str]) -> Optional[str]:
    if not value or not isinstance(value, str):
        return value
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%H:%M")
    except ValueError:
        return value


def _minutes_between(start: Optional[str], end: Optional[str],
                     start_offset: int = 0, end_offset: int = 0) -> Optional[int]:
    if not start or not end:
        return None
    try:
        start_time = datetime.strptime(start, "%H:%M:%S")
        end_time = datetime.strptime(end, "%H:%M:%S")
    except ValueError:
        try:
            start_time = datetime.strptime(start, "%H:%M")
            end_time = datetime.strptime(end, "%H:%M")
        except ValueError:
            return None
    minutes = int((end_time - start_time).total_seconds() // 60)
    minutes += (end_offset - start_offset) * 24 * 60
    if minutes <= 0:
        minutes += 24 * 60
    return minutes


def _duration_label(minutes: Optional[int]) -> Optional[str]:
    if minutes is None:
        return None
    hours, mins = divmod(int(minutes), 60)
    if hours and mins:
        return f"{hours}h {mins}m"
    if hours:
        return f"{hours}h"
    return f"{mins}m"


def _error_of(raw: Dict[str, Any], fallback: str) -> Optional[str]:
    if not isinstance(raw, dict):
        return fallback
    if raw.get("error"):
        return str(raw["error"])
    return None


def build_train_leg(from_location: str, to_location: str) -> Dict[str, Any]:
    try:
        raw = search_trains_tool(from_location, to_location)
    except Exception as exc:
        return {"mode": "train", "options": [], "error": f"Train search failed: {exc}"}

    error = _error_of(raw, None)
    if error:
        return {"mode": "train", "options": [], "error": error}

    from_station = (raw.get("from_stations") or [{}])[0]
    to_station = (raw.get("to_stations") or [{}])[0]
    trains = (raw.get("trains") or {}).get("data") or []
    options = []
    for train in trains[:5]:
        departure = train.get("from_station") or {}
        arrival = train.get("to_station") or {}
        dep_time = departure.get("departure_time")
        arr_time = arrival.get("arrival_time")
        duration = _minutes_between(
            dep_time,
            arr_time,
            int(departure.get("departure_day_offset") or 0),
            int(arrival.get("arrival_day_offset") or 0),
        )
        options.append({
            "title": train.get("train_name") or train.get("train_no"),
            "subtitle": " · ".join(
                part for part in (train.get("train_no"), train.get("train_type")) if part
            ),
            "from": departure.get("display_name_en"),
            "to": arrival.get("display_name_en"),
            "depart": _clock(dep_time),
            "arrive": _clock(arr_time),
            "duration": _duration_label(duration),
            "price": None,
            "meta": f"{train.get('stops_count', 0)} stops" if train.get("stops_count") else None,
        })

    return {
        "mode": "train",
        "from": from_station.get("display_name_en") or from_location,
        "to": to_station.get("display_name_en") or to_location,
        "options": options,
        "error": None if options else "No trains found for this route.",
    }


def _flight_options(raw: Dict[str, Any]) -> List[Dict[str, Any]]:
    payload = raw.get("flights") or {}
    data = payload.get("data") if isinstance(payload, dict) else {}
    if isinstance(payload, dict) and isinstance(payload.get("itineraries"), list):
        itineraries = payload.get("itineraries")
    else:
        itineraries = (data or {}).get("itineraries") if isinstance(data, dict) else None
    options = []
    for itinerary in (itineraries or [])[:5]:
        legs = itinerary.get("legs") or []
        leg = legs[0] if legs else {}
        origin = leg.get("origin") or {}
        destination = leg.get("destination") or {}
        carriers = (leg.get("carriers") or {}).get("marketing") or []
        carrier = carriers[0].get("name") if carriers else None
        price = itinerary.get("price") or {}
        options.append({
            "title": carrier or f"{origin.get('displayCode', '')} → {destination.get('displayCode', '')}".strip(),
            "subtitle": " · ".join(
                part for part in (origin.get("displayCode"), destination.get("displayCode")) if part
            ),
            "from": origin.get("name"),
            "to": destination.get("name"),
            "depart": _iso_time(leg.get("departure")),
            "arrive": _iso_time(leg.get("arrival")),
            "duration": _duration_label(leg.get("durationInMinutes")),
            "price": price.get("formatted") or price.get("raw"),
            "meta": f"{len(leg.get('segments') or [])} segment(s)"
            if leg.get("segments") else None,
        })
    return options


def build_flight_leg(from_location: str, to_location: str, travel_date: str,
                     cabin_class: str, adults: int) -> Dict[str, Any]:
    try:
        raw = search_flights_tool(from_location, to_location, travel_date, cabin_class, adults)
    except Exception as exc:
        return {"mode": "flight", "options": [], "error": f"Flight search failed: {exc}"}

    error = _error_of(raw, None)
    if error:
        return {"mode": "flight", "options": [], "error": error}

    options = _flight_options(raw)
    return {
        "mode": "flight",
        "options": options,
        "error": None if options else "No flights found for this route.",
    }


def _bus_options(raw: Dict[str, Any]) -> List[Dict[str, Any]]:
    journeys = (raw.get("buses") or {}).get("journeys") or []
    options = []
    for journey in journeys[:5]:
        if journey.get("error"):
            continue
        departure = journey.get("departure") or {}
        arrival = journey.get("arrival") or {}
        price = journey.get("price") or {}
        options.append({
            "title": journey.get("provider") or journey.get("name") or "Bus",
            "subtitle": journey.get("line") or journey.get("number"),
            "from": departure.get("name") or departure.get("station"),
            "to": arrival.get("name") or arrival.get("station"),
            "depart": _iso_time(departure.get("time") or departure.get("datetime") or journey.get("departure_time")),
            "arrive": _iso_time(arrival.get("time") or arrival.get("datetime") or journey.get("arrival_time")),
            "duration": journey.get("duration") or _duration_label(journey.get("duration_minutes")),
            "price": price.get("formatted") if isinstance(price, dict) else price,
            "meta": f"{journey.get('transfers', 0)} transfer(s)" if journey.get("transfers") else None,
        })
    return options


def build_bus_leg(from_location: str, to_location: str, travel_date: str, adults: int) -> Dict[str, Any]:
    try:
        raw = search_buses_tool(from_location, to_location, travel_date, adults)
    except Exception as exc:
        return {"mode": "bus", "options": [], "error": f"Bus search failed: {exc}"}

    error = _error_of(raw, None)
    if not error:
        journeys = (raw.get("buses") or {}).get("journeys") or []
        for journey in journeys:
            if journey.get("error"):
                error = journey.get("message") or "No buses found for this route."
                break

    options = _bus_options(raw) if not error else []
    return {
        "mode": "bus",
        "options": options,
        "error": error if error else (None if options else "No buses found for this route."),
    }


def _car_options(raw: Dict[str, Any]) -> List[Dict[str, Any]]:
    payload = raw.get("rentals") or {}
    data = payload.get("data") if isinstance(payload, dict) else {}
    content = (data or {}).get("content") if isinstance(data, dict) else {}
    items = (content or {}).get("items") if isinstance(content, dict) else None
    if not items and isinstance(data, dict):
        items = data.get("items")
    options = []
    for item in (items or [])[:5]:
        vehicle = item.get("vehicle_info") or item.get("vehicle") or {}
        supplier = item.get("supplier_info") or {}
        price = item.get("price") or item.get("pricing") or {}
        options.append({
            "title": vehicle.get("v_group") or vehicle.get("name") or item.get("name") or "Car rental",
            "subtitle": supplier.get("name") or item.get("supplier_name") or item.get("supplier"),
            "from": (raw.get("pickup_location") or {}).get("name"),
            "to": None,
            "depart": None,
            "arrive": None,
            "duration": None,
            "price": price.get("formatted") if isinstance(price, dict) else price,
            "meta": vehicle.get("transmission") or vehicle.get("category"),
        })
    return options


def build_car_leg(location: str, pick_up_date: str, drop_off_date: str,
                  country_of_residence: str = "in") -> Dict[str, Any]:
    try:
        raw = search_rentals_tool(
            location, pick_up_date, "10:00", drop_off_date, "10:00",
            country_of_residence,
        )
    except Exception as exc:
        return {"mode": "car", "options": [], "error": f"Car rental search failed: {exc}"}

    error = _error_of(raw, None)
    if error:
        return {"mode": "car", "options": [], "error": error}

    options = _car_options(raw)
    return {
        "mode": "car",
        "options": options,
        "error": None if options else "No car rentals available for these dates.",
    }


def _return_date(travel_date: str, num_days: int, return_date: Optional[str]) -> str:
    if return_date:
        return return_date
    try:
        start = datetime.strptime(travel_date, "%Y-%m-%d")
        return (start + timedelta(days=max(1, num_days))).strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        return travel_date


def build_transport_summary(
    from_location: str,
    to_location: str,
    travel_date: str,
    num_days: int = 1,
    return_date: Optional[str] = None,
    adults: int = 1,
    cabin_class: str = "economy",
    include_rentals: bool = False,
    country_of_residence: str = "in",
) -> Dict[str, Any]:
    legs: Dict[str, Any] = {}
    legs["train"] = build_train_leg(from_location, to_location)
    legs["flight"] = build_flight_leg(from_location, to_location, travel_date, cabin_class, adults)
    legs["bus"] = build_bus_leg(from_location, to_location, travel_date, adults)
    if include_rentals:
        legs["car"] = build_car_leg(
            to_location,
            travel_date,
            _return_date(travel_date, num_days, return_date),
            country_of_residence,
        )
    return {
        "from": from_location,
        "to": to_location,
        "date": travel_date,
        "legs": legs,
    }
